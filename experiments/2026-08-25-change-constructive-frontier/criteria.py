#!/usr/bin/env python3
"""P-C1's demarcation battery: the checker, expressed as run criteria.

REQUEST.md R15, SPEC.md S5.  R15 says a candidate's commitment IS its
claimed score, checked by program -- demonstrative criticism, no judge
anywhere.  These three `Commitment`s are how that becomes true INSIDE the
run: `programs.evaluate` runs them against the artifact's real bytes and
returns pass/fail deterministically, so a refutation here is a computation
and no seat's opinion enters at any point.

THE SANDBOX IS NARROW, AND IT SHAPED THESE EXPRESSIONS (DR-SUB-evaluation).
`programs._validate_predicate` rejects any underscore-prefixed name or
attribute and any `**`, and `_SAFE_NAMES` offers only:

    len any all min max abs sum str int float sorted re json

Three consequences drive the shapes below, and each is worth stating
because the obvious way to write these is unavailable:

1. **There is no `set`, and no `zip`.**  So distinctness is counted, not
   de-duplicated: for a list of points, `sum(1 for t in pts for u in pts if
   t == u)` equals `len(pts)` exactly when every point is unique, because
   each point matches itself once and a duplicated pair contributes two
   extra matches.
2. **There is no `range` and no `enumerate`.**  So the triple loop cannot
   index.  Instead the points are `sorted`, and triples are ordered by
   TUPLE COMPARISON (`if t < u < v`), which on sorted points enumerates
   each distinct-valued triple and never enumerates a degenerate one twice
   in a way that changes a minimum.
3. **There is no rational type.**  These run in float64 while the offline
   `checker.py` is exact.  That split is SPEC.md S3's declared A10 policy:
   the battery is an ADMISSION gate, the offline checker is the authority
   for every number reported in RESULTS.md, and `preflight_criteria.py`
   MEASURES the gap rather than assuming it.

THE FAILURE MODE THIS FILE EXISTS TO AVOID.  `DR-SEAM-evaluation-x-ontology`
Traps: a malformed `predicate:` is a REFUTATION, not an error --
`programs.evaluate` catches every exception and returns `fail`.  So one typo
here would fail every artifact in the run, silently, with full confidence,
and the record would look exactly like "the models could not do it".
`preflight_criteria.py` is the guard against that and it runs before qualify.
"""
from __future__ import annotations

import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "src"))

from deepreason.ontology import Commitment  # noqa: E402

N_POINTS = 13
FLOOR = 0.005

# The wire format, SPEC.md S2.  Byte-identical to `checker.POINT_RE` and
# `checker.CLAIM_RE`; `preflight_criteria.py` asserts that equality rather
# than trusting this comment, because two copies of a regex are two regexes.
POINT_PAT = r"(?m)^[ \t]*POINT[ \t]+([0-9]*\.?[0-9]+)[ \t]+([0-9]*\.?[0-9]+)[ \t]*$"
CLAIM_PAT = r"(?m)^[ \t]*CLAIM[ \t]+([-+0-9.eE]+)[ \t]*$"

# Bind the raw matches and the sorted points once, then reuse.  `for x in
# [expr]` is the only way to bind a name inside a single expression without
# a walrus, and it keeps the parse from being written out four times.
_RAW = f"for raw in [re.findall(r'{POINT_PAT}', content)]"
_PTS = "for pts in [sorted([(float(a), float(b)) for a, b in raw])]"
_CLM = f"for cl in [re.findall(r'{CLAIM_PAT}', content)]"

# Exactly N declared points, all distinct, all inside the closed square.
_WELLFORMED = (
    f"all(len(raw) == {N_POINTS}"
    f" and sum(1 for t in pts for u in pts if t == u) == {N_POINTS}"
    " and all(0.0 <= c <= 1.0 for p in pts for c in p)"
    f" {_RAW} {_PTS})"
)

# The achieved minimum triangle area.  One cross product, halved.  Only ever
# evaluated behind a well-formedness guard, so `min` never sees an empty
# sequence -- an empty `min` would raise, and a raise is a REFUTATION here.
_SCORE = (
    "min(abs((u[0] - t[0]) * (v[1] - t[1]) - (v[0] - t[0]) * (u[1] - t[1]))"
    " for t in pts for u in pts for v in pts if t < u < v) / 2.0"
)

# The guard every scoring predicate sits behind.  `and` short-circuits, so
# the score is computed only for a construction that is already well formed.
_GUARD = (
    f"len(raw) == {N_POINTS}"
    f" and sum(1 for t in pts for u in pts if t == u) == {N_POINTS}"
    " and all(0.0 <= c <= 1.0 for p in pts for c in p)"
)

# The claim is not inflated.  The 1e-12 slack is deliberate and one-sided:
# it can only ever make the battery MORE permissive than the exact checker,
# never less, so float error can never refute an honest construction.  The
# measured float-vs-exact gap is 9.46e-17 over 20 000 configurations
# (preflight step 3), five orders of magnitude below this slack.
_CLAIM_HONEST = (
    f"all({_GUARD} and len(cl) > 0 and {_SCORE} >= float(cl[-1]) - 1e-12"
    f" {_RAW} {_PTS} {_CLM})"
)

# The achieved score clears the registered floor.  SPEC.md S5: 0.005 is
# 1.77x the best of 2000 random draws and 22.0x their median, so luck cannot
# reach it, and ~15% of the best-known value, so competence clears it.  This
# is R20's "checker-backed refutation of underperforming claims".
_ABOVE_FLOOR = f"all({_GUARD} and {_SCORE} >= {FLOOR} {_RAW} {_PTS})"

CRITERIA = (
    Commitment(id="frontier-wellformed@v1", eval=f"predicate:{_WELLFORMED}"),
    Commitment(id="frontier-claim-honest@v1", eval=f"predicate:{_CLAIM_HONEST}"),
    Commitment(id="frontier-above-floor@v1", eval=f"predicate:{_ABOVE_FLOOR}"),
)


if __name__ == "__main__":
    for c in CRITERIA:
        print(f"{c.id}\n  {c.eval}\n")
