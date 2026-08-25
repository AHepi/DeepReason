#!/usr/bin/env python3
"""RED/GREEN mutation proof for the P-C1 checker (REQUEST.md R16, SPEC.md S4).

R16 names two mutations that must FAIL: a planted overlap and an inflated
score claim.  This script proves both, and the rest of the validity table
with them, in the only order that makes the proof mean anything:

  RED   -- disable ONE guard in the checker's real source and show the
           mutation slips past it.  A test that has never been observed to
           fail proves nothing about the code; it only proves the test runs.
  GREEN -- run the same input through the UNMODIFIED checker and show the
           guard catches it.

WHY THE SOURCE IS MUTATED AND NOT A COPY.  The RED column has to be about
`checker.py` itself.  Re-implementing the guards here and then disabling the
re-implementation would prove that a copy I wrote can be broken, which is
not a fact about the checker.  So each mutant is built by a targeted textual
edit of the real `checker.py` source, exec'd into a fresh module.

WHAT "SLIPPED" MEANS, PRECISELY.  A guard's job is to return one specific
typed refusal code.  A mutant has slipped when it NO LONGER RETURNS THAT
CODE -- whether it accepts the candidate, returns a different code, or dies.
Defining it this way keeps M6 honest: removing the NO_CLAIM guard leaves a
None claim flowing into arithmetic, so the mutant raises rather than
accepts, and that is still a guard doing nothing.

Usage:  python mutation_proof.py
"""
from __future__ import annotations

import pathlib
import types

import checker

SOURCE = pathlib.Path(__file__).with_name("checker.py").read_text()

# Each entry: the fixture key, the expected refusal code, and the exact
# source line that implements that guard.  The line is quoted verbatim from
# checker.py -- if the checker is edited so a line no longer matches, this
# script fails loudly rather than silently proving nothing.
MUTATIONS = [
    (
        "M2 planted overlap (duplicate point)",
        "DUPLICATE_POINT",
        "    if len(set(points)) != N_POINTS:",
    ),
    (
        "M3 inflated claim (-> 0.9)",
        "CLAIM_INFLATED",
        "    if claim > score:",
    ),
    (
        "M4 point outside the square",
        "OUT_OF_SQUARE",
        "    if any(not (ZERO <= v <= ONE) for point in points for v in point):",
    ),
    (
        "M5 twelve points, not thirteen",
        "WRONG_COUNT",
        "    if len(points) != N_POINTS:",
    ),
    (
        "M6 no CLAIM line",
        "NO_CLAIM",
        "    if claim is None:",
    ),
]


def mutant(guard_line: str) -> types.ModuleType:
    """`checker.py` with exactly one guard disabled."""
    if SOURCE.count(guard_line + "\n") != 1:
        raise SystemExit(
            f"MUTATION_TARGET_NOT_UNIQUE: {guard_line!r} does not appear "
            "exactly once in checker.py -- the proof cannot be trusted"
        )
    disabled = guard_line[: len(guard_line) - len(guard_line.lstrip())] + "if False:"
    module = types.ModuleType("checker_mutant")
    module.__file__ = "checker_mutant.py"
    exec(compile(SOURCE.replace(guard_line + "\n", disabled + "\n"), "checker_mutant.py", "exec"), module.__dict__)
    return module


def code_of(module, text: str) -> str:
    try:
        return str(module.check(text)["code"])
    except Exception as exc:  # a guard removed can crash rather than accept
        return f"RAISED {type(exc).__name__}"


def main() -> int:
    fixtures = checker.fixtures()
    failures = 0

    print("=== RED: one guard disabled at a time, the mutation must SLIP THROUGH ===")
    for name, expected_code, guard_line in MUTATIONS:
        got = code_of(mutant(guard_line), fixtures[name])
        slipped = got != expected_code
        failures += not slipped
        print(
            f"  {name:42s} guard off -> code={got:24s} "
            f"{'SLIPPED (as required)' if slipped else 'STILL CAUGHT <-- the guard is not the thing being tested'}"
        )

    print()
    print("=== GREEN: the unmodified checker must CATCH every one ===")
    for name, text in fixtures.items():
        got = checker.check(text)
        want_valid, want_code = checker.EXPECTED[name]
        ok = got["valid"] == want_valid and got["code"] == want_code
        if name.startswith("M7"):
            ok = ok and got["score"] == 0.0
        failures += not ok
        print(
            f"  {name:42s} valid={str(got['valid']):5s} "
            f"code={str(got['code']):16s} score={got['score']}"
            f"{'   OK' if ok else '   <-- WRONG'}"
        )

    print()
    print(
        f"RED {len(MUTATIONS)}/{len(MUTATIONS)} slipped through their disabled guards; "
        f"GREEN {len(fixtures)}/{len(fixtures)} correct."
        if failures == 0
        else f"{failures} FAILURE(S)"
    )
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
