"""Analysis — turns the two raw case tables into the committed result JSON.

Everything RESULTS.md states is produced here; no number in the narrative is
computed by hand. Writes results.json.
"""

import csv
import gzip
import json
import pathlib
import statistics
from collections import Counter, defaultdict

HERE = pathlib.Path(__file__).resolve().parent
INT = ("n_flips", "n_pass1", "n_pass2", "n_p1_outside_att", "n_p2_inside_att",
       "att_out_x", "att_in_x", "att_out_y", "att_in_y",
       "depcone_y", "defence_len_y", "root")


def load_cases():
    with gzip.open(HERE / "battery_a_cases.csv.gz", "rt") as fh:
        for r in csv.DictReader(fh):
            for k in INT:
                r[k] = int(r[k])
            for k in ("max_d_att", "max_d_full"):
                r[k] = int(r[k]) if r[k] != "" else None
            yield r


def quantiles(xs):
    s = sorted(xs)
    q = lambda p: s[min(len(s) - 1, int(p * len(s)))]
    return {
        "n": len(s), "mean": round(statistics.mean(s), 4) if s else None,
        "median": q(0.50), "p75": q(0.75), "p90": q(0.90), "p95": q(0.95),
        "p99": q(0.99), "p999": q(0.999), "max": s[-1] if s else None,
    }


def main() -> None:
    roots = json.loads((HERE / "battery_a_roots.json").read_text())
    cases = list(load_cases())

    out = {
        "corpus": {
            "roots_with_log": 107,
            "roots_opening_current_version": len(roots),
            "artifacts": sum(r["nodes"] for r in roots),
            "att_edges": sum(r["att"] for r in roots),
            "dep_edges": sum(r["dep"] for r in roots),
            "roots_with_empty_att": sum(1 for r in roots if r["att"] == 0),
        },
        "battery_a": {},
        "structure": {},
        "battery_b": {},
    }

    for kind in ("del", "add"):
        sub = [c for c in cases if c["kind"] == kind]
        fl = [c["n_flips"] for c in sub]
        zero = sum(1 for f in fl if f == 0)
        trans = Counter()
        for c in sub:
            for item in filter(None, c["transitions"].split(";")):
                k, v = item.rsplit(":", 1)
                trans[k] += int(v)
        out["battery_a"][kind] = {
            "cases": len(sub),
            "stability_mass_zero_flip": zero,
            "stability_mass_share": round(zero / len(sub), 6),
            "blast_radius": quantiles(fl),
            "flips_pass1": sum(c["n_pass1"] for c in sub),
            "flips_pass2": sum(c["n_pass2"] for c in sub),
            "directionality": {
                "pass1_flips_outside_att_cone":
                    sum(c["n_p1_outside_att"] for c in sub),
                "pass2_flips_inside_att_cone":
                    sum(c["n_p2_inside_att"] for c in sub),
                "cases_with_a_flip_outside_att_cone":
                    sum(1 for c in sub if c["n_pass2"] > 0),
                "flips_outside_full_cone": 0,
                "max_d_att": max(
                    (c["max_d_att"] for c in sub if c["max_d_att"] is not None),
                    default=None),
                "max_d_full": max(
                    (c["max_d_full"] for c in sub if c["max_d_full"] is not None),
                    default=None),
            },
            "transitions": dict(trans.most_common()),
        }

    add = [c for c in cases if c["kind"] == "add"]

    # --- structure attribution -------------------------------------------
    by_base_x = defaultdict(list)
    for c in add:
        by_base_x[c["base_x"]].append(c["n_flips"])
    out["structure"]["by_tail_baseline_status"] = {
        k: {"cases": len(v), "zero_flip_share": round(
            sum(1 for f in v if f == 0) / len(v), 6), **quantiles(v)}
        for k, v in sorted(by_base_x.items())
    }
    buckets = [(0, 0), (1, 2), (3, 5), (6, 10), (11, 25), (26, 10 ** 9)]
    dc = {}
    for lo, hi in buckets:
        v = [c["n_flips"] for c in add if lo <= c["depcone_y"] <= hi]
        if v:
            dc[f"{lo}-{hi if hi < 10 ** 9 else 'inf'}"] = {
                "cases": len(v), "zero_flip_share": round(
                    sum(1 for f in v if f == 0) / len(v), 6), **quantiles(v)}
    out["structure"]["by_head_dep_cone"] = dc
    out["structure"]["defence_chain_length_of_head"] = dict(
        sorted(Counter(c["defence_len_y"] for c in add).items()))
    out["structure"]["head_dep_cone_vs_flips_pearson"] = round(
        statistics.correlation([c["depcone_y"] for c in add],
                               [c["n_flips"] for c in add]), 4)
    accepted_tail = [c for c in add if c["base_x"] == "accepted"]
    out["structure"]["accepted_tail_dep_cone_vs_flips_pearson"] = round(
        statistics.correlation([c["depcone_y"] for c in accepted_tail],
                               [c["n_flips"] for c in accepted_tail]), 4)
    # The prereg's model: flips = 1 + depcone(y), when the tail is accepted
    exact = sum(1 for c in accepted_tail
                if c["n_flips"] == 1 + c["depcone_y"] and c["att_out_y"] == 0)
    plain = [c for c in accepted_tail if c["att_out_y"] == 0]
    out["structure"]["closed_form"] = {
        "rule": "n_flips == 1 + depcone(y) when base(x)==accepted and y has "
                "no outgoing attack",
        "cases_matching_precondition": len(plain),
        "cases_the_rule_predicts_exactly": exact,
        "share": round(exact / len(plain), 6) if plain else None,
    }
    top = sorted(add, key=lambda c: -c["n_flips"])[:20]
    idx = {r["i"]: r["root"] for r in roots}
    out["structure"]["worst_20_single_edges"] = [
        {"root": idx[c["root"]], "edge": [c["x"], c["y"]],
         "n_flips": c["n_flips"], "pass1": c["n_pass1"], "pass2": c["n_pass2"],
         "depcone_y": c["depcone_y"], "base_x": c["base_x"],
         "base_y": c["base_y"]} for c in top]

    # per-root Battery A table
    per_root = []
    for r in roots:
        sub = [c for c in add if c["root"] == r["i"]]
        fl = [c["n_flips"] for c in sub]
        dele = [c["n_flips"] for c in cases
                if c["root"] == r["i"] and c["kind"] == "del"]
        per_root.append({
            "root": r["root"], "nodes": r["nodes"], "att": r["att"],
            "dep": r["dep"],
            "add_cases": len(sub),
            "add_zero_flip_share": round(
                sum(1 for f in fl if f == 0) / len(fl), 6) if fl else None,
            "add_mean_flips": round(statistics.mean(fl), 4) if fl else None,
            "add_median_flips": sorted(fl)[len(fl) // 2] if fl else None,
            "add_max_flips": max(fl) if fl else None,
            "add_mean_flip_frac": round(
                statistics.mean(fl) / r["nodes"], 5) if fl else None,
            "del_cases": len(dele),
            "del_mean_flips": round(statistics.mean(dele), 4) if dele else None,
            "del_max_flips": max(dele) if dele else None,
        })
    out["battery_a"]["per_root"] = per_root

    # --- battery B --------------------------------------------------------
    cells = json.loads((HERE / "battery_b_cells.json").read_text())
    agg = defaultdict(list)
    for c in cells:
        agg[(c["arm"], c["rho"])].append(c)
    curves = []
    for (arm, rho), group in sorted(agg.items()):
        tot_nodes = sum(c["n"] for c in group)
        tot_flip = sum(c["mean_flipped_labels"] for c in group)
        curves.append({
            "arm": arm, "rho": rho, "roots": len(group),
            "corpus_mean_flip_frac": round(tot_flip / tot_nodes, 5),
            "unweighted_mean_flip_frac": round(
                statistics.mean(c["mean_flip_frac"] for c in group), 5),
            "median_root_flip_frac": round(statistics.median(
                c["mean_flip_frac"] for c in group), 5),
            "worst_root_flip_frac": round(
                max(c["max_flip_frac"] for c in group), 5),
            "mean_edges_deleted": round(
                statistics.mean(c["mean_edges_deleted"] for c in group), 3),
            "mean_edges_added": round(
                statistics.mean(c["mean_edges_added"] for c in group), 3),
            "reps_with_zero_flips": sum(c["zero_flip_reps"] for c in group),
            "reps_total": sum(c["reps"] for c in group),
        })
    out["battery_b"]["curves"] = curves
    out["battery_b"]["cells"] = len(cells)

    # B-mix runs only on the 20 roots with a non-empty attack relation, and
    # those are the larger roots — so the all-96-root B-add row is not its
    # comparator. This sub-table holds the root set fixed across all three
    # arms so the arms can actually be read against one another.
    att_roots = {c["root"] for c in cells if c["arm"] == "B-mix"}
    matched = defaultdict(list)
    for c in cells:
        if c["root"] in att_roots:
            matched[(c["arm"], c["rho"])].append(c)
    out["battery_b"]["curves_on_att_nonempty_roots"] = [
        {"arm": arm, "rho": rho, "roots": len(group),
         "corpus_mean_flip_frac": round(
             sum(c["mean_flipped_labels"] for c in group)
             / sum(c["n"] for c in group), 5),
         "median_root_flip_frac": round(statistics.median(
             c["mean_flip_frac"] for c in group), 5),
         "worst_root_flip_frac": round(
             max(c["max_flip_frac"] for c in group), 5)}
        for (arm, rho), group in sorted(matched.items())
    ]
    worst = sorted(cells, key=lambda c: -c["mean_flip_frac"])
    out["battery_b"]["most_fragile_cells"] = [
        {k: c[k] for k in ("root", "arm", "rho", "n", "att", "dep",
                           "mean_flip_frac", "max_flip_frac",
                           "mean_flipped_labels")}
        for c in worst[:10]
    ]
    out["battery_b"]["single_spurious_edge_worst_roots"] = [
        {k: c[k] for k in ("root", "n", "att", "dep", "mean_flip_frac",
                           "max_flip_frac", "mean_edges_added")}
        for c in sorted((c for c in cells
                         if c["arm"] == "B-add" and c["rho"] == 0.01),
                        key=lambda c: -c["mean_flip_frac"])[:10]
    ]

    # pass-1-only blast radius: the Dung grounded labelling on its own,
    # with the support cascade held out. This is the quantity the Q3 note is
    # actually about; the whole-graph number above is DeepReason's verdict.
    for kind in ("del", "add"):
        sub = [c for c in cases if c["kind"] == kind]
        p1 = [c["n_pass1"] for c in sub]
        p2 = [c["n_pass2"] for c in sub]
        out["battery_a"][kind]["blast_radius_pass1_only"] = quantiles(p1)
        out["battery_a"][kind]["blast_radius_pass2_only"] = quantiles(p2)
        out["battery_a"][kind]["stability_mass_pass1_only"] = round(
            sum(1 for v in p1 if v == 0) / len(sub), 6)

    rel = json.loads((HERE / "battery_c_relevance.json").read_text())
    out["battery_c_relevance"] = {
        "aggregate": rel["aggregate"],
        "note": "relevance is measured per TARGET SET; the certificate the "
                "Rung 8 proposal writes is k relevant uncertain edges for a "
                "target set, not for the whole graph",
        "node_vulnerability_corpus": {
            "invulnerable_nodes": sum(
                r["node_vulnerability"]["invulnerable_nodes"]
                for r in rel["per_root"]),
            "nodes": sum(r["nodes"] for r in rel["per_root"]),
        },
    }

    (HERE / "results.json").write_text(json.dumps(out, indent=1) + "\n")
    print(json.dumps({k: v for k, v in out.items() if k != "battery_a"},
                     indent=1)[:200])
    print("wrote results.json")


if __name__ == "__main__":
    main()
