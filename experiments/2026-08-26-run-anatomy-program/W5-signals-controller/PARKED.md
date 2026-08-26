# W5 — PARKED

Everything this census surfaced that is NOT its goal. Nothing here was
fixed: W5 is read-only, and the RUN ANATOMY PROGRAM fixes nothing in any
window or round. Each entry is written for its FUTURE RUNNER — one line of
WHAT, then a prompt that can be pasted into a fresh window without this
one's context.

Ordered by what they cost if left alone, not by how interesting they are.

---

## P1 — The allocation controller steers nothing, silently

**What.** 47 knob-moves across the nine post-landing roots, every one
in-envelope and logged as a replayable policy artifact, and not one ever
became the `max_tokens` of a later dispatch. `Controller._apply_cap` writes
`endpoint.max_tokens`; `Adapter._completion_cap` books
`lease.route.max_tokens` whenever the route declares
`context_window_tokens`, which every committed root's routes do. The value
the controller writes has no reader. This is a RECURRENCE of the class the
2026-08-13 `defect-controller-steering-inert` tranche fixed, arriving
through a different door, and it is now silent where it used to be
terminal.

**Priority.** Highest. Not because a knob is wrong — because a control loop
that logs decisions nothing acts on will read, to any later reader of the
record, as a working controller.

```
Route through deepreason-orchestrator. ONE GOAL: decide, and record, what
the allocation controller's cap decisions should do now that nothing reads
them — then implement whatever that decision is.

EVIDENCE, already committed, do not re-derive it:
experiments/2026-08-26-run-anatomy-program/W5-signals-controller/
  RESULTS.md            segment 1, "Why steering does nothing"
  DECISIONS_AND_EFFECT.md   47 rows; the `wire` column is `no` in all 47
  CONTROLLER_CENSUS.json    the machine-readable form
Re-derive with: cd to that directory, `python3 census.py && python3 render.py`.

THE MECHANISM, in three files:
- src/deepreason/controller.py `_apply_cap` writes `endpoint.max_tokens`.
- src/deepreason/llm/adapter.py `_completion_cap` returns
  `lease.route.max_tokens` when `route.context_window_tokens is not None`,
  ignoring the endpoint's settled cap ON PURPOSE — its docstring names the
  run it fixed (bb0455384ea09b5b, epoch-3 attempt 3, which died at
  log.jsonl seq 555 with `transactional reservation bound differs from
  rendered request`).
- src/deepreason/llm/adapter.py:1611 builds each `attempt_trace` entry with
  `**transport_limits`, so the trace records the number actually sent. It
  is a route-declared cap in every dispatch of all 54 committed roots.

THIS IS A DESIGN-AND-STOP. There are at least three roads and they are not
equivalent; do NOT pick one by inference:
  (a) give the controller a consumer — book from the settled cap, and solve
      the booking-window instability that killed attempt 3 some other way;
  (b) move the controller's authority to the reservation, so it settles the
      booked bound rather than an object nobody reads;
  (c) retire the cap knobs and keep the controller for transport timeout
      only, recording that cap steering was withdrawn and why.
Write DIAGNOSIS.md and FIX.md, price the three roads for the operator, and
STOP at the approval gate. Do not implement before the operator chooses.

FROZEN-SURFACE WARNING, read before designing: `invariants.py` re-derives
`allocation.route_cap_for_knob` and `controller.cap_envelope` to decide what
a logged policy authorized — that is frozen surface 3. Read
docs/map/INV-frozen-surfaces.md and docs/map/INV-signal-contract.md first,
and docs/map/SEAM-llm-x-scheduler.md before either subsystem.

END STATE: a committed FIX.md with three priced roads and a recommendation,
and an ended turn. No code change in the same tranche as the design.
```

---

## P2 — `controller-update` is declared, has no emitter, and its only test asserts its absence

**What.** `signals.py` declares `controller-update` with a real unit
(`event`) and a real staleness (`cycle`) — it was one of the five entries
the Rung 1b-ii paydown moved off the `unspecified` debt marker, on the
stated ground that "that rung's consumption side is what establishes when
each is emitted and how long a consumer may believe it". Nothing in `src/`
emits it. The only test naming it
(`tests/test_controller.py:152`) asserts that it does NOT appear. The
controller records updates as `Refl` policy artifacts, which is exactly
what ERRATA E43 corrected a comment for getting wrong.

**Priority.** Medium. A registry entry that promises a record nothing
writes is the failure mode the registry exists to prevent.

```
Route through dr-change-orchestrator. ONE GOAL: reconcile the
`controller-update` registry entry with the fact that nothing emits it —
either by emitting it where the controller applies a policy, or by retiring
the entry, whichever the operator chooses.

EVIDENCE:
experiments/2026-08-26-run-anatomy-program/W5-signals-controller/
  DECLARED_VS_EMITTED.md   "Structural silence"
  SIGNAL_CENSUS.json       `controller-update`: ever_emitted 0 over 54 roots
Confirm the absence of an emitter yourself:
  grep -rn "controller-update" --include=*.py src/
  -> only src/deepreason/signals.py.

THE TENSION TO RESOLVE, stated so it is not resolved by accident: the
paydown's justification for giving this entry a real unit and bound was
that the consumption side establishes them. There is no consumption side.
Either the paydown was premature for this one entry, or the emit site was
dropped. docs/map/INV-signal-contract.md pins the debt census at 84 and
says it may only SHRINK — retiring an entry changes that census, so read
docs/map/REC-add-signal.md §"paying down the debt" before touching it.

NOTE the ordering dependency: if P1 changes where the controller's decision
is recorded, this entry's answer changes with it. Ask the operator whether
to sequence this after P1.

END STATE: REQUEST.md capturing the operator's choice verbatim, then the
ordinary change phases.
```

---

## P3 — Four of the five `allocation.POLICY_SIGNALS` are not auditable from any record

**What.** `allocation.POLICY_SIGNALS` names five signals "the allocation
policy reads". Only `dropped-call` is a logged Measure tag.
`allocation.seat-truncation.v1` and `allocation.seat-repair.v1` are
computed inside `Controller._process_signals` from `event.llm` fields;
`allocation.policy-authorized.v1` and `allocation.policy-contested.v1` are
read out of `harness.state.status`. None has an emit site. The values a
policy acted on are therefore recoverable only from the `evidence` block
the policy artifact happens to carry, and only for decisions that produced
a delta — a step that proposed nothing logs nothing.

**Priority.** Medium. This is not a bug: the interface-only consumption it
implements is the contract working as designed. It is an EVIDENCE gap, and
it is why "what did the controller read in a cycle where it held?" is not
answerable for any committed root.

```
Route through dr-change-orchestrator. ONE GOAL: decide whether the four
in-process policy signals should be emitted as Measure values, so that what
the allocation controller read is auditable in every cycle rather than only
in cycles that produced a delta.

EVIDENCE:
experiments/2026-08-26-run-anatomy-program/W5-signals-controller/
  DECLARED_VS_EMITTED.md   "Structural silence" — the five-row table
  RESULTS.md               "The declared-but-silent census"

THE ARGUMENT ON BOTH SIDES, so the tranche does not present one:
FOR emitting — the census could not answer "what did the controller read
  when it held?" for any of the nine roots, because a held step is silent;
  a per-cycle seat-truncation/seat-repair measure would make the whole
  input series auditable, and the two capture14 families already do exactly
  this every cycle (`Scheduler._record_detection_signals`).
AGAINST emitting — it is pure log volume for a controller that, per P1,
  currently steers nothing; and every new Measure event is a replay
  obligation on a frozen surface.
The honest sequencing is: this question is downstream of P1's answer. Say
so to the operator rather than deciding it here.

END STATE: REQUEST.md with the operator's verbatim decision, or a recorded
decision to defer until P1 is settled.
```

---

## P4 — `capture14.hysteresis-mode.v1` declares a `cycle` bound and is relied on for the whole run

**What.** The signal is declared `unit=event, staleness=cycle`. Its reader,
`capture.hysteresis.policies()` feeding `mode()` and `slice_budgets()`
(reached from `calculus/render.py:283`), takes
`reversed(policies(harness))` — the most recent receipt, whatever its age.
Measured on the record: emitted once, in cycle 1, in each of the three
roots that emit it at all, and still in force at cycle 11, 11 and 15
respectively — up to 14 cycles past its declared bound.

**Priority.** Medium-low, and the fix is almost certainly one word. The
mismatch is in the DECLARATION, not the reader: hysteresis is a mode that
persists until it changes; that is what hysteresis IS. A signal whose whole
purpose is to persist should not declare `cycle`.

```
Route through dr-change-orchestrator. ONE GOAL: correct the declared
staleness of `capture14.hysteresis-mode.v1` to match the reliance its
reader actually places on it, or state on the record why `cycle` is right
and the reader is wrong.

EVIDENCE:
experiments/2026-08-26-run-anatomy-program/W5-signals-controller/
  STALENESS.md    "The one bound the record shows exceeded" — the per-root
                  ages, 10 / 10 / 14 cycles
  STALENESS.json  the machine-readable form

READ FIRST: docs/map/INV-signal-contract.md (the registry is VERSIONED, so
changing a declaration is a recorded decision, not a free edit) and
docs/map/REC-add-signal.md. `run` is the candidate bound; check it against
`capture/hysteresis.py::mode`'s absence-tolerant reader before proposing it.

WHILE YOU ARE THERE, one adjacent row from the same census, cheap to settle
in the same tranche if the operator agrees to widen it — and PARKED
separately if not: `premise.work-invited.v1` declares `unit=event,
staleness=cycle` and has NO consumer anywhere in src/ (it is the anti-E28
receipt, written so an untaken invitation is still on the record). A bound
nothing relies on is not wrong, but it is not a promise either, and the
census records it as `NO-CONSUMER` rather than as a pass.

END STATE: REQUEST.md, SPEC.md, one declaration change, the map moving in
the same commit.
```

---

## P5 — Eight Measure tags are emitted 18,151 times and no registry entry declares them

**What.** `signals.py` opens by promising a reader following the log "never
meets an undocumented tag", and names exactly two families that carry no
signal string by design. The record contains a third class:
`criticism.coverage-debt.v1` (11,764 events),
`v6-model-phase-deferred.v1` (2,668), `criticism.attempt.v1` (1,767),
`criticism.assignment.v1` (1,742), `defended-trial-deferred` (119),
`module-fingerprints.v1` (38), `contract-decomposition-effect` (31),
`seat-bindings.v1` (22). Six are typed-record SCHEMA identity tags written
through `record_*` helpers; two are signal literals bound to a variable
before the call. `tests/test_signals.py` scans for
`record_measure(inputs=[<literal>...])` heads, so all eight escape it.

**Priority.** Medium-low as a correctness matter, higher as a documentation
one: the census that says "32 of 111 names have ever been emitted" is
measured against a registry that does not cover a fifth of the Measure
events in the corpus.

```
Route through dr-change-orchestrator. ONE GOAL: make the signal registry
cover what the log actually carries — either by declaring the third class
(typed-record schema tags) as a named family the way HV and reach are, or
by declaring the eight tags individually, and by widening the enforcement
so a tag assembled into a variable cannot escape it.

EVIDENCE:
experiments/2026-08-26-run-anatomy-program/W5-signals-controller/
  DECLARED_VS_EMITTED.md   "Emitted but NOT declared" — the eight-row table
                           with the emit site and the reason the scan misses
                           each one
  SIGNAL_CENSUS.json       `undeclared_tags_ever`

TWO PARTS, and the second is the one that lasts:
1. The eight tags. Note that six are `_identity_domain` / `schema_` fields
   on typed records, so declaring them individually may be the wrong shape
   — signals.py's own docstring already recognises TWO payload-recognised
   families, and this is a third.
2. The enforcement. `tests/test_signals.py::_emitted_signals` matches only
   an inline list literal at the call site. `rules/crit.py:2189` builds
   `deferral_inputs = ["defended-trial-deferred", ...]` and passes
   `record_measure(inputs=deferral_inputs)` — a literal, one line away from
   where the scan looks. Widening the scan is what stops this recurring;
   declaring eight names is not.

Read docs/map/REC-add-signal.md and docs/map/INV-signal-contract.md first.
The 84-entry debt census may only shrink, so check what adding entries does
to it before writing the SPEC.

END STATE: REQUEST.md, SPEC.md, a widened scan that FAILS on the current
tree before the declarations land (prove the test can fail), then the
declarations.
```

---

## P6 — The E43 lease ceiling has never been exercised live

**What.** `Controller._lease_ceiling` clamps a proposal downward to the
seat's leased `max_tokens`, so it can only bind on a WIDENING proposal.
Every one of the 47 decisions in the population is a narrowing:
`truncation_rate` is `0.0` and `repair_rate` is `0.0` in every `evidence`
block of every policy artifact in all nine roots, so `_propose`'s widening
branch was never entered. The ceiling is proven offline
(`tests/test_route_lease_maxtokens_tuning.py`) and has never fired in a
committed run.

**Priority.** Low, and it is an EVIDENCE request rather than a defect —
recorded so that a later reader does not mistake "no live clamp" for "the
clamp does not work". Note also that it is downstream of P1: if the
controller's caps have no consumer, a live clamp cannot be observed at all.

```
Route through deepreason-orchestrator, dr-set-goal only, and expect the
goal to be "generate evidence", not "fix something". ONE GOAL: produce one
committed root in which `Controller._lease_ceiling` demonstrably clamps a
widening proposal.

WHY IT HAS NOT HAPPENED, from the census — do not re-derive:
experiments/2026-08-26-run-anatomy-program/W5-signals-controller/
  DECISIONS_AND_EFFECT.md  "The E43 ceiling: where it binds, and why no row
                           shows a clamp"
No seat in any of the nine post-landing roots ever recorded a truncation,
so `_propose`'s widening branch (`sig["truncation_rate"] > TRUNC_HI`, i.e.
above 0.25) was never entered.

THE PRECONDITION, and it is a hard one: this cannot be observed until P1 is
settled, because a controller whose caps reach no dispatch cannot be seen
to clamp. Read P1 first and say so in GOAL.md.

The operator's standing law applies here — "Tokens are cheap; the agent is
not": if this can be answered by a live run with a deliberately tight seat
cap rather than by building machinery, run it. No live launch without a
green `python -u scripts/cycle_soak.py --case <case>` on the launch config.
```
