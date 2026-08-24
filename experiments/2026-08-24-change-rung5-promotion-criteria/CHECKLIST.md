# Checklist for: Rung 5 — promotion problems and their criteria as programs
State: next=1 blockers=none
Map ids this plan was built on: `DR-SUB-calculus`, `DR-SUB-evaluation`,
`DR-SUB-rules`, `DR-SEAM-evaluation-x-rules` (read first, per the map's own
seam-before-subsystem rule), `DR-SEAM-evaluation-x-ontology`,
`DR-CON-standing-and-background`, `DR-CON-problem-layer-lifecycle`,
`DR-INV-frozen-surfaces`, `DR-INV-axiom-basis`.
Re-read REQUEST.md + SPEC.md before every step. Execute strictly in order.
One step per dr-execute-step invocation.

- [ ] 1. (S1, S11) Write `tests/test_calculus_nomination.py` — lineage
      derivation and the K_FRAME boundary, both sides — against the
      not-yet-existing `calculus/nomination.py`.
      done-when: `python -m pytest tests/test_calculus_nomination.py -q` fails
      with a collection/import error naming `nomination` (the test exists and
      guards nothing yet).

- [ ] 2. (S3) Add `ReachCertificateV1` to `calculus/claims.py`, its rule to
      `calculus/compiler.py`, and `reach_certificate_wf` to
      `calculus/programs.py`.
      done-when: `python -c "from deepreason.calculus.claims import decode; import json; b=decode(json.dumps({'schema':'poietic.reach-certificate.v1','subject_ref':'b','scope':{'schema':'declarative-scope.v1','predicate':{'const':True}},'k_frame':2})); assert b.subject_ref=='b'"`
      exits 0.

- [ ] 3. (S2) Add `Config.K_FRAME` and `Config.PROMOTION_ENVIRONMENT_MAX`, each
      with its `data.pop(..., None)` line and reason comment in
      `run_manifest.py::_versioned_source_config_data`.
      done-when: `python -c "import json; from tests.test_reusable_qualification import _manifest, _profile; c=json.loads(_manifest(_profile()).engine_config_json); leaked=sorted(k for k in c if k in ('K_FRAME','PROMOTION_ENVIRONMENT_MAX')); assert not leaked, leaked"`
      exits 0.

- [ ] 4. (S1, S3) Write `src/deepreason/calculus/nomination.py`: `problem_parents`,
      `lineage_root`, `lineage_span`, the canonical scope builder, the
      certificate builder, and `nominate`.
      done-when: `python -m pytest tests/test_calculus_nomination.py -q` ends
      "N passed" with 0 failed.

- [ ] 5. (S1) [COMMIT] Prove the measure cannot decide: it reads and writes no
      label.
      done-when: `python -c "import ast,pathlib; t=ast.parse(pathlib.Path('src/deepreason/calculus/nomination.py').read_text()); names={n.attr for n in ast.walk(t) if isinstance(n,ast.Attribute)}; assert not {'status','hv'} & names, sorted(names)"`
      exits 0, and the commit lands.

- [ ] 6. (S11, S15) Write `tests/test_promotion_nomination_live.py` — M-4's
      NEGATIVE half on the committed attempt-4 root, opened `read_only=True`,
      asserting the empty nomination AND the one-lineage reason.
      done-when: `python -m pytest tests/test_promotion_nomination_live.py -q`
      ends "N passed" with 0 failed.

- [ ] 7. (S11) [COMMIT] Mutation-prove the live negative: temporarily make
      `lineage_root` return the problem id itself, watch the live test go RED,
      restore, watch it go GREEN. Paste both runs.
      done-when: both pasted outputs are in the step record, tree restored,
      `git diff --stat src/` shows no residue of the mutation.

- [ ] 8. (S4–S8, S12) Write `tests/test_promotion_criteria.py` — one passing and
      one refusing case per criterion, plus a budget-0 `overrun` case per
      program.
      done-when: `python -m pytest tests/test_promotion_criteria.py -q` fails
      with an import error naming `promotion` (the tests exist, the module does
      not).

- [ ] 9. (S10 of REQUEST R10, i.e. SPEC S8) Write
      `tests/test_promotion_succession.py` — the FOUR refusals the strong
      relation owes: recovery-only, easier-to-vary, excisable-idle-part, and
      every-clause-non-strict.
      done-when: `python -m pytest tests/test_promotion_succession.py -q` fails
      with an import error naming `promotion`.

- [ ] 10. (S4–S8, A10) Write `src/deepreason/calculus/promotion.py`: the five
      criterion programs, pure over (candidate bytes, frozen certificate).
      done-when: `python -m pytest tests/test_promotion_criteria.py tests/test_promotion_succession.py -q`
      ends "N passed" with 0 failed.

- [ ] 11. (A10, S15) Register the six programs in `programs.py` — `PROGRAMS`
      with `class_="structural"` and `BLOB_PROGRAMS` for blob dispatch — and
      update `docs/map/SEAM-evaluation-x-ontology.md:54`'s `G(f)` list in the
      SAME edit.
      done-when: `python -c "from deepreason.programs import programs_by_class; from deepreason.measures.reach import _STRUCTURAL_PROGRAMS; d=set(programs_by_class()['structural']); assert d == set(_STRUCTURAL_PROGRAMS); assert {'reach_certificate_wf','promotion_subject_demarcation','promotion_reach_integrity','promotion_scope_determinism','promotion_compatibility','promotion_accounts_for'} <= d"`
      exits 0, and `python -m pytest tests/test_reflexive_discipline.py tests/test_prose_refutation_boundaries.py tests/test_verifier_registry.py tests/test_decommissioned_pipeline_stays_out.py -q`
      ends 0 failed.

- [ ] 12. (S8) [COMMIT] Mutation-prove the strong relation's first refusal (R10):
      temporarily drop the strictness-witness clause, watch
      `test_a_rival_that_only_recovers_is_not_a_successor` go RED, restore,
      watch it go GREEN. Paste both runs.
      done-when: both pasted outputs are in the step record and the tree is
      restored.

- [ ] 13. (S9, S12) Write `tests/test_promotion_closure.py` — Remark 9.5 both
      ways: an assertion outside a promotion problem is ignored; one addressed
      to a promotion problem whose criteria FAIL does not frame its scope.
      done-when: `python -m pytest tests/test_promotion_closure.py -q` fails
      with an import error naming `promotion_criteria_sweep`.

- [ ] 14. (S9) Add `promotion_criteria_sweep` to `calculus/promotion.py`, minting
      demonstrative warrants through `rules/warrants.py::register_fail_warrant`
      and minting nothing for `overrun`.
      done-when: `python -m pytest tests/test_promotion_closure.py -q` ends 0
      failed.

- [ ] 15. (S1, S9) Wire `nominate` and `promotion_criteria_sweep` into the
      scheduler beside the existing reach sweep, BEFORE consultation.
      done-when: `python -m pytest tests/test_calculus_standing.py tests/test_scheduler.py -q`
      ends 0 failed.

- [ ] 16. (S13) [COMMIT] Write `tests/test_promotion_solo.py` — the whole path on
      `Config()` defaults, no judge seat, no ensemble.
      done-when: `python -m pytest tests/test_promotion_solo.py -q` ends 0
      failed, and the test asserts `Config().JUDGE_SEATS_ENABLED is False`.

- [ ] 17. (S10) Write `src/deepreason/views/knowledge.py` with `KNOWLEDGE_LABEL`
      and render it as a section of the existing `deepreason standing` command;
      extend `tests/test_calculus_standing.py:416`'s CLI assertion rather than
      weakening it.
      done-when: `python -c "from deepreason.views.knowledge import KNOWLEDGE_LABEL; assert KNOWLEDGE_LABEL=='knowledge (unrefuted ∧ active ∧ reach > 0)'"`
      exits 0 and `python -m pytest tests/test_calculus_standing.py -q` ends 0
      failed.

- [ ] 18. (S10, C1) [COMMIT] Prove the public surface did not move.
      done-when: `python scripts/wheel_smoke.py` and `python -u
      scripts/wheel_operational_smoke.py` both exit 0 (paste both).

- [ ] 19. (S14) Update `docs/map/INV-axiom-basis.md`: A8 PROVED with its spawn-half
      check, A4 and Ax 4.1 preservation checks over the new modules. Every check
      RUN before it is written down.
      done-when: each new check pasted with its exit-0 run, in the step record.

- [ ] 20. (S15) Update `docs/map/SEAM-evaluation-x-rules.md` (the promotion
      lifecycle — the ladder's named exit artifact), `SUB-calculus.md`,
      `SUB-evaluation.md`, `CON-standing-and-background.md`,
      `CON-problem-layer-lifecycle.md`, `INV-frozen-surfaces.md` (the granted
      surface-4 contact and its measurement), and `INDEX.md`.
      done-when: `python tools/docs_verify.py --links` exits 0 and every new
      check was run before being written.

- [ ] 21. (all) Map check, FULL (never `--fast`).
      done-when: `python tools/docs_verify.py` reports only the 3 known
      shallow-clone `CON-run-identity.md` failures, and
      `python tools/docs_verify.py --audit` reports 0 findings.

- [ ] 22. (C2) Diff budget against the ledgered ceiling.
      done-when: `git add -A && python tools/diff_budget.py ade214037 --ceiling 1900`
      prints `"verdict": "WITHIN"`.

- [ ] 23. (all) Full gate, on an otherwise idle box.
      done-when: `python -m pytest tests/ -q -n 4` output ends "N passed, 0
      failed" (pasted).

- [ ] 24. (all) [COMMIT] Push and confirm a clean tree.
      done-when: `git status --porcelain` is empty AND the branch head is on
      `origin/claude/rung-5-promotion-criteria-wu31d8`.
