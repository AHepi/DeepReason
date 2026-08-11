"""Typed v6 work failures remain dimensional verification findings."""

from __future__ import annotations

from types import SimpleNamespace

from deepreason.llm.firewall import route_fingerprint
from deepreason.run_manifest import Route
from deepreason.verification.report import (
    _deferred_model_phase_findings,
    _transaction_findings,
)
from deepreason.workflow.models import RouteLeaseRefV1


def _item(status, *, issued=True, reason="test_reason"):
    return SimpleNamespace(
        preparation=SimpleNamespace(task_kind=SimpleNamespace(value="criticism")),
        issued=issued,
        terminal=(
            None
            if status is None
            else SimpleNamespace(status=status, reason_code=reason)
        ),
    )


def test_typed_work_terminals_separate_operations_from_completion(tmp_path, monkeypatch):
    work = {
        "sha256:" + "1" * 64: _item("schema_exhausted"),
        "sha256:" + "2" * 64: _item("transport_failed"),
        "sha256:" + "3" * 64: _item("budget_denied"),
        "sha256:" + "4" * 64: _item(None, issued=True),
        "sha256:" + "5" * 64: _item(None, issued=False),
        "sha256:" + "6" * 64: _item("completed"),
    }
    fake = SimpleNamespace(
        workflow_state=SimpleNamespace(transaction_work=work)
    )
    monkeypatch.setattr("deepreason.harness.Harness", lambda *_a, **_k: fake)

    findings = _transaction_findings(tmp_path)

    assert [item.channel for item in findings] == [
        "operational",
        "operational",
        "completion",
        "operational",
        "completion",
    ]
    assert all(item.check == "transaction-terminal" for item in findings)
    assert any("schema_exhausted" in item.detail for item in findings)
    assert any("budget_denied" in item.detail for item in findings)


def test_prepared_abandonment_is_completion_but_issued_abandonment_is_operational(
    tmp_path, monkeypatch
):
    work = {
        "sha256:" + "a" * 64: _item("abandoned", issued=False),
        "sha256:" + "b" * 64: _item("abandoned", issued=True),
    }
    fake = SimpleNamespace(
        workflow_state=SimpleNamespace(transaction_work=work)
    )
    monkeypatch.setattr("deepreason.harness.Harness", lambda *_a, **_k: fake)

    findings = _transaction_findings(tmp_path)

    assert [item.channel for item in findings] == ["completion", "operational"]

def test_prepared_budget_denial_still_checks_frozen_contract_authority(
    tmp_path, monkeypatch
):
    route = Route(
        endpoint_id="conjecturer-route",
        base_url="mock://conjecturer-route",
        model_id="offline-model",
        provider="mock",
        family="offline-family",
    )
    lease = RouteLeaseRefV1(
        role="conjecturer",
        seat=0,
        endpoint_id=route.endpoint_id,
        route_sha256=route_fingerprint(route),
    )
    work_id = "sha256:" + "c" * 64
    preparation = SimpleNamespace(
        manifest_digest="d" * 64,
        route_lease=lease,
        task_kind=SimpleNamespace(value="conjecture"),
        contract_id="conjecturer.turn.v5",
        task_payload_value={
            "schema": "conjecture.semantic-task.v2",
            "run_input_digest": "e" * 64,
        },
    )
    work = {
        work_id: SimpleNamespace(
            preparation=preparation,
            issued=False,
            terminal=SimpleNamespace(
                status="budget_denied", reason_code="token_budget_denied"
            ),
        )
    }
    manifest = SimpleNamespace(
        schema_version=6,
        sha256="d" * 64,
        roles={"conjecturer": (route,)},
        run_input_digest="e" * 64,
        criticism_policy=None,
        bridge_policy=SimpleNamespace(),
        control_plane_policy=SimpleNamespace(
            contract_versions=SimpleNamespace(
                conjecturer_turn_contract="conjecturer.turn.v6",
                batch_critic_contract="batch-critic.v2",
            ),
            school_execution=SimpleNamespace(
                mode="conditioning_only", bindings=()
            ),
            scratch_authoring=SimpleNamespace(enabled=False),
        ),
    )
    fake = SimpleNamespace(
        workflow_state=SimpleNamespace(transaction_work=work)
    )
    (tmp_path / "run-manifest.json").write_text("{}", encoding="utf-8")
    monkeypatch.setattr("deepreason.harness.Harness", lambda *_a, **_k: fake)
    monkeypatch.setattr(
        "deepreason.run_manifest.load_run_manifest", lambda *_a, **_k: manifest
    )

    findings = _transaction_findings(tmp_path)

    assert [item.channel for item in findings] == ["security", "completion"]
    authority = findings[0]
    assert authority.check == "transaction-authority"
    assert "conjecturer.turn.v5" in authority.detail
    assert "conjecturer.turn.v6" in authority.detail


def test_v6_deferred_model_phase_is_completion_debt_and_malformed_is_integrity(
    tmp_path, monkeypatch
):
    events = (
        SimpleNamespace(
            seq=7,
            inputs=[
                "v6-model-phase-deferred.v1",
                "rubric-trial",
                "judge",
                "artifact-1",
                "criterion-1",
                "transaction-contract-unavailable",
            ],
        ),
        SimpleNamespace(
            seq=8,
            inputs=["v6-model-phase-deferred.v1", "truncated"],
        ),
    )
    fake = SimpleNamespace(log=SimpleNamespace(read=lambda: iter(events)))
    monkeypatch.setattr("deepreason.harness.Harness", lambda *_a, **_k: fake)

    findings = _deferred_model_phase_findings(tmp_path)

    assert [item.channel for item in findings] == ["completion", "integrity"]
    assert findings[0].check == "model-phase-deferred"
    assert "rubric-trial" in findings[0].detail
    assert "malformed" in findings[1].detail


def test_report_includes_signal_snapshot(tmp_path):
    """Part F Step 54 (R15): `verify_root_report`'s `stats` dict gains an
    additive `signal_snapshot` key carrying `signals_read.read_signal_
    snapshot`'s output -- not a new report shape, no change to the typed
    `VerificationReportV2` field set, so `deepreason status`/`report`
    surfaces it without any consumer needing a schema migration."""

    from deepreason.harness import Harness
    from deepreason.ontology.event import LLMCall
    from deepreason.verification.report import verify_root_report

    root = tmp_path / "run"
    harness = Harness(root)
    harness.record_measure(
        inputs=["config-critique:config_mistuned", "recommendation:x", "cited:1"]
    )
    prompt_ref = harness.blobs.put(b"prompt")
    raw_ref = harness.blobs.put(b'{"ok":true}')
    call = LLMCall(
        role="conjecturer",
        model="gemma4:31b",
        endpoint="https://gemma.invalid/v1",
        prompt_ref=prompt_ref,
        raw_ref=raw_ref,
        tokens=5,
        prompt_tokens=3,
        completion_tokens=2,
    )
    harness.record_llm_calls([call], "test-spend")

    report = verify_root_report(root, allow_missing_terminal=True)

    snapshot = report.stats["signal_snapshot"]
    assert snapshot["schema"] == "deepreason-signal-snapshot.v1"
    assert snapshot["config_critique"]["signal"] == "config-critique:config_mistuned"
    assert snapshot["deferred_model_phase_counts"] == {}
    assert snapshot["token_spend"] == {
        "prompt_tokens": 3,
        "completion_tokens": 2,
        "total": 5,
        "calls": 1,
    }
