# Spec for: the two-call seat protocol — deliberation and emission become separate calls
Traces: every item cites R/C numbers from REQUEST.md. Untraceable items are bugs.

Status: **STOPPED at the frozen-surface contact gate** (dr-spec-change step 3)
and at one material design fork (Q2). See "Questions for operator". Nothing
below this line has been implemented.

## Design summary (one paragraph, for the reader who reads nothing else)

A seat call keeps its single `LLMAdapter.call` entry point, its single route
lease, and its single authorization. Inside attempt 0 it becomes two provider
legs on the SAME endpoint object: leg `reason` sends the rendered request with a
deliberation directive appended, at `B_r` completion tokens and the route's own
reasoning setting, tolerating an empty completion; leg `extract` sends a small
request carrying the (possibly truncated, possibly empty) trace plus the wire
contract's schema, at `B_a` completion tokens with the reasoning knob turned
off. `B_a = min(SPLIT_BUDGET_EXTRACTION_TOKENS, ceiling)` and
`B_r = ceiling - B_a`, so `B_r + B_a == ceiling` exactly and neither leg's cap
can exceed the route lease ceiling (R9). Each leg appends its own `LLMAttempt`,
carrying `split_leg`, `natural_stop`, and `split_notice`. Everything the
protocol cannot honor becomes a typed notice on the record, never a refusal
(R3).

## Items

S1 (R1, R9) — the protocol module | `src/deepreason/llm/split.py` (new)
    before: no such module.
    after: `SplitPlan` (frozen dataclass: `armed`, `reason_max_tokens`,
      `extract_max_tokens`, `extract_reasoning`, `notice`), `plan_split(...)`,
      `deliberation_request(request)`, `extraction_request(schema_json, trace)`,
      and the two leg labels `SPLIT_LEG_REASON = "reason"` /
      `SPLIT_LEG_EXTRACT = "extract"`. `plan_split` is pure: no I/O, no route
      mutation, no provider knowledge beyond `llm/providers.py`'s two
      predicates.
    accept: `python -m pytest tests/test_split_budget_protocol.py -q -k plan`
      -> 0 failed; and
      `python -c "from deepreason.llm.split import plan_split, SplitPlan, deliberation_request, extraction_request, SPLIT_LEG_REASON, SPLIT_LEG_EXTRACT"`
      -> exit 0.

S2 (R1, R3) — per-request overrides at the endpoint | `src/deepreason/llm/endpoints.py`
    before: `build_body`/`complete` read `self.max_tokens` and `self.reasoning`
      only; a `null` content is always an `EndpointError`; the provider's
      reasoning payload is discarded.
    after: `complete`/`build_body` gain keyword-only `max_tokens`,
      `reasoning` (sentinel-defaulted so "not passed" differs from "None"),
      and `allow_empty_content`. With `allow_empty_content=True` a `null`
      content returns `""` instead of raising, and is not retried as a
      transient body. `self.last_reasoning_trace` is set from
      `message["reasoning"]` or `message["reasoning_content"]` when present.
      The endpoint object is never mutated by an override, so
      `EndpointLease.verify` still sees the frozen route values (C3).
      `MockEndpoint` gains an optional `finish_reasons` script and
      `last_finish_reason` / `last_reasoning_trace` so the offline regression
      can drive both shapes.
    accept: `python -m pytest tests/test_split_budget_protocol.py tests/test_llm.py tests/test_providers.py tests/test_vision.py -q`
      -> 0 failed.

S3 (R1, R3, R4, R6) — the split dispatch | `src/deepreason/llm/adapter.py`
    before: attempt 0 issues exactly one `endpoint.complete(request, **kwargs)`;
      an empty or truncated completion becomes `SchemaRepairError` after the
      bounded repair budget, and a `null` completion becomes `EndpointError`
      (measured: M10).
    after: `LLMAdapter.__init__` gains `split_budget_mode` (default `"auto"`)
      and `split_extraction_tokens` (default 512); `build_adapter` sets both
      from `Config`. At attempt 0, when `plan_split(...).armed`, the dispatch
      runs the two legs described in the design summary. Both legs pass
      `_enforce_request_envelope` and are blob-stored; both append an
      `LLMAttempt`. When the plan is not armed, or when any precondition
      fails at run time (extraction request over the frozen envelope, no
      meter headroom for the extraction leg), the call proceeds exactly as
      today and the reason is recorded as `split_notice` — never a refusal
      (R3). Repair attempts (attempt >= 1) never split (A3).
    accept: `python -m pytest tests/test_split_budget_protocol.py tests/test_adapter_attempt_logging.py tests/test_budget.py tests/test_llm_repair_capabilities.py -q`
      -> 0 failed.

S4 (R1) — export surface | `src/deepreason/llm/__init__.py`
    before: no split symbols exported.
    after: `plan_split` / `SplitPlan` exported alongside the existing names.
      No console entry point, MCP tool, or wheel-layout change (R12).
    accept: `python scripts/wheel_smoke.py` -> unchanged pin verdict, run only
      if `git diff --stat` shows a public-surface file moved (R12: it should
      not).

S5 (R2) — the Config choice | `src/deepreason/config.py`
    before: no split setting.
    after: `SPLIT_BUDGET_SEAT_PROTOCOL: Literal["auto", "on", "off"] = "auto"`
      and `SPLIT_BUDGET_EXTRACTION_TOKENS: int = 512`. `"auto"` arms the
      protocol for a seat whose route both HAS a realizable reasoning knob
      (`reasoning_knob_available(route.provider)`) and does NOT have thinking
      explicitly switched off (`not reasoning_disabled(route.reasoning)`) —
      which is ON for glm-5.2 on Ollama Cloud and OFF for a non-thinking
      profile (A1). Config, never the manifest, per
      `DR-INV-frozen-surfaces` "Where authority is allowed to live instead".
    accept: `python -c "from deepreason.config import Config; c=Config(); print(c.SPLIT_BUDGET_SEAT_PROTOCOL, c.SPLIT_BUDGET_EXTRACTION_TOKENS)"`
      -> `auto 512`; and `python -m pytest tests/test_config.py -q` -> 0 failed.

S6 (R6, R7) — the typed per-attempt fields | `src/deepreason/ontology/event.py`
    before: `LLMAttempt` has no natural-stop, no leg label, no notice.
    after: three optional fields with replay-safe defaults, following the row
      `DR-SUB-ontology` already carries for exactly this work ("record new
      per-call provider accounting | `LLMAttempt` / `LLMCall` in
      `ontology/event.py` (defaults required for replay)"):
        `natural_stop: bool | None = None`   # finish_reason == "stop"; None when unknown
        `split_leg: str = ""`                # "" | "reason" | "extract"
        `split_notice: str = ""`             # typed reason the mode was not honored
      `natural_stop` is written and never read: no guard, gate, rank, status,
      label, warrant, or adjudication input consumes it (R7, and the
      operator's seats/evidence law).
    accept: `python -c "from deepreason.ontology.event import LLMAttempt as A; a=A(prompt_ref='blob:p'); assert a.natural_stop is None and a.split_leg=='' and a.split_notice==''"`
      -> exit 0.

S7 (R10, R11) — the regressions | `tests/test_split_budget_protocol.py` (new)
    - `test_the_old_path_yields_the_empty_completion_typed_failure`: split off,
      truncated/empty completion -> the typed failure measured at M10.
    - `test_the_split_path_extracts_an_answer_from_a_truncated_trace`: split
      armed, leg `reason` returns a truncated non-JSON trace, leg `extract`
      returns the schema-valid envelope -> `call` returns the compiled model.
      MUTATION PROOF: with `split_budget_mode="off"` the identical script
      raises; the test asserts both branches in one file so the assertion
      cannot pass vacuously.
    - `test_the_split_path_survives_a_null_completion_on_the_reasoning_leg`:
      leg `reason` returns `None` content -> leg `extract` still runs from the
      provider's reasoning payload (or an empty trace) and yields an answer
      (R4).
    - `test_neither_leg_exceeds_the_route_lease_ceiling` (R9/R10): over a
      parameter sweep of ceilings, `plan.reason_max_tokens <= ceiling`,
      `plan.extract_max_tokens <= ceiling`, and
      `plan.reason_max_tokens + plan.extract_max_tokens <= ceiling`; plus an
      end-to-end assertion that the `max_tokens` actually sent on each leg
      (captured from `MockEndpoint.last_kwargs`) obeys the same three bounds.
    - `test_a_provider_that_cannot_disable_thinking_still_compiles` (R3): mode
      `"on"` against a provider with no reasoning adapter -> armed, with a
      typed `split_notice`, and no exception.
    - `test_auto_is_on_for_a_reasoning_route_and_off_for_a_non_thinking_one` (R2).
    - `test_the_extraction_schema_is_the_minimal_envelope` (R8): the extraction
      request contains the wire contract's schema and NOT the deliberation
      directives, pinned by an explicit absence assertion.
    accept: `python -m pytest tests/test_split_budget_protocol.py -q` -> 0 failed.

S8 (R7) — the no-consumer proof | `tests/test_seats_evidence_law.py`
    before: the file pins the existing seats/evidence separations.
    after: one added test performing a repository census — `natural_stop`
      appears only in `src/deepreason/ontology/event.py`,
      `src/deepreason/llm/adapter.py`, `src/deepreason/llm/split.py`, `tests/`
      and `docs/` — and one behavioral test flipping `natural_stop` on a
      replayed attempt and asserting no status, label, guard, or verdict moves.
    accept: `python -m pytest tests/test_seats_evidence_law.py -q` -> 0 failed.

S9 (R14) — the map moves in the same commits | `docs/map/SUB-llm.md`,
    `docs/map/SUB-ontology.md`, `docs/map/CON-seats.md`
    after: `SUB-llm.md` gains `split.py` in its entry points and a
      "Where to change what" row ("the split-budget seat protocol or its
      arming rule | `llm/split.py::plan_split`; `Config.SPLIT_BUDGET_*` |
      `tests/test_split_budget_protocol.py`") with a `check:` that fails if
      the protocol regresses; `SUB-ontology.md`'s per-call accounting row
      names the three new fields; `CON-seats.md` gains the two-leg shape.
      `Verified-at:` advances only on documents whose checks were re-run.
    accept: `python tools/docs_verify.py` -> failures identical to the C6
      baseline (3 pre-existing shallow-clone failures), none new;
      `python tools/docs_verify.py --audit` -> no new unfailable check.

S10 (R13) — the requalification cost report | DELIVERY.md
    Measured, not reasoned (M9): `qualification_subject_payload(manifest,
    profile)` is a closed function of the RunManifest, the ProviderProfileV1
    and the policy preset. `Config` is not an input. This change adds no
    manifest field and no provider-profile field, so **no qualification
    subject digest moves and the requalification price is zero per home**.
    accept: a pasted before/after `qualification_subject_digest` over the same
    manifest+profile fixture, identical.

S11 (R16) — R-by-R delivery | DELIVERY.md, per `dr-deliver-change`.

## Assumptions (operator may override)

A1 (Q1): "per-profile ... default ON for reasoning-model profiles (glm-5.2),
OFF where a profile is non-thinking" is read as the SEAT'S ROUTE, not
`ModelProfile`. Reason it is the smallest reading: `ModelProfile`
(compact/standard/frontier) is documented in `llm/profiles.py` as tuning "only
rendering and transport" and carries no statement about whether a model thinks,
so it cannot express "reasoning-model" at all; `Route.reasoning` plus
`reasoning_knob_available(provider)` is the only machine-readable statement in
the tree that does. Assumed, operator may override.

A2 (Q4): a per-call reasoning override for the extraction leg is admissible
because it never mutates the endpoint object, so `EndpointLease.verify`'s
frozen equality set (which reads `endpoint.reasoning`) still passes unchanged;
the override travels in the request body only and is recorded on that leg's
`LLMAttempt`. Where the provider has no reasoning adapter the leg simply cannot
be made non-thinking, which is precisely the case R3 names ("typed notice,
never refusal, where a provider cannot honor the mode"). Assumed, operator may
override.

A3 (Q3): the split applies to attempt 0 only. Repair turns already feed the
model a diagnostic and a prior value — they are extraction-shaped by
construction — and under transactional dispatch `retry_max` is 0, so attempt 0
is the only attempt that exists there anyway. Assumed, operator may override.

A4 (Q5): R7's negative is proved two ways rather than one — a repository
reference census (the field's name occurs in no guard, rule, adjudication or
verification module) and a behavioral mutation test (flipping the field moves
no outcome). Assumed, operator may override.

A5: `B_a` defaults to 512, the mid-point of Q7's "extraction saturates by
`B_a ~ 256-512`", and is a Config value so a home can move it without code.
Assumed, operator may override.

## Questions for operator (STOP if non-empty) — TWO

**QO1 — the frozen-surface contact gate returned CONTACT. Row it, or halt?**
`tools/blast_radius.py` reports `frozen_surface_verdict: CONTACT`. Its computed
list, pasted verbatim, is in "Frozen-surface contact forecast" below. Every one
of the eight entries is tier `SYMBOL_INDIRECT` on the two generic English words
`call` and `complete`, and each carries the gate's own caveat "grep-based; not
proof of semantic contact". Measured disposal: M1-M5 below show ZERO
`.call(`/`.complete(` sites in all five named files — the hits are comment
prose, `caller`, `completed`, `_semantic_split_call_candidates`,
`_expected_call_outcome`, `_complete_channel_priority`. `INV-frozen-surfaces.md`
already carries a rowed precedent of exactly this shape ("False alarm rowed,
same date ... a substring false positive ... the disposal is by measurement
rather than by assurance").
RECOMMENDATION: **row it and proceed** — the measurements dispose all eight,
and no plan below writes to any of the five frozen surfaces. One word resumes
the tranche at `dr-plan-steps`.

**QO2 — does the extraction leg ride the existing authorization bundle?**
Under a v6 RunManifest EVERY `adapter.call` is transactional, so if the answer
is no, the shipped default reaches no live glm-5.2 run at all. Three roads,
priced:
  (a) **The extraction leg rides the bundle.** Cost: 0 lines outside `llm/`;
      the bundle keeps binding one prompt digest (leg `reason`), and both legs'
      prompts, raw bytes, token counts and notices land in the append-only
      attempt trace, so the record stays complete and replayable
      (`record_provider_attempt` performs no bound reconciliation — M11). What
      it gives up: "one authorization = one model-facing prompt" becomes "one
      authorization = one authorized prompt plus one derived extraction
      prompt". Guard shipped with it: the extraction leg is refused, with a
      typed notice, on any repair bundle, so this can never become a second
      bite at the contract.
  (b) **Split does not reach transactional seats.** Cost: 0 risk, and 0 value —
      R2 names glm-5.2 and R4 names the empty seat failure, both of which only
      occur on the transactional path.
  (c) **Extend the workflow transaction to authorize two legs.** Cost: edits to
      `workflow/` record shapes (the v6 wire-contract series) and ~6 preview/
      reserve call sites across `rules/`, `bridge/`, `informal/`, `referee/`,
      `scratch/` — outside C3's stated blast radius ("llm/ + provider profiles
      + the seat call path").
RECOMMENDATION: **(a)**. (b) contradicts R2 and R4 in the operator's own words;
(c) breaches C3.

## Out of scope (explicit)

- Enum escape values, structured refusal, CFR/EUR measurement — C1, "a later
  tranche".
- Any change to what counts as evidence — C1. `natural_stop` is recorded and
  never consumed (S8) precisely to keep that line.
- The schema hedge-impossibility audit named in the coercion note's consumption
  points — not requested here.
- Span-binding committed fields to scratchpad lines — the coercion note itself
  files it as "an option, not an obligation"; not requested here.
- Warrant, premise, validity or localization code — C3/C4 forbid it; nothing in
  the plan touches those trees.

## Frozen-surface contact forecast

`tools/blast_radius.py --files src/deepreason/llm/adapter.py
src/deepreason/llm/endpoints.py src/deepreason/llm/providers.py
src/deepreason/config.py src/deepreason/ontology/event.py --symbols call
build_body complete build_adapter LLMAttempt natural_stop split_leg
SPLIT_BUDGET_SEAT_PROTOCOL SPLIT_BUDGET_EXTRACTION_TOKENS`

`frozen_surface_verdict: CONTACT`

`frozen_surface_contacts` (verbatim, the tool's own list):

    {"surface": "harness.py event application and well-formedness", "tier": "SYMBOL_INDIRECT", "target": "call", "detail": "'call' referenced in src/deepreason/harness.py (grep-based; not proof of semantic contact)"}
    {"surface": "harness.py event application and well-formedness", "tier": "SYMBOL_INDIRECT", "target": "complete", "detail": "'complete' referenced in src/deepreason/harness.py (grep-based; not proof of semantic contact)"}
    {"surface": "replay-validation record formats (invariants.py)", "tier": "SYMBOL_INDIRECT", "target": "call", "detail": "'call' referenced in src/deepreason/invariants.py (grep-based; not proof of semantic contact)"}
    {"surface": "replay-validation record formats (invariants.py)", "tier": "SYMBOL_INDIRECT", "target": "complete", "detail": "'complete' referenced in src/deepreason/invariants.py (grep-based; not proof of semantic contact)"}
    {"surface": "manifest schemas and validators (run_manifest.py)", "tier": "SYMBOL_INDIRECT", "target": "call", "detail": "'call' referenced in src/deepreason/run_manifest.py (grep-based; not proof of semantic contact)"}
    {"surface": "manifest schemas and validators (run_manifest.py)", "tier": "SYMBOL_INDIRECT", "target": "complete", "detail": "'complete' referenced in src/deepreason/run_manifest.py (grep-based; not proof of semantic contact)"}
    {"surface": "qualification subject digests (qualification.py)", "tier": "SYMBOL_INDIRECT", "target": "call", "detail": "'call' referenced in src/deepreason/qualification.py (grep-based; not proof of semantic contact)"}
    {"surface": "qualification subject digests (qualification.py)", "tier": "SYMBOL_INDIRECT", "target": "complete", "detail": "'complete' referenced in src/deepreason/qualification.py (grep-based; not proof of semantic contact)"}

`frozen_adjacent_contacts` (verbatim):

    {"surface": "route_fingerprint serialization (llm/firewall.py)", "tier": "SYMBOL_INDIRECT", "target": "call", "detail": "'call' referenced in src/deepreason/llm/firewall.py (grep-based; not proof of semantic contact)"}

`reachability`: `call`, `build_body`, `complete`, `build_adapter` = REACHABLE.
`LLMAttempt`, `natural_stop`, `split_leg`, `SPLIT_BUDGET_SEAT_PROTOCOL`,
`SPLIT_BUDGET_EXTRACTION_TOKENS` = UNKNOWN. The last four do not exist yet, so
UNKNOWN is expected; for `LLMAttempt` the skill's required manual cross-check
was run and is the M8/M6 census below.

`disclosure_summary` (verbatim): "This change touches 4 of the five frozen
surfaces (locked-down files that a change can silently corrupt old,
already-recorded runs by touching): harness.py event application and
well-formedness; manifest schemas and validators (run_manifest.py);
qualification subject digests (qualification.py); replay-validation record
formats (invariants.py). It also touches frozen-adjacent ground:
route_fingerprint serialization (llm/firewall.py). 5 test file(s) and 10 map
document(s) assert on the touched targets today. Reachability here means a
syntactic call path exists from a known entry point; it does not prove the path
is ever actually exercised at runtime -- a symbol can be syntactically
reachable and still never fire because of a runtime precondition this gate does
not evaluate."

**Author's disposal, by measurement (M1-M8), pending the operator's word (QO1).**
No file in the plan writes to any of the five frozen surfaces. The only
record-shape change is three optional, defaulted fields on `LLMAttempt`, which
`DR-SUB-ontology` documents as the ordinary recipe for new per-call accounting.

## Blast-radius census

From the gate's own `consumers` field. Every hit classified.

| target | consumer | classification |
|---|---|---|
| `call` | 552 hits across 123 test files | MUST NOT MOVE — `LLMAdapter.call`'s signature, return type and single-leg behavior are unchanged when the plan is not armed, and `"auto"` does not arm for a `MockEndpoint` route (M13: provider resolves to `mock`, which has no reasoning adapter, so `reasoning_knob_available` is False). |
| `call` | 382 hits across 41 map documents | MUST NOT MOVE except `SUB-llm.md`, `CON-seats.md` (S9). |
| `complete` | 130 hits across 57 test files | MUST NOT MOVE — the three new `complete` parameters are keyword-only with sentinel defaults, so every existing call site is byte-identical in behavior. |
| `complete` | 28 hits across 18 map documents | MUST NOT MOVE except `SUB-llm.md` (S9). |
| `build_body` | 8 hits in `tests/test_llm_repair_capabilities.py`, `tests/test_providers.py`, `tests/test_vision.py` | MUST NOT MOVE — same keyword-only defaulted-parameter argument. |
| `build_body` | 1 hit in `docs/map/SUB-llm.md` | EXPECTED TO MOVE (S9). |
| `build_adapter` | 33 hits across 14 test files | MUST NOT MOVE — the two new constructor arguments are defaulted. |
| `build_adapter` | 13 hits across 6 map documents | MUST NOT MOVE except `SUB-llm.md` (S9). |
| `LLMAttempt` | 31 hits across 13 test files | MUST NOT MOVE — three optional fields with defaults; no existing construction or assertion changes. |
| `LLMAttempt` | 10 hits across 7 map documents | EXPECTED TO MOVE: `SUB-ontology.md` (S9). MUST NOT MOVE: `CON-schools.md`, `INV-signal-contract.md`, `SEAM-bridge-x-llm.md`, `SEAM-evaluation-x-ontology.md`, `SEAM-ontology-x-rules.md` — each pins a NAMED field subset or an `__all__` set, neither of which a new field alters. VERIFY IN THE RING: `SEAM-evaluation-x-ontology.md` and `SEAM-ontology-x-rules.md` assert exact `set(o.__all__) - N` literals; adding a FIELD does not change `__all__`, but the check must be re-run. |
| `qualification_digest` | `call`, `complete` -> tier PLAUSIBLE, "referenced in qualification.py" | MUST NOT MOVE — disposed by M9: the subject payload is a closed function of manifest + provider profile + policy preset; `Config` is not an input. Pinned by S10's pasted before/after digest. |
| `wheel_smoke_pins` | `call` -> `scripts/wheel_smoke.py`; `complete` -> `scripts/wheel_operational_smoke.py`, tier PLAUSIBLE | MUST NOT MOVE — no console entry point, MCP tool, schema sha or wheel-layout change is planned (R12). Confirmed by running both smokes at validation. |

Manual cross-check (required for the UNKNOWN reachability entries):
`grep -rn "LLMAttempt" tests/ docs/map/` -> the 13 test files and 7 map
documents already tabled above; no other consumer.

## Measurements

M1-M5 — the eight frozen-surface contacts are substring false positives.
`grep -n "\.call(\|\.complete(" <file>` over each named file:

    src/deepreason/harness.py       -> (no hits)
    src/deepreason/invariants.py    -> (no method-call hits)
    src/deepreason/run_manifest.py  -> (no method-call hits)
    src/deepreason/qualification.py -> (no method-call hits)
    src/deepreason/llm/firewall.py  -> 'call' only at line 357 ("before any
                                       rubric model call.") and 507 ("Resolve
                                       one school call without consulting
                                       semantic/model content.") — both prose.

Supports: no plan target semantically reaches a frozen surface (QO1).

M6 — `invariants.py`'s `attempt.*` reads are `ProviderAttemptV1` fields
(`authorization_bundle_ref`, `prompt_sha256`, `route_lease`, `outcome`), not
`LLMAttempt`. The one `LLMAttempt` read is line 1526-1527,
`attempt.contract_id for attempt in source.llm.attempt_trace` — a NAMED field.
`grep -rn "attempt_trace" src/deepreason/verification/` -> no hits. No wholesale
serialization of `LLMAttempt` exists in `invariants.py`.
Supports: three defaulted fields cannot change any `verify_root` output.

M7 — `grep -rn "LLMAttempt\|attempt_trace" src/deepreason/capabilities/state.py
src/deepreason/run_manifest.py src/deepreason/qualification.py` -> no hits.
Supports: `LLMAttempt` enters no digest and no manifest schema.

M8 — the manual census for the UNKNOWN reachability entries; results tabled in
"Blast-radius census" above.

M9 — `inspect.signature(qualification_subject_payload)` ->
`(manifest: 'RunManifest', profile: 'ProviderProfileV1') -> 'dict'`;
`'Config' in source or 'config' in source` -> `False`.
Supports: S10 — no profile moves, requalification price zero per home (R13).

M10 — today's behavior on an empty completion, ordinary path, `MockEndpoint`
returning `""` three times through `LLMAdapter.call`:

    TYPED FAILURE: SchemaRepairError role summarizer: no schema-valid output
    after bounded repair: no complete top-level JSON value at offset 0
    spend attempts: 3

and on the `null`-content shape, `OpenAICompatEndpoint` raises
`EndpointError("null content (finish_reason='length')")`
(`src/deepreason/llm/endpoints.py:400-403`).
Supports: S3's "before", and R11's "the old path yields the empty-completion
typed failure".

M12 — `grep -rn "_lease_ceiling" src/deepreason/controller.py` ->

    211:    def _lease_ceiling(self, instance: str) -> int | None:
    462:                ceiling = self._lease_ceiling(instance)
    587:        ceiling = self._lease_ceiling(instance)

Supports: the E43 mechanism this spec's S1/S7 bound against exists and is the
controller's own clamp ("the tuner clamps within lease", R9).

M13 — does `"auto"` arm for a `MockEndpoint` route?

    provider: 'mock' reasoning: None max_tokens: 512 ctx: None
    knob_available: False reasoning_disabled: False
    AUTO ARMS: False

Supports: the census's "MUST NOT MOVE" verdict for the 552 `call` and 130
`complete` test hits — no existing `MockEndpoint`-backed test can arm the
protocol by default, so the new code path is unreachable from them. The
regressions in S7 arm it explicitly.

M11 — `TransactionService.record_provider_attempt` performs no reconciliation
of reported tokens against the reservation's `completion_bound_tokens`; it
records `prompt_sha256=bundle.prompt_sha256` and `raw_ref=call.raw_ref`.
Supports: QO2 option (a) needs no `workflow/` change.

## Options

A — split only on the non-transactional path.
  Files: `llm/` only. Frozen contact: none. ~200 lines. Risk: low.
  REJECTED, cites M-none-needed: under a v6 manifest `build_adapter` sets
  `transaction_authority_required=True` and `call` refuses any dispatch without
  an authorization, so every live seat call is transactional. The feature would
  never fire in a real run — contradicting R2 ("default ON for ... glm-5.2")
  and R4.

B — extend the workflow transaction to authorize two legs.
  Files: `workflow/transaction_service.py`, `workflow/models.py`, plus the six
  preview/reserve sites in `rules/`, `bridge/`, `informal/`, `referee/`,
  `scratch/`. Frozen contact: v6 wire-contract record shapes. ~450+ lines.
  Risk: high. REJECTED: breaches C3's stated blast radius.

C — two legs inside one `adapter.call`, sharing the authorization and the
  ceiling. Files: `llm/split.py` (new), `llm/adapter.py`, `llm/endpoints.py`,
  `llm/__init__.py`, `config.py`, `ontology/event.py`. Frozen contact: none
  (M1-M7). ~324 lines of code+map, ~235 of tests. Risk: medium — concentrated
  in the two-leg dispatch inside `call`.
  CHOSEN, cites M11 (no `workflow/` reconciliation to break), M6/M7 (no record
  format or digest moves), M9 (no requalification price). Subject to QO2.

## Budget

Itemized (`python3 -c "print(sum([115,38,98,3,12,16,205,30,42]))"`):

    115  S1  src/deepreason/llm/split.py (new)
     38  S2  src/deepreason/llm/endpoints.py
     98  S3  src/deepreason/llm/adapter.py
      3  S4  src/deepreason/llm/__init__.py
     12  S5  src/deepreason/config.py
     16  S6  src/deepreason/ontology/event.py
    205  S7  tests/test_split_budget_protocol.py (new)
     30  S8  tests/test_seats_evidence_law.py
     42  S9  docs/map (SUB-llm, SUB-ontology, CON-seats)
    ----
    559  total changed lines
    324  excluding the two new test items

**~559 lines, 3 commits.** Over the ~300-line guidance, driven by the 235
lines of regression the operator's own R10/R11 require. Proposed ordered
commits inside this one tranche rather than separate tranches, because S6's
fields are written by S3's legs and cannot be delivered independently:

    commit 1 — S6 + S8 (the natural-stop typed field and its no-consumer proof)
    commit 2 — S1 + S2 + S3 + S4 + S5 + S7 (the protocol)
    commit 3 — S9 (map) — folded into commits 1 and 2 per R14 ("map moves in
               the same commits"); listed separately only for the budget.

Frozen surfaces touched: **none** (gate says CONTACT; measured disposal M1-M7;
operator's word requested at QO1).

Rubric: 6/6 yes — every R has a spec item with a machine-decidable accept
(R1→S1/S2/S3, R2→S5, R3→S2/S3/S7, R4→S3/S7, R5→REQUEST.md AUTHORITY block +
this spec's Q7/coercion citations, R6→S6, R7→S6/S8, R8→S7, R9→S1/S7,
R10→S7, R11→S7, R12→S4, R13→S10, R14→S9, R15→process, R16→S11); blast-radius
census pasted and every hit classified; frozen-surface contact forecast
recorded with the tool's verbatim list; every mechanism the request names
traced to code it reaches (E43's lease ceiling traced to
`EndpointLease.verify`'s `route.max_tokens` bound and
`Controller._lease_ceiling`; Q7's `B_a ~ 512` traced to S5's Config default);
every claim measured and every option priced; nothing untraceable to an R/C
number.
