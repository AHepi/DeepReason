# Checklist for: make the critic's byte-checked citation channel reachable, and stop it latching shut

State: next=10 blockers=none
Re-read REQUEST.md + SPEC.md before every step. Execute strictly in order.
One step per dr-execute-step invocation.

Map ids this plan was built on (read in this order, per `dr-drive-harness` §4):
`DR-INV-frozen-surfaces` (first; verdict CLEAR, pasted in SPEC.md) →
`DR-SEAM-scheduler-x-rules` (the seam, before either side; row 58 owns the
premise-layer consult) → `DR-CON-problem-layer-lifecycle` (owns `premises.py`) →
`DR-CON-criticism-source` (owns `rules/crit.py`) → `DR-INV-signal-contract` +
`DR-REC-add-signal` (the channel S3 declares through) →
`DR-CON-packs-and-token-economy` (read-only: it pins `DISCLOSED_ON_DROP`, which
M4 relies on and C4 forbids touching).

No seam document needs CREATING: the pair is `scheduler x rules`, already
written, and this change stays on the rules side of it.

- [x] 1. (S4) Write the RED regression: the late-refutation reopen, plus the
      disposition receipts, against the UNCHANGED tree.
      New tests in `tests/test_premise_channel.py` (the gate arithmetic) and
      `tests/test_premise_channel_loop.py` (the driven run: refutations →
      premise filed → gate shut → LATE refutations → gate open again → a critic
      dispatch carries the invitation and records its disposition).
      done-when: `python -m pytest tests/test_premise_channel.py tests/test_premise_channel_loop.py -q`
      FAILS on exactly the new tests, and the output is saved to
      `proof/s4_red.txt` (this is the mutation proof: the tests are red on the
      tree that lacks the fix).

- [x] 2. (S4) [COMMIT] Commit the red tests with their pasted red output.
      done-when: `git log --oneline -1` names the red-test commit and
      `proof/s4_red.txt` is tracked.

- [x] 3. (S1) Implement the ladder in `src/deepreason/premises.py`
      `premise_work_invited`: count this problem's standing attributions;
      return `refuted >= after * (standing + 1)`. Docstring states the ladder,
      its bound (`floor(refuted/after)` invitations per problem) and the
      unchanged-at-zero-attributions property. `PREMISE_INVITE_AFTER` untouched.
      done-when: `python -m pytest tests/test_premise_channel.py -q` -> 0 failed
      (the gate-arithmetic half of step 1 now GREEN; the loop half may still be
      red until step 5).

- [x] 4. (S1, S5) Move `docs/map/CON-problem-layer-lifecycle.md` in the SAME
      change: lines 149 and 216 state the ladder, with a NEW `check:` that would
      fail if the latch came back. Run the check before writing it down.
      done-when: the new `check:` command exits 0 when run by hand, AND
      `python tools/docs_verify.py --fast` reports no NEW failure over the C7
      baseline.

- [x] 5. (S1, S5) [COMMIT] Commit the ladder + its map move together.
      done-when: `git show --stat HEAD` lists `src/deepreason/premises.py` and
      `docs/map/CON-problem-layer-lifecycle.md` in one commit, and
      `python3 tools/diff_budget.py` (or the equivalent line count) is within
      the SPEC.md budget.

- [x] 6. (S3) Declare `premise-answer:` in `src/deepreason/signals.py`
      `_DECLARED_PREFIXES` — producer-agnostic semantics saying what one
      occurrence means, what it is NOT evidence of, `unit="event"`,
      `staleness="permanent"`, no `unspecified` (so `MIGRATION_DEBT` does not
      move). Declaration lands BEFORE the emitter, so an existing root with the
      signal absent stays valid and the registry never sees an undeclared tag.
      done-when: `python -m pytest tests/test_signal_contract.py tests/test_signals.py -q`
      -> 0 failed, AND
      `python -c "from deepreason.signals import is_known, describe; assert is_known('premise-answer:DECLINED'); print(describe('premise-answer:DECLINED'))"`
      prints the declared semantics.

- [x] 7. (S2) Emit the disposition in `src/deepreason/rules/crit.py`
      `_file_attribution`: invitation lookup FIRST; uninvited returns None and
      records nothing; invited records exactly one
      `premise-answer:{DECLINED|UNCITED|CITED}` Measure with
      `[tag, problem_id, target_id]`. No status moves, no artifact is minted.
      done-when: `python -m pytest tests/test_premise_channel_loop.py tests/test_premise_channel.py tests/test_p4_citable_evidence.py -q`
      -> 0 failed (step 1's loop tests now GREEN).

- [x] 8. (S2, S3, S5) Move `docs/map/CON-criticism-source.md` (the citation trap
      at line 137 gains the disposition receipt) and
      `docs/map/SEAM-scheduler-x-rules.md` line 58 (the premise-layer row states
      the ladder) in the SAME change, each with a `check:` that would fail on a
      regression, run before it is written.
      done-when: both new `check:` commands exit 0 by hand, AND
      `python tools/docs_verify.py --fast` reports no NEW failure over baseline.

- [x] 9. (S2, S3, S5) [COMMIT] Commit the receipt + its declaration + its map
      moves together.
      done-when: `git show --stat HEAD` lists `src/deepreason/rules/crit.py`,
      `src/deepreason/signals.py`, `docs/map/CON-criticism-source.md` and
      `docs/map/SEAM-scheduler-x-rules.md` in one commit.

- [ ] 10. (S4) Prove the regression GREEN and record the mutation pair.
      done-when: `proof/s4_green.txt` holds the same pytest invocation as
      `proof/s4_red.txt`, now passing, and both files are tracked.

- [ ] 11. (S1, M1) Re-run the counterfactual probe against the CHANGED tree, so
      the ladder's measured effect is re-derived by the shipped code rather than
      by a hand-written formula inside the probe.
      done-when: `probes/p11_ladder_counterfactual_shipped.json` shows
      `dispatches_with_an_open_problem_new` computed by the shipped
      `premise_work_invited` and matching SPEC.md's M1 table (epoch 6: 10).

- [ ] 12. (S6) Write `ANSWERS.md`: the three answers at full length, in the
      brief's order, each with its measurements pasted, plus the R7 note.
      done-when: `grep -c "^## " ANSWERS.md` >= 3 and each of the three headings
      is present verbatim.

- [ ] 13. (S8) Write `PARKED.md`: the planted-presupposition probe (R8, unstarted
      by instruction), the batch-unanimity narrowing (M6), and the
      `PREMISE_INVITE_AFTER`-as-configuration tension (A4) — each as a
      ready-to-send prompt with route, one-goal statement, evidence pointers and
      end state.
      done-when: `grep -c "Ready-to-send prompt" PARKED.md` == 3.

- [ ] 14. (S6, S8) [COMMIT] Commit the artifacts.
      done-when: `git status --porcelain` shows no untracked file under the
      tranche directory.

- [ ] 15. (S5, all) Map check, FULL mode (not `--fast`: `--fast` reuses cached
      results and cannot catch a document this tranche's `src/` change broke).
      Run on an otherwise idle box — never concurrently with the gate.
      done-when: `python tools/docs_verify.py` failures <= 4 (C7 baseline: 3
      shallow-clone + 1 pre-existing falsified census), and
      `python tools/docs_verify.py --audit` reports no new unfailable check.

- [ ] 16. (S7, all) Full gate.
      done-when: `python -m pytest tests/ -q -n 4` output ends "N passed, 0
      failed" with N >= 4374, pasted into VALIDATION.md.

- [ ] 17. (all) [COMMIT] Push and confirm a clean tree.
      done-when: `git status --porcelain` is empty AND
      `git rev-parse HEAD origin/claude/deepreason-premise-invitation-7qs3kc`
      prints the same sha twice.
