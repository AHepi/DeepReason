# Diagnosis: the guard's real subject is a run that FINISHED — `completed` is a production stop reason, is written into a typed receipt by the production writer, and is not resumable

Primary cause: `RESUMABLE_STOP_REASONS` holds `{converged,
budget_exhausted}`, but the deterministic `StopController` can return
three stop reasons — `completed`, `converged`, `stuck` — and the
scheduler writes ALL of them into a typed STOPPED lifecycle receipt via
`build_stopped_lifecycle` (`scheduler.py:2657-2668`,
`reason=decision.reason`, no filtering). So two of the controller's
three reasons produce exactly the state `lifecycle.py:273` guards: a
receipt present, its reason not resumable. The guard is uncovered not
because its subject is exotic but because **no committed root happens to
carry one** — the campaign roots all stopped on `budget_exhausted`, and
`operational_failure` roots carry no receipt at all.

The subject is not merely constructible; it is the ORDINARY outcome of a
run that finishes its workload. `completed` is what the controller
returns when `metrics.workload_complete` and the mandatory checks and
research are clear — the best ending a run has. That such a run is
non-resumable is coherent (there is nothing left to continue) and it
means the guard's most common real-world subject is a successful run,
not a broken one.

## Measured, not inferred

A real `StopController` — the production class, no stub — under the same
policy the existing scaffolding uses:

    RESUMABLE_STOP_REASONS = ['budget_exhausted', 'converged']

    metrics                          stop   reason        resumable
    StopMetrics(cycle=0,
                workload_complete=True)  True   'completed'   False
    StopMetrics(cycle=0)                 True   'converged'   True

One field flips the decision from the resumable reason to the
non-resumable one, through the product's own evaluator. That is the
whole construction: no invented reason string, no hand-built
`StopDecision`.

## Evidence

- `src/deepreason/runtime/stop.py:184,188,209` — the controller's three
  stop reasons: `completed` (workload complete, checks clear),
  `converged` (stable window), `stuck` (repeated corroborated signal
  after the escape ladder). Only `converged` is resumable.
- `src/deepreason/scheduler/scheduler.py:2657-2668` — the typed-receipt
  writer, called with `deterministic_decision=decision` for whatever the
  controller decided. The only branch that skips it is a manifest with
  no owned control plane, which falls back to `write_stop_record` and a
  bare stop.
- `src/deepreason/application/text_runs.py:205-232` — the OTHER writer,
  `_record_exhaustion_lifecycle_stop`, which is `budget_exhausted`-only.
  Between them, every reason that can reach a receipt is accounted for.
- `src/deepreason/workflow/lifecycle.py:28,273` — the frozenset and the
  guard.
- The census in
  `experiments/2026-08-05-fix-continue-refusal-coverage/DIAGNOSIS.md` —
  16 roots hold a receipt, all `budget_exhausted`. This diagnosis
  explains WHY rather than merely restating it: the committed roots are
  campaign runs that exhausted bounded budgets, and no committed run
  ever finished its workload or went `stuck`.

## The scaffolding already exists, and it is the right kind

`tests/test_v6_resumed_terminal_revalidation.py:148`
`_record_converged_stop` drives a REAL `StopController`, asserts the
decision it got, and hands it to `build_stopped_lifecycle` and
`harness.record_lifecycle_transition` — the production path end to end.
It is one `StopMetrics` field away from producing this tranche's
subject, and `_start_converged_run` (line 186) already builds the v6
root it needs.

## A finding about the neighbouring test, recorded not fixed

`tests/test_bridge_after_typed_stop.py`'s `_state` helper builds its
non-resumable stop with `reason="repair_exhausted"` on a
`SimpleNamespace`. **`repair_exhausted` is a `StopMetrics` FIELD, not a
stop reason** — no code path can produce it as one. The test still
proves what it means to, because its branch only needs "a reason outside
`RESUMABLE_STOP_REASONS`", and it is testing `WorkflowReplayState`
rather than the controller. But it is a hand-assembled subject using a
string the product never emits, and it is the anti-pattern GOAL.md
warned this tranche against. Parked, not fixed: it is a different test
guarding a different branch, and touching it would widen this tranche.

## Implicated code (0 sites)

None. The guard is correct and `src/` is not touched. What is missing is
a witness, and the gap is in `tests/`.

## Falsifiable prediction (what `dr-reproduce` must show)

    # A v6 root stopped through the production writer with a real
    # controller decision of 'completed' must be refused by the PUBLIC
    # entry, not by calling the guarded function directly:
    prepare_continuation(root, cycles=1, tokens=10)
      -> ValueError containing "terminal stop reason does not authorize
         continuation"   (wrapped by prepare_continuation as
         CONTINUE_NOT_AUTHORIZED)

    # and the twin, proving the subject is the REASON and nothing else:
    the same construction with metrics workload_complete=False
      -> reason 'converged', continuation ACCEPTED

If the second half does not hold, the refusal is coming from something
other than the reason and the test would be guarding the wrong thing.

## Ruled out

- **That the subject needs an invented or exotic reason.** It does not:
  `completed` is what an ordinary successful run records. Checked
  against the controller itself rather than assumed from the frozenset.
- **That `repair_exhausted` is the reason to use** — the neighbouring
  test's choice. It is a metrics field; no writer emits it as a reason,
  so a test using it would assert against a string the product cannot
  produce, and would keep passing if the real reasons changed.
- **That a committed root might witness it after all.** The census is
  exhaustive over `git ls-files` and every receipt-carrying root reads
  `budget_exhausted`. Record replay, which W1 used, is genuinely
  unavailable here.
