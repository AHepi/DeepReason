# Checklist for: rung 2, tranche 3 — unify the bridge settings
Re-read REQUEST.md + SPEC.md before every step. Execute strictly in
order. One step per dr-execute-step invocation.

Map preflight (recorded per dr-plan-steps rule 4b): resolved to
`DR-CON-authority` (the only map document with an established `Owns:`
claim on both `src/deepreason/v6_policy.py` and
`src/deepreason/preparation.py`, added there in tranche 2). Candidates
checked and rejected: `DR-SUB-bridge` owns `src/deepreason/bridge/` —
the actual bridge WORKFLOW directory (ledger/compose/evidence packs), a
completely different code area from `config.py::BridgeConfig`/
`v6_policy.py::engaged_bridge_source`; `DR-SUB-manifest` owns
`run_manifest.py`/`qualification.py` — manifest compilation/validation,
not preset construction. No document specifically covers "engaged
preset construction hygiene" as its own concept, and `INDEX.md` lists no
such document; creating one for a ~50-line tranche would be
disproportionate. `DR-INV-frozen-surfaces` read (already fresh from
tranche 2) — confirmed not touched by this tranche's design (SPEC.md's
"Key technical finding," verified by direct test, not inferred).

- [x] 1. (S1) Change `src/deepreason/v6_policy.py::engaged_bridge_source()`'s
      body to build the same 5 values through a validated `BridgeConfig`
      instance instead of a bare literal dict (import `BridgeConfig`
      from `deepreason.config`; keep the function's return type and
      exact 5-key shape unchanged; docstring unchanged).
      done-when: `python -c "import inspect; from deepreason import v6_policy as p; src = inspect.getsource(p.engaged_bridge_source); assert 'BridgeConfig(' in src"` exits 0 AND `python -c "from deepreason.v6_policy import engaged_bridge_source as f; assert f() == {'mode': 'grounded_two_stage', 'grounding_review': True, 'max_schema_repair_attempts': 1, 'max_grounding_repair_attempts': 0, 'output_section_limit': 4}"` exits 0.
      DONE. Added `from deepreason.config import BridgeConfig` import
      (alphabetically ordered after `capabilities.policy`, before
      `run_manifest`). Function body now constructs a `BridgeConfig`
      instance with the 5 override values and projects onto the same 5
      keys via `model_dump(include={...})`. Docstring unchanged. Output:
      ```
      CHECK1_OK
      CHECK2_OK
      ```
      Not committed yet — bundled at step 7 with steps 4 and 6.

- [x] 2. (S1) Confirm the EXISTING test
      (`test_engaged_bridge_source_enables_the_reviewed_grounded_bridge`,
      `tests/test_v6_policy_preset.py`) still passes UNCHANGED — this is
      R3's own required proof, already present before this tranche.
      done-when: `python -m pytest tests/test_v6_policy_preset.py -k test_engaged_bridge_source_enables_the_reviewed_grounded_bridge -q` ends "1 passed" (paste it).
      DONE. Output: `1 passed, 13 deselected in 0.09s`. No file
      modified this step.

- [x] 3. (S2) Verification-only: confirm `BridgeConfig`'s class-level
      field defaults in `src/deepreason/config.py` received NO changes
      (Amendment 1's resolution — do not touch this file at all in
      this tranche).
      done-when: `git diff --stat <tranche-base>..HEAD -- src/deepreason/config.py` is EMPTY AND `python -m pytest tests/test_config_scratch_bridge.py -k test_safe_defaults_are_bounded_and_features_remain_opt_in -q` ends "1 passed" (paste both).
      DONE. Tranche base `899ebb18` (commit before REQUEST.md's capture,
      `59238adc`'s parent). `git diff --stat 899ebb18..HEAD --
      src/deepreason/config.py` produced no output (empty). Test output:
      `1 passed, 13 deselected in 0.06s`. No file modified this step.

- [x] 4. (S3) Add ONE new test to `tests/test_v6_policy_preset.py`
      proving `engaged_bridge_source()`'s output equals a freshly-built
      `BridgeConfig(mode="grounded_two_stage", grounding_review=True,
      max_schema_repair_attempts=1, max_grounding_repair_attempts=0,
      output_section_limit=4).model_dump(include={...same 5 keys...})`
      — the "built THROUGH BridgeConfig" property, not merely a second
      hard-coded literal.
      done-when: `python -m pytest tests/test_v6_policy_preset.py -q` ends "N passed, 0 failed" and the new test name appears in `python -m pytest tests/test_v6_policy_preset.py --collect-only -q` output (paste both).
      DONE. Added `test_engaged_bridge_source_is_built_through_bridge_config`
      right after the existing bridge-source test; imported `BridgeConfig`
      alongside the already-imported `Config`. Output:
      ```
      ...............                                                          [100%]
      15 passed in 0.21s
      ---collect---
      tests/test_v6_policy_preset.py::test_engaged_bridge_source_is_built_through_bridge_config
      ```
      Not committed yet — bundled at step 7.

- [x] 5. (S4) Run the full golden-test set SPEC.md names, to directly
      confirm zero drift (belt-and-braces beyond step 1's own
      dict-equality check — the exact class of risk tranche 2's
      Amendment 2 discovered).
      done-when: `python -m pytest tests/test_run_manifest_v4.py tests/test_run_manifest_v5_inquiry.py tests/test_incident_wave_a_v2_fixtures.py tests/test_v6_policy_preset.py tests/test_v6_engaged_public_defaults.py tests/test_config_scratch_bridge.py -q` ends "N passed, 0 failed" (paste it).
      DONE. Output: `75 passed in 15.55s`. No file modified this step.

- [x] 6. (S5) Update `docs/map/CON-authority.md` in the SAME commit as
      steps 1 and 4's code: add one new checked claim proving
      `engaged_bridge_source()` constructs through `BridgeConfig`
      (reusing step 1's own check, not duplicating a new one), with a
      short note on why this claim lives here (established `Owns:` home
      for `v6_policy.py`/`preparation.py`, not because it is
      thematically about authority) — and why `BridgeConfig`'s shared
      defaults were deliberately left untouched (Amendment 1).
      done-when: `python tools/docs_verify.py --fast` shows the new
      claim passing (or 0 new failures beyond any pre-existing,
      unrelated ones) AND `grep -q "engaged_bridge_source" docs/map/CON-authority.md` exits 0 (paste both).
      DONE. Added a new "Adjacent, not authority" section at the end of
      the document, explaining the ownership rationale plainly, plus one
      new checked claim (reusing step 1's own check verbatim). Output:
      ```
      grep: PASS
      docs_verify [fast]: 49 documents, 796 checks, 738 reused, 4 workers
      docs_verify: 0 failed
      ```
      Not committed yet — bundled at step 7.

- [x] 7. (all) [COMMIT] Commit steps 1-6 together (v6_policy.py change,
      new test, map update) as one tranche commit — code and map in the
      SAME commit per R6.
      done-when: `git log -1 --stat` shows `src/deepreason/v6_policy.py`,
      `tests/test_v6_policy_preset.py`, and `docs/map/CON-authority.md`
      all in the same commit; `git push -u origin claude/delivery-rungs-handover-m22sdy`
      succeeds (paste confirmation).
      DONE. Commit `e15103d8` (4 files: v6_policy.py, test_v6_policy_preset.py,
      CON-authority.md, this CHECKLIST.md). Push initially rejected (403 /
      fetch-first — the monitoring session had pushed X11 in the
      meantime); fetched, merged cleanly (`11e25189`, no conflicts,
      unrelated files), pushed successfully. `git rev-parse HEAD
      origin/...` both `11e25189` — confirmed synced.

- [x] 8. (all) Map check: `python tools/docs_verify.py` (full, not
      `--fast`) AND `python tools/docs_verify.py --audit`.
      done-when: both show 0 failed / 0 findings (paste both).
      DONE. Output:
      ```
      docs_verify [full]: 49 documents, 796 checks, 4 workers
      docs_verify: 0 failed
      docs_verify --audit: 0 finding(s)
      ```

- [x] 9. (S6, R4) Full gate: `python -m pytest tests/ -q -n 4`, ISOLATED
      (nothing else running concurrently — tranche 2's validation pass
      hit a resource-contention false-failure when this was violated).
      Rerun once if only the known flake
      (`test_grounded_counterexample_recovery_does_not_invent_override_on_repeat`)
      fails, per C4.
      done-when: output ends "N passed, 0 failed" (paste it).
      DONE. Output: `3292 passed, 7 skipped in 617.12s (0:10:17)`. 0
      failed; one more passed than tranche 2's 3291 baseline, matching
      this tranche's one new test. The known flake did not fire; no
      rerun needed.

- [ ] 10. (S6, R5) Root sweep: `python tools/root_sweep.py`, run in
      ISOLATION (nothing else concurrent), compared against the last
      accepted baseline (42 rows, 11 ERROR, all
      `UnsupportedRunManifestVersionError`, per ERRATA E5/E6/E8). Since
      no reader logic changes in this tranche, this run IS the
      after-answer; no fresh BEFORE capture is needed (same reasoning as
      tranche 2's CHECKLIST, confirmed sound there).
      done-when: sweep output has 42 rows, 11 ERROR (paste it, plus a
      diff against the most recent prior capture on disk if one is
      still present in the scratchpad).

- [ ] 11. (all) [COMMIT] Final push and cleanliness check.
      done-when: `git status --porcelain` is empty AND branch head is
      on `origin/claude/delivery-rungs-handover-m22sdy` (paste both).
