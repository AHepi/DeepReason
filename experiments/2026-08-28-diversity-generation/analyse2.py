#!/usr/bin/env python3
"""LEG 2 metrics and verdicts, computed from raw_leg2/ alone.

Identical to leg 1 in every respect except the distinctness metric:
same arms, same prompts, same questions, same sampling configuration, same
M2, same M3, same §7 decision rules and the same 3-cluster effect floor.
What changes is M1's clustering rule, which is now (linkage, tau2) as
CALIBRATED ON LEG 1 by calibrate_leg2.py and frozen in
calibration_leg2.json before any leg 2 response existed.

Why a second leg rather than re-scoring leg 1: a metric must never be tuned
on the data it judges.  Leg 1 calibrates; leg 2 measures.
"""
import argparse
import hashlib
import json
import pathlib
import statistics
import sys
import tempfile

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from analyse import (VS_EXPECTED_ITEMS, _assert_probabilities_unused, extract,  # noqa: E402
                     mean_pairwise_distance)
from calibrate_leg2 import cluster  # noqa: E402
from driver import ARMS  # noqa: E402
from questions import QUESTIONS  # noqa: E402

EFFECT_FLOOR = 3.0          # PREREG §7, unchanged
ROOT = "raw_leg2"


def n_clusters(vectors, tau, linkage):
    return len(set(cluster(vectors, tau, linkage))) if vectors else 0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--reps", default="1,2,3,4,5,6,7,8,9")
    ap.add_argument("--root", default=ROOT)
    ap.add_argument("--out", default="metrics_leg2.json")
    args = ap.parse_args()
    reps = [int(r) for r in args.reps.split(",")]

    for module_source in (HERE / "analyse.py", HERE / "analyse2.py"):
        _assert_probabilities_unused(module_source.read_text())

    calib = json.loads((HERE / "calibration_leg2.json").read_text())
    tau2, linkage = calib["tau2"], calib["linkage"]
    tau_grid = sorted({round(tau2 + d, 4) for d in (-0.04, -0.02, 0.0, 0.02, 0.04)})
    sensitivity = [round(tau2 - 0.02, 4), tau2, round(tau2 + 0.02, 4)]

    from deepreason.llm.embedder import NeuralEmbedder
    emb = NeuralEmbedder()
    fingerprint = emb.fingerprint()
    if fingerprint != calib["embedder_fingerprint"]:
        print("WARNING: embedder fingerprint drift since calibration; this is a "
              "different measurement.", file=sys.stderr)

    cache_path = pathlib.Path(tempfile.gettempdir()) / "dr_diversity_embcache.json"
    cache = {}
    if cache_path.exists():
        blob = json.loads(cache_path.read_text())
        if blob.get("fingerprint") == fingerprint:
            cache = blob["vectors"]

    def embed(text):
        key = hashlib.sha256(text.encode("utf-8")).hexdigest()
        if key not in cache:
            cache[key] = emb.embed(text)
        return cache[key]

    raw_cells, vectors = {}, {}
    for q in sorted(QUESTIONS):
        for rep in reps:
            for arm in ARMS:
                if not (HERE / args.root / arm / q / f"r{rep}").exists():
                    continue
                cands, m3 = extract(arm, q, rep, root=args.root)
                raw_cells[(arm, q, rep)] = (cands, m3)
                vectors[(arm, q, rep)] = [embed(text) for _, text in cands]
    cache_path.write_text(json.dumps({"fingerprint": fingerprint, "vectors": cache}))

    counts = [len(c) for (c, _) in raw_cells.values() if c]
    n_min = min(counts) if counts else 0

    rows = []
    for (arm, q, rep), (cands, m3) in sorted(raw_cells.items()):
        vecs = vectors[(arm, q, rep)]
        sub = vecs[:n_min]
        emitted = max(m3["calls"] * (1 if arm in ("A", "B") else VS_EXPECTED_ITEMS), len(cands))
        rows.append({
            "arm": arm, "question": q, "rep": rep,
            "n_valid": len(cands), "n_min_used": len(sub),
            "M1_full": {str(t): n_clusters(vecs, t, linkage) for t in tau_grid},
            "M1_nmin": {str(t): n_clusters(sub, t, linkage) for t in tau_grid},
            "M2_full": mean_pairwise_distance(vecs),
            "M2_nmin": mean_pairwise_distance(sub),
            "M3": m3,
            "invalid_rate": (m3["parse_failure"] + m3["empty_candidate"]) / max(1, emitted),
        })

    questions = sorted(QUESTIONS)

    def mean_m1(arm, q, tau):
        vals = [r["M1_nmin"][str(tau)] for r in rows if r["arm"] == arm and r["question"] == q]
        return statistics.fmean(vals) if vals else float("nan")

    verdicts = {}

    def compare(a, b, label, claim):
        per_q = {q: {str(t): mean_m1(b, q, t) - mean_m1(a, q, t) for t in sensitivity}
                 for q in questions}
        supported = all(per_q[q][str(t)] >= EFFECT_FLOOR for q in questions for t in sensitivity)
        refuted = sum(1 for q in questions if per_q[q][str(tau2)] <= 0) >= 2
        verdicts[label] = {
            "claim": claim,
            "verdict": "SUPPORTED" if supported else ("REFUTED" if refuted else "INCONCLUSIVE"),
            "delta_by_question": per_q,
        }

    compare("A", "B", "H1", "B > A on M1 (stratification; note row 5, grade B)")
    compare("A", "C", "H2", "C > A on M1 (verbalized sampling; note row 7, grade C)")

    per_q_h3 = {q: {
        "D_minus_B": {str(t): mean_m1("D", q, t) - mean_m1("B", q, t) for t in sensitivity},
        "D_minus_C": {str(t): mean_m1("D", q, t) - mean_m1("C", q, t) for t in sensitivity},
    } for q in questions}
    h3_supported = all(per_q_h3[q][k][str(t)] >= -EFFECT_FLOOR
                       for q in questions for k in per_q_h3[q] for t in sensitivity)
    h3_refuted = any(sum(1 for q in questions if per_q_h3[q][k][str(tau2)] < -EFFECT_FLOOR) >= 2
                     for k in ("D_minus_B", "D_minus_C"))
    verdicts["H3"] = {
        "claim": "D >= B and D >= C on M1",
        "verdict": "SUPPORTED" if h3_supported else ("REFUTED" if h3_refuted else "INCONCLUSIVE"),
        "delta_by_question": per_q_h3,
    }

    def arm_invalid(arm):
        rs = [r for r in rows if r["arm"] == arm]
        return statistics.fmean(r["invalid_rate"] for r in rs) if rs else float("nan")

    gap_pp = (arm_invalid("C") - arm_invalid("A")) * 100
    verdicts["H4"] = {
        "claim": "C's gain does not come with M3 degradation (<= 5pp over A)",
        "verdict": "SUPPORTED" if gap_pp <= 5.0 else "REFUTED",
        "invalid_rate_A_pct": arm_invalid("A") * 100,
        "invalid_rate_C_pct": arm_invalid("C") * 100,
        "gap_percentage_points": gap_pp,
    }

    detected = [mean_m1(a, q, tau2) for a in ARMS for q in questions]
    report = {
        "leg": 2, "root": args.root,
        "embedder_fingerprint": fingerprint,
        "tau2": tau2, "linkage": linkage,
        "tau_sensitivity": sensitivity, "tau_grid": tau_grid,
        "calibrated_on": calib["source"],
        "n_min": n_min, "reps_analysed": reps,
        "effect_floor_clusters": EFFECT_FLOOR,
        "cells": rows,
        "arm_totals": {a: {
            "tokens": sum(r["M3"]["tokens"] for r in rows if r["arm"] == a),
            "calls": sum(r["M3"]["calls"] for r in rows if r["arm"] == a),
            "valid_candidates": sum(r["n_valid"] for r in rows if r["arm"] == a),
            "invalid_rate_pct": arm_invalid(a) * 100,
            "mean_M1_nmin_at_tau2": statistics.fmean([mean_m1(a, q, tau2) for q in questions]),
            "mean_M2_nmin": statistics.fmean(
                [r["M2_nmin"] for r in rows if r["arm"] == a and r["M2_nmin"] is not None]),
        } for a in ARMS},
        "verdicts": verdicts,
        "instrument_null_result": (max(detected) - min(detected)) < EFFECT_FLOOR if detected else True,
    }
    (HERE / args.out).write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps({"tau2": tau2, "linkage": linkage, "n_min": n_min,
                      "arm_totals": report["arm_totals"],
                      "verdicts": {k: v["verdict"] for k, v in verdicts.items()},
                      "instrument_null_result": report["instrument_null_result"]}, indent=2))


if __name__ == "__main__":
    main()
