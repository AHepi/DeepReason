<!-- tranche: 2026-09-02-defect-provider-transport-faults -->

# Parked — found here, deliberately NOT done here

Each entry: one line of WHAT, then a ready-to-send prompt. Starting the
follow-up should cost a paste, not an authoring session.

---

## P1 — Seat degradation: retire an exhausted or dead seat and continue on the others

WHAT: P-A1 died because ONE seat (seat 1, glm-5.3) exhausted its contract
ladder after a 10-call transport-failure streak, while seat 0 (deepseek) was
healthy the whole run. The run has no way to stand a seat down and keep going.

```
DEFECT TRANCHE: one dead seat kills a run that has a healthy seat
(P-A1 run 4565139800f5ca02)

Read CLAUDE.md fully, then load deepreason-orchestrator, dr-drive-harness and
dr-explain-to-operator. Start at dr-set-goal. Work on your window's assigned
branch; commit and push at every phase boundary.

THE DEFECT, FROM THE RECORD (diagnose from the record BEFORE reading code):
P-A1 (branch claude/live-reasoning-p-a1-bv65kl,
experiments/2026-09-01-live-all-modules-p-a1/run/, READ-ONLY) terminated on
`workflow-route-seat-insufficient-capability-v1`: seat 1 glm-5.3,
`smallest_authorized_contract_schema_exhausted`. Seat 0 (deepseek-v4-pro) was
healthy throughout and had answered every call it was given. The run had
completed real cycles. One seat's exhaustion terminated the whole run.

GOAL (for dr-set-goal to bound): a run whose seat becomes unusable — contract
ladder exhausted, or a typed dead-provider streak — must be able to stand that
seat down with a typed notice and continue on the seats that remain, when the
configuration permits it. Success criterion, falsifiable: on a stub where seat
1 always fails and seat 0 always answers, the run reaches a clean terminal
having completed cycles on seat 0, records a typed seat-standdown event naming
the seat and the reason, and `deepreason results` reports the standdown.
Mutation-proven RED/GREEN, committed.

DESIGN CONSTRAINTS: whether a run SHOULD continue on fewer seats is a policy
question the operator decides — raise it once in FIX.md with a proposal, do
not implement a default silently. Standing a seat down changes what a run
GENERATES, never what counts as EVIDENCE (the seats law). Frozen surfaces
untouched. The all-configurations law applies: disclose, never die.

DEPENDS ON: the provider-health counters landed by
experiments/2026-09-02-defect-provider-transport-faults/ (per-seat attempts /
faults / zero-byte returns / last fault kind, in progress.jsonl and
`deepreason results`) — that tranche's typed dead-provider-streak notice is the
natural trigger for a standdown. Read its FIX.md and VERIFY.md first.

OUT OF SCOPE: the transport layer itself; the model-profile registry; live runs.
```

---

## P2 — The dead-provider-streak STOP question (operator decision, raised not implemented)

WHAT: this tranche emits a typed NOTICE after N consecutive zero-byte attempts
on one seat. Whether the run should additionally STOP CLEANLY after such a
streak is a policy question. Raised in FIX.md with a proposal; not implemented.
Resolution belongs with P1 above (a standdown is the alternative to a stop).

---

## P3 — Monitor scripts read keys the attempt trace does not carry

WHAT: P-A1's `monitor.sh` classified a failed attempt by
`t.get("error") or t.get("failure") or t.get("status") == "error"`; the attempt
trace carries none of those keys, so 40 faults raised 0 alerts. This tranche
fixes the HARNESS side (publish provider health where a monitor already reads).
It does not ship a corrected monitor template.

```
CHANGE TRANCHE: ship a provider-health monitor template that reads the typed
signature, and retire the hand-rolled per-experiment monitor.sh

Read CLAUDE.md fully, then load dr-change-orchestrator, dr-drive-harness and
dr-explain-to-operator. Start at dr-capture-request.

THE REQUEST (operator's standing intent, from the P-A1 monitor review F7):
every live ladder hand-rolls a monitor.sh, and P-A1's tested keys the record
does not carry (`error` / `failure` / `status`), so 40 transport faults raised
0 alerts. After
experiments/2026-09-02-defect-provider-transport-faults/, provider health is
published typed in progress.jsonl and `deepreason results`. Ship ONE reusable
monitor that reads those published fields, and have the ladder scripts use it
instead of a per-experiment copy.

Success criterion: against a recorded progress.jsonl containing a
dead-provider streak, the shipped monitor raises the alert; against a healthy
one it stays silent; both pinned by a committed test.
```

---

## P4 — `deepreason results` is the ONE retrieval surface, but summaries are hand-written

WHAT: the P-S1 finding is that 54 typed transport failures appeared in ZERO
summary documents. This tranche makes them visible in the two typed surfaces.
It does NOT make any workflow REQUIRE that a delivery document quote the
provider-health block, which is what would actually have caught P-S1.

```
CHANGE TRANCHE: a delivery document for a live run must quote the typed
provider-health block

Read CLAUDE.md fully, then load dr-change-orchestrator. Start at
dr-capture-request.

THE REQUEST: P-S1 (run 9e48a36b1dec91ee) ran 15 of 24 cycles against a dead
provider with 54 typed transport failures, and not one summary document said
so. P-A1 repeated it. After
experiments/2026-09-02-defect-provider-transport-faults/, the numbers exist in
`deepreason results`. Make the live-run reporting phases REQUIRE the typed
provider-health block to be pasted into RESULTS.md / FINDINGS.md, so a summary
cannot be written that omits a dead provider. This is a skill/workflow change,
not a code change — the enforcement lives in the phase that writes the
document.

OUT OF SCOPE: the harness; the monitor template (see P3).
```

---

## P5 — `SPLIT_BUDGET_EXTRACTION_TOKENS` default (512) does not fit the conjecturer schema

WHAT: recorded by the P-A1 monitor review addendum — deepseek's conjecturer
extraction legs were cut at 512 tokens in 10 of 13 cases. NOT this tranche's:
`llm/split.py` and the extraction leg belong to the model-profile window.
Noted here only so the finding is not lost.

---

## P6 — `dropped-call` is an overloaded signal, and the controller answers it by widening a wait

WHAT: found while diagnosing. `Scheduler._drop` tags every dropped call
`dropped-call` (`controller.TRANSPORT_DROP_TAG`), which is the same signal the
allocation controller reads to LENGTHEN the transport timeout. A firewall lease
refusal therefore lands in the same channel as a genuine transport drop, so the
controller can answer a lease violation by widening a wait. Already parked once
at `experiments/2026-08-22-fix-route-lease-maxtokens/FIX.md` and recorded in
`docs/map/SEAM-llm-x-scheduler.md` Traps. This tranche does NOT add a second
consumer to that signal; its retry policy reads its own per-call state.

```
DEFECT TRANCHE: `dropped-call` conflates a firewall lease refusal with a
transport drop, and the allocation controller widens a wait in response

Read CLAUDE.md fully, then load deepreason-orchestrator, dr-drive-harness and
dr-explain-to-operator. Start at dr-set-goal.

THE DEFECT, FROM THE RECORD: `docs/map/SEAM-llm-x-scheduler.md` Traps records
it verbatim — "`Scheduler._drop` tags every dropped call `dropped-call`, which
is the same signal the controller reads to LENGTHEN the transport timeout.
After the fix no lawful tune produces such a refusal, so nothing acts on it; if
a future change reopens a path where a run survives a lease refusal, the
controller will answer a lease violation by widening a wait. Parked, not fixed."
Emit sites: `scheduler/scheduler.py:579,583` and `:3253,3255`; declaration
`signals.py:89` and `:380`; consumer `controller.py:93`.

GOAL (for dr-set-goal to bound): a lease refusal and a transport drop must be
distinguishable at the signal layer, so no consumer can answer one by acting on
the other. Success criterion, falsifiable: an offline test drives both paths and
asserts the controller's timeout widening fires on the transport drop and NOT on
the lease refusal; mutation-proven RED/GREEN.

DESIGN CONSTRAINTS: this is a signal-registry change — read
`docs/map/INV-signal-contract.md` and `docs/map/REC-add-signal.md` first, and
follow REC-add-signal exactly (a producer predicate is half the declaration; a
name added to POLICY_SIGNALS without its `_PRODUCERS` entry raises KeyError in
`open_loop_signals`). Allocation touches EFFICIENCY, never EVIDENCE. Frozen
surfaces untouched.

CONTEXT: `experiments/2026-09-02-defect-provider-transport-faults/` deliberately
did not add a second consumer to this signal; its retry policy is per-call and
reads no signal. Read its FIX.md §"signal layer" before designing.
```
