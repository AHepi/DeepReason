# Parked — Rung D1 (the pipeline census)

Noticed while running the full pytest gate at this tranche's boundary
(step 25) — deliberately NOT fixed here: this is a MEASURE ONLY
tranche; `src/`, `tests/`, `tools/` stay byte-untouched throughout, and
this session changed no code that could cause either failure below.

## P1 (pre-existing, already tracked elsewhere as "P1/P3"): `test_module_fingerprints.py::test_absence_is_valid_before_the_feature_and_presence_valid_after`

**What's broken:** fails with `ValueError: too many values to unpack
(expected 1)` — a continued committed root can carry 2
`module_fingerprints` payloads where the test's own
`(payload,) = recorded_module_fingerprints(...)` line assumes exactly
1.

**Not this tranche's finding — already diagnosed four times over:**
`experiments/2026-08-07-change-seats-in-record-s5/PARKED.md` names this
exact failure "tracked as P1/P3 in every one of Rungs S1-S4's own
`PARKED.md` files" (`experiments/2026-08-06-change-seat-census-s1/PARKED.md`,
`experiments/2026-08-06-change-seat-binding-wired-s3/PARKED.md`,
`experiments/2026-08-06-change-qualification-per-seat-s4/PARKED.md`).
This IS the "P1/P3" the operator's task message for this tranche named
in its acceptance line ("0 failed net of the named pre-existing
P1/P3") — confirmed by reproducing it here on a clean, zero-code-change
tree, with `jsonschema`/`pytest-xdist` installed locally (not
committed) so the gate could actually run to completion.

**Reproduce:**
```
pip install -e ".[dev]" --break-system-packages -q
pip install jsonschema pytest-xdist --break-system-packages -q
python -m pytest tests/test_module_fingerprints.py::test_absence_is_valid_before_the_feature_and_presence_valid_after -q
# ValueError: too many values to unpack (expected 1)
```

**Ready-to-send prompt:** "Diagnose and fix the harness/continuation
defect behind `tests/test_module_fingerprints.py::test_absence_is_valid_before_the_feature_and_presence_valid_after`
(`ValueError: too many values to unpack`, a continued root carrying 2
`module_fingerprints` payloads) — already reproduced independently by
five tranches (S1, S3, S4, S5, D1) without being fixed. Start from
`deepreason-orchestrator`/`dr-set-goal` with
`experiments/2026-08-07-change-seats-in-record-s5/PARKED.md`'s own entry
(candidate root cause: `run-a518e33a75507207633f864ba6a864b1`) as the
starting diagnosis."

## P2 (pre-existing, NEWLY connected to a gate failure): `test_continuation.py::test_a_stop_with_no_typed_receipt_refuses_continuation` fails because of S6's own PARKED P3 root

**What's broken:** fails with `AssertionError: failed-epoch1-run-8c77c6588485304d1f73416318c62949
stopped on 'operational_failure' and was refused for the wrong reason:
CONTINUE_RESUME_RECOVERY_MISMATCH` (expected
`CONTINUE_TYPED_STOP_REQUIRED`). The test scans every committed root for
a "non-resumable stop" witness and asserts each one is refused
continuation for the SAME typed reason; this root is refused for a
DIFFERENT typed reason than the test expects.

**Traced to:** `experiments/2026-08-08-live-two-seat-ab-s6/PARKED.md`
P3 — the exact same root
(`failed-epoch1-run-8c77c6588485304d1f73416318c62949`) is P3's own
named reproduction fixture for
`NonConjectureRecoveryAuthorityError("unknown critic task")`, a
`continue`-resume crash on a partially-decomposed criticism batch.
S6's own PARKED.md documents the LIVE-RUN defect (the crash itself) but
does not connect it to this specific offline gate test — this tranche's
own full-gate run at its boundary is what surfaces the connection: the
root's typed stop record (`operational_failure` /
`CONTINUE_RESUME_RECOVERY_MISMATCH`) is not the shape
`test_a_stop_with_no_typed_receipt_refuses_continuation` expects from a
non-resumable stop, so committing that root (necessary to keep it as
S6's own live reproduction fixture) broke this test for every tranche
that runs the full gate afterward.

**Not this tranche's finding, root cause — S6's own P3, dated
2026-08-08, same day, before this session started.** Not fixed here for
the same reason S6 itself did not fix it: `src/` stays byte-untouched,
and the right fix is a design decision about `continue`'s resume
semantics for a partially-decomposed batch (S6 P3's own language),
not a test-assertion patch.

**Reproduce:**
```
python -m pytest tests/test_continuation.py::test_a_stop_with_no_typed_receipt_refuses_continuation -q
# AssertionError: failed-epoch1-run-... stopped on 'operational_failure'
# and was refused for the wrong reason: CONTINUE_RESUME_RECOVERY_MISMATCH
```

**Ready-to-send prompt:** "`tests/test_continuation.py::test_a_stop_with_no_typed_receipt_refuses_continuation`
now fails because committed root
`experiments/2026-08-08-live-two-seat-ab-s6/home-s6/runs/failed-epoch1-run-8c77c6588485304d1f73416318c62949`
(S6's own `PARKED.md` P3 reproduction fixture) is refused continuation
for `CONTINUE_RESUME_RECOVERY_MISMATCH`, not the
`CONTINUE_TYPED_STOP_REQUIRED` this test expects from every non-
resumable stop. Diagnose whether the test's expectation is too narrow
(a second legitimate non-resumable-refusal reason now exists and the
test should accept it) or whether `CONTINUE_RESUME_RECOVERY_MISMATCH`
is itself a symptom of S6 P3's unresolved resume-semantics defect and
the test is correctly catching a real inconsistency. Start from
`dr-set-goal` with this entry and S6 `PARKED.md` P3 as the starting
diagnosis — do not patch the test's assertion without first deciding
which of the two readings is true."

## Not parked — worked around, not a defect

`jsonschema` and `pytest-xdist` are absent from `pyproject.toml`'s `dev`
extra (already fully diagnosed as rung4 `PARKED.md` P6a and S1
`PARKED.md`'s own entry — not re-diagnosed here). This tranche installed
both locally (`pip install jsonschema pytest-xdist --break-system-packages`)
to get a clean full-gate read; `pyproject.toml` itself was not touched
(out of this tranche's `src/`/`tests/`/`tools/`-only boundary anyway,
and the fix is already ready-to-run in rung4's own `PARKED.md`).
