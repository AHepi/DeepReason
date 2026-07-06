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


class ConcurrentWriterError(RuntimeError):
    """The log grew outside this writer: two live sessions on one root."""


class EventLog:
    def __init__(self, path: Path) -> None:
        self.path = Path(path)
        self._repair_torn_tail()
        self._size = self.path.stat().st_size if self.path.exists() else 0

    def _repair_torn_tail(self) -> None:
        """Truncate a torn FINAL line at open (crash mid-append). Without
        this, the next append writes onto the unterminated fragment and the
        merged line is later dropped as torn — a real, fsynced event lost
        AFTER a clean recovery (found by the MiniReason chaos battery; the
        same append path lives here). Only bytes never acknowledged durable
        are removed: append returns only after line + newline are written
        and fsynced. A bad line with valid lines after it is corruption and
        is left for read() to raise on."""
        if not self.path.exists():
            return
        data = self.path.read_bytes()
        if not data:
            return
        offset, valid_end = 0, 0
        torn_at: int | None = None
        while offset < len(data):
            nl = data.find(b"\n", offset)
            end = (nl + 1) if nl != -1 else len(data)
            line = data[offset:end].strip()
            ok = not line
            if line:
                try:
                    Event.model_validate_json(line)
                    ok = nl != -1  # a parseable line is still torn without its newline
                except ValidationError:
                    ok = False
            if ok:
                valid_end = end
                torn_at = None
            elif torn_at is None:
                torn_at = offset
            else:
                return  # bad line followed by more lines: corruption, read() raises
            offset = end
        if torn_at is not None:
            warnings.warn(
                f"{self.path}: truncating torn final line (crash mid-append), "
                f"{len(data) - valid_end} bytes discarded",
                stacklevel=3,
            )
            with open(self.path, "r+b") as f:
                f.truncate(valid_end)
                f.flush()
                os.fsync(f.fileno())

    def append(self, event: Event) -> None:
        # Single-writer fence: a second live Harness on this root would
        # append a duplicate seq — silent corruption surfacing only at the
        # next replay (found by the MiniReason chaos battery). Fail here.
        actual = self.path.stat().st_size if self.path.exists() else 0
        if actual != self._size:
            raise ConcurrentWriterError(
                f"{self.path}: log advanced under us "
                f"({actual} != {self._size} bytes): concurrent writer")
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.path, "a", encoding="utf-8") as f:
            f.write(event.model_dump_json(by_alias=True) + "\n")
            f.flush()
            os.fsync(f.fileno())
            self._size = f.tell()

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
