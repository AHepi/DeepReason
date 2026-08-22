"""Battery A — single-edge perturbation, EXHAUSTIVE in both directions.

A-del: delete each of the corpus's 60 attack edges, one at a time.
A-add: add each ordered non-self pair that is not already an attack edge —
       645 564 cases across the 96 roots.

No sampling, therefore no seed. Every case carries the structural features
registered in GOAL.md's prereg, so "what makes an edge dangerous" is answered
from the same table as the flip rate rather than from a second pass.

Writes:
  battery_a_cases.csv.gz   every case, one row; ``root`` is an index into
                           battery_a_roots.json
  battery_a_roots.json     root index + per-root graph shape
  battery_a_detail.json    per-flip detail: all 60 deletions, plus the 25
                           largest-blast-radius additions per root
"""

import csv
import gzip
import json
import pathlib
import sys
import time
from collections import Counter, deque
from multiprocessing import Pool

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

FIELDS = [
    "root", "kind", "x", "y",
    "n_flips", "n_pass1", "n_pass2",
    "n_p1_outside_att", "n_p2_inside_att",
    "max_d_att", "max_d_full",
    "att_out_x", "att_in_x", "att_out_y", "att_in_y",
    "base_x", "base_y", "depcone_y", "defence_len_y",
    "transitions",
]
DETAIL_PER_ROOT = 25


def _reach(source, adj):
    seen = {source}
    q = deque([source])
    while q:
        u = q.popleft()
        for v in adj.get(u, ()):
            if v not in seen:
                seen.add(v)
                q.append(v)
    return seen


def run_root(job):
    idx, g = job
    from perturb import cone_distances, diff_case, labels_of

    nodes = set(g["nodes"])
    att = {tuple(e) for e in g["att"]}
    dep = {tuple(e) for e in g["dep"]}
    base_l0, base_final = labels_of(nodes, att, dep)
    assert base_final == g["baseline"], g["root"]
    d_att, d_full = cone_distances(g["nodes"], att, dep)

    out_deg, in_deg = Counter(), Counter()
    att_adj: dict[str, list[str]] = {}
    for u, v in att:
        out_deg[u] += 1
        in_deg[v] += 1
        att_adj.setdefault(u, []).append(v)
    revdep: dict[str, list[str]] = {}
    for a, b in dep:  # a depends on b; a demotion travels b -> a
        revdep.setdefault(b, []).append(a)
    depcone = {n: len(_reach(n, revdep)) - 1 for n in g["nodes"]}
    # longest directed att path ENDING at n (the defence chain below it)
    fwd: dict[str, list[str]] = {}
    for u, v in att:
        fwd.setdefault(v, []).append(u)
    memo: dict[str, int] = {}

    def chain(n, stack=frozenset()):
        if n in memo:
            return memo[n]
        if n in stack:  # a cycle would make this unbounded; corpus has none
            return 0
        best = max((1 + chain(p, stack | {n}) for p in fwd.get(n, ())),
                   default=0)
        memo[n] = best
        return best

    rows, detail = [], []

    def record(kind, x, y, new_att):
        new_l0, new_final = labels_of(nodes, new_att, dep)
        flips = diff_case(base_l0, base_final, new_l0, new_final, y,
                          d_att, d_full)
        da = [f["d_att"] for f in flips if f["d_att"] is not None]
        df = [f["d_full"] for f in flips if f["d_full"] is not None]
        rows.append({
            "root": idx, "kind": kind, "x": x, "y": y,
            "n_flips": len(flips),
            "n_pass1": sum(1 for f in flips if f["pass"] == 1),
            "n_pass2": sum(1 for f in flips if f["pass"] == 2),
            "n_p1_outside_att": sum(
                1 for f in flips if f["pass"] == 1 and f["d_att"] is None),
            "n_p2_inside_att": sum(
                1 for f in flips if f["pass"] == 2 and f["d_att"] is not None),
            "max_d_att": max(da) if da else "",
            "max_d_full": max(df) if df else "",
            "att_out_x": out_deg[x], "att_in_x": in_deg[x],
            "att_out_y": out_deg[y], "att_in_y": in_deg[y],
            "base_x": base_final[x], "base_y": base_final[y],
            "depcone_y": depcone[y], "defence_len_y": chain(y),
            "transitions": ";".join(sorted(
                f"{k}:{v}" for k, v in Counter(
                    f"{f['before']}->{f['after']}" for f in flips).items())),
        })
        if kind == "del":
            detail.append({"root": g["root"], "kind": kind, "edge": [x, y],
                           "n_flips": len(flips), "flips": flips})
        return len(flips), (kind, x, y, flips)

    top: list = []
    for x, y in sorted(att):
        record("del", x, y, att - {(x, y)})
    order = g["nodes"]
    for x in order:
        for y in order:
            if x == y or (x, y) in att:
                continue
            n, case = record("add", x, y, att | {(x, y)})
            if n:
                top.append((n, case))
    top.sort(key=lambda t: (-t[0], t[1][1], t[1][2]))
    for n, (kind, x, y, flips) in top[:DETAIL_PER_ROOT]:
        detail.append({"root": g["root"], "kind": kind, "edge": [x, y],
                       "n_flips": n, "flips": flips})
    return rows, detail


def main() -> None:
    graphs = json.loads((HERE / "graphs.json").read_text())
    graphs.sort(key=lambda g: g["root"])
    index = [{"i": i, "root": g["root"], "log_lines": g["log_lines"],
              "nodes": len(g["nodes"]), "att": len(g["att"]),
              "dep": len(g["dep"])} for i, g in enumerate(graphs)]
    (HERE / "battery_a_roots.json").write_text(json.dumps(index, indent=1) + "\n")

    jobs = sorted(enumerate(graphs), key=lambda j: -len(j[1]["nodes"]))
    t0 = time.time()
    all_rows, all_detail = [], []
    with Pool(8) as pool:
        for rows, detail in pool.imap_unordered(run_root, jobs):
            all_rows.extend(rows)
            all_detail.extend(detail)
    all_rows.sort(key=lambda r: (r["root"], r["kind"], r["x"], r["y"]))
    with gzip.open(HERE / "battery_a_cases.csv.gz", "wt", newline="") as fh:
        w = csv.DictWriter(fh, FIELDS)
        w.writeheader()
        w.writerows(all_rows)
    all_detail.sort(key=lambda d: (d["root"], d["kind"], -d["n_flips"],
                                   d["edge"]))
    (HERE / "battery_a_detail.json").write_text(
        json.dumps(all_detail, indent=1) + "\n")
    print(f"{len(all_rows)} cases in {time.time() - t0:.0f}s "
          f"({len(all_detail)} detailed)")


if __name__ == "__main__":
    main()
