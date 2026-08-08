# Fix: recover_nonconjecture_admission recognizes an atomic criticism decomposition child before it ever reaches the batch-only handler

Guarantee restored: crash-recovery re-checks of criticism work never
route an ATOMIC decomposition child through the handler built for the
BATCH payload shape — an already-resolved atomic child is a clean
no-op (nothing to recover), and a genuinely still-open one refuses
with one consistent, actionable typed reason, never a crash.

## Change sites (exhaustive)

- `src/deepreason/workflow/nonconjecture_recovery.py`, inside
  `recover_nonconjecture_admission`, immediately after the existing
  `if existing_admission is not None and existing_admission.outcome !=
  "admitted": return existing_admission` early-return (currently lines
  1000-1001) and BEFORE `raw_bytes = _raw_bytes(...)` (currently line
  1002) — insert one new branch, ~18 lines:

  ```python
  if (
      preparation.task_kind == WorkflowTaskKind.CRITICISM
      and hasattr(payload, "get")
      and payload.get("schema") == "contract-decomposition-child.v1"
  ):
      # An atomic child of a criticism decomposition
      # (rules/crit.py's execute_atomic_transition). _criticism_contract
      # below is built only for the BATCH payload shape
      # ("criticism.semantic-task.v1") and misroutes this. An
      # already-terminal child needs no recovery action; a still-open
      # one has no supported resume path here, so it refuses typed
      # instead of crashing on the wrong authority check.
      # (Rung L1: S6 PARKED P3, D1 PARKED P2.)
      if item.terminal is not None:
          _authority(
              existing_admission is not None,
              "atomic child has no durable admission",
          )
          return existing_admission
      raise NonConjectureRecoveryAuthorityError(
          "atomic criticism decomposition child recovery is not "
          "supported by this dispatch; retire this root and "
          "re-attempt the criticism batch fresh"
      )
  ```

  `WorkflowTaskKind` and `NonConjectureRecoveryAuthorityError` are
  already imported/defined in this file; no new imports.

- `tests/test_continuation.py`, `_non_resumable_committed_roots`
  (currently lines 94-121) — exclude a root that already carries a
  continuation receipt (a CHEAP file check, consistent with the
  function's own documented cost discipline — it already avoids
  opening a Harness for exactly this reason), ~8 lines:

  ```python
  continuations = root / "continuations.jsonl"
  if continuations.exists() and continuations.stat().st_size > 0:
      # Already resumed once: prepare_continuation takes its
      # "already resumed" branch for this root
      # (CONTINUE_RESUME_RECOVERY_MISMATCH / re-authorization), not
      # the CONTINUE_TYPED_STOP_REQUIRED branch this test targets.
      # Rung L1 (2026-08-08): S6's own crash-reproduction fixture is
      # exactly this case.
      continue
  ```
  inserted into the existing `for root in roots:` loop, before
  `witnesses.append((root, reason))`.

- `docs/map/SUB-workflow.md` — one new `Traps` entry naming this
  mechanism (the map moves in the same commit as the code, per
  CLAUDE.md), ~15-20 lines, with a `check:` line pinning the new
  branch's presence and the specific message.

- NEW `tests/test_l1_continue_resumable_crash.py` — the permanent
  regression artifact GOAL.md's own success criterion names, covering
  (reusing `test_v6_nonconjecture_recovery.py`'s `_manifest`/`_config`/
  `_lease`/`_provider_prefix` helpers, per that file's own established
  pattern):
  1. an already-terminal atomic criticism child recovers as a clean
     no-op (adapts this tranche's own `repro_synthetic_atomic_child.py`
     into a permanent `pytest` test — same construction, asserts
     `recover_nonconjecture_admission` returns the existing admission
     and appends no new log events, mirroring `_recover`'s own
     no-redispatch assertion style in `test_v6_nonconjecture_
     recovery.py`);
  2. a genuinely still-open atomic criticism child (admission
     recorded, `terminal` left `None`) raises the NEW, single,
     consistent message — never the old `"unknown critic task"`;
  3. the real fixture, copied to `tmp_path`, replays through
     `Scheduler.run(0)` cleanly (adapts `repro_fixture_replay.py`),
     proving the exact reproduced defect is gone on the actual
     committed record, not only a synthetic construction.
  Estimated ~150-180 lines (three scenarios, each needing its own
  harness/manifest setup, even with helper reuse).

## Regression artifact

This tranche's own `repro_fixture_replay.py` and
`repro_synthetic_atomic_child.py` (REPRO.md) must both invert:
- `repro_fixture_replay.py <scratch-copy>` must print "NO CRASH --
  recovery completed cleanly" (the fixture's one decomposition is
  fully resolved, so this is the already-terminal no-op path).
- `repro_synthetic_atomic_child.py`, run UNMODIFIED, must also print
  "NO CRASH -- recovery completed cleanly" (same reason: it builds an
  already-terminal atomic child).
- A NEW condition this fix must also be tested against, not covered by
  either existing repro artifact: a genuinely still-open (admitted,
  not yet terminal) atomic child must raise the new refusal message
  exactly once, consistently — this is `tests/test_l1_continue_
  resumable_crash.py`'s own scenario 2, since neither repro artifact
  happens to construct that narrower case (both fixtures — the real
  one and the synthetic one — have their one decomposition fully
  resolved).

## Existing tests at risk

- `grep -rn "unknown critic task" tests/` -> no hits. No existing test
  asserts on the message this fix's new branch intercepts before
  `_criticism_contract` would raise it.
- `grep -rn "contract-decomposition-child" tests/test_v6_nonconjecture_recovery.py`
  -> no hits. No existing test exercises
  `recover_nonconjecture_admission` with an atomic-child payload at
  all, so nothing currently depends on the crash as intended
  behavior.
- `test_mismatched_rendered_request_fails_before_recovery_append` and
  `test_authority_mismatch_fails_closed_before_recovery_append`
  (`tests/test_v6_nonconjecture_recovery.py:1184,1266`) both use
  `_criticism_prefix`, which builds a genuine BATCH-shape payload
  (`schema == "criticism.semantic-task.v1"`) — my new branch's
  condition (`schema == "contract-decomposition-child.v1"`) never
  matches their fixtures, so both keep passing unchanged, exercising
  the SAME `_criticism_contract` path they always have.
- `tests/test_continuation.py::
  test_a_stop_with_no_typed_receipt_refuses_continuation` — measured
  directly (see below): 6 committed roots currently carry a
  non-resumable stop reason; only the S6 fixture (this tranche's own
  root) carries a continuation receipt. Excluding it leaves 5
  witnesses, well above the test's own `assert witnesses` floor of 1 —
  this test's population narrows from 6 to 5, does not empty.
- `docs_verify --coverage`/`--audit` — unaffected; no seam document is
  touched by this fix's own change sites (only `SUB-workflow.md`,
  which is the owning subsystem document, not a seam).

## Explicitly not changed

- `atomic_recovery.recover_atomic_child_output` and its live caller
  (`rules/crit.py`'s `execute_atomic_transition`) — the ordinary LIVE
  dispatch path already correctly recognizes and resumes an atomic
  child; this fix touches only the CRASH-RECOVERY sweep's own
  dispatch, which never reaches that path today.
- Building a full "resume the still-open atomic child and complete the
  decomposition" path (calling `atomic_recovery.recover_atomic_child_
  output` plus whatever caller-owned effect-application `rules/crit.py`
  would normally run) — GOAL.md's own success criterion explicitly
  allows "refuses with a typed, actionable reason" as an equal
  alternative to full resume, and building genuine atomic resume
  support through the crash-recovery sweep (reconstructing the right
  `AtomicCriticWireContractV1`/alias table/effect-application call
  outside its normal live call site) is materially larger, riskier,
  and unevidenced by either reproduction — no still-open atomic child
  has actually been observed in the record. If a future live run hits
  the "still-open" refusal in practice, that is new evidence for a
  follow-on tranche to build real resume support against, not
  something to build speculatively now.
- `scheduler.py`'s `_recover_workflow_prefixes` sweep itself (the
  `admitted_effect_candidates` filter) — an earlier draft of this fix
  considered adding an `item.terminal is None` guard there instead.
  Rejected: `recover_incomplete()` (line 341) is a SECOND, independent
  source feeding the same dispatch loop, and a sweep-level-only guard
  would leave that path's atomic children unprotected. Fixing inside
  `recover_nonconjecture_admission` itself covers both sources with
  one change, since both dispatch through it.
- `PARKED P1`/`P2` from S6's own `PARKED.md` (dead coder seat;
  run-identity omits seat bindings) and Rungs L2-L4 of the same defect
  program — separate, unrelated tranches (GOAL.md's own NOT-in-scope
  list).
- The pre-existing `P1/P3` module-fingerprints double-stamp failure —
  out of scope per the task's explicit instruction; stays parked.

## Frozen-surface contact forecast

None. `workflow/nonconjecture_recovery.py` and `tests/test_
continuation.py` are not among the five frozen surfaces
(`capabilities/state.py`, `harness.py` event application,
replay-validation record formats, manifest schemas+validators,
qualification subject digests) or the frozen-adjacent
`route_fingerprint`. Confirmed by construction: this fix reads
existing durable records (`item.terminal`, `existing_admission`) and
returns/raises based on them — it writes no new record shape, appends
no new event type, and does not touch `harness.py` at all.

## Estimated diff

~26 lines in the two production/test change sites above (18 +
`nonconjecture_recovery.py`, 8 `test_continuation.py`), plus the map
Traps entry (~15-20 lines) and the new regression test file
(~150-180 lines) GOAL.md's own success criterion names — **total
estimate ~190-220 lines across 4 files**, modestly over the nominal
150-line guideline. The fix ITSELF (the two production/test change
sites) is ~26 lines; the overage is entirely in the regression test
file's own thoroughness (three scenarios: already-resolved no-op,
still-open typed refusal, and the real fixture replayed end-to-end)
and the map documentation this fix owes. Per this tranche's own task
instruction, execution stops here regardless — `dr-implement-fix`
does not run until this design is reviewed and approved.
