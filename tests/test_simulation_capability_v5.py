"""Offline acceptance tests for the autonomous Tranche-A capability loop."""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

import pytest

from deepreason.bridge.retry import WorkflowRetryPolicyV1
from deepreason.capabilities.audit import write_tranche_a_audits
from deepreason.capabilities.enums import CapabilityLifecycle
from deepreason.capabilities.policy import (
    AttachedEvidencePolicyV1,
    InquiryCapabilityPolicyV1,
    SimulationCapabilityPolicyV1,
)
from deepreason.config import Config
from deepreason.evidence import (
    AttachedSourceProvenanceV1,
    EvidenceDossierV1,
    RunInputManifestV1,
    RunInputProblemV1,
    attach_bound_evidence,
    bind_run_input,
    stage_attached_source,
)
from deepreason.harness import Harness, WellFormednessError
from deepreason.invariants import verify_root
from deepreason.llm.adapter import LLMAdapter, WorkflowAuthorizationError
from deepreason.llm.endpoints import MockEndpoint
from deepreason.llm.firewall import ModelControlFieldError, leases_from_manifest
from deepreason.llm.wire import AliasTable, ConjecturerTurnWireContractV5
from deepreason.ontology import Problem, ProblemProvenance, Rule
from deepreason.rules.conj import conj
from deepreason.run_manifest import (
    ConjectureContextPolicyV1,
    ContractVersionPolicyV2,
    ControlPlanePolicyV2,
    SchoolExecutionPolicyV1,
    ToolchainEntry,
    bind_run_manifest,
    compile_run_manifest,
)
from deepreason.scheduler.scheduler import Scheduler
from deepreason.workflow.models import TransitionKind
from deepreason.workflow.shadow import ConjectureShadowObserver
from deepreason.workflow.trace import ConjectureControlTrace


STAMP = "2026-07-16T00:00:00Z"
PROBLEM_ID = "pi-autonomous-simulation-v5"
PROBLEM_TEXT = "Exercise one bounded, model-proposed numerical simulation."


def _control() -> ControlPlanePolicyV2:
    return ControlPlanePolicyV2(
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
        contract_versions=ContractVersionPolicyV2(),
    )


def _toolchain(*, executable: str | None = None, runner: str = "local") -> ToolchainEntry:
    version = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
    return ToolchainEntry(
        id="python@test-runtime",
        runner=runner,
        executable=executable or str(Path(sys.executable).resolve()),
        version_output_sha256=hashlib.sha256(version.encode()).hexdigest(),
        network=False,
    )


def _simulation_policy(**updates) -> SimulationCapabilityPolicyV1:
    values = {
        "enabled": True,
        "runner_profile": "simulation.declarative.v1",
        "python_toolchain_identity": "python@test-runtime",
        "maximum_simulation_requests": 4,
        "maximum_simulation_executions": 4,
        "maximum_proposals_per_turn": 2,
        "maximum_generated_code_bytes": 16_384,
        "maximum_input_bytes": 16_384,
        "maximum_output_bytes": 16_384,
        "maximum_wall_ms": 10_000,
        "maximum_memory_bytes": 256 * 1024 * 1024,
        "maximum_steps": 50_000,
        "maximum_samples": 32,
        "deterministic_seed_policy": "fixed_manifest",
        "fixed_seed_set": (7,),
        "maximum_follow_up_reasoning_turns": 4,
        "retry_ceiling": 0,
    }
    values.update(updates)
    return SimulationCapabilityPolicyV1(**values)


def _config() -> Config:
    return Config(
        CONTROLLER=False,
        RETRY_MAX=0,
        N_SCHOOLS=0,
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


def _prepare_run(
    root: Path,
    *,
    policy: SimulationCapabilityPolicyV1 | None = None,
    toolchain: ToolchainEntry | None = None,
):
    policy = policy or _simulation_policy()
    provenance = AttachedSourceProvenanceV1(
        supplied_by="offline test fixture",
        acquisition_method="pre-freeze construction",
    )
    source = stage_attached_source(
        root,
        source_id="synthetic-machine",
        title="Frozen synthetic machine",
        source_locator="urn:deepreason:synthetic-machine",
        source_class="synthetic_assumption",
        media_type="text/plain",
        content="Host-to-GPU bandwidth is a frozen synthetic 12 GB/s.",
        provenance=provenance,
        declared_entities=("GPU",),
        declared_facets=("bandwidth",),
    )
    dossier = EvidenceDossierV1.create(
        problem_ref=PROBLEM_ID,
        sources=(source,),
        total_byte_count=source.byte_count,
        creation_provenance=provenance,
    )
    run_input = RunInputManifestV1.create(
        problem=RunInputProblemV1(id=PROBLEM_ID, description=PROBLEM_TEXT),
        evidence_dossier_digest=dossier.dossier_digest,
    )
    bind_run_input(run_input, dossier, root)
    evidence = AttachedEvidencePolicyV1(
        enabled=True,
        maximum_sources=1,
        maximum_total_bytes=4_096,
        maximum_excerpt_bytes_per_source=1_024,
        maximum_sources_per_pack=1,
    )
    capabilities = InquiryCapabilityPolicyV1(
        attached_evidence=evidence,
        simulation=policy,
    )
    config = _config()
    toolchains = () if not policy.enabled else (toolchain or _toolchain(),)
    manifest = compile_run_manifest(
        config,
        schema_version=5,
        workload_profile="text",
        rubric_policy="forbid",
        compiled_at=STAMP,
        control_plane_policy=_control(),
        inquiry_capability_policy=capabilities,
        run_input_digest=run_input.run_input_digest,
        toolchains=toolchains,
    )
    bind_run_manifest(manifest, root)
    harness = Harness(root)
    problem = harness.register_problem(
        Problem(
            id=PROBLEM_ID,
            description=PROBLEM_TEXT,
            provenance=ProblemProvenance.model_validate(
                {"trigger": "seed", "from": []}
            ),
        )
    )
    attach_bound_evidence(
        harness,
        run_input=run_input,
        dossier=dossier,
        problem_id=problem.id,
    )
    return config, manifest, harness


def _adapter(manifest, harness, responses, prompts):
    pending = [json.dumps(item) for item in responses]

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
    return adapter, pending


def _patch_production_adapter(monkeypatch, manifest, complete):
    def build_adapter(_config, blobs, *, meter=None, **_kwargs):
        return LLMAdapter(
            {
                "conjecturer": MockEndpoint(
                    complete,
                    name=manifest.roles["conjecturer"][0].base_url,
                    model=manifest.roles["conjecturer"][0].model_id,
                    max_tokens=1_024,
                )
            },
            blobs,
            meter=meter,
            retry_max=0,
            model_profile=manifest.model_profile,
            leases=leases_from_manifest(manifest),
        )

    monkeypatch.setattr("deepreason.llm.adapter.build_adapter", build_adapter)
    monkeypatch.setattr("deepreason.ops.make_embedder", lambda *_args: None)
    monkeypatch.setattr(
        "deepreason.ops.make_research_service", lambda *_args: None
    )


def _numeric_source(expression=None, *, observable="x") -> str:
    expression = expression or {
        "op": "div",
        "args": [
            {"input": "parameters.weight_bytes"},
            {"const": 2},
        ],
    }
    return json.dumps(
        {
            "schema": "declarative-numeric.v1",
            "observables": {observable: expression},
        }
    )


def _simulation_proposal(**updates):
    proposal = {
        "request_identifier": "bandwidth-sensitivity",
        "hypothesis": "The scheduled transfer fits the declared bound.",
        "rival_predictions": ["x is below 10", "x is at least 10"],
        "discriminating_purpose": "Separate two live transfer predictions.",
        "declared_assumptions": ["The input is a synthetic schedule."],
        "parameter_definitions": [
            {"name": "one", "values_json": "{\"weight_bytes\":12}"}
        ],
        "simulation_mode": "declarative_numeric_v1",
        "model_source": _numeric_source(),
        "requested_observables": ["x"],
        "interpretation_conditions": ["x below 10 favors the first rival."],
    }
    proposal.update(updates)
    return proposal


def _simulation_turn(*proposals):
    return {"simulation_proposals": list(proposals or (_simulation_proposal(),))}


def _initial_conjecture(harness, manifest, config, adapter):
    return conj(
        harness,
        PROBLEM_ID,
        adapter,
        config,
        workload_profile="text",
        run_manifest=manifest,
    )


def test_run_scheduler_initializes_v5_authority_before_provider_dispatch(
    tmp_path, monkeypatch
):
    """The production constructor seam must bind authority before cycle zero."""

    config, manifest, harness = _prepare_run(tmp_path / "production-authority")
    observed = {}
    original_authorize = ConjectureControlTrace.authorize_dispatch

    def observe_authorize(trace, reserved_tokens=0):
        observed["trace"] = trace
        result = original_authorize(trace, reserved_tokens)
        observed["authorized_before_provider"] = (
            trace.authoritative and trace.dispatch_authorized
        )
        return result

    monkeypatch.setattr(
        ConjectureControlTrace, "authorize_dispatch", observe_authorize
    )

    def complete(_prompt):
        # This callback is the provider boundary.  Both durable planning
        # transitions and the authoritative in-memory trace must predate it.
        assert observed["authorized_before_provider"] is True
        work_ids = tuple(harness.workflow_state.work_orders)
        assert len(work_ids) == 1
        work_id = work_ids[0]
        transition_kinds = set()
        for event in harness.log.read():
            if event.control is None:
                continue
            _schema, decision = harness.objects.get(
                event.control.decision_ref,
                schema="workflow-transition-decision",
            )
            if decision.work_order_id == work_id:
                transition_kinds.add(decision.transition_kind)
        assert {
            TransitionKind.WORK_ENABLED,
            TransitionKind.WORK_ISSUED,
        }.issubset(transition_kinds)
        observed["work_order_id"] = work_id
        return json.dumps(
            {
                "candidates": [
                    {
                        "content": "A production-path v5 authority candidate.",
                        "typicality": 0.4,
                        "neighbours": [],
                    }
                ]
            }
        )

    _patch_production_adapter(monkeypatch, manifest, complete)

    from deepreason.ops import run_scheduler

    run_scheduler(
        harness,
        config,
        cycles=1,
        token_budget=100_000,
        run_manifest=manifest,
    )

    work_id = observed["work_order_id"]
    work = harness.workflow_state.work_orders[work_id]
    assert work.workflow_profile == "inquiry.active.v1"
    assert work.contract_id == "conjecturer.turn.v5"
    assert observed["trace"].authoritative is True

    events = tuple(harness.log.read())
    controls = []
    for event in events:
        if event.control is None:
            continue
        _schema, decision = harness.objects.get(
            event.control.decision_ref,
            schema="workflow-transition-decision",
        )
        if decision.work_order_id == work_id:
            controls.append(decision.transition_kind)
    assert TransitionKind.WORK_ENABLED in controls
    assert TransitionKind.WORK_ISSUED in controls
    (provider_event,) = tuple(
        event
        for event in events
        if event.llm is not None and event.llm.role == "conjecturer"
    )
    assert provider_event.llm.work_order_id == work_id
    assert provider_event.llm.attempt_trace[-1].contract_id == work.contract_id
    assert any(event.rule == Rule.CONTROL for event in events)

    replayed = Harness(harness.root)
    assert replayed.workflow_state.digest == harness.workflow_state.digest
    assert replayed.workflow_state.outstanding_work_order_ids == ()
    assert verify_root(harness.root)["violations"] == []


def test_run_scheduler_fails_closed_when_v5_authority_is_genuinely_absent(
    tmp_path, monkeypatch
):
    config, manifest, harness = _prepare_run(tmp_path / "authority-absent")
    provider_calls = []

    def complete(_prompt):
        provider_calls.append("called")
        return json.dumps({"abstention": {"search_signal": "stuck"}})

    _patch_production_adapter(monkeypatch, manifest, complete)
    monkeypatch.setattr(
        ConjectureShadowObserver,
        "from_manifest",
        classmethod(lambda _cls, _manifest: None),
    )

    from deepreason.ops import run_scheduler

    with pytest.raises(
        WorkflowAuthorizationError,
        match="active conjecture control trace is unavailable",
    ):
        run_scheduler(
            harness,
            config,
            cycles=1,
            token_budget=100_000,
            run_manifest=manifest,
        )

    assert provider_calls == []
    assert not any(event.llm is not None for event in harness.log.read())


def test_v5_wire_allows_simulation_only_and_rejects_authority_fields():
    contract = ConjecturerTurnWireContractV5(
        reasoning=False,
        aliases=AliasTable(),
        maximum_simulation_proposals=1,
    )
    turn = contract.parse_compile(json.dumps(_simulation_turn()))
    assert turn.candidates == ()
    assert turn.simulation_proposals[0].simulation_mode == "declarative_numeric_v1"

    poisoned = _simulation_turn()
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
    poisoned = _simulation_turn()
    poisoned["simulation_proposals"][0][field] = value
    with pytest.raises((ValueError, ModelControlFieldError)):
        contract.parse_compile(json.dumps(poisoned))


def test_v5_wire_rejects_malformed_sealed_input_alias():
    contract = ConjecturerTurnWireContractV5(
        reasoning=False,
        aliases=AliasTable(),
        maximum_simulation_proposals=1,
    )
    poisoned = _simulation_turn(
        _simulation_proposal(input_aliases=["../../outside"])
    )
    with pytest.raises((ValueError, ModelControlFieldError)):
        contract.parse_compile(json.dumps(poisoned))


def test_conjecture_records_only_proposal_and_scheduler_executes_later(tmp_path):
    config, manifest, harness = _prepare_run(tmp_path / "separated")
    prompts = []
    adapter, pending = _adapter(
        manifest,
        harness,
        [
            _simulation_turn(),
            {
                "candidates": [
                    {
                        "content": (
                            "Under the exact recorded schedule, x=6 favors the "
                            "first rival; this remains a conditional negative bound."
                        ),
                        "typicality": 0.4,
                        "neighbours": [],
                    }
                ]
            },
        ],
        prompts,
    )

    assert _initial_conjecture(harness, manifest, config, adapter) == []
    assert len(pending) == 1
    state = harness.capability_state
    assert state.request_count == 1
    assert state.execution_count == 0
    transition = state.transitions[next(iter(state.current_transition_by_request.values()))]
    assert transition.lifecycle == CapabilityLifecycle.PROPOSED

    scheduler = Scheduler(
        harness,
        adapter,
        config,
        workload_profile="text",
        run_manifest=manifest,
    )
    scheduler.step()
    assert harness.capability_state.execution_count == 1
    assert len(pending) == 1
    scheduler.step()
    assert pending == []
    assert harness.capability_state.consumption_count == 1
    assert "FROZEN EVIDENCE DOSSIER" in prompts[0]
    assert "RECORDED SIMULATION OBSERVATION" in prompts[1]
    assert "recorded_observation" in prompts[1]
    assert any(
        "conditional negative bound" in artifact.content_ref
        for artifact in harness.state.artifacts.values()
    )

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
    assert verify_root(harness.root)["violations"] == []

    written = write_tranche_a_audits(harness.root)
    assert "CAPABILITY_REQUEST_AUDIT.md" in written
    assert "SIMULATION_RESULTS.md" in written
    replay = json.loads((harness.root / "REPLAY_VALIDATION.json").read_text())
    assert replay["valid"] is True


def test_disabled_capability_grants_no_model_facing_simulation_outcome():
    policy = SimulationCapabilityPolicyV1()
    assert policy.enabled is False
    contract = ConjecturerTurnWireContractV5(
        reasoning=False,
        aliases=AliasTable(),
        maximum_simulation_proposals=policy.maximum_proposals_per_turn,
    )
    with pytest.raises(ValueError, match="count exceeds"):
        contract.parse_compile(json.dumps(_simulation_turn()))


def test_unavailable_frozen_runner_is_denied_before_execution(tmp_path):
    config, manifest, harness = _prepare_run(
        tmp_path / "unavailable",
        toolchain=_toolchain(executable="/opt/deepreason-unavailable-python"),
    )
    prompts = []
    adapter, _pending = _adapter(manifest, harness, [_simulation_turn()], prompts)
    _initial_conjecture(harness, manifest, config, adapter)
    Scheduler(harness, adapter, config, workload_profile="text", run_manifest=manifest).step()

    transition = harness.capability_state.transitions[
        next(iter(harness.capability_state.current_transition_by_request.values()))
    ]
    assert transition.lifecycle == CapabilityLifecycle.DENIED
    assert transition.reason_code == "runner_unavailable"
    assert harness.capability_state.execution_count == 0
    assert verify_root(harness.root)["violations"] == []


def test_invalid_declarative_program_is_denied_without_dispatch(tmp_path):
    config, manifest, harness = _prepare_run(tmp_path / "invalid-program")
    proposal = _simulation_proposal(
        model_source=json.dumps(
            {
                "schema": "declarative-numeric.v1",
                "observables": {"x": {"op": "exec", "args": []}},
            }
        )
    )
    prompts = []
    adapter, _pending = _adapter(
        manifest, harness, [_simulation_turn(proposal)], prompts
    )
    _initial_conjecture(harness, manifest, config, adapter)
    Scheduler(
        harness,
        adapter,
        config,
        workload_profile="text",
        run_manifest=manifest,
    ).step()

    transition = harness.capability_state.transitions[
        next(iter(harness.capability_state.current_transition_by_request.values()))
    ]
    assert transition.lifecycle == CapabilityLifecycle.DENIED
    assert transition.reason_code == "invalid_model_program"
    assert not harness.capability_state.work_orders
    assert verify_root(harness.root)["violations"] == []


def test_request_exhaustion_denies_later_proposal_and_duplicate_dispatch_fails(tmp_path):
    policy = _simulation_policy(
        maximum_simulation_requests=1,
        maximum_simulation_executions=1,
        maximum_proposals_per_turn=2,
    )
    config, manifest, harness = _prepare_run(tmp_path / "exhausted", policy=policy)
    first = _simulation_proposal()
    second = _simulation_proposal(request_identifier="second-over-budget")
    prompts = []
    adapter, _pending = _adapter(
        manifest,
        harness,
        [_simulation_turn(first, second), {"abstention": {"search_signal": "stuck", "note": "First result consumed."}}],
        prompts,
    )
    _initial_conjecture(harness, manifest, config, adapter)
    scheduler = Scheduler(harness, adapter, config, workload_profile="text", run_manifest=manifest)
    scheduler.step()
    scheduler.step()  # follow up the first result before selecting later requests
    scheduler.step()

    assert harness.capability_state.request_count == 2
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
        harness.record_capability_transition(
            dispatched,
            phase_record=harness.capability_state.work_orders[
                dispatched.phase_record_ref
            ],
        )
    assert harness.capability_state.digest == before
    assert verify_root(harness.root)["violations"] == []


def test_sandboxed_python_has_no_host_fallback(tmp_path):
    policy = _simulation_policy(runner_profile="simulation.container.v1")
    config, manifest, harness = _prepare_run(
        tmp_path / "python-denied",
        policy=policy,
        toolchain=_toolchain(runner="container", executable="/pinned/container-python"),
    )
    proposal = _simulation_proposal(
        simulation_mode="sandboxed_python_v1",
        model_source="def simulate(inputs, rng):\n    return {'x': 1}\n",
    )
    prompts = []
    adapter, _pending = _adapter(manifest, harness, [_simulation_turn(proposal)], prompts)
    _initial_conjecture(harness, manifest, config, adapter)
    Scheduler(harness, adapter, config, workload_profile="text", run_manifest=manifest).step()

    transition = harness.capability_state.transitions[
        next(iter(harness.capability_state.current_transition_by_request.values()))
    ]
    assert transition.lifecycle == CapabilityLifecycle.DENIED
    assert transition.reason_code == "runner_unavailable"
    assert not harness.capability_state.compiled
    assert harness.capability_state.execution_count == 0
    assert verify_root(harness.root)["violations"] == []


def test_operational_failure_is_packaged_and_does_not_refute_hypothesis(tmp_path):
    config, manifest, harness = _prepare_run(tmp_path / "failed")
    divide_by_zero = _simulation_proposal(
        model_source=_numeric_source(
            {"op": "div", "args": [{"const": 1}, {"const": 0}]}
        )
    )
    prompts = []
    adapter, pending = _adapter(
        manifest,
        harness,
        [
            _simulation_turn(divide_by_zero),
            {
                "abstention": {
                    "search_signal": "stuck",
                    "note": "The operational failure does not refute the hypothesis.",
                }
            },
        ],
        prompts,
    )
    _initial_conjecture(harness, manifest, config, adapter)
    scheduler = Scheduler(harness, adapter, config, workload_profile="text", run_manifest=manifest)
    scheduler.step()
    receipt = next(iter(harness.capability_state.receipts.values()))
    assert receipt.operational_status == "failed"
    assert receipt.final_backend_verdict == "fail"
    scheduler.step()

    assert pending == []
    assert "does not refute the hypothesis" in prompts[1]
    assert harness.capability_state.consumption_count == 1
    assert verify_root(harness.root)["violations"] == []


def test_dispatched_crash_recovers_as_unknown_without_silent_rerun(
    tmp_path, monkeypatch
):
    config, manifest, harness = _prepare_run(tmp_path / "interrupted")
    prompts = []
    adapter, pending = _adapter(
        manifest,
        harness,
        [
            _simulation_turn(),
            {
                "abstention": {
                    "search_signal": "stuck",
                    "note": "The interrupted execution remains unknown.",
                }
            },
        ],
        prompts,
    )
    _initial_conjecture(harness, manifest, config, adapter)

    from deepreason.verification.simulation import SimulationBackend

    calls = []

    def process_died(_backend, _request, _blobs):
        calls.append("attempted")
        raise SystemExit("simulated process death")

    monkeypatch.setattr(SimulationBackend, "verify", process_died)
    scheduler = Scheduler(
        harness,
        adapter,
        config,
        workload_profile="text",
        run_manifest=manifest,
    )
    with pytest.raises(SystemExit, match="simulated process death"):
        scheduler.step()
    proposal = next(iter(harness.capability_state.proposals.values()))
    transition = harness.capability_state.transitions[
        harness.capability_state.current_transition_by_request[proposal.id]
    ]
    assert transition.lifecycle == CapabilityLifecycle.DISPATCHED
    assert not harness.capability_state.receipts

    monkeypatch.undo()
    scheduler = Scheduler(
        harness,
        adapter,
        config,
        workload_profile="text",
        run_manifest=manifest,
    )
    scheduler.step()
    receipt = next(iter(harness.capability_state.receipts.values()))
    assert receipt.execution_disposition == "dispatch_interrupted"
    assert receipt.operational_status == "failed"
    assert calls == ["attempted"]
    scheduler.step()

    assert pending == []
    assert "did not silently rerun" in prompts[1]
    assert harness.capability_state.consumption_count == 1
    assert verify_root(harness.root)["violations"] == []
