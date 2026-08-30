# PARKED — checkpoint hardening (lane A, batch 2)

Written at park time, per the batch rule that a parked STOP is pushed the
moment it is parked. Each entry is one line of WHAT, then a prompt the
operator can paste whole into a fresh executor window.

Nothing here was decided by this tranche. F1 is an operator call; F2, F3 and
F5 are out of this lane's cone; F4 needs a written frozen-surface grant; F6
and F7 are pre-existing findings this tranche deliberately did not widen into.

---

## F1 — OPERATOR CALL: does "every terminal must leave checkpoints sufficient
## for relaunch" mean failure terminals become RESUMABLE?

WHAT: 16 committed roots hold the complete checkpoint file set and cannot be
continued, by an owner decision of 2026-07-27 whose comment reads "Failure
terminals stay non-resumable". The 2026-08-29 law is readable as overturning
that. Lane A read it the narrow way (record the uncontinuability, do not widen
the resumable set) and says so in SPEC.md assumption A1.

```
Route: dr-change-orchestrator, starting at dr-capture-request.

One goal: decide, and then implement, what the operator's 2026-08-29 law
("EVERY terminal -- clean or failed -- must leave checkpoints sufficient for
relaunch") requires of FAILURE terminals, and record the decision where the
next reader will find it.

The fork, stated so the operator can answer in one sentence:
  (a) the FILES must be there, and they are -- so nothing further is owed
      beyond recording, typed, that such a terminal cannot be continued
      (this is what experiments/2026-08-30-change-checkpoint-hardening
      shipped, as assumption A1);
  (b) "sufficient for relaunch" is literal -- a failure terminal must become
      continuable, which means widening RESUMABLE_STOP_REASONS in
      src/deepreason/workflow/lifecycle.py and giving failure terminals a
      STOPPED lifecycle receipt.

Evidence, all re-derivable:
- src/deepreason/workflow/lifecycle.py, the RESUMABLE_STOP_REASONS block --
  owner decision 4a (2026-07-27), "Failure terminals stay non-resumable."
- experiments/2026-08-30-change-checkpoint-hardening/proof/census.json:
  16 roots at (failed, operational_failure), 15 of them with no continuation
  authority at all; population 59.
- experiments/2026-08-30-change-checkpoint-hardening/SPEC.md, the
  four-population table and assumption A1.
- CLAUDE.md, the 2026-08-29 law, verbatim.

End state: REQUEST.md carrying the operator's answer verbatim; if (b), a
delivered change widening the resumable set WITH the receipt that makes it
mean something, and the 2026-07-27 comment rewritten rather than deleted; if
(a), the decision ledgered in CLAUDE.md and in docs/map/SUB-workflow.md so no
later tranche re-opens it.
```

---

## F2 — OUT OF CONE: limb one's unshipped half. WorkBudgetDenied still
## terminates as operational_failure.

WHAT: the operator's law says a budget denial on an exhausted budget must
terminate `budget_exhausted`, never `operational_failure`. Token-METER
exhaustion already does. RESERVATION denial does not, and two committed roots
prove it at HEAD.

```
Route: deepreason-orchestrator, starting at dr-set-goal.

One goal: make a run whose token budget denies a work reservation terminate as
a clean, continuable budget_exhausted stop instead of an operational_failure,
per the operator's 2026-08-29 law.

Evidence, verified 2026-08-30:
- experiments/2026-08-24-change-rung7-wounds-falls-succession/run --
  run-status.json state "failed", stop_reason "operational_failure";
  run-result.json error_type "WorkBudgetDenied".
- experiments/2026-08-22-change-epoch3-second-lineage/failed-attempt2-run-bb045538... --
  identical shape.
- src/deepreason/workflow/transaction.py, class WorkBudgetDenied: "Raised
  after a durable ``budget_denied`` terminal was appended." The denial is
  raised AFTER a durable typed terminal exists, which is why the clean-stop
  reading is the one the record supports.
- src/deepreason/scheduler/scheduler.py, Scheduler.run's except clauses:
  TokenBudgetExceeded is caught and becomes a logged stop; WorkBudgetDenied is
  not among them.
- experiments/2026-08-28-fix-swallowed-terminal-lifecycle-refusal/P2_OPERATOR_DECISION.md
  prices both roads already.

Cone needed: src/deepreason/scheduler/, src/deepreason/workflow/,
src/deepreason/application/text_runs.py, tests, docs/map.
NOT in cone: any frozen surface.

End state: a run that hits a reservation denial reaches stop_reason
budget_exhausted with a typed STOPPED lifecycle receipt, a regression test
naming the two roots above in its docstring, and the map moved in the same
commit.
```

---

## F3 — OUT OF CONE: a second corrupted-stop path, one layer down in the
## scheduler.

WHAT: `Scheduler._record_stop` calls `build_stopped_lifecycle` with no handler
for `UnfinishedWorkflowAuthorityError`, while `application/text_runs.py`
catches exactly that and records a typed refusal. So a CONTROLLER-decided stop
holding unfinished authority becomes an untyped `operational_failure` — the
same defect P6 fixed on the exhaustion path, never mirrored here.

```
Route: deepreason-orchestrator, starting at dr-set-goal.

One goal: make a controller-decided stop that cannot take a STOPPED lifecycle
receipt record the typed refusal instead of collapsing into an untyped
operational_failure -- the scheduler-side twin of the P6 fix.

Evidence:
- src/deepreason/scheduler/scheduler.py, Scheduler._record_stop: the
  build_stopped_lifecycle call has no except clause.
- src/deepreason/application/text_runs.py, _record_exhaustion_lifecycle_stop:
  "except UnfinishedWorkflowAuthorityError as refused: return None,
  _refusal(...)" -- the shape to mirror.
- src/deepreason/workflow/lifecycle.py, UnfinishedWorkflowAuthorityError, code
  "STOPPED_REFUSES_UNFINISHED_WORKFLOW_AUTHORITY".
- experiments/2026-08-30-change-checkpoint-hardening/SPEC.md items S5/S6,
  which closed the application-layer half only.

Cone needed: src/deepreason/scheduler/, tests, docs/map.

End state: the refusal is on the record, a regression test drives a controller
stop holding unfinished authority, and docs/map/SUB-scheduler.md carries the
Traps entry.
```

---

## F4 — FROZEN SURFACE 3, NOT GRANTED: "unresolved containment-breach
## evidence" has no typed form to gate on.

WHAT: the operator's law gates continuation on a record that "fails replay
validation OR carries unresolved containment-breach evidence". The second
clause names a record type this repo does not have. Lane A scoped its limb
three to replay validity and said so plainly (SPEC.md assumption A4).

```
Route: dr-change-orchestrator, starting at dr-capture-request. This tranche
REQUESTS A FROZEN-SURFACE GRANT IN WRITING BEFORE ANY CODE; the operator has
refused verbal grants on the record.

One goal: decide whether DeepReason should carry a typed containment-breach
record at all, and if so, build it so continue/amend can refuse on it.

What was searched, 2026-08-30, and found absent:
- grep -rn "containment" --include=*.py src/deepreason/  -> 77 hits, every one
  a limit, a timeout, or a free-text "sandbox_abort" trace string
  (verification/simulation.py, verification/runner.py, verification/lean.py,
  v6_policy.py). No event kind. No verify_root check. No receipt field.
- src/deepreason/verification/report.py, _SECURITY_CHECKS: a closed seven-name
  set -- attempt-route, capability-authority, capability-compiled-authority,
  capability-grant, capability-work-order, frozen-route, school-route. None is
  about containment.
- src/deepreason/sandbox_guard.py is a GUARD over untrusted source, not a
  RECORD of a breach.

Why it is a grant request: a typed containment-breach finding must enter
_SECURITY_CHECKS in src/deepreason/verification/report.py, and probably a new
verify_root finding in src/deepreason/invariants.py. Both are frozen surface 3
(docs/map/INV-frozen-surfaces.md section 3). Note the branch tripwire's regex
does NOT cover src/deepreason/verification/, so a green tripwire is not
authorization here.

Alternative the operator may prefer, at zero cost: rule that limb three IS
replay validity, and amend CLAUDE.md's law text to say so. The clause would
then name something real.

End state: either an amended law with no code, or SPEC.md carrying a written
grant with tools/blast_radius.py's own contact rows disposed one by one,
followed by the typed record and the gate.
```

---

## F5 — MAP REPAIR, another lane's territory: INDEX.md cannot route to the
## documents that cover this work.

WHAT: `docs/map/INDEX.md`'s subsystem table omits `SUB-application.md`,
`SUB-amendment.md` and `SUB-periphery.md`, and the seams this work joins
(application x verification, amendment x verification) are undocumented on
both sides. The mandated map preflight therefore cannot be performed as
written; lane A derived routing from each document's own `Owns:` header
instead and recorded the gap.

```
Route: dr-change-orchestrator (map repair), or fold into the batch's map lane.

One goal: make docs/map/INDEX.md route to every map document that exists, so
the mandated preflight reaches the covering document instead of concluding
there is none.

Evidence, measured 2026-08-30:
  $ grep -n -iE "application|amendment|periphery" docs/map/INDEX.md
  46:| `SUB-harness.md` | ... |
  54:| `SUB-bridge.md` | ... |
  129:| — | periphery × verification | `SEAM-periphery-x-verification.md` |
  136:the periphery × verification and calculus × rules cases ...
  $ ls docs/map/ | grep -E "application|amendment|periphery"
  SEAM-periphery-x-verification.md
  SUB-amendment.md
  SUB-application.md
  SUB-periphery.md

Also absent from INDEX.md's tables, per the batch's shared reconnaissance:
CON-problem-layer-lifecycle.md, CON-standing-and-background.md,
INV-signal-contract.md, REC-add-signal.md, REC-revise-allocation-policy.md,
SEAM-schools-x-scheduler.md.

End state: INDEX.md lists every document under docs/map/, with a check that
FAILS when a document exists and is not routed to -- a count, not a floor
(docs/map/SCHEMA.md check-writing rule 6).
```

---

## F6 — PRE-EXISTING READER SEMANTICS: `amend_ready` requires a resumable stop
## reason, and `amend` does not.

WHAT: `results.py` reports `amend_ready: false` for the 16 committed roots
that `amend` actually accepts, because its predicate includes
`stop_reason_resumable` — a CONTINUE precondition that AMEND does not have.
Lane A fixed WHICH VERDICT the reader reads (SPEC.md S7) and deliberately did
not change what the field MEANS.

```
Route: dr-change-orchestrator, starting at dr-capture-request.

One goal: decide whether results.py's `amend_ready` names the AMEND verb's
predicate or a general "ready for the lifecycle" state, and make the reader
and the actors agree either way.

Evidence:
- src/deepreason/application/results.py, _terminal: amend_ready = valid typed
  terminal AND stop_reason_resumable AND continuation_authority.
- src/deepreason/amendment/apply.py, _require_terminal_stop: amend's whole
  terminal precondition; it consults NO stop reason.
- experiments/2026-08-30-change-checkpoint-hardening/proof/census.json:
  16 roots at (failed, operational_failure, amend_ready False) that
  derive_terminal_authority reports current_valid_committed.
- docs/map/SUB-application.md Traps: "when two verbs answer one question, the
  reporting verb reads the ACTING verb's own predicate".

Watch out: tests/test_results_command.py pins the `terminal` block's six keys
with an EXACT-SET assertion, so splitting amend_ready into amend_ready +
continue_ready moves that test. That is a legitimate, predicted fixture change
-- record it in SPEC.md before the edit, and do not relax the assertion to a
subset check.

End state: the reader's readiness fields name their verbs, a test asserts over
committed roots that reader and actor never disagree, and the map moves in the
same commit.
```

---

## F7 — ONE STRANDED COMMITTED ROOT: the operator's "corrupted stop", in the
## flesh, that no verb can touch.

WHAT: one committed root is neither amendable nor finalizable. `amend` refuses
it (`AMEND_NOT_AT_TERMINAL`) and `finalize` refuses it
(`FINALIZE_AUTHORITY_UNAVAILABLE`, which requires `current_open_uncommitted`).
Lane A recorded it by name and did not add a repair verb — that is a new
operation, not a hardening.

```
Route: dr-change-orchestrator, starting at dr-capture-request.

One goal: decide whether DeepReason owes a repair path for a root whose
terminal authority is invalid_incomplete, and if so build it -- WITHOUT ever
editing a committed root's bytes.

The root, re-derived 2026-08-30:
  experiments/live_research_2026-07-29/selfstudy/runs/failed-epoch2-run-9175f0ecb055e57455af3c50df153c5a
    authority_status      invalid_incomplete
    authority_detail_code TERMINAL_REPLAY_VALIDATION_BINDING_INVALID
    stored_replay_valid   true      (its own file says valid; the BINDING does not)
    state / stop_reason   failed / operational_failure

Re-derive it yourself:
  python experiments/2026-08-30-change-checkpoint-hardening/proof/census.py
  then read census.json's "stranded_neither_amend_nor_finalize".

Why finalize refuses: src/deepreason/application/text_runs.py,
finalize_stopped_root raises FINALIZE_AUTHORITY_UNAVAILABLE for any status
other than current_open_uncommitted.

Note the interaction with the 2026-08-29 law: a repair verb that made this
root continuable would need to explain why that is not "a jailbroken run being
continuable". The honest end state may well be "no repair verb; the root is an
artifact of its own version" -- which is a legitimate answer under the
2026-08-14 law that old runs owe the future nothing.

End state: a decision, ledgered; and if a verb, one that appends and never
edits.
```

---

## F8 — DIFF BUDGET EXCEEDED, a stop this lane may not decide for itself

WHAT: `tools/diff_budget.py` reads `EXCEEDED` against the ceiling SPEC.md
declared for this tranche. SPEC.md's own rule says that verdict "is a STOP
decided above this lane, per the batch-1 record", so it is parked here rather
than resolved by trimming. Measured at delivery, against tranche base
`84514a0280f45d29e5066bb3be3d273ba73798db`:

    {"areas": {"src": 103, "tests": 397, "docs/map": 65},
     "total_insertions": 565, "ceiling": 400, "verdict": "EXCEEDED"}

The overshoot is entirely OUTSIDE production code. `src` came in at 103
insertions against a SPEC estimate of 102 — the four source edits landed
almost exactly as designed. `tests` came in at 397 against an estimate of 200,
because SPEC.md budgeted 150 lines for a NEW test module that has to carry six
mutation-proven tests, each selecting its witnesses from committed roots and
each explaining what would make it vacuous. Nothing was trimmed to fit the
number: a test whose comment explaining the mutation is deleted is a test the
next reader cannot maintain, and this repo's recorded failure mode is vacuous
tests, not verbose ones.

```
Route: no workflow. This is a one-line ruling for the monitor or the operator.

DECIDE: does the ultracode diff-budget ceiling apply to TEST and MAP lines, or
only to production `src` lines?

The measurement that forces the question
(experiments/2026-08-30-change-checkpoint-hardening, lane A of batch 2):

    src        103 insertions  (SPEC.md estimated 102)
    tests      397 insertions  (SPEC.md estimated 200)
    docs/map    65 insertions  (SPEC.md estimated  58)
    total      565             ceiling 400  ->  EXCEEDED

Both readings are defensible:
  (a) the ceiling is a blast-radius instrument, and blast radius is
      production surface -- so it should be measured over `src` alone, where
      this lane came in ON estimate;
  (b) the ceiling is a review-cost instrument, and a 400-line test module is
      400 lines a reviewer must read -- so the total is the right measure and
      SPEC.md simply under-budgeted the tests.

If (a): change the ceiling's `--paths` in the tranche template to `src`, and
say so where the batch-1 withheld lanes are recorded, so the next lane does
not stop on the same reading.
If (b): the ceiling stands, this tranche is over it, and the disposition is
whether to split the delivered work into two tranches after the fact -- which
buys nothing here, since both commits are already self-contained and gated.

Evidence: run
  python tools/diff_budget.py 84514a0280f45d29e5066bb3be3d273ba73798db \
    --ceiling 400 --paths src tests docs/map
and
  python tools/diff_budget.py 84514a0280f45d29e5066bb3be3d273ba73798db \
    --ceiling 400 --paths src
```
