"""Frozen Tranche-A capability and attached-evidence policies."""

from __future__ import annotations

import hashlib
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from deepreason.canonical import canonical_json

_DIGEST = r"^[0-9a-f]{64}$"
_ALIAS = r"^[A-Z][A-Z0-9_]{0,31}$"


class _PolicyModel(BaseModel):
    model_config = ConfigDict(
        extra="forbid", frozen=True, populate_by_name=True, serialize_by_alias=True
    )


def _finite_json(value: Any, depth: int = 0) -> Any:
    if depth > 12:
        raise ValueError("sealed simulation input exceeds maximum nesting depth")
    if value is None or isinstance(value, (bool, str, int)):
        return value
    if isinstance(value, float):
        if value != value or value in {float("inf"), -float("inf")}:
            raise ValueError("sealed simulation input numbers must be finite")
        return value
    if isinstance(value, list):
        return [_finite_json(item, depth + 1) for item in value]
    if isinstance(value, dict):
        if any(not isinstance(key, str) or not key for key in value):
            raise ValueError("sealed simulation input keys must be nonempty strings")
        return {key: _finite_json(item, depth + 1) for key, item in value.items()}
    raise ValueError("sealed simulation inputs must be finite JSON")


class SimulationInputBindingV1(_PolicyModel):
    alias: str = Field(pattern=_ALIAS)
    description: str = Field(min_length=1, max_length=1_024)
    value: Any
    content_sha256: str = Field(pattern=_DIGEST)

    @field_validator("value", mode="before")
    @classmethod
    def _json_value(cls, value):
        return _finite_json(value)

    @model_validator(mode="after")
    def _identity_matches(self):
        digest = hashlib.sha256(canonical_json(self.value)).hexdigest()
        if digest != self.content_sha256:
            raise ValueError("sealed simulation input digest does not match its value")
        return self


class SimulationCapabilityPolicyV1(_PolicyModel):
    """Complete finite authority for model-proposed local simulations."""

    schema_: Literal["simulation-capability-policy.v1"] = Field(
        "simulation-capability-policy.v1", alias="schema"
    )
    enabled: bool = False
    backend_identity: Literal["simulation-python"] = "simulation-python"
    runner_profile: Literal[
        "simulation.declarative.v1", "simulation.container.v1"
    ] = "simulation.declarative.v1"
    runner_template_identity: Literal[
        "python-numerical-simulation-v1",
        "python-deterministic-sensitivity-v1",
        "python-bandwidth-schedule-v1",
        "python-property-check-v1",
    ] = "python-numerical-simulation-v1"
    python_toolchain_identity: str = Field(default="disabled", min_length=1, max_length=128)
    maximum_simulation_requests: int = Field(default=0, ge=0, le=1_000)
    maximum_simulation_executions: int = Field(default=0, ge=0, le=1_000)
    maximum_proposals_per_turn: int = Field(default=0, ge=0, le=32)
    maximum_generated_code_bytes: int = Field(default=0, ge=0, le=262_144)
    maximum_input_bytes: int = Field(default=0, ge=0, le=8 * 1024 * 1024)
    maximum_output_bytes: int = Field(default=0, ge=0, le=8 * 1024 * 1024)
    maximum_wall_ms: int = Field(default=0, ge=0, le=300_000)
    maximum_memory_bytes: int = Field(default=0, ge=0, le=4 * 1024 * 1024 * 1024)
    maximum_steps: int = Field(default=0, ge=0, le=100_000_000)
    maximum_samples: int = Field(default=0, ge=0, le=1_000_000)
    deterministic_seed_policy: Literal[
        "fixed_manifest", "proposal_declared_bounded"
    ] = "fixed_manifest"
    fixed_seed_set: tuple[int, ...] = ()
    maximum_follow_up_reasoning_turns: int = Field(default=0, ge=0, le=1_000)
    filesystem_policy: Literal["isolated_no_filesystem"] = "isolated_no_filesystem"
    network_policy: Literal["forbidden"] = "forbidden"
    failure_policy: Literal["record_and_continue", "terminal"] = "record_and_continue"
    retry_ceiling: int = Field(default=0, ge=0, le=1)
    accounting_policy: Literal["exact_or_explicitly_unknown"] = (
        "exact_or_explicitly_unknown"
    )
    input_catalog: tuple[SimulationInputBindingV1, ...] = ()

    @field_validator("fixed_seed_set")
    @classmethod
    def _unique_seeds(cls, value):
        if (
            len(value) != len(set(value))
            or len(value) > 256
            or any(
                isinstance(seed, bool)
                or not isinstance(seed, int)
                or not -(2**63) <= seed < 2**63
                for seed in value
            )
        ):
            raise ValueError("fixed simulation seeds must be unique and bounded")
        return tuple(value)

    @field_validator("input_catalog")
    @classmethod
    def _canonical_catalog(cls, value):
        aliases = tuple(item.alias for item in value)
        if aliases != tuple(sorted(aliases)) or len(aliases) != len(set(aliases)):
            raise ValueError("simulation input catalog must be unique and alias-sorted")
        return tuple(value)

    @model_validator(mode="after")
    def _enabled_shape(self):
        positive = (
            self.maximum_simulation_requests,
            self.maximum_simulation_executions,
            self.maximum_proposals_per_turn,
            self.maximum_generated_code_bytes,
            self.maximum_input_bytes,
            self.maximum_output_bytes,
            self.maximum_wall_ms,
            self.maximum_memory_bytes,
            self.maximum_steps,
            self.maximum_samples,
            self.maximum_follow_up_reasoning_turns,
        )
        if not self.enabled:
            if any(positive) or self.fixed_seed_set or self.input_catalog:
                raise ValueError("disabled simulation capability must have zero bounds")
            if self.python_toolchain_identity != "disabled":
                raise ValueError("disabled simulation capability cannot bind a toolchain")
        else:
            if not all(positive):
                raise ValueError("enabled simulation capability requires finite positive bounds")
            if self.maximum_simulation_executions > self.maximum_simulation_requests:
                raise ValueError("simulation executions cannot exceed request authority")
            if self.python_toolchain_identity == "disabled":
                raise ValueError("enabled simulation capability requires a pinned toolchain")
            if self.deterministic_seed_policy == "fixed_manifest":
                if not self.fixed_seed_set:
                    raise ValueError("fixed-manifest seed policy requires frozen seeds")
            elif self.fixed_seed_set:
                raise ValueError("proposal-declared seed policy cannot carry fixed seeds")
        return self

    @property
    def digest(self) -> str:
        return hashlib.sha256(canonical_json(self.model_dump(mode="json"))).hexdigest()


class FrozenEvidenceItemV1(_PolicyModel):
    alias: str = Field(pattern=r"^E[1-9][0-9]{0,3}$")
    title: str = Field(min_length=1, max_length=1_024)
    source_locator: str = Field(min_length=1, max_length=4_096)
    source_class: Literal[
        "primary_paper",
        "official_hardware_documentation",
        "official_implementation",
        "reproducible_benchmark",
        "disputed_measurement",
        "synthetic_assumption",
        "other",
    ]
    content: str = Field(min_length=1, max_length=262_144)
    content_sha256: str = Field(pattern=_DIGEST)
    reliability_note: str | None = Field(default=None, max_length=4_096)

    @model_validator(mode="after")
    def _content_identity(self):
        if hashlib.sha256(self.content.encode("utf-8")).hexdigest() != self.content_sha256:
            raise ValueError("frozen evidence digest does not match excerpt content")
        return self


class FrozenEvidencePolicyV1(_PolicyModel):
    schema_: Literal["frozen-evidence-policy.v1"] = Field(
        "frozen-evidence-policy.v1", alias="schema"
    )
    enabled: bool = False
    maximum_sources: int = Field(default=0, ge=0, le=1_000)
    maximum_excerpt_bytes_per_source: int = Field(default=0, ge=0, le=262_144)
    maximum_total_excerpt_bytes: int = Field(default=0, ge=0, le=4 * 1024 * 1024)
    items: tuple[FrozenEvidenceItemV1, ...] = ()

    @field_validator("items")
    @classmethod
    def _canonical_items(cls, value):
        aliases = tuple(item.alias for item in value)
        numeric = tuple(int(alias[1:]) for alias in aliases)
        if numeric != tuple(sorted(numeric)) or len(aliases) != len(set(aliases)):
            raise ValueError("frozen evidence aliases must be unique and numerically sorted")
        return tuple(value)

    @model_validator(mode="after")
    def _bounded_dossier(self):
        if not self.enabled:
            if any(
                (
                    self.maximum_sources,
                    self.maximum_excerpt_bytes_per_source,
                    self.maximum_total_excerpt_bytes,
                )
            ) or self.items:
                raise ValueError("disabled frozen evidence must have zero bounds")
            return self
        if not all(
            (
                self.maximum_sources,
                self.maximum_excerpt_bytes_per_source,
                self.maximum_total_excerpt_bytes,
            )
        ):
            raise ValueError("enabled frozen evidence requires finite positive bounds")
        if len(self.items) > self.maximum_sources:
            raise ValueError("frozen evidence source count exceeds policy")
        sizes = [len(item.content.encode("utf-8")) for item in self.items]
        if any(size > self.maximum_excerpt_bytes_per_source for size in sizes):
            raise ValueError("frozen evidence excerpt exceeds its per-source bound")
        if sum(sizes) > self.maximum_total_excerpt_bytes:
            raise ValueError("frozen evidence dossier exceeds its total byte bound")
        return self

    @property
    def digest(self) -> str:
        payload = self.model_dump(mode="json")
        return hashlib.sha256(canonical_json(payload)).hexdigest()


class AttachedEvidencePolicyV1(_PolicyModel):
    """Finite packing authority for content held by a bound run input."""

    schema_: Literal["attached-evidence-policy.v1"] = Field(
        "attached-evidence-policy.v1", alias="schema"
    )
    enabled: bool = False
    maximum_sources: int = Field(default=0, ge=0, le=1_000)
    maximum_total_bytes: int = Field(default=0, ge=0, le=64 * 1024 * 1024)
    maximum_excerpt_bytes_per_source: int = Field(default=0, ge=0, le=262_144)
    maximum_sources_per_pack: int = Field(default=0, ge=0, le=1_000)

    @model_validator(mode="after")
    def _finite_shape(self):
        bounds = (
            self.maximum_sources,
            self.maximum_total_bytes,
            self.maximum_excerpt_bytes_per_source,
            self.maximum_sources_per_pack,
        )
        if self.enabled:
            if not all(bounds):
                raise ValueError("enabled attached evidence requires finite positive bounds")
            if self.maximum_sources_per_pack > self.maximum_sources:
                raise ValueError("evidence pack source bound exceeds dossier source bound")
        elif any(bounds):
            raise ValueError("disabled attached evidence must have zero bounds")
        return self

    @property
    def digest(self) -> str:
        return hashlib.sha256(
            canonical_json(self.model_dump(mode="json", by_alias=True))
        ).hexdigest()


class FormalizationCapabilityPolicyV1(_PolicyModel):
    schema_: Literal["formalization-capability-policy.v1"] = Field(
        "formalization-capability-policy.v1", alias="schema"
    )
    enabled: bool = False
    lean_toolchain_identity: str = Field(default="disabled", min_length=1, max_length=128)
    maximum_executions: int = Field(default=0, ge=0, le=1_000)

    @model_validator(mode="after")
    def _finite_shape(self):
        if self.enabled:
            if self.lean_toolchain_identity == "disabled" or not self.maximum_executions:
                raise ValueError("enabled formalization requires a toolchain and finite budget")
        elif self.lean_toolchain_identity != "disabled" or self.maximum_executions:
            raise ValueError("disabled formalization cannot bind authority")
        return self


class ResearchCapabilityPolicyV1(_PolicyModel):
    schema_: Literal["research-capability-policy.v1"] = Field(
        "research-capability-policy.v1", alias="schema"
    )
    enabled: bool = False
    backend_identity: str = Field(default="disabled", min_length=1, max_length=128)
    maximum_requests: int = Field(default=0, ge=0, le=10_000)
    maximum_sources: int = Field(default=0, ge=0, le=10_000)

    @model_validator(mode="after")
    def _finite_shape(self):
        if self.enabled:
            if self.backend_identity == "disabled" or not all(
                (self.maximum_requests, self.maximum_sources)
            ):
                raise ValueError("enabled research requires a backend and finite bounds")
        elif self.backend_identity != "disabled" or any(
            (self.maximum_requests, self.maximum_sources)
        ):
            raise ValueError("disabled research cannot bind authority")
        return self


class InquiryCapabilityPolicyV1(_PolicyModel):
    """The complete, opt-in A-tranche capability topology."""

    schema_: Literal["inquiry-capability-policy.v1"] = Field(
        "inquiry-capability-policy.v1", alias="schema"
    )
    # The policy record remains byte-compatible at schema v1.  RunManifest v6
    # selects the v2 capability *profile* so controller-v3 work cannot be
    # mistaken for controller-v2 authority during replay.
    capability_profile: Literal[
        "inquiry-capabilities.v1", "inquiry-capabilities.v2"
    ] = "inquiry-capabilities.v1"
    attached_evidence: AttachedEvidencePolicyV1 = Field(
        default_factory=AttachedEvidencePolicyV1
    )
    simulation: SimulationCapabilityPolicyV1 = Field(
        default_factory=SimulationCapabilityPolicyV1
    )
    formalization: FormalizationCapabilityPolicyV1 = Field(
        default_factory=FormalizationCapabilityPolicyV1
    )
    research: ResearchCapabilityPolicyV1 = Field(
        default_factory=ResearchCapabilityPolicyV1
    )

    @property
    def digest(self) -> str:
        return hashlib.sha256(
            canonical_json(self.model_dump(mode="json", by_alias=True))
        ).hexdigest()


__all__ = [
    "AttachedEvidencePolicyV1",
    "FormalizationCapabilityPolicyV1",
    "FrozenEvidenceItemV1",
    "FrozenEvidencePolicyV1",
    "InquiryCapabilityPolicyV1",
    "ResearchCapabilityPolicyV1",
    "SimulationCapabilityPolicyV1",
    "SimulationInputBindingV1",
]
