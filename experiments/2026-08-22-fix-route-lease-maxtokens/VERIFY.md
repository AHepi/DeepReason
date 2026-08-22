# Verification

## Criterion command + output

GOAL.md named three machine-decidable criteria. All three, verbatim:

    $ python -m pytest tests/test_route_lease_maxtokens_tuning.py -q
    .........                                                                [100%]
    9 passed in 0.15s

    $ python -m pytest tests/ -q -n 4
    3829 passed, 6 skipped in 933.26s (0:15:33)
    rc=0

    $ python tools/docs_verify.py
    docs_verify [full]: 62 documents, 976 checks, 4 workers
      FAIL CON-run-identity.md:200: ... (shallow clone: the referenced roots'
           rename history is not in this container's git objects)
      FAIL CON-run-identity.md:202: ... fatal: ambiguous argument '1637e808'
      FAIL CON-run-identity.md:204: ... fatal: ambiguous argument 'f304fec1'
    docs_verify: 3 failed

The gate baseline at `32492cdb8` was 3820 passed, 0 failed; 3829 is that
baseline plus exactly the nine tests this tranche adds. No MCP-thread flake
appeared in this run. The three `docs_verify` failures are the three the
tranche brief named as pre-existing: all in `CON-run-identity.md`, all
`unknown revision`, all caused by the shallow clone rather than by any claim
being false. Nothing this tranche wrote is among them.

Two further modes, both required before commit:

    $ python tools/docs_verify.py --audit
    docs_verify --audit: 0 finding(s)      # no check that cannot fail

    $ python tools/docs_verify.py --links
    docs_verify --links: 0 dangling reference(s), 62 document(s)

    $ python tools/docs_verify.py --coverage
    docs_verify --coverage: 7 seam(s) swept, 16 without a Sweep: header,
    2 finding(s)                            # both pre-existing, in
    # SEAM-periphery-x-verification and SEAM-schools-x-scratch;
    # SEAM-llm-x-scheduler swept clean.

## Mutation proof of the regression suite

Not a criterion, but the thing that makes the criterion mean something. Five
deliberate sabotages of the fix, each reverted immediately after measuring:

| Mutation | Test that died | Others affected |
|---|---|---|
| firewall ceiling deleted | `test_a_cap_above_the_qualified_lease_is_still_refused` | none |
| firewall equality restored | `test_controller_settling_a_qualified_seat_does_not_terminate_the_run` | none |
| propose-time clamp removed, apply-time kept | `test_an_applied_policy_states_the_cap_the_seat_actually_got` | none |
| both controller clamps removed | `test_the_controller_never_calibrates_above_a_qualified_lease` | none |
| ceiling made unconditional | `test_an_unqualified_seat_may_still_widen_past_its_configured_cap` | none |

Each mutation kills exactly one test and no others, so every distinct claim
carries its own witness and none is load-bearing for a claim it does not make.

## Reproduction, inverted

`repro.py` re-run on the fixed tree (`repro_after.json`, committed beside
`repro.json`):

| Case | Before | After |
|---|---|---|
| A/recorded — qualified route, controller narrows 32768 -> 20480 | `ROUTE_LEASE_MISMATCH ... expected=32768 actual=20480` | admitted |
| B/predicted — qualified route leased at 3000, truncation widening | `ROUTE_LEASE_MISMATCH ... expected=3000 actual=4800` | controller proposes nothing; cap stays 3000; admitted |
| C/control — unqualified route, same narrowing | admitted | admitted (unchanged) |

Case B's "controller proposes nothing" is the correct shape, not a suppressed
delta: the clamped proposal equals the current cap, so there is no change to
apply and no policy to emit.

## Historical roots re-checked

Two named roots, re-derived individually. **This is not a sweep** — the root
sweep is retired as an instrument (operator ruling 2026-08-22) and nothing here
requires one; single-root replays remain the permitted form.

| Root | Stored verdict | Re-derived on the fixed tree |
|---|---|---|
| `experiments/2026-08-22-live-reach-rich-run/run` (epoch 2, the defect) | `valid: true`, 0 violations | 0 violations |
| `.../failed-epoch1-run-40e713b3...` (epoch 1, same policy artifact) | `valid: true`, 0 violations | 0 violations |

No verdict moved, which is the expected result and worth stating as a
prediction met rather than an absence noticed: the fix leaves
`controller.cap_envelope` byte-identical, and that function is what
`invariants.py` re-derives to decide whether a logged policy value was
authorized. Had the ceiling been folded into `cap_envelope` instead, a policy
recorded above a qualified lease would have become unauthorized retroactively —
a moved verdict on a frozen surface.

## Live attempt

None, deliberately. In order of weight:

1. **GOAL.md's success criterion is offline in full.** The ladder of proof is
   ascended only as far as the goal requires, and it requires no live run.
2. **The instrument belongs to another tranche.** The reach-rich root is a
   frozen pre-registered experiment; relaunching it means retiring a committed
   root of a tranche this one does not own, and changing an instrument between
   its own epochs.
3. **A live attempt could not have proven this anyway.** Epoch 1 shows why: it
   emitted the byte-identical controller policy and then died of the P7-reach
   repair exhaustion before the firewall could refuse anything. A relaunch has
   a real chance of doing the same, which would be inconclusive for this path
   while consuming the run identity. The offline regression is the proof.
4. Contributing but not deciding: no `env` credential file exists in this
   container (`ls experiments/*/env` -> nothing), so a live run would need the
   operator's handover to recreate one.

## Verdict

**PASS** (offline; no live proof attempted, for the reasons above).

## Residue (honest)

- **The fix is proven offline, not live.** Nine mutation-proven tests and an
  exact offline reproduction of the recorded error string are strong evidence
  that this configuration can no longer die this way. They are not the same
  thing as a third epoch running past cycle 2. That remains unproven, and the
  next reach-rich relaunch is where it would be observed.
- **P7-reach is still open.** Epoch 1 died of repair exhaustion on the same
  frozen design, and this tranche did not touch the schema-repair machinery
  (a parallel window is working it). A third epoch can still die at cycle 2 —
  just not of *this* cause. Saying otherwise would claim more than the record
  shows.
- **The `dropped-call` mis-tagging survives**, parked as P1-lease. After this
  fix no lawful tune produces a firewall refusal, so nothing acts on it; the
  mechanism is intact if a future change reopens a path.
- **Case B has no live witness.** The widening direction is demonstrated only
  offline and is closed only by this tranche's controller clamp. No committed
  root has ever shown it, and none now can.

## Errata

`docs/ERRATA.md` **E42**, added in this commit. `SUB-scheduler.md`'s controller
Traps entry claimed the anchored barrier meant "the controller can never move a
cap past the operator's own setting", which was false for any seat assigned a
cap below the static ceiling. Corrected in place in the fix commit rather than
deleted, per the map's rule that a Traps entry is rewritten and never removed.

---

## Why a third epoch of the frozen design cannot die the way epoch 2 died

Because the only component that can move a leased seat's `max_tokens` mid-run
is now bounded by the same number the only component that can refuse it checks
against — that seat's leased cap — so the efficiency step which produced 20480
from 32768 is admitted by construction, and a step above 32768 is never
proposed.
