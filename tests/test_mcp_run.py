"""Production MCP progress, cancellation, result, and continuation surface."""

from __future__ import annotations

import json
import threading

from deepreason.application import OperatorCancellationIntentV1
from deepreason import mcp_server
from deepreason.cli.main import main as cli_main
from deepreason.config import Config
from deepreason.evidence import (
    AttachedSourceProvenanceV1,
    EvidenceDossierV1,
    RunInputManifestV1,
    RunInputProblemV1,
    bind_run_input,
)
from deepreason.run_manifest import (
    ToolchainEntry,
    bind_run_manifest,
    compile_run_manifest,
    write_run_manifest,
)
from deepreason.runtime.stop import (
    StopController,
    StopMetrics,
    StopPolicy,
    build_stop_record,
    persist_stop_record,
)
from deepreason.verification.models import VerificationResult
from deepreason.workflow.lifecycle import build_stopped_lifecycle
from deepreason.workloads.text import spec_from_text


def _manifest(root, text):
    from tests.test_application_text_runs_d0 import _prepared_cli_manifest
    from tests.test_run_input_v6_commitments import _write_qualification

    manifest, path = _prepared_cli_manifest(root, text)
    _write_qualification(root, manifest)
    return manifest, path


def _manifest_v5(tmp_path, run_root, *, problem_id: str, problem_text: str):
    provenance = AttachedSourceProvenanceV1(
        supplied_by="offline MCP fixture",
        acquisition_method="pre-freeze construction",
    )
    dossier = EvidenceDossierV1.create(
        problem_ref=problem_id,
        sources=(),
        total_byte_count=0,
        creation_provenance=provenance,
    )
    run_input = RunInputManifestV1.create(
        problem=RunInputProblemV1(id=problem_id, description=problem_text),
        evidence_dossier_digest=dossier.dossier_digest,
    )
    bind_run_input(run_input, dossier, run_root)
    from tests.test_run_input_v6_commitments import _manifest as compile_version

    manifest = compile_version(5, run_input.run_input_digest)
    path, _ = bind_run_manifest(manifest, run_root)
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


def _typed_finish(manifest, calls):
    def finish_without_provider(
        harness, _config, _cycles, token_budget, on_cycle, run_manifest,
        progress_sink=None,
    ):
        assert run_manifest == manifest
        calls.append(token_budget)
        policy = StopPolicy(min_cycles=0, window=1, stable_windows=1)
        controller = StopController(policy)
        before = controller.snapshot()
        metrics = StopMetrics(cycle=len(calls) - 1)
        decision = controller.evaluate(metrics)
        stop = build_stop_record(
            reason=decision.reason,
            policy=policy,
            metrics=metrics,
            event_seq=harness._next_seq,
        )
        observation, snapshot, lifecycle = build_stopped_lifecycle(
            harness.workflow_state,
            manifest_digest=manifest.sha256,
            controller_version="workflow.controller.v3",
            workflow_profile="inquiry.active.v2",
            policy=policy,
            metrics=metrics,
            deterministic_decision=decision,
            controller_state_before=before,
            controller_state_after=controller.snapshot(),
            stop_event_seq=harness._next_seq,
            stop_record_digest=stop["digest"],
        )
        harness.record_lifecycle_transition(observation, snapshot, lifecycle)
        persist_stop_record(harness.root, stop)
        return (
            {"frontier": [], "survivors": [], "stop_reason": decision.reason},
            None,
            {"metered_tokens": None, "logged_tokens_this_run": 0, "delta": None},
        )

    return finish_without_provider


def test_start_poll_result_and_progress_notifications(tmp_path, monkeypatch):
    root = tmp_path / "run"
    text = "Why do explanations generalize?"
    manifest, manifest_path = _manifest(root, text)

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
    notifications = []
    started = _payload(
        _call(
            "start_run",
            {
                "root": str(root),
                "workload": "text",
                "problem": {"description": text},
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


def test_mcp_rejects_contained_v5_before_worker_or_capability_audits(
    tmp_path,
    monkeypatch,
):
    root = tmp_path / "run-v5"
    problem_text = "When is a simulation discriminating?"
    problem_id = spec_from_text(problem_text).problem.id
    manifest, manifest_path = _manifest_v5(
        tmp_path,
        root,
        problem_id=problem_id,
        problem_text=problem_text,
    )

    def fake_run(
        harness, _config, _cycles, token_budget, on_cycle, run_manifest,
        progress_sink=None,
    ):
        assert run_manifest == manifest
        on_cycle(_SchedulerView(harness, 1))
        return (
            {"frontier": [], "survivors": [], "problems": [], "diagnostics": []},
            None,
            {"metered_tokens": None, "logged_tokens_this_run": 0, "delta": None},
        )

    monkeypatch.setattr("deepreason.ops.run_scheduler", fake_run)
    rejected = _call(
        "start_run",
        {
            "root": str(root),
            "workload": "text",
            "problem": {"description": problem_text},
            "run_manifest_ref": str(manifest_path),
            "budget": {"cycles": 1, "token_budget": "unlimited"},
        },
    )
    assert rejected["isError"] is True
    assert "UNSUPPORTED_RUN_MANIFEST_VERSION" in rejected["content"][0]["text"]
    assert str(root.resolve()) not in mcp_server._RUN_THREADS
    assert not (root / "run-result.json").exists()
    assert not list(root.glob("*_AUDIT.*"))
    assert not (root / "REPLAY_VALIDATION.json").exists()


def test_cancel_waits_for_safe_boundary(tmp_path, monkeypatch):
    root = tmp_path / "run"
    text = "What makes a test discriminating?"
    manifest, manifest_path = _manifest(root, text)
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
    _payload(
        _call(
            "start_run",
            {
                "root": str(root),
                "workload": "text",
                "problem": {"description": text},
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

def test_typed_v6_stop_can_continue_and_append(tmp_path, monkeypatch):
    root = tmp_path / "converged-run"
    text = "When should search converge?"
    manifest, manifest_path = _manifest(root, text)

    calls = []
    monkeypatch.setattr("deepreason.ops.run_scheduler", _typed_finish(manifest, calls))
    _payload(
        _call(
            "start_run",
            {
                "root": str(root),
                "workload": "text",
                "problem": {"description": text},
                "run_manifest_ref": str(manifest_path),
                "budget": {"cycles": 12, "token_budget": "unlimited"},
            },
        )
    )
    mcp_server._RUN_THREADS[str(root.resolve())].join(timeout=2)
    assert _payload(_call("run_result", {"root": str(root)}))["stop"]["reason"] == "converged"
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
    assert calls == [None, None]


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
