#!/usr/bin/env python3
"""ARM V's bank of contentless objections — SPEC S4, R7, R9.

    python make_vacuous_bank.py --target-median N --target-iqr LO HI --out FILE
    python make_vacuous_bank.py --self-test

WHAT AN ENTRY MUST BE. An objection of ARM C's shape and ARM C's length that
carries NO INFORMATION ABOUT ITS TARGET. That is the whole design of ARM V: if
ARM C beats ARM 0 and ARM V beats ARM 0 by the same margin, the harness's
advantage is the loop and not the criticism; if ARM C beats ARM V, the content
of criticism is doing work. Everything therefore turns on the entries being
genuinely target-free, which is why the vacuity check is a separate instrument
that reads the bank and its targets and can go red.

WHY A BANK AND NOT A MODEL ASKED TO BE VACUOUS. The brief priced both and chose
this one: a fixed bank carries no information BY CONSTRUCTION, while a model
asked to write contentless objections may quietly comply only partly, and the
partial compliance is invisible in the record. A stub cannot be persuaded.

WHY THE LENGTHS COME FROM ARM C AND NOT FROM AN OPINION. Length is the one
property ARM V must share with ARM C, because a systematically shorter or
longer objection is a different treatment and the comparison would measure
that instead. Tranche 1 ships this generator and its self-test; the REAL bank
is minted in tranche 2 from ARM C's own measured objection lengths (median and
interquartile range over both ARM C runs, pooled and reported before the bank
is generated). The rule is fixed here; the numbers are a measurement, and that
split is what stops the bank from being tuned after the fact.

DETERMINISM. The same seed and the same target distribution produce the same
bank, byte for byte, so the bank a run used can be re-derived from the record
rather than trusted.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import pathlib
import random
import sys

# Sentence stems that say something about ARGUING and nothing about any
# subject matter. Every one is a complaint whose object is left empty: no
# noun from any domain, no claim, no mechanism, no quantity. They are dull on
# purpose -- an interesting generic objection would smuggle in a topic.
STEMS = (
    "The position is asserted more firmly than the support offered for it warrants",
    "An alternative reading is available and is not addressed",
    "The argument moves from its premises to its conclusion faster than the "
    "intervening steps are established",
    "A distinction the argument relies on is used without being drawn",
    "The strongest objection available is not the one the argument answers",
    "What would count as evidence against the position is not stated",
    "The scope of the claim is broader than what is argued for",
    "A term is doing different work in different places in the argument",
    "The conclusion would survive the removal of part of the support offered, "
    "which suggests the support is not what is carrying it",
    "The case rests on a step that is plausible but not defended",
    "An assumption is treated as shared when it is exactly what is in dispute",
    "The argument establishes something weaker than what is concluded",
)
CONTINUATIONS = (
    "This is a gap in the case as presented rather than a rejection of it",
    "The objection stands until that is made explicit",
    "Nothing here settles the matter either way",
    "This much can be said without going further",
    "The point is raised as an objection and not as a counter-proposal",
    "It is offered as a difficulty for the case to answer",
)


def _entry(rng: random.Random, target_chars: int) -> str:
    """One objection, grown to approximately `target_chars` by ADDING whole
    generic clauses — never by padding, and never by naming anything."""

    parts = [rng.choice(STEMS)]
    while len(". ".join(parts)) < target_chars - 40:
        parts.append(rng.choice(STEMS if rng.random() < 0.6 else CONTINUATIONS))
    return ". ".join(parts) + "."


def build(median: int, iqr: tuple[int, int], count: int, seed: int) -> dict:
    rng = random.Random(seed)
    lo, hi = iqr
    entries = []
    for index in range(count):
        # Lengths are drawn across the reported interquartile range rather than
        # all set to the median: ARM C's objections vary, and a bank of
        # identical lengths would be distinguishable from ARM C's on length
        # alone, which is the one thing the arms must share.
        target = lo + ((hi - lo) * index) // max(1, count - 1)
        entries.append({"index": index, "target_chars": target,
                        "text": _entry(rng, target)})
    payload = {
        "schema": "vacuous-bank.v1",
        "seed": seed,
        "target_median": median,
        "target_iqr": list(iqr),
        "count": count,
        "entries": entries,
        "achieved_median": sorted(len(e["text"]) for e in entries)[count // 2],
    }
    payload["digest"] = hashlib.sha256(
        json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()
    return payload


def self_test() -> int:
    """Determinism, length-tracking, and the absence of any subject matter."""

    first = build(median=600, iqr=(400, 900), count=12, seed=20260909)
    second = build(median=600, iqr=(400, 900), count=12, seed=20260909)
    assert first == second, "not deterministic under a fixed seed"
    print(f"deterministic: same seed -> same bank, digest {first['digest'][:16]}")

    lengths = sorted(len(e["text"]) for e in first["entries"])
    print(f"lengths: min {lengths[0]}, median {lengths[len(lengths)//2]}, "
          f"max {lengths[-1]} (target iqr 400-900)")
    assert lengths[0] >= 380, lengths
    assert lengths[-1] <= 1100, lengths

    different = build(median=600, iqr=(400, 900), count=12, seed=1)
    assert different["digest"] != first["digest"], "seed does not change the bank"
    print("a different seed gives a different bank, so the seed is real")

    # The property the whole arm rests on: every entry is built only from the
    # committed generic clauses. Nothing else can enter, because nothing else
    # is ever read.
    vocabulary = " ".join(STEMS + CONTINUATIONS).lower()
    for entry in first["entries"]:
        for sentence in entry["text"].rstrip(".").split(". "):
            assert sentence.lower() in vocabulary, sentence
    print(f"every sentence in every entry comes from the {len(STEMS)} stems and "
          f"{len(CONTINUATIONS)} continuations, and from nowhere else")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--target-median", type=int, default=None)
    ap.add_argument("--target-iqr", type=int, nargs=2, default=None)
    ap.add_argument("--count", type=int, default=48)
    ap.add_argument("--seed", type=int, default=20260909)
    ap.add_argument("--out", default=None)
    ap.add_argument("--self-test", action="store_true")
    args = ap.parse_args()
    if args.self_test:
        return self_test()
    if args.target_median is None or args.target_iqr is None:
        ap.error("--target-median and --target-iqr are REQUIRED and have no "
                 "defaults: they are ARM C's own measured objection lengths, "
                 "and a default would let the bank be built before the "
                 "measurement exists")
    payload = build(args.target_median, tuple(args.target_iqr), args.count, args.seed)
    text = json.dumps(payload, indent=1, sort_keys=True) + "\n"
    if args.out:
        pathlib.Path(args.out).write_text(text, encoding="utf-8")
        print(f"{args.out}: {payload['count']} entries, achieved median "
              f"{payload['achieved_median']}, digest {payload['digest']}")
    else:
        sys.stdout.write(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
