# Parked — found during Rung S4 (qualification per seat), not fixed

## S4b — per-role provenance qualification (Option 1 from SPEC.md revision 1), parked as real future value, not required for correctness

**What it would do:** today (this rung's Option 2b), a heterogeneous
manifest is qualified as ONE combination subject — every distinct
`(default + bound-profile-set)` combination pays its own full battery,
even when every individual profile in it has separately been qualified
before. Option 1 would instead give qualification PER-ROLE PROVENANCE:
qualify each distinct profile once, and let any manifest that mixes
already-qualified profiles launch without a fresh combination battery.
This is a real cost optimization for operators who reshuffle seat
bindings often (N models, M combinations, currently M full batteries;
Option 1 would need only N).

**Why it is not required now:** SPEC.md's M5 (dispatch-purity
measurement, `tests/test_qualification_per_seat.py::
test_heterogeneous_manifest_dispatches_with_zero_cross_contamination`)
and M6 (`RunPreparationService.prepare` already refuses typed for an
unqualified combination, zero new code) together prove
combination-subject qualification is CORRECT, not merely convenient —
every heterogeneous manifest this rung's `deepreason qualify`/`status`/
launch path handles is dispatch-pure and typed-refusal-safe today.
Option 1 buys cost, not correctness.

**Why it is real frozen-surface-5 contact when eventually built:**
Option 1 requires `project_qualification_report` (`qualification.py`)
and the 5 `require_v6_production_qualification` call sites
(`cli/main.py`, `application/text_runs.py`, `ops.py`,
`bridge/transactional_adapter.py`, `scratch/authoring.py`) to accept a
report whose `subject_digest` was computed from a DIFFERENT profile set
than the launching manifest's own combination — i.e., a report stitched
together from N independent single-profile qualifications rather than
one battery run against the exact launching manifest. That is a
digest-equality-check redesign inside
`docs/map/INV-frozen-surfaces.md`'s named surface #5 (replay-validation
record formats), not a CLI-layer addition. This rung deliberately did
NOT touch that surface (S9, confirmed in VALIDATION.md); S4b's design
still needs its own `dr-spec-change` STOP and explicit operator
approval before any code lands.

**Ready-to-run entry point:** `dr-change-orchestrator`, starting from
`dr-capture-request` with this PARKED.md paragraph and SPEC.md
revision 1's "Option 1" section (superseded by revision 2's Option 2b
for THIS rung, but its design sketch — per-profile provenance records,
a combination-report synthesis step — is still the right starting
point for S4b's own `dr-spec-change`). Map ids to open with: `DR-CON-
seats`, `DR-SUB-manifest` (qualification subject digests),
`INV-frozen-surfaces.md`'s surface #5 entry.

## P1 — pre-existing full-gate failure, not caused by this tranche

**Where found:** step 21, running `pytest tests/ -q -n 4` after all of
this tranche's code landed.

**What's broken:** `tests/test_module_fingerprints.py::test_absence_is_valid_before_the_feature_and_presence_valid_after`
fails with `ValueError: too many values to unpack (expected 1)` on root
`run-a518e33a75507207633f864ba6a864b1` — a continued root now carries 2
`module_fingerprints` payloads where the test expects exactly 1.

**Already diagnosed, not this tranche's finding:** this is the
IDENTICAL failure already root-caused as P3 in
`experiments/2026-08-06-change-seat-census-s1/PARKED.md` and
re-confirmed unrelated (not fixed) in
`experiments/2026-08-06-change-seat-binding-wired-s3/PARKED.md`'s own
P1. See S1's P3 entry for the full reproduce steps and ready-to-run
diagnosis pointer (`deepreason-orchestrator`, a harness/continuation-
record question, not a call-site or qualification question).

**Confirmed unrelated to Rung S4:**
```
$ git log --oneline d6b8dea9~1..HEAD -- src/deepreason/harness.py src/deepreason/module_events.py tests/test_module_fingerprints.py
(no output)
```
This tranche's commits (from `d6b8dea9`, S4's first commit, through
HEAD) never touched any file that test depends on.

**Not fixed here:** same reasoning as S1's P3 and S3's P1 — it is a
harness/continuation record question, not a qualification-per-seat
question, and already queued for `deepreason-orchestrator` via S1's
PARKED.md entry. Not duplicating that diagnosis a third time; this
entry exists only to record that Rung S4's own gate run hit the same
known issue, not a new one.

## No other defects surfaced

Extracting `_cmd_qualify` into `_qualify_one_profile`, adding
`readiness.py::get_seat_readiness`/`SeatReadinessV1`, and extending
`_cmd_status` surfaced no new bugs reaching a commit broken — the
extraction was mechanical (proven byte-identical for the no-bindings
case at every step: import smoke checks, R6 pinning tests, and the
final before/after CLI-output + 45-root sweep diffs, all empty).
