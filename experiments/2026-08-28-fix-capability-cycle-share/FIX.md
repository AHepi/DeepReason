# FIX — the accounting rule, stated, and the smallest change that enforces it

Phase: `dr-propose-fix`. Reads DIAGNOSIS.md and REPRO.md. No code changed yet.

## The design question, answered

> Should a capability cycle advance the share denominator at all, should it
> consult the policy like any other cycle, or should the share be computed
> over problem-selection cycles only?

**Answer: a capability cycle advances `self._cycles`, and is counted OUT of
the allocation policy's denominator. The policy IS consulted on it, and its
reading IS disclosed on it — the exclusion is arithmetic, not silence.**

The argument, and it is one argument, not a preference:

**The throttle's only lever is candidacy at problem selection.**
`DR-CON-scheduler-ranking` states this as the sharpest thing to know about the
cap: "the wander cap is a CANDIDACY gate, never a rank term … self-spawned
problems yield candidacy FOR THAT CYCLE". A capability cycle selects no
problem. There is no configuration under which throttling one means anything,
because there are no candidates to restrict. A floor whose denominator counts
cycles the floor cannot act on is not a floor — it is a number that falls for
reasons nothing can answer. REPRO.md shows what that number looks like:
`0.166667` on a run whose governed share is `1/1`.

**The rejected alternatives, and why.**

- *Count the capability cycle to the lineage of the problem its proposal was
  made under.* Defensible, and it is the option that would make the floor
  protect seed-lineage EXPERIMENTS as well as seed-lineage conjecture. Rejected
  here for two reasons. (1) It needs a proposal→problem→trigger attribution at
  three separate heartbeat sites, and any site where the attribution is absent
  silently counts as "other" — a floor that quietly penalises what it cannot
  attribute is the defect this tranche is fixing, in a new place. (2) It is not
  foreclosed: see "What this deliberately leaves open" below. This tranche
  makes it a policy decision rather than a scheduler decision, which is the
  precondition for taking it later without touching the scheduler again.
- *Leave the denominator moving and simply consult the policy on every cycle.*
  Rejected: it is the arm REPRO.md measured at `0.166667`. It would throttle a
  run for spending cycles on the operator's own experiment.
- *Leave it as today.* Rejected on the audit's own ground: the reading means
  something nobody chose, and the record is silent for the length of an
  experiment.

## Where the cut lives, and why not in the scheduler

`_count_lineage`'s own docstring already states the repo's rule for cuts like
this: *"An alternative cut is a different registered policy, not an edit
here."* `DR-REC-revise-allocation-policy` says the same from the other side:
*"A new throttle is a registry entry, never an edit to the scheduler."*

So the scheduler does not decide that capability cycles are excluded. The
scheduler REPORTS the fact — how many of its cycles were taken by a capability
step — and the POLICY decides what to do with it. `LineageReading` grows one
declared field; `wander_cap_v1` and `open_lineage_v1` divide by the governed
count. A future policy that wants option 1's attribution is then a registry
entry, exactly as the recipe requires.

This is a VERSIONED-layer change under `DR-INV-signal-contract` and it obeys
the FROZEN row untouched: the new field is a count of cycles. It reads no
status, no artifact, no warrant, no conjecture kind. `wander.py` still imports
nothing from `deepreason`.

## The change

**1. `src/deepreason/wander.py` — the reading carries the fact, the policy
uses it.**

- `LineageReading` gains `capability_cycles: int = 0`, defaulted so every
  existing construction (the suite's, the map's `check:` blocks') is unchanged.
  The partition it completes is exact:
  `seed_worked + other_worked + capability_cycles == cycles`.
- `reading_from` gains `capability_cycles: int = 0` and computes
  `other_worked = max(0, cycles - seed_worked - capability_cycles)`.
- `wander_cap_v1` and `open_lineage_v1` divide by
  `governed = cycles - capability_cycles`, with the same empty-record rule
  (`governed <= 0 → share 1.0, never engaged`).

With `capability_cycles == 0` every one of these is arithmetically identical to
today, which is S3.

**2. `src/deepreason/scheduler/scheduler.py` — the counter, and the
disclosure.**

- `self._capability_cycles = 0` beside `self._seed_cycles`, same comment
  block, same non-epistemic rebuildable status.
- `_wander_reading()`, a two-line private helper returning
  `wander.reading_from(config, cycles=self._cycles,
  seed_worked=self._seed_cycles, capability_cycles=self._capability_cycles)`.
  `_select_problem` keeps its literal `wander.decide(` call and its literal
  `self._pending_wander = decision` — both are pinned by `check:` blocks in
  `DR-CON-scheduler-ranking` and `DR-INV-signal-contract`, and neither moves.
- The capability branch in `step()` becomes:

```python
if self._simulation_capability_step():
    self._pending_wander = wander.decide(self.config, self._wander_reading())
    self._disclose_wander()
    self._capability_cycles += 1
    self._cycles += 1
    return
```

Order matters and is the same order the selection path uses: the decision is
computed from the counters BEFORE the cycle they describe is added, exactly as
`wander.decide` at the top of `_select_problem` runs before `_count_lineage` at
its bottom and before `_cycles += 1` in the cycle body.

## Why this cannot invent a throttle

The throttle record fires on the TRANSITION into engagement
(`_disclose_wander`: `if decision.engaged and not self._wander_engaged`). Across
a capability cycle neither `_seed_cycles` nor `governed` moves, so the decision
is identical to the previous cycle's and the transition cannot fire. Twenty
capability cycles produce twenty readings and zero throttle records. Asserted,
not argued: `test_a_capability_cycle_discloses_without_inventing_a_throttle`.

## What this deliberately leaves open (not a defect, a stated boundary)

Under this rule a run CAN spend twenty cycles on capability work with the floor
none the wiser. That is the honest cost of the answer and it is now visible
rather than hidden: the record carries a reading on every one of those cycles,
and the heartbeat beside it names the package being worked, so a reader can see
governed cycles and capability cycles diverge and say by how much. If the
operator later wants capability cycles attributed to their proposing lineage,
that is a new entry in `wander.LINEAGE_POLICIES` reading a field this change
puts in the reading — no scheduler edit, which is what
`DR-REC-revise-allocation-policy` requires.

## Acceptance

| id | check |
|---|---|
| S1 | `test_capability_cycles_do_not_dilute_the_floor`, `test_the_denominator_is_order_independent` GREEN |
| S2 | same tests: 24 readings for 24 cycles |
| S3 | `test_the_offline_spawner_reproduces_epoch_1_bit_for_bit` still GREEN, unchanged |
| S4 | `test_the_denominator_is_order_independent` — interleaving changes nothing |
| — | mutation proof: each of the two production edits reverted in turn goes RED |
| — | full gate 0 failed; `docs_verify` at its 4-failure baseline |

## Map documents that move in the same commits

- `DR-CON-scheduler-ranking` — the accounting rule, with a `check:` that fails
  if the capability branch stops consulting or disclosing.
- `DR-INV-signal-contract` — the reading's new field and the governed-cycle
  arithmetic, in the third-controller section.
- `DR-SUB-scheduler` — `_capability_cycles` in the counters it lists.
- `docs/ERRATA.md` — the audit probe's docstring claim that a capability cycle
  emits no heartbeat, minted from the tail.

## Size

Production diff: ~20 changed lines across two files. Well inside the stop line.
