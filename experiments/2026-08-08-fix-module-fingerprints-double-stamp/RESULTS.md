# Results — module-fingerprints double-stamp (P1/P3, S1-S4)

Honest-ledger segments only. "Accepted does not mean true." Model prose
is never evidence; the pasted pytest/`verify_root` output above (and in
`VERIFY.md`) is.

## 2026-08-08 — diagnosed, reproduced, fixed, verified in one tranche

**What the record showed.** P3 (first parked
`experiments/2026-08-06-change-seat-census-s1/PARKED.md`, restated
unfixed through every rung since) named
`tests/test_module_fingerprints.py::
test_absence_is_valid_before_the_feature_and_presence_valid_after`
failing with `ValueError: too many values to unpack (expected 1)` on
committed root `run-a518e33a75507207633f864ba6a864b1`, which carries 2
`module_fingerprints` stamps after a `deepreason continue`.

**What was fixed, and why the WRITER was not the problem.** Three
tranches' worth of independent evidence — Rung S5's REQUEST.md C6
(fresh diagnosis of the per-instance idempotency guard), Rung S5's
SPEC.md Q5/A5 (the deliberate design decision to copy that guard and
write the sibling reader as a partition claim instead), and Rung S6's
live two-seat A/B run (`experiments/2026-08-08-live-two-seat-ab-s6/
RESULTS.md`, audit2, criterion (d): a continued run legitimately
carrying 2 byte-identical seat-bindings stamps, `replay_valid: true`)
— converged on the same conclusion for the sibling `seat-bindings.v1`
payload, and this tranche confirmed it applies identically to
`module-fingerprints.v1`: `Scheduler._module_fingerprints_recorded` is
a per-instance guard that legitimately re-fires across a continuation
boundary, both stamps on the offending root are byte-identical
(digest `ebe19641...`), and `verify_root` reports the root fully
valid. The test's `(payload,) = recorded_module_fingerprints(...)`
line asserted a stronger claim than the design ever promised — the
exact "census check expires; a partition check does not" pattern
`docs/map/SEAM-harness-x-verification.md`'s Traps section already
named this same test for once before (2026-08-05, a different
census-shaped claim).

**The fix:** rewrote the presence-half assertion as a partition claim
(at least one well-formed payload per stamped root), added a direct
offline regression test mirroring the sibling's own partition-claim
test, and extended (never deleted) the map's existing Traps entry with
this second chapter. No `src/` file changed; no frozen surface
touched.

**What the record now shows:** full gate 3400 passed, 0 failed, 7
skipped (749s) — the first fully green full-gate run in this
program's tranche history. `docs_verify.py`: 842 checks, 0 failed.
`verify_root` on the motivating root: unchanged, still `violations: []`.

**Residue — what remains unproven:** nothing for this tranche's own
goal (GOAL.md's success criterion is fully met and pasted in
`VERIFY.md`). P1/P2 (undeclared `jsonschema`/`pytest-xdist` dev
dependencies) remain open, out of this tranche's scope, unchanged from
every prior rung's own parking of them.

## Verdict

PASS. `GOAL.md` -> `DIAGNOSIS.md` -> `REPRO.md` -> `FIX.md`
(operator-approved) -> implemented -> `VERIFY.md`: PASS. Tranche
delivered.
