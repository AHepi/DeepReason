# Advisory scratchpad and grounded final output

This is the user and operator guide for the v1.4 advisory tranche. The
normative rules are in
[`harness-spec-v1.4-amendment.md`](harness-spec-v1.4-amendment.md).

## A short, ordinary-user flow

Enable the features in the same typed source profile that already contains
your concrete `summarizer`, `thesis`, and (when review is enabled) `judge` or
`grounding_reviewer` routes:

```yaml
scratchpad:
  enabled: true
  semantic_retrieval: false  # deterministic literal/structural retrieval only
bridge:
  mode: grounded_two_stage
  grounding_review: true
```

Unknown keys are errors. Compile this source policy once into a v3 manifest,
then bind that immutable manifest to the run in the normal way:

```bash
deepreason setup
deepreason --config config/my-provider.yaml config compile \
  --schema-version 3 --workload-profile text --profile compact \
  --rubric-policy forbid --out run-manifest-v3.json
deepreason --root runs/my-question reason --text "Why might X happen?" \
  --run-manifest run-manifest-v3.json
```

Capture loose ideas without ceremony. Only `--content` is required; the
keep-reason, unfinished note, and next move remain optional:

```bash
deepreason --root runs/my-question scratch add \
  --content "A mechanism worth comparing with the current survivors."
deepreason --root runs/my-question scratch search "mechanism" --limit 10
deepreason --root runs/my-question scratch map --limit 10
deepreason --root runs/my-question scratch related <block-prefix> --limit 10
deepreason --root runs/my-question scratch coverage --limit 10
```

`scratch revise` creates a new block and may branch from an older revision.
`scratch link` records a provisional relation; `scratch retire-link` retires it
without erasing history. `scratch cluster` manages provisional navigation
groups. Add `--json` for stable IDs and typed machine output. Add `--at-seq N`
to supported read commands for a physically read-only historical view.

Build the grounded final view only after the run has the desired formal record:

```bash
deepreason --root runs/my-question bridge build <problem-prefix> --target answer
deepreason --root runs/my-question bridge status
deepreason --root runs/my-question bridge claims --limit 25
deepreason --root runs/my-question bridge result
deepreason --root runs/my-question bridge validate
```

The result labels grounded facts, recorded observations, supported inferences,
surviving conjectures, explicit assumptions, unknowns, and conflicts
separately. `partially_answered`, `underdetermined`, `insufficient_evidence`,
`conflicting_evidence`, and `outside_scope` are successful epistemic results,
not generic process errors.

## What scratch material can and cannot do

Scratch blocks are immutable advisory notes. Revisions branch instead of
overwriting; exact duplicates remain separate instances. Links, clusters, and
snapshot-bound guides improve navigation but confer no evidential or formal
authority. A stale guide stays attached to the snapshot it described.

A scratch reference says where an idea came from intellectually. It does not
ground the idea, support it, attack another object, satisfy a premise, or alter
acceptance/refutation. There is deliberately no promote command. A model may
see a bounded attention pack and author a new formal conjecture, but that new
object must pass the existing formal validator and registration path.

Similarity is also advisory. High similarity can rank retrieval but cannot
merge, delete, deduplicate, link, support, or validate blocks. The optional
`fastembed` backend is installed with `deepreason[embed]`; without it, the
deterministic hashing backend remains available. A configured neural failure
that falls back is identified in the replay record.

Attention mixes direct focus, explicit links, clusters, literal search,
semantic retrieval, recency, loose material, dormancy, underexposure,
deterministic exploration, and coverage. Coverage freezes the block set for a
cycle and eventually renders every member; blocks created during that cycle
wait for the next one. The entire workspace can be browsed in bounded pages,
but it is not dumped into each model call.

### Ordinary conjecture and bounded context requests

RunManifest v4 can make this attention pack a first-class input to ordinary
conjecture work. Planning is bound to the current formal and scratch event
fence. The selection and render receipts become durable only when the exact
context is rendered to the call; a stale plan is rebuilt. The prompt labels the
pack advisory and tells the model it may be wrong, stale, contradictory,
abandoned, or irrelevant.

With `conjecture_context.mode: harness_plus_model_request`, the v4 turn may
return a bounded semantic `ContextRequest`. It may use query text, already
visible aliases, permitted retrieval channels, and an optional purpose. It
cannot request a path, tool, command, provider, route, budget, phase, or status.
The request is a proposal to the deterministic harness, not retrieval
authority.

A grant creates another bounded attention plan and a **fresh one-call work
order** with a decremented expansion allowance. The expanded receipt links the
prior selection and expansion decision. A denial or exhausted allowance is
typed and replayable. A request-only turn or abstention creates no formal
artifact, and a candidate still passes the ordinary anti-relapse and formal
registration path. Scratch never promotes itself.

## Why the final bridge has two stages

Stage A creates a claim ledger and checks the epistemic requirements of every
entry. Facts and observations need canonical grounding. Inferences need
premises. Conjectures may be genuinely new but remain marked as conjectures.
Assumptions, unknowns, and conflicts remain explicit. Scratch references never
substitute for grounding.

Stage B composes from that validated ledger. It may reword entries, but it
cannot smuggle in a new factual assertion. A newly needed inference or
conjecture takes the one bounded ledger-amendment route and is validated before
composition continues. Repair cannot invent citations, sources, evidence,
premises, or an answer to fill a schema; it must remove, downgrade, or leave
unsupported material unresolved.

### Repair and whole-workflow retry are separate

Schema or grounding repair operates inside one bridge workflow. It corrects a
rejected payload under the same evidence and bounded policy; it cannot invent a
source, citation, premise, route, or answer.

For a bound v4 manifest, a separate `WorkflowRetryPolicyV1` may authorize a
fresh complete bridge workflow after a typed retryable failure. The fresh
attempt uses a new workflow and sink but the same sealed catalog/materials,
composition request, formal fence, manifest, prompt-policy digest, wire
contract, role, seat, endpoint, and route. Failed ledger content is not carried
into the next attempt. Authorization is persisted before dispatch and includes
the prior failure, cumulative prior tokens, retry lineage, and deterministic
next-attempt identity.

Zero retries is the default. The policy can allow at most two retries—three
total attempts—and only for listed typed error codes. The final failure at the
ceiling remains a valid terminal process record. V1–v3 retain the historical
single-workflow path and ledger contract v1.

## RunManifest v3 and migration

The v3 manifest freezes every advisory and bridge policy, including all eleven
attention channels, coverage cadence, bounded pack sizes, exact authoring and
review roles, embedder identity/fallback policy, ledger amendment bound, repair
bounds, and output limits. It contains concrete routes and environment-variable
names, never credential values, unresolved `auto` routes, provider fallback, or
runtime route decisions. The run binds its canonical digest before use.

Versions 1 and 2 remain readable under their original byte and hash contracts.
Installing a newer wheel does not add v3 fields to them. Opening an old run,
including a historical sequence, does not create scratch state, bridge state,
directories, manifests, objects, embeddings, receipts, or events. There is no
in-place migration. Use the explicit derived mode to build over an old fence:

```bash
deepreason --root runs/old-v2 bridge build <problem-prefix> \
  --derived-output runs/old-v2-answer --at-seq 74 \
  --run-manifest run-manifest-v3.json --target answer
deepreason --root runs/old-v2-answer bridge result
```

The source is opened through the physically read-only historical Harness. The
destination must be a new, non-overlapping directory whose parent already
exists; symlinked, nested, ancestor, or existing destinations are rejected.
That directory owns the v3 manifest, bridge objects, blobs, and append-only
events. Its evidence pack and terminal record retain a path-independent source
digest and exact source sequence; the source path itself is not persisted or
shown to a model. Source and destination event sequences are independent.
Derived scratch focus currently fails closed because copying source scratch
without a canonical destination attention receipt would lose replayability.

MiniReason follows the same rule. `MiniAdvisorySession` opens an already-bound
`engine_profile: mini` v3 run and delegates to the canonical Harness,
ScratchService, AttentionPlanner, and bridge. Older MiniReason roots keep their
legacy format and are opened without mutation.

RunManifest v4 extends, rather than rewrites, this contract. A complete v4
control policy may select the conjecture turn v4 wire contract and bridge ledger
contract v2. It does not change scratch's epistemic status. Opening a v3 run
does not add those contracts, context capabilities, control events, or workflow
retries. Use a separately compiled and bound v4 root for the active boundary;
see [`JOLT_CONTROL_PLANE_MIGRATION.md`](JOLT_CONTROL_PLANE_MIGRATION.md).

## Security and process safety

Treat every scratch phrase, guide, source excerpt, model result, handle, and ID
as hostile input. CLI and MCP requests are closed and bounded; canonical IDs
are recomputed; path traversal, unsafe symlinks/control files, arbitrary file
reads, raw event/object writes, and route-like scratch fields fail closed.
Terminal rendering bounds and neutralizes untrusted control text.

Repair calls have one compact contract and cannot browse or use tools. Model
content cannot choose roles, providers, models, routes, concurrency, commands,
guards, statuses, or workflow transitions. The shared process lock works on
Windows, macOS, and Linux and serializes writers without making historical
reads mutate the root.

On an active v4 conjecture path, a local repair additionally requires a durable
`RepairWorkOrderV1` binding the rejected raw result, diagnostic and JSON
pointer, authorized subtree, remaining attempts, original contract and route,
and immutable state fence. This local authorization is not permission to start
a bridge workflow retry or to change evidence.

The default MCP server exposes only the exact 17 tools listed in
[`AGENT.md`](AGENT.md). Its five scratch operations are read-only attention and
browsing views; it exposes no scratch mutation. Bridge execution uses
`start_bridge`, `bridge_status`, `bridge_result`, and `bridge_claims`, with
operational failure kept separate from epistemic resolution.

## Offline distribution check

From a source checkout, run:

```bash
python scripts/wheel_smoke.py
```

The script builds a wheel, installs it into a fresh virtual environment, checks
both entry points and the exact default MCP tool list, imports the canonical
scratch/bridge/locking and MiniReason advisory packages, and proves that the
deterministic embedder works without `fastembed`. It makes no provider call.
