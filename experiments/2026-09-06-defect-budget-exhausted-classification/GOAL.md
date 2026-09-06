# GOAL — a budget denial on a spent budget must stop the run clean

Tranche opened 2026-09-06. Route: `deepreason-orchestrator` (defect family).
Parked entry: `experiments/2026-09-06-change-writers-room-organiser-testing/
PARKED.md` P8; narrative context in that tranche's RESULTS.md fourth segment
§5.

## Map preflight (resolved before any code was read)

| id | why it is in scope |
|---|---|
| `DR-SEAM-scheduler-x-workflow` | read FIRST: the seam owns how the scheduler's cycle loop absorbs a typed workflow denial; its `Traps` already carry two budget-denial incidents |
| `DR-SUB-scheduler` | owns `scheduler/scheduler.py`, whose `run()` loop decides whether a denial ends the run cleanly |
| `DR-SUB-workflow` | owns `workflow/transaction_service.py`, which raises the typed denial, and `workflow/lifecycle.py`, which owns the resumable-stop sets |
| `DR-SUB-application` | owns `application/text_runs.py`, where the escaping error becomes a published `stop_reason` |
| `DR-SUB-llm` | owns `llm/budget.py`, the meter that decides a reservation is unaffordable |
| `DR-INV-frozen-surfaces` | read before designing: the five surfaces |

**Frozen-surface reading.** None of the five surfaces is touched by the work
this goal describes. `budget_exhausted` is already a member of `StopReason`
(`runtime/stop.py`), already in `RESUMABLE_STOP_REASONS` and already in
`COMPOSABLE_STOP_REASONS` (`workflow/lifecycle.py`), so no stop vocabulary
moves. No record format, digest, manifest schema or qualification subject is
in the design. If the implementation turns out to need one, the tranche STOPS
at FIX.md and prices the roads.

## The defect, in one sentence

A run stopped by the ceiling the operator set is published as a breakage.

## Evidence (typed record only)

Root `experiments/2026-09-06-change-writers-room-organiser-testing/runs/
home-r/runs/run-c3f3bf10bc57d63e224a9f1c68bf1057`, at its **epoch-0 terminal**
— commit `ebdfe976e`, before the continuation of the fifth segment raised the
ceiling and republished the same files:

- `run-status.json`: `state: failed`, `stop_reason: operational_failure`,
  `activity: operational failure`, `message: token budget denied transactional
  work sha256:dcd8fa45…`, `cycle: 3`, `token_spend: 495362`,
  `token_limit: 500000`.
- `run-stop.json`: `reason: operational_failure`, `event_seq: 1166`.
- `log.jsonl` seq 1165: a `work_transition` Control event whose inputs are
  the work id `sha256:dcd8fa45…` and the trigger `budget-denied:token-budget`.
- `runs/armR/ARMR_RESULTS.json`: `violations: 0`, `valid: true`,
  `source: rederived`; the record itself is sound.
- `deepreason stop-report` (recorded in that tranche's §2) rules out
  CONFIGURATION and ENVIRONMENT: 53 critic attempts, 0 faults, no 429, no
  transport fault.

## Success criterion (falsifiable, both sides)

A committed regression test proves BOTH:

1. **Exhausted → clean.** A denial issued when the remaining headroom cannot
   cover another dispatch of the shape that was denied terminates
   `stop_reason: budget_exhausted`, `state: completed` — and that terminal
   leaves relaunch checkpoints: `checkpoint.json` written, a typed STOPPED
   lifecycle receipt, `stop_reason_resumable: true`.
2. **Not exhausted → unchanged.** A denial issued while the budget still has
   headroom for another dispatch of that shape does NOT become a clean stop;
   it stays `operational_failure`.

Both assertions are mutation-proven: reverting the fix must turn each red for
its own reason, and each mutation is captured under `proof/`.

The gate is 0 failed at the boundary. `python tools/docs_verify.py` is 0
failed, with the map moved in the same commit as the code and a `Traps` entry
naming run `run-c3f3bf10bc57d63e224a9f1c68bf1057`.

## Out of scope (park, do not fix)

- P9 (the same three events verify clean before a continuation and violate
  after it) — its own window.
- The organiser seat, the sealed measure, and the disposition of ARM R's unit
  under PREREG §3 — an operator ruling, not a code change.
- The committed root itself: never edited, never relaunched.
- Any widening of what `_arg_crit` absorbs beyond what this goal needs.
