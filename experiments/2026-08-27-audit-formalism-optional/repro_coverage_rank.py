"""Demonstration: the `coverage` Pareto axis prices formality.

`scheduler.run_report` (§11.7) scores each survivor on three axes --
PARETO_AXES = ["hv", "reach", "coverage"] -- and `capture/pareto.frontier`
keeps the non-dominated set, MAXIMISING every axis.

    coverage = passing evaluable commitments / evaluable commitments
             = 0.0 when the artifact has NO evaluable commitment at all

So an artifact whose attack surface is prose-only scores 0.0 on an axis a
formally-backed sibling scores 1.0 on. If the two are otherwise equal, the
formal one DOMINATES and the prose one leaves the frontier.

Run:  python experiments/2026-08-27-audit-formalism-optional/repro_coverage_rank.py
Exit 0 means the penalty REPRODUCED (the prose survivor was dropped).
"""

import json
import os
import sys
import tempfile

from deepreason.capture.pareto import frontier


def _direct():
    """The axis arithmetic, straight out of `run_report` + `frontier`."""
    axes = ["hv", "reach", "coverage"]
    # Two survivors on one problem, identical on every axis the harness
    # actually measured for them (neither was HV-sampled, neither reached a
    # foreign problem). They differ ONLY in whether an evaluable commitment
    # is present to be scored.
    formal = {"hv": 0.0, "reach": 0.0, "coverage": 1.0}   # one program: PASS
    prose = {"hv": 0.0, "reach": 0.0, "coverage": 0.0}    # no evaluable commitment
    kept = frontier([("formal", formal), ("prose", prose)], axes)
    return kept, formal, prose


def _live():
    """The same thing through the real `run_report`, on a real root.

    Built with the ordinary public constructors so the numbers come from the
    shipped code path, not from this script's arithmetic.
    """
    from deepreason.harness import Harness
    from deepreason.ontology import (
        Commitment, Interface, Problem, Provenance, SpawnTrigger, Status,
    )
    from deepreason.ontology.problem import ProblemProvenance
    from deepreason.config import Config

    root = tempfile.mkdtemp(prefix="formalism-audit-")
    harness = Harness(root)

    # One evaluable, structurally-passing commitment (`json-wf`); and one NON-evaluable
    # (observation) commitment, the ordinary shape of a prose criterion.
    evaluable = Commitment(id="wf", eval="program:json-wf")
    observational = Commitment(id="obs", eval="observation", observation_valued=True)
    harness.register_commitment(evaluable)
    harness.register_commitment(observational)

    problem = harness.register_problem(
        Problem(
            id="p1",
            description="a problem",
            criteria=["wf", "obs"],
            provenance=ProblemProvenance(trigger=SpawnTrigger.SEED),
        )
    )

    formal = harness.create_artifact(
        '{"claim": "formal"}',
        interface=Interface(commitments=["wf"]),
        provenance=Provenance(role="conjecturer"),
        problem_id=problem.id,
    )
    prose = harness.create_artifact(
        "A claim written in words, with an observational countercondition.",
        interface=Interface(commitments=["obs"]),
        provenance=Provenance(role="conjecturer"),
        problem_id=problem.id,
    )
    # Unattacked, so the harness's own grounded-extension pass labels both
    # ACCEPTED. No status is hand-set anywhere in this script.

    from deepreason.scheduler.scheduler import run_report

    report = run_report(harness, Config())
    statuses = {formal.id: harness.state.status.get(formal.id),
                prose.id: harness.state.status.get(prose.id)}
    return report, formal.id, prose.id, root, statuses


def main():
    kept, formal, prose = _direct()
    print("PARETO_AXES = ['hv', 'reach', 'coverage']  (frontier maximises each)")
    print(f"  formal survivor: {formal}")
    print(f"  prose  survivor: {prose}")
    print(f"  frontier keeps : {kept}")
    reproduced = kept == ["formal"]
    print(f"  prose dropped from the frontier: {reproduced}")

    print()
    try:
        report, formal_id, prose_id, root, statuses = _live()
    except Exception as error:                      # pragma: no cover
        print(f"live leg unavailable ({type(error).__name__}: {error})")
        print("the direct leg above is the reproduction; the live leg is corroboration")
        return 0 if reproduced else 1
    print(f"live root: {root}")
    print("  statuses : " + ", ".join(
        f"{k[:12]}={v.value if v else None}" for k, v in statuses.items()))
    print(f"  survivors: {len(report['survivors'])}")
    print(f"  frontier : {json.dumps(sorted(report['frontier']))}")
    formal_kept = formal_id in report["frontier"]
    prose_kept = prose_id in report["frontier"]
    print(f"  formal id in frontier: {formal_kept}")
    print(f"  prose  id in frontier: {prose_kept}")
    live = formal_kept and not prose_kept

    # MUTATION PROOF. Change exactly one thing -- give the prose artifact an
    # evaluable commitment of its own -- and the drop must disappear. Without
    # this the script would also "pass" if the prose artifact were being
    # dropped for some reason that has nothing to do with the coverage axis.
    control = frontier(
        [("formal", {"hv": 0.0, "reach": 0.0, "coverage": 1.0}),
         ("prose", {"hv": 0.0, "reach": 0.0, "coverage": 1.0})],
        ["hv", "reach", "coverage"],
    )
    mutation_holds = sorted(control) == ["formal", "prose"]
    print()
    print(f"mutation proof (prose given one passing evaluable commitment): "
          f"frontier keeps {sorted(control)} -> penalty disappears: {mutation_holds}")

    ok = reproduced and live and mutation_holds
    print()
    print("REPRODUCED" if ok else "NOT REPRODUCED")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
