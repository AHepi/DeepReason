"""C4 local repair is scope-limited and durably authorized per attempt."""

from __future__ import annotations

import json

import pytest
from pydantic import BaseModel, ConfigDict, model_validator

from deepreason.control_events import ControlEventPayloadV1
from deepreason.harness import Harness
from deepreason.llm.adapter import LLMAdapter, SchemaRepairError
from deepreason.llm.contracts import ConjecturerOutput
from deepreason.llm.endpoints import MockEndpoint
from deepreason.workflow.models import RepairWorkOrderV1, TransitionKind
from deepreason.workflow.replay import WorkflowRecoveryStatus

from tests.test_workflow_shadow_c0 import _run


def test_whole_object_repair_cannot_change_an_unrelated_field(tmp_path):
    endpoint = MockEndpoint(
        [
            '{"candidates":[{"content":"keep","typicality":2}]}',
            '{"candidates":[{"content":"replace","typicality":0.5}]}',
            "0.4",
        ]
    )
    harness = Harness(tmp_path / "scoped-diff")
    output, call = LLMAdapter(
        {"conjecturer": endpoint},
        harness.blobs,
        retry_max=2,
    ).call(
        "conjecturer",
        "PACK",
        ConjecturerOutput,
        repair_scope_required=True,
    )

    assert output.candidates[0].content == "keep"
    assert output.candidates[0].typicality == 0.4
    assert [attempt.valid for attempt in call.attempt_trace] == [False, False, True]
    rejected_repair = call.attempt_trace[1]
    assert rejected_repair.validation_path == "/candidates/0/content"
    assert rejected_repair.repair_scope == "/candidates/0/typicality"
    diagnostic = json.loads(harness.blobs.get(rejected_repair.diagnostic_ref))
    assert diagnostic["error"] == (
        "repair changed JSON outside its authorized subtree"
    )


class _RootCheckedOutput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    left: int
    right: int

    @model_validator(mode="after")
    def _values_match(self):
        if self.left != self.right:
            raise ValueError("values must match")
        return self


def test_root_repair_is_only_open_when_no_parseable_baseline_exists(tmp_path):
    syntax_endpoint = MockEndpoint(['{broken', '{"left":1,"right":1}'])
    fixed, syntax_call = LLMAdapter(
        {"conjecturer": syntax_endpoint},
        Harness(tmp_path / "syntax").blobs,
        retry_max=1,
    ).call(
        "conjecturer",
        "PACK",
        _RootCheckedOutput,
        repair_scope_required=True,
    )
    assert fixed.left == fixed.right == 1
    assert [attempt.valid for attempt in syntax_call.attempt_trace] == [False, True]

    harness = Harness(tmp_path / "parseable-root")
    parseable_endpoint = MockEndpoint(
        ['{"left":1,"right":2}', '{"left":2,"right":2}']
    )
    with pytest.raises(SchemaRepairError) as raised:
        LLMAdapter(
            {"conjecturer": parseable_endpoint},
            harness.blobs,
            retry_max=1,
        ).call(
            "conjecturer",
            "PACK",
            _RootCheckedOutput,
            repair_scope_required=True,
        )
    final = raised.value.spend.attempt_trace[-1]
    diagnostic = json.loads(harness.blobs.get(final.diagnostic_ref))
    assert diagnostic["repair_scope"] == ""
    assert diagnostic["error"] == (
        "repair changed JSON outside its authorized subtree"
    )


def _active_repair_run(tmp_path, responses: tuple[str, ...]):
    return _run(
        tmp_path,
        "active_conjecture",
        responses=responses,
        retry_max=1,
    )


def _control_decision(harness: Harness, event):
    return harness.objects.get(
        event.control.decision_ref,
        schema="workflow-transition-decision",
    )[1]


def test_active_repair_work_order_binds_the_exact_rejected_attempt(tmp_path):
    capture = _active_repair_run(
        tmp_path / "active-repair",
        (
            '{"candidates":[{"content":"keep","typicality":2}]}',
            '{"candidates":[{"content":"keep","typicality":0.5}]}',
        ),
    )
    events = tuple(capture.harness.log.read())
    repair_event = next(
        event
        for event in events
        if event.control is not None
        and _control_decision(capture.harness, event).transition_kind
        == TransitionKind.REPAIR_REQUESTED
    )
    provider_event = next(event for event in events if event.llm is not None)
    rejected = provider_event.llm.attempt_trace[0]
    repair_refs = [
        object_id
        for object_id in repair_event.outputs
        if capture.harness.objects.get(object_id)[0]
        == "workflow-repair-work-order"
    ]
    assert len(repair_refs) == 1
    repair = capture.harness.objects.get(
        repair_refs[0], schema="workflow-repair-work-order"
    )[1]
    work = capture.harness.workflow_state.work_orders[repair.parent_work_order_id]

    assert repair.attempt == 1
    assert repair.rejected_prompt_ref == rejected.prompt_ref
    assert repair.rejected_raw_ref == rejected.raw_ref
    assert repair.rejected_diagnostic_ref == rejected.diagnostic_ref
    assert repair.validation_pointer == rejected.validation_path
    assert repair.authorized_subtree_pointer == rejected.repair_scope
    assert repair.remaining_local_attempts == 1
    assert repair.contract_id == work.contract_id
    assert repair.route_lease == work.route_lease
    assert repair.formal_fence_seq == work.formal_fence_seq
    assert repair.scratch_fence_seq == work.scratch_fence_seq
    assert repair.repair_policy_ref == work.repair_policy_ref

    reopened = Harness(capture.harness.root)
    assert reopened.workflow_state.repair_work_orders == {
        repair.id: repair
    }
    prefix = Harness.at(capture.harness.root, repair_event.seq)
    assert prefix.workflow_state.recovery_status(
        work.id
    ) == WorkflowRecoveryStatus.REPAIR_PENDING


def test_replay_rejects_forged_repair_lineage_at_provider_settlement(tmp_path):
    capture = _active_repair_run(
        tmp_path / "forged-lineage",
        (
            '{"candidates":[{"content":"keep","typicality":2}]}',
            '{"candidates":[{"content":"keep","typicality":0.5}]}',
        ),
    )
    events = tuple(capture.harness.log.read())
    repair_event = next(
        event
        for event in events
        if event.control is not None
        and _control_decision(capture.harness, event).transition_kind
        == TransitionKind.REPAIR_REQUESTED
    )
    decision = _control_decision(capture.harness, repair_event)
    repair_id = next(
        object_id
        for object_id in repair_event.outputs
        if capture.harness.objects.get(object_id)[0]
        == "workflow-repair-work-order"
    )
    repair = capture.harness.objects.get(
        repair_id, schema="workflow-repair-work-order"
    )[1]
    forged_values = repair.model_dump(
        mode="python", by_alias=True, exclude={"id"}
    )
    forged_values["rejected_raw_ref"] = "forged-rejected-raw"
    forged = RepairWorkOrderV1.create(**forged_values)
    forged_payload = ControlEventPayloadV1(
        decision_ref=decision.id,
        inputs=repair_event.inputs,
        outputs=(forged.id, decision.id),
    )
    forged_event = repair_event.model_copy(
        update={"control": forged_payload, "outputs": (forged.id, decision.id)}
    )

    replay = Harness.at(capture.harness.root, repair_event.seq - 1).workflow_state
    replay.apply(
        forged_event,
        (
            ("workflow-repair-work-order", forged.id, forged),
            ("workflow-transition-decision", decision.id, decision),
        ),
    )
    provider_event = next(
        event for event in events if event.seq > repair_event.seq and event.llm
    )
    replay.observe_event(provider_event)
    proposal_event = next(
        event
        for event in events
        if event.seq > provider_event.seq and event.control is not None
    )
    proposal_records = tuple(
        (
            *capture.harness.objects.get(object_id),
        )
        for object_id in proposal_event.outputs
    )
    # Replay records are ordered as (schema, id, value), not (schema, value).
    proposal_records = tuple(
        (schema, object_id, value)
        for object_id, (schema, value) in zip(
            proposal_event.outputs,
            proposal_records,
            strict=True,
        )
    )
    with pytest.raises(ValueError, match="rejected provider attempt"):
        replay.apply(proposal_event, proposal_records)


def test_active_repair_exhaustion_is_emitted_once(tmp_path):
    capture = _active_repair_run(
        tmp_path / "exhausted",
        ("{invalid-initial", "{invalid-repair"),
    )
    transitions = [
        _control_decision(capture.harness, event).transition_kind
        for event in capture.harness.log.read()
        if event.control is not None
    ]
    assert transitions.count(TransitionKind.REPAIR_REQUESTED) == 1
    assert transitions.count(TransitionKind.REPAIR_EXHAUSTED) == 1
    (work_id,) = tuple(capture.harness.workflow_state.work_orders)
    assert capture.harness.workflow_state.recovery_status(
        work_id
    ) == WorkflowRecoveryStatus.FINISHED
