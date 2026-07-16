"""Pure deterministic reducer for the C0 conjecture workflow slice."""

from __future__ import annotations

from collections.abc import Sequence
from typing import Any, TypeVar

from pydantic import BaseModel

from deepreason.workflow.events import (
    ConjectureWorkAssignmentV1,
    WorkflowSignalKind,
    WorkflowSignalV1,
)
from deepreason.workflow.models import (
    BudgetDeltaV1,
    CapabilityOutcome,
    GuardFindingOutcome,
    ProposalReceiptV1,
    RouteLeaseRefV1,
    TransitionDecisionV1,
    TransitionKind,
    TriggerKind,
    WorkOrderEnvelopeV1,
)
from deepreason.workflow.profiles import ConjectureWorkflowProfileV1
from deepreason.workflow.state import (
    ReductionV1,
    WorkItemStatus,
    WorkflowProcessStateV1,
    state_after_transition,
)


_ModelT = TypeVar("_ModelT", bound=BaseModel)


def _canonical_revalidate(model_type: type[_ModelT], value: Any) -> _ModelT:
    """Reparse a model tree so copied nested instances cannot bypass guards."""

    payload = (
        value.model_dump(mode="python", by_alias=True)
        if isinstance(value, BaseModel)
        else value
    )
    return model_type.model_validate(payload)


def plan_conjecture_work(
    profile: ConjectureWorkflowProfileV1,
    *,
    problem_ref: str,
    school_id: str | None,
    route_lease: RouteLeaseRefV1,
    contract_id: str | None = None,
    formal_fence_seq: int,
    scratch_fence_seq: int,
    task_payload_schema_id: str,
    task_payload_ref: str | None = None,
    task_payload_value: Any | None = None,
    target_refs: tuple[str, ...] = (),
    input_refs: tuple[str, ...] = (),
    advisory_context_ref: str | None = None,
    budget_reservation_ref: str | None = None,
    completed_context_expansions: int = 0,
) -> WorkOrderEnvelopeV1:
    """Create one authority-only work order from resolved inputs."""

    profile = _canonical_revalidate(ConjectureWorkflowProfileV1, profile)
    return WorkOrderEnvelopeV1.create(
        manifest_digest=profile.manifest_digest,
        workflow_profile=profile.workflow_profile,
        formal_fence_seq=formal_fence_seq,
        scratch_fence_seq=scratch_fence_seq,
        problem_ref=problem_ref,
        target_refs=target_refs,
        school_id=school_id,
        route_lease=route_lease,
        contract_id=contract_id or profile.conjecturer_contract_id,
        input_refs=input_refs,
        advisory_context_ref=advisory_context_ref,
        capability_grant=profile.capability_grant(
            completed_context_expansions=completed_context_expansions
        ),
        budget_reservation_ref=budget_reservation_ref,
        repair_policy_ref=profile.repair_policy.id,
        task_payload_schema_id=task_payload_schema_id,
        task_payload_ref=task_payload_ref,
        task_payload_value=task_payload_value,
    )


def _validate_boundary(
    state: WorkflowProcessStateV1,
    work_order: WorkOrderEnvelopeV1,
) -> None:
    if (
        state.manifest_digest != work_order.manifest_digest
        or state.workflow_profile != work_order.workflow_profile
    ):
        raise ValueError("work order belongs to another workflow process")
    if (
        state.formal_fence_seq != work_order.formal_fence_seq
        or state.scratch_fence_seq != work_order.scratch_fence_seq
    ):
        raise ValueError("work order state fence differs from the process state")
    if (
        state.selected_problem_ref is not None
        and state.selected_problem_ref != work_order.problem_ref
    ):
        raise ValueError("work order belongs to another selected problem")


def _decide(
    state: WorkflowProcessStateV1,
    work_order: WorkOrderEnvelopeV1,
    *,
    trigger_kind: TriggerKind,
    trigger_ref: str,
    transition_kind: TransitionKind,
    budget_delta: BudgetDeltaV1 | None = None,
    provider_call_delta: int = 0,
    local_repair_delta: int = 0,
    context_expansion_delta: int = 0,
    guard_result_ref: str | None = None,
    output_refs: tuple[str, ...] = (),
) -> tuple[WorkflowProcessStateV1, TransitionDecisionV1]:
    _validate_boundary(state, work_order)
    if (
        transition_kind == TransitionKind.WORK_ENABLED
        and trigger_ref != work_order.problem_ref
    ):
        raise ValueError("work-enabled trigger differs from its selected problem")
    budget_delta = budget_delta or BudgetDeltaV1()
    next_state = state_after_transition(
        state,
        transition_kind=transition_kind,
        work_order_id=work_order.id,
        trigger_ref=trigger_ref,
        guard_result_ref=guard_result_ref,
        output_refs=output_refs,
        reserved_tokens=budget_delta.reserved_tokens,
        spent_tokens=budget_delta.spent_tokens,
        released_tokens=budget_delta.released_tokens,
        provider_call_delta=provider_call_delta,
        local_repair_delta=local_repair_delta,
        context_expansion_delta=context_expansion_delta,
    )
    decision = TransitionDecisionV1.create(
        manifest_digest=state.manifest_digest,
        workflow_profile=state.workflow_profile,
        previous_process_digest=state.digest,
        trigger_kind=trigger_kind,
        trigger_ref=trigger_ref,
        transition_kind=transition_kind,
        work_order_id=work_order.id,
        route_lease=work_order.route_lease,
        budget_delta=budget_delta,
        provider_call_delta=provider_call_delta,
        local_repair_delta=local_repair_delta,
        context_expansion_delta=context_expansion_delta,
        guard_result_ref=guard_result_ref,
        output_refs=output_refs,
        next_process_digest=next_state.digest,
    )
    return next_state, decision


def plan_conjecture_batch(
    profile: ConjectureWorkflowProfileV1,
    *,
    state: WorkflowProcessStateV1,
    problem_ref: str,
    assignments: Sequence[ConjectureWorkAssignmentV1],
    canonical_problem_refs: Sequence[str],
) -> ReductionV1:
    """Enable and issue a deterministic batch of resolved conjecture work."""

    profile = _canonical_revalidate(ConjectureWorkflowProfileV1, profile)
    state = _canonical_revalidate(WorkflowProcessStateV1, state)
    if (
        state.manifest_digest != profile.manifest_digest
        or state.workflow_profile != profile.workflow_profile
    ):
        raise ValueError("workflow profile belongs to another process state")
    if state.selected_problem_ref not in {None, problem_ref}:
        raise ValueError("workflow process already selected another problem")
    canonical_problem_refs = tuple(canonical_problem_refs)
    if len(canonical_problem_refs) != len(set(canonical_problem_refs)):
        raise ValueError("canonical problem references must be unique")
    if problem_ref not in canonical_problem_refs:
        raise ValueError("selected problem is not among the canonical references")
    normalized = tuple(
        _canonical_revalidate(ConjectureWorkAssignmentV1, item)
        for item in assignments
    )
    school_ids = tuple(item.school_id for item in normalized)
    if len(school_ids) != len(set(school_ids)):
        raise ValueError("conjecture batch contains duplicate school assignments")
    planned = sorted(
        (
            (
                plan_conjecture_work(
                    profile,
                    problem_ref=problem_ref,
                    school_id=item.school_id,
                    route_lease=item.route_lease,
                    contract_id=item.contract_id,
                    formal_fence_seq=state.formal_fence_seq,
                    scratch_fence_seq=state.scratch_fence_seq,
                    task_payload_schema_id=item.task_payload_schema_id,
                    task_payload_ref=item.task_payload_ref,
                    task_payload_value=item.task_payload_value,
                    target_refs=item.target_refs,
                    input_refs=item.input_refs,
                    advisory_context_ref=item.advisory_context_ref,
                    budget_reservation_ref=item.budget_reservation_ref,
                    completed_context_expansions=item.completed_context_expansions,
                ),
                item,
            )
            for item in normalized
        ),
        key=lambda pair: pair[0].id,
    )
    work_orders = tuple(work_order for work_order, _ in planned)
    if len({item.id for item in work_orders}) != len(work_orders):
        raise ValueError("conjecture batch contains duplicate work assignments")

    decisions: list[TransitionDecisionV1] = []
    for work_order, assignment in planned:
        state, enabled = _decide(
            state,
            work_order,
            trigger_kind=TriggerKind.PROBLEM_SELECTED,
            trigger_ref=problem_ref,
            transition_kind=TransitionKind.WORK_ENABLED,
        )
        state, issued = _decide(
            state,
            work_order,
            trigger_kind=TriggerKind.CONTEXT_PREPARED,
            trigger_ref=work_order.advisory_context_ref or work_order.id,
            transition_kind=TransitionKind.WORK_ISSUED,
            budget_delta=BudgetDeltaV1(
                reserved_tokens=assignment.reserved_tokens
            ),
        )
        decisions.extend((enabled, issued))
    return ReductionV1(
        state=state,
        decisions=tuple(decisions),
        work_orders=work_orders,
    )


def _guard_transition(signal: WorkflowSignalV1) -> tuple[TransitionKind, tuple[str, ...]]:
    guard = signal.guard_result
    if guard is None:  # guarded by WorkflowSignalV1; keeps type narrowing explicit
        raise ValueError("guard signal has no guard result")
    outcomes = {finding.outcome for finding in guard.findings}
    if GuardFindingOutcome.ADMIT in outcomes:
        return TransitionKind.PROPOSAL_ADMITTED, guard.admitted_refs
    if GuardFindingOutcome.REJECT in outcomes:
        return TransitionKind.PROPOSAL_REJECTED, guard.rejected_refs
    return TransitionKind.PROPOSAL_DEDUPLICATED, guard.deduplicated_refs


def reduce_conjecture(
    state: WorkflowProcessStateV1,
    signal: WorkflowSignalV1,
) -> ReductionV1:
    """Reduce one typed observation without I/O, clocks, stores, or mutation."""

    state = _canonical_revalidate(WorkflowProcessStateV1, state)
    signal = _canonical_revalidate(WorkflowSignalV1, signal)
    work_order = signal.work_order
    _validate_boundary(state, work_order)

    transition_map = {
        WorkflowSignalKind.WORK_ISSUED: (
            TriggerKind.CONTEXT_PREPARED,
            TransitionKind.WORK_ISSUED,
        ),
        WorkflowSignalKind.PROPOSAL_RECEIVED: (
            TriggerKind.PROVIDER_RESULT,
            TransitionKind.PROPOSAL_RECEIVED,
        ),
        WorkflowSignalKind.REPAIR_REQUESTED: (
            TriggerKind.REPAIR_DECISION,
            TransitionKind.REPAIR_REQUESTED,
        ),
        WorkflowSignalKind.REPAIR_EXHAUSTED: (
            TriggerKind.PROVIDER_RESULT,
            TransitionKind.REPAIR_EXHAUSTED,
        ),
        WorkflowSignalKind.CONTEXT_REQUESTED: (
            TriggerKind.PROVIDER_RESULT,
            TransitionKind.CONTEXT_REQUESTED,
        ),
        WorkflowSignalKind.CONTEXT_GRANTED: (
            TriggerKind.CONTEXT_DECISION,
            TransitionKind.CONTEXT_GRANTED,
        ),
        WorkflowSignalKind.CONTEXT_DENIED: (
            TriggerKind.CONTEXT_DECISION,
            TransitionKind.CONTEXT_DENIED,
        ),
        WorkflowSignalKind.WORK_FINISHED: (
            TriggerKind.PROVIDER_RESULT,
            TransitionKind.WORK_FINISHED,
        ),
        WorkflowSignalKind.WORK_ABANDONED: (
            TriggerKind.WORKFLOW_TERMINATION,
            TransitionKind.WORK_ABANDONED,
        ),
    }
    guard_result_ref = None
    output_refs: tuple[str, ...] = ()
    if signal.kind == WorkflowSignalKind.GUARD_EVALUATED:
        trigger_kind = TriggerKind.GUARD_RESULT
        transition_kind, output_refs = _guard_transition(signal)
        guard = signal.guard_result
        assert guard is not None
        current = state.work_item(work_order.id)
        if current is None or current.proposal_receipt_id != guard.proposal_receipt_id:
            raise ValueError("guard result belongs to another proposal receipt")
        guarded_candidates = {finding.candidate_ref for finding in guard.findings}
        if guarded_candidates != set(current.proposal_candidate_refs):
            raise ValueError("guard findings do not cover the proposal candidates")
        guard_result_ref = guard.id
    else:
        trigger_kind, transition_kind = transition_map[signal.kind]

    proposal_receipts: tuple[ProposalReceiptV1, ...] = ()
    budget_delta = BudgetDeltaV1()
    provider_call_delta = 0
    local_repair_delta = 0
    context_expansion_delta = 0
    current = state.work_item(work_order.id)
    if current is None:
        raise ValueError("signal belongs to work that was not enabled")
    if signal.proposal_receipt is not None:
        receipt = signal.proposal_receipt
        if (
            receipt.contract_id != work_order.contract_id
            or receipt.route_lease != work_order.route_lease
        ):
            raise ValueError("proposal receipt changed contract or route authority")
        if len(receipt.candidate_payload_refs) > work_order.capability_grant.max_candidates:
            raise ValueError("proposal exceeds its candidate capability")
        allowed = work_order.capability_grant.allowed_outcomes
        if (
            receipt.candidate_payload_refs
            and CapabilityOutcome.CANDIDATE_PROPOSAL not in allowed
        ):
            raise ValueError("proposal exceeds its candidate capability")
        if (
            receipt.context_request_ref is not None
            and CapabilityOutcome.CONTEXT_REQUEST not in allowed
        ):
            raise ValueError("proposal exceeds its context-request capability")
        if (
            receipt.abstention_ref is not None
            and CapabilityOutcome.ABSTENTION not in allowed
        ):
            raise ValueError("proposal exceeds its abstention capability")
        proposal_receipts = (receipt,)
        output_refs = receipt.candidate_payload_refs
        requested_repairs = receipt.attempt_count - 1
        if requested_repairs > work_order.capability_grant.max_local_repairs:
            raise ValueError("proposal exceeds its local-repair capability")
        repaired = receipt.attempt_count > 1
        if repaired != (current.status == WorkItemStatus.REPAIR_PENDING):
            raise ValueError(
                "proposal attempt count differs from durable repair authority"
            )
        # Receipt tokens are measured by the harness.  Cover any unreserved
        # amount locally and release only this work item's unused reservation.
        provider_call_delta = 1
        local_repair_delta = requested_repairs
        grant = work_order.capability_grant
        if current.provider_calls_used + provider_call_delta > grant.max_provider_calls:
            raise ValueError("proposal exceeds its provider-call capability")
        if current.local_repairs_used + local_repair_delta > grant.max_local_repairs:
            raise ValueError("proposal exceeds its local-repair capability")
        budget_delta = BudgetDeltaV1(
            reserved_tokens=max(0, receipt.tokens - current.reserved_tokens),
            spent_tokens=receipt.tokens,
            released_tokens=max(0, current.reserved_tokens - receipt.tokens),
        )
    if signal.kind == WorkflowSignalKind.REPAIR_REQUESTED and (
        current.local_repairs_used >= work_order.capability_grant.max_local_repairs
    ):
        raise ValueError("work order has exhausted local-repair authority")
    if signal.kind == WorkflowSignalKind.CONTEXT_REQUESTED:
        permits_context = (
            CapabilityOutcome.CONTEXT_REQUEST
            in work_order.capability_grant.allowed_outcomes
        )
        if not permits_context:
            raise ValueError("work order does not grant context-request authority")
    if signal.kind == WorkflowSignalKind.CONTEXT_GRANTED:
        if (
            CapabilityOutcome.CONTEXT_REQUEST
            not in work_order.capability_grant.allowed_outcomes
        ):
            raise ValueError("work order does not grant context-expansion authority")
        context_expansion_delta = 1
        if (
            current.context_expansions_used + context_expansion_delta
            > work_order.capability_grant.remaining_context_expansions
        ):
            raise ValueError("work order has exhausted context-expansion authority")
    if signal.kind in {
        WorkflowSignalKind.WORK_FINISHED,
        WorkflowSignalKind.WORK_ABANDONED,
    }:
        budget_delta = BudgetDeltaV1(released_tokens=current.reserved_tokens)

    next_state, decision = _decide(
        state,
        work_order,
        trigger_kind=trigger_kind,
        trigger_ref=signal.trigger_ref,
        transition_kind=transition_kind,
        budget_delta=budget_delta,
        provider_call_delta=provider_call_delta,
        local_repair_delta=local_repair_delta,
        context_expansion_delta=context_expansion_delta,
        guard_result_ref=guard_result_ref,
        output_refs=output_refs,
    )
    return ReductionV1(
        state=next_state,
        decisions=(decision,),
        proposal_receipts=proposal_receipts,
        guard_results=(signal.guard_result,) if signal.guard_result is not None else (),
    )


__all__ = [
    "ConjectureWorkAssignmentV1",
    "ReductionV1",
    "WorkflowSignalKind",
    "WorkflowSignalV1",
    "plan_conjecture_batch",
    "plan_conjecture_work",
    "reduce_conjecture",
]
