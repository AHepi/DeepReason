"""MCP server (docs/AGENT.md): the harness as agent-installable tools.
Protocol handling is pure functions (handle/call_tool), so the full
initialize -> tools/list -> tools/call flow is testable without a
subprocess. The tool surface must be the §13 verb set — no status-setting
tool may exist."""

import json
import subprocess
import sys
import threading

import pytest

from deepreason import mcp_server
from deepreason.ontology import Status


@pytest.fixture(autouse=True)
def _explicit_legacy_surface(monkeypatch):
    """Most tests exercise the quarantined historical verbs explicitly."""
    monkeypatch.setenv("DEEPREASON_ENABLE_LEGACY_MCP", "1")


def _call(name: str, arguments: dict) -> dict:
    return mcp_server.handle(
        {"jsonrpc": "2.0", "id": 1, "method": "tools/call",
         "params": {"name": name, "arguments": arguments}}
    )["result"]


def test_initialize_and_tools_list():
    init = mcp_server.handle({"jsonrpc": "2.0", "id": 0, "method": "initialize", "params": {}})
    assert init["result"]["serverInfo"]["name"] == "deepreason"
    assert mcp_server.handle({"jsonrpc": "2.0", "method": "notifications/initialized"}) is None
    tools = mcp_server.handle({"jsonrpc": "2.0", "id": 1, "method": "tools/list"})
    names = {t["name"] for t in tools["result"]["tools"]}
    assert {"start_make", "make_status", "make_result", "seed_problem", "run_cycles",
            "frontier", "theory", "why", "eval_report", "docket",
            "appellate_rule"} <= names
    # make_status is read-only operational progress. No tool sets an
    # epistemic status or directly accepts/refutes an artifact (§0).
    assert not any("set_status" in n or "accept" in n or "refute" in n for n in names)
    for tool in tools["result"]["tools"]:
        assert tool["description"] and tool["inputSchema"]["type"] == "object"


def test_default_surface_is_only_harness_owned_make_tools(monkeypatch):
    monkeypatch.delenv("DEEPREASON_ENABLE_LEGACY_MCP", raising=False)
    tools = mcp_server.handle(
        {"jsonrpc": "2.0", "id": 1, "method": "tools/list"}
    )
    names = {tool["name"] for tool in tools["result"]["tools"]}
    assert names == {"start_make", "make_status", "make_result"}

    hidden = _call("run_cycles", {"cycles": 1})
    assert hidden["isError"]
    assert "MCP_TOOL_NOT_EXPOSED" in hidden["content"][0]["text"]


def test_seed_then_inspect_roundtrip(tmp_path):
    root = str(tmp_path / "h")
    result = _call(
        "seed_problem",
        {
            "root": root,
            "problem": {"id": "pi-x", "description": "explain x",
                        "criteria": ["k-x", "skeleton-wf"]},
            "commitments": [{"id": "k-x", "eval": "predicate:'x' in content"}],
            "standard": {"id": "std-x", "rubric": "must name a mechanism"},
        },
    )
    assert result["isError"] is False
    assert "pi-x" in result["content"][0]["text"]

    frontier = _call("frontier", {"root": root})
    assert frontier["isError"] is False
    listing = json.loads(frontier["content"][0]["text"])
    assert listing[0]["problem"] == "pi-x"

    # skeleton-wf was auto-registered; standard artifact exists and is accepted
    from deepreason.harness import Harness
    from pathlib import Path

    harness = Harness(Path(root))
    assert "skeleton-wf" in harness.commitments
    assert Status.ACCEPTED in set(harness.state.status.values())


def test_run_cycles_without_engine_is_tool_error(tmp_path):
    root = str(tmp_path / "h")
    _call("seed_problem", {"root": root, "problem": {"id": "pi-x", "description": "x"}})
    result = _call("run_cycles", {"root": root, "cycles": 1})
    assert result["isError"] is True
    assert "conjecturer" in result["content"][0]["text"]


def test_unknown_tool_and_method():
    result = _call("set_status", {"id": "a", "status": "accepted"})
    assert result["isError"] is True
    err = mcp_server.handle({"jsonrpc": "2.0", "id": 9, "method": "no/such"})
    assert err["error"]["code"] == -32601
    assert mcp_server.handle({"jsonrpc": "2.0", "method": "no/such/notification"}) is None


def test_make_status_and_result_are_fixed_root_reads(tmp_path):
    status = _call("make_status", {"root": str(tmp_path / "run")})
    assert status["isError"] is False
    assert json.loads(status["content"][0]["text"])["state"] == "not-started"

    result = _call("make_result", {"root": str(tmp_path / "run")})
    assert result["isError"] is True
    assert "MAKE_RESULT_NOT_READY" in result["content"][0]["text"]


def test_start_make_accepts_only_manifest_bound_workflow(tmp_path, monkeypatch):
    from deepreason.config import Config
    from deepreason.run_manifest import compile_run_manifest, write_run_manifest

    route = {
        "endpoint": "https://ollama.invalid/v1",
        "model": "gemma4:31b",
        "provider": "ollama",
        "family": "gemma",
    }
    manifest = compile_run_manifest(
        Config(roles={"conjecturer": route}),
        single_model="gemma4:31b",
        rubric_policy="forbid",
        compiled_at="2026-07-11T00:00:00Z",
    )
    manifest_path, _ = write_run_manifest(manifest, tmp_path / "input.json")
    made = []

    def fake_make(description, **kwargs):
        made.append((description, kwargs))
        kwargs["echo"]("planning")
        return [tmp_path / "run" / "deliverable" / "index.html"]

    monkeypatch.setattr("deepreason.easy.make", fake_make)
    started = _call(
        "start_make",
        {
            "root": str(tmp_path / "run"),
            "problem": {"description": "the wonders of DNA"},
            "run_manifest_ref": str(manifest_path),
            "budget": {"cycles": 3, "token_budget": 0},
        },
    )
    assert started["isError"] is False
    thread = mcp_server._MAKE_THREADS[str((tmp_path / "run").resolve())]
    thread.join(timeout=2)

    status = json.loads(_call("make_status", {"root": str(tmp_path / "run")})
                        ["content"][0]["text"])
    assert status["state"] == "completed"
    assert made[0][0] == "the wonders of DNA"
    assert made[0][1]["token_budget"] is None
    assert made[0][1]["config"].endswith(".run-manifest-config.json")
    assert (tmp_path / "run" / "run-manifest.json").exists()

    result = _call("make_result", {"root": str(tmp_path / "run")})
    assert "index.html" in result["content"][0]["text"]


def test_start_make_exposes_typed_terminal_website_failure(tmp_path, monkeypatch):
    from deepreason.config import Config
    from deepreason.run_manifest import compile_run_manifest, write_run_manifest

    route = {
        "endpoint": "https://ollama.invalid/v1",
        "model": "gemma4:31b",
        "provider": "ollama",
        "family": "gemma",
    }
    manifest = compile_run_manifest(
        Config(roles={"conjecturer": route}),
        single_model="gemma4:31b",
        rubric_policy="forbid",
        compiled_at="2026-07-11T00:00:00Z",
    )
    manifest_path, _ = write_run_manifest(manifest, tmp_path / "input.json")
    run_root = tmp_path / "terminal-run"
    resume = "deepreason make DNA --root terminal-run --cycles 7"

    def fake_make(_description, **kwargs):
        terminal = {
            "failed_stage": "MANIFEST_VALIDATE",
            "direct_calls": 1,
            "compact_calls": 3,
            "schema_failures_by_path": {"/components/0": 1},
            "manifest_wf_failures_by_code": {"EXPORT_NOT_DECLARED": 1},
            "critic_refutations": 0,
            "last_valid_intermediate": "outline-ref",
            "checkpoint_ref": str(run_root / "website-checkpoint.json"),
            "manifest_sha256": manifest.sha256,
            "resume_command": resume,
            "diagnostics": [
                {"code": "EXPORT_NOT_DECLARED", "path": "/components/0"}
            ],
        }
        (run_root / "website-terminal.json").write_text(json.dumps(terminal))
        kwargs["echo"]("terminal diagnostics persisted")
        return []

    monkeypatch.setattr("deepreason.easy.make", fake_make)
    started = _call(
        "start_make",
        {
            "root": str(run_root),
            "problem": {"description": "DNA"},
            "run_manifest_ref": str(manifest_path),
            "budget": {"cycles": 3, "token_budget": 0},
        },
    )
    assert started["isError"] is False
    mcp_server._MAKE_THREADS[str(run_root.resolve())].join(timeout=2)

    status = json.loads(
        _call("make_status", {"root": str(run_root)})["content"][0]["text"]
    )
    assert status["state"] == "failed"
    assert status["failure_kind"] == "website-terminal"
    assert status["outputs"] == []
    assert status["resume_command"] == resume
    assert status["terminal_summary"]["failed_stage"] == "MANIFEST_VALIDATE"
    assert status["terminal_summary"]["diagnostics"][0]["code"] == (
        "EXPORT_NOT_DECLARED"
    )

    result_response = _call("make_result", {"root": str(run_root)})
    assert result_response["isError"] is False
    result = json.loads(result_response["content"][0]["text"])
    assert result["state"] == "failed"
    assert result["failure_kind"] == "website-terminal"
    assert result["resume_command"] == resume
    assert result["terminal_summary"] == status["terminal_summary"]


def test_start_make_empty_output_without_terminal_is_failure(tmp_path, monkeypatch):
    from deepreason.config import Config
    from deepreason.run_manifest import compile_run_manifest, write_run_manifest

    route = {
        "endpoint": "https://ollama.invalid/v1",
        "model": "gemma4:31b",
        "provider": "ollama",
        "family": "gemma",
    }
    manifest = compile_run_manifest(
        Config(roles={"conjecturer": route}),
        single_model="gemma4:31b",
        rubric_policy="forbid",
        compiled_at="2026-07-11T00:00:00Z",
    )
    manifest_path, _ = write_run_manifest(manifest, tmp_path / "input-empty.json")
    run_root = tmp_path / "empty-run"
    monkeypatch.setattr("deepreason.easy.make", lambda *_args, **_kwargs: [])

    started = _call(
        "start_make",
        {
            "root": str(run_root),
            "problem": {"description": "DNA"},
            "run_manifest_ref": str(manifest_path),
            "budget": {"cycles": 1},
        },
    )
    assert started["isError"] is False
    mcp_server._MAKE_THREADS[str(run_root.resolve())].join(timeout=2)
    result = json.loads(
        _call("make_result", {"root": str(run_root)})["content"][0]["text"]
    )
    assert result["state"] == "failed"
    assert result["failure_kind"] == "missing-terminal-summary"
    assert result["outputs"] == []


def test_start_make_recovers_stale_running_status(tmp_path, monkeypatch):
    from deepreason.config import Config
    from deepreason.run_manifest import (
        bind_run_manifest,
        compile_run_manifest,
        write_run_manifest,
    )

    route = {
        "endpoint": "https://ollama.invalid/v1",
        "model": "gemma4:31b",
        "provider": "ollama",
        "family": "gemma",
    }
    manifest = compile_run_manifest(
        Config(roles={"conjecturer": route}),
        single_model="gemma4:31b",
        rubric_policy="forbid",
        compiled_at="2026-07-11T00:00:00Z",
    )
    manifest_path, _ = write_run_manifest(manifest, tmp_path / "input.json")
    run_root = (tmp_path / "stale-run").resolve()
    bind_run_manifest(manifest, run_root)
    mcp_server._write_make_status(
        run_root,
        {
            "state": "running",
            "root": str(run_root),
            "manifest_sha256": manifest.sha256,
            "problem": "DNA",
        },
    )
    monkeypatch.setattr(
        "deepreason.easy.make",
        lambda *_args, **_kwargs: [run_root / "deliverable" / "index.html"],
    )

    result = _call(
        "start_make",
        {
            "root": str(run_root),
            "problem": {"description": "DNA"},
            "run_manifest_ref": str(manifest_path),
            "budget": {"cycles": 1},
        },
    )
    assert result["isError"] is False
    mcp_server._MAKE_THREADS[str(run_root)].join(timeout=2)
    status = json.loads(
        _call("make_status", {"root": str(run_root)})["content"][0]["text"]
    )
    assert status["state"] == "completed"
    assert status["recovered_from_stale_status"] is True
    assert status["manifest_sha256"] == manifest.sha256


def test_start_make_preflights_missing_credentials_synchronously(
    tmp_path, monkeypatch
):
    from deepreason.config import Config
    from deepreason.run_manifest import compile_run_manifest, write_run_manifest

    credential_name = "DEEPREASON_TEST_MISSING_MCP_KEY"
    monkeypatch.delenv(credential_name, raising=False)
    route = {
        "endpoint": "https://ollama.invalid/v1",
        "model": "gemma4:31b",
        "provider": "ollama",
        "family": "gemma",
        "api_key_env": credential_name,
    }
    manifest = compile_run_manifest(
        Config(roles={"conjecturer": route}),
        single_model="gemma4:31b",
        rubric_policy="forbid",
        compiled_at="2026-07-11T00:00:00Z",
    )
    manifest_path, _ = write_run_manifest(manifest, tmp_path / "credential-input.json")
    run_root = (tmp_path / "credential-run").resolve()
    called = threading.Event()

    def fake_make(*_args, **_kwargs):
        called.set()
        return []

    monkeypatch.setattr("deepreason.easy.make", fake_make)
    result = _call(
        "start_make",
        {
            "root": str(run_root),
            "problem": {"description": "DNA"},
            "run_manifest_ref": str(manifest_path),
            "budget": {"cycles": 1},
        },
    )

    assert result["isError"] is True
    assert "MAKE_CREDENTIAL_MISSING" in result["content"][0]["text"]
    assert credential_name in result["content"][0]["text"]
    assert not called.is_set()
    assert not run_root.exists()
    assert str(run_root) not in mcp_server._MAKE_THREADS


def test_start_make_system_exit_becomes_terminal_failure(tmp_path, monkeypatch):
    from deepreason.config import Config
    from deepreason.run_manifest import compile_run_manifest, write_run_manifest

    route = {
        "endpoint": "https://ollama.invalid/v1",
        "model": "gemma4:31b",
        "provider": "ollama",
        "family": "gemma",
    }
    manifest = compile_run_manifest(
        Config(roles={"conjecturer": route}),
        single_model="gemma4:31b",
        rubric_policy="forbid",
        compiled_at="2026-07-11T00:00:00Z",
    )
    manifest_path, _ = write_run_manifest(manifest, tmp_path / "exit-input.json")
    run_root = (tmp_path / "exit-run").resolve()

    def exit_make(*_args, **_kwargs):
        raise SystemExit("credential loader exited")

    monkeypatch.setattr("deepreason.easy.make", exit_make)
    started = _call(
        "start_make",
        {
            "root": str(run_root),
            "problem": {"description": "DNA"},
            "run_manifest_ref": str(manifest_path),
            "budget": {"cycles": 1},
        },
    )
    assert started["isError"] is False
    mcp_server._MAKE_THREADS[str(run_root)].join(timeout=2)

    result_response = _call("make_result", {"root": str(run_root)})
    assert result_response["isError"] is False
    result = json.loads(result_response["content"][0]["text"])
    assert result["state"] == "failed"
    assert result["failure_kind"] == "worker-exception"
    assert result["error_type"] == "SystemExit"
    assert result["error"] == "credential loader exited"
    assert result["outputs"] == []


def test_start_make_holds_operator_lock_for_full_worker_lifetime_across_processes(
    tmp_path, monkeypatch
):
    from deepreason.config import Config
    from deepreason.run_manifest import compile_run_manifest, write_run_manifest

    route = {
        "endpoint": "https://ollama.invalid/v1",
        "model": "gemma4:31b",
        "provider": "ollama",
        "family": "gemma",
    }
    manifest = compile_run_manifest(
        Config(roles={"conjecturer": route}),
        single_model="gemma4:31b",
        rubric_policy="forbid",
        compiled_at="2026-07-11T00:00:00Z",
    )
    manifest_path, _ = write_run_manifest(manifest, tmp_path / "lock-input.json")
    run_root = (tmp_path / "locked-run").resolve()
    entered = threading.Event()
    release = threading.Event()

    def blocked_make(*_args, **_kwargs):
        entered.set()
        assert release.wait(timeout=5)
        return [run_root / "deliverable" / "index.html"]

    monkeypatch.setattr("deepreason.easy.make", blocked_make)
    started = _call(
        "start_make",
        {
            "root": str(run_root),
            "problem": {"description": "DNA"},
            "run_manifest_ref": str(manifest_path),
            "budget": {"cycles": 1},
        },
    )
    assert started["isError"] is False
    assert entered.wait(timeout=2)

    probe = (
        "import fcntl, sys\n"
        "stream = open(sys.argv[1], 'a+b')\n"
        "try:\n"
        "    fcntl.flock(stream.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)\n"
        "except BlockingIOError:\n"
        "    raise SystemExit(23)\n"
        "raise SystemExit(0)\n"
    )
    lock_path = run_root / mcp_server._MAKE_OPERATOR_LOCK_NAME
    try:
        contended = subprocess.run(
            [sys.executable, "-c", probe, str(lock_path)], check=False
        )
        assert contended.returncode == 23
    finally:
        release.set()
        mcp_server._MAKE_THREADS[str(run_root)].join(timeout=2)

    released = subprocess.run(
        [sys.executable, "-c", probe, str(lock_path)], check=False
    )
    assert released.returncode == 0
    status = mcp_server._read_make_status(run_root)
    assert status["state"] == "completed"
    assert status["manifest_sha256"] == manifest.sha256


def test_run_cycles_resume_loads_bound_manifest_and_ignores_config(
    tmp_path, monkeypatch
):
    from deepreason.config import Config
    from deepreason.run_manifest import bind_run_manifest, compile_run_manifest

    route = {
        "endpoint": "https://ollama.invalid/v1",
        "model": "gemma4:31b",
        "provider": "ollama",
        "family": "gemma",
    }
    manifest = compile_run_manifest(
        Config(roles={"conjecturer": route}),
        single_model="gemma4:31b",
        rubric_policy="forbid",
        compiled_at="2026-07-11T00:00:00Z",
    )
    run_root = tmp_path / "resume-run"
    bind_run_manifest(manifest, run_root)
    _call(
        "seed_problem",
        {"root": str(run_root), "problem": {"id": "pi-x", "description": "x"}},
    )
    monkeypatch.setattr(
        mcp_server, "_config", lambda *_a, **_k: pytest.fail("resume loaded config")
    )

    def fake_scheduler(harness, config, cycles, token_budget=None, run_manifest=None):
        assert run_manifest == manifest
        assert config.roles["conjecturer"]["model"] == "gemma4:31b"
        return (
            {"survivors": [], "frontier": [], "problems": [], "diagnostics": []},
            None,
            {"metered_tokens": 0, "logged_tokens_this_run": 0, "delta": 0},
        )

    monkeypatch.setattr("deepreason.ops.run_scheduler", fake_scheduler)
    result = _call(
        "run_cycles",
        {"root": str(run_root), "config": str(tmp_path / "decoy.yaml"), "cycles": 1},
    )
    assert result["isError"] is False
    assert json.loads(result["content"][0]["text"])["accounting"]["delta"] == 0
