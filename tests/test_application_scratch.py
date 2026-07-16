"""D0 shared application boundary for advisory scratch queries."""

from __future__ import annotations

import argparse
import hashlib
import inspect
import io
import json
from pathlib import Path

import pytest
from pydantic import TypeAdapter, ValidationError

from deepreason import mcp_scratch_bridge as mcp
from deepreason.application.scratch import (
    SCRATCH_QUERY_SERVICE,
    ScratchAttentionPreviewQueryV1,
    ScratchOpenPreviewQueryV1,
    ScratchQueryV1,
    ScratchRecordDirectOpenQueryV1,
)
from deepreason.cli import scratch as cli_scratch
from deepreason.cli.scratch import dispatch_scratch, register_scratch_parser
from deepreason.harness import Harness
from deepreason.scratch.service import ScratchService
from tests.test_mcp_scratch_bridge import _create_run


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="deepreason")
    parser.add_argument("--root", default=".deepreason")
    parser.add_argument("--config", default=None)
    commands = parser.add_subparsers(dest="command", required=True)
    register_scratch_parser(commands)
    return parser


def _cli_json(root: Path, *arguments: str) -> dict:
    args = _parser().parse_args(["--root", str(root), "scratch", *arguments, "--json"])
    stdout = io.StringIO()
    stderr = io.StringIO()
    status = dispatch_scratch(args, stdout=stdout, stderr=stderr)
    assert status == 0, stderr.getvalue()
    return json.loads(stdout.getvalue())["result"]


def _tree_digest(root: Path) -> str:
    digest = hashlib.sha256()
    for path in sorted(item for item in root.rglob("*") if item.is_file()):
        digest.update(path.relative_to(root).as_posix().encode())
        digest.update(path.read_bytes())
    return digest.hexdigest()


def _mcp_payload(name: str, arguments: dict) -> dict:
    payload = mcp.call_tool(name, arguments)
    truncation = payload.pop("truncation")
    assert truncation == {"truncated": False, "fields": []}
    return payload


def test_query_union_is_closed_and_direct_open_is_not_a_preview_mode(tmp_path):
    adapter = TypeAdapter(ScratchQueryV1)
    preview = adapter.validate_python(
        {
            "operation": "open_preview",
            "root": str(tmp_path),
            "block": "deadbeef",
        }
    )
    direct = adapter.validate_python(
        {
            "operation": "record_direct_open",
            "root": str(tmp_path),
            "block": "deadbeef",
        }
    )
    assert isinstance(preview, ScratchOpenPreviewQueryV1)
    assert isinstance(direct, ScratchRecordDirectOpenQueryV1)

    with pytest.raises(ValidationError):
        adapter.validate_python(
            {
                "operation": "open_preview",
                "root": str(tmp_path),
                "block": "deadbeef",
                "record_direct_open": True,
            }
        )
    with pytest.raises(ValidationError):
        adapter.validate_python(
            {
                "operation": "record_direct_open",
                "root": str(tmp_path),
                "block": "deadbeef",
                "at_seq": 0,
            }
        )


def test_cli_and_mcp_query_payloads_are_equivalent_and_read_only(tmp_path):
    run = _create_run(tmp_path / "run")
    event_seq = Harness(run.root, read_only=True)._next_seq - 1
    before = _tree_digest(run.root)
    block = run.blocks[0].id[7:19]
    common = {"root": str(run.root), "at_seq": event_seq, "limit": 2}

    cases = (
        (
            "scratch_map",
            {**common, "ordering": "size"},
            ("map", "--ordering", "size", "--limit", "2", "--at-seq", str(event_seq)),
        ),
        (
            "scratch_search",
            {**common, "query": "shared literal"},
            (
                "search",
                "shared literal",
                "--limit",
                "2",
                "--at-seq",
                str(event_seq),
            ),
        ),
        (
            "scratch_related",
            {**common, "block": block},
            ("related", block, "--limit", "2", "--at-seq", str(event_seq)),
        ),
        (
            "scratch_open",
            {**common, "block": block},
            ("show", block, "--limit", "2", "--at-seq", str(event_seq)),
        ),
    )
    for name, arguments, cli_arguments in cases:
        mcp_payload = _mcp_payload(name, arguments)
        if name == "scratch_open":
            assert mcp_payload.pop("committed") is False
        assert _cli_json(run.root, *cli_arguments) == mcp_payload

    assert _tree_digest(run.root) == before


def test_preview_and_record_direct_open_have_distinct_mutation_semantics(tmp_path):
    root = tmp_path / "run"
    block = ScratchService(root).create_block(
        {"content": "open boundary"},
        {"actor": "user", "origin": "application-test"},
    )
    before = _tree_digest(root)
    preview = SCRATCH_QUERY_SERVICE.execute(
        ScratchOpenPreviewQueryV1(root=str(root), block=block.id)
    )
    assert preview.committed is False
    assert preview.retrieval_receipt_id is None
    assert _tree_digest(root) == before

    recorded = SCRATCH_QUERY_SERVICE.execute(
        ScratchRecordDirectOpenQueryV1(root=str(root), block=block.id)
    )
    assert recorded.committed is True
    assert recorded.retrieval_receipt_id.startswith("sha256:")
    state = ScratchService(root).state
    assert recorded.retrieval_receipt_id in state.attention_receipts
    assert state.visibility[block.id].render_count == 1
    assert [channel.value for channel in state.visibility[block.id].retrieval_channels_used] == [
        "direct_open"
    ]


def test_attention_preview_matches_mcp_and_remains_uncommitted(tmp_path):
    run = _create_run(tmp_path / "run")
    before = _tree_digest(run.root)
    arguments = {
        "root": str(run.root),
        "focus_blocks": [run.blocks[0].id[7:19]],
        "focus_clusters": [run.cluster.id[7:19]],
        "maximum_blocks": 2,
        "maximum_cluster_guides": 1,
        "deterministic_seed": 7,
    }
    result = SCRATCH_QUERY_SERVICE.execute(
        ScratchAttentionPreviewQueryV1(
            root=arguments["root"],
            focus_blocks=tuple(arguments["focus_blocks"]),
            focus_clusters=tuple(arguments["focus_clusters"]),
            maximum_blocks=arguments["maximum_blocks"],
            maximum_cluster_guides=arguments["maximum_cluster_guides"],
            deterministic_seed=arguments["deterministic_seed"],
        )
    )
    assert result.presentation_payload() == _mcp_payload("scratch_attention", arguments)
    assert result.committed is False
    assert result.pack.selection_receipt.id not in ScratchService(run.root).state.attention_receipts
    assert _tree_digest(run.root) == before


def test_cli_and_mcp_handlers_are_thin_application_adapters():
    mcp_source = inspect.getsource(mcp)
    assert "deepreason.cli.scratch import" not in mcp_source
    for handler in (
        mcp._scratch_map,
        mcp._scratch_search,
        mcp._scratch_open,
        mcp._scratch_related,
        mcp._scratch_attention,
        cli_scratch._show,
        cli_scratch._search,
        cli_scratch._related,
        cli_scratch._map,
    ):
        source = inspect.getsource(handler)
        assert "SCRATCH_QUERY_SERVICE.execute" in source
        assert "ScratchService(" not in source
        assert "Harness(" not in source
