# Checklist for: reference grounding — the model chooses handles from a menu

State: next=1 blockers=none

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

- [ ] 1. (S16) Write `docs/map/INV-reference-menu.md` — the three layers,
      the one-authority rule, the never-decides-validity rule, `Owns:`
      the new module, one `check:` per load-bearing claim. Written BEFORE
      the code, per dr-plan-steps rule 6: writing down the agreement is
      how you find out whether you understand it. Checks will fail until
      step 4; that is expected and is recorded in the step output.
      done-when: `test -f docs/map/INV-reference-menu.md && head -1
      docs/map/INV-reference-menu.md` -> `<!-- DR-INV-reference-menu -->`

- [ ] 2. (S1, S2, S13, S15) Write `tests/test_reference_menu.py` with the
      F2-a tests ONLY, and run them RED: registry shape, declaration
      completeness, omission-is-entry-zero, index grammar, long-list same
      grammar, index order not key order, index grammar never shadows a
      legal handle, register-don't-edit (S12 limb 1).
      done-when: `python -m pytest tests/test_reference_menu.py -q` exits
      nonzero with every test ERRORing on the missing module (paste the
      summary line)

- [ ] 3. (S1, S2) [COMMIT] Create
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

- [ ] 4. (S3) Add the token accounting and truncation disclosure to
      `MenuRender`: `tokens` from `packs.approximate_tokens`, `total`,
      `shown`, `truncated`, and the disclosure line rendered INSIDE the
      menu text. Add the three truncation/token tests.
      done-when: `python -m pytest tests/test_reference_menu.py -k
      "truncation_is_disclosed or menu_tokens_are_counted" -q` -> 0 failed

- [ ] 5. (S16) Verify the map document written in step 1 now passes, and
      that its checks can fail.
      done-when: `python tools/docs_verify.py --fast 2>&1 | tail -3` ->
      0 failed, AND `python tools/docs_verify.py --audit 2>&1 | tail -3`
      -> 0 refused checks

- [ ] 6. (S1-S3, S13, S15) Ring: the affected test files only.
      done-when: `python -m pytest tests/test_reference_menu.py
      tests/test_pack_prefix.py -q` -> 0 failed (paste the summary line)

- [ ] 7. (S1-S3, S13, S15, S16) [COMMIT] Stage F2-a: commit the module,
      its tests and the map document together, and push with retry.
      done-when: `git status --porcelain` empty AND `git log --oneline -1
      origin/claude/rebuild-f2-reference-menu-i94dq9` equals local HEAD

## Stage F2-b — the menu reaches the first ask

- [ ] 8. (S10) Add the reuse-is-not-modification pin: a test asserting
      `src/deepreason/invariants.py`, `src/deepreason/scratch/render.py`
      and `src/deepreason/evidence/render.py` are byte-identical to their
      content at this tranche's base commit (SPEC §1's disposition, made
      failable).
      done-when: `python -m pytest tests/test_reference_menu.py -k
      "the_reused_modules_are_not_modified" -q` -> 0 failed

- [ ] 9. (S4) Write the conjecturer first-ask test and run it RED: the
      rendered conj pack contains the field pointer and a legal handle
      for `/candidates/*/evidence_refs/*/block`, with no provider call.
      done-when: `python -m pytest tests/test_reference_menu.py -k
      "conj_pack_carries_the_menu_on_the_first_ask" -q` -> 1 failed

- [ ] 10. (S4) Add `reference_menus: tuple[MenuRender, ...] = ()` to
      `render_conj_pack` and emit each as a `_pack_section` adjacent to
      the section carrying its field's content; add the menu section ids
      to `DISCLOSED_ON_DROP`.
      done-when: `python -m pytest tests/test_reference_menu.py -k
      "menu_sections_are_disclosed_on_drop" -q` -> 0 failed

- [ ] 11. (S4) Build the `MenuBinding` in `rules/conj.py` from
      `citable_blocks_shown`, `scratch_aliases` and `aliases`, pass the
      pre-allocation renders into `render_conj_pack`, and append the
      `artifact_alias` menu as a post-allocation `AllocatedPack` suffix
      (DR-SEAM-llm-x-rules: a rule that appends bytes after allocation
      MUST re-wrap or the adapter re-clips the whole prompt).
      done-when: `python -m pytest tests/test_reference_menu.py -k
      "conj_pack_carries_the_menu_on_the_first_ask" -q` -> 0 failed

- [ ] 12. (S4) Regression ring for the conj pack's existing consumers —
      the census (SPEC §7) says these MUST NOT MOVE.
      done-when: `python -m pytest tests/test_frame_render.py
      tests/test_pack_prefix.py tests/test_easy.py
      tests/test_harness_fixes.py -q` -> 0 failed (paste summary)

- [ ] 13. (S5) Write the batch-critic menu test and run it RED.
      done-when: `python -m pytest tests/test_reference_menu.py -k
      "batch_crit_pack_carries_the_menu" -q` -> 1 failed

- [ ] 14. (S5) Add `reference_menus` to `render_batch_crit_pack` and
      `render_crit_pack`, and build the binding in `rules/crit.py` from
      the legend and the alias table.
      done-when: `python -m pytest tests/test_reference_menu.py -k
      "batch_crit_pack_carries_the_menu" -q` -> 0 failed

- [ ] 15. (S5) Regression ring for the critic packs' existing consumers.
      done-when: `python -m pytest tests/test_crit_batch.py
      tests/test_oracle.py tests/test_prose_refutation_boundaries.py
      tests/test_decommissioned_pipeline_stays_out.py -q` -> 0 failed

- [ ] 16. (S4, S5, S16) Update `docs/map/SEAM-llm-x-rules.md` in the SAME
      stage as the behaviour: the crossing-name prose count and the
      "Where it is expressed" table row for the menu renderers.
      done-when: `python tools/docs_verify.py --fast 2>&1 | tail -3` ->
      0 failed

- [ ] 17. (S4, S5, S10, S16) [COMMIT] Stage F2-b: commit and push with
      retry.
      done-when: `git status --porcelain` empty AND local HEAD is on
      origin

## Stage F2-c — one authority, index replies, the mutation proof

- [ ] 18. (S8) Write the schema-immobility test and run it GREEN on the
      unchanged tree first, so it is known to be a real pin rather than a
      tautology before S7 moves anything.
      done-when: `python -m pytest tests/test_reference_menu.py -k
      "wire_schema_sha_does_not_move" -q` -> 0 failed

- [ ] 19. (S6) Write the one-authority divergence test and run it RED:
      the menu's handle set and the diagnostic's `legal_handles` for the
      same field and binding must be the same set.
      done-when: `python -m pytest tests/test_reference_menu.py -k
      "menu_and_diagnostic_are_one_set" -q` -> 1 failed

- [ ] 20. (S6) Rewrite `_scratch_reference_guidance` and
      `_handle_fields_from_error` in `llm/repair.py` to call
      `legal_handles_for`; derive `_MAX_DIAGNOSTIC_LEGAL_HANDLES` from
      `policy.maximum_entries`; source the omission instruction from the
      declaration's `omission_repair`.
      done-when: `python -m pytest tests/test_reference_menu.py -k
      "menu_and_diagnostic_are_one_set" -q` -> 0 failed

- [ ] 21. (S6) Regression ring for the repair path — the census says
      `diagnostic_from_error`'s shape MUST NOT MOVE.
      done-when: `python -m pytest tests/test_llm_repair_capabilities.py
      tests/test_v6_live_multi_pointer_repair.py
      tests/test_bridge_stage_a_v2.py
      tests/test_bridge_composition_repair.py -q` -> 0 failed

- [ ] 22. (S7) Write the `block`-field diagnostic test and run it RED:
      an invalid `evidence_refs/*/block` yields a diagnostic listing the
      legal block ids.
      done-when: `python -m pytest tests/test_reference_menu.py -k
      "block_field_diagnostic_lists_legal_blocks" -q` -> 1 failed

- [ ] 23. (S7) Add `citable_block_ids` to the two contracts' construction
      and attach it to the raised validation error, mirroring
      `_attach_scratch_reference_context`.
      done-when: `python -m pytest tests/test_reference_menu.py -k
      "block_field_diagnostic_lists_legal_blocks" -q` -> 0 failed

- [ ] 24. (S8) Re-run the schema pin AFTER S7 — this is the step that
      proves R8 held.
      done-when: `python -m pytest tests/test_reference_menu.py -k
      "wire_schema_sha_does_not_move" -q` -> 0 failed

- [ ] 25. (S9, S15) Write the index-resolution tests and run them RED:
      a reply of `[2]` resolves to the handle at index 2; `[0]` on an
      omission-legal field drops the field; no index token is a legal
      handle under any registered field's own grammar.
      done-when: `python -m pytest tests/test_reference_menu.py -k
      "index_reply_resolves or index_zero_takes_the_omission or
      index_grammar_never_shadows_a_legal_handle" -q` -> 3 failed

- [ ] 26. (S9) Add index resolution to the wire preflight, before
      validation, for fields with a declared menu only.
      done-when: `python -m pytest tests/test_reference_menu.py -k
      "index_reply_resolves or index_zero_takes_the_omission or
      index_grammar_never_shadows_a_legal_handle" -q` -> 0 failed

- [ ] 27. (S11, S12) Add the two architecture tests: a menu never changes
      what is valid (registry emptied -> identical verdicts), and
      consumers reach the legal set only through the interface (AST scan
      of `packs.py` and `repair.py`).
      done-when: `python -m pytest tests/test_reference_menu.py -k
      "a_menu_never_changes_what_is_valid or
      consumers_reach_the_legal_set_only_through_the_interface" -q` ->
      0 failed

- [ ] 28. (S14) Run the mutation proof: fork the resolver in a SCRATCHPAD
      copy so the menu and diagnostic paths read two independent lists,
      run the step-19 divergence test against it, and capture RED and
      GREEN outputs to `proof/`. The fork lives in the session
      scratchpad, never in the repo (CLAUDE.md).
      done-when: `grep -c FAILED
      experiments/2026-08-26-change-f2-reference-menu/proof/s14_forked_red.txt`
      -> >=1 AND `grep -c "1 passed"
      experiments/2026-08-26-change-f2-reference-menu/proof/s14_unforked_green.txt`
      -> 1

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
