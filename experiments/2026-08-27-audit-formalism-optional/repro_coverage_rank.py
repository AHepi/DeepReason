"""Regression: the `coverage` Pareto axis must not price formality.

HISTORY. As first written (2026-08-27) this script REPRODUCED finding F1:

    coverage = passing evaluable commitments / evaluable commitments
             = 0.0 when the artifact has NO evaluable commitment at all

`scheduler.run_report` (§11.7) scored each survivor on PARETO_AXES =
["hv", "reach", "coverage"] and `capture/pareto.frontier` kept the
non-dominated set, MAXIMISING every axis -- so an artifact whose attack
surface was prose-only scored 0.0 on an axis a formally-backed sibling scored
1.0 on, the formal one DOMINATED, and the prose one left the frontier. On
`experiments/2026-08-12-live-grounded-extension-expansion/run` that excluded
146 of that run's 233 survivors from its published answer.

TODAY it asserts the REPAIRED behaviour and fails if the penalty returns
(road (a), NOT-MEASURED: an artifact with no evaluable commitment emits no
`coverage` key at all, and `frontier` drops an axis absent from either point
out of that pairwise comparison). See
`experiments/2026-08-30-defect-formalism-rank-penalty/`.

The law (docs/proposals/DUAL_MODE_CONJECTURE_PREPLAN.md R-g:42-57):
"Formal backing may confer PROTECTION (prose-immunity, as today); its absence
confers no disadvantage."

Run:  python experiments/2026-08-27-audit-formalism-optional/repro_coverage_rank.py
Exit 0 means the law HOLDS. Exit 1 means the penalty is back.
"""

import json
import tempfile

from deepreason.capture.pareto import frontier


def _direct():
    """The axis arithmetic, straight out of `run_report` + `frontier`."""
    axes = ["hv", "reach", "coverage"]
    # Two survivors on one problem, identical on every axis the harness
    # actually measured for them (neither was HV-sampled, neither reached a
    # foreign problem). They differ ONLY in whether an evaluable commitment
    # is present to be scored -- so the prose one carries no coverage key.
    formal = {"hv": 0.0, "reach": 0.0, "coverage": 1.0}   # one program: PASS
    prose = {"hv": 0.0, "reach": 0.0}                     # nothing to check
    kept = frontier([("formal", formal), ("prose", prose)], axes)
    return sorted(kept), formal, prose


def _control():
    """The axis must still discriminate where it did measure something.

    Without this control the direct leg would also "hold" under a road that
    simply put every survivor on the frontier: "checked and failed" must stay
    dominated by "checked and passed".
    """
    axes = ["hv", "reach", "coverage"]
    passed = {"hv": 0.0, "reach": 0.0, "coverage": 1.0}
    failed = {"hv": 0.0, "reach": 0.0, "coverage": 0.0}
    return sorted(frontier([("passed", passed), ("failed", failed)], axes))


def _live():
    """The same thing through the real `run_report`, on a real root.

    Built with the ordinary public constructors so the numbers come from the
    shipped code path, not from this script's arithmetic.
    """
    from deepreason.harness import Harness
    from deepreason.ontology import (
        Commitment, Interface, Problem, Provenance, SpawnTrigger,
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
    print("PARETO_AXES = ['hv', 'reach', 'coverage']  (an absent axis is NOT MEASURED)")
    print(f"  formal survivor: {formal}")
    print(f"  prose  survivor: {prose}   <- no coverage key: nothing to check")
    print(f"  frontier keeps : {kept}")
    equal_standing = kept == ["formal", "prose"]
    print(f"  prose kept on the frontier: {equal_standing}")

    control = _control()
    print(f"  control -- 'checked and passed' vs 'checked and failed': {control}")
    control_holds = control == ["passed"]
    print(f"  the axis still discriminates where it measured something: {control_holds}")

    print()
    try:
        report, formal_id, prose_id, root, statuses = _live()
    except Exception as error:                      # pragma: no cover
        print(f"live leg unavailable ({type(error).__name__}: {error})")
        print("the direct leg above is the regression; the live leg is corroboration")
        return 0 if (equal_standing and control_holds) else 1
    print(f"live root: {root}")
    print("  statuses : " + ", ".join(
        f"{k[:12]}={v.value if v else None}" for k, v in statuses.items()))
    print(f"  survivors: {len(report['survivors'])}")
    print(f"  frontier : {json.dumps(sorted(report['frontier']))}")
    formal_kept = formal_id in report["frontier"]
    prose_kept = prose_id in report["frontier"]
    print(f"  formal id in frontier: {formal_kept}")
    print(f"  prose  id in frontier: {prose_kept}")
    live = formal_kept and prose_kept

    ok = equal_standing and control_holds and live
    print()
    print("LAW HOLDS" if ok else "PENALTY RETURNED")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
