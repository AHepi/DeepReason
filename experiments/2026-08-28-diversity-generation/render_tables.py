#!/usr/bin/env python3
"""Emit RESULTS.md's tables from metrics.json / metrics_leg2.json.

Every number RESULTS.md states is printed here from the committed metrics
artifacts, so no figure in the narrative is retyped by hand."""
import json
import pathlib
import statistics
import sys

HERE = pathlib.Path(__file__).resolve().parent
ARMS = "ABCD"
NAMES = {"A": "A direct", "B": "B stratified", "C": "C verbalized sampling",
         "D": "D stratified + VS"}


def load(name):
    p = HERE / name
    return json.loads(p.read_text()) if p.exists() else None


def mean(xs):
    xs = [x for x in xs if x is not None]
    return statistics.fmean(xs) if xs else float("nan")


def cell_stats(rows, arm, q, key, tau):
    vals = [r[key][str(tau)] for r in rows if r["arm"] == arm and r["question"] == q]
    return vals


def main():
    out = []
    leg1, leg2 = load("metrics.json"), load("metrics_leg2.json")

    for leg, d, tau_key in ((1, leg1, "tau_star"), (2, leg2, "tau2")):
        if not d:
            continue
        rows = d["cells"]
        tau = d[tau_key]
        qs = sorted({r["question"] for r in rows})
        rule = "single linkage" if leg == 1 else f"{d['linkage']} linkage"
        out.append(f"\n### Leg {leg} — M1@Nmin at τ = {tau} ({rule}), n_min = {d['n_min']}\n")
        out.append("Mean over 9 repetitions, with (min–max) across those repetitions.\n")
        out.append("| arm | " + " | ".join(qs) + " | overall |")
        out.append("|---|" + "---|" * (len(qs) + 1))
        for a in ARMS:
            cells_ = []
            for q in qs:
                v = cell_stats(rows, a, q, "M1_nmin", tau)
                cells_.append(f"{mean(v):.1f} ({min(v):.0f}–{max(v):.0f})" if v else "—")
            overall = mean([mean(cell_stats(rows, a, q, "M1_nmin", tau)) for q in qs])
            out.append(f"| {NAMES[a]} | " + " | ".join(cells_) + f" | **{overall:.1f}** |")

        out.append(f"\n### Leg {leg} — M2 (mean pairwise distance, threshold-free)\n")
        out.append("| arm | " + " | ".join(qs) + " | overall |")
        out.append("|---|" + "---|" * (len(qs) + 1))
        for a in ARMS:
            per = [mean([r["M2_nmin"] for r in rows if r["arm"] == a and r["question"] == q])
                   for q in qs]
            out.append(f"| {NAMES[a]} | " + " | ".join(f"{v:.4f}" for v in per)
                       + f" | **{mean(per):.4f}** |")

        out.append(f"\n### Leg {leg} — M3 (yield) and token spend\n")
        out.append("| arm | calls | valid candidates | parse fail | empty | off-format count "
                   "| off-format prob | invalid % | tokens | tokens/candidate |")
        out.append("|---|---|---|---|---|---|---|---|---|---|")
        for a in ARMS:
            rs = [r for r in rows if r["arm"] == a]
            t = d["arm_totals"][a]
            s = lambda k: sum(r["M3"][k] for r in rs)  # noqa: E731
            out.append(
                f"| {NAMES[a]} | {t['calls']} | {t['valid_candidates']} | {s('parse_failure')} "
                f"| {s('empty_candidate')} | {s('off_format_count')} | {s('off_format_probability')} "
                f"| {t['invalid_rate_pct']:.2f}% | {t['tokens']:,} "
                f"| {t['tokens'] / max(1, t['valid_candidates']):.1f} |")

        out.append(f"\n### Leg {leg} — τ sensitivity (M1@Nmin, overall mean)\n")
        grid = d.get("tau_grid") or d.get("tau_curve")
        out.append("| arm | " + " | ".join(f"τ={t}" for t in grid) + " |")
        out.append("|---|" + "---|" * len(grid))
        for a in ARMS:
            vals = [mean([r["M1_nmin"][str(t)] for r in rows if r["arm"] == a]) for t in grid]
            out.append(f"| {NAMES[a]} | " + " | ".join(f"{v:.1f}" for v in vals) + " |")

        out.append(f"\n### Leg {leg} — verdicts\n")
        out.append("| | claim | verdict |")
        out.append("|---|---|---|")
        for h in ("H1", "H2", "H3", "H4"):
            v = d["verdicts"][h]
            out.append(f"| **{h}** | {v['claim']} | **{v['verdict']}** |")
        if leg == 2:
            v = d["verdicts"]["H4"]
            out.append(f"\nH4 detail: invalid rate A {v['invalid_rate_A_pct']:.2f}% vs "
                       f"C {v['invalid_rate_C_pct']:.2f}%, gap "
                       f"{v['gap_percentage_points']:+.2f} percentage points "
                       f"(threshold: +5.00).")

    text = "\n".join(out) + "\n"
    (HERE / "RESULTS_TABLES.md").write_text(text)
    print(text)


if __name__ == "__main__":
    main()
