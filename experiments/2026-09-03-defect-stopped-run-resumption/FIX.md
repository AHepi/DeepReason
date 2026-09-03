# Fix: refuse the STOPPED receipt on unread provider authority, not on outstanding work — and let a failure terminal take the same receipt

Guarantee restored, in one sentence:

> **A stop refuses its lifecycle receipt if and only if it would close over a
> provider call whose result nobody has read; every other terminal — clean,
> failed, or finalized after a kill — takes the SAME receipt carrying its own
> stop reason, and whether that root may actually be continued is decided,
> as it already is, by the SECURITY-channel integrity gate at `continue`/
> `amend` time.**

The receipt records that the run reached a terminal. The gate decides whether
that terminal may be resumed. Those are two different questions and the defect
was one answering the other.

## What "unfinished workflow authority" protects, and how this preserves it

The window instruction requires this to be stated before any edit, so it is
stated first.

`outstanding_work_snapshot` (`workflow/lifecycle.py:58-149`) computes two
things about a stop, and the refusal at `:236` currently fires on either:

1. `outstanding_work` — every work order not yet FINISHED or ABANDONED,
   including transactional work whose provider call COMPLETED and was already
   consumed by replay, awaiting only semantic admission.
2. `unconsumed_bound_call_seqs` — provider calls bound to a work order for
   which no `ProposalReceipt` exists. **This is a provider call whose result
   nobody has read.**

Only (2) is a safety property. Closing a stop over an unread provider call
means resumption must either re-issue it — spending the tokens twice and
recording two calls for one authority — or drop a result the record already
holds. Either outcome corrupts the accounting the whole record exists to make
auditable. (2) is also COMPLETE by construction, not by luck: the same
function raises `"unconsumed provider call is not represented as outstanding
work"` (`:136-138`) unless the orphaned-call set equals the represented set,
so `unconsumed_bound_call_seqs` is the whole inventory of unread provider
authority. **The fix keeps refusal (2) exactly as it is, at all five sites.**

(1) is not a safety property; it is a work-in-progress fact, and the system
already owns a designated remedy for it. `Scheduler._recover_workflow_prefixes`
(`scheduler/scheduler.py:429-499`) runs BEFORE the first cycle of any
scheduler — including a resumed one — routes each result-bearing outstanding
item through `recover_conjecture_admission` or `recover_nonconjecture_admission`
by task kind, and then asserts its own completeness:

    if self.harness.workflow_state.outstanding_work_order_ids:
        raise RuntimeError("transaction recovery left unfinished authority")

So outstanding work is RECORDED in the snapshot (unchanged — the snapshot's
content and identity are untouched) and RE-ENTERED typed on resume by
machinery that already exists and already fails loudly rather than silently.
That is precisely the window instruction's "recorded as outstanding and
re-entered or abandoned typed on resume — they must not veto the receipt."

Measured, not asserted: across the four committed roots and all three stub
shapes, `unconsumed_bound_call_seqs` is EMPTY on every single one, while
`outstanding_work` is 6 / 10 / 2 / 6 and 31 / 3 / 11. The refusal has never
once fired for the reason it exists (`proof/outstanding_census.py`,
`proof/RED_three_shapes.txt`).

And the existing gate tests prove the protection survives: the shared
`_OutstandingReplay` fixture (`tests/test_workflow_stop_lifecycle_c4.py:152`)
carries call seq 7 with no receipt, so its
`unconsumed_bound_call_seqs == (7,)`. Both tests that assert the refusal fires
must keep passing UNCHANGED after this fix. They are the regression that the
narrowing is a narrowing and not a removal.

## Frozen-surface forecast (made before the first edit, as required)

**No frozen surface is touched.** Checked path by path against
`docs/map/INV-frozen-surfaces.md`:

| path | status |
|---|---|
| `capabilities/state.py` | not touched |
| `harness.py` | not touched |
| `invariants.py` | not touched — its only reference to outstanding work (`:4179`) is a STATS field in the replay report, `"outstanding_work_orders"`, which raises nothing |
| `verification/` | not touched |
| `run_manifest.py` | not touched |
| `qualification.py` | not touched |
| `llm/firewall.py` `route_fingerprint` | not touched |

`workflow/replay.py` IS touched and is deliberately named here, because it is
the workflow control plane's event application and reads adjacent to frozen
surface 2. It is not that surface: surface 2 is `harness.py`'s event
application, and `replay.py` is owned by `DR-SUB-workflow`, which is not
frozen. Two claims about it, both testable and both in the regression set:

- **No record FORMAT changes.** `WorkflowLifecycleSnapshotV1` gains no field
  and loses none; `outstanding_work` was always part of it and is already
  populated. What changes is only that a snapshot carrying entries is now
  ACCEPTED where it was refused. This is a new instance of an existing
  format, not a new format — so it is not the PRICED STOP the window
  reserves for one.
- **No historical root replays differently.** The builder refused to WRITE a
  STOPPED snapshot with outstanding work, so no committed root contains an
  event that exercises the narrowed branch. Removing a raise that no
  historical event reaches cannot change any historical replay. The
  `SUB-workflow` Traps warning about the replay digest concerns adding
  unconditional KEYS to `WorkflowReplayState.digest`; no key is added.

## Change sites (exhaustive)

**A. `src/deepreason/workflow/lifecycle.py`** — the predicate, and the reasons.

- `:28` `RESUMABLE_STOP_REASONS` gains `"operational_failure"`. The operator's
  2026-08-29 law makes every terminal continuable; the 2026-07-27 owner
  comment beside it ("Failure terminals stay non-resumable") is SUPERSEDED and
  is rewritten to say so rather than deleted.
- `:28` gains a sibling constant `COMPOSABLE_STOP_REASONS =
  frozenset({"converged", "budget_exhausted"})` — the OLD value, under its own
  name, for the bridge's post-terminal composition admission. Splitting the
  two keeps bridge semantics byte-identical: widening resumption is this
  tranche's mandate, widening what may be COMPOSED from a failed terminal is
  not, and one frozenset serving two questions is how it would have happened
  silently.
- `:152` `_is_runtime_exhaustion` → `_is_runtime_decided`, widened to
  `{"budget_exhausted", "operational_failure"}` with `escape_action is None`.
  Both are decided by the runtime, not by `StopController`, so neither has a
  controller evaluation to replay and both must declare unchanged controller
  state. The existing exhaustion comment is extended, not replaced.
- `:236` `if snapshot.outstanding_work or snapshot.unconsumed_bound_call_seqs:`
  → `if snapshot.unconsumed_bound_call_seqs:`
- `:317` and `:330` — the two symmetric refusals in `build_resumed_lifecycle`
  (`"terminal checkpoint contains unfinished provider work"` and
  `"RESUMED refuses unfinished workflow authority"`) narrowed identically. A
  stop that may be taken over outstanding work must be resumable over it, or
  the fix produces roots that terminate and then refuse one layer later.
- `__all__` gains `COMPOSABLE_STOP_REASONS`.

**B. `src/deepreason/workflow/replay.py`** — the apply side of the same two
transitions. These MUST move with A or the receipt is built and then rejected
when replayed.

- `:2151` `"STOPPED cannot forget unfinished workflow authority"` narrowed to
  `unconsumed_bound_call_seqs`.
- `:2275` `"RESUMED cannot forget unfinished workflow authority"` likewise.
- `:2154` and `:2198` import `_is_runtime_exhaustion` / `RESUMABLE_STOP_REASONS`;
  the first follows the rename, the second is unchanged.
- `:1121` `_post_terminal_composition_call` switches from
  `RESUMABLE_STOP_REASONS` to `COMPOSABLE_STOP_REASONS` — the change that
  makes bridge admission provably unchanged.

**C. `src/deepreason/application/text_runs.py`** — one run path for the receipt.

- `:233` `_record_exhaustion_lifecycle_stop` → `_record_lifecycle_stop`, taking
  the stop `reason` as a parameter instead of hardcoding `"budget_exhausted"`
  at `:288` and `:302`. Its docstring is rewritten: the P6 note it carries
  ("Whether unfinished authority OUGHT to block continuation is a separate,
  open question") is now ANSWERED by the operator, and the docstring says so
  and cites the law rather than leaving a stale open question in the tree.
- `:1618-1660` the failure terminal calls `_record_lifecycle_stop(...,
  reason="operational_failure")` and keeps the existing bare-stop write as its
  `if stop is None:` fallback — structurally identical to the clean path at
  `:405-432`. `TERMINAL_LIFECYCLE_NOT_TAKEN_FAILURE_TERMINAL` and the comment
  declaring 16 roots stand that way are removed: the terminal no longer
  declines the receipt, so a refusal claiming it did would be false. Any
  refusal the builder DOES return is recorded exactly as the clean path
  records it.
**C-amendment (added during dr-implement-fix, 2026-09-03).** Renaming
`_record_exhaustion_lifecycle_stop` has ONE caller outside `src/` that the
change-site list missed:

- `tests/test_lifecycle_operation_parity.py:355,370`
  `test_finalize_resumes_after_an_interrupted_terminalization` imports the
  helper by name to construct the exact state an interrupted `finalize` left
  (grounded-extension root, 2026-08-13). It follows the rename and gains the
  new required `reason="budget_exhausted"` argument — which is the value it
  was already getting implicitly, so the state it builds is unchanged and its
  assertions are untouched. This is rename follow-through, not a fixture
  weakened to obtain green: the test still asserts `refusal is None`, still
  asserts no second stop event is recorded, and still asserts
  `current_valid_committed`.

Recorded as an amendment rather than applied silently, per `dr-implement-fix`
step 1: a change site discovered during implementation stops and amends this
document before the edit lands.

- `finalize_stopped_root` (`:583`) emits one progress line after
  `terminalize_text_run` returns. Without it a finalized root keeps
  `state: running` in `run-status.json` — reproduced on the stub and matching
  live P-A2 epoch 4 exactly — which makes `stop-report` section 5 answer
  `continue: UNKNOWN` about a root that is now resumable. This is inside the
  goal's "must report the truth after the fix" and is 5 lines; it is named as
  a separable site so it can be reverted alone if the gate disputes it.

Nothing in `runtime/continuation.py` changes. That is deliberate and is the
design's centre: the gate stays exactly as the jailbreak tranche left it.

## Regression artifact

Must INVERT (currently RED, listed in REPRO.md):

    python experiments/2026-09-03-defect-stopped-run-resumption/proof/three_shapes.py --workdir <dir>
    # all three shapes: record_verification_refusal None, continue rc=0,
    # cycle after > cycle before

Must be UNCHANGED, character for character (the control):

    python experiments/2026-09-03-defect-stopped-run-resumption/proof/mutate_one_byte.py <root> <copy>
    # CONTINUE_RECORD_NOT_VERIFIED: ... attempt-route, frozen-route

New gate-speed regressions, in `tests/test_stopped_run_resumption.py`:

1. A snapshot with outstanding work and ZERO unconsumed calls no longer
   refuses the receipt — the shape every real root has.
2. A snapshot with an unconsumed bound call STILL refuses, typed, with its
   counts — the protection, pinned separately from the narrowing.
3. Symmetry: whatever `build_stopped_lifecycle` accepts,
   `build_resumed_lifecycle` and both `replay.py` apply-side guards accept —
   asserted as one property, so the five sites cannot drift apart.
4. A failure terminal records NO `terminal_lifecycle_refusal` and DOES carry a
   `terminal_lifecycle_decision` whose reason is `operational_failure`.
5. **The two-record agreement fixture the goal requires**: on one root,
   `run-status.json`'s `terminal_lifecycle_refusal` and `results_summary`'s
   `stop_reason_resumable` / `continuation_authority` must describe the same
   root consistently — the test fails if a root reports resumable while
   authority is absent.
6. `COMPOSABLE_STOP_REASONS` still excludes `operational_failure`, so the
   bridge's post-terminal admission is unchanged by the widening.

Declared limit of the stub, stated so a partial GREEN is not read as a full
one: all outstanding items on all three stub shapes are result-bearing
(`outcome=provider_result`), so the stub cannot exercise the ISSUED-with-no-
attempt item that P-A2 epoch 4 carries and that `recover_incomplete` cannot
close. Regression 7 covers it at unit level — a snapshot carrying such an item
takes the receipt (it holds no unread result) — but that resume ACTUALLY
completes on such a root is NOT demonstrated by this tranche. It is recorded
in VERIFY.md as residue, not claimed.

## Existing tests at risk

From grep, named individually with a verdict each:

- `tests/test_workflow_stop_lifecycle_c4.py::test_terminal_builder_snapshots_then_refuses_unfinished_provider_work`
  — **must keep passing unchanged.** Its `_OutstandingReplay` has call seq 7
  unconsumed, so it trips the disjunct being KEPT.
- `tests/test_terminal_lifecycle_refusal_is_recorded.py::test_the_stopped_refusal_is_typed_and_carries_the_counts_that_caused_it`
  — **must keep passing unchanged.** Same fixture, same reason.
- `tests/test_terminal_lifecycle_refusal_is_recorded.py` (remaining three
  tests) — **must keep passing unchanged.** They INJECT the refusal by
  monkeypatch, so they test the caller's handling, which is preserved: a
  returned refusal is still recorded and still reported.
- `tests/test_workflow_resume_lifecycle_c4.py::test_completed_typed_terminal_is_not_continuation_authority`
  — **must keep passing unchanged.** Its reason is `completed`, which stays
  outside `RESUMABLE_STOP_REASONS`.
- `tests/test_bridge_after_typed_stop.py` (all three) — **must keep passing
  unchanged**, and change B `:1121` is what guarantees it. The
  non-resumable case uses `reason="repair_exhausted"`, outside both sets.
- `tests/test_jailbreak_gate.py` (all) — **must keep passing unchanged.** No
  gate predicate is touched.
- `docs/map/SUB-workflow.md` carries
  `check: grep -q 'RESUMABLE_STOP_REASONS = frozenset({"converged",
  "budget_exhausted"})' ...` — this check WILL fail, correctly, because the
  literal changes. The map moves in the SAME commit: that Traps entry is
  rewritten to state the widening and its date, and its check re-derived.

No fixture is weakened and no assertion is loosened to obtain green. If any
test above goes red, that is a design error to route back through
dr-diagnose, not a fixture to update.

## Explicitly not changed

- **`runtime/continuation.py` and `amendment/apply.py`** — the integrity gate.
  Not one predicate moves. **Stated exposure**, per the window instruction:
  this fix WIDENS EXPOSURE to the jailbreak tranche's parked P2 ("a record too
  corrupt to replay passes the gate",
  `experiments/2026-08-31-defect-jailbreak-gate-closure/`), because roads that
  were closed for lifecycle reasons now reach the gate and the gate becomes
  the sole guard on them. The residue is not enlarged — the same records pass
  and fail as before — but more traffic meets it. That is the correct
  architecture under the operator's own clause (the receipt never authorizes
  continuation; the gate does) and it is recorded rather than left implicit.
  Parked as P3 with the owner named.
- **Seat-level degradation** (`llm/adapter.py:524`) — the mechanism that
  KILLED P-A1. Out of scope by the window instruction; parked as P1.
- **`operator_cancelled` stays non-resumable.** A cancellation is a decision,
  not an interruption; making it resumable was not asked for and would need
  its own operator ruling.
- **The 16 committed roots, P-A1 and P-A2 are NOT rewritten** and gain nothing
  retroactively. Old roots owe the future nothing (2026-08-14). Every
  reproduction here is a fresh stub root.

## Estimated diff

Production code: ~95 lines across 3 files (`lifecycle.py` ~35,
`replay.py` ~12, `text_runs.py` ~48). Under the 150-line budget.
Tests and map documents are additional and are not counted against it.

## Approval gate

GOAL.md classes this `defect`; the estimate is under 150 lines; no frozen
surface is touched; no new record format or event kind is introduced; no
jailbreak-gate predicate moves. Per `dr-propose-fix`, this proceeds to
`dr-implement-fix` without an operator stop.
