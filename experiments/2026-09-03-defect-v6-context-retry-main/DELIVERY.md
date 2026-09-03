# DELIVERY — the v6 conjecture-context retry fix, on main

Tranche `experiments/2026-09-03-defect-v6-context-retry-main/`,
2026-09-03. Family: DEFECT. Base: `main` at `5df7246ad`
(= `origin/main`). Branch: `claude/scratchpad-retry-fix-main-lwwks1`.

## What shipped

`Scheduler.step` had two independent expressions producing the
conjecture context plan it dispatches `conj` with, and only the first
carried the v6 rule. The `ConjectureContextStale` retry therefore
handed `conj` exactly what `conj` refuses, and the resulting
`ValueError` — caught by none of the handlers around the dispatch —
terminalized the run. Now there is one owner,
`_dispatch_conjecture_context_plan`, and both sites call it.

## Provenance — where this came from, and what did NOT come with it

The fix ORIGINATES at commit **`06b0d9fd9`** ("fix: v6 conjecture
context retry planned a context v6 refuses, killing the run") on
branch **`claude/model-profile-registry-opkgal`**, where it was
diagnosed, reproduced and mutation-proven. It is independently
confirmed on main by the live record: **F7** in
`experiments/2026-09-02-live-p-a2-corrected/FINDINGS.md:247`, P-A2
epoch 3, run
`63e48f57415d05323b608a84f138ee5c22c274d7d8ebccc2e219b613d7c3a722`.

Taken from `06b0d9fd9`: **two files only.**

| file | how |
|---|---|
| `src/deepreason/scheduler/scheduler.py` | the commit's own hunks, applied with `git apply --3way`, clean |
| `tests/test_scheduler_v6_context_plan_retry.py` | verbatim, sha256 `03c84608a418455df5ea341d5ead01fde65c7c0c8ddfedd6fe00069d37c68858`, identical to the source copy |

Deliberately NOT taken, per the tranche instruction: the commit's
`experiments/` payload (the arm-A run root and its objects and blobs),
anything under `mini/`, and the env-var generator hook in
`rules/conj.py`. Nothing else from that branch is on this one.

## Evidence, criterion by criterion

| GOAL.md criterion | result | where |
|---|---|---|
| 1. test file byte-identical to `06b0d9fd9`'s | PASS | VERIFY.md §1 |
| 2. mutation proof re-run ON MAIN, identical test bytes | PASS — 5 passed / 2 failed 3 passed / 5 passed | REPRO.md §Results, `mutation.log` |
| 3. `pytest tests/ -q -n 4` → 0 failed | **PASS — 4694 passed, 6 skipped, 0 failed** | VERIFY.md §3 |
| 4. `docs_verify` no delta beyond rows this tranche repairs | <!-- DV1 --> | VERIFY.md §4 |

## The map, moved in the same commit

Two committed map checks pinned the PRE-FIX expression by literal text
and would have gone red the moment the fix landed. This was found at
map preflight, before the patch — not after it broke.

| document | what moved | claim changed? |
|---|---|---|
| `SUB-scheduler.md` | new `Traps` entry naming P-A2 run `63e48f5741…` (F7) and episode-config arm A root `run-cd878ff440f61294de34bea1fd45f8ad`, with its own `check:` | no — new |
| `SEAM-scheduler-x-workflow.md` | "Preparation ordering" row, the prose above the check, and the check itself, re-expressed against `_dispatch_conjecture_context_plan` | **no** |
| `SEAM-schools-x-scratch.md` | the check that grepped the literal pre-fix line, re-expressed against the owner's forwarding | **no** |

Neither re-expression is a weakening, and that is proven rather than
asserted: three mutations were run against both checks
(REPRO.md §"The map checks are mutation-proven too"). The
scheduler-x-workflow check goes RED on the defect itself and on
deleting the v6 rule from the owner; the schools-x-scratch check goes
RED when the owner stops forwarding the raw allocated `school_id`,
which is the claim it has always carried. Each is red on its own claim
and green on the other's.

`SEAM-scheduler-x-rules.md` was checked and does NOT name the context
plan handoff — it carries no `conjecture_context_plan`, `context_plan`
or `ConjectureContextStale` reference — so it needed no edit. The
tranche instruction made that conditional and the condition is false.

`Verified-at:` stamps were NOT advanced on the three documents. Only
the claims this tranche touched were re-checked, not each document in
full, and `SCHEMA.md` is explicit that a stale stamp is honest while a
false one is not. The last three tranches to edit `SUB-scheduler.md`
did the same.

## Frozen surfaces

CLEAR. `INV-frozen-surfaces.md` was read before designing. The five
frozen surfaces span `capabilities/state.py`, `harness.py`,
`invariants.py`, `verification/`, `run_manifest.py` and
`qualification.py`, plus the frozen-adjacent `route_fingerprint` in
`llm/firewall.py`. `src/deepreason/scheduler/scheduler.py` is on none
of them, and no file in either of the seven paths was opened for
writing in this tranche.

## Residue — what this delivery does not prove

Stated so no later reader over-reads it:

- No live run. The fix is proven offline and structurally; the live
  evidence it answers to predates it. A v6 ladder that fires the
  scratchpad is the live test and is not owed here.
- The stale-context condition is unchanged. This makes the retry
  survivable, not rarer.
- Only two files crossed from the originating branch. Nothing else on
  `claude/model-profile-registry-opkgal` is asserted sound or unsound
  by this tranche.

## Parked

None. Nothing outside the goal was found that needed parking.
