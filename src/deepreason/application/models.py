"""Strict, transport-neutral intents and results for text-run operations.

The intent vocabulary contains no provider route, graph status, event payload,
guard override, or raw controller field.  CLI and MCP may select an immutable
manifest document, budgets, and user workload content; the application service
owns every lifecycle and scheduler decision after that boundary.
"""

from __future__ import annotations

import re
from collections.abc import Mapping
from typing import Any, Literal

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    StrictInt,
    field_validator,
    model_validator,
)

from deepreason.canonical import canonical_json, sha256_hex
from deepreason.runtime.stop import StopMetrics, StopReason

from deepreason.workloads.text import ReasoningWorkloadSpec


class _StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, strict=True)


class RunBudgetIntentV1(_StrictModel):
    cycles: StrictInt | Literal["unlimited"]
    token_budget: StrictInt | Literal["unlimited"]

    @field_validator("cycles")
    @classmethod
    def _positive_cycles(cls, value):
        if isinstance(value, int) and value < 1:
            raise ValueError("cycles must be positive or unlimited")
        return value

    @field_validator("token_budget")
    @classmethod
    def _nonnegative_tokens(cls, value):
        if isinstance(value, int) and value < 0:
            raise ValueError("token_budget cannot be negative")
        return value


class StartTextRunIntentV1(_StrictModel):
    schema_: Literal["application.text-run.start.v1"] = Field(
        "application.text-run.start.v1", alias="schema"
    )
    root: str = Field(min_length=1, max_length=4_096)
    workload: ReasoningWorkloadSpec
    run_manifest_ref: str = Field(min_length=1, max_length=4_096)
    budget: RunBudgetIntentV1
    experimental_v5: bool = False

    @field_validator("root", "run_manifest_ref")
    @classmethod
    def _safe_path_text(cls, value: str) -> str:
        if "\x00" in value:
            raise ValueError("path text cannot contain NUL")
        return value


class ContinueTextRunIntentV1(_StrictModel):
    schema_: Literal["application.text-run.continue.v1"] = Field(
        "application.text-run.continue.v1", alias="schema"
    )
    root: str = Field(min_length=1, max_length=4_096)
    budget: RunBudgetIntentV1
    expected_manifest_digest: str | None = Field(
        default=None, pattern=r"^[0-9a-f]{64}$"
    )
    experimental_v5: bool = False


class InspectTextRunIntentV1(_StrictModel):
    schema_: Literal["application.text-run.inspect.v1"] = Field(
        "application.text-run.inspect.v1", alias="schema"
    )
    root: str = Field(min_length=1, max_length=4_096)
    since_seq: StrictInt = Field(default=-1, ge=-1)


class WatchTextRunIntentV1(_StrictModel):
    schema_: Literal["application.text-run.watch.v1"] = Field(
        "application.text-run.watch.v1", alias="schema"
    )
    root: str = Field(min_length=1, max_length=4_096)
    interval: float = Field(default=0.25, gt=0)
    once: bool = False


class CancelTextRunIntentV1(_StrictModel):
    schema_: Literal["application.text-run.cancel.v1"] = Field(
        "application.text-run.cancel.v1", alias="schema"
    )
    root: str = Field(min_length=1, max_length=4_096)


class RunStartedV1(_StrictModel):
    schema_: Literal["application.text-run.started.v1"] = Field(
        "application.text-run.started.v1", alias="schema"
    )
    lifecycle: Literal["running"] = "running"
    root: str
    manifest_digest: str = Field(pattern=r"^[0-9a-f]{64}$")
    workload: Literal["text"] = "text"

    def presentation_payload(self) -> dict[str, Any]:
        return {
            "state": self.lifecycle,
            "root": self.root,
            "manifest_sha256": self.manifest_digest,
            "workload": self.workload,
            "status_operation": "run_status",
            "result_operation": "run_result",
        }


class RunProgressResultV1(_StrictModel):
    schema_: Literal["application.text-run.progress.v1"] = Field(
        "application.text-run.progress.v1", alias="schema"
    )
    lifecycle: str
    payload: dict[str, Any]

    def presentation_payload(self) -> dict[str, Any]:
        return dict(self.payload)


class OutstandingWorkItemProjectionV1(_StrictModel):
    work_order_id: str = Field(pattern=r"^sha256:[0-9a-f]{64}$")
    recovery: str
    role: str
    seat: StrictInt = Field(ge=0)
    endpoint_id: str
    route_digest: str = Field(pattern=r"^[0-9a-f]{64}$")
    contract_id: str
    reserved_tokens: StrictInt = Field(ge=0)
    provider_calls_used: StrictInt = Field(ge=0)
    provider_calls_limit: StrictInt = Field(ge=1)
    local_repairs_used: StrictInt = Field(ge=0)
    local_repairs_limit: StrictInt = Field(ge=0)
    context_expansions_used: StrictInt = Field(ge=0)
    context_expansions_limit: StrictInt = Field(ge=0)


class OutstandingWorkResultV1(_StrictModel):
    schema_: Literal["application.text-run.outstanding-work.v1"] = Field(
        "application.text-run.outstanding-work.v1", alias="schema"
    )
    process_digest: str = Field(pattern=r"^sha256:[0-9a-f]{64}$")
    last_control_seq: StrictInt = Field(ge=-1)
    work: tuple[OutstandingWorkItemProjectionV1, ...] = ()

    def presentation_payload(self) -> dict[str, Any]:
        return self.model_dump(mode="json", by_alias=True)


class TextRunTerminalResultV1(_StrictModel):
    schema_: Literal["application.text-run.terminal.v1"] = Field(
        "application.text-run.terminal.v1", alias="schema"
    )
    lifecycle: Literal["completed", "cancelled", "failed"]
    payload: dict[str, Any]

    def presentation_payload(self) -> dict[str, Any]:
        return dict(self.payload)

    def exit_code(self) -> int:
        return run_result_exit_code(self.payload)


class RunVerificationSummaryV2(_StrictModel):
    schema_: Literal["verification.summary.v2"] = Field(
        "verification.summary.v2", alias="schema"
    )
    valid: bool
    integrity_valid: bool
    security_valid: bool
    completion_satisfied: bool
    epistemic_checks_passed: bool
    operational_checks_passed: bool
    finding_counts: dict[str, StrictInt]

    @model_validator(mode="after")
    def _valid_means_authority_valid(self):
        if self.valid != (self.integrity_valid and self.security_valid):
            raise ValueError("verification summary valid flag is inconsistent")
        expected = {
            "integrity",
            "security",
            "completion",
            "epistemic",
            "operational",
        }
        if set(self.finding_counts) != expected or any(
            isinstance(value, bool) or value < 0
            for value in self.finding_counts.values()
        ):
            raise ValueError("verification summary finding counts are invalid")
        flags_by_channel = {
            "integrity": self.integrity_valid,
            "security": self.security_valid,
            "completion": self.completion_satisfied,
            "epistemic": self.epistemic_checks_passed,
            "operational": self.operational_checks_passed,
        }
        if any(
            passed != (self.finding_counts[channel] == 0)
            for channel, passed in flags_by_channel.items()
        ):
            raise ValueError("verification summary flags differ from finding counts")
        return self


class CompactRecoveryLanguageV1(_StrictModel):
    """Stable user-facing meaning for one compact-recovery projection."""

    triggering_work: Literal["schema-exhausted triggering work"] = (
        "schema-exhausted triggering work"
    )
    activation: Literal["route-seat compact recovery activated"] = (
        "route-seat compact recovery activated"
    )
    subsequent_call: Literal["subsequent compact-path call"] = (
        "subsequent compact-path call"
    )
    subsequent_completion: Literal["subsequent compact-path completion"] = (
        "subsequent compact-path completion"
    )


class RouteSeatBaseProjectionV1(_StrictModel):
    """Frozen base presentation authority for one concrete route seat."""

    schema_: Literal["route-seat-base-projection.v1"] = Field(
        "route-seat-base-projection.v1", alias="schema"
    )
    role: str = Field(min_length=1, max_length=128)
    seat: StrictInt = Field(ge=0)
    endpoint_id: str = Field(min_length=1, max_length=512)
    route_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    base_profile: Literal["standard", "frontier", "compact"]
    selection_basis: Literal["manifest_default", "explicit_endpoint"]

    @property
    def route_seat_key(self) -> tuple[str, int, str, str]:
        return (self.role, self.seat, self.endpoint_id, self.route_sha256)


class CompactRecoveryRouteProjectionV1(_StrictModel):
    """Truthful process projection for one durable route-seat transition."""

    schema_: Literal["compact-recovery-route-projection.v1"] = Field(
        "compact-recovery-route-projection.v1", alias="schema"
    )
    transition_ref: str = Field(pattern=r"^sha256:[0-9a-f]{64}$")
    triggering_work_id: str = Field(pattern=r"^sha256:[0-9a-f]{64}$")
    triggering_terminal_ref: str = Field(pattern=r"^sha256:[0-9a-f]{64}$")
    triggering_semantic_admission_ref: str = Field(
        pattern=r"^sha256:[0-9a-f]{64}$"
    )
    triggering_status: Literal["schema_exhausted"] = "schema_exhausted"
    role: str = Field(min_length=1, max_length=128)
    seat: StrictInt = Field(ge=0)
    endpoint_id: str = Field(min_length=1, max_length=512)
    route_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    source_profile: Literal["standard", "frontier"]
    target_profile: Literal["compact"] = "compact"
    trigger: Literal["schema_exhausted"] = "schema_exhausted"
    sticky: Literal[True] = True
    applies_to: Literal["all_subsequent_model_calls"] = (
        "all_subsequent_model_calls"
    )
    retry_failed_work: Literal[False] = False
    subsequent_compact_call_count: StrictInt = Field(ge=0)
    subsequent_compact_work_ids: tuple[str, ...] = ()
    actual_contract_ids: tuple[str, ...] = ()
    completed_compact_work_ids: tuple[str, ...] = ()
    language: CompactRecoveryLanguageV1 = Field(
        default_factory=CompactRecoveryLanguageV1
    )

    @field_validator(
        "subsequent_compact_work_ids",
        "actual_contract_ids",
        "completed_compact_work_ids",
        mode="before",
    )
    @classmethod
    def _json_arrays_are_frozen(cls, value):
        return tuple(value) if isinstance(value, list) else value

    @field_validator(
        "subsequent_compact_work_ids",
        "completed_compact_work_ids",
    )
    @classmethod
    def _canonical_work_ids(cls, value):
        if any(
            not isinstance(item, str)
            or not re.fullmatch(r"sha256:[0-9a-f]{64}", item)
            for item in value
        ):
            raise ValueError("compact work IDs must be content addresses")
        if tuple(value) != tuple(sorted(set(value))):
            raise ValueError("compact work IDs must be unique and sorted")
        return tuple(value)

    @field_validator("actual_contract_ids")
    @classmethod
    def _canonical_contract_ids(cls, value):
        if any(not isinstance(item, str) or not item for item in value):
            raise ValueError("compact contract IDs must be non-empty strings")
        if tuple(value) != tuple(sorted(set(value))):
            raise ValueError("compact contract IDs must be unique and sorted")
        return tuple(value)

    @model_validator(mode="after")
    def _honest_route_projection(self):
        if self.subsequent_compact_call_count != len(
            self.subsequent_compact_work_ids
        ):
            raise ValueError("compact call count differs from its work IDs")
        if self.triggering_work_id in self.subsequent_compact_work_ids:
            raise ValueError("triggering work cannot be a subsequent compact call")
        if self.triggering_work_id in self.completed_compact_work_ids:
            raise ValueError("triggering work cannot be a compact completion")
        if not set(self.completed_compact_work_ids).issubset(
            self.subsequent_compact_work_ids
        ):
            raise ValueError("compact completions must be subsequent compact calls")
        if self.subsequent_compact_call_count and not self.actual_contract_ids:
            raise ValueError("compact calls require their actual contract IDs")
        if not self.subsequent_compact_call_count and self.actual_contract_ids:
            raise ValueError("a route without compact calls cannot claim contracts")
        return self

    @property
    def route_seat_key(self) -> tuple[str, int, str, str]:
        return (self.role, self.seat, self.endpoint_id, self.route_sha256)


class RouteSeatModelClassificationProjectionV1(_StrictModel):
    """Replay-derived model classification for one exact route seat."""

    schema_: Literal["route-seat-model-classification-projection.v1"] = Field(
        "route-seat-model-classification-projection.v1", alias="schema"
    )
    role: str = Field(min_length=1, max_length=64)
    seat: StrictInt = Field(ge=0, le=1_023)
    endpoint_id: str = Field(min_length=1, max_length=256)
    route_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    behavioral_grant_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    selected_class: Literal[
        "qualified_exact_behavior",
        "unqualified_exact_behavior",
        "inactive_no_authorized_contract",
    ]
    authorized_contract_ids: tuple[str, ...] = ()
    evidence_pair_ids: tuple[str, ...] = ()
    qualification_evidence_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    classification_plan_ref: str = Field(pattern=r"^sha256:[0-9a-f]{64}$")
    classification_binding_ref: str = Field(pattern=r"^sha256:[0-9a-f]{64}$")

    @field_validator("authorized_contract_ids", "evidence_pair_ids", mode="before")
    @classmethod
    def _json_arrays_are_frozen(cls, value):
        return tuple(value) if isinstance(value, list) else value

    @model_validator(mode="after")
    def _classification_is_canonical(self):
        if self.authorized_contract_ids != tuple(
            sorted(set(self.authorized_contract_ids))
        ):
            raise ValueError("classification contract IDs must be unique and sorted")
        if self.evidence_pair_ids != tuple(sorted(set(self.evidence_pair_ids))):
            raise ValueError("classification evidence pair IDs must be unique and sorted")
        inactive = self.selected_class == "inactive_no_authorized_contract"
        if inactive != (not self.authorized_contract_ids):
            raise ValueError("inactive classification cannot authorize contracts")
        if inactive != (not self.evidence_pair_ids):
            raise ValueError("inactive classification cannot claim evidence pairs")
        return self

    @property
    def route_seat_key(self) -> tuple[str, int, str, str]:
        return (self.role, self.seat, self.endpoint_id, self.route_sha256)


class AtomicWorkAttemptProjectionV1(_StrictModel):
    """One actual atomic child or its fresh schema-repair transaction."""

    schema_: Literal["atomic-work-attempt-projection.v1"] = Field(
        "atomic-work-attempt-projection.v1", alias="schema"
    )
    work_id: str = Field(pattern=r"^sha256:[0-9a-f]{64}$")
    contract_id: str = Field(min_length=1, max_length=128)
    child_key: str = Field(min_length=1, max_length=512)
    child_index: StrictInt = Field(ge=0, le=255)
    repair_index: StrictInt = Field(ge=0, le=2)
    work_kind: Literal["atomic_child", "schema_repair"]
    parent_work_id: str | None = Field(
        default=None, pattern=r"^sha256:[0-9a-f]{64}$"
    )
    terminal_status: Literal[
        "prepared",
        "issued",
        "completed",
        "budget_denied",
        "abandoned",
        "schema_exhausted",
        "transport_failed",
        "rejected",
        "cancelled",
    ]
    semantic_admission_ref: str | None = Field(
        default=None, pattern=r"^sha256:[0-9a-f]{64}$"
    )
    provider_attempt_count: StrictInt = Field(ge=0, le=3)

    @model_validator(mode="after")
    def _attempt_identity_is_exact(self):
        if self.work_kind == "atomic_child":
            if self.parent_work_id is not None or self.repair_index != 0:
                raise ValueError("atomic child cannot claim repair ancestry")
        elif self.parent_work_id is None or self.repair_index == 0:
            raise ValueError("schema repair requires its atomic parent")
        return self

    @property
    def ordering_key(self) -> tuple[int, int, str]:
        return (self.child_index, self.repair_index, self.work_id)


class ContractDecompositionProjectionV1(_StrictModel):
    """Truthful strong-failure and atomic-child execution projection."""

    schema_: Literal["contract-decomposition-projection.v1"] = Field(
        "contract-decomposition-projection.v1", alias="schema"
    )
    transition_ref: str = Field(pattern=r"^sha256:[0-9a-f]{64}$")
    source_work_id: str = Field(pattern=r"^sha256:[0-9a-f]{64}$")
    source_terminal_ref: str = Field(pattern=r"^sha256:[0-9a-f]{64}$")
    source_semantic_admission_ref: str = Field(pattern=r"^sha256:[0-9a-f]{64}$")
    source_status: Literal["schema_exhausted"] = "schema_exhausted"
    source_failure_preserved: Literal[True] = True
    role: str = Field(min_length=1, max_length=128)
    seat: StrictInt = Field(ge=0)
    endpoint_id: str = Field(min_length=1, max_length=512)
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
    child_keys: tuple[str, ...]
    child_work_ids: tuple[str, ...]
    child_semantic_admission_refs: tuple[str, ...]
    completion_ref: str | None = Field(
        default=None, pattern=r"^sha256:[0-9a-f]{64}$"
    )
    admitted_effect_refs: tuple[str, ...] = ()
    atomic_work_attempts: tuple[AtomicWorkAttemptProjectionV1, ...] = Field(
        default=(), exclude_if=lambda value: not value
    )

    @field_validator(
        "child_keys",
        "child_work_ids",
        "child_semantic_admission_refs",
        "admitted_effect_refs",
        "atomic_work_attempts",
        mode="before",
    )
    @classmethod
    def _json_arrays_are_frozen(cls, value):
        return tuple(value) if isinstance(value, list) else value

    @model_validator(mode="after")
    def _projection_is_exact(self):
        if not self.child_keys or self.child_keys != tuple(dict.fromkeys(self.child_keys)):
            raise ValueError("decomposition child keys must be nonempty and unique")
        if self.source_contract_id == self.atomic_contract_id:
            raise ValueError("decomposition must use a separately named atomic contract")
        if self.source_work_id in self.child_work_ids:
            raise ValueError("schema-exhausted source cannot be an atomic child")
        if len(set(self.child_work_ids)) != len(self.child_work_ids):
            raise ValueError("decomposition child work IDs must be unique")
        if len(set(self.child_semantic_admission_refs)) != len(
            self.child_semantic_admission_refs
        ):
            raise ValueError("decomposition child admissions must be unique")
        if len(set(self.admitted_effect_refs)) != len(self.admitted_effect_refs):
            raise ValueError("decomposition effects must be unique")
        attempt_keys = tuple(item.ordering_key for item in self.atomic_work_attempts)
        if attempt_keys != tuple(sorted(set(attempt_keys))):
            raise ValueError("atomic work attempts must be unique and sorted")
        if any(
            item.contract_id != self.atomic_contract_id
            or item.child_index >= len(self.child_keys)
            or item.child_key != self.child_keys[item.child_index]
            for item in self.atomic_work_attempts
        ):
            raise ValueError("atomic work attempt differs from decomposition")
        completed = self.completion_ref is not None
        if completed:
            if (
                len(self.child_work_ids) != len(self.child_keys)
                or len(self.child_semantic_admission_refs) != len(self.child_keys)
            ):
                raise ValueError("completed decomposition requires every atomic child")
            attempted_ids = {item.work_id for item in self.atomic_work_attempts}
            if not set(self.child_work_ids).issubset(attempted_ids):
                raise ValueError("completed children are absent from atomic attempts")
            attempts_by_id = {
                item.work_id: item for item in self.atomic_work_attempts
            }
            if any(
                attempts_by_id[work_id].terminal_status != "completed"
                or attempts_by_id[work_id].semantic_admission_ref
                != admission_ref
                for work_id, admission_ref in zip(
                    self.child_work_ids,
                    self.child_semantic_admission_refs,
                    strict=True,
                )
            ):
                raise ValueError("decomposition completion claims failed atomic work")
        elif self.child_semantic_admission_refs or self.admitted_effect_refs:
            raise ValueError("incomplete decomposition cannot claim merged results")
        return self

    @property
    def ordering_key(self) -> tuple[str, int, str, str, str]:
        return (
            self.role,
            self.seat,
            self.endpoint_id,
            self.route_sha256,
            self.transition_ref,
        )


class RouteSeatInsufficientCapabilityProjectionV1(_StrictModel):
    """Canonical terminal truth for one route seat's smallest contract."""

    schema_: Literal["route-seat-insufficient-capability-projection.v1"] = Field(
        "route-seat-insufficient-capability-projection.v1", alias="schema"
    )
    outcome_ref: str = Field(pattern=r"^sha256:[0-9a-f]{64}$")
    work_id: str = Field(pattern=r"^sha256:[0-9a-f]{64}$")
    terminal_ref: str = Field(pattern=r"^sha256:[0-9a-f]{64}$")
    provider_attempt_ref: str = Field(pattern=r"^sha256:[0-9a-f]{64}$")
    semantic_admission_ref: str = Field(pattern=r"^sha256:[0-9a-f]{64}$")
    outcome: Literal["insufficient_capability"] = "insufficient_capability"
    reason: Literal["smallest_authorized_contract_schema_exhausted"] = (
        "smallest_authorized_contract_schema_exhausted"
    )
    triggering_status: Literal["schema_exhausted"] = "schema_exhausted"
    terminal_authority: Literal["workflow.work-terminal.v1"] = (
        "workflow.work-terminal.v1"
    )
    role: str = Field(min_length=1, max_length=128)
    seat: StrictInt = Field(ge=0)
    endpoint_id: str = Field(min_length=1, max_length=512)
    route_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    final_contract_id: str = Field(min_length=1, max_length=512)
    attempted_work_ids: tuple[str, ...]
    attempted_contract_ids: tuple[str, ...]
    decomposition_transition_refs: tuple[str, ...] = ()
    compact_recovery_transition_refs: tuple[str, ...] = ()
    classification_plan_ref: str = Field(pattern=r"^sha256:[0-9a-f]{64}$")
    classification_binding_ref: str = Field(pattern=r"^sha256:[0-9a-f]{64}$")
    qualification_evidence_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    behavioral_grant_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    maximum_schema_repairs: StrictInt = Field(ge=0, le=2)
    maximum_provider_calls: StrictInt = Field(ge=1, le=3)
    observed_provider_calls: StrictInt = Field(ge=1, le=3)
    retry_failed_work: Literal[False] = False

    @field_validator(
        "attempted_work_ids",
        "attempted_contract_ids",
        "decomposition_transition_refs",
        "compact_recovery_transition_refs",
        mode="before",
    )
    @classmethod
    def _json_arrays_are_frozen(cls, value):
        return tuple(value) if isinstance(value, list) else value

    @model_validator(mode="after")
    def _terminal_projection_is_exact(self):
        if (
            not self.attempted_work_ids
            or len(self.attempted_work_ids) != len(self.attempted_contract_ids)
            or self.attempted_work_ids[-1] != self.work_id
            or self.attempted_contract_ids[-1] != self.final_contract_id
            or len(set(self.attempted_work_ids)) != len(self.attempted_work_ids)
            or len(set(self.decomposition_transition_refs))
            != len(self.decomposition_transition_refs)
            or len(set(self.compact_recovery_transition_refs))
            != len(self.compact_recovery_transition_refs)
        ):
            raise ValueError("insufficient-capability attempt history is not exact")
        if self.maximum_provider_calls != self.maximum_schema_repairs + 1:
            raise ValueError("insufficient-capability repair arithmetic differs")
        if self.observed_provider_calls > self.maximum_provider_calls:
            raise ValueError("insufficient-capability provider use exceeds authority")
        return self

    @property
    def route_seat_key(self) -> tuple[str, int, str, str]:
        return (self.role, self.seat, self.endpoint_id, self.route_sha256)


class ModelExecutionSummaryV1(_StrictModel):
    """Replay-derived presentation mode and exact compact transitions."""

    schema_: Literal["model-execution-summary.v1"] = Field(
        "model-execution-summary.v1", alias="schema"
    )
    mode: Literal[
        "base_only",
        "base_compact",
        "route_seat_base",
        "route_seat_compact_recovery",
    ]
    base_profile: Literal["standard", "frontier", "compact"]
    route_seat_bases: tuple[RouteSeatBaseProjectionV1, ...] = Field(
        default=(),
        exclude_if=lambda value: not value,
    )
    route_seat_model_classifications: tuple[
        RouteSeatModelClassificationProjectionV1, ...
    ] = Field(default=(), exclude_if=lambda value: not value)
    recovery_routes: tuple[CompactRecoveryRouteProjectionV1, ...] = ()
    contract_decompositions: tuple[ContractDecompositionProjectionV1, ...] = Field(
        default=(), exclude_if=lambda value: not value
    )
    insufficient_capability_routes: tuple[
        RouteSeatInsufficientCapabilityProjectionV1, ...
    ] = Field(default=(), exclude_if=lambda value: not value)
    event_horizon_seq: StrictInt | None = Field(
        default=None,
        ge=0,
        exclude_if=lambda value: value is None,
    )

    @field_validator(
        "route_seat_bases",
        "route_seat_model_classifications",
        "recovery_routes",
        "contract_decompositions",
        "insufficient_capability_routes",
        mode="before",
    )
    @classmethod
    def _json_routes_are_frozen(cls, value):
        return tuple(value) if isinstance(value, list) else value

    @model_validator(mode="after")
    def _mode_matches_routes(self):
        base_keys = tuple(item.route_seat_key for item in self.route_seat_bases)
        if base_keys != tuple(sorted(set(base_keys))):
            raise ValueError("route-seat base projections must be unique and sorted")
        classification_keys = tuple(
            item.route_seat_key for item in self.route_seat_model_classifications
        )
        if classification_keys != tuple(sorted(set(classification_keys))):
            raise ValueError("route-seat classifications must be unique and sorted")
        if classification_keys and base_keys and classification_keys != base_keys:
            raise ValueError("route-seat classifications differ from base projections")
        if self.route_seat_model_classifications:
            plan_refs = {
                item.classification_plan_ref
                for item in self.route_seat_model_classifications
            }
            binding_refs = {
                item.classification_binding_ref
                for item in self.route_seat_model_classifications
            }
            evidence_refs = {
                item.qualification_evidence_sha256
                for item in self.route_seat_model_classifications
            }
            if len(plan_refs) != 1 or len(binding_refs) != 1 or len(evidence_refs) != 1:
                raise ValueError("route-seat classifications must share one authority")
        keys = tuple(item.route_seat_key for item in self.recovery_routes)
        if keys != tuple(sorted(set(keys))):
            raise ValueError("compact recovery routes must be unique and sorted")
        transition_refs = tuple(
            item.transition_ref for item in self.recovery_routes
        )
        if len(transition_refs) != len(set(transition_refs)):
            raise ValueError("compact recovery transition references must be unique")
        decomposition_keys = tuple(
            item.ordering_key for item in self.contract_decompositions
        )
        if decomposition_keys != tuple(sorted(set(decomposition_keys))):
            raise ValueError("contract decompositions must be unique and sorted")
        insufficient_keys = tuple(
            item.route_seat_key for item in self.insufficient_capability_routes
        )
        if insufficient_keys != tuple(sorted(set(insufficient_keys))):
            raise ValueError("insufficient-capability routes must be unique and sorted")
        outcome_refs = tuple(
            item.outcome_ref for item in self.insufficient_capability_routes
        )
        if len(outcome_refs) != len(set(outcome_refs)):
            raise ValueError("insufficient-capability outcome references must be unique")
        base_by_key = {
            item.route_seat_key: item.base_profile
            for item in self.route_seat_bases
        }
        base_profiles = set(base_by_key.values())
        if self.mode == "base_only":
            if self.recovery_routes or (
                self.route_seat_bases
                and (len(base_profiles) != 1 or "compact" in base_profiles)
            ) or (not self.route_seat_bases and self.base_profile == "compact"):
                raise ValueError("base_only cannot contain compact recovery")
        elif self.mode == "base_compact":
            if self.recovery_routes or (
                self.route_seat_bases and base_profiles != {"compact"}
            ) or (not self.route_seat_bases and self.base_profile != "compact"):
                raise ValueError("base_compact requires one compact base profile")
        elif self.mode == "route_seat_base":
            if self.recovery_routes or not self.route_seat_bases:
                raise ValueError("route_seat_base requires only base projections")
            if len(base_profiles) < 2:
                raise ValueError("route_seat_base requires heterogeneous profiles")
        else:
            if not self.recovery_routes:
                raise ValueError("route recovery requires recovery routes")
            if self.route_seat_bases:
                if any(
                    route.route_seat_key not in base_by_key
                    or route.source_profile
                    != base_by_key[route.route_seat_key]
                    for route in self.recovery_routes
                ):
                    raise ValueError(
                        "recovery route source differs from its route-seat base"
                    )
            elif (
                self.base_profile not in {"standard", "frontier"}
                or any(
                    route.source_profile != self.base_profile
                    for route in self.recovery_routes
                )
            ):
                raise ValueError("recovery route source differs from base profile")
        decomposition_refs = {
            item.transition_ref for item in self.contract_decompositions
        }
        compact_refs = {item.transition_ref for item in self.recovery_routes}
        classification_by_key = {
            item.route_seat_key: item
            for item in self.route_seat_model_classifications
        }
        for outcome in self.insufficient_capability_routes:
            if outcome.route_seat_key not in base_by_key:
                raise ValueError("insufficient capability lacks route-seat base authority")
            classification = classification_by_key.get(outcome.route_seat_key)
            if (
                classification is None
                or classification.classification_plan_ref
                != outcome.classification_plan_ref
                or classification.classification_binding_ref
                != outcome.classification_binding_ref
                or classification.qualification_evidence_sha256
                != outcome.qualification_evidence_sha256
                or classification.behavioral_grant_sha256
                != outcome.behavioral_grant_sha256
            ):
                raise ValueError(
                    "insufficient capability differs from classification authority"
                )
            if not set(outcome.decomposition_transition_refs).issubset(
                decomposition_refs
            ):
                raise ValueError("insufficient capability lacks decomposition history")
            if not set(outcome.compact_recovery_transition_refs).issubset(
                compact_refs
            ):
                raise ValueError("insufficient capability lacks compact history")
        return self


class RunStopReceiptV1(_StrictModel):
    """Typed canonical stop receipt carried by current v6 run results."""

    schema_: Literal["deepreason-run-stop-v1"] = Field(
        "deepreason-run-stop-v1", alias="schema"
    )
    reason: StopReason
    policy_digest: str = Field(pattern=r"^[0-9a-f]{64}$")
    metrics: StopMetrics
    event_seq: StrictInt = Field(ge=0)
    digest: str = Field(pattern=r"^[0-9a-f]{64}$")

    @model_validator(mode="after")
    def _canonical_self_digest(self):
        unsigned = self.model_dump(
            mode="json",
            by_alias=True,
            exclude={"digest"},
        )
        if self.digest != sha256_hex(canonical_json(unsigned)):
            raise ValueError("run stop digest differs from its canonical payload")
        return self


def derive_model_execution_summary(
    harness,
    manifest,
    *,
    event_horizon_seq: int | None = None,
) -> ModelExecutionSummaryV1:
    """Project v6 execution only from manifest-bound canonical replay."""

    if getattr(manifest, "schema_version", None) != 6:
        raise ValueError("model execution summary requires RunManifest v6")
    profile = str(manifest.model_profile)
    if profile not in {"standard", "frontier", "compact"}:
        raise ValueError("v6 manifest has an unknown model profile")
    all_events = tuple(harness.log.read())
    if event_horizon_seq is not None:
        if type(event_horizon_seq) is not int or event_horizon_seq < 0:
            raise ValueError("model execution event horizon is invalid")
        last_seq = all_events[-1].seq if all_events else 0
        if event_horizon_seq > last_seq:
            raise ValueError("model execution event horizon exceeds durable history")
        from deepreason.workflow.replay import replay_workflow

        events = tuple(
            event for event in all_events if event.seq <= event_horizon_seq
        )
        state = replay_workflow(events, harness.objects, manifest=manifest)
    else:
        events = all_events
        state = harness.workflow_state
    replay_manifest = getattr(state, "_run_manifest", None)
    if replay_manifest is None or replay_manifest.sha256 != manifest.sha256:
        raise ValueError("model execution replay differs from the bound manifest")

    from deepreason.llm.firewall import route_fingerprint
    from deepreason.run_manifest import resolve_route_seat_base_profile

    route_seat_bases: list[RouteSeatBaseProjectionV1] = []
    plan = manifest.route_seat_presentation_plan
    if plan is not None:
        for entry in plan.entries:
            route = manifest.roles[entry.role][entry.seat]
            resolved = resolve_route_seat_base_profile(
                manifest,
                role=entry.role,
                seat=entry.seat,
                endpoint_id=route.endpoint_id,
            )
            if resolved != entry.base_profile:
                raise ValueError("route-seat base projection differs from manifest")
            route_seat_bases.append(
                RouteSeatBaseProjectionV1(
                    role=entry.role,
                    seat=entry.seat,
                    endpoint_id=route.endpoint_id,
                    route_sha256=route_fingerprint(route),
                    base_profile=resolved,
                    selection_basis=entry.selection_basis,
                )
            )

    classifications: list[RouteSeatModelClassificationProjectionV1] = []
    classification = state.route_seat_model_classification
    binding = state.model_classification_binding
    if classification is not None or binding is not None:
        if classification is None or binding is None:
            raise ValueError("model classification authority is incomplete")
        state._validate_model_classification(manifest, classification)
        if (
            binding.classification_plan_ref != classification.id
            or binding.manifest_digest != manifest.sha256
            or binding.qualification_evidence_sha256
            != classification.qualification_evidence_sha256
        ):
            raise ValueError("model classification binding differs from its plan")
        for entry in classification.entries:
            classifications.append(
                RouteSeatModelClassificationProjectionV1(
                    role=entry.role,
                    seat=entry.seat,
                    endpoint_id=entry.endpoint_id,
                    route_sha256=entry.route_sha256,
                    behavioral_grant_sha256=entry.behavioral_grant_sha256,
                    selected_class=entry.selected_class,
                    authorized_contract_ids=entry.authorized_contract_ids,
                    evidence_pair_ids=entry.evidence_pair_ids,
                    qualification_evidence_sha256=(
                        classification.qualification_evidence_sha256
                    ),
                    classification_plan_ref=classification.id,
                    classification_binding_ref=binding.id,
                )
            )

    event_seq_by_transition: dict[str, int] = {}
    for event in events:
        for object_id in event.outputs:
            if object_id in event_seq_by_transition:
                continue
            if any(
                transition.id == object_id
                for transition in state.compact_recovery_by_route_seat.values()
            ):
                event_seq_by_transition[object_id] = event.seq

    projections: list[CompactRecoveryRouteProjectionV1] = []
    for key, transition in sorted(
        state.compact_recovery_by_route_seat.items()
    ):
        transition_seq = event_seq_by_transition.get(transition.id)
        if transition_seq is None:
            raise ValueError("compact transition is absent from canonical history")
        item = state.transaction_work.get(transition.work_id)
        terminal = item.terminal if item is not None else None
        if (
            terminal is None
            or terminal.status != "schema_exhausted"
            or terminal.id is None
            or terminal.compact_recovery_transition_ref != transition.id
            or terminal.semantic_admission_ref
            != transition.semantic_admission_ref
        ):
            raise ValueError("compact transition lacks its schema-exhausted terminal")
        source_profile = resolve_route_seat_base_profile(
            manifest,
            role=key[0],
            seat=key[1],
            endpoint_id=key[2],
        )
        if transition.source_profile != source_profile:
            raise ValueError("compact transition differs from route-seat base")

        work_ids: set[str] = set()
        contract_ids: set[str] = set()
        for event in events:
            call = event.llm
            if call is None or event.seq <= transition_seq:
                continue
            matching = tuple(
                attempt
                for attempt in call.attempt_trace
                if (
                    call.role,
                    attempt.seat,
                    attempt.endpoint_id,
                    attempt.route_sha256,
                )
                == key
            )
            if not matching:
                continue
            if any(
                attempt.model_profile != transition.source_profile
                or attempt.transport_profile != transition.target_profile
                for attempt in matching
            ):
                raise ValueError(
                    "later route-seat call differs from compact transition authority"
                )
            if call.work_order_id is None:
                raise ValueError("transactional compact call lacks a work identity")
            if call.work_order_id == transition.work_id:
                raise ValueError("schema-exhausted work was retried under compact")
            if call.work_order_id in work_ids:
                raise ValueError("one compact work item has multiple provider calls")
            work_ids.add(call.work_order_id)
            contract_ids.update(attempt.contract_id for attempt in matching)

        completed = {
            work_id
            for work_id in work_ids
            if work_id in state.transaction_work
            and state.transaction_work[work_id].terminal is not None
            and state.transaction_work[work_id].terminal.status == "completed"
        }
        if any(work_id not in state.transaction_work for work_id in work_ids):
            raise ValueError("compact call is absent from transaction replay")
        projections.append(
            CompactRecoveryRouteProjectionV1(
                transition_ref=transition.id,
                triggering_work_id=transition.work_id,
                triggering_terminal_ref=terminal.id,
                triggering_semantic_admission_ref=(
                    transition.semantic_admission_ref
                ),
                role=key[0],
                seat=key[1],
                endpoint_id=key[2],
                route_sha256=key[3],
                source_profile=transition.source_profile,
                target_profile=transition.target_profile,
                trigger=transition.trigger,
                sticky=transition.sticky,
                applies_to=transition.applies_to,
                retry_failed_work=transition.retry_failed_work,
                subsequent_compact_call_count=len(work_ids),
                subsequent_compact_work_ids=tuple(sorted(work_ids)),
                actual_contract_ids=tuple(sorted(contract_ids)),
                completed_compact_work_ids=tuple(sorted(completed)),
            )
        )

    decompositions: list[ContractDecompositionProjectionV1] = []
    for transition in sorted(
        state.contract_decomposition_by_source_work.values(),
        key=lambda item: (
            item.route_lease.role,
            item.route_lease.seat,
            item.route_lease.endpoint_id,
            item.route_lease.route_sha256,
            item.id,
        ),
    ):
        source = state.transaction_work.get(transition.source_work_id)
        if (
            source is None
            or source.terminal is None
            or source.terminal.status != "schema_exhausted"
            or source.terminal.id != transition.source_terminal_ref
            or source.terminal.semantic_admission_ref
            != transition.source_semantic_admission_ref
        ):
            raise ValueError("decomposition lacks its preserved strong failure")
        completion = state.contract_decomposition_completion_by_transition.get(
            transition.id
        )
        atomic_attempts: list[AtomicWorkAttemptProjectionV1] = []
        for candidate in state.transaction_work.values():
            root = state._root_transaction_item(candidate)
            root_payload = root.preparation.task_payload_value
            if (
                not isinstance(root_payload, Mapping)
                or root_payload.get("schema") != "contract-decomposition-child.v1"
                or root_payload.get("decomposition_transition_ref") != transition.id
            ):
                continue
            child_index = root_payload.get("child_index")
            if type(child_index) is not int or not 0 <= child_index < len(
                transition.child_keys
            ):
                raise ValueError("atomic work has an invalid child index")
            payload = candidate.preparation.task_payload_value
            is_repair = (
                isinstance(payload, Mapping)
                and payload.get("schema") == "repair.semantic-task.v1"
            )
            terminal = candidate.terminal
            admission = candidate.admissions.get(candidate.preparation.attempt_index)
            atomic_attempts.append(
                AtomicWorkAttemptProjectionV1(
                    work_id=candidate.preparation.id,
                    contract_id=candidate.preparation.contract_id,
                    child_key=transition.child_keys[child_index],
                    child_index=child_index,
                    repair_index=(candidate.preparation.attempt_index if is_repair else 0),
                    work_kind=("schema_repair" if is_repair else "atomic_child"),
                    parent_work_id=(
                        payload.get("parent_work_id") if is_repair else None
                    ),
                    terminal_status=(
                        terminal.status
                        if terminal is not None
                        else ("issued" if candidate.issued else "prepared")
                    ),
                    semantic_admission_ref=(admission.id if admission is not None else None),
                    provider_attempt_count=len(candidate.provider_attempts),
                )
            )
        atomic_attempts.sort(key=lambda item: item.ordering_key)
        decompositions.append(
            ContractDecompositionProjectionV1(
                transition_ref=transition.id,
                source_work_id=transition.source_work_id,
                source_terminal_ref=transition.source_terminal_ref,
                source_semantic_admission_ref=(
                    transition.source_semantic_admission_ref
                ),
                role=transition.route_lease.role,
                seat=transition.route_lease.seat,
                endpoint_id=transition.route_lease.endpoint_id,
                route_sha256=transition.route_lease.route_sha256,
                source_contract_id=transition.source_contract_id,
                atomic_contract_id=transition.atomic_contract_id,
                trigger=transition.trigger,
                child_partition=transition.child_partition,
                child_keys=transition.child_keys,
                child_work_ids=(
                    completion.child_work_ids if completion is not None else ()
                ),
                child_semantic_admission_refs=(
                    completion.child_semantic_admission_refs
                    if completion is not None
                    else ()
                ),
                completion_ref=(completion.id if completion is not None else None),
                admitted_effect_refs=(
                    completion.admitted_effect_refs if completion is not None else ()
                ),
                atomic_work_attempts=tuple(atomic_attempts),
            )
        )

    insufficient_capability: list[RouteSeatInsufficientCapabilityProjectionV1] = []
    for key, outcome in sorted(state.insufficient_capability_by_route_seat.items()):
        item = state.transaction_work.get(outcome.work_id)
        terminal = item.terminal if item is not None else None
        if (
            terminal is None
            or terminal.status != "schema_exhausted"
            or terminal.insufficient_capability_ref != outcome.id
            or terminal.provider_attempt_ref != outcome.provider_attempt_ref
            or terminal.semantic_admission_ref != outcome.semantic_admission_ref
        ):
            raise ValueError("insufficient capability lacks its exact work terminal")
        insufficient_capability.append(
            RouteSeatInsufficientCapabilityProjectionV1(
                outcome_ref=outcome.id,
                work_id=outcome.work_id,
                terminal_ref=terminal.id,
                provider_attempt_ref=outcome.provider_attempt_ref,
                semantic_admission_ref=outcome.semantic_admission_ref,
                outcome=outcome.outcome,
                reason=outcome.reason,
                terminal_authority=outcome.terminal_authority,
                role=key[0],
                seat=key[1],
                endpoint_id=key[2],
                route_sha256=key[3],
                final_contract_id=outcome.contract_id,
                attempted_work_ids=outcome.attempted_work_ids,
                attempted_contract_ids=outcome.attempted_contract_ids,
                decomposition_transition_refs=(
                    outcome.decomposition_transition_refs
                ),
                compact_recovery_transition_refs=(
                    outcome.compact_recovery_transition_refs
                ),
                classification_plan_ref=outcome.classification_plan_ref,
                classification_binding_ref=outcome.classification_binding_ref,
                qualification_evidence_sha256=(
                    outcome.qualification_evidence_sha256
                ),
                behavioral_grant_sha256=outcome.behavioral_grant_sha256,
                maximum_schema_repairs=outcome.maximum_schema_repairs,
                maximum_provider_calls=outcome.maximum_provider_calls,
                observed_provider_calls=outcome.observed_provider_calls,
                retry_failed_work=outcome.retry_failed_work,
            )
        )

    if projections:
        mode = "route_seat_compact_recovery"
    elif route_seat_bases and len(
        {item.base_profile for item in route_seat_bases}
    ) > 1:
        mode = "route_seat_base"
    elif route_seat_bases and route_seat_bases[0].base_profile == "compact":
        mode = "base_compact"
    elif not route_seat_bases and profile == "compact":
        mode = "base_compact"
    else:
        mode = "base_only"
    return ModelExecutionSummaryV1(
        mode=mode,
        base_profile=profile,
        route_seat_bases=tuple(route_seat_bases),
        route_seat_model_classifications=tuple(classifications),
        recovery_routes=tuple(projections),
        contract_decompositions=tuple(decompositions),
        insufficient_capability_routes=tuple(insufficient_capability),
        event_horizon_seq=event_horizon_seq,
    )


class RunResultV2(BaseModel):
    """Typed v6 terminal envelope; workload-specific fields remain extensible."""

    model_config = ConfigDict(extra="allow", frozen=True, strict=True)

    schema_: Literal["deepreason-run-result-v2"] = Field(
        "deepreason-run-result-v2", alias="schema"
    )
    state: Literal["completed", "cancelled", "failed"]
    workload: str = Field(min_length=1, max_length=128)
    verification: RunVerificationSummaryV2
    completion_status: Literal["satisfied", "incomplete"]
    canonical_bridge_eligible: bool
    terminal_commitment_ref: str | None = Field(
        default=None,
        pattern=r"^sha256:[0-9a-f]{64}$",
        exclude_if=lambda value: value is None,
    )
    stop: RunStopReceiptV1 | None = Field(
        default=None,
        exclude_if=lambda value: value is None,
    )
    model_execution: ModelExecutionSummaryV1 | None = Field(
        default=None,
        exclude_if=lambda value: value is None,
    )

    @model_validator(mode="after")
    def _derived_terminal_fields(self):
        expected_completion = (
            "satisfied" if self.verification.completion_satisfied else "incomplete"
        )
        if self.completion_status != expected_completion:
            raise ValueError("completion status differs from verification summary")
        expected_bridge = self.state == "completed" and self.verification.valid
        if self.canonical_bridge_eligible != expected_bridge:
            raise ValueError("canonical bridge eligibility is inconsistent")
        if (
            self.model_execution is not None
            and self.model_execution.event_horizon_seq is not None
        ):
            if self.stop is None:
                raise ValueError("model execution horizon requires a typed run stop")
            if self.model_execution.event_horizon_seq != self.stop.event_seq:
                raise ValueError("model execution horizon differs from run stop")
        elif self.stop is not None and self.model_execution is not None:
            raise ValueError("typed run stop requires a model execution horizon")
        if self.terminal_commitment_ref is not None and (
            self.stop is None
            or self.model_execution is None
            or self.model_execution.event_horizon_seq is None
        ):
            raise ValueError(
                "terminal commitment reference requires stop and execution horizon"
            )
        return self


def run_result_exit_code(payload: dict[str, Any]) -> int:
    """Map one canonical terminal payload to the stable CLI exit contract."""

    state = payload.get("state")
    if state not in {"completed", "cancelled", "failed"}:
        return 6
    verification = payload.get("verification")
    if isinstance(verification, dict) and (
        verification.get("integrity_valid") is False
        or verification.get("security_valid") is False
    ):
        return 5
    if state == "completed":
        return 0
    if state == "cancelled":
        return 3
    if state == "failed":
        return 4
    return 4


class RunCancellationAcceptedV1(_StrictModel):
    schema_: Literal["application.text-run.cancellation-accepted.v1"] = Field(
        "application.text-run.cancellation-accepted.v1", alias="schema"
    )
    lifecycle: Literal["cancellation-requested"] = "cancellation-requested"
    root: str
    safe_boundary: Literal["completed-cycle"] = "completed-cycle"

    def presentation_payload(self) -> dict[str, Any]:
        return {
            "state": self.lifecycle,
            "root": self.root,
            "safe_boundary": self.safe_boundary,
        }


class OperatorCancellationIntentV1(_StrictModel):
    """Durable operator request; the controller still owns terminalization."""

    schema_: Literal["application.operator-cancellation-intent.v1"] = Field(
        "application.operator-cancellation-intent.v1", alias="schema"
    )
    id: str = Field(pattern=r"^sha256:[0-9a-f]{64}$")
    sequence: StrictInt = Field(ge=0)
    manifest_digest: str = Field(pattern=r"^[0-9a-f]{64}$")
    process_digest: str = Field(pattern=r"^sha256:[0-9a-f]{64}$")
    last_control_seq: StrictInt = Field(ge=-1)
    safe_boundary: Literal["completed-cycle"] = "completed-cycle"

    @classmethod
    def create(cls, **values):
        payload = {
            "schema": "application.operator-cancellation-intent.v1",
            "safe_boundary": "completed-cycle",
            **values,
        }
        record_id = "sha256:" + sha256_hex(
            b"application.operator-cancellation-intent.v1\x00"
            + canonical_json(payload)
        )
        return cls(id=record_id, **values)

    @model_validator(mode="after")
    def _canonical_id(self):
        payload = self.model_dump(
            mode="json", by_alias=True, exclude={"id"}
        )
        expected = "sha256:" + sha256_hex(
            b"application.operator-cancellation-intent.v1\x00"
            + canonical_json(payload)
        )
        if self.id != expected:
            raise ValueError("operator cancellation intent ID is not canonical")
        return self


__all__ = [
    "CancelTextRunIntentV1",
    "ContinueTextRunIntentV1",
    "InspectTextRunIntentV1",
    "OutstandingWorkItemProjectionV1",
    "OutstandingWorkResultV1",
    "OperatorCancellationIntentV1",
    "RunBudgetIntentV1",
    "RunCancellationAcceptedV1",
    "RunProgressResultV1",
    "RunResultV2",
    "RunStartedV1",
    "RunVerificationSummaryV2",
    "StartTextRunIntentV1",
    "TextRunTerminalResultV1",
    "WatchTextRunIntentV1",
    "run_result_exit_code",
]
