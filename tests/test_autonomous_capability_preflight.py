"""A0 regression for the stopped autonomous-inquiry preflight."""

from __future__ import annotations

from pathlib import Path

import pytest

from deepreason.bridge.retry import WorkflowRetryPolicyV1
from deepreason.capabilities.preflight import (
    AutonomousCapabilityRequirementsV1,
    AutonomousCapabilityTopologyUnavailable,
    preflight_autonomous_capabilities,
)
from deepreason.config import Config
from deepreason.run_manifest import (
    ConjectureContextPolicyV1,
    ContractVersionPolicyV1,
    ControlPlanePolicyV1,
    SchoolExecutionPolicyV1,
    compile_run_manifest,
)


def _v4_manifest():
    control = ControlPlanePolicyV1(
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
        contract_versions=ContractVersionPolicyV1(
            bridge_ledger_wire_contract="bridge.ledger.v2",
            conjecturer_turn_contract="conjecturer.turn.v4",
            control_event_schema="control.event.v1",
        ),
        capability_profile="conjecture-control.v1",
    )
    config = Config(
        N_SCHOOLS=0,
        roles={
            "conjecturer": {
                "endpoint_id": "offline",
                "endpoint": "mock://offline",
                "model": "offline-model",
                "provider": "mock",
                "family": "offline",
            }
        },
    )
    return compile_run_manifest(
        config,
        schema_version=4,
        workload_profile="text",
        rubric_policy="forbid",
        control_plane_policy=control,
        compiled_at="2026-07-16T00:00:00Z",
    )


@pytest.mark.parametrize("required", ["simulation", "research"])
def test_missing_autonomous_topology_fails_before_binding(
    tmp_path: Path, required: str
) -> None:
    root = tmp_path / "must-not-exist"
    requirements = AutonomousCapabilityRequirementsV1(**{required: True})

    with pytest.raises(AutonomousCapabilityTopologyUnavailable) as caught:
        preflight_autonomous_capabilities(_v4_manifest(), requirements)

    assert caught.value.code == "AUTONOMOUS_CAPABILITY_TOPOLOGY_UNAVAILABLE"
    assert caught.value.missing == (required,)
    assert not root.exists()
    assert list(tmp_path.iterdir()) == []


def test_operator_facing_tools_do_not_satisfy_autonomous_requirements() -> None:
    requirements = AutonomousCapabilityRequirementsV1(
        formalization=True,
        code=True,
    )
    with pytest.raises(AutonomousCapabilityTopologyUnavailable) as caught:
        preflight_autonomous_capabilities(_v4_manifest(), requirements)
    assert caught.value.missing == ("formalization", "code")
