"""A commitment that was NOT EVALUATED must not move the coverage coordinate.

Regression (live roots P-S1 `9e48a36b1dec91ee`, P-A1 `4565139800f5ca02`,
P-R1 `experiments/2026-08-25-poietics-program/run`): on all three, every
artifact answering the operator's SEED question was dominated off the Pareto
frontier and every frontier member answered a harness-minted `connection`
problem — 40/58, 4/7 and 18/40 respectively, a total split. No commitment
FAILED anywhere on any of the three roots, so the coverage axis carried no
quality signal at all: its whole variance was the number of falsifiable
counterconditions each artifact had declared. Seed artifacts passed twice as
many checks (4 vs 2) and ranked below.

The mechanism: `pareto_scores` counts `programs.OVERRUN` in the coverage
denominator as a non-pass. OVERRUN is the typed verdict for "the harness
obtained no verdict", and every other consumer of `programs.evaluate` already
reads it that way (`rules/act.py:15-17` "a spec defect, not the candidate's
fault"; `rules/crit.py:893-897` and `:1145-1147`; the `_lean_external_check`
docstring "an operational overrun, never a failed proof"). The ranking axis
was the sole dissenter, so declaring a testable claim lowered your rank.

Why `tests/test_formalism_optional_rank.py` did not catch it: it builds its
pending commitment as `eval="observation"`, which `programs.evaluable` screens
out (empty battery -> coverage omitted, the protected road). No live run ever
carries that spelling — `workloads/text.py:222-226` rewrites every declared
`eval: "observation"` into `eval: "program:reasoning_observation_pending"`,
which IS evaluable and evaluates OVERRUN. `test_the_minted_spelling_is_the_one
_scored_here` below pins the two spellings together so they cannot diverge
again.

The law this serves: ranking is EFFICIENCY, never EVIDENCE — no coverage
number may move a Status (`test_status_unchanged_by_the_coverage_axis`), and
formal backing may confer protection while its absence confers no
disadvantage (DUAL_MODE_CONJECTURE_PREPLAN.md R-g).
"""

import pytest

from deepreason.config import Config
from deepreason.harness import Harness
from deepreason.ontology import (
    Commitment,
    Interface,
    Problem,
    Provenance,
    SpawnTrigger,
)
from deepreason.ontology.commitment import Budget
from deepreason.ontology.problem import ProblemProvenance
from deepreason.scheduler.scheduler import pareto_scores, run_report

PASSING = "predicate:len(content) > 0"
ALSO_PASSING = "predicate:content == content"
FAILING = "predicate:len(content) > 10**9"

# The verbatim shape a live root carries, read off P-A1 commitment
# `reason-counter@1de371e0006ce0a0bdf77483`:
#   {'eval': 'program:reasoning_observation_pending', 'observation_valued': True,
#    'budget': {'steps': 100000, 'time_ms': 2000, 'extra': {}}}
PENDING = "program:reasoning_observation_pending"


def _root(tmp_path, batteries: dict[str, list[str]]) -> tuple[Harness, dict[str, str]]:
    """One seed problem, one artifact per battery. No status is hand-set:
    every artifact is unattacked, so the harness's own grounded-extension pass
    labels it and `run_report`'s survivor predicate admits it."""
    harness = Harness(tmp_path / "run")
    harness.register_commitment(Commitment(id="ok", eval=PASSING))
    harness.register_commitment(Commitment(id="ok2", eval=ALSO_PASSING))
    harness.register_commitment(Commitment(id="no", eval=FAILING))
    for n in (1, 2, 3):
        harness.register_commitment(
            Commitment(
                id=f"pend{n}",
                eval=PENDING,
                observation_valued=True,
                budget=Budget(steps=100_000, time_ms=2_000),
            )
        )
    problem = harness.register_problem(
        Problem(
            id="p1",
            description="a problem",
            criteria=["ok", "ok2", "no", "pend1", "pend2", "pend3"],
            provenance=ProblemProvenance(trigger=SpawnTrigger.SEED),
        )
    )
    ids = {}
    for label, commitments in batteries.items():
        ids[label] = harness.create_artifact(
            f"a conjecture, written as {label}",
            interface=Interface(commitments=list(commitments)),
            provenance=Provenance(role="conjecturer"),
            problem_id=problem.id,
        ).id
    return harness, ids


def _frontier(harness, ids) -> list[str]:
    by_id = {v: k for k, v in ids.items()}
    report = run_report(harness, Config())
    assert sorted(report["survivors"]) == sorted(ids.values()), "setup: all must survive"
    return sorted(by_id[aid] for aid in report["frontier"])


def _coverage(harness, aid):
    return pareto_scores(harness, aid).get("coverage")


# --- the defect itself -------------------------------------------------------

def test_declaring_pending_counterconditions_does_not_lower_coverage(tmp_path):
    """THE GOAL. Two artifacts identical except that one declares three extra
    observation-valued counterconditions. "Not measured" is neither a pass nor
    a fail, so the two must receive the SAME coverage coordinate.

    RED before the fix: `declares` scores 2/5 = 0.4 against `plain`'s 2/2."""
    harness, ids = _root(
        tmp_path,
        {
            "plain": ["ok", "ok2"],
            "declares": ["ok", "ok2", "pend1", "pend2", "pend3"],
        },
    )
    assert _coverage(harness, ids["declares"]) == _coverage(harness, ids["plain"])


def test_declaring_pending_counterconditions_does_not_cost_the_frontier(tmp_path):
    """The consequence the live roots recorded: the declaring artifact was
    dominated off the published frontier by its non-declaring sibling."""
    harness, ids = _root(
        tmp_path,
        {
            "plain": ["ok", "ok2"],
            "declares": ["ok", "ok2", "pend1", "pend2", "pend3"],
        },
    )
    assert _frontier(harness, ids) == ["declares", "plain"]


def test_the_live_three_countercondition_shape_scores_a_full_battery(tmp_path):
    """The numeric statement, so a partial repair cannot pass: an artifact
    whose only unevaluated commitments are pending scores on what WAS
    evaluated — 2 passes out of 2 decided, not 2 out of 5 declared."""
    harness, ids = _root(tmp_path, {"declares": ["ok", "ok2", "pend1", "pend2", "pend3"]})
    assert _coverage(harness, ids["declares"]) == 1.0


# --- what must NOT change (mutation controls) --------------------------------

def test_fails_still_lowers_coverage(tmp_path):
    """MUTATION CONTROL, and the line between a lawful repair and "put everyone
    on the frontier": a commitment that was CHECKED AND FAILED must still lower
    coverage. Only "not measured" leaves the denominator."""
    harness, ids = _root(tmp_path, {"passed": ["ok"], "failed": ["no"]})
    assert _coverage(harness, ids["failed"]) == 0.0
    assert _coverage(harness, ids["passed"]) == 1.0
    assert _frontier(harness, ids) == ["passed"]


def test_fails_still_lowers_coverage_when_pending_are_also_declared(tmp_path):
    """The two rules compose: pending leaves the denominator, a failure stays
    in it. One pass and one failure alongside three pending scores 1/2, never
    1/5 (today's bug) and never 1/1 (an over-eager repair that also dropped
    the failure)."""
    harness, ids = _root(tmp_path, {"mixed": ["ok", "no", "pend1", "pend2", "pend3"]})
    assert _coverage(harness, ids["mixed"]) == 0.5


def test_pending_commitments_do_not_inflate_a_score_either(tmp_path):
    """R-g is direction-neutral. Declaring counterconditions must not become an
    ADVANTAGE: an artifact that failed a real check stays dominated by a clean
    sibling no matter how many pending observations it also declares."""
    harness, ids = _root(
        tmp_path,
        {"clean": ["ok", "ok2"], "failed_but_declares": ["ok", "no", "pend1", "pend2", "pend3"]},
    )
    assert _frontier(harness, ids) == ["clean"]


def test_a_wholly_pending_battery_omits_coverage_rather_than_scoring_it(tmp_path):
    """Composition with the rule already shipped: an artifact with NOTHING
    decided has no denominator, so `pareto_scores` must OMIT the key — the
    typed "not measured" that `capture.pareto.frontier` drops from the pairwise
    comparison. Writing 0.0 would put it on the floor; writing 1.0 would let it
    dominate a sibling that was actually checked."""
    harness, ids = _root(tmp_path, {"all_pending": ["pend1", "pend2", "pend3"]})
    scores = pareto_scores(harness, ids["all_pending"])
    assert "coverage" not in scores, scores


def test_status_unchanged_by_the_coverage_axis(tmp_path):
    """Ranking is EFFICIENCY, never EVIDENCE (CLAUDE.md; the allocation law's
    "touches efficiency never evidence"). Whatever the coverage numbers do,
    every artifact's Status and the survivor set are exactly what the harness's
    own adjudication produced. Pinned as literals so a fix that moved an
    acceptance would go red here."""
    harness, ids = _root(
        tmp_path,
        {
            "plain": ["ok", "ok2"],
            "declares": ["ok", "ok2", "pend1", "pend2", "pend3"],
            "failed": ["no"],
            "all_pending": ["pend1", "pend2", "pend3"],
        },
    )
    by_id = {v: k for k, v in ids.items()}
    statuses = {
        by_id[a]: getattr(s, "name", str(s))
        for a, s in harness.state.status.items()
        if a in by_id
    }
    assert statuses == {
        "plain": "ACCEPTED",
        "declares": "ACCEPTED",
        "failed": "ACCEPTED",
        "all_pending": "ACCEPTED",
    }, statuses
    report = run_report(harness, Config())
    assert sorted(by_id[a] for a in report["survivors"]) == [
        "all_pending",
        "declares",
        "failed",
        "plain",
    ]


# --- the guard that would have caught the original defect --------------------

def test_the_minted_spelling_is_the_one_scored_here(tmp_path):
    """The defect survived `tests/test_formalism_optional_rank.py` because that
    file pins `eval="observation"`, which `programs.evaluable` screens out,
    while every live artifact carries the REWRITTEN spelling this file pins.
    Assert the two together, so a future change to either road cannot silently
    reopen the gap."""
    from deepreason import programs
    from deepreason.workloads.text import (
        Countercondition,
        ReasoningEnvelopeV1,
        draft_countercondition_commitments,
    )

    envelope = ReasoningEnvelopeV1(
        claim="a claim",
        mechanism="a mechanism",
        counterconditions=(Countercondition(case="if the count exceeds n", eval="observation"),),
    )
    (minted,) = draft_countercondition_commitments(envelope)

    assert minted.eval == PENDING, "the minting road changed spelling"
    assert minted.observation_valued is True
    assert programs.evaluable(minted) is True, (
        "the minted spelling enters the battery -- which is why the coverage "
        "denominator, not evaluable(), has to be the thing that protects it"
    )
    assert not programs.evaluable(Commitment(id="x", eval="observation")), (
        "the spelling test_formalism_optional_rank.py pins is screened out "
        "before the battery, by a different road"
    )
    verdict, trace = programs.evaluate(
        minted, Harness(tmp_path / "run").create_artifact(
            "prose",
            interface=Interface(commitments=[]),
            provenance=Provenance(role="conjecturer"),
            problem_id=None,
        ), {}
    )
    assert verdict == programs.OVERRUN
    assert trace["reason"] == "observation requires registered evidence"


@pytest.mark.parametrize(
    "battery,expected",
    [
        (["ok"], 1.0),
        (["no"], 0.0),
        (["ok", "no"], 0.5),
        (["ok", "pend1"], 1.0),
        (["no", "pend1"], 0.0),
        (["ok", "no", "pend1", "pend2"], 0.5),
        (["pend1"], None),
        (["pend1", "pend2", "pend3"], None),
    ],
)
def test_coverage_is_passes_over_what_was_actually_decided(tmp_path, battery, expected):
    """The whole rule as a table. `None` means the key is OMITTED — nothing
    was decided, so there is no denominator and no coordinate."""
    harness, ids = _root(tmp_path, {"a": battery})
    assert _coverage(harness, ids["a"]) == expected
