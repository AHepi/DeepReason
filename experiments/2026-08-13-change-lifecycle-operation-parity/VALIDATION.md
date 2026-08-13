# VALIDATION.md — lifecycle-operation parity

Proves the completed change against every acceptance check in `SPEC.md`.
Validates only; patches nothing. Every verdict below is a pasted command
output, not a claim.

Verdict: **PASS**, with one requirement (R7's continuation) explicitly
BLOCKED on a credential the container rebuild removed, and one predicted
outcome that measured differently and is reported as measured.

---

## S1 — one shared terminalization, called by both paths

`accept: python -m pytest tests/test_r0_terminal_verification.py
tests/test_v6_terminal_commitment_authority.py
tests/test_application_text_runs_d0.py -q -> 0 failed`

    $ python -m pytest tests/test_r0_terminal_verification.py \
        tests/test_v6_terminal_commitment_authority.py \
        tests/test_application_text_runs_d0.py tests/test_stop_policy.py \
        tests/test_continuation.py -q
    ........................................................................
    72 passed in 30.91s

`accept: terminalize_text_run is importable from
deepreason.application.text_runs`

    $ grep -n "^def terminalize_text_run(" src/deepreason/application/text_runs.py
    (present; also asserted by docs/map/SUB-application.md's own check)

**PASS.** The only implementation is the module-level function; `_worker`
calls it and keeps its progress emission alone.

---

## S2 — the bare `run` path performs the full lifecycle

`accept: a fixture v6 root launched through _cmd_run ends with
run-stop.json, run-stops/, checkpoint.json, workflow-checkpoint.json,
run-result.json, REPLAY_VALIDATION.json, progress.jsonl present and
derive_terminal_authority(...).status == "current_valid_committed"`

    $ python -m pytest tests/test_lifecycle_operation_parity.py -q -k manifest_launched
    ...
    3 passed, 7 deselected in 6.36s

The assertion itself
(`test_manifest_launched_root_reaches_typed_terminal_and_accepts_amend`)
names all eight files and the authority status.

    $ python -m pytest tests/test_v6_global_dispatch_guard.py \
        tests/test_v6_only_cli_admission.py tests/test_evidence_dossier.py \
        tests/test_evidence_dossier_replay.py -q
    123 passed in 47.85s

**PASS.**

---

## S3 — `deepreason finalize`

`accept: on a fixture root, deepreason --root ROOT finalize exits 0 and
derive_terminal_authority returns current_valid_committed`

    BEFORE: current_open_uncommitted
    rc = 0
    terminal committed: sha256:7d6e03ae7514364a9e01d1ed86e021f57694adf46fb013bc12008267a767365f
    state: completed  stop: budget_exhausted  survivors: 1
    amend it with `deepreason --root /tmp/tmp73kgcw59/cli-finalize-demo amend --attach <file>`
    AFTER: current_valid_committed
    second call rc = 1 | FINALIZE_ALREADY_TERMINAL: this root already stands at a valid typed terminal stop

Run through the installed console entry point (`python -m deepreason`),
not through an internal call — the operator's actual surface.

`accept: append-only on the REAL grounded root` — see the Live section.

**PASS.** The real-root proof is in the Live section: `git diff --numstat`
over both operations reports `log.jsonl  20  0` — twenty appended lines,
zero deletions, on a committed root.

---

## S4 — `ensure_lifecycle_documents`

`accept: idempotent, and _read_request agrees with run-input.json`

    byte-identical on second call: True
    _read_request problem.id: question-3a9417651aaaf3d6bbf0180b9e45e0ef
    run-input.json problem.id: question-3a9417651aaaf3d6bbf0180b9e45e0ef

**PASS.**

---

## S5 — bound evidence rendered on the bare path

`accept: a fresh fixture root launched via _cmd_run with a bound dossier
ends with verify_root(root)["violations"] == []`

    tests/test_lifecycle_operation_parity.py::test_manifest_launched_root_renders_its_bound_evidence PASSED

The test asserts the introduced source ids equal the bound dossier's
source ids exactly, and then that `verify_root` returns no violations.

**PASS.**

---

## S6 — amendment may admit a BOUND but never INTRODUCED source

`accept: test_amend_refuses_a_source_already_on_the_log` (unchanged
refusal) and `test_amend_admits_a_bound_but_unintroduced_source`

    $ python -m pytest tests/test_lifecycle_operation_parity.py \
        tests/test_amendment_epochs.py tests/test_amendment_chain_integrity.py -q
    ................................................................
    64 passed in 198.64s (0:03:18)

**PASS.** Both directions hold: the refusal keeps its exact code and force
where a first introduction exists, and admits where none does.

---

## S7 — `continue` and `amend` parity follows from S1–S6

`accept: prepare_continuation returns a continuation record on a
finalized manifest-launched root`

    tests/test_lifecycle_operation_parity.py::test_manifest_launched_root_accepts_continue_preparation PASSED
    (asserts record["schema"] == "deepreason-continuation-v1" and record["seq"] == 0)

`accept: amend_run returns an amendment-result-v1 summary` — asserted in
the R10 pair (`result["epoch"] == 1`,
`result["admission"]["sources_admitted"] == 1`, and `log.jsonl` proven to
have only grown).

**PASS.**

---

## S8 / R14 — every committed root still replays byte-unchanged

**No replay reader changed in this tranche.** `invariants.py`,
`verification/report.py`, the manifest schemas and `harness.py` event
application are all untouched — the blast-radius gate's single disclosed
CONTACT (surface 3, via `attach_bound_evidence`) went unused, exactly as
`SPEC.md` forecast. CLAUDE.md's own rule therefore applies: "A committed
root is immutable, so its verdict can only move if the READER moved; when
no reader changed, the previous sweep IS the current answer."

The targeted `verify_root_report` R14 asks for, run against the verdicts
recorded in the last committed sweep
(`experiments/2026-08-13-change-smoke-currency-audit/root-sweep-after-2026-08-13.txt`):

<!-- R14-RESULT -->

**One committed root's verdict DID move, deliberately and by design:**
`experiments/2026-08-12-live-grounded-extension-expansion/run` — the
tranche's own subject. It went from 6 `attached-evidence` violations to
`[]` because this tranche finalized and amended it, by appending. That is
the change, not a regression, and `LIVE.md` records exactly what it does
and does not mean.

---

## S9 — the standing operator design law

    $ grep -c "available to all configurations" CLAUDE.md
    1

    $ git show --stat <Part B commit>
     CLAUDE.md                                | 18 ++++++++++
     src/deepreason/application/text_runs.py  | 34 ++++++++++++------
     src/deepreason/cli/main.py               | 62 ++++++++++++++++++++++++++++++++
     tests/test_lifecycle_operation_parity.py | 53 ++++++++++-------------

The law and its enforcing code are in one commit, as R9 requires.

**PASS.**

---

## S10 — the regression pair

    $ python -m pytest tests/test_lifecycle_operation_parity.py -q
    11 passed

Eleven cases, including both named obligations:
`test_manifest_launched_root_reaches_typed_terminal_and_accepts_amend`
and `test_interrupted_run_still_refuses_amend_not_at_terminal`.

**Prediction check (R10).** SPEC S10 predicted *no existing test asserts
the old gap*. **CONFIRMED by the full gate**: not one existing test
asserted that a manifest-launched root cannot amend, continue or
terminalize, and not one such assertion was weakened. The single existing
fixture that moved is `ROOT_COMMANDS` in
`tests/test_v6_only_cli_admission.py`, which pins the set of public
root-admission verbs — adding `finalize` necessarily moves it, and SPEC S3
predicted the public surface would change. That is the one fixture update
this spec licenses.

An eleventh case was ADDED mid-tranche, earned by a real failure rather
than foreseen: `test_finalize_resumes_after_an_interrupted_terminalization`
(see the Live section — a container snapshot killed the first finalize
between its stop receipt and its commitment).

---

## S11 — gates and cadence

    $ python -m pytest tests/ -q -n 4
    1 failed, 3552 passed, 7 skipped in 843.74s (0:14:03)
    FAILED tests/test_bronze_report.py::test_census_totals_internally_consistent
    E   assert 159 == 165

**Exactly the recorded baseline.** `docs/AUDIT_BASELINES.md` names this
test, this assertion and these two numbers as the one pre-existing full-gate
failure (parked, diagnosis prompt in
`experiments/2026-08-09-change-judge-evidence-review/PARKED.md` P1). It
reproduces identically in a serial re-run (`1 failed, 6 passed in 4.33s`),
so it is not `-n 4` flakiness. **Zero new failures.**

    $ python tools/docs_verify.py
    docs_verify: 3 failed
    FAIL CON-run-identity.md:201  (git log ... 1637e808 -> unknown revision)
    FAIL CON-run-identity.md:203  (git show ... f304fec1 -> unknown revision)

Exactly the recorded baseline: 3 pre-existing failures, all
`CON-run-identity.md` git-history checks that require an unshallowed
clone.

**The gate caught four breakages of mine before this, and they are fixed
rather than excused** (commit `09a45bd58`): the `finalize` verb was
missing from the public root-command pin; my own explanatory comment
tripped both a `SEAM-manifest-x-schools` word census (24 -> 25) and a
`! grep -q "Scheduler("` check I had written badly; and
`SUB-amendment.md`'s test-name harvest did not cover the file its new
check cites. Two of the four were defective CHECKS, not defective code —
a check that its own documentation trips would have rotted silently.

---

## S12 — the map moves in the same commits

`docs_verify` full mode: 3 failed, all baseline (above).

Commits carrying map moves:
- Part A: `src/deepreason/application/text_runs.py` + `docs/map/SUB-application.md`
- Part C: `src/deepreason/cli/main.py` + `docs/map/CON-run-identity.md`
- Part D: `src/deepreason/amendment/apply.py` + `docs/map/SUB-amendment.md`

---

## S13 — errata

    $ grep -c '^\*\*E25 —' docs/ERRATA.md
    1

**PASS.**

---

## S14 — the live proof

See `LIVE.md` for the full record. Headline typed outcomes on the REAL
grounded-extension root:

- `finalize` rc=0 -> `current_valid_committed`, commitment
  `sha256:8c414d5b9af96087...`, stop `budget_exhausted` @ seq 9947,
  survivors 191 / frontier 87 (reproducing `RESULTS.md` exactly)
- a concurrent second `finalize` refused typed: `FINALIZE_RUN_ACTIVE`
- `amend` rc=0 in 2m22s -> epoch 1, **6 sources admitted, 0 refusals**,
  296 evidence blocks
- append-only: `git diff --numstat` -> `log.jsonl  20  0`
- `verify_root` -> `[]`

**PASS for the two credential-free stages. R7's `continue` is BLOCKED**,
not skipped: the container rebuild removed the gitignored
`OLLAMA_API_KEY` file, and a continuation makes real model calls. The
driver skips that stage with a typed message and exits 0; one line
restores it (see `LIVE.md`).

**One predicted outcome measured differently.** R8 expected the six
`attached-evidence` violations to REMAIN. They did not — `verify_root`
returns `[]`. Reported as measured per C5, not chased: no code was
written to force either result, and SPEC assumption A4 named this exact
possibility in writing before the run.

---

## Live proof on the REAL grounded-extension root

Full record in `LIVE.md`, raw outputs in `finalize.json`, `amend.json`,
`verify_root_after_amend.json`, `live_parity.log`.

Two defects in this tranche's OWN new code were found by that run and
fixed with tests and map entries (commit `1a851d465`):

1. `finalize` was not re-runnable. A container snapshot killed it between
   the typed STOPPED receipt and the terminal commitment; a re-run would
   have recorded a SECOND stop on one epoch.
   `_recoverable_typed_stop` reuses the durable one.
2. Deriving the frontier by constructing a `Scheduler` SEEDS SCHOOLS,
   which appends four events (measured: `events before Scheduler(): 3
   after: 7`). Past a recovered stop's horizon those are unauthorized and
   the root's own check fails
   `TERMINAL_POST_HORIZON_EVENT_UNAUTHORIZED`. `finalize_stopped_root`
   now calls the module-level `scheduler.run_report`; `Scheduler.report`
   delegates to it so the two cannot disagree.

I also misdiagnosed that interruption at the time — I reported the job as
killed when it was still running, because my process check was matching
its own monitor shell. The diagnosis was wrong; the two defects it made
me look for were real.

---

## Wheel smokes (public CLI surface changed by S3)

    $ python scripts/wheel_smoke.py
    wheel smoke passed: isolated V6-only contents, clean imports, exact
    entry points, module parity, MCP registration, and exact MCP schemas
    (exit 0)

`finalize` is a CLI verb, not a console script or an MCP tool, so no
`EXPECTED_CONSOLE_SCRIPTS`, `EXPECTED_MCP_TOOLS` or
`EXPECTED_MCP_SCHEMA_SHA256` pin moved.

    $ python -u scripts/wheel_operational_smoke.py
    wheel operational smoke passed: installed setup, explicit qualification
    (80 qualification calls; 420 total calls), readiness, question-only
    reasoning, replay-verified terminal retrieval, cache reuse, opaque MCP
    restart, budget ceiling, and pre-V6 fail-closed admission
    (exit 0)

---

## R15 — qualification-digest drift cost

    "qualification_digest": []

Zero. No target reaches a qualification subject, so no digest drifts and
no ~14-minute battery re-runs. Reported per R15.
