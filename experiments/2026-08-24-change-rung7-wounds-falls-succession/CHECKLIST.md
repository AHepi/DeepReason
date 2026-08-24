# CHECKLIST — Rung 7: wounds, falls, and succession

Authority: `SPEC.md` (S1-S11, A1-A10), which cites `REQUEST.md` (R1-R9,
G1-G7, C-*). One step per `dr-execute-step` invocation. A step is done
only when its DONE-CRITERION output is pasted under it.

Gate discipline (C-GATE): the RING while iterating, the full gate at each
`[COMMIT]` boundary marked GATE. `python tools/blast_radius.py` and
`python tools/diff_budget.py 053c129ac --ceiling 700 --paths src` run at
every `[COMMIT]`. Map documents move in the SAME commit as their code
(C-MAP).

---

## Step 1 — the frame entry's recognition (S1; R2, G2, G7)

Add to `src/deepreason/calculus/standing.py`: `FallenFrame`,
`fallen_frames`, `unseparated_fallen_frames`, `framed_problem_ids`.
`consulted()`, `StandingGrant`, `frame_assertions` and
`consultability_of` are NOT touched. Export the new names from
`calculus/__init__.py`.

DONE-CRITERION:
`python -c "from deepreason.calculus import fallen_frames, framed_problem_ids, unseparated_fallen_frames; import inspect; from deepreason.calculus.standing import consulted, StandingGrant; assert str(inspect.signature(consulted)) == '(harness)'; print('ok')"`

**DONE 2026-08-24.**

```
DONE-CRITERION step 1: consulted() and StandingGrant unchanged; four new names import
33 passed in 39.08s        # tests/test_calculus_standing.py tests/test_calculus_frame_assertions.py
```

## Step 2 — tests for the frame entry, RED first (S1, S2; G2, G3)

Write `tests/test_calculus_cascade_frame_entry.py`. It must be RED
against step 1's tree (the marking function does not yet read the frame
entry) and green after step 3. Covers: fall marks, revocation marks,
contestation marks NOTHING, an unseparated fallen assertion marks
nothing, a scope that no longer compiles admits nothing, and the
structural assertions for G2 (one marking function) and G3 (no stored
grade, exactly one assigning function).

DONE-CRITERION: the RED run pasted (`python -m pytest
tests/test_calculus_cascade_frame_entry.py -q` — failures naming the
missing frame entry, not import errors).

**DONE 2026-08-24 — RED, as designed.** Four failures, every one naming the
missing frame entry; no import error, no collection error.

```
FAILED tests/test_calculus_cascade_frame_entry.py::test_a_fall_marks_every_problem_the_frame_carried
FAILED tests/test_calculus_cascade_frame_entry.py::test_a_revocation_marks_with_the_weaker_grade
FAILED tests/test_calculus_cascade_frame_entry.py::test_the_frame_entry_is_read_not_reimplemented
FAILED tests/test_calculus_cascade_frame_entry.py::test_the_mark_is_reversible_by_the_same_computed_predicate
4 failed, 9 passed in 3.49s
```

## Step 3 — ONE marking function, both entries (S2; R2, G2, G3)

Rewrite `premises.py::premise_orphaned` as: collect `(problem_id,
status)` pairs from both entries, then ONE grading step. Function-local
import of `deepreason.calculus.standing`. Narrow `DR-SUB-calculus`'s
`premises.py` trap check to the claim it was always about, in this same
commit, with the narrowing's reason written down.

DONE-CRITERION: `python -m pytest
tests/test_calculus_cascade_frame_entry.py tests/test_premise_channel.py
tests/test_premise_channel_loop.py -q` — 0 failed.

**DONE 2026-08-24.** GREEN, and the ring with it.

```
tests/test_calculus_cascade_frame_entry.py ..... 14 passed in 4.01s
tests/test_premise_channel.py tests/test_premise_channel_loop.py
tests/test_calculus_cascade_frame_entry.py ..... 49 passed in 7.45s
ring (premises + standing + frame assertions + render + separation + closure):
129 passed in 44.50s
diff budget: {"areas": {"src": 191}, "ceiling": 700, "verdict": "WITHIN"}
```

**One design point the tests forced, recorded rather than absorbed.** σ can
admit the assertion's OWN promotion problem, because the two are about the same
subject — and marking it would deprioritize in scheduling the one problem D-1
requires to stay on the frontier when a frame falls. The entry excludes exactly
that problem, and `test_a_fallen_frame_does_not_orphan_its_own_promotion_problem`
proves σ admits it, so the exclusion is what does the work rather than the
scope.

Map moved in this commit: `DR-CON-problem-layer-lifecycle` (the second entry,
one marking function, the three conditions), `DR-SUB-calculus` (the NARROWED
`premises.py` trap check, with the narrowing's reason).

## Step 4 — Prop 9.6 end to end, with its mutation proof (S10; G1)

Write `tests/test_calculus_wound_persistence.py`: a wound on the
subject's own observation-valued commitment moves `status(b)` to
`REFUTED`, leaves the grant returned by `standing_of` byte-identical,
leaves the frame rendering, and produces NO cascade mark. Then the
MUTATION: in a scratch copy, make a wound touch standing; run RED;
restore; run GREEN. Both outputs pasted.

DONE-CRITERION: the RED output, the restore, and the GREEN output all
pasted in the step's record.

**DONE 2026-08-24.** Six proofs, then the mutation.

GREEN (shipped tree):

```
tests/test_calculus_wound_persistence.py ......   6 passed in 0.36s
```

MUTATION APPLIED — `standing.py::consultability_of` gains a clause making a
REFUTED subject remove its own standing, which is exactly what Prop 9.6
forbids:

```python
    if harness.state.status.get(body.subject_ref) is Status.REFUTED:
        return Consultability(False, FRAME_NOT_UNREFUTED, (body.subject_ref,))
```

RED:

```
FAILED tests/test_calculus_wound_persistence.py::test_a_wound_changes_status_and_leaves_standing_untouched
FAILED tests/test_calculus_wound_persistence.py::test_the_wound_renders_in_frame_across_the_scope
FAILED tests/test_calculus_wound_persistence.py::test_many_wounds_still_leave_standing_untouched
3 failed, 3 passed in 0.38s
```

RESTORED from the scratch copy — `git diff src/deepreason/calculus/standing.py`
prints nothing — then GREEN again:

```
......                                                                   [100%]
6 passed in 0.36s
```

The mutation kills three of the six: the end-to-end proposition, the in-frame
wound render, and the many-wounds quantitative form. The three it does NOT kill
are the ones a label-only test would have been satisfied by — which is why the
file checks the grant, the render and the cascade as well as the label.

## Step 5 — batch translation offers (S3; R3) `[COMMIT]` GATE

`premises.py::batch_translation_offers`, the
`premise.batch-translation-offered.v1` declaration in `signals.py`, the
scheduler's per-cycle receipt, and
`tests/test_premise_batch_offers.py`. Map: `DR-CON-problem-layer-lifecycle`
and `DR-INV-signal-contract` move in this commit.

DONE-CRITERION: `python -m pytest tests/test_premise_batch_offers.py
tests/test_signals.py -q` — 0 failed — plus the blast-radius and
diff-budget JSON for the commit.

**DONE 2026-08-24.**

```
tests/test_premise_batch_offers.py ...........        11 passed in 0.51s
tests/test_signal_contract.py tests/test_signals.py   19 passed in 3.66s
blast radius: {"frozen_surface_verdict": "CLEAR"}
diff budget:  {"areas": {"src": 300}, "ceiling": 700, "verdict": "WITHIN"}
```

**One near miss, recorded rather than absorbed.** The first `orphan_causes`
compared GRADE STRINGS to decide which cause explains a mark — a second place
where a grade was being decided, which
`test_there_is_no_second_marking_mechanism` caught in the same session. It now
expresses precedence on the LABEL, exactly as the marking function does, and
READS the grade from the mark, so the two cannot disagree.

Map moved in this commit: `DR-CON-problem-layer-lifecycle` (batch offers, the
sixth signal, the new entry points). `DR-INV-signal-contract` needed NO change —
it pins no signal count — and `DR-REC-add-signal`'s own gate
(`tests/test_signal_contract.py tests/test_signals.py`) is green, which is that
recipe's step 4.

## Step 6 — N3 at scale (S10; G4)

`tests/test_cascade_n3_at_scale.py`: ONE fall over a thousand problems;
the cascade marks them; a sample retires, another translates, another is
found independent; NOT ONE resolution asserts insolubility; attacking a
retirement returns its problem to the frontier. The laziness claim is
measured, not asserted: marking a thousand problems costs one derivation.

DONE-CRITERION: `python -m pytest tests/test_cascade_n3_at_scale.py -q`
— 0 failed, with the recorded wall time.

**DONE 2026-08-24.**

```
tests/test_cascade_n3_at_scale.py .......   7 passed in 11.15s
under the gate's own parallelism:           7 passed in 12.23s   (-n 4)
```

**Restructured mid-step for a real defect, not a style preference.** The first
version had tests that depended on earlier tests' mutations of a module-scoped
fixture. That passes serially and FAILS under `-n 4`, which scatters tests
across workers by default — the gate's own configuration. The fixture now
builds the final state and every test is a pure read, so the file is
order-independent by construction. Verified under `-n 4` above, not assumed.

## Step 7 — succession detection and the render exception (S4; R4)

`src/deepreason/calculus/succession.py` (detection, criteria,
`render_succession_context`) and the ONE suppression site in
`calculus/render.py::frame_slices`. `tests/test_calculus_succession.py`.

DONE-CRITERION: `python -m pytest tests/test_calculus_succession.py
tests/test_frame_render.py -q` — 0 failed.


**DONE 2026-08-24.**

```
tests/test_calculus_succession.py ..............   14 passed in 0.83s
ring (succession + frame render + standing + H1 + promotion closure/succession):
88 passed in 41.59s
```

**One fixture point the tests forced.** The narrow tides scope does NOT admit
the discrimination problem, so a suppression test written against it would have
looked green while the frame was merely out of scope. The rivalry fixture uses
a scope that DOES admit it, and the test asserts admission first — the
suppression is what does the work, not the scope.

## Step 8 — the trial's two roads and its record (S5, S6; R6-R9, G5)

The two GENERIC keywords on `informal/trial.py::pairwise_discriminate`
(`presentation`, `observer`); `program_road`, `run_succession_trial` and
the record in `calculus/succession.py`; the scheduler's succession branch.
`tests/test_calculus_succession_trial.py`, including the CONSTRUCTED
order-disagreement case.

DONE-CRITERION: `python -m pytest tests/test_calculus_succession_trial.py
tests/test_trial.py tests/test_scheduler*.py -q` — 0 failed.


**DONE 2026-08-24.**

```
tests/test_calculus_succession_trial.py ...................   19 passed in 0.84s
ring (succession trial + succession + trial + authority policy + scheduler +
frame render):                                               111 passed in 6.57s
tests/test_signals.py tests/test_signal_contract.py           19 passed in 3.73s
```

**The gate caught an undeclared signal, and that is the mechanism working.**
`succession.trial-flip-rate.v1` was emitted before it was declared;
`test_every_emitted_signal_is_registered` AST-scans the source tree and failed
on it. Declared through the typed channel per `DR-REC-add-signal` — name, unit,
producer-agnostic semantics, staleness bound — never by teaching a consumer
about succession.

`informal/trial.py` gained exactly two GENERIC keywords, `presentation` and
`observer`. Neither names succession and the module imports nothing from
`calculus`, so no new package edge exists and there is still ONE pairwise
instrument.

## Step 9 — anomaly conservation, proved (S7; R5) `[COMMIT]` GATE

`tests/test_calculus_anomaly_conservation.py`, all four limbs. Map:
`DR-SUB-calculus`, `DR-CON-standing-and-background` and
`DR-SEAM-calculus-x-rules` move in this commit.

DONE-CRITERION: `python -m pytest
tests/test_calculus_anomaly_conservation.py -q` — 0 failed — plus the
blast-radius and diff-budget JSON.


**DONE 2026-08-24.**

```
tests/test_calculus_anomaly_conservation.py ........   8 passed in 0.27s
ring (succession, trial, promotion, scheduler, signals, frame render):
145 passed in 11.11s
diff budget: {"areas": {"src": 893}, "ceiling": 700, "verdict": "EXCEEDED"}
```

**The diff budget EXCEEDED at this checkpoint — the workflow's own stop
condition.** 893 src insertions against the ledgered 700, with roughly 1000
projected at completion. Put to the operator with priced roads; the answer and
its disposition are ledgered as REQUEST.md Amendment 1.

Map moved in this commit: `DR-SUB-calculus` (succession, the render exception,
anomaly conservation, `Owns:` gains `succession.py`),
`DR-SEAM-calculus-x-rules` (the exception rides the seam without widening it,
plus its own trap row), `DR-CON-standing-and-background` (Prop 9.6 proved, the
second cascade entry).

## Step 10 — the promotion problem's wound-count rank (S8; C-D1)

`calculus/nomination.py::promotion_wound_counts`, one term in
`Scheduler._select_problem`'s `rank` AFTER the SEED term, and the same
term in the non-liveness pool sort. `tests/test_scheduler_promotion_rank.py`,
including the assertion that the operator's seed still wins every tie.

DONE-CRITERION: `python -m pytest tests/test_scheduler_promotion_rank.py
tests/test_scheduler*.py -q` — 0 failed.

## Step 11 — `cascade-integrity` in `verify_root` (S9; the §1 grant)

The three limbs at the END of `verify_root`, the name in
`_EPISTEMIC_CHECKS`, `tests/test_cascade_integrity.py`, and the
committed-root probe proving the check is additive. Map:
`DR-INV-frozen-surfaces` and `DR-SUB-verification` move in this commit.

DONE-CRITERION: `python -m pytest tests/test_cascade_integrity.py -q` —
0 failed — plus the committed-root probe output and the insertions/
deletions count for `invariants.py`.

## Step 12 — the axiom ledger (S10; G7)

`tests/test_calculus_axioms_rung7.py`: A6 preserved at the frame entry,
A9 preserved (the succession render and the trial record move no label),
and NO standing-layer spawn trigger exists (C-D1's absence). Map:
`DR-INV-axiom-basis` and `DR-CON-scheduler-ranking` move in this commit.

DONE-CRITERION: `python -m pytest tests/test_calculus_axioms_rung7.py -q`
— 0 failed.

## Step 13 — boundary gate `[COMMIT]` GATE

Full gate, `docs_verify` FULL, both wheel smokes (C-PUBLIC: prove no
re-pin is owed), blast radius, diff budget against the 700 ceiling.

DONE-CRITERION: `python -m pytest tests/ -q -n 4` (0 real failures),
`python tools/docs_verify.py` (no NEW failures against the base's three),
`python scripts/wheel_smoke.py`, `python -u
scripts/wheel_operational_smoke.py`, and both tool JSONs — all pasted.

## Step 14 — the cycle soak, before any live launch (S11; G6)

`python -u scripts/cycle_soak.py --case epoch3`. The launch config is the
epoch3 shape and is already in the case table, so no case is added.

DONE-CRITERION: exit 0, with the soak's own summary pasted.

## Step 15 — the live gate (S11; G6)

ONLY after step 14 is green: ask the operator for the `OLLAMA_API_KEY`
env file, launch detached, stage a fall on the resulting live root, and
judge on TYPED OUTCOMES ONLY — the mark appears with its grade, the
cascade fires, `verify_root` is clean.

DONE-CRITERION: the run id, the typed mark with its grade, the cascade's
own output, and `verify_root`'s verdict — all pasted.

## Step 16 — RESULTS.md and the §13 residue (G7)

The tranche's RESULTS.md segment, carrying §13's residue VERBATIM and the
honest ledger of what remains unproven.

DONE-CRITERION: the residue quoted verbatim, checked character for
character against `docs/COMPUTABLE_CALCULUS.md`.
