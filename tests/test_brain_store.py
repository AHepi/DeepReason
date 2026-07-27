from __future__ import annotations

import json
import shutil
from datetime import date, datetime, timezone

import pytest

from deepreason.brain.cards import build_cards
from deepreason.brain.index import build_index
from deepreason.brain.ingest import ingest_file
from deepreason.brain.models import LessonRecord
from deepreason.brain.distill import distill_lesson
from deepreason.brain.store import BrainStore


def _brain(tmp_path) -> BrainStore:
    return BrainStore.init(
        tmp_path / "brain",
        brain_id="00000000-0000-0000-0000-000000000001",
        created_at=datetime(2026, 1, 1, tzinfo=timezone.utc),
    )


def test_brain_store_is_explicit_content_addressed_and_append_only(tmp_path) -> None:
    brain = _brain(tmp_path)
    assert (brain.path / "brain.json").is_file()
    assert (brain.path / "brain.log.jsonl").is_file()
    assert {path.name for path in brain.path.iterdir()} >= {
        "objects",
        "blobs",
        "indexes",
        "cards",
        "locks",
    }

    source = tmp_path / "claim.txt"
    source.write_text("A constructive account of DNA repair.")
    record_id = ingest_file(brain, source, title="DNA repair", created_day=date(2026, 1, 1))
    record = brain.get_memory(record_id)
    assert record.content_ref == brain.put_blob(source.read_bytes())
    assert brain._object_path(record_id).name == f"{record_id}.json"
    assert brain._object_path(record_id).parent.name == record_id[:2]
    before = brain.log_path.read_bytes()

    copy = tmp_path / "same-bytes.txt"
    copy.write_bytes(source.read_bytes())
    assert ingest_file(brain, copy, created_day=date(2026, 2, 1)) == record_id
    assert brain.log_path.read_bytes() == before
    assert "Delete" not in {event.type for event in brain.events}

    object_before = brain._object_path(record_id).read_bytes()
    brain.put_object(record)
    assert brain._object_path(record_id).read_bytes() == object_before


def test_ingestion_rejects_directories_and_never_crawls(tmp_path) -> None:
    brain = _brain(tmp_path)
    nested = tmp_path / "workspace"
    nested.mkdir()
    (nested / "ambient.txt").write_text("must not be discovered")
    with pytest.raises(ValueError, match="explicit file"):
        ingest_file(brain, nested)
    assert brain.record_ids() == ()


def test_cards_and_indexes_are_root_bound_and_rebuildable_from_log(tmp_path) -> None:
    brain = _brain(tmp_path)
    source = tmp_path / "mechanism.txt"
    source.write_text("mechanism body")
    record_id = ingest_file(
        brain,
        source,
        title="repair mechanism",
        facets=("biology",),
        created_day=date(2026, 1, 1),
    )
    root = brain.manifest.root_digest
    card_projection = build_cards(brain)
    index_projection = build_index(brain)
    assert card_projection.name == root
    assert index_projection.name == root
    assert json.loads((card_projection / "manifest.json").read_text())["root_digest"] == root

    shutil.rmtree(brain.cards_path)
    shutil.rmtree(brain.indexes_path)
    brain.cards_path.mkdir()
    brain.indexes_path.mkdir()
    build_index(brain, force=True)
    assert brain.get_memory(record_id).title == "repair mechanism"


def test_constructive_lesson_has_no_verdict_or_evidence_channel(tmp_path) -> None:
    brain = _brain(tmp_path)
    lesson = LessonRecord(
        claim="Probe the boundary before widening the model.",
        conditions=("A small counterexample is available.",),
        procedure=("Generate the boundary case.",),
        checks=("Run the fixed checker.",),
        limits=("Applies only to the declared model.",),
        overturn_conditions=("The boundary is not observable.",),
        source_refs=("run:1/artifact:a",),
    )
    record_id = distill_lesson(brain, lesson, source_ref="run:1", created_day=date(2026, 1, 2))
    record = brain.get_memory(record_id)
    assert record.form == "lesson"
    serialized = record.model_dump(mode="json")
    assert "status" not in serialized
    assert "evidence" not in serialized
    assert distill_lesson(brain, lesson, source_ref="run:1") == record_id
