# Preregistration: full defended-trial seat and configuration census

Frozen before any live chat completion. At this freeze point no chat
completion has occurred and `OLLAMA_API_KEY` is not present in the process.
The authenticated model catalog is a second required freeze point; catalog
discovery itself is limited to the provider's model-list endpoint and is not a
completion request.

Repository: `AHepi/DeepReason`. Branch:
`codex/live-full-judge-seat-matrix-20260901`. Shipped source parent under test:
`ec09b122b26bef2f99f26484ea70d19ad15e798b`. This branch is never merged into
or rebased onto `main` during the campaign. The pushed commit containing this
file is the preregistration freeze identity; the canonical SHA-256 of this file,
the matrix-domain document, and the later catalog are recorded alongside every
attempt.

## Purpose

This campaign asks which configurations the shipped DeepReason v6 defended
argument trial can compile and drive, and which first typed boundary prevents
it. It is a reachability census, not a model evaluation, leaderboard,
optimization exercise, elimination process, or statistical estimate.

Valid prose does not rank below a mechanically convenient form. The campaign
preserves the shipped parser and fallback path and records their events. A
parse refusal or malformed response is evidence about that path, not a claim
that the response's prose is epistemically invalid.

## Frozen authorities

Provider behavior is interpreted from first-party Ollama documentation:

- OpenAI compatibility and the actual `reasoning_effort` request field:
  <https://docs.ollama.com/api/openai-compatibility>
- Thinking may be enabled by a model even when a caller does not request a
  visible trace: <https://docs.ollama.com/capabilities/thinking>
- GLM-5.3 documents low, high, and max thinking and defaults to max, so this
  campaign never relies on omission:
  <https://ollama.com/library/glm-5.3:cloud>
- GLM-5.3-Flash documents always-on reasoning; a `none` request is therefore
  an observed compatibility probe, not an assertion that no trace exists:
  <https://ollama.com/library/glm-5.3-flash:cloud>

The following alphaXiv work informed coverage only. It does not supply an
optimization target or a preference ordering:

| Paper (retrieved 2026-09-01) | Frozen coverage consequence | Registered check |
|---|---|---|
| 2607.08535, *When the Judge Changes, So Does the Measurement* | Preserve parse/fallback records and keep evaluator replacements distinct. | `test_prose_and_parser_receipts_are_separate` |
| 2606.22329, *BabelJudge* | Treat reversed judge-seat order as a different case. | `test_domain_preserves_ordered_judge_swaps` |
| 2608.00243, *More Debate, Same Evidence* | Include homogeneous and heterogeneous judge panels. | `test_structural_domain_has_homogeneous_and_heterogeneous_panels` |

No heuristic learned from these papers is used to discard, rank, prioritize by
predicted merit, or statistically tighten a configuration.

## Frozen provider domain

Before the first completion, the authenticated `GET /v1/models` response from
`https://ollama.com/v1` is canonicalized, sorted, committed, and pushed as
`CATALOG.json`. Every returned model id enters the live domain except a typed
Kimi-K3 exclusion. No chat-capability prefilter exists: an unreachable,
non-chat, or strict-JSON-incompatible model remains in every applicable case
and yields a typed provider outcome.

Raw returned model ids are identity and are never normalized for case ids.
Exact duplicate ids refuse catalog freeze. Distinct raw ids that normalize to
the same non-Kimi string remain distinct cases. The raw fixture-id list is
UTF-8-bytewise sorted before hashing; its canonical-list SHA-256 is
`eaf7a61a8fdb4f7231dcac8f0fa2898ce48249b6c16dcfbe6e1cdea61a79ca64`.

Kimi normalization is exactly
`re.sub('[^a-z0-9]', '', unicodedata.normalize('NFKC', id).casefold())`.
The model is excluded iff that normalized string contains `kimik3`. Positive
test vectors are `kimi-k3`, `KIMI K3:cloud`, `kimi_k3/cloud`, and
`ollama/kimi-k3`. Negative vectors are `kimi-k2.6`, `kimi-k2.7-code`,
`minimax-m3`, and `glm-5.3`. Tags and cloud suffixes need no separate rewrite
because normalization leaves their letters after the decisive substring.

The preregistration fixture contains 22 predicted non-Kimi-K3 model ids. It is
used only to test enumeration arithmetic. The authenticated snapshot controls
the live roster and its exact digest controls resume.

For roster size `M`, the exact ordered live domain is:

```text
critic x defender x judge[0] x judge[1] x (variator absent | variator model)
```

It contains `M^4 + M^5` unique cases. Judge order is never collapsed. The
catalog anchor is the first model id under UTF-8 bytewise sort. The `M^2`
judge-pair prefix fixes critic and defender to that anchor and omits variator.
The `M^3` defender/judge prefix fixes only critic to the anchor and omits
variator. The `M^4` prefix enumerates every no-variator court. The `M^5` tail
adds every variator court. Generation keeps one `seen` set of canonical case
ids, so rows already emitted by an earlier prefix are not repeated. These are
useful milestones in one full set; no prefix is called exhaustive.

A live case id is `sha256:` plus the SHA-256 of the exact Python serialization
`json.dumps(payload, sort_keys=True, separators=(",", ":"),
ensure_ascii=False, allow_nan=False).encode("utf-8")` over
`{schema, catalog_sha256, critic, defender, judge0, judge1, variator}`. The
schema literal is `deepreason.full-judge-seat-case.v1`; variator absence is JSON
`null`. The expected set is regenerated independently as the literal Cartesian
product and must equal the generator's id set.

The guaranteed arm makes a small compatibility dispatch to the configured
critic, then drives a fixed valid ungrounded attack through the shipped court
so critic willingness cannot hide defender or judge reachability. The critic's
response does not cause that fixed trial and the report never calls the two a
causally integrated five-seat trial. It reports `critic_compatibility` and
`fixed_case_court_reachability` separately.

A separate, clearly labelled scheduler arm records natural critic behavior
once per critic and topology class, with all other roles fixed to the anchor.
Neither arm substitutes for the other.

## Frozen structural configuration domain

Offline enumeration is exact over the finite control-flow cases and literal
Cartesian subdomains declared in `MATRIX_DOMAIN.json`; the document marks each
group with `combination: cartesian` or `combination: enumerated_cases` and
carries the literal expected case-id set and digest.
It includes managed and direct construction, all frozen role-cardinality
values, ordered judge identities and family relationships, auxiliary-role
model diversity, status/legacy/judge gates, explicit defended authority,
school counts and bindings, presentation and output contracts, allowed
reasoning values, split protocol, paraphrase boundaries, and request-envelope
boundaries.

Arbitrary strings, arbitrary list lengths, arbitrary numeric values, future
provider settings, and future catalog models are unbounded. Reports therefore
say `exhaustive over frozen domain <digest>` and list these unbounded axes;
they never translate boundary coverage or pairwise coverage into "all".

The API-backed configuration sweep is a second exact live domain, separate
from the heterogeneous seat-assignment product. For each catalog model it puts
that model uniformly in every active court seat and crosses three model
profiles, two output modes, three output mechanisms, four typed reasoning
values (`"none"`, `"low"`, `"medium"`, and integer `2000`), and three split
protocols. The no-variator arm has 216 cases per model. The variator arm also
crosses paraphrase counts -1, 0, 1, 2, and 3, for 1080 per model. Total is 1296
per model, 28512 at fixture M=22. These are real full-court provider cases, not
offline stand-ins.

The transport sweep is not crossed with every heterogeneous `M^4+M^5` seat
assignment, and transport settings are uniform across active seats. That
unexecuted heterogeneous per-seat Cartesian cross is explicitly unbounded by
this preregistration and is never included in an "all configurations" claim.
The combined primary live domain is 5416400 cases at fixture M=22.

## Campaign-integrity invariants

Every executable court is compiled with an explicit
`CriticismPolicyV1(authority="defended_trial")`. Before any provider dispatch,
the runner checks the Config request, manifest authority, defender grant, each
judge grant, and optional variator grant. Encountering `observe_only` anywhere
is a campaign-integrity failure and stops before dispatch. `Observe_only` is
not a live case in this campaign.

Kimi K3 is rejected after model-id normalization of every final serialized
body's exact `model` field. The reasoning ban examines only the exact value of
the recognized `reasoning_effort` field; it rejects case-insensitive `high`,
`max`, and `xhigh`. It never substring-scans the body, so names such as
`minimax-m3` are not false positives. Every completion body must contain that
field. DeepReason integer reasoning above 2000 maps to high and is therefore a
typed excluded structural case. No live request omits the reasoning setting.

Each authenticated model receives explicit `none`, `low`, and `medium`
strict-JSON probes. These are compatibility observations, including for models
whose own documentation names only low/high/max. A probe form is mechanically
usable only when transport succeeds, content parses as one JSON object, and it
validates the frozen schema
`{"type":"object","required":["ok"],"properties":{"ok":{"const":true}},"additionalProperties":false}`.
A failed form never removes a model or a court case, and valid prose outside
that probe form is not classified as epistemically invalid. It remains
`provider_indeterminate` for this mechanical probe.

Every full court uses explicit `low`, regardless of probe outcome. Refusal of
that setting is recorded, not routed around. The runner records only the raw
response key set plus presence, byte length, and SHA-256 digest of `reasoning`,
`reasoning_content`, and `thinking`; it never persists trace text. A populated
GLM-5.3 trace under `none` remains exactly that observed fact.

One coordinator process first obtains a non-blocking exclusive `flock` on
`/tmp/deepreason-ollama-full-judge-seat-matrix.lock`; a second coordinator
refuses before provider contact. That coordinator owns one
`threading.BoundedSemaphore(3)` around every endpoint `complete()` call,
including the duration of its internal retries and any private endpoint.
Probe, qualification, and trial phases do not overlap. Peak endpoint calls in
flight must be at most three.

The frozen baseline seat-product route uses base URL `https://ollama.com/v1`, provider
`ollama`, `reasoning_effort=low`, split protocol off, JSON-text contracts,
timeout 300 seconds, two paraphrases, context ceiling 131072, and per-seat
completion cap 8192. The shipped transport performs at most four sequential
HTTP attempts per endpoint call; the manifest grants at most two schema-repair
calls after an initial call. Thus one logical seat call has a conservative
twelve-HTTP-attempt ceiling. At roster size `M`, the registered upper bound is
`12*(4*M^4 + 9*M^5) + 168*M`: baseline fixed-case courts, three probes per model,
and two anchor-role natural-critic topology arms. At fixture `M=22` this is
567840240 HTTP attempts. This is not a campaign-wide ceiling: the additional
live transport domain includes the shipped negative-paraphrase boundary, whose
Python slice can consume a provider-dependent number of returned edits. Its
per-request token, timeout, transport-retry, and repair bounds remain finite,
but this preregistration does not invent an edit-count bound. The offline soak
makes no provider request. Actual counts are recorded. Reports call
567840240 the baseline-seat upper bound, never the whole campaign bound.

## Frozen call sequence

The full guaranteed court uses the shipped v6 compiler, route seats, leases,
behavioral grants, and `run_argument_trial_from_case`. For `J` judge seats and
`P` returned paraphrases, the logical sequence is:

```text
critic + defender + J initial judges + [variator + P*J rerulings]
```

With two judges this is four calls without a variator and nine calls when two
paraphrases are returned. Repairs and split legs are typed additional attempts,
not additional seat configurations. A variator may validly return fewer than
requested paraphrases; assertions follow the returned count.

The fixed structural court uses three schools: target school `school-0`, critic
school `school-1`, and spare `school-2`, with explicit school-to-critic-seat
bindings and minimum foreign coverage one. The explicit manifest value
`defended_trial` resolves in `rules/crit.py` to `trial_required`, which invokes
`run_argument_trial_from_case(..., authority="status")`. Tests assert this
whole mapping rather than equating the three vocabularies.

## Registered outcomes

Each frozen case id has one mutually exclusive immutable terminal status:

| Outcome | Registered meaning |
|---|---|
| `configuration_refused` | A deterministic shipped compile/runtime refusal decided the configuration before provider-dependent content could. |
| `trial_outcome` | A semantic court result such as defence sustained, ensemble split, referential-integrity refusal, or paraphrase flip; not configuration impossibility. |
| `provider_indeterminate` | Transport failure, timeout, unavailable/non-chat model, malformed provider response, or provider silence. |
| `unexpected_error` | An unregistered driver failure; preserves the first boundary and blocks a PASS claim. |

Campaign/attempt state is separate from case status. `integrity_stop` means a
registered global invariant failed before further provider contact;
`interrupted` means an attempt ended with some cases unterminated and is
preserved; `pending` means no immutable case terminal exists. None of these is
counted as a tested case or written as a synthetic case result.

Every terminal record also has a separate `dispatch_extent` field containing
the exact ordered dispatch stages reached. `full_dispatch_reached` is a derived
boolean, not a competing status. An early `defence-sustained` may validly end
before the variator; it is `trial_outcome` with
`variator_reachability=not_exercised_by_outcome`, neither a refusal nor proof
that the variator configuration is reachable. The human `possible` count is
derived only from records that reached every seat unconditionally required by
the particular shipped branch. Reports always expose the underlying status and
extent, and use the phrase "configuration refused by the shipped path at
ec09b122b26bef2f99f26484ea70d19ad15e798b" rather than global impossibility.

For every refusal or indeterminate result, the record preserves the first
stage, exception type, typed code when present, pointer when present, exact
message after secret scanning, and dispatch history. Shipped refusals are
findings and are never hotfixed in this tranche. Results distinguish direct
court reachability, managed preparation reachability, contract/qualification
compatibility, and semantic court outcome.

Every provider response also produces two separate receipts. The prose receipt
contains an allowlisted non-git blob reference, byte count, and content digest
after secret scanning, so a human can inspect ordinary prose. The mechanical
receipt contains parser outcome, schema outcome, fallback events, and the
structured value when one exists. Parser failure never deletes or overwrites
the prose receipt and never becomes a configuration refusal. Hidden reasoning
trace text is the sole exception: only its presence, length, and digest are
retained.

Completion is exact set equality: the frozen expected case-id set equals the
terminal case-id set, with no duplicates. Until then, the report publishes
exact terminal, pending, interrupted, and category counts plus the next
resumable case id. It does not extrapolate.

## Credential and persistence gate

The only credential source is the process environment variable
`OLLAMA_API_KEY`. The key is never accepted on a command line, written to a
manifest, copied into an exception, printed, hashed, or committed. Manifests
name only `api_key_env="OLLAMA_API_KEY"`. Persistence uses an allowlist of
typed fields and never serializes request headers, full request bodies,
environment mappings, endpoint objects, or exception request dumps. Proposed
persisted bytes are additionally scanned in memory for the exact secret. A
match withholds the diagnostic and records
`SECRET_BEARING_DIAGNOSTIC_WITHHELD` without printing the key or its hash.

The domain and catalog digests bind every attempt. Terminal results are
immutable. An interrupted attempt is preserved unchanged and a fresh numbered
attempt root is created. Result files are written to a temporary sibling,
fsynced, and atomically renamed. A digest mismatch or corrupt driver state
refuses resume.

## Launch gates and stop rules

No live completion is authorized until this preregistration is committed and
pushed, the authenticated catalog is committed and pushed, the exact offline
matrix tests are green, the unchanged shipped judge ring is green, and the
experiment-owned Kimi-K3-free defended-court soak passes eight cycles through
the unchanged soak driver.

Missing credential, secret-bearing output, domain/catalog digest mismatch,
corrupt state, observe-only authority, forbidden model, forbidden reasoning,
or peak concurrency above three is a global stop. A case-level provider error
or shipped typed refusal is recorded and the immutable queue continues.

There is no campaign-level token budget. Per-request limits remain explicit and
recorded. No work in this campaign merges, rebases, pulls into, or updates
`main`; no historical run root is edited or relaunched.

## Registered reports

`RESULTS.md` leads with exact expected and terminal counts, category counts,
the frozen domain and catalog digests, and peak calls in flight. Human rows name
the configured model in every seat. The report states what is possible,
refused, provider-indeterminate, interrupted, and still pending without
ranking models or treating mechanical form as epistemic authority.

The registered primary live outcome is either the typed sequence reaching
critic, defender, judge 0, and judge 1 for each case, or the first typed refusal
or provider-dependent boundary verbatim after secret scanning. The registered
campaign outcome is exact terminal-set equality, or an explicitly incomplete
resumable queue with no exhaustiveness claim.
