# Checklist for: the two-tier hard question set

State: next=2 blockers=none
Map ids: `DR-CON-run-identity`, `DR-SUB-manifest`, `DR-CON-seats`,
`DR-SUB-scheduler` (navigation only — no `src/` change in this
tranche; see SPEC.md).
Re-read REQUEST.md + SPEC.md before every step. Execute strictly in
order. One step per `dr-execute-step` invocation.

- [x] 1. (R3/R11) Create `experiments/2026-08-09-change-hard-question-set/schema_check.py`: validates a Tier V or Tier O JSON array against SPEC.md's field lists (id/tier/q/kind/accept-or-checker/source/license/verification for V; id/tier/q/attribution/source_url/still_open_verified/computable_special_case/verification for O), exits 1 with a clear message per violation.
      done-when: `python experiments/2026-08-09-change-hard-question-set/schema_check.py --selftest` exits 0 against two small inline fixtures (one valid, one deliberately broken, asserting the broken one is rejected).
      DONE: `SELFTEST PASS: valid fixture accepted (0 errors), broken fixture rejected (1 errors: ["error: record 0 (tv-m01): missing ['source']"])`, exit=0.

- [x] 2. (R3/R11) [COMMIT] Commit schema_check.py.
      done-when: `git add ... && git commit -m ... && git push` succeeds; `git diff --numstat` for the commit touches only files under `experiments/2026-08-09-change-hard-question-set/`.
      DONE: commit ae79a24e5, pushed. diff_budget: 164 insertions (WITHIN ceiling 2500), both changed files under experiments/2026-08-09-change-hard-question-set/.

- [x] 3. (R4/R5/A3) Draft 10 Tier V math problems into `experiments/2026-08-09-change-hard-question-set/draft_tier_v_math.json`: sourced from the Hendrycks MATH dataset's level-4/5 (competition-difficulty) split, each with id (`tv-m01`..`tv-m10`), statement, numeric/short `accept` answer(s), `source` (dataset+problem locator+URL), `license: MIT`.
      done-when: file contains exactly 10 entries; `python experiments/2026-08-09-change-hard-question-set/schema_check.py experiments/2026-08-09-change-hard-question-set/draft_tier_v_math.json --kind math` exits 0.
      DONE: `PASS: .../draft_tier_v_math.json (10 records, kind=math)`. Sourced via the EleutherAI/hendrycks_math HF mirror (content = MIT-licensed hendrycks/math), fetched live via the datasets-server REST API, filtered to Level 4-5, self-contained (no diagram dependency), clean short answers. Subjects: number_theory(4), counting_and_probability(2), intermediate_algebra(2), algebra(1), precalculus(1).

- [x] 4. (R4/R5/A3) Draft 10 Tier V coding problems into `experiments/2026-08-09-change-hard-question-set/draft_tier_v_coding.json`: sourced from OpenAI HumanEval, hand-selected for multi-step algorithmic content (not single-line ops), each with id (`tv-c01`..`tv-c10`), statement (docstring), reference solution (kept in the draft for checker-authoring, not in the final public JSON), `source`/`license: MIT`.
      done-when: file contains exactly 10 entries; `python experiments/2026-08-09-change-hard-question-set/schema_check.py experiments/2026-08-09-change-hard-question-set/draft_tier_v_coding.json --kind coding` exits 0.
      DONE: `PASS: .../draft_tier_v_coding.json (10 records, kind=coding)`. Sourced live from openai/openai_humaneval via the HF datasets-server API, ranked by canonical-solution length as a difficulty proxy, hand-picked for genuine algorithmic content (grid DP, prime Fibonacci, interval/primality, date validation, array-rotation feasibility, prime factorization, polynomial root bisection, closest-pair search, Roman numeral conversion, bracket-nesting depth) rather than string one-liners.

- [x] 5. (R6) [COMMIT] Commit the two Tier V drafts.
      done-when: pushed; `git diff --numstat` scoped to the tranche directory only.

- [x] 6. (R6) Write the 10 math checkers, `experiments/tier_v_checkers/tv-m0{1..10}_checker.py` (normalize+compare against `accept`, mirroring `scripts/validate.py`'s `normalize()`), and RUN each against its own known answer.
      done-when: for each of the 10 scripts, `python experiments/tier_v_checkers/tv-mNN_checker.py "<known-answer>"` prints/exits PASS (paste all 10 results).
      DONE (all 10, known-answer input → PASS rc=0; +1-off wrong input → FAIL rc=1, mutation-proving each checker can actually fail):
      tv-m01 PASS 44 / FAIL 45 | tv-m02 PASS 13 / FAIL 14 | tv-m03 PASS 201 / FAIL 202 |
      tv-m04 PASS 16592 / FAIL 16593 | tv-m05 PASS 835 / FAIL 836 | tv-m06 PASS 31 / FAIL 32 |
      tv-m07 PASS 2 / FAIL 3 | tv-m08 PASS 38 / FAIL 39 | tv-m09 PASS 9 / FAIL 10 | tv-m10 PASS 144 / FAIL 145.
      ALL_OK.

- [x] 7. (R6) Write the 10 coding checkers, `experiments/tier_v_checkers/tv-c0{1..10}_checker.py` (each embeds that HumanEval problem's own `check(candidate)` test function), and RUN each against its problem's reference solution.
      done-when: for each of the 10 scripts, running it with the reference solution loaded prints/exits PASS (paste all 10 results) — a checker that has not produced a passing run is not committed (R6).
      DONE: all 10 PASS rc=0 against the embedded reference solution (`python tv-cNN_checker.py` with no args). One bug found and fixed during authoring: tv-c07 (HumanEval/32, find_zero) initially raised `NameError: name 'poly' is not defined` because its test calls a PROMPT-level helper (`poly`) that a naive per-call `exec` into a throwaway dict didn't expose to `check()`'s own module scope; fixed by `exec(PROMPT, globals())` once at module load so helper functions defined in the prompt are visible everywhere the checker runs, same as any real HumanEval harness. Mutation-proof: all 10 also run against a deliberately wrong candidate (`return '__WRONG_SENTINEL__'` for any input) and all 10 correctly FAIL rc=1 (tv-c07 raises TypeError uncaught, still rc=1 — a genuine reject, not a false pass).

- [ ] 8. (R6/R11) [COMMIT] Commit `experiments/tier_v_checkers/` (20 files).
      done-when: pushed; `git diff --numstat` shows only `experiments/tier_v_checkers/*`; `tools/diff_budget.py <base> --paths experiments/tier_v_checkers` reported and under the 2500-line ceiling.

- [ ] 9. (R3/R4/R11) Assemble `experiments/validation_questions_tier_v.json` from the two drafts (public shape only — no reference solutions inline, checker path instead) and validate.
      done-when: `python experiments/2026-08-09-change-hard-question-set/schema_check.py experiments/validation_questions_tier_v.json --kind both` exits 0; file has exactly 20 entries.

- [ ] 10. (R3/R4) [COMMIT] Commit `experiments/validation_questions_tier_v.json`.
      done-when: pushed; diff scoped to that one file plus nothing under src/tests/tools.

- [ ] 11. (R7/R8/R9/A4) Source and independently verify 10 Tier O problems (shortlist in SPEC.md, subject to swap if re-verification fails): for each, restate the conjecture in original words, record attribution, source_url, and `still_open_verified` date from an independent check performed THIS step (not copied from SPEC.md's research pass), and `computable_special_case` (or null, stated honestly). Write to `experiments/2026-08-09-change-hard-question-set/draft_tier_o.json`.
      done-when: file has exactly 10 entries, each with a `still_open_verified` date and a distinct `source_url`; `python experiments/2026-08-09-change-hard-question-set/schema_check.py experiments/2026-08-09-change-hard-question-set/draft_tier_o.json --kind open` exits 0.

- [ ] 12. (R7/R8) [COMMIT] Commit the Tier O draft.
      done-when: pushed; diff scoped to the tranche directory.

- [ ] 13. (R3/R7/R11) Assemble `experiments/validation_questions_tier_o.json` from the draft and validate.
      done-when: `python experiments/2026-08-09-change-hard-question-set/schema_check.py experiments/validation_questions_tier_o.json --kind open` exits 0; 10 entries.

- [ ] 14. (R3/R7) [COMMIT] Commit `experiments/validation_questions_tier_o.json`.
      done-when: pushed; `tools/diff_budget.py <base> --paths experiments/validation_questions_tier_v.json experiments/validation_questions_tier_o.json experiments/tier_v_checkers experiments/2026-08-09-change-hard-question-set` reported and under 2500 lines total so far.

- [ ] 15. (R10) Write `experiments/2026-08-09-change-hard-question-set/PREREG.md`: the Tier O hygiene rule verbatim (claims-resolution = fail, honest inconclusive/partial = success), the typed fields the audit will read to classify a run, and the Tier V checker-invocation rule — written before any pilot output exists.
      done-when: file exists; `git log` shows this commit's timestamp precedes any `pilot-tier-*` run-root commit (checked at delivery, not here, but the ordering constraint is satisfied by executing this step before 17+).

- [ ] 16. (R10) [COMMIT] Commit PREREG.md.
      done-when: pushed.

- [ ] 17. (R12) Write `experiments/2026-08-09-change-hard-question-set/env` containing `OLLAMA_API_KEY=<the key from this session>`; `chmod 600` it.
      done-when: `git check-ignore experiments/2026-08-09-change-hard-question-set/env` exits 0 (already confirmed session-start; re-confirmed here); `ls -l` shows mode 600; `git status --porcelain` does NOT list the file.

- [ ] 18. (R13/R14/A5) Write `experiments/2026-08-09-change-hard-question-set/pilot_tier_v_run.sh`: modeled on `experiments/2026-08-08-live-two-seat-ab-s6/s6_run.sh` MINUS any `--seat` flag, `deepreason setup --model gemma4:31b` (A5 profile values), `qualify --yes --json`, `reason "<the chosen Tier V representative question>" --cycles 10 --token-budget 195000 --allow-partial`, audit, `continue --budget cycles=2` (up to twice) if `stop_reason` is resumable, re-audit.
      done-when: `bash -n experiments/2026-08-09-change-hard-question-set/pilot_tier_v_run.sh` (syntax check) exits 0; `chmod +x` applied.

- [ ] 19. (R13/R14/R15/R16) [COMMIT] Commit the Tier V pilot ladder script (not the env file), then launch it detached (`setsid nohup ./pilot_tier_v_run.sh & disown`) and wait for completion, reading `qualify`'s tier verdict, `run-status.json`'s `stop_reason`, `verify_root`, and the Tier V checker result against the run's committed final answer.
      done-when: driver log shows an end marker with every `rc=` line; `qualify` tier (full/shallow) is recorded; `stop_reason` is a typed value; `verify_root` reports no violations; the checker's PASS/FAIL against the committed answer is recorded (either is an acceptable typed outcome per R16).

- [ ] 20. (R13/R18) [COMMIT] Commit the Tier V pilot run root and driver log/audit output.
      done-when: pushed; the failure-budget ledger (S6-style, cap 6 for this phase) is updated in RESULTS.md-in-progress with this leg's count.

- [ ] 21. (R13/R14/A5) Write `experiments/2026-08-09-change-hard-question-set/pilot_tier_o_run.sh`, same template as step 18, for the chosen Tier O representative question.
      done-when: `bash -n` exits 0; `chmod +x` applied.

- [ ] 22. (R13/R14/R15/R16) [COMMIT] Commit the Tier O pilot ladder script, launch detached, wait for completion, read `qualify` tier, `stop_reason`, `verify_root`, and compute the Tier O hygiene verdict per PREREG.md against the run's final state.
      done-when: driver log end marker present; typed `stop_reason` recorded; `verify_root` clean; hygiene verdict (success/junk-acceptance) recorded per PREREG.md's rule — an honest inconclusive/partial final state is a SUCCESS per R16/PREREG.md, not a failure to retry.

- [ ] 23. (R13/R18) [COMMIT] Commit the Tier O pilot run root and driver log/audit output.
      done-when: pushed; failure-budget ledger updated.

- [ ] 24. (R18) Write `experiments/2026-08-09-change-hard-question-set/PARKED.md` listing every defect noticed during steps 1-23 (or explicitly "none found this tranche" if true), each with a one-line WHAT and a ready-to-send prompt for its future `deepreason-orchestrator` runner.
      done-when: file exists and is non-empty (even the "none found" case is a written, dated statement, not a missing file).

- [ ] 25. (R19/R20) [COMMIT] Commit PARKED.md, then write `experiments/2026-08-09-change-hard-question-set/RESULTS.md`: the dated honest-ledger segment — corpus delivered (counts, licenses), what the two live pilots proved and did NOT prove (n=1 per tier, stochasticity doctrine), the gemma-sole-model calibration answer (full vs shallow tier reached), the failure-budget spend.
      done-when: pushed; RESULTS.md contains a dated segment header and explicitly answers the operator's standing gemma-sole-model question.

- [ ] 26. (all) Map check: `python tools/docs_verify.py`
      done-when: exits reporting 0 failed (this tranche touches no `docs/map/` document, so this is a no-regression check, not new content).

- [ ] 27. (all) Full gate: `python -m pytest tests/ -q -n 4`
      done-when: output ends "N passed, 0 failed" (paste it); if the known bronze-census environment-coupling item (`experiments/2026-08-08-parked-bronze-census-env/PARKED.md`) is the only failure, name it explicitly rather than treating it as new.

- [ ] 28. (R21) [COMMIT] Final push and clean-tree check.
      done-when: `git status --porcelain` is empty; `git log origin/<branch>..HEAD` is empty (local head == pushed head).
