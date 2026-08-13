# INVENTORY.md — lifecycle operations: managed path vs manifest-launched root

Satisfies R2. Every verdict is proved against the REAL stopped root
`experiments/2026-08-12-live-grounded-extension-expansion/run` (9 947
events, RunManifest v6, `manifest_sha256=8e22d0431fd2b98d…`), launched by
`deepreason run --run-manifest` (`grounded_run.sh`). Write-probes ran
against a byte-copy of that root in the session scratchpad; the committed
root was never written to.

## Diagnosis first (R5, R6) — which hypothesis the record supports

The record decides between the tranche's two hypotheses:

- **(a) the bare `run` path never WRITES the terminal-commit record** —
  **CONFIRMED.**
- **(b) amend's reader does not RECOGNIZE the records this config style
  produced** — **REFUTED.** The reader is correct; there is nothing for
  it to read.

Proof, verbatim tool output:

    AUTHORITY: {'schema': 'terminal-authority-derivation.v1',
      'status': 'current_open_uncommitted',
      'manifest_sha256': '8e22d0431fd2b98dc915c66f2f3ccc6dc43184b4c326ff5d388a7c013a80989d',
      'terminal_epoch': None, 'terminal_status': None,
      'canonical_bridge_eligible': None, 'terminal_commitment_ref': None,
      'result_draft_ref': None, 'reasoning_event_horizon_seq': None,
      'terminal_commitment_event_seq': None, 'stop_record_digest': None,
      'detail_code': None}
    next_seq: 9947
    current_terminal_commitment: None
    current_terminal_epoch: 0
    terminal_lifecycle_decision: None
    root files: ['.make-operator.lock', '.run-input.lock', '.run-manifest.lock',
      '.run-operator.lock', 'blobs', 'evidence-dossier.json',
      'evidence-dossier.sha256', 'log.jsonl', 'objects', 'problem.json',
      'production-contract-qualification.json', 'relapse.log.jsonl',
      'run-input.json', 'run-input.sha256', 'run-manifest.json',
      'run-manifest.sha256']

`derive_terminal_authority` reaches `current_open_uncommitted` through
exactly one branch (`runtime/terminal_authority.py:738-743`):
`workflow_state.current_terminal_commitment is None` **and**
`run-result.json` absent. Both hold. The manifest DOES require a
commitment — `terminal_commitment_policy … required=True` — so this is a
root that was obliged to commit a terminal and never did.

**The exact missing records**, named against what
`amendment/apply.py::_require_terminal_stop` needs:

| # | Missing record | Who writes it on the managed path | Consequence |
|---|---|---|---|
| 1 | the `run-stop` MEASURE event (or the typed STOPPED lifecycle CONTROL event) | `text_runs.py::_worker` lines 1023-1059 | no reasoning event horizon exists |
| 2 | `run-stop.json` + `run-stops/<seq>-<digest>.json` | `runtime/stop.py::persist_stop_record` | `CONTINUE_STOP_REQUIRED` |
| 3 | `checkpoint.json` | `_worker` lines 1060-1068 | `CONTINUE_CHECKPOINT_REQUIRED` |
| 4 | `workflow-run-terminal-commitment-v1` object + its CONTROL event | `ensure_terminal_commitment` via `_v6_run_result` | `AMEND_NOT_AT_TERMINAL` |
| 5 | `workflow-checkpoint.json` sealed at the commitment | `_seal_terminal_commitment_checkpoint` | commitment unverifiable |
| 6 | `run-result.json` | `_worker` line 1094 | `RUN_RESULT_NOT_READY` |
| 7 | `REPLAY_VALIDATION.json` (with `terminal_binding`) | `finalize_terminal_result` | no replay-bound result projection |
| 8 | `run-request.json`, `text-workload.json` | `_launch` lines 851-855 | `RUN_REQUEST_MISSING` |
| 9 | `progress.jsonl` | `ProgressSink` in `_launch`/`_worker` | run reads as `not-started` |
| 10 | import-role `attached-source-record.v1` artifacts | `attach_bound_evidence` in `_worker` line 952 | 6 `attached-evidence` violations |

None of these is a *reader* defect. Every one is a *writer* that only the
managed path calls.

## The operation inventory (R2)

`W` = works · `B` = broken (the operation exists and is reachable, but
refuses on this root) · `N` = never-wired (the bare path never performs
it at all).

| # | Lifecycle operation | Managed path (`TEXT_RUN_SERVICE` / `deepreason reason`) | Manifest-launched root (`deepreason run --run-manifest`) | Proof |
|---|---|---|---|---|
| 1 | bind manifest + write `run-request.json` / `text-workload.json` | `_launch` → `bind_run_manifest`, `_atomic_json` | **N** | `_read_request(root)` → `RUN_REQUEST_MISSING: fixed run-request.json is absent` |
| 2 | seed workload | `seed_reasoning_workload` | **W** (via `--problem`) | root carries `problem.json` (`deepreason-text-workload-v1`) and 2 882 problems replay |
| 3 | `attach_bound_evidence` (render bound dossier into import-role records) | `_worker` (schema ≥ 5) | **N** | `import-role artifacts in log: 0` against `bound dossier sources: 6`; `verify_root` reports 6 × `attached-evidence` |
| 4 | progress emission (`progress.jsonl`) | `ProgressSink` throughout | **N** | `progress.jsonl: False`; `inspect(lifecycle)` → `not-started` after 9 947 events |
| 5 | `inspect` / `watch` / `status` | `TEXT_RUN_SERVICE.inspect` | **B** — returns `not-started` for a finished run | `[inspect(lifecycle)] OK -> not-started` |
| 6 | `inspect_outstanding_work` | replay projection | **W** | `process_digest sha256:a0822a89e last_control_seq 9943 work 0` |
| 7 | `cancel` | `TEXT_RUN_SERVICE.cancel` | **B** | `[cancel] ValueError: RUN_NOT_ACTIVE: current state is not-started` |
| 8 | stop record (typed STOPPED lifecycle receipt / bare stop) | `_record_exhaustion_lifecycle_stop` / `write_stop_record` | **N** | no `run-stop.json`; `prepare_continuation` → `CONTINUE_STOP_REQUIRED` |
| 9 | run fence `checkpoint.json` | `_worker` | **N** | file absent |
| 10 | capability audits (`write_tranche_a_audits`) | `_worker` (schema ≥ 5) | **N** | `capability audit files present: []` |
| 11 | terminal commitment (`ensure_terminal_commitment`) | `_v6_run_result` | **N** | `current_terminal_commitment: None`, authority `current_open_uncommitted` |
| 12 | terminal result publication (`finalize_terminal_result`, `REPLAY_VALIDATION.json`) | `_worker` line 1093 | **N** | neither file exists |
| 13 | `result` / `recover_terminal_result` | `TEXT_RUN_SERVICE.result` | **B** | `[result] ValueError: RUN_RESULT_NOT_READY: current terminalization is not-started` |
| 14 | **`amend`** (append an amendment epoch) | works on managed roots | **B** | `[amend --attach README.md] AmendmentError: AMEND_NOT_AT_TERMINAL: amendment requires a run standing at a valid typed terminal stop (terminal authority is current_open_uncommitted)` |
| 15 | **`continue`** | `TEXT_RUN_SERVICE.continue_run` | **B** | `prepare_continuation ValueError: CONTINUE_STOP_REQUIRED`; and `_read_request` → `RUN_REQUEST_MISSING` |
| 16 | read-only views (`theory`, `why`, `evidence`, `export`, `findings`, `trace`) | — | **W** | the ladder's own `findings.json` (1.8 MB) was produced from this root |
| 17 | compiled-config launch (`--run-manifest`) | **N** on the managed path — `deepreason reason` mints its own manifest via `RunPreparationService` and has no `--run-manifest` flag | **W** | `cli/main.py:285-326` (`reason` parser: `--cycles`, `--token-budget`, `--shallow`, `--dossier`, `--attach`, `--allow-partial`; no manifest flag); `cli/main.py:2240-2247` |

Row 17 is the parity gap in the other direction, and it is the first half
of the operator's sentence: *"The new generic reason run doesn't
recognise the new config style."* Rows 1, 3, 4, 8-15 are the second half:
*"nor does 'append'."*

## Why the gap exists (single structural cause)

`cli/main.py::_execute_bound_run` (lines 2768-2822) calls
`ops.run_scheduler` and then **prints**. `text_runs.py::_worker` (lines
902-1109) calls the same `ops.run_scheduler` and then performs steps
1-12. Everything in the table above that is `N` lives in the ~90 lines of
`_worker` that follow the scheduler call and have no counterpart on the
CLI side. The behaviour was never shared, so it never propagated —
precisely the failure mode `ops.py`'s own module docstring was written to
prevent ("the behavior lives here exactly once so a fix to seeding or run
setup cannot land on one surface and drift on the other").

## GATE verdict (C2)

**Proceed.** Reaching a valid typed terminal on this root requires only
APPENDED typed records and NEW files; not one committed byte is edited.
Proved on a byte-copy of the real root:

    owned v4/v6 control: True
    lifecycle stop: {"digest": "a02da10aee3f9a431d569afd808b24e5458395ba34478035a3a194ecf2017d9b",
      "event_seq": 9947, "metrics": {..., "cycle": 24, ...},
      "policy_digest": "76a98a16373c7575acfc41e8877c17b2f3476622cb06f8cbcefc8d388101b147",
      "reason": "budget_exhausted", "schema": "deepreason-run-stop-v1"}
    terminal_lifecycle_decision: True
    next_seq now: 9948

The typed STOPPED lifecycle receipt is the one that matters: `continue`
on an owned v6 control plane refuses with `CONTINUE_TYPED_STOP_REQUIRED`
unless `workflow_state.terminal_lifecycle_decision` exists
(`runtime/continuation.py:351`). It does now, and it was produced by
appending one CONTROL event at seq 9947 — the same event the managed path
appends at its own stop.

## Contradiction found between R7 and the record (reported, not silently resolved)

R7 asks for `deepreason amend` "admitting the six dossier documents as
attached evidence". Those six documents are **already bound** in epoch
0's dossier (they are exactly what the six `attached-evidence` violations
name). `amendment/apply.py::_admit_supplement` refuses a content digest
that any bound dossier already carries:

    AMEND_SOURCE_ALREADY_ADMITTED: … is already admitted as src-…
    An amendment admits new evidence only; drop the already-admitted
    file(s) and re-run

The refusal's own recorded rationale is *"re-admitting one adds no
evidence while producing a second introduction that replay validation
rejects."* Neither half holds for this root: the first introduction never
happened (0 import-role artifacts), so re-admitting **does** add
evidence, and there is no second introduction to reject. `SPEC.md`
resolves this as S6 — a narrow widening of the refusal, not a bypass.
