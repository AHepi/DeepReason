# spec-drift.md — 2026-08-13 audit

Two-direction census against the spec series (`docs/harness-spec-v1.3.md`
base + `v1.4`–`v1.7` amendments, all read; later files supersede
earlier ones on conflict).

**Counts: SPEC→TREE 187 unique backtick-quoted terms + 47 `##`
headings censused, 7 real `spec-orphan` findings (4 filename
cross-refs excluded as scan artifacts, not spec terms). TREE→SPEC 272
surface items censused (75 CLI flags, 75 config fields, 122 typed
strings), 203 `spec-silent` (34 CLI, 51 config, 118 typed), batched
below by feature area.**

| id | direction | target | gate | verdict | proof file | disposition |
|---|---|---|---|---|---|---|
| SD1 | spec→tree | `ContextRequest` | pass | spec-orphan (code has `ContextRequestV1`) | proof/spec-orphan-detail.txt | parked |
| SD2 | spec→tree | `` R_t `` (Pareto-axis notation) | pass | covered (code identifier is `reach`) | proof/spec-orphan-detail.txt | baseline |
| SD3 | spec→tree | `codec:json` | pass | spec-orphan | proof/spec-orphan-detail.txt | parked |
| SD4 | spec→tree | `deepreason.config.load` | pass | covered (unqualified `load()` exists, dotted path isn't literal) | proof/spec-orphan-detail.txt | baseline |
| SD5 | spec→tree | `novel-case` | pass | spec-orphan | proof/spec-orphan-detail.txt | parked |
| SD6 | spec→tree | `positions.accepted` | pass | covered (concept present as separate `positions`/`accepted` terms, not a literal dotted path) | proof/spec-orphan-detail.txt | baseline |
| SD7 | spec→tree | `workflow-resume-decision.v1` | pass | spec-orphan (3-way spelling drift, see detail) | proof/spec-orphan-detail.txt | parked |
| SD8 | tree→spec | CLI flags (34/75 spec-silent) | pass | spec-silent, batched | proof/tree-cli-flags.txt | parked |
| SD9 | tree→spec | config fields (51/75 spec-silent) | pass | spec-silent, batched | proof/tree-config-fields.txt | parked |
| SD10 | tree→spec | typed strings — manifest-generation V3–V6 (28/118) | pass | spec-silent, batched | proof/tree-typed-strings.txt | parked |
| SD11 | tree→spec | typed strings — preparation/managed-run (20/118) | pass | spec-silent, batched | proof/tree-typed-strings.txt | parked |
| SD12 | tree→spec | typed strings — run-input/manifest-file (11/118) | pass | spec-silent, batched | proof/tree-typed-strings.txt | parked |
| SD13 | tree→spec | typed strings — routing/bridge presentation (9/118) | pass | spec-silent, batched | proof/tree-typed-strings.txt | parked |
| SD14 | tree→spec | typed strings — credential/path-safety (9/118) | pass | spec-silent, batched | proof/tree-typed-strings.txt | parked |
| SD15 | tree→spec | typed strings — judge-family/seats (6/118) | pass | spec-silent, batched | proof/tree-typed-strings.txt | parked |
| SD16 | tree→spec | typed strings — scratch/embedder, admission/qualification, public defaults, other (35/118) | pass | spec-silent, batched | proof/tree-typed-strings.txt | parked |

## Direction 1: SPEC→TREE

Census (`proof/spec-terms.txt`): every `` `backtick-quoted` `` token in
`docs/harness-spec-*.md` (187 unique after filename-prefix dedup) plus
every `##`-level heading (47). Filename cross-refs inside the spec
docs themselves (`` `AGENT.md` ``, `` `harness-spec-v1.4-amendment.md` ``,
etc. — 4 of the 11 raw `SPEC-ORPHAN` hits) are doc-to-doc pointers, not
spec-defined terms; excluded from the table above as scan artifacts,
not findings.

**SD1 — `ContextRequest`.** `rg -w` against `src/deepreason/` misses
because the shipped identifier is `ContextRequestV1`
(`conjecture_turn.py`, `scratch/conjecture.py`, `llm/wire.py`,
`rules/conj.py`, `invariants.py`, `harness.py`) — a version suffix the
spec's bare name doesn't carry. **Verdict: spec-orphan** (naming
mismatch, not a missing feature). Park: update the spec's next
amendment to spell the versioned name, or confirm `ContextRequest` is
meant as the version-agnostic concept name (operator call).

**SD2 — `` R_t ``.** Spec prose: "Pareto frontier over `PARETO_AXES`
(default: `HV_B`, reach `R_t`, criteria-coverage)" — `R_t` is
mathematical notation for the "reach" axis, not a code identifier.
`reach` itself is a live field (`state.reach`, `harness.py`).
**Verdict: covered** — no action.

**SD3 — `codec:json`.** Spec (§10, informal-domain `eval:program`
commitments): "the candidate's content is `codec:json` conforming
to...". The `Artifact.codec` field exists (`ontology/artifact.py`,
default `"utf8"`), but no call site sets or checks a `"json"` codec
value. **Verdict: spec-orphan** — either the json-codec convention for
informal-domain program-eval candidates was never built, or it's
expressed under a different field/value the census didn't catch.
Park: confirm with someone who knows the informal-domain skeleton-wf
path.

**SD4 — `deepreason.config.load`.** Spec: "`deepreason.config.load`
and construct endpoints through...". `config.py` has `def load(path
...)`, and `compat_eval.py` does `from deepreason.config import load`.
The concept is fully present; only the fully-qualified dotted spelling
as one literal token is absent (nobody writes
`deepreason.config.load(...)` — they import `load` unqualified).
**Verdict: covered** — no action; scan-form limitation, not drift.

**SD5 — `novel-case`.** Spec §10.5: "Informal problems SHOULD pin
`novel-case` criteria: the candidate commits, via its skeleton, to
expectations over unseen cases." No form of `novel-case` / `novel_case`
appears anywhere under `src/`. **Verdict: spec-orphan** — the
Lakatos-style novel-fact criteria pin described in the spec has no
visible implementation. Park: confirm whether this shipped under an
unrelated name or was never built.

**SD6 — `positions.accepted`.** Spec (v1.7 amendment, adjudication-
blindness section): "A reader of `positions.accepted` MUST consult
this...". No literal dotted path exists, but `findings.py` both
computes `summary["positions"]` and separately tracks "accepted"
positions in prose/logic. Reads as the spec using a dotted-path style
to name a concept informally, not a real attribute-access chain.
**Verdict: covered** — no action.

**SD7 — `workflow-resume-decision.v1`.** Spec (v1.5 amendment §H):
"Continuation may append a typed `workflow-resume-decision.v1` control
...". The tree itself is inconsistent about this name: `storage/
objects.py` and `workflow/replay.py`/`harness.py` use the string
`"workflow-resume-decision"` (no `.v1` suffix), while `workflow/
models.py` uses `"workflow.resume-decision.v1"` (dot before "resume",
hyphen inside "resume-decision", `.v1` suffix) — a *third* spelling,
matching neither the spec's `workflow-resume-decision.v1` nor the
other two code sites exactly. **Verdict: spec-orphan** (by literal
string match) **and a genuine 3-way naming inconsistency inside the
tree itself**, independent of the spec question. Park: this is worth
a small change tranche on its own — pick one canonical spelling and
conform all three sites (plus the spec) to it.

## Direction 2: TREE→SPEC

Census: 75 CLI flags (`rg -o -N '"--[a-z][a-z0-9-]*"'
src/deepreason/cli/main.py`), 75 config fields (`rg -o -N
'^    [A-Z][A-Z0-9_]*:' src/deepreason/config.py`), 122 typed
error/refusal strings (`rg -o -N '"[A-Z][A-Z0-9_]{6,}"'
src/deepreason/run_manifest.py src/deepreason/preparation.py`). Each
checked with `rg -l -F <item>` against `docs/harness-spec-*.md`.

**The headline shape, before the per-batch detail:** 203/272 (75%) of
the shipped surface is spec-silent. Sampling the misses shows this is
**not evenly distributed noise** — it clusters almost entirely around
features CLAUDE.md itself flags as living in a separate documentation
series: *"note 'V6' elsewhere names the RunManifest/policy generation
and the wire-contract series, NOT this spec document series."* 28 of
the 118 spec-silent typed strings are literally `V3_`/`V4_`/`V5_`/
`V6_`-prefixed refusal codes; most of the rest are preparation/
managed-run, admission/qualification, judge-seats, and bridge-routing
concerns that are all downstream of that same generation lineage. This
audit cannot determine, from the tree alone, whether that separate
series fully covers this surface elsewhere (in which case
`harness-spec-*.md` being silent on it is correct-by-design and not a
finding) or whether it's a genuine, uncovered documentation gap. That
determination is parked to the operator — see `PARKED.md`.

**SD8 — CLI flags (34/75 spec-silent, `proof/tree-cli-flags.txt`):**
`--allow-partial, --api-key-env, --attached-evidence,
--blind-same-model-judges, --capsule, --category, --concurrency,
--context-window-tokens, --control-plane-policy, --credential-env,
--criticism-seat, --dry-run, --engine-profile,
--expected-manifest-digest, --interval, --judge-family,
--maximum-completion-tokens, --model-revision, --no-browser,
--output-profile, --pack-profile, --production-contracts,
--provider-profile, --reshape-question, --retrieved-at,
--rubric-policy, --run-input-digest, --shallow, --single-model,
--title, --token-budget, --top-k, --upto, --workload-profile`.

**SD9 — config fields (51/75 spec-silent,
`proof/tree-config-fields.txt`):**
`ADJUDICATION_STATUS_AUTHORITY_ENABLED, ADVISORY_TRIALS_PER_CYCLE,
ARGUMENTATIVE_AUTHORITY, ARG_CRIT_PER_CYCLE, ATTACK_ENTROPY_FLOOR,
BROWSER_PER_CYCLE, CALIBRATION_RECEIPT, CHUNK_MAX_CHARS,
COMPLEMENT_ALWAYS, CONTROLLER, CRIT_BATCH_K, CRIT_DEBT_CEILING,
CX_RETRY_MAX, DISC_ATTEMPTS_MAX, DISC_COOLDOWN,
EMBEDDER_FAILURE_POLICY, EMBEDDER_MODEL, ENGAGED_CRITICISM_AUTHORITY,
FOCUS_FAMILY, FOCUS_PROBLEM, FUZZ_N, GATE_ORBIT_MIN, GEN_MAX,
GEN_PROPOSE_PERIOD, GROUNDING_USE_EVIDENCE_LAMBDA,
HV_CONTENT_MAX_CHARS, IMPORT_POLICY, INFRASTRUCTURE_REVIEW_AUTHORITY,
JUDGE_SEATS_ENABLED, JUDGE_SUMMONS_COOLDOWN, JUDGE_SUMMONS_PER_CYCLE,
LIVENESS_QUEUE, MIN_ATTACKS_FOR_RITUAL, NEIGHBOURHOOD_N,
PAIRWISE_AUTHORITY, PROP_MAX, PROP_PROBATION_EVENTS,
PROP_PROPOSE_PERIOD, REACH_COVERAGE_MIN, RECRIT_STANDING,
RESEARCH_ATTEMPTS_MAX, RESEARCH_ATTENDED, RESEARCH_BACKEND,
RESEARCH_COOLDOWN, RESEARCH_PERIOD, RESEED_RATIO_MAX,
RUBRIC_TRIALS_PER_ARTIFACT, SPEC_INJECTION, TEXT_RUBRIC_AUTHORITY,
VISION_CRIT_PER_CYCLE, WEBSITE_CHUNKED`.

**SD10–SD16 — typed error/refusal strings (118/122 spec-silent,
`proof/tree-typed-strings.txt`), batched by feature area** (full
per-string list in the proof file):

- SD10 manifest-generation V3/V4/V5/V6 (28): version-gated refusal
  codes (`V3_POLICY_REQUIRED`, `V4_CONTROL_POLICY_REQUIRED`,
  `V4_ENGINE_CONFIG_INVALID`, `V5_ACTIVE_INQUIRY_REQUIRED`,
  `V5_CAPABILITY_POLICY_REQUIRED`, `V5_CAPABILITY_PROFILE_MISMATCH`,
  `V5_PROTOTYPE_CAPABILITY_POLICY_FORBIDDEN`,
  `V6_BEHAVIORAL_CAPABILITY_PLAN_REQUIRED` and 12 more
  `V6_BEHAVIORAL_*`, `V6_CAPABILITY_POLICY_REQUIRED`,
  `V6_CAPABILITY_PROFILE_MISMATCH`,
  `V6_CONFIG_REFEREE_CRITIC_SEAT_REQUIRED`,
  `V6_CONTRACT_DECOMPOSITION_*` ×3, `V6_FORMALIZATION_UNAVAILABLE`,
  `V6_RESEARCH_UNAVAILABLE`, `V6_TRANSACTIONAL_INQUIRY_REQUIRED`,
  `UNSUPPORTED_RUN_MANIFEST_VERSION`).
- SD11 preparation/managed-run (20): `PREPARATION_*` (12 codes),
  `MANAGED_RUN_IDENTITY_MISMATCH`, `MANAGED_RUN_ID_INVALID`,
  `MANAGED_RUN_NOT_FOUND`, plus 5 more in this family.
- SD12 run-input/manifest-file (11): `RUN_INPUT_DIGEST_REQUIRED`,
  `RUN_INPUT_EVIDENCE_BUDGET_EXCEEDED`, `RUN_INPUT_MANIFEST_MISMATCH`,
  `RUN_INPUT_REQUIRED`, `RUN_INPUT_SCHEMA_MISMATCH`,
  `RUN_MANIFEST_CONFLICT`, `INVALID_RUN_MANIFEST`,
  `MANIFEST_FILE_UNAVAILABLE`, `MANIFEST_FILE_UNSAFE`,
  `MANIFEST_HASH_INVALID`, `MANIFEST_HASH_MISMATCH`.
- SD13 routing/bridge presentation (9): `ROUTE_SEAT_PRESENTATION_*`
  ×6, `BRIDGE_REVIEWER_SEATS_MISMATCH`,
  `BRIDGE_UNRESOLVED_SUCCESS_SAFETY_DISABLED`,
  `GROUNDED_BRIDGE_MANIFEST_V3_REQUIRED`.
- SD14 credential/path-safety (9): `O_CLOEXEC`, `O_NOFOLLOW`,
  `O_DIRECTORY`, `CREDENTIAL`, `PASSWORD`,
  `ROUTE_URL_CREDENTIAL_FORBIDDEN`, `PROVIDER_CREDENTIAL_MISSING`, and
  2 more.
- SD15 judge-family/seats (6): `JUDGE_FAMILY_AND_BLIND_SAME_MODEL_CONFLICT`,
  `JUDGE_SEATS_ENABLED`, `JUDGE_SUMMONS_COOLDOWN`,
  `JUDGE_SUMMONS_PER_CYCLE`, `SECOND_JUDGE_FAMILY_REQUIRED`,
  `SECOND_JUDGE_ROUTE_NOT_FOUND`.
- SD16 remainder (35): scratch/embedder (5:
  `SCRATCH_EMBEDDER_FAILURE_POLICY_INVALID`,
  `SCRATCH_EMBEDDER_MODEL_UNRESOLVED`, `SCRATCH_MANIFEST_V3_REQUIRED`,
  `EMBEDDER_FAILURE_POLICY`, `EMBEDDER_MODEL`), admission/
  qualification/seats (4: `ADMISSION_PROBLEM_MISMATCH`,
  `QUALIFICATION_NOT_CONFIGURED`, `SCHOOL_SEATS_DISABLED`,
  `SEAT_BINDINGS_SNAPSHOT_NAME`), public API defaults (3:
  `PUBLIC_DEFAULT_CYCLES`, `PUBLIC_DEFAULT_TOKEN_BUDGET`,
  `PUBLIC_MAX_CYCLES`), and 23 miscellaneous single-subsystem codes
  (`CAPABILITY_MANIFEST_V5_REQUIRED`, `CONTROL_PLANE_MANIFEST_V4_REQUIRED`,
  `CONTROL_PLANE_POLICY_REQUIRED`,
  `CRITICISM_ACTIVE_CONJECTURE_REQUIRED`,
  `CRITICISM_MANIFEST_V4_REQUIRED`,
  `CRITICISM_SEATS_REQUIRE_SCHOOL_ROUTED_CRITICISM`,
  `ENDPOINT_REQUIRED`, `ENGAGED_CRITICISM_AUTHORITY`,
  `INVALID_CONCURRENCY`, `INVALID_ENGINE_CONFIG`, `MODEL_REQUIRED`,
  `PROPERTY_RUBRIC_TRIAL_FORBIDDEN`, `PROP_PROPOSE_PERIOD`,
  `RUBRIC_INPUT_FORBIDDEN`, `SINGLE_MODEL_MUST_BE_CONCRETE`,
  `SINGLE_MODEL_ROUTE_AMBIGUOUS`, `SINGLE_MODEL_ROUTE_REQUIRED`,
  `TEXT_AUTHORITY_POLICY_MANIFEST_MISMATCH`, `UNRESOLVED_MODEL`,
  `WORKLOAD_PROFILE_REQUIRED`, and 4 more single-mention codes).

## Outlet notes

No amendment was drafted now — every `spec-silent` batch's parked
prompt asks for a spec-amendment draft (append-only, never an edit to
existing spec text), routed `dr-change-orchestrator`, per this
worker's own Outlets table. SD1/SD3/SD5/SD7's `spec-orphan` prompts
are likewise parked, not fixed here.
