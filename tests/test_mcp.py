"""Closed, environment-invariant MCP public contract."""

import hashlib
import json
from pathlib import Path
from types import SimpleNamespace

import pytest

from deepreason import mcp_server


SUPPORTED_TOOLS = {
    "get_readiness",
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
    "get_capabilities",
    "get_help_topic",
    "get_request_requirements",
}
REMOVED_TOOLS = (
    "start_make",
    "make_status",
    "make_result",
    "seed_problem",
    "run_cycles",
    "frontier",
    "theory",
    "narrate",
    "why",
    "eval_report",
    "docket",
    "appellate_rule",
    "research_docket",
    "submit_evidence",
    "report_research_failure",
)


def _call(name: str, arguments) -> dict:
    return mcp_server.handle(
        {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "tools/call",
            "params": {"name": name, "arguments": arguments},
        }
    )["result"]


def _listed_names() -> set[str]:
    response = mcp_server.handle(
        {"jsonrpc": "2.0", "id": 1, "method": "tools/list"}
    )
    return {tool["name"] for tool in response["result"]["tools"]}


def _tree_digest(root: Path) -> str:
    digest = hashlib.sha256()
    for path in sorted(item for item in root.rglob("*") if item.is_file()):
        digest.update(path.relative_to(root).as_posix().encode())
        digest.update(path.read_bytes())
    return digest.hexdigest()


def test_initialize_and_tools_list_are_truthful_and_exact(monkeypatch):
    initialized = mcp_server.handle(
        {"jsonrpc": "2.0", "id": 0, "method": "initialize", "params": {}}
    )
    assert initialized["result"]["serverInfo"]["name"] == "deepreason"
    assert "call get_readiness" in initialized["result"]["instructions"]
    assert "normal question" in initialized["result"]["instructions"]
    assert (
        mcp_server.handle(
            {"jsonrpc": "2.0", "method": "notifications/initialized"}
        )
        is None
    )

    assert _listed_names() == SUPPORTED_TOOLS
    monkeypatch.setenv("DEEPREASON_ENABLE_LEGACY_MCP", "1")
    assert _listed_names() == SUPPORTED_TOOLS


@pytest.mark.parametrize("name", REMOVED_TOOLS)
def test_removed_mcp_tools_are_not_exposed_and_cannot_mutate(name, tmp_path):
    root = tmp_path / name
    result = _call(
        name,
        {
            "root": str(root),
            "config": "provider.yaml",
            "cycles": 1,
            "problem": {"id": "pi", "description": "historical"},
            "run_manifest_ref": "historical.json",
            "budget": {"cycles": 1, "token_budget": 1},
        },
    )

    assert result["isError"] is True
    assert "MCP_TOOL_NOT_EXPOSED" in result["content"][0]["text"]
    assert not root.exists()


def test_unknown_tool_and_method():
    result = _call("set_status", {"id": "a", "status": "accepted"})
    assert result["isError"] is True
    error = mcp_server.handle(
        {"jsonrpc": "2.0", "id": 9, "method": "no/such"}
    )
    assert error["error"]["code"] == -32601
    assert (
        mcp_server.handle(
            {"jsonrpc": "2.0", "method": "no/such/notification"}
        )
        is None
    )


@pytest.mark.parametrize(
    "field",
    ("provider", "route", "policy", "credential", "api_key", "api_key_env"),
)
def test_run_tools_reject_provider_and_credential_authority_fields(field):
    result = _call("run_status", {field: "must-not-be-accepted"})

    assert result["isError"] is True
    text = result["content"][0]["text"]
    assert "MCP_INPUT_INVALID" in text
    assert "must-not-be-accepted" not in text


def test_runtime_enforces_closed_bounded_tool_schemas():
    oversized = _call("scratch_map", {"root": "x" * 4_097})
    assert oversized["isError"] is True
    assert "MCP_INPUT_INVALID" in oversized["content"][0]["text"]

    non_object = _call("bridge_status", [])
    assert non_object["isError"] is True
    assert "arguments must be an object" in non_object["content"][0]["text"]

    hostile_name = "x" * 10_000
    invalid_name = _call(hostile_name, {})
    assert invalid_name["isError"] is True
    text = invalid_name["content"][0]["text"]
    assert "MCP_TOOL_NOT_EXPOSED" in text
    assert hostile_name not in text

    oversized_token = mcp_server.handle(
        {
            "jsonrpc": "2.0",
            "id": 3,
            "method": "tools/call",
            "params": {
                "name": "bridge_status",
                "arguments": {},
                "_meta": {"progressToken": "p" * 257},
            },
        }
    )["result"]
    assert oversized_token["isError"] is True
    assert "progressToken is invalid" in oversized_token["content"][0]["text"]


def test_no_removed_make_state_is_created_by_mcp(tmp_path: Path):
    root = tmp_path / "run"
    for name in ("start_make", "make_status", "make_result", "run_cycles"):
        assert _call(name, {"root": str(root)})["isError"] is True
    assert not root.exists()


@pytest.mark.parametrize("version", range(1, 6))
@pytest.mark.parametrize(
    "name",
    (
        "start_run",
        "run_status",
        "scratch_map",
        "start_bridge",
        "bridge_status",
    ),
)
def test_public_mcp_rejects_caller_owned_historical_roots_before_interpretation(
    tmp_path, monkeypatch, version, name
):
    import deepreason.evidence as evidence
    from deepreason import mcp_scratch_bridge

    root = tmp_path / f"v{version}-{name}"
    root.mkdir()
    secret = f"NESTED_HISTORICAL_SECRET_{version}_{name}"
    (root / "run-manifest.json").write_text(
        json.dumps(
            {
                "schema_version": version,
                "historical_nested_payload": {
                    "credential": secret,
                    "migration": "must-not-run",
                },
            }
        ),
        encoding="utf-8",
    )
    (root / "run-input.json").write_text(secret, encoding="utf-8")
    (root / "evidence-dossier.json").write_text(secret, encoding="utf-8")
    before = _tree_digest(root)

    def forbidden(*_args, **_kwargs):
        raise AssertionError("historical payload reached a post-manifest seam")

    monkeypatch.setattr(evidence, "load_run_input", forbidden)
    monkeypatch.setattr(mcp_server.TEXT_RUN_SERVICE, "start", forbidden)
    monkeypatch.setattr(mcp_server.TEXT_RUN_SERVICE, "inspect", forbidden)
    monkeypatch.setattr(
        mcp_scratch_bridge.SCRATCH_QUERY_SERVICE, "execute", forbidden
    )
    monkeypatch.setattr(
        mcp_scratch_bridge.GROUNDED_BRIDGE_SERVICE, "start", forbidden
    )
    monkeypatch.setattr(
        mcp_scratch_bridge.GROUNDED_BRIDGE_SERVICE, "status", forbidden
    )

    arguments = {"root": str(root)}
    if name == "start_run":
        arguments.update(
            {
                "workload": "text",
                "problem": {"description": "must stop before interpretation"},
                "run_manifest_ref": str(root / "run-manifest.json"),
                "budget": {"cycles": 1, "token_budget": 1},
            }
        )
    elif name == "start_bridge":
        arguments["problem"] = "problem-must-not-resolve"

    result = _call(name, arguments)

    assert result["isError"] is True
    text = result["content"][0]["text"]
    assert "MCP_INPUT_INVALID" in text
    assert secret not in text
    assert _tree_digest(root) == before


@pytest.mark.parametrize(
    "name",
    (
        "start_run",
        "run_status",
        "scratch_map",
        "start_bridge",
        "bridge_status",
    ),
)
def test_every_mcp_family_rejects_caller_owned_missing_root_without_creation(
    tmp_path, name
):
    root = tmp_path / name

    arguments = {"root": str(root)}
    if name == "start_run":
        arguments.update(
            {
                "workload": "text",
                "problem": {"description": "must stop before preparation"},
                "run_manifest_ref": str(root / "run-manifest.json"),
                "budget": {"cycles": 1, "token_budget": 1},
            }
        )
    elif name == "start_bridge":
        arguments["problem"] = "problem-must-not-resolve"

    result = _call(name, arguments)

    assert result["isError"] is True
    assert "MCP_INPUT_INVALID" in result["content"][0]["text"]
    assert not root.exists()


def test_missing_credential_error_redacts_the_configured_reference(
    tmp_path, monkeypatch
):
    from deepreason.provider_profile import ProviderProfileV1, write_provider_profile

    state = tmp_path / "state"
    monkeypatch.setenv("DEEPREASON_HOME", str(state))
    secret_reference = "DEEPREASON_PRIVATE_PROVIDER_REFERENCE"
    monkeypatch.delenv(secret_reference, raising=False)
    profile = ProviderProfileV1.create(
        provider="fixture",
        endpoint="https://example.invalid/v1",
        model_id="model-a",
        family="family-a",
        context_window_tokens=8192,
        maximum_completion_tokens=1024,
        credential_env=secret_reference,
    )
    write_provider_profile(profile, state / "provider.yaml")
    result = _call("get_readiness", {})
    assert result["isError"] is False
    text = result["content"][0]["text"]
    assert '"credential_present":false' in text
    assert secret_reference not in text
