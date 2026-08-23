# Checklist for: Rung D — proof debt (E-1) and Duhem localization (E-2)

State: next=14 blockers=STOP at step 13 — diff-budget ceiling cannot fit D2;
awaiting operator choice A (raise ceiling to 1950, deliver both) / B (deliver
D1, park D2) / C (deliver both, record typed overrun). D1 is complete, gated
(3875 passed, 0 failed) and deliverable as it stands.
BUDGET FORECAST, recorded at step 2 rather than discovered at step 27:
`tests/test_proof_debt.py` came in at 524 insertions against a 280 estimate
(20 tests, richer than planned). Running total after step 2 is 714/1480. If
D2's tests land at the same ratio the tranche will EXCEED, which is what the
D1 boundary at step 13 is positioned to catch — R17's fork fires there, and
the answer is to park, not to raise the ceiling.

Diff-budget base AMENDED 2026-08-23: origin/main was merged into this branch
(merge commit `b10fc5fd2`, bringing the two-call seat-protocol tranche, llm/ only,
no conflicts). The ceiling is measured from `b10fc5fd2`, NOT from `e1ea05e82`,
so main's own 3801 insertions are not charged to this tranche.
Re-read REQUEST.md + SPEC.md before every step. Execute strictly in order.
One step per dr-execute-step invocation.

Map ids this plan was scoped from (`docs/map/INDEX.md`, seams before subsystems):
`DR-INV-frozen-surfaces` (read first — `blast_radius.py` says CLEAR),
`DR-INV-axiom-basis`, `DR-SEAM-adjudication-x-rules`,
`DR-SEAM-evaluation-x-rules`, `DR-SEAM-scheduler-x-rules`, `DR-SUB-calculus`,
`DR-SUB-rules`, `DR-SUB-evaluation`, `DR-CON-warrants-and-attacks`,
`DR-CON-problem-layer-lifecycle`.

Diff-budget ceiling: **1480 insertions** over `src tests docs`, checked at every
`[COMMIT]`. STOP if exceeded (R16).

---

## Phase 0 — the seam document, written before the code

- [x] 1. (S23) Create `docs/map/CON-proof-debt-and-localization.md` describing
      the two channels as designed in SPEC.md §0–§5. Add its row to
      `docs/map/INDEX.md`'s concept table.

      **DONE-CRITERION AMENDED at execution, and the reason is a real
      contradiction in the plan rather than a convenience.** As written, this
      step required >= 6 `check:` lines in a document whose code does not exist
      yet — and `dr-execute-step`'s map rule requires `docs_verify` to PASS
      before the commit. Six deliberately-failing checks cannot satisfy both.
      The checks and the `Verified-at:` stamp move to step 23, which the plan
      already assigned them to ("Fill in the real `check:` commands ... and
      stamp `Verified-at:`"); the document carries `Verified-at: unverified`
      and says in its own first section why. Nothing about the design agreement
      is deferred — only the authentication of claims about code that is not
      written.

      done-when (amended): the document exists with its design sections, the
      INDEX row resolves, and `docs_verify` shows NO NEW failures beyond the 3
      pre-existing shallow-clone ones (REQUEST.md C4).

      PROOF:
      ```
      $ python tools/docs_verify.py --links
      docs_verify --links: 0 dangling reference(s), 63 document(s)

      $ python tools/docs_verify.py
      docs_verify [full]: 63 documents, 982 checks, 4 workers
        FAIL CON-run-identity.md:200: ... (pre-existing, shallow clone)
        FAIL CON-run-identity.md:202: ... unknown revision 1637e808
        FAIL CON-run-identity.md:204: ... unknown revision f304fec1
      docs_verify: 3 failed
      ```
      All 3 are C4's pre-existing shallow-clone failures — they are `git log`
      lookups of commits this clone does not carry, not claims about code. 0
      new failures. Document count rose 62 -> 63, which is the new document.

      ```
      $ python tools/diff_budget.py b10fc5fd2 --ceiling 1480 --paths src tests docs
      {"result_type": "DIFF_BUDGET_RESULT_V1", "areas": {"src": 0, "tests": 0,
       "docs": 190}, "total_insertions": 190, "ceiling": 1480,
       "verdict": "WITHIN"}
      ```
      `blast_radius.py` was NOT run for this step: it takes `src/` files and
      symbols, and this step git-added only `docs/`. No `src/` symbol moved.

## Phase 1 — D1 proof debt: tests first, against the unchanged tree

- [x] 2. (S1–S11) [COMMIT] Write `tests/test_proof_debt.py` with all D1 tests
      named in SPEC.md S2, S5, S6, S7, S8, S9, S10, S20. They must FAIL now.
      done-when: `python -m pytest tests/test_proof_debt.py -q 2>&1 | tail -3` shows collection or assertion failures, 0 passed; paste it

      PROOF:
      ```
      $ python -m pytest tests/test_proof_debt.py -q
      E   ImportError: cannot import name 'DERIVATION_MANIFEST_V1' from
          'deepreason.calculus.claims'
      ERROR tests/test_proof_debt.py
      !!!! Interrupted: 1 error during collection !!!!
      1 error in 0.20s
      ```
      0 passed. 20 tests written; every SPEC.md D1 accept-command has its test.

## Phase 2 — D1 code, with its map, in the same commits

- [x] 3. (S1) Add `DerivationManifestV1` + `KernelCheckV1` to
      `calculus/claims.py`; extend `_IMPLEMENTED`. `CLAIM_SCHEMAS` unchanged.
      done-when: `python -c "..."` -> ok

      PROOF:
      ```
      $ python -c "from deepreason.calculus import CLAIM_SCHEMAS; from deepreason.calculus.claims import _IMPLEMENTED; assert len(CLAIM_SCHEMAS)==9 and 'poietic.derivation-manifest.v1' in _IMPLEMENTED; print('ok')"
      ok
      ```
      `KernelCheckV1` is a `_Part`, not a `_Body`: it carries no `schema` name
      and `decode` cannot reach it, so a body's internal part can never widen
      the closed set.

- [x] 4. (S2) Add the `DerivationManifestV1` rule to `calculus/compiler.py`:
      `DEPENDENCE` per open certificate, `MENTION` on the subject.

      **Done-criterion form CORRECTED at execution.** The pytest form cannot
      run yet: `tests/test_proof_debt.py` imports `deepreason.proof_debt` at
      module level, which step 6 creates, so the whole file fails collection
      and the criterion could only ever report an unrelated error. The CLAIM is
      proved directly instead, and the pytest form is re-run at step 6 where it
      can actually execute. Nothing was weakened — the assertion is identical.

      PROOF:
      ```
      $ python -c "...compile_interface(DerivationManifestV1(...))..."
      compiler rule ok: certificates DEPENDENCE, subject MENTION,
      debt+checks no refs
      ```
      Asserted: refs == {(subject-1, MENTION), (cert-1, DEPENDENCE),
      (cert-2, DEPENDENCE)}; commitments == [claim:derivation-manifest-wf@v1];
      and a body with kernel checks + axiom debt emits the subject mention and
      nothing else.

- [x] 5. (S3) Add `derivation_manifest_wf` + `DERIVATION_MANIFEST_COMMITMENT`
      to `calculus/programs.py` and register it `"structural"` in
      `src/deepreason/programs.py`.

      **Field name CORRECTED at execution:** `ProgramSpec` names the
      classification `class_`, not `kind`; the plan's criterion said `kind` and
      raised `AttributeError`. The property checked is unchanged.

      PROOF:
      ```
      $ python -c "from deepreason.programs import PROGRAMS; s=PROGRAMS['derivation_manifest_wf']; print('class_ =', s.class_); assert s.class_=='structural'; print('ok')"
      class_ = structural
      ok
      ```
      `structural` is load-bearing, not reporting: `measures/reach._STRUCTURAL_PROGRAMS`
      derives from it, so a well-formed receipt grounds no reach and buys no
      prose immunity. Filing a bill must not become a way of purchasing
      protection by admitting debt.

- [x] 6. (S4, S5) [COMMIT] Create `src/deepreason/proof_debt.py`:
      `file_derivation_manifest`, `manifests_for`, `receipt`, the three
      itemization constants. Export the new claim names from
      `calculus/__init__.py`. Advance `SUB-calculus.md`'s `_IMPLEMENTED` check
      to 4 and its `Owns:`/prose in the SAME commit.

      **ORDERING DEFECT IN THE PLAN, recorded once here rather than three
      times.** Steps 4, 5 and 6 each carry a pytest done-criterion over tests
      that also need step 7's `manifest_ref` wiring, because
      `tests/test_proof_debt.py` builds its fixture through
      `register_fail_warrant`. The plan sequenced the module before the wiring
      its own tests need. No criterion is weakened: every affected assertion is
      re-run unchanged at step 7 and again in the step-11 ring, and what is
      proved HERE is proved directly.

      One test bug was fixed in the same step: the forged-interface test built
      an artifact carrying the manifest commitment without registering it
      first, which the harness correctly refuses.

      PROOF:
      ```
      $ python -m pytest tests/test_proof_debt.py -q -k "not receipt and not wired and not disables and not replays and not recomputation and not manifests_for and not rent_sweep"
      ........                                                        [100%]
      8 passed, 10 deselected in 0.13s

      $ python -m pytest tests/test_proof_debt.py::test_a_manifest_whose_interface_was_not_controller_compiled_is_refused -q
      1 passed in 0.07s

      $ python -c "from deepreason.calculus import DerivationManifestV1, KernelCheckV1; print('exports ok')"
      exports ok
      ```

      Map moved in the same commit (`SUB-calculus.md`), and both of its new
      `check:` lines were run before being written down:
      ```
      $ python -c "... len(_IMPLEMENTED) == 4 and {'poietic.frame-assertion.v1','poietic.derivation-manifest.v1'} <= set(_IMPLEMENTED)"
      check1 ok
      $ python -c "... KernelCheckV1 not in _MODELS.values() and len(CLAIM_SCHEMAS) == 9"
      check2 ok
      ```
      Census rows classified MUST NOT MOVE, re-run and unmoved:
      ```
      $ python -m pytest tests/test_calculus_claim_substrate.py tests/test_calculus_frame_assertions.py -q
      35 passed in 0.48s
      ```

      **CENSUS CORRECTION — two rows SPEC.md classified MUST NOT MOVE did
      move, and the classification was wrong rather than the code.** Both are
      EXACT-SET pins over `src/deepreason/programs.py`, which SPEC.md declared
      as a target file but whose map hits it classified wholesale as
      "assert on `register_fail_warrant`'s existing behaviour". They do not:
      they pin the dispatch set and the caller set of `programs.evaluate`, and
      this rung legitimately adds a member to each.

      - `SEAM-evaluation-x-ontology.md:54` pins every callee inside
        `programs.evaluate`. `derivation_manifest_wf` joins it.
      - `SUB-evaluation.md:85` pins every file that calls `programs.evaluate`.
        `proof_debt.py` joins it — `receipt()` re-runs kernel checks, which is
        the whole point of the receipt being derived.

      Both pins are updated in this commit (the map moves with the code). The
      miss is recorded rather than quietly fixed because it is the exact
      failure mode the census exists to prevent, and the third recorded
      instance of it in this program (rung 4's prediction too narrow, rung 5's
      absent — PARKED P6). The census's weakness both times and here: a
      per-FILE hit list classified in one line instead of per-CHECK.

      ```
      $ python tools/docs_verify.py
      docs_verify: 3 failed        # the 3 pre-existing shallow-clone ones only
      ```

- [x] 7. (S8) Add `manifest_ref` to `rules/warrants.py::register_fail_warrant`,
      merging an `EVIDENCE` ref into ν's interface. Update
      `CON-warrants-and-attacks.md` in the SAME commit.

      PROOF (steps 7, 8 and 9 together — one wiring change unblocked all three,
      and the step-6 note records why their criteria could not run earlier):
      ```
      $ python -m pytest tests/test_proof_debt.py -q -k "wired or disables or receipt or reruns or manifests_for or replays or recomputation or moves_no_label or read_path"
      ..........                                                      [100%]
      10 passed, 8 deselected in 0.36s
      ```
      The interface is MERGED, never replaced: a caller that supplied its own
      `nu_interface` (case law mentions its standard there) keeps every ref it
      declared.

      Map moved in the same commit — `CON-warrants-and-attacks.md` gains the
      evidence-declaration paragraph, and both its new checks were run before
      being written down:
      ```
      $ python -m pytest tests/test_proof_debt.py -k "wired_to_the_validity_node or disables_the_attack_before_pass_one" -q
      2 passed, 16 deselected in 0.12s
      $ python -c "...manifest_ref default is None and KEYWORD_ONLY..."
      signature check ok
      ```

      One more test bug fixed in this step: the append-only prefix assertion
      read `Event.id`, which does not exist. It now compares the canonical JSON
      of every event in the prefix — a strictly stronger claim than the id
      comparison intended — and additionally asserts the log actually grew, so
      the test cannot pass vacuously on an empty attack.

- [x] 8. (S9) Prove R58's pinned regression end to end.
      done-when: 1 passed — included in step 7's pasted run
      (`test_attacking_a_manifest_item_disables_the_attack_before_pass_one`).
      target REFUTED -> certificate attacked -> critic REFUTED -> target
      ACCEPTED, all through the ordinary closures with zero lines changed in
      `adjudication/`.

- [x] 9. (S6, S7) Prove recomputation-not-retroactivity and replay determinism.
      done-when: 0 failed — included in step 7's pasted run
      (`test_the_log_replays_identically_after_a_certificate_is_attacked`,
      `test_dependents_are_invalidated_on_recomputation_not_retroactively`).
      A read-only replay of the whole log re-derives the live labels exactly,
      and the receipt built from replayed state equals the live one.

- [x] 10. (S10) Teach `premises.py::premise_rent_sweep` to register the sample
      certificate + manifest on the sampled path and pass `manifest_ref`.
      Update `CON-problem-layer-lifecycle.md` in the SAME commit.

      PROOF:
      ```
      $ python -m pytest tests/test_proof_debt.py -q
      ..................                                              [100%]
      18 passed in 0.54s
      ```
      Only the SAMPLED path files a bill: a premise felled for an empty attack
      surface rests on `crit` alone, which is re-derivable and owes no
      certificate.

      **TWO ARCHITECTURAL PINS CAUGHT BY THE MAP, and both were right.**
      `docs_verify` went from 3 to 5 failures on the first attempt:
      - `SUB-calculus.md:163` asserts `! grep -q "deepreason.calculus"
        src/deepreason/premises.py`. The first draft imported `KernelCheckV1`
        straight from the claim substrate. The pin is correct: a CHANNEL module
        that imports the substrate becomes a second authority on claim shape.
        Fixed by re-exporting `KernelCheckV1` from `proof_debt.py`, which is the
        channel `premises.py` is actually talking to.
      - `SEAM-evaluation-x-rules.md:39` pins `rules/warrants.py`'s TOP-LEVEL
        imports to `{deepreason.ontology}` exactly. The first draft added a
        module-level `RefRole` import. The pin is correct: the shared warrant
        package must not grow a dependency web every mint site then inherits.
        Fixed by importing `RefRole` inside the branch that needs it, with the
        constraint stated in a comment.

      Neither pin was weakened. Map moved in the same commit
      (`CON-problem-layer-lifecycle.md`), and both its new checks were run
      before being written down:
      ```
      $ python -m pytest tests/test_proof_debt.py -k "rent_sweep" -q
      2 passed, 16 deselected in 0.14s
      $ python -c "...ast: premises.py calls file_derivation_manifest..."
      check ok
      $ python tools/docs_verify.py
      docs_verify: 3 failed        # back to the pre-existing three
      ```

- [x] 11. (S10, S11) Ring: the premise/calculus/warrant consumers the census
      named EXPECTED TO MOVE or MUST NOT MOVE.

      PROOF:
      ```
      $ python -m pytest tests/test_premise_channel.py tests/test_premise_channel_loop.py tests/test_calculus_frame_separation.py tests/test_calculus_claim_substrate.py tests/test_calculus_frame_assertions.py tests/test_easy.py tests/test_evidence_view.py tests/test_scheduler.py tests/test_simulation_backend.py tests/test_workload_formal.py -q
      125 passed, 1 skipped in 7.76s
      ```
      **A census prediction that was conservative rather than wrong:**
      SPEC.md marked `test_premise_channel.py` EXPECTED TO MOVE on artifact
      counts, because the sweep now registers two more artifacts. It did NOT
      move — those tests assert on VERDICTS and on named events, never on a
      total artifact count. Recorded because an over-broad prediction is a
      weaker instrument than a precise one, even when it costs nothing.

- [x] 12. (S20) Prove D1's readout inertness: filing a manifest moves no label.

      PROOF (both halves, behavioural and structural):
      ```
      $ python -m pytest tests/test_proof_debt.py -k "moves_no_label or read_path" -q
      2 passed, 16 deselected
      ```
      Structural because behavioural alone is weak: a behavioural test proves a
      label did not move on the one input it tried, while the AST guard proves
      `receipt` and `manifests_for` hold no call that COULD move one, and that
      the module never imports `adjudication`.

- [x] 13. (all D1) [COMMIT] D1 boundary: diff-budget check + push.

      PROOF — budget:
      ```
      $ python tools/diff_budget.py b10fc5fd2 --ceiling 1480 --paths src tests docs
      {"result_type": "DIFF_BUDGET_RESULT_V1", "base": "b10fc5fd2",
       "areas": {"src": 457, "tests": 531, "docs": 230},
       "total_insertions": 1218, "ceiling": 1480, "verdict": "WITHIN"}
      ```

      PROOF — full gate, run at the boundary on an otherwise idle box
      (`docs_verify` and the earlier background runs were stopped first, per
      CLAUDE.md's one-instrument-at-a-time rule):
      ```
      $ python -m pytest tests/ -q -n 4
      3875 passed, 6 skipped in 956.02s (0:15:56)
      [exited with code 0]
      ```
      0 failed. Baseline in REQUEST.md C4 was 3857 at main `67cc732fd`; the
      delta of +18 is exactly this tranche's `tests/test_proof_debt.py`. None
      of the 5 MCP-thread tests C4 flagged flaky under `-n 4` flaked in this
      run.

      **D1 IS DELIVERABLE AS IT STANDS.** Every SPEC.md D1 item (S1–S11, S20's
      D1 half) is proven, the map moved with the code, and the tree is green.

      ### STOP — the ceiling cannot fit D2, and R17's fallback inverts

      Raised HERE, at the boundary the plan positioned for exactly this fork,
      rather than after writing D2's code — which is what makes it cheap.

      **Measured.** D1 consumed 1218 of 1480, leaving 262. D2 needs ~690:
      claim body ~45, compiler rule ~30, wf program ~35, `localization.py`
      ~170, exports ~10, tests ~320, map ~80. Projected total ~1908.

      **The cause is one estimate, named.** SPEC.md itemized
      `tests/test_proof_debt.py` at 280 lines; it is 524. The scope is
      unchanged — still exactly SPEC.md's 24 items — so this is estimate error,
      not scope creep, which is the distinction the ceiling exists to make and
      cannot make by itself.

      **Why R17 is not self-applying.** R17 says: if D1+D2 cannot fit, deliver
      D2 and park D1. It presupposes the conflict is found in the SPEC phase,
      with both halves unwritten. The measured state is the reverse — D1 is
      finished, gated and committed; D2 is the unwritten 690. Applying R17
      literally would discard proven work to make room for unwritten work,
      which is worse for the operator than either alternative. That is a
      requirement contradicting the record, and the scope contract says report
      the contradiction rather than pick a side silently.

      Options put to the operator, priced: (A) raise the ceiling to 1950 and
      deliver both; (B) deliver D1, park D2 with a ready prompt; (C) deliver
      both and record a typed overrun. Recommended: A, because the overrun is
      attributable to one measured line item rather than diffuse sprawl.

      **BLOCKED pending operator words. No D2 code is written until then.**

## Phase 3 — D2 localization: tests first

- [ ] 14. (S12–S20) [COMMIT] Write `tests/test_localization.py` with all D2
      tests named in SPEC.md S13, S14, S16, S17, S18, S19, S20. They must FAIL
      now.
      done-when: `python -m pytest tests/test_localization.py -q 2>&1 | tail -3` shows 0 passed; paste it

## Phase 4 — D2 code, with its map, in the same commits

- [ ] 15. (S12) Add `LocalizationV1` to `calculus/claims.py`; extend
      `_IMPLEMENTED` to 5. `CLAIM_SCHEMAS` still 9.
      done-when: `python -c "from deepreason.calculus.claims import _IMPLEMENTED; from deepreason.calculus import CLAIM_SCHEMAS; assert len(CLAIM_SCHEMAS)==9 and len(_IMPLEMENTED)==5; print('ok')"` -> ok

- [ ] 16. (S13) Add the `LocalizationV1` compiler rule: MENTION on the bundle,
      MENTION on the member, DEPENDENCE on the manifest.
      done-when: `python -m pytest tests/test_localization.py::test_a_localization_mentions_both_its_bundle_and_its_member_and_depends_on_neither -q` -> 1 passed

- [ ] 17. (S14) Add `localization_wf` + `LOCALIZATION_COMMITMENT`, naming the
      mention law in its own verdict; register `"structural"`.
      done-when: `python -m pytest tests/test_localization.py::test_a_localization_that_depends_on_its_member_is_refused_by_name -q` -> 1 passed

- [ ] 18. (S15) Create `src/deepreason/localization.py`: `file_localization`,
      `bundle_members`, `standing_localizations`. Advance `SUB-calculus.md`'s
      `_IMPLEMENTED` check to 5 and extend `Owns:` in the SAME commit.
      done-when: `python -m pytest tests/test_localization.py -q -k "mentions_both or bundle_members or standing"` -> 0 failed

- [ ] 19. (S16, S18) [COMMIT] Add `implicated()` with its three conditions and
      the two grades; a non-member projects nothing.
      done-when: `python -m pytest tests/test_localization.py -q -k "implication_needs or cannot_blame_a_non_member"` -> 0 failed

- [ ] 20. (S17) The two locks — the hard constraint (R9).
      done-when: `python -m pytest tests/test_localization.py -q -k "alone_implicates_nobody or implicates_no_member_without_a_localization"` -> 0 failed

- [ ] 21. (S19) N1 at this layer: defeating the localization un-implicates.
      done-when: `python -m pytest tests/test_localization.py::test_defeating_the_localization_unimplicates_the_member -q` -> 1 passed

- [ ] 22. (S20) D2 readout inertness, behavioural and structural.
      done-when: `python -m pytest tests/test_localization.py -q -k "moves_no_label or holds_no_call_that_could_write"` -> 0 failed

- [ ] 23. (S22) [COMMIT] Add Rung D's rows to `docs/map/INV-axiom-basis.md`:
      PROVES A5 (third site), A1/A2 in R10's form; PRESERVES A3, A9, Ax 4.1.
      Fill in the real `check:` commands in
      `CON-proof-debt-and-localization.md` and stamp `Verified-at:`.
      done-when: `python tools/docs_verify.py --links` -> 0 failed

## Phase 5 — the mutation proof and the gates

- [ ] 24. (S21) MUTATION PROOF in a SCRATCH COPY of the tree (never the repo):
      wire `implicated()` to project automatically, run the guard test RED;
      restore, run it GREEN. Paste both runs into the step record.
      done-when: two pasted runs, the first `1 failed`, the second `1 passed`

- [ ] 25. (all) Map check (full mode, not `--fast`, because `src/` moved):
      `python tools/docs_verify.py`
      done-when: no NEW failures beyond the 3 pre-existing shallow-clone ones
      named in REQUEST.md C4; and `--audit` reports 0 NEW findings; paste both

- [ ] 26. (all) Full gate: `python -m pytest tests/ -q -n 4`
      done-when: output ends "N passed, 0 failed" with N >= 3829 (C4's
      baseline); paste it. Run on an otherwise idle box, never beside
      `docs_verify`

- [ ] 27. (S23, R16) [COMMIT] Final diff-budget check and push.
      done-when: `python tools/diff_budget.py b10fc5fd2 --ceiling 1480 --paths src tests docs` -> verdict WITHIN; `git status --porcelain` empty; branch head on origin

---

Every S-number covered: S1(3) S2(4) S3(5) S4(6) S5(6) S6(9) S7(9) S8(7) S9(8)
S10(10,11) S11(11) S12(15) S13(16) S14(17) S15(18) S16(19) S17(20) S18(19)
S19(21) S20(12,22) S21(24) S22(23) S23(1,6,7,10,18,23,25) S24(dr-deliver-change).
