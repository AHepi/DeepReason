"""Offline derived Jolt acceptance without mutating the recorded inquiry."""

from __future__ import annotations

import json
from pathlib import Path

from deepreason.bridge.events import BridgeAction
from deepreason.bridge.retry import WorkflowRetryPolicyV1
from deepreason.config import Config
from deepreason.harness import Harness
from deepreason.invariants import verify_root
from deepreason.llm.adapter import LLMAdapter
from deepreason.llm.endpoints import MockEndpoint
from deepreason.llm.firewall import leases_from_manifest
from deepreason.ontology import Problem, ProblemProvenance, Provenance
from deepreason.run_manifest import (
    ConjectureContextPolicyV1,
    ContractVersionPolicyV1,
    ControlPlanePolicyV1,
    SchoolExecutionPolicyV1,
    bind_run_manifest,
    compile_run_manifest,
)
from deepreason.scratch.attention import AttentionPlanner, AttentionRequestV1
from deepreason.scratch.models import ScratchProvenanceV1
from deepreason.scratch.service import ScratchService


FIXTURE = (
    Path(__file__).parent / "fixtures" / "jolt_derived_acceptance.json"
)
STAMP = "2026-07-16T00:00:00Z"


def _route() -> dict:
    return {
        "endpoint_id": "jolt-derived-route",
        "endpoint": "mock://jolt-derived",
        "model": "jolt-derived-offline",
        "provider": "mock",
        "family": "jolt-derived",
        "output_mechanism": "json_text",
        "max_tokens": 512,
    }


def _control_policy() -> ControlPlanePolicyV1:
    return ControlPlanePolicyV1(
        controller_version="workflow.controller.v1",
        mode="active_conjecture",
        workflow_profile="conjecture.active.v1",
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
            bridge_ledger_wire_contract="bridge.ledger.v2",
            conjecturer_turn_contract="conjecturer.turn.v4",
            control_event_schema="control.event.v1",
        ),
        capability_profile="conjecture-control.v1",
    )


def _manifest():
    config = Config(
        model_profile="compact",
        scratchpad={
            "enabled": True,
            "max_blocks_per_pack": 2,
            "max_guides_per_pack": 0,
            "semantic_retrieval": False,
            "coverage_slot_every_n_packs": 8,
        },
        bridge={
            "mode": "grounded_two_stage",
            "grounding_review": False,
            "max_schema_repair_attempts": 2,
            "max_grounding_repair_attempts": 0,
            "output_section_limit": 4,
        },
        roles={
            "conjecturer": _route(),
            "summarizer": _route(),
            "thesis": _route(),
        },
    )
    return compile_run_manifest(
        config,
        schema_version=4,
        workload_profile="text",
        rubric_policy="forbid",
        compiled_at=STAMP,
        control_plane_policy=_control_policy(),
    )


def test_derived_jolt_v2_repair_reaches_stage_b_and_verifies_cleanly(tmp_path):
    fixture = json.loads(FIXTURE.read_text(encoding="utf-8"))
    original = Path(__file__).parents[1] / fixture["source_root"]
    original_before = {
        path.relative_to(original): path.read_bytes()
        for path in original.rglob("*")
        if path.is_file()
    }

    root = tmp_path / "jolt-derived-acceptance"
    harness = Harness(root)
    manifest = _manifest()
    bind_run_manifest(manifest, root)
    problem_id = "problem-jolt-derived"
    harness.register_problem(
        Problem(
            id=problem_id,
            description="What does the bounded Jolt-derived record establish?",
            provenance=ProblemProvenance(trigger="seed", **{"from": []}),
        )
    )
    artifact = harness.create_artifact(
        "A surviving formal proposal remains conjectural.",
        problem_id=problem_id,
        provenance=Provenance(role="conjecturer"),
    )
    scratch = ScratchService(harness)
    block = scratch.create_block(
        {"content": "A provisional Jolt note remains advisory."},
        ScratchProvenanceV1(actor="user", origin="jolt-derived-fixture"),
    )
    pack = AttentionPlanner(
        scratch,
        manifest.scratch_policy.attention_policy(),
    ).plan(
        AttentionRequestV1(
            focus_blocks=[block.id],
            maximum_blocks=1,
            maximum_cluster_guides=0,
            include_nearby=False,
            include_recent=False,
            include_loose=False,
            include_dormant=False,
            include_underexposed=False,
            include_exploratory=False,
            deterministic_seed=17,
        )
    )

    stage_a = MockEndpoint(
        [json.dumps(value) for value in fixture["stage_a_attempts"]],
        name="mock://jolt-derived",
        model="jolt-derived-offline",
    )
    stage_b = MockEndpoint(
        [json.dumps(fixture["stage_b_output"])],
        name="mock://jolt-derived",
        model="jolt-derived-offline",
    )
    adapter = LLMAdapter(
        {"summarizer": stage_a, "thesis": stage_b},
        harness.blobs,
        retry_max=2,
        model_profile="compact",
        output_mechanism="json_text",
        leases=leases_from_manifest(manifest),
    )
    supplied_policy = manifest.bridge_policy.workflow_policy(
        ledger_contract_version="v1"
    )
    terminal = harness.build_bridge(
        problem_id,
        "answer",
        supplied_policy,
        run_manifest_digest=manifest.sha256,
        stage_a_adapter=adapter,
        composition_adapter=adapter,
        attention_pack=pack,
    )

    assert terminal.process_status == "success", (
        terminal.error_code,
        terminal.error_message,
    )
    assert terminal.resolution.value == fixture["expected"]["resolution"]
    assert stage_a.last_transport_attempts == 1
    assert stage_b.last_transport_attempts == 1
    events = tuple(harness.log.read())
    ledger_event = next(
        event
        for event in events
        if event.bridge is not None
        and event.bridge.action == BridgeAction.LEDGER_CREATED
    )
    assert ledger_event.llm.attempt_trace[-1].contract_id == fixture["expected"][
        "ledger_contract"
    ]
    assert [attempt.valid for attempt in ledger_event.llm.attempt_trace] == fixture[
        "expected"
    ]["stage_a_attempt_validity"]
    validation_event = next(
        event
        for event in events
        if event.bridge is not None
        and event.bridge.action == BridgeAction.LEDGER_VALIDATED
    )
    composition_event = next(
        event
        for event in events
        if event.bridge is not None
        and event.bridge.action == BridgeAction.OUTPUT_COMPOSED
    )
    assert validation_event.seq < composition_event.seq
    ledger = harness.bridge_state.ledgers[terminal.claim_ledger_id]
    entry, = ledger.entries
    assert entry.formal_artifact_refs == [artifact.id]
    assert entry.scratch_refs == [block.id]
    report = verify_root(root)
    assert len(report["violations"]) == fixture["expected"][
        "verify_root_violations"
    ]
    assert {
        path.relative_to(original): path.read_bytes()
        for path in original.rglob("*")
        if path.is_file()
    } == original_before
