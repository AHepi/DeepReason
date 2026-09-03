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
from typing import Any, Callable, Literal
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


class UnsupportedRunManifestVersionError(RunManifestError):
    """A historical top-level RunManifest version was rejected raw."""

    def __init__(self, rejected_version: int) -> None:
        self.rejected_version = rejected_version
        super().__init__(
            "UNSUPPORTED_RUN_MANIFEST_VERSION",
            f"RunManifest schema version {rejected_version} is unsupported; "
            f"only schema version {LATEST_SCHEMA_VERSION} is accepted",
            "/schema_version",
        )


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
    # Frozen total prompt-plus-completion capacity. ``None`` retains legacy
    # unqualified behavior and is not evidence of an unlimited window.
    context_window_tokens: int | None = Field(default=None, gt=0)
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

    @model_validator(mode="after")
    def _qualified_context_window_has_finite_completion_allowance(self):
        if self.context_window_tokens is None:
            return self
        if self.max_tokens is None:
            raise ValueError(
                "context_window_tokens requires a finite max_tokens allowance"
            )
        if self.context_window_tokens <= self.max_tokens:
            raise ValueError("context_window_tokens must be greater than max_tokens")
        return self

    @model_serializer(mode="wrap")
    def _serialize_context_capacity(self, handler):
        payload = handler(self)
        if self.context_window_tokens is None:
            # Preserve historical route bytes while making an explicit
            # qualified capacity part of route and manifest identity.
            payload.pop("context_window_tokens", None)
        return payload

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
            "context_window_tokens": self.context_window_tokens,
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

    @model_validator(mode="before")
    @classmethod
    def _reserved_fractions_are_clamped(cls, data):
        """The manifest-side mirror of `ScratchpadConfig`'s clamp. Both sides
        move together by construction -- they call the same helper."""

        if not isinstance(data, dict):
            return data
        exploratory = data.get("exploratory_fraction")
        underexposed = data.get("underexposed_fraction")
        if exploratory is None or underexposed is None:
            return data
        from deepreason.config import clamp_reserved_attention_fractions

        try:
            clamped = clamp_reserved_attention_fractions(
                float(exploratory), float(underexposed)
            )
        except (TypeError, ValueError):
            return data
        if clamped == (exploratory, underexposed):
            return data
        data = dict(data)
        data["exploratory_fraction"], data["underexposed_fraction"] = clamped
        return data

    @model_validator(mode="after")
    def _resolved_policy_is_consistent(self):
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
        # The unresolved-success-safety combination (all-configs-allowed,
        # 2026-08-12) is disclosed as a compile notice by
        # _compile_bridge_policy, its only constructor with notice access;
        # no field here has a runtime reader, so nothing needs restoring.
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
    # D2 rev 2 (dual-mode conjecture, Amendment 3 scoped grant): v7 adds the
    # program:candidate_checker eval-kind vocabulary entry to the skeleton/
    # reasoning candidate conventions. Additive to the Literal, default
    # UNCHANGED at v6 -- every existing committed root's manifest keeps
    # validating and replaying byte-for-byte; v7 is opt-in only.
    conjecturer_turn_contract: Literal["conjecturer.turn.v6", "conjecturer.turn.v7"] = (
        "conjecturer.turn.v6"
    )
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


class CompactRecoveryPolicyV1(BaseModel):
    """Frozen authority for a later route-seat-local presentation transition."""

    model_config = ConfigDict(
        extra="forbid", frozen=True, populate_by_name=True, serialize_by_alias=True
    )

    schema_: Literal["compact-recovery-policy.v1"] = Field(
        "compact-recovery-policy.v1", alias="schema"
    )
    trigger: Literal["schema_exhausted"] = "schema_exhausted"
    source_profiles: tuple[
        Literal["standard"], Literal["frontier"]
    ] = ("standard", "frontier")
    target_profile: Literal["compact"] = "compact"
    scope: Literal["route_seat"] = "route_seat"
    sticky: Literal[True] = True
    applies_to: Literal["all_subsequent_model_calls"] = (
        "all_subsequent_model_calls"
    )
    retry_failed_work: Literal[False] = False


class ContractSchemaRepairGrantV1(BaseModel):
    """One manifest-owned schema-repair grant for one provider contract."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    contract_id: str = Field(
        min_length=1,
        max_length=128,
        pattern=r"^[A-Za-z0-9][A-Za-z0-9_.:-]{0,127}$",
    )
    # The schema bound admits the conjecture family's multi-pointer ceiling
    # (one single-pointer patch per diagnostic, at most four observed live);
    # compilation grants most contracts the smaller shared ceiling.
    maximum_schema_repairs: int = Field(ge=0, le=4, strict=True)
    maximum_provider_calls: int = Field(ge=1, le=5, strict=True)
    repair_execution: Literal["fresh_transaction_per_repair"] = (
        "fresh_transaction_per_repair"
    )
    route_scope: Literal["same_route_seat"] = "same_route_seat"
    exhaustion_status: Literal["schema_exhausted"] = "schema_exhausted"

    @model_validator(mode="after")
    def _provider_call_arithmetic_is_exact(self):
        if self.maximum_provider_calls != self.maximum_schema_repairs + 1:
            raise ValueError(
                "maximum_provider_calls must equal maximum_schema_repairs + 1"
            )
        return self


class ContractSchemaRepairPolicyV1(BaseModel):
    """Frozen per-contract repair authority for transactional v6 calls."""

    model_config = ConfigDict(
        extra="forbid", frozen=True, populate_by_name=True, serialize_by_alias=True
    )

    schema_: Literal["contract-schema-repair-policy.v1"] = Field(
        "contract-schema-repair-policy.v1", alias="schema"
    )
    grants: tuple[ContractSchemaRepairGrantV1, ...]

    @model_validator(mode="after")
    def _grants_are_nonempty_unique_and_sorted(self):
        if not self.grants:
            raise ValueError("contract schema-repair policy requires at least one grant")
        contract_ids = tuple(grant.contract_id for grant in self.grants)
        if len(set(contract_ids)) != len(contract_ids):
            raise ValueError("contract schema-repair grant IDs must be unique")
        if contract_ids != tuple(sorted(contract_ids)):
            raise ValueError(
                "contract schema-repair grants must be sorted by contract_id"
            )
        return self


class RouteSeatContractDecompositionGrantV1(BaseModel):
    """Frozen strong-to-atomic authority for one exact v6 route seat."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    role: str = Field(min_length=1)
    seat: int = Field(ge=0, strict=True)
    endpoint_id: str = Field(min_length=1)
    route_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    source_contract_id: str = Field(min_length=1, max_length=128)
    atomic_contract_id: str = Field(min_length=1, max_length=128)
    trigger: Literal["schema_exhausted"] = "schema_exhausted"
    child_partition: Literal[
        "conjecture_candidate_slot",
        "critic_target",
        "bridge_catalog_batch",
        "bridge_ledger_batch",
        "scratch_single_object",
    ]
    maximum_children: int = Field(ge=1, le=256, strict=True)
    coverage: Literal["all_deterministically_assigned_children"] = (
        "all_deterministically_assigned_children"
    )
    execution: Literal["fresh_transaction_per_child"] = (
        "fresh_transaction_per_child"
    )
    source_failure_preserved: Literal[True] = True
    model_selectable: Literal[False] = False

    @model_validator(mode="after")
    def _contracts_are_distinct(self):
        if self.source_contract_id == self.atomic_contract_id:
            raise ValueError("decomposition source and atomic contracts must differ")
        return self


class RouteSeatContractDecompositionPlanV1(BaseModel):
    """Complete immutable v6 authority for existing atomic fallbacks."""

    model_config = ConfigDict(
        extra="forbid", frozen=True, populate_by_name=True, serialize_by_alias=True
    )

    schema_: Literal["route-seat-contract-decomposition-plan.v1"] = Field(
        "route-seat-contract-decomposition-plan.v1", alias="schema"
    )
    entries: tuple[RouteSeatContractDecompositionGrantV1, ...]

    @model_validator(mode="after")
    def _entries_are_unique_and_sorted(self):
        # Presence freezes the complete set of permitted edges.  An empty
        # tuple is therefore an explicit grant of no decomposition authority,
        # not an inferred fallback.  Newly compiled manifests still receive
        # the canonical supported edges below.
        keys = tuple(
            (entry.role, entry.seat, entry.source_contract_id)
            for entry in self.entries
        )
        if keys != tuple(sorted(set(keys))):
            raise ValueError("contract decomposition entries must be unique and sorted")
        return self


class RouteSeatPresentationGrantV1(BaseModel):
    """Frozen base-presentation authority for one exact manifest route seat."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    role: str = Field(min_length=1)
    seat: int = Field(ge=0, strict=True)
    endpoint_id: str = Field(min_length=1)
    base_profile: Literal["compact", "standard", "frontier"]
    selection_basis: Literal["manifest_default", "explicit_endpoint"]


class RouteSeatPresentationPlanV1(BaseModel):
    """Complete immutable presentation authority for concrete v6 route seats."""

    model_config = ConfigDict(
        extra="forbid", frozen=True, populate_by_name=True, serialize_by_alias=True
    )

    schema_: Literal["route-seat-presentation-plan.v1"] = Field(
        "route-seat-presentation-plan.v1", alias="schema"
    )
    entries: tuple[RouteSeatPresentationGrantV1, ...]

    @model_validator(mode="after")
    def _entries_are_nonempty_unique_and_sorted(self):
        if not self.entries:
            raise ValueError("route-seat presentation plan requires at least one entry")
        keys = tuple((entry.role, entry.seat) for entry in self.entries)
        if len(set(keys)) != len(keys):
            raise ValueError("route-seat presentation entries must be unique")
        if keys != tuple(sorted(keys)):
            raise ValueError(
                "route-seat presentation entries must be sorted by role and seat"
            )
        return self


class RouteSeatBehavioralContractGrantV1(BaseModel):
    """Frozen behavioral authority for one real contract on one route seat."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    contract_id: str = Field(
        min_length=1,
        max_length=128,
        pattern=r"^[A-Za-z0-9][A-Za-z0-9_.:-]{0,127}$",
    )
    schema_repair: ContractSchemaRepairGrantV1
    request_envelope_qualification: Literal[
        "complete_rendered_prompt_plus_completion"
    ] = "complete_rendered_prompt_plus_completion"
    scratch_read: Literal["none", "advisory"]
    scratch_write: Literal["none", "contract_governed"]
    scratch_formal_authority: Literal[False] = False
    decomposition_permission: Literal["none", "authorized_atomic_children"] = "none"
    contract_fallback_permission: Literal[
        "none", "schema_exhaustion_to_atomic"
    ] = "none"

    @model_validator(mode="after")
    def _repair_grant_matches_contract(self):
        if self.schema_repair.contract_id != self.contract_id:
            raise ValueError(
                "behavioral contract grant must contain its exact repair grant"
            )
        return self


class RouteSeatBehavioralCapabilityGrantV1(BaseModel):
    """One exact route-seat behavioral authority grant, not capability evidence."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    role: str = Field(min_length=1)
    seat: int = Field(ge=0, strict=True)
    endpoint_id: str = Field(min_length=1)
    route_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    base_profile: Literal["compact", "standard", "frontier"]
    presentation_selection_basis: Literal[
        "manifest_default", "explicit_endpoint"
    ]
    contracts: tuple[RouteSeatBehavioralContractGrantV1, ...] = ()
    context_window_tokens: int | None = Field(default=None, gt=0)
    maximum_completion_tokens: int | None = Field(default=None, gt=0)
    scratch_access: Literal["advisory_available"] = "advisory_available"
    scratch_formal_authority: Literal[False] = False
    presentation_recovery: Literal["none", "authorized_compact_after_exhaustion"]
    qualification_evidence: Literal["manifest_bound_production_doctor"] = (
        "manifest_bound_production_doctor"
    )

    @model_validator(mode="after")
    def _contracts_are_unique_and_sorted(self):
        contract_ids = tuple(grant.contract_id for grant in self.contracts)
        if len(set(contract_ids)) != len(contract_ids):
            raise ValueError("route-seat behavioral contract grants must be unique")
        if contract_ids != tuple(sorted(contract_ids)):
            raise ValueError(
                "route-seat behavioral contract grants must be sorted by contract_id"
            )
        if (self.context_window_tokens is None) != (
            self.maximum_completion_tokens is None
        ):
            raise ValueError(
                "route-seat behavioral capacity must be wholly present or absent"
            )
        if (
            self.context_window_tokens is not None
            and self.context_window_tokens <= self.maximum_completion_tokens
        ):
            raise ValueError(
                "route-seat context capacity must exceed its completion allowance"
            )
        return self


class RouteSeatBehavioralCapabilityPlanV1(BaseModel):
    """Complete immutable behavioral authority for concrete v6 route seats."""

    model_config = ConfigDict(
        extra="forbid", frozen=True, populate_by_name=True, serialize_by_alias=True
    )

    schema_: Literal["route-seat-behavioral-capability-plan.v1"] = Field(
        "route-seat-behavioral-capability-plan.v1", alias="schema"
    )
    authority: Literal["manifest_frozen_route_seat_behavior"] = (
        "manifest_frozen_route_seat_behavior"
    )
    evidence: Literal["separate_exact_production_qualification"] = (
        "separate_exact_production_qualification"
    )
    entries: tuple[RouteSeatBehavioralCapabilityGrantV1, ...]

    @model_validator(mode="after")
    def _entries_are_nonempty_unique_and_sorted(self):
        if not self.entries:
            raise ValueError("route-seat behavioral capability plan requires entries")
        keys = tuple((entry.role, entry.seat) for entry in self.entries)
        if len(set(keys)) != len(keys):
            raise ValueError("route-seat behavioral capability entries must be unique")
        if keys != tuple(sorted(keys)):
            raise ValueError(
                "route-seat behavioral capability entries must be sorted"
            )
        return self


class ProductionQualificationPolicyV1(BaseModel):
    """Frozen authority requiring exact production-contract qualification."""

    model_config = ConfigDict(
        extra="forbid",
        frozen=True,
        populate_by_name=True,
        serialize_by_alias=True,
        strict=True,
    )

    schema_: Literal["production-qualification-policy.v1"] = Field(
        "production-qualification-policy.v1", alias="schema"
    )
    required: Literal[True] = True
    report_schema: Literal["deepreason-production-contract-doctor-v1"] = (
        "deepreason-production-contract-doctor-v1"
    )
    report_filename: Literal["production-contract-qualification.json"] = (
        "production-contract-qualification.json"
    )
    manifest_binding: Literal["exact_sha256"] = "exact_sha256"
    pair_inventory: Literal["exact_manifest_pairs"] = "exact_manifest_pairs"
    pair_requirement: Literal["all_qualified"] = "all_qualified"
    repair_authority: Literal["exact_contract_grants"] = "exact_contract_grants"
    enforcement_point: Literal["before_provider_dispatch"] = (
        "before_provider_dispatch"
    )

    @field_validator("required", mode="before")
    @classmethod
    def _required_is_an_exact_boolean(cls, value):
        if type(value) is not bool:
            raise ValueError("required must be the boolean true literal")
        return value


class TerminalCommitmentPolicyV1(BaseModel):
    """Frozen root-local authority for one terminal commitment per epoch."""

    model_config = ConfigDict(
        extra="forbid",
        frozen=True,
        populate_by_name=True,
        serialize_by_alias=True,
        strict=True,
    )

    schema_: Literal["terminal-commitment-policy.v1"] = Field(
        "terminal-commitment-policy.v1", alias="schema"
    )
    required: Literal[True] = True
    commitment_schema: Literal["run-terminal-commitment.v1"] = (
        "run-terminal-commitment.v1"
    )
    selection: Literal["first_commitment_per_epoch"] = (
        "first_commitment_per_epoch"
    )
    resume: Literal["typed_resume_opens_next_epoch"] = (
        "typed_resume_opens_next_epoch"
    )
    integrity_scope: Literal["root_local_manifest_and_replay"] = (
        "root_local_manifest_and_replay"
    )
    post_terminal: Literal["exact_commitment_bound_descendants"] = (
        "exact_commitment_bound_descendants"
    )

    @field_validator("required", mode="before")
    @classmethod
    def _required_is_an_exact_boolean(cls, value):
        if type(value) is not bool:
            raise ValueError("required must be the boolean true literal")
        return value


class CompileNoticeV1(BaseModel):
    """A configuration choice a prior gate would have refused at compile
    time. Notices describe what the retired gate would have said; they
    never block compilation (all-configs-allowed tranche, 2026-08-12)."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    code: str = Field(min_length=1)
    message: str = Field(min_length=1)
    pointer: str = Field(min_length=1)
    resolution: str | None = None
    # Canonical JSON of the configured value this notice CARRIES, so a
    # disclosure is also the road back: `config_from_run_manifest` restores it.
    # None when the notice carries nothing.
    value: str | None = None

    @model_serializer(mode="wrap")
    def _omit_absent_carried_value(self, handler):
        """Drop `value` from the dump when absent.

        Load-bearing, not tidiness. `qualification_subject_payload` strips
        ENGINE_CONFIG_FIELD_NOT_CARRIED notices but KEEPS every other notice,
        so a `"value": null` on an unrelated notice moves the manifest sha256
        AND every qualification subject digest that manifest feeds. Measured
        both ways before this field was added; see the tranche's
        `proof/notice_digest_probe.py`.
        """

        dumped = handler(self)
        if self.value is None:
            dumped.pop("value", None)
        return dumped


# A notice sink bound to one manifest construction. Helper validators
# receive it as an argument rather than reaching for a module-global or a
# contextvar: `compile_run_manifest` and the model's own "after" validator
# each own a different sink, and a validator must never write into the
# wrong one.
CompileNoticeEmitter = Callable[..., None]


def _emit_compile_notice(
    sink: list[CompileNoticeV1],
    code: str,
    message: str,
    pointer: str,
    *,
    resolution: str | None = None,
    value: str | None = None,
) -> None:
    sink.append(
        CompileNoticeV1(
            code=code,
            message=message,
            pointer=pointer,
            resolution=resolution,
            value=value,
        )
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
    compact_recovery_policy: CompactRecoveryPolicyV1 | None = None
    contract_schema_repair_policy: ContractSchemaRepairPolicyV1 | None = None
    route_seat_presentation_plan: RouteSeatPresentationPlanV1 | None = None
    route_seat_behavioral_capability_plan: (
        RouteSeatBehavioralCapabilityPlanV1 | None
    ) = None
    route_seat_contract_decomposition_plan: (
        RouteSeatContractDecompositionPlanV1 | None
    ) = None
    production_qualification_policy: ProductionQualificationPolicyV1 | None = None
    compile_notices: tuple[CompileNoticeV1, ...] | None = None
    terminal_commitment_policy: TerminalCommitmentPolicyV1 | None = None
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
        if self.schema_version < 6 or self.compact_recovery_policy is None:
            # V1-v5 never had this authority. An omitted historical v6 field
            # also remains absent and therefore authorizes no transition.
            payload.pop("compact_recovery_policy", None)
        if self.schema_version < 6 or self.contract_schema_repair_policy is None:
            # Historical documents gain no inferred repair authority. V1-v5
            # omit the field entirely, preserving their canonical byte shape.
            payload.pop("contract_schema_repair_policy", None)
        if self.schema_version < 6 or self.route_seat_presentation_plan is None:
            # Historical v6 manifests gain no per-seat authority merely by
            # being loaded by a newer binary.
            payload.pop("route_seat_presentation_plan", None)
        if (
            self.schema_version < 6
            or self.route_seat_behavioral_capability_plan is None
        ):
            # Historical v6 documents receive no behavioral authority from
            # installing a newer binary.
            payload.pop("route_seat_behavioral_capability_plan", None)
        if (
            self.schema_version < 6
            or self.route_seat_contract_decomposition_plan is None
        ):
            payload.pop("route_seat_contract_decomposition_plan", None)
        if self.schema_version < 6 or self.production_qualification_policy is None:
            # Qualification authority is never inferred for historical v6
            # documents, and the field did not exist in v1-v5.
            payload.pop("production_qualification_policy", None)
        if self.schema_version < 6 or not self.compile_notices:
            # Historical documents disclosed nothing merely by being loaded
            # by a newer binary; a notice-free compile is byte-identical to
            # every manifest compiled before this field existed.
            payload.pop("compile_notices", None)
        if self.schema_version < 6 or self.terminal_commitment_policy is None:
            # Historical v6 documents gain no terminal authority merely by
            # being loaded by a newer binary.
            payload.pop("terminal_commitment_policy", None)
        # Criticism is an optional C3 extension.  Absence must preserve the
        # canonical bytes of every pre-C3 manifest, including schema v4.
        if self.criticism_policy is None:
            payload.pop("criticism_policy", None)
        return payload

    @model_validator(mode="after")
    def _production_routes_are_concrete(self):
        # Notices this validator would add are deduped against notices
        # already frozen on `self`: compile_run_manifest's own free-function
        # checks run the identical rule before construction, so the first
        # RunManifest(...) call and any later model_validate() round trip
        # (schema v6's contract-decomposition/behavioral-plan passes) must
        # never double-record the same disclosure.
        new_notices: list[CompileNoticeV1] = []
        existing_keys = {(n.code, n.pointer) for n in (self.compile_notices or ())}

        def _emit_deduped(
            code: str,
            message: str,
            pointer: str,
            *,
            resolution: str | None = None,
        ) -> None:
            key = (code, pointer)
            if key in existing_keys:
                return
            existing_keys.add(key)
            new_notices.append(
                CompileNoticeV1(
                    code=code,
                    message=message,
                    pointer=pointer,
                    resolution=resolution,
                )
            )

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
        if (
            self.schema_version < 6
            and "compact_recovery_policy" in self.model_fields_set
        ):
            raise ValueError("v1-v5 manifests cannot carry compact recovery policy")
        if (
            self.schema_version < 6
            and "contract_schema_repair_policy" in self.model_fields_set
        ):
            raise ValueError(
                "v1-v5 manifests cannot carry contract schema-repair policy"
            )
        if (
            self.schema_version < 6
            and "route_seat_presentation_plan" in self.model_fields_set
        ):
            raise ValueError(
                "v1-v5 manifests cannot carry a route-seat presentation plan"
            )
        if (
            self.schema_version < 6
            and "route_seat_behavioral_capability_plan" in self.model_fields_set
        ):
            raise ValueError(
                "v1-v5 manifests cannot carry a route-seat behavioral capability plan"
            )
        if (
            self.schema_version < 6
            and "route_seat_contract_decomposition_plan" in self.model_fields_set
        ):
            raise ValueError(
                "v1-v5 manifests cannot carry a route-seat contract decomposition plan"
            )
        if (
            self.schema_version < 6
            and "production_qualification_policy" in self.model_fields_set
        ):
            raise ValueError(
                "v1-v5 manifests cannot carry production qualification policy"
            )
        if (
            self.schema_version < 6
            and "terminal_commitment_policy" in self.model_fields_set
        ):
            raise ValueError(
                "v1-v5 manifests cannot carry terminal commitment policy"
            )
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
                        _emit_deduped(
                            f"BRIDGE_{task.upper()}_ROUTE_REQUIRED",
                            f"grounded bridge requires an explicit {role!r} route",
                            f"/roles/{role}",
                        )
                if bridge.grounding_review:
                    reviewer_routes = self.roles.get(bridge.reviewer_role, ())
                    if len(reviewer_routes) < bridge.reviewer_seats:
                        _emit_deduped(
                            "BRIDGE_REVIEWER_SEATS_MISMATCH",
                            "frozen reviewer route count is smaller than reviewer_seats",
                            f"/roles/{bridge.reviewer_role}",
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
            _validate_v4_control_plane_policy(self, emit=_emit_deduped)
            _validate_v4_criticism_policy(self, emit=_emit_deduped)
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
            _validate_v5_capability_policy(self, emit=_emit_deduped)
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
            _validate_v6_capability_policy(self, emit=_emit_deduped)
            if self.route_seat_presentation_plan is not None:
                expected = tuple(
                    (role, seat, route.endpoint_id)
                    for role, routes in self.roles.items()
                    for seat, route in enumerate(routes)
                )
                actual = tuple(
                    (entry.role, entry.seat, entry.endpoint_id)
                    for entry in self.route_seat_presentation_plan.entries
                )
                if actual != tuple(sorted(expected, key=lambda item: item[:2])):
                    raise ValueError(
                        "V6_ROUTE_SEAT_PRESENTATION_PLAN_MISMATCH: entries must "
                        "exactly cover the frozen role seats and endpoint IDs"
                    )
            if self.route_seat_behavioral_capability_plan is not None:
                expected_behavioral = _compile_route_seat_behavioral_capability_plan(
                    self
                )
                if self.route_seat_behavioral_capability_plan != expected_behavioral:
                    raise ValueError(
                        "V6_ROUTE_SEAT_BEHAVIORAL_CAPABILITY_PLAN_MISMATCH: plan "
                        "must exactly match frozen route, contract, presentation, "
                        "scratch, repair, and fallback authority"
                    )
            if self.route_seat_contract_decomposition_plan is not None:
                expected_decomposition = _compile_route_seat_contract_decomposition_plan(
                    self,
                    source_config=json.loads(self.engine_config_json),
                )
                expected_by_key = {
                    (entry.role, entry.seat, entry.source_contract_id): entry
                    for entry in expected_decomposition.entries
                }
                if any(
                    expected_by_key.get(
                        (entry.role, entry.seat, entry.source_contract_id)
                    )
                    != entry
                    for entry in self.route_seat_contract_decomposition_plan.entries
                ):
                    raise ValueError(
                        "V6_ROUTE_SEAT_CONTRACT_DECOMPOSITION_PLAN_MISMATCH: plan "
                        "entries must be canonical supported edges for the frozen route"
                    )
        for role, routes in self.roles.items():
            for index, route in enumerate(routes):
                if route.model_id in _UNRESOLVED_MODELS:
                    raise ValueError(
                        f"roles.{role}.{index}.model_id is unresolved: {route.model_id}"
                    )
        if self.rubric_policy == "require_cross_family":
            judge_routes = self.roles.get("judge", ())
            families = {
                route.family.strip().casefold()
                for route in judge_routes
                if route.family.strip()
            }
            models = {
                f"{route.provider.strip().casefold()}:{route.model_id.strip().casefold()}"
                for route in judge_routes
            }
            # Structural same-model substitute (Amendment 9/R24, mirrors
            # llm/firewall.py::require_cross_family_judge_ensemble's
            # runtime check): >=2 judge seats that are the exact same
            # model satisfy this, narrower than same-family so a
            # same-family-different-model pair still fails below.
            if len(families) < 2 and not (len(judge_routes) >= 2 and len(models) == 1):
                _emit_deduped(
                    "SECOND_JUDGE_FAMILY_REQUIRED",
                    "require_cross_family needs at least two distinct judge families",
                    "/roles/judge",
                )
        if new_notices:
            # `model_copy` from a top-level "after" validator is silently
            # discarded when constructing via `__init__` (pydantic only
            # honors a validator's replacement return value through
            # `model_validate`); `object.__setattr__` bypasses this
            # model's own `frozen=True` to set the derived field in place,
            # which works identically through both construction paths.
            object.__setattr__(
                self, "compile_notices", (*(self.compile_notices or ()), *new_notices)
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
        if self.schema_version < 6 or self.compact_recovery_policy is None:
            payload.pop("compact_recovery_policy", None)
        if self.schema_version < 6 or self.contract_schema_repair_policy is None:
            payload.pop("contract_schema_repair_policy", None)
        if self.schema_version < 6 or self.route_seat_presentation_plan is None:
            payload.pop("route_seat_presentation_plan", None)
        if (
            self.schema_version < 6
            or self.route_seat_behavioral_capability_plan is None
        ):
            payload.pop("route_seat_behavioral_capability_plan", None)
        if (
            self.schema_version < 6
            or self.route_seat_contract_decomposition_plan is None
        ):
            payload.pop("route_seat_contract_decomposition_plan", None)
        if self.schema_version < 6 or self.production_qualification_policy is None:
            payload.pop("production_qualification_policy", None)
        if self.schema_version < 6 or not self.compile_notices:
            payload.pop("compile_notices", None)
        if self.schema_version < 6 or self.terminal_commitment_policy is None:
            payload.pop("terminal_commitment_policy", None)
        if self.criticism_policy is None:
            payload.pop("criticism_policy", None)
        return _canonical_json(payload)

    @property
    def sha256(self) -> str:
        return hashlib.sha256(self.canonical_bytes()).hexdigest()


def resolve_route_seat_base_profile(
    manifest: RunManifest,
    *,
    role: str,
    seat: int,
    endpoint_id: str,
) -> Literal["compact", "standard", "frontier"]:
    """Resolve one exact v6 route seat's frozen base presentation authority.

    Historical v6 manifests predate the per-seat plan and retain their global
    profile semantics. Plan-bearing manifests must resolve through the exact
    role, seat, and endpoint identity; absence is never implicit permission.
    """

    if manifest.schema_version != 6:
        raise RunManifestError(
            "ROUTE_SEAT_PRESENTATION_V6_REQUIRED",
            "route-seat presentation authority requires RunManifest v6",
            "/schema_version",
        )
    routes = manifest.roles.get(role, ())
    if seat < 0 or seat >= len(routes):
        raise RunManifestError(
            "ROUTE_SEAT_PRESENTATION_ROUTE_REQUIRED",
            f"frozen route seat {role}[{seat}] does not exist",
            f"/roles/{role}/{seat}",
        )
    route = routes[seat]
    if route.endpoint_id != endpoint_id:
        raise RunManifestError(
            "ROUTE_SEAT_PRESENTATION_ENDPOINT_MISMATCH",
            f"endpoint identity differs from frozen route seat {role}[{seat}]",
            f"/roles/{role}/{seat}/endpoint_id",
        )
    plan = manifest.route_seat_presentation_plan
    if plan is None:
        return manifest.model_profile
    matches = tuple(
        entry
        for entry in plan.entries
        if entry.role == role and entry.seat == seat
    )
    if len(matches) != 1:
        raise RunManifestError(
            "ROUTE_SEAT_PRESENTATION_GRANT_REQUIRED",
            f"presentation plan lacks one exact grant for {role}[{seat}]",
            "/route_seat_presentation_plan/entries",
        )
    entry = matches[0]
    if entry.endpoint_id != endpoint_id:
        raise RunManifestError(
            "ROUTE_SEAT_PRESENTATION_GRANT_MISMATCH",
            f"presentation grant differs from frozen route seat {role}[{seat}]",
            "/route_seat_presentation_plan/entries",
        )
    return entry.base_profile


def _compile_route_seat_contract_decomposition_plan(
    manifest: RunManifest,
    *,
    source_config: dict[str, Any],
    notices: list[CompileNoticeV1] | None = None,
) -> RouteSeatContractDecompositionPlanV1:
    """Freeze every repository-owned strong-to-smaller execution edge."""

    from deepreason.llm.firewall import route_fingerprint
    from deepreason.llm.wire import (
        ATOMIC_CONJECTURE_CONTRACT_V1,
        ATOMIC_CRITIC_CONTRACT_V1,
        BATCH_CRITIC_CONTRACT_V2,
        CONJECTURER_TURN_CONTRACT_V6,
    )

    entries: list[RouteSeatContractDecompositionGrantV1] = []
    candidate_slots = min(256, max(1, int(source_config.get("VS_K", 6))))
    for seat, route in enumerate(manifest.roles.get("conjecturer", ())):
        entries.append(
            RouteSeatContractDecompositionGrantV1(
                role="conjecturer",
                seat=seat,
                endpoint_id=route.endpoint_id,
                route_sha256=route_fingerprint(route),
                source_contract_id=CONJECTURER_TURN_CONTRACT_V6,
                atomic_contract_id=ATOMIC_CONJECTURE_CONTRACT_V1,
                child_partition="conjecture_candidate_slot",
                maximum_children=candidate_slots,
            )
        )
    critic_seats = {
        binding.seat
        for binding in (manifest.criticism_policy.bindings if manifest.criticism_policy else ())
        if binding.role == "argumentative_critic"
    }
    if manifest.criticism_policy is None:
        critic_seats = set(range(len(manifest.roles.get("argumentative_critic", ()))))
    for seat in sorted(critic_seats):
        route = manifest.roles["argumentative_critic"][seat]
        entries.append(
            RouteSeatContractDecompositionGrantV1(
                role="argumentative_critic",
                seat=seat,
                endpoint_id=route.endpoint_id,
                route_sha256=route_fingerprint(route),
                source_contract_id=BATCH_CRITIC_CONTRACT_V2,
                atomic_contract_id=ATOMIC_CRITIC_CONTRACT_V1,
                child_partition="critic_target",
                maximum_children=256,
            )
        )
    bridge = manifest.bridge_policy
    if bridge is not None and bridge.mode == "grounded_two_stage":
        for role, source_contract, child_contract, partition in (
            (
                bridge.ledger_role,
                "bridge.ledger.v3",
                "bridge.ledger-batch.v1",
                "bridge_catalog_batch",
            ),
            (
                bridge.composer_role,
                "bridge.composition.v2",
                "bridge.composition-batch.v1",
                "bridge_ledger_batch",
            ),
        ):
            seats = manifest.roles.get(role, ())
            if not seats:
                # All-configurations-allowed made a grounded bridge with an
                # unbound stage role COMPILE (BRIDGE_*_ROUTE_REQUIRED became a
                # notice in the 2026-08-12 tranche), which walked this lookup
                # into a bare IndexError -- neither a compile nor a typed
                # refusal. The grant is skipped and disclosed; the point of use
                # (`resolve_route_seat_contract_decomposition`) refuses typed
                # because a skipped grant simply is not in the plan.
                if notices is not None:
                    _emit_compile_notice(
                        notices,
                        "V6_CONTRACT_DECOMPOSITION_ROUTE_REQUIRED",
                        f"contract {source_contract} requires frozen route seat "
                        f"{role}[0]",
                        f"/roles/{role}/0",
                        resolution=(
                            "decomposition grant omitted from the plan; the "
                            "contract cannot be decomposed at dispatch"
                        ),
                    )
                continue
            route = seats[0]
            entries.append(
                RouteSeatContractDecompositionGrantV1(
                    role=role,
                    seat=0,
                    endpoint_id=route.endpoint_id,
                    route_sha256=route_fingerprint(route),
                    source_contract_id=source_contract,
                    atomic_contract_id=child_contract,
                    child_partition=partition,
                    maximum_children=256,
                )
            )
    scratch = manifest.scratch_policy
    control = manifest.control_plane_policy
    if (
        scratch is not None
        and scratch.enabled
        and isinstance(control, ControlPlanePolicyV3)
        and control.scratch_authoring.enabled
    ):
        for role, source_contract, child_contract in (
            (
                scratch.block_role,
                "scratch.block.compact.v1",
                "scratch.block.minimal.v1",
            ),
            (
                scratch.link_role,
                "scratch.link.compact.v1",
                "scratch.link.minimal.v1",
            ),
            (
                scratch.guide_role,
                "scratch.cluster-guide.compact.v1",
                "scratch.cluster-guide.minimal.v1",
            ),
        ):
            route = manifest.roles[role][0]
            entries.append(
                RouteSeatContractDecompositionGrantV1(
                    role=role,
                    seat=0,
                    endpoint_id=route.endpoint_id,
                    route_sha256=route_fingerprint(route),
                    source_contract_id=source_contract,
                    atomic_contract_id=child_contract,
                    child_partition="scratch_single_object",
                    maximum_children=1,
                )
            )
    return RouteSeatContractDecompositionPlanV1(
        entries=tuple(
            sorted(
                entries,
                key=lambda item: (item.role, item.seat, item.source_contract_id),
            )
        )
    )


def resolve_route_seat_contract_decomposition(
    manifest: RunManifest,
    *,
    role: str,
    seat: int,
    endpoint_id: str,
    route_sha256: str,
    source_contract_id: str,
) -> RouteSeatContractDecompositionGrantV1:
    """Resolve one exact manifest-owned decomposition edge without fallback."""

    plan = manifest.route_seat_contract_decomposition_plan
    if manifest.schema_version != 6 or plan is None:
        raise RunManifestError(
            "V6_CONTRACT_DECOMPOSITION_AUTHORITY_REQUIRED",
            "contract decomposition requires an explicit v6 route-seat plan",
            "/route_seat_contract_decomposition_plan",
        )
    matches = tuple(
        entry
        for entry in plan.entries
        if entry.role == role
        and entry.seat == seat
        and entry.source_contract_id == source_contract_id
    )
    if len(matches) != 1:
        raise RunManifestError(
            "V6_CONTRACT_DECOMPOSITION_GRANT_REQUIRED",
            "route seat lacks one exact source-contract decomposition grant",
            "/route_seat_contract_decomposition_plan/entries",
        )
    entry = matches[0]
    if entry.endpoint_id != endpoint_id or entry.route_sha256 != route_sha256:
        raise RunManifestError(
            "V6_CONTRACT_DECOMPOSITION_GRANT_MISMATCH",
            "contract decomposition grant differs from the frozen route seat",
            "/route_seat_contract_decomposition_plan/entries",
        )
    return entry


def _route_seat_behavioral_contract_assignments(
    manifest: RunManifest,
    *,
    notices: list[CompileNoticeV1] | None = None,
) -> tuple[tuple[str, str, int], ...]:
    """Return the closed set of real v6 provider contracts and route seats.

    This is the semantic inventory used to compile behavioral authority.  It
    deliberately contains no pair IDs or qualification results; those are
    evidence projected later by the production doctor.
    """

    if manifest.schema_version != 6:
        raise RunManifestError(
            "V6_BEHAVIORAL_CAPABILITY_REQUIRED",
            "behavioral capability authority requires RunManifest v6",
            "/schema_version",
        )
    control = manifest.control_plane_policy
    if not isinstance(control, ControlPlanePolicyV3):
        raise RunManifestError(
            "V6_BEHAVIORAL_CONTROL_POLICY_REQUIRED",
            "behavioral capability authority requires workflow.controller.v3",
            "/control_plane_policy",
        )
    contracts = control.contract_versions
    assignments: set[tuple[str, str, int]] = set()

    for seat, _route in enumerate(manifest.roles.get("conjecturer", ())):
        assignments.add(
            (contracts.conjecturer_turn_contract, "conjecturer", seat)
        )

    # Defended-trial provider boundary (informal/trial.py's defender/judge/
    # variator calls, wired through InquiryTransactionService the way the
    # ordinary batch-critic call already is). Granted exactly when
    # criticism_policy.authority == "defended_trial" -- narrower than
    # route presence, and deliberately so: `_compile_route_seat_
    # behavioral_capability_plan` is recomputed from a manifest's OWN
    # stored fields not only at fresh compile but every time an existing
    # v6 manifest is RELOADED (`_production_routes_are_concrete` compares
    # the recomputed plan against the stored one), so an unconditional
    # by-route-presence grant would retroactively add a repair-authority
    # requirement no historical manifest's frozen `contract_schema_
    # repair_policy` satisfies -- breaking replay of every already-
    # committed v6 root that happens to have a defender/judge/variator
    # route configured for an unrelated reason (`judge` alone is also the
    # rubric-trial role, unconditionally present on many roots that never
    # touch criticism authority at all). `DR-INV-frozen-surfaces`'s own
    # law is unconditional: fix READERS, never invalidate an existing
    # replay-valid root. The residual gap this narrower gate leaves is the
    # school-free self-detection dispatch path resolving `trial_required`
    # purely from a runtime `Config` value with NO `criticism_policy` set
    # at all (never written to the manifest -- see below): that specific,
    # narrow combination surfaces a typed refusal at dispatch time rather
    # than at compile time, which is exactly the accepted "impossibility
    # surfaces at the point of use" shape the operator's all-
    # configurations-allowed law already describes for compile-unprovable
    # cases, not a silent gap.
    # The exact contract id is computed through the same
    # `wire_contract_for` the live call uses (never hand-rolled): a direct
    # JudgeRuling contract ids as "judgeruling.direct.v1", not
    # "judge.direct.v1" -- the alias table supplied here is a placeholder
    # only, since every one of these contracts' ids is fixed by
    # role/profile/output-model alone, never by alias content. Resolved
    # PER SEAT through `resolve_route_seat_base_profile`, not the
    # manifest-wide default: a route seat's own presentation authority
    # (e.g. a `route_profiles` override, or a later compact-recovery
    # source profile) can differ from `manifest.model_profile`, and only
    # the seat's own profile decides which of the direct/compact
    # wire-contract shapes it will actually render.
    from deepreason.llm.contracts import DefenderOutput, JudgeRuling, VariatorOutput
    from deepreason.llm.wire import AliasTable, wire_contract_for

    _trial_output_models = {
        "defender": DefenderOutput,
        "judge": JudgeRuling,
        "variator": VariatorOutput,
    }
    _placeholder_aliases = AliasTable({"K_001": "placeholder"})
    _defended_trial_authorized = (
        manifest.criticism_policy is not None
        and manifest.criticism_policy.authority == "defended_trial"
    )
    for trial_role, output_model in (
        _trial_output_models.items() if _defended_trial_authorized else ()
    ):
        routes = manifest.roles.get(trial_role, ())
        for seat, route in enumerate(routes):
            seat_profile = resolve_route_seat_base_profile(
                manifest,
                role=trial_role,
                seat=seat,
                endpoint_id=route.endpoint_id,
            )
            contract_id = wire_contract_for(
                trial_role, output_model, seat_profile, _placeholder_aliases
            ).contract_id
            assignments.add((contract_id, trial_role, seat))

    criticism = manifest.criticism_policy
    referee = (
        manifest.inquiry_capability_policy.config_referee
        if manifest.inquiry_capability_policy is not None
        else None
    )
    referee_enabled = referee is not None and referee.enabled
    if criticism is not None:
        for binding in criticism.bindings:
            if binding.role == "argumentative_critic":
                assignments.add(
                    (contracts.batch_critic_contract, binding.role, binding.seat)
                )
                if referee_enabled:
                    # The config referee is an ordinary critic call on the
                    # same frozen seat, under its own narrow contract.
                    assignments.add(
                        ("config-referee.v1", binding.role, binding.seat)
                    )
    else:
        # The ordinary scheduler retains its non-school batch-criticism path
        # when no foreign-school policy is configured. It still uses the real
        # v2 batch contract, so each concrete critic seat is an active pair.
        for seat, _route in enumerate(
            manifest.roles.get("argumentative_critic", ())
        ):
            assignments.add(
                (contracts.batch_critic_contract, "argumentative_critic", seat)
            )
            if referee_enabled:
                assignments.add(("config-referee.v1", "argumentative_critic", seat))

    bridge = manifest.bridge_policy
    if bridge is not None and bridge.mode == "grounded_two_stage":
        assignments.add(
            (contracts.bridge_ledger_wire_contract, bridge.ledger_role, 0)
        )
        assignments.add(
            (contracts.bridge_composition_contract, bridge.composer_role, 0)
        )
        if bridge.grounding_review:
            from deepreason.bridge.repair import GroundingRepairWireV1
            from deepreason.bridge.review import GroundingVerdictWireV1
            from deepreason.llm.wire import DirectWireContract

            assignments.add(
                (
                    DirectWireContract(GroundingVerdictWireV1).contract_id,
                    bridge.reviewer_role,
                    bridge.reviewer_seat,
                )
            )
            if bridge.max_grounding_repair_attempts:
                assignments.add(
                    (
                        DirectWireContract(GroundingRepairWireV1).contract_id,
                        bridge.grounding_repair_role,
                        bridge.reviewer_seat,
                    )
                )

    scratch = manifest.scratch_policy
    if (
        scratch is not None
        and scratch.enabled
        and control.scratch_authoring.enabled
    ):
        assignments.update(
            {
                ("scratch.block.compact.v1", scratch.block_role, 0),
                ("scratch.link.compact.v1", scratch.link_role, 0),
                ("scratch.cluster-guide.compact.v1", scratch.guide_role, 0),
            }
        )

    unbound = set()
    for contract_id, role, seat in assignments:
        routes = manifest.roles.get(role, ())
        if seat < 0 or seat >= len(routes):
            # Disclosed and skipped, never refused: the grant is omitted, so
            # `resolve_route_seat_behavioral_capability` refuses typed at
            # dispatch -- an unbound seat can never act on this contract.
            unbound.add((contract_id, role, seat))
            if notices is not None:
                _emit_compile_notice(
                    notices,
                    "V6_BEHAVIORAL_CONTRACT_ROUTE_REQUIRED",
                    f"contract {contract_id} requires frozen route seat "
                    f"{role}[{seat}]",
                    f"/roles/{role}/{seat}",
                    resolution=(
                        "behavioral grant omitted from the plan; the seat "
                        "carries no authority for this contract"
                    ),
                )
    assignments -= unbound
    decomposition = manifest.route_seat_contract_decomposition_plan
    if decomposition is not None:
        assignments.update(
            (entry.atomic_contract_id, entry.role, entry.seat)
            for entry in decomposition.entries
        )
    return tuple(sorted(assignments, key=lambda item: (item[1], item[2], item[0])))


# P-CEPP-1: both conjecturer-turn contract versions a v6-schema manifest
# may configure (ContractVersionPolicyV3.conjecturer_turn_contract) share
# the SAME conjecture-family scratch authority below -- v7 (D2 rev 2
# dual-mode) is additive to v6, never a different kind of turn.
CONJECTURER_TURN_CONTRACTS = frozenset(
    {"conjecturer.turn.v6", "conjecturer.turn.v7"}
)


def _compile_route_seat_behavioral_capability_plan(
    manifest: RunManifest,
    *,
    notices: list[CompileNoticeV1] | None = None,
) -> RouteSeatBehavioralCapabilityPlanV1:
    """Compile exact behavioral authority from already-frozen v6 policies."""

    from deepreason.llm.firewall import route_fingerprint

    presentation = manifest.route_seat_presentation_plan
    if presentation is None:
        raise RunManifestError(
            "V6_BEHAVIORAL_PRESENTATION_PLAN_REQUIRED",
            "behavioral capability compilation requires per-seat presentation authority",
            "/route_seat_presentation_plan",
        )
    repair_policy = manifest.contract_schema_repair_policy
    if repair_policy is None:
        raise RunManifestError(
            "V6_BEHAVIORAL_REPAIR_POLICY_REQUIRED",
            "behavioral capability compilation requires per-contract repair authority",
            "/contract_schema_repair_policy",
        )
    repairs = {grant.contract_id: grant for grant in repair_policy.grants}
    presentation_by_key = {
        (entry.role, entry.seat): entry for entry in presentation.entries
    }
    assignments: dict[tuple[str, int], list[str]] = {}
    for contract_id, role, seat in _route_seat_behavioral_contract_assignments(
        manifest, notices=notices
    ):
        assignments.setdefault((role, seat), []).append(contract_id)
    decomposition_by_contract = {
        (entry.role, entry.seat, entry.source_contract_id): entry
        for entry in (
            manifest.route_seat_contract_decomposition_plan.entries
            if manifest.route_seat_contract_decomposition_plan is not None
            else ()
        )
    }

    entries: list[RouteSeatBehavioralCapabilityGrantV1] = []
    for role in sorted(manifest.roles):
        for seat, route in enumerate(manifest.roles[role]):
            key = (role, seat)
            presentation_grant = presentation_by_key.get(key)
            if (
                presentation_grant is None
                or presentation_grant.endpoint_id != route.endpoint_id
            ):
                raise RunManifestError(
                    "V6_BEHAVIORAL_PRESENTATION_GRANT_REQUIRED",
                    f"behavioral route seat {role}[{seat}] lacks exact presentation authority",
                    "/route_seat_presentation_plan/entries",
                )
            contract_grants: list[RouteSeatBehavioralContractGrantV1] = []
            for contract_id in sorted(assignments.get(key, ())):
                repair = repairs.get(contract_id)
                if repair is None:
                    raise RunManifestError(
                        "V6_BEHAVIORAL_REPAIR_GRANT_REQUIRED",
                        f"contract {contract_id} lacks exact repair authority",
                        "/contract_schema_repair_policy/grants",
                    )
                is_scratch = contract_id.startswith("scratch.")
                is_conjecture = (
                    contract_id in CONJECTURER_TURN_CONTRACTS
                    or contract_id == "conjecturer.atomic-candidate.v1"
                )
                decomposition = decomposition_by_contract.get(
                    (role, seat, contract_id)
                )
                contract_grants.append(
                    RouteSeatBehavioralContractGrantV1(
                        contract_id=contract_id,
                        schema_repair=repair,
                        scratch_read=(
                            "advisory" if is_scratch or is_conjecture else "none"
                        ),
                        scratch_write=(
                            "contract_governed"
                            if is_scratch or contract_id in CONJECTURER_TURN_CONTRACTS
                            else "none"
                        ),
                        decomposition_permission=(
                            "authorized_atomic_children"
                            if decomposition is not None
                            else "none"
                        ),
                        contract_fallback_permission=(
                            "schema_exhaustion_to_atomic"
                            if decomposition is not None
                            else "none"
                        ),
                    )
                )
            recovery = manifest.compact_recovery_policy
            entries.append(
                RouteSeatBehavioralCapabilityGrantV1(
                    role=role,
                    seat=seat,
                    endpoint_id=route.endpoint_id,
                    route_sha256=route_fingerprint(route),
                    base_profile=presentation_grant.base_profile,
                    presentation_selection_basis=(
                        presentation_grant.selection_basis
                    ),
                    contracts=tuple(contract_grants),
                    context_window_tokens=route.context_window_tokens,
                    maximum_completion_tokens=(
                        route.max_tokens
                        if route.context_window_tokens is not None
                        else None
                    ),
                    presentation_recovery=(
                        "authorized_compact_after_exhaustion"
                        if recovery is not None
                        and presentation_grant.base_profile
                        in recovery.source_profiles
                        else "none"
                    ),
                )
            )
    return RouteSeatBehavioralCapabilityPlanV1(entries=tuple(entries))


def resolve_route_seat_behavioral_capability(
    manifest: RunManifest,
    *,
    role: str,
    seat: int,
    endpoint_id: str,
    route_sha256: str,
) -> RouteSeatBehavioralCapabilityGrantV1:
    """Resolve one exact manifest-owned behavioral grant without fallback."""

    if manifest.schema_version != 6:
        raise RunManifestError(
            "V6_BEHAVIORAL_CAPABILITY_REQUIRED",
            "behavioral capability authority requires RunManifest v6",
            "/schema_version",
        )
    plan = manifest.route_seat_behavioral_capability_plan
    if plan is None:
        raise RunManifestError(
            "V6_BEHAVIORAL_CAPABILITY_PLAN_REQUIRED",
            "historical manifest has no route-seat behavioral authority",
            "/route_seat_behavioral_capability_plan",
        )
    routes = manifest.roles.get(role, ())
    if seat < 0 or seat >= len(routes):
        raise RunManifestError(
            "V6_BEHAVIORAL_ROUTE_REQUIRED",
            f"frozen route seat {role}[{seat}] does not exist",
            f"/roles/{role}/{seat}",
        )
    route = routes[seat]
    from deepreason.llm.firewall import route_fingerprint

    if route.endpoint_id != endpoint_id or route_fingerprint(route) != route_sha256:
        raise RunManifestError(
            "V6_BEHAVIORAL_ROUTE_MISMATCH",
            f"route identity differs from frozen seat {role}[{seat}]",
            f"/roles/{role}/{seat}",
        )
    matches = tuple(
        entry for entry in plan.entries if (entry.role, entry.seat) == (role, seat)
    )
    if len(matches) != 1:
        raise RunManifestError(
            "V6_BEHAVIORAL_GRANT_REQUIRED",
            f"plan lacks one exact grant for {role}[{seat}]",
            "/route_seat_behavioral_capability_plan/entries",
        )
    grant = matches[0]
    if grant.endpoint_id != endpoint_id or grant.route_sha256 != route_sha256:
        raise RunManifestError(
            "V6_BEHAVIORAL_GRANT_MISMATCH",
            f"behavioral grant differs from frozen seat {role}[{seat}]",
            "/route_seat_behavioral_capability_plan/entries",
        )
    return grant


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
    # ENGAGED_CRITICISM_AUTHORITY postdates every schema version's frozen
    # wire-byte goldens (v1-v3 canonical hashes, the v5 incident goldens);
    # its actual effect is already visible in the compiled manifest's own
    # criticism_policy.authority field, so the Config echo drops it
    # unconditionally rather than tracking which versions happen to have
    # a pinned test today.
    data.pop("ENGAGED_CRITICISM_AUTHORITY", None)
    # The three F3 knobs (2026-08-26) drop unconditionally, for the reason the
    # eight above them do and with the operator's forecast of this contact in
    # the tranche instruction itself ("Config knob, versioned-source line for
    # every schema version"). The two attention knobs are consulted inside a
    # run and never written to a manifest; CHANNELS_DISABLED's effect is
    # already visible in the compiled manifest's own capability policies.
    # Their presence in the echo would move every qualification subject digest
    # and every frozen manifest golden; their absence PRESERVES both.
    data.pop("SEED_PROBLEM_BUDGET_FLOOR", None)
    data.pop("ATTENTION_ALLOCATION_POLICY", None)
    data.pop("CHANNELS_DISABLED", None)
    # LEGACY_CRITICISM_ENABLED postdates every schema version's frozen
    # wire-byte goldens for the same reason: its effect is already visible
    # in the compiled manifest's own criticism_policy (None vs populated),
    # so the Config echo drops it unconditionally too.
    data.pop("LEGACY_CRITICISM_ENABLED", None)
    # ADJUDICATION_STATUS_AUTHORITY_ENABLED postdates every schema version's
    # frozen wire-byte goldens too. Unlike the two knobs above, its effect
    # is NEVER written to the manifest at all (the frozen-surfaces law:
    # authority knobs live on Config only, consulted at mint sites) -- the
    # Config echo drops it unconditionally for the same reason every other
    # authority knob was never added here in the first place.
    data.pop("ADJUDICATION_STATUS_AUTHORITY_ENABLED", None)
    # DISCHARGE_POLICY postdates every schema version's frozen wire-byte
    # goldens for the same reason, and the pop is UNCONDITIONAL for the reason
    # ENGAGED_CRITICISM_AUTHORITY's own entry above records: a fix scoped to
    # the versions that happen to carry a pinned test today was itself refuted
    # by the full gate. The knob selects a GENERATION-side policy preset that
    # is never written to the manifest at all, so the echo has nothing to
    # preserve and dropping it keeps every qualification subject digest still.
    # Granted contact, 2026-08-26; see DR-INV-frozen-surfaces.
    data.pop("DISCHARGE_POLICY", None)
    # JUDGE_SEATS_ENABLED and its throttle knobs postdate every schema
    # version's frozen wire-byte goldens too, for the same reason as
    # ADJUDICATION_STATUS_AUTHORITY_ENABLED above: the master judge-dispatch
    # gate lives on Config only, consulted at scheduler dispatch sites, and
    # is never itself written to the manifest.
    data.pop("JUDGE_SEATS_ENABLED", None)
    data.pop("JUDGE_SUMMONS_PER_CYCLE", None)
    data.pop("JUDGE_SUMMONS_COOLDOWN", None)
    # SCHOOL_SEATS_ENABLED (Part E, S2d/R5) postdates every schema
    # version's frozen wire-byte goldens too, for the same reason as
    # every other master gate above: it lives on Config only and is never
    # itself written to the manifest -- its eventual effect (a school
    # bound to a distinct route) is visible in the compiled manifest's
    # own school_execution/criticism_policy fields, not in this echo.
    data.pop("SCHOOL_SEATS_ENABLED", None)
    # The split-budget seat protocol knobs postdate every schema version's
    # frozen wire-byte goldens too, and belong here for the same reason: they
    # are process/transport policy consulted at the adapter's dispatch site and
    # never written to the manifest. Their effect IS recorded, per attempt
    # rather than per manifest -- LLMAttempt.split_legs / split_notice say
    # exactly which legs produced what and under which budget, which is a
    # stronger record than a Config echo would be. Dropping them
    # also keeps a transport choice from costing every home a ~14-minute
    # qualification battery for a subject whose behaviour contract is unchanged.
    data.pop("SPLIT_BUDGET_SEAT_PROTOCOL", None)
    data.pop("SPLIT_BUDGET_EXTRACTION_TOKENS", None)
    # The promotion-nomination knobs (v2 calculus Rung 5) postdate every schema
    # version's frozen wire-byte goldens, and belong here for the same reason as
    # every gate above: they are consulted at one measure site inside the run
    # and are never written to the manifest. Their effect IS recorded, and more
    # precisely than a Config echo would record it -- the reach certificate each
    # nomination registers carries its own `k_frame` and its own `truncated`
    # list, so the record says what threshold fired and what the environment cap
    # dropped, per nomination rather than per manifest. Omitting the drop would
    # move every qualification subject digest for a measure threshold, which is
    # the ENGAGED_CRITICISM_AUTHORITY incident exactly (docs/ERRATA.md E44).
    data.pop("K_FRAME", None)
    data.pop("PROMOTION_ENVIRONMENT_MAX", None)
    # The v2 calculus Rung 8 knobs, dropped for the same reason and with the
    # same guarantee: every one is consulted at a site INSIDE the run and none
    # is ever written to the manifest, and each one's effect is recorded more
    # precisely than a Config echo could record it. The two scope bounds travel
    # inside each reach certificate (`scope_max_depth`/`scope_max_nodes`), so
    # the record says which bound a given verdict was reached under. The eight
    # capture knobs travel inside the diagnostics payload and the
    # `capture14-hysteresis.v1` policy artifact, which carry their own window,
    # precision and bands. Omitting any of these drops would move every
    # qualification subject digest for a measure threshold, which is the
    # ENGAGED_CRITICISM_AUTHORITY incident exactly (docs/ERRATA.md E44).
    data.pop("SCOPE_MAX_DEPTH", None)
    data.pop("SCOPE_MAX_NODES", None)
    data.pop("FRAME_SLICE_ATTACKERS", None)
    data.pop("FRAME_SLICE_DEPARTURES", None)
    data.pop("CAPTURE14_WINDOW", None)
    data.pop("CAPTURE14_AGE_FLOOR", None)
    data.pop("CAPTURE14_PRECISION", None)
    data.pop("CAPTURE14_SC_CEILING", None)
    data.pop("CAPTURE14_ENTER_K", None)
    data.pop("CAPTURE14_EXIT_K", None)
    # The successor-question channel's two per-run switches (granted contact
    # 2026-08-30, DR-INV-frozen-surfaces). Here for the reason every gate above
    # is: each is consulted at a site INSIDE the run -- `registry.resolve` and
    # `registry.minting_enabled` -- and neither is ever written to the
    # manifest. Their effect IS recorded, per proposal rather than per
    # manifest, by the `successor-question:` and `successor-problem-minted`
    # receipts. UNCONDITIONAL and at four spaces: scoping such a pop to a
    # schema range was refuted by two v5 goldens (2026-08-26), and an
    # eight-space guard-scoped pop passes a naive substring check while v6's
    # hash has already moved.
    data.pop("SUCCESSOR_QUESTION_DESTINATION", None)
    data.pop("SUCCESSOR_MINTING_ENABLED", None)
    # The transport retry policy (granted contact, 2026-09-03; see
    # DR-INV-frozen-surfaces). Here for the reason every knob above is: it is
    # consulted at the adapter's dispatch site INSIDE a run and is never written
    # to the manifest. Its effect IS recorded, and per attempt rather than per
    # manifest -- transport_attempts, transport_diagnostics and the per-seat
    # health block say what the transport did on each call. Dropping it also
    # keeps a transport choice from costing every home a ~14-minute
    # qualification battery for a subject whose behaviour contract is unchanged.
    data.pop("TRANSPORT_POLICY", None)
    return data


# Every `Config` field the engine-config echo drops UNCONDITIONALLY, derived
# from the drop list above rather than restated beside it: a knob added there
# must join the disclosure automatically, not escape it. Derived at the highest
# schema version so the version-conditional `scratchpad`/`bridge` pops stay out
# -- those have their own typed policy fields and their own compile notices.
# Deferred to call time because this module must not import `deepreason.config`
# at module scope (`config_from_run_manifest` imports it inside the function
# for the same reason).
_DROPPED_CONFIG_FIELDS: tuple[str, ...] | None = None
_DEFAULT_CONFIG_DATA: dict[str, Any] | None = None

# The three dropped fields whose whole effect is a COMPILE-time decision the
# manifest records in a typed policy field of its own; every other dropped
# field is consulted at a site inside the run, where only the rebuilt Config
# exists. A pointer here names where the effect ALSO appears; it never
# suppresses the notice, because under carriage the notice IS the road back.
_DROPPED_FIELD_CARRIERS: dict[str, str] = {
    "ENGAGED_CRITICISM_AUTHORITY": "/criticism_policy/authority",
    "LEGACY_CRITICISM_ENABLED": "/criticism_policy",
    "SCHOOL_SEATS_ENABLED": "/control_plane_policy/school_execution",
}


# The pointer prefix every carriage notice uses, and the notice code itself.
# The CODE must stay ENGINE_CONFIG_FIELD_NOT_CARRIED: it is the exact key
# `qualification.py::qualification_subject_payload` strips before digesting,
# so renaming it for cosmetics would contact frozen surface 5.
_CARRIAGE_POINTER_PREFIX = "/engine_config/"
_CARRIAGE_NOTICE_CODE = "ENGINE_CONFIG_FIELD_NOT_CARRIED"

# Fields whose carriage changes what a run QUALIFIES against, and therefore
# costs a home one battery. Data, not a branch: a future priced field is a row
# here, which is what keeps the price a configuration concern rather than a
# code edit (modularity law, 2026-08-26).
_CARRIAGE_REQUALIFIES: dict[str, str] = {
    "LEGACY_CRITICISM_ENABLED": (
        "carrying this value engages the criticism policy, which changes the "
        "qualification subject; this home requalifies once (~14 minutes)"
    ),
}


def _unconditionally_dropped_config_fields() -> tuple[str, ...]:
    global _DROPPED_CONFIG_FIELDS, _DEFAULT_CONFIG_DATA
    if _DROPPED_CONFIG_FIELDS is None:
        from deepreason.config import Config

        defaults = _source_config_data(Config())
        _DEFAULT_CONFIG_DATA = defaults
        _DROPPED_CONFIG_FIELDS = tuple(
            sorted(defaults.keys() - _versioned_source_config_data(Config(), 6).keys())
        )
    return _DROPPED_CONFIG_FIELDS


def _default_config_data() -> dict[str, Any]:
    _unconditionally_dropped_config_fields()
    assert _DEFAULT_CONFIG_DATA is not None
    return _DEFAULT_CONFIG_DATA


def _carrier_field_effective_value(field, criticism_policy, control_policy):
    """What this manifest's OWN carrier field says, or None if it says nothing.

    `_DROPPED_FIELD_CARRIERS` points a reader at a typed policy field that
    also expresses the setting. That pointer must not imply agreement it
    cannot deliver: `preparation` gates the compiled authority behind
    `ADJUDICATION_STATUS_AUTHORITY_ENABLED`, so a manifest can hold
    `observe_only` while the configuration asked for `defended_trial`. When
    the two differ the notice says so rather than sending a reader to a field
    that contradicts it. The GATE itself is a separate, parked defect -- a
    named setting silently overridden, which is this batch's own subject one
    layer up (`PARKED.md`, the criticism-authority gate).
    """

    if field == "ENGAGED_CRITICISM_AUTHORITY":
        return getattr(criticism_policy, "authority", None)
    if field == "LEGACY_CRITICISM_ENABLED":
        return criticism_policy is None
    if field == "SCHOOL_SEATS_ENABLED":
        execution = getattr(control_policy, "school_execution", None)
        return getattr(execution, "mode", None) == "route_bound"
    return None


def _emit_uncarried_config_notices(
    data: dict[str, Any],
    engine_config: dict[str, Any],
    *,
    notices: list[CompileNoticeV1],
    criticism_policy=None,
    control_policy=None,
) -> None:
    """Carry every configured Config field the engine-config echo drops.

    The echo cannot hold them: putting them there would move
    `source_config_hash`, and with it every manifest digest and every
    qualification subject digest (docs/ERRATA.md E44). So the value travels
    BESIDE the echo, on the notice that already disclosed its absence -- which
    makes one channel serve both limbs of the operator's 2026-08-28 law, the
    warning and the "at will".

    Emission stays COMPILE-TIME ONLY: this has exactly one caller, inside
    `compile_run_manifest`. Loading a committed manifest attaches no notice.
    The READ half is `_carried_config_values`.
    """

    defaults = _default_config_data()
    for field in _unconditionally_dropped_config_fields():
        if field not in data or field in engine_config:
            continue
        configured = data[field]
        if configured == defaults[field]:
            continue
        price = _CARRIAGE_REQUALIFIES.get(field)
        carrier = _DROPPED_FIELD_CARRIERS.get(field)
        effective = _carrier_field_effective_value(
            field, criticism_policy, control_policy
        )
        diverged = carrier is not None and effective is not None and (
            effective != configured
        )
        _emit_compile_notice(
            notices,
            _CARRIAGE_NOTICE_CODE,
            f"{field}={configured!r} is not carried by this manifest's engine "
            f"config and is restored at run time from this notice"
            + (f"; {price}" if price else "")
            + (
                f"; NOTE this manifest's {carrier} holds {effective!r}, which "
                "this setting did not change -- another switch gated it, so "
                "the two disagree"
                if diverged
                else ""
            ),
            f"{_CARRIAGE_POINTER_PREFIX}{field}",
            # A pointer that disagrees is worse than no pointer: it sends a
            # reader to a field that contradicts the value beside it.
            resolution=None if diverged else carrier,
            value=_canonical_json(configured).decode("utf-8"),
        )


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
        context_window_tokens=spec.get("context_window_tokens"),
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


def _compile_route_seat_presentation_plan(
    *,
    roles: dict[str, tuple[Route, ...]],
    source_specs: dict[str, tuple[dict[str, Any], ...]],
    manifest_default: Literal["compact", "standard", "frontier"],
) -> RouteSeatPresentationPlanV1:
    """Freeze one setup-owned presentation grant per concrete route seat."""

    entries: list[RouteSeatPresentationGrantV1] = []
    for role in sorted(roles):
        routes = roles[role]
        specs = source_specs.get(role, ())
        if len(routes) != len(specs):
            raise RunManifestError(
                "ROUTE_SEAT_PRESENTATION_SOURCE_MISMATCH",
                "resolved route seats no longer match their setup-time endpoint specs",
                f"/roles/{role}",
            )
        for seat, (route, spec) in enumerate(zip(routes, specs, strict=True)):
            explicit = spec.get("model_profile")
            entries.append(
                RouteSeatPresentationGrantV1(
                    role=role,
                    seat=seat,
                    endpoint_id=route.endpoint_id,
                    base_profile=explicit or manifest_default,
                    selection_basis=(
                        "explicit_endpoint"
                        if explicit is not None
                        else "manifest_default"
                    ),
                )
            )
    return RouteSeatPresentationPlanV1(entries=tuple(entries))


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
                route.context_window_tokens,
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


def _compile_scratch_policy(
    source,
    *,
    model_profile: str,
    data: dict[str, Any],
    notices: list[CompileNoticeV1] | None = None,
):
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

    if notices is not None:
        from deepreason.config import clamp_reserved_attention_fractions

        clamped = clamp_reserved_attention_fractions(
            source.exploratory_fraction, source.underexposed_fraction
        )
        if clamped != (source.exploratory_fraction, source.underexposed_fraction):
            _emit_compile_notice(
                notices,
                "SCRATCH_RESERVED_ATTENTION_FRACTIONS_EXCEED_ONE",
                "reserved scratch attention fractions must not exceed one",
                "/scratchpad/exploratory_fraction",
                resolution=(
                    "fractions scaled to sum to one, ratio preserved: "
                    f"{source.exploratory_fraction},{source.underexposed_fraction}"
                    f" -> {clamped[0]},{clamped[1]}"
                ),
            )

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
            # All-configurations-allowed: an unresolved model id falls back to
            # the deterministic hashing backend -- the documented safe default
            # every surface already degrades to -- instead of refusing.
            if notices is not None:
                _emit_compile_notice(
                    notices,
                    "SCRATCH_EMBEDDER_MODEL_UNRESOLVED",
                    "semantic retrieval requires an exact embedder model or "
                    "deterministic hashing",
                    "/EMBEDDER_MODEL",
                    resolution=(
                        f"embedder model {embedder_model!r} is unresolved; the "
                        "run falls back to the deterministic hashing backend"
                    ),
                )
            embedder_backend = "deterministic_hashing"
            embedder_model = None
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


def _compile_bridge_policy(source, *, model_profile: str, notices: list[CompileNoticeV1] | None = None):
    if source.mode == "grounded_two_stage" and notices is not None:
        disabled = [
            name
            for name in ("allow_partial", "allow_abstention", "require_claim_ledger", "require_claim_uses")
            if not getattr(source, name)
        ]
        if disabled:
            # No code in src/deepreason/ reads these four fields outside this
            # check and its frozen-manifest twin (BridgePolicy's own
            # validator below) -- disabling one changes no run behavior
            # today, so the operator's literal values pass through unforced.
            _emit_compile_notice(
                notices,
                "BRIDGE_UNRESOLVED_SUCCESS_SAFETY_DISABLED",
                "grounded_two_stage requires unresolved-success-safe settings: "
                + ", ".join(disabled),
                "/bridge",
            )
    output_section_limit = source.output_section_limit
    if model_profile == "compact":
        output_section_limit = min(output_section_limit, 12)
    values = source.model_dump(mode="json")
    values["output_section_limit"] = output_section_limit
    values["grounding_repair_role"] = source.reviewer_role
    return BridgePolicy(**values)


# One v6 patch repairs exactly one authorized pointer, so a conjecture turn
# with several independent field failures needs one repair per pointer.  The
# first live engaged run (mistral-large-3:675b) made four such mistakes in a
# single semantically sound conjecturer.turn.v6 output and was structurally
# doomed under the shared two-repair ceiling.  The conjecture family (the
# strong turn and its atomic decomposition child) therefore gets double the
# shared ceiling, capped at this explicit bound; RETRY_MAX=0 still disables
# repairs entirely.
CONJECTURE_SCHEMA_REPAIR_CEILING = 4


def _compile_contract_schema_repair_policy(
    *,
    source_config: dict[str, Any],
    control_plane_policy: ControlPlanePolicyV3,
    bridge_policy: BridgePolicy,
    inquiry_capability_policy: InquiryCapabilityPolicyV1 | None = None,
) -> ContractSchemaRepairPolicyV1:
    """Freeze current schema-repair authority per model-facing v6 contract."""

    shared_ceiling = min(2, max(0, int(source_config.get("RETRY_MAX", 2))))
    conjecture_ceiling = min(
        CONJECTURE_SCHEMA_REPAIR_CEILING, 2 * shared_ceiling
    )
    bridge_ceiling = min(2, max(0, bridge_policy.max_schema_repair_attempts))
    ceilings = {
        "batch-critic.v2": shared_ceiling,
        "critic.atomic-target.v1": shared_ceiling,
        "conjecturer.atomic-candidate.v1": conjecture_ceiling,
        # P-CEPP-1: granted to whichever conjecturer-turn contract the
        # manifest actually configured (v6 or v7, D2 rev 2 dual-mode) --
        # v7 is additive to v6, so it earns the identical ceiling, not a
        # separately hardcoded one.
        control_plane_policy.contract_versions.conjecturer_turn_contract: (
            conjecture_ceiling
        ),
        # Defended-trial provider boundary (informal/trial.py's defender/
        # judge/variator calls). Granted unconditionally, the same as the
        # three entries above: a route seat that never materializes simply
        # never consumes this ceiling
        # (`_route_seat_behavioral_contract_assignments` is the gate that
        # decides whether any seat is actually granted a contract at all).
        # Both the direct and compact wire-contract id for each role are
        # granted, since which one a given seat resolves to is a per-seat
        # presentation decision (`resolve_route_seat_base_profile`), not a
        # single run-wide choice this function has visibility into.
        "defender.direct.v1": shared_ceiling,
        "defender.compact.v1": shared_ceiling,
        "judgeruling.direct.v1": shared_ceiling,
        "judge.compact.v1": shared_ceiling,
        "variator.direct.v1": shared_ceiling,
        "variator.compact.v1": shared_ceiling,
    }
    if control_plane_policy.scratch_authoring.enabled:
        ceilings.update(
            {
                "scratch.block.compact.v1": shared_ceiling,
                "scratch.cluster-guide.compact.v1": shared_ceiling,
                "scratch.link.compact.v1": shared_ceiling,
                "scratch.block.minimal.v1": shared_ceiling,
                "scratch.cluster-guide.minimal.v1": shared_ceiling,
                "scratch.link.minimal.v1": shared_ceiling,
            }
        )
    if bridge_policy.mode == "grounded_two_stage":
        ceilings.update(
            {
                "bridge.composition.v2": bridge_ceiling,
                "bridge.ledger.v3": bridge_ceiling,
                "bridge.composition-batch.v1": bridge_ceiling,
                "bridge.ledger-batch.v1": bridge_ceiling,
            }
        )
        if bridge_policy.grounding_review:
            from deepreason.bridge.repair import GroundingRepairWireV1
            from deepreason.bridge.review import GroundingVerdictWireV1
            from deepreason.llm.wire import DirectWireContract

            ceilings.update(
                {
                    DirectWireContract(
                        GroundingRepairWireV1
                    ).contract_id: bridge_ceiling,
                    DirectWireContract(
                        GroundingVerdictWireV1
                    ).contract_id: bridge_ceiling,
                }
            )
    if (
        inquiry_capability_policy is not None
        and inquiry_capability_policy.config_referee is not None
        and inquiry_capability_policy.config_referee.enabled
    ):
        # Conditional exactly like the scratch and bridge contracts above:
        # manifests without an enabled referee keep their exact bytes.
        ceilings["config-referee.v1"] = shared_ceiling
    return ContractSchemaRepairPolicyV1(
        grants=tuple(
            ContractSchemaRepairGrantV1(
                contract_id=contract_id,
                maximum_schema_repairs=ceiling,
                maximum_provider_calls=ceiling + 1,
            )
            for contract_id, ceiling in sorted(ceilings.items())
        )
    )


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


def _validate_v4_control_plane_policy(
    manifest: RunManifest, *, emit: CompileNoticeEmitter
) -> None:
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
            # All-configurations-allowed (CLAUDE.md 2026-08-12): the binding
            # is kept verbatim in the frozen policy. `resolve_school_route`
            # is the point of use and refuses typed
            # (SCHOOL_ROUTE_ROLE_UNSUPPORTED) for any role v4 cannot drive.
            emit(
                "V4_SCHOOL_ROLE_UNSUPPORTED",
                "v4 initially binds conjecturer only",
                "/control_plane_policy/school_execution/bindings",
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
        emit(
            "V4_SCHOOL_BINDING_INCOMPLETE",
            "; ".join(detail),
            "/control_plane_policy/school_execution/bindings",
        )

    # The three checks below are R4 conflicts, not impossibilities: one part
    # of the configuration (a coarse switch) contradicts another (the
    # enumerated bindings). Resolution is fixed and stated in SPEC §4.1 --
    # THE BINDINGS WIN, because they name the seats explicitly and the
    # switch only describes them. The overridden switch is the notice's
    # `resolution`, so the record says which half of the conflict was
    # dropped and why.
    assigned_seats = [(binding.role, binding.seat) for binding, _route in resolved]
    if not school_policy.allow_shared and len(set(assigned_seats)) != len(assigned_seats):
        shared = sorted(
            f"{role}[{seat}]"
            for role, seat in {
                pair for pair in assigned_seats if assigned_seats.count(pair) > 1
            }
        )
        emit(
            "V4_SCHOOL_SHARED_SEAT_FORBIDDEN",
            "allow_shared is false",
            "/control_plane_policy/school_execution/allow_shared",
            resolution=(
                "explicit bindings win over allow_shared=false; shared seats: "
                + ", ".join(shared)
            ),
        )
    if school_policy.require_distinct_models:
        models = {_normalized_model_identity(route) for _binding, route in resolved}
        if len(models) != len(resolved):
            emit(
                "V4_SCHOOL_DISTINCT_MODEL_REQUIRED",
                "bound schools share a model",
                "/control_plane_policy/school_execution/require_distinct_models",
                resolution=(
                    "explicit bindings win over require_distinct_models; "
                    "bound model identities: "
                    + ", ".join(sorted(str(model) for model in models))
                ),
            )
    if school_policy.require_distinct_families:
        families = {route.family.strip().casefold() for _binding, route in resolved}
        if len(families) != len(resolved):
            emit(
                "V4_SCHOOL_DISTINCT_FAMILY_REQUIRED",
                "bound schools share a family",
                "/control_plane_policy/school_execution/require_distinct_families",
                resolution=(
                    "explicit bindings win over require_distinct_families; "
                    "bound families: " + ", ".join(sorted(families))
                ),
            )


def _validate_v4_criticism_policy(
    manifest: RunManifest, *, emit: CompileNoticeEmitter
) -> None:
    """Bind foreign critics to the frozen role matrix and trial topology."""

    policy = manifest.criticism_policy
    if policy is None:
        return
    control = manifest.control_plane_policy
    if control is None or control.mode not in {"active_conjecture", "active_inquiry"}:
        # A control mode that never dispatches foreign criticism simply never
        # reaches this policy; the policy is compiled as given rather than
        # refused (CLAUDE.md 2026-08-12).
        emit(
            "V4_CRITICISM_ACTIVE_REQUIRED",
            "criticism policy requires active_conjecture",
            "/criticism_policy",
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
        # No resolution is available: the field is `ge=1`, so an
        # unsatisfiable requirement cannot be clamped to zero without
        # inventing a value the operator did not ask for. The declared
        # coverage is kept and workflow/criticism.py refuses typed
        # (V4_CRITICISM_FOREIGN_COVERAGE_UNSATISFIED) at the point of use.
        emit(
            "V4_CRITICISM_FOREIGN_COVERAGE_IMPOSSIBLE",
            "minimum coverage exceeds the number of foreign schools "
            f"(coverage={policy.minimum_foreign_school_coverage}, "
            f"foreign schools={max(0, school_count - 1)})",
            "/criticism_policy/minimum_foreign_school_coverage",
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
            emit(
                "V4_CRITICISM_ROLE_UNSUPPORTED",
                "bindings must name argumentative_critic",
                "/criticism_policy/bindings",
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
        emit(
            "V4_CRITICISM_BINDING_INCOMPLETE",
            "; ".join(detail),
            "/criticism_policy/bindings",
        )

    assigned_seats = [(binding.role, binding.seat) for binding, _route in resolved]
    if not policy.allow_shared and len(set(assigned_seats)) != len(assigned_seats):
        shared = sorted(
            f"{role}[{seat}]"
            for role, seat in {
                pair for pair in assigned_seats if assigned_seats.count(pair) > 1
            }
        )
        emit(
            "V4_CRITICISM_SHARED_SEAT_FORBIDDEN",
            "allow_shared is false",
            "/criticism_policy/allow_shared",
            resolution=(
                "explicit bindings win over allow_shared=false; shared seats: "
                + ", ".join(shared)
            ),
        )

    if policy.authority == "defended_trial":
        if not manifest.roles.get("defender"):
            # informal/trial.py declines typed (`no-defender-role`) before any
            # call when the seat is absent; no warrant can be produced.
            emit(
                "V4_CRITICISM_DEFENDER_REQUIRED",
                "defended_trial requires a defender route",
                "/roles/defender",
            )
        judge_routes = manifest.roles.get("judge", ())
        judge_families = {
            route.family.strip().casefold()
            for route in judge_routes
            if route.family.strip()
        }
        judge_models = {
            f"{route.provider.strip().casefold()}:{route.model_id.strip().casefold()}"
            for route in judge_routes
        }
        # Structural same-model substitute (Amendment 9/R24), mirrored
        # from the rubric_policy checks and llm/firewall.py's runtime
        # gate: >=2 judge seats, all the exact same model, reads the same
        # manifest.roles["judge"] shape the manifest-compile CLI's
        # --blind-same-model-judges lever produces -- no separate lever
        # needed for this site.
        # require_cross_family_judge_ensemble refuses typed
        # (JudgeEnsemblePolicyError) from the immutable leases before any
        # judge call, so an insufficient ensemble cannot reach a status
        # decision -- the seats/evidence law's own guard, not this one.
        if len(judge_routes) < 2 or (
            len(judge_families) < 2 and len(judge_models) != 1
        ):
            emit(
                "V4_CRITICISM_CROSS_FAMILY_JUDGES_REQUIRED",
                "defended_trial requires two frozen judge seats from distinct "
                "families",
                "/roles/judge",
            )


def _validate_v5_capability_policy(
    manifest: RunManifest, *, emit: CompileNoticeEmitter
) -> None:
    """Validate the complete, finite Tranche-A capability topology."""

    capabilities = manifest.inquiry_capability_policy
    if capabilities is None:
        raise ValueError("V5_CAPABILITY_POLICY_REQUIRED")
    control = manifest.control_plane_policy
    if not isinstance(control, ControlPlanePolicyV2):
        raise ValueError("V5_ACTIVE_INQUIRY_REQUIRED")
    if capabilities.capability_profile != control.capability_profile:
        # R4 conflict: two parts of one configuration disagree. The control
        # plane wins -- it is the coarser, earlier-frozen authority, and the
        # capability policy is the narrower statement made under it. The
        # overwrite is recorded as the notice's resolution so the record
        # says which half was dropped.
        was = capabilities.capability_profile
        capabilities = capabilities.model_copy(
            update={"capability_profile": control.capability_profile}
        )
        object.__setattr__(manifest, "inquiry_capability_policy", capabilities)
        emit(
            "V5_CAPABILITY_PROFILE_MISMATCH",
            "inquiry capability profile differs from the control-plane profile",
            "/inquiry_capability_policy/capability_profile",
            resolution=(
                "control-plane policy wins; capability_profile overwritten "
                f"{was} -> {control.capability_profile}"
            ),
        )
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


def _validate_v6_capability_policy(
    manifest: RunManifest, *, emit: CompileNoticeEmitter
) -> None:
    """Validate v6 capability authority without weakening the v5 topology."""

    capabilities = manifest.inquiry_capability_policy
    if capabilities is None:
        raise ValueError("V6_CAPABILITY_POLICY_REQUIRED")
    control = manifest.control_plane_policy
    if not isinstance(control, ControlPlanePolicyV3):
        raise ValueError("V6_TRANSACTIONAL_INQUIRY_REQUIRED")
    if capabilities.capability_profile != control.capability_profile:
        # R4 conflict: two parts of one configuration disagree. The control
        # plane wins -- it is the coarser, earlier-frozen authority, and the
        # capability policy is the narrower statement made under it. The
        # overwrite is recorded as the notice's resolution so the record
        # says which half was dropped.
        was = capabilities.capability_profile
        capabilities = capabilities.model_copy(
            update={"capability_profile": control.capability_profile}
        )
        object.__setattr__(manifest, "inquiry_capability_policy", capabilities)
        emit(
            "V6_CAPABILITY_PROFILE_MISMATCH",
            "inquiry capability profile differs from the control-plane profile",
            "/inquiry_capability_policy/capability_profile",
            resolution=(
                "control-plane policy wins; capability_profile overwritten "
                f"{was} -> {control.capability_profile}"
            ),
        )
    if capabilities.formalization.enabled:
        raise ValueError("V6_FORMALIZATION_UNAVAILABLE")
    if capabilities.research.enabled and (
        capabilities.research.backend_identity != "web.contained.v1"
    ):
        # The contained directed-fetch runtime is the only implemented
        # research authority; any other backend identity stays refused.
        raise ValueError("V6_RESEARCH_UNAVAILABLE")
    if (
        capabilities.config_referee is not None
        and capabilities.config_referee.enabled
        and not manifest.roles.get("argumentative_critic")
    ):
        # The referee is an ordinary critic call; without a frozen critic
        # seat there is no route that could ever carry its contract.
        raise ValueError("V6_CONFIG_REFEREE_CRITIC_SEAT_REQUIRED")
    # V6_DEFENDED_TRIAL_TRANSACTION_CONTRACT_REQUIRED retired
    # (defended-trial-wiring tranche, 2026-08-13): informal/trial.py's
    # defender and judge calls are now wired through
    # InquiryTransactionService the same way the ordinary batch-critic
    # call is (see _v6_transactional_trial_call in informal/trial.py and
    # the defender/judge/variator grants in
    # _route_seat_behavioral_contract_assignments above), so a
    # defended_trial-authorized v6 manifest no longer has an unauthorized
    # dispatch waiting to crash mid-cycle. Per the operator's
    # all-configurations-allowed law (CLAUDE.md, 2026-08-12), a refusal
    # this wiring makes moot is retired outright, not converted to a
    # notice.
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
    blind_same_model_judges: bool = False,
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
    notices: list[CompileNoticeV1] = []
    if judge_family and blind_same_model_judges:
        # Precedence (all-configs-allowed, R4 rule 2): judge_family is an
        # explicit request for a SPECIFIC second family, the stronger of the
        # two diversity mechanisms; blind_same_model_judges is dropped.
        _emit_compile_notice(
            notices,
            "JUDGE_FAMILY_AND_BLIND_SAME_MODEL_CONFLICT",
            "pass at most one of judge_family, blind_same_model_judges",
            "/roles/judge",
            resolution="judge_family wins; blind_same_model_judges dropped",
        )
        blind_same_model_judges = False
    explicit_config_profile = (
        "model_profile" in getattr(config, "model_fields_set", set())
        if not isinstance(config, dict)
        else "model_profile" in config
    )
    data = _source_config_data(config)
    scratch_source, bridge_source = _source_feature_policies(data)
    if schema_version < 6:
        for role, seat, spec in _configured_seats(data):
            if spec.get("model_profile") is not None:
                raise RunManifestError(
                    "ROUTE_SEAT_PRESENTATION_MANIFEST_V6_REQUIRED",
                    "endpoint model_profile overrides require RunManifest schema v6",
                    f"/roles/{role}/{seat}/model_profile",
                )
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
        # Compile-time twin of `_validate_v4_criticism_policy`'s
        # V4_CRITICISM_ACTIVE_REQUIRED; both disclose, neither refuses.
        _emit_compile_notice(
            notices,
            "CRITICISM_ACTIVE_CONJECTURE_REQUIRED",
            "criticism_policy requires active_conjecture control mode",
            "/criticism_policy",
        )
    if schema_version < 3 and scratch_source.enabled:
        # scratch_policy is unconditionally popped below schema v3 (see
        # _versioned_serialization); the compile proceeds without it.
        _emit_compile_notice(
            notices,
            "SCRATCH_MANIFEST_V3_REQUIRED",
            "scratchpad.enabled requires RunManifest schema v3",
            "/scratchpad/enabled",
        )
    if schema_version < 3 and bridge_source.mode == "grounded_two_stage":
        # bridge_policy is unconditionally popped below schema v3; the
        # compile proceeds with grounded-review dropped, not silently kept.
        _emit_compile_notice(
            notices,
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
    _preflight_text_authority(config, schema_version, workload_profile, notices=notices)
    engine_profile = engine_profile or data.get("engine_profile") or "full"
    if model_profile is None:
        model_profile = data.get("model_profile") or "standard"
        # A doctor result recommends presentation only. It may select the
        # default profile, never a route or an epistemic policy, and an
        # explicit config/CLI profile always wins.
        if (
            schema_version < 6
            and capability_cache is not None
            and not explicit_config_profile
        ):
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
    presentation_specs: dict[str, tuple[dict[str, Any], ...]] = {
        role: () for role in role_names
    }

    if schema_version >= 3 and bridge_source.mode == "grounded_two_stage":
        required_roles = {
            "ledger": bridge_source.ledger_role,
            "composer": bridge_source.composer_role,
        }
        if bridge_source.grounding_review:
            required_roles["reviewer"] = bridge_source.reviewer_role
        for task, role in required_roles.items():
            if role not in configured_roles:
                # The role stays absent from `roles`; the bridge policy still
                # names it, so dispatching that stage fails typed at the
                # first attempt (select_lease has no route for the role).
                _emit_compile_notice(
                    notices,
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
            presentation_specs[role] = (seed,)
        if "judge" in configured_roles and judge_family:
            second_spec = _select_second_judge_spec(
                data, judge_family, exact.family, capability_cache=capability_cache
            )
            roles["judge"] = (
                exact, _route_from_spec(second_spec, capability_cache=capability_cache)
            )
            presentation_specs["judge"] = (seed, second_spec)
        elif "judge" in configured_roles and blind_same_model_judges:
            # R24 (adjudication-judge-seats-optins tranche, Amendment 9,
            # 2026-08-10): a second seat on the SAME frozen route, relying
            # on the judge pack's content-blindness guarantee
            # (tests/test_judge_ensemble_boundary.py::
            # test_judge_pack_never_names_an_author_school_or_model) rather
            # than model diversity. require_cross_family_judge_ensemble and
            # RunManifest's own rubric_policy validator both read this exact
            # shape (>=2 seats, identical model) as a structural substitute.
            roles["judge"] = (exact, exact)
            presentation_specs["judge"] = (seed, seed)
    else:
        grouped: dict[str, list[Route]] = {role: [] for role in role_names}
        grouped_specs: dict[str, list[dict[str, Any]]] = {
            role: [] for role in role_names
        }
        for role, _index, spec in _configured_seats(data):
            if role not in role_names:
                continue
            grouped.setdefault(role, []).append(
                _route_from_spec(spec, capability_cache=capability_cache)
            )
            grouped_specs.setdefault(role, []).append(spec)
        roles = {role: tuple(grouped.get(role, ())) for role in role_names}
        presentation_specs = {
            role: tuple(grouped_specs.get(role, ())) for role in role_names
        }

    if schema_version == 6 and criticism_policy is None:
        # Imported only after this module is initialized: v6_policy owns the
        # shared derivation helper and imports this module's policy models.
        from deepreason.config import Config
        from deepreason.v6_policy import configured_criticism_policy

        critic_routes = roles.get("argumentative_critic", ())
        resolved_criticism_policy = configured_criticism_policy(
            Config.model_validate(data),
            critic_routes[0].endpoint_id if critic_routes else None,
        )

    if rubric_policy == "require_cross_family":
        judge_routes = roles.get("judge", ())
        families = {
            route.family.strip().casefold()
            for route in judge_routes
            if route.family.strip()
        }
        judge_models = {
            f"{route.provider.strip().casefold()}:{route.model_id.strip().casefold()}"
            for route in judge_routes
        }
        # Structural same-model substitute (Amendment 9/R24), mirrored
        # from RunManifest's own model-validator above and
        # llm/firewall.py::require_cross_family_judge_ensemble's runtime
        # check: >=2 judge seats, all the exact same model.
        if len(families) < 2 and not (
            len(judge_routes) >= 2 and len(judge_models) == 1
        ):
            _emit_compile_notice(
                notices,
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
        _compile_scratch_policy(
            scratch_source,
            model_profile=model_profile,
            data=data,
            notices=notices,
        )
        if schema_version >= 3
        else None
    )
    bridge_policy = (
        _compile_bridge_policy(bridge_source, model_profile=model_profile, notices=notices)
        if schema_version >= 3
        else None
    )

    engine_config = _versioned_source_config_data(data, schema_version)
    _emit_uncarried_config_notices(
        data,
        engine_config,
        notices=notices,
        criticism_policy=resolved_criticism_policy,
        control_policy=resolved_control_policy,
    )
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
    if schema_version == 6:
        manifest_values["compact_recovery_policy"] = CompactRecoveryPolicyV1()
        manifest_values["production_qualification_policy"] = (
            ProductionQualificationPolicyV1()
        )
        manifest_values["terminal_commitment_policy"] = TerminalCommitmentPolicyV1()
        assert isinstance(resolved_control_policy, ControlPlanePolicyV3)
        assert bridge_policy is not None
        manifest_values["contract_schema_repair_policy"] = (
            _compile_contract_schema_repair_policy(
                source_config=data,
                control_plane_policy=resolved_control_policy,
                bridge_policy=bridge_policy,
                inquiry_capability_policy=resolved_inquiry_policy,
            )
        )
        manifest_values["route_seat_presentation_plan"] = (
            _compile_route_seat_presentation_plan(
                roles=roles,
                source_specs=presentation_specs,
                manifest_default=model_profile,
            )
        )
    manifest = RunManifest(
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
        compile_notices=tuple(notices) or None,
        source_config_hash=source_config_hash(data, schema_version=schema_version),
        compiled_at=stamp,
        engine_config_json=_canonical_json(engine_config).decode("utf-8"),
        **manifest_values,
    )
    if schema_version != 6:
        return manifest
    # The two v6 plan passes run AFTER the manifest exists, so anything they
    # disclose has to be folded back into `compile_notices` before the next
    # `model_validate` -- otherwise the record would carry a plan with a
    # silently missing grant.
    plan_notices: list[CompileNoticeV1] = []
    payload = manifest.model_dump(mode="python", by_alias=False)
    payload["route_seat_contract_decomposition_plan"] = (
        _compile_route_seat_contract_decomposition_plan(
            manifest,
            source_config=data,
            notices=plan_notices,
        )
    )
    payload["compile_notices"] = _merged_compile_notices(
        manifest.compile_notices, plan_notices
    )
    manifest = RunManifest.model_validate(payload)
    plan_notices = []
    behavioral_plan = _compile_route_seat_behavioral_capability_plan(
        manifest, notices=plan_notices
    )
    payload = manifest.model_dump(mode="python", by_alias=False)
    payload["route_seat_behavioral_capability_plan"] = behavioral_plan
    payload["compile_notices"] = _merged_compile_notices(
        manifest.compile_notices, plan_notices
    )
    return RunManifest.model_validate(payload)


def _merged_compile_notices(
    existing: tuple[CompileNoticeV1, ...] | None,
    fresh: list[CompileNoticeV1],
) -> tuple[CompileNoticeV1, ...] | None:
    """Append plan-pass disclosures to a manifest's frozen notices.

    Deduped on (code, pointer) for the same reason
    `_production_routes_are_concrete` dedupes: the v6 tail re-validates the
    manifest twice, and one disclosure must not be recorded twice.
    """

    merged = list(existing or ())
    seen = {(n.code, n.pointer) for n in merged}
    for notice in fresh:
        key = (notice.code, notice.pointer)
        if key in seen:
            continue
        seen.add(key)
        merged.append(notice)
    return tuple(merged) or None


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


def _discriminate_raw_run_manifest_version(raw: bytes) -> None:
    """Reject historical versions before any RunManifest model validation."""
    try:
        payload = json.loads(raw)
    except RecursionError as error:
        raise RunManifestError(
            "INVALID_RUN_MANIFEST",
            "manifest JSON nesting exceeds the supported depth",
        ) from error
    except (ValueError, UnicodeDecodeError):
        # Preserve the existing model-validation error path for malformed JSON.
        return
    if not isinstance(payload, dict):
        # Preserve the existing model-validation error path for other JSON roots.
        return
    if "schema_version" not in payload:
        raise RunManifestError(
            "INVALID_RUN_MANIFEST",
            "manifest JSON must declare an integer schema_version",
            "/schema_version",
        )
    schema_version = payload["schema_version"]
    if type(schema_version) is not int:
        raise RunManifestError(
            "INVALID_RUN_MANIFEST",
            "manifest schema_version must be an integer",
            "/schema_version",
        )
    if 1 <= schema_version <= 5:
        raise UnsupportedRunManifestVersionError(schema_version)
    if schema_version != LATEST_SCHEMA_VERSION:
        raise RunManifestError(
            "INVALID_RUN_MANIFEST",
            f"manifest schema_version must be {LATEST_SCHEMA_VERSION}",
            "/schema_version",
        )


def load_run_manifest(path: Path | str, *, verify_hash: bool = True) -> RunManifest:
    target = Path(path)
    raw = _read_bounded_regular(
        target,
        maximum_bytes=_MAX_MANIFEST_BYTES,
        required=True,
    )
    assert raw is not None
    _discriminate_raw_run_manifest_version(raw)
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


def _strict_carried_value(field: str, decoded: Any, pointer: str) -> Any:
    """Validate one carried value against its own Config field, strictly."""

    from pydantic import ValidationError

    from deepreason.config import Config

    try:
        validated = Config.__pydantic_validator__.validate_assignment(
            Config.model_construct(), field, decoded
        )
    except ValidationError as error:
        raise RunManifestError(
            "CARRIED_CONFIG_VALUE_INVALID",
            f"carriage notice for {field!r} holds a value {type(decoded).__name__} "
            f"that {field} does not accept: {error.errors()[0]['msg']}",
            pointer,
        ) from error
    accepted = getattr(validated, field)
    if type(accepted) is not type(decoded) and not (
        isinstance(decoded, list) and isinstance(accepted, tuple)
    ):
        raise RunManifestError(
            "CARRIED_CONFIG_VALUE_INVALID",
            f"carriage notice for {field!r} holds a {type(decoded).__name__} that "
            f"would be coerced to {type(accepted).__name__}; a record must not "
            "buy a run by coercion",
            pointer,
        )
    return accepted


def _carried_config_values(manifest: RunManifest) -> dict[str, Any]:
    """Values this manifest's carriage notices restore into the rebuilt Config.

    Fail-closed on every malformed input. Silently defaulting is the defect
    being repaired, and a hand-edited record must not buy a working run
    (continuation-integrity law, 2026-08-29) -- so a pointer outside the
    engine-config namespace, a field that is not actually dropped, or
    undecodable JSON is a TYPED refusal, never a shrug.
    """

    dropped = set(_unconditionally_dropped_config_fields())
    carried: dict[str, Any] = {}
    for notice in manifest.compile_notices or ():
        if notice.code != _CARRIAGE_NOTICE_CODE or notice.value is None:
            continue
        if not notice.pointer.startswith(_CARRIAGE_POINTER_PREFIX):
            raise RunManifestError(
                "CARRIED_CONFIG_POINTER_INVALID",
                "carriage notice points outside the engine-config namespace",
                notice.pointer,
            )
        field = notice.pointer[len(_CARRIAGE_POINTER_PREFIX):]
        if field not in dropped:
            raise RunManifestError(
                "CARRIED_CONFIG_FIELD_UNKNOWN",
                f"carriage notice names {field!r}, which the engine config "
                "does not drop",
                notice.pointer,
            )
        try:
            decoded = json.loads(notice.value)
        except json.JSONDecodeError as error:
            raise RunManifestError(
                "CARRIED_CONFIG_VALUE_INVALID",
                f"carriage notice for {field!r} holds undecodable JSON: {error}",
                notice.pointer,
            ) from error
        # Shape is not enough. `Config` validates in lax mode, so a JSON
        # string "yes" would COERCE into a bool and a hand-edited record would
        # buy a working run -- the exact thing the continuation-integrity law
        # (2026-08-29) forbids. Validate the field on its own, in strict mode,
        # and surface a coercion or a range violation as a TYPED refusal
        # rather than letting a raw ValidationError escape a function whose
        # every other failure mode is coded.
        carried[field] = _strict_carried_value(field, decoded, notice.pointer)
    return carried


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
    # Carriage lands BEFORE the roles/profile injection below, so a carried key
    # can never become a second route authority even if the drop-set guard
    # above were ever defeated.
    data.update(_carried_config_values(manifest))
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
    *,
    notices: list[CompileNoticeV1] | None = None,
) -> None:
    """Disclose text status authority issues instead of refusing.

    Retired as a refusal 2026-08-13 (all-configs-allowed follow-up):
    `calibration_receipt_is_verified` has no verifier and can never be
    satisfied, so failing closed here was a dead end no configuration
    could resolve, not a real point-of-use failure. The run proceeds;
    every issue the old gate would have refused on is recorded as a
    notice instead, with the safe runtime fallback `trial_authority_for`
    already applies named as the resolution.
    """

    if schema_version not in {2, 3, 4, 5, 6} or workload_profile != "text":
        return
    if notices is None:
        return
    from deepreason.authority import text_status_authority_issues

    for issue in text_status_authority_issues(config, workload_profile):
        _emit_compile_notice(
            notices,
            issue.code,
            issue.message,
            issue.pointer,
            resolution=(
                "status authority stays observe_only for this surface "
                "until a calibration-receipt verifier exists"
            ),
        )


def preflight_payload(
    manifest: RunManifest, payload: dict[str, Any]
) -> tuple[CompileNoticeV1, ...]:
    """Disclose workload/manifest policy conflicts before the first call.

    Retired as a refusal 2026-08-16 (all-configs-allowed completion):
    every configuration compiles, so a payload the manifest's policy did
    not anticipate is DISCLOSED here, not stopped. The payload is never
    mutated -- preflight is read-only over the operator's own input, and
    silently stripping a criterion would change what the run is about.

    Nothing is lost by disclosing: a rubric-derived warrant without a
    conforming trial transcript is refused by `Harness._validate_warrant`
    (harness.py, frozen surface), and an insufficient judge ensemble is
    refused by `require_cross_family_judge_ensemble` from the immutable
    leases before any judge call. Those are the points of use.
    """
    notices: list[CompileNoticeV1] = []
    if payload_has_rubric(payload) and manifest.rubric_policy == "forbid":
        _emit_compile_notice(
            notices,
            "RUBRIC_INPUT_FORBIDDEN",
            "this run manifest permits program and predicate evaluation only",
            "/standard",
        )
    if payload_has_rubric(payload):
        families = {route.family for route in manifest.roles.get("judge", ())}
        if len(families) < 2:
            _emit_compile_notice(
                notices,
                "SECOND_JUDGE_FAMILY_REQUIRED",
                "rubric input requires two distinct frozen judge families",
                "/roles/judge",
            )
    return tuple(notices)


def report_preflight_notices(
    notices: tuple[CompileNoticeV1, ...] | None, *, stream=None
) -> None:
    """Surface preflight disclosures on the same channel `config compile`
    uses for `compile_notices`. The manifest is frozen by preflight time, so
    the return value is the only channel a disclosure has."""

    import sys as _sys

    # A stubbed preflight (test doubles do this) returns nothing; an absent
    # disclosure channel is not a disclosure of nothing to say.
    for notice in notices or ():
        print(
            f"NOTICE {notice.code}: {notice.message}",
            file=_sys.stderr if stream is None else stream,
        )


def preflight_harness(
    manifest: RunManifest, harness, config
) -> tuple[CompileNoticeV1, ...]:
    """Reject materialized workload/policy conflicts before an endpoint call.

    Payload preflight cannot see criteria that reference commitments already
    present in a resumed root, nor scheduler features that can introduce a
    rubric trial later.  This check operates on the replayed canonical state
    and the frozen engine config, while remaining purely read-only.

    Returns any text-status-authority disclosure notices found on this
    re-check (2026-08-13): the manifest is already frozen by this point, so
    a fresh notice cannot be appended to ``manifest.compile_notices`` -- the
    caller inspects this return value for the run record instead of a
    refusal, mirroring what `compile_run_manifest` records at compile time.
    """
    notices: list[CompileNoticeV1] = []
    _preflight_text_authority(
        config,
        manifest.schema_version,
        manifest.workload_profile,
        notices=notices,
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
            _emit_compile_notice(
                notices,
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
            _emit_compile_notice(
                notices,
                "PROPERTY_RUBRIC_TRIAL_FORBIDDEN",
                "property proposals require the frozen cross-family judge "
                "ensemble; disable PROP_PROPOSE_PERIOD explicitly or compile "
                "a require_cross_family manifest",
                "/engine_config/PROP_PROPOSE_PERIOD",
            )
    return tuple(notices)
