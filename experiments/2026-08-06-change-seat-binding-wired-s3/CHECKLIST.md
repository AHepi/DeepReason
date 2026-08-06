# Checklist for: the binding, wired — Rung S3 of role-seat separation
State: next=1 blockers=none
Map ids: DR-CON-seats (updated by step 10), DR-SUB-manifest, DR-SUB-llm,
DR-SUB-application (read-only reference points, per SPEC.md's preflight).
Re-read REQUEST.md + SPEC.md before every step. Execute strictly in
order. One step per dr-execute-step invocation.

- [ ] 1. (S7) Capture the BEFORE sweep, before any `src/` edit lands:
      `python tools/root_sweep.py experiments/2026-08-06-change-seat-binding-wired-s3/sweep-before.txt`.
      done-when: the file exists and the command's own summary line is
      pasted.

- [ ] 2. (S2) Create `src/deepreason/seat_bindings.py` with
      `GROUP_ROLES`, `GROUP_ALIASES`, `SeatBindingError`,
      `SEAT_BINDINGS_FILENAME`, `seat_bindings_path`.
      done-when: `python -c "from deepreason.seat_bindings import GROUP_ROLES, GROUP_ALIASES, SeatBindingError, SEAT_BINDINGS_FILENAME, seat_bindings_path; print(sorted(GROUP_ROLES), GROUP_ALIASES)"`
      prints `['coder', 'conjecture', 'scratch']
      {'simulation': 'conjecture'}`.

- [ ] 3. (S2) Add `parse_seat_flags` plus a new test file
      `tests/test_seat_bindings.py` covering: unknown group raises
      `SeatBindingError` code `SEAT_BINDING_GROUP_UNKNOWN`; duplicate
      group in one call raises code `SEAT_BINDING_GROUP_DUPLICATED`;
      `simulation=...` alone parses without error; `None`/`[]` returns
      `{}`.
      done-when: `python -m pytest tests/test_seat_bindings.py -q -k parse`
      passes, output pasted.

- [ ] 4. (S2) Add `write_seat_bindings`/`load_seat_bindings` plus
      tests: round-trip through a temp dir; `load_seat_bindings` on a
      path with no file returns `{}`.
      done-when: `python -m pytest tests/test_seat_bindings.py -q -k "write or load"`
      passes, output pasted.

- [ ] 5. (S3) Add `resolve_seat_bindings` (including the conflict
      check, A8) plus tests: `conjecture=A, simulation=B` (A != B)
      raises `SeatBindingError` code `SEAT_BINDING_ROLE_CONFLICT`
      naming `conjecturer`; `conjecture=A, scratch=B` (A != B) ALSO
      raises the same code naming `conjecturer` (the A8-generalized
      case); `conjecture=A, simulation=A` (same profile) does NOT
      raise; no bindings file returns `{}`.
      done-when: `python -m pytest tests/test_seat_bindings.py -q -k resolve`
      passes, output pasted.

- [ ] 6. (S2, S3) [COMMIT] Commit `seat_bindings.py` and
      `tests/test_seat_bindings.py`.
      done-when: `git log -1 --stat` shows both files, pushed.

- [ ] 7. (S1) Add `--seat` (`action="append"`, `metavar="GROUP=PATH"`)
      to the `setup` subcommand's argparse registration in
      `cli/main.py`, and the dispatch block calling
      `parse_seat_flags`/`write_seat_bindings` after
      `easy.setup_wizard(...)` succeeds, only when `args.seat` is not
      `None`.
      done-when: `deepreason setup --help` output contains `--seat`
      (paste the relevant line).

- [ ] 8. (S1) Add a `tests/test_cli_setup_seats.py` (or extend
      `tests/test_easy.py`/an existing CLI test file) proving: a
      scripted non-interactive `setup` call with `--seat
      conjecture=<path>` writes `seat-bindings.yaml` containing
      `{"conjecture": "<path>"}` under the test's `DEEPREASON_HOME`;
      a call with NO `--seat` writes no such file.
      done-when: `python -m pytest tests/test_cli_setup_seats.py -q`
      (or the extended file, named exactly) passes, output pasted.

- [ ] 9. (S1) [COMMIT] Commit the CLI wiring and its test.
      done-when: `git log -1 --stat` shows the changed files, pushed.

- [ ] 10. (S4, S9) Generalize `_config_for_profile` (optional
      `seat_bindings` parameter, default `None`, per SPEC.md's
      Concrete design section) in `preparation.py`, AND in the SAME
      commit update `docs/map/CON-seats.md`'s row 44 and its
      `_config_for_profile` `check:` line to reflect the generalized
      function (`docs/map/SCHEMA.md`'s rule: map moves with the code,
      same commit).
      done-when: `python tools/docs_verify.py --self-test` exits 0 and
      `grep -n "_config_for_profile" docs/map/CON-seats.md` shows the
      updated check line.

- [ ] 11. (S4) Add a test proving: `_config_for_profile(profile)` (no
      `seat_bindings`) produces a `roles` dict identical to today's
      `{role: dict(endpoint) for role in V3_CANONICAL_ROLES}`; with
      `seat_bindings={"conjecturer": other_profile}`,
      `config.roles["conjecturer"] == dict(other_profile.endpoint_spec())`
      while every other role still equals `dict(profile.endpoint_spec())`.
      done-when: `python -m pytest tests/test_reusable_qualification.py -q -k config_for_profile`
      (extending that existing file, since it already imports
      `_config_for_profile`) passes, output pasted.

- [ ] 12. (S4, S9) [COMMIT] Commit the `_config_for_profile`
      generalization, its test, and the `docs/map/CON-seats.md`
      update together.
      done-when: `git log -1 --stat` shows all three, pushed.

- [ ] 13. (S5) Thread the optional `seat_bindings` parameter through
      `build_preparation_manifest`, `qualification_subject_manifest`
      (and its caller `_cmd_qualify` in `cli/main.py`, resolving via
      `resolve_seat_bindings()`), and `RunPreparationService.prepare`
      (resolving via `resolve_seat_bindings(environ=self._environ,
      home=self._home)`).
      done-when: `grep -n "seat_bindings" src/deepreason/preparation.py src/deepreason/cli/main.py`
      shows the new parameter/call sites (pasted).

- [ ] 14. (S5) Add a test proving `RunPreparationService.prepare`
      with a seat-bindings file present on disk produces a compiled
      `RunManifest.roles` reflecting the bound profiles on their roles
      and the default profile everywhere else; with no file present,
      produces manifest bytes byte-identical to a captured
      before-this-tranche golden for a fixed question+profile.
      done-when: `python -m pytest tests/test_v6_engaged_public_defaults.py -q -k seat`
      (or a new test file, named exactly) passes, output pasted.

- [ ] 15. (S5) [COMMIT] Commit the threading and its test.
      done-when: `git log -1 --stat` shows the changed files, pushed.

- [ ] 16. (S8) Write the two-`MockEndpoint` routing proof: build
      `seat_bindings={"conjecturer": profile_a, "judge": profile_b}`,
      assert `_config_for_profile`'s resulting `Config.roles` per
      SPEC.md Item S8; separately build an `LLMAdapter` from
      `endpoints={"conjecturer": MockEndpoint([...], name="A",
      model="model-a"), "judge": MockEndpoint([...], name="B",
      model="model-b")}`, dispatch `adapter.call("conjecturer", ...)`
      and `adapter.call("judge", ...)`, and assert the returned
      `LLMCall.model` is `"model-a"` / `"model-b"` respectively.
      done-when: `python -m pytest tests/test_seat_bindings.py -q -k routing`
      (or a new test file) passes, output pasted.

- [ ] 17. (S8) [COMMIT] Commit the routing-proof test.
      done-when: `git log -1 --stat` shows the file, pushed.

- [ ] 18. (S7) Capture the AFTER sweep and diff against step 1's
      before file:
      `python tools/root_sweep.py experiments/2026-08-06-change-seat-binding-wired-s3/sweep-after.txt`
      then `diff experiments/2026-08-06-change-seat-binding-wired-s3/sweep-before.txt experiments/2026-08-06-change-seat-binding-wired-s3/sweep-after.txt`.
      done-when: the diff is empty (pasted).

- [ ] 19. (all) Map gate: `python tools/docs_verify.py` (full mode).
      done-when: output ends with a summary line containing "0 failed".

- [ ] 20. (all) Full gate: `pytest tests/ -q -n 4`.
      done-when: output ends "N passed, 0 failed" (pasted in full).

- [ ] 21. (S10) Write or confirm `PARKED.md`: any defect noticed while
      implementing this rung (e.g. anything found beyond A4's already-
      recorded `experimenter`-template gap) that was not fixed here.
      done-when: `PARKED.md` exists in the tranche dir.

- [ ] 22. (all) [COMMIT] Final commit of any remaining tranche
      changes, push with retry, confirm clean tree.
      done-when: `git status --porcelain` is empty and
      `git rev-parse HEAD` equals
      `git rev-parse origin/claude/seat-census-rung-s1-7gphj9`.
