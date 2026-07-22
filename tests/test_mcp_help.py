"""Focused coverage for the bounded novice-facing MCP help surface."""

from __future__ import annotations

import json
import os
import socket
from pathlib import Path

import pytest

from deepreason import mcp_server


HELP_TOOL_NAMES = (
    "get_capabilities",
    "get_help_topic",
    "get_request_requirements",
)
HELP_TOPICS = (
    "overview",
    "examples",
    "creating_a_run",
    "epistemic_outcomes",
    "scratchpad",
    "grounded_bridge",
    "troubleshooting",
)
REQUEST_OPERATIONS = (
    "reasoning_run",
    "continue_run",
    "grounded_bridge",
)
SUPPORTED_TOOL_NAMES = {
    "start_run",
    "run_status",
    "run_result",
    "continue_run",
    "cancel_run",
    "scratch_map",
    "scratch_search",
    "scratch_open",
    "scratch_related",
    "scratch_attention",
    "start_bridge",
    "bridge_status",
    "bridge_result",
    "bridge_claims",
    *HELP_TOOL_NAMES,
}
ANNOTATIONS = {
    "readOnlyHint": True,
    "destructiveHint": False,
    "idempotentHint": True,
    "openWorldHint": False,
}


@pytest.fixture(autouse=True)
def _default_surface(monkeypatch):
    monkeypatch.delenv("DEEPREASON_ENABLE_LEGACY_MCP", raising=False)


def _listed_tools() -> dict[str, dict]:
    response = mcp_server.handle(
        {"jsonrpc": "2.0", "id": 1, "method": "tools/list"}
    )
    return {tool["name"]: tool for tool in response["result"]["tools"]}


def _call(name: str, arguments: dict) -> dict:
    response = mcp_server.handle(
        {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "tools/call",
            "params": {"name": name, "arguments": arguments},
        }
    )
    return response["result"]


def _payload(name: str, arguments: dict) -> dict:
    result = _call(name, arguments)
    assert result["isError"] is False
    return json.loads(result["content"][0]["text"])


def _tree_snapshot(root: Path) -> list[tuple[str, int]]:
    return sorted(
        (
            str((Path(directory) / filename).relative_to(root)),
            (Path(directory) / filename).stat().st_size,
        )
        for directory, _, filenames in os.walk(root)
        for filename in filenames
    )


def test_help_tools_are_listed_with_exact_closed_schemas_and_annotations(monkeypatch):
    initialization = mcp_server.handle(
        {"jsonrpc": "2.0", "id": 0, "method": "initialize", "params": {}}
    )
    assert initialization["result"]["serverInfo"]["name"] == "deepreason"
    assert "operator-prepared" in initialization["result"]["instructions"]
    assert "RunManifest schema 6" in initialization["result"]["instructions"]

    tools = _listed_tools()
    assert set(tools) == SUPPORTED_TOOL_NAMES
    monkeypatch.setenv("DEEPREASON_ENABLE_LEGACY_MCP", "1")
    assert set(_listed_tools()) == SUPPORTED_TOOL_NAMES
    assert tuple(name for name in tools if name in HELP_TOOL_NAMES) == HELP_TOOL_NAMES
    assert {name: tools[name]["inputSchema"] for name in HELP_TOOL_NAMES} == {
        "get_capabilities": {
            "type": "object",
            "properties": {},
            "additionalProperties": False,
        },
        "get_help_topic": {
            "type": "object",
            "properties": {
                "topic": {"type": "string", "enum": list(HELP_TOPICS)},
            },
            "required": ["topic"],
            "additionalProperties": False,
        },
        "get_request_requirements": {
            "type": "object",
            "properties": {
                "operation": {"type": "string", "enum": list(REQUEST_OPERATIONS)},
            },
            "required": ["operation"],
            "additionalProperties": False,
        },
    }
    for name in HELP_TOOL_NAMES:
        assert tools[name]["annotations"] == ANNOTATIONS


def test_capabilities_are_deterministic_and_only_describe_registered_core_operations():
    tools = _listed_tools()
    first = _payload("get_capabilities", {})
    second = _payload("get_capabilities", {})

    assert first == second
    assert set(first) == {"schema_version", "capabilities", "limitations"}
    assert first["schema_version"] == "deepreason.mcp-help.v1"
    assert [capability["id"] for capability in first["capabilities"]] == [
        "reasoning_runs",
        "continuation",
        "run_information",
        "cancellation",
        "scratchpad_browsing",
        "grounded_bridge",
        "help",
    ]
    for capability in first["capabilities"]:
        assert set(capability) == {"id", "summary", "operations"}
        assert isinstance(capability["summary"], str)
        assert capability["operations"]
        assert all(name in tools for name in capability["operations"])
    assert first["capabilities"][-1]["operations"] == list(HELP_TOOL_NAMES)
    assert all(
        isinstance(limitation, str) and len(limitation) <= 256
        for limitation in first["limitations"]
    )

    serialized = json.dumps(first, sort_keys=True).casefold()
    for forbidden in (
        "website",
        "campaign",
        "jolt",
        "doctor",
        "defended",
        "trial",
        "experimental",
        "legacy",
        "hash",
        "path",
        "file",
        "directory",
        "filesystem",
    ):
        assert forbidden not in serialized
    assert "operator-prepared v6 root" in serialized
    assert "accepts no provider, route, policy, credential" in serialized


@pytest.mark.parametrize("topic", HELP_TOPICS)
def test_each_help_topic_uses_the_stable_bounded_shape(topic: str):
    payload = _payload("get_help_topic", {"topic": topic})

    assert set(payload) == {
        "schema_version",
        "topic",
        "title",
        "summary",
        "details",
        "examples",
    }
    assert payload["schema_version"] == "deepreason.mcp-help.v1"
    assert payload["topic"] == topic
    assert isinstance(payload["title"], str)
    assert isinstance(payload["summary"], str)
    assert 1 <= len(payload["details"]) <= 4
    assert 1 <= len(payload["examples"]) <= 4
    assert all(
        isinstance(value, str) and len(value) <= 512
        for value in [payload["title"], payload["summary"], *payload["details"], *payload["examples"]]
    )
    assert payload == _payload("get_help_topic", {"topic": topic})


@pytest.mark.parametrize("operation", REQUEST_OPERATIONS)
def test_each_request_requirements_response_uses_the_stable_bounded_shape(
    operation: str,
):
    payload = _payload("get_request_requirements", {"operation": operation})

    assert set(payload) == {
        "schema_version",
        "operation",
        "required_information",
        "optional_information",
        "next_operation",
    }
    assert payload["schema_version"] == "deepreason.mcp-help.v1"
    assert payload["operation"] == operation
    assert payload["next_operation"] in _listed_tools()
    assert "root" not in {
        entry["field"] for entry in payload["required_information"]
    }
    assert "root" in {
        entry["field"] for entry in payload["optional_information"]
    }
    for entries in (
        payload["required_information"],
        payload["optional_information"],
    ):
        assert 1 <= len(entries) <= 6
        for entry in entries:
            assert set(entry) == {"field", "reason"}
            assert all(
                isinstance(value, str) and len(value) <= 256
                for value in entry.values()
            )


@pytest.mark.parametrize(
    ("name", "arguments", "field", "enum_values"),
    [
        ("get_capabilities", {"unexpected": True}, "/unexpected", ()),
        ("get_help_topic", {}, "/topic", ()),
        ("get_help_topic", {"topic": "not-a-topic"}, "/topic", HELP_TOPICS),
        ("get_help_topic", {"topic": ["overview"]}, "/topic", HELP_TOPICS),
        ("get_help_topic", {"topic": "../outside"}, "/topic", HELP_TOPICS),
        ("get_help_topic", {"topic": r"..\outside"}, "/topic", HELP_TOPICS),
        ("get_help_topic", {"topic": "/absolute"}, "/topic", HELP_TOPICS),
        ("get_help_topic", {"topic": r"C:\absolute"}, "/topic", HELP_TOPICS),
        ("get_help_topic", {"topic": "notes.json"}, "/topic", HELP_TOPICS),
        ("get_help_topic", {"topic": "https://example.invalid"}, "/topic", HELP_TOPICS),
        ("get_help_topic", {"topic": "x" * 65_537}, "/topic", HELP_TOPICS),
        ("get_help_topic", {"topic": "overview", "extra": True}, "/extra", ()),
        ("get_request_requirements", {}, "/operation", ()),
        (
            "get_request_requirements",
            {"operation": {"value": "reasoning_run"}},
            "/operation",
            REQUEST_OPERATIONS,
        ),
        (
            "get_request_requirements",
            {"operation": "../outside"},
            "/operation",
            REQUEST_OPERATIONS,
        ),
        (
            "get_request_requirements",
            {"operation": r"C:\absolute"},
            "/operation",
            REQUEST_OPERATIONS,
        ),
        (
            "get_request_requirements",
            {"operation": "x" * 65_537},
            "/operation",
            REQUEST_OPERATIONS,
        ),
        (
            "get_request_requirements",
            {"operation": "reasoning_run", "extra": True},
            "/extra",
            (),
        ),
    ],
)
def test_help_rejects_every_noncompact_or_unsafe_input_before_dispatch(
    name: str,
    arguments: dict,
    field: str,
    enum_values: tuple[str, ...],
):
    result = _call(name, arguments)

    assert result["isError"] is True
    error = result["content"][0]["text"]
    assert f"MCP_INPUT_INVALID: {name}:" in error
    assert field in error
    if enum_values:
        assert "must be one of:" in error
        for value in enum_values:
            assert repr(value) in error


def test_help_dispatch_is_local_and_does_not_access_or_mutate_state(
    tmp_path: Path,
    monkeypatch,
):
    _listed_tools()
    before = _tree_snapshot(tmp_path)

    def forbidden(*_args, **_kwargs):
        pytest.fail("help dispatch attempted a non-local operation")

    monkeypatch.setattr(socket, "create_connection", forbidden)
    monkeypatch.setattr(mcp_server, "_start_run", forbidden)
    for method_name in (
        "exists",
        "iterdir",
        "mkdir",
        "open",
        "read_bytes",
        "read_text",
        "replace",
        "resolve",
        "touch",
        "unlink",
        "write_bytes",
        "write_text",
    ):
        monkeypatch.setattr(Path, method_name, forbidden)

    _payload("get_capabilities", {})
    _payload("get_help_topic", {"topic": "scratchpad"})
    _payload("get_request_requirements", {"operation": "grounded_bridge"})

    assert _tree_snapshot(tmp_path) == before
