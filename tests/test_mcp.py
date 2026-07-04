"""MCP server (docs/AGENT.md): the harness as agent-installable tools.
Protocol handling is pure functions (handle/call_tool), so the full
initialize -> tools/list -> tools/call flow is testable without a
subprocess. The tool surface must be the §13 verb set — no status-setting
tool may exist."""

import json

from deepreason import mcp_server
from deepreason.ontology import Status


def _call(name: str, arguments: dict) -> dict:
    return mcp_server.handle(
        {"jsonrpc": "2.0", "id": 1, "method": "tools/call",
         "params": {"name": name, "arguments": arguments}}
    )["result"]


def test_initialize_and_tools_list():
    init = mcp_server.handle({"jsonrpc": "2.0", "id": 0, "method": "initialize", "params": {}})
    assert init["result"]["serverInfo"]["name"] == "deepreason"
    assert mcp_server.handle({"jsonrpc": "2.0", "method": "notifications/initialized"}) is None
    tools = mcp_server.handle({"jsonrpc": "2.0", "id": 1, "method": "tools/list"})
    names = {t["name"] for t in tools["result"]["tools"]}
    assert {"seed_problem", "run_cycles", "frontier", "theory", "why",
            "eval_report", "docket", "appellate_rule"} <= names
    # No tool sets a status — adjudication is not on the surface (§0).
    assert not any("status" in n or "accept" in n or "refute" in n for n in names)
    for tool in tools["result"]["tools"]:
        assert tool["description"] and tool["inputSchema"]["type"] == "object"


def test_seed_then_inspect_roundtrip(tmp_path):
    root = str(tmp_path / "h")
    result = _call(
        "seed_problem",
        {
            "root": root,
            "problem": {"id": "pi-x", "description": "explain x",
                        "criteria": ["k-x", "skeleton-wf"]},
            "commitments": [{"id": "k-x", "eval": "predicate:'x' in content"}],
            "standard": {"id": "std-x", "rubric": "must name a mechanism"},
        },
    )
    assert result["isError"] is False
    assert "pi-x" in result["content"][0]["text"]

    frontier = _call("frontier", {"root": root})
    assert frontier["isError"] is False
    listing = json.loads(frontier["content"][0]["text"])
    assert listing[0]["problem"] == "pi-x"

    # skeleton-wf was auto-registered; standard artifact exists and is accepted
    from deepreason.harness import Harness
    from pathlib import Path

    harness = Harness(Path(root))
    assert "skeleton-wf" in harness.commitments
    assert Status.ACCEPTED in set(harness.state.status.values())


def test_run_cycles_without_engine_is_tool_error(tmp_path):
    root = str(tmp_path / "h")
    _call("seed_problem", {"root": root, "problem": {"id": "pi-x", "description": "x"}})
    result = _call("run_cycles", {"root": root, "cycles": 1})
    assert result["isError"] is True
    assert "conjecturer" in result["content"][0]["text"]


def test_unknown_tool_and_method():
    result = _call("set_status", {"id": "a", "status": "accepted"})
    assert result["isError"] is True
    err = mcp_server.handle({"jsonrpc": "2.0", "id": 9, "method": "no/such"})
    assert err["error"]["code"] == -32601
    assert mcp_server.handle({"jsonrpc": "2.0", "method": "no/such/notification"}) is None
