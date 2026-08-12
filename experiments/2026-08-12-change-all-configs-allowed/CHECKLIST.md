# Checklist for: all configurations are allowed — compile-time denial abolished

State: next=4 blockers=none

Map ids: `DR-SUB-manifest` (frozen surface 4, `run_manifest.py`),
`DR-SUB-application` (`cli/main.py`, `intake_form.py`), `DR-CON-authority`
(`config.py`), `DR-CON-seats` (`seat_bindings.py`).
Re-read REQUEST.md + SPEC.md before every step. Execute strictly in
order. One step per `dr-execute-step` invocation.

- [x] 1. (S-INFRA) Add `CompileNoticeV1` model, the `compile_notices`
      field on `RunManifest`, the version-pop guard in BOTH
      `_versioned_serialization` and `canonical_bytes`, and the
      `_emit_compile_notice` helper to `src/deepreason/run_manifest.py`.
      Thread a `notices: list[CompileNoticeV1]` local through
      `compile_run_manifest` (unused by any call yet) and pass
      `compile_notices=tuple(notices) or None` into the final
      `RunManifest(...)` construction.
      done-when: `python -c "from deepreason.run_manifest import CompileNoticeV1, RunManifest; RunManifest.model_fields['compile_notices']"` succeeds, and `python -m pytest tests/test_run_manifest.py -q -k canonical` passes unchanged (proves no existing golden moved).
      DONE: field annotation confirmed
      `Union[tuple[CompileNoticeV1, ...], NoneType], default=None`; canonical
      golden tests `2 passed, 70 deselected`; broader ring
      (`tests/test_run_manifest.py tests/test_run_manifest_scratch_bridge.py
      tests/test_run_manifest_v4.py tests/test_v6_only_manifest_loading.py`)
      `134 passed`. No map document change needed (no caller-visible
      behavior changed yet — the field is written but nothing reads it).

- [x] 2. (S-B1) Convert `GROUNDED_BRIDGE_MANIFEST_V3_REQUIRED`
      (`compile_run_manifest` :3123) from `raise` to
      `_emit_compile_notice(notices, ...)`, no other change to control
      flow (the field is already unconditionally popped for
      schema<3). Rewrite `tests/test_run_manifest_scratch_bridge.py`'s
      pinned test (currently asserts `bridge_error.value.code ==
      "GROUNDED_BRIDGE_MANIFEST_V3_REQUIRED"`) to assert the manifest
      NOW compiles and `manifest.compile_notices[0].code ==
      "GROUNDED_BRIDGE_MANIFEST_V3_REQUIRED"`.
      done-when: `python -m pytest tests/test_run_manifest_scratch_bridge.py -q` passes, 0 failed.
      DONE (executed together with step 3, same site cluster):
      `test_new_features_require_v3_before_any_route_resolution` renamed
      to `test_new_features_below_v3_compile_with_a_notice_instead_of_refusing`,
      asserts compile succeeds, `bridge_policy is None` (feature still
      dropped, unchanged), and `compile_notices[0].code ==
      "GROUNDED_BRIDGE_MANIFEST_V3_REQUIRED"`.
      `tests/test_run_manifest_scratch_bridge.py -q`: `23 passed`.

- [x] 3. (S-B2) Convert `SCRATCH_MANIFEST_V3_REQUIRED`
      (`compile_run_manifest` :3117) the same way. Find and rewrite its
      pinned test analogously (grep `tests/` for the code first).
      done-when: `python -m pytest tests/test_run_manifest_scratch_bridge.py tests/test_run_manifest.py -q -k scratch` passes, 0 failed.
      DONE (same commit as step 2 — one test guarded both codes).
      Broader ring (`tests/test_run_manifest.py
      tests/test_run_manifest_scratch_bridge.py tests/test_run_manifest_v4.py
      tests/test_v6_only_manifest_loading.py`): `134 passed`. No other
      `tests/`/`docs/map/` reference to either code expected a raise
      (grepped both before committing).

- [ ] 4. (S-B3) Convert `BRIDGE_LEDGER_ROUTE_REQUIRED` /
      `_COMPOSER_ROUTE_REQUIRED` / `_REVIEWER_ROUTE_REQUIRED` at BOTH
      sites together: `compile_run_manifest` (:3204-3210) and the
      frozen model's own `_production_routes_are_concrete` (:1399-1402,
      via `self.model_copy(update={"compile_notices": ...})`, since the
      model is frozen and an "after" validator returns a new instance
      rather than mutating `self`). Rewrite
      `tests/test_run_manifest_scratch_bridge.py::test_grounded_review_requires_explicit_reviewer_before_route_resolution`
      (and any sibling ledger/composer test) to assert compile-with-notice.
      done-when: `python -m pytest tests/test_run_manifest_scratch_bridge.py -q` passes, 0 failed.

- [ ] 5. (S-B4) Convert `BRIDGE_REVIEWER_SEATS_MISMATCH`
      (`_production_routes_are_concrete` :1406-1409) the same way.
      Rewrite its pinned test (grep `tests/` for the code first).
      done-when: `python -m pytest tests/test_run_manifest_scratch_bridge.py tests/test_run_manifest.py -q` passes, 0 failed.

- [ ] 6. (S-B5) Convert `SECOND_JUDGE_FAMILY_REQUIRED` at all three
      sites together (`compile_run_manifest` :3282-3288,
      `_production_routes_are_concrete` :1532-1536, the
      `preflight_harness` rubric re-check :3872-3876) — they enforce one
      rule at three call points and must move together per SPEC §3.1.
      Rewrite `tests/test_run_manifest.py::test_cross_family_rubric_policy_fails_preflight_for_one_family`,
      `test_judge_seats_opt_in_does_not_bypass_cross_family_requirement`,
      and `test_materialized_rubric_reference_is_preflighted_on_resume`
      to assert compile-with-notice at each of the three sites.
      done-when: `python -m pytest tests/test_run_manifest.py -q -k "cross_family or rubric"` passes, 0 failed.

- [ ] 7. (S-B6) [COMMIT] Convert `JUDGE_FAMILY_AND_BLIND_SAME_MODEL_CONFLICT`
      at both its sites (`run_manifest.py::compile_run_manifest` :3016-3021
      and `cli/main.py`'s `config compile` branch :822-828) to the
      precedence rule in SPEC §4 rule 2: `judge_family` wins,
      `blind_same_model_judges` is dropped, notice carries
      `resolution="judge_family wins; blind_same_model_judges dropped"`.
      Rewrite `tests/test_run_manifest.py::test_blind_same_model_judges_conflicts_with_judge_family`
      and `test_cli_judge_family_and_blind_same_model_judges_conflict`.
      Run the subsystem ring and commit steps 1-7 together (the whole
      `run_manifest.py`/bridge/judge-family cluster is one coherent unit).
      done-when: `python -m pytest tests/test_run_manifest.py tests/test_run_manifest_scratch_bridge.py -q` output ends "N passed, 0 failed" (paste it), then `git add -A && git commit -m "..." && git push`.

- [ ] 8. (S-B7) Reproduce SPEC §1's two grounded-extension blocks against
      the now-converted code and confirm both compile clean with
      notices — this is the tranche's explicit delivery proof.
      done-when: the §1 script (schema_version omitted, then with
      schema_version=3 and no judge route) now returns a compiled
      `RunManifest` with `len(manifest.compile_notices) >= 1` at each
      stage instead of raising, paste the notices' `.code` values.

- [ ] 9. (S-C1) Convert `BridgeConfig._grounded_mode_preserves_valid_unresolved_results`
      (`config.py` :228-244) from `raise` to a no-op pass-through — grep
      confirmed `allow_partial`/`allow_abstention`/`require_claim_ledger`/
      `require_claim_uses` have NO runtime reader anywhere in
      `src/deepreason/` outside the two validators themselves (this
      validator and its manifest-level twin below), so no restoration is
      needed; the literal values the operator set simply stand. Convert
      the frozen-model twin, `BridgePolicyV1._grounded_contract_is_complete`
      (`run_manifest.py` :421-434), the same way (frozen surface 4:
      model and validator move together) — its notice is emitted into
      `compile_notices` via the same `_emit_compile_notice`/`model_copy`
      pattern as step 4. Rewrite
      `tests/test_config_scratch_bridge.py::test_grounded_mode_cannot_disable_unresolved_success_safety`
      to assert `Config(...)` now constructs without raising, and add a
      manifest-level assertion that compiling with the same disabled
      fields yields a `compile_notices` entry instead of raising.
      done-when: `python -m pytest tests/test_config_scratch_bridge.py tests/test_run_manifest.py -q` passes, 0 failed.

- [ ] 10. (S-S1, S-S2) [COMMIT] Convert `SEAT_BINDING_ROLE_CONFLICT`
      (`resolve_seat_bindings`) and `SEAT_BINDING_GROUP_DUPLICATED`
      (`parse_seat_flags`) in `seat_bindings.py` to SPEC §4 rule 1
      (explicit-most-wins, then last-flag-wins) — the operator's own
      named example. Update `docs/map/CON-seats.md`'s own check
      (`grep -q "SEAT_BINDING_ROLE_CONFLICT" src/deepreason/seat_bindings.py`)
      in the SAME commit if the code string itself moves (it should not
      if the code is now used in a notice message rather than deleted —
      confirm before editing the map doc). Rewrite
      `tests/test_seat_bindings.py::test_resolve_seat_bindings_conflict_on_named_simulation_conjecture_pair`,
      `::test_resolve_seat_bindings_conflict_on_discovered_scratch_conjecture_overlap`,
      and `::test_parse_seat_flags_duplicate_group_refuses_typed` to
      assert the deterministic winner and a resolution note instead of
      a raise.
      done-when: `python -m pytest tests/test_seat_bindings.py -q` output ends "N passed, 0 failed" (paste it), then commit and push.

- [ ] 11. (S-S3) Convert `SCHOOL_SEAT_DUPLICATED` (`parse_school_seat_flags`)
      the same way (unpinned by any existing test — add a new regression
      test asserting the deterministic last-flag-wins resolution rather
      than only removing the old behavior untested).
      done-when: `python -m pytest tests/test_seat_bindings.py -q` passes, 0 failed, and the new test name appears in the output.

- [ ] 12. (S-I1) Convert `INTAKE_SEAT_CONFLICT`
      (`IntakeFormV1._no_conflicting_role_bindings`, `intake_form.py`)
      to the identical SPEC §4 rule 1 precedence (must match
      `seat_bindings.py`'s rule exactly — same vocabulary, same
      resolution). Rewrite the `tests/test_intake_form.py` assertion
      that currently expects `INTAKE_SEAT_CONFLICT` to raise.
      done-when: `python -m pytest tests/test_intake_form.py tests/test_error_catalog.py -q` passes, 0 failed.

- [ ] 13. (S-V1) [COMMIT] Convert `cli/main.py::_cmd_validate_intake`
      (:1924-1941) to advisory per R6: always print the full
      violation/notice report and return 0, EXCEPT when
      `_load_intake_file` itself fails (unreadable file or non-object
      JSON/YAML — `INTAKE_FILE_NOT_AN_OBJECT` and friends stay
      non-zero-exit per R2, they are non-inputs not configurations).
      Add a new CLI-level regression test (none exists today per the
      census) asserting exit code 0 on a semantic violation and exit
      code 1 on a parse failure. Confirm the MCP `validate_intake` tool
      needs NO code change (already returns `{"ok": False, ...}` as
      normal tool data — re-run `tests/test_mcp.py -k validate_intake`
      to confirm unchanged).
      done-when: new CLI test passes; `python -m pytest tests/test_mcp.py -q -k validate_intake` passes unchanged; commit and push.

- [ ] 14. (S-DOC) [COMMIT] Ledger REQUEST.md's two operator-verbatim
      statements (R1 and the superseded R1a) as a new standing entry in
      CLAUDE.md's "Operator design laws" section, quoting the operator
      verbatim, noting the supersession explicitly, in the SAME commit
      as this step (a docs-only commit is acceptable here since no code
      changes in this step).
      done-when: `grep -q "All configurations should be allowed" CLAUDE.md`, `grep -q "flat out denial" CLAUDE.md`, then commit and push.

- [ ] 15. (S-VERIFY) Prove R8 (old roots replay byte-unchanged) with a
      targeted `verify_root_report` on a committed root that carries
      `bridge_policy` and/or `criticism_policy` (the fields whose
      validators moved in steps 4-9) — e.g. one of
      `experiments/2026-08-08-change-grounded-overlay-o1/`'s roots or
      `experiments/2026-08-01-change-prose-can-refute/`'s, whichever
      actually carries `grounded_two_stage` or a `criticism_policy` (grep
      its `run-manifest.json` first). Compare the report's `valid`,
      `epistemic_checks_passed`, and `att` length against a report taken
      BEFORE step 1 (re-run against `git stash` if not already captured)
      — byte-identical required.
      done-when: `python -c "from deepreason.verification.report import verify_root_report; print(verify_root_report('<root>'))"` output pasted, matching the pre-change baseline exactly.

- [ ] 16. (all) Map check: `python tools/docs_verify.py`
      done-when: exactly the 3 pre-existing `CON-run-identity.md`
      shallow-clone failures from SPEC §7's baseline, no new failures
      (paste the output).

- [ ] 17. (all) Full gate: `python -m pytest tests/ -q -n 4`
      done-when: output ends "N passed, M failed" where M equals the
      pre-existing baseline (1 `test_bronze_report` failure; isolate any
      MCP-thread failure with `-n 1` before attributing) — paste the
      final summary line.

- [ ] 18. (all) [COMMIT] Root sweep before/after comparison per
      `DR-INV-frozen-surfaces`: `python tools/root_sweep.py
      after-all-configs-allowed.txt`, diff against a pre-tranche sweep
      (run one now if none exists yet from before step 1 — if it's too
      late to get a true "before," note that honestly in DELIVERY.md
      rather than fabricate one).
      done-when: diff shows no root's `valid`/`att`/`module_digests`/
      `seat_digests` changed (paste the diff or "no differences").

- [ ] 19. (all) [COMMIT] Final push and clean-tree check.
      done-when: `git status --porcelain` is empty AND
      `git log --oneline -1 origin/claude/all-configs-allowed-r54a3b`
      matches local HEAD.
