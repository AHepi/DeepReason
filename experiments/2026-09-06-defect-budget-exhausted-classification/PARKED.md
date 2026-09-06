# PARKED — noticed in this tranche, deliberately not fixed here

## P1 — a budget denial the ceiling could still afford kills the run instead of dropping one batch

**What.** `scheduler.py::_arg_crit`'s direct batch road (the one a run with a
null `criticism_policy` takes) catches only `(SchemaRepairError,
EndpointError)` around `crit_argumentative_batch`. Its foreign-criticism
sibling `_foreign_arg_crit` catches `WorkBudgetDenied` as well and records a
typed `budget_denied` coverage outcome. So a denial on the direct road leaves
the criticism pass entirely. This tranche made that harmless when the ceiling
is SPENT — the cycle loop now ends the run clean — but a denial the ceiling
could still have afforded (one oversized batch prompt) still ends the run as
an operational failure where dropping that one batch and carrying on would
have been the better answer.

Not fixed here because the goal is the CLASSIFICATION of a stop, and widening
what the criticism road absorbs changes what a run DOES. It also needs a
decision this tranche has no evidence for: whether a dropped batch should
record a typed coverage debt the way the foreign road does.

Evidence: `src/deepreason/scheduler/scheduler.py::_arg_crit` (the `except
(SchemaRepairError, EndpointError)` around `crit_argumentative_batch`) against
`_foreign_arg_crit`'s own arm; run
`run-c3f3bf10bc57d63e224a9f1c68bf1057` took the direct road (102 `criticism:`
triggers, 0 `foreign-criticism:` triggers in its `log.jsonl`).

```
EXECUTOR WINDOW — DEFECT: one oversized criticism batch ends the whole run
Read CLAUDE.md. Load deepreason-orchestrator and pinker-write-for-readers.
GOAL: a token-budget denial that the ceiling could still have afforded drops
the criticism batch it was for and lets the cycle continue, instead of ending
the run. Diagnose from the record first: `_arg_crit`'s direct batch road
catches only (SchemaRepairError, EndpointError) while `_foreign_arg_crit`
catches WorkBudgetDenied and records a typed `budget_denied` coverage outcome
-- decide whether the direct road owes the same typed debt, and say what the
record must show either way. A denial on a SPENT ceiling must keep ending the
run cleanly as `budget_exhausted`
(experiments/2026-09-06-defect-budget-exhausted-classification/), so the fix
turns on the same `budget_exhausted` verdict the meter already stamps.
Regression tests for both sides, mutation-proven. OUT OF SCOPE: the stop
classification itself, and anything under experiments/.
```
