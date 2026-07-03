"""Pareto retention (spec §11.7) — attention and reporting only.

Scheduler focus and reports keep the Pareto frontier over PARETO_AXES
(default: HV_B, reach, criteria-coverage) instead of argmax-HV. Never a
status: an artifact off the frontier is merely unfunded, not demoted.
"""


def frontier(candidates: list, axes: list[str]) -> list:
    """Non-dominated set over the configured axes. TODO(P2)."""
    raise NotImplementedError
