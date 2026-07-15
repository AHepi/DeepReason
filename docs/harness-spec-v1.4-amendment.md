# Conjecture–Criticism Harness — v1.4 normative amendment

**Status: normative.** This document amends
[`harness-spec-v1.3.md`](harness-spec-v1.3.md); it does not replace or modify
that file. The v1.3 specification remains normative except where this
amendment adds the advisory scratch ontology, bounded attention, RunManifest
v3, or the grounded final-output bridge. If those additions conflict with an
older presentation rule, this amendment controls only for those additions.

## A. Control and authority boundary

The deterministic harness owns control flow, canonical storage, append-only
event recording, replay, route binding, validation, scheduling, repair bounds,
and adjudication. An LLM may author or interpret bounded content but has no
workflow, routing, storage, validation, or verdict authority.

Scratch material is advisory and is a separate ontology. Scratch blocks,
revisions, links, retirements, clusters, memberships, guides, similarity
observations, retrieval receipts, attention receipts, visibility records, and
coverage cycles MUST NOT enter formal `A`, `Π`, `att`, `dep`, `carry`, `addr`,
status, warrant, commitment, acceptance, or refutation computation. Scratch
activity therefore cannot change a formal verdict.

There is no automatic promotion operation. The only permitted scratch-to-formal
path is:

1. the harness renders a bounded advisory context;
2. an LLM authors a new formal object;
3. the existing formal schema validates that new object; and
4. the existing formal registration path records it.

The source scratch objects remain unchanged. A scratch reference records
intellectual provenance only and MUST NOT count as a source, observation,
evidence item, premise, warrant, support, or attack.

## B. Advisory scratch ontology

Every scratch object and event payload is strict, bounded, canonically hashed,
immutable, stored in the shared object/blob stores, and registered through the
shared append-only event log. Caller-supplied canonical IDs MUST equal the IDs
computed from canonical content. Replay is the source of truth; a derived index
is permitted only when it can be rebuilt from immutable objects and events.

A block is one immutable instance. Its content is required; its
`why_keep_this`, `unfinished`, and `possible_next_move` fields are genuinely
optional. An exact duplicate body remains a distinct block instance. A revision
creates another immutable block and may branch from any earlier live block; it
does not overwrite its parent.

A link is a provisional, plain-language navigation assertion. It may be used,
superseded, or retired, but it has no truth or graph authority. Retirement is an
append-only event: the retired link remains visible in historical replay.
Clusters and their memberships are provisional navigation structures. A guide
is bound to the exact scratch snapshot from which it was authored. Later
changes make it stale; they never silently rewrite it. No cluster or guide may
be treated as a summary verdict.

All model-authored content, source excerpts, handles, IDs, relation phrases,
and guide text are untrusted data. They cannot select a provider, role, route,
tool, command, path, status, or guard policy.

## C. Similarity, retrieval, and attention

Embedding similarity is retrieval metadata only. It MUST NOT establish
identity, duplication, truth, support, attack, equivalence, deletion, merging,
or promotion. Similar blocks remain separate immutable instances regardless of
score. A neural embedder is optional. Basic scratch operation requires no new
dependency; the deterministic hashing embedder remains available, and a
configured neural-backend fallback is recorded visibly.

The whole live scratchpad is logically addressable through bounded operations,
but no model call receives it in full by default. Retrieval and attention
selection produce bounded, replayable receipts. Attention has independent
channels for direct focus, explicit links, shared clusters, literal keywords,
semantic similarity, recency, loose/unlinked blocks, dormancy, underexposure,
deterministic exploration, and coverage. Semantic ranking cannot consume every
slot.

Coverage is deterministic anti-starvation. A cycle freezes the live-block set
at its start and advances only after a committed receipt proves that its next
block was rendered. Continued eligible attention packs MUST eventually render
every block in that frozen set. Blocks created during a cycle enter the next
cycle. Time of day and elapsed wall-clock time MUST NOT affect order or
selection.

A historical view at an event sequence is physically read-only. Opening or
browsing it MUST NOT create a directory, event, object, blob, repair record,
embedding, guide, receipt, visibility update, or coverage transition.

## D. Grounded final-output bridge

The grounded bridge has two mandatory stages.

Stage A constructs and deterministically validates a claim ledger from bounded
canonical evidence, formal state, and optional advisory scratch context. Stage
B composes prose from that validated ledger. New wording is allowed. Stage B
MUST NOT silently introduce a source-backed factual assertion. A new inference
or conjecture that is not already represented requires the explicit, bounded
ledger-amendment path and another validation pass.

The ledger and output preserve these distinct epistemic classes:

| Ledger class | Required discipline |
|---|---|
| source-backed fact | identifies canonical grounding; scratch references alone are invalid |
| recorded observation | identifies its canonical observation or evidence record |
| supported inference | identifies ledger premises that support the conclusion |
| surviving conjecture | remains explicitly conjectural; it may contain a genuinely novel idea |
| explicit assumption | is visibly presented as an assumption |
| unknown | preserves the missing answer instead of filling it |
| conflict | preserves incompatible grounded evidence instead of choosing silently |

Formal status is not, by itself, external factual grounding. Intellectual
provenance is not evidence. A conjecture need not appear in source material,
but it cannot be rendered as fact. An inference may be novel, but it cannot be
rendered without premises. Missing grounding cannot be repaired into a fact or
observation.

Schema and grounding repair are bounded content-correction calls with no tools
or browsing. Repair MUST NOT manufacture a fact, citation, source reference,
evidence reference, premise, positive answer, or canonical ID to satisfy a
required field. When support is absent, repair must downgrade the claim, remove
it, mark it unresolved, or change the overall resolution. Every model call,
raw output, attempt trace, amendment, ledger, validation finding, composition,
grounded review, repair, failure, and terminal result is append-only and
replayable.

The following are valid terminal epistemic successes:
`answered`, `partially_answered`, `underdetermined`,
`insufficient_evidence`, `conflicting_evidence`, and `outside_scope`.
An unresolved result is not a transport failure and MUST return process
success. Operational failures remain separate, non-epistemic records.

## E. Manifest, compatibility, and interfaces

RunManifest v3 freezes the complete scratch, attention, coverage, embedding,
bridge, review, repair, and role policies before model use. Its routes are
concrete and credential-free. It MUST NOT contain credential values, unresolved
model sentinels, provider fallback, or runtime route-selection instructions.
Unknown source-policy or manifest keys fail validation.

RunManifest v1 and v2 retain their original canonical bytes and hashes. Opening
an old manifest or old run does not migrate or mutate it. The v3 advisory
features require an explicitly compiled and bound v3 manifest. A bridge over an
old run MUST use explicit derived mode: the source is opened read-only at an
exact event fence, the destination is a distinct non-overlapping v3 run root,
and canonical bridge records bind a path-independent source digest and source
sequence. The source path is not canonical data. Source scratch context MUST
fail closed unless its bounded attention receipt and context are persisted in
the destination protocol. MiniReason and the full engine use the same canonical
scratch and bridge implementation; no reduced ontology or bridge protocol is
permitted.

Human CLI views use clear epistemic labels and approachable short handles;
machine JSON retains stable full IDs and typed results. Browsing is bounded.
Path traversal, unsafe control files, arbitrary reads, raw object/event writes,
and caller-authored mismatched IDs fail closed.

The default production MCP surface is the exact narrow, harness-owned set
documented in [`AGENT.md`](AGENT.md). Scratch tools are read-only by default;
the bridge follows start/status/result/claims. MCP MUST NOT expose shell access,
arbitrary files, generic prompts, raw model invocation, credentials, route
mutation, direct writes, guard bypasses, or status setters. Process locking is
one shared cross-platform abstraction and cannot depend on importing `fcntl`
on platforms where it does not exist.
