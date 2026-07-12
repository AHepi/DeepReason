"""Same-root continuation with immutable manifest and preserved stop history."""

from __future__ import annotations

import fcntl
import hashlib
import json
import os
from pathlib import Path

from pydantic import BaseModel, ConfigDict

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
    for name in (".run-operator.lock", ".make-operator.lock"):
        path = root / name
        stream = path.open("a+b")
        try:
            try:
                fcntl.flock(stream.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
            except BlockingIOError as error:
                raise ValueError("CONTINUE_RUN_ACTIVE: operator lock is live") from error
            finally:
                try:
                    fcntl.flock(stream.fileno(), fcntl.LOCK_UN)
                except OSError:
                    pass
        finally:
            stream.close()


def prepare_continuation(
    root: Path | str,
    *,
    cycles: int | str | Limit,
    tokens: int | str | None | Limit,
    expected_manifest_digest: str | None = None,
) -> dict:
    root_path = Path(root)
    manifest = load_run_manifest(root_path / MANIFEST_NAME)
    if expected_manifest_digest and manifest.sha256 != expected_manifest_digest:
        raise ValueError("CONTINUE_MANIFEST_MISMATCH")
    stop_path = root_path / "run-stop.json"
    if not stop_path.exists():
        raise ValueError("CONTINUE_STOP_REQUIRED")
    stop = json.loads(stop_path.read_text(encoding="utf-8"))
    stop_digest = stop.get("digest") or _digest(stop)
    checkpoint = root_path / "checkpoint.json"
    if checkpoint.exists():
        try:
            json.loads(checkpoint.read_text(encoding="utf-8"))
        except json.JSONDecodeError as error:
            raise ValueError("CONTINUE_CHECKPOINT_INVALID") from error
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
