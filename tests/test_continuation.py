import json
from types import SimpleNamespace

import pytest

from deepreason.config import Config
from deepreason.run_manifest import bind_run_manifest, compile_run_manifest
from deepreason.runtime.continuation import prepare_continuation
from deepreason.runtime.stop import StopMetrics, StopPolicy, write_stop_record


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
