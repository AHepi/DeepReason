"""Evidence states — a DERIVED reading over the record, never a Status.

Today an admitted conjecture nobody ever attacked and one that beat off a
warranted attack both read as `Status.ACCEPTED`. The operator's success
criterion is "survivors harder to vary, bolder conjectures that survived
criticism" (CLAUDE.md, progress-over-baseline law, 2026-09-03), so the record
has to be able to tell those two apart cheaply. This module is the reader that
does it, over facts already on the record.

Four readings, one per admitted artifact:

    OPEN       nothing warranted has been brought against it, and no trial
               reached a ruling on it
    SUPPORTED  it survived a warranted attack, or a trial ruled and did not
               sustain, or a cycle declared its criticism ran in full and
               brought nothing
    REFUTED    the status label says so
    CONTESTED  evidence both ways

WHAT DOES NOT COUNT. A critic CALL is not criticism for this purpose. The
blind-critic bench of 2026-09-04 measured a critic that attacked every target
it was shown, at rate 1.000 across all four cells
(`experiments/2026-09-04-experiment-blind-critic/RESULTS.md`), so counting
calls would read a saturated instrument as universal survival. Only a
REGISTERED warrant that became an attack edge, or a trial that reached a
ruling, moves an artifact off OPEN.

WHAT THIS READING MAY NOT DO. It decides nothing: no admission, no rank, no
immunity, no refutation. `tests/test_evidence_states_law_line.py` is that
prohibition made falsifiable, and it has an EMPTY permitted-exception list.

Import-role admission records are excluded from the population rather than
given a state — they are admission bookkeeping, never positions that survived
criticism (`deepreason.ontology.state.is_import_admission`).
"""

from __future__ import annotations

from collections import defaultdict
from enum import Enum
from typing import Any

from deepreason.ontology.state import Status, is_import_admission
from deepreason.runtime.criticism_dispatch import (
    CRITICISM_DISPATCH_SIGNAL,
    OUTCOME_COMPLETE,
)

SCHEMA = "deepreason-evidence-states.v1"

# The heartbeat the scheduler stamps at the head of every cycle. Every event
# that follows it, by seq, belongs to that cycle until the next one.
_CYCLE_SIGNAL = "cycle"

# Artifacts registered before the first heartbeat belong to no cycle. They get
# their own bucket rather than being folded into cycle 0, which would state a
# fact the record does not carry.
PRE_CYCLE = "pre-cycle"

# A trial that reached a ruling and did not sustain. `trial-blocked:*` is NOT
# here: a guard stopping a trial is not a trial that ran.
_TRIAL_RULED = ("trial-declined", "trial-observation")

# The one guard outcome that is itself evidence both ways: the judges split.
_TRIAL_SPLIT = "trial-blocked:ensemble-split"


class EvidenceState(str, Enum):
    OPEN = "open"
    SUPPORTED = "supported"
    REFUTED = "refuted"
    CONTESTED = "contested"


class _Record:
    """What one walk of the log found, so the log is walked exactly once."""

    __slots__ = ("ruled", "split", "licensed", "registered_in", "declarations")

    def __init__(self) -> None:
        self.ruled: set[str] = set()
        self.split: set[str] = set()
        self.licensed: set[str] = set()
        self.registered_in: dict[str, str] = {}
        self.declarations: list[dict[str, Any]] = []


def _walk(harness) -> _Record:
    found = _Record()
    cycle = PRE_CYCLE
    for event in harness.log.read():
        inputs = [str(value) for value in (event.inputs or ())]
        for produced in event.outputs or ():
            found.registered_in.setdefault(str(produced), cycle)
        if not inputs:
            continue
        signal = inputs[0]
        if signal == _CYCLE_SIGNAL and len(inputs) > 1:
            cycle = inputs[1]
        elif signal in _TRIAL_RULED and len(inputs) > 1:
            found.ruled.add(inputs[1])
        elif signal == _TRIAL_SPLIT and len(inputs) > 1:
            found.split.add(inputs[1])
        elif signal == CRITICISM_DISPATCH_SIGNAL and len(inputs) >= 5:
            declaration = {
                "cycle": inputs[1],
                "outcome": inputs[2],
                "planned": inputs[3],
                "dispatched": inputs[4],
                "targets": inputs[5:],
            }
            found.declarations.append(declaration)
            if inputs[2] == OUTCOME_COMPLETE:
                found.licensed.update(inputs[5:])
    return found


def evidence_states(harness) -> dict[str, EvidenceState]:
    """One reading per admitted artifact. Reads; never writes, never adjudicates."""

    state = harness.state
    found = _walk(harness)

    attackers: dict[str, set[str]] = defaultdict(set)
    for attacker, target in state.att:
        attackers[target].add(attacker)

    readings: dict[str, EvidenceState] = {}
    for artifact_id in state.artifacts:
        if is_import_admission(state, artifact_id):
            continue
        label = state.status.get(artifact_id)
        against = attackers.get(artifact_id, frozenset())
        # An attacker the graph itself refuted is an attack that did not land:
        # the target survived it, which is the whole point of the reading.
        failed = {a for a in against if state.status.get(a) == Status.REFUTED}
        standing = against - failed
        if label == Status.REFUTED:
            readings[artifact_id] = EvidenceState.REFUTED
        elif (
            artifact_id in found.split
            or (failed and standing)
            or (label == Status.SUSPENDED and against)
        ):
            readings[artifact_id] = EvidenceState.CONTESTED
        elif (
            failed
            or artifact_id in found.ruled
            or (not against and artifact_id in found.licensed)
        ):
            readings[artifact_id] = EvidenceState.SUPPORTED
        else:
            readings[artifact_id] = EvidenceState.OPEN
    return readings


def _completeness(found: _Record) -> dict[str, Any]:
    if not found.declarations:
        return {
            "absent": True,
            "reason": "NO_CRITICISM_DISPATCH_DECLARATION",
            "detail": (
                "nothing on this record says whether any cycle's criticism ran "
                "in full, so no artifact is read as having survived merely "
                "because nothing attacked it"
            ),
        }
    outcomes: dict[str, int] = {}
    for declaration in found.declarations:
        outcome = declaration["outcome"]
        outcomes[outcome] = outcomes.get(outcome, 0) + 1
    return {
        "passes": len(found.declarations),
        "outcomes": dict(sorted(outcomes.items())),
        "complete_passes": outcomes.get(OUTCOME_COMPLETE, 0),
        "licensed_artifacts": len(found.licensed),
    }


def _empty_counts() -> dict[str, int]:
    return {state.value: 0 for state in EvidenceState}


def evidence_state_summary(harness) -> dict[str, Any]:
    """The reading as a JSON-stable section, for `results` and `stop-report`."""

    found = _walk(harness)
    readings = evidence_states(harness)
    state = harness.state

    counts = _empty_counts()
    per_cycle: dict[str, dict[str, int]] = {}
    for artifact_id, reading in readings.items():
        counts[reading.value] += 1
        cycle = found.registered_in.get(artifact_id, PRE_CYCLE)
        per_cycle.setdefault(cycle, _empty_counts())[reading.value] += 1

    excluded = sum(
        1 for artifact_id in state.artifacts if is_import_admission(state, artifact_id)
    )
    return {
        "schema": SCHEMA,
        "counts": counts,
        "per_cycle": {key: per_cycle[key] for key in sorted(per_cycle, key=_cycle_key)},
        "excluded_import_admissions": excluded,
        "completeness": _completeness(found),
    }


def _cycle_key(cycle: str) -> tuple[int, int, str]:
    """Order the pre-cycle bucket first, then cycles numerically."""

    if cycle == PRE_CYCLE:
        return (0, 0, "")
    try:
        return (1, int(cycle), "")
    except ValueError:
        return (2, 0, cycle)


def frontier_column(readings: dict[str, EvidenceState], artifact_ids) -> list[str]:
    """One reading per frontier id, in the order given. An id with no reading
    (import bookkeeping, or an id the replay never registered) prints as `-`
    rather than being dropped, so the column and the listing stay aligned."""

    return [
        readings[artifact_id].value if artifact_id in readings else "-"
        for artifact_id in artifact_ids
    ]
