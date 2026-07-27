"""Constructive lesson storage without source verdict transfer."""

from __future__ import annotations

from datetime import date

from deepreason.brain.models import (
    ActivationSpec,
    LessonRecord,
    MemoryProvenance,
    MemoryRecord,
    utc_day,
)
from deepreason.brain.store import BrainStore
from deepreason.canonical import canonical_json, sha256_hex

DISTILLER_VERSION = "constructive-lesson-v1"


def distill_lesson(
    store: BrainStore,
    lesson: LessonRecord,
    *,
    source_ref: str,
    created_day: date | None = None,
    facets: tuple[str, ...] = (),
    entities: tuple[str, ...] = (),
    distiller_version: str = DISTILLER_VERSION,
) -> str:
    """Store an already-structured positive lesson as advisory memory.

    This API accepts no verdict, warrant, status, evidence credit, failed-rival
    body, or criticism transcript.  Source refs remain provenance strings.
    """

    if not lesson.procedure and not lesson.checks:
        raise ValueError("a constructive lesson needs a procedure or check")
    body = canonical_json(lesson.model_dump(mode="json"))
    source_digest = sha256_hex(body)
    for event in store.iter_events():
        if (
            event.type == "Distill"
            and event.payload.get("source_digest") == source_digest
            and event.payload.get("distiller_version") == distiller_version
        ):
            existing = event.payload.get("record_id")
            if isinstance(existing, str):
                return existing

    day = created_day or utc_day()
    content_ref = store.put_blob(body)
    summary_ref = store.put_blob(lesson.claim.encode("utf-8"))
    record = MemoryRecord.create(
        form="lesson",
        title=lesson.claim[:500],
        content_ref=content_ref,
        codec="application/vnd.deepreason.lesson+json",
        summary_ref=summary_ref,
        facets=tuple(sorted(set(facets))),
        entities=tuple(sorted(set(entities))),
        refs=(),
        provenance=MemoryProvenance(
            origin="run",
            source_ref=source_ref,
            source_digest=source_digest,
            created_seq=store.manifest.head_seq + 1,
            created_day=day,
        ),
        activation=ActivationSpec(),
    )
    return store.add_memory(
        record,
        event_type="Distill",
        event_payload={
            "source_digest": source_digest,
            "distiller_version": distiller_version,
            "source_refs": list(lesson.source_refs),
        },
        event_day=day,
    )
