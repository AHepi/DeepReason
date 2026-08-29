# GOAL — capability cycles bypass the wander cap while moving its denominator

Tranche opened 2026-08-28. Family: DEFECT (`deepreason-orchestrator`).
Branch: `claude/capability-cycle-share-fix-okwqgt`. Base: `90b1347f4`.

## Authority

Operator, 2026-08-28, approving the continuing program from the run-problems
audit. Brief: `experiments/2026-08-28-audit-run-problems/PARKED.md` §P12 and
`AUDIT_REPORT.md` §F-F, with `probes/q3_wander.json` and
`probes/q3_cycle_accounting.json`.

## Map preflight (resolved ids, recorded here so every later phase starts here)

Read in this order, before any design:

| id | why it is in scope |
|---|---|
| `DR-INV-frozen-surfaces` | forecast says none in this cone; re-checked, none |
| `DR-INV-signal-contract` | owns `wander.py`; the three layers decide what may move |
| `DR-CON-scheduler-ranking` | owns the candidacy gate and the read-only rule on `_select_problem` |
| `DR-REC-revise-allocation-policy` | the recipe any VERSIONED-layer move must follow |
| `DR-SUB-scheduler` | owns `scheduler.py`, `step()`, `_simulation_capability_step` |
| `DR-SUB-capabilities` | the simulation controller whose steps consume the cycles |
| `DR-SEAM-capabilities-x-rules`, `DR-SEAM-scheduler-x-rules` | the two seams the cycle body crosses |

Frozen-surface check: the cone touches `scheduler/scheduler.py`, `wander.py`,
tests and map documents. None of `capabilities/state.py`, `harness.py`,
`invariants.py`, `verification/`, `run_manifest.py`, `qualification.py` or
`llm/firewall.py::route_fingerprint` is in it. No committed digest pin moves.

## The defect, in one sentence

`scheduler.py:2052-2054` returns from the cycle body when
`_simulation_capability_step()` handles the cycle — before `_select_problem()`
(where `wander.decide` runs) and before `_disclose_wander()` — while still
doing `self._cycles += 1`, so every capability cycle advances the seed-lineage
share's DENOMINATOR without advancing `_seed_cycles` and without consulting or
disclosing the policy.

## What the record shows (evidence, not reading)

`experiments/2026-08-28-audit-run-problems/probes/q3_cycle_accounting.json`
and `probes/q3_wander.json`, both committed:

- epoch 1: 12 cycles, 12 `allocation.seed-lineage-share.v1` readings,
  5 throttles; share trajectory
  `1.0, 1.0, 0.5, 0.333, 0.5, 0.4, 0.5, 0.429, 0.5, 0.444, 0.5, 0.455`.
- epoch 6: 24 cycles, **4** readings, 1 throttle (cycle 3,
  `share 0.3333 below floor 0.5000`), then 20 cycles of silence.
  Heartbeat census: 19 `simulation-result:`, 1 `simulation-request:`,
  2 seed, 1 `disc:`, 1 `conn:` — 20 capability + 4 selection = 24.

## Success criterion (falsifiable)

A run whose capability steps dominate must satisfy all four:

1. **S1 — no ungoverned denominator.** Every cycle that advances
   `self._cycles` either consults the allocation policy or is excluded from
   that policy's denominator, by a stated rule recorded in the map.
2. **S2 — no silence.** `allocation.seed-lineage-share.v1` is emitted on
   EVERY cycle that advanced `self._cycles`, capability cycles included, so a
   reader can tell stability from silence.
3. **S3 — epoch-1 behaviour preserved bit-for-bit.** On a run with zero
   capability cycles, every emitted reading, every throttle record and every
   policy artifact is byte-identical to today's, including the policy id
   string `wander-cap.v1` inside the disclosure.
4. **S4 — deterministic given a configuration.** No wall-clock, no ordering
   dependence beyond the already-deterministic capability queue.

## Out of scope — PARKED, not fixed here

- The manifest echo dropping `SEED_PROBLEM_BUDGET_FLOOR` and
  `ATTENTION_ALLOCATION_POLICY` (`run_manifest.py:2386-2387`). That file
  belongs to the parallel manifest window and to audit finding P10. Recorded
  in this tranche's `PARKED.md`. This tranche's testability does NOT depend on
  it: the regression tests set the floor on `Config` directly, as
  `tests/test_wander_cap.py` already does.
- Anything about criticism, repair, lifecycle or the manifest surface.

## Stop lines

Any frozen surface or committed digest pin moving; a diff beyond ~150 changed
lines of production code; evidence contradicting the diagnosis.
