"""Strict, read-only projection of operational progress files."""

from __future__ import annotations

import json
from pathlib import Path

from deepreason.runtime.progress import ProgressEvent


def _events(path: Path) -> list[ProgressEvent]:
    if not path.exists():
        return []
    events = [
        ProgressEvent.model_validate_json(line)
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    for expected, event in enumerate(events):
        if event.seq != expected:
            raise ValueError("progress sequence is not contiguous")
    return events


def read_run_status(root: Path | str, *, since_seq: int = -1) -> dict:
    """Read fixed operational records below ``root``; never mutate graph state."""
    if since_seq < -1:
        raise ValueError("since_seq must be -1 or a non-negative progress sequence")
    root_path = Path(root)
    progress_path = root_path / "progress.jsonl"
    events = _events(progress_path)
    status_path = root_path / "run-status.json"
    if status_path.exists():
        latest = ProgressEvent.model_validate_json(
            status_path.read_text(encoding="utf-8")
        )
        if events and latest.seq > events[-1].seq:
            # A writer may have completed append+replace between our two reads.
            events = _events(progress_path)
        if not events or latest.seq >= len(events) or events[latest.seq] != latest:
            raise ValueError("run-status.json is not derived from the progress log")
        # Append happens before the atomic latest-file replace. During that
        # small window the complete append-only event is the newer snapshot.
        status = events[-1].model_dump(mode="json")
    elif events:
        raise ValueError("progress log exists without run-status.json")
    else:
        status = {"state": "not-started"}
    status["events"] = [
        event.model_dump(mode="json") for event in events if event.seq > since_seq
    ]
    stop_path = root_path / "run-stop.json"
    if stop_path.exists():
        stop = json.loads(stop_path.read_text(encoding="utf-8"))
        if not isinstance(stop, dict):
            raise ValueError("invalid run stop record")
        status["stop"] = stop
    return status
