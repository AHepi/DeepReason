# The research backend (owner decisions resolved 2026-07-28)

Status: tranche 1 IMPLEMENTED — the contained fetcher and the directed
`web:` backend (`src/deepreason/research/fetch.py`,
`tests/test_research_web.py`). V6 in-run enablement remains gated
(`V6_RESEARCH_UNAVAILABLE`) and is tranche 2.

## The two parked decisions, and how they were resolved

The 2026-07-27 handover parked autonomous research on two questions.

1. **Open web vs per-run domain allowlist → allowlist.** Decided from
   the harness's own doctrine: where a run may look is part of what the
   run *is*. The allowlist is a frozen containment authority (bare
   lowercase hostnames, subdomains implied, https only, every redirect
   hop re-validated before dispatch). Open web would make runs
   non-replayable in intent and unbounded in prompt-injection surface.
2. **Fetch budget semantics → requests-denominated, typed exhaustion.**
   Decided by the campaign's grounded evidence: the deepseek-v4-pro
   deep run on exactly this question ended ANSWERED with a
   requests-only budget whose exhaustion is recorded as a typed,
   auditable terminal carrying the count and the limit. That is the
   implemented shape: every dispatched round-trip (redirect hops and
   failures included) spends one request; validation refusals spend
   nothing; `RESEARCH_BUDGET_EXHAUSTED` receipts always carry
   `requests_used` and `requests_limit`. The per-response byte ceiling
   is containment, not a budget — it bounds any single response without
   changing the denomination.

## Tranche 1 (implemented)

- `ContainedFetcher`: allowlist + budget + receipts. Every fetch
  attempt — success, refusal, failure, exhaustion — mints a
  `FetchReceiptV1` with a content digest for fetched bytes.
- `WebBackend` (`RESEARCH_BACKEND: "web:<config.yaml>"`): **directed**
  retrieval — explicit https URLs in the research problem description
  are fetched (bounded per problem); the backend never searches.
  Choosing sources is the director's act; executing them safely is the
  harness's.
- Evidence enters through the one canonical `register_evidence` shape:
  the source-reliability node carries the fetch provenance claim (url,
  content sha256, receipt seq) — attackable, on the record.
- `run_research` persists every receipt as a `research-fetch:` Measure,
  so no fetch ever vanishes from the append-only log.
- Config file shape:

      domain_allowlist: [example.org, data.example.net]
      maximum_requests: 25
      maximum_response_bytes: 2097152   # optional, per-fetch containment
      timeout_seconds: 30               # optional

## Tranche 2 (open): V6 in-run enablement

`ResearchCapabilityPolicyV1` gains `domain_allowlist` and the
requests-denominated budget, binding both into the manifest digest
(this drifts the engaged preset digest and therefore invalidates cached
qualifications — schedule it with a requalification window). The
conjecture turn gains a bounded research-proposal contract (the model
proposes allowlisted URLs; the transactional service executes them
through the same `ContainedFetcher`), fetched material flows through
admission (§ADMISSION_SPEC) so it becomes citable blocks rather than
raw prompt text, and replay validates the receipt arithmetic. Until
then `V6_RESEARCH_UNAVAILABLE` stands, exactly as before.

## Injection posture

Fetched text is untrusted data under the same normative rules as
admitted documents (ADMISSION_SPEC §5): quoted material, never
instructions, no special status for rubric-bearing content. Tranche 1
surfaces fetched text only through the evidence artifact path, which
already frames it as attackable candidate material resting on an
attackable reliability node.

## Increment B build map (IMPLEMENTED except item 2)

Template: `capabilities/simulation.py` over the generic capability
transition machinery (`capabilities/models.py`): lifecycle
PROPOSED→GRANTED→COMPILED→DISPATCHED→SUCCEEDED/FAILED→RESULT_PACKAGED→
CONSUMED, budget deltas (requests/executions/result_follow_ups),
chained process digests.

1. `capabilities/research.py`: ResearchCapabilityController. Proposal =
   ResearchFetchProposalV1 (bounded https URL list ≤3, validated against
   the frozen policy allowlist at admission AND dispatch). requests
   budget = policy maximum_requests; executions = dispatched fetches;
   maximum_sources caps CONSUMED evidence. execute() runs
   ContainedFetcher under the policy's allowlist/ceilings; every
   FetchReceiptV1 lands in the DISPATCHED phase record;
   RESEARCH_BUDGET_EXHAUSTED maps to typed FAILED carrying count+limit.
2. Conjecture wire: ConjecturerTurnWireV6 gains bounded
   `research_proposals`, schema-visible only when the manifest enables
   research (same gating idiom as simulation_proposals).
3. run_manifest.py: the V6 gate accepts research.enabled iff
   backend_identity == "web.contained.v1"; V5/Tranche A keeps refusing;
   the engaged public preset keeps research disabled (no digest drift).
4. Replay/verifier: validate the transition chain and the receipts'
   requests arithmetic against the frozen limit.
5. Increment C: CONSUMED routes fetched text through admission so it
   enters as citable blocks joining the §4 citation contract.

## Status after 2026-07-28 session

- Increment A (policy fields, digest-stable): DONE, gated.
- Increment B (transactional runtime): DONE, gated — controller chain,
  kind-checked phase records, replay-derived cumulative budget, typed
  exhaustion receipts, V6 gate lifted for web.contained.v1
  (tests/test_research_capability.py).
- Increment C1 (citable blocks): DONE — consumed fetches segmented by the
  canonical admission parser; block ids on the reliability node; §4
  checker universe = bound dossier + replay-derived research blocks.
- Remaining (C2): the bounded `research_proposals` field on
  ConjecturerTurnWireV6, schema-visible only when the manifest enables
  research (simulation_proposals gating idiom), compiled to
  ResearchFetchProposalDraftV1 and staged through the controller in
  rules/conj.py's transactional flow. Until C2, research runs under
  harness/workflow direction rather than model proposal.

## C2 design notes (from reading the simulation staging seam)

C2 makes research proposals a model-visible capability on the conjecture
wire, mirroring how `simulation_proposals` works end to end:

1. **Task-payload authority block.** The transaction service's conjecture
   task payload must embed a `research_authority` block alongside
   `simulation_authority`: `{enabled, policy_digest, per-turn cap}`, and
   the work order's `allowed_outcomes` must include `"research_request"`
   when the manifest enables research. Grep `simulation_authority` in the
   payload builder to find the seam.
2. **Wire field.** `research_proposals` on `ConjecturerTurnWireV6` and
   `ConjectureTurnV6` — bounded (≤2 per turn), additive, default-empty.
   Schema-visible only when the manifest enables research, using the same
   `_omit_property` idiom that gates `scratch_proposal` /
   `simulation_proposals`. Wire entries compile to
   `ResearchFetchProposalDraftV1`.
3. **Controller staging.** `ResearchCapabilityController` gains
   `stage_transactional_proposals(drafts, *, preparation, provider_attempt,
   source_call_seq)` validating durable provider work before accepting a
   proposal: the transaction work item and provider attempt exist,
   `task_kind` is CONJECTURE, contract is `conjecturer.turn.v6`, the task
   payload's `research_authority` block matches the live policy digest, and
   the source call is the provider-result event. Mirror
   `_stage_transactional_proposal` in `capabilities/simulation.py`.
4. **conj.py mirror.** `rules/conj.py` stages research drafts through the
   controller exactly where it stages `simulation_drafts`, with the same
   typed rejection path; `execute()` and `consume()` then run inside the
   cycle so consumed fetches become citable blocks (C1) before the next
   gate-loop citation check.
