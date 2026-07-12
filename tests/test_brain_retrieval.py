from __future__ import annotations

import shutil
from datetime import date, datetime, timezone

from deepreason.brain.ingest import ingest_file
from deepreason.brain.models import ActivationSpec, MemoryPolicy
from deepreason.brain.retrieve import retrieve
from deepreason.brain.snapshot import replay_snapshot, snapshot_retrieval
from deepreason.brain.store import BrainStore
from deepreason.storage.blobs import BlobStore


def _populated_brain(tmp_path) -> BrainStore:
    brain = BrainStore.init(
        tmp_path / "brain",
        brain_id="retrieval-test",
        created_at=datetime(2026, 1, 1, tzinfo=timezone.utc),
    )
    for index, title in enumerate(
        (
            "DNA repair mechanism",
            "DNA mutation boundary",
            "protein folding simulation",
            "genetic repair experiment",
            "old DNA analogy",
        )
    ):
        source = tmp_path / f"source-{index}.txt"
        source.write_text(f"body {title}")
        ingest_file(
            brain,
            source,
            title=title,
            facets=("biology" if index < 4 else "analogy",),
            created_day=date(2020 if index == 4 else 2026, 1, 1),
            activation=ActivationSpec(half_life_days=30.0),
        )
    return brain


def test_retrieval_is_bounded_stable_and_has_deterministic_exploration(tmp_path) -> None:
    brain = _populated_brain(tmp_path)
    policy = MemoryPolicy(
        candidate_pool_limit=4,
        selected_limit=3,
        expanded_limit=2,
        exploration_ppm=333_334,
        collection_quota=3,
    )
    first = retrieve(
        brain,
        "DNA repair",
        query_day=date(2026, 6, 1),
        policy=policy,
        record_access=False,
    )
    second = retrieve(
        brain,
        "DNA repair",
        query_day=date(2026, 6, 1),
        policy=policy,
        record_access=False,
    )
    assert first.receipt == second.receipt
    assert len(first.receipt.candidate_pool) <= 4
    assert len(first.receipt.selected) <= 3
    assert len(first.receipt.expanded) <= 2
    assert first.receipt.query == "dna repair"
    assert all("confidence" not in score.model_dump() for score in first.receipt.candidate_pool)


def test_access_changes_attention_root_but_reuses_root_bound_index(tmp_path) -> None:
    brain = _populated_brain(tmp_path)
    before = brain.manifest.root_digest
    retrieve(brain, "DNA", query_day=date(2026, 1, 2), record_access=True)
    after = brain.manifest.root_digest
    assert after != before
    assert (brain.indexes_path / brain.manifest.index_version / after / "manifest.json").is_file()
    retrieve(brain, "DNA", query_day=date(2026, 1, 2), record_access=False)


def test_query_after_index_creation_does_not_enumerate_brain_log(tmp_path, monkeypatch) -> None:
    brain = _populated_brain(tmp_path)
    retrieve(brain, "DNA repair", query_day=date(2026, 1, 2), record_access=False)

    def fail_scan():
        raise AssertionError("retrieval must use the root-bound derived indexes")

    monkeypatch.setattr(brain, "iter_events", fail_scan)
    replay = retrieve(brain, "DNA repair", query_day=date(2026, 1, 2), record_access=False)
    assert replay.receipt.selected


def test_receipt_snapshot_replays_after_external_brain_is_gone(tmp_path) -> None:
    brain = _populated_brain(tmp_path)
    result = retrieve(
        brain,
        "DNA repair",
        query_day=date(2026, 2, 1),
        record_access=False,
    )
    run_blobs = BlobStore(tmp_path / "run-blobs")
    snapshot = snapshot_retrieval(brain, result, run_blobs)
    shutil.rmtree(brain.path)
    replayed = replay_snapshot(snapshot, run_blobs)
    assert replayed == result
    assert replayed.receipt == result.receipt
    assert replayed.cards == result.cards
    assert replayed.bodies == result.bodies
    receipt_data = replayed.receipt.model_dump(mode="json")
    assert "evidence" not in receipt_data
    assert "status" not in receipt_data
    assert "grounding" not in receipt_data
