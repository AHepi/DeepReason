"""The render layout policy, and the architecture test that catches a bypass.

`docs/map/INV-render-layout.md` is the governing document. The rules under
test come from the "robust across models" list of
`docs/RESEARCH_ATTENTION_LAYOUT_2026-08-28.md`; the note is an external
document and is never evidence here -- these tests assert what the tree
renders, which is.
"""

import ast
import pathlib

import pytest

from deepreason.llm.layout import (
    DEFAULT_LAYOUT_POLICY_ID,
    LAYOUT_POLICY_ENV,
    LEGACY_LAYOUT_POLICY_ID,
    RenderLayoutPolicyError,
    RenderLayoutPolicyV1,
    layout_policy_ids,
    register_layout_policy,
    resolve_layout_policy,
)


def test_the_policy_registry_resolves_and_refuses(monkeypatch):
    monkeypatch.delenv(LAYOUT_POLICY_ENV, raising=False)
    assert resolve_layout_policy().policy_id == DEFAULT_LAYOUT_POLICY_ID
    assert resolve_layout_policy().question_last is True

    # The environment selects an arrangement without a code edit -- the
    # customisation point the modularity law requires to exist.
    monkeypatch.setenv(LAYOUT_POLICY_ENV, LEGACY_LAYOUT_POLICY_ID)
    legacy = resolve_layout_policy()
    assert legacy.policy_id == LEGACY_LAYOUT_POLICY_ID
    assert legacy.question_last is False
    assert legacy.merge_head_label_blocks is False

    # An explicit argument beats the environment.
    assert resolve_layout_policy(DEFAULT_LAYOUT_POLICY_ID).question_last is True

    monkeypatch.setenv(LAYOUT_POLICY_ENV, "render-layout.does-not-exist")
    with pytest.raises(RenderLayoutPolicyError) as caught:
        resolve_layout_policy()
    assert caught.value.code == "RENDER_LAYOUT_POLICY_UNKNOWN"
    assert set(layout_policy_ids()) >= {
        DEFAULT_LAYOUT_POLICY_ID,
        LEGACY_LAYOUT_POLICY_ID,
    }


@pytest.mark.parametrize(
    "field,value",
    [
        ("instruction_ceiling", 0),
        ("instruction_ceiling", 81),  # above the note's hard floor
        ("live_verbatim_n", -1),
        ("live_verbatim_n", 9),
        ("distilled_head_chars", 31),
        ("distilled_head_chars", 4097),
        ("superseded_summary_n", -1),
        ("superseded_summary_n", 9),
    ],
)
def test_a_free_parameter_outside_its_envelope_is_refused_not_clamped(field, value):
    """FREE means free WITHIN an envelope. A silent clamp would render one
    arrangement while the policy claimed another."""
    with pytest.raises(ValueError):
        RenderLayoutPolicyV1(policy_id="probe", **{field: value})


def test_a_policy_is_frozen_and_closed():
    policy = resolve_layout_policy(DEFAULT_LAYOUT_POLICY_ID)
    with pytest.raises(ValueError):
        policy.question_last = False
    with pytest.raises(ValueError):
        RenderLayoutPolicyV1(policy_id="probe", unknown_flag=True)


def test_re_registering_one_id_with_different_values_is_refused():
    """A policy id names ONE arrangement, or two renders citing the same id do
    not mean the same thing."""
    first = RenderLayoutPolicyV1(policy_id="render-layout.probe-conflict")
    register_layout_policy(first)
    register_layout_policy(first)  # idempotent
    with pytest.raises(RenderLayoutPolicyError) as caught:
        register_layout_policy(
            RenderLayoutPolicyV1(
                policy_id="render-layout.probe-conflict", question_last=False
            )
        )
    assert caught.value.code == "RENDER_LAYOUT_POLICY_CONFLICT"
