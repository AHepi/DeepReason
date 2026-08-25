#!/usr/bin/env python3
"""The P-C1 checker: a deterministic scorer for Heilbronn constructions.

REQUEST.md R12-R16, SPEC.md S3/S4.  This is the tranche's ONE piece of new
code and it is an EXPERIMENT script -- nothing under `src/` changes (R32).

WHAT IT DECIDES.  A candidate construction claims a number.  This module
says whether the construction is valid and what it actually scores, and it
does so by computation rather than by anyone's reading.  That is the whole
epistemic point: in this program a refutation is a COMPUTATION, so the
criticism is demonstrative and no judge seat is involved anywhere (R15).

THE ARITHMETIC IS EXACT, AND THAT IS A POLICY, NOT AN IMPLEMENTATION
DETAIL (A10, R14).  Coordinates arrive as decimal strings and are parsed
with `Fraction(str)`, which is exact for any decimal.  Heilbronn's score is
a cross product over three points -- no square root anywhere -- so the
entire computation stays in the rationals and NO ROUNDING OCCURS.  Rounding
happens exactly once, at the reporting boundary, to 12 significant figures,
and the exact rational is carried alongside it in the JSON so a reader can
re-derive the rounded figure and never has to trust it.

This is the reason SPEC.md S1 chose Heilbronn over circle packing: packing's
score needs a square root, which forces either a float or a declared
tolerance, and its validity condition is coupled to the claimed radius.
Here validity and score are independent and both are exact.

WHY `Fraction` AND NOT `Decimal`.  Decimal is exact for decimal INPUT but
its arithmetic rounds to a context precision, so a product of two 6-decimal
coordinates is already a rounding decision.  Fraction has no context and
makes no decisions.

Usage:
    python checker.py --score FILE     typed JSON verdict for one candidate
    python checker.py --score -        read the candidate from stdin
    python checker.py --self-test      the S4 mutation table
"""
from __future__ import annotations

import argparse
import itertools
import json
import re
import sys
from fractions import Fraction
from pathlib import Path

# The instance, frozen.  SPEC.md S1.
N_POINTS = 13

# The registered performance floor, SPEC.md S5.  Chosen from
# instance_probe.py, not by feel: 1.77x the best of 2000 random draws and
# 22.0x their median, so luck cannot reach it; ~15% of the best-known value,
# so a competent construction clears it (a plain circle of 13 scores
# 0.013308, i.e. 2.7x this floor).
FLOOR = Fraction(5, 1000)

# The wire format, SPEC.md S2.  Line-anchored keywords rather than bare
# parenthesised pairs: a candidate is mostly prose, and prose contains
# parenthesised numbers.  Anchoring means nothing but a declared point line
# can ever be read as a point.
POINT_RE = re.compile(r"(?m)^[ \t]*POINT[ \t]+([0-9]*\.?[0-9]+)[ \t]+([0-9]*\.?[0-9]+)[ \t]*$")
CLAIM_RE = re.compile(r"(?m)^[ \t]*CLAIM[ \t]+([-+0-9.eE]+)[ \t]*$")

ZERO, ONE = Fraction(0), Fraction(1)


def parse_points(text: str) -> list[tuple[Fraction, Fraction]]:
    """Every declared point, in document order, as exact rationals."""
    return [(Fraction(x), Fraction(y)) for x, y in POINT_RE.findall(text)]


def parse_claim(text: str) -> Fraction | None:
    """The claimed score, or None.  The LAST CLAIM line wins (SPEC.md S2):
    a candidate that revises itself mid-answer is taken at its final word,
    which is the reading least likely to convict it on a superseded draft."""
    found = CLAIM_RE.findall(text)
    if not found:
        return None
    try:
        return Fraction(found[-1])
    except (ValueError, ZeroDivisionError):
        # Fraction accepts "1e-2"; it rejects "1.2.3" and "+-1".  A claim
        # that cannot be read is not a claim.
        return None


def min_triangle_area(points) -> Fraction:
    """The score: the least area over all C(n,3) triangles, exactly.

    area = |cross| / 2 with
    cross = (bx-ax)(cy-ay) - (cx-ax)(by-ay).

    A collinear triple gives cross == 0 and therefore a score of 0.  That is
    not an error and not invalidity -- it is a VALID construction that is
    worthless, and keeping the two apart is what lets the record distinguish
    "the model broke the rules" from "the model obeyed them and lost".
    """
    return min(
        abs((b[0] - a[0]) * (c[1] - a[1]) - (c[0] - a[0]) * (b[1] - a[1]))
        for a, b, c in itertools.combinations(points, 3)
    ) / 2


def _round_sig(value: Fraction, digits: int = 12) -> float:
    """The ONE rounding in this module, at the reporting boundary (A10)."""
    if value == 0:
        return 0.0
    as_float = float(value)
    from math import floor, log10

    exponent = floor(log10(abs(as_float)))
    return round(as_float, digits - 1 - exponent)


def check(text: str) -> dict:
    """The typed verdict.  Validity first, in SPEC.md S3's declared order,
    then the score, then the claim.

    Order matters and is registered: an invalid construction is never
    scored, so an out-of-square candidate can never be reported with a
    number beside it that a later reader might quote.
    """
    points = parse_points(text)
    verdict: dict = {
        "valid": False,
        "code": None,
        "n_points": len(points),
        "n_triples": None,
        "score": None,
        "score_exact": None,
        "claim": None,
        "claim_confirmed": False,
    }

    # V1 -- exactly N point lines.
    if len(points) != N_POINTS:
        verdict["code"] = "WRONG_COUNT"
        return verdict

    # V2 -- every coordinate inside the closed unit square.
    if any(not (ZERO <= v <= ONE) for point in points for v in point):
        verdict["code"] = "OUT_OF_SQUARE"
        return verdict

    # V3 -- pairwise distinct.  Heilbronn's form of "no overlaps": two
    # coincident points make a degenerate triangle with EVERY third point,
    # so a duplicate is not merely a low score, it is a malformed entry.
    if len(set(points)) != N_POINTS:
        verdict["code"] = "DUPLICATE_POINT"
        return verdict

    # V4 -- a readable claim.  R15 makes the claim the commitment, so a
    # candidate without one has committed to nothing and cannot be refuted
    # or confirmed.
    claim = parse_claim(text)
    if claim is None:
        verdict["code"] = "NO_CLAIM"
        return verdict

    score = min_triangle_area(points)
    verdict["valid"] = True
    verdict["n_triples"] = len(list(itertools.combinations(range(N_POINTS), 3)))
    verdict["score"] = _round_sig(score)
    verdict["score_exact"] = str(score)
    verdict["claim"] = _round_sig(claim)

    # The claim is the commitment.  Over-claiming is a refutation; honest
    # UNDER-claiming is not, and the checker reports what was achieved.
    if claim > score:
        verdict["valid"] = False
        verdict["code"] = "CLAIM_INFLATED"
        return verdict

    verdict["claim_confirmed"] = True
    verdict["above_floor"] = score >= FLOOR
    return verdict


# ---------------------------------------------------------------------------
# Fixtures and the S4 mutation table
# ---------------------------------------------------------------------------

def _circle_13() -> str:
    """A plain circle of 13 -- the known-good fixture.  Written out at 6
    decimal places, the same grid a candidate is held to, so the fixture is
    a legal candidate and not a privileged one."""
    import math

    lines = []
    for i in range(N_POINTS):
        angle = 2 * math.pi * i / N_POINTS
        lines.append(
            f"POINT {0.5 + 0.5 * math.cos(angle):.6f} {0.5 + 0.5 * math.sin(angle):.6f}"
        )
    body = "\n".join(lines)
    score = min_triangle_area(parse_points(body))
    # TRUNCATE, never round, when writing the claim.  Rounding a claim to 6
    # decimal places can round it UP past the exact score, which is an
    # inflated claim and is refuted -- as this fixture was, on first run,
    # by the checker's own CLAIM_INFLATED guard.  Truncation can only ever
    # under-claim, and under-claiming is honest (M8).
    micro = int(score * 10**6)  # int() on a Fraction truncates toward zero
    return f"{body}\nCLAIM {micro // 10**6}.{micro % 10**6:06d}\n"


def fixtures() -> dict[str, str]:
    """The S4 table's inputs.  Each mutation is a MINIMAL edit of the
    known-good fixture, so a failure localises to the mutated property."""
    good = _circle_13()
    good_lines = good.strip().split("\n")
    points, claim_line = good_lines[:N_POINTS], good_lines[N_POINTS]

    duplicated = points[:-1] + [points[0]]
    outside = ["POINT 1.500000 0.500000"] + points[1:]
    twelve = points[:-1]
    collinear = (
        [f"POINT {0.1 + 0.05 * i:.6f} {0.1 + 0.05 * i:.6f}" for i in range(3)]
        + points[3:]
    )

    return {
        "M1 known-good construction": good,
        "M2 planted overlap (duplicate point)": "\n".join(duplicated + [claim_line]) + "\n",
        "M3 inflated claim (-> 0.9)": "\n".join(points + ["CLAIM 0.900000"]) + "\n",
        "M4 point outside the square": "\n".join(outside + [claim_line]) + "\n",
        "M5 twelve points, not thirteen": "\n".join(twelve + [claim_line]) + "\n",
        "M6 no CLAIM line": "\n".join(points) + "\n",
        "M7 collinear triple (valid, worthless)": "\n".join(collinear + ["CLAIM 0.000000"]) + "\n",
        "M8 honest under-claim": "\n".join(points + ["CLAIM 0.001000"]) + "\n",
    }


EXPECTED = {
    "M1 known-good construction": (True, None),
    "M2 planted overlap (duplicate point)": (False, "DUPLICATE_POINT"),
    "M3 inflated claim (-> 0.9)": (False, "CLAIM_INFLATED"),
    "M4 point outside the square": (False, "OUT_OF_SQUARE"),
    "M5 twelve points, not thirteen": (False, "WRONG_COUNT"),
    "M6 no CLAIM line": (False, "NO_CLAIM"),
    "M7 collinear triple (valid, worthless)": (True, None),
    "M8 honest under-claim": (True, None),
}


def self_test() -> int:
    ok = 0
    for name, text in fixtures().items():
        got = check(text)
        want_valid, want_code = EXPECTED[name]
        good = got["valid"] == want_valid and got["code"] == want_code
        # M7's whole point is that a valid construction can score zero.
        if name.startswith("M7"):
            good = good and got["score"] == 0.0
        ok += good
        print(
            f"  {name:42s} valid={str(got['valid']):5s} "
            f"code={str(got['code']):16s} score={got['score']}"
            f"{'' if good else '   <-- WRONG'}"
        )
    total = len(EXPECTED)
    print(f"{ok}/{total} cases correct")
    return 0 if ok == total else 1


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--score", metavar="FILE", help="score one candidate ('-' for stdin)")
    parser.add_argument("--self-test", action="store_true", help="run the S4 mutation table")
    args = parser.parse_args()

    if args.self_test:
        return self_test()
    if args.score:
        text = sys.stdin.read() if args.score == "-" else Path(args.score).read_text()
        print(json.dumps(check(text), indent=2, sort_keys=True))
        return 0
    parser.print_help()
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
