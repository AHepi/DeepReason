# Checklist for: "Prose can refute" + the single-family path

Re-read REQUEST.md + SPEC.md before every step. Execute strictly in order.
One step per `dr-execute-step` invocation.

## Standing prohibition for EVERY step

No step may add or alter a manifest field, a state digest, event application
order, a qualification subject, or a replay-validation record format.
SPEC.md's budget says **frozen surfaces touched: none**. A step that turns out
to need one STOPS and reports; it does not proceed. Authority stays on
`Config` (`config.py`), never on the run manifest — that is the whole reason
this tranche is not a frozen-surface change.

## Call sites established before planning (so steps name real targets)

- `llm/adapter.py:609-613` `require_cross_family_judges` is the ONLY caller of
  `require_cross_family_judge_ensemble` (`llm/firewall.py:261`).
- `rules/crit.py:1287-1300` is the authority gate: `observe_only` observes,
  `trial_required` calls `run_argument_trial_from_case` from
  `deepreason.informal.trial`.
- `rules/crit.py:56` `_POLICY_AUTHORITIES = {"observe_only", "defended_trial"}`
  and `:87` maps `defended_trial` -> `trial_required`. Two vocabularies exist;
  any new value must be added consistently or deliberately not at all.

---

- [x] 1. (S6, S11) Capture the 42-root BEFORE baseline to the session
      scratchpad, recording per root: `valid`, `epistemic_checks_passed`,
      `len(state.att)`, and the count of `adjudication-blindness` findings.
      files: none (read-only script in the scratchpad)
      done-when: ~~the baseline file has 42 lines and `grep -c ERROR` is 0~~
      **CORRECTED at execution — the second clause was mis-specified.**
      done-when: 42 lines, and every ERROR line is
      `UnsupportedRunManifestVersionError` (the known pre-v6 set)

      Output:

          SWEEP COMPLETE: 42 roots -> .../scratchpad/sweep_BEFORE.txt
          lines: 42
          ERROR count: 11
          valid=False: 5 | blind=1: 26 | att>0: 5

          $ grep ERROR sweep_BEFORE.txt | cut -d: -f1 | sort | uniq -c
               11 UnsupportedRunManifestVersionError

      Why the criterion was wrong, recorded rather than quietly fixed: 11 of
      42 roots being unopenable pre-v6 was established three separate times
      earlier this session (INVESTIGATION.md, the adjudication-blindness
      GOAL.md, FEASIBILITY.md) and I wrote `0` into the criterion anyway. The
      first clause passed unchanged; the second is corrected to what the fact
      always was, and all 11 are verified to be the single expected exception
      type rather than assumed. The substance of the step — one complete,
      reusable baseline — is achieved, and the script is saved for verbatim
      re-run at step 15.

      Baseline shape for later comparison: 5 roots `valid=False`, 26 carrying
      `adjudication-blindness`, 5 with any attacks.

- [x] 2. (S5, S12) [COMMIT] Write the scratchpad-separation assertions:
      no scratch id in any warrant, attack edge, criticism pack or judge pack,
      and `rules/crit.py` imports nothing from `deepreason.scratch`.
      files: `tests/test_prose_refutation_boundaries.py` (new)
      done-when: `pytest tests/test_prose_refutation_boundaries.py -q -k scratch`
      reports all passed (these should be GREEN today; they pin, not fix)

      Output:

          $ pytest tests/test_prose_refutation_boundaries.py -q -k scratch
          .....                                        [100%]
          5 passed in 0.10s

      Five assertions, GREEN as predicted — they pin the boundary rather than
      move it:

        - `rules/crit.py` imports no `deepreason.scratch` module. The whole
          module is AST-walked, not grepped at the header, because a
          function-local import would pass a header check and still couple the
          two.
        - `rules/crit.py`'s only scratch mentions are `scratch_fence_seq`
          (lines 342, 583) — transactional ordering, not content. Any other
          scratch name appearing there now fails.
        - The criticism packs cannot be GIVEN scratch: `render_conj_pack` takes
          `scratch_context` (packs.py:322, correctly — conjecture is where the
          workshop belongs) and `render_crit_pack` / `render_batch_crit_pack`
          have no such parameter. Enforced by signature, so no future caller
          can pass one without changing this contract.
        - `informal/trial.py` imports no scratch module. This is the last link
          before a sustained prose case can change a status, so it is authority
          chain proper.
        - `rules/warrants.py` and `adjudication/edges.py` import no scratch
          module — the narrowest part of the chain.

- [ ] 3. (S10) Write the prompt byte-identity assertion: for identical inputs
      the rendered criticism and judge prompts are byte-identical with the new
      mode enabled and disabled, and contain no author or school label.
      files: `tests/test_prose_refutation_boundaries.py`
      done-when: the test exists and is RED only because the new mode value
      does not exist yet (paste the error naming the unknown value)

- [ ] 4. (S9) Write the author-school exclusion assertion: no criticism
      assignment is ever produced whose critic school equals its target's
      school, under both the old and the new mode.
      files: `tests/test_prose_refutation_boundaries.py`
      done-when: the old-mode half passes today (paste it); the new-mode half
      is RED for the same unknown-value reason as step 3

- [ ] 5. (S7) [COMMIT] Add the single-family predicate, derived from immutable
      leases exactly as `require_cross_family_judge_ensemble` derives families.
      files: `src/deepreason/llm/firewall.py`
      done-when: a new test shows True for one family, False for two, False for
      an empty lease set (fails closed) — paste all three

- [ ] 6. (S8) Add `require_cross_school_judge_ensemble`: >=2 judge seats from
      >=2 distinct SCHOOLS. `require_cross_family_judge_ensemble` is NOT
      modified.
      files: `src/deepreason/llm/firewall.py`
      done-when: accepts one family + two schools; raises on one family + one
      school; and `git diff` shows zero changed lines inside
      `require_cross_family_judge_ensemble`

- [ ] 7. (S8) [COMMIT] Make the ensemble choice select cross-school ONLY when
      the single-family predicate holds; cross-family governs otherwise.
      files: `src/deepreason/llm/adapter.py`
      done-when: with two families present the cross-school gate is not
      selected even when configured (paste the assertion); the existing
      cross-family tests still pass

- [ ] 8. (S4) Confirm the formal/informal boundary needs no code change:
      demonstrative outcomes are already status-changing under every mode and
      `programs.evaluable` is already the line (A1).
      files: `tests/test_prose_refutation_boundaries.py`
      done-when: a test shows prose cannot alter a target carrying an evaluable
      commitment, and can alter one that carries none — under the new mode

- [ ] 9. (S3) Give the refuting endpoint the full argument: the target's
      complete text (no excerpt marker) and its declared `Interface.refs`
      support chain. Scratch stays out (R5/R6).
      files: `src/deepreason/llm/packs.py`
      done-when: for a target exceeding the old budget the pack contains the
      whole text, no `HARNESS PACK EXCERPT` marker, every id in
      `target.interface.refs`, and no `SCR_` handle

- [ ] 10. (S1, S11) [COMMIT] Stop discarding the computed text authority mode,
      and add the single-family authority value to `Config`. Default unchanged
      at `observe_only`. No manifest field.
      files: `src/deepreason/authority.py`, `src/deepreason/config.py`
      done-when: `trial_authority_for` varies with the knob for every
      `AuthoritySurface`; non-text still returns `STATUS`; and
      `grep -rn "ARGUMENTATIVE_AUTHORITY\|require_distinct_families"
      src/deepreason/run_manifest.py` shows no new field

- [ ] 11. (S1, S11) Reconcile the two authority vocabularies at
      `rules/crit.py:56,87` (`_POLICY_AUTHORITIES` vs `_ARGUMENTATIVE_VALUES`)
      so the new value is accepted consistently or deliberately excluded.
      files: `src/deepreason/rules/crit.py`, `src/deepreason/authority.py`
      done-when: a test asserts the same value is accepted by both, or that the
      new value is rejected by the manifest-bound path with a typed reason

- [ ] 12. (S2) [COMMIT] Show the end-to-end result offline: a single-family run
      with the new mode produces `len(state.att) >= 1` and at least one
      `Status.REFUTED`, from a criticism whose target carries no evaluable
      commitment and whose critic school differs from the target's.
      files: `tests/test_prose_refutation_boundaries.py`
      done-when: that test passes (paste it)

- [ ] 13. (S3, S10) Re-run steps 3 and 4's assertions now that the mode exists.
      files: none
      done-when: the whole of `tests/test_prose_refutation_boundaries.py`
      passes, including the byte-identity halves that were RED

- [ ] 14. (all) Full gate: `pytest tests/ -q -n 4`
      done-when: output ends "N passed, 0 failed" — paste it. No assertion
      weakened anywhere (C2).

- [ ] 15. (S6, S11) Capture the AFTER sweep with the identical script from
      step 1 and diff.
      done-when: no root's `valid` changes and no root's `len(state.att)`
      changes; report any `epistemic_checks_passed` movement as a number

- [ ] 16. (all) [COMMIT] Push and confirm clean.
      done-when: `git status --porcelain` is empty AND the branch head is on
      origin

## Coverage

S1 -> 10, 11.  S2 -> 12.  S3 -> 9, 13.  S4 -> 8.  S5 -> 2.  S6 -> 1, 15.
S7 -> 5.  S8 -> 6, 7.  S9 -> 4.  S10 -> 3, 13.  S11 -> 1, 10, 15.  S12 -> 2.

## Risks carried from FEASIBILITY.md that steps must respect

- Step 12 is the one that could break a live run if done wrong: reusing the
  existing criticism-obligation records with author-equals-critic raises before
  the model is contacted. This tranche keeps author != critic (S9), so the
  hazard should not arise — step 4 is what proves it.
- The mechanical-checking defeat channel stays untouched (A7). If step 12's
  refutation turns out to come from that channel rather than from prose, the
  step has NOT demonstrated S2 and must say so.
