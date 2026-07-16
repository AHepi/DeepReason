"""C1 Control events reconstruct authority without model or reducer reruns."""

from __future__ import annotations

import copy
import json

import pytest

from deepreason.capture.detection import gate_block_count
from deepreason.harness import Harness, WellFormednessError
from deepreason.ontology import LLMAttempt, LLMCall, Rule
from deepreason.run_manifest import ConjectureContextPolicyV1
from deepreason.workflow.events import ConjectureWorkAssignmentV1, WorkflowSignalV1
from deepreason.workflow.models import (
    GuardFindingCode,
    GuardFindingOutcome,
    GuardFindingV1,
    GuardResultV1,
    LocalRepairPolicyV1,
    ProposalReceiptV1,
    ProposalValidationOutcome,
    RouteLeaseRefV1,
)
from deepreason.workflow.profiles import ConjectureWorkflowProfileV1
from deepreason.workflow.reducer import plan_conjecture_batch, reduce_conjecture
from deepreason.workflow.replay import WorkflowRecoveryStatus
from deepreason.workflow.state import WorkflowProcessStateV1


def _route() -> RouteLeaseRefV1:
    return RouteLeaseRefV1(
        seat=0,
        endpoint_id="c1-conjecturer",
        route_sha256="a" * 64,
    )


def _profile() -> ConjectureWorkflowProfileV1:
    return ConjectureWorkflowProfileV1(
        manifest_digest="b" * 64,
        mode="shadow",
        workflow_profile="conjecture.shadow.v1",
        conjecturer_contract_id="conjecturer.legacy.v1",
        model_profile="standard",
        workload_profile="text",
        max_candidates=2,
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
        repair_policy=LocalRepairPolicyV1.create(
            max_schema_repairs=0,
            scopes=(),
        ),
    )


def _planned():
    profile = _profile()
    initial = WorkflowProcessStateV1.initial(
        manifest_digest=profile.manifest_digest,
        workflow_profile=profile.workflow_profile,
        formal_fence_seq=0,
        scratch_fence_seq=0,
    )
    return initial, plan_conjecture_batch(
        profile,
        state=initial,
        problem_ref="problem:c1-replay",
        assignments=(
            ConjectureWorkAssignmentV1(
                route_lease=_route(),
                contract_id=profile.conjecturer_contract_id,
                reserved_tokens=40,
                task_payload_schema_id="semantic.conjecture.open.v1",
                task_payload_ref="problem:c1-replay",
                input_refs=("problem:c1-replay",),
            ),
        ),
        canonical_problem_refs=("problem:c1-replay",),
    )


def _call(harness: Harness, work_order_id: str, *, tokens: int = 23) -> LLMCall:
    prompt_ref = harness.blobs.put(b"c1 prompt")
    raw_ref = harness.blobs.put(b'{"candidates": []}')
    attempt = LLMAttempt(
        prompt_ref=prompt_ref,
        raw_ref=raw_ref,
        attempt=0,
        contract_id="conjecturer.legacy.v1",
        endpoint_id="c1-conjecturer",
        route_sha256="a" * 64,
        seat=0,
        model_profile="standard",
        transport_profile="standard",
        tokens=tokens,
        valid=True,
    )
    return LLMCall(
        role="conjecturer",
        model="c1-model",
        endpoint="mock://c1",
        prompt_ref=prompt_ref,
        raw_ref=raw_ref,
        tokens=tokens,
        attempts=1,
        attempt_trace=[attempt],
        work_order_id=work_order_id,
    )


def _write_complete_trace(root, *, call_work_order_id: str | None = None):
    harness = Harness(root)
    initial, planned = _planned()
    work = planned.work_orders[0]
    harness.record_control_transition(
        planned.decisions[0],
        work_order=work,
    )
    harness.record_control_transition(planned.decisions[1])
    call = _call(harness, call_work_order_id or work.id)
    call_event = harness.record_measure(inputs=["provider-result"], llm=call)
    proposal = ProposalReceiptV1.create(
        work_order_id=work.id,
        source_call_seq=call_event.seq,
        prompt_ref=call.prompt_ref,
        raw_ref=call.raw_ref,
        contract_id=work.contract_id,
        route_lease=work.route_lease,
        validation_outcome=ProposalValidationOutcome.VALID_FIRST_ATTEMPT,
        attempt_count=1,
        candidate_payload_refs=("candidate:c1",),
        tokens=call.tokens,
    )
    received = reduce_conjecture(
        planned.state,
        WorkflowSignalV1.proposal(work, proposal),
    )
    harness.record_control_transition(
        received.decisions[0],
        proposal_receipt=proposal,
    )
    finding = GuardFindingV1(
        candidate_ref="candidate:c1",
        outcome=GuardFindingOutcome.ADMIT,
        code=GuardFindingCode.PASSED,
    )
    guard = GuardResultV1.create(
        work_order_id=work.id,
        proposal_receipt_id=proposal.id,
        findings=(finding,),
        admitted_refs=(finding.candidate_ref,),
    )
    guarded = reduce_conjecture(
        received.state,
        WorkflowSignalV1.guarded(work, guard),
    )
    harness.record_control_transition(
        guarded.decisions[0],
        guard_result=guard,
    )
    harness.write_workflow_checkpoint()
    return harness, initial, planned, received, guarded


def test_control_trace_round_trips_every_prefix_with_empty_formal_diff(tmp_path):
    harness, initial, planned, received, guarded = _write_complete_trace(tmp_path)
    work = planned.work_orders[0]
    events = list(harness.log.read())

    assert [event.rule for event in events] == [
        Rule.CONTROL,
        Rule.CONTROL,
        Rule.MEASURE,
        Rule.CONTROL,
        Rule.CONTROL,
    ]
    assert all(
        not any(event.state_diff.model_dump(mode="json", by_alias=True).values())
        for event in events
        if event.rule == Rule.CONTROL
    )
    assert list(events[0].outputs) == [work.id, planned.decisions[0].id]
    assert list(events[1].outputs) == [planned.decisions[1].id]
    assert list(events[3].outputs) == [
        received.proposal_receipts[0].id,
        received.decisions[0].id,
    ]
    assert list(events[4].outputs) == [
        guarded.guard_results[0].id,
        guarded.decisions[0].id,
    ]

    prefixes = {
        0: WorkflowRecoveryStatus.ENABLED,
        1: WorkflowRecoveryStatus.ISSUED,
        2: WorkflowRecoveryStatus.ISSUED,
        3: WorkflowRecoveryStatus.PROVIDER_RESULT_RECEIVED,
        4: WorkflowRecoveryStatus.FINISHED,
    }
    for seq, expected in prefixes.items():
        replayed = Harness.at(tmp_path, seq)
        assert replayed.workflow_state.recovery_status(work.id) == expected
    assert Harness.at(tmp_path, 4).workflow_state.branches[work.id].process_state == (
        guarded.state
    )
    assert initial.work_items == ()


def test_reopen_replays_workflow_without_reducer_or_model(tmp_path, monkeypatch):
    harness, _initial, planned, _received, _guarded = _write_complete_trace(tmp_path)
    expected_digest = harness.workflow_state.digest
    expected_formal = copy.deepcopy(harness.state)

    def forbidden(*_args, **_kwargs):
        raise AssertionError("replay called a live reducer or model")

    monkeypatch.setattr("deepreason.workflow.reducer.reduce_conjecture", forbidden)
    reopened = Harness(tmp_path)

    assert reopened.workflow_state.digest == expected_digest
    assert reopened.workflow_state.outstanding_work_order_ids == ()
    assert reopened.state == expected_formal
    assert reopened.workflow_state.recovery_status(
        planned.work_orders[0].id
    ) == WorkflowRecoveryStatus.FINISHED


def test_duplicate_work_order_enable_fails_closed(tmp_path):
    harness = Harness(tmp_path)
    _initial, planned = _planned()
    work = planned.work_orders[0]
    harness.record_control_transition(planned.decisions[0], work_order=work)

    with pytest.raises((ValueError, WellFormednessError), match="duplicate"):
        harness.record_control_transition(planned.decisions[0], work_order=work)


def test_provider_response_cannot_attach_to_another_work_order(tmp_path):
    with pytest.raises(WellFormednessError, match="provider call"):
        _write_complete_trace(
            tmp_path,
            call_work_order_id="sha256:" + "9" * 64,
        )


def test_failed_control_append_rolls_live_materialization_back(tmp_path):
    harness = Harness(tmp_path)
    _initial, planned = _planned()
    before = harness.workflow_state.digest

    with pytest.raises(ValueError, match="work_enabled"):
        harness.record_control_transition(planned.decisions[0])

    assert harness.workflow_state.digest == before
    assert list(harness.log.read()) == []


def test_checkpoint_detects_deleted_final_authority_event(tmp_path):
    _write_complete_trace(tmp_path)
    log_path = tmp_path / "log.jsonl"
    lines = log_path.read_text(encoding="utf-8").splitlines()
    log_path.write_text("\n".join(lines[:-1]) + "\n", encoding="utf-8")

    with pytest.raises(ValueError, match="lost its checkpointed tail"):
        Harness(tmp_path)


def test_control_events_do_not_consume_legacy_capture_windows(tmp_path):
    harness = Harness(tmp_path)
    harness.record_measure(inputs=["gate:blocked", "candidate:a", "problem:a"])
    harness.record_measure(inputs=["neutral"])
    assert gate_block_count(harness, 2) == 1

    _initial, planned = _planned()
    harness.record_control_transition(
        planned.decisions[0],
        work_order=planned.work_orders[0],
    )

    assert gate_block_count(harness, 2) == 1


def test_checkpoint_verifies_its_prefix_when_newer_controls_exist(tmp_path):
    harness, *_rest = _write_complete_trace(tmp_path)
    profile = _profile()
    initial = WorkflowProcessStateV1.initial(
        manifest_digest=profile.manifest_digest,
        workflow_profile=profile.workflow_profile,
        formal_fence_seq=12,
        scratch_fence_seq=12,
    )
    later = plan_conjecture_batch(
        profile,
        state=initial,
        problem_ref="problem:later",
        canonical_problem_refs=("problem:later",),
        assignments=(
            ConjectureWorkAssignmentV1(
                school_id=None,
                route_lease=_route(),
                contract_id="conjecturer.legacy.v1",
                task_payload_schema_id="conjecture.semantic-ref.v1",
                task_payload_ref="problem:later",
                input_refs=("problem:later",),
            ),
        ),
    )
    harness.record_control_transition(
        later.decisions[0],
        work_order=later.work_orders[0],
    )

    log_path = tmp_path / "log.jsonl"
    rows = [json.loads(line) for line in log_path.read_text().splitlines()]
    checkpointed_guard = rows[4]
    rows[4] = {
        "seq": checkpointed_guard["seq"],
        "ts": checkpointed_guard["ts"],
        "rule": Rule.MEASURE.value,
        "inputs": ["replaced-checkpointed-control"],
        "outputs": [],
        "llm": None,
        "state_diff": checkpointed_guard["state_diff"],
    }
    log_path.write_text(
        "".join(
            json.dumps(row, sort_keys=True, separators=(",", ":")) + "\n"
            for row in rows
        ),
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="checkpoint differs"):
        Harness(tmp_path)
