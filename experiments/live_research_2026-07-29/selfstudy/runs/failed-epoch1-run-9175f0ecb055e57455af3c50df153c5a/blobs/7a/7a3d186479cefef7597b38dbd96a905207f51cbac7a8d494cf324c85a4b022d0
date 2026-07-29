# Conjecture–Criticism Harness — v1.5 normative amendment

**Status: normative for explicitly selected RunManifest v4 behavior.** This
document amends
[`harness-spec-v1.3.md`](harness-spec-v1.3.md) and
[`harness-spec-v1.4-amendment.md`](harness-spec-v1.4-amendment.md). It does not
rewrite either historical contract. Versions 1–3 of `RunManifest` retain their
established serialization and execution semantics; the authority boundary in
this amendment is opt-in through a complete v4 control-plane policy.

This amendment separates four concepts that reports and operators must not
collapse: school lineage, route topology, advisory attention, and workflow
authority.

## A. School lineage and route topology

A school is a conditioning lineage. It names a stance, ancestry, and history of
generated work. A school is not inherently a provider, endpoint, model, model
family, or route seat. School count therefore proves neither route diversity
nor model diversity.

RunManifest v4 has two school execution modes:

- `conditioning_only` preserves the historical meaning. Multiple schools may
  condition calls sent through the same role route. It carries no school-seat
  bindings and MUST NOT be reported as model- or route-diverse merely because
  several lineages exist.
- `route_bound` binds every configured school and supported role to one exact
  manifest seat and endpoint identity. Shared seats remain legal only when the
  policy explicitly permits them. Distinct-model or distinct-family
  requirements are separate, explicit constraints.

The harness MUST resolve a complete school batch before provider dispatch. A
missing, duplicate, out-of-range, or mismatched binding fails before partial
provider spend. Model text cannot select or replace a school, seat, endpoint,
provider, model, or family.

Evidence of actual route use consists of the immutable manifest binding plus
the call's route lease and `SchoolRouteReceiptV1`. Reports MUST distinguish
foreign-school coverage, distinct-route coverage, and distinct-model coverage.
Two school-owned calls through the same model remain valid coverage but are not
route-diverse.

## B. Scratch attention and bounded model recourse

The v1.4 scratch non-authority rules continue unchanged. Scratch blocks,
links, clusters, guides, similarity observations, and attention choices are
advisory. They cannot establish truth, grounding, support, attack, identity,
status, or promotion into the formal graph.

When enabled, ordinary conjecture work may receive a bounded advisory context
planned against one formal/scratch event fence. The harness commits the
selection and render receipts only at the actual render boundary. A stale plan
must be rejected and rebuilt. A failed provider call may still leave an honest
receipt proving what was rendered.

RunManifest v4 may grant the conjecturer a bounded `ContextRequest`. Such a
request is semantic input to the controller, not an executable command. It may
name bounded query text, aliases already visible in the call, permitted
retrieval channels, and an optional purpose. It cannot name paths, tools,
commands, providers, routes, budgets, status changes, or workflow phases.

The deterministic harness may grant, deny, or exhaust the request under the
frozen capability and context limits. A grant creates a new attention plan and
a fresh one-call work order with a decremented expansion allowance; it does not
reuse the original provider authorization. A denial creates a typed process
record and does not force a candidate. An abstention or no-proposal outcome is
recorded as search/process information and creates no formal artifact.

Candidate content remains open. Claims, mechanisms, counterconditions,
analogies, uncertainty, and optional semantic fields are not restricted to a
closed mechanism vocabulary. Every candidate still passes the existing
anti-relapse and formal registration path.

## C. Authority envelope and control replay

RunManifest v4 defines a small, strict authority envelope around role-specific
semantic contracts. The canonical records include:

- `WorkOrderEnvelopeV1`, containing state fences, problem/target references,
  school assignment, exact route lease, contract, bounded capability grant,
  budget reservation, repair policy, and a task-payload reference or value;
- `ProposalReceiptV1`, recording the returned payload references, validation
  outcome, attempt count, route, contract, and token spend;
- `GuardResultV1`, authored by deterministic code rather than the model;
- `RepairWorkOrderV1`, authorizing one subordinate local repair; and
- `TransitionDecisionV1`, binding the previous and next process-state digests,
  trigger, transition, route, capability consumption, and budget delta.

Authority fields are closed and reject unknown keys. The task payload remains
in its existing role-specific semantic schema; it is not copied into a generic
workflow language. Model output cannot author a transition, guard result,
route lease, budget delta, status, or capability grant.

`Rule.CONTROL` and `ControlEventPayloadV1` persist authority transitions by
canonical reference. Control events have an empty formal `StateDiff`; they do
not duplicate or adjudicate the semantic conjecture, scratch, criticism,
evidence, or bridge objects they authorize. Replay reconstructs workflow state
from immutable records without re-running a model or trusting a mutable
scheduler counter.

An active conjecture provider call requires a durable issued work order. A
provider receipt must match that work order's route, contract, and capability
grant. A guard disposition is durable before semantic admission. Crash
recovery either resumes the exactly recorded boundary or records the work as
abandoned; an orphan provider response or silently forgotten outstanding work
is invalid.

## D. Shadow and active scope

The v4 control modes are complete profiles, not user-authored workflow code:

- `legacy` names the historical scheduler profile and historical wire
  contracts.
- `shadow` runs the repository-owned conjecture reducer as an observer while
  legacy actuation remains authoritative. It preserves the legacy
  conjecturer contract and cannot alter route, prompt, budget, formal state,
  scratch state, or model output.
- `active_conjecture` authorizes the v4 conjecturer turn contract and moves the
  conjecture dispatch, bounded context expansion, local repair authorization,
  and admission boundary under the typed reducer.

Activation is deliberately narrow. It does not imply that proof, code,
simulation, evidence, website, trial, bridge, stop, continuation, or every
criticism transition has moved under one universal reducer. Existing semantic
and deterministic subsystems remain authoritative outside the explicitly
migrated boundary.

No document or report may describe v4 as superior merely because its control
trace is stricter. A superiority claim requires matched active-mode evidence
covering semantic diversity, verifier-backed quality, repair and no-proposal
rates, context-request behavior, and cost.

## E. Foreign-school criticism

An optional v4 criticism policy may require bounded criticism from configured
foreign schools for eligible accepted school artifacts. The deterministic
planner selects foreign schools, exact critic seats, and bounded batches. A
target's own school cannot satisfy foreign-school coverage.

Criticism content remains open semantic text. Confidence, a requested verdict,
or status-like prose has no direct formal effect. Under `observe_only`, a case
is scrutiny only. Executable counterexamples continue through the existing
deterministic warrant path. Argumentative status effects require the existing
configured defended-trial and warrant machinery. Shared critic models are
legal only when the policy permits shared seats and MUST NOT be reported as
route diversity.

## F. Local repair and workflow retry

Local schema repair and whole-workflow retry are different authorities.

A local repair work order is subordinate to one conjecture work order. It
binds the rejected prompt and raw result, validation diagnostic and JSON
pointer, permitted subtree, remaining attempts, original contract, original
route lease, immutable state fence, and repair policy. It cannot change route,
contract, evidence, unrelated fields, phase, or budget. Authorization is
durable before the next provider attempt, and exhaustion is one typed terminal
transition for that work item.

A bridge workflow retry starts a fresh bridge workflow and fresh persistence
sink after a typed failed attempt. RunManifest v4 is the sole authority for its
wire contract and retry policy. The retry keeps the sealed catalog and
materials, composition request, formal fence, manifest digest, prompt-policy
digest, contract, role, seat, endpoint, and route unchanged. Failed ledger
content is not fed into the fresh attempt. Each authorization is persisted as
`WORKFLOW_RETRY_STARTED` before the new attempt begins and links the prior
failure, cumulative prior token spend, prior authorization, and deterministic
next-attempt identity.

The policy permits zero through two workflow retries, for at most three total
attempts, and only for its explicitly listed typed error codes. Reaching the
ceiling produces the already-typed final failure; it does not authorize
another event or provider call. Versions 1–3 retain the single-workflow bridge
path and ledger contract v1.

## G. Failed calls and accounting

A typed failed LLM call is a valid process trace when it honestly records its
attempts, route, contract, output mechanism, token information, and failure
shape. It need not contain a valid final semantic result. A successful call,
by contrast, requires a valid final attempt. Unknown provider usage must be
recorded as unknown rather than converted to a false zero.

Failure validity does not relax route, token, reservation, or replay checks.
Every provider attempt must remain attributable to exactly one canonical call
and, on an active controlled path, to exactly one work order.

## H. Stop, cancellation, and continuation boundary

The existing deterministic `StopController` remains the sole stopping policy.
Model signals such as `stuck`, `complete`, `need_context`, or
`capability_mismatch` may be recorded and supplied as bounded observations;
they do not directly stop a run.

For v4, a terminal stop is recorded through typed lifecycle records that bind
the manifest and controller version, workflow process digest, content-addressed
checkpoint and outstanding-work snapshot, stop record digest and event fence,
and the controller state before and after evaluation. The stored object schemas
are `workflow-stop-metrics-observation`, `workflow-lifecycle-snapshot`, and
`workflow-lifecycle-decision`. The lifecycle decision records `STOPPED`; it
does not invent a second pause state. `STOPPED` also refuses unfinished
workflow authority. Versions 1–3 keep their existing `run-stop.json` bytes and
behavior.

Cancellation remains a fixed run-bound operator intent observed at a safe
completed-cycle boundary; it cannot interrupt a provider call or author a
status. Continuation may append a typed `workflow-resume-decision.v1` control
event only after replay proves a typed deterministic converged `STOPPED`
decision, the same immutable manifest/controller/profile, the prior process
and stop records, the exact canonical checkpoint-file byte digests, the event
fence, the restored controller state, and an empty outstanding/unconsumed-work
snapshot. `RESUMED` is emitted before any continuation worker starts and is
idempotently replayed after interruption. Completed, stuck, exhausted, budget,
cancelled, and untyped historical stops are refused. `PAUSED` is not
implemented and MUST NOT be claimed.

## I. Interfaces and compatibility

CLI, MCP, MiniReason, and future chat clients may translate argv, JSON-RPC, or
natural language into typed requests. They may not select hidden routes,
append raw control events, set status, bypass guards, mutate a bound manifest,
or implement a competing scheduler policy. CLI and MCP text-run operations use
the same strict intents and `TextRunApplicationService`; scratch queries and
grounded-bridge operations use their respective shared application services.
Those services own dispatch, process locking, replay-safe lifecycle behavior,
and result projection. Scratch preview is read-only; direct open is an
explicitly separate intent that records visibility under the service-owned
lock. This extraction does not imply one universal service or grant any client
raw control authority.

MiniReason continues to use the shared ontology, storage, route firewall,
wire/repair kernel, scratch, attention, and bridge services while retaining its
reduced scheduler. Its explicit v4 `shadow` path also reuses the parent
conjecture application boundary and the exact canonical work-order, proposal,
guard, and transition record types for the overlapping generate boundary. It
does not implement the active v4 turn/context-expansion controller,
full-engine trials, research, or website stages. The default Mini path and
historical roots remain byte-compatible and open without migration.

Opening a v1, v2, or v3 manifest does not synthesize v4 fields, control events,
school bindings, context capabilities, criticism policy, or workflow retries.
Historical reads remain physically read-only. Opting into v4 requires an
explicitly compiled complete policy and a newly bound compatible run root.
