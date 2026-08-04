# Checklist for: rung 5 — one deliberately dumb alternative, swapped in
Re-read REQUEST.md + SPEC.md before every step. Execute strictly in
order. One step per dr-execute-step invocation.

Map ids this plan was scoped from (seams before subsystems, per the
map's one ordering rule): `DR-INV-frozen-surfaces` (first, always) →
`DR-SEAM-schools-x-scheduler` (owns `capture/schools.py`,
`scheduler/scheduler.py`, `capture/ladder.py` — the seam rung 5 exists
to exercise, and whose "How to change it" step 1 binds C9) →
`DR-CON-schools` (owns `capture/schools.py`, `scheduler/scheduler.py`,
`ontology/event.py`, `module_events.py`) → `DR-SUB-scheduler`,
`DR-SUB-verification`.

Design under execution: SPEC.md items S1-S13, measurements M1-M5,
assumptions A1-A4. Target files: `src/deepreason/capture/schools.py`
and tests only. **No frozen surface is forecast; any contact discovered
mid-execution is a STOP for the operator's words (C10), not a judgement
call.**

The tranche's LAST step is a mandatory stop (R13), not a delivery.

- [ ] 1. (S9) Confirm the sweep baseline still reproduces on the
      pristine tree BEFORE any `src/` edit, against rung 4's committed
      5-field digest. A container rollback between tranches would
      invalidate every later comparison silently.
      done-when: `python tools/root_sweep.py <scratch>/r5-before.txt`
      -> 42 rows, 11 ERROR, sha256
      `6d6c3366c821d4555a8a4866c6a208c2b5d08db704e8f13c1611c7c5a74fd525`

- [ ] 2. (S2, S3, A1, M2, M2a) Add `RoundRobinSchoolPopulationBackend`
      to `src/deepreason/capture/schools.py` and register it as
      `"round-robin"`. It overrides `allocate` ONLY — rotating on a
      stable function of the problem id, never on call order or instance
      state — and delegates the other four operations to the same module
      functions the default delegates to. Its `fingerprint()` names the
      backend so rung 4's stamp distinguishes it.
      done-when: `SCHOOL_POPULATION.ids() == ("default", "round-robin")`
      and `allocate` returns the same list on a repeat call and from a
      fresh instance

- [ ] 3. (S3) Tests for step 2's determinism claim, mutation-proved:
      the round-robin allocation is a function of (log, config) alone.
      Include the companion mutation the durable-test doctrine requires
      for an equality assertion — a call-order-dependent variant must
      fail the comparison.
      done-when: `python -m pytest tests/test_rung5_alternative_backend.py -q`
      -> 0 failed, and the call-order variant demonstrably fails

- [ ] 4. (S4, M3) Add the scoped selection to `capture/schools.py`: it
      overrides `_ACTIVE_BACKEND_ID` for the duration of a run and
      restores it after, refusing an unregistered name BEFORE mutating
      anything. **No `Config` import, no `os` import** — a map check
      pins the first and M3 depends on both.
      done-when: inside the scope `active_backend()` resolves the
      alternative and outside it resolves `"default"`; an unknown name
      raises `UnknownSchoolPopulationBackend` with the selection
      untouched; the selection is restored when the body raises

- [ ] 5. (S4) Tests for step 4, including the raise-and-restore path —
      a selection that leaks across tests would corrupt every later test
      in the same process, which is the specific hazard of a module
      global.
      done-when: `python -m pytest tests/test_rung5_alternative_backend.py -q`
      -> 0 failed, including a test asserting restoration after an
      exception

- [ ] 6. (S5, S6, A2, A4) The offline proof run: a mock-endpoint
      `Scheduler` run under the alternative, in `tmp_path`, asserting
      the run COMPLETES and `verify_root(root)["violations"] == []`, and
      that the root records `module_id == "round-robin"` via rung 4's
      stamp. Epistemic quality is NOT asserted (A4).
      done-when: the test passes, and the same test under the default
      records `"default"`

- [ ] 7. (S7, C11) Prove the DEFAULT path unchanged in A3's reading:
      `tests/test_school_population_determinism.py` passes UNMODIFIED.
      If it needs an edit, that is a FAIL of R6, not a fixture update.
      done-when: `git diff --stat tests/test_school_population_determinism.py`
      is EMPTY and the file passes

- [ ] 8. (S11, C10) Map update in the same commit as the behaviour:
      `DR-SEAM-schools-x-scheduler` (a second registered backend now
      exists — its "How to change it" step 1 and its single-entry check
      `len(SCHOOL_POPULATION.ids()) == 1` MOVE) and `DR-CON-schools`.
      Add a check at column 0 for the new behaviour, anchored to meaning
      not form.
      done-when: `python tools/docs_verify.py --links` -> 0 dangling,
      and the single-entry check is updated rather than deleted

- [ ] 9. (S10, C8) FULL `python tools/docs_verify.py` — never `--fast`
      alone — plus `--audit`.
      done-when: full run 0 failed AND `--audit` 0 findings (paste both)

- [ ] 10. (S8) FULL gate: `python -m pytest tests/ -q -n 4` (never bare
      `pytest`, per C5). Baseline to beat: 3323 passed, 0 failed. Any
      test that moves must be explained, not edited.
      done-when: output ends "N passed, 0 failed" (paste it)

- [ ] 11. (S9) Re-run the sweep and diff against step 1's capture.
      `tools/root_sweep.py` is UNCHANGED this tranche (S12).
      done-when: empty diff, 42 rows, 11 ERROR

- [ ] 12. (S12) Confirm no new typed-record observable was added, so no
      new sweep probe is owed — rung 5 is the first CONSUMER of rung 4's.
      done-when: `git diff` adds no `Event` field, no record type, no
      `verify_root` finding, and `tools/root_sweep.py` is untouched

- [ ] 13. (all) Frozen-surface diff must be EMPTY — this tranche has NO
      authorization for any surface, unlike rung 4.
      done-when: `git diff --stat <base>..HEAD -- capabilities/state.py
      harness.py invariants.py run_manifest.py qualification.py
      verification/ config.py` -> empty

- [ ] 14. (all) [COMMIT] Commit and push; run `dr-validate-change`.
      done-when: `git status --porcelain` empty AND branch head on
      origin

- [ ] 15. (S13, R2, R13) **MANDATORY STOP.** Deliver the offline work
      and ASK THE OPERATOR FOR CREDENTIALS for the live A/B. Do not
      create, read, or commit any credential file; do not start a live
      run.
      done-when: DELIVERY.md ends with the credential request, and
      `git log -p` for this tranche contains no key material
