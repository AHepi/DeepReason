<!-- DR-SUB-manifest -->
Verified-at: 08dcdf3c
Verify: python -m pytest tests/test_v6_only_manifest_loading.py tests/test_reusable_qualification.py tests/test_qualification_tier.py tests/test_v6_route_seat_behavioral_capability_plan.py -q
Owns: src/deepreason/run_manifest.py, src/deepreason/qualification.py, src/deepreason/cli/doctor.py
Seams: DR-SEAM-bridge-x-manifest, DR-SEAM-llm-x-manifest, DR-SEAM-manifest-x-schools
Seams-undocumented: authority x manifest, capabilities x manifest, harness x manifest, manifest x packs-and-token-economy, manifest x rules, manifest x run-identity, manifest x scheduler, manifest x scratch, manifest x verification, manifest x workflow

# Manifest — the frozen plan a run may execute, and the evidence its routes can execute it

## What it is

Routing, policy and per-seat authority are resolved once, before the first
provider call, and frozen into one canonical JSON document bound to the run
root. `run_manifest.py` compiles and validates that document; `cli/doctor.py`
exercises every route/contract pair the document authorizes against the live
provider and returns a sanitized qualification report; `qualification.py` keys
that report by a behaviour-subject digest so an unchanged provider and policy
need not be re-measured for every run. Only schema version 6 loads — versions 1
through 5 are discriminated out of the raw bytes before any model validation, so
a historical root fails with a typed version error instead of a validation
error. The manifest is also deliberately process metadata: it names the
environment variable holding a credential but never a credential value, it
rejects query strings and userinfo in a route URL rather than filter them, and
it imports nothing from the harness, the ontology or the adjudication graph.
`check: grep -q "if 1 <= schema_version <= 5:" src/deepreason/run_manifest.py && grep -q "class UnsupportedRunManifestVersionError" src/deepreason/run_manifest.py && grep -q "^def _discriminate_raw_run_manifest_version(raw: bytes) -> None:" src/deepreason/run_manifest.py && grep -q "^    api_key_env: str | None = None$" src/deepreason/run_manifest.py && sh -c '! grep -qE "^    api_key: " src/deepreason/run_manifest.py' && grep -q "if parsed.username is not None or parsed.password is not None:" src/deepreason/run_manifest.py && grep -q "if parsed.query or parsed.fragment:" src/deepreason/run_manifest.py && grep -q "route URL must not contain credentials" src/deepreason/run_manifest.py && sh -c '! grep -qE "^(from|import) deepreason\.(harness|adjudication|ontology|scheduler|rules|informal)[. ]" src/deepreason/run_manifest.py'`

Manifest schemas, their validators, and anything entering a qualification
subject digest are a **frozen surface** — see `DR-INV-frozen-surfaces` before
scoping any change here.

## Seams

| Side | Status | What the agreement is (one line) |
|---|---|---|
| `DR-SEAM-bridge-x-manifest` | documented | the manifest promises the bridge one immutable, already-validated authority document (whether `grounded_two_stage` mode is in effect) |
| `DR-SEAM-llm-x-manifest` | documented | the manifest promises one thing permanently: a closed set of exact provider routes, one `Route` per role seat, secret-free |
| `DR-SEAM-manifest-x-schools` | documented | a school promises the manifest one thing — an identifier of the form `school-<n>` — and nothing else: no stance, no weight, no lineage |
| manifest x rules | **deliberately absent** | this document's own check proves it: the exclusion list (`harness\|adjudication\|ontology\|scheduler\|rules\|informal`) names `rules` explicitly — the manifest imports nothing from it |
| manifest x scheduler | **deliberately absent** | same check, same exclusion list — matches `DR-SUB-scheduler`'s own claim that `RunManifest` is injected, never imported |
| harness x manifest | **deliberately absent** | same check again — `manifest` is process metadata the harness never reaches for directly |
| authority x manifest | undocumented | real: `run_manifest.py` is jointly `Owns:`-listed by `DR-CON-authority` — `CriticismPolicyV1.authority` is the frozen manifest vocabulary half of that concept |
| manifest x scratch | undocumented | real: `DR-SEAM-rules-x-scratch`'s own "How to change it" names `ScratchPolicy`/`attention_policy()` as manifest surfaces — any change to pack size, channels or roles moves the qualification subject digest |
| manifest x run-identity | undocumented | plausible, unconfirmed here: the qualification cache keys on a subject digest derived from the manifest, and a run root binds one manifest for its life — `DR-CON-run-identity`'s territory, worth a real check before writing the doc |
| manifest x workflow | undocumented | plausible, unconfirmed here: v6 dispatch guards and `control_plane_policy` are read widely by transactional workflow code, but the exact import direction is not verified in this document |
| manifest x verification | undocumented | not evidenced here either way — candidate pair, not yet analyzed |
| manifest x packs-and-token-economy | undocumented | not evidenced here either way — candidate pair, not yet analyzed |
| capabilities x manifest | undocumented | not evidenced here either way — candidate pair, not yet analyzed (matches `DR-SUB-capabilities`'s own Seams table, same verdict from its side) |

## Entry points

Compilation, binding, reconstruction (`run_manifest.py`):

- `compile_run_manifest(config, ...)` — resolve `auto`/`auto-alt`, select
  output mechanisms, derive every typed policy and per-seat plan, return a
  frozen `RunManifest`.
- `bind_run_manifest(manifest, root)` (alias `persist_run_manifest`) —
  first-writer binding of one manifest to one run root under a process lock;
  later callers are idempotent only on byte-identical canonical bytes.
- `write_run_manifest(manifest, path)` — the looser export used by
  `config compile`; overwrites, unlike binding.
- `load_run_manifest(path, verify_hash=True)` — bounded symlink-free read,
  raw version discrimination, model validation, then every recognised digest
  sidecar is checked (not just the first that matches).
- `config_from_run_manifest(manifest)` / `materialize_run_config(manifest, root)`
  — rebuild `Config` with routes injected solely from `roles` and v3 policy
  injected solely from the typed policies.
- `role_matrix(manifest)` / `render_role_matrix(manifest)` — the inspection and
  dry-run projection.
- `preflight_payload(manifest, payload)` / `preflight_harness(manifest, harness, config)`
  — refuse workload/policy conflicts (rubric input, text status authority drift,
  a rubric-reaching property path) before any endpoint exists.
- `resolve_route_seat_base_profile(manifest, *, role, seat, endpoint_id)` /
  `resolve_route_seat_behavioral_capability(..., route_sha256)` /
  `resolve_route_seat_contract_decomposition(..., route_sha256, source_contract_id)`
  — the only route from an exact seat identity to a frozen grant; within a plan,
  absence of a grant is never implicit permission. **The seat identity is not
  uniform across the three.** The presentation resolver keys on
  `(role, seat, endpoint_id)` only — it never sees `route_sha256`, so route
  bytes cannot move a base profile — and when the manifest carries no
  presentation plan at all it falls back to the global `manifest.model_profile`
  rather than refusing. The behavioural and decomposition resolvers both bind
  `route_sha256`, and both refuse outright when their plan is absent.
`check: for s in compile_run_manifest bind_run_manifest persist_run_manifest load_run_manifest write_run_manifest config_from_run_manifest materialize_run_config role_matrix render_role_matrix preflight_payload preflight_harness resolve_route_seat_base_profile resolve_route_seat_behavioral_capability resolve_route_seat_contract_decomposition; do grep -q "^def $s(" src/deepreason/run_manifest.py || exit 1; done && python -c "import inspect, deepreason.run_manifest as m; sig = lambda f: list(inspect.signature(f).parameters); assert sig(m.resolve_route_seat_base_profile) == [\"manifest\", \"role\", \"seat\", \"endpoint_id\"], sig(m.resolve_route_seat_base_profile); assert sig(m.resolve_route_seat_behavioral_capability) == [\"manifest\", \"role\", \"seat\", \"endpoint_id\", \"route_sha256\"], sig(m.resolve_route_seat_behavioral_capability); assert sig(m.resolve_route_seat_contract_decomposition) == [\"manifest\", \"role\", \"seat\", \"endpoint_id\", \"route_sha256\", \"source_contract_id\"], sig(m.resolve_route_seat_contract_decomposition)" && grep -q "return manifest.model_profile" src/deepreason/run_manifest.py`

Qualification evidence (`qualification.py`):

- `qualification_subject_digest(manifest, profile)` — the cache key. **Frozen.**
- `resolve_completed_qualification(manifest, profile, cache_dir=..., executor=None)`
  — load completed evidence, or execute only through an explicitly injected
  executor. With no executor a missing bundle becomes a typed refusal:
  `QUALIFICATION_TIER_SHALLOW` / `_UNQUALIFIED` when a tier record exists,
  otherwise `QUALIFICATION_NOT_CONFIGURED`. It never silently degrades.
- `project_qualification_report(bundle, manifest, profile)` — bind cached
  sanitized cases back onto one exact manifest and re-validate.
- `resolve_qualification_tier(cache_dir, subject_digest)` — `full` /
  `shallow` / `unqualified`, failing closed on a damaged cache.
- `production_qualification_maximum_provider_calls(manifest)` — the worst-case
  call count announced before the battery is dispatched.
- `default_qualification_executor` / `qualification_executor_options(...)` — the
  live executor and its scoped concurrency/progress options.

The battery (`cli/doctor.py`):

- `production_contract_pairs(manifest)` — project the exact pair inventory from
  the frozen behavioural plan.
- `run_production_contract_doctor(manifest, case_executor=None, ...)` — execute
  the whole battery; `run_production_contract_doctor_cli` wraps it for
  `deepreason doctor`.
- `exercise_production_contract_case(manifest, pair, case_index)` — one live
  case through the v6 patch-repair protocol; the seam a scripted executor
  replaces.
- `validate_production_contract_qualification(report, manifest)` — the gate: v6,
  exact manifest sha, exact pair inventory, every pair qualified, repair counts
  within grant, classification reproduced.
- `derive_route_seat_model_classification(manifest, pairs=..., summary=...)` —
  per-seat `qualified_exact_behavior` / `unqualified_exact_behavior` /
  `inactive_no_authorized_contract`.
- `write_production_contract_report` / `load_production_contract_report` —
  canonical atomic write and strict bounded read.
`check: for s in qualification_subject_payload qualification_subject_digest resolve_completed_qualification resolve_qualification_tier project_qualification_report completed_bundle_from_report production_qualification_maximum_provider_calls default_qualification_executor qualification_executor_options shallow_tier_record_from_cases load_completed_qualification write_completed_qualification write_qualification_tier; do grep -q "^def $s(" src/deepreason/qualification.py || exit 1; done && for s in production_contract_pairs run_production_contract_doctor run_production_contract_doctor_cli validate_production_contract_qualification derive_route_seat_model_classification exercise_production_contract_case write_production_contract_report load_production_contract_report; do grep -q "^def $s(" src/deepreason/cli/doctor.py || exit 1; done`

## State it owns

In the run root: `run-manifest.json` (canonical bytes) and the fixed-name
`run-manifest.sha256` digest sidecar written by `bind_run_manifest`; the
suffix-name `run-manifest.json.sha256` that `write_run_manifest` produces is
never written by binding but IS validated by both bind and load. Also
`.run-manifest.lock`, which serialises bind across processes, and
`.run-manifest-config.json` from `materialize_run_config`. Every write goes
through `_atomic_write`, which fsyncs the file and its directory entry so a
reported successful bind survives a host crash.

In the qualification cache directory, keyed by subject digest:
`<digest>.json` (the completed `ReusableQualificationBundleV1`),
`<digest>.tier.json` (the durable `shallow`/`unqualified` conclusion), and
`<digest>.unqualified-doctor.json` (the sanitized failing report, preserved so
diagnosing a failed battery never costs a second battery). This subsystem does
not choose where that directory lives — the surfaces do
(`provider_state_dir() / "qualification-cache"`).
`check: grep -q 'MANIFEST_NAME = "run-manifest.json"' src/deepreason/run_manifest.py && grep -q 'MANIFEST_HASH_NAME = "run-manifest.sha256"' src/deepreason/run_manifest.py && test "$(grep -c 'target.with_suffix(target.suffix + ".sha256")' src/deepreason/run_manifest.py)" = 4 && grep -q "^def _atomic_write(target: Path, payload: bytes) -> None:" src/deepreason/run_manifest.py && grep -q "os.fsync(directory_fd)" src/deepreason/run_manifest.py && grep -q '".run-manifest-config.json"' src/deepreason/run_manifest.py && grep -q 'RUN_MANIFEST_LOCK_NAME = ".run-manifest.lock"' src/deepreason/locking.py && grep -q 'f"{subject_digest}.json"' src/deepreason/qualification.py && grep -q 'f"{subject_digest}.tier.json"' src/deepreason/qualification.py && grep -q '".unqualified-doctor.json"' src/deepreason/qualification.py && sh -c '! grep -q "qualification-cache" src/deepreason/qualification.py' && grep -q "qualification-cache" src/deepreason/cli/main.py`

No provider content is ever persisted: a case result carries booleans, counts
and an uppercase sanitized `failure_code`, never a prompt, response, base URL or
credential. The only mutable in-memory state is `_EXECUTOR_OPTIONS` in
`qualification.py`, scoped by a context manager so the executor stays a pure
`RunManifest -> report` function.

## Where to change what

| To change... | Edit | Test |
|---|---|---|
| Add a manifest field or bump the schema version | `RunManifest` **and** `_versioned_serialization` **and** `canonical_bytes` **and** `_production_routes_are_concrete`, `run_manifest.py` — **frozen surface** | `python -m pytest tests/test_run_manifest.py tests/test_v6_only_manifest_loading.py -q` |
| What one route may carry (capacity, output mechanism, credential reference) | `Route` and its field validators, `run_manifest.py` | `python -m pytest "tests/test_run_manifest.py::test_context_window_tokens_are_frozen_and_round_trip" -q` |
| Which roles exist or are routable | `LEGACY_CANONICAL_ROLES` / `V3_CANONICAL_ROLES` — extending the legacy tuple in place would change historical canonical bytes | `python -m pytest tests/test_run_manifest.py -q -k role` |
| School or foreign-criticism topology | `SchoolExecutionPolicyV1`, `CriticismPolicyV1`, `_validate_v4_control_plane_policy`, `_validate_v4_criticism_policy` — see `DR-CON-schools` | `python -m pytest tests/test_school_execution_binding_v4.py tests/test_foreign_criticism_policy_c3.py -q` |
| A seat's presentation profile | `RouteSeatPresentationPlanV1`, `_compile_route_seat_presentation_plan`, `resolve_route_seat_base_profile` | `python -m pytest tests/test_v6_route_seat_presentation_plan.py -q` |
| Which contracts a seat may speak, and its repair budget | `RouteSeatBehavioralCapabilityPlanV1`, `_compile_route_seat_behavioral_capability_plan`, `ContractSchemaRepairGrantV1` | `python -m pytest tests/test_v6_route_seat_behavioral_capability_plan.py -q` |
| The atomic-fallback edges after `schema_exhausted` | `RouteSeatContractDecompositionPlanV1`, `_compile_route_seat_contract_decomposition_plan` | `python -m pytest tests/test_v6_route_seat_behavioral_capability_plan.py -q` |
| What is refused before the first provider call | `preflight_payload`, `preflight_harness`, `_preflight_text_authority` | `python -m pytest "tests/test_run_manifest.py::test_property_proposal_rubric_path_fails_before_any_model_call" -q` |
| What one contract's qualification case actually sends | `_production_probe_contract` and the `_production_*_probe` helpers, `cli/doctor.py` | `python -m pytest tests/test_cli_production_doctor_v6.py -q` |
| The release gate or the re-exercise allowance | `PRODUCTION_CASES_PER_PAIR`, `PRODUCTION_EVENTUAL_VALID_MINIMUM`, `PRODUCTION_PAIR_RE_EXERCISE_LIMIT`, `_release_gate` | `python -m pytest "tests/test_cli_production_doctor_v6.py::test_report_computes_19_of_20_gate_and_all_metrics" -q` |
| What a cache hit means (the reusable subject) | `qualification_subject_payload` — **frozen surface**, every cached verdict is keyed by it | `python -m pytest tests/test_reusable_qualification.py -q` |
| The shallow tier ladder or its battery size | `SHALLOW_FITNESS_*`, `QualificationTierRecordV1`, `shallow_tier_record_from_cases` | `python -m pytest tests/test_qualification_tier.py -q` |
| Where the qualification cache lives | not here — `_cmd_qualify` in `cli/main.py`, `readiness.py`, `preparation.py`, `webapp.py` | `python -m pytest tests/test_qualification_tier.py -q -k readiness` |
`check: for s in _compile_route_seat_behavioral_capability_plan _compile_route_seat_contract_decomposition_plan _compile_route_seat_presentation_plan _validate_v4_control_plane_policy _validate_v4_criticism_policy _preflight_text_authority; do grep -q "^def $s(" src/deepreason/run_manifest.py || exit 1; done && grep -q "^LEGACY_CANONICAL_ROLES = (" src/deepreason/run_manifest.py && grep -q "^V3_CANONICAL_ROLES = (\*LEGACY_CANONICAL_ROLES, \"grounding_reviewer\")" src/deepreason/run_manifest.py && for s in _production_probe_contract _production_bridge_ledger_probe _production_bridge_composition_probe _production_grounding_probe _production_scratch_probe _release_gate _validate_production_contract_request_envelopes; do grep -q "^def $s(" src/deepreason/cli/doctor.py || exit 1; done && grep -q "^PRODUCTION_CASES_PER_PAIR = 20$" src/deepreason/cli/doctor.py && grep -q "^PRODUCTION_EVENTUAL_VALID_MINIMUM = 19$" src/deepreason/cli/doctor.py && grep -q "^PRODUCTION_PAIR_RE_EXERCISE_LIMIT = 3$" src/deepreason/cli/doctor.py && grep -q "^SHALLOW_FITNESS_CASES = 6$" src/deepreason/qualification.py && grep -q "^SHALLOW_FITNESS_EVENTUAL_VALID_MINIMUM = 5$" src/deepreason/qualification.py && grep -q "class QualificationTierRecordV1" src/deepreason/qualification.py`

## Traps

- **The version gating is written twice.** `_versioned_serialization` (public
  `model_dump`) and `canonical_bytes` (hashed bytes) each pop the same
  version-absent fields. Editing one and not the other makes a manifest whose
  dump and whose digest disagree about which fields exist — and the digest is
  what binding, qualification and replay compare.
`check: test "$(grep -c 'payload.pop("terminal_commitment_policy", None)' src/deepreason/run_manifest.py)" = 2 && test "$(grep -c 'payload.pop("route_seat_presentation_plan", None)' src/deepreason/run_manifest.py)" = 2`
- **Reading the model and not the validator.** Pydantic admits values the
  module-level `_validate_v*` functions refuse, so a field's `Literal` is not
  the admissibility rule. `DR-INV-frozen-surfaces` records the tranche this
  actually cost; read it before scoping any change to a policy model. A live
  example of exactly this trap: `ContractVersionPolicyV3.conjecturer_turn_
  contract`'s `Literal` admitted `"conjecturer.turn.v7"` (D2 rev 2 dual-mode,
  additive to v6) from the day it was added, but
  `_compile_contract_schema_repair_policy` hardcoded the repair-grant key to
  the literal `"conjecturer.turn.v6"`, so any v7-configured manifest was
  refused at `V6_BEHAVIORAL_REPAIR_GRANT_REQUIRED` before a run could start —
  parked as P-CEPP-1, fixed in
  `experiments/2026-08-09-change-fix-p-cepp-1-dual-mode-wiring/`. The grant
  key and the conjecture-family scratch-authority checks
  (`CONJECTURER_TURN_CONTRACTS`) now read the manifest's own configured
  value instead of re-hardcoding it a second time.
`check: grep -q "^CONJECTURER_TURN_CONTRACTS = frozenset(" src/deepreason/run_manifest.py && python -m pytest "tests/test_v6_contract_schema_repair_policy.py::test_v7_manifest_gets_an_equivalent_repair_grant_and_scratch_authority" -q`
- **`roles` is a `_FrozenDict`, not a dict.** Mutating it raises `TypeError`
  rather than silently producing a manifest whose bytes no longer describe its
  routes. `budget_policy`, `stop_policy` and `memory_policy` are frozen the same
  way.
`check: grep -q 'raise TypeError("RunManifest roles are immutable")' src/deepreason/run_manifest.py && grep -q "class _FrozenDict(dict)" src/deepreason/run_manifest.py`
- **Completed evidence is write-once; a tier record is not.** The bundle lands
  via `os.link`, so a second differing bundle for one subject raises
  `QUALIFICATION_CACHE_CONFLICT`; the tier record lands via `os.replace`,
  because an explicit `deepreason qualify` rerun may lawfully move a subject
  between `shallow` and `unqualified`. Do not "fix" the asymmetry.
`check: grep -q "os.link(temporary, path, follow_symlinks=False)" src/deepreason/qualification.py && grep -q "QUALIFICATION_CACHE_CONFLICT" src/deepreason/qualification.py && grep -q "os.replace(temporary, path)" src/deepreason/qualification.py`
- **The subject digest excludes exactly two things: `compiled_at` and
  `run_input_digest`.** Everything else about the manifest and the provider
  profile is in it, so changing completion tokens, an output mechanism or a
  contract version is a cache MISS and costs the whole battery (~14 min,
  ~1160 calls). That is by design; budget for it rather than widening the
  subject.
`check: grep -q "^def qualification_subject_payload(" src/deepreason/qualification.py && grep -q 'behavior.pop("compiled_at", None)' src/deepreason/qualification.py && grep -q 'behavior.pop("run_input_digest", None)' src/deepreason/qualification.py && python -m pytest "tests/test_reusable_qualification.py::test_subject_digest_is_invariant_only_to_question_and_compile_time" "tests/test_reusable_qualification.py::test_subject_digest_mutates_for_every_provider_behavior_field" -q`
- **The pair inventory comes from the behavioural plan, not from `roles`.**
  `production_contract_pairs` walks
  `route_seat_behavioral_capability_plan.entries` and expands each seat's
  granted contracts; a seat with no plan entry is never probed, and a manifest
  without the plan refuses qualification with
  `DOCTOR_BEHAVIORAL_CAPABILITY_PLAN_REQUIRED`. Adding a route does not add a
  qualification pair.
`check: python -m pytest "tests/test_cli_production_doctor_v6.py::test_doctor_pairs_are_exact_projection_of_behavioral_plan" "tests/test_cli_production_doctor_v6.py::test_disabled_optional_families_are_omitted_instead_of_probed" -q`
- **`pair_id` carries the manifest digest; the reusable pair subject does not.**
  `_pair_id` hashes `manifest_sha256`, so pair ids differ across manifests,
  while `_pair_payload` excludes `pair_id` precisely so cached cases can be
  re-projected onto a different manifest with the same behaviour. Adding a
  manifest-dependent field to the pair payload would silently make every cache
  entry unreusable.
`check: grep -q '"manifest_sha256": manifest_sha256' src/deepreason/cli/doctor.py && grep -q 'return pair.model_dump(mode="json", exclude={"pair_id"})' src/deepreason/qualification.py`
- **A tier drop is how a wire-contract defect reaches you.** The live battery is
  the only path where a real provider response — a JSON *document*, not a Python
  object a test constructed — meets a production contract. In the
  `live_jolt_2026-07-31` epoch boundary, `scratch.block.compact.v1` fell from
  20/20 to 2/20, the subject was durably tiered `shallow`, and `reason` was
  refused at preparation with `QUALIFICATION_TIER_SHALLOW` — the cause was a
  contract field, not the qualification code. Read the tier record and the
  preserved `<digest>.unqualified-doctor.json` before touching this subsystem.
`check: grep -q "QUALIFICATION_TIER_SHALLOW" src/deepreason/qualification.py && python -m pytest "tests/test_qualification_tier.py::test_full_reason_refuses_shallow_tier_with_typed_error" -q`
- **An orphaned sidecar still claims the root.** `bind_run_manifest` treats a
  surviving `*.sha256` as a binding record even when `run-manifest.json` is
  gone, so deleting the manifest does not free a root for different bytes. A
  bound root is retired by renaming it, never by editing it — see
  `DR-CON-run-identity`.
`check: python -m pytest "tests/test_run_manifest.py::test_run_root_binding_honors_orphaned_digest_record" "tests/test_run_manifest.py::test_run_root_binding_is_idempotent_and_never_overwrites_conflict" -q`
- **Doctor concurrency changes wall clock, never the report.** Blocks are
  assembled in canonical case order regardless of completion order, and a
  supplied (scripted) executor defaults to one worker because it may be
  order-sensitive. A report that differs by worker count is a defect, not
  provider noise.
`check: python -m pytest "tests/test_cli_production_doctor_v6.py::test_battery_parallelism_changes_wall_clock_never_the_report" -q`
