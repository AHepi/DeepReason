"""Did this cycle's criticism actually run in full, or was it cut short?

The reading in `deepreason.views.evidence_states` needs to tell two situations
apart that look identical on today's record: an artifact nothing warranted was
ever brought against BECAUSE the critics looked and found nothing, and one
nothing was brought against because the critics never got to it. Only the first
is evidence. Without a declaration, both read as ignorance, which is why the
reader leaves an un-attacked artifact OPEN unless a pass that ran in full names
it.

This module is the declaration: the signal name, the closed outcome vocabulary,
and the one writer. It rides `Harness.record_measure`, the existing notice
channel — a measure "steers attention, never status", which is exactly what a
statement about how the run behaved is. No new record object kind, and
therefore no contact with the harness's frozen event application.

It is deliberately separate from the reader. The scheduler emits from here; the
reader reads from here; neither imports the other, which is what lets
`tests/test_evidence_states_law_line.py` forbid the deciding packages from
naming the reading at all.
"""

from __future__ import annotations

from typing import Iterable

CRITICISM_DISPATCH_SIGNAL = "criticism.dispatch.v1"

# The only outcome that licenses reading an ABSENCE of attack as evidence.
OUTCOME_COMPLETE = "complete"

# Every way a criticism pass can end short, one member per branch that exists
# in `Scheduler._arg_crit` / `_foreign_arg_crit`. CLOSED on purpose: a future
# road that ends the pass some other way has to add a member here rather than
# inherit `complete` by silence, which would license an absence nobody measured.
OUTCOME_CUT_BUDGET = "cut:budget"    # ARG_CRIT_PER_CYCLE truncated the targets
OUTCOME_CUT_SEAT = "cut:seat"        # no argumentative critic role was available
OUTCOME_CUT_CALL = "cut:call"        # a batch call was dropped before it was made
OUTCOME_CUT_FOREIGN = "cut:foreign"  # the manifest road, which this does not measure

OUTCOMES = (
    OUTCOME_COMPLETE,
    OUTCOME_CUT_BUDGET,
    OUTCOME_CUT_SEAT,
    OUTCOME_CUT_CALL,
    OUTCOME_CUT_FOREIGN,
)


def declare_criticism_dispatch(
    harness,
    *,
    cycle: int | str,
    outcome: str,
    planned: int,
    dispatched: int,
    targets: Iterable[str] = (),
) -> None:
    """File one pass's declaration. Positional grammar, read back by
    `views.evidence_states`:

        [signal, cycle, outcome, planned, dispatched, *dispatched_target_ids]

    The target ids ride the declaration because a reader holding only a cycle
    number would have to guess which artifacts that cycle's criticism actually
    looked at. Naming them makes the licence exact: an artifact is licensed only
    if a pass that ran in full names it.
    """

    if outcome not in OUTCOMES:
        raise ValueError(f"unknown criticism dispatch outcome: {outcome!r}")
    harness.record_measure(
        inputs=[
            CRITICISM_DISPATCH_SIGNAL,
            str(cycle),
            outcome,
            str(planned),
            str(dispatched),
            *(str(target) for target in targets),
        ]
    )
