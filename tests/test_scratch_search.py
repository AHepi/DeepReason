"""C3 deterministic bounded literal and non-semantic query tests."""

from __future__ import annotations

import pytest

from deepreason.scratch.errors import (
    ScratchBlockPrefixAmbiguous,
    ScratchLimitInvalid,
)
from deepreason.scratch.models import AttentionReceiptV1, ScratchProvenanceV1, domain_hash
from deepreason.scratch.events import ScratchEventPayloadV1
from deepreason.scratch.service import ScratchService


def _user() -> ScratchProvenanceV1:
    return ScratchProvenanceV1(actor="user", origin="test")


def _shared_prefix(ids: list[str]) -> str:
    for width in range(1, 65):
        groups: dict[str, list[str]] = {}
        for value in ids:
            groups.setdefault(value[7 : 7 + width], []).append(value)
        collision = next((prefix for prefix, values in groups.items() if len(values) > 1), None)
        if collision is not None:
            return collision
    raise AssertionError("expected a hash-prefix collision")


def test_literal_search_casefold_whitespace_ranking_and_stability(tmp_path):
    service = ScratchService(tmp_path / "run")
    phrase = service.create_block({"content": "  STRASSE\ncollapse  "}, _user())
    token_only = service.create_block(
        {"content": "collapse appears before Straße"}, _user()
    )
    unrelated = service.create_block({"content": "different vocabulary"}, _user())

    first = service.search_phrase("straße   collapse", 10)
    second = ScratchService(tmp_path / "run").search_phrase("STRASSE collapse", 10)
    assert [block.id for block in first] == [phrase.id, token_only.id]
    assert [block.id for block in second] == [phrase.id, token_only.id]
    assert unrelated.id not in {block.id for block in first}
    assert service.search_phrase("", 10) == []


def test_prefix_ambiguity_and_limit_errors_have_stable_codes(tmp_path):
    service = ScratchService(tmp_path / "run")
    blocks = [
        service.create_block({"content": f"block {index}"}, _user())
        for index in range(40)
    ]
    prefix = _shared_prefix([block.id for block in blocks])
    with pytest.raises(ScratchBlockPrefixAmbiguous) as ambiguous:
        service.get_block(prefix)
    assert ambiguous.value.code == "SCRATCH_BLOCK_PREFIX_AMBIGUOUS"
    assert ambiguous.value.location == "/block_id"
    assert len(ambiguous.value.details["candidates"]) >= 2

    for invalid in (0, -1, True, 10_001):
        with pytest.raises(ScratchLimitInvalid) as error:
            service.search_phrase("block", invalid)
        assert error.value.as_dict()["code"] == "SCRATCH_LIMIT_INVALID"
        assert error.value.as_dict()["location"] == "/limit"


def test_bounded_navigation_queries_are_deterministic(tmp_path):
    service = ScratchService(tmp_path / "run")
    old = service.create_block({"content": "old unlinked"}, _user())
    seen = service.create_block({"content": "seen"}, _user())
    linked = service.create_block({"content": "linked"}, _user())
    service.create_link(
        {"from": seen.id, "to": linked.id, "relation_hint": "provisional"},
        _user(),
    )

    assert [block.id for block in service.unlinked_blocks(10)] == [old.id]
    assert old.id in {
        block.id
        for block in service.dormant_blocks(
            service.harness._next_seq + 10, dormant_after_events=3, limit=10
        )
    }
    assert [block.id for block in service.underexposed_blocks(3)] == sorted(
        [old.id, seen.id, linked.id]
    )
    sample_one = [block.id for block in service.sample_without_semantic_relevance(7, 3)]
    sample_two = [
        block.id for block in service.sample_without_semantic_relevance(7, 3)
    ]
    assert sample_one == sample_two
    assert set(sample_one) == {old.id, seen.id, linked.id}

    receipt = AttentionReceiptV1.create(
        state_seq=service.harness._next_seq,
        request_hash=domain_hash("test.request", {"one": 1}),
        selected_by_channel={"direct_open": [seen.id]},
        final_order=[seen.id],
        excluded_by_global_limit=[],
        excluded_by_channel={},
        deterministic_seed=0,
        instance=service._instance(),
    )
    service.harness.objects.put("scratch-attention-receipt", receipt)
    service.harness.record_scratch_event(
        ScratchEventPayloadV1(
            action="attention_pack_rendered",
            actor="harness",
            outputs=[receipt.id],
            retrieval_receipt_ref=receipt.id,
        )
    )
    assert [
        block.id for block in service.unseen_in_investigation([receipt.id], 10)
    ] == sorted([old.id, linked.id], key=lambda item: service.state.blocks[item].instance.seq)
