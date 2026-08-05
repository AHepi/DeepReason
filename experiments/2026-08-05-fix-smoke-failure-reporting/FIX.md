# Fix: give the smoke a scrubbed human-facing diagnostic channel, and keep artifacts on failure

Guarantee restored: **when the operational smoke fails, it reports what
happened — the child's output, the assertion that fired, and where the
artifacts are — without widening the closed, payload-free typed record.**

## Change sites (exhaustive)

1. NEW `_redact(text, *, repo)` — replaces the repository path and
   `TEST_CREDENTIAL` with fixed placeholders, using the same forbidden
   values `_assert_no_disclosure` already enforces. Every diagnostic
   below goes through it, so the new channel cannot become the
   disclosure the smoke exists to disprove.
2. NEW `_report_diagnostic(title, body)` — writes a delimited block to
   `sys.stderr`. Human-facing only; nothing parses it, and the typed
   record is untouched.
3. `_run`, `except subprocess.TimeoutExpired as error:` — bind the
   exception, report its partial `stdout`/`stderr` (redacted) before
   raising the unchanged `OperationalSmokeFailure`.
4. `main`, `except AssertionError as error:` — bind it, report
   `str(error)` and the traceback (redacted) before building the
   unchanged record.
5. `main` / `_finalize_operational_smoke` — thread a `keep` flag so the
   temp directory is retained on FAILURE too, and print its path. When
   retention is deliberate, `cleanup_completed` stays `True`: choosing
   not to delete is not a cleanup failure.

## Explicitly not changed

- **The v4 record's field set, stage/kind/detail vocabularies, or
  `OperationalSmokeFailure`'s signature.** Closed by design and pinned
  by `test_v4_diagnostic_fields_types_and_allowlists_are_closed`.
- **`_assert_no_disclosure`** — untouched, and the new channel is
  routed through the same forbidden values so it stays true.
- **T1's call-count pin** — the operator's sequencing; this tranche
  makes the failure legible, it does not make it pass.

## Regression artifact

`repro.py` must report **0 of 3** concealments, having reported 3 of 3.

## Existing tests at risk

`tests/test_wheel_operational.py` (108 tests) exercises `_run`, the
failure record and cleanup. The record's shape does not move, so they
must pass UNEDITED; if any fails, this fix is wrong.

## Estimated diff

~45 lines in 1 file. Under the 150-line budget.

## Approval gate

Class `defect`, ≤150 lines, no frozen surface (`scripts/` only).
**Proceeds to `dr-implement-fix`.**
