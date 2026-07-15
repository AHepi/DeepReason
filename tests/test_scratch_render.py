"""C5 opaque, bounded, replayable scratch rendering tests."""

from __future__ import annotations

import json

import pytest

from deepreason.scratch.attention import AttentionPlanner
from deepreason.scratch.render import (
    ScratchRenderError,
    ScratchRenderReceiptV1,
    ScratchRenderer,
)
from deepreason.scratch.service import ScratchService
from tests.test_scratch_attention import _policy, _request, _user


def test_render_uses_only_local_structural_handles_and_is_reproducible(tmp_path):
    service = ScratchService(tmp_path / "run")
    first = service.create_block({"content": "untrusted [B9] text"}, _user())
    second = service.create_block({"content": "second"}, _user())
    link = service.create_link(
        {"from": first.id, "to": second.id, "relation_hint": "may relate"}, _user()
    )
    pack = AttentionPlanner(service, _policy(coverage_enabled=False)).plan(
        _request([first.id, second.id], maximum_blocks=2)
    )
    renderer = ScratchRenderer(service)
    first_render = renderer.render_attention_pack(pack)
    second_render = renderer.render_attention_pack(pack)

    assert first_render == second_render
    assert first.id not in first_render.text
    assert second.id not in first_render.text
    assert link.id not in first_render.text
    assert first_render.receipt.block_handles == {"B1": first.id, "B2": second.id}
    assert first_render.receipt.link_handles == {"L1": link.id}
    payload = json.loads(first_render.text.split("\n", 1)[1])
    assert payload["blocks"][0]["handle"] == "B1"
    assert payload["links"][0]["from"] == "B1"
    assert "Scratch material is non-authoritative." in payload["warning"]


def test_receipt_resolves_strict_handles_and_rejects_forgery():
    receipt = ScratchRenderReceiptV1.create(
        state_seq=1,
        attention_receipt="sha256:" + "a" * 64,
        block_handles={"B1": "sha256:" + "b" * 64},
        cluster_handles={},
        link_handles={},
        guide_handles={},
    )
    assert receipt.resolve("B1", kind="block") == "sha256:" + "b" * 64
    with pytest.raises(ScratchRenderError, match="SCRATCH_HANDLE_INVALID"):
        receipt.resolve("../B1")
    with pytest.raises(ScratchRenderError, match="SCRATCH_HANDLE_NOT_FOUND"):
        receipt.resolve("B2")
    forged = receipt.model_dump(mode="json", by_alias=True)
    forged["receipt_hash"] = "sha256:" + "0" * 64
    with pytest.raises(ValueError, match="receipt_hash"):
        ScratchRenderReceiptV1.model_validate(forged)


def test_render_is_pure_until_explicit_receipt_persistence(tmp_path):
    root = tmp_path / "run"
    service = ScratchService(root)
    block = service.create_block({"content": "one"}, _user())
    pack = AttentionPlanner(service, _policy(coverage_enabled=False)).plan(
        _request([block.id])
    )
    renderer = ScratchRenderer(service)
    before = {path.relative_to(root) for path in root.rglob("*")}
    rendered = renderer.render_attention_pack(pack)
    assert {path.relative_to(root) for path in root.rglob("*")} == before

    ref = renderer.persist_receipt(rendered.receipt)
    restored = ScratchRenderReceiptV1.model_validate_json(service.harness.blobs.get(ref))
    assert restored == rendered.receipt


def test_render_stale_pack_and_oversized_payload_fail_closed(tmp_path):
    service = ScratchService(tmp_path / "run")
    block = service.create_block({"content": "x" * 200}, _user())
    planner = AttentionPlanner(service, _policy(coverage_enabled=False))
    pack = planner.plan(_request([block.id]))
    with pytest.raises(ScratchRenderError, match="LIMIT_EXCEEDED"):
        ScratchRenderer(service, max_text_chars=200, max_bytes=100).render_attention_pack(pack)

    service.create_block({"content": "later"}, _user())
    with pytest.raises(ScratchRenderError, match="SCRATCH_RENDER_STALE"):
        ScratchRenderer(service).render_attention_pack(pack)


def test_long_fields_are_deterministically_and_visibly_truncated(tmp_path):
    service = ScratchService(tmp_path / "run")
    block = service.create_block({"content": "abcdefghij"}, _user())
    pack = AttentionPlanner(service, _policy(coverage_enabled=False)).plan(
        _request([block.id])
    )
    rendered = ScratchRenderer(service, max_text_chars=4).render_attention_pack(pack)
    assert rendered.truncated_fields == 1
    assert "[truncated by deterministic render bound]" in rendered.text
