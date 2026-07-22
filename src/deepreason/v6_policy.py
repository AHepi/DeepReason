"""The single repository-owned conservative RunManifest-v6 control preset."""

from __future__ import annotations

from deepreason.bridge.retry import WorkflowRetryPolicyV1
from deepreason.canonical import canonical_json, sha256_hex
from deepreason.run_manifest import (
    ConjectureContextPolicyV1,
    ContractVersionPolicyV3,
    ControlPlanePolicyV3,
    ScratchAuthoringPolicyV1,
    SchoolExecutionPolicyV1,
)


POLICY_PRESET_ID = "deepreason.v6.conservative.v1"


def conservative_control_plane_policy_v3() -> ControlPlanePolicyV3:
    """Return the closed baseline: no retries, model context requests, or scratch writes."""

    return ControlPlanePolicyV3(
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
        contract_versions=ContractVersionPolicyV3(),
        scratch_authoring=ScratchAuthoringPolicyV1(),
    )


def conservative_policy_digest() -> str:
    policy = conservative_control_plane_policy_v3()
    return sha256_hex(
        b"deepreason.v6-policy-preset.v1\x00"
        + canonical_json(
            {
                "preset": POLICY_PRESET_ID,
                "control_plane_policy": policy.model_dump(
                    mode="json", by_alias=True, exclude_none=True
                ),
            }
        )
    )


__all__ = [
    "POLICY_PRESET_ID",
    "conservative_control_plane_policy_v3",
    "conservative_policy_digest",
]
