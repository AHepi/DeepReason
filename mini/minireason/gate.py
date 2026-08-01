"""Process-only gate-block and orbit analytics for MiniReason.

Admission is deliberately absent from this module.  MiniReason delegates
every refuted-relapse decision to :mod:`deepreason.rules.guards.anti_relapse`
through ``Session.admit_candidate``; keeping a second approximation here once
made the two engine profiles disagree about battery equivalence and counter-
warrants.  Gate refusals still use the parent's ``gate:<reason>`` Measure
format, so these analytics and the parent's detection/invariant tooling read
the same replayable process record.
"""

import re


def gate_blocks(events, window: int = 20) -> list[str]:
    """gate:<reason> inputs across the recent event window."""
    return [
        i
        for e in events[-window:]
        for i in e.inputs
        if isinstance(i, str) and i.startswith("gate:")
    ]


def orbit(events, artifacts: dict[str, dict], window: int = 20, floor: int = 5) -> str | None:
    """Refuted-attractor orbiting: gate-block rate over the window reaches
    the floor => return the school (stance) whose refuted attractor is being
    orbited — majority school across the refuted targets named by the
    blocks, deterministic tiebreak. None => healthy (measured rate: exactly
    zero in every healthy arm; 4.3x token burn when ignored)."""
    blocks = gate_blocks(events, window)
    if len(blocks) < floor:
        return None
    counts: dict[str, int] = {}
    for reason in blocks:
        # Both refusal shapes name the refuted prior: the parent's detector
        # matches the "to refuted <id>" form; hash relapses count here too.
        m = re.search(r"(?:to refuted|hash:) ([0-9a-f]{8,})", reason)
        if not m:
            continue
        prefix = m.group(1)
        for aid, a in artifacts.items():
            school = (a.get("provenance") or {}).get("school")
            if aid.startswith(prefix) and school:
                counts[school] = counts.get(school, 0) + 1
                break
    if not counts:
        return None
    return max(sorted(counts), key=lambda s: counts[s])
