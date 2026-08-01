"""Canonical advisory contexts are bounded, append-only, and replayable."""

from __future__ import annotations

import hashlib

import pytest

from deepreason.harness import Harness
from deepreason.scratch.attention import (
    AttentionPlanner,
    AttentionPolicyV1,
    AttentionRequestV1,
)
from deepreason.scratch.errors import ScratchReadOnly
from deepreason.scratch.events import ScratchEventPayloadV1
from deepreason.scratch.models import (
    AdvisoryContextV1,
    RetrievalChannel,
    ScratchProvenanceV1,
)
from deepreason.scratch.service import ScratchService


CHANNELS = [
    channel for channel in RetrievalChannel if channel != RetrievalChannel.DIRECT_OPEN
]


def _policy():
    return AttentionPolicyV1(
        max_blocks_per_pack=8,
        max_guides_per_pack=2,
        semantic_retrieval=False,
        keyword_retrieval=False,
        coverage_enabled=False,
        coverage_slot_every_n_packs=1,
        exploratory_fraction=0,
        underexposed_fraction=0,
        dormant_after_events=10,
        similarity_top_k=4,
        guide_max_open_threads=4,
        guide_max_entry_points=4,
        channel_priority=CHANNELS,
        per_channel_limits={channel: 8 for channel in CHANNELS},
    )


def _tree_digest(root) -> str:
    digest = hashlib.sha256()
    for path in sorted(root.rglob("*")):
        digest.update(str(path.relative_to(root)).encode())
        if path.is_file():
            digest.update(path.read_bytes())
    return digest.hexdigest()


def test_advisory_context_binds_exact_committed_attention_and_replays(tmp_path):
    service = ScratchService(tmp_path / "run")
    provenance = ScratchProvenanceV1(actor="user", origin="context-test")
    first = service.create_block({"content": "First loose thought."}, provenance)
    second = service.create_block({"content": "Second loose thought."}, provenance)
    link = service.create_link(
        {"from": first.id, "to": second.id, "relation_hint": "may connect"},
        provenance,
    )
    formal_before = service.harness.state.model_dump(mode="json")
    request = AttentionRequestV1(
        focus_blocks=[first.id, second.id],
        maximum_blocks=2,
        maximum_cluster_guides=0,
        include_nearby=False,
        include_recent=False,
        include_loose=False,
        include_dormant=False,
        include_underexposed=False,
        include_exploratory=False,
        deterministic_seed=7,
    )
    planner = AttentionPlanner(service, _policy())
    pack = planner.plan(request)
    receipt = planner.commit_render(pack)

    context = service.create_advisory_context(pack)

    assert context.retrieval_receipt == receipt.id
    assert [block.id for block in context.blocks] == list(receipt.final_order)
    assert context.links == [link]
    assert "non-authoritative" in context.warning
    assert service.state.advisory_contexts[context.id] == context
    assert service.harness.state.model_dump(mode="json") == formal_before
    reopened = Harness(service.harness.root)
    assert reopened.scratch_state.advisory_contexts[context.id] == context
    assert reopened.state.model_dump(mode="json") == formal_before


def test_historical_advisory_context_open_is_physically_read_only(tmp_path):
    service = ScratchService(tmp_path / "run")
    block = service.create_block(
        {"content": "Bounded thought."},
        ScratchProvenanceV1(actor="user", origin="context-test"),
    )
    planner = AttentionPlanner(service, _policy())
    pack = planner.plan(
        AttentionRequestV1(
            focus_blocks=[block.id],
            maximum_blocks=1,
            maximum_cluster_guides=0,
            include_nearby=False,
            include_recent=False,
            include_loose=False,
            include_dormant=False,
            include_underexposed=False,
            include_exploratory=False,
            deterministic_seed=1,
        )
    )
    planner.commit_render(pack)
    context = service.create_advisory_context(pack)
    context_seq = service.harness._next_seq - 1
    before = _tree_digest(service.harness.root)
    historical = ScratchService(service.harness.root, upto_seq=context_seq)

    assert historical.state.advisory_contexts[context.id] == context
    assert _tree_digest(service.harness.root) == before
    with pytest.raises(ScratchReadOnly):
        historical.create_advisory_context(pack)
    assert _tree_digest(service.harness.root) == before


def test_context_requires_the_exact_committed_receipt(tmp_path):
    service = ScratchService(tmp_path / "run")
    block = service.create_block(
        {"content": "Uncommitted selection."},
        ScratchProvenanceV1(actor="user", origin="context-test"),
    )
    pack = AttentionPlanner(service, _policy()).plan(
        AttentionRequestV1(
            focus_blocks=[block.id],
            maximum_blocks=1,
            maximum_cluster_guides=0,
            include_nearby=False,
            include_recent=False,
            include_loose=False,
            include_dormant=False,
            include_underexposed=False,
            include_exploratory=False,
            deterministic_seed=1,
        )
    )

    with pytest.raises(ValueError, match="commit the exact attention receipt"):
        service.create_advisory_context(pack)
    assert service.state.advisory_contexts == {}


def test_prepared_context_is_pure_and_commits_exact_receipt_and_context(tmp_path):
    service = ScratchService(tmp_path / "run")
    block = service.create_block(
        {"content": "Prepared but not yet rendered."},
        ScratchProvenanceV1(actor="user", origin="context-test"),
    )
    cycle = service.start_coverage_cycle()
    policy = _policy().model_copy(update={"coverage_enabled": True})
    planner = AttentionPlanner(service, policy)
    pack = planner.plan(
        AttentionRequestV1(
            focus_blocks=[block.id],
            maximum_blocks=1,
            maximum_cluster_guides=0,
            include_nearby=False,
            include_recent=False,
            include_loose=False,
            include_dormant=False,
            include_underexposed=False,
            include_exploratory=False,
            deterministic_seed=4,
        )
    )
    before_seq = service.harness._next_seq
    before = _tree_digest(service.harness.root)

    prepared = service.prepare_advisory_context(pack)

    assert service.harness._next_seq == before_seq
    assert _tree_digest(service.harness.root) == before
    assert service.state.attention_receipts == {}
    assert service.state.advisory_contexts == {}
    assert service.state.visibility == {}

    committed = service.commit_prepared_advisory_context(pack, prepared)

    assert committed == prepared
    assert service.state.attention_receipts[pack.selection_receipt.id] == (
        pack.selection_receipt
    )
    assert service.state.advisory_contexts[prepared.id] == prepared
    assert service.state.visibility[block.id].render_count == 1
    assert service.state.coverage_cycles[cycle.id].rendered_block_ids == [block.id]
    assert service.state.coverage_cycles[cycle.id].completed
    reopened = Harness(service.harness.root)
    assert reopened.scratch_state.attention_receipts == (
        service.state.attention_receipts
    )
    assert reopened.scratch_state.advisory_contexts == (
        service.state.advisory_contexts
    )


def test_raw_context_event_cannot_inject_an_out_of_selection_link(tmp_path):
    service = ScratchService(tmp_path / "run")
    provenance = ScratchProvenanceV1(actor="user", origin="context-test")
    selected = service.create_block({"content": "Selected thought."}, provenance)
    outside = service.create_block({"content": "Unselected thought."}, provenance)
    link = service.create_link(
        {"from": selected.id, "to": outside.id, "relation_hint": "must not leak"},
        provenance,
    )
    planner = AttentionPlanner(service, _policy())
    pack = planner.plan(
        AttentionRequestV1(
            focus_blocks=[selected.id],
            maximum_blocks=1,
            maximum_cluster_guides=0,
            include_nearby=False,
            include_recent=False,
            include_loose=False,
            include_dormant=False,
            include_underexposed=False,
            include_exploratory=False,
            deterministic_seed=2,
        )
    )
    receipt = planner.commit_render(pack)
    context = AdvisoryContextV1.create(
        warning="Scratch material is non-authoritative.",
        blocks=[selected],
        links=[link],
        retrieval_receipt=receipt.id,
        instance=service._instance(),
    )
    service.harness.objects.put("scratch-advisory-context", context)

    with pytest.raises(ValueError, match="must connect selected blocks"):
        service.harness.record_scratch_event(
            ScratchEventPayloadV1(
                action="advisory_context_created",
                actor="harness",
                inputs=[receipt.id],
                outputs=[context.id],
                retrieval_receipt_ref=receipt.id,
            )
        )
    assert context.id not in service.state.advisory_contexts
