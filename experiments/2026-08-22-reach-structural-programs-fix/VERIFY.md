# Verification

**Criterion:** the one named by the tranche brief — re-run the committed
rehearsal (`experiments/2026-08-22-live-reach-rich-run/rehearsal.py`) after
the real fix and WITHOUT its in-process rebind. S8a must become a HIT and
agree with S8b; S8c must stay E4.

## 1. The decisive regression — the rehearsal re-run, no rebind anywhere

`rehearsal.py`'s `wf_structural` parameter and its two call sites are deleted
(commit `84656d02c`), so all ten scenarios run against the shipped
`_STRUCTURAL_PROGRAMS`. Before/after over the same script, the "before" column
read from `rehearsal-as-shipped.json` (the pre-fix file preserved verbatim in
this tranche, and in git at `29b0d9638`):

    sc    before                 after                  events b/a  coverage b -> a
    S1    E3 no-novel            E3 no-novel            0/0         1.0   -> 0.5
    S2    E4 criterion-fail      HIT full               0/1         1.0   -> 0.5
    S3    HIT full               HIT full               1/1         1.0   -> 0.5
    S4    E4 criterion-fail      E4 criterion-fail      0/0         1.0   -> 0.5
    S5    E4 criterion-fail      E4 criterion-fail      0/0         1.0   -> 1.0
    S6    E4 criterion-fail      E4 criterion-fail      0/0         0.333 -> 0.333
    S7    E1 no-criteria         E1 no-criteria         0/0         None  -> None
    S8a   E4 criterion-fail      HIT full               0/1         1.0   -> 0.667
    S8b   HIT full               HIT full               1/1         0.667 -> 0.667
    S8c   E4 criterion-fail      E4 criterion-fail      0/0         0.667 -> 0.667

    S8a == S8b on every recorded field but scenario/note: True

**S8a: `E4 criterion-fail` / 0 events -> `HIT full` / 1 event**, at coverage
0.667, qualifying on exactly the two subject predicates. **It is now identical
to S8b field for field**, which is the whole point: S8b was previously
obtainable only by rebinding the module constant in-process, and S8a is what
the shipped code does. **S8c stays `E4 criterion-fail` / 0 events** — the
off-SUBJECT control holds, so the fix grounds reach on subject, not on form.

Coverage moves on S1–S4 without any exit moving: those foreign problems
carried `reasoning-envelope-wf`, which has left the qualifying numerator while
staying in the criteria denominator. No verdict depends on it.

**One movement the prediction did not name, reported not folded in.** S2 also
went `E4 -> HIT full`. Same mechanism (a novel, passing subject predicate),
but it is the only pair in this corpus that exercises an artifact with an
EMPTY own battery, and its coverage lands exactly ON `REACH_COVERAGE_MIN`
(0.500, and `reach_sweep` compares with `<`). Neither boundary has ever been
reached before — the 08-21 census puts `E5 coverage` at 0 of 1 178 430 pairs.
Parked as **P5-reach** for a deliberate ruling rather than treated as
confirmation.

## 2. GOAL.md's success criteria, verbatim

    $ python -c "from deepreason.programs import programs_by_class; from deepreason.measures.reach import _STRUCTURAL_PROGRAMS as S; d=set(programs_by_class()['structural']); raise SystemExit(0 if d == set(S) else 1)"
    $ echo $?
    0                                        # was 1 before the fix

    $ python experiments/.../repro.py
    HOLDS  R1 declared structural class == reach's structural set
               declared_minus_reach = []      reach_minus_declared = []
    HOLDS  R2 a declared-structural gate never enters reach's qualifying set,
               so it can neither ground nor veto a hit
               qualifying = ['uhi-energy-balance@r1', 'uhi-nocturnal-release@r1']
               wf_in_qualifying = False       coverage = 0.667
               hits = [[6b7747a9..., 'foreign']]   recorded_reach_events = 1
    HOLDS  R3 a passing declared-structural gate confers no formally_backed
               prose immunity
               wf_verdict = pass              formally_backed = False
    EXIT=0                                    # all three VIOLATED before (REPRO.md)

## 3. Targeted regressions, mutation-proved

Three new tests, all asserted over `programs_by_class()` rather than over a
fixed list of names, so registering a new structural program cannot break
them:

    tests/test_reflexive_discipline.py::test_declared_structural_programs_are_never_substantive
    tests/test_reflexive_discipline.py::test_a_well_formedness_gate_cannot_veto_a_reach_hit
    tests/test_prose_refutation_boundaries.py::test_a_declared_structural_program_confers_no_formal_backing

Mutation proof — the pre-fix hand list restored in a SCRATCH copy of
`reach.py` (`src/` restored immediately after; `git diff --stat` confirmed
clean):

    ===== MUTATION (pre-fix hand list restored) =====
    FAILED tests/test_reflexive_discipline.py::test_declared_structural_programs_are_never_substantive
    FAILED tests/test_reflexive_discipline.py::test_a_well_formedness_gate_cannot_veto_a_reach_hit
    FAILED tests/test_prose_refutation_boundaries.py::test_a_declared_structural_program_confers_no_formal_backing
    3 failed in 0.28s

    ===== RESTORED =====
    3 passed in 2.43s

The P3 documentation check is mutation-proved both ways as well: dropping the
`E1 no-criteria` label from the docstring fails it (rc=1), and adding a sixth
undocumented exit to `reach_sweep`'s inner loop fails it (rc=1); restoring
passes (rc=0).

## 4. Committed roots: nothing moved

The root sweep is RETIRED (CLAUDE.md, operator ruling 2026-08-22) and was not
run. The consequence measurement that replaces it is targeted:
`immunity_delta.py`, which imports the 08-21 tranche's `probe_immunity.probe`
verbatim rather than copying it, over every root carrying a `log.jsonl`.

    roots compared                            107
    roots with open_error                     11   (identical before and after)
    roots whose formally_backed count MOVED   0
    totals before  {'candidates': 3528, 'formally_backed': 903}
    totals after   {'candidates': 3528, 'formally_backed': 903}

Compared PER ROOT, not only in aggregate, so an offsetting pair of moves could
not hide. The eleven `open_error` roots are old-version roots the current
reader refuses; they fail identically in both runs, so none is masked by the
change.

## 5. Gates

    python -m pytest tests/ -q -n 4        3818 passed, 6 skipped, 0 failed (18:07)
    python tools/docs_verify.py            3 failed — all three the pre-existing
                                           CON-run-identity.md shallow-clone checks
                                           (git objects absent in this clone),
                                           unchanged from the pre-tranche baseline
    python tools/docs_verify.py --audit    0 findings
    python tools/docs_verify.py --links    0 dangling references, 61 documents
    python scripts/wheel_smoke.py          passed: isolated V6-only contents, clean imports, exact
                                           entry points, module parity, MCP registration,
                                           and exact MCP schemas
    python -u scripts/wheel_operational_smoke.py   launched, still running at 22 min
                                           when the tranche closed — see the note below

The wheel smokes pin the public surface (console entry points, MCP tool set +
schema sha, wheel layout). This tranche changes no entry point, no CLI
command, no MCP tool and no wheel layout — the `programs.py` edit is two
docstrings — so no pin needed updating and no smoke was OWED (CLAUDE.md
requires re-running them only in a commit that changes that surface). They
were run anyway rather than assumed:

  - `wheel_smoke.py` — the one that actually checks the pins — **passed**,
    reporting "isolated V6-only contents, clean imports, exact entry points,
    module parity, MCP registration, and exact MCP schemas". That is the
    evidence that the surface did not move.
  - `wheel_operational_smoke.py` — build-and-operate over a freshly installed
    wheel — was launched and was still running after 22 minutes in this
    container (it builds and pip-installs into a clean environment, and the
    fastembed dependency makes that slow here). It was left running rather
    than killed, and its result is NOT claimed. Recorded as residue, not as a
    pass: nothing in this tranche can change what it exercises, but this
    tranche did not observe it finish.

Diff-budget gate: `EXCEEDED` — 265 insertions against the 150 ceiling GOAL.md
set. Recorded in full, with the breakdown and three priced options, in FIX.md
Amendment 2, and surfaced to the operator rather than buried. Production code
is 42 of the 265; the remaining 223 are the mandated regressions (160) and the
three `Traps` rewrites (63).

## Verdict: **PASS (offline)**

Every success criterion GOAL.md named is met, the decisive regression the
brief named inverted, and the control held. No live run was attempted and none
was required: this defect is a set-membership error whose consequence is fully
determined offline.

## Residue (honest)

- **Offline only.** No provider call was made. The regressions prove the
  mechanism is CORRECT; they do not show how often a real `glm-5.2`
  connection candidate would survive a seed problem's subject predicates.
  That frequency is what the frozen reach-rich run measures and it stays
  unknown. `PREREG.md` §4's PRECONDITION-BLOCKED outcome is discharged — the
  precondition is cleared, the hypothesis is not tested.
- **The rehearsal's candidate is hand-written.** Its prose is a stand-in for
  what the model would produce, so S8a proves the pair CAN survive, not that
  one will.
- **P5-reach is a live open question, not a closed one.** S2's hit rests on
  two boundaries no committed root has ever exercised.
- **P2 is untouched and is now the last hole of its kind.** With the
  program-class exclusion complete, a form gate spelled `predicate:` is the
  only remaining route by which a shape check can ground reach. S5 shows an
  integration problem whose entire qualifying battery is one.
- **Rung 5 needs more than this.** Nomination counts reach across DISTINCT
  problem lineages, and P4-reach (the live-reach tranche's own parked finding)
  says a text run cannot currently seed a second problem with different
  criteria. This fix removes the blocker on producing a reach event at all; it
  does not make nomination reachable.
- **`ProgramSpec.class_` now has teeth in two places.** Declaring a program
  `structural` silently narrows what can ground reach and what confers prose
  immunity. The direction is safe — both consumers only withhold — but it is a
  real change in what registering a program means, recorded in the
  `ProgramSpec` docstring and `SUB-evaluation.md` Traps rather than left
  implicit.
- **`wheel_operational_smoke.py` was not observed to finish.** It was
  launched and left running; no gate owes it and this tranche changes nothing
  it exercises, but its result is unclaimed rather than assumed green.
- **Accepted does not mean true.** Nothing here shows that any artifact
  genuinely explains a foreign problem — only that a well-formedness check is
  no longer what decides.

## Errata

`docs/ERRATA.md` **E41** — added in the same push. A map `Traps` entry named
one consumer of a shared predicate that had two, and its recorded residue
("not an observed live failure") was right about `formally_backed` and wrong
about `reach_sweep`, where the same misclassification was blocking every text
run. A permissive-looking error had a restrictive effect because one predicate
gates two directions.

---

**What a text run's reach sweep can now do that it could not before:** it can
record a reach event at all — an accepted artifact that survives another
problem's subject criteria is now measured on those criteria, instead of being
rejected first by that problem's own well-formedness gate.
