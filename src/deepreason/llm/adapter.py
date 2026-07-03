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

from deepreason.llm.endpoints import OpenAICompatEndpoint
from deepreason.llm.roles import TEMPLATES
from deepreason.ontology.event import LLMCall


class SchemaRepairError(RuntimeError):
    """Bounded retries exhausted without schema-valid output."""


def _extract_json(raw: str) -> str:
    s = raw.strip()
    start, end = s.find("{"), s.rfind("}")
    if start >= 0 and end > start:
        return s[start : end + 1]
    return s


class LLMAdapter:
    def __init__(self, endpoints: dict[str, object], blob_store, retry_max: int = 2) -> None:
        self.endpoints = endpoints
        self.blobs = blob_store
        self.retry_max = retry_max

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
    ) -> tuple[BaseModel, LLMCall]:
        """endpoint_index selects within a role's ensemble (§9: the judge
        MUST run on >=2 endpoints from different families)."""
        if role not in self.endpoints:
            raise KeyError(f"no endpoint configured for role {role!r}")
        endpoint = self._resolve(role, endpoint_index)
        import json as _json

        schema = _json.dumps(output_model.model_json_schema(), sort_keys=True)
        prompt = TEMPLATES[role].format(schema=schema, pack=pack)
        prompt_ref = self.blobs.put(prompt.encode())
        started = time.monotonic()
        error = ""
        for attempt in range(self.retry_max + 1):
            request = prompt if not error else (
                prompt + f"\n\nYour previous output was invalid: {error}\n"
                "Return ONLY a valid JSON object for the schema."
            )
            raw = endpoint.complete(request)
            raw_ref = self.blobs.put(raw.encode())
            try:
                data = output_model.model_validate_json(_extract_json(raw))
            except (ValidationError, ValueError) as e:
                error = str(e)[:500]
                continue
            call = LLMCall(
                role=role,
                model=getattr(endpoint, "model", ""),
                endpoint=getattr(endpoint, "name", ""),
                prompt_ref=prompt_ref,
                raw_ref=raw_ref,
                tokens=0,
                ms=int((time.monotonic() - started) * 1000),
                attempts=attempt + 1,
            )
            return data, call
        raise SchemaRepairError(f"role {role}: no schema-valid output after retries: {error}")


def _endpoint_from_spec(spec: dict) -> OpenAICompatEndpoint | None:
    if not isinstance(spec, dict) or not spec.get("endpoint"):
        return None
    api_key_env = spec.get("api_key_env") or ""
    return OpenAICompatEndpoint(
        base_url=spec["endpoint"],
        model=spec.get("model") or "",
        api_key=os.environ.get(api_key_env) if api_key_env else None,
        temperature=spec.get("temperature"),
    )


def build_adapter(config, blob_store) -> LLMAdapter:
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
    return LLMAdapter(endpoints, blob_store, retry_max=config.RETRY_MAX)
