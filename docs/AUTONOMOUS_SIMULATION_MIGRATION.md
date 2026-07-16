# Autonomous Simulation Migration

## Why v5 exists

Versions 1 through 4 cannot express the complete authority needed for a model
to propose a test, have the harness execute it, and reason from the immutable
result. They remain unchanged. A run that requires that topology must fail
preflight with `AUTONOMOUS_CAPABILITY_TOPOLOGY_UNAVAILABLE` unless it selects
v5.

The stopped 2026-07-16 preflight is preserved under
`experiments/autonomous_inquiry_preflight_2026-07-16/` as an offline regression
fixture. Preflight performs no manifest binding, run-root creation, provider
call, or executor call.

## Preparing a v5 run

1. Stage every attached source into the intended run root with
   `stage_attached_source`.
2. Construct `EvidenceDossierV1` and `RunInputManifestV1` for the exact problem
   and criteria.
3. Call `bind_run_input` before compiling or binding the run manifest.
4. Construct `ControlPlanePolicyV2`, `ContractVersionPolicyV2`, and one
   `InquiryCapabilityPolicyV1`.
5. If declarative simulation is enabled, freeze one exact local Python
   toolchain and select `simulation.declarative.v1`. Set every capability
   limit explicitly.
6. Compile RunManifest v5 with the exact run-input digest and bind it to that
   same root.
7. Launch the ordinary canonical text workflow.

The text application verifies that the workload problem, criteria, dossier,
manifest, and bound run input all agree before starting its worker.

## Compatibility

- Do not add v5 fields to v1-v4 documents.
- Do not select `conjecturer.turn.v5` through `ContractVersionPolicyV1`.
- Do not use the abandoned split `simulation_capability_policy` or
  `frozen_evidence_policy` fields for new v5 manifests.
- Do not reinterpret `ReasoningWorkloadSpec.sources` as a v5 evidence dossier.
- Do not manually invoke the simulation CLI for a v5 inquiry proposal.
- Do not inject a result into an existing provider call.

## Available and unavailable modes

`declarative_numeric_v1` is active and offline-testable. It accepts JSON of the
form:

```json
{
  "schema": "declarative-numeric.v1",
  "observables": {
    "bytes_per_second": {
      "op": "mul",
      "args": [
        {"input": "parameters.bytes_per_token"},
        {"input": "parameters.tokens_per_second"}
      ]
    }
  }
}
```

`sandboxed_python_v1` remains unavailable for execution until a certified,
manifest-bound container adapter is implemented. Validation does not imply
execution authority, and there is no local-host fallback.

Formalisation and research are explicitly disabled in this tranche. They must
receive separate versioned proposal, controller, runner, result, replay, and
graduation work before being enabled.

## Offline acceptance

The Tranche-A suite covers:

- pure preflight refusal with no run artefacts;
- historical manifest hash stability;
- conflict-safe run-input binding and replay;
- bounded deterministic evidence packing and underexposure resurfacing;
- rejection of model-authored commands and authority fields;
- simulation-only model turns;
- proposal/execute/follow-up separation across scheduler cycles;
- grant, denial, exhaustion, unavailable runner, invalid program, duplicate
  dispatch, execution failure, packaging, and single fresh consumption;
- no host fallback for model-authored Python;
- epistemic separation between execution success and general support;
- complete root verification and canonical audit generation.

No live provider call is needed for these tests.
