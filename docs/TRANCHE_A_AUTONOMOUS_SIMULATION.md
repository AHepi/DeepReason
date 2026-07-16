# Tranche A autonomous simulation

RunManifest v5 adds the first complete, bounded theory-to-test loop without
changing v1 through v4. Its governing rule is that models invent semantic
hypotheses and discriminators while the harness alone owns routes, budgets,
runners, files, seeds, lifecycle, and status.

The normative details are in
[`harness-spec-v1.6-amendment.md`](harness-spec-v1.6-amendment.md). Migration
and preparation instructions are in
[`AUTONOMOUS_SIMULATION_MIGRATION.md`](AUTONOMOUS_SIMULATION_MIGRATION.md).

## Boundary

A v5 run requires:

- a pre-bound `RunInputManifestV1` and `EvidenceDossierV1`;
- `ControlPlanePolicyV2` and `ContractVersionPolicyV2`;
- one finite `InquiryCapabilityPolicyV1`;
- an exact run-input digest in every manifest and work order;
- no enabled research or formalisation capability in Tranche A.

Attached source bytes are content addressed before the first model call. The
run never fetches their locators. A deterministic pack receipt records which
untrusted excerpts were shown; visibility is not evidence admission.

`conjecturer.turn.v5` may return candidates, context requests, abstention, or
semantic simulation proposals. It may request a simulation without fabricating
a candidate. Operational fields are rejected by the closed wire contract.

## Execution

The canonical lifecycle is:

```text
PROPOSED → VALIDATED → GRANTED or DENIED → COMPILED → DISPATCHED
→ SUCCEEDED or FAILED → RESULT_PACKAGED → CONSUMED
```

Conjecture records `PROPOSED` only. A later scheduler cycle makes the policy
decision and, when granted, persists a compiled program and simulation work
order before execution. A later cycle creates fresh result-consumption work.

`declarative_numeric_v1` is the active local mode. Its JSON expression tree is
compiled into harness-authored Python using a fixed numeric vocabulary and
sealed input roots. The existing verifier then runs that generated program
with deterministic seeds, bounded IPC, output, samples and steps, and
manifest-derived wall-time and memory limits.

`sandboxed_python_v1` does not execute locally. Syntax validation is not
authority; without a frozen certified container adapter the controller records
`runner_unavailable` and preserves the denial.

A successful result is a `recorded_observation` about the exact stored program,
inputs, seeds, toolchain, and limits. It is not universal proof. An operational
failure does not refute the motivating hypothesis.

## Offline acceptance

No provider call is required:

```bash
.venv/bin/pytest -q tests/test_autonomous_capability_preflight.py
.venv/bin/pytest -q tests/test_run_manifest_v5_inquiry.py
.venv/bin/pytest -q tests/test_evidence_dossier.py tests/test_evidence_dossier_replay.py
.venv/bin/pytest -q tests/test_simulation_compiler.py tests/test_simulation_capability_v5.py
.venv/bin/pytest -q
```

The suites cover pure preflight refusal, historical manifest stability,
immutable input binding, bounded evidence packing, forbidden authority fields,
proposal/execution separation, grant, denial, exhaustion, unavailable runner,
duplicate dispatch, deterministic success, operational failure, immutable
receipts, fresh result work, replay, and audit generation.

Tranche B (conditional formalisation) and Tranche C (autonomous evidence
acquisition) remain separate graduation-gated work.
