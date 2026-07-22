from __future__ import annotations

import importlib
import json
import runpy
import sys
from pathlib import Path

import pytest

from deepreason import mcp_server
from deepreason.application import (
    RunProgressResultV1,
    RunStartedV1,
    TextRunTerminalResultV1,
)
from deepreason.cli.doctor import (
    ProductionContractCaseResultV1,
    run_production_contract_doctor,
)
from deepreason.cli.main import main
from deepreason.preparation import qualification_subject_manifest
from deepreason.provider_profile import (
    ProviderProfileV1,
    setup_provider_profile_path,
    write_provider_profile,
)
from deepreason.qualification import resolve_completed_qualification
from deepreason.readiness import get_readiness


def _profile(**updates) -> ProviderProfileV1:
    values = dict(
        provider="openai",
        endpoint="https://api.example.test/v1",
        model_id="model-public-v6",
        model_revision="revision-1",
        family="family-public-v6",
        context_window_tokens=131_072,
        maximum_completion_tokens=4_096,
        credential_env="DEEPREASON_PUBLIC_TEST_KEY",
    )
    values.update(updates)
    return ProviderProfileV1.create(**values)


def _qualified_report(manifest):
    return run_production_contract_doctor(
        manifest,
        case_executor=lambda _manifest, _pair, index: ProductionContractCaseResultV1(
            case_id=f"case-{index + 1:03d}",
            first_pass_valid=True,
            eventual_valid=True,
            repair_count=0,
            semantic_admission=True,
        ),
    )


def _configure(monkeypatch, tmp_path: Path, *, credential: bool = True):
    state = tmp_path / "state"
    monkeypatch.setenv("DEEPREASON_HOME", str(state))
    if credential:
        monkeypatch.setenv("DEEPREASON_PUBLIC_TEST_KEY", "never-print-this-secret")
    else:
        monkeypatch.delenv("DEEPREASON_PUBLIC_TEST_KEY", raising=False)
    profile = _profile()
    write_provider_profile(
        profile,
        setup_provider_profile_path(environ={"DEEPREASON_HOME": str(state)}),
    )
    return state, profile


def _qualify(state: Path, profile: ProviderProfileV1):
    calls = []
    manifest = qualification_subject_manifest(profile)
    bundle = resolve_completed_qualification(
        manifest,
        profile,
        cache_dir=state / "qualification-cache",
        executor=lambda value: calls.append(value.sha256) or _qualified_report(value),
    )
    return bundle, calls


def test_readiness_transitions_are_stable_redacted_and_have_one_action(
    tmp_path, monkeypatch
):
    monkeypatch.setenv("DEEPREASON_HOME", str(tmp_path / "state"))
    missing = get_readiness()
    assert missing.qualification_state == "profile_missing"
    assert missing.next_action == "deepreason setup"

    state, profile = _configure(monkeypatch, tmp_path, credential=False)
    no_credential = get_readiness()
    assert no_credential.qualification_state == "credential_missing"
    assert no_credential.credential_present is False

    monkeypatch.setenv("DEEPREASON_PUBLIC_TEST_KEY", "never-print-this-secret")
    unqualified = get_readiness()
    assert unqualified.qualification_state == "unqualified"
    assert unqualified.next_action == "deepreason qualify"
    _qualify(state, profile)
    ready = get_readiness()
    assert ready.ready is True
    assert ready.qualification_state == "ready"
    assert ready.next_action == 'deepreason reason "YOUR QUESTION"'
    encoded = ready.model_dump_json(by_alias=True)
    assert "never-print-this-secret" not in encoded
    assert "DEEPREASON_PUBLIC_TEST_KEY" not in encoded
    assert list(json.loads(encoded)).count("next_action") == 1


def test_qualification_is_explicit_warns_before_fake_dispatch_and_reuses_cache(
    tmp_path, monkeypatch, capsys
):
    state, _profile_value = _configure(monkeypatch, tmp_path)
    calls = []

    def execute(manifest):
        warning = capsys.readouterr().err
        assert "maximum expected provider calls" in warning
        calls.append(manifest.sha256)
        return _qualified_report(manifest)

    monkeypatch.setattr(
        "deepreason.qualification.default_qualification_executor", execute
    )
    assert main(["qualify", "--json"]) == 0
    first = json.loads(capsys.readouterr().out)
    assert first["cache_reused"] is False
    assert first["maximum_expected_provider_calls"] > 0
    assert len(calls) == 1
    assert main(["qualify", "--json"]) == 0
    second = json.loads(capsys.readouterr().out)
    assert second["cache_reused"] is True
    assert second["maximum_expected_provider_calls"] == 0
    assert len(calls) == 1
    assert any((state / "qualification-cache").iterdir())


def test_failed_explicit_qualification_publishes_no_reusable_cache(
    tmp_path, monkeypatch, capsys
):
    state, _profile_value = _configure(monkeypatch, tmp_path)
    monkeypatch.setattr(
        "deepreason.qualification.default_qualification_executor",
        lambda _manifest: (_ for _ in ()).throw(RuntimeError("secret provider body")),
    )
    assert main(["qualify"]) == 1
    output = capsys.readouterr()
    assert "QUALIFICATION_EXECUTION_FAILED" in output.err
    assert "secret provider body" not in output.err + output.out
    cache_dir = state / "qualification-cache"
    assert not cache_dir.exists() or not list(cache_dir.iterdir())


def test_question_only_cli_reaches_terminal_result_without_provider_call(
    tmp_path, monkeypatch, capsys
):
    state, profile = _configure(monkeypatch, tmp_path)
    _qualify(state, profile)
    starts = []

    def start(intent, **_kwargs):
        starts.append(intent)
        return RunStartedV1(root=intent.root, manifest_digest="a" * 64)

    monkeypatch.setattr("deepreason.application.TEXT_RUN_SERVICE.start", start)
    monkeypatch.setattr("deepreason.application.TEXT_RUN_SERVICE.wait", lambda *_: None)
    monkeypatch.setattr(
        "deepreason.application.TEXT_RUN_SERVICE.result",
        lambda _intent: TextRunTerminalResultV1(
            lifecycle="completed",
            payload={
                "schema": "deepreason-run-result-v2",
                "state": "completed",
                "workload": "text",
            },
        ),
    )
    assert main(["reason", "Why do explanations generalize?", "--cycles", "1"]) == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["state"] == "completed"
    assert payload["run_id"].startswith("run-")
    assert starts[0].workload.problem.description == "Why do explanations generalize?"
    assert Path(starts[0].root).parent == state / "runs"


def test_bare_and_module_entry_share_readiness_path(tmp_path, monkeypatch, capsys):
    monkeypatch.setenv("DEEPREASON_HOME", str(tmp_path / "state"))
    assert main([]) == 1
    direct = capsys.readouterr().out
    monkeypatch.setattr(sys, "argv", ["deepreason"])
    with pytest.raises(SystemExit) as caught:
        runpy.run_module("deepreason", run_name="__main__")
    assert caught.value.code == 1
    assert capsys.readouterr().out == direct


def test_mcp_question_and_opaque_id_survive_module_restart(
    tmp_path, monkeypatch
):
    state, profile = _configure(monkeypatch, tmp_path)
    _qualify(state, profile)

    def start(intent, **_kwargs):
        return RunStartedV1(root=intent.root, manifest_digest="b" * 64)

    monkeypatch.setattr(mcp_server.TEXT_RUN_SERVICE, "start", start)
    monkeypatch.setattr(
        mcp_server.TEXT_RUN_SERVICE,
        "inspect",
        lambda _intent: RunProgressResultV1(
            lifecycle="completed", payload={"state": "completed"}
        ),
    )
    monkeypatch.setattr(
        mcp_server.TEXT_RUN_SERVICE,
        "result",
        lambda _intent: TextRunTerminalResultV1(
            lifecycle="completed",
            payload={"schema": "deepreason-run-result-v2", "state": "completed"},
        ),
    )
    started = json.loads(mcp_server.call_tool("start_run", {"question": "Unknown question"}))
    run_id = started["run_id"]
    assert "/" not in run_id and "\\" not in run_id

    reloaded = importlib.reload(mcp_server)
    status = json.loads(reloaded.call_tool("run_status", {"run_id": run_id}))
    result = json.loads(reloaded.call_tool("run_result", {"run_id": run_id}))
    assert status == {"run_id": run_id, "state": "completed"}
    assert result["run_id"] == run_id
    assert result["state"] == "completed"


def test_mcp_schemas_expose_no_path_manifest_provider_or_credential_authority():
    schemas = json.dumps(mcp_server._tools(), sort_keys=True).casefold()
    for forbidden in (
        '"root"',
        "run_manifest_ref",
        "provider_profile",
        "credential_env",
        "api_key",
    ):
        assert forbidden not in schemas
    start = next(item for item in mcp_server._tools() if item["name"] == "start_run")
    assert start["inputSchema"]["required"] == ["question"]
    assert "qualify" not in {item["name"] for item in mcp_server._tools()}


def test_mcp_pins_managed_id_and_redacts_root_and_arbitrary_error_text():
    payload = mcp_server._managed_response(
        "run-managed",
        {"run_id": "sha256:internal", "root": "/private/run", "state": "completed"},
    )
    assert payload == {"run_id": "run-managed", "state": "completed"}
    safe = mcp_server._safe_tool_error(
        ValueError("provider returned secret body at /private/run")
    )
    assert safe == "ValueError: MCP_OPERATION_FAILED"
    coded = ValueError("provider failed")
    coded.code = "never-print-this-secret"
    assert mcp_server._safe_tool_error(coded) == "ValueError: MCP_OPERATION_FAILED"
    response = mcp_server.handle(
        {"jsonrpc": "2.0", "id": 1, "method": "never-print-this-secret"}
    )
    assert response["error"] == {"code": -32601, "message": "method not found"}


def test_profile_identity_rejects_human_output_control_characters():
    with pytest.raises(ValueError, match="control characters"):
        _profile(model_id="model-a\nforged qualification")


def test_missing_readiness_stops_before_preparation_or_dispatch(
    tmp_path, monkeypatch
):
    monkeypatch.setenv("DEEPREASON_HOME", str(tmp_path / "state"))
    monkeypatch.setattr(
        "deepreason.preparation.RunPreparationService.prepare",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(
            AssertionError("preparation must not run")
        ),
    )
    monkeypatch.setattr(
        mcp_server.TEXT_RUN_SERVICE,
        "start",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(
            AssertionError("dispatch must not run")
        ),
    )
    with pytest.raises(ValueError, match="READINESS_REQUIRED"):
        mcp_server.call_tool("start_run", {"question": "Must not prepare"})
    assert not (tmp_path / "state" / "runs").exists()


@pytest.mark.parametrize(
    "arguments",
    [
        ["reason", "bounded", "--cycles", "13"],
        ["reason", "bounded", "--token-budget", "200001"],
    ],
)
def test_public_budget_cannot_exceed_the_fixed_ceiling(
    tmp_path, monkeypatch, capsys, arguments
):
    state, profile = _configure(monkeypatch, tmp_path)
    _qualify(state, profile)
    monkeypatch.setattr(
        "deepreason.application.TEXT_RUN_SERVICE.start",
        lambda *_args, **_kwargs: pytest.fail("over-ceiling budget reached dispatch"),
    )
    assert main(arguments) == 1
    assert "fixed V6 policy ceiling" in capsys.readouterr().err
    assert not (state / "runs").exists()
