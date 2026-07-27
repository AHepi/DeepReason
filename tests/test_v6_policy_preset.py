import sys
from pathlib import Path

from deepreason.canonical import canonical_json, sha256_hex
from deepreason.v6_policy import (
    POLICY_PRESET_ID,
    PUBLIC_SCHOOL_COUNT,
    PUBLIC_SIMULATION_TOOLCHAIN_ID,
    conservative_control_plane_policy_v3,
    conservative_policy_digest,
    engaged_bridge_source,
    engaged_control_plane_policy_v3,
    engaged_criticism_policy,
    engaged_inquiry_capability_policy,
    engaged_local_simulation_toolchain,
    engaged_policy_digest,
    engaged_scratchpad_source,
    engaged_simulation_policy,
)


def test_public_policy_preset_is_the_engaged_v1_version():
    assert POLICY_PRESET_ID == "deepreason.v6.engaged.v1"


def test_engaged_policy_enables_bounded_scratch_and_context():
    policy = engaged_control_plane_policy_v3()

    assert policy.controller_version == "workflow.controller.v3"
    assert policy.mode == "active_inquiry"
    # Schools stay conditioning-only; the run seeds them without routing.
    assert policy.school_execution.mode == "conditioning_only"
    assert policy.school_execution.bindings == ()
    assert policy.school_execution.allow_shared is True
    # Bounded advisory context: small, finite, and model-requestable.
    context = policy.conjecture_context
    assert context.mode == "harness_plus_model_request"
    assert context.initial_max_blocks == 8
    assert context.initial_max_guides == 2
    assert context.max_context_expansion_requests == 2
    assert context.max_extra_blocks == 8
    assert context.permitted_retrieval_channels == (
        "focus",
        "link",
        "keyword",
        "semantic",
        "recent",
    )
    assert context.coverage_slot_mandatory is False
    assert context.exploration_slot_mandatory is False
    # No workflow retries; the frozen v6 contract set.
    assert policy.workflow_retry.max_workflow_retries == 0
    # Scratch authoring ON with modest finite per-turn allowances.
    scratch = policy.scratch_authoring
    assert scratch.enabled is True
    assert scratch.maximum_new_blocks_per_turn == 4
    assert scratch.maximum_revisions_per_turn == 4
    assert scratch.maximum_links_per_turn == 4
    assert scratch.maximum_unresolved_questions_per_turn == 4
    assert scratch.maximum_cluster_suggestions_per_turn == 4
    assert scratch.maximum_total_bytes == 128 * 1024
    assert engaged_scratchpad_source() == {"enabled": True}
    assert engaged_policy_digest() == engaged_policy_digest()
    assert len(engaged_policy_digest()) == 64


def test_engaged_bridge_source_enables_the_review_free_grounded_bridge():
    source = engaged_bridge_source()

    # The audited review-free single-route shape: Stage A on the frozen
    # summarizer route, Stage B on the frozen thesis route, one schema
    # repair, no grounding-review stream, four bounded output sections.
    assert source == {
        "mode": "grounded_two_stage",
        "grounding_review": False,
        "max_schema_repair_attempts": 1,
        "max_grounding_repair_attempts": 0,
        "output_section_limit": 4,
    }


def test_engaged_policy_digest_reflects_the_bridge_source():
    policy = engaged_control_plane_policy_v3()
    criticism = engaged_criticism_policy("preset-endpoint-template")
    without_bridge = sha256_hex(
        b"deepreason.v6-policy-preset.v2\x00"
        + canonical_json(
            {
                "preset": POLICY_PRESET_ID,
                "control_plane_policy": policy.model_dump(
                    mode="json", by_alias=True, exclude_none=True
                ),
                "criticism_policy_template": criticism.model_dump(
                    mode="json", by_alias=True, exclude_none=True
                ),
                "scratchpad_source": engaged_scratchpad_source(),
            }
        )
    )
    # The digest is bound to the bridge source content, not merely its name:
    # the pre-bridge payload no longer reproduces the preset digest.
    assert engaged_policy_digest() != without_bridge


def test_engaged_simulation_policy_is_declarative_local_and_modest():
    policy = engaged_simulation_policy()

    assert policy.enabled is True
    # Declarative-numeric only: no model-authored Python can reach the
    # local subprocess backend under this runner profile.
    assert policy.runner_profile == "simulation.declarative.v1"
    assert policy.python_toolchain_identity == PUBLIC_SIMULATION_TOOLCHAIN_ID
    assert policy.maximum_simulation_requests == 2
    assert policy.maximum_simulation_executions == 2
    assert policy.maximum_proposals_per_turn == 1
    assert policy.maximum_generated_code_bytes == 16_384
    assert policy.maximum_input_bytes == 16_384
    assert policy.maximum_output_bytes == 16_384
    assert policy.maximum_wall_ms == 10_000
    assert policy.maximum_memory_bytes == 256 * 1024 * 1024
    assert policy.maximum_steps == 50_000
    assert policy.maximum_samples == 32
    assert policy.deterministic_seed_policy == "fixed_manifest"
    assert policy.fixed_seed_set == (7,)
    assert policy.maximum_follow_up_reasoning_turns == 2
    assert policy.network_policy == "forbidden"
    assert policy.filesystem_policy == "isolated_no_filesystem"
    assert policy.failure_policy == "record_and_continue"
    assert policy.input_catalog == ()

    topology = engaged_inquiry_capability_policy()
    assert topology.capability_profile == "inquiry-capabilities.v2"
    assert topology.simulation == policy
    assert topology.attached_evidence.enabled is False
    assert topology.formalization.enabled is False
    assert topology.research.enabled is False


def test_engaged_simulation_toolchain_pin_is_derived_not_hardcoded():
    toolchain = engaged_local_simulation_toolchain()

    assert toolchain.id == PUBLIC_SIMULATION_TOOLCHAIN_ID
    assert toolchain.runner == "local"
    assert toolchain.network is False
    # Derived from the executing interpreter at compile time — the portable
    # pin the wheel needs on end-user machines.
    assert toolchain.executable == str(Path(sys.executable).resolve())
    version = (
        f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
    )
    assert toolchain.version_output_sha256 == sha256_hex(version.encode("utf-8"))


def test_engaged_policy_digest_reflects_the_simulation_policy():
    policy = engaged_control_plane_policy_v3()
    criticism = engaged_criticism_policy("preset-endpoint-template")
    without_simulation = sha256_hex(
        b"deepreason.v6-policy-preset.v2\x00"
        + canonical_json(
            {
                "preset": POLICY_PRESET_ID,
                "control_plane_policy": policy.model_dump(
                    mode="json", by_alias=True, exclude_none=True
                ),
                "criticism_policy_template": criticism.model_dump(
                    mode="json", by_alias=True, exclude_none=True
                ),
                "scratchpad_source": engaged_scratchpad_source(),
                "bridge_source": engaged_bridge_source(),
            }
        )
    )
    # The digest is bound to the simulation policy content, not merely its
    # name: the pre-simulation payload no longer reproduces the preset digest.
    assert engaged_policy_digest() != without_simulation
    # And the digest itself stays machine-neutral: it must not move with the
    # local interpreter pin.
    payload = engaged_simulation_policy().model_dump(mode="json")
    assert sys.executable not in canonical_json(payload).decode("utf-8")


def test_engaged_criticism_policy_binds_every_public_school_observe_only():
    policy = engaged_criticism_policy("endpoint-under-test")

    assert PUBLIC_SCHOOL_COUNT == 4
    assert policy.minimum_foreign_school_coverage == 1
    assert policy.max_batch_size == 4
    assert policy.target_eligibility == "accepted_school_artifacts"
    assert policy.authority == "observe_only"
    assert policy.allow_shared is True
    assert tuple(binding.school_id for binding in policy.bindings) == (
        "school-0",
        "school-1",
        "school-2",
        "school-3",
    )
    assert all(
        binding.role == "argumentative_critic"
        and binding.seat == 0
        and binding.endpoint_id == "endpoint-under-test"
        for binding in policy.bindings
    )


def test_conservative_baseline_remains_closed_and_stable():
    policy = conservative_control_plane_policy_v3()

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
    # The two presets are distinct versions with distinct digests.
    assert conservative_policy_digest() != engaged_policy_digest()
    assert policy != engaged_control_plane_policy_v3()


def test_policy_factories_return_equal_independent_frozen_models():
    assert (
        conservative_control_plane_policy_v3()
        == conservative_control_plane_policy_v3()
    )
    assert conservative_control_plane_policy_v3() is not (
        conservative_control_plane_policy_v3()
    )
    assert engaged_control_plane_policy_v3() == engaged_control_plane_policy_v3()
    assert engaged_control_plane_policy_v3() is not engaged_control_plane_policy_v3()
