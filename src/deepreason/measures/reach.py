"""Reach (spec §6, Def 3.7).

Periodic budgeted cross-evaluation of accepted artifacts against OTHER
problems' evaluable criteria; a hit raises standing (state.reach, via a
Measure event) and Spawns an explanation-debt problem. Reach tracks
coupling (Prop 4.1) — an attackable modelling commitment, not a proven
bound. The event log timestamps what an artifact was built for, so
"accounts for something it wasn't built for" is verifiable in the trace.
"""

from deepreason import programs
from deepreason.ontology.state import Status


def reach_sweep(harness) -> list[tuple[str, str]]:
    """Returns (artifact, foreign_problem) hits; records reach counts."""
    addressed: dict[str, set[str]] = {}
    for aid, pid in harness.state.addr:
        addressed.setdefault(aid, set()).add(pid)
    hits: list[tuple[str, str]] = []
    reach_counts: dict[str, float] = {}
    for aid, status in harness.state.status.items():
        if status != Status.ACCEPTED or aid not in addressed:
            continue
        artifact = harness.state.artifacts[aid]
        count = 0
        carried = set(artifact.interface.commitments)
        for pid, problem in harness.state.problems.items():
            if pid in addressed[aid]:
                continue
            criteria = [
                c for c in problem.criteria
                if c in harness.commitments and programs.evaluable(harness.commitments[c])
            ]
            # Reach means passing criteria it was NOT built for: at least one
            # foreign criterion must be novel to the artifact's own battery.
            if not criteria or not (set(criteria) - carried):
                continue
            if all(
                programs.evaluate(harness.commitments[c], artifact, harness.blobs)[0]
                == programs.PASS
                for c in criteria
            ):
                hits.append((aid, pid))
                count += 1
        if count and harness.state.reach.get(aid) != float(count):
            reach_counts[aid] = float(count)
    if reach_counts:
        harness.record_measure(reach=reach_counts, inputs=sorted(reach_counts))
    return hits
