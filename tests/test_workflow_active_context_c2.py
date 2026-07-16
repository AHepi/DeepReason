"""C2 active conjecture context authority is fresh, bounded, and replayable."""

from __future__ import annotations

import pytest

from deepreason.harness import Harness
from deepreason.llm.adapter import WorkflowAuthorizationError
from deepreason.workflow.models import CapabilityOutcome, TransitionKind
from deepreason.workflow.replay import WorkflowRecoveryStatus

from tests.test_conjecturer_turn_v4 import (
    _candidate_wire,
    _request_only,
    _run_turn,
)


def _controls(harness: Harness):
    rows = []
    for event in harness.log.read():
        if event.control is None:
            continue
        _schema, decision = harness.objects.get(
            event.control.decision_ref,
            schema="workflow-transition-decision",
        )
        rows.append((event, decision))
    return rows


def _turn_events(harness: Harness):
    return [
        event for event in harness.log.read() if event.conjecture_turn is not None
    ]


def test_grant_closes_parent_and_dispatches_fresh_reduced_child(tmp_path):
    fixture, admitted, _prompts = _run_turn(
        tmp_path,
        [
            _request_only("quasar-only", "keyword"),
            {"candidates": [_candidate_wire("Fresh child candidate.")]},
        ],
    )
    harness = fixture[0]
    calls = [
        event
        for event in harness.log.read()
        if event.llm is not None and event.llm.role == "conjecturer"
    ]
    assert len(calls) == 2
    parent_id, child_id = (event.llm.work_order_id for event in calls)
    assert parent_id is not None and child_id is not None and parent_id != child_id
    parent = harness.workflow_state.work_orders[parent_id]
    child = harness.workflow_state.work_orders[child_id]
    assert parent.capability_grant.remaining_context_expansions == 1
    assert child.capability_grant.remaining_context_expansions == 0
    assert CapabilityOutcome.CONTEXT_REQUEST in child.capability_grant.allowed_outcomes
    assert child.input_refs[-1] == parent_id
    assert child.advisory_context_ref != parent.advisory_context_ref
    assert [event.llm.work_order_id for event in calls].count(parent_id) == 1
    assert [event.llm.work_order_id for event in calls].count(child_id) == 1

    controls = _controls(harness)
    parent_controls = {
        decision.transition_kind: event
        for event, decision in controls
        if decision.work_order_id == parent_id
    }
    child_controls = {
        decision.transition_kind: event
        for event, decision in controls
        if decision.work_order_id == child_id
    }
    grant_turn = next(
        event
        for event in _turn_events(harness)
        if event.conjecture_turn.action.value == "context_granted"
    )
    assert (
        parent_controls[TransitionKind.PROPOSAL_RECEIVED].seq
        < parent_controls[TransitionKind.CONTEXT_REQUESTED].seq
        < parent_controls[TransitionKind.CONTEXT_GRANTED].seq
        < parent_controls[TransitionKind.WORK_FINISHED].seq
        < grant_turn.seq
        < child_controls[TransitionKind.WORK_ENABLED].seq
        < child_controls[TransitionKind.WORK_ISSUED].seq
        < calls[1].seq
        < child_controls[TransitionKind.PROPOSAL_RECEIVED].seq
        < child_controls[TransitionKind.PROPOSAL_ADMITTED].seq
    )
    parent_receipt = next(
        receipt
        for receipt in harness.workflow_state.proposal_receipts.values()
        if receipt.work_order_id == parent_id
    )
    assert parent_receipt.context_request_hash == grant_turn.conjecture_turn.request_hash
    assert parent_receipt.context_request_ref == grant_turn.conjecture_turn.request_ref
    assert harness.workflow_state.outstanding_work_order_ids == ()
    assert len(admitted) == 1

    request_prefix = Harness.at(
        harness.root,
        parent_controls[TransitionKind.CONTEXT_REQUESTED].seq,
    )
    assert request_prefix.workflow_state.recovery_status(
        parent_id
    ) == WorkflowRecoveryStatus.CONTEXT_PENDING
    grant_prefix = Harness.at(
        harness.root,
        parent_controls[TransitionKind.CONTEXT_GRANTED].seq,
    )
    assert grant_prefix.workflow_state.recovery_status(
        parent_id
    ) == WorkflowRecoveryStatus.PROVIDER_RESULT_RECEIVED
    reopened = Harness(harness.root)
    assert reopened.workflow_state.digest == harness.workflow_state.digest
    assert reopened.workflow_state.outstanding_work_order_ids == ()


def test_denial_and_exhaustion_controls_precede_typed_turn_events(tmp_path):
    denied_fixture, denied_admitted, _ = _run_turn(
        tmp_path / "denied",
        [_request_only("quasar-only", "keyword")],
        context_mode="harness_only",
    )
    denied = denied_fixture[0]
    denied_turn = _turn_events(denied)[0]
    denied_rows = _controls(denied)
    denied_kinds = [decision.transition_kind for _event, decision in denied_rows]
    assert denied_kinds[-4:] == [
        TransitionKind.PROPOSAL_RECEIVED,
        TransitionKind.CONTEXT_REQUESTED,
        TransitionKind.CONTEXT_DENIED,
        TransitionKind.WORK_FINISHED,
    ]
    assert denied_rows[-1][0].seq < denied_turn.seq
    assert denied_turn.conjecture_turn.action.value == "context_denied"
    assert denied_admitted == []
    assert denied.workflow_state.outstanding_work_order_ids == ()

    exhausted_fixture, exhausted_admitted, _ = _run_turn(
        tmp_path / "exhausted",
        [
            _request_only("quasar-only", "keyword"),
            _request_only("tertiary-only", "keyword"),
        ],
    )
    exhausted = exhausted_fixture[0]
    exhausted_turn = _turn_events(exhausted)[-1]
    exhausted_rows = _controls(exhausted)
    exhausted_work_id = next(
        event.llm.work_order_id
        for event in reversed(list(exhausted.log.read()))
        if event.llm is not None
    )
    child_rows = [
        (event, decision)
        for event, decision in exhausted_rows
        if decision.work_order_id == exhausted_work_id
    ]
    assert [decision.transition_kind for _event, decision in child_rows][-4:] == [
        TransitionKind.PROPOSAL_RECEIVED,
        TransitionKind.CONTEXT_REQUESTED,
        TransitionKind.CONTEXT_DENIED,
        TransitionKind.WORK_FINISHED,
    ]
    assert child_rows[-1][0].seq < exhausted_turn.seq
    assert exhausted_turn.conjecture_turn.action.value == "context_exhausted"
    assert exhausted_admitted == []
    assert exhausted.workflow_state.outstanding_work_order_ids == ()


def test_abstention_receipt_closes_work_before_semantic_turn(tmp_path):
    fixture, admitted, _ = _run_turn(
        tmp_path,
        [
            {
                "abstention": {
                    "search_signal": "stuck",
                    "note": "The bounded view does not support a candidate.",
                }
            }
        ],
    )
    harness = fixture[0]
    call = next(event for event in harness.log.read() if event.llm is not None)
    work_id = call.llm.work_order_id
    assert work_id is not None
    receipt = next(iter(harness.workflow_state.proposal_receipts.values()))
    turn = _turn_events(harness)[0]
    controls = [
        (event, decision)
        for event, decision in _controls(harness)
        if decision.work_order_id == work_id
    ]
    finished = next(
        event
        for event, decision in controls
        if decision.transition_kind == TransitionKind.WORK_FINISHED
    )
    assert receipt.abstention_hash == turn.conjecture_turn.abstention_hash
    assert receipt.abstention_ref == turn.conjecture_turn.abstention_ref
    assert finished.seq < turn.seq
    assert admitted == []
    assert harness.workflow_state.recovery_status(
        work_id
    ) == WorkflowRecoveryStatus.FINISHED
    assert harness.workflow_state.outstanding_work_order_ids == ()


def test_active_guard_persistence_failure_prevents_formal_admission(
    tmp_path,
    monkeypatch,
):
    original = Harness.record_control_transition

    def fail_guard(self, decision, **records):
        if decision.transition_kind == TransitionKind.PROPOSAL_ADMITTED:
            raise OSError("injected guard persistence failure")
        return original(self, decision, **records)

    monkeypatch.setattr(Harness, "record_control_transition", fail_guard)
    with pytest.raises(WorkflowAuthorizationError):
        _run_turn(
            tmp_path,
            [{"candidates": [_candidate_wire("Must never be admitted.")]}],
        )

    recovered = Harness(tmp_path / "run")
    assert recovered.state.artifacts == {}
    assert not any(event.rule.value == "Conj" for event in recovered.log.read())
    work_id = next(iter(recovered.workflow_state.work_orders))
    assert recovered.workflow_state.recovery_status(
        work_id
    ) == WorkflowRecoveryStatus.PROVIDER_RESULT_RECEIVED
