"""Battery C — IAF relevance, measured rather than assumed.

The Rung 8 proposal's certificate is not "the graph is stable"; it is
"of N uncertain edges, k are RELEVANT" — relevant to a target set of
arguments whose verification status you care about. Battery A answers the
whole-graph version (does this edge flip anything at all). This battery
answers the version the certificate is actually written in, for four target
sets, by re-running the same exhaustive single-edge sweep and asking, per
case, whether any member of the target set flipped.

Target sets:
  all      every artifact — the whole-graph question, restated
  seed     the operator's seed-question artifacts (provenance role 'seed')
  critic   critic-role artifacts (the ones a criticism verdict is about)
  refuted  the artifacts the baseline actually refuted — a run's headline

Also accumulates per-node vulnerability: how many of the root's single-edge
perturbations flip THIS node. Exhaustive; no sampling, no seed.
"""

import json
import pathlib
import statistics
import sys
import time
from collections import Counter
from multiprocessing import Pool

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

TARGETS = ("all", "seed", "critic", "refuted")


def run_root(g):
    from perturb import labels_of

    nodes = set(g["nodes"])
    order = g["nodes"]
    att = {tuple(e) for e in g["att"]}
    dep = {tuple(e) for e in g["dep"]}
    _, base = labels_of(nodes, att, dep)
    assert base == g["baseline"], g["root"]

    sets = {
        "all": set(order),
        "seed": {i for i in order if g["roles"][i] == "seed"},
        "critic": {i for i in order if g["roles"][i] == "critic"},
        "refuted": {i for i in order if base[i] == "refuted"},
    }
    relevant = {t: {"add": 0, "del": 0} for t in TARGETS}
    cases = {"add": 0, "del": 0}
    vuln: Counter = Counter()

    def one(kind, new_att):
        cases[kind] += 1
        _, lab = labels_of(nodes, new_att, dep)
        flipped = {a for a in order if lab[a] != base[a]}
        vuln.update(flipped)
        for t in TARGETS:
            if flipped & sets[t]:
                relevant[t][kind] += 1

    for e in sorted(att):
        one("del", att - {e})
    for x in order:
        for y in order:
            if x == y or (x, y) in att:
                continue
            one("add", att | {(x, y)})

    n = len(order)
    return {
        "root": g["root"], "nodes": n, "att": len(att), "dep": len(dep),
        "cases": cases,
        "target_sizes": {t: len(sets[t]) for t in TARGETS},
        "relevant": relevant,
        "relevant_share": {
            t: {k: (relevant[t][k] / cases[k] if cases[k] else None)
                for k in ("add", "del")} for t in TARGETS},
        "node_vulnerability": {
            "mean": statistics.mean(vuln[a] for a in order),
            "median": sorted(vuln[a] for a in order)[n // 2],
            "max": max(vuln[a] for a in order),
            "invulnerable_nodes": sum(1 for a in order if vuln[a] == 0),
        },
        "per_node": {a: vuln[a] for a in order},
    }


def main() -> None:
    graphs = json.loads((HERE / "graphs.json").read_text())
    graphs.sort(key=lambda g: -len(g["nodes"]))
    t0 = time.time()
    rows = []
    with Pool(8) as pool:
        for r in pool.imap_unordered(run_root, graphs):
            rows.append(r)
    rows.sort(key=lambda r: r["root"])

    agg = {}
    for t in TARGETS:
        for kind in ("add", "del"):
            num = sum(r["relevant"][t][kind] for r in rows)
            den = sum(r["cases"][kind] for r in rows)
            agg[f"{t}/{kind}"] = {
                "relevant_cases": num, "cases": den,
                "share": round(num / den, 6) if den else None,
                "roots_with_zero_relevant": sum(
                    1 for r in rows
                    if r["cases"][kind] and r["relevant"][t][kind] == 0),
                "roots_measured": sum(1 for r in rows if r["cases"][kind]),
            }
    out = {"aggregate": agg, "per_root": rows}
    (HERE / "battery_c_relevance.json").write_text(json.dumps(out, indent=1) + "\n")
    print(f"{sum(r['cases']['add'] + r['cases']['del'] for r in rows)} cases "
          f"in {time.time() - t0:.0f}s")
    for k, v in agg.items():
        print(f"  {k:14} relevant {v['share']} "
              f"({v['relevant_cases']}/{v['cases']}), roots with k=0: "
              f"{v['roots_with_zero_relevant']}/{v['roots_measured']}")


if __name__ == "__main__":
    main()
