# Diagnosis: `single_family_trial` is the one authority value no caller can pair with a critic school, and the cross-school judge ensemble it was built for is not on the trial's solo path at all

## Stop report, section 4 (pasted verbatim, before anything of mine)

Source: the stub root built by `proof/stub_solo_config_path.py` — a one-model
configuration (one model id in every seat), two judge seats, a defender seat,
`ARGUMENTATIVE_AUTHORITY=single_family_trial` and
`ADJUDICATION_STATUS_AUTHORITY_ENABLED=True`, four cycles, mock endpoints.
Full report at `proof/STOP_REPORT_config_path.txt`.

```
## 4. THE STOP, CLASSIFIED

Stop message: `(none recorded)`

Boxes ranked by evidence:

### 1. HARNESS — NO EVIDENCE EITHER WAY

- note: not claimable:  still holds evidence. A harness verdict requires the other three to be ruled out.

### 2. CONFIGURATION — RULED OUT

- evidence RULING IT OUT: no ENGINE_CONFIG_FIELD_NOT_CARRIED notice was recorded; no run-config was supplied to diff against the manifest, so a mismatch there cannot be ruled out — re-run with --config to close that gap
- note: no manifest: nothing to compare

### 3. ENVIRONMENT — RULED OUT

- evidence RULING IT OUT: no HTTP 429, no transport-fault streak, and no qualification case carrying an environment failure code

### 4. MODEL — RULED OUT

- evidence RULING IT OUT: no qualification failure, no schema rejection and no truncation recorded against the implicated seats
```

The run did not stop: it completed four cycles, spent ten critic calls, and
recorded ten typed declines. Configuration, environment and model are ruled out
by the report; what remains is the harness's own arrangement, which is what this
diagnosis names.

Primary cause: the trial's solo path asks for a CRITIC SCHOOL, and
`single_family_trial` is reachable only from the caller that cannot supply one.
`informal/trial.py::_argument_trial_steps` branches on
`adapter.is_single_model()`, and its single-model branch demands two judge
leases, a `critic_school_id`, and a critic school differing from the target's
author school — it never consults `school_judge_bindings` and never calls
`require_cross_family_judges()`. Only two callers reach a trial.
`Scheduler._legacy_arg_crit` (`scheduler/scheduler.py:1655`) passes neither a
critic school nor an explicit authority, so it reads
`Config.ARGUMENTATIVE_AUTHORITY` — the only place `single_family_trial` can
arrive — and every trial it starts declines `no-critic-school`.
`Scheduler._foreign_arg_crit` (`scheduler/scheduler.py:1898-1906`) passes both,
but its authority comes from the frozen `criticism_policy.authority`, and
`rules/crit.py::_resolve_authority` refuses any value outside
`_POLICY_AUTHORITIES = {observe_only, defended_trial}` with
`ARGUMENTATIVE_AUTHORITY_NOT_MANIFEST_BOUND`. So `single_family_trial` names a
mode whose own guarantee its only caller cannot satisfy. The cross-school judge
ensemble (`llm/firewall.py::require_cross_school_judge_ensemble`,
`LLMAdapter.school_judge_bindings`) is dead for a second and independent reason:
`build_adapter` never populates the bindings, and even populated they are
selected only by `_select_judge_ensemble`, which the solo path does not call.

Evidence:
  - `proof/STUB_CONFIG_PATH.txt` (stub root, four cycles) -> `is_single_model:
    True`, `judge seats: 2`, `warrants total: 4 argumentative: 0`,
    `trial-declined:no-critic-school` x10. Zero argumentative warrants minted;
    the four warrants and four attack edges present are demonstrative, from the
    counterexample channel, which the operator's law never doubted.
  - `proof/STOP_REPORT_config_path.txt` §3 -> the critic seat took 10 attempts
    with 0 invalid and 0 zero-token responses. The model answered every time;
    nothing failed. The cases were recorded as scrutiny and then declined.
  - `proof/STOP_REPORT_config_path.txt` §6 -> "rounds of criticism that ran to
    the end: 5 of 5". A complete criticism pass that mints no argumentative
    warrant is the shape this defect has: nothing errors, nothing is missing,
    and the road is simply not there.
  - `tests/test_prose_refutation_boundaries.py::
    test_the_config_only_path_cannot_satisfy_the_cross_school_guarantee` — a
    committed, passing test asserting `declines == ["no-critic-school"]` for
    exactly this configuration. The defect has been pinned as intended
    behaviour since the 2026-08-01 tranche.
  - `docs/map/CON-schools.md` Traps, verbatim: "`ARGUMENTATIVE_AUTHORITY=
    single_family_trial` cannot complete a trial ... Parked as dead weight, not
    removed." And: "`require_cross_school_judge_ensemble` ... retained but
    superseded — correct only for a manifest that authors judge bindings, which
    the validator does not permit."
  - `docs/map/CON-schools.md:151` check (green today) -> `school_judge_bindings`
    occurs in `llm/adapter.py` and in no other file under `src/deepreason`.

Implicated code: `src/deepreason/rules/crit.py:73,79,100-113`
(`_POLICY_AUTHORITIES` / `_TRIAL_MODES` / `_resolve_authority`);
`src/deepreason/llm/adapter.py:270,295,692-706,1928-1944`
(`school_judge_bindings`, `_select_judge_ensemble`, `build_adapter`);
`src/deepreason/informal/trial.py:974-989` (the single-model branch that asks
for a critic school and never for a judge binding).

SECOND, INDEPENDENT FINDING — recorded here rather than parked, because the
success criterion depends on it: **a launchable one-model configuration CAN
already reach the trial and mint an argumentative warrant, through
`defended_trial` rather than through `single_family_trial`.** Measured, not
read:
  - `configured_criticism_policy(Config(N_SCHOOLS=2,
    LEGACY_CRITICISM_ENABLED=False, ADJUDICATION_STATUS_AUTHORITY_ENABLED=True,
    ENGAGED_CRITICISM_AUTHORITY="defended_trial"), "r-crit")` returns
    `authority='defended_trial'` with both schools bound to the critic seat.
  - `compile_run_manifest(...)` on that config with one model in every seat and
    two judge routes compiles to sha `ad6016bd73e456ee` carrying
    `criticism_policy.authority='defended_trial'` and emits NO
    `V4_CRITICISM_CROSS_FAMILY_JUDGES_REQUIRED` notice — the validator's
    same-model substitute (`len(judge_routes) >= 2` and `len(judge_models) == 1`)
    already covers a solo run.
  - `rules/crit.py:113` maps `defended_trial` -> `trial_required`, which is in
    `_TRIAL_MODES`, and the scheduler's school-routed path supplies the critic
    school the solo branch asks for.
This is the difference between "the law has no road" and "the law has a road
under a different name". Which one is true decides whether road (a) is a
capability gap being closed or a second road to the same place.

Falsifiable prediction: `dr-reproduce` must show BOTH halves on the same
one-model configuration and the same stub endpoints —
  (1) `python proof/stub_solo_config_path.py <root> 4`
      -> `argumentative: 0` and `trial-declined:no-critic-school` > 0;
  (2) a second stub root compiling the `defended_trial` manifest above and
      driving the school-routed criticism path
      -> at least one ARGUMENTATIVE warrant and a matching attack edge.
If (2) fails, the law has no road at all and road (a) is mandatory. If (2)
succeeds, road (b) removes a redundant declaration rather than narrowing the
law, and the FIX.md pricing must say so in those terms.

Ruled out: "the manifest validators refuse the judge school binding, and that
is what blocks the solo road" (SPEC.md M6's gate 2, and the first sentence of
this tranche's brief). They do refuse it — `V4_SCHOOL_ROLE_UNSUPPORTED` and
`V4_CRITICISM_ROLE_UNSUPPORTED` are emitted, and `resolve_school_route` refuses
again at dispatch — but that refusal is not ON the solo path: the stub root
above reached the trial and declined without any judge binding being consulted,
because `_argument_trial_steps`'s single-model branch never calls
`_select_judge_ensemble`. The judge-binding gates block a DIFFERENT road (a
single-FAMILY, MULTI-model run, where the else-branch runs
`require_cross_family_judges()` and the cross-school substitute is the only
ensemble available). Both are real; only the first is what `single_family_trial`
needs.
