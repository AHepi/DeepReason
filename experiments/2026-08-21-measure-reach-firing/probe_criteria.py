"""Supplementary probe (READ-ONLY): what do the qualifying criteria that
reject every pair actually SAY, and how do they fail?

For the roots named on the command line, dumps for every (accepted+addressed
artifact, foreign problem) pair that reaches reach_sweep's verdict gate:
the qualifying criteria, their eval strings, and the verdict each returned.
Aggregated, so the output is a census and not a dump of 500k rows.
"""

import collections
import json
import pathlib
import sys

REPO = pathlib.Path(__file__).resolve().parents[2]


def probe(root: pathlib.Path, sample: int = 12) -> dict:
    from deepreason import programs
    from deepreason.harness import Harness
    from deepreason.measures.reach import _substantive
    from deepreason.ontology.state import Status

    harness = Harness(root, read_only=True)
    state = harness.state
    addressed: dict[str, set[str]] = {}
    for aid, pid in state.addr:
        addressed.setdefault(aid, set()).add(pid)

    per_criterion = collections.defaultdict(collections.Counter)
    eval_of: dict[str, str] = {}
    coverage_hist = collections.Counter()
    would_pass_all = 0
    gate_pairs = 0
    examples: list[dict] = []
    cache: dict[tuple[str, str], str] = {}

    for aid, status in state.status.items():
        if status != Status.ACCEPTED or aid not in addressed:
            continue
        artifact = state.artifacts[aid]
        carried = set(artifact.interface.commitments)
        for pid, problem in state.problems.items():
            if pid in addressed[aid] or not problem.criteria:
                continue
            qualifying = [
                c for c in problem.criteria
                if c in harness.commitments and _substantive(harness.commitments[c])
            ]
            if not qualifying or not (set(qualifying) - carried):
                continue
            gate_pairs += 1
            coverage_hist[
                round(len(qualifying) / len(problem.criteria), 2)
            ] += 1
            verdicts = {}
            for cid in qualifying:
                key = (cid, aid)
                if key not in cache:
                    try:
                        value, _trace = programs.evaluate(
                            harness.commitments[cid], artifact, harness.blobs
                        )
                    except Exception as error:
                        value = f"error:{type(error).__name__}"
                    cache[key] = value
                verdicts[cid] = cache[key]
                eval_of[cid] = harness.commitments[cid].eval
                per_criterion[cid][cache[key]] += 1
            if all(v == programs.PASS for v in verdicts.values()):
                would_pass_all += 1
                if len(examples) < sample:
                    examples.append({
                        "artifact": aid, "problem": pid,
                        "qualifying": len(qualifying),
                        "total_criteria": len(problem.criteria),
                        "coverage": round(len(qualifying) / len(problem.criteria), 3),
                    })

    # the criteria that actually did the rejecting, ranked
    rejectors = sorted(
        (
            {
                "criterion": cid,
                "eval": eval_of[cid][:220],
                "verdicts": dict(counter),
                "nonpass": sum(v for k, v in counter.items() if k != programs.PASS),
            }
            for cid, counter in per_criterion.items()
        ),
        key=lambda row: -row["nonpass"],
    )
    return {
        "root": str(root.relative_to(REPO)),
        "gate_pairs": gate_pairs,
        "pairs_passing_every_qualifying_criterion": would_pass_all,
        "coverage_histogram": dict(sorted(coverage_hist.items())),
        "examples_passing_all": examples,
        "distinct_qualifying_criteria": len(per_criterion),
        "criteria_never_passing": sum(
            1 for c in per_criterion.values() if not c.get(programs.PASS)
        ),
        "criteria_passing_sometimes": sum(
            1 for c in per_criterion.values() if c.get(programs.PASS)
        ),
        "top_rejectors": rejectors[:25],
    }


if __name__ == "__main__":
    out = [probe(REPO / arg) for arg in sys.argv[1:]]
    path = pathlib.Path(__file__).with_name("probe_criteria.json")
    path.write_text(json.dumps(out, indent=2, sort_keys=True) + "\n")
    print(json.dumps(out, indent=2, sort_keys=True)[:6000])
    print(f"\nwrote {path}")
