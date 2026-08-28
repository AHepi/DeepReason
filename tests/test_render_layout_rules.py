"""The four robust layout rules, as behaviour of the two IR renderers.

Every test here is a BEFORE/AFTER pair against the two shipped policies:
`render-layout.v1` is the arrangement this tranche introduces and
`render-layout.legacy-v0` is the arrangement every committed root was
rendered under. A pair that cannot tell them apart is a consumer ignoring its
policy, which is the bypass `test_render_layout_policy.py` exists to catch.

Regression (census 2026-08-28, experiments/2026-08-28-change-render-layout-
robust/CENSUS.md): measured over 2836 real dispatched prompts, five seats
rendered load-bearing material AFTER the question -- up to 16091 characters
of it on `conjecturer.turn.v6`.
"""

import pytest

from deepreason.harness import Harness
from deepreason.llm.layout import (
    DEFAULT_LAYOUT_POLICY_ID,
    LEGACY_LAYOUT_POLICY_ID,
    resolve_layout_policy,
)
from deepreason.llm.packs import render_conj_pack, render_crit_pack
from deepreason.ontology import (
    Interface,
    Problem,
    ProblemProvenance,
    Provenance,
)

ROBUST = resolve_layout_policy(DEFAULT_LAYOUT_POLICY_ID)
LEGACY = resolve_layout_policy(LEGACY_LAYOUT_POLICY_ID)

QUESTION = (
    "Why does the air in a large city stay several degrees warmer than the "
    "surrounding countryside on a clear, calm night?"
)


def _problem(harness, pid=" p-layout"):
    return harness.register_problem(
        Problem(
            id=pid.strip(),
            description=QUESTION,
            criteria=[],
            provenance=ProblemProvenance.model_validate(
                {"trigger": "seed", "from": []}
            ),
        )
    )


def _art(harness, text, role="import"):
    return harness.create_artifact(
        text, interface=Interface(refs=[]), provenance=Provenance(role=role)
    )


def _headers(pack: str) -> list[str]:
    return [line[3:] for line in pack.splitlines() if line.startswith("## ")]


def _after_question_chars(pack: str, question_id: str) -> int:
    """Characters rendered after the question's section ends."""
    marker = f"## {question_id}\n"
    start = pack.index(marker) + len(marker)
    end = pack.find("\n## ", start)
    return 0 if end == -1 else len(pack) - end


# ---------------------------------------------------------------- R2a


def test_the_conjecturer_pack_ends_with_the_question(harness):
    problem = _problem(harness)
    _art(harness, "an accepted neighbour with some content to carry forward")

    robust = render_conj_pack(
        problem, harness.state, harness.commitments, harness.blobs,
        vs_k=2, token_budget=2500, layout=ROBUST,
    )
    legacy = render_conj_pack(
        problem, harness.state, harness.commitments, harness.blobs,
        vs_k=2, token_budget=2500, layout=LEGACY,
    )

    assert _headers(robust)[-1] == "question"
    assert _after_question_chars(robust, "question") == 0
    # The question restatement carries no new content: it is the problem, again.
    assert QUESTION in robust.split("## question", 1)[1]

    assert "question" not in _headers(legacy)
    assert _after_question_chars(legacy, "problem") > 0


def test_the_critic_pack_ends_with_the_question_and_names_its_target(harness):
    _problem(harness)
    target = _art(harness, "the nocturnal gap is driven by stored heat release")

    robust = render_crit_pack(
        target.id, harness.state, harness.commitments, harness.blobs,
        token_budget=2500, layout=ROBUST,
    )
    legacy = render_crit_pack(
        target.id, harness.state, harness.commitments, harness.blobs,
        token_budget=2500, layout=LEGACY,
    )

    assert _headers(robust)[-1] == "question"
    assert _after_question_chars(robust, "question") == 0
    tail = robust.split("## question", 1)[1]
    assert target.id in tail

    assert "question" not in _headers(legacy)


def test_the_question_survives_a_budget_that_drops_everything_optional(harness):
    """Mandatory and exact, for the reason `target` and `open-criticisms` are:
    a droppable restatement would let budget pressure silently restore the
    arrangement the section exists to abolish."""
    problem = _problem(harness)
    _art(harness, "x" * 4000)

    pack = render_conj_pack(
        problem, harness.state, harness.commitments, harness.blobs,
        vs_k=2, token_budget=1, layout=ROBUST,
    )
    assert _headers(pack)[-1] == "question"
    assert QUESTION in pack.split("## question", 1)[1]


# ---------------------------------------------------------------- R2a, judge


def _judge_texts():
    return {
        "target_text": "the nocturnal gap is driven by reduced sky view factor",
        "case_text": "SRC_001 confuses emissivity with geometry, and the "
                     "cross-city modulator it names is a proxy, not a cause.",
        "defence": "The critic conflates an algorithmic process with a "
                   "mathematical definition; the target names both.",
    }


def test_the_argument_trial_judge_pack_asks_last(monkeypatch):
    """Regression (census 2026-08-28): across 342 recorded judge prompts the
    QUESTION line preceded the case and the defence -- the two things the
    judge is asked to weigh -- by up to 7503 characters."""
    from deepreason.informal.trial import argument_trial_judge_pack

    t = _judge_texts()
    robust = argument_trial_judge_pack(**t, layout=ROBUST)
    legacy = argument_trial_judge_pack(**t, layout=LEGACY)

    assert robust.index("QUESTION:") > robust.index("THE DEFENCE:")
    assert robust.rstrip().endswith(
        "Rule on the exchange; decisive_point MUST quote a span of it."
    )
    assert legacy.index("QUESTION:") < legacy.index("THE CASE FOR FAIL:")

    # A reordering and only a reordering: the same lines, in a different order.
    assert sorted(robust.split("\n")) == sorted(legacy.split("\n"))


def test_the_standard_trial_judge_pack_asks_last(harness):
    from deepreason.config import Config
    from deepreason.informal.trial import _judge_pack

    body = {"spec": "s-uhi", "mode": "direct", "rubric": "the standard"}
    kwargs = dict(
        harness=harness, config=Config(), body=body,
        target_text="stored heat release explains the nocturnal gap",
        case="the case for fail", answer="the defence",
        standard_id="s-uhi",
    )
    robust = _judge_pack(**kwargs, layout=ROBUST)
    legacy = _judge_pack(**kwargs, layout=LEGACY)

    assert robust.index("QUESTION:") > robust.index("THE DEFENCE:")
    assert legacy.index("QUESTION:") < legacy.index("THE CASE FOR FAIL:")
    assert robust.rstrip().endswith(
        "Rule on the exchange; decisive_point MUST quote a span of it."
    )
    assert sorted(robust.split("\n")) == sorted(legacy.split("\n"))


# ---------------------------------------------------------------- R2c

# A claim longer than the default 160-char distillation width, so the in-band
# clip marker is exercised, inside an envelope whose serialization is far
# longer still, so the prefix-clip and the distillation cannot be confused.
ENVELOPE = (
    '{"analogy": null, "claim": "Nocturnal urban warmth is stored daytime heat '
    'released after sunset from surfaces with high thermal admittance, and the '
    'single best cross-city modulator is the sky view factor, which sets how '
    'much longwave escapes to the cold sky.", '
    '"mechanism": "' + "long prose about radiative exchange. " * 40 + '", '
    '"counterconditions": [], "premises": []}'
)


def _accepted(harness, text):
    """A created artifact is ACCEPTED until something attacks it."""
    return _art(harness, text)


def test_a_carried_forward_artifact_is_its_claim_not_a_cut_through_its_middle(
    harness,
):
    """Regression (census 2026-08-28): packs.py::_head took the first 160
    characters of a serialized envelope -- a cut through the middle of a JSON
    object, which is neither the verbatim text nor a distilled summary."""
    problem = _problem(harness)
    art = _accepted(harness, ENVELOPE)

    robust = render_conj_pack(
        problem, harness.state, harness.commitments, harness.blobs,
        vs_k=2, token_budget=2500, layout=ROBUST,
    )
    legacy = render_conj_pack(
        problem, harness.state, harness.commitments, harness.blobs,
        vs_k=2, token_budget=2500, layout=LEGACY,
    )

    # With one accepted artifact and live_verbatim_n=2 it renders whole and
    # late; force it into the distilled section by asking for none verbatim.
    distilling = ROBUST.model_copy(update={"live_verbatim_n": 0})
    distilled = render_conj_pack(
        problem, harness.state, harness.commitments, harness.blobs,
        vs_k=2, token_budget=2500, layout=distilling,
    )
    entry = [
        line for line in distilled.splitlines()
        if line.startswith(f"- {art.id}:")
    ][0]
    assert "Nocturnal urban warmth is stored daytime heat" in entry
    assert '"mechanism"' not in entry
    assert entry.endswith("[clipped; request this alias for the whole text]")

    # The header names the retrieval route the pack never used to mention.
    assert "context_request" in distilled

    # Legacy is the cut through the middle, with no marker and no route.
    legacy_entry = [
        line for line in legacy.splitlines()
        if line.startswith(f"- {art.id}:")
    ][0]
    assert legacy_entry.startswith("- " + art.id + ': {"analogy": null, "claim"')
    assert "clipped" not in legacy_entry
    assert "context_request" not in legacy
    assert robust != legacy


def test_live_neighbours_render_whole_and_late(harness):
    problem = _problem(harness)
    live = _accepted(harness, ENVELOPE)

    pack = render_conj_pack(
        problem, harness.state, harness.commitments, harness.blobs,
        vs_k=2, token_budget=6000, layout=ROBUST,
    )
    headers = _headers(pack)
    assert "live-neighbourhood" in headers
    # Late: after every context section, before only the question.
    # Late: the LAST context section, with only the output contract and the
    # question after it.
    assert headers[-3:] == ["live-neighbourhood", "output-contract", "question"]
    body = pack.split("## live-neighbourhood", 1)[1].split("\n## ", 1)[0]
    assert ENVELOPE in body        # whole, not distilled
    assert live.id in body

    legacy = render_conj_pack(
        problem, harness.state, harness.commitments, harness.blobs,
        vs_k=2, token_budget=6000, layout=LEGACY,
    )
    assert "live-neighbourhood" not in _headers(legacy)


def test_superseded_conjectures_are_omitted_by_default_and_renderable_on_request(
    harness,
):
    """Omission is one of the two options the research note's own table gives
    for this row, and it is what this tree ships. The knob exists so the
    question can be settled by a run rather than by argument."""
    from deepreason.ontology import Status
    from tests.conftest import attack

    problem = _problem(harness)
    dead = _art(harness, '{"claim": "the tide is the moon alone"}')
    attack(harness, dead.id, "moon-only")
    assert harness.state.status[dead.id] is Status.REFUTED

    default = render_conj_pack(
        problem, harness.state, harness.commitments, harness.blobs,
        vs_k=2, token_budget=2500, layout=ROBUST,
    )
    assert "superseded-conjectures" not in _headers(default)
    assert dead.id not in default

    asked = ROBUST.model_copy(update={"superseded_summary_n": 3})
    carried = render_conj_pack(
        problem, harness.state, harness.commitments, harness.blobs,
        vs_k=2, token_budget=2500, layout=asked,
    )
    assert "superseded-conjectures" in _headers(carried)
    assert "the tide is the moon alone" in carried
    assert '"claim"' not in carried.split("## superseded-conjectures", 1)[1]


def test_an_artifact_with_no_claim_keeps_its_entry(harness):
    """The fallback is not decoration: prose artifacts, school policies and
    relations have no claim field, and an entry that vanished would be a
    silent omission."""
    problem = _problem(harness)
    prose = _accepted(harness, "a plain prose artifact with no claim field " * 8)

    distilling = ROBUST.model_copy(update={"live_verbatim_n": 0})
    pack = render_conj_pack(
        problem, harness.state, harness.commitments, harness.blobs,
        vs_k=2, token_budget=2500, layout=distilling,
    )
    entry = [
        line for line in pack.splitlines() if line.startswith(f"- {prose.id}:")
    ][0]
    assert "a plain prose artifact with no claim field" in entry


# ---------------------------------------------------------------- R2d


def _head_blocks(prompt: str) -> list[str]:
    head = prompt.split("\nINPUT:", 1)[0]
    return [b for b in head.split("\n\n") if b.strip()]


def test_a_label_and_the_body_it_labels_are_one_block():
    """Regression (census 2026-08-28): a compact prompt head carried nine
    blocks, five of them under 100 characters and four of them bare labels.
    The U-shape re-instantiates inside every delimiter-bounded interval, so a
    bare label buys a block boundary for six characters of text."""
    from deepreason.llm.roles import render_role_prompt

    kwargs = dict(
        role="conjecturer",
        schema='{"type": "object"}',
        pack="## problem\nwhy is the city warm at night",
        profile="compact",
        example='{"abstention": {"search_signal": "stuck"}}',
        aliases="SRC_001\nSRC_002",
    )
    robust = render_role_prompt(**kwargs, layout=ROBUST)
    legacy = render_role_prompt(**kwargs, layout=LEGACY)

    assert len(_head_blocks(robust)) < len(_head_blocks(legacy))
    assert not any(
        b.strip() in {"ONE SYNTAX EXAMPLE:", "INPUT:",
                      "LOCAL REFERENCES (copy aliases, not identifiers):",
                      "Return ONLY one JSON value matching this closed schema:"}
        for b in _head_blocks(robust)
    )
    # Not one word changes, and not one changes order.
    assert robust.split() == legacy.split()


def test_the_standard_profile_head_is_already_few_blocks_and_is_untouched():
    """R1's closure rule: the non-compact template is role text, schema, pack.
    There is no bare label to merge, so nothing is churned."""
    from deepreason.llm.roles import render_role_prompt

    kwargs = dict(
        role="conjecturer", schema='{"type": "object"}',
        pack="## problem\nwhy is the city warm at night", profile="standard",
    )
    assert render_role_prompt(**kwargs, layout=ROBUST) == render_role_prompt(
        **kwargs, layout=LEGACY
    )
