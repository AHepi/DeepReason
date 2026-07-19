import json
from pathlib import Path
from types import SimpleNamespace

import pytest

from deepreason.application.models import (
    InspectTextRunIntentV1,
    StartTextRunIntentV1,
)
from deepreason.application.text_runs import (
    TextRunApplicationService,
    TextRunWorkerRegistry,
)
from deepreason.canonical import canonical_json, sha256_hex
from deepreason.cli.main import main
from deepreason.experiments.campaign import (
    CampaignCoordinator,
    CampaignPlan,
    CampaignRunPlan,
    CampaignWavePlan,
    QualificationReportRef,
)
from deepreason.runtime.launch_policy import (
    RELEASE_POLICY_ENV,
    RELEASE_POLICY_SCHEMA,
    V6_LAUNCH_DISABLE_ENV,
    require_v6_launch_allowed,
)
from deepreason.workloads.text import ReasoningWorkloadSpec, WorkloadProblem


MANIFEST_SHA256 = "a" * 64


def _verification_report():
    return {
        "schema": "verification.report.v2",
        "integrity_valid": True,
        "security_valid": True,
        "completion_satisfied": True,
        "epistemic_checks_passed": True,
        "operational_checks_passed": True,
        "integrity": [],
        "security": [],
        "completion": [],
        "epistemic": [],
        "operational": [],
        "stats": {},
    }


def _write_terminal(root: Path) -> None:
    root.mkdir(parents=True, exist_ok=True)
    (root / "run-result.json").write_text(
        json.dumps({"schema": "deepreason-run-result-v2", "state": "completed"}),
        encoding="utf-8",
    )
    (root / "log.jsonl").touch()


def _plan(tmp_path: Path, *, qualification: bool) -> CampaignPlan:
    return CampaignPlan(
        qualification=qualification,
        waves=(
            CampaignWavePlan(
                "A",
                (
                    CampaignRunPlan(
                        "A1",
                        tmp_path / "run",
                        ("reason", "A1"),
                        run_manifest=tmp_path / "v6.json",
                    ),
                ),
            ),
        ),
    )


def _report_refs(tmp_path: Path) -> tuple[QualificationReportRef, ...]:
    refs = []
    for gate in ("R0", "R1", "R2", "R3", "R4"):
        payload = {
            "schema": "deepreason-v6-qualification-report-v1",
            "gate": gate,
            "passed": True,
            "manifest_sha256s": [MANIFEST_SHA256],
            "checks": [{"id": f"{gate}-qualification", "passed": True}],
        }
        raw = canonical_json(payload)
        path = tmp_path / f"{gate}.json"
        path.write_bytes(raw)
        refs.append(
            QualificationReportRef(
                gate=gate,
                path=path,
                sha256=sha256_hex(raw),
            )
        )
    return tuple(refs)


def _clear_release_policy(monkeypatch) -> None:
    monkeypatch.delenv(V6_LAUNCH_DISABLE_ENV, raising=False)
    monkeypatch.delenv(RELEASE_POLICY_ENV, raising=False)


def test_qualification_mode_can_run_without_prior_reports(
    tmp_path, monkeypatch
):
    _clear_release_policy(monkeypatch)
    manifest = SimpleNamespace(schema_version=6, sha256=MANIFEST_SHA256)
    monkeypatch.setattr(
        "deepreason.experiments.campaign.load_run_manifest",
        lambda _path: manifest,
    )

    def runner(_command, _cwd):
        _write_terminal(tmp_path / "run")
        return 0

    index = CampaignCoordinator(
        runner=runner,
        verifier=lambda _root: _verification_report(),
    ).run(_plan(tmp_path, qualification=True))

    gate = index.to_dict()["qualification_gate"]
    assert gate["mode"] == "qualification"
    assert gate["required"] is False
    assert gate["manifest_sha256s"] == [MANIFEST_SHA256]
    assert gate["reports"] == []


def test_broad_v6_requires_reports_before_runner(tmp_path, monkeypatch):
    _clear_release_policy(monkeypatch)
    manifest = SimpleNamespace(schema_version=6, sha256=MANIFEST_SHA256)
    monkeypatch.setattr(
        "deepreason.experiments.campaign.load_run_manifest",
        lambda _path: manifest,
    )
    runner_called = False

    def runner(_command, _cwd):
        nonlocal runner_called
        runner_called = True
        return 0

    with pytest.raises(ValueError, match="CAMPAIGN_QUALIFICATION_GATE_REQUIRED"):
        CampaignCoordinator(runner=runner).run(
            _plan(tmp_path, qualification=False)
        )
    assert runner_called is False


def test_broad_v6_verifies_and_binds_exact_r0_r4_reports(
    tmp_path, monkeypatch
):
    _clear_release_policy(monkeypatch)
    manifest = SimpleNamespace(schema_version=6, sha256=MANIFEST_SHA256)
    monkeypatch.setattr(
        "deepreason.experiments.campaign.load_run_manifest",
        lambda _path: manifest,
    )
    plan = _plan(tmp_path, qualification=False)
    plan = CampaignPlan(
        waves=plan.waves,
        qualification=False,
        qualification_reports=_report_refs(tmp_path),
    )

    def runner(_command, _cwd):
        _write_terminal(tmp_path / "run")
        return 0

    index = CampaignCoordinator(
        runner=runner,
        verifier=lambda _root: _verification_report(),
    ).run(plan)
    gate = index.to_dict()["qualification_gate"]
    digest = gate.pop("gate_sha256")
    assert digest == sha256_hex(canonical_json(gate))
    assert gate["required"] is True
    assert [report["gate"] for report in gate["reports"]] == [
        "R0",
        "R1",
        "R2",
        "R3",
        "R4",
    ]


def test_changed_qualification_report_fails_before_runner(
    tmp_path, monkeypatch
):
    _clear_release_policy(monkeypatch)
    manifest = SimpleNamespace(schema_version=6, sha256=MANIFEST_SHA256)
    monkeypatch.setattr(
        "deepreason.experiments.campaign.load_run_manifest",
        lambda _path: manifest,
    )
    refs = _report_refs(tmp_path)
    refs[2].path.write_text("{}", encoding="utf-8")
    plan = CampaignPlan(
        waves=_plan(tmp_path, qualification=False).waves,
        qualification=False,
        qualification_reports=refs,
    )
    with pytest.raises(
        ValueError, match="CAMPAIGN_QUALIFICATION_REPORT_DIGEST_MISMATCH"
    ):
        CampaignCoordinator(
            runner=lambda *_args: pytest.fail("gate failure launched a runner")
        ).run(plan)


def test_release_switch_rejects_reason_before_root_mutation_but_not_inspection(
    tmp_path, monkeypatch
):
    monkeypatch.setenv(V6_LAUNCH_DISABLE_ENV, "true")
    monkeypatch.delenv(RELEASE_POLICY_ENV, raising=False)
    root = tmp_path / "run"
    service = TextRunApplicationService(TextRunWorkerRegistry())
    intent = StartTextRunIntentV1(
        root=str(root),
        workload=ReasoningWorkloadSpec(
            problem=WorkloadProblem(id="p", description="rollback fixture")
        ),
        run_manifest_ref=str(tmp_path / "unused.json"),
        budget={"cycles": 1, "token_budget": "unlimited"},
    )

    with pytest.raises(ValueError, match="V6_LAUNCH_DISABLED"):
        service.start(
            intent,
            manifest_override=SimpleNamespace(schema_version=6),
            credential_checker=lambda _manifest: pytest.fail(
                "rollback rejection reached credential checking"
            ),
        )
    assert not root.exists()
    assert (
        service.inspect(InspectTextRunIntentV1(root=str(root))).lifecycle
        == "not-started"
    )


def test_release_switch_precedes_v6_make_contract_preflight(
    tmp_path, monkeypatch, capsys
):
    monkeypatch.setenv(V6_LAUNCH_DISABLE_ENV, "1")
    monkeypatch.delenv(RELEASE_POLICY_ENV, raising=False)
    manifest = SimpleNamespace(schema_version=6, engine_profile="full")
    monkeypatch.setattr(
        "deepreason.run_manifest.load_run_manifest",
        lambda _path: manifest,
    )
    root = tmp_path / "site"

    exit_code = main(
        [
            "--root",
            str(root),
            "make",
            "rollback site",
            "--run-manifest",
            str(tmp_path / "v6.json"),
        ]
    )

    assert exit_code == 1
    assert "V6_LAUNCH_DISABLED" in capsys.readouterr().err
    assert not root.exists()

def test_release_switch_rejects_campaign_before_runner(tmp_path, monkeypatch):
    monkeypatch.setenv(V6_LAUNCH_DISABLE_ENV, "on")
    monkeypatch.delenv(RELEASE_POLICY_ENV, raising=False)
    manifest = SimpleNamespace(schema_version=6, sha256=MANIFEST_SHA256)
    monkeypatch.setattr(
        "deepreason.experiments.campaign.load_run_manifest",
        lambda _path: manifest,
    )

    with pytest.raises(ValueError, match="V6_LAUNCH_DISABLED"):
        CampaignCoordinator(
            runner=lambda *_args: pytest.fail("rollback launched campaign work")
        ).run(_plan(tmp_path, qualification=True))


def test_broad_legacy_campaign_needs_no_v6_reports(tmp_path, monkeypatch):
    _clear_release_policy(monkeypatch)
    manifest = SimpleNamespace(schema_version=5, sha256="b" * 64)
    monkeypatch.setattr(
        "deepreason.experiments.campaign.load_run_manifest",
        lambda _path: manifest,
    )

    def runner(_command, _cwd):
        _write_terminal(tmp_path / "run")
        return 0

    index = CampaignCoordinator(
        runner=runner,
        verifier=lambda _root: _verification_report(),
    ).run(_plan(tmp_path, qualification=False))
    assert index.qualification_gate.required is False
    assert index.qualification_gate.reports == ()




def test_release_policy_file_is_fail_closed_only_for_v6(tmp_path, monkeypatch):
    monkeypatch.delenv(V6_LAUNCH_DISABLE_ENV, raising=False)
    policy = tmp_path / "release-policy.json"
    policy.write_text(
        json.dumps(
            {
                "schema": RELEASE_POLICY_SCHEMA,
                "v6_launches_enabled": False,
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setenv(RELEASE_POLICY_ENV, str(policy))

    with pytest.raises(ValueError, match="V6_LAUNCH_DISABLED"):
        require_v6_launch_allowed(
            SimpleNamespace(schema_version=6),
            operation="test launch",
        )
    policy.write_text("{", encoding="utf-8")
    assert (
        require_v6_launch_allowed(
            SimpleNamespace(schema_version=5),
            operation="legacy launch",
        )
        is None
    )
