# Checklist for: test all seat configurations on full judge trial

State: next=7 blockers=none

Re-read `REQUEST.md` and `SPEC.md` before every step. Execute strictly in
order. One step per `dr-execute-step` invocation.

Map scope: `DR-SUB-evaluation`, `DR-SUB-llm`, `DR-SUB-manifest`,
`DR-CON-authority`, `DR-CON-criticism-source`, `DR-CON-schools`, `DR-CON-seats`,
`DR-SEAM-evaluation-x-rules`, `DR-SEAM-llm-x-manifest`,
`DR-SEAM-llm-x-workflow`, and `DR-INV-frozen-surfaces`.

No map document moves: the campaign adds experiment/test instrumentation and
changes no shipped behavior or owner agreement.

- [x] 1. (S1) Write the frozen provider/research preregistration.
      done-when: `test -f experiments/2026-09-01-change-live-full-judge-seat-matrix/PREREG.md && grep -q 'Registered outcomes' experiments/2026-09-01-change-live-full-judge-seat-matrix/PREREG.md` -> exit 0.

      proof: exit 0; `PREREG.md:231:## Registered outcomes`;
      `PREREG_SHA256=33afd81aac209cdf280faf7bd59ff0a194d2abcf8794cd620f61172ab0e77ae6`.

- [x] 2. (S1, S2) Write the canonical finite matrix-domain document.
      done-when: `python -m json.tool experiments/2026-09-01-change-live-full-judge-seat-matrix/MATRIX_DOMAIN.json >/dev/null` -> exit 0.

      proof: exit 0; `MATRIX_DOMAIN_JSON=OK`; `STRUCTURAL_COUNT=452
      UNIQUE=452`; `SET_SHA256=b8c2e8c3d1d650c39ef46c59d499c954b36ec9202cddaab740d2c525148cf895`;
      `LIVE_SEAT_TOTAL=5387888 LIVE_TRANSPORT_TOTAL=28512
      PRIMARY_LIVE_TOTAL=5416400`;
      `DOMAIN_FILE_SHA256=1be915b5cccb5164b17691cb6602fa630d26603064d0096f4b3600fd2975442d`.

- [x] 3. (S2, S3, S5) Write domain, exclusion, digest, concurrency, credential, and resume tests before implementation.
      done-when: `python -m pytest tests/test_live_full_judge_seat_matrix.py -q` -> nonzero with failures caused by the absent experiment module, saved verbatim in `proof/domain-tests-red.txt`.

      proof: exit 1; `10 errors in 0.09s`; every error is `Failed: absent
      experiment module: .../matrix.py`; full output in
      `proof/domain-tests-red.txt`.

- [x] 4. (S1, S2, S3, S5) [COMMIT] Push the preregistration, domain, and RED test proof.
      done-when: the GitHub branch contains `PREREG.md`, `MATRIX_DOMAIN.json`, the test file, and `proof/domain-tests-red.txt`, and local HEAD equals `origin/codex/live-full-judge-seat-matrix-20260901`.

      proof: `RED_PHASE_PUSHED=YES`; all four paths are present at
      `a31f30eb92d7896e1bfa1175f96c6807d00630c3`; local HEAD equalled origin.

- [x] 5. (S2, S3, S5) Implement the domain generator, normalized bans, exact case ids, digest binding, atomic result writes, and resume rules in `matrix.py`.
      done-when: `python experiments/2026-09-01-change-live-full-judge-seat-matrix/matrix.py enumerate --fixture-catalog` prints `CATALOG_MODELS=22 JUDGE_PAIRS=484 CORE_COURTS=10648 NO_VARIATOR=234256 WITH_VARIATOR=5153632 TOTAL=5387888`.

      proof: exit 0 with the exact registered line; `python -m py_compile`
      exit 0; focused file `10 passed in 0.09s`; two-model emitted prefixes
      `judge_pairs=4 core_courts=4 no_variator=8 with_variator=32`.

- [x] 6. (S2, S3, S5) Run the actual-file blast-radius gate over the domain implementation.
      done-when: `python tools/blast_radius.py --files experiments/2026-09-01-change-live-full-judge-seat-matrix/matrix.py tests/test_live_full_judge_seat_matrix.py` reports `"frozen_surface_contacts": []`, `"frozen_adjacent_contacts": []`, and `"frozen_surface_verdict": "CLEAR"`.

      proof: `frozen_surface_contacts=[]`;
      `frozen_adjacent_contacts=[]`; `frozen_surface_verdict=CLEAR`;
      consumers and reachability are empty.

- [ ] 7. (S2, S3, S5) Prove the domain/safety/resume tests GREEN.
      done-when: `python -m pytest tests/test_live_full_judge_seat_matrix.py -q -k 'domain or authority or kimi or reasoning or concurrency or credential or resume or digest'` ends with 0 failed, saved in `proof/domain-tests-green.txt`.

- [ ] 8. (S2, S3, S5) Measure checkpoint-one diff budget.
      done-when: `python tools/diff_budget.py 70e9c73ed0a5630994613afea74c80de6bf59302 --ceiling 540 --paths experiments/2026-09-01-change-live-full-judge-seat-matrix/matrix.py tests/test_live_full_judge_seat_matrix.py` reports `WITHIN`.

- [ ] 9. (S2, S3, S5) [COMMIT] Push the domain/safety/resume implementation and GREEN proof.
      done-when: local HEAD equals the GitHub branch head and `git status --porcelain` is empty.

- [ ] 10. (S4, S6) Add shipped-court, topology, managed-path, typed-boundary, sequence, and soak tests before live implementation.
      done-when: `python -m pytest tests/test_live_full_judge_seat_matrix.py -q -k 'topology or typed or managed or sequence or soak'` -> nonzero for missing implementation, saved in `proof/court-tests-red.txt`.

- [ ] 11. (S4, S6) [COMMIT] Push the RED shipped-court tests and proof.
      done-when: the GitHub branch contains the new tests and `proof/court-tests-red.txt`, and local HEAD equals origin.

- [ ] 12. (S4) Implement exact defended v6 manifest compilation and deterministic full-court driving through the shipped argumentative-trial path.
      done-when: `python -m pytest tests/test_live_full_judge_seat_matrix.py -q -k 'topology or typed or managed or sequence'` ends with 0 failed.

- [ ] 13. (S6) Implement the experiment-owned Kimi-K3-free `cycle_soak.SoakCase` wrapper without editing `scripts/cycle_soak.py`.
      done-when: `python -u experiments/2026-09-01-change-live-full-judge-seat-matrix/matrix.py soak` prints `SOAK_VERDICT=PASS CASE=judge-matrix CYCLES=8`.

- [ ] 14. (S3, S4, S5) Implement live endpoint construction, reasoning probes, the global three-call semaphore, typed result classification, and leak-safe persistence.
      done-when: `python -m pytest tests/test_live_full_judge_seat_matrix.py -q` ends with 0 failed, saved in `proof/all-matrix-tests-green.txt`.

- [ ] 15. (S3, S4, S5, S6) Run the actual-file blast-radius gate over the assembled runner.
      done-when: `python tools/blast_radius.py --files experiments/2026-09-01-change-live-full-judge-seat-matrix/matrix.py tests/test_live_full_judge_seat_matrix.py` reports both frozen contact lists empty and verdict CLEAR.

- [ ] 16. (S3, S4, S5, S6) Measure checkpoint-two diff budget.
      done-when: `python tools/diff_budget.py 70e9c73ed0a5630994613afea74c80de6bf59302 --ceiling 960 --paths experiments/2026-09-01-change-live-full-judge-seat-matrix/matrix.py tests/test_live_full_judge_seat_matrix.py` reports `WITHIN`.

- [ ] 17. (S3, S4, S5, S6) [COMMIT] Push the assembled runner, soak proof, and full matrix-test GREEN proof.
      done-when: local HEAD equals the GitHub branch head and `git status --porcelain` is empty.

- [ ] 18. (S4) Re-run the unchanged shipped judge control ring.
      done-when: `python -m pytest tests/test_judge_ensemble_boundary.py tests/test_judge_canary_dispatch.py tests/test_judge_canary_compile_gap.py -q` ends with 13 passed, 0 failed.

- [ ] 19. (S2, S4) Run the frozen offline structural matrix to its exact terminal-set check.
      done-when: `python experiments/2026-09-01-change-live-full-judge-seat-matrix/matrix.py structural` prints `STRUCTURAL_EXPECTED=<n> STRUCTURAL_TERMINAL=<same n> DUPLICATE=0 MISSING=0`.

- [ ] 20. (S1, S3, S5) Confirm the live credential is securely mounted without displaying it.
      done-when: `python -c "import os; raise SystemExit(0 if os.environ.get('OLLAMA_API_KEY') else 2)"` exits 0 and no credential bytes appear in output or tracked files.

- [ ] 21. (S1, S2) Discover the authenticated Ollama catalog without making a chat completion.
      done-when: `python experiments/2026-09-01-change-live-full-judge-seat-matrix/matrix.py catalog` writes canonical `CATALOG.json`, excludes only typed Kimi-K3 rows, and prints its model count and digest without credential material.

- [ ] 22. (S1, S2, S3) [COMMIT] Freeze and push the authenticated catalog before any completion request.
      done-when: the GitHub branch contains `CATALOG.json`, local HEAD equals origin, and `git grep -n 'kimi.k3' -- experiments/2026-09-01-change-live-full-judge-seat-matrix/CATALOG.json` finds only typed exclusion rows.

- [ ] 23. (S3, S5) Run explicit none/low/medium reasoning probes for every catalog model at a maximum of three calls in flight.
      done-when: `python experiments/2026-09-01-change-live-full-judge-seat-matrix/matrix.py probe` reports one terminal probe row per model/setting, `PEAK_IN_FLIGHT<=3`, no high/max/xhigh wire value, and no secret-leak finding.

- [ ] 24. (S4, S5, S6) Run one serial live full-court smoke after the green soak.
      done-when: `python experiments/2026-09-01-change-live-full-judge-seat-matrix/matrix.py live --limit 1 --workers 1` records critic, defender, judge 0, and judge 1 dispatches or the first typed refusal verbatim.

- [ ] 25. (S2, S4, S5, S6) Launch the exact ordered-judge-pair prefix with at most three live calls in flight.
      done-when: `matrix.py live --through judge-pairs --workers 3` is launched detached with a PID-specific monitor, and its first checkpoint reports `PEAK_IN_FLIGHT<=3` and an exact expected/pending set.

- [ ] 26. (S2, S6) Preserve and push the ordered-judge-pair prefix result when terminal or when this session stops monitoring.
      done-when: `RESULTS.md` states exact expected, terminal, possible, impossible, provider-indeterminate, interrupted, and pending counts; no prefix is labelled exhaustive over the full domain.

- [ ] 27. (S2, S6) Continue the immutable queue through defender/judge courts, no-variator courts, and variator courts without changing its domain digest.
      done-when: `matrix.py summarize` either reports `PENDING=0` or records the exact remaining count and a resumable next case id without mutating terminal results.

- [ ] 28. (S7) Prove branch isolation and no merge with `main`.
      done-when: `git rev-list --merges 00f10dde8c734e2f874358f9e2a375bb63aa4a35..HEAD` is empty and the current branch is `codex/live-full-judge-seat-matrix-20260901`.

- [ ] 29. (S1-S7) Run the full matrix regression file.
      done-when: `python -m pytest tests/test_live_full_judge_seat_matrix.py -q` ends with 0 failed.

- [ ] 30. (S1-S7) Run the full repository gate while no live worker or docs verifier is running.
      done-when: `python -m pytest tests/ -q -n 4` ends with 0 failed; any baseline failure is recorded verbatim and routes to validation FAIL, never skipped or edited around.

- [ ] 31. (S1-S7) Run the authoritative documentation verifier while the machine is otherwise idle.
      done-when: `python tools/docs_verify.py` reports 0 failed, `--audit` 0 findings, `--links` 0 dangling, and `--coverage` 0 findings; every `--stale` row is disposed in validation.

- [ ] 32. (S1-S7) Produce `VALIDATION.md` with every acceptance output and an R-by-R reconciliation.
      done-when: `grep -q '^## Verdict: PASS$' experiments/2026-09-01-change-live-full-judge-seat-matrix/VALIDATION.md` exits 0, or a truthful FAIL document is pushed and execution stops for replanning.

- [ ] 33. (S1-S7) [COMMIT] Push the final evidence checkpoint.
      done-when: `git status --porcelain` is empty, local HEAD equals `origin/codex/live-full-judge-seat-matrix-20260901`, and `main` has not been updated or merged.
