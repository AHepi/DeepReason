# Small-model compatibility status

The `deepreason-small-model-compat-v1` compatibility kernel and its v1.4
advisory extension are implemented. DeepReason compiles typed source
configuration into a canonical immutable `RunManifest`, binds every call to an
`EndpointLease`, isolates model-visible wire contracts from canonical outputs,
logs every bounded repair attempt, and uses deterministic harness-owned
workflow state machines.

The model contract remains:

- one bounded task per call;
- one compact, closed output contract per call;
- localized validation errors and bounded repair;
- no repository, source YAML, provider catalog, peer-model, routing, or
  workflow authority; and
- no tools or browsing during repair.

Scratch block hints remain truly optional: omitting `why_keep_this`,
`unfinished`, or `possible_next_move` does not trigger repair. Retrieval packs
are bounded; no model receives the whole scratchpad by default. Facts and
observations require grounding, inferences require premises, and novel
conjectures remain allowed under an explicit conjectural mode. Unknown and
partial results are valid successes, so a compact model is never pressured to
invent a positive answer merely to satisfy a schema.

MiniReason consumes the same route, profile, wire, repair, event, blob, object
store, scratch, attention, and bridge modules while retaining its reduced
scheduler. `minireason.advisory.MiniAdvisorySession` is a thin facade over the
parent `Harness`, `ScratchService`, `AttentionPlanner`, and grounded bridge. It
requires an already-bound `engine_profile: mini` RunManifest v3 and does not
define a second ontology, validator, storage layout, or bridge protocol.

## RunManifest v4 boundary

V4 is an explicit full-engine control profile, not a new default for compact
models or MiniReason. The compact presentation profile remains usable with
`legacy`, `shadow`, or `active_conjecture`; presentation size and workflow
authority are independent choices.

Under `active_conjecture`, the same compact model still authors open claims,
mechanisms, counterconditions, optional analogy, uncertainty, bounded context
requests, and abstentions. It does not author work orders, routes, budgets,
guards, repair scope, context grants, or status. A granted context request
creates a fresh one-call authorization. Local repair is limited to the rejected
object or authorized subtree under the same contract and route. A typed failed
call is a valid accounted trace, while a successful call still requires a valid
final attempt.

Schools remain conditioning lineages. `conditioning_only` may intentionally
send several schools through one compact-model route. `route_bound` uses exact
manifest seats, but distinct schools are not reported as distinct models unless
the route receipts prove that stronger claim.

Historical Mini roots and the default Mini manifest path remain unchanged and
are not upgraded on open. With an explicit v4 `shadow` manifest, Mini now
reuses the parent's conjecture application boundary and exact canonical work
order, proposal, guard, and transition records for its generate boundary.
Mini retains its reduced generate/check/rotate semantics and does not import
the active v4 turn/context-expansion controller, full-engine trials, research,
or website stages. Do not describe it as controlled by
`conjecture.active.v1`.

The normative boundary and migration status are documented in
[`harness-spec-v1.5-amendment.md`](harness-spec-v1.5-amendment.md) and
[`JOLT_CONTROL_PLANE_MIGRATION.md`](JOLT_CONTROL_PLANE_MIGRATION.md).

The production MCP surface contains the exact 17 harness-owned run, website,
read-only scratch, and grounded-bridge tools listed in
[`AGENT.md`](AGENT.md). Endpoint models receive a rendered role pack and one
closed output schema only. Model-authored route, model, delegation, command,
guard, status, acceptance, and concurrency fields fail validation and have no
operational effect.

## Local conformance

The earlier frozen local record is
[`experiments/results/small_model_compat_local_verification_v1.json`](../experiments/results/small_model_compat_local_verification_v1.json).
It records 751 passing tests, one skipped optional `fastembed` test, real
Chromium execution, clean Ruff, successful bytecode compilation, and a clean
diff check. The suite includes the three Gemma failure reproductions, route
mutation fail-closed behavior, per-attempt replay/accounting, direct-to-compact
later-cycle recovery, malicious control fields, deterministic component
concurrency, localized manifest repair, terminal diagnostics, MiniReason
graduation, and process-metadata isolation.

The v1.4 extension adds local scripted tests for loose optional-field blocks,
immutable branching revisions, replayable links/clusters/guides, similarity
non-authority, independent attention channels, anti-starvation coverage,
formal-state isolation, claim-ledger-first composition, epistemic
classification and repair, unresolved success, historical read-only behavior,
RunManifest v1/v2 byte compatibility, portable process locking, the exact MCP
surface, and MiniReason forward compatibility. The wheel gate in
`scripts/wheel_smoke.py` installs a clean wheel on Linux, macOS, and Windows,
checks both entry points, imports the MiniReason advisory facade from the
wheel, and verifies the deterministic embedder with no `fastembed` install.
It makes no provider call.

## Live acceptance protocol

The preregistered 60-prompt matrix is
[`experiments/website_compat_matrix_v1.json`](../experiments/website_compat_matrix_v1.json).
Run it with `scripts/compatibility_eval.py`; checkpoints are resumable, mock
observations are never acceptance-eligible, and reports leave A3-A10 as
`insufficient_evidence` until complete non-mock coverage exists. A9 also
requires the separately preregistered live frontier baseline from the same
matrix digest and at least two non-mock frozen frontier families. The resumable
checkpoint may be populated in separate invocations—for example, compact
Gemma trials first, then frontier trials from an explicitly mixed-family
configuration—without changing keys, seeds, or budgets.

No provider credential was available during local verification, so this
implementation does not claim the Gemma schema-rate, three-round website, or
frontier regression thresholds have been empirically met. That is an explicit
evidence gap, not an inferred failure or a substituted mock result.

The same evidentiary limit applies to v4 active control. Offline differential,
replay, semantic-freedom, and verifier-backed fixtures can establish boundary
correctness; they do not establish live novelty, quality, latency, or cost
superiority. Any such claim requires separately authorized matched provider
runs under frozen routes and budgets.
