"""Reach (spec §6, Def 3.7, as amended).

Reach is CROSS-PROBLEM SURVIVAL, never textual reference: an artifact built
for one problem also survives the commitments of another problem it was not
written to address. That enlarges its attack surface — more places to be
refuted, more unified if it stands — and (normative amendment, approved) a
FULL hit registers the artifact as ADDRESSING the foreign problem, recorded
in the Measure event's addr_add so replay applies it.

Discipline (the Bronze Age postmortem): no reach from an empty, trivial, or
unguarded battery.

  - QUALIFYING commitments are evaluable AND substantive: structural
    well-formedness programs (json-wf, skeleton_wf, lineage_ref, checker_wf)
    qualify anything well-formed and prove nothing about the foreign
    problem's subject — they never ground reach.
  - A hit requires passing EVERY qualifying foreign criterion, at least one
    of which is novel to the artifact's own battery.
  - COVERAGE: qualifying criteria must cover at least ``coverage_min`` of
    the foreign problem's total criteria. Below that the hit is PROVISIONAL
    — logged (reach-provisional) for attention and later re-evaluation, but
    it grounds no reach count, no addressing, and no explanation debt.
    Rubric criteria count toward the total but are not machine-evaluated
    here, so rubric-heavy problems yield provisional hits until their
    guarded procedures (trials, holdouts, audits) put survivals on the
    record.

The event log timestamps what an artifact was built for, so "accounts for
something it wasn't built for" stays verifiable in the trace.
"""

from deepreason import programs
from deepreason.ontology.state import Status

# Structural well-formedness programs: passing them says the CONTENT IS
# WELL-FORMED, not that it answers the problem — they can never carry reach.
_STRUCTURAL_PROGRAMS = frozenset(
    {"json-wf", "skeleton_wf", "lineage_ref", "checker_wf"}
)


def _substantive(commitment) -> bool:
    if not programs.evaluable(commitment):
        return False
    kind, _, arg = commitment.eval.partition(":")
    return not (kind == "program" and arg in _STRUCTURAL_PROGRAMS)


def _verdict(harness, cid: str, aid: str, artifact) -> str:
    """Cached verdict for the (commitment, artifact) pair. Both are
    immutable and content-addressed, and verdicts are deterministic pure
    functions (§0), so the sweep re-evaluating every pair every cycle was
    pure waste (measured O(artifacts x problems x criteria) per cycle)."""
    key = (cid, aid)
    v = harness._verdict_cache.get(key)
    if v is None:
        v, trace = programs.evaluate(harness.commitments[cid], artifact, harness.blobs)
        # A subprocess resource kill is explicitly not an epistemic verdict.
        # Retrying later is legal; caching the API's overrun envelope would
        # silently turn machine availability into graph semantics.
        if "sandbox_abort" not in trace:
            harness._verdict_cache[key] = v
    return v


def reach_sweep(harness, coverage_min: float = 0.5) -> list[tuple[str, str]]:
    """Returns FULL (artifact, foreign_problem) hits; records reach counts
    and registers full hits as addressing (addr_add). Provisional hits are
    measured but ground nothing."""
    addressed: dict[str, set[str]] = {}
    for aid, pid in harness.state.addr:
        addressed.setdefault(aid, set()).add(pid)
    hits: list[tuple[str, str]] = []
    provisional: list[tuple[str, str]] = []
    reach_counts: dict[str, float] = {}
    addr_new: list[tuple[str, str]] = []
    for aid, status in harness.state.status.items():
        if status != Status.ACCEPTED or aid not in addressed:
            continue
        artifact = harness.state.artifacts[aid]
        count = 0
        carried = set(artifact.interface.commitments)
        for pid, problem in harness.state.problems.items():
            if pid in addressed[aid] or not problem.criteria:
                continue
            qualifying = [
                c for c in problem.criteria
                if c in harness.commitments and _substantive(harness.commitments[c])
            ]
            # Reach means passing criteria it was NOT built for: at least one
            # qualifying foreign criterion must be novel to its own battery.
            if not qualifying or not (set(qualifying) - carried):
                continue
            if not all(
                _verdict(harness, c, aid, artifact) == programs.PASS
                for c in qualifying
            ):
                continue
            if len(qualifying) / len(problem.criteria) < coverage_min:
                provisional.append((aid, pid))
                continue
            hits.append((aid, pid))
            addr_new.append((aid, pid))
            count += 1
        # Record whenever reach changed — including a drop back to zero, so a
        # once-reaching artifact that no longer reaches is cleared rather than
        # ranked forever on a stale count (frontier scoring, explanation-debt).
        # Default stored to 0.0 so never-reached artifacts don't log noise.
        if float(count) != harness.state.reach.get(aid, 0.0):
            reach_counts[aid] = float(count)
    if reach_counts or addr_new:
        harness.record_measure(
            reach=reach_counts, addr=addr_new,
            inputs=sorted(set(list(reach_counts) + [a for a, _ in addr_new])),
        )
    for aid, pid in provisional:
        harness.record_measure(inputs=["reach-provisional", aid, pid])
    return hits
