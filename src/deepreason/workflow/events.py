"""Strict, in-memory inputs for the C0 conjecture reducer.

Signals in this module are deliberately not ontology events.  They are typed
observations supplied to the pure reducer and have no durable or scheduling
authority of their own.
"""

from __future__ import annotations

from enum import Enum
from typing import Any

from pydantic import Field, field_validator, model_validator

from deepreason.workflow.models import (
    GuardResultV1,
    ProposalReceiptV1,
    ProposalValidationOutcome,
    RouteLeaseRefV1,
    WorkOrderEnvelopeV1,
    WorkflowRecord,
    freeze_workflow_json,
)


class WorkflowSignalKind(str, Enum):
    """Closed set of observations understood by the C0 Conj reducer."""

    WORK_ISSUED = "work_issued"
    PROPOSAL_RECEIVED = "proposal_received"
    GUARD_EVALUATED = "guard_evaluated"
    REPAIR_REQUESTED = "repair_requested"
    REPAIR_EXHAUSTED = "repair_exhausted"
    CONTEXT_REQUESTED = "context_requested"
    CONTEXT_GRANTED = "context_granted"
    CONTEXT_DENIED = "context_denied"
    WORK_FINISHED = "work_finished"


class ConjectureWorkAssignmentV1(WorkflowRecord):
    """One already-resolved school/route input to batch planning."""

    school_id: str | None = Field(
        default=None, pattern=r"^school-(0|[1-9][0-9]*)$"
    )
    route_lease: RouteLeaseRefV1
    contract_id: str | None = Field(default=None, min_length=1, max_length=512)
    target_refs: tuple[str, ...] = ()
    input_refs: tuple[str, ...] = ()
    advisory_context_ref: str | None = None
    budget_reservation_ref: str | None = None
    reserved_tokens: int = Field(default=0, ge=0)
    completed_context_expansions: int = Field(default=0, ge=0, le=8)
    task_payload_schema_id: str = Field(min_length=1, max_length=512)
    task_payload_ref: str | None = None
    task_payload_value: Any | None = None

    @field_validator("target_refs", "input_refs")
    @classmethod
    def _unique_refs(cls, value):
        if len(value) != len(set(value)):
            raise ValueError("assignment references must not contain duplicates")
        return tuple(value)

    @field_validator("task_payload_value", mode="before")
    @classmethod
    def _canonical_payload_value(cls, value):
        return None if value is None else freeze_workflow_json(value)

    @model_validator(mode="after")
    def _one_payload_source(self):
        if (self.task_payload_ref is None) == (self.task_payload_value is None):
            raise ValueError(
                "assignment requires exactly one task payload ref or value"
            )
        return self


class WorkflowSignalV1(WorkflowRecord):
    """One typed observation consumed by :func:`reduce_conjecture`.

    Every signal carries the work order so that route and capability authority
    never has to be recovered from mutable scheduler state.
    """

    kind: WorkflowSignalKind
    work_order: WorkOrderEnvelopeV1
    trigger_ref: str = Field(min_length=1, max_length=512)
    proposal_receipt: ProposalReceiptV1 | None = None
    guard_result: GuardResultV1 | None = None

    @model_validator(mode="before")
    @classmethod
    def _derive_record_trigger(cls, value):
        if isinstance(value, dict) and not value.get("trigger_ref"):
            proposal = value.get("proposal_receipt")
            guard = value.get("guard_result")
            work_order = value.get("work_order")
            if proposal is not None:
                value = {**value, "trigger_ref": getattr(proposal, "id", None) or proposal.get("id")}
            elif guard is not None:
                value = {**value, "trigger_ref": getattr(guard, "id", None) or guard.get("id")}
            elif work_order is not None:
                work_id = getattr(work_order, "id", None)
                if work_id is None and isinstance(work_order, dict):
                    work_id = work_order.get("id")
                value = {**value, "trigger_ref": work_id}
        return value

    @model_validator(mode="after")
    def _payload_matches_kind(self):
        wants_proposal = self.kind in {
            WorkflowSignalKind.PROPOSAL_RECEIVED,
            WorkflowSignalKind.REPAIR_EXHAUSTED,
        }
        wants_guard = self.kind == WorkflowSignalKind.GUARD_EVALUATED
        if wants_proposal != (self.proposal_receipt is not None):
            raise ValueError(
                "proposal_received and repair_exhausted signals require a receipt"
            )
        if wants_guard != (self.guard_result is not None):
            raise ValueError("only guard_result signals carry a guard result")
        if self.proposal_receipt is not None:
            if self.proposal_receipt.work_order_id != self.work_order.id:
                raise ValueError("proposal receipt belongs to another work order")
            if self.trigger_ref != self.proposal_receipt.id:
                raise ValueError("proposal signal trigger must be the receipt ID")
            valid_outcomes = {
                ProposalValidationOutcome.VALID_FIRST_ATTEMPT,
                ProposalValidationOutcome.VALID_AFTER_REPAIR,
            }
            is_valid = self.proposal_receipt.validation_outcome in valid_outcomes
            if self.kind == WorkflowSignalKind.PROPOSAL_RECEIVED and not is_valid:
                raise ValueError("proposal_received requires a valid receipt")
            if self.kind == WorkflowSignalKind.REPAIR_EXHAUSTED and is_valid:
                raise ValueError("repair_exhausted requires a failed receipt")
        if self.guard_result is not None:
            if self.guard_result.work_order_id != self.work_order.id:
                raise ValueError("guard result belongs to another work order")
            if self.trigger_ref != self.guard_result.id:
                raise ValueError("guard signal trigger must be the guard-result ID")
        return self

    @classmethod
    def proposal(
        cls,
        work_order: WorkOrderEnvelopeV1,
        proposal_receipt: ProposalReceiptV1,
    ) -> "WorkflowSignalV1":
        return cls(
            kind=WorkflowSignalKind.PROPOSAL_RECEIVED,
            work_order=work_order,
            trigger_ref=proposal_receipt.id,
            proposal_receipt=proposal_receipt,
        )

    @classmethod
    def guarded(
        cls,
        work_order: WorkOrderEnvelopeV1,
        guard_result: GuardResultV1,
    ) -> "WorkflowSignalV1":
        return cls(
            kind=WorkflowSignalKind.GUARD_EVALUATED,
            work_order=work_order,
            trigger_ref=guard_result.id,
            guard_result=guard_result,
        )

    @classmethod
    def repair_exhausted(
        cls,
        work_order: WorkOrderEnvelopeV1,
        proposal_receipt: ProposalReceiptV1,
    ) -> "WorkflowSignalV1":
        return cls(
            kind=WorkflowSignalKind.REPAIR_EXHAUSTED,
            work_order=work_order,
            trigger_ref=proposal_receipt.id,
            proposal_receipt=proposal_receipt,
        )


__all__ = [
    "ConjectureWorkAssignmentV1",
    "WorkflowSignalKind",
    "WorkflowSignalV1",
]
