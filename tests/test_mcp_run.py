"""Production MCP progress, cancellation, result, and continuation surface."""

from __future__ import annotations

import json
import threading

from deepreason.application import OperatorCancellationIntentV1
from deepreason import mcp_server
from deepreason.cli.main import main as cli_main
from deepreason.config import Config
from deepreason.run_manifest import ToolchainEntry, compile_run_manifest, write_run_manifest
from deepreason.verification.models import VerificationResult


def _manifest(tmp_path):
    route = {
        "endpoint": "https://example.invalid/v1",
        "model": "gemma4:31b",
        "provider": "ollama",
        "family": "gemma",
    }
    manifest = compile_run_manifest(
        Config(roles={"conjecturer": route}),
        single_model="gemma4:31b",
        rubric_policy="forbid",
        compiled_at="2026-07-13T00:00:00Z",
        schema_version=2,
        workload_profile="text",
    )
    path, _ = write_run_manifest(manifest, tmp_path / "manifest.json")
    return manifest, path


def _call(name, arguments, *, sink=None, token=None):
    params = {"name": name, "arguments": arguments}
    if token is not None:
        params["_meta"] = {"progressToken": token}
    return mcp_server.handle(
        {"jsonrpc": "2.0", "id": 1, "method": "tools/call", "params": params},
        notification_sink=sink,
    )["result"]


def _payload(result):
    assert not result["isError"], result["content"][0]["text"]
    return json.loads(result["content"][0]["text"])


class _SchedulerView:
    def __init__(self, harness, cycles):
        self.harness = harness
        self._cycles = cycles

    def report(self):
        return {"frontier": []}


def test_start_poll_result_and_progress_notifications(tmp_path, monkeypatch):
    manifest, manifest_path = _manifest(tmp_path)

    def fake_run(
        harness, _config, _cycles, token_budget, on_cycle, run_manifest,
        progress_sink=None,
    ):
        assert run_manifest == manifest
        assert token_budget is None
        assert progress_sink is not None
        on_cycle(_SchedulerView(harness, 1))
        return (
            {"frontier": [], "survivors": [], "problems": [], "diagnostics": []},
            None,
            {"metered_tokens": None, "logged_tokens_this_run": 0, "delta": None},
        )

    monkeypatch.setattr("deepreason.ops.run_scheduler", fake_run)
    root = tmp_path / "run"
    notifications = []
    started = _payload(
        _call(
            "start_run",
            {
                "root": str(root),
                "workload": "text",
                "problem": {"description": "Why do explanations generalize?"},
                "run_manifest_ref": str(manifest_path),
                "budget": {"cycles": 1, "token_budget": "unlimited"},
            },
            sink=notifications.append,
            token="progress-1",
        )
    )
    mcp_server._RUN_THREADS[str(root.resolve())].join(timeout=2)

    assert started["status_operation"] == "run_status"
    status = _payload(_call("run_status", {"root": str(root), "since_seq": 0}))
    assert status["state"] == "completed"
    assert status["determinate"] is False
    assert status["token_limit"] is None
    assert status["events"] and all(event["seq"] > 0 for event in status["events"])
    result = _payload(_call("run_result", {"root": str(root)}))
    assert result["stop"]["reason"] == "budget_exhausted"
    assert notifications
    assert {item["params"]["progressToken"] for item in notifications} == {"progress-1"}


def test_cancel_waits_for_safe_boundary_then_continue_appends(tmp_path, monkeypatch):
    manifest, manifest_path = _manifest(tmp_path)
    cycle_started = threading.Event()
    release_cycle = threading.Event()

    def blocked_run(
        harness, _config, _cycles, token_budget, on_cycle, run_manifest,
        progress_sink=None,
    ):
        assert token_budget is None and run_manifest == manifest
        cycle_started.set()
        assert release_cycle.wait(timeout=2)
        assert on_cycle(_SchedulerView(harness, 1)) is True
        return (
            {"frontier": [], "survivors": [], "problems": [], "diagnostics": []},
            None,
            {"metered_tokens": None, "logged_tokens_this_run": 0, "delta": None},
        )

    monkeypatch.setattr("deepreason.ops.run_scheduler", blocked_run)
    root = tmp_path / "run"
    _payload(
        _call(
            "start_run",
            {
                "root": str(root),
                "workload": "text",
                "problem": {"description": "What makes a test discriminating?"},
                "run_manifest_ref": str(manifest_path),
                "budget": {"cycles": "unlimited", "token_budget": "unlimited"},
            },
        )
    )
    assert cycle_started.wait(timeout=2)
    cancel = _payload(_call("cancel_run", {"root": str(root)}))
    assert cancel["safe_boundary"] == "completed-cycle"
    cancellation_intents = [
        OperatorCancellationIntentV1.model_validate_json(line)
        for line in (root / "operator-intents.jsonl").read_text().splitlines()
    ]
    assert len(cancellation_intents) == 1
    assert cancellation_intents[0].manifest_digest == manifest.sha256
    assert cancellation_intents[0].sequence == 0
    assert (root / "cancel.requested").exists()
    assert _payload(_call("run_status", {"root": str(root)}))["state"] == "running"
    release_cycle.set()
    mcp_server._RUN_THREADS[str(root.resolve())].join(timeout=2)
    assert _payload(_call("run_result", {"root": str(root)}))["state"] == "cancelled"

    def resumed_run(
        harness, _config, _cycles, token_budget, on_cycle, run_manifest,
        progress_sink=None,
    ):
        assert token_budget is None and run_manifest == manifest
        assert not (root / "cancel.requested").exists()
        on_cycle(_SchedulerView(harness, 1))
        return (
            {"frontier": [], "survivors": [], "problems": [], "diagnostics": []},
            None,
            {"metered_tokens": None, "logged_tokens_this_run": 0, "delta": None},
        )

    monkeypatch.setattr("deepreason.ops.run_scheduler", resumed_run)
    continued = _payload(
        _call(
            "continue_run",
            {
                "root": str(root),
                "budget": {"cycles": 1, "token_budget": "unlimited"},
                "expected_manifest_digest": manifest.sha256,
            },
        )
    )
    assert continued["manifest_sha256"] == manifest.sha256
    mcp_server._RUN_THREADS[str(root.resolve())].join(timeout=2)
    assert len(list((root / "run-stops").glob("*.json"))) == 2
    assert len((root / "continuations.jsonl").read_text().splitlines()) == 1
    assert any(
        event.inputs and event.inputs[0] == "run-resume"
        for event in __import__("deepreason.harness", fromlist=["Harness"]).Harness(root).log.read()
    )


def test_scheduler_convergence_stop_is_not_overwritten(tmp_path, monkeypatch):
    manifest, manifest_path = _manifest(tmp_path)

    def converged_run(
        harness, _config, _cycles, token_budget, on_cycle, run_manifest,
        progress_sink=None,
    ):
        from deepreason.runtime.stop import StopMetrics, StopPolicy, write_stop_record

        on_cycle(_SchedulerView(harness, 3))
        policy = StopPolicy()
        metrics = StopMetrics(cycle=3)
        harness.record_measure(inputs=["scheduler-stop", "converged", policy.digest])
        write_stop_record(
            harness.root,
            reason="converged",
            policy=policy,
            metrics=metrics,
            event_seq=harness._next_seq - 1,
        )
        return (
            {
                "frontier": [],
                "survivors": [],
                "problems": [],
                "diagnostics": [],
                "stop_reason": "converged",
            },
            None,
            {"metered_tokens": None, "logged_tokens_this_run": 0, "delta": None},
        )

    monkeypatch.setattr("deepreason.ops.run_scheduler", converged_run)
    root = tmp_path / "converged-run"
    _payload(
        _call(
            "start_run",
            {
                "root": str(root),
                "workload": "text",
                "problem": {"description": "When should search converge?"},
                "run_manifest_ref": str(manifest_path),
                "budget": {"cycles": 12, "token_budget": "unlimited"},
            },
        )
    )
    mcp_server._RUN_THREADS[str(root.resolve())].join(timeout=2)
    assert _payload(_call("run_result", {"root": str(root)}))["stop"]["reason"] == "converged"
    assert len(list((root / "run-stops").glob("*.json"))) == 1


def test_watch_once_is_read_only(tmp_path, capsys):
    assert cli_main(["--root", str(tmp_path), "watch", "--once"]) == 0
    assert "not-started" in capsys.readouterr().out
    assert list(tmp_path.iterdir()) == []


def test_production_run_schema_exposes_no_control_or_path_browser_fields():
    tools = {tool["name"]: tool for tool in mcp_server._tools()}
    assert {"start_run", "run_status", "run_result", "continue_run", "cancel_run"} <= tools.keys()
    encoded = json.dumps(tools["start_run"]["inputSchema"], sort_keys=True)
    for forbidden in ("shell", "argv", "route", "guard", "status_set", "repository"):
        assert forbidden not in encoded


def test_prove_and_check_proof_use_only_pinned_lean_toolchain(
    tmp_path, monkeypatch, capsys
):
    version_digest = "a" * 64
    toolchain = ToolchainEntry(
        id="lean4@4.19.0",
        runner="local",
        executable="/pinned/bin/lean",
        version_output_sha256=version_digest,
        network=False,
        allowed_programs=("lean_kernel",),
    )
    route = {
        "endpoint": "https://example.invalid/v1",
        "model": "gemma4:31b",
        "provider": "ollama",
        "family": "gemma",
    }
    manifest = compile_run_manifest(
        Config(roles={"conjecturer": route}),
        rubric_policy="forbid",
        compiled_at="2026-07-13T00:00:00Z",
        schema_version=2,
        workload_profile="formal",
        toolchains=(toolchain,),
    )
    manifest_path, _ = write_run_manifest(manifest, tmp_path / "formal.json")
    source = tmp_path / "sample.lean"
    source.write_text("theorem sample : True := by trivial\n", encoding="utf-8")
    seen = []

    class FakeLeanBackend:
        def __init__(self, blobs, *, executable, toolchain_id):
            assert executable == "/pinned/bin/lean"
            assert toolchain_id == "lean4@4.19.0"
            self.blobs = blobs

        def fingerprint(self):
            return {"version_output_sha256": version_digest}

        def verify(self, request):
            seen.append(request)
            assert self.blobs.get(request.source_ref) == source.read_bytes()
            return VerificationResult(
                backend="lean4",
                fingerprint={"version_output_sha256": version_digest},
                verdict="pass",
                source_sha256=request.source_ref,
                theorems=["sample"],
            )

    monkeypatch.setattr("deepreason.verification.lean.LeanBackend", FakeLeanBackend)
    root = tmp_path / "proof-run"
    for command in ("prove", "check-proof"):
        assert cli_main(
            [
                "--root", str(root), command,
                "--source", str(source),
                "--run-manifest", str(manifest_path),
                "--theorem", "sample",
            ]
        ) == 0
        assert "not informal or empirical truth" in capsys.readouterr().out
    assert len(seen) == 2
    assert all(request.allow_sorry is False for request in seen)
