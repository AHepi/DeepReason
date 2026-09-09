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

## P2 — three organiser tests fail on `main`, and two instruments report them

**What.** `tests/test_organiser_seat.py` fails three tests on `origin/main` in
a clean worktree — `test_the_fixture_is_the_committed_attachment_byte_for_byte`
(a pinned fixture digest no longer matches) and two block-count mismatches
(`test_admission_mints_one_block_per_room_record`,
`test_the_organiser_brief_shows_the_whole_room_and_the_directive`: 4 vs 7, 11
vs 12, 17 vs 13 blocks). The full gate reports them (3 failed, 5153 passed)
and `docs_verify` reports them a second time through
`INV-seat-section-plugins.md:179`, which runs that file.

A second, separate row from the same tranche:
`INV-frozen-surfaces.md:1241` runs `tools/record_claims.py` against run root
`run-36d9a22c3e2045ae1b8c7bfb9d95d092`, which is not committed —
`no run-status.json (not a run root)`, on `origin/main` too.

**Why it matters beyond tidiness.** `docs/AUDIT_BASELINES.md`'s docs_verify
entry lists six expected failures and these two are not among them, so the
next audit reads a delta of +2 and has to re-derive from scratch what this
window already measured. And the gate is the tranche boundary instrument: at
3 failed, nobody after this can tell a new failure from an old one without
repeating the worktree comparison.

Not fixed here: the organiser is explicitly out of this window's scope, and
the fixture question (is the pinned digest stale, or did the attachment
change?) is that tranche's to answer.

```
EXECUTOR WINDOW — DEFECT: three organiser tests fail on main, twice reported
Read CLAUDE.md. Load deepreason-orchestrator and pinker-write-for-readers.
GOAL: `pytest tests/ -q -n 4` returns 0 failed, and `docs/AUDIT_BASELINES.md`
describes the docs_verify failure list that a fresh container actually sees.
Diagnose from the record first: `tests/test_organiser_seat.py` fails 3 of 12
on origin/main (one pinned fixture digest, two block counts -- 4 vs 7, 11 vs
12, 17 vs 13), and decide from the committed attachment whether the PIN or the
FIXTURE is what moved; never re-pin a digest to make a test pass without
saying which side changed and why. Second, separate finding in the same brief:
INV-frozen-surfaces.md:1241 reads run root
run-36d9a22c3e2045ae1b8c7bfb9d95d092, which is not committed -- decide whether
the root should be committed or the check should name one that exists. Both
belong to experiments/2026-09-06-change-writers-room-organiser-testing.
Measured 2026-09-06 in
experiments/2026-09-06-defect-budget-exhausted-classification/VERIFY.md.
OUT OF SCOPE: the budget-stop classification, and the organiser's design.
```
