"""Compile source configuration into a frozen, replayable run manifest.

YAML and command-line options are setup inputs.  Runtime model calls consume
only the concrete routes in :class:`RunManifest`: ``auto`` sentinels are
resolved once, before the first call, and credentials never enter the file.
The manifest is deliberately process metadata; it has no place in the
artifact ontology or adjudication graph.
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import stat
import tempfile
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Literal
from urllib.parse import urlsplit

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    field_validator,
    model_serializer,
    model_validator,
)

from deepreason.bridge.retry import WorkflowRetryPolicyV1
from deepreason.capabilities.policy import (
    InquiryCapabilityPolicyV1,
    FrozenEvidencePolicyV1,
    SimulationCapabilityPolicyV1,
)
from deepreason.locking import ProcessLock, RUN_MANIFEST_LOCK_NAME
from deepreason.llm.endpoints import DEFAULT_TIMEOUT_S, resolve_model
from deepreason.llm.providers import infer_provider


SCHEMA_VERSION = 1
LATEST_SCHEMA_VERSION = 6
MANIFEST_NAME = "run-manifest.json"
MANIFEST_HASH_NAME = "run-manifest.sha256"
_MAX_MANIFEST_BYTES = 4 * 1024 * 1024
_MAX_MANIFEST_HASH_BYTES = 1_024
_UNRESOLVED_MODELS = {"auto", "auto-alt"}

# Configured endpoint roles. Auxiliary prompt templates such as
# ``batch_critic`` and ``experimenter`` reuse one of these seats and are not
# independently routable roles.
LEGACY_CANONICAL_ROLES = (
    "conjecturer",
    "argumentative_critic",
    "defender",
    "variator",
    "judge",
    "summarizer",
    "synthesizer",
    "vision_critic",
    "property_designer",
    "thesis",
)

# V1/v2 serialized an entry for every role in this exact tuple, including
# inactive roles.  Extending that tuple in-place would therefore change old
# canonical bytes and hashes merely by installing a newer DeepReason wheel.
# The grounded-review seat is available only to manifests that opt into v3.
V3_CANONICAL_ROLES = (*LEGACY_CANONICAL_ROLES, "grounding_reviewer")
CANONICAL_ROLES = LEGACY_CANONICAL_ROLES

_ATTENTION_CHANNELS = (
    "focus",
    "link",
    "cluster",
    "keyword",
    "semantic",
    "recent",
    "loose",
    "dormant",
    "underexposed",
    "exploratory",
    "coverage",
)


class RunManifestError(ValueError):
    """Stable preflight/manifest error suitable for CLI and MCP callers."""

    def __init__(self, code: str, message: str, pointer: str = "") -> None:
        self.code = code
        self.pointer = pointer
        location = f" at {pointer}" if pointer else ""
        super().__init__(f"{code}{location}: {message}")


class RouteSecretError(RuntimeError):
    """A route URL contains credential material that must not be persisted.

    This deliberately does not inherit from ``ValueError``: Pydantic includes
    rejected input values in ordinary validation errors, which would echo the
    very credential this boundary is meant to keep out of logs and manifests.
    """

    code = "ROUTE_URL_CREDENTIAL_FORBIDDEN"
    pointer = "/base_url"

    def __init__(self) -> None:
        super().__init__(
            f"{self.code} at {self.pointer}: route URL must not contain credentials"
        )


def validate_route_base_url(value: str) -> str:
    """Reject credential-bearing URLs without placing their values in errors."""
    try:
        parsed = urlsplit(value)
    except ValueError:
        # General URL syntax belongs to the endpoint implementation.  This
        # check has one narrow job: prevent secrets entering canonical data.
        return value
    if parsed.username is not None or parsed.password is not None:
        raise RouteSecretError()
    # API base URLs are origin/path identifiers. Queries and fragments are not
    # routing identity and are common credential carriers, so accepting any
    # would leave a value-pattern loophole in the no-secrets invariant.
    if parsed.query or parsed.fragment:
        raise RouteSecretError()
    return value


class _FrozenDict(dict):
    """A JSON-serializable dict whose contents cannot change after compile."""

    @staticmethod
    def _blocked(*_args, **_kwargs):
        raise TypeError("RunManifest roles are immutable")

    __setitem__ = _blocked
    __delitem__ = _blocked
    clear = _blocked
    pop = _blocked
    popitem = _blocked
    setdefault = _blocked
    update = _blocked


class Route(BaseModel):
    """One exact provider route, with no credential value."""

    model_config = ConfigDict(
        extra="forbid", frozen=True, hide_input_in_errors=True
    )

    endpoint_id: str = Field(min_length=1)
    base_url: str = Field(min_length=1)
    model_id: str = Field(min_length=1)
    model_revision: str | None = None
    provider: str = Field(min_length=1)
    family: str = Field(min_length=1)
    reasoning: str | int | None = None
    output_mode: Literal["json_object", "text"] = "text"
    output_mechanism: Literal["native_json_schema", "grammar", "json_text"] = "json_text"
    temperature: float | None = None
    max_tokens: int | None = Field(default=None, gt=0)
    timeout_s: int = Field(default=DEFAULT_TIMEOUT_S, gt=0)
    logprobs: bool = False
    # The name of an environment variable is routing metadata, not a secret.
    # The variable's value is looked up only while constructing the endpoint.
    api_key_env: str | None = None

    @field_validator("base_url")
    @classmethod
    def _secret_free_url(cls, value: str) -> str:
        return validate_route_base_url(value)

    @field_validator("api_key_env")
    @classmethod
    def _credential_reference_is_an_env_name(cls, value: str | None) -> str | None:
        if value is not None and not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", value):
            raise ValueError("api_key_env must be a POSIX environment-variable name")
        return value

    @field_validator("model_id")
    @classmethod
    def _concrete_model(cls, value: str) -> str:
        if value in _UNRESOLVED_MODELS:
            raise ValueError("production routes cannot contain auto or auto-alt")
        return value

    def endpoint_spec(self) -> dict[str, Any]:
        """Return the legacy Config role-table shape for this frozen route."""
        return {
            "endpoint_id": self.endpoint_id,
            "endpoint": self.base_url,
            "model": self.model_id,
            "model_revision": self.model_revision,
            "provider": self.provider,
            "family": self.family,
            "reasoning": self.reasoning,
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
            "timeout_s": self.timeout_s,
            "json_mode": self.output_mode == "json_object",
            "output_mechanism": self.output_mechanism,
            "logprobs": self.logprobs,
            "api_key_env": self.api_key_env,
        }


class ToolchainEntry(BaseModel):
    """Resolved, secret-free verifier/program toolchain coordinates."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    id: str = Field(min_length=1)
    runner: Literal["local", "container"]
    executable: str = Field(min_length=1)
    version_output_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    lock_digest: str | None = Field(default=None, pattern=r"^[0-9a-f]{64}$")
    network: Literal[False] = False
    environment: dict[str, str] = Field(default_factory=dict)
    allowed_programs: tuple[str, ...] = ()

    @field_validator("executable")
    @classmethod
    def _resolved_executable(cls, value: str) -> str:
        if value.strip().casefold() in {
            "auto",
            "unresolved",
            "<resolved path or image digest>",
        }:
            raise ValueError("toolchain executable must be resolved before use")
        return value

    @field_validator("environment", mode="after")
    @classmethod
    def _secret_free_environment(cls, value: dict[str, str]):
        secret_markers = ("KEY", "TOKEN", "SECRET", "PASSWORD", "CREDENTIAL")
        if any(marker in key.upper() for key in value for marker in secret_markers):
            raise ValueError("toolchain environment cannot contain credential fields")
        return _FrozenDict(dict(value))


class ScratchPolicy(BaseModel):
    """Resolved, immutable advisory-attention policy for manifest v3."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    enabled: bool
    max_blocks_per_pack: int = Field(gt=0, le=1_000)
    max_guides_per_pack: int = Field(ge=0, le=100)
    semantic_retrieval: bool
    keyword_retrieval: bool
    coverage_enabled: bool
    coverage_slot_every_n_packs: int = Field(gt=0, le=100_000)
    exploratory_fraction: float = Field(ge=0.0, le=1.0)
    underexposed_fraction: float = Field(ge=0.0, le=1.0)
    dormant_after_events: int = Field(ge=0)
    similarity_top_k: int = Field(gt=0, le=10_000)
    similarity_threshold: float | None = None
    guide_max_open_threads: int = Field(ge=0, le=256)
    guide_max_entry_points: int = Field(ge=0, le=256)
    block_role: Literal["conjecturer", "synthesizer"]
    link_role: Literal["synthesizer"]
    guide_role: Literal["summarizer"]
    channel_priority: tuple[str, ...]
    per_channel_limits: dict[str, int]
    embedder_backend: Literal["disabled", "deterministic_hashing", "neural"]
    embedder_model: str | None = None
    embedder_failure_policy: Literal["fallback", "error"]
    fallback_embedder: Literal["deterministic_hashing"] = "deterministic_hashing"

    @field_validator("similarity_threshold")
    @classmethod
    def _finite_similarity_threshold(cls, value: float | None) -> float | None:
        if value is not None and not (-float("inf") < value < float("inf")):
            raise ValueError("similarity_threshold must be finite")
        return value

    @field_validator("embedder_model")
    @classmethod
    def _concrete_embedder_model(cls, value: str | None) -> str | None:
        if value is None:
            return None
        normalized = value.strip()
        if (
            not normalized
            or normalized != value
            or normalized.casefold() in {"auto", "auto-alt", "unresolved"}
        ):
            raise ValueError("embedder model must be one exact concrete identifier")
        return value

    @field_validator("channel_priority", mode="after")
    @classmethod
    def _complete_channel_priority(cls, value: tuple[str, ...]):
        if tuple(value) != _ATTENTION_CHANNELS:
            raise ValueError("channel_priority must contain every channel in frozen order")
        return tuple(value)

    @field_validator("per_channel_limits", mode="after")
    @classmethod
    def _complete_channel_limits(cls, value: dict[str, int]):
        if set(value) != set(_ATTENTION_CHANNELS):
            raise ValueError("per_channel_limits must name every attention channel")
        if any(
            isinstance(limit, bool) or not isinstance(limit, int) or not 0 < limit <= 10_000
            for limit in value.values()
        ):
            raise ValueError("per-channel limits must be integers from 1 through 10000")
        return _FrozenDict(dict(value))

    @model_validator(mode="after")
    def _resolved_policy_is_consistent(self):
        if self.exploratory_fraction + self.underexposed_fraction > 1.0:
            raise ValueError("reserved attention fractions must not exceed one")
        if self.embedder_backend == "neural" and self.embedder_model is None:
            raise ValueError("neural embedder backend requires one exact model")
        if self.embedder_backend != "neural" and self.embedder_model is not None:
            raise ValueError("only the neural embedder backend may name a model")
        if not self.enabled or not self.semantic_retrieval:
            if self.embedder_backend != "disabled":
                raise ValueError("disabled semantic retrieval requires disabled embedder backend")
        elif self.embedder_backend == "disabled":
            raise ValueError("enabled semantic retrieval requires a deterministic backend")
        return self

    def attention_policy(self):
        """Return the canonical C4 policy without leaking manifest-only fields."""

        from deepreason.scratch.attention import AttentionPolicyV1

        return AttentionPolicyV1(
            max_blocks_per_pack=self.max_blocks_per_pack,
            max_guides_per_pack=self.max_guides_per_pack,
            semantic_retrieval=self.semantic_retrieval,
            keyword_retrieval=self.keyword_retrieval,
            coverage_enabled=self.coverage_enabled,
            coverage_slot_every_n_packs=self.coverage_slot_every_n_packs,
            exploratory_fraction=self.exploratory_fraction,
            underexposed_fraction=self.underexposed_fraction,
            dormant_after_events=self.dormant_after_events,
            similarity_top_k=self.similarity_top_k,
            similarity_threshold=self.similarity_threshold,
            guide_max_open_threads=self.guide_max_open_threads,
            guide_max_entry_points=self.guide_max_entry_points,
            channel_priority=self.channel_priority,
            per_channel_limits=self.per_channel_limits,
        )


class BridgePolicy(BaseModel):
    """Resolved two-stage output and repair policy for manifest v3."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    mode: Literal["legacy_thesis", "grounded_two_stage"]
    allow_partial: bool
    allow_abstention: bool
    require_claim_ledger: bool
    require_claim_uses: bool
    grounding_review: bool
    max_schema_repair_attempts: int = Field(ge=0, le=2)
    max_grounding_repair_attempts: int = Field(ge=0, le=8)
    max_ledger_amendments: Literal[1] = 1
    reviewer_seats: Literal[1] = 1
    reviewer_seat: Literal[0] = 0
    output_section_limit: int = Field(gt=0, le=128)
    target_profile: str = Field(
        min_length=1,
        max_length=128,
        pattern=r"^[A-Za-z][A-Za-z0-9_.:-]{0,127}$",
    )
    ledger_role: Literal["summarizer"]
    composer_role: Literal["thesis", "summarizer"]
    reviewer_role: Literal["judge", "grounding_reviewer"]
    grounding_repair_role: Literal["judge", "grounding_reviewer"]

    @model_validator(mode="after")
    def _grounded_contract_is_complete(self):
        if self.mode == "grounded_two_stage" and not all(
            (
                self.allow_partial,
                self.allow_abstention,
                self.require_claim_ledger,
                self.require_claim_uses,
            )
        ):
            raise ValueError(
                "grounded_two_stage requires partial and abstention outcomes, "
                "a claim ledger, and typed claim uses"
            )
        if self.grounding_repair_role != self.reviewer_role:
            raise ValueError(
                "grounding_repair_role must equal the frozen reviewer_role"
            )
        return self

    def workflow_policy(
        self,
        *,
        ledger_contract_version: Literal["v1", "v2", "v3"] = "v1",
        composition_contract_version: Literal["v1", "v2"] | None = None,
    ):
        """Compile the manifest policy into C8's exact orchestration contract."""

        from deepreason.bridge.workflow import BridgeWorkflowPolicy

        if composition_contract_version is None:
            composition_contract_version = (
                "v2" if ledger_contract_version == "v3" else "v1"
            )
        return BridgeWorkflowPolicy(
            grounding_review=self.grounding_review,
            max_ledger_amendments=self.max_ledger_amendments,
            max_grounding_repair_attempts=self.max_grounding_repair_attempts,
            ledger_role=self.ledger_role,
            ledger_contract_version=ledger_contract_version,
            composer_role=self.composer_role,
            composition_contract_version=composition_contract_version,
            reviewer_role=self.reviewer_role,
        )


class SchoolRoleBindingV1(BaseModel):
    """One manifest-owned school-to-seat assignment for v4 execution."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    school_id: str = Field(
        min_length=8,
        max_length=64,
        pattern=r"^school-(0|[1-9][0-9]*)$",
    )
    role: str = Field(
        min_length=1,
        max_length=64,
        pattern=r"^[a-z][a-z0-9_]*$",
    )
    seat: int = Field(ge=0, le=1_023)
    endpoint_id: str = Field(min_length=1, max_length=256)


class SchoolExecutionPolicyV1(BaseModel):
    """Closed route-topology policy; school semantics remain open text."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    mode: Literal["conditioning_only", "route_bound"]
    bindings: tuple[SchoolRoleBindingV1, ...]
    allow_shared: bool
    require_distinct_models: bool
    require_distinct_families: bool

    @field_validator("bindings", mode="after")
    @classmethod
    def _canonical_bindings(cls, value: tuple[SchoolRoleBindingV1, ...]):
        keys = tuple(
            (binding.school_id, binding.role, binding.seat, binding.endpoint_id)
            for binding in value
        )
        if keys != tuple(sorted(keys)) or len(set(keys)) != len(keys):
            raise ValueError("school bindings must be sorted and contain no duplicates")
        return tuple(value)

    @model_validator(mode="after")
    def _mode_is_consistent(self):
        if self.mode == "conditioning_only":
            if self.bindings:
                raise ValueError("conditioning_only cannot carry route bindings")
            if not self.allow_shared:
                raise ValueError("conditioning_only must explicitly allow shared routes")
            if self.require_distinct_models or self.require_distinct_families:
                raise ValueError(
                    "conditioning_only cannot claim model or family route diversity"
                )
        return self


class CriticismPolicyV1(BaseModel):
    """Closed v4 policy for manifest-owned foreign-school criticism.

    The policy describes routing and authority only.  Criticism content stays
    open text and is never interpreted here as a status decision.
    """

    model_config = ConfigDict(extra="forbid", frozen=True)

    minimum_foreign_school_coverage: int = Field(ge=1, le=1_023)
    bindings: tuple[SchoolRoleBindingV1, ...]
    max_batch_size: int = Field(ge=1, le=256)
    target_eligibility: Literal["accepted_school_artifacts"]
    authority: Literal["observe_only", "defended_trial"]
    allow_shared: bool

    @field_validator("bindings", mode="after")
    @classmethod
    def _canonical_bindings(cls, value: tuple[SchoolRoleBindingV1, ...]):
        keys = tuple(
            (binding.school_id, binding.role, binding.seat, binding.endpoint_id)
            for binding in value
        )
        if keys != tuple(sorted(keys)) or len(set(keys)) != len(keys):
            raise ValueError(
                "criticism bindings must be sorted and contain no duplicates"
            )
        return tuple(value)


class ConjectureContextPolicyV1(BaseModel):
    """Bounded advisory-context capability for one conjecture work item."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    mode: Literal["disabled", "harness_only", "harness_plus_model_request"]
    initial_max_blocks: int = Field(ge=0, le=1_000)
    initial_max_guides: int = Field(ge=0, le=100)
    max_context_expansion_requests: int = Field(ge=0, le=8)
    max_extra_blocks: int = Field(ge=0, le=1_000)
    permitted_retrieval_channels: tuple[str, ...]
    coverage_slot_mandatory: bool
    exploration_slot_mandatory: bool

    @field_validator("permitted_retrieval_channels", mode="after")
    @classmethod
    def _canonical_channels(cls, value: tuple[str, ...]):
        unknown = set(value) - set(_ATTENTION_CHANNELS)
        if unknown:
            raise ValueError(
                "unknown conjecture retrieval channels: "
                + ", ".join(sorted(unknown))
            )
        canonical = tuple(channel for channel in _ATTENTION_CHANNELS if channel in value)
        if value != canonical:
            raise ValueError(
                "permitted retrieval channels must be unique and in canonical order"
            )
        return tuple(value)

    @model_validator(mode="after")
    def _mode_is_consistent(self):
        if self.coverage_slot_mandatory and "coverage" not in self.permitted_retrieval_channels:
            raise ValueError("mandatory coverage requires the coverage retrieval channel")
        if (
            self.exploration_slot_mandatory
            and "exploratory" not in self.permitted_retrieval_channels
        ):
            raise ValueError(
                "mandatory exploration requires the exploratory retrieval channel"
            )
        if self.mode == "disabled":
            if any(
                (
                    self.initial_max_blocks,
                    self.initial_max_guides,
                    self.max_context_expansion_requests,
                    self.max_extra_blocks,
                )
            ) or self.permitted_retrieval_channels:
                raise ValueError("disabled conjecture context must have zero limits")
            if self.coverage_slot_mandatory or self.exploration_slot_mandatory:
                raise ValueError("disabled conjecture context cannot require reserved slots")
        elif self.mode == "harness_only":
            if self.max_context_expansion_requests or self.max_extra_blocks:
                raise ValueError("harness_only cannot authorize model context expansion")
        elif not self.max_context_expansion_requests or not self.max_extra_blocks:
            raise ValueError(
                "harness_plus_model_request requires a non-zero expansion allowance"
            )
        return self


class ContractVersionPolicyV1(BaseModel):
    """Repository-owned wire versions selected by a v4 manifest."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    bridge_ledger_wire_contract: Literal["bridge.ledger.v1", "bridge.ledger.v2"]
    conjecturer_turn_contract: Literal[
        "conjecturer.legacy.v1", "conjecturer.turn.v4"
    ]
    control_event_schema: Literal["none", "control.event.v1"]


class ContractVersionPolicyV2(BaseModel):
    """Exact wire contracts selected by an active-inquiry v5 manifest."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    bridge_ledger_wire_contract: Literal["bridge.ledger.v2"] = "bridge.ledger.v2"
    conjecturer_turn_contract: Literal["conjecturer.turn.v5"] = "conjecturer.turn.v5"
    control_event_schema: Literal["control.event.v2"] = "control.event.v2"
    simulation_request_contract: Literal["simulation.request.v1"] = (
        "simulation.request.v1"
    )
    simulation_result_contract: Literal["simulation.result.v1"] = (
        "simulation.result.v1"
    )


class ContractVersionPolicyV3(BaseModel):
    """Exact capability-specialized contracts selected by RunManifest v6."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    bridge_catalog_contract: Literal["bridge.catalog.v3"] = "bridge.catalog.v3"
    bridge_ledger_wire_contract: Literal["bridge.ledger.v3"] = "bridge.ledger.v3"
    bridge_composition_contract: Literal["bridge.composition.v2"] = (
        "bridge.composition.v2"
    )
    conjecturer_turn_contract: Literal["conjecturer.turn.v6"] = "conjecturer.turn.v6"
    batch_critic_contract: Literal["batch-critic.v2"] = "batch-critic.v2"
    control_event_schema: Literal["control.event.v3"] = "control.event.v3"
    simulation_request_contract: Literal["simulation.request.v1"] = (
        "simulation.request.v1"
    )
    simulation_result_contract: Literal["simulation.result.v1"] = (
        "simulation.result.v1"
    )


class ScratchAuthoringPolicyV1(BaseModel):
    """Finite authority for optional model-proposed advisory scratch updates."""

    model_config = ConfigDict(
        extra="forbid", frozen=True, populate_by_name=True, serialize_by_alias=True
    )

    schema_: Literal["scratch-authoring-policy.v1"] = Field(
        "scratch-authoring-policy.v1", alias="schema"
    )
    purpose: Literal["imaginative_workshop"] = "imaginative_workshop"
    epistemic_boundary: Literal["advisory_non_grounding"] = (
        "advisory_non_grounding"
    )
    enabled: bool = False
    maximum_new_blocks_per_turn: int = Field(default=0, ge=0, le=32)
    maximum_revisions_per_turn: int = Field(default=0, ge=0, le=32)
    maximum_links_per_turn: int = Field(default=0, ge=0, le=64)
    maximum_unresolved_questions_per_turn: int = Field(default=0, ge=0, le=32)
    maximum_cluster_suggestions_per_turn: int = Field(default=0, ge=0, le=32)
    maximum_total_bytes: int = Field(default=0, ge=0, le=16 * 1024 * 1024)

    @model_validator(mode="after")
    def _finite_authority(self):
        per_turn = (
            self.maximum_new_blocks_per_turn,
            self.maximum_revisions_per_turn,
            self.maximum_links_per_turn,
            self.maximum_unresolved_questions_per_turn,
            self.maximum_cluster_suggestions_per_turn,
        )
        if self.enabled:
            if not self.maximum_total_bytes or not any(per_turn):
                raise ValueError(
                    "enabled scratch authoring requires a byte budget and at least one allowance"
                )
        elif self.maximum_total_bytes or any(per_turn):
            raise ValueError("disabled scratch authoring must have zero bounds")
        return self


class ControlPlanePolicyV1(BaseModel):
    """Complete opt-in v4 authority boundary with no user-authored program."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    controller_version: Literal["legacy.scheduler.v1", "workflow.controller.v1"]
    mode: Literal["legacy", "shadow", "active_conjecture"]
    workflow_profile: Literal[
        "legacy.scheduler.v1", "conjecture.shadow.v1", "conjecture.active.v1"
    ]
    school_execution: SchoolExecutionPolicyV1
    conjecture_context: ConjectureContextPolicyV1
    workflow_retry: WorkflowRetryPolicyV1
    contract_versions: ContractVersionPolicyV1
    capability_profile: Literal["legacy.v1", "conjecture-control.v1"]

    @model_validator(mode="after")
    def _owned_profile_is_consistent(self):
        if self.mode == "legacy":
            if (
                self.controller_version != "legacy.scheduler.v1"
                or self.workflow_profile != "legacy.scheduler.v1"
                or self.capability_profile != "legacy.v1"
            ):
                raise ValueError("legacy mode requires the complete legacy profile")
            if self.school_execution.mode != "conditioning_only":
                raise ValueError("legacy mode requires conditioning_only school execution")
            if self.conjecture_context.mode != "disabled":
                raise ValueError("legacy mode cannot authorize conjecture context control")
            if self.workflow_retry.max_workflow_retries:
                raise ValueError("legacy mode cannot authorize workflow retries")
            if self.contract_versions != ContractVersionPolicyV1(
                bridge_ledger_wire_contract="bridge.ledger.v1",
                conjecturer_turn_contract="conjecturer.legacy.v1",
                control_event_schema="none",
            ):
                raise ValueError("legacy mode requires the historical contract versions")
        elif self.mode == "shadow":
            if (
                self.controller_version != "workflow.controller.v1"
                or self.workflow_profile != "conjecture.shadow.v1"
                or self.capability_profile != "conjecture-control.v1"
                or self.contract_versions.bridge_ledger_wire_contract
                != "bridge.ledger.v1"
                or self.contract_versions.conjecturer_turn_contract
                != "conjecturer.legacy.v1"
                or self.contract_versions.control_event_schema != "control.event.v1"
            ):
                raise ValueError("shadow mode requires the complete shadow profile")
        elif (
            self.controller_version != "workflow.controller.v1"
            or self.workflow_profile != "conjecture.active.v1"
            or self.capability_profile != "conjecture-control.v1"
            or self.contract_versions.bridge_ledger_wire_contract != "bridge.ledger.v2"
            or self.contract_versions.conjecturer_turn_contract != "conjecturer.turn.v4"
            or self.contract_versions.control_event_schema != "control.event.v1"
        ):
            raise ValueError(
                "active_conjecture requires the v1 controller and new wire contracts"
            )
        return self


class ControlPlanePolicyV2(BaseModel):
    """Manifest-owned authority profile for autonomous inquiry capabilities."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    controller_version: Literal["workflow.controller.v2"] = "workflow.controller.v2"
    mode: Literal["active_inquiry"] = "active_inquiry"
    workflow_profile: Literal["inquiry.active.v1"] = "inquiry.active.v1"
    school_execution: SchoolExecutionPolicyV1
    conjecture_context: ConjectureContextPolicyV1
    workflow_retry: WorkflowRetryPolicyV1
    contract_versions: ContractVersionPolicyV2
    capability_profile: Literal["inquiry-capabilities.v1"] = "inquiry-capabilities.v1"


class ControlPlanePolicyV3(BaseModel):
    """Transactional active-inquiry authority selected only by RunManifest v6."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    controller_version: Literal["workflow.controller.v3"] = "workflow.controller.v3"
    mode: Literal["active_inquiry"] = "active_inquiry"
    workflow_profile: Literal["inquiry.active.v2"] = "inquiry.active.v2"
    school_execution: SchoolExecutionPolicyV1
    conjecture_context: ConjectureContextPolicyV1
    workflow_retry: WorkflowRetryPolicyV1
    contract_versions: ContractVersionPolicyV3
    capability_profile: Literal["inquiry-capabilities.v2"] = "inquiry-capabilities.v2"
    scratch_authoring: ScratchAuthoringPolicyV1 = Field(
        default_factory=ScratchAuthoringPolicyV1
    )


class RunManifest(BaseModel):
    """Canonical, immutable routing and presentation plan for one run."""

    model_config = ConfigDict(
        extra="forbid", frozen=True, hide_input_in_errors=True
    )

    schema_version: Literal[1, 2, 3, 4, 5, 6] = SCHEMA_VERSION
    engine_profile: Literal["mini", "full"] = "full"
    model_profile: Literal["compact", "standard", "frontier"] = "standard"
    workload_profile: Literal["text", "code", "formal", "website"] | None = None
    roles: dict[str, tuple[Route, ...]]
    rubric_policy: Literal["forbid", "require_cross_family"] = "require_cross_family"
    provider_fallback: Literal[False] = False
    concurrency: int = Field(default=1, ge=1)
    pack_profile: str = Field(min_length=1)
    output_profile: str = Field(min_length=1)
    toolchains: tuple[ToolchainEntry, ...] = ()
    budget_policy: dict[str, Any] = Field(default_factory=dict)
    stop_policy: dict[str, Any] = Field(default_factory=dict)
    memory_policy: dict[str, Any] = Field(default_factory=dict)
    scratch_policy: ScratchPolicy | None = None
    bridge_policy: BridgePolicy | None = None
    control_plane_policy: (
        ControlPlanePolicyV1 | ControlPlanePolicyV2 | ControlPlanePolicyV3 | None
    ) = None
    criticism_policy: CriticismPolicyV1 | None = None
    simulation_capability_policy: SimulationCapabilityPolicyV1 | None = None
    frozen_evidence_policy: FrozenEvidencePolicyV1 | None = None
    inquiry_capability_policy: InquiryCapabilityPolicyV1 | None = None
    run_input_digest: str | None = Field(default=None, pattern=r"^[0-9a-f]{64}$")
    source_config_hash: str = Field(pattern=r"^[0-9a-f]{64}$")
    compiled_at: str = Field(min_length=1)
    # Canonical engine configuration without a role table. Runtime
    # reconstruction injects routes solely from ``roles`` and injects v3
    # scratch/bridge settings solely from their typed policies. Thus neither a
    # decoy provider nor a duplicate policy can become a second authority.
    engine_config_json: str = Field(min_length=2, repr=False)

    @field_validator("roles", mode="after")
    @classmethod
    def _freeze_roles(cls, value: dict[str, tuple[Route, ...]]):
        return _FrozenDict({role: tuple(routes) for role, routes in value.items()})

    @field_validator("budget_policy", "stop_policy", "memory_policy", mode="after")
    @classmethod
    def _freeze_policies(cls, value: dict[str, Any]):
        return _FrozenDict(json.loads(json.dumps(value)))

    @field_validator("compiled_at")
    @classmethod
    def _valid_timestamp(cls, value: str) -> str:
        try:
            parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
        except ValueError as error:
            raise ValueError("compiled_at must be an ISO-8601 timestamp") from error
        if parsed.tzinfo is None:
            raise ValueError("compiled_at must include a timezone")
        return value

    @model_serializer(mode="wrap")
    def _versioned_serialization(self, handler):
        payload = handler(self)
        if self.schema_version < 3:
            # Preserve the public model_dump shape of historical manifests as
            # well as their canonical bytes: newly installed v3 defaults are
            # not retroactively fields in a v1/v2 document.
            payload.pop("scratch_policy", None)
            payload.pop("bridge_policy", None)
        if self.schema_version < 4:
            # The v4 control boundary is absent, rather than null, in every
            # historical public dump and canonical document.
            payload.pop("control_plane_policy", None)
        if self.schema_version < 5:
            payload.pop("simulation_capability_policy", None)
            payload.pop("frozen_evidence_policy", None)
            payload.pop("inquiry_capability_policy", None)
            payload.pop("run_input_digest", None)
        else:
            # The abandoned pre-v5 prototype fields remain parse-visible only
            # so its stopped failure roots can be audited. New v5 manifests
            # use the complete inquiry capability policy exclusively.
            if self.simulation_capability_policy is None:
                payload.pop("simulation_capability_policy", None)
            if self.frozen_evidence_policy is None:
                payload.pop("frozen_evidence_policy", None)
        # Criticism is an optional C3 extension.  Absence must preserve the
        # canonical bytes of every pre-C3 manifest, including schema v4.
        if self.criticism_policy is None:
            payload.pop("criticism_policy", None)
        return payload

    @model_validator(mode="after")
    def _production_routes_are_concrete(self):
        if (
            self.schema_version < 4
            and "control_plane_policy" in self.model_fields_set
        ):
            raise ValueError("v1-v3 manifests cannot carry v4 control policy")
        if self.schema_version < 4 and "criticism_policy" in self.model_fields_set:
            raise ValueError("v1-v3 manifests cannot carry v4 criticism policy")
        if self.schema_version < 5 and (
            "simulation_capability_policy" in self.model_fields_set
            or "frozen_evidence_policy" in self.model_fields_set
            or "inquiry_capability_policy" in self.model_fields_set
            or "run_input_digest" in self.model_fields_set
        ):
            raise ValueError("v1-v4 manifests cannot carry v5 capability policy")
        if self.schema_version == 1:
            if self.workload_profile is not None or self.toolchains:
                raise ValueError("v1 manifest cannot carry v2 workload/toolchain fields")
            if self.budget_policy or self.stop_policy or self.memory_policy:
                raise ValueError("v1 manifest cannot carry v2 process policies")
        elif self.workload_profile is None:
            raise ValueError("v2+ manifest requires workload_profile")
        if self.schema_version < 3:
            if self.scratch_policy is not None or self.bridge_policy is not None:
                raise ValueError("v1/v2 manifests cannot carry v3 scratch or bridge policy")
        else:
            if self.scratch_policy is None or self.bridge_policy is None:
                raise ValueError(
                    "v3+ manifest requires scratch_policy and bridge_policy"
                )
            bridge = self.bridge_policy
            if bridge.mode == "grounded_two_stage":
                required = {
                    "ledger": bridge.ledger_role,
                    "composer": bridge.composer_role,
                }
                if bridge.grounding_review:
                    required["reviewer"] = bridge.reviewer_role
                for task, role in required.items():
                    routes = self.roles.get(role, ())
                    if not routes:
                        raise ValueError(
                            f"BRIDGE_{task.upper()}_ROUTE_REQUIRED: "
                            f"grounded bridge requires frozen role {role!r}"
                        )
                if bridge.grounding_review:
                    reviewer_routes = self.roles.get(bridge.reviewer_role, ())
                    if len(reviewer_routes) < bridge.reviewer_seats:
                        raise ValueError(
                            "BRIDGE_REVIEWER_SEATS_MISMATCH: frozen reviewer route "
                            "count is smaller than reviewer_seats"
                        )
            unknown_roles = set(self.roles) - set(V3_CANONICAL_ROLES)
            if unknown_roles:
                raise ValueError(
                    "v3+ manifest contains non-canonical roles: "
                    + ", ".join(sorted(unknown_roles))
                )
            _validate_v3_engine_policy_consistency(self)
        if self.schema_version >= 4:
            if self.control_plane_policy is None:
                raise ValueError("v4+ manifest requires complete control_plane_policy")
            _validate_v4_control_plane_policy(self)
            _validate_v4_criticism_policy(self)
        if self.schema_version == 4:
            if (
                not isinstance(self.control_plane_policy, ControlPlanePolicyV1)
                or
                self.control_plane_policy.mode == "active_conjecture"
                and
                self.control_plane_policy.contract_versions.conjecturer_turn_contract
                != "conjecturer.turn.v4"
            ):
                raise ValueError("v4 manifest requires conjecturer.turn.v4")
        if self.schema_version == 5:
            if (
                not isinstance(self.control_plane_policy, ControlPlanePolicyV2)
                or self.control_plane_policy.mode != "active_inquiry"
            ):
                raise ValueError(
                    "v5 manifest requires the workflow.controller.v2 active-inquiry profile"
                )
            if self.inquiry_capability_policy is None:
                raise ValueError("v5 manifest requires inquiry capability policy")
            if self.run_input_digest is None:
                raise ValueError("v5 manifest requires a bound run-input digest")
            if self.simulation_capability_policy is not None or self.frozen_evidence_policy is not None:
                raise ValueError("v5 manifest cannot use prototype split capability fields")
            _validate_v5_capability_policy(self)
        if self.schema_version == 6:
            if (
                not isinstance(self.control_plane_policy, ControlPlanePolicyV3)
                or self.control_plane_policy.mode != "active_inquiry"
            ):
                raise ValueError(
                    "v6 manifest requires the workflow.controller.v3 transactional profile"
                )
            if self.inquiry_capability_policy is None:
                raise ValueError("v6 manifest requires inquiry capability policy")
            if self.run_input_digest is None:
                raise ValueError("v6 manifest requires a bound run-input digest")
            if (
                self.simulation_capability_policy is not None
                or self.frozen_evidence_policy is not None
            ):
                raise ValueError("v6 manifest cannot use prototype split capability fields")
            _validate_v6_capability_policy(self)
        for role, routes in self.roles.items():
            for index, route in enumerate(routes):
                if route.model_id in _UNRESOLVED_MODELS:
                    raise ValueError(
                        f"roles.{role}.{index}.model_id is unresolved: {route.model_id}"
                    )
        if self.rubric_policy == "require_cross_family":
            families = {
                route.family.strip().casefold()
                for route in self.roles.get("judge", ())
                if route.family.strip()
            }
            if len(families) < 2:
                raise ValueError(
                    "SECOND_JUDGE_FAMILY_REQUIRED: require_cross_family needs "
                    "at least two distinct judge families"
                )
        return self

    def canonical_bytes(self) -> bytes:
        # Alias-aware output keeps nested canonical records on their wire
        # names (for example workflow retry's ``schema`` field). Historical
        # manifest models have no aliases, so their byte contracts are intact.
        payload = self.model_dump(mode="json", by_alias=True)
        if self.schema_version == 1:
            # Preserve the exact canonical v1 byte and hash contract.  The v2
            # fields did not exist and must not appear as serialized defaults.
            for field in (
                "workload_profile",
                "toolchains",
                "budget_policy",
                "stop_policy",
                "memory_policy",
            ):
                payload.pop(field, None)
        if self.schema_version < 3:
            # V3 fields are absent, rather than serialized as null defaults,
            # under both historical byte contracts.
            payload.pop("scratch_policy", None)
            payload.pop("bridge_policy", None)
        if self.schema_version < 4:
            payload.pop("control_plane_policy", None)
        if self.schema_version < 5:
            payload.pop("simulation_capability_policy", None)
            payload.pop("frozen_evidence_policy", None)
            payload.pop("inquiry_capability_policy", None)
            payload.pop("run_input_digest", None)
        else:
            if self.simulation_capability_policy is None:
                payload.pop("simulation_capability_policy", None)
            if self.frozen_evidence_policy is None:
                payload.pop("frozen_evidence_policy", None)
        if self.criticism_policy is None:
            payload.pop("criticism_policy", None)
        return _canonical_json(payload)

    @property
    def sha256(self) -> str:
        return hashlib.sha256(self.canonical_bytes()).hexdigest()


def _canonical_json(value: Any) -> bytes:
    return json.dumps(
        value, sort_keys=True, separators=(",", ":"), ensure_ascii=False
    ).encode("utf-8")


def _source_config_data(config) -> dict[str, Any]:
    if hasattr(config, "model_dump"):
        return config.model_dump(mode="json")
    if not isinstance(config, dict):
        raise TypeError("config must be a deepreason.config.Config or mapping")
    return json.loads(json.dumps(config))


def _versioned_source_config_data(
    config, schema_version: Literal[1, 2, 3, 4, 5, 6]
) -> dict[str, Any]:
    """Normalize newly added defaults out of historical source contracts.

    ``Config.model_dump`` necessarily gains the typed scratch and bridge
    defaults in this tranche.  Those keys did not exist when v1/v2 source
    hashes and ``engine_config_json`` were defined, so retaining them would
    make the same old profile acquire a different identity after an upgrade.
    """

    data = _source_config_data(config)
    if schema_version < 3:
        data.pop("scratchpad", None)
        data.pop("bridge", None)
    return data


def source_config_hash(
    config, *, schema_version: Literal[1, 2, 3, 4, 5, 6] = SCHEMA_VERSION
) -> str:
    """Hash the effective source configuration under one schema contract."""

    data = _versioned_source_config_data(config, schema_version)
    return hashlib.sha256(_canonical_json(data)).hexdigest()


def infer_model_family(model_id: str, provider: str) -> str:
    """Deterministic setup-time family inference, overridable in Config.

    Family is normative for judge ensembles, so unknown identifiers are kept
    distinct by their stable provider/model stem rather than guessed into a
    known family.
    """
    lowered = model_id.lower()
    known = (
        ("deepseek", "deepseek"),
        ("gemma", "gemma"),
        ("claude", "claude"),
        ("qwen", "qwen"),
        ("llama", "llama"),
        ("mistral", "mistral"),
        ("mixtral", "mistral"),
        ("gpt", "openai-gpt"),
        ("o1", "openai-o"),
        ("o3", "openai-o"),
        ("o4", "openai-o"),
    )
    for marker, family in known:
        if marker in lowered:
            return family
    stem = lowered.rsplit("/", 1)[-1].split(":", 1)[0].split("-", 1)[0]
    return f"{provider}:{stem or 'unknown'}"


def _endpoint_identifier(spec: dict[str, Any], provider: str) -> str:
    explicit = str(spec.get("endpoint_id") or "").strip()
    if explicit:
        return explicit
    base_url = str(spec.get("endpoint") or "").rstrip("/")
    digest = hashlib.sha256(base_url.encode()).hexdigest()[:16]
    return f"{provider}:{digest}"


def _route_from_spec(
    spec: dict[str, Any], *, forced_model: str | None = None, capability_cache=None
) -> Route:
    base_url = str(spec.get("endpoint") or "").strip()
    if not base_url:
        raise RunManifestError("ENDPOINT_REQUIRED", "route has no endpoint")
    try:
        validate_route_base_url(base_url)
    except RouteSecretError as error:
        raise RunManifestError(error.code, "route URL must not contain credentials", "/base_url") from error
    provider = str(spec.get("provider") or infer_provider(base_url))
    model = forced_model if forced_model is not None else str(spec.get("model") or "")
    if not model:
        raise RunManifestError("MODEL_REQUIRED", "route has no model")
    api_key_env = str(spec.get("api_key_env") or "") or None
    api_key = os.environ.get(api_key_env) if api_key_env else None
    resolved = resolve_model(model, base_url, api_key)
    if resolved in _UNRESOLVED_MODELS or not resolved:
        raise RunManifestError(
            "UNRESOLVED_MODEL", f"could not resolve concrete model from {model!r}"
        )
    family = str(spec.get("family") or infer_model_family(resolved, provider))
    output_mode = spec.get("output_mode")
    if output_mode is None:
        output_mode = "json_object" if spec.get("json_mode") else "text"
    mechanism = spec.get("output_mechanism")
    if mechanism is None and capability_cache is not None:
        capabilities = capability_cache.get(
            provider, base_url, resolved, str(spec.get("model_revision") or "")
        )
        if capabilities is not None:
            from deepreason.llm.repair import select_output_mechanism

            mechanism = select_output_mechanism(capabilities).value
    return Route(
        endpoint_id=_endpoint_identifier(spec, provider),
        base_url=base_url,
        model_id=resolved,
        model_revision=str(spec.get("model_revision") or "") or None,
        provider=provider,
        family=family,
        reasoning=spec.get("reasoning"),
        output_mode=output_mode,
        # A capability probe or explicit source profile may select a stronger
        # transport. In its absence strict JSON text is the only honest fixed
        # choice; runtime calls must not probe or fall back.
        output_mechanism=mechanism or "json_text",
        temperature=spec.get("temperature"),
        max_tokens=spec.get("max_tokens"),
        timeout_s=spec.get("timeout_s") or DEFAULT_TIMEOUT_S,
        logprobs=bool(spec.get("logprobs", False)),
        api_key_env=api_key_env,
    )


def _configured_seats(config_data: dict[str, Any]):
    for role, configured in (config_data.get("roles") or {}).items():
        if configured is None:
            continue
        seats = configured if isinstance(configured, list) else [configured]
        for index, spec in enumerate(seats):
            if isinstance(spec, dict) and spec.get("endpoint"):
                yield role, index, spec


def _select_single_model_seed(
    config_data: dict[str, Any], model_id: str, *, allowed_roles=CANONICAL_ROLES
) -> dict[str, Any]:
    seats = list(_configured_seats(config_data))
    exact = [
        entry for entry in seats
        if entry[0] in allowed_roles and entry[2].get("model") == model_id
    ]
    if exact:
        # Distinct creative caps/temperatures on roles do not name different
        # provider routes; single-model mode deliberately copies the chosen
        # seed's complete settings to every role. Multiple origins, endpoint
        # identities, credential references, revisions, providers, or
        # families are genuinely ambiguous and must fail closed.
        identities = set()
        for _role, _index, spec in exact:
            route = _route_from_spec(spec, forced_model=model_id)
            identities.add((
                route.endpoint_id,
                route.base_url,
                route.model_id,
                route.model_revision,
                route.provider,
                route.family,
                route.api_key_env,
            ))
        if len(identities) > 1:
            raise RunManifestError(
                "SINGLE_MODEL_ROUTE_AMBIGUOUS",
                "the requested model is bound to multiple distinct configured "
                "routes; make the route unique before compiling",
                "/roles",
            )
        exact.sort(key=lambda item: (item[0] != "conjecturer", item[0], item[1]))
        return exact[0][2]
    raise RunManifestError(
        "SINGLE_MODEL_ROUTE_REQUIRED",
        f"no configured endpoint is explicitly bound to model {model_id!r}; "
        "add one concrete route before compiling",
        "/roles",
    )


def _select_second_judge_spec(
    config_data: dict[str, Any], selector: str, primary_family: str,
    capability_cache=None,
) -> dict[str, Any]:
    matches: list[dict[str, Any]] = []
    for _role, _index, spec in _configured_seats(config_data):
        provider = str(spec.get("provider") or infer_provider(str(spec.get("endpoint") or "")))
        model = str(spec.get("model") or "")
        family = str(spec.get("family") or (
            infer_model_family(model, provider) if model not in _UNRESOLVED_MODELS else ""
        ))
        endpoint_id = _endpoint_identifier(spec, provider)
        if selector in {family, endpoint_id, model, str(spec.get("endpoint") or "")}:
            matches.append(spec)
    if not matches:
        raise RunManifestError(
            "SECOND_JUDGE_ROUTE_NOT_FOUND",
            f"no configured route matches judge-family selector {selector!r}",
            "/roles/judge",
        )
    route = _route_from_spec(matches[0], capability_cache=capability_cache)
    if route.family == primary_family:
        raise RunManifestError(
            "SECOND_JUDGE_FAMILY_REQUIRED",
            f"second judge route is still family {primary_family!r}",
            "/roles/judge",
        )
    return matches[0]


def _source_feature_policies(data: dict[str, Any]):
    """Validate nested source policy even for direct mapping callers."""

    from deepreason.config import BridgeConfig, ScratchpadConfig

    return (
        ScratchpadConfig.model_validate(data.get("scratchpad") or {}),
        BridgeConfig.model_validate(data.get("bridge") or {}),
    )


def _compile_scratch_policy(source, *, model_profile: str, data: dict[str, Any]):
    max_blocks = source.max_blocks_per_pack
    max_guides = source.max_guides_per_pack
    similarity_top_k = source.similarity_top_k
    guide_open_threads = source.guide_max_open_threads
    guide_entry_points = source.guide_max_entry_points
    if model_profile == "compact":
        max_blocks = min(max_blocks, 12)
        max_guides = min(max_guides, 2)
        similarity_top_k = min(similarity_top_k, 12)
        guide_open_threads = min(guide_open_threads, 8)
        guide_entry_points = min(guide_entry_points, 8)

    semantic_active = source.enabled and source.semantic_retrieval
    configured_embedder = data.get("EMBEDDER_MODEL")
    failure_policy = str(data.get("EMBEDDER_FAILURE_POLICY") or "fallback")
    if failure_policy not in {"fallback", "error"}:
        raise RunManifestError(
            "SCRATCH_EMBEDDER_FAILURE_POLICY_INVALID",
            "EMBEDDER_FAILURE_POLICY must be fallback or error",
            "/EMBEDDER_FAILURE_POLICY",
        )
    if semantic_active and configured_embedder:
        embedder_backend = "neural"
        embedder_model = str(configured_embedder)
        if embedder_model in _UNRESOLVED_MODELS or embedder_model == "unresolved":
            raise RunManifestError(
                "SCRATCH_EMBEDDER_MODEL_UNRESOLVED",
                "semantic retrieval requires an exact embedder model or deterministic hashing",
                "/EMBEDDER_MODEL",
            )
    elif semantic_active:
        embedder_backend = "deterministic_hashing"
        embedder_model = None
    else:
        embedder_backend = "disabled"
        embedder_model = None

    per_channel = {channel: max_blocks for channel in _ATTENTION_CHANNELS}
    per_channel["semantic"] = max(1, min(max_blocks, similarity_top_k))
    per_channel["coverage"] = 1
    values = source.model_dump(mode="json")
    values.update(
        max_blocks_per_pack=max_blocks,
        max_guides_per_pack=max_guides,
        similarity_top_k=similarity_top_k,
        guide_max_open_threads=guide_open_threads,
        guide_max_entry_points=guide_entry_points,
        channel_priority=_ATTENTION_CHANNELS,
        per_channel_limits=per_channel,
        embedder_backend=embedder_backend,
        embedder_model=embedder_model,
        embedder_failure_policy=failure_policy,
    )
    return ScratchPolicy(**values)


def _compile_bridge_policy(source, *, model_profile: str):
    output_section_limit = source.output_section_limit
    if model_profile == "compact":
        output_section_limit = min(output_section_limit, 12)
    values = source.model_dump(mode="json")
    values["output_section_limit"] = output_section_limit
    values["grounding_repair_role"] = source.reviewer_role
    return BridgePolicy(**values)


def _effective_source_policy(policy: ScratchPolicy | BridgePolicy) -> dict[str, Any]:
    """Return only keys understood by the typed source Config models."""

    if isinstance(policy, ScratchPolicy):
        excluded = {
            "channel_priority",
            "per_channel_limits",
            "embedder_backend",
            "embedder_model",
            "embedder_failure_policy",
            "fallback_embedder",
        }
    else:
        # reviewer_seats is a source field; reviewer_seat is the derived,
        # fixed seat index for this tranche.
        excluded = {
            "max_ledger_amendments",
            "reviewer_seat",
            "grounding_repair_role",
        }
    return policy.model_dump(mode="json", exclude=excluded)


def _validate_v3_engine_policy_consistency(manifest: RunManifest) -> None:
    """Reject a second or inconsistent v3 policy authority on load.

    ``engine_config_json`` predates typed v3 feature policy. Scratch and bridge
    keys are deliberately absent there and are injected from the immutable
    policies during reconstruction. Recompiling those injected source fields
    also binds shared embedder configuration and compact-profile clamping to
    the exact top-level policy recorded in the manifest.
    """

    try:
        engine_data = json.loads(manifest.engine_config_json)
    except json.JSONDecodeError as error:
        raise ValueError("V3_ENGINE_CONFIG_INVALID: engine config is not JSON") from error
    if not isinstance(engine_data, dict):
        raise ValueError("V3_ENGINE_CONFIG_INVALID: engine config must be an object")
    if engine_data.get("roles") != {}:
        raise ValueError(
            "V3_ENGINE_ROLES_FORBIDDEN: routes must exist only in the typed role matrix"
        )
    duplicates = sorted({"scratchpad", "bridge"}.intersection(engine_data))
    if duplicates:
        raise ValueError(
            "V3_ENGINE_POLICY_DUPLICATE: typed policy cannot also appear in "
            "engine_config_json: " + ", ".join(duplicates)
        )

    scratch_policy = manifest.scratch_policy
    bridge_policy = manifest.bridge_policy
    if scratch_policy is None or bridge_policy is None:  # guarded by caller
        raise ValueError("V3_POLICY_REQUIRED: missing scratch or bridge policy")
    reconstructed = dict(engine_data)
    reconstructed["scratchpad"] = _effective_source_policy(scratch_policy)
    reconstructed["bridge"] = _effective_source_policy(bridge_policy)

    from deepreason.config import Config

    try:
        config = Config.model_validate(reconstructed)
    except ValueError as error:
        raise ValueError(
            "V3_ENGINE_CONFIG_INVALID: engine config cannot reconstruct Config"
        ) from error
    normalized = config.model_dump(mode="json")
    expected_scratch = _compile_scratch_policy(
        config.scratchpad,
        model_profile=manifest.model_profile,
        data=normalized,
    )
    expected_bridge = _compile_bridge_policy(
        config.bridge,
        model_profile=manifest.model_profile,
    )
    if expected_scratch != scratch_policy or expected_bridge != bridge_policy:
        raise ValueError(
            "V3_ENGINE_POLICY_MISMATCH: engine configuration and typed policy differ"
        )


def _normalized_model_identity(route: Route) -> tuple[str, str, str]:
    return (
        route.provider.strip().casefold(),
        route.model_id.strip().casefold(),
        (route.model_revision or "").strip().casefold(),
    )


def _validate_v4_control_plane_policy(manifest: RunManifest) -> None:
    """Bind every route-bound school assignment to the frozen role matrix."""

    policy = manifest.control_plane_policy
    if policy is None:  # guarded by the caller; keeps this helper total.
        raise ValueError("V4_CONTROL_POLICY_REQUIRED")
    school_policy = policy.school_execution
    if school_policy.mode == "conditioning_only":
        return

    try:
        engine_data = json.loads(manifest.engine_config_json)
    except json.JSONDecodeError as error:  # also checked by the v3 policy layer
        raise ValueError("V4_ENGINE_CONFIG_INVALID") from error
    school_count = engine_data.get("N_SCHOOLS")
    if isinstance(school_count, bool) or not isinstance(school_count, int):
        raise ValueError("V4_SCHOOL_COUNT_INVALID: N_SCHOOLS must be an integer")
    if school_count < 0:
        raise ValueError("V4_SCHOOL_COUNT_INVALID: N_SCHOOLS cannot be negative")
    expected_schools = {f"school-{index}" for index in range(school_count)}

    by_school_role: dict[tuple[str, str], SchoolRoleBindingV1] = {}
    resolved: list[tuple[SchoolRoleBindingV1, Route]] = []
    for binding in school_policy.bindings:
        key = (binding.school_id, binding.role)
        if key in by_school_role:
            raise ValueError(
                "V4_SCHOOL_BINDING_DUPLICATE: one school-role pair has multiple bindings"
            )
        by_school_role[key] = binding
        if binding.school_id not in expected_schools:
            raise ValueError(
                f"V4_SCHOOL_UNKNOWN: no configured school {binding.school_id!r}"
            )
        if binding.role not in manifest.roles:
            raise ValueError(
                f"V4_SCHOOL_ROLE_UNKNOWN: no frozen role {binding.role!r}"
            )
        if binding.role != "conjecturer":
            raise ValueError(
                "V4_SCHOOL_ROLE_UNSUPPORTED: v4 initially binds conjecturer only"
            )
        routes = manifest.roles[binding.role]
        if binding.seat >= len(routes):
            raise ValueError(
                "V4_SCHOOL_SEAT_OUT_OF_RANGE: binding does not name a frozen route"
            )
        route = routes[binding.seat]
        if binding.endpoint_id != route.endpoint_id:
            raise ValueError(
                "V4_SCHOOL_ENDPOINT_MISMATCH: endpoint_id does not match the frozen seat"
            )
        resolved.append((binding, route))

    expected_bindings = {(school, "conjecturer") for school in expected_schools}
    actual_bindings = set(by_school_role)
    if actual_bindings != expected_bindings:
        missing = sorted(expected_bindings - actual_bindings)
        extra = sorted(actual_bindings - expected_bindings)
        detail = []
        if missing:
            detail.append("missing " + ", ".join(f"{school}/{role}" for school, role in missing))
        if extra:
            detail.append("extra " + ", ".join(f"{school}/{role}" for school, role in extra))
        raise ValueError(
            "V4_SCHOOL_BINDING_INCOMPLETE: " + "; ".join(detail)
        )

    assigned_seats = [(binding.role, binding.seat) for binding, _route in resolved]
    if not school_policy.allow_shared and len(set(assigned_seats)) != len(assigned_seats):
        raise ValueError(
            "V4_SCHOOL_SHARED_SEAT_FORBIDDEN: allow_shared is false"
        )
    if school_policy.require_distinct_models:
        models = {_normalized_model_identity(route) for _binding, route in resolved}
        if len(models) != len(resolved):
            raise ValueError(
                "V4_SCHOOL_DISTINCT_MODEL_REQUIRED: bound schools share a model"
            )
    if school_policy.require_distinct_families:
        families = {route.family.strip().casefold() for _binding, route in resolved}
        if len(families) != len(resolved):
            raise ValueError(
                "V4_SCHOOL_DISTINCT_FAMILY_REQUIRED: bound schools share a family"
            )


def _validate_v4_criticism_policy(manifest: RunManifest) -> None:
    """Bind foreign critics to the frozen role matrix and trial topology."""

    policy = manifest.criticism_policy
    if policy is None:
        return
    control = manifest.control_plane_policy
    if control is None or control.mode not in {"active_conjecture", "active_inquiry"}:
        raise ValueError(
            "V4_CRITICISM_ACTIVE_REQUIRED: criticism policy requires active_conjecture"
        )
    try:
        engine_data = json.loads(manifest.engine_config_json)
    except json.JSONDecodeError as error:
        raise ValueError("V4_ENGINE_CONFIG_INVALID") from error
    school_count = engine_data.get("N_SCHOOLS")
    if isinstance(school_count, bool) or not isinstance(school_count, int):
        raise ValueError("V4_SCHOOL_COUNT_INVALID: N_SCHOOLS must be an integer")
    if school_count < 0:
        raise ValueError("V4_SCHOOL_COUNT_INVALID: N_SCHOOLS cannot be negative")
    if policy.minimum_foreign_school_coverage > max(0, school_count - 1):
        raise ValueError(
            "V4_CRITICISM_FOREIGN_COVERAGE_IMPOSSIBLE: minimum coverage exceeds "
            "the number of foreign schools"
        )

    expected_schools = {f"school-{index}" for index in range(school_count)}
    by_school: dict[str, SchoolRoleBindingV1] = {}
    resolved: list[tuple[SchoolRoleBindingV1, Route]] = []
    critic_routes = manifest.roles.get("argumentative_critic", ())
    for binding in policy.bindings:
        if binding.school_id in by_school:
            raise ValueError(
                "V4_CRITICISM_BINDING_DUPLICATE: one school has multiple critic bindings"
            )
        by_school[binding.school_id] = binding
        if binding.school_id not in expected_schools:
            raise ValueError(
                f"V4_CRITICISM_SCHOOL_UNKNOWN: no configured school {binding.school_id!r}"
            )
        if binding.role != "argumentative_critic":
            raise ValueError(
                "V4_CRITICISM_ROLE_UNSUPPORTED: bindings must name argumentative_critic"
            )
        if binding.seat >= len(critic_routes):
            raise ValueError(
                "V4_CRITICISM_SEAT_OUT_OF_RANGE: binding does not name a frozen route"
            )
        route = critic_routes[binding.seat]
        if binding.endpoint_id != route.endpoint_id:
            raise ValueError(
                "V4_CRITICISM_ENDPOINT_MISMATCH: endpoint_id does not match the frozen seat"
            )
        resolved.append((binding, route))

    actual_schools = set(by_school)
    if actual_schools != expected_schools:
        missing = sorted(expected_schools - actual_schools)
        extra = sorted(actual_schools - expected_schools)
        detail = []
        if missing:
            detail.append("missing " + ", ".join(missing))
        if extra:
            detail.append("extra " + ", ".join(extra))
        raise ValueError(
            "V4_CRITICISM_BINDING_INCOMPLETE: " + "; ".join(detail)
        )

    assigned_seats = [(binding.role, binding.seat) for binding, _route in resolved]
    if not policy.allow_shared and len(set(assigned_seats)) != len(assigned_seats):
        raise ValueError(
            "V4_CRITICISM_SHARED_SEAT_FORBIDDEN: allow_shared is false"
        )

    if policy.authority == "defended_trial":
        if not manifest.roles.get("defender"):
            raise ValueError(
                "V4_CRITICISM_DEFENDER_REQUIRED: defended_trial requires a defender route"
            )
        judge_routes = manifest.roles.get("judge", ())
        judge_families = {
            route.family.strip().casefold()
            for route in judge_routes
            if route.family.strip()
        }
        if len(judge_routes) < 2 or len(judge_families) < 2:
            raise ValueError(
                "V4_CRITICISM_CROSS_FAMILY_JUDGES_REQUIRED: defended_trial requires "
                "two frozen judge seats from distinct families"
            )


def _validate_v5_capability_policy(manifest: RunManifest) -> None:
    """Validate the complete, finite Tranche-A capability topology."""

    capabilities = manifest.inquiry_capability_policy
    if capabilities is None:
        raise ValueError("V5_CAPABILITY_POLICY_REQUIRED")
    control = manifest.control_plane_policy
    if not isinstance(control, ControlPlanePolicyV2):
        raise ValueError("V5_ACTIVE_INQUIRY_REQUIRED")
    if capabilities.capability_profile != control.capability_profile:
        raise ValueError("V5_CAPABILITY_PROFILE_MISMATCH")
    if capabilities.formalization.enabled:
        raise ValueError(
            "V5_FORMALIZATION_UNAVAILABLE: Tranche A cannot enable formalization"
        )
    if capabilities.research.enabled:
        raise ValueError("V5_RESEARCH_UNAVAILABLE: Tranche A cannot enable research")
    policy = capabilities.simulation
    if not policy.enabled:
        return
    matches = tuple(
        toolchain
        for toolchain in manifest.toolchains
        if toolchain.id == policy.python_toolchain_identity
    )
    if len(matches) != 1:
        raise ValueError(
            "V5_SIMULATION_TOOLCHAIN_REQUIRED: policy must bind one frozen toolchain"
        )
    toolchain = matches[0]
    required_runner = (
        "container" if policy.runner_profile == "simulation.container.v1" else "local"
    )
    if toolchain.runner != required_runner or toolchain.network is not False:
        raise ValueError(
            "V5_SIMULATION_TOOLCHAIN_UNSAFE: runner profile and frozen toolchain differ"
        )


def _validate_v6_capability_policy(manifest: RunManifest) -> None:
    """Validate v6 capability authority without weakening the v5 topology."""

    capabilities = manifest.inquiry_capability_policy
    if capabilities is None:
        raise ValueError("V6_CAPABILITY_POLICY_REQUIRED")
    control = manifest.control_plane_policy
    if not isinstance(control, ControlPlanePolicyV3):
        raise ValueError("V6_TRANSACTIONAL_INQUIRY_REQUIRED")
    if capabilities.capability_profile != control.capability_profile:
        raise ValueError("V6_CAPABILITY_PROFILE_MISMATCH")
    if capabilities.formalization.enabled:
        raise ValueError("V6_FORMALIZATION_UNAVAILABLE")
    if capabilities.research.enabled:
        raise ValueError("V6_RESEARCH_UNAVAILABLE")
    if (
        manifest.criticism_policy is not None
        and manifest.criticism_policy.authority == "defended_trial"
    ):
        raise ValueError(
            "V6_DEFENDED_TRIAL_TRANSACTION_CONTRACT_REQUIRED: "
            "defender and judge calls are not yet transaction-authorized"
        )
    policy = capabilities.simulation
    if not policy.enabled:
        return
    matches = tuple(
        toolchain
        for toolchain in manifest.toolchains
        if toolchain.id == policy.python_toolchain_identity
    )
    if len(matches) != 1:
        raise ValueError(
            "V6_SIMULATION_TOOLCHAIN_REQUIRED: policy must bind one frozen toolchain"
        )
    toolchain = matches[0]
    required_runner = (
        "container" if policy.runner_profile == "simulation.container.v1" else "local"
    )
    if toolchain.runner != required_runner or toolchain.network is not False:
        raise ValueError(
            "V6_SIMULATION_TOOLCHAIN_UNSAFE: runner profile and frozen toolchain differ"
        )


def compile_run_manifest(
    config,
    *,
    engine_profile: Literal["mini", "full"] | None = None,
    model_profile: Literal["compact", "standard", "frontier"] | None = None,
    single_model: str | None = None,
    judge_family: str | None = None,
    rubric_policy: Literal["forbid", "require_cross_family"] = "require_cross_family",
    concurrency: int | None = None,
    compiled_at: str | None = None,
    capability_cache=None,
    schema_version: Literal[1, 2, 3, 4, 5, 6] = SCHEMA_VERSION,
    workload_profile: Literal["text", "code", "formal", "website"] | None = None,
    pack_profile: str | None = None,
    output_profile: str | None = None,
    toolchains: tuple[ToolchainEntry, ...] = (),
    budget_policy: dict[str, Any] | None = None,
    stop_policy: dict[str, Any] | None = None,
    memory_policy: dict[str, Any] | None = None,
    control_plane_policy: (
        ControlPlanePolicyV1 | ControlPlanePolicyV2 | ControlPlanePolicyV3 | None
    ) = None,
    criticism_policy: CriticismPolicyV1 | None = None,
    inquiry_capability_policy: InquiryCapabilityPolicyV1 | None = None,
    run_input_digest: str | None = None,
    # Prototype-only arguments are retained as explicit rejections so callers
    # receive a stable migration error rather than silently losing authority.
    simulation_capability_policy: SimulationCapabilityPolicyV1 | None = None,
    frozen_evidence_policy: FrozenEvidencePolicyV1 | None = None,
) -> RunManifest:
    """Resolve and freeze the role matrix before any role-model call.

    In single-model mode only the route explicitly carrying ``single_model``
    is consulted. Other provider entries are not discovered or used.
    """
    explicit_config_profile = (
        "model_profile" in getattr(config, "model_fields_set", set())
        if not isinstance(config, dict)
        else "model_profile" in config
    )
    data = _source_config_data(config)
    scratch_source, bridge_source = _source_feature_policies(data)
    if schema_version < 4 and control_plane_policy is not None:
        raise RunManifestError(
            "CONTROL_PLANE_MANIFEST_V4_REQUIRED",
            "control_plane_policy requires RunManifest schema v4+",
            "/control_plane_policy",
        )
    if schema_version < 4 and criticism_policy is not None:
        raise RunManifestError(
            "CRITICISM_MANIFEST_V4_REQUIRED",
            "criticism_policy requires RunManifest schema v4",
            "/criticism_policy",
        )
    if schema_version >= 4 and control_plane_policy is None:
        raise RunManifestError(
            "CONTROL_PLANE_POLICY_REQUIRED",
            "schema v4+ requires a complete control_plane_policy",
            "/control_plane_policy",
        )
    resolved_control_policy = None
    if control_plane_policy is not None:
        control_model = (
            ControlPlanePolicyV3
            if schema_version == 6
            else ControlPlanePolicyV2
            if schema_version == 5
            else ControlPlanePolicyV1
        )
        resolved_control_policy = control_model.model_validate(control_plane_policy)
    resolved_criticism_policy = (
        CriticismPolicyV1.model_validate(criticism_policy)
        if criticism_policy is not None
        else None
    )
    if schema_version < 5 and (
        simulation_capability_policy is not None
        or frozen_evidence_policy is not None
        or inquiry_capability_policy is not None
        or run_input_digest is not None
    ):
        raise RunManifestError(
            "CAPABILITY_MANIFEST_V5_REQUIRED",
            "simulation and frozen evidence policies require RunManifest schema v5",
            "/simulation_capability_policy",
        )
    if schema_version >= 5 and (
        simulation_capability_policy is not None or frozen_evidence_policy is not None
    ):
        raise RunManifestError(
            "V5_PROTOTYPE_CAPABILITY_POLICY_FORBIDDEN",
            "use one InquiryCapabilityPolicyV1 instead of split prototype policies",
            "/inquiry_capability_policy",
        )
    if inquiry_capability_policy is not None:
        resolved_inquiry_policy = InquiryCapabilityPolicyV1.model_validate(
            inquiry_capability_policy
        )
    elif schema_version == 6:
        resolved_inquiry_policy = InquiryCapabilityPolicyV1(
            capability_profile="inquiry-capabilities.v2"
        )
    elif schema_version == 5:
        resolved_inquiry_policy = InquiryCapabilityPolicyV1()
    else:
        resolved_inquiry_policy = None
    if schema_version >= 5 and run_input_digest is None:
        raise RunManifestError(
            "RUN_INPUT_DIGEST_REQUIRED",
            "schema v5+ requires an exact version-appropriate run-input digest",
            "/run_input_digest",
        )
    if (
        resolved_criticism_policy is not None
        and resolved_control_policy is not None
        and resolved_control_policy.mode not in {"active_conjecture", "active_inquiry"}
    ):
        raise RunManifestError(
            "CRITICISM_ACTIVE_CONJECTURE_REQUIRED",
            "criticism_policy requires active_conjecture control mode",
            "/criticism_policy",
        )
    if schema_version < 3 and scratch_source.enabled:
        raise RunManifestError(
            "SCRATCH_MANIFEST_V3_REQUIRED",
            "scratchpad.enabled requires RunManifest schema v3",
            "/scratchpad/enabled",
        )
    if schema_version < 3 and bridge_source.mode == "grounded_two_stage":
        raise RunManifestError(
            "GROUNDED_BRIDGE_MANIFEST_V3_REQUIRED",
            "grounded_two_stage requires RunManifest schema v3",
            "/bridge/mode",
        )
    if schema_version >= 2 and workload_profile is None:
        raise RunManifestError(
            "WORKLOAD_PROFILE_REQUIRED",
            "schema v2+ requires a text, code, formal, or website workload profile",
            "/workload_profile",
        )
    # This must precede route resolution: a rejected authority policy cannot
    # spend an endpoint/model-discovery call merely to learn that it is unsafe.
    _preflight_text_authority(config, schema_version, workload_profile)
    engine_profile = engine_profile or data.get("engine_profile") or "full"
    if model_profile is None:
        model_profile = data.get("model_profile") or "standard"
        # A doctor result recommends presentation only. It may select the
        # default profile, never a route or an epistemic policy, and an
        # explicit config/CLI profile always wins.
        if capability_cache is not None and not explicit_config_profile:
            try:
                seed = (
                    _select_single_model_seed(
                        data,
                        single_model,
                        allowed_roles=(
                            V3_CANONICAL_ROLES
                            if schema_version >= 3
                            else LEGACY_CANONICAL_ROLES
                        ),
                    )
                    if single_model
                    else next(
                        spec for role, _index, spec in _configured_seats(data)
                        if role in (
                            V3_CANONICAL_ROLES
                            if schema_version >= 3
                            else LEGACY_CANONICAL_ROLES
                        )
                    )
                )
            except (RunManifestError, StopIteration):
                seed = None
            if seed is not None:
                base_url = str(seed.get("endpoint") or "")
                provider = str(seed.get("provider") or infer_provider(base_url))
                model_id = single_model or str(seed.get("model") or "")
                if model_id not in _UNRESOLVED_MODELS:
                    capabilities = capability_cache.get(
                        provider, base_url, model_id,
                        str(seed.get("model_revision") or ""),
                    )
                    if capabilities is not None:
                        from deepreason.llm.profiles import select_profile

                        model_profile = select_profile(capabilities).name.value
    role_names = (
        V3_CANONICAL_ROLES if schema_version >= 3 else LEGACY_CANONICAL_ROLES
    )
    configured_roles = {
        role for role, _index, _spec in _configured_seats(data)
        if role in role_names
    }
    roles: dict[str, tuple[Route, ...]] = {role: () for role in role_names}

    if schema_version >= 3 and bridge_source.mode == "grounded_two_stage":
        required_roles = {
            "ledger": bridge_source.ledger_role,
            "composer": bridge_source.composer_role,
        }
        if bridge_source.grounding_review:
            required_roles["reviewer"] = bridge_source.reviewer_role
        for task, role in required_roles.items():
            if role not in configured_roles:
                raise RunManifestError(
                    f"BRIDGE_{task.upper()}_ROUTE_REQUIRED",
                    f"grounded bridge requires an explicit {role!r} route",
                    f"/roles/{role}",
                )

    if single_model:
        if single_model in _UNRESOLVED_MODELS:
            raise RunManifestError(
                "SINGLE_MODEL_MUST_BE_CONCRETE", "--single-model cannot be auto or auto-alt"
            )
        seed = _select_single_model_seed(
            data, single_model, allowed_roles=role_names
        )
        exact = _route_from_spec(
            seed, forced_model=single_model, capability_cache=capability_cache
        )
        for role in configured_roles:
            # One exact route is copied to every active role. Ensembles are
            # not inferred from another provider or model.
            roles[role] = (exact,)
        if "judge" in configured_roles and judge_family:
            second_spec = _select_second_judge_spec(
                data, judge_family, exact.family, capability_cache=capability_cache
            )
            roles["judge"] = (
                exact, _route_from_spec(second_spec, capability_cache=capability_cache)
            )
    else:
        grouped: dict[str, list[Route]] = {role: [] for role in role_names}
        for role, _index, spec in _configured_seats(data):
            if role not in role_names:
                continue
            grouped.setdefault(role, []).append(
                _route_from_spec(spec, capability_cache=capability_cache)
            )
        roles = {role: tuple(grouped.get(role, ())) for role in role_names}

    if rubric_policy == "require_cross_family":
        families = {
            route.family.strip().casefold()
            for route in roles.get("judge", ())
            if route.family.strip()
        }
        if len(families) < 2:
            raise RunManifestError(
                "SECOND_JUDGE_FAMILY_REQUIRED",
                "rubric workloads require at least two frozen judge families; "
                "supply --judge-family or use --rubric-policy forbid only for "
                "program/predicate workloads",
                "/roles/judge",
            )

    if concurrency is None:
        from deepreason.llm.profiles import get_profile

        concurrency = get_profile(model_profile).default_concurrency
    if concurrency < 1:
        raise RunManifestError("INVALID_CONCURRENCY", "concurrency must be at least 1")

    scratch_policy = (
        _compile_scratch_policy(scratch_source, model_profile=model_profile, data=data)
        if schema_version >= 3
        else None
    )
    bridge_policy = (
        _compile_bridge_policy(bridge_source, model_profile=model_profile)
        if schema_version >= 3
        else None
    )

    engine_config = _versioned_source_config_data(data, schema_version)
    engine_config["roles"] = {}
    if schema_version >= 3:
        # Typed v3 policy is canonical and must not be duplicated inside the
        # legacy engine-config envelope.
        engine_config.pop("scratchpad", None)
        engine_config.pop("bridge", None)
    stamp = compiled_at or datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    default_pack_profiles = {
        "text": "reasoning.text.v1",
        "code": "reasoning.code.v1",
        "formal": "reasoning.formal.v1",
        "website": "website.v1",
    }
    manifest_values: dict[str, Any] = {}
    if schema_version >= 4:
        manifest_values["control_plane_policy"] = resolved_control_policy
        if resolved_criticism_policy is not None:
            manifest_values["criticism_policy"] = resolved_criticism_policy
    if schema_version >= 5:
        manifest_values["inquiry_capability_policy"] = resolved_inquiry_policy
        manifest_values["run_input_digest"] = run_input_digest
    return RunManifest(
        schema_version=schema_version,
        engine_profile=engine_profile,
        model_profile=model_profile,
        workload_profile=workload_profile,
        roles=roles,
        rubric_policy=rubric_policy,
        concurrency=concurrency,
        pack_profile=(
            pack_profile
            or (default_pack_profiles[workload_profile] if workload_profile else model_profile)
        ),
        output_profile=(
            output_profile
            or (
                "compact.v2"
                if schema_version >= 2 and model_profile == "compact"
                else model_profile
            )
        ),
        toolchains=toolchains,
        budget_policy=budget_policy or {},
        stop_policy=stop_policy or {},
        memory_policy=memory_policy or {},
        scratch_policy=scratch_policy,
        bridge_policy=bridge_policy,
        source_config_hash=source_config_hash(data, schema_version=schema_version),
        compiled_at=stamp,
        engine_config_json=_canonical_json(engine_config).decode("utf-8"),
        **manifest_values,
    )


def write_run_manifest(manifest: RunManifest, path: Path | str) -> tuple[Path, Path]:
    """Atomically write canonical bytes and a sibling SHA-256 file.

    This is the explicit export operation used by ``config compile``.  A run
    root must use :func:`bind_run_manifest`, whose first-writer semantics are
    deliberately stricter.
    """
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    _atomic_write(target, manifest.canonical_bytes())
    digest_path = target.with_suffix(target.suffix + ".sha256")
    _atomic_write(digest_path, (manifest.sha256 + "\n").encode("utf-8"))
    return target, digest_path


def _atomic_write(target: Path, payload: bytes) -> None:
    """Replace ``target`` with one complete, fsynced payload."""
    target.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary_name = tempfile.mkstemp(
        dir=target.parent, prefix=f".{target.name}.", suffix=".tmp"
    )
    temporary = Path(temporary_name)
    try:
        with os.fdopen(descriptor, "wb") as stream:
            stream.write(payload)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, target)
        # Persist the directory entry as well as the file contents so a
        # reported successful bind survives a host crash.
        directory_flag = getattr(os, "O_DIRECTORY", None)
        if os.name != "nt" and directory_flag is not None:
            directory_fd = os.open(target.parent, os.O_RDONLY | directory_flag)
            try:
                os.fsync(directory_fd)
            finally:
                os.close(directory_fd)
    finally:
        if temporary.exists():
            temporary.unlink()


def _read_bounded_regular(
    path: Path,
    *,
    maximum_bytes: int,
    required: bool,
) -> bytes | None:
    """Read one manifest control file without following links or echoing data."""

    try:
        observed = path.lstat()
    except FileNotFoundError:
        if required:
            raise RunManifestError(
                "MANIFEST_FILE_UNAVAILABLE",
                "required manifest file is absent",
                f"/{path.name}",
            )
        return None
    except OSError as error:
        raise RunManifestError(
            "MANIFEST_FILE_UNAVAILABLE",
            "manifest control file cannot be inspected safely",
            f"/{path.name}",
        ) from error
    if (
        not stat.S_ISREG(observed.st_mode)
        or path.is_symlink()
        or not 1 <= observed.st_size <= maximum_bytes
    ):
        raise RunManifestError(
            "MANIFEST_FILE_UNSAFE",
            "manifest control file must be a bounded regular non-symlink file",
            f"/{path.name}",
        )
    flags = os.O_RDONLY | getattr(os, "O_CLOEXEC", 0) | getattr(os, "O_NOFOLLOW", 0)
    try:
        descriptor = os.open(path, flags)
        with os.fdopen(descriptor, "rb") as stream:
            opened = os.fstat(stream.fileno())
            if (
                not stat.S_ISREG(opened.st_mode)
                or opened.st_size != observed.st_size
                or opened.st_size > maximum_bytes
            ):
                raise RunManifestError(
                    "MANIFEST_FILE_UNSAFE",
                    "manifest control file changed while it was opened",
                    f"/{path.name}",
                )
            payload = stream.read(maximum_bytes + 1)
        current = path.lstat()
    except RunManifestError:
        raise
    except OSError as error:
        raise RunManifestError(
            "MANIFEST_FILE_UNAVAILABLE",
            "manifest control file cannot be read safely",
            f"/{path.name}",
        ) from error
    if (
        len(payload) != opened.st_size
        or len(payload) > maximum_bytes
        or not stat.S_ISREG(current.st_mode)
        or current.st_size != opened.st_size
        or (
            opened.st_ino
            and current.st_ino
            and (opened.st_dev, opened.st_ino) != (current.st_dev, current.st_ino)
        )
    ):
        raise RunManifestError(
            "MANIFEST_FILE_UNSAFE",
            "manifest control file changed while it was read",
            f"/{path.name}",
        )
    return payload


def _manifest_sidecar_digest(path: Path) -> str | None:
    payload = _read_bounded_regular(
        path,
        maximum_bytes=_MAX_MANIFEST_HASH_BYTES,
        required=False,
    )
    if payload is None:
        return None
    try:
        words = payload.decode("utf-8").strip().split()
    except UnicodeDecodeError as error:
        raise RunManifestError(
            "MANIFEST_HASH_INVALID",
            "manifest digest sidecar is not valid UTF-8",
            f"/{path.name}",
        ) from error
    digest = words[0] if words else ""
    if re.fullmatch(r"[0-9a-f]{64}", digest) is None:
        raise RunManifestError(
            "MANIFEST_HASH_INVALID",
            "manifest digest sidecar is not one lowercase SHA-256 digest",
            f"/{path.name}",
        )
    return digest


@contextmanager
def _run_manifest_lock(root: Path):
    """Serialize bind/check across processes sharing a run root."""

    with ProcessLock(
        root / RUN_MANIFEST_LOCK_NAME,
        owner="run-manifest",
        blocking=True,
    ):
        yield


def bind_run_manifest(manifest: RunManifest, root: Path | str) -> tuple[Path, Path]:
    """Bind exactly one immutable manifest to a run root.

    The first caller writes canonical bytes atomically.  Later callers are
    idempotent only when their canonical manifest is byte-for-byte identical;
    a resume can therefore never replace routing, profile, policy, or even
    compile-time identity.  The filesystem lock makes that guarantee hold for
    concurrent processes as well as threads.
    """
    root_path = Path(root)
    root_path.mkdir(parents=True, exist_ok=True)
    if manifest.schema_version >= 5:
        # A v5+ manifest names one exact run input. Refuse to create any
        # manifest binding until the dossier and every source blob have
        # already passed their independent first-writer verification.
        from deepreason.evidence.state import RunInputError, verify_run_input

        try:
            verified_input = verify_run_input(root_path)
        except RunInputError as error:
            raise RunManifestError(
                "RUN_INPUT_REQUIRED",
                "v5+ manifest binding requires a verified pre-bound run input",
                "/run-input.json",
            ) from error
        if verified_input["run_input_digest"] != manifest.run_input_digest:
            raise RunManifestError(
                "RUN_INPUT_MANIFEST_MISMATCH",
                "bound run input does not match the manifest digest",
                "/run_input_digest",
            )
        expected_input_version = 1 if manifest.schema_version == 5 else 2
        observed_input_version = int(
            verified_input.get("input_schema_version", 1)
        )
        if observed_input_version != expected_input_version:
            raise RunManifestError(
                "RUN_INPUT_SCHEMA_MISMATCH",
                f"v{manifest.schema_version} requires run-input manifest "
                f"v{expected_input_version}, not v{observed_input_version}",
                "/run-input.json/schema",
            )

        capability = manifest.inquiry_capability_policy
        assert capability is not None
        evidence = capability.attached_evidence
        if evidence.enabled and (
            verified_input["source_count"] > evidence.maximum_sources
            or verified_input["source_bytes"] > evidence.maximum_total_bytes
        ):
            raise RunManifestError(
                "RUN_INPUT_EVIDENCE_BUDGET_EXCEEDED",
                "bound evidence dossier exceeds manifest authority",
                "/inquiry_capability_policy/attached_evidence",
            )
    target = root_path / MANIFEST_NAME
    fixed_hash = root_path / MANIFEST_HASH_NAME
    payload = manifest.canonical_bytes()
    digest_payload = (manifest.sha256 + "\n").encode("utf-8")

    with _run_manifest_lock(root_path):
        if target.exists():
            existing = _read_bounded_regular(
                target,
                maximum_bytes=_MAX_MANIFEST_BYTES,
                required=True,
            )
            assert existing is not None
            if existing != payload:
                existing_hash = hashlib.sha256(existing).hexdigest()
                raise RunManifestError(
                    "RUN_MANIFEST_CONFLICT",
                    "run root is already bound to a different manifest "
                    f"({existing_hash} != {manifest.sha256})",
                    f"/{MANIFEST_NAME}",
                )
            # Validate every sidecar that load_run_manifest could select. A
            # missing fixed-name sidecar is safe to recover because the
            # canonical target bytes already match the requested manifest.
            sidecars = (
                target.with_suffix(target.suffix + ".sha256"),
                fixed_hash,
            )
            for sidecar in sidecars:
                expected = _manifest_sidecar_digest(sidecar)
                if expected is None:
                    continue
                if expected != manifest.sha256:
                    raise RunManifestError(
                        "MANIFEST_HASH_MISMATCH",
                        "manifest digest sidecar does not match canonical bytes",
                        f"/{sidecar.name}",
                    )
            if not fixed_hash.exists():
                _atomic_write(fixed_hash, digest_payload)
            return target, fixed_hash

        # A surviving sidecar is also a binding record (for example after an
        # interrupted/manual target removal). Never let a later caller claim
        # that root for different canonical bytes.
        for sidecar in (
            target.with_suffix(target.suffix + ".sha256"),
            fixed_hash,
        ):
            expected = _manifest_sidecar_digest(sidecar)
            if expected is None:
                continue
            if expected != manifest.sha256:
                raise RunManifestError(
                    "RUN_MANIFEST_CONFLICT",
                    "run root already records a different manifest digest",
                    f"/{sidecar.name}",
                )
        _atomic_write(target, payload)
        if not fixed_hash.exists():
            _atomic_write(fixed_hash, digest_payload)
    return target, fixed_hash


def persist_run_manifest(manifest: RunManifest, root: Path | str) -> tuple[Path, Path]:
    """Backward-compatible name for conflict-safe run-root binding."""
    return bind_run_manifest(manifest, root)


def load_run_manifest(path: Path | str, *, verify_hash: bool = True) -> RunManifest:
    target = Path(path)
    raw = _read_bounded_regular(
        target,
        maximum_bytes=_MAX_MANIFEST_BYTES,
        required=True,
    )
    assert raw is not None
    try:
        manifest = RunManifest.model_validate_json(raw)
    except ValueError as error:
        raise RunManifestError(
            "INVALID_RUN_MANIFEST",
            "manifest JSON does not satisfy the selected schema",
        ) from error
    if verify_hash:
        candidates = [
            target.with_suffix(target.suffix + ".sha256"),
            target.parent / MANIFEST_HASH_NAME,
        ]
        # Every recognized sidecar is an integrity record. Accepting the
        # first match would let a stale/conflicting second record hide behind
        # candidate ordering and make verification depend on filename choice.
        for sidecar in candidates:
            expected = _manifest_sidecar_digest(sidecar)
            if expected is None:
                continue
            if expected != manifest.sha256:
                raise RunManifestError(
                    "MANIFEST_HASH_MISMATCH",
                    "manifest digest sidecar does not match canonical bytes",
                    f"/{sidecar.name}",
                )
    return manifest


def config_from_run_manifest(manifest: RunManifest):
    """Reconstruct Config with routes sourced only from the manifest."""
    from deepreason.config import Config
    from deepreason.llm.profiles import apply_profile_to_config

    try:
        data = json.loads(manifest.engine_config_json)
    except json.JSONDecodeError as error:
        raise RunManifestError("INVALID_ENGINE_CONFIG", str(error)) from error
    if manifest.schema_version >= 3:
        # V3+ feature policy has exactly one authority. The model validator has
        # already checked its consistency with shared engine settings (for
        # example the embedder identity); reconstruction injects it here.
        if manifest.scratch_policy is None or manifest.bridge_policy is None:
            raise RunManifestError(
                "V3_POLICY_REQUIRED", "v3/v4 manifest is missing typed policy"
            )
        data["scratchpad"] = _effective_source_policy(manifest.scratch_policy)
        data["bridge"] = _effective_source_policy(manifest.bridge_policy)
    data["roles"] = {
        role: (
            [route.endpoint_spec() for route in routes]
            if len(routes) > 1
            else routes[0].endpoint_spec()
        )
        for role, routes in manifest.roles.items()
        if routes
    }
    data["engine_profile"] = manifest.engine_profile
    data["model_profile"] = manifest.model_profile
    return apply_profile_to_config(Config.model_validate(data), manifest.model_profile)


def materialize_run_config(manifest: RunManifest, root: Path | str) -> Path:
    """Write a harness-readable Config generated solely from frozen routes."""
    path = Path(root) / ".run-manifest-config.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    config = config_from_run_manifest(manifest)
    _atomic_write(path, _canonical_json(config.model_dump(mode="json")))
    return path


def role_matrix(manifest: RunManifest) -> list[dict[str, Any]]:
    """Exact resolved role matrix for dry-run and inspection surfaces."""
    return [
        {
            "role": role,
            "seat": index,
            "endpoint_id": route.endpoint_id,
            "base_url": route.base_url,
            "model_id": route.model_id,
            "provider": route.provider,
            "family": route.family,
            "reasoning": route.reasoning,
            "output_mode": route.output_mode,
            "output_mechanism": route.output_mechanism,
            "temperature": route.temperature,
        }
        for role, routes in manifest.roles.items()
        for index, route in enumerate(routes)
    ]


def render_role_matrix(manifest: RunManifest) -> str:
    rows = role_matrix(manifest)
    if not rows:
        return "(no active model routes)"
    return "\n".join(
        f"{row['role']}[{row['seat']}]  endpoint={row['endpoint_id']}  "
        f"model={row['model_id']}  provider={row['provider']}  "
        f"family={row['family']}  output={row['output_mode']}  "
        f"mechanism={row['output_mechanism']}  "
        f"reasoning={row['reasoning']}  temperature={row['temperature']}"
        for row in rows
    )


def payload_has_rubric(payload: dict[str, Any]) -> bool:
    if payload.get("standard"):
        return True
    return any(
        str(commitment.get("eval") or "").startswith("rubric:")
        for commitment in (payload.get("commitments") or [])
        if isinstance(commitment, dict)
    )


def _preflight_text_authority(
    config,
    schema_version: int,
    workload_profile: str | None,
) -> None:
    """Fail closed before any endpoint exists for text status authority."""

    if schema_version not in {2, 3, 4, 5, 6} or workload_profile != "text":
        return
    from deepreason.authority import text_status_authority_issues

    issues = text_status_authority_issues(config, workload_profile)
    if issues:
        issue = issues[0]
        raise RunManifestError(issue.code, issue.message, issue.pointer)


def preflight_payload(manifest: RunManifest, payload: dict[str, Any]) -> None:
    """Reject workload/manifest policy conflicts before the first call."""
    if payload_has_rubric(payload) and manifest.rubric_policy == "forbid":
        raise RunManifestError(
            "RUBRIC_INPUT_FORBIDDEN",
            "this run manifest permits program and predicate evaluation only",
            "/standard",
        )
    if payload_has_rubric(payload):
        families = {route.family for route in manifest.roles.get("judge", ())}
        if len(families) < 2:
            raise RunManifestError(
                "SECOND_JUDGE_FAMILY_REQUIRED",
                "rubric input requires two distinct frozen judge families",
                "/roles/judge",
            )


def preflight_harness(manifest: RunManifest, harness, config) -> None:
    """Reject materialized workload/policy conflicts before an endpoint call.

    Payload preflight cannot see criteria that reference commitments already
    present in a resumed root, nor scheduler features that can introduce a
    rubric trial later.  This check operates on the replayed canonical state
    and the frozen engine config, while remaining purely read-only.
    """
    _preflight_text_authority(
        config,
        manifest.schema_version,
        manifest.workload_profile,
    )
    if (
        manifest.schema_version in {2, 3, 4, 5, 6}
        and manifest.workload_profile == "text"
    ):
        # The policy that authorizes a status-changing text judgement is part
        # of the frozen manifest, not a knob a caller may replace between
        # manifest compilation and adapter construction. Reconstruct through
        # Config so older manifests with newly introduced fields retain their
        # safe defaults during replay.
        from deepreason.authority import authority_policy_snapshot

        frozen_config = config_from_run_manifest(manifest)
        if (
            authority_policy_snapshot(config)
            != authority_policy_snapshot(frozen_config)
        ):
            raise RunManifestError(
                "TEXT_AUTHORITY_POLICY_MANIFEST_MISMATCH",
                "runtime text authority policy differs from the frozen manifest",
                "/engine_config",
            )
    active_commitments = {
        commitment_id: harness.commitments[commitment_id]
        for problem in harness.state.problems.values()
        for commitment_id in problem.criteria
        if commitment_id in harness.commitments
    }
    if manifest.rubric_policy == "forbid":
        if any(
            commitment.eval.startswith("rubric:")
            for commitment in active_commitments.values()
        ):
            raise RunManifestError(
                "RUBRIC_INPUT_FORBIDDEN",
                "this materialized run contains an active rubric criterion",
                "/problems/*/criteria",
            )

        # Property admission contains a normative cross-family relevance
        # trial. A program:property_wf criterion is program-evaluable, but an
        # enabled proposal path can still reach judges later in the run.
        from deepreason.oracle import PROPERTY_PROGRAM

        property_path_enabled = (
            int(getattr(config, "PROP_PROPOSE_PERIOD", 0)) > 0
            and int(getattr(config, "FUZZ_N", 0)) > 0
            and bool(manifest.roles.get("property_designer"))
            and bool(manifest.roles.get("judge"))
        )
        if property_path_enabled and any(
            commitment.eval == f"program:{PROPERTY_PROGRAM}"
            for commitment in active_commitments.values()
        ):
            raise RunManifestError(
                "PROPERTY_RUBRIC_TRIAL_FORBIDDEN",
                "property proposals require the frozen cross-family judge "
                "ensemble; disable PROP_PROPOSE_PERIOD explicitly or compile "
                "a require_cross_family manifest",
                "/engine_config/PROP_PROPOSE_PERIOD",
            )
