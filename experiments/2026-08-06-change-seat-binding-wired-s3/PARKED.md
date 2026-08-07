# Parked — found during Rung S3 (the binding, wired), not fixed

## P1 — pre-existing full-gate failure, not caused by this tranche (see S1's P3)

**Where found:** step 20, running `pytest tests/ -q -n 4` after all of
this tranche's code landed.

**What's broken:** `tests/test_module_fingerprints.py::test_absence_is_valid_before_the_feature_and_presence_valid_after`
fails with `ValueError: too many values to unpack (expected 1)` — a
continued root now carries 2 `module_fingerprints` payloads where the
test expects exactly 1.

**Already diagnosed, not this tranche's finding:** this is the
IDENTICAL failure already root-caused as P3 in
`experiments/2026-08-06-change-seat-census-s1/PARKED.md` (root
`run-a518e33a75507207633f864ba6a864b1`, the testphase root continued
via `deepreason continue --budget cycles=2`). See that entry for the
full reproduce steps and ready-to-run diagnosis pointer.

**Confirmed unrelated to Rung S3:**
```
$ git log --oneline b4327cc6..HEAD -- src/deepreason/harness.py src/deepreason/module_events.py tests/test_module_fingerprints.py
(no output)
```
This tranche's commits never touched any file that test depends on.

**Not fixed here:** same reasoning as S1's P3 — it is a
harness/continuation record question, not a seat-binding call-site
question; belongs to `deepreason-orchestrator`, already queued there
via S1's PARKED.md entry. Not duplicating that diagnosis in a second
place; this entry exists only to record that Rung S3's own gate run
hit the same known issue, not a new one.

## No other defects surfaced

Implementing `seat_bindings.py`, the CLI wiring, `_config_for_profile`'s
generalization, and the two callers' threading surfaced two BUGS IN
THIS TRANCHE'S OWN NEW CODE — both caught and fixed within the same
step they were introduced, never reaching a commit broken (see
CHECKLIST.md steps 5, 13, 14 for details): non-deterministic
`frozenset` iteration order in `resolve_seat_bindings`'s conflict
detection (fixed with `sorted()`), a self-inflicted import-block
corruption in `preparation.py` (caught by an import smoke-check before
committing), and a test-only `DEEPREASON_HOME` resolution mismatch
between `environ`/`home` forms of `provider_state_dir` (fixed in the
test, not the implementation — the implementation was already
internally consistent). None of these are open defects; all are closed
in the tranche's own commit history.
