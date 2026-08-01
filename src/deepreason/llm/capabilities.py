"""Deterministic, process-only model capability probes.

Capability measurements describe a concrete transport route.  They are not
epistemic evidence and deliberately have no dependency on the ontology,
adjudicator, or event log.  The setup/``doctor`` path may persist these values;
normal role calls only consume the frozen result.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Callable, Protocol


def _validated_endpoint(value: str) -> str:
    """Apply the canonical, non-echoing RunManifest route boundary."""
    # Local import keeps capability datatypes independent of setup-time
    # manifest compilation while ensuring both paths enforce one validator.
    from deepreason.run_manifest import validate_route_base_url

    return validate_route_base_url(value)


class ProbeEndpoint(Protocol):
    """Small endpoint surface used by the setup-time probe suite."""

    name: str
    model: str
    provider: str

    def complete(self, prompt: str, **kwargs) -> str: ...


@dataclass(frozen=True)
class ModelCapabilities:
    """Measured transport capabilities for one exact model route.

    These fields may select a presentation/transport profile.  They MUST NOT
    be used in a guard, status calculation, warrant, or label computation.
    """

    provider: str
    endpoint: str
    model: str
    revision: str = ""
    native_json_schema: bool = False
    grammar: bool = False
    enum_adherence: float = 0.0
    nested_object_reliability: float = 0.0
    array_reliability: float = 0.0
    long_context_retention: float = 0.0
    max_reliable_output_tokens: int = 0
    stop_sequence_reliable: bool = False
    repair_reliability: float = 0.0
    probe_version: int = 1
    diagnostics: tuple[str, ...] = field(default_factory=tuple)

    @property
    def cache_key(self) -> str:
        identity = json.dumps(
            [self.provider, self.endpoint, self.model, self.revision, self.probe_version],
            separators=(",", ":"),
            ensure_ascii=False,
        )
        return hashlib.sha256(identity.encode()).hexdigest()


class CapabilityCache:
    """Secret-free JSON cache keyed by exact route and model revision."""

    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)

    @staticmethod
    def key(
        provider: str,
        endpoint: str,
        model: str,
        revision: str = "",
        probe_version: int = 1,
    ) -> str:
        endpoint = _validated_endpoint(endpoint)
        identity = json.dumps(
            [provider, endpoint, model, revision, probe_version],
            separators=(",", ":"),
            ensure_ascii=False,
        )
        return hashlib.sha256(identity.encode()).hexdigest()

    def _read(self) -> dict:
        try:
            data = json.loads(self.path.read_text())
        except (FileNotFoundError, OSError, ValueError):
            return {}
        if not isinstance(data, dict):
            return {}
        # Treat every cached route identity as untrusted input. In
        # particular, a safe new entry must never rewrite an older
        # credential-bearing URL back to disk unchanged.
        for value in data.values():
            if isinstance(value, dict) and isinstance(value.get("endpoint"), str):
                _validated_endpoint(value["endpoint"])
        return data

    def get(
        self, provider: str, endpoint: str, model: str, revision: str = ""
    ) -> ModelCapabilities | None:
        endpoint = _validated_endpoint(endpoint)
        value = self._read().get(self.key(provider, endpoint, model, revision))
        if not isinstance(value, dict):
            return None
        try:
            value["diagnostics"] = tuple(value.get("diagnostics") or ())
            return ModelCapabilities(**value)
        except (TypeError, ValueError):
            return None

    def put(self, capabilities: ModelCapabilities) -> None:
        _validated_endpoint(capabilities.endpoint)
        data = self._read()
        value = asdict(capabilities)
        value["diagnostics"] = list(capabilities.diagnostics)
        data[capabilities.cache_key] = value
        self.path.parent.mkdir(parents=True, exist_ok=True)
        # A single deterministic serialization keeps cache diffs inspectable.
        self.path.write_text(json.dumps(data, sort_keys=True, indent=2) + "\n")


@dataclass(frozen=True)
class ProbeCase:
    name: str
    prompt: str
    validate: Callable[[str], bool]
    kwargs: dict = field(default_factory=dict)
    repetitions: int = 1


def _json_value(raw: str):
    from deepreason.llm.repair import parse_one_json_value

    try:
        return parse_one_json_value(raw).value
    except ValueError:
        return None


def deterministic_probe_cases() -> tuple[ProbeCase, ...]:
    """Fixed probes; callers never ask the model to classify itself."""

    schema = {
        "type": "object",
        "additionalProperties": False,
        "required": ["answer"],
        "properties": {
            "answer": {"type": "string", "const": "ok"},
            # Optional/defaulted fields occur throughout canonical role
            # schemas. A provider that accepts only the trivial all-required
            # subset is not reliable for our native fast path.
            "note": {"type": "string", "default": ""},
        },
    }
    nested = {
        "outer": {"inner": {"label": "kept"}},
        "items": [{"id": "x", "enabled": True}, {"id": "y", "enabled": False}],
    }
    marker = "retain-4f92"
    cases = (
        ProbeCase(
            "native_json_schema",
            'Return only {"answer":"ok"}.',
            lambda raw: _json_value(raw) == {"answer": "ok"},
            {"output_mechanism": "native_json_schema", "response_schema": schema},
        ),
        ProbeCase(
            "grammar",
            'Return only {"answer":"ok"}.',
            lambda raw: _json_value(raw) == {"answer": "ok"},
            {"output_mechanism": "grammar", "response_schema": schema},
        ),
        ProbeCase(
            "enum_adherence",
            'Return only JSON: {"choice":"beta"}. choice must be alpha or beta.',
            lambda raw: _json_value(raw) == {"choice": "beta"},
            repetitions=3,
        ),
        ProbeCase(
            "nested_object_reliability",
            "Return only this exact JSON: " + json.dumps(nested, separators=(",", ":")),
            lambda raw: _json_value(raw) == nested,
            repetitions=3,
        ),
        ProbeCase(
            "array_reliability",
            'Return only JSON: {"items":[1,2,3,4,5,6]}.',
            lambda raw: _json_value(raw) == {"items": [1, 2, 3, 4, 5, 6]},
            repetitions=3,
        ),
        ProbeCase(
            "long_context_retention",
            ("Ignore filler and return only JSON containing the marker at the end. "
             + ("filler " * 1800)
             + f' marker={marker}. Required output: {{"marker":"{marker}"}}'),
            lambda raw: _json_value(raw) == {"marker": marker},
            repetitions=3,
        ),
        ProbeCase(
            "stop_sequence_reliable",
            'Return the word READY followed by <END>, then stop.',
            lambda raw: raw.strip() == "READY",
            {"stop": ["<END>"]},
            repetitions=3,
        ),
        ProbeCase(
            "repair_reliability",
            ('Repair only /choice in {"choice":"gamma","keep":7}. '
             'Return the whole JSON with choice="beta" and keep unchanged.'),
            lambda raw: _json_value(raw) == {"choice": "beta", "keep": 7},
            repetitions=3,
        ),
    )
    lengths = (256, 512, 1024, 2048, 4096)
    length_cases = tuple(
        ProbeCase(
            f"output_length_{tokens}",
            (
                f"OUTPUT_LENGTH_PROBE chars={tokens * 4}. Return only JSON with "
                f"one key payload whose value is exactly {tokens * 4} lowercase x characters."
            ),
            lambda raw, count=tokens * 4: (
                isinstance((value := _json_value(raw)), dict)
                and isinstance(value.get("payload"), str)
                and len(value["payload"]) == count
                and set(value["payload"]) == {"x"}
            ),
        )
        for tokens in lengths
    )
    return cases + length_cases


def probe_capabilities(
    endpoint: ProbeEndpoint,
    *,
    revision: str = "",
    cache: CapabilityCache | None = None,
    force: bool = False,
) -> ModelCapabilities:
    """Run the fixed setup-time suite and return secret-free measurements.

    Unsupported mechanism kwargs count as a failed probe; they never trigger a
    fallback call.  Output-length capability may be supplied by a concrete
    endpoint as ``max_reliable_output_tokens`` and otherwise remains unknown.
    """

    provider = str(getattr(endpoint, "provider", "unknown"))
    endpoint_id = _validated_endpoint(str(getattr(endpoint, "name", "")))
    model = str(getattr(endpoint, "model", ""))
    if cache is not None and not force:
        hit = cache.get(provider, endpoint_id, model, revision)
        if hit is not None:
            return hit

    scores: dict[str, float] = {}
    diagnostics: list[str] = []
    for case in deterministic_probe_cases():
        outcomes: list[bool] = []
        for sample in range(case.repetitions):
            try:
                raw = endpoint.complete(case.prompt, **case.kwargs)
                outcomes.append(bool(case.validate(raw)))
            except Exception as exc:  # probe failure is data, never run authority
                outcomes.append(False)
                diagnostics.append(
                    f"{case.name}[{sample}]:{type(exc).__name__}"
                )
        scores[case.name] = sum(outcomes) / len(outcomes)

    caps = ModelCapabilities(
        provider=provider,
        endpoint=endpoint_id,
        model=model,
        revision=revision,
        native_json_schema=scores["native_json_schema"] == 1.0,
        grammar=scores["grammar"] == 1.0,
        enum_adherence=scores["enum_adherence"],
        nested_object_reliability=scores["nested_object_reliability"],
        array_reliability=scores["array_reliability"],
        long_context_retention=scores["long_context_retention"],
        max_reliable_output_tokens=max(
            (
                tokens
                for tokens in (256, 512, 1024, 2048, 4096)
                if scores.get(f"output_length_{tokens}") == 1.0
            ),
            default=0,
        ),
        stop_sequence_reliable=scores["stop_sequence_reliable"] == 1.0,
        repair_reliability=scores["repair_reliability"],
        diagnostics=tuple(diagnostics),
    )
    if cache is not None:
        cache.put(caps)
    return caps
