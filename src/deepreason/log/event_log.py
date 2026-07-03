"""Append-only JSONL event log (spec §1).

Source of truth; graph state is a materialized view. Nothing is deleted
(D8). Materialization/replay lives in ``deepreason.harness`` — the log
itself only appends and reads. Replay consumes logged LLM raws (§0), so
verdicts are replay-deterministic.
"""

from collections.abc import Iterator
from pathlib import Path

from deepreason.ontology.event import Event


class EventLog:
    def __init__(self, path: Path) -> None:
        self.path = Path(path)

    def append(self, event: Event) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.path, "a", encoding="utf-8") as f:
            f.write(event.model_dump_json(by_alias=True) + "\n")

    def read(self, upto_seq: int | None = None) -> Iterator[Event]:
        """Iterate events in order, optionally truncated for time-travel."""
        if not self.path.exists():
            return
        with open(self.path, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                event = Event.model_validate_json(line)
                if upto_seq is not None and event.seq > upto_seq:
                    return
                yield event
