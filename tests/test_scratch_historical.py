"""Physical read-only guarantees for historical scratchpad views."""

from __future__ import annotations

import hashlib

import pytest

from deepreason.harness import Harness, ReadOnlyHarnessError
from deepreason.scratch.events import ScratchEventPayloadV1
from deepreason.scratch.models import (
    InstanceRef,
    ScratchBlockBodyV1,
    ScratchBlockV1,
    ScratchProvenanceV1,
    domain_hash,
)


def _tree_digest(root) -> str:
    digest = hashlib.sha256()
    for path in sorted(root.rglob("*")):
        digest.update(str(path.relative_to(root)).encode())
        if path.is_file():
            digest.update(path.read_bytes())
    return digest.hexdigest()


def test_historical_scratch_views_create_no_files_or_events(tmp_path):
    root = tmp_path / "run"
    live = Harness(root)
    run_id = domain_hash("test.run", {"root": "historical"})
    block = ScratchBlockV1.create(
        ScratchBlockBodyV1(content="An old unfinished thought."),
        InstanceRef(run_id=run_id, seq=0),
        ScratchProvenanceV1(actor="user"),
    )
    live.objects.put("scratch-block", block)
    live.record_scratch_event(
        ScratchEventPayloadV1(
            action="block_created", actor="user", outputs=[block.id]
        )
    )
    before = _tree_digest(root)

    historical = Harness.at(root, 0)
    assert historical.scratch_state.blocks[block.id] == block
    assert historical.scratch_state.current_snapshot_hash(
        domain_hash("fixture.cluster", {})
    ).startswith("sha256:")
    assert _tree_digest(root) == before

    with pytest.raises(ReadOnlyHarnessError, match="read-only"):
        historical.record_scratch_event(
            ScratchEventPayloadV1(
                action="link_used",
                actor="harness",
                inputs=[block.id],
                context_ref="forbidden",
            )
        )
    assert _tree_digest(root) == before


def test_missing_historical_root_is_not_materialized(tmp_path):
    root = tmp_path / "missing"
    with pytest.raises(FileNotFoundError):
        Harness.at(root, 0)
    assert not root.exists()

