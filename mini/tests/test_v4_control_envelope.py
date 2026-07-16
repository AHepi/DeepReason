"""D0: Mini reuses the parent's opt-in conjecture authority envelope."""

from __future__ import annotations

import inspect
import json

from deepreason.bridge.retry import WorkflowRetryPolicyV1
from deepreason.config import Config
from deepreason.harness import Harness
from deepreason.invariants import verify_root
from deepreason.llm.firewall import route_from_endpoint
from deepreason.ontology import Rule
from deepreason.run_manifest import (
    ConjectureContextPolicyV1,
    ContractVersionPolicyV1,
    ControlPlanePolicyV1,
    SchoolExecutionPolicyV1,
    bind_run_manifest,
    compile_run_manifest,
)
from deepreason.workflow.models import ProposalReceiptV1, WorkOrderEnvelopeV1
from minireason.call import MockEndpoint
from minireason.loop import run


def _candidate() -> str:
    content = json.dumps(
        {
            "claim": "A compact mechanism remains open semantic text.",
            "mechanism": "A bounded feedback path could explain the effect.",
            "forbidden": [
                {"case": "the payload must be JSON", "eval": "program:json-wf"}
            ],
        }
    )
    return json.dumps(
        {"candidates": [{"content": content, "typicality": 0.37}]}
    )


def _shadow_policy() -> ControlPlanePolicyV1:
    return ControlPlanePolicyV1(
        controller_version="workflow.controller.v1",
        mode="shadow",
        workflow_profile="conjecture.shadow.v1",
        school_execution=SchoolExecutionPolicyV1(
            mode="conditioning_only",
            bindings=(),
            allow_shared=True,
            require_distinct_models=False,
            require_distinct_families=False,
        ),
        conjecture_context=ConjectureContextPolicyV1(
            mode="disabled",
            initial_max_blocks=0,
            initial_max_guides=0,
            max_context_expansion_requests=0,
            max_extra_blocks=0,
            permitted_retrieval_channels=(),
            coverage_slot_mandatory=False,
            exploration_slot_mandatory=False,
        ),
        workflow_retry=WorkflowRetryPolicyV1(),
        contract_versions=ContractVersionPolicyV1(
            bridge_ledger_wire_contract="bridge.ledger.v1",
            conjecturer_turn_contract="conjecturer.legacy.v1",
            control_event_schema="control.event.v1",
        ),
        capability_profile="conjecture-control.v1",
    )


def _bind_shadow_manifest(endpoint, root):
    config = Config(
        roles={"conjecturer": route_from_endpoint(endpoint).endpoint_spec()},
        model_profile="compact",
    )
    manifest = compile_run_manifest(
        config,
        engine_profile="mini",
        model_profile="compact",
        schema_version=4,
        workload_profile="text",
        rubric_policy="forbid",
        compiled_at="2026-07-16T00:00:00Z",
        control_plane_policy=_shadow_policy(),
    )
    bind_run_manifest(manifest, root)
    return manifest


def test_opt_in_mini_v4_uses_parent_work_order_and_receipt_types(tmp_path):
    endpoint = MockEndpoint(
        [_candidate()], name="mock://mini-v4", model="mini-v4-model"
    )
    root = tmp_path / "mini-v4"
    _bind_shadow_manifest(endpoint, root)

    summary = run(
        [("pi-mini-v4", "Why might this happen?")],
        endpoint,
        budget=100_000,
        root=root,
        vs_k=1,
        max_cycles=1,
    )

    replayed = Harness(root)
    workflow = replayed.workflow_state
    work, = workflow.work_orders.values()
    receipt, = workflow.proposal_receipts.values()
    assert isinstance(work, WorkOrderEnvelopeV1)
    assert isinstance(receipt, ProposalReceiptV1)
    assert work.workflow_profile == "conjecture.shadow.v1"
    assert work.school_id is None
    assert receipt.work_order_id == work.id
    assert receipt.source_call_seq < workflow.decision_event_seq[
        next(
            decision_id
            for decision_id, decision in workflow.decisions.items()
            if decision.transition_kind.value == "proposal_received"
        )
    ]
    call_events = [event for event in replayed.log.read() if event.llm is not None]
    assert len(call_events) == 1
    assert call_events[0].inputs[0] == "workflow-conjecture-call"
    assert call_events[0].llm.work_order_id == work.id
    assert any(event.rule == Rule.CONJ for event in replayed.log.read())
    assert summary["meter_equals_log"]
    assert verify_root(root)["violations"] == []


def test_mini_v4_repairs_are_authorized_before_the_next_provider_attempt(tmp_path):
    content = json.loads(_candidate())["candidates"][0]["content"]
    endpoint = MockEndpoint(
        [
            json.dumps(
                {"candidates": [{"content": content, "typicality": 2.0}]}
            ),
            _candidate(),
        ],
        name="mock://mini-v4-repair",
        model="mini-v4-model",
    )
    root = tmp_path / "mini-v4-repair"
    _bind_shadow_manifest(endpoint, root)

    run(
        [("pi-mini-v4-repair", "Why might this happen?")],
        endpoint,
        budget=100_000,
        root=root,
        vs_k=1,
        max_cycles=1,
    )

    harness = Harness(root)
    receipt, = harness.workflow_state.proposal_receipts.values()
    transitions = [
        decision.transition_kind.value
        for decision in harness.workflow_state.decisions.values()
    ]
    assert transitions.index("repair_requested") < transitions.index(
        "proposal_received"
    )
    assert receipt.validation_outcome.value == "valid_after_repair"
    assert receipt.attempt_count == 2
    assert verify_root(root)["violations"] == []


def test_mini_v4_schema_exhaustion_is_a_typed_failed_workflow_call(tmp_path):
    content = json.loads(_candidate())["candidates"][0]["content"]
    invalid = json.dumps(
        {"candidates": [{"content": content, "typicality": 2.0}]}
    )
    endpoint = MockEndpoint(
        [invalid, invalid, invalid],
        name="mock://mini-v4-exhausted",
        model="mini-v4-model",
    )
    root = tmp_path / "mini-v4-exhausted"
    _bind_shadow_manifest(endpoint, root)

    summary = run(
        [("pi-mini-v4-exhausted", "Why might this happen?")],
        endpoint,
        budget=100_000,
        root=root,
        vs_k=1,
        max_cycles=1,
    )

    harness = Harness(root)
    receipt, = harness.workflow_state.proposal_receipts.values()
    assert receipt.validation_outcome.value == "repair_exhausted"
    assert receipt.attempt_count == 3
    assert summary["meter_equals_log"]
    report = verify_root(root)
    assert report["violations"] == []
    assert report["stats"]["process"]["profile_totals"]["compact"][
        "schema_exhausted"
    ] == 1


def test_mini_client_does_not_implement_workflow_records_or_transitions():
    import minireason.loop as mini_loop

    source = inspect.getsource(mini_loop)
    for forbidden in (
        "WorkOrderEnvelopeV1",
        "ProposalReceiptV1",
        "TransitionDecisionV1",
        "record_control_transition",
    ):
        assert forbidden not in source
