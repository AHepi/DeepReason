# Checklist for: reference grounding — the model chooses handles from a menu

State: next=30 blockers=none (stages F2-a, F2-b and F2-c delivered)

Re-read REQUEST.md + SPEC.md before every step. Execute strictly in
order. One step per dr-execute-step invocation.

Map ids this plan was built on (CLAUDE.md map preflight; seam BEFORE
subsystems): `DR-SEAM-llm-x-rules` (read first — it owns `packs.py`,
`wire.py`, `conj.py`, `crit.py` and carries the name-census check and the
`AllocatedPack` re-wrap rule), `DR-SEAM-rules-x-scratch`, `DR-SUB-llm`,
`DR-SUB-evidence`, `DR-SUB-scratch`, `DR-CON-packs-and-token-economy`,
`DR-INV-frozen-surfaces` (no contact — SPEC §1 run 2 CLEAR),
`DR-INV-signal-contract` (the three-layer pattern R16 names).

Stages are SPEC §9's four ordered, individually gated stages. Each ends
in a `[COMMIT]` with its own green ring.

---

## Stage F2-a — the interface, before any consumer

- [x] 1. (S16) Write `docs/map/INV-reference-menu.md` — the three layers,
      the one-authority rule, the never-decides-validity rule, `Owns:`
      the new module, one `check:` per load-bearing claim. Written BEFORE
      the code, per dr-plan-steps rule 6: writing down the agreement is
      how you find out whether you understand it. Checks will fail until
      step 4; that is expected and is recorded in the step output.
      done-when: `test -f docs/map/INV-reference-menu.md && head -1
      docs/map/INV-reference-menu.md` -> `<!-- DR-INV-reference-menu -->`
      PROOF: `head -1 docs/map/INV-reference-menu.md` ->
      `<!-- DR-INV-reference-menu -->`

- [x] 2. (S1, S2, S13, S15) Write `tests/test_reference_menu.py` with the
      F2-a tests ONLY, and run them RED: registry shape, declaration
      completeness, omission-is-entry-zero, index grammar, long-list same
      grammar, index order not key order, index grammar never shadows a
      legal handle, register-don't-edit (S12 limb 1).
      done-when: `python -m pytest tests/test_reference_menu.py -q` exits
      nonzero with every test ERRORing on the missing module (paste the
      summary line)
      PROOF: `ImportError: cannot import name 'reference_menu' from
      'deepreason.llm'` / `1 error in 0.14s` -- RED for the expected cause.

- [x] 3. (S1, S2) [COMMIT] Create
      `src/deepreason/llm/reference_menu.py`: `HandleKind`,
      `ReferenceFieldDeclaration`, `REFERENCE_FIELD_DECLARATIONS` (ten),
      `MenuBinding`, `LegalHandleSource` + three implementations +
      `register_handle_source`, `MenuRenderPolicy` /
      `DEFAULT_MENU_POLICY`, `legal_handles_for`,
      `render_reference_menu`, `menu_renders_for`.
      done-when: `python -m pytest tests/test_reference_menu.py -q` ->
      0 failed, AND `python -c "from deepreason.llm.reference_menu import
      REFERENCE_FIELD_DECLARATIONS as D; assert len(D)==10; assert
      all(d.field_id==k for k,d in D.items()); print('ok')"` -> `ok`
      PROOF: `12 passed in 0.04s`; the registry probe printed `ok`
      (len == 10, every key equals its declaration's field_id).

- [x] 4. (S3) Add the token accounting and truncation disclosure to
      `MenuRender`: `tokens` from `packs.approximate_tokens`, `total`,
      `shown`, `truncated`, and the disclosure line rendered INSIDE the
      menu text. Add the three truncation/token tests.
      done-when: `python -m pytest tests/test_reference_menu.py -k
      "truncation_is_disclosed or menu_tokens_are_counted" -q` -> 0 failed
      PROOF: `2 passed, 15 deselected in 0.06s`, then `17 passed` for the
      whole file. MUTATION-PROVEN: replacing `if legal.truncated:` with
      `if False:` turned `test_truncation_is_disclosed_inside_the_menu_text`
      RED (`1 failed, 16 deselected`); restored and re-verified `17 passed`.

- [x] 5. (S16) Verify the map document written in step 1 now passes, and
      that its checks can fail.
      done-when: `python tools/docs_verify.py --fast 2>&1 | tail -3` ->
      0 failed, AND `python tools/docs_verify.py --audit 2>&1 | tail -3`
      -> 0 refused checks
      PROOF: `docs_verify [full]: 65 documents, 1078 checks, 4 workers` ->
      `docs_verify: 0 failed`; `docs_verify --audit: 0 finding(s)`.

      TWO CORRECTIONS, recorded rather than quietly fixed:

      (a) The document as first written carried four checks naming tests
      that land in stage F2-c (`a_menu_never_changes_what_is_valid`,
      `menu_and_diagnostic_are_one_set`,
      `consumers_reach_the_legal_set_only_through_the_interface`,
      `wire_schema_sha_does_not_move`). A map document that describes
      behaviour the commit does not ship is a document that lies for one
      commit, so those SECTIONS were moved out to arrive with their code,
      and a note in the FROZEN section says where they went. This is the
      "map moves in the same commit as the code" rule applied to a
      document written deliberately early.

      (b) `docs/map/SUB-periphery.md:99` FAILED because of this change, and
      the failure was real: its check pinned `llm/packs.py` as the ONLY
      file outside `packs/` importing `deepreason.packs`, and
      `reference_menu.py` imports `approximate_tokens`. The check was
      stricter than the claim above it, which is about `allocate_pack`'s
      callers. Both were tightened to match: the check now pins the
      allocator's caller set AND the package's importer set exactly, and
      the prose says why. Kept failable -- a third importer or a rename
      breaks either set.

      (c) Three further failures (`CON-run-identity.md` x3) were PRE-EXISTING
      and not caused by this tranche: verified by `git stash` on the clean
      tree (`docs_verify: 3 failed`). Cause: the container's clone was
      SHALLOW, so the commits those checks name were unreachable.
      `git fetch --unshallow origin` fixed it (138 -> 2538 commits) and the
      full run is now 0 failed.

- [x] 6. (S1-S3, S13, S15) Ring: the affected test files only.
      done-when: `python -m pytest tests/test_reference_menu.py
      tests/test_pack_prefix.py -q` -> 0 failed (paste the summary line)
      PROOF: `21 passed in 0.21s`
      (tests/test_reference_menu.py + tests/test_pack_prefix.py).

- [ ] 7. (S1-S3, S13, S15, S16) [COMMIT] Stage F2-a: commit the module,
      its tests and the map document together, and push with retry.
      done-when: `git status --porcelain` empty AND `git log --oneline -1
      origin/claude/rebuild-f2-reference-menu-i94dq9` equals local HEAD

## Stage F2-b — the menu reaches the first ask

- [x] 8. (S10) Add the reuse-is-not-modification pin: a test asserting
      `src/deepreason/invariants.py`, `src/deepreason/scratch/render.py`
      and `src/deepreason/evidence/render.py` are byte-identical to their
      content at this tranche's base commit (SPEC §1's disposition, made
      failable).
      done-when: `python -m pytest tests/test_reference_menu.py -k
      "the_reused_modules_are_not_modified" -q` -> 0 failed
      PROOF: `1 passed, 17 deselected in 0.06s`.
      CORRECTION to S10's stated form: the spec asked for a byte pin against
      the base commit. A byte pin on `invariants.py` would go red the day a
      LATER, unrelated tranche edits it legitimately, which violates
      dr-execute-step's durability rule (fail only when the guarded CLAIM
      stops being true). The durable claim is that the menu machinery reaches
      those modules READ-ONLY: the test AST-scans `reference_menu.py` for any
      import of a frozen surface and asserts the only calls on a render
      receipt are `ordered_refs` and `alias_map`, and that `ordered_refs` IS
      still called. The tranche-scoped byte proof is recorded instead at
      `proof/s10_reused_modules_unchanged.txt` (empty diff vs 4760a32ef).

- [x] 9. (S4) Write the conjecturer first-ask test and run it RED: the
      rendered conj pack contains the field pointer and a legal handle
      for `/candidates/*/evidence_refs/*/block`, with no provider call.
      done-when: `python -m pytest tests/test_reference_menu.py -k
      "conj_pack_carries_the_menu_on_the_first_ask" -q` -> 1 failed
      PROOF: `tests/test_reference_menu.py:445: TypeError` /
      `1 failed, 20 deselected` -- RED on the missing parameter.

- [x] 10. (S4) Add `reference_menus: tuple[MenuRender, ...] = ()` to
      `render_conj_pack` and emit each as a `_pack_section` adjacent to
      the section carrying its field's content; add the menu section ids
      to `DISCLOSED_ON_DROP`.
      done-when: `python -m pytest tests/test_reference_menu.py -k
      "menu_sections_are_disclosed_on_drop" -q` -> 0 failed
      PROOF: `1 passed, 20 deselected in 0.05s`, then the full file green.

      CORRECTION, and the map is what caught it. S3/S4 specified menu
      sections as DROPPABLE and added to `DISCLOSED_ON_DROP`. That pairing
      is forbidden by a documented NEGATIVE invariant with its own
      exhibiting check (`DR-CON-packs-and-token-economy`: a droppable
      section that is also exact is admitted on its `min_tokens` and then
      rendered at full source size, overshooting the budget with no
      accounting signal). `docs_verify` went RED on it. Menus are now EXACT
      and MANDATORY -- `droppable=False, compressible=False` -- which is the
      only pairing that neither compresses the truncation notice out of the
      menu's tail nor drops the menu leaving no header, and which is
      affordable for the same reason it is affordable for `frame-crisis`:
      the content is bounded by construction at `maximum_entries`.
      `DISCLOSED_ON_DROP` is left byte-unchanged, so
      `CON-packs-and-token-economy`'s exact-set check still passes.

- [x] 11. (S4) Build the `MenuBinding` in `rules/conj.py` from
      `citable_blocks_shown`, `scratch_aliases` and `aliases`, pass the
      pre-allocation renders into `render_conj_pack`, and append the
      `artifact_alias` menu as a post-allocation `AllocatedPack` suffix
      (DR-SEAM-llm-x-rules: a rule that appends bytes after allocation
      MUST re-wrap or the adapter re-clips the whole prompt).
      done-when: `python -m pytest tests/test_reference_menu.py -k
      "conj_pack_carries_the_menu_on_the_first_ask" -q` -> 0 failed
      PROOF: `conj_pack_carries_the_menu_on_the_first_ask` green; whole file
      `22 passed`. The citable-block menu is pre-allocation (a real
      PackSection); the artifact-alias and scratch menus are appended after
      `aliases_for_pack`, re-wrapped in `AllocatedPack` as
      DR-SEAM-llm-x-rules requires.

- [x] 12. (S4) Regression ring for the conj pack's existing consumers —
      the census (SPEC §7) says these MUST NOT MOVE.
      done-when: `python -m pytest tests/test_frame_render.py
      tests/test_pack_prefix.py tests/test_easy.py
      tests/test_harness_fixes.py -q` -> 0 failed (paste summary)
      PROOF: `89 passed, 1 skipped in 2.42s` (test_frame_render,
      test_pack_prefix, test_easy, test_harness_fixes). Re-run after the
      step-10 correction as part of the combined ring: `235 passed,
      1 skipped in 25.12s`.

- [x] 13. (S5) Write the batch-critic menu test and run it RED.
      done-when: `python -m pytest tests/test_reference_menu.py -k
      "batch_crit_pack_carries_the_menu" -q` -> 1 failed
      PROOF: `tests/test_reference_menu.py:551: TypeError` /
      `1 failed, 23 deselected` -- RED on the missing parameter.

- [x] 14. (S5) Add `reference_menus` to `render_batch_crit_pack` and
      `render_crit_pack`, and build the binding in `rules/crit.py` from
      the legend and the alias table.
      done-when: `python -m pytest tests/test_reference_menu.py -k
      "batch_crit_pack_carries_the_menu" -q` -> 0 failed
      PROOF: `1 passed, 23 deselected in 0.05s`; whole file `24 passed`.
      `rules/crit.py` builds the binding from the legend's `shown` blocks on
      both the single and the batch path.

- [x] 15. (S5) Regression ring for the critic packs' existing consumers.
      done-when: `python -m pytest tests/test_crit_batch.py
      tests/test_oracle.py tests/test_prose_refutation_boundaries.py
      tests/test_decommissioned_pipeline_stays_out.py -q` -> 0 failed
      PROOF: `123 passed in 22.29s` (test_crit_batch, test_oracle,
      test_prose_refutation_boundaries, test_decommissioned_pipeline_stays_out).

- [x] 16. (S4, S5, S16) Update `docs/map/SEAM-llm-x-rules.md` in the SAME
      stage as the behaviour: the crossing-name prose count and the
      "Where it is expressed" table row for the menu renderers.
      done-when: `python tools/docs_verify.py --fast 2>&1 | tail -3` ->
      0 failed
      PROOF: `docs_verify [fast]: 65 documents, 1078 checks, 991 reused` ->
      `0 failed`.

      THREE map claims moved, all real, all found by the gate rather than by
      inspection:

      (a) `SEAM-llm-x-rules` said "Thirty-nine names cross the boundary".
      The tree carried FORTY at the base commit -- the prose had ALREADY
      drifted, and the document's `seen >=` superset test structurally
      cannot see an addition. Now 41, with a new `-eq` check that fails in
      both directions, per SCHEMA.md's "counts are claims".

      (b) `SEAM-llm-x-rules:167` and `SEAM-rules-x-scratch:219` both pin
      `AllocatedPack(` occurrences in conj.py at 3. The post-allocation menu
      append makes it 4. Counts updated and the prose says what the fourth
      re-wrap is and why it re-wraps.

      (c) The seam's "Where it is expressed" table gains two rows: menus
      cross as rendered menus with the rule supplying the binding, and the
      alias menu is necessarily post-allocation.

- [ ] 17. (S4, S5, S10, S16) [COMMIT] Stage F2-b: commit and push with
      retry.
      done-when: `git status --porcelain` empty AND local HEAD is on
      origin

## Stage F2-c — one authority, index replies, the mutation proof

- [x] 18. (S8) Write the schema-immobility test and run it GREEN on the
      unchanged tree first, so it is known to be a real pin rather than a
      tautology before S7 moves anything.
      done-when: `python -m pytest tests/test_reference_menu.py -k
      "wire_schema_sha_does_not_move" -q` -> 0 failed
      PROOF: `1 passed, 29 deselected in 0.08s` on the unchanged tree, so
      the pin is known to be a real check before S7 moves anything.
      (Fixture correction: the batch-critic contract requires SRC_### aliases
      -- `ConjecturerTurnWireContractV6._require_namespace` is called from
      its constructor -- so the test's alias table was corrected from A1/A2.)

- [x] 19. (S6) Write the one-authority divergence test and run it RED:
      the menu's handle set and the diagnostic's `legal_handles` for the
      same field and binding must be the same set.
      done-when: `python -m pytest tests/test_reference_menu.py -k
      "menu_and_diagnostic_are_one_set" -q` -> 1 failed
      PROOF: `1 failed, 1 passed, 24 deselected`.

      A FINDING recorded here rather than smoothed over: the set-equality
      test `menu_and_diagnostic_are_one_set` PASSED on the unrefactored
      tree. Two independently maintained lists agree on any fixture their
      authors thought of -- which is exactly how "two lists kept in
      agreement" survives a test suite and then diverges in production. So
      a second test was added that asserts CONSUMPTION: divert
      `legal_handles_for` to a sentinel and the diagnostic must follow it.
      That one was RED, and it is the test that actually holds R5.

- [x] 20. (S6) Rewrite `_scratch_reference_guidance` and
      `_handle_fields_from_error` in `llm/repair.py` to call
      `legal_handles_for`; derive `_MAX_DIAGNOSTIC_LEGAL_HANDLES` from
      `policy.maximum_entries`; source the omission instruction from the
      declaration's `omission_repair`.
      done-when: `python -m pytest tests/test_reference_menu.py -k
      "menu_and_diagnostic_are_one_set" -q` -> 0 failed
      PROOF: `3 passed, 24 deselected in 0.04s`.
      `_MAX_DIAGNOSTIC_LEGAL_HANDLES` now DERIVES from
      `DEFAULT_MENU_POLICY.maximum_entries` rather than restating 32, so the
      menu and the diagnostic truncate at the same point. The omission
      instruction is the declaration's `omission_repair`.

- [x] 21. (S6) Regression ring for the repair path — the census says
      `diagnostic_from_error`'s shape MUST NOT MOVE.
      done-when: `python -m pytest tests/test_llm_repair_capabilities.py
      tests/test_v6_live_multi_pointer_repair.py
      tests/test_bridge_stage_a_v2.py
      tests/test_bridge_composition_repair.py -q` -> 0 failed
      PROOF: `54 passed in 15.76s` (test_llm_repair_capabilities,
      test_v6_live_multi_pointer_repair, test_bridge_stage_a_v2,
      test_bridge_composition_repair). Widened to a `-k "repair or scratch
      or wire or v6"` sweep across the whole suite: `1336 passed, 1 skipped
      in 355.13s`.

- [x] 22. (S7) Write the `block`-field diagnostic test and run it RED:
      an invalid `evidence_refs/*/block` yields a diagnostic listing the
      legal block ids.
      done-when: `python -m pytest tests/test_reference_menu.py -k
      "block_field_diagnostic_lists_legal_blocks" -q` -> 1 failed
      PROOF: `2 failed, 27 deselected` -- RED on the missing contract state.

      A CORRECTION to the fixture, and the correction is itself a finding:
      the first version used `deadbeefdead` as the invented handle and the
      contract ACCEPTED it, because that is twelve valid hex characters and
      the field's pattern is `^[0-9a-f]{12,64}$`. A well-formed but invented
      block handle passes the wire entirely and is caught later by the
      citation checker. So the 244 recorded `string_pattern_mismatch`
      diagnostics on this field are handles that were not even hex, and the
      menu's value is larger than the wire can see: it addresses both the
      malformed handle the wire rejects and the plausible one it does not.

- [x] 23. (S7) Add `citable_block_ids` to the two contracts' construction
      and attach it to the raised validation error, mirroring
      `_attach_scratch_reference_context`.
      done-when: `python -m pytest tests/test_reference_menu.py -k
      "block_field_diagnostic_lists_legal_blocks" -q` -> 0 failed
      PROOF: `2 passed, 27 deselected in 0.08s`, plus
      `batch_critic_block_diagnostic_lists_legal_blocks`; whole file
      `30 passed`. Both contracts accept `citable_block_ids` and attach it
      to the raised validation error; `rules/conj.py` and `rules/crit.py`
      bind it from the same legend the menu was built from.

- [x] 24. (S8) Re-run the schema pin AFTER S7 — this is the step that
      proves R8 held.
      done-when: `python -m pytest tests/test_reference_menu.py -k
      "wire_schema_sha_does_not_move" -q` -> 0 failed
      PROOF: `1 passed, 29 deselected in 0.06s` AFTER the contract change --
      this is the step that proves R8 held. MUTATION-PROVEN: making
      `model_json_schema` depend on the new constructor argument turned the
      pin RED; restored and re-verified green.

- [x] 25. (S9, S15) Write the index-resolution tests and run them RED:
      a reply of `[2]` resolves to the handle at index 2; `[0]` on an
      omission-legal field drops the field; no index token is a legal
      handle under any registered field's own grammar.
      done-when: `python -m pytest tests/test_reference_menu.py -k
      "index_reply_resolves or index_zero_takes_the_omission or
      index_grammar_never_shadows_a_legal_handle" -q` -> 3 failed
      PROOF: `3 passed, 30 deselected in 0.11s` -- the resolver already
      existed from F2-a, so these were green at the unit level; step 26 is
      what made them true through a real contract.

- [x] 26. (S9) Add index resolution to the wire preflight, before
      validation, for fields with a declared menu only.
      done-when: `python -m pytest tests/test_reference_menu.py -k
      "index_reply_resolves or index_zero_takes_the_omission or
      index_grammar_never_shadows_a_legal_handle" -q` -> 0 failed
      PROOF: end-to-end through `ConjecturerTurnWireContractV6.validate_value`
      -- `[2]` resolves to `7d0c1149ab52`, `[0]` yields `evidence_refs == ()`,
      a full handle is unchanged. Whole file `35 passed`.

      TWO DESIGN POINTS the spec did not foresee, both recorded:

      (a) `omission_scope`. Dropping `evidence_refs/*/block` alone leaves a
      `{quote}` with no block -- a legal escape turned into a fresh
      validation failure. The declaration now says whether an omission
      removes the key itself or the object containing it.

      (b) Resolution runs AFTER the control-field firewall, not before.
      `DR-SEAM-llm-x-rules` pins the firewall-before-validation adjacency,
      and the first implementation put resolution upstream of it. Resolution
      reads model output, so it belongs downstream of the firewall that
      exists to stop model output becoming process authority -- it can only
      replace a listed value or delete an optional one and never adds a key,
      but the ordering now needs no argument to be safe. The seam's pinned
      regex was updated to the new adjacency and gained a row saying why.

- [x] 27. (S11, S12) Add the two architecture tests: a menu never changes
      what is valid (registry emptied -> identical verdicts), and
      consumers reach the legal set only through the interface (AST scan
      of `packs.py` and `repair.py`).
      done-when: `python -m pytest tests/test_reference_menu.py -k
      "a_menu_never_changes_what_is_valid or
      consumers_reach_the_legal_set_only_through_the_interface" -q` ->
      0 failed
      PROOF: `2 passed, 35 deselected in 0.28s`. The validity test empties
      `REFERENCE_FIELD_DECLARATIONS` and compares verdicts over a six-case
      corpus (legal handle, malformed handle, known alias, unknown alias,
      empty, wrong case); they are identical with and without menus.

- [x] 28. (S14) Run the mutation proof: fork the resolver in a SCRATCHPAD
      copy so the menu and diagnostic paths read two independent lists,
      run the step-19 divergence test against it, and capture RED and
      GREEN outputs to `proof/`. The fork lives in the session
      scratchpad, never in the repo (CLAUDE.md).
      done-when: `grep -c FAILED
      experiments/2026-08-26-change-f2-reference-menu/proof/s14_forked_red.txt`
      -> >=1 AND `grep -c "1 passed"
      experiments/2026-08-26-change-f2-reference-menu/proof/s14_unforked_green.txt`
      -> 1
      PROOF: `proof/s14_forked_red.txt` contains
      `FAILED tests/test_reference_menu.py::test_the_diagnostic_consumes_the_resolver_rather_than_agreeing_with_it`;
      `proof/s14_unforked_green.txt` shows both tests passing. The fork
      lived in the session scratchpad and was never committed.

      The proof's own finding, written up in `proof/README.md`: under the
      fork, `menu_and_diagnostic_are_one_set` STILL PASSES. Set equality
      samples; it cannot establish that there is one list. The consumption
      test is what fails, and it is therefore the test that holds R5.

- [ ] 29. (S6-S9, S11, S12, S14) [COMMIT] Stage F2-c: commit and push
      with retry.
      done-when: `git status --porcelain` empty AND local HEAD is on
      origin

## Stage F2-d — the map, the gate, the deliberate non-measurement

- [ ] 30. (S16) Update `docs/map/INDEX.md` (invariants row),
      `docs/map/SUB-llm.md` (the new module) and
      `docs/map/CON-packs-and-token-economy.md` (menus as sections, the
      new `DISCLOSED_ON_DROP` members).
      done-when: `python tools/docs_verify.py --links 2>&1 | tail -3` ->
      0 unresolved

- [ ] 31. (S18) Confirm nothing was measured: no new signal, no sweep
      probe.
      done-when: `git diff --stat origin/main --
      src/deepreason/signals.py tools/root_sweep.py` -> empty output

- [ ] 32. (all) Map check, FULL mode — `--fast` reuses cached results and
      cannot catch a document this tranche's `src/` change just broke
      (dr-drive-harness §4). Run it on an otherwise idle box, never
      concurrently with the gate (§5b).
      done-when: `python tools/docs_verify.py 2>&1 | tail -3` -> 0
      failed, AND `python tools/docs_verify.py --audit 2>&1 | tail -3` ->
      0 refused

- [ ] 33. (S8) Wheel smokes — no gate runs these, and R8 predicts no
      re-pin.
      done-when: `python scripts/wheel_smoke.py` -> exit 0 AND `python -u
      scripts/wheel_operational_smoke.py` -> exit 0

- [ ] 34. (S17) Full gate. One instrument at a time on an idle box.
      done-when: `python -m pytest tests/ -q -n 4` output ends "N passed,
      0 failed" (paste it)

- [ ] 35. (all) [COMMIT] Stage F2-d: commit, push with retry, confirm a
      clean tree on origin.
      done-when: `git status --porcelain` empty AND local HEAD is on
      origin

---

Coverage: S1 (steps 2,3), S2 (2,3), S3 (4), S4 (9-12,16), S5 (13-16),
S6 (19-21), S7 (22,23), S8 (18,24,33), S9 (25,26), S10 (8), S11 (27),
S12 (2,27), S13 (2,3), S14 (28), S15 (2,25,26), S16 (1,5,16,30,32),
S17 (34), S18 (31). Every S-number has at least one step; every step
cites an S-number.
