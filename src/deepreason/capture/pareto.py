"""Pareto retention (spec §11.7) — attention and reporting only.

Scheduler focus and reports keep the Pareto frontier over PARETO_AXES
(default: HV_B, reach, criteria-coverage) instead of argmax-HV. Never a
status: an artifact off the frontier is merely unfunded, not demoted.
"""


def frontier(scored: list[tuple[object, dict[str, float]]], axes: list[str]) -> list[object]:
    """Non-dominated set (maximizing every axis; a missing score is NOT
    MEASURED, never zero).

    An axis absent from EITHER point leaves that pairwise comparison, so an
    artifact the harness never measured on an axis neither loses nor wins
    there. Defaulting a missing score to 0.0 makes "not measured"
    indistinguishable from "measured at the floor", which on the coverage axis
    weights rank on conjecture KIND: an artifact carrying no evaluable
    commitment has nothing to divide, and scoring it at the floor lets a
    formally-backed sibling dominate it — forbidden by
    DUAL_MODE_CONJECTURE_PREPLAN.md R-g, "its absence confers no disadvantage".

    Two points sharing no axis therefore never dominate each other, which is
    what keeps `loop.py`'s P1 frontier — every survivor scored `{}` — equal to
    the survivor set.
    """

    def dominates(a: dict[str, float], b: dict[str, float]) -> bool:
        shared = [x for x in axes if x in a and x in b]
        return (
            bool(shared)
            and all(a[x] >= b[x] for x in shared)
            and any(a[x] > b[x] for x in shared)
        )

    return [
        item
        for item, scores in scored
        if not any(dominates(other, scores) for _, other in scored)
    ]
