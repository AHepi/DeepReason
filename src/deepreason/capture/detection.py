"""Capture detection (spec §11.3) — Measure-rule replay programs over the log.

All metrics are deterministic functions of the log (embedder raws logged).
Windows of CAPTURE_W cycles; flags are CONJUNCTIONS with hysteresis.

Generator surface: mean pairwise embedding distance + slope; near-miss rate
at the anti-relapse gate; min inter-school centroid distance; optional
effective rank of window embedding covariance.

Adjudicator surface (graph-native): attack-target entropy; criticism debt;
G-churn; reinstatement rate (band, not floor); validity-node attack rate.

Grounding ratio lambda: program/observation vs rubric verdict fraction;
evidence entry rate; exogenous-anchor bottoming fraction. LAMBDA_FLOOR is
the closed-loop alarm line.

Honest limit (§17): detects STALLED dynamics, not wrong-but-stable ones.
"""


def generator_metrics(log, window: int) -> dict:
    raise NotImplementedError


def adjudicator_metrics(log, window: int) -> dict:
    raise NotImplementedError


def grounding_lambda(log, window: int) -> float:
    raise NotImplementedError


def flags(log, config) -> dict:
    """lineage-stagnation | school-convergence | adjudication-ritual |
    grounding-decay, each a conjunction with hysteresis. TODO(P2)."""
    raise NotImplementedError
