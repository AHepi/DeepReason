#!/usr/bin/env python3
"""Freeze the M1 clustering threshold BEFORE any provider call.

Runs entirely offline on committed repository text: no API key is read and
no network call is made, so this can and must run before the credential is
used.  Its single output, `calibration.json`, carries the number that
PREREG.md then freezes.

Two labelled classes, both constructed deterministically so the number is
reproducible from the commit alone:

  HARD NEGATIVE  two different paragraphs of the SAME document -- shared
                 jargon, shared topic, different idea.  This is the pair
                 the metric must call "distinct", and the pair the E0.1
                 record showed bge-small could not separate
                 (experiments/results/e01_embedder_recalibration_report.json:
                 near_dup_gate separable = False).
  SAME-IDEA      a paragraph against a 60% sentence-subsample of itself,
                 order preserved.  A lower bound on same-idea similarity,
                 not a paraphrase: real paraphrase pairs would need a
                 generator, and a generator call here would contaminate the
                 threshold with the very model under test.
"""
import hashlib
import json
import pathlib
import random
import re
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2] / "src"))
from deepreason.llm.embedder import NeuralEmbedder  # noqa: E402

SEED = 20260828
REPO = pathlib.Path(__file__).resolve().parents[2]
N_PAIRS = 200
MIN_CHARS, MAX_CHARS = 300, 1500


def paragraphs(path):
    text = path.read_text(encoding="utf-8", errors="replace")
    out = []
    for block in re.split(r"\n\s*\n", text):
        block = " ".join(block.split())
        # Tables, code fences and headings are not prose paragraphs; the
        # candidates this threshold will govern are prose.
        if block.startswith(("|", "#", "```", "-", "*", ">")):
            continue
        if MIN_CHARS <= len(block) <= MAX_CHARS:
            out.append(block)
    return out


def sentences(block):
    return [s for s in re.split(r"(?<=[.!?]) +", block) if s.strip()]


def cos(a, b):
    return sum(x * y for x, y in zip(a, b))


def main():
    files = sorted(p for p in (REPO / "docs").glob("*.md"))
    corpus = {}
    for p in files:
        paras = paragraphs(p)
        if len(paras) >= 4:
            corpus[str(p.relative_to(REPO))] = paras
    rng = random.Random(SEED)

    keys = sorted(corpus)
    negatives = []
    while len(negatives) < N_PAIRS:
        k = rng.choice(keys)
        a, b = rng.sample(range(len(corpus[k])), 2)
        negatives.append((corpus[k][a], corpus[k][b]))

    positives = []
    flat = [(k, i) for k in keys for i in range(len(corpus[k]))]
    while len(positives) < N_PAIRS:
        k, i = rng.choice(flat)
        block = corpus[k][i]
        sents = sentences(block)
        if len(sents) < 4:
            continue
        keep = sorted(rng.sample(range(len(sents)), max(2, int(round(0.6 * len(sents))))))
        positives.append((block, " ".join(sents[j] for j in keep)))

    emb = NeuralEmbedder()
    fingerprint = emb.fingerprint()
    cache = {}

    def vec(text):
        key = hashlib.sha256(text.encode()).hexdigest()
        if key not in cache:
            cache[key] = emb.embed(text)
        return cache[key]

    neg = sorted(cos(vec(a), vec(b)) for a, b in negatives)
    pos = sorted(cos(vec(a), vec(b)) for a, b in positives)

    # Youden's J over every observed similarity as a candidate cut.
    best = None
    for tau in sorted(set(round(x, 4) for x in neg + pos)):
        tpr = sum(1 for x in pos if x >= tau) / len(pos)
        fpr = sum(1 for x in neg if x >= tau) / len(neg)
        j = tpr - fpr
        if best is None or j > best[1]:
            best = (tau, j, tpr, fpr)

    def pct(xs, q):
        return xs[min(len(xs) - 1, int(q * len(xs)))]

    report = {
        "seed": SEED,
        "embedder_fingerprint": fingerprint,
        "documents": len(corpus),
        "n_pairs_per_class": N_PAIRS,
        "metric": "cosine similarity of NeuralEmbedder vectors (raw text, no task prefix)",
        "hard_negative_same_document": {
            "n": len(neg), "min": neg[0], "p10": pct(neg, 0.10), "median": pct(neg, 0.50),
            "p90": pct(neg, 0.90), "max": neg[-1],
        },
        "same_idea_subsample": {
            "n": len(pos), "min": pos[0], "p10": pct(pos, 0.10), "median": pct(pos, 0.50),
            "p90": pct(pos, 0.90), "max": pos[-1],
        },
        "tau_star": best[0], "youden_J": best[1], "tpr_at_tau_star": best[2],
        "fpr_at_tau_star": best[3],
    }
    out = pathlib.Path(__file__).with_name("calibration.json")
    out.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
