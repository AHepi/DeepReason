"""C4 deterministic bounded multi-channel attention tests."""

from __future__ import annotations

import pytest

from deepreason.scratch.attention import (
    AttentionPlanner,
    AttentionPolicyV1,
    AttentionRequestV1,
)
from deepreason.scratch.models import (
    RetrievalChannel,
    ScratchProvenanceV1,
    SimilarityHitV1,
)
from deepreason.scratch.service import ScratchService


CHANNELS = [
    RetrievalChannel.FOCUS,
    RetrievalChannel.LINK,
    RetrievalChannel.CLUSTER,
    RetrievalChannel.KEYWORD,
    RetrievalChannel.SEMANTIC,
    RetrievalChannel.RECENT,
    RetrievalChannel.LOOSE,
    RetrievalChannel.DORMANT,
    RetrievalChannel.UNDEREXPOSED,
    RetrievalChannel.EXPLORATORY,
    RetrievalChannel.COVERAGE,
]


def _policy(**changes) -> AttentionPolicyV1:
    values = {
        "max_blocks_per_pack": 12,
        "max_guides_per_pack": 2,
        "semantic_retrieval": True,
        "keyword_retrieval": True,
        "coverage_enabled": True,
        "coverage_slot_every_n_packs": 1,
        "exploratory_fraction": 0.10,
        "underexposed_fraction": 0.15,
        "dormant_after_events": 0,
        "similarity_top_k": 4,
        "similarity_threshold": 0.5,
        "guide_max_open_threads": 8,
        "guide_max_entry_points": 8,
        "channel_priority": CHANNELS,
        "per_channel_limits": {channel: 12 for channel in CHANNELS},
    }
    values.update(changes)
    return AttentionPolicyV1(**values)


def _request(focus: list[str], **changes) -> AttentionRequestV1:
    values = {
        "focus_blocks": focus,
        "maximum_blocks": 8,
        "maximum_cluster_guides": 2,
        "include_nearby": True,
        "include_recent": True,
        "include_loose": True,
        "include_dormant": True,
        "include_underexposed": True,
        "include_exploratory": True,
        "deterministic_seed": 17,
    }
    values.update(changes)
    return AttentionRequestV1(**values)


def _user() -> ScratchProvenanceV1:
    return ScratchProvenanceV1(actor="user", origin="attention-test")


def _record_similarity(service, first, second, score=0.9):
    hit = SimilarityHitV1.create(
        block_a=min(first.id, second.id),
        block_b=max(first.id, second.id),
        embedder="scripted",
        embedder_version="1",
        score=score,
        threshold_used=0.5,
        input_body_hash_a=(
            first.body_hash if first.id < second.id else second.body_hash
        ),
        input_body_hash_b=(
            second.body_hash if first.id < second.id else first.body_hash
        ),
        output_ref="scripted-vector",
        instance=service._instance(),
    )
    service.record_similarity(hit)
    return hit


def test_every_attention_channel_is_independent_and_pack_is_reproducible(tmp_path):
    service = ScratchService(tmp_path / "run")
    focus = service.create_block({"content": "anchor vocabulary"}, _user())
    linked = service.create_block({"content": "linked only"}, _user())
    clustered = service.create_block({"content": "cluster only"}, _user())
    keyword = service.create_block({"content": "anchor literal match"}, _user())
    semantic = service.create_block({"content": "semantic only"}, _user())
    loose = service.create_block({"content": "unlinked loose"}, _user())
    service.create_link(
        {"from": focus.id, "to": linked.id, "relation_hint": "provisional"},
        _user(),
    )
    cluster = service.create_cluster("local region", _user())
    service.add_cluster_member(cluster.id, clustered.id, None, _user())
    _record_similarity(service, focus, semantic)
    cycle = service.start_coverage_cycle()
    request = _request(focus=[focus.id], focus_clusters=[cluster.id])
    planner = AttentionPlanner(service, _policy())

    before_formal = service.harness.state.model_dump(mode="json")
    first = planner.plan(request)
    second = planner.plan(request)
    assert first == second
    assert first.selection_receipt.receipt_hash == second.selection_receipt.receipt_hash
    assert len(first.blocks) <= request.maximum_blocks <= 12
    assert service.state.visibility == {}
    assert service.harness.state.model_dump(mode="json") == before_formal

    channels = first.channel_blocks
    assert channels[RetrievalChannel.FOCUS] == [focus.id]
    assert linked.id in channels[RetrievalChannel.LINK]
    assert clustered.id in channels[RetrievalChannel.CLUSTER]
    assert keyword.id in channels[RetrievalChannel.KEYWORD]
    assert semantic.id in channels[RetrievalChannel.SEMANTIC]
    assert channels[RetrievalChannel.RECENT]
    assert loose.id in channels[RetrievalChannel.LOOSE]
    assert channels[RetrievalChannel.DORMANT]
    assert channels[RetrievalChannel.UNDEREXPOSED]
    assert channels[RetrievalChannel.EXPLORATORY]
    assert channels[RetrievalChannel.COVERAGE] == [
        service.state.coverage_cycles[cycle.id].pending_block_ids[0]
    ]

    final_ids = [block.id for block in first.blocks]
    assert final_ids == list(first.selection_receipt.final_order)
    assert len(final_ids) == len(set(final_ids))
    planner.commit_render(first, context_ref="model:attention")
    assert set(service.state.visibility) == set(final_ids)
    assert service.harness.state.model_dump(mode="json") == before_formal


def test_semantic_channel_can_be_disabled_and_threshold_only_changes_retrieval(tmp_path):
    service = ScratchService(tmp_path / "run")
    focus = service.create_block({"content": "focus"}, _user())
    other = service.create_block({"content": "other"}, _user())
    _record_similarity(service, focus, other, score=0.7)
    request = _request(
        [focus.id],
        include_recent=False,
        include_loose=False,
        include_dormant=False,
        include_underexposed=False,
        include_exploratory=False,
    )

    disabled = AttentionPlanner(
        service, _policy(semantic_retrieval=False, coverage_enabled=False)
    ).plan(request)
    strict = AttentionPlanner(
        service,
        _policy(similarity_threshold=0.8, coverage_enabled=False),
    ).plan(request)
    permissive = AttentionPlanner(
        service,
        _policy(similarity_threshold=0.6, coverage_enabled=False),
    ).plan(request)
    assert disabled.channel_blocks[RetrievalChannel.SEMANTIC] == []
    assert strict.channel_blocks[RetrievalChannel.SEMANTIC] == []
    assert permissive.channel_blocks[RetrievalChannel.SEMANTIC] == [other.id]
    assert set(service.state.blocks) == {focus.id, other.id}
    assert service.state.links == {}


def test_reserved_channels_admit_material_outside_repeated_focus(tmp_path):
    service = ScratchService(tmp_path / "run")
    focus = [
        service.create_block({"content": f"focus {index}"}, _user())
        for index in range(5)
    ]
    outside = service.create_block({"content": "outside the attractor"}, _user())
    policy = _policy(
        coverage_enabled=False,
        exploratory_fraction=0.25,
        underexposed_fraction=0.25,
    )
    pack = AttentionPlanner(service, policy).plan(
        _request(
            [block.id for block in focus],
            maximum_blocks=4,
            include_nearby=False,
            include_recent=False,
            include_loose=False,
            include_dormant=False,
        )
    )
    final = set(pack.selection_receipt.final_order)
    assert outside.id in final
    assert len(final) == 4
    assert pack.selection_receipt.excluded_by_global_limit


def test_stale_plan_is_rejected_and_compact_policy_caps_are_enforced(tmp_path):
    service = ScratchService(tmp_path / "run")
    focus = service.create_block({"content": "focus"}, _user())
    planner = AttentionPlanner(service, _policy(coverage_enabled=False))
    pack = planner.plan(_request([focus.id]))
    service.create_block({"content": "later event"}, _user())
    with pytest.raises(ValueError, match="stale"):
        planner.commit_render(pack)

    with pytest.raises(ValueError, match="compiled policy"):
        planner.plan(_request([focus.id], maximum_blocks=13))
    with pytest.raises(ValueError, match="greater than 0"):
        AttentionRequestV1(
            maximum_blocks=0,
            maximum_cluster_guides=0,
            deterministic_seed=0,
        )


def test_coverage_eventually_renders_irrelevant_buried_block_through_planner(tmp_path):
    service = ScratchService(tmp_path / "run")
    focus = service.create_block({"content": "present vocabulary"}, _user())
    buried = service.create_block(
        {"content": "semantically distant old unlinked unknown"}, _user()
    )
    cluster = service.create_cluster("Dormant cluster", _user())
    service.add_cluster_member(cluster.id, buried.id, "historical", _user())
    policy = _policy(
        coverage_slot_every_n_packs=1,
        exploratory_fraction=0,
        underexposed_fraction=0,
    )
    planner = AttentionPlanner(service, policy)
    request = _request(
        [focus.id],
        maximum_blocks=2,
        include_nearby=False,
        include_recent=False,
        include_loose=False,
        include_dormant=False,
        include_underexposed=False,
        include_exploratory=False,
    )

    rendered: list[str] = []
    for index in range(5):
        pack = planner.plan(request)
        if index == 0:
            assert pack.selection_receipt.coverage_cycle_id is None
            assert service.active_coverage_cycle() is None
        rendered.extend(pack.selection_receipt.final_order)
        planner.commit_render(pack)
        if index == 0:
            assert service.active_coverage_cycle() is not None
        if (
            buried.id in service.state.visibility
            and RetrievalChannel.COVERAGE
            in service.state.visibility[buried.id].retrieval_channels_used
        ):
            break
    assert buried.id in rendered
    visibility = service.state.visibility[buried.id]
    assert RetrievalChannel.COVERAGE in visibility.retrieval_channels_used
