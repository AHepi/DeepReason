"""Transactional provider-work authority for RunManifest v6.

The immutable records in this module deliberately separate preparation from
canonical exposure.  Content-addressed objects may be written while a request
is being prepared, but context becomes an asserted exposure only when one
``control.event.v3`` append makes the reservation, receipt, and authorization
bundle reachable together.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
import re
from typing import Any, Literal

from pydantic import Field, field_validator, model_validator

from deepreason.llm.budget import Reservation
from deepreason.workflow.models import (
    IdentifiedWorkflowRecord,
    RouteLeaseRefV1,
    WorkflowRecord,
    WorkflowTaskKind,
    freeze_workflow_json,
)


_ID = r"^sha256:[0-9a-f]{64}$"
_DIGEST = r"^[0-9a-f]{64}$"


class ContextNamespace(str, Enum):
    SOURCE = "source"
    SIMULATION = "simulation"
    SCRATCH = "scratch"


class RouteSeatModelClassificationV1(WorkflowRecord):
    """Deterministic result for one exact behavioral route-seat grant."""

    role: str = Field(min_length=1, max_length=64)
    seat: int = Field(ge=0, le=1_023)
    endpoint_id: str = Field(min_length=1, max_length=256)
    route_sha256: str = Field(pattern=_DIGEST)
    behavioral_grant_sha256: str = Field(pattern=_DIGEST)
    selected_class: Literal[
        "qualified_exact_behavior",
        "unqualified_exact_behavior",
        "inactive_no_authorized_contract",
    ]
    authorized_contract_ids: tuple[str, ...] = ()
    evidence_pair_ids: tuple[str, ...] = ()

    @model_validator(mode="after")
    def _classification_is_exact(self):
        if self.authorized_contract_ids != tuple(
            sorted(set(self.authorized_contract_ids))
        ):
            raise ValueError("classification contract IDs must be unique and sorted")
        if self.evidence_pair_ids != tuple(sorted(set(self.evidence_pair_ids))):
            raise ValueError("classification evidence pair IDs must be unique and sorted")
        inactive = self.selected_class == "inactive_no_authorized_contract"
        if inactive != (not self.authorized_contract_ids):
            raise ValueError("inactive classification must have no authorized contracts")
        if inactive != (not self.evidence_pair_ids):
            raise ValueError("inactive classification must have no evidence pairs")
        return self


class RouteSeatModelClassificationPlanV1(IdentifiedWorkflowRecord):
    """Manifest-bound deterministic selection derived from doctor evidence."""

    _identity_domain = "workflow.route-seat-model-classification-plan.v1"

    schema_: Literal["workflow.route-seat-model-classification-plan.v1"] = Field(
        "workflow.route-seat-model-classification-plan.v1", alias="schema"
    )
    manifest_digest: str = Field(pattern=_DIGEST)
    algorithm: Literal["exact-production-contract-qualification.v1"] = (
        "exact-production-contract-qualification.v1"
    )
    algorithm_version: Literal[1] = 1
    qualification_evidence_sha256: str = Field(pattern=_DIGEST)
    entries: tuple[RouteSeatModelClassificationV1, ...]

    @model_validator(mode="after")
    def _entries_are_complete_ordered_identities(self):
        if not self.entries:
            raise ValueError("model classification plan requires route-seat entries")
        keys = tuple(
            (entry.role, entry.seat, entry.endpoint_id, entry.route_sha256)
            for entry in self.entries
        )
        if keys != tuple(sorted(set(keys))):
            raise ValueError("model classification entries must be unique and sorted")
        return self


class ModelClassificationBindingV1(IdentifiedWorkflowRecord):
    """Exact-once durable reachability for one qualified classification plan."""

    _identity_domain = "workflow.model-classification-binding.v1"

    schema_: Literal["workflow.model-classification-binding.v1"] = Field(
        "workflow.model-classification-binding.v1", alias="schema"
    )
    manifest_digest: str = Field(pattern=_DIGEST)
    classification_plan_ref: str = Field(pattern=_ID)
    algorithm: Literal["exact-production-contract-qualification.v1"] = (
        "exact-production-contract-qualification.v1"
    )
    algorithm_version: Literal[1] = 1
    qualification_evidence_sha256: str = Field(pattern=_DIGEST)


class WorkTransitionKind(str, Enum):
    WORK_PREPARED = "work_prepared"
    WORK_ISSUED = "work_issued"
    BUDGET_DENIED = "budget_denied"
    PROVIDER_RESULT = "provider_result"
    SEMANTIC_ADMISSION = "semantic_admission"
    WORK_TERMINATED = "work_terminated"


class VisibleContextItemV1(WorkflowRecord):
    namespace: ContextNamespace
    alias: str = Field(pattern=r"^(SRC|SIM|SCR)_[0-9]{3,}$")
    object_ref: str = Field(min_length=1, max_length=512)
    content_sha256: str = Field(pattern=_DIGEST)
    planned_bytes: int = Field(ge=0, le=64 * 1024 * 1024)

    @model_validator(mode="after")
    def _namespace_is_disjoint(self):
        expected = {
            ContextNamespace.SOURCE: "SRC_",
            ContextNamespace.SIMULATION: "SIM_",
            ContextNamespace.SCRATCH: "SCR_",
        }[self.namespace]
        if not self.alias.startswith(expected):
            raise ValueError("visible alias belongs to another context namespace")
        return self


class WorkPreparationV1(IdentifiedWorkflowRecord):
    """Durable-but-unissued authority proposal for one provider attempt."""

    _identity_domain = "workflow.work-preparation.v1"

    schema_: Literal["workflow.work-preparation.v1"] = Field(
        "workflow.work-preparation.v1", alias="schema"
    )
    manifest_digest: str = Field(pattern=_DIGEST)
    controller_version: Literal["workflow.controller.v3"] = "workflow.controller.v3"
    workflow_profile: Literal["inquiry.active.v2"] = "inquiry.active.v2"
    task_kind: WorkflowTaskKind
    attempt_index: int = Field(ge=0, le=64)
    formal_fence_seq: int = Field(ge=0)
    scratch_fence_seq: int = Field(ge=0)
    trigger_ref: str = Field(min_length=1, max_length=512)
    target_refs: tuple[str, ...] = ()
    input_refs: tuple[str, ...] = ()
    route_lease: RouteLeaseRefV1
    contract_id: str = Field(min_length=1, max_length=512)
    source_terminal_commitment_ref: str | None = Field(
        default=None,
        pattern=_ID,
        exclude_if=lambda value: value is None,
    )
    task_payload_ref: str | None = Field(default=None, max_length=512)
    task_payload_value: Any | None = None

    @field_validator("target_refs", "input_refs")
    @classmethod
    def _unique_refs(cls, value):
        if len(value) != len(set(value)):
            raise ValueError("work preparation references must be unique")
        return tuple(value)

    @field_validator("task_payload_value", mode="before")
    @classmethod
    def _freeze_payload(cls, value):
        return None if value is None else freeze_workflow_json(value)

    @model_validator(mode="after")
    def _one_state_fence_and_payload(self):
        if self.formal_fence_seq != self.scratch_fence_seq:
            raise ValueError("transactional work requires one immutable state fence")
        if (self.task_payload_ref is None) == (self.task_payload_value is None):
            raise ValueError("work preparation requires exactly one payload source")
        return self

    @property
    def work_id(self) -> str:
        return self.id


class ContextPackPlanV1(IdentifiedWorkflowRecord):
    """Pure packing plan; it is not evidence that context was exposed."""

    _identity_domain = "workflow.context-pack-plan.v1"

    schema_: Literal["workflow.context-pack-plan.v1"] = Field(
        "workflow.context-pack-plan.v1", alias="schema"
    )
    work_id: str = Field(pattern=_ID)
    attempt_index: int = Field(ge=0, le=64)
    plan_kind: Literal[
        "dossier",
        "scratch",
        "simulation",
        "simulation_result",
        "combined",
    ]
    items: tuple[VisibleContextItemV1, ...] = ()
    maximum_bytes: int = Field(ge=0, le=64 * 1024 * 1024)
    rendered_bytes: int = Field(ge=0, le=64 * 1024 * 1024)

    @field_validator("items")
    @classmethod
    def _unique_aliases_and_refs(cls, value):
        aliases = [item.alias for item in value]
        refs = [item.object_ref for item in value]
        if len(aliases) != len(set(aliases)) or len(refs) != len(set(refs)):
            raise ValueError("context plan aliases and object references must be unique")
        return tuple(value)

    @model_validator(mode="after")
    def _within_plan_budget(self):
        if self.rendered_bytes > self.maximum_bytes:
            raise ValueError("rendered context exceeds the plan byte ceiling")
        if sum(item.planned_bytes for item in self.items) < self.rendered_bytes:
            raise ValueError("rendered context cannot exceed planned item bytes")
        return self


class TokenReservationV2(IdentifiedWorkflowRecord):
    """Content-addressed evidence that a conservative token bound was booked."""

    _identity_domain = "workflow.token-reservation.v2"

    schema_: Literal["workflow.token-reservation.v2"] = Field(
        "workflow.token-reservation.v2", alias="schema"
    )
    work_id: str = Field(pattern=_ID)
    attempt_index: int = Field(ge=0, le=64)
    meter_scope: str = Field(min_length=1, max_length=512)
    prompt_sha256: str = Field(pattern=_DIGEST)
    prompt_bound_tokens: int = Field(ge=0)
    completion_bound_tokens: int = Field(ge=0)
    reserved_tokens: int = Field(ge=0)
    state: Literal["reserved"] = "reserved"

    @model_validator(mode="after")
    def _bound_is_exact(self):
        if self.reserved_tokens != (
            self.prompt_bound_tokens + self.completion_bound_tokens
        ):
            raise ValueError("reservation total differs from its conservative bounds")
        return self


class ContextExposureReceiptV2(IdentifiedWorkflowRecord):
    """Canonical exposure claim created only as part of ``WORK_ISSUED``."""

    _identity_domain = "workflow.context-exposure-receipt.v2"

    schema_: Literal["workflow.context-exposure-receipt.v2"] = Field(
        "workflow.context-exposure-receipt.v2", alias="schema"
    )
    work_id: str = Field(pattern=_ID)
    attempt_index: int = Field(ge=0, le=64)
    prompt_sha256: str = Field(pattern=_DIGEST)
    context_plan_refs: tuple[str, ...] = Field(default=(), max_length=16)
    exposed_items: tuple[VisibleContextItemV1, ...] = ()

    @field_validator("context_plan_refs")
    @classmethod
    def _unique_plans(cls, value):
        if any(not str(ref).startswith("sha256:") for ref in value):
            raise ValueError("context exposure must name content-addressed plans")
        if len(value) != len(set(value)):
            raise ValueError("context exposure plan references must be unique")
        return tuple(value)

    @field_validator("exposed_items")
    @classmethod
    def _unique_exposure(cls, value):
        aliases = [item.alias for item in value]
        refs = [item.object_ref for item in value]
        if len(aliases) != len(set(aliases)) or len(refs) != len(set(refs)):
            raise ValueError("one exposure cannot duplicate an alias or object")
        return tuple(value)


class WorkLifecycleTransitionV1(IdentifiedWorkflowRecord):
    """Controller-v3 decision named by ``control.event.v3``."""

    _identity_domain = "workflow.work-lifecycle-transition.v1"

    schema_: Literal["workflow.work-lifecycle-transition.v1"] = Field(
        "workflow.work-lifecycle-transition.v1", alias="schema"
    )
    controller_version: Literal["workflow.controller.v3"] = "workflow.controller.v3"
    workflow_profile: Literal["inquiry.active.v2"] = "inquiry.active.v2"
    work_id: str = Field(pattern=_ID)
    attempt_index: int = Field(ge=0, le=64)
    transition_kind: WorkTransitionKind
    trigger_ref: str = Field(min_length=1, max_length=512)


class DispatchAuthorizationBundleV1(IdentifiedWorkflowRecord):
    """Complete, immutable capability passed to the v6 provider adapter."""

    _identity_domain = "workflow.dispatch-authorization-bundle.v1"

    schema_: Literal["workflow.dispatch-authorization-bundle.v1"] = Field(
        "workflow.dispatch-authorization-bundle.v1", alias="schema"
    )
    work_id: str = Field(pattern=_ID)
    attempt_index: int = Field(ge=0, le=64)
    contract_id: str = Field(min_length=1, max_length=512)
    route_lease: RouteLeaseRefV1
    prompt_sha256: str = Field(pattern=_DIGEST)
    reservation_ref: str = Field(pattern=_ID)
    exposure_receipt_ref: str = Field(pattern=_ID)
    issue_transition_ref: str = Field(pattern=_ID)

    def verify_dispatch(
        self,
        *,
        work_id: str,
        attempt_index: int,
        contract_id: str,
        route_lease: RouteLeaseRefV1,
        prompt_sha256: str,
        reservation_ref: str,
    ) -> None:
        supplied = (
            work_id,
            attempt_index,
            contract_id,
            route_lease,
            prompt_sha256,
            reservation_ref,
        )
        expected = (
            self.work_id,
            self.attempt_index,
            self.contract_id,
            self.route_lease,
            self.prompt_sha256,
            self.reservation_ref,
        )
        if supplied != expected:
            raise ValueError("dispatch differs from its authorization bundle")


class ProviderAttemptV1(IdentifiedWorkflowRecord):
    _identity_domain = "workflow.provider-attempt.v1"

    schema_: Literal["workflow.provider-attempt.v1"] = Field(
        "workflow.provider-attempt.v1", alias="schema"
    )
    work_id: str = Field(pattern=_ID)
    attempt_index: int = Field(ge=0, le=64)
    authorization_bundle_ref: str = Field(pattern=_ID)
    contract_id: str = Field(min_length=1, max_length=512)
    route_lease: RouteLeaseRefV1
    prompt_sha256: str = Field(pattern=_DIGEST)
    raw_ref: str | None = Field(default=None, max_length=512)
    outcome: Literal["provider_result", "transport_failure"]
    usage_status: Literal["exact", "unknown"]
    prompt_tokens: int | None = Field(default=None, ge=0)
    completion_tokens: int | None = Field(default=None, ge=0)
    diagnostic_ref: str | None = Field(default=None, max_length=512)

    @model_validator(mode="after")
    def _provider_shape(self):
        counts_known = self.prompt_tokens is not None and self.completion_tokens is not None
        if self.usage_status == "exact" and not counts_known:
            raise ValueError("exact provider usage requires both token counts")
        if self.usage_status == "unknown" and (
            self.prompt_tokens is not None or self.completion_tokens is not None
        ):
            raise ValueError("unknown provider usage cannot assert token counts")
        if self.outcome == "provider_result" and self.raw_ref is None:
            raise ValueError("durable provider result requires a raw blob reference")
        if self.outcome == "transport_failure" and self.diagnostic_ref is None:
            raise ValueError("transport failure requires a diagnostic reference")
        return self


class SemanticAdmissionV1(IdentifiedWorkflowRecord):
    _identity_domain = "workflow.semantic-admission.v1"

    schema_: Literal["workflow.semantic-admission.v1"] = Field(
        "workflow.semantic-admission.v1", alias="schema"
    )
    work_id: str = Field(pattern=_ID)
    attempt_index: int = Field(ge=0, le=64)
    provider_attempt_ref: str = Field(pattern=_ID)
    outcome: Literal["admitted", "rejected", "schema_exhausted", "unrepairable"]
    admitted_refs: tuple[str, ...] = ()
    diagnostic_refs: tuple[str, ...] = ()
    authorized_pointers: tuple[str, ...] = ()

    @field_validator("admitted_refs", "diagnostic_refs", "authorized_pointers")
    @classmethod
    def _unique_values(cls, value):
        if len(value) != len(set(value)):
            raise ValueError("semantic admission values must be unique")
        return tuple(value)

    @model_validator(mode="after")
    def _admission_shape(self):
        if self.outcome == "admitted" and not self.admitted_refs:
            raise ValueError("admitted provider work requires semantic output references")
        if self.outcome != "admitted" and self.admitted_refs:
            raise ValueError("failed semantic admission cannot expose admitted outputs")
        return self


class CompactRecoveryTransitionV1(IdentifiedWorkflowRecord):
    """Durable authority to use compact presentation on one route seat later."""

    _identity_domain = "workflow.compact-recovery-transition.v1"

    schema_: Literal["workflow.compact-recovery-transition.v1"] = Field(
        "workflow.compact-recovery-transition.v1", alias="schema"
    )
    manifest_digest: str = Field(pattern=_DIGEST)
    work_id: str = Field(pattern=_ID)
    attempt_index: int = Field(ge=0, le=64)
    route_lease: RouteLeaseRefV1
    source_profile: Literal["standard", "frontier"]
    target_profile: Literal["compact"] = "compact"
    trigger: Literal["schema_exhausted"] = "schema_exhausted"
    scope: Literal["route_seat"] = "route_seat"
    sticky: Literal[True] = True
    applies_to: Literal["all_subsequent_model_calls"] = (
        "all_subsequent_model_calls"
    )
    retry_failed_work: Literal[False] = False
    semantic_admission_ref: str = Field(pattern=_ID)

    @property
    def route_seat_key(self) -> tuple[str, int, str, str]:
        lease = self.route_lease
        return (lease.role, lease.seat, lease.endpoint_id, lease.route_sha256)


class ContractDecompositionTransitionV1(IdentifiedWorkflowRecord):
    """Durable authorization to replace one exhausted strong work item."""

    _identity_domain = "workflow.contract-decomposition-transition.v1"

    schema_: Literal["workflow.contract-decomposition-transition.v1"] = Field(
        "workflow.contract-decomposition-transition.v1", alias="schema"
    )
    manifest_digest: str = Field(pattern=_DIGEST)
    source_work_id: str = Field(pattern=_ID)
    source_attempt_index: int = Field(ge=0, le=64)
    source_terminal_ref: str = Field(pattern=_ID)
    source_semantic_admission_ref: str = Field(pattern=_ID)
    route_lease: RouteLeaseRefV1
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
    child_keys: tuple[str, ...]
    child_context_refs: tuple[str, ...]

    @model_validator(mode="after")
    def _child_inventory_is_exact(self):
        if (
            not self.child_keys
            or len(self.child_keys) != len(self.child_context_refs)
            or len(self.child_keys) > self.maximum_children
            or len(set(self.child_keys)) != len(self.child_keys)
            or any(re.fullmatch(_DIGEST, ref) is None for ref in self.child_context_refs)
        ):
            raise ValueError("decomposition child inventory must be finite and exact")
        return self


class ContractDecompositionCompletionV1(IdentifiedWorkflowRecord):
    """Durable merge receipt preserving the exhausted source separately."""

    _identity_domain = "workflow.contract-decomposition-completion.v1"

    schema_: Literal["workflow.contract-decomposition-completion.v1"] = Field(
        "workflow.contract-decomposition-completion.v1", alias="schema"
    )
    manifest_digest: str = Field(pattern=_DIGEST)
    transition_ref: str = Field(pattern=_ID)
    source_work_id: str = Field(pattern=_ID)
    child_work_ids: tuple[str, ...]
    child_semantic_admission_refs: tuple[str, ...]
    admitted_effect_refs: tuple[str, ...] = ()
    source_failure_preserved: Literal[True] = True

    @model_validator(mode="after")
    def _child_results_are_exact(self):
        if (
            not self.child_work_ids
            or len(self.child_work_ids) != len(self.child_semantic_admission_refs)
            or len(set(self.child_work_ids)) != len(self.child_work_ids)
            or len(set(self.child_semantic_admission_refs))
            != len(self.child_semantic_admission_refs)
            or len(set(self.admitted_effect_refs)) != len(self.admitted_effect_refs)
        ):
            raise ValueError("decomposition completion requires exact child results")
        return self


class RouteSeatInsufficientCapabilityV1(IdentifiedWorkflowRecord):
    """Final route-seat outcome after its smallest authorized contract fails."""

    _identity_domain = "workflow.route-seat-insufficient-capability.v1"

    schema_: Literal["workflow.route-seat-insufficient-capability.v1"] = Field(
        "workflow.route-seat-insufficient-capability.v1", alias="schema"
    )
    manifest_digest: str = Field(pattern=_DIGEST)
    work_id: str = Field(pattern=_ID)
    attempt_index: int = Field(ge=0, le=64)
    route_lease: RouteLeaseRefV1
    contract_id: str = Field(min_length=1, max_length=512)
    provider_attempt_ref: str = Field(pattern=_ID)
    semantic_admission_ref: str = Field(pattern=_ID)
    outcome: Literal["insufficient_capability"] = "insufficient_capability"
    reason: Literal["smallest_authorized_contract_schema_exhausted"] = (
        "smallest_authorized_contract_schema_exhausted"
    )
    terminal_authority: Literal["workflow.work-terminal.v1"] = (
        "workflow.work-terminal.v1"
    )
    attempted_work_ids: tuple[str, ...]
    attempted_contract_ids: tuple[str, ...]
    decomposition_transition_refs: tuple[str, ...] = ()
    compact_recovery_transition_refs: tuple[str, ...] = ()
    classification_plan_ref: str = Field(pattern=_ID)
    classification_binding_ref: str = Field(pattern=_ID)
    qualification_evidence_sha256: str = Field(pattern=_DIGEST)
    behavioral_grant_sha256: str = Field(pattern=_DIGEST)
    maximum_schema_repairs: int = Field(ge=0, le=2)
    maximum_provider_calls: int = Field(ge=1, le=3)
    observed_provider_calls: int = Field(ge=1, le=3)
    retry_failed_work: Literal[False] = False

    @field_validator(
        "attempted_work_ids",
        "attempted_contract_ids",
        "decomposition_transition_refs",
        "compact_recovery_transition_refs",
    )
    @classmethod
    def _freeze_inventory(cls, value):
        return tuple(value)

    @model_validator(mode="after")
    def _outcome_is_exact(self):
        if (
            not self.attempted_work_ids
            or len(self.attempted_work_ids) != len(self.attempted_contract_ids)
            or self.attempted_work_ids[-1] != self.work_id
            or self.attempted_contract_ids[-1] != self.contract_id
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
        return (
            self.route_lease.role,
            self.route_lease.seat,
            self.route_lease.endpoint_id,
            self.route_lease.route_sha256,
        )


class WorkTerminalV1(IdentifiedWorkflowRecord):
    _identity_domain = "workflow.work-terminal.v1"

    schema_: Literal["workflow.work-terminal.v1"] = Field(
        "workflow.work-terminal.v1", alias="schema"
    )
    work_id: str = Field(pattern=_ID)
    attempt_index: int = Field(ge=0, le=64)
    status: Literal[
        "completed",
        "budget_denied",
        "abandoned",
        "schema_exhausted",
        "transport_failed",
        "rejected",
        "cancelled",
    ]
    usage_status: Literal["exact", "unknown"]
    prompt_tokens: int | None = Field(default=None, ge=0)
    completion_tokens: int | None = Field(default=None, ge=0)
    provider_attempt_ref: str | None = Field(default=None, pattern=_ID)
    semantic_admission_ref: str | None = Field(default=None, pattern=_ID)
    compact_recovery_transition_ref: str | None = Field(
        default=None,
        pattern=_ID,
        exclude_if=lambda value: value is None,
    )
    insufficient_capability_ref: str | None = Field(
        default=None,
        pattern=_ID,
        exclude_if=lambda value: value is None,
    )
    reason_code: str = Field(min_length=1, max_length=128)

    @model_validator(mode="after")
    def _terminal_shape(self):
        counts_known = self.prompt_tokens is not None and self.completion_tokens is not None
        if self.usage_status == "exact" and not counts_known:
            raise ValueError("exact terminal usage requires both token counts")
        if self.usage_status == "unknown" and (
            self.prompt_tokens is not None or self.completion_tokens is not None
        ):
            raise ValueError("unknown terminal usage cannot assert token counts")
        if self.status == "completed" and self.semantic_admission_ref is None:
            raise ValueError("completed work requires semantic admission")
        if self.status == "budget_denied" and (
            self.provider_attempt_ref is not None
            or self.semantic_admission_ref is not None
            or self.usage_status != "exact"
            or self.prompt_tokens != 0
            or self.completion_tokens != 0
        ):
            raise ValueError("budget denial cannot claim provider work or token use")
        if self.insufficient_capability_ref is not None and (
            self.status != "schema_exhausted"
            or self.provider_attempt_ref is None
            or self.semantic_admission_ref is None
        ):
            raise ValueError(
                "insufficient capability requires schema-exhausted provider authority"
            )
        return self


@dataclass(frozen=True)
class AuthorizedDispatch:
    """Runtime-only pairing of durable authority and its live meter lease."""

    preparation: WorkPreparationV1
    reservation_record: TokenReservationV2
    exposure_receipt: ContextExposureReceiptV2
    bundle: DispatchAuthorizationBundleV1
    reservation: Reservation

    def release(self) -> None:
        self.reservation.release()


class WorkBudgetDenied(RuntimeError):
    """Raised after a durable ``budget_denied`` terminal was appended."""

    def __init__(self, terminal: WorkTerminalV1) -> None:
        self.terminal = terminal
        super().__init__(f"token budget denied transactional work {terminal.work_id}")


__all__ = [
    "AuthorizedDispatch",
    "CompactRecoveryTransitionV1",
    "ContractDecompositionTransitionV1",
    "ContractDecompositionCompletionV1",
    "RouteSeatInsufficientCapabilityV1",
    "ContextExposureReceiptV2",
    "ContextNamespace",
    "ContextPackPlanV1",
    "DispatchAuthorizationBundleV1",
    "ProviderAttemptV1",
    "ModelClassificationBindingV1",
    "RouteSeatModelClassificationPlanV1",
    "RouteSeatModelClassificationV1",
    "SemanticAdmissionV1",
    "TokenReservationV2",
    "VisibleContextItemV1",
    "WorkBudgetDenied",
    "WorkLifecycleTransitionV1",
    "WorkPreparationV1",
    "WorkTerminalV1",
    "WorkTransitionKind",
]
