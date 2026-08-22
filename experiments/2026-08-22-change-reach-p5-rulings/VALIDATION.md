# Validation: codify two operator rulings on reach semantics (P5-reach)
Validated: 2026-08-22, branch `claude/reach-p5-rulings-codify-097nkz`,
base `2a744325f`.

Verdict: **PASS**. Every SPEC.md acceptance check ran and matched. The full
gate is 0 failed, both wheel smokes are green, and `docs_verify` fails only on
the three pre-existing shallow-clone history lookups REQUEST.md C9 named as
the baseline.

## Acceptance checks, item by item

### S1 (R1, R2, C1) — the E0 empty-own-battery exit

    $ python -m pytest "tests/test_reflexive_discipline.py::test_an_empty_own_battery_grounds_no_reach" -q
    1 passed in 0.15s

    $ python -m pytest "tests/test_review_fixes.py::test_reach_clears_to_zero" -q
    1 passed
    (part of the 3-passed run at CHECKLIST step 3)

PASS. The guard is the inner loop's first branch; the second check is the
invariant the placement protects.

### S2 (R3) — the exit-documentation docstring and check

    $ <the amended SUB-evaluation.md check, copied out and run>
    amended check exit=0

    $ python tools/docs_verify.py
    docs_verify: 3 failed   (all three CON-run-identity.md, see below)

PASS. Both moved in the same commit (`1fbf071af`), as R3 requires.

Mutation-proven in both directions, which is what makes the check an
instrument rather than a decoration:

    --- MUTATION A: remove the E0 guard (branch count falls to 4) ---
    check exit=1  (expected 1)
    --- MUTATION B: remove the E0 label from the docstring ---
    check exit=1  (expected 1)
    --- RESTORED ---
    check exit=0  (expected 0)

### S3 (R4, R5, C2, C3) — the coverage-floor pin

    $ python -m pytest "tests/test_reflexive_discipline.py::test_coverage_exactly_at_the_floor_is_a_full_hit" -q
    1 passed in 0.12s

    $ git diff 2a744325f -- src/deepreason/config.py
    (empty)

PASS. `REACH_COVERAGE_MIN` is untouched (C3) and the `<` comparison is
unchanged (C2) — the only edit at that line is the comment on the line above
it. The pin was GREEN before any code moved (CHECKLIST step 1), so it records
a PRESERVED property, not a manufactured one.

### S4 (R6, C2) — the deliberate-`<` note

    $ grep -c "2026-08-22-change-reach-p5-rulings" src/deepreason/measures/reach.py
    3

PASS. Three citations: the E0 bullet, the E5 bullet's floor note, and the
inline comment at the comparison itself.

### S5 (R1, R2) — fixture drift, exactly as forecast

    $ python -m pytest tests/test_reflexive_discipline.py tests/test_review_fixes.py tests/test_prose_refutation_boundaries.py -q
    85 passed in 4.21s

    $ git diff 2a744325f -- tests/ | grep -E "^-[[:space:]]+assert"
    (empty)

PASS. The four tests SPEC.md M2 named moved and no others; no assertion was
deleted or weakened anywhere.

### S6 (R10) — the map moves in the same commits

    $ python tools/docs_verify.py --links
    docs_verify --links: 0 dangling reference(s), 61 document(s)

    $ python tools/docs_verify.py --audit
    docs_verify --audit: 0 finding(s)

PASS. `SUB-evaluation.md` gained the Traps entry for the ruling pair, the
amended exit-documentation check, a new "Which ARTIFACTS are too weak to
ground reach" row, and the floor pin on the coverage-threshold row. Its
`Verified-at:` advanced `7b82206d -> 7cae749c` only after its own `Verify:`
line was re-run (112 passed in 22.29s).

The new Traps check was mutation-proven before being written down, and the
mutation also proves the claim the entry makes:

    --- MUTATION: hoist E0 to the outer loop (the placement the trap forbids) ---
    placement check exit=1  (expected 1)
    FAILED tests/test_review_fixes.py::test_reach_clears_to_zero
    1 failed in 0.11s
    --- RESTORED ---
    placement check exit=0  (expected 0)

### S7 (R7) — the rehearsal re-run

    $ python experiments/2026-08-22-live-reach-rich-run/rehearsal.py
    S2  prose artifact vs wf-carrying seed             exit=E0 empty-own-battery  hits=0 reach_events=0 cov=0.5
    S8a prose conn: candidate vs seed (as shipped)     exit=HIT full              hits=1 reach_events=1 cov=0.667
    S8c prose OFF-subject candidate vs seed (P1 landed) exit=E4 criterion-fail    hits=0 reach_events=0 cov=0.667

PASS, all three as required. The rest of the ladder is unchanged: S1 E3,
S3 HIT full, S4 E4, S5 E4, S6 E4, S8b HIT full, S7 E1. Copied here as
`rehearsal-after-p5-rulings.json`.

### S8 (R8) — the census tooling's exit vocabulary

    $ python -c "...assert 'E0 empty-own-battery' in census.py"
    exit 0

    $ git diff --stat 2a744325f -- .../census.json .../census-verdicts.json
    (empty)

PASS. The vocabulary moved; the committed 96-root measurements did not (A4).

### S9 (R9) — mutation proof, both rulings

RULING 1:

    GUARD DELETED
    FAILED tests/test_reflexive_discipline.py::test_an_empty_own_battery_grounds_no_reach
    1 failed in 0.20s
    --- restore ---
    1 passed in 0.15s

RULING 2:

    BOUNDARY BROKEN: '<' -> '<=' (coverage exactly at the floor becomes provisional)
    FAILED tests/test_reflexive_discipline.py::test_coverage_exactly_at_the_floor_is_a_full_hit
    1 failed in 0.13s
    --- restore ---
    1 passed in 0.12s
    --- tree clean? ---
    (git diff --stat -- src/ empty)

PASS. Four runs, RED/GREEN on each ruling, both mutations reverted.

## Gate results

    $ python -m pytest tests/ -q -n 4
    3820 passed, 6 skipped in 861.17s (0:14:21)

3818 (C9's baseline at `2a744325f`) + the 2 new pins = 3820. **0 failed.**
C9's 5 known MCP-thread flakes did not fire, so no serial re-run was needed.

    $ python tools/docs_verify.py
    docs_verify [full]: 61 documents, 969 checks, 4 workers
      FAIL CON-run-identity.md:200
      FAIL CON-run-identity.md:202 -> fatal: ambiguous argument '1637e808'
      FAIL CON-run-identity.md:204 -> fatal: ambiguous argument 'f304fec1'
    docs_verify: 3 failed

Exactly C9's three pre-existing failures. All three resolve commit hashes or
rename history this shallow clone does not carry; none is in a document this
tranche touched, and all three fail identically at the base commit.

    $ python scripts/wheel_smoke.py                    -> rc=0
    $ python -u scripts/wheel_operational_smoke.py     -> rc=0

Both green, and no pin moved — SPEC.md forecast `wheel_smoke_pins: []` and the
public surface is untouched.

The root sweep was NOT run and is not owed: retired as an instrument (CLAUDE.md,
operator ruling 2026-08-22), and separately unnecessary here — `reach_sweep`
has exactly two callers, both in the live scheduler (SPEC.md M4), so no
committed root is re-derived by anything this change touches.

## Budget

    $ python tools/diff_budget.py 2a744325f --ceiling 210 --paths src tests docs/map
    {"areas": {"src": 25, "tests": 108, "docs/map": 44},
     "total_insertions": 177, "ceiling": 210, "verdict": "WITHIN"}

Plus 30 insertions across the two measurement instruments (`census.py` +19,
`rehearsal.py` +13, -2), for 207 against the amended ceiling of 210. The
ceiling was raised from 150 to 210 by the operator at CHECKLIST step 10, on a
stop presented in the standard format; ledgered as REQUEST.md Amendment 1 /
R12.

## Frozen surfaces

    $ python tools/blast_radius.py --files <every git-added src/tests/map file> \
        --symbols reach_sweep _substantive --against 2a744325f
    "frozen_surface_contacts": [],
    "frozen_adjacent_contacts": [],
    "frozen_surface_verdict": "CLEAR",
    "reachability": [{"symbol": "reach_sweep", "direction": "unchanged"},
                     {"symbol": "_substantive", "direction": "unchanged"}]

No contact, and no drift from SPEC.md's forecast. Re-run over the two
instrument files at step 16: also CLEAR, no direction change.

## Residue — what this tranche did NOT establish

Recorded because "accepted does not mean true".

1. **No live-run evidence.** Every proof here is offline: unit pins, the
   offline rehearsal, and the gate. The rehearsal is a real `Harness` calling
   the real `reach_sweep`, not a stub, but it is ten hand-built scenarios, not
   a run. Whether an empty-own-battery artifact is a shape a live text run
   actually produces is UNMEASURED — PARKED.md P5-reach itself raised the
   possibility that S2's shape "may be a rehearsal artefact". The parallel
   reach-rich live run may settle it; this tranche does not.
2. **The census numbers are stale with respect to E0.** `census.json` and
   `census-verdicts.json` still attribute across E1..E5/HIT the pairs a
   post-E0 reader would put at E0. How many pairs that is, over 96 roots, is
   unknown and deliberately unmeasured (A4).
3. **RULING 2 changed nothing observable.** It is a pin and two notes. Its
   value is that the boundary is now deliberate and defended; no behaviour
   moved, so nothing about it was tested by the change itself — only by the
   mutation that broke it.
4. **P2-reach is untouched and still open.** S5 and S6 still exit E4 on
   `relation-form` alone, so a `predicate:` form gate remains substantive by
   construction. Out of scope, still parked.
