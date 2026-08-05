# Parked — noticed during the W1 tranche, not done

## X1 — the receipt-present, reason-non-resumable path has no witness at all

This tranche guarded `CONTINUE_TYPED_STOP_REQUIRED`
(`runtime/continuation.py:352`), which fires when a run holds NEITHER a
terminal lifecycle decision NOR a resume decision. A second, independent
guard sits at `workflow/lifecycle.py:273`:

    if terminal.deterministic_decision.reason not in RESUMABLE_STOP_REASONS:
        raise ValueError("terminal stop reason does not authorize continuation")

That one fires when a typed receipt IS present but names a reason
outside `{converged, budget_exhausted}` — and it is reached only through
`build_resumed_lifecycle`, wrapped by `prepare_continuation` as
`CONTINUE_NOT_AUTHORIZED`.

**No committed root can witness it.** The census in DIAGNOSIS.md is
decisive: all 16 roots carrying a receipt stopped on `budget_exhausted`,
which is resumable. So unlike the refusal this tranche guarded, record
replay is not available and a constructed fixture is required — the
`build_stopped_lifecycle` helpers in
`tests/test_v6_resumed_terminal_revalidation.py` are the nearest
scaffolding.

This is the mirror-image gap of the one just closed, and it is the
guard that would actually fire if someone NARROWED
`RESUMABLE_STOP_REASONS` — for instance by reverting owner decision 4a.

**Ready-to-send prompt for the next runner:**

> Defect tranche via deepreason-orchestrator. X1 from
> `experiments/2026-08-05-fix-continue-refusal-coverage/PARKED.md`:
> `workflow/lifecycle.py:273` ("terminal stop reason does not authorize
> continuation") has no test in the gate, and no committed root can
> witness it — all 16 roots carrying a typed receipt stopped on
> `budget_exhausted`, which is resumable. One goal: give that guard a
> constructed regression. Build a v6 root with a typed STOPPED receipt
> whose reason is outside `RESUMABLE_STOP_REASONS`, using the
> `build_stopped_lifecycle` scaffolding already in
> `tests/test_v6_resumed_terminal_revalidation.py`, and assert
> `prepare_continuation` refuses it. Mutation-prove by NARROWING
> `RESUMABLE_STOP_REASONS` (removing `budget_exhausted`) and by
> neutralising the raise — check both kill it and note which assertion
> each fires, since the W1 tranche found two mutations that looked
> interchangeable and were not. Do NOT change `src/`. End state: full
> gate 0 failed with one new test, `DR-SUB-application`'s Traps entry
> updated. W2/W3 stay parked. One tranche, one goal.

## X2 — the witness set can only grow by a run failing

The five witnesses are `operational_failure` roots. That class
accumulates when runs break, which is not something to wish for, and it
is the only permanently non-resumable population in the repo.

If the class were ever pruned — a repo cleanup retiring failed roots,
say — the non-empty guard fires and reports "the refusal has lost its
witness". That is the guard working. The correct response then is to
CONSTRUCT a witness (see X1's scaffolding), never to delete the test or
loosen the guard to tolerate zero.

Recorded so the failure message is read as designed behaviour rather
than as a broken test.

## X3 — the selection trusts `run-stop.json`'s `reason` field

`_non_resumable_committed_roots` reads each root's stop record rather
than its replayed workflow state, deliberately: the replay costs 63.3s
across 28 roots and would assert the code-under-test's own branch
condition back at itself (FIX.md).

The residual exposure is a root whose stop record disagreed with its
replayed state. Nothing suggests one exists, and the failure mode is
legible rather than silent — such a root would be selected and then
raise a DIFFERENT error, failing the per-witness assertion with a
message naming the root and both reasons. Recorded, not chased.

## Carried, still parked

W2 (the unmeasured cancel race in the operational smoke's rejection
stage), W3 (six smoke stages with exactly one green observation each),
V2 (set-vs-tuple `EXPECTED_MCP_TOOLS` duplication), V4 (T2's diagnostic
channel with no legal destination on a failing run), U1, U3, T3, T4, S2,
S3, P1a, P1b, P1e, P7.

Also still open from the V1 preflight, unchanged: `application ×
periphery` is an unwritten seam absent from `INDEX.md`'s matrix
entirely, and `SUB-application.md`, `SUB-periphery.md` and
`SUB-amendment.md` are on disk but routable from no `INDEX.md` table.
