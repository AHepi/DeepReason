"""Public V6 terminal publication must validate the committed current epoch."""

from __future__ import annotations

import hashlib
import json
import threading

import pytest

import deepreason.application.text_runs as text_runs_module
from deepreason.application import (
    ContinueTextRunIntentV1,
    InspectTextRunIntentV1,
    RunBudgetIntentV1,
    StartTextRunIntentV1,
)
from deepreason.application.models import derive_model_execution_summary
from deepreason.application.text_runs import (
    TextRunApplicationService,
    TextRunWorkerRegistry,
)
from deepreason.canonical import canonical_json, sha256_hex
from deepreason.harness import Harness
from deepreason.locking import ProcessLock, ProcessLockBusy
from deepreason.runtime.stop import (
    StopController,
    StopMetrics,
    StopPolicy,
    build_stop_record,
    persist_stop_record,
)
from deepreason.runtime.continuation import prepare_continuation
from deepreason.runtime.terminal_authority import (
    _expected_commitment,
    derive_terminal_authority,
    ensure_terminal_commitment,
)
from deepreason.verification.report import (
    verify_post_commit_report,
    verify_root_report,
)
from deepreason.workflow.lifecycle import build_stopped_lifecycle
from deepreason.workflow.models import RunTerminalCommitmentV1
from tests.test_run_input_v6_commitments import (
    _bind_v2,
    _commitment,
    _manifest,
    _spec,
    _write_qualification,
)
from tests.test_v6_terminal_commitment_authority import _result_body


def _terminal_object_bytes(root):
    found = {}
    for schema in (
        "workflow-run-terminal-commitment-v1",
        "workflow-run-terminal-result-draft-v1",
    ):
        directory = root / "objects" / schema
        for path in sorted(directory.glob("*.json")):
            found[path.relative_to(root).as_posix()] = path.read_bytes()
    return found


def _derived_audit_bytes(root):
    return {
        name: (root / name).read_bytes()
        for name in (
            "CAPABILITY_REQUEST_AUDIT.md",
            "RESEARCH_SOURCE_AUDIT.md",
            "SIMULATION_RESULTS.md",
            "THEORY_TEST_LINEAGE.md",
            "TOKEN_ACCOUNTING.json",
        )
    }


def _terminal_commit_events(harness):
    return tuple(
        event
        for event in harness.log.read()
        if getattr(event.control, "action", None) == "terminal_committed"
    )


def _assert_current_validation(root, manifest, result, *, epoch):
    harness = Harness(root, read_only=True)
    commitment = harness.workflow_state.current_terminal_commitment
    assert commitment is not None
    assert commitment.terminal_epoch == epoch
    replay = json.loads((root / "REPLAY_VALIDATION.json").read_text())
    binding = replay["terminal_binding"]
    commitment_seq = harness.workflow_state.terminal_commitment_event_seq[
        commitment.id
    ]
    projection = {
        "verification": result["verification"],
        "completion_status": result["completion_status"],
        "canonical_bridge_eligible": result["canonical_bridge_eligible"],
    }

    assert replay["valid"] is True
    assert replay["manifest_digest"] == manifest.sha256
    assert binding["run_id"] == manifest.sha256
    assert binding["manifest_digest"] == manifest.sha256
    assert binding["terminal_epoch"] == epoch
    assert binding["terminal_commitment_ref"] == commitment.id
    assert binding["result_draft_ref"] == commitment.result_draft_ref
    assert binding["terminal_commitment_event_seq"] == commitment_seq
    assert (
        binding["reasoning_event_horizon_seq"]
        == commitment.reasoning_event_horizon_seq
    )
    assert binding["evaluated_event_horizon_seq"] >= commitment_seq
    assert (
        binding["evaluated_event_horizon_seq"]
        == replay["verification"]["stats"]["events"] - 1
    )
    assert (
        binding["terminal_commitment_ledger_digest"]
        == harness.workflow_state.terminal_commitment_ledger_digest
    )
    assert binding["stop_record_digest"] == commitment.stop_record_digest
    replay_base = {
        key: value
        for key, value in replay.items()
        if key != "terminal_binding"
    }
    assert binding["replay_validation_digest"] == sha256_hex(
        canonical_json(replay_base)
    )
    assert binding["result_projection_digest"] == sha256_hex(
        canonical_json(projection)
    )
    assert result["terminal_commitment_ref"] == commitment.id
    assert result["verification"]["valid"] is True
    assert result["verification"]["security_valid"] is True
    assert result["verification"]["integrity_valid"] is True
    assert derive_terminal_authority(
        root,
        manifest=manifest,
    ).terminal_commitment_ref == commitment.id
    return harness, commitment, replay


def _record_converged_stop(root, manifest, harness):
    policy = StopPolicy(min_cycles=0, window=1, stable_windows=1)
    resume = harness.workflow_state.current_resume_decision
    controller = StopController(
        policy,
        state=resume.controller_state if resume is not None else None,
    )
    before = controller.snapshot()
    cycle = 0 if before.last_cycle is None else before.last_cycle + 1
    metrics = StopMetrics(cycle=cycle)
    decision = controller.evaluate(metrics)
    assert decision.stop is True
    assert decision.reason == "converged"
    stop = build_stop_record(
        reason=decision.reason,
        policy=policy,
        metrics=metrics,
        event_seq=harness._next_seq,
    )
    control = manifest.control_plane_policy
    observation, snapshot, lifecycle = build_stopped_lifecycle(
        harness.workflow_state,
        manifest_digest=manifest.sha256,
        controller_version=control.controller_version,
        workflow_profile=control.workflow_profile,
        policy=policy,
        metrics=metrics,
        deterministic_decision=decision,
        controller_state_before=before,
        controller_state_after=controller.snapshot(),
        stop_event_seq=harness._next_seq,
        stop_record_digest=stop["digest"],
    )
    harness.record_lifecycle_transition(observation, snapshot, lifecycle)
    persist_stop_record(root, stop)
    return stop


def _start_converged_run(tmp_path, monkeypatch):
    root = tmp_path / "public-v6"
    commitment = _commitment()
    frozen = _bind_v2(root, commitment)
    manifest = _manifest(6, frozen.run_input_digest)
    _write_qualification(root, manifest)
    scheduler_calls = []

    def finish_without_provider(
        harness, _config, _cycles, token_budget, **_kwargs
    ):
        scheduler_calls.append(token_budget)
        stop = _record_converged_stop(root, manifest, harness)
        return (
            {
                "frontier": [],
                "survivors": [],
                "stop_reason": stop["reason"],
            },
            None,
            {
                "metered_tokens": None,
                "logged_tokens_this_run": 0,
                "delta": None,
                "note": "offline no-provider fixture",
            },
        )

    monkeypatch.setattr("deepreason.ops.run_scheduler", finish_without_provider)
    service = TextRunApplicationService(TextRunWorkerRegistry())
    started = service.start(
        StartTextRunIntentV1(
            root=str(root),
            workload=_spec(commitment),
            run_manifest_ref=str(tmp_path / "unused-manifest.json"),
            budget={"cycles": 1, "token_budget": "unlimited"},
        ),
        manifest_override=manifest,
        credential_checker=lambda _manifest: [],
    )
    service.wait(started.root, timeout=15)
    epoch_zero = service.result(
        InspectTextRunIntentV1(root=started.root)
    ).payload
    return root, manifest, service, scheduler_calls, epoch_zero


def _continue_converged_run(root, manifest, service):
    continued = service.continue_run(
        ContinueTextRunIntentV1(
            root=str(root),
            budget=RunBudgetIntentV1(cycles=1, token_budget="unlimited"),
            expected_manifest_digest=manifest.sha256,
        ),
        credential_checker=lambda _manifest: [],
    )
    service.wait(continued.root, timeout=15)
    return service.result(
        InspectTextRunIntentV1(root=continued.root)
    ).payload


def _forbid_dispatch(monkeypatch):
    def unexpected_dispatch(*_args, **_kwargs):
        pytest.fail("terminal recovery attempted provider or scheduler dispatch")

    monkeypatch.setattr("deepreason.ops.run_scheduler", unexpected_dispatch)
    monkeypatch.setattr(
        "deepreason.llm.endpoints.MockEndpoint.complete",
        unexpected_dispatch,
    )
    monkeypatch.setattr(
        "deepreason.llm.endpoints.OpenAICompatEndpoint.complete",
        unexpected_dispatch,
    )


def test_public_epochs_publish_only_commitment_inclusive_validation(
    tmp_path, monkeypatch
):
    root, manifest, service, scheduler_calls, epoch_zero = _start_converged_run(
        tmp_path,
        monkeypatch,
    )
    epoch_zero_harness, parent, _replay = _assert_current_validation(
        root,
        manifest,
        epoch_zero,
        epoch=0,
    )
    assert verify_root_report(root).valid is True
    assert verify_post_commit_report(root).valid is True
    assert scheduler_calls == [None]
    assert all(event.llm is None for event in epoch_zero_harness.log.read())
    epoch_zero_objects = _terminal_object_bytes(root)

    from deepreason.runtime import terminal_authority

    original_finalize = terminal_authority.finalize_terminal_result
    finalize_entered = threading.Event()
    permit_finalize = threading.Event()

    def pause_after_commit(harness, bound_manifest, result):
        finalize_entered.set()
        assert permit_finalize.wait(timeout=15)
        return original_finalize(harness, bound_manifest, result)

    monkeypatch.setattr(
        terminal_authority,
        "finalize_terminal_result",
        pause_after_commit,
    )
    continued = service.continue_run(
        ContinueTextRunIntentV1(
            root=str(root),
            budget=RunBudgetIntentV1(cycles=1, token_budget="unlimited"),
            expected_manifest_digest=manifest.sha256,
        ),
        credential_checker=lambda _manifest: [],
    )
    try:
        assert finalize_entered.wait(timeout=15)
        committed = Harness(root, read_only=True)
        child = committed.workflow_state.current_terminal_commitment
        assert child is not None
        assert child.terminal_epoch == 1
        assert child.parent_terminal_commitment_ref == parent.id
        assert (
            child.opening_resume_ref
            == committed.workflow_state.terminal_epoch_opening_resume_ref[1]
        )
        stale = json.loads((root / "REPLAY_VALIDATION.json").read_text())
        child_seq = committed.workflow_state.terminal_commitment_event_seq[
            child.id
        ]
        assert "terminal_binding" not in stale
        assert stale["valid"] is False
        assert stale["verification"]["stats"]["events"] - 1 < child_seq
        assert (
            json.loads((root / "run-result.json").read_text())[
                "terminal_commitment_ref"
            ]
            == parent.id
        )
        authority = derive_terminal_authority(root, manifest=manifest)
        assert authority.status == "invalid_incomplete"
    finally:
        permit_finalize.set()

    service.wait(continued.root, timeout=15)
    epoch_one = service.result(
        InspectTextRunIntentV1(root=continued.root)
    ).payload
    final_harness, child, _replay = _assert_current_validation(
        root,
        manifest,
        epoch_one,
        epoch=1,
    )
    assert child.parent_terminal_commitment_ref == parent.id
    assert (
        child.opening_resume_ref
        == final_harness.workflow_state.terminal_epoch_opening_resume_ref[1]
    )
    assert len(final_harness.workflow_state.terminal_commitments_by_epoch) == 2
    assert len(_terminal_commit_events(final_harness)) == 2
    assert scheduler_calls == [None, None]
    assert all(event.llm is None for event in final_harness.log.read())
    assert verify_root_report(root).valid is True
    assert verify_post_commit_report(root).valid is True
    final_objects = _terminal_object_bytes(root)
    assert all(final_objects[path] == data for path, data in epoch_zero_objects.items())


def test_public_recovery_completes_while_original_replay_refresh_is_interrupted(
    tmp_path, monkeypatch
):
    root, manifest, service, scheduler_calls, _epoch_zero = _start_converged_run(
        tmp_path,
        monkeypatch,
    )
    from deepreason.runtime import terminal_authority

    original_fresh = terminal_authority._fresh_replay_validation
    main_thread = threading.current_thread()
    refresh_entered = threading.Event()
    permit_refresh = threading.Event()

    def interrupt_original_refresh(bound_root):
        current = Harness(bound_root, read_only=True).workflow_state
        if (
            threading.current_thread() is not main_thread
            and current.current_terminal_epoch == 1
            and not refresh_entered.is_set()
        ):
            refresh_entered.set()
            assert permit_refresh.wait(timeout=15)
        return original_fresh(bound_root)

    def fail_fast_terminal_lock(harness):
        return ProcessLock(
            (
                harness.root
                / terminal_authority._TERMINAL_COMMITMENT_LOCK_NAME
            ),
            owner="terminal-commitment",
            blocking=False,
        )

    monkeypatch.setattr(
        terminal_authority,
        "_fresh_replay_validation",
        interrupt_original_refresh,
    )
    monkeypatch.setattr(
        terminal_authority,
        "_terminal_commitment_lock",
        fail_fast_terminal_lock,
    )
    continued = service.continue_run(
        ContinueTextRunIntentV1(
            root=str(root),
            budget=RunBudgetIntentV1(cycles=1, token_budget="unlimited"),
            expected_manifest_digest=manifest.sha256,
        ),
        credential_checker=lambda _manifest: [],
    )
    try:
        assert refresh_entered.wait(timeout=15)
        interrupted = Harness(root, read_only=True)
        child = interrupted.workflow_state.current_terminal_commitment
        assert child is not None
        assert child.terminal_epoch == 1
        assert child.opening_resume_ref == (
            interrupted.workflow_state.terminal_epoch_opening_resume_ref[1]
        )
        pending = json.loads((root / "run-result.json").read_text())
        replay = json.loads((root / "REPLAY_VALIDATION.json").read_text())
        assert pending["terminal_commitment_ref"] == child.id
        assert pending["verification"]["valid"] is False
        assert "terminal_binding" not in replay
        assert len(interrupted.workflow_state.terminal_commitments_by_epoch) == 2
        assert len(_terminal_commit_events(interrupted)) == 2
        assert len(_terminal_object_bytes(root)) == 4

        _forbid_dispatch(monkeypatch)
        recovered = TextRunApplicationService(TextRunWorkerRegistry()).result(
            InspectTextRunIntentV1(root=str(root))
        ).payload
    finally:
        permit_refresh.set()
        service.wait(continued.root, timeout=15)

    recovered_harness, recovered_child, _replay = _assert_current_validation(
        root,
        manifest,
        recovered,
        epoch=1,
    )
    assert recovered_child == child
    assert len(recovered_harness.workflow_state.terminal_commitments_by_epoch) == 2
    assert len(_terminal_commit_events(recovered_harness)) == 2
    assert len(_terminal_object_bytes(root)) == 4
    assert scheduler_calls == [None, None]


def test_restart_recovers_stale_preceding_epoch_without_redispatch(
    tmp_path, monkeypatch
):
    root, manifest, service, scheduler_calls, epoch_zero = _start_converged_run(
        tmp_path,
        monkeypatch,
    )
    epoch_zero_result = (root / "run-result.json").read_bytes()
    epoch_zero_replay = (root / "REPLAY_VALIDATION.json").read_bytes()
    epoch_one = _continue_converged_run(root, manifest, service)
    _harness, child, _replay = _assert_current_validation(
        root,
        manifest,
        epoch_one,
        epoch=1,
    )
    expected_result = (root / "run-result.json").read_bytes()
    expected_replay = (root / "REPLAY_VALIDATION.json").read_bytes()
    log_bytes = (root / "log.jsonl").read_bytes()
    immutable_bytes = _terminal_object_bytes(root)
    audit_bytes = _derived_audit_bytes(root)

    (root / "run-result.json").write_bytes(epoch_zero_result)
    (root / "REPLAY_VALIDATION.json").write_bytes(epoch_zero_replay)
    _forbid_dispatch(monkeypatch)
    restarted = TextRunApplicationService(TextRunWorkerRegistry())
    recovered = restarted.result(
        InspectTextRunIntentV1(root=str(root))
    ).payload

    assert recovered == epoch_one
    assert recovered["terminal_commitment_ref"] == child.id
    assert scheduler_calls == [None, None]
    assert (root / "log.jsonl").read_bytes() == log_bytes
    assert _terminal_object_bytes(root) == immutable_bytes
    assert _derived_audit_bytes(root) == audit_bytes
    assert len(_terminal_commit_events(Harness(root, read_only=True))) == 2
    assert (root / "run-result.json").read_bytes() == expected_result
    assert (root / "REPLAY_VALIDATION.json").read_bytes() == expected_replay

    first_result_bytes = (root / "run-result.json").read_bytes()
    first_replay_bytes = (root / "REPLAY_VALIDATION.json").read_bytes()
    assert TextRunApplicationService(TextRunWorkerRegistry()).result(
        InspectTextRunIntentV1(root=str(root))
    ).payload == epoch_one
    assert (root / "run-result.json").read_bytes() == first_result_bytes
    assert (root / "REPLAY_VALIDATION.json").read_bytes() == first_replay_bytes
    assert (root / "log.jsonl").read_bytes() == log_bytes
    assert _terminal_object_bytes(root) == immutable_bytes
    assert _derived_audit_bytes(root) == audit_bytes


def test_interrupted_replay_and_result_publication_recover_exact_bytes(
    tmp_path, monkeypatch
):
    root, manifest, service, scheduler_calls, epoch_zero = _start_converged_run(
        tmp_path,
        monkeypatch,
    )
    epoch_zero_replay = (root / "REPLAY_VALIDATION.json").read_bytes()
    epoch_one = _continue_converged_run(root, manifest, service)
    harness, child, _replay = _assert_current_validation(
        root,
        manifest,
        epoch_one,
        epoch=1,
    )
    expected_result_bytes = (root / "run-result.json").read_bytes()
    expected_replay_bytes = (root / "REPLAY_VALIDATION.json").read_bytes()
    log_bytes = (root / "log.jsonl").read_bytes()
    immutable_bytes = _terminal_object_bytes(root)
    audit_bytes = _derived_audit_bytes(root)
    from deepreason.runtime import terminal_authority

    expected, _draft = terminal_authority._expected_terminal_result(
        harness,
        manifest,
        child,
    )
    pending = terminal_authority._pending_terminal_result(expected)
    (root / "run-result.json").write_bytes(canonical_json(pending) + b"\n")
    (root / "REPLAY_VALIDATION.json").write_bytes(epoch_zero_replay)
    _forbid_dispatch(monkeypatch)

    original_atomic = terminal_authority._atomic_json
    replacement_attempted = False

    def interrupt_replay_replacement(path, value):
        nonlocal replacement_attempted
        if path.name == "REPLAY_VALIDATION.json" and not replacement_attempted:
            replacement_attempted = True
            raise OSError("simulated replay replacement interruption")
        return original_atomic(path, value)

    monkeypatch.setattr(
        terminal_authority,
        "_atomic_json",
        interrupt_replay_replacement,
    )
    with pytest.raises(OSError, match="simulated replay replacement interruption"):
        TextRunApplicationService(TextRunWorkerRegistry()).result(
            InspectTextRunIntentV1(root=str(root))
        )
    assert replacement_attempted is True
    assert json.loads((root / "run-result.json").read_text()) == pending
    assert (root / "REPLAY_VALIDATION.json").read_bytes() == epoch_zero_replay
    assert derive_terminal_authority(
        root,
        manifest=manifest,
    ).status == "current_valid_committed"

    monkeypatch.setattr(terminal_authority, "_atomic_json", original_atomic)
    recovered = TextRunApplicationService(TextRunWorkerRegistry()).result(
        InspectTextRunIntentV1(root=str(root))
    ).payload
    assert recovered == epoch_one
    assert (root / "run-result.json").read_bytes() == expected_result_bytes
    assert (root / "REPLAY_VALIDATION.json").read_bytes() == expected_replay_bytes

    (root / "run-result.json").write_bytes(canonical_json(pending) + b"\n")
    assert (root / "REPLAY_VALIDATION.json").read_bytes() == expected_replay_bytes
    recovered_after_result_interruption = TextRunApplicationService(
        TextRunWorkerRegistry()
    ).result(InspectTextRunIntentV1(root=str(root))).payload

    assert recovered_after_result_interruption == epoch_one
    assert epoch_zero["terminal_commitment_ref"] != child.id
    assert (root / "run-result.json").read_bytes() == expected_result_bytes
    assert (root / "REPLAY_VALIDATION.json").read_bytes() == expected_replay_bytes
    assert (root / "log.jsonl").read_bytes() == log_bytes
    assert _terminal_object_bytes(root) == immutable_bytes
    assert _derived_audit_bytes(root) == audit_bytes
    assert len(_terminal_commit_events(Harness(root, read_only=True))) == 2
    assert scheduler_calls == [None, None]


def test_windows_text_translation_cannot_change_terminal_json_bytes(
    tmp_path, monkeypatch
):
    from deepreason.runtime import progress as progress_module

    original_fdopen = progress_module.os.fdopen
    opened_modes = []

    def windows_translation_oracle(descriptor, mode, *args, **kwargs):
        opened_modes.append(mode)
        if "b" not in mode:
            kwargs["newline"] = "\r\n"
        return original_fdopen(descriptor, mode, *args, **kwargs)

    monkeypatch.setattr(progress_module.os, "fdopen", windows_translation_oracle)
    root, manifest, _service, scheduler_calls, terminal = _start_converged_run(
        tmp_path,
        monkeypatch,
    )
    raw = (root / "run-result.json").read_bytes()
    expected = (
        json.dumps(terminal, sort_keys=True, separators=(",", ":")).encode("utf-8")
        + b"\n"
    )

    assert raw.decode("utf-8")
    assert raw == expected
    assert raw.endswith(b"\n")
    assert not raw.endswith(b"\n\n")
    assert not raw.endswith(b"\r\n")
    assert not raw.startswith(b"\xef\xbb\xbf")
    harness, commitment, _replay = _assert_current_validation(
        root,
        manifest,
        terminal,
        epoch=0,
    )
    assert verify_post_commit_report(root).valid is True

    log_bytes = (root / "log.jsonl").read_bytes()
    replay_bytes = (root / "REPLAY_VALIDATION.json").read_bytes()
    immutable_bytes = _terminal_object_bytes(root)
    _forbid_dispatch(monkeypatch)
    recovered = TextRunApplicationService(TextRunWorkerRegistry()).result(
        InspectTextRunIntentV1(root=str(root))
    ).payload

    assert recovered == terminal
    assert (root / "run-result.json").read_bytes() == raw
    assert (root / "REPLAY_VALIDATION.json").read_bytes() == replay_bytes
    assert (root / "log.jsonl").read_bytes() == log_bytes
    assert _terminal_object_bytes(root) == immutable_bytes
    recovered_harness = Harness(root, read_only=True)
    assert recovered_harness.workflow_state.current_terminal_commitment == commitment
    assert len(_terminal_commit_events(recovered_harness)) == 1
    assert scheduler_calls == [None]

    representative = tmp_path / "representative.json"
    progress_module._atomic_json(
        representative,
        {
            "z": {
                "unicode": "Māori—雪",
                "logical_newline": "line1\nline2",
            },
            "a": [True, None, 3, 1.25],
        },
    )
    golden = (
        b'{"a":[true,null,3,1.25],"z":{"logical_newline":"line1\\nline2",'
        b'"unicode":"M\\u0101ori\\u2014\\u96ea"}}\n'
    )
    representative_bytes = representative.read_bytes()
    assert representative_bytes == golden
    assert (
        hashlib.sha256(representative_bytes).hexdigest()
        == "3d88b7505b375a2b0af1f95aae511436fda72ae8341be812fbda0729e7211c39"
    )
    assert representative_bytes.count(b"\n") == 1
    assert b"line1\\nline2" in representative_bytes
    assert not representative_bytes.endswith(b"\r\n")
    assert "wb" in opened_modes
    assert all("b" in mode for mode in opened_modes)


def test_failed_post_commit_refresh_leaves_fail_closed_recoverable_result(
    tmp_path, monkeypatch
):
    root, manifest, service, scheduler_calls, _epoch_zero = _start_converged_run(
        tmp_path,
        monkeypatch,
    )
    preceding_result = (root / "run-result.json").read_bytes()
    preceding_replay = (root / "REPLAY_VALIDATION.json").read_bytes()
    epoch_one = _continue_converged_run(root, manifest, service)
    harness, child, _replay = _assert_current_validation(
        root,
        manifest,
        epoch_one,
        epoch=1,
    )
    log_bytes = (root / "log.jsonl").read_bytes()
    immutable_bytes = _terminal_object_bytes(root)

    (root / "run-result.json").write_bytes(preceding_result)
    (root / "REPLAY_VALIDATION.json").write_bytes(preceding_replay)
    _forbid_dispatch(monkeypatch)
    from deepreason.runtime import terminal_authority

    original_fresh = terminal_authority._fresh_replay_validation

    def fail_refresh(_root):
        raise RuntimeError("simulated post-commit refresh failure")

    monkeypatch.setattr(
        terminal_authority,
        "_fresh_replay_validation",
        fail_refresh,
    )
    with pytest.raises(RuntimeError, match="simulated post-commit refresh failure"):
        TextRunApplicationService(TextRunWorkerRegistry()).result(
            InspectTextRunIntentV1(root=str(root))
        )
    pending = json.loads((root / "run-result.json").read_text())
    assert pending["state"] == "completed"
    assert pending["terminal_commitment_ref"] == child.id
    assert pending["verification"]["valid"] is False
    assert pending["verification"]["integrity_valid"] is False
    assert pending["canonical_bridge_eligible"] is False
    assert (root / "log.jsonl").read_bytes() == log_bytes
    assert _terminal_object_bytes(root) == immutable_bytes
    assert len(_terminal_commit_events(Harness(root))) == 2
    assert scheduler_calls == [None, None]

    monkeypatch.setattr(
        terminal_authority,
        "_fresh_replay_validation",
        original_fresh,
    )
    recovered = TextRunApplicationService(TextRunWorkerRegistry()).result(
        InspectTextRunIntentV1(root=str(root))
    ).payload
    assert recovered == epoch_one
    assert (root / "log.jsonl").read_bytes() == log_bytes
    assert _terminal_object_bytes(root) == immutable_bytes
    assert harness.workflow_state.terminal_commitments_by_epoch == (
        Harness(root).workflow_state.terminal_commitments_by_epoch
    )


def test_worker_post_commit_publication_failure_preserves_terminal_authority(
    tmp_path, monkeypatch
):
    root, manifest, service, scheduler_calls, _epoch_zero = _start_converged_run(
        tmp_path,
        monkeypatch,
    )
    from deepreason.runtime import terminal_authority

    original_fresh = terminal_authority._fresh_replay_validation
    original_v6_result = text_runs_module._v6_run_result
    failure_text = "SENTINEL_POST_COMMIT_PUBLICATION_EXCEPTION"
    observed_result_states: list[str] = []
    captured: dict[str, object] = {}

    def observe_v6_result(*args, **kwargs):
        payload = args[2]
        observed_result_states.append(payload["state"])
        return original_v6_result(*args, **kwargs)

    def fail_after_current_pending_result(bound_root):
        durable = Harness(bound_root, read_only=True)
        commitment = durable.workflow_state.current_terminal_commitment
        if (
            commitment is not None
            and commitment.terminal_epoch == 1
            and not captured
        ):
            pending = json.loads(
                (root / "run-result.json").read_text(encoding="utf-8")
            )
            assert pending["terminal_commitment_ref"] == commitment.id
            assert pending["verification"]["valid"] is False
            replay = json.loads(
                (root / "REPLAY_VALIDATION.json").read_text(encoding="utf-8")
            )
            assert "terminal_binding" not in replay
            captured.update(
                {
                    "log": (root / "log.jsonl").read_bytes(),
                    "stop_pointer": (root / "run-stop.json").read_bytes(),
                    "checkpoint": (root / "checkpoint.json").read_bytes(),
                    "workflow_checkpoint": (
                        root / "workflow-checkpoint.json"
                    ).read_bytes(),
                    "pending_result": (root / "run-result.json").read_bytes(),
                    "replay": (root / "REPLAY_VALIDATION.json").read_bytes(),
                    "stops": {
                        path.relative_to(root).as_posix(): path.read_bytes()
                        for path in sorted((root / "run-stops").glob("*.json"))
                    },
                    "terminal_objects": _terminal_object_bytes(root),
                    "commitment": commitment,
                }
            )
            raise ProcessLockBusy(failure_text)
        return original_fresh(bound_root)

    monkeypatch.setattr(
        text_runs_module,
        "_v6_run_result",
        observe_v6_result,
    )
    monkeypatch.setattr(
        terminal_authority,
        "_fresh_replay_validation",
        fail_after_current_pending_result,
    )
    continued = service.continue_run(
        ContinueTextRunIntentV1(
            root=str(root),
            budget=RunBudgetIntentV1(cycles=1, token_budget="unlimited"),
            expected_manifest_digest=manifest.sha256,
        ),
        credential_checker=lambda _manifest: [],
    )
    service.wait(continued.root, timeout=15)

    worker = service.registry.threads[str(root.resolve())]
    assert not worker.is_alive()
    assert captured
    current_stops = {
        path.relative_to(root).as_posix(): path.read_bytes()
        for path in sorted((root / "run-stops").glob("*.json"))
    }
    current_terminal_objects = _terminal_object_bytes(root)
    committed = Harness(root, read_only=True)
    child = captured["commitment"]
    status = service.inspect(
        InspectTextRunIntentV1(root=str(root))
    ).presentation_payload()
    observed = {
        "single_completed_terminal_attempt": observed_result_states
        == ["completed"],
        "event_log_preserved": (
            root / "log.jsonl"
        ).read_bytes()
        == captured["log"],
        "stop_pointer_preserved": (
            root / "run-stop.json"
        ).read_bytes()
        == captured["stop_pointer"],
        "checkpoint_preserved": (
            root / "checkpoint.json"
        ).read_bytes()
        == captured["checkpoint"],
        "workflow_checkpoint_preserved": (
            root / "workflow-checkpoint.json"
        ).read_bytes()
        == captured["workflow_checkpoint"],
        "pending_result_preserved": (
            root / "run-result.json"
        ).read_bytes()
        == captured["pending_result"],
        "replay_preserved": (
            root / "REPLAY_VALIDATION.json"
        ).read_bytes()
        == captured["replay"],
        "stop_inventory_preserved": current_stops == captured["stops"],
        "terminal_inventory_preserved": (
            current_terminal_objects == captured["terminal_objects"]
        ),
        "current_commitment_preserved": (
            committed.workflow_state.current_terminal_commitment == child
        ),
        "commitment_count": len(
            committed.workflow_state.terminal_commitments_by_epoch
        ),
        "commitment_event_count": len(_terminal_commit_events(committed)),
        "draft_and_commitment_object_count": len(current_terminal_objects),
        "fixed_operational_status": (
            status["state"] == "failed"
            and status["phase"] == "stop"
            and status["activity"]
            == "terminal publication recovery required"
            and status["message"]
            == "TERMINAL_PUBLICATION_RECOVERY_REQUIRED"
            and status["stop_reason"] == "operational_failure"
        ),
    }
    assert observed == {
        "single_completed_terminal_attempt": True,
        "event_log_preserved": True,
        "stop_pointer_preserved": True,
        "checkpoint_preserved": True,
        "workflow_checkpoint_preserved": True,
        "pending_result_preserved": True,
        "replay_preserved": True,
        "stop_inventory_preserved": True,
        "terminal_inventory_preserved": True,
        "current_commitment_preserved": True,
        "commitment_count": 2,
        "commitment_event_count": 2,
        "draft_and_commitment_object_count": 4,
        "fixed_operational_status": True,
    }
    public_operational_bytes = json.dumps(
        {
            "status": status,
            "result": json.loads(
                (root / "run-result.json").read_text(encoding="utf-8")
            ),
        },
        sort_keys=True,
    )
    assert failure_text not in public_operational_bytes

    monkeypatch.setattr(
        terminal_authority,
        "_fresh_replay_validation",
        original_fresh,
    )
    _forbid_dispatch(monkeypatch)
    recovered = service.result(
        InspectTextRunIntentV1(root=str(root))
    ).payload
    recovered_harness, recovered_child, _replay = _assert_current_validation(
        root,
        manifest,
        recovered,
        epoch=1,
    )
    assert recovered_child == child
    assert len(recovered_harness.workflow_state.terminal_commitments_by_epoch) == 2
    assert len(_terminal_commit_events(recovered_harness)) == 2
    assert (root / "log.jsonl").read_bytes() == captured["log"]
    assert (root / "run-stop.json").read_bytes() == captured["stop_pointer"]
    assert {
        path.relative_to(root).as_posix(): path.read_bytes()
        for path in sorted((root / "run-stops").glob("*.json"))
    } == captured["stops"]
    assert _terminal_object_bytes(root) == captured["terminal_objects"]
    assert scheduler_calls == [None, None]


def test_foreign_or_stale_validation_binding_is_rederived(
    tmp_path, monkeypatch
):
    root, manifest, service, scheduler_calls, _epoch_zero = _start_converged_run(
        tmp_path,
        monkeypatch,
    )
    epoch_one = _continue_converged_run(root, manifest, service)
    harness, child, good_replay = _assert_current_validation(
        root,
        manifest,
        epoch_one,
        epoch=1,
    )
    parent = harness.workflow_state.terminal_commitments_by_epoch[0]
    parent_seq = harness.workflow_state.terminal_commitment_event_seq[parent.id]
    child_seq = harness.workflow_state.terminal_commitment_event_seq[child.id]
    log_bytes = (root / "log.jsonl").read_bytes()
    immutable_bytes = _terminal_object_bytes(root)
    good_result_bytes = (root / "run-result.json").read_bytes()
    good_replay_bytes = (root / "REPLAY_VALIDATION.json").read_bytes()
    variants = {
        "preceding_epoch": {
            "terminal_epoch": 0,
            "terminal_commitment_ref": parent.id,
            "result_draft_ref": parent.result_draft_ref,
            "parent_terminal_commitment_ref": None,
            "opening_resume_ref": None,
            "terminal_commitment_event_seq": parent_seq,
            "reasoning_event_horizon_seq": parent.reasoning_event_horizon_seq,
            "stop_record_digest": parent.stop_record_digest,
        },
        "excluded_commitment_event": {
            "evaluated_event_horizon_seq": child_seq - 1,
        },
        "foreign_run": {"run_id": "f" * 64},
        "foreign_manifest": {
            "run_id": "e" * 64,
            "manifest_digest": "e" * 64,
        },
        "wrong_commitment": {"terminal_commitment_ref": parent.id},
    }

    _forbid_dispatch(monkeypatch)
    for changes in variants.values():
        stale = json.loads(canonical_json(good_replay))
        stale["terminal_binding"].update(changes)
        (root / "REPLAY_VALIDATION.json").write_bytes(canonical_json(stale) + b"\n")
        authority = derive_terminal_authority(root, manifest=manifest)
        assert authority.status == "invalid_incomplete"
        recovered = TextRunApplicationService(TextRunWorkerRegistry()).result(
            InspectTextRunIntentV1(root=str(root))
        ).payload
        assert recovered == epoch_one
        assert (root / "run-result.json").read_bytes() == good_result_bytes
        assert (root / "REPLAY_VALIDATION.json").read_bytes() == good_replay_bytes
        assert (root / "log.jsonl").read_bytes() == log_bytes
        assert _terminal_object_bytes(root) == immutable_bytes

    mixed = json.loads(canonical_json(good_replay))
    mixed["verification"]["stats"]["artifacts"] += 1
    (root / "REPLAY_VALIDATION.json").write_bytes(canonical_json(mixed) + b"\n")
    assert derive_terminal_authority(
        root,
        manifest=manifest,
    ).status == "invalid_incomplete"
    assert TextRunApplicationService(TextRunWorkerRegistry()).result(
        InspectTextRunIntentV1(root=str(root))
    ).payload == epoch_one

    foreign_process = json.loads(canonical_json(good_replay))
    process_digest = foreign_process["workflow_process_digest"]
    foreign_digest = (
        "sha256:" + "f" * 64
        if process_digest.startswith("sha256:")
        else "f" * 64
    )
    foreign_process["workflow_process_digest"] = foreign_digest
    foreign_process["verification"]["stats"][
        "workflow_process_digest"
    ] = foreign_digest
    foreign_base = {
        key: value
        for key, value in foreign_process.items()
        if key != "terminal_binding"
    }
    foreign_process["terminal_binding"]["replay_validation_digest"] = sha256_hex(
        canonical_json(foreign_base)
    )
    (root / "REPLAY_VALIDATION.json").write_bytes(
        canonical_json(foreign_process) + b"\n"
    )
    assert derive_terminal_authority(
        root,
        manifest=manifest,
    ).status == "invalid_incomplete"
    assert TextRunApplicationService(TextRunWorkerRegistry()).result(
        InspectTextRunIntentV1(root=str(root))
    ).payload == epoch_one

    (root / "REPLAY_VALIDATION.json").unlink()
    assert derive_terminal_authority(
        root,
        manifest=manifest,
    ).status == "invalid_incomplete"
    assert TextRunApplicationService(TextRunWorkerRegistry()).result(
        InspectTextRunIntentV1(root=str(root))
    ).payload == epoch_one
    assert scheduler_calls == [None, None]
    assert (root / "log.jsonl").read_bytes() == log_bytes
    assert _terminal_object_bytes(root) == immutable_bytes


def test_open_epoch_rejects_missing_or_broken_child_commitment(
    tmp_path, monkeypatch
):
    root, manifest, service, scheduler_calls, _epoch_zero = _start_converged_run(
        tmp_path,
        monkeypatch,
    )
    parent = Harness(root).workflow_state.current_terminal_commitment
    prepare_continuation(
        root,
        cycles=1,
        tokens="unlimited",
        expected_manifest_digest=manifest.sha256,
        check_operator_lock=False,
    )
    opened = Harness(root)
    assert opened.workflow_state.current_terminal_epoch == 1
    assert opened.workflow_state.current_terminal_commitment is None
    missing = derive_terminal_authority(root, manifest=manifest)
    assert missing.status == "invalid_incomplete"
    assert missing.detail_code == "TERMINAL_COMMITMENT_REQUIRED"
    with pytest.raises(ValueError, match="^RUN_RESULT_NOT_READY:"):
        service.result(InspectTextRunIntentV1(root=str(root)))

    opened.record_measure(
        inputs=["run-resume", parent.stop_record_digest, manifest.sha256]
    )
    stop = _record_converged_stop(root, manifest, opened)
    summary = derive_model_execution_summary(
        opened,
        manifest,
        event_horizon_seq=stop["event_seq"],
    )
    draft, correct = _expected_commitment(
        opened,
        manifest,
        terminal_status="completed",
        stop=stop,
        model_execution=summary,
        result_body=_result_body("completed", stop, summary),
        commitment_event_seq=opened._next_seq,
    )
    values = correct.model_dump(
        mode="python",
        by_alias=True,
        exclude={"id"},
        exclude_none=False,
    )
    with pytest.raises(
        ValueError,
        match="child terminal epoch requires parent and resume references",
    ):
        RunTerminalCommitmentV1.create(
            **{
                **values,
                "opening_resume_ref": None,
            }
        )
    broken_parent = RunTerminalCommitmentV1.create(
        **{
            **values,
            "parent_terminal_commitment_ref": "sha256:" + "f" * 64,
        }
    )
    _forbid_dispatch(monkeypatch)
    with pytest.raises(
        ValueError,
        match="terminal child epoch differs from resume authority",
    ):
        opened.record_terminal_commitment(broken_parent, draft)
    assert Harness(root).workflow_state.current_terminal_commitment is None
    assert len(_terminal_commit_events(Harness(root))) == 1

    opened.record_terminal_commitment(correct, draft)
    objects_before_conflict = _terminal_object_bytes(root)
    with pytest.raises(ValueError, match="^TERMINAL_COMMITMENT_CONFLICT$"):
        ensure_terminal_commitment(
            opened,
            manifest,
            terminal_status="completed",
            stop=stop,
            model_execution=summary,
            result_body={
                **_result_body("completed", stop, summary),
                "completion_status": "incomplete",
            },
        )
    committed = Harness(root, read_only=True)
    assert committed.workflow_state.current_terminal_commitment == correct
    assert len(committed.workflow_state.terminal_commitments_by_epoch) == 2
    assert len(_terminal_commit_events(committed)) == 2
    assert _terminal_object_bytes(root) == objects_before_conflict
    assert scheduler_calls == [None]


def test_budget_exhausted_terminal_remains_non_resumable(tmp_path, monkeypatch):
    root = tmp_path / "budget-terminal"
    commitment = _commitment()
    frozen = _bind_v2(root, commitment)
    manifest = _manifest(6, frozen.run_input_digest)
    _write_qualification(root, manifest)
    scheduler_calls = []

    def exhaust_budget(_harness, _config, _cycles, token_budget, **_kwargs):
        scheduler_calls.append(token_budget)
        return (
            {"frontier": [], "survivors": []},
            None,
            {
                "metered_tokens": None,
                "logged_tokens_this_run": 0,
                "delta": None,
                "note": "offline budget exhaustion",
            },
        )

    monkeypatch.setattr("deepreason.ops.run_scheduler", exhaust_budget)
    service = TextRunApplicationService(TextRunWorkerRegistry())
    started = service.start(
        StartTextRunIntentV1(
            root=str(root),
            workload=_spec(commitment),
            run_manifest_ref=str(tmp_path / "unused-manifest.json"),
            budget={"cycles": 1, "token_budget": "unlimited"},
        ),
        manifest_override=manifest,
        credential_checker=lambda _manifest: [],
    )
    service.wait(started.root, timeout=15)
    terminal = service.result(
        InspectTextRunIntentV1(root=started.root)
    ).payload
    assert terminal["stop"]["reason"] == "budget_exhausted"
    assert terminal["verification"]["valid"] is True
    assert Harness(root).workflow_state.terminal_lifecycle_decision is None

    with pytest.raises(ValueError, match="^CONTINUE_TYPED_STOP_REQUIRED$"):
        service.continue_run(
            ContinueTextRunIntentV1(
                root=str(root),
                budget=RunBudgetIntentV1(cycles=1, token_budget="unlimited"),
                expected_manifest_digest=manifest.sha256,
            ),
            credential_checker=lambda _manifest: [],
        )
    assert scheduler_calls == [None]
