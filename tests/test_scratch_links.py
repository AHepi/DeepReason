"""C3 deterministic scratch block/revision/link service tests."""

from __future__ import annotations

import pytest

from deepreason.harness import Harness
from deepreason.scratch.errors import (
    ScratchBlockNotFound,
    ScratchLinkNotFound,
    ScratchLinkRetired,
    ScratchReadOnly,
)
from deepreason.scratch.models import ScratchProvenanceV1
from deepreason.scratch.service import ScratchService
from deepreason.scratch.state import LinkState


def _user() -> ScratchProvenanceV1:
    return ScratchProvenanceV1(actor="user", origin="test")


def test_loose_blocks_revision_branches_and_reopen(tmp_path):
    root = tmp_path / "run"
    service = ScratchService(root)
    original = service.create_block({"content": "A loose thought"}, _user())
    left = service.revise_block(original.id, {"content": "Left branch"}, _user())
    right = service.revise_block(original.id, {"content": "Right branch"}, _user())

    assert original.body.why_keep_this is None
    assert [block.id for block in service.revisions(original.id)] == [left.id, right.id]
    assert service.get_block(original.id[7:19]) == original
    assert service.get_blocks([left.id, right.id]) == [left, right]
    assert ScratchService(root).get_block(original.id) == original
    assert len({original.id, left.id, right.id}) == 3


def test_link_lifecycle_is_provisional_supersedable_and_historical(tmp_path):
    service = ScratchService(tmp_path / "run")
    one = service.create_block({"content": "one"}, _user())
    two = service.create_block({"content": "two"}, _user())
    first = service.create_link(
        {"from": one.id, "to": two.id, "relation_hint": "may connect"}, _user()
    )
    assert service.state.link_status[first.id] == LinkState.SUGGESTED

    service.mark_link_used(first.id, "investigation:one")
    assert service.state.link_status[first.id] == LinkState.ACTIVE
    replacement = service.create_link(
        {
            "from": one.id,
            "to": two.id,
            "relation_hint": "better qualification",
            "supersedes": first.id,
        },
        _user(),
    )
    assert service.state.link_status[first.id] == LinkState.SUPERSEDED

    service.retire_link(replacement.id, "Misleading in this context", _user())
    assert service.state.link_status[replacement.id] == LinkState.RETIRED
    assert service.state.link_status[first.id] == LinkState.ACTIVE
    assert [link.id for link in service.links_for(one.id)] == [first.id]
    assert [link.id for link in service.links_for(one.id, include_retired=True)] == [
        first.id,
        replacement.id,
    ]

    with pytest.raises(ScratchLinkRetired, match="SCRATCH_LINK_RETIRED"):
        service.mark_link_used(replacement.id, "investigation:two")
    with pytest.raises(ScratchLinkRetired):
        service.retire_link(replacement.id, "again", _user())


def test_link_and_block_errors_are_stable_and_historical_service_is_read_only(tmp_path):
    root = tmp_path / "run"
    service = ScratchService(root)
    block = service.create_block({"content": "one"}, _user())

    with pytest.raises(ScratchBlockNotFound) as missing:
        service.get_block("deadbeef")
    assert missing.value.code == "SCRATCH_BLOCK_NOT_FOUND"
    assert missing.value.location == "/block_id"
    with pytest.raises(ScratchLinkNotFound, match="SCRATCH_LINK_NOT_FOUND"):
        service.mark_link_used("sha256:" + "0" * 64, "context")

    before = list(root.rglob("*"))
    historical = ScratchService(Harness.at(root, 0))
    assert historical.get_block(block.id) == block
    with pytest.raises(ScratchReadOnly, match="SCRATCH_READ_ONLY"):
        historical.create_block({"content": "forbidden"}, _user())
    assert list(root.rglob("*")) == before
