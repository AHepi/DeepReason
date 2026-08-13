# Checklist for: one discoverable way to retrieve run results — `deepreason results`

State: next=1 blockers=none
Map ids this plan was scoped from: `DR-SUB-application` (owns
`src/deepreason/application/` and `src/deepreason/cli/` — the covering document
for both the reader and the verb), `DR-SUB-verification` (read-only use of
`verify_root_report`; **frozen**), `DR-CON-run-identity` (run id, roots on disk,
amendment epochs), `DR-INV-frozen-surfaces` (gate returned `CLEAR`).
No SEAM document exists for `application x verification` or
`application x run-identity` (both listed `Seams-undocumented` in
`SUB-application.md`); creating one is not required here because this change
adds a READER on the application side only and defines no new agreement —
recorded in SPEC.md rather than assumed away.

Re-read REQUEST.md + SPEC.md before every step. Execute strictly in order.
One step per dr-execute-step invocation.

Ceiling (SPEC.md Budget): 433 lines. `python tools/diff_budget.py` runs at
every `[COMMIT]` step; EXCEEDED is a stop, decided by the calling skill.

---

- [ ] 1. (S13, S9, S3) Write the reader's tests FIRST, in
      `tests/test_results_command.py`: the read-only tree-unchanged snapshot
      test (S13/R17), the typed-absence key-set test over the
      grounded-extension root (S9/R12), and the fact-presence tests for
      identity/run/artifacts (S3, S4). They must FAIL for the right reason
      (no module yet).
      done-when: `python -m pytest tests/test_results_command.py -q 2>&1 | tail -3`
      reports collection/import errors naming
      `deepreason.application.results` — not a syntax error in the test file.

- [ ] 2. (S1, S2, S3, S4) Create `src/deepreason/application/results.py` with
      `results_summary(path, *, verify=False)` covering the schema's `schema`,
      `root`, `resolved_from`, `question`, `identity`, `run`, `artifacts`,
      `absences` keys, composing `findings.findings_summary` for status counts
      and the question (S2/R4).
      done-when: `python -m pytest tests/test_results_command.py -q` → the
      S3/S4/S9/S13 tests pass (the S5–S7 tests are not written yet).

- [ ] 3. (S5) Add `adjudication` to the reader: `judge_calls` from
      `event.llm.role == "judge"`, and the `trial-observation` /
      `trial-declined` / `trial-blocked:<reason>` Measure counts.
      done-when: a new test in `tests/test_results_command.py` asserts
      `ran is True` and `judge_calls > 0` on a committed root carrying
      `trial-declined` events, and a typed-zero `ran is False` on one without.

- [ ] 4. (S6) Add `verification` to the reader: stored
      `REPLAY_VALIDATION.json` by default, `verify_root_report(root,
      allow_missing_terminal=True).summary_payload()` only under
      `verify=True`, both emitting the same five-family shape plus `source`.
      done-when: a new test asserts `source == "stored"` with
      `verify_root_report` monkeypatched to fail (proving it is NOT called),
      and `source == "rederived"` under `verify=True`.

- [ ] 5. (S7) Add `amendment` and `terminal` to the reader: epoch count and
      seqs from `amendment.state`, `valid_typed_terminal`,
      `stop_reason_resumable` against `runtime.stop.RESUMABLE_STOP_REASONS`,
      and `amend_ready`.
      done-when: a new test asserts all four `terminal` keys plus both
      `amendment` keys exist on a root with a terminal, and that
      `amend_ready is False` with typed absences on the grounded-extension
      root.

- [ ] 6. (S8) Add `render_results(summary) -> str` — the human-readable mode
      with a plain-language gloss in-line on every technical label.
      done-when: a new test asserts the rendering contains `verify_root`, at
      least one `(` gloss on the verification line, and every top-level
      section heading.

- [ ] 7. (S1–S9) [COMMIT] Ring the reader and commit it with its tests.
      done-when: `python -m pytest tests/test_results_command.py
      tests/test_findings_command.py -q` → `0 failed`, and
      `python tools/blast_radius.py --files
      src/deepreason/application/results.py --symbols results_summary
      render_results` → `"frozen_surface_verdict": "CLEAR"` (the
      forecast-then-verify SPEC.md promised, now that the file exists), and
      `python tools/diff_budget.py origin/main --ceiling 433` → not EXCEEDED,
      and the commit exists.

- [ ] 8. (S10) Add `RESULTS_ROOT_NOT_FOUND` and `RESULTS_HOME_AMBIGUOUS` raise
      sites to `results.py` (path resolution per SPEC.md A1/A2) and their two
      entries to `src/deepreason/error_catalog.py`; raise
      `test_catalog_covers_46_entries`' pin to 48 and add a test proving both
      new codes are byte-identical to real raise-site strings in `results.py`.
      done-when: `python -m pytest tests/test_error_catalog.py -q` → `0
      failed`, and `python -m deepreason explain-error RESULTS_ROOT_NOT_FOUND`
      prints a non-empty gloss.

- [ ] 9. (S11, S16-defect) Add the `results` verb to `build_parser` in
      `src/deepreason/cli/main.py` with `help="read a run's typed results"`,
      an optional positional, `--json` and `--verify`; add the `_main`
      dispatch branch. Do NOT add it to `_ROOT_ADMISSION_COMMANDS` (SPEC.md
      A8).
      done-when: `deepreason --help | grep -c "read a run's typed results"` →
      `1`, and `python -m pytest
      tests/test_v6_only_cli_admission.py::test_public_parser_omits_make_and_unqualified_advanced_commands
      -q` → `1 passed`.

- [ ] 10. (S11, R16) Add
      `tests/test_results_command.py::test_top_level_help_names_the_results_verb`
      — the acceptance test for the defect itself: a session given only
      `deepreason --help` can name the verb that retrieves results.
      done-when: that test passes, and it FAILS if the help string is removed
      (prove by temporary edit, revert before proceeding).

- [ ] 11. (S18) Update `docs/map/SUB-application.md` in the SAME commit as the
      verb: Entry points row for `results_summary`/`render_results` with a
      `check:`, a "Where to change what" row, the corrected admission sentence
      naming the reader exception, and a `Traps` entry naming this tranche.
      done-when: `python tools/docs_verify.py --fast 2>&1 | tail -3` reports
      no NEW failure for `SUB-application.md`, and
      `grep -q "results_summary" docs/map/SUB-application.md` → exit 0.

- [ ] 12. (S12) Add the retrieval line to
      `.claude/skills/dr-drive-harness/SKILL.md` §2 (the public CLI lifecycle
      block) and to `README.md`'s CLI list, in the SAME commit as step 9/11.
      done-when: `grep -q "deepreason results"
      .claude/skills/dr-drive-harness/SKILL.md && grep -q "deepreason results"
      README.md` → exit 0.

- [ ] 13. (S8, S21) Run the demonstration R25 requires and capture it:
      `deepreason results
      experiments/2026-08-12-live-grounded-extension-expansion/run` and the
      same with `--json`, output saved to the tranche's `proof/` directory.
      done-when: `proof/results-grounded-extension.txt` and
      `proof/results-grounded-extension.json` exist and the JSON parses.

- [ ] 14. (S8–S12, S18) [COMMIT] Commit the verb, catalog, help pin, map,
      manual and README together.
      done-when: `python tools/diff_budget.py origin/main --ceiling 433` →
      not EXCEEDED, and `git show --stat HEAD` lists
      `cli/main.py`, `error_catalog.py`, `tests/test_error_catalog.py`,
      `tests/test_results_command.py`, `docs/map/SUB-application.md`,
      `.claude/skills/dr-drive-harness/SKILL.md`, `README.md`.

- [ ] 15. (S15) Prove the MCP surface and console entry points did not move.
      done-when: `git diff --stat origin/main -- scripts/wheel_smoke.py
      scripts/wheel_operational_smoke.py src/deepreason/mcp_server.py
      pyproject.toml` → empty output.

- [ ] 16. (S19) Re-run R23's errata trigger grep at validation time.
      done-when: `grep -rn "deepreason results" docs/ README.md
      .claude/skills/ | grep -v "dr-drive-harness"` returns only hits this
      tranche introduced (i.e. no PRE-EXISTING document names a nonexistent
      results command) — pasted into VALIDATION.md either way.

- [ ] 17. (S16, R20) Prove old roots are untouched.
      done-when: `git status --porcelain experiments/ | grep -v
      "2026-08-13-change-results-retrieval-surface"` → empty, AND the S13
      tree-unchanged test passes. (SPEC.md's Record-observable guardrails
      section authorizes this as the admissible substitute for the ~10-minute
      42-root sweep: no reader this tranche touches was MODIFIED — every
      reader it uses is called, not changed — and no writer or format moved.)

- [ ] 18. (all) Map check: `python tools/docs_verify.py` (FULL, not `--fast`
      — `--fast` reuses cached results and cannot catch a document this
      `src/` change just broke).
      done-when: failures ≤ the 3 pre-existing `CON-run-identity.md`
      git-history failures recorded in `docs/AUDIT_BASELINES.md`, with the
      output pasted; and `python tools/docs_verify.py --audit` reports no new
      finding.

- [ ] 19. (all) Full gate: `python -m pytest tests/ -q -n 4`, run on an
      otherwise idle box, never concurrently with step 18.
      done-when: output pasted, and failures ≤ the baseline recorded in
      `docs/AUDIT_BASELINES.md` (1 pre-existing:
      `tests/test_bronze_report.py::test_census_totals_internally_consistent`;
      plus the 5 known `-n 4` thread-timing flakes in `tests/test_mcp_run.py`
      and `tests/test_mcp_scratch_bridge.py`, which must go green on a serial
      re-run if they appear).

- [ ] 20. (all) Wheel smoke: `python scripts/wheel_smoke.py`.
      done-when: exit code compared against
      `docs/AUDIT_BASELINES.md`'s KNOWN STALE note and the verdict pasted —
      an MCP-pin failure is baseline, any OTHER failure is a finding and a
      stop.

- [ ] 21. (all) Write VALIDATION.md: every SPEC.md accept command run and its
      output pasted, with the PASS/FAIL verdict.
      done-when: `VALIDATION.md` exists and its verdict line reads PASS or
      FAIL.

- [ ] 22. (S21, R25) Write DELIVERY.md: the R-by-R reconciliation table with
      pasted PROOF per requirement, including the `deepreason results` output
      against the grounded-extension root from step 13.
      done-when: `DELIVERY.md` contains one row per R1–R25 and the pasted
      demonstration output.

- [ ] 23. (all) [COMMIT] Push and confirm a clean tree.
      done-when: `git status --porcelain` is empty AND
      `git rev-parse HEAD` == `git rev-parse origin/claude/results-retrieval-surface-v6jmiy`.
