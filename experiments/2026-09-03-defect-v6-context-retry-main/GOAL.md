# GOAL — bring the v6 conjecture-context retry fix (F7) to main

Tranche opened 2026-09-03. Family: DEFECT (`deepreason-orchestrator`).
Base: `main` at `5df7246ad` ("cycle_soak.py: repair the P-A1 merge
resolution"), which is `origin/main`.

## The defect, in one sentence

On a v6 run, the `ConjectureContextStale` retry inside
`Scheduler.step` re-planned a conjecture context that `rules/conj.py`
refuses on v6, so the retry raised an uncaught `ValueError` and
terminalized the run.

## Why this tranche exists

The defect is ALREADY diagnosed, reproduced and fixed — on branch
`claude/model-profile-registry-opkgal`, commit `06b0d9fd9`
("fix: v6 conjecture context retry planned a context v6 refuses,
killing the run"). It is independently confirmed on main by the live
record: `experiments/2026-09-02-live-p-a2-corrected/FINDINGS.md` F7,
P-A2 epoch 3, run `63e48f57415d05323b608a84f138ee5c22c274d7d8ebccc2e219b613d7c3a722`.

Main does not carry the fix. This tranche transplants it and nothing
else.

## The one goal

Main carries the `06b0d9fd9` fix to
`src/deepreason/scheduler/scheduler.py` and its regression tests, with
the mutation proof re-run ON MAIN, the map moved in the same commit,
and the full gate at 0 failed.

## Success criterion (falsifiable)

1. `tests/test_scheduler_v6_context_plan_retry.py` exists on this
   branch with bytes identical to `06b0d9fd9`'s copy.
2. Mutation proof on main: with the pre-fix retry line restored, that
   file is RED; with the fix in place, it is GREEN; the test file's
   bytes are identical in both halves (sha256 recorded in REPRO.md).
3. `python -m pytest tests/ -q -n 4` → 0 failed.
4. `python tools/docs_verify.py` shows no delta from the recorded
   baseline set beyond rows this tranche itself repairs.

## Scope — what is IN

- `src/deepreason/scheduler/scheduler.py`: the
  `_dispatch_conjecture_context_plan` owner and its two call sites.
- `tests/test_scheduler_v6_context_plan_retry.py`, verbatim.
- The map, in the same commit: a `SUB-scheduler.md` Traps entry, and
  the two map checks that pin the OLD expression by text and would
  otherwise go red (found at preflight, see DIAGNOSIS.md §Map).

## Scope — what is OUT (explicitly)

Nothing from `06b0d9fd9` outside those two files: no `experiments/`
payload (the arm-A run root and its objects), no `mini/`, and NOT the
env-var generator hook in `rules/conj.py`. Nothing else from branch
`claude/model-profile-registry-opkgal`.

## Map preflight (ids resolved before any code was read)

- `DR-SUB-scheduler` — owns `src/deepreason/scheduler/`.
- `DR-SEAM-scheduler-x-rules` — the side the refusal is raised on
  (`rules/conj.py`).
- `DR-SEAM-scheduler-x-workflow` — carries the "Preparation ordering"
  row and the check that pins `context_plan = None` under v6.
- `DR-SEAM-schools-x-scratch` — carries a check that pins the literal
  pre-fix line `context_plan = self._plan_conjecture_context(...)`.
- `DR-INV-frozen-surfaces` — read before designing. The five frozen
  surfaces span `capabilities/state.py`, `harness.py`, `invariants.py`,
  `verification/`, `run_manifest.py`, `qualification.py`, plus the
  frozen-adjacent `route_fingerprint` in `llm/firewall.py`.
  `scheduler/scheduler.py` is on NONE of them. If the work reaches one,
  STOP.

## Stop conditions

- Any frozen surface is touched → stop and report.
- The mutation proof does not go RED on main → stop; the defect is not
  the one diagnosed on the originating branch and the diagnosis must be
  redone here.
- Gate failures beyond the recorded baselines → stop.
