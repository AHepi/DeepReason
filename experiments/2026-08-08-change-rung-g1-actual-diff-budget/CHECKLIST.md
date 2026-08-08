# Checklist for: Rung G1 — actual-diff budget gate
State: next=3 blockers=none
Map ids: `DR-INV-frozen-surfaces` (only map document touched — an
additive subsection, no existing header/check moved; no `DR-SUB-`/
`DR-CON-`/`DR-SEAM-` id applies, this tranche touches no
`src/deepreason/` subsystem).
Re-read REQUEST.md + SPEC.md before every step. Execute strictly in
order. One step per dr-execute-step invocation.

- [x] 1. (S1, S6) Write `tools/diff_budget.py` (CLI: `<base> [--against
      REF] [--ceiling N] [--paths PATH ...]` -> `DIFF_BUDGET_RESULT_V1`
      JSON; exit 0 result-emitted / 2 invalid-invocation / 3
      evidence-unavailable; `--self-test` mode proving WITHIN/
      EXCEEDED/NO_CEILING plus both non-zero exit classes against a
      throwaway `git init` temp dir) AND add the new subsection to
      `docs/map/INV-frozen-surfaces.md` (two `check:` lines: `ast.parse`
      syntactic validity, `grep -q "DIFF_BUDGET_RESULT_V1"`) in the SAME
      step, per the map-obligations rule that a map update rides the
      commit of the behavior it documents.
      done-when: `python tools/diff_budget.py --self-test` -> exit 0,
      prints `SELF-TEST PASS`; `python tools/docs_verify.py` -> ends
      `0 failed` (includes the two new checks).

      DONE. Self-test:
      ```
      SELF-TEST PASS
      ```
      docs_verify (full run, background task bjcs9r9g3):
      ```
      docs_verify [full]: 52 documents, 831 checks, 4 workers
      docs_verify: 0 failed
      ```
      831 checks, up from the 829 baseline -- the two new `check:`
      lines registered and passed.

      Mid-step discovery, fixed before commit (not a separate PARKED
      item -- it was this step's own SPEC.md scope text, caught before
      any code landed): SPEC.md's Budget headline named this tranche's
      own `experiments/` dir in the enforced ceiling scope, which
      contradicted its own itemization (never counted REQUEST.md/
      SPEC.md/CHECKLIST.md, already 638 lines together). Corrected in
      SPEC.md (see that file's "Correction" paragraph under `## Budget`)
      to match S5's own precedent of excluding the workflow's own
      ledger documents from the ceiling. No item's line count, the
      ceiling value (450), or any requirement changed.

- [x] 2. (S1, S6) [COMMIT] Commit `tools/diff_budget.py` +
      `docs/map/INV-frozen-surfaces.md` together; run the diff-budget
      check per dr-execute-step step 6 (still its pre-amendment prose
      form here — the gate cannot check its own first commit into
      existence).
      done-when: `git log -1 --stat` shows both files; push succeeds
      (retry 2/4/8/16s on failure).

      DONE, combined with the SPEC.md correction above (same commit,
      since both were staged together before the discovery was made):
      commit `1edbe1be` --
      ```
       docs/map/INV-frozen-surfaces.md                    |  19 +-
       experiments/.../SPEC.md                            |  22 +-
       tools/diff_budget.py                               | 222 ++++++
       3 files changed, 258 insertions(+), 5 deletions(-)
      ```
      Pre-commit budget check (pre-amendment prose form, tranche-base
      `d4f63007`, paths `tools/ tests/ .claude/skills/ docs/map/`):
      222 (tool) + 17 net (map doc) = 239 insertions, well within the
      450 ceiling (SPEC.md's own headline low bound alone is 318, so
      239 is under even that). Pushed.

- [x] 3. (S2) Write `tests/test_diff_budget.py`: fixture-repo pytest
      tests (subprocess-invoking the real CLI) for WITHIN, EXCEEDED,
      NO_CEILING, multi-`--paths` area breakdown, `total_insertions`
      independent of `--paths` overlap, exit class 2 (missing `<base>`),
      exit class 3 (unresolvable `<base>`), and the permanent
      boundary-equality companion test (`total_insertions == ceiling`
      asserts `WITHIN`, catching a `>`/`>=` mutation).
      done-when: `python -m pytest tests/test_diff_budget.py -q` ->
      ends `N passed, 0 failed`.

      DONE.
      ```
      ............                                                             [100%]
      12 passed in 2.42s
      ```
      12 tests, not the originally-planned ~7: also added
      `--against REF` coverage (needed by S3's retrodiction demo),
      `--ceiling -1` invalid-invocation coverage, a not-a-git-repo
      evidence-unavailable case, and a `--self-test` passthrough check
      -- all traceable to S1/S2's own spec text, not new scope.

- [x] 4. (S2) [COMMIT] Commit `tests/test_diff_budget.py`; run the
      diff-budget check per current (pre-amendment) step 6 prose.
      done-when: `git log -1 --stat` shows the file; push succeeds.

- [ ] 5. (S1, S2) Mutation-prove the gate: perturb
      `tools/diff_budget.py`'s WITHIN/EXCEEDED comparison operator
      (`<=` -> `<`), re-run `tests/test_diff_budget.py -q` and confirm
      the boundary companion test goes RED; `git checkout --
      tools/diff_budget.py` to restore; re-run and confirm GREEN again.
      No net file change — no commit.
      done-when: perturbed run shows `1 failed` (the boundary test,
      named); `git diff --stat tools/diff_budget.py` empty after
      restore; restored run ends `N passed, 0 failed` again — all three
      pasted.

- [ ] 6. (S3) [COMMIT] Retrodiction: `git fetch origin
      claude/s5-dr-plan-steps-q5utlc`; run `python tools/diff_budget.py
      54feb5cc --against ca34dc49 --ceiling 300 --paths src/ tests/
      docs/map/ tools/root_sweep.py` and the same command with
      `--against b0813f59`; paste both JSON outputs into this step;
      commit CHECKLIST.md.
      done-when: first command's `verdict` is `WITHIN`
      (`total_insertions` 284); second's is `EXCEEDED`
      (`total_insertions` 361) — the commit ("step 7-10", `b0813f59`)
      REQUEST.md Amendment 2 names as where the overrun was caught by
      hand; push succeeds.

- [ ] 7. (S4) [COMMIT] Amend `.claude/skills/dr-spec-change/SKILL.md`
      step 6 ("Set the budget") per SPEC.md S4: headline must equal the
      computed sum of the itemization, naming `tools/diff_budget.py`
      and `DIFF_BUDGET_RESULT_V1` exactly. Run the diff-budget check
      (current prose form) before committing.
      done-when: `grep -n "tools/diff_budget.py"
      .claude/skills/dr-spec-change/SKILL.md` and `grep -n
      "DIFF_BUDGET_RESULT_V1" .claude/skills/dr-spec-change/SKILL.md`
      both match; push succeeds.

- [ ] 8. (S5) [COMMIT] Amend `.claude/skills/dr-execute-step/SKILL.md`
      step 6 per SPEC.md S5: invoke `tools/diff_budget.py` against the
      tranche-base and SPEC.md's ceiling/paths, read
      `DIFF_BUDGET_RESULT_V1.verdict`; EXCEEDED remains the STOP in the
      standard format. THIS is the commit where the tool's own gate
      first checks itself — run it (against this tranche's own base
      and the SPEC.md ceiling of 450) before committing, using the now
      newly-amended procedure.
      done-when: `grep -n "tools/diff_budget.py"
      .claude/skills/dr-execute-step/SKILL.md` and `grep -n
      "DIFF_BUDGET_RESULT_V1" .claude/skills/dr-execute-step/SKILL.md`
      both match; `python tools/diff_budget.py <tranche-base-sha>
      --ceiling 450 --paths tools/ tests/ .claude/skills/ docs/map/`
      pasted, verdict `WITHIN`; push succeeds.

- [ ] 9. (S7) [COMMIT] Write `PARKED.md`: the `.claude/skills/
      README.md` discrepancy (Q1) — WHAT, plus a ready-to-send
      follow-up prompt for a future session (route: doc fix, not
      routed through either orchestrator skill family since it is a
      one-line stale-reference correction).
      done-when: `PARKED.md` exists, contains the entry; push succeeds.

- [ ] 10. (all) Full docs_verify: `python tools/docs_verify.py`.
      done-when: output ends `0 failed`, pasted.

- [ ] 11. (all) Full gate: `python -m pytest tests/ -q -n 4`.
      done-when: output ends `N passed, M failed` with the only
      failure(s) being the named pre-existing P1/P3
      (`tests/test_module_fingerprints.py::
      test_absence_is_valid_before_the_feature_and_presence_valid_after`),
      pasted.

- [ ] 12. (all) [COMMIT] Final CHECKLIST.md update (all boxes checked,
      State: line advanced to `next=none`); push and confirm clean
      tree.
      done-when: `git status --porcelain` empty AND branch head is on
      origin (`git rev-parse HEAD` == `git rev-parse
      origin/claude/rung-g1-actual-diff-budget-b0jede`).
