# Reproduction

Form: **offline unit reproduction**. Record replay was unavailable and
DIAGNOSIS.md establishes why — no committed root carries a receipt whose
reason is non-resumable — so the subject is constructed. The construction
is held to GOAL.md's line: a real `StopController` decides, the
production writer `build_stopped_lifecycle` records, the harness applies
the transition, and the assertion comes from `prepare_continuation`, the
public entry, not from calling the guarded function directly.

## Artifact

The scaffolding is `tests/test_v6_resumed_terminal_revalidation.py`'s
`_record_converged_stop` (line 148) and `_start_converged_run` (line
186), with ONE difference: the `StopMetrics` field that decides which
reason the controller returns.

    def _record_stop(root, manifest, harness, *, workload_complete):
        policy = StopPolicy(min_cycles=0, window=1, stable_windows=1)
        resume = harness.workflow_state.current_resume_decision
        controller = StopController(
            policy,
            state=resume.controller_state if resume is not None else None,
        )
        before = controller.snapshot()
        cycle = 0 if before.last_cycle is None else before.last_cycle + 1
        metrics = StopMetrics(cycle=cycle, workload_complete=workload_complete)
        decision = controller.evaluate(metrics)      # the REAL controller
        assert decision.stop is True
        stop = build_stop_record(reason=decision.reason, policy=policy,
                                 metrics=metrics, event_seq=harness._next_seq)
        control = manifest.control_plane_policy
        observation, snapshot, lifecycle = build_stopped_lifecycle(
            harness.workflow_state, ..., deterministic_decision=decision, ...
        )                                            # the PRODUCTION writer
        harness.record_lifecycle_transition(observation, snapshot, lifecycle)
        persist_stop_record(root, stop)
        return stop

The run is started through `TextRunApplicationService` with
`deepreason.ops.run_scheduler` replaced by a fixture that records the
stop and returns, so no provider is involved. Then, on the finished root:

    prepare_continuation(root, cycles=1, tokens=10,
                         expected_manifest_digest=manifest.sha256,
                         check_operator_lock=False)

## Current output

    RESUMABLE_STOP_REASONS = ['budget_exhausted', 'converged']

    workload_complete=True
      receipt present : True
      receipt reason  : 'completed'
      resumable       : False
      prepare_continuation -> ValueError: CONTINUE_NOT_AUTHORIZED:
                              terminal stop reason does not authorize continuation

    workload_complete=False
      receipt present : True
      receipt reason  : 'converged'
      resumable       : True
      prepare_continuation -> ACCEPTED

## Confirms diagnosis: yes

Both halves of DIAGNOSIS.md's prediction hold. One `StopMetrics` field
flips a real controller decision from `converged` to `completed`, and
that alone flips `prepare_continuation` from accepting to refusing. The
twin is what makes it a claim about the REASON rather than about the
fixture: everything else — root, manifest, writer, harness, entry point
— is identical between the two runs.

## Mutation proof: four candidates measured, two bite as intended

| # | mutation | `completed` | `converged` | verdict |
|---|---|---|---|---|
| — | baseline | refused | ACCEPTED | — |
| a | drop `budget_exhausted` from the frozenset | refused | ACCEPTED | **VACUOUS** |
| b | drop `converged` from the frozenset | refused | refused | kills the TWIN |
| c | add `completed` to the frozenset | **ACCEPTED** | ACCEPTED | kills the REFUSAL |
| d | delete the raise at `lifecycle.py:273` | refused, DIFFERENT error | ACCEPTED | kills on error identity |

`git status --porcelain src/` clean after each restore.

### Correction: GOAL.md's proposed mutation is vacuous

GOAL.md specified *"narrow `RESUMABLE_STOP_REASONS` (drop
`budget_exhausted`) -> must FAIL"*. Measured, it changes nothing —
mutation (a) above. The reason is obvious once stated: this tranche's
subject is `completed` versus `converged`, and `budget_exhausted`
appears in neither. That reason belongs to W1's roots, not to these.

The narrowing that DOES kill the test is dropping **`converged`** (b),
and the mutation that most directly expresses the defect being guarded
is ADDING **`completed`** (c) — literally "reclassify a finished run as
resumable", which is what a careless widening of owner decision 4a would
look like.

This is the second proposed mutation in two tranches that turned out not
to bite. Both were plausible and both were checked before being relied
on; the pattern is that a mutation aimed at a frozenset only bites if
the frozenset entry it touches is one the test's subject actually
exercises.

## The finding that mutation (d) surfaced: the rule is defended twice

Deleting `lifecycle.py:273` outright does NOT let a completed run
resume. It fails one layer deeper:

    WellFormednessError: terminal stop reason does not authorize RESUMED

from `src/deepreason/workflow/replay.py:2251`, which applies the same
`RESUMABLE_STOP_REASONS` test when the RESUMED transition is applied to
the harness. `lifecycle.py:273` is the outer guard, raised while
BUILDING the resume decision; `replay.py:2251` is the inner one, raised
while APPLYING it.

Two consequences, and they pull in opposite directions:

- **Reassuring**: removing the outer guard is not a security hole. The
  product still refuses; only the error type and the layer change.
- **Sobering**: it means a test asserting merely "some exception is
  raised" would survive mutation (d) and prove almost nothing. The
  assertion must be on the ERROR IDENTITY —
  `CONTINUE_NOT_AUTHORIZED: terminal stop reason does not authorize
  continuation` — for the mutation to bite. That is a real design
  constraint on the fix, not a stylistic preference.

`replay.py` is owned by `DR-SUB-workflow` (`Owns:
src/deepreason/workflow/`). The inner guard is not named by any of
`INV-frozen-surfaces`'s five surfaces, but it lives on the replay path
that surface 3 protects, which is a reason to guard it rather than
rewrite it. Its own coverage is a separate question and is parked as
**Y1**.

## Post-fix expectation

The artifact becomes a test in `tests/`, and:

    python -m pytest tests/ -q -n 4   -> 3341 passed, 0 failed

with mutations (b), (c) and (d) still killing it and (a) still not —
recorded so a later reader does not "fix" the test for failing to
respond to a mutation it was never sensitive to. As with W1, the
reproduction PASSES today: the product is correct and the gap is the
absence of a guard, so the mutation table, not the pass, is the
evidence.

## Cost

One `TemporaryDirectory`, two constructed roots, no provider, no
committed root touched. Wall clock for both halves: a few seconds — the
existing sibling tests in
`tests/test_v6_resumed_terminal_revalidation.py` run the same
construction and the file completes well inside the gate's budget.
