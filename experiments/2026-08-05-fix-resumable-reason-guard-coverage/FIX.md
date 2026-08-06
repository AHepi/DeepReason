# Fix: **NONE.** The premise is refuted — the guard is already covered, and the existing test kills both mutations

Guarantee restored: nothing, because nothing was missing.
`tests/test_workflow_resume_lifecycle_c4.py:353`
`test_completed_typed_terminal_is_not_continuation_authority` already
guards `lifecycle.py:273`, and it is a better test than X1 assumed had
to be built.

## What the existing test does

Read after the reproduction was already working — which is the wrong
order, and the correction below says so:

    policy = StopPolicy()
    controller = StopController(policy)              # the REAL controller
    metrics = StopMetrics(cycle=1, workload_complete=True)
    stop_decision = controller.evaluate(metrics)     # -> reason 'completed'
    ...
    observation, snapshot, lifecycle = build_stopped_lifecycle(...)
    harness.record_lifecycle_transition(observation, snapshot, lifecycle)
    persist_stop_record(tmp_path, stop_record)
    harness.write_workflow_checkpoint()
    ...
    with pytest.raises(ValueError, match="NOT_AUTHORIZED"):
        prepare_continuation(tmp_path, cycles=5, tokens=100)

That is, feature for feature, the construction DIAGNOSIS.md derived
independently and REPRO.md demonstrated: a real `StopController`,
`workload_complete=True` producing the `completed` reason, the
production writer, the harness transition, and the assertion taken from
`prepare_continuation` — the public entry, exactly the line GOAL.md said
must be held.

## And it bites — measured, not assumed

The same mutations REPRO.md ran against the reproduction, run against
the EXISTING test:

| mutation | existing test |
|---|---|
| baseline | `1 passed` |
| (c) add `completed` to `RESUMABLE_STOP_REASONS` | **`1 failed`** |
| (d) delete the raise at `lifecycle.py:273` | **`1 failed`** |
| restored | `1 passed` |

Mutation (d) is the one that could have slipped past. `WellFormednessError`
IS a `ValueError` subclass (`MRO: WellFormednessError, ValueError,
Exception, BaseException`), so `pytest.raises(ValueError)` alone would
have caught the inner guard's error and passed. It fails because
`match="NOT_AUTHORIZED"` does not match the inner guard's message,
`"terminal stop reason does not authorize RESUMED"`. The existing test
already satisfies the error-identity constraint REPRO.md derived as
necessary.

## The correction, and how the error was made

**GOAL.md's Observed line is wrong**, and so is the X1 entry in
`experiments/2026-08-05-fix-continue-refusal-coverage/PARKED.md` that
seeded it. Both assert "no test in the gate exercises it". A test does.

The inference that produced the error is specific and worth naming.
W1's census established a TRUE fact — *no committed root can witness
this guard*, because every receipt-carrying root stopped on
`budget_exhausted` — and I extended it to *therefore nothing tests it*.
That step is invalid: a constructed test needs no committed root, which
is the entire point of the constructed-subject discipline GOAL.md then
went on to specify. The census answered a question about the RECORD and
I let it answer a question about the TESTS.

What a correct check costs, and what it would have returned:

    $ grep -rn "NOT_AUTHORIZED" tests/ --include=*.py
    tests/test_workflow_resume_lifecycle_c4.py:407:
        with pytest.raises(ValueError, match="NOT_AUTHORIZED"):

One grep. In W1 I grepped for `CONTINUE_TYPED_STOP_REQUIRED` — that
tranche's string — and never for `CONTINUE_NOT_AUTHORIZED`, the code
`prepare_continuation` wraps THIS guard in. The guard's own message,
`"terminal stop reason does not authorize continuation"`, appears
nowhere in `tests/`, so grepping the message would ALSO have missed it;
only the wrapped code finds it.

The map pointed the right way and I under-read it.
`DR-SUB-workflow`'s `Verify:` line runs
`tests/test_workflow_resume_lifecycle_c4.py`, and the file's own
function list contains
`test_completed_typed_terminal_is_not_continuation_authority` — a name
that states the finding outright. I read that file's `Traps` section in
`dr-diagnose` (which correctly surfaced
`test_bridge_after_typed_stop.py`) but not its test index.

## Change sites (exhaustive)

None in `src/`. None in `tests/`. Specifically **no new test**: adding
one would duplicate an existing guard, cost gate time on every run, and
create two places to update when the reason vocabulary changes — the
opposite of what this tranche was for.

Documentation only, and only because the false claim is now committed in
three places:

1. **`experiments/2026-08-05-fix-continue-refusal-coverage/PARKED.md`** —
   X1's entry, corrected in place with a pointer here. The ready-to-send
   prompt it carries must not be sent.
2. **This tranche's `GOAL.md` and `DIAGNOSIS.md`** — corrected in place
   rather than rewritten, per the repo's practice for a wrong turn that
   is itself evidence (see
   `experiments/2026-08-05-fix-loopback-fixture-daemon/DIAGNOSIS.md`).
3. **`docs/map/SUB-workflow.md`** — a `Traps` entry, because the next
   person to ask "is this guard covered?" should not have to repeat
   this. The trap is the inference, not the guard: a census over
   committed roots cannot tell you what the tests cover.

## What the tranche produced that is worth keeping

Not nothing, and not the test it set out to write:

- **The inner guard, `replay.py:2251`.** Found by REPRO.md's mutation
  (d). Parked as **Y1**, and it is a REAL gap: the existing test fails
  under (d) because the outer guard's message changes, but nothing
  witnesses the inner guard on its own. Y1's prompt needs the same
  correction discipline applied before it is run — check for an existing
  test first.
- **`repair_exhausted` is not a stop reason** (Y2), a durability smell
  in `test_bridge_after_typed_stop.py`.
- **The controller's reason vocabulary**, measured:
  `completed` / `converged` / `stuck`, with only `converged` resumable —
  and the observation that the guard's most common real subject is a run
  that FINISHED.

## Existing tests at risk

None. Nothing is changed that any test reads.

## Budget ceiling

GOAL.md set <=150 changed lines. The actual diff will be documentation
only — this file, three corrections, one `Traps` entry — and will be
compared against the ceiling with `git diff --stat` before the commit
per `132bdbb9`, as with any other commit.

## Approval gate

`dr-propose-fix` says a refuted premise stops and reports rather than
proceeding. There is no fix to approve and no code to change, so this
tranche does not advance to `dr-implement-fix`. It closes at
`dr-verify-outcome` with a verdict of **REFUTED**, the corrections
committed, and Y1 as the surviving lead.
