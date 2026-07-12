"""Append-only, run-neutral operational progress."""

from __future__ import annotations

import json
import os
import tempfile
import threading
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class ProgressEvent(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    seq: int = Field(ge=0)
    run_id: str = Field(min_length=1)
    state: Literal["starting", "running", "paused", "completed", "failed", "cancelled"]
    workload: Literal["text", "code", "formal", "website"]
    phase: str
    activity: str
    cycle: int = Field(default=0, ge=0)
    problem_id: str | None = None
    artifact_id: str | None = None
    frontier_size: int = Field(default=0, ge=0)
    accepted: int = Field(default=0, ge=0)
    refuted: int = Field(default=0, ge=0)
    suspended: int = Field(default=0, ge=0)
    queued_checks: int = Field(default=0, ge=0)
    queued_criticism: int = Field(default=0, ge=0)
    token_spend: int = Field(default=0, ge=0)
    token_limit: int | None = Field(default=None, gt=0)
    determinate: bool = False
    completed_units: int | None = Field(default=None, ge=0)
    total_units: int | None = Field(default=None, gt=0)
    message: str = Field(default="", max_length=500)
    stop_reason: str | None = None


def _atomic_json(path: Path, value: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary_name = tempfile.mkstemp(
        dir=path.parent, prefix=f".{path.name}.", suffix=".tmp"
    )
    temporary = Path(temporary_name)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as stream:
            json.dump(value, stream, sort_keys=True, separators=(",", ":"))
            stream.write("\n")
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
    finally:
        if temporary.exists():
            temporary.unlink()


class ProgressSink:
    def __init__(self, root: Path | str, *, run_id: str, workload: str) -> None:
        self.root = Path(root)
        self.root.mkdir(parents=True, exist_ok=True)
        self.run_id = run_id
        self.workload = workload
        self.log_path = self.root / "progress.jsonl"
        self.status_path = self.root / "run-status.json"
        self._lock = threading.Lock()
        existing = self.read_since(-1)
        self._next_seq = existing[-1].seq + 1 if existing else 0

    def emit(self, **values) -> ProgressEvent:
        with self._lock:
            event = ProgressEvent(
                seq=self._next_seq,
                run_id=self.run_id,
                workload=self.workload,
                **values,
            )
            payload = event.model_dump_json() + "\n"
            with self.log_path.open("a", encoding="utf-8") as stream:
                stream.write(payload)
                stream.flush()
                os.fsync(stream.fileno())
            _atomic_json(self.status_path, event.model_dump(mode="json"))
            self._next_seq += 1
            return event

    def read_since(self, seq: int = -1) -> list[ProgressEvent]:
        if not self.log_path.exists():
            return []
        events: list[ProgressEvent] = []
        for line in self.log_path.read_text(encoding="utf-8").splitlines():
            event = ProgressEvent.model_validate_json(line)
            if event.seq > seq:
                events.append(event)
        for expected, event in enumerate(events, start=events[0].seq if events else 0):
            if event.seq != expected:
                raise ValueError("progress sequence is not contiguous")
        return events

    @property
    def cancel_path(self) -> Path:
        return self.root / "cancel.requested"

    def request_cancel(self) -> None:
        self.cancel_path.write_text(self.run_id + "\n", encoding="utf-8")

    def cancellation_requested(self) -> bool:
        return self.cancel_path.exists()

    def clear_cancellation(self) -> None:
        if self.cancel_path.exists():
            self.cancel_path.unlink()
