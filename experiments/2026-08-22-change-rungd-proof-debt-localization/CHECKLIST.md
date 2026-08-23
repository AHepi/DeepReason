# Checklist for: Rung D — proof debt (E-1) and Duhem localization (E-2)

State: next=2 blockers=none
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

- [ ] 2. (S1–S11) [COMMIT] Write `tests/test_proof_debt.py` with all D1 tests
      named in SPEC.md S2, S5, S6, S7, S8, S9, S10, S20. They must FAIL now.
      done-when: `python -m pytest tests/test_proof_debt.py -q 2>&1 | tail -3` shows collection or assertion failures, 0 passed; paste it

## Phase 2 — D1 code, with its map, in the same commits

- [ ] 3. (S1) Add `DerivationManifestV1` + `KernelCheckV1` to
      `calculus/claims.py`; extend `_IMPLEMENTED`. `CLAIM_SCHEMAS` unchanged.
      done-when: `python -c "from deepreason.calculus import CLAIM_SCHEMAS; from deepreason.calculus.claims import _IMPLEMENTED; assert len(CLAIM_SCHEMAS)==9 and 'poietic.derivation-manifest.v1' in _IMPLEMENTED; print('ok')"` -> ok

- [ ] 4. (S2) Add the `DerivationManifestV1` rule to `calculus/compiler.py`:
      `DEPENDENCE` per open certificate, `MENTION` on the subject.
      done-when: `python -m pytest tests/test_proof_debt.py::test_open_certificates_are_dependences_and_the_subject_is_a_mention -q` -> 1 passed

- [ ] 5. (S3) Add `derivation_manifest_wf` + `DERIVATION_MANIFEST_COMMITMENT`
      to `calculus/programs.py` and register it `"structural"` in
      `src/deepreason/programs.py`.
      done-when: `python -c "from deepreason.programs import PROGRAMS; assert PROGRAMS['derivation_manifest_wf'].kind=='structural'; print('ok')"` -> ok

- [ ] 6. (S4, S5) [COMMIT] Create `src/deepreason/proof_debt.py`:
      `file_derivation_manifest`, `manifests_for`, `receipt`, the three
      itemization constants. Export the new claim names from
      `calculus/__init__.py`. Advance `SUB-calculus.md`'s `_IMPLEMENTED` check
      to 4 and its `Owns:`/prose in the SAME commit.
      done-when: `python -m pytest tests/test_proof_debt.py -q -k "receipt or manifest_is_recomputed or reruns_its_kernel"` -> 0 failed

- [ ] 7. (S8) Add `manifest_ref` to `rules/warrants.py::register_fail_warrant`,
      merging an `EVIDENCE` ref into ν's interface. Update
      `CON-warrants-and-attacks.md` in the SAME commit.
      done-when: `python -m pytest tests/test_proof_debt.py::test_a_manifest_is_wired_to_the_validity_node_as_evidence -q` -> 1 passed

- [ ] 8. (S9) Prove R58's pinned regression end to end.
      done-when: `python -m pytest tests/test_proof_debt.py::test_attacking_a_manifest_item_disables_the_attack_before_pass_one -q` -> 1 passed

- [ ] 9. (S6, S7) Prove recomputation-not-retroactivity and replay determinism.
      done-when: `python -m pytest tests/test_proof_debt.py -q -k "replays_identically or recomputation_not_retroactively"` -> 0 failed

- [ ] 10. (S10) Teach `premises.py::premise_rent_sweep` to register the sample
      certificate + manifest on the sampled path and pass `manifest_ref`.
      Update `CON-problem-layer-lifecycle.md` in the SAME commit.
      done-when: `python -m pytest tests/test_proof_debt.py::test_the_rent_sweep_files_a_manifest_whose_sample_is_attackable -q` -> 1 passed

- [ ] 11. (S10, S11) Ring: the premise/calculus/warrant consumers the census
      named EXPECTED TO MOVE or MUST NOT MOVE.
      done-when: `python -m pytest tests/test_premise_channel.py tests/test_premise_channel_loop.py tests/test_calculus_frame_separation.py tests/test_calculus_claim_substrate.py tests/test_calculus_frame_assertions.py tests/test_easy.py tests/test_evidence_view.py tests/test_scheduler.py tests/test_simulation_backend.py tests/test_workload_formal.py -q` -> 0 failed; paste it

- [ ] 12. (S20) Prove D1's readout inertness: filing a manifest moves no label.
      done-when: `python -m pytest tests/test_proof_debt.py::test_filing_a_manifest_moves_no_label -q` -> 1 passed

- [ ] 13. (all D1) [COMMIT] D1 boundary: diff-budget check + push.
      done-when: `python tools/diff_budget.py b10fc5fd2 --ceiling 1480 --paths src tests docs` -> verdict WITHIN; paste it

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
