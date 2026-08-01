"""Explicit, idempotent brain ingestion.

Callers supply every input path.  Directories and implicit workspace scans are
rejected so attaching a brain can never become ambient filesystem authority.
"""

from __future__ import annotations

import mimetypes
from datetime import date
from pathlib import Path
from typing import Iterable

from deepreason.brain.models import ActivationSpec, MemoryProvenance, MemoryRecord, utc_day
from deepreason.brain.store import BrainStore
from deepreason.canonical import sha256_hex

IMPORTER_VERSION = "explicit-file-v1"


def ingest_file(
    store: BrainStore,
    path: str | Path,
    *,
    form: str = "source",
    codec: str | None = None,
    title: str | None = None,
    facets: Iterable[str] = (),
    entities: Iterable[str] = (),
    created_day: date | None = None,
    activation: ActivationSpec | None = None,
    importer_version: str = IMPORTER_VERSION,
) -> str:
    source = Path(path)
    if not source.exists():
        raise FileNotFoundError(source)
    if not source.is_file():
        raise ValueError(f"brain ingestion requires an explicit file, not a directory: {source}")
    body = source.read_bytes()
    source_digest = sha256_hex(body)
    existing = store.find_ingest(source_digest, importer_version)
    if existing is not None:
        return existing

    content_ref = store.put_blob(body)
    inferred_codec = codec or mimetypes.guess_type(source.name)[0] or "application/octet-stream"
    day = created_day or utc_day()
    record = MemoryRecord.create(
        form=form,
        title=title or source.name,
        content_ref=content_ref,
        codec=inferred_codec,
        summary_ref=None,
        facets=tuple(sorted(set(facets))),
        entities=tuple(sorted(set(entities))),
        refs=(),
        provenance=MemoryProvenance(
            origin="file",
            source_ref=str(source),
            source_digest=source_digest,
            created_seq=store.manifest.head_seq + 1,
            created_day=day,
        ),
        activation=activation or ActivationSpec(),
    )
    return store.add_memory(
        record,
        event_payload={
            "source_digest": source_digest,
            "importer_version": importer_version,
            "source_ref": str(source),
        },
        event_day=day,
    )


def ingest_files(store: BrainStore, paths: Iterable[str | Path], **kwargs: object) -> tuple[str, ...]:
    """Ingest only the explicitly enumerated files, preserving caller order."""

    supplied = tuple(paths)
    if not supplied:
        raise ValueError("at least one explicit input path is required")
    return tuple(ingest_file(store, path, **kwargs) for path in supplied)
