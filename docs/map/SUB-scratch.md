<!-- DR-SUB-scratch -->
Verified-at: 08dcdf3c
Verify: python -m pytest tests/test_scratch_replay.py tests/test_scratch_attention.py tests/test_scratch_render.py tests/test_scratch_contracts.py tests/test_scratch_provenance_refs.py -q
Owns: src/deepreason/scratch/
Seams: DR-SEAM-application-x-scratch, DR-SEAM-bridge-x-scratch, DR-SEAM-harness-x-scratch, DR-SEAM-llm-x-scratch, DR-SEAM-manifest-x-scratch, DR-SEAM-ontology-x-scratch, DR-SEAM-packs-and-token-economy-x-scratch, DR-SEAM-periphery-x-scratch, DR-SEAM-rules-x-scratch, DR-SEAM-scheduler-x-scratch, DR-SEAM-schools-x-scratch, DR-SEAM-scratch-x-verification, DR-SEAM-scratch-x-workflow

# The scratchpad — the imaginative workshop, advisory and non-grounding

## What it is

`scratch/` is the only place in DeepReason where the model may be wrong on
purpose. Speculative mechanisms, counterfactuals, half-finished fragments,
outright contradictions and unresolved questions are all admissible here,
because nothing stored here carries a warrant, a status, an attack edge, or
support for one. The package's whole job is therefore RETRIEVAL under a budget:
keep an immutable, replayable graph of notes, links, clusters and guides; choose
deterministically which small subset a model sees next; render it behind opaque
local handles; and admit whatever the model writes back without ever letting it
become evidence. It reaches into no epistemic machinery — the dependency arrow
points only at the harness, the ontology, the manifest, the workflow ledger and
the LLM plumbing, and never at the rules, the scheduler, or adjudication.
`check: ! grep -rqE "deepreason\.(adjudication|rules|scheduler|measures|informal)" --include=*.py src/deepreason/scratch/`

The boundary is a typed declaration, not a comment: the authoring policy carries
`purpose="imaginative_workshop"` and `epistemic_boundary="advisory_non_grounding"`
as frozen manifest literals, alongside the finite per-turn allowances and the
byte ceiling that bound what one turn may add. This separation is the operator's
requirement — the scratchpad authority chain and the conjecture/criticism
adjudication chain must not exist together.
`check: grep -q 'SCRATCH_EPISTEMIC_BOUNDARY = "advisory_non_grounding"' src/deepreason/scratch/proposals.py && grep -q 'epistemic_boundary: Literal\["advisory_non_grounding"\]' src/deepreason/run_manifest.py && grep -q "    def attention_policy(" src/deepreason/run_manifest.py && for f in maximum_new_blocks_per_turn maximum_total_bytes; do grep -q "$f: int" src/deepreason/run_manifest.py || exit 1; done && python -m pytest tests/test_prose_refutation_boundaries.py -q -k scratch`

## Entry points

- `service.ScratchService` — the one deterministic API shared by the scheduler,
  the workflow, the CLI, the MCP bridge and tests. Constructed from a live
  `Harness`, or from a path plus `upto_seq` for a physically read-only historical
  view. It owns no database or cache of its own.
- `ScratchService.create_block`, `revise_block`, `create_link`, `retire_link`,
  `store_guide`, `record_attention_receipt` — the mutations. Each persists its
  immutable output first, then appends exactly one typed scratch event.
- `ScratchService.prepare_advisory_context` / `commit_prepared_advisory_context`
  — split so planning stays pure: preparation writes nothing, and the receipt,
  its derived visibility and any coverage progress are appended only immediately
  before the model call.
- `ScratchService.cluster_map`, `search_phrase`, `dormant_blocks`,
  `underexposed_blocks`, `unlinked_blocks` — the read side the retrieval
  channels are built from.
- `attention.AttentionPlanner.plan` — deterministic multi-channel selection
  (focus, linked, clustered, keyword, semantic, recent, exploratory,
  underexposed, coverage) under `AttentionPolicyV1`, producing an
  `AttentionPackV1` and its `AttentionReceiptV1`; `_candidates`,
  `_apply_channel_limits` and `_final_order` are where the ordering lives.
  `commit_render` is the durable half.
- `render.ScratchRenderer.render_attention_pack` / `render_advisory_context` —
  turn records into bounded model-facing text carrying only opaque handles
  (`B1`, `C3`, `L2`, `G1`); `persist_receipt` is the sole writing method.
- `render.ScratchRenderReceiptV1.resolve` / `alias_map` / `ordered_refs` — the
  handle→hash direction. `ordered_refs` is the only correct way to compare a
  receipt against a selection's order.
`check: for s in create_block revise_block create_link retire_link store_guide record_attention_receipt prepare_advisory_context commit_prepared_advisory_context cluster_map search_phrase dormant_blocks underexposed_blocks unlinked_blocks; do grep -q "    def $s(" src/deepreason/scratch/service.py || exit 1; done; for s in plan commit_render _candidates _apply_channel_limits _final_order; do grep -q "    def $s(" src/deepreason/scratch/attention.py || exit 1; done; for s in render_attention_pack render_advisory_context persist_receipt resolve alias_map ordered_refs; do grep -q "    def $s(" src/deepreason/scratch/render.py || exit 1; done`

- `authoring.ScratchAuthoringService.validate_proposal` / `admit_proposal` — the
  v6 path: check one whole `ScratchProposalV1` against the manifest's ceilings
  and byte budget and resolve its entire local reference graph BEFORE the first
  event, then admit it restart-safely (a matching durable prefix is consumed,
  only the missing suffix appended).
- `authoring.ScratchAuthoringService.author_block` / `author_link` /
  `author_cluster_guide` / `admit_transactional_effect` — the per-record seats,
  and the transactional-effect admission the workflow lifecycle drives.
- `proposals.ScratchProposalV1` — the wire-independent draft container the model
  fills in (`new_blocks`, `revisions`, `links`, `unresolved_questions`,
  `cluster_suggestions`), with no IDs, provenance, snapshots or status.
- `conjecture.plan_conjecture_context`, `prepare_conjecture_context_call`,
  `commit_conjecture_context`, `validate_conjecture_context_call`,
  `plan_conjecture_context_expansion`, `render_v6_conjecture_context` — the
  Conj-facing lifecycle: plan purely at a fence, prepare, commit just in time,
  re-validate on replay. `ConjectureContextStale` is raised when the log advanced
  under a prepared plan.
- `state.rebuild_scratch_state` and `ScratchState.apply` — replay. The harness
  calls `apply` for every event carrying a scratch payload;
  `_expected_output_schemas` is the per-action output contract.
- `events.ScratchEventPayloadV1` — the only admissible scratch event body, with a
  closed `ScratchAction` enum and a per-action input-arity contract.
- `coverage.CoverageController.coverage_due` / `record_receipt` —
  anti-starvation: every live block eventually gets a rendered slot, advanced
  only by a durable receipt.
- `similarity.select_embedder` / `ScratchSimilarityService` — one retrieval
  signal, recorded as a receipt so replay never re-embeds.
`check: for s in validate_proposal admit_proposal author_block author_link author_cluster_guide admit_transactional_effect; do grep -q "    def $s(" src/deepreason/scratch/authoring.py || exit 1; done; grep -q "^class ScratchProposalV1" src/deepreason/scratch/proposals.py; for s in plan_conjecture_context prepare_conjecture_context_call commit_conjecture_context validate_conjecture_context_call plan_conjecture_context_expansion render_v6_conjecture_context; do grep -q "^def $s(" src/deepreason/scratch/conjecture.py || exit 1; done; grep -q "^def rebuild_scratch_state(" src/deepreason/scratch/state.py && grep -q "    def _expected_output_schemas(" src/deepreason/scratch/state.py && grep -q "^class ScratchEventPayloadV1" src/deepreason/scratch/events.py; for s in coverage_due record_receipt; do grep -q "    def $s(" src/deepreason/scratch/coverage.py || exit 1; done; grep -q "^def select_embedder(" src/deepreason/scratch/similarity.py`

## State it owns

Nothing on disk of its own. No module under `scratch/` opens a path — every
durable record goes into the harness object store under a `scratch-*` schema,
and every mutation is one `Rule.SCRATCH` event in the same append-only log as the
formal graph.
`check: test "$(grep -rlE 'path\.open|write_text|write_bytes|[^_a-z]open\(' --include=*.py src/deepreason/scratch | wc -l)" -eq 0 && for s in scratch-block scratch-link scratch-cluster scratch-membership scratch-cluster-snapshot scratch-guide scratch-similarity scratch-attention-receipt scratch-visibility scratch-coverage-cycle scratch-advisory-context; do grep -q "\"$s\":" src/deepreason/storage/objects.py || exit 1; done`

The in-memory materialization is `ScratchState`, held by the harness as
`harness.scratch_state` and rebuilt by replay: blocks and their revision
children, links plus derived `link_status`, clusters, memberships, snapshots,
guides by cluster and by snapshot, similarity hits, attention receipts, advisory
contexts, visibility records, coverage progress. `record_scratch_event` is the
single narrow persistence seam, and `Rule.SCRATCH` may appear only together with
a typed payload. It is replayed BESIDE the formal state, never inside it, so a
scratch event cannot move a status; two replays of one root must produce equal
`scratch_state`, and `verify_root` additionally pins each conjecture-context
receipt to the render receipt and scratch fence it names (`DR-SUB-verification`).
`check: grep -q "self.scratch_state = ScratchState()" src/deepreason/harness.py && grep -q "self.scratch_state.apply(event, self.objects)" src/deepreason/harness.py && grep -q "    def record_scratch_event(" src/deepreason/harness.py && grep -q 'if (self.rule == Rule.SCRATCH) != (self.scratch is not None):' src/deepreason/ontology/event.py && grep -q 'fail("scratch-replay"' src/deepreason/invariants.py && grep -q "selection receipt names another scratch fence" src/deepreason/invariants.py`

## Where to change what

| To change... | Edit | Test |
|---|---|---|
| What a note may carry (fields, bounds, provenance refs) | `ScratchBlockBodyV1` in `scratch/models.py` AND `ScratchBlockDraftBodyV1` in `scratch/proposals.py` — both, or the schema and the validator diverge | `tests/test_scratch_provenance_refs.py::test_every_rule_the_validator_enforces_is_visible_in_the_schema` |
| Which blocks the model is shown: channels, quotas, tie-breaks | `_candidates`, `_apply_channel_limits`, `_final_order` in `scratch/attention.py` | `tests/test_scratch_attention.py::test_every_attention_channel_is_independent_and_pack_is_reproducible` |
| The caps a run actually runs under (pack size, embedder, roles) | `ScratchPolicy` and `ScratchPolicy.attention_policy` in `run_manifest.py` — a manifest surface, so `DR-INV-frozen-surfaces` applies | `tests/test_run_manifest_scratch_bridge.py::test_v3_round_trip_freezes_complete_attention_and_bridge_policy` |
| The text the model actually sees: handles, truncation, warning | `ScratchRenderer.render_attention_pack` in `scratch/render.py` | `tests/test_scratch_render.py::test_long_fields_are_deterministically_and_visibly_truncated` |
| The JSON schema the model fills in for a block, link or guide | the `*WireContract` classes in `scratch/contracts.py` | `tests/test_scratch_contracts.py::test_the_endpoint_rule_is_enforced_by_the_schema_not_only_by_prose` |
| What one turn may propose, and its ceilings | `ScratchProposalV1` in `scratch/proposals.py` plus `maximum_*_per_turn` / `maximum_total_bytes` on the manifest scratch-authoring policy | `tests/test_v6_scratch_atomicity.py::test_unknown_reference_is_rejected_before_any_scratch_event` |
| Add a new scratch mutation kind | `ScratchAction` and its arity row in `scratch/events.py`, `_expected_output_schemas` + `apply` in `scratch/state.py`, one `ScratchService` method | `tests/test_scratch_replay.py::test_typed_event_contract_rejects_raw_actions_and_formal_graph_injection` |
| How Conj's advisory context is planned, fenced and committed | `plan_conjecture_context` / `commit_conjecture_context` in `scratch/conjecture.py` | `tests/test_v6_conjecture_scratch_consumption.py::test_initial_v6_conjecture_commits_exact_model_facing_scratch_once` |
| The anti-starvation cadence, or when a cycle restarts | `CoverageController.coverage_due` / `record_receipt` in `scratch/coverage.py` | `tests/test_scratch_coverage.py::test_continued_packs_eventually_select_pathological_block_by_coverage` |
| The embedder, its fallback, or the similarity threshold | `select_embedder` in `scratch/similarity.py` | `tests/test_scratch_similarity.py::test_unavailable_optional_backend_uses_visibly_identified_deterministic_fallback` |
| Giving criticism or adjudication any scratch object | refused by contract — see `DR-SEAM-rules-x-scratch` | `tests/test_prose_refutation_boundaries.py::test_no_scratch_identifier_reaches_a_warrant_or_an_attack_edge` |

`check: python -m pytest tests/test_scratch_provenance_refs.py::test_every_rule_the_validator_enforces_is_visible_in_the_schema tests/test_scratch_attention.py::test_every_attention_channel_is_independent_and_pack_is_reproducible tests/test_run_manifest_scratch_bridge.py::test_v3_round_trip_freezes_complete_attention_and_bridge_policy tests/test_scratch_render.py::test_long_fields_are_deterministically_and_visibly_truncated tests/test_scratch_contracts.py::test_the_endpoint_rule_is_enforced_by_the_schema_not_only_by_prose tests/test_v6_scratch_atomicity.py::test_unknown_reference_is_rejected_before_any_scratch_event tests/test_scratch_replay.py::test_typed_event_contract_rejects_raw_actions_and_formal_graph_injection tests/test_v6_conjecture_scratch_consumption.py::test_initial_v6_conjecture_commits_exact_model_facing_scratch_once tests/test_scratch_coverage.py::test_continued_packs_eventually_select_pathological_block_by_coverage tests/test_scratch_similarity.py::test_unavailable_optional_backend_uses_visibly_identified_deterministic_fallback tests/test_prose_refutation_boundaries.py::test_no_scratch_identifier_reaches_a_warrant_or_an_attack_edge -q`

## Traps

- **A refusal raised from inside a nested draft item kills the whole turn.** In
  turmite `run-bc3e8797b3e0609eddb324299c8257bd` a proposal declared exactly one
  new block, so no legal `to_ref` existed: every candidate target was either that
  same block (a self-link) or a key the response never declared. The old
  `_not_a_self_link` validator rejected the entire conjecture turn, candidates
  and all; the model oscillated between the two invalid values across four repair
  attempts, the seat exhausted its smallest authorized contract, and the run died
  at cycle 0 discarding a correct refutation it had already written. A self-link
  is inert, so `_drop_self_links` now DISCARDS it on the container — the only
  place an element can actually be removed — and runs before the
  namespace-closure check so a dropped link stops contributing references.
  Judgement belongs on the item; disposal belongs on the container.
`check: grep -q "def _drop_self_links" src/deepreason/scratch/proposals.py && ! grep -q "_not_a_self_link" src/deepreason/scratch/proposals.py && python -m pytest tests/test_scratch_contracts.py::test_a_self_link_is_dropped_rather_than_killing_the_whole_turn -q`
- **A rule stated only in a docstring is a rule the model cannot obey.** With
  glm-5.2's reasoning disabled, `scratch.link.compact.v1` scored 11/20 then 9/20
  first-pass valid and failed production qualification twice: its "exactly one of
  index/handle per endpoint" rule lived in the class docstring while the schema
  left all four reference fields independently optional. On the gpt-oss:20b
  battery the same contract failed the release gate on invented handles because
  the schema said only `{"type": "string"}` where the compiler already knew the
  exact alias table. Constraints belong in the emitted JSON Schema — and a
  `json_schema_extra` `items` REPLACES the rendered item type, so restate `type`
  beside any `pattern` or a number slips past it.
`check: python -m pytest tests/test_scratch_contracts.py::test_the_endpoint_rule_is_enforced_by_the_schema_not_only_by_prose tests/test_scratch_contracts.py::test_legal_handles_are_named_in_the_schema_not_only_enforced_by_the_compiler -q`
- **Render-receipt handle maps reload key-sorted.** Canonical JSON sorts keys
  lexicographically, so a reloaded map iterates `B1, B10, B11, B2, …`. In
  selfstudy `run-9175f0ec` (replay seqs 390/547) a consumer comparing `.values()`
  against a selection's `final_order` reported spurious order violations on
  faithful renders once a window reached ten blocks. Compare through
  `ordered_refs`, which sorts by handle INDEX, never through `.values()`.
`check: python -m pytest tests/test_scratch_render.py::test_ordered_refs_survive_canonical_json_at_ten_plus_handles -q && grep -q "never through .values()" src/deepreason/scratch/render.py`
- **The harness may not author interpretive scratch.** `ScratchActor.HARNESS` is
  refused for the eight interpretive actions — block creation and revision, link
  creation and retirement, cluster creation, membership changes, guide writing.
  It may still record link USE, similarity, attention renders, advisory-context
  binding and coverage. Otherwise the system could manufacture its own notes and
  read them back as if a model had thought them.
`check: grep -q "the harness cannot author interpretive scratch action" src/deepreason/scratch/events.py`
- **A historical view must be inert.** Every mutating path re-checks writability
  and raises `ScratchReadOnly`, including all three Conj planning functions —
  planning future work off a replayed prefix would append events into a root that
  was already verified.
`check: test "$(grep -c "ScratchReadOnly(" src/deepreason/scratch/conjecture.py)" -eq 3 && python -m pytest tests/test_scratch_historical.py -q`
- **Formal and scratch aliases share one prompt but must not share a namespace.**
  `SRC_###` is formal, `SCR_###`/`NEW_###` is scratch; an overlap is refused at
  wire construction, because a collision would let a scratch note resolve as a
  formal artifact reference.
`check: grep -q "formal and scratch alias namespaces must not overlap" src/deepreason/llm/wire.py`
- **Provenance refs are aim-at-time-of-writing, not live pointers.**
  `experiment_refs` and `bears_on_refs` record what a note was FOR; nothing in the
  harness follows them, and they are admissible whether or not the aim turns out
  right. `MAX_PROVENANCE_REFS = 4` is a measured stop against `maximum_total_bytes`
  crowding, not a guess.
`check: grep -q "^MAX_PROVENANCE_REFS = 4" src/deepreason/scratch/models.py && python -m pytest tests/test_scratch_provenance_refs.py -q -k "history_and_not_as_live_pointers or hashes_as_it_did_before"`
- **Known and parked, not fixed:** block identity dumps with `exclude_none` while
  the byte accounting in `validate_proposal` does not, so two `null` placeholders
  cost the budget roughly five blocks of headroom (133 → 128 in the measurement
  recorded beside `MAX_PROVENANCE_REFS`). The divergence predates the
  provenance-ref fields and was not introduced by them.
