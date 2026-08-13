# VALIDATION.md — lifecycle-operation parity

Proves the completed change against every acceptance check in `SPEC.md`.
Validates only; patches nothing. Every verdict below is a pasted command
output, not a claim.

Verdict: **PENDING** — filled in as each gate lands. Sections marked
`PENDING` have not run yet; sections marked `PASS` carry their output.

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

**PASS** (fixture); real-root proof pending in the Live section.

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

## S8 — every committed root still replays byte-unchanged

PENDING — `python tools/root_sweep.py` and the targeted
`verify_root_report` on a known-good committed root.

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
    10 passed

Ten cases, including both named obligations:
`test_manifest_launched_root_reaches_typed_terminal_and_accepts_amend`
and `test_interrupted_run_still_refuses_amend_not_at_terminal`.

**Prediction check (R10).** SPEC S10 predicted *no existing test asserts
the old gap*. Result: PENDING until the full gate confirms it — no
existing test has been modified so far, and none needed to be.

---

## S11 — gates and cadence

PENDING — full gate and `docs_verify`.

---

## S12 — the map moves in the same commits

PENDING — `python tools/docs_verify.py` full mode plus `--audit`.

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

PENDING — see the Live section below.

---

## Live proof on the REAL grounded-extension root

PENDING.

---

## Wheel smokes (public CLI surface changed by S3)

    $ python scripts/wheel_smoke.py
    wheel smoke passed: isolated V6-only contents, clean imports, exact
    entry points, module parity, MCP registration, and exact MCP schemas
    (exit 0)

`finalize` is a CLI verb, not a console script or an MCP tool, so no
`EXPECTED_CONSOLE_SCRIPTS`, `EXPECTED_MCP_TOOLS` or
`EXPECTED_MCP_SCHEMA_SHA256` pin moved.

`python -u scripts/wheel_operational_smoke.py`: PENDING.

---

## R15 — qualification-digest drift cost

    "qualification_digest": []

Zero. No target reaches a qualification subject, so no digest drifts and
no ~14-minute battery re-runs. Reported per R15.
