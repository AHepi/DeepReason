# VERIFY — the outcome, against GOAL.md's criterion

Phase: `dr-verify-outcome`. Offline only; the goal called for no live proof
(GOAL.md scope), and the capability channel is stochastic across identical
runs, so one live attempt would be inconclusive either way. The offline
regression is the proof, per CLAUDE.md's live-run rule.

## The answer to the design question, in one line

A capability cycle advances `self._cycles`, is counted OUT of the allocation
policy's governed denominator, and the policy is still consulted and disclosed
on it. The exclusion is arithmetic; it is not silence.

## What epoch 6's 4-of-24 accounting would have looked like under the fix

Derived, not asserted: `epoch6_accounting.py` in this directory reads the
AUDIT's own committed probe
(`experiments/2026-08-28-audit-run-problems/probes/q3_cycle_accounting.json`)
and runs its census through the shipped policy. Output committed at
`proof-epoch6-accounting.txt`:

| | as shipped | **under the fix** | consulted but diluted |
|---|---|---|---|
| readings emitted | **4** of 24 | **24** of 24 | 24 of 24 |
| terminal share | `0.333333`, then 20 cycles unrecorded | **`0.500000`** | `0.083333` |
| against floor | `0.500000` | `0.500000` | `0.500000` |
| throttle at the end | unknown — unrecorded | **not engaged** | **engaged** |
| throttle records | 1 | 1 | many |

Read across that row: **epoch 6 was never actually below its floor.** It
worked the operator's question on 2 of its 4 governed cycles — exactly at the
floor of 0.5 — and spent the other 20 cycles executing the simulation that
work had proposed. The record said `0.333333` and then went quiet, and the
shipped code had no way to say the run had recovered. Under the fix the record
says `0.500000` twenty more times, and a reader can see it.

The third column is the alternative this tranche rejected and is shown so the
rejection is checkable: consulting the policy without excluding the cycles
would have reported `0.083333` and throttled a run for spending cycles on the
operator's own experiment.

**Not claimed:** the interleaving of epoch 6's 20 capability cycles among its 4
selection cycles. That root is not on this branch. Nothing above needs it — the
governed denominator counts selection cycles, so every interleaving gives the
same answer, and `test_the_denominator_is_order_independent` is the proof of
that rather than an assumption.

## GOAL.md's four criteria

| id | criterion | verdict | evidence |
|---|---|---|---|
| **S1** | every cycle that advances `_cycles` either consults the policy or is excluded from its denominator, by a stated rule in the map | **PASS** | `test_capability_cycles_do_not_dilute_the_floor`; rule stated in `DR-CON-scheduler-ranking` and `DR-INV-signal-contract`, each with a mutation-proven `check:` |
| **S2** | the reading is emitted on EVERY cycle that advanced the counter | **PASS** | same test: 24 readings for 24 heartbeats (was 4) |
| **S3** | a run with zero capability cycles is byte-identical to today | **PASS** | `test_the_offline_spawner_reproduces_epoch_1_bit_for_bit` — epoch 1's 12 committed share values, 5 throttles, and the disclosure string `wander-cap.v1: seed-lineage share 0.3333 below floor 0.5000`, all unchanged |
| **S4** | deterministic given a configuration | **PASS** | `test_the_denominator_is_order_independent` — the same counts interleaved differently give the same governed trajectory |

## Mutation proof

Each production edit reverted in turn, `proof-mutation.txt` committed:

| mutation | result |
|---|---|
| M1 — the capability branch stops disclosing | 2 failed (S2 tests RED) |
| M2 — `_capability_cycles` stops advancing (cycles re-enter the denominator) | 3 failed |
| M3 — `wander_cap_v1` divides by all cycles again | 3 failed |
| M4 — the empty-record rule flipped to `0.0` | 3 failed, **including the epoch-1 pin** |
| restored | 20 passed |

The two new map `check:` blocks are mutation-proven separately
(`proof-map-checks.txt`): M1 fails `DR-CON-scheduler-ranking`'s structural
check with `AssertionError: the capability branch stopped disclosing`, and M3
fails `DR-INV-signal-contract`'s arithmetic check.

## Gate

- Ring while iterating: `tests/test_wander_cap.py` (20 passed),
  plus `test_channel_and_wander_modularity`, `test_signal_contract`,
  `test_allocation_signal_consumption`, `test_scheduler`, `test_rotation`,
  `test_controller`, `test_reflexive_discipline` — **101 passed**.
- Full gate at the boundary, run on the EXACT committed tree (`4b801172b`):
  **4407 passed, 6 skipped, 0 failed** in 13:36. The stated baseline was 4403
  passed; the delta is exactly this tranche's four new tests.
  `proof-gate.txt`.
- `python tools/docs_verify.py` on the same tree: **4 failed**, exactly the
  recorded baseline (3 shallow-clone `CON-run-identity.md`, 1 pre-existing
  `INV-frozen-surfaces.md:181`). No delta. Collected checks moved 1139 → 1143,
  the four this tranche added, all of them single-line so they are actually
  collected (`PARKED.md` §Q1). `--audit`: 0 findings. `proof-docs-verify.txt`.

## Residue — what remains unproven

1. **No live run exercised this.** The fix is proven against an offline fixture
   that reproduces epoch 1's committed trajectory bit-for-bit and epoch 6's
   census exactly. It has not been driven by a provider. Capability-channel use
   is stochastic across identical runs, so a single live attempt could miss the
   path entirely and would prove nothing either way.
2. **The counterfactual is arithmetic, not a replay.** The table above states
   what epoch 6's ACCOUNTING becomes. It does not claim epoch 6 would have
   SELECTED differently: it would not have, because under this rule the four
   selection cycles see the same readings they saw, and the fourth one throttled
   either way.
3. **The rule's own cost is real and stated, not hidden.** A run can spend
   twenty cycles on capability work with the floor none the wiser. FIX.md
   states this as a boundary, and the change puts `capability_cycles` on the
   reading so an alternative accounting is a registry entry rather than another
   scheduler edit.
4. **Two attention knobs are still unreachable from a `--run-manifest`
   launch** (`PARKED.md` §Q2 / audit P10). This tranche's tests set the floor on
   `Config` directly, so its proof does not depend on them — but an operator
   launching from a manifest still cannot choose a floor.
5. **67 map checks are never executed by `docs_verify`** (`PARKED.md` §Q1),
   7 of them in `INV-frozen-surfaces.md`. This tranche's own two checks were
   flattened to single lines and mutation-proven so they are not part of that
   set. The tool is untouched.

## Verdict

**PASS.** All four success criteria met, four mutations RED and restored GREEN,
map moved in the same commit with two checks that fail when the fix is reverted,
`docs_verify` at baseline.
