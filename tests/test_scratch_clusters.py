"""C3 cluster, membership, guide, and similarity service tests."""

from __future__ import annotations

import pytest

from deepreason.scratch.errors import (
    ScratchAlreadyMember,
    ScratchClusterPrefixAmbiguous,
    ScratchNotMember,
)
from deepreason.scratch.models import (
    ClusterGuideV1,
    LLMCallRef,
    ScratchProvenanceV1,
    SimilarityHitV1,
)
from deepreason.scratch.service import ScratchService


def _user() -> ScratchProvenanceV1:
    return ScratchProvenanceV1(actor="user", origin="test")


def test_cluster_membership_order_idempotence_and_map(tmp_path):
    service = ScratchService(tmp_path / "run")
    later = service.create_block({"content": "later"}, _user())
    earlier = service.create_block({"content": "earlier"}, _user())
    cluster = service.create_cluster("Representation collapse", _user())

    service.add_cluster_member(cluster.id, later.id, "possible member", _user())
    service.add_cluster_member(cluster.id, earlier.id, None, _user())
    assert [block.id for block in service.cluster_members(cluster.id)] == sorted(
        [later.id, earlier.id]
    )
    with pytest.raises(ScratchAlreadyMember) as duplicate:
        service.add_cluster_member(cluster.id, later.id, None, _user())
    assert duplicate.value.code == "SCRATCH_ALREADY_MEMBER"

    removed = service.remove_cluster_member(
        cluster.id, later.id, "not useful locally", _user()
    )
    assert removed.action.value == "remove"
    with pytest.raises(ScratchNotMember, match="SCRATCH_NOT_MEMBER"):
        service.remove_cluster_member(cluster.id, later.id, None, _user())
    assert service.cluster_map(1, "size") == [cluster]
    assert service.get_cluster(cluster.id[7:20]) == cluster


def test_guide_is_snapshot_bound_and_becomes_stale(tmp_path):
    service = ScratchService(tmp_path / "run")
    first = service.create_block({"content": "first"}, _user())
    second = service.create_block({"content": "second"}, _user())
    cluster = service.create_cluster("Local focus", _user())
    service.add_cluster_member(cluster.id, first.id, None, _user())
    snapshot = service.cluster_snapshot(cluster.id)
    guide = ClusterGuideV1.create(
        cluster_id=cluster.id,
        based_on_snapshot=snapshot.snapshot_hash,
        working_focus="Inspect the first block",
        entry_points=[first.id],
        authored_by=LLMCallRef(
            event_seq=service.harness._next_seq,
            model="scripted",
            endpoint="fixture",
            prompt_ref="prompt",
            raw_ref="raw",
        ),
        instance=service._instance(),
    )
    service.store_guide(guide)
    assert service.current_guide(cluster.id) == guide

    service.add_cluster_member(cluster.id, second.id, None, _user())
    assert service.current_guide(cluster.id) is None
    assert service.state.guide_state(guide) == "stale"
    assert service.state.guides_by_cluster[cluster.id] == [guide]


def test_similarity_observation_never_merges_equal_or_near_blocks(tmp_path):
    service = ScratchService(tmp_path / "run")
    first = service.create_block({"content": "same body"}, _user())
    second = service.create_block({"content": "same body"}, _user())
    assert first.body_hash == second.body_hash
    assert first.id != second.id

    hit = SimilarityHitV1.create(
        block_a=first.id,
        block_b=second.id,
        embedder="deterministic-fallback",
        embedder_version="1",
        score=1.0,
        threshold_used=0.5,
        input_body_hash_a=first.body_hash,
        input_body_hash_b=second.body_hash,
        output_ref="fixture-vector",
        instance=service._instance(),
    )
    service.record_similarity(hit)
    assert set(service.state.blocks) == {first.id, second.id}
    assert service.state.links == {}
    assert service.state.similarity_hits[hit.id] == hit


def test_cluster_prefix_ambiguity_is_stable(tmp_path):
    service = ScratchService(tmp_path / "run")
    clusters = [
        service.create_cluster(f"cluster {index}", _user()) for index in range(20)
    ]
    groups: dict[str, list[str]] = {}
    for cluster in clusters:
        groups.setdefault(cluster.id[7:8], []).append(cluster.id)
    prefix = next(key for key, values in groups.items() if len(values) > 1)
    with pytest.raises(ScratchClusterPrefixAmbiguous) as error:
        service.get_cluster(prefix)
    assert error.value.code == "SCRATCH_CLUSTER_PREFIX_AMBIGUOUS"
    assert error.value.location == "/cluster_id"
