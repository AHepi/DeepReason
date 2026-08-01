"""Deterministic paraphrase-pair generator for E0.1 threshold calibration.

Generates 60 same-meaning / different-wording sentence pairs from fixed
templates and a fixed seed, with no reference to any corpus content, so the
planted-duplicate set exists independently of the data it will calibrate
against. Committed with the E0.1 prereg, before any measurement.
"""

from __future__ import annotations

import random

SEED = 20260713

_SUBJECTS = [
    ("the scheduler", "the run coordinator"),
    ("the critic", "the refutation role"),
    ("the append-only log", "the immutable event record"),
    ("the conjecture stream", "the sequence of proposed ideas"),
    ("the token meter", "the spend accountant"),
    ("the browser oracle", "the headless page checker"),
    ("the anti-relapse gate", "the refuted-duplicate blocker"),
    ("the judge ensemble", "the panel of rubric evaluators"),
    ("the memory store", "the local knowledge base"),
    ("the manifest", "the frozen route table"),
]

_PREDICATES = [
    (
        "must reject any candidate that names no refutation conditions",
        "is required to turn away every candidate lacking stated falsifiers",
    ),
    (
        "records every verdict with a content-addressed trace",
        "stores each ruling alongside a hash-addressed execution trace",
    ),
    (
        "never deletes an entry, only supersedes it with a newer one",
        "cannot erase records; it may only layer newer ones above them",
    ),
    (
        "treats a timeout as containment rather than as a failure verdict",
        "counts running out of time as a bounded stop, never as a refutation",
    ),
    (
        "assigns each role exactly one endpoint for the whole run",
        "binds every role to a single fixed endpoint from start to finish",
    ),
    (
        "re-runs inherited tests instead of trusting their old passes",
        "executes adopted checks afresh rather than crediting past results",
    ),
]


def pairs() -> list[tuple[str, str]]:
    rng = random.Random(SEED)
    combos = [(s, p) for s in _SUBJECTS for p in _PREDICATES]
    rng.shuffle(combos)
    out: list[tuple[str, str]] = []
    for (subj_a, subj_b), (pred_a, pred_b) in combos[:60]:
        out.append(
            (
                f"{subj_a.capitalize()} {pred_a}.",
                f"{subj_b.capitalize()} {pred_b}.",
            )
        )
    return out


if __name__ == "__main__":
    for a, b in pairs():
        print(repr((a, b)))
