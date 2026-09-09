#!/usr/bin/env python3
"""The bare essay's counterpart unit for a per-position comparison — SPEC S8 §10, R19, A5.

    python essay_counterparts.py --units DIR --essays DIR [--out FILE]
    python essay_counterparts.py --self-test

WHAT THIS IS FOR. The primary comparison judges a run's whole composed result
against a bare essay, and the sealed 1.5× length rule will almost certainly
downgrade any win there to NULL, because a composed unit runs several times an
essay's length. The secondary comparison the length rule cannot defeat judges
ONE SURVIVING POSITION against a matched-length piece of a bare essay. A
position unit already exists and is deterministic (`compose_result.py
--per-position`). The essay has no section structure, so its counterpart has to
be DEFINED — and defined by a rule fixed before any reading, or it becomes a
knob that can be turned until the answer comes out right.

THE RULE, registered in PREREG §10 and implemented here exactly:

  1. Split the essay into SENTENCES, in the essay's own order, on the boundary
     `(?<=[.!?])\s+`. Nothing is reordered, dropped, or rewritten.
  2. Consider every PREFIX of that sentence list, from one sentence to all.
  3. Take the prefix whose character count is CLOSEST to the position unit's;
     ties go to the SHORTER prefix, so the choice is total and deterministic.
  4. The match is two-sided. A counterpart matches only when the ratio lies
     within [1/1.5, 1.5] — a piece far SHORTER than the position is as
     unmatched as one far longer, and calling a tenth-length fragment "within
     the length rule" would smuggle the length confound back in under the
     rule meant to exclude it.
  5. Report the achieved ratio for every pair. An unmatched pair is REPORTED
     as unmatched and excluded from the secondary comparison, never padded and
     never quietly included.

WHY SENTENCES, AND WHY THE CLOSEST PREFIX. This rule was written twice before
it worked, and both corrections came from its own self-test rather than from
review, which is why the rule is built and tested BEFORE the pre-registration
seals it.

  * The first version took the FIRST prefix at or above the target. Paragraphs
    in these essays run about 350 characters, so the crossing paragraph
    overshot: achieved ratios 1.73, 1.84, 1.94 — every pair unmatched.
  * The second version took the CLOSEST paragraph prefix and was two-sided.
    Still empty: measured on the first committed essay, the paragraph prefixes
    are 358, 464, 469, 579, 741, 2212, … and NOT ONE lies in the [800, 1800]
    window a ~1 200-character position allows. The granularity of a paragraph
    is simply too coarse for the window the length rule leaves.
  * Sentences are fine enough. The same essay's sentence prefixes include 888,
    1 079, 1 082, 1 322, 1 494 and 1 497 — six inside that window.

So the unit of concatenation is the sentence. Everything else is unchanged: the
essay's own order, a prefix from its opening, closest to the target, ties to
the shorter, two-sided. The rule is no less arbitrary than before and no more —
it is simply capable of matching, which a rule that can only ever report
"unmatched" is not.

WHY THE FIRST PARAGRAPHS AND NOT THE BEST ONES. Choosing the passage of the
essay that best matches a position would be choosing the essay's answer to
that position, which is the judging the instrument is supposed to leave to the
judges. A fixed prefix is arbitrary in a way that is stated in advance and
identical for every pair; "the most relevant passage" is arbitrary in a way
that moves with whoever picks it.
"""
from __future__ import annotations

import argparse
import json
import pathlib
import re
import sys

HERE = pathlib.Path(__file__).resolve().parent
REPO = HERE.parents[2]
D8_ESSAYS = REPO / "experiments/2026-09-05-change-mini-isolation-programme/d8/arm0"
LENGTH_RULE = 1.5


def paragraphs(text: str) -> list[str]:
    """The essay's own paragraphs, in its own order. Reported, not used to
    build the counterpart — see `sentences` and the rule above."""
    return [p.strip() for p in re.split(r"\n\s*\n", text) if p.strip()]


def sentences(text: str) -> list[str]:
    """The essay's own sentences, in its own order.

    The boundary is deliberately crude and deliberately fixed: a smarter
    splitter would be a knob, and this one only has to be the SAME for every
    pair, not linguistically right.
    """
    return [s.strip() for s in re.split(r"(?<=[.!?])\s+", text) if s.strip()]


def counterpart(essay: str, target_chars: int, ratio: float = LENGTH_RULE) -> dict:
    """The matched-length prefix of one essay for one position unit."""

    paras = sentences(essay)
    if not paras or not target_chars:
        return {"text": "", "sentences_taken": 0,
                "sentences_available": len(paras), "chars": 0,
                "target_chars": target_chars, "ratio": None,
                "within_length_rule": False, "shortfall": target_chars,
                "whole_essay_used": not paras}
    # Every prefix, then the closest; ties to the SHORTER, so the choice is
    # total and cannot depend on iteration order.
    best_n, best_gap = 1, None
    for n in range(1, len(paras) + 1):
        gap = abs(len(" ".join(paras[:n])) - target_chars)
        if best_gap is None or gap < best_gap:
            best_n, best_gap = n, gap
    taken = paras[:best_n]
    text = " ".join(taken)
    achieved = len(text) / target_chars
    return {
        "text": text,
        "sentences_taken": len(taken),
        "sentences_available": len(paras),
        "chars": len(text),
        "target_chars": target_chars,
        "ratio": achieved,
        # TWO-SIDED. Far shorter is as unmatched as far longer: a fragment a
        # tenth the length would otherwise pass a rule that exists precisely to
        # keep length out of the comparison.
        "within_length_rule": (1 / ratio) <= achieved <= ratio,
        # Stated, never padded: an essay too short to reach the target is a
        # fact about the essay, and inventing text to close the gap would make
        # the comparison measure the instrument instead of the arms.
        "shortfall": max(0, target_chars - len(text)),
        "whole_essay_used": len(taken) == len(paras),
    }


def load_essays(directory: pathlib.Path) -> list[tuple[str, str]]:
    out = []
    for path in sorted(directory.glob("call-*.json")):
        record = json.loads(path.read_text(encoding="utf-8"))
        content = record.get("content") or ""
        if content.strip():
            out.append((path.stem, content))
    return out


def pair(units_dir: pathlib.Path, essays: list[tuple[str, str]]) -> dict:
    units = sorted(units_dir.glob("position-*.txt"))
    rows = []
    for unit_path in units:
        target = len(unit_path.read_text(encoding="utf-8"))
        for essay_name, essay in essays:
            result = counterpart(essay, target)
            rows.append({
                "unit": unit_path.name, "unit_chars": target,
                "essay": essay_name,
                "counterpart_chars": result["chars"],
                "sentences_taken": result["sentences_taken"],
                "ratio": result["ratio"],
                "within_length_rule": result["within_length_rule"],
                "shortfall": result["shortfall"],
                "whole_essay_used": result["whole_essay_used"],
            })
    matched = [r for r in rows if r["within_length_rule"]]
    return {
        "schema": "essay-counterparts.v1",
        "length_rule": LENGTH_RULE,
        "pairs": len(rows),
        "pairs_within_length_rule": len(matched),
        "pairs_excluded_as_unmatched": len(rows) - len(matched),
        "rows": rows,
    }


def self_test() -> int:
    """Determinism and the rule's own boundary, on committed evidence."""

    essays = load_essays(D8_ESSAYS)
    if len(essays) != 3:
        print(f"expected the three committed D8 essays, found {len(essays)}",
              file=sys.stderr)
        return 1
    sizes = [len(text) for _name, text in essays]
    print(f"three committed D8 essays: {sizes} characters")
    for name, text in essays:
        print(f"  {name}: {len(paragraphs(text))} paragraphs, {len(sentences(text))} sentences")

    # Two runs of the same rule on the same bytes must agree exactly.
    first = [counterpart(text, 1200) for _n, text in essays]
    second = [counterpart(text, 1200) for _n, text in essays]
    assert [f["text"] for f in first] == [s["text"] for s in second], "not deterministic"
    print("deterministic: two runs at target 1200 produced identical counterparts")
    for (name, _t), result in zip(essays, first):
        print(f"  {name}: {result['sentences_taken']}/{result['sentences_available']} "
              f"sentences, {result['chars']} chars, ratio {result['ratio']:.2f}, "
              f"within 1.5x: {result['within_length_rule']}")

    # The boundary the rule must not paper over: a target no prefix can reach.
    huge = counterpart(essays[0][1], 10 ** 6)
    assert huge["whole_essay_used"] and huge["shortfall"] > 0, huge
    assert not huge["within_length_rule"], "an unreachable target must not report as matched"
    print(f"unreachable target: whole essay used, shortfall {huge['shortfall']} "
          f"chars, ratio {huge['ratio']:.4f}, REPORTED as unmatched rather than padded")

    tiny = counterpart(essays[0][1], 20)
    assert not tiny["within_length_rule"], "a far-too-long counterpart must not match"
    print(f"target far below one paragraph: ratio {tiny['ratio']:.2f}, "
          f"REPORTED as unmatched")

    # And the rule must actually be able to MATCH, or the secondary comparison
    # is empty by construction rather than by evidence.
    matched = [counterpart(text, 1200) for _n, text in essays]
    assert all(m["within_length_rule"] for m in matched), [m["ratio"] for m in matched]
    print("at a 1200-character position, all three essays match: ratios "
          + ", ".join(f"{m['ratio']:.2f}" for m in matched))
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--units", default=None)
    ap.add_argument("--essays", default=str(D8_ESSAYS))
    ap.add_argument("--out", default=None)
    ap.add_argument("--self-test", action="store_true")
    args = ap.parse_args()
    if args.self_test:
        return self_test()
    if not args.units:
        ap.error("--units DIR is required (compose_result.py --per-position writes it)")
    payload = pair(pathlib.Path(args.units), load_essays(pathlib.Path(args.essays)))
    print(json.dumps({k: v for k, v in payload.items() if k != "rows"},
                     indent=1, sort_keys=True))
    if args.out:
        pathlib.Path(args.out).write_text(
            json.dumps(payload, indent=1, sort_keys=True) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
