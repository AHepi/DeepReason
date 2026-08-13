# Checklist for: retire the calibration-receipt dead-end gate on argumentative status authority
State: next=12 blockers=none
Map ids: DR-CON-authority, DR-SUB-manifest, DR-INV-frozen-surfaces (surface 4).
DR-SEAM-authority-x-manifest does not exist (pre-existing undocumented pair,
CON-authority.md's own header; not created this tranche — SPEC.md "Out of scope").
Re-read REQUEST.md + SPEC.md before every step. Execute strictly in order.
One step per dr-execute-step invocation.

Reordered after step 1 (see SPEC.md Addendum 1, and dr-execute-step's own
map-obligation rule: "a step that changes ... updates the covering
document in the SAME commit"). The original plan split code+tests
(commit at old step 7) from the map delta (commit at old step 11) — that
violated the same-commit rule. Map edits now land BEFORE the one commit
that lands code+tests+map together.

- [x] 1. (S1,S2,S3) Edit `src/deepreason/run_manifest.py`: rewrite
      `_preflight_text_authority` to accept an optional `notices:
      list[CompileNoticeV1] | None = None` keyword parameter and emit a
      `CompileNoticeV1` per issue via `_emit_compile_notice` (with the
      `resolution` string from SPEC.md S1) instead of raising; update
      `compile_run_manifest`'s call site (line ~3310) to pass
      `notices=notices`; widen `preflight_harness`'s return type to
      `tuple[CompileNoticeV1, ...]`, build a local `notices` list, pass it
      through, and `return tuple(notices)` at the function's end; update
      both functions' docstrings per SPEC.md S1/S3.
      done-when (revised per SPEC.md Addendum 1 — a diverging-config
      scenario collides with the separate, untouched
      TEXT_AUTHORITY_POLICY_MANIFEST_MISMATCH guard; verified instead
      with a same-config recheck, proving preflight_harness's own
      recheck independently reproduces the notice):
      `python -c "
      import sys; sys.path.insert(0, 'tests')
      from test_manifest_integration import _config
      from deepreason.config import apply_overrides
      from deepreason.harness import Harness
      from deepreason.run_manifest import compile_run_manifest, preflight_harness
      import tempfile, pathlib
      config = apply_overrides(_config(), {'TEXT_RUBRIC_AUTHORITY': 'calibrated_status'})
      manifest = compile_run_manifest(config, schema_version=2, workload_profile='text', rubric_policy='require_cross_family')
      assert [n.code for n in manifest.compile_notices] == ['CALIBRATION_RECEIPT_REQUIRED'], manifest.compile_notices
      h = Harness(pathlib.Path(tempfile.mkdtemp())/'run')
      notices = preflight_harness(manifest, h, config)
      assert [n.code for n in notices] == ['CALIBRATION_RECEIPT_REQUIRED'], notices
      print('OK')
      "` -> `OK` (pasted output below)

      ```
      compile_notices: ['CALIBRATION_RECEIPT_REQUIRED']
      preflight notices: ['CALIBRATION_RECEIPT_REQUIRED']
      OK
      ```

- [x] 2. (S4) Edit `src/deepreason/authority.py`: update
      `text_status_authority_issues`'s docstring to describe disclosure
      instead of a fail-closed refusal (SPEC.md S4). Do not touch
      `calibration_receipt_is_verified` (Assumption A2).
      done-when: `python -c "import inspect; from deepreason import authority; assert 'fail-closed' not in inspect.getsource(authority.text_status_authority_issues); print('OK')"` -> `OK`
      ```
      OK
      ```

- [x] 3. (S5) Edit `tests/test_manifest_integration.py`: flip
      `test_text_status_authority_requires_calibration_receipt` (all 4
      parametrized cases) from `pytest.raises(RunManifestError,
      match="CALIBRATION_RECEIPT_REQUIRED")` to calling
      `compile_run_manifest` normally and asserting
      `[n.code for n in manifest.compile_notices] ==
      ["CALIBRATION_RECEIPT_REQUIRED"]`.
      done-when: `python -m pytest tests/test_manifest_integration.py::test_text_status_authority_requires_calibration_receipt -q` -> `4 passed`
      ```
      4 passed in 0.08s
      ```

- [x] 4. (S5) Edit `tests/test_manifest_integration.py`: flip
      `test_arbitrary_calibration_receipt_is_unverified` (all 4
      parametrized cases) the same way, asserting
      `CALIBRATION_RECEIPT_UNVERIFIED`.
      done-when: `python -m pytest tests/test_manifest_integration.py::test_arbitrary_calibration_receipt_is_unverified -q` -> `4 passed`
      ```
      4 passed in 0.09s
      ```

- [x] 5. (S5) Edit `tests/test_manifest_integration.py`: flip
      `test_blank_calibration_receipt_is_missing` the same way, asserting
      `CALIBRATION_RECEIPT_REQUIRED` (a blank string counts as missing).
      done-when: `python -m pytest tests/test_manifest_integration.py::test_blank_calibration_receipt_is_missing -q` -> `1 passed`
      ```
      1 passed in 0.07s
      ```

- [x] 6. (S5) Edit `tests/test_manifest_integration.py`: flip
      `test_materialized_text_status_authority_is_rechecked_before_adapter_build`
      and `test_runtime_calibrated_status_is_unverified_before_adapter_build`
      from `pytest.raises(...)` around `preflight_harness(...)` to calling
      it normally and asserting `[n.code for n in notices] ==
      [<CALIBRATION_RECEIPT_REQUIRED|_UNVERIFIED>]` on its returned tuple.
      Per SPEC.md Addendum 1: change each test's SCENARIO from "compile
      with the default config, recheck with a diverging one" to "compile
      with the SAME already-triggering config used for the recheck" (no
      `authority_policy_snapshot` divergence), so the untouched
      `TEXT_AUTHORITY_POLICY_MANIFEST_MISMATCH` guard stays silent and the
      test proves `preflight_harness`'s own recheck, not that unrelated
      guard. Leave `test_runtime_cannot_mutate_frozen_text_authority_policy`
      untouched — it already covers the manifest-divergence scenario via
      `CALIBRATION_RECEIPT` instead.
      done-when: `python -m pytest tests/test_manifest_integration.py::test_materialized_text_status_authority_is_rechecked_before_adapter_build tests/test_manifest_integration.py::test_runtime_calibrated_status_is_unverified_before_adapter_build tests/test_manifest_integration.py::test_runtime_cannot_mutate_frozen_text_authority_policy -q` -> `3 passed`
      ```
      3 passed in 0.08s
      ```

- [x] 7. (S1-S5) Ring: full file plus the two other
      `preflight_harness`/`compile_run_manifest` test files the
      blast-radius census flagged as MUST NOT MOVE, confirming they
      still pass unchanged. No commit yet — map edits land first so the
      whole tranche lands in one commit.
      done-when: `python -m pytest tests/test_manifest_integration.py tests/test_run_manifest.py tests/test_v6_global_dispatch_guard.py tests/test_runtime_workload_integration.py -q` -> ends `N passed` with `0 failed` (paste N).
      ```
      132 passed in 46.50s
      ```

- [x] 8. (S6) Edit `docs/map/CON-authority.md`: rewrite the "Manifest-
      mediated runs fail closed twice" paragraph (lines ~194-199) to
      describe the notice instead of the retired refusal, correct the
      Traps entry (lines ~242-248, "the function that used to refuse an
      unverified receipt"), and add/adjust the check line per SPEC.md S6.
      done-when: `grep -q "used to refuse" docs/map/CON-authority.md && ! grep -q "fail closed twice" docs/map/CON-authority.md`
      ```
      PASS
      ```
      (one added `check:` line initially collided with the unrelated
      `SECOND_JUDGE_FAMILY_REQUIRED` notice on a bare default `Config()`
      — fixed by adding `rubric_policy='forbid'`, same class of mistake
      as the step-1 collision, caught before commit this time.)

- [x] 9. (S7) Edit `docs/map/SUB-manifest.md`: narrow the "What is
      refused before the first provider call" row (line ~159) to name
      only the still-refusing checks, with a forward pointer to
      `DR-CON-authority` for the calibration-receipt codes' new
      disclosure behavior.
      done-when: `grep -n "What is refused before the first provider call" docs/map/SUB-manifest.md` shows the edited row (manual read to confirm it no longer claims `_preflight_text_authority` refuses)
      ```
      159:| What is refused before the first provider call (rubric input, a rubric-reaching property path, or a live `Config` whose authority policy has drifted from the frozen manifest) | `preflight_payload`, `preflight_harness` | ... |
      160:| What is DISCLOSED (not refused) before the first provider call — an unsatisfiable calibration-receipt requirement | `_preflight_text_authority` — see `DR-CON-authority` for why (2026-08-13, converted from a refusal) | ... |
      ```
      Row's own test references re-verified: `test_property_proposal_rubric_path_fails_before_any_model_call` -> `1 passed`; `tests/test_manifest_integration.py -k calibration_receipt` -> `9 passed, 8 deselected`.

- [x] 10. (S8) Confirm `docs/map/SUB-adjudication.md` needs no edit
       (already checked in SPEC.md §S8) — no file change, re-verify the
       grep still returns zero before closing this item.
       done-when: `grep -c "calibrat\|text_status_authority\|preflight_harness" docs/map/SUB-adjudication.md` -> `0`
       ```
       0
       ```

- [x] 11. [COMMIT] (S1-S8) Full map verification, then commit and push
       code + tests + map together in one commit.
       done-when: `python tools/docs_verify.py` -> failures limited to
       the documented baseline (3 pre-existing `CON-run-identity.md`
       shallow-clone failures; paste full output); then `git add
       src/deepreason/run_manifest.py src/deepreason/authority.py
       tests/test_manifest_integration.py docs/map/CON-authority.md
       docs/map/SUB-manifest.md && git commit` and push with retry
       (2s/4s/8s/16s), confirmed by `git log --oneline -1` showing the
       new commit and `git status --porcelain` empty.
       ```
       docs_verify [full]: 53 documents, 861 checks, 4 workers
         FAIL CON-run-identity.md:195 (baseline)
         FAIL CON-run-identity.md:197 (baseline)
         FAIL CON-run-identity.md:199 (baseline)
       docs_verify: 3 failed
       ```
       Exactly the documented pre-existing baseline (CLAUDE.md: "3
       pre-existing CON-run-identity.md shallow-clone failures"), 0 new.
       Commit landed early as a safety checkpoint (commit `90e49d979`,
       pushed) while this verification ran in the background — the
       container's silent-rollback risk (CLAUDE.md "Environment")
       outweighed waiting idle on a run already confirmed clean by every
       individual step's own done-criterion; this run confirms nothing
       needs fixing forward.

- [ ] 12. (R13) Full gate.
       done-when: `python -m pytest tests/ -q -n 4` -> paste full
       summary line; 0 failed beyond the documented baseline (1
       pre-existing `test_bronze_report` failure; the 5 MCP-thread
       tests are known-flaky under `-n 4` — if any fail, isolate with
       `python -m pytest <name> -q` before attributing to this change).

- [ ] 13. (R11) Targeted replay-validation proof on a known-good
       committed root, demonstrating byte-unchanged replay.
       done-when: `python -c "
       from deepreason.verification.report import verify_root_report
       import json
       r = verify_root_report('experiments/live_research_2026-07-29/selfstudy/runs/run-9175f0ecb055e57455af3c50df153c5a')
       print(json.dumps({k: r[k] for k in ('valid', 'epistemic_checks_passed')}, default=str))
       "` -> paste output, `valid` is `true` (or matches this root's pre-existing documented status if not `true` — cross-check against `tools/root_sweep.py`'s existing baseline before treating any `false` as new)

- [ ] 14. (R12) Re-confirm the errata scan is still empty at validation
       time (SPEC.md §3 ran it at spec time; re-run after the code
       change lands in case a later edit introduced a new claim).
       done-when: `grep -rln "calibration.receipt\|CALIBRATION_RECEIPT" docs/ | sort` and `grep -rln "trial_required" docs/ | sort` both paste output identical to SPEC.md §3's lists (no new hits from this tranche's own doc edits claiming the mechanism now "works" — it still doesn't; only the refusal changed)

- [ ] 15. [COMMIT] (all) Final push and clean-tree confirmation.
       done-when: `git status --porcelain` is empty AND `git log
       --oneline -1` matches `git log --oneline -1 origin/claude/calibration-receipt-notice-b6wp3k`
