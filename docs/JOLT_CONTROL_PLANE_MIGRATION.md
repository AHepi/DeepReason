# Jolt boundary and RunManifest v4 migration

This guide explains the operational boundary introduced after the recorded
Jolt failure. It is a migration guide, not a claim that a larger control plane
improves answer quality. The normative rules are in
[`harness-spec-v1.5-amendment.md`](harness-spec-v1.5-amendment.md); advisory
scratch and grounded-output rules remain in
[`harness-spec-v1.4-amendment.md`](harness-spec-v1.4-amendment.md).

## What changed

The repair separates authority from semantic model output.

| Concern | Semantic freedom retained by the model | Authority retained by code |
|---|---|---|
| Conjecture | claim, mechanism, counterconditions, analogy, uncertainty, context request, abstention | selected problem, school assignment, route, contract, budget, context grant, repair ceiling, admission transition |
| Criticism | open criticism and counterexamples | target eligibility, foreign-school coverage, route assignment, batch size, observe-only or defended-trial policy |
| Scratch | ideas may be used, ignored, contradicted, or abandoned | state fence, bounded selection, render receipt, expansion allowance |
| Repair | corrected rejected object or authorized subtree | same route, contract, evidence, fence, and attempt ceiling |
| Bridge retry | a fresh workflow may author a fresh ledger | same sealed catalog, prompt policy, contract, route, manifest, and bounded retry policy |
| Stop | model signals may be recorded as observations | the deterministic stop controller decides whether to stop |

Control records reference semantic records instead of copying them. They carry
no formal `StateDiff` and cannot grant a model-authored verdict.

## Compatibility matrix

| Manifest/profile | Conjecture actuation | School routing | Context request | Bridge retry | Historical guarantee |
|---|---|---|---|---|---|
| v1–v2 | historical scheduler | conditioning lineage only | unavailable | disabled | original canonical bytes and behavior |
| v3 | historical scheduler plus advisory/bridge policy | conditioning lineage only | unavailable to ordinary conjecture; advisory services remain available | disabled | original v3 contract; no synthesized v4 fields |
| v4 `legacy` | historical scheduler and wire contracts | `conditioning_only` | disabled | disabled | explicit v4 description of legacy behavior |
| v4 `shadow` | historical scheduler remains authoritative; reducer observes | manifest policy, without active conjecture cutover | disabled by the owned shadow profile | manifest-bound; disabled when the policy ceiling is zero | control comparison cannot change formal or scratch state |
| v4 `active_conjecture` | typed work order, provider receipt, guard, and transition authority | `conditioning_only` or `route_bound` | bounded grant/deny/exhaust with a fresh follow-up work order | v4 bridge ledger contract v2 and manifest-bound retry policy | only the conjecture boundary is actively migrated |

Never edit an old manifest in place. A v4 run requires a complete
`ControlPlanePolicyV1`; missing or incompatible controller, workflow,
capability, contract, school, or context fields fail validation.

## Choosing school execution semantics

Use `conditioning_only` when schools are distinct lineages or stances but one
shared conjecturer route is intentional. This mode has no school-seat bindings
and makes no route-diversity claim.

Use `route_bound` when each configured school must resolve to a specific
manifest seat. Bindings name `school-N`, role, seat, and endpoint identity.
Choose independently whether shared seats are allowed and whether models or
families must be distinct.

The durable proof is the combination of:

1. the bound manifest and digest;
2. the resolved endpoint lease;
3. `SchoolRouteReceiptV1`; and
4. the matching attempt route fingerprint in the recorded LLM call.

A school name in artifact provenance is not, by itself, route proof.

## Context policy

The conjecture context modes are:

- `disabled`: no controlled scratch context;
- `harness_only`: the harness may prepare the initial bounded advisory pack,
  but the model cannot request expansion; and
- `harness_plus_model_request`: the v4 turn may request bounded additional
  context through permitted retrieval channels.

A request can be granted only within `max_context_expansion_requests`,
`max_extra_blocks`, and the frozen channel policy. A grant creates a fresh
attention selection/render receipt and a fresh one-call work order. A denial
or exhausted allowance is recorded. Scratch remains non-authoritative in all
three modes, and no empty or irrelevant scratchpad is required to produce a
candidate.

## Local repair versus workflow retry

Local repair corrects a schema-invalid provider result inside one work order.
It is bounded to the rejected object or smallest authorized subtree and cannot
change route, contract, evidence, or state fence.

Workflow retry restarts the complete grounded bridge after a typed retryable
failure. It creates a fresh workflow and sink under the same sealed catalog,
composition request, prompt-policy digest, contract, route, and manifest. The
failed ledger is not supplied as the next attempt's input. A policy may allow
at most two retries; zero is the default.

These mechanisms have separate receipts and ceilings. A local repair attempt
does not consume or authorize a workflow retry, and a workflow retry does not
expand the local repair scope.

## Stop and resume status

The v4 controlled path records typed terminal stop lifecycle evidence around
the existing deterministic `StopController`. It binds controller state and the
workflow/checkpoint/outstanding-work snapshot used for the decision. Model
prose cannot stop a run.

Operational cancellation is a typed operator intent observed after a
completed cycle; it cannot interrupt a provider call or set status. A typed
`RESUMED` transition is implemented only for a typed deterministic converged
`STOPPED` decision with no outstanding or unconsumed work. Continuation binds
the same manifest, controller, and profile; the prior process and stop records;
the exact canonical checkpoint bytes; the event fence; and restored controller
state. The transition is persisted before new work and replays idempotently.
Completed, stuck, exhausted, budget, cancelled, and untyped historical stops
are refused. `PAUSED` remains unimplemented.

## CLI and MCP behavior

Compile a v4 manifest explicitly:

```bash
deepreason --config config/my-provider.yaml config compile \
  --schema-version 4 --workload-profile text --profile compact \
  --rubric-policy forbid \
  --control-plane-policy control-plane-policy.json \
  --out run-manifest-v4.json

deepreason config inspect --run-manifest run-manifest-v4.json
deepreason --root runs/v4-question reason \
  --text "Why might X happen?" \
  --run-manifest run-manifest-v4.json
```

The policy file is strict JSON matching `ControlPlanePolicyV1`. It is control
configuration, not a workflow program. Inspect the compiled role matrix and
digest before starting the run.

The narrow MCP `start_run` operation accepts a precompiled immutable manifest;
it does not compile source YAML or accept route overrides. `run_status`,
`run_result`, `continue_run`, and `cancel_run` retain their bounded operational
roles. Neither CLI nor MCP exposes a status setter, guard bypass, raw control
event writer, generic model invocation, or route editor.

CLI and MCP text runs translate their transport-specific inputs into the same
strict application intents. `TextRunApplicationService` owns start, continue,
progress/watch, cancellation, terminal results, locking, and text scheduler
dispatch. Scratch queries and grounded-bridge operations have matching shared
application services, including a separate mutating intent for direct scratch
open. The facades therefore do not carry competing execution loops. Do not
generalize these bounded services into one universal application service or
client authority over raw records.

## MiniReason

MiniReason keeps its reduced generate/check/rotate scheduler. It shares the
parent ontology, storage, route firewall, model profiles, wire/repair kernel,
scratch, attention, and grounded bridge; it does not gain full-engine trials,
research, website stages, or a duplicate workflow language.

Existing MiniReason roots and its default manifest path remain historical.
Opening them does not add v4 records. An explicit v4 `shadow` Mini manifest now
reuses the parent conjecture application boundary and exact canonical work
order, proposal, guard, and transition records for the overlapping generate
boundary. Mini still owns its reduced generate/check/rotate semantics and does
not implement active v4 turn/context-expansion behavior, full-engine trials,
research, or website stages. It must not be represented as fully controlled by
the `active_conjecture` reducer.

## What the implementation proves—and does not prove

Offline tests can establish that:

- authority fields are closed and replayable;
- route and work-order pairing fail closed;
- scratch remains non-authoritative;
- context expansion is bounded and creates fresh work;
- criticism prose cannot set status;
- local repair and workflow retry preserve their frozen boundaries; and
- v1–v3 fixtures retain their historical contracts.

Those tests do not prove that active control improves novelty, factual
correctness, explanatory quality, or cost. No live provider rerun is part of
this documentation change. A comparative claim requires separately authorized,
frozen, matched runs and must report semantic outcomes as well as control
correctness.
