# Goal: the module-fingerprints reader-side regression test fails on a committed continued root

Class: defect

Observed: `pytest tests/test_module_fingerprints.py::
test_absence_is_valid_before_the_feature_and_presence_valid_after -q`
raises `ValueError: too many values to unpack (expected 1)` because
committed root `experiments/2026-08-05-testphase-live-validation/
home-testphase/runs/run-a518e33a75507207633f864ba6a864b1` carries 2
`module_fingerprints` stamps, and the test's `(payload,) =
recorded_module_fingerprints(harness)` line assumes exactly 1. Tracked
as P1/P3 in every `PARKED.md` since Rung S1
(`experiments/2026-08-06-change-seat-census-s1/PARKED.md` P3, restated
unfixed through Rungs S2-S4).

Map preflight (resolved ids): `DR-SUB-harness` (owns
`module_events.py`, the payload/reader this test guards),
`DR-SEAM-harness-x-verification` (owns the `record_*` seam and carries
a Traps entry for this exact test's first expiry — "a census check
expires; a partition check does not"), `DR-INV-frozen-surfaces`
(surface 2, `harness.py` — presumptively NOT touched by this tranche;
to be reconfirmed at diagnosis).

Success criterion (machine-decidable):
    python -m pytest tests/test_module_fingerprints.py -q
    0 failed
    python -m pytest tests/ -q -n 4
    0 failed (the first fully green run of the full gate recorded in
    this program's tranche history)

In scope: `tests/test_module_fingerprints.py` (the failing assertion);
`docs/map/SEAM-harness-x-verification.md`'s existing Traps entry for
this test (rewritten to add its second chapter, per project convention
a Traps entry is never deleted); the `PARKED.md` P3 entries this
tranche closes out. If diagnosis instead finds the writer
(`Scheduler._record_module_fingerprints` / `harness.py:
record_module_fingerprints`) defective, `src/deepreason/
scheduler/scheduler.py` becomes in-scope instead — determined by
`dr-diagnose`, not assumed here.

NOT in scope: `src/deepreason/seat_events.py` / the seat-bindings
sibling payload and its own reader (Rung S5, already delivered and
already written as a partition claim — informative precedent only, not
a target); any other frozen-surface change; P1/P2 (`pyproject.toml`
dev-dependency gaps) — separate, already-parked defects, not this
tranche's goal.

Budget: <=150 changed lines, 1 commit for the fix itself (plus one
commit per phase boundary for tranche artifacts), <=2 hours.

Stop conditions inherited from orchestrator: yes. Additionally: any
diff hunk touching `src/deepreason/harness.py`'s `_apply_event` or
well-formedness checks, or any of the other four frozen surfaces, is a
STOP regardless of how compelling the fix looks in the moment.
