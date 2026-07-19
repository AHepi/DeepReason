"""D0: one typed application boundary for CLI and MCP text runs."""

from __future__ import annotations

import inspect
import json

import pytest
from pydantic import ValidationError

from deepreason import mcp_server
from deepreason.application import (
    InspectTextRunIntentV1,
    RunStartedV1,
    StartTextRunIntentV1,
    TEXT_RUN_SERVICE,
    TEXT_RUN_WORKERS,
    TextRunTerminalResultV1,
)
from deepreason.application.text_runs import (
    TextRunApplicationService,
    TextRunWorkerRegistry,
)
from deepreason.cli import main as cli_module
from deepreason.cli.main import main as cli_main
from deepreason.config import Config
from deepreason.harness import Harness
from deepreason.locking import operator_locks
from deepreason.run_manifest import compile_run_manifest, write_run_manifest
from deepreason.workloads.text import spec_from_text


def _manifest(tmp_path):
    manifest = compile_run_manifest(
        Config(
            roles={
                "conjecturer": {
                    "endpoint": "https://application.invalid/v1",
                    "model": "application-model",
                    "provider": "fixture",
                    "family": "fixture",
                }
            }
        ),
        schema_version=2,
        workload_profile="text",
        rubric_policy="forbid",
        compiled_at="2026-07-16T00:00:00Z",
    )
    path, _ = write_run_manifest(manifest, tmp_path / "manifest.json")
    return manifest, path


def test_start_intent_is_strict_and_has_no_client_authority_fields(tmp_path):
    spec = spec_from_text("Why should clients share one application service?")
    payload = {
        "root": str(tmp_path / "run"),
        "workload": spec,
        "run_manifest_ref": str(tmp_path / "manifest.json"),
        "budget": {"cycles": 1, "token_budget": "unlimited"},
    }

    with pytest.raises(ValidationError, match="extra_forbidden"):
        StartTextRunIntentV1.model_validate(
            {**payload, "route": "model-authored"}
        )
    with pytest.raises(ValidationError, match="extra_forbidden"):
        StartTextRunIntentV1.model_validate(
            {**payload, "status": "accepted"}
        )
    with pytest.raises(ValidationError):
        StartTextRunIntentV1.model_validate(
            {**payload, "budget": {"cycles": True, "token_budget": 10}}
        )

    schema = json.dumps(StartTextRunIntentV1.model_json_schema(), sort_keys=True)
    assert all(
        forbidden not in schema
        for forbidden in ("route", "status", "raw_control", "guard_override")
    )


def test_cli_and_mcp_compile_the_same_start_intent(
    tmp_path, monkeypatch, capsys
):
    manifest, manifest_path = _manifest(tmp_path)
    root = tmp_path / "same-root"
    text = "Why should equivalent clients produce equivalent authority?"
    captured = []

    def fake_start(intent, **_kwargs):
        captured.append(intent)
        return RunStartedV1(
            root=str(root.resolve()), manifest_digest=manifest.sha256
        )

    monkeypatch.setattr(TEXT_RUN_SERVICE, "start", fake_start)
    monkeypatch.setattr(TEXT_RUN_SERVICE, "wait", lambda *_args, **_kwargs: None)
    monkeypatch.setattr(
        TEXT_RUN_SERVICE,
        "result",
        lambda _intent: TextRunTerminalResultV1(
            lifecycle="completed",
            payload={
                "schema": "deepreason-run-result-v1",
                "state": "completed",
                "workload": "text",
            },
        ),
    )

    mcp_server._start_run(
        {
            "root": str(root),
            "workload": "text",
            "problem": {"description": text},
            "run_manifest_ref": str(manifest_path),
            "budget": {"cycles": 12, "token_budget": 200_000},
        }
    )
    assert (
        cli_main(
            [
                "--root",
                str(root),
                "reason",
                "--text",
                text,
                "--run-manifest",
                str(manifest_path),
                "--cycles",
                "12",
                "--token-budget",
                "200000",
            ]
        )
        == 0
    )

    assert len(captured) == 2
    assert captured[0] == captured[1]
    assert json.loads(capsys.readouterr().out)["state"] == "completed"


@pytest.mark.parametrize(
    ("state", "verification", "expected"),
    [
        ("completed", None, 0),
        ("cancelled", None, 3),
        ("failed", None, 4),
        (
            "completed",
            {"integrity_valid": False, "security_valid": True},
            5,
        ),
    ],
)
def test_synchronous_cli_preserves_state_and_uses_terminal_exit_contract(
    tmp_path, monkeypatch, capsys, state, verification, expected
):
    manifest, manifest_path = _manifest(tmp_path)
    root = tmp_path / state
    payload = {
        "schema": "deepreason-run-result-v1",
        "state": state,
        "workload": "text",
    }
    if verification is not None:
        payload["verification"] = verification
    monkeypatch.setattr(
        TEXT_RUN_SERVICE,
        "start",
        lambda *_args, **_kwargs: RunStartedV1(
            root=str(root.resolve()), manifest_digest=manifest.sha256
        ),
    )
    monkeypatch.setattr(TEXT_RUN_SERVICE, "wait", lambda *_args, **_kwargs: None)
    monkeypatch.setattr(
        TEXT_RUN_SERVICE,
        "result",
        lambda _intent: TextRunTerminalResultV1(
            lifecycle=state, payload=payload
        ),
    )

    exit_code = cli_main(
        [
            "--root",
            str(root),
            "reason",
            "--text",
            "Which terminal state controls automation?",
            "--run-manifest",
            str(manifest_path),
            "--cycles",
            "1",
        ]
    )

    assert exit_code == expected
    assert json.loads(capsys.readouterr().out)["state"] == state


def test_synchronous_cli_returns_unknown_terminal_exit_for_invalid_result(
    tmp_path, monkeypatch, capsys
):
    manifest, manifest_path = _manifest(tmp_path)
    root = tmp_path / "invalid"
    monkeypatch.setattr(
        TEXT_RUN_SERVICE,
        "start",
        lambda *_args, **_kwargs: RunStartedV1(
            root=str(root.resolve()), manifest_digest=manifest.sha256
        ),
    )
    monkeypatch.setattr(TEXT_RUN_SERVICE, "wait", lambda *_args, **_kwargs: None)
    monkeypatch.setattr(
        TEXT_RUN_SERVICE,
        "result",
        lambda _intent: (_ for _ in ()).throw(ValueError("RUN_RESULT_INVALID")),
    )

    assert (
        cli_main(
            [
                "--root",
                str(root),
                "reason",
                "--text",
                "Can an unknown terminal be reported as success?",
                "--run-manifest",
                str(manifest_path),
                "--cycles",
                "1",
            ]
        )
        == 6
    )
    assert "RUN_RESULT_INVALID" in capsys.readouterr().err


def test_outstanding_work_projection_reads_replay_state_without_reducing(
    tmp_path, monkeypatch
):
    from tests.test_workflow_control_replay_c1 import _planned

    harness = Harness(tmp_path)
    _initial, planned = _planned()
    work = planned.work_orders[0]
    harness.record_control_transition(planned.decisions[0], work_order=work)
    harness.record_control_transition(planned.decisions[1])
    monkeypatch.setattr(
        "deepreason.workflow.reducer.reduce_conjecture",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(
            AssertionError("projection must not rerun reducer")
        ),
    )

    projection = TEXT_RUN_SERVICE.inspect_outstanding_work(tmp_path)

    assert projection.process_digest == harness.workflow_state.digest
    assert projection.last_control_seq == max(harness.workflow_state.event_seqs)
    assert len(projection.work) == 1
    item = projection.work[0]
    assert item.work_order_id == work.id
    assert item.recovery == "issued"
    assert item.route_digest == work.route_lease.route_sha256
    assert item.contract_id == work.contract_id
    assert item.reserved_tokens == planned.state.reserved_tokens
    assert item.provider_calls_limit == work.capability_grant.max_provider_calls
    status = TEXT_RUN_SERVICE.inspect(
        InspectTextRunIntentV1(root=str(tmp_path))
    ).presentation_payload()
    assert status["outstanding_work"] == projection.presentation_payload()


def test_outstanding_work_projection_accepts_v6_transaction_ids(tmp_path):
    from deepreason.llm.budget import TokenMeter
    from deepreason.workflow.transaction_service import InquiryTransactionService
    from tests.test_v6_transaction_qualification import _manifest, _prepare

    manifest = _manifest()
    harness = Harness(tmp_path)
    service = InquiryTransactionService(harness, manifest, TokenMeter(1_000))
    preparation = _prepare(service, manifest, trigger="cancellation-inspection")

    projection = TEXT_RUN_SERVICE.inspect_outstanding_work(tmp_path)

    assert projection.process_digest == harness.workflow_state.digest
    assert [item.work_order_id for item in projection.work] == [preparation.id]
    assert projection.work[0].recovery == "prepared"
    assert projection.work[0].contract_id == "conjecturer.turn.v6"
    assert projection.work[0].reserved_tokens == 0


def test_worker_harness_constructor_failure_releases_operator_lock(tmp_path):
    import deepreason.harness as harness_module

    manifest, manifest_path = _manifest(tmp_path)
    root = tmp_path / "constructor-failure"
    service = TextRunApplicationService(TextRunWorkerRegistry())
    original_init = Harness.__init__

    def fail_constructor(_self, *_args, **_kwargs):
        raise RuntimeError("constructor failed")

    with pytest.MonkeyPatch.context() as scoped:
        scoped.setattr(Harness, "__init__", fail_constructor)
        assert harness_module.Harness is Harness
        accepted = service.start(
            StartTextRunIntentV1(
                root=str(root),
                workload=spec_from_text("Can construction fail safely?"),
                run_manifest_ref=str(manifest_path),
                budget={"cycles": 1, "token_budget": "unlimited"},
            ),
            credential_checker=lambda _manifest: [],
        )
        worker = service.registry.threads[str(root.resolve())]
        service.wait(accepted.root)

        assert not worker.is_alive()
        assert service.registry.live(root) is None
        terminal = service.result(InspectTextRunIntentV1(root=accepted.root))
        assert terminal.lifecycle == "failed"
        assert terminal.payload["error_type"] == "RuntimeError"
        assert terminal.payload["error"] == "constructor failed"

    assert harness_module.Harness is Harness
    assert Harness.__init__ is original_init
    locks = operator_locks(root, owner="lock-release-test", blocking=False)
    locks.release()


def test_clients_have_only_thin_service_dispatch_and_one_registry():
    assert mcp_server._RUN_THREADS is TEXT_RUN_WORKERS.threads
    assert mcp_server._RUN_LOCK is TEXT_RUN_WORKERS.lock
    for function in (mcp_server._start_run, cli_module._execute_reason):
        source = inspect.getsource(function)
        assert "run_scheduler" not in source
        assert "StopPolicy" not in source
        assert "Harness(" not in source
