from deepreason.v6_policy import (
    POLICY_PRESET_ID,
    conservative_control_plane_policy_v3,
    conservative_policy_digest,
)


def test_repository_owned_policy_is_closed_and_conservative():
    policy = conservative_control_plane_policy_v3()

    assert POLICY_PRESET_ID == "deepreason.v6.conservative.v1"
    assert policy.controller_version == "workflow.controller.v3"
    assert policy.mode == "active_inquiry"
    assert policy.school_execution.mode == "conditioning_only"
    assert policy.school_execution.bindings == ()
    assert policy.school_execution.allow_shared is True
    assert policy.conjecture_context.mode == "disabled"
    assert policy.workflow_retry.max_workflow_retries == 0
    assert policy.scratch_authoring.enabled is False
    assert conservative_policy_digest() == conservative_policy_digest()
    assert len(conservative_policy_digest()) == 64


def test_policy_factory_returns_equal_independent_frozen_models():
    first = conservative_control_plane_policy_v3()
    second = conservative_control_plane_policy_v3()

    assert first == second
    assert first is not second
