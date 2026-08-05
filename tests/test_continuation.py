import json
import shutil
import subprocess
import tempfile
from pathlib import Path
from types import SimpleNamespace

import pytest

from deepreason.config import Config
from deepreason.run_manifest import bind_run_manifest, compile_run_manifest
from deepreason.runtime.continuation import prepare_continuation
from deepreason.runtime.stop import StopMetrics, StopPolicy, write_stop_record
from deepreason.workflow.lifecycle import RESUMABLE_STOP_REASONS


def _manifest():
    route = {
        "endpoint": "https://example.invalid/v1",
        "model": "gemma4:31b",
        "provider": "ollama",
        "family": "gemma",
    }
    return compile_run_manifest(
        Config(roles={"conjecturer": route}),
        single_model="gemma4:31b",
        rubric_policy="forbid",
        compiled_at="2026-07-13T00:00:00Z",
    )


def test_stop_history_is_preserved_behind_latest_pointer(tmp_path):
    policy = StopPolicy()
    first = write_stop_record(
        tmp_path, reason="converged", policy=policy,
        metrics=StopMetrics(cycle=8), event_seq=10,
    )
    second = write_stop_record(
        tmp_path, reason="completed", policy=policy,
        metrics=StopMetrics(cycle=12, workload_complete=True), event_seq=20,
    )
    assert first["digest"] != second["digest"]
    assert len(list((tmp_path / "run-stops").glob("*.json"))) == 2
    assert json.loads((tmp_path / "run-stop.json").read_text())["digest"] == second["digest"]


def test_continue_keeps_manifest_and_appends_after_stop(tmp_path, monkeypatch):
    manifest = _manifest()
    bind_run_manifest(manifest, tmp_path)
    monkeypatch.setattr(
        "deepreason.runtime.continuation.load_run_manifest",
        lambda _path: manifest,
    )
    stop = write_stop_record(
        tmp_path, reason="converged", policy=StopPolicy(),
        metrics=StopMetrics(cycle=8), event_seq=10,
    )
    first = prepare_continuation(
        tmp_path, cycles=5, tokens="unlimited",
        expected_manifest_digest=manifest.sha256,
    )
    second = prepare_continuation(
        tmp_path, cycles="unlimited", tokens=100,
        expected_manifest_digest=manifest.sha256,
    )
    assert first["prior_stop_digest"] == stop["digest"]
    assert second["seq"] == 1
    assert len((tmp_path / "continuations.jsonl").read_text().splitlines()) == 2
    assert (tmp_path / "run-manifest.json").read_bytes() == manifest.canonical_bytes()
    assert (tmp_path / "run-stops" / f"{10:012d}-{stop['digest']}.json").exists()


def test_continue_rejects_tampered_stop_digest(tmp_path, monkeypatch):
    manifest = _manifest()
    bind_run_manifest(manifest, tmp_path)
    monkeypatch.setattr(
        "deepreason.runtime.continuation.load_run_manifest",
        lambda _path: manifest,
    )
    stop = write_stop_record(
        tmp_path, reason="converged", policy=StopPolicy(),
        metrics=StopMetrics(cycle=8), event_seq=10,
    )
    stop["reason"] = "completed"
    (tmp_path / "run-stop.json").write_text(json.dumps(stop), encoding="utf-8")
    try:
        prepare_continuation(tmp_path, cycles=1, tokens=10)
    except ValueError as error:
        assert str(error) == "CONTINUE_STOP_DIGEST_MISMATCH"
    else:  # pragma: no cover - assertion clarity
        raise AssertionError("tampered stop record was accepted")


def _non_resumable_committed_roots() -> list[tuple[Path, str]]:
    """Committed roots whose recorded stop reason cannot authorize a resume.

    Selected from each root's OWN ``run-stop.json`` rather than from a list of
    names, and against the product's own ``RESUMABLE_STOP_REASONS`` rather than
    a literal: a change that reclassifies these stops empties the set and trips
    the guard below instead of leaving the assertion passing over nothing.

    Reading the reason is deliberately cheaper than reading the condition the
    code under test branches on. Opening a Harness per root to inspect
    ``terminal_lifecycle_decision`` replays every root (~63s) and asserts that
    branch back at itself; a root that somehow carried a receipt raises a
    DIFFERENT error below and fails loudly rather than being skipped.
    """

    tracked = subprocess.run(
        ["git", "ls-files", "experiments", "runs"],
        capture_output=True,
        text=True,
        check=True,
    ).stdout.splitlines()
    roots = sorted({Path(p).parent for p in tracked if p.endswith("/run-stop.json")})
    witnesses = []
    for root in roots:
        reason = json.loads((root / "run-stop.json").read_text()).get("reason")
        if reason not in RESUMABLE_STOP_REASONS:
            witnesses.append((root, reason))
    return witnesses


def test_a_stop_with_no_typed_receipt_refuses_continuation():
    """Regression (V1, tranche 2026-08-05-fix-continue-refusal-coverage):
    ``CONTINUE_TYPED_STOP_REQUIRED`` had no test the gate ran. Its only
    end-to-end witness was scripts/wheel_operational_smoke.py, which no pytest
    run executes, so 2d4ca2e1 could change what a budget-exhausted stop
    authorizes and leave the gate green for nine days.

    The witnesses are committed roots that really stopped -- today five
    operational_failure roots, e.g. failed-epoch1-run-9175f0ec -- not fixtures
    asserting the state into existence.
    """

    witnesses = _non_resumable_committed_roots()
    assert witnesses, (
        "no committed root carries a non-resumable stop; "
        "the refusal has lost its witness"
    )

    for root, reason in witnesses:
        # A copy, never the original: prepare_continuation opens a writable
        # Harness before it reaches the refusal, and a committed root is
        # evidence whose contents never change.
        with tempfile.TemporaryDirectory() as scratch:
            copy = Path(scratch) / root.name
            shutil.copytree(root, copy)
            with pytest.raises(ValueError) as raised:
                prepare_continuation(
                    copy, cycles=1, tokens=10, check_operator_lock=False
                )
        assert str(raised.value) == "CONTINUE_TYPED_STOP_REQUIRED", (
            f"{root.name} stopped on {reason!r} and was refused for the wrong "
            f"reason: {raised.value}"
        )


def test_v3_continuation_requires_checkpoint(tmp_path, monkeypatch):
    write_stop_record(
        tmp_path,
        reason="converged",
        policy=StopPolicy(),
        metrics=StopMetrics(cycle=8),
        event_seq=10,
    )
    manifest = SimpleNamespace(schema_version=3, sha256="a" * 64)
    monkeypatch.setattr(
        "deepreason.runtime.continuation.load_run_manifest", lambda _path: manifest
    )

    with pytest.raises(ValueError, match="CONTINUE_CHECKPOINT_REQUIRED"):
        prepare_continuation(tmp_path, cycles=1, tokens=10)
