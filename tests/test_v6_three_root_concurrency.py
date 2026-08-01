"""Interconnected qualification: ordinary failures remain root-local."""

from __future__ import annotations

import json
from concurrent.futures import ThreadPoolExecutor
from threading import Barrier

from deepreason.application.models import RunResultV2
from deepreason.application.text_runs import _v6_run_result
from deepreason.evidence import (
    AttachedSourceProvenanceV1,
    EvidenceDossierV1,
    RunInputManifestV2,
    RunInputProblemV2,
    bind_run_input,
)
from deepreason.evidence.render import attach_bound_evidence
from deepreason.harness import Harness
from deepreason.llm.adapter import LLMAdapter
from deepreason.llm.budget import TokenMeter
from deepreason.llm.endpoints import MockEndpoint
from deepreason.llm.firewall import leases_from_manifest
from deepreason.ontology import Provenance
from deepreason.run_manifest import bind_run_manifest, compile_run_manifest
from deepreason.runtime.progress import _atomic_json
from deepreason.runtime.stop import StopMetrics, StopPolicy, write_stop_record
from deepreason.scheduler.scheduler import Scheduler
from deepreason.verification.report import verify_root_report
from deepreason.workloads.text import (
    ReasoningWorkloadSpec,
    WorkloadProblem,
    seed_reasoning_workload,
)
from tests.test_v6_transaction_qualification import (
    STAMP,
    _config,
    _control,
    _criticism_policy,
)
from tests.test_v6_compact_recovery_transition import _bind_classification


VALID_CRITIC = json.dumps(
    {
        "cases": [
            {
                "target_alias": "SRC_001",
                "attack": False,
                "case": "",
                "counterexample": None,
            }
        ]
    }
)


def _prepare_root(root, run_id: str):
    problem_id = f"concurrency-{run_id}"
    spec = ReasoningWorkloadSpec(
        problem=WorkloadProblem(
            id=problem_id,
            description=f"Root-local concurrent qualification {run_id}.",
        ),
        criteria=(),
        allow_rubric=False,
    )
    dossier = EvidenceDossierV1.create(
        problem_ref=problem_id,
        sources=(),
        total_byte_count=0,
        creation_provenance=AttachedSourceProvenanceV1(
            supplied_by="concurrency fixture",
            acquisition_method="offline construction",
        ),
    )
    run_input = RunInputManifestV2.create(
        problem=RunInputProblemV2.from_commitments(
            id=problem_id,
            description=spec.problem.description,
            criteria=(),
        ),
        evidence_dossier_digest=dossier.dossier_digest,
    )
    bind_run_input(run_input, dossier, root)
    config = _config(critics=True)
    manifest = compile_run_manifest(
        config,
        schema_version=6,
        workload_profile="text",
        rubric_policy="forbid",
        compiled_at=STAMP,
        control_plane_policy=_control(),
        criticism_policy=_criticism_policy(),
        run_input_digest=run_input.run_input_digest,
    )
    bind_run_manifest(manifest, root)
    harness = Harness(root)
    seed_reasoning_workload(harness, spec)
    attach_bound_evidence(
        harness,
        run_input=run_input,
        dossier=dossier,
        problem_id=problem_id,
    )
    target = harness.create_artifact(
        f"unique concurrent target {run_id}",
        provenance=Provenance(role="conjecturer", school="school-0"),
    )
    return config, manifest, harness, target


def test_three_concurrent_roots_isolate_schema_budget_and_success(tmp_path):
    barrier = Barrier(3)

    def execute(run_id: str, mode: str):
        root = tmp_path / run_id
        config, manifest, harness, target = _prepare_root(root, run_id)
        forbidden_calls: list[str] = []

        def forbidden(_prompt):
            forbidden_calls.append(run_id)
            raise AssertionError("provider dispatched after root-local budget denial")

        critics = []
        for seat, route in enumerate(manifest.roles["argumentative_critic"]):
            if mode == "denied":
                responses = forbidden
            elif mode == "schema" and seat == 1:
                responses = [
                    "{not-json",
                    "{still-not-json",
                    "{atomic-not-json",
                    "{atomic-still-not-json",
                    "{atomic-final-not-json",
                ]
            else:
                responses = [VALID_CRITIC]
            critics.append(
                MockEndpoint(
                    responses,
                    name=route.base_url,
                    model=route.model_id,
                    max_tokens=route.max_tokens,
                )
            )
        meter = TokenMeter(1 if mode == "denied" else 100_000)
        adapter = LLMAdapter(
            {
                "conjecturer": MockEndpoint([]),
                "argumentative_critic": critics,
            },
            harness.blobs,
            retry_max=2,
            meter=meter,
            model_profile=manifest.model_profile,
            leases=leases_from_manifest(manifest),
            transaction_authority_required=True,
        )
        _bind_classification(harness, manifest)
        barrier.wait(timeout=10)
        Scheduler(harness, adapter, config, run_manifest=manifest)._foreign_arg_crit()
        stop_policy = StopPolicy()
        stop_metrics = StopMetrics(cycle=0)
        event_horizon = harness._next_seq
        stop_event = harness.record_measure(
            inputs=[
                "run-stop",
                stop_policy.digest,
                json.dumps(stop_metrics.model_dump(mode="json"), sort_keys=True),
                "completed",
                str(event_horizon),
            ]
        )
        assert stop_event.seq == event_horizon
        stop = write_stop_record(
            root,
            reason="completed",
            policy=stop_policy,
            metrics=stop_metrics,
            event_seq=stop_event.seq,
        )
        _atomic_json(
            root / "run-result.json",
            _v6_run_result(
                root,
                manifest,
                {
                    "schema": "deepreason-run-result-v1",
                    "state": "completed",
                    "workload": "text",
                    "problem_id": f"concurrency-{run_id}",
                    "stop": stop,
                },
                harness=harness,
            ),
        )
        work = dict(harness.workflow_state.transaction_work)
        debts = []
        for event in harness.log.read():
            for object_id in event.outputs:
                schema, record = harness.objects.get(object_id)
                if schema == "criticism-coverage-debt-v1" and record.target_id == target.id:
                    debts.append(record)
        return {
            "root": root,
            "target_id": target.id,
            "work": work,
            "debt": debts[-1],
            "meter": meter.snapshot(),
            "forbidden_calls": tuple(forbidden_calls),
        }

    cases = (("schema-root", "schema"), ("denied-root", "denied"), ("ok-root", "ok"))
    with ThreadPoolExecutor(max_workers=3) as pool:
        futures = {run_id: pool.submit(execute, run_id, mode) for run_id, mode in cases}
        results = {run_id: future.result(timeout=30) for run_id, future in futures.items()}

    schema = results["schema-root"]
    denied = results["denied-root"]
    success = results["ok-root"]
    assert {item.terminal.status for item in schema["work"].values()} == {
        "completed",
        "schema_exhausted",
        "rejected",
    }
    assert schema["debt"].outstanding_school_ids == ("school-1",)
    assert all(item.terminal.status == "budget_denied" for item in denied["work"].values())
    assert all(not item.issued for item in denied["work"].values())
    assert all(item.exposure is None for item in denied["work"].values())
    assert denied["meter"]["total"] == 0
    assert denied["forbidden_calls"] == ()
    assert all(item.terminal.status == "completed" for item in success["work"].values())
    assert success["debt"].outstanding_school_ids == ()
    assert success["meter"]["calls"] == 2

    target_ids = {name: result["target_id"] for name, result in results.items()}
    work_ids = {name: set(result["work"]) for name, result in results.items()}
    assert all(
        work_ids[left].isdisjoint(work_ids[right])
        for left in work_ids
        for right in work_ids
        if left < right
    )
    for name, result in results.items():
        log_text = (result["root"] / "log.jsonl").read_text(encoding="utf-8")
        assert all(
            foreign_id not in log_text for other, foreign_id in target_ids.items() if other != name
        )
        assert all(
            foreign_work_id not in log_text
            for other, foreign_ids in work_ids.items()
            if other != name
            for foreign_work_id in foreign_ids
        )
        assert all(
            str(other_result["root"].resolve()) not in log_text
            for other, other_result in results.items()
            if other != name
        )

    run_results = {
        name: RunResultV2.model_validate(
            json.loads((result["root"] / "run-result.json").read_text(encoding="utf-8"))
        )
        for name, result in results.items()
    }
    reports = {name: verify_root_report(result["root"]) for name, result in results.items()}

    assert all(result.state == "completed" for result in run_results.values())
    assert all(
        report.integrity_valid and report.security_valid for report in reports.values()
    )

    assert not reports["schema-root"].operational_checks_passed
    assert reports["denied-root"].operational_checks_passed
    assert reports["denied-root"].epistemic_checks_passed
    assert not reports["denied-root"].completion_satisfied
    assert reports["ok-root"].completion_satisfied
    assert reports["ok-root"].epistemic_checks_passed
    assert reports["ok-root"].operational_checks_passed
