# Spec for: one run path — "Get rid of the old one"

Traces: every item cites R/C numbers from REQUEST.md. Untraceable items
are bugs.

Map ids (from REQUEST.md's preflight): `DR-SUB-application` (owns BOTH
`application/` and `cli/`), `DR-CON-run-identity`,
`DR-INV-frozen-surfaces`.

## The measurement this spec is built on

Before designing, the managed service was driven directly against a
pre-bound, precompiled-manifest root — the exact shape
`deepreason run --run-manifest` operates on — to find out how much of
S1's "widen the door" is actually missing.

M0 (probe, offline, no provider): `TEXT_RUN_SERVICE.start(...,
manifest_override=manifest)` on `tests/test_lifecycle_operation_parity`'s
own `_bind_v6_root` fixture root:

    SPEC MATCHES: True
    STATE: completed
    STOP: budget_exhausted
    EXIT: 0
    WITH MANIFEST: current_valid_committed valid: True
      run-stop.json: True
      checkpoint.json: True
      workflow-checkpoint.json: True
      run-result.json: True
      REPLAY_VALIDATION.json: True
      run-request.json: True
      text-workload.json: True
      progress.jsonl: True
    AMEND EPOCH: 1 sources: 1

**The door is already wide.** `_launch` never inspects roles, judge
ensembles, schools, or `criticism_policy`; it validates schema version,
workload profile, run-input agreement and qualification, then hands
`config_from_run_manifest(manifest)` to the scheduler. So R2's "no
narrowing" is a property of the EXISTING service, and S1's work is a
typed entry point that supplies the three things a `run` caller has and
`start()`'s intent does not accept directly: a manifest OBJECT already
bound at the root, an optional `--problem` file, and `--token-budget`
absent.

M1 (the one genuine incompatibility found): `budget_intent(cycles=1,
token_budget=None)` raises

    ValidationError: 2 validation errors for RunBudgetIntentV1
    token_budget.int  Input should be a valid integer [input_value=None]
    token_budget.literal['unlimited']  Input should be 'unlimited'

`run --token-budget` defaults to `None`; the intent vocabulary spells
that `"unlimited"`. The alias must translate.

## Items

### S1 — widen the door (R1, R2, R3, C5, C7)

**S1.1 (R1)** | `src/deepreason/application/text_runs.py` |
before: the only entries are `start(intent, manifest_override=...)`,
which requires a caller to have already built a `ReasoningWorkloadSpec`
and a `RunBudgetIntentV1`, and `continue_run`. There is no entry a
caller holding only (root, manifest, optional problem file, cycles,
token budget) can use. | after: a new public method
`TextRunApplicationService.start_manifest_run(*, root, manifest,
problem_path=None, cycles, token_budget=None, progress_callback=None,
credential_checker=missing_manifest_credentials) -> RunStartedV1` that

  - accepts `manifest` as a `RunManifest` OBJECT or as a path to a
    `run-manifest.json` (resolved with `load_run_manifest`);
  - resolves the workload with the existing
    `workload_spec_for_root(root, problem_path=..., harness=...)`,
    opening a READ-ONLY harness only when the root already has a
    `log.jsonl` (a fresh root has no commitments to reconstruct from and
    must not be written to before `_launch` decides it may be);
  - translates `token_budget=None` to `"unlimited"` (M1);
  - builds the intent with `start_text_run_intent` and delegates to
    `self.start(intent, manifest_override=manifest, ...)`, so exactly
    one `_launch` exists.

  It adds NO validation of its own. Every refusal a manifest can earn is
  already `_launch`'s, which is what makes R2 true by construction rather
  than by enumeration.

  accept: `python -m pytest tests/test_single_run_path.py::test_service_entry_accepts_a_precompiled_manifest_object_and_a_manifest_path -q`
  -> `2 passed` equivalent (1 test, parametrized over object/path)

**S1.2 (R2, C7)** | new test | before: nothing asserts the service
declines to narrow the configuration space. | after: a test compiles a
manifest carrying a **judge role ensemble**, **school-routed conjecture**
and a **`criticism_policy`**, binds it to a root, and asserts
`start_manifest_run` reaches scheduler dispatch (stubbed) rather than any
refusal — and, separately, that `start_manifest_run` contains no
role/policy inspection at all.

  accept: `python -m pytest tests/test_single_run_path.py::test_the_door_narrows_no_configuration_the_compiler_admits -q`
  -> `1 passed`

**S1.3 (R3)** | new test | before: the grounded tranche's config can only
enter through `build_manifest.py` + the bare CLI path. | after: a test
imports `experiments/2026-08-12-live-grounded-extension-expansion/
build_manifest.py`, calls `build(root)` under a tmp `DEEPREASON_HOME`,
and drives that exact root through `start_manifest_run`.

  Verified reachable before speccing (the named-mechanism rule): running
  the script offline against a tmp root produced

      "manifest_sha256": "8e22d0431fd2b98dc915c66f2f3ccc6dc43184b4c326ff5d388a7c013a80989d"
      "run_input_digest": "f6e488fd77c89b067283ca2bb38658e91022e9e39a27b8edb8ba7b0417d25377"
      "evidence_dossier_digest": "3155b3d79c781e1b0866623934de6ae7ca10ca0c9aae0f776a535c16ef505c31"
      "compile_notices": []

  — byte-identical to the live grounded run's own manifest digest
  `8e22d0431fd2b98d`, so the fixture is the real configuration, not a
  lookalike.

  accept: `python -m pytest tests/test_single_run_path.py::test_the_grounded_tranche_config_enters_through_the_new_door -q`
  -> `1 passed`

### S2 — alias the verb (R4, R5, R6)

**S2.1 (R4)** | `src/deepreason/cli/main.py` `_cmd_run` | before: after
preflight it acquires the operator lock itself and calls
`_execute_bound_run`, which runs the scheduler inline. | after: `_cmd_run`
keeps, unchanged and in the same order, its budget parse,
`_admit_v6_root`, `--run-manifest` conflict check, workload-profile check,
`require_v6_launch_allowed` (non-dry-run only), `require_full_engine`,
`--problem` preflight (`_require_v6_workload_match` + `preflight_payload`)
and the `--dry-run` render-and-return-0 branch; then, instead of
qualifying and locking itself, calls

      TEXT_RUN_SERVICE.start_manifest_run(...) -> .wait(root) -> .result(root)

  and renders. `require_v6_production_qualification` and
  `operator_locks` are REMOVED from `_cmd_run` — not dropped but
  relocated: `_launch` performs both, qualification first, exactly the
  order the CLI performed them in. Leaving the CLI's lock in place would
  make the service's own non-blocking acquisition fail
  `RUN_ALREADY_RUNNING` against the caller itself.

  The parser is untouched: same verb, same flags, same defaults.

  accept: `git diff --stat origin/main -- src/deepreason/cli/main.py` shows
  `build_parser` unchanged, proved by
  `python -m pytest tests/test_single_run_path.py::test_run_verb_parser_surface_is_byte_identical -q`
  -> `1 passed` (pins the `run` subparser's option strings, defaults and
  `required` flags against a literal expected table)

**S2.2 (R5)** | `src/deepreason/cli/main.py` | before: `_cmd_run` returns
`0` for any scheduler completion and `1` for every typed refusal;
`run_result_exit_code` is never consulted on this path. | after:
outcomes that produce a terminal return `terminal.exit_code()` — i.e.
`application/models.py::run_result_exit_code` — and refusals raised
BEFORE a terminal exists keep returning `1`, unchanged. Regression-pinned
both ways.

  This is the reading recorded in A3; it keeps `completed -> 0` (what
  every ladder branches on) and makes `failed`/`cancelled`/`invalid`
  distinguishable instead of collapsed into `1`.

  accept: `python -m pytest tests/test_single_run_path.py::test_run_exit_code_contract_is_run_result_exit_code tests/test_single_run_path.py::test_run_preflight_refusals_still_exit_one -q`
  -> `2 passed`

**S2.3 (R6)** | no file changes | before/after: the only committed ladder
invoking this verb is
`experiments/2026-08-12-live-grounded-extension-expansion/grounded_run.sh`,
which runs `python -m deepreason --root "$ROOT" run --budget cycles=24
--token-budget 1000000` and branches on rc alone. `completed` stays `0`
and every failure stays non-zero (S2.2), so the script is unaffected. It
is NOT edited.

  accept: `git diff --stat origin/main -- experiments/*/**.sh` -> empty

### S3 — delete the old road (R7, R8, R9)

**S3.1 (R7)** | `src/deepreason/cli/main.py` | before: `_execute_bound_run`
(≈117 lines) holds a second, parallel implementation of the run
lifecycle: its own `Harness(...)`, its own `--problem` seeding, its own
`ProgressSink` construction and single `running/workload/loaded` emission,
its own `ensure_lifecycle_documents` / `attach_bound_evidence_once` calls
(the lifecycle tranche's bare-path retrofit), its own `run_scheduler`
call, its own `terminalize_text_run` call, and its own rendering. | after:
the function does not exist. Everything it did is `_launch`/`_worker`'s,
which does it for every configuration.

  accept: `! grep -q "_execute_bound_run" src/deepreason/cli/main.py` and
  `test -z "$(grep -rn '_execute_bound_run' --include='*.py' src tests scripts)"`
  -> both exit 0

**S3.2 (R8)** | `experiments/2026-08-13-change-single-run-path-unification/proof/dead-census.txt` |
before: no census. | after: the two-scan `dr-audit-dead` discipline over
every symbol the change deletes — scan 1 repo-wide reference count before
deletion, scan 2 after — pasted into VALIDATION.md, with an explicit row
per symbol. Deleted symbols at spec time: `_execute_bound_run` only. The
census must also prove no OTHER symbol became unreferenced as a
consequence (`ops.run_scheduler`, `attach_bound_evidence_once`,
`ensure_lifecycle_documents`, `completed_cycles`, `workload_spec_for_root`
each lose their `cli/main.py` caller and MUST retain callers elsewhere —
if one does not, that is a finding, not a silent deletion).

  accept: `proof/dead-census.txt` exists, lists every symbol with
  before/after counts, and every non-target symbol shows a surviving
  caller.

**S3.3 (R9)** | `tests/test_lifecycle_operation_parity.py`,
`tests/test_v6_global_dispatch_guard.py`,
`tests/test_v6_only_cli_admission.py` | before: three tests reach the old
road directly. | after: each asserts the SAME property through the alias.
Nothing is deleted.

  | test | today | migrates to |
  |---|---|---|
  | `test_lifecycle_operation_parity.py::_launch_through_cli` (helper for 6 tests) | calls `cli_module._execute_bound_run(...)` | drives `main(["--root", root, "run", "--budget", "1", "--problem", ...])` with the scheduler and qualification stubbed |
  | `test_v6_global_dispatch_guard.py::test_execute_bound_run_v6_launch_policy_precedes_harness` | calls `_execute_bound_run` with V6 disabled, asserts no `Harness` and `not root.exists()` | asserts the same through `_cmd_run` — V6_LAUNCH_DISABLED before any `Harness`, root untouched |
  | `test_v6_only_cli_admission.py::test_run_requires_qualification_before_operator_lock` | patches `deepreason.locking.operator_locks` | patches `deepreason.application.text_runs.operator_locks` — the binding the service actually calls (`text_runs.py` imports it at module level, so the old patch target no longer proves the ordering) |

  accept: `python -m pytest tests/test_lifecycle_operation_parity.py tests/test_v6_global_dispatch_guard.py tests/test_v6_only_cli_admission.py -q`
  -> `0 failed`, and the three files' `def test_` counts are unchanged or
  higher (`grep -c "^def test_"` before/after, pasted).

### S4 — prove nothing moved that must not (R10, R11, R12, R13)

**S4.1 (R10)** | new test | before: no fixture pins run identity through
this road. | after: a test asserts (a) compiling the acceptance fixture
twice yields the identical `manifest.sha256`
(`8e22d0431fd2b98dc915c66f2f3ccc6dc43184b4c326ff5d388a7c013a80989d`), and
(b) the run id the root's own `progress.jsonl` records equals that digest
— `DR-CON-run-identity`'s rule that for a manifest-launched root
`run_id == manifest.sha256`, now written by the ONE path.

  accept: `python -m pytest tests/test_single_run_path.py::test_run_identity_is_deterministic_through_the_one_road -q`
  -> `1 passed`

**S4.2 (R11)** | `DELIVERY.md` | before: nothing states the delta. |
after: DELIVERY.md carries an explicit table of what a
`run --run-manifest` root gains and what it loses, stated as the PURPOSE.
Gains (already true of the managed path, now true of every root):
per-cycle progress events and cancellation checks, `display_status_counts`
in the progress stream, resumable typed stop receipts, dossier attachment
at seed through `_worker`'s own `attach_bound_evidence` rather than a
separate retrofit, the operational-failure terminal branch, and
`run-result.json` recovery through `result()`.
Losses, stated plainly and not hidden: `_cmd_run`'s two rendering lines
that no longer have a source — the scheduler `[note]` diagnostics and the
raw `meter.snapshot()` JSON — and the narrowing in A5.

  accept: `grep -q "paths before = 2, paths after = 1" DELIVERY.md` and the
  gains/losses table present.

**S4.3 (R12)** | `experiments/.../proof/replay.txt` | before: no proof. |
after: `verify_root_report` run READ-ONLY over the committed
grounded-extension root plus two other committed roots, output pasted into
VALIDATION.md, compared against the standing sweep baseline
(`docs/AUDIT_BASELINES.md`: 11 ERROR lines, all
`UnsupportedRunManifestVersionError`). Per CLAUDE.md's own sweep rule —
"when no reader changed, the previous sweep IS the current answer" — this
change alters no reader (it deletes a writer path and reuses the surviving
writer unchanged), so the targeted report is the instrument and the full
10-minute sweep is not re-run. That reasoning is recorded, not assumed.

  accept: `proof/replay.txt` pasted in VALIDATION.md, every root's `valid`
  matching its prior recorded verdict.

**S4.4 (R13)** | no file changes | `mcp_server.py`'s `start_run` and the
qualification battery's dispatch are not touched.

  accept: `git diff --stat origin/main -- src/deepreason/mcp_server.py src/deepreason/qualification.py`
  -> empty

### R14–R20 — process and artifacts

**S5.1 (R14)** — see "Frozen-surface contact forecast" below. Verdict
`CLEAR`; the stop is armed but not triggered.

**S5.2 (R15)** | ring while iterating (`tests/test_single_run_path.py`,
`tests/test_lifecycle_operation_parity.py`,
`tests/test_v6_global_dispatch_guard.py`,
`tests/test_v6_only_cli_admission.py`,
`tests/test_application_text_runs_d0.py`,
`tests/test_run_manifest.py`, `tests/test_workload_text.py`,
`tests/test_engine_profile_dispatch.py`); full gate
(`python -m pytest tests/ -q -n 4`) at the phase boundary; full
`python tools/docs_verify.py` (NOT `--fast`) before any commit touching
`src/`. Baselines: `docs/AUDIT_BASELINES.md` — 1 pre-existing pytest
failure (`test_bronze_report.py::test_census_totals_internally_consistent`)
and, on this shallow clone, 3 `CON-run-identity.md` git-history
docs_verify failures.

  accept: both instrument outputs pasted in VALIDATION.md, deltas against
  baseline = 0.

**S5.3 (R16)** | `docs/map/SUB-application.md`,
`docs/map/CON-run-identity.md` | before: both describe two launch paths
calling one terminalization, and both carry a `check:` that will FAIL the
moment S3 lands:

    SUB-application.md:201  grep -q "terminalize_text_run(" src/deepreason/cli/main.py
    CON-run-identity.md:241 grep -q "terminalize_text_run(" src/deepreason/cli/main.py

  | after: both rewritten to describe ONE path, with checks that would
  fail if a second one reappeared — i.e. the negation is now the
  guarantee:

    ! grep -q "run_scheduler" src/deepreason/cli/main.py
    grep -q "start_manifest_run" src/deepreason/cli/main.py

  Specifically: `SUB-application.md`'s entry-points list gains
  `start_manifest_run` and drops `cli.main._execute_bound_run`; its
  "Where to change what" row for "What ANY finished run writes at stop"
  is restated for one path; its Traps entry on the bare path is
  REWRITTEN (never deleted — SCHEMA.md) to say the split was closed by
  unification and when. `CON-run-identity.md`'s
  "Every launch path's one shared route to a terminal" row loses
  "(called by `_worker` AND by `cli.main._execute_bound_run`)", and its
  "Assuming a root that ran real cycles can be continued" trap gains the
  second date.

  R16's "SEAM-application-x-cli (or first-time-document it if the matrix
  says unwritten)" resolves to NEITHER branch, for a reason recorded in
  REQUEST.md's map preflight: `SUB-application.md`'s `Owns:` covers
  `src/deepreason/application/` and `src/deepreason/cli/` alike, so
  application × cli is not a seam between two documents — it is internal
  to one. Writing `SEAM-application-x-cli.md` would violate `SCHEMA.md`'s
  ID grammar (a seam joins two subsystem/concept documents) and would
  create a document `docs_verify --links` could not resolve. Recorded as
  a deviation from R16's literal wording, delivered as R16's property.

  Map documents move in the SAME commit as the code (CLAUDE.md).

  accept: `python tools/docs_verify.py` -> failures == baseline, and
  `git log --oneline -1 --name-only` for the S3 commit lists both map
  files.

**S5.4 (R17)** | `scripts/wheel_smoke.py` | before: pins
`"deepreason = deepreason.cli.main:main"` (line 33). | after: unchanged —
this tranche adds and removes no console entry point, and changes no MCP
tool or schema. If a smoke pin moves, all four pin locations move in the
same commit; the expectation is that none does.

  accept: `python scripts/wheel_smoke.py` -> exit 0 with no pin edit in
  the diff (`git diff --stat origin/main -- scripts/`  -> empty).

**S5.5 (R18)** | `docs/ERRATA.md` (next free number **E26** — the tail is
E25), `CLAUDE.md` | before: two committed statements describe the
two-path arrangement as the mechanism. `CLAUDE.md:299-301` (the
operations-parity law): "The mechanism is therefore ONE shared
implementation both paths call — `application/text_runs.py::
terminalize_text_run` — never a copy". `docs/map/CON-run-identity.md:55`:
"called by `_worker` AND by `cli.main._execute_bound_run`". Neither was
false when written and neither claimed permanence in so many words, which
is exactly why an entry is owed: a reader auditing them after this tranche
finds two paths described where one exists. | after: E26 records both,
says what remains true (the law itself — the mechanism sentence was the
means, not the law), and names this tranche. `CLAUDE.md`'s mechanism
sentence is updated in the same commit; the operator's verbatim quote in
that law is NOT touched.

  accept: `grep -q "E26" docs/ERRATA.md` and
  `! grep -q "both paths call" CLAUDE.md` and
  `grep -q "available to all configurations" CLAUDE.md` (the operator's
  words survive verbatim).

**S5.6 (R19)** | process | commit and push at every phase boundary and
every `[COMMIT]` step, `git push -u origin
claude/single-run-path-unification-bhn2ob` with 2s/4s/8s/16s retry.

  accept: `git log origin/claude/single-run-path-unification-bhn2ob` shows
  a commit per boundary.

**S5.7 (R20)** | `DELIVERY.md` | R-by-R reconciliation with pasted PROOF
per requirement, closing with the literal census line
`paths before = 2, paths after = 1, operations reachable from it = all`.

  accept: `grep -q "paths before = 2, paths after = 1, operations
  reachable from it = all" DELIVERY.md` and every R1–R20 appears in the
  reconciliation table.

## Assumptions (operator may override)

A1 (Q1): **The new door takes a precompiled manifest — object or path —
not a run-config YAML.** Assumed, operator may override. Smallest reading
and the one the fixture proves: `compile_run_manifest` needs
`run_input_digest`, `control_plane_policy`, `criticism_policy`,
`inquiry_capability_policy` and `toolchains` from the caller (see
`build_manifest.py:147-166`); a service that compiled YAML would have to
invent those, which is the compiler's job and `deepreason config compile`'s
surface, not the run service's. R2's substance — "any manifest the
compiler emits, the service runs" — is delivered in full by S1.2.

A2 (Q2): **"Exact CLI surface" = the verb, its flags and defaults, its
synchronous blocking behavior, and its exit contract.** Assumed, operator
may override. Stdout keeps the `survivors (N):` block, the frontier lines
and the rendered theory, all now derived from the published terminal
payload. Two lines lose their source and are dropped: the scheduler's
`[note]` diagnostics (never persisted anywhere) and the raw
`meter.snapshot()` JSON (the meter is constructed inside `run_scheduler`
and the worker discards it; its information survives as
`accounting` in `run-result.json` and as `token_spend` in
`progress.jsonl`). No committed test or ladder asserts either line —
census in "Blast-radius census" below.

A3 (Q3): **Terminal outcomes exit through `run_result_exit_code`;
pre-terminal refusals keep exiting `1`.** Assumed, operator may override.
R5 names `run_result_exit_code` as "the rc exit-code contract", and this
reading satisfies both R5 and R6 at once: `completed` is `0` under old and
new behavior alike, and every failure stays non-zero, so
`grounded_run.sh`'s `if` branch cannot observe the difference. The gain is
that `cancelled` (3), `failed` (4) and integrity-invalid (5) stop
collapsing into `1`.

A4 (Q5): **The acceptance fixture is `build_manifest.build(root)` called
from the test, under a tmp `DEEPREASON_HOME`.** Assumed, operator may
override. Verified reachable and offline (S1.3's pasted digests).

A5 (Q4 + a narrowing this design creates): **`_cmd_run` keeps everything
up to and including `--dry-run`; only the dispatch tail is replaced.** One
behavior narrows as a consequence, and it is recorded here rather than
discovered later: a SECOND `deepreason run` on a root that already has
`progress.jsonl` or `run-result.json` now refuses
`RUN_ALREADY_STARTED: choose a fresh root or continue_run`, because that
is `_launch`'s rule for every configuration
(`DR-CON-run-identity`: "A root that has already run may never be started
again"). Today's bare path re-enters such a root silently. The successor
operation is `deepreason continue`, which this same unification makes
available to these roots. This narrowing is the direct consequence of C5
("parity by construction") and is stated in DELIVERY.md's delta table.

A6 (Q6): **R12's "targeted" = `verify_root_report` over the
grounded-extension committed root and two others, not the 42-root
sweep.** Assumed, operator may override. Justified by CLAUDE.md's own
rule that a committed root's verdict can move only if the READER moved,
and this change moves no reader. Cost avoided: ~10 minutes per sweep.

A7: **`workload_spec_for_root` opens a read-only harness only when the
root already carries a `log.jsonl`.** Assumed; the alternative
(constructing a writable `Harness` to resolve a spec) writes to a root
before `_launch` has authorized the launch, which is the ordering
`DR-CON-run-identity` pins.

## Questions for operator (STOP if non-empty)

(none — every open question above resolved from the record or the
operator's ledgered laws; each is recorded as an assumption the operator
may override)

## Out of scope (explicit)

- `mcp_server.py::start_run` — R13 places it out of scope explicitly.
- The qualification battery's own dispatch — R13, same.
- `deepreason reason` / `_cmd_reason` — already the managed path; not
  requested.
- `_cmd_reason_shallow` / MiniReason — a third engine, not a second run
  path; not requested.
- The `easy.make` / `workflows/website.py` tombstones — dead already, not
  requested.
- Making `deepreason run` resume an already-started root by routing to
  `continue_run` — a plausible kindness, not requested (A5 records the
  refusal instead).
- `_cmd_code`, `_cmd_simulate`, `_cmd_proof` — they call
  `_bind_cli_manifest`, not the run path; not requested.

## Frozen-surface contact forecast

Computed, not hand-checked — `python tools/blast_radius.py --files
src/deepreason/cli/main.py src/deepreason/application/text_runs.py
src/deepreason/application/models.py src/deepreason/application/intents.py
--symbols _execute_bound_run _cmd_run start _launch start_text_run_intent
run_result_exit_code`:

    "frozen_surface_contacts": []
    "frozen_adjacent_contacts": []
    "frozen_surface_verdict": "CLEAR"
    "reachability": [
      {"symbol": "_execute_bound_run",   "status_current": "REACHABLE"},
      {"symbol": "_cmd_run",             "status_current": "REACHABLE"},
      {"symbol": "start",                "status_current": "REACHABLE"},
      {"symbol": "_launch",              "status_current": "REACHABLE"},
      {"symbol": "start_text_run_intent","status_current": "REACHABLE"},
      {"symbol": "run_result_exit_code", "status_current": "REACHABLE"}
    ]
    "qualification_digest": []

No `UNKNOWN` reachability entry. **No STOP.** This matches R14's
expectation ("none are expected — this is application-layer
consolidation"): the change adds no manifest field, alters no validator,
writes no new record shape, and touches no digest input. The one record
this tranche causes to be written on roots that previously lacked it —
the terminal commitment — is written by the UNCHANGED
`terminalize_text_run`, i.e. no new observable enters the typed record, so
§4's record-observable guardrails and the sweep-probe requirement do not
apply and no `tools/root_sweep.py` probe is proposed.

## Blast-radius census

From the same gate run, `consumers.tests` and `consumers.map_checks`,
every hit classified. Hits on `start` (85 test locations) are the existing
managed-path callers and are listed as a group because the method's
signature and behavior do not change; the new entry only calls it.

| target | consumer | classification |
|---|---|---|
| `_execute_bound_run` | `tests/test_lifecycle_operation_parity.py:136` | EXPECTED TO MOVE (S3.3 migration) |
| `_execute_bound_run` | `tests/test_v6_global_dispatch_guard.py:1051` | EXPECTED TO MOVE (S3.3 migration) |
| `_execute_bound_run` | `docs/map/CON-run-identity.md:55` | EXPECTED TO MOVE (S5.3) |
| `_execute_bound_run` | `docs/map/SUB-application.md:68` | EXPECTED TO MOVE (S5.3) |
| `_cmd_run` | `tests/test_v6_global_dispatch_guard.py:1035`, `:1090` | MUST NOT MOVE (preflight + dry-run behavior preserved by S2.1) |
| `start` | 85 locations across 40 test files | MUST NOT MOVE (signature and behavior unchanged) |
| `_launch` | `tests/test_v6_only_application_admission.py:414` | MUST NOT MOVE |
| `start_text_run_intent` | `tests/test_v6_only_application_admission.py:21`, `:398` | MUST NOT MOVE |
| `run_result_exit_code` | `tests/test_r0_terminal_verification.py:14`, `:58`; `tests/test_v6_compact_recovery_reporting.py:14`, `:307` | MUST NOT MOVE (the function is reused, not changed) |
| `src/deepreason/cli/main.py` | `docs/map/SUB-application.md:40,111,141,176,190,201,328` | 201 EXPECTED TO MOVE (its `terminalize_text_run(` grep breaks on deletion); 40/111/141/176/190/328 MUST NOT MOVE |
| `src/deepreason/cli/main.py` | `docs/map/CON-run-identity.md:130,241` | 241 EXPECTED TO MOVE (same grep); 130 MUST NOT MOVE |
| `src/deepreason/cli/main.py` | `docs/map/SUB-periphery.md:44`, `SUB-manifest.md:140`, `SUB-amendment.md:139`, `SUB-verification.md:232`, `SEAM-schools-x-scheduler.md:81` | MUST NOT MOVE |
| `src/deepreason/application/text_runs.py` | `docs/map/SUB-application.md` (16 lines), `CON-run-identity.md:4,241`, `SUB-scheduler.md:63`, `SUB-amendment.md:139` | MUST NOT MOVE except the two lines above; the file gains a method and loses nothing |
| `src/deepreason/application/models.py`, `intents.py` | `docs/map/SUB-application.md:111` | MUST NOT MOVE (neither file is edited) |
| wheel-smoke pin | `scripts/wheel_operational_smoke.py` (tier PLAUSIBLE, target `start`) | MUST NOT MOVE (S5.4) |

Manual cross-check, required where the gate cannot resolve a symbol shape
(here: CLI verb strings and stdout text, which are not Python
identifiers):

    grep -rn 'survivors (' tests/ scripts/ docs/
      -> 2 hits, both prose: tests/test_thesis.py:43 (docstring),
         docs/harness-spec-v1.3.md:259. No test asserts the run verb's
         "survivors (N):" stdout line.
    grep -rn 'meter.snapshot' tests/ scripts/
      -> 10 hits, all direct AggregateMeter unit assertions
         (test_v6_profile_authority, test_v6_transaction_qualification,
         test_school_execution_binding_v4). None reads the run verb's
         stdout; the meter object itself is untouched by this change.
    precise census of `main([... "run" ...])` call sites    -> 5 test files, 12 lines
      test_engine_profile_dispatch.py:138  (--dry-run, UNSUPPORTED_RUN_MANIFEST_VERSION)   MUST NOT MOVE
      test_run_manifest.py:1059,1067,1093  (--dry-run / pre-v6 refusals)                   MUST NOT MOVE
      test_v6_only_cli_admission.py:262    (parser: --experimental-v5 rejected)            MUST NOT MOVE
      test_v6_only_cli_admission.py:385    (qualification ordering)                        EXPECTED TO MOVE (S3.3)
      test_workload_text.py:172            (--dry-run, prints sha256)                      MUST NOT MOVE
      test_v6_global_dispatch_guard.py:273,363,724,956,995 (scheduler call-order fixtures) MUST NOT MOVE

No committed shell script other than `grounded_run.sh` invokes the verb
(`grep -rln 'run --run-manifest\|deepreason run ' experiments/ --include=*.sh`
-> 1 file), and it branches on rc only.

## Budget

Itemized insertions, and the headline is their computed sum:

       55  S1 service entry start_manifest_run (text_runs.py) + __all__
        2  S1 export in application/__init__.py
       55  S2 _cmd_run alias body (cli/main.py, new lines)
        0  S3 deletion of _execute_bound_run (insertions; ~117 deletions)
      130  S4/R9 new tests tests/test_single_run_path.py
       40  R9 migrations in 3 existing test files
       35  R16 map: SUB-application.md
       20  R16 map: CON-run-identity.md
       28  R18 docs/ERRATA.md E26
        8  R18 CLAUDE.md mechanism sentence
      ----
      373  insertions total

    $ python3 -c "print(sum([55,2,55,0,130,40,35,20,28,8]))"
    373

**~373 insertions, ceiling 400, 4 commits.** Frozen surfaces touched:
none (gate verdict `CLEAR`).

Over the ~300-line split threshold, and a split is explicitly REJECTED
with its reason: S3 cannot land without S2, S2 cannot land without S1,
and the two map `check:` greps at `SUB-application.md:201` /
`CON-run-identity.md:241` fail the instant S3 lands — so the map must ride
the same commit, and CLAUDE.md's mechanism sentence describes the state
S3 ends. The only genuinely separable ~36 lines are E26 + the CLAUDE.md
sentence, and separating them would leave a committed document describing
two paths after the second one is gone, which is the exact failure R18
exists to prevent. Ordered commits within this one tranche instead:

1. `[COMMIT]` S1 — the door + its three tests (green before anything is
   deleted; both paths still exist and both still pass).
2. `[COMMIT]` S2 + S3 — the alias, the deletion, the three test
   migrations, and BOTH map documents.
3. `[COMMIT]` S4 proofs + E26 + CLAUDE.md.
4. `[COMMIT]` VALIDATION.md / DELIVERY.md.

Rubric: 6/6 yes
- every R has a spec item with a machine-decidable accept? yes (R1→S1.1,
  R2→S1.2, R3→S1.3, R4→S2.1, R5→S2.2, R6→S2.3, R7→S3.1, R8→S3.2,
  R9→S3.3, R10→S4.1, R11→S4.2, R12→S4.3, R13→S4.4, R14→S5.1, R15→S5.2,
  R16→S5.3, R17→S5.4, R18→S5.5, R19→S5.6, R20→S5.7)
- blast-radius census pasted and every hit classified? yes
- frozen-surface contact forecast recorded from the gate's own output?
  yes — `CLEAR`, list pasted verbatim
- every mechanism the request names traced to code it actually reaches?
  yes — `build_manifest.py` executed offline (S1.3 digests),
  `run_result_exit_code` read (S2.2), `terminalize_text_run` reached by
  the probe (M0)
- DESIGN-AND-STOP only: n/a (this is an implementing tranche)
- nothing untraceable to an R/C number? yes — anti-invention pass run;
  the only non-R content is the map-id preflight, which C-traces to
  CLAUDE.md's own map rule
