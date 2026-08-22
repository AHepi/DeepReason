"""Reach (spec §6, Def 3.7, as amended).

Reach is CROSS-PROBLEM SURVIVAL, never textual reference: an artifact built
for one problem also survives the commitments of another problem it was not
written to address. That enlarges its attack surface — more places to be
refuted, more unified if it stands — and (normative amendment, approved) a
FULL hit registers the artifact as ADDRESSING the foreign problem, recorded
in the Measure event's addr_add so replay applies it.

Discipline (the Bronze Age postmortem): no reach from an empty, trivial, or
unguarded battery. That sentence governs BOTH batteries -- the foreign one a
pair must survive, and the reaching artifact's own (E0).

Each (artifact, foreign problem) pair takes exactly one of SEVEN exits, and
``reach_sweep`` takes them in this order. All six rejections are listed
because a reader who knows only some of them misattributes the rest: a census
over 96 committed roots put 285 070 of 1 178 430 pairs at E1 and 585 096 at
E4, the two that went undocumented longest
(``experiments/2026-08-21-measure-reach-firing/CENSUS.md``).

  - **E0 empty-own-battery** — the reaching artifact declares no commitments
    of its own, so it forbids nothing and earns no promotion signal. This is
    the Bronze Age discipline applied to the reaching side, and it is a
    property of the ARTIFACT: every pair it appears in takes this exit
    (operator ruling 2026-08-22,
    ``experiments/2026-08-22-change-reach-p5-rulings``). It is NOT a
    formalism-kind penalty — emptiness of commitments is not informality, and
    nothing outside reach eligibility moves: admission, rank and criticism
    outcomes are untouched.
  - **E1 no-criteria** — the foreign problem declares no criteria at all, so
    there is nothing to survive. Discovery problems spawn this way.
  - **E2 non-qualifying** — no criterion is both evaluable AND substantive.
    QUALIFYING excludes structural well-formedness programs: every program
    `programs.PROGRAMS` declares ``class_="structural"``, which is where this
    module reads the set from, qualifies anything well-formed and proves
    nothing about the foreign problem's subject, so it never grounds reach.
  - **E3 no-novel** — every qualifying criterion is already in the artifact's
    own battery. Reach means surviving what it was NOT built for, so at least
    one qualifying foreign criterion must be novel to it.
  - **E4 criterion-fail** — some qualifying criterion does not PASS. A hit
    requires passing EVERY one of them, so this is where a genuine content
    failure lands, and where a criterion wrongly counted qualifying can veto
    a pair the rest of the battery had already settled.
  - **E5 coverage** — qualifying criteria cover less than ``coverage_min`` of
    the foreign problem's total criteria. The hit is PROVISIONAL: logged
    (reach-provisional) for attention and later re-evaluation, but it grounds
    no reach count, no addressing, and no explanation debt. Rubric criteria
    count toward the total but are not machine-evaluated here, so rubric-heavy
    problems yield provisional hits until their guarded procedures (trials,
    holdouts, audits) put survivals on the record. Coverage exactly EQUAL to
    ``coverage_min`` is a FULL hit, not this exit: a floor means "at least",
    so the comparison is ``<`` deliberately (operator ruling 2026-08-22,
    ``experiments/2026-08-22-change-reach-p5-rulings``).
  - **HIT full** — everything above is cleared: recorded as a reach count and
    as addressing.

The event log timestamps what an artifact was built for, so "accounts for
something it wasn't built for" stays verifiable in the trace.
"""

from deepreason import programs
from deepreason.ontology.state import Status

# Structural well-formedness programs: passing them says the CONTENT IS
# WELL-FORMED, not that it answers the problem -- they can never carry reach.
#
# DERIVED, never hand-listed. A second copy of this set drifted five names
# deep (component_wf, generator_wf, integration_wf, manifest_wf,
# reasoning-envelope-wf declared themselves structural and were still counted
# substantive here), so the registry's own declaration is the single source.
# Every consumer of the class reads the same answer: rules/warrants.py for
# prose immunity, rules/guards/anti_relapse.py for relapse equivalence.
#
# What the class means, program by program, is the reason it is load-bearing
# rather than clerical. presupposition_wf/premise_resolution_wf prove an
# attribution or resolution is WELL FORMED, never that its claim holds.
# frame_assertion_wf is structural for that reason and one more: an artifact
# that could ground reach by being a well-formed frame assertion would let the
# standing axis buy its own promotion case. reasoning-envelope-wf is the seed
# problem's own envelope gate, so counting it substantive let a well-formedness
# check decide -- in either direction -- a reach outcome the subject criteria
# had already settled.
_STRUCTURAL_PROGRAMS = frozenset(programs.programs_by_class()["structural"])


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
            # E0. Loop-INVARIANT on purpose: hoisting it above this loop skips
            # the reach-count accounting below, so an empty-battery artifact
            # holding a stale reach count would stay ranked on it forever.
            if not carried:
                continue
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
            # Strictly LESS THAN: coverage exactly equal to the floor is a
            # FULL hit, because a floor means "at least" (operator ruling
            # 2026-08-22, experiments/2026-08-22-change-reach-p5-rulings).
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
