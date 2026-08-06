# Parked — noticed during the X1 tranche, not done

## Y1 — the INNER resumable-reason guard is also uncovered

`src/deepreason/workflow/replay.py:2251` applies the same
`RESUMABLE_STOP_REASONS` test as `lifecycle.py:273`, one layer deeper:
the outer guard fires while BUILDING a resume decision, the inner one
while APPLYING the RESUMED transition to the harness. Found by mutation
(d) in REPRO.md — deleting the outer guard does not let a completed run
resume, it fails as
`WellFormednessError: terminal stop reason does not authorize RESUMED`.

This tranche guards the outer one and asserts on its error identity, so
mutation (d) bites. The inner guard remains unwitnessed on its own: a
change that removed BOTH would be caught, but a change that removed only
the inner one would not be.

Reaching it requires constructing a resume decision that passes the
outer guard and then applying it — i.e. building the transition against
a receipt the outer guard accepts and mutating the reason afterwards, or
calling the replay application path directly. That is a different
subject and a different construction from this tranche's.

**Ready-to-send prompt for the next runner:**

> Defect tranche via deepreason-orchestrator. Y1 from
> `experiments/2026-08-05-fix-resumable-reason-guard-coverage/PARKED.md`:
> `workflow/replay.py:2251` ("terminal stop reason does not authorize
> RESUMED") is the inner twin of the guard X1 covered, and nothing
> witnesses it alone — X1's test asserts on the OUTER guard's error
> identity, so removing only the inner guard breaks no test. One goal:
> give the inner guard its own regression. Read
> `experiments/2026-08-05-fix-resumable-reason-guard-coverage/REPRO.md`
> first — its mutation (d) is the evidence, and its scaffolding
> (`_record_stop`, a real StopController plus `build_stopped_lifecycle`)
> is what to reuse. Mutation-prove by neutralising the inner raise ONLY,
> with the outer guard intact, and record which assertion fires. Note
> that replay.py sits on the path `DR-INV-frozen-surfaces` surface 3
> protects: guard it, do not rewrite it, and do NOT change `src/`. End
> state: full gate 0 failed with one new test, `DR-SUB-workflow`'s Traps
> updated. One tranche, one goal.

## Y2 — `test_bridge_after_typed_stop.py` asserts against a reason the product cannot emit

Carried from DIAGNOSIS.md. `_state` builds its non-resumable subject
with `reason="repair_exhausted"` on a `SimpleNamespace`;
`repair_exhausted` is a `StopMetrics` FIELD, and no writer emits it as a
stop reason. The controller's three reasons are `completed`,
`converged`, `stuck`.

The test still proves what it means to — its branch only needs a reason
outside `RESUMABLE_STOP_REASONS` — so this is not a defect in what it
guards. It is a durability smell: a hand-assembled subject asserting
against a string the product never produces would keep passing if the
real reason vocabulary changed underneath it.

Not fixed here: different test, different branch (`WorkflowReplayState.
observe_event`, not the continuation guard), and touching it would widen
this tranche past its one goal.

## Carried, still parked

X2 (W1's witness class grows only when runs fail), X3 (W1's selection
trusts the stop record over replayed state), W2 (unmeasured cancel race
in the operational smoke), W3 (six smoke stages with one green
observation each), V2, V4, U1, U3, T3, T4, S2, S3, P1a, P1b, P1e, P7.

Also still open from the V1 preflight: `application × periphery` is an
unwritten seam absent from `INDEX.md`'s matrix, and `SUB-application.md`,
`SUB-periphery.md` and `SUB-amendment.md` are on disk but routable from
no `INDEX.md` table.
