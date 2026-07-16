# Harness Specification v1.6 Amendment

## Status and scope

This amendment introduces the opt-in RunManifest v5 autonomous-inquiry
boundary. It does not reinterpret RunManifest versions 1 through 4. Tranche A
implements immutable attached evidence and model-proposed deterministic
simulation. Formalisation and autonomous research remain disabled.

The authority rule is:

> Code controls operational authority. Models control semantic invention.

## Frozen run input

A v5 run binds `run-input-manifest.v1` before it binds `run-manifest.json`.
The run input identifies the exact problem, criteria, evidence-dossier digest,
and optional brain snapshot. Every attached source has a content digest,
run-local blob reference, byte count, source card, and claimed provenance.
Source locators are never fetched during the run.

Binding is first-writer, lock-protected, atomic, and conflict detecting. A v5
manifest cannot bind until the run input, dossier, and all source blobs verify.
Every v5 reasoning work order carries the run-input digest.

Attached source bytes are untrusted data. Attachment creates separate source,
attackable reliability, and candidate-evidence records. Prompt inclusion does
not create support, refutation, reliability, or truth.

`dossier-pack-receipt.v1` records the deterministic query, originating work
order, state fence, candidates, selected and excluded source IDs, exact excerpt
digests, and packing-policy digest. Literal overlap, deterministic exploration,
and underexposure may influence attention only.

## Manifest v5 authority

RunManifest v5 requires:

- `workflow.controller.v2`;
- `active_inquiry` / `inquiry.active.v1`;
- `inquiry-capabilities.v1`;
- `conjecturer.turn.v5`;
- `control.event.v2`;
- a bound run-input digest;
- one complete `InquiryCapabilityPolicyV1`.

All capability bounds are finite. Simulation, attached evidence,
formalisation, and research default to disabled. Tranche A rejects enabled
formalisation or research. It rejects simulation without one exact frozen
toolchain, an offline runner profile, finite request/execution/source/input/
output/sample/step/wall/memory/follow-up limits, and deterministic seed policy.

Historical serializers and canonical hashes for v1 through v4 remain
unchanged.

## Model-facing simulation request

`conjecturer.turn.v5` may return candidates, a bounded context request, an
abstention, or semantic simulation proposals. Candidates and simulation
proposals may coexist. A simulation-only response is valid. Abstention cannot
coexist with a semantic proposal.

`SimulationProposalV1` contains a hypothesis, rival predictions,
discriminating purpose, assumptions, sealed input aliases, parameter sets,
requested observables, interpretation conditions, and semantic model source.
It cannot contain commands, paths, environment variables, routes, providers,
credentials, network targets, execution limits, token budgets, phases, or
status authority.

Two semantic modes are recognised:

- `declarative_numeric_v1` is a finite JSON expression language compiled into
  harness-authored Python. It can read only `parameters` and `sealed_inputs`
  and use a fixed arithmetic/comparison/select vocabulary.
- `sandboxed_python_v1` is syntax checked but cannot use the local runner. It
  fails closed unless a separately implemented and frozen certified container
  adapter is available. Tranche A provides no host fallback for model-authored
  Python.

## Capability process

Simulation advances only through canonical capability events:

`PROPOSED → VALIDATED → GRANTED or DENIED → COMPILED → DISPATCHED → SUCCEEDED or FAILED → RESULT_PACKAGED → CONSUMED`

The conjecture rule records `PROPOSED` and returns. It never executes a
simulation inline. The scheduler processes at most one capability item per
cycle, before selecting ordinary conjecture work.

Each transition binds the manifest, run input, policy, request, originating
work order, formal/scratch fence, previous transition, phase record, trigger,
budget delta, and canonical previous/next capability-process digest. Request,
execution, and result-follow-up budgets are consumed respectively by
`PROPOSED`, `DISPATCHED`, and `CONSUMED`.

`DISPATCHED` carries an immutable `SimulationWorkOrderV1`. The work order binds
the grant, compiled program, runner profile, template, backend, toolchain,
network denial, filesystem policy, seeds, output/sample/step limits, and exact
wall-time and memory ceilings. A runner cannot execute without that durable
record.

Denied, failed, interrupted, packaged, and unconsumed work remains replayable.
Duplicate dispatch and duplicate result consumption fail closed.

If replay finds a durable `DISPATCHED` work order without a receipt, it does
not guess that execution succeeded and does not silently rerun it. The
controller records `dispatch_interrupted`, packages an explicit unknown
operational failure, and sends that limitation through fresh reasoning work.

## Execution and epistemic status

The existing simulation verifier executes only harness-generated declarative
programs for the local profile. The worker uses a fixed command, deterministic
environment and RNG, bounded IPC, AST/builtin boundary, process isolation,
step/sample/output limits, and manifest-derived wall-time and memory limits.
Network access and candidate filesystem access are unavailable.

A successful receipt establishes only that the recorded program produced the
recorded output under the recorded inputs, seeds, toolchain, and limits. A
failed execution does not by itself refute the motivating hypothesis. The
checker validates execution and declared output shape; it does not decide
scientific interpretation.

## Fresh result work

A result is never injected into an in-flight provider call. The scheduler
creates a fresh, route-bound conjecture work order for the originating school
and includes the exact proposal, receipt, structured result, assumptions,
limitations, and provenance. Its prompt labels the data `RECORDED SIMULATION
OBSERVATION` and states the limited epistemic meaning.

The result is marked consumed only through a canonical consumption record that
names the fresh work order. Later schools and critics encounter the result only
through normal recorded context.

## Replay and verification

Replay reconstructs proposed, denied, granted, compiled, dispatched, failed,
succeeded, packaged, unconsumed, and consumed work. Root verification checks
the run input, dossier blobs, source/reliability/evidence separation, evidence
packs, controller v2 authority, transition hash chain, budget deltas, grants,
generated program, work order, runner identity, receipts, result packages,
fresh work, and single consumption.

Unknown provider or embedding usage is recorded as unknown, never zero.
