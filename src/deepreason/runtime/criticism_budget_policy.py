"""What a run does with a criticism batch its token budget refuses.

One refused batch used to end the whole run. Its sibling road — the
foreign-school one — already absorbed the same refusal, recorded a typed
coverage debt and carried on, so the two roads disagreed about whether a
budget refusal is a local event or a death (parked P1,
`experiments/2026-09-06-defect-budget-exhausted-classification/PARKED.md`).

This module is the choice, made once and made as CONFIGURATION: the closed
value set, the default, and the one resolver every consumer asks. It decides
nothing about a SPENT ceiling — a refusal on an exhausted budget still ends
the run cleanly as `budget_exhausted`, which is the operator's law of
2026-08-29 and is deliberately not switchable. What varies here is only what
happens when the budget could still have afforded the work.

Shaped on `runtime/seat_retirement.py`: an unknown id falls back to the
shipped default and discloses rather than refusing, which is the
all-configurations law (2026-08-12) applied to a policy selector.
"""

from __future__ import annotations

# Re-plan the refused work into calls the remaining budget CAN cover: halve
# the batch and try again, down to single targets, dropping only what still
# will not fit. The setting that does the most work with money the run
# already has.
POLICY_SHRINK = "shrink-the-batch.v1"

# Drop the refused batch whole and carry on, leaving those tokens for later
# cycles.
POLICY_DROP = "drop-the-batch.v1"

# The behaviour before P1 was fixed: one refused batch ends the run. Kept
# reachable because a gate is always switchable (the ungated-seats law,
# 2026-08-28), and warned about because switching one is never silent.
POLICY_STOP = "stop-the-run"

CRITICISM_BUDGET_POLICIES = (POLICY_SHRINK, POLICY_DROP, POLICY_STOP)
DEFAULT_CRITICISM_BUDGET_POLICY = POLICY_SHRINK

STOP_SIGNAL = "criticism.budget-stop-the-run.v1"

# The warning text the ungated-seats law requires when a gate is switched to
# the setting that can kill a run.
STOP_WARNING = (
    "criticism budget denial is set to stop the run: one criticism batch the "
    "token budget refuses will end the whole run, including a run whose "
    "budget could still afford smaller work"
)


def resolve_policy(config) -> tuple[str, str | None]:
    """(policy id, id it fell back from). Never raises, never refuses."""

    requested = str(getattr(config, "CRITICISM_BUDGET_DENIAL_POLICY", None) or "")
    if requested in CRITICISM_BUDGET_POLICIES:
        return requested, None
    return DEFAULT_CRITICISM_BUDGET_POLICY, (requested or None)


def split_batch(batch: tuple[str, ...]) -> tuple[tuple[str, ...], ...]:
    """Halve a refused batch, or return () when there is nothing left to halve.

    A single target cannot be made smaller, so an empty result is the caller's
    signal to drop rather than to try again — which is what bounds the retry:
    every refusal either halves the batch or ends it.
    """

    if len(batch) < 2:
        return ()
    half = len(batch) // 2
    return (batch[:half], batch[half:])
