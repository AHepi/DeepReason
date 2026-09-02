# Superseding preregistration: fully crossed defended-trial domain

Frozen before any live completion in this expanded domain. This is a pre-live
addendum to `PREREG.md` and `MATRIX_DOMAIN.json`; it does not alter either
earlier freeze. Where the earlier preregistration described separate seat and
uniform-transport products, this addendum supersedes that live-domain claim
with one exact finite Cartesian product in which every active seat has its own
transport tuple. The earlier fixture total of 5,416,400 is retained only as a
named early projection. It is not the size of this domain and is not evidence
that all live configurations were tested.

Repository: `AHepi/DeepReason`. Branch:
`codex/live-full-judge-seat-matrix-20260901`. This branch is never merged into,
rebased onto, or used to update `main` during the campaign. Historical run
roots and the earlier preregistration remain immutable.

## Claim and its boundary

This is an exact census over the literal finite axes frozen below. It uses no
sample. A completed report may say only “exhaustive over the fully crossed
finite domain identified by `FULL_CROSS_DOMAIN.json` and its recorded digest.”
It may not say “all DeepReason configurations.”

Universal “all” is impossible here. `Config` has 145 leaf settings before
the role collection is expanded; `EndpointSpec` has 17 fields per seat; role
lists and role names are open-ended; strings, numbers, policy dictionaries,
and future fields are unbounded. A finite live campaign cannot enumerate
those sets. The boundary is therefore declared first, not inferred from what
the runner happens to support.

The campaign is a reachability census, not a leaderboard, eliminator,
optimizer, statistical estimator, or formal adjudicator of prose. Valid prose
never ranks below a mechanically convenient representation. A parser,
schema, transport, or trial refusal records what the shipped path did; it does
not establish that the prose was invalid. No constraint filtering,
optimization, ranking, sampling, symmetry reduction, formal oracle over
prose, or mechanically learned pruning may remove a registered case.

## Exact fully crossed domain

The authenticated catalog contributes every raw model id except the one typed
Kimi-K3 exclusion below. Let its post-exclusion cardinality be `M`. Each
active seat independently receives the following tuple:

```text
model_id                 catalog, M values
model_profile            compact | standard | frontier
output_mode              text | json_object
output_mechanism         native_json_schema | grammar | json_text
reasoning_effort         "none" | "low" | "medium" | integer 2000
```

Thus the number of per-seat tuples is

```text
S = M * 3 * 2 * 3 * 4 = 72M.
```

`split_protocol` is a run-level axis with the three values `auto`, `on`, and
`off`. It is crossed once with the court and is not silently copied into the
seat tuple. Judge count is exactly `J in {2, 3}`. The active ordered roles are
`critic`, `defender`, `judge[0]` through `judge[J-1]`, and, in the second arm,
`variator`. Judge order and every other role assignment are identity-bearing;
no swap or repeated-seat symmetry is collapsed.

The no-variator arm has one null paraphrase value and exactly

```text
3 * S^(2+J)
```

cases for judge count `J`. The variator arm crosses the exact requested
paraphrase-count values `-1, 0, 1, 2, 3`, and therefore has exactly

```text
3 * 5 * S^(3+J) = 15 * S^(3+J)
```

cases. The whole frozen product is

```text
sum over J in {2,3} of [3*S^(2+J) + 15*S^(3+J)], where S=72M.
```

For the 22-model fixture, `S=1,584`. The exact `J=2` cardinality is
149,596,687,470,624,768; the exact `J=3` cardinality is
236,961,152,953,469,632,512; and their exact sum is
237,110,749,640,940,257,280. Enumeration code must prove these equalities
with integer arithmetic before provider contact.

This astronomical cardinality is part of the finding, not permission to
quietly replace the product with a tractable sample. If resources prevent
completion, the campaign reports the immutable completed cases and the exact
uncompleted remainder. It does not rename a prefix, pairwise cover, or reduced
set “all.”

## Catalog and request integrity

Before the first completion, the authenticated `GET /v1/models` response from
`https://ollama.com/v1` is canonicalized, committed, and pushed. Every raw
returned model id is preserved as identity. Exact duplicate raw ids refuse
catalog freeze; distinct raw ids remain distinct even if their normalized
forms coincide.

The only model exclusion is Kimi K3. Normalization is exactly
`re.sub('[^a-z0-9]', '', unicodedata.normalize('NFKC', id).casefold())`; a
model is excluded iff the result contains `kimik3`. This ban is checked again
against the exact serialized request body's `model` field before every
provider dispatch. It is not a family, capability, availability, probe, or
quality filter. Kimi K2 variants remain in the catalog.

Every executable case compiles an explicit defended-trial criticism policy.
`observe_only` is not an arm and is an integrity stop before dispatch. No
configuration default changes. The exact `reasoning_effort` field must be
present in each final body and must equal the shipped mapping of that seat's
registered typed configuration value. Case-insensitive string values `high`,
`max`, and `xhigh` are banned. An integer `2000` remains a distinct typed
configuration value and case-id input even though the shipped adapter maps it
to wire string `low`. String `low` and integer `2000` are therefore separate
cases with the same expected wire effort, and that alias is recorded rather
than collapsed. Provider acceptance, rejection, or hidden trace population is
recorded rather than used to remove later cases.

One coordinator holds the non-blocking machine-wide lock. Every endpoint
completion, including retries, repairs, split legs, and private endpoints, is
inside one shared `threading.BoundedSemaphore(3)`. No more than three provider
calls may be in flight. Concurrency changes execution order only; it never
changes membership or case identity.

## Canonical identity and completeness

A case payload contains exactly these top-level fields:

```text
schema
catalog_sha256
judge_count
split_protocol
paraphrase_count
seats
```

`schema` is the literal `deepreason.full-cross-judge-case.v1`.
`paraphrase_count` is JSON `null` when the variator is absent and one of the
five registered integers when it is present. `seats` is an ordered JSON array.
Its entries are, in order, critic, defender, every indexed judge, then the
optional variator. Each entry contains exactly `role`, `model_id`,
`model_profile`, `output_mode`, `output_mechanism`, and a typed `reasoning`
object with keys `kind` (`string` or `integer`) and `value`. The role literals
are `critic`, `defender`, `judge:0`, `judge:1`, optional `judge:2`, and
`variator`.

The canonical bytes are exactly:

```python
json.dumps(
    payload,
    sort_keys=True,
    separators=(",", ":"),
    ensure_ascii=False,
    allow_nan=False,
).encode("utf-8")
```

The case id is `sha256:` followed by the lowercase hexadecimal SHA-256 of
those bytes. The catalog digest is part of every id, so a changed roster
creates a different subject. Before dispatch, the generator's
arbitrary-precision length must equal the closed formula,
ordinal-to-payload and payload-to-ordinal must be inverse at every boundary of
every component, and a separately written tiny finite domain must be enumerated
completely and match the literal Cartesian case-id set and length-prefixed set
digest. Computing the 237-quintillion-row fixture set digest itself before
dispatch would require enumerating the very campaign the digest is meant to
precede, so it is not falsely registered as a preflight check. If the full
campaign ever terminates, its streamed terminal ordinal range and case-id
receipts become the completion artifact. No successful-only `findAll`,
deduplication, post-hoc constraint repair, or queue priority may alter that
set. These membership checks say nothing about the truth or validity of
provider prose.

## Research disposition

These alphaXiv papers informed checks and warnings only. None supplies an
optimization target, epistemic score, routing rule, or authority over prose.

| Paper | Adopted for this census | Explicitly rejected |
|---|---|---|
| [2604.08633, ICEPICK](https://www.alphaxiv.org/abs/2604.08633) | Finite scope, isolation, typed outcomes, and reproducible traces. | Coverage-guided BFS, random insertion, abstraction or duplicate reduction, and contract-based exclusions. |
| [2603.22093, Bounded Structural Model Finding](https://www.alphaxiv.org/abs/2603.22093) | Separate declared bounds, canonical ids, and completeness only relative to those bounds. | SMT pruning, symmetry or subsumption reduction, heuristic queues, and satisfying-only output. |
| [2607.18265, State Compression in Two-Agent LLM Relays](https://www.alphaxiv.org/abs/2607.18265) | A frozen inventory, exact ordered pair enumeration, and per-option receipts. | State compression, embedding pruning, ranking, and treating a schema as truth about prose. |
| [2608.00243, More Debate, Same Evidence](https://www.alphaxiv.org/abs/2608.00243) | Exact seat orders and separate receipts for each. | Routing, optimization, and statistical confidence claims. |
| [2607.08535, When the Judge Changes, So Does the Measurement](https://www.alphaxiv.org/abs/2607.08535) | Separate raw prose, parser, and fallback receipts. | Accuracy ranking or learned evaluator preference. |
| [2606.22329, BabelJudge](https://www.alphaxiv.org/abs/2606.22329) | Both judge orders and their raw outputs. | Degraded-gold labels, composite scores, or score-driven routing. |
| [2607.17083, Optimal Combinatorial Testing with Constraints](https://www.alphaxiv.org/abs/2607.17083) | A negative precedent: pairwise minima and heuristic profiles are not the full Cartesian product; post-hoc constraint fixes are unsafe. | Pairwise substitution, constrained reduction, or any “optimal” subset standing in for this registered set. |
| [1807.03975, Testing Global Constraints](https://www.alphaxiv.org/abs/1807.03975) | A tiny exact Cartesian mutation oracle and exact cardinality equality as runner tests. | Random domains, trial counts, and shrinking as evidence that the live campaign is exhaustive. |

## Registered evidence and outcomes

Every attempt first records its exact case payload and id, catalog digest,
full-cross-domain digest, branch commit, serialized request-body digest,
ordered dispatch extent, response metadata, and first typed boundary. Raw
prose is stored separately from parser/schema/fallback receipts. Hidden
reasoning trace text is never persisted; only its key presence, byte count,
and digest are retained. A schema result is evidence about that schema path,
never an epistemic verdict on otherwise valid prose.

Each case has exactly one immutable terminal outcome:

| Outcome | Registered meaning |
|---|---|
| `configuration_refused` | The shipped compiler or runtime refused the registered configuration before provider-dependent prose could decide it. |
| `trial_outcome` | The shipped defended court produced a semantic result after the required dispatch path. |
| `provider_indeterminate` | Transport, timeout, unavailable/non-chat model, malformed envelope, provider silence, or another provider-dependent boundary prevented a court result. |
| `unexpected_error` | The driver reached an unregistered failure; the first boundary is preserved and no PASS claim is allowed. |

Global `integrity_stop`, attempt `interrupted`, and case `pending` remain
separate from terminal outcomes. They never synthesize a result for an
untested case. A refused or indeterminate case remains in the denominator.
The record preserves the first stage, exception type, typed code and pointer
when present, exact message, and dispatch sequence verbatim. The runner never
works around a typed refusal and never edits shipped trial machinery to make a
case pass.

The registered campaign-level result is one of: (1) the full exact set has one
terminal record per canonical case id; (2) an integrity stop names the first
violated invariant and freezes all prior records; or (3) an interrupted or
resource-limited campaign reports the exact completed-id set and exact pending
remainder without an exhaustiveness claim. Provider success, judge unanimity,
parser acceptance, and guard acceptance are observations, not eligibility
filters.
