#!/usr/bin/env python3
"""Compute M1/M2/M3 and the §7 verdicts from raw/ alone.

Everything here is a function of the committed raw responses plus the frozen
constants in PREREG.md, so the metrics are recomputable by anyone holding the
commit.  No number in this file was chosen after seeing a result: tau*, the
tau grid, the effect-size floor and the four decision rules are all §6/§7.

BINDING (PREREG §6).  The model's self-reported probability values never
enter any metric, rank, filter, or ordering.  They are counted for ONE
purpose -- the M3 contract check `off_format_probability`, which asks whether
the model obeyed the output format, not what the number says.  A probability
violation therefore NEVER removes a candidate: excluding a candidate because
of its probability value would be reading the number as a signal, which is
exactly what the binding rule forbids.  `_assert_probabilities_unused` below
is that rule made checkable.
"""
import argparse
import hashlib
import itertools
import json
import pathlib
import statistics
import sys
import tempfile

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from questions import QUESTIONS  # noqa: E402
from driver import (ARMS, REPS, content_of, parse_json_object, tokens_of)  # noqa: E402

TAU_STAR = 0.7454                                   # PREREG §6, calibration.json
TAU_SENSITIVITY = (TAU_STAR - 0.05, TAU_STAR, TAU_STAR + 0.05)
TAU_CURVE = (0.60, 0.65, 0.70, 0.75, 0.80, 0.85, 0.90)
MIN_CONJECTURE_CHARS = 20
EFFECT_FLOOR = 3.0                                  # PREREG §7
VS_EXPECTED_ITEMS = 10
PROBABILITY_CEILING = 0.10


REPS_USED = list(REPS)


def cells():
    for q in sorted(QUESTIONS):
        for rep in REPS_USED:
            for arm in ARMS:
                yield arm, q, rep


def extract(arm, q, rep):
    """-> (candidates, m3) for one cell.  candidates are (id, text) pairs in
    candidate-id order; m3 counts every registered failure code."""
    d = HERE / "raw" / arm / q / f"r{rep}"
    m3 = {"calls": 0, "parse_failure": 0, "empty_candidate": 0,
          "off_format_count": 0, "off_format_probability": 0,
          "transport_error": 0, "planning_failed": 0, "tokens": 0}
    out = []
    if not d.exists():
        return out, m3

    plan = d / "plan.json"
    if arm in ("B", "D"):
        if not plan.exists():
            m3["planning_failed"] = 1
            return out, m3
        rec = json.loads(plan.read_text())
        m3["tokens"] += tokens_of(rec)
        m3["calls"] += 1
        if not (d / "directions.json").exists():
            m3["planning_failed"] = 1

    for path in sorted(d.glob("c*.json")):
        idx = int(path.stem[1:])
        rec = json.loads(path.read_text())
        m3["calls"] += 1
        m3["tokens"] += tokens_of(rec)
        if rec.get("transport_error"):
            m3["transport_error"] += 1
        obj = parse_json_object(content_of(rec))
        if obj is None:
            m3["parse_failure"] += 1
            continue

        if arm in ("A", "B"):
            text = obj.get("conjecture")
            if not isinstance(text, str):
                m3["parse_failure"] += 1
                continue
            if len(text.strip()) < MIN_CONJECTURE_CHARS:
                m3["empty_candidate"] += 1
                continue
            out.append((f"{arm}-{q}-r{rep}-c{idx:03d}-i00", text.strip()))
        else:
            items = obj.get("candidates")
            if not isinstance(items, list):
                m3["parse_failure"] += 1
                continue
            if len(items) != VS_EXPECTED_ITEMS:
                m3["off_format_count"] += 1
            for j, item in enumerate(items):
                if not isinstance(item, dict):
                    m3["empty_candidate"] += 1
                    continue
                prob = item.get("probability")
                if not isinstance(prob, (int, float)) or prob >= PROBABILITY_CEILING:
                    # Contract check only.  The value is NOT read, and this
                    # never removes the candidate (see the module docstring).
                    m3["off_format_probability"] += 1
                text = item.get("conjecture")
                if not isinstance(text, str) or len(text.strip()) < MIN_CONJECTURE_CHARS:
                    m3["empty_candidate"] += 1
                    continue
                out.append((f"{arm}-{q}-r{rep}-c{idx:03d}-i{j:02d}", text.strip()))
    out.sort(key=lambda pair: pair[0])
    return out, m3


def clusters(vectors, tau):
    """Single-linkage: two candidates share a cluster iff cosine >= tau,
    transitively.  Order-independent, so M1 is a function of the set."""
    n = len(vectors)
    parent = list(range(n))

    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    for i, j in itertools.combinations(range(n), 2):
        if sum(a * b for a, b in zip(vectors[i], vectors[j])) >= tau:
            ri, rj = find(i), find(j)
            if ri != rj:
                parent[ri] = rj
    return len({find(i) for i in range(n)})


def mean_pairwise_distance(vectors):
    pairs = list(itertools.combinations(range(len(vectors)), 2))
    if not pairs:
        return None
    return statistics.fmean(
        1.0 - sum(a * b for a, b in zip(vectors[i], vectors[j])) for i, j in pairs
    )


def _assert_probabilities_unused(source_text):
    """The binding rule, made checkable.

    `extract` is the ONE function allowed to touch a probability field, and
    only for the M3 contract check.  Every other function -- the clustering,
    the distances, the per-arm means, the verdicts -- must be unable to see
    the number at all.  This walks the parsed module rather than the text so
    it cannot be satisfied by a comment, and it fails on an identifier, a
    string key, or an attribute: writing
    `sorted(items, key=lambda c: c["probability"])` inside any metric
    function trips it.
    """
    import ast

    allowed = {"extract"}
    tree = ast.parse(source_text)
    offending = []

    def mentions(node):
        for sub in ast.walk(node):
            if isinstance(sub, ast.Name) and "probability" in sub.id.lower():
                yield sub.lineno, sub.id
            elif isinstance(sub, ast.Attribute) and "probability" in sub.attr.lower():
                yield sub.lineno, sub.attr
            elif isinstance(sub, ast.arg) and "probability" in sub.arg.lower():
                yield sub.lineno, sub.arg
            elif isinstance(sub, ast.Constant) and isinstance(sub.value, str) \
                    and sub.value.strip().lower() == "probability":
                yield sub.lineno, sub.value

    for node in tree.body:
        if isinstance(node, ast.FunctionDef):
            if node.name in allowed or node.name == "_assert_probabilities_unused":
                continue
            offending += [(node.name, ln, what) for ln, what in mentions(node)]
        elif not isinstance(node, (ast.Import, ast.ImportFrom, ast.Assign, ast.Expr)):
            offending += [("<module>", ln, what) for ln, what in mentions(node)]

    if offending:
        raise SystemExit(
            "BINDING VIOLATION (PREREG §6): a self-reported probability value "
            "reached a metric:\n  "
            + "\n  ".join(f"{fn}() line {ln}: {what}" for fn, ln, what in offending)
        )


def main():
    global REPS_USED
    ap = argparse.ArgumentParser()
    ap.add_argument("--reps", default=",".join(str(r) for r in REPS),
                    help="repetitions to analyse; the full set is PREREG "
                         "Appendix A's 1-9. A subset is a DEBUG run and its "
                         "output is not the experiment's result.")
    ap.add_argument("--out", default="metrics.json")
    args = ap.parse_args()
    REPS_USED = [int(r) for r in args.reps.split(",")]

    _assert_probabilities_unused((HERE / "analyse.py").read_text())
    from deepreason.llm.embedder import NeuralEmbedder

    emb = NeuralEmbedder()
    fingerprint = emb.fingerprint()
    frozen = json.loads((HERE / "calibration.json").read_text())["embedder_fingerprint"]
    if fingerprint != frozen:
        print(f"WARNING: embedder fingerprint drift.\n  frozen: {frozen}\n  now:    {fingerprint}\n"
              "  tau* was calibrated under the frozen fingerprint; this is a "
              "different measurement (PREREG §6).", file=sys.stderr)

    # Embeddings are cached on disk by content hash under the frozen
    # fingerprint.  A pure performance measure: the vector for a given text is
    # the same object the uncached path would compute, and the cache key
    # carries the fingerprint so a drifted embedder can never read a stale
    # vector.
    # Outside the repository on purpose: this is a derived, large, and
    # entirely reconstructible file, and the write cone for this tranche is
    # the experiment directory.
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
    for arm, q, rep in cells():
        if not (HERE / "raw" / arm / q / f"r{rep}").exists():
            continue
        cands, m3 = extract(arm, q, rep)
        raw_cells[(arm, q, rep)] = (cands, m3)
        vectors[(arm, q, rep)] = [embed(text) for _, text in cands]
    cache_path.write_text(json.dumps({"fingerprint": fingerprint, "vectors": cache}))

    counts = [len(c) for (c, _) in raw_cells.values() if c]
    n_min = min(counts) if counts else 0

    rows = []
    for arm, q, rep in cells():
        if (arm, q, rep) not in raw_cells:
            continue
        cands, m3 = raw_cells[(arm, q, rep)]
        vecs = vectors[(arm, q, rep)]
        sub = vecs[:n_min]
        emitted = m3["calls"] * (1 if arm in ("A", "B") else VS_EXPECTED_ITEMS)
        emitted = max(emitted, len(cands))
        rows.append({
            "arm": arm, "question": q, "rep": rep,
            "n_valid": len(cands), "n_min_used": len(sub),
            "M1_full": {str(t): clusters(vecs, t) for t in TAU_CURVE + TAU_SENSITIVITY},
            "M1_nmin": {str(t): clusters(sub, t) for t in TAU_CURVE + TAU_SENSITIVITY},
            "M2_full": mean_pairwise_distance(vecs),
            "M2_nmin": mean_pairwise_distance(sub),
            "M3": m3,
            "invalid_rate": (m3["parse_failure"] + m3["empty_candidate"]) / max(1, emitted),
        })

    def mean_m1(arm, q, tau, key="M1_nmin"):
        vals = [r[key][str(tau)] for r in rows if r["arm"] == arm and r["question"] == q]
        return statistics.fmean(vals) if vals else float("nan")

    questions = sorted(QUESTIONS)
    verdicts = {}

    def compare(a, b, label, claim):
        """`claim`: b exceeds a by >= EFFECT_FLOOR."""
        per_q = {q: {str(t): mean_m1(b, q, t) - mean_m1(a, q, t) for t in TAU_SENSITIVITY}
                 for q in questions}
        supported = all(per_q[q][str(t)] >= EFFECT_FLOOR for q in questions for t in TAU_SENSITIVITY)
        refuted = sum(1 for q in questions if per_q[q][str(TAU_STAR)] <= 0) >= 2
        verdicts[label] = {
            "claim": claim,
            "verdict": "SUPPORTED" if supported else ("REFUTED" if refuted else "INCONCLUSIVE"),
            "delta_by_question": per_q,
        }

    compare("A", "B", "H1", "B > A on M1 (stratification; note row 5, grade B)")
    compare("A", "C", "H2", "C > A on M1 (verbalized sampling; note row 7, grade C)")

    per_q_h3 = {}
    for q in questions:
        per_q_h3[q] = {
            "D_minus_B": {str(t): mean_m1("D", q, t) - mean_m1("B", q, t) for t in TAU_SENSITIVITY},
            "D_minus_C": {str(t): mean_m1("D", q, t) - mean_m1("C", q, t) for t in TAU_SENSITIVITY},
        }
    h3_supported = all(
        per_q_h3[q][k][str(t)] >= -EFFECT_FLOOR
        for q in questions for k in ("D_minus_B", "D_minus_C") for t in TAU_SENSITIVITY)
    h3_refuted = any(
        sum(1 for q in questions if per_q_h3[q][k][str(TAU_STAR)] < -EFFECT_FLOOR) >= 2
        for k in ("D_minus_B", "D_minus_C"))
    verdicts["H3"] = {
        "claim": "D >= B and D >= C on M1",
        "verdict": "SUPPORTED" if h3_supported else ("REFUTED" if h3_refuted else "INCONCLUSIVE"),
        "delta_by_question": per_q_h3,
    }

    def arm_invalid_rate(arm):
        rs = [r for r in rows if r["arm"] == arm]
        return statistics.fmean(r["invalid_rate"] for r in rs) if rs else float("nan")

    gap_pp = (arm_invalid_rate("C") - arm_invalid_rate("A")) * 100
    verdicts["H4"] = {
        "claim": "C's gain does not come with M3 degradation (<= 5pp over A)",
        "verdict": "SUPPORTED" if gap_pp <= 5.0 else "REFUTED",
        "invalid_rate_A_pct": arm_invalid_rate("A") * 100,
        "invalid_rate_C_pct": arm_invalid_rate("C") * 100,
        "gap_percentage_points": gap_pp,
    }

    detected = [mean_m1(a, q, TAU_STAR) for a in ARMS for q in questions]
    null_result = (max(detected) - min(detected)) < EFFECT_FLOOR if detected else True

    report = {
        "embedder_fingerprint": fingerprint,
        "tau_star": TAU_STAR,
        "tau_sensitivity": list(TAU_SENSITIVITY),
        "tau_curve": list(TAU_CURVE),
        "n_min": n_min,
        "effect_floor_clusters": EFFECT_FLOOR,
        "cells": rows,
        "arm_totals": {
            a: {
                "tokens": sum(r["M3"]["tokens"] for r in rows if r["arm"] == a),
                "calls": sum(r["M3"]["calls"] for r in rows if r["arm"] == a),
                "valid_candidates": sum(r["n_valid"] for r in rows if r["arm"] == a),
                "invalid_rate_pct": arm_invalid_rate(a) * 100,
                "mean_M1_nmin_at_tau_star": statistics.fmean(
                    [mean_m1(a, q, TAU_STAR) for q in questions]),
                "mean_M2_nmin": statistics.fmean(
                    [r["M2_nmin"] for r in rows if r["arm"] == a and r["M2_nmin"] is not None]),
            } for a in ARMS
        },
        "verdicts": verdicts,
        "instrument_null_result": null_result,
    }
    report["reps_analysed"] = REPS_USED
    (HERE / args.out).write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps({"n_min": n_min, "arm_totals": report["arm_totals"],
                      "verdicts": {k: v["verdict"] for k, v in verdicts.items()},
                      "instrument_null_result": null_result}, indent=2))


if __name__ == "__main__":
    main()
