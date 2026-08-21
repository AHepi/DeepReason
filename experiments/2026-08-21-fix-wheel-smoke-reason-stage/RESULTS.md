# RESULTS — wheel-smoke `reason`-stage terminal-verification failure

## 2026-08-21 — an unsatisfiable assertion, mistaken for a race

**Observed.** `python -u scripts/wheel_operational_smoke.py` failed at
`_assert_resumable_terminal` (`scripts/wheel_operational_smoke.py:2061`) with
`AssertionError: terminal verification is incomplete`, on an unmodified tree,
carried forward from `experiments/2026-08-16-change-embedder-auto-install/`
PARKED P1 as a FLAKY pre-existing defect.

**What the record shows.** Re-run with `--keep` at `c7e605553`, the retained
root `run-e9d4bb16796b8aa4b560c632b33d6500` answers the question the
assertion text cannot. Of the five conditions the assertion requires, exactly
two are false, and they are the same fact twice:
`verification.completion_satisfied` is `false` and `completion_status` is
`"incomplete"` (`application/models.py:1230` derives the second from the
first). `stop.reason` IS `"converged"`; `epistemic_checks_passed` and
`operational_checks_passed` ARE true; `integrity_valid`, `security_valid`,
`verification.valid` and `REPLAY_VALIDATION.json`'s `"valid"` are all true,
with a whole `terminal_binding`. The run reached a genuine, replay-valid,
converged, resumable terminal.

Its `finding_counts.completion` is exactly **1**, and re-deriving the report
names it: `model-phase-deferred | derived | phase
'premise-demarcation-variation' for role 'variator' was deferred
(transaction-contract-unavailable); target=premise-rent, obligation=-`. The
marker sits at log seq 34 — 195 events before the stop.

**Mechanism.** `Scheduler._premise_rent_step` runs on every cycle with no
state gate. A v6 manifest grants the trial roles (`defender`, `judge`,
`variator`) a behavioral contract only under `criticism_policy.authority ==
"defended_trial"`, and the public managed `deepreason reason` path seats a
`variator` while setting no criticism policy at all — confirmed on that run's
own manifest. So cycle 0 of every run down that path records a deferral,
`completion_satisfied` is `not self.completion`, and the flag can never be
true. The assertion demanded an outcome the design makes unreachable. It has
been unsatisfiable since `a476c564f` (2026-08-15) added the step.

**The flakiness was not real.** The prior tranche's three observations were
read as "pass, fail, fail". The pass never evaluated this assertion: that run
aborted at line 3447, inside `STAGE_MCP_REQUEST`, which the smoke reaches
before `_assert_resumable_terminal` at line 3565. Four separate sub-stages
set `stage = STAGE_REASON`, so the failure envelope's `"stage":"reason"` does
not identify which assertion ran. Counting only runs that reached it:
**4 evaluations before the fix, 4 failures; 3 after, 3 passes.** Recorded as
`docs/ERRATA.md` E34. The prior tranche's inference was honest and its
conclusions stand — the defect was pre-existing and correctly parked, and its
own ONNX-non-determinism hypothesis was refuted in its own record. Only the
word "flaky" was wrong.

**Fixed — in the instrument, not the harness.** The harness is doing what
three design records describe (`_defer_untransactional_v6_phase`'s docstring,
`v6_policy.py:170-179`, and the operator's all-configurations-allowed law:
disclose typed, never die). `_assert_resumable_terminal` now takes the run
root and compares `finding_counts["completion"]` against the number of
well-formed `v6-model-phase-deferred.v1` markers the run DECLARED in its own
log, mirroring `verification/report.py::_deferred_model_phase_findings`
including its malformed-marker branch.

This is not a weakening. Undeclared completion debt — budget-denied work, a
cancelled reasoning span, `foreign-criticism` coverage debt — still fails, and
so do a non-convergence stop, a failed epistemic or operational channel, a
broken integrity or security channel, a missing terminal commitment and an
unreadable event log. The original conditions survive in satisfiable form: a
run declaring no deferrals must still report `completion_satisfied: true`, and
`completion_status` must still agree with the debt. A 14-case mutation table
proves each; deleting the count comparison turns exactly its three count cases
red.

**Gate.** Full gate 3755 passed, 6 skipped, 0 failed. `docs_verify` 3 failed
(the recorded `CON-run-identity.md` shallow-clone baseline, unchanged);
`--audit` 0 findings; `--links` 0 dangling. `wheel_smoke.py` rc=0, no pin
moved. `wheel_operational_smoke.py` rc=0 three times.

**Residue.** `docs/map/` still owns nothing under `scripts/`, and that gap has
now produced this same class of defect twice; it is PARKED (P1) with three
priced roads rather than closed by invention. Whether
`_premise_rent_step` should run its free half when the variator is
uncontracted is PARKED (P2) as a question this tranche did not test. The
tranche's diff exceeded its own 150-line estimate at 276 insertions and that
verdict is surfaced, not absorbed. And green does not mean debt-free: the
smoke's run converged carrying one deliberately deferred phase, and the fix
asserts only that the debt matches the declaration — never that the phase
should have been deferrable at all.
