#!/usr/bin/env python3
"""Prove the P-C1 battery works BEFORE the run pays for finding out.

SPEC.md S6.  This exists because of one line in `DR-SEAM-evaluation-x-
ontology`'s Traps section:

    A malformed `predicate:` is a REFUTATION, not an error.

`programs.evaluate` catches EVERY exception from `_validate_predicate` and
from `eval` and returns `fail` with the error in the trace.  So a single
typo in `criteria.py` would refute every artifact the run ever produces,
silently, with no error anywhere in the record -- and the finished run would
read exactly like "the model could not construct anything".  That is a
failure mode worth ~3 000 000 tokens, and it is invisible after the fact.

Four things are checked, and the ladder refuses to qualify unless all four
pass:

  1. Every predicate is sandbox-legal (the thing the trap is about).
  2. The S4 mutation table again -- but through `programs.evaluate`, the
     harness's OWN evaluator, not through `checker.py`.  The offline checker
     being right says nothing about whether the battery agrees with it.
  3. The float-vs-exact gap of SPEC.md S3's declared A10 policy is MEASURED,
     not assumed.
  4. Discrimination: the battery must refuse prose that contains no
     construction, and must refuse a lucky random configuration.  A battery
     that passes everything is not a battery.

Usage:  python preflight_criteria.py
"""
from __future__ import annotations

import random
import sys
from fractions import Fraction
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "src"))
sys.path.insert(0, str(Path(__file__).resolve().parent))

import checker  # noqa: E402
import criteria  # noqa: E402
from deepreason.ontology import Artifact  # noqa: E402
from deepreason.ontology.artifact import Provenance, ProvenanceRole  # noqa: E402
from deepreason.programs import _validate_predicate, evaluate  # noqa: E402

N = checker.N_POINTS
EXACT_BOUND = 1e-12


class _InlineBlobs:
    """`content_text` reads `inline:` refs without touching a store."""

    def get(self, ref):  # pragma: no cover - never reached for inline refs
        raise KeyError(ref)


def verdicts(text: str) -> dict[str, str]:
    """Run all three criteria through the harness's own evaluator."""
    artifact = Artifact(
        id="a" * 64,
        codec="text",
        content_ref="inline:" + text,
        provenance=Provenance(role=ProvenanceRole.CONJECTURER),
    )
    return {
        c.id.split("@")[0].replace("frontier-", ""): evaluate(c, artifact, _InlineBlobs())[0]
        for c in criteria.CRITERIA
    }


def main() -> int:
    failures = 0

    # -- 1 ----------------------------------------------------------------
    print("== 1. every predicate is sandbox-legal ==")
    for c in criteria.CRITERIA:
        try:
            _validate_predicate(c.eval.split(":", 1)[1])
            print(f"  SAFE  {c.id}")
        except Exception as exc:
            failures += 1
            print(f"  UNSAFE {c.id}: {exc}")

    # The two regex copies must be the same regex, or the battery and the
    # checker are reading different documents.
    if criteria.POINT_PAT != checker.POINT_RE.pattern or criteria.CLAIM_PAT != checker.CLAIM_RE.pattern:
        failures += 1
        print("  REGEX DRIFT between criteria.py and checker.py")
    else:
        print("  SAFE  criteria.py and checker.py share the same wire regexes")

    # -- 2 ----------------------------------------------------------------
    # What each criterion is REGISTERED to say about each fixture.  The
    # battery is a conjunction, so a candidate is refuted when ANY member
    # fails; a member is not required to fail for every reason.
    expected = {
        "M1 known-good construction": ("pass", "pass", "pass"),
        # A duplicate breaks well-formedness, and the degenerate triple it
        # creates drops the achieved score to 0, which is below both the
        # claim and the floor.
        "M2 planted overlap (duplicate point)": ("fail", "fail", "fail"),
        "M3 inflated claim (-> 0.9)": ("pass", "fail", "pass"),
        "M4 point outside the square": ("fail", "fail", "fail"),
        "M5 twelve points, not thirteen": ("fail", "fail", "fail"),
        "M6 no CLAIM line": ("pass", "fail", "pass"),
        # Valid, and worthless: the floor is what refutes it, not validity.
        "M7 collinear triple (valid, worthless)": ("pass", "pass", "fail"),
        "M8 honest under-claim": ("pass", "pass", "pass"),
    }
    print()
    print("== 2. the S4 mutation table, through programs.evaluate ==")
    for name, text in checker.fixtures().items():
        got = verdicts(text)
        want = expected[name]
        ok = (got["wellformed"], got["claim-honest"], got["above-floor"]) == want
        failures += not ok
        print(
            f"  {name:42s} wellformed={got['wellformed']:4s} "
            f"claim={got['claim-honest']:4s} floor={got['above-floor']:4s}"
            f"{'   OK' if ok else '   <-- expected ' + str(want)}"
        )

    # -- 3 ----------------------------------------------------------------
    print()
    print("== 3. float-vs-exact agreement (SPEC S3's declared A10 bound) ==")
    rng = random.Random(11)
    worst = 0.0
    trials = 20000
    for _ in range(trials):
        pts = [
            (Fraction(rng.randrange(10**6 + 1), 10**6), Fraction(rng.randrange(10**6 + 1), 10**6))
            for _ in range(N)
        ]
        exact = checker.min_triangle_area(pts)
        as_float = [(float(x), float(y)) for x, y in pts]
        flt = min(
            abs((u[0] - t[0]) * (v[1] - t[1]) - (v[0] - t[0]) * (u[1] - t[1]))
            for t in as_float
            for u in as_float
            for v in as_float
            if t < u < v
        ) / 2.0
        worst = max(worst, abs(float(exact) - flt))
    ok = worst < EXACT_BOUND
    failures += not ok
    print(f"  {trials} configurations at the 6-dp grid")
    print(f"  max |exact - float| = {worst:.12e}   bound {EXACT_BOUND:.0e}   {'OK' if ok else 'EXCEEDED'}")

    # -- 4 ----------------------------------------------------------------
    print()
    print("== 4. discrimination controls ==")
    prose = (
        "The optimal arrangement is achieved by spreading the points as evenly\n"
        "as possible, which maximises the minimum triangle area (0.032). This\n"
        "is a well-studied problem and the answer is known.\n"
    )
    got = verdicts(prose)
    ok = got["wellformed"] == "fail" and got["above-floor"] == "fail"
    failures += not ok
    print(f"  prose with no construction              {got}   {'OK' if ok else '<-- LEAKS'}")

    rng = random.Random(5)
    body = "\n".join(f"POINT {rng.random():.6f} {rng.random():.6f}" for _ in range(N))
    rand_text = body + "\nCLAIM 0.000001\n"
    got = verdicts(rand_text)
    ok = got["above-floor"] == "fail"
    failures += not ok
    print(f"  random configuration (seeded)           {got}   {'OK' if ok else '<-- LEAKS'}")

    got = verdicts(checker._circle_13())
    ok = all(v == "pass" for v in got.values())
    failures += not ok
    print(f"  the plain circle of 13                  {got}   {'OK' if ok else '<-- REFUSES HONEST WORK'}")

    print()
    if failures:
        print(f"PREFLIGHT FAILED -- {failures} problem(s)")
        return 1
    print("PREFLIGHT OK -- the battery discriminates and no predicate is malformed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
