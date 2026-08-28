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
