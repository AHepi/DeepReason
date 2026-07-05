"""Append-only JSONL event log (spec §1).

Source of truth; graph state is a materialized view. Nothing is deleted
(D8). Materialization/replay lives in ``deepreason.harness`` — the log
itself only appends and reads. Replay consumes logged LLM raws (§0), so
verdicts are replay-deterministic.
"""

import os
import warnings
from collections.abc import Iterator
from pathlib import Path

from pydantic import ValidationError

from deepreason.ontology.event import Event


class CorruptLogError(Exception):
    """A non-final log line failed to parse: the log is genuinely damaged."""


class EventLog:
    def __init__(self, path: Path) -> None:
        self.path = Path(path)

    def append(self, event: Event) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.path, "a", encoding="utf-8") as f:
            f.write(event.model_dump_json(by_alias=True) + "\n")
            f.flush()
            os.fsync(f.fileno())

    def read(self, upto_seq: int | None = None) -> Iterator[Event]:
        """Iterate events in order, optionally truncated for time-travel.

        A final line that fails to parse is a torn write from a crash
        mid-append: the event was never acknowledged durable, so it is
        skipped (with a warning) rather than rendering the session
        unopenable. A bad line anywhere else is real corruption and raises.
        """
        if not self.path.exists():
            return
        pending: tuple[int, str] | None = None  # one-line lookahead
        with open(self.path, encoding="utf-8") as f:
            for lineno, line in enumerate(f, start=1):
                line = line.strip()
                if not line:
                    continue
                if pending is not None:
                    try:
                        event = Event.model_validate_json(pending[1])
                    except ValidationError as e:
                        raise CorruptLogError(
                            f"{self.path}: bad line {pending[0]}: {e}"
                        ) from e
                    if upto_seq is not None and event.seq > upto_seq:
                        return
                    yield event
                pending = (lineno, line)
        if pending is not None:
            try:
                event = Event.model_validate_json(pending[1])
            except ValidationError as e:
                warnings.warn(
                    f"{self.path}: dropping torn final line {pending[0]} "
                    f"(crash mid-append): {e}",
                    stacklevel=2,
                )
                return
            if upto_seq is not None and event.seq > upto_seq:
                return
            yield event
