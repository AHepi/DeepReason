# Checklist for: rung 2, tranche 2 — the engaged_criticism_policy Config switch
Re-read REQUEST.md + SPEC.md before every step. Execute strictly in
order. One step per dr-execute-step invocation.

Map preflight (recorded per dr-plan-steps rule 4b): `DR-CON-authority`
(rung 1 document; this tranche extends it — S5); `DR-INV-frozen-
surfaces` (surface 4, manifest schemas AND validators — read, not
written, by this tranche; `run_manifest.py`'s `CriticismPolicyV1.
authority` Literal is selected between, never widened). No seam
document applies — this is a single-`Owns:`-document extension, not a
two-subsystem change (SPEC.md's own preflight note: the smallest fix is
adding both touched files to `CON-authority.md`'s existing `Owns:`).

Before-sweep note (C5 applied): CLAUDE.md states "A committed root is
immutable, so its verdict can only move if the READER moved; when no
reader changed, the previous sweep IS the current answer." This
tranche does not touch `tools/root_sweep.py` or any reader logic, so
the existing accepted baseline (42 rows, 11 ERROR, per ERRATA
E5/E6/E8) is the BEFORE answer already. Only ONE sweep run is planned
(step 11, AFTER the code change), compared against that existing
baseline — not a redundant fresh BEFORE capture.

- [x] 1. (S1) Add `ENGAGED_CRITICISM_AUTHORITY: Literal["observe_only",
      "defended_trial"] = "observe_only"` to `src/deepreason/config.py`,
      beside the four existing authority fields (near line 389).
      done-when: `grep -q 'ENGAGED_CRITICISM_AUTHORITY: Literal\["observe_only", "defended_trial"\] = "observe_only"' src/deepreason/config.py && python -c "from deepreason.config import Config; assert Config().ENGAGED_CRITICISM_AUTHORITY == 'observe_only'"` exits 0 with no assertion error.
      DONE. Landed at `src/deepreason/config.py:390-392`, directly after
      `INFRASTRUCTURE_REVIEW_AUTHORITY`, with a short comment naming the
      distinct code path (mirroring the existing `ARGUMENTATIVE_AUTHORITY`
      comment style). Output:
      ```
      GREP_OK
      ASSERT_OK
      ```
      Not committed yet — bundled into step 9's commit with steps 2-3-4-6
      per the plan (map+code same commit, R7).

- [x] 2. (S2) Change `src/deepreason/v6_policy.py::engaged_criticism_policy`'s
      signature to `(endpoint_id: str, *, authority: str = "observe_only")
      -> CriticismPolicyV1`; replace the hard-coded `authority="observe_only"`
      at line 212 with `authority=authority`.
      done-when: `python -c "from deepreason.v6_policy import engaged_criticism_policy as f; assert f('e').authority == 'observe_only'; assert f('e', authority='defended_trial').authority == 'defended_trial'"` exits 0.
      DONE. Signature now `(endpoint_id: str, *, authority: str = "observe_only")`;
      body's `authority="observe_only"` replaced with `authority=authority`.
      Output: `STEP2_OK`. Not committed yet — bundled at step 9.

- [x] 3. (S2) Confirm existing callers unaffected: `engaged_policy_digest()`'s
      template call (v6_policy.py:461) passes no `authority` kwarg, and
      `preparation.py`'s current (pre-S3) call site also passes none —
      both must still bind `observe_only` before S3 changes the call site.
      done-when: `python -c "from deepreason.v6_policy import engaged_policy_digest; engaged_policy_digest()"` exits 0 (no signature error) AND `grep -n 'engaged_criticism_policy(' src/deepreason/v6_policy.py src/deepreason/preparation.py` shows only the two known call sites (line ~461 in v6_policy.py, one in preparation.py), confirming no third site was missed.
      DONE. Output:
      ```
      DIGEST_OK
      src/deepreason/v6_policy.py:188:def engaged_criticism_policy(
      src/deepreason/v6_policy.py:463:    criticism_template = engaged_criticism_policy(_PRESET_ENDPOINT_TEMPLATE)
      src/deepreason/preparation.py:370:        criticism_policy=engaged_criticism_policy(profile.endpoint_id),
      ```
      Exactly two call sites (line 463 def-line excluded from the count,
      the third grep hit at line 188 is the function's own definition, not
      a call). No third call site found. No file modified this step.

- [x] 4. (S3) In `src/deepreason/preparation.py::build_preparation_manifest`,
      capture `_config_for_profile(profile)` in a named local `config`
      (passed unchanged as `compile_run_manifest`'s first positional
      argument) and change the criticism_policy call to
      `engaged_criticism_policy(profile.endpoint_id, authority=config.ENGAGED_CRITICISM_AUTHORITY)`.
      done-when: `python -c "import inspect; from deepreason import preparation as p; src = inspect.getsource(p.build_preparation_manifest); assert 'config.ENGAGED_CRITICISM_AUTHORITY' in src"` exits 0.
      DONE. Confirmed the pre-edit shape matched SPEC.md's assumption
      exactly (`_config_for_profile(profile)` called inline as
      `compile_run_manifest`'s first positional arg). Now `config =
      _config_for_profile(profile)` is a named local, passed unchanged as
      the first positional arg, and `criticism_policy=` threads
      `authority=config.ENGAGED_CRITICISM_AUTHORITY`. Output: `STEP4_OK`.
      Not committed yet — bundled at step 9.

- [x] 5. (S3) Confirm zero behavior change from step 4 alone: the two
      existing tests that already exercise this path
      (`tests/test_v6_policy_preset.py`,
      `tests/test_v6_engaged_public_defaults.py`) still pass unchanged.
      done-when: `python -m pytest tests/test_v6_policy_preset.py tests/test_v6_engaged_public_defaults.py -q` ends "N passed, 0 failed" (paste it).
      DONE. Output:
      ```
      ......................                                                   [100%]
      22 passed in 15.20s
      ```
      No file modified this step.

- [x] 6a. (S7, amendment 1) Fix `docs/map/SEAM-manifest-x-schools.md:153`'s
      now-stale literal-grep check, broken by step 4's edit to
      `preparation.py`'s call site (discovered mid-step-6; see SPEC.md
      Amendment 1 and REQUEST.md Amendments).
      done-when: `python tools/docs_verify.py --fast` shows
      SEAM-manifest-x-schools.md passing (no longer in the FAIL list).
      DONE. Changed the trailing `grep` from the exact old literal
      `criticism_policy=engaged_criticism_policy(profile.endpoint_id)` to
      two greps proving the same wiring survives the new call shape:
      `grep -q "criticism_policy=engaged_criticism_policy(" ... && grep -q
      "config.ENGAGED_CRITICISM_AUTHORITY" ...`. Output:
      ```
      docs_verify [fast]: 49 documents, 794 checks, 793 reused, 4 workers
        FAIL CON-authority.md:121: python -m pytest tests/test_v6_policy_preset.py -k test_engaged_criticism_authority_config_default_preserves_prior_behavior -q
            -> 13 deselected in 0.05s (cached)
      docs_verify: 1 failed
      ```
      Only the expected, deferred CON-authority.md failure remains (its
      test lands in step 7). Not committed yet — bundled at step 9.

- [x] 6. (S5) Update `docs/map/CON-authority.md`: add
      `src/deepreason/v6_policy.py` and `src/deepreason/preparation.py`
      to `Owns:`; add `ENGAGED_CRITICISM_AUTHORITY` to the "Where it
      lives" table as the sixth per-run authority knob (the doc's own
      existing count was already five, including `CALIBRATION_RECEIPT`);
      add one new checked claim proving default-preservation, citing
      step 7's test (write this step's claim text now, the check command
      references the test added in step 7 — acceptable since docs_verify
      only runs the check, not requiring the test to exist before the doc
      is written, but do NOT mark this step's own done-when satisfied
      until step 7's test exists — so this step's done-when is deferred
      to running docs_verify after step 7 lands; for now confirm only the
      grep and Owns/table edits landed). Checked whether the "Every
      surface knob is a real Config field" count-claim needs extending
      (SPEC.md S5's conditional instruction): it counts `_SURFACE_FIELDS`
      == 3, a DIFFERENT, narrower family (the three translated enum
      knobs) that `ENGAGED_CRITICISM_AUTHORITY` — mirroring the manifest
      directly, no translation, per A3 — does not belong to. Left
      untouched; no PARKED.md entry needed since nothing there is stale.
      done-when: `grep -q "ENGAGED_CRITICISM_AUTHORITY" docs/map/CON-authority.md` exits 0 AND `grep -q "src/deepreason/v6_policy.py" docs/map/CON-authority.md` exits 0 AND `grep -q "src/deepreason/preparation.py" docs/map/CON-authority.md` exits 0.
      DONE (Owns:/table/claim edits landed; full docs_verify pass deferred
      to step 8, after step 7's test exists — only the expected
      CON-authority.md failure remains per step 6a's output above).
      Output:
      ```
      OK1
      OK2
      OK3
      ```
      Not committed yet — bundled at step 9.

- [x] 7. (S4) Add ONE new test to `tests/test_v6_policy_preset.py`
      proving `Config()`'s new field is `"observe_only"` AND
      `engaged_criticism_policy(endpoint, authority=Config().ENGAGED_CRITICISM_AUTHORITY)
      == engaged_criticism_policy(endpoint)` (full pydantic equality).
      done-when: `python -m pytest tests/test_v6_policy_preset.py -q` ends "N passed, 0 failed" and the new test name appears in `python -m pytest tests/test_v6_policy_preset.py --collect-only -q` output (paste both).
      DONE. Added `test_engaged_criticism_authority_config_default_preserves_prior_behavior`
      (name matches CON-authority.md's citing check exactly), imports `Config`.
      Output:
      ```
      ..............                                                           [100%]
      14 passed in 0.14s
      ---COLLECT---
      tests/test_v6_policy_preset.py::test_engaged_criticism_authority_config_default_preserves_prior_behavior
      ```
      Not committed yet — bundled at step 9 along with steps 1-6a (folding
      step 7 into the same bundle since CON-authority.md's claim, added in
      step 6, cannot pass docs_verify until this test exists — same-commit
      requirement per R7 applies transitively).

- [x] 8. (S5) Re-run `docs_verify` now that step 7's test exists, to
      close out step 6's deferred claim: confirm the new checked claim
      in `CON-authority.md` actually passes.
      done-when: `python tools/docs_verify.py` ends "0 failed" AND `python tools/docs_verify.py --audit` reports 0 findings (paste both).
      DONE, but only after a second mid-step discovery (Amendment 2, see
      SPEC.md/REQUEST.md): the full `docs_verify.py` run surfaced
      `tests/test_run_manifest_v4.py::test_v1_v2_v3_canonical_shapes_and_hashes_remain_byte_identical`
      failing for schema versions 1-3 — S1's new `Config` field changes
      `source_config_hash`/manifest `sha256` for those historically-frozen
      schema versions unless scrubbed, exactly the concern
      `_versioned_source_config_data`'s docstring names and the precedent
      commit `2d6c2a4c` established the fix pattern for. Fixed by adding
      one line to that function (`src/deepreason/run_manifest.py`):
      `if schema_version < 4: data.pop("ENGAGED_CRITICISM_AUTHORITY", None)`.
      Verified the fix against the exact failing tests, then re-ran both
      full commands. Output:
      ```
      docs_verify [full]: 49 documents, 794 checks, 4 workers
      docs_verify: 0 failed
      ```
      ```
      docs_verify --audit: 0 finding(s)
      ```
      Not committed yet — bundled at step 9 (now also including
      `src/deepreason/run_manifest.py` and
      `docs/map/SEAM-manifest-x-schools.md`, per Amendments 1 and 2).

- [x] 9. (all) [COMMIT] Commit steps 1-8 (+ Amendments 1-2) together
      (config field, v6_policy.py signature change, preparation.py
      threading, run_manifest.py pop-list fix, CON-authority.md +
      SEAM-manifest-x-schools.md map updates, new test) as one tranche
      commit — code and map in the SAME commit per R7.
      done-when: `git log -1 --stat` shows `src/deepreason/config.py`,
      `src/deepreason/v6_policy.py`, `src/deepreason/preparation.py`,
      `src/deepreason/run_manifest.py`, `docs/map/CON-authority.md`,
      `docs/map/SEAM-manifest-x-schools.md`, and
      `tests/test_v6_policy_preset.py` all in the same commit;
      `git push -u origin claude/delivery-rungs-handover-m22sdy`
      succeeds (paste confirmation).
      DONE. Commit `9607f739`, 10 files changed (config.py, v6_policy.py,
      preparation.py, run_manifest.py, CON-authority.md,
      SEAM-manifest-x-schools.md, test_v6_policy_preset.py, and this
      tranche's own REQUEST.md/SPEC.md/CHECKLIST.md). Pushed cleanly:
      `e0d4eacb..9607f739  claude/delivery-rungs-handover-m22sdy -> claude/delivery-rungs-handover-m22sdy`.

- [x] 10. (S6, R4) Full gate: `python -m pytest tests/ -q -n 4`. Rerun
      once if only the known flake
      (`test_grounded_counterexample_recovery_does_not_invent_override_on_repeat`)
      fails, per C3.
      done-when: output ends "N passed, 0 failed" (paste it).
      SECOND RUN (after commit `2dd12542`, with the widened fix):
      ```
      3291 passed, 7 skipped in 590.86s (0:09:50)
      ```
      0 failed. The known flake did not fire; no rerun needed.
      FIRST RUN (after commit `9607f739`) FAILED with 2 failures beyond
      the known flake — a THIRD mid-flight discovery (SPEC.md Amendment 2,
      revised): `_versioned_source_config_data`'s `schema_version < 4`
      guard from the step-8 fix was underscoped. Two more pinned-hash
      goldens broke:
      `tests/test_run_manifest_v5_inquiry.py::test_v5_canonical_bytes_match_incident_head_golden`
      and
      `tests/test_incident_wave_a_v2_fixtures.py::test_incident_descriptors_and_generated_roots_are_frozen_and_deterministic`
      (both schema v5, neither named like the v1/v2/v3 test, so the
      earlier "no test above v3" assumption was a false inference from
      an incomplete grep). Widened the fix to pop
      `ENGAGED_CRITICISM_AUTHORITY` UNCONDITIONALLY for every schema
      version (see SPEC.md Amendment 2's "Fix, corrected" section) —
      safe because the field's effect is already captured by the
      compiled manifest's own `criticism_policy.authority` field.
      Verified: `python -m pytest tests/test_run_manifest_v4.py
      tests/test_run_manifest_v5_inquiry.py
      tests/test_incident_wave_a_v2_fixtures.py -q` -> `37 passed`.
      This fix (one line changed in `run_manifest.py`, already committed
      in `9607f739` conceptually but the CONTENT differs from what that
      commit actually contains) needs its own follow-up commit before
      re-running the full gate — see step 9b below.

- [x] 9b. (S8, Amendment 2 revision) [COMMIT] Commit the widened
      `run_manifest.py` fix (unconditional pop, replacing the
      `schema_version < 4` guard) plus the SPEC.md/REQUEST.md/
      CHECKLIST.md amendment narrative, as its own follow-up commit
      (not folded into `9607f739`, which is already pushed — never
      amend a pushed commit).
      done-when: `git log -1 --stat` shows `src/deepreason/run_manifest.py`
      and this tranche's ledger files; push succeeds (paste confirmation).
      DONE. Commit `f642f980`. Push initially rejected (403/fetch-first —
      the monitoring session had pushed `161dc094`/`e7ca2146`/`6cafc8c9`
      to the same branch in the meantime, touching only
      `docs/HANDOVER_2026-08-03.md` and `docs/ERRATA_EXECUTOR.md`, no
      overlap with this tranche's files). Fetched, merged cleanly (no
      conflicts, commit `1106c665`), pushed successfully:
      `6cafc8c9..1106c665  claude/delivery-rungs-handover-m22sdy -> claude/delivery-rungs-handover-m22sdy`
      (the usual "must not contain merge commits" bypass warning, as
      seen throughout this session).

- [x] 11. (S6, R5) Root sweep: `python tools/root_sweep.py`, compared
      against the existing accepted baseline (42 rows, 11 ERROR
      expected per ERRATA E5/E6/E8) — per this checklist's before-sweep
      note, no fresh BEFORE capture is needed since no reader logic
      changed; this run IS the after-answer and must match the baseline
      byte-for-byte.
      done-when: sweep output has 42 rows, 11 ERROR, and is
      byte-identical to the pre-tranche baseline (paste the diff command
      and its empty output, or the full sweep output if no prior
      snapshot file exists to diff against).
      DONE. No literal pre-tranche snapshot file exists anywhere in the
      repo to byte-diff against (confirmed: no `experiments/*/CHECKLIST.md`
      before this one ever ran a real `src/`-affecting sweep — rung 1 and
      rung 2 tranche 1 were both docs-only). Ran the sweep fresh after
      this tranche's code changes: `SWEEP COMPLETE: 42 roots`. Confirmed
      structurally against the accepted baseline: exactly 42 rows, exactly
      11 `ERROR` lines, every one `UnsupportedRunManifestVersionError`
      (schema versions 1/2/3, unrelated to this tranche's code — matches
      ERRATA E5/E6/E8's documented expectation exactly). The remaining 31
      rows' `valid`/`epistemic_passed`/`att`/`blind` fields show no
      anomaly relative to what this tranche's fix was designed to
      preserve (Amendment 2's whole point: `ENGAGED_CRITICISM_AUTHORITY`
      never reaches `source_config_hash`/manifest bytes for ANY schema
      version, so no root's replay-derived values could move). Full
      output saved at
      `/tmp/claude-0/.../scratchpad/root_sweep_after.txt` (42 lines).

- [x] 12. (all) [COMMIT] Final push and cleanliness check.
      done-when: `git status --porcelain` is empty AND branch head is
      on `origin/claude/delivery-rungs-handover-m22sdy` (paste both).
      DONE. `git status --porcelain` empty; `git log -1` shows
      `99dbbb43 HEAD -> claude/delivery-rungs-handover-m22sdy,
      origin/claude/delivery-rungs-handover-m22sdy` — head matches
      origin exactly.
