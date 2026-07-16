"""D0 shared application boundary for CLI and MCP grounded bridges."""

from __future__ import annotations

import inspect
import json
from pathlib import Path
from types import SimpleNamespace

import pytest
from pydantic import ValidationError

from deepreason import mcp_scratch_bridge as mcp
from deepreason.application import bridge as bridge_application
from deepreason.application.bridge import (
    GROUNDED_BRIDGE_SERVICE,
    GroundedBridgeBuildIntentV1,
    GroundedBridgeStartResultV1,
)
from deepreason.bridge.events import BridgeAction
from deepreason.bridge.retry import WorkflowRetryPolicyV1
from deepreason.cli import bridge as bridge_cli
from deepreason.config import Config
from deepreason.harness import Harness
from deepreason.llm.adapter import LLMAdapter
from deepreason.llm.endpoints import MockEndpoint
from deepreason.llm.firewall import leases_from_manifest
from deepreason.locking import operator_locks
from deepreason.ontology import Problem, ProblemProvenance
from deepreason.run_manifest import (
    ConjectureContextPolicyV1,
    ContractVersionPolicyV1,
    ControlPlanePolicyV1,
    SchoolExecutionPolicyV1,
    bind_run_manifest,
    compile_run_manifest,
)


STAMP = "2026-07-16T00:00:00Z"


def _route() -> dict:
    return {
        "endpoint_id": "application-bridge-fixture",
        "endpoint": "https://models.invalid/v1",
        "model": "fixture-31b",
        "provider": "fixture",
        "family": "fixture",
    }


def _control_policy(*, schema_version: int = 4) -> ControlPlanePolicyV1:
    return ControlPlanePolicyV1(
        controller_version="workflow.controller.v1",
        mode="active_conjecture",
        workflow_profile="conjecture.active.v1",
        school_execution=SchoolExecutionPolicyV1(
            mode="conditioning_only",
            bindings=(),
            allow_shared=True,
            require_distinct_models=False,
            require_distinct_families=False,
        ),
        conjecture_context=ConjectureContextPolicyV1(
            mode="harness_plus_model_request",
            initial_max_blocks=8,
            initial_max_guides=2,
            max_context_expansion_requests=1,
            max_extra_blocks=4,
            permitted_retrieval_channels=("focus", "exploratory", "coverage"),
            coverage_slot_mandatory=True,
            exploration_slot_mandatory=True,
        ),
        workflow_retry=WorkflowRetryPolicyV1(),
        contract_versions=ContractVersionPolicyV1(
            bridge_ledger_wire_contract="bridge.ledger.v2",
            conjecturer_turn_contract=(
                "conjecturer.turn.v5"
                if schema_version == 5
                else "conjecturer.turn.v4"
            ),
            control_event_schema="control.event.v1",
        ),
        capability_profile="conjecture-control.v1",
    )


def _manifest(*, schema_version: int = 3):
    return compile_run_manifest(
        Config(
            scratchpad={"enabled": True},
            bridge={
                "mode": "grounded_two_stage",
                "grounding_review": False,
                "max_schema_repair_attempts": 0,
                "max_grounding_repair_attempts": 0,
            },
            roles={
                "conjecturer": _route(),
                "summarizer": _route(),
                "thesis": _route(),
            },
        ),
        schema_version=schema_version,
        workload_profile="text",
        rubric_policy="forbid",
        compiled_at=STAMP,
        control_plane_policy=(
            _control_policy(schema_version=schema_version)
            if schema_version in {4, 5}
            else None
        ),
    )


def _run_root(root, *, schema_version: int = 3):
    harness = Harness(root)
    harness.register_problem(
        Problem(
            id="problem-application-boundary",
            description="What does the bounded record establish?",
            provenance=ProblemProvenance.model_validate({"trigger": "seed", "from": []}),
        )
    )
    bind_run_manifest(_manifest(schema_version=schema_version), root)
    return root


def _adapter(harness: Harness, manifest=None) -> LLMAdapter:
    return LLMAdapter(
        {
            "summarizer": MockEndpoint(
                [
                    json.dumps(
                        {
                            "entries": [
                                {
                                    "entry_key": "CLM_1",
                                    "claim_class": "unknown",
                                    "claim": "The bounded record does not establish an answer.",
                                }
                            ]
                        }
                    )
                ],
                name="https://models.invalid/v1",
                model="fixture-31b",
            ),
            "thesis": MockEndpoint(
                [
                    json.dumps(
                        {
                            "sections": [
                                {
                                    "span_id": "S1",
                                    "text": "The requested answer remains unknown.",
                                    "rendering_mode": "unknown",
                                    "ledger_entry_handles": ["E1"],
                                }
                            ],
                            "resolution": "insufficient_evidence",
                        }
                    )
                ],
                name="https://models.invalid/v1",
                model="fixture-31b",
            ),
        },
        harness.blobs,
        retry_max=0,
        leases=(leases_from_manifest(manifest) if manifest is not None else None),
    )


def _bridge_events(root) -> list[dict]:
    return [
        event.bridge.model_dump(mode="json", by_alias=True, exclude_none=True)
        for event in Harness(root, read_only=True).log.read()
        if event.bridge is not None
    ]


def test_equivalent_cli_and_mcp_intents_emit_equivalent_bridge_control_events(
    tmp_path, monkeypatch, capsys
):
    cli_root = _run_root(tmp_path / "cli")
    mcp_root = _run_root(tmp_path / "mcp")
    monkeypatch.setattr(
        bridge_application,
        "_build_bridge_adapter",
        lambda manifest, harness: _adapter(harness, manifest),
    )

    cli_args = SimpleNamespace(
        root=str(cli_root),
        bridge_command="build",
        problem="problem-application-boundary",
        target="answer",
        run_manifest=None,
        derived_output=None,
        at_seq=None,
        focus_block=[],
        focus_cluster=[],
        limit=25,
        offset=0,
        json=True,
    )
    assert bridge_cli.handle_bridge_command(cli_args) == 0
    capsys.readouterr()

    started = mcp.call_tool(
        "start_bridge",
        {
            "root": str(mcp_root),
            "problem": "problem-application-boundary",
            "target": "answer",
        },
    )
    assert started["state"] == "running"
    worker = mcp._BRIDGE_THREADS[str(mcp_root.resolve())]
    worker.join(timeout=5)
    assert not worker.is_alive()

    assert _bridge_events(cli_root) == _bridge_events(mcp_root)
    assert [event["action"] for event in _bridge_events(cli_root)][-1] == (
        BridgeAction.COMPLETED.value
    )


@pytest.mark.parametrize("schema_version", [4, 5])
def test_shared_bridge_service_accepts_bound_controlled_manifest_and_enacts_ledger_v2(
    tmp_path, monkeypatch, schema_version
):
    root = _run_root(tmp_path / f"v{schema_version}", schema_version=schema_version)
    monkeypatch.setattr(
        bridge_application,
        "_build_bridge_adapter",
        lambda manifest, harness: _adapter(harness, manifest),
    )

    result = GROUNDED_BRIDGE_SERVICE.build(
        GroundedBridgeBuildIntentV1(
            root=str(root),
            problem="problem-application-boundary",
        )
    )

    assert result.exit_code == 0
    assert result.snapshot.terminal.process_status == "success"
    contracts = {
        attempt.contract_id
        for event in Harness(root, read_only=True).log.read()
        if event.llm is not None and event.llm.role == "summarizer"
        for attempt in event.llm.attempt_trace
    }
    assert contracts == {"bridge.claim-ledger.compact.v2"}


def test_bridge_intents_are_closed_and_do_not_expose_control_or_routes():
    payload = {
        "root": "/tmp/run",
        "problem": "problem-id",
        "status": "success",
    }
    with pytest.raises(ValidationError):
        GroundedBridgeBuildIntentV1.model_validate(payload)

    schema = GroundedBridgeBuildIntentV1.model_json_schema()
    encoded = json.dumps(schema, sort_keys=True)
    assert schema["additionalProperties"] is False
    for forbidden in (
        "provider_route",
        "route_selector",
        "raw_event",
        "guard_override",
        "prompt",
    ):
        assert forbidden not in encoded

    assert "adapter_builder" not in inspect.signature(
        GROUNDED_BRIDGE_SERVICE.build
    ).parameters
    assert "adapter_builder" not in inspect.signature(
        GROUNDED_BRIDGE_SERVICE.start
    ).parameters
    assert "executor" not in inspect.signature(
        GROUNDED_BRIDGE_SERVICE.start
    ).parameters


def test_existing_failed_terminal_start_preserves_explicit_null_resolution():
    result = GroundedBridgeStartResultV1(
        state="failed",
        root="/tmp/run",
        manifest_sha256="0" * 64,
        process_status="failure",
        terminal_event_seq=7,
    )

    assert result.presentation_payload()["resolution"] is None


def test_async_terminal_race_error_releases_acquired_operator_lock(
    tmp_path, monkeypatch
):
    root = _run_root(tmp_path / "terminal-race")
    calls = 0

    def terminal_race(_root):
        nonlocal calls
        calls += 1
        if calls == 1:
            return None
        raise ValueError("BRIDGE_RESULT_INVALID: raced terminal is corrupt")

    monkeypatch.setattr(bridge_application, "_existing_terminal", terminal_race)
    intent = GroundedBridgeBuildIntentV1(
        root=str(root),
        problem="problem-application-boundary",
    )
    with pytest.raises(ValueError, match="raced terminal is corrupt"):
        GROUNDED_BRIDGE_SERVICE.start(intent)

    locks = operator_locks(root, owner="post-race-probe", blocking=False)
    locks.release()


@pytest.mark.parametrize(
    "path",
    [
        "src/deepreason/cli/bridge.py",
        "src/deepreason/mcp_scratch_bridge.py",
    ],
)
def test_bridge_clients_do_not_own_workflow_or_persistence(path):
    source = Path(path).read_text(encoding="utf-8")
    for forbidden in (
        "Harness(",
        ".build_bridge(",
        "operator_locks(",
        "bind_run_manifest(",
        "record_bridge_event(",
        "write_running(",
        "write_failure(",
        "build_bridge_adapter",
        "execute_bridge",
    ):
        assert forbidden not in source
