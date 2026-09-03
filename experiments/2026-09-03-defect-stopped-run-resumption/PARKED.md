# Parked — found during this tranche, deliberately NOT fixed here

One tranche, one goal (`deepreason-orchestrator` scope contract). Each entry
is written for its future runner at park time: one line of WHAT, then a
ready-to-send prompt.

---

## P1 — a seat's terminal exhaustion kills the whole run instead of retiring the seat

**What.** P-A1 died `V6_ROUTE_SEAT_INSUFFICIENT_CAPABILITY` — "route seat has
terminally exhausted its smallest authorized contract" — at cycle 5 of a
3 000 000-token budget with 1 093 086 spent, i.e. with 64% of the budget
unspent and eleven other seats healthy. Named out of scope by the window
instruction for this tranche. Making a killed run RESUMABLE is this tranche;
stopping the run dying is not.

**Evidence.** `experiments/2026-09-01-live-all-modules-p-a1/run/run-status.json`
(`state: failed`, that message, cycle 5). Stop report section 3 shows the seat
context: `conjecturer#1` 17 attempts / 12 invalid / 6 zero-token with
`RemoteDisconnected ×23`, `defender#0` 8 / 6 / 4 with `RemoteDisconnected ×18`
— 41 transport faults on endpoint `ollama-glm-5.3`, which the report's
section 4 ranks as SUPPORTED evidence for the ENVIRONMENT box. The suspected
site is `src/deepreason/llm/adapter.py:524`.

**Ready-to-send prompt:**

```
EXECUTOR WINDOW — DEFECT TRANCHE: one seat's terminal exhaustion kills the
whole run instead of retiring the seat (P-A1 4565139800...)

Read CLAUDE.md fully, then load deepreason-orchestrator, dr-drive-harness and
dr-explain-to-operator. Start at dr-set-goal. Base on main. Commit and push at
every phase boundary.

FIRST ACT, before any diagnosis: run
  deepreason stop-report experiments/2026-09-01-live-all-modules-p-a1/run
and paste section 4 ("THE STOP, CLASSIFIED") at the top of DIAGNOSIS.md. Every
cause you name must cite a report line.

THE DEFECT. P-A1 terminated `operational_failure` with
`V6_ROUTE_SEAT_INSUFFICIENT_CAPABILITY at
/workflow/insufficient_capability_by_route_seat: route seat has terminally
exhausted its smallest authorized contract` at cycle 5, having spent 1 093 086
of 3 000 000 tokens. Section 3 of the report attributes 41 transport faults
(RemoteDisconnected) to ONE endpoint, ollama-glm-5.3, carrying conjecturer#1
and defender#0. Eleven other seats were healthy and the run had 64% of its
budget left. Suspected site: src/deepreason/llm/adapter.py:524.

GOAL (for dr-set-goal to bound): a seat that terminally exhausts its smallest
authorized contract is RETIRED with a typed record, and the run continues on
its remaining seats, degrading typed rather than dying — unless retiring it
leaves no seat able to fill a required role, which is a typed run stop naming
the role. Success criterion offline: a stub run whose one conjecturer seat is
driven to terminal exhaustion, where a second conjecturer seat exists,
completes its remaining cycles and its record carries a typed seat-retirement;
and the same run with only ONE conjecturer seat stops typed, naming the role.
RED/GREEN mutation proofs committed.

DESIGN CONSTRAINTS. Read CON-seats.md and SUB-llm.md before designing. The
operator's solo-run law (CLAUDE.md, 2026-08-09) is binding: sole-model
operation may never be structurally locked out, so the single-seat road must
stop typed rather than be treated as a misconfiguration. A NEW record format
or event kind is frozen surface 3 -> PRICED STOP.

OUT OF SCOPE, parked: stopped-run resumption (tranche
experiments/2026-09-03-defect-stopped-run-resumption/, which made P-A1's
terminal SHAPE resumable but did not stop it happening).

VALIDATION: full gate, 0 failed. Map in the SAME commit: SUB-llm / CON-seats,
re-runnable single-line check: lines, Traps entry naming run 4565139800.
```

---

## P2 — budget exhaustion still terminating as `operational_failure` (CHECK, then record or park)

**What.** The operator's 2026-08-29 law says a budget denial on an exhausted
budget terminates `budget_exhausted` (clean), never `operational_failure`.
This tranche's fix makes the failure terminal resumable, which REMOVES the
practical sting of a misclassification but does not fix the classification.
The window instruction directs: check, record, park.

**State at park time.** Checked, and the answer is not yet in evidence: none
of this tranche's four roots exhibits a budget denial misclassified as
`operational_failure` (P-A1's `operational_failure` is seat exhaustion, which
is a genuine operational failure, not a budget denial). So this is parked as
UNMEASURED rather than as a confirmed defect — the census that would settle it
has not been run.

**Ready-to-send prompt:**

```
EXECUTOR WINDOW — AUDIT-THEN-DEFECT: does any road still terminate a
budget-exhausted run as operational_failure?

Read CLAUDE.md fully, then load dr-drive-harness and dr-explain-to-operator.
This starts READ-ONLY. Base on main.

THE LAW (operator, 2026-08-29, verbatim in CLAUDE.md): "clean stop. with an
assurance that continuing is possible." Ledgered reading: a budget denial on
an EXHAUSTED budget terminates `budget_exhausted` (clean), never
`operational_failure`.

STEP 1, read-only census. Enumerate every road that can raise or record
stop_reason="operational_failure" (grep is fine for enumeration, but attribute
each site from the record, not from reading). For each, decide whether a
budget denial can reach it. Then census the committed roots: any root whose
run-status.json says operational_failure while its log's last denial is a
budget denial is a confirmed instance. Write CENSUS.md.

STEP 2. If the census finds ZERO instances, the law is already held: record
that verdict in CENSUS.md with the commands, commit, and STOP — do not open a
defect tranche for a defect that is not there. If it finds instances, route
into deepreason-orchestrator at dr-set-goal with the census as Observed.

CONTEXT. experiments/2026-09-03-defect-stopped-run-resumption/ made failure
terminals resumable, so a misclassification here no longer strands a run — it
mislabels one. That lowers the severity; it does not settle the question.
```

---

## P3 — the jailbreak tranche's P2 residue: a record too corrupt to replay passes the gate

**What.** NOT introduced by this tranche and NOT widened by it — but this
tranche increases EXPOSURE to it, and that is stated in FIX.md rather than
left implicit. Before this tranche, failure terminals and stops with
outstanding work were unreachable by `continue` for lifecycle reasons, so the
integrity gate was never the only thing standing between a tampered record and
a resumed run on those roots. After it, the gate IS the only thing standing
there — which is the correct design (the receipt never authorizes continuation
by itself; the gate does) and is exactly what the operator's security clause
asks for. The residue is unchanged in size; more roads now lead to it.

**Owner.** `experiments/2026-08-31-defect-jailbreak-gate-closure/` PARKED P2.
Do not re-park it here as if it were new; this entry exists so the next runner
knows the exposure changed and where the residue is owned.

**Ready-to-send prompt:** use the one already committed at
`experiments/2026-08-31-defect-jailbreak-gate-closure/PARKED.md` P2, and add
this sentence to its context: "Exposure widened 2026-09-03 by
experiments/2026-09-03-defect-stopped-run-resumption/, which made failure
terminals and stops-with-outstanding-work reachable by continue/amend, leaving
the SECURITY-channel gate as the sole guard on those roads."

---

## P4 — the two seams this defect lives on are undocumented

**What.** `application x workflow` and `application x run-identity` are both
declared `Seams-undocumented:` by their own subsystem documents, and
`INDEX.md` states that a pair listed without a document "has NOT been shown to
be uninteresting". The STOPPED receipt meets the outstanding-work predicate on
the first; the terminal write meets the `continue` gate on the second. Whether
this tranche writes `SEAM-application-x-workflow.md` is decided in
dr-implement-fix by where the fix actually lands; if it does not, this entry
carries the work forward.

**Ready-to-send prompt:**

```
EXECUTOR WINDOW — MAP TRANCHE: write SEAM-application-x-workflow.md

Read CLAUDE.md, docs/map/SCHEMA.md and docs/map/REC-change-a-seam.md. This is
a map-only tranche: no src/ change.

WHY. Both SUB-application.md and SUB-workflow.md declare this pair
Seams-undocumented. It is the seam where terminalize_text_run's STOPPED
receipt meets build_stopped_lifecycle's outstanding-work predicate — the seam
that produced the 2026-09-03 stopped-run-resumption defect across three
terminal shapes and 16+ committed roots.

WHAT IT MUST SAY. Which fraction of each side is involved (small: the receipt
request, the snapshot predicate, and the refusal that travels back as
terminal_lifecycle_refusal); the agreement about WHO may refuse a receipt and
on what evidence; and the Traps already earned, citing runs 4565139800,
63e48f5741 and fe00609058.

EVERY load-bearing claim carries a re-runnable single-line `check:` at column
0 that would FAIL if the behaviour regressed. Run `python
tools/docs_verify.py` (FULL mode) and `--audit` before committing.
```

---

## P5 — a resumed run may still die on an outstanding item with no provider attempt

**What.** Found during dr-verify-outcome, and the one thing this tranche's
end-to-end proof could NOT demonstrate. P-A2 epoch 4 carries a CRITICISM work
order that was ISSUED with no provider attempt recorded — the container kill
landed between dispatch and the atomic attempt append. It holds no unread
provider result, so it correctly no longer vetoes the STOPPED receipt (unit
test `test_outstanding_work_with_no_unread_result_takes_the_receipt[False]`).
But `InquiryTransactionService.recover_incomplete()` cannot CLOSE it either:
there is no result to admit. So `Scheduler._recover_workflow_prefixes` would
reach its own `raise RuntimeError("transaction recovery left unfinished
authority")` on exactly the killed-run shape resumption exists for.

**Why it was not fixed here.** The stub cannot produce the sub-shape: every
outstanding item on all three stub shapes is `outcome=provider_result`. Fixing
a road that no offline instrument can drive would mean shipping an untested
recovery path, which is worse than shipping a loud typed failure. The loud
failure is the current behaviour and it is honest.

**What is genuinely open.** Whether the right answer is (a) leave the
RuntimeError — a kill in that exact window is unrecoverable and says so; (b) a
typed ABANDONMENT for an outstanding work order with no provider attempt, which
is a new record kind and therefore frozen surface 3, a PRICED STOP; or (c)
re-dispatch, which risks a second call bound to one authority. This tranche
takes no position.

**Ready-to-send prompt:**

```
EXECUTOR WINDOW — DEFECT TRANCHE: a resumed run dies on an outstanding work
order that has no provider attempt

Read CLAUDE.md fully, then load deepreason-orchestrator, dr-drive-harness and
dr-explain-to-operator. Start at dr-set-goal. Base on main after the
stopped-run-resumption tranche merged. Commit and push at every phase boundary.

FIRST ACT: run
  deepreason stop-report experiments/2026-09-02-live-p-a2-corrected/run
and paste section 4 at the top of DIAGNOSIS.md.

THE DEFECT. Since 2026-09-03 a stop takes its lifecycle receipt over
outstanding work, and Scheduler._recover_workflow_prefixes closes that work on
resume. It closes work whose provider call RETURNED. P-A2 epoch 4's work order
sha256:93672cb is a CRITICISM ISSUED with provider_attempts == {} -- the kill
landed between dispatch and the atomic attempt append -- and
recover_incomplete() cannot close it. The method then raises
RuntimeError("transaction recovery left unfinished authority"), so the resume
this shape most needs is the one that fails. Census it first: how many
committed roots carry such an item, and does any shape other than a kill
produce one?

GOAL (for dr-set-goal to bound): a run killed between dispatch and its provider
attempt resumes, with the un-started work order disposed TYPED. Success
criterion offline: a stub root driven to a kill inside that window (the
existing proof/three_shapes.py `killed` shape does NOT reach it -- extending
the stub to do so is part of the tranche and is the hardest step; do it before
designing) resumes and reaches a later cycle, and its record names what
happened to the work order.

DESIGN CONSTRAINTS. Three roads, priced in
experiments/2026-09-03-defect-stopped-run-resumption/PARKED.md P5: leave the
loud failure; a typed abandonment (NEW RECORD KIND -> frozen surface 3 ->
PRICED STOP, get the grant in SPEC.md before code, never verbally); or
re-dispatch (risks two calls bound to one authority -- read
workflow/lifecycle.py's unconsumed_bound_call_seqs invariant before proposing
it). Do NOT weaken the unconsumed-provider-call refusal: it is the one thing
the 2026-09-03 tranche deliberately kept.

VALIDATION: full gate, 0 failed. Map in the SAME commit: SUB-workflow /
SUB-scheduler, Traps entry naming 63e48f5741 and work order sha256:93672cb.
```

---

## P6 — `stop-report` and `verify_root` disagree about P-A2 epoch 4

**What.** `deepreason stop-report` section 5 reports
`verify_root: {"checks": [], "source": "stored", "violations": 0}` for
`experiments/2026-09-02-live-p-a2-corrected/run`, while that root's own
`REPLAY_VALIDATION.json` AND a fresh `verify_root` on a copy both report **1**
violation (`foreign-criticism`: "target 6049eea6b9e2b1260a929389c9a97baf7b3e6af560ff2a0561179ca34ecc817d
has 0 foreign schools; policy requires 1"). Two instruments, one root,
different numbers.

**Why it is parked and not fixed.** Out of this tranche's goal, and it changed
nothing in its verdict under either reading: `foreign-criticism` is not a
SECURITY-channel finding, `record_verification_refusal` returns `None` on that
root, and the refusal it actually received was a lifecycle one. But
`stop-report` is the instrument `dr-diagnose` now GATES on, so a root where it
under-reports violations is a diagnosis surface that could mislead the next
runner.

**Ready-to-send prompt:**

```
EXECUTOR WINDOW — DEFECT TRANCHE: stop-report under-reports verify_root
violations on at least one committed root

Read CLAUDE.md fully, then load deepreason-orchestrator, dr-drive-harness and
dr-explain-to-operator. Start at dr-set-goal. Read-heavy, small blast radius.

THE DEFECT. On experiments/2026-09-02-live-p-a2-corrected/run:
  deepreason stop-report <root>            -> section 5: "violations": 0
  python -c "from deepreason.invariants import verify_root; ..." on a COPY
                                           -> 1 violation, foreign-criticism
and the root's own REPLAY_VALIDATION.json agrees with the second, not the
first. stop-report says source "stored", so the suspicion is that it reads a
different stored field, or a different shape of stored verdict, than
REPLAY_VALIDATION.json's -- note DR-SUB-application's Traps entry recording
that REPLAY_VALIDATION.json's `verification` block is the LEGACY
{stats, violations} shape in all 86 committed roots that carry it, while the
five-channel finding_counts breakdown lives in run-result.json. Census which
of the two shapes stop_report.py actually reads and on how many roots the two
disagree.

WHY IT MATTERS. dr-diagnose now GATES on stop-report section 4, so every
diagnosis starts from this instrument. An instrument that under-reports
violations sends the next runner past the evidence.

GOAL (for dr-set-goal): stop-report's continuability section reports the same
violation count as the root's own stored verdict, or states in typed terms
which verdict it is reading and why it differs. Success criterion: a census
over committed roots showing zero disagreements, plus a regression fixture on
the disagreeing root.

OUT OF SCOPE: changing verify_root or any replay-validation record format
(frozen surface 3). This is a READER defect if it is one at all.
```
