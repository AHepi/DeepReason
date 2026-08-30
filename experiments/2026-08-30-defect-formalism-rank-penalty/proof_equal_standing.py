"""THE DEFECT'S PROOF: an informal conjecture and a formal one of equal
standing do not rank equally.

The law, verbatim (docs/proposals/DUAL_MODE_CONJECTURE_PREPLAN.md R-g:42-57):
"Formal backing may confer PROTECTION (prose-immunity, as today); its absence
confers no disadvantage."

This script is deliberately NOT a pytest file. It asserts behaviour the tree
does not have, so as a collected test it would be RED, and 0 failed is the
only acceptable gate result. As a script under this tranche directory it is
outside the gate's collection path in BOTH states and reports a typed verdict
either way:

    VERDICT: PENALTY_PRESENT    exit 0   -- the defect reproduced
    VERDICT: PENALTY_ABSENT     exit 1   -- the tree ranks them equally
    VERDICT: INSTRUMENT_BROKEN  exit 2   -- a control failed; believe nothing

Run:  python experiments/2026-08-30-defect-formalism-rank-penalty/proof_equal_standing.py

Four legs, three of them controls, so the verdict cannot be right by accident:

  LEG 1  THE ASSERTION. Two survivors on one problem, unattacked, both
         labelled ACCEPTED by the harness's own grounded-extension pass, equal
         on every axis the harness actually measured for both. One carries a
         PASSING evaluable commitment; the other carries only an observational
         one. Both must be on `run_report`'s frontier.

  LEG 2  MUTATION CONTROL A (must hold on EVERY tree). Change exactly one
         thing -- give the prose artifact a passing evaluable commitment of
         its own -- and the exclusion must disappear. Without this, leg 1
         would also "reproduce" if the prose artifact were being dropped for
         a reason having nothing to do with the coverage axis.

  LEG 3  MUTATION CONTROL B (must hold on EVERY tree). An artifact whose
         evaluable battery FAILS must still be dominated by an equal artifact
         whose battery passes. This is what separates a lawful repair from
         "put everyone on the frontier": a road that destroys the axis rather
         than repairing it fails here.

  LEG 4  SIMULATED FIX. Re-score the SAME real artifacts from leg 1 under
         road (a)'s rule -- a commitment-free artifact emits no `coverage`
         key, and an axis absent from either point leaves that pairwise
         comparison -- and the exclusion must be gone. This is the
         instrument's own mutation proof: it shows the script reacts to a
         fix instead of reporting PENALTY_PRESENT unconditionally.
"""

import json
import sys
import tempfile

PASSING = "predicate:len(content) > 0"
FAILING = "predicate:len(content) > 10**9"


def _root(commitments_by_label):
    """Build a real root with the ordinary public constructors.

    `commitments_by_label` maps a label to the commitment ids that label's
    artifact declares. No status is hand-set anywhere: every artifact is
    unattacked, so the harness's own grounded-extension pass labels it
    ACCEPTED.
    """
    from deepreason.harness import Harness
    from deepreason.ontology import (
        Commitment, Interface, Problem, Provenance, SpawnTrigger,
    )
    from deepreason.ontology.problem import ProblemProvenance

    harness = Harness(tempfile.mkdtemp(prefix="equal-standing-"))
    harness.register_commitment(Commitment(id="ok", eval=PASSING))
    harness.register_commitment(Commitment(id="no", eval=FAILING))
    harness.register_commitment(
        Commitment(id="obs", eval="observation", observation_valued=True)
    )
    problem = harness.register_problem(
        Problem(
            id="p1",
            description="a problem",
            criteria=["ok", "no", "obs"],
            provenance=ProblemProvenance(trigger=SpawnTrigger.SEED),
        )
    )
    ids = {}
    for label, commitments in commitments_by_label.items():
        artifact = harness.create_artifact(
            f"a conjecture, written as {label}",
            interface=Interface(commitments=list(commitments)),
            provenance=Provenance(role="conjecturer"),
            problem_id=problem.id,
        )
        ids[label] = artifact.id
    return harness, ids


def _frontier_labels(harness, ids):
    from deepreason.config import Config
    from deepreason.scheduler.scheduler import run_report

    report = run_report(harness, Config())
    by_id = {v: k for k, v in ids.items()}
    return sorted(by_id[aid] for aid in report["frontier"] if aid in by_id), report


def _statuses(harness, ids):
    status = harness.state.status
    return {
        label: (status.get(aid).value if status.get(aid) else None)
        for label, aid in ids.items()
    }


def _road_a_labels(harness, ids):
    """Road (a) applied to the SAME artifacts, without touching src/.

    Scores each survivor from its own real battery exactly as `run_report`
    does, except that an empty evaluable battery emits NO `coverage` key; then
    computes the frontier with an axis absent from either point excluded from
    that pairwise comparison.
    """
    from deepreason import programs
    from deepreason.config import Config
    from deepreason.ontology.state import counts_as_survivor

    state = harness.state
    survivors = sorted({aid for aid, _ in state.addr if counts_as_survivor(state, aid)})
    scored = []
    for aid in survivors:
        battery = [
            c
            for c in state.artifacts[aid].interface.commitments
            if c in harness.commitments and programs.evaluable(harness.commitments[c])
        ]
        scores = {"hv": state.hv.get(aid, 0.0), "reach": state.reach.get(aid, 0.0)}
        if battery:
            scores["coverage"] = sum(
                1
                for c in battery
                if programs.evaluate(
                    harness.commitments[c], state.artifacts[aid], harness.blobs
                )[0]
                == programs.PASS
            ) / len(battery)
        scored.append((aid, scores))

    axes = Config().PARETO_AXES

    def dominates(a, b):
        shared = [x for x in axes if x in a and x in b]
        if not shared:
            return False
        return all(a[x] >= b[x] for x in shared) and any(a[x] > b[x] for x in shared)

    kept = [
        aid
        for aid, scores in scored
        if not any(dominates(other, scores) for _, other in scored)
    ]
    by_id = {v: k for k, v in ids.items()}
    return sorted(by_id[aid] for aid in kept if aid in by_id)


def main():
    # LEG 1 -- the assertion.
    harness, ids = _root({"formal": ["ok"], "prose": ["obs"]})
    kept, report = _frontier_labels(harness, ids)
    print("LEG 1  equal standing, through the shipped run_report")
    print(f"       statuses : {json.dumps(_statuses(harness, ids), sort_keys=True)}")
    print(f"       survivors: {len(report['survivors'])}")
    print(f"       frontier : {kept}")
    leg1_holds = kept == ["formal", "prose"]
    print(f"       both on the frontier (the law's requirement): {leg1_holds}")

    # LEG 2 -- mutation control A.
    h2, ids2 = _root({"formal": ["ok"], "prose": ["ok"]})
    kept2, _ = _frontier_labels(h2, ids2)
    leg2_holds = kept2 == ["formal", "prose"]
    print()
    print("LEG 2  mutation control A: prose given one PASSING evaluable commitment")
    print(f"       frontier : {kept2}")
    print(f"       control holds (the coverage axis is what excludes): {leg2_holds}")

    # LEG 3 -- mutation control B.
    h3, ids3 = _root({"passed": ["ok"], "failed": ["no"]})
    kept3, _ = _frontier_labels(h3, ids3)
    leg3_holds = kept3 == ["passed"]
    print()
    print("LEG 3  mutation control B: a FAILED battery must stay dominated")
    print(f"       frontier : {kept3}")
    print(f"       control holds (the axis still discriminates): {leg3_holds}")

    # LEG 4 -- simulated fix over the same leg-1 artifacts.
    kept4 = _road_a_labels(harness, ids)
    leg4_holds = kept4 == ["formal", "prose"]
    print()
    print("LEG 4  simulated fix: road (a) re-scoring, same artifacts as leg 1")
    print(f"       frontier : {kept4}")
    print(f"       the exclusion disappears under the fix: {leg4_holds}")

    print()
    if not (leg2_holds and leg3_holds):
        print("VERDICT: INSTRUMENT_BROKEN")
        return 2
    if leg1_holds:
        print("VERDICT: PENALTY_ABSENT")
        print("  The shipped run_report ranks an informal and a formal conjecture")
        print("  of equal standing equally. R-g's requirement is met on this tree.")
        return 1
    if not leg4_holds:
        print("VERDICT: INSTRUMENT_BROKEN")
        print("  Leg 1 reproduced but the simulated fix did not remove it, so this")
        print("  script cannot show it is measuring the coverage axis.")
        return 2
    print("VERDICT: PENALTY_PRESENT")
    print("  The prose conjecture is dropped from the frontier for carrying no")
    print("  evaluable commitment, and re-scoring it as NOT-MEASURED restores it.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
