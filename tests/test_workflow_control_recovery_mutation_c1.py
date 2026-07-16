"""C1 crash prefixes and authority mutations fail closed under replay."""

from __future__ import annotations

import json

import pytest

from deepreason.harness import Harness, WellFormednessError
from deepreason.ontology import LLMAttempt, LLMCall, Rule
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
    repair_attempt_trigger_ref,
)
from deepreason.workflow.profiles import ConjectureWorkflowProfileV1
from deepreason.workflow.reducer import plan_conjecture_batch, reduce_conjecture
from deepreason.workflow.replay import WorkflowRecoveryStatus
from deepreason.workflow.state import (
    ReductionV1,
    WorkflowProcessStateV1,
    state_after_transition,
)


def _route() -> RouteLeaseRefV1:
    return RouteLeaseRefV1(
        seat=0,
        endpoint_id="c1-recovery-conjecturer",
        route_sha256="a" * 64,
    )


def _disabled_context() -> ConjectureContextPolicyV1:
    return ConjectureContextPolicyV1(
        mode="disabled",
        initial_max_blocks=0,
        initial_max_guides=0,
        max_context_expansion_requests=0,
        max_extra_blocks=0,
        permitted_retrieval_channels=(),
        coverage_slot_mandatory=False,
        exploration_slot_mandatory=False,
    )


def _profile(*, repairs: int = 0, context: bool = False):
    context_policy = (
        ConjectureContextPolicyV1(
            mode="harness_plus_model_request",
            initial_max_blocks=0,
            initial_max_guides=0,
            max_context_expansion_requests=1,
            max_extra_blocks=2,
            permitted_retrieval_channels=("keyword",),
            coverage_slot_mandatory=False,
            exploration_slot_mandatory=False,
        )
        if context
        else _disabled_context()
    )
    scopes = ("whole_object", "smallest_subtree")[:repairs]
    return ConjectureWorkflowProfileV1(
        manifest_digest=("c" if context else "b") * 64,
        mode="active_conjecture" if context else "shadow",
        workflow_profile=(
            "conjecture.active.v1" if context else "conjecture.shadow.v1"
        ),
        conjecturer_contract_id=(
            "conjecturer.turn.v4" if context else "conjecturer.legacy.v1"
        ),
        model_profile="standard",
        workload_profile="text",
        max_candidates=2,
        context_policy=context_policy,
        repair_policy=LocalRepairPolicyV1.create(
            max_schema_repairs=repairs,
            scopes=scopes,
        ),
    )


def _plan(*, repairs: int = 0, context: bool = False):
    profile = _profile(repairs=repairs, context=context)
    initial = WorkflowProcessStateV1.initial(
        manifest_digest=profile.manifest_digest,
        workflow_profile=profile.workflow_profile,
        formal_fence_seq=0,
        scratch_fence_seq=0,
    )
    planned = plan_conjecture_batch(
        profile,
        state=initial,
        problem_ref="problem:c1-crash-prefix",
        assignments=(
            ConjectureWorkAssignmentV1(
                route_lease=_route(),
                contract_id=profile.conjecturer_contract_id,
                reserved_tokens=40,
                task_payload_schema_id="semantic.conjecture.open.v1",
                task_payload_ref="problem:c1-crash-prefix",
                input_refs=("problem:c1-crash-prefix",),
            ),
        ),
        canonical_problem_refs=("problem:c1-crash-prefix",),
    )
    return planned


def _plan_with_outcomes(allowed_outcomes: tuple[CapabilityOutcome, ...]):
    original = _plan()
    original_work = original.work_orders[0]
    permits_context = CapabilityOutcome.CONTEXT_REQUEST in allowed_outcomes
    grant = CapabilityGrantV1.create(
        allowed_outcomes=allowed_outcomes,
        max_candidates=2,
        max_local_repairs=0,
        remaining_context_expansions=1 if permits_context else 0,
        max_extra_context_blocks=2 if permits_context else 0,
    )
    values = original_work.model_dump(
        mode="python",
        by_alias=True,
        exclude={"id", "capability_grant"},
    )
    work = WorkOrderEnvelopeV1.create(**values, capability_grant=grant)
    initial = WorkflowProcessStateV1.initial(
        manifest_digest=work.manifest_digest,
        workflow_profile=work.workflow_profile,
        formal_fence_seq=work.formal_fence_seq,
        scratch_fence_seq=work.scratch_fence_seq,
    )
    enabled_state = state_after_transition(
        initial,
        transition_kind=TransitionKind.WORK_ENABLED,
        work_order_id=work.id,
        trigger_ref=work.problem_ref,
    )
    enabled = TransitionDecisionV1.create(
        manifest_digest=work.manifest_digest,
        workflow_profile=work.workflow_profile,
        previous_process_digest=initial.digest,
        trigger_kind=TriggerKind.PROBLEM_SELECTED,
        trigger_ref=work.problem_ref,
        transition_kind=TransitionKind.WORK_ENABLED,
        work_order_id=work.id,
        route_lease=work.route_lease,
        next_process_digest=enabled_state.digest,
    )
    budget = original.decisions[1].budget_delta
    issued_state = state_after_transition(
        enabled_state,
        transition_kind=TransitionKind.WORK_ISSUED,
        work_order_id=work.id,
        trigger_ref=work.id,
        reserved_tokens=budget.reserved_tokens,
    )
    issued = TransitionDecisionV1.create(
        manifest_digest=work.manifest_digest,
        workflow_profile=work.workflow_profile,
        previous_process_digest=enabled_state.digest,
        trigger_kind=TriggerKind.CONTEXT_PREPARED,
        trigger_ref=work.id,
        transition_kind=TransitionKind.WORK_ISSUED,
        work_order_id=work.id,
        route_lease=work.route_lease,
        budget_delta=budget,
        next_process_digest=issued_state.digest,
    )
    return ReductionV1(
        state=issued_state,
        decisions=(enabled, issued),
        work_orders=(work,),
    )


def _record_plan(harness: Harness, planned):
    work = planned.work_orders[0]
    harness.record_control_transition(planned.decisions[0], work_order=work)
    harness.record_control_transition(planned.decisions[1])
    return work


def _record_call(
    harness: Harness,
    work,
    *,
    attempts: int = 1,
    tokens: int = 23,
    valid: bool = True,
    bound_work_order_id: str | None = None,
    attempt_tokens: tuple[int, ...] | None = None,
    usage_unknown: tuple[bool, ...] | None = None,
):
    attempt_tokens = attempt_tokens or tuple(
        tokens if index == attempts - 1 else 0 for index in range(attempts)
    )
    usage_unknown = usage_unknown or (False,) * attempts
    assert len(attempt_tokens) == attempts
    assert len(usage_unknown) == attempts
    prompt_ref = harness.blobs.put(f"c1 prompt {attempts}".encode())
    raw_ref = harness.blobs.put(b'{"candidates": []}')
    trace = [
        LLMAttempt(
            prompt_ref=prompt_ref,
            raw_ref=raw_ref,
            diagnostic_ref=(
                harness.blobs.put(f"c1 diagnostic {index}".encode())
                if not (valid and index == attempts - 1)
                else ""
            ),
            attempt=index,
            contract_id=work.contract_id,
            endpoint_id=work.route_lease.endpoint_id,
            route_sha256=work.route_lease.route_sha256,
            seat=work.route_lease.seat,
            model_profile="standard",
            transport_profile="standard",
            repair_scope="" if index == 0 else "whole_object",
            tokens=attempt_tokens[index],
            usage_unknown=usage_unknown[index],
            valid=valid and index == attempts - 1,
        )
        for index in range(attempts)
    ]
    call = LLMCall(
        role="conjecturer",
        model="c1-model",
        endpoint="mock://c1-recovery",
        prompt_ref=prompt_ref,
        raw_ref=raw_ref,
        tokens=tokens,
        attempts=attempts,
        attempt_trace=trace,
        work_order_id=bound_work_order_id or work.id,
    )
    event = harness.record_measure(inputs=["provider-result"], llm=call)
    return call, event


def _valid_proposal(work, call, call_event, *, context: bool = False):
    values = {
        "work_order_id": work.id,
        "source_call_seq": call_event.seq,
        "prompt_ref": call.prompt_ref,
        "raw_ref": call.raw_ref,
        "contract_id": work.contract_id,
        "route_lease": work.route_lease,
        "validation_outcome": ProposalValidationOutcome.VALID_FIRST_ATTEMPT,
        "attempt_count": 1,
        "candidate_payload_refs": () if context else ("candidate:c1-admit",),
        "tokens": call.tokens,
    }
    if context:
        values.update(
            context_request_hash="sha256:" + "d" * 64,
            context_request_ref="context-request:c1",
        )
    return ProposalReceiptV1.create(**values)


def _forged_provider_decision(
    planned,
    work,
    proposal,
    *,
    local_repair_delta: int,
    transition_kind: TransitionKind = TransitionKind.PROPOSAL_RECEIVED,
    spent_tokens: int | None = None,
):
    current = planned.state.work_item(work.id)
    assert current is not None
    spent_tokens = proposal.tokens if spent_tokens is None else spent_tokens
    budget = BudgetDeltaV1(
        reserved_tokens=max(0, spent_tokens - current.reserved_tokens),
        spent_tokens=spent_tokens,
        released_tokens=max(0, current.reserved_tokens - spent_tokens),
    )
    next_state = state_after_transition(
        planned.state,
        transition_kind=transition_kind,
        work_order_id=work.id,
        trigger_ref=proposal.id,
        output_refs=proposal.candidate_payload_refs,
        reserved_tokens=budget.reserved_tokens,
        spent_tokens=budget.spent_tokens,
        released_tokens=budget.released_tokens,
        provider_call_delta=1,
        local_repair_delta=local_repair_delta,
    )
    return TransitionDecisionV1.create(
        manifest_digest=work.manifest_digest,
        workflow_profile=work.workflow_profile,
        previous_process_digest=planned.state.digest,
        trigger_kind=TriggerKind.PROVIDER_RESULT,
        trigger_ref=proposal.id,
        transition_kind=transition_kind,
        work_order_id=work.id,
        route_lease=work.route_lease,
        budget_delta=budget,
        provider_call_delta=1,
        local_repair_delta=local_repair_delta,
        output_refs=proposal.candidate_payload_refs,
        next_process_digest=next_state.digest,
    )


def _record_admitted_trace(root):
    harness = Harness(root)
    planned = _plan()
    work = _record_plan(harness, planned)
    call, call_event = _record_call(harness, work)
    proposal = _valid_proposal(work, call, call_event)
    received = reduce_conjecture(
        planned.state,
        WorkflowSignalV1.proposal(work, proposal),
    )
    harness.record_control_transition(
        received.decisions[0],
        proposal_receipt=proposal,
    )
    finding = GuardFindingV1(
        candidate_ref=proposal.candidate_payload_refs[0],
        outcome=GuardFindingOutcome.ADMIT,
        code=GuardFindingCode.PASSED,
    )
    guard = GuardResultV1.create(
        work_order_id=work.id,
        proposal_receipt_id=proposal.id,
        findings=(finding,),
        admitted_refs=(finding.candidate_ref,),
    )
    admitted = reduce_conjecture(
        received.state,
        WorkflowSignalV1.guarded(work, guard),
    )
    harness.record_control_transition(
        admitted.decisions[0],
        guard_result=guard,
    )
    return harness, work


def _assert_empty_control_diffs(harness: Harness) -> None:
    controls = [event for event in harness.log.read() if event.rule == Rule.CONTROL]
    assert controls
    assert all(
        not any(event.state_diff.model_dump(mode="json", by_alias=True).values())
        for event in controls
    )


def test_recovery_reconstructs_empty_and_every_admission_crash_prefix(tmp_path):
    root = tmp_path / "admission"
    empty = Harness(root)
    empty_digest = empty.workflow_state.digest
    assert empty.workflow_state.branches == {}
    assert empty.workflow_state.outstanding_work_order_ids == ()

    harness, work = _record_admitted_trace(root)
    assert empty_digest != harness.workflow_state.digest
    expected = {
        0: WorkflowRecoveryStatus.ENABLED,
        1: WorkflowRecoveryStatus.ISSUED,
        2: WorkflowRecoveryStatus.ISSUED,
        3: WorkflowRecoveryStatus.PROVIDER_RESULT_RECEIVED,
        4: WorkflowRecoveryStatus.FINISHED,
    }
    for seq, recovery in expected.items():
        prefix = Harness.at(root, seq)
        assert prefix.workflow_state.recovery_status(work.id) == recovery
        assert prefix.state.artifacts == {}
        assert prefix.state.problems == {}
    provider_prefix = Harness.at(root, 2)
    assert tuple(provider_prefix.workflow_state.calls_by_seq) == (2,)
    assert provider_prefix.workflow_state.outstanding_work_order_ids == (work.id,)
    assert harness.workflow_state.outstanding_work_order_ids == ()
    _assert_empty_control_diffs(harness)


def test_abandonment_releases_reservation_and_checkpoints_closed_recovery(tmp_path):
    root = tmp_path / "abandoned"
    harness = Harness(root)
    planned = _plan()
    work = _record_plan(harness, planned)

    abandoned = reduce_conjecture(
        planned.state,
        WorkflowSignalV1(
            kind=WorkflowSignalKind.WORK_ABANDONED,
            work_order=work,
            trigger_ref="runtime:token_budget_exceeded",
        ),
    )
    decision = abandoned.decisions[0]
    assert decision.transition_kind == TransitionKind.WORK_ABANDONED
    assert decision.trigger_kind == TriggerKind.WORKFLOW_TERMINATION
    assert decision.budget_delta == BudgetDeltaV1(released_tokens=40)
    assert abandoned.state.reserved_tokens == 0
    item = abandoned.state.work_item(work.id)
    assert item is not None
    assert item.status.value == "abandoned"
    assert item.outcome is not None and item.outcome.value == "abandoned"

    harness.record_control_transition(decision)
    harness.write_workflow_checkpoint()

    checkpoint = json.loads((root / "workflow-checkpoint.json").read_text())
    assert checkpoint["outstanding_work_order_ids"] == []
    reopened = Harness(root)
    assert reopened.workflow_state.recovery_status(
        work.id
    ) == WorkflowRecoveryStatus.ABANDONED
    assert reopened.workflow_state.outstanding_work_order_ids == ()
    replayed_item = reopened.workflow_state.branches[
        work.id
    ].process_state.work_item(work.id)
    assert replayed_item is not None
    assert replayed_item.reserved_tokens == 0
    _assert_empty_control_diffs(harness)


def test_recovery_reconstructs_repair_requested_and_exhausted(tmp_path):
    root = tmp_path / "repair"
    harness = Harness(root)
    planned = _plan(repairs=1)
    work = _record_plan(harness, planned)
    requested = reduce_conjecture(
        planned.state,
        WorkflowSignalV1(
            kind=WorkflowSignalKind.REPAIR_REQUESTED,
            work_order=work,
            trigger_ref=repair_attempt_trigger_ref(
                0, harness.blobs.put(b"c1 diagnostic 0")
            ),
        ),
    )
    harness.record_control_transition(requested.decisions[0])
    call, call_event = _record_call(
        harness,
        work,
        attempts=2,
        tokens=7,
        valid=False,
    )
    failed = ProposalReceiptV1.create(
        work_order_id=work.id,
        source_call_seq=call_event.seq,
        prompt_ref=call.prompt_ref,
        raw_ref=call.raw_ref,
        contract_id=work.contract_id,
        route_lease=work.route_lease,
        validation_outcome=ProposalValidationOutcome.REPAIR_EXHAUSTED,
        attempt_count=2,
        tokens=call.tokens,
    )
    exhausted = reduce_conjecture(
        requested.state,
        WorkflowSignalV1.repair_exhausted(work, failed),
    )
    harness.record_control_transition(
        exhausted.decisions[0],
        proposal_receipt=failed,
    )

    assert Harness.at(root, 2).workflow_state.recovery_status(
        work.id
    ) == WorkflowRecoveryStatus.REPAIR_PENDING
    assert Harness.at(root, 3).workflow_state.recovery_status(
        work.id
    ) == WorkflowRecoveryStatus.REPAIR_PENDING
    terminal = Harness.at(root, 4)
    assert terminal.workflow_state.recovery_status(
        work.id
    ) == WorkflowRecoveryStatus.FINISHED
    item = terminal.workflow_state.branches[work.id].process_state.work_item(work.id)
    assert item.local_repairs_used == 1
    assert terminal.workflow_state.outstanding_work_order_ids == ()
    _assert_empty_control_diffs(harness)


def test_recovery_reconstructs_context_requested_and_granted(tmp_path):
    root = tmp_path / "context"
    harness = Harness(root)
    planned = _plan(context=True)
    work = _record_plan(harness, planned)
    call, call_event = _record_call(harness, work)
    proposal = _valid_proposal(work, call, call_event, context=True)
    received = reduce_conjecture(
        planned.state,
        WorkflowSignalV1.proposal(work, proposal),
    )
    harness.record_control_transition(
        received.decisions[0],
        proposal_receipt=proposal,
    )
    requested = reduce_conjecture(
        received.state,
        WorkflowSignalV1(
            kind=WorkflowSignalKind.CONTEXT_REQUESTED,
            work_order=work,
            trigger_ref=proposal.context_request_hash,
        ),
    )
    harness.record_control_transition(requested.decisions[0])
    granted = reduce_conjecture(
        requested.state,
        WorkflowSignalV1(
            kind=WorkflowSignalKind.CONTEXT_GRANTED,
            work_order=work,
            trigger_ref="sha256:" + "e" * 64,
        ),
    )
    harness.record_control_transition(granted.decisions[0])

    assert Harness.at(root, 4).workflow_state.recovery_status(
        work.id
    ) == WorkflowRecoveryStatus.CONTEXT_PENDING
    resumed = Harness.at(root, 5)
    assert resumed.workflow_state.recovery_status(
        work.id
    ) == WorkflowRecoveryStatus.ISSUED
    item = resumed.workflow_state.branches[work.id].process_state.work_item(work.id)
    assert item.context_expansions_used == 1
    assert resumed.workflow_state.outstanding_work_order_ids == (work.id,)
    _assert_empty_control_diffs(harness)


def test_deleting_and_renumbering_middle_authority_event_breaks_replay(tmp_path):
    root = tmp_path / "mutated"
    _harness, _work = _record_admitted_trace(root)
    log_path = root / "log.jsonl"
    records = [json.loads(line) for line in log_path.read_text().splitlines()]
    assert records[1]["rule"] == Rule.CONTROL.value
    del records[1]
    for seq, record in enumerate(records):
        record["seq"] = seq
    log_path.write_text(
        "".join(
            json.dumps(record, sort_keys=True, separators=(",", ":")) + "\n"
            for record in records
        )
    )

    with pytest.raises(
        WellFormednessError,
        match="issued work|previous process digest|illegal workflow transition",
    ):
        Harness(root, read_only=True)


def test_duplicate_work_and_wrong_provider_pairing_fail_without_advancing_log(tmp_path):
    duplicate_root = tmp_path / "duplicate"
    duplicate = Harness(duplicate_root)
    planned = _plan()
    work = planned.work_orders[0]
    duplicate.record_control_transition(planned.decisions[0], work_order=work)
    with pytest.raises((ValueError, WellFormednessError), match="duplicate"):
        duplicate.record_control_transition(planned.decisions[0], work_order=work)
    assert len(list(duplicate.log.read())) == 1

    pairing_root = tmp_path / "pairing"
    pairing = Harness(pairing_root)
    planned = _plan()
    work = _record_plan(pairing, planned)
    wrong_work = "sha256:" + "9" * 64
    with pytest.raises(
        WellFormednessError, match="provider call names an unknown work order"
    ):
        _record_call(
            pairing,
            work,
            bound_work_order_id=wrong_work,
        )
    assert len(list(pairing.log.read())) == 2
    assert pairing.workflow_state.recovery_status(
        work.id
    ) == WorkflowRecoveryStatus.ISSUED
    _assert_empty_control_diffs(pairing)


def test_work_enabled_cannot_select_a_problem_other_than_its_work_order(tmp_path):
    harness = Harness(tmp_path)
    planned = _plan()
    work = planned.work_orders[0]
    original = planned.decisions[0]
    initial = WorkflowProcessStateV1.initial(
        manifest_digest=work.manifest_digest,
        workflow_profile=work.workflow_profile,
        formal_fence_seq=work.formal_fence_seq,
        scratch_fence_seq=work.scratch_fence_seq,
    )
    wrong_problem = "problem:forged-selection"
    forged_state = state_after_transition(
        initial,
        transition_kind=TransitionKind.WORK_ENABLED,
        work_order_id=work.id,
        trigger_ref=wrong_problem,
    )
    forged = TransitionDecisionV1.create(
        manifest_digest=original.manifest_digest,
        workflow_profile=original.workflow_profile,
        previous_process_digest=original.previous_process_digest,
        trigger_kind=original.trigger_kind,
        trigger_ref=wrong_problem,
        transition_kind=original.transition_kind,
        work_order_id=original.work_order_id,
        route_lease=original.route_lease,
        next_process_digest=forged_state.digest,
    )

    with pytest.raises(
        (ValueError, WellFormednessError), match="selected problem"
    ):
        harness.record_control_transition(forged, work_order=work)
    assert list(harness.log.read()) == []


def test_work_issued_requires_the_exact_prepared_context_trigger(tmp_path):
    harness = Harness(tmp_path)
    planned = _plan()
    work = planned.work_orders[0]
    harness.record_control_transition(planned.decisions[0], work_order=work)
    original = planned.decisions[1]
    forged = TransitionDecisionV1.create(
        manifest_digest=original.manifest_digest,
        workflow_profile=original.workflow_profile,
        previous_process_digest=original.previous_process_digest,
        trigger_kind=original.trigger_kind,
        trigger_ref="sha256:" + "8" * 64,
        transition_kind=original.transition_kind,
        work_order_id=original.work_order_id,
        route_lease=original.route_lease,
        budget_delta=original.budget_delta,
        next_process_digest=original.next_process_digest,
    )

    with pytest.raises(
        WellFormednessError,
        match="work-issued trigger differs from its prepared context",
    ):
        harness.record_control_transition(forged)
    assert len(list(harness.log.read())) == 1
    assert harness.workflow_state.recovery_status(
        work.id
    ) == WorkflowRecoveryStatus.ENABLED


def test_repair_request_replay_enforces_the_work_order_ceiling(tmp_path):
    harness = Harness(tmp_path)
    planned = _plan(repairs=0)
    work = _record_plan(harness, planned)
    signal = WorkflowSignalV1(
        kind=WorkflowSignalKind.REPAIR_REQUESTED,
        work_order=work,
        trigger_ref="repair:forged-request",
    )
    with pytest.raises(ValueError, match="exhausted local-repair"):
        reduce_conjecture(planned.state, signal)

    forged_state = state_after_transition(
        planned.state,
        transition_kind=TransitionKind.REPAIR_REQUESTED,
        work_order_id=work.id,
        trigger_ref=signal.trigger_ref,
    )
    forged = TransitionDecisionV1.create(
        manifest_digest=work.manifest_digest,
        workflow_profile=work.workflow_profile,
        previous_process_digest=planned.state.digest,
        trigger_kind=TriggerKind.REPAIR_DECISION,
        trigger_ref=signal.trigger_ref,
        transition_kind=TransitionKind.REPAIR_REQUESTED,
        work_order_id=work.id,
        route_lease=work.route_lease,
        next_process_digest=forged_state.digest,
    )
    with pytest.raises(
        (ValueError, WellFormednessError), match="exhausted local-repair"
    ):
        harness.record_control_transition(forged)
    assert len(list(harness.log.read())) == 2


def test_repaired_receipt_attempts_must_match_replay_consumption(tmp_path):
    harness = Harness(tmp_path)
    planned = _plan(repairs=2)
    work = _record_plan(harness, planned)
    requested = reduce_conjecture(
        planned.state,
        WorkflowSignalV1(
            kind=WorkflowSignalKind.REPAIR_REQUESTED,
            work_order=work,
            trigger_ref=repair_attempt_trigger_ref(
                0, harness.blobs.put(b"c1 diagnostic 0")
            ),
        ),
    )
    harness.record_control_transition(requested.decisions[0])
    call, call_event = _record_call(harness, work, attempts=2)
    proposal = ProposalReceiptV1.create(
        work_order_id=work.id,
        source_call_seq=call_event.seq,
        prompt_ref=call.prompt_ref,
        raw_ref=call.raw_ref,
        contract_id=work.contract_id,
        route_lease=work.route_lease,
        validation_outcome=ProposalValidationOutcome.VALID_AFTER_REPAIR,
        attempt_count=2,
        candidate_payload_refs=("candidate:repaired",),
        tokens=call.tokens,
    )
    valid = reduce_conjecture(
        requested.state,
        WorkflowSignalV1.proposal(work, proposal),
    )
    assert valid.decisions[0].local_repair_delta == 1
    forged = _forged_provider_decision(
        requested,
        work,
        proposal,
        local_repair_delta=0,
    )

    with pytest.raises(
        (ValueError, WellFormednessError),
        match="attempt count differs from local-repair",
    ):
        harness.record_control_transition(forged, proposal_receipt=proposal)
    assert len(list(harness.log.read())) == 4


def test_replay_rejects_candidate_count_above_work_order_capability(tmp_path):
    harness = Harness(tmp_path)
    planned = _plan()
    work = _record_plan(harness, planned)
    call, call_event = _record_call(harness, work)
    proposal = ProposalReceiptV1.create(
        work_order_id=work.id,
        source_call_seq=call_event.seq,
        prompt_ref=call.prompt_ref,
        raw_ref=call.raw_ref,
        contract_id=work.contract_id,
        route_lease=work.route_lease,
        validation_outcome=ProposalValidationOutcome.VALID_FIRST_ATTEMPT,
        attempt_count=1,
        candidate_payload_refs=("candidate:one", "candidate:two", "candidate:three"),
        tokens=call.tokens,
    )
    with pytest.raises(ValueError, match="candidate capability"):
        reduce_conjecture(
            planned.state,
            WorkflowSignalV1.proposal(work, proposal),
        )
    forged = _forged_provider_decision(
        planned,
        work,
        proposal,
        local_repair_delta=0,
    )

    with pytest.raises(
        (ValueError, WellFormednessError), match="candidate capability"
    ):
        harness.record_control_transition(forged, proposal_receipt=proposal)
    assert len(list(harness.log.read())) == 3


@pytest.mark.parametrize(
    ("case", "allowed_outcomes", "receipt_payload", "error"),
    (
        (
            "candidate",
            (CapabilityOutcome.ABSTENTION,),
            {"candidate_payload_refs": ("candidate:not-granted",)},
            "candidate capability",
        ),
        (
            "context",
            (CapabilityOutcome.CANDIDATE_PROPOSAL,),
            {
                "context_request_hash": "sha256:" + "7" * 64,
                "context_request_ref": "context-request:not-granted",
            },
            "context-request capability",
        ),
        (
            "abstention",
            (CapabilityOutcome.CANDIDATE_PROPOSAL,),
            {
                "abstention_hash": "sha256:" + "8" * 64,
                "abstention_ref": "abstention:not-granted",
            },
            "abstention capability",
        ),
    ),
)
def test_replay_enforces_allowed_outcome_for_every_proposal_payload(
    tmp_path,
    case,
    allowed_outcomes,
    receipt_payload,
    error,
):
    harness = Harness(tmp_path / case)
    planned = _plan_with_outcomes(allowed_outcomes)
    work = _record_plan(harness, planned)
    call, call_event = _record_call(harness, work)
    proposal = ProposalReceiptV1.create(
        work_order_id=work.id,
        source_call_seq=call_event.seq,
        prompt_ref=call.prompt_ref,
        raw_ref=call.raw_ref,
        contract_id=work.contract_id,
        route_lease=work.route_lease,
        validation_outcome=ProposalValidationOutcome.VALID_FIRST_ATTEMPT,
        attempt_count=1,
        tokens=call.tokens,
        **receipt_payload,
    )
    with pytest.raises(ValueError, match=error):
        reduce_conjecture(
            planned.state,
            WorkflowSignalV1.proposal(work, proposal),
        )
    forged = _forged_provider_decision(
        planned,
        work,
        proposal,
        local_repair_delta=0,
    )

    with pytest.raises((ValueError, WellFormednessError), match=error):
        harness.record_control_transition(forged, proposal_receipt=proposal)
    assert len(list(harness.log.read())) == 3


def test_context_requested_replay_requires_context_capability(tmp_path):
    harness = Harness(tmp_path)
    planned = _plan()
    work = _record_plan(harness, planned)
    call, call_event = _record_call(harness, work)
    proposal = _valid_proposal(work, call, call_event)
    received = reduce_conjecture(
        planned.state,
        WorkflowSignalV1.proposal(work, proposal),
    )
    harness.record_control_transition(
        received.decisions[0], proposal_receipt=proposal
    )
    trigger = "sha256:" + "6" * 64
    signal = WorkflowSignalV1(
        kind=WorkflowSignalKind.CONTEXT_REQUESTED,
        work_order=work,
        trigger_ref=trigger,
    )
    with pytest.raises(ValueError, match="does not grant context-request"):
        reduce_conjecture(received.state, signal)

    forged_state = state_after_transition(
        received.state,
        transition_kind=TransitionKind.CONTEXT_REQUESTED,
        work_order_id=work.id,
        trigger_ref=trigger,
    )
    forged = TransitionDecisionV1.create(
        manifest_digest=work.manifest_digest,
        workflow_profile=work.workflow_profile,
        previous_process_digest=received.state.digest,
        trigger_kind=TriggerKind.PROVIDER_RESULT,
        trigger_ref=trigger,
        transition_kind=TransitionKind.CONTEXT_REQUESTED,
        work_order_id=work.id,
        route_lease=work.route_lease,
        next_process_digest=forged_state.digest,
    )
    with pytest.raises(
        (ValueError, WellFormednessError), match="does not grant context-request"
    ):
        harness.record_control_transition(forged)
    assert len(list(harness.log.read())) == 4


@pytest.mark.parametrize("receipt_has_request", (False, True))
def test_context_requested_trigger_must_match_stored_proposal(
    tmp_path, receipt_has_request
):
    harness = Harness(tmp_path / str(receipt_has_request))
    planned = _plan(context=True)
    work = _record_plan(harness, planned)
    call, call_event = _record_call(harness, work)
    proposal = _valid_proposal(
        work,
        call,
        call_event,
        context=receipt_has_request,
    )
    received = reduce_conjecture(
        planned.state,
        WorkflowSignalV1.proposal(work, proposal),
    )
    harness.record_control_transition(
        received.decisions[0], proposal_receipt=proposal
    )
    trigger = "sha256:" + "5" * 64
    requested = reduce_conjecture(
        received.state,
        WorkflowSignalV1(
            kind=WorkflowSignalKind.CONTEXT_REQUESTED,
            work_order=work,
            trigger_ref=trigger,
        ),
    )

    with pytest.raises(
        (ValueError, WellFormednessError), match="stored proposal receipt"
    ):
        harness.record_control_transition(requested.decisions[0])
    assert len(list(harness.log.read())) == 4


def test_replay_rejects_a_second_call_bound_to_one_call_work(tmp_path):
    harness = Harness(tmp_path)
    planned = _plan()
    work = _record_plan(harness, planned)
    _record_call(harness, work)

    with pytest.raises(WellFormednessError, match="provider-call capability"):
        _record_call(harness, work)

    assert len(list(harness.log.read())) == 3


def test_bound_provider_call_requires_prior_work_enable_and_issue(tmp_path):
    planned = _plan()
    work = planned.work_orders[0]

    before_enable = Harness(tmp_path / "before-enable")
    with pytest.raises(
        WellFormednessError, match="provider call names an unknown work order"
    ):
        _record_call(before_enable, work)
    assert list(before_enable.log.read()) == []

    before_issue = Harness(tmp_path / "before-issue")
    before_issue.record_control_transition(planned.decisions[0], work_order=work)
    with pytest.raises(
        (ValueError, WellFormednessError), match="preceded by issued work"
    ):
        _record_call(before_issue, work)
    assert len(list(before_issue.log.read())) == 1


@pytest.mark.parametrize(
    ("transition_kind", "outcome", "valid", "candidate_refs"),
    (
        (
            TransitionKind.PROPOSAL_RECEIVED,
            ProposalValidationOutcome.REPAIR_EXHAUSTED,
            False,
            (),
        ),
        (
            TransitionKind.REPAIR_EXHAUSTED,
            ProposalValidationOutcome.VALID_FIRST_ATTEMPT,
            True,
            ("candidate:wrong-terminal",),
        ),
    ),
)
def test_provider_transition_requires_a_matching_validation_outcome(
    tmp_path,
    transition_kind,
    outcome,
    valid,
    candidate_refs,
):
    harness = Harness(tmp_path)
    planned = _plan()
    work = _record_plan(harness, planned)
    call, call_event = _record_call(harness, work, valid=valid)
    proposal = ProposalReceiptV1.create(
        work_order_id=work.id,
        source_call_seq=call_event.seq,
        prompt_ref=call.prompt_ref,
        raw_ref=call.raw_ref,
        contract_id=work.contract_id,
        route_lease=work.route_lease,
        validation_outcome=outcome,
        attempt_count=1,
        candidate_payload_refs=candidate_refs,
        tokens=call.tokens,
    )
    forged = _forged_provider_decision(
        planned,
        work,
        proposal,
        local_repair_delta=0,
        transition_kind=transition_kind,
    )

    with pytest.raises(
        (ValueError, WellFormednessError), match="validation outcome"
    ):
        harness.record_control_transition(forged, proposal_receipt=proposal)
    assert len(list(harness.log.read())) == 3


def test_proposal_spend_must_equal_the_attempt_trace_total(tmp_path):
    harness = Harness(tmp_path)
    planned = _plan()
    work = _record_plan(harness, planned)
    call, call_event = _record_call(
        harness,
        work,
        tokens=23,
        attempt_tokens=(22,),
    )
    proposal = _valid_proposal(work, call, call_event)
    received = reduce_conjecture(
        planned.state,
        WorkflowSignalV1.proposal(work, proposal),
    )

    with pytest.raises(
        WellFormednessError, match="attempt-trace token total"
    ):
        harness.record_control_transition(
            received.decisions[0],
            proposal_receipt=proposal,
        )
    assert len(list(harness.log.read())) == 3


def test_transport_failure_allows_zero_spend_for_unknown_usage(tmp_path):
    root = tmp_path / "unknown-usage"
    harness = Harness(root)
    planned = _plan(repairs=1)
    work = _record_plan(harness, planned)
    requested = reduce_conjecture(
        planned.state,
        WorkflowSignalV1(
            kind=WorkflowSignalKind.REPAIR_REQUESTED,
            work_order=work,
            trigger_ref=repair_attempt_trigger_ref(
                0, harness.blobs.put(b"c1 diagnostic 0")
            ),
        ),
    )
    harness.record_control_transition(requested.decisions[0])
    call, call_event = _record_call(
        harness,
        work,
        attempts=2,
        tokens=7,
        valid=False,
        attempt_tokens=(7, 0),
        usage_unknown=(False, True),
    )
    proposal = ProposalReceiptV1.create(
        work_order_id=work.id,
        source_call_seq=call_event.seq,
        prompt_ref=call.prompt_ref,
        raw_ref=call.raw_ref,
        contract_id=work.contract_id,
        route_lease=work.route_lease,
        validation_outcome=ProposalValidationOutcome.TRANSPORT_FAILED,
        attempt_count=2,
        tokens=call.tokens,
    )
    exhausted = reduce_conjecture(
        requested.state,
        WorkflowSignalV1.repair_exhausted(work, proposal),
    )
    harness.record_control_transition(
        exhausted.decisions[0],
        proposal_receipt=proposal,
    )

    reopened = Harness(root)
    assert reopened.workflow_state.recovery_status(
        work.id
    ) == WorkflowRecoveryStatus.FINISHED


def test_unknown_usage_attempt_cannot_claim_known_tokens(tmp_path):
    harness = Harness(tmp_path)
    planned = _plan()
    work = _record_plan(harness, planned)
    call, call_event = _record_call(
        harness,
        work,
        tokens=0,
        valid=False,
        attempt_tokens=(5,),
        usage_unknown=(True,),
    )
    proposal = ProposalReceiptV1.create(
        work_order_id=work.id,
        source_call_seq=call_event.seq,
        prompt_ref=call.prompt_ref,
        raw_ref=call.raw_ref,
        contract_id=work.contract_id,
        route_lease=work.route_lease,
        validation_outcome=ProposalValidationOutcome.TRANSPORT_FAILED,
        attempt_count=1,
        tokens=0,
    )
    exhausted = reduce_conjecture(
        planned.state,
        WorkflowSignalV1.repair_exhausted(work, proposal),
    )

    with pytest.raises(WellFormednessError, match="unknown usage.*zero tokens"):
        harness.record_control_transition(
            exhausted.decisions[0],
            proposal_receipt=proposal,
        )
    assert len(list(harness.log.read())) == 3


def test_proposal_budget_spend_must_equal_the_provider_call(tmp_path):
    harness = Harness(tmp_path)
    planned = _plan()
    work = _record_plan(harness, planned)
    call, call_event = _record_call(harness, work)
    proposal = _valid_proposal(work, call, call_event)
    forged = _forged_provider_decision(
        planned,
        work,
        proposal,
        local_repair_delta=0,
        spent_tokens=proposal.tokens - 1,
    )

    with pytest.raises(
        (ValueError, WellFormednessError), match="budget settlement"
    ):
        harness.record_control_transition(forged, proposal_receipt=proposal)
    assert len(list(harness.log.read())) == 3
