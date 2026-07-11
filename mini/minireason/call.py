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

from pydantic import BaseModel, ValidationError

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


class SchemaError(RuntimeError):
    """Bounded repair retries exhausted without schema-valid output."""

    def __init__(self, message: str, spend: Call | None = None) -> None:
        super().__init__(message)
        self.spend = spend


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
    """Normalize a provider usage block: a truthy-but-partial dict must not
    count as zero spend (parent bug) — fall back to the chars/4 estimate."""
    if usage:
        prompt, completion = usage.get("prompt_tokens"), usage.get("completion_tokens")
        if prompt is not None or completion is not None:
            return {"prompt_tokens": int(prompt or 0), "completion_tokens": int(completion or 0)}
        if usage.get("total_tokens") is not None:
            return {"prompt_tokens": int(usage["total_tokens"]), "completion_tokens": 0}
    return {"prompt_tokens": len(request) // 4, "completion_tokens": len(raw) // 4}


def _extract_json(raw: str) -> str:
    s = raw.strip()
    start, end = s.find("{"), s.rfind("}")
    return s[start:end + 1] if (start >= 0 and end > start) else s


class MockEndpoint:
    """Scripted (or prompt-computed) responses with chars/4 usage, so token
    accounting is testable without network."""

    def __init__(self, responses, name: str = "mock", model: str = "mock") -> None:
        self._fn = responses if callable(responses) else None
        self._responses = None if callable(responses) else list(responses)
        self.name, self.model = name, model
        self.last_usage: dict | None = None
        self.last_finish_reason: str | None = None

    def complete(self, prompt: str) -> str:
        if self._fn is not None:
            response = self._fn(prompt)
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
        self.temperature, self.max_tokens = temperature, max_tokens
        self.json_mode, self.timeout_s = json_mode, timeout_s
        self.last_usage: dict | None = None
        self.last_finish_reason: str | None = None

    def complete(self, prompt: str) -> str:
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
                if e.code not in _RETRYABLE_HTTP:
                    raise EndpointError(f"HTTP {e.code}: {e.reason}") from e
                last = e
            except (urllib.error.URLError, ConnectionError, TimeoutError, OSError,
                    ValueError, KeyError, IndexError, TypeError) as e:
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


def call(endpoint, prompt: str, schema: type[BaseModel], meter: TokenMeter,
         blobs: BlobStore, retry_max: int = 2, role: str = "call") -> tuple[BaseModel, Call]:
    """Schema-enforced completion with a bounded repair loop (error fed
    back; length truncation gets a compression hint, not a blind retry)."""
    schema_json = json.dumps(schema.model_json_schema(), sort_keys=True)
    base = (f"Respond with ONLY a JSON object conforming to this JSON Schema — "
            f"no prose, no code fences:\n{schema_json}\n\n{prompt}")
    started = time.monotonic()
    error, tokens_used, truncated_any, raw_ref = "", 0, False, ""
    prompt_ref = blobs.put(base.encode())

    def _spend(attempts: int) -> Call | None:
        if not tokens_used:
            return None
        return Call(role=role, model=getattr(endpoint, "model", ""),
                    endpoint=getattr(endpoint, "name", ""), prompt_ref=prompt_ref,
                    raw_ref=raw_ref, tokens=tokens_used,
                    ms=int((time.monotonic() - started) * 1000),
                    attempts=attempts, truncated=truncated_any)

    for attempt in range(retry_max + 1):
        try:
            meter.check()  # hard stop BEFORE spending
        except BudgetExceeded as e:
            e.spend = _spend(attempt)  # prior attempts already spent (G1)
            raise
        request = base if not error else (
            base + f"\n\nYour previous output was invalid: {error}\n"
            "Return ONLY a valid JSON object for the schema.")
        # Log the ACTUAL request sent this attempt (replay reconstructs the wire).
        prompt_ref = prompt_ref if not error else blobs.put(request.encode())
        try:
            raw = endpoint.complete(request)
        except EndpointError as e:
            e.spend = _spend(attempt)
            raise
        if getattr(endpoint, "last_finish_reason", None) == "length":
            truncated_any = True
        usage = usage_tokens(getattr(endpoint, "last_usage", None), request, raw)
        tokens_used += usage["prompt_tokens"] + usage["completion_tokens"]
        meter.add(usage)
        raw_ref = blobs.put(raw.encode())
        try:
            data = schema.model_validate_json(_extract_json(raw))
        except (ValidationError, ValueError) as e:
            error = str(e)[:500]
            if getattr(endpoint, "last_finish_reason", None) == "length":
                error = ("your output hit the length limit and was CUT OFF mid-JSON. "
                         "Respond MORE COMPACTLY: fewer/shorter items, terse strings, "
                         "same schema. Original error: " + error)[:500]
            continue
        return data, _spend(attempt + 1)
    raise SchemaError(f"no schema-valid output after retries: {error}",
                      spend=_spend(retry_max + 1))
