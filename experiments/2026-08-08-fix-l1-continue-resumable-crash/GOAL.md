# Goal: `deepreason continue` must never crash resuming a run stopped mid-decomposition of a criticism batch
Class: defect

Map ids (preflight): `DR-SUB-workflow`, `DR-SEAM-harness-x-workflow`
(the recovery/decomposition dispatch this defect lives in is workflow
authority materialized through the harness's control-event seams);
`DR-INV-frozen-surfaces` read first — `workflow/` is NOT one of the
five frozen surfaces, but `harness.py` (surface 2) is, and this seam
document's own "How to change it" section orders any workflow-side fix
as reader-before-writer against that frozen surface.

Observed (two symptoms of the same root cause, both from the typed
record, not from prose):

1. `deepreason --root <root> continue` on the committed reproduction
   fixture (`experiments/2026-08-08-live-two-seat-ab-s6/home-s6/runs/
   failed-epoch1-run-8c77c6588485304d1f73416318c62949`) crashes:
   `error_type: "NonConjectureRecoveryAuthorityError"`, `error:
   "unknown critic task"`, terminal `state: "failed"`, `stop_reason:
   "operational_failure"` — traced (S6's own `PARKED.md` P3) to
   `workflow/nonconjecture_recovery.py:644`'s `_criticism_contract`,
   which asserts the top-level batch schema
   (`criticism.semantic-task.v1`) against what the fixture's own
   `run-result.json` (`model_execution.contract_decompositions`) shows
   is an ATOMIC child payload (`critic.atomic-target.v1`) of a
   partially-completed `route_seat_compact_recovery` decomposition
   (two sibling children already `terminal_status: "completed"`).
2. The SAME committed fixture root, once present in the tree, makes
   `tests/test_continuation.py::
   test_a_stop_with_no_typed_receipt_refuses_continuation` fail
   (D1's own `PARKED.md` P2): the test's non-resumable-stop witness
   scan finds this root refused with `CONTINUE_RESUME_RECOVERY_
   MISMATCH`, not the `CONTINUE_TYPED_STOP_REQUIRED` it asserts every
   non-resumable stop shares.

Success criterion (machine-decidable, covers BOTH symptoms):

    # (a) the crash class is gone, on both the real fixture (copied,
    #     never edited) and a synthetic mid-decomposition root built
    #     without a live provider:
    python -m pytest tests/test_l1_continue_resumable_crash.py -q
    # -> "N passed, 0 failed" — asserts, per case: no
    #    NonConjectureRecoveryAuthorityError is raised; terminal state
    #    is NEVER "failed"/"operational_failure" for this cause; the
    #    outcome is either a correct resumption (decomposition
    #    continues/completes) or ONE consistent typed refusal reason.

    # (b) the currently-red continuation gate test goes green under
    #     whichever semantics FIX.md chooses (resume-and-continue, or
    #     refuse-typed-consistently) -- FIX.md decides which, with
    #     evidence; if FIX.md concludes the test's own expectation is
    #     too narrow, FIX.md argues that in writing and the change to
    #     the test is part of the same reviewed fix, never a silent
    #     patch:
    python -m pytest tests/test_continuation.py::test_a_stop_with_no_typed_receipt_refuses_continuation -q
    # -> "1 passed"

    # (c) nothing else regresses:
    python -m pytest tests/ -q -n 4
    # -> "0 failed" net of the named pre-existing P1/P3
    #    (tests/test_module_fingerprints.py::
    #    test_absence_is_valid_before_the_feature_and_presence_valid_after)
    #    — explicitly out of this tranche's scope, stays parked.

In scope:
- `src/deepreason/workflow/nonconjecture_recovery.py` (the traced
  dispatch defect, `_criticism_contract` and its resume-time routing)
- `src/deepreason/workflow/` more broadly, ONLY if diagnosis shows the
  correct fix lives in a sibling dispatch/replay function rather than
  `nonconjecture_recovery.py` itself (e.g. how a resumed item is
  routed to its handler) — DIAGNOSIS.md must show the trace, not
  assume the file
- `tests/test_continuation.py` (test-expectation revision only if
  FIX.md argues in writing that the current assertion is too narrow;
  never a silent patch to make it pass)

NOT in scope:
- The module-fingerprints double-stamp failure (`P1/P3`,
  `tests/test_module_fingerprints.py`) — a different, already
  four-times-parked defect; stays parked, per the task's explicit
  instruction and CLAUDE.md's one-tranche-one-goal rule.
- Rung L2 (budget-stop-invalid-record design), L3 (seat bindings in
  run identity), L4 (dead coder seat) — separate rungs of the same
  defect PROGRAM, each its own tranche per
  `docs/proposals/RECORD_LIFECYCLE_DEFECT_PLAN.md`.
- Any of the five frozen surfaces (`capabilities/state.py`,
  `harness.py` event application, replay-validation record formats,
  manifest schemas+validators, qualification subject digests) — the
  plan's own expectation is zero contact; any actual contact is a STOP
  for operator words, not a fix decision this tranche makes alone.
- P1/P2 from S6's own `PARKED.md` (dead coder seat; run-identity
  omits seat bindings) — unrelated defects, already parked with their
  own ready-to-send prompts.

Budget: <=150 changed lines, 1 commit (the `dr-implement-fix` commit;
`FIX.md` itself is a separate, earlier, no-code commit per this
tranche's own STOP-after-FIX.md instruction), sized to a single-file
dispatch-routing correction — a design that requires touching
`harness.py`'s frozen event-application surface would itself trip the
orchestrator's stop condition, not fit this budget.

Stop conditions inherited from orchestrator: yes. Additional stop
named by the task assignment: stop after `FIX.md` is committed and
pushed — the fix design is reviewed before `dr-implement-fix` runs.
