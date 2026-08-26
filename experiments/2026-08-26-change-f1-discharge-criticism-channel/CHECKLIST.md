# Checklist for: the discharge-required criticism channel (REBUILD tranche F1)

State: next=2b blockers=none

Re-read REQUEST.md + SPEC.md before every step. Execute strictly in order.
One step per `dr-execute-step` invocation. Every step cites its S-number.

**Map ids this plan was built on** (`dr-drive-harness` §4; seams read BEFORE
their subsystems): `DR-SEAM-llm-x-rules` (the pack/dispatch agreement — its
`Owns:` list already covers `llm/packs.py`, `llm/wire.py`, `rules/conj.py`),
`DR-SEAM-calculus-x-rules` (Rung 6's render machinery, the declared vehicle),
`DR-SEAM-rules-x-workflow` (the submission lifecycle),
`DR-SEAM-adjudication-x-rules` (the law line's far side);
`DR-CON-criticism-source`, `DR-CON-conjecture-source`,
`DR-CON-packs-and-token-economy`, `DR-CON-authority`,
`DR-CON-warrants-and-attacks`, `DR-CON-conjecture-kinds`;
`DR-SUB-llm`, `DR-SUB-rules`, `DR-SUB-adjudication`;
`DR-INV-frozen-surfaces`, `DR-INV-signal-contract`.
NEW: `DR-CON-discharge-channel` — created at step 1, because the map had no id
for a discharge channel and writing the agreement down is how you find out
whether you understand it.

**Two counts this plan must not disturb, found by reading the map's own checks
before planning** (they are pinned with `-eq`, so they fail loudly, which is the
point):
- `DR-SEAM-llm-x-rules` pins `grep -rl "deepreason\.llm" src/deepreason/rules
  | wc -l` at **8** and `adapter.call(` in `conj.py`+`crit.py` at **8**. F1 adds
  a `deepreason.discharge` import to `rules/conj.py` — NOT a `deepreason.llm`
  one — and re-uses the existing `conj()` recursion for the re-ask rather than
  opening a new call site. Both counts must read 8 after every step.
- `DR-CON-packs-and-token-economy` line 80 pins `len(j)==17` for
  `render_conj_pack`'s `_pack_section` calls. Adding `open-criticisms` makes it
  **18**. That check is EXPECTED TO MOVE and moves in step 8, the same commit
  as the section.

---

## Commit 1 — interface, registry, record, render (S1, S2, S3, S8, S11)

- [x] 1. (S11) Draft the `DR-CON-discharge-channel` map document: the
      agreement, the three layers (FROZEN interface / VERSIONED registry / FREE
      parameters), what the channel may never touch, and a `Traps` section.
      Write the `check:` lines now, at column 0, for behaviour that does not
      exist yet — they are the specification of what steps 3–7 must make true.
      done-when: the drafted file's first line is
      `<!-- DR-CON-discharge-channel -->` AND it carries >= 6 `check:` lines at
      column 0

      **PLAN CORRECTION, recorded rather than improvised (dr-execute-step
      procedure item 2).** The step as planned said to draft the file directly
      at `docs/map/CON-discharge-channel.md`. That contradicts the tree: this
      skill requires `python tools/docs_verify.py` to PASS before any commit,
      and `docs_verify` scans `docs/map/*.md`, so a draft whose checks describe
      behaviour that does not exist yet would fail the gate at the very step
      that creates it — every step from 1 to 7 would be uncommittable.
      `check: grep -q 'MAP_DIR.glob("\*.md")' tools/docs_verify.py`
      Correction, smallest available: the draft lives in the TRANCHE
      directory as `DESIGN_CON-discharge-channel.md` (committed, so a fresh
      session resumes from it; not scanned, so it cannot fail the map gate),
      and step 8 installs it at `docs/map/CON-discharge-channel.md` in the same
      commit as the code that makes its checks pass. Ordering rule 6 is
      satisfied in full — the agreement is written down BEFORE the code, which
      is how you find out whether you understand it. No scope moved.

      PASTED OUTPUT:
      ```
      $ wc -l experiments/.../DESIGN_CON-discharge-channel.md
      203
      $ head -1 experiments/.../DESIGN_CON-discharge-channel.md
      <!-- DR-CON-discharge-channel -->
      $ grep -c '^`check:' experiments/.../DESIGN_CON-discharge-channel.md
      11
      ```
      Eleven checks, not the six the criterion required. Two of them
      (`test_a_fourth_kind_enters_by_declaration_alone`,
      `test_no_consumer_reaches_past_the_interface`) name the architecture test
      by node id, so the modularity claim is bound to a failable check from the
      moment the document exists — R14's own requirement, written down before
      the code rather than after it.

      **THE `docs_verify` FULL BASELINE, captured here** because it can only be
      measured on an untouched tree and step 8 compares against it:
      ```
      $ python tools/docs_verify.py            # FULL, on 4760a32ef, tree clean
        FAIL CON-run-identity.md:200: git log -M --diff-filter=R --name-status ...
        FAIL CON-run-identity.md:202: git log -1 --format=%s 1637e808 | grep -qi retire
        FAIL CON-run-identity.md:204: test -z "$(git show -M --diff-filter=R ...
      docs_verify: 3 failed
      ```
      All three are the pre-existing `CON-run-identity` failures, and all three
      fail for the same environmental reason rather than a rotted claim: they
      reach for commits (`1637e808`, `f304fec1`) that this container's shallow
      clone does not carry — `fatal: ambiguous argument 'f304fec1': unknown
      revision`. Rung 6's own DELIVERY.md recorded the identical baseline ("3
      failed — all three the pre-existing CON-run-identity shallow-clone
      failures, unchanged from the base"), so this is a known, stable floor and
      not a regression this tranche must clear. **3 is the number every later
      step compares against; anything above 3 is this tranche's fault.**

      One check in this draft is deliberately a placeholder: the F2 composition
      note (R18) is installed at step 26 with the wire, and the draft says so
      in-band rather than carrying a check that would pass vacuously.

- [x] 2. (S8) Write `tests/test_discharge_contract.py` — the architecture test,
      all four checks (interface-only consumption; the package's own import
      confinement to `ontology`/`config`/`programs`; a fourth kind by
      declaration; a policy change as pure configuration). It must be RED now.
      done-when: `python -m pytest tests/test_discharge_contract.py -q 2>&1
      | tail -5` shows an import/collection failure naming
      `deepreason.discharge` (paste it) — the test can fail, which is what
      makes it a check rather than decoration

      PASTED OUTPUT:
      ```
      $ python -m pytest tests/test_discharge_contract.py -q
      tests/test_discharge_contract.py:32: in <module>
          from deepreason.discharge import (
      E   ModuleNotFoundError: No module named 'deepreason.discharge'
      ERROR tests/test_discharge_contract.py
      !!!!!! Interrupted: 1 error during collection !!!!!!
      1 error in 0.21s
      ```

      One anchor was tightened while writing it, and it is worth recording
      because it turned a weak check into a claim. The interface-only test's
      positive anchor was drafted as `len(consumers) >= 2`; a floor of two
      would have been FALSE on the delivered tree and, worse, unfalsifiable in
      the direction that matters. The channel reaches the rest of the tree
      through exactly ONE file, so the anchor now reads
      `assert consumers == ["src/deepreason/rules/conj.py"]` — the blast radius
      stated as a pinned count (`DR-SCHEMA` check-writing rule 6, "counts are
      claims"). `llm/packs.py` is deliberately NOT a consumer: the render hands
      it a plain string, so the pack layer never learns that criticism is what
      it is rendering.

      **ORDERING FAULT IN THE PLAN, found by writing the test (dr-execute-step
      procedure item 3).** Two of the four architecture checks construct
      `Config(DISCHARGE_POLICY=...)`, and `Config` is `extra="forbid"`, so they
      cannot pass until that field exists. The plan put the field in commit 3
      (steps 19–21) for narrative tidiness — grouping "the granted contact"
      together — which inverts a real dependency: `resolve_policy(config)` is
      part of S1 and S1 is step 3. Steps 9, 10, 16 and 18 would all have failed
      their own done-criteria for a reason that is a planning error, not a code
      one.
      Correction, per the re-planning rule (touch only implicated steps; never
      rewrite a CHECKED step's history): steps 19–21 are unchecked, so they are
      RE-SEQUENCED to run here as **2a, 2b, 2c**, before step 3. Numbering of
      every other step is untouched and the audit trail is intact. Nothing
      moves in or out of scope; the granted contact's four riders are carried
      verbatim onto the relocated steps, including rider (c) — the map's
      frozen-surface document still moves in the SAME commit as the
      `run_manifest.py` line.

- [x] 2a. (S13) [was step 19] Capture `proof/digest_before.txt` on the CURRENT
      tree: the six `source_config_hash` values (v1..v6) and the qualification
      subject digest, one command, output pasted into the file verbatim.
      Rider (b).
      done-when: `grep -c b9038b84efdea313 proof/digest_before.txt` is 1 AND
      `grep -c 2624603035bc335e proof/digest_before.txt` is 4

      PASTED OUTPUT:
      ```
      $ python experiments/.../digests.py > proof/digest_before.txt
      source_config_hash(Config()) by schema version:
        v1  6c2d01f6b8cbe65e2a26bb57e864a80feec07b0896142fb2267bc83d2717dc81
        v2  6c2d01f6b8cbe65e2a26bb57e864a80feec07b0896142fb2267bc83d2717dc81
        v3  2624603035bc335e59da63f25426d3ae6619bf7f84d48657e8f25310de49edc5
        v4  2624603035bc335e59da63f25426d3ae6619bf7f84d48657e8f25310de49edc5
        v5  2624603035bc335e59da63f25426d3ae6619bf7f84d48657e8f25310de49edc5
        v6  2624603035bc335e59da63f25426d3ae6619bf7f84d48657e8f25310de49edc5
      qualification_subject_digest(_manifest(_profile()), _profile()):
        b9038b84efdea313c3f3f2a8862d8acf180d3938ab3d1bf3588c3585dfe07386
      $ grep -c b9038b84efdea313 proof/digest_before.txt   ->  1
      $ grep -c 2624603035bc335e proof/digest_before.txt   ->  4
      ```
      Both values are byte-identical to the ones `DR-INV-frozen-surfaces`
      records for Rung 8 and to SPEC.md's M2/M3, measured independently here.

      The capture is a COMMITTED INSTRUMENT (`digests.py`) rather than a
      one-off shell line, for the reason the durable-evidence rule gives: a
      proof file whose command died with the session proves nothing a later
      reader can re-run. It resolves the repository root from its own path, so
      it works from any working directory.

- [ ] 2b. (S13) [was step 20] THE GRANTED CONTACT, all in ONE step because
      rider (c) requires the map to move in the SAME commit as the code: add
      `Config.DISCHARGE_POLICY: str = "off"` (SPEC A7 — the DEFAULT is F3's, so
      F1 ships it off); add `data.pop("DISCHARGE_POLICY", None)` to
      `run_manifest.py::_versioned_source_config_data` UNCONDITIONALLY, outside
      the `if schema_version < 3:` guard, per rider (d) and the
      `ENGAGED_CRITICISM_AUTHORITY` trap the operator named as its ancestor;
      and add the granted-contact block to `docs/map/INV-frozen-surfaces.md`
      with its own `check:`.
      done-when: ALL THREE pasted — (a) `python -c "from deepreason.config
      import Config; from deepreason.run_manifest import source_config_hash;
      h=[source_config_hash(Config(), schema_version=v) for v in
      (1,2,3,4,5,6)]; assert
      h[0]==h[1]=='6c2d01f6b8cbe65e2a26bb57e864a80feec07b0896142fb2267bc83d2717dc81';
      assert
      h[2]==h[3]==h[4]==h[5]=='2624603035bc335e59da63f25426d3ae6619bf7f84d48657e8f25310de49edc5'"`
      exits 0; (b) `test "$(grep -c 'data.pop("DISCHARGE_POLICY", None)'
      src/deepreason/run_manifest.py)" -eq 1` exits 0 AND the line is outside
      every `schema_version` guard (paste the surrounding 6 lines);
      (c) `python tools/docs_verify.py --fast` passes the new
      `INV-frozen-surfaces` check

- [ ] 2c. (S13) [was step 21] Capture `proof/digest_after.txt` with the SAME
      command as 2a and diff the pair. This is the acceptance check for the
      grant — not a green suite, the digest itself, at every schema version.
      done-when: `diff proof/digest_before.txt proof/digest_after.txt` prints
      nothing and exits 0 (paste the empty result and the exit code)

- [ ] 3. (S1) Create `src/deepreason/discharge/__init__.py` (the declared
      interface, re-exporting exactly the nine names SPEC S1 lists) and
      `policy.py` (`DischargeKindDeclaration`, `DISCHARGE_KIND_DECLARATIONS`
      with three entries, the DERIVED `KINDS` view, `DischargePolicyV1`,
      `DISCHARGE_POLICY_PRESETS`, `resolve_policy`, `policy_digest`).
      done-when: `python -c "from deepreason.discharge import resolve_policy,
      discharge_kind_names; from deepreason.discharge.policy import
      DISCHARGE_KIND_DECLARATIONS, KINDS; assert KINDS == {n: d.asserts for n,
      d in DISCHARGE_KIND_DECLARATIONS.items()}; assert
      set(discharge_kind_names()) ==
      {'revised','rebutted','departure_declared'}"` exits 0

- [ ] 4. (S2) Write `tests/test_discharge_channel.py`'s `open_criticisms`
      cases: an `observe_only` scrutiny criticism with NO warrant IS in the
      population (this is W2's own 0-of-196 population, so excluding it would
      leave the motivating defect in place); an attack-edge criticism IS; a
      REFUTED critic artifact is NOT; a discharged handle is NOT; the cap
      states itself in-band. RED now.
      done-when: `python -m pytest tests/test_discharge_channel.py -q -k
      open_criticisms 2>&1 | tail -5` shows failures naming
      `open_criticisms` (paste it)

- [ ] 5. (S2) Implement `src/deepreason/discharge/channel.py`:
      `OpenCriticism`, `open_criticisms`, `discharged_handles`. The handle IS
      the critic artifact id (SPEC A3). Reads BOTH channels — the
      `["scrutiny", target, critic]` Measures and `state.att` — over targets
      `t` with `(t, problem_id) in state.addr`.
      done-when: `python -m pytest tests/test_discharge_channel.py -q -k
      open_criticisms` ends `passed` with 0 failed (paste it)

- [ ] 6. (S3) Add the render cases to `tests/test_discharge_channel.py`: the
      section lands in the BINDING block (priority 2, after `criteria`, before
      `mandatory-interface`) and not among the advisory sections; an absent
      channel renders NOTHING rather than a "no criticisms" notice; and the
      persistence claim asserted AT THE TERMINAL cycle — eight cycles of
      accumulating ACCEPTED state, criticism injected at cycle 2, the claim
      made at cycle 8 under a budget measured to bite, modelled on
      `test_a_standing_attacker_at_cycle_k_still_renders_at_the_terminal_cycle`.
      RED now.
      done-when: `python -m pytest tests/test_discharge_channel.py -q -k
      "binding_block or terminal_cycle or renders_nothing" 2>&1 | tail -5`
      shows failures (paste it)

- [ ] 7. (S3) Implement the render: `channel.py::
      render_open_criticism_context`; `llm/packs.py` gains the
      `open_criticism_context` parameter and the `open-criticisms` section at
      priority 2, `droppable=False, compressible=False`; the
      `output-contract` section gains the discharge precondition sentence when
      the channel renders anything; `rules/conj.py` threads it beside the two
      frame values.
      done-when: `python -m pytest tests/test_discharge_channel.py -q` ends
      `passed` with 0 failed (paste it)

- [ ] 8. (S11) Move the map WITH the code, same commit: update
      `DR-CON-packs-and-token-economy` (the `len(j)==17` → `18` pin, and the
      new section's non-droppable/non-compressible row with its own check),
      `DR-CON-criticism-source` (where an open criticism now goes),
      `DR-CON-conjecture-source` (the submission precondition arriving in
      commit 2), `DR-SEAM-llm-x-rules` (the new parameter on the boundary),
      and `INDEX.md`'s concept table. Advance `Verified-at:` ONLY on documents
      whose checks were actually re-run.
      done-when: `python tools/docs_verify.py` (FULL) reports the SAME failure
      count as the tranche base (paste both numbers; the base is captured in
      this step's record before any edit)

- [ ] 9. (S8) Architecture-test checks 1, 2 and 4 green (check 3 needs the
      wire, and lands in commit 2).
      done-when: `python -m pytest tests/test_discharge_contract.py -q -k
      "interface_only or package_imports or pure_configuration"` ends `passed`
      with 0 failed (paste it)

- [ ] 10. (S1,S2,S3,S8,S11,S15) [COMMIT] Ring, budget, commit, push.
      done-when: ALL FOUR pasted — (a) `python -m pytest
      tests/test_discharge_channel.py "tests/test_discharge_contract.py::
      test_a_fourth_kind_enters_by_declaration_alone" --deselect
      tests/test_discharge_contract.py tests/test_frame_render.py
      tests/test_pack_prefix.py -q` — i.e. the whole ring EXCEPT
      `test_a_fourth_kind_enters_by_declaration_alone`, which reads the wire
      schema enum that lands at step 12 — → 0 failed. Corrected here rather
      than at step 10 (same ordering fault as step 2's record: the ring as
      first written demanded a commit-2 surface inside commit 1). Step 18 runs
      the file whole, with nothing deselected;
      (b) `python tools/diff_budget.py <base> --paths src/ --ceiling 640` →
      `DIFF_BUDGET_RESULT_V1` with `"verdict": "WITHIN"` (EXCEEDED is a typed
      STOP to the operator, never a re-baselined ceiling — R19);
      (c) commit created; (d) `git status --porcelain` empty and the branch
      head is on `origin`

---

## Commit 2 — wire, submission, discharge records (S4, S5, S6, S8, S11)

- [ ] 11. (S4) Write `tests/test_discharge_wire.py`: `DischargeWireV1` shape;
      the `kind` enum in the EMITTED schema derives from the registry; and the
      PRUNING claim across ALL THREE embedding contracts —
      `ConjecturerWireContract`, `AtomicConjectureWireContractV1` and the v6
      turn — because three committed tests read that `$def` directly
      (SPEC's census). RED now.
      done-when: `python -m pytest tests/test_discharge_wire.py -q 2>&1 |
      tail -5` shows failures naming `DischargeWireV1` (paste it)

- [ ] 12. (S4) Implement `DischargeWireV1` in `llm/wire.py`;
      `CompactConjectureCandidate.discharges` (list, max_length=32) and
      `ReasoningCandidateProposal.discharges` (tuple) in
      `workloads/text.py` — both additive and optional, the precedent
      `checker_specs`'s own comment names; prune via `wire.prune_property`
      wherever the channel renders nothing.
      done-when: BOTH pasted — (a) `python -m pytest
      tests/test_discharge_wire.py -q` → 0 failed; (b) `python -c "from
      tests.test_reusable_qualification import _manifest, _profile; from
      deepreason.qualification import qualification_subject_digest; p=_profile();
      assert qualification_subject_digest(_manifest(p), p) ==
      'b9038b84efdea313c3f3f2a8862d8acf180d3938ab3d1bf3588c3585dfe07386'"`
      exits 0

- [ ] 13. (S5) Write `tests/test_discharge_submission.py`: an undischarged
      submission is re-asked ONCE with the open list; the SECOND submission is
      ACCEPTED with a typed undischarged-disclosure Measure and NOT re-asked
      again; no candidate is ever refused for an undischarged handle; the
      re-ask consumes no repair budget and touches no repair contract; and
      R11's structural guard — no acknowledgment-shaped name anywhere in the
      package, and no kind whose `requires` is empty. RED now.
      done-when: `python -m pytest tests/test_discharge_submission.py -q 2>&1
      | tail -5` shows failures naming `screen_submission` (paste it)

- [ ] 14. (S5) Implement `src/deepreason/discharge/submission.py::
      screen_submission` and wire it into `rules/conj.py` immediately after
      `output` is parsed and BEFORE `candidate_rows` is built; the re-ask
      re-enters `conj(..., _discharge_reask_index=1, ...)` on the existing
      `_context_expansion_index` recursion shape — NO new `adapter.call` site.
      done-when: BOTH pasted — (a) `python -m pytest
      tests/test_discharge_submission.py -q` → 0 failed; (b) `test "$(cat
      src/deepreason/rules/conj.py src/deepreason/rules/crit.py | grep -c
      'adapter\.call(')" -eq 8 && test "$(grep -rl "deepreason\.llm"
      --include=*.py src/deepreason/rules | wc -l)" -eq 8` exits 0 (the two
      pinned counts this plan promised not to disturb)

- [ ] 15. (S6) Implement `record_discharges`: one Measure per accepted
      discharge (`["discharge:<kind>", handle, candidate_ref, problem_id]`),
      and for `rebutted` ONLY, register the rebuttal as an ordinary artifact
      with TWO `MENTION` refs and no dependence and no warrant — mirroring
      `calculus/operations.py::file_departure_declaration`, including its
      refusal to judge whether the rebuttal is earned.
      done-when: `python -m pytest tests/test_discharge_submission.py -q -k
      "rebuttal_is_itself_attackable or rebuttal_moves_no_existing_label"`
      ends `passed` with 0 failed (paste it)

- [ ] 16. (S8) Architecture-test check 3 — a fourth kind enters by
      DECLARATION: a synthetic kind reaches the wire schema enum, the
      screening and the pack render with `rules/conj.py`, `llm/packs.py` and
      `llm/wire.py` UNEDITED, and none of those three files contains the
      literal `"revised"`, `"rebutted"` or `"departure_declared"`. Then prove
      the check CAN fail: hard-code the kind tuple in a scratch copy outside
      the repo, capture RED to `proof/arch_red.txt`, restore.
      done-when: BOTH pasted — (a) `python -m pytest
      tests/test_discharge_contract.py -q` → 0 failed; (b)
      `grep -c FAILED proof/arch_red.txt` >= 1 AND
      `git status --porcelain src/` is empty

- [ ] 17. (S11) Move the map with the code: `DR-CON-discharge-channel`'s
      remaining checks now pass; `DR-CON-conjecture-source` gains the
      submission precondition; `DR-SEAM-llm-x-rules` re-verified against its
      own two counts.
      done-when: `python tools/docs_verify.py` (FULL) failure count equals the
      base captured at step 8 (paste both)

- [ ] 18. (S4,S5,S6,S8,S11,S15) [COMMIT] Ring, budget, commit, push.
      done-when: ALL FOUR pasted — (a) `python -m pytest
      tests/test_discharge_wire.py tests/test_discharge_submission.py
      tests/test_discharge_contract.py tests/test_wire_contracts.py
      tests/test_v6_patch_repair_and_wire.py tests/test_conjecturer_turn_v4.py
      tests/test_skills_models.py -q` → 0 failed; (b) `diff_budget` verdict
      `WITHIN` against 640; (c) commit created; (d) `git status --porcelain`
      empty and head on `origin`

---

## Commit 3 — the granted contact, the law line, the coupling proof, the gate

- [~] 19. (S13) **RE-SEQUENCED TO STEP 2a** (see step 2's record: two
      architecture checks depend on `Config.DISCHARGE_POLICY`, so the field
      cannot land after them). Original text kept for the audit trail.
      ~~Capture `proof/digest_before.txt`~~ on the CURRENT tree: the six
      `source_config_hash` values (v1..v6) and the qualification subject
      digest, one command, output pasted into the file verbatim. Rider (b).
      done-when: `grep -c b9038b84efdea313 proof/digest_before.txt` is 1 AND
      `grep -c 2624603035bc335e proof/digest_before.txt` is 4

- [~] 20. (S13) **RE-SEQUENCED TO STEP 2b.** Original text kept for the
      audit trail. ~~THE GRANTED CONTACT~~, all in ONE step because rider (c) says
      the map moves in the SAME commit as the code: add
      `Config.DISCHARGE_POLICY: str = "off"` (SPEC A7 — the DEFAULT is F3's,
      so F1 ships it off); add `data.pop("DISCHARGE_POLICY", None)` to
      `run_manifest.py::_versioned_source_config_data` UNCONDITIONALLY,
      outside the `if schema_version < 3:` guard, per rider (d) and the
      `ENGAGED_CRITICISM_AUTHORITY` trap the operator named as its ancestor;
      and add the granted-contact block to
      `docs/map/INV-frozen-surfaces.md` with its own `check:`.
      done-when: ALL THREE pasted — (a) `python -c "from deepreason.config
      import Config; from deepreason.run_manifest import source_config_hash;
      h=[source_config_hash(Config(), schema_version=v) for v in
      (1,2,3,4,5,6)]; assert
      h[0]==h[1]=='6c2d01f6b8cbe65e2a26bb57e864a80feec07b0896142fb2267bc83d2717dc81';
      assert
      h[2]==h[3]==h[4]==h[5]=='2624603035bc335e59da63f25426d3ae6619bf7f84d48657e8f25310de49edc5'"`
      exits 0; (b) `test "$(grep -c 'data.pop(\"DISCHARGE_POLICY\", None)'
      src/deepreason/run_manifest.py)" -eq 1` exits 0 AND the line is outside
      every `schema_version` guard (paste the surrounding 6 lines);
      (c) `python tools/docs_verify.py --fast` passes the new
      `INV-frozen-surfaces` check

- [~] 21. (S13) **RE-SEQUENCED TO STEP 2c.** Original text kept for the
      audit trail. ~~Capture `proof/digest_after.txt`~~ with the SAME command as step
      19 and diff the pair. This is the acceptance check for the grant — not a
      green suite, the digest itself, at every schema version.
      done-when: `diff proof/digest_before.txt proof/digest_after.txt` prints
      nothing and exits 0 (paste the empty result and the exit code)

- [ ] 22. (S7) Write `tests/test_discharge_law_line.py` pins 1–3: the ABSENCE
      pin over `scheduler/`, `adjudication/`, `informal/` and `rules/` except
      `rules/conj.py`, EVERY negative grep paired with a positive anchor on
      the same tree; `DischargeKindDeclaration` has no numeric field at all;
      and admission is byte-identical with and without discharges on the same
      candidate.
      done-when: `python -m pytest tests/test_discharge_law_line.py -q -k
      "not no_label_differs"` ends `passed` with 0 failed (paste it)

- [ ] 23. (S7) THE MUTATION PROOF (R7). In a scratch copy OUTSIDE the repo,
      wire a discharge into label computation in `adjudication/`; run
      `tests/test_discharge_law_line.py` against it; capture RED to
      `proof/c3_red.txt`; restore; capture GREEN to `proof/c3_green.txt`.
      Clear `__pycache__` before measuring — stale bytecode survives a revert
      (`DR-SCHEMA`'s own measurement rule).
      done-when: `grep -c FAILED proof/c3_red.txt` >= 1 AND
      `grep -c "0 failed\| passed" proof/c3_green.txt` >= 1 AND
      `git status --porcelain src/` is empty

- [ ] 24. (S9) Write `coupling.py` and run it: two offline stub-driven roots,
      identical but for `Config.DISCHARGE_POLICY`, each with a criticism whose
      warrant names a mechanical respect and a RESPONSIVE stub writer. Run
      W2's committed `census.py` and `q5.py` UNMODIFIED over both; if either
      cannot run on a stub root for want of a record field the stub path does
      not write, record that as a measured limit IN `coupling.json` and
      reproduce R1 directly from `q5.py` lines 20–24, citing them.
      done-when: `python coupling.py coupling.json` exits 0 AND `python -c
      "import json; d=json.load(open('coupling.json')); assert
      d['on']['R1_mechanical']['coupling_minus_placebo'] > 0; assert
      d['off']['R1_mechanical']['coupling_minus_placebo'] == 0"` exits 0
      (paste both rates)

- [ ] 25. (S10) Add the `no_label_differs` case to
      `tests/test_discharge_law_line.py`: replay both step-24 roots and
      compare final labels over the artifact set present in BOTH; the
      channel-on root's extra rebuttal artifacts and discharge Measures are
      the DELTA and are listed, never hidden.
      done-when: `python -m pytest tests/test_discharge_law_line.py -q` ends
      `passed` with 0 failed (paste it)

- [ ] 26. (S14) Record the F2 composition note in
      `docs/map/CON-discharge-channel.md`, verbatim from SPEC S14, so F2's
      window or a successor finds it (R18).
      done-when: `grep -q "reference-bearing"
      docs/map/CON-discharge-channel.md && grep -q "open_criticisms"
      docs/map/CON-discharge-channel.md && python -c "from
      deepreason.llm.wire import DischargeWireV1; assert
      DischargeWireV1.model_fields['handle'].annotation is str"` exits 0

- [ ] 27. (S11) Map gate, FULL — never concurrently with the test gate
      (`dr-drive-harness` §5b: both fan out workers and the contention
      manufactures failures).
      done-when: ALL THREE pasted — `python tools/docs_verify.py` failure
      count equals the base from step 8; `python tools/docs_verify.py --audit`
      refuses none of this tranche's new checks; `python tools/docs_verify.py
      --links` exits 0

- [ ] 28. (all) Wheel smokes — no gate runs them, so a public-surface change
      would rot the pins silently. No console entry point, MCP tool or wheel
      layout is planned to move; these run as proof rather than assurance.
      done-when: `python scripts/wheel_smoke.py` and `python -u
      scripts/wheel_operational_smoke.py` both PASS with pins unchanged, AND
      `git diff -- scripts/` is empty (paste all three)

- [ ] 29. (all) FULL GATE, on an otherwise idle box.
      done-when: `python -m pytest tests/ -q -n 4` output ends
      `N passed, 0 failed` (paste the line; 0 failed is the only acceptable
      result, and no assertion is weakened to reach it)

- [ ] 30. (S15) Final diff budget against the declared ceiling.
      done-when: `python tools/diff_budget.py <base> --paths src/ --ceiling
      640` prints `DIFF_BUDGET_RESULT_V1` with `"verdict": "WITHIN"` (paste
      it). EXCEEDED is a typed STOP to the operator naming what grew — never a
      silent overrun and never a re-baselined ceiling (R19).

- [ ] 31. (S16) Write `RESULTS.md` as a dated honest-ledger segment, with the
      claim boundary the operator fixed in advance: F1 claims DELIVERY, not
      RESPONSE; the live four-arm A/B stays PARKED as P2; P-C2's rematch bears
      on it but does not replace P2's design.
      done-when: `RESULTS.md` contains a `## What this does NOT establish`
      section carrying all four points AND
      `! grep -qi "a live model responded\|the model responded to the channel"
      RESULTS.md` exits 0

- [ ] 32. (all) [COMMIT] Push and confirm clean.
      done-when: `git status --porcelain` is empty AND `git log --oneline -1`
      equals `git log --oneline -1
      origin/claude/rebuild-discharge-criticism-channel-2b8z8i` (paste both)

---

## Coverage

Every SPEC item reaches at least one step: S1→3,9,10; S2→4,5; S3→6,7;
S4→11,12; S5→13,14; S6→15; S7→22,23; S8→2,9,16; S9→24; S10→25;
S11→1,8,17,27; S12→28,29; S13→2a,2b,2c (re-sequenced from 19,20,21);
S14→26; S15→10,18,30; S16→31.
Every step carries an S-number; no step lacks a done-criterion.
