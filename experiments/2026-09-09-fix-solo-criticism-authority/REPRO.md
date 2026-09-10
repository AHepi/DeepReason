# Reproduction

Form: unit-test (two stub roots driven through the real `Scheduler`, mock
provider seats, both roots replay-validated)

Artifact:
  - `proof/stub_solo_config_path.py` — the Config road
    `python -W ignore <artifact> <root> 4`
  - `proof/stub_solo_defended_trial.py` — the school-routed road
    `python -W ignore <artifact> <root> 2`
Both stubs use the SAME provider shape: one model id (`qwen3.5:397b`) in every
seat, two judge seats, a defender seat, two schools, the same seed question and
the same scripted critic case. The only difference is which caller reaches the
trial and which authority value it carries.

## Current output

Road 1 — Config's `ARGUMENTATIVE_AUTHORITY=single_family_trial`, master gate on
(`proof/REPRO_A_config_path.txt`):

```
is_single_model: True
judge seats: 2
warrants total: 4 argumentative: 0
attack edges: 4
trial/crit measures: Counter({'trial-declined:no-critic-school': 10})
```

Road 2 — the same one-model shape, criticism school-routed, authority
`defended_trial` frozen into a v6 manifest that compiles clean
(`proof/REPRO_B_defended_trial.txt`):

```
criticism authority: defended_trial
compile notices: ['ENGINE_CONFIG_FIELD_NOT_CARRIED', x3]
is_single_model: True judge seats: 2
warrants total: 1 argumentative: 1
attack edges: 1
  ARGUMENTATIVE warrant -> cbe3f6a6a96f43028d06540e7ee0734b68c9470abc22a6aca105ba1644d3e9e4
```

Both roots replay clean (`proof/REPLAY_VALIDATION.txt`):

```
rA violations= 0 warrants= 4 refuted= 2 accepted= 14
rB violations= 0 warrants= 1 refuted= 1 accepted= 5
```

The three compile notices are `ENGINE_CONFIG_FIELD_NOT_CARRIED` for
`ADJUDICATION_STATUS_AUTHORITY_ENABLED`, `ENGAGED_CRITICISM_AUTHORITY` and
`LEGACY_CRITICISM_ENABLED` — the disclosure that those knobs are not written
into the manifest bytes, which is the designed behaviour, not a refusal. No
`V4_CRITICISM_CROSS_FAMILY_JUDGES_REQUIRED` notice appears: the validator's
same-model substitute (two judge seats, one model) already admits a solo run.

Confirms diagnosis: yes, and it settles the fork DIAGNOSIS.md left open. Road 1
mints zero argumentative warrants and declines ten times with the typed reason
the diagnosis named (`no-critic-school`), while the model answered every call
(0 invalid, 0 zero-token, per the stop report §3). Road 2, on the same one-model
shape, completes a trial and mints an ARGUMENTATIVE warrant that becomes an
attack edge and a REFUTED status. So the operator's 2026-08-09 solo law is
SERVED TODAY — under `defended_trial`, not under `single_family_trial`. The
defect is not that solo runs are locked out of status-changing criticism; it is
that one declared value promises a road it cannot take, and a reader of
`Config` cannot tell which of the three values works.

Post-fix expectation, by road:
  - Road (a) WIRE IT: `proof/stub_solo_config_path.py` reports
    `argumentative: >= 1` and no `trial-declined:no-critic-school`, and a
    committed stub test asserts the warrant plus the typed disclosure for the
    switched gate. Road 2's output is unchanged.
  - Road (b) RETIRE IT: `single_family_trial` is absent from `Config`'s Literal
    and from `_TRIAL_MODES`; `proof/stub_solo_config_path.py` no longer
    constructs (the value is rejected at Config validation), and a committed
    stub test asserts Road 2's output — one argumentative warrant on a
    one-model configuration — as the law's road, with `docs/ERRATA.md` naming
    it.

## What this reproduction does NOT show

The judge-binding gates SPEC.md M6 names — `V4_SCHOOL_ROLE_UNSUPPORTED`,
`V4_CRITICISM_ROLE_UNSUPPORTED`, `SCHOOL_ROUTE_ROLE_UNSUPPORTED`,
`build_adapter` never passing `school_judge_bindings` — were never reached by
either stub, because `informal/trial.py`'s single-model branch does not consult
a judge binding at all. They are real refusals on a DIFFERENT road: a
single-FAMILY, MULTI-model run, where `_argument_trial_steps` takes its
else-branch into `require_cross_family_judges()` and the cross-school ensemble
is the only one available. That road is not what `single_family_trial` needs and
is not in this tranche's goal; it is priced in FIX.md and parked if unchosen.
