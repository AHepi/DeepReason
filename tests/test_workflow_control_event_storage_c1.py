"""C1 workflow authority records have typed, compatibility-safe persistence."""

from __future__ import annotations

import json

import pytest
from pydantic import ValidationError

from deepreason.control_events import ControlEventPayloadV1
from deepreason.ontology import (
    ControlEventPayloadV1 as ExportedControlEventPayloadV1,
    Event,
    LLMCall,
    Rule,
    StateDiff,
)
from deepreason.run_manifest import ConjectureContextPolicyV1
from deepreason.storage.objects import ObjectStore
from deepreason.workflow.events import ConjectureWorkAssignmentV1
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
from deepreason.workflow.reducer import plan_conjecture_batch
from deepreason.workflow.state import WorkflowProcessStateV1


def _route() -> RouteLeaseRefV1:
    return RouteLeaseRefV1(
        seat=0,
        endpoint_id="conjecturer-c1",
        route_sha256="a" * 64,
    )


def test_control_payload_has_a_cycle_free_public_export():
    assert ExportedControlEventPayloadV1 is ControlEventPayloadV1


def _records():
    repair = LocalRepairPolicyV1.create(max_schema_repairs=0, scopes=())
    profile = ConjectureWorkflowProfileV1(
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
        repair_policy=repair,
    )
    initial = WorkflowProcessStateV1.initial(
        manifest_digest=profile.manifest_digest,
        workflow_profile=profile.workflow_profile,
        formal_fence_seq=4,
        scratch_fence_seq=4,
    )
    reduction = plan_conjecture_batch(
        profile,
        state=initial,
        problem_ref="problem:c1-control",
        assignments=(
            ConjectureWorkAssignmentV1(
                route_lease=_route(),
                contract_id=profile.conjecturer_contract_id,
                reserved_tokens=64,
                task_payload_schema_id="semantic.conjecture.open.v1",
                task_payload_ref="problem:c1-control",
                input_refs=("problem:c1-control",),
            ),
        ),
        canonical_problem_refs=("problem:c1-control",),
    )
    work_order = reduction.work_orders[0]
    decision = reduction.decisions[0]
    candidate_ref = "sha256:" + "c" * 64
    proposal = ProposalReceiptV1.create(
        work_order_id=work_order.id,
        source_call_seq=9,
        prompt_ref="prompt:c1",
        raw_ref="raw:c1",
        contract_id=work_order.contract_id,
        route_lease=work_order.route_lease,
        validation_outcome=ProposalValidationOutcome.VALID_FIRST_ATTEMPT,
        attempt_count=1,
        candidate_payload_refs=(candidate_ref,),
        tokens=23,
    )
    finding = GuardFindingV1(
        candidate_ref=candidate_ref,
        outcome=GuardFindingOutcome.ADMIT,
        code=GuardFindingCode.PASSED,
    )
    guard = GuardResultV1.create(
        work_order_id=work_order.id,
        proposal_receipt_id=proposal.id,
        findings=(finding,),
        admitted_refs=(candidate_ref,),
    )
    return {
        "workflow-work-order": work_order,
        "workflow-proposal-receipt": proposal,
        "workflow-guard-result": guard,
        "workflow-transition-decision": decision,
    }


@pytest.mark.parametrize("schema", sorted(_records()))
def test_every_workflow_record_round_trips_through_shared_store(tmp_path, schema):
    store = ObjectStore(tmp_path / "objects")
    record = _records()[schema]

    store.put(schema, record)

    assert store.get(record.id, schema=schema) == (schema, record)


def test_workflow_storage_omits_absent_optional_fields(tmp_path):
    store = ObjectStore(tmp_path / "objects")
    records = _records()
    for schema, record in records.items():
        store.put(schema, record)

    work = json.loads(
        store._schema_path(
            "workflow-work-order", records["workflow-work-order"].id
        ).read_text()
    )["data"]
    proposal = json.loads(
        store._schema_path(
            "workflow-proposal-receipt",
            records["workflow-proposal-receipt"].id,
        ).read_text()
    )["data"]
    decision = json.loads(
        store._schema_path(
            "workflow-transition-decision",
            records["workflow-transition-decision"].id,
        ).read_text()
    )["data"]

    assert "advisory_context_ref" not in work
    assert "task_payload_value" not in work
    assert "context_request_hash" not in proposal
    assert "abstention_hash" not in proposal
    assert "guard_result_ref" not in decision


def test_control_event_has_one_exact_typed_authority_envelope():
    records = _records()
    work = records["workflow-work-order"]
    decision = records["workflow-transition-decision"]
    inputs = [work.id, decision.trigger_ref]
    outputs = [work.id, decision.id]
    payload = ControlEventPayloadV1(
        decision_ref=decision.id,
        inputs=inputs,
        outputs=outputs,
    )

    event = Event(
        seq=10,
        ts="2026-07-16T00:00:00Z",
        rule=Rule.CONTROL,
        inputs=inputs,
        outputs=outputs,
        control=payload,
    )

    assert event.control == payload
    assert event.outputs[-1] == decision.id
    assert not any(event.state_diff.model_dump(mode="json", by_alias=True).values())
    assert '"schema":"control.event.v1"' in event.model_dump_json(by_alias=True)


def test_control_event_deeply_revalidates_preconstructed_payloads():
    records = _records()
    work = records["workflow-work-order"]
    decision = records["workflow-transition-decision"]
    payload = ControlEventPayloadV1(
        decision_ref=decision.id,
        inputs=[work.id, decision.trigger_ref],
        outputs=[work.id, decision.id],
    )

    forged_schema = payload.model_copy(update={"schema_": "forged"})
    with pytest.raises(ValidationError, match="control.event.v1"):
        Event(
            seq=10,
            ts="2026-07-16T00:00:00Z",
            rule=Rule.CONTROL,
            inputs=list(payload.inputs),
            outputs=list(payload.outputs),
            control=forged_schema,
        )

    copied_sequences = payload.model_copy(
        update={
            "inputs": list(payload.inputs),
            "outputs": list(payload.outputs),
        }
    )
    event = Event(
        seq=10,
        ts="2026-07-16T00:00:00Z",
        rule=Rule.CONTROL,
        inputs=list(payload.inputs),
        outputs=list(payload.outputs),
        control=copied_sequences,
    )
    with pytest.raises(TypeError, match="immutable"):
        event.control.inputs.append("forged")


def test_control_event_rejects_mismatched_refs_llm_and_formal_state():
    records = _records()
    work = records["workflow-work-order"]
    decision = records["workflow-transition-decision"]
    payload = ControlEventPayloadV1(
        decision_ref=decision.id,
        inputs=[work.id, decision.trigger_ref],
        outputs=[work.id, decision.id],
    )
    values = {
        "seq": 10,
        "ts": "2026-07-16T00:00:00Z",
        "rule": Rule.CONTROL,
        "inputs": list(payload.inputs),
        "outputs": list(payload.outputs),
        "control": payload,
    }

    with pytest.raises(ValidationError, match="inputs must match"):
        Event(**{**values, "inputs": [work.id, "another-trigger"]})
    with pytest.raises(ValidationError, match="outputs must match"):
        Event(**{**values, "outputs": [decision.id]})
    with pytest.raises(ValidationError, match="cannot contain an LLM call"):
        Event(
            **values,
            llm=LLMCall(
                role="conjecturer",
                model="fixture",
                endpoint="fixture://c1",
                prompt_ref="prompt",
                raw_ref="raw",
                work_order_id=work.id,
            ),
        )
    with pytest.raises(ValidationError, match="formal StateDiff"):
        Event(**values, state_diff=StateDiff(hv_set={"artifact": 0.1}))


def test_control_payload_rejects_noncanonical_or_ambiguous_decision_refs():
    records = _records()
    work = records["workflow-work-order"]
    decision = records["workflow-transition-decision"]

    with pytest.raises(ValidationError, match="final event output"):
        ControlEventPayloadV1(
            decision_ref=decision.id,
            inputs=[work.id, decision.trigger_ref],
            outputs=[decision.id, work.id],
        )
    with pytest.raises(ValidationError, match="duplicate object IDs"):
        ControlEventPayloadV1(
            decision_ref=decision.id,
            inputs=[work.id, decision.trigger_ref],
            outputs=[decision.id, decision.id],
        )
    with pytest.raises(ValidationError, match="canonical work order"):
        ControlEventPayloadV1(
            decision_ref=decision.id,
            inputs=["work-order:forged", decision.trigger_ref],
            outputs=[decision.id],
        )


def test_control_rule_and_payload_must_appear_together():
    records = _records()
    work = records["workflow-work-order"]
    decision = records["workflow-transition-decision"]
    payload = ControlEventPayloadV1(
        decision_ref=decision.id,
        inputs=[work.id, decision.trigger_ref],
        outputs=[work.id, decision.id],
    )

    with pytest.raises(ValidationError, match="Control rule"):
        Event(seq=0, ts="legacy", rule=Rule.CONTROL)
    with pytest.raises(ValidationError, match="Control rule"):
        Event(
            seq=0,
            ts="legacy",
            rule=Rule.MEASURE,
            inputs=list(payload.inputs),
            outputs=list(payload.outputs),
            control=payload,
        )


def test_work_order_call_binding_is_conjecturer_only_and_legacy_shape_is_unchanged():
    work = _records()["workflow-work-order"]
    legacy_call = LLMCall(
        role="critic",
        model="fixture",
        endpoint="fixture://legacy",
        prompt_ref="prompt",
        raw_ref="raw",
    )
    legacy_event = Event(seq=0, ts="legacy", rule=Rule.MEASURE, llm=legacy_call)

    assert "work_order_id" not in legacy_call.model_dump(mode="json")
    assert '"control"' not in legacy_event.model_dump_json(by_alias=True)

    bound = LLMCall(
        role="conjecturer",
        model="fixture",
        endpoint="fixture://c1",
        prompt_ref="prompt",
        raw_ref="raw",
        work_order_id=work.id,
    )
    assert bound.model_dump(mode="json")["work_order_id"] == work.id

    with pytest.raises(ValidationError, match="only conjecturer"):
        LLMCall(
            role="critic",
            model="fixture",
            endpoint="fixture://c1",
            prompt_ref="prompt",
            raw_ref="raw",
            work_order_id=work.id,
        )
    with pytest.raises(ValidationError, match="string_pattern_mismatch"):
        LLMCall(
            role="conjecturer",
            model="fixture",
            endpoint="fixture://c1",
            prompt_ref="prompt",
            raw_ref="raw",
            work_order_id="work-order:forged",
        )

    forged_nested = bound.model_copy(
        update={"work_order_id": "work-order:forged"}
    )
    with pytest.raises(ValidationError, match="string_pattern_mismatch"):
        Event(
            seq=1,
            ts="legacy",
            rule=Rule.MEASURE,
            llm=forged_nested,
        )
