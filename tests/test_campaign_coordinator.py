import json
import os
from pathlib import Path
from types import SimpleNamespace

import pytest

from deepreason.run_manifest import (
    MANIFEST_NAME,
    RunManifestError,
    load_run_manifest as canonical_load_run_manifest,
)
from deepreason.experiments.campaign import (
    CAMPAIGN_MANIFEST_AUTHORITY_MISMATCH,
    CampaignCoordinator,
    CampaignPlan,
    CampaignRunPlan,
    CampaignWavePlan,
    RootClassification,
    audit_root,
    campaign_plan_from_mapping,
    inspect_bridge_terminal,
)


@pytest.fixture(autouse=True)
def _explicit_test_launch_manifest(monkeypatch):
    """Resolve explicit synthetic authority used by command-launch fixtures."""

    def load(path):
        candidate = Path(path)
        name = candidate.name
        if name == MANIFEST_NAME:
            try:
                name = candidate.read_text(encoding="utf-8").strip()
            except OSError as error:
                raise AssertionError(
                    f"unreadable synthetic bound manifest: {path}"
                ) from error
            if name == "unreadable":
                raise OSError("synthetic unreadable bound manifest")
            if name not in {"campaign-test-v5.json", "campaign-test-v6.json"}:
                return canonical_load_run_manifest(candidate)
        if name == "campaign-test-v5.json":
            return SimpleNamespace(schema_version=5, sha256="5" * 64)
        if name == "campaign-test-v6.json":
            return SimpleNamespace(schema_version=6, sha256="6" * 64)
        raise AssertionError(f"unexpected synthetic launch manifest: {path}")

    monkeypatch.setattr(
        "deepreason.experiments.campaign.load_run_manifest",
        load,
    )
    monkeypatch.setattr(
        "deepreason.run_manifest.load_run_manifest",
        load,
    )


def _manifest_authority(tmp_path: Path, version: int = 5) -> Path:
    return tmp_path / f"campaign-test-v{version}.json"


def _bind_manifest(root: Path, authority: Path) -> None:
    (root / MANIFEST_NAME).write_text(authority.name, encoding="utf-8")


def _report(**updates):
    value = {
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
    value.update(updates)
    return value


def _write_result(
    root: Path, state: str, *, manifest: Path | None = None
) -> None:
    root.mkdir(parents=True, exist_ok=True)
    if manifest is not None:
        _bind_manifest(root, manifest)
    (root / "run-result.json").write_text(
        json.dumps({"schema": "deepreason-run-result-v1", "state": state}),
        encoding="utf-8",
    )
    (root / "log.jsonl").touch()


def _append_bridge(root: Path, action: str, *, sequence: int = 0) -> None:
    event = {
        "seq": sequence,
        "rule": "Bridge",
        "bridge": {
            "schema": "bridge.event.payload.v1",
            "action": action,
        },
    }
    with (root / "log.jsonl").open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(event) + "\n")


def test_audit_uses_canonical_result_and_log_not_process_or_events_file(tmp_path):
    root = tmp_path / "A1"
    _write_result(root, "failed")
    _append_bridge(root, "completed", sequence=7)
    (root / "events.jsonl").write_text(
        json.dumps(
            {
                "seq": 99,
                "rule": "Bridge",
                "bridge": {"action": "failed"},
            }
        )
        + "\n",
        encoding="utf-8",
    )

    audit = audit_root(
        root,
        verifier=lambda _: _report(),
        reasoning_returncode=0,
    )

    assert audit.reasoning_terminal.state == "failed"
    assert audit.bridge_terminal.state == "completed"
    assert audit.bridge_terminal.sequence == 7
    assert audit.classification == RootClassification.OPERATIONAL_FAILURE
    assert audit.canonical_bridge_eligible is False


def test_classification_precedence_retains_every_dimension(tmp_path):
    root = tmp_path / "mixed"
    _write_result(root, "completed")
    report = _report(
        security_valid=False,
        integrity_valid=False,
        operational_checks_passed=False,
        completion_satisfied=False,
        epistemic_checks_passed=False,
        security=[{"channel": "security", "check": "s", "detail": "S", "source": "v"}],
        integrity=[{"channel": "integrity", "check": "i", "detail": "I", "source": "v"}],
        operational=[
            {"channel": "operational", "check": "o", "detail": "O", "source": "v"}
        ],
        completion=[
            {"channel": "completion", "check": "c", "detail": "C", "source": "v"}
        ],
        epistemic=[
            {"channel": "epistemic", "check": "e", "detail": "E", "source": "v"}
        ],
    )

    audit = audit_root(root, verifier=lambda _: report)

    assert audit.classification == RootClassification.SECURITY_FAILURE
    assert [finding.detail for finding in audit.dimensions.security] == ["S"]
    assert [finding.detail for finding in audit.dimensions.integrity] == ["I"]
    assert [finding.detail for finding in audit.dimensions.operational] == ["O"]
    assert [finding.detail for finding in audit.dimensions.completion] == ["C"]
    assert [finding.detail for finding in audit.dimensions.epistemic] == ["E"]


def test_epistemic_failure_is_incomplete_not_integrity_failure(tmp_path):
    root = tmp_path / "epistemic"
    _write_result(root, "completed")
    audit = audit_root(
        root,
        verifier=lambda _: _report(
            epistemic_checks_passed=False,
            epistemic=[
                {
                    "channel": "epistemic",
                    "check": "grounding",
                    "detail": "unsupported rendering",
                    "source": "bridge",
                }
            ],
        ),
    )

    assert audit.classification == RootClassification.INCOMPLETE
    assert audit.dimensions.integrity_valid is True
    assert audit.dimensions.security_valid is True


def test_ordinary_root_failure_does_not_suppress_sibling_or_later_wave(tmp_path):
    calls: list[tuple[str, str]] = []
    roots = {name: tmp_path / name for name in ("A1", "A2", "B1")}
    authority = _manifest_authority(tmp_path)

    def runner(command, _cwd):
        phase, run_id = command
        calls.append((phase, run_id))
        if phase == "reason":
            _write_result(
                roots[run_id],
                "failed" if run_id == "A1" else "completed",
                manifest=authority,
            )
        else:
            _append_bridge(roots[run_id], "completed")
        return 0

    plan = CampaignPlan(
        waves=(
            CampaignWavePlan(
                "A",
                (
                    CampaignRunPlan("A1", roots["A1"], ("reason", "A1"), ("bridge", "A1"), run_manifest=authority),
                    CampaignRunPlan("A2", roots["A2"], ("reason", "A2"), ("bridge", "A2"), run_manifest=authority),
                ),
            ),
            CampaignWavePlan(
                "B",
                (
                    CampaignRunPlan("B1", roots["B1"], ("reason", "B1"), ("bridge", "B1"), run_manifest=authority),
                ),
            ),
        )
    )

    index = CampaignCoordinator(runner=runner, verifier=lambda _: _report()).run(plan)

    assert index.systemic_stop is False
    assert [wave.state for wave in index.waves] == ["completed", "completed"]
    assert ("reason", "A1") in calls
    assert ("reason", "A2") in calls
    assert ("reason", "B1") in calls
    assert ("bridge", "A1") not in calls
    assert ("bridge", "A2") in calls
    assert ("bridge", "B1") in calls
    a1, a2 = index.waves[0].runs
    assert a1.bridge_decision == "skipped_non_completed_reasoning"
    assert a1.audit.classification == RootClassification.OPERATIONAL_FAILURE
    assert a2.audit.classification == RootClassification.COMPLETE


def test_systemic_finding_suppresses_later_wave_only_after_siblings_finish(tmp_path):
    calls: list[str] = []
    roots = {name: tmp_path / name for name in ("A1", "A2", "B1")}
    authority = _manifest_authority(tmp_path)

    def runner(command, _cwd):
        run_id = command[1]
        calls.append(run_id)
        _write_result(roots[run_id], "completed", manifest=authority)
        return 0

    def verifier(root):
        if root.name == "A1":
            return _report(
                security_valid=False,
                security=[
                    {
                        "channel": "security",
                        "check": "boundary",
                        "detail": "foreign root authority",
                        "source": "test",
                    }
                ],
            )
        return _report()

    plan = CampaignPlan(
        waves=(
            CampaignWavePlan(
                "A",
                (
                    CampaignRunPlan("A1", roots["A1"], ("reason", "A1"), run_manifest=authority),
                    CampaignRunPlan("A2", roots["A2"], ("reason", "A2"), run_manifest=authority),
                ),
            ),
            CampaignWavePlan(
                "B",
                (CampaignRunPlan("B1", roots["B1"], ("reason", "B1"), run_manifest=authority),),
            ),
        )
    )

    index = CampaignCoordinator(runner=runner, verifier=verifier).run(plan)

    assert set(calls) == {"A1", "A2"}
    assert index.systemic_stop is True
    assert index.stopped_after_wave == "A"
    assert index.waves[0].state == "completed"
    assert len(index.waves[0].runs) == 2
    assert index.waves[1].state == "suppressed"
    assert index.waves[1].suppressed_run_ids == ("B1",)


def test_nonzero_process_exit_cannot_block_bridge_for_completed_canonical_run(tmp_path):
    root = tmp_path / "A1"
    authority = _manifest_authority(tmp_path)
    bridge_called = False

    def runner(command, _cwd):
        nonlocal bridge_called
        if command[0] == "reason":
            _write_result(root, "completed", manifest=authority)
            return 4
        bridge_called = True
        _append_bridge(root, "completed")
        return 0

    plan = CampaignPlan(
        waves=(
            CampaignWavePlan(
                "A",
                (
                    CampaignRunPlan("A1", root, ("reason", "A1"), ("bridge", "A1"), run_manifest=authority),
                ),
            ),
        )
    )

    index = CampaignCoordinator(runner=runner, verifier=lambda _: _report()).run(plan)

    assert bridge_called is True
    record = index.waves[0].runs[0]
    assert record.bridge_decision == "executed"
    assert record.audit.reasoning_terminal.state == "completed"
    assert record.audit.bridge_terminal.state == "completed"
    assert record.audit.classification == RootClassification.OPERATIONAL_FAILURE


def test_run_result_v2_bridge_eligibility_is_honoured(tmp_path):
    root = tmp_path / "A1"
    authority = _manifest_authority(tmp_path)
    bridge_called = False

    def runner(command, _cwd):
        nonlocal bridge_called
        if command[0] == "reason":
            root.mkdir(parents=True, exist_ok=True)
            _bind_manifest(root, authority)
            (root / "run-result.json").write_text(
                json.dumps(
                    {
                        "schema": "deepreason-run-result-v2",
                        "state": "completed",
                        "canonical_bridge_eligible": False,
                    }
                ),
                encoding="utf-8",
            )
            (root / "log.jsonl").touch()
        else:
            bridge_called = True
        return 0

    plan = CampaignPlan(
        waves=(
            CampaignWavePlan(
                "A",
                (
                    CampaignRunPlan(
                        "A1", root, ("reason", "A1"), ("bridge", "A1"),
                        run_manifest=authority,
                    ),
                ),
            ),
        )
    )

    index = CampaignCoordinator(runner=runner, verifier=lambda _: _report()).run(plan)

    record = index.waves[0].runs[0]
    assert bridge_called is False
    assert record.bridge_decision == "skipped_not_bridge_eligible"
    assert record.audit.canonical_bridge_eligible is False


def test_bridge_inspection_tolerates_torn_final_append(tmp_path):
    root = tmp_path / "run"
    _write_result(root, "completed")
    _append_bridge(root, "completed", sequence=2)
    with (root / "log.jsonl").open("ab") as handle:
        handle.write(b'{"seq":3,"rule":"Bridge"')

    terminal, findings = inspect_bridge_terminal(root)

    assert terminal.state == "completed"
    assert terminal.sequence == 2
    assert findings == ()


def test_qualification_plan_rejects_experimental_v5(tmp_path):
    plan = campaign_plan_from_mapping(
        {
            "schema": "campaign.plan.v2",
            "qualification": True,
            "waves": [
                {
                    "id": "A",
                    "runs": [
                        {
                            "id": "A1",
                            "root": "A1",
                            "reasoning_command": [
                                "deepreason",
                                "reason",
                                "--experimental-v5",
                            ],
                        }
                    ],
                }
            ],
        },
        base_directory=tmp_path,
    )

    with pytest.raises(ValueError, match="qualification campaigns"):
        CampaignCoordinator(verifier=lambda _: _report()).run(plan)


def test_cross_root_scan_reads_log_jsonl_not_events_jsonl(tmp_path):
    root_a = tmp_path / "A"
    root_b = tmp_path / "B"
    _write_result(root_a, "completed")
    _write_result(root_b, "completed")
    (root_a / "events.jsonl").write_text(str(root_b.resolve()), encoding="utf-8")
    plan = CampaignPlan(
        waves=(
            CampaignWavePlan(
                "A",
                (
                    CampaignRunPlan("A", root_a),
                    CampaignRunPlan("B", root_b),
                ),
            ),
        )
    )

    index = CampaignCoordinator(verifier=lambda _: _report()).run(plan)

    assert all(
        record.audit.classification == RootClassification.COMPLETE
        for record in index.waves[0].runs
    )

    (root_a / "log.jsonl").write_text(
        json.dumps({"foreign_root": str(root_b.resolve())}) + "\n",
        encoding="utf-8",
    )
    index = CampaignCoordinator(verifier=lambda _: _report()).run(plan)
    assert index.waves[0].runs[0].audit.classification == RootClassification.SECURITY_FAILURE
def _write_v6_result_v2(
    root: Path, *, eligible: bool = True, manifest: Path | None = None
) -> None:
    root.mkdir(parents=True, exist_ok=True)
    if manifest is not None:
        _bind_manifest(root, manifest)
    valid = bool(eligible)
    payload = {
        "schema": "deepreason-run-result-v2",
        "state": "completed",
        "workload": "text",
        "verification": {
            "schema": "verification.summary.v2",
            "valid": valid,
            "integrity_valid": valid,
            "security_valid": True,
            "completion_satisfied": True,
            "epistemic_checks_passed": True,
            "operational_checks_passed": True,
            "finding_counts": {
                "integrity": 0 if valid else 1,
                "security": 0,
                "completion": 0,
                "epistemic": 0,
                "operational": 0,
            },
        },
        "completion_status": "satisfied",
        "canonical_bridge_eligible": valid,
    }
    (root / "run-result.json").write_text(
        json.dumps(payload),
        encoding="utf-8",
    )
    (root / "log.jsonl").touch()


def test_v6_campaign_rejects_v1_result_before_auto_bridge(tmp_path):
    root = tmp_path / "v6-v1"
    authority = _manifest_authority(tmp_path, version=6)
    bridge_called = False


    def runner(command, _cwd):
        nonlocal bridge_called
        if command[0] == "reason":
            _write_result(root, "completed", manifest=authority)
        else:
            bridge_called = True
        return 0

    plan = CampaignPlan(
        qualification=True,
        waves=(
            CampaignWavePlan(
                "A",
                (
                    CampaignRunPlan(
                        "A1", root, ("reason", "A1"), ("bridge", "A1"),
                        run_manifest=authority,
                    ),
                ),
            ),
        )
    )

    index = CampaignCoordinator(runner=runner, verifier=lambda _: _report()).run(plan)

    record = index.waves[0].runs[0]
    assert bridge_called is False
    assert record.bridge_decision == "skipped_not_bridge_eligible"
    assert record.audit.canonical_bridge_eligible is False


def test_v6_campaign_uses_report_before_self_asserted_auto_bridge(tmp_path):
    root = tmp_path / "v6-self-asserted"
    authority = _manifest_authority(tmp_path, version=6)
    order: list[str] = []


    def runner(command, _cwd):
        if command[0] == "reason":
            order.append("reason")
            _write_v6_result_v2(root, manifest=authority)
        else:
            order.append("bridge")
        return 0

    def verifier(_root):
        order.append("verify")
        return _report(
            integrity_valid=False,
            integrity=[
                {
                    "channel": "integrity",
                    "check": "post-terminal-history",
                    "detail": "history changed after the terminal summary was written",
                    "source": "verify_root_report",
                }
            ],
        )

    plan = CampaignPlan(
        qualification=True,
        waves=(
            CampaignWavePlan(
                "A",
                (
                    CampaignRunPlan(
                        "A1", root, ("reason", "A1"), ("bridge", "A1"),
                        run_manifest=authority,
                    ),
                ),
            ),
        )
    )

    index = CampaignCoordinator(runner=runner, verifier=verifier).run(plan)

    record = index.waves[0].runs[0]
    assert order[0:2] == ["reason", "verify"]
    assert "bridge" not in order
    assert record.bridge_decision == "skipped_not_bridge_eligible"
    assert record.audit.classification == RootClassification.INTEGRITY_FAILURE
    assert record.audit.canonical_bridge_eligible is False


def test_declared_v5_manifest_cannot_authorize_v6_root_or_auto_bridge(tmp_path):
    root = tmp_path / "A1"
    later_root = tmp_path / "B1"
    declared_v5 = _manifest_authority(tmp_path, version=5)
    actual_v6 = _manifest_authority(tmp_path, version=6)
    bridge_calls = 0
    reasoning_calls: list[str] = []

    def runner(command, _cwd):
        nonlocal bridge_calls
        phase, run_id = command
        if phase == "bridge":
            bridge_calls += 1
            return 0
        reasoning_calls.append(run_id)
        if run_id == "A1":
            _write_v6_result_v2(root, manifest=actual_v6)
        else:
            _write_result(later_root, "completed", manifest=declared_v5)
        return 0

    plan = CampaignPlan(
        waves=(
            CampaignWavePlan(
                "A",
                (
                    CampaignRunPlan(
                        "A1",
                        root,
                        ("reason", "A1"),
                        ("bridge", "A1"),
                        run_manifest=declared_v5,
                    ),
                ),
            ),
            CampaignWavePlan(
                "B",
                (
                    CampaignRunPlan(
                        "B1",
                        later_root,
                        ("reason", "B1"),
                        run_manifest=declared_v5,
                    ),
                ),
            ),
        )
    )

    index = CampaignCoordinator(runner=runner, verifier=lambda _: _report()).run(plan)

    record = index.waves[0].runs[0]
    assert reasoning_calls == ["A1"]
    assert bridge_calls == 0
    assert record.bridge_decision == "skipped_not_bridge_eligible"
    assert record.audit.classification == RootClassification.SECURITY_FAILURE
    assert record.audit.canonical_bridge_eligible is False
    assert any(
        finding.check == CAMPAIGN_MANIFEST_AUTHORITY_MISMATCH
        for finding in record.audit.dimensions.security
    )
    assert index.systemic_stop is True
    assert index.waves[1].state == "suppressed"


def test_runs_cannot_borrow_each_others_declared_manifest_authority(tmp_path):
    roots = {"A1": tmp_path / "A1", "A2": tmp_path / "A2"}
    declared_v5 = _manifest_authority(tmp_path, version=5)
    declared_v6 = _manifest_authority(tmp_path, version=6)
    bridge_calls: list[str] = []

    def runner(command, _cwd):
        phase, run_id = command
        if phase == "bridge":
            bridge_calls.append(run_id)
            return 0
        if run_id == "A1":
            _write_v6_result_v2(roots[run_id], manifest=declared_v6)
        else:
            _write_result(roots[run_id], "completed", manifest=declared_v5)
        return 0

    plan = CampaignPlan(
        qualification=True,
        waves=(
            CampaignWavePlan(
                "A",
                (
                    CampaignRunPlan(
                        "A1",
                        roots["A1"],
                        ("reason", "A1"),
                        ("bridge", "A1"),
                        run_manifest=declared_v5,
                    ),
                    CampaignRunPlan(
                        "A2",
                        roots["A2"],
                        ("reason", "A2"),
                        ("bridge", "A2"),
                        run_manifest=declared_v6,
                    ),
                ),
            ),
        )
    )

    index = CampaignCoordinator(runner=runner, verifier=lambda _: _report()).run(plan)

    assert bridge_calls == []
    for record in index.waves[0].runs:
        assert record.audit.classification == RootClassification.SECURITY_FAILURE
        assert record.audit.canonical_bridge_eligible is False
        assert any(
            finding.check == CAMPAIGN_MANIFEST_AUTHORITY_MISMATCH
            for finding in record.audit.dimensions.security
        )


def test_matched_per_run_manifest_remains_eligible_under_existing_rules(tmp_path):
    root = tmp_path / "A1"
    authority = _manifest_authority(tmp_path)
    bridge_calls = 0

    def runner(command, _cwd):
        nonlocal bridge_calls
        if command[0] == "reason":
            _write_result(root, "completed", manifest=authority)
        else:
            bridge_calls += 1
            _append_bridge(root, "completed")
        return 0

    plan = CampaignPlan(
        waves=(
            CampaignWavePlan(
                "A",
                (
                    CampaignRunPlan(
                        "A1",
                        root,
                        ("reason", "A1"),
                        ("bridge", "A1"),
                        run_manifest=authority,
                    ),
                ),
            ),
        )
    )

    index = CampaignCoordinator(runner=runner, verifier=lambda _: _report()).run(plan)

    record = index.waves[0].runs[0]
    assert bridge_calls == 1
    assert record.bridge_decision == "executed"
    assert record.audit.classification == RootClassification.COMPLETE
    assert record.audit.canonical_bridge_eligible is True


@pytest.mark.parametrize("bound_value", [None, "unreadable"], ids=["missing", "unreadable"])
def test_missing_or_unreadable_bound_manifest_fails_closed(tmp_path, bound_value):
    root = tmp_path / "A1"
    authority = _manifest_authority(tmp_path)
    bridge_calls = 0

    def runner(command, _cwd):
        nonlocal bridge_calls
        if command[0] == "reason":
            _write_result(root, "completed")
            if bound_value is not None:
                (root / MANIFEST_NAME).write_text(bound_value, encoding="utf-8")
        else:
            bridge_calls += 1
        return 0

    plan = CampaignPlan(
        waves=(
            CampaignWavePlan(
                "A",
                (
                    CampaignRunPlan(
                        "A1",
                        root,
                        ("reason", "A1"),
                        ("bridge", "A1"),
                        run_manifest=authority,
                    ),
                ),
            ),
        )
    )

    index = CampaignCoordinator(runner=runner, verifier=lambda _: _report()).run(plan)

    record = index.waves[0].runs[0]
    assert bridge_calls == 0
    assert record.bridge_decision == "skipped_not_bridge_eligible"
    assert record.audit.classification == RootClassification.SECURITY_FAILURE
    assert record.audit.canonical_bridge_eligible is False
    assert any(
        finding.check == CAMPAIGN_MANIFEST_AUTHORITY_MISMATCH
        for finding in record.audit.dimensions.security
    )



def test_malformed_bound_manifest_fails_closed_through_canonical_loader(tmp_path):
    root = tmp_path / "A1"
    later_root = tmp_path / "B1"
    authority = _manifest_authority(tmp_path)
    bridge_calls = 0
    reasoning_calls: list[str] = []

    def runner(command, _cwd):
        nonlocal bridge_calls
        phase, run_id = command
        if phase == "bridge":
            bridge_calls += 1
            return 0
        reasoning_calls.append(run_id)
        if run_id == "A1":
            _write_result(root, "completed")
            (root / MANIFEST_NAME).write_bytes(b'{"schema":')
            with pytest.raises(RunManifestError):
                canonical_load_run_manifest(root / MANIFEST_NAME)
        else:
            _write_result(later_root, "completed", manifest=authority)
        return 0

    plan = CampaignPlan(
        waves=(
            CampaignWavePlan(
                "A",
                (
                    CampaignRunPlan(
                        "A1",
                        root,
                        ("reason", "A1"),
                        ("bridge", "A1"),
                        run_manifest=authority,
                    ),
                ),
            ),
            CampaignWavePlan(
                "B",
                (
                    CampaignRunPlan(
                        "B1",
                        later_root,
                        ("reason", "B1"),
                        run_manifest=authority,
                    ),
                ),
            ),
        )
    )

    index = CampaignCoordinator(runner=runner, verifier=lambda _: _report()).run(plan)

    record = index.waves[0].runs[0]
    assert reasoning_calls == ["A1"]
    assert bridge_calls == 0
    assert record.bridge_decision == "skipped_not_bridge_eligible"
    assert record.audit.classification == RootClassification.SECURITY_FAILURE
    assert record.audit.canonical_bridge_eligible is False
    assert any(
        finding.check == CAMPAIGN_MANIFEST_AUTHORITY_MISMATCH
        for finding in record.audit.dimensions.security
    )
    assert index.systemic_stop is True
    assert index.waves[1].state == "suppressed"


def _direct_campaign_plan(*runs: CampaignRunPlan) -> CampaignPlan:
    return CampaignPlan(waves=(CampaignWavePlan("A", tuple(runs)),))


def _assert_direct_plan_rejected_before_runner(
    plan: CampaignPlan, match: str
) -> None:
    calls: list[tuple[str, ...]] = []

    def runner(command, _cwd):
        calls.append(tuple(command))
        return 0

    with pytest.raises(ValueError, match=match):
        CampaignCoordinator(runner=runner).run(plan)

    assert calls == []


def test_direct_plan_duplicate_run_ids_rejected_before_commands_are_keyed(tmp_path):
    authority = _manifest_authority(tmp_path)
    plan = _direct_campaign_plan(
        CampaignRunPlan(
            "same",
            tmp_path / "first",
            ("reason", "first"),
            run_manifest=authority,
        ),
        CampaignRunPlan(
            "same",
            tmp_path / "second",
            ("reason", "second"),
            run_manifest=authority,
        ),
    )

    _assert_direct_plan_rejected_before_runner(plan, "globally unique")


def test_direct_plan_equivalent_roots_rejected_before_runner(tmp_path):
    authority = _manifest_authority(tmp_path)
    root = tmp_path / "same-root"
    plan = _direct_campaign_plan(
        CampaignRunPlan(
            "A1", root, ("reason", "A1"), run_manifest=authority
        ),
        CampaignRunPlan(
            "A2",
            tmp_path / "different" / ".." / "same-root",
            ("reason", "A2"),
            run_manifest=authority,
        ),
    )

    _assert_direct_plan_rejected_before_runner(plan, "roots must be globally unique")


@pytest.mark.skipif(
    os.name != "nt", reason="requires Windows case-insensitive path identity"
)
def test_direct_plan_case_varied_windows_roots_rejected_before_runner(tmp_path):
    authority = _manifest_authority(tmp_path)
    root = tmp_path / "CaseRoot"
    plan = _direct_campaign_plan(
        CampaignRunPlan(
            "A1", root, ("reason", "A1"), run_manifest=authority
        ),
        CampaignRunPlan(
            "A2",
            root.with_name(root.name.swapcase()),
            ("reason", "A2"),
            run_manifest=authority,
        ),
    )

    _assert_direct_plan_rejected_before_runner(plan, "roots must be globally unique")


def test_direct_plan_ancestor_descendant_roots_rejected_before_runner(tmp_path):
    authority = _manifest_authority(tmp_path)
    parent = tmp_path / "parent"
    plan = _direct_campaign_plan(
        CampaignRunPlan(
            "A1", parent, ("reason", "A1"), run_manifest=authority
        ),
        CampaignRunPlan(
            "A2",
            parent / "child",
            ("reason", "A2"),
            run_manifest=authority,
        ),
    )

    _assert_direct_plan_rejected_before_runner(
        plan, "ancestors or descendants"
    )


def test_direct_plan_with_disjoint_roots_runs_normally(tmp_path):
    authority = _manifest_authority(tmp_path)
    roots = {"A1": tmp_path / "A1", "A2": tmp_path / "A2"}
    calls: list[tuple[str, ...]] = []

    def runner(command, _cwd):
        calls.append(tuple(command))
        _write_result(roots[command[1]], "completed", manifest=authority)
        return 0

    plan = _direct_campaign_plan(
        CampaignRunPlan(
            "A1", roots["A1"], ("reason", "A1"), run_manifest=authority
        ),
        CampaignRunPlan(
            "A2", roots["A2"], ("reason", "A2"), run_manifest=authority
        ),
    )

    index = CampaignCoordinator(runner=runner, verifier=lambda _: _report()).run(plan)

    assert sorted(calls) == [("reason", "A1"), ("reason", "A2")]
    assert index.systemic_stop is False
    assert index.waves[0].state == "completed"
    assert {record.run_id for record in index.waves[0].runs} == {"A1", "A2"}


def _run_foreign_root_scan_case(tmp_path, write_log):
    roots = {"A1": tmp_path / "A1", "B1": tmp_path / "B1"}
    authority = _manifest_authority(tmp_path)
    bridge_calls: list[str] = []
    reasoning_calls: list[str] = []

    def runner(command, _cwd):
        phase, run_id = command
        if phase == "bridge":
            bridge_calls.append(run_id)
            _append_bridge(roots[run_id], "completed")
            return 0
        reasoning_calls.append(run_id)
        _write_result(roots[run_id], "completed", manifest=authority)
        if run_id == "A1":
            write_log(roots[run_id] / "log.jsonl", roots["B1"])
        return 0

    plan = CampaignPlan(
        waves=(
            CampaignWavePlan(
                "A",
                (
                    CampaignRunPlan(
                        "A1",
                        roots["A1"],
                        ("reason", "A1"),
                        ("bridge", "A1"),
                        run_manifest=authority,
                    ),
                ),
            ),
            CampaignWavePlan(
                "B",
                (
                    CampaignRunPlan(
                        "B1",
                        roots["B1"],
                        ("reason", "B1"),
                        run_manifest=authority,
                    ),
                ),
            ),
        )
    )

    index = CampaignCoordinator(runner=runner, verifier=lambda _: _report()).run(plan)

    return index, bridge_calls, reasoning_calls


def _assert_foreign_root_scan_blocks_bridge(index, bridge_calls, reasoning_calls):
    record = index.waves[0].runs[0]
    assert reasoning_calls == ["A1"]
    assert bridge_calls == []
    assert record.bridge_decision == "skipped_not_bridge_eligible"
    assert record.audit.classification == RootClassification.SECURITY_FAILURE
    assert record.audit.canonical_bridge_eligible is False
    assert any(
        finding.channel == "security" and finding.check == "foreign_root_path"
        for finding in record.audit.dimensions.security
    )
    assert index.systemic_stop is True
    assert index.waves[1].state == "suppressed"


@pytest.mark.skipif(
    os.name != "nt", reason="requires Windows case-insensitive path identity"
)
def test_foreign_root_scan_blocks_case_varied_windows_reference(tmp_path):
    def write_log(log_path, foreign_root):
        reference = foreign_root.with_name(foreign_root.name.swapcase())
        log_path.write_text(
            json.dumps({"nested": {"path": str(reference)}}) + "\n",
            encoding="utf-8",
        )

    result = _run_foreign_root_scan_case(tmp_path, write_log)

    _assert_foreign_root_scan_blocks_bridge(*result)


def test_foreign_root_scan_blocks_equivalent_relative_reference(tmp_path):
    def write_log(log_path, foreign_root):
        reference = Path("..") / foreign_root.name / ".." / foreign_root.name
        log_path.write_text(
            json.dumps({"path": str(reference)}) + "\n", encoding="utf-8"
        )

    result = _run_foreign_root_scan_case(tmp_path, write_log)

    _assert_foreign_root_scan_blocks_bridge(*result)


def test_foreign_root_scan_fails_closed_on_unreadable_log(tmp_path, monkeypatch):
    original_open = Path.open

    def write_log(log_path, _foreign_root):
        def deny_log_open(path, *args, **kwargs):
            if path == log_path:
                raise OSError("access denied")
            return original_open(path, *args, **kwargs)

        monkeypatch.setattr(Path, "open", deny_log_open)

    result = _run_foreign_root_scan_case(tmp_path, write_log)

    _assert_foreign_root_scan_blocks_bridge(*result)


def test_foreign_root_scan_fails_closed_on_invalid_utf8(tmp_path):
    def write_log(log_path, _foreign_root):
        log_path.write_bytes(b'{"path":"\xff"}\n')

    result = _run_foreign_root_scan_case(tmp_path, write_log)

    _assert_foreign_root_scan_blocks_bridge(*result)


def test_foreign_root_scan_fails_closed_on_malformed_jsonl(tmp_path):
    def write_log(log_path, _foreign_root):
        log_path.write_bytes(b'{"path":\n')

    result = _run_foreign_root_scan_case(tmp_path, write_log)

    _assert_foreign_root_scan_blocks_bridge(*result)


def test_foreign_root_scan_fails_closed_on_oversized_log(tmp_path, monkeypatch):
    monkeypatch.setattr(
        "deepreason.experiments.campaign._MAX_QUALIFICATION_REPORT_BYTES", 64
    )

    def write_log(log_path, _foreign_root):
        log_path.write_bytes(b'{"note":"' + b"x" * 64 + b'"}\\n')

    result = _run_foreign_root_scan_case(tmp_path, write_log)

    _assert_foreign_root_scan_blocks_bridge(*result)


def test_foreign_root_scan_avoids_component_prefix_false_positive(tmp_path):
    roots = {"A1": tmp_path / "a", "B1": tmp_path / "ab"}
    authority = _manifest_authority(tmp_path)
    bridge_calls: list[str] = []
    reasoning_calls: list[str] = []

    def runner(command, _cwd):
        phase, run_id = command
        if phase == "bridge":
            bridge_calls.append(run_id)
            _append_bridge(roots[run_id], "completed")
            return 0
        reasoning_calls.append(run_id)
        _write_result(roots[run_id], "completed", manifest=authority)
        if run_id == "A1":
            (roots[run_id] / "log.jsonl").write_text(
                json.dumps({"path": str(roots[run_id].resolve())}) + "\n",
                encoding="utf-8",
            )
        return 0

    plan = CampaignPlan(
        waves=(
            CampaignWavePlan(
                "A",
                (
                    CampaignRunPlan(
                        "A1",
                        roots["A1"],
                        ("reason", "A1"),
                        ("bridge", "A1"),
                        run_manifest=authority,
                    ),
                ),
            ),
            CampaignWavePlan(
                "B",
                (
                    CampaignRunPlan(
                        "B1",
                        roots["B1"],
                        ("reason", "B1"),
                        run_manifest=authority,
                    ),
                ),
            ),
        )
    )

    index = CampaignCoordinator(runner=runner, verifier=lambda _: _report()).run(plan)

    assert bridge_calls == ["A1"]
    assert reasoning_calls == ["A1", "B1"]
    assert index.systemic_stop is False
    assert index.waves[0].runs[0].audit.classification == RootClassification.COMPLETE


def test_foreign_root_scan_allows_clean_log_to_bridge(tmp_path):
    root = tmp_path / "A1"
    authority = _manifest_authority(tmp_path)
    bridge_calls = 0

    def runner(command, _cwd):
        nonlocal bridge_calls
        if command[0] == "bridge":
            bridge_calls += 1
            _append_bridge(root, "completed")
        else:
            _write_result(root, "completed", manifest=authority)
        return 0

    plan = CampaignPlan(
        waves=(
            CampaignWavePlan(
                "A",
                (
                    CampaignRunPlan(
                        "A1",
                        root,
                        ("reason", "A1"),
                        ("bridge", "A1"),
                        run_manifest=authority,
                    ),
                ),
            ),
        )
    )

    index = CampaignCoordinator(runner=runner, verifier=lambda _: _report()).run(plan)

    assert bridge_calls == 1
    assert index.systemic_stop is False
    assert index.waves[0].runs[0].bridge_decision == "executed"
    assert index.waves[0].runs[0].audit.classification == RootClassification.COMPLETE
