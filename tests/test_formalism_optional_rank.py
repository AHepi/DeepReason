"""Rank is blind to conjecture KIND on the Pareto axes (§11.7).

Regression (2026-08-27 audit finding F1; live root
experiments/2026-08-12-live-grounded-extension-expansion/run, where 146 of 233
survivors carried no evaluable commitment, scored coverage 0.0, and every one
of them was dominated off the published frontier by one of the 87 that did):
`run_report` wrote 0.0 on the `coverage` axis for an artifact with nothing to
check, `capture.pareto.frontier` maximises every axis, and a formally-backed
sibling therefore dominated an otherwise-equal prose one.

The law, verbatim (docs/proposals/DUAL_MODE_CONJECTURE_PREPLAN.md R-g:42-57):
"Formal backing may confer PROTECTION (prose-immunity, as today); its absence
confers no disadvantage."

No status is hand-set in any test here: every artifact is unattacked, so the
harness's own grounded-extension pass labels it ACCEPTED and `run_report`'s own
survivor predicate admits it.
"""

import pytest

from deepreason.capture.pareto import frontier
from deepreason.config import Config
from deepreason.harness import Harness
from deepreason.ontology import (
    Commitment,
    Interface,
    Problem,
    Provenance,
    SpawnTrigger,
)
from deepreason.ontology.problem import ProblemProvenance
from deepreason.scheduler.scheduler import pareto_scores, run_report

PASSING = "predicate:len(content) > 0"
FAILING = "predicate:len(content) > 10**9"

# Which Pareto axes can a survivor carrying no evaluable commitment reach the
# MINIMUM of, as an EMITTED score rather than an omission?
#
# A new axis added to PARETO_AXES fails `test_architecture_...` below until it
# is annotated here, which forces the question R-g asks to be answered before
# the axis ships: can an artifact reach this axis's floor merely by declining
# to formalise? If yes, `pareto_scores` must OMIT the key (not-measured) rather
# than emit the floor, or a formally-backed sibling dominates on it.
#
# hv and reach are True and are NOT repaired here: the 2026-08-27 audit rowed
# both STRUCTURAL-GAP rather than unlawful, and in both roots measured on
# 2026-08-30 they are 0.0 for every survivor of both kinds, so no penalty is
# reachable through them in any committed record. See
# experiments/2026-08-30-defect-formalism-rank-penalty/PARKED.md L3.
COMMITMENT_FREE_CAN_REACH_THE_FLOOR = {
    "hv": True,
    "reach": True,
    "coverage": False,
}


def _root(tmp_path, batteries: dict[str, list[str]]) -> tuple[Harness, dict[str, str]]:
    harness = Harness(tmp_path / "run")
    harness.register_commitment(Commitment(id="ok", eval=PASSING))
    harness.register_commitment(Commitment(id="no", eval=FAILING))
    harness.register_commitment(
        Commitment(id="obs", eval="observation", observation_valued=True)
    )
    problem = harness.register_problem(
        Problem(
            id="p1",
            description="a problem",
            criteria=["ok", "no", "obs"],
            provenance=ProblemProvenance(trigger=SpawnTrigger.SEED),
        )
    )
    ids = {}
    for label, commitments in batteries.items():
        artifact = harness.create_artifact(
            f"a conjecture, written as {label}",
            interface=Interface(commitments=list(commitments)),
            provenance=Provenance(role="conjecturer"),
            problem_id=problem.id,
        )
        ids[label] = artifact.id
    return harness, ids


def _frontier(harness, ids) -> list[str]:
    by_id = {v: k for k, v in ids.items()}
    report = run_report(harness, Config())
    assert sorted(report["survivors"]) == sorted(ids.values()), "setup: all must survive"
    return sorted(by_id[aid] for aid in report["frontier"])


def test_informal_and_formal_of_equal_standing_rank_equally(tmp_path):
    """The law itself. Two survivors on one problem, equal on every axis the
    harness measured for both; one carries a passing evaluable commitment and
    one carries only an observational criterion."""
    harness, ids = _root(tmp_path, {"formal": ["ok"], "prose": ["obs"]})
    assert _frontier(harness, ids) == ["formal", "prose"]


def test_control_a_prose_artifact_given_a_battery_also_ranks(tmp_path):
    """MUTATION CONTROL A. Change exactly one thing — give the prose artifact a
    passing evaluable commitment — and it must still rank. Without this control
    the test above would also pass if prose were being kept for some reason
    that has nothing to do with the coverage axis."""
    harness, ids = _root(tmp_path, {"formal": ["ok"], "prose": ["ok"]})
    assert _frontier(harness, ids) == ["formal", "prose"]


def test_control_b_a_failed_battery_is_still_dominated(tmp_path):
    """MUTATION CONTROL B, and what separates a lawful repair from "put
    everyone on the frontier": an artifact that WAS checked and failed must
    still be dominated by an equal one that was checked and passed. "Nothing to
    check" and "checked and failed" must not share a coordinate — the
    operator's own question at experiments/2026-08-27-audit-formalism-optional/
    PARKED.md:73-77."""
    harness, ids = _root(tmp_path, {"passed": ["ok"], "failed": ["no"]})
    assert _frontier(harness, ids) == ["passed"]


def test_a_partly_passing_battery_is_not_out_ranked_by_nothing_to_check(tmp_path):
    """The reverse-direction weight R-g also forbids ("may weight ranking ...
    on a conjecture's KIND" is direction-neutral). Scoring an empty battery at
    a neutral 1.0 instead of omitting it would make the prose artifact dominate
    the partly-passing formal one; omitting it makes them incomparable."""
    harness, ids = _root(tmp_path, {"partial": ["ok", "no"], "prose": ["obs"]})
    assert _frontier(harness, ids) == ["partial", "prose"]


def test_kind_blindness_prose_ranks_the_same_with_and_without_a_formal_channel(
    tmp_path,
):
    """R-g's proof standard: "an informal conjecture's rank ... byte-identical
    whether or not the formal channel exists in the build". Same prose
    artifact, same problem; only the siblings' batteries differ."""
    with_channel, ids_with = _root(
        tmp_path / "with", {"pass": ["ok"], "partial": ["ok", "no"], "prose": ["obs"]}
    )
    without_channel, ids_without = _root(
        tmp_path / "without", {"pass": ["obs"], "partial": ["obs"], "prose": ["obs"]}
    )
    assert "prose" in _frontier(with_channel, ids_with)
    assert "prose" in _frontier(without_channel, ids_without)


def test_architecture_every_pareto_axis_declares_its_commitment_free_state():
    """ARCHITECTURE. A new Pareto axis cannot ship without someone deciding
    whether an artifact can reach its floor by carrying no commitment. Adding a
    name to Config.PARETO_AXES turns this red until it is annotated above."""
    assert set(Config().PARETO_AXES) == set(COMMITMENT_FREE_CAN_REACH_THE_FLOOR)


def test_architecture_axes_that_must_not_be_zeroed_are_omitted_instead(tmp_path):
    """ARCHITECTURE, the enforcing half: every axis annotated False must be
    ABSENT from a commitment-free survivor's scores (not-measured), and every
    axis annotated True must be present. An axis that is neither is
    unannotated, which the test above already caught."""
    harness, ids = _root(tmp_path, {"prose": ["obs"]})
    scores = pareto_scores(harness, ids["prose"])
    for axis, reachable in COMMITMENT_FREE_CAN_REACH_THE_FLOOR.items():
        assert (axis in scores) is reachable, (axis, scores)


@pytest.mark.parametrize(
    "scored,expected",
    [
        # An axis absent from either point leaves that comparison entirely.
        ([("a", {"hv": 1.0}), ("b", {"reach": 1.0})], ["a", "b"]),
        # Points sharing no axis at all never dominate — this is what keeps
        # loop.py's P1 report (every survivor scored `{}`) equal to its
        # survivor set.
        ([("a", {}), ("b", {}), ("c", {})], ["a", "b", "c"]),
        # A shared axis still discriminates normally.
        ([("a", {"hv": 1.0}), ("b", {"hv": 0.0})], ["a"]),
        # Present-and-equal on the shared axis, absent elsewhere: neither wins.
        ([("a", {"hv": 1.0, "coverage": 1.0}), ("b", {"hv": 1.0})], ["a", "b"]),
    ],
)
def test_frontier_treats_a_missing_score_as_not_measured(scored, expected):
    assert sorted(frontier(scored, ["hv", "reach", "coverage"])) == expected
