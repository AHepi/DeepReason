"""Tranche-A autonomous simulation capability acceptance tests."""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

import pytest

from deepreason.bridge.retry import WorkflowRetryPolicyV1
from deepreason.capabilities.audit import write_tranche_a_audits
from deepreason.capabilities.evidence import attach_frozen_evidence
from deepreason.capabilities.enums import CapabilityLifecycle
from deepreason.capabilities.policy import (
    FrozenEvidenceItemV1,
    FrozenEvidencePolicyV1,
    SimulationCapabilityPolicyV1,
)
from deepreason.config import Config
from deepreason.harness import Harness, WellFormednessError
from deepreason.invariants import verify_root
from deepreason.llm.adapter import LLMAdapter
from deepreason.llm.endpoints import MockEndpoint
from deepreason.llm.firewall import ModelControlFieldError, leases_from_manifest
from deepreason.llm.wire import AliasTable, ConjecturerTurnWireContractV5
from deepreason.ontology import Problem, ProblemProvenance, Rule
from deepreason.rules.conj import conj
from deepreason.run_manifest import (
    ConjectureContextPolicyV1,
    ContractVersionPolicyV1,
    ControlPlanePolicyV1,
    SchoolExecutionPolicyV1,
    ToolchainEntry,
    bind_run_manifest,
    compile_run_manifest,
)

STAMP = "2026-07-16T00:00:00Z"


def _control() -> ControlPlanePolicyV1:
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
            conjecturer_turn_contract="conjecturer.turn.v5",
            control_event_schema="control.event.v1",
        ),
        capability_profile="conjecture-control.v1",
    )


def _toolchain() -> ToolchainEntry:
    version = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
    return ToolchainEntry(
        id="python@test-runtime",
        runner="local",
        executable=str(Path(sys.executable).resolve()),
        version_output_sha256=hashlib.sha256(version.encode()).hexdigest(),
        network=False,
    )


def _simulation_policy(**updates) -> SimulationCapabilityPolicyV1:
    values = {
        "enabled": True,
        "python_toolchain_identity": "python@test-runtime",
        "maximum_simulation_requests": 4,
        "maximum_simulation_executions": 4,
        "maximum_proposals_per_turn": 2,
        "maximum_generated_code_bytes": 16_384,
        "maximum_input_bytes": 16_384,
        "maximum_output_bytes": 16_384,
        "maximum_steps": 50_000,
        "maximum_samples": 32,
        "deterministic_seed_policy": "fixed_manifest",
        "fixed_seed_set": (7,),
        "maximum_follow_up_reasoning_turns": 4,
        "retry_ceiling": 0,
    }
    values.update(updates)
    return SimulationCapabilityPolicyV1(**values)


def _evidence() -> FrozenEvidencePolicyV1:
    content = "Synthetic bandwidth assumption: host-to-device is 12 GB/s."
    return FrozenEvidencePolicyV1(
        enabled=True,
        maximum_sources=1,
        maximum_excerpt_bytes_per_source=1_024,
        maximum_total_excerpt_bytes=1_024,
        items=(
            FrozenEvidenceItemV1(
                alias="E1",
                title="Frozen reference-machine assumption",
                source_locator="urn:deepreason:synthetic-machine",
                source_class="synthetic_assumption",
                content=content,
                content_sha256=hashlib.sha256(content.encode()).hexdigest(),
            ),
        ),
    )


def _manifest(*, policy=None, evidence=None, toolchain=None):
    config = Config(
        RETRY_MAX=0,
        roles={
            "conjecturer": {
                "endpoint_id": "conjecturer-0",
                "endpoint": "mock://conjecturer-0",
                "model": "offline-conjecturer",
                "provider": "mock",
                "family": "offline-family",
                "max_tokens": 1_024,
            }
        },
    )
    return config, compile_run_manifest(
        config,
        schema_version=5,
        workload_profile="text",
        rubric_policy="forbid",
        compiled_at=STAMP,
        control_plane_policy=_control(),
        toolchains=(toolchain or _toolchain(),),
        simulation_capability_policy=policy or _simulation_policy(),
        frozen_evidence_policy=evidence or _evidence(),
    )


def _run_scripted(tmp_path, *, config, manifest, responses, problem_id):
    root = tmp_path / problem_id
    bind_run_manifest(manifest, root)
    harness = Harness(root)
    problem = harness.register_problem(
        Problem(
            id=problem_id,
            description="Exercise one bounded simulation capability path.",
            provenance=ProblemProvenance.model_validate(
                {"trigger": "seed", "from": []}
            ),
        )
    )
    attach_frozen_evidence(harness, manifest, problem_id=problem.id)
    pending = [json.dumps(item) for item in responses]
    prompts = []

    def complete(prompt: str) -> str:
        prompts.append(prompt)
        return pending.pop(0)

    adapter = LLMAdapter(
        {
            "conjecturer": MockEndpoint(
                complete,
                name=manifest.roles["conjecturer"][0].base_url,
                model=manifest.roles["conjecturer"][0].model_id,
                max_tokens=1_024,
            )
        },
        harness.blobs,
        retry_max=0,
        model_profile=manifest.model_profile,
        leases=leases_from_manifest(manifest),
    )
    admitted = conj(
        harness,
        problem.id,
        adapter,
        config,
        workload_profile="text",
        run_manifest=manifest,
    )
    assert pending == []
    return harness, admitted, prompts


def _simulation_wire(**updates):
    proposal = {
        "request_identifier": "bandwidth-sensitivity",
        "hypothesis": "The scheduled transfer fits the declared bound.",
        "rival_predictions": ["x is below 10", "x is at least 10"],
        "discriminating_purpose": "Separate two live transfer predictions.",
        "declared_assumptions": ["The input is a synthetic schedule."],
        "parameter_definitions": [
            {"name": "one", "values_json": "{\"weight_bytes\":12}"}
        ],
        "model_source": (
            "def simulate(input_item, rng):\n"
            "    return {'x': input_item['parameters']['weight_bytes'] / 2}\n"
        ),
        "requested_observables": ["x"],
        "interpretation_conditions": ["x below 10 favors the first rival."],
    }
    proposal.update(updates)
    return {"simulation_proposals": [proposal]}


def test_v5_wire_allows_simulation_only_and_rejects_authority_fields():
    contract = ConjecturerTurnWireContractV5(
        reasoning=False,
        aliases=AliasTable(),
        maximum_simulation_proposals=1,
    )
    turn = contract.parse_compile(json.dumps(_simulation_wire()))
    assert turn.candidates == ()
    assert len(turn.simulation_proposals) == 1

    poisoned = _simulation_wire()
    poisoned["simulation_proposals"][0]["command"] = "python unsafe.py"
    with pytest.raises((ValueError, ModelControlFieldError)):
        contract.parse_compile(json.dumps(poisoned))


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("command", "python unsafe.py"),
        ("executable_path", "/usr/bin/python"),
        ("working_directory", "/tmp/work"),
        ("environment_variables", {"TOKEN": "secret"}),
        ("provider_route", "other-model"),
        ("token_budget", 100_000),
        ("execution_budget", 50),
        ("network_permissions", ["example.com"]),
        ("unrestricted_inputs", {"path": "/etc/passwd"}),
    ],
)
def test_v5_wire_rejects_model_authored_operational_authority(field, value):
    contract = ConjecturerTurnWireContractV5(
        reasoning=False,
        aliases=AliasTable(),
        maximum_simulation_proposals=1,
    )
    poisoned = _simulation_wire()
    poisoned["simulation_proposals"][0][field] = value
    with pytest.raises((ValueError, ModelControlFieldError)):
        contract.parse_compile(json.dumps(poisoned))


def test_v5_wire_rejects_malformed_input_alias():
    contract = ConjecturerTurnWireContractV5(
        reasoning=False,
        aliases=AliasTable(),
        maximum_simulation_proposals=1,
    )
    malformed = _simulation_wire(input_aliases=("../../outside",))
    with pytest.raises((ValueError, ModelControlFieldError)):
        contract.parse_compile(json.dumps(malformed))


def test_disabled_policy_is_the_v5_default_and_historical_v4_is_unchanged():
    policy = SimulationCapabilityPolicyV1()
    assert policy.enabled is False
    assert policy.maximum_simulation_requests == 0


def test_disabled_capability_records_validated_denial_and_closes_work(tmp_path):
    config, manifest = _manifest(
        policy=SimulationCapabilityPolicyV1(),
        evidence=FrozenEvidencePolicyV1(),
    )
    harness, admitted, _prompts = _run_scripted(
        tmp_path,
        config=config,
        manifest=manifest,
        responses=[_simulation_wire()],
        problem_id="pi-disabled-simulation-v5",
    )
    assert admitted == []
    lifecycles = [
        event.capability.lifecycle
        for event in harness.log.read()
        if event.capability is not None
    ]
    assert lifecycles == [
        CapabilityLifecycle.PROPOSED,
        CapabilityLifecycle.VALIDATED,
        CapabilityLifecycle.DENIED,
    ]
    final = harness.capability_state.transitions[
        harness.capability_state.current_transition_by_request[
            next(iter(harness.capability_state.proposals))
        ]
    ]
    assert final.reason_code == "capability_disabled"
    assert harness.workflow_state.outstanding_work_order_ids == ()
    assert verify_root(harness.root)["violations"] == []


def test_unavailable_frozen_runner_is_denied_before_execution(tmp_path):
    unavailable = _toolchain().model_copy(
        update={"executable": "/opt/deepreason-unavailable-python"}
    )
    config, manifest = _manifest(
        policy=_simulation_policy(),
        evidence=FrozenEvidencePolicyV1(),
        toolchain=unavailable,
    )
    harness, admitted, _prompts = _run_scripted(
        tmp_path,
        config=config,
        manifest=manifest,
        responses=[_simulation_wire()],
        problem_id="pi-unavailable-simulation-v5",
    )
    assert admitted == []
    assert harness.capability_state.execution_count == 0
    transition = harness.capability_state.transitions[
        next(iter(harness.capability_state.current_transition_by_request.values()))
    ]
    assert transition.lifecycle == CapabilityLifecycle.DENIED
    assert transition.reason_code == "runner_unavailable"
    assert verify_root(harness.root)["violations"] == []


def test_request_exhaustion_denies_second_proposal_and_duplicate_dispatch_fails_closed(
    tmp_path,
):
    policy = _simulation_policy(
        maximum_simulation_requests=1,
        maximum_simulation_executions=1,
        maximum_proposals_per_turn=2,
    )
    config, manifest = _manifest(
        policy=policy,
        evidence=FrozenEvidencePolicyV1(),
    )
    first = _simulation_wire()["simulation_proposals"][0]
    second = {**first, "request_identifier": "second-over-budget"}
    harness, admitted, _prompts = _run_scripted(
        tmp_path,
        config=config,
        manifest=manifest,
        responses=[
            {"simulation_proposals": [first, second]},
            {
                "abstention": {
                    "search_signal": "stuck",
                    "note": "The first result is recorded; no conjecture is responsible yet.",
                }
            },
        ],
        problem_id="pi-exhausted-simulation-v5",
    )
    assert admitted == []
    assert harness.capability_state.request_count == 2
    assert len(harness.capability_state.grants) == 1
    assert harness.capability_state.execution_count == 1
    denied = [
        item
        for item in harness.capability_state.transitions.values()
        if item.lifecycle == CapabilityLifecycle.DENIED
    ]
    assert len(denied) == 1
    assert denied[0].reason_code == "request_budget_exhausted"

    dispatched = next(
        item
        for item in harness.capability_state.transitions.values()
        if item.lifecycle == CapabilityLifecycle.DISPATCHED
    )
    before = harness.capability_state.digest
    with pytest.raises(WellFormednessError):
        harness.record_capability_transition(dispatched)
    assert harness.capability_state.digest == before
    assert verify_root(harness.root)["violations"] == []


def test_autonomous_simulation_creates_receipt_and_fresh_reasoning_work(tmp_path):
    config, manifest = _manifest()
    root = tmp_path / "run"
    bind_run_manifest(manifest, root)
    harness = Harness(root)
    problem = harness.register_problem(
        Problem(
            id="pi-simulation-v5",
            description="Discriminate a synthetic transfer schedule.",
            provenance=ProblemProvenance.model_validate(
                {"trigger": "seed", "from": []}
            ),
        )
    )
    attach_frozen_evidence(harness, manifest, problem_id=problem.id)
    responses = [
        json.dumps(_simulation_wire()),
        json.dumps(
            {
                "candidates": [
                    {
                        "content": "The recorded x=6 observation favors the first rival under the declared model only.",
                        "typicality": 0.4,
                        "neighbours": [],
                    }
                ]
            }
        ),
    ]
    prompts = []

    def complete(prompt: str) -> str:
        prompts.append(prompt)
        return responses.pop(0)

    endpoint = MockEndpoint(
        complete,
        name=manifest.roles["conjecturer"][0].base_url,
        model=manifest.roles["conjecturer"][0].model_id,
        max_tokens=1_024,
    )
    adapter = LLMAdapter(
        {"conjecturer": endpoint},
        harness.blobs,
        retry_max=0,
        model_profile=manifest.model_profile,
        leases=leases_from_manifest(manifest),
    )
    admitted = conj(
        harness,
        problem.id,
        adapter,
        config,
        workload_profile="text",
        run_manifest=manifest,
    )

    assert len(admitted) == 1
    assert len(prompts) == 2
    assert "FROZEN EVIDENCE DOSSIER" in prompts[0]
    assert "SIMULATION RESULT RECEIPT" in prompts[1]
    assert "recorded_observation" in prompts[1]
    state = harness.capability_state
    assert state.request_count == state.execution_count == state.consumption_count == 1
    lifecycles = [
        event.capability.lifecycle
        for event in harness.log.read()
        if event.rule == Rule.CAPABILITY
    ]
    assert lifecycles == [
        CapabilityLifecycle.PROPOSED,
        CapabilityLifecycle.VALIDATED,
        CapabilityLifecycle.GRANTED,
        CapabilityLifecycle.COMPILED,
        CapabilityLifecycle.DISPATCHED,
        CapabilityLifecycle.SUCCEEDED,
        CapabilityLifecycle.RESULT_PACKAGED,
        CapabilityLifecycle.CONSUMED,
    ]
    assert verify_root(root)["violations"] == []

    audit_paths = write_tranche_a_audits(root)
    assert set(audit_paths) == {
        "CAPABILITY_REQUEST_AUDIT.md",
        "REPLAY_VALIDATION.json",
        "RESEARCH_SOURCE_AUDIT.md",
        "SIMULATION_RESULTS.md",
        "THEORY_TEST_LINEAGE.md",
        "TOKEN_ACCOUNTING.json",
    }
    replay = json.loads((root / "REPLAY_VALIDATION.json").read_text())
    assert replay["valid"] is True
    accounting = json.loads((root / "TOKEN_ACCOUNTING.json").read_text())
    assert accounting["simulation_executions"] == 1
    assert accounting["preflight_provider_usage"]["usage_known"] is False
    assert accounting["embedding_usage"]["usage_known"] is False
    results = (root / "SIMULATION_RESULTS.md").read_text()
    assert '"network":false' in results
    lineage = (root / "THEORY_TEST_LINEAGE.md").read_text()
    assert "admitted formal candidate output(s)" in lineage


def test_unsafe_simulation_fails_operationally_but_is_reinjected(tmp_path):
    config, manifest = _manifest(evidence=FrozenEvidencePolicyV1())
    root = tmp_path / "failed"
    bind_run_manifest(manifest, root)
    harness = Harness(root)
    problem = harness.register_problem(
        Problem(
            id="pi-simulation-failure-v5",
            description="Preserve an operational simulation failure.",
            provenance=ProblemProvenance.model_validate(
                {"trigger": "seed", "from": []}
            ),
        )
    )
    bad = _simulation_wire(
        model_source="import os\ndef simulate(input_item, rng):\n    return {'x': 1}\n"
    )
    responses = [
        json.dumps(bad),
        json.dumps({"abstention": {"search_signal": "stuck", "note": "The operational failure does not refute the hypothesis."}}),
    ]
    prompts = []

    def complete(prompt: str) -> str:
        prompts.append(prompt)
        return responses.pop(0)

    adapter = LLMAdapter(
        {
            "conjecturer": MockEndpoint(
                complete,
                name=manifest.roles["conjecturer"][0].base_url,
                model=manifest.roles["conjecturer"][0].model_id,
                max_tokens=1_024,
            )
        },
        harness.blobs,
        retry_max=0,
        model_profile=manifest.model_profile,
        leases=leases_from_manifest(manifest),
    )
    assert conj(
        harness,
        problem.id,
        adapter,
        config,
        workload_profile="text",
        run_manifest=manifest,
    ) == []
    receipt = next(iter(harness.capability_state.receipts.values()))
    assert receipt.operational_status == "failed"
    assert receipt.final_backend_verdict == "fail"
    assert "does not refute the hypothesis" in prompts[1]
    assert verify_root(root)["violations"] == []


def test_missing_declared_observable_is_a_recorded_operational_failure(tmp_path):
    config, manifest = _manifest(evidence=FrozenEvidencePolicyV1())
    missing = _simulation_wire(
        model_source="def simulate(input_item, rng):\n    return {'y': 1}\n"
    )
    harness, admitted, prompts = _run_scripted(
        tmp_path,
        config=config,
        manifest=manifest,
        responses=[
            missing,
            {
                "abstention": {
                    "search_signal": "stuck",
                    "note": "The requested observable was absent, so no scientific conclusion follows.",
                }
            },
        ],
        problem_id="pi-missing-observable-v5",
    )
    assert admitted == []
    receipt = next(iter(harness.capability_state.receipts.values()))
    assert receipt.operational_status == "failed"
    diagnostics = harness.blobs.get(receipt.attempts[-1].diagnostics_ref).decode()
    assert "declared observable missing" in diagnostics
    assert "does not refute the hypothesis" in prompts[1]
    assert verify_root(harness.root)["violations"] == []


def test_oversized_output_is_bounded_and_reinjected_as_an_overrun(tmp_path):
    config, manifest = _manifest(
        policy=_simulation_policy(maximum_output_bytes=64),
        evidence=FrozenEvidencePolicyV1(),
    )
    oversized = _simulation_wire(
        model_source=(
            "def simulate(input_item, rng):\n"
            "    return {'x': 'z' * 1000}\n"
        )
    )
    harness, admitted, prompts = _run_scripted(
        tmp_path,
        config=config,
        manifest=manifest,
        responses=[
            oversized,
            {
                "abstention": {
                    "search_signal": "stuck",
                    "note": "The bounded output overran, so the hypothesis remains unresolved.",
                }
            },
        ],
        problem_id="pi-oversized-output-v5",
    )
    assert admitted == []
    receipt = next(iter(harness.capability_state.receipts.values()))
    attempt = receipt.attempts[-1]
    assert receipt.operational_status == "failed"
    assert receipt.final_backend_verdict == "overrun"
    assert receipt.output_truncated is True
    assert receipt.output_bytes <= 64
    assert len(harness.blobs.get(attempt.output_ref)) <= 64
    assert "does not refute the hypothesis" in prompts[1]
    assert verify_root(harness.root)["violations"] == []
