"""Append-only event log primitives for :mod:`deepreason.brain`."""

from __future__ import annotations

import json
import os
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator

from deepreason.brain.models import BrainEvent
from deepreason.canonical import canonical_json, sha256_hex

_DERIVED_EVENT_TYPES = frozenset({"Index", "Card"})
_EMPTY_ROOT = sha256_hex(b"deepreason-brain-v1")


def event_root(events: list[BrainEvent] | tuple[BrainEvent, ...]) -> str:
    """Digest all authoritative events in order.

    Card and Index events describe rebuildable projections and therefore do
    not change the source root they are bound to.  Access, pin, and reinforce
    events do change it because they affect deterministic attention.
    """

    root = _EMPTY_ROOT
    for event in events:
        if event.type not in _DERIVED_EVENT_TYPES:
            root = sha256_hex(bytes.fromhex(root) + bytes.fromhex(event.digest))
    return root


def iter_log(path: Path) -> Iterator[BrainEvent]:
    if not path.exists():
        raise FileNotFoundError(path)
    count = 0
    previous: str | None = None
    with path.open("rb") as stream:
        for line_number, line in enumerate(stream, 1):
            if not line.endswith(b"\n"):
                raise ValueError(f"torn brain log line {line_number}")
            try:
                event = BrainEvent.model_validate_json(line)
            except ValueError as exc:
                raise ValueError(f"invalid brain log line {line_number}") from exc
            if event.seq != count:
                raise ValueError(f"non-contiguous brain sequence at line {line_number}")
            if event.prev_digest != previous:
                raise ValueError(f"brain hash-chain break at line {line_number}")
            if count == 0 and event.type != "Init":
                raise ValueError("brain log must begin with Init")
            count += 1
            previous = event.digest
            yield event
    if count == 0:
        raise ValueError("brain log must begin with Init")


def read_log(path: Path) -> list[BrainEvent]:
    return list(iter_log(path))


def append_lines(path: Path, events: list[BrainEvent]) -> None:
    """Durably append complete canonical JSON lines in one locked operation."""

    if not events:
        return
    payload = b"".join(canonical_json(e.model_dump(mode="json")) + b"\n" for e in events)
    with path.open("ab") as stream:
        stream.write(payload)
        stream.flush()
        os.fsync(stream.fileno())


@contextmanager
def brain_lock(path: Path) -> Iterator[None]:
    """Advisory process lock; the brain stays append-only under concurrency."""

    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a+b") as stream:
        try:
            import fcntl

            fcntl.flock(stream.fileno(), fcntl.LOCK_EX)
        except ImportError:  # pragma: no cover - Windows is not a supported runner today
            pass
        try:
            yield
        finally:
            try:
                import fcntl

                fcntl.flock(stream.fileno(), fcntl.LOCK_UN)
            except ImportError:  # pragma: no cover
                pass


def last_json_line(path: Path) -> dict | None:
    """Small diagnostic helper that never treats derived data as authority."""

    if not path.exists() or path.stat().st_size == 0:
        return None
    with path.open("rb") as stream:
        lines = stream.readlines()
    return json.loads(lines[-1])
