"""M0 — schema-validated pure LLM calls + spend accounting (MINI_PLAN §3.2).

One function: ``call(endpoint, prompt, schema, meter, blobs)``. EVERY exit
path carries spend: success returns it; SchemaError / EndpointError /
BudgetExceeded all carry ``.spend`` for the caller to log — the parent's
exception-spend family, ported verbatim (retry-exhausted calls burned 8.4%
of a live run; exhaustion mid-retry leaked an 833-token delta). The
TokenMeter check-before-spend is approximate by design: the attempt that
crosses the ceiling completes (documented overshoot, not pretended away).
"""

import json
import time
import urllib.error
import urllib.request

from pydantic import BaseModel

from deepreason.llm.firewall import (
    EndpointLease,
    RouteFirewallError,
    reject_model_control_fields,
    route_from_endpoint,
    route_fingerprint,
)
from deepreason.llm.profiles import ModelProfile, ProfileSpec, clip_pack, get_profile
from deepreason.llm.providers import infer_provider
from deepreason.llm.repair import (
    BoundedRepairSession,
    SchemaRepairError,
)
from deepreason.llm.wire import (
    WireContract,
    minimal_example,
    wire_contract_for,
)
from deepreason.ontology.event import LLMAttempt
from minireason.log import BlobStore, Call

_RETRYABLE_HTTP = {429, 500, 502, 503, 504}
_BACKOFFS = (2, 4, 8)
_TIMEOUT_FACTORS = (1, 2)  # bounded read-timeout escalation; see HttpEndpoint


class BudgetExceeded(RuntimeError):
    def __init__(self, message: str, spend: Call | None = None) -> None:
        super().__init__(message)
        self.spend = spend


class EndpointError(RuntimeError):
    def __init__(self, message: str, spend: Call | None = None) -> None:
        super().__init__(message)
        self.spend = spend


# Backwards-compatible MiniReason name for the parent's shared bounded-repair
# failure.  Callers keep catching ``SchemaError`` while both engines now use
# one process exception and one repair protocol.
SchemaError = SchemaRepairError


class TokenMeter:
    """Hard provider-wide ceiling; enforcement lives in call() — the one
    place every request passes through. Meter total must equal the sum of
    logged Call.tokens (G1), enforced by tests and the smoke driver."""

    def __init__(self, budget: int | None = None) -> None:
        self.budget = budget
        self.prompt_tokens = 0
        self.completion_tokens = 0
        self.calls = 0

    @property
    def total(self) -> int:
        return self.prompt_tokens + self.completion_tokens

    def check(self) -> None:
        if self.budget is not None and self.total >= self.budget:
            raise BudgetExceeded(f"token budget exhausted: {self.total}/{self.budget}")

    def add(self, usage: dict) -> None:
        self.prompt_tokens += int(usage.get("prompt_tokens", 0))
        self.completion_tokens += int(usage.get("completion_tokens", 0))
        self.calls += 1

    def snapshot(self) -> dict:
        return {"prompt_tokens": self.prompt_tokens,
                "completion_tokens": self.completion_tokens,
                "total": self.total, "budget": self.budget, "calls": self.calls}


def usage_tokens(usage: dict | None, request: str, raw: str) -> dict:
    """Mirror DeepReason's deterministic partial-usage normalization."""

    def estimate(text: str) -> int:
        return max(1, (len(text) + 3) // 4) if text else 0

    prompt_est = estimate(request)
    completion_est = estimate(raw)
    prompt = usage.get("prompt_tokens") if usage else None
    completion = usage.get("completion_tokens") if usage else None
    total = usage.get("total_tokens") if usage else None

    if prompt is not None or completion is not None:
        prompt_tokens = int(prompt) if prompt is not None else prompt_est
        completion_tokens = (
            int(completion) if completion is not None else completion_est
        )
        if total is not None and (prompt is None) != (completion is None):
            remainder = max(0, int(total) - prompt_tokens - completion_tokens)
            if prompt is None:
                prompt_tokens += remainder
            else:
                completion_tokens += remainder
        return {
            "prompt_tokens": prompt_tokens,
            "completion_tokens": completion_tokens,
        }

    if total is not None:
        total_tokens = max(0, int(total))
        estimated_total = prompt_est + completion_est
        if estimated_total == 0:
            return {"prompt_tokens": total_tokens, "completion_tokens": 0}
        nonempty_sides = int(prompt_est > 0) + int(completion_est > 0)
        if total_tokens < nonempty_sides:
            return {
                "prompt_tokens": prompt_est,
                "completion_tokens": completion_est,
            }
        prompt_tokens = round(total_tokens * prompt_est / estimated_total)
        if prompt_est:
            prompt_tokens = max(1, prompt_tokens)
        if completion_est:
            prompt_tokens = min(total_tokens - 1, prompt_tokens)
        return {
            "prompt_tokens": prompt_tokens,
            "completion_tokens": total_tokens - prompt_tokens,
        }

    return {
        "prompt_tokens": prompt_est,
        "completion_tokens": completion_est,
    }


class MockEndpoint:
    """Scripted (or prompt-computed) responses with chars/4 usage, so token
    accounting is testable without network."""

    def __init__(self, responses, name: str = "mock", model: str = "mock") -> None:
        self._fn = responses if callable(responses) else None
        self._responses = None if callable(responses) else list(responses)
        self.name, self.model = name, model
        self.last_usage: dict | None = None
        self.last_finish_reason: str | None = None
        self.last_transport_attempts = 0
        self.last_transport_diagnostics: list[str] = []

    def complete(self, prompt: str) -> str:
        self.last_usage = None
        self.last_finish_reason = None
        self.last_transport_attempts = 1
        self.last_transport_diagnostics = []
        if self._fn is not None:
            try:
                response = self._fn(prompt)
            except EndpointError as error:
                self.last_transport_diagnostics.append(
                    f"{type(error).__name__}:{str(error)[:200]}"
                )
                raise
        elif self._responses:
            response = self._responses.pop(0)
        else:
            raise EndpointError("MockEndpoint exhausted")
        self.last_usage = {"prompt_tokens": max(1, len(prompt) // 4),
                           "completion_tokens": max(1, len(response) // 4)}
        return response


class HttpEndpoint:
    """OpenAI-compatible chat completions; transient faults retry 2s/4s/8s."""

    def __init__(self, base_url: str, model: str, api_key: str | None = None,
                 temperature: float | None = None, max_tokens: int | None = None,
                 json_mode: bool = True, timeout_s: int = 300) -> None:
        self.name, self.model, self.api_key = base_url, model, api_key
        # Shared route freezing records the real provider identity instead of
        # route_from_endpoint's mock fallback. Mini still exposes only its
        # fixed JSON-text transport.
        self.provider = infer_provider(base_url)
        self.output_mechanism = "json_text"
        self.temperature, self.max_tokens = temperature, max_tokens
        self.json_mode, self.timeout_s = json_mode, timeout_s
        self.last_usage: dict | None = None
        self.last_finish_reason: str | None = None
        self.last_transport_attempts = 0
        self.last_transport_diagnostics: list[str] = []

    def complete(self, prompt: str) -> str:
        self.last_usage = None
        self.last_finish_reason = None
        self.last_transport_attempts = 0
        self.last_transport_diagnostics = []
        body: dict = {"model": self.model, "messages": [{"role": "user", "content": prompt}]}
        if self.temperature is not None:
            body["temperature"] = self.temperature
        if self.max_tokens is not None:
            body["max_tokens"] = self.max_tokens
        if self.json_mode:
            body["response_format"] = {"type": "json_object"}
        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        request = urllib.request.Request(
            self.name.rstrip("/") + "/chat/completions",
            data=json.dumps(body).encode(), headers=headers)
        last: Exception | None = None
        # Bounded read-timeout escalation (mirrors llm/endpoints.py): a read
        # timeout proves only that no complete response arrived before the
        # deadline; the retry waits 2x and a second read timeout is terminal
        # (max total wait 3x the base), other transport faults keep backoff.
        read_timeouts = 0
        for delay in (*_BACKOFFS, None):
            timeout = self.timeout_s * _TIMEOUT_FACTORS[read_timeouts]
            self.last_transport_attempts += 1
            try:
                with urllib.request.urlopen(request, timeout=timeout) as response:
                    data = json.load(response)
                choice = data["choices"][0]
                content = choice["message"]["content"]
                if content is None:
                    raise EndpointError(
                        f"null content (finish_reason={choice.get('finish_reason')!r})")
                self.last_usage = data.get("usage") or None
                self.last_finish_reason = choice.get("finish_reason")
                return content
            except urllib.error.HTTPError as e:
                self.last_transport_diagnostics.append(
                    f"HTTPError:HTTP-{e.code}:{str(e)[:200]}"
                )
                if e.code not in _RETRYABLE_HTTP:
                    raise EndpointError(f"HTTP {e.code}: {e.reason}") from e
                last = e
            except (urllib.error.URLError, ConnectionError, TimeoutError, OSError,
                    ValueError, KeyError, IndexError, TypeError) as e:
                self.last_transport_diagnostics.append(
                    f"{type(e).__name__}:{str(e)[:200]}"
                )
                if isinstance(e, TimeoutError) or (
                    isinstance(e, urllib.error.URLError)
                    and isinstance(e.reason, TimeoutError)
                ):
                    read_timeouts += 1
                    if read_timeouts >= len(_TIMEOUT_FACTORS):
                        waits = ", ".join(
                            f"{self.timeout_s * f}s" for f in _TIMEOUT_FACTORS)
                        raise EndpointError(
                            f"no complete response within escalated read "
                            f"timeouts ({waits}): {e}") from e
                last = e  # malformed 200 shapes are transient in practice
            if delay is None:
                break
            time.sleep(delay)
        raise EndpointError(f"transport failed after retries: {last}")


def call(
    endpoint,
    prompt: str,
    schema: type[BaseModel],
    meter: TokenMeter,
    blobs: BlobStore,
    retry_max: int = 2,
    role: str = "call",
    *,
    model_profile: str | ModelProfile | ProfileSpec = ModelProfile.COMPACT,
    wire_contract: WireContract | None = None,
    endpoint_lease: EndpointLease | None = None,
) -> tuple[BaseModel, Call]:
    """Run one leased, profile-rendered call through shared wire and repair.

    MiniReason owns the small outer loop; the parent compatibility kernel
    owns model-facing schemas, control-field rejection, semantic-preserving
    normalization, and the fixed initial + two-repair bound.
    """

    profile = get_profile(model_profile)
    contract = wire_contract or wire_contract_for(role, schema, profile.name)
    if contract.canonical_model is not schema:
        raise TypeError(
            f"wire contract {contract.contract_id} compiles to "
            f"{contract.canonical_model.__name__}, expected {schema.__name__}"
        )
    lease = endpoint_lease or EndpointLease(role, 0, route_from_endpoint(endpoint))
    if lease.role != role or lease.seat != 0:
        raise ValueError(
            f"endpoint lease {lease.role}[{lease.seat}] cannot serve {role}[0]"
        )
    lease.verify(endpoint)

    schema_value = contract.model_json_schema()
    schema_json = json.dumps(schema_value, sort_keys=True)
    rendered = clip_pack(prompt, profile)
    base = (
        "Respond with ONLY a JSON object conforming to this JSON Schema — "
        f"no prose, no code fences:\n{schema_json}\n"
        f"SYNTAX EXAMPLE:\n{minimal_example(contract)}\n\n{rendered}"
    )
    started = time.monotonic()
    tokens_used, truncated_any, raw_ref = 0, False, ""
    prompt_ref = blobs.put(base.encode())
    attempt_trace: list[LLMAttempt] = []
    trace_identity = {
        "contract_id": contract.contract_id,
        "endpoint_id": lease.route.endpoint_id,
        "route_sha256": route_fingerprint(lease.route),
        "seat": 0,
        "model_profile": profile.name.value,
        "transport_profile": profile.name.value,
    }
    repair = BoundedRepairSession(
        contract=contract.contract_id,
        schema=schema_value,
        initial_request=base,
        retry_max=retry_max,
    )

    def _spend(attempts: int) -> Call | None:
        if not tokens_used and not attempt_trace:
            return None
        return Call(role=role, model=getattr(endpoint, "model", ""),
                    endpoint=getattr(endpoint, "name", ""), prompt_ref=prompt_ref,
                    raw_ref=raw_ref, tokens=tokens_used,
                    ms=int((time.monotonic() - started) * 1000),
                    attempts=max(attempts, len(attempt_trace)),
                    truncated=truncated_any, attempt_trace=attempt_trace)

    # RETRY_MAX is a ceiling, never an escape hatch: W4 permits at most an
    # initial generation, one whole-object correction, and one local subtree.
    for attempt in range(repair.attempt_count):
        attempt_started = time.monotonic()
        try:
            meter.check()  # hard stop BEFORE spending
        except BudgetExceeded as e:
            e.spend = _spend(attempt)  # prior attempts already spent (G1)
            raise
        turn = repair.turn(attempt)
        request = turn.request
        # Re-check immediately before every provider request, including both
        # repair forms. A mid-call mutation is terminal, but the exception
        # must carry every earlier attempt's spend and replay trace.
        try:
            lease.verify(endpoint)
        except RouteFirewallError as e:
            e.spend = _spend(attempt)
            raise
        # Log only an ACTUAL provider request. A generated-but-unsent repair
        # prompt must not masquerade as a wire exchange.
        prompt_ref = prompt_ref if attempt == 0 else blobs.put(request.encode())
        try:
            raw = endpoint.complete(request)
        except EndpointError as e:
            diagnostic_payload = json.dumps(
                {
                    "contract": contract.contract_id,
                    "attempt": attempt,
                    "error": str(e)[:500],
                    "validation_path": turn.validation_path,
                    "repair_scope": turn.repair_scope,
                    "transport_diagnostics": list(
                        getattr(endpoint, "last_transport_diagnostics", ())
                    ),
                },
                sort_keys=True,
            )
            attempt_trace.append(LLMAttempt(
                prompt_ref=prompt_ref,
                diagnostic_ref=blobs.put(diagnostic_payload.encode()),
                attempt=attempt,
                validation_path=turn.validation_path,
                **trace_identity,
                repair_scope=turn.repair_scope,
                ms=int((time.monotonic() - attempt_started) * 1000),
                valid=False,
                usage_unknown=True,
                output_mechanism=lease.route.output_mechanism,
                transport_attempts=max(
                    1, int(getattr(endpoint, "last_transport_attempts", 0) or 0)
                ),
                transport_diagnostics=list(
                    getattr(endpoint, "last_transport_diagnostics", ())
                ),
            ))
            e.spend = _spend(attempt + 1)
            raise
        if getattr(endpoint, "last_finish_reason", None) == "length":
            truncated_any = True
        usage = usage_tokens(getattr(endpoint, "last_usage", None), request, raw)
        tokens_used += usage["prompt_tokens"] + usage["completion_tokens"]
        meter.add(usage)
        raw_ref = blobs.put(raw.encode())
        try:
            candidate = repair.candidate_from_raw(turn, raw)
            reject_model_control_fields(candidate)
            wire_value = contract.validate_value(candidate)
            data = contract.compile(wire_value)
        except (TypeError, ValueError) as e:
            diagnostic = repair.note_invalid(
                turn,
                raw,
                e,
                truncated=(
                    getattr(endpoint, "last_finish_reason", None) == "length"
                ),
            )
            attempt_trace.append(LLMAttempt(
                prompt_ref=prompt_ref,
                raw_ref=raw_ref,
                diagnostic_ref=blobs.put(diagnostic.model_dump_json().encode()),
                attempt=attempt,
                validation_path=diagnostic.path,
                **trace_identity,
                repair_scope=diagnostic.repair_scope,
                tokens=usage["prompt_tokens"] + usage["completion_tokens"],
                ms=int((time.monotonic() - attempt_started) * 1000),
                valid=False,
                output_mechanism=lease.route.output_mechanism,
                transport_attempts=max(
                    1, int(getattr(endpoint, "last_transport_attempts", 1) or 1)
                ),
                transport_diagnostics=list(
                    getattr(endpoint, "last_transport_diagnostics", ())
                ),
            ))
            continue
        attempt_trace.append(LLMAttempt(
            prompt_ref=prompt_ref,
            raw_ref=raw_ref,
            attempt=attempt,
            validation_path=turn.validation_path,
            **trace_identity,
            repair_scope=turn.repair_scope,
            tokens=usage["prompt_tokens"] + usage["completion_tokens"],
            ms=int((time.monotonic() - attempt_started) * 1000),
            valid=True,
            output_mechanism=lease.route.output_mechanism,
            transport_attempts=max(
                1, int(getattr(endpoint, "last_transport_attempts", 1) or 1)
            ),
            transport_diagnostics=list(
                getattr(endpoint, "last_transport_diagnostics", ())
            ),
        ))
        return data, _spend(attempt + 1)
    raise SchemaError(
        "no schema-valid output after bounded repair: "
        + str(repair.last_error)[:500],
        spend=_spend(repair.attempt_count),
    )
