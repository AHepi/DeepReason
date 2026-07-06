#!/usr/bin/env python
"""Basin study, offline battery (experiments/basin_study_prereg.yaml).

Measures WHEN conjecture circles a basin (novelty-onset curves) and which
mechanism correlates with it (stance decay, neighbourhood echo, school
monopoly, survivorship narrowing, embedder scale) — over every committed
run root, costing zero tokens. The live manipulation battery is designed
AFTER these measurements say which hypotheses deserve tokens.
"""

import json
import sys
from pathlib import Path
from statistics import mean

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from deepreason.harness import Harness  # noqa: E402
from deepreason.llm.embedder import HashingEmbedder  # noqa: E402
from deepreason.views.basin import (  # noqa: E402
    basin_onset,
    conjecture_series,
    embedder_calibration,
    survivorship,
    windowed,
)

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "experiments" / "results" / "basin_offline_report.json"

ROOTS = [
    "runs/criticism",           # 700k self-referential run, richest
    "runs/ab_harness",          # republic A/B arm
    "runs/ab_bronze",           # bronze A/B arm
    "runs/ab_needham",          # needham A/B arm
    "runs/chaos/S1-garbage-generator",
    "runs/chaos/S2-weak-judge-seat",
    "runs/chaos/S3-all-weak-lowtemp",   # capture ladder fired here
    "runs/chaos/S4-weak-skeletons",
]


def _pearson(xs: list[float], ys: list[float]) -> float | None:
    pairs = [(x, y) for x, y in zip(xs, ys) if x is not None and y is not None]
    if len(pairs) < 8:
        return None
    xs2, ys2 = [p[0] for p in pairs], [p[1] for p in pairs]
    mx, my = mean(xs2), mean(ys2)
    num = sum((x - mx) * (y - my) for x, y in pairs)
    dx = sum((x - mx) ** 2 for x in xs2) ** 0.5
    dy = sum((y - my) ** 2 for y in ys2) ** 0.5
    if dx == 0 or dy == 0:
        return None
    return num / (dx * dy)


def analyze_root(path: Path) -> dict:
    h = Harness(path)
    emb = HashingEmbedder()
    series = conjecture_series(h, emb)
    if len(series) < 4:
        return {"root": str(path), "skipped": f"only {len(series)} conjectures"}
    win = windowed(series, h, emb)
    surv = survivorship(h, emb)
    calib = embedder_calibration(h, emb)
    onset = basin_onset(series)

    idx = list(range(len(series)))
    nov = [r["novelty_global"] for r in series]
    correlations = {
        # H-decay: novelty should FALL as stance weight falls (positive r).
        "novelty_vs_stance_weight": _pearson(
            [r["stance_weight"] for r in series], nov),
        # H-echo: conjectures that sit close to their own pack's exemplars
        # should also be close to prior output generally (positive r
        # between echo_min and novelty_global; echo LOW when novelty LOW).
        "novelty_vs_echo": _pearson([r["echo_min"] for r in series], nov),
        # Baseline drift: novelty vs time (negative = the basin pull).
        "novelty_vs_index": _pearson([float(i) for i in idx], nov),
        # Surprisal contraction alongside content contraction.
        "novelty_vs_surprisal": _pearson([r["surprisal"] for r in series], nov),
        # H-turnover: does novelty fall with PROBLEM age and reset on new
        # problems? (negative r = problem age is the basin clock)
        "novelty_vs_problem_age": _pearson(
            [float(r["problem_age"]) for r in series], nov),
    }
    monopoly = [w["top_school_share"] for w in win]
    within = [w["within_school_diversity"] for w in win]
    correlations["within_diversity_vs_monopoly"] = _pearson(monopoly, within)

    echo_rows = [r for r in series if r["echo_min"] is not None]
    shown_rows = [(i, r) for i, r in enumerate(series)
                  if r["nearest_was_shown"] is not None and r["echo_n_exemplars"] > 0]
    shown = [r["nearest_was_shown"] for _, r in shown_rows]
    # Chance baseline: if the nearest prior were random, P(shown) is the
    # fraction of priors the pack displayed at that moment.
    chance = [min(1.0, r["echo_n_exemplars"] / i) for i, r in shown_rows if i > 0]
    shown_rate = sum(shown) / len(shown) if shown else None
    chance_rate = mean(chance) if chance else None
    return {
        # The pack-echo fingerprint: how often is the single nearest prior
        # artifact one the generator was LOOKING AT when it produced this?
        # Compare against chance: >1x = echoing the pack, <1x = actively
        # avoiding it (the VS 'diverse candidates' directive working).
        "nearest_was_shown_rate": round(shown_rate, 3) if shown_rate is not None else None,
        "nearest_was_shown_chance": round(chance_rate, 3) if chance_rate else None,
        "echo_vs_chance": round(shown_rate / chance_rate, 2)
                          if shown_rate is not None and chance_rate else None,
        "root": str(path),
        "n_conjectures": len(series),
        "n_schools": len({r["school"] for r in series if r["school"]}),
        "onset": onset,
        "survivorship": surv,
        "embedder_calibration": calib,
        "correlations": {k: (round(v, 3) if v is not None else None)
                         for k, v in correlations.items()},
        "echo": {
            "n_with_exemplars": len(echo_rows),
            "mean_echo_min": round(mean(r["echo_min"] for r in echo_rows), 4)
                             if echo_rows else None,
            "mean_novelty_when_echoing": round(
                mean(r["novelty_global"] for r in echo_rows
                     if r["novelty_global"] is not None), 4)
                if echo_rows else None,
        },
        "stance": {
            "n_zero_weight": sum(1 for r in series if r["stance_weight"] == 0.0),
            "mean_novelty_weight_pos": round(mean(
                [r["novelty_global"] for r in series
                 if r["stance_weight"] > 0 and r["novelty_global"] is not None]
                or [0]), 4),
            "mean_novelty_weight_zero": round(mean(
                [r["novelty_global"] for r in series
                 if r["stance_weight"] == 0 and r["novelty_global"] is not None]
                or [0]), 4),
        },
        "windows_tail": win[-3:],
        "series": series,          # full curve, for plotting/reanalysis
    }


def main() -> int:
    report = {"roots": [], "notes": [
        "stance_weight computed with default STANCE_DECAY=20 (all committed "
        "runs used the default; recorded assumption)",
        "embedder = HashingEmbedder(128) — the same instrument the live "
        "school_convergence detector uses, so its scale problems ARE the "
        "detector's scale problems",
    ]}
    for r in ROOTS:
        path = ROOT / r
        if not (path / "log.jsonl").exists():
            report["roots"].append({"root": r, "skipped": "no log"})
            continue
        print(f"analyzing {r} ...", flush=True)
        try:
            report["roots"].append(analyze_root(path))
        except Exception as e:  # noqa: BLE001 — a crash is a finding
            report["roots"].append({"root": r, "error": repr(e)[:300]})
    OUT.write_text(json.dumps(report, indent=2))

    print(f"\n{'root':34s} {'n':>4s} {'onset':>6s} {'nov~t':>6s} {'nov~stance':>10s} "
          f"{'nov~echo':>8s} {'div~monop':>9s} {'surv_narrow':>11s}")
    for r in report["roots"]:
        if "error" in r or "skipped" in r:
            print(f"{r['root']:34s} {r.get('error') or r.get('skipped')}")
            continue
        c = r["correlations"]
        s = r["survivorship"]
        narrow = (round(s["diversity_accepted"] / s["diversity_all"], 2)
                  if s["diversity_all"] and s["diversity_accepted"] else None)
        print(f"{r['root']:34s} {r['n_conjectures']:>4d} "
              f"{str(r['onset']['onset_index']):>6s} "
              f"{str(c['novelty_vs_index']):>6s} {str(c['novelty_vs_stance_weight']):>10s} "
              f"{str(c['novelty_vs_echo']):>8s} {str(c['within_diversity_vs_monopoly']):>9s} "
              f"{str(narrow):>11s}")
    print(f"\nreport: {OUT}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
