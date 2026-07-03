"""Append-only JSONL event log (spec §1).

Source of truth; graph state is a materialized view. Nothing is deleted (D8).
Replay from the log must reproduce state byte-for-byte (P0 acceptance test) —
replay consumes logged LLM raws, so verdicts are replay-deterministic (§0).
"""

from collections.abc import Iterator
from pathlib import Path

from deepreason.ontology.event import Event


class EventLog:
    def __init__(self, path: Path) -> None:
        self.path = path

    def append(self, event: Event) -> None:
        """Append one event; seq must be the next integer. TODO(P0)."""
        raise NotImplementedError

    def read(self, upto_seq: int | None = None) -> Iterator[Event]:
        """Iterate events, optionally truncated for time-travel. TODO(P0)."""
        raise NotImplementedError

    def replay(self, upto_seq: int | None = None):
        """Materialize EpistemicState from the log (time-travel). TODO(P0)."""
        raise NotImplementedError
