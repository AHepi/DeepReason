# dead.md — 2026-08-13 audit

Per-package reference census over every top-level `def`/`class` symbol
under `src/deepreason/` (82 packages/files), per `dr-audit-dead`'s
specified algorithm: for each symbol, (1) a cross-file reference scan
(`rg -l -w NAME src/ tests/ scripts/ tools/`, excluding the defining
file) — hits ⇒ verdict `referenced`; (2) a string/dynamic-dispatch
scan — hits ⇒ verdict `dynamic-ref`; (3) an entry-point scan against
`pyproject.toml` — hit ⇒ verdict `entry-point`; else verdict
`candidate-dead`.

**Totals: 2640 top-level symbols, 1727 `referenced`, 77 `dynamic-ref`,
0 `entry-point`, 836 `candidate-dead`.**

## Methodology finding, ahead of the per-symbol table (important — read first)

The worker's specified algorithm only searches for a symbol *outside*
its own defining file (G-step 2's `grep -v <defining-file>`). It never
checks whether the symbol is called from elsewhere **within the same
file**. In a codebase organized as large single-purpose modules (many
`.py` files run 1000–3800+ lines, e.g. `invariants.py`,
`run_manifest.py`, `bridge/*.py`), a great many top-level helpers are
private (`_leading_underscore`) and are only ever called by other
functions later in the *same* file — which is completely normal,
intentional, non-dead code, but the specified algorithm cannot tell
that apart from a genuinely orphaned symbol.

To separate the two without changing the worker's mechanical verdict
(G3 — this worker adds no judgment of its own; `candidate-dead` stays
the recorded verdict for all 836, per spec), every `candidate-dead`
row below was additionally annotated with a second mechanical count:
`grep -c -w NAME <its own file>` (does the symbol's own file contain
more than the one line where it's defined?).

- **821 of 836 (98.2%)** have 2+ occurrences in their own file — the
  symbol *is* called, just only from inside its own module. Spot
  checks confirm this is real, wired code, not dead code: e.g. all 7
  `candidate-dead` rows in `invariants.py`
  (`_expected_call_outcome`, `_controller_v3_history`,
  `ExpectedCallOutcome`, `_is_typed_bridge_failure`,
  `_legacy_bridge_failure_call_seqs`, `_amendment_epochs`,
  `_epoch_input_for_dossier`) are called from `verify_root`'s call
  graph inside that same file; all 8 sampled `bridge` package rows
  (`LedgerAmendmentWireV1`, `_exact_statement_detail`,
  `_VerifiedBlobView`, `_holdout_marker_exists`, `_sealed_blob_refs`,
  `_required_blob_refs`, `_absolute`, `_reject_symlink_components`)
  likewise have 2–4 in-file occurrences.
- **15 of 836 (1.8%)** have exactly 1 occurrence — the definition
  line and nothing else, anywhere in the tree, including their own
  file. These are the genuine candidates; listed in full below.
  Spot check: `_cmd_check_proof`, `_cmd_code`, `_cmd_simulate` in
  `cli/main.py` are defined but the CLI's `if args.command == ...`
  dispatch chain (`main()`, from line 664) has no `"check-proof"`,
  `"code"`, or `"simulate"` branch calling them — confirmed genuinely
  unwired, not just unreferenced by name.

**This is itself a `dr-audit-dead` methodology gap worth fixing**
(park below, P-D1): adding a same-file occurrence check as a cheap
pre-step before declaring `candidate-dead` would cut this dimension's
false-positive rate from 98% to near zero, at the cost of one more
`grep -c -w` per symbol (already computed here as a courtesy — not
part of the worker's specified steps, so it does not change any
verdict, only which rows are worth the operator's attention first).

## Tallies

| package | symbols | referenced | dynamic-ref | entry-point | candidate-dead | status |
|---|---|---|---|---|---|---|
| __init__.py | 0 | 0 | 0 | 0 | 0 | done |
| __main__.py | 0 | 0 | 0 | 0 | 0 | done |
| adjudication | 7 | 6 | 0 | 0 | 1 | done |
| admission | 34 | 22 | 2 | 0 | 10 | done |
| amendment | 39 | 22 | 0 | 0 | 17 | done |
| application | 130 | 79 | 5 | 0 | 46 | done |
| assets | 6 | 6 | 0 | 0 | 0 | done |
| authority.py | 14 | 9 | 0 | 0 | 5 | done |
| brain | 70 | 49 | 0 | 0 | 21 | done |
| bridge | 226 | 127 | 22 | 0 | 77 | done |
| browser.py | 7 | 7 | 0 | 0 | 0 | done |
| canonical.py | 2 | 2 | 0 | 0 | 0 | done |
| capabilities | 55 | 43 | 5 | 0 | 7 | done |
| capture | 33 | 27 | 1 | 0 | 5 | done |
| cli | 124 | 54 | 1 | 0 | 69 | done |
| compat_eval.py | 32 | 23 | 0 | 0 | 9 | done |
| config.py | 10 | 10 | 0 | 0 | 0 | done |
| conjecture_events.py | 2 | 2 | 0 | 0 | 0 | done |
| conjecture_turn.py | 10 | 8 | 1 | 0 | 1 | done |
| control_events.py | 3 | 3 | 0 | 0 | 0 | done |
| controller.py | 2 | 2 | 0 | 0 | 0 | done |
| easy.py | 32 | 22 | 0 | 0 | 10 | done |
| error_catalog.py | 3 | 2 | 0 | 0 | 1 | done |
| evidence | 45 | 37 | 0 | 0 | 8 | done |
| experiments | 111 | 57 | 8 | 0 | 46 | done |
| findings.py | 6 | 5 | 0 | 0 | 1 | done |
| frozen.py | 3 | 3 | 0 | 0 | 0 | done |
| harness.py | 3 | 3 | 0 | 0 | 0 | done |
| imports.py | 13 | 7 | 0 | 0 | 6 | done |
| indexes.py | 9 | 7 | 0 | 0 | 2 | done |
| informal | 51 | 35 | 0 | 0 | 16 | done |
| intake_form.py | 3 | 3 | 0 | 0 | 0 | done |
| invariants.py | 9 | 2 | 0 | 0 | 7 | done |
| jolts.py | 24 | 14 | 0 | 0 | 10 | done |
| llm | 258 | 169 | 0 | 0 | 89 | done |
| locking.py | 13 | 5 | 2 | 0 | 6 | done |
| log | 4 | 3 | 0 | 0 | 1 | done |
| loop.py | 1 | 1 | 0 | 0 | 0 | done |
| manifest.py | 19 | 13 | 0 | 0 | 6 | done |
| mcp_help.py | 4 | 2 | 0 | 0 | 2 | done |
| mcp_registration.py | 4 | 3 | 1 | 0 | 0 | done |
| mcp_scratch_bridge.py | 29 | 9 | 0 | 0 | 20 | done |
| mcp_server.py | 19 | 10 | 0 | 0 | 9 | done |
| measures | 17 | 10 | 0 | 0 | 7 | done |
| module_events.py | 3 | 3 | 0 | 0 | 0 | done |
| ontology | 23 | 23 | 0 | 0 | 0 | done |
| ops.py | 15 | 14 | 0 | 0 | 1 | done |
| oracle.py | 36 | 27 | 0 | 0 | 9 | done |
| oracle_sandbox.py | 10 | 5 | 0 | 0 | 5 | done |
| packs | 8 | 6 | 0 | 0 | 2 | done |
| preparation.py | 19 | 11 | 2 | 0 | 6 | done |
| programs.py | 27 | 12 | 0 | 0 | 15 | done |
| provider_profile.py | 12 | 9 | 0 | 0 | 3 | done |
| qualification.py | 29 | 21 | 2 | 0 | 6 | done |
| readiness.py | 8 | 5 | 2 | 0 | 1 | done |
| referee.py | 16 | 12 | 2 | 0 | 2 | done |
| report.py | 6 | 2 | 0 | 0 | 4 | done |
| research | 21 | 15 | 2 | 0 | 4 | done |
| rules | 81 | 46 | 0 | 0 | 35 | done |
| run_manifest.py | 81 | 53 | 0 | 0 | 28 | done |
| runtime | 74 | 44 | 1 | 0 | 29 | done |
| scheduler | 6 | 4 | 1 | 0 | 1 | done |
| scratch | 120 | 97 | 6 | 0 | 17 | done |
| seat_bindings.py | 13 | 12 | 0 | 0 | 1 | done |
| seat_events.py | 4 | 4 | 0 | 0 | 0 | done |
| shallow.py | 5 | 3 | 0 | 0 | 2 | done |
| shallow_fitness.py | 5 | 3 | 0 | 0 | 2 | done |
| signals.py | 4 | 4 | 0 | 0 | 0 | done |
| signals_read.py | 4 | 2 | 0 | 0 | 2 | done |
| simulation | 8 | 3 | 0 | 0 | 5 | done |
| skills | 55 | 40 | 0 | 0 | 15 | done |
| status_display.py | 3 | 2 | 0 | 0 | 1 | done |
| storage | 16 | 12 | 0 | 0 | 4 | done |
| ui | 4 | 3 | 0 | 0 | 1 | done |
| unification | 5 | 5 | 0 | 0 | 0 | done |
| v6_policy.py | 17 | 14 | 2 | 0 | 1 | done |
| verification | 73 | 52 | 3 | 0 | 18 | done |
| views | 59 | 34 | 0 | 0 | 25 | done |
| webapp.py | 9 | 3 | 1 | 0 | 5 | done |
| workflow | 171 | 128 | 5 | 0 | 38 | done |
| workflows | 27 | 18 | 0 | 0 | 9 | done |
| workloads | 77 | 53 | 0 | 0 | 24 | done |
## The 15 true candidates (0 occurrences anywhere, including own file)

These are the only rows where deletion review is actually likely to
be productive; each still needs a `dr-change-orchestrator` tranche
before anything is removed (X3 — `candidate-dead` is the strongest
claim this worker may make).

  - `last_json_line` (src/deepreason/brain/log.py) — TRUE-CANDIDATE (0 refs anywhere) — proof/dead-brain-last_json_line.txt
  - `retrieval_metrics` (src/deepreason/brain/metrics.py) — TRUE-CANDIDATE (0 refs anywhere) — proof/dead-brain-retrieval_metrics.txt
  - `_cmd_check_proof` (src/deepreason/cli/main.py) — TRUE-CANDIDATE (0 refs anywhere) — proof/dead-cli-_cmd_check_proof.txt
  - `_cmd_code` (src/deepreason/cli/main.py) — TRUE-CANDIDATE (0 refs anywhere) — proof/dead-cli-_cmd_code.txt
  - `_cmd_simulate` (src/deepreason/cli/main.py) — TRUE-CANDIDATE (0 refs anywhere) — proof/dead-cli-_cmd_simulate.txt
  - `_slug` (src/deepreason/easy.py) — TRUE-CANDIDATE (0 refs anywhere) — proof/dead-easy-_slug.txt
  - `_fresh` (src/deepreason/easy.py) — TRUE-CANDIDATE (0 refs anywhere) — proof/dead-easy-_fresh.txt
  - `_first_line` (src/deepreason/easy.py) — TRUE-CANDIDATE (0 refs anywhere) — proof/dead-easy-_first_line.txt
  - `suppressible_lineage_exemplars` (src/deepreason/jolts.py) — TRUE-CANDIDATE (0 refs anywhere) — proof/dead-jolts-suppressible_lineage_exemplars.txt
  - `_document_excerpt` (src/deepreason/llm/packs.py) — TRUE-CANDIDATE (0 refs anywhere) — proof/dead-llm-_document_excerpt.txt
  - `alias_references` (src/deepreason/llm/packs.py) — TRUE-CANDIDATE (0 refs anywhere) — proof/dead-llm-alias_references.txt
  - `domain_log_input` (src/deepreason/rules/guards/anti_relapse.py) — TRUE-CANDIDATE (0 refs anywhere) — proof/dead-rules-domain_log_input.txt
  - `refl` (src/deepreason/rules/refl.py) — TRUE-CANDIDATE (0 refs anywhere) — proof/dead-rules-refl.txt
  - `materialize_run_config` (src/deepreason/run_manifest.py) — TRUE-CANDIDATE (0 refs anywhere) — proof/dead-run_manifest-materialize_run_config.txt
  - `record_trigger_decision` (src/deepreason/views/jolt_signals.py) — TRUE-CANDIDATE (0 refs anywhere) — proof/dead-views-record_trigger_decision.txt

## Full candidate-dead table, by package (all 836, both classes)

### adjudication

  - `grounded_extension` (src/deepreason/adjudication/grounded.py) — intra-file-only (2 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-adjudication-grounded_extension.txt

### admission

  - `_first_party_manifests` (src/deepreason/admission/adapters.py) — intra-file-only (2 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-admission-_first_party_manifests.txt
  - `_spine_order` (src/deepreason/admission/adapters_epub.py) — intra-file-only (2 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-admission-_spine_order.txt
  - `_line_offsets` (src/deepreason/admission/parse.py) — intra-file-only (3 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-admission-_line_offsets.txt
  - `_mint_span_block` (src/deepreason/admission/parse.py) — intra-file-only (4 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-admission-_mint_span_block.txt
  - `_segment_text` (src/deepreason/admission/parse.py) — intra-file-only (2 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-admission-_segment_text.txt
  - `_format_number` (src/deepreason/admission/parse.py) — intra-file-only (4 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-admission-_format_number.txt
  - `_csv_projections` (src/deepreason/admission/parse.py) — intra-file-only (2 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-admission-_csv_projections.txt
  - `_first_heading` (src/deepreason/admission/parse.py) — intra-file-only (2 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-admission-_first_heading.txt
  - `_adapter_blocks` (src/deepreason/admission/parse.py) — intra-file-only (2 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-admission-_adapter_blocks.txt
  - `_state_home` (src/deepreason/admission/store.py) — intra-file-only (2 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-admission-_state_home.txt

### amendment

  - `_reshaped_problem_id` (src/deepreason/amendment/apply.py) — intra-file-only (2 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-amendment-_reshaped_problem_id.txt
  - `_require_terminal_stop` (src/deepreason/amendment/apply.py) — intra-file-only (2 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-amendment-_require_terminal_stop.txt
  - `_admit_supplement` (src/deepreason/amendment/apply.py) — intra-file-only (2 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-amendment-_admit_supplement.txt
  - `_check_evidence_budget` (src/deepreason/amendment/apply.py) — intra-file-only (2 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-amendment-_check_evidence_budget.txt
  - `_successor_workload` (src/deepreason/amendment/apply.py) — intra-file-only (2 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-amendment-_successor_workload.txt
  - `_parent_workload` (src/deepreason/amendment/apply.py) — intra-file-only (2 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-amendment-_parent_workload.txt
  - `_amend_locked` (src/deepreason/amendment/apply.py) — intra-file-only (2 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-amendment-_amend_locked.txt
  - `_stage_epoch_documents` (src/deepreason/amendment/apply.py) — intra-file-only (2 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-amendment-_stage_epoch_documents.txt
  - `_now` (src/deepreason/amendment/apply.py) — intra-file-only (3 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-amendment-_now.txt
  - `_write_once` (src/deepreason/amendment/apply.py) — intra-file-only (9 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-amendment-_write_once.txt
  - `_discard_staged_epoch` (src/deepreason/amendment/apply.py) — intra-file-only (2 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-amendment-_discard_staged_epoch.txt
  - `_AmendmentRecord` (src/deepreason/amendment/models.py) — intra-file-only (2 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-amendment-_AmendmentRecord.txt
  - `_epoch_root` (src/deepreason/amendment/state.py) — intra-file-only (5 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-amendment-_epoch_root.txt
  - `_epoch_manifest_path` (src/deepreason/amendment/state.py) — intra-file-only (2 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-amendment-_epoch_manifest_path.txt
  - `_chain_path` (src/deepreason/amendment/state.py) — intra-file-only (2 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-amendment-_chain_path.txt
  - `_read_chain_lines` (src/deepreason/amendment/state.py) — intra-file-only (2 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-amendment-_read_chain_lines.txt
  - `_decode_record` (src/deepreason/amendment/state.py) — intra-file-only (3 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-amendment-_decode_record.txt

### application

  - `_model_json` (src/deepreason/application/bridge.py) — intra-file-only (18 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-application-_model_json.txt
  - `_json_item` (src/deepreason/application/bridge.py) — intra-file-only (2 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-application-_json_item.txt
  - `_page_model_field` (src/deepreason/application/bridge.py) — intra-file-only (4 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-application-_page_model_field.txt
  - `_bounded_json_text` (src/deepreason/application/bridge.py) — intra-file-only (4 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-application-_bounded_json_text.txt
  - `_finish_bounded_payload` (src/deepreason/application/bridge.py) — intra-file-only (5 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-application-_finish_bounded_payload.txt
  - `_notify` (src/deepreason/application/bridge.py) — intra-file-only (3 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-application-_notify.txt
  - `_start_result` (src/deepreason/application/bridge.py) — intra-file-only (6 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-application-_start_result.txt
  - `_GroundedBridgePageIntentV1` (src/deepreason/application/bridge.py) — intra-file-only (5 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-application-_GroundedBridgePageIntentV1.txt
  - `_PreparedBridge` (src/deepreason/application/bridge.py) — intra-file-only (4 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-application-_PreparedBridge.txt
  - `validate_reference` (src/deepreason/application/bridge.py) — intra-file-only (3 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-application-validate_reference.txt
  - `_validate_manifest_files` (src/deepreason/application/bridge.py) — intra-file-only (5 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-application-_validate_manifest_files.txt
  - `_load_manifest_without_echo` (src/deepreason/application/bridge.py) — intra-file-only (5 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-application-_load_manifest_without_echo.txt
  - `_build_canonical` (src/deepreason/application/bridge.py) — intra-file-only (2 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-application-_build_canonical.txt
  - `_build_derived` (src/deepreason/application/bridge.py) — intra-file-only (2 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-application-_build_derived.txt
  - `_load_result_manifest` (src/deepreason/application/bridge.py) — intra-file-only (2 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-application-_load_result_manifest.txt
  - `_shared_meter_snapshot` (src/deepreason/application/conjecture.py) — intra-file-only (3 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-application-_shared_meter_snapshot.txt
  - `CompactRecoveryLanguageV1` (src/deepreason/application/models.py) — intra-file-only (3 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-application-CompactRecoveryLanguageV1.txt
  - `RouteSeatBaseProjectionV1` (src/deepreason/application/models.py) — intra-file-only (4 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-application-RouteSeatBaseProjectionV1.txt
  - `CompactRecoveryRouteProjectionV1` (src/deepreason/application/models.py) — intra-file-only (4 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-application-CompactRecoveryRouteProjectionV1.txt
  - `RouteSeatModelClassificationProjectionV1` (src/deepreason/application/models.py) — intra-file-only (4 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-application-RouteSeatModelClassificationProjectionV1.txt
  - `AtomicWorkAttemptProjectionV1` (src/deepreason/application/models.py) — intra-file-only (4 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-application-AtomicWorkAttemptProjectionV1.txt
  - `ContractDecompositionProjectionV1` (src/deepreason/application/models.py) — intra-file-only (4 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-application-ContractDecompositionProjectionV1.txt
  - `RouteSeatInsufficientCapabilityProjectionV1` (src/deepreason/application/models.py) — intra-file-only (4 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-application-RouteSeatInsufficientCapabilityProjectionV1.txt
  - `RunStopReceiptV1` (src/deepreason/application/models.py) — intra-file-only (2 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-application-RunStopReceiptV1.txt
  - `ScratchIdentityIndexV1` (src/deepreason/application/scratch.py) — intra-file-only (4 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-application-ScratchIdentityIndexV1.txt
  - `ScratchBlockSummaryV1` (src/deepreason/application/scratch.py) — intra-file-only (6 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-application-ScratchBlockSummaryV1.txt
  - `ScratchLinkSummaryV1` (src/deepreason/application/scratch.py) — intra-file-only (6 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-application-ScratchLinkSummaryV1.txt
  - `ScratchClusterMapItemV1` (src/deepreason/application/scratch.py) — intra-file-only (4 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-application-ScratchClusterMapItemV1.txt
  - `ScratchRelatedClusterV1` (src/deepreason/application/scratch.py) — intra-file-only (4 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-application-ScratchRelatedClusterV1.txt
  - `ScratchSimilaritySummaryV1` (src/deepreason/application/scratch.py) — intra-file-only (4 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-application-ScratchSimilaritySummaryV1.txt
  - `ScratchRelatedBlockV1` (src/deepreason/application/scratch.py) — intra-file-only (4 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-application-ScratchRelatedBlockV1.txt
  - `_ResultBase` (src/deepreason/application/scratch.py) — intra-file-only (6 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-application-_ResultBase.txt
  - `_ScratchOpenResultBase` (src/deepreason/application/scratch.py) — intra-file-only (3 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-application-_ScratchOpenResultBase.txt
  - `_identity_index` (src/deepreason/application/scratch.py) — intra-file-only (6 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-application-_identity_index.txt
  - `_open_result_values` (src/deepreason/application/scratch.py) — intra-file-only (3 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-application-_open_result_values.txt
  - `_QueryBase` (src/deepreason/application/scratch.py) — intra-file-only (4 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-application-_QueryBase.txt
  - `_HistoricalQueryBase` (src/deepreason/application/scratch.py) — intra-file-only (4 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-application-_HistoricalQueryBase.txt
  - `_BlockQueryBase` (src/deepreason/application/scratch.py) — intra-file-only (3 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-application-_BlockQueryBase.txt
  - `_record_exhaustion_lifecycle_stop` (src/deepreason/application/text_runs.py) — intra-file-only (2 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-application-_record_exhaustion_lifecycle_stop.txt
  - `_budget_values` (src/deepreason/application/text_runs.py) — intra-file-only (2 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-application-_budget_values.txt
  - `_request_path` (src/deepreason/application/text_runs.py) — intra-file-only (3 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-application-_request_path.txt
  - `_request_for_intent` (src/deepreason/application/text_runs.py) — intra-file-only (2 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-application-_request_for_intent.txt
  - `_read_request` (src/deepreason/application/text_runs.py) — intra-file-only (2 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-application-_read_request.txt
  - `_spec_from_request` (src/deepreason/application/text_runs.py) — intra-file-only (3 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-application-_spec_from_request.txt
  - `_run_input_matches_spec` (src/deepreason/application/text_runs.py) — intra-file-only (2 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-application-_run_input_matches_spec.txt
  - `_require_v6_manifest` (src/deepreason/application/text_runs.py) — intra-file-only (4 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-application-_require_v6_manifest.txt

### authority.py

  - `calibration_receipt` (src/deepreason/authority.py) — intra-file-only (3 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-authority-calibration_receipt.txt
  - `AuthorityPolicyIssue` (src/deepreason/authority.py) — intra-file-only (7 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-authority-AuthorityPolicyIssue.txt
  - `_get` (src/deepreason/authority.py) — intra-file-only (6 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-authority-_get.txt
  - `text_authority_mode` (src/deepreason/authority.py) — intra-file-only (4 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-authority-text_authority_mode.txt
  - `_adjudication_status_authority_enabled` (src/deepreason/authority.py) — intra-file-only (2 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-authority-_adjudication_status_authority_enabled.txt

### brain

  - `_calendar_age` (src/deepreason/brain/activation.py) — intra-file-only (3 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-brain-_calendar_age.txt
  - `_logical_age` (src/deepreason/brain/activation.py) — intra-file-only (3 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-brain-_logical_age.txt
  - `card_path` (src/deepreason/brain/cards.py) — intra-file-only (4 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-brain-card_path.txt
  - `_bounded` (src/deepreason/brain/cards.py) — intra-file-only (3 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-brain-_bounded.txt
  - `card_for_record` (src/deepreason/brain/cards.py) — intra-file-only (2 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-brain-card_for_record.txt
  - `_compatible_base` (src/deepreason/brain/cards.py) — intra-file-only (2 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-brain-_compatible_base.txt
  - `_index_source_digest` (src/deepreason/brain/index.py) — intra-file-only (2 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-brain-_index_source_digest.txt
  - `_connect` (src/deepreason/brain/index.py) — intra-file-only (7 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-brain-_connect.txt
  - `vector_buckets` (src/deepreason/brain/index.py) — intra-file-only (3 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-brain-vector_buckets.txt
  - `_compatible_projection` (src/deepreason/brain/index.py) — intra-file-only (2 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-brain-_compatible_projection.txt
  - `last_json_line` (src/deepreason/brain/log.py) — TRUE-CANDIDATE (0 refs anywhere) — proof/dead-brain-last_json_line.txt
  - `retrieval_metrics` (src/deepreason/brain/metrics.py) — TRUE-CANDIDATE (0 refs anywhere) — proof/dead-brain-retrieval_metrics.txt
  - `BrainModel` (src/deepreason/brain/models.py) — intra-file-only (15 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-brain-BrainModel.txt
  - `memory_identity` (src/deepreason/brain/models.py) — intra-file-only (3 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-brain-memory_identity.txt
  - `_jsonable` (src/deepreason/brain/models.py) — intra-file-only (5 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-brain-_jsonable.txt
  - `make_inclusion_proofs` (src/deepreason/brain/receipts.py) — intra-file-only (2 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-brain-make_inclusion_proofs.txt
  - `_ppm` (src/deepreason/brain/retrieve.py) — intra-file-only (3 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-brain-_ppm.txt
  - `_novelty_ppm` (src/deepreason/brain/retrieve.py) — intra-file-only (3 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-brain-_novelty_ppm.txt
  - `_weighted_score` (src/deepreason/brain/retrieve.py) — intra-file-only (2 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-brain-_weighted_score.txt
  - `_quota_select` (src/deepreason/brain/retrieve.py) — intra-file-only (4 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-brain-_quota_select.txt
  - `BlobStoreLike` (src/deepreason/brain/snapshot.py) — intra-file-only (3 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-brain-BlobStoreLike.txt

### bridge

  - `LedgerAmendmentWireV1` (src/deepreason/bridge/compose.py) — intra-file-only (3 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-bridge-LedgerAmendmentWireV1.txt
  - `_exact_statement_detail` (src/deepreason/bridge/compose.py) — intra-file-only (3 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-bridge-_exact_statement_detail.txt
  - `_VerifiedBlobView` (src/deepreason/bridge/derived.py) — intra-file-only (2 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-bridge-_VerifiedBlobView.txt
  - `_holdout_marker_exists` (src/deepreason/bridge/derived.py) — intra-file-only (2 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-bridge-_holdout_marker_exists.txt
  - `_sealed_blob_refs` (src/deepreason/bridge/derived.py) — intra-file-only (2 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-bridge-_sealed_blob_refs.txt
  - `_required_blob_refs` (src/deepreason/bridge/derived.py) — intra-file-only (2 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-bridge-_required_blob_refs.txt
  - `_absolute` (src/deepreason/bridge/derived.py) — intra-file-only (4 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-bridge-_absolute.txt
  - `_reject_symlink_components` (src/deepreason/bridge/derived.py) — intra-file-only (3 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-bridge-_reject_symlink_components.txt
  - `_validate_roots` (src/deepreason/bridge/derived.py) — intra-file-only (3 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-bridge-_validate_roots.txt
  - `_is_link_like` (src/deepreason/bridge/derived.py) — intra-file-only (9 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-bridge-_is_link_like.txt
  - `_checked_directory` (src/deepreason/bridge/derived.py) — intra-file-only (3 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-bridge-_checked_directory.txt
  - `_read_verified_blob` (src/deepreason/bridge/derived.py) — intra-file-only (3 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-bridge-_read_verified_blob.txt
  - `_claim_line` (src/deepreason/bridge/evidence_pack.py) — intra-file-only (2 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-bridge-_claim_line.txt
  - `_is_source_artifact` (src/deepreason/bridge/evidence_pack.py) — intra-file-only (4 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-bridge-_is_source_artifact.txt
  - `_artifact_content_available` (src/deepreason/bridge/evidence_pack.py) — intra-file-only (11 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-bridge-_artifact_content_available.txt
  - `_is_evidence_artifact` (src/deepreason/bridge/evidence_pack.py) — intra-file-only (4 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-bridge-_is_evidence_artifact.txt
  - `_evidence_sources` (src/deepreason/bridge/evidence_pack.py) — intra-file-only (3 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-bridge-_evidence_sources.txt
  - `_lineage` (src/deepreason/bridge/evidence_pack.py) — intra-file-only (3 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-bridge-_lineage.txt
  - `_decisive_from_warrants` (src/deepreason/bridge/evidence_pack.py) — intra-file-only (2 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-bridge-_decisive_from_warrants.txt
  - `_bounded_structured_text` (src/deepreason/bridge/evidence_pack.py) — intra-file-only (9 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-bridge-_bounded_structured_text.txt
  - `_advisory_catalog_inputs` (src/deepreason/bridge/evidence_pack.py) — intra-file-only (2 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-bridge-_advisory_catalog_inputs.txt
  - `_catalog_excerpt` (src/deepreason/bridge/evidence_pack.py) — intra-file-only (5 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-bridge-_catalog_excerpt.txt
  - `_catalog_items` (src/deepreason/bridge/evidence_pack.py) — intra-file-only (2 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-bridge-_catalog_items.txt
  - `_freeze` (src/deepreason/bridge/evidence_pack.py) — intra-file-only (5 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-bridge-_freeze.txt
  - `_validate_formal_seq` (src/deepreason/bridge/evidence_pack.py) — intra-file-only (2 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-bridge-_validate_formal_seq.txt
  - `_BridgeExecutionSnapshot` (src/deepreason/bridge/harness.py) — intra-file-only (5 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-bridge-_BridgeExecutionSnapshot.txt
  - `_snapshot_model_value` (src/deepreason/bridge/harness.py) — intra-file-only (5 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-bridge-_snapshot_model_value.txt
  - `_attention_pack_id` (src/deepreason/bridge/harness.py) — intra-file-only (3 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-bridge-_attention_pack_id.txt
  - `_snapshot_error` (src/deepreason/bridge/harness.py) — intra-file-only (12 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-bridge-_snapshot_error.txt
  - `_load_bridge_execution_snapshot` (src/deepreason/bridge/harness.py) — intra-file-only (3 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-bridge-_load_bridge_execution_snapshot.txt
  - `_write_bridge_execution_snapshot` (src/deepreason/bridge/harness.py) — intra-file-only (2 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-bridge-_write_bridge_execution_snapshot.txt
  - `_find_bridge_execution_snapshot` (src/deepreason/bridge/harness.py) — intra-file-only (2 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-bridge-_find_bridge_execution_snapshot.txt
  - `_transactional_bridge_adapters` (src/deepreason/bridge/harness.py) — intra-file-only (3 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-bridge-_transactional_bridge_adapters.txt
  - `_transactional_v6_manifest_required` (src/deepreason/bridge/harness.py) — intra-file-only (2 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-bridge-_transactional_v6_manifest_required.txt
  - `_transactional_source_terminal_commitment_ref` (src/deepreason/bridge/harness.py) — intra-file-only (2 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-bridge-_transactional_source_terminal_commitment_ref.txt
  - `_assert_snapshot_matches_invocation` (src/deepreason/bridge/harness.py) — intra-file-only (2 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-bridge-_assert_snapshot_matches_invocation.txt
  - `_bound_manifest_digest` (src/deepreason/bridge/harness.py) — intra-file-only (2 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-bridge-_bound_manifest_digest.txt
  - `_bound_scratch_attention_policy` (src/deepreason/bridge/harness.py) — intra-file-only (2 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-bridge-_bound_scratch_attention_policy.txt
  - `_derive_bridge_execution_policy` (src/deepreason/bridge/harness.py) — intra-file-only (3 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-bridge-_derive_bridge_execution_policy.txt
  - `_assert_adapter_matches_retry_lease` (src/deepreason/bridge/harness.py) — intra-file-only (2 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-bridge-_assert_adapter_matches_retry_lease.txt
  - `_terminal_record` (src/deepreason/bridge/harness.py) — intra-file-only (2 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-bridge-_terminal_record.txt
  - `_lexical_handle_kind` (src/deepreason/bridge/ledger.py) — intra-file-only (4 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-bridge-_lexical_handle_kind.txt
  - `_array_schema` (src/deepreason/bridge/ledger.py) — intra-file-only (2 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-bridge-_array_schema.txt
  - `_bind_schema_enum` (src/deepreason/bridge/ledger.py) — intra-file-only (5 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-bridge-_bind_schema_enum.txt
  - `_namespaced_handle` (src/deepreason/bridge/ledger.py) — intra-file-only (2 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-bridge-_namespaced_handle.txt
  - `_coerce_amendment_request` (src/deepreason/bridge/ledger.py) — intra-file-only (3 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-bridge-_coerce_amendment_request.txt
  - `_handle_type` (src/deepreason/bridge/ledger.py) — intra-file-only (12 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-bridge-_handle_type.txt
  - `_fallback_ledger` (src/deepreason/bridge/ledger.py) — intra-file-only (3 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-bridge-_fallback_ledger.txt
  - `_failure_message` (src/deepreason/bridge/ledger.py) — intra-file-only (3 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-bridge-_failure_message.txt
  - `LedgerFrozenRecord` (src/deepreason/bridge/ledger.py) — intra-file-only (7 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-bridge-LedgerFrozenRecord.txt
  - `_coerce_catalog` (src/deepreason/bridge/ledger.py) — intra-file-only (5 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-bridge-_coerce_catalog.txt
  - `LedgerWireModel` (src/deepreason/bridge/ledger.py) — intra-file-only (5 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-bridge-LedgerWireModel.txt
  - `_prior_entry_keys` (src/deepreason/bridge/ledger.py) — intra-file-only (2 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-bridge-_prior_entry_keys.txt
  - `_prior_conflict_keys` (src/deepreason/bridge/ledger.py) — intra-file-only (2 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-bridge-_prior_conflict_keys.txt
  - `_safe_remove` (src/deepreason/bridge/operations.py) — intra-file-only (4 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-bridge-_safe_remove.txt
  - `_safe_read` (src/deepreason/bridge/operations.py) — intra-file-only (3 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-bridge-_safe_read.txt
  - `_sanitized_detail` (src/deepreason/bridge/operations.py) — intra-file-only (2 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-bridge-_sanitized_detail.txt
  - `_ensure_write_target` (src/deepreason/bridge/operations.py) — intra-file-only (5 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-bridge-_ensure_write_target.txt
  - `_make_output` (src/deepreason/bridge/repair.py) — intra-file-only (3 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-bridge-_make_output.txt
  - `_quarantine_span` (src/deepreason/bridge/repair.py) — intra-file-only (6 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-bridge-_quarantine_span.txt
  - `_assert_failed_call_matches_fence` (src/deepreason/bridge/retry.py) — intra-file-only (2 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-bridge-_assert_failed_call_matches_fence.txt
  - `_bounded_materials` (src/deepreason/bridge/review.py) — intra-file-only (2 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-bridge-_bounded_materials.txt
  - `_entry_refs` (src/deepreason/bridge/review.py) — intra-file-only (2 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-bridge-_entry_refs.txt
  - `_entry_for_review` (src/deepreason/bridge/review.py) — intra-file-only (3 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-bridge-_entry_for_review.txt
  - `_semantic_bytes` (src/deepreason/bridge/transactional_adapter.py) — intra-file-only (3 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-bridge-_semantic_bytes.txt
  - `_namespace_for` (src/deepreason/bridge/transactional_adapter.py) — intra-file-only (4 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-bridge-_namespace_for.txt
  - `_context_seeds` (src/deepreason/bridge/transactional_adapter.py) — intra-file-only (3 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-bridge-_context_seeds.txt
  - `_context_items` (src/deepreason/bridge/transactional_adapter.py) — intra-file-only (2 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-bridge-_context_items.txt
  - `_require_durable_model_classification` (src/deepreason/bridge/transactional_adapter.py) — intra-file-only (2 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-bridge-_require_durable_model_classification.txt
  - `_allowed_modes` (src/deepreason/bridge/validate.py) — intra-file-only (2 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-bridge-_allowed_modes.txt
  - `_entry_grounding_findings` (src/deepreason/bridge/validate.py) — intra-file-only (2 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-bridge-_entry_grounding_findings.txt
  - `_validation_records` (src/deepreason/bridge/workflow.py) — intra-file-only (5 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-bridge-_validation_records.txt
  - `_output_records` (src/deepreason/bridge/workflow.py) — intra-file-only (3 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-bridge-_output_records.txt
  - `_review_records` (src/deepreason/bridge/workflow.py) — intra-file-only (2 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-bridge-_review_records.txt
  - `_stable_error_code` (src/deepreason/bridge/workflow.py) — intra-file-only (2 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-bridge-_stable_error_code.txt
  - `_error_calls` (src/deepreason/bridge/workflow.py) — intra-file-only (3 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-bridge-_error_calls.txt
  - `_stage_a_failure_error` (src/deepreason/bridge/workflow.py) — intra-file-only (3 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-bridge-_stage_a_failure_error.txt

### capabilities

  - `_write_markdown` (src/deepreason/capabilities/audit.py) — intra-file-only (5 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-capabilities-_write_markdown.txt
  - `_transition_chains` (src/deepreason/capabilities/audit.py) — intra-file-only (2 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-capabilities-_transition_chains.txt
  - `_bounded_json` (src/deepreason/capabilities/models.py) — intra-file-only (7 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-capabilities-_bounded_json.txt
  - `_IdentifiedCapabilityRecord` (src/deepreason/capabilities/models.py) — intra-file-only (16 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-capabilities-_IdentifiedCapabilityRecord.txt
  - `_PolicyModel` (src/deepreason/capabilities/policy.py) — intra-file-only (10 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-capabilities-_PolicyModel.txt
  - `_finite_json` (src/deepreason/capabilities/policy.py) — intra-file-only (4 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-capabilities-_finite_json.txt
  - `_host` (src/deepreason/capabilities/research.py) — intra-file-only (2 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-capabilities-_host.txt

### capture

  - `_conjecture_stream` (src/deepreason/capture/detection.py) — intra-file-only (4 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-capture-_conjecture_stream.txt
  - `_mean_pairwise` (src/deepreason/capture/detection.py) — intra-file-only (3 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-capture-_mean_pairwise.txt
  - `_with_cross_examiner` (src/deepreason/capture/schools.py) — intra-file-only (3 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-capture-_with_cross_examiner.txt
  - `SchoolPopulationRegistration` (src/deepreason/capture/schools.py) — intra-file-only (5 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-capture-SchoolPopulationRegistration.txt
  - `_policy_content` (src/deepreason/capture/schools.py) — intra-file-only (3 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-capture-_policy_content.txt

### cli

  - `_add_page_arguments` (src/deepreason/cli/bridge.py) — intra-file-only (3 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-cli-_add_page_arguments.txt
  - `_safe_human` (src/deepreason/cli/bridge.py) — intra-file-only (12 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-cli-_safe_human.txt
  - `_build_intent` (src/deepreason/cli/bridge.py) — intra-file-only (2 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-cli-_build_intent.txt
  - `_grounding_source_count` (src/deepreason/cli/bridge.py) — intra-file-only (2 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-cli-_grounding_source_count.txt
  - `_render_inspect` (src/deepreason/cli/bridge.py) — intra-file-only (2 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-cli-_render_inspect.txt
  - `_atomic_write_report` (src/deepreason/cli/doctor.py) — intra-file-only (2 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-cli-_atomic_write_report.txt
  - `_DuplicateDoctorReportKey` (src/deepreason/cli/doctor.py) — intra-file-only (3 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-cli-_DuplicateDoctorReportKey.txt
  - `_read_production_contract_report` (src/deepreason/cli/doctor.py) — intra-file-only (2 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-cli-_read_production_contract_report.txt
  - `_release_gate` (src/deepreason/cli/doctor.py) — intra-file-only (4 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-cli-_release_gate.txt
  - `_pair_id` (src/deepreason/cli/doctor.py) — intra-file-only (2 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-cli-_pair_id.txt
  - `_behavioral_contract_grant` (src/deepreason/cli/doctor.py) — intra-file-only (2 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-cli-_behavioral_contract_grant.txt
  - `_is_alias_failure` (src/deepreason/cli/doctor.py) — intra-file-only (4 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-cli-_is_alias_failure.txt
  - `_DoctorRecord` (src/deepreason/cli/doctor.py) — intra-file-only (6 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-cli-_DoctorRecord.txt
  - `_production_bridge_ledger_probe` (src/deepreason/cli/doctor.py) — intra-file-only (3 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-cli-_production_bridge_ledger_probe.txt
  - `_production_bridge_composition_probe` (src/deepreason/cli/doctor.py) — intra-file-only (3 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-cli-_production_bridge_composition_probe.txt
  - `_production_grounding_probe` (src/deepreason/cli/doctor.py) — intra-file-only (3 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-cli-_production_grounding_probe.txt
  - `_production_scratch_probe` (src/deepreason/cli/doctor.py) — intra-file-only (2 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-cli-_production_scratch_probe.txt
  - `_validate_production_contract_request_envelopes` (src/deepreason/cli/doctor.py) — intra-file-only (4 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-cli-_validate_production_contract_request_envelopes.txt
  - `_production_qualification_evidence_sha256` (src/deepreason/cli/doctor.py) — intra-file-only (2 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-cli-_production_qualification_evidence_sha256.txt
  - `_read_problem_file` (src/deepreason/cli/main.py) — intra-file-only (10 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-cli-_read_problem_file.txt
  - `_cmd_input` (src/deepreason/cli/main.py) — intra-file-only (2 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-cli-_cmd_input.txt
  - `_doctor_role_seats` (src/deepreason/cli/main.py) — intra-file-only (2 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-cli-_doctor_role_seats.txt
  - `_cmd_doctor` (src/deepreason/cli/main.py) — intra-file-only (2 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-cli-_cmd_doctor.txt
  - `_load_problem_file` (src/deepreason/cli/main.py) — intra-file-only (2 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-cli-_load_problem_file.txt
  - `_qualify_one_profile` (src/deepreason/cli/main.py) — intra-file-only (3 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-cli-_qualify_one_profile.txt
  - `_print_qualify_failure` (src/deepreason/cli/main.py) — intra-file-only (3 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-cli-_print_qualify_failure.txt
  - `_cmd_explain_error` (src/deepreason/cli/main.py) — intra-file-only (2 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-cli-_cmd_explain_error.txt
  - `_load_intake_file` (src/deepreason/cli/main.py) — intra-file-only (2 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-cli-_load_intake_file.txt
  - `_cmd_validate_intake` (src/deepreason/cli/main.py) — intra-file-only (2 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-cli-_cmd_validate_intake.txt
  - `_print_qualify_headline` (src/deepreason/cli/main.py) — intra-file-only (4 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-cli-_print_qualify_headline.txt
  - `_cmd_qualify` (src/deepreason/cli/main.py) — intra-file-only (3 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-cli-_cmd_qualify.txt
  - `_cmd_reason_shallow` (src/deepreason/cli/main.py) — intra-file-only (2 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-cli-_cmd_reason_shallow.txt
  - `_cmd_admit` (src/deepreason/cli/main.py) — intra-file-only (2 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-cli-_cmd_admit.txt
  - `_reasoning_disabled_refusal` (src/deepreason/cli/main.py) — intra-file-only (3 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-cli-_reasoning_disabled_refusal.txt
  - `_cmd_skills` (src/deepreason/cli/main.py) — intra-file-only (2 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-cli-_cmd_skills.txt
  - `_cmd_distill` (src/deepreason/cli/main.py) — intra-file-only (2 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-cli-_cmd_distill.txt
  - `_cmd_brain` (src/deepreason/cli/main.py) — intra-file-only (2 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-cli-_cmd_brain.txt
  - `_cmd_amend` (src/deepreason/cli/main.py) — intra-file-only (2 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-cli-_cmd_amend.txt
  - `_cmd_continue` (src/deepreason/cli/main.py) — intra-file-only (2 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-cli-_cmd_continue.txt
  - `_cmd_cancel` (src/deepreason/cli/main.py) — intra-file-only (2 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-cli-_cmd_cancel.txt
  - `_cmd_check_proof` (src/deepreason/cli/main.py) — TRUE-CANDIDATE (0 refs anywhere) — proof/dead-cli-_cmd_check_proof.txt
  - `_bind_cli_manifest` (src/deepreason/cli/main.py) — intra-file-only (3 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-cli-_bind_cli_manifest.txt
  - `_cmd_code` (src/deepreason/cli/main.py) — TRUE-CANDIDATE (0 refs anywhere) — proof/dead-cli-_cmd_code.txt
  - `_cmd_simulate` (src/deepreason/cli/main.py) — TRUE-CANDIDATE (0 refs anywhere) — proof/dead-cli-_cmd_simulate.txt
  - `_require_v6_workload_match` (src/deepreason/cli/main.py) — intra-file-only (2 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-cli-_require_v6_workload_match.txt
  - `_short_id` (src/deepreason/cli/scratch.py) — intra-file-only (3 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-cli-_short_id.txt
  - `_label` (src/deepreason/cli/scratch.py) — intra-file-only (15 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-cli-_label.txt
  - `_query_label` (src/deepreason/cli/scratch.py) — intra-file-only (6 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-cli-_query_label.txt
  - `_read_explicit_file` (src/deepreason/cli/scratch.py) — intra-file-only (2 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-cli-_read_explicit_file.txt
  - `_read_stdin` (src/deepreason/cli/scratch.py) — intra-file-only (2 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-cli-_read_stdin.txt
  - `_block_body` (src/deepreason/cli/scratch.py) — intra-file-only (3 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-cli-_block_body.txt
  - `_writable_service` (src/deepreason/cli/scratch.py) — intra-file-only (6 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-cli-_writable_service.txt
  - `_query_sequence` (src/deepreason/cli/scratch.py) — intra-file-only (5 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-cli-_query_sequence.txt
  - `_emit` (src/deepreason/cli/scratch.py) — intra-file-only (2 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-cli-_emit.txt
  - `_error_payload` (src/deepreason/cli/scratch.py) — intra-file-only (2 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-cli-_error_payload.txt
  - `_emit_error` (src/deepreason/cli/scratch.py) — intra-file-only (2 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-cli-_emit_error.txt
  - `_add` (src/deepreason/cli/scratch.py) — intra-file-only (2 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-cli-_add.txt
  - `_revise` (src/deepreason/cli/scratch.py) — intra-file-only (2 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-cli-_revise.txt
  - `_retire_link` (src/deepreason/cli/scratch.py) — intra-file-only (2 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-cli-_retire_link.txt
  - `_cluster` (src/deepreason/cli/scratch.py) — intra-file-only (2 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-cli-_cluster.txt
  - `_add_json` (src/deepreason/cli/scratch.py) — intra-file-only (15 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-cli-_add_json.txt
  - `_add_limit` (src/deepreason/cli/scratch.py) — intra-file-only (9 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-cli-_add_limit.txt
  - `_dormant_threshold` (src/deepreason/cli/scratch.py) — intra-file-only (2 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-cli-_dormant_threshold.txt
  - `_add_history` (src/deepreason/cli/scratch.py) — intra-file-only (9 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-cli-_add_history.txt
  - `_dormant` (src/deepreason/cli/scratch.py) — intra-file-only (2 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-cli-_dormant.txt
  - `_underexposed` (src/deepreason/cli/scratch.py) — intra-file-only (2 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-cli-_underexposed.txt
  - `_sample` (src/deepreason/cli/scratch.py) — intra-file-only (2 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-cli-_sample.txt
  - `_coverage` (src/deepreason/cli/scratch.py) — intra-file-only (2 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-cli-_coverage.txt
  - `_add_content_input` (src/deepreason/cli/scratch.py) — intra-file-only (3 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-cli-_add_content_input.txt

### compat_eval.py

  - `_write_running_record` (src/deepreason/compat_eval.py) — intra-file-only (2 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-compat_eval-_write_running_record.txt
  - `expected_trial_keys` (src/deepreason/compat_eval.py) — intra-file-only (2 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-compat_eval-expected_trial_keys.txt
  - `_stage_rows` (src/deepreason/compat_eval.py) — intra-file-only (2 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-compat_eval-_stage_rows.txt
  - `_terminal_summary` (src/deepreason/compat_eval.py) — intra-file-only (2 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-compat_eval-_terminal_summary.txt
  - `_terminal_summary_complete` (src/deepreason/compat_eval.py) — intra-file-only (2 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-compat_eval-_terminal_summary_complete.txt
  - `_quality_counts` (src/deepreason/compat_eval.py) — intra-file-only (2 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-compat_eval-_quality_counts.txt
  - `_terminal_records` (src/deepreason/compat_eval.py) — intra-file-only (2 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-compat_eval-_terminal_records.txt
  - `_safe_rate` (src/deepreason/compat_eval.py) — intra-file-only (14 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-compat_eval-_safe_rate.txt
  - `_frontier_quality` (src/deepreason/compat_eval.py) — intra-file-only (2 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-compat_eval-_frontier_quality.txt

### conjecture_turn.py

  - `_TurnRecord` (src/deepreason/conjecture_turn.py) — intra-file-only (10 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-conjecture_turn-_TurnRecord.txt

### easy.py

  - `base_dir` (src/deepreason/easy.py) — intra-file-only (3 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-easy-base_dir.txt
  - `_stored_credential_present` (src/deepreason/easy.py) — intra-file-only (3 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-easy-_stored_credential_present.txt
  - `_preparation_required` (src/deepreason/easy.py) — intra-file-only (5 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-easy-_preparation_required.txt
  - `_positive_capacity` (src/deepreason/easy.py) — intra-file-only (7 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-easy-_positive_capacity.txt
  - `_stage_gate` (src/deepreason/easy.py) — intra-file-only (4 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-easy-_stage_gate.txt
  - `_page_text` (src/deepreason/easy.py) — intra-file-only (2 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-easy-_page_text.txt
  - `_slug` (src/deepreason/easy.py) — TRUE-CANDIDATE (0 refs anywhere) — proof/dead-easy-_slug.txt
  - `_fresh` (src/deepreason/easy.py) — TRUE-CANDIDATE (0 refs anywhere) — proof/dead-easy-_fresh.txt
  - `_echo` (src/deepreason/easy.py) — intra-file-only (2 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-easy-_echo.txt
  - `_first_line` (src/deepreason/easy.py) — TRUE-CANDIDATE (0 refs anywhere) — proof/dead-easy-_first_line.txt

### error_catalog.py

  - `ErrorCatalogEntry` (src/deepreason/error_catalog.py) — intra-file-only (5 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-error_catalog-ErrorCatalogEntry.txt

### evidence

  - `_whitespace_folded` (src/deepreason/evidence/citations.py) — intra-file-only (3 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-evidence-_whitespace_folded.txt
  - `_bounded_prefix` (src/deepreason/evidence/dossier.py) — intra-file-only (2 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-evidence-_bounded_prefix.txt
  - `_InputRecord` (src/deepreason/evidence/models.py) — intra-file-only (16 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-evidence-_InputRecord.txt
  - `_read_regular` (src/deepreason/evidence/state.py) — intra-file-only (5 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-evidence-_read_regular.txt
  - `_read_digest` (src/deepreason/evidence/state.py) — intra-file-only (4 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-evidence-_read_digest.txt
  - `_input_lock` (src/deepreason/evidence/state.py) — intra-file-only (2 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-evidence-_input_lock.txt
  - `_bind_record` (src/deepreason/evidence/state.py) — intra-file-only (3 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-evidence-_bind_record.txt
  - `_resolve_record_path` (src/deepreason/evidence/state.py) — intra-file-only (3 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-evidence-_resolve_record_path.txt

### experiments

  - `_command_manifest_paths` (src/deepreason/experiments/campaign.py) — intra-file-only (2 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-experiments-_command_manifest_paths.txt
  - `_launch_manifest_paths` (src/deepreason/experiments/campaign.py) — intra-file-only (2 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-experiments-_launch_manifest_paths.txt
  - `_load_launch_manifests` (src/deepreason/experiments/campaign.py) — intra-file-only (2 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-experiments-_load_launch_manifests.txt
  - `_bound_manifest_authority_findings` (src/deepreason/experiments/campaign.py) — intra-file-only (2 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-experiments-_bound_manifest_authority_findings.txt
  - `_strict_report_json` (src/deepreason/experiments/campaign.py) — intra-file-only (2 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-experiments-_strict_report_json.txt
  - `_verify_qualification_report` (src/deepreason/experiments/campaign.py) — intra-file-only (2 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-experiments-_verify_qualification_report.txt
  - `_new_qualification_gate` (src/deepreason/experiments/campaign.py) — intra-file-only (2 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-experiments-_new_qualification_gate.txt
  - `_foreign_root_scan_failure` (src/deepreason/experiments/campaign.py) — intra-file-only (2 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-experiments-_foreign_root_scan_failure.txt
  - `_decoded_json_string_values` (src/deepreason/experiments/campaign.py) — intra-file-only (2 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-experiments-_decoded_json_string_values.txt
  - `_normalized_log_path` (src/deepreason/experiments/campaign.py) — intra-file-only (2 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-experiments-_normalized_log_path.txt
  - `_path_is_at_or_below` (src/deepreason/experiments/campaign.py) — intra-file-only (2 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-experiments-_path_is_at_or_below.txt
  - `_foreign_root_path_findings` (src/deepreason/experiments/campaign.py) — intra-file-only (3 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-experiments-_foreign_root_path_findings.txt
  - `_apply_findings` (src/deepreason/experiments/campaign.py) — intra-file-only (5 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-experiments-_apply_findings.txt
  - `_root_manifest_schema_version` (src/deepreason/experiments/campaign.py) — intra-file-only (2 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-experiments-_root_manifest_schema_version.txt
  - `_canonical_bridge_eligible` (src/deepreason/experiments/campaign.py) — intra-file-only (2 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-experiments-_canonical_bridge_eligible.txt
  - `_default_verifier` (src/deepreason/experiments/campaign.py) — intra-file-only (3 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-experiments-_default_verifier.txt
  - `_normalized_campaign_root` (src/deepreason/experiments/campaign.py) — intra-file-only (4 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-experiments-_normalized_campaign_root.txt
  - `_campaign_roots_overlap` (src/deepreason/experiments/campaign.py) — intra-file-only (2 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-experiments-_campaign_roots_overlap.txt
  - `_validate_campaign_plan` (src/deepreason/experiments/campaign.py) — intra-file-only (3 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-experiments-_validate_campaign_plan.txt
  - `CommandOutcome` (src/deepreason/experiments/campaign.py) — intra-file-only (8 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-experiments-CommandOutcome.txt
  - `_subprocess_runner` (src/deepreason/experiments/campaign.py) — intra-file-only (2 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-experiments-_subprocess_runner.txt
  - `CampaignRunRecord` (src/deepreason/experiments/campaign.py) — intra-file-only (4 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-experiments-CampaignRunRecord.txt
  - `CampaignWaveRecord` (src/deepreason/experiments/campaign.py) — intra-file-only (5 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-experiments-CampaignWaveRecord.txt
  - `QualificationReportBinding` (src/deepreason/experiments/campaign.py) — intra-file-only (5 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-experiments-QualificationReportBinding.txt
  - `RunManifestAuthorityBinding` (src/deepreason/experiments/campaign.py) — intra-file-only (7 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-experiments-RunManifestAuthorityBinding.txt
  - `CampaignQualificationGate` (src/deepreason/experiments/campaign.py) — intra-file-only (4 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-experiments-CampaignQualificationGate.txt
  - `_vote` (src/deepreason/experiments/criticism_voting.py) — intra-file-only (4 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-experiments-_vote.txt
  - `_post_weights` (src/deepreason/experiments/criticism_voting.py) — intra-file-only (4 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-experiments-_post_weights.txt
  - `realized_outcome_before` (src/deepreason/experiments/criticism_voting.py) — intra-file-only (2 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-experiments-realized_outcome_before.txt
  - `realized_outcome_after` (src/deepreason/experiments/criticism_voting.py) — intra-file-only (2 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-experiments-realized_outcome_after.txt
  - `flag_vector_prob` (src/deepreason/experiments/criticism_voting.py) — intra-file-only (2 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-experiments-flag_vector_prob.txt
  - `sample_flags` (src/deepreason/experiments/criticism_voting.py) — intra-file-only (2 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-experiments-sample_flags.txt
  - `ExactMetrics` (src/deepreason/experiments/criticism_voting.py) — intra-file-only (6 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-experiments-ExactMetrics.txt
  - `_count_branches` (src/deepreason/experiments/criticism_voting.py) — intra-file-only (2 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-experiments-_count_branches.txt
  - `_accumulate` (src/deepreason/experiments/criticism_voting.py) — intra-file-only (2 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-experiments-_accumulate.txt
  - `_exact_by_counts` (src/deepreason/experiments/criticism_voting.py) — intra-file-only (2 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-experiments-_exact_by_counts.txt
  - `_frac` (src/deepreason/experiments/criticism_voting.py) — intra-file-only (2 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-experiments-_frac.txt
  - `_exact_by_full_enumeration` (src/deepreason/experiments/criticism_voting.py) — intra-file-only (2 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-experiments-_exact_by_full_enumeration.txt
  - `_check_prob` (src/deepreason/experiments/criticism_voting.py) — intra-file-only (11 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-experiments-_check_prob.txt
  - `ordinary_history_render` (src/deepreason/experiments/jolt_tsp.py) — intra-file-only (2 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-experiments-ordinary_history_render.txt
  - `matrix_render` (src/deepreason/experiments/jolt_tsp.py) — intra-file-only (2 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-experiments-matrix_render.txt
  - `incumbent_edges_render` (src/deepreason/experiments/jolt_tsp.py) — intra-file-only (2 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-experiments-incumbent_edges_render.txt
  - `recent_edge_differences` (src/deepreason/experiments/jolt_tsp.py) — intra-file-only (2 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-experiments-recent_edge_differences.txt
  - `instance_ids` (src/deepreason/experiments/jolt_tsp.py) — intra-file-only (3 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-experiments-instance_ids.txt
  - `distance_matrix` (src/deepreason/experiments/jolt_tsp.py) — intra-file-only (4 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-experiments-distance_matrix.txt
  - `validate_tour` (src/deepreason/experiments/jolt_tsp.py) — intra-file-only (2 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-experiments-validate_tour.txt

### findings.py

  - `_claim_text` (src/deepreason/findings.py) — intra-file-only (3 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-findings-_claim_text.txt

### imports.py

  - `_integrity_matches` (src/deepreason/imports.py) — intra-file-only (3 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-imports-_integrity_matches.txt
  - `_archive_manifest` (src/deepreason/imports.py) — intra-file-only (2 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-imports-_archive_manifest.txt
  - `_safe_extract` (src/deepreason/imports.py) — intra-file-only (2 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-imports-_safe_extract.txt
  - `BundleResult` (src/deepreason/imports.py) — intra-file-only (3 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-imports-BundleResult.txt
  - `_exact_ref` (src/deepreason/imports.py) — intra-file-only (4 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-imports-_exact_ref.txt
  - `_artifact_bytes` (src/deepreason/imports.py) — intra-file-only (5 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-imports-_artifact_bytes.txt

### indexes.py

  - `_generation_key` (src/deepreason/indexes.py) — intra-file-only (4 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-indexes-_generation_key.txt
  - `_event_rows` (src/deepreason/indexes.py) — intra-file-only (2 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-indexes-_event_rows.txt

### informal

  - `_standards_for` (src/deepreason/informal/appellate.py) — intra-file-only (2 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-informal-_standards_for.txt
  - `_log_calls` (src/deepreason/informal/audits.py) — intra-file-only (5 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-informal-_log_calls.txt
  - `_rubric_warrants` (src/deepreason/informal/audits.py) — intra-file-only (3 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-informal-_rubric_warrants.txt
  - `_audit_warrant` (src/deepreason/informal/audits.py) — intra-file-only (3 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-informal-_audit_warrant.txt
  - `_ensemble_call` (src/deepreason/informal/audits.py) — intra-file-only (4 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-informal-_ensemble_call.txt
  - `_judge_exchange` (src/deepreason/informal/audits.py) — intra-file-only (3 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-informal-_judge_exchange.txt
  - `_body` (src/deepreason/informal/standards.py) — intra-file-only (4 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-informal-_body.txt
  - `_record_pairwise_observation` (src/deepreason/informal/trial.py) — intra-file-only (2 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-informal-_record_pairwise_observation.txt
  - `_advisory_pairwise_result` (src/deepreason/informal/trial.py) — intra-file-only (6 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-informal-_advisory_pairwise_result.txt
  - `_pairwise_steps` (src/deepreason/informal/trial.py) — intra-file-only (2 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-informal-_pairwise_steps.txt
  - `_coerce_trial_authority` (src/deepreason/informal/trial.py) — intra-file-only (4 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-informal-_coerce_trial_authority.txt
  - `_record_trial_observation` (src/deepreason/informal/trial.py) — intra-file-only (2 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-informal-_record_trial_observation.txt
  - `_advisory_trial_result` (src/deepreason/informal/trial.py) — intra-file-only (8 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-informal-_advisory_trial_result.txt
  - `_v6_trial_manifest` (src/deepreason/informal/trial.py) — intra-file-only (2 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-informal-_v6_trial_manifest.txt
  - `_trial_steps` (src/deepreason/informal/trial.py) — intra-file-only (2 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-informal-_trial_steps.txt
  - `_paraphrase_screen` (src/deepreason/informal/trial.py) — intra-file-only (3 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-informal-_paraphrase_screen.txt

### invariants.py

  - `_expected_call_outcome` (src/deepreason/invariants.py) — intra-file-only (2 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-invariants-_expected_call_outcome.txt
  - `_controller_v3_history` (src/deepreason/invariants.py) — intra-file-only (2 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-invariants-_controller_v3_history.txt
  - `ExpectedCallOutcome` (src/deepreason/invariants.py) — intra-file-only (12 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-invariants-ExpectedCallOutcome.txt
  - `_is_typed_bridge_failure` (src/deepreason/invariants.py) — intra-file-only (2 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-invariants-_is_typed_bridge_failure.txt
  - `_legacy_bridge_failure_call_seqs` (src/deepreason/invariants.py) — intra-file-only (2 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-invariants-_legacy_bridge_failure_call_seqs.txt
  - `_amendment_epochs` (src/deepreason/invariants.py) — intra-file-only (2 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-invariants-_amendment_epochs.txt
  - `_epoch_input_for_dossier` (src/deepreason/invariants.py) — intra-file-only (2 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-invariants-_epoch_input_for_dossier.txt

### jolts.py

  - `suppressible_lineage_exemplars` (src/deepreason/jolts.py) — TRUE-CANDIDATE (0 refs anywhere) — proof/dead-jolts-suppressible_lineage_exemplars.txt
  - `validate_action_against_state` (src/deepreason/jolts.py) — intra-file-only (2 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-jolts-validate_action_against_state.txt
  - `BranchBudget` (src/deepreason/jolts.py) — intra-file-only (3 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-jolts-BranchBudget.txt
  - `BranchSpec` (src/deepreason/jolts.py) — intra-file-only (3 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-jolts-BranchSpec.txt
  - `MatchedBranchPlan` (src/deepreason/jolts.py) — intra-file-only (4 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-jolts-MatchedBranchPlan.txt
  - `_file_digest` (src/deepreason/jolts.py) — intra-file-only (5 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-jolts-_file_digest.txt
  - `_stable_order` (src/deepreason/jolts.py) — intra-file-only (2 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-jolts-_stable_order.txt
  - `PilotPreflightReceipt` (src/deepreason/jolts.py) — intra-file-only (3 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-jolts-PilotPreflightReceipt.txt
  - `_mode_value` (src/deepreason/jolts.py) — intra-file-only (2 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-jolts-_mode_value.txt
  - `re_full_digest` (src/deepreason/jolts.py) — intra-file-only (3 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-jolts-re_full_digest.txt

### llm

  - `ProbeCase` (src/deepreason/llm/capabilities.py) — intra-file-only (11 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-llm-ProbeCase.txt
  - `deterministic_probe_cases` (src/deepreason/llm/capabilities.py) — intra-file-only (2 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-llm-deterministic_probe_cases.txt
  - `_validated_endpoint` (src/deepreason/llm/capabilities.py) — intra-file-only (6 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-llm-_validated_endpoint.txt
  - `ProbeEndpoint` (src/deepreason/llm/capabilities.py) — intra-file-only (2 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-llm-ProbeEndpoint.txt
  - `PropertyProposal` (src/deepreason/llm/contracts.py) — intra-file-only (2 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-llm-PropertyProposal.txt
  - `EncoderTestCase` (src/deepreason/llm/contracts.py) — intra-file-only (2 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-llm-EncoderTestCase.txt
  - `ThesisSection` (src/deepreason/llm/contracts.py) — intra-file-only (3 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-llm-ThesisSection.txt
  - `ThesisRival` (src/deepreason/llm/contracts.py) — intra-file-only (2 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-llm-ThesisRival.txt
  - `_library_versions` (src/deepreason/llm/embedder.py) — intra-file-only (2 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-llm-_library_versions.txt
  - `_sentinel_hash` (src/deepreason/llm/embedder.py) — intra-file-only (3 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-llm-_sentinel_hash.txt
  - `_TransientBody` (src/deepreason/llm/endpoints.py) — intra-file-only (4 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-llm-_TransientBody.txt
  - `_pick_primary` (src/deepreason/llm/endpoints.py) — intra-file-only (2 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-llm-_pick_primary.txt
  - `_pick_alt` (src/deepreason/llm/endpoints.py) — intra-file-only (2 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-llm-_pick_alt.txt
  - `_json_pointer_part` (src/deepreason/llm/firewall.py) — intra-file-only (2 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-llm-_json_pointer_part.txt
  - `_strings_in` (src/deepreason/llm/firewall.py) — intra-file-only (4 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-llm-_strings_in.txt
  - `_control_value_strings` (src/deepreason/llm/firewall.py) — intra-file-only (4 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-llm-_control_value_strings.txt
  - `_sanitize_for_repair` (src/deepreason/llm/firewall.py) — intra-file-only (4 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-llm-_sanitize_for_repair.txt
  - `_redact_strings` (src/deepreason/llm/firewall.py) — intra-file-only (4 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-llm-_redact_strings.txt
  - `_lease_families` (src/deepreason/llm/firewall.py) — intra-file-only (2 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-llm-_lease_families.txt
  - `_lineage_foundation` (src/deepreason/llm/packs.py) — intra-file-only (2 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-llm-_lineage_foundation.txt
  - `_carries_execution_oracle` (src/deepreason/llm/packs.py) — intra-file-only (3 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-llm-_carries_execution_oracle.txt
  - `_execution_spec_lines` (src/deepreason/llm/packs.py) — intra-file-only (4 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-llm-_execution_spec_lines.txt
  - `_pack_section` (src/deepreason/llm/packs.py) — intra-file-only (25 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-llm-_pack_section.txt
  - `_allocate_sections` (src/deepreason/llm/packs.py) — intra-file-only (3 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-llm-_allocate_sections.txt
  - `_document_excerpt` (src/deepreason/llm/packs.py) — TRUE-CANDIDATE (0 refs anywhere) — proof/dead-llm-_document_excerpt.txt
  - `alias_references` (src/deepreason/llm/packs.py) — TRUE-CANDIDATE (0 refs anywhere) — proof/dead-llm-alias_references.txt
  - `_simulation_contract_note` (src/deepreason/llm/packs.py) — intra-file-only (2 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-llm-_simulation_contract_note.txt
  - `_problem_context` (src/deepreason/llm/packs.py) — intra-file-only (3 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-llm-_problem_context.txt
  - `_active_property_claims` (src/deepreason/llm/packs.py) — intra-file-only (2 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-llm-_active_property_claims.txt
  - `_deepseek_reasoning` (src/deepreason/llm/providers.py) — intra-file-only (2 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-llm-_deepseek_reasoning.txt
  - `_openai_reasoning` (src/deepreason/llm/providers.py) — intra-file-only (2 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-llm-_openai_reasoning.txt
  - `_ollama_reasoning` (src/deepreason/llm/providers.py) — intra-file-only (2 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-llm-_ollama_reasoning.txt
  - `_no_reasoning_knob` (src/deepreason/llm/providers.py) — intra-file-only (4 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-llm-_no_reasoning_knob.txt
  - `_received_for_diagnostic` (src/deepreason/llm/repair.py) — intra-file-only (2 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-llm-_received_for_diagnostic.txt
  - `_allowed_at_pointer` (src/deepreason/llm/repair.py) — intra-file-only (4 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-llm-_allowed_at_pointer.txt
  - `patch_repair_prompt` (src/deepreason/llm/repair.py) — intra-file-only (2 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-llm-patch_repair_prompt.txt
  - `whole_object_repair_prompt` (src/deepreason/llm/repair.py) — intra-file-only (3 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-llm-whole_object_repair_prompt.txt
  - `subtree_repair_prompt` (src/deepreason/llm/repair.py) — intra-file-only (2 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-llm-subtree_repair_prompt.txt
  - `V6RepairTurn` (src/deepreason/llm/repair.py) — intra-file-only (8 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-llm-V6RepairTurn.txt
  - `FrozenSubtreeHashV1` (src/deepreason/llm/repair.py) — intra-file-only (8 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-llm-FrozenSubtreeHashV1.txt
  - `RepairDiagnostic` (src/deepreason/llm/repair.py) — intra-file-only (16 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-llm-RepairDiagnostic.txt
  - `ParsedJSON` (src/deepreason/llm/repair.py) — intra-file-only (6 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-llm-ParsedJSON.txt
  - `RepairTurn` (src/deepreason/llm/repair.py) — intra-file-only (8 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-llm-RepairTurn.txt
  - `strip_json_fence` (src/deepreason/llm/repair.py) — intra-file-only (2 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-llm-strip_json_fence.txt
  - `_contains_json_value` (src/deepreason/llm/repair.py) — intra-file-only (2 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-llm-_contains_json_value.txt
  - `_sole_fenced_json_value` (src/deepreason/llm/repair.py) — intra-file-only (2 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-llm-_sole_fenced_json_value.txt
  - `_pointer_token` (src/deepreason/llm/repair.py) — intra-file-only (2 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-llm-_pointer_token.txt
  - `json_pointer` (src/deepreason/llm/repair.py) — intra-file-only (13 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-llm-json_pointer.txt
  - `_unescape_pointer_token` (src/deepreason/llm/repair.py) — intra-file-only (2 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-llm-_unescape_pointer_token.txt
  - `pointer_parts` (src/deepreason/llm/repair.py) — intra-file-only (8 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-llm-pointer_parts.txt
  - `pointer_get` (src/deepreason/llm/repair.py) — intra-file-only (7 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-llm-pointer_get.txt
  - `_subtree_hash` (src/deepreason/llm/repair.py) — intra-file-only (7 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-llm-_subtree_hash.txt
  - `_frozen_subtree_hashes` (src/deepreason/llm/repair.py) — intra-file-only (2 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-llm-_frozen_subtree_hashes.txt
  - `_verify_repair_envelope_baseline` (src/deepreason/llm/repair.py) — intra-file-only (2 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-llm-_verify_repair_envelope_baseline.txt
  - `_patch_parent` (src/deepreason/llm/repair.py) — intra-file-only (2 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-llm-_patch_parent.txt
  - `_json_differences` (src/deepreason/llm/repair.py) — intra-file-only (4 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-llm-_json_differences.txt
  - `enforce_repair_subtree` (src/deepreason/llm/repair.py) — intra-file-only (3 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-llm-enforce_repair_subtree.txt
  - `_resolve_schema_node` (src/deepreason/llm/repair.py) — intra-file-only (5 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-llm-_resolve_schema_node.txt
  - `_schema_at` (src/deepreason/llm/repair.py) — intra-file-only (3 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-llm-_schema_at.txt
  - `_scratch_handle_kind` (src/deepreason/llm/repair.py) — intra-file-only (2 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-llm-_scratch_handle_kind.txt
  - `_handle_fields_from_error` (src/deepreason/llm/repair.py) — intra-file-only (3 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-llm-_handle_fields_from_error.txt
  - `_scratch_reference_guidance` (src/deepreason/llm/repair.py) — intra-file-only (3 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-llm-_scratch_reference_guidance.txt
  - `CompactConjecturer` (src/deepreason/llm/wire.py) — intra-file-only (3 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-llm-CompactConjecturer.txt
  - `ReferenceFreeConjectureCandidate` (src/deepreason/llm/wire.py) — intra-file-only (2 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-llm-ReferenceFreeConjectureCandidate.txt
  - `ReferenceFreeConjecturer` (src/deepreason/llm/wire.py) — intra-file-only (3 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-llm-ReferenceFreeConjecturer.txt
  - `ReasoningConjecturerWireContract` (src/deepreason/llm/wire.py) — intra-file-only (2 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-llm-ReasoningConjecturerWireContract.txt
  - `SimulationParameterSetWireV1` (src/deepreason/llm/wire.py) — intra-file-only (2 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-llm-SimulationParameterSetWireV1.txt
  - `ConjecturerTurnWireV5` (src/deepreason/llm/wire.py) — intra-file-only (3 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-llm-ConjecturerTurnWireV5.txt
  - `ReasoningConjecturerTurnWireV5` (src/deepreason/llm/wire.py) — intra-file-only (3 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-llm-ReasoningConjecturerTurnWireV5.txt
  - `_concrete_options` (src/deepreason/llm/wire.py) — intra-file-only (7 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-llm-_concrete_options.txt
  - `CompactCritic` (src/deepreason/llm/wire.py) — intra-file-only (3 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-llm-CompactCritic.txt
  - `_renders_as` (src/deepreason/llm/wire.py) — intra-file-only (5 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-llm-_renders_as.txt
  - `ResponseClause` (src/deepreason/llm/wire.py) — intra-file-only (2 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-llm-ResponseClause.txt
  - `CompactDefender` (src/deepreason/llm/wire.py) — intra-file-only (3 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-llm-CompactDefender.txt
  - `CompactJudge` (src/deepreason/llm/wire.py) — intra-file-only (3 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-llm-CompactJudge.txt
  - `CompactPairwiseJudge` (src/deepreason/llm/wire.py) — intra-file-only (3 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-llm-CompactPairwiseJudge.txt
  - `CompactEdit` (src/deepreason/llm/wire.py) — intra-file-only (2 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-llm-CompactEdit.txt
  - `CompactVariator` (src/deepreason/llm/wire.py) — intra-file-only (3 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-llm-CompactVariator.txt
  - `CompactSynthesizer` (src/deepreason/llm/wire.py) — intra-file-only (3 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-llm-CompactSynthesizer.txt
  - `_without_property` (src/deepreason/llm/wire.py) — intra-file-only (4 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-llm-_without_property.txt
  - `outcome_shape_schema` (src/deepreason/llm/wire.py) — intra-file-only (4 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-llm-outcome_shape_schema.txt
  - `_clause_branch` (src/deepreason/llm/wire.py) — intra-file-only (3 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-llm-_clause_branch.txt
  - `_declared_enum` (src/deepreason/llm/wire.py) — intra-file-only (2 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-llm-_declared_enum.txt
  - `_clause_condition` (src/deepreason/llm/wire.py) — intra-file-only (2 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-llm-_clause_condition.txt
  - `_clause_consequent` (src/deepreason/llm/wire.py) — intra-file-only (2 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-llm-_clause_consequent.txt
  - `_ref_users` (src/deepreason/llm/wire.py) — intra-file-only (4 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-llm-_ref_users.txt
  - `_branch_is_unsatisfiable` (src/deepreason/llm/wire.py) — intra-file-only (2 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-llm-_branch_is_unsatisfiable.txt
  - `_consequent_groups` (src/deepreason/llm/wire.py) — intra-file-only (2 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-llm-_consequent_groups.txt
  - `_reject_control_fields` (src/deepreason/llm/wire.py) — intra-file-only (2 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-llm-_reject_control_fields.txt

### locking.py

  - `_posix_acquire` (src/deepreason/locking.py) — intra-file-only (2 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-locking-_posix_acquire.txt
  - `_posix_release` (src/deepreason/locking.py) — intra-file-only (2 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-locking-_posix_release.txt
  - `_windows_acquire` (src/deepreason/locking.py) — intra-file-only (2 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-locking-_windows_acquire.txt
  - `_windows_release` (src/deepreason/locking.py) — intra-file-only (2 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-locking-_windows_release.txt
  - `_validated_owner` (src/deepreason/locking.py) — intra-file-only (2 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-locking-_validated_owner.txt
  - `_open_lock_file` (src/deepreason/locking.py) — intra-file-only (2 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-locking-_open_lock_file.txt

### log

  - `CorruptLogError` (src/deepreason/log/event_log.py) — intra-file-only (3 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-log-CorruptLogError.txt

### manifest.py

  - `_ids_in` (src/deepreason/manifest.py) — intra-file-only (3 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-manifest-_ids_in.txt
  - `_style_blocks` (src/deepreason/manifest.py) — intra-file-only (2 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-manifest-_style_blocks.txt
  - `_script_blocks` (src/deepreason/manifest.py) — intra-file-only (3 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-manifest-_script_blocks.txt
  - `_css_violations` (src/deepreason/manifest.py) — intra-file-only (2 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-manifest-_css_violations.txt
  - `_js_violations` (src/deepreason/manifest.py) — intra-file-only (2 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-manifest-_js_violations.txt
  - `ImportBudget` (src/deepreason/manifest.py) — intra-file-only (2 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-manifest-ImportBudget.txt

### mcp_help.py

  - `_requirement_entries` (src/deepreason/mcp_help.py) — intra-file-only (3 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-mcp_help-_requirement_entries.txt
  - `capabilities_payload` (src/deepreason/mcp_help.py) — intra-file-only (2 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-mcp_help-capabilities_payload.txt

### mcp_scratch_bridge.py

  - `ScratchOpenInput` (src/deepreason/mcp_scratch_bridge.py) — intra-file-only (3 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-mcp_scratch_bridge-ScratchOpenInput.txt
  - `ScratchRelatedInput` (src/deepreason/mcp_scratch_bridge.py) — intra-file-only (3 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-mcp_scratch_bridge-ScratchRelatedInput.txt
  - `ScratchAttentionInput` (src/deepreason/mcp_scratch_bridge.py) — intra-file-only (4 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-mcp_scratch_bridge-ScratchAttentionInput.txt
  - `BridgeStartBudget` (src/deepreason/mcp_scratch_bridge.py) — intra-file-only (2 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-mcp_scratch_bridge-BridgeStartBudget.txt
  - `StartBridgeInput` (src/deepreason/mcp_scratch_bridge.py) — intra-file-only (4 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-mcp_scratch_bridge-StartBridgeInput.txt
  - `BridgeStatusInput` (src/deepreason/mcp_scratch_bridge.py) — intra-file-only (3 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-mcp_scratch_bridge-BridgeStatusInput.txt
  - `_BridgePage` (src/deepreason/mcp_scratch_bridge.py) — intra-file-only (3 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-mcp_scratch_bridge-_BridgePage.txt
  - `BridgeResultInput` (src/deepreason/mcp_scratch_bridge.py) — intra-file-only (3 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-mcp_scratch_bridge-BridgeResultInput.txt
  - `BridgeClaimsInput` (src/deepreason/mcp_scratch_bridge.py) — intra-file-only (3 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-mcp_scratch_bridge-BridgeClaimsInput.txt
  - `_bounded_scratch_payload` (src/deepreason/mcp_scratch_bridge.py) — intra-file-only (6 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-mcp_scratch_bridge-_bounded_scratch_payload.txt
  - `_bridge_intent` (src/deepreason/mcp_scratch_bridge.py) — intra-file-only (2 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-mcp_scratch_bridge-_bridge_intent.txt
  - `_start_bridge` (src/deepreason/mcp_scratch_bridge.py) — intra-file-only (3 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-mcp_scratch_bridge-_start_bridge.txt
  - `_bridge_status` (src/deepreason/mcp_scratch_bridge.py) — intra-file-only (2 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-mcp_scratch_bridge-_bridge_status.txt
  - `_bridge_result` (src/deepreason/mcp_scratch_bridge.py) — intra-file-only (2 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-mcp_scratch_bridge-_bridge_result.txt
  - `_bridge_claims` (src/deepreason/mcp_scratch_bridge.py) — intra-file-only (2 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-mcp_scratch_bridge-_bridge_claims.txt
  - `_Input` (src/deepreason/mcp_scratch_bridge.py) — intra-file-only (7 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-mcp_scratch_bridge-_Input.txt
  - `_HistoricalPage` (src/deepreason/mcp_scratch_bridge.py) — intra-file-only (4 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-mcp_scratch_bridge-_HistoricalPage.txt
  - `ScratchMapInput` (src/deepreason/mcp_scratch_bridge.py) — intra-file-only (3 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-mcp_scratch_bridge-ScratchMapInput.txt
  - `ScratchSearchInput` (src/deepreason/mcp_scratch_bridge.py) — intra-file-only (3 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-mcp_scratch_bridge-ScratchSearchInput.txt
  - `_BlockInput` (src/deepreason/mcp_scratch_bridge.py) — intra-file-only (3 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-mcp_scratch_bridge-_BlockInput.txt

### mcp_server.py

  - `_MCPInputSchemaError` (src/deepreason/mcp_server.py) — intra-file-only (27 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-mcp_server-_MCPInputSchemaError.txt
  - `_schema_ref` (src/deepreason/mcp_server.py) — intra-file-only (2 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-mcp_server-_schema_ref.txt
  - `_validate_mcp_input` (src/deepreason/mcp_server.py) — intra-file-only (7 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-mcp_server-_validate_mcp_input.txt
  - `_intake_form_schema` (src/deepreason/mcp_server.py) — intra-file-only (2 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-mcp_server-_intake_form_schema.txt
  - `_missing_manifest_credentials` (src/deepreason/mcp_server.py) — intra-file-only (3 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-mcp_server-_missing_manifest_credentials.txt
  - `_public_budget` (src/deepreason/mcp_server.py) — intra-file-only (2 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-mcp_server-_public_budget.txt
  - `_plain_readiness_guidance` (src/deepreason/mcp_server.py) — intra-file-only (2 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-mcp_server-_plain_readiness_guidance.txt
  - `_run_tools` (src/deepreason/mcp_server.py) — intra-file-only (2 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-mcp_server-_run_tools.txt
  - `_read_run_result` (src/deepreason/mcp_server.py) — intra-file-only (2 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-mcp_server-_read_run_result.txt

### measures

  - `_variator_pack` (src/deepreason/measures/hv.py) — intra-file-only (2 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-measures-_variator_pack.txt
  - `_sample_edits` (src/deepreason/measures/hv.py) — intra-file-only (3 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-measures-_sample_edits.txt
  - `_survival` (src/deepreason/measures/hv.py) — intra-file-only (3 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-measures-_survival.txt
  - `_normalize` (src/deepreason/measures/hv.py) — intra-file-only (2 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-measures-_normalize.txt
  - `_text_vector` (src/deepreason/measures/hv.py) — intra-file-only (2 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-measures-_text_vector.txt
  - `_evaluable_battery` (src/deepreason/measures/hv.py) — intra-file-only (2 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-measures-_evaluable_battery.txt
  - `_verdict` (src/deepreason/measures/reach.py) — intra-file-only (2 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-measures-_verdict.txt

### ops.py

  - `_escalated_research` (src/deepreason/ops.py) — intra-file-only (2 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-ops-_escalated_research.txt

### oracle.py

  - `_short` (src/deepreason/oracle.py) — intra-file-only (4 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-oracle-_short.txt
  - `_sandbox_abort_verdict` (src/deepreason/oracle.py) — intra-file-only (6 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-oracle-_sandbox_abort_verdict.txt
  - `_run_local` (src/deepreason/oracle.py) — intra-file-only (2 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-oracle-_run_local.txt
  - `_run_property_local` (src/deepreason/oracle.py) — intra-file-only (3 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-oracle-_run_property_local.txt
  - `_gate_local` (src/deepreason/oracle.py) — intra-file-only (2 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-oracle-_gate_local.txt
  - `_fuzz_property_local` (src/deepreason/oracle.py) — intra-file-only (2 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-oracle-_fuzz_property_local.txt
  - `_check_generator_local` (src/deepreason/oracle.py) — intra-file-only (2 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-oracle-_check_generator_local.txt
  - `_check_checker_local` (src/deepreason/oracle.py) — intra-file-only (2 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-oracle-_check_checker_local.txt
  - `_run_dataset_local` (src/deepreason/oracle.py) — intra-file-only (2 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-oracle-_run_dataset_local.txt

### oracle_sandbox.py

  - `_write_worker_message` (src/deepreason/oracle_sandbox.py) — intra-file-only (6 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-oracle_sandbox-_write_worker_message.txt
  - `_ResourceAbort` (src/deepreason/oracle_sandbox.py) — intra-file-only (3 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-oracle_sandbox-_ResourceAbort.txt
  - `WorkerError` (src/deepreason/oracle_sandbox.py) — intra-file-only (4 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-oracle_sandbox-WorkerError.txt
  - `_cpu_seconds` (src/deepreason/oracle_sandbox.py) — intra-file-only (2 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-oracle_sandbox-_cpu_seconds.txt
  - `_kill_worker` (src/deepreason/oracle_sandbox.py) — intra-file-only (2 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-oracle_sandbox-_kill_worker.txt

### packs

  - `_bounded_view` (src/deepreason/packs/allocate.py) — intra-file-only (2 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-packs-_bounded_view.txt
  - `AllocatedSection` (src/deepreason/packs/allocate.py) — intra-file-only (4 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-packs-AllocatedSection.txt

### preparation.py

  - `_qualification_report_sha256` (src/deepreason/preparation.py) — intra-file-only (3 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-preparation-_qualification_report_sha256.txt
  - `_request_digest` (src/deepreason/preparation.py) — intra-file-only (2 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-preparation-_request_digest.txt
  - `_school_seat_route_ensemble` (src/deepreason/preparation.py) — intra-file-only (5 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-preparation-_school_seat_route_ensemble.txt
  - `_records_for_admitted_dossier` (src/deepreason/preparation.py) — intra-file-only (2 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-preparation-_records_for_admitted_dossier.txt
  - `_compiled_at` (src/deepreason/preparation.py) — intra-file-only (2 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-preparation-_compiled_at.txt
  - `_write_preparation_record` (src/deepreason/preparation.py) — intra-file-only (2 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-preparation-_write_preparation_record.txt

### programs.py

  - `_json_wf` (src/deepreason/programs.py) — intra-file-only (2 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-programs-_json_wf.txt
  - `_tsp14_tour_wf` (src/deepreason/programs.py) — intra-file-only (2 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-programs-_tsp14_tour_wf.txt
  - `_skeleton_wf` (src/deepreason/programs.py) — intra-file-only (2 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-programs-_skeleton_wf.txt
  - `_exec_oracle` (src/deepreason/programs.py) — intra-file-only (2 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-programs-_exec_oracle.txt
  - `_candidate_checker` (src/deepreason/programs.py) — intra-file-only (2 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-programs-_candidate_checker.txt
  - `_property_oracle` (src/deepreason/programs.py) — intra-file-only (2 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-programs-_property_oracle.txt
  - `_generator_wf` (src/deepreason/programs.py) — intra-file-only (2 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-programs-_generator_wf.txt
  - `_checker_wf` (src/deepreason/programs.py) — intra-file-only (2 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-programs-_checker_wf.txt
  - `_lineage_ref` (src/deepreason/programs.py) — intra-file-only (2 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-programs-_lineage_ref.txt
  - `_manifest_wf` (src/deepreason/programs.py) — intra-file-only (2 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-programs-_manifest_wf.txt
  - `_component_wf` (src/deepreason/programs.py) — intra-file-only (2 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-programs-_component_wf.txt
  - `_integration_wf` (src/deepreason/programs.py) — intra-file-only (2 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-programs-_integration_wf.txt
  - `_reasoning_observation_pending` (src/deepreason/programs.py) — intra-file-only (2 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-programs-_reasoning_observation_pending.txt
  - `_lean_external_check` (src/deepreason/programs.py) — intra-file-only (5 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-programs-_lean_external_check.txt
  - `_dataset_oracle` (src/deepreason/programs.py) — intra-file-only (2 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-programs-_dataset_oracle.txt

### provider_profile.py

  - `_UniqueKeyLoader` (src/deepreason/provider_profile.py) — intra-file-only (3 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-provider_profile-_UniqueKeyLoader.txt
  - `_construct_unique_mapping` (src/deepreason/provider_profile.py) — intra-file-only (2 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-provider_profile-_construct_unique_mapping.txt
  - `_read_profile` (src/deepreason/provider_profile.py) — intra-file-only (2 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-provider_profile-_read_profile.txt

### qualification.py

  - `_pair_payload` (src/deepreason/qualification.py) — intra-file-only (6 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-qualification-_pair_payload.txt
  - `_pair_subject_digest` (src/deepreason/qualification.py) — intra-file-only (5 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-qualification-_pair_subject_digest.txt
  - `_read_cache` (src/deepreason/qualification.py) — intra-file-only (3 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-qualification-_read_cache.txt
  - `_DuplicateCacheKey` (src/deepreason/qualification.py) — intra-file-only (5 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-qualification-_DuplicateCacheKey.txt
  - `_reusable_pair` (src/deepreason/qualification.py) — intra-file-only (2 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-qualification-_reusable_pair.txt
  - `_write_unqualified_report` (src/deepreason/qualification.py) — intra-file-only (2 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-qualification-_write_unqualified_report.txt

### readiness.py

  - `_readiness_fields` (src/deepreason/readiness.py) — intra-file-only (3 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-readiness-_readiness_fields.txt

### referee.py

  - `_read_clipped` (src/deepreason/referee.py) — intra-file-only (3 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-referee-_read_clipped.txt
  - `_wire_contract_class` (src/deepreason/referee.py) — intra-file-only (2 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-referee-_wire_contract_class.txt

### report.py

  - `_process_report` (src/deepreason/report.py) — intra-file-only (2 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-report-_process_report.txt
  - `_mean_pairwise_texts` (src/deepreason/report.py) — intra-file-only (2 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-report-_mean_pairwise_texts.txt
  - `_latest_tagged` (src/deepreason/report.py) — intra-file-only (4 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-report-_latest_tagged.txt
  - `_program_grounding_breakdown` (src/deepreason/report.py) — intra-file-only (2 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-report-_program_grounding_breakdown.txt

### research

  - `load_static_corpus` (src/deepreason/research/backends.py) — intra-file-only (2 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-research-load_static_corpus.txt
  - `_evidence_for` (src/deepreason/research/backends.py) — intra-file-only (3 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-research-_evidence_for.txt
  - `_record_fetch_receipts` (src/deepreason/research/backends.py) — intra-file-only (3 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-research-_record_fetch_receipts.txt
  - `AskUserBackend` (src/deepreason/research/backends.py) — intra-file-only (2 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-research-AskUserBackend.txt

### rules

  - `_guard_finding` (src/deepreason/rules/conj.py) — intra-file-only (2 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-rules-_guard_finding.txt
  - `_v6_component_diagnostic` (src/deepreason/rules/conj.py) — intra-file-only (7 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-rules-_v6_component_diagnostic.txt
  - `_v6_scratch_effect_refs` (src/deepreason/rules/conj.py) — intra-file-only (2 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-rules-_v6_scratch_effect_refs.txt
  - `_v6_capability_effect_refs` (src/deepreason/rules/conj.py) — intra-file-only (3 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-rules-_v6_capability_effect_refs.txt
  - `_v6_simulation_effect_refs` (src/deepreason/rules/conj.py) — intra-file-only (2 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-rules-_v6_simulation_effect_refs.txt
  - `_v6_research_effect_refs` (src/deepreason/rules/conj.py) — intra-file-only (2 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-rules-_v6_research_effect_refs.txt
  - `_validate_v6_context_continuation` (src/deepreason/rules/conj.py) — intra-file-only (2 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-rules-_validate_v6_context_continuation.txt
  - `_v6_context_continuation_input_refs` (src/deepreason/rules/conj.py) — intra-file-only (2 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-rules-_v6_context_continuation_input_refs.txt
  - `_v6_no_context_reason` (src/deepreason/rules/conj.py) — intra-file-only (2 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-rules-_v6_no_context_reason.txt
  - `_v6_atomic_conjecture_fallback` (src/deepreason/rules/conj.py) — intra-file-only (3 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-rules-_v6_atomic_conjecture_fallback.txt
  - `_union_blocks` (src/deepreason/rules/conj.py) — intra-file-only (2 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-rules-_union_blocks.txt
  - `_active_control_trace` (src/deepreason/rules/conj.py) — intra-file-only (2 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-rules-_active_control_trace.txt
  - `_refute_crashing_property` (src/deepreason/rules/crit.py) — intra-file-only (3 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-rules-_refute_crashing_property.txt
  - `_crit_proposed_properties` (src/deepreason/rules/crit.py) — intra-file-only (2 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-rules-_crit_proposed_properties.txt
  - `_conditioned_budget` (src/deepreason/rules/crit.py) — intra-file-only (6 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-rules-_conditioned_budget.txt
  - `_condition_pack` (src/deepreason/rules/crit.py) — intra-file-only (6 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-rules-_condition_pack.txt
  - `_simulation_enabled` (src/deepreason/rules/crit.py) — intra-file-only (2 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-rules-_simulation_enabled.txt
  - `_filed_simulations` (src/deepreason/rules/crit.py) — intra-file-only (2 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-rules-_filed_simulations.txt
  - `_llm_event_seq` (src/deepreason/rules/crit.py) — intra-file-only (6 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-rules-_llm_event_seq.txt
  - `_observe_coverage` (src/deepreason/rules/crit.py) — intra-file-only (4 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-rules-_observe_coverage.txt
  - `_artifact_context_digest` (src/deepreason/rules/crit.py) — intra-file-only (3 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-rules-_artifact_context_digest.txt
  - `_v6_transactional_atomic_critic_call` (src/deepreason/rules/crit.py) — intra-file-only (2 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-rules-_v6_transactional_atomic_critic_call.txt
  - `_has_property_oracle` (src/deepreason/rules/crit.py) — intra-file-only (3 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-rules-_has_property_oracle.txt
  - `try_counterexample` (src/deepreason/rules/crit.py) — intra-file-only (5 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-rules-try_counterexample.txt
  - `_authority_value` (src/deepreason/rules/crit.py) — intra-file-only (2 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-rules-_authority_value.txt
  - `_prop_text` (src/deepreason/rules/experiment.py) — intra-file-only (2 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-rules-_prop_text.txt
  - `crash_probe` (src/deepreason/rules/experiment.py) — intra-file-only (2 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-rules-crash_probe.txt
  - `_oracle_ready` (src/deepreason/rules/experiment.py) — intra-file-only (5 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-rules-_oracle_ready.txt
  - `_append_operational` (src/deepreason/rules/guards/anti_relapse.py) — intra-file-only (6 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-rules-_append_operational.txt
  - `domain_log_input` (src/deepreason/rules/guards/anti_relapse.py) — TRUE-CANDIDATE (0 refs anywhere) — proof/dead-rules-domain_log_input.txt
  - `_record_scope_diagnostic` (src/deepreason/rules/guards/anti_relapse.py) — intra-file-only (4 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-rules-_record_scope_diagnostic.txt
  - `_battery` (src/deepreason/rules/guards/anti_relapse.py) — intra-file-only (2 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-rules-_battery.txt
  - `verdict_vector` (src/deepreason/rules/guards/anti_relapse.py) — intra-file-only (3 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-rules-verdict_vector.txt
  - `refl` (src/deepreason/rules/refl.py) — TRUE-CANDIDATE (0 refs anywhere) — proof/dead-rules-refl.txt
  - `_screenshots` (src/deepreason/rules/vision.py) — intra-file-only (2 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-rules-_screenshots.txt

### run_manifest.py

  - `RouteSeatBehavioralCapabilityGrantV1` (src/deepreason/run_manifest.py) — intra-file-only (5 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-run_manifest-RouteSeatBehavioralCapabilityGrantV1.txt
  - `_emit_compile_notice` (src/deepreason/run_manifest.py) — intra-file-only (8 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-run_manifest-_emit_compile_notice.txt
  - `_FrozenDict` (src/deepreason/run_manifest.py) — intra-file-only (5 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-run_manifest-_FrozenDict.txt
  - `_compile_route_seat_contract_decomposition_plan` (src/deepreason/run_manifest.py) — intra-file-only (3 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-run_manifest-_compile_route_seat_contract_decomposition_plan.txt
  - `_canonical_json` (src/deepreason/run_manifest.py) — intra-file-only (5 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-run_manifest-_canonical_json.txt
  - `_source_config_data` (src/deepreason/run_manifest.py) — intra-file-only (3 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-run_manifest-_source_config_data.txt
  - `_endpoint_identifier` (src/deepreason/run_manifest.py) — intra-file-only (3 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-run_manifest-_endpoint_identifier.txt
  - `_route_from_spec` (src/deepreason/run_manifest.py) — intra-file-only (6 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-run_manifest-_route_from_spec.txt
  - `_configured_seats` (src/deepreason/run_manifest.py) — intra-file-only (7 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-run_manifest-_configured_seats.txt
  - `_compile_route_seat_presentation_plan` (src/deepreason/run_manifest.py) — intra-file-only (2 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-run_manifest-_compile_route_seat_presentation_plan.txt
  - `_select_single_model_seed` (src/deepreason/run_manifest.py) — intra-file-only (3 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-run_manifest-_select_single_model_seed.txt
  - `_select_second_judge_spec` (src/deepreason/run_manifest.py) — intra-file-only (2 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-run_manifest-_select_second_judge_spec.txt
  - `_source_feature_policies` (src/deepreason/run_manifest.py) — intra-file-only (2 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-run_manifest-_source_feature_policies.txt
  - `_compile_scratch_policy` (src/deepreason/run_manifest.py) — intra-file-only (3 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-run_manifest-_compile_scratch_policy.txt
  - `_compile_bridge_policy` (src/deepreason/run_manifest.py) — intra-file-only (4 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-run_manifest-_compile_bridge_policy.txt
  - `_effective_source_policy` (src/deepreason/run_manifest.py) — intra-file-only (5 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-run_manifest-_effective_source_policy.txt
  - `_validate_v3_engine_policy_consistency` (src/deepreason/run_manifest.py) — intra-file-only (2 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-run_manifest-_validate_v3_engine_policy_consistency.txt
  - `_normalized_model_identity` (src/deepreason/run_manifest.py) — intra-file-only (2 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-run_manifest-_normalized_model_identity.txt
  - `_validate_v4_control_plane_policy` (src/deepreason/run_manifest.py) — intra-file-only (2 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-run_manifest-_validate_v4_control_plane_policy.txt
  - `_validate_v5_capability_policy` (src/deepreason/run_manifest.py) — intra-file-only (2 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-run_manifest-_validate_v5_capability_policy.txt
  - `_read_bounded_regular` (src/deepreason/run_manifest.py) — intra-file-only (4 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-run_manifest-_read_bounded_regular.txt
  - `_run_manifest_lock` (src/deepreason/run_manifest.py) — intra-file-only (2 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-run_manifest-_run_manifest_lock.txt
  - `_discriminate_raw_run_manifest_version` (src/deepreason/run_manifest.py) — intra-file-only (2 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-run_manifest-_discriminate_raw_run_manifest_version.txt
  - `materialize_run_config` (src/deepreason/run_manifest.py) — TRUE-CANDIDATE (0 refs anywhere) — proof/dead-run_manifest-materialize_run_config.txt
  - `payload_has_rubric` (src/deepreason/run_manifest.py) — intra-file-only (3 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-run_manifest-payload_has_rubric.txt
  - `_preflight_text_authority` (src/deepreason/run_manifest.py) — intra-file-only (3 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-run_manifest-_preflight_text_authority.txt
  - `RouteSeatContractDecompositionGrantV1` (src/deepreason/run_manifest.py) — intra-file-only (8 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-run_manifest-RouteSeatContractDecompositionGrantV1.txt
  - `RouteSeatPresentationGrantV1` (src/deepreason/run_manifest.py) — intra-file-only (4 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-run_manifest-RouteSeatPresentationGrantV1.txt

### runtime

  - `_assert_amendment_committed` (src/deepreason/runtime/continuation.py) — intra-file-only (2 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-runtime-_assert_amendment_committed.txt
  - `_assert_no_live_lock` (src/deepreason/runtime/continuation.py) — intra-file-only (2 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-runtime-_assert_no_live_lock.txt
  - `_append_continuation_record` (src/deepreason/runtime/continuation.py) — intra-file-only (3 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-runtime-_append_continuation_record.txt
  - `_emit_resume_progress` (src/deepreason/runtime/continuation.py) — intra-file-only (4 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-runtime-_emit_resume_progress.txt
  - `_prepare_owned_v4_continuation` (src/deepreason/runtime/continuation.py) — intra-file-only (2 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-runtime-_prepare_owned_v4_continuation.txt
  - `ContinuationRequest` (src/deepreason/runtime/continuation.py) — intra-file-only (3 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-runtime-ContinuationRequest.txt
  - `_owned_v4_control` (src/deepreason/runtime/continuation.py) — intra-file-only (2 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-runtime-_owned_v4_control.txt
  - `_canonical_file` (src/deepreason/runtime/continuation.py) — intra-file-only (3 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-runtime-_canonical_file.txt
  - `_continuation_history` (src/deepreason/runtime/continuation.py) — intra-file-only (2 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-runtime-_continuation_history.txt
  - `_validate_typed_history` (src/deepreason/runtime/continuation.py) — intra-file-only (2 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-runtime-_validate_typed_history.txt
  - `_invalid` (src/deepreason/runtime/launch_policy.py) — intra-file-only (13 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-runtime-_invalid.txt
  - `_disabled` (src/deepreason/runtime/launch_policy.py) — intra-file-only (3 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-runtime-_disabled.txt
  - `_read_policy` (src/deepreason/runtime/launch_policy.py) — intra-file-only (2 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-runtime-_read_policy.txt
  - `_current_epoch_orphans` (src/deepreason/runtime/terminal_authority.py) — intra-file-only (2 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-runtime-_current_epoch_orphans.txt
  - `_write_generic_terminal_checkpoint` (src/deepreason/runtime/terminal_authority.py) — intra-file-only (4 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-runtime-_write_generic_terminal_checkpoint.txt
  - `_seal_terminal_commitment_checkpoint` (src/deepreason/runtime/terminal_authority.py) — intra-file-only (5 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-runtime-_seal_terminal_commitment_checkpoint.txt
  - `_post_commit_result` (src/deepreason/runtime/terminal_authority.py) — intra-file-only (3 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-runtime-_post_commit_result.txt
  - `_current_projection_is_fresh` (src/deepreason/runtime/terminal_authority.py) — intra-file-only (2 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-runtime-_current_projection_is_fresh.txt
  - `_terminal_projection` (src/deepreason/runtime/terminal_authority.py) — intra-file-only (7 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-runtime-_terminal_projection.txt
  - `_result_without_projection` (src/deepreason/runtime/terminal_authority.py) — intra-file-only (6 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-runtime-_result_without_projection.txt
  - `_result_projection` (src/deepreason/runtime/terminal_authority.py) — intra-file-only (2 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-runtime-_result_projection.txt
  - `_result_projection_digest` (src/deepreason/runtime/terminal_authority.py) — intra-file-only (2 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-runtime-_result_projection_digest.txt
  - `_public_terminal_projection_required` (src/deepreason/runtime/terminal_authority.py) — intra-file-only (5 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-runtime-_public_terminal_projection_required.txt
  - `_same_epoch_commitment_objects` (src/deepreason/runtime/terminal_authority.py) — intra-file-only (2 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-runtime-_same_epoch_commitment_objects.txt
  - `_validate_commitment_checkpoint` (src/deepreason/runtime/terminal_authority.py) — intra-file-only (2 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-runtime-_validate_commitment_checkpoint.txt
  - `_evaluated_replay_horizon` (src/deepreason/runtime/terminal_authority.py) — intra-file-only (2 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-runtime-_evaluated_replay_horizon.txt
  - `_amendment_application_window` (src/deepreason/runtime/terminal_authority.py) — intra-file-only (2 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-runtime-_amendment_application_window.txt
  - `_is_amendment_application_event` (src/deepreason/runtime/terminal_authority.py) — intra-file-only (2 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-runtime-_is_amendment_application_event.txt
  - `_validate_stop_history` (src/deepreason/runtime/terminal_authority.py) — intra-file-only (3 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-runtime-_validate_stop_history.txt

### scheduler

  - `stable_component_spec` (src/deepreason/scheduler/scheduler.py) — intra-file-only (3 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-scheduler-stable_component_spec.txt

### scratch

  - `_dedupe` (src/deepreason/scratch/attention.py) — intra-file-only (8 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-scratch-_dedupe.txt
  - `_ScratchModelResult` (src/deepreason/scratch/authoring.py) — intra-file-only (14 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-scratch-_ScratchModelResult.txt
  - `_bounded_attention_policy` (src/deepreason/scratch/conjecture.py) — intra-file-only (2 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-scratch-_bounded_attention_policy.txt
  - `_expanded_attention_policy` (src/deepreason/scratch/conjecture.py) — intra-file-only (2 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-scratch-_expanded_attention_policy.txt
  - `_focus_blocks` (src/deepreason/scratch/conjecture.py) — intra-file-only (2 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-scratch-_focus_blocks.txt
  - `_expansion_seed` (src/deepreason/scratch/conjecture.py) — intra-file-only (2 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-scratch-_expansion_seed.txt
  - `_v6_aliases_for_render_receipt` (src/deepreason/scratch/conjecture.py) — intra-file-only (3 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-scratch-_v6_aliases_for_render_receipt.txt
  - `_replace_local_handles` (src/deepreason/scratch/conjecture.py) — intra-file-only (3 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-scratch-_replace_local_handles.txt
  - `_ReferenceCompiler` (src/deepreason/scratch/contracts.py) — intra-file-only (9 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-scratch-_ReferenceCompiler.txt
  - `ScratchWireModel` (src/deepreason/scratch/contracts.py) — intra-file-only (7 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-scratch-ScratchWireModel.txt
  - `_without_none` (src/deepreason/scratch/models.py) — intra-file-only (3 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-scratch-_without_none.txt
  - `_require_nonblank` (src/deepreason/scratch/models.py) — intra-file-only (11 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-scratch-_require_nonblank.txt
  - `_freeze_list` (src/deepreason/scratch/models.py) — intra-file-only (4 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-scratch-_freeze_list.txt
  - `_sorted_unique` (src/deepreason/scratch/models.py) — intra-file-only (3 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-scratch-_sorted_unique.txt
  - `ScratchProposalModel` (src/deepreason/scratch/proposals.py) — intra-file-only (8 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-scratch-ScratchProposalModel.txt
  - `_finite_vector` (src/deepreason/scratch/similarity.py) — intra-file-only (3 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-scratch-_finite_vector.txt
  - `_engine_fingerprint` (src/deepreason/scratch/similarity.py) — intra-file-only (2 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-scratch-_engine_fingerprint.txt

### seat_bindings.py

  - `_known_groups` (src/deepreason/seat_bindings.py) — intra-file-only (3 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-seat_bindings-_known_groups.txt

### shallow.py

  - `_shallow_runs_dir` (src/deepreason/shallow.py) — intra-file-only (2 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-shallow-_shallow_runs_dir.txt
  - `_mint_run_id` (src/deepreason/shallow.py) — intra-file-only (2 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-shallow-_mint_run_id.txt

### shallow_fitness.py

  - `_case_prompt` (src/deepreason/shallow_fitness.py) — intra-file-only (2 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-shallow_fitness-_case_prompt.txt
  - `_profile_endpoint` (src/deepreason/shallow_fitness.py) — intra-file-only (2 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-shallow_fitness-_profile_endpoint.txt

### signals_read.py

  - `_deferred_model_phase_counts` (src/deepreason/signals_read.py) — intra-file-only (2 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-signals_read-_deferred_model_phase_counts.txt
  - `_token_spend` (src/deepreason/signals_read.py) — intra-file-only (2 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-signals_read-_token_spend.txt

### simulation

  - `_Budget` (src/deepreason/simulation/compiler.py) — intra-file-only (3 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-simulation-_Budget.txt
  - `_exact_keys` (src/deepreason/simulation/compiler.py) — intra-file-only (3 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-simulation-_exact_keys.txt
  - `_constant` (src/deepreason/simulation/compiler.py) — intra-file-only (2 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-simulation-_constant.txt
  - `_input_path` (src/deepreason/simulation/compiler.py) — intra-file-only (2 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-simulation-_input_path.txt
  - `_compile_expression` (src/deepreason/simulation/compiler.py) — intra-file-only (3 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-simulation-_compile_expression.txt

### skills

  - `_check_toolchain` (src/deepreason/skills/adoption.py) — intra-file-only (2 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-skills-_check_toolchain.txt
  - `_semantic_texts` (src/deepreason/skills/distill.py) — intra-file-only (2 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-skills-_semantic_texts.txt
  - `_ngrams` (src/deepreason/skills/distill.py) — intra-file-only (3 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-skills-_ngrams.txt
  - `_negative_ngrams` (src/deepreason/skills/distill.py) — intra-file-only (2 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-skills-_negative_ngrams.txt
  - `_retrieval_text` (src/deepreason/skills/retrieve.py) — intra-file-only (2 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-skills-_retrieval_text.txt
  - `_school_slices` (src/deepreason/skills/retrieve.py) — intra-file-only (2 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-skills-_school_slices.txt
  - `_SummaryMaterial` (src/deepreason/skills/revoice.py) — intra-file-only (2 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-skills-_SummaryMaterial.txt
  - `_voice_text` (src/deepreason/skills/revoice.py) — intra-file-only (2 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-skills-_voice_text.txt
  - `_overlap` (src/deepreason/skills/revoice.py) — intra-file-only (2 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-skills-_overlap.txt
  - `capsule_bytes` (src/deepreason/skills/snapshot.py) — intra-file-only (2 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-skills-capsule_bytes.txt
  - `_content_bytes` (src/deepreason/skills/validate.py) — intra-file-only (3 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-skills-_content_bytes.txt
  - `_positive_dependency_closure` (src/deepreason/skills/validate.py) — intra-file-only (2 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-skills-_positive_dependency_closure.txt
  - `_toolchains` (src/deepreason/skills/validate.py) — intra-file-only (2 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-skills-_toolchains.txt
  - `_config_provenance` (src/deepreason/skills/validate.py) — intra-file-only (2 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-skills-_config_provenance.txt
  - `_packages` (src/deepreason/skills/validate.py) — intra-file-only (2 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-skills-_packages.txt

### status_display.py

  - `_status_value` (src/deepreason/status_display.py) — intra-file-only (2 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-status_display-_status_value.txt

### storage

  - `_link_like` (src/deepreason/storage/blobs.py) — intra-file-only (9 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-storage-_link_like.txt
  - `_known` (src/deepreason/storage/merge.py) — intra-file-only (2 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-storage-_known.txt
  - `_signature` (src/deepreason/storage/merge.py) — intra-file-only (3 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-storage-_signature.txt
  - `_object_data` (src/deepreason/storage/objects.py) — intra-file-only (3 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-storage-_object_data.txt

### ui

  - `_events` (src/deepreason/ui/status.py) — intra-file-only (3 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-ui-_events.txt

### v6_policy.py

  - `_contained_runner_opted` (src/deepreason/v6_policy.py) — intra-file-only (3 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-v6_policy-_contained_runner_opted.txt

### verification

  - `_deny_network` (src/deepreason/verification/_sandbox.py) — intra-file-only (2 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-verification-_deny_network.txt
  - `_derive_v2` (src/deepreason/verification/brokered.py) — intra-file-only (2 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-verification-_derive_v2.txt
  - `_broker_call` (src/deepreason/verification/brokered.py) — intra-file-only (2 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-verification-_broker_call.txt
  - `json_safe` (src/deepreason/verification/contained.py) — intra-file-only (5 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-verification-json_safe.txt
  - `_kill_group` (src/deepreason/verification/contained.py) — intra-file-only (2 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-verification-_kill_group.txt
  - `_digest_prefix` (src/deepreason/verification/llm_broker.py) — intra-file-only (2 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-verification-_digest_prefix.txt
  - `VerifierRegistration` (src/deepreason/verification/registry.py) — intra-file-only (5 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-verification-VerifierRegistration.txt
  - `_adjudication_blindness_findings` (src/deepreason/verification/report.py) — intra-file-only (2 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-verification-_adjudication_blindness_findings.txt
  - `_legacy_channel` (src/deepreason/verification/report.py) — intra-file-only (2 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-verification-_legacy_channel.txt
  - `_read_terminal` (src/deepreason/verification/report.py) — intra-file-only (2 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-verification-_read_terminal.txt
  - `_terminal_findings` (src/deepreason/verification/report.py) — intra-file-only (2 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-verification-_terminal_findings.txt
  - `_model_execution_findings` (src/deepreason/verification/report.py) — intra-file-only (2 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-verification-_model_execution_findings.txt
  - `_terminal_authority_findings` (src/deepreason/verification/report.py) — intra-file-only (2 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-verification-_terminal_authority_findings.txt
  - `_minimal_environment` (src/deepreason/verification/runner.py) — intra-file-only (2 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-verification-_minimal_environment.txt
  - `_limit_child` (src/deepreason/verification/runner.py) — intra-file-only (2 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-verification-_limit_child.txt
  - `_output_items` (src/deepreason/verification/runner.py) — intra-file-only (2 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-verification-_output_items.txt
  - `_local_run` (src/deepreason/verification/simulation.py) — intra-file-only (2 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-verification-_local_run.txt
  - `_run_worker` (src/deepreason/verification/simulation.py) — intra-file-only (2 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-verification-_run_worker.txt

### views

  - `_quantiles` (src/deepreason/views/basin.py) — intra-file-only (2 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-views-_quantiles.txt
  - `_conjectures` (src/deepreason/views/basin.py) — intra-file-only (5 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-views-_conjectures.txt
  - `_pack_exemplars` (src/deepreason/views/basin.py) — intra-file-only (2 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-views-_pack_exemplars.txt
  - `_spec_summary` (src/deepreason/views/evidence.py) — intra-file-only (2 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-views-_spec_summary.txt
  - `_extension` (src/deepreason/views/export.py) — intra-file-only (2 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-views-_extension.txt
  - `_carries_browser_oracle` (src/deepreason/views/export.py) — intra-file-only (2 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-views-_carries_browser_oracle.txt
  - `_deliverables` (src/deepreason/views/export.py) — intra-file-only (2 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-views-_deliverables.txt
  - `ObservationReceipt` (src/deepreason/views/jolt_signals.py) — intra-file-only (7 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-views-ObservationReceipt.txt
  - `PilotSignalPolicy` (src/deepreason/views/jolt_signals.py) — intra-file-only (5 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-views-PilotSignalPolicy.txt
  - `HardOrbitSnapshot` (src/deepreason/views/jolt_signals.py) — intra-file-only (4 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-views-HardOrbitSnapshot.txt
  - `SoftExhaustionSnapshot` (src/deepreason/views/jolt_signals.py) — intra-file-only (4 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-views-SoftExhaustionSnapshot.txt
  - `DiagnosisResult` (src/deepreason/views/jolt_signals.py) — intra-file-only (4 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-views-DiagnosisResult.txt
  - `_GateBlock` (src/deepreason/views/jolt_signals.py) — intra-file-only (5 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-views-_GateBlock.txt
  - `_ConjecturerCall` (src/deepreason/views/jolt_signals.py) — intra-file-only (5 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-views-_ConjecturerCall.txt
  - `_gate_block` (src/deepreason/views/jolt_signals.py) — intra-file-only (2 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-views-_gate_block.txt
  - `_conjecturer_calls` (src/deepreason/views/jolt_signals.py) — intra-file-only (2 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-views-_conjecturer_calls.txt
  - `_max_share` (src/deepreason/views/jolt_signals.py) — intra-file-only (3 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-views-_max_share.txt
  - `_calls_since` (src/deepreason/views/jolt_signals.py) — intra-file-only (2 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-views-_calls_since.txt
  - `_novelty_rows` (src/deepreason/views/jolt_signals.py) — intra-file-only (2 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-views-_novelty_rows.txt
  - `record_trigger_decision` (src/deepreason/views/jolt_signals.py) — TRUE-CANDIDATE (0 refs anywhere) — proof/dead-views-record_trigger_decision.txt
  - `_school` (src/deepreason/views/narrate.py) — intra-file-only (2 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-views-_school.txt
  - `_Prose` (src/deepreason/views/narrate.py) — intra-file-only (3 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-views-_Prose.txt
  - `_narrate_event` (src/deepreason/views/narrate.py) — intra-file-only (2 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-views-_narrate_event.txt
  - `_snippet` (src/deepreason/views/narrate.py) — intra-file-only (4 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-views-_snippet.txt
  - `_resolve_problem` (src/deepreason/views/thesis.py) — intra-file-only (3 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-views-_resolve_problem.txt

### webapp.py

  - `QualificationRunner` (src/deepreason/webapp.py) — intra-file-only (2 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-webapp-QualificationRunner.txt
  - `WebAppError` (src/deepreason/webapp.py) — intra-file-only (14 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-webapp-WebAppError.txt
  - `_sanitized_name` (src/deepreason/webapp.py) — intra-file-only (2 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-webapp-_sanitized_name.txt
  - `_decoded_uploads` (src/deepreason/webapp.py) — intra-file-only (2 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-webapp-_decoded_uploads.txt
  - `_Handler` (src/deepreason/webapp.py) — intra-file-only (2 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-webapp-_Handler.txt

### workflow

  - `_catalogs` (src/deepreason/workflow/conjecture_recovery.py) — intra-file-only (2 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-workflow-_catalogs.txt
  - `_validate_authority` (src/deepreason/workflow/conjecture_recovery.py) — intra-file-only (2 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-workflow-_validate_authority.txt
  - `_mandatory_interface` (src/deepreason/workflow/conjecture_recovery.py) — intra-file-only (2 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-workflow-_mandatory_interface.txt
  - `_existing_conjecture_artifacts` (src/deepreason/workflow/conjecture_recovery.py) — intra-file-only (2 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-workflow-_existing_conjecture_artifacts.txt
  - `_terminal_failure` (src/deepreason/workflow/conjecture_recovery.py) — intra-file-only (3 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-workflow-_terminal_failure.txt
  - `_payload_dict` (src/deepreason/workflow/conjecture_recovery.py) — intra-file-only (2 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-workflow-_payload_dict.txt
  - `_route_hash` (src/deepreason/workflow/criticism.py) — intra-file-only (3 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-workflow-_route_hash.txt
  - `_model_identity_hash` (src/deepreason/workflow/criticism.py) — intra-file-only (3 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-workflow-_model_identity_hash.txt
  - `_diagnostic` (src/deepreason/workflow/nonconjecture_recovery.py) — intra-file-only (3 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-workflow-_diagnostic.txt
  - `_terminalize` (src/deepreason/workflow/nonconjecture_recovery.py) — intra-file-only (3 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-workflow-_terminalize.txt
  - `_existing_admission` (src/deepreason/workflow/nonconjecture_recovery.py) — intra-file-only (5 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-workflow-_existing_admission.txt
  - `_complete_admitted` (src/deepreason/workflow/nonconjecture_recovery.py) — intra-file-only (4 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-workflow-_complete_admitted.txt
  - `_recovered_criticism_authority` (src/deepreason/workflow/nonconjecture_recovery.py) — intra-file-only (2 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-workflow-_recovered_criticism_authority.txt
  - `_criticism_retry_fallback_cases` (src/deepreason/workflow/nonconjecture_recovery.py) — intra-file-only (2 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-workflow-_criticism_retry_fallback_cases.txt
  - `_unapplied` (src/deepreason/workflow/nonconjecture_recovery.py) — intra-file-only (4 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-workflow-_unapplied.txt
  - `_artifact_digest` (src/deepreason/workflow/nonconjecture_recovery.py) — intra-file-only (2 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-workflow-_artifact_digest.txt
  - `_config_referee_contract` (src/deepreason/workflow/nonconjecture_recovery.py) — intra-file-only (2 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-workflow-_config_referee_contract.txt
  - `_recover_config_referee_effect` (src/deepreason/workflow/nonconjecture_recovery.py) — intra-file-only (2 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-workflow-_recover_config_referee_effect.txt
  - `_bridge_authority` (src/deepreason/workflow/nonconjecture_recovery.py) — intra-file-only (3 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-workflow-_bridge_authority.txt
  - `_decide` (src/deepreason/workflow/reducer.py) — intra-file-only (4 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-workflow-_decide.txt
  - `_validate_boundary` (src/deepreason/workflow/reducer.py) — intra-file-only (3 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-workflow-_validate_boundary.txt
  - `_raise_exhausted` (src/deepreason/workflow/repair_transaction.py) — intra-file-only (7 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-workflow-_raise_exhausted.txt
  - `_PointerValidationError` (src/deepreason/workflow/repair_transaction.py) — intra-file-only (2 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-workflow-_PointerValidationError.txt
  - `_finite_error` (src/deepreason/workflow/repair_transaction.py) — intra-file-only (3 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-workflow-_finite_error.txt
  - `_record_bytes` (src/deepreason/workflow/repair_transaction.py) — intra-file-only (6 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-workflow-_record_bytes.txt
  - `_diagnostic_refs` (src/deepreason/workflow/repair_transaction.py) — intra-file-only (5 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-workflow-_diagnostic_refs.txt
  - `_raw_text` (src/deepreason/workflow/repair_transaction.py) — intra-file-only (3 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-workflow-_raw_text.txt
  - `_assess` (src/deepreason/workflow/repair_transaction.py) — intra-file-only (3 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-workflow-_assess.txt
  - `_terminalize_invalid` (src/deepreason/workflow/repair_transaction.py) — intra-file-only (5 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-workflow-_terminalize_invalid.txt
  - `_PlannedApply` (src/deepreason/workflow/replay.py) — intra-file-only (3 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-workflow-_PlannedApply.txt
  - `_record_map` (src/deepreason/workflow/replay.py) — intra-file-only (6 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-workflow-_record_map.txt
  - `_call_index` (src/deepreason/workflow/replay.py) — intra-file-only (3 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-workflow-_call_index.txt
  - `TransactionReplayItem` (src/deepreason/workflow/replay.py) — intra-file-only (9 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-workflow-TransactionReplayItem.txt
  - `_meter_snapshot` (src/deepreason/workflow/shadow.py) — intra-file-only (3 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-workflow-_meter_snapshot.txt
  - `_gate_findings` (src/deepreason/workflow/shadow.py) — intra-file-only (2 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-workflow-_gate_findings.txt
  - `_synthetic_candidate_ref` (src/deepreason/workflow/shadow.py) — intra-file-only (2 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-workflow-_synthetic_candidate_ref.txt
  - `_diagnostic_seq` (src/deepreason/workflow/shadow.py) — intra-file-only (3 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-workflow-_diagnostic_seq.txt
  - `ReservedDispatch` (src/deepreason/workflow/transaction_service.py) — intra-file-only (4 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-workflow-ReservedDispatch.txt

### workflows

  - `_pointer` (src/deepreason/workflows/manifest_compiler.py) — intra-file-only (5 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-workflows-_pointer.txt
  - `_slug_identifier` (src/deepreason/workflows/manifest_compiler.py) — intra-file-only (3 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-workflows-_slug_identifier.txt
  - `_js_identifier` (src/deepreason/workflows/manifest_compiler.py) — intra-file-only (3 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-workflows-_js_identifier.txt
  - `_component_alias_for_index` (src/deepreason/workflows/manifest_compiler.py) — intra-file-only (2 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-workflows-_component_alias_for_index.txt
  - `_error_code` (src/deepreason/workflows/manifest_compiler.py) — intra-file-only (3 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-workflows-_error_code.txt
  - `_validation_diagnostics` (src/deepreason/workflows/manifest_compiler.py) — intra-file-only (3 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-workflows-_validation_diagnostics.txt
  - `_cycle_aliases` (src/deepreason/workflows/manifest_compiler.py) — intra-file-only (2 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-workflows-_cycle_aliases.txt
  - `WorkflowCheckpoint` (src/deepreason/workflows/website.py) — intra-file-only (6 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-workflows-WorkflowCheckpoint.txt
  - `_LockedBlobStore` (src/deepreason/workflows/website.py) — intra-file-only (2 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-workflows-_LockedBlobStore.txt

### workloads

  - `CodeExport` (src/deepreason/workloads/code.py) — intra-file-only (2 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-workloads-CodeExport.txt
  - `SymbolRecord` (src/deepreason/workloads/code.py) — intra-file-only (5 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-workloads-SymbolRecord.txt
  - `DependencyEdge` (src/deepreason/workloads/code.py) — intra-file-only (7 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-workloads-DependencyEdge.txt
  - `WorkspaceFile` (src/deepreason/workloads/code.py) — intra-file-only (9 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-workloads-WorkspaceFile.txt
  - `CodeCard` (src/deepreason/workloads/code.py) — intra-file-only (4 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-workloads-CodeCard.txt
  - `_normal_relative` (src/deepreason/workloads/code.py) — intra-file-only (5 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-workloads-_normal_relative.txt
  - `_allowed` (src/deepreason/workloads/code.py) — intra-file-only (4 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-workloads-_allowed.txt
  - `_python_metadata` (src/deepreason/workloads/code.py) — intra-file-only (3 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-workloads-_python_metadata.txt
  - `_module_name` (src/deepreason/workloads/code.py) — intra-file-only (2 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-workloads-_module_name.txt
  - `_safe_target` (src/deepreason/workloads/code.py) — intra-file-only (4 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-workloads-_safe_target.txt
  - `_replace_occurrence` (src/deepreason/workloads/code.py) — intra-file-only (2 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-workloads-_replace_occurrence.txt
  - `FormalWorkflowError` (src/deepreason/workloads/formal.py) — intra-file-only (11 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-workloads-FormalWorkflowError.txt
  - `FormalWorkflowArtifacts` (src/deepreason/workloads/formal.py) — intra-file-only (3 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-workloads-FormalWorkflowArtifacts.txt
  - `_request_commitment` (src/deepreason/workloads/formal.py) — intra-file-only (2 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-workloads-_request_commitment.txt
  - `_validate_receipt` (src/deepreason/workloads/formal.py) — intra-file-only (2 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-workloads-_validate_receipt.txt
  - `_FormalModel` (src/deepreason/workloads/formal.py) — intra-file-only (6 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-workloads-_FormalModel.txt
  - `WorkloadAdapter` (src/deepreason/workloads/registry.py) — intra-file-only (4 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-workloads-WorkloadAdapter.txt
  - `_SimulationModel` (src/deepreason/workloads/simulation.py) — intra-file-only (4 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-workloads-_SimulationModel.txt
  - `SimulationWorkflowArtifacts` (src/deepreason/workloads/simulation.py) — intra-file-only (3 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-workloads-SimulationWorkflowArtifacts.txt
  - `BrainRequest` (src/deepreason/workloads/text.py) — intra-file-only (2 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-workloads-BrainRequest.txt
  - `TextWorkloadAdapter` (src/deepreason/workloads/text.py) — intra-file-only (2 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-workloads-TextWorkloadAdapter.txt
  - `Definition` (src/deepreason/workloads/text.py) — intra-file-only (2 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-workloads-Definition.txt
  - `DerivationStep` (src/deepreason/workloads/text.py) — intra-file-only (2 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-workloads-DerivationStep.txt
  - `WebsiteWorkloadAdapter` (src/deepreason/workloads/website.py) — intra-file-only (2 occurrences in own file — false positive of the outside-file-only scan) — proof/dead-workloads-WebsiteWorkloadAdapter.txt
