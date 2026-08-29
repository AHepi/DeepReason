# FIX — one derivation for all four terminals, and a narrowly scoped reader

## Process note, recorded rather than hidden

This document was written AFTER the code, not before it. The orchestrator's
scope contract requires FIX.md first (clause 3, no phase-skipping), and this
tranche went from DIAGNOSIS.md straight to implementation. The consequence
was real and is visible in the record: the predicted-fixture list below is
partly retrospective — `test_results_command.py::
test_results_summary_reports_run_identity_state_and_budget` was discovered
at the ring rather than declared in advance, which is exactly the failure
mode writing the design first prevents. Nothing was weakened to accommodate
it, and the mutation proofs are unaffected, but the phase order was broken
and saying so is cheaper than the next reader inferring it from timestamps.

## F1 — `application/text_runs.py`: one derivation, shared by four terminals

New module function `log_token_spend(harness_or_root)`: the sum of
`event.llm.tokens` over the root's own log, accepting either a live harness
or a path (opened `read_only=True`). It replaces three hand-copied copies of
that expression and supplies the three failure terminals that had none.

Why a helper rather than three more copies: the defect is that four
terminals must agree and only one of them did. Three duplicated expressions
are three places the next terminal can forget.

Fail-safe: an unreadable log returns 0, which is the one case where no
evidence of spending exists to report.

The `harness is None` failure emit passes the ROOT rather than a harness,
because no harness was built. It matters that this is not simply left at 0:
a resumed root carries its earlier epochs' spend, and reporting zero for one
would understate the run by everything it had already spent.

## F2 — `application/results.py`: a NARROWLY scoped reader

`_token_spend(status, harness)` consults the log **only where the sidecar
says zero**, and reports a nonzero sidecar figure exactly as recorded.

- A root with no `run-status.json`, or with the key genuinely absent, still
  reports the typed absence `NO_RUN_STATUS_JSON`. The sentinel is preserved;
  deriving a 0 there would state a fact the record never held, which is the
  same class of error being fixed.
- The scope is narrow ON PURPOSE, and a regression pins it. The census found
  a SECOND class — nine roots whose nonzero figure is smaller than their log
  — with a different, un-diagnosed cause. A reader that derived from the log
  unconditionally would silently re-adjudicate those nine, answering a
  question (`RUN_ANATOMY_SYNTHESIS` organ 10's "three token instruments, 27
  disagreements") that nobody has yet asked. PARKED, with a ready-to-send
  prompt.

## The categorical argument: no committed root's verdict moves

1. **No committed root is written to.** F1 executes only while a run is
   terminating; F2 opens the root `read_only=True` and a regression asserts
   `run-status.json` is byte-identical after `results_summary` runs.
2. **No replay-validation output moves.** `verify_root`, `invariants.py`,
   `verification/`, `harness.py` and `capabilities/state.py` are untouched —
   the diff does not name them. Every committed `REPLAY_VALIDATION.json` and
   every stored verdict is unchanged.
3. **No digest input moves.** `token_spend` is a `progress.jsonl` /
   `run-status.json` field. Neither feeds a manifest schema, a capability
   digest, or a terminal commitment.
4. **`ProgressEvent` gains no field**, so nothing about historical
   `progress.jsonl` readability changes.
5. **The reported spend DOES change for 20 committed roots, and that is the
   fix.** Their bytes are untouched; the reader stopped repeating a zero the
   writer asserted without measuring. The truth was always in those roots —
   in the append-only log — and reading it is the only power a reader over an
   append-only record has, the same power `_adjudication` already exercises
   in that file.

## Frozen surfaces

NONE touched. Forecast held.

## Regressions, and how each is mutation-proven

| test | asserts | mutation that turns it RED |
|---|---|---|
| `test_a_failed_run_reports_the_spend_its_own_log_carries` | (a) WRITER — a run that logs 4 242 tokens then dies writes 4 242, not 0 | drop `token_spend=` from the ordinary failure emit → `proof/mutation1_red.txt` |
| `test_the_reader_recovers_the_spend_of_a_committed_root_stating_zero` | (b) READER — a committed false-zero root reports its log's figure, and its bytes are unchanged | reader trusts the sidecar unconditionally → `proof/mutation2_red.txt` |
| `test_a_nonzero_sidecar_figure_is_reported_as_recorded_and_not_re_derived` | the reader's SCOPE stays narrow | reader derives from the log always → `proof/mutation3_red.txt` |
| `test_a_run_that_genuinely_spent_nothing_still_reports_zero` | the control: a real zero survives | any fix that reports non-zero unconditionally |
| `test_a_root_without_a_status_record_still_reports_a_typed_absence` | the sentinel is preserved | returning 0 for an absent key |

**A mutation that did NOT hold on the first attempt, recorded because it
is the reason the test is trustworthy.** The scope test's first version used
a stand-in harness whose `log` property RAISED. `_token_spend` falls back to
the sidecar on any log error, so that test passed whether or not the log was
consulted — mutation 3 came back GREEN and exposed a test that could not
fail. Rewritten with a stand-in whose log reads cleanly and reports a
different number, plus a positive half asserting the same stand-in IS
consulted when the sidecar says zero. Mutation 3 then went RED.

## Fixture updates

- `test_results_command.py::test_results_summary_reports_run_identity_state_and_budget`
  asserted `summary["run"]["token_spend"] == status["token_spend"]` — that
  the reader parrots the sidecar, which IS the defective behaviour, on a
  fixture root that is itself one of the 20 false zeros. Updated to expect
  the log-derived figure where the sidecar says zero and the recorded figure
  otherwise, still derived from the root rather than from the reader's code.
  Found at the ring, not predicted — see the process note above.
