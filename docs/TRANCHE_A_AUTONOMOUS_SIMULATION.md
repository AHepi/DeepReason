# Tranche A autonomous simulation

RunManifest schema v5 adds the bounded theory-to-test loop. It does not enable simulation implicitly. Both the simulation capability and frozen-evidence attachment have typed, manifest-owned policies and default to disabled.

The ordinary conjecture turn uses `conjecturer.turn.v5`. A model may return candidates, a context request, an abstention, or semantic simulation proposals. A proposal contains a hypothesis, rival predictions, a discriminating purpose, declared assumptions, sealed input aliases or bounded JSON parameter sets, model equations or bounded source, requested observables, and interpretation conditions. It cannot carry a command, executable path, working directory, environment, network permission, route, token budget, or execution budget.

The controller records this lifecycle in the append-only capability event stream:

```text
PROPOSED → VALIDATED → GRANTED or DENIED → COMPILED → DISPATCHED
→ SUCCEEDED or FAILED → RESULT_PACKAGED → CONSUMED
```

Every transition binds the originating work order, manifest digest, capability-policy digest, request digest, previous transition, and one immutable formal/scratch fence. The compiled operation uses the existing `simulation-python` backend, a manifest-pinned local Python toolchain, a fixed trusted invocation, deterministic seeds, finite step and sample limits, a subprocess watchdog, bounded IPC and memory, no candidate file builtins, and no candidate imports. Network access is therefore unavailable to candidate code. Models never choose the operational command.

A successful receipt means only that the recorded program produced the recorded output under the stored inputs, seeds, checker, toolchain, and limits. It is a `recorded_observation`, not proof of a hardware or scientific claim. An operational failure is preserved and does not refute the motivating hypothesis. Results return only through a fresh, separately authorized reasoning work order.

## Manifest compilation

Compile schema v5 with a complete active control-plane policy using `conjecturer.turn.v5`:

```bash
deepreason config compile \
  --schema-version 5 \
  --workload-profile text \
  --control-plane-policy control-v5.json \
  --simulation-capability-policy simulation-policy.json \
  --simulation-toolchain python-toolchain.json \
  --frozen-evidence-policy evidence-policy.json \
  --rubric-policy forbid \
  --out run-manifest-v5.json
```

Omit the three simulation/evidence options only when intentionally compiling the disabled-by-default v5 boundary. An enabled `SimulationCapabilityPolicyV1` must name exactly one `ToolchainEntry` whose runner is `local` and whose `network` field is `false`. Its executable and version-output digest must identify the Python runtime that will execute the run. The frozen dossier stores bounded excerpts, provenance locators, source classes, and SHA-256 content identities. It is attached before the first provider call and cannot be extended after manifest binding.

The canonical text application writes these v5 process audits at termination:

```text
CAPABILITY_REQUEST_AUDIT.md
SIMULATION_RESULTS.md
THEORY_TEST_LINEAGE.md
RESEARCH_SOURCE_AUDIT.md
TOKEN_ACCOUNTING.json
REPLAY_VALIDATION.json
```

The theory-to-test report follows explicit result-package, fresh-work-order, provider-call, conjecture-output, abstention, and follow-on-request references. It does not infer causation from temporal adjacency. Unknown provider or embedding usage is marked `usage_known: false`; it is never silently recorded as zero.

## Offline acceptance tests

No provider tokens are required for these tests:

```bash
.venv/bin/pytest -q tests/test_simulation_capability_v5.py
.venv/bin/pytest -q tests/test_simulation_backend.py
.venv/bin/pytest -q tests/test_application_bridge_service.py tests/test_mcp_run.py
.venv/bin/pytest -q
```

The focused suites cover disabled-by-default authority, schema-only simulation turns, forbidden operational fields, malformed aliases, grant and denial, request exhaustion, unavailable runners, duplicate dispatch, deterministic success, missing observables, unsafe imports, bounded oversized output, finite step and sample limits, operational failure reinjection, fresh result work, audit generation, replay verification, and v5 grounded-bridge compatibility.

Tranche A does not add autonomous Lean scheduling or open-web research. Those remain gated Tranche B and Tranche C work.
