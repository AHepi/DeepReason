# Results — continue must never crash on a resumable record (Rung L1)

## 2026-08-08 — the crash-recovery sweep misrouted a resolved atomic criticism child, not (only) a pending one

**What was observed.** `deepreason --root <root> continue` crashed
`NonConjectureRecoveryAuthorityError("unknown critic task")` on the
committed S6 fixture (`experiments/2026-08-08-live-two-seat-ab-s6/
home-s6/runs/failed-epoch1-run-8c77c6588485304d1f73416318c62949`),
terminalizing the run `state="failed"`/`stop_reason=
"operational_failure"` — S6's own `PARKED.md` P3. The same root then
made `tests/test_continuation.py::
test_a_stop_with_no_typed_receipt_refuses_continuation` fail
(D1's `PARKED.md` P2), refused `CONTINUE_RESUME_RECOVERY_MISMATCH`
where the test expected `CONTINUE_TYPED_STOP_REQUIRED`.

**What the record showed, and how it changed the diagnosis.** P3's own
hypothesis was that an atomic decomposition child was still IN FLIGHT
when the run stopped. The fixture's own replayed state refuted the
narrower reading directly: the ONE recorded decomposition
(`contract_decomposition_activated`/`_completed`, seqs 47/64) was
FULLY resolved — both children `terminal_status: "completed"`. The
crash still fired. Tracing `Scheduler._recover_workflow_prefixes`
(its `admitted_effect_candidates` sweep, called as `Scheduler.run`'s
own first action on every `continue`) showed why: it re-checks EVERY
admitted `CRITICISM`/`SCRATCH_AUTHORING` work item, without reading
`item.terminal` at all, and routes anything not `CONJECTURE` through
`recover_nonconjecture_admission`, which for `CRITICISM` always calls
`_criticism_contract` — a handler built ONLY for the batch payload
shape (`"criticism.semantic-task.v1"`). An atomic child's own shape
(`"contract-decomposition-child.v1"`) fails that handler's first
check, regardless of whether the child is done or still open. The
mechanism is broader than P3 first read it, confirmed two independent
ways before any fix: replaying the real fixture with today's code
(no crash-fix, no code change — deterministic from the frozen log),
and a from-scratch synthetic root built through the harness's own real
`activate_contract_decomposition` seams (an earlier, simpler draft
that skipped that seam was correctly refused by the harness's own
write-time validator — a finding worth recording on its own: the
harness's atomic-child provenance checks are already strict and
correct; the gap was entirely in the crash-recovery DISPATCH layer,
which never reads them).

**What was built.** One new branch in `recover_nonconjecture_
admission` (`workflow/nonconjecture_recovery.py`), ~18 lines: before
ever reaching `_criticism_contract`, recognize an atomic-child payload.
Already-terminal → return the existing admission untouched (nothing to
recover — the effect and its closing record are already durable).
Genuinely still-open → refuse with one new, consistent, actionable
message instead of the old, misleading "unknown critic task". Chosen
over building full atomic-resume support through the crash-recovery
sweep (reconstructing the right wire contract/alias table/effect
application outside their normal live call site) because no still-open
atomic child has ever been observed in the record — GOAL.md's own
success criterion treats a clean typed refusal as an equally valid
outcome to full resume, and the smaller, evidence-backed fix was
preferred; a live occurrence of the still-open case is new evidence
for a follow-on tranche, not something to build speculatively now.

`tests/test_continuation.py`'s witness-selection was narrowed by 8
lines to exclude a root that already carries a continuation receipt
(a cheap file check on `continuations.jsonl`, consistent with the
function's own existing cost discipline) — such a root is testing
`prepare_continuation`'s "already resumed" branch, not the "no typed
receipt" branch the test's own name targets. Measured directly before
changing it: 6 committed roots carry a non-resumable stop reason;
only the S6 fixture carries a receipt. Excluding it leaves 5
witnesses, well above the test's own `assert witnesses` floor of 1.

**The size the plan underestimated, and how it was resolved.** The
new permanent regression test (`tests/test_l1_continue_resumable_
crash.py`) needed the SAME real `activate_contract_decomposition`
construction the diagnosis surfaced — no shortcut passes the harness's
own validator — so it landed at 290 lines against a planned 150-180.
Total diff 352 lines against `FIX.md`'s own pre-implementation
estimate of ~190-220. Raised to the operator as a priced stop (accept
as-is / drop the real-fixture-replay test / merge the two synthetic
tests); accepted as-is, ledgered as `FIX.md` Amendment 1 with the
corrected 352-line ceiling — the overage was entirely in test-setup
fidelity the diagnosis itself had already shown was necessary, not
scope creep.

**Instruments.** Full gate: 3385 passed, 1 failed net of the named
pre-existing `P1/P3`
(`tests/test_module_fingerprints.py::
test_absence_is_valid_before_the_feature_and_presence_valid_after`) —
0 failed net of it. `docs_verify`: 53 documents, 840 checks, 0 failed;
`--audit` 0 findings. (One same-day full-gate run showed 4 additional
failures while running concurrently with an unrelated background
`docs_verify` job — all background-thread MCP/bridge tests with short
`.join()` timeouts, unrelated to this fix's subsystem; re-run in
isolation and in a clean full gate afterward, all passed — CPU
contention from running two heavy jobs at once, not a regression,
recorded rather than quietly re-run past.)

**The residue.**

- The tranche's own scratch reproduction script
  (`repro_fixture_replay.py`) was never updated with the
  `stop_controller` construction the permanent regression test needed
  to add — it now fails one step further than before (a setup gap in
  the script itself), superseded by the permanent test as the
  authoritative proof. Not owed further maintenance.
- The "genuinely still-open atomic child" refusal branch is proven
  only synthetically; no live or historical root has exhibited it.
- Rungs L2 (budget stop stranding an invalid record), L3 (seat
  bindings in run identity), L4 (the dead coder seat) remain
  untouched — separate tranches, per
  `docs/proposals/RECORD_LIFECYCLE_DEFECT_PLAN.md`.
- `P1/P3` (module-fingerprints double-stamp) stays parked, unrelated,
  already tracked independently across five prior tranches.

Accepted does not mean true: what is established is that the specific
crash reproduced twice offline no longer occurs, on the real fixture
and on a constructed root exercising the same mechanism, and that
`test_a_stop_with_no_typed_receipt_refuses_continuation` passes again
for a reason argued in writing (a narrower witness population), not a
weakened assertion. Nothing here proves the still-open-atomic-child
refusal branch against a real run, and nothing here touches Rungs
L2-L4 of the same defect program.
