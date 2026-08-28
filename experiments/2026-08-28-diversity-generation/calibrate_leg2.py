#!/usr/bin/env python3
"""Calibrate LEG 2's distinctness metric on LEG 1's candidates.

Leg 1's registered M1 saturated: tau* = 0.7454 was calibrated on paragraphs
drawn from DIFFERENT documents, and sixty conjectures answering ONE question
occupy a far tighter similarity band than that, so single-linkage joined the
whole cell into one cluster.  The failure is in the instrument, not the arms
-- leg 1's own registered tau curve and its threshold-free M2 both separate
the arms cleanly.

This script fixes the instrument using a label leg 1 already contains and
that no model supplied: arms B and D generate every candidate under a NAMED
DIRECTION from that cell's planning call.  Two candidates from the same
direction are a same-family pair; two from different directions of the same
cell are a different-family pair.  Those are labelled pairs in exactly the
regime the metric must work in -- candidates answering one question.

Two frozen choices come out of here, and both are made on LEG 1 data only,
before any leg 2 response exists:

  tau2      the similarity cut, by Youden's J on the pair labels (linkage-free)
  linkage   single / complete / average, by the adjusted Rand index between
            the clustering it produces at tau2 and the direction partition

Honest limit, stated where it is made: a direction label is a PROXY for idea
identity.  Two candidates inside one direction can still be genuinely
different ideas, so the same-family class is contaminated by construction and
tau2 is, if anything, conservative -- it will under-split rather than
over-split.  What it is not is a threshold chosen after seeing leg 2.
"""
import itertools
import json
import pathlib
import statistics
import sys
import tempfile

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from analyse import extract  # noqa: E402
from driver import N_DIRECTIONS, PER_DIRECTION_CALLS  # noqa: E402
from questions import QUESTIONS  # noqa: E402

LEG1_REPS = range(1, 10)
LINKAGES = ("single", "complete", "average")
TAU_GRID = [round(0.50 + 0.01 * i, 2) for i in range(46)]   # 0.50 .. 0.95


def direction_index(arm, call_index):
    """Arm B issues PER_DIRECTION_CALLS single-candidate calls per direction;
    arm D issues exactly one k=10 call per direction."""
    return call_index // PER_DIRECTION_CALLS if arm == "B" else call_index


def labelled_cells(embed):
    """-> [(vectors, labels)] one entry per B/D cell that planned successfully."""
    out = []
    for arm in ("B", "D"):
        for q in sorted(QUESTIONS):
            for rep in LEG1_REPS:
                cell = HERE / "raw" / arm / q / f"r{rep}"
                if not (cell / "directions.json").exists():
                    continue
                cands, _ = extract(arm, q, rep)
                if len(cands) < 2 * N_DIRECTIONS:
                    continue
                vecs, labels = [], []
                for cid, text in cands:
                    call_index = int(cid.split("-c")[1].split("-")[0])
                    labels.append(direction_index(arm, call_index))
                    vecs.append(embed(text))
                out.append((vecs, labels))
    return out


def cluster(vectors, tau, linkage):
    """Agglomerative clustering to a similarity floor: merge the closest pair
    of clusters while their linkage similarity is >= tau.

    Inter-cluster similarities are maintained incrementally by the
    Lance-Williams update rather than recomputed from members -- exact for all
    three linkages, and the difference between seconds and hours over the 54
    labelled cells x 3 linkages this calibration sweeps.

      single    sim(a+b, k) = max(sim(a,k), sim(b,k))
      complete  sim(a+b, k) = min(sim(a,k), sim(b,k))
      average   sim(a+b, k) = (|a|*sim(a,k) + |b|*sim(b,k)) / (|a|+|b|)
    """
    n = len(vectors)
    if n == 0:
        return []
    sim = {}
    for i, j in itertools.combinations(range(n), 2):
        sim[(i, j)] = sum(a * b for a, b in zip(vectors[i], vectors[j]))
    live = list(range(n))
    size = {i: 1 for i in range(n)}
    members = {i: {i} for i in range(n)}

    def get(i, j):
        return sim[(i, j)] if i < j else sim[(j, i)]

    while len(live) > 1:
        best, pair = None, None
        for a, b in itertools.combinations(live, 2):
            value = get(a, b)
            if best is None or value > best:
                best, pair = value, (a, b)
        if best is None or best < tau:
            break
        a, b = pair
        for k in live:
            if k in (a, b):
                continue
            sa, sb = get(a, k), get(b, k)
            if linkage == "single":
                merged = max(sa, sb)
            elif linkage == "complete":
                merged = min(sa, sb)
            else:
                merged = (size[a] * sa + size[b] * sb) / (size[a] + size[b])
            key = (a, k) if a < k else (k, a)
            sim[key] = merged
        members[a] |= members[b]
        size[a] += size[b]
        live.remove(b)

    assignment = [0] * n
    for label, root in enumerate(live):
        for i in members[root]:
            assignment[i] = label
    return assignment


def adjusted_rand(a, b):
    from collections import Counter
    pairs = Counter(zip(a, b))
    rows, cols = Counter(a), Counter(b)
    comb = lambda x: x * (x - 1) / 2  # noqa: E731
    index = sum(comb(v) for v in pairs.values())
    exp_a = sum(comb(v) for v in rows.values())
    exp_b = sum(comb(v) for v in cols.values())
    n = comb(len(a))
    expected = exp_a * exp_b / n if n else 0.0
    maximum = (exp_a + exp_b) / 2
    return (index - expected) / (maximum - expected) if maximum != expected else 0.0


def main():
    from deepreason.llm.embedder import NeuralEmbedder
    import hashlib

    emb = NeuralEmbedder()
    fingerprint = emb.fingerprint()
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

    cells = labelled_cells(embed)
    cache_path.write_text(json.dumps({"fingerprint": fingerprint, "vectors": cache}))
    if not cells:
        raise SystemExit("no labelled leg-1 cells found")

    same, diff = [], []
    for vecs, labels in cells:
        for i, j in itertools.combinations(range(len(vecs)), 2):
            s = sum(a * b for a, b in zip(vecs[i], vecs[j]))
            (same if labels[i] == labels[j] else diff).append(s)
    same.sort(); diff.sort()

    best = None
    for tau in TAU_GRID:
        tpr = sum(1 for x in same if x >= tau) / len(same)
        fpr = sum(1 for x in diff if x >= tau) / len(diff)
        if best is None or (tpr - fpr) > best[1]:
            best = (tau, tpr - fpr, tpr, fpr)
    tau2 = best[0]

    linkage_scores = {}
    for linkage in LINKAGES:
        aris, counts = [], []
        for vecs, labels in cells:
            assignment = cluster(vecs, tau2, linkage)
            aris.append(adjusted_rand(assignment, labels))
            counts.append(len(set(assignment)))
        linkage_scores[linkage] = {
            "mean_adjusted_rand": statistics.fmean(aris),
            "mean_clusters": statistics.fmean(counts),
            "cells": len(cells),
        }
    chosen = max(LINKAGES, key=lambda k: linkage_scores[k]["mean_adjusted_rand"])

    def pct(xs, q):
        return xs[min(len(xs) - 1, int(q * len(xs)))]

    report = {
        "source": "LEG 1 candidates only (arms B and D, all questions, reps 1-9)",
        "embedder_fingerprint": fingerprint,
        "labelled_cells": len(cells),
        "same_direction_pairs": {"n": len(same), "p10": pct(same, .10),
                                 "median": pct(same, .50), "p90": pct(same, .90)},
        "different_direction_pairs": {"n": len(diff), "p10": pct(diff, .10),
                                      "median": pct(diff, .50), "p90": pct(diff, .90)},
        "tau2": tau2, "youden_J": best[1], "tpr": best[2], "fpr": best[3],
        "linkage_scores": linkage_scores,
        "linkage": chosen,
        "leg1_tau_star_for_contrast": 0.7454,
    }
    (HERE / "calibration_leg2.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
