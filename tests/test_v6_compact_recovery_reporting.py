"""Truthful v6 reporting for durable route-seat compact recovery."""

from __future__ import annotations

from copy import deepcopy
import json

import pytest

from deepreason.application.models import (
    ModelExecutionSummaryV1,
    RunResultV2,
    derive_model_execution_summary,
    run_result_exit_code,
)
from deepreason.application.bridge import preflight_canonical_bridge
from deepreason.application.text_runs import _v6_run_result
from deepreason.canonical import canonical_json
from deepreason.config import Config
from deepreason.harness import Harness
from deepreason.llm.budget import TokenMeter
from deepreason.report import eval_report
from deepreason.runtime.stop import StopMetrics, StopPolicy, write_stop_record
from deepreason.runtime.terminal_authority import derive_terminal_authority
from deepreason.verification.report import verify_root_report
from deepreason.workflow.transaction_service import InquiryTransactionService
from tests.test_v6_compact_recovery_runtime import (
    _adapter,
    _dispatch_conjecture,
)
from tests.test_v6_compact_recovery_transition import (
    _exhaust,
    _manifest,
    _persist_manifest,
)


def _root(tmp_path, *, profile="standard", historical_without_policy=False):
    manifest = _manifest(
        profile=profile,
        historical_without_policy=historical_without_policy,
    )
    _persist_manifest(manifest, tmp_path)
    return manifest, Harness(tmp_path)


def _summary(harness, manifest, *, event_horizon_seq=None) -> dict:
    return derive_model_execution_summary(
        harness,
        manifest,
        event_horizon_seq=event_horizon_seq,
    ).model_dump(
        mode="json", by_alias=True
    )


def _completed_stop(harness):
    policy = StopPolicy()
    metrics = StopMetrics(cycle=0)
    event_horizon = harness._next_seq
    event = harness.record_measure(
        inputs=[
            "run-stop",
            policy.digest,
            json.dumps(metrics.model_dump(mode="json"), sort_keys=True),
            "completed",
            str(event_horizon),
        ]
    )
    assert event.seq == event_horizon
    return write_stop_record(
        harness.root,
        reason="completed",
        policy=policy,
        metrics=metrics,
        event_seq=event.seq,
    )


def _root_bytes(root):
    return {
        path.relative_to(root).as_posix(): path.read_bytes()
        for path in sorted(root.rglob("*"))
        if path.is_file()
    }


def _transition_with_later_completion(tmp_path, *, profile="standard"):
    manifest, harness = _root(tmp_path, profile=profile)
    adapter, _endpoints = _adapter(
        harness,
        manifest,
        {
            ("conjecturer", 0): [
                '{"candidates":[{"content":"later compact result",'
                '"typicality":0.5}]}'
            ]
        },
    )
    trigger = _exhaust(
        InquiryTransactionService(harness, manifest, adapter.meter),
        trigger="schema-exhausted-trigger",
    )
    _prompt, contract, _output, call = _dispatch_conjecture(
        adapter,
        harness,
        manifest,
        trigger="subsequent-compact-completion",
    )
    return manifest, harness, trigger, contract, call


@pytest.mark.parametrize("profile", ["standard", "frontier"])
def test_strong_v6_without_transition_reports_base_only(tmp_path, profile):
    manifest, harness = _root(tmp_path / profile, profile=profile)

    summary = _summary(harness, manifest)
    assert summary["schema"] == "model-execution-summary.v1"
    assert summary["mode"] == "base_only"
    assert summary["base_profile"] == profile
    assert {
        route["base_profile"] for route in summary["route_seat_bases"]
    } == {profile}
    assert summary["recovery_routes"] == []


def test_base_compact_and_historical_policy_absence_are_honest(tmp_path):
    compact, compact_harness = _root(tmp_path / "compact", profile="compact")
    historical, historical_harness = _root(
        tmp_path / "historical",
        historical_without_policy=True,
    )

    assert _summary(compact_harness, compact)["mode"] == "base_compact"
    assert _summary(compact_harness, compact)["recovery_routes"] == []
    assert _summary(historical_harness, historical)["mode"] == "base_only"
    assert _summary(historical_harness, historical)["recovery_routes"] == []


def test_transition_without_later_call_reports_zero_and_restarts_identically(
    tmp_path,
):
    root = tmp_path / "no-later-call"
    manifest, harness = _root(root)
    _preparation, _attempt, admission, terminal = _exhaust(
        InquiryTransactionService(harness, manifest, TokenMeter(100_000)),
        trigger="no-later-call",
    )

    first = _summary(harness, manifest)
    route = first["recovery_routes"][0]
    assert first["mode"] == "route_seat_compact_recovery"
    assert route["triggering_status"] == "schema_exhausted"
    assert route["triggering_terminal_ref"] == terminal.id
    assert route["triggering_semantic_admission_ref"] == admission.id
    assert route["subsequent_compact_call_count"] == 0
    assert route["subsequent_compact_work_ids"] == []
    assert route["completed_compact_work_ids"] == []
    assert route["actual_contract_ids"] == []
    assert route["language"] == {
        "triggering_work": "schema-exhausted triggering work",
        "activation": "route-seat compact recovery activated",
        "subsequent_call": "subsequent compact-path call",
        "subsequent_completion": "subsequent compact-path completion",
    }

    reopened = Harness(root, read_only=True)
    second = _summary(reopened, manifest)
    assert canonical_json(first) == canonical_json(second)


def test_heterogeneous_bases_and_recovery_source_are_reported_exactly(tmp_path):
    manifest = _manifest(
        profile="standard",
        route_profiles={
            ("conjecturer", 0): "frontier",
            ("conjecturer", 1): "compact",
        },
    )
    root = tmp_path / "heterogeneous-report"
    _persist_manifest(manifest, root)
    harness = Harness(root)
    _exhaust(
        InquiryTransactionService(harness, manifest, TokenMeter(100_000)),
        seat=0,
        trigger="frontier-route-trigger",
    )

    summary = _summary(harness, manifest)
    bases = {
        (item["role"], item["seat"]): item["base_profile"]
        for item in summary["route_seat_bases"]
    }
    assert summary["mode"] == "route_seat_compact_recovery"
    assert summary["base_profile"] == "standard"
    assert bases[("conjecturer", 0)] == "frontier"
    assert bases[("conjecturer", 1)] == "compact"
    assert summary["recovery_routes"][0]["source_profile"] == "frontier"
    process = eval_report(harness, Config())["process"]
    assert set(process["profile_totals"]) == {"frontier"}
    assert process["profile_totals"]["frontier"]["calls"] == 1
    assert canonical_json(summary) == canonical_json(
        _summary(Harness(root, read_only=True), manifest)
    )


def test_later_compact_completion_reports_exact_seat_and_actual_contract(tmp_path):
    manifest, harness, trigger, contract, call = _transition_with_later_completion(
        tmp_path / "later"
    )

    summary = _summary(harness, manifest)
    assert len(summary["recovery_routes"]) == 1
    route = summary["recovery_routes"][0]
    assert (route["role"], route["seat"], route["endpoint_id"]) == (
        "conjecturer",
        0,
        "conjecturer-a",
    )
    assert route["subsequent_compact_call_count"] == 1
    assert route["subsequent_compact_work_ids"] == [call.work_order_id]
    assert route["actual_contract_ids"] == [contract.contract_id]
    assert route["completed_compact_work_ids"] == [call.work_order_id]
    assert route["triggering_work_id"] == trigger[0].id
    assert trigger[0].id not in route["completed_compact_work_ids"]
    assert all(
        (item["role"], item["seat"])
        not in {("conjecturer", 1), ("argumentative_critic", 0)}
        for item in summary["recovery_routes"]
    )


def test_multiple_route_projections_are_sorted_and_independently_scoped(tmp_path):
    manifest, harness = _root(tmp_path / "multiple")
    service = InquiryTransactionService(
        harness, manifest, TokenMeter(100_000)
    )
    _exhaust(service, seat=1, trigger="seat-one-first")
    _exhaust(
        service,
        role="argumentative_critic",
        trigger="other-role-second",
    )
    _exhaust(service, seat=0, trigger="seat-zero-third")

    routes = _summary(harness, manifest)["recovery_routes"]
    keys = [
        (item["role"], item["seat"], item["endpoint_id"], item["route_sha256"])
        for item in routes
    ]
    assert keys == sorted(keys)
    assert len(set(keys)) == 3
    assert all(item["subsequent_compact_call_count"] == 0 for item in routes)


def test_process_report_keeps_counters_and_adds_canonical_projection(tmp_path):
    manifest, harness, _trigger, contract, _call = _transition_with_later_completion(
        tmp_path / "process"
    )

    process = eval_report(harness, Config())["process"]
    assert process["transport_totals"]["compact_recovery_calls"] == 1
    assert process["transport_totals"]["profiles"] == {
        "compact": 1,
        "standard": 1,
    }
    assert process["transport_totals"]["contracts"] == {
        "conjecturer.turn.v6": 2,
    }
    assert contract.contract_id == "conjecturer.turn.v6"
    assert process["model_execution"] == _summary(harness, manifest)


def test_new_v6_result_contains_summary_without_changing_terminal_authority(
    tmp_path,
):
    root = tmp_path / "terminal"
    manifest, harness, _trigger, _contract, _call = (
        _transition_with_later_completion(root)
    )
    before = verify_root_report(root, allow_missing_terminal=True)
    stop = _completed_stop(harness)

    result = _v6_run_result(
        root,
        manifest,
        {
            "schema": "deepreason-run-result-v1",
            "state": "completed",
            "workload": "text",
            "survivors": [],
            "stop": stop,
        },
        harness=harness,
    )

    assert result["model_execution"] == _summary(
        harness,
        manifest,
        event_horizon_seq=stop["event_seq"],
    )
    assert result["completion_status"] == (
        "satisfied" if before.completion_satisfied else "incomplete"
    )
    assert result["verification"]["valid"] == before.valid
    assert result["canonical_bridge_eligible"] is before.valid
    assert run_result_exit_code(result) == (0 if before.valid else 5)


def test_run_result_model_rejects_false_compact_completion():
    summary = {
        "schema": "model-execution-summary.v1",
        "mode": "route_seat_compact_recovery",
        "base_profile": "standard",
        "recovery_routes": [
            {
                "schema": "compact-recovery-route-projection.v1",
                "transition_ref": "sha256:" + "1" * 64,
                "triggering_work_id": "sha256:" + "2" * 64,
                "triggering_terminal_ref": "sha256:" + "3" * 64,
                "triggering_semantic_admission_ref": "sha256:" + "4" * 64,
                "triggering_status": "schema_exhausted",
                "role": "conjecturer",
                "seat": 0,
                "endpoint_id": "route",
                "route_sha256": "5" * 64,
                "source_profile": "standard",
                "target_profile": "compact",
                "trigger": "schema_exhausted",
                "sticky": True,
                "applies_to": "all_subsequent_model_calls",
                "retry_failed_work": False,
                "subsequent_compact_call_count": 0,
                "subsequent_compact_work_ids": [],
                "actual_contract_ids": [],
                "completed_compact_work_ids": ["sha256:" + "2" * 64],
            }
        ],
    }

    with pytest.raises(ValueError, match="triggering work"):
        ModelExecutionSummaryV1.model_validate(summary)


@pytest.mark.parametrize(
    "mutation",
    [
        "wrong_trigger",
        "retry_failed_work",
        "base_only_with_route",
        "recovery_without_route",
        "base_compact_with_standard",
        "duplicate_route",
        "unsorted_routes",
        "duplicate_work",
        "duplicate_contract",
    ],
)
def test_summary_rejects_internal_contradictions(tmp_path, mutation):
    manifest, harness, _trigger, _contract, _call = (
        _transition_with_later_completion(tmp_path / mutation)
    )
    summary = _summary(harness, manifest)
    route = summary["recovery_routes"][0]
    if mutation == "wrong_trigger":
        route["triggering_status"] = "completed"
    elif mutation == "retry_failed_work":
        route["retry_failed_work"] = True
    elif mutation == "base_only_with_route":
        summary["mode"] = "base_only"
    elif mutation == "recovery_without_route":
        summary["recovery_routes"] = []
    elif mutation == "base_compact_with_standard":
        summary["mode"] = "base_compact"
    elif mutation == "duplicate_route":
        summary["recovery_routes"].append(deepcopy(route))
    elif mutation == "unsorted_routes":
        other = deepcopy(route)
        other["transition_ref"] = "sha256:" + "9" * 64
        other["triggering_work_id"] = "sha256:" + "8" * 64
        other["triggering_terminal_ref"] = "sha256:" + "7" * 64
        other["triggering_semantic_admission_ref"] = "sha256:" + "6" * 64
        other["seat"] = 1
        other["endpoint_id"] = "conjecturer-b"
        other["route_sha256"] = "5" * 64
        summary["recovery_routes"] = [other, route]
    elif mutation == "duplicate_work":
        work_id = route["subsequent_compact_work_ids"][0]
        route["subsequent_compact_call_count"] = 2
        route["subsequent_compact_work_ids"] = [work_id, work_id]
    else:
        contract_id = route["actual_contract_ids"][0]
        route["actual_contract_ids"] = [contract_id, contract_id]

    with pytest.raises(ValueError):
        ModelExecutionSummaryV1.model_validate(summary)


def test_historical_run_result_without_summary_remains_readable():
    payload = {
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
    assert RunResultV2.model_validate(payload).model_execution is None


def test_historical_policy_absent_terminal_may_omit_summary(tmp_path):
    root = tmp_path / "historical-terminal"
    _manifest_value, _harness = _root(
        root,
        historical_without_policy=True,
    )
    payload = {
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
    (root / "run-result.json").write_text(
        json.dumps(payload, sort_keys=True), encoding="utf-8"
    )

    assert not [
        item
        for item in verify_root_report(root).integrity
        if item.check == "model-execution-summary"
    ]


def test_verification_rejects_omitted_altered_and_false_completion_summaries(
    tmp_path,
    monkeypatch,
):
    root = tmp_path / "tamper"
    manifest, harness, _trigger, _contract, _call = (
        _transition_with_later_completion(root)
    )
    stop = _completed_stop(harness)
    correct = _v6_run_result(
        root,
        manifest,
        {
            "schema": "deepreason-run-result-v1",
            "state": "completed",
            "workload": "text",
            "stop": stop,
        },
        harness=harness,
    )

    (root / "run-result.json").write_bytes(canonical_json(correct) + b"\n")
    baseline_authority = derive_terminal_authority(root, manifest=manifest)
    assert baseline_authority.current_valid
    assert not [
        item
        for item in verify_root_report(root).integrity
        if item.check == "model-execution-summary"
    ]

    def forbidden_provider_call(*_args, **_kwargs):
        pytest.fail("bridge preflight reached a model provider")

    monkeypatch.setattr(
        "deepreason.llm.adapter.LLMAdapter.call",
        forbidden_provider_call,
    )

    def assert_current_committed_tamper_rejected(payload):
        (root / "run-result.json").write_bytes(
            canonical_json(payload) + b"\n"
        )
        before = _root_bytes(root)
        event_count = len(tuple(harness.log.read()))
        model_call_count = sum(
            event.llm is not None for event in harness.log.read()
        )

        authority = derive_terminal_authority(root, manifest=manifest)
        report = verify_root_report(root)
        assert not authority.current_valid
        assert authority.canonical_bridge_eligible is None
        assert not report.integrity_valid
        assert any(item.check == "terminal-authority" for item in report.integrity)
        assert not any(
            item.check == "model-execution-summary"
            for item in report.integrity
        )
        with pytest.raises(ValueError):
            preflight_canonical_bridge(root, manifest)

        assert _root_bytes(root) == before
        assert len(tuple(harness.log.read())) == event_count
        assert sum(
            event.llm is not None for event in harness.log.read()
        ) == model_call_count

    omitted = deepcopy(correct)
    omitted.pop("model_execution")
    assert_current_committed_tamper_rejected(omitted)

    altered = deepcopy(correct)
    altered["model_execution"]["recovery_routes"][0]["transition_ref"] = (
        "sha256:" + "f" * 64
    )
    assert_current_committed_tamper_rejected(altered)

    false_completion = deepcopy(correct)
    route = false_completion["model_execution"]["recovery_routes"][0]
    route["completed_compact_work_ids"] = [route["triggering_work_id"]]
    assert_current_committed_tamper_rejected(false_completion)
