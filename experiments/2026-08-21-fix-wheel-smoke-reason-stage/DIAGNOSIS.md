# Diagnosis: the instrument over-specifies — `_assert_resumable_terminal` demands `completion_satisfied`, which the public `deepreason reason` path makes structurally unreachable

Primary cause: `Scheduler._premise_rent_step` runs on EVERY cycle and, on a
v6 manifest whose `criticism_policy` does not carry
`authority == "defended_trial"`, the `variator` seat has no behavioral
transaction contract, so the step calls
`_defer_untransactional_v6_phase("premise-demarcation-variation",
"variator", "premise-rent")` and returns. That call appends a
`v6-model-phase-deferred.v1` marker to the log on the first cycle.
`verification/report.py::_deferred_model_phase_findings` classifies every
such marker as a **completion** finding, and `completion_satisfied` is
`not self.completion`. The public managed `deepreason reason` path seats a
`variator` and sets no `criticism_policy`, so EVERY run down that path
carries at least one completion finding and can never report
`completion_satisfied: true` or `completion_status: "satisfied"`. The smoke's
`_assert_resumable_terminal` requires both. The defect is in the INSTRUMENT.

**The failure is deterministic, not flaky.** See "The flakiness was an
artifact of stage ordering" below — the one recorded "pass" never evaluated
this assertion.

## Which of the five conditions is false — from the record, not from the text

Run root `run-e9d4bb16796b8aa4b560c632b33d6500` (the smoke's
`RESUMABLE_STOP_QUESTION` run, `--cycles 12 --token-budget 200000`),
retained by `python -u scripts/wheel_operational_smoke.py --keep` on this
container at `c7e605553`:

| # | Condition the assertion requires | Record value | Verdict |
|---|---|---|---|
| 1 | `verification.completion_satisfied` is `True` | `false` | **FALSE** |
| 2 | `verification.epistemic_checks_passed` is `True` | `true` | true |
| 3 | `verification.operational_checks_passed` is `True` | `true` | true |
| 4 | `completion_status == "satisfied"` | `"incomplete"` | **FALSE** |
| 5 | `stop.reason == "converged"` | `"converged"` | true |

Conditions 1 and 4 are the same fact twice: `application/models.py:1230`
derives `completion_status` as `"satisfied" if
self.verification.completion_satisfied else "incomplete"`.

Everything else about the run is clean: `verification.valid: true`,
`integrity_valid: true`, `security_valid: true`,
`REPLAY_VALIDATION.json` `"valid": true`, state `completed`, stop
`converged` at cycle 9, 168 867 / 200 000 tokens. **The run reached a
genuine, replay-valid, converged, resumable terminal.** The only thing it
did not do is discharge one deliberately deferred model phase.

## Evidence

- `<root>/run-result.json` → `verification`:
  `{"completion_satisfied": false, "epistemic_checks_passed": true,
  "operational_checks_passed": true, "finding_counts": {"completion": 1,
  "epistemic": 0, "integrity": 0, "operational": 0, "security": 0},
  "integrity_valid": true, "security_valid": true, "valid": true}`;
  `completion_status: "incomplete"`; `stop.reason: "converged"`.
  **Exactly ONE completion finding.**
- `verify_root_report(<root>, _include_stored_verification=False)`
  re-derived on the retained root names that one finding verbatim:

      COMPLETION | model-phase-deferred | derived |
        phase 'premise-demarcation-variation' for role 'variator' was
        deferred (transaction-contract-unavailable);
        target=premise-rent, obligation=-

- `<root>/log.jsonl` seq **34** (first cycle):
  `('v6-model-phase-deferred.v1', 'premise-demarcation-variation',
  'variator', 'premise-rent', '-', 'transaction-contract-unavailable')`
  — one marker, recorded once, deduplicated by
  `_defer_untransactional_v6_phase`'s `_v6_deferred_model_phases` set.
- `<root>/run-manifest.json`: `schema_version: 6`,
  `criticism_policy: null`, `roles.variator` has 1 seat. The manifest's
  own `route_seat_bases` (in `REPLAY_VALIDATION.json`) list `variator`
  among the eleven seated roles.
- `run_manifest.py::_route_seat_behavioral_contract_assignments`
  (lines 2031-2050) grants `defender`/`judge`/`variator` a contract only
  under `_defended_trial_authorized`, i.e. `criticism_policy is not None
  and criticism_policy.authority == "defended_trial"`. With
  `criticism_policy: null` the variator seat exists with no contract, which
  is exactly the state `v6_policy.py:178` documents as "the seat qualifies
  `inactive_no_authorized_contract` and every phase that needs it defers
  `transaction-contract-unavailable`".
- The deferral is UNCONDITIONAL in the cycle body:
  `scheduler.py:2273` calls `self._premise_rent_step()` every cycle;
  `scheduler.py:2331` defers with no state predicate in front of it. The
  other twelve `_defer_untransactional_v6_phase` call sites ARE state-gated
  (`hv-spot-check` needs an unskipped artifact, `hv-floor` needs an
  `is_hv_floor` commitment, `vision-criticism` needs browser evidence) —
  which is why the smoke's other two roots
  (`run-909397ae…`, `run-a20f0b9e…`) carry three or four completion findings
  and this one carries one, and why no configuration of cycle count removes
  the premise-rent marker.
- Census of every committed root carrying a `verification.summary.v2` block
  (90 roots): `completion_satisfied` is `true` in 5, and all 5 stopped
  `operational_failure` with `finding_counts.completion == 0` — i.e. they
  died before any phase could defer. **Zero committed roots stopped
  `converged`.** No root in the repository has ever satisfied conditions 1
  and 5 together.

## The flakiness was an artifact of stage ordering, not non-determinism

`experiments/2026-08-16-change-embedder-auto-install/CHECKLIST.md` step 21
records three observations and concludes "the `reason` stage is FLAKY here"
from "my run 1 (passed), my run 2 (failed), base (failed)". Run 1 did NOT
pass this assertion — it never reached it. Run 1 died at
`wheel_operational_smoke.py:3447` with `AssertionError: durable CLI result
changed when retrieved through MCP`, and line 3447 lies inside
`STAGE_MCP_REQUEST` (`stage = STAGE_MCP_REQUEST` at line 3435, next
transition at line 3461), which the smoke reaches **before**
`_assert_resumable_terminal` at line 3565. Run 1 aborted upstream of the
assertion; it is silent about it, not a pass. Both stage labels read
`reason` in the failure envelope only for runs 2 and 3.

So the correct count is: of every smoke run that has actually EVALUATED
`_assert_resumable_terminal` on a tree at or after `a476c564f`
(2026-08-15, the commit that added `_premise_rent_step` and its
unconditional deferral), 100% have failed it. My own run on `c7e605553`
is the third such evaluation and it failed identically.

The prior tranche's "flaky" label was an honest inference from a stage name
in a failure envelope; the stage name is shared by four separate `reason`
sub-stages, which is the trap. This tranche's own conclusion is stated as
falsifiable and is being tested by two further full smoke repeats
(§Falsifiable prediction).

## Implicated code (max 3 sites)

1. `scripts/wheel_operational_smoke.py:2052-2065` — `_assert_resumable_terminal`,
   the over-specifying assertion. **This is the site to change.**
2. `src/deepreason/scheduler/scheduler.py:2313-2343` — `_premise_rent_step`,
   the unconditional per-cycle deferral (behaving as designed;
   `a476c564f`, 2026-08-15).
3. `src/deepreason/verification/report.py:1091-1129` +
   `report.py:77-79` — `_deferred_model_phase_findings` classifies deferral
   markers as `completion`, and `completion_satisfied` is `not
   self.completion` (behaving as designed and documented:
   "Expose deliberately deferred v6 model phases as completion debt").

## Why the INSTRUMENT and not the harness

The harness is doing precisely what three separate design records say it
should. `_defer_untransactional_v6_phase`'s docstring: "Optional legacy
scheduler phases must therefore become visible completion debt instead of
tripping that global guard and failing the whole root." `v6_policy.py:170-179`
documents seats without authority deferring. The operator's
all-configurations-allowed law (CLAUDE.md, 2026-08-12) is the same shape:
disclose typed, never die. A deferral marker is a DISCLOSURE that one
optional phase did not run — it is not a claim that the terminal is
defective, and the record proves the terminal is not: integrity valid,
security valid, replay valid, converged, resumable, and the smoke's own
subsequent continuation stage does in fact continue it.

`_assert_resumable_terminal` exists to prove that the run about to be
CONTINUED holds a committed, resumable convergence terminal. Completion
debt is orthogonal to that property. Requiring zero completion debt makes
the assertion unsatisfiable by construction on the public path — which is
the definition of an over-specified assertion, not of a broken run.

## Falsifiable prediction (what dr-reproduce must show)

1. Offline, with no smoke run: for a v6 manifest whose `criticism_policy`
   is absent (or whose authority is not `defended_trial`) but which seats a
   `variator`, `_route_seat_behavioral_contract_assignments` yields no
   `variator` assignment, and a scheduler cycle on that manifest appends
   exactly one `v6-model-phase-deferred.v1` marker for
   `premise-demarcation-variation`; `verify_root_report` on the resulting
   root reports `completion_satisfied is False` with a
   `model-phase-deferred` completion finding, while
   `epistemic_checks_passed`, `operational_checks_passed`, `integrity_valid`
   and `security_valid` are all `True`.
   Expected: the assertion's conditions 2, 3, 5 hold and 1, 4 fail — the
   same five-way split the record shows.
2. Live, as the repeat count: two further full
   `python -u scripts/wheel_operational_smoke.py` runs on `c7e605553`
   BOTH fail at `_assert_resumable_terminal` with
   `terminal verification is incomplete`, and their retained/observable
   `RESUMABLE_STOP_QUESTION` roots each carry exactly one completion
   finding, `model-phase-deferred / premise-demarcation-variation`.
   Expected: 3 of 3 evaluations fail. A PASS in either repeat REFUTES this
   diagnosis and sends the tranche back to `dr-diagnose`.

## Ruled out

**"A real race in terminalization."** The failure envelope has every
terminalization phase counter at 0 across
`terminalization_phase_entry_counts`, `…_error_counts`, `…_return_counts`
and `…_total_ms`, and `terminalization_last_error_family: "none"` — the
diagnostic ledger was never armed for this stage, so those zeros are
"not observed", not "observed zero". The positive evidence against a race
is the root itself: `REPLAY_VALIDATION.json` `"valid": true` with a complete
`terminal_binding` (commitment ref, ledger digest, result draft ref,
`terminal_commitment_event_seq: 229`, `terminal_epoch: 0`), and
`run-result.json` carrying `terminal_commitment_ref`. A terminalization race
leaves a missing or half-written commitment; this root's commitment is
whole, and the one thing that is "incomplete" is a completion finding
recorded at seq 34 — 195 events before the stop.

**"ONNX embedder non-determinism"** was already refuted in the prior
tranche's own record: the base worktree at `d52c739ff` does not declare
fastembed, measured with the hashing embedder, and failed identically.
Recorded here so the hypothesis is not re-picked-up.
