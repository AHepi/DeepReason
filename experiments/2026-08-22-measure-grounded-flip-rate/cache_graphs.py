"""Replay each current-version root ONCE and cache its argument graph.

The replay is the expensive step (~275 s for the corpus, 40 s of it for the
one 13 k-line root); every later battery reads this cache and perturbs in
memory. Roots are opened read-only and never written to.

Cached per root: node ids, the att relation, the dep relation, and the
baseline Status map exactly as the harness computed it. The baseline is
re-derived here from the committed adjudication functions and asserted equal
to ``h.state.status`` — if that assertion ever fails, the cache is not a
faithful stand-in for the run and the measurement is void.
"""

import json
import pathlib
import sys
import time

HERE = pathlib.Path(__file__).resolve().parent
REPO = HERE.parents[1]


def main() -> None:
    from deepreason.adjudication.grounded import label0
    from deepreason.adjudication.support import final_labels
    from deepreason.harness import Harness

    inv = json.loads((HERE / "inventory.json").read_text())
    out = []
    t0 = time.time()
    for row in inv:
        if not row["opened"]:
            continue
        root = REPO / row["root"]
        h = Harness(root, read_only=True)
        nodes = list(h.state.artifacts)  # registration order
        att = sorted(tuple(e) for e in h.state.att)
        dep = sorted(tuple(e) for e in h.state.dep)
        baseline = final_labels(label0(set(nodes), set(att)), set(dep))
        recorded = {i: s.value for i, s in h.state.status.items()}
        derived = {i: s.value for i, s in baseline.items()}
        assert derived == recorded, f"{row['root']}: cache != harness status"
        out.append({
            "root": row["root"],
            "log_lines": row["log_lines"],
            "nodes": nodes,
            "att": [list(e) for e in att],
            "dep": [list(e) for e in dep],
            "baseline": {i: derived[i] for i in nodes},
        })
        print(f"cached {row['root']} n={len(nodes)} att={len(att)}",
              file=sys.stderr)
    (HERE / "graphs.json").write_text(json.dumps(out) + "\n")
    print(f"{len(out)} graphs cached in {time.time() - t0:.0f}s")


if __name__ == "__main__":
    main()
