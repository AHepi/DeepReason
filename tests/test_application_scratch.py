"""D0 shared application boundary for advisory scratch queries."""

from __future__ import annotations

import argparse
import hashlib
import inspect
import io
import json
from pathlib import Path
from types import SimpleNamespace

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
from deepreason.config import Config
from deepreason.harness import Harness
from deepreason.run_manifest import ConjectureContextPolicyV1, bind_run_manifest, compile_run_manifest
from deepreason.scratch.service import ScratchService


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


def _create_v6_scratch_run(root: Path, *, active: bool = False):
    from deepreason.capabilities.policy import InquiryCapabilityPolicyV1
    from tests.test_run_input_v6_commitments import (
        _bind_v2,
        _commitment,
        _config,
        _control,
    )

    frozen = _bind_v2(root, _commitment())
    base = _config()
    config = base.model_copy(
        update={
            "scratchpad": base.scratchpad.model_copy(
                update={"enabled": True, "max_blocks_per_pack": 24}
            )
        }
    )
    control = _control(6)
    inquiry_policy = None
    if active:
        control = control.model_copy(
            update={
                "conjecture_context": ConjectureContextPolicyV1(
                    mode="harness_plus_model_request",
                    initial_max_blocks=8,
                    initial_max_guides=2,
                    max_context_expansion_requests=1,
                    max_extra_blocks=4,
                    permitted_retrieval_channels=(
                        "focus",
                        "exploratory",
                        "coverage",
                    ),
                    coverage_slot_mandatory=True,
                    exploration_slot_mandatory=True,
                )
            }
        )
        inquiry_policy = InquiryCapabilityPolicyV1(
            capability_profile="inquiry-capabilities.v2"
        )
    manifest = compile_run_manifest(
        config,
        schema_version=6,
        workload_profile="text",
        rubric_policy="forbid",
        compiled_at="2026-07-22T00:00:00Z",
        control_plane_policy=control,
        inquiry_capability_policy=inquiry_policy,
        run_input_digest=frozen.run_input_digest,
    )
    bind_run_manifest(manifest, root)
    harness = Harness(root)
    scratch = ScratchService(harness)
    blocks = tuple(
        scratch.create_block(
            {"content": f"active v6 attention thought {index}"},
            {"actor": "user", "origin": "application-v6-test"},
        )
        for index in range(3)
    )
    cluster = scratch.create_cluster(
        "active v4 attention",
        {"actor": "user", "origin": "application-v6-test"},
    )
    scratch.add_cluster_member(
        cluster.id,
        blocks[0].id,
        None,
        {"actor": "user", "origin": "application-v6-test"},
    )
    return SimpleNamespace(root=root, manifest=manifest, blocks=blocks, cluster=cluster)


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
    run = _create_v6_scratch_run(tmp_path / "run")
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
    run = _create_v6_scratch_run(tmp_path / "run")
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


def test_active_v6_attention_preview_is_deterministic_across_service_and_mcp(tmp_path):
    root = tmp_path / "run-v6"
    run = _create_v6_scratch_run(root, active=True)
    manifest, blocks, cluster = run.manifest, run.blocks, run.cluster
    assert manifest.schema_version == 6
    assert manifest.scratch_policy is not None
    assert manifest.control_plane_policy is not None
    assert manifest.control_plane_policy.mode == "active_inquiry"

    before = _tree_digest(root)
    arguments = {
        "root": str(root),
        "focus_blocks": [blocks[0].id[7:19]],
        "focus_clusters": [cluster.id[7:19]],
        "maximum_blocks": 2,
        "maximum_cluster_guides": 1,
        "deterministic_seed": 17,
    }
    query = ScratchAttentionPreviewQueryV1(
        root=arguments["root"],
        focus_blocks=tuple(arguments["focus_blocks"]),
        focus_clusters=tuple(arguments["focus_clusters"]),
        maximum_blocks=arguments["maximum_blocks"],
        maximum_cluster_guides=arguments["maximum_cluster_guides"],
        deterministic_seed=arguments["deterministic_seed"],
    )
    first = SCRATCH_QUERY_SERVICE.execute(query)
    second = SCRATCH_QUERY_SERVICE.execute(query)
    mcp_payload = _mcp_payload("scratch_attention", arguments)

    assert first == second
    assert first.presentation_payload() == mcp_payload
    assert first.committed is False
    assert first.pack.selection_receipt.id not in ScratchService(root).state.attention_receipts
    assert _tree_digest(root) == before


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
