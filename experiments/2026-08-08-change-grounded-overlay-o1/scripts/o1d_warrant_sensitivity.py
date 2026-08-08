"""O1d — load-bearing-warrant sensitivity distributions (SPEC.md S9,
GROUNDED_OVERLAY_PREPLAN.md Rung O1). Read-only: recomputes `att`/
`label0`/`final_labels` with one warrant's carriage removed at a time,
reusing adjudication's own functions — never a hand-rolled semantics.

Single-warrant sensitivity only (SPEC.md A6): "minimum set" beyond size
1 is out of this rung's scope, named as a residue item, not attempted.
"""

import pathlib
import sys
from collections import defaultdict

sys.path.insert(0, str(pathlib.Path(__file__).parent))
from overlay_common import corpus, open_root  # noqa: E402

from deepreason.adjudication.edges import build_att, build_dep  # noqa: E402
from deepreason.adjudication.grounded import label0 as compute_label0  # noqa: E402
from deepreason.adjudication.support import final_labels  # noqa: E402
from deepreason.ontology.state import Status  # noqa: E402


def analyze_root(root: pathlib.Path) -> dict:
    harness = open_root(root)
    nodes = set(harness.state.artifacts)
    accepted = [aid for aid, s in harness.state.status.items() if s == Status.ACCEPTED]
    dep_edges = build_dep(harness.state.artifacts)
    all_carries = list(harness.state.carries)

    flips_by_artifact: dict = defaultdict(list)
    for wid in harness.warrants:
        warrants_minus = {k: v for k, v in harness.warrants.items() if k != wid}
        carries_minus = [c for c in all_carries if c[1] != wid]
        att_minus = build_att(
            harness.state.artifacts, warrants_minus, harness.commitments, carries=carries_minus
        )
        label0_minus = compute_label0(nodes, att_minus)
        final_minus = final_labels(label0_minus, dep_edges)
        for aid in accepted:
            if final_minus.get(aid) != Status.ACCEPTED:
                flips_by_artifact[aid].append(wid)

    histogram: dict = defaultdict(int)
    for aid in accepted:
        histogram[len(flips_by_artifact.get(aid, ()))] += 1

    return {
        "root": str(root),
        "accepted_count": len(accepted),
        "warrant_count": len(harness.warrants),
        "flip_histogram": dict(sorted(histogram.items())),
        "single_flip_artifacts": {
            aid: warrants for aid, warrants in flips_by_artifact.items() if len(warrants) == 1
        },
        "multi_flip_artifacts": {
            aid: warrants for aid, warrants in flips_by_artifact.items() if len(warrants) > 1
        },
    }


def main():
    for root in corpus():
        try:
            result = analyze_root(root)
        except Exception as error:  # noqa: BLE001 - a per-root failure must not kill the sweep
            print(f"{root} ERROR {type(error).__name__}: {error}")
            continue
        print(
            f"{root} accepted={result['accepted_count']} "
            f"warrants={result['warrant_count']} "
            f"histogram={result['flip_histogram']}"
        )


if __name__ == "__main__":
    main()
