<!-- DR-SUB-bridge -->
Verified-at: 08dcdf3c
Verify: python -m pytest tests/test_bridge_workflow.py tests/test_bridge_events_replay.py tests/test_bridge_validate.py tests/test_bridge_failure_replay.py -q
Owns: src/deepreason/bridge/
Seams: DR-SEAM-application-x-bridge, DR-SEAM-bridge-x-harness, DR-SEAM-bridge-x-llm, DR-SEAM-bridge-x-manifest, DR-SEAM-bridge-x-ontology, DR-SEAM-bridge-x-scratch, DR-SEAM-bridge-x-verification, DR-SEAM-bridge-x-workflow

# Bridge — turning a stopped epistemic record into a grounded final answer

## What it is

`bridge/` is the only place where the run's formal record is turned into prose a
person reads, and it is built so that turning it into prose cannot change it. A
bridge opens at one exact event fence, extracts a bounded evidence pack, makes
the model write a *claim ledger* — one row per claim, each row carrying an
epistemic class and the canonical references that back it — then composes the
answer out of ledger rows only, validates every span against its row's class,
has a second model role review the grounding, and runs a bounded repair kernel
when review fails. Every stage appends a typed `Rule.BRIDGE` event whose
materialization is advisory: bridge records contribute no artifacts, warrants,
graph edges, statuses or adjudication inputs, and the event ontology refuses any
process event that carries a non-empty `StateDiff`. The whole run is idempotent
against a terminal pointer file, resumable after a crash from a durable
execution snapshot, and re-derivable — `verify_root` replays the log twice and
fails if the two bridge states differ. The package is deliberately import-light
at the top level, because `ontology/event.py` imports the bridge event envelope
and eager re-exports would close the cycle.
`check: grep -q "raise RuntimeError(\"bridge workflow altered formal materialized state\")" src/deepreason/bridge/harness.py && grep -q "never contribute artifacts, warrants, graph edges" src/deepreason/bridge/state.py && grep -q "raise ValueError(\"process events cannot mutate formal StateDiff\")" src/deepreason/ontology/event.py && ! grep -qE "^(from|import) " src/deepreason/bridge/__init__.py && grep -q "Exports are lazy" src/deepreason/bridge/__init__.py && grep -q "def __getattr__" src/deepreason/bridge/__init__.py`

## Entry points

- `harness.build_grounded_bridge` — the whole thing: bind the manifest, derive
  the effective policy, pin the fence, assemble the pack and catalog, run the
  workflow under retries, and write the terminal pointer files. Reached in
  production as `Harness.build_bridge`. Returns `BridgeTerminalResultV1`, a
  fixed machine-readable pointer record whose validators make a "successful"
  terminal without object IDs, or a failed one without diagnostics,
  unconstructible.
- `harness.preflight_bound_bridge_policy` — derive and validate bridge authority
  from a manifest with no runtime mutation; what the application layer calls
  before it binds an adapter.
- `Harness.record_bridge_event` — the sole public persistence seam. Revalidates
  every supplied `(schema, model)` pair against the shared object store and its
  computed canonical identity before any write, so a caller cannot author an ID
  into the log.
`check: grep -q "^def build_grounded_bridge(" src/deepreason/bridge/harness.py && grep -q "^def preflight_bound_bridge_policy(" src/deepreason/bridge/harness.py && grep -q "^class BridgeTerminalResultV1" src/deepreason/bridge/harness.py && grep -q "    def build_bridge(" src/deepreason/harness.py && grep -q "sole public bridge persistence seam" src/deepreason/harness.py && grep -q "    def record_bridge_event(" src/deepreason/harness.py`

- `workflow.BridgeWorkflow` / `.run` — the stage machine: Stage A ledger →
  optional bounded amendment → Stage B composition → validation → grounded
  review → bounded repair → `COMPLETED` or a typed `FAILED`. Single-use.
- `workflow.BridgeWorkflowPolicy` — the frozen knobs (review on/off, amendment
  and repair ceilings, the four model roles, ledger and composition contract
  versions).
- `ledger.build_claim_ledger_stage_a` / `.amend_claim_ledger_stage_a` — one
  bounded Stage A call against a closed input catalog, and the single
  additions-only amendment Stage B may request.
- `compose.BridgeComposer.compose` — Stage B; returns `COMPOSED`,
  `LEDGER_AMENDMENT_NEEDED` or `VALIDATION_FAILED`, never raw text.
- `evidence_pack.assemble_evidence_pack` / `.build_claim_ledger_catalog` — the
  fence-pinned, budgeted extraction (survivors, argued refutations, pairwise
  rulings, open rivalries, omissions, lineage) and its projection into the
  handle-addressed catalog the model actually sees.
- `review.GroundingReviewService` / `repair.GroundingRepairService` — the second
  role that checks every span against exact catalog excerpts, and the bounded
  correction kernel that may reword, downgrade, quarantine or remove a span.
- `validate.validate_claim_ledger` / `.validate_bridge_output` — the pure,
  model-free validators; the same functions run on the composed output and on
  every repaired output.
- `state.BridgeState` / `.rebuild_bridge_state` / `.validate_terminal_bridge_history`
  — the replay-derived index, its standalone rebuilder, and the post-terminal
  consistency predicate the harness runs before appending a bridge event inside
  a closed terminal epoch.
- `transactional_adapter.TransactionalBridgeAdapter` — the v6 wrapper that gives
  each model call its own complete workflow transaction, and recovers a restart
  from durable provider receipts instead of re-dispatching.
- `retry.run_bridge_workflow_with_retries` / `.authorize_workflow_retry` /
  `.authorize_operator_workflow_retry` — automatic whole-workflow retry under a
  frozen fence, and the explicit operator retry of an already-failed terminal.
- `derived.build_derived_bridge` / `.source_snapshot_digest` /
  `.open_derived_source` / `.reserve_derived_destination` — build a view of a
  read-only source root into a separate destination root, binding the source by
  a path-independent digest.
`check: grep -q "^class BridgeWorkflow:" src/deepreason/bridge/workflow.py && grep -q "^class BridgeWorkflowPolicy" src/deepreason/bridge/workflow.py && grep -q "^def build_claim_ledger_stage_a(" src/deepreason/bridge/ledger.py && grep -q "^def amend_claim_ledger_stage_a(" src/deepreason/bridge/ledger.py && grep -q "^class BridgeComposer:" src/deepreason/bridge/compose.py && grep -q "^def assemble_evidence_pack(" src/deepreason/bridge/evidence_pack.py && grep -q "^def build_claim_ledger_catalog(" src/deepreason/bridge/evidence_pack.py && grep -q "^class GroundingReviewService:" src/deepreason/bridge/review.py && grep -q "^class GroundingRepairService:" src/deepreason/bridge/repair.py && grep -q "^def validate_claim_ledger(" src/deepreason/bridge/validate.py && grep -q "^def validate_bridge_output(" src/deepreason/bridge/validate.py && grep -q "^class BridgeState" src/deepreason/bridge/state.py && grep -q "^def rebuild_bridge_state(" src/deepreason/bridge/state.py && grep -q "^def validate_terminal_bridge_history(" src/deepreason/bridge/state.py && grep -q "^class TransactionalBridgeAdapter:" src/deepreason/bridge/transactional_adapter.py && grep -q "^def run_bridge_workflow_with_retries(" src/deepreason/bridge/retry.py && grep -q "^def authorize_workflow_retry(" src/deepreason/bridge/retry.py && grep -q "^def authorize_operator_workflow_retry(" src/deepreason/bridge/retry.py && grep -q "^def build_derived_bridge(" src/deepreason/bridge/derived.py && grep -q "^def source_snapshot_digest(" src/deepreason/bridge/derived.py && grep -q "^def open_derived_source(" src/deepreason/bridge/derived.py && grep -q "^def reserve_derived_destination(" src/deepreason/bridge/derived.py`

## State it owns

Four files in the run root, all written atomically. `bridge-result.json` is the
terminal pointer record and the idempotency key — a second identical build reads
it and returns without a model call. `bridge-status.json` is the supervisor-
readable summary. `operations.py` owns `bridge-operation-status.json` and
`bridge-operation-result.json`, the running/failed markers an async worker
writes and a poller reads. `FINDINGS.md` is regenerated at the end of a build
but belongs to `findings.py`, not here. Everything else persists through the
harness rather than as files of its own: fifteen `bridge-*` object-store
schemas (evidence pack, input catalog, ledger and its entries / uncovered
requirements / source conflicts, output and its claim uses / unresolved items,
validation findings and reports, grounding findings and reviews, failure, and
the workflow-retry receipt), and one `Rule.BRIDGE` event per stage carrying a
`BridgeEventPayloadV1`. Rule and payload are paired by ontology well-formedness,
and the payload's inputs/outputs must equal the event's, so a bridge event can
neither appear bare nor be smuggled onto another rule.
`check: grep -q "^BRIDGE_RESULT_NAME = \"bridge-result.json\"" src/deepreason/bridge/harness.py && grep -q "^BRIDGE_STATUS_NAME = \"bridge-status.json\"" src/deepreason/bridge/harness.py && grep -q "^BRIDGE_OPERATION_STATUS_NAME = \"bridge-operation-status.json\"" src/deepreason/bridge/operations.py && grep -q "^BRIDGE_OPERATION_RESULT_NAME = \"bridge-operation-result.json\"" src/deepreason/bridge/operations.py && for s in write_running write_failure clear read_status read_result read_failure; do grep -q "^def $s(" src/deepreason/bridge/operations.py || exit 1; done && for s in bridge-ledger-entry bridge-uncovered-requirement bridge-source-conflict bridge-claim-ledger bridge-claim-use bridge-unresolved-item bridge-output bridge-validation-finding bridge-validation-report bridge-grounding-finding bridge-grounding-review bridge-ledger-input-catalog bridge-evidence-pack bridge-failure bridge-workflow-retry; do grep -q "\"$s\":" src/deepreason/storage/objects.py || exit 1; done && test "$(grep -c "\"bridge-[a-z-]*\":" src/deepreason/storage/objects.py)" -eq 15 && grep -q "if (self.rule == Rule.BRIDGE) != (self.bridge is not None):" src/deepreason/ontology/event.py`

In memory the package owns `harness.bridge_state`, rebuilt entirely by replay
and compared across two independent replays by `verify_root`. On the v6 path it
also owns one raw blob per build: a canonical `bridge.execution-snapshot.v1`
holding the fence, evidence pack, catalog, composition request and effective
policy. That blob is what makes a crashed build resumable — it is located by
scanning the workflow state's transaction work for `bridge.transaction-task.v2`
payloads naming its `execution_snapshot_ref`.
`check: grep -q "self.bridge_state = BridgeState()" src/deepreason/harness.py && grep -q "self.bridge_state.apply(" src/deepreason/harness.py && grep -q "fail(\"bridge-replay\", \"two replays produced different advisory bridge state\")" src/deepreason/invariants.py && grep -q "_BRIDGE_EXECUTION_SNAPSHOT_SCHEMA = \"bridge.execution-snapshot.v1\"" src/deepreason/bridge/harness.py && grep -q "snapshot_ref = harness.blobs.put(canonical_json(payload))" src/deepreason/bridge/harness.py`

## Where to change what

| To change... | Edit | Test |
|---|---|---|
| What a ledger row may assert, and which reference channels back which class | `ClaimClass` and `ClaimLedgerEntryV1` in `bridge/models.py`, AND `ClaimLedgerEntryWireV1/V2` plus `ClaimLedgerWireContractV2/V3` in `bridge/ledger.py` — both, or the model schema and the validator diverge | `tests/test_bridge_ledger.py::test_ungrounded_observation_and_inference_without_premises_fail` |
| Which rendering mode a claim class may be written in | `RENDERING_COMPATIBILITY` and `_allowed_modes` in `bridge/validate.py` | `tests/test_bridge_validate.py::test_every_invalid_cross_class_rendering_is_rejected`, `::test_recorded_observation_fact_mode_requires_explicit_profile_permission` |
| How Stage B picks a span's mode under composition v2 (it is derived, not model-authored) | `_RENDERING_PRECEDENCE` / `_MODE_FOR_CLASS` / `CompositionSpanWireV2` in `bridge/compose.py` | `tests/test_bridge_v3_epistemics.py::test_mixed_ledger_classes_derive_the_weakest_rendering_mode` |
| Whether review runs, the amendment and repair ceilings, the four roles, the contract pair | `BridgeWorkflowPolicy` in `bridge/workflow.py`, plus `bridge_policy` and `control_plane_policy.contract_versions` on the manifest — a manifest surface, so `DR-INV-frozen-surfaces` and the qualification-cache cost apply | `tests/test_bridge_workflow_retry.py::test_policy_is_frozen_bounded_and_canonical` |
| The stage order, or which objects a stage may emit | `BridgeWorkflow.run` in `bridge/workflow.py`, `BridgeAction` in `bridge/events.py`, and `_ALLOWED_OUTPUT_SCHEMAS` / `_PRIMARY_SCHEMA` in `bridge/state.py` — record formats are frozen, see `DR-INV-frozen-surfaces` | `tests/test_bridge_events_replay.py::test_action_schema_and_lifecycle_checks_reject_malformed_bridge_events` |
| What evidence reaches Stage A, and its character budget | `assemble_evidence_pack`, `_catalog_items` and `DEFAULT_EVIDENCE_PACK_BUDGET` in `bridge/evidence_pack.py`; the reference channels themselves are `LedgerCatalogKind` in `bridge/ledger.py` | `tests/test_bridge_evidence_pack.py::test_structured_pack_preserves_every_load_bearing_thesis_category` |
| What a grounding repair is allowed to touch | `assert_safe_repair_diff`, `_quarantine_span` and `_MAX_SEMANTIC_REPAIR_CALLS` in `bridge/repair.py` | `tests/test_bridge_repair.py::test_safe_diff_guard_rejects_new_refs_and_new_spans` |
| Which whole-workflow failures retry, and the ceiling | `WorkflowRetryPolicyV1` and `authorize_workflow_retry` in `bridge/retry.py` | `tests/test_bridge_workflow_retry.py::test_unlisted_error_and_retry_ceiling_stop_without_an_extra_attempt` |
| Fields on the terminal pointer record, or what counts as a well-formed terminal | `BridgeTerminalResultV1` in `bridge/harness.py` | `tests/test_bridge_workflow.py::test_harness_build_bridge_uses_fixed_fence_and_writes_typed_terminal` |
| How a v6 model call is transacted, and what a restart may reuse | `TransactionalBridgeAdapter` in `bridge/transactional_adapter.py` plus `_load_bridge_execution_snapshot` / `_find_bridge_execution_snapshot` in `bridge/harness.py` | `tests/test_v6_bridge_transactions.py::test_v6_bridge_restart_missing_snapshot_fails_before_dispatch` |
| Building from a stopped run into a separate output root | `bridge/derived.py` plus the `derived` branch of `build_grounded_bridge` | `tests/test_bridge_derived.py::test_low_level_derived_bridge_recomputes_digest_and_rejects_overlap`, `::test_derived_holdout_availability_is_fixed_at_source_fence` |
| The CLI/service surface (flags, intents, async worker, poll files) | `cli/bridge.py` and `application/bridge.py` — NOT this package; they may not own workflow or persistence | `tests/test_application_bridge_service.py::test_bridge_clients_do_not_own_workflow_or_persistence` |

`check: grep -q "^RENDERING_COMPATIBILITY: dict\[ClaimClass, frozenset\[RenderingMode\]\] = {" src/deepreason/bridge/validate.py && grep -q "^def _allowed_modes(" src/deepreason/bridge/validate.py && grep -q "^_RENDERING_PRECEDENCE = (" src/deepreason/bridge/compose.py && grep -q "^_MODE_FOR_CLASS = {" src/deepreason/bridge/compose.py && ! sed -n "/^class CompositionSpanWireV2/,/^class CompositionUnresolvedWireV1/p" src/deepreason/bridge/compose.py | grep -q "rendering_mode" && grep -q "^class LedgerCatalogKind(str, Enum):" src/deepreason/bridge/ledger.py && grep -q "^DEFAULT_EVIDENCE_PACK_BUDGET = 24_000" src/deepreason/bridge/evidence_pack.py && grep -q "^_MAX_SEMANTIC_REPAIR_CALLS = 8" src/deepreason/bridge/repair.py && grep -q "^class RepairDisposition(str, Enum):" src/deepreason/bridge/repair.py && grep -q "^def _quarantine_span(" src/deepreason/bridge/repair.py && python -m pytest tests/test_bridge_ledger.py::test_ungrounded_observation_and_inference_without_premises_fail tests/test_bridge_validate.py::test_every_invalid_cross_class_rendering_is_rejected tests/test_bridge_validate.py::test_recorded_observation_fact_mode_requires_explicit_profile_permission tests/test_bridge_events_replay.py::test_action_schema_and_lifecycle_checks_reject_malformed_bridge_events tests/test_bridge_evidence_pack.py::test_structured_pack_preserves_every_load_bearing_thesis_category tests/test_bridge_v3_epistemics.py::test_mixed_ledger_classes_derive_the_weakest_rendering_mode tests/test_bridge_workflow_retry.py::test_policy_is_frozen_bounded_and_canonical tests/test_bridge_workflow_retry.py::test_unlisted_error_and_retry_ceiling_stop_without_an_extra_attempt tests/test_bridge_workflow.py::test_harness_build_bridge_uses_fixed_fence_and_writes_typed_terminal tests/test_bridge_derived.py::test_low_level_derived_bridge_recomputes_digest_and_rejects_overlap tests/test_bridge_derived.py::test_derived_holdout_availability_is_fixed_at_source_fence tests/test_v6_bridge_transactions.py::test_v6_bridge_restart_missing_snapshot_fails_before_dispatch tests/test_application_bridge_service.py::test_bridge_clients_do_not_own_workflow_or_persistence -q`

## Traps

- **The `BridgeWorkflowPolicy` a caller passes is NOT the policy that runs.**
  `_derive_bridge_execution_policy` requires the supplied value to equal the
  manifest's *historical v1 projection* — `BRIDGE_WORKFLOW_POLICY_MISMATCH`
  otherwise — and then derives the effective policy from the control plane's
  `contract_versions`. So `application/bridge.py` deliberately hands down a
  policy whose `ledger_contract_version` is `"v1"` while the run executes v3/v2.
  "Fixing" the caller to pass the real contract version breaks every v6 build.
`check: grep -q "historical_projection = bridge.workflow_policy(ledger_contract_version=\"v1\")" src/deepreason/bridge/harness.py && grep -q "raise ValueError(\"BRIDGE_WORKFLOW_POLICY_MISMATCH\")" src/deepreason/bridge/harness.py && grep -q "^def _historical_bridge_caller_policy(" src/deepreason/application/bridge.py && python -m pytest tests/test_v6_bridge_transactions.py::test_v6_application_supplies_only_historical_bridge_caller_projection -q`
- **A completed epistemic resolution is permanent; only a PROCESS failure may be
  retried.** `retry_failed_terminal` fails closed with
  `BRIDGE_RETRY_TERMINAL_NOT_FAILED` on any terminal whose `process_status` is
  `success`, however unwelcome its `resolution` — refused, conflicted and
  underdetermined are answers, and retrying them is answer shopping. Separately,
  a stored terminal whose `source_terminal_commitment_ref` no longer matches the
  run's current terminal commitment is treated as a superseded fence-stamped
  snapshot: `_read_existing_bridge_terminal` returns `None` and a fresh view
  composes at the new fence rather than the stale one being served as final.
`check: grep -q "BRIDGE_RETRY_TERMINAL_NOT_FAILED" src/deepreason/bridge/harness.py && grep -q "BRIDGE_RETRY_TRANSACTIONAL_REQUIRED" src/deepreason/bridge/harness.py && grep -q "Fence supersession" src/deepreason/bridge/harness.py && grep -q "retrying it would be answer" src/deepreason/bridge/harness.py && python -m pytest tests/test_bridge_retry_failed_terminal.py::test_failed_terminal_stays_idempotent_without_the_flag tests/test_bridge_retry_failed_terminal.py::test_completed_terminal_is_superseded_when_the_commitment_advances -q`
- **Repair is a text edit, never a re-grounding.** `assert_safe_repair_diff`
  rejects a changed ledger id, an added span, any change to a span's
  `ledger_entry_ids`, any change of `rendering_mode`, a newly asserted
  `resolution=answered`, and any edit to unresolved items — each with its own
  typed code. The same predicate is re-run by `BridgeState` during replay, so a
  controller bug that produced a laundered output fails `verify_root` rather
  than reaching a reader. An epistemic-class change is only legal through an
  explicit ledger amendment.
`check: for c in BRIDGE_REPAIR_LEDGER_CHANGED BRIDGE_REPAIR_SPAN_ADDED BRIDGE_REPAIR_REFS_CHANGED BRIDGE_REPAIR_CLASS_CHANGE_REQUIRES_AMENDMENT BRIDGE_REPAIR_RESOLUTION_TOO_STRONG BRIDGE_REPAIR_UNRESOLVED_CHANGED; do grep -q "\"$c\"" src/deepreason/bridge/repair.py || exit 1; done && grep -q "from deepreason.bridge.repair import assert_safe_repair_diff" src/deepreason/bridge/state.py && python -m pytest tests/test_bridge_repair.py::test_safe_diff_guard_rejects_new_refs_and_new_spans tests/test_bridge_repair.py::test_class_downgrade_is_an_explicit_amendment_not_unknown_remapping -q`
- **Scratch is provenance, not grounding, and the asymmetry is easy to undo.**
  Scratch blocks DO enter the Stage A catalog (as `scratch`-kind items via the
  attention pack's advisory context) but are deliberately excluded from the
  review materials, because an excerpt of a thought cannot ground a span. On the
  ledger side `scratch_refs` has its own field and its own type precisely so it
  can never satisfy a grounding requirement. Widening the review materials dict
  to all catalog items would silently make provenance count as evidence.
`check: grep -q "provenance cannot ground a span" src/deepreason/bridge/harness.py && grep -q "item.kind != \"scratch\"" src/deepreason/bridge/harness.py && grep -q "These refs never satisfy any grounding" src/deepreason/bridge/models.py && python -m pytest tests/test_bridge_ledger.py::test_structural_evidence_grounds_fact_but_scratch_provenance_does_not -q`
- **One authorized v6 dispatch, one receipt — counted once, appended once.**
  `BridgeState.apply_v6_provider_result` raises if the same provider attempt is
  accounted twice, and `_HarnessBridgeSink.persist_bridge_batch` drops
  `batch.llm` whenever the call carries a `dispatch_authorization_ref`, because
  the controller-v3 provider result already owns the sole canonical receipt.
  Re-attaching the call to the semantic bridge event double-counts tokens and
  breaks replay accounting; legacy (non-authorized) calls have no such ref and
  must still ride their event.
`check: grep -q "raise ValueError(\"bridge v6 provider result was counted twice\")" src/deepreason/bridge/state.py && grep -q "never append the same authorized dispatch a second time" src/deepreason/bridge/harness.py && grep -q "dispatch_authorization_ref" src/deepreason/bridge/harness.py && python -m pytest tests/test_v6_bridge_transactions.py::test_bridge_sink_does_not_append_transactional_call_twice -q`
- **One object-store slot holds two catalog contracts.**
  `bridge-ledger-input-catalog` maps to `ClaimLedgerInputCatalogV1`, whose
  `schema_` literal deliberately admits `bridge.catalog.v3`; the identity domain
  and the process-observation rules switch on that literal inside the model, and
  `ClaimLedgerInputCatalogV3` is never registered separately. Narrowing the V1
  literal, or registering V3 as its own schema, makes every existing v6 root
  unreadable — a change that invalidates replay-valid roots is wrong by
  definition.
`check: grep -q "raise ValueError(\"process observations require bridge.catalog.v3\")" src/deepreason/bridge/ledger.py && grep -q "\"bridge-ledger-input-catalog\": ClaimLedgerInputCatalogV1" src/deepreason/storage/objects.py && ! grep -q "ClaimLedgerInputCatalogV3" src/deepreason/storage/objects.py && python -m pytest tests/test_bridge_v3_epistemics.py::test_v3_catalog_with_process_records_round_trips_through_object_store -q`
- **A failure must still leave the reader everything the attempt saw.** The sink
  inserts the evidence pack on the first material event — `LEDGER_CREATED` *or*
  `FAILED` — and adds the catalog on the failure path, so even a Stage A death
  persists the exact inputs; and `BridgeWorkflow._failure` refuses to name any
  terminal input that is not a retained partial object. A new failure path that
  short-circuits before the sink produces an unreplayable, uninspectable death.
`check: grep -q "first_material_event = batch.action in {" src/deepreason/bridge/harness.py && grep -q "records.insert(0, (\"bridge-evidence-pack\", self.evidence_pack))" src/deepreason/bridge/harness.py && grep -q "raise RuntimeError(\"bridge failure inputs are not retained partial objects\")" src/deepreason/bridge/workflow.py && python -m pytest tests/test_bridge_failure_replay.py::test_stage_a_failure_is_canonical_and_replay_backed tests/test_bridge_failure_replay.py::test_late_failure_preserves_exact_partial_objects_and_replays -q`
- **`bridge.ledger.v3` and `bridge.composition.v2` are one contract, not two.**
  `BridgeWorkflowPolicy` rejects any policy selecting one without the other, and
  the v6 adapter refuses a manifest whose contract versions are not exactly that
  pair. A `BridgeWorkflow` instance is also single-use: re-running one raises
  rather than appending a second stage sequence onto the first attempt's
  batches.
`check: grep -q "bridge.ledger.v3 and bridge.composition.v2 must be selected together" src/deepreason/bridge/workflow.py && grep -q "v6 bridge adapter requires the frozen v3/v2 contract pair" src/deepreason/bridge/transactional_adapter.py && grep -q "raise RuntimeError(\"a BridgeWorkflow instance can run only once\")" src/deepreason/bridge/workflow.py`
