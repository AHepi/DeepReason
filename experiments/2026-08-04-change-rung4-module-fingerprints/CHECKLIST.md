# Checklist for: rung 4 — every run records which modules built it
Re-read REQUEST.md + SPEC.md before every step. Execute strictly in
order. One step per dr-execute-step invocation.

Map ids this plan was scoped from (read in this order — seams before
subsystems, per the map's one ordering rule):
`DR-INV-frozen-surfaces` (first, always) → `DR-SEAM-harness-x-workflow`
(the closest precedent: it owns `harness.py`, `control_events.py` AND
`ontology/event.py`, i.e. exactly this change's shape) →
`DR-SEAM-harness-x-verification` (owns `harness.py`, `invariants.py`) →
`DR-SEAM-schools-x-scheduler` (owns `capture/schools.py`,
`scheduler/scheduler.py` — where the writer fires) → `DR-CON-schools`
(owns `capture/schools.py`, `scheduler/scheduler.py`,
`ontology/event.py`) → `DR-SUB-ontology`, `DR-SUB-harness`,
`DR-SUB-scheduler`.

Design under execution: SPEC.md's "Resolution of the DESIGN-AND-STOP",
items D1-D9 and S10-S13. **Reader before writer is the ordering
constraint this list exists to enforce** (R8, C12): steps 2-5 land and
prove the reader; the writer does not appear until step 9.

- [x] 1. (S5) Capture the sweep BASELINE on the pristine tree, before
      any `src/` edit. This is the "accepted capture" S5 diffs against;
      it cannot be taken after the change.
      done-when: `python tools/root_sweep.py <scratch>/sweep-before.txt`
      -> "SWEEP COMPLETE: 42 roots", and the file contains exactly 11
      `ERROR` lines (paste the count command's output)

      DONE 2026-08-04, on a tree `git status --porcelain` reported
      clean at head `35a74b46` (no `src/` edit had been made):

          SWEEP COMPLETE: 42 roots -> .../sweep-before.txt
          rows: 42
          ERROR rows: 11
          sha256: 9c092414321e12b97f631b59b98aa007e9505a289014a38c3a57b5bd9e050cd2
          --- error kinds ---
                2 ERROR UnsupportedRunManifestVersionError: ... schema version 1 ...
                8 ERROR UnsupportedRunManifestVersionError: ... schema version 2 ...
                1 ERROR UnsupportedRunManifestVersionError: ... schema version 3 ...

      Matches the documented baseline exactly (`DR-INV-frozen-surfaces`:
      42 roots, 11 ERROR, all `UnsupportedRunManifestVersionError` — not
      a failure). The capture file itself is session-local, so the
      **sha256 above is the durable anchor** (durable-test rule 1): if
      the container rolls back, re-run the sweep on a pristine tree and
      the digest must reproduce before step 19's diff means anything.
      No sweep capture is committed to the repo — no prior tranche
      commits one either (`git ls-files | grep sweep` finds none); the
      pasted digest is the tranche's evidence.

- [x] 2. (S3, S10, D1) Create `src/deepreason/module_events.py`: the
      typed payload models (`ModuleFingerprintV1`,
      `ModuleFingerprintsEventPayloadV1`, schema literal
      `module-fingerprints.v1`) and the absence-tolerant reader
      `recorded_module_fingerprints(harness)`. No wall-clock field in
      any model (durable-test rule 4). The reader uses
      `getattr(event, "module_fingerprints", None)` so it is correct
      BEFORE the field exists — that is what makes it a reader-first
      step rather than a rename of the writer.
      done-when: `python -c` opens a committed pre-change root
      read-only and `recorded_module_fingerprints` returns `()` on it

      DONE 2026-08-04. Reader result, over every git-tracked root:

          git-tracked roots            : 45
          opened, reader returned ()   : 31
          refused at open (pre-v6)     : 14
          payload schema               : module-fingerprints.v1
          module fingerprint_sha256    : 9a6411e64ec1a66d797ad49584ac37733dfcaba0056f459d44dbf03ca1e1e9b2
          payload digest               : ebe196411351a47abb87716a534c7d4e3cbd7b2648c4b29d1fb3cede4ce1825d
          key-order independent digest : True

      31 + 14 = 45 reproduces the documented census exactly (28 v6 + 3
      no-manifest open; 14 raise `UnsupportedRunManifestVersionError`).
      The 14 refusals are the HARNESS declining to open a pre-v6 root,
      not the reader failing on it — see PARKED.md P7.

      Environment finding while running C9's full mode the first time:
      `pytest` was absent from this container, so `docs_verify` reported
      **292 failed**, every one `-> No module named pytest`. Nothing to
      do with the documents. Installed `pytest`/`pytest-xdist` and
      re-ran; that re-run then failed on ONE test at its own
      `import jsonschema` — also undeclared. Installed too; both checks
      passed (`5 passed`). PARKED.md P6/P6a.

      C9's obligation for this `src/`-touching step, satisfied on the
      FULL mode (never `--fast`):

          docs_verify [full]: 50 documents, 803 checks, 4 workers
          docs_verify: 0 failed
          rc=0

      **Pre-writer gate baseline, recorded here because D9's
      fixture-drift prediction is measured against it.** Run with
      `module_events.py` present but referenced by nothing, so it is
      the count the writer must be judged against at step 18:

          3303 passed, 7 skipped in 599.88s (0:09:59)
          rc=0

      0 failed, and no flake needed a re-run (C5's known flake
      `test_grounded_counterexample_recovery_does_not_invent_override_on_repeat`
      passed first time).

- [x] 3. (S3, S13) Write `tests/test_module_fingerprints.py` with the
      READER tests only — absence is valid on committed roots (pin to
      `git ls-files` roots, durable-test rule 1; name the rung in the
      docstring) and the reader tolerates events with no such field.
      done-when: `python -m pytest tests/test_module_fingerprints.py -q`
      -> "N passed, 0 failed"

      DONE 2026-08-04:

          ........                                          [100%]
          8 passed in 57.04s

      Eight tests, all reader-side; no writer exists yet. Roots are
      taken from `git ls-files` only (durable-test rule 1) and the
      docstring names the rung. Two claims are kept SEPARATE on purpose
      — absence-is-valid, and the open/refuse census — so that a future
      change making roots unopenable cannot show up as a passing
      absence test. First run took 114s because each opened ~45
      recorded roots; an `lru_cache`d single sweep shared by both
      brought it to 57s without merging the two claims.

      Touches no `src/` file, so no map document and no C9 full
      `docs_verify` is owed by this step (that obligation is per
      `src/`-touching commit).

- [x] 4. (S3) [COMMIT] Mutation-prove the reader tests can fail
      (durable-test rule 3): make the reader raise on a missing
      attribute, watch the absence test go red, restore, re-run green.
      Commit the reader + its tests.
      done-when: the red run's failure line and the restored green run
      are both pasted, and `git log --oneline -1` shows the commit

      DONE 2026-08-04. Mutation: replace the reader's
      `getattr(event, "module_fingerprints", None)` with a direct
      attribute read — i.e. delete exactly the absence-tolerance R8
      demands. RED:

          E   AttributeError: 'Event' object has no attribute 'module_fingerprints'
          FAILED ...::test_every_committed_root_reads_as_having_no_module_fingerprints
          FAILED ...::test_the_census_of_committed_roots_is_unchanged
          FAILED ...::test_the_reader_tolerates_an_event_with_no_fingerprint_attribute
          3 failed, 5 passed in 5.32s

      The three that died are exactly the three absence claims; the
      five that survived are the digest/shape claims, which the
      mutation does not touch. That split is the evidence the tests
      are aimed at what they say they guard.

      Restored (`git diff --stat` empty — byte-identical to HEAD) and
      GREEN:

          ........                                          [100%]
          8 passed in 56.80s

      The equality assertions additionally ship with a PERMANENT
      companion mutation test in the suite,
      `test_a_different_module_produces_a_different_digest`, as
      durable-test rule 3 requires for equality tests.

- [x] 5. (S10, D3) Add the optional payload field to `Event` in
      `src/deepreason/ontology/event.py`:
      `module_fingerprints: ModuleFingerprintsEventPayloadV1 | None =
      Field(default=None, exclude_if=lambda value: value is None)`.
      Nothing else in that file.
      done-when: `python -c` shows an `Event` that does not set the
      field has NO `module_fingerprints` key in
      `model_dump_json(by_alias=True)` (absence is absence from the
      BYTES, not a null in them)

      DONE 2026-08-04. An `Event` that does not set the field:

          keys on an event that does not set the field:
          ['inputs', 'llm', 'outputs', 'rule', 'seq', 'state_diff', 'ts']

          module_fingerprints in serialized bytes : False
          field exists on the model               : True
          field is optional (not required)        : True
          attribute reads as None                 : True

      This is the whole basis of R8/C12 for this design: the field is
      absent from the BYTES, so no existing root's serialization moves
      and no old event becomes invalid. Import placed alphabetically in
      the existing block; nothing else in the file touched.

- [x] 6. (S3) Re-run step 3's reader tests unchanged now that the field
      exists — absence must still be valid, which is the half of R8
      that only becomes testable at this point.
      done-when: `python -m pytest tests/test_module_fingerprints.py -q`
      -> "0 failed", with no edit to the test file

      DONE 2026-08-04. `git diff --stat tests/test_module_fingerprints.py`
      is EMPTY (the file is unedited since step 4), and:

          ........                                          [100%]
          8 passed in 54.70s

      Absence stays valid now that the field exists -- the half of R8
      that only becomes testable at this point.

- [x] 7. (S3, S10) Prove no committed root's verdict moved by the field
      alone: `verify_root` on a committed root, compared to the same
      call on the pre-change tree.
      done-when: the verdict JSON (sorted keys) is byte-identical to
      the pre-change capture for at least three committed roots,
      including one v6 root and one that raises

      DONE 2026-08-04. Three roots chosen to span all three arms of the
      documented census (28 v6 / 14 raising / 3 no-manifest -- the
      census reproduced exactly by the capture script):

          experiments/2026-08-02-stress-triplet/home-orbit/runs/run-6472629dbc5d408a733d472040671752   (v6)
          experiments/bronze_feedback_v1_superseded_2026-07-14/observe_only            (raises)
          experiments/bronze_flat_2026-07-13/deepseek-v4-pro                           (no manifest)

      `verify_root` output, canonical JSON, sorted keys:

          sha256 BEFORE field: 62614bfcdbf494b2f3997c363a9a83ce024307ebc4718cbdea2ebeb16ac11f67
          sha256  AFTER field: 62614bfcdbf494b2f3997c363a9a83ce024307ebc4718cbdea2ebeb16ac11f67

      Identical. "BEFORE" was taken by stashing ONLY `event.py` so the
      comparison isolates the field rather than the whole tranche.
      `DR-INV-frozen-surfaces`' governing question -- "does any
      recorded root's `valid` or `att` move" -- answers no.

- [x] 8. (S3) [COMMIT] Commit the `Event` field with steps 5-7 evidence.
      done-when: `git log --oneline -1` shows it and
      `git diff --stat HEAD~1 -- src/deepreason/` names only
      `ontology/event.py`

      DONE 2026-08-04. C9's FULL `docs_verify` before this
      `src/`-touching commit:

          docs_verify [full]: 50 documents, 803 checks, 4 workers
          docs_verify: 0 failed
          rc=0

- [ ] 9. (S11, D6) Add the TWO declared `harness.py` hunks and no
      others: (i) the `record_module_fingerprints(payload)` appender
      committing `Rule.MEASURE` — no new `Rule` member (D4); (ii) the
      `module_fingerprints` keyword on `_commit`, forwarded verbatim
      into the `Event(...)` constructor. The harness validates the
      payload's SHAPE and computes nothing
      (`DR-SEAM-harness-x-workflow` step 5).
      done-when: `git diff -- src/deepreason/harness.py` shows exactly
      those two hunks, and an AST check proves `_apply_event` and the
      well-formedness path are byte-identical to `HEAD`

- [ ] 10. (S11) Assert R18's two exclusions mechanically, as a
      permanent test rather than a one-off eyeball: `_apply_event` has
      no `module_fingerprints` branch, and the payload materializes no
      state.
      done-when: a test in `tests/test_module_fingerprints.py` asserts
      the appended event changes no `Harness` state family, and it
      passes

- [ ] 11. (S3, S10) [COMMIT] Re-run step 7's committed-root comparison
      after the appender lands; commit the harness hunks.
      done-when: the three roots' verdicts are still byte-identical to
      the pre-change capture, pasted, and the commit exists

- [ ] 12. (S2, S10, D7) Wire the writer: `Scheduler.__init__` emits the
      stamp for `schools.active_backend()`, **unconditionally — NOT
      under the `config.N_SCHOOLS > 0` gate** (`scheduler.py:272-276`),
      because a zero-school run was still built by the registered
      backend.
      done-when: a `Scheduler` built with `N_SCHOOLS=0` still records
      exactly one fingerprint event

- [ ] 13. (S2) Write the writer test SPEC.md S2 names: a mock-endpoint
      `Scheduler` run's record carries the backend fingerprint with no
      capability exercised, and the recorded value equals
      `SCHOOL_POPULATION`'s pinned one.
      done-when: `python -m pytest tests/test_module_fingerprints.py -q`
      -> "0 failed", including the new writer test

- [ ] 14. (S13, D9) Replay/determinism test: reopen the run and compare
      applied state and the event log, scrubbing time-dependent fields
      RECURSIVELY (durable-test rule 4 — `Event.ts` and any nested
      `llm.ms`; never widen an exclusion on a guess).
      done-when: the replay-equality test passes twice in a row

- [ ] 15. (S2, S13) Mutation-prove the writer and replay tests
      (durable-test rule 3): perturb the recorded fingerprint, watch
      both go red, restore, green.
      done-when: the red output and the restored green run are pasted

- [ ] 16. (S10, all) Map update, in the same tranche as the behaviour
      it describes and NOT as a trailing docs step: give
      `src/deepreason/module_events.py` an owning document and record
      the new observable where the map already describes this seam —
      `DR-SEAM-harness-x-workflow` (owns `harness.py`,
      `ontology/event.py`), `DR-CON-schools` (owns `capture/schools.py`,
      `scheduler/scheduler.py`, `ontology/event.py`), and
      `DR-SEAM-schools-x-scheduler`. Add a `check:` line per
      `SCHEMA.md`, anchored to meaning not form (durable-test rule 2;
      never pin line numbers).
      done-when: every touched document's `Owns:`/`check:` lines are
      updated and `python tools/docs_verify.py --links` -> 0 failed

- [ ] 17. (S8, C9) FULL `python tools/docs_verify.py` — NOT `--fast`,
      which reuses cached results and cannot see a map document newly
      broken by a `src/` change (rung 3 evidence: commit `55b16ce9`,
      ERRATA E10). Plus `--audit` for vacuous checks.
      done-when: full run -> 0 failed, and `--audit` -> 0 findings
      (paste both)

- [ ] 18. (S4, S13, D9) FULL gate: `python -m pytest tests/ -q -n 4`
      (never bare `pytest`, per C5). Any fixture that moved must be a
      COUNT/position assertion predicted by D9; a content or replay
      test that moved is escalated, not edited. Known flake
      `test_grounded_counterexample_recovery_does_not_invent_override_on_repeat`
      may be re-run once before diagnosing (C5).
      done-when: output ends "N passed, 0 failed" (paste it), and any
      edited fixture is named against D9

- [ ] 19. (S5) Re-run the sweep on the changed tree and diff against
      step 1's baseline. `tools/root_sweep.py` is UNCHANGED at this
      point — the probe is step 22 and must not ride this commit (C13).
      done-when: `diff <scratch>/sweep-before.txt
      <scratch>/sweep-after.txt` -> empty, 42 rows, 11 ERROR

- [ ] 20. (S7, S11) Frozen-surface diff: everything except the
      authorized `harness.py` hunks must be empty.
      done-when: `git diff --stat <base>..HEAD --
      src/deepreason/capabilities/state.py src/deepreason/invariants.py
      src/deepreason/run_manifest.py src/deepreason/qualification.py`
      -> empty, and `src/deepreason/verification/report.py` untouched

- [ ] 21. (all) [COMMIT] Commit the writer + tests + map update with
      the full-gate line in the message; push with retry.
      done-when: `git status --porcelain` empty AND the branch head is
      on origin

- [ ] 22. (S6, S12, R20, C13) **Separate commit, `tools/root_sweep.py`
      ONLY, no `src/` file.** Add the sweep probe that actually READS
      the new observable via `recorded_module_fingerprints`, asserting
      the attribute exists before reading it (the tool's own probe
      rule; durable-test rule 5). Take its own before/after capture on
      an unchanged tree — extending the tool resets the byte-identity
      baseline, which is why it cannot ride step 21.
      done-when: `git show --stat HEAD` lists only
      `tools/root_sweep.py`; the probe's own before/after sweep on an
      unchanged tree is byte-identical; every root reports zero
      fingerprints (absence tolerated, proven rather than unexamined)

- [ ] 23. (S6) Mutation-prove the probe is not vacuous (durable-test
      rule 3): make `recorded_module_fingerprints` return a bogus
      value, watch the probe's output change, restore.
      done-when: the changed sweep line and the restored identical one
      are both pasted

- [ ] 24. (all) [COMMIT] Push the probe commit and confirm a clean
      tree.
      done-when: `git status --porcelain` empty AND branch head is on
      origin
