# Checklist for: one run path — "Get rid of the old one"

State: next=20 blockers=none
Map ids: `DR-SUB-application` (owns both `application/` and `cli/` — the
single covering document for both sides), `DR-CON-run-identity`,
`DR-INV-frozen-surfaces` (read; verdict CLEAR). No `DR-SEAM-` id applies:
application × cli is internal to one subsystem document, per SPEC.md S5.3.
Re-read REQUEST.md + SPEC.md before every step. Execute strictly in order.
One step per dr-execute-step invocation.

Branch: `claude/single-run-path-unification-bhn2ob` (REQUEST.md C9).
Push with 2s/4s/8s/16s retry at every `[COMMIT]`.

---

## Commit 1 — S1, the door (both paths still exist and both still pass)

- [x] 1. (S1.2, S1.3) Create `tests/test_single_run_path.py` with the two
      configuration-space tests RED:
      `test_the_door_narrows_no_configuration_the_compiler_admits` (a
      manifest carrying a judge role ensemble + school-routed conjecture +
      `criticism_policy` reaches scheduler dispatch through the new entry)
      and `test_the_grounded_tranche_config_enters_through_the_new_door`
      (imports `experiments/2026-08-12-live-grounded-extension-expansion/
      build_manifest.py`, calls `build(root)` under a tmp
      `DEEPREASON_HOME`, drives that root through the new entry).
      done-when: `python -m pytest tests/test_single_run_path.py -q` ends
      `2 failed` with `AttributeError` naming `start_manifest_run` in both
      (RED for the intended reason, pasted)

      PROOF:
      ```
      E  AttributeError: 'TextRunApplicationService' object has no attribute 'start_manifest_run'
      tests/test_single_run_path.py:257: AttributeError
      E  AttributeError: 'TextRunApplicationService' object has no attribute 'start_manifest_run'
      tests/test_single_run_path.py:295: AttributeError
      2 failed in 1.57s
      ```
      Both RED at the intended line, not at fixture construction. One
      fixture correction was needed inside this step to get there: the
      rich manifest earned `V6_SIMULATION_TOOLCHAIN_REQUIRED` until
      `toolchains=(engaged_simulation_toolchain(),)` was supplied, the
      same argument `build_manifest.py:165` supplies.

- [x] 2. (S1.1) Add
      `test_service_entry_accepts_a_precompiled_manifest_object_and_a_manifest_path`
      to `tests/test_single_run_path.py` — parametrized over a
      `RunManifest` object and a path string, both reaching a published
      terminal.
      done-when: `python -m pytest tests/test_single_run_path.py -q` ends
      `4 failed` (2 params × 1 test + the 2 from step 1), all
      `AttributeError: start_manifest_run` (pasted)

      PROOF:
      ```
      E  AttributeError: 'TextRunApplicationService' object has no attribute 'start_manifest_run'
      E  AttributeError: 'TextRunApplicationService' object has no attribute 'start_manifest_run'
      E  AttributeError: 'TextRunApplicationService' object has no attribute 'start_manifest_run'
      E  AttributeError: 'TextRunApplicationService' object has no attribute 'start_manifest_run'
      4 failed in 2.81s
      ```

- [x] 3. (S1.1) Implement `TextRunApplicationService.start_manifest_run`
      in `src/deepreason/application/text_runs.py` per SPEC.md S1.1
      (manifest object OR path; `workload_spec_for_root` with a read-only
      harness only when `log.jsonl` exists per A7; `token_budget=None` →
      `"unlimited"` per M1; delegates to `self.start(...,
      manifest_override=manifest)`), and add it to the module `__all__`.
      done-when: `grep -q "    def start_manifest_run(" src/deepreason/application/text_runs.py`
      exits 0 AND `python -c "from deepreason.application.text_runs import TextRunApplicationService as S; assert hasattr(S, 'start_manifest_run')"`
      exits 0

      PROOF:
      ```
      GREP OK
      ATTR OK
      ```
      The method resolves the manifest (object or path), resolves the
      workload read-only, translates an absent ceiling, and delegates to
      `start`. It inspects nothing about the manifest -- pinned by a new
      `check:` in `docs/map/SUB-application.md`, mutation-proved:
      injecting `manifest.criticism_policy` into the method body takes the
      check to rc=1, removing it returns rc=0.

- [x] 4. (S1.1) Export `start_manifest_run` reachability from
      `src/deepreason/application/__init__.py` — no new name is exported
      if the service object already carries the method; confirm which,
      and if `__all__` there needs no change, record that as the
      done-criterion output instead of editing.
      done-when: `python -c "from deepreason.application import TEXT_RUN_SERVICE; assert callable(TEXT_RUN_SERVICE.start_manifest_run)"`
      exits 0

      PROOF:
      ```
      SERVICE OK
      ```
      `src/deepreason/application/__init__.py` needed NO edit: the method
      hangs off the already-exported `TEXT_RUN_SERVICE` singleton, so
      there is no new module-level name to export. Recorded rather than
      edited, per the step's own instruction.

- [x] 5. (S1) Ring green for the new door.
      done-when: `python -m pytest tests/test_single_run_path.py -q` ends
      `4 passed` (pasted)

      PROOF:
      ```
      ....                                    [100%]
      4 passed in 22.65s
      ```

- [x] 6. (S1) Ring green for the existing managed path — the new entry
      must not have disturbed it.
      done-when: `python -m pytest tests/test_application_text_runs_d0.py tests/test_v6_only_application_admission.py tests/test_lifecycle_operation_parity.py -q`
      ends `0 failed` (pasted)

      PROOF:
      ```
      ..................................................    [100%]
      50 passed in 28.49s
      ```

- [x] 7. (S1) [COMMIT] Commit and push commit 1 (the door, its tests, no
      deletion yet).
      done-when: `git status --porcelain` empty AND
      `git rev-parse HEAD` == `git rev-parse origin/claude/single-run-path-unification-bhn2ob`

      PROOF: see the commit below. Map moved in this same commit
      (`docs/map/SUB-application.md`) because step 3 added a public entry
      point, which is a surface change, not a later documentation chore.

      One map-gate incident inside this step, recorded because it is the
      form-brittleness `SCHEMA.md` warns about: the new method's DOCSTRING
      contained the word "school", which moved
      `SEAM-manifest-x-schools.md`'s coupling census from 24 to 25 files
      and failed that document's check. Fixed by rewording the docstring
      (role ensembles / route-bound seats / adjudication policy), NOT by
      editing another subsystem's expected count -- a prose word must not
      be able to change a coupling measurement.
      ```
      $ python -u tools/docs_verify.py --failed
      docs_verify: 3 failed
      # all three CON-run-identity.md git-history checks, the exact
      # docs/AUDIT_BASELINES.md baseline for a shallow clone. Delta = 0.
      ```

---

## Commit 2 — S2 + S3, the alias, the deletion, the migrations, the map

- [x] 8. (S3.2) Dead-census SCAN 1, taken BEFORE any deletion: repo-wide
      reference counts for `_execute_bound_run` and for every symbol that
      loses its `cli/main.py` caller (`ops.run_scheduler`,
      `attach_bound_evidence_once`, `ensure_lifecycle_documents`,
      `completed_cycles`, `workload_spec_for_root`,
      `terminalize_text_run`), written to
      `experiments/2026-08-13-change-single-run-path-unification/proof/dead-census.txt`.
      done-when: `test -s experiments/2026-08-13-change-single-run-path-unification/proof/dead-census.txt`
      AND the file contains a `SCAN 1` section with one line per symbol

      PROOF: `proof/dead-census.txt`, 89 lines, `SCAN 1` at HEAD c9a476130.
      `_execute_bound_run` src=2 (its own def and its one call site),
      tests=2, docs=2. Every other censused symbol has src callers
      besides `cli/main.py` recorded verbatim, which is what SCAN 2 will
      be compared against.

- [x] 9. (S2.1) Add `test_run_verb_parser_surface_is_byte_identical` to
      `tests/test_single_run_path.py` — pins the `run` subparser's option
      strings, defaults and `required` flags against a literal expected
      table, so a later edit to `build_parser` fails loudly.
      done-when: `python -m pytest tests/test_single_run_path.py::test_run_verb_parser_surface_is_byte_identical -q`
      ends `1 passed` against the UNCHANGED parser (it is a pin, green
      before and after)

      PROOF: green as part of the 7-test file run below. The pin is the
      full introspected action table -- option strings, dest, default,
      required, action class -- so removing a flag, changing a default or
      making one required fails it.

- [x] 10. (S2.2) Add `test_run_exit_code_contract_is_run_result_exit_code`
      and `test_run_preflight_refusals_still_exit_one` RED.
      done-when: `python -m pytest tests/test_single_run_path.py -q` shows
      the exit-code test failing and the preflight test PASSING (the
      refusal path is already `1`; pasted)

      PROOF:
      ```
      FAILED tests/test_single_run_path.py::test_run_exit_code_contract_is_run_result_exit_code[failed]
      1 failed, 7 passed in 27.65s
      ```
      DEVIATION recorded, not silently absorbed: the test as first written
      (completed -> 0 only) PASSED against the old path, because a
      completed run maps to 0 under both behaviors. A pin that cannot fail
      is not a pin (dr-execute-step rule 3), so it was parametrized to add
      the discriminating case -- a scheduler that DIES mid-run. On the old
      path that leaves exit 1 and NO published terminal
      (`FileNotFoundError: .../exit-failed/run-result.json`); on the one
      path it publishes `state=failed` and exits 4.

- [x] 11. (S2.1, S2.2) Rewrite `_cmd_run`'s dispatch tail in
      `src/deepreason/cli/main.py`: keep budget parse, `_admit_v6_root`,
      `--run-manifest` conflict, workload-profile check,
      `require_v6_launch_allowed`, `require_full_engine`, `--problem`
      preflight and `--dry-run` unchanged and in order; REMOVE
      `require_v6_production_qualification` and the `operator_locks`
      acquisition (the service performs both, qualification first);
      dispatch through `TEXT_RUN_SERVICE.start_manifest_run` → `wait` →
      `result`; render `survivors (N):`, the frontier lines and the theory
      from the published terminal payload; return `terminal.exit_code()`
      for terminal outcomes and `1` for pre-terminal refusals.
      done-when: `grep -q "start_manifest_run" src/deepreason/cli/main.py`
      AND `! grep -q "require_v6_production_qualification" src/deepreason/cli/main.py`
      (both exit 0)

      PROOF:
      ```
      ALIAS OK
      QUALIFICATION RELOCATED OK
      ```
      The rendering moved into a named `_dispatch_managed_run`, which
      qualifies nothing and locks nothing: both live in `_launch`, in that
      order, for every configuration. `config_from_run_manifest` also left
      `_cmd_run` -- the worker builds the config it runs from.

- [x] 12. (S3.1) Delete `_execute_bound_run` from
      `src/deepreason/cli/main.py` in full.
      done-when: `! grep -q "_execute_bound_run" src/deepreason/cli/main.py`
      exits 0

      PROOF:
      ```
      removing lines 2818..2938 (121 lines)
      DELETED OK
      IMPORT OK
      COMPILE OK
      ```

- [x] 13. (S3.3) Migrate `tests/test_lifecycle_operation_parity.py`'s
      `_launch_through_cli` helper from `cli_module._execute_bound_run(...)`
      to the `run` verb through `main([...])`, keeping every one of its
      test functions and their assertions.
      done-when: `python -m pytest tests/test_lifecycle_operation_parity.py -q`
      ends `0 failed` AND `grep -c "^def test_" tests/test_lifecycle_operation_parity.py`
      is unchanged from its pre-step value (both pasted)

      PROOF:
      ```
      11 passed in 29.99s
      test count before: 11   after: 11
      ```
      The helper now drives `main(["--root", ..., "run", "--budget", ...,
      "--problem", ..., "--run-manifest", ...])`. Nothing was deleted; the
      now-unused `SimpleNamespace` import went with the direct call.

- [x] 14. (S3.3) Migrate
      `tests/test_v6_global_dispatch_guard.py::test_execute_bound_run_v6_launch_policy_precedes_harness`
      to assert the same property (V6_LAUNCH_DISABLED before any
      `Harness`, root untouched) through `_cmd_run`.
      done-when: `python -m pytest tests/test_v6_global_dispatch_guard.py -q`
      ends `0 failed` AND `grep -c "^def test_" tests/test_v6_global_dispatch_guard.py`
      is unchanged (pasted)

      PROOF:
      ```
      30 passed in 60.68s
      test count: 23 (was 23)
      ```
      Renamed to `test_run_v6_launch_policy_precedes_harness_and_dispatch`
      and STRENGTHENED: it now forbids `Harness` in both the cli module and
      `deepreason.harness`, forbids `TEXT_RUN_SERVICE.start_manifest_run`,
      and asserts a byte-identical root snapshot on a REAL bound root
      (the old version used a bare nonexistent path).

- [x] 15. (S3.3) Migrate
      `tests/test_v6_only_cli_admission.py::test_run_requires_qualification_before_operator_lock`
      to patch `deepreason.application.text_runs.operator_locks` — the
      binding the service actually calls.
      done-when: the test FAILS when the patch target is reverted to
      `deepreason.locking.operator_locks` and the qualification check is
      stubbed out, and PASSES as migrated; both runs pasted (a pin that
      cannot fail is not a pin)

      PROOF:
      ```
      === migrated: expect PASS ===         1 passed in 0.40s
      === mutation: stub qualification ===  1 failed in 0.54s
                                            tests/...:395: Failed
      === restored: expect PASS ===         1 passed in 0.40s
      ```
      The mutation removes the qualification gate so the lock IS reached;
      the forbid fires. That proves the new patch target
      (`deepreason.application.text_runs.operator_locks`) is the live
      binding, which the old target
      (`deepreason.locking.operator_locks`) no longer is -- `text_runs`
      binds `operator_locks` at import.

- [x] 16. (S3.2) Dead-census SCAN 2, after the deletion: same symbols,
      same command, appended to `proof/dead-census.txt` as a `SCAN 2`
      section, plus a verdict line per symbol.
      done-when: `grep -q "SCAN 2" experiments/2026-08-13-change-single-run-path-unification/proof/dead-census.txt`
      AND every non-target symbol shows ≥1 surviving caller (any symbol
      that does not is a STOP, not a deletion)

      PROOF: `proof/dead-census.txt` SCAN 2 + SCAN 3 + a per-symbol
      VERDICT block. The census DID find one orphan, which is why it
      exists: `attach_bound_evidence_once` fell to src 2 (its own def and
      its `__all__` entry) and tests 0 -- its only caller in the entire
      tree was the deleted `_execute_bound_run`. It is the lifecycle
      tranche's bare-path retrofit, which R7 authorizes removing by name,
      and the managed worker attaches bound evidence directly through
      `evidence.render.attach_bound_evidence`. Deleted, and
      `test_manifest_launched_root_renders_its_bound_evidence` still
      passes through the alias without it. SCAN 3 records the result:
      src 4 -> 2 -> 0. Every other censused symbol keeps callers, listed
      file:line.

- [x] 17. (S5.3) Update `docs/map/SUB-application.md` in this same commit:
      entry-points list gains `start_manifest_run` and drops
      `cli.main._execute_bound_run`; the "What ANY finished run writes at
      stop" row restated for one path; the bare-path Trap REWRITTEN (never
      deleted) to record that the split was closed by unification on
      2026-08-13; the `check:` at line 201 replaced by one that would fail
      if a second path reappeared (`! grep -q "run_scheduler"
      src/deepreason/cli/main.py`).
      done-when: `python tools/docs_verify.py 2>&1 | tail -5` shows no
      NEW failure for `SUB-application.md` versus the
      `docs/AUDIT_BASELINES.md` baseline (pasted)

      PROOF: all 44 checks in the two edited documents re-run directly
      (the same way `docs_verify` runs them); 3 failed, all three the
      `CON-run-identity.md` git-history checks that need an unshallowed
      clone -- the exact AUDIT_BASELINES baseline. Delta 0. The new
      one-path check is a NEGATION and was mutation-proved: reinstating an
      `ops.run_scheduler` import in `cli/main.py` takes it to rc=1,
      removing it returns rc=0.

- [x] 18. (S5.3) Update `docs/map/CON-run-identity.md` in this same
      commit: the "Every launch path's one shared route to a terminal" row
      loses "(called by `_worker` AND by `cli.main._execute_bound_run`)";
      the "Assuming a root that ran real cycles can be continued" Trap
      gains the unification date; the `check:` at line 241 replaced the
      same way as step 17.
      done-when: `python tools/docs_verify.py 2>&1 | tail -5` shows
      failures == baseline (3 `CON-run-identity.md` git-history failures
      on this shallow clone, 0 others), pasted

      PROOF: same 44-check run as step 17 -- `3 failed`, all git-history.
      The document's own "one shared route to a terminal" row now names
      `_worker` and `finalize_stopped_root` and states that `cli/` calls
      neither a scheduler nor a terminalization; its trap gains the
      supersession and its check became the same negation.

- [x] 19. (S2, S3) Ring green across everything the alias and the deletion
      touch.
      done-when: `python -m pytest tests/test_single_run_path.py tests/test_lifecycle_operation_parity.py tests/test_v6_global_dispatch_guard.py tests/test_v6_only_cli_admission.py tests/test_run_manifest.py tests/test_workload_text.py tests/test_engine_profile_dispatch.py tests/test_application_text_runs_d0.py -q`
      ends `0 failed` (pasted)

      PROOF:
      ```
      236 passed in 132.15s (0:02:12)
      ```

      ALSO IN THIS COMMIT, under REQUEST.md Amendment 1 (the operator's
      two mid-execution questions about the token-steering controller and
      the dynamic token allocation): a ninth test,
      `test_the_door_carries_the_token_steering_authority`, drives a
      manifest with `config_referee` ENABLED through the door and asserts
      the scheduler receives it byte-identically, with `research` and
      `simulation` intact, an absent `--token-budget` still unbounded, and
      the cycle count intact. Mutation-proved: a door that strips
      `config_referee` fails it. This is R2's existing obligation ("no
      narrowing") proved for the specific lever the operator asked about,
      not new scope.

- [ ] 20. (S2, S3) [COMMIT] Commit and push commit 2 (alias + deletion +
      migrations + BOTH map documents in one commit, per CLAUDE.md's
      same-commit rule and SPEC.md's split rejection).
      done-when: `git status --porcelain` empty AND
      `git show --stat HEAD` lists `src/deepreason/cli/main.py`,
      `docs/map/SUB-application.md` and `docs/map/CON-run-identity.md`

---

## Commit 3 — S4 proofs, errata, the law's mechanism sentence

- [ ] 21. (S4.1) Add
      `test_run_identity_is_deterministic_through_the_one_road` to
      `tests/test_single_run_path.py`: compiling the acceptance fixture
      twice yields manifest sha256
      `8e22d0431fd2b98dc915c66f2f3ccc6dc43184b4c326ff5d388a7c013a80989d`
      both times, and the launched root's `progress.jsonl` records
      `run_id` equal to that digest.
      done-when: `python -m pytest tests/test_single_run_path.py::test_run_identity_is_deterministic_through_the_one_road -q`
      ends `1 passed` (pasted)

- [ ] 22. (S4.3) Replay proof: run `verify_root_report` READ-ONLY over the
      committed grounded-extension root and two other committed roots,
      writing output to
      `experiments/2026-08-13-change-single-run-path-unification/proof/replay.txt`.
      done-when: `test -s .../proof/replay.txt` AND each root's `valid`
      matches its prior recorded verdict (the comparison stated in the
      file, not inferred)

- [ ] 23. (S4.4) Prove the out-of-scope surfaces are untouched.
      done-when: `git diff --stat origin/main -- src/deepreason/mcp_server.py src/deepreason/qualification.py scripts/ experiments/2026-08-12-live-grounded-extension-expansion/grounded_run.sh`
      prints nothing

- [ ] 24. (S5.5) Append **E26** to `docs/ERRATA.md` recording the two
      committed statements that describe two launch paths calling one
      terminalization (`CLAUDE.md`'s operations-parity law mechanism
      sentence; `docs/map/CON-run-identity.md:55`), what remains true (the
      law itself), and this tranche as the supersession.
      done-when: `grep -q "E26" docs/ERRATA.md` exits 0 AND the entry
      names `experiments/2026-08-13-change-single-run-path-unification`

- [ ] 25. (S5.5) Update `CLAUDE.md`'s operations-parity law mechanism
      sentence for one path, leaving the operator's verbatim quote
      untouched.
      done-when: `! grep -q "both paths call" CLAUDE.md` AND
      `grep -q "available to all configurations." CLAUDE.md` (both exit 0)

- [ ] 26. (S5.4) Wheel smoke — the third instrument no gate runs.
      done-when: `python scripts/wheel_smoke.py` exits 0 AND
      `git diff --stat origin/main -- scripts/` prints nothing (no pin
      moved)

- [ ] 27. (S4, S5) [COMMIT] Commit and push commit 3.
      done-when: `git status --porcelain` empty AND branch head is on
      origin

---

## Close — the gates

- [ ] 28. (all) Map gate, FULL mode (not `--fast`; `--fast` reuses cached
      results and cannot see what a `src/` change just broke).
      done-when: `python tools/docs_verify.py` failures == the
      `docs/AUDIT_BASELINES.md` baseline (3 `CON-run-identity.md`
      git-history failures on a shallow clone, 0 others), pasted; and
      `python tools/docs_verify.py --audit` reports 0 findings

- [ ] 29. (all) Full gate, on an otherwise idle box (never concurrently
      with `docs_verify` — both fan out workers and the contention
      manufactures failures).
      done-when: `python -m pytest tests/ -q -n 4` ends with 0 failed
      beyond the single baseline failure
      `tests/test_bronze_report.py::test_census_totals_internally_consistent`
      (`docs/AUDIT_BASELINES.md`); output pasted

- [ ] 30. (all) [COMMIT] Final push and clean-tree confirmation.
      done-when: `git status --porcelain` empty AND
      `git rev-parse HEAD` == `git rev-parse origin/claude/single-run-path-unification-bhn2ob`
