# Checklist for: "Take this particular task out of the hands of the machine"

State: next=1 blockers=none

Re-read REQUEST.md (including Amendment 1) + SPEC.md before every step.
Execute strictly in order. One step per `dr-execute-step` invocation.

Map ids this plan was built on (`dr-drive-harness` §4; same set REQUEST.md
recorded at capture, plus the one this tranche creates):
`DR-INV-frozen-surfaces`, `DR-SUB-llm`, `DR-CON-seats`,
`DR-CON-packs-and-token-economy`, `DR-SUB-scheduler`, `DR-SUB-manifest`,
`DR-SEAM-llm-x-manifest`, `DR-SEAM-llm-x-verification`,
`DR-SEAM-llm-x-workflow`, `DR-SEAM-llm-x-scheduler`,
`DR-SEAM-schools-x-scheduler` (it owns the module-fingerprint checks S4
touches), and **`DR-CON-model-profiles`, created by step 4 of this plan**.

Baseline for every mutation proof: `git rev-parse HEAD` recorded at step 1,
before any source change. Pre-authorized red baselines (C6), to be recorded and
not stopped on: the `bc`-dependent map check, and
`test_the_shipped_qualification_subject_digest_does_not_move`.

---

- [ ] 1. (all) Record the pre-change baseline the mutation proofs detach to,
      and the two pre-authorized red baselines as they stand BEFORE any edit.
      done-when: `experiments/2026-09-01-change-model-profile-registry/BASELINE.txt`
      exists containing `production_base=<40-hex>` from `git rev-parse HEAD`,
      the output of `python -m pytest tests/test_qualification_subject.py -q
      -k shipped_qualification_subject_digest_does_not_move`, and the output of
      `python tools/docs_verify.py 2>&1 | tail -20`.

- [ ] 2. (S1) Write `tests/test_model_profiles_document.py` — the document
      parser's own tests, before the parser exists: one fenced block parses;
      zero blocks is a typed error; TWO blocks is a typed error; an unknown
      field is rejected (`extra="forbid"`); a model id with a colon round-trips;
      prose around the block is ignored.
      done-when: `python -m pytest tests/test_model_profiles_document.py -q`
      exits non-zero with `ModuleNotFoundError: No module named
      'deepreason.model_profiles'` (RED for the right reason, pasted).

- [ ] 3. (S1) Create `src/deepreason/model_profiles/document.py` and
      `src/deepreason/model_profiles/__init__.py`: `ModelProfileV1`,
      `ReasoningFactsV1`, `parse_document`, `ModelProfileError`.
      done-when: `python -m pytest tests/test_model_profiles_document.py -q`
      ends `N passed, 0 failed` (pasted).

- [ ] 4. (S1, S8) Create `docs/map/CON-model-profiles.md` — the concept
      document, written NOW rather than at the end, because writing the
      agreement down is how the remaining steps find out whether it is
      understood. Full `SCHEMA.md` anatomy; `Seams:` naming only documents that
      exist; every load-bearing claim carrying a column-0 `check:`.
      done-when: `python tools/docs_verify.py --links` exits 0 AND
      `python tools/docs_verify.py --audit 2>&1 | grep -c
      "CON-model-profiles"` is 0 (no vacuous or unparseable check in the new
      document).

- [ ] 5. (S1) Write `tests/test_model_profile_registry.py` FIRST HALF — the
      registry's resolution tests: `profiles_root` honours `DEEPREASON_HOME`;
      an installed document resolves by its declared `model_id` and not by its
      directory name; an absent model resolves to `None`, never an exception;
      `register`/`unregister` are in-process and write no file; two documents
      declaring the same id is a typed error naming both paths.
      done-when: `python -m pytest tests/test_model_profile_registry.py -q`
      exits non-zero for a missing-symbol reason (pasted).

- [ ] 6. (S1) [COMMIT] Create `src/deepreason/model_profiles/registry.py` and
      export the declared interface from `__init__.py`.
      done-when: `python -m pytest tests/test_model_profiles_document.py
      tests/test_model_profile_registry.py -q` ends `N passed, 0 failed`, AND
      SPEC.md item S1's `accept` snippet exits 0 (both pasted).

- [ ] 7. (S2) Write the S2 half of `tests/test_model_profile_registry.py`: the
      extraction leg sends the profile's declared value; `plan_split` raises
      `TypeError` when `profile` is omitted; `REASONING_OFF` and
      `reasoning_disabled` are absent from the tree.
      done-when: `python -m pytest tests/test_model_profile_registry.py -q -k
      "extraction or absent or required"` exits non-zero (pasted).

- [ ] 8. (S2) Retire `REASONING_OFF` and `reasoning_disabled` from
      `src/deepreason/llm/providers.py`.
      done-when: `grep -rn "REASONING_OFF\|def reasoning_disabled" src/ tests/
      docs/ tools/ scripts/` prints nothing and exits 1.

- [ ] 9. (S2, S3) Change `src/deepreason/llm/split.py`: `plan_split` takes a
      required keyword-only `profile`; the extraction value comes from the
      profile; add `NOTICE_MODEL_PROFILE_MISSING` and
      `NOTICE_PROFILE_DECLARES_NO_REASONING`; the `auto`-mode thinking-off test
      becomes profile-informed.
      done-when: SPEC.md item S3's `accept` snippet exits 0 (pasted).

- [ ] 10. (S2) Change `src/deepreason/llm/adapter.py::_split_plan` to resolve
      the profile from `lease.route.model` through
      `deepreason.model_profiles.resolve` and pass it.
      done-when: `python -c "import inspect; from
      deepreason.llm.adapter import LLMAdapter; s =
      inspect.getsource(LLMAdapter._split_plan); assert 'model_profiles' in s
      and 'profile=' in s"` exits 0.

- [ ] 11. (S2, S3) Update the tests the census predicted would move:
      `tests/test_split_budget_protocol.py`, `tests/test_providers.py`,
      `tests/test_split_leg_recording.py`. Fixtures may be updated only where
      SPEC.md S2/S3 predicted the move; no assertion is weakened.
      done-when: `python -m pytest tests/test_split_budget_protocol.py
      tests/test_providers.py tests/test_split_leg_recording.py
      tests/test_model_profile_registry.py tests/test_model_profiles_document.py
      -q` ends `N passed, 0 failed` (pasted).

- [ ] 12. (S8) Update `docs/map/SUB-llm.md`, `docs/map/CON-seats.md` and
      `docs/map/INDEX.md` in THIS step, i.e. in the same commit as the
      behaviour change — the entry-points check at SUB-llm.md:102, the split
      rows, the `plan_split` call in CON-seats.md:138, the Traps entry at
      SUB-llm.md:244-255 REWRITTEN in place (never deleted) plus a new Traps
      entry naming P-S1 M-1/M-16 and P-A1 run `4565139800f5ca02`, and INDEX.md's
      concept-table and routing rows for `DR-CON-model-profiles`.
      done-when: `python tools/docs_verify.py` ends with 0 failed, or fails
      ONLY on the pre-authorized `bc` check recorded in BASELINE.txt (pasted).

- [ ] 13. (S2, S3) [COMMIT] Commit steps 7-12 as one behaviour change with its
      map.
      done-when: `git status --porcelain` is empty and `git log --oneline -1`
      shows the commit.

- [ ] 14. (S2, S3, S7) Produce `MUTATION_RED.txt` for S2 and S3: detach the
      `production_base` tree from BASELINE.txt, copy the NEW test files in
      byte-unchanged, run them against the OLD source.
      done-when: `MUTATION_RED.txt` exists in `MUTATION_PROOF_V1` format with
      `phase=RED`, `production_base=`, `test_file_sha256.<path>=` for each test
      file, `command=`, `exit=1`, and the pasted failure lines.

- [ ] 15. (S2, S3, S7) Produce `MUTATION_GREEN.txt`: the same byte-identical
      test files against the current tree.
      done-when: `MUTATION_GREEN.txt` exists in the same format with
      `phase=GREEN`, `exit=0`, the SAME `test_file_sha256` values as
      MUTATION_RED.txt, and the pasted pass line.

- [ ] 16. (S4) Write the S4 test: the module-fingerprints event carries a
      second row with `registry == "model-profiles"`; zero installed profiles
      still produces a row; the school-population row is unchanged.
      done-when: `python -m pytest tests/test_model_profile_registry.py -q -k
      record_stamp` exits non-zero (pasted).

- [ ] 17. (S4) [COMMIT] Change
      `src/deepreason/scheduler/scheduler.py::_record_module_fingerprints` to
      append the `model-profiles` row, and check the map documents the census
      flagged (`SEAM-schools-x-scheduler.md`, `CON-schools.md:93`,
      `CON-seats.md:98`) for any that pins the module-list LENGTH.
      done-when: SPEC.md item S4's `accept` snippets exit 0 AND
      `python -m pytest tests/test_model_profile_registry.py -q` ends
      `N passed, 0 failed` (pasted).

- [ ] 18. (S5) Write `docs/model-profiles/README.md` and the glm-5.3 document
      `docs/model-profiles/glm-5.3/agent.md` — the one that answers R1. Every
      declared value cites its evidence by `git show <sha>:<path>`, never a
      moving branch head; a value the record does not measure is ABSENT.
      done-when: `python -c "from deepreason.model_profiles.document import
      parse_document; import pathlib;
      p=parse_document(pathlib.Path('docs/model-profiles/glm-5.3/agent.md').read_text());
      assert p.reasoning.extraction_value=='low' and
      p.reasoning.thinking_disablable is False and p.can_compact is False and
      p.evidence"` exits 0.

- [ ] 19. (S5) [COMMIT] Write the remaining four documents: `glm-5.2`,
      `deepseek-v4-pro:0813`, `qwen3.5:397b`, `gpt-oss:120b`.
      done-when: SPEC.md item S5's `accept` snippet exits 0 (pasted).

- [ ] 20. (S6) Write `scripts/model_profile_probe.py` with `--self-test` and
      `--offline`, and a recorded fixture under the tranche directory.
      done-when: `python scripts/model_profile_probe.py --self-test` exits 0
      AND the offline run against a fixture mutated to contradict one declared
      claim exits NON-ZERO (both pasted — a probe that cannot fail is not a
      probe, `SCHEMA.md`'s own rule applied here).

- [ ] 21. (S6) [COMMIT] Wire the probe command into each document's `probe:`
      field.
      done-when: `python -c "from deepreason.model_profiles.document import
      parse_document; import pathlib; ps=[parse_document(p.read_text()) for p
      in pathlib.Path('docs/model-profiles').glob('*/agent.md')]; assert
      all(p.probe for p in ps), [p.model_id for p in ps if not p.probe]"`
      exits 0.

- [ ] 22. (S7) Complete `tests/test_model_profile_registry.py` with the four
      architecture checks, each with its positive anchor.
      done-when: `python -m pytest tests/test_model_profile_registry.py -q`
      ends `N passed, 0 failed` (pasted).

- [ ] 23. (S7) Produce `MUTATION_RED_ARCH.txt` / `MUTATION_GREEN_ARCH.txt`:
      plant a bypass (a per-model reasoning literal reintroduced into
      `llm/split.py`), show the architecture test RED, revert, show it GREEN.
      done-when: both files exist in `MUTATION_PROOF_V1` format with the same
      `test_file_sha256`, `exit=1` then `exit=0` (pasted), and
      `git status --porcelain` shows the planted bypass reverted.

- [ ] 24. (S7) [COMMIT] Commit steps 22-23.
      done-when: `git status --porcelain` is empty.

- [ ] 25. (all) Map check, run ALONE on an otherwise idle box
      (`dr-drive-harness` §5b: never concurrently with another worker-spawning
      instrument): `python tools/docs_verify.py` then
      `python tools/docs_verify.py --audit` then
      `python tools/docs_verify.py --links`.
      done-when: 0 failed except the pre-authorized `bc` check recorded in
      BASELINE.txt; `--audit` reports no new vacuous or unparseable check;
      `--links` exits 0 (all pasted).

- [ ] 26. (all) Wheel smokes — NO gate runs them, and this tranche adds a
      console-visible surface (`scripts/model_profile_probe.py`) and a new
      package directory, so the pins are re-checked here rather than left to
      rot: `python scripts/wheel_smoke.py` and
      `python -u scripts/wheel_operational_smoke.py`.
      done-when: both exit 0, or a pin is updated in this same step and both
      then exit 0 (pasted).

- [ ] 27. (all) Full gate, alone on an idle box: `python -m pytest tests/ -q -n 4`.
      done-when: output ends `N passed, 0 failed`, or fails ONLY on
      `test_the_shipped_qualification_subject_digest_does_not_move` recorded as
      already red in BASELINE.txt (pasted in full).

- [ ] 28. (all) [COMMIT] Push and confirm clean tree.
      done-when: `git status --porcelain` is empty AND `git rev-parse HEAD` ==
      `git rev-parse origin/claude/model-profile-registry-opkgal`.
