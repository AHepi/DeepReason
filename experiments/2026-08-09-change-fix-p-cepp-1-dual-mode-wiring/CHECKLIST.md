# Checklist for: fix dual seat wiring and test with a short live run
State: next=1 blockers=none
Re-read REQUEST.md + SPEC.md before every step. Execute strictly in
order. One step per `dr-execute-step` invocation.

Map scoping (per SPEC.md's own preflight, re-confirmed here):
`DR-SUB-manifest` (`run_manifest.py`, `cli/doctor.py`), `DR-SUB-rules`
(`rules/conj.py`), `DR-SUB-workflow` (`workflow/profiles.py`),
`DR-SUB-verification` (`invariants.py`). Three touched pairs —
manifest×rules, manifest×verification, manifest×workflow — are listed
in `docs/map/INDEX.md`'s seam matrix as **undocumented**, not
uninteresting. This tranche's budget (SPEC.md) scopes the map update as
prose additions to the four EXISTING `SUB-*.md` documents (describing
the v6/v7 conjecturer-turn-contract dispatch mechanism each owns its
piece of), not new `SEAM-*.md` documents — a full seam write-up for
three newly-surfaced pairs is out of this tranche's ~120-190 line
budget and is PARKED as its own future map-closing tranche if the
operator wants it (recorded in PARKED.md at delivery).

- [ ] 1. (S1) Write the regression test for `run_manifest.py`'s three
      S1 sites (repair-grant dict, `is_conjecture` set, `scratch_write`
      check) BEFORE changing the source — it must FAIL against the
      current tree, proving it actually exercises the gap.
      done-when: `python -m pytest tests/test_v6_contract_schema_repair_policy.py -k v7 -q`
      shows the new test collected and FAILING (paste the failure).

- [ ] 2. (S1) Apply the three `run_manifest.py` source changes: the
      `ceilings` dict key (~line 2491) reads
      `control_plane_policy.contract_versions.conjecturer_turn_contract`
      instead of the literal `"conjecturer.turn.v6"`; the `is_conjecture`
      set (~line 2004-2007) and `scratch_write` check (~line 2020) both
      recognize `"conjecturer.turn.v7"` alongside `"conjecturer.turn.v6"`
      (a shared 2-element constant/tuple, not two independently
      maintained literals). Update `docs/map/SUB-manifest.md` in the
      SAME step: add a sentence to its existing prose naming the
      contract-version dispatch this function performs, and advance its
      `Verified-at:` only if its own `check:` commands are re-run (they
      are, at step 6).
      done-when: `python -m pytest tests/test_v6_contract_schema_repair_policy.py -k v7 -q`
      now PASSES (paste it), AND `python -m pytest tests/test_v6_contract_schema_repair_policy.py tests/test_v6_contract_schema_repair_runtime.py tests/test_v6_route_seat_behavioral_capability_plan.py tests/test_v6_route_seat_behavioral_capability_runtime.py -q`
      is unchanged-green (0 failed, same count as before this step).

- [ ] 3. (S1) [COMMIT] Commit S1 with `tools/diff_budget.py` run against
      the tranche's base commit and pasted.
      done-when: `git log -1 --oneline` shows the S1 commit AND the
      diff-budget tool's `DIFF_BUDGET_RESULT_V1.verdict` is pasted and
      is not `EXCEEDED`.

- [ ] 4. (S2) Write the regression test for `rules/conj.py`'s five S2
      sites (a v7-configured conjecture turn mints a
      `"conjecturer.turn.v7"`-contracted commitment, not v6) BEFORE
      changing the source — it must FAIL against the current tree
      (either at the `expected_contract` `ValueError`, or by minting the
      wrong contract id if that guard is bypassed some other way; paste
      whichever failure actually occurs).
      done-when: the new test is collected and FAILING, pasted output
      showing which of the two failure modes fired.

- [ ] 5. (S2) Apply the five `rules/conj.py` source changes: capture the
      manifest's configured `conjecturer_turn_contract` once into a new
      local variable where `control`/`active_v6` are already resolved;
      `expected_contract` (~line 730-742) accepts that captured value for
      schema_version 6 instead of the hardcoded literal; `effective_contract`
      (~line 2210-2218) and the three atomic-decomposition bookkeeping
      sites (~lines 946, 1018, 1874) all reference the SAME captured
      variable instead of re-hardcoding `"conjecturer.turn.v6"`
      independently. Update `docs/map/SUB-rules.md` in the same step
      (one sentence: `rules/conj.py` reads the manifest's configured
      conjecturer-turn contract version rather than assuming v6).
      done-when: the S2 regression test from step 4 now PASSES (paste
      it), AND `python -m pytest tests/test_v6_conjecture_component_atomicity.py tests/test_v6_conjecture_scratch_consumption.py tests/test_v6_context_continuation.py tests/test_v6_controller3_replay_verification.py tests/test_v6_engaged_public_defaults.py tests/test_v6_engaged_repair_verification.py tests/test_v6_transaction_qualification.py -q`
      is unchanged-green.

- [ ] 6. (S2) [COMMIT] Commit S2 with `tools/diff_budget.py` pasted.
      done-when: same shape as step 3, for S2's diff.

- [ ] 7. (S3) Write the regression test for `workflow/profiles.py`'s
      four S3 sites (a `WorkflowControlProfileV1` with
      `conjecturer_contract_id="conjecturer.turn.v7"` validates and
      exposes the same capability outcomes a v6-configured profile
      does) BEFORE changing the source — it must FAIL (a
      `pydantic.ValidationError`) against the current tree.
      done-when: the new test is collected and FAILING with a
      `ValidationError`, pasted.

- [ ] 8. (S3) Apply the four `workflow/profiles.py` source changes: widen
      `WorkflowControlProfileV1.conjecturer_contract_id`'s `Literal`
      (~line 74-79) to admit `"conjecturer.turn.v7"`; widen the two
      membership-set checks (~lines 109-113, 154-158) the same way.
      Update `docs/map/SUB-workflow.md` in the same step (one sentence
      on the same dispatch mechanism, workflow's side of it).
      done-when: the S3 regression test from step 7 now PASSES (paste
      it), AND `python -m pytest tests/test_workflow_reducer_c0.py tests/test_workflow_control_replay_c1.py -q`
      is unchanged-green.

- [ ] 9. (S3) [COMMIT] Commit S3 with `tools/diff_budget.py` pasted.
      done-when: same shape as step 3, for S3's diff.

- [ ] 10. (S4) Write the regression test for `invariants.py`'s two S4
      sites (a v7-authored root's replay validation does not raise the
      `"conjecture-turn"` violation reserved for an unauthorized
      contract) BEFORE changing the source — it must FAIL (or the
      violation must fire) against the current tree, using a minimal
      fixture (no live call), adapted from whatever existing fixture
      proves the same for v6.
      done-when: the new test is collected and FAILING (violation
      fires when it should not), pasted.

- [ ] 11. (S4) Apply the two `invariants.py` source changes: widen both
      membership-set checks (~lines 1192, 2987) to admit
      `"conjecturer.turn.v7"`. Update `docs/map/SUB-verification.md` in
      the same step (one sentence: replay validation authorizes both
      conjecturer-turn contract versions a v6-schema manifest may
      configure).
      done-when: the S4 regression test from step 10 now PASSES (paste
      it), AND `python -m pytest tests/test_scratch_provenance_refs.py tests/test_v6_transaction_qualification.py tests/test_chaos_invariants.py tests/test_invariant_call_outcomes.py tests/test_persistence_invariants.py tests/test_replay.py tests/test_replay_code.py tests/test_replay_formal.py tests/test_replay_reasoning.py -q`
      is unchanged-green.

- [ ] 12. (S4) [COMMIT] Commit S4 with `tools/diff_budget.py` pasted
      AND the cumulative diff against the tranche's base commit
      (`781ad6811`), confirming the running total is still within
      SPEC.md's ~120-190 line estimate (report the actual number either
      way — an honest overage is not a stop, an unreported one is).
      done-when: same shape as step 3, plus the cumulative-diff number
      pasted.

- [ ] 13. (all) Root sweep before/after — the frozen-surface instrument
      (`INV-frozen-surfaces.md`): run `python tools/root_sweep.py
      /tmp/root_sweep_after_p_cepp_1.txt` and diff against a sweep taken
      on the pre-change tree (checkpoint from before step 1, or
      `git stash`+sweep+`git stash pop` if no prior capture exists).
      done-when: the diff shows zero changes to any root's `valid`,
      `epistemic_checks_passed`, `len(state.att)`, or adjudication-
      blindness count (paste "0 differences" or the exact diff if
      nonzero, which would be a STOP, not a thing to explain away).

- [ ] 14. (all) Map check: `python tools/docs_verify.py`
      done-when: 0 failed (paste the summary line).

- [ ] 15. (all) Full gate: `pytest tests/ -q -n 4`
      done-when: output ends "N passed, 0 failed" (paste it in full).

- [ ] 16. (all) [COMMIT] Push and confirm clean tree.
      done-when: `git status --porcelain` is empty AND
      `git log origin/claude/cp1m-stratification-retrodiction-wae6g1..HEAD`
      is empty (branch head matches origin).

R2's live-run test is NOT a CHECKLIST step here — `dr-validate-change`
and the live run happen after every step above is checked, per the
routing table ("All steps checked, no VALIDATION.md" → `dr-validate-change`).
The live run is this tranche's own R2 obligation, executed and reported
in `VALIDATION.md`/a dedicated live-run log before `dr-deliver-change`.
