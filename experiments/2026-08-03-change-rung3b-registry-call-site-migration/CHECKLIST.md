# Checklist for: rung 3, tranche B — migrate the call sites through the registry
Re-read REQUEST.md + SPEC.md before every step. Execute strictly in
order. One step per dr-execute-step invocation.

Map preflight (recorded per dr-plan-steps rule 4b): `DR-CON-schools` and
`DR-SUB-scheduler`, joined by `DR-SEAM-schools-x-scheduler`. That seam
document was CREATED by Tranche A, so this tranche UPDATES it — rule
4c's "create it before the code steps" clause does not apply; the map
update bundles into the SAME commit as the code it describes (step 7),
per the map's own same-commit rule. `DR-INV-frozen-surfaces` re-read:
none of the five surfaces are touched by this design (A1 deliberately
avoids the `Config`-field shape that would have hit surface 4).

Planned, not to be discovered mid-flight: `SEAM-schools-x-scheduler.md`
lines 64-65 assert the migration has NOT happened
(`! grep -q "SCHOOL_POPULATION" ...` for `scheduler.py` and
`capture/ladder.py`). Both go FALSE at steps 2-3. Step 6 inverts them
and rewrites the now-false "What is deliberately absent" section, in the
same commit.

- [ ] 1. (S1) Add `_ACTIVE_BACKEND_ID = "default"` and an
      `active_backend()` helper to `src/deepreason/capture/schools.py`,
      returning `SCHOOL_POPULATION.resolve(_ACTIVE_BACKEND_ID).backend`.
      done-when: `python -c "from deepreason.capture.schools import active_backend, DefaultSchoolPopulationBackend; assert isinstance(active_backend(), DefaultSchoolPopulationBackend)"` exits 0.

- [ ] 2. (S2) Migrate `src/deepreason/scheduler/scheduler.py`'s two call
      sites — line 272 `schools.init_schools(harness, config)` and line
      1804 `schools.allocate(harness, problem, self.schools, config)` —
      to `schools.active_backend().init_schools(...)` / `.allocate(...)`.
      done-when: `test "$(grep -c 'schools.active_backend()' src/deepreason/scheduler/scheduler.py)" = 2` exits 0 AND `python -m pytest tests/test_schools.py tests/test_scheduler.py tests/test_rotation.py -q` ends "N passed, 0 failed" (paste it).

- [ ] 3. (S3) Migrate `src/deepreason/capture/ladder.py`'s four call
      sites (28, 73 `roster`; 39, 81 `reseed`) the same way.
      done-when: `test "$(grep -c 'schools.active_backend()' src/deepreason/capture/ladder.py)" = 4` exits 0 AND `python -m pytest tests/test_orbit.py tests/test_schools.py -q` ends "N passed, 0 failed" (paste it).

- [ ] 4. (S4) Migrate `src/deepreason/cli/main.py`'s three call sites
      (906, 1064 `roster`; 1068 `reseed`) and `src/deepreason/report.py`'s
      one (402 `roster`).
      done-when: `test "$(grep -c 'active_backend()' src/deepreason/cli/main.py)" = 3` AND `test "$(grep -c 'active_backend()' src/deepreason/report.py)" = 1` both exit 0 (paste both).

- [ ] 5. (S5) Verification-only: confirm no bare call site of the four
      named functions survives outside `capture/schools.py`, and that
      exactly one backend remains registered.
      done-when: `python -c "import pathlib,re; bad=[(p,l) for p in ('src/deepreason/scheduler/scheduler.py','src/deepreason/capture/ladder.py','src/deepreason/cli/main.py','src/deepreason/report.py') for l in pathlib.Path(p).read_text().splitlines() if re.search(r'schools(_mod)?\.(init_schools|roster|allocate|reseed)\(', l)]; assert not bad, bad; from deepreason.capture.schools import SCHOOL_POPULATION; assert SCHOOL_POPULATION.ids() == ('default',)"` exits 0.

- [ ] 6. (S6) Update `docs/map/SEAM-schools-x-scheduler.md`: INVERT the
      two `! grep -q "SCHOOL_POPULATION"` checks (lines 64-65) into
      positive assertions that the migration landed; rewrite the "What
      is deliberately absent" section (its no-call-sites-yet paragraph
      is now false — replace it with what is STILL deliberately absent,
      i.e. no second backend and no `Config` knob); add the migrated
      call sites to the "Where it is expressed" table; add
      `src/deepreason/scheduler/scheduler.py` to the document's `Owns:`
      header, exactly as that document's own "How to change it" step 4
      instructed.
      done-when: `python tools/docs_verify.py --fast` reports 0 failed (paste it).

- [ ] 7. (all) [COMMIT] Commit steps 1-6 together (helper, four migrated
      files, seam document) as one tranche commit — code and map in the
      SAME commit.
      done-when: `git log -1 --stat` shows `src/deepreason/capture/schools.py`,
      `src/deepreason/scheduler/scheduler.py`, `src/deepreason/capture/ladder.py`,
      `src/deepreason/cli/main.py`, `src/deepreason/report.py` and
      `docs/map/SEAM-schools-x-scheduler.md` all in the same commit;
      `git push -u origin claude/delivery-rungs-handover-m22sdy` succeeds
      (paste confirmation).

- [ ] 8. (S7) Add `tests/test_school_population_determinism.py`: two
      mock-endpoint `Scheduler` runs over identically-seeded harnesses
      and identical `Config` (the `tests/test_schools.py` pattern —
      `Scheduler(harness, adapter, config)` with
      `MockEndpoint(lambda p: _vs(...))`), run A through the migrated
      registry path and run B with the backend's delegation bypassed,
      asserting the two event logs are byte-identical. The test must
      prove it genuinely executed `Scheduler.__init__` (assert the
      scheduler's roster is non-empty in-test) — otherwise it repeats
      exactly the defect SPEC.md's Q3 identified in R7's named fixture.
      The precise bypass shape is settled here, at execution time, per
      SPEC.md's S7; FALLBACK if a clean bypass cannot be expressed:
      assert run A's log is byte-identical to a run whose call shape is
      reconstructed in the test itself, and record the deviation.
      done-when: `python -m pytest tests/test_school_population_determinism.py -q` ends "N passed, 0 failed", N >= 1 (paste it).

- [ ] 9. (all) [COMMIT] Commit step 8's new test file.
      done-when: `git log -1 --stat` shows
      `tests/test_school_population_determinism.py`; push succeeds
      (paste confirmation).

- [ ] 10. (all) Full map check: `python tools/docs_verify.py` AND
      `--audit` AND `--links`.
      done-when: all three report 0 failed / 0 findings / 0 dangling
      (paste all three).

- [ ] 11. (S8, R5) Full gate: `python -m pytest tests/ -q -n 4`,
      ISOLATED (nothing else running concurrently). Rerun once if only
      the known flake
      (`test_grounded_counterexample_recovery_does_not_invent_override_on_repeat`)
      fails, per C5.
      done-when: output ends "N passed, 0 failed" (paste it).

- [ ] 12. (S8, R6) Root sweep: `python tools/root_sweep.py`, ISOLATED,
      compared against the last accepted capture (42 rows, 11 ERROR, all
      `UnsupportedRunManifestVersionError`).
      done-when: sweep reports 42 roots and 11 ERROR lines, and diffs
      empty against the most recent prior capture in the scratchpad
      (paste both).

- [ ] 13. (all) [COMMIT] Final push and cleanliness check.
      done-when: `git status --porcelain` is empty AND branch head
      matches `origin/claude/delivery-rungs-handover-m22sdy` (paste both).
