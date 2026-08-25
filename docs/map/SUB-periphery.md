<!-- DR-SUB-periphery -->
Verified-at: 748c9ab61
Verify: python -m pytest tests/test_torn_append.py tests/test_merge.py tests/test_pack_ir.py tests/test_workload_text.py tests/test_admission.py tests/test_research.py tests/test_schools.py tests/test_simulation_compiler.py tests/test_webapp.py tests/test_campaign_coordinator.py -q
Owns: src/deepreason/log/, src/deepreason/storage/, src/deepreason/evidence/, src/deepreason/admission/, src/deepreason/packs/, src/deepreason/workloads/, src/deepreason/capture/, src/deepreason/research/, src/deepreason/simulation/, src/deepreason/unification/, src/deepreason/views/, src/deepreason/ui/, src/deepreason/brain/, src/deepreason/skills/, src/deepreason/experiments/, src/deepreason/mcp_server.py, src/deepreason/webapp.py, src/deepreason/imports.py, src/deepreason/compat_eval.py
Seams: DR-SEAM-periphery-x-verification
Seams-undocumented: application x periphery, capabilities x periphery, harness x periphery, llm x periphery, manifest x periphery, periphery x scheduler, periphery x scratch

# The periphery — everything no other map document owns

## Seams

| Side | Status | What the agreement is (one line) |
|---|---|---|
| `DR-SEAM-periphery-x-verification` | documented | the evidence machinery (periphery) and replay validation agree on one durable shape: for every source bound into a run's identity, the writer's claim and the verifier's re-derivation must match |
| harness x periphery | undocumented | real, first tier: `Harness` constructs the log, object store, blob store and connectivity map by name from this package's `log/`/`storage/` — this document's own "What it is" says so directly |
| periphery x scheduler | undocumented | real: `capture/schools.py` (roster/allocation), `capture/ladder.py` (`activate_interventions` -> `respond`), and `capture/detection.py` (convergence) are all periphery-owned and directly driven by the scheduler |
| capabilities x periphery | undocumented, likely real | plausible: `simulation/` here is "the trusted simulation compiler" — likely what `DR-SUB-capabilities`'s simulation controller actually executes against, though the exact call site is not confirmed here. NOT to be confused with periphery's `research/` backends, which belong to the scheduler's OLDER `_research_step` subsystem, not to `capabilities/research.py`'s typed lifecycle (see `DR-SUB-capabilities`'s own "What it is" for that naming collision) |
| llm x periphery | undocumented | plausible, unconfirmed here: this package's `packs/` is "the deterministic pack allocator" (PackIR, section allocation — `DR-CON-packs-and-token-economy`'s territory), a different module from `llm/packs.py`'s pack RENDERING; whether one calls the other is not verified in this document |
| application x periphery | undocumented | not evidenced here either way — candidate pair, not yet analyzed |
| manifest x periphery | undocumented | not evidenced here either way — candidate pair, not yet analyzed |
| periphery x scratch | undocumented | not evidenced here either way — candidate pair, not yet analyzed |

## What it is

This is the residue of the map: the packages a run depends on that no other
document claims. Reading it as one thing is the mistake it exists to prevent,
because four unrelated tiers share the directory listing. The first is the
record's physical substrate and its inputs — the append-only file, the
content-addressed object and blob stores, evidence admission, and the frozen
run-input records — which `Harness` opens directly and every cycle touches. The
second is hot-path machinery with no epistemic authority: the deterministic pack
allocator, the workload-profile registry, school allocation and capture
detection, the research backends, the trusted simulation compiler, and the
isolation primitives. The third is operator-facing and strictly downstream —
graph views, the terminal/web/MCP front ends, cross-run memory, campaign
coordination. The fourth is not a tier but debris: `imports.py` and
`compat_eval.py` are reachable only from the retired website path or from
`scripts/`, and treating them as live behaviour is a documented failure mode.

The first tier is not peripheral in any sense except that it has no document of
its own; `Harness` constructs the log, object store, blob store and connectivity
map by name. By contrast `brain/` and `skills/` have exactly one caller in the
entire package.
`check: grep -q "^from deepreason.log.event_log import EventLog" src/deepreason/harness.py && grep -q "^from deepreason.storage.objects import SCHEMAS, ObjectStore" src/deepreason/harness.py && grep -q "^from deepreason.storage.blobs import" src/deepreason/harness.py && grep -q "^from deepreason.unification.isolation import conn_map" src/deepreason/harness.py && test "$(grep -rl "deepreason\.brain\b\|deepreason\.skills\b" --include=*.py src/deepreason | grep -vE "^src/deepreason/(brain|skills)/")" = "src/deepreason/cli/main.py"`

`imports.py` (npm resolution and bundling for accepted website manifests) has no
caller outside `easy.py` and `workflows/website.py`, both of which are the
tombstoned website path documented in `DR-SUB-application`. `compat_eval.py` has
no caller inside the package at all — only `scripts/` and its own test. Neither
is dead code to delete on sight; both are dead code to stop reading as live.
`check: ! grep -rl "deepreason\.imports" --include=*.py src/deepreason | grep -qvE "^src/deepreason/(easy\.py|workflows/website\.py)$" && grep -q "V6_PREPARATION_REQUIRED" src/deepreason/easy.py && ! grep -rq "compat_eval" --include=*.py src/deepreason && grep -q "from deepreason.compat_eval import" scripts/compatibility_eval.py && python -m pytest tests/test_easy.py::test_internal_easy_execution_facades_are_fail_closed_tombstones -q`

## Entry points

**Substrate — the bytes under the record (see `DR-SUB-harness` for what is
written, `DR-INV-frozen-surfaces` for what may not change).**

- `log.event_log.EventLog.append` / `.read` — the only writer of a run's
  `log.jsonl`, and the only reader that validates sequence and torn tails.
  `append` enforces the next sequence number and a single-writer size fence;
  `_repair_torn_tail` runs at open. `indexes.py` and `experiments/campaign.py`
  open the same file directly for derived indexes and campaign audit.
- `storage.objects.ObjectStore.put` / `.get`, and the `SCHEMAS` map that decides
  which record types exist at all.
- `storage.blobs.BlobStore.put` / `.get` / `.resolve_prefix`, plus
  `FencedBlobStore` and its `is_grounding_available` — the sealed-holdout view.
- `storage.merge.merge` — set-union another run root into this one and
  re-adjudicate.

**Run inputs — bytes to citable evidence, bound into run identity.**

- `evidence.bind_run_input` / `load_run_input` / `verify_run_input` /
  `stage_attached_source` — the frozen run-input record and its digest sidecars.
- `evidence.pack_dossier`, `render_dossier_pack`, `attach_bound_evidence`,
  `check_candidate_citations` — dossier to prompt blocks to verified quotes.
- `admission.admit_sources` with `admission.PARSER_VERSION`, and
  `admission.AdmissionStore` — the only path from user bytes to a dossier digest.

**Hot-path machinery, no epistemic authority.**

- `packs.allocate_pack` over `packs.ir.PackIR` — the single deterministic
  allocator. `llm/packs.py` is its only caller and the four `packs/render_*.py`
  modules are aliases of it; the policy lives in `DR-CON-packs-and-token-economy`.
- `workloads.WORKLOADS` (`WorkloadRegistry.register` / `.get`),
  `workloads.models.compile_interface` / `compile_interface_draft`,
  `workloads.text.seed_reasoning_workload` / `proposal_envelope`, and
  `workloads.code.snapshot_workspace` / `apply_code_patch`.
- `capture.schools.init_schools` / `roster` / `allocate` / `reseed`,
  `capture.detection.raw_flags`, `capture.ladder.respond` — school population and
  the capture instruments the scheduler polls (`DR-CON-schools`).
- `research.backends.build_service` / `run_research` / `covered` / `pending` /
  `register_evidence` — evidence acquisition for observation-valued commitments.
- `simulation.compiler.compile_declarative_numeric` /
  `validate_sandboxed_python_source` — the trusted compilers behind
  `DR-SUB-capabilities`' simulation channel.
- `unification.isolation.conn_map` / `iso` / `rank_neighbours` /
  `lineage_ref_commitment` / `relation_form_commitment`.
`check: grep -q "^class EventLog" src/deepreason/log/event_log.py && grep -q "    def append(" src/deepreason/log/event_log.py && grep -q "    def _repair_torn_tail(" src/deepreason/log/event_log.py && ! grep -rnE "open\([^)]*log\.jsonl|log\.jsonl\"\)?\.(write_text|write_bytes)" --include=*.py src/deepreason && grep -q "log_path = root / \"log.jsonl\"" src/deepreason/indexes.py && grep -q "^CANONICAL_LOG_NAME = \"log.jsonl\"" src/deepreason/experiments/campaign.py && grep -q "^class ObjectStore" src/deepreason/storage/objects.py && grep -q "^SCHEMAS: dict\[str, type\[BaseModel\]\] = {" src/deepreason/storage/objects.py && grep -q "^class BlobStore" src/deepreason/storage/blobs.py && grep -q "^class FencedBlobStore" src/deepreason/storage/blobs.py && grep -q "    def resolve_prefix(" src/deepreason/storage/blobs.py && grep -q "    def is_grounding_available(" src/deepreason/storage/blobs.py && grep -q "^def merge(" src/deepreason/storage/merge.py && for s in bind_run_input load_run_input verify_run_input stage_attached_source; do grep -q "^def $s(" src/deepreason/evidence/state.py || exit 1; done && grep -q "^def pack_dossier(" src/deepreason/evidence/dossier.py && grep -q "^def render_dossier_pack(" src/deepreason/evidence/render.py && grep -q "^def attach_bound_evidence(" src/deepreason/evidence/render.py && grep -q "^def check_candidate_citations(" src/deepreason/evidence/citations.py && grep -q "^def admit_sources(" src/deepreason/admission/parse.py && grep -q "^PARSER_VERSION = \"admission-parser.v1\"" src/deepreason/admission/parse.py && grep -q "^class AdmissionStore" src/deepreason/admission/store.py`
`check: grep -q "^def allocate_pack(" src/deepreason/packs/allocate.py && grep -q "^class PackIR" src/deepreason/packs/ir.py && grep -q "from deepreason.packs import PackIR, PackSection, allocate_pack" src/deepreason/llm/packs.py && test "$(grep -rl "deepreason\.packs\b" --include=*.py src/deepreason | grep -v "^src/deepreason/packs/")" = "src/deepreason/llm/packs.py" && for f in render_text render_code render_formal render_memory; do grep -q "^render = allocate_pack" src/deepreason/packs/$f.py || exit 1; done && grep -q "^WORKLOADS = WorkloadRegistry()" src/deepreason/workloads/registry.py && grep -q "    def register(" src/deepreason/workloads/registry.py && grep -q "^def compile_interface(" src/deepreason/workloads/models.py && grep -q "^def compile_interface_draft(" src/deepreason/workloads/models.py && grep -q "^def seed_reasoning_workload(" src/deepreason/workloads/text.py && grep -q "^def proposal_envelope(" src/deepreason/workloads/text.py && grep -q "^TEXT_WORKLOAD = TextWorkloadAdapter()" src/deepreason/workloads/text.py && grep -q "^def snapshot_workspace(" src/deepreason/workloads/code.py && grep -q "^def apply_code_patch(" src/deepreason/workloads/code.py && for s in roster init_schools allocate reseed; do grep -q "^def $s(" src/deepreason/capture/schools.py || exit 1; done && grep -q "^def raw_flags(" src/deepreason/capture/detection.py && grep -q "^def respond(" src/deepreason/capture/ladder.py && for s in build_service run_research covered pending register_evidence; do grep -q "^def $s(" src/deepreason/research/backends.py || exit 1; done && grep -q "^def compile_declarative_numeric(" src/deepreason/simulation/compiler.py && grep -q "^def validate_sandboxed_python_source(" src/deepreason/simulation/compiler.py && for s in conn_map iso rank_neighbours lineage_ref_commitment relation_form_commitment; do grep -q "^def $s(" src/deepreason/unification/isolation.py || exit 1; done`

**Operator surfaces — read-only over a finished or running record.**

- `mcp_server.call_tool` / `main` — the `deepreason-mcp` console script and the
  closed tool facade; `webapp.serve` / `create_server` is a loopback HTTP shim
  over `call_tool` and can do nothing the facade cannot.
- `ui.read_run_status` / `render_terminal_status` / `watch_run`; `views.why`,
  `views.theory`, `views.narrate`, `views.export.export_run`,
  `views.evidence.evidence`, `views.basin.threshold_calibration` — deterministic
  functions of the graph, driven by `cli/main.py`.
- `experiments.campaign.CampaignCoordinator`, `audit_root`, `load_campaign_plan`,
  `write_campaign_index` — multi-root wave scheduling and typed per-root audit
  for live campaigns. `experiments/lambda_run.py`, `criticism_voting.py` and
  `jolt_tsp.py` are single-experiment instruments, not a framework — but note
  that `programs.py` imports `experiments.jolt_tsp.parse_tour`, so one of them
  is reachable from an oracle program and is not free to change shape.
- `brain.BrainStore` / `retrieve` / `ingest_files` and `skills.retrieve_skills` /
  `snapshot_library` / `distill_capsule` — optional cross-run memory, reachable
  only through `cli/main.py`.
`check: grep -q "^def call_tool(" src/deepreason/mcp_server.py && grep -q "^def main(" src/deepreason/mcp_server.py && grep -q "^deepreason-mcp = \"deepreason.mcp_server:main\"" pyproject.toml && grep -q "^def serve(" src/deepreason/webapp.py && grep -q "^def create_server(" src/deepreason/webapp.py && grep -q "from deepreason.mcp_server import call_tool" src/deepreason/webapp.py && grep -q "^def read_run_status(" src/deepreason/ui/status.py && grep -q "^def render_terminal_status(" src/deepreason/ui/terminal.py && grep -q "^def watch_run(" src/deepreason/ui/terminal.py && grep -q "^def why(" src/deepreason/views/why.py && grep -q "^def theory(" src/deepreason/views/theory.py && grep -q "^def narrate(" src/deepreason/views/narrate.py && grep -q "^def export_run(" src/deepreason/views/export.py && grep -q "^def evidence(" src/deepreason/views/evidence.py && grep -q "^def threshold_calibration(" src/deepreason/views/basin.py && grep -q "^class CampaignCoordinator" src/deepreason/experiments/campaign.py && grep -q "^def audit_root(" src/deepreason/experiments/campaign.py && grep -q "^def load_campaign_plan(" src/deepreason/experiments/campaign.py && grep -q "^def write_campaign_index(" src/deepreason/experiments/campaign.py && grep -q "from deepreason.experiments.jolt_tsp import parse_tour" src/deepreason/programs.py && grep -q "^def parse_tour(" src/deepreason/experiments/jolt_tsp.py && grep -q "^class BrainStore" src/deepreason/brain/store.py && grep -q "^def retrieve(" src/deepreason/brain/retrieve.py && grep -q "^def ingest_files(" src/deepreason/brain/ingest.py && grep -q "^def retrieve_skills(" src/deepreason/skills/retrieve.py && grep -q "^def snapshot_library(" src/deepreason/skills/snapshot.py && grep -q "^def distill_capsule(" src/deepreason/skills/distill.py && test -f src/deepreason/experiments/lambda_run.py && test -f src/deepreason/experiments/criticism_voting.py`

## State it owns

Inside a run root: `log.jsonl` (`log/event_log.py`), `objects/<schema>/<sha256 of
the object id>.json` with the legacy flat slot still readable
(`storage/objects.py`), `blobs/<first two hex chars>/<sha256>`
(`storage/blobs.py`), and the four evidence records `run-input.json`,
`run-input.sha256`, `evidence-dossier.json`, `evidence-dossier.sha256` written
under a `ProcessLock` (`evidence/state.py`). Outside a run root:
`$DEEPREASON_HOME/admission/dossiers/<digest>.json` plus a parallel blob store
(`admission/store.py`), an optional brain directory holding `brain.json`,
`brain.log.jsonl` and its own `objects/`, `blobs/`, `indexes/`, `cards/`, `locks/`
(`brain/store.py`), and a derived, noncanonical campaign index
(`experiments/campaign.write_campaign_index`). `views/export.py` writes only the
output directory the caller names.

`packs/`, `capture/`, `research/`, `unification/` and `ui/` persist nothing at
all — they are pure functions of the record, and the only durable consequence of
calling them is whatever the caller appends through the harness. `workloads/` is
the one exception in that group: `workloads/code.py` writes into the declared
workspace root when a patch is applied.
`check: grep -q "EventLog(self.root / \"log.jsonl\"" src/deepreason/harness.py && grep -q "return self.root / schema / f\"{sha256_hex(oid.encode())}.json\"" src/deepreason/storage/objects.py && grep -q "return self.root / ref\[:2\] / ref" src/deepreason/storage/blobs.py && grep -q "^RUN_INPUT_NAME = \"run-input.json\"" src/deepreason/evidence/state.py && grep -q "^RUN_INPUT_HASH_NAME = \"run-input.sha256\"" src/deepreason/evidence/state.py && grep -q "^EVIDENCE_DOSSIER_NAME = \"evidence-dossier.json\"" src/deepreason/evidence/state.py && grep -q "^EVIDENCE_DOSSIER_HASH_NAME = \"evidence-dossier.sha256\"" src/deepreason/evidence/state.py && grep -q "RUN_INPUT_LOCK_NAME" src/deepreason/evidence/state.py && grep -q "return base / \"admission\"" src/deepreason/admission/store.py && grep -q "self.dossiers = self.base / \"dossiers\"" src/deepreason/admission/store.py && grep -q "self.manifest_path = self.path / \"brain.json\"" src/deepreason/brain/store.py && grep -q "self.log_path = self.path / \"brain.log.jsonl\"" src/deepreason/brain/store.py && grep -q 'for directory in ("objects", "blobs", "indexes", "cards", "locks")' src/deepreason/brain/store.py && grep -q "^def write_campaign_index(" src/deepreason/experiments/campaign.py && ! grep -rqE "write_text\(|write_bytes\(|os\.replace\(|mkstemp\(" --include=*.py src/deepreason/packs src/deepreason/capture src/deepreason/research src/deepreason/unification src/deepreason/ui && test "$(grep -rlE "write_text\(|write_bytes\(" --include=*.py src/deepreason/workloads)" = "src/deepreason/workloads/code.py"`

## Where to change what

| To change... | Edit | Test |
|---|---|---|
| how a prompt section is compressed, dropped, or held exact | `allocate_pack` in `packs/allocate.py`; the section flags in `packs/ir.py` | `tests/test_pack_ir.py::test_mandatory_criteria_and_output_contract_are_never_clipped` |
| add a workload profile (a new kind of run) | a `WorkloadAdapter` module under `workloads/`, registered on `WORKLOADS` in `workloads/__init__.py` | `tests/test_runtime_workload_integration.py::test_ops_forwards_bound_v6_workload_and_stop_policy` |
| what a text run's frozen spec may declare (opt-ins, sources, brain) | `ReasoningWorkloadSpec` in `workloads/text.py` | `tests/test_workload_text.py` |
| what a code workload may write, and where | `_safe_target` and `apply_code_patch` in `workloads/code.py` | `tests/test_workload_code.py::test_source_change_and_symlink_are_rejected_after_snapshot` |
| add a durable record type | `SCHEMAS` in `storage/objects.py` | `tests/test_persistence_invariants.py::test_object_store_is_namespaced_and_rejects_cross_schema_collision` |
| document segmentation, media sniffing, or admission budgets | `admission/parse.py` — and bump `PARSER_VERSION` in the same edit | `tests/test_admission.py::test_parser_version_binds_into_the_dossier_digest` |
| add an input format (PDF, EPUB, …) | an adapter in `admission/adapters*.py`, hosted by `admission/adapter_host.py` | `tests/test_admission.py::test_registered_adapter_runs_sandboxed_and_binds_into_the_digest` |
| how bound evidence reaches a pack, or how a quote is verified | `evidence/render.py`, `evidence/citations.py` | `tests/test_evidence_citations.py::test_unrecoverable_block_text_never_passes_silently` |
| where research evidence comes from (add a backend) | `build_service` and the backend classes in `research/backends.py` | `tests/test_research.py::test_backend_modes_are_distinct_and_invalid_values_fail_loudly` |
| school roster, seats per problem, cross-examiner injection | `init_schools` / `allocate` / `_with_cross_examiner` in `capture/schools.py` | `tests/test_schools.py` |
| which capture flags fire, and the response to each | `raw_flags` in `capture/detection.py`; `respond` in `capture/ladder.py` | `tests/test_orbit.py::test_ladder_rotates_the_orbiting_school` |
| the arithmetic a model-authored simulation may use | `_compile_expression` / `compile_declarative_numeric` in `simulation/compiler.py` | `tests/test_simulation_compiler.py` |
| the MCP tool surface (add, remove, or retype a tool) | `_run_tools` / `_tools` / `call_tool` in `mcp_server.py` — and FOUR pins move with it, in the same commit | `tests/test_mcp.py::test_initialize_and_tools_list_are_truthful_and_exact` |
| what stops a campaign's later waves | `AuditDimensions` / `classify_dimensions` in `experiments/campaign.py` | `tests/test_campaign_coordinator.py` |
| the browser page or its containment rules | `_Handler` in `webapp.py` | `tests/test_webapp.py::test_nonlocal_host_header_is_rejected` |
`check: grep -q "^def _compile_expression(" src/deepreason/simulation/compiler.py && grep -q "^def _with_cross_examiner(" src/deepreason/capture/schools.py && grep -q "^def _safe_target(" src/deepreason/workloads/code.py && grep -q "^def _run_tools(" src/deepreason/mcp_server.py && grep -q "^def _tools(" src/deepreason/mcp_server.py && grep -q "^class _Handler(BaseHTTPRequestHandler)" src/deepreason/webapp.py && grep -q "^def classify_dimensions(" src/deepreason/experiments/campaign.py && grep -q "^class AuditDimensions" src/deepreason/experiments/campaign.py && grep -q "^def main(" src/deepreason/admission/adapter_host.py && grep -q "deepreason.admission.adapter_host" src/deepreason/admission/adapters.py && test -f src/deepreason/admission/adapters_pdf.py && test -f src/deepreason/admission/adapters_epub.py && grep -q "^class ReasoningWorkloadSpec" src/deepreason/workloads/text.py && grep -q "WORKLOADS.register(_adapter)" src/deepreason/workloads/__init__.py && grep -q "^    droppable: bool" src/deepreason/packs/ir.py && grep -q "^    compressible: bool" src/deepreason/packs/ir.py && python -m pytest tests/test_pack_ir.py::test_mandatory_criteria_and_output_contract_are_never_clipped tests/test_runtime_workload_integration.py::test_ops_forwards_bound_v6_workload_and_stop_policy tests/test_workload_text.py tests/test_workload_code.py::test_source_change_and_symlink_are_rejected_after_snapshot tests/test_persistence_invariants.py::test_object_store_is_namespaced_and_rejects_cross_schema_collision tests/test_admission.py::test_parser_version_binds_into_the_dossier_digest tests/test_admission.py::test_registered_adapter_runs_sandboxed_and_binds_into_the_digest tests/test_evidence_citations.py::test_unrecoverable_block_text_never_passes_silently tests/test_research.py::test_backend_modes_are_distinct_and_invalid_values_fail_loudly tests/test_schools.py tests/test_orbit.py::test_ladder_rotates_the_orbiting_school tests/test_simulation_compiler.py tests/test_mcp.py::test_initialize_and_tools_list_are_truthful_and_exact tests/test_campaign_coordinator.py tests/test_webapp.py::test_nonlocal_host_header_is_rejected -q`

## `capture/` grew a SECOND instrument family at Rung 8, and they are not siblings

`capture/detection.py` measures over an EVENT window (`CAPTURE_W`, via
`harness.recent_semantic_events`) and feeds `raw_flags` -> `ladder.respond`.
`capture/diagnostics.py` implements §14's six over a SEQUENCE-NUMBER window
`W_m(n)`, and feeds declared signals and `capture/hysteresis.py`. Four
quantities carry near-identical names across the two and none of them is the
same number — the full three-population table is in `DR-INV-signal-contract`.

What keeps them from silently merging is that they share a BAND VOCABULARY and
nothing else: the hysteresis controller reuses `ATTACK_ENTROPY_FLOOR`,
`CRIT_DEBT_CEILING`, `LAMBDA_FLOOR` and `MIN_ATTACKS_FOR_RITUAL` rather than
inventing a parallel set, so a calibration lands once. That reuse is the G-4
obligation ("the existing capture instruments extend to the new surface")
discharged as code rather than as a claim.

`check: grep -q "^def window(" src/deepreason/capture/diagnostics.py && grep -q "^def diagnostics(" src/deepreason/capture/diagnostics.py && grep -q "^CAPTURE14_SIGNALS" src/deepreason/capture/diagnostics.py && python -c "from deepreason.capture.diagnostics import CAPTURE14_SIGNALS; assert len(CAPTURE14_SIGNALS) == 6"`

**No diagnostic may read wall-clock.** §15.1 puts wall-clock outside every
verdict and serialization, and a windowed instrument is the easiest place to
lose that by accident. Enforced by an AST scan over the whole module rather
than a grep, because `from datetime import datetime as dt` defeats a grep and
`.ts` matches every attribute ending in those letters.

`check: python -m pytest tests/test_capture14_diagnostics.py::test_no_diagnostic_reads_wall_clock -q`

**The age floor and the signature are both one line from being vacuous**, and
both have a test that fails against the vacuous version. `Provenance.event_seq`
defaults to 0 and almost nothing sets it, so an age derived from it would read
every artifact as maximally old; and a behavioural signature carrying ref
TARGETS would be unique for every content-addressed artifact, so SC would read
0 on every record ever made.

`check: python -m pytest tests/test_capture14_diagnostics.py::test_the_age_floor_actually_discriminates tests/test_capture14_diagnostics.py::test_stream_contraction_ignores_artifact_identity -q`

## Traps

- **Adding one MCP tool moves FOUR pins, and no gate runs two of them.**
  `tests/test_mcp.py::SUPPORTED_TOOLS` and
  `tests/test_mcp_help.py::SUPPORTED_TOOL_NAMES` fail in the ordinary suite; the
  two wheel smokes (`scripts/wheel_smoke.py`,
  `scripts/wheel_operational_smoke.py`) pin the same inventory PLUS a
  `sha256` over the whole tool-schema list, and nothing runs them for you. The
  two smokes also differ in how they compare: `wheel_smoke` compares a SET, so
  order is free, while `wheel_operational_smoke` compares a TUPLE, so declaring
  the new tool in a different position than the pin lists it fails there and
  passes everywhere else. Landing `run_standing` (Rung 4, 2026-08-22) hit
  exactly that: the tool was declared before `run_findings` and pinned after it.
`check: python -c "
import hashlib, json, pathlib
from deepreason import mcp_server
tools = mcp_server.handle({'jsonrpc':'2.0','id':1,'method':'tools/list','params':{}})['result']['tools']
sha = hashlib.sha256(json.dumps(tools, sort_keys=True, separators=(',',':')).encode()).hexdigest()
names = [t['name'] for t in tools]
for f in ('scripts/wheel_smoke.py','scripts/wheel_operational_smoke.py','tests/test_mcp.py','tests/test_mcp_help.py'):
    src = pathlib.Path(f).read_text()
    assert all(('\"%s\"' % n) in src for n in names), f
for f in ('scripts/wheel_smoke.py','scripts/wheel_operational_smoke.py'):
    assert sha in pathlib.Path(f).read_text(), f
"`
- **A crash mid-append used to swallow the NEXT event.** A torn final line has
  no trailing newline, so a post-recovery append wrote onto the fragment and the
  merged line was dropped as torn on the following read — an acknowledged,
  fsynced event lost after a clean recovery. Found by the MiniReason chaos
  battery; `_repair_torn_tail` now truncates the never-durable tail at open.
  Two neighbouring rules are load-bearing and easy to relax by accident: a bad
  line with valid lines after it is corruption and must raise, not be repaired;
  and `append` compares the file size it last wrote against the size on disk, so
  a second live `Harness` on the same root fails with `ConcurrentWriterError`
  instead of duplicating a sequence number.
`check: grep -q "^class ConcurrentWriterError" src/deepreason/log/event_log.py && grep -q "Single-writer fence" src/deepreason/log/event_log.py && grep -q "    def _repair_torn_tail(" src/deepreason/log/event_log.py && python -m pytest tests/test_torn_append.py tests/test_persistence_invariants.py::test_replay_verification_does_not_repair_a_torn_tail -q`
- **An object id has exactly one immutable meaning, and a corrupt slot is never
  deleted.** `ObjectStore.put` checks every namespaced path plus the legacy flat
  slot before writing; a same-id record with a different schema or different
  bytes raises `ObjectConflictError` rather than being resolved by write order.
  A torn target is atomically healed, but an unreadable legacy or foreign slot is
  skipped and left on disk (D8) — "clean it up" is the wrong instinct here.
  `merge` refuses a source containing `Control` events or a work-bound provider
  call, and it scans the whole source log before opening any copy loop so a
  rejection cannot half-mutate the destination. Both stores route every real
  filesystem operation through their own `_io_path`, so that a deeply nested root
  still works on Windows; a new path that calls `Path.open` or `os.stat` on
  `self.root / ...` directly passes on Linux and fails in the field.
`check: grep -q "^class ObjectConflictError" src/deepreason/storage/objects.py && grep -q "are never deleted (D8)" src/deepreason/storage/objects.py && grep -q "^class ControlEventMergeError" src/deepreason/storage/merge.py && grep -q "workflow authority must retain its original process branch" src/deepreason/storage/merge.py && grep -q "^def _io_path(" src/deepreason/storage/blobs.py && grep -q "^def _io_path(" src/deepreason/storage/objects.py && python -m pytest tests/test_persistence_invariants.py::test_object_store_is_namespaced_and_rejects_cross_schema_collision tests/test_persistence_invariants.py::test_legacy_flat_object_is_readable_and_lazily_namespaced tests/test_merge.py::test_control_source_is_rejected_before_any_destination_mutation tests/test_merge.py::test_work_bound_call_is_rejected_before_any_destination_mutation tests/test_blob_store_long_paths.py -q`
- **`PARSER_VERSION` versions the whole admission contract, not just the parser
  functions.** The sniffing rules, every segmentation and budget constant, and
  the projection formats are all covered by one monotonic identifier, because two
  parser versions must never share a dossier digest — and the dossier digest joins
  frozen run identity (`DR-CON-run-identity`). Editing `MAX_BLOCK_BYTES` or a CSV
  constant without bumping the version silently re-mints identity for the same
  input bytes.
`check: grep -q "two parser versions never share a" src/deepreason/admission/parse.py && grep -q "^MAX_BLOCK_BYTES = " src/deepreason/admission/parse.py && python -m pytest tests/test_admission.py::test_parser_version_binds_into_the_dossier_digest tests/test_admission.py::test_admission_is_deterministic_across_invocations -q`
- **An embedding threshold that has never fired reads exactly like a healthy
  run.** `RESEED_DIST_MIN` is an ABSOLUTE inter-school centroid distance, so it
  is only meaningful relative to the embedder: with the default
  `HashingEmbedder` pairwise distances run hot (~0.6–0.9), so the 0.15 that
  `config/deepseek.yaml` still ships can never trip on real content — a live run
  went out with every convergence tripwire silently off. The code default is now
  `None`, which leaves the absolute path off rather than armed and dead, so a
  profile that sets the knob at all is the case to scrutinise. That is why
  `school_convergence` in `raw_flags` has two firing paths, and the second,
  `RESEED_RATIO_MAX` over `inter_school_dist_ratio`, is scale-free and on by
  default (0.3). Calibrate any absolute embedding knob against
  `views.basin.embedder_calibration` before trusting it, and do not delete the
  ratio path in favour of the absolute one.
`check: grep -q "RESEED_DIST_MIN" src/deepreason/capture/detection.py && grep -q "can never fire on real content" src/deepreason/capture/detection.py && grep -q "inter_school_dist_ratio" src/deepreason/capture/detection.py && grep -q "^    RESEED_RATIO_MAX: float | None = 0.3" src/deepreason/config.py && grep -q "^    RESEED_DIST_MIN: float | None = None" src/deepreason/config.py && grep -q "^RESEED_DIST_MIN: 0.15" config/deepseek.yaml && grep -q "^def embedder_calibration(" src/deepreason/views/basin.py`
- **An unattended `ask-user` run gets no backend object at all.** `build_service`
  hands back `ResearchService("ask-user", None, attended=False)` on purpose: the
  scheduler must never block on, or poll for, a human who is not there, so the
  requests stay visible in the docket instead. Attended versus unattended is
  explicit configuration precisely so the distinction is replay-visible. An
  invalid `RESEARCH_BACKEND` raises at startup rather than degrading to no
  research.
`check: grep -q "the scheduler must never" src/deepreason/research/backends.py && python -m pytest tests/test_research.py::test_unattended_ask_user_never_blocks_and_attended_is_explicit tests/test_research.py::test_backend_modes_are_distinct_and_invalid_values_fail_loudly tests/test_research.py::test_null_mode_logs_research_off_once_per_episode -q`
- **A simulation observable may be a dotted name, and the schema has to say so.**
  Regression (jolt `run-b4d6dfda0c20676a864a051fbc97bda4`): the run died at cycle
  0 with `simulation observables must be plain identifiers`, four repair attempts
  never converged, and the rule appeared in neither the rendered schema nor the
  field description — the refusal was its first statement. The compiler's
  `_OBSERVABLE_NAME` is now bound to the wire's `OBSERVABLE_NAME_PATTERN` so the
  disclosed rule and the enforced rule cannot drift apart. A dotted name is a
  literal flat key, not a traversal; `_NAME` (parameters and inputs) is still
  plain identifiers only. This is the concrete instance of the "read the
  diagnostic blob before theorising" invariant.
`check: grep -q "_OBSERVABLE_NAME = re.compile(OBSERVABLE_NAME_PATTERN)" src/deepreason/simulation/compiler.py && python -m pytest tests/test_simulation_dotted_observables.py tests/test_simulation_compiler.py::test_the_conjecturer_is_shown_the_program_contract_the_harness_enforces -q`
- **The allocator never prefix-clips a whole pack, and a mandatory section can
  legally exceed the target.** A non-droppable, non-compressible section (the
  criteria, the output contract) is retained in full even past its declared
  budget; the excess is reported as `mandatory_overflow` rather than silently
  truncated. Code that treats `allocated_tokens > target_tokens` as a bug, or
  that clips the assembled text, breaks the exactness the contract depends on.
`check: grep -q "never prefix-clips a whole pack" src/deepreason/packs/allocate.py && grep -q "mandatory_overflow" src/deepreason/packs/allocate.py && python -m pytest tests/test_pack_ir.py -q`
- **The web app's containment is three separate defences, not one.** It binds
  loopback only, rejects any request whose `Host` header is not local (DNS
  rebinding), and requires a per-process token on every API call (cross-site
  request). The page carries the token, so only pages this process served can
  drive the API. Removing any one of the three leaves a local HTTP server that a
  visited web page can reach.
`check: grep -q "_LOCAL_HOSTS = " src/deepreason/webapp.py && grep -q "hmac.compare_digest(supplied, self.server.api_token)" src/deepreason/webapp.py && python -m pytest tests/test_webapp.py::test_server_refuses_to_bind_beyond_loopback tests/test_webapp.py::test_nonlocal_host_header_is_rejected tests/test_webapp.py::test_page_carries_the_token_and_api_requires_it -q`

Deserving their own documents later, in this order: `evidence/` + `admission/`
together (they define what a run may cite and they feed run identity, which is
frozen-surface adjacent); `storage/` + `log/` (the physical record under
`DR-SUB-harness`); `capture/` (schools and the capture instruments already have
`DR-CON-schools` but no owning subsystem document). `brain/`, `skills/`,
`views/`, `experiments/` and the two debris modules do not — a paragraph here is
proportionate to their coupling.
