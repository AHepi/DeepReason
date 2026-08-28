# DIAGNOSIS — one cause, from the typed record

Phase: `dr-diagnose`. Reads GOAL.md. Record first; code second.

## Primary cause

`Scheduler.step()` (`src/deepreason/scheduler/scheduler.py:2052-2054`) has one
early return whose branch advances the cycle counter without ever reaching the
allocation policy:

```python
if self._simulation_capability_step():
    self._cycles += 1
    return
```

`self._cycles` is the DENOMINATOR of the seed-lineage share
(`wander.reading_from(..., cycles=self._cycles, seed_worked=self._seed_cycles)`
at `scheduler.py:1130-1135`). `self._seed_cycles` is advanced only by
`_count_lineage` (`1214-1226`), which is reached only from `_select_problem`
(`2056`). `_disclose_wander` (`1229-1274`), which emits
`allocation.seed-lineage-share.v1`, is called only at `2061`.

All three of those sites are BELOW the early return. Therefore a capability
cycle:

1. moves the denominator (`_cycles += 1`),
2. cannot move the numerator (`_seed_cycles` is unreachable on that path),
3. consults no policy (`wander.decide` is unreachable on that path),
4. emits no reading (`_disclose_wander` is unreachable on that path).

(1)+(2) is the arithmetic defeat of the floor. (3)+(4) is the invisibility.

## Why a heartbeat census does not show it

The capability step emits its OWN cycle heartbeat, at three sites —
`scheduler.py:1802`, `1950` and `2030` — so `cycle_heartbeats_emitted` equals
`terminal_cycle_in_status` and a census that compares those two reports a gap
of zero. The audit's own probe carries this in its docstring as
"a cycle taken by the simulation-capability step emits NO `cycle` heartbeat",
which is why its `cycles_that_bypassed_the_cap` field reads `0` for epoch 6.
That field is wrong for this defect; the field that shows it is
`wander_readings` against `cycle_heartbeats_emitted`. Correction noted here
rather than in the audit's committed file, which this tranche does not edit.

## The record's own numbers (re-derived first-hand, not quoted)

From `experiments/2026-08-28-audit-run-problems/probes/q3_cycle_accounting.json`,
committed:

| root | cycles | heartbeats | wander readings | throttles | share trajectory |
|---|---|---|---|---|---|
| epoch 1 (`completed-epoch1-…a97e3`) | 12 | 12 | **12** | 5 | `1.0, 1.0, 0.5, 0.333333, 0.5, 0.4, 0.5, 0.428571, 0.5, 0.444444, 0.5, 0.454545` |
| epoch 6 (`run`) | 24 | 24 | **4** | 1 | `1.0, 1.0, 0.5, 0.333333` |

Epoch 1's `capability_event_counts` is `{}` — zero capability cycles — and its
readings equal its cycles exactly. Epoch 6's heartbeat census is
`simulation-result:` ×19, `simulation-request:` ×1, seed ×2, `disc:` ×1,
`conn:` ×1: **20 capability cycles, 4 selection cycles**, against exactly 4
readings. The correspondence is one reading per selection cycle and none per
capability cycle, which is what the code above predicts.

## What epoch 6's four readings prove about the two lost counters

Each reading at selection cycle *k* is computed from the counters BEFORE that
cycle (`wander.decide` runs at the top of `_select_problem`; `_count_lineage`
runs at its bottom). Solving the four values:

| reading | value | implies |
|---|---|---|
| 1st | `1.000000` | 0 cycles worked (the empty-record rule) |
| 2nd | `1.000000` | after selection cycle 1: 1 worked, 1 seeded |
| 3rd | `0.500000` | after selection cycle 2: 2 worked, 1 seeded |
| 4th | `0.333333` | after selection cycle 3: 3 worked, 1 seeded — **throttle engages**, floor `0.5` |

The throttle engaging is what forced selection cycle 4 onto the seed, which is
why the heartbeat census shows exactly 2 seed cycles. So the policy read a
denominator of 3 while `self._cycles` stood at 3 + however many capability
cycles had already run. The two numbers are the same only in a run with no
capability cycles — which is exactly the class of run (epoch 1) where the
mechanism was measured working.

## Named invariant this defeats

CLAUDE.md, "Hard-won invariants": *the operator's seed question always wins
scheduler rank ties*. The wander cap is the budget-share sibling of that rule
(`DR-CON-scheduler-ranking`: "the wander cap is a CANDIDACY gate, never a rank
term"). A denominator that grows on cycles the gate can never see drives the
computed share toward zero for reasons the gate cannot act on, and drives the
DISCLOSED share nowhere at all, because it is not disclosed.

## Not the cause (ruled out)

- **Not a policy bug.** `wander_cap_v1` is arithmetic over the reading it is
  handed; it computed `0.333333` correctly from `cycles=3, seed_worked=1`.
- **Not a registry/selection bug.** `ATTENTION_ALLOCATION_POLICY` resolved to
  `wander-cap.v1` and `fallback_from` is absent from every epoch-6 record.
- **Not the manifest echo drop.** The dropped knobs
  (`run_manifest.py:2386-2387`) meant epoch 6 got the cap at its DEFAULTS
  rather than at a configured value. That is a real second defect (audit P10)
  and it is PARKED, not fixed here: it changes which floor was in force, never
  whether the floor's denominator was consulted. Epoch 6 would show the same
  4-of-24 accounting at any floor.
- **Not a `_select_problem` bug.** Selection stayed read-only and the stash
  discipline held; the four readings it did produce are correct.

## The design question the fix must answer first

Stated by the brief and answered in FIX.md, not here: should a capability cycle
advance the share denominator, consult the policy like any other cycle, or be
excluded so the share is computed over problem-selection cycles only?
