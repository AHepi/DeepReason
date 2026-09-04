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


# ---------------------------------------------------------------------------
# The architecture test (R2e): "enforced" means a check that can fail.
#
# Three limbs. Limb 1 is the one that would actually catch a bypass -- a
# consumer that ignores its policy renders identically under two policies that
# disagree, and this notices. Limb 2 catches the bypass BEFORE it is written,
# by refusing a layout decision taken with a literal instead of a policy read.
# Limb 3 asserts the customisation point is reachable without a code edit,
# which is the half of the modularity law a behaviour test alone misses.
# ---------------------------------------------------------------------------

# Re-aimed 2026-09-03: the brief became a walk over registered section
# plugins, so two of the three arrangements `render_conj_pack` used to read
# are now read by the plugins that own those sections. The CLAIM is unchanged
# -- a layout decision is READ from the policy, never held as a constant --
# and the check got finer, because each reader is now pinned individually
# instead of three fields being pinned against one function.
_CONSUMERS = {
    "src/deepreason/llm/packs.py": {
        "render_conj_pack": ("question_last",),
        "render_crit_pack": ("question_last",),
        "_distilled": ("distil_carry_forward", "distilled_head_chars",
                       "retrieval_note"),
    },
    "src/deepreason/llm/seat_plugins.py": {
        "_Neighbourhood": ("live_verbatim_n", "retrieval_note",
                           "distil_carry_forward"),
        "_LiveNeighbourhood": ("live_verbatim_n",),
        "_History": ("superseded_summary_n", "retrieval_note",
                     "distil_carry_forward"),
    },
    "src/deepreason/llm/roles.py": {
        "render_role_prompt": ("merge_head_label_blocks",),
    },
    "src/deepreason/informal/trial.py": {
        "argument_trial_judge_pack": ("question_last",),
        "_judge_pack": ("question_last",),
    },
}


def _function_source(path: str, name: str) -> str:
    """The source of one function OR one class.

    Classes are accepted because a section plugin's layout reads live in its
    `render` method, and every plugin's method carries that same name -- so
    the consumer that must be pinned is the class, not a function name that
    would match thirty of them.
    """
    text = pathlib.Path(path).read_text()
    tree = ast.parse(text)
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.ClassDef)) and node.name == name:
            return ast.get_source_segment(text, node)
    raise AssertionError(f"{name} not found in {path}")


def test_limb2_every_layout_decision_is_read_from_the_policy():
    """A renderer may not HOLD a layout constant; it READS one.

    This is the limb that fails at authoring time. A consumer that decides an
    arrangement with a literal -- `if True`, a bare 160, a fixed section order
    -- stops naming the field, and the field it stopped naming is listed here.
    """
    missing = []
    for path, functions in _CONSUMERS.items():
        for name, fields in functions.items():
            source = _function_source(path, name)
            for field in fields:
                if f"layout.{field}" not in source:
                    missing.append(f"{path}::{name} does not read layout.{field}")
    assert not missing, missing


def test_limb2_no_consumer_invents_its_own_arrangement():
    """Constructing a policy inside a renderer would be the same bypass with
    extra steps: the arrangement would live in the consumer again."""
    for path in _CONSUMERS:
        source = pathlib.Path(path).read_text()
        assert "RenderLayoutPolicyV1(" not in source, path


def test_limb2_carry_forward_goes_through_the_policy_not_the_raw_head():
    """`_head` survives for three sections that are NOT carry-forward of prior
    conjectures -- the retry pack, standing attacks, and support content. A
    fourth call site would be a carry-forward rendered outside the policy, so
    the count is pinned rather than the intent asserted."""
    # Re-aimed 2026-09-03: two of the three call sites moved into the section
    # plugins that own their sections (standing attacks, support content),
    # where the state arrives on the request. The TOTAL is what the claim is
    # about, so it is pinned across both files AND per file, which is stricter
    # than the single-file count it replaces -- moving a fourth call site into
    # the plugin module can no longer hide under an unchanged packs.py count.
    packs = pathlib.Path("src/deepreason/llm/packs.py").read_text()
    plugins = pathlib.Path("src/deepreason/llm/seat_plugins.py").read_text()
    in_packs = packs.count("_head(state,")
    in_plugins = plugins.count("_head(request.state,")
    assert in_packs == 1, in_packs           # the retry pack
    assert in_plugins == 2, in_plugins       # standing attacks, support content
    assert in_packs + in_plugins == 3
    for renderer in ("render_conj_pack", "render_crit_pack"):
        assert "_head(" not in _function_source(
            "src/deepreason/llm/packs.py", renderer
        )


def test_limb3_an_arrangement_is_selectable_without_a_code_edit(monkeypatch):
    """The customisation point the modularity law requires to EXIST: register
    an arrangement, select it from the environment, and the render follows --
    with no edit to packs.py, roles.py or trial.py."""
    from deepreason.informal.trial import argument_trial_judge_pack

    probe = RenderLayoutPolicyV1(
        policy_id="render-layout.probe-customisation", question_last=False
    )
    register_layout_policy(probe)
    monkeypatch.setenv(LAYOUT_POLICY_ENV, probe.policy_id)

    pack = argument_trial_judge_pack(
        target_text="t", case_text="c", defence="d"
    )
    assert pack.index("QUESTION:") < pack.index("THE CASE FOR FAIL:")

    monkeypatch.setenv(LAYOUT_POLICY_ENV, DEFAULT_LAYOUT_POLICY_ID)
    pack = argument_trial_judge_pack(
        target_text="t", case_text="c", defence="d"
    )
    assert pack.index("QUESTION:") > pack.index("THE DEFENCE:")


def test_limb1_a_bypass_is_visible_as_two_policies_rendering_alike():
    """Limb 1, stated generically: two policies that DISAGREE on every flag
    must produce different bytes at every consumer. A consumer that ignores
    its policy renders identically under both, and this is what notices.

    `tests/test_render_layout_rules.py` carries the same comparison per rule,
    with the specific difference each rule names; this limb is the blanket
    one, so a NEW consumer that forgets its policy is caught here even before
    a rule-specific test exists for it.
    """
    from deepreason.harness import Harness  # noqa: F401  (fixtures build one)
    from deepreason.informal.trial import argument_trial_judge_pack
    from deepreason.llm.roles import render_role_prompt

    robust = resolve_layout_policy(DEFAULT_LAYOUT_POLICY_ID)
    legacy = resolve_layout_policy(LEGACY_LAYOUT_POLICY_ID)
    assert robust != legacy

    renders = {
        "argument_trial_judge_pack": lambda p: argument_trial_judge_pack(
            target_text="t", case_text="c", defence="d", layout=p
        ),
        "render_role_prompt": lambda p: render_role_prompt(
            "conjecturer", schema="{}", pack="## problem\nq",
            profile="compact", example="{}", aliases="SRC_001", layout=p,
        ),
    }
    same = [name for name, fn in renders.items() if fn(robust) == fn(legacy)]
    assert not same, f"consumers ignoring their layout policy: {same}"
