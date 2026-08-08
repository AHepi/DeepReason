# Fix: rewrite the presence half of the module-fingerprints reader test as a partition claim, not a single-unpack census

Guarantee restored: `recorded_module_fingerprints(harness)` returning
one payload per legitimate re-emission (e.g. across a `deepreason
continue` boundary) is READABLE and VALID — the test asserts "every
stamped root has at least one well-formed payload," never "exactly
one," matching what the writer (`Scheduler._record_module_fingerprints`,
mirrored deliberately by the sibling `_record_seat_bindings`) actually
promises and what Rung S6's live run already proved correct in
production.

Change sites (exhaustive):
  - `tests/test_module_fingerprints.py:64-93` —
    `test_absence_is_valid_before_the_feature_and_presence_valid_after`:
    (1) docstring gains a second regression note, alongside the
    existing rung-5 A/B one, naming this tranche's root
    (`run-a518e33a75507207633f864ba6a864b1`, P1/P3) and the mechanism
    (continuation re-stamping); (2) the presence-half loop changes from
    `(payload,) = recorded_module_fingerprints(...)` (exactly one) to
    iterating every payload the reader returns and asserting each is
    well-formed, plus `assert payloads, root` so the presence check
    still requires a non-empty witness (unchanged guarantee: an empty
    return on a root the sweep already classified "stamped" would still
    fail loudly). No change to `_sweep_committed_roots` itself — it
    already treats stampedness as a boolean (`if
    recorded_module_fingerprints(harness)`), not a count.
  - `tests/test_module_fingerprints.py` (new test, appended near the
    existing appender-behavior tests, e.g. after
    `test_the_appender_round_trips_through_the_log_alone`) — a new
    `test_recorded_module_fingerprints_is_a_partition_claim_never_a_
    single_unpack(tmp_path)`, mirroring
    `tests/test_seat_bindings_record.py::
    test_recorded_seat_bindings_is_a_partition_claim_never_a_single_
    unpack` line for line: two `harness.record_module_fingerprints(...)`
    calls on one fresh harness, then asserts
    `recorded_module_fingerprints(harness)` returns both, in append
    order (`[p.digest for p in got] == [first.digest, second.digest]`).
    This is the durable, offline, mutation-provable regression guard —
    REPRO.md's record-replay artifact proves today's committed root;
    this test proves the mechanism will not regress even if that root
    is ever retired.
  - `docs/map/SEAM-harness-x-verification.md` Traps section, the "A
    census check expires; a partition check does not" bullet (currently
    ends "...true only until the first run recorded after rung 4's
    writer was committed.") — appended, not deleted, per project
    convention: a second sentence naming this test's SECOND instance of
    the same pattern (exactly-one, not merely non-empty), the
    continuation mechanism that triggered it, and this tranche's fix
    (dated, with the tranche directory named), since the map moves in
    the same commit as the code that fixes what it documents.

Regression artifact: REPRO.md's
`python -m pytest tests/test_module_fingerprints.py::
test_absence_is_valid_before_the_feature_and_presence_valid_after -q`
must invert from `1 failed` to pass. New condition this fix must also
satisfy: the new partition-claim unit test passes and is mutation-
provable (reverting its assertion to a single-unpack must fail it,
proving it actually exercises the two-stamp case rather than passing
vacuously).

Existing tests at risk: grepped every `recorded_module_fingerprints`
call site in `tests/` (see DIAGNOSIS.md/this phase's grep). Five other
single-unpack/`len(...) == 1` sites exist in
`tests/test_module_fingerprints.py` (lines 333, 360, 394, 428, 431) and
two more in `tests/test_school_population_determinism.py:162-163` and
`tests/test_rung5_alternative_backend.py:242,247`. None are at risk:
each constructs exactly one fresh `Harness`/`Scheduler` in a `tmp_path`
and calls `.run(1)` exactly once with no `continue` boundary crossed —
"exactly one stamp" is a TRUE, unconditional guarantee for a
single-`run()` fixture, not the census-shaped over-assertion this fix
targets. None will be touched or need updating; the fix is scoped to
the one assertion that reads a COMMITTED, possibly-continued root.

Explicitly not changed:
  - `src/deepreason/scheduler/scheduler.py` /
    `src/deepreason/harness.py` — the writer is not defective per
    DIAGNOSIS.md; touching frozen surface 2 (`harness.py` event
    application) is out of GOAL.md's scope and this fix needs none of
    it.
  - Historical `PARKED.md` files in Rungs S1-S4
    (`experiments/2026-08-0{6,7}-*/PARKED.md`) — left exactly as
    written. They are the dated, honest-ledger record of what was
    parked AT THE TIME (CLAUDE.md: "Experiment narrative lives... as
    dated, honest-ledger segments"); retroactively editing a past
    tranche's own ledger to say "closed" would blur when the closure
    actually happened. This tranche's own `VERIFY.md` is the closure
    record instead, and can be handed to any future reader who greps
    P1/P3.
  - `tools/root_sweep.py` — already reports a `modules=` column derived
    from the same `recorded_module_fingerprints` call
    (comma-joined `module_id`s across every returned payload, `-` when
    empty); it does not unpack and needs no change.

Estimated diff: ~45-55 lines across 2 files (`tests/
test_module_fingerprints.py`: docstring rewrite ~8 lines changed + new
test ~18-22 lines; `docs/map/SEAM-harness-x-verification.md`: ~8-12
lines appended to one Traps bullet). Well under the 150-line budget.
No frozen surface touched.
