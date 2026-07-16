"""Pure replay state for the conjecture workflow slice."""

from __future__ import annotations

from enum import Enum
from typing import Any, Literal, TypeVar

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from deepreason.canonical import canonical_json, sha256_hex
from deepreason.workflow.models import (
    GuardResultV1,
    ProposalReceiptV1,
    TransitionDecisionV1,
    TransitionKind,
    WorkOrderEnvelopeV1,
    WorkflowRecord,
)


_ModelT = TypeVar("_ModelT", bound=BaseModel)


def _canonical_revalidate(model_type: type[_ModelT], value: Any) -> _ModelT:
    """Reparse a model tree so pre-built nested instances cannot skip validation."""

    payload = (
        value.model_dump(mode="python", by_alias=True)
        if isinstance(value, BaseModel)
        else value
    )
    return model_type.model_validate(payload)


class WorkItemStatus(str, Enum):
    ENABLED = "enabled"
    ISSUED = "issued"
    PROPOSAL_RECEIVED = "proposal_received"
    REPAIR_PENDING = "repair_pending"
    CONTEXT_PENDING = "context_pending"
    FINISHED = "finished"
    ABANDONED = "abandoned"


class WorkOutcome(str, Enum):
    ADMITTED = "admitted"
    REJECTED = "rejected"
    DEDUPLICATED = "deduplicated"
    NO_PROPOSAL = "no_proposal"
    ABANDONED = "abandoned"


class ConjectureWorkStateV1(WorkflowRecord):
    model_config = ConfigDict(extra="forbid", frozen=True)

    work_order_id: str = Field(pattern=r"^sha256:[0-9a-f]{64}$")
    status: WorkItemStatus
    proposal_receipt_id: str | None = Field(
        default=None, pattern=r"^sha256:[0-9a-f]{64}$"
    )
    proposal_candidate_refs: tuple[str, ...] = ()
    guard_result_id: str | None = Field(
        default=None, pattern=r"^sha256:[0-9a-f]{64}$"
    )
    reserved_tokens: int = Field(default=0, ge=0)
    provider_calls_used: int = Field(default=0, ge=0)
    local_repairs_used: int = Field(default=0, ge=0)
    context_expansions_used: int = Field(default=0, ge=0)
    outcome: WorkOutcome | None = None

    @field_validator("proposal_candidate_refs")
    @classmethod
    def _unique_candidate_refs(cls, value):
        if len(value) != len(set(value)):
            raise ValueError("proposal candidate references must be unique")
        return tuple(value)

    @model_validator(mode="after")
    def _status_shape(self):
        if self.status == WorkItemStatus.ENABLED and (
            self.proposal_receipt_id is not None
            or self.guard_result_id is not None
            or self.outcome is not None
        ):
            raise ValueError("enabled work cannot already contain a result")
        if self.guard_result_id is not None and self.proposal_receipt_id is None:
            raise ValueError("guard result requires a proposal receipt")
        if self.proposal_candidate_refs and self.proposal_receipt_id is None:
            raise ValueError("proposal candidates require a proposal receipt")
        terminal = self.status in {WorkItemStatus.FINISHED, WorkItemStatus.ABANDONED}
        if terminal != (self.outcome is not None):
            raise ValueError("only terminal work carries an outcome")
        if terminal and self.reserved_tokens:
            raise ValueError("terminal work cannot retain a token reservation")
        if self.status == WorkItemStatus.FINISHED and self.proposal_receipt_id is None:
            raise ValueError("finished work requires a proposal receipt")
        guarded_outcomes = {
            WorkOutcome.ADMITTED,
            WorkOutcome.REJECTED,
            WorkOutcome.DEDUPLICATED,
        }
        if (self.outcome in guarded_outcomes) != (self.guard_result_id is not None):
            raise ValueError("guarded work outcome requires exactly one guard result")
        if self.status == WorkItemStatus.ABANDONED and self.outcome != WorkOutcome.ABANDONED:
            raise ValueError("abandoned work requires the abandoned outcome")
        return self


class WorkflowProcessStateV1(WorkflowRecord):
    model_config = ConfigDict(extra="forbid", frozen=True)

    schema_: Literal["workflow.process-state.v1"] = Field(
        "workflow.process-state.v1", alias="schema"
    )
    manifest_digest: str = Field(pattern=r"^[0-9a-f]{64}$")
    workflow_profile: Literal["conjecture.shadow.v1", "conjecture.active.v1"]
    phase: Literal["conjecture"] = "conjecture"
    selected_problem_ref: str | None = Field(default=None, max_length=512)
    formal_fence_seq: int = Field(ge=0)
    scratch_fence_seq: int = Field(ge=0)
    work_items: tuple[ConjectureWorkStateV1, ...] = ()
    reserved_tokens: int = Field(default=0, ge=0)
    spent_tokens: int = Field(default=0, ge=0)

    @field_validator("work_items")
    @classmethod
    def _canonical_work_items(cls, value):
        ids = tuple(item.work_order_id for item in value)
        if ids != tuple(sorted(ids)) or len(ids) != len(set(ids)):
            raise ValueError("workflow work items must be unique and sorted by id")
        return tuple(value)

    @model_validator(mode="after")
    def _one_state_prefix(self):
        if self.formal_fence_seq != self.scratch_fence_seq:
            raise ValueError("workflow state requires one formal/scratch fence")
        if self.reserved_tokens != sum(
            item.reserved_tokens for item in self.work_items
        ):
            raise ValueError("workflow reservation total differs from its work items")
        return self

    @property
    def digest(self) -> str:
        payload = self.model_dump(mode="json", by_alias=True, exclude_none=True)
        return "sha256:" + sha256_hex(
            b"workflow.process-state.v1\x00" + canonical_json(payload)
        )

    @classmethod
    def initial(
        cls,
        *,
        manifest_digest: str,
        workflow_profile: Literal[
            "conjecture.shadow.v1", "conjecture.active.v1"
        ],
        formal_fence_seq: int,
        scratch_fence_seq: int,
    ) -> "WorkflowProcessStateV1":
        return cls(
            manifest_digest=manifest_digest,
            workflow_profile=workflow_profile,
            formal_fence_seq=formal_fence_seq,
            scratch_fence_seq=scratch_fence_seq,
        )

    def work_item(self, work_order_id: str) -> ConjectureWorkStateV1 | None:
        return next(
            (item for item in self.work_items if item.work_order_id == work_order_id),
            None,
        )

    def replace_work_item(
        self, item: ConjectureWorkStateV1
    ) -> "WorkflowProcessStateV1":
        state = _canonical_revalidate(WorkflowProcessStateV1, self)
        item = _canonical_revalidate(ConjectureWorkStateV1, item)
        previous = state.work_item(item.work_order_id)
        items = {
            current.work_order_id: current
            for current in state.work_items
            if current.work_order_id != item.work_order_id
        }
        items[item.work_order_id] = item
        return _canonical_revalidate(
            WorkflowProcessStateV1,
            state.model_copy(
                update={
                "work_items": tuple(items[key] for key in sorted(items)),
                "reserved_tokens": (
                    state.reserved_tokens
                    - (previous.reserved_tokens if previous is not None else 0)
                    + item.reserved_tokens
                ),
                }
            ),
        )


class ReductionV1(WorkflowRecord):
    """Pure reducer output; none of these records is durable in C0."""

    state: WorkflowProcessStateV1
    decisions: tuple[TransitionDecisionV1, ...] = ()
    work_orders: tuple[WorkOrderEnvelopeV1, ...] = ()
    proposal_receipts: tuple[ProposalReceiptV1, ...] = ()
    guard_results: tuple[GuardResultV1, ...] = ()

    @model_validator(mode="after")
    def _unique_records(self):
        for label, records in (
            ("decisions", self.decisions),
            ("work orders", self.work_orders),
            ("proposal receipts", self.proposal_receipts),
            ("guard results", self.guard_results),
        ):
            ids = [record.id for record in records]
            if len(ids) != len(set(ids)):
                raise ValueError(f"reduction {label} must have unique IDs")
        return self


_LEGAL_STATUS: dict[TransitionKind, tuple[set[WorkItemStatus | None], WorkItemStatus]] = {
    TransitionKind.WORK_ENABLED: ({None}, WorkItemStatus.ENABLED),
    TransitionKind.WORK_ISSUED: ({WorkItemStatus.ENABLED}, WorkItemStatus.ISSUED),
    TransitionKind.PROPOSAL_RECEIVED: (
        {WorkItemStatus.ISSUED, WorkItemStatus.REPAIR_PENDING},
        WorkItemStatus.PROPOSAL_RECEIVED,
    ),
    TransitionKind.REPAIR_REQUESTED: (
        {
            WorkItemStatus.ISSUED,
            WorkItemStatus.PROPOSAL_RECEIVED,
            WorkItemStatus.REPAIR_PENDING,
        },
        WorkItemStatus.REPAIR_PENDING,
    ),
    TransitionKind.REPAIR_EXHAUSTED: (
        {WorkItemStatus.ISSUED, WorkItemStatus.REPAIR_PENDING},
        WorkItemStatus.FINISHED,
    ),
    TransitionKind.CONTEXT_REQUESTED: (
        {WorkItemStatus.PROPOSAL_RECEIVED},
        WorkItemStatus.CONTEXT_PENDING,
    ),
    TransitionKind.CONTEXT_GRANTED: (
        {WorkItemStatus.CONTEXT_PENDING},
        WorkItemStatus.PROPOSAL_RECEIVED,
    ),
    TransitionKind.CONTEXT_DENIED: (
        {WorkItemStatus.CONTEXT_PENDING},
        WorkItemStatus.PROPOSAL_RECEIVED,
    ),
    TransitionKind.PROPOSAL_ADMITTED: (
        {WorkItemStatus.PROPOSAL_RECEIVED},
        WorkItemStatus.FINISHED,
    ),
    TransitionKind.PROPOSAL_REJECTED: (
        {WorkItemStatus.PROPOSAL_RECEIVED},
        WorkItemStatus.FINISHED,
    ),
    TransitionKind.PROPOSAL_DEDUPLICATED: (
        {WorkItemStatus.PROPOSAL_RECEIVED},
        WorkItemStatus.FINISHED,
    ),
    TransitionKind.WORK_FINISHED: (
        {WorkItemStatus.PROPOSAL_RECEIVED, WorkItemStatus.CONTEXT_PENDING},
        WorkItemStatus.FINISHED,
    ),
    TransitionKind.WORK_ABANDONED: (
        {
            WorkItemStatus.ENABLED,
            WorkItemStatus.ISSUED,
            WorkItemStatus.PROPOSAL_RECEIVED,
            WorkItemStatus.REPAIR_PENDING,
            WorkItemStatus.CONTEXT_PENDING,
        },
        WorkItemStatus.ABANDONED,
    ),
}


def state_after_transition(
    state: WorkflowProcessStateV1,
    *,
    transition_kind: TransitionKind,
    work_order_id: str,
    trigger_ref: str,
    guard_result_ref: str | None = None,
    output_refs: tuple[str, ...] = (),
    reserved_tokens: int = 0,
    spent_tokens: int = 0,
    released_tokens: int = 0,
    provider_call_delta: int = 0,
    local_repair_delta: int = 0,
    context_expansion_delta: int = 0,
) -> WorkflowProcessStateV1:
    """Return the deterministic next state without mutating ``state``."""

    state = _canonical_revalidate(WorkflowProcessStateV1, state)
    for label, delta in (
        ("provider call", provider_call_delta),
        ("local repair", local_repair_delta),
        ("context expansion", context_expansion_delta),
    ):
        if delta < 0:
            raise ValueError(f"workflow {label} consumption cannot be negative")
    provider_result = transition_kind in {
        TransitionKind.PROPOSAL_RECEIVED,
        TransitionKind.REPAIR_EXHAUSTED,
    }
    if provider_call_delta != int(provider_result):
        raise ValueError(
            "provider-result transitions consume exactly one provider call"
        )
    if local_repair_delta and not provider_result:
        raise ValueError("only provider-result transitions consume local repairs")
    context_granted = transition_kind == TransitionKind.CONTEXT_GRANTED
    if context_expansion_delta != int(context_granted):
        raise ValueError("context-granted transitions consume exactly one expansion")
    current = state.work_item(work_order_id)
    current_status = current.status if current is not None else None
    allowed, next_status = _LEGAL_STATUS[transition_kind]
    if current_status not in allowed:
        raise ValueError(
            f"illegal workflow transition {transition_kind.value} from "
            f"{getattr(current_status, 'value', None)!r}"
        )
    selected_problem_ref = state.selected_problem_ref
    if transition_kind == TransitionKind.WORK_ENABLED:
        if selected_problem_ref not in {None, trigger_ref}:
            raise ValueError("work enables a different selected problem")
        selected_problem_ref = trigger_ref
    proposal_ref = current.proposal_receipt_id if current is not None else None
    proposal_candidate_refs = (
        current.proposal_candidate_refs if current is not None else ()
    )
    guard_ref = current.guard_result_id if current is not None else None
    outcome = current.outcome if current is not None else None
    current_reserved = current.reserved_tokens if current is not None else 0
    provider_calls_used = current.provider_calls_used if current is not None else 0
    local_repairs_used = current.local_repairs_used if current is not None else 0
    context_expansions_used = (
        current.context_expansions_used if current is not None else 0
    )
    next_work_reserved = (
        current_reserved + reserved_tokens - spent_tokens - released_tokens
    )
    if next_work_reserved < 0:
        raise ValueError("workflow transition spends another work item's reservation")
    if transition_kind in {
        TransitionKind.PROPOSAL_RECEIVED,
        TransitionKind.REPAIR_EXHAUSTED,
    }:
        proposal_ref = trigger_ref
        proposal_candidate_refs = tuple(output_refs)
    if transition_kind in {
        TransitionKind.PROPOSAL_ADMITTED,
        TransitionKind.PROPOSAL_REJECTED,
        TransitionKind.PROPOSAL_DEDUPLICATED,
    }:
        guard_ref = guard_result_ref
        if transition_kind == TransitionKind.PROPOSAL_ADMITTED:
            outcome = WorkOutcome.ADMITTED
        elif transition_kind == TransitionKind.PROPOSAL_DEDUPLICATED:
            outcome = WorkOutcome.DEDUPLICATED
        else:
            outcome = WorkOutcome.REJECTED
    elif transition_kind in {
        TransitionKind.REPAIR_EXHAUSTED,
        TransitionKind.WORK_FINISHED,
    }:
        outcome = WorkOutcome.NO_PROPOSAL
    elif transition_kind == TransitionKind.WORK_ABANDONED:
        outcome = WorkOutcome.ABANDONED

    updated = ConjectureWorkStateV1(
        work_order_id=work_order_id,
        status=next_status,
        proposal_receipt_id=proposal_ref,
        proposal_candidate_refs=proposal_candidate_refs,
        guard_result_id=guard_ref,
        reserved_tokens=next_work_reserved,
        provider_calls_used=provider_calls_used + provider_call_delta,
        local_repairs_used=local_repairs_used + local_repair_delta,
        context_expansions_used=(
            context_expansions_used + context_expansion_delta
        ),
        outcome=outcome,
    )
    items = {
        item.work_order_id: item
        for item in state.work_items
        if item.work_order_id != work_order_id
    }
    items[work_order_id] = updated
    next_reserved = (
        state.reserved_tokens + reserved_tokens - spent_tokens - released_tokens
    )
    if next_reserved < 0:
        raise ValueError("workflow transition releases more tokens than reserved")
    return _canonical_revalidate(
        WorkflowProcessStateV1,
        state.model_copy(
            update={
                "selected_problem_ref": selected_problem_ref,
                "work_items": tuple(items[key] for key in sorted(items)),
                "reserved_tokens": next_reserved,
                "spent_tokens": state.spent_tokens + spent_tokens,
            }
        ),
    )


def apply_decision(
    state: WorkflowProcessStateV1,
    decision: TransitionDecisionV1,
) -> WorkflowProcessStateV1:
    """Replay one code-authored decision and verify both state digests."""

    state = _canonical_revalidate(WorkflowProcessStateV1, state)
    decision = _canonical_revalidate(TransitionDecisionV1, decision)
    if state.digest != decision.previous_process_digest:
        raise ValueError("transition previous process digest does not match state")
    if (
        state.manifest_digest != decision.manifest_digest
        or state.workflow_profile != decision.workflow_profile
    ):
        raise ValueError("transition belongs to another workflow profile")
    next_state = state_after_transition(
        state,
        transition_kind=decision.transition_kind,
        work_order_id=decision.work_order_id,
        trigger_ref=decision.trigger_ref,
        guard_result_ref=decision.guard_result_ref,
        output_refs=decision.output_refs,
        reserved_tokens=decision.budget_delta.reserved_tokens,
        spent_tokens=decision.budget_delta.spent_tokens,
        released_tokens=decision.budget_delta.released_tokens,
        provider_call_delta=decision.provider_call_delta,
        local_repair_delta=decision.local_repair_delta,
        context_expansion_delta=decision.context_expansion_delta,
    )
    if next_state.digest != decision.next_process_digest:
        raise ValueError("transition next process digest does not match replay")
    return next_state


__all__ = [
    "ConjectureWorkStateV1",
    "ReductionV1",
    "WorkflowProcessStateV1",
    "WorkItemStatus",
    "WorkOutcome",
    "apply_decision",
    "state_after_transition",
]
