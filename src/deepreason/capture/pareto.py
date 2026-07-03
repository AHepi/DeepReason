"""Pareto retention (spec §11.7) — attention and reporting only.

Scheduler focus and reports keep the Pareto frontier over PARETO_AXES
(default: HV_B, reach, criteria-coverage) instead of argmax-HV. Never a
status: an artifact off the frontier is merely unfunded, not demoted.
"""


def frontier(scored: list[tuple[object, dict[str, float]]], axes: list[str]) -> list[object]:
    """Non-dominated set (maximizing every axis; missing scores are 0)."""

    def dominates(a: dict[str, float], b: dict[str, float]) -> bool:
        return all(a.get(x, 0.0) >= b.get(x, 0.0) for x in axes) and any(
            a.get(x, 0.0) > b.get(x, 0.0) for x in axes
        )

    return [
        item
        for item, scores in scored
        if not any(dominates(other, scores) for _, other in scored)
    ]
