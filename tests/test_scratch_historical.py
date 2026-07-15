"""Physical read-only guarantees for historical scratchpad views."""

from __future__ import annotations

import os
import stat

import pytest

from deepreason.cli.main import main as cli_main
from deepreason.harness import Harness, ReadOnlyHarnessError
from deepreason.scratch.events import ScratchEventPayloadV1
from deepreason.scratch.models import (
    InstanceRef,
    ScratchBlockBodyV1,
    ScratchBlockV1,
    ScratchProvenanceV1,
    domain_hash,
)


def _tree_snapshot(root):
    """Capture directories, types, modes, mtimes, and bytes exactly."""

    root = root.resolve()
    paths = [
        root,
        *sorted(root.rglob("*"), key=lambda item: item.relative_to(root).as_posix()),
    ]
    snapshot = []
    for path in paths:
        observed = path.lstat()
        if stat.S_ISREG(observed.st_mode):
            payload = path.read_bytes()
        elif stat.S_ISLNK(observed.st_mode):
            payload = os.fsencode(os.readlink(path))
        else:
            payload = b""
        snapshot.append(
            (
                "." if path == root else path.relative_to(root).as_posix(),
                stat.S_IFMT(observed.st_mode),
                stat.S_IMODE(observed.st_mode),
                observed.st_mtime_ns,
                payload,
            )
        )
    return tuple(snapshot)


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
    before = _tree_snapshot(root)

    historical = Harness.at(root, 0)
    assert historical.scratch_state.blocks[block.id] == block
    assert historical.scratch_state.current_snapshot_hash(
        domain_hash("fixture.cluster", {})
    ).startswith("sha256:")
    assert _tree_snapshot(root) == before

    with pytest.raises(ReadOnlyHarnessError, match="read-only"):
        historical.record_scratch_event(
            ScratchEventPayloadV1(
                action="link_used",
                actor="harness",
                inputs=[block.id],
                context_ref="forbidden",
            )
        )
    assert _tree_snapshot(root) == before


def test_historical_scratch_cli_show_and_map_make_zero_filesystem_changes(
    tmp_path, monkeypatch, capsys
):
    root = tmp_path / "run"
    live = Harness(root)
    service_run_id = domain_hash("test.run", {"root": "historical-cli"})
    block = ScratchBlockV1.create(
        ScratchBlockBodyV1(content="An old loose thought."),
        InstanceRef(run_id=service_run_id, seq=0),
        ScratchProvenanceV1(actor="user"),
    )
    live.objects.put("scratch-block", block)
    live.record_scratch_event(
        ScratchEventPayloadV1(
            action="block_created", actor="user", outputs=[block.id]
        )
    )
    before = _tree_snapshot(root)
    monkeypatch.setattr("deepreason.easy.load_credentials", lambda: None)

    for command in (
        ["show", block.id[7:19]],
        ["map"],
    ):
        assert (
            cli_main(
                [
                    "--root",
                    str(root),
                    "scratch",
                    *command,
                    "--at-seq",
                    "0",
                    "--json",
                ]
            )
            == 0
        )
        capsys.readouterr()
        assert _tree_snapshot(root) == before


def test_missing_historical_root_is_not_materialized(tmp_path):
    root = tmp_path / "missing"
    with pytest.raises(FileNotFoundError):
        Harness.at(root, 0)
    assert not root.exists()
