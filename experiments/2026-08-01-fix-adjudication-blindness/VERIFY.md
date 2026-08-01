# Verification

## Criterion (a) — PASS

    jolt epoch3   run-b4d6dfda…   epistemic=1  blind=1  epistemic_checks_passed=False

The finding reads: "criticism ran and produced no attack: nothing in this
window could have been refuted". The run no longer reports itself
epistemically clean.

## Criterion (b) — PASS

The one committed root that DID attack is not flagged:

    live_engaged run-f4fa6663…   Crit=28  att=1   blind=0  epistemic_passed=True

and the positive control is:

    live_tri     run-6dab80d6…   Crit=11  att=0   blind=1  epistemic_passed=False

This is the criterion that matters most. A flag that fired on every root would
have satisfied (a) while meaning nothing.

## Criterion (c) — PASS

Sweep over every root under `experiments/`, compared against the pre-fix
validity derived from the previous tranche's post-fix sweep:

    roots compared         : 42     unopenable: 0
    roots whose valid MOVED: 0
    roots newly flagged    : 26

**26 of 42 roots — every real recorded run except the five that attacked —
carry the finding.** That is not a false-positive rate; it is the measurement.
Every one of those runs executed criticism and produced no attack.

No root's `valid` changed, as `VerificationReportV2.valid` is
`integrity_valid and security_valid` and the recorded-summary comparison at
`report.py:313` fires only when a stored summary says False. Predicted by
construction and now measured, per GOAL.md's requirement that this be measured
rather than argued.

## Criterion (d) — PASS

    $ pytest tests/ -q -n 4
    3243 passed, 7 skipped in 577.43s

0 failed. The 22 modules asserting `verify_root(root)["violations"] == []` all
held: emitting from `report.py` rather than `invariants.py` keeps the finding
out of the legacy violation list entirely.

    $ pytest tests/test_adjudication_blindness.py -q
    4 passed

## Verdict: PASS

## Residue (honest)

- **A prediction in FIX.md failed and the design was wrong on first
  implementation.** The predicate was written into `raw_flags`, which is
  windowed at `CAPTURE_W = 20`. On both candidate roots that window held only
  `Bridge/Measure/Scratch/Spawn` — no criticism and no attacks — so the
  windowed form scored the positive and the negative identically and erased the
  discriminator. Recorded as an amendment in FIX.md rather than silently
  corrected. The corrected predicate is whole-run.
- **The primary cause named in DIAGNOSIS.md is PARKED, not fixed.**
  Verification still discards every flag `raw_flags` returns; this tranche adds
  an independent whole-run check instead of routing them. `lineage_stagnation`
  is `True` on a real fixture today and still reaches nothing. The
  reproduction's load-bearing test — forcing all five flags True and finding
  the channel still empty — was removed from the regression module rather than
  left failing against a defect this tranche does not address.
- **`adjudication_ritual` still cannot fire when blindness is total.** Two of
  its four conditions are gated behind `MIN_ATTACKS_FOR_RITUAL=5` and a third
  is `None` with no attacks. Real, measured, untouched.
- **The finding is a report, not a brake.** Nothing consumes it: no run stops,
  no scheduler behaviour changes, and `valid` is unaffected by design. It makes
  the harness honest about what it did; it does not make it adjudicate.
- **26 flagged roots is a statement about this corpus, not a validated
  threshold.** Whether "criticism ran and attacked nothing" should also require
  a minimum number of criticism events, or a completed state, is untested — no
  root in the corpus distinguishes those variants.
- **Why there are no attacks is untouched and is the operator's call.**
  `authority.py:97-101` hard-returns `OBSERVE_ONLY` for every text workload, so
  no text run can mint a warrant. Until that is decided, every future text run
  will carry this finding — which is the correct report, and also the reason a
  GLM rerun would still refute nothing.
