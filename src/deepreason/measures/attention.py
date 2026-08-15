"""Attention measures — quantities about WHERE work went, never about truth.

Every function here is a pure function of replayed state (or of the caller's
own bounded selection history) and feeds the signal registry only. Allocation
touches efficiency, never evidence (`DR-INV-signal-contract`, FROZEN layer):
nothing computed in this module may reach a `Status`, a warrant, or an edge.
"""

import math


def problem_thrash(selections) -> float:
    """Fraction of consecutive work units that changed subject.

    0.0 = every unit stayed on the same problem (depth); 1.0 = every unit
    moved (scatter). Fewer than two observations is not a rate, and 0.0 is the
    honest reading of "nothing has moved yet".
    """
    window = list(selections)
    if len(window) < 2:
        return 0.0
    changes = sum(1 for a, b in zip(window, window[1:]) if a != b)
    return changes / (len(window) - 1)


def attack_target_entropy(state) -> float:
    """Normalised Shannon entropy of the standing attacks over their targets.

    1.0 = criticism is spread evenly across everything it has touched; near 0
    = it is concentrated on one target. Normalised by log(k) so runs with
    different target counts are comparable; a single attacked target has no
    dispersion to report and scores 0.0.
    """
    counts: dict[str, int] = {}
    for _, target in state.att:
        counts[target] = counts.get(target, 0) + 1
    total = sum(counts.values())
    if total == 0 or len(counts) < 2:
        return 0.0
    entropy = -sum(
        (n / total) * math.log(n / total) for n in counts.values()
    )
    return entropy / math.log(len(counts))
