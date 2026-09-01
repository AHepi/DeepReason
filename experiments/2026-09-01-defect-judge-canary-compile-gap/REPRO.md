# R1 reproduction: defended-trial intent compiles silently to observation only

Date: 2026-09-01

Tree under test: `3cb51b14e` plus record-only tranche files; no production code
had changed.

Command:

```text
python experiments/2026-09-01-defect-judge-canary-compile-gap/reproduce_compile_gap.py
```

Result: exit 1 (expected RED).

```json
{
  "carried_intent_notice": {
    "code": "ENGINE_CONFIG_FIELD_NOT_CARRIED",
    "message": "ENGAGED_CRITICISM_AUTHORITY='defended_trial' is not carried by this manifest's engine config and is restored at run time from this notice",
    "pointer": "/engine_config/ENGAGED_CRITICISM_AUTHORITY",
    "resolution": "/criticism_policy/authority",
    "value": "\"defended_trial\""
  },
  "effective_authority": "observe_only",
  "matching_compile_notices": [],
  "requested_authority": "defended_trial",
  "silent_gap": true,
  "stored_criticism_policy": null,
  "trial_contracts": {
    "defender#0": [],
    "judge#0": [],
    "judge#1": []
  }
}
```

The terminal assertion was:

```text
AssertionError: DEFENDED_TRIAL_NOT_COMPILED: authority will resolve observe_only; trial contracts will be empty
```

This reproduces the P-S1 builder call shape: the runtime configuration still
asks for `defended_trial`, but the builder omits the separate
`criticism_policy=` compiler argument. The manifest stores no criticism policy,
authority therefore resolves `observe_only`, all three trial seats have empty
behavioral-contract grants, and no compile notice names that consequence.
The carried-intent notice proves the P10 runtime-carriage repair is present;
the separate compiler-parameter gap is what remains.

The probe is also the mutation proof. It remains RED on the 2026-09-01 main
tree and must turn GREEN only when compilation delivers defended-trial policy
plus non-empty trial grants. A notice alone does not satisfy the corrected
operator requirement.

`observe_only` remains an intentional, optional per-run selection. R2 must add
an unchanged explicit-`observe_only` control: no derivation to defended trial,
no omission notice, and no default change.
