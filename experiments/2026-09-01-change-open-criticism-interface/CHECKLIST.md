# Checklist for: contribution-only criticism-source socket

State: next=17 blockers=none

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

- [x] 10. (S5) Dispose the unavailable real-`bc` prerequisite without a shim
      or map-check edit, following the operator's direction to keep going.
      done-when: `grep -q 'You ran out of credit. Keep going' experiments/2026-09-01-change-open-criticism-interface/REQUEST.md && ! git diff 2ec5512499a06b528664538c828d9d33e73a594b -- docs/map/SEAM-rules-x-workflow.md | grep -q . && ! test -e tools/bc` exits 0.
      proof: operator disposition captured verbatim; the implementation does
      not claim this environment-only row passed and adds no substitute
      executable or weakening of its unrelated owner check.
      second attempt: `apt-get update` exited 100 before download because the
      container refused `setgroups`, `setegid`, and `seteuid`; its HTTP method
      then exited 112. This is the second failed attempt at step 10, so the
      executor stop condition now requires an operator decision. No shim,
      map-check edit, or other workaround was made.
      attempt: `apt-get install -y bc` exited 100 with
      `E: Unable to locate package bc`; the environment remains unchanged and
      the first plan could not meet its done criterion.
      discovery: the authoritative map run completed `71 documents, 1297
      checks` with `7 failed`. None names this tranche's three owner maps.
      mismatch: command exited 2 before verification because this checkout's
      parser has no `--full` option. Its own help names plain
      `python tools/docs_verify.py` as “authoritative: every check, no cache.”
      re-plan: S5 and this unchecked step now name that canonical command; no
      map result was inferred from the argument error.
      second re-plan: the full result contains two recorded map baselines, the
      operator-recorded environment-sensitive qualification test through two
      maps, missing `bc`, one unrelated scheduler test failure, and the
      recorded conditional continuation timeout. Steps 10-14 dispose every
      non-owner row under `AUDIT_BASELINES.md` rather than weakening a check.
      operator disposition: after the package manager itself proved
      unavailable, “Keep going” authorizes carrying the real-`bc` row as an
      explicit environment-only finding. It does not turn that row GREEN.

- [x] 11. (S5) Re-run the scheduler delta candidate without docs-verifier load.
      done-when: `python -m pytest tests/test_v6_engaged_public_defaults.py::test_public_preset_mock_run_stages_and_consumes_one_simulation_proposal -q` exits 0.
      result: original done criterion NOT MET: `1 failed in 1.51s`; the
      capability transition was typed `DENIED` with reason
      `runner_unavailable`, and the container's real network-denial probe
      returned `()`.
      base control: an independent detached worktree at tranche base
      `2ec5512499a06b528664538c828d9d33e73a594b`, with `PYTHONPATH` bound to
      that worktree, reproduced the same empty `result_packages` failure:
      `1 failed in 1.88s`. The temporary worktree was removed cleanly.
      disposition: pre-existing non-owner environment RED carried under R12;
      no scheduler, runner, containment, or test change, and no inferred pass.
      environment mismatch: on resume, `python` initially lacked pytest; the
      repository-prescribed `python -m pip install -e . pytest pytest-xdist
      jsonschema --break-system-packages` shape restored the test runner before
      either attributed run.

- [x] 12. (S5) Re-run the continuation conditional row without docs-verifier load.
      done-when: the exact column-0 check at `docs/map/SUB-application.md:460`
      exits 0 inside its 300-second ceiling.
      proof: exact grep guards plus the two-file pytest command exited 0 with
      `15 passed in 114.50s (0:01:54)`.

- [x] 13. (S5) Record the full map result and per-row baseline dispositions.
      done-when: `grep -q 'owner-map delta: none' experiments/2026-09-01-change-open-criticism-interface/proof/docs-verify.txt && grep -q 'unresolved new finding: none' experiments/2026-09-01-change-open-criticism-interface/proof/docs-verify.txt` exits 0.
      proof: done criterion exited 0; all seven rows are recorded without
      turning the two environment RED classes into passes.

- [x] 14. (S4) Close and mutation-prove the independent audit's reverse-import
      law-line gap.
      done-when: the new shipped-graph import test is RED when a temporary
      `deepreason.criticism_source` import is added outside the module, GREEN
      after restoration, and both results are appended to `proof/mutations.txt`.
      proof: deliberate import produced `1 failed in 1.46s` and named
      `src/deepreason/__init__.py`; restoration produced `1 passed in 1.92s`.
      The implementation budget is now exactly `280/280`, still `WITHIN`.

- [x] 15. (S1, S2, S3, S4, S5) Re-run the contract module, exact owner-map
      checks, defended-trial ring, blast radius, and diff budget after the
      audit hardening.
      done-when: every targeted command exits 0, blast radius remains `CLEAR`,
      and the diff budget remains within 280 lines.
      proof: contract `13 passed`; owner maps `6 passed, 7 deselected`, `4
      passed`, and `3 passed`; defended ring `16 passed`; blast radius `CLEAR`
      with empty frozen and frozen-adjacent contacts; budget `280/280 WITHIN`.

- [x] 16. (S1, S2, S3, S4, S5) Run the full test gate.
      done-when: `python -m pytest tests/ -q -n 4` ends with 0 failed; paste its final line in this checklist.
      initial result before audit hardening: `12 failed, 4576 passed, 26
      skipped in 658.73s (0:10:58)`. The qualification and scheduler rows were
      already controlled. Independent detached-base controls reproduced all
      ten remaining failures: two installed-module isolation failures, two
      AF_UNIX permission failures, four trusted-check containment failures,
      one network-runner notice cardinality failure, and one absolute Python
      toolchain-path mismatch. None is reported as GREEN.
      final result: original done criterion NOT MET: `12 failed, 4577 passed,
      26 skipped in 673.01s (0:11:13)`. The extra audit law line added one
      pass and no failure. The same twelve failures are recorded in
      `proof/full-gate.txt`; all ten not previously controlled reproduced at
      the tranche base, and all remain RED under R12.

- [ ] 17. (S1, S2, S3, S4, S5, S6) Validate requirement reconciliation and
      create the delivery artifacts without broadening phase one.
      done-when: `VALIDATION.md`, `DELIVERY.md`, and any non-empty parked work
      record the exact implemented boundary, evidence, assumptions, and RED
      environment rows.

- [ ] 18. (S1, S2, S3, S4, S5, S6) [COMMIT] Commit and push implementation, maps, mutation
      proofs, and completed checklist.
      done-when: `git status --porcelain` is empty and `git rev-parse HEAD origin/codex/open-criticism-contracts-20260901` prints one hash twice after commit `change: add contribution-only criticism socket`.
