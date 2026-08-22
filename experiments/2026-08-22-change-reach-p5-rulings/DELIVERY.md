# Delivery: codify two operator rulings on reach semantics (P5-reach)
Delivered: 2026-08-22, branch `claude/reach-p5-rulings-codify-097nkz`,
base `2a744325f`.

VALIDATION.md verdict: PASS. Full gate 3820 passed, 0 failed.

## Requirement-by-requirement reconciliation

| # | The operator's words | Delivered | Proof |
|---|---|---|---|
| R1 | "an artifact carrying an EMPTY own commitment battery may NOT ground reach" | `reach_sweep`'s new `E0 empty-own-battery` exit rejects every pair whose reaching artifact has no commitments of its own | `test_an_empty_own_battery_grounds_no_reach` 1 passed; mutation RED/GREEN, VALIDATION.md S9 |
| R2 | "a reaching artifact with no commitments of its own takes a NEW typed rejection exit in reach_sweep" | `E0`, the inner loop's first branch, named and documented in the module docstring's exit ladder | VALIDATION.md S1, S2 |
| R3 | "the new exit and that docstring/check move in the SAME commit" | commit `1fbf071af` carries the guard, the SEVEN-exit docstring, and the amended `SUB-evaluation.md` check together | `git log -1 --stat 1fbf071af`; check mutation-proven both ways, VALIDATION.md S2 |
| R4 | "coverage exactly EQUAL to REACH_COVERAGE_MIN remains a FULL hit, as written (`<` comparison stands)" | the comparison is unchanged; only the comment above it is new | `git diff -- src/deepreason/config.py` empty; mutation to `<=` turns the pin RED, VALIDATION.md S9 |
| R5 | "a test constructing coverage == floor asserts HIT full" | `test_coverage_exactly_at_the_floor_is_a_full_hit` — 1 of 2 criteria qualifying, coverage asserted equal to `Config().REACH_COVERAGE_MIN` before the outcome is asserted | 1 passed, GREEN before any code moved (CHECKLIST step 1) |
| R6 | "a one-line doc note marks the `<` comparison deliberate, citing this tranche" | two: the E5 docstring bullet, and an inline comment at the comparison | `grep -c` 3 tranche citations in `reach.py`, VALIDATION.md S4 |
| R7 | "S2 must now take the NEW exit; S8a must remain HIT; S8c must remain E4. Paste all three." | pasted below and in CHECKLIST step 14; JSON copied here as `rehearsal-after-p5-rulings.json` | VALIDATION.md S7 |
| R8 | "Update the 08-21 census tooling's exit vocabulary if it enumerates exits by name" | `census.py`'s docstring ladder and `rederived_census` counters gained `E0`, in `reach_sweep`'s own order | VALIDATION.md S8; recorded outputs byte-unchanged (A4, parked as P5b) |
| R9 | "mutation-proven on both rulings ... paste both runs" | four runs pasted: guard deleted → RED, restored → GREEN; `<` → `<=` → RED, restored → GREEN | VALIDATION.md S9 |
| R10 | "Map moves in the same commits (the reach-covering document's Traps gains this ruling pair)" | `DR-SUB-evaluation` gained the Traps entry for both rulings with its own mutation-proven check, the amended exit check, a new "Which ARTIFACTS are too weak to ground reach" row, and the floor pin on the coverage row — all in `1fbf071af` | `docs_verify` 3 pre-existing failures only; `--links` 0; `--audit` 0 |
| R11 | "Deliver R-by-R with pasted PROOF, closing with one line per ruling" | this document | below |
| R12 | Amendment 1: "Raise ceiling to 210, continue" | SPEC.md's ceiling amended with the re-itemisation and the measurement that forced it | `diff_budget` WITHIN 207 of 210 |

Constraints C1–C10 all held. C1: nothing outside reach eligibility moved —
`_substantive` and `_STRUCTURAL_PROGRAMS` are untouched, so admission, rank,
criticism and prose immunity are unchanged. C2/C3: neither the comparison nor
`REACH_COVERAGE_MIN`'s value was edited. C8: no file belonging to either
parallel window's live work was written except `rehearsal.py`, an offline
script the live ladder does not run.

## PROOF — the rehearsal against the fixed tree

    S2  prose artifact vs wf-carrying seed              exit=E0 empty-own-battery  hits=0 reach_events=0 cov=0.5   novel=['uhi-energy-balance@r1']
    S8a prose conn: candidate vs seed (as shipped)      exit=HIT full              hits=1 reach_events=1 cov=0.667 novel=['uhi-energy-balance@r1', 'uhi-nocturnal-release@r1']
    S8c prose OFF-subject candidate vs seed (P1 landed) exit=E4 criterion-fail     hits=0 reach_events=0 cov=0.667 novel=['uhi-energy-balance@r1', 'uhi-nocturnal-release@r1']

S2 is the only row this tranche moved. Its full history is now: `E4
criterion-fail` as shipped → `HIT full` after the structural-programs fix →
`E0 empty-own-battery` after these rulings.

## PROOF — the two mutations

    GUARD DELETED
    FAILED tests/test_reflexive_discipline.py::test_an_empty_own_battery_grounds_no_reach
    1 failed in 0.20s
    --- restore ---
    1 passed in 0.15s

    BOUNDARY BROKEN: '<' -> '<=' (coverage exactly at the floor becomes provisional)
    FAILED tests/test_reflexive_discipline.py::test_coverage_exactly_at_the_floor_is_a_full_hit
    1 failed in 0.13s
    --- restore ---
    1 passed in 0.12s

## PROOF — the gates

    python -m pytest tests/ -q -n 4     3820 passed, 6 skipped, 0 failed
    python tools/docs_verify.py         3 failed (all pre-existing, CON-run-identity.md)
    python tools/docs_verify.py --links 0 dangling reference(s)
    python tools/docs_verify.py --audit 0 finding(s)
    python scripts/wheel_smoke.py                 rc=0
    python -u scripts/wheel_operational_smoke.py  rc=0

## One line per ruling — what `reach_sweep` now does that is deliberate

**RULING 1.** `reach_sweep` now REFUSES to ground reach on an artifact that
declares no commitments of its own, taking a named `E0 empty-own-battery` exit
before it reads a single foreign criterion — the Bronze Age discipline applied
to the reaching side, not only the foreign one.

**RULING 2.** `reach_sweep` now treats coverage exactly equal to
`REACH_COVERAGE_MIN` as a FULL hit ON PURPOSE rather than by inheritance: the
`<` comparison is unchanged, but it is documented as a floor meaning "at
least", pinned by a test, and defended by a mutation that proves the pin
notices if anyone loosens it.
