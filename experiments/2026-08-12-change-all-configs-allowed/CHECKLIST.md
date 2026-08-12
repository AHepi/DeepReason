# Checklist for: all configurations are allowed — compile-time denial abolished

State: next=16 blockers=none

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

- [x] 4. (S-B3) Convert `BRIDGE_LEDGER_ROUTE_REQUIRED` /
      `_COMPOSER_ROUTE_REQUIRED` / `_REVIEWER_ROUTE_REQUIRED` at BOTH
      sites together: `compile_run_manifest` and the frozen model's own
      `_production_routes_are_concrete`.
      done-when: `python -m pytest tests/test_run_manifest_scratch_bridge.py -q` passes, 0 failed.
      DONE, with a design correction found during execution: an "after"
      model validator's `self.model_copy(update=...)` is SILENTLY
      DISCARDED by pydantic when the model is constructed via `__init__`
      (only honored via `model_validate`) — confirmed empirically (a
      `UserWarning` fires and `compile_notices` stays `None`). Since
      `compile_run_manifest` constructs via `RunManifest(...)` (i.e.
      `__init__`), this would have silently dropped every notice this
      validator alone is responsible for on any manifest NOT going
      through `compile_run_manifest`'s own pre-check (e.g. a future
      direct `RunManifest(...)` construction or `.model_validate()` of a
      hand-built payload). Fixed by using `object.__setattr__(self,
      "compile_notices", ...)` instead of `model_copy` — verified
      correct via BOTH `RunManifest(**payload)` and
      `RunManifest.model_validate(payload)` directly (no warning, notice
      present in both). Renamed
      `test_grounded_review_requires_explicit_reviewer_before_route_resolution`
      to `test_grounded_review_missing_reviewer_compiles_with_a_notice`
      (the "before any route resolution" guarantee is gone by design —
      the OTHER configured roles now resolve normally; only the missing
      role's absence and the notice are asserted).

- [x] 5. (S-B4) Convert `BRIDGE_REVIEWER_SEATS_MISMATCH`
      (`_production_routes_are_concrete`) the same way.
      done-when: `python -m pytest tests/test_run_manifest_scratch_bridge.py tests/test_run_manifest.py -q` passes, 0 failed.
      DONE together with step 4 (same `_emit_deduped` helper, same
      dedup-on-(code,pointer) mechanism to avoid double-recording across
      the schema-v6 `model_validate` round trips in
      `_compile_route_seat_contract_decomposition_plan`/
      `_compile_route_seat_behavioral_capability_plan`).

- [x] 6. (S-B5) Convert `SECOND_JUDGE_FAMILY_REQUIRED` at the two sites
      SPEC named that actually construct/validate a manifest
      (`compile_run_manifest`, `_production_routes_are_concrete`).
      done-when: `python -m pytest tests/test_run_manifest.py -q -k "cross_family or rubric"` passes, 0 failed.
      CORRECTION found during execution: SPEC's third named site
      ("preflight_harness's rubric re-check") does not exist as
      described — the actual third site is `preflight_payload`
      (`RUBRIC_INPUT_FORBIDDEN` + `SECOND_JUDGE_FAMILY_REQUIRED`, called
      against an ALREADY-COMPILED, frozen manifest with no field to
      attach a notice to and no return-value contract for one; converting
      it would require a signature change across every caller, out of
      this tranche's tier-1 budget). Left as a hard error, NOT converted
      — moved from CONVERT-T1 to STAYS-FOR-NOW in SPEC's own terms; see
      SPEC §3.1 addendum. A FOURTH occurrence was also found mid-search
      (`_select_second_judge_spec`, run_manifest.py — refuses when a
      `--judge-family` selector resolves to a route sharing the primary
      family): also NOT converted, recorded as a discovered-but-deferred
      site rather than silently folded in.
      Rewrote `test_cross_family_rubric_policy_fails_preflight_for_one_family`
      (renamed `test_cross_family_rubric_policy_compiles_with_a_notice_for_one_family`)
      and `test_judge_seats_opt_in_does_not_bypass_cross_family_requirement`
      to assert compile-with-notice. `tests/test_run_manifest.py -q -k "cross_family or rubric"`: passed.

- [x] 7. (S-B6) [COMMIT] Convert `JUDGE_FAMILY_AND_BLIND_SAME_MODEL_CONFLICT`
      at both its sites (`run_manifest.py::compile_run_manifest` and
      `cli/main.py`'s `config compile` branch) to the precedence rule in
      SPEC §4 rule 2: `judge_family` wins, `blind_same_model_judges` is
      dropped, notice carries
      `resolution="judge_family wins; blind_same_model_judges dropped"`.
      The now-redundant CLI-level pre-check was removed (compile_run_manifest
      applies the rule unconditionally); `config compile` now prints
      `NOTICE <code>: <message>` to stderr for every notice on the
      compiled manifest. Rewrote
      `tests/test_run_manifest.py::test_blind_same_model_judges_conflicts_with_judge_family`
      and `test_cli_judge_family_and_blind_same_model_judges_conflict`
      (both needed a genuinely second-family judge route added to their
      fixture config — the original fixture's identical judge routes
      would otherwise hit the undiscussed 4th
      `SECOND_JUDGE_FAMILY_REQUIRED`-adjacent site from step 6's note).
      done-when: `python -m pytest tests/test_run_manifest.py tests/test_run_manifest_scratch_bridge.py tests/test_run_manifest_v4.py tests/test_v6_only_manifest_loading.py -q` -> `134 passed`.
      Additional due-diligence (not required by SPEC, run out of caution):
      the SAME grounded/missing-judge config at `schema_version=6` (not
      3) hits a DIFFERENT, unconverted site,
      `V6_BEHAVIORAL_CONTRACT_ROUTE_REQUIRED` in
      `_compile_route_seat_behavioral_capability_plan` — a v6-only
      downstream consequence of the same missing route, discovered by
      running the scenario, not from the census. NOT converted (out of
      scope for this tranche): recorded as a known gap in DELIVERY.md.
      R2's "any input that parses compiles" therefore holds for a
      grounded-bridge config missing a role at schema_version<6 today;
      schema_version=6 with the SAME missing role still refuses at this
      one additional, newly-identified site.
      Ring: `python -m pytest tests/test_v6_route_seat_behavioral_capability_plan.py tests/test_v6_contract_schema_repair_policy.py tests/test_foreign_criticism_policy_c3.py tests/test_run_manifest_v5_inquiry.py -q` -> `64 passed` (no regression elsewhere from the dedup/object.__setattr__ change).

- [x] 8. (S-B7) Reproduce SPEC §1's two grounded-extension blocks against
      the now-converted code and confirm both compile clean with
      notices — this is the tranche's explicit delivery proof.
      done-when: the §1 script (schema_version omitted, then with
      schema_version=3 and no judge route) now returns a compiled
      `RunManifest` with `len(manifest.compile_notices) >= 1` at each
      stage instead of raising, paste the notices' `.code` values.
      CORRECTION found while executing: "schema_version omitted" (the
      compiler's true default, 1) cannot carry `workload_profile` at
      all — that was masked before conversion because
      GROUNDED_BRIDGE_MANIFEST_V3_REQUIRED raised first, every time,
      regardless. Re-scoped block 1 to `schema_version=2` (matching the
      codebase's own pre-existing `test_new_features_require_v3_...`
      fixture) — SPEC §1 updated with this correction plus the
      schema_version=6 known-gap note.
      DONE:
        BLOCK 1 -- compiled OK, schema_version = 2, bridge_policy = None
          notices: ['GROUNDED_BRIDGE_MANIFEST_V3_REQUIRED']
        BLOCK 2 -- compiled OK, schema_version = 3
          notices: ['BRIDGE_REVIEWER_ROUTE_REQUIRED', 'BRIDGE_REVIEWER_SEATS_MISMATCH']

- [x] 9. (S-C1) Convert `BridgeConfig._grounded_mode_preserves_valid_unresolved_results`
      (`config.py`) from `raise` to deletion — grep-confirmed
      `allow_partial`/`allow_abstention`/`require_claim_ledger`/
      `require_claim_uses` have NO runtime reader anywhere in
      `src/deepreason/` outside the two validators themselves, so no
      restoration is needed; the literal values the operator set simply
      stand. The frozen-model twin's OWN gate,
      `BridgePolicy._grounded_contract_is_complete` (`run_manifest.py`),
      had its raise removed too (its SECOND check,
      `grounding_repair_role != reviewer_role`, is a genuine internal
      invariant `_compile_bridge_policy` always satisfies by construction
      and stays a hard error, unconverted). The notice is instead emitted
      by `_compile_bridge_policy` itself (the one function with access to
      `compile_run_manifest`'s `notices` list) BEFORE constructing
      `BridgePolicy`, with a NEW code
      (`BRIDGE_UNRESOLVED_SUCCESS_SAFETY_DISABLED` — the retired site had
      no typed code of its own, only a bare message, so one was minted).
      `_validate_v3_engine_policy_consistency`'s frozen-record re-derivation
      call site passes no `notices` (default `None`), so R8 holds by
      construction, not by the caller remembering to skip it.
      Rewrote `tests/test_config_scratch_bridge.py::test_grounded_mode_cannot_disable_unresolved_success_safety`
      (renamed `..._now_constructs`) and one incidental user of the same
      validator in `test_nested_assignment_is_validated_and_arbitrary_roles_remain_supported`
      (switched to a still-live structural check,
      `max_schema_repair_attempts` range, to keep proving nested
      `validate_assignment=True` works). Added
      `tests/test_run_manifest_scratch_bridge.py::test_grounded_mode_disabled_unresolved_success_safety_compiles_with_a_notice`.
      done-when: `python -m pytest tests/test_config_scratch_bridge.py tests/test_run_manifest.py -q` passes, 0 failed.
      DONE: `python -m pytest tests/test_run_manifest.py tests/test_run_manifest_scratch_bridge.py tests/test_run_manifest_v4.py tests/test_v6_only_manifest_loading.py tests/test_config_scratch_bridge.py tests/test_config.py -q` -> `161 passed`.

- [x] 10. (S-S1, S-S2) [COMMIT] Convert `SEAT_BINDING_ROLE_CONFLICT`
      (`resolve_seat_bindings`) and `SEAT_BINDING_GROUP_DUPLICATED`
      (`parse_seat_flags`) in `seat_bindings.py` to SPEC §4 rule 1
      (explicit-most-wins, then last-flag-wins) — the operator's own
      named example. CORRECTION found during execution: `resolve_seat_bindings`
      operates on the PERSISTED `{group: path}` file, which carries no
      `--seat` flag order at all (`resolve_seat_bindings_by_group` already
      iterates `sorted(raw)`) — "last-flag-wins" is only meaningful at
      `parse_seat_flags` (which sees the raw flag list). For
      `resolve_seat_bindings`'s role-level conflict, the tie-break actually
      implemented is: a direct group (its own `GROUP_ROLES` entry) beats a
      group reaching the role only via `GROUP_ALIASES`; among two equally
      direct (or equally aliased) groups, the alphabetically LATER group
      name wins — deterministic and config-derived either way. SPEC §4
      updated to state this precisely. The retired code strings no longer
      appear anywhere in `seat_bindings.py` (they were deleted, not kept in
      a notice message — there is no notice-recording target at this layer,
      see below), which broke `docs/map/CON-seats.md`'s own
      `grep -q "SEAT_BINDING_ROLE_CONFLICT" ...` check; replaced with a
      behavioral check (fires both the alias-vs-direct and the tie-break
      case) per dr-execute-step's "anchor to meaning, not form" rule, and
      the table row/rule prose rewritten. Rewrote
      `test_resolve_seat_bindings_conflict_on_named_simulation_conjecture_pair`
      (renamed `..._direct_group_outranks_its_own_alias`),
      `test_resolve_seat_bindings_conflict_on_discovered_scratch_conjecture_overlap`
      (renamed `..._alphabetically_later_group_wins_a_direct_tie`), and
      `test_parse_seat_flags_duplicate_group_refuses_typed` (renamed
      `..._last_flag_wins`).
      **Scope note (recorded, not silently expanded):** unlike the
      run_manifest.py conversions, this resolution is NOT recorded as a
      `CompileNoticeV1` anywhere — `deepreason setup`'s seat-binding
      resolution happens long before any `compile_run_manifest` call, and
      threading a notice from `seat_bindings.py` through `preparation.py`
      into a future manifest's `compile_notices` was judged out of this
      tranche's tier-1 budget (see SPEC §3.3 addendum). R4's "deterministic
      resolution instead of refusal" is satisfied; R3's "recorded in the
      compiled manifest/run record" is NOT yet wired for this specific
      denial family — a real, disclosed gap, not an oversight.
      done-when: `python -m pytest tests/test_seat_bindings.py -q` output ends "16 passed" (paste it), then commit and push.
      DONE: `16 passed in 0.28s`. Also ran
      `python -m pytest tests/test_seat_bindings.py tests/test_qualification_per_seat.py -q -k seat` -> `23 passed`.

- [x] 11. (S-S3) Convert `SCHOOL_SEAT_DUPLICATED` (`parse_school_seat_flags`)
      the same way (unpinned by any existing test — add a new regression
      test asserting the deterministic last-flag-wins resolution rather
      than only removing the old behavior untested).
      done-when: `python -m pytest tests/test_seat_bindings.py -q` passes, 0 failed, and the new test name appears in the output.
      DONE: added `test_parse_school_seat_flags_duplicate_id_last_flag_wins`;
      `tests/test_seat_bindings.py -q` -> `16 passed` (includes this new test).

- [x] 12. (S-I1) Convert `INTAKE_SEAT_CONFLICT`
      (`IntakeFormV1._no_conflicting_role_bindings`, `intake_form.py`).
      CORRECTION found during execution: unlike `seat_bindings.py`'s
      `resolve_seat_bindings`, grep confirmed `IntakeFormV1.seats` has NO
      consumer anywhere in `cli/main.py`/`mcp_server.py` that reads a
      "resolved" projection of it — the field is purely a self-consistency
      check on the form today (per its own docstring: "never touches
      RunManifest... only checks whether a caller's stated intent would be
      well-formed"). There is nothing to resolve INTO, so the validator now
      returns `seats` exactly as given (unresolved, not silently repaired)
      instead of computing and discarding a winner nobody reads; a future
      caller wiring `seats` to an actual run applies
      `seat_bindings.resolve_seat_bindings`'s own precedence rule at that
      point. `GROUP_ALIASES` import removed (now unused).
      Rewrote `error_catalog.py`'s `INTAKE_SEAT_CONFLICT` entry text (no
      longer claims "the harness refuses this") and
      `tests/test_intake_form.py::test_seat_conflict_raises_intake_seat_conflict`
      (renamed `..._now_validates_unchanged`).
      Verified the JSON Schema (`IntakeFormV1.model_json_schema()`) is
      BYTE-IDENTICAL before/after (diffed directly) — only validator
      BEHAVIOR changed, no field/type/description moved — so R9's four-pin
      FORM_DR1 regeneration is NOT triggered by this step.
      done-when: `python -m pytest tests/test_intake_form.py tests/test_error_catalog.py -q` passes, 0 failed.
      DONE: `17 passed`.

- [x] 13. (S-V1) [COMMIT] Convert `cli/main.py::_cmd_validate_intake`
      to advisory per R6: report every violation and return 0, EXCEPT
      when the violation set contains at least one genuine parse/shape
      error (missing field, wrong type — a non-input per R2, still exit
      1) or `_load_intake_file` itself fails. Implemented by classifying
      each `ValidationError` item via `intake_form._LEADING_CODE`
      (matches our own `"CODE: message"` raises) — all-semantic exits 0,
      any-structural exits 1; a mixed set (one semantic, one structural)
      correctly stays non-zero since the structural error is still real.
      Added four CLI-level regression tests (none existed before, per the
      census): valid file (exit 0), semantic violation — cycles ceiling —
      (exit 0, message printed), missing required field (exit 1), and
      unparseable file (exit 1). Confirmed MCP `validate_intake` needs no
      change (`tests/test_mcp.py tests/test_mcp_help.py -q` all pass
      unchanged — it already returns `{"ok": False, "violations": [...]}`
      as ordinary tool data, per the census's own finding).
      done-when: new CLI test passes; `python -m pytest tests/test_mcp.py -q -k validate_intake` passes unchanged; commit and push.
      DONE: `tests/test_intake_form.py tests/test_error_catalog.py -q` -> `21 passed`;
      `tests/test_mcp.py tests/test_mcp_help.py -q` -> `89 passed`.

- [x] 14. (S-DOC) [COMMIT] Ledger REQUEST.md's two operator-verbatim
      statements (R1 and the superseded R1a) as a new standing entry in
      CLAUDE.md's "Operator design laws" section, quoting the operator
      verbatim, noting the supersession explicitly, in the SAME commit
      as this step (a docs-only commit is acceptable here since no code
      changes in this step).
      done-when: `grep -q "All configurations should be allowed" CLAUDE.md`, `grep -q "flat out denial" CLAUDE.md`, then commit and push.
      DONE: both checks pass; new bullet added after "Tokens are cheap;
      the agent is not", quoting R1 verbatim and noting R1a's
      supersession, pointing at this tranche directory.

- [x] 15. (S-VERIFY) Prove R8 (old roots replay byte-unchanged) with a
      targeted `verify_root_report` on a committed root that carries
      `bridge_policy` (grep found `grounded_two_stage` in
      `experiments/2026-08-04-change-rung5-dumb-alternative-backend/ab-home/runs/run-9a6be78e1e79184a0bd89923b957586c/run-manifest.json`
      — a real committed root, not a fixture). Compared the FULL report
      (not just `valid`/`epistemic_checks_passed`) against the identical
      root read by the pre-tranche code, via `git worktree add
      /tmp/before-tranche a9d9b31a3` (the tranche's own base commit) rather
      than `git stash` (14 commits deep by this step; stash/pop across
      that many is itself risky) — `pip install -e` was not even needed
      since the worktree's `src/` was added to `sys.path` directly.
      done-when: `python -c "from deepreason.verification.report import verify_root_report; print(verify_root_report('<root>'))"` output pasted, matching the pre-change baseline exactly.
      DONE: both before and after report `valid=True`,
      `epistemic_checks_passed=False` (a pre-existing, unrelated fact about
      this root, not something this tranche caused); the FULL
      `model_dump(mode='json')` of both reports diffed as byte-identical.
      Worktree removed after comparison (`git worktree remove
      /tmp/before-tranche --force`).

- [x] 16. (all) Map check: `python tools/docs_verify.py`
      done-when: exactly the 3 pre-existing `CON-run-identity.md`
      shallow-clone failures from SPEC §7's baseline, no new failures
      (paste the output).
      DONE: `docs_verify [full]: 53 documents, 859 checks, 4 workers` ->
      exactly 3 failed, all `CON-run-identity.md` shallow-clone
      `git log`/`git show` ambiguous-revision failures, matching SPEC §7's
      baseline exactly (this run also caught and required fixing the two
      real map-doc drifts from steps 9-11, already committed).

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
