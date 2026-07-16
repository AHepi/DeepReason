"""Same-root continuation with immutable manifest and preserved stop history."""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path

from pydantic import BaseModel, ConfigDict

from deepreason.locking import ProcessLockBusy, operator_locks
from deepreason.run_manifest import MANIFEST_NAME, load_run_manifest
from deepreason.runtime.budget import Limit, parse_limit
from deepreason.runtime.progress import ProgressSink


class ContinuationRequest(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    cycles: Limit
    tokens: Limit


def _digest(value: dict) -> str:
    return hashlib.sha256(
        json.dumps(value, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()


def _assert_no_live_lock(root: Path) -> None:
    try:
        locks = operator_locks(root, owner="continue-check", blocking=False)
    except ProcessLockBusy as error:
        raise ValueError("CONTINUE_RUN_ACTIVE: operator lock is live") from error
    locks.release()


def prepare_continuation(
    root: Path | str,
    *,
    cycles: int | str | Limit,
    tokens: int | str | None | Limit,
    expected_manifest_digest: str | None = None,
    check_operator_lock: bool = True,
) -> dict:
    root_path = Path(root)
    manifest = load_run_manifest(root_path / MANIFEST_NAME)
    if expected_manifest_digest and manifest.sha256 != expected_manifest_digest:
        raise ValueError("CONTINUE_MANIFEST_MISMATCH")
    stop_path = root_path / "run-stop.json"
    if not stop_path.exists():
        raise ValueError("CONTINUE_STOP_REQUIRED")
    stop = json.loads(stop_path.read_text(encoding="utf-8"))
    if not isinstance(stop, dict):
        raise ValueError("CONTINUE_STOP_INVALID")
    claimed_stop_digest = stop.get("digest")
    unsigned_stop = {key: value for key, value in stop.items() if key != "digest"}
    stop_digest = _digest(unsigned_stop)
    if claimed_stop_digest not in (None, stop_digest):
        raise ValueError("CONTINUE_STOP_DIGEST_MISMATCH")
    checkpoint = root_path / "checkpoint.json"
    if manifest.schema_version in {2, 3, 4} and not checkpoint.exists():
        raise ValueError("CONTINUE_CHECKPOINT_REQUIRED")
    if checkpoint.exists():
        try:
            fence = json.loads(checkpoint.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as error:
            raise ValueError("CONTINUE_CHECKPOINT_INVALID") from error
        expected = {
            "schema": "deepreason-checkpoint-v1",
            "manifest_digest": manifest.sha256,
            "stop_digest": stop_digest,
        }
        if not isinstance(fence, dict) or any(
            fence.get(key) != value for key, value in expected.items()
        ):
            raise ValueError("CONTINUE_CHECKPOINT_MISMATCH")
        from deepreason.harness import Harness

        if fence.get("event_seq") != Harness(root_path)._next_seq:
            raise ValueError("CONTINUE_CHECKPOINT_EVENT_FENCE_MISMATCH")
    if check_operator_lock:
        _assert_no_live_lock(root_path)
    cycle_limit, cycle_diagnostic = parse_limit(cycles, optional=False)
    token_limit, token_diagnostic = parse_limit(tokens)
    request = ContinuationRequest(cycles=cycle_limit, tokens=token_limit)

    # Preserve a legacy/latest stop before the mutable latest pointer changes
    # on a later stop.
    history = root_path / "run-stops" / (
        f"{int(stop.get('event_seq', 0)):012d}-{stop_digest}.json"
    )
    history.parent.mkdir(parents=True, exist_ok=True)
    if not history.exists():
        history.write_text(
            json.dumps(stop, sort_keys=True, separators=(",", ":")) + "\n",
            encoding="utf-8",
        )

    log_path = root_path / "continuations.jsonl"
    seq = len(log_path.read_text(encoding="utf-8").splitlines()) if log_path.exists() else 0
    record = {
        "schema": "deepreason-continuation-v1",
        "seq": seq,
        "manifest_digest": manifest.sha256,
        "prior_stop_digest": stop_digest,
        "request": request.model_dump(mode="json"),
        "diagnostics": [
            item for item in (cycle_diagnostic, token_diagnostic) if item is not None
        ],
    }
    with log_path.open("a", encoding="utf-8") as stream:
        stream.write(json.dumps(record, sort_keys=True, separators=(",", ":")) + "\n")
        stream.flush()
        os.fsync(stream.fileno())

    workload = getattr(manifest, "workload_profile", None) or "text"
    sink = ProgressSink(root_path, run_id=manifest.sha256, workload=workload)
    sink.clear_cancellation()
    sink.emit(
        state="running",
        phase="resume",
        activity="continuation prepared",
        message=f"resuming after {stop_digest[:12]}",
    )
    return record
