"""Rebuildable, bounded progressive-disclosure cards."""

from __future__ import annotations

import json
import os
from pathlib import Path

from deepreason.brain.models import LessonRecord, MemoryCard, TopicCard
from deepreason.brain.store import BrainStore
from deepreason.canonical import canonical_json, sha256_hex

_SUMMARY_CHARS = 600


def records_digest(record_ids: tuple[str, ...]) -> str:
    return sha256_hex(canonical_json(sorted(record_ids)))


def _bounded(text: str) -> str:
    normalized = " ".join(text.split())
    if len(normalized) <= _SUMMARY_CHARS:
        return normalized
    return normalized[: _SUMMARY_CHARS - 1].rstrip() + "…"


def card_for_record(store: BrainStore, record_id: str) -> MemoryCard:
    record = store.get_memory(record_id)
    conditions: tuple[str, ...] = ()
    overturn: tuple[str, ...] = ()
    # Arbitrary source bodies are intentionally not copied onto level-2 cards.
    # A supplied summary is explicit pack-facing material; lessons have a
    # constructive schema whose limits and overturn conditions are safe to show.
    summary = record.title
    if record.form == "lesson":
        try:
            lesson = LessonRecord.model_validate_json(store.get_blob(record.content_ref))
            summary = lesson.claim
            conditions = lesson.conditions
            overturn = lesson.overturn_conditions
        except ValueError:
            summary = record.title
    elif record.summary_ref is not None:
        summary = store.get_blob(record.summary_ref).decode("utf-8", errors="replace")
    related = tuple(sorted({ref.target for ref in record.refs}))
    return MemoryCard(
        record_id=record.id,
        title=_bounded(record.title),
        summary=_bounded(summary),
        facets=tuple(sorted(set(record.facets))),
        entities=tuple(sorted(set(record.entities))),
        conditions=conditions,
        overturn_conditions=overturn,
        related=related,
        content_digest=record.content_ref,
    )


def _atomic_write(path: Path, data: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(f".tmp.{os.getpid()}")
    with tmp.open("wb") as stream:
        stream.write(data)
        stream.flush()
        os.fsync(stream.fileno())
    os.replace(tmp, path)


def _projection_manifest(path: Path) -> dict | None:
    manifest = path / "manifest.json"
    if not manifest.is_file():
        return None
    try:
        return json.loads(manifest.read_text())
    except (OSError, ValueError):
        return None


def _compatible_base(version_root: Path, digest: str) -> str | None:
    if not version_root.is_dir():
        return None
    for child in sorted(version_root.iterdir()):
        data = _projection_manifest(child)
        if data and data.get("records_digest") == digest:
            return str(data.get("base_root") or data.get("root_digest"))
    return None


def build_cards(store: BrainStore, *, force: bool = False) -> Path:
    manifest = store.manifest
    root = manifest.root_digest
    version_root = store.cards_path / manifest.card_version
    target = version_root / root
    if not force and _projection_manifest(target):
        return target

    ids = store.record_ids()
    digest = records_digest(ids)
    base = None if force else _compatible_base(version_root, digest)
    if base is None:
        base = root
        actual = version_root / base
        topics: dict[str, list[str]] = {}
        for record_id in ids:
            card = card_for_record(store, record_id)
            card_path = actual / "records" / record_id[:2] / f"{record_id}.json"
            _atomic_write(card_path, canonical_json(card.model_dump(mode="json")))
            topic_names = card.facets or ("unfiled",)
            for topic in topic_names:
                topics.setdefault(topic, []).append(record_id)
        for topic, members in sorted(topics.items()):
            ordered_members = tuple(sorted(members))
            topic_card = TopicCard(
                topic=topic,
                record_count=len(members),
                record_ids=ordered_members[:64],
                truncated=len(ordered_members) > 64,
            )
            digest_name = sha256_hex(topic.encode())
            _atomic_write(
                actual / "topics" / f"{digest_name}.json",
                canonical_json(topic_card.model_dump(mode="json")),
            )

    projection = {
        "schema": "deepreason-card-projection-v1",
        "root_digest": root,
        "records_digest": digest,
        "base_root": base,
        "record_count": len(ids),
        "card_version": manifest.card_version,
    }
    _atomic_write(target / "manifest.json", canonical_json(projection))
    store.append_event(
        "Card", {"root_digest": root, "records_digest": digest, "base_root": base}
    )
    return target


def card_path(store: BrainStore, root_digest: str, record_id: str) -> Path:
    root = store.cards_path / store.manifest.card_version / root_digest
    projection = _projection_manifest(root)
    if not projection:
        raise KeyError(f"cards not built for brain root {root_digest}")
    base = projection["base_root"]
    return (
        store.cards_path
        / store.manifest.card_version
        / base
        / "records"
        / record_id[:2]
        / f"{record_id}.json"
    )


def load_card(store: BrainStore, root_digest: str, record_id: str) -> MemoryCard:
    path = card_path(store, root_digest, record_id)
    if not path.is_file():
        raise KeyError(f"memory card not found: {record_id}")
    return MemoryCard.model_validate_json(path.read_bytes())
