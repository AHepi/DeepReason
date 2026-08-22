"""Battery B — error-rate curves, three arms, as registered in GOAL.md.

Rates need a denominator and the corpus makes the obvious one degenerate:
10 % of 0 attack edges is 0 edges. So three arms are run, each stating its
own denominator, and all three are reported whatever they show.

  B-del  delete each true edge independently with probability rho
         (rho = 0.65 is Q10's recall complement at Attack-F1 ~ 0.4).
         20 roots with a non-empty attack relation.
  B-add  add k = max(1, round(rho * n)) spurious edges — one per 100 / 50 /
         20 / 10 arguments. All 96 roots.
  B-mix  both at once at matched rho. 20 roots.

Seeds derive from the root id and cell coordinates, never from the clock, so
the whole battery replays byte-identically from graphs.json.
"""

import json
import pathlib
import random
import statistics
import sys
import time
from hashlib import blake2b
from multiprocessing import Pool

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

REPS = 200
RHO_DEL = [0.10, 0.25, 0.50, 0.65]
RHO_ADD = [0.01, 0.02, 0.05, 0.10]
RHO_MIX = [0.10, 0.25, 0.50]


def seeded(root: str, arm: str, rho: float, rep: int) -> random.Random:
    key = f"{root}|{arm}|{rho}|{rep}".encode()
    return random.Random(
        int.from_bytes(blake2b(key, digest_size=8).digest(), "big"))


def _sample_additions(rng, order, att, k):
    """k distinct non-self pairs outside att, drawn without replacement."""
    n = len(order)
    added = set()
    guard = 0
    while len(added) < k and guard < 200 * k + 1000:
        guard += 1
        x = order[rng.randrange(n)]
        y = order[rng.randrange(n)]
        if x == y or (x, y) in att or (x, y) in added:
            continue
        added.add((x, y))
    return added


def run_root(job):
    idx, g = job
    from perturb import labels_of

    nodes = set(g["nodes"])
    order = g["nodes"]
    att = {tuple(e) for e in g["att"]}
    dep = {tuple(e) for e in g["dep"]}
    n = len(order)
    _, base = labels_of(nodes, att, dep)
    assert base == g["baseline"], g["root"]

    out = []
    arms = [("B-add", rho) for rho in RHO_ADD]
    if att:
        arms += [("B-del", rho) for rho in RHO_DEL]
        arms += [("B-mix", rho) for rho in RHO_MIX]
    for arm, rho in arms:
        fracs, counts, ndel, nadd = [], [], [], []
        for rep in range(REPS):
            rng = seeded(g["root"], arm, rho, rep)
            new = set(att)
            if arm in ("B-del", "B-mix"):
                dropped = {e for e in sorted(att) if rng.random() < rho}
                new -= dropped
            else:
                dropped = set()
            if arm in ("B-add", "B-mix"):
                k = max(1, round(rho * n))
                extra = _sample_additions(rng, order, att, k)
                new |= extra
            else:
                extra = set()
            _, lab = labels_of(nodes, new, dep)
            flipped = sum(1 for a in order if lab[a] != base[a])
            fracs.append(flipped / n)
            counts.append(flipped)
            ndel.append(len(dropped))
            nadd.append(len(extra))
        s = sorted(fracs)
        out.append({
            "root": g["root"], "root_i": idx, "arm": arm, "rho": rho,
            "n": n, "att": len(att), "dep": len(dep), "reps": REPS,
            "mean_flip_frac": statistics.mean(fracs),
            "median_flip_frac": s[REPS // 2],
            "p90_flip_frac": s[int(0.90 * REPS)],
            "max_flip_frac": s[-1],
            "mean_flipped_labels": statistics.mean(counts),
            "max_flipped_labels": max(counts),
            "zero_flip_reps": sum(1 for c in counts if c == 0),
            "mean_edges_deleted": statistics.mean(ndel),
            "mean_edges_added": statistics.mean(nadd),
        })
    return out


def main() -> None:
    graphs = json.loads((HERE / "graphs.json").read_text())
    graphs.sort(key=lambda g: g["root"])
    jobs = sorted(enumerate(graphs), key=lambda j: -len(j[1]["nodes"]))
    t0 = time.time()
    cells = []
    with Pool(8) as pool:
        for part in pool.imap_unordered(run_root, jobs):
            cells.extend(part)
    cells.sort(key=lambda c: (c["arm"], c["rho"], c["root"]))
    (HERE / "battery_b_cells.json").write_text(json.dumps(cells, indent=1) + "\n")
    print(f"{len(cells)} cells ({len(cells) * REPS} recomputes) "
          f"in {time.time() - t0:.0f}s")


if __name__ == "__main__":
    main()
