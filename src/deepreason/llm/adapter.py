"""Role -> endpoint routing (spec §9).

Every call stores the rendered prompt and the raw output as blobs and
returns an LLMCall record for the consuming event — replay consumes logged
raws (§0), so nothing downstream depends on live model behavior.
Schema-invalid output => feed the error back, RETRY_MAX bounded retries,
then SchemaRepairError (caller drops the cycle, logged).
"""

import os
import time

from pydantic import BaseModel, ValidationError

from deepreason.llm.endpoints import OpenAICompatEndpoint, resolve_model
from deepreason.llm.roles import TEMPLATES
from deepreason.ontology.event import LLMCall


class SchemaRepairError(RuntimeError):
    """Bounded retries exhausted without schema-valid output."""


def _usage_tokens(usage: dict | None, request: str, raw: str) -> dict:
    """Normalize a provider usage block to prompt/completion token counts.

    Some servers report only ``total_tokens`` (or other partial shapes); a
    truthy-but-partial dict must not count as zero spend against the hard
    budget — fall back to the chars/4 estimate instead.
    """
    if usage:
        prompt = usage.get("prompt_tokens")
        completion = usage.get("completion_tokens")
        if prompt is not None or completion is not None:
            return {
                "prompt_tokens": int(prompt or 0),
                "completion_tokens": int(completion or 0),
            }
        total = usage.get("total_tokens")
        if total is not None:
            return {"prompt_tokens": int(total), "completion_tokens": 0}
    return {
        "prompt_tokens": len(request) // 4,
        "completion_tokens": len(raw) // 4,
    }


def _extract_json(raw: str) -> str:
    s = raw.strip()
    start, end = s.find("{"), s.rfind("}")
    if start >= 0 and end > start:
        return s[start : end + 1]
    return s


class LLMAdapter:
    def __init__(
        self,
        endpoints: dict[str, object],
        blob_store,
        retry_max: int = 2,
        meter=None,
    ) -> None:
        self.endpoints = endpoints
        self.blobs = blob_store
        self.retry_max = retry_max
        self.meter = meter  # TokenMeter: hard provider-wide budget (llm/budget.py)

    def has_role(self, role: str) -> bool:
        return role in self.endpoints

    def ensemble_size(self, role: str) -> int:
        entry = self.endpoints.get(role)
        return len(entry) if isinstance(entry, (list, tuple)) else (1 if entry else 0)

    def _resolve(self, role: str, index: int):
        entry = self.endpoints[role]
        if isinstance(entry, (list, tuple)):
            return entry[index]
        if index:
            raise KeyError(f"role {role!r} has no ensemble endpoint {index}")
        return entry

    def call(
        self,
        role: str,
        pack: str,
        output_model: type[BaseModel],
        endpoint_index: int = 0,
        template_role: str | None = None,
    ) -> tuple[BaseModel, LLMCall]:
        """endpoint_index selects within a role's ensemble (§9: the judge
        MUST run on >=2 endpoints from different families). template_role
        lets an auxiliary contract (e.g. spec generation) reuse a configured
        endpoint with a different prompt template."""
        if role not in self.endpoints:
            raise KeyError(f"no endpoint configured for role {role!r}")
        endpoint = self._resolve(role, endpoint_index)
        import json as _json

        schema = _json.dumps(output_model.model_json_schema(), sort_keys=True)
        prompt = TEMPLATES[template_role or role].format(schema=schema, pack=pack)
        started = time.monotonic()
        error = ""
        tokens_used = 0
        truncated_any = False
        prompt_ref = self.blobs.put(prompt.encode())
        for attempt in range(self.retry_max + 1):
            if self.meter is not None:
                self.meter.check()  # hard stop BEFORE spending (llm/budget.py)
            request = prompt if not error else (
                prompt + f"\n\nYour previous output was invalid: {error}\n"
                "Return ONLY a valid JSON object for the schema."
            )
            # Log the ACTUAL request sent this attempt; repair retries append
            # the error suffix, so the logged prompt must match the raw it
            # produced (replay/audit reconstructs the wire exchange, §0).
            prompt_ref = prompt_ref if not error else self.blobs.put(request.encode())
            raw = endpoint.complete(request)
            if getattr(endpoint, "last_finish_reason", None) == "length":
                truncated_any = True  # process signal for the controller
            usage = _usage_tokens(getattr(endpoint, "last_usage", None), request, raw)
            tokens_used += usage["prompt_tokens"] + usage["completion_tokens"]
            if self.meter is not None:
                self.meter.add(usage)
            raw_ref = self.blobs.put(raw.encode())
            try:
                data = output_model.model_validate_json(_extract_json(raw))
            except (ValidationError, ValueError) as e:
                error = str(e)[:500]
                # A length-truncated response will truncate identically on a
                # blind retry — tell the model to compress instead.
                if getattr(endpoint, "last_finish_reason", None) == "length":
                    error = (
                        "your output hit the length limit and was CUT OFF mid-JSON. "
                        "Respond MORE COMPACTLY: fewer/shorter items, terse strings, "
                        "same schema. Original error: " + error
                    )[:500]
                continue
            call = LLMCall(
                role=role,
                model=getattr(endpoint, "model", ""),
                endpoint=getattr(endpoint, "name", ""),
                prompt_ref=prompt_ref,
                raw_ref=raw_ref,
                tokens=tokens_used,
                ms=int((time.monotonic() - started) * 1000),
                attempts=attempt + 1,
                truncated=truncated_any,
                mean_surprisal=getattr(endpoint, "last_mean_surprisal", None),
            )
            return data, call
        raise SchemaRepairError(f"role {role}: no schema-valid output after retries: {error}")


def _endpoint_from_spec(spec: dict) -> OpenAICompatEndpoint | None:
    """The §15 role table is the model-change plug: endpoint, model,
    provider, reasoning, caps — all config, no call-site edits."""
    if not isinstance(spec, dict) or not spec.get("endpoint"):
        return None
    api_key_env = spec.get("api_key_env") or ""
    api_key = os.environ.get(api_key_env) if api_key_env else None
    model = resolve_model(spec.get("model") or "", spec["endpoint"], api_key)
    return OpenAICompatEndpoint(
        base_url=spec["endpoint"],
        model=model,
        api_key=api_key,
        temperature=spec.get("temperature"),
        max_tokens=spec.get("max_tokens"),
        json_mode=bool(spec.get("json_mode", False)),
        request_logprobs=bool(spec.get("logprobs", False)),
        reasoning=spec.get("reasoning"),
        provider=spec.get("provider"),
    )


def build_adapter(config, blob_store, meter=None) -> LLMAdapter:
    """Build from the §15 role table. Roles with a null endpoint are absent
    (has_role False); a list spec becomes an ensemble (judge, §9)."""
    endpoints: dict[str, object] = {}
    for role, spec in (config.roles or {}).items():
        if isinstance(spec, list):
            built = [e for e in (_endpoint_from_spec(s) for s in spec) if e is not None]
            if built:
                endpoints[role] = built
            continue
        endpoint = _endpoint_from_spec(spec)
        if endpoint is not None:
            endpoints[role] = endpoint
    return LLMAdapter(endpoints, blob_store, retry_max=config.RETRY_MAX, meter=meter)
