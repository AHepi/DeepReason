# Request: the two-call seat protocol — deliberation and emission become separate calls
Captured: 2026-08-22 from the operator's tranche-opening message (single message, this window).

## Map ids resolved (map preflight, before any design)

- `DR-SUB-llm` — `src/deepreason/llm/` (adapter, route firewall, packs, wire
  contracts, repair, profiles, endpoints, providers, budget). Primary.
- `DR-CON-seats` — how a role becomes a provider request: `select_lease`,
  `EndpointLease`, the one-profile-per-run mint.
- `DR-INV-frozen-surfaces` — read before designing. Five frozen surfaces;
  none is `llm/`. Its own "Where authority is allowed to live instead"
  section is directly load-bearing here: "When a change needs a new per-run
  mode, put it on `Config` (`config.py`), never on the manifest."
  Frozen-adjacent: `route_fingerprint` output format (`llm/firewall.py`).
- `DR-SEAM-llm-x-manifest` — the manifest promises a closed set of exact
  provider routes, one `Route` per role seat.
- `DR-SEAM-llm-x-workflow` — `workflow/` decides by what recorded authority a
  provider may be spoken to; `llm/` is the only place that speaks to one.
  This seam is the one the split protocol presses on (one authorization
  bundle, two provider legs) and is treated in SPEC.md.
- `DR-SUB-ontology` — owns `LLMAttempt` / `LLMCall` record shapes (R6's
  per-attempt field lands here).

## Verbatim

> Change tranche: the two-call seat protocol — deliberation and
> emission become separate calls, so a truncated reasoning trace
> yields an answer instead of an empty seat failure. Route through
> dr-change-orchestrator; the workflow's own stops apply.
>
> SETUP (fresh container): git fetch origin main && git checkout -B
> claude/two-call-seat-protocol-g5rm2x origin/main; git merge-base
> --is-ancestor e1ea05e82 HEAD || re-fetch. pip install -e .
> --break-system-packages -q; pip install pytest pytest-xdist
> jsonschema --break-system-packages -q. Use `python -m pytest`, never
> bare pytest. Read CLAUDE.md in full; load dr-drive-harness,
> dr-explain-to-operator.
>
> AUTHORITY for REQUEST.md: the operator approved (2026-08-22) the
> consumption points of docs/RESEARCH_FINDINGS_Q1Q10_2026-08-22.md
> (Q7, "provider profiles") and
> docs/RESEARCH_STRUCTURED_OUTPUT_COERCION_2026-08-22.md (two-call
> absorption) — read both sections IN FULL and ledger them. External
> findings are design intelligence; everything lands as this repo's
> own tested behavior.
>
> SCOPE:
> S1 SPLIT-BUDGET PROTOCOL: a seat call becomes reason-at-B_r then a
>    separate non-thinking extraction pass at B_a (order ~512),
>    feeding the possibly-truncated trace. Shipped as a per-profile
>    Config choice with the default ON for reasoning-model profiles
>    (glm-5.2), OFF where a profile is non-thinking. All
>    configurations compile (typed notice, never refusal, where a
>    provider cannot honor the mode).
> S2 NATURAL-STOP RECORDED: whether the reasoning call terminated on
>    its own becomes a typed per-attempt field (external work: ~99%
>    PPV correctness signal, currently discarded). Recorded, not
>    acted on — no gate or label may consume it (seats/evidence law).
> S3 EMISSION SCHEMAS STAY LIGHT: the extraction call's schema is the
>    minimal envelope; do not move deliberation constraints into it
>    (the dose-response on schema weight is steep).
> S4 CEILING LAW RESPECTED: both calls' token budgets sit inside the
>    route lease ceiling from the P9 fix (E43) — the tuner clamps
>    within lease; add the regression that the split never exceeds it.
> OUT OF SCOPE: enum escape values / CFR / EUR measurement (a later
> tranche); any change to WHAT counts as evidence.
>
> COST, reported not stopped: profile changes move qualification
> subject digests — state which profiles moved and the requalification
> price per home (~14 min battery), per the standing rule.
>
> TESTS: offline regression with a synthetic truncated trace — the
> old path yields the empty-completion typed failure, the new path
> yields the extracted answer; mutation-proven. Wheel smokes only if
> the public surface moves (it should not).
>
> KNOWN CURRENT STATE: gate baseline 0 failed (3829 at e1ea05e82);
> docs_verify 3 pre-existing shallow-clone failures; 5 MCP-thread
> flaky under -n 4; sweep retired. Parallel windows: a live-run
> tranche (experiments only) and a Rung D tranche
> (warrants/validity + a localization module) — your blast radius is
> llm/ + provider profiles + the seat call path; if you find yourself
> editing warrant or premise code, STOP and say so.
>
> GATE: ring while iterating; full gate at the boundary; docs_verify
> full. Map moves in the same commits. Commit and push every phase
> boundary (retry 2s/4s/8s/16s). Deliver R-by-R with pasted PROOF,
> closing with one line: what a glm-5.2 seat that burns its cap now
> produces, and what it cost before.

## Requirements

R1 (behavior): "a seat call becomes reason-at-B_r then a separate
non-thinking extraction pass at B_a (order ~512), feeding the
possibly-truncated trace."

R2 (behavior): "Shipped as a per-profile Config choice with the default
ON for reasoning-model profiles (glm-5.2), OFF where a profile is
non-thinking."

R3 (behavior): "All configurations compile (typed notice, never
refusal, where a provider cannot honor the mode)."

R4 (behavior): "deliberation and emission become separate calls, so a
truncated reasoning trace yields an answer instead of an empty seat
failure."

R5 (process): "the operator approved (2026-08-22) the consumption
points of docs/RESEARCH_FINDINGS_Q1Q10_2026-08-22.md (Q7, 'provider
profiles') and docs/RESEARCH_STRUCTURED_OUTPUT_COERCION_2026-08-22.md
(two-call absorption) — read both sections IN FULL and ledger them."

R6 (behavior): "whether the reasoning call terminated on its own
becomes a typed per-attempt field."

R7 (behavior): "Recorded, not acted on — no gate or label may consume
it (seats/evidence law)."

R8 (behavior): "the extraction call's schema is the minimal envelope;
do not move deliberation constraints into it."

R9 (behavior): "both calls' token budgets sit inside the route lease
ceiling from the P9 fix (E43) — the tuner clamps within lease."

R10 (artifact): "add the regression that the split never exceeds it."

R11 (artifact): "offline regression with a synthetic truncated trace —
the old path yields the empty-completion typed failure, the new path
yields the extracted answer; mutation-proven."

R12 (process): "Wheel smokes only if the public surface moves (it
should not)."

R13 (process): "COST, reported not stopped: profile changes move
qualification subject digests — state which profiles moved and the
requalification price per home (~14 min battery), per the standing
rule."

R14 (process): "GATE: ring while iterating; full gate at the boundary;
docs_verify full. Map moves in the same commits."

R15 (process): "Commit and push every phase boundary (retry
2s/4s/8s/16s)."

R16 (artifact): "Deliver R-by-R with pasted PROOF, closing with one
line: what a glm-5.2 seat that burns its cap now produces, and what it
cost before."

## Standing constraints

C1: "OUT OF SCOPE: enum escape values / CFR / EUR measurement (a later
tranche); any change to WHAT counts as evidence." — SCOPE block.

C2: "External findings are design intelligence; everything lands as
this repo's own tested behavior." — AUTHORITY block.

C3: "your blast radius is llm/ + provider profiles + the seat call
path; if you find yourself editing warrant or premise code, STOP and
say so." — KNOWN CURRENT STATE block.

C4: "Parallel windows: a live-run tranche (experiments only) and a
Rung D tranche (warrants/validity + a localization module)." — KNOWN
CURRENT STATE block.

C5: "Use `python -m pytest`, never bare pytest." — SETUP block.

C6: "KNOWN CURRENT STATE: gate baseline 0 failed (3829 at e1ea05e82);
docs_verify 3 pre-existing shallow-clone failures; 5 MCP-thread flaky
under -n 4; sweep retired." — the baselines every verdict compares
against.

C7: "Route through dr-change-orchestrator; the workflow's own stops
apply." — opening line.

C8 (repo law, CLAUDE.md, binding on this tranche): "The root sweep is
RETIRED as an instrument (operator ruling 2026-08-22)." Consistent
with C6's "sweep retired".

## Open questions (for dr-spec-change)

Q1: S1 says "per-profile Config choice with the default ON for
reasoning-model profiles (glm-5.2), OFF where a profile is
non-thinking". Which "profile" is meant — `ModelProfile`
(compact/standard/frontier, a presentation profile that carries no
reasoning information), the `ProviderProfileV1` at the application
boundary, or the per-seat `Route.reasoning` knob that is the only
machine-readable statement of whether a seat thinks?

Q2: Under a v6 RunManifest every `adapter.call` is transactional
(`transaction_authority_required`), and one authorization bundle binds
exactly one prompt digest and one token reservation. A split call
issues two model-facing provider requests. Does the second (extraction)
leg ride the existing bundle, or does S1 not reach transactional seats?
This decides whether the shipped default reaches a live glm-5.2 run at
all.

Q3: Does the split apply to every attempt in the repair session, or
only to the first generation (attempt 0), repair turns being already
extraction-shaped?

Q4: "non-thinking extraction pass" requires setting the reasoning knob
off for leg 2, but `EndpointLease.verify` freezes `reasoning` in its
equality set. Is a per-call reasoning override on a frozen route
admissible as a declared protocol property, or is it a route
substitution?

Q5: R7 says no gate or label may consume the natural-stop field. What
instrument proves a negative here (a grep-shaped check, an import
boundary, or a test that mutates the field and shows no outcome moves)?

## Amendments

(append-only)
