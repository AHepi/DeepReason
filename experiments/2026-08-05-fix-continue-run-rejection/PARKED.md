# Parked — noticed during the V1 tranche, not done

## W1 — `CONTINUE_TYPED_STOP_REQUIRED` has no test the gate runs

Repo-wide the string appears exactly four times: its raise site
(`src/deepreason/runtime/continuation.py:352`), the smoke's matcher
(`scripts/wheel_operational_smoke.py`, two lines), and
`tests/test_wheel_operational.py::test_operational_smoke_requires_exact_non_resumable_rejection`
— which tests the SMOKE'S STRING MATCHER, not the product path. After
this tranche the refusal has a real end-to-end witness again, but that
witness is `scripts/wheel_operational_smoke.py`, and **no `pytest` run
executes it**. It runs only in CI's wheel-smoke job.

So a `src/` change that made the refusal unreachable — widening
`RESUMABLE_STOP_REASONS` again, or recording a typed receipt on a path
that should not carry one — would pass the full gate and be caught only
after a CI job that has been red for over a week at a stretch this year.
That is exactly how the present defect survived from 2026-07-27 to
2026-08-05.

Not fixed here: GOAL.md's one goal was the continuation surface, and
adding product-side coverage for a refusal is a different tranche with a
different subject (a constructed non-resumable terminal, offline).

**Ready-to-send prompt for the next runner:**

> Defect tranche via deepreason-orchestrator. W1 from
> `experiments/2026-08-05-fix-continue-run-rejection/PARKED.md`:
> `CONTINUE_TYPED_STOP_REQUIRED` (`runtime/continuation.py:352`) has no
> test the full gate runs — its only end-to-end witness is
> `scripts/wheel_operational_smoke.py`, which no `pytest` run executes,
> and the one test naming the string tests the smoke's own matcher. One
> goal: give the refusal an offline regression the gate runs. Build the
> non-resumable terminal with the existing helpers in
> `tests/test_continuation.py` / `test_v6_resumed_terminal_revalidation.py`
> (the latter already constructs typed stops for the resumable case, so
> the inverse should be cheap), assert `prepare_continuation` raises
> `CONTINUE_TYPED_STOP_REQUIRED`, and mutation-prove it by removing the
> raise. Do NOT change `src/`: `2d4ca2e1` is a named owner decision and
> the current behaviour is correct — this tranche adds coverage, not
> behaviour. End state: full gate 0 failed with one new test, and
> `DR-SUB-application`'s Traps entry updated to say the gate now covers
> it. W2 stays parked. One tranche, one goal.

## W2 — the cancel race is bounded but unmeasured

`_await_cancellable_cycle` gives the subject 11 cycles of margin
(`NON_RESUMABLE_SUBJECT_CYCLES = 12`,
`NON_RESUMABLE_CANCEL_AFTER_CYCLE = 1`) and raises rather than proceeds
if the run has already left `starting`/`running`, so a lost race fails
the stage loudly instead of silently substituting a continuable stop for
a non-resumable one. That is fail-closed by construction.

What is NOT established is how often it loses. Two observations exist —
REPRO.md's manual run and this tranche's verifying smoke run — and both
won at cycle 2 of 12. Two is not a flakiness measurement, and the smoke
runs on three CI arms.

Recorded rather than chased: measuring it costs many smoke runs, and the
failure mode is a loud stage failure, not a wrong verdict. Revisit if
the wheel-smoke job shows an intermittent `continuation_rejection`
failure whose message is "cancellation subject did not reach an
operator-cancelled stop" or "cancellation subject terminated before it
could be cancelled".

## W3 — every stage past `continuation_rejection` has now run exactly once

`replay_validation`, `restart_recovery`, `budget_rejection`,
`manifest_rejection`, `disclosure_check` and `cleanup` reached green for
the first time in this container today. Their assertions are newly
EXERCISED, not newly PROVEN: any staleness in them of the kind this
session found four times over would have been invisible until now, and a
single green run does not distinguish "correct" from "correct today".
No action; recorded so a later failure in one of them is read as
first-exposure rather than as a regression.

## Carried, still parked

V2 (set-vs-tuple `EXPECTED_MCP_TOOLS` duplication across the two smokes
— the operator parked it explicitly for this tranche, and the fix did
not touch either pin), V4 (T2's diagnostic channel with no legal
destination on a failing run), U1, U3, T3, T4, S2, S3, P1a, P1b, P1e,
P7.
