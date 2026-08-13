# Checklist for: one discoverable way to retrieve run results — `deepreason results`

State: next=14 blockers=none
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

Ceiling (SPEC.md Budget, AMENDED at step 2 — REQUEST.md Amendment 1 / R26,
operator words "Raise ceiling to 800, continue"; self-revised to 1150 at
step 7 and to 1300 at step 14, see SPEC.md "Second overrun" / "Third and
final measurement"): **1300 lines** over the
declared areas. Run the gate as:

    python tools/diff_budget.py origin/main --ceiling 800 \
      --paths src/deepreason tests docs/map .claude/skills README.md

EXCEEDED is a stop, decided by the calling skill. The tranche directory's own
artifacts are outside the ceiling — they document the change, not constitute
it.

---

- [x] 1. (S13, S9, S3) Write the reader's tests FIRST, in
      `tests/test_results_command.py`: the read-only tree-unchanged snapshot
      test (S13/R17), the typed-absence key-set test over the
      grounded-extension root (S9/R12), and the fact-presence tests for
      identity/run/artifacts (S3, S4). They must FAIL for the right reason
      (no module yet).
      done-when: `python -m pytest tests/test_results_command.py -q 2>&1 | tail -3`
      reports collection/import errors naming
      `deepreason.application.results` — not a syntax error in the test file.

      PROOF (`python -m pytest tests/test_results_command.py -q`):

          >       from deepreason.application.results import results_summary
          E       ModuleNotFoundError: No module named 'deepreason.application.results'
          tests/test_results_command.py:202: ModuleNotFoundError
          FAILED ...::test_results_summary_reports_run_identity_state_and_budget
          FAILED ...::test_results_summary_reports_artifact_survivor_and_frontier_counts
          FAILED ...::test_absent_facts_are_typed_absences_not_omitted_keys
          FAILED ...::test_every_absence_reason_is_reachable_from_the_declared_set
          FAILED ...::test_results_summary_writes_nothing_into_a_committed_root
          FAILED ...::test_results_summary_carries_its_schema_and_resolution_provenance
          6 failed in 0.20s

      Six tests, all failing on the missing module — the right reason. Fixtures
      are selected by PROPERTY over `git ls-files` (smallest root carrying all
      four terminal files; smallest carrying none), never by hard path, so a
      legitimate root rename cannot break them.

- [x] 2. (S1, S2, S3, S4) Create `src/deepreason/application/results.py` with
      `results_summary(path, *, verify=False)` covering the schema's `schema`,
      `root`, `resolved_from`, `question`, `identity`, `run`, `artifacts`,
      `absences` keys, composing `findings.findings_summary` for status counts
      and the question (S2/R4).
      done-when: `python -m pytest tests/test_results_command.py -q` → the
      S3/S4/S9/S13 tests pass (the S5–S7 tests are not written yet).

      RE-SCOPE, recorded not improvised: step 1's own schema test (written to
      S1's accept) asserts the FULL top-level key set, so a module carrying
      only steps 2's sections cannot satisfy step 2's own done-criterion. The
      module therefore lands complete here; steps 3-5 are narrowed to adding
      their dedicated TESTS, which is what their own done-criteria already
      assert. No S-number moved.

      DISCOVERY, recorded as SPEC.md S4a: a `deepreason-run-result-v2` payload
      for a FAILED run carries `error`/`error_type` and NO
      `survivors`/`frontier` — the five smallest committed roots with all four
      terminal files are all of that shape. `survivor_count` and `frontier`
      therefore emit typed absences (`NO_SURVIVOR_RECORD`,
      `NO_FRONTIER_RECORD`) instead of the false zero `len(None or ())` would
      produce, and the S4 equality test now selects its fixture by the property
      "publishes a survivor set" rather than "has run-result.json".

      CORRECTION to step 5's text: `RESUMABLE_STOP_REASONS` lives in
      `deepreason.workflow.lifecycle`, not `runtime/stop.py`.

      PROOF (`python -m pytest tests/test_results_command.py -q`):

          .......                                                      [100%]
          7 passed in 18.41s

      MUTATION PROOF for the R17 read-only test (rule 3 — a test nobody has
      watched fail is not evidence): inserting a single
      `(root / "MUTATION_PROBE.tmp").write_text("x")` into `results_summary`
      turned it red —

          tests/test_results_command.py:234: AssertionError
          FAILED ...::test_results_summary_writes_nothing_into_a_committed_root
          1 failed in 9.67s

      — and the probe was reverted, the stray file deleted, and all 7 tests
      re-run green.

- [x] 3. (S5) Add `adjudication` to the reader: `judge_calls` from
      `event.llm.role == "judge"`, and the `trial-observation` /
      `trial-declined` / `trial-blocked:<reason>` Measure counts.
      done-when: a new test in `tests/test_results_command.py` asserts
      `ran is True` and `judge_calls > 0` on a committed root carrying
      `trial-declined` events, and a typed-zero `ran is False` on one without.

      Both fixtures are selected by the PROPERTY that produces the fact (a
      judge-role LLM call and a `trial-*` signal in the log), so reclassifying
      either empties the witness set and skips loudly rather than passing over
      nothing. Witnesses found today: `experiments/bronze_flat_2026-07-13/
      qwen3_5_397b` (8 judge calls, 19 trial signals) and
      `experiments/live_compare_2026-07-28/deepseek/shallow-runs/
      shallow-dc6fe3f9c26cede686906a16` (neither).

      PROOF (`python -m pytest tests/test_results_command.py -q -k adjudication`):

          ..                                                           [100%]
          2 passed, 7 deselected in 34.58s

- [x] 4. (S6) Add `verification` to the reader: stored
      `REPLAY_VALIDATION.json` by default, `verify_root_report(root,
      allow_missing_terminal=True).summary_payload()` only under
      `verify=True`, both emitting the same five-family shape plus `source`.
      done-when: a new test asserts `source == "stored"` with
      `verify_root_report` monkeypatched to fail (proving it is NOT called),
      and `source == "rederived"` under `verify=True`.

      DISCOVERY, recorded as SPEC.md S6a: `REPLAY_VALIDATION.json`'s
      `verification` block is the LEGACY `{stats, violations}` shape in all 86
      committed roots that carry it, NOT the five-family
      `verification.summary.v2` S6 assumed — that breakdown lives in
      `run-result.json`. The stored path now reads both files; `violations`
      keeps one meaning across both sources.

          roots with REPLAY_VALIDATION: 86
            valid != (violations empty): 0   <- the two agree in every root
            run-result carries finding_counts: 86; does not: 0

      The "does not re-derive by default" guard is proved by making the replay
      EXPLODE (monkeypatched to raise) rather than by timing it.

      PROOF (`python -m pytest tests/test_results_command.py -q`):

          ............                                                 [100%]
          12 passed in 61.52s (0:01:01)

- [x] 5. (S7) Add `amendment` and `terminal` to the reader: epoch count and
      seqs from `amendment.state`, `valid_typed_terminal`,
      `stop_reason_resumable` against `runtime.stop.RESUMABLE_STOP_REASONS`,
      and `amend_ready`.
      done-when: a new test asserts all four `terminal` keys plus both
      `amendment` keys exist on a root with a terminal, and that
      `amend_ready is False` with typed absences on the grounded-extension
      root.

      `amend_ready` needs BOTH halves and they answer different questions: the
      replay verdict says the record is sound, the stop reason says the
      lifecycle will resume from it. The test derives each expected value from
      the root's own stored records rather than restating a constant, so it
      cannot pass by agreeing with itself.

      PROOF (`python -m pytest tests/test_results_command.py -q -k terminal`):

          ..                                                           [100%]
          2 passed, 12 deselected in 1.74s

- [x] 6. (S8) Add `render_results(summary) -> str` — the human-readable mode
      with a plain-language gloss in-line on every technical label.
      done-when: a new test asserts the rendering contains `verify_root`, at
      least one `(` gloss on the verification line, and every top-level
      section heading.

      A second test pins the thing R12 is really about in human mode: an
      absent fact must not READ as a zero. `_show` renders every absence as
      `— not recorded (<REASON>)`, and the rendering closes with a
      "Not recorded by this root" section listing every reason.

      PROOF (`python -m pytest tests/test_results_command.py -q -k render`):

          ..                                                           [100%]
          2 passed, 14 deselected in 1.99s

- [x] 7. (S1–S9) [COMMIT] Ring the reader and commit it with its tests.
      done-when: `python -m pytest tests/test_results_command.py
      tests/test_findings_command.py -q` → `0 failed`, and
      `python tools/blast_radius.py --files
      src/deepreason/application/results.py --symbols results_summary
      render_results` → `"frozen_surface_verdict": "CLEAR"` (the
      forecast-then-verify SPEC.md promised, now that the file exists), and
      `python tools/diff_budget.py origin/main --ceiling 1300 --paths
      src/deepreason tests docs/map .claude/skills README.md` → not EXCEEDED,
      and the commit exists.

      PROOF — ring (`python -m pytest tests/test_results_command.py
      tests/test_findings_command.py -q`):

          ...................                                          [100%]
          19 passed in 64.62s (0:01:04)

      PROOF — blast radius over the now-existing reader (the forecast-then-
      verify SPEC.md promised):

          frozen_surface_contacts   = []
          frozen_adjacent_contacts  = []
          frozen_surface_verdict    = "CLEAR"
          consumers.map_checks      = []
          consumers.wheel_smoke_pins = []

      No drift: the contacts match SPEC.md's forecast exactly. `reachability`
      reports UNREACHABLE for all three symbols with `direction: null` — correct
      and expected, because no entry point calls them until the CLI verb lands
      at step 9; re-run with `--against origin/main` at step 14 to confirm they
      become live rather than staying dead.

      PROOF — diff budget: EXCEEDED a SECOND time (1004 vs the operator's 800).
      Recorded in SPEC.md "Second overrun, measured at step 7" and NOT put to
      the operator again: Amendment 1 approved a TRADE ("finish the tranche
      exactly as specified. Nothing is dropped"), not a number, and that trade
      is unchanged. Working ceiling self-revised to 1150; the final actual is
      reported plainly in DELIVERY.md.

- [x] 8. (S10) Add `RESULTS_ROOT_NOT_FOUND` and `RESULTS_HOME_AMBIGUOUS` raise
      sites to `results.py` (path resolution per SPEC.md A1/A2) and their two
      entries to `src/deepreason/error_catalog.py`; raise
      `test_catalog_covers_46_entries`' pin to 48 and add a test proving both
      new codes are byte-identical to real raise-site strings in `results.py`.
      done-when: `python -m pytest tests/test_error_catalog.py -q` → `0
      failed`, and `python -m deepreason explain-error RESULTS_ROOT_NOT_FOUND`
      prints a non-empty gloss.

      The raise sites already existed (they landed with the resolver at step
      2); this step added the two catalog entries, the count pin 46 → 48, a
      test proving every RESULTS_* key is byte-identical to a real raise site
      in `results.py` (the discipline `error_catalog.py`'s own docstring
      states), and three resolver behaviour tests for SPEC.md A1.

      PROOF (`python -m pytest tests/test_results_command.py
      tests/test_error_catalog.py -q`):

          ...........................                                  [100%]
          27 passed in 63.42s (0:01:03)

      PROOF (`python -m deepreason explain-error RESULTS_ROOT_NOT_FOUND`, rc=0):

          The path given to `deepreason results` holds no run.
          What this means: `deepreason results` accepts either a run root (a
          directory holding `log.jsonl`, the append-only record of one run) or
          a home (a directory holding a `runs/` folder of them). The path you
          gave is neither, so there is no run whose outcome could be reported.
          Next: Point it at the run root itself, or at the home holding
          `runs/` — `deepreason results <root-or-home>`. With no argument it
          reads $DEEPREASON_HOME (or ~/.deepreason).

- [x] 9. (S11, S16-defect) Add the `results` verb to `build_parser` in
      `src/deepreason/cli/main.py` with `help="read a run's typed results"`,
      an optional positional, `--json` and `--verify`; add the `_main`
      dispatch branch. Do NOT add it to `_ROOT_ADMISSION_COMMANDS` (SPEC.md
      A8).
      done-when: `deepreason --help | grep -c "read a run's typed results"` →
      `1`, and `python -m pytest
      tests/test_v6_only_cli_admission.py::test_public_parser_omits_make_and_unqualified_advanced_commands
      -q` → `1 passed`.

      PROOF:

          $ python -m deepreason --help | grep -c "read a run's typed results"
          1
          $ python -m deepreason --help | grep -A2 "^    results"
              results             read a run's typed results
              findings            reader-facing findings summary: rivalries,
          $ python -m pytest ...::test_public_parser_omits_make_and_unqualified_advanced_commands -q
          1 passed in 0.25s

      End-to-end smoke: the verb renders the grounded-extension root (rc=0),
      `--json` parses to the 12 documented top-level keys, and an unknown path
      refuses `RESULTS_ROOT_NOT_FOUND: /tmp/nowhere-at-all is neither a run
      root (no log.jsonl) nor a home holding one` with rc=1.

- [x] 10. (S11, R16) Add
      `tests/test_results_command.py::test_top_level_help_names_the_results_verb`
      — the acceptance test for the defect itself: a session given only
      `deepreason --help` can name the verb that retrieves results.
      done-when: that test passes, and it FAILS if the help string is removed
      (prove by temporary edit, revert before proceeding).

      PROOF — 4 tests pass (help text, positional parsing, and A8's
      not-admitted pin). MUTATION PROOF: replacing the help string with
      `help="reader"` turned the acceptance test red —

          tests/test_results_command.py:257: AssertionError
          FAILED ...::test_top_level_help_names_the_results_verb
          1 failed in 0.22s

      — restored, and all 4 pass again.

- [x] 11. (S18) Update `docs/map/SUB-application.md` in the SAME commit as the
      verb: Entry points row for `results_summary`/`render_results` with a
      `check:`, a "Where to change what" row, the corrected admission sentence
      naming the reader exception, and a `Traps` entry naming this tranche.
      done-when: `python tools/docs_verify.py --fast 2>&1 | tail -3` reports
      no NEW failure for `SUB-application.md`, and
      `grep -q "results_summary" docs/map/SUB-application.md` → exit 0.

      DRIFT CAUGHT AND FIXED IN THIS COMMIT, which SPEC.md's blast-radius
      census did NOT predict: `SEAM-harness-x-workflow.md`'s check counts files
      under `src/deepreason` naming both sides, pinned at 58. The new reader
      legitimately names both (`deepreason.harness` for a read-only open,
      `deepreason.workflow.lifecycle` for `RESUMABLE_STOP_REASONS`), moving it
      to 59. The gate's `consumers.map_checks` returned `[]` for `results.py`
      because that check keys off a shell grep COUNT, not a symbol name —
      exactly the class SPEC.md said the manual cross-check is retained for,
      and here the manual cross-check missed it too; `docs_verify` is what
      caught it. Count re-derived (not incremented) and both the check and its
      prose set to 59.

      Also found: that document's prose said "Fifty-seven" while its own check
      pinned 58 — already one behind before this tranche touched it. Recorded
      as `docs/ERRATA.md` E25 (next free number, ledger tail was E24).

      `Verified-at:` advanced to `15498f72` on both `SUB-application.md` and
      `SEAM-harness-x-workflow.md` — the only two documents whose checks were
      actually re-run.

      PROOF (`python tools/docs_verify.py --fast`, after the fix):

          docs_verify [fast]: 53 documents, 864 checks, 863 reused, 4 workers
            FAIL CON-run-identity.md:195 ...
            FAIL CON-run-identity.md:197 ...
            FAIL CON-run-identity.md:199 ...
          docs_verify: 3 failed

      3 failed == the docs/AUDIT_BASELINES.md baseline exactly (all three are
      the `CON-run-identity.md` git-history checks that need an unshallowed
      clone). The full — not `--fast` — run happens at step 18.

- [x] 12. (S12) Add the retrieval line to
      `.claude/skills/dr-drive-harness/SKILL.md` §2 (the public CLI lifecycle
      block) and to `README.md`'s CLI list, in the SAME commit as step 9/11.
      done-when: `grep -q "deepreason results"
      .claude/skills/dr-drive-harness/SKILL.md && grep -q "deepreason results"
      README.md` → exit 0.

      The manual's §2 entry also corrects the trap the census found: `status`
      now carries "NB: provider readiness, NOT a run's outcome — for that,
      `results` below", and the `results` entry ends "This is the ONE retrieval
      surface — do not go hunting through root files for it."

- [x] 13. (S8, S21) Run the demonstration R25 requires and capture it:
      `deepreason results
      experiments/2026-08-12-live-grounded-extension-expansion/run` and the
      same with `--json`, output saved to the tranche's `proof/` directory.
      done-when: `proof/results-grounded-extension.txt` and
      `proof/results-grounded-extension.json` exist and the JSON parses.

      PROOF: both written (45 and 118 lines); `json.load` on the second
      succeeds. Pasted in full in DELIVERY.md per R25.

- [ ] 14. (S8–S12, S18) [COMMIT] Commit the verb, catalog, help pin, map,
      manual and README together.
      done-when: `python tools/diff_budget.py origin/main --ceiling 1300 --paths
      src/deepreason tests docs/map .claude/skills README.md` → not EXCEEDED, and `git show --stat HEAD` lists
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
