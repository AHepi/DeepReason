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
(step 9, AFTER the code change), compared against that existing
baseline — not a redundant fresh BEFORE capture.

- [ ] 1. (S1) Add `ENGAGED_CRITICISM_AUTHORITY: Literal["observe_only",
      "defended_trial"] = "observe_only"` to `src/deepreason/config.py`,
      beside the four existing authority fields (near line 389).
      done-when: `grep -q 'ENGAGED_CRITICISM_AUTHORITY: Literal\["observe_only", "defended_trial"\] = "observe_only"' src/deepreason/config.py && python -c "from deepreason.config import Config; assert Config().ENGAGED_CRITICISM_AUTHORITY == 'observe_only'"` exits 0 with no assertion error.

- [ ] 2. (S2) Change `src/deepreason/v6_policy.py::engaged_criticism_policy`'s
      signature to `(endpoint_id: str, *, authority: str = "observe_only")
      -> CriticismPolicyV1`; replace the hard-coded `authority="observe_only"`
      at line 212 with `authority=authority`.
      done-when: `python -c "from deepreason.v6_policy import engaged_criticism_policy as f; assert f('e').authority == 'observe_only'; assert f('e', authority='defended_trial').authority == 'defended_trial'"` exits 0.

- [ ] 3. (S2) Confirm existing callers unaffected: `engaged_policy_digest()`'s
      template call (v6_policy.py:461) passes no `authority` kwarg, and
      `preparation.py`'s current (pre-S3) call site also passes none —
      both must still bind `observe_only` before S3 changes the call site.
      done-when: `python -c "from deepreason.v6_policy import engaged_policy_digest; engaged_policy_digest()"` exits 0 (no signature error) AND `grep -n 'engaged_criticism_policy(' src/deepreason/v6_policy.py src/deepreason/preparation.py` shows only the two known call sites (line ~461 in v6_policy.py, one in preparation.py), confirming no third site was missed.

- [ ] 4. (S3) In `src/deepreason/preparation.py::build_preparation_manifest`,
      capture `_config_for_profile(profile)` in a named local `config`
      (passed unchanged as `compile_run_manifest`'s first positional
      argument) and change the criticism_policy call to
      `engaged_criticism_policy(profile.endpoint_id, authority=config.ENGAGED_CRITICISM_AUTHORITY)`.
      done-when: `python -c "import inspect; from deepreason import preparation as p; src = inspect.getsource(p.build_preparation_manifest); assert 'config.ENGAGED_CRITICISM_AUTHORITY' in src"` exits 0.

- [ ] 5. (S3) Confirm zero behavior change from step 4 alone: the two
      existing tests that already exercise this path
      (`tests/test_v6_policy_preset.py`,
      `tests/test_v6_engaged_public_defaults.py`) still pass unchanged.
      done-when: `python -m pytest tests/test_v6_policy_preset.py tests/test_v6_engaged_public_defaults.py -q` ends "N passed, 0 failed" (paste it).

- [ ] 6. (S5) Update `docs/map/CON-authority.md`: add
      `src/deepreason/v6_policy.py` and `src/deepreason/preparation.py`
      to `Owns:`; add `ENGAGED_CRITICISM_AUTHORITY` to the "Where it
      lives" table as the fifth per-run authority knob; add one new
      checked claim proving default-preservation, citing step 7's test
      (write this step's claim text now, the check command references
      the test added in step 7 — acceptable since docs_verify only runs
      the check, not requiring the test to exist before the doc is
      written, but do NOT mark this step's own done-when satisfied until
      step 7's test exists — so this step's done-when is deferred to
      running docs_verify after step 7 lands; for now confirm only the
      grep and Owns/table edits landed).
      done-when: `grep -q "ENGAGED_CRITICISM_AUTHORITY" docs/map/CON-authority.md` exits 0 AND `grep -q "src/deepreason/v6_policy.py" docs/map/CON-authority.md` exits 0 AND `grep -q "src/deepreason/preparation.py" docs/map/CON-authority.md` exits 0.

- [ ] 7. (S4) Add ONE new test to `tests/test_v6_policy_preset.py`
      proving `Config()`'s new field is `"observe_only"` AND
      `engaged_criticism_policy(endpoint, authority=Config().ENGAGED_CRITICISM_AUTHORITY)
      == engaged_criticism_policy(endpoint)` (full pydantic equality).
      done-when: `python -m pytest tests/test_v6_policy_preset.py -q` ends "N passed, 0 failed" and the new test name appears in `python -m pytest tests/test_v6_policy_preset.py --collect-only -q` output (paste both).

- [ ] 8. (S5) Re-run `docs_verify` now that step 7's test exists, to
      close out step 6's deferred claim: confirm the new checked claim
      in `CON-authority.md` actually passes.
      done-when: `python tools/docs_verify.py` ends "0 failed" AND `python tools/docs_verify.py --audit` reports 0 findings (paste both).

- [ ] 9. (all) [COMMIT] Commit steps 1-8 together (config field,
      v6_policy.py signature change, preparation.py threading, map
      update, new test) as one tranche commit — code and map in the
      SAME commit per R7.
      done-when: `git log -1 --stat` shows `src/deepreason/config.py`,
      `src/deepreason/v6_policy.py`, `src/deepreason/preparation.py`,
      `docs/map/CON-authority.md`, and `tests/test_v6_policy_preset.py`
      all in the same commit; `git push -u origin claude/delivery-rungs-handover-m22sdy`
      succeeds (paste confirmation).

- [ ] 10. (S6, R4) Full gate: `python -m pytest tests/ -q -n 4`. Rerun
      once if only the known flake
      (`test_grounded_counterexample_recovery_does_not_invent_override_on_repeat`)
      fails, per C3.
      done-when: output ends "N passed, 0 failed" (paste it).

- [ ] 11. (S6, R5) Root sweep: `python tools/root_sweep.py`, compared
      against the existing accepted baseline (42 rows, 11 ERROR
      expected per ERRATA E5/E6/E8) — per this checklist's before-sweep
      note, no fresh BEFORE capture is needed since no reader logic
      changed; this run IS the after-answer and must match the baseline
      byte-for-byte.
      done-when: sweep output has 42 rows, 11 ERROR, and is
      byte-identical to the pre-tranche baseline (paste the diff command
      and its empty output, or the full sweep output if no prior
      snapshot file exists to diff against).

- [ ] 12. (all) [COMMIT] Final push and cleanliness check.
      done-when: `git status --porcelain` is empty AND branch head is
      on `origin/claude/delivery-rungs-handover-m22sdy` (paste both).
