"""Re-measure the live footprint of the `coverage` Pareto penalty, read-only.

Independent of the 2026-08-27 audit's numbers: this script recomputes the
survivor set, the (hv, reach, coverage) score triples and the frontier from
each committed root's own replayed state, through the SHIPPED `run_report`,
and then recomputes the frontier under each of PARKED.md's two behaviour-
changing roads.

Roots are opened `read_only=True`; nothing here writes to a committed record.

Run:  python experiments/2026-08-30-defect-formalism-rank-penalty/measure_footprint.py
Exit 0 always; the numbers are the output.
"""

import collections
import json
import pathlib
import sys

REPO = pathlib.Path(__file__).resolve().parents[2]

ROOTS = [
    REPO / "experiments/2026-08-12-live-grounded-extension-expansion/run",
    REPO / "experiments/2026-08-25-poietics-program/run",
]


def _road_a_frontier(scored, axes):
    """Road (a): an axis absent from EITHER point drops out of that pairwise
    comparison — 'missing' means NOT MEASURED, never zero."""

    def dominates(a, b):
        shared = [x for x in axes if x in a and x in b]
        if not shared:
            return False
        return all(a[x] >= b[x] for x in shared) and any(a[x] > b[x] for x in shared)

    return [
        item
        for item, scores in scored
        if not any(dominates(other, scores) for _, other in scored)
    ]


def _road_b_frontier(scored, axes):
    """Road (b): an empty battery scores 1.0 rather than 0.0."""
    from deepreason.capture.pareto import frontier

    patched = []
    for item, scores in scored:
        s = dict(scores)
        if s.get("coverage") is None:
            s["coverage"] = 1.0
        patched.append((item, s))
    return frontier(patched, axes)


def _measure(root):
    from deepreason import programs
    from deepreason.config import Config
    from deepreason.harness import Harness
    from deepreason.ontology.state import counts_as_survivor
    from deepreason.scheduler.scheduler import run_report

    harness = Harness(root, read_only=True)
    config = Config()
    report = run_report(harness, config)
    state = harness.state
    survivors = sorted({aid for aid, _ in state.addr if counts_as_survivor(state, aid)})

    triples = collections.Counter()
    shipped = collections.Counter()   # the triple run_report ACTUALLY emits today
    scored_raw = []          # coverage None when the evaluable battery is empty
    empty_battery = 0
    for aid in survivors:
        commitments = [
            c
            for c in state.artifacts[aid].interface.commitments
            if c in harness.commitments and programs.evaluable(harness.commitments[c])
        ]
        if commitments:
            coverage = sum(
                1
                for c in commitments
                if programs.evaluate(
                    harness.commitments[c], state.artifacts[aid], harness.blobs
                )[0]
                == programs.PASS
            ) / len(commitments)
        else:
            coverage = None
            empty_battery += 1
        hv = state.hv.get(aid, 0.0)
        reach = state.reach.get(aid, 0.0)
        triples[(hv, reach, coverage, bool(commitments))] += 1
        shipped[(hv, reach, 0.0 if coverage is None else coverage)] += 1
        scores = {"hv": hv, "reach": reach}
        if coverage is not None:
            scores["coverage"] = coverage
        scored_raw.append((aid, scores))

    axes = config.PARETO_AXES
    with_battery = {aid for aid, scores in scored_raw if "coverage" in scores}
    stored_path = root / "run-result.json"
    stored = None
    if stored_path.exists():
        stored = json.loads(stored_path.read_text()).get("frontier")

    return {
        "root": str(root.relative_to(REPO)),
        "survivors": len(survivors),
        "empty_battery": empty_battery,
        "triples": {str(k): v for k, v in sorted(triples.items(), key=lambda kv: -kv[1])},
        "shipped_score_triples": {
            str(k): v for k, v in sorted(shipped.items(), key=lambda kv: -kv[1])
        },
        "stored_frontier_len": None if stored is None else len(stored),
        "current_frontier_len": len(report["frontier"]),
        "current_frontier_is_exactly_the_battery_carriers": (
            set(report["frontier"]) == with_battery
        ),
        "empty_battery_survivors_on_current_frontier": len(
            set(report["frontier"]) - with_battery
        ),
        "current_equals_stored": (
            None if stored is None else list(report["frontier"]) == list(stored)
        ),
        "road_a_frontier_len": len(_road_a_frontier(scored_raw, axes)),
        "road_b_frontier_len": len(_road_b_frontier(scored_raw, axes)),
    }


def main():
    out = []
    for root in ROOTS:
        if not root.exists():
            print(f"MISSING ROOT: {root}", file=sys.stderr)
            return 1
        row = _measure(root)
        out.append(row)
        print(json.dumps(row, indent=2, sort_keys=True))
        print()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
