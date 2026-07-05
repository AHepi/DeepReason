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


def _verdict(harness, cid: str, aid: str, artifact) -> str:
    """Cached verdict for the (commitment, artifact) pair. Both are
    immutable and content-addressed, and verdicts are deterministic pure
    functions (§0), so the sweep re-evaluating every pair every cycle was
    pure waste (measured O(artifacts x problems x criteria) per cycle)."""
    key = (cid, aid)
    v = harness._verdict_cache.get(key)
    if v is None:
        v = programs.evaluate(harness.commitments[cid], artifact, harness.blobs)[0]
        harness._verdict_cache[key] = v
    return v


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
            if all(_verdict(harness, c, aid, artifact) == programs.PASS for c in criteria):
                hits.append((aid, pid))
                count += 1
        # Record whenever reach changed — including a drop back to zero, so a
        # once-reaching artifact that no longer reaches is cleared rather than
        # ranked forever on a stale count (frontier scoring, explanation-debt).
        # Default stored to 0.0 so never-reached artifacts don't log noise.
        if float(count) != harness.state.reach.get(aid, 0.0):
            reach_counts[aid] = float(count)
    if reach_counts:
        harness.record_measure(reach=reach_counts, inputs=sorted(reach_counts))
    return hits
