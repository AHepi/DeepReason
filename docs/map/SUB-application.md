<!-- DR-SUB-application -->
Verified-at: a82872b38
Verify: python -m pytest tests/test_v6_only_cli_admission.py tests/test_v6_only_application_admission.py tests/test_easy.py -q && python -m pytest tests/test_application_text_runs_d0.py tests/test_r0_terminal_verification.py tests/test_continuation.py tests/test_stop_policy.py tests/test_progress.py -q
Owns: src/deepreason/application/, src/deepreason/workflows/, src/deepreason/cli/, src/deepreason/runtime/, src/deepreason/easy.py, src/deepreason/intake_form.py, src/deepreason/shallow.py
Seams: 
Seams-undocumented: application x bridge, application x run-identity, application x scratch, application x verification, application x workflow

# The application boundary — starting, watching, and ending a run

## What it is

Everything between a human (or a ladder shell script) and the reasoning engine
lives here, and none of it is epistemic: no rule fires, no status moves, no
artifact is adjudicated. `application/` defines a closed typed vocabulary —
intents in, result records out — for the three things a client can ask for: a
text reasoning run, a grounded bridge, and a read-only scratchpad query. `cli/`
and the MCP server are the only clients of that vocabulary, and both are
deliberately thin: they parse arguments, build an intent, call one shared
service object, and render what comes back. `runtime/` holds the workload-
neutral machinery every run needs whatever it is reasoning about — budget
limits, the progress files a watcher polls, the deterministic stopping
controller, continuation preparation from a typed stop, and the terminal
commitment and result publication that make a finished run inspectable.
`easy.py` is host-side provider setup — the wizard, the endpoint presets, and
the credentials file — plus a fail-closed tombstone where the retired website
execution facade used to be, and, still live beside that tombstone, the website
graph helpers (`seed_component`, `register_assembly`, `integration_criticism`)
whose only callers are in `workflows/`; `workflows/` is the website state
machine that tombstone once drove, which no public entry point reaches any more.
`check: for s in seed_component register_assembly integration_criticism; do grep -q "^def $s(" src/deepreason/easy.py || exit 1; grep -q "easy.$s(" src/deepreason/workflows/website.py || exit 1; test "$(grep -rl "easy\.$s(" --include=*.py src/deepreason | wc -l)" -eq 1 || exit 1; done; grep -q "^def setup_wizard(" src/deepreason/easy.py && grep -q "^def base_dir(" src/deepreason/easy.py`

Exactly two client families use the typed services, and neither reaches a
scheduler, a harness or a stop policy of its own.
`check: grep -q '^deepreason = "deepreason.cli.main:main"' pyproject.toml && ! grep -rl "TEXT_RUN_SERVICE\|GROUNDED_BRIDGE_SERVICE\|SCRATCH_QUERY_SERVICE" --include=*.py src/deepreason | grep -qvE "^src/deepreason/(application/|cli/|mcp_server\.py|mcp_scratch_bridge\.py)" && python -m pytest tests/test_application_text_runs_d0.py::test_clients_have_only_thin_service_dispatch_and_one_registry tests/test_application_scratch.py::test_cli_and_mcp_handlers_are_thin_application_adapters tests/test_application_bridge_service.py::test_bridge_clients_do_not_own_workflow_or_persistence tests/test_application_text_runs_d0.py::test_cli_and_mcp_compile_the_same_start_intent tests/test_v6_only_cli_admission.py::test_public_parser_omits_make_and_unqualified_advanced_commands -q`

Admission precedes interpretation — for every verb that INTERPRETS or MUTATES a
run root. Those pass through one V6 gate — RunManifest v6, run-input manifest
v2, a matching evidence dossier — before their own code runs, so a pre-V6 or
tampered root fails with a typed code instead of being half-read by a view.
Two pure READERS are deliberately outside the gate, `findings` and `results`:
a reader that refused a pre-V6 root would refuse exactly the roots an operator
most needs to inspect, so `results` reports the manifest's admission state as a
typed fact (`identity.manifest_present`, `identity.manifest_schema_version`)
instead of turning it into a refusal. Whether read-only verbs SHOULD be
admitted is an open design question, not settled here
(`experiments/2026-08-13-change-results-retrieval-surface/PARKED.md` P1).
`check: python -c "from deepreason.cli.main import _ROOT_ADMISSION_COMMANDS as c; assert 'results' not in c and 'findings' not in c"`
`check: grep -q "^_ROOT_ADMISSION_COMMANDS = frozenset(" src/deepreason/cli/main.py && grep -q "^def _admit_v6_root(" src/deepreason/cli/main.py && python -m pytest tests/test_v6_only_cli_admission.py::test_every_shared_root_command_rejects_a_historical_manifest tests/test_v6_only_cli_admission.py::test_every_shared_root_command_rejects_missing_manifest_before_interpretation tests/test_v6_only_cli_admission.py::test_historical_roots_with_sidecars_fail_before_command_services -q`

## Seams

No `Seams:` entries yet.

| Side | Status | What the agreement is (one line) |
|---|---|---|
| application x bridge | undocumented | real: `application.GROUNDED_BRIDGE_SERVICE` is a thin client over `DR-SUB-bridge`'s `build`/`start`/`status`/`result`/`claims`/`inspect`/`validate` — this doc says so explicitly ("see `DR-SUB-bridge` for what a bridge is") |
| application x scratch | undocumented | real: `application.SCRATCH_QUERY_SERVICE.execute` is the whole public surface for read-only scratchpad queries |
| application x run-identity | undocumented | likely real, unverified here: every admitted CLI verb resolves and locks a run root, which is `DR-CON-run-identity`'s charter ("deterministic run ids, roots on disk") — candidate, worth a seam document rather than an assumption |
| application x verification | undocumented | plausible: the V6 admission gate (`_admit_v6_root`) refuses a tampered or historical root by manifest/dossier shape before any command runs — whether it calls into `verify_root` itself or only manifest-level checks is not confirmed here |
| application x workflow | undocumented | CORRECTED (caught while writing batch D): this pair names `DR-SUB-workflow`, the singular v6 transactional control plane — NOT this package's own plural `workflows/` (the retired website machine, which is a true but irrelevant fact about a different directory of the same near-name). Likely real: `runtime.terminal_authority.ensure_terminal_commitment`/`finalize_terminal_result` (owned here) plausibly reads the typed terminal `workflow/` itself authors, but the exact call site is not confirmed in this document |

## Entry points

- `cli.main.main` — the `deepreason` console script; `build_parser` is the whole
  public verb surface, and `_main` is the dispatch table. `_admit_v6_root` and
  `_ROOT_ADMISSION_COMMANDS` are the gate described above.
- `application.TEXT_RUN_SERVICE` (`TextRunApplicationService`) — the only way to
  run text reasoning: `start`, `start_manifest_run`, `continue_run`, `inspect`,
  `inspect_outstanding_work`, `result`, `cancel`, `watch`, `wait`. `_launch`
  performs the whole admission sequence and then hands one daemon thread to
  `TEXT_RUN_WORKERS`; `_worker` owns the scheduler call and the progress
  stream. `start_manifest_run` is the entry for a caller that already HOLDS a
  compiled manifest and a root — a ladder, or `deepreason run --run-manifest` —
  and it inspects nothing about the manifest: it resolves the workload from the
  root (read-only), spells an absent token ceiling as `"unlimited"`, and calls
  `start`. That is what makes it unable to refuse a configuration for its
  shape.
- `application.text_runs.terminalize_text_run` — the ONE stop-to-published-
  terminal sequence (stop record, `checkpoint.json`, capability audits,
  `_v6_run_result`, `finalize_terminal_result`, `run-result.json`), shared by
  `_worker` and by `finalize_stopped_root` — and by nothing in `cli/`, which
  since 2026-08-13 runs nothing itself. `ensure_lifecycle_documents`,
  `workload_spec_for_root` and `finalize_stopped_root` are its companions: the
  documents a continuation reads, the workload a root can name itself by, and
  the operator-facing `deepreason finalize` that brings an already-stopped root
  to its terminal by APPENDING (see Traps).
- `application.GROUNDED_BRIDGE_SERVICE` (`GroundedBridgeApplicationService`) —
  `build`, `start`, `status`, `result`, `claims`, `inspect`, `validate` over a
  finished reasoning root (see `DR-SUB-bridge` for what a bridge is).
- `application.results.results_summary` / `render_results` /
  `resolve_results_root` / `embedder_summary` — the ONE typed-outcome
  retrieval surface behind
  `deepreason results`. A pure reader over durable sidecars, the log and the
  amendment chain; it composes `findings.findings_summary` rather than
  re-deriving status counts, reads the STORED verification verdict unless
  `verify=True`, and emits `{"absent": True, "reason": <code>}` for every fact
  a root does not carry. It writes nothing into a run root.
  `embedder_summary` / `embedder_summary_for_root` derive which embedder a run ACTUALLY measured with from
  the log's own `embedder` / `embedder-fallback` Measure events (last stamp
  wins, so an amended run reports the geometry its final cycles used), and is
  the one fact here that is also decorated onto `deepreason reason`'s printed
  terminal remark — printed to STDERR, never added as a key on the payload:
  stdout's JSON is the durable result contract and MCP `run_result` must
  return it byte-identically
  (`wheel_operational_smoke.py`'s `STAGE_MCP_REQUEST` compares them for exact
  equality, and caught the first attempt, which did add a key).
  `run-result.json` is not modified either. The CLI calls the PATH-taking
  `embedder_summary_for_root`, never the harness-taking one: clients are thin
  service dispatch and may not construct a `Harness`
  (`test_clients_have_only_thin_service_dispatch_and_one_registry`).
`check: for s in results_summary render_results resolve_results_root embedder_summary embedder_summary_for_root; do grep -q "^def $s(" src/deepreason/application/results.py || exit 1; done; grep -q "from deepreason.findings import findings_summary" src/deepreason/application/results.py && python -c "import ast, pathlib; src = pathlib.Path('src/deepreason/cli/main.py').read_text(); f = [n for n in ast.walk(ast.parse(src)) if isinstance(n, ast.FunctionDef) and n.name == '_cmd_reason'][0]; body = ast.get_source_segment(src, f); assert 'embedder_line(embedder_summary_for_root(' in body, 'the run terminal must report the embedder it measured with'; assert not [n for n in ast.walk(f) if isinstance(n, ast.Assign) and any(isinstance(x, ast.Subscript) and getattr(x.value, 'id', '') == 'payload' and getattr(getattr(x, 'slice', None), 'value', None) == 'embedder' for x in n.targets)], 'the embedder must NOT become a key on the durable result payload: MCP run_result must stay byte-identical to CLI stdout'; assert 'Harness(' not in body, 'the client stays thin: the application layer opens the root'" && ! grep -rn "embedder" src/deepreason/runtime/terminal_authority.py && python -m pytest tests/test_results_command.py::test_results_summary_writes_nothing_into_a_committed_root tests/test_results_command.py::test_absent_facts_are_typed_absences_not_omitted_keys tests/test_results_command.py::test_verification_reads_the_stored_verdict_and_does_not_replay tests/test_results_command.py::test_top_level_help_names_the_results_verb tests/test_results_command.py::test_results_surfaces_the_embedder_and_names_a_fallback_loudly tests/test_results_command.py::test_results_embedder_absence_is_typed_not_a_failure -q`
- `application.SCRATCH_QUERY_SERVICE.execute` — dispatches the closed scratch
  query union; every branch is read-only except the explicit record-direct-open.
- `application.intents.start_text_run_intent` / `continue_text_run_intent` /
  `budget_intent` — the pure parsers a client uses so CLI and MCP compile
  byte-identical intents. `application.models.run_result_exit_code` is the
  process exit contract.
- `application.ConjectureApplicationBoundary.begin` — the shared authority
  envelope wrapped around one conjecture provider call, so the full scheduler
  and the reduced loop record the same control chain.
- `runtime.launch_policy.require_v6_launch_allowed` (schema gate plus the
  rollback kill switch and release policy), `resolve_effective_run_manifest`
  (explicit vs. bound manifest reconciliation), and
  `require_v6_production_qualification` (one exact doctor report authorizes the
  launch).
- `runtime.terminal_authority.ensure_terminal_commitment`,
  `finalize_terminal_result`, `recover_terminal_result`,
  `derive_terminal_authority`, `validate_terminal_commitment_storage` — build,
  publish, revalidate and re-derive the one terminal head of a run.
- `runtime.continuation.prepare_continuation` — the only way a stopped root
  becomes runnable again; validates the stop digest, the typed continuation
  history and the checkpoint fence before authorizing a RESUMED transition.
- `runtime.progress.ProgressSink`, `runtime.stop.StopController` /
  `write_stop_record`, `runtime.budget.parse_limit` / `AggregateMeter` — the
  observation, stopping and metering primitives every workload shares.
- `cli.doctor.run_production_contract_doctor` / `load_production_contract_report`
  — the production-contract battery whose report is launch authority.
- `cli.bridge.handle_bridge_command`, `cli.scratch.dispatch_scratch` — the
  rendering-only subcommand front ends.
- `easy.setup_wizard` / `apply_setup` / `setup_options` / `load_credentials` /
  `save_credential` — provider configuration and key storage. `easy.make` is a
  tombstone, not an entry point (see Traps).
- `workflows.manifest_compiler.compile_compact_manifest` / `ManifestCompiler` and
  `workflows.website.WebsiteWorkflow` — the legacy website path, exercised only
  by its tests.
`check: for s in main build_parser _admit_v6_root; do grep -q "^def $s(" src/deepreason/cli/main.py || exit 1; done; for s in terminalize_text_run ensure_lifecycle_documents workload_spec_for_root finalize_stopped_root; do grep -q "^def $s(" src/deepreason/application/text_runs.py || exit 1; done; for s in start start_manifest_run continue_run inspect inspect_outstanding_work result cancel watch wait _launch _worker; do grep -q "    def $s(" src/deepreason/application/text_runs.py || exit 1; done; python -c "import inspect;from deepreason.application.text_runs import TextRunApplicationService as S;f=S.start_manifest_run;code=inspect.getsource(f).replace(f.__doc__, '');assert not any(t in code for t in ('judge', 'school', 'criticism', 'roles')), code" || exit 1; for s in build start status result claims inspect validate; do grep -q "    def $s(" src/deepreason/application/bridge.py || exit 1; done; grep -q "    def execute(" src/deepreason/application/scratch.py && grep -q "    def begin(" src/deepreason/application/conjecture.py && grep -q "^def run_result_exit_code(" src/deepreason/application/models.py; for s in budget_intent start_text_run_intent continue_text_run_intent; do grep -q "^def $s(" src/deepreason/application/intents.py || exit 1; done; grep -q "^TEXT_RUN_SERVICE = TextRunApplicationService()" src/deepreason/application/text_runs.py && grep -q "^GROUNDED_BRIDGE_SERVICE = GroundedBridgeApplicationService()" src/deepreason/application/bridge.py && grep -q "^SCRATCH_QUERY_SERVICE = ScratchQueryApplicationService()" src/deepreason/application/scratch.py`
`check: for s in require_v6_launch_allowed resolve_effective_run_manifest require_v6_production_qualification; do grep -q "^def $s(" src/deepreason/runtime/launch_policy.py || exit 1; done; for s in derive_terminal_authority ensure_terminal_commitment finalize_terminal_result recover_terminal_result validate_terminal_commitment_storage; do grep -q "^def $s(" src/deepreason/runtime/terminal_authority.py || exit 1; done; grep -q "^def prepare_continuation(" src/deepreason/runtime/continuation.py && grep -q "^class ProgressSink" src/deepreason/runtime/progress.py && grep -q "^class StopController" src/deepreason/runtime/stop.py && grep -q "^def write_stop_record(" src/deepreason/runtime/stop.py && grep -q "^def parse_limit(" src/deepreason/runtime/budget.py && grep -q "^class AggregateMeter" src/deepreason/runtime/budget.py; for s in setup_wizard setup_options apply_setup load_credentials save_credential make; do grep -q "^def $s(" src/deepreason/easy.py || exit 1; done; grep -q "^def run_production_contract_doctor(" src/deepreason/cli/doctor.py && grep -q "^def load_production_contract_report(" src/deepreason/cli/doctor.py && grep -q "^def handle_bridge_command(" src/deepreason/cli/bridge.py && grep -q "^def dispatch_scratch(" src/deepreason/cli/scratch.py && grep -q "^class WebsiteWorkflow" src/deepreason/workflows/website.py && grep -q "^def compile_compact_manifest(" src/deepreason/workflows/manifest_compiler.py && grep -q "^class ManifestCompiler" src/deepreason/workflows/manifest_compiler.py`

## State it owns

Every mutable control file in a run root that is not the append-only record
itself. `runtime/progress.py` owns `progress.jsonl` (append-only, contiguous
sequence), its `run-status.json` latest snapshot, and the `cancel.requested`
flag. `runtime/stop.py` owns `run-stop.json` as a mutable latest pointer over
an immutable `run-stops/<event_seq>-<digest>.json` history.
`runtime/continuation.py` owns `continuations.jsonl`.
`runtime/terminal_authority.py` owns `run-result.json` and
`REPLAY_VALIDATION.json`. `application/text_runs.py` owns the frozen
`run-request.json` and `text-workload.json` written at bind time, and
`checkpoint.json` at stop. `workflows/website.py` owns `website-checkpoint.json`
and `website-terminal.json`. Everything under `runtime/` and `application/` is
published through one shared helper, `runtime.progress._atomic_json`, which
fsyncs the payload, renames it over the target, then fsyncs the directory so the
rename itself survives a power loss. `workflows/website.py` is the exception and
not the shape to copy: it open-codes its own temp-and-rename with no directory
fsync, and writes `website-terminal.json` with a bare `write_text`.

Outside any run root it owns the host's provider state: `easy.base_dir()`
(`$DEEPREASON_HOME` or `~/.deepreason`) holds `credentials`, created
owner-read-write before any key bytes exist, and `engine.yaml`.
`load_credentials` injects stored keys into the environment at the top of every
CLI invocation, and an already-set environment variable always wins. In memory,
`TEXT_RUN_WORKERS` and `GROUNDED_BRIDGE_WORKERS` are process-global registries
of live worker threads; they are advisory only — durable concurrency safety
comes from the operator locks and the terminal-commitment lock.
`check: grep -q '"progress.jsonl"' src/deepreason/runtime/progress.py && grep -q '"run-status.json"' src/deepreason/runtime/progress.py && grep -q '"cancel.requested"' src/deepreason/runtime/progress.py && grep -q '"run-stops"' src/deepreason/runtime/stop.py && grep -q '"run-stop.json"' src/deepreason/runtime/stop.py && grep -q '"continuations.jsonl"' src/deepreason/runtime/continuation.py && grep -q '"run-request.json"' src/deepreason/application/text_runs.py && grep -q '"text-workload.json"' src/deepreason/application/text_runs.py && grep -q '"checkpoint.json"' src/deepreason/application/text_runs.py && grep -q '_REPLAY_VALIDATION_NAME = "REPLAY_VALIDATION.json"' src/deepreason/runtime/terminal_authority.py && grep -q '"run-result.json"' src/deepreason/runtime/terminal_authority.py && grep -q '"website-checkpoint.json"' src/deepreason/workflows/website.py && grep -q '(self.harness.root / "website-terminal.json").write_text(' src/deepreason/workflows/website.py && grep -q "^def _atomic_json(" src/deepreason/runtime/progress.py && grep -q "^from deepreason.runtime.progress import _atomic_json" src/deepreason/runtime/stop.py && grep -q "^from deepreason.runtime.progress import _atomic_json" src/deepreason/runtime/terminal_authority.py && grep -q "from deepreason.runtime.progress import ProgressSink, _atomic_json" src/deepreason/application/text_runs.py && ! grep -q "_atomic_json" src/deepreason/workflows/website.py && grep -q "os.replace(temporary, target)" src/deepreason/workflows/website.py && ! grep -q "O_RDONLY" src/deepreason/workflows/website.py && grep -q 'os.environ.get("DEEPREASON_HOME")' src/deepreason/easy.py && grep -q 'return base_dir() / "credentials"' src/deepreason/easy.py && grep -q 'return base_dir() / "engine.yaml"' src/deepreason/easy.py && grep -q "stat.S_IRUSR | stat.S_IWUSR" src/deepreason/easy.py && grep -q "easy.load_credentials()  # stored keys reach every command; env vars win" src/deepreason/cli/main.py && grep -q "^TEXT_RUN_WORKERS = TextRunWorkerRegistry()" src/deepreason/application/text_runs.py && grep -q "^GROUNDED_BRIDGE_WORKERS = GroundedBridgeWorkerRegistry()" src/deepreason/application/bridge.py && python -m pytest tests/test_r0_terminal_verification.py::test_v6_writer_emits_verified_v2_envelope tests/test_continuation.py::test_stop_history_is_preserved_behind_latest_pointer tests/test_easy.py::test_save_and_load_credentials_roundtrip tests/test_easy.py::test_existing_environment_wins_over_stored_key -q`

The boundary appends few events, and only through named harness recorders —
never by reaching the log itself. `cli/` appends none at all. `runtime/`
appends two Control-family kinds, not one: the terminal commitment from
`terminal_authority` and the RESUMED transition from `continuation`.
`application/` appends `record_measure` entries plus the single
`record_lifecycle_transition` that gives a budget-exhausted stop its lifecycle
receipt (see Traps); its one writing scratch branch goes through the scratch
service rather than a harness recorder. `workflows/website.py` and the website
graph helpers in `easy.py` append only Measure events — `record_llm_calls` is a
`record_measure` wrapper.
`check: test -z "$(grep -rhoE "harness\.record_[a-z_]+" --include=*.py src/deepreason/cli)" && test "$(grep -rhoE "harness\.record_[a-z_]+" --include=*.py src/deepreason/runtime | sort -u | tr "\n" " ")" = "harness.record_resume_transition harness.record_terminal_commitment " && test "$(grep -rhoE "harness\.record_[a-z_]+" --include=*.py src/deepreason/application | sort -u | tr "\n" " ")" = "harness.record_lifecycle_transition harness.record_measure " && test "$(grep -rhoE "harness\.record_[a-z_]+" --include=*.py src/deepreason/workflows src/deepreason/easy.py | sort -u | tr "\n" " ")" = "harness.record_llm_calls harness.record_measure " && grep -q "harness.record_terminal_commitment(expected, expected_draft)" src/deepreason/runtime/terminal_authority.py && grep -q "harness.record_resume_transition(snapshot, resume)" src/deepreason/runtime/continuation.py && grep -q "harness.record_lifecycle_transition(observation, snapshot, lifecycle)" src/deepreason/application/text_runs.py && grep -q "self.record_measure(inputs=\[tag, \*extra\], llm=call)" src/deepreason/harness.py && grep -q "service.record_attention_receipt(receipt, context_ref=" src/deepreason/application/scratch.py`

## Where to change what

| To change... | Edit | Test |
|---|---|---|
| What `deepreason results` reports, or how a fact's absence is typed | `results_summary` and `ABSENCE_REASONS` in `application/results.py`; `render_results` for the glossed human mode | `tests/test_results_command.py::test_absent_facts_are_typed_absences_not_omitted_keys` |
| What the reported survivor COUNT means | NOT this package: `is_import_admission` in `ontology/state.py` (`DR-SUB-ontology`). `_survivor_count` may only SUBTRACT the admission records the invariant bars from the set the record published — never re-derive membership, never re-adjudicate a member's status | `tests/test_import_role_survivors.py::test_the_results_surface_reports_the_conjectures_and_not_the_dossier` |
| Add, rename or retire a CLI verb | `build_parser` and the matching `_main` branch in `cli/main.py`; add it to `_ROOT_ADMISSION_COMMANDS` if it reads a run root | `tests/test_v6_only_cli_admission.py::test_public_parser_omits_make_and_unqualified_advanced_commands` |
| What a command may do to a pre-V6, unbound or tampered root | `_admit_v6_root` in `cli/main.py` | `tests/test_v6_only_cli_admission.py::test_every_shared_root_command_rejects_a_historical_manifest` |
| The process exit-code contract | `run_result_exit_code` in `application/models.py` | `tests/test_r0_terminal_verification.py::test_run_result_exit_contract` |
| What a client is allowed to ask for (intent fields) | the `*IntentV1` models in `application/models.py`, constructed only via `application/intents.py` | `tests/test_application_text_runs_d0.py::test_start_intent_is_strict_and_has_no_client_authority_fields` |
| The order of checks before a text run touches disk | `TextRunApplicationService._launch` in `application/text_runs.py` | `tests/test_v6_only_application_admission.py::test_v6_rejects_mismatched_question` |
| Whether launches are permitted at all (kill switch, release policy) | `require_v6_launch_allowed` and `_read_policy` in `runtime/launch_policy.py` | `tests/test_v6_only_application_admission.py::test_require_v6_launch_allowed_fails_closed_for_non_v6` |
| Which qualification evidence authorizes a launch | `require_v6_production_qualification` in `runtime/launch_policy.py` | `tests/test_v6_only_cli_admission.py::test_run_requires_qualification_before_operator_lock` |
| The production-contract release gate (20 cases, 19 must be eventually valid) | `PRODUCTION_CASES_PER_PAIR` / `PRODUCTION_EVENTUAL_VALID_MINIMUM` / `_release_gate` in `cli/doctor.py` | `tests/test_cli_production_doctor_v6.py::test_report_computes_19_of_20_gate_and_all_metrics` |
| Stopping thresholds, or the fixed escape ladder | `StopPolicy` and `ESCAPE_LADDER` in `runtime/stop.py` | `tests/test_stop_policy.py::test_corroborated_stuck_exhausts_fixed_escape_ladder_before_stop` |
| What a watcher can observe | `ProgressEvent` and `ProgressSink.emit` in `runtime/progress.py` | `tests/test_progress.py::test_progress_is_monotonic_append_only_and_latest_is_atomic` |
| What a continuation may resume from | `prepare_continuation` in `runtime/continuation.py` | `tests/test_continuation.py::test_continue_rejects_tampered_stop_digest` |
| Whether a TAMPERED record may be resumed or amended, and what counts as tampered | `security_channel_checks` / `record_security_checks` / `record_verification_refusal` in `runtime/continuation.py` — ONE definition, called last in `prepare_continuation` and last in `_amend_locked`. The membership it filters on is READ from `verification/report.py`'s `_SECURITY_CHECKS`, never redefined here: that package owns the channel taxonomy. Deliberately NOT configurable — the 2026-08-29 P2 law calls it a security boundary, so the 2026-08-28 gates-are-optional law is read as not reaching it | `tests/test_jailbreak_gate.py::test_continue_refuses_a_forged_record_and_names_the_checks` |
| The published terminal result envelope | `_v6_run_result` in `application/text_runs.py` and `finalize_terminal_result` in `runtime/terminal_authority.py` | `tests/test_r0_terminal_verification.py::test_v6_writer_emits_verified_v2_envelope` |
| What ANY finished run writes at stop — there is one launch path, so this is every run | `terminalize_text_run` in `application/text_runs.py` (never a second path's copy of it) | `tests/test_lifecycle_operation_parity.py::test_manifest_launched_root_reaches_typed_terminal_and_accepts_amend` |
| What a FAILURE terminal records about its own continuability | two of the THREE exits of `_worker`'s single `except (Exception, SystemExit)` block in `application/text_runs.py` — `TERMINAL_NO_CHECKPOINT_WRITTEN` (no harness) and `TERMINAL_LIFECYCLE_NOT_TAKEN_FAILURE_TERMINAL` (ordinary), both through `_refusal` onto the existing `terminal_lifecycle_refusal` key. The third exit (`current_terminal_commitment is not None`) still records nothing — parked, `2026-08-30-change-checkpoint-hardening` F10 | `tests/test_checkpoint_hardening.py::test_a_failure_terminal_records_why_it_cannot_be_continued` |
| How a caller holding a compiled manifest starts a run, and what `deepreason run --run-manifest` dispatches into | `TextRunApplicationService.start_manifest_run` in `application/text_runs.py`; `_dispatch_managed_run` in `cli/main.py` renders the result and owns nothing else | `tests/test_single_run_path.py::test_the_door_narrows_no_configuration_the_compiler_admits` |
| How a root that stopped without a terminal reaches one | `finalize_stopped_root` in `application/text_runs.py` and `_cmd_finalize` in `cli/main.py` | `tests/test_lifecycle_operation_parity.py::test_finalize_reaches_terminal_on_a_root_that_stopped_without_one` |
| Provider presets, or what the wizard asks | `PROVIDERS` / `MAKE_OVERRIDES` / `setup_wizard` / `apply_setup` in `easy.py` | `tests/test_easy.py::test_setup_wizard_writes_config_without_the_key` |
| Website stage order, retry scope, or design-manifest compilation | `_NEXT_STAGE` and `WebsiteStateMachine` in `workflows/website.py`; `ManifestCompiler.compile` in `workflows/manifest_compiler.py` | `tests/test_website_state_machine.py::test_retry_is_local_and_cannot_choose_a_transition` |
| What the global `--config` DOES on the two public verbs, and why both must read it (2026-08-29) | `_cmd_reason` passes `config_path=args.config` into `RunPreparationRequestV1`; `_qualify_one_profile` passes the loaded `Config` into `qualification_subject_manifest`, both in `cli/main.py`. One configuration, one qualification subject: the battery `qualify` warms must be the battery a configured `reason` needs, or a configuration that compiles is one no operation can qualify (operations-parity law, 2026-08-13). The two BUILDERS agreeing is not evidence that either VERB calls them: deleting the `config=` line from `_qualify_one_profile` left the whole suite green until the two tests below were added | `tests/test_managed_path_config_read.py::test_prepare_compiles_the_run_from_the_operator_config_file` and `::test_qualify_addresses_the_subject_the_configured_run_needs` |
`check: python -m pytest tests/test_managed_path_config_read.py::test_qualify_and_reason_agree_on_the_subject_for_every_configuration tests/test_managed_path_config_read.py::test_a_configured_run_is_refused_nowhere_a_default_run_starts tests/test_managed_path_config_read.py::test_prepare_compiles_the_run_from_the_operator_config_file tests/test_managed_path_config_read.py::test_qualify_addresses_the_subject_the_configured_run_needs -q`
| `deepreason qualify`'s per-profile loop, or `deepreason status`'s per-seat section (Rung S4 of role-seat separation) | `_qualify_one_profile` (the extracted single-profile body, called once for the unchanged combination and additionally per distinct bound profile) and `_print_qualify_headline`/`_print_qualify_failure` in `cli/main.py`; `get_seat_readiness` is called from `_cmd_status`, defined in `readiness.py` (see `DR-CON-seats`, which owns that file) | `tests/test_qualification_per_seat.py::test_two_profile_home_qualifies_each_seat_plus_the_combination` |
`check: python -m pytest tests/test_v6_only_cli_admission.py::test_public_parser_omits_make_and_unqualified_advanced_commands tests/test_v6_only_cli_admission.py::test_every_shared_root_command_rejects_a_historical_manifest tests/test_v6_only_cli_admission.py::test_run_requires_qualification_before_operator_lock tests/test_v6_only_application_admission.py::test_v6_rejects_mismatched_question tests/test_v6_only_application_admission.py::test_require_v6_launch_allowed_fails_closed_for_non_v6 tests/test_application_text_runs_d0.py::test_start_intent_is_strict_and_has_no_client_authority_fields tests/test_r0_terminal_verification.py::test_run_result_exit_contract tests/test_stop_policy.py::test_corroborated_stuck_exhausts_fixed_escape_ladder_before_stop tests/test_progress.py::test_progress_is_monotonic_append_only_and_latest_is_atomic tests/test_continuation.py::test_continue_rejects_tampered_stop_digest tests/test_cli_production_doctor_v6.py::test_report_computes_19_of_20_gate_and_all_metrics tests/test_easy.py::test_setup_wizard_writes_config_without_the_key tests/test_website_state_machine.py::test_retry_is_local_and_cannot_choose_a_transition tests/test_website_state_machine.py::test_manifest_failure_selects_component_contract_repair tests/test_qualification_per_seat.py::test_two_profile_home_qualifies_each_seat_plus_the_combination tests/test_qualification_per_seat.py::test_status_two_seat_home_names_both_seats tests/test_qualification_per_seat.py::test_single_profile_home_qualify_output_is_byte_identical_to_pre_s4 -q && grep -q "^PRODUCTION_CASES_PER_PAIR = 20" src/deepreason/cli/doctor.py && grep -q "^PRODUCTION_EVENTUAL_VALID_MINIMUM = 19" src/deepreason/cli/doctor.py && grep -q "^ESCAPE_LADDER = (" src/deepreason/runtime/stop.py && grep -q "^_NEXT_STAGE = {" src/deepreason/workflows/website.py && grep -q "^PROVIDERS = {" src/deepreason/easy.py && grep -q "^MAKE_OVERRIDES = {" src/deepreason/easy.py && grep -q "^def _read_policy(" src/deepreason/runtime/launch_policy.py && grep -q "^class WebsiteStateMachine" src/deepreason/workflows/website.py && grep -q "    def compile(" src/deepreason/workflows/manifest_compiler.py && grep -q "^def _v6_run_result(" src/deepreason/application/text_runs.py && grep -q "^def _qualify_one_profile(" src/deepreason/cli/main.py && grep -q "^def _print_qualify_headline(" src/deepreason/cli/main.py && grep -q "^def _print_qualify_failure(" src/deepreason/cli/main.py && grep -q "get_seat_readiness()" src/deepreason/cli/main.py`

## Traps

- **A run could not see its own provider dying.** `ProgressEvent` carried 24
  keys and not one of them matched `transport|provider|health|fault`, and
  `deepreason results` had 17 absence codes and no provider block — so P-S1
  (run `9e48a36b1dec91ee`) ran 15 of 24 cycles against a dead provider, with 54
  typed `transport_failure` attempt objects in the record, and named them in 0
  of its 13 summary documents; its dead cycles were reported as a milestone MET.
  P-A1 (run `4565139800f5ca02`) repeated it and spent 3.27 h of a 4.94 h run on
  ten calls that returned nothing. The record held the receipts throughout —
  P-S1's `REPLAY_VALIDATION.json` even publishes `provider_transport_attempts:
  442` against `attempts: 280` — and nothing named or printed them. Fixed
  2026-09-03: one derivation (`runtime/provider_health.py`) feeds both surfaces,
  so they cannot disagree. The trap that remains is the DEFAULT: `provider_health`
  defaults to `None`, never `{}`, because an empty map on a row that measured
  nothing asserts every seat is healthy — the `token_spend` incident one field
  over, where an omitted keyword asserted a spend of zero and 20 of 59 roots
  carry the false zero. A default is not an absence.
`check: python -c "
from deepreason.runtime.progress import ProgressEvent
from deepreason.application.results import ABSENCE_REASONS
f = ProgressEvent.model_fields['provider_health']
assert f.default is None, f.default
assert 'NO_PROVIDER_ATTEMPTS' in ABSENCE_REASONS
" && grep -q "## Provider health" src/deepreason/application/results.py && grep -q "provider_health=health," src/deepreason/scheduler/scheduler.py && python -m pytest tests/test_provider_transport_faults.py -q -k "progress or results"`

- **Assuming a verb that reads a root has checked the root.** Until 2026-08-31 neither `continue` nor `amend` consulted any replay verdict, so a one-byte flip of a recorded provider endpoint bought an amendment epoch AND a resumption, while the root's own `REPLAY_VALIDATION.json` still published `valid: true` (`experiments/2026-08-31-defect-jailbreak-gate-closure/proof/RED-forge_amend_ready.txt`). Two things about the fix are easy to get wrong and were both got wrong once. FIRST, it must RE-DERIVE: the stored verdict is part of the record and forges with it. SECOND, it must ask the SECURITY channel and not `verify_root`'s whole verdict — the 2026-08-30 attempt asked the whole verdict, turned eight lifecycle tests red where its spec predicted one, and was reverted (`experiments/2026-08-30-change-checkpoint-hardening/proof/gate_collisions.md`). Three of those eight assert roads that REPAIR an invalid record, so a gate on the whole verdict strands the very roots the recovery paths exist for. The public accessor `verify_root_report(root).security_valid` is NOT the narrowing: it also counts DERIVED findings, and on the largest committed root that is 494 `transaction-authority` findings reading `unknown v6 task kind` — version skew, not tampering.
`check: python -m pytest tests/test_jailbreak_gate.py::test_a_record_that_is_merely_incomplete_still_passes_the_gate tests/test_jailbreak_gate.py::test_the_gate_agrees_with_the_reports_own_channel_classification tests/test_jailbreak_gate.py::test_a_refused_verb_writes_nothing_into_the_tampered_root -q`

- **`deepreason reason` accepted `--config` and threw it away.** The global
  flag parsed, and nothing downstream ever opened the file: `_cmd_reason` built
  a `RunPreparationRequestV1` with no configuration field at all, and
  `preparation._config_for_profile` synthesised a fresh `Config` from the
  provider profile. Every switch an operator wrote -- judges, adjudication
  authority, school seats -- was neither carried nor disclosed nor refused, and
  41 committed managed-path roots share ONE engine-config echo with zero
  compile notices to show for it. FIXED 2026-08-29, tranche
  `experiments/2026-08-29-defect-managed-path-config-read/` (defect P14). The
  companion half is the reason it is filed here rather than only under
  `DR-CON-authority`: `deepreason qualify` had no way to address a configured
  subject either, so carriage ALONE would have made all 8 committed
  `run-config.yaml` files permanently unrunnable (`QUALIFICATION_NOT_CONFIGURED`
  with no command able to clear it). Both verbs read the same flag or neither
  should.

- **The survivor count was the writer's word, and the writer was wrong.**
  `_artifacts` reported `len(result["survivors"])` verbatim, so when
  `scheduler.run_report` published import-role admission records into that set
  this surface stated them to the operator under the gloss "positions still
  standing at the end". Measured on two committed roots, not one:
  `run-1b31f006` reported 82 where the record supports 58, and
  `completed-epoch3-run-9e9812fe` reported 10 where it supports 6. FIXED
  2026-08-25 (`experiments/2026-08-25-fix-import-role-survivors/`); the reader
  now subtracts through `ontology.state.is_import_admission`. Note what the fix
  deliberately does NOT do, because the obvious version is wrong: it does not
  re-derive the survivor set from replayed state. A reader that did could
  report a survivor the record never published, and would silently
  re-adjudicate a root whose epoch moved after its payload was written.
  Subtracting is the only power a reader over an append-only record has here.
`check: python -m pytest tests/test_import_role_survivors.py::test_the_results_surface_reports_the_conjectures_and_not_the_dossier tests/test_results_command.py::test_results_summary_reports_artifact_survivor_and_frontier_counts -q`
- **The result-retrieval surface used to have no verb, and every session
  reinvented it.** Operator, 2026-08-13: "When retrieving run results, Opus 5
  keeps grepping for flags that dont exist." The facts were scattered across
  `run-status.json`, `run-result.json`, `REPLAY_VALIDATION.json`,
  `progress.jsonl` and `verify_root` with nothing in `deepreason --help`
  naming them, and the two nearest verbs actively mislead: `status` is
  PROVIDER readiness, not a run's outcome, and `findings`' help line never
  uses the word *result*. FIXED 2026-08-13 by `deepreason results`
  (`experiments/2026-08-13-change-results-retrieval-surface/`). Two shapes the
  reader had to learn from the record rather than from the schema, both of
  which a future reader will meet again: a `deepreason-run-result-v2` payload
  for a FAILED run carries `error`/`error_type` and NO `survivors`/`frontier`
  at all (counting the missing key as 0 states a result the record never
  held), and `REPLAY_VALIDATION.json`'s `verification` block is the legacy
  `{stats, violations}` shape in all 86 committed roots that carry it — the
  five-channel `finding_counts` breakdown lives in `run-result.json`.
`check: grep -q '"read a run.s typed results"' src/deepreason/cli/main.py && grep -q "NO_SURVIVOR_RECORD" src/deepreason/application/results.py && python -m pytest tests/test_results_command.py::test_a_failed_run_reports_no_survivor_set_rather_than_zero tests/test_results_command.py::test_verification_reads_the_stored_verdict_and_does_not_replay -q`
- **`easy.make` and the whole website execution path are tombstones, not code
  you can call.** `make`, `_make_single`, `_make_chunked` and `_run_stage` all
  raise `EasyV6PreparationRequired` (`V6_PREPARATION_REQUIRED`) before touching
  configuration, a root, an adapter or a provider, because managed
  question-to-run preparation is not wired to a public surface yet. Reading
  `workflows/website.py` as live behaviour is the mistake it invites: nothing
  in `cli/`, `application/` or `runtime/` names it, its one adapter hook
  `workloads.website.WebsiteWorkloadAdapter.workflow_class` has no caller at
  all, and both `run` and `start` refuse any manifest whose workload profile is
  not `text`.
`check: grep -q "V6_PREPARATION_REQUIRED" src/deepreason/easy.py && ! grep -rq "deepreason.workflows\|WebsiteWorkflow\|run_website_workflow" --include=*.py src/deepreason/cli src/deepreason/application src/deepreason/runtime && test "$(grep -roh "workflow_class()" --include=*.py src/deepreason tests | wc -l)" -eq 1 && grep -q "    def workflow_class():" src/deepreason/workloads/website.py && grep -q 'f"run requires text, got {manifest.workload_profile}"' src/deepreason/cli/main.py && grep -q "RUN_MANIFEST_WORKLOAD_MISMATCH: start_run requires a v6 text manifest" src/deepreason/application/text_runs.py && python -m pytest tests/test_easy.py::test_easy_make_requires_future_v6_preparation_before_any_side_effect tests/test_easy.py::test_internal_easy_execution_facades_are_fail_closed_tombstones -q`
- **Omitting a keyword argument ASSERTED a spend of zero, on exactly the runs
  that overspent.** The success terminal passes
  `token_spend=sum(event.llm.tokens for event in harness.log.read() if
  event.llm)`; the three FAILURE terminals passed `token_limit` and no
  `token_spend` at all, and `runtime/progress.py`'s
  `token_spend: int = Field(default=0, ge=0)` turns that omission into a
  positive claim of zero rather than a gap. So the key is PRESENT in
  `run-status.json`, the results reader's absence sentinel can never fire on
  it, and `deepreason results` printed `tokens spent vs budget: 0 / 600000`
  for a run that spent 580 016. Measured over the whole committed tree, not
  argued: **20 of 59 roots carry the false zero**, the largest a 1 193 009-token
  run — up from the 18 of 54 `RUN_ANATOMY_SYNTHESIS_2026-08-26.md` organ 10
  recorded, so the population was growing. FIXED 2026-08-29
  (`experiments/2026-08-29-fix-failure-path-token-spend/`): one shared
  `log_token_spend` derivation that all four terminals call, and a reader that
  walks the log for roots ALREADY committed with the false zero — those are
  evidence and are never edited, so recovering their truth is the only power a
  reader has. The general rule this earns: **a default is not an absence.**
  A field whose default is a legal VALUE cannot represent "not measured", so
  any writer that may skip it must pass the value explicitly or the model must
  make the gap representable. Note the reader's scope is deliberately narrow —
  it consults the log only where the sidecar says ZERO, because nine further
  roots carry a nonzero figure smaller than their log from an unrelated,
  un-diagnosed cause, and a reader that quietly re-adjudicated those would
  answer a question nobody asked (parked, that tranche's `PARKED.md`).
`check: grep -q "^def log_token_spend(harness_or_root) -> int:" src/deepreason/application/text_runs.py && grep -q "def _token_spend(status: dict | None, harness)" src/deepreason/application/results.py && python -c 'import pathlib, re; src = pathlib.Path("src/deepreason/application/text_runs.py").read_text(); calls = re.findall(r"progress\.emit\((.*?)\n\s*\)", src, re.S); terminal = [c for c in calls if re.search(r"state=\"(failed|completed|cancelled)\"", c) or "state=payload" in c]; assert len(terminal) == 4, len(terminal); assert all("token_spend=" in c for c in terminal), "a terminal progress.emit omits token_spend, which ASSERTS zero"' && python -m pytest tests/test_failure_terminal_reports_real_token_spend.py -q`
- **A correct refusal, answered with silence, published roots that lied
  about their own continuability.** `workflow/lifecycle.py` refuses to record
  a STOPPED transition while the workflow still holds unfinished authority.
  `_record_exhaustion_lifecycle_stop` caught that refusal with a bare
  `except ValueError: return None` and fell through to the bare stop record,
  so the run published `state=completed`, `stop_reason=budget_exhausted` and
  a clean `verify_root` with NO trace that its terminal transition had been
  rejected. `deepreason results` then reported *"ready for `deepreason amend`
  / `deepreason continue`: yes"* on a root `deepreason continue` refused with
  CONTINUE_TYPED_STOP_REQUIRED. Measured on four committed roots and one
  minted offline in 98 s (`cycle_soak.py --case epoch3 --cycles 3`: 11
  outstanding work orders, ZERO lifecycle decisions of any kind); epoch 1
  carried 3 and epoch 6 carried 9, so the condition was not shrinking. FIXED
  2026-08-28 (`experiments/2026-08-28-fix-swallowed-terminal-lifecycle-
  refusal/`) in three places, none of which changes any run's terminal: the
  refusal became a named type, the handler became specific and RECORDS what
  it caught as `terminal_lifecycle_refusal` in `run-result.json` and
  `run-status.json`, and the reader stopped inferring continuability from a
  stop REASON. Note what the fix deliberately does NOT do: it does not let
  the run continue. Whether unfinished authority ought to block continuation
  is an open question for the operator (parked P2); this surface only stopped
  hiding that it does. The reader's rule generalises past this defect — when
  two verbs answer one question, the reporting verb reads the ACTING verb's
  own predicate (`terminal_lifecycle_decision` / `current_resume_decision`,
  `runtime/continuation.py`), never a proxy for it.
  P2 UPDATED 2026-08-30 (`experiments/2026-08-30-change-checkpoint-hardening`),
  and only in part. The operator ruled on the law, not on this question: a
  stop that cannot assure continuability must RECORD that fact typed. So the
  two failure terminals here now carry
  `TERMINAL_LIFECYCLE_NOT_TAKEN_FAILURE_TERMINAL` and
  `TERMINAL_NO_CHECKPOINT_WRITTEN` on the same `terminal_lifecycle_refusal`
  key, so a FUTURE run of that shape says so. The 16 committed roots of that
  shape stay silent, as artifacts of their own version — no code here touches
  a committed record, and the retired cross-version law (2026-08-14) expects
  exactly that. TWO
  halves stay open, both parked with measurements in that tranche's
  `PARKED.md`: whether unfinished authority — or a failure terminal at all —
  OUGHT to permit continuation (widening `RESUMABLE_STOP_REASONS` would
  overturn owner decision 4a of 2026-07-27, "Failure terminals stay
  non-resumable"); and the integrity gate the same law asks for, which was
  built, measured, and NOT shipped — see `DR-CON-run-identity`'s Traps.
`check: ! grep -A1 "except ValueError:" src/deepreason/application/text_runs.py | grep -q "return None$" && grep -q "except UnfinishedWorkflowAuthorityError as refused:" src/deepreason/application/text_runs.py && grep -q "TERMINAL_LIFECYCLE_REFUSAL_SCHEMA = \"deepreason-terminal-lifecycle-refusal-v1\"" src/deepreason/application/text_runs.py && grep -q "def _continuation_authority(harness)" src/deepreason/application/results.py && python -m pytest tests/test_terminal_lifecycle_refusal_is_recorded.py tests/test_results_command.py::test_terminal_readiness_answers_the_amend_question -q`
- **A failure terminal that says nothing is indistinguishable from one that
  can be picked up again.** Two of the three exits of `_worker`'s single
  `except` block used to publish `state: failed` and no continuability record
  at all: the ORDINARY one writes
  `run-stop.json`, `checkpoint.json`, `run-result.json` and a progress line and
  takes NO STOPPED lifecycle receipt, so `continue` refuses
  `CONTINUE_TYPED_STOP_REQUIRED`; the NO-HARNESS one writes `run-result.json`
  and nothing else — no stop record, no checkpoint — which is the operator's
  "corrupted stop" in its purest form. Measured 2026-08-30: 16 of 59 committed
  roots hold the complete checkpoint FILE set and cannot be continued, and 15
  of the 16 carry no continuation authority at all. FIXED 2026-08-30
  (`experiments/2026-08-30-change-checkpoint-hardening`) by recording the fact,
  not by making the terminals resumable — that reading is parked as an operator
  call. NOT fixed on the third exit, the one taken when a terminal commitment
  is already open: it emits a `failed` progress line carrying
  `TERMINAL_PUBLICATION_RECOVERY_REQUIRED` as prose in `message`, writes no
  `run-result.json`, and records no refusal. Measured in that tranche's skeptic
  pass and parked as F10, because `deepreason finalize` RECOVERS that root to
  `completed` and a typed "cannot continue" left behind on a root that was
  continued would be a second wrong record, not a fix. No schema moved: `RunResultV2` is `extra="allow"` and
  `ProgressEvent.terminal_lifecycle_refusal` already existed with a default.
`check: grep -q "TERMINAL_LIFECYCLE_NOT_TAKEN_FAILURE_TERMINAL" src/deepreason/application/text_runs.py && grep -q "TERMINAL_NO_CHECKPOINT_WRITTEN" src/deepreason/application/text_runs.py && python -m pytest tests/test_checkpoint_hardening.py::test_a_failure_terminal_records_why_it_cannot_be_continued tests/test_checkpoint_hardening.py::test_a_terminal_that_wrote_no_checkpoint_records_that_fact -q`
- **There is ONE run path, and `cli/` is not allowed to be a second one.**
  The bare `deepreason run --run-manifest` path used to call
  `ops.run_scheduler` and then print. Grounded-extension run
  `8e22d0431fd2b98d` (2026-08-13) completed 24 real cycles that way and could
  not be amended, continued, cancelled, or read as a result: terminal
  authority stayed `current_open_uncommitted`, so `amend` refused
  `AMEND_NOT_AT_TERMINAL`, `continue` refused `CONTINUE_STOP_REQUIRED`, and
  `result` refused `RUN_RESULT_NOT_READY` — ten missing writers, no reader
  defect anywhere. First fixed 2026-08-13 by making the terminalization one
  shared function both paths called; SUPERSEDED the same day by deleting the
  second path outright (`experiments/2026-08-13-change-single-run-path-
  unification`), because two paths calling one function is still two places
  a lifecycle step can be forgotten. `deepreason run` is now a rendering
  shell over `TEXT_RUN_SERVICE.start_manifest_run`. The check below is
  therefore a NEGATION: `cli/main.py` must not name the scheduler at all.
  Reintroducing a scheduler call there is the same defect a third time.
`check: grep -q "^def terminalize_text_run(" src/deepreason/application/text_runs.py && ! grep -q "run_scheduler" src/deepreason/cli/main.py && grep -q "start_manifest_run" src/deepreason/cli/main.py && python -m pytest tests/test_lifecycle_operation_parity.py::test_manifest_launched_root_reaches_typed_terminal_and_accepts_amend tests/test_lifecycle_operation_parity.py::test_interrupted_run_still_refuses_amend_not_at_terminal -q`
- **`finalize` appends; it never edits.** A committed run root is immutable, so
  the only legitimate route from "stopped without a terminal" to "amendable" is
  new events and new files. `finalize_stopped_root` re-derives the frontier
  read-only through `scheduler.run_report` — no adapter is built and no model is
  called — then appends the typed stop receipt and the terminal commitment. It
  refuses `FINALIZE_ALREADY_TERMINAL` on a root that already committed one, so
  it can never republish over settled history.
`check: grep -q "^def finalize_stopped_root(" src/deepreason/application/text_runs.py && grep -q "FINALIZE_ALREADY_TERMINAL" src/deepreason/application/text_runs.py && python -m pytest tests/test_lifecycle_operation_parity.py::test_finalize_reaches_terminal_on_a_root_that_stopped_without_one tests/test_lifecycle_operation_parity.py::test_finalize_refuses_a_root_that_already_holds_a_terminal -q`
- **Deriving a report is not free of the record: constructing a `Scheduler`
  SEEDS SCHOOLS, which appends events.** Four of them, on a root whose schools
  are not yet seeded. Inside a live run that is correct; inside `finalize` it is
  not, because those events land past the reasoning horizon of a stop that
  already exists, and the root's own terminal check then fails
  `TERMINAL_POST_HORIZON_EVENT_UNAUTHORIZED`. `finalize_stopped_root` therefore
  calls the module-level `scheduler.run_report`, which is the same Pareto
  retention with no constructor. `Scheduler.report` delegates to it, so the two
  can never disagree. Measured 2026-08-13 while finalizing the
  grounded-extension root: `events before Scheduler(): 3 after: 7`.
`check: grep -q "^def run_report(" src/deepreason/scheduler/scheduler.py && grep -q "return run_report(self.harness, self.config, diagnostics=self.diagnostics)" src/deepreason/scheduler/scheduler.py && grep -q "report = run_report(harness, config_from_run_manifest(manifest))" src/deepreason/application/text_runs.py && ! grep -q "import Scheduler" src/deepreason/application/text_runs.py && python -m pytest tests/test_lifecycle_operation_parity.py::test_finalize_resumes_after_an_interrupted_terminalization -q`
- **Terminalization is not atomic, so a killed process leaves a stop with no
  commitment — and the re-run must COMPLETE it, not restart it.** A container
  snapshot killed `finalize` on the grounded-extension root between its typed
  STOPPED receipt (event seq 9947) and its terminal commitment.
  `_recoverable_typed_stop` reuses that durable stop when
  `terminal_lifecycle_decision` exists, no commitment does, and `run-stop.json`
  agrees with it on digest, sequence and reason; anything less returns `None`
  and the ordinary path records a fresh stop. Without it, the re-run writes a
  SECOND stop on one epoch.
`check: grep -q "^def _recoverable_typed_stop(" src/deepreason/application/text_runs.py && grep -q "elif (recovered := _recoverable_typed_stop(harness, root)) is not None:" src/deepreason/application/text_runs.py && python -m pytest tests/test_lifecycle_operation_parity.py::test_finalize_resumes_after_an_interrupted_terminalization -q`
- **`result()` re-derives the terminal; it does not read a file.** For a v6
  root it replays and calls `recover_terminal_result`, rewriting
  `run-result.json` when the durable authority disagrees with it. Two guards
  make that safe and are easy to break: it refuses with
  `RUN_RESULT_NOT_READY: terminalization remains active` while a process-local
  worker still holds the root, and it runs the replay *outside* the registry
  lock on purpose — holding a process-wide lock across an O(run length) replay
  serialized every start, cancel and result for every root behind one slow
  reader, and gave no safety a cross-process worker did not already need.
`check: grep -q "RUN_RESULT_NOT_READY: terminalization remains active" src/deepreason/application/text_runs.py && grep -q "Recovery runs outside the registry lock" src/deepreason/application/text_runs.py && python -m pytest tests/test_application_text_runs_d0.py::test_result_does_not_enter_recovery_while_process_local_worker_is_alive -q`
- **Recovering a terminal during a live continuation can destroy a valid
  result.** When a successor epoch has opened but not committed, the current
  commitment's publication is settled history, not an interrupted one;
  rebuilding it would overwrite a valid final result with the fail-closed
  pending projection, possibly from another process. `recover_terminal_result`
  compares `current_terminal_epoch` against the commitment's epoch and returns
  the settled publication untouched. Any new caller of the recovery path needs
  the same regression guard.
`check: grep -q "if harness.workflow_state.current_terminal_epoch > commitment.terminal_epoch:" src/deepreason/runtime/terminal_authority.py && python -m pytest tests/test_v6_resumed_terminal_revalidation.py::test_restart_recovers_stale_preceding_epoch_without_redispatch tests/test_v6_resumed_terminal_revalidation.py::test_worker_post_commit_publication_failure_preserves_terminal_authority -q`
- **A bridged run's workflow state legitimately drifts past its stop
  checkpoint.** Bridge composition appends commitment-bound transactions after
  the typed stop, so `fence.event_seq` no longer equals the harness's next seq
  and the naive equality check fails a perfectly legal continuation.
  `prepare_continuation` re-derives terminal authority and passes
  `validated_post_terminal_drift` into `build_resumed_lifecycle`; everything
  else still fails closed as `CONTINUE_TYPED_STOP_MISMATCH`. Removing that flag
  makes every bridged run uncontinuable; setting it unconditionally lets an
  unvalidated tail resume.
`check: grep -q "validated_post_terminal_drift = True" src/deepreason/runtime/continuation.py && grep -q "CONTINUE_TYPED_STOP_MISMATCH" src/deepreason/runtime/continuation.py && grep -q ") and not validated_post_terminal_drift:" src/deepreason/workflow/lifecycle.py && python -m pytest tests/test_continuation.py::test_stop_history_is_preserved_behind_latest_pointer tests/test_continuation.py::test_continue_keeps_manifest_and_appends_after_stop tests/test_continuation.py::test_continue_rejects_tampered_stop_digest tests/test_continuation.py::test_v3_continuation_requires_checkpoint -q`
- **The RECOVERY branch needs that same tolerance, and did not have it.**
  `prepare_continuation` has two paths: the terminal branch (first
  continuation) and the `current_resume is not None` branch (completing a
  crashed one). The terminal branch validates post-terminal drift; the
  recovery branch demanded `fence.event_seq == resume.resume_event_seq`,
  which is a FRESHNESS assertion that only holds when nothing was appended
  between the terminal and the resume. An amendment epoch appends exactly
  there, so a continuation crashed on an amended root was permanently
  unrecoverable — `CONTINUE_RESUME_RECOVERY_MISMATCH` forever, with every
  other field matching. Measured on grounded-extension run
  `8e22d0431fd2b98d`: fence 9949, resume 9967, stop digest and requested
  budget identical. Exact fence identity is carried by
  `run_checkpoint_digest`, which pins the file's bytes; the sequence check
  is now `fence_seq > resume_event_seq` (a fence AHEAD is still refused)
  rather than inequality. FIXED 2026-08-13.
`check: grep -q "fence_seq > current_resume.resume_event_seq" src/deepreason/runtime/continuation.py && ! grep -q 'or fence.get("event_seq") != current_resume.resume_event_seq' src/deepreason/runtime/continuation.py && python -m pytest tests/test_continuation.py::test_continue_keeps_manifest_and_appends_after_stop tests/test_continuation.py::test_continue_rejects_tampered_stop_digest tests/test_v6_resumed_terminal_revalidation.py::test_public_recovery_completes_while_original_replay_refresh_is_interrupted tests/test_v6_resumed_terminal_revalidation.py::test_restart_recovers_stale_preceding_epoch_without_redispatch -q`
- **A budget-exhausted run must end with a typed STOPPED receipt, or it can
  never be continued.** `_record_exhaustion_lifecycle_stop` gives the exhaustion
  a lifecycle receipt so `budget_exhausted` counts as resumable; a root that
  cannot take one (no owned control plane, or unfinished workflow authority)
  deliberately falls back to the bare fail-closed stop record. Both branches
  exist; deleting either changes what a budget stop means for the record.
`check: grep -q "^def _record_exhaustion_lifecycle_stop(" src/deepreason/application/text_runs.py && python -m pytest tests/test_v6_resumed_terminal_revalidation.py::test_budget_exhausted_terminal_is_a_typed_resumable_stop -q`
- **That decision changed a property an out-of-map instrument asserted, and
  nothing pointed at it.** `2d4ca2e1` moved `budget_exhausted` into
  `RESUMABLE_STOP_REASONS` and updated its own test, but
  `scripts/wheel_operational_smoke.py` had a whole stage asserting the
  opposite for a budget-exhausted run — and `docs/map/` owns nothing under
  `scripts/`, so no reader connected the two. The smoke only surfaced it on
  2026-08-05 (tranche `2026-08-05-fix-continue-run-rejection`), after three
  other defects in front of that stage were cleared. The smoke now proves
  each half against its own subject — a cancelled run for the refusal, the
  budget-exhausted run for the continuation. Changing what a stop reason
  authorizes means auditing `scripts/` too; the map cannot route you there.
  **Half fixed 2026-08-05** (`2026-08-05-fix-continue-refusal-coverage`):
  the refusal ALSO had no product test anywhere in the gate — repo-wide,
  `CONTINUE_TYPED_STOP_REQUIRED` appeared at its raise site, in the smoke's
  matcher, and in one unit test of that matcher — so the smoke, which no
  `pytest` run executes, was its only witness. `tests/test_continuation.py`
  now guards it against committed roots selected by the property that
  causes the refusal: a recorded stop reason outside
  `RESUMABLE_STOP_REASONS` (5 `operational_failure` roots today, of 28
  carrying a `run-stop.json`). The selection reads the frozenset, so
  reclassifying those stops empties the witness set and fails the guard
  rather than passing over nothing. **Still true and NOT fixed**: the
  continuation half's only end-to-end witness remains the smoke.
  **RECURRED 2026-08-15, same shape, same reason** (`a476c564f` added
  `Scheduler._premise_rent_step`, whose unconditional deferral made
  `verification.completion_satisfied` unreachable on the public reason
  path, while the smoke's `_assert_resumable_terminal` still demanded it;
  fixed 2026-08-21, `experiments/2026-08-21-fix-wheel-smoke-reason-stage/`,
  see `DR-SUB-verification`'s Traps). Twice now a `src/` change has moved a
  property only `scripts/` asserted. The rule stands and is the reason this
  entry is never deleted: changing what a stop, a phase, or a channel MEANS
  means auditing `scripts/` too, and the map cannot route you there.
`check: grep -q "^def _assert_continuation_accepted(" scripts/wheel_operational_smoke.py && grep -q "^def _await_cancellable_cycle(" scripts/wheel_operational_smoke.py && grep -q "^def _assert_non_resumable_rejection(" scripts/wheel_operational_smoke.py && python -m pytest tests/test_wheel_operational.py::test_operational_smoke_witnesses_an_accepted_continuation tests/test_wheel_operational.py::test_operational_smoke_requires_exact_non_resumable_rejection -q && grep -q "CONTINUE_TYPED_STOP_REQUIRED" src/deepreason/runtime/continuation.py && grep -q "CONTINUE_TYPED_STOP_REQUIRED" scripts/wheel_operational_smoke.py`
- **An amendment epoch supersedes the question, and only from its own durable
  workload.** `_read_request` reads the newest epoch's workload for a
  continuation while leaving the root's original `run-request.json` exactly as
  written; epoch 0 keeps the strict request/workload agreement check in
  `_spec_from_request`. Letting epoch 0 restate the question would make the
  frozen run input unenforceable, and letting a continuation ignore the epoch
  would silently rerun the superseded question. See `DR-SUB-amendment`.
`check: grep -q "Only an amendment epoch may restate the question" src/deepreason/application/text_runs.py && grep -q "^def _spec_from_request(" src/deepreason/application/text_runs.py && python -m pytest tests/test_amendment_epochs.py::test_continuation_runs_the_reshaped_question_under_the_same_root tests/test_amendment_epochs.py::test_reshaped_question_wins_the_continuation_first_cycle -q`
- **Run-root occupancy has three distinct refusals, and a leaked lock imitates
  a running run.** `_launch` refuses a root that already has `progress.jsonl`
  or `run-result.json` with `RUN_ALREADY_STARTED`, and refuses a live registry
  entry or a held operator lock with `RUN_ALREADY_RUNNING`. Because the lock is
  taken before the preparation block, every failure in between must release it
  — `_launch` wraps the block in `except BaseException: locks.release()` and
  releases again if `thread.start()` raises after the registry entry exists;
  the bridge service has the same shape for its async terminal race. Miss one
  path and the root is bricked, indistinguishably from a concurrent operator.
  `deepreason reason` sidesteps the whole question by refusing an
  operator-chosen root (`PUBLIC_REASON_ROOT_FORBIDDEN`): managed run paths are
  host-owned and derived from the question and profile, see
  `DR-CON-run-identity`.
`check: grep -q "RUN_ALREADY_STARTED: choose a fresh root or continue_run" src/deepreason/application/text_runs.py && grep -q "RUN_ALREADY_RUNNING: another operator owns this run root" src/deepreason/application/text_runs.py && grep -q "PUBLIC_REASON_ROOT_FORBIDDEN: managed run paths are host-owned" src/deepreason/cli/main.py && python -m pytest tests/test_application_text_runs_d0.py::test_worker_harness_constructor_failure_releases_operator_lock tests/test_application_bridge_service.py::test_async_terminal_race_error_releases_acquired_operator_lock tests/test_v6_only_cli_admission.py::test_reason_rejects_caller_owned_root_before_application_service -q`
- **`inspect` caches the outstanding-work projection, and the cache key is the
  durable input, not time.** A full replay per status poll is O(run length) and
  starved the worker's own terminalization replays on slow filesystems. The
  projection is a pure function of an append-only log, so identical durable
  inputs reuse the previous answer — which means a corruption introduced with
  no input change is not re-raised by a poll. Result reads and every input
  change still revalidate.
`check: grep -q "_outstanding_cache" src/deepreason/application/text_runs.py && grep -q "A full replay per status poll is O(run length) and starves the" src/deepreason/application/text_runs.py && python -m pytest tests/test_application_text_runs_d0.py::test_outstanding_work_projection_reads_replay_state_without_reducing tests/test_application_text_runs_d0.py::test_outstanding_work_projection_accepts_v6_transaction_ids -q`
