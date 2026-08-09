# Checklist for: judge-evidence review — read-only archaeology
Map ids: DR-SUB-evaluation, DR-SUB-adjudication, DR-CON-authority, DR-CON-schools
State: next=7 blockers=none
Re-read REQUEST.md + SPEC.md before every step. Execute strictly in order.
One step per dr-execute-step invocation.

Process note (deviation from the generic template, recorded here so a
fresh session does not "fix" it back): this tranche makes NO change under
`src/`, so the full `pytest tests/ -q -n 4` gate and `python
tools/docs_verify.py` are NOT repeated as checklist steps here — SPEC.md
S10/S11 and REQUEST.md R11 already assign the ONE full-gate run and the
tripwire diff to `dr-validate-change`/VALIDATION.md ("full gate once at the
boundary"). Running it twice would contradict CLAUDE.md's own gate
discipline ("the full suite is a gate, not a feedback loop"). This
checklist's last step re-confirms the tripwire is still 0 as a cheap local
check before handing off to validation, not as the gate itself.

- [x] 1. (S1) Create REVIEW.md skeleton: title, the operator's question
      verbatim, one-paragraph preview, section headers for S2-S9.
      done-when: `head -5 REVIEW.md | grep -q "LLM-judge discrimination"`
      DONE: `head -5 REVIEW.md | grep -q "LLM-judge discrimination" && echo "DONE-CRITERION PASS"` -> `DONE-CRITERION PASS`
      (preview paragraph deferred to end of §8, not written before evidence
      — see note in REVIEW.md; this is a smaller-than-planned but still
      compliant reading of "one-paragraph preview")
- [x] 2. (S2) Read `src/deepreason/informal/audits.py`'s four audit
      functions and log tags; read the 15 `experiments/results/*.json`
      files named in SPEC S2 plus `tests/test_audits.py`'s pinned numbers;
      write REVIEW.md §2 with every number sourced inline.
      done-when: REVIEW.md §2 exists and cites all 15 files by path
      DONE: python census script confirmed all 17 files SPEC S2 names
      (15 + the glm_judge/gemma files it also lists) appear in REVIEW.md
      -> `missing: NONE - all 17 cited`
- [x] 3. (S2) [COMMIT] commit REVIEW.md §2 progress.
      done-when: `git log -1 --oneline` shows this tranche's commit
- [x] 4. (S3) Read `informal/trial.py`'s order-swap/paraphrase guard code,
      the `2026-08-01-change-prose-can-refute` tranche files, and grep
      committed logs for `trial-llm`/`pairwise-observation`/
      `blocked:order-swap`/`blocked:paraphrase` hits; write REVIEW.md §3,
      explicitly separating live-run counts from test-fixture
      demonstrations.
      done-when: REVIEW.md §3 has both a "live-run" and a "test-fixture"
      subsection
      DONE: REVIEW.md §3.2 header says "TEST-FIXTURE, not live"; §3.3
      header says "Live-run counts"; both present -> pass
- [x] 5. (S4) Read the `2026-08-01-fix-adjudication-blindness` tranche
      files; write REVIEW.md §4 stating plainly whether it is
      judge-discrimination evidence.
      done-when: REVIEW.md §4 contains the words "is judge-discrimination
      evidence" or "is not judge-discrimination evidence"
      DONE: `grep -q "is NOT judge-discrimination evidence" REVIEW.md &&
      echo PASS` -> PASS (bolded variant satisfies the substring check)
- [x] 6. (S5) [COMMIT] Grep the stress-triplet run roots and audit files
      for judge content, check lambda's run status; write REVIEW.md §5;
      commit §3-§5 progress.
      done-when: REVIEW.md §5 states the stress-triplet zero-hit finding
      with its grep command, and lambda's status
      DONE: REVIEW.md §5.1 has the grep command and 0/0/0 output; §5.2
      states lambda's prereg-only status -> pass
- [ ] 7. (S6) Read `docs/EXPERIMENT_PROGRAM_2026-07.md`'s judge sections
      (L52-67, L153-200, L257-320, L415-528, L747-826) and cross-reference
      predictions P1/P2 against the e02 results from step 2; write
      REVIEW.md §6.
      done-when: REVIEW.md §6 states P1 and P2 each as
      confirmed/falsified/untested with a cited result file
- [ ] 8. (S7) [COMMIT] Write REVIEW.md §7's three-way scoring
      ((a) incorrect rulings, (b) discrimination-insensitivity,
      (c) over-prosecution) using only numbers already pasted in §2-§6;
      commit §6-§7 progress.
      done-when: REVIEW.md §7 has 3 subsections each ending in SUPPORTED /
      CONTRADICTED / MIXED / INSUFFICIENT EVIDENCE
- [ ] 9. (S8) Write REVIEW.md §8, the design-consequence section:
      program/predicate commitments, counterexample execution, and the
      trial guard's non-judge screens (referential integrity, order-swap),
      each with can/cannot/price/recommendation, plus a "decisions not
      made" list.
      done-when: REVIEW.md §8 enumerates >=3 mechanisms and ends with a
      non-empty "Decisions not made" list
- [ ] 10. (S9) [COMMIT] Write RESULTS.md's dated honest-ledger segment;
      commit §8 and RESULTS.md.
      done-when: `grep -q "residue" RESULTS.md`
- [ ] 11. (S10) Re-confirm the tripwire is still 0 after all edits.
      done-when: `git diff origin/main...HEAD -- src/ | wc -l` -> `0`
- [ ] 12. (all) [COMMIT] push and confirm clean tree.
      done-when: `git status --porcelain` is empty AND branch head is on
      origin
