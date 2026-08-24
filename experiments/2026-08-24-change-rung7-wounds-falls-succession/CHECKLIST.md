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

## Step 3 — ONE marking function, both entries (S2; R2, G2, G3)

Rewrite `premises.py::premise_orphaned` as: collect `(problem_id,
status)` pairs from both entries, then ONE grading step. Function-local
import of `deepreason.calculus.standing`. Narrow `DR-SUB-calculus`'s
`premises.py` trap check to the claim it was always about, in this same
commit, with the narrowing's reason written down.

DONE-CRITERION: `python -m pytest
tests/test_calculus_cascade_frame_entry.py tests/test_premise_channel.py
tests/test_premise_channel_loop.py -q` — 0 failed.

## Step 4 — Prop 9.6 end to end, with its mutation proof (S10; G1)

Write `tests/test_calculus_wound_persistence.py`: a wound on the
subject's own observation-valued commitment moves `status(b)` to
`REFUTED`, leaves the grant returned by `standing_of` byte-identical,
leaves the frame rendering, and produces NO cascade mark. Then the
MUTATION: in a scratch copy, make a wound touch standing; run RED;
restore; run GREEN. Both outputs pasted.

DONE-CRITERION: the RED output, the restore, and the GREEN output all
pasted in the step's record.

## Step 5 — batch translation offers (S3; R3) `[COMMIT]` GATE

`premises.py::batch_translation_offers`, the
`premise.batch-translation-offered.v1` declaration in `signals.py`, the
scheduler's per-cycle receipt, and
`tests/test_premise_batch_offers.py`. Map: `DR-CON-problem-layer-lifecycle`
and `DR-INV-signal-contract` move in this commit.

DONE-CRITERION: `python -m pytest tests/test_premise_batch_offers.py
tests/test_signals.py -q` — 0 failed — plus the blast-radius and
diff-budget JSON for the commit.

## Step 6 — N3 at scale (S10; G4)

`tests/test_cascade_n3_at_scale.py`: ONE fall over a thousand problems;
the cascade marks them; a sample retires, another translates, another is
found independent; NOT ONE resolution asserts insolubility; attacking a
retirement returns its problem to the frontier. The laziness claim is
measured, not asserted: marking a thousand problems costs one derivation.

DONE-CRITERION: `python -m pytest tests/test_cascade_n3_at_scale.py -q`
— 0 failed, with the recorded wall time.

## Step 7 — succession detection and the render exception (S4; R4)

`src/deepreason/calculus/succession.py` (detection, criteria,
`render_succession_context`) and the ONE suppression site in
`calculus/render.py::frame_slices`. `tests/test_calculus_succession.py`.

DONE-CRITERION: `python -m pytest tests/test_calculus_succession.py
tests/test_frame_render.py -q` — 0 failed.

## Step 8 — the trial's two roads and its record (S5, S6; R6-R9, G5)

The two GENERIC keywords on `informal/trial.py::pairwise_discriminate`
(`presentation`, `observer`); `program_road`, `run_succession_trial` and
the record in `calculus/succession.py`; the scheduler's succession branch.
`tests/test_calculus_succession_trial.py`, including the CONSTRUCTED
order-disagreement case.

DONE-CRITERION: `python -m pytest tests/test_calculus_succession_trial.py
tests/test_trial.py tests/test_scheduler*.py -q` — 0 failed.

## Step 9 — anomaly conservation, proved (S7; R5) `[COMMIT]` GATE

`tests/test_calculus_anomaly_conservation.py`, all four limbs. Map:
`DR-SUB-calculus`, `DR-CON-standing-and-background` and
`DR-SEAM-calculus-x-rules` move in this commit.

DONE-CRITERION: `python -m pytest
tests/test_calculus_anomaly_conservation.py -q` — 0 failed — plus the
blast-radius and diff-budget JSON.

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
