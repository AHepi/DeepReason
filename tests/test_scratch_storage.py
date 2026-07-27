"""C1 persistence coverage for immutable scratch canonical records."""

import json
import os

import pytest

from deepreason.canonical import canonical_json, sha256_hex
from deepreason.ontology import Commitment
from deepreason.scratch.models import (
    AdvisoryContextV1,
    AttentionReceiptV1,
    ClusterGuideV1,
    ClusterMembershipV1,
    ClusterSnapshotV1,
    CoverageCycleV1,
    InstanceRef,
    LLMCallRef,
    ScratchBlockBodyV1,
    ScratchBlockV1,
    ScratchClusterV1,
    ScratchLinkBodyV1,
    ScratchLinkV1,
    ScratchProvenanceV1,
    SimilarityHitV1,
    VisibilityRecordV1,
)
from deepreason.storage.objects import (
    SCHEMAS,
    ObjectConflictError,
    ObjectStore,
    ReadOnlyObjectStoreError,
)


def _hash(label: str) -> str:
    return f"sha256:{sha256_hex(label.encode('utf-8'))}"


def _instance(seq: int) -> InstanceRef:
    return InstanceRef(run_id=_hash("run"), seq=seq)


def _scratch_records() -> dict[str, tuple[str, object]]:
    provenance = ScratchProvenanceV1(actor="user", origin="seed")
    first = ScratchBlockV1.create(
        body=ScratchBlockBodyV1(content="An unfinished possibility."),
        instance=_instance(1),
        provenance=provenance,
    )
    second = ScratchBlockV1.create(
        body=ScratchBlockBodyV1(content="A separate observation."),
        instance=_instance(2),
        provenance=provenance,
    )
    link = ScratchLinkV1.create(
        body=ScratchLinkBodyV1.model_validate(
            {
                "from": first.id,
                "to": second.id,
                "relation_hint": "may be relevant to",
            }
        ),
        instance=_instance(3),
    )
    cluster = ScratchClusterV1.create(
        seed_focus="Possible convergence causes", instance=_instance(4)
    )
    membership = ClusterMembershipV1.create(
        cluster_id=cluster.id,
        block_id=first.id,
        action="add",
        reason="A provisional navigation route",
        instance=_instance(5),
    )
    snapshot = ClusterSnapshotV1.create(
        cluster_id=cluster.id,
        member_ids=[first.id, second.id],
        live_link_ids=[link.id],
    )
    call = LLMCallRef(
        event_seq=6,
        model="scripted-model",
        endpoint="fixture://scratch",
        prompt_ref=_hash("prompt"),
        raw_ref=_hash("raw"),
    )
    guide = ClusterGuideV1.create(
        cluster_id=cluster.id,
        based_on_snapshot=snapshot.snapshot_hash,
        working_focus="Compare the two unfinished thoughts.",
        open_threads=["The relation remains provisional."],
        entry_points=[first.id],
        local_summary=None,
        authored_by=call,
        instance=_instance(6),
    )
    similarity = SimilarityHitV1.create(
        block_a=first.id,
        block_b=second.id,
        embedder="deterministic-hash",
        embedder_version="1",
        score=0.25,
        threshold_used=0.8,
        input_body_hash_a=first.body_hash,
        input_body_hash_b=second.body_hash,
        instance=_instance(7),
    )
    attention = AttentionReceiptV1.create(
        state_seq=7,
        request_hash=_hash("request"),
        selected_by_channel={"focus": [first.id], "exploratory": [second.id]},
        final_order=[first.id, second.id],
        excluded_by_global_limit=[],
        excluded_by_channel={},
        deterministic_seed=17,
        coverage_cycle_id=None,
        instance=_instance(7),
    )
    visibility = VisibilityRecordV1.create(
        block_id=first.id,
        first_created_seq=1,
        render_count=1,
        last_rendered_seq=8,
        retrieval_channels_used=["focus"],
        contexts_rendered_into=[attention.receipt_hash],
        instance=_instance(8),
    )
    coverage = CoverageCycleV1.create(
        live_ids=[first.id, second.id], instance=_instance(9)
    )
    advisory = AdvisoryContextV1.create(
        warning="Scratch material is non-authoritative.",
        blocks=[first, second],
        links=[link],
        guides=[guide],
        retrieval_receipt=attention.receipt_hash,
        instance=_instance(10),
    )
    return {
        "scratch-block": (first.id, first),
        "scratch-link": (link.id, link),
        "scratch-cluster": (cluster.id, cluster),
        "scratch-membership": (membership.id, membership),
        "scratch-cluster-snapshot": (snapshot.snapshot_hash, snapshot),
        "scratch-guide": (guide.id, guide),
        "scratch-similarity": (similarity.id, similarity),
        "scratch-attention-receipt": (attention.receipt_hash, attention),
        "scratch-visibility": (visibility.id, visibility),
        "scratch-coverage-cycle": (coverage.cycle_id, coverage),
        "scratch-advisory-context": (advisory.id, advisory),
    }


def test_put_get_every_registered_scratch_schema_as_canonical_bytes(tmp_path):
    store = ObjectStore(tmp_path / "objects")
    records = _scratch_records()

    assert {name for name in SCHEMAS if name.startswith("scratch-")} == set(records)
    for schema, (oid, obj) in records.items():
        store.put(schema, obj)
        loaded_schema, loaded = store.get(oid, schema=schema)
        assert loaded_schema == schema
        assert loaded == obj
        expected = {
            "schema": schema,
            "id": oid,
            "data": obj.model_dump(mode="json", by_alias=True, exclude_none=True),
        }
        assert store._schema_path(schema, oid).read_bytes() == canonical_json(expected)


def test_same_schema_same_bytes_is_idempotent(tmp_path, monkeypatch):
    store = ObjectStore(tmp_path / "objects")
    oid, block = _scratch_records()["scratch-block"]
    store.put("scratch-block", block)
    target = store._schema_path("scratch-block", oid)
    before = target.read_bytes()

    def unexpected_replace(*_args):
        raise AssertionError("an idempotent put must not replace the canonical target")

    monkeypatch.setattr(os, "replace", unexpected_replace)
    reconstructed = ScratchBlockV1.model_validate(
        json.loads(json.dumps(block.model_dump(mode="json", by_alias=True), sort_keys=False))
    )
    store.put("scratch-block", reconstructed)

    assert target.read_bytes() == before


@pytest.mark.parametrize("scratch_first", [True, False])
def test_same_global_id_across_scratch_and_formal_schema_conflicts(tmp_path, scratch_first):
    store = ObjectStore(tmp_path / "objects")
    oid, block = _scratch_records()["scratch-block"]
    commitment = Commitment(id=oid, eval="predicate:True")

    if scratch_first:
        store.put("scratch-block", block)
        original = store._schema_path("scratch-block", oid).read_bytes()
        with pytest.raises(ObjectConflictError, match="conflicts"):
            store.put("commitment", commitment)
        assert store._schema_path("scratch-block", oid).read_bytes() == original
        assert not store._schema_path("commitment", oid).exists()
    else:
        store.put("commitment", commitment)
        original = store._schema_path("commitment", oid).read_bytes()
        with pytest.raises(ObjectConflictError, match="conflicts"):
            store.put("scratch-block", block)
        assert store._schema_path("commitment", oid).read_bytes() == original
        assert not store._schema_path("scratch-block", oid).exists()


def test_read_only_store_rejects_scratch_write_without_creating_root(tmp_path):
    root = tmp_path / "missing-objects"
    store = ObjectStore(root, read_only=True)
    _, block = _scratch_records()["scratch-block"]

    with pytest.raises(ReadOnlyObjectStoreError, match="read-only"):
        store.put("scratch-block", block)

    assert not root.exists()


def test_old_formal_object_still_loads_unchanged(tmp_path):
    store = ObjectStore(tmp_path / "objects")
    commitment = Commitment(id="legacy-compatible", eval="predicate:True")

    store.put("commitment", commitment)

    assert store.get(commitment.id) == ("commitment", commitment)
    assert store.get(commitment.id, schema="commitment") == ("commitment", commitment)


def test_legacy_flat_record_remains_readable_and_unchanged(tmp_path):
    store = ObjectStore(tmp_path / "objects")
    commitment = Commitment(id="flat-object", eval="predicate:True")
    record = {
        "schema": "commitment",
        "id": commitment.id,
        "data": commitment.model_dump(mode="json", by_alias=True),
    }
    legacy = store._path(commitment.id)
    original = canonical_json(record)
    legacy.write_bytes(original)

    assert store.get(commitment.id) == ("commitment", commitment)
    store.put("commitment", commitment)

    assert legacy.read_bytes() == original
    assert store._schema_path("commitment", commitment.id).exists()
    assert store.get(commitment.id, schema="commitment") == ("commitment", commitment)


def test_namespaced_read_rejects_conflicting_valid_legacy_record(tmp_path):
    store = ObjectStore(tmp_path / "objects")
    oid, block = _scratch_records()["scratch-block"]
    store.put("scratch-block", block)
    conflicting = Commitment(id=oid, eval="predicate:True")
    store._path(oid).write_bytes(
        canonical_json(
            {
                "schema": "commitment",
                "id": oid,
                "data": conflicting.model_dump(mode="json", by_alias=True),
            }
        )
    )

    with pytest.raises(ObjectConflictError, match="conflicts with legacy"):
        store.get(oid)
    with pytest.raises(ObjectConflictError, match="conflicts with legacy"):
        store.get(oid, schema="scratch-block")


def test_torn_namespaced_target_is_atomically_healed(tmp_path):
    store = ObjectStore(tmp_path / "objects")
    oid, block = _scratch_records()["scratch-block"]
    target = store._schema_path("scratch-block", oid)
    target.parent.mkdir(parents=True)
    target.write_bytes(b'{"schema":"scratch-block","id":')

    with pytest.raises(ValueError, match="corrupt object record"):
        store.get(oid)

    store.put("scratch-block", block)

    expected = canonical_json(
        {
            "schema": "scratch-block",
            "id": oid,
            "data": block.model_dump(mode="json", by_alias=True, exclude_none=True),
        }
    )
    assert target.read_bytes() == expected
    assert not list(target.parent.glob(f"{target.stem}.tmp.*"))
    assert store.get(oid, schema="scratch-block") == ("scratch-block", block)
