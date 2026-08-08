# Verification

## Criterion command + output (GOAL.md, verbatim)

(a)
```
python -m pytest tests/test_l1_continue_resumable_crash.py -q
...                                                                      [100%]
3 passed in 14.52s
```

(b)
```
python -m pytest tests/test_continuation.py::test_a_stop_with_no_typed_receipt_refuses_continuation -q
.                                                                        [100%]
1 passed in 7.89s
```

(c)
```
python -m pytest tests/ -q -n 4
FAILED tests/test_module_fingerprints.py::test_absence_is_valid_before_the_feature_and_presence_valid_after
1 failed, 3385 passed, 7 skipped in 791.62s (0:13:11)
```
Run at commit `a05c3d44` (the fix commit); `git diff --stat a05c3d44
HEAD -- src/ tests/ tools/` is empty against the current head
(`d763b839`, the FIX.md ledger amendment only) — no code changed
since, so this result is still current, not re-derived for its own
sake per CLAUDE.md's "preserve results, re-derive only what moved"
rule. Net of the named pre-existing P1/P3: **3385 passed, 0 failed.**
(An earlier same-day run of this same suite, executed CONCURRENTLY
with a `docs_verify` background job competing for CPU, showed 4
additional failures — all background-thread-`.join(timeout=2-5s)`
MCP/bridge tests unrelated to this fix's own subsystem; re-run in
isolation, all 4 passed cleanly, confirming CPU contention, not a
regression. Documented for the record, not hidden.)

## Historical roots re-checked

The fix touches a READER (`recover_nonconjecture_admission`'s
dispatch), not a writer, format, or digest — `verify_root`'s own
output shape is untouched by this change, and no committed root's
`valid`/`att`/digest fields are affected by it (confirmed by
construction: the fix only changes which function handles an
in-memory recovery attempt during `continue`, never what gets written
to `log.jsonl`). The relevant "before/after" comparison for THIS fix
is the crash itself, not a `verify_root` finding class:

- `experiments/2026-08-08-live-two-seat-ab-s6/home-s6/runs/
  failed-epoch1-run-8c77c6588485304d1f73416318c62949` (the committed,
  byte-frozen crash fixture) — copied fresh to scratch and replayed via
  `tests/test_l1_continue_resumable_crash.py::
  test_committed_fixture_replays_without_crashing` (part of criterion
  (a) above): before this fix, `Scheduler.run(0)` raised
  `NonConjectureRecoveryAuthorityError("unknown critic task")`
  (`REPRO.md`); after, it completes without raising, and the fixture's
  own atomic-child work item (`sha256:82f77c8...17f9`) is confirmed
  still `terminal.status == "completed"` — recovery correctly leaves
  an already-resolved child untouched rather than corrupting or
  re-processing it.
- `git status --porcelain
  experiments/2026-08-08-live-two-seat-ab-s6/` stays empty after every
  replay in this tranche (this run and all prior ones) — the committed
  fixture itself was never edited, only copied.
- No "known-good" root comparison is owed: this fix adds no new
  authority check reachable by a NON-atomic-child recovery path
  (confirmed in FIX.md's "Existing tests at risk" — the two batch-shape
  authority tests in `test_v6_nonconjecture_recovery.py` still pass
  unchanged, exercising the exact same code they always have).

## Live attempt

None. GOAL.md's success criterion is fully machine-decidable from
offline record replay and the full gate; it does not ask for live
proof, and `dr-verify-outcome`'s own ladder says ascend only as far as
the goal requires. `deepreason continue` runs no model call at all
during crash-prefix recovery (`SUB-workflow.md`'s own "What it is":
"a crashed run can be resumed from the record alone... with the
provider boundary deliberately absent") — a live attempt would add
provider cost and time while proving nothing beyond what the offline
replay of the actual crash fixture already proves byte-for-byte.

## Residue (honest)

- The tranche's own scratch reproduction script
  (`repro_fixture_replay.py`, from `REPRO.md`) was never updated with
  the `stop_controller` construction the permanent regression test
  needed to add (`Scheduler.run()` calls
  `_rehydrate_resumed_stop_controller()` immediately after the
  recovery sweep this fix targets, and needs one bound for a resumed
  run) — it now fails one step further than before, on a SETUP gap in
  the scratch script itself, not on the fixed defect. Not fixed here:
  `FIX.md`'s own change sites never named it, and the PERMANENT
  regression test (`test_committed_fixture_replays_without_crashing`)
  already replays the real fixture correctly with the right setup,
  superseding the scratch script as the authoritative proof. Left as
  informational residue, not a follow-up prompt — the scratch script's
  job was to prove the diagnosis before any fix existed, which it did;
  it is not owed further maintenance.
- The "genuinely still-open atomic child refuses typed" branch this
  fix adds (`recover_nonconjecture_admission`'s new
  `raise NonConjectureRecoveryAuthorityError(...)` arm) is proven only
  by the synthetic regression test
  (`test_still_open_atomic_child_refuses_with_one_consistent_typed_reason`)
  — no live or historical root has ever exhibited this narrower case
  (FIX.md's own "Explicitly not changed" section states this plainly:
  no still-open atomic child has been observed in the record). If a
  future live run reaches it, that is new evidence for a follow-on
  tranche to build real atomic-resume support against, not something
  this tranche claims to have proven live.
- Rungs L2-L4 of `docs/proposals/RECORD_LIFECYCLE_DEFECT_PLAN.md`
  (budget-stop-invalid-record design, seat bindings in run identity,
  the dead coder seat) remain untouched, as scoped — separate
  tranches.
- The pre-existing `P1/P3` module-fingerprints double-stamp failure
  stays parked, per the task's explicit instruction — unrelated to
  this fix, already tracked independently across five prior tranches.

## Verdict: PASS
