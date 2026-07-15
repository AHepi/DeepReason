"""Typed source configuration for advisory scratch and grounded output."""

from __future__ import annotations

import math

import pytest
from pydantic import ValidationError

from deepreason.config import (
    BridgeConfig,
    Config,
    ScratchpadConfig,
    apply_overrides,
)


def test_safe_defaults_are_bounded_and_features_remain_opt_in():
    config = Config()

    assert config.scratchpad == ScratchpadConfig()
    assert config.scratchpad.enabled is False
    assert config.scratchpad.coverage_enabled is True
    assert config.scratchpad.coverage_slot_every_n_packs == 4
    assert config.scratchpad.exploratory_fraction == 0.10
    assert config.scratchpad.underexposed_fraction == 0.15
    assert config.scratchpad.dormant_after_events == 200
    assert config.bridge == BridgeConfig()
    assert config.bridge.mode == "legacy_thesis"
    assert config.bridge.target_profile == "plain"
    assert config.bridge.reviewer_seats == 1


def test_nested_unknown_knobs_fail_for_models_profiles_and_overrides():
    with pytest.raises(ValidationError, match="unknown_attention_knob"):
        Config.model_validate(
            {"scratchpad": {"unknown_attention_knob": "ignored-never"}}
        )
    with pytest.raises(ValidationError, match="unknown_bridge_knob"):
        Config.model_validate({"bridge": {"unknown_bridge_knob": True}})
    with pytest.raises(ValueError, match="unknown config path"):
        apply_overrides(Config(), {"scratchpad.unknown_attention_knob": 1})
    with pytest.raises(ValueError, match="unknown config path"):
        apply_overrides(Config(), {"bridge.unknown_bridge_knob": 1})


def test_dotted_overrides_use_the_same_nested_validation():
    configured = apply_overrides(
        Config(),
        {
            "scratchpad.enabled": True,
            "scratchpad.max_blocks_per_pack": 12,
            "scratchpad.semantic_retrieval": False,
            "bridge.mode": "grounded_two_stage",
            "bridge.composer_role": "summarizer",
            "bridge.reviewer_role": "grounding_reviewer",
            "bridge.target_profile": "answer.compact-v1",
        },
    )

    assert configured.scratchpad.enabled is True
    assert configured.scratchpad.max_blocks_per_pack == 12
    assert configured.scratchpad.semantic_retrieval is False
    assert configured.bridge.mode == "grounded_two_stage"
    assert configured.bridge.composer_role == "summarizer"
    assert configured.bridge.reviewer_role == "grounding_reviewer"
    assert configured.bridge.target_profile == "answer.compact-v1"

    with pytest.raises(ValidationError, match="less than or equal to 2"):
        apply_overrides(Config(), {"bridge.max_schema_repair_attempts": 3})


@pytest.mark.parametrize(
    "field",
    [
        "allow_partial",
        "allow_abstention",
        "require_claim_ledger",
        "require_claim_uses",
    ],
)
def test_grounded_mode_cannot_disable_unresolved_success_safety(field):
    with pytest.raises(
        ValidationError, match="grounded_two_stage requires unresolved-success-safe"
    ):
        BridgeConfig(mode="grounded_two_stage", **{field: False})

    # Legacy mode remains an exact compatibility surface; inactive grounded
    # policy does not change the historical thesis path.
    assert BridgeConfig(**{field: False}).mode == "legacy_thesis"


@pytest.mark.parametrize("value", [math.inf, -math.inf, math.nan])
def test_similarity_threshold_must_be_finite(value):
    with pytest.raises(ValidationError, match="similarity_threshold must be finite"):
        ScratchpadConfig(similarity_threshold=value)


def test_reserved_attention_fractions_and_limits_are_bounded():
    with pytest.raises(ValidationError, match="fractions must not exceed one"):
        ScratchpadConfig(exploratory_fraction=0.6, underexposed_fraction=0.5)
    with pytest.raises(ValidationError, match="greater than 0"):
        ScratchpadConfig(max_blocks_per_pack=0)
    with pytest.raises(ValidationError, match="greater than 0"):
        ScratchpadConfig(coverage_slot_every_n_packs=0)
    with pytest.raises(ValidationError, match="less than or equal to 1"):
        ScratchpadConfig(exploratory_fraction=1.1)
    with pytest.raises(ValidationError, match="less than or equal to 128"):
        BridgeConfig(output_section_limit=129)
    with pytest.raises(ValidationError, match="less than or equal to 1"):
        BridgeConfig(reviewer_seats=2)
    with pytest.raises(ValidationError, match="less than or equal to 8"):
        BridgeConfig(max_grounding_repair_attempts=9)


def test_roles_modes_and_target_profile_are_closed_or_safely_bounded():
    with pytest.raises(ValidationError):
        ScratchpadConfig(block_role="judge")
    with pytest.raises(ValidationError):
        ScratchpadConfig(link_role="conjecturer")
    with pytest.raises(ValidationError):
        BridgeConfig(mode="automatic")
    with pytest.raises(ValidationError):
        BridgeConfig(ledger_role="conjecturer")
    with pytest.raises(ValidationError):
        BridgeConfig(composer_role="conjecturer")
    with pytest.raises(ValidationError):
        BridgeConfig(reviewer_role="summarizer")
    with pytest.raises(ValidationError):
        BridgeConfig(target_profile="../../prompt")


def test_nested_assignment_is_validated_and_arbitrary_roles_remain_supported():
    scratchpad = ScratchpadConfig()
    with pytest.raises(ValidationError):
        scratchpad.max_blocks_per_pack = 0

    bridge = BridgeConfig(mode="grounded_two_stage")
    with pytest.raises(ValidationError, match="unresolved-success-safe"):
        bridge.allow_abstention = False

    configured = Config(
        roles={
            "researcher": {
                "endpoint": "https://example.invalid/v1",
                "model": "research-model",
            }
        }
    )
    assert configured.roles["researcher"]["model"] == "research-model"


def test_embedder_failure_policy_is_closed_without_requiring_neural_dependency():
    assert Config(EMBEDDER_MODEL=None).EMBEDDER_FAILURE_POLICY == "fallback"
    assert Config(
        EMBEDDER_MODEL="not-installed/in-config-validation",
        EMBEDDER_FAILURE_POLICY="error",
        scratchpad={"semantic_retrieval": False},
    ).scratchpad.semantic_retrieval is False
    with pytest.raises(ValidationError):
        Config(EMBEDDER_FAILURE_POLICY="silent")

