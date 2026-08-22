# Spec for: codify two operator rulings on reach semantics (P5-reach)
Traces: every item cites R/C numbers from REQUEST.md. Untraceable items are bugs.

Map ids in force (resolved in REQUEST.md, not re-derived here):
`DR-INV-frozen-surfaces`, `DR-SEAM-evaluation-x-rules`, `DR-SUB-evaluation`,
`DR-CON-warrants-and-attacks`.

## Items

### S1 (R1, R2, C1) — the E0 empty-own-battery exit

`src/deepreason/measures/reach.py`, `reach_sweep`.

before: the inner per-pair loop begins at `if pid in addressed[aid] or not
problem.criteria`. An ACCEPTED, addressed artifact whose
`interface.commitments` is empty is a full reach candidate; rehearsal S2 shows
it taking `HIT full` and recording one reach event.

after: the inner loop's FIRST branch is the new exit — `if not carried:
continue` — so every pair whose reaching artifact carries no commitments of
its own is rejected before any criterion is read.

    for pid, problem in harness.state.problems.items():
        if not carried:
            continue
        if pid in addressed[aid] or not problem.criteria:
            continue

Nothing else in the function moves. `_substantive`, `_STRUCTURAL_PROGRAMS`,
`_verdict`, the coverage comparison, the Measure emission and the
clear-to-zero accounting are untouched (C1: only reach ELIGIBILITY moves).

**Placement is measured, not chosen by taste** — see M1. The guard is
loop-INVARIANT and is deliberately NOT hoisted above the inner loop: hoisting
it skips the outer loop's clear-to-zero accounting, so an empty-battery
artifact carrying a stale reach count would stay ranked on it forever, and
`tests/test_review_fixes.py::test_reach_clears_to_zero` — the test that exists
for exactly that invariant — goes RED. A comment at the guard states this
constraint, per CLAUDE.md's comment rule.

    accept: python -m pytest "tests/test_reflexive_discipline.py::test_an_empty_own_battery_grounds_no_reach" -q
            -> 1 passed
    accept: python -m pytest "tests/test_review_fixes.py::test_reach_clears_to_zero" -q
            -> 1 passed (the invariant the placement protects)

### S2 (R3) — the exit-documentation docstring and check

`src/deepreason/measures/reach.py` module docstring; `docs/map/SUB-evaluation.md`
line 218-227 (the trap and its `check:`). **Same commit as S1** (R3, verbatim).

before: "exactly one of SIX exits"; six labelled bullets `E1 no-criteria` ..
`HIT full`; the map check asserts `len(conts) == 4` inner-loop `continue`
statements and all six labels present in the docstring.

after: "exactly one of SEVEN exits"; a new FIRST bullet `E0
empty-own-battery` stating the ruling and its basis; the map check asserts
`len(conts) == 5` and all SEVEN labels. The check keeps its shape — it is the
instrument that makes an undocumented exit impossible — so an eighth exit
added without documenting it still fails it.

Naming (A2): `E0`, not `E6`. The existing labels E1..E5 are the recorded
vocabulary of `experiments/2026-08-21-measure-reach-firing/CENSUS.md` and its
committed JSON; renumbering would invalidate numbers already in the record,
and the new exit is taken BEFORE E1, so `E0` is both order-true and
non-destructive.

    accept: python -c "<the amended SUB-evaluation.md check>" -> exit 0
    accept: python tools/docs_verify.py  -> failures == the 3 pre-existing
            shallow-clone ones named in C9, no others

### S3 (R4, R5, C2, C3) — the coverage-floor pin

`tests/test_reflexive_discipline.py`, new test.

before: no test constructs coverage exactly equal to the floor. The census
proves the gate has never decided anything: `E5` rejected 0 of 1 178 430 pairs
over 96 committed roots, so the `<` boundary is inherited, never exercised.

after: `test_coverage_exactly_at_the_floor_is_a_full_hit` builds a foreign
problem with two criteria, one of them substantive-and-evaluable, giving
coverage exactly `1/2 == 0.5 == REACH_COVERAGE_MIN`, and asserts `HIT full`:
the pair is in `reach_sweep`'s returned hits, `state.reach[aid] == 1.0`,
`(aid, pid) in state.addr`, and NO `reach-provisional` Measure event was
logged. The last assertion is what distinguishes this from E5 and is what
goes RED if the boundary is ever moved.

NO production line changes (C2: "`<` comparison stands"; C3: the VALUE of
`REACH_COVERAGE_MIN` is not touched). This item is a pin, not an edit.

    accept: python -m pytest "tests/test_reflexive_discipline.py::test_coverage_exactly_at_the_floor_is_a_full_hit" -q
            -> 1 passed
    accept: git diff -- src/deepreason/config.py -> empty
    accept: git diff -- src/deepreason/measures/reach.py | grep -c "coverage_min" -> 0 changed lines matching the comparison itself

### S4 (R6, C2) — the deliberate-`<` note

Two one-line notes, both citing this tranche:

1. `src/deepreason/measures/reach.py`, the `E5 coverage` docstring bullet: one
   sentence recording that coverage exactly EQUAL to `coverage_min` is a FULL
   hit by operator ruling 2026-08-22, so a floor means "at least".
2. `src/deepreason/measures/reach.py`, an inline comment at the comparison
   itself: the same constraint where a reader about to write `<=` will see it.
   This is a constraint the code cannot show (CLAUDE.md's comment rule), not
   narration of the change.

    accept: grep -n "2026-08-22-change-reach-p5-rulings" src/deepreason/measures/reach.py
            -> at least 2 hits (the E5 bullet and the comparison comment)

### S5 (R1, R2 — fixture drift, PREDICTED IN ADVANCE)

Four existing tests create their reaching artifact through
`Harness.create_artifact(...)` with no `interface=`, which defaults to
`Interface()` — an EMPTY own battery. Under S1 they exercise E0 instead of
what they were written to pin. Each is minimally updated to give the reaching
artifact the battery a production artifact actually gets (`compile_interface`
pins the home problem's criteria), which restores the pair each test was
about. This is the CLAUDE.md-sanctioned fixture update: predicted by the
design doc, before the code moved.

Measured, not guessed — M2 lists exactly these four and no others:

| test | change |
|---|---|
| `test_reflexive_discipline.py::test_genuine_cross_problem_survival_registers_addressing` | reaching artifact carries `["k-moon"]` |
| `test_reflexive_discipline.py::test_thin_coverage_yields_provisional_not_reach` | reaching artifact carries `["k-moon"]` |
| `test_reflexive_discipline.py::test_debt_problem_asks_the_genuine_question` | reaching artifact carries `["k-moon"]` |
| `test_review_fixes.py::test_reach_verdict_cache_consistent` | reaching artifact carries `["k-a"]` |

No assertion is weakened anywhere; each test keeps every assertion it had.

    accept: python -m pytest tests/test_reflexive_discipline.py tests/test_review_fixes.py tests/test_prose_refutation_boundaries.py -q -> 0 failed
    accept: git diff -- tests/ | grep -E "^-\s+assert" -> empty (no assertion deleted or weakened)

### S6 (R10) — the map moves in the same commits

`docs/map/SUB-evaluation.md`:
- the exit-documentation trap entry and its `check:` (S2 above);
- a NEW `Traps` entry for this ruling pair: what E0 forbids, what the floor
  boundary means, the two ruling texts' authority date, and this tranche id,
  with a `check:` that runs the two new tests and asserts the docstring
  carries the E0 label. A `Traps` entry is never deleted, only rewritten.
- the "Where to change what" row for the reach coverage threshold gains the
  boundary ruling's pin test alongside the existing provisional test.

`Verified-at:` on `SUB-evaluation.md` advances ONLY if that document's checks
are actually re-run in the same step (SCHEMA.md; a false stamp is worse than a
stale one).

    accept: python tools/docs_verify.py -> failures == C9's 3 pre-existing only
    accept: python tools/docs_verify.py --links -> 0 unresolved
    accept: python tools/docs_verify.py --audit -> no new un-failable check

### S7 (R7) — the rehearsal re-run

`experiments/2026-08-22-live-reach-rich-run/rehearsal.py` carries its OWN copy
of the exit classifier (it is a printer, not a reader: it calls the real
`reach_sweep` and separately attributes the exit for the report). Its
classifier gains the E0 branch first, mirroring S1's order, or S2 would be
misreported as `HIT full` while `reach_sweep` returned nothing.

Then re-run it against the fixed tree and paste S2, S8a, S8c. Expected:
S2 → the new E0 exit, 0 hits, 0 recorded reach events; S8a → `HIT full`
unchanged; S8c → `E4 criterion-fail` unchanged.

The regenerated `rehearsal.json` is also copied into THIS tranche as
`rehearsal-after-p5-rulings.json`, so the tranche is self-contained and the
proof does not depend on another tranche's working file.

    accept: python experiments/2026-08-22-live-reach-rich-run/rehearsal.py
            -> S2 exit == the E0 label; S8a exit == "HIT full"; S8c exit ==
               "E4 criterion-fail"

### S8 (R8) — the 08-21 census tooling's exit vocabulary

`experiments/2026-08-21-measure-reach-firing/census.py` enumerates exits by
name in both its module docstring ("E1 no-criteria" .. "HIT") and its
`rederived_census` counters. It gains the E0 branch in the same position
`reach_sweep` takes it, so the instrument keeps attributing every pair to the
exit the current reader actually takes — which is that pass's stated purpose.

`census_new_root.py` in the live-reach-rich-run tranche is an import shim over
this file and needs no edit; it inherits the vocabulary.

RECORDED OUTPUTS ARE NOT RE-DERIVED (A4). `census.json` and
`census-verdicts.json` stay exactly as measured on 2026-08-21 under the old
vocabulary; re-deriving them is a MEASUREMENT over 96 committed roots, which
this change tranche was not asked for and which the retired-sweep ruling
(CLAUDE.md 2026-08-22) argues against. A one-line note in `census.py` records
that the committed JSON predates E0.

    accept: python -c "import pathlib; s=pathlib.Path('experiments/2026-08-21-measure-reach-firing/census.py').read_text(); assert 'E0 empty-own-battery' in s"
    accept: git diff --stat -- experiments/2026-08-21-measure-reach-firing/census.json experiments/2026-08-21-measure-reach-firing/census-verdicts.json -> empty

### S9 (R9) — mutation proof, both rulings

Two mutations, each applied to the working tree, run, and reverted; both runs
pasted into VALIDATION.md.

- **Ruling 1**: delete the `if not carried: continue` guard →
  `test_an_empty_own_battery_grounds_no_reach` must go RED. Restore → GREEN.
- **Ruling 2**: break the boundary the other way — change the comparison to
  `<=` so coverage exactly 0.5 becomes PROVISIONAL →
  `test_coverage_exactly_at_the_floor_is_a_full_hit` must go RED. Restore →
  GREEN. (The mutation is applied and reverted; C2's "`<` stands" is about the
  DELIVERED tree, and a mutation that is never committed is the proof that it
  stands.)

    accept: four pasted pytest runs in VALIDATION.md — RED, GREEN, RED, GREEN

### S10 (R11) — delivery

`DELIVERY.md` reconciles R1..R11 one by one against the operator's verbatim
words with pasted proof, and closes with one line per ruling naming what
`reach_sweep` now does that is deliberate.

    accept: DELIVERY.md contains a row for every R1..R11 with a proof pointer

## Measurements

M1 — placement of the E0 guard is decided by measurement, not preference.
The guard was applied at the INNER-loop position on a scratch tree and the
reach ring run; `test_reach_clears_to_zero` — the test whose entire subject is
"a once-reaching artifact that no longer reaches must be cleared to 0.0, not
ranked forever on a stale count" — stayed GREEN, because the outer loop still
reaches its accounting for an empty-battery artifact. Hoisting the guard to
the outer loop would `continue` past that accounting. Command and output:

    $ python -m pytest tests/test_reflexive_discipline.py tests/test_review_fixes.py \
        tests/test_prose_refutation_boundaries.py -q
    FAILED tests/test_reflexive_discipline.py::test_genuine_cross_problem_survival_registers_addressing
    FAILED tests/test_reflexive_discipline.py::test_thin_coverage_yields_provisional_not_reach
    FAILED tests/test_reflexive_discipline.py::test_debt_problem_asks_the_genuine_question
    FAILED tests/test_review_fixes.py::test_reach_verdict_cache_consistent - Asse...
    4 failed, 79 passed in 5.13s

`test_reach_clears_to_zero` is absent from that FAILED list. Supports S1's
placement and its comment.

M2 — the fixture drift is exactly four tests, in two files. Same run as M1;
the four named FAILED lines are the complete set. Supports S5, and is the
census the drift forecast is written from rather than recalled.

M3 — the wider ring is unaffected. Under the same scratch guard:

    $ python -m pytest tests/test_scheduler.py tests/test_module_fingerprints.py \
        tests/test_chaos_invariants.py tests/test_easy.py tests/test_blast_radius.py \
        tests/test_programs.py -q
    85 passed, 1 skipped in 499.88s (0:08:19)

Supports the Blast-radius census's MUST NOT MOVE classifications.

M4 — `reach_sweep` has exactly two callers, both in the live scheduler:

    $ grep -rn "reach_sweep" src/ | grep -v "measures/reach.py"
    src/deepreason/scheduler/scheduler.py:35:from deepreason.measures.reach import reach_sweep
    src/deepreason/scheduler/scheduler.py:2024:            reach_sweep(harness, coverage_min=config.REACH_COVERAGE_MIN)
    src/deepreason/scheduler/scheduler.py:2274:        reach_sweep(

Replay and `verify_root` do not call it — they APPLY recorded Measure events.
Supports the record-observable guardrail below: every committed root stays
valid and byte-identical, because nothing re-runs the sweep over it.

M5 — the scratch measurement patch was fully reverted before this spec was
written:

    $ git checkout -- src/deepreason/measures/reach.py && git status --short
    (empty)

## Assumptions (operator may override)

A1 (Q1): the E0 guard is taken in the INNER per-pair loop, not the outer
per-artifact loop — assumed, operator may override. Not a taste call: M1
measures that the outer position breaks the documented clear-to-zero
invariant. Observable behaviour of the two placements is otherwise identical.

A2 (Q2): the new exit is named **`E0 empty-own-battery`** — assumed, operator
may override. `E0` rather than `E6` because it is taken before E1 and because
E1..E5 are the recorded census vocabulary; renumbering would falsify numbers
already committed in `CENSUS.md` and its JSON.

A3 (Q3): "EMPTY own commitment battery" is read narrowly as
`artifact.interface.commitments` being empty — assumed, operator may override.
That is `carried`, the set `reach_sweep` already computes, and it is the
reading the brief's own evidence pointer uses (rehearsal S2, `"carried": []`).
An interface whose commitments are all UNREGISTERED is not empty and is not
covered; nothing in the ruling asks for it.

A4 (Q4): `census.py`'s exit VOCABULARY is updated; its committed measurement
OUTPUTS are not re-derived — assumed, operator may override. R8 says "update
the ... exit vocabulary", not "re-measure". Re-deriving is a 96-root
measurement this tranche was not asked for.

A5: the four fixture updates in S5 give the reaching artifact the home
problem's criteria as its own battery, because that is what the production
path (`workloads/models.py::compile_interface`) pins — assumed, operator may
override. The alternative, asserting the new E0 outcome in those tests
instead, would delete the four properties they were written to pin.

## Questions for operator (STOP if non-empty)

None. Every open question in REQUEST.md resolved to an assumption above: Q1 by
measurement (M1), Q2 and Q3 by the smallest non-destructive reading, Q4 by the
requirement's own wording. No fork changes behaviour, files touched, or effort
by more than a line.

## Out of scope (explicit)

- **P2-reach** (a `predicate:` form gate is substantive by construction) —
  not requested; still parked in the structural-programs tranche's PARKED.md.
  Rehearsal S5/S6 will still exit E4 on `relation-form` after this change.
- **P6-reach** (the missing `SEAM-evaluation-x-warrants-and-attacks`
  document) — not requested; still parked.
- Changing `REACH_COVERAGE_MIN`'s value — forbidden by C3.
- Changing the `<` comparison — forbidden by C2.
- Re-deriving the 08-21 census outputs — A4.
- Any change to `_substantive` / `_STRUCTURAL_PROGRAMS`, i.e. the surface
  `DR-SEAM-evaluation-x-rules` shares with `rules/warrants.py::formally_backed`
  — neither ruling touches it (C1).
- The root sweep — retired as an instrument (CLAUDE.md, operator ruling
  2026-08-22).

## Frozen-surface contact forecast

`tools/blast_radius.py` (Rung G6), run on the full target set, verbatim:

    "frozen_surface_contacts": [],
    "frozen_adjacent_contacts": [],
    "frozen_surface_verdict": "CLEAR"

    "disclosure_summary": "This change touches none of the five frozen
    surfaces. 2 test file(s) and 5 map document(s) assert on the touched
    targets today. ..."

Command:

    python tools/blast_radius.py \
      --files src/deepreason/measures/reach.py tests/test_reflexive_discipline.py docs/map/SUB-evaluation.md \
      --symbols reach_sweep _substantive REACH_COVERAGE_MIN

One `reachability` entry came back `UNKNOWN` — `REACH_COVERAGE_MIN` (a module
constant, not a call target the gate can trace). Per `dr-spec-change` step 5,
the manual grep cross-check is therefore REQUIRED for it and is pasted in the
census below. `reach_sweep` and `_substantive` both resolved `REACHABLE`.

Record-observable guardrail: this change adds NO new field or record type. It
REMOVES a Measure event that would otherwise be emitted, in live runs only.
M4 shows `reach_sweep` is called only by the live scheduler, never by replay
or `verify_root`, so every committed root replays byte-identically and no
sweep probe is owed. No `tools/root_sweep.py` change (also: the sweep is
retired).

## Blast-radius census

From `tools/blast_radius.py`'s `consumers` field, every hit classified.

`consumers.tests` for `reach_sweep`:

| hit | verdict |
|---|---|
| tests/test_reflexive_discipline.py:20 (import) | MUST NOT MOVE |
| tests/test_reflexive_discipline.py:47 `test_textual_reference_alone_creates_no_reach` | MUST NOT MOVE (asserts no reach; E0 cannot turn a non-hit into a hit) |
| tests/test_reflexive_discipline.py:70 `test_structural_programs_never_ground_reach` | MUST NOT MOVE (already `== []`) |
| tests/test_reflexive_discipline.py:83 `test_genuine_cross_problem_survival_registers_addressing` | **EXPECTED TO MOVE** — S5 |
| tests/test_reflexive_discipline.py:103 `test_thin_coverage_yields_provisional_not_reach` | **EXPECTED TO MOVE** — S5 |
| tests/test_reflexive_discipline.py:121 `test_debt_problem_asks_the_genuine_question` | **EXPECTED TO MOVE** — S5 |
| tests/test_reflexive_discipline.py:366 `test_a_well_formedness_gate_cannot_veto_a_reach_hit` | MUST NOT MOVE (builds its artifact through `compile_interface`, so its battery is non-empty) |
| tests/test_review_fixes.py:241,263 `test_reach_clears_to_zero` | MUST NOT MOVE — and it is the invariant A1's placement exists to protect (M1) |
| tests/test_review_fixes.py:463,475,482 `test_reach_verdict_cache_consistent` | **EXPECTED TO MOVE** — S5 |

`consumers.tests` for `_substantive` — tests/test_prose_refutation_boundaries.py
:562,595,600 and tests/test_reflexive_discipline.py:20,293,301,304,365: ALL
MUST NOT MOVE. `_substantive` is not edited (C1).

`consumers.map_checks` for `src/deepreason/measures/reach.py`:

| hit | verdict |
|---|---|
| docs/map/CON-warrants-and-attacks.md:37 | MUST NOT MOVE (`_substantive` row) |
| docs/map/SEAM-evaluation-x-rules.md:4 (`Owns:`) | MUST NOT MOVE |
| docs/map/SEAM-evaluation-x-rules.md:200 (verdict-cache check) | MUST NOT MOVE |
| docs/map/SUB-evaluation.md:126 (`def reach_sweep(` exists) | MUST NOT MOVE |
| docs/map/SUB-evaluation.md:153 (`reach-provisional` tag present) | MUST NOT MOVE |
| docs/map/SUB-evaluation.md:177 (`_STRUCTURAL_PROGRAMS` / `_substantive` shape) | MUST NOT MOVE |
| docs/map/SUB-evaluation.md:216 (derived-structural-set check) | MUST NOT MOVE |
| docs/map/SUB-evaluation.md:227 (exit-documentation check) | **EXPECTED TO MOVE** — S2 |
| docs/map/SUB-rules.md:182 | MUST NOT MOVE (`_substantive` reference) |

`consumers.map_checks` for `REACH_COVERAGE_MIN` — docs/map/SUB-evaluation.md
:169 (the "Where to change what" row) **EXPECTED TO MOVE** (S6, gains the pin
test); :176 (`REACH_COVERAGE_MIN: float = 0.5` literal) MUST NOT MOVE (C3).

Manual cross-check required by the `UNKNOWN` reachability entry:

    $ grep -rn "REACH_COVERAGE_MIN" tests/ docs/map/
    docs/map/SUB-evaluation.md:169
    docs/map/SUB-evaluation.md:176

No test asserts on the constant. Both map hits are classified above.

`consumers.map_checks` for `tests/test_reflexive_discipline.py` — 15 hits
across CON-scheduler-ranking, SEAM-evaluation-x-rules, SEAM-scheduler-x-rules,
SUB-evaluation, SUB-ontology, SUB-scheduler. All are `python -m pytest
<file>::<nodeid>` checks naming EXISTING node ids; this change ADDS node ids
and renames none, so ALL MUST NOT MOVE. `docs/map/SUB-evaluation.md:169` is
the one exception, EXPECTED TO MOVE by S6's own edit.

`qualification_digest`: `[]`. `wheel_smoke_pins`: `[]` — the public surface
(console entry points, MCP tool set, wheel layout) is untouched, so no smoke
pin moves and no smoke re-run is owed by the pin rule. The smokes are still
run once at the validation boundary as a control.

## Budget

Itemized changed lines (production + tests + map + instruments; tranche
artifacts excluded, as they are the workflow's own record):

    S1 reach.py guard + comment            8
    S2 reach.py docstring + map check     24
    S3 new floor-pin test                 30
    S4 the two deliberate-`<` notes        4
    S5 four fixture updates               12
    S6 map Traps entry + row              26
    S7 rehearsal.py classifier             8
    S8 census.py vocabulary + note        10
    new E0 test (S1's accept)             28

    $ python3 -c "print(sum([8,24,30,4,12,26,8,10,28]))"
    150

~150 changed lines, 3 commits:
1. S1+S2+S3+S4+S5+S6 — the rulings, their docstring, their check, their
   tests, their map. R3 requires the exit and its documentation in ONE commit,
   and S5's fixtures must land with S1 or the tree is red between commits.
2. S7+S8 — the two measurement instruments' vocabulary, plus the pasted
   rehearsal evidence.
3. VALIDATION.md + DELIVERY.md.

Frozen surfaces touched: none (`frozen_surface_verdict: CLEAR`, pasted above).

Rubric: 6/6 yes — every R1..R11 has a spec item with a machine-decidable
accept (R1→S1, R2→S1, R3→S2, R4→S3, R5→S3, R6→S4, R7→S7, R8→S8, R9→S9,
R10→S6, R11→S10); the blast-radius census is pasted from the tool and every
hit classified, with the manual grep supplied for the one `UNKNOWN`; the
frozen-surface forecast is the tool's own verbatim output; the one mechanism
the request names (the exit-documentation check "mutation-proven both ways")
was traced to `docs/map/SUB-evaluation.md:227` and confirmed to be the check
that actually counts `reach_sweep`'s inner-loop branches; measurements M1-M5
back every load-bearing claim; nothing in this spec is untraceable to an R or
C number.
