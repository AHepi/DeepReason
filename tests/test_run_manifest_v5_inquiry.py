from __future__ import annotations

import hashlib
import sys
from pathlib import Path

import pytest
from pydantic import ValidationError

from deepreason.bridge.retry import WorkflowRetryPolicyV1
from deepreason.capabilities.policy import (
    AttachedEvidencePolicyV1,
    FormalizationCapabilityPolicyV1,
    InquiryCapabilityPolicyV1,
    ResearchCapabilityPolicyV1,
    SimulationCapabilityPolicyV1,
)
from deepreason.config import Config
from deepreason.evidence import (
    AttachedSourceProvenanceV1,
    EvidenceDossierV1,
    RunInputManifestV1,
    RunInputProblemV1,
    bind_run_input,
)
from deepreason.run_manifest import (
    ConjectureContextPolicyV1,
    ContractVersionPolicyV1,
    ContractVersionPolicyV2,
    ControlPlanePolicyV2,
    RunManifestError,
    SchoolExecutionPolicyV1,
    ToolchainEntry,
    bind_run_manifest,
    compile_run_manifest,
)


STAMP = "2026-07-16T00:00:00Z"


def _control() -> ControlPlanePolicyV2:
    return ControlPlanePolicyV2(
        school_execution=SchoolExecutionPolicyV1(
            mode="conditioning_only",
            bindings=(),
            allow_shared=True,
            require_distinct_models=False,
            require_distinct_families=False,
        ),
        conjecture_context=ConjectureContextPolicyV1(
            mode="disabled",
            initial_max_blocks=0,
            initial_max_guides=0,
            max_context_expansion_requests=0,
            max_extra_blocks=0,
            permitted_retrieval_channels=(),
            coverage_slot_mandatory=False,
            exploration_slot_mandatory=False,
        ),
        workflow_retry=WorkflowRetryPolicyV1(),
        contract_versions=ContractVersionPolicyV2(),
    )


def _config() -> Config:
    return Config(
        roles={
            "conjecturer": {
                "endpoint_id": "offline-v5",
                "endpoint": "mock://offline-v5",
                "model": "offline-model",
                "provider": "mock",
                "family": "offline",
            }
        }
    )


def _empty_input(root):
    provenance = AttachedSourceProvenanceV1(
        supplied_by="offline fixture",
        acquisition_method="pre-freeze construction",
    )
    dossier = EvidenceDossierV1.create(
        problem_ref="pi-v5",
        sources=(),
        total_byte_count=0,
        creation_provenance=provenance,
    )
    run_input = RunInputManifestV1.create(
        problem=RunInputProblemV1(id="pi-v5", description="v5 fixture"),
        evidence_dossier_digest=dossier.dossier_digest,
    )
    bind_run_input(run_input, dossier, root)
    return run_input


def _compile(run_input_digest, *, capabilities=None, toolchains=()):
    return compile_run_manifest(
        _config(),
        schema_version=5,
        workload_profile="text",
        rubric_policy="forbid",
        compiled_at=STAMP,
        control_plane_policy=_control(),
        inquiry_capability_policy=capabilities or InquiryCapabilityPolicyV1(),
        run_input_digest=run_input_digest,
        toolchains=toolchains,
    )


def test_contract_v1_cannot_select_v5_or_control_event_v2():
    with pytest.raises(ValidationError):
        ContractVersionPolicyV1(
            bridge_ledger_wire_contract="bridge.ledger.v2",
            conjecturer_turn_contract="conjecturer.turn.v5",
            control_event_schema="control.event.v2",
        )


def test_v5_requires_run_input_digest_before_route_resolution():
    with pytest.raises(RunManifestError, match="RUN_INPUT_DIGEST_REQUIRED"):
        compile_run_manifest(
            _config(),
            schema_version=5,
            workload_profile="text",
            rubric_policy="forbid",
            compiled_at=STAMP,
            control_plane_policy=_control(),
        )


def test_v5_manifest_binds_only_after_matching_run_input(tmp_path):
    root = tmp_path / "run"
    manifest = _compile("a" * 64)
    with pytest.raises(RunManifestError, match="RUN_INPUT_REQUIRED"):
        bind_run_manifest(manifest, root)
    assert not (root / "run-manifest.json").exists()

    run_input = _empty_input(root)
    matching = _compile(run_input.run_input_digest)
    bind_run_manifest(matching, root)
    assert matching.control_plane_policy.controller_version == "workflow.controller.v2"
    assert matching.control_plane_policy.workflow_profile == "inquiry.active.v1"
    assert matching.control_plane_policy.contract_versions.control_event_schema == "control.event.v2"
    dumped = matching.model_dump(mode="json", by_alias=True)
    assert "simulation_capability_policy" not in dumped
    assert "frozen_evidence_policy" not in dumped


def test_simulation_runner_profile_must_match_exact_frozen_toolchain(tmp_path):
    run_input = _empty_input(tmp_path / "input")
    version = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
    toolchain = ToolchainEntry(
        id="python@offline",
        runner="local",
        executable=str(Path(sys.executable).resolve()),
        version_output_sha256=hashlib.sha256(version.encode()).hexdigest(),
        network=False,
    )
    simulation = SimulationCapabilityPolicyV1(
        enabled=True,
        runner_profile="simulation.container.v1",
        python_toolchain_identity=toolchain.id,
        maximum_simulation_requests=1,
        maximum_simulation_executions=1,
        maximum_proposals_per_turn=1,
        maximum_generated_code_bytes=4_096,
        maximum_input_bytes=4_096,
        maximum_output_bytes=4_096,
        maximum_wall_ms=1_000,
        maximum_memory_bytes=64 * 1024 * 1024,
        maximum_steps=1_000,
        maximum_samples=1,
        fixed_seed_set=(7,),
        maximum_follow_up_reasoning_turns=1,
    )
    topology = InquiryCapabilityPolicyV1(simulation=simulation)
    with pytest.raises(ValueError, match="V5_SIMULATION_TOOLCHAIN_UNSAFE"):
        _compile(
            run_input.run_input_digest,
            capabilities=topology,
            toolchains=(toolchain,),
        )


@pytest.mark.parametrize(
    "capabilities",
    [
        InquiryCapabilityPolicyV1(
            formalization=FormalizationCapabilityPolicyV1(
                enabled=True,
                lean_toolchain_identity="lean@pinned",
                maximum_executions=1,
            )
        ),
        InquiryCapabilityPolicyV1(
            research=ResearchCapabilityPolicyV1(
                enabled=True,
                backend_identity="search@future",
                maximum_requests=1,
                maximum_sources=1,
            )
        ),
    ],
)
def test_tranche_a_rejects_unimplemented_capabilities(capabilities, tmp_path):
    run_input = _empty_input(tmp_path / "input")
    with pytest.raises(ValueError, match="UNAVAILABLE"):
        _compile(run_input.run_input_digest, capabilities=capabilities)


def test_attached_evidence_policy_has_finite_bounds():
    with pytest.raises(ValidationError):
        AttachedEvidencePolicyV1(enabled=True)
