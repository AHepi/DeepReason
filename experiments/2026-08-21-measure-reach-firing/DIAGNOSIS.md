# Diagnosis: reach never fires because the corpus's only two qualifying criteria are FORM gates that an artifact passes if and only if it already carries them

Primary cause: `reach_sweep` requires, of one criterion set, both NOVELTY
(at least one qualifying foreign criterion absent from the artifact's own
battery) and SURVIVAL (every qualifying foreign criterion passes). Across
the 96 in-scope roots the qualifying vocabulary is exactly two criteria —
`relation-form@578e42df713e`, a form gate whose expression is a constant and
whose content-addressed id is therefore a singleton shared by every
connection and integration problem in every run, and `reasoning-envelope-wf`,
a well-formedness program. An artifact satisfies either gate precisely when
it was built carrying it (the connection/integration spawn prompt instructs
the conjecturer to name a relation kind and state a REFUTED IF), so the cell
"does not carry it, yet passes it" — the only cell that can produce a hit —
is empty: 0 of 3 414 artifact observations for `relation-form`, 0 of 3 236
for `reasoning-envelope-wf`. Novelty and survival are jointly unsatisfiable
in this corpus, not by threshold and not by reader, but because no problem in
any in-scope root carries a machine-evaluable criterion about its own
SUBJECT.

Evidence:
  - `census-verdicts.json` (RE-DERIVED, 96 roots): 1 178 430 pairs =
    285 070 `E1 no-criteria` + 308 264 `E3 no-novel` + 585 096
    `E4 criterion-fail`. `E2 non-qualifying` = 0, `E5 coverage` = 0,
    `HIT full` = 0. Every `E4` first non-pass verdict is `fail` — never
    `overrun`, never an evaluator error.
  - `census.json` (RECORDED, straight from `log.jsonl`): 0 Measure events
    carrying `reach_set` or `addr+`, and 0 `reach-provisional` inputs, on
    every one of the 96 in-scope roots. The two roots that ever recorded
    reach (`gemma4_dna_unattended_2026-07-12`: 4 events / 24 pairs;
    `gemma4_dna_unattended_3_2026-07-12`: 2 / 11) are both out of scope —
    the reader refuses them with `UNSUPPORTED_RUN_MANIFEST` — and both
    predate the Bronze Age discipline.
  - `probe_novelty.json`: the carries x passes 2x2 for both qualifying
    criteria. `carries=False passes=True` is 0 in both rows.
  - `probe_content.json`: 3 528 / 3 528 candidate artifacts resolve to
    non-empty content (shortest 402 chars), so the `SUB-evaluation` Traps
    hazard — a missing blob reading as `""` and yielding a confident `fail` —
    is ruled out. 880 artifacts DO satisfy `relation-form`; all 880 already
    carry it.
  - `verify_sweep_equivalence.json`: the real `reach_sweep`, run against
    copies of four roots (including the largest, 12 991 log lines), returns
    `[]` and appends nothing.
  - `census.json` `_gate_coverage`: 487 912 of 585 096 gate pairs (83%) sit
    at coverage 1.00, i.e. above `REACH_COVERAGE_MIN`. Coverage is not the
    binding constraint.

Implicated code (read AFTER the record, and NOT modified):
  - `src/deepreason/measures/reach.py:91-93` — the joint novelty+survival
    requirement, `if not qualifying or not (set(qualifying) - carried)`
    followed by the all-PASS check. Correct as written; it is the criterion
    vocabulary that starves it.
  - `src/deepreason/unification/isolation.py:43-55` —
    `relation_form_commitment()`, a form gate over a CONSTANT expression,
    hence a singleton id shared corpus-wide.
  - `src/deepreason/rules/spawn.py:171,221` — the two sites that attach it as
    a problem criterion.

Falsifiable prediction: a run whose problems carry at least one
subject-substantive machine-evaluable criterion that the candidate
conjecturer is NOT instructed to satisfy will move pairs out of `E4` and
produce non-zero `reach_set` events. Conversely, any change that leaves the
criterion vocabulary as-is — lowering `coverage_min`, widening or narrowing
`_STRUCTURAL_PROGRAMS` — will leave the census at zero, because `E5` and `E2`
already reject nothing.

Ruled out:
  - **"A threshold suppresses hits."** `E5 coverage` rejected 0 pairs; 83% of
    gate pairs already clear 0.5. Lowering `REACH_COVERAGE_MIN` changes
    nothing.
  - **"The structural filter is too aggressive."** `E2 non-qualifying`
    rejected 0 pairs. The filter never fired as a sole cause anywhere.
  - **"The reader cannot resolve artifact bytes on replay."** 100% of
    candidate artifacts resolve to non-empty content.
  - **"The sweep is never called."** It runs every cycle
    (`scheduler.py:2274`), and the real function run on root copies confirms
    the empty result rather than an absent call.
