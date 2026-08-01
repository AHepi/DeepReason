---
name: dr-propose-fix
description: Design the smallest correct DeepReason fix for a reproduced cause, as FIX.md. No code changes yet. Use after REPRO.md confirms the diagnosis.
---

# Propose the fix

Input: DIAGNOSIS.md + REPRO.md. Output: FIX.md. You may read code
freely now, but you still change nothing.

## Design rules (DeepReason-specific)

- **Smallest semantic change that makes the reproduction invert.** If
  a comparison is wrong, fix the comparison — do not redesign the data
  it compares.
- **The record is law.** Never change what is WRITTEN to the
  append-only record to fix what is READ from it. Fix readers
  (validators, gates, accessors) so old committed roots stay valid.
  A fix that invalidates existing replay-valid roots is wrong by
  definition.
- **Frozen surfaces need a flag, not a patch.** Anything that alters
  state digests, event application order, manifest schemas, or
  qualification subjects is out of a normal tranche: FIX.md must say
  so and stop for operator approval.
- **Budgets and priorities are guarantees.** A scheduling or budget
  fix must state the guarantee in one sentence ("the operator's seed
  question always wins rank ties"; "simulation budgets meter only
  simulation records") and the fix must make that sentence true in
  EVERY selection/gate path, not just the default one.
- **Counters count one thing.** When filtering a pooled collection,
  filter by type (`isinstance`) at every consumer, and check for the
  mirror-image bug in the sibling capability before declaring done —
  note it in PARKED.md if real.

## FIX.md template

    # Fix: <one line>
    Guarantee restored: <one sentence>
    Change sites (exhaustive):
      - <file:line-range> — <what changes, one line each>
    Regression artifact: <the REPRO artifact that must invert, plus
      any NEW conditions this fix must be tested against>
    Existing tests at risk: <tests whose fixtures assumed the old
      behavior, from grep — name them and say whether each will be
      updated (fixture was defect-dependent) or must keep passing>
    Explicitly not changed: <the tempting neighbor, and why>
    Estimated diff: <n> lines across <n> files (must be <=150)

## Approval gate

- Class `defect` (per GOAL.md) with diff estimate <=150 lines and no
  frozen surface: proceed to `dr-implement-fix`.
- Anything else: stop, present FIX.md, await operator direction.

## Exit criteria

- FIX.md committed and pushed. No production code changed.
- Return to the orchestrator.
