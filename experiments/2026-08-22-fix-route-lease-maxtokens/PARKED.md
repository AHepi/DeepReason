# PARKED — found while fixing the route-lease / max_tokens disagreement

---

## P1-lease — a route-firewall refusal is recorded under the tag the controller reads to WIDEN a timeout

**What:** `Scheduler._drop` tags every dropped call `dropped-call`, and
`controller.TRANSPORT_DROP_TAG` is the string `"dropped-call"`. So the typed
lease violation that ended run `40e713b3…` was written into the log under the
signal the allocation controller consumes as evidence that the transport is
too slow. In the epoch-2 record this is visible directly: `log.jsonl` seq 577
is `Measure ["dropped-call", "ROUTE_LEASE_MISMATCH role='conjecturer' seat=0
field=max_tokens expected=32768 actual=20480"]`.

Nothing acted on it, and nothing can act on it today: the run terminated at
seq 578, and after this tranche's fix no lawful controller tune produces a
lease refusal at all. It is parked rather than fixed because it is a second
mechanism (signal classification), this tranche has one goal, and the
`_new_transport_drops` reader does already filter on `TRANSPORT_REASONS` —
whether `ROUTE_LEASE_MISMATCH` passes that filter is the first thing the
follow-up must measure rather than assume.

```
Route: deepreason-orchestrator (defect, design-first -- expect to stop at
DIAGNOSIS.md; the answer may legitimately be "correct as written", since
`_new_transport_drops` filters on TRANSPORT_REASONS and the mis-tag may never
reach the controller at all).

One goal: establish whether a RouteFirewallError recorded as `dropped-call`
can reach `Controller._new_transport_drops` as a fresh transport drop, and if
it can, give a non-transport drop its own typed tag -- so a lease violation
can never be answered by lengthening a wait.

Measure this FIRST, before any design; it may end the tranche:
    python -c "from deepreason.controller import TRANSPORT_REASONS; \
      print(TRANSPORT_REASONS); \
      print([m for m in TRANSPORT_REASONS if m in 'ROUTE_LEASE_MISMATCH'])"
If no reason substring matches, the mis-tag is cosmetic and the correct
outcome is a recorded 'correct as written' plus a check pinning the filter,
not a new tag.

Evidence, already committed:
  - experiments/2026-08-22-live-reach-rich-run/run/log.jsonl seq 577 -- the
    refusal recorded under the `dropped-call` tag.
  - src/deepreason/scheduler/scheduler.py, `_drop` (both call sites, ~545 and
    ~3002) -- every dropped call gets the same tag regardless of cause.
  - src/deepreason/controller.py, TRANSPORT_DROP_TAG and
    `_new_transport_drops` -- the consumer, and the reason filter that may
    already make this harmless.
  - docs/map/SEAM-llm-x-scheduler.md Traps, fourth entry -- the finding as
    recorded by the tranche that found it.

Read first: docs/map/SEAM-llm-x-scheduler.md (written by that tranche; it is
the agreement this would touch), docs/map/INV-signal-contract.md (a signal is
a CONTRACT declaring name, unit, producer-agnostic semantics and a staleness
bound -- a new tag is an ADD-SIGNAL, so docs/map/REC-add-signal.md is the
recipe), and CLAUDE.md's allocation design law.

Constraint the design must respect: `dropped-call` is a declared signal that
committed roots already carry. Do not re-spell it. A non-transport drop gets
its own name; the existing name keeps its existing meaning, or every root's
drop census changes meaning retroactively.

End state: DIAGNOSIS.md naming one of -- (a) correct as written, the reason
filter already excludes it, with the check that pins that; (b) reachable, and
a new declared signal for non-transport drops, added through REC-add-signal.
A regression test pinning whichever answer is chosen, naming run 40e713b3 in
its docstring.
```
