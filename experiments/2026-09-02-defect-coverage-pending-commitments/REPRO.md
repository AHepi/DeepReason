# Reproduction

Form: **unit-test** (primary regression artifact) + **record-replay**
(the same mechanism on three committed roots, no fixture involved).

## Artifact 1 — the fixed stub

`tests/test_coverage_pending_commitments.py` (new; 17 tests). Built on the
idiom of `tests/test_formalism_optional_rank.py::_root` — one SEED problem, one
artifact per battery, no status hand-set — and faithful to the live shape: the
pending commitment is registered verbatim as the P-A1 record carries it
(`reason-counter@1de371e0006ce0a0bdf77483`):

    Commitment(eval="program:reasoning_observation_pending",
               observation_valued=True,
               budget=Budget(steps=100_000, time_ms=2_000))

### Current output

    $ python -m pytest tests/test_coverage_pending_commitments.py -q
    9 failed, 8 passed in 1.08s

The 9 failures are the defect; the 8 passes are the mutation controls that must
stay green through the fix. Both halves matter — a repair that turns the 9 green
by removing the denominator altogether would turn the controls red.

    RED (the defect)                                     |  today  | required
    -----------------------------------------------------+---------+----------
    declaring 3 pending counterconditions lowers coverage |   0.4   |   1.0
      (`plain` ["ok","ok2"]        -> coverage 1.0)       |         |
      (`declares` + 3 pending      -> coverage 0.4)       |         |
    ...and costs the frontier: frontier == ['plain']      | dropped | both
    a wholly-pending battery scores the FLOOR             |   0.0   | OMITTED
    one pass + one fail + 3 pending                       |   0.2   |   0.5
    table rows ["ok","pend1"] / ["ok","no","pend1","pend2"]|  0.5/0.25|  1.0/0.5
    table rows ["pend1"] / ["pend1","pend2","pend3"]      |   0.0   | OMITTED

    GREEN (must not move)                                            | today
    -----------------------------------------------------------------+-------
    test_fails_still_lowers_coverage                                  | pass
    test_pending_commitments_do_not_inflate_a_score_either            | pass
    test_status_unchanged_by_the_coverage_axis                        | pass
    test_the_minted_spelling_is_the_one_scored_here                   | pass
    table rows ["ok"]=1.0, ["no"]=0.0, ["ok","no"]=0.5, ["no","pend1"]=0.0 | pass

### The sharpest single line

    all_pending scores = {'hv': 0.0, 'reach': 0.0, 'coverage': 0.0}

An artifact whose entire battery is pending scores the coverage **floor**.
`pareto_scores`' own docstring (`scheduler/scheduler.py:206-211`) forbids
exactly this in words: *"writing 0.0 there would put 'nothing to check' on the
same coordinate as 'checked and failed everything' and let a formally-backed
sibling dominate it, which weights rank on conjecture KIND (R-g)."* The shipped
code honours that sentence only for `eval="observation"`, the spelling
`programs.evaluable` screens out. For `program:reasoning_observation_pending` —
the spelling `workloads/text.py:224-226` rewrites every live declaration into —
it does the thing the docstring forbids, verbatim.

## Artifact 2 — record replay (no fixture)

`rescore.py` in this directory, run read-only against three committed roots
with the shipped `pareto_scores` / `capture.pareto.frontier`. Nothing is
constructed; this is the defect as it actually landed.

    root                        survivors  frontier  frontier=harness-minted  dominated=seed
    P-S1 9e48a36b1dec91ee            98        58          58/58  (100%)         40/40 (100%)
    P-A1 4565139800f5ca02            11         7           7/7   (100%)          4/4  (100%)
    P-R1 poietics-program            58        40          40/40  (100%)         18/18 (100%)

    OVERRUN reasons, all three roots: only "observation requires registered
    evidence" (129 / 10 / 65). FAIL verdicts, all three roots: zero.

## Confirms diagnosis

Yes. The stub isolates the single variable the diagnosis names — three extra
`program:reasoning_observation_pending` commitments, nothing else different —
and reproduces both the lowered coordinate (0.4 vs 1.0) and its consequence
(dominated off the frontier). The record replay shows the same mechanism
producing a 100% split on three independent live roots, with no FAIL verdict
anywhere to supply an alternative explanation.

## Post-fix expectation

    $ python -m pytest tests/test_coverage_pending_commitments.py -q
    17 passed

with `plain` and `declares` both at coverage 1.0 and both on the frontier;
`mixed` (one pass, one fail, three pending) at 0.5, not 1.0; `all_pending`
carrying NO `coverage` key at all; and every currently-green control still
green. `tests/test_formalism_optional_rank.py` stays at its present pass count —
extended by this file, not weakened.
