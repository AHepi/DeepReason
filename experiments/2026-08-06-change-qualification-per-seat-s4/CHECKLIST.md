# Checklist for: qualification per seat — Rung S4 of role-seat separation
State: next=20 blockers=none
Map ids: DR-SUB-manifest (qualification subject digests), DR-SUB-application
(cli/main.py, readiness.py, preparation.py), DR-CON-seats. No SEAM
document exists naming seats x manifest specifically; DR-CON-seats'
own Seams: header already points at DR-SEAM-llm-x-manifest for the
underlying mechanism — read there if anything below contradicts it.
Re-read REQUEST.md + SPEC.md before every step. Execute strictly in
order. One step per dr-execute-step invocation.

- [x] 1. (S8) Capture the BEFORE sweep, before any `src/` edit:
      `python tools/root_sweep.py experiments/2026-08-06-change-qualification-per-seat-s4/sweep-before.txt`.
      done-when: file exists, summary line pasted.
      DONE: `SWEEP COMPLETE: 45 roots -> sweep-before.txt`.

- [x] 2. (S6) Capture BEFORE output for `deepreason qualify --json`
      and `deepreason status --json` against a single-profile (no
      `--seat`) test home, before any `src/` edit:
      write both outputs to
      `experiments/2026-08-06-change-qualification-per-seat-s4/before-qualify.json`
      and `.../before-status.json` (using an injected/mocked executor
      so no real provider call is needed).
      done-when: both files exist, non-empty.
      DONE: canonical capture script committed as
      `capture_qualify_status.py` (reused identically for the AFTER
      capture at step 18); `before-qualify.json`/`before-status.json`
      both populated (pasted content above).

- [x] 3. (S1) Promote the dispatch-purity measurement
      (`measure_dispatch.py`) into a committed regression test,
      `tests/test_qualification_per_seat.py::test_heterogeneous_manifest_dispatches_with_zero_cross_contamination`
      — 3 roles (2 explicitly bound to different profiles, 1 default),
      asserting `ALL ROLES DISPATCH-PURE` per M5's own shape.
      done-when: `python -m pytest tests/test_qualification_per_seat.py -q -k dispatch_purity`
      passes, output pasted.
      DONE: `1 passed, 1 deselected in 0.45s`.

- [x] 4. (S1) Add the mutation-companion test proving step 3's test
      CAN fail: temporarily wire a SHARED fake endpoint across roles
      (simulating a hypothetical regression where role identity is
      lost) and confirm the purity assertion catches it, then restore.
      done-when: `python -m pytest tests/test_qualification_per_seat.py -q -k mutation`
      passes, output pasted.
      DONE: `1 passed, 1 deselected in 0.28s`. Test named
      `test_dispatch_purity_mutation_companion_can_actually_fail`
      (first attempt's name lacked "mutation", missing the filter;
      renamed).

- [x] 5. (S1) [COMMIT] Commit `tests/test_qualification_per_seat.py`.
      done-when: `git log -1 --stat` shows the file, pushed.
      DONE: commit `0d86b5c5`, pushed.

- [x] 6. (S5) Add the R4 pinning test to
      `tests/test_run_preparation_service.py`: a two-profile home
      where the COMBINATION is unqualified — `prepare()` raises the
      EXACT typed error M6 measured (`QualificationError` code
      `QUALIFICATION_NOT_CONFIGURED`, pinned exactly); once the
      combination IS qualified (injected test executor), `prepare()`
      succeeds and the committed run manifest's roles reflect both
      profiles.
      done-when: `python -m pytest tests/test_run_preparation_service.py -q -k combination`
      passes, output pasted. Confirms ZERO `src/` changes were needed
      for this to pass (git status shows only the test file changed).
      DONE: `2 passed, 11 deselected in 5.74s`; `git status --porcelain -- src/`
      empty, confirming M6's claim (R4 needs zero new production code).

- [x] 7. (S5) [COMMIT] Commit the combination pinning test.
      done-when: `git log -1 --stat` shows the file, pushed.
      DONE: commit `f33ffa3d`, pushed.

- [x] 8. (S2) Add `_cmd_qualify`'s additive per-profile loop in
      `cli/main.py`: default + every distinct bound profile (deduped
      by `profile_digest`, excluding ones equal to default), each
      qualified via the extracted per-profile body with NO
      `seat_bindings`; the EXISTING combination-qualify call
      (unmodified) still runs too when seat bindings exist.
      done-when: `python -c "import deepreason.cli.main"` succeeds
      (import smoke check, learned from Rung S3's step 13 mishap).
      DONE: `IMPORT_OK`. Extracted `_qualify_one_profile(profile_path,
      *, args, seat_bindings=None) -> dict | None` (per-profile body,
      unmodified logic, `None` return means a refusal/cancellation was
      already printed). `_cmd_qualify` now: calls it once for the
      combination (`seat_bindings=resolve_seat_bindings() or None`,
      byte-identical call to pre-S4 when no bindings exist -- this IS
      the loop's one iteration for R6); when bindings exist, loops
      `sorted(load_seat_bindings(...))`, dedupes by `profile_digest`
      against the default's digest, and calls the same helper with
      `seat_bindings=None` for each distinct bound profile. Existing
      qualify/qualification_per_seat tests: `8 passed, 2 skipped`.

- [x] 9. (S2, R6) Add a test proving the single-profile case (no
      `--seat`) produces a payload byte-identical in shape to pre-S4
      (loop has exactly one iteration, no new keys).
      done-when: `python -m pytest tests/test_qualification_per_seat.py -q -k single_profile`
      passes, output pasted.
      DONE: `1 passed, 3 deselected in 3.80s`.
      `test_single_profile_home_qualify_output_is_byte_identical_to_pre_s4`
      runs `deepreason qualify --yes --json` against a fresh home built
      from the exact fixture `capture_qualify_status.py` used, and
      asserts the printed payload equals `before-qualify.json` exactly
      (not just same keys) -- the combination call IS the loop's only
      iteration when no `--seat` bindings exist.

- [x] 10. (S2) Add a test proving a two-distinct-profile home: the
      per-profile loop qualifies both, AND the existing combination
      call still qualifies the combination — output names all three
      outcomes distinctly.
      done-when: `python -m pytest tests/test_qualification_per_seat.py -q -k two_profile`
      passes, output pasted.
      DONE: `1 passed, 3 deselected in 7.72s`. Test named
      `test_two_profile_home_qualifies_each_seat_plus_the_combination`
      (first attempt lacked the exact "two_profile" substring --
      "two_distinct_profile" doesn't match the `-k two_profile` filter;
      renamed, same lesson as Rungs S3/S4's earlier filter-name
      mishaps). Asserts the top-level payload's `"combination"` and
      `"seats"` entries carry distinct `qualification_subject_digest`
      values -- the three outcomes are not conflated.

- [x] 11. (S2) [COMMIT] Commit `_cmd_qualify`'s per-profile loop and
      its tests.
      done-when: `git log -1 --stat` shows the changed files, pushed.
      DONE: commit `68b5b69b`, pushed
      (`f33ffa3d..68b5b69b claude/seat-census-rung-s1-7gphj9 ->
      claude/seat-census-rung-s1-7gphj9`).

- [x] 12. (S3) Add `readiness.py::get_seat_readiness` and
      `SeatReadinessV1` — default + each raw `{group: path}` entry,
      readiness computed via the per-profile uniform subject (shared
      helper extracted from `get_readiness`); `ReadinessV1`/
      `get_readiness`/the MCP tool untouched.
      done-when: `python -c "import deepreason.readiness"` succeeds;
      a quick no-bindings call returns `()` (pasted).
      DONE: `()`. Extracted `_readiness_fields(explicit_profile_path,
      *, environ, home, qualification_cache_dir) -> dict` (the shared
      per-profile logic, previously `get_readiness`'s entire body);
      `get_readiness` now just wraps it in `ReadinessV1` -- confirmed
      byte-identical since it's the same code, only relocated.
      `get_seat_readiness` returns one `SeatReadinessV1(group=...)`
      per RAW bound `{group: path}` entry (sorted), each via the same
      helper with `qualification_subject_manifest(profile)` (no
      seat_bindings). `grep` confirms `get_readiness`/`ReadinessV1`/
      the MCP `get_readiness` tool (`mcp_server.py`) reference nothing
      changed. `tests/test_cli_readiness.py`: `3 passed`.

- [x] 13. (S3) Add a test: two bound groups produce 2
      `SeatReadinessV1` entries with correct per-profile
      `qualification_state`, independent of combination-qualify
      status.
      done-when: `python -m pytest tests/test_qualification_per_seat.py -q -k seat_readiness`
      passes, output pasted.
      DONE: `1 passed, 4 deselected in 3.80s`.
      `test_seat_readiness_two_bound_groups_independent_of_combination`
      seeds ONLY the "coder" seat's own uniform subject as completed
      (`resolve_completed_qualification` directly), leaves "scratch"
      unqualified, and never qualifies the combination at all --
      `get_seat_readiness` still correctly reports coder=ready,
      scratch=unqualified.

- [x] 14. (S3) [COMMIT] Commit `get_seat_readiness`/`SeatReadinessV1`
      and their test.
      done-when: `git log -1 --stat` shows the changed files, pushed.
      DONE: commit `7ef63b01`, pushed
      (`68b5b69b..7ef63b01 claude/seat-census-rung-s1-7gphj9 ->
      claude/seat-census-rung-s1-7gphj9`).

- [x] 15. (S4) Extend `_cmd_status` in `cli/main.py`: when
      `get_seat_readiness()` is non-empty, print an additional
      "Per-seat readiness" section (text) / add a `"seats"` key to a
      new wrapping JSON object (`--json`); empty case untouched.
      done-when: `python -c "import deepreason.cli.main"` succeeds.
      DONE: `IMPORT_OK`. Empty-seats branch prints exactly
      `readiness_json(readiness)`/`readiness_text(readiness)` as
      before (untouched code path, R6). Non-empty: JSON case parses
      `readiness_json`'s own output and adds a `"seats"` list; text
      case prints `readiness_text` then an indented "Per-seat
      readiness:" block per seat group. Return code stays keyed to
      the default profile's own `readiness.ready` (unchanged
      semantics -- launch capability is a combination-qualify
      question per M6, not a status-command concern).

- [x] 16. (S4) Add a test: two-seat home's `deepreason status --json`
      names both seats; single-profile home's output is BYTE-IDENTICAL
      to step 2's captured before-file.
      done-when: `python -m pytest tests/test_qualification_per_seat.py -q -k status`
      passes, output pasted; `diff` against
      `before-status.json` for the single-profile case is empty
      (pasted).
      DONE: `2 passed, 5 deselected in 3.79s`.
      `test_status_single_profile_home_output_is_byte_identical_to_pre_s4`
      asserts `payload == before_payload` directly; independently
      re-verified with a standalone `diff` of a fresh capture against
      `before-status.json`: `DIFF_EMPTY` (no output lines).
      `test_status_two_seat_home_names_both_seats` asserts the
      `"seats"` key names both bound groups with correct model ids.

- [x] 17. (S4) [COMMIT] Commit `_cmd_status`'s extension and its test.
      done-when: `git log -1 --stat` shows the changed files, pushed.
      DONE: commit `1da24da7`, pushed
      (`7ef63b01..1da24da7 claude/seat-census-rung-s1-7gphj9 ->
      claude/seat-census-rung-s1-7gphj9`).

- [x] 18. (S6) Capture AFTER output for `deepreason qualify --json`/
      `deepreason status --json` against the SAME single-profile test
      home as step 2, and diff both against the before-files.
      done-when: both diffs empty (pasted).
      DONE: `python capture_qualify_status.py after` (same script as
      step 2), then `diff before-qualify.json after-qualify.json` ->
      `QUALIFY_DIFF_EMPTY`; `diff before-status.json after-status.json`
      -> `STATUS_DIFF_EMPTY`. `after-qualify.json`/`after-status.json`
      committed alongside the before-files as durable evidence.

- [x] 19. (S8) Capture the AFTER sweep and diff against step 1's
      before file.
      done-when: diff empty (pasted).
      DONE: `SWEEP COMPLETE: 45 roots -> sweep-after.txt`;
      `diff sweep-before.txt sweep-after.txt` -> `SWEEP_DIFF_EMPTY`.

- [ ] 20. (all) Map gate: `python tools/docs_verify.py` (full mode).
      done-when: summary line contains "0 failed".

- [ ] 21. (all) Full gate: `pytest tests/ -q -n 4`.
      done-when: output pasted in full; net of the already-diagnosed
      pre-existing failure (Rungs S1/S3's PARKED.md P1/P3),
      independently re-confirmed unrelated via
      `git log --oneline <tranche-base>..HEAD -- src/deepreason/harness.py src/deepreason/module_events.py tests/test_module_fingerprints.py`
      being empty.

- [ ] 22. (S9) Write `PARKED.md`: record Rung S4b (Option 1 from
      SPEC.md revision 1 — per-role provenance so N models mix freely
      without a fresh combination battery per new combination) as a
      ready-to-run future tranche with its own frozen-surface-5 gate,
      plus the already-known P1 (Rungs S1/S3's pre-existing test
      failure) pointer.
      done-when: `PARKED.md` exists.

- [ ] 23. (all) [COMMIT] Final commit of any remaining tranche
      changes, push with retry, confirm clean tree.
      done-when: `git status --porcelain` empty; `git rev-parse HEAD`
      equals `git rev-parse origin/claude/seat-census-rung-s1-7gphj9`.
