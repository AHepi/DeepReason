"""MiniReason compatibility views over DeepReason's canonical persistence.

MiniReason intentionally has no event, object, replay, or status ontology of
its own.  The small engine owns scheduling only; this module preserves its
historical dictionary-shaped read API while every value is projected from a
canonical :class:`deepreason.harness.Harness` materialization.
"""

from pathlib import Path

from deepreason.canonical import canonical_json, sha256_hex
from deepreason.harness import Harness
from deepreason.log.event_log import (
    ConcurrentWriterError,
    CorruptLogError,
    EventLog as ParentEventLog,
    EventSequenceError,
)
from deepreason.ontology.artifact import Artifact, Interface
from deepreason.ontology.event import Event
from deepreason.ontology.event import Event as ParentEvent
from deepreason.ontology.event import LLMCall as Call
from deepreason.ontology.state import Status
from deepreason.storage.blobs import BlobStore as BlobStore
from deepreason.storage.objects import ObjectStore as ParentObjectStore
from deepreason.storage.objects import SCHEMAS as PARENT_SCHEMAS

__all__ = ["BlobStore", "Call", "Event"]

def artifact_id(content_ref: str, codec: str, interface: dict) -> str:
    """Delegate content identity to the canonical Artifact implementation."""
    return Artifact.compute_id(content_ref, codec, Interface.model_validate(interface))


class ObjectStore:
    """Reduced-engine adapter over the parent's immutable object store."""

    SCHEMAS = tuple(PARENT_SCHEMAS)

    def __init__(self, root: Path) -> None:
        self.root = Path(root)
        self._parent = ParentObjectStore(self.root)

    def _path(self, oid: str) -> Path:
        # Compatibility helper used by the Mini chaos battery. New writes are
        # namespaced by the shared store; legacy flat records remain readable.
        digest = f"{sha256_hex(oid.encode())}.json"
        matches = [
            self.root / schema / digest
            for schema in self.SCHEMAS
            if (self.root / schema / digest).exists()
        ]
        return matches[0] if len(matches) == 1 else self.root / digest

    def put(self, schema: str, oid: str, data: dict) -> None:
        if schema not in self.SCHEMAS:
            raise ValueError(f"unknown object schema: {schema}")
        obj = PARENT_SCHEMAS[schema].model_validate(data)
        if obj.id != oid:
            raise ValueError(f"object id mismatch: {oid}")
        self._parent.put(schema, obj)

    def get(self, oid: str) -> tuple[str, dict]:
        schema, obj = self._parent.get(oid)
        return schema, obj.model_dump(mode="json", by_alias=True)


class SeqError(ValueError):
    """An append would break the strictly-consecutive seq stream."""


class EventLog:
    def __init__(self, path: Path) -> None:
        self.path = Path(path)
        self._parent = ParentEventLog(self.path)
        # Prime the shared log's sequence fence and retain Mini's public name.
        try:
            self.next_seq = sum(1 for _ in self._parent.read())
        except (CorruptLogError, EventSequenceError) as error:
            raise SeqError(str(error)) from error

    def _delegate(self) -> ParentEventLog:
        # The chaos battery constructs an uninitialized reader over a
        # deliberately corrupt file. Preserve that diagnostic technique.
        if not hasattr(self, "_parent"):
            self._parent = ParentEventLog(self.path)
        return self._parent

    def append(self, event: Event) -> None:
        if event.seq != self.next_seq:
            raise SeqError(f"seq {event.seq} != expected {self.next_seq}")
        parent_event = ParentEvent.model_validate(
            event.model_dump(mode="json", exclude_none=True)
        )
        try:
            self._delegate().append(parent_event)
        except (ConcurrentWriterError, CorruptLogError, EventSequenceError) as error:
            raise SeqError(str(error)) from error
        self.next_seq += 1

    def read(self):
        """Delegate parsing, torn-tail handling, and seq checks upstream."""
        parent = self._delegate()
        try:
            yield from parent.read()
        except (CorruptLogError, EventSequenceError) as error:
            raise SeqError(str(error)) from error
        finally:
            if parent._next_seq is not None:
                self.next_seq = int(parent._next_seq)


class State:
    """Read-only Mini API projected from one canonical Harness state.

    ``dict`` payloads remain available for old Mini scripts, but attacks,
    support, labels, carriage, and replay are never recomputed here.
    """

    def __init__(self, harness: Harness) -> None:
        self._harness = harness

    @staticmethod
    def _records(values) -> dict[str, dict]:
        return {
            oid: value.model_dump(mode="json", by_alias=True)
            for oid, value in values.items()
        }

    @property
    def artifacts(self) -> dict[str, dict]:
        return self._records(self._harness.state.artifacts)

    @property
    def problems(self) -> dict[str, dict]:
        return self._records(self._harness.state.problems)

    @property
    def commitments(self) -> dict[str, dict]:
        return self._records(self._harness.commitments)

    @property
    def warrants(self) -> dict[str, dict]:
        return self._records(self._harness.warrants)

    @property
    def addr(self) -> list[tuple[str, str]]:
        return list(self._harness.state.addr)

    @property
    def events(self) -> list[Event]:
        return list(self._harness.log.read())

    @property
    def statuses(self) -> dict[str, Status]:
        """The canonical grounded/support labels, with no Mini relabelling."""
        return dict(self._harness.state.status)

    @property
    def refuted(self) -> set[str]:
        """Artifacts labelled REFUTED by the canonical adjudicator."""
        return {
            aid
            for aid, status in self._harness.state.status.items()
            if status == Status.REFUTED
        }

    @property
    def accepted(self) -> set[str]:
        return {
            aid
            for aid, status in self._harness.state.status.items()
            if status == Status.ACCEPTED
        }

    def canonical_status(self, aid: str) -> Status:
        return self._harness.state.status[aid]

    def status(self, aid: str) -> str:
        """Historical Mini spelling backed directly by the canonical label.

        ``refuted-by-check`` is retained for callers that used the v0 API;
        non-refuted labels are returned verbatim so suspension is never
        misrepresented as a live survivor.
        """
        status = self.canonical_status(aid)
        return "refuted-by-check" if status == Status.REFUTED else status.value

    def logged_tokens(self) -> int:
        return sum(e.llm.tokens for e in self.events if e.llm is not None)

    def digest(self) -> str:
        """Canonical fingerprint for the byte-replay invariant (G2)."""
        return sha256_hex(canonical_json({
            "artifacts": sorted(self.artifacts),
            "problems": sorted(self.problems),
            "commitments": sorted(self.commitments),
            "warrants": sorted(self.warrants),
            "addr": sorted(self.addr),
            "carries": sorted(self._harness.state.carries),
            "att": sorted(self._harness.state.att),
            "dep": sorted(self._harness.state.dep),
            "status": {
                aid: status.value
                for aid, status in sorted(self._harness.state.status.items())
            },
            "events": len(self.events),
            "logged_tokens": self.logged_tokens(),
        }))


def replay(root: Path) -> State:
    """Replay through the parent Harness, translating only Mini diagnostics."""
    try:
        return State(Harness(Path(root)))
    except (CorruptLogError, EventSequenceError) as error:
        raise SeqError(str(error)) from error
