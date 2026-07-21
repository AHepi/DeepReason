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
from deepreason.capabilities.policy import InquiryCapabilityPolicyV1
from deepreason.evidence import (
    AttachedSourceProvenanceV1,
    EvidenceDossierV1,
    RunInputManifestV1,
    RunInputProblemV1,
    bind_run_input,
)
from deepreason.harness import Harness
from deepreason.llm.adapter import LLMAdapter
from deepreason.llm.endpoints import MockEndpoint
from deepreason.llm.firewall import leases_from_manifest
from deepreason.locking import operator_locks
from deepreason.ontology import Problem, ProblemProvenance
from deepreason.run_manifest import (
    ConjectureContextPolicyV1,
    ContractVersionPolicyV1,
    ContractVersionPolicyV2,
    ControlPlanePolicyV1,
    ControlPlanePolicyV2,
    SchoolExecutionPolicyV1,
    bind_run_manifest,
    compile_run_manifest,
)
from deepreason.runtime.launch_policy import V6_LAUNCH_DISABLE_ENV


STAMP = "2026-07-16T00:00:00Z"


def _route() -> dict:
    return {
        "endpoint_id": "application-bridge-fixture",
        "endpoint": "https://models.invalid/v1",
        "model": "fixture-31b",
        "provider": "fixture",
        "family": "fixture",
    }


def _control_policy(*, schema_version: int = 4):
    common = dict(
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
    )
    if schema_version == 5:
        return ControlPlanePolicyV2(
            **common,
            contract_versions=ContractVersionPolicyV2(),
        )
    return ControlPlanePolicyV1(
        controller_version="workflow.controller.v1",
        mode="active_conjecture",
        workflow_profile="conjecture.active.v1",
        **common,
        contract_versions=ContractVersionPolicyV1(
            bridge_ledger_wire_contract="bridge.ledger.v2",
            conjecturer_turn_contract="conjecturer.turn.v4",
            control_event_schema="control.event.v1",
        ),
        capability_profile="conjecture-control.v1",
    )


def _manifest(*, schema_version: int = 3, run_input_digest: str | None = None):
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
        inquiry_capability_policy=(
            InquiryCapabilityPolicyV1() if schema_version == 5 else None
        ),
        run_input_digest=(run_input_digest if schema_version == 5 else None),
    )


def _run_root(root, *, schema_version: int = 3):
    run_input = None
    if schema_version == 5:
        provenance = AttachedSourceProvenanceV1(
            supplied_by="offline bridge fixture",
            acquisition_method="pre-freeze construction",
        )
        dossier = EvidenceDossierV1.create(
            problem_ref="problem-application-boundary",
            sources=(),
            total_byte_count=0,
            creation_provenance=provenance,
        )
        run_input = RunInputManifestV1.create(
            problem=RunInputProblemV1(
                id="problem-application-boundary",
                description="What does the bounded record establish?",
            ),
            evidence_dossier_digest=dossier.dossier_digest,
        )
        bind_run_input(run_input, dossier, root)
    bind_run_manifest(
        _manifest(
            schema_version=schema_version,
            run_input_digest=(run_input.run_input_digest if run_input else None),
        ),
        root,
    )
    harness = Harness(root)
    harness.register_problem(
        Problem(
            id="problem-application-boundary",
            description="What does the bounded record establish?",
            provenance=ProblemProvenance.model_validate({"trigger": "seed", "from": []}),
        )
    )
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


def _forbid(label: str):
    def blocked(*_args, **_kwargs):
        pytest.fail(f"{label} must not run after a disabled v6 launch")

    return blocked


def test_equivalent_cli_and_mcp_intents_emit_equivalent_bridge_control_events(
    tmp_path, monkeypatch, capsys
):
    cli_root = _run_root(tmp_path / "cli")
    mcp_root = _run_root(tmp_path / "mcp")
    monkeypatch.setattr(
        bridge_application,
        "_build_bridge_adapter",
        lambda manifest, harness, **_kwargs: _adapter(harness, manifest),
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
        lambda manifest, harness, **_kwargs: _adapter(harness, manifest),
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


@pytest.mark.parametrize("state", ["failed", "cancelled"])
def test_canonical_bridge_rejects_noncompleted_reasoning_before_adapter(
    tmp_path, monkeypatch, state
):
    root = _run_root(tmp_path / state)
    (root / "run-result.json").write_text(
        json.dumps(
            {
                "schema": "deepreason-run-result-v1",
                "state": state,
                "workload": "text",
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr(
        bridge_application,
        "_build_bridge_adapter",
        lambda *_args: pytest.fail("terminal gate must precede adapter construction"),
    )

    with pytest.raises(ValueError, match="BRIDGE_REASONING_NOT_COMPLETED"):
        GROUNDED_BRIDGE_SERVICE.build(
            GroundedBridgeBuildIntentV1(
                root=str(root), problem="problem-application-boundary"
            )
        )

    assert _bridge_events(root) == []


def test_v6_canonical_bridge_requires_run_result_but_legacy_missing_is_allowed(
    tmp_path,
):
    bridge_application.preflight_canonical_bridge(
        tmp_path, SimpleNamespace(schema_version=5)
    )
    with pytest.raises(ValueError, match="BRIDGE_RUN_RESULT_REQUIRED"):
        bridge_application.preflight_canonical_bridge(
            tmp_path, SimpleNamespace(schema_version=6)
        )


def test_run_result_v2_can_deny_canonical_bridge(tmp_path):
    (tmp_path / "run-result.json").write_text(
        json.dumps(
            {
                "schema": "deepreason-run-result-v2",
                "state": "completed",
                "workload": "text",
                "verification": {
                    "schema": "verification.summary.v2",
                    "valid": False,
                    "integrity_valid": False,
                    "security_valid": True,
                    "completion_satisfied": True,
                    "epistemic_checks_passed": True,
                    "operational_checks_passed": True,
                    "finding_counts": {
                        "integrity": 1,
                        "security": 0,
                        "completion": 0,
                        "epistemic": 0,
                        "operational": 0,
                    },
                },
                "completion_status": "satisfied",
                "canonical_bridge_eligible": False,
            }
        ),
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="BRIDGE_RUN_NOT_ELIGIBLE"):
        bridge_application.preflight_canonical_bridge(
            tmp_path, SimpleNamespace(schema_version=6)
        )


def test_diagnostic_after_failure_requires_separate_derived_output():
    with pytest.raises(ValidationError, match="BRIDGE_DIAGNOSTIC_DERIVED_REQUIRED"):
        GroundedBridgeBuildIntentV1(
            root="/run",
            problem="problem-id",
            diagnostic_after_failure=True,
        )


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
def _eligible_v6_run_result() -> dict:
    return {
        "schema": "deepreason-run-result-v2",
        "state": "completed",
        "workload": "text",
        "verification": {
            "schema": "verification.summary.v2",
            "valid": True,
            "integrity_valid": True,
            "security_valid": True,
            "completion_satisfied": True,
            "epistemic_checks_passed": True,
            "operational_checks_passed": True,
            "finding_counts": {
                "integrity": 0,
                "security": 0,
                "completion": 0,
                "epistemic": 0,
                "operational": 0,
            },
        },
        "completion_status": "satisfied",
        "canonical_bridge_eligible": True,
    }


def test_v6_canonical_bridge_rejects_legacy_result_before_adapter(
    tmp_path, monkeypatch
):
    root = tmp_path / "v6-legacy-result"
    root.mkdir()
    (root / "run-result.json").write_text(
        json.dumps(
            {
                "schema": "deepreason-run-result-v1",
                "state": "completed",
                "workload": "text",
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr(
        bridge_application,
        "load_bound_manifest",
        lambda *_args, **_kwargs: SimpleNamespace(schema_version=6),
    )
    monkeypatch.setattr(
        bridge_application,
        "_preflight_bridge_caller_policy",
        lambda *_args, **_kwargs: None,
    )
    monkeypatch.setattr(
        bridge_application,
        "_build_bridge_adapter",
        lambda *_args: pytest.fail("result-version gate must precede adapter construction"),
    )

    with pytest.raises(ValueError, match="BRIDGE_RUN_RESULT_V2_REQUIRED"):
        GROUNDED_BRIDGE_SERVICE.build(
            GroundedBridgeBuildIntentV1(root=str(root), problem="problem-v6")
        )


def test_v6_live_verification_rejects_post_terminal_corruption_before_adapter(
    tmp_path, monkeypatch
):
    from deepreason import invariants
    from deepreason.verification import report as verification_report

    root = tmp_path / "v6-post-terminal-corruption"
    root.mkdir()
    (root / "run-result.json").write_text(
        json.dumps(_eligible_v6_run_result()),
        encoding="utf-8",
    )
    monkeypatch.setattr(
        bridge_application,
        "load_bound_manifest",
        lambda *_args, **_kwargs: SimpleNamespace(schema_version=6),
    )
    monkeypatch.setattr(
        bridge_application,
        "_preflight_bridge_caller_policy",
        lambda *_args, **_kwargs: None,
    )
    monkeypatch.setattr(
        bridge_application,
        "_build_bridge_adapter",
        lambda *_args: pytest.fail("live authority gate must precede adapter construction"),
    )
    monkeypatch.setattr(
        invariants,
        "verify_root",
        lambda *_args, **_kwargs: {
            "violations": [
                {
                    "check": "event-log",
                    "detail": "post-terminal event history no longer matches authority",
                }
            ],
            "stats": {},
        },
    )
    monkeypatch.setattr(
        verification_report,
        "_manifest_schema_version",
        lambda _root: 6,
    )

    with pytest.raises(ValueError, match="BRIDGE_ROOT_AUTHORITY_INVALID"):
        GROUNDED_BRIDGE_SERVICE.build(
            GroundedBridgeBuildIntentV1(root=str(root), problem="problem-v6")
        )


def test_disabled_v6_canonical_bridge_stops_before_preflight_or_mutation(
    tmp_path, monkeypatch
):
    root = tmp_path / "disabled-v6-canonical"
    root.mkdir()
    manifest = SimpleNamespace(schema_version=6)
    monkeypatch.setenv(V6_LAUNCH_DISABLE_ENV, "1")
    monkeypatch.setattr(
        bridge_application,
        "load_bound_manifest",
        lambda *_args, **_kwargs: manifest,
    )
    monkeypatch.setattr(
        bridge_application,
        "_preflight_bridge_caller_policy",
        lambda *_args, **_kwargs: None,
    )
    monkeypatch.setattr(
        bridge_application,
        "preflight_canonical_bridge",
        _forbid("canonical preflight"),
    )
    monkeypatch.setattr(
        bridge_application,
        "operator_locks",
        _forbid("canonical operator lock"),
    )
    monkeypatch.setattr(
        "deepreason.run_manifest.bind_run_manifest",
        _forbid("canonical manifest binding"),
    )
    monkeypatch.setattr(
        bridge_application,
        "_build_bridge_adapter",
        _forbid("canonical adapter construction"),
    )

    with pytest.raises(ValueError, match="V6_LAUNCH_DISABLED"):
        GROUNDED_BRIDGE_SERVICE.build(
            GroundedBridgeBuildIntentV1(root=str(root), problem="problem-v6")
        )

    assert list(root.iterdir()) == []


def test_disabled_v6_async_bridge_stops_before_worker_or_mutation(
    tmp_path, monkeypatch
):
    root = tmp_path / "disabled-v6-async"
    root.mkdir()
    manifest = SimpleNamespace(schema_version=6)
    service = bridge_application.GroundedBridgeApplicationService(
        registry=bridge_application.GroundedBridgeWorkerRegistry()
    )
    monkeypatch.setenv(V6_LAUNCH_DISABLE_ENV, "1")
    monkeypatch.setattr(
        bridge_application,
        "load_bound_manifest",
        lambda *_args, **_kwargs: manifest,
    )
    monkeypatch.setattr(
        bridge_application,
        "_preflight_bridge_caller_policy",
        lambda *_args, **_kwargs: None,
    )
    monkeypatch.setattr(
        bridge_application,
        "preflight_canonical_bridge",
        _forbid("asynchronous preflight"),
    )
    monkeypatch.setattr(
        bridge_application,
        "operator_locks",
        _forbid("asynchronous operator lock"),
    )
    monkeypatch.setattr(
        bridge_application,
        "_prepare_bridge",
        _forbid("asynchronous preparation"),
    )

    with pytest.raises(ValueError, match="V6_LAUNCH_DISABLED"):
        service.start(
            GroundedBridgeBuildIntentV1(root=str(root), problem="problem-v6")
        )

    assert service.registry.threads == {}
    assert list(root.iterdir()) == []


def test_disabled_v6_derived_bridge_stops_before_destination_reservation(
    tmp_path, monkeypatch
):
    import deepreason.bridge.derived as derived_bridge

    source = _run_root(tmp_path / "disabled-v6-derived-source")
    destination = tmp_path / "disabled-v6-derived-destination"
    manifest = SimpleNamespace(schema_version=6)
    monkeypatch.setenv(V6_LAUNCH_DISABLE_ENV, "1")
    monkeypatch.setattr(
        bridge_application,
        "load_bound_manifest",
        lambda *_args, **_kwargs: manifest,
    )
    monkeypatch.setattr(
        bridge_application,
        "_preflight_bridge_caller_policy",
        lambda *_args, **_kwargs: None,
    )
    monkeypatch.setattr(
        derived_bridge,
        "reserve_derived_destination",
        _forbid("derived destination reservation"),
    )
    monkeypatch.setattr(
        bridge_application,
        "operator_locks",
        _forbid("derived operator lock"),
    )
    monkeypatch.setattr(
        "deepreason.run_manifest.bind_run_manifest",
        _forbid("derived manifest binding"),
    )
    monkeypatch.setattr(
        bridge_application,
        "_build_bridge_adapter",
        _forbid("derived adapter construction"),
    )

    with pytest.raises(ValueError, match="V6_LAUNCH_DISABLED"):
        GROUNDED_BRIDGE_SERVICE.build(
            GroundedBridgeBuildIntentV1(
                root=str(source),
                problem="problem-application-boundary",
                run_manifest_ref=str(tmp_path / "v6-manifest.json"),
                derived_output=str(destination),
                at_seq=0,
            )
        )

    assert not destination.exists()
