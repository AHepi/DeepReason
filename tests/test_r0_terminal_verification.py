"""R0 containment, terminal exit, and dimensioned verification contracts."""

from __future__ import annotations

import json

import pytest
from pydantic import ValidationError

from deepreason.application.models import (
    InspectTextRunIntentV1,
    RunResultV2,
    StartTextRunIntentV1,
    run_result_exit_code,
)
from deepreason.application.text_runs import (
    TextRunApplicationService,
    TextRunWorkerRegistry,
    _v6_run_result,
)
from deepreason.harness import Harness
from deepreason.run_manifest import RunManifestError
from deepreason.verification.report import verify_root_report
from deepreason.workloads.text import ReasoningWorkloadSpec, WorkloadProblem


@pytest.mark.parametrize(
    ("payload", "expected"),
    [
        ({"state": "completed"}, 0),
        ({"state": "cancelled"}, 3),
        ({"state": "failed"}, 4),
        (
            {
                "state": "completed",
                "verification": {
                    "integrity_valid": False,
                    "security_valid": True,
                },
            },
            5,
        ),
        ({"state": "mystery"}, 6),
        (
            {
                "state": "mystery",
                "verification": {
                    "integrity_valid": False,
                    "security_valid": False,
                },
            },
            6,
        ),
        ({}, 6),
    ],
)
def test_run_result_exit_contract(payload, expected):
    assert run_result_exit_code(payload) == expected


def test_run_result_v2_validates_derived_summary_fields():
    payload = {
        "schema": "deepreason-run-result-v2",
        "state": "completed",
        "workload": "text",
        "verification": {
            "schema": "verification.summary.v2",
            "valid": True,
            "integrity_valid": True,
            "security_valid": True,
            "completion_satisfied": False,
            "epistemic_checks_passed": True,
            "operational_checks_passed": True,
            "finding_counts": {
                "integrity": 0,
                "security": 0,
                "completion": 1,
                "epistemic": 0,
                "operational": 0,
            },
        },
        "completion_status": "incomplete",
        "canonical_bridge_eligible": True,
    }

    assert RunResultV2.model_validate(payload).state == "completed"
    with pytest.raises(ValueError, match="bridge eligibility"):
        RunResultV2.model_validate(
            {**payload, "canonical_bridge_eligible": False}
        )

    contradictory = {
        **payload,
        "verification": {
            **payload["verification"],
            "finding_counts": {
                **payload["verification"]["finding_counts"],
                "operational": 1,
            },
        },
    }
    with pytest.raises(ValueError, match="flags differ from finding counts"):
        RunResultV2.model_validate(contradictory)


def test_v6_writer_emits_verified_v2_envelope(tmp_path, monkeypatch):
    import json

    from deepreason.runtime.stop import StopMetrics, StopPolicy, write_stop_record
    from deepreason.verification.report import VerificationReportV2
    from tests.test_v6_compact_recovery_transition import (
        _manifest,
        _persist_manifest,
    )

    manifest = _manifest()
    _persist_manifest(manifest, tmp_path)
    harness = Harness(tmp_path)
    policy = StopPolicy()
    metrics = StopMetrics(cycle=0)
    event = harness.record_measure(
        inputs=[
            "run-stop",
            policy.digest,
            json.dumps(metrics.model_dump(mode="json"), sort_keys=True),
            "completed",
            str(harness._next_seq),
        ]
    )
    stop = write_stop_record(
        tmp_path,
        reason="completed",
        policy=policy,
        metrics=metrics,
        event_seq=event.seq,
    )

    monkeypatch.setattr(
        "deepreason.verification.report.verify_root_report",
        lambda _root, **_kwargs: VerificationReportV2(),
    )

    payload = _v6_run_result(
        tmp_path,
        manifest,
        {
            "schema": "deepreason-run-result-v1",
            "state": "completed",
            "workload": "text",
            "survivors": [],
            "stop": stop,
        },
    )

    assert payload["schema"] == "deepreason-run-result-v2"
    assert payload["state"] == "completed"
    assert payload["verification"]["valid"] is True
    assert payload["completion_status"] == "satisfied"
    assert payload["canonical_bridge_eligible"] is True
    assert payload["model_execution"]["mode"] == "base_only"
    assert payload["model_execution"]["event_horizon_seq"] == stop["event_seq"]
    assert payload["stop"] == stop
    assert payload["survivors"] == []


def test_verify_root_report_separates_completion_from_false_authority(
    tmp_path, monkeypatch
):
    from deepreason import invariants

    monkeypatch.setattr(
        invariants,
        "verify_root",
        lambda *_args, **_kwargs: {
            "violations": [
                {
                    "check": "foreign-criticism",
                    "detail": "target A has 0 foreign schools; policy requires 2",
                },
                {
                    "check": "dossier-pack",
                    "detail": "event seq=9: receipt exceeds bound dossier authority",
                },
            ],
            "stats": {"capability_requests": 1, "capability_executions": 0},
        },
    )

    report = verify_root_report(tmp_path)

    assert not report.integrity_valid
    assert report.security_valid
    assert not report.completion_satisfied
    assert not report.valid
    assert [item.check for item in report.integrity] == ["dossier-pack"]
    assert [item.check for item in report.completion] == [
        "foreign-criticism",
        "capability-lifecycle",
    ]


def test_failed_terminal_is_operational_without_invalidating_history(
    tmp_path, monkeypatch
):
    from deepreason import invariants

    monkeypatch.setattr(
        invariants,
        "verify_root",
        lambda *_args, **_kwargs: {"violations": [], "stats": {}},
    )
    (tmp_path / "run-result.json").write_text(
        json.dumps(
            {
                "schema": "deepreason-run-result-v1",
                "state": "failed",
                "workload": "text",
                "error_type": "SchemaRepairError",
                "error": "critic output exhausted its repair ceiling",
            }
        ),
        encoding="utf-8",
    )

    report = verify_root_report(tmp_path)

    assert report.valid
    assert report.integrity_valid and report.security_valid
    assert not report.operational_checks_passed
    assert report.operational[0].check == "run-terminal"


def test_v6_missing_terminal_is_operational_but_not_invalid(tmp_path, monkeypatch):
    from deepreason import invariants

    monkeypatch.setattr(
        invariants,
        "verify_root",
        lambda *_args, **_kwargs: {"violations": [], "stats": {}},
    )
    monkeypatch.setattr(
        "deepreason.verification.report._manifest_schema_version",
        lambda _root: 6,
    )

    report = verify_root_report(tmp_path)
    assert report.valid
    assert not report.operational_checks_passed
    assert report.operational[0].check == "run-result"

    writer_view = verify_root_report(tmp_path, allow_missing_terminal=True)
    assert writer_view.operational_checks_passed

def test_application_reader_normalizes_malformed_terminal_to_unknown_exit(
    tmp_path,
):
    (tmp_path / "run-result.json").write_text("{", encoding="utf-8")
    service = TextRunApplicationService(TextRunWorkerRegistry())

    with pytest.raises(ValueError, match="RUN_RESULT_INVALID"):
        service.result(InspectTextRunIntentV1(root=str(tmp_path)))


def test_v5_active_inquiry_and_override_fail_before_application_launch(
    tmp_path, monkeypatch
):
    from tests.test_run_manifest_v5_inquiry import _compile, _empty_input

    root = tmp_path / "v5"
    run_input = _empty_input(root)
    manifest = _compile(run_input.run_input_digest)
    workload = ReasoningWorkloadSpec(
        problem=WorkloadProblem(id="pi-v5", description="v5 fixture")
    )
    service = TextRunApplicationService(TextRunWorkerRegistry())
    base = {
        "root": str(root),
        "workload": workload,
        "run_manifest_ref": str(tmp_path / "unused.json"),
        "budget": {"cycles": 1, "token_budget": "unlimited"},
    }
    before = {
        path.relative_to(root).as_posix(): path.read_bytes()
        for path in root.rglob("*")
        if path.is_file()
    }
    calls = []
    monkeypatch.setattr(
        "deepreason.ops.run_scheduler",
        lambda *_args, **_kwargs: calls.append("scheduler"),
    )

    with pytest.raises(RunManifestError) as caught:
        service.start(
            StartTextRunIntentV1(**base),
            manifest_override=manifest,
            credential_checker=lambda _manifest: [],
        )
    assert caught.value.code == "V6_RUN_MANIFEST_REQUIRED"

    with pytest.raises(ValidationError, match="extra_forbidden"):
        StartTextRunIntentV1(**base, experimental_v5=True)

    after = {
        path.relative_to(root).as_posix(): path.read_bytes()
        for path in root.rglob("*")
        if path.is_file()
    }
    assert after == before
    assert calls == []


def test_v6_legacy_run_result_schema_is_an_integrity_failure(
    tmp_path, monkeypatch
):
    from deepreason import invariants

    monkeypatch.setattr(
        invariants,
        "verify_root",
        lambda *_args, **_kwargs: {"violations": [], "stats": {}},
    )
    monkeypatch.setattr(
        "deepreason.verification.report._manifest_schema_version",
        lambda _root: 6,
    )
    (tmp_path / "run-result.json").write_text(
        json.dumps(
            {
                "schema": "deepreason-run-result-v1",
                "state": "completed",
                "workload": "text",
            }
        ),
        encoding="utf-8",
    )

    report = verify_root_report(tmp_path)

    assert not report.integrity_valid
    assert report.security_valid
    assert "run-result-version" in {finding.check for finding in report.integrity}
