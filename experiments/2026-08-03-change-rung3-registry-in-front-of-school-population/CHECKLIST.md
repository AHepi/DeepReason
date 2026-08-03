# Checklist for: rung 3, tranche A — the school-population registry (build only)
Re-read REQUEST.md + SPEC.md before every step. Execute strictly in
order. One step per dr-execute-step invocation.

Map preflight (recorded per dr-plan-steps rule 4b): resolved to
`DR-CON-schools` (owns `capture/schools.py`, `scheduler/scheduler.py`,
others) and `DR-SUB-scheduler` (owns `scheduler/`) as the two sides;
both currently list `scheduler x schools` under `Seams-undocumented:`.
This tranche creates `DR-SEAM-schools-x-scheduler` (alphabetical:
schools < scheduler) per `docs/map/REC-change-a-seam.md` Step 7's
template. Per rule 4c, the seam document is written FIRST (steps 1-2),
before any code — writing the agreement down is how understanding is
tested, not a chore after the fact. `docs/map/INV-frozen-surfaces.md`
re-confirmed untouched by this tranche's design.

- [x] 1. (S5) Create `docs/map/SEAM-schools-x-scheduler.md` following
      `REC-change-a-seam.md`'s template: `Owns: src/deepreason/capture/
      schools.py` ONLY in this tranche (scheduler.py stays unclaimed —
      Tranche B adds it when the scheduler actually consumes the
      registry); `Sides: DR-CON-schools, DR-SUB-scheduler`; sections
      "The agreement," "Where it is expressed," "What is deliberately
      absent" (explicitly: no call site resolves through the registry
      yet — this is Tranche A, not an oversight), "How to change it,"
      "Traps." At least one checked claim proving the registry exists
      (forward-reference to S1's own symbols — acceptable since this
      step lands in the SAME commit as the code per step 6's bundling).
      done-when: file exists at
      `docs/map/SEAM-schools-x-scheduler.md` containing the string
      `DR-SEAM-schools-x-scheduler` in its header comment (`grep -q
      "DR-SEAM-schools-x-scheduler" docs/map/SEAM-schools-x-scheduler.md`).
      DONE. Output: `PASS`. Document forward-references
      `SchoolPopulationRegistry`/`DefaultSchoolPopulationBackend`/
      `SCHOOL_POPULATION` (steps 3-6 add these in the same commit);
      also includes checks proving the DELIBERATE absence of any
      `SCHOOL_POPULATION` reference in `scheduler.py`/`capture/
      ladder.py` today. Not committed yet — bundled at step 7.

- [x] 2. (S5) Update `docs/map/CON-schools.md` and `docs/map/SUB-
      scheduler.md`: remove `scheduler x schools` (respectively `schools
      x scheduler`... check the exact wording used in each file's own
      `Seams-undocumented:` line) from each document's
      `Seams-undocumented:` line, add `DR-SEAM-schools-x-scheduler` to
      each document's `Seams:` line.
      done-when: `grep -q "DR-SEAM-schools-x-scheduler" docs/map/CON-schools.md docs/map/SUB-scheduler.md` exits 0 AND neither file's
      `Seams-undocumented:` line still contains the schools/scheduler
      pair (paste both files' header lines to confirm).
      DONE. Output: `grep: PASS`. Both headers updated; `scheduler x
      schools` removed from both `Seams-undocumented:` lines, `DR-SEAM-
      schools-x-scheduler` added to both `Seams:` lines. Not committed
      yet — bundled at step 7.

- [ ] 3. (S1) Add to `src/deepreason/capture/schools.py`: the
      `SchoolPopulationBackend` `Protocol` (methods `fingerprint`,
      `init_schools`, `roster`, `allocate`, `reseed`, signatures per
      SPEC.md A1), the `SchoolPopulationRegistration` frozen dataclass,
      `SchoolPopulationRegistryError(ValueError)` and
      `UnknownSchoolPopulationBackend(SchoolPopulationRegistryError,
      KeyError)`, and the `SchoolPopulationRegistry` class (`register`,
      `get`, `resolve` alias, `ids`, `fingerprint`,
      `fingerprint_is_pinned`) — mirroring `verification/registry.py`'s
      shape exactly, adapted for schools' four differently-shaped
      methods.
      done-when: `python -c "from deepreason.capture.schools import SchoolPopulationRegistry, SchoolPopulationBackend, SchoolPopulationRegistration; assert callable(SchoolPopulationBackend.__dict__.get('init_schools')) and callable(SchoolPopulationBackend.__dict__.get('roster')) and callable(SchoolPopulationBackend.__dict__.get('allocate')) and callable(SchoolPopulationBackend.__dict__.get('reseed')) and callable(SchoolPopulationBackend.__dict__.get('fingerprint'))"` exits 0 AND `python -c "from deepreason.capture.schools import SchoolPopulationRegistry; r = SchoolPopulationRegistry(); assert hasattr(r, 'register') and hasattr(r, 'get') and hasattr(r, 'resolve') and hasattr(r, 'ids') and hasattr(r, 'fingerprint') and hasattr(r, 'fingerprint_is_pinned')"` exits 0.
      DONE. Output: `CHECK1_OK` / `CHECK2_OK`. One deliberate deviation
      from `verification/registry.py`'s exact shape: the fingerprint
      re-check lives inside `get()` itself (not a separate `verify()`
      call), since schools has no single dispatch verb to attach the
      check to — noted here as an intentional adaptation, matching
      A1's own "adapted for schools' four differently-shaped methods."
      Not committed yet — bundled at step 7.

- [ ] 4. (S2) Add `DefaultSchoolPopulationBackend` to
      `src/deepreason/capture/schools.py`: four methods delegating
      UNCHANGED to today's existing module-level `init_schools`/
      `roster`/`allocate`/`reseed` functions (those functions themselves
      are NOT modified); `fingerprint()` returns a small stable dict
      (e.g. `{"backend": "default", "stance_count": len(_STANCES)}`).
      done-when: `python -c "from deepreason.capture.schools import DefaultSchoolPopulationBackend; b = DefaultSchoolPopulationBackend(); fp = b.fingerprint(); assert fp['backend'] == 'default'"` exits 0.
      DONE. Output: `CHECK_OK`. Each method calls the module-level free
      function of the same name directly (no `self.` shadowing issue,
      since Python resolves the bare name inside a method body to the
      module global, not the class attribute). Not committed yet —
      bundled at step 7.

- [x] 5. (S2) Confirm the default backend's methods produce results
      identical to calling the bare module functions directly (the
      wrapper adds nothing) — a quick inline check ahead of S4's fuller
      test file, to catch a wiring mistake early rather than only in a
      larger test.
      done-when: a `python -c` snippet constructs a fixture `Harness` in
      a temp dir, calls both `schools.init_schools(harness, config)` and
      `DefaultSchoolPopulationBackend().init_schools(harness2, config)`
      against two identically-seeded harnesses, and asserts the two
      rosters are equal (paste the exact command and output — the
      concrete fixture construction is decided at execution time,
      matching existing test helpers in `tests/test_scheduler.py` or
      similar if one exists).
      DONE. Two identically-seeded `Harness` objects, `Config(N_SCHOOLS=4)`.
      Output:
      ```
      init_schools rosters equal: True
      roster equal: True
      ```
      No file modified this step (throwaway snippet, not saved).

- [ ] 6. (S3) Add the module-level singleton
      `SCHOOL_POPULATION = SchoolPopulationRegistry()` to
      `src/deepreason/capture/schools.py`, with
      `DefaultSchoolPopulationBackend()` registered under `"default"` at
      import time — mirroring `workloads/registry.py`'s `WORKLOADS =
      WorkloadRegistry()` singleton precedent.
      done-when: `python -c "from deepreason.capture.schools import SCHOOL_POPULATION; assert SCHOOL_POPULATION.ids() == ('default',)"` exits 0.
      DONE. Output: `CHECK_OK`. Not committed yet — bundled at step 7.

- [x] 7. (all) [COMMIT] Commit steps 1-6 together (new seam document,
      header updates, protocol, default backend, singleton) as one
      tranche commit — code and map in the SAME commit per R6.
      done-when: `git log -1 --stat` shows
      `docs/map/SEAM-schools-x-scheduler.md`, `docs/map/CON-schools.md`,
      `docs/map/SUB-scheduler.md`, and
      `src/deepreason/capture/schools.py` all in the same commit;
      `git push -u origin claude/delivery-rungs-handover-m22sdy`
      succeeds (paste confirmation).
      DONE. Commit `697a551a`, 8 files (also includes
      `SEAM-manifest-x-schools.md`'s Amendment 1 fix and this tranche's
      own REQUEST.md/SPEC.md/CHECKLIST.md ledger updates). Pushed
      cleanly: `5eaf4bcb..697a551a`.

- [x] 6a. (S7, amendment 1) Fix `docs/map/SEAM-manifest-x-schools.md:179`'s
      now-stale closed-world import-set check, broken by step 3's new
      imports to `capture/schools.py` (discovered running `docs_verify
      --fast` ahead of step 7's commit; see SPEC.md Amendment 1 and
      REQUEST.md Amendments). The invariant the check protects (schools.py
      cannot reach the manifest/firewall/Config) is NOT violated — only
      the literal closed-world set needed widening.
      done-when: `python tools/docs_verify.py --fast` 0 failed.
      DONE. Widened the check's `mods==` set to include the six new
      imports (`copy`, `typing`, `collections.abc`, `dataclasses`,
      `deepreason.canonical`, `deepreason.ontology.frozen`), added an
      explicit `assert not mods & {'deepreason.run_manifest',
      'deepreason.llm.firewall', 'deepreason.config'}` exclusion so the
      check's actual protective claim is now MORE explicit than before,
      not weaker. Also updated the prose paragraph above the check
      (which had the same stale "imports exactly json and
      deepreason.ontology" claim) for honesty. Output:
      ```
      docs_verify [fast]: 50 documents, 800 checks, 799 reused, 4 workers
      docs_verify: 0 failed
      ```
      Not committed yet — bundled at step 7.

- [ ] 8. (S4) Add `tests/test_school_population_registry.py`: registry
      mechanics coverage (register, get, unknown-name error,
      duplicate-registration error — mirroring `tests/
      test_verifier_registry.py`'s own coverage shape) plus the
      default-backend-equals-bare-functions equivalence tests for all
      four methods (`init_schools`, `roster`, `allocate`, `reseed`),
      at least 5 test functions total.
      done-when: `python -m pytest tests/test_school_population_registry.py -q` ends "N passed, 0 failed", N >= 5 (paste it) AND `python -m pytest tests/test_school_population_registry.py --collect-only -q` lists >= 5 test names (paste it).
      DONE. 9 test functions (4 registry-mechanics, 4 default-backend
      equivalence covering all four protocol methods, 1 module-singleton
      check). Output:
      ```
      .........                                                                [100%]
      9 passed in 0.29s
      ```
      Collection: 9 tests collected, all listed. Not committed yet —
      bundled at step 9.

- [x] 9. (all) [COMMIT] Commit step 8's new test file.
      done-when: `git log -1 --stat` shows
      `tests/test_school_population_registry.py`; push succeeds (paste
      confirmation).
      DONE. Commit `bd2151dc`, pushed cleanly: `74c577f1..bd2151dc`.

- [x] 10. (all) Map check: `python tools/docs_verify.py` (full) AND
      `python tools/docs_verify.py --audit` AND
      `python tools/docs_verify.py --links`.
      done-when: all three show 0 failed / 0 findings / 0 dangling
      (paste all three).
      DONE. Output:
      ```
      docs_verify [full]: 50 documents, 800 checks, 4 workers
      docs_verify: 0 failed
      docs_verify --audit: 0 finding(s)
      docs_verify --links: 0 dangling reference(s), 50 document(s)
      ```

- [x] 11. (S6, R5) Full gate: `python -m pytest tests/ -q -n 4`,
      ISOLATED (nothing else running concurrently — learned the hard
      way in rung 2 tranche 2's validation pass). Rerun once if only the
      known flake
      (`test_grounded_counterexample_recovery_does_not_invent_override_on_repeat`)
      fails, per C5.
      done-when: output ends "N passed, 0 failed" (paste it).
      DONE. Output: `3301 passed, 7 skipped in 632.73s (0:10:32)`. 0
      failed; exactly rung 2's 3292 baseline plus this tranche's 9 new
      tests. The known flake did not fire; no rerun needed.

- [x] 12. (S6, R6) Root sweep: `python tools/root_sweep.py`, ISOLATED,
      compared against the last accepted baseline (42 rows, 11 ERROR,
      all `UnsupportedRunManifestVersionError`). Since no reader logic
      changes in this tranche, this run IS the after-answer.
      done-when: sweep output has 42 rows, 11 ERROR (paste it, plus a
      diff against the most recent prior capture on disk if one is
      still present in the scratchpad).
      DONE. `SWEEP COMPLETE: 42 roots`; 11 ERROR lines; diffed against
      rung 2's own last accepted capture (`v_sweep.txt`) — empty diff,
      byte-identical. No committed root's verdict moved.

- [ ] 13. (all) [COMMIT] Final push and cleanliness check.
      done-when: `git status --porcelain` is empty AND branch head is
      on `origin/claude/delivery-rungs-handover-m22sdy` (paste both).
