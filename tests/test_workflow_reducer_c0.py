"""C0 conjecture reduction is pure, deterministic, and code-authoritative."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from deepreason.run_manifest import ConjectureContextPolicyV1
from deepreason.workflow.events import (
    ConjectureWorkAssignmentV1,
    WorkflowSignalKind,
    WorkflowSignalV1,
)
from deepreason.workflow.models import (
    BudgetDeltaV1,
    CapabilityGrantV1,
    CapabilityOutcome,
    GuardFindingCode,
    GuardFindingOutcome,
    GuardFindingV1,
    GuardResultV1,
    LocalRepairPolicyV1,
    ProposalReceiptV1,
    ProposalValidationOutcome,
    RouteLeaseRefV1,
    TransitionDecisionV1,
    TransitionKind,
    TriggerKind,
    WorkOrderEnvelopeV1,
)
from deepreason.workflow.profiles import ConjectureWorkflowProfileV1
from deepreason.workflow.reducer import plan_conjecture_batch, reduce_conjecture
from deepreason.workflow.state import (
    ConjectureWorkStateV1,
    WorkOutcome,
    WorkItemStatus,
    WorkflowProcessStateV1,
    apply_decision,
    state_after_transition,
)


def _hash(char: str) -> str:
    return "sha256:" + char * 64


def _route() -> RouteLeaseRefV1:
    return RouteLeaseRefV1(
        seat=0,
        endpoint_id="conjecturer-primary",
        route_sha256="a" * 64,
    )


def _initial() -> WorkflowProcessStateV1:
    return WorkflowProcessStateV1.initial(
        manifest_digest="b" * 64,
        workflow_profile="conjecture.shadow.v1",
        formal_fence_seq=4,
        scratch_fence_seq=4,
    )


def _profile() -> ConjectureWorkflowProfileV1:
    return ConjectureWorkflowProfileV1(
        manifest_digest="b" * 64,
        mode="shadow",
        workflow_profile="conjecture.shadow.v1",
        conjecturer_contract_id="conjecturer.legacy.v1",
        model_profile="standard",
        workload_profile="text",
        max_candidates=3,
        context_policy=ConjectureContextPolicyV1(
            mode="disabled",
            initial_max_blocks=0,
            initial_max_guides=0,
            max_context_expansion_requests=0,
            max_extra_blocks=0,
            permitted_retrieval_channels=(),
            coverage_slot_mandatory=False,
            exploration_slot_mandatory=False,
        ),
        repair_policy=LocalRepairPolicyV1.create(max_schema_repairs=0, scopes=()),
    )


def _assignment(
    *,
    task_payload_ref: str | None = "payload:semantic-conjecture",
    task_payload_value=None,
) -> ConjectureWorkAssignmentV1:
    return ConjectureWorkAssignmentV1(
        school_id=None,
        route_lease=_route(),
        contract_id="conjecturer.legacy.v1",
        task_payload_schema_id="semantic.conjecture.open.v1",
        task_payload_ref=task_payload_ref,
        task_payload_value=task_payload_value,
        input_refs=("problem:deterministic-c0",),
    )


def _planned(*, assignment: ConjectureWorkAssignmentV1 | None = None):
    return plan_conjecture_batch(
        _profile(),
        state=_initial(),
        problem_ref="problem:deterministic-c0",
        assignments=(assignment or _assignment(),),
        canonical_problem_refs=("problem:deterministic-c0",),
    )


def _work_with_grant(
    grant: CapabilityGrantV1,
) -> tuple[WorkOrderEnvelopeV1, WorkflowProcessStateV1]:
    original = _planned().work_orders[0]
    payload = original.model_dump(
        mode="python",
        by_alias=True,
        exclude={"id", "capability_grant"},
    )
    work_order = WorkOrderEnvelopeV1.create(**payload, capability_grant=grant)
    state = state_after_transition(
        _initial(),
        transition_kind=TransitionKind.WORK_ENABLED,
        work_order_id=work_order.id,
        trigger_ref=work_order.problem_ref,
    )
    state = state_after_transition(
        state,
        transition_kind=TransitionKind.WORK_ISSUED,
        work_order_id=work_order.id,
        trigger_ref=work_order.id,
    )
    return work_order, state


def _proposal(work_order, *, candidate_ref: str) -> ProposalReceiptV1:
    return ProposalReceiptV1.create(
        work_order_id=work_order.id,
        source_call_seq=9,
        prompt_ref="prompt:code-owned",
        raw_ref="raw:model-output",
        contract_id=work_order.contract_id,
        route_lease=work_order.route_lease,
        validation_outcome=ProposalValidationOutcome.VALID_FIRST_ATTEMPT,
        attempt_count=1,
        candidate_payload_refs=(candidate_ref,),
        tokens=23,
    )


def _enabled_decision(
    state: WorkflowProcessStateV1,
    *,
    work_order_id: str = _hash("c"),
) -> TransitionDecisionV1:
    budget = BudgetDeltaV1(reserved_tokens=40)
    next_state = state_after_transition(
        state,
        transition_kind=TransitionKind.WORK_ENABLED,
        work_order_id=work_order_id,
        trigger_ref="problem:deterministic-c0",
        reserved_tokens=budget.reserved_tokens,
    )
    return TransitionDecisionV1.create(
        manifest_digest=state.manifest_digest,
        workflow_profile=state.workflow_profile,
        previous_process_digest=state.digest,
        trigger_kind=TriggerKind.PROBLEM_SELECTED,
        trigger_ref="problem:deterministic-c0",
        transition_kind=TransitionKind.WORK_ENABLED,
        work_order_id=work_order_id,
        route_lease=_route(),
        budget_delta=budget,
        next_process_digest=next_state.digest,
    )


def test_state_transition_and_replay_are_pure_and_deterministic():
    state = _initial()
    before = state.model_dump(mode="json", by_alias=True)

    first_decision = _enabled_decision(state)
    second_decision = _enabled_decision(state)
    first = apply_decision(state, first_decision)
    second = apply_decision(state, second_decision)

    assert state.model_dump(mode="json", by_alias=True) == before
    assert first_decision == second_decision
    assert first == second
    assert first.digest == second.digest
    assert first.reserved_tokens == 40
    assert state.work_items == ()


def test_same_canonical_profile_state_and_assignments_yield_same_batch():
    profile = _profile()
    state = _initial()
    assignment = _assignment()
    state_before = state.model_dump(mode="json", by_alias=True)
    assignment_before = assignment.model_dump(mode="json", by_alias=True)

    first = plan_conjecture_batch(
        profile,
        state=state,
        problem_ref="problem:deterministic-c0",
        assignments=(assignment,),
        canonical_problem_refs=("problem:deterministic-c0",),
    )
    second = plan_conjecture_batch(
        profile,
        state=state,
        problem_ref="problem:deterministic-c0",
        assignments=(assignment,),
        canonical_problem_refs=("problem:deterministic-c0",),
    )

    assert first == second
    assert first.state.digest == second.state.digest
    assert tuple(item.transition_kind for item in first.decisions) == (
        TransitionKind.WORK_ENABLED,
        TransitionKind.WORK_ISSUED,
    )
    assert first.state.selected_problem_ref == "problem:deterministic-c0"
    assert first.state.work_items[0].status == WorkItemStatus.ISSUED
    assert first.work_orders[0].route_lease == _route()
    assert state.model_dump(mode="json", by_alias=True) == state_before
    assert assignment.model_dump(mode="json", by_alias=True) == assignment_before

    replayed = state
    for decision in first.decisions:
        replayed = apply_decision(replayed, decision)
    assert replayed == first.state


def test_open_semantic_payload_does_not_change_route_budget_or_phase_decisions():
    first_assignment = _assignment(
        task_payload_ref=None,
        task_payload_value={
            "mechanism": "palimpsestic phase braid",
            "claim": "Novel prose A",
            "optional_terms": ["unclassified", "sui generis"],
        },
    )
    first = _planned(assignment=first_assignment)
    second = _planned(
        assignment=_assignment(
            task_payload_ref=None,
            task_payload_value={
                "mechanism": "unclassified Möbius coupling",
                "claim": "Novel prose B with no analogy",
            },
        )
    )

    assert first.work_orders[0].id != second.work_orders[0].id
    assert first.work_orders[0].route_lease == second.work_orders[0].route_lease
    assert first.work_orders[0].capability_grant == second.work_orders[0].capability_grant
    assert first.state.phase == second.state.phase == "conjecture"
    assert [decision.transition_kind for decision in first.decisions] == [
        decision.transition_kind for decision in second.decisions
    ]
    assert [decision.route_lease for decision in first.decisions] == [
        decision.route_lease for decision in second.decisions
    ]
    assert [decision.budget_delta for decision in first.decisions] == [
        decision.budget_delta for decision in second.decisions
    ]
    with pytest.raises(TypeError):
        first_assignment.task_payload_value["route_lease"] = "model-selected"
    with pytest.raises((AttributeError, TypeError)):
        first_assignment.task_payload_value["optional_terms"].append("route:99")


def test_model_prose_cannot_author_proposal_transition_route_budget_or_phase():
    planned = _planned()
    work_order = planned.work_orders[0]
    first_receipt = _proposal(
        work_order,
        candidate_ref="payload:novel-semantic-proposal-a",
    )
    second_receipt = _proposal(
        work_order,
        candidate_ref="payload:novel-semantic-proposal-b-with-route-prose",
    )

    first = reduce_conjecture(
        planned.state,
        WorkflowSignalV1.proposal(
            work_order,
            first_receipt,
        ),
    )
    second = reduce_conjecture(
        planned.state,
        WorkflowSignalV1.proposal(
            work_order,
            second_receipt,
        ),
    )

    first_decision = first.decisions[0]
    second_decision = second.decisions[0]
    assert first_decision.transition_kind == second_decision.transition_kind == (
        TransitionKind.PROPOSAL_RECEIVED
    )
    assert first_decision.route_lease == second_decision.route_lease == _route()
    assert first_decision.budget_delta == second_decision.budget_delta
    assert first.state.phase == second.state.phase == planned.state.phase
    assert first.state.work_items[0].status == second.state.work_items[0].status == (
        WorkItemStatus.PROPOSAL_RECEIVED
    )

    signal = WorkflowSignalV1.proposal(
        work_order,
        first_receipt,
    )
    for field, value in (
        ("transition_kind", "proposal_admitted"),
        ("route_lease", {"seat": 99}),
        ("budget_delta", {"reserved_tokens": 1_000_000}),
        ("phase", "finished"),
    ):
        payload = signal.model_dump(mode="json", by_alias=True)
        payload[field] = value
        with pytest.raises(ValidationError, match=f"{field}|extra"):
            WorkflowSignalV1.model_validate(payload)


def test_code_authored_guard_alone_controls_disposition():
    planned = _planned()
    work_order = planned.work_orders[0]
    proposal = _proposal(work_order, candidate_ref="payload:open-semantic-claim")
    received = reduce_conjecture(
        planned.state,
        WorkflowSignalV1.proposal(
            work_order,
            proposal,
        ),
    )
    finding = GuardFindingV1(
        candidate_ref=proposal.candidate_payload_refs[0],
        outcome=GuardFindingOutcome.ADMIT,
        code=GuardFindingCode.PASSED,
        detail="Code-authored anti-relapse guard admitted the proposal.",
    )
    guard = GuardResultV1.create(
        work_order_id=work_order.id,
        proposal_receipt_id=proposal.id,
        findings=(finding,),
        admitted_refs=(finding.candidate_ref,),
    )

    reduced = reduce_conjecture(
        received.state,
        WorkflowSignalV1.guarded(work_order, guard),
    )

    assert reduced.decisions[0].transition_kind == TransitionKind.PROPOSAL_ADMITTED
    assert reduced.decisions[0].guard_result_ref == guard.id
    assert reduced.decisions[0].output_refs == guard.admitted_refs
    assert reduced.state.work_items[0].status == WorkItemStatus.FINISHED


def test_work_order_result_pairing_is_fail_closed():
    planned = _planned()
    work_order = planned.work_orders[0]
    mismatched = ProposalReceiptV1.create(
        work_order_id=_hash("9"),
        source_call_seq=9,
        prompt_ref="prompt:code-owned",
        raw_ref="raw:model-output",
        contract_id=work_order.contract_id,
        route_lease=work_order.route_lease,
        validation_outcome=ProposalValidationOutcome.VALID_FIRST_ATTEMPT,
        attempt_count=1,
        candidate_payload_refs=("payload:semantic-proposal",),
        tokens=23,
    )
    with pytest.raises(ValidationError, match="another work order"):
        WorkflowSignalV1(
            kind=WorkflowSignalKind.PROPOSAL_RECEIVED,
            work_order=work_order,
            trigger_ref=mismatched.id,
            proposal_receipt=mismatched,
        )

    proposal = _proposal(work_order, candidate_ref="payload:semantic-proposal")
    received = reduce_conjecture(
        planned.state,
        WorkflowSignalV1.proposal(
            work_order,
            proposal,
        ),
    )
    finding = GuardFindingV1(
        candidate_ref=proposal.candidate_payload_refs[0],
        outcome=GuardFindingOutcome.REJECT,
        code=GuardFindingCode.CONTENT_DUPLICATE,
    )
    wrong_proposal_guard = GuardResultV1.create(
        work_order_id=work_order.id,
        proposal_receipt_id=_hash("8"),
        findings=(finding,),
        rejected_refs=(finding.candidate_ref,),
    )
    with pytest.raises(ValueError, match="another proposal receipt"):
        reduce_conjecture(
            received.state,
            WorkflowSignalV1.guarded(work_order, wrong_proposal_guard),
        )


def test_guard_must_contain_code_authored_findings():
    planned = _planned()
    work_order = planned.work_orders[0]
    proposal = _proposal(work_order, candidate_ref="payload:unguarded-semantic-proposal")

    with pytest.raises(ValidationError, match="finding|classification|partition"):
        GuardResultV1.create(
            work_order_id=work_order.id,
            proposal_receipt_id=proposal.id,
            findings=(),
        )


def test_guard_findings_must_cover_the_received_candidate_set():
    planned = _planned()
    work_order = planned.work_orders[0]
    proposal = ProposalReceiptV1.create(
        work_order_id=work_order.id,
        source_call_seq=9,
        prompt_ref="prompt:code-owned",
        raw_ref="raw:model-output",
        contract_id=work_order.contract_id,
        route_lease=work_order.route_lease,
        validation_outcome=ProposalValidationOutcome.VALID_FIRST_ATTEMPT,
        attempt_count=1,
        candidate_payload_refs=("payload:first", "payload:omitted"),
        tokens=23,
    )
    received = reduce_conjecture(
        planned.state,
        WorkflowSignalV1.proposal(work_order, proposal),
    )
    finding = GuardFindingV1(
        candidate_ref="payload:first",
        outcome=GuardFindingOutcome.ADMIT,
        code=GuardFindingCode.PASSED,
    )
    incomplete = GuardResultV1.create(
        work_order_id=work_order.id,
        proposal_receipt_id=proposal.id,
        findings=(finding,),
        admitted_refs=(finding.candidate_ref,),
    )

    with pytest.raises(ValueError, match="cover the proposal candidates"):
        reduce_conjecture(
            received.state,
            WorkflowSignalV1.guarded(work_order, incomplete),
        )


def test_candidate_payload_requires_candidate_proposal_capability():
    planned = _planned()
    original = planned.work_orders[0]
    grant = CapabilityGrantV1.create(
        allowed_outcomes=(CapabilityOutcome.ABSTENTION,),
        max_candidates=3,
        max_local_repairs=0,
        remaining_context_expansions=0,
        max_extra_context_blocks=0,
    )
    payload = original.model_dump(
        mode="python",
        by_alias=True,
        exclude={"id", "capability_grant"},
    )
    work_order = WorkOrderEnvelopeV1.create(**payload, capability_grant=grant)
    state = state_after_transition(
        _initial(),
        transition_kind=TransitionKind.WORK_ENABLED,
        work_order_id=work_order.id,
        trigger_ref=work_order.problem_ref,
    )
    state = state_after_transition(
        state,
        transition_kind=TransitionKind.WORK_ISSUED,
        work_order_id=work_order.id,
        trigger_ref=work_order.id,
    )
    proposal = _proposal(work_order, candidate_ref="payload:not-granted")

    with pytest.raises(ValueError, match="candidate capability"):
        reduce_conjecture(
            state,
            WorkflowSignalV1.proposal(work_order, proposal),
        )


def test_proposal_settlement_is_attributed_to_its_own_work_item():
    assignments = (
        ConjectureWorkAssignmentV1(
            school_id="school-0",
            route_lease=_route(),
            contract_id="conjecturer.legacy.v1",
            reserved_tokens=40,
            task_payload_schema_id="semantic.conjecture.open.v1",
            task_payload_ref="payload:school-0",
            input_refs=("problem:deterministic-c0",),
        ),
        ConjectureWorkAssignmentV1(
            school_id="school-1",
            route_lease=_route(),
            contract_id="conjecturer.legacy.v1",
            reserved_tokens=60,
            task_payload_schema_id="semantic.conjecture.open.v1",
            task_payload_ref="payload:school-1",
            input_refs=("problem:deterministic-c0",),
        ),
    )
    planned = plan_conjecture_batch(
        _profile(),
        state=_initial(),
        problem_ref="problem:deterministic-c0",
        assignments=assignments,
        canonical_problem_refs=("problem:deterministic-c0",),
    )
    work_by_school = {work.school_id: work for work in planned.work_orders}
    settled_work = work_by_school["school-0"]
    other_work = work_by_school["school-1"]
    proposal = _proposal(settled_work, candidate_ref="payload:settled")

    received = reduce_conjecture(
        planned.state,
        WorkflowSignalV1.proposal(settled_work, proposal),
    )

    assert received.decisions[0].budget_delta == BudgetDeltaV1(
        spent_tokens=23,
        released_tokens=17,
    )
    assert received.state.work_item(settled_work.id).reserved_tokens == 0
    assert received.state.work_item(other_work.id).reserved_tokens == 60
    assert received.state.reserved_tokens == 60
    assert received.state.spent_tokens == 23
    assert apply_decision(planned.state, received.decisions[0]) == received.state


def test_failed_receipt_is_retained_settled_and_replayable():
    assignment = ConjectureWorkAssignmentV1(
        school_id=None,
        route_lease=_route(),
        contract_id="conjecturer.legacy.v1",
        reserved_tokens=40,
        task_payload_schema_id="semantic.conjecture.open.v1",
        task_payload_ref="payload:failed-call",
        input_refs=("problem:deterministic-c0",),
    )
    planned = _planned(assignment=assignment)
    work_order = planned.work_orders[0]
    receipt = ProposalReceiptV1.create(
        work_order_id=work_order.id,
        source_call_seq=9,
        prompt_ref="prompt:failed-call",
        raw_ref=None,
        contract_id=work_order.contract_id,
        route_lease=work_order.route_lease,
        validation_outcome=ProposalValidationOutcome.REPAIR_EXHAUSTED,
        attempt_count=1,
        tokens=7,
    )

    reduced = reduce_conjecture(
        planned.state,
        WorkflowSignalV1.repair_exhausted(work_order, receipt),
    )

    decision = reduced.decisions[0]
    item = reduced.state.work_item(work_order.id)
    assert decision.transition_kind == TransitionKind.REPAIR_EXHAUSTED
    assert decision.trigger_ref == receipt.id
    assert decision.budget_delta == BudgetDeltaV1(
        spent_tokens=7,
        released_tokens=33,
    )
    assert reduced.proposal_receipts == (receipt,)
    assert item.proposal_receipt_id == receipt.id
    assert item.status == WorkItemStatus.FINISHED
    assert item.reserved_tokens == 0
    assert reduced.state.reserved_tokens == 0
    assert reduced.state.spent_tokens == 7
    assert apply_decision(planned.state, decision) == reduced.state


def test_candidate_count_cannot_exceed_work_order_capability():
    planned = _planned()
    work_order = planned.work_orders[0]
    assert work_order.capability_grant.max_candidates == 3
    receipt = ProposalReceiptV1.create(
        work_order_id=work_order.id,
        source_call_seq=9,
        prompt_ref="prompt:code-owned",
        raw_ref="raw:model-output",
        contract_id=work_order.contract_id,
        route_lease=work_order.route_lease,
        validation_outcome=ProposalValidationOutcome.VALID_FIRST_ATTEMPT,
        attempt_count=1,
        candidate_payload_refs=tuple(f"payload:candidate-{index}" for index in range(4)),
        tokens=23,
    )

    with pytest.raises(ValueError, match="candidate capability"):
        reduce_conjecture(
            planned.state,
            WorkflowSignalV1.proposal(
                work_order,
                receipt,
            ),
        )


def test_replay_rejects_wrong_prefix_or_tampered_next_state():
    state = _initial()
    decision = _enabled_decision(state)

    wrong_state = state.model_copy(update={"formal_fence_seq": 5, "scratch_fence_seq": 5})
    with pytest.raises(ValueError, match="previous process digest"):
        apply_decision(wrong_state, decision)

    tampered = decision.model_dump(mode="json", by_alias=True)
    tampered["next_process_digest"] = _hash("d")
    tampered.pop("id")
    forged = TransitionDecisionV1.create(**tampered)
    with pytest.raises(ValueError, match="next process digest"):
        apply_decision(state, forged)


def test_process_state_is_closed_frozen_and_requires_one_fence():
    state = _initial()
    assert state.model_config.get("extra") == "forbid"
    assert state.model_config.get("frozen") is True

    with pytest.raises(ValidationError, match="extra|forbidden"):
        WorkflowProcessStateV1.model_validate(
            {**state.model_dump(mode="json", by_alias=True), "phase_command": "skip"}
        )
    with pytest.raises(ValidationError, match="fence"):
        WorkflowProcessStateV1.initial(
            manifest_digest=state.manifest_digest,
            workflow_profile=state.workflow_profile,
            formal_fence_seq=4,
            scratch_fence_seq=5,
        )
    with pytest.raises(ValidationError, match="frozen"):
        state.phase = "conjecture"


def test_terminal_work_cannot_retain_an_unsettled_reservation():
    with pytest.raises(ValidationError, match="terminal work"):
        ConjectureWorkStateV1(
            work_order_id=_hash("a"),
            status=WorkItemStatus.FINISHED,
            reserved_tokens=1,
            outcome=WorkOutcome.NO_PROPOSAL,
        )


def test_reducer_revalidates_forged_nested_work_order_identity():
    planned = _planned()
    work_order = planned.work_orders[0]
    enabled_state = apply_decision(_initial(), planned.decisions[0])
    valid = WorkflowSignalV1(
        kind=WorkflowSignalKind.WORK_ISSUED,
        work_order=work_order,
        trigger_ref=work_order.id,
    )
    forged_route = work_order.route_lease.model_copy(update={"seat": 99})
    forged_work = work_order.model_copy(update={"route_lease": forged_route})
    forged_signal = valid.model_copy(update={"work_order": forged_work})

    with pytest.raises(ValidationError, match="id does not match"):
        reduce_conjecture(enabled_state, forged_signal)


def test_zero_local_repair_grant_refuses_authorization_and_repaired_receipt():
    planned = _planned()
    work_order = planned.work_orders[0]
    assert work_order.capability_grant.max_local_repairs == 0
    request = WorkflowSignalV1(
        kind=WorkflowSignalKind.REPAIR_REQUESTED,
        work_order=work_order,
        trigger_ref="repair:requested-by-validator",
    )
    with pytest.raises(ValueError, match="exhausted local-repair"):
        reduce_conjecture(planned.state, request)

    repaired = ProposalReceiptV1.create(
        work_order_id=work_order.id,
        source_call_seq=9,
        prompt_ref="prompt:repair",
        raw_ref="raw:repaired",
        contract_id=work_order.contract_id,
        route_lease=work_order.route_lease,
        validation_outcome=ProposalValidationOutcome.VALID_AFTER_REPAIR,
        attempt_count=2,
        candidate_payload_refs=("payload:repaired",),
        tokens=31,
    )
    with pytest.raises(ValueError, match="local-repair capability"):
        reduce_conjecture(
            planned.state,
            WorkflowSignalV1.proposal(work_order, repaired),
        )


def test_provider_call_grant_is_consumed_and_replay_visible():
    grant = CapabilityGrantV1.create(
        allowed_outcomes=(
            CapabilityOutcome.CANDIDATE_PROPOSAL,
            CapabilityOutcome.CONTEXT_REQUEST,
        ),
        max_candidates=3,
        max_local_repairs=0,
        remaining_context_expansions=1,
        max_extra_context_blocks=2,
        permitted_retrieval_channels=(),
    )
    work_order, state = _work_with_grant(grant)
    first_receipt = _proposal(work_order, candidate_ref="payload:first-call")
    first = reduce_conjecture(
        state,
        WorkflowSignalV1.proposal(work_order, first_receipt),
    )
    first_decision = first.decisions[0]
    assert first_decision.provider_call_delta == 1
    assert first.state.work_item(work_order.id).provider_calls_used == 1
    assert apply_decision(state, first_decision) == first.state

    requested = reduce_conjecture(
        first.state,
        WorkflowSignalV1(
            kind=WorkflowSignalKind.CONTEXT_REQUESTED,
            work_order=work_order,
            trigger_ref="context:request-1",
        ),
    )
    granted = reduce_conjecture(
        requested.state,
        WorkflowSignalV1(
            kind=WorkflowSignalKind.CONTEXT_GRANTED,
            work_order=work_order,
            trigger_ref="context:grant-1",
        ),
    )
    assert granted.decisions[0].context_expansion_delta == 1
    assert granted.state.work_item(work_order.id).context_expansions_used == 1
    assert apply_decision(requested.state, granted.decisions[0]) == granted.state

    second_receipt = _proposal(work_order, candidate_ref="payload:second-call")
    with pytest.raises(ValueError, match="provider-call capability"):
        reduce_conjecture(
            granted.state,
            WorkflowSignalV1.proposal(work_order, second_receipt),
        )


def test_context_expansion_grant_cannot_be_reused():
    grant = CapabilityGrantV1.create(
        allowed_outcomes=(
            CapabilityOutcome.CANDIDATE_PROPOSAL,
            CapabilityOutcome.CONTEXT_REQUEST,
        ),
        max_candidates=3,
        max_local_repairs=0,
        remaining_context_expansions=1,
        max_extra_context_blocks=2,
        permitted_retrieval_channels=(),
    )
    work_order, _state = _work_with_grant(grant)
    exhausted_item = ConjectureWorkStateV1(
        work_order_id=work_order.id,
        status=WorkItemStatus.CONTEXT_PENDING,
        proposal_receipt_id=_hash("e"),
        provider_calls_used=1,
        context_expansions_used=1,
    )
    exhausted_state = WorkflowProcessStateV1(
        manifest_digest=work_order.manifest_digest,
        workflow_profile=work_order.workflow_profile,
        selected_problem_ref=work_order.problem_ref,
        formal_fence_seq=work_order.formal_fence_seq,
        scratch_fence_seq=work_order.scratch_fence_seq,
        work_items=(exhausted_item,),
    )

    with pytest.raises(ValueError, match="exhausted context-expansion"):
        reduce_conjecture(
            exhausted_state,
            WorkflowSignalV1(
                kind=WorkflowSignalKind.CONTEXT_GRANTED,
                work_order=work_order,
                trigger_ref="context:grant-reused",
            ),
        )
