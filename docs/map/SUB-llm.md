<!-- DR-SUB-llm -->
Verified-at: 9e80ceab0
Verify: python -m pytest tests/test_llm.py tests/test_model_firewall.py tests/test_wire_contracts.py tests/test_llm_repair_capabilities.py tests/test_adapter_attempt_logging.py tests/test_compact_profiles.py tests/test_providers.py tests/test_budget.py -q
Owns: src/deepreason/llm/
Seams: DR-SEAM-llm-x-workflow, DR-SEAM-llm-x-manifest, DR-SEAM-llm-x-rules, DR-SEAM-bridge-x-llm, DR-SEAM-llm-x-scheduler, DR-SEAM-llm-x-verification
Seams-undocumented: capabilities x llm, harness x llm, llm x model-profiles, llm x ontology, llm x schools, llm x scratch

# The LLM boundary — one bounded `pack -> schema-valid JSON` function on a frozen route

## What it is

`llm/` is the only place in the engine where a provider is spoken to, and its
job is to make that conversation *bounded* in every direction at once. A caller
hands it a role name, a rendered pack and a canonical output model; it resolves
the seat, renders the exact prompt, enforces the route's context envelope and
the run's token ceiling, dispatches, validates the answer against a closed
schema, runs a finite repair protocol on failure, and returns a typed
`LLMCall` alongside the compiled value. Everything the model says is treated as
untrusted transport: it may fill fields in a contract, and it may not choose a
route, name a tool, delegate, or set a status — a firewall rejects those field
names before any validator sees them. The package decides nothing epistemic; it
constructs no status, computes no label, and writes no log, so the dependency
arrow points strictly outward and a transport bug cannot become an adjudication
bug. That asymmetry is enforced structurally: `llm/` never imports the harness,
the scheduler, the rules or the adjudicator, and `LLMCall` is minted in exactly
one function.
`check: ! grep -rqE "^[[:space:]]*(from|import) +deepreason\.(harness|scheduler|rules|adjudication|capture|informal|verification|amendment)\b" src/deepreason/llm/ --include=*.py && ! grep -rqE "append_event|log\.jsonl" src/deepreason/llm/ && test "$(grep -rl "LLMCall(" src/deepreason --include=*.py | grep -v "src/deepreason/ontology/" | tr "\n" " ")" = "src/deepreason/llm/adapter.py " && python -c "import ast, pathlib; t = ast.parse(pathlib.Path('src/deepreason/llm/adapter.py').read_text()); c = [n for n in ast.walk(t) if isinstance(n, ast.FunctionDef) and n.name == 'call'][0]; m = [n.lineno for n in ast.walk(t) if isinstance(n, ast.Call) and getattr(n.func, 'id', '') == 'LLMCall']; assert m and all(c.lineno <= l <= c.end_lineno for l in m), (m, c.lineno, c.end_lineno)" && ! grep -rn "\.complete(" src/deepreason --include=*.py | grep -v "^src/deepreason/llm/" | grep -qv "^src/deepreason/cli/doctor.py:"`

## Seams

| Side | Status | What the agreement is (one line) |
|---|---|---|
| `DR-SEAM-llm-x-workflow` | documented | `workflow/` decides by what recorded authority a provider may be spoken to; `llm/` is the only place that speaks to one |
| `DR-SEAM-llm-x-manifest` | documented | the manifest promises one thing permanently: a closed set of exact provider routes, one `Route` per role seat, secret-free |
| `DR-SEAM-llm-x-rules` | documented | a rule decides what to ask and what the answer means; `llm/` decides how it is asked and refuses anything the answer may not contain |
| `DR-SEAM-bridge-x-llm` | documented | `llm/` sells one bounded `pack -> schema-valid JSON` call on a frozen route and knows nothing about grounding; `bridge/` buys exactly that |
| llm x ontology | undocumented | real: `LLMCall` is minted in exactly one function (`adapter.call`) but the class itself is DEFINED in `ontology/event.py` — this package's central record type is ontology's, not its own |
| llm x schools | undocumented | real, richly evidenced from the schools side (`DR-CON-schools`'s Where-it-lives table): `llm/firewall.py::resolve_school_role_lease`, `llm/adapter.py::school_judge_bindings`, `llm/packs.py::render_conj_pack` all carry school routing/conditioning |
| llm x scratch | undocumented | real, already partly documented from the scratch side (`DR-SEAM-rules-x-scratch`'s site table): `llm/packs.py::render_conj_pack(scratch_context=...)` and `llm/wire.py`'s `SCR_` alias namespace |
| llm x verification | **deliberately absent** | this document's own check proves it: `llm/` never imports `verification` (the exclusion list in the "What it is" check names it explicitly, alongside harness/scheduler/rules/adjudication/capture/informal/amendment) |
| llm x scheduler | **deliberately absent** | same check, same exclusion list — `llm/` never imports `scheduler` |
| harness x llm | **deliberately absent** | same check; also independently confirmed from `DR-SUB-harness`'s own Seams table (`harness x llm` there too) |
| capabilities x llm | undocumented | not evidenced here either way — candidate pair, not yet analyzed (consistent with `DR-SUB-capabilities`'s own Seams table, which marks this pair the same way from its side) |

Pack construction and the cost model are documented separately in
DR-CON-packs-and-token-economy; school-to-seat routing in DR-CON-schools; the
surfaces here that may not move in DR-INV-frozen-surfaces. `reference_menu.py`
is this package's newest module and has its own invariant document,
DR-INV-reference-menu: it owns the single answer to "what may this
reference-bearing field contain", which both `packs.py` (the prompt menu) and
`repair.py` (the diagnostic's legal list) consume rather than each deriving.

`check: grep -q "^def legal_handles_for(" src/deepreason/llm/reference_menu.py && grep -q "reference_menu" src/deepreason/llm/packs.py && grep -q "reference_menu" src/deepreason/llm/repair.py && python -m pytest tests/test_reference_menu.py -q`

## Entry points

- `build_adapter(config, blob_store, meter=..., run_manifest=..., process_events=...)`
  — build the role table from a `RunManifest` (preferred) or the §15 config
  role table. A v6 manifest makes the adapter refuse untransactional dispatch.
- `LLMAdapter.call(role, pack, output_model, ...)` — the single provider
  boundary. Returns `(compiled canonical model, LLMCall)`; raises typed
  failures (`SchemaRepairError`, `EndpointError`, `RouteFirewallError`,
  `TokenBudgetExceeded`, `RequestEnvelopeExceeded`, `WorkflowAuthorizationError`),
  each carrying `.spend` so prior tokens still reach the record.
- `LLMAdapter.preview_request(...)` — render byte-for-byte what `call` would
  send, without dispatching. Transactional callers bind the prompt digest and
  completion ceiling from this before `WORK_ISSUED`; both paths render through
  the same private `_render_request`, so preview and dispatch cannot drift.
- `LLMAdapter.bind_v6_authority(harness, manifest)` — attach canonical v6
  replay authority. Afterwards profiles, wire contracts and route liveness are
  read from the manifest and workflow state, not from adapter-local settings.
- `LLMAdapter.require_cross_family_judges()` / `judge_seats()` — the normative
  rubric-ensemble gate, and the ungated seat count for code downstream of it.
- `LLMAdapter.profile_for` / `base_profile_for` / `rehydrate_compact_recovery`
  — effective vs frozen presentation for a seat, and the durable-evidence
  restore of compact transport after a legacy run crashed mid-recovery.
- `wire_contract_for(role, output_model, profile, aliases, expected_target=...)`
  — pick the transport for a role at a profile; `WireContract.validate_value`
  and `.compile` are the closed-schema check and the wire→canonical compiler.
- `render_role_prompt(role, schema=..., pack=..., profile=..., example=..., aliases=...)`
  — assemble the final provider request from `TEMPLATES` / `COMPACT_TEMPLATES`.
- `render_conj_pack`, `render_crit_pack`, `render_batch_crit_pack`,
  `render_experiment_pack`, `render_property_pack`, `render_cx_retry_pack`
  — the model-facing bodies (see DR-CON-packs-and-token-economy).
- `BoundedRepairSession` / `V6PatchRepairSession` — the finite repair state
  machines. No I/O, no route, no budget authority; a caller asks for the next
  turn, sends it, and reports the outcome.
- `TokenMeter.reserve(...)` → `Reservation.settle|release` — the hard
  provider-wide ceiling, booked before dispatch and shrunk to reported usage.
- `plan_split(...)` → `SplitPlan`, `deliberation_request`, `extraction_request`
  — the split-budget seat protocol: one seat call becomes a deliberation leg at
  `B_r` and a lower-reasoning emission leg at `B_a`, against the same route,
  lease and authorization, with `B_r + B_a == ceiling`. Pure: it plans and
  renders, and `LLMAdapter._dispatch_split` spends and records both legs as
  `LLMSplitLegV1` on the attempt they produce. The value the emission leg sends
  is READ from the model's own document (`profile`, a required keyword with no
  default) and is never a literal in `llm/`; a model nobody has described
  stands the protocol down. See `DR-CON-model-profiles`.
- `reject_model_control_fields` / `sanitize_model_control_fields_for_repair` /
  `route_fingerprint` / `select_lease` / `resolve_school_role_lease` — the
  route-and-authority firewall.
- `probe_capabilities` + `select_profile`, and `build_embedder` — setup-time
  measurement of a route, and the non-generator embedding role.
`check: grep -q "^class LLMAdapter:" src/deepreason/llm/adapter.py && grep -q "^def build_adapter(" src/deepreason/llm/adapter.py && for s in call preview_request bind_v6_authority profile_for base_profile_for rehydrate_compact_recovery require_cross_family_judges judge_seats has_role ensemble_size is_single_model _render_request; do grep -q "^    def $s(" src/deepreason/llm/adapter.py || exit 1; done && grep -q "^class EndpointLease:" src/deepreason/llm/firewall.py && for s in reject_model_control_fields sanitize_model_control_fields_for_repair route_fingerprint leases_from_manifest leases_from_endpoints select_lease resolve_school_role_lease require_cross_family_judge_ensemble require_cross_school_judge_ensemble is_single_family_run is_single_model_run route_from_endpoint; do grep -q "^def $s(" src/deepreason/llm/firewall.py || exit 1; done`
`check: for s in wire_contract_for minimal_example; do grep -q "^def $s(" src/deepreason/llm/wire.py || exit 1; done && grep -q "^class WireContract(" src/deepreason/llm/wire.py && grep -q "^class AliasTable:" src/deepreason/llm/wire.py && grep -q "^def render_role_prompt(" src/deepreason/llm/roles.py && for s in render_conj_pack render_crit_pack render_batch_crit_pack render_experiment_pack render_property_pack render_cx_retry_pack apply_model_profile aliases_for_pack; do grep -q "^def $s(" src/deepreason/llm/packs.py || exit 1; done && for s in select_output_mechanism parse_one_json_value diagnostic_from_error diagnostic_envelope_from_error apply_repair_patch minimal_skeleton; do grep -q "^def $s(" src/deepreason/llm/repair.py || exit 1; done && for c in BoundedRepairSession V6PatchRepairSession OutputMechanism; do grep -q "^class $c" src/deepreason/llm/repair.py || exit 1; done && for s in get_profile select_profile apply_profile_to_config clip_pack; do grep -q "^def $s(" src/deepreason/llm/profiles.py || exit 1; done && grep -q "^class TokenMeter:" src/deepreason/llm/budget.py && grep -q "^class Reservation:" src/deepreason/llm/budget.py && grep -q "^def conservative_prompt_bound(" src/deepreason/llm/budget.py && for s in request_with_retries resolve_model list_models mean_surprisal; do grep -q "^def $s(" src/deepreason/llm/endpoints.py || exit 1; done && grep -q "^class OpenAICompatEndpoint:" src/deepreason/llm/endpoints.py && grep -q "^class MockEndpoint:" src/deepreason/llm/endpoints.py && for s in reasoning_body infer_provider reasoning_knob_available; do grep -q "^def $s(" src/deepreason/llm/providers.py || exit 1; done && python -c "import ast,pathlib,sys; tree=ast.parse(pathlib.Path('src/deepreason/llm/providers.py').read_text()); names={n.id for n in ast.walk(tree) if isinstance(n,ast.Name)} | {n.name for n in ast.walk(tree) if isinstance(n,ast.FunctionDef)}; sys.exit(1 if ('REASONING_OFF' in names or 'reasoning_disabled' in names) else 0)" && grep -q "^def probe_capabilities(" src/deepreason/llm/capabilities.py && grep -q "^class CapabilityCache:" src/deepreason/llm/capabilities.py && grep -q "^def build_embedder(" src/deepreason/llm/embedder.py && grep -q "^def generate_specs(" src/deepreason/llm/specs.py`

`ROLES` is the §9 generator roster (8 entries, `embedder` among them and
deliberately template-less). `TEMPLATES` is larger, because `template_role`
lets an auxiliary contract — batch critic, config referee, experimenter,
property designer, spec generator, the scratch and bridge authors, thesis —
reuse a configured seat under a different prompt. Compact mode adds three
website directives that have no standard-profile template at all.
`check: python -c "from deepreason.llm.roles import ROLES, TEMPLATES, COMPACT_TEMPLATES; assert len(ROLES) == 8 and 'embedder' in ROLES and 'embedder' not in TEMPLATES; assert len(TEMPLATES) > len(ROLES); assert sorted(set(COMPACT_TEMPLATES) - set(TEMPLATES)) == ['website_art_direction', 'website_component_contract', 'website_outline']"`

## State it owns

**On disk: one file, and only from the setup path.** `CapabilityCache.put`
writes a secret-free JSON map keyed by `(provider, endpoint, model, revision,
probe_version)` at a path the caller chooses. Nothing else in the package
opens, creates or writes a file. Prompt, raw and diagnostic bytes are handed to
an *injected* blob store — twelve `blobs.put` sites in `LLMAdapter.call`, six on
the undivided path and six more for the split-budget protocol: each leg's own
prompt and raw, the deliberation trace, and the empty trace an over-envelope
emission leg names in its place. The trace is blobbed ONCE and both legs name
that ref, which is what makes their agreement checkable rather than a claim
(DR-SEAM-llm-x-verification, limb L4). The `objects/` directory belongs to
DR-SUB-harness.

**In memory, per adapter:** `_compact_recovery_roles` (roles armed for compact
transport on their next ordinary call), `_v6_authority_harness` /
`_v6_authority_manifest` (the transactional binding), and the frozen `leases`
map. Per meter: `prompt_tokens`, `completion_tokens`, `calls` and the
outstanding `reserved` bound, all under one lock. Per endpoint object:
`last_usage`, `last_finish_reason`, `last_mean_surprisal`,
`last_transport_attempts`, `last_transport_diagnostics` — read once, right
after `complete()`, to build the attempt trace. There is also a module-level
`_MODEL_CACHE` in `endpoints.py` memoizing `/models` per `(base_url, api_key)`
for the `auto` / `auto-alt` sentinels; it is process-global, not per-run.
`check: grep -q "self.path.write_text" src/deepreason/llm/capabilities.py && test "$(grep -rlE "write_text|write_bytes|\.mkdir\(" src/deepreason/llm/ --include=*.py)" = "src/deepreason/llm/capabilities.py" && grep -q "^_MODEL_CACHE: dict\[tuple\[str, str | None\]" src/deepreason/llm/endpoints.py && grep -q "self._compact_recovery_roles: set\[str\] = set()" src/deepreason/llm/adapter.py && test "$(grep -c "self.blobs.put" src/deepreason/llm/adapter.py)" -eq 12`

**Typed records it constructs** (shapes owned by DR-SUB-ontology): `LLMCall`,
one per completed or abandoned call; `LLMAttempt`, one per provider request
including transport failures, carrying `contract_id`, `endpoint_id`,
`route_sha256`, `seat`, `model_profile` (frozen/base) vs `transport_profile`
(effective), `repair_scope`, `validation_path`, `diagnostic_ref`, the
controller's effective `max_tokens`/`timeout_s`, and the transport diagnostics;
`LLMSplitLegV1`, two per split seat call, hanging off the ONE attempt they
jointly produced and NEVER an entry in `attempt_trace` — that list is the
repair ladder, and putting legs in it made every thinking-ON run replay-invalid
(`experiments/2026-08-27-defect-split-leg-recording/`);
`SchoolRouteReceiptV1` and `ConjectureContextCallReceiptV1` when the call is
school-routed or carries advisory context. Every one of these reaches the log
through the caller, including on the failure paths.
`check: python -m pytest tests/test_adapter_attempt_logging.py tests/test_review_fixes.py::test_every_llm_call_reaches_the_log tests/test_review_fixes.py::test_retry_exhausted_spend_reaches_the_log -q`

## Where to change what

| To change... | Edit | Test |
|---|---|---|
| Add a provider, or how its reasoning knob is SPELLED on the wire | `llm/providers.py`: `REASONING_ADAPTERS`, `infer_provider`, `reasoning_knob_available` | `tests/test_providers.py::test_knob_availability_is_a_provider_fact_and_stays_here` |
| What a reasoning value MEANS on one model — whether it disables thinking, where the trace lands, what the emission leg should send | that model's own document at `$DEEPREASON_HOME/model-profiles/<id>/agent.md`. **NO source edit** — see `DR-CON-model-profiles` | `tests/test_providers.py::test_what_off_means_is_a_model_fact_and_lives_in_the_model_document`, `tests/test_model_profile_registry.py` |
| Point a role at a different model/endpoint | the role table (config §15 or `RunManifest.roles`); `_endpoint_from_spec` needs no edit | `tests/test_providers.py::test_role_table_is_the_model_change_plug` |
| A role's prompt wording, or add an auxiliary `template_role` | `llm/roles.py`: `TEMPLATES`, `COMPACT_TEMPLATES` | `tests/test_compact_profiles.py::test_compact_prompt_has_one_example_and_no_operator_context` |
| What a role's JSON must contain | the canonical model in `llm/contracts.py` + its wire model and branch in `wire_contract_for` | `tests/test_wire_contracts.py::test_role_wire_contracts_compile_to_existing_canonical_models` |
| Move a rule from prompt prose into the schema | `llm/wire.py` primitives: `present_and_nonempty`, `absent_or_empty`, `outcome_shape_schema`, `discriminated_shape_schema`, `restrict_discriminator_values`, `prune_property` | `tests/test_schema_carries_every_prose_rule.py` |
| Which transport a role gets at a given profile | `wire_contract_for`; `ProfileSpec.direct_contracts` in `llm/profiles.py` | `tests/test_compact_profiles.py::test_alias_dependent_hot_roles_fail_closed_without_a_table` |
| Whether a seat splits its completion budget, or the budgets it splits into | `llm/split.py`: `plan_split`, `MIN_EXTRACT_TOKENS`; `Config.SPLIT_BUDGET_SEAT_PROTOCOL` / `SPLIT_BUDGET_EXTRACTION_TOKENS`; and whether the seat's model has a document at all | `tests/test_split_budget_protocol.py::test_neither_leg_nor_their_sum_exceeds_the_route_lease_ceiling` |
| What a split leg records, or when the protocol stands down | `LLMAdapter._split_plan` / `_dispatch_split`; `LLMSplitLegV1` in `ontology/event.py`; the `NOTICE_` constants in `llm/split.py` | `tests/test_split_budget_protocol.py::test_a_provider_that_cannot_disable_thinking_still_compiles`, `tests/test_split_leg_recording.py::test_a_split_call_records_two_legs_on_one_attempt` |
| Anything a split call writes into the RECORD | `LLMSplitLegV1` and the `split-legs` family that reads it — see DR-SEAM-llm-x-verification BEFORE either side | `tests/test_split_leg_recording.py::test_verify_root_accepts_a_thinking_on_record` |
| Repair protocol shape or attempt ceiling | `BoundedRepairSession` (legacy, `retry_max` capped at 2) or `V6PatchRepairSession` (one authorization per attempt) | `tests/test_llm_repair_capabilities.py::test_repair_exhaustion_is_bounded_even_with_large_retry_max` |
| Which output mechanism a route uses | `select_output_mechanism` at setup; `OpenAICompatEndpoint.build_body` for the wire form | `tests/test_llm_repair_capabilities.py::test_output_mechanism_priority_is_fixed`, `::test_runtime_cannot_change_frozen_lease_mechanism` |
| What model output may never name | `FORBIDDEN_MODEL_CONTROL_FIELDS` / `_OPAQUE_DATA_FIELDS` in `llm/firewall.py` | `tests/test_model_firewall.py` |
| The judge-ensemble independence rule | `LLMAdapter._select_judge_ensemble`, `require_cross_family_judge_ensemble`, `require_cross_school_judge_ensemble` | `tests/test_judge_ensemble_boundary.py`, `tests/test_prose_refutation_boundaries.py::test_the_cross_school_gate_governs_only_a_single_family_run` |
| Transport retry / timeout policy | `_BACKOFFS`, `TIMEOUT_FACTORS`, `DEFAULT_TIMEOUT_S`, `request_with_retries` in `llm/endpoints.py` | `tests/test_llm.py` |
| What a transport failure SAYS about itself | `EndpointError.__init__`'s `http_status` / `condition` in `llm/endpoints.py`; the two branches in `cli/doctor.py::_failure_code` that read them. The bound ABOVE the per-call ladder is not here — see DR-SUB-manifest | `tests/test_llm.py::test_failure_code_distinguishes_a_credential_from_a_quota_refusal`, `::test_the_provider_status_is_never_exposed_as_a_numeric_code_attribute` |
| The hard provider ceiling or its bound | `TokenMeter.reserve`, `conservative_prompt_bound` (see DR-CON-packs-and-token-economy) | `tests/test_budget.py::test_budget_smaller_than_any_bound_blocks_the_first_dispatch` |
| How a school resolves to a seat | `resolve_school_role_lease` (see DR-CON-schools) | `tests/test_school_execution_binding_v4.py` |
| v6 transactional dispatch preconditions | `bind_v6_authority`, `_require_transactional_route_dispatchable`, `_transactional_profile_for` | `tests/test_adapter_workflow_authorization_c2.py`, `tests/test_v6_insufficient_capability_terminal.py` |
| Which capabilities are probed, or the profile they select | `deterministic_probe_cases` + `probe_capabilities`; `select_profile` in `llm/profiles.py` | `tests/test_llm_repair_capabilities.py::test_capability_probes_are_deterministic_and_cached_by_revision`, `tests/test_compact_profiles.py::test_capable_route_selects_frontier_and_unknown_length_selects_standard` |
| The embedding backend or its drift stamp | `build_embedder`, `HashingEmbedder.fingerprint`, `NeuralEmbedder` | `tests/test_embedder.py` |
| Whether the configured backend can be BUILT at all | `pyproject.toml`'s core dependency list (fastembed), `deepreason embedder-warmup` | `tests/test_embedder.py::test_fastembed_is_a_core_dependency` |

`check: python -m pytest tests/test_providers.py tests/test_compact_profiles.py tests/test_wire_contracts.py tests/test_schema_carries_every_prose_rule.py tests/test_llm_repair_capabilities.py tests/test_model_firewall.py tests/test_llm.py tests/test_budget.py tests/test_judge_ensemble_boundary.py tests/test_school_execution_binding_v4.py tests/test_adapter_workflow_authorization_c2.py tests/test_v6_insufficient_capability_terminal.py tests/test_embedder.py -q`

## Traps

- **`EndpointError` must never expose its status as `.code`.**
  `cli/doctor.py::_failure_code` reads `.code` FIRST and returns it as the
  case's `failure_code`, which is constrained to `^[A-Z][A-Z0-9_]*$`. A
  numeric `.code` therefore normalises to the string `"429"`, fails that
  pattern, and — because `qualification.py:830-836` flattens ANY executor
  exception into `QUALIFICATION_EXECUTION_FAILED` — takes the whole battery
  down with the cause erased. That is parked finding **C5** pointed at its own
  fix. Found while fixing P7-A (tranche
  `experiments/2026-08-29-defect-qualification-circuit-breaker/`); the status
  therefore rides `http_status`, and a regression test pins that `.code` stays
  absent.

`check: python -c "
from deepreason.cli.doctor import _failure_code
from deepreason.llm.endpoints import EndpointError
refusal = EndpointError('HTTP 401: Unauthorized', http_status=401, condition='http_refusal')
quota = EndpointError('transport failed after retries', http_status=429)
assert not hasattr(refusal, 'code'), 'a numeric .code normalises to the schema-invalid 401 (parked C5)'
assert _failure_code(refusal) == 'ENDPOINT_HTTP_401', _failure_code(refusal)
assert _failure_code(quota) == 'ENDPOINT_HTTP_429', _failure_code(quota)
assert _failure_code(EndpointError('x')) == 'ENDPOINT_TRANSPORT'
assert _failure_code(refusal) != _failure_code(quota), 'the two conditions must not collapse'
"`

- **A repair grant is spent by the provider CALL, so a spelling the harness
  cannot read costs the same as a wrong answer.** In reach-rich
  `run-40e713b30a147dfc` the conjecturer seat exhausted
  `conjecturer.turn.v6` at 4/4 grants and killed the run at cycle 2 — while
  holding a correct final patch. All 13 repair turns patched a pointer inside
  their own dispatched authorized set (there were NO off-target patches), but
  six responses died at the wire: the patch wrapped under `patch` / `patches` /
  `operations`, the envelope's own `contract` / `baseline_sha256` echoed back
  beside it, or the pointer field spelled `pointer`. `tolerant_patch_value` now
  takes the dispatched envelope and absorbs exactly what costs no information —
  a container that could never be a valid patch, bytes the harness itself sent
  (exact equality only), and a synonym for an absent field. It still refuses
  `old`/`new` in place of `value`, which would mean inventing the value, and it
  does not widen `authorized_pointers`: an off-target patch is still a
  `RepairScopeViolation` in the record.
  **Diagnostic trap in the same run:** a repair attempt's own `diagnostic_ref`
  is written by `repair_transaction._terminalize_invalid` as
  `trace_ref or next_diagnostic_ref` — the diagnostic derived AFTER the
  response. Scoring a response against it compares attempt N to attempt N+1's
  authority and makes every converging repair look off-target, which is how the
  first reading of this run recorded two "sibling-index" patches that never
  happened. The dispatched authority is the work preparation's
  `repair.semantic-task.v1` payload.
`check: python -m pytest tests/test_v6_patch_repair_and_wire.py::test_recorded_epoch1_patch_spellings_are_tolerated tests/test_v6_patch_repair_and_wire.py::test_recorded_epoch1_substantive_patch_loss_is_still_rejected tests/test_v6_patch_repair_and_wire.py::test_off_target_patch_remains_a_typed_scope_violation -q && grep -q "def tolerant_patch_value(value, envelope=None)" src/deepreason/llm/repair.py`
- **A repair loop can have no legal exit, and the recorded reason will hide
  it.** In turmite `run-bc3e8797b3e0609eddb324299c8257bd` a scratch link's
  `to_ref` had no satisfiable value: every candidate was either a self-link or
  an undeclared key, and each diagnostic named only the violation of the state
  the document was currently in, so patching the reported fault landed the
  model in the other one. The seat exhausted its smallest authorized contract
  and the run died at cycle 0 — with the exhaustion reason showing whichever
  validation error happened to come last. `_note_repeated_state` now RECORDS
  the cycle in the exhaustion reason and deliberately does not cut the attempts
  short (a repeated state is evidence of non-convergence, not proof of it).
  When a run dies at cycle 0, the `attempt_trace` gives `validation_path` and
  `diagnostic_ref` and the blob under `blobs/` gives the verbatim error and the
  rejected value; read that before theorising about JSON Schema expressiveness.
`check: grep -q "def _note_repeated_state" src/deepreason/llm/repair.py && grep -q "diagnostic_ref=self.blobs.put" src/deepreason/llm/adapter.py && python -m pytest tests/test_v6_patch_repair_and_wire.py::test_a_repair_that_cycles_is_named_in_the_exhaustion_reason -q`
- **Unset reasoning is not off — and neither is `"none"`, on every model.**
  Two failures, four years of runs apart in cost, and the second one is why the
  first one's fix had to move.
  **The original (2026-08).** In coin canonicity `run-c5f901f3` the live
  profile carried `reasoning=None`, which sends no reasoning field at all;
  glm-5.2 then thought by default, the first conjecture turn returned
  `completion_tokens` exactly equal to the 24576 cap, and no candidate was
  emitted. That claim still holds and is still asserted.
  **What was wrong with the fix, and when (2026-09-01).** The fix was
  `reasoning_disabled(value)`, comparing against `REASONING_OFF = "none"` — one
  answer for every model. On glm-5.3 it is FALSE: `reasoning_effort: "none"`
  does not stop the thinking there, it stops the SEPARATION, so the trace lands
  in `message.content` ahead of the answer (0/8 clean at `none` against 8/8 at
  `low`, and `none` is also the dearer of the two at 64 median completion
  tokens against 7). `llm/split.py` sent that constant on every emission leg of
  every model, and it killed three runs: P-S1 `MISTAKES.md` M-1 (the 512-token
  emission leg at cycle 0) and M-16 (the cap ratchet's 1,953-token floor at
  cycle 11), then P-A1 run `4565139800f5ca02` re-running M-1's mechanism
  verbatim. A launch refusal in `cli/main.py` made it worse by DEMANDING
  `reasoning: none` before it would spend a call.
  **FIXED 2026-09-01** by `DR-CON-model-profiles`: the constant and the
  predicate are gone, what a value means on a model is that model's own
  document to say, and the refusal became a disclosure. `reasoning_knob_available`
  stays here and stays a provider fact — a provider whose adapter is the no-op
  cannot carry any reasoning field at all.
  The DeepSeek effort table is the sibling hazard, unchanged: an earlier
  version collapsed `low`/`medium` up to `high`, silently billing
  maximum-cost reasoning for the cheapest configured setting.
`check: python -m pytest tests/test_providers.py::test_knob_availability_is_a_provider_fact_and_stays_here tests/test_providers.py::test_what_off_means_is_a_model_fact_and_lives_in_the_model_document tests/test_review_fixes.py::test_deepseek_low_effort_stays_cheap -q`
- **A per-model fact answered by a per-provider table is invisible until it
  kills something.** The shape, so the next one is caught earlier: the claim
  reads as vocabulary ("`none` means off"), it is stated once in a constant,
  every model inherits it, and it is right about most of them. `llm/providers.py`
  is the PROVIDER seam — what the wire carries — and it must never acquire a
  model id, a model table, or a claim about what a value does.
`check: python -c "
import ast, pathlib
tree = ast.parse(pathlib.Path('src/deepreason/llm/providers.py').read_text())
names = {n.id for n in ast.walk(tree) if isinstance(n, ast.Name)}
assert 'REASONING_OFF' not in names, 'the per-model constant is back'
assert 'REASONING_ADAPTERS' in names, 'positive anchor: the provider table is still here'
funcs = {n.name for n in ast.walk(tree) if isinstance(n, ast.FunctionDef)}
assert 'reasoning_disabled' not in funcs
assert {'reasoning_body', 'reasoning_knob_available', 'infer_provider'} <= funcs, funcs
"`
- **The configuration VALUE and the wire FIELD share the word "reasoning", and
  reading one as the other reported a working launch config as broken.** On
  2026-09-04 a four-model probe recorded Ollama Cloud refusing
  `{"reasoning": "none"}` with HTTP 400 -- `json: cannot unmarshal string into
  Go struct field ChatCompletionRequest.reasoning of type openai.Reasoning` --
  and the finding was parked as "the newest committed launch config binds
  exactly that value on its critic seat"
  (`experiments/2026-09-04-experiment-blind-critic/PARKED.md` P2). It binds the
  VALUE. `_ollama_reasoning` spells that value as `reasoning_effort`, so the
  refused field appears in no request the harness has ever built. The launch
  config's own run had already made 99 provider attempts with zero faults the
  day before, and a 45-call probe the day after accepted 42 of 42
  harness-built bodies across six models and the whole neutral vocabulary,
  refusing only the hand-built control
  (`experiments/2026-09-04-fix-provider-reasoning-contract/PROBE.json`).
  NOT A CODE DEFECT -- no `src/` line changed. What it cost was a tranche, and
  what it left behind is the pin: no adapter may put a STRING directly under
  `reasoning`, because that is the one shape the provider rejects before
  generating anything. An OBJECT under `reasoning` is accepted, so the rule is
  about the string and not about the key.
  **The shape, so the next one is caught earlier:** a provider seam names
  fields, a run config names values, and when a value and a field are spelled
  the same the record cannot tell you which one a report meant. Build the
  request and look at its keys -- `build_body` is callable offline and takes
  one line -- before believing any claim about what the harness sends.
`check: python -m pytest tests/test_provider_reasoning_wire_contract.py -q`
- **Retrying an identical REQUEST fails identically, and the lesson was learned
  for only one of the two branches.** First half, fixed 2026-08: two variator
  calls were dropped live after four 120s waits while ~110s generations were
  succeeding at the same endpoint. `TIMEOUT_FACTORS = (1, 2)` makes the retry
  wait twice as long and makes a second read timeout terminal, bounding total
  wait at 3x rather than opening a ladder. Separately, `IncompleteRead` is an
  `http.client.HTTPException`, not an `OSError`: it escaped the retryable net
  and killed two runs at cycle 1, so the exception tuple names it explicitly.

  Second half, and the reason this entry is rewritten rather than added to:
  that reasoning was encoded in `_timed_out()` for `TimeoutError` ONLY, so a
  `RemoteDisconnected` — the strictly worse case, where zero bytes arrived and
  the wall is on the far side — kept the unbounded identical ladder. Ten of
  glm-5.3's 25 calls in run `4565139800f5ca02` therefore cost ~1215 s each and
  returned nothing: four byte-identical resends against a wall, 3.27 h of a
  4.94 h run. Run `9e48a36b1dec91ee` is the same shape with a different kind,
  54 faults on one seat.

  Fixed 2026-09-03 by MEASURING the wall rather than inferring it (17 calls,
  `experiments/2026-09-02-defect-provider-transport-faults/REPRO.md`): four
  non-streaming calls closed at 300.510 / 300.268 / 300.210 / 300.289 s with
  zero bytes, across glm-5.3 AND deepseek-v4-pro:0813 — a 0.3-second range is a
  timer on the path, not a model's fault. The same cap streamed completed at
  369.6 s and at 756.5 s. So a `zero_byte_close` now bounds at
  `ZERO_BYTE_WALL_MAX_ATTEMPTS = 2` and the retry is the SAME request on a
  framing that survives.

  Three things about that fix are easy to get wrong and two were got wrong once
  here. FIRST, the retry may NOT shrink `max_tokens`: `invariants.py` requires
  every recorded `attempt.max_tokens` to be the route's or one a PRIOR logged
  controller policy authorized, and `llm/` may not write to the log, so a cap
  chosen at this layer could never be authorized and every such run would fail
  replay validation — a cap change arms the NEXT call, exactly as compact
  recovery does. SECOND, a streamed attempt may NOT record
  `transport_profile: "streaming"`: that field is pinned to the manifest's
  profile or `"compact"`, and a third value fails `attempt-profile-authority`.
  Streaming therefore records nothing at all, which is the property that makes
  it a transport change rather than an evidence change. THIRD, a streamed body
  reports NO usage unless `stream_options.include_usage` is sent, and an
  unreported spend defeats the hard ceiling — the fix asks for it, and no chunk
  carries `logprobs` at all, so a call that asked for logprobs stays
  non-streaming.
`check: grep -q "^TIMEOUT_FACTORS = (1, 2)$" src/deepreason/llm/endpoints.py && grep -q "http.client.HTTPException" src/deepreason/llm/endpoints.py && grep -q "^ZERO_BYTE_WALL_MAX_ATTEMPTS = 2$" src/deepreason/llm/transport_policy.py && grep -q "include_usage" src/deepreason/llm/endpoints.py && ! grep -q "transport_profile" src/deepreason/llm/transport_policy.py && python -c "
import ast, inspect, pathlib
from deepreason.llm import endpoints
# Over the AST, not the text: this module's own docstring says why it may not
# name max_tokens, and a substring check would read that as the violation.
tree = ast.parse(pathlib.Path('src/deepreason/llm/transport_policy.py').read_text())
names = {n.id for n in ast.walk(tree) if isinstance(n, ast.Name)}
names |= {n.attr for n in ast.walk(tree) if isinstance(n, ast.Attribute)}
names |= {k.value for k in ast.walk(tree) if isinstance(k, ast.Constant) and isinstance(k.value, str) and k.value.count(chr(10)) == 0}
assert 'max_tokens' not in names, 'the retry policy must never choose a cap'
src = inspect.getsource(endpoints.OpenAICompatEndpoint.complete)
assert 'request_logprobs' in src and 'stream_options' in src
" && python -m pytest tests/test_llm.py::test_second_read_timeout_is_terminal_and_bounded tests/test_llm.py::test_retry_covers_mid_stream_disconnects tests/test_provider_transport_faults.py -q`
- **A truthy usage block does not mean the missing side is zero.** Providers
  routinely report only `total_tokens`, or only one side. Treating the object's
  truthiness as "usage known" under-counted spend — found in-band by the
  accounting check as an 833-token delta on the first outing. `_usage_tokens`
  keeps every reported side verbatim, estimates only the missing one, and
  splits a total-only report proportionally while preserving the provider
  total. Under-counting here is not cosmetic: it defeats the hard ceiling.
`check: python -m pytest tests/test_review_fixes.py::test_partial_usage_dict_counts_tokens tests/test_review_fixes.py::test_partial_usage_dict_trips_budget tests/test_review_fixes.py::test_one_sided_usage_estimates_peer_and_reconciles_log -q`
- **One stray `[` cost a route seat its whole contract.** A fully qualified
  model wrapped an otherwise valid atomic candidate in a single-element JSON
  array; the resulting object-wide extra-field error had no finite repair and
  terminally exhausted the seat's smallest contract. `WireContract.validate_value`
  now strips exactly that one unambiguous wrapper, like a narrated code fence.
  Multiple elements and nested wrappers still fail. The same tolerance must be
  mirrored in whichever repair session applies patches, or a patch the session
  accepts gets re-rejected at admission.
`check: grep -q "if isinstance(value, list) and len(value) == 1 and isinstance(value\[0\], dict):" src/deepreason/llm/wire.py && python -m pytest tests/test_scratch_contracts.py::test_single_element_array_wrapper_is_tolerated_like_a_fence -q`
- **Counting judge seats must not assert the guarantee, and an empty lease set
  guarantees nothing.** `require_cross_family_judges` used to be the only way
  to learn the seat count, so a path whose independence guarantee came from
  elsewhere could not ask how many seats it had without also asserting one it
  did not use; `judge_seats()` is the ungated reader, and carries no
  `require_cross` call. On the other side, `is_single_family_run` /
  `is_single_model_run` are the preconditions that unlock the cross-SCHOOL
  substitute for cross-FAMILY independence, so they must fail closed on zero
  leases — no family is not one family — and cross-family governs whenever more
  than one family is present, regardless of configuration.
`check: sed -n "/    def judge_seats(/,/    def _select_judge_ensemble(/p" src/deepreason/llm/adapter.py | grep -qF "self.leases.get(" && ! sed -n "/    def judge_seats(/,/    def _select_judge_ensemble(/p" src/deepreason/llm/adapter.py | grep -q "require_cross" && python -m pytest tests/test_prose_refutation_boundaries.py::test_the_single_family_predicate_fails_closed_on_no_leases tests/test_prose_refutation_boundaries.py::test_the_single_model_predicate_fails_closed_on_no_leases tests/test_prose_refutation_boundaries.py::test_the_cross_school_gate_governs_only_a_single_family_run -q`
- **Compact recovery arms the NEXT call and can never be armed by the model.**
  Switching transport inside a failing call would make one `LLMCall` describe
  two presentations; `_mark_compact_recovery` therefore only sets a flag after
  the call has already raised, and the frozen `model_profile` in the attempt
  trace stays the manifest's while `transport_profile` shows the effective
  wire. `rehydrate_compact_recovery` restores that flag across a crash from
  harness-authored fields only — never prompt bytes, raw bytes or error prose —
  and drops evidence whose route fingerprint or endpoint identity does not
  match this adapter's leases. A compact run stays compact; recovery has no
  reverse gear.
`check: python -m pytest tests/test_adapter_attempt_logging.py::test_direct_exhaustion_arms_only_the_next_ordinary_call_for_compact tests/test_adapter_attempt_logging.py::test_model_output_cannot_rehydrate_compact_recovery tests/test_adapter_attempt_logging.py::test_foreign_route_drop_cannot_rehydrate_compact_recovery tests/test_adapter_attempt_logging.py::test_compact_profile_never_changes_after_exhaustion -q`
- **`minimal_skeleton` cannot see cross-field rules.** It reads `properties`
  and `required`, ignores `allOf`, and takes the first enum value — so on any
  contract carrying a conditional shape it happily builds an example document
  that the contract itself rejects. A contract whose rules it cannot see must
  supply `minimal_example_document`; the `conjecturer.turn.v4/v5/v6/v7` family
  (P-CEPP-1 added v7, additive to v6, same exemption) is the older hardcoded
  form of the same exemption. Adding a shape clause to a contract without
  adding one of those two escapes ships a prompt whose worked example is
  invalid.
`check: grep -q "minimal_example_document" src/deepreason/llm/wire.py && ! grep -q "allOf" src/deepreason/llm/repair.py && grep -q "conjecturer.turn.v4" src/deepreason/llm/wire.py && grep -q "^CONJECTURER_TURN_CONTRACT_V7 = " src/deepreason/llm/wire.py`
- **`ConjecturerTurnWireContractV6.contract_id` is a constructor parameter,
  not a fixed literal.** P-CEPP-1: the class's own name is now the SAME wire
  schema for both `conjecturer.turn.v6` and `conjecturer.turn.v7` (D2 rev 2
  dual-mode is additive — no new fields on this class), distinguished only by
  which `contract_id` the caller (`rules/conj.py`, from the manifest's own
  configured `conjecturer_turn_contract`) passes at construction. The
  frozen-authority check at `llm/adapter.py`'s `_render_request` v6 branch
  (`resolve_route_seat_behavioral_capability`, `DR-SEAM-llm-x-manifest`)
  refuses a wire contract whose `contract_id` disagrees with the seat's
  frozen grants — this is what caught the gap before the fix (a v7-authorized
  seat handed a hardcoded v6-labeled wire contract), not a new guard added
  for it.
`check: grep -q "contract_id: str = CONJECTURER_TURN_CONTRACT_V6" src/deepreason/llm/wire.py && grep -q "contract_id=configured_turn_contract" src/deepreason/rules/conj.py`
- **`_document_excerpt` is dead code.** The labeled head/tail excerpt existed
  because prefix-only clipping made compact critics refute valid compiled
  designs for "ending abruptly"; the critic target is now a mandatory section
  and the helper has no callers anywhere in `src/`. Why it was built, and why
  it stays, is recorded in full under DR-CON-packs-and-token-economy — do not
  re-derive that here.
`check: test "$(grep -rc "_document_excerpt" src/deepreason --include=*.py | grep -v ":0$")" = "src/deepreason/llm/packs.py:1"`
- **A default that names a backend the install does not carry degrades every
  run, typed and unread.** `config.EMBEDDER_MODEL` has defaulted to
  `nomic-ai/nomic-embed-text-v1.5` since E0.1, while `fastembed` sat in the
  optional `[embed]` extra — so every container preflight running the
  documented plain `pip install -e .` produced runs where `NeuralEmbedder`
  raised `EmbedderUnavailable`, `EMBEDDER_FAILURE_POLICY="fallback"` swapped
  in `HashingEmbedder`, and the substitution was recorded as an
  `embedder-fallback` Measure nobody read. The grounded-extension run
  (`experiments/2026-08-12-live-grounded-extension-expansion/run/log.jsonl`)
  carries both halves at seq 2 and seq 8, and again at 9969/10045/10092 for
  its continuation epoch: a run that configured neural geometry and measured
  with `hashing-128` for 24 cycles. FIXED 2026-08-16 — fastembed moved into
  the core dependency list, `deepreason embedder-warmup` pays the ~523 MB
  weight fetch in the setup phase where it is visible, and `deepreason
  results` prints the fallback rather than leaving it on the log. The general
  lesson: a default naming an OPTIONAL backend is a default that silently
  isn't, and the typed degradation record only helps a reader who is looking
  at it — arm the default by install, and surface the fallback where the
  operator already looks.
`check: python -c "import tomllib,pathlib; d=tomllib.loads(pathlib.Path('pyproject.toml').read_text()); core=[r for r in d['project']['dependencies'] if r.split('[')[0].split('>')[0].split('<')[0].split('=')[0].strip()=='fastembed']; assert core, ('fastembed must stay in the CORE dependency list', d['project']['dependencies']); assert d['project']['optional-dependencies'].get('embed') == [], 'the [embed] extra must stay declared and empty'" && grep -q "\"embedder-warmup\"" src/deepreason/cli/main.py && python -m pytest tests/test_embedder.py::test_fastembed_is_a_core_dependency -q`
- **A leased field the controller is licensed to tune was also frozen for
  equality, and the two rules sat six lines apart in the same function.**
  `EndpointLease.verify`'s comment said `max_tokens` was "intentionally absent"
  from the frozen checks because the deterministic controller may tune it; the
  conditional below it added `max_tokens` back whenever the route declared
  `context_window_tokens`. Reach-rich epoch 2 (run `40e713b3…`) declared it,
  the controller settled the conjecturer seat from 32768 to 20480, and the run
  died at cycle 2 of 24 with `ROUTE_LEASE_MISMATCH` /
  `stop_reason=operational_failure`. FIXED 2026-08-22
  (`experiments/2026-08-22-fix-route-lease-maxtokens/`): a qualified route now
  binds `max_tokens` as a CEILING — at or below the lease is admitted, above it
  is still refused — and the comment was corrected in the same commit. The
  general lesson outlives the field: when a comment and a check in one function
  disagree, a live run will eventually pick the reading you did not test. Full
  agreement is written up at `DR-SEAM-llm-x-scheduler`.
`check: python -m pytest tests/test_route_lease_maxtokens_tuning.py::test_controller_settling_a_qualified_seat_does_not_terminate_the_run tests/test_route_lease_maxtokens_tuning.py::test_a_cap_above_the_qualified_lease_is_still_refused tests/test_v6_request_envelope.py::test_runtime_endpoint_cannot_widen_frozen_capacity -q`