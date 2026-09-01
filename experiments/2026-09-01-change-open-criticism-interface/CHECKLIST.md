# Checklist for: contribution-only criticism-source socket

State: next=10 blockers=docs_verify returned 7; baseline disposition required

Map scope: `DR-CON-criticism-source`, `DR-CON-conjecture-kinds`,
`DR-CON-authority`, and the unchanged boundary
`DR-SEAM-adjudication-x-authority`; frozen disposition from
`DR-INV-frozen-surfaces` is `CLEAR`.

Re-read `REQUEST.md` and `SPEC.md` before every step. Execute strictly in
order. One step per `dr-execute-step` invocation.

- [x] 1. (S1, S2, S3, S4) Add the closed-contract,
      representation-neutral, registry,
      invocation, description, and architecture tests.
      done-when: `test -f tests/test_criticism_source_contract.py && grep -q 'test_contract_fields_are_closed' tests/test_criticism_source_contract.py && grep -q 'test_arbitrary_content_crosses_without_classification' tests/test_criticism_source_contract.py` exits 0.
      proof: `105 tests/test_criticism_source_contract.py`; `done-criterion exit: 0`.

- [x] 2. (S4) Run the new test on the pre-feature tree and record the base RED
      transcript.
      done-when: `grep -q "ImportError: cannot import name 'criticism_source'" experiments/2026-09-01-change-open-criticism-interface/proof/base-red.txt && grep -q 'exit: [^0]' experiments/2026-09-01-change-open-criticism-interface/proof/base-red.txt` exits 0.
      mismatch: pytest exited 2 before collection as required, but
      `from deepreason import criticism_source` spells the missing module as
      `ImportError: cannot import name 'criticism_source' from 'deepreason'`;
      the planned `ModuleNotFoundError` grep therefore exited 1. Re-plan:
      accept the exact emitted `ImportError` spelling; the required nonzero
      pre-feature collection failure is unchanged.
      proof: `done-criterion exit: 0`; transcript records pytest exit 2 and
      the exact pre-feature import refusal.

- [x] 3. (S4) [COMMIT] Commit and push the tests plus base RED checkpoint.
      done-when: `test "$(git rev-parse HEAD)" = "$(git rev-parse origin/codex/open-criticism-contracts-20260901)"` exits 0 after commit `test: pin contribution-only criticism contract`.
      proof: post-push equality command exit 0.

- [x] 4. (S1, S2, S3, S5, S6) Land the alphaXiv-disposed contribution-only module
      as one mapped behavior change, running each proposed map check before
      recording it.
      done-when: `python -m pytest tests/test_criticism_source_contract.py -q` reports 0 failed and all three owner-map documents contain a new single-line `check:` for the boundary they own.
      proof: `12 passed in 0.13s`; map checks reported `5 passed, 7 deselected`,
      `4 passed`, and `3 passed`; diff budget `267/280 WITHIN`; blast-radius
      verdict `CLEAR` with no frozen or frozen-adjacent contacts.

- [x] 5. (S4) Produce the forbidden-contribution-score mutation proof and
      restore GREEN.
      done-when: `grep -q 'score mutant exit: [^0]' experiments/2026-09-01-change-open-criticism-interface/proof/mutations.txt && grep -q 'score restore exit: 0' experiments/2026-09-01-change-open-criticism-interface/proof/mutations.txt` exits 0.
      proof: deliberate `score` field produced the exact-field failure with
      exit 1; restoring the field census returned `1 passed` with exit 0.

- [x] 6. (S4) Produce the forbidden-manifest-priority mutation proof and
      restore GREEN.
      done-when: `grep -q 'priority mutant exit: [^0]' experiments/2026-09-01-change-open-criticism-interface/proof/mutations.txt && grep -q 'priority restore exit: 0' experiments/2026-09-01-change-open-criticism-interface/proof/mutations.txt` exits 0.
      proof: deliberate `priority` field produced the manifest-field failure
      with exit 1; restoring the field census returned `1 passed` with exit 0.

- [x] 7. (S5) Execute every newly recorded owner-map check.
      done-when: the three exact `check:` commands added to `CON-criticism-source.md`, `CON-conjecture-kinds.md`, and `CON-authority.md` each exit 0.
      proof: the exact recorded commands exited 0 with `5 passed, 7 deselected`,
      `4 passed`, and `3 passed`, respectively.

- [x] 8. (S3, S4) Run the defended-trial independence regression ring.
      done-when: `python -m pytest tests/test_criticism_source_contract.py tests/test_judge_canary_dispatch.py tests/test_v6_manifest_defended_trial.py -q` reports 0 failed.
      proof: `15 passed in 6.00s`; the unchanged canary and defended-manifest
      controls remained GREEN beside all source outcomes.

- [x] 9. (S1, S2, S3, S4, S5, S6) Re-run actual blast-radius and insertion-budget gates.
      done-when: `python tools/blast_radius.py --files src/deepreason/criticism_source.py tests/test_criticism_source_contract.py docs/map/CON-criticism-source.md docs/map/CON-conjecture-kinds.md docs/map/CON-authority.md --symbols describe_criticism_sources invoke_criticism_source` reports `"frozen_surface_verdict": "CLEAR"`, and `python tools/diff_budget.py 7d266f85cc6bd4548fde8ce05012b4a49329e209 --ceiling 280 --paths src/deepreason/criticism_source.py tests/test_criticism_source_contract.py docs/map/CON-criticism-source.md docs/map/CON-conjecture-kinds.md docs/map/CON-authority.md` reports a non-exceeded verdict.
      proof: blast radius `CLEAR`, frozen and frozen-adjacent contact lists
      empty; insertion budget `267/280`, verdict `WITHIN`.

- [ ] 10. (S5) Run the full map gate.
      done-when: `python tools/docs_verify.py` reports 0 failed.
      mismatch: command exited 2 before verification because this checkout's
      parser has no `--full` option. Its own help names plain
      `python tools/docs_verify.py` as “authoritative: every check, no cache.”
      re-plan: S5 and this unchecked step now name that canonical command; no
      map result was inferred from the argument error.
      second run: authoritative invocation completed `71 documents, 1297
      checks` with `7 failed`. None names this tranche's three owner maps. The
      set contains two recorded map baselines (`SEAM-llm-x-rules.md:54`,
      `INV-frozen-surfaces.md:181`), the operator-recorded environment-sensitive
      qualification test through two maps, missing container utility `bc`, one
      unrelated scheduler test failure, and the recorded conditional
      continuation timeout. This does not meet the written zero-failure
      criterion; step remains unchecked pending baseline disposition and
      required serial re-runs.

- [ ] 11. (S1, S2, S3, S4, S5) Run the full test gate.
      done-when: `pytest tests/ -q -n 4` ends with 0 failed; paste its final line in this checklist.

- [ ] 12. (S1, S2, S3, S4, S5, S6) [COMMIT] Commit and push implementation, maps, mutation
      proofs, and completed checklist.
      done-when: `git status --porcelain` is empty and `git rev-parse HEAD origin/codex/open-criticism-contracts-20260901` prints one hash twice after commit `change: add contribution-only criticism socket`.
