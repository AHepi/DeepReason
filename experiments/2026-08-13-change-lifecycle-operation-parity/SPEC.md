# Spec for: lifecycle-operation parity — "The flags and operations available to the newer reason runs should be available to all configurations"

Traces: every item cites R/C numbers from `REQUEST.md`. Untraceable items
are bugs. The diagnosis and operation census this spec builds on are
`INVENTORY.md` (satisfies R2, R5, R6 in full).

## Items

**S1 (R1, R3) — one shared terminalization, called by both paths.**
Files: `src/deepreason/application/text_runs.py`.
Before: the ~90 lines following `run_scheduler` inside
`TextRunApplicationService._worker` (lines 1021-1094) are the ONLY
implementation of stop-record → `checkpoint.json` → capability audits →
`_v6_run_result` → `finalize_terminal_result` → `run-result.json`, and
they are unreachable from any other caller.
After: that block becomes a module-level
`terminalize_text_run(harness, manifest, *, root, report, accounting,
problem_id, cancelled, scheduler_stop_reason, latest_cycle,
capability_accounting=True)` returning the published payload;
`_worker` calls it and keeps only its progress emission. Exactly one
implementation exists (the parity mechanism — a copy would drift, which
is the failure `ops.py`'s own module docstring names).

    accept: python -m pytest tests/test_r0_terminal_verification.py \
      tests/test_v6_terminal_commitment_authority.py \
      tests/test_application_text_runs_d0.py -q
      -> 0 failed
    accept: python -c "from deepreason.application.text_runs import
      terminalize_text_run; print(terminalize_text_run.__module__)"
      -> deepreason.application.text_runs

**S2 (R1, R3) — the bare `run` path performs the full lifecycle.**
Files: `src/deepreason/cli/main.py` (`_execute_bound_run`).
Before: calls `ops.run_scheduler` and prints; writes no stop record, no
commitment, no result, no progress (INVENTORY rows 1, 4, 8-13).
After: for a v6 manifest it (a) ensures the lifecycle documents exist
(S4), (b) opens a `ProgressSink` and emits `starting`/`running`/terminal
events, (c) calls `attach_bound_evidence` when it is seeding a fresh root
whose manifest binds a dossier (S5), and (d) calls
`terminalize_text_run` after the scheduler returns. Pre-v6 roots are
untouched — the manifest gate is `schema_version == 6`, exactly the gate
`_v6_run_result` already uses.

    accept: a fixture v6 root launched through `_cmd_run` ends with
      run-stop.json, run-stops/, checkpoint.json, workflow-checkpoint.json,
      run-result.json, REPLAY_VALIDATION.json, progress.jsonl all present
      and `derive_terminal_authority(...).status == "current_valid_committed"`
      (tests/test_lifecycle_operation_parity.py::test_manifest_launched_root_reaches_typed_terminal)

**S3 (R4, C1) — `deepreason finalize`, the append-only route to terminal
for a root that stopped without terminalizing.**
Files: `src/deepreason/cli/main.py` (parser + `_cmd_finalize`),
`src/deepreason/application/text_runs.py` (`finalize_stopped_root`).
Before: no operation exists; such a root is permanently
`current_open_uncommitted` (INVENTORY, "Diagnosis first").
After: `deepreason --root ROOT finalize [--json]` derives the run report
read-only (`Scheduler(harness, None, config).report()`), records the typed
STOPPED lifecycle receipt, and runs the same `terminalize_text_run`. It
writes ONLY new files and APPENDS ONLY new log events; it never opens an
existing byte for modification. It refuses, typed, when the root already
holds a valid terminal (`FINALIZE_ALREADY_TERMINAL`), when a run is live
(`FINALIZE_RUN_ACTIVE`), or when the manifest is not v6
(`FINALIZE_MANIFEST_UNSUPPORTED`).

    accept: on a byte-copy of the real grounded root,
      `deepreason --root <copy> finalize --json` exits 0 and
      `derive_terminal_authority` returns current_valid_committed
    accept: `git status --short experiments/2026-08-12-live-grounded-extension-expansion/`
      after finalizing the REAL root shows only ADDED files plus the
      appended `log.jsonl` — every other tracked file byte-unchanged
      (`git diff --stat` names log.jsonl and nothing else)

**S4 (R1, R3) — `ensure_lifecycle_documents`.**
Files: `src/deepreason/application/text_runs.py`.
Before: `run-request.json` and `text-workload.json` are written only by
`_launch`; `_read_request` fails `RUN_REQUEST_MISSING` on a
manifest-launched root, so `continue` cannot start (INVENTORY row 15).
After: a module-level `ensure_lifecycle_documents(root, *, spec)` writes
both documents when absent and refuses (`RUN_REQUEST_CONFLICT`) rather
than replacing different bytes. The spec is the root's own
`problem.json` when present (it already carries schema
`deepreason-text-workload-v1` — measurement M1), otherwise it is rebuilt
from `run-input.json`. Called by S2 and S3.

    accept: after `finalize` on the grounded-root copy,
      `_read_request(root)` returns a dict whose `problem.id` equals
      `run-input.json`'s `problem.id`
    accept: calling it twice is a no-op (byte-identical documents)

**S5 (R1, R3) — bound evidence is rendered on the bare path too.**
Files: `src/deepreason/cli/main.py` (`_execute_bound_run`).
Before: `attach_bound_evidence` is called from exactly two places
(`text_runs.py`, `amendment/apply.py`) and never from the CLI run path —
the cause of the grounded root's 6 `attached-evidence` violations
(INVENTORY row 3).
After: `_execute_bound_run` calls it once, immediately after problem
registration and before any scheduler dispatch, when the manifest
schema is ≥ 5 and the root's log carries no import-role source record
yet. Idempotent by that guard.

    accept: a fresh fixture root launched via `_cmd_run` with a bound
      dossier ends with `verify_root(root)["violations"] == []`

**S6 (R7, R8) — an amendment may admit a source that was BOUND but never
INTRODUCED.**
Files: `src/deepreason/amendment/apply.py` (`_admit_supplement`).
Before: any content digest present in any bound dossier is refused
`AMEND_SOURCE_ALREADY_ADMITTED`, whose recorded rationale is
*"re-admitting one adds no evidence while producing a second
introduction that replay validation rejects."*
After: the refusal keeps its exact code, message, and force for a source
that HAS a source record on the log — the case the rationale describes.
A source that is bound but has no `attached-source-record.v1` artifact
carrying it is admitted: no first introduction exists, so there is no
second one, and admitting it does add evidence. The discriminator is
computed from the log, not from a flag.

    accept: tests/test_lifecycle_operation_parity.py::
      test_amend_refuses_a_source_already_on_the_log (unchanged refusal)
    accept: tests/test_lifecycle_operation_parity.py::
      test_amend_admits_a_bound_but_unintroduced_source
    accept: python -m pytest tests/test_amendment_epochs.py
      tests/test_amendment_chain_integrity.py -q -> 0 failed

**S7 (R1) — parity for `continue` and `amend` follows from S1-S6.**
No new code. `continue` needs `run-stop.json` + `checkpoint.json` +
`terminal_lifecycle_decision` + `run-request.json`; `amend` needs
`current_valid_committed`. S2/S3 produce all five.

    accept: on the finalized grounded-root copy,
      `prepare_continuation(root, cycles="8", tokens="500000",
      check_operator_lock=False)` returns a continuation record
    accept: `amend_run(copy, attach=[...six paths...])` returns an
      amendment-result-v1 summary

**S8 (R14) — every committed root still replays byte-unchanged.**
Files: none (validation obligation).

    accept: `python tools/root_sweep.py` -> zero verdict drift vs
      docs/AUDIT_BASELINES.md
    accept: targeted `verify_root_report` on one known-good committed
      root, pasted in VALIDATION.md

**S9 (R9) — ledger the standing operator design law.**
Files: `CLAUDE.md` (§Operator design laws).
After: a new law, "**Operations are available to every configuration**
(2026-08-13, operator's words verbatim: 'The flags and operations
available to the newer reason runs should be available to all
configurations.')", written as the operations-parity sibling of the
2026-08-12 all-configurations law and landing in the SAME commit as its
enforcing code (S2/S3).

    accept: `grep -c "available to all configurations" CLAUDE.md` -> ≥1,
      and `git show --stat <commit>` names both CLAUDE.md and
      src/deepreason/cli/main.py

**S10 (R10) — the regression pair.**
Files: new `tests/test_lifecycle_operation_parity.py`.
Two named obligations, plus the supporting cases above:
`test_manifest_launched_root_reaches_typed_terminal_and_accepts_amend`
and `test_interrupted_run_still_refuses_amend_not_at_terminal`. The
second is the guard that the refusal stays CORRECT for genuinely open
runs — it builds a root with reasoning events and no stop and asserts the
exact code `AMEND_NOT_AT_TERMINAL`.
Prediction (R10, "Tests asserting the old gap flip with SPEC.md's
prediction"): **no existing test asserts the old gap.** The blast-radius
census below lists every test that touches a target; none asserts that a
manifest-launched root cannot amend, continue, or terminalize. If the
full gate contradicts this prediction, the contradiction is recorded in
VALIDATION.md and the fixture is minimally updated only where this spec
predicted it.

    accept: `python -m pytest tests/test_lifecycle_operation_parity.py -q`
      -> 0 failed, ≥6 passed

**S11 (R11, R16) — gates and cadence.** Ring while iterating (the test
files named in each accept line); full gate
`python -m pytest tests/ -q -n 4` at the phase boundary; full
`python tools/docs_verify.py` before any commit touching `src/`; commit
and push at every phase boundary with 2s/4s/8s/16s retry.

    accept: VALIDATION.md carries pasted `N passed, 0 failed` and
      docs_verify `0 failed`

**S12 (R12) — the map moves in the same commits.**
Files: `docs/map/SUB-application.md` (the terminalization block moves out
of `_worker`; the CLI run path gains it), `docs/map/SUB-amendment.md`
(the narrowed duplicate refusal), `docs/map/CON-run-identity.md` (a
manifest-launched root is now a full lifecycle citizen). Each gains a
`check:` command that would FAIL if the behaviour regressed, and a
`Traps` entry naming the grounded-extension run.

    accept: `python tools/docs_verify.py` -> 0 failed
    accept: `python tools/docs_verify.py --audit` -> no check that
      cannot fail

**S13 (R13) — errata.**
Files: `docs/ERRATA.md`, next free number **E25** (ledger tail measured —
M3).
Any committed document claiming amend/continue work for all run types
gets the entry. The census is part of the item: `grep -rn` over
`docs/` for amend/continue universality claims; if the census finds
none, E25 records the *census result and the newly-true state* rather
than a correction, so a future reader knows the claim was checked.

    accept: `docs/ERRATA.md` contains a section beginning `**E25 —`

**S14 (R7, R8, R15) — the live proof.**
Files: `experiments/2026-08-12-live-grounded-extension-expansion/RESULTS.md`
(new dated segment), plus this tranche's `LIVE.md`.
Sequence on the REAL root: `finalize` → `amend --attach` (the six
dossier documents) → `continue --budget cycles=8 --token-budget 500000`
at `DEEPREASON_QUALIFY_CONCURRENCY=2`. Typed outcomes only.
Qualification-digest drift is REPORTED, never a stop (R15).

    accept: RESULTS.md gains a dated segment naming: the amendment
      epoch's attached source record count and provenance role, the
      NEW-violation delta from `verify_root`, the count of continued-cycle
      criticism citing an imported source, judge verdict counts, and the
      residue

## Assumptions (operator may override)

A1 (Q1) — **"append" names the amendment's evidence append (`amend
--attach`), not a `deepreason append` subcommand.** Assumed, operator may
override. Smallest reading and the only one the code admits: there is no
`append` subcommand in `cli/main.py` (measurement M2), and the operator's
own sentence pairs it with the `AMEND_NOT_AT_TERMINAL` evidence, which is
`amend`'s refusal. The append-only record write itself is not an operator
operation.

A2 (Q2) — **parity is delivered by making the compiled-config launch path
(`deepreason run --run-manifest`) lifecycle-complete, not by adding
`--run-manifest` to `deepreason reason`.** Assumed, operator may
override. With S2 in place a compiled-config run gets every operation the
managed path has, which is what the operator's sentence asks for; adding
a second surface that does the same thing is a distinct change (launch-path
parity, not operation parity) and is PARKED with that reason, not dropped.

A3 (Q3) — **continuation concurrency is not settable at continue time.**
Assumed, operator may override. The bound manifest freezes route
concurrency for the run's whole life; `DEEPREASON_QUALIFY_CONCURRENCY=2`
governs the qualification battery only. The live proof therefore sets the
environment variable the ladder set and reports the manifest's own
concurrency as the operative number.

A4 (Q4) — **an amendment epoch's appended source records CAN satisfy the
attached-evidence check for that epoch.** Assumed, operator may override;
verified rather than trusted at S14. The check windows each epoch as
`[fence, next_fence)` and computes `first_llm_seq` within the window,
defaulting to `next_fence` when the window holds no LLM event
(`invariants.py:2110-2114`) — so records appended into a fresh amendment
epoch arrive strictly before that epoch's first model call.
**Consequence the operator did not predict, flagged now:** because
`source_records` accumulates across epochs and the final check is over the
union (`invariants.py:2157-2161`), records supplied by the amendment epoch
may CLEAR the epoch-0 violations rather than leaving them standing. C5
says report, do not chase — so whichever way it lands is reported as
measured, and no code is written to force either outcome.

## Questions for operator (STOP if non-empty)

None. Every fork above was decided from the record or from the operator's
own pre-granted authority (C3), and each decision is recorded as an
assumption the operator can override.

## Out of scope (explicit)

- `deepreason reason --run-manifest` — not requested as a separate
  surface; see A2. PARKED.
- Fixing the grounded root's epoch-0 `attached-evidence` violations —
  explicitly excluded by C5.
- Any change to `verify_root`'s attached-evidence rule — not requested;
  A4 shows none is needed.
- Website/simulation workload parity — not requested.
- Retro-finalizing any OTHER committed root — not requested; the sweep
  (S8) proves they stay byte-identical precisely because nothing touches
  them.

## Frozen-surface contact forecast

`tools/blast_radius.py` output, computed and pasted verbatim
(`--files src/deepreason/application/text_runs.py
src/deepreason/cli/main.py src/deepreason/amendment/apply.py --symbols
terminalize_text_run finalize_stopped_root _execute_bound_run _worker
_v6_run_result _record_exhaustion_lifecycle_stop _admit_supplement
_cmd_run attach_bound_evidence`):

    "frozen_surface_contacts": [
      {"surface": "replay-validation record formats (invariants.py)",
       "tier": "SYMBOL_INDIRECT",
       "target": "attach_bound_evidence",
       "detail": "'attach_bound_evidence' referenced in src/deepreason/invariants.py (grep-based; not proof of semantic contact)"}
    ],
    "frozen_adjacent_contacts": [],
    "frozen_surface_verdict": "CONTACT"

    "reachability": [
      {"symbol": "terminalize_text_run", "status_current": "UNKNOWN"},
      {"symbol": "finalize_stopped_root", "status_current": "UNKNOWN"},
      {"symbol": "_execute_bound_run", "status_current": "REACHABLE"},
      {"symbol": "_worker", "status_current": "UNREACHABLE"},
      {"symbol": "_v6_run_result", "status_current": "UNREACHABLE"},
      {"symbol": "_record_exhaustion_lifecycle_stop", "status_current": "UNREACHABLE"},
      {"symbol": "_admit_supplement", "status_current": "REACHABLE"},
      {"symbol": "_cmd_run", "status_current": "REACHABLE"},
      {"symbol": "attach_bound_evidence", "status_current": "REACHABLE"}
    ]

    "disclosure_summary": "This change touches 1 of the five frozen
    surfaces (locked-down files that a change can silently corrupt old,
    already-recorded runs by touching): replay-validation record formats
    (invariants.py). 3 declared symbol(s) already have no live call path
    today, independent of this change: _worker, _v6_run_result,
    _record_exhaustion_lifecycle_stop. 5 test file(s) and 7 map
    document(s) assert on the touched targets today. ..."

**Verdict `CONTACT` — and the operator's words over this exact disclosed
surface are already in hand, in advance, as C3:** *"PRE-GRANTED (scoped,
additive/widening only): surface 2 (harness.py) and surface 3 (replay
readers) as far as writing/recognizing the terminal and amendment records
for manifest-launched runs requires."* The single contact is surface 3,
reached through `attach_bound_evidence` — the exact symbol the pre-grant
names by function. C4 ("no stops beyond the one gate below") makes this a
disclosure, not a stop.

**What this spec actually does to surface 3: nothing.** No item changes
`invariants.py`, any replay-validation record format, any manifest
schema, or `harness.py`. S5 CALLS the existing `attach_bound_evidence`
from a third call site; S6 changes when an amendment admits a source,
which is a writer decision the reader already accommodates (A4). The
pre-grant is therefore disclosed and, on this design, unused. If
implementation discovers a real reader change is required, that is a new
STOP.

Manual cross-check retained for the two `UNKNOWN` reachability entries
(the gate cannot resolve symbols that do not exist yet):

    $ grep -rn "terminalize_text_run\|finalize_stopped_root\|ensure_lifecycle_documents" tests/ docs/map/ src/
    NO HITS (new symbols)

## Blast-radius census

From the same `tools/blast_radius.py` invocation, `consumers.tests` and
`consumers.map_checks`, every hit classified.

**Tests:**

| Target | Hit | Classification |
|---|---|---|
| `_execute_bound_run` | `tests/test_v6_global_dispatch_guard.py:1051` | EXPECTED TO MOVE — the function gains lifecycle wiring; the guard asserts dispatch refusal, so the assertion itself must not move, only the fixture's post-conditions if it inspects the root |
| `_worker` | `tests/test_simulation_dotted_observables.py:33,44` | MUST NOT MOVE |
| `_worker` | `tests/test_v6_only_application_admission.py:417,491` | MUST NOT MOVE |
| `_worker` | `tests/test_wheel_operational.py:291` | MUST NOT MOVE |
| `_v6_run_result` | `tests/test_r0_terminal_verification.py:19,143` | MUST NOT MOVE — S1 moves the CALLER, not this function |
| `_v6_run_result` | `tests/test_v6_bridge_transactions.py:21,325,361,400` | MUST NOT MOVE |
| `_v6_run_result` | `tests/test_v6_compact_recovery_reporting.py:17,284,475` | MUST NOT MOVE |
| `_v6_run_result` | `tests/test_v6_insufficient_capability_reporting.py:16,129,157,382` | MUST NOT MOVE |
| `_v6_run_result` | `tests/test_v6_resumed_terminal_revalidation.py:760,810` | MUST NOT MOVE |
| `_v6_run_result` | `tests/test_v6_terminal_commitment_authority.py:19,527,817,844` | MUST NOT MOVE |
| `_v6_run_result` | `tests/test_v6_three_root_concurrency.py:10,185` | MUST NOT MOVE |
| `_cmd_run` | `tests/test_v6_global_dispatch_guard.py:1035,1090` | EXPECTED TO MOVE — same reason as `_execute_bound_run`; assertions on refusal codes MUST NOT move |
| `attach_bound_evidence` | `tests/test_evidence_dossier.py:12,194` | MUST NOT MOVE |
| `attach_bound_evidence` | `tests/test_evidence_dossier_replay.py:8,57` | MUST NOT MOVE |
| `attach_bound_evidence` | `tests/test_simulation_capability_v5.py:28,233` | MUST NOT MOVE |
| `attach_bound_evidence` | `tests/test_v6_three_root_concurrency.py:18,100` | MUST NOT MOVE |

**Map documents:**

| Target | Hit | Classification |
|---|---|---|
| `application/text_runs.py` | `CON-run-identity.md:4`; `SUB-amendment.md:139`; `SUB-application.md:102,132,144,165,179,189,215,247,261,269` | EXPECTED TO MOVE (S12) |
| `cli/main.py` | `CON-run-identity.md:126`; `SEAM-schools-x-scheduler.md:81`; `SUB-amendment.md:139`; `SUB-application.md:40,102,132,165,179,261`; `SUB-manifest.md:140`; `SUB-periphery.md:44`; `SUB-verification.md:232` | EXPECTED TO MOVE for `SUB-application`/`CON-run-identity`; MUST NOT MOVE for `SEAM-schools-x-scheduler`, `SUB-manifest`, `SUB-periphery`, `SUB-verification` (this change adds no schools, manifest, periphery, or verifier behaviour) |
| `amendment/apply.py` | `CON-run-identity.md:4,152`; `SUB-amendment.md:100,179,204` | EXPECTED TO MOVE (S12) |
| `_worker` | `SUB-application.md:63,102` | EXPECTED TO MOVE — `_worker` no longer owns the terminalization block |
| `_v6_run_result` | `SUB-application.md:161,165` | MUST NOT MOVE |
| `_record_exhaustion_lifecycle_stop` | `SUB-application.md:210,215` | EXPECTED TO MOVE — its caller becomes `terminalize_text_run` |
| `attach_bound_evidence` | `SEAM-periphery-x-verification.md:6,15,31,51,80`; `SUB-amendment.md:100,115,118`; `SUB-periphery.md:74,98` | EXPECTED TO MOVE for `SEAM-periphery-x-verification` (its "called from exactly two places" claim gains a third) and `SUB-amendment` (S6); MUST NOT MOVE for `SUB-periphery` |

`qualification_digest`: `[]` — empty. **R15 cost report: zero.** No
target reaches a qualification subject, so no digest drifts and no
~14-minute battery re-runs.
`wheel_smoke_pins`: `[]` — but a NEW console subcommand (`finalize`, S3)
changes the public CLI surface, so `scripts/wheel_smoke.py` /
`scripts/wheel_operational_smoke.py` pins are re-checked and re-run in
the same commit as S3 (CLAUDE.md's wheel-smoke rule), whether or not this
census names them.

## Record-observable guardrails

This change adds NO new typed-record field, record type, or verification
finding. It causes EXISTING record types (`run-stop`, the terminal
commitment CONTROL event, `attached-source-record.v1`) to be written on a
path that previously wrote none. Every existing committed root is
unaffected because nothing reads a new field and nothing writes to those
roots — proved by S8's sweep rather than asserted. No `tools/root_sweep.py`
probe change is therefore required, and none is proposed; if S14's live
finalize shows the sweep would not have noticed a terminal appearing on a
root, that becomes a PARKED probe proposal in its own separate commit.

## Measurements

M1 — the bare-run root already carries a `deepreason-text-workload-v1`
document, so S4 rebuilds nothing it does not have:

    $ head -c 400 experiments/2026-08-12-live-grounded-extension-expansion/run/problem.json
    {"criteria": [], "problem": {"description": "Propose innovative ways to
    expand and strengthen DeepReason's grounded extension ...",
    "id": "question-6fcc770419da1e9c8fccb2db8ed32bbe"},
    "schema": "deepreason-text-workload-v1", "sources": [ ... 6 ids ... ]}

M2 — there is no `append` subcommand (supports A1):

    $ grep -n 'sub.add_parser(' src/deepreason/cli/main.py
    (58 setup, 147 qualify, 175 status, 177 explain-error, 182
    validate-intake, 187 config, 242 input, 257 doctor, 285 reason, 327
    web, 345 admit, 373 skills, 380 distill, 388 brain, 414 amend, 440
    continue, 450 watch, 453 cancel, 456 frontier, 457 run, 466 mcp, 467
    why, 468 evidence, 472 blob, 476 signals, 477 export, 483 theory,
    484 prose, 485 docket, 486 research, 487 submit, 500 fail, 507 rule,
    511 schools, 512 calibrate, 520 capture, 521 report, 522 findings,
    531 reseed, 532 merge, 533 trace, 537 narrate)
    -> no "append"

M3 — the errata ledger tail ends at E24, so E25 is the next free number
(supports S13):

    $ tail -25 docs/ERRATA.md
    **E24 — `dr-drive-harness/SKILL.md`'s "never generalize instruction
    scope" rule is an accepted, permanent exception ...

M4 — `Scheduler(harness, None, config).report()` derives the run report
read-only, with no adapter and no model call (supports S3):

    report ok: survivors 191 frontier 87 problems 2882
    frontier head: ['013723d2dbc56eaed95f38658e93c8d30875d102f70f8440e58cbdb3e061aa39', ...]

191 survivors and frontier head `013723d2dbc5` match
`experiments/2026-08-12-live-grounded-extension-expansion/RESULTS.md`
exactly — the derivation reproduces the live run's own reported numbers.

M5 — the typed STOPPED lifecycle receipt lands on a byte-copy of the real
root by APPENDING one CONTROL event (supports S3 and the GATE verdict):

    owned v4/v6 control: True
    lifecycle stop: {"digest": "a02da10aee3f9a431d569afd808b24e5458395ba34478035a3a194ecf2017d9b",
      "event_seq": 9947, "reason": "budget_exhausted",
      "schema": "deepreason-run-stop-v1", ...}
    terminal_lifecycle_decision: True
    next_seq now: 9948

## Budget

    $ python3 -c "..."
      180  S1 terminalize_text_run + _worker refactor (text_runs.py)
       50  S2 bare-run lifecycle wiring (cli/main.py _execute_bound_run)
       95  S3 deepreason finalize command (cli/main.py + finalize_stopped_root)
       40  S4 ensure_lifecycle_documents (text_runs.py)
       25  S6 amendment duplicate-refusal narrowing (amendment/apply.py)
      190  S10 regression tests (tests/test_lifecycle_operation_parity.py)
       55  S12 map documents (SUB-application, SUB-amendment, CON-run-identity)
       14  S9 CLAUDE.md operator design law
       16  S13 docs/ERRATA.md E25
    TOTAL 665

**~665 lines, 6 commits.** Frozen surfaces touched: **none by this
design** — one disclosed CONTACT (surface 3, via
`attach_bound_evidence`), pre-granted by C3 and unused.

Over the ~300-line guideline, so the split is declared as ordered parts
with independent commits rather than one sprawling change; `dr-plan-steps`
turns these into CHECKLIST steps in this order, and each part's gate runs
before the next begins:

    Part A (S1, S4)    — shared terminalization + lifecycle documents  ~220
    Part B (S2, S5, S9) — bare-run wiring + the ledgered law            ~64
    Part C (S3)        — the `finalize` command + wheel smokes          ~95
    Part D (S6)        — amendment duplicate-refusal narrowing          ~25
    Part E (S10, S12, S13) — tests, map, errata                        ~261
    Part F (S14, S8)   — the live proof and the sweep                 (no src)

Splitting further into separate tranches is rejected: C4 forbids stops
beyond the one gate, and S14's live proof cannot run until A-E are all
in.

Rubric: 6/6 yes — every R has a spec item with a machine-decidable
accept (R1→S1/S2/S7, R2→INVENTORY.md, R3→S1/S2/S3/S4/S5, R4→S3,
R5/R6→INVENTORY.md, R7→S6/S14, R8→S14, R9→S9, R10→S10, R11→S11,
R12→S12, R13→S13, R14→S8, R15→census `qualification_digest: []`,
R16→S11); blast-radius census pasted and every hit classified;
frozen-surface contact forecast recorded with the tool's own list
verbatim; every named mechanism traced (`TEXT_RUN_SERVICE`,
`amendment/apply.py` terminal authority, `attach_bound_evidence`,
`OLLAMA_CLOUD_OPERATIONS.md` — see A3); not a DESIGN-AND-STOP request,
though Measurements and Options discipline was applied anyway; nothing
in this spec is untraceable to an R or C number.
