# Verification

## Verdict: **REFUTED — no fix, and none was needed**

GOAL.md's Observed line was wrong. `lifecycle.py:273` is already
guarded, by a test that builds the same subject the same way and kills
both meaningful mutations. No test was written; writing one would have
duplicated an existing guard and cost gate time on every run forever.

`dr-reproduce` states the principle this tranche closes on: *"a refuted
diagnosis is a successful phase, not a failure."* The same holds one
phase later, where the refutation actually landed.

## The covering test, and proof that it bites

`tests/test_workflow_resume_lifecycle_c4.py:353`
`test_completed_typed_terminal_is_not_continuation_authority`

    baseline                                          1 passed
    add "completed" to RESUMABLE_STOP_REASONS         1 FAILED
    delete the raise at lifecycle.py:273              1 FAILED
    restored                                          1 passed

`git status --porcelain src/` clean after each restore.

The second mutation is the one that could have slipped past.
`WellFormednessError` IS a `ValueError` subclass
(`MRO: WellFormednessError, ValueError, Exception, BaseException`), so
`pytest.raises(ValueError)` alone would have caught the INNER guard's
error and passed green. The existing test fails because
`match="NOT_AUTHORIZED"` does not match the inner guard's message,
`"terminal stop reason does not authorize RESUMED"`. It already
satisfies the error-identity constraint REPRO.md derived as necessary —
independently, and before this tranche existed.

## The error, and its cost

The false claim originated in W1's PARKED.md and propagated into this
tranche's GOAL.md and DIAGNOSIS.md. The invalid step is one sentence
wide: W1's census proved **no committed ROOT can witness this guard**,
which is true, and I extended it to **therefore nothing tests it**,
which does not follow. A constructed test needs no committed root —
which is precisely what GOAL.md then went on to specify in detail, at
length, without noticing the contradiction.

What a correct check cost:

    $ grep -rn "NOT_AUTHORIZED" tests/ --include=*.py
    tests/test_workflow_resume_lifecycle_c4.py:407:
        with pytest.raises(ValueError, match="NOT_AUTHORIZED"):

In W1 I grepped `CONTINUE_TYPED_STOP_REQUIRED` — that tranche's string —
and never `CONTINUE_NOT_AUTHORIZED`, the code `prepare_continuation`
wraps THIS guard in. Grepping the guard's own message would also have
missed it: that string appears nowhere in `tests/`.

The map pointed the right way and I under-read it. `DR-SUB-workflow`'s
`Verify:` line runs the very file holding the test, and the test's NAME
states the finding outright. `dr-diagnose` had me read that document's
`Traps` section — which did its job, surfacing
`test_bridge_after_typed_stop.py` — but I never read the test index of
the file the same document's `Verify:` line runs.

Cost: one tranche of goal, diagnosis and reproduction. Cheap relative to
committing a duplicate test, which is what the alternative was.

## What survives, and it is not nothing

- **Y1 — the inner guard is genuinely unwitnessed.** `replay.py:2251`
  applies the same rule while APPLYING the RESUMED transition. The
  existing test fails when the OUTER guard is deleted (the message
  changes), but nothing fails when only the INNER guard is removed.
  Found by REPRO.md's mutation (d); parked with a ready-to-send prompt
  that carries this tranche's lesson — check for an existing test first.
- **Partial mitigation shipped.** The new `Traps` check greps for the
  inner guard's raise, so deleting it now fails `docs_verify`. That is
  presence, not behaviour: Y1 still stands.
- **Y2** — `test_bridge_after_typed_stop.py` asserts against
  `repair_exhausted`, a `StopMetrics` field no writer emits as a stop
  reason.
- **The controller's reason vocabulary, measured**: `completed` /
  `converged` / `stuck`, only `converged` resumable — so the guard's
  commonest real subject is a run that FINISHED, not one that broke.

## Changes made, and instruments

Documentation only. No `src/`, no `tests/`:

    M docs/map/SUB-workflow.md
    M experiments/2026-08-05-fix-continue-refusal-coverage/PARKED.md   (X1 withdrawn at source)
    M experiments/2026-08-05-fix-resumable-reason-guard-coverage/DIAGNOSIS.md
    M experiments/2026-08-05-fix-resumable-reason-guard-coverage/GOAL.md
    A experiments/2026-08-05-fix-resumable-reason-guard-coverage/FIX.md

    docs_verify: 51 documents, 817 checks, 0 failed   (816 -> 817, the new check)
    docs_verify --audit: 0 finding(s)
    DR-SUB-workflow Verify line: 71 passed
    diff: 87 changed lines against the <=150 ceiling

**The full gate was NOT re-run, deliberately.** Nothing under `src/` or
`tests/` changed, and `CLAUDE.md` records re-deriving an unmoved result
as a real mistake ("one tranche ran the full gate four times… ~44
minutes"). The last gate measurement, `3340 passed, 7 skipped, 0 failed`
at `a65e8578`, remains the current answer because no reader and no
subject moved. `docs_verify`'s 817 checks include the covering test and
run it live.

`Verified-at:` on `SUB-workflow.md` advances to `a65e8578` — the commit
its `Verify:` line was re-run against, which is the last commit that
touched the code it describes.

## Corrections, in place rather than rewritten

GOAL.md, DIAGNOSIS.md and W1's X1 entry each keep their original text
below a correction banner, per the practice set by
`experiments/2026-08-05-fix-loopback-fixture-daemon/DIAGNOSIS.md`: the
wrong turn is evidence about how this class of error is made, and
deleting it would delete the lesson while leaving the habit.

## Residue (honest)

- **Y1 is a real gap and this tranche did not close it.** The tranche
  that set out to add coverage added none, and the coverage that IS
  missing is one layer deeper than the one it aimed at.
- **The X1 prompt was live for one operator turn.** It was in
  PARKED.md, marked ready-to-send, and it was sent. Any other
  ready-to-send prompt in this session's PARKED files carries the same
  risk of asserting a gap that a grep would close.
- **Carried**: X2, X3, W2, W3, V2, V4, U1, U3, T3, T4, S2, S3, P1a,
  P1b, P1e, P7, and the `INDEX.md` routing gaps.
