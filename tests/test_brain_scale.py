from __future__ import annotations

import sqlite3
from datetime import datetime, timezone

from deepreason.brain.index import build_index, candidate_ids, index_database
from deepreason.brain.store import BrainStore


def test_100k_index_query_has_a_bounded_pool(tmp_path) -> None:
    brain = BrainStore.init(
        tmp_path / "brain",
        brain_id="scale-test",
        created_at=datetime(2026, 1, 1, tzinfo=timezone.utc),
    )
    root = brain.manifest.root_digest
    build_index(brain)
    database = index_database(brain, root)
    rows = (("shared", f"{index:064x}") for index in range(100_000))
    with sqlite3.connect(database) as connection:
        connection.executemany("INSERT INTO lexical(token,id) VALUES (?,?)", rows)
        connection.commit()
    lexical, vector = candidate_ids(
        brain, root, "shared", limit=64, posting_limit=64
    )
    assert len(lexical) == 64
    assert vector == {}


def test_existing_index_avoids_record_enumeration(tmp_path, monkeypatch) -> None:
    brain = BrainStore.init(
        tmp_path / "brain",
        brain_id="no-scan-test",
        created_at=datetime(2026, 1, 1, tzinfo=timezone.utc),
    )
    projection = build_index(brain)

    def fail_scan():
        raise AssertionError("record log enumeration is not allowed after index creation")

    monkeypatch.setattr(brain, "record_ids", fail_scan)
    assert build_index(brain) == projection
