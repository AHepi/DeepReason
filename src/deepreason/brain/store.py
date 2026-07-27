"""Explicit-path, append-only and content-addressed brain storage."""

from __future__ import annotations

import os
import uuid
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any, Iterable

from deepreason.brain.log import append_lines, brain_lock, event_root, iter_log, read_log
from deepreason.brain.models import (
    BrainEvent,
    BrainEventType,
    BrainManifest,
    MemoryRecord,
    utc_day,
)
from deepreason.canonical import canonical_json
from deepreason.storage.blobs import BlobStore


class BrainStore:
    """A local brain whose root must always be supplied by its caller.

    Merely importing this class performs no filesystem discovery.  Opening a
    brain validates its manifest, hash chain, and content-addressed objects.
    """

    def __init__(self, path: str | Path) -> None:
        if path is None:  # type: ignore[comparison-overlap]
            raise TypeError("brain path must be explicit")
        self.path = Path(path)
        self.manifest_path = self.path / "brain.json"
        self.log_path = self.path / "brain.log.jsonl"
        if not self.manifest_path.is_file() or not self.log_path.is_file():
            raise FileNotFoundError(f"not an initialized brain: {self.path}")
        self.objects_path = self.path / "objects"
        self.blobs = BlobStore(self.path / "blobs")
        self.indexes_path = self.path / "indexes"
        self.cards_path = self.path / "cards"
        self.locks_path = self.path / "locks"
        self._validate()

    @classmethod
    def init(
        cls,
        path: str | Path,
        *,
        brain_id: str | None = None,
        created_at: datetime | None = None,
        card_version: str = "v1",
        index_version: str = "hybrid-v1",
    ) -> BrainStore:
        if path is None:  # type: ignore[comparison-overlap]
            raise TypeError("brain path must be explicit")
        root = Path(path)
        if root.exists() and any(root.iterdir()):
            raise FileExistsError(f"brain directory is not empty: {root}")
        root.mkdir(parents=True, exist_ok=True)
        for directory in ("objects", "blobs", "indexes", "cards", "locks"):
            (root / directory).mkdir(parents=True, exist_ok=True)

        created = created_at or datetime.now(timezone.utc)
        if created.tzinfo is None:
            created = created.replace(tzinfo=timezone.utc)
        identifier = brain_id or str(uuid.uuid4())
        event = BrainEvent.create(
            seq=0,
            type="Init",
            day=created.astimezone(timezone.utc).date(),
            payload={"brain_id": identifier},
            prev_digest=None,
            logical_seq=0,
        )
        append_lines(root / "brain.log.jsonl", [event])
        manifest = BrainManifest(
            brain_id=identifier,
            head_seq=0,
            root_digest=event_root([event]),
            card_version=card_version,
            index_version=index_version,
            created_at=created,
        )
        cls._write_manifest(root / "brain.json", manifest)
        return cls(root)

    @property
    def manifest(self) -> BrainManifest:
        return BrainManifest.model_validate_json(self.manifest_path.read_bytes())

    @property
    def events(self) -> tuple[BrainEvent, ...]:
        return tuple(read_log(self.log_path))

    def iter_events(self) -> Iterable[BrainEvent]:
        return iter_log(self.log_path)

    @staticmethod
    def _write_manifest(path: Path, manifest: BrainManifest) -> None:
        payload = canonical_json(manifest.model_dump(mode="json"))
        tmp = path.with_name(f"{path.name}.tmp.{os.getpid()}")
        with tmp.open("wb") as stream:
            stream.write(payload)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(tmp, path)

    def _validate(self) -> None:
        manifest = self.manifest
        events = read_log(self.log_path)
        if manifest.head_seq != events[-1].seq:
            raise ValueError("brain manifest/log head mismatch")
        if manifest.root_digest != event_root(events):
            raise ValueError("brain manifest/log root mismatch")
        if events[0].payload.get("brain_id") != manifest.brain_id:
            raise ValueError("brain id mismatch")

    def append_event(
        self,
        event_type: BrainEventType,
        payload: dict[str, Any] | None = None,
        *,
        event_day: date | None = None,
        logical_seq: int | None = None,
    ) -> BrainEvent:
        with brain_lock(self.locks_path / "brain.lock"):
            events = read_log(self.log_path)
            manifest = self.manifest
            if manifest.head_seq != events[-1].seq or manifest.root_digest != event_root(events):
                raise ValueError("brain changed inconsistently while locked")
            event = BrainEvent.create(
                seq=events[-1].seq + 1,
                type=event_type,
                day=event_day or utc_day(),
                payload=payload,
                prev_digest=events[-1].digest,
                logical_seq=logical_seq,
            )
            append_lines(self.log_path, [event])
            updated_events = [*events, event]
            updated = manifest.model_copy(
                update={"head_seq": event.seq, "root_digest": event_root(updated_events)}
            )
            self._write_manifest(self.manifest_path, updated)
            if event_type in {"Access", "Reinforce", "Pin", "Unpin"}:
                self._alias_derived(manifest.root_digest, updated.root_digest, event)
            return event

    def _alias_derived(
        self, previous_root: str, current_root: str, event: BrainEvent
    ) -> None:
        """Bind unchanged text projections to an activation-only new root."""

        if previous_root == current_root:
            return
        for version_root in (
            self.cards_path / self.manifest.card_version,
            self.indexes_path / self.manifest.index_version,
        ):
            source = version_root / previous_root / "manifest.json"
            target = version_root / current_root / "manifest.json"
            if not source.is_file() or target.exists():
                continue
            import json

            projection = json.loads(source.read_text())
            projection["root_digest"] = current_root
            if projection.get("schema") == "deepreason-hybrid-index-v1":
                projection["activation_parent_root"] = previous_root
                projection["activation_event"] = {
                    "seq": event.seq,
                    "type": event.type,
                    "day": event.day.isoformat(),
                    "logical_seq": event.logical_seq,
                    "payload": event.payload,
                }
            target.parent.mkdir(parents=True, exist_ok=True)
            tmp = target.with_suffix(f".tmp.{os.getpid()}")
            tmp.write_bytes(canonical_json(projection))
            os.replace(tmp, target)

    def _object_path(self, record_id: str) -> Path:
        return self.objects_path / record_id[:2] / f"{record_id}.json"

    def put_object(self, record: MemoryRecord) -> None:
        target = self._object_path(record.id)
        payload = canonical_json(record.model_dump(mode="json"))
        if target.exists():
            if target.read_bytes() != payload:
                raise ValueError(f"immutable memory conflict: {record.id}")
            return
        target.parent.mkdir(parents=True, exist_ok=True)
        tmp = target.with_suffix(f".tmp.{os.getpid()}")
        with tmp.open("wb") as stream:
            stream.write(payload)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(tmp, target)

    def get_memory(self, record_id: str) -> MemoryRecord:
        target = self._object_path(record_id)
        if not target.is_file():
            raise KeyError(f"memory not found: {record_id}")
        record = MemoryRecord.model_validate_json(target.read_bytes())
        if record.id != record_id:
            raise ValueError(f"memory object/path mismatch: {record_id}")
        return record

    def record_ids(self) -> tuple[str, ...]:
        """Enumerate authoritative records from the log, never directory crawl."""

        seen: set[str] = set()
        ordered: list[str] = []
        for event in self.events:
            if event.type not in {"Ingest", "Distill"}:
                continue
            record_id = event.payload.get("record_id")
            if isinstance(record_id, str) and record_id not in seen:
                seen.add(record_id)
                ordered.append(record_id)
        return tuple(ordered)

    def find_ingest(self, source_digest: str, importer_version: str) -> str | None:
        for event in self.events:
            if event.type != "Ingest":
                continue
            if (
                event.payload.get("source_digest") == source_digest
                and event.payload.get("importer_version") == importer_version
            ):
                record_id = event.payload.get("record_id")
                if isinstance(record_id, str):
                    return record_id
        return None

    def add_memory(
        self,
        record: MemoryRecord,
        *,
        event_type: BrainEventType = "Ingest",
        event_payload: dict[str, Any] | None = None,
        event_day: date | None = None,
    ) -> str:
        if event_type not in {"Ingest", "Distill"}:
            raise ValueError("memory records may enter through Ingest or Distill only")
        self.put_object(record)
        if record.id in self.record_ids():
            return record.id
        payload = {"record_id": record.id, **(event_payload or {})}
        self.append_event(event_type, payload, event_day=event_day)
        return record.id

    def link(self, source: str, target: str, role: str = "related") -> BrainEvent:
        self.get_memory(source)
        self.get_memory(target)
        if role not in {"related", "derived", "supersedes", "source"}:
            raise ValueError(f"invalid memory link role: {role}")
        return self.append_event("Link", {"source": source, "target": target, "role": role})

    def reinforce(
        self,
        record_id: str,
        *,
        reason: str = "explicit_user",
        event_day: date | None = None,
        logical_seq: int | None = None,
    ) -> BrainEvent:
        self.get_memory(record_id)
        if reason not in {"explicit_user", "candidate_citation"}:
            raise ValueError("reinforcement reason is not allowed; acceptance never reinforces")
        return self.append_event(
            "Reinforce",
            {"record_id": record_id, "reason": reason},
            event_day=event_day,
            logical_seq=logical_seq,
        )

    def record_access(
        self,
        record_ids: Iterable[str],
        *,
        event_day: date,
        logical_seq: int | None = None,
    ) -> BrainEvent | None:
        ids = tuple(dict.fromkeys(record_ids))
        if not ids:
            return None
        for record_id in ids:
            self.get_memory(record_id)
        return self.append_event(
            "Access",
            {"record_ids": list(ids), "reason": "pack_exposure"},
            event_day=event_day,
            logical_seq=logical_seq,
        )

    def pin(
        self, record_id: str, *, floor: float = 1.0, event_day: date | None = None
    ) -> BrainEvent:
        self.get_memory(record_id)
        if floor < 0:
            raise ValueError("pin floor must be non-negative")
        return self.append_event(
            "Pin", {"record_id": record_id, "floor": floor}, event_day=event_day
        )

    def unpin(self, record_id: str, *, event_day: date | None = None) -> BrainEvent:
        self.get_memory(record_id)
        return self.append_event("Unpin", {"record_id": record_id}, event_day=event_day)

    def supersede(
        self, record_id: str, replacement_id: str, *, event_day: date | None = None
    ) -> BrainEvent:
        self.get_memory(record_id)
        self.get_memory(replacement_id)
        return self.append_event(
            "Supersede",
            {"record_id": record_id, "replacement_id": replacement_id},
            event_day=event_day,
        )

    def put_blob(self, body: bytes) -> str:
        return self.blobs.put(body)

    def get_blob(self, digest: str) -> bytes:
        return self.blobs.get(digest)
