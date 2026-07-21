"""Honest replay-derived reporting for final route-seat capability failure."""

from __future__ import annotations

from copy import deepcopy
import json

import pytest

from deepreason.application.models import (
    ModelExecutionSummaryV1,
    RunResultV2,
    derive_model_execution_summary,
)
from deepreason.application.bridge import preflight_canonical_bridge
from deepreason.application.text_runs import _v6_run_result
from deepreason.canonical import canonical_json
from deepreason.config import Config
from deepreason.harness import Harness
from deepreason.invariants import verify_root
from deepreason.llm.budget import TokenMeter
from deepreason.report import eval_report
from deepreason.runtime.stop import StopMetrics, StopPolicy, write_stop_record
from deepreason.runtime.progress import _atomic_json
from deepreason.verification.report import verify_root_report
from deepreason.workflow.transaction_service import InquiryTransactionService
from tests.test_v6_compact_recovery_transition import _exhaust
from tests.test_v6_insufficient_capability_terminal import _exhaust_minimal_block


def _summary(harness, manifest, *, event_horizon_seq=None):
    return derive_model_execution_summary(
        harness,
        manifest,
        event_horizon_seq=event_horizon_seq,
    ).model_dump(mode="json", by_alias=True)


def _durable_stop(harness, *, reason):
    policy = StopPolicy()
    metrics = StopMetrics(cycle=0)
    event_seq = harness._next_seq
    event = harness.record_measure(
        inputs=[
            "run-stop",
            policy.digest,
            json.dumps(metrics.model_dump(mode="json"), sort_keys=True),
            reason,
            str(event_seq),
        ]
    )
    assert event.seq == event_seq
    return write_stop_record(
        harness.root,
        reason=reason,
        policy=policy,
        metrics=metrics,
        event_seq=event_seq,
    )


def test_insufficient_capability_projection_preserves_strong_and_atomic_truth(
    tmp_path,
):
    root = tmp_path / "insufficient-report"
    manifest, service, adapter, _rendered = _exhaust_minimal_block(root)

    summary = _summary(service.harness, manifest)
    assert len(summary["insufficient_capability_routes"]) == 1
    outcome = summary["insufficient_capability_routes"][0]
    work = tuple(service.harness.workflow_state.transaction_work.values())
    assert outcome["outcome"] == "insufficient_capability"
    assert outcome["reason"] == "smallest_authorized_contract_schema_exhausted"
    assert outcome["triggering_status"] == "schema_exhausted"
    assert outcome["work_id"] == work[-1].preparation.id
    assert outcome["terminal_ref"] == work[-1].terminal.id
    assert outcome["attempted_work_ids"] == [
        item.preparation.id for item in work
    ]
    assert outcome["attempted_contract_ids"] == [
        "scratch.block.compact.v1",
        "scratch.block.compact.v1",
        "scratch.block.minimal.v1",
    ]
    assert outcome["final_contract_id"] == "scratch.block.minimal.v1"
    assert outcome["maximum_schema_repairs"] == 0
    assert outcome["maximum_provider_calls"] == 1
    assert outcome["observed_provider_calls"] == 1
    assert outcome["retry_failed_work"] is False
    assert len(outcome["decomposition_transition_refs"]) == 1
    assert len(outcome["compact_recovery_transition_refs"]) == 1
    assert work[-1].terminal.status == "schema_exhausted"
    assert adapter.meter.calls == 3

    decomposition = summary["contract_decompositions"][0]
    assert decomposition["source_status"] == "schema_exhausted"
    assert decomposition["source_failure_preserved"] is True
    assert decomposition["atomic_contract_id"] == "scratch.block.minimal.v1"
    assert decomposition["completion_ref"] is None
    assert decomposition["atomic_work_attempts"] == [
        {
            "schema": "atomic-work-attempt-projection.v1",
            "work_id": work[-1].preparation.id,
            "contract_id": "scratch.block.minimal.v1",
            "child_key": "scratch-block-minimal",
            "child_index": 0,
            "repair_index": 0,
            "work_kind": "atomic_child",
            "parent_work_id": None,
            "terminal_status": "schema_exhausted",
            "semantic_admission_ref": work[-1].terminal.semantic_admission_ref,
            "provider_attempt_count": 1,
        }
    ]

    restarted = Harness(root, read_only=True)
    assert canonical_json(summary) == canonical_json(_summary(restarted, manifest))
    process = eval_report(service.harness, Config())["process"]
    assert process["model_execution"] == summary
    invariants = verify_root(root)
    assert invariants["stats"]["process"]["model_execution"] == summary


def test_terminal_result_rejects_durable_activity_after_stop_horizon(tmp_path):
    root = tmp_path / "terminal-horizon"
    manifest, service, _adapter, _rendered = _exhaust_minimal_block(root)
    stop = _durable_stop(service.harness, reason="completed")
    horizon = stop["event_seq"]
    result = _v6_run_result(
        root,
        manifest,
        {
            "schema": "deepreason-run-result-v1",
            "state": "completed",
            "workload": "text",
            "stop": stop,
        },
        harness=service.harness,
    )
    assert result["state"] == "completed"
    assert result["model_execution"]["event_horizon_seq"] == horizon
    assert len(result["model_execution"]["insufficient_capability_routes"]) == 1
    _atomic_json(root / "run-result.json", result)

    service.harness.record_measure(inputs=["later-unrelated-route-activity"])
    findings = verify_root_report(root).integrity
    assert [
        item
        for item in findings
        if item.check in {"model-execution-summary", "terminal-authority"}
    ]


def _completed_terminal(root):
    manifest, service, adapter, _rendered = _exhaust_minimal_block(root)
    stop = _durable_stop(service.harness, reason="completed")
    result = _v6_run_result(
        root,
        manifest,
        {
            "schema": "deepreason-run-result-v1",
            "state": "completed",
            "workload": "text",
            "stop": stop,
        },
        harness=service.harness,
    )
    _atomic_json(root / "run-result.json", result)
    return manifest, service, adapter, result


def _root_bytes(root):
    return {
        path.relative_to(root).as_posix(): path.read_bytes()
        for path in sorted(root.rglob("*"))
        if path.is_file()
    }


def test_valid_current_completed_stop_authority_verifies_and_bridges(tmp_path):
    root = tmp_path / "valid-current-stop"
    manifest, _service, adapter, result = _completed_terminal(root)
    before = _root_bytes(root)
    provider_calls = adapter.meter.calls

    assert RunResultV2.model_validate(result).state == "completed"
    report = verify_root_report(root)
    assert report.integrity_valid
    assert report.security_valid
    preflight_canonical_bridge(root, manifest)

    assert adapter.meter.calls == provider_calls
    assert _root_bytes(root) == before


@pytest.mark.parametrize(
    "mutation",
    ["missing_stop", "missing_horizon", "missing_both", "missing_summary"],
)
def test_current_completed_stop_authority_is_required_for_verification_and_bridge(
    tmp_path,
    mutation,
):
    root = tmp_path / mutation
    manifest, _service, adapter, result = _completed_terminal(root)
    altered = deepcopy(result)
    if mutation in {"missing_stop", "missing_both"}:
        altered.pop("stop")
    if mutation in {"missing_horizon", "missing_both"}:
        altered["model_execution"].pop("event_horizon_seq")
    if mutation == "missing_both":
        altered.pop("terminal_commitment_ref")
    if mutation == "missing_summary":
        altered.pop("model_execution")

    if mutation == "missing_both":
        # The deliberately supported historical envelope remains readable, but
        # cannot classify itself as current authority at a bound v6 root.
        assert RunResultV2.model_validate(altered).state == "completed"
    elif mutation in {"missing_stop", "missing_horizon"}:
        with pytest.raises(ValueError):
            RunResultV2.model_validate(altered)

    (root / "run-result.json").write_text(
        json.dumps(altered, sort_keys=True), encoding="utf-8"
    )
    before = _root_bytes(root)
    provider_calls = adapter.meter.calls

    report = verify_root_report(root)
    assert not report.integrity_valid
    assert any(
        item.check in {
            "run-result",
            "model-execution-summary",
            "terminal-authority",
        }
        for item in report.integrity
    )
    with pytest.raises(ValueError, match="BRIDGE_(RUN_RESULT_INVALID|ROOT_AUTHORITY_INVALID)"):
        preflight_canonical_bridge(root, manifest)

    assert adapter.meter.calls == provider_calls
    assert _root_bytes(root) == before


def test_current_completed_stop_object_and_post_horizon_history_are_authority(
    tmp_path,
):
    missing_root = tmp_path / "missing-stop-object"
    manifest, _service, adapter, result = _completed_terminal(missing_root)
    stop = result["stop"]
    history = missing_root / "run-stops" / (
        f"{stop['event_seq']:012d}-{stop['digest']}.json"
    )
    history.unlink()
    before = _root_bytes(missing_root)
    provider_calls = adapter.meter.calls
    assert not verify_root_report(missing_root).integrity_valid
    with pytest.raises(ValueError, match="BRIDGE_ROOT_AUTHORITY_INVALID"):
        preflight_canonical_bridge(missing_root, manifest)
    assert adapter.meter.calls == provider_calls
    assert _root_bytes(missing_root) == before

    later_root = tmp_path / "post-horizon"
    manifest, service, adapter, _result = _completed_terminal(later_root)
    service.harness.record_measure(inputs=["durable-history-after-stop"])
    before = _root_bytes(later_root)
    provider_calls = adapter.meter.calls
    report = verify_root_report(later_root)
    assert not report.integrity_valid
    assert any(item.check == "terminal-authority" for item in report.integrity)
    with pytest.raises(ValueError, match="BRIDGE_ROOT_AUTHORITY_INVALID"):
        preflight_canonical_bridge(later_root, manifest)
    assert adapter.meter.calls == provider_calls
    assert _root_bytes(later_root) == before


@pytest.mark.parametrize(
    "missing_artifact",
    ["commitment", "result_draft", "checkpoint"],
)
def test_current_terminal_immutable_authority_artifacts_are_required(
    tmp_path,
    missing_artifact,
):
    root = tmp_path / f"missing-{missing_artifact}"
    manifest, _service, adapter, result = _completed_terminal(root)
    replayed = Harness(root, read_only=True)
    _schema, commitment = replayed.objects.get(
        result["terminal_commitment_ref"],
        schema="workflow-run-terminal-commitment-v1",
    )
    if missing_artifact == "commitment":
        target = replayed.objects._schema_path(
            "workflow-run-terminal-commitment-v1",
            commitment.id,
        )
    elif missing_artifact == "result_draft":
        target = replayed.objects._schema_path(
            "workflow-run-terminal-result-draft-v1",
            commitment.result_draft_ref,
        )
    else:
        target = root / "workflow-checkpoint.json"
    target.unlink()
    before = _root_bytes(root)
    provider_calls = adapter.meter.calls

    report = verify_root_report(root)
    assert not report.integrity_valid
    assert any(item.check == "terminal-authority" for item in report.integrity)
    with pytest.raises(ValueError, match="BRIDGE_ROOT_AUTHORITY_INVALID"):
        preflight_canonical_bridge(root, manifest)

    assert adapter.meter.calls == provider_calls
    assert _root_bytes(root) == before


def test_historical_terminal_is_readable_but_cannot_self_authorize_v6_bridge(
    tmp_path,
):
    from types import SimpleNamespace

    historical = {
        "schema": "deepreason-run-result-v2",
        "state": "completed",
        "workload": "text",
        "verification": {
            "schema": "verification.summary.v2",
            "valid": True,
            "integrity_valid": True,
            "security_valid": True,
            "completion_satisfied": True,
            "epistemic_checks_passed": True,
            "operational_checks_passed": True,
            "finding_counts": {
                "integrity": 0,
                "security": 0,
                "completion": 0,
                "epistemic": 0,
                "operational": 0,
            },
        },
        "completion_status": "satisfied",
        "canonical_bridge_eligible": True,
    }
    assert RunResultV2.model_validate(historical).state == "completed"
    (tmp_path / "run-result.json").write_text(
        json.dumps(historical, sort_keys=True), encoding="utf-8"
    )
    before = _root_bytes(tmp_path)
    with pytest.raises(ValueError, match="BRIDGE_ROOT_AUTHORITY_INVALID"):
        preflight_canonical_bridge(
            tmp_path,
            SimpleNamespace(
                schema_version=6,
                production_qualification_policy=None,
            ),
        )
    assert _root_bytes(tmp_path) == before


@pytest.mark.parametrize(
    "mutation",
    [
        "wrong_outcome_ref",
        "false_terminal",
        "foreign_decomposition",
        "foreign_classification",
        "omitted_outcome",
        "wrong_horizon",
        "missing_stop",
        "coordinated_lower_horizon",
    ],
)
def test_verification_rejects_tampered_capability_projection(tmp_path, mutation):
    root = tmp_path / mutation
    manifest, service, _adapter, _rendered = _exhaust_minimal_block(root)
    stop = _durable_stop(service.harness, reason="operational_failure")
    horizon = stop["event_seq"]
    result = _v6_run_result(
        root,
        manifest,
        {
            "schema": "deepreason-run-result-v1",
            "state": "failed",
            "workload": "text",
            "stop": stop,
        },
        harness=service.harness,
    )
    altered = deepcopy(result)
    route = altered["model_execution"]["insufficient_capability_routes"][0]
    if mutation == "wrong_outcome_ref":
        route["outcome_ref"] = "sha256:" + "f" * 64
    elif mutation == "false_terminal":
        route["triggering_status"] = "completed"
    elif mutation == "foreign_decomposition":
        route["decomposition_transition_refs"] = ["sha256:" + "e" * 64]
    elif mutation == "foreign_classification":
        route["classification_plan_ref"] = "sha256:" + "d" * 64
    elif mutation == "omitted_outcome":
        altered["model_execution"].pop("insufficient_capability_routes")
    elif mutation == "missing_stop":
        altered.pop("stop")
    elif mutation == "coordinated_lower_horizon":
        lower_horizon = horizon - 1
        altered["stop"]["event_seq"] = lower_horizon
        unsigned_stop = {
            key: value for key, value in altered["stop"].items() if key != "digest"
        }
        from deepreason.canonical import sha256_hex

        altered["stop"]["digest"] = sha256_hex(canonical_json(unsigned_stop))
        altered["model_execution"] = _summary(
            service.harness,
            manifest,
            event_horizon_seq=lower_horizon,
        )
    else:
        altered["model_execution"]["event_horizon_seq"] = horizon - 1
    (root / "run-result.json").write_text(
        json.dumps(altered, sort_keys=True), encoding="utf-8"
    )

    findings = verify_root_report(root).integrity
    assert any(
        item.check in {
            "run-result",
            "model-execution-summary",
            "terminal-authority",
        }
        for item in findings
    )


def test_summary_model_rejects_false_atomic_success_for_failed_smallest_contract(
    tmp_path,
):
    root = tmp_path / "false-atomic-success"
    manifest, service, _adapter, _rendered = _exhaust_minimal_block(root)
    summary = _summary(service.harness, manifest)
    altered = deepcopy(summary)
    decomposition = altered["contract_decompositions"][0]
    decomposition["completion_ref"] = "sha256:" + "a" * 64
    decomposition["child_work_ids"] = [
        altered["insufficient_capability_routes"][0]["work_id"]
    ]
    decomposition["child_semantic_admission_refs"] = [
        altered["insufficient_capability_routes"][0]["semantic_admission_ref"]
    ]

    with pytest.raises(ValueError):
        ModelExecutionSummaryV1.model_validate(altered)
