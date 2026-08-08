# Parked — discovered during D2, not this tranche's to fix

One tranche, one goal (CLAUDE.md). Anything broken found while executing
this checklist that is not this tranche's own regression is recorded here,
never fixed in place.

## P-D2-1 — `test_a_stop_with_no_typed_receipt_refuses_continuation` fails on a pre-existing continuation defect

Discovered: step 25 (`python tools/docs_verify.py`, full sweep), while
verifying 0 failed before committing the map document update.

`tests/test_continuation.py::test_a_stop_with_no_typed_receipt_refuses_continuation`
fails:

    AssertionError: failed-epoch1-run-8c77c6588485304d1f73416318c62949
    stopped on 'operational_failure' and was refused for the wrong reason:
    CONTINUE_RESUME_RECOVERY_MISMATCH
    assert 'CONTINUE_RESUME_RECOVERY_MISMATCH' == 'CONTINUE_TYPED_STOP_REQUIRED'

Confirmed pre-existing and unrelated to this tranche: reproduces
byte-identically on a fresh worktree checked out at this tranche's own base
commit `f103a03a` (`dr-deliver-change: DELIVERY.md, D1 pipeline census
closed`), before any D2 code landed. `git diff --stat f103a03a -- \
src/deepreason/runtime/continuation.py src/deepreason/workflow/lifecycle.py \
scripts/wheel_operational_smoke.py` is empty for the whole D2 tranche —
nothing this tranche touched is anywhere near this failure's own machinery
(continuation/recovery-reason typing on a committed root's own stop_reason).
This matches the operator's own established shorthand ("S6 PARKED P1/P3")
for a recurring continuation-typing defect tracked across prior tranches,
per CLAUDE.md's own note on that naming.

Two `docs_verify.py` check lines depend on this same test and fail for the
same reason: `SUB-application.md:208` and `SUB-application.md:239`. Neither
document's own claim is wrong; the test itself is.

**Not fixed here.** Left for whichever tranche owns continuation/recovery
typing.

## P-D2-2 — `test_module_fingerprints.py`'s double-stamp defect (CLAUDE.md's own "P1")

Discovered: step 30 (`python -m pytest tests/ -q -n 4`, full gate).

`tests/test_module_fingerprints.py::test_absence_is_valid_before_the_feature_and_presence_valid_after`
fails:

    ValueError: too many values to unpack (expected 1)
        (payload,) = recorded_module_fingerprints(Harness(root, read_only=True))

Confirmed pre-existing: reproduces byte-identically on a fresh worktree at
this tranche's own base commit `f103a03a`, and matches CLAUDE.md's own
established shorthand for this defect ("the S6 PARKED P3 continuation
test" and, separately, "P1: `test_module_fingerprints`" — this tranche's
own CHECKLIST.md step 30 already named it in advance as a known,
already-tracked pre-existing failure). Nothing this tranche touched is
anywhere near `module_fingerprints`'s own recording/reading machinery.

**Not fixed here.**

## P-D2-3 — `test_bronze_report.py`'s gate_measures/gate_blocked mismatch

Discovered: step 30 (`python -m pytest tests/ -q -n 4`, full gate).

`tests/test_bronze_report.py::test_census_totals_internally_consistent`
fails:

    assert counts["gate_blocked"] == census["streams"][stream]["gate_measures"]
    AssertionError: assert 159 == 165

Confirmed pre-existing and unrelated: this test's own `census` fixture
(`scripts/bronze_census.py::build_census`) reconciles internal counts over
the RETAINED, committed `experiments/bronze_flat_2026-07-13/` roots — a
forensic report over historical logs this tranche never touched. Reproduces
byte-identically (159 == 165) on a fresh worktree at this tranche's own
base commit `f103a03a`; `git diff --stat f103a03a -- scripts/bronze_census.py
tests/test_bronze_report.py` is empty for the whole D2 tranche.

**Not fixed here.**
