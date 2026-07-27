"""V6 freezes complete criterion definitions while v5 retains ID-only inputs."""

from __future__ import annotations

import json

import pytest

from deepreason.application import (
    ContinueTextRunIntentV1,
    InspectTextRunIntentV1,
    RunBudgetIntentV1,
    StartTextRunIntentV1,
)
from deepreason.application.text_runs import (
    TextRunApplicationService,
    TextRunWorkerRegistry,
)
from deepreason.bridge.retry import WorkflowRetryPolicyV1
from deepreason.config import Config
from deepreason.evidence import (
    AttachedSourceProvenanceV1,
    EvidenceDossierV1,
    RunInputManifestV1,
    RunInputManifestV2,
    RunInputProblemV1,
    RunInputProblemV2,
    bind_run_input,
    load_run_input,
    verify_run_input,
)
from deepreason.llm.firewall import route_fingerprint
from deepreason.ontology import Commitment
from deepreason.ontology.commitment import Budget
from deepreason.run_manifest import (
    ConjectureContextPolicyV1,
    ContractVersionPolicyV2,
    ContractVersionPolicyV3,
    ControlPlanePolicyV2,
    ControlPlanePolicyV3,
    RunManifestError,
    SchoolExecutionPolicyV1,
    bind_run_manifest,
    compile_run_manifest,
)
from deepreason.runtime.stop import (
    StopController,
    StopMetrics,
    StopPolicy,
    build_stop_record,
    persist_stop_record,
)
from deepreason.workflow.lifecycle import build_stopped_lifecycle
from deepreason.workloads.text import ReasoningWorkloadSpec, WorkloadProblem


STAMP = "2026-07-17T00:00:00Z"
PROBLEM_ID = "immutable-criteria"
PROBLEM_TEXT = "Find a solution that satisfies every frozen commitment."


def _config() -> Config:
    return Config(
        roles={
            "conjecturer": {
                "endpoint_id": "offline-v6-commitments",
                "endpoint": "mock://offline-v6-commitments",
                "model": "offline-model",
                "provider": "mock",
                "family": "offline",
                "max_tokens": 64,
                "context_window_tokens": 262_144,
            }
        }
    )


def _school_execution() -> SchoolExecutionPolicyV1:
    return SchoolExecutionPolicyV1(
        mode="conditioning_only",
        bindings=(),
        allow_shared=True,
        require_distinct_models=False,
        require_distinct_families=False,
    )


def _context_policy() -> ConjectureContextPolicyV1:
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


def _control(version: int):
    values = {
        "school_execution": _school_execution(),
        "conjecture_context": _context_policy(),
        "workflow_retry": WorkflowRetryPolicyV1(),
    }
    if version == 5:
        return ControlPlanePolicyV2(
            **values, contract_versions=ContractVersionPolicyV2()
        )
    return ControlPlanePolicyV3(
        **values, contract_versions=ContractVersionPolicyV3()
    )


def _manifest(version: int, digest: str):
    return compile_run_manifest(
        _config(),
        schema_version=version,
        workload_profile="text",
        rubric_policy="forbid",
        compiled_at=STAMP,
        control_plane_policy=_control(version),
        run_input_digest=digest,
    )


def _dossier() -> EvidenceDossierV1:
    return EvidenceDossierV1.create(
        problem_ref=PROBLEM_ID,
        sources=(),
        total_byte_count=0,
        creation_provenance=AttachedSourceProvenanceV1(
            supplied_by="offline fixture",
            acquisition_method="pre-freeze construction",
        ),
    )


def _bind_v1(root, commitment: Commitment) -> RunInputManifestV1:
    dossier = _dossier()
    run_input = RunInputManifestV1.create(
        problem=RunInputProblemV1(
            id=PROBLEM_ID,
            description=PROBLEM_TEXT,
            criteria=(commitment.id,),
        ),
        evidence_dossier_digest=dossier.dossier_digest,
    )
    bind_run_input(run_input, dossier, root)
    return run_input


def _bind_v2(root, commitment: Commitment) -> RunInputManifestV2:
    dossier = _dossier()
    run_input = RunInputManifestV2.create(
        problem=RunInputProblemV2.from_commitments(
            id=PROBLEM_ID,
            description=PROBLEM_TEXT,
            criteria=(commitment,),
        ),
        evidence_dossier_digest=dossier.dossier_digest,
    )
    bind_run_input(run_input, dossier, root)
    return run_input


def _commitment(**updates) -> Commitment:
    values = {
        "id": "C001",
        "eval": "predicate:True",
        "budget": Budget(steps=100, time_ms=50, extra={"case": "frozen"}),
        "observation_valued": False,
    }
    values.update(updates)
    return Commitment(**values)


def _spec(commitment: Commitment) -> ReasoningWorkloadSpec:
    return ReasoningWorkloadSpec(
        problem=WorkloadProblem(id=PROBLEM_ID, description=PROBLEM_TEXT),
        criteria=(commitment,),
        allow_rubric=False,
    )


def _write_qualification(root, manifest, *, report=None):
    from deepreason.cli.doctor import write_production_contract_report
    from tests.test_cli_production_doctor_v6 import _qualified_report

    policy = manifest.production_qualification_policy
    assert policy is not None
    return write_production_contract_report(
        report or _qualified_report(manifest),
        root / policy.report_filename,
    )


@pytest.mark.parametrize(
    "changed",
    [
        _commitment(eval="predicate:False"),
        _commitment(
            budget=Budget(steps=101, time_ms=50, extra={"case": "frozen"})
        ),
        _commitment(observation_valued=True),
    ],
    ids=("eval", "budget", "observation-valued"),
)
def test_v2_digest_binds_every_commitment_field_under_same_id(changed):
    baseline = _commitment()
    dossier = _dossier()

    def record(commitment):
        return RunInputManifestV2.create(
            problem=RunInputProblemV2.from_commitments(
                id=PROBLEM_ID,
                description=PROBLEM_TEXT,
                criteria=(commitment,),
            ),
            evidence_dossier_digest=dossier.dossier_digest,
        )

    frozen = record(baseline)
    modified = record(changed)
    assert frozen.problem.criteria[0].id == modified.problem.criteria[0].id
    assert frozen.problem.criteria[0] != modified.problem.criteria[0]
    assert frozen.run_input_digest != modified.run_input_digest


def test_v2_round_trip_is_immutable_and_v1_report_shape_is_unchanged(tmp_path):
    v2_root = tmp_path / "v2"
    v2 = _bind_v2(v2_root, _commitment())
    loaded = load_run_input(v2_root)

    assert loaded == v2
    assert verify_run_input(v2_root)["input_schema_version"] == 2
    with pytest.raises(TypeError):
        loaded.problem.criteria[0].budget.extra["case"] = "changed"

    v1_root = tmp_path / "v1"
    v1 = _bind_v1(v1_root, _commitment())
    assert load_run_input(v1_root) == v1
    assert verify_run_input(v1_root) == {
        "valid": True,
        "run_input_digest": v1.run_input_digest,
        "evidence_dossier_digest": v1.evidence_dossier_digest,
        "source_count": 0,
        "source_bytes": 0,
    }


def test_manifest_versions_require_their_versioned_run_input(tmp_path):
    v1_root = tmp_path / "v1-rejected-by-v6"
    v1 = _bind_v1(v1_root, _commitment())
    with pytest.raises(RunManifestError, match="RUN_INPUT_SCHEMA_MISMATCH"):
        bind_run_manifest(_manifest(6, v1.run_input_digest), v1_root)

    v2_root = tmp_path / "v2-rejected-by-v5"
    v2 = _bind_v2(v2_root, _commitment())
    with pytest.raises(RunManifestError, match="RUN_INPUT_SCHEMA_MISMATCH"):
        bind_run_manifest(_manifest(5, v2.run_input_digest), v2_root)

    legacy_root = tmp_path / "v1-v5"
    legacy = _bind_v1(legacy_root, _commitment())
    bind_run_manifest(_manifest(5, legacy.run_input_digest), legacy_root)

    transactional_root = tmp_path / "v2-v6"
    transactional = _bind_v2(transactional_root, _commitment())
    bind_run_manifest(
        _manifest(6, transactional.run_input_digest), transactional_root
    )



@pytest.mark.parametrize(
    "runtime_commitment",
    [
        _commitment(eval="predicate:False"),
        _commitment(
            budget=Budget(steps=100, time_ms=51, extra={"case": "frozen"})
        ),
        _commitment(observation_valued=True),
    ],
    ids=("eval", "budget", "observation-valued"),
)
def test_v6_application_rejects_same_id_with_changed_definition_before_start(
    tmp_path, runtime_commitment
):
    root = tmp_path / runtime_commitment.eval.replace(":", "-")
    frozen = _bind_v2(root, _commitment())
    service = TextRunApplicationService(TextRunWorkerRegistry())

    with pytest.raises(ValueError, match="RUN_INPUT_MISMATCH"):
        service.start(
            StartTextRunIntentV1(
                root=str(root),
                workload=_spec(runtime_commitment),
                run_manifest_ref=str(tmp_path / "unused-manifest.json"),
                budget={"cycles": 1, "token_budget": "unlimited"},
            ),
            manifest_override=_manifest(6, frozen.run_input_digest),
            credential_checker=lambda _manifest: [],
        )

    assert not (root / "run-manifest.json").exists()
    assert not (root / "progress.jsonl").exists()


def test_exact_v6_commitments_start_worker_and_continuation_rechecks_full_bytes(
    tmp_path, monkeypatch
):
    root = tmp_path / "successful-v6"
    commitment = _commitment()
    frozen = _bind_v2(root, commitment)
    manifest = _manifest(6, frozen.run_input_digest)
    _write_qualification(root, manifest)
    calls = []

    def finish_without_provider(
        _harness, _config, _cycles, token_budget, **_kwargs
    ):
        calls.append(token_budget)
        policy = StopPolicy(min_cycles=0, window=1, stable_windows=1)
        controller = StopController(policy)
        before = controller.snapshot()
        metrics = StopMetrics(cycle=len(calls) - 1)
        decision = controller.evaluate(metrics)
        stop = build_stop_record(
            reason=decision.reason,
            policy=policy,
            metrics=metrics,
            event_seq=_harness._next_seq,
        )
        observation, snapshot, lifecycle = build_stopped_lifecycle(
            _harness.workflow_state,
            manifest_digest=manifest.sha256,
            controller_version="workflow.controller.v3",
            workflow_profile="inquiry.active.v2",
            policy=policy,
            metrics=metrics,
            deterministic_decision=decision,
            controller_state_before=before,
            controller_state_after=controller.snapshot(),
            stop_event_seq=_harness._next_seq,
            stop_record_digest=stop["digest"],
        )
        _harness.record_lifecycle_transition(observation, snapshot, lifecycle)
        persist_stop_record(root, stop)
        return (
            {"frontier": [], "survivors": [], "stop_reason": "converged"},
            None,
            {
                "metered_tokens": None,
                "logged_tokens_this_run": 0,
                "delta": None,
                "note": "offline no-provider fixture",
            },
        )

    monkeypatch.setattr("deepreason.ops.run_scheduler", finish_without_provider)
    service = TextRunApplicationService(TextRunWorkerRegistry())
    started = service.start(
        StartTextRunIntentV1(
            root=str(root),
            workload=_spec(commitment),
            run_manifest_ref=str(tmp_path / "unused-manifest.json"),
            budget={"cycles": 1, "token_budget": "unlimited"},
        ),
        manifest_override=manifest,
        credential_checker=lambda _manifest: [],
    )
    service.wait(started.root, timeout=10)

    terminal = service.result(
        InspectTextRunIntentV1(root=started.root)
    )
    assert terminal.lifecycle == "completed"
    assert terminal.payload["schema"] == "deepreason-run-result-v2"
    assert terminal.payload["model_execution"] == {
        "schema": "model-execution-summary.v1",
        "mode": "base_only",
        "base_profile": manifest.model_profile,
        "route_seat_bases": [
            {
                "schema": "route-seat-base-projection.v1",
                "role": entry.role,
                "seat": entry.seat,
                "endpoint_id": entry.endpoint_id,
                "route_sha256": route_fingerprint(
                    manifest.roles[entry.role][entry.seat]
                ),
                "base_profile": entry.base_profile,
                "selection_basis": entry.selection_basis,
            }
            for entry in manifest.route_seat_presentation_plan.entries
        ],
        "recovery_routes": [],
        "event_horizon_seq": terminal.payload["stop"]["event_seq"],
    }
    assert calls == [None]

    continued = service.continue_run(
        ContinueTextRunIntentV1(
            root=str(root),
            budget=RunBudgetIntentV1(cycles=1, token_budget="unlimited"),
            expected_manifest_digest=manifest.sha256,
        ),
        credential_checker=lambda _manifest: [],
    )
    service.wait(continued.root, timeout=10)
    assert service.result(
        InspectTextRunIntentV1(root=continued.root)
    ).lifecycle == "completed"
    assert calls == [None, None]

    workload_path = root / "text-workload.json"
    altered = json.loads(workload_path.read_text(encoding="utf-8"))
    altered["criteria"][0]["eval"] = "predicate:False"
    workload_path.write_text(
        json.dumps(altered, sort_keys=True), encoding="utf-8"
    )

    with pytest.raises(ValueError, match="RUN_INPUT_MISMATCH"):
        service.continue_run(
            ContinueTextRunIntentV1(
                root=str(root),
                budget=RunBudgetIntentV1(
                    cycles=1, token_budget="unlimited"
                ),
                expected_manifest_digest=manifest.sha256,
            ),
            credential_checker=lambda _manifest: [],
        )
    assert calls == [None, None]
