# Parked

One line each. Noticed while capturing this request, not part of it.

- `authority.py` `trial_authority_for` computes `mode = text_authority_mode(...)`
  and discards it — the same compute-then-throw-away shape as the detector in
  `invariants.py:4040-4048`. Worth a sweep for other instances.
- **An operator decision, surfaced at step 8, deliberately not taken here.**
  SPEC.md's A1 read R4's "formal claims" as `programs.evaluable`. The line the
  code actually enforces is `execution_backed` (`rules/warrants.py:24`), which
  is narrower: only EXEC-oracle commitments (exec / property / dataset_oracle)
  that all currently pass. A `predicate:` commitment is `evaluable` but NOT
  execution-backed, so a target carrying only predicates is open to prose
  refutation. Whether R4 means to protect those too is the operator's call;
  widening the guard would change what every existing run may do, so it is not
  done under an assumption. Asserted as-is in
  `test_the_formal_boundary_is_execution_backing_and_not_evaluability`.
- **`ARGUMENTATIVE_AUTHORITY=single_family_trial` is now dead weight.** Added
  at steps 10-11 as the switch for the single-family path. Step 21 made the
  substitute guarantee cross-school CRITICISM, and step 26 measured the
  consequence: the Config direct-helper path passes no `critic_school_id`, a
  school can only arrive through the v4 envelope, and that envelope demands a
  manifest-bound authority value — so this value can never complete a trial.
  R20 ("exposed whenever a single model is occupying all positions") also makes
  it redundant in principle: route topology decides, so an authority value for
  the same thing is a knob for something that should not have one. Removing it
  reverts part of two committed steps and touches `authority.py`, `config.py`
  and `crit.py`; it is a decision about the Config surface, not a fix, so it is
  recorded rather than taken.
- **The 11.6%.** Widening the formal line makes 148 of 1279 recorded artifacts
  immune to prose refutation (100.0% -> 88.4% refutable); one root goes from 79
  refutable to 31. Measured at step 18. This is the price of "they are both
  formal" and whether it is the intended price is the operator's call.
- **The cross-school JUDGE gate is superseded but retained (A10).**
  `require_cross_school_judge_ensemble` and `school_judge_bindings` are no
  longer the mechanism — step 21 moved the guarantee to criticism. They stay
  because they are correct for a manifest that authors judge bindings, which
  `run_manifest.py:2751` does not currently permit. Deleting tested, working
  code was not asked for.
- **The cross-school gate is unwired for live runs.** `llm/adapter.py:1467` is
  the only production `LLMAdapter` construction and it passes no
  `school_judge_bindings`, so `_select_judge_ensemble` always falls back to
  cross-family in a real run. The architecture is complete and proven offline
  (step 12); it is not reachable from a ladder. Natural source:
  `run_manifest.criticism_policy.bindings` filtered to `role == "judge"`.
  Not done here — nothing in R7-R17 or S7-S12 asks for it, and it would change
  gate selection for every v6 run that carries judge bindings.
  **SUPERSEDED by step 21**: the substitute no longer needs bindings at all, so
  the wiring gap this recorded is no longer on the path R20 asks for. Kept for
  the history of the decision.
- **`render_batch_crit_pack` still prefix-clips its targets**
  (`llm/packs.py:594`, `content_text(target, blobs)[:content_chars]`) — the
  exact "ends abruptly" truncation `_document_excerpt` was written to avoid,
  and now the only crit path where R3 is unmet. S3 names `render_crit_pack`
  alone, so the batch path is left as it is rather than widened under this
  tranche. Related: after step 9, `_document_excerpt` has no caller anywhere;
  it is deliberately kept rather than deleted, because it is the right tool for
  this path if the operator wants R3 extended to it.
- Everything already parked in
  `experiments/2026-08-01-fix-adjudication-blindness/PARKED.md`, which carries
  the nine items from the jolt investigation plus the discarded detection flags.
