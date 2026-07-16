"""C11 narrow MCP scratch reads and grounded bridge operations."""

from __future__ import annotations

import hashlib
import json
import threading
from types import SimpleNamespace

import pytest

from deepreason import mcp_scratch_bridge as mcp
from deepreason import mcp_server
from deepreason.application import bridge as bridge_application
from deepreason.config import Config
from deepreason.harness import Harness
from deepreason.llm.adapter import LLMAdapter
from deepreason.llm.endpoints import MockEndpoint
from deepreason.ontology import Problem, ProblemProvenance
from deepreason.run_manifest import (
    bind_run_manifest,
    compile_run_manifest,
    write_run_manifest,
)
from deepreason.scratch.service import ScratchService


STAMP = "2026-07-16T00:00:00Z"


def _route() -> dict:
    return {
        "endpoint_id": "mcp-fixture-route",
        "endpoint": "https://models.invalid/v1",
        "model": "fixture-31b",
        "provider": "fixture",
        "family": "fixture",
    }


def _manifest(*, scratch_max_blocks: int = 24):
    return compile_run_manifest(
        Config(
            scratchpad={
                "enabled": True,
                "max_blocks_per_pack": scratch_max_blocks,
            },
            bridge={
                "mode": "grounded_two_stage",
                "grounding_review": False,
                "max_schema_repair_attempts": 0,
                "max_grounding_repair_attempts": 0,
            },
            roles={"summarizer": _route(), "thesis": _route()},
        ),
        schema_version=3,
        workload_profile="text",
        rubric_policy="forbid",
        compiled_at=STAMP,
    )


def _create_run(root, *, scratch_max_blocks: int = 24):
    harness = Harness(root)
    harness.register_problem(
        Problem(
            id="problem-mcp-grounded",
            description="What conclusion is justified?",
            provenance=ProblemProvenance.model_validate(
                {"trigger": "seed", "from": []}
            ),
        )
    )
    manifest = _manifest(scratch_max_blocks=scratch_max_blocks)
    bind_run_manifest(manifest, root)
    service = ScratchService(harness)
    blocks = [
        service.create_block(
            {"content": f"shared literal thought {index}"},
            {"actor": "user", "origin": "mcp-test"},
        )
        for index in range(4)
    ]
    link = service.create_link(
        {
            "from": blocks[0].id,
            "to": blocks[1].id,
            "relation_hint": "may qualify",
        },
        {"actor": "user", "origin": "mcp-test"},
    )
    cluster = service.create_cluster(
        "possible local explanation", {"actor": "user", "origin": "mcp-test"}
    )
    service.add_cluster_member(
        cluster.id,
        blocks[0].id,
        None,
        {"actor": "user", "origin": "mcp-test"},
    )
    service.add_cluster_member(
        cluster.id,
        blocks[2].id,
        None,
        {"actor": "user", "origin": "mcp-test"},
    )
    return SimpleNamespace(
        root=root,
        manifest=manifest,
        manifest_ref=root / "run-manifest.json",
        blocks=blocks,
        link=link,
        cluster=cluster,
    )


@pytest.fixture()
def mcp_run(tmp_path):
    return _create_run(tmp_path / "run")


def _tree_digest(root) -> str:
    digest = hashlib.sha256()
    for path in sorted(item for item in root.rglob("*") if item.is_file()):
        digest.update(path.relative_to(root).as_posix().encode())
        digest.update(path.read_bytes())
    return digest.hexdigest()


def _formal_snapshot(root) -> tuple[str, str, str]:
    harness = Harness(root, read_only=True)
    return (
        harness.state.model_dump_json(),
        json.dumps(harness.commitments, sort_keys=True),
        json.dumps(harness.warrants, sort_keys=True),
    )


def _assert_closed_objects(schema: object) -> None:
    if isinstance(schema, dict):
        if schema.get("type") == "object":
            assert schema.get("additionalProperties") is False
        for value in schema.values():
            _assert_closed_objects(value)
    elif isinstance(schema, list):
        for value in schema:
            _assert_closed_objects(value)


def _scripted_adapter(harness: Harness) -> LLMAdapter:
    return LLMAdapter(
        {
            "summarizer": MockEndpoint(
                [
                    json.dumps(
                        {
                            "entries": [
                                {
                                    "entry_key": "K1",
                                    "claim_class": "unknown",
                                    "claim": "The conclusion is not established.",
                                }
                            ],
                            "uncovered_requirements": [
                                {
                                    "requirement": "Grounding for a positive answer.",
                                    "reason": "No source-backed evidence is present.",
                                }
                            ],
                        }
                    )
                ],
                name="mcp-scripted-summarizer",
            ),
            "thesis": MockEndpoint(
                [
                    json.dumps(
                        {
                            "sections": [
                                {
                                    "span_id": "S1",
                                    "text": "The requested conclusion remains unknown.",
                                    "rendering_mode": "unknown",
                                    "ledger_entry_handles": ["E1"],
                                }
                            ],
                            "resolution": "insufficient_evidence",
                            "resolution_reason": "The record supplies no grounding.",
                        }
                    )
                ],
                name="mcp-scripted-thesis",
            ),
        },
        harness.blobs,
        retry_max=0,
    )


def _server_call(name: str, arguments: dict) -> tuple[dict, dict]:
    response = mcp_server.handle(
        {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "tools/call",
            "params": {"name": name, "arguments": arguments},
        }
    )
    result = response["result"]
    return result, json.loads(result["content"][0]["text"])


def test_exact_nine_tools_have_recursively_closed_bounded_schemas():
    tools = mcp.tool_definitions()

    assert [tool["name"] for tool in tools] == [
        "scratch_map",
        "scratch_search",
        "scratch_open",
        "scratch_related",
        "scratch_attention",
        "start_bridge",
        "bridge_status",
        "bridge_result",
        "bridge_claims",
    ]
    assert len(tools) == 9
    for tool in tools:
        _assert_closed_objects(tool["inputSchema"])
    attention_schema = next(
        tool["inputSchema"] for tool in tools if tool["name"] == "scratch_attention"
    )
    for field in ("focus_blocks", "focus_clusters"):
        assert attention_schema["properties"][field]["uniqueItems"] is True
        assert attention_schema["properties"][field]["items"]["maxLength"] == 512
        assert "pattern" in attention_schema["properties"][field]["items"]
    serialized = json.dumps(tools)
    for forbidden in (
        "provider_credentials",
        "raw_event",
        "status_setter",
        "model_prompt",
        "shell_command",
        "source_yaml",
        "route_override",
    ):
        assert forbidden not in serialized


@pytest.mark.parametrize(
    ("name", "extra"),
    [
        ("scratch_map", {"file": "/etc/passwd"}),
        ("scratch_search", {"raw_event": {"action": "append"}}),
        ("scratch_open", {"status": "accepted"}),
        ("scratch_related", {"route": "other"}),
        ("scratch_attention", {"prompt": "invoke a model"}),
        ("start_bridge", {"provider": "override"}),
        ("bridge_status", {"set_state": "completed"}),
        ("bridge_result", {"path": "objects/raw"}),
        ("bridge_claims", {"event": "inject"}),
    ],
)
def test_runtime_rejects_unknown_control_and_raw_access_fields(
    mcp_run, name, extra
):
    base = {"root": str(mcp_run.root)}
    if name == "scratch_search":
        base["query"] = "literal"
    elif name in {"scratch_open", "scratch_related"}:
        base["block"] = mcp_run.blocks[0].id
    elif name == "start_bridge":
        base.update(
            {
                "problem": "problem-mcp-grounded",
                "run_manifest_ref": str(mcp_run.manifest_ref),
            }
        )
    base.update(extra)

    with pytest.raises(ValueError, match="MCP_INPUT_INVALID"):
        mcp.call_tool(name, base)


def test_scratch_reads_are_bounded_and_physically_read_only(mcp_run):
    before_tree = _tree_digest(mcp_run.root)
    before_formal = _formal_snapshot(mcp_run.root)
    calls = (
        (
            "scratch_map",
            {"root": str(mcp_run.root), "limit": 2, "ordering": "size"},
        ),
        (
            "scratch_search",
            {"root": str(mcp_run.root), "query": "shared literal", "limit": 2},
        ),
        (
            "scratch_open",
            {"root": str(mcp_run.root), "block": mcp_run.blocks[0].id[7:19]},
        ),
        (
            "scratch_related",
            {"root": str(mcp_run.root), "block": mcp_run.blocks[0].id[7:19]},
        ),
    )
    results = {name: mcp.call_tool(name, arguments) for name, arguments in calls}

    assert len(results["scratch_search"]["blocks"]) == 2
    assert results["scratch_open"]["committed"] is False
    assert results["scratch_open"]["retrieval_receipt_id"] is None
    assert results["scratch_related"]["advisory_warning"].startswith(
        "Similarity is retrieval-only"
    )
    assert results["scratch_map"]["clusters"][0]["cluster_id"] == mcp_run.cluster.id
    assert _tree_digest(mcp_run.root) == before_tree
    assert _formal_snapshot(mcp_run.root) == before_formal
    transport, searched = _server_call(
        "scratch_search",
        {"root": str(mcp_run.root), "query": "shared literal", "limit": 1},
    )
    assert transport["isError"] is False
    assert len(searched["blocks"]) == 1
    assert _tree_digest(mcp_run.root) == before_tree


def test_scratch_attention_is_a_pure_uncommitted_plan(mcp_run):
    before_tree = _tree_digest(mcp_run.root)
    state_before = ScratchService(Harness(mcp_run.root, read_only=True)).state
    receipt_ids = set(state_before.attention_receipts)
    visibility = dict(state_before.visibility)
    coverage = dict(state_before.coverage_cycles)

    result = mcp.call_tool(
        "scratch_attention",
        {
            "root": str(mcp_run.root),
            "focus_blocks": [mcp_run.blocks[0].id[7:19]],
            "focus_clusters": [mcp_run.cluster.id[7:19]],
            "maximum_blocks": 2,
            "maximum_cluster_guides": 1,
            "deterministic_seed": 7,
        },
    )

    state_after = ScratchService(Harness(mcp_run.root, read_only=True)).state
    assert result["committed"] is False
    assert len(result["blocks"]) <= 2
    assert (
        result["selection_receipt"]["id"]
        not in state_after.attention_receipts
    )
    assert result["selection_receipt"]["id"] == result["selection_receipt"][
        "receipt_hash"
    ]
    assert set(state_after.attention_receipts) == receipt_ids
    assert dict(state_after.visibility) == visibility
    assert dict(state_after.coverage_cycles) == coverage
    assert _tree_digest(mcp_run.root) == before_tree


def test_historical_scratch_read_and_large_content_remain_bounded(mcp_run):
    long_block = ScratchService(mcp_run.root).create_block(
        {"content": "x" * 20_000}, {"actor": "user", "origin": "mcp-test"}
    )
    before = _tree_digest(mcp_run.root)

    opened = mcp.call_tool(
        "scratch_open",
        {
            "root": str(mcp_run.root),
            "block": long_block.id,
            "at_seq": long_block.instance.seq,
            "limit": 1,
        },
    )

    assert len(opened["block"]["body"]["content"]) == 16_384
    assert opened["truncation"]["truncated"] is True
    assert _tree_digest(mcp_run.root) == before


def test_attention_candidate_and_exclusion_arrays_are_globally_capped(tmp_path):
    mcp_run = _create_run(tmp_path / "wide-attention", scratch_max_blocks=64)
    service = ScratchService(mcp_run.root)
    for index in range(40):
        service.create_block(
            {"content": f"extra attention candidate {index}"},
            {"actor": "user", "origin": "mcp-test"},
        )

    result = mcp.call_tool(
        "scratch_attention",
        {
            "root": str(mcp_run.root),
            "maximum_blocks": 1,
            "maximum_cluster_guides": 0,
        },
    )

    def assert_bounded(value):
        if isinstance(value, list):
            assert len(value) <= 25
            for item in value:
                assert_bounded(item)
        elif isinstance(value, dict):
            for item in value.values():
                assert_bounded(item)

    assert_bounded(result)
    assert result["truncation"]["truncated"] is True


def test_identifiers_reject_path_traversal_before_any_operation(mcp_run):
    with pytest.raises(ValueError, match="MCP_INPUT_INVALID"):
        mcp.call_tool(
            "scratch_open",
            {"root": str(mcp_run.root), "block": "../../objects"},
        )
    prefix = mcp_run.blocks[0].id[7:19]
    with pytest.raises(ValueError, match="MCP_INPUT_INVALID"):
        mcp.call_tool(
            "scratch_attention",
            {
                "root": str(mcp_run.root),
                "focus_blocks": [prefix.upper(), prefix.lower()],
            },
        )
    with pytest.raises(ValueError, match="MCP_INPUT_INVALID"):
        mcp.call_tool(
            "start_bridge",
            {
                "root": str(mcp_run.root),
                "problem": "../../other-run",
                "run_manifest_ref": str(mcp_run.manifest_ref),
            },
        )


def test_bound_manifest_symlink_is_rejected_without_reading_target(
    mcp_run, tmp_path
):
    secret = "BOUND_MANIFEST_SECRET_MUST_NOT_ECHO"
    target = tmp_path / "secret-bound.txt"
    target.write_text(secret, encoding="utf-8")
    manifest_path = mcp_run.root / "run-manifest.json"
    manifest_path.unlink()
    try:
        manifest_path.symlink_to(target)
    except OSError:
        pytest.skip("platform does not permit unprivileged symlink creation")

    with pytest.raises(ValueError) as error:
        mcp.call_tool(
            "start_bridge",
            {"root": str(mcp_run.root), "problem": "problem-mcp-grounded"},
        )

    assert "BRIDGE_MANIFEST_INVALID" in str(error.value)
    assert secret not in str(error.value)
    assert target.read_text(encoding="utf-8") == secret


def test_supplied_manifest_sidecar_symlink_is_rejected_without_secret_echo(
    tmp_path,
):
    root = tmp_path / "unbound-run"
    Harness(root).register_problem(
        Problem(
            id="problem-mcp-grounded",
            description="What conclusion is justified?",
            provenance=ProblemProvenance.model_validate(
                {"trigger": "seed", "from": []}
            ),
        )
    )
    manifest_path, sidecar = write_run_manifest(
        _manifest(), tmp_path / "candidate-manifest.json"
    )
    secret = "SIDECAR_SECRET_MUST_NOT_ECHO"
    target = tmp_path / "secret-sidecar.txt"
    target.write_text(secret, encoding="utf-8")
    sidecar.unlink()
    try:
        sidecar.symlink_to(target)
    except OSError:
        pytest.skip("platform does not permit unprivileged symlink creation")

    with pytest.raises(ValueError) as error:
        mcp.call_tool(
            "start_bridge",
            {
                "root": str(root),
                "problem": "problem-mcp-grounded",
                "run_manifest_ref": str(manifest_path),
            },
        )

    assert "BRIDGE_MANIFEST_INVALID" in str(error.value)
    assert secret not in str(error.value)
    assert target.read_text(encoding="utf-8") == secret


def test_bridge_start_poll_result_claims_and_unresolved_success(
    mcp_run, monkeypatch
):
    monkeypatch.setattr(
        bridge_application,
        "_build_bridge_adapter",
        lambda _manifest, harness: _scripted_adapter(harness),
    )
    formal_before = _formal_snapshot(mcp_run.root)
    progress = []

    started = mcp.call_tool(
        "start_bridge",
        {
            "root": str(mcp_run.root),
            "problem": "problem-mcp",
            "target": "answer",
            "run_manifest_ref": str(mcp_run.manifest_ref),
            "focus_blocks": [mcp_run.blocks[0].id[7:19]],
            "budget": {"token_budget": 100_000},
        },
        progress_callback=progress.append,
    )
    assert started["state"] == "running"
    thread = mcp._BRIDGE_THREADS[str(mcp_run.root.resolve())]
    thread.join(timeout=5)
    assert not thread.is_alive()

    status = mcp.call_tool("bridge_status", {"root": str(mcp_run.root)})
    result = mcp.call_tool(
        "bridge_result", {"root": str(mcp_run.root), "limit": 1}
    )
    claims = mcp.call_tool(
        "bridge_claims", {"root": str(mcp_run.root), "limit": 1}
    )

    assert status["state"] == "completed"
    assert status["process_status"] == "success"
    assert status["resolution"] == "insufficient_evidence"
    assert result["terminal"]["process_status"] == "success"
    assert result["output"]["resolution"] == "insufficient_evidence"
    assert claims["entries"][0]["claim_class"] == "unknown"
    assert [event["seq"] for event in progress] == [0, 1]
    assert _formal_snapshot(mcp_run.root) == formal_before
    completed = mcp.call_tool(
        "start_bridge",
        {
            "root": str(mcp_run.root),
            "problem": "problem-mcp-grounded",
        },
    )
    assert completed["state"] == "completed"
    transport, transported_result = _server_call(
        "bridge_result", {"root": str(mcp_run.root), "limit": 1}
    )
    assert transport["isError"] is False
    assert transported_result["output"]["resolution"] == "insufficient_evidence"


def test_duplicate_start_returns_typed_busy_without_launching_second_worker(
    tmp_path, monkeypatch
):
    run = _create_run(tmp_path / "busy-run")
    monkeypatch.setattr(
        bridge_application,
        "_build_bridge_adapter",
        lambda _manifest, harness: _scripted_adapter(harness),
    )
    entered = threading.Event()
    release = threading.Event()

    def blocked(_prepared):
        entered.set()
        assert release.wait(timeout=5)

    monkeypatch.setattr(bridge_application, "_execute_bridge", blocked)
    arguments = {
        "root": str(run.root),
        "problem": "problem-mcp-grounded",
        "run_manifest_ref": str(run.manifest_ref),
    }

    assert mcp.call_tool("start_bridge", arguments)["state"] == "running"
    assert entered.wait(timeout=5)
    busy = mcp.call_tool("start_bridge", arguments)
    assert busy["state"] == "busy"
    assert busy["schema"] == "deepreason-mcp-bridge-start-v1"
    release.set()
    mcp._BRIDGE_THREADS[str(run.root.resolve())].join(timeout=5)


def test_process_lock_contention_is_typed_busy_without_mutation(mcp_run):
    from deepreason.locking import operator_locks

    locks = operator_locks(mcp_run.root, owner="other-process", blocking=False)
    try:
        before_tree = _tree_digest(mcp_run.root)
        before_seq = Harness(mcp_run.root, read_only=True)._next_seq
        transport, payload = _server_call(
            "start_bridge",
            {
                "root": str(mcp_run.root),
                "problem": "problem-mcp-grounded",
            },
        )
        assert transport["isError"] is False
        assert payload["state"] == "busy"
        assert Harness(mcp_run.root, read_only=True)._next_seq == before_seq
        assert _tree_digest(mcp_run.root) == before_tree
        assert not (mcp_run.root / "bridge-operation-status.json").exists()
        assert not (mcp_run.root / "bridge-operation-result.json").exists()
    finally:
        locks.release()


def test_status_before_start_is_typed_and_result_is_not_an_arbitrary_read(mcp_run):
    status = mcp.call_tool("bridge_status", {"root": str(mcp_run.root)})
    assert status == {
        "schema": "deepreason-mcp-bridge-status-v1",
        "state": "not_started",
    }
    with pytest.raises(ValueError, match="BRIDGE_RECORD_UNAVAILABLE"):
        mcp.call_tool("bridge_result", {"root": str(mcp_run.root)})


def test_worker_failure_is_persisted_and_visible_after_thread_registry_loss(
    tmp_path, monkeypatch, capsys
):
    run = _create_run(tmp_path / "failed-worker")
    monkeypatch.setattr(
        bridge_application,
        "_build_bridge_adapter",
        lambda _manifest, harness: _scripted_adapter(harness),
    )
    monkeypatch.setattr(
        bridge_application,
        "_execute_bridge",
        lambda _prepared: (_ for _ in ()).throw(RuntimeError("worker exploded")),
    )

    started = mcp.call_tool(
        "start_bridge",
        {
            "root": str(run.root),
            "problem": "problem-mcp-grounded",
        },
    )
    assert started["state"] == "running"
    key = str(run.root.resolve())
    mcp._BRIDGE_THREADS[key].join(timeout=5)
    mcp._BRIDGE_THREADS.pop(key, None)  # simulate a fresh MCP process

    status = mcp.call_tool("bridge_status", {"root": str(run.root)})
    result = mcp.call_tool("bridge_result", {"root": str(run.root)})
    assert status["state"] == "failed"
    assert status["error_code"] == "BRIDGE_WORKER_FAILED"
    assert result["process_status"] == "failure"
    assert result["error_code"] == "BRIDGE_WORKER_FAILED"
    assert (run.root / "bridge-operation-status.json").is_file()
    assert (run.root / "bridge-operation-result.json").is_file()
    assert not (run.root / "bridge-status.json").exists()
    assert not (run.root / "bridge-result.json").exists()

    from deepreason.cli.main import main

    assert main(["--root", str(run.root), "bridge", "status", "--json"]) == 1
    cli_status = json.loads(capsys.readouterr().out)
    assert cli_status["error_code"] == "BRIDGE_WORKER_FAILED"
    assert cli_status["non_epistemic"] is True
    assert main(["--root", str(run.root), "bridge", "result", "--json"]) == 1
    cli_result = json.loads(capsys.readouterr().out)
    assert cli_result == result


def test_thread_start_failure_persists_both_operation_records_and_releases_lock(
    tmp_path, monkeypatch
):
    run = _create_run(tmp_path / "thread-start-failure")
    monkeypatch.setattr(
        bridge_application,
        "_build_bridge_adapter",
        lambda _manifest, harness: _scripted_adapter(harness),
    )
    monkeypatch.setattr(
        threading.Thread,
        "start",
        lambda _thread: (_ for _ in ()).throw(RuntimeError("cannot start")),
    )

    started = mcp.call_tool(
        "start_bridge",
        {"root": str(run.root), "problem": "problem-mcp-grounded"},
    )

    assert started["state"] == "failed"
    status = mcp.call_tool("bridge_status", {"root": str(run.root)})
    result = mcp.call_tool("bridge_result", {"root": str(run.root)})
    assert status["error_type"] == "RuntimeError"
    assert result["error_type"] == "RuntimeError"
    assert (run.root / "bridge-operation-status.json").is_file()
    assert (run.root / "bridge-operation-result.json").is_file()
    from deepreason.locking import operator_locks

    locks = operator_locks(run.root, owner="post-failure-probe", blocking=False)
    locks.release()


def test_progress_callback_failure_cannot_relabel_success(mcp_run, monkeypatch):
    monkeypatch.setattr(
        bridge_application,
        "_build_bridge_adapter",
        lambda _manifest, harness: _scripted_adapter(harness),
    )

    started = mcp.call_tool(
        "start_bridge",
        {
            "root": str(mcp_run.root),
            "problem": "problem-mcp-grounded",
        },
        progress_callback=lambda _event: (_ for _ in ()).throw(
            RuntimeError("transport callback failed")
        ),
    )
    assert started["state"] == "running"
    mcp._BRIDGE_THREADS[str(mcp_run.root.resolve())].join(timeout=5)

    status = mcp.call_tool("bridge_status", {"root": str(mcp_run.root)})
    assert status["state"] == "completed"
    assert status["process_status"] == "success"
    assert not (mcp_run.root / "bridge-operation-status.json").exists()
    assert not (mcp_run.root / "bridge-operation-result.json").exists()


def test_system_exit_progress_callback_cannot_strand_worker_locks(
    mcp_run, monkeypatch
):
    monkeypatch.setattr(
        bridge_application,
        "_build_bridge_adapter",
        lambda _manifest, harness: _scripted_adapter(harness),
    )

    started = mcp.call_tool(
        "start_bridge",
        {
            "root": str(mcp_run.root),
            "problem": "problem-mcp-grounded",
        },
        progress_callback=lambda _event: (_ for _ in ()).throw(
            SystemExit("transport callback exited")
        ),
    )
    assert started["state"] == "running"
    thread = mcp._BRIDGE_THREADS[str(mcp_run.root.resolve())]
    thread.join(timeout=5)
    assert not thread.is_alive()

    status = mcp.call_tool("bridge_status", {"root": str(mcp_run.root)})
    assert status["state"] == "completed"
    assert status["process_status"] == "success"
    from deepreason.locking import operator_locks

    locks = operator_locks(mcp_run.root, owner="callback-exit-probe", blocking=False)
    locks.release()


def test_unknown_tool_cannot_reach_mutation_or_broad_dispatch(mcp_run):
    for name in (
        "scratch_add",
        "scratch_link",
        "raw_object_put",
        "append_event",
        "set_status",
        "invoke_model",
        "read_file",
        "shell",
    ):
        with pytest.raises(ValueError, match="MCP_TOOL_NOT_EXPOSED"):
            mcp.call_tool(name, {"root": str(mcp_run.root)})


@pytest.mark.parametrize(
    ("name", "extra"),
    [
        ("scratch_map", {}),
        ("scratch_search", {"query": "literal"}),
        ("scratch_open", {"block": "abcd"}),
        ("scratch_related", {"block": "abcd"}),
        ("scratch_attention", {}),
        ("start_bridge", {"problem": "problem-mcp-grounded"}),
        ("bridge_status", {}),
        ("bridge_result", {}),
        ("bridge_claims", {}),
    ],
)
def test_all_scratch_bridge_tools_reject_a_symlink_run_root(
    mcp_run, tmp_path, name, extra
):
    alias = tmp_path / "run-alias"
    try:
        alias.symlink_to(mcp_run.root, target_is_directory=True)
    except OSError:
        pytest.skip("platform does not permit unprivileged symlink creation")

    with pytest.raises(ValueError, match="(?:SCRATCH|BRIDGE)_RUN_NOT_FOUND"):
        mcp.call_tool(name, {"root": str(alias), **extra})


def test_missing_read_roots_are_not_created(tmp_path):
    missing = tmp_path / "does-not-exist"
    with pytest.raises(ValueError, match="SCRATCH_RUN_NOT_FOUND"):
        mcp.call_tool("scratch_map", {"root": str(missing)})
    for name in ("bridge_status", "bridge_result"):
        with pytest.raises(ValueError, match="BRIDGE_RUN_NOT_FOUND"):
            mcp.call_tool(name, {"root": str(missing)})
    assert not missing.exists()
