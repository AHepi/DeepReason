# Checklist for: test all seat configurations on full judge trial

State: next=28 blockers=none

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

- [x] 7. (S2, S3, S5) Prove the domain/safety/resume tests GREEN.
      done-when: `python -m pytest tests/test_live_full_judge_seat_matrix.py -q -k 'domain or authority or kimi or reasoning or concurrency or credential or resume or digest'` ends with 0 failed, saved in `proof/domain-tests-green.txt`.

      proof: exit 0; `9 passed, 1 deselected in 0.09s`; full output in
      `proof/domain-tests-green.txt`. The complete file also passed 10/10 at
      step 5.

- [x] 8. (S2, S3, S5) Measure checkpoint-one diff budget.
      done-when: `python tools/diff_budget.py 70e9c73ed0a5630994613afea74c80de6bf59302 --ceiling 540 --paths experiments/2026-09-01-change-live-full-judge-seat-matrix/matrix.py tests/test_live_full_judge_seat_matrix.py` reports `WITHIN`.

      proof: `matrix.py=274`, `test_live_full_judge_seat_matrix.py=217`,
      `total_insertions=491`, `ceiling=540`, `verdict=WITHIN`.

- [x] 9. (S2, S3, S5) [COMMIT] Push the domain/safety/resume implementation and GREEN proof.
      done-when: local HEAD equals the GitHub branch head and `git status --porcelain` is empty.

      proof: `DOMAIN_PHASE_PUSHED=YES` at
      `9dff8518d5c94de6a0500181570f4c2b2eca9d35`; local HEAD equalled origin;
      worktree empty.

- [x] 10. (S4, S6) Add shipped-court, topology, managed-path, typed-boundary, sequence, and soak tests before live implementation.
      done-when: `python -m pytest tests/test_live_full_judge_seat_matrix.py -q -k 'topology or typed or managed or sequence or soak'` -> nonzero for missing implementation, saved in `proof/court-tests-red.txt`.

      proof: exit 1; `8 failed, 10 deselected in 0.13s`; every failure is
      `AttributeError` for one of the deliberately absent experiment APIs;
      full output in `proof/court-tests-red.txt`.

- [x] 11. (S4, S6) [COMMIT] Push the RED shipped-court tests and proof.
      done-when: the GitHub branch contains the new tests and `proof/court-tests-red.txt`, and local HEAD equals origin.

      proof: `COURT_RED_PHASE_PUSHED=YES` at
      `7c54681cf5dac8fa43aa8b983908b53ea48fb477`; local HEAD equalled origin;
      worktree empty after synchronization.

- [x] 12. (S4) Implement exact defended v6 manifest compilation and deterministic full-court driving through the shipped argumentative-trial path.
      done-when: `python -m pytest tests/test_live_full_judge_seat_matrix.py -q -k 'topology or typed or managed or sequence'` ends with 0 failed.

      proof: exit 0; `7 passed, 11 deselected in 7.04s`; dispatch extent is
      read from durable shipped workflow work and cross-checked against endpoint
      callbacks; semantic outcome is read from committed trial measures/state;
      full output in `proof/court-tests-green.txt`.

- [x] 12A. (S1, S2, S6) Write the superseding full-cross preregistration and
      machine-readable domain before any live completion.
      done-when: `python -m json.tool experiments/2026-09-01-change-live-full-judge-seat-matrix/FULL_CROSS_DOMAIN.json >/dev/null` exits 0 and the document records fixture total `237110749640940257280`.

      proof: JSON exit 0; independently recomputed `S=1584`,
      `J2=149596687470624768`, `J3=236961152953469632512`, and
      `FULL=237110749640940257280`. Original file hashes remain
      `PREREG=33afd81aac209cdf280faf7bd59ff0a194d2abcf8794cd620f61172ab0e77ae6`
      and `MATRIX_DOMAIN=1be915b5cccb5164b17691cb6602fa630d26603064d0096f4b3600fd2975442d`.
      New hashes are
      `FULL_CROSS_PREREG=a8ffe20ea6d7f060a92d4da385c3bcc679c396f35f31de6e46e373883fdaf76c`
      and `FULL_CROSS_DOMAIN=148793d2bd570869a5e2be7b1d1a3845c1fb69095ac987e4396f3c99b9d9322e`.

- [x] 12B. (S1, S2, S6) [COMMIT] Push the superseding preregistration, domain,
      scope correction, and forward budget before generator implementation.
      done-when: local HEAD equals origin and both new files are present on the
      branch; the original `PREREG.md` and `MATRIX_DOMAIN.json` blobs are
      unchanged.

      proof: `FULL_CROSS_PREREGISTRATION_PUSHED=YES` at
      `5caeea7501a2e229334e23d9e02bc1fad3ee4195`; local HEAD equalled origin;
      original preregistration and domain Git blobs remained
      `dcd444bc2fa53adcf2f1d3c4da406188ef70ae8a` and
      `08e99f1aa4a48d841775498a22d1c6d630b826ea`. Pre-implementation
      computability correction pushed at
      `685b1c8c9a5566e6cfc70d7ba845a9d294b6f7eb`; it replaces an impossible
      whole-fixture preflight set digest with exact count/ordinal boundaries
      plus a complete tiny Cartesian oracle.

- [x] 12C. (S2, S3, S5) Add full-cross count, literal Cartesian membership,
      per-seat independence, case-id, ban, and resume tests before implementation.
      done-when: `python -m pytest tests/test_live_full_judge_seat_matrix.py -q -k 'full_cross'` fails only because the new generator APIs are absent, with output saved in `proof/full-cross-tests-red.txt`.

      proof: exit 1; `10 failed, 18 deselected in 0.16s`; every failure is an
      `AttributeError` for an absent registered full-cross API. The tests include
      direct fixture-tail ordinal lookup with the iterator monkeypatched to
      fail, so a linear resume implementation cannot satisfy the contract.
      Full output is in `proof/full-cross-tests-red.txt`.

- [x] 12D. (S2, S3, S5) [COMMIT] Push the full-cross RED tests and mutation proof.
      done-when: local HEAD equals origin and `proof/full-cross-tests-red.txt`
      is present on the branch.

      proof: `FULL_CROSS_RED_PUSHED=YES` at
      `9c3a0bc1ec5ed96340438e40cf4221f078cb571f`; local HEAD equalled origin;
      worktree empty.

- [x] 12E. (S2, S3, S5) Implement the exact lazy two-/three-judge full-cross
      generator without filtering any family, preflight, parser, or provider
      refusal.
      done-when: the focused `full_cross` tests end with 0 failed and the
      fixture command prints the exact two-judge, three-judge, and union counts.

      proof: `10 passed, 18 deselected in 0.26s`. The fixture command printed
      `SEAT_TUPLES=1584`, `JUDGE_2=149596687470624768`,
      `JUDGE_3=236961152953469632512`, and
      `TOTAL=237110749640940257280`. Direct mixed-radix lookup and inverse
      reached the fixture tail without walking the iterator.

- [x] 12F. (S2, S3, S5) Run full-cross GREEN, actual-file blast radius, and
      the corrected cumulative 2200-line budget.
      done-when: GREEN output is saved, both frozen-contact lists are empty,
      and `tools/diff_budget.py ... --ceiling 2200` reports `WITHIN`.

      proof: `frozen_surface_contacts=[]`,
      `frozen_adjacent_contacts=[]`, `frozen_surface_verdict=CLEAR`;
      `matrix.py=1076`, `test_live_full_judge_seat_matrix.py=708`,
      `total_insertions=1784`, `ceiling=2200`, `verdict=WITHIN`. Full output
      is in `proof/full-cross-tests-green.txt`.

- [x] 12G. (S2, S3, S5) [COMMIT] Push the full-cross generator and GREEN proof.
      done-when: local HEAD equals origin and the worktree is empty.

      proof: `FULL_CROSS_GREEN_PUSHED=YES` at
      `270be24a10ff05ae5d73eb616a4e0d554c58ccec`; local HEAD equalled origin;
      worktree empty.

- [x] 13. (S6) Implement the experiment-owned Kimi-K3-free `cycle_soak.SoakCase` wrapper without editing `scripts/cycle_soak.py`.
      done-when: `python -u experiments/2026-09-01-change-live-full-judge-seat-matrix/matrix.py soak` prints `SOAK_VERDICT=PASS CASE=judge-matrix CYCLES=8`.

      proof: exit 0; `SOAK_VERDICT=PASS CASE=judge-matrix CYCLES=8`;
      eight of eight managed cycles reached; terminal state `completed` with
      `stop_reason='budget_exhausted'`; `verify_root` found 0 violations;
      31 transaction-authorized provider attempts exercised the defended,
      Kimi-K3-free two-judge launch shape. Full output is in
      `proof/soak-green.txt`; `scripts/cycle_soak.py` remained byte-unchanged.

- [x] 14. (S3, S4, S5) Implement live endpoint construction, reasoning probes, the global three-call semaphore, typed result classification, and leak-safe persistence.
      done-when: `python -m pytest tests/test_live_full_judge_seat_matrix.py -q` ends with 0 failed, saved in `proof/all-matrix-tests-green.txt`.

      proof: exit 0; `37 passed in 7.48s`; the authenticated-catalog,
      exact per-seat transport, defended-authority, explicit reasoning,
      populated-trace metadata, global three-call ceiling, typed boundary,
      leak-safe persistence, case-receipt, and direct-resume contracts are
      GREEN. Full output is in `proof/all-matrix-tests-green.txt`.

- [x] 15. (S3, S4, S5, S6) Run the actual-file blast-radius gate over the assembled runner.
      done-when: `python tools/blast_radius.py --files experiments/2026-09-01-change-live-full-judge-seat-matrix/matrix.py experiments/2026-09-01-change-live-full-judge-seat-matrix/soak_builder.py tests/test_live_full_judge_seat_matrix.py` reports both frozen contact lists empty and verdict CLEAR.

      proof: exit 0; `frozen_surface_contacts=[]`;
      `frozen_adjacent_contacts=[]`; `reachability=[]`;
      `frozen_surface_verdict=CLEAR`.

- [x] 16. (S3, S4, S5, S6) Measure checkpoint-two diff budget.
      done-when: `python tools/diff_budget.py 70e9c73ed0a5630994613afea74c80de6bf59302 --ceiling 3200 --paths experiments/2026-09-01-change-live-full-judge-seat-matrix/matrix.py experiments/2026-09-01-change-live-full-judge-seat-matrix/soak_builder.py tests/test_live_full_judge_seat_matrix.py` reports `WITHIN`.

      proof: exit 0; `matrix.py=1480`, `soak_builder.py=123`,
      `test_live_full_judge_seat_matrix.py=984`, `total_insertions=2587`,
      `ceiling=3200`, `verdict=WITHIN`.

- [x] 17. (S3, S4, S5, S6) [COMMIT] Push the assembled runner, soak proof, and full matrix-test GREEN proof.
      done-when: local HEAD equals the GitHub branch head and `git status --porcelain` is empty.

      proof: `ASSEMBLED_RUNNER_PUSHED=YES`; the branch checkpoint contains
      the eight-cycle soak proof, 37-test GREEN proof, exact live endpoint
      bindings, three-call gate, typed classifications, and leak-safe
      receipts; local HEAD equalled origin and the worktree was empty.

- [x] 18. (S4) Re-run the unchanged shipped judge control ring.
      done-when: `python -m pytest tests/test_judge_ensemble_boundary.py tests/test_judge_canary_dispatch.py tests/test_judge_canary_compile_gap.py -q` ends with 13 passed, 0 failed.

      proof: exit 0; `13 passed in 2.50s`; the unchanged ensemble,
      dispatch, and compile-gap control ring remains GREEN.

- [x] 19. (S2, S4) Run the frozen offline structural matrix to its exact terminal-set check.
      done-when: `python experiments/2026-09-01-change-live-full-judge-seat-matrix/matrix.py structural` prints `STRUCTURAL_EXPECTED=<n> STRUCTURAL_TERMINAL=<same n> DUPLICATE=0 MISSING=0`.

      proof: exit 0; `STRUCTURAL_EXPECTED=452`;
      `STRUCTURAL_TERMINAL=452`; `DUPLICATE=0`; `MISSING=0`. The matrix
      regression remained GREEN at `37 passed in 7.18s` after wiring the
      experiment-only command.

- [x] 20. (S1, S3, S5) Confirm the live credential is securely mounted without displaying it.
      done-when: `python -c "import os; raise SystemExit(0 if os.environ.get('OLLAMA_API_KEY') else 2)"` exits 0 and no credential bytes appear in output or tracked files.

      proof: environment-only presence check exited 0 with no output;
      an exact in-memory scan of every tracked working-tree file reported
      `TRACKED_SECRET_SCAN=PASS`. No credential bytes or credential hash were
      printed, written, or committed.

- [x] 21. (S1, S2) Discover the authenticated Ollama catalog without making a chat completion.
      done-when: `python experiments/2026-09-01-change-live-full-judge-seat-matrix/matrix.py catalog` writes canonical `CATALOG.json`, excludes only typed Kimi-K3 rows, and prints its model count and digest without credential material.

      proof: authenticated models-only GET exited 0;
      `CATALOG_MODELS=18`; `EXCLUDED=1`;
      `CATALOG_SHA256=77a5a11f946b21e82488ddc66473f1bfa50c6bd6c394fd420ad1baacc81754b4`.
      Independent byte-canonicality, UTF-8 ordering, duplicate, digest, and
      normalized typed-exclusion checks reported `CATALOG_VERIFY=PASS`. No
      chat completion was made.

- [x] 22. (S1, S2, S3) [COMMIT] Freeze and push the authenticated catalog before any completion request.
      done-when: the GitHub branch contains `CATALOG.json`, local HEAD equals origin, and `git grep -n 'kimi.k3' -- experiments/2026-09-01-change-live-full-judge-seat-matrix/CATALOG.json` finds only typed exclusion rows.

      proof: `AUTHENTICATED_CATALOG_PUSHED=YES`; the branch snapshot has 18
      included raw ids, one `KIMI_K3_FORBIDDEN` row, and digest
      `77a5a11f946b21e82488ddc66473f1bfa50c6bd6c394fd420ad1baacc81754b4`;
      local HEAD equalled origin before the first completion request.

- [x] 23. (S3, S5) Run explicit none/low/medium reasoning probes for every catalog model at a maximum of three calls in flight.
      done-when: `python experiments/2026-09-01-change-live-full-judge-seat-matrix/matrix.py probe` reports one terminal probe row per model/setting, `PEAK_IN_FLIGHT<=3`, no high/max/xhigh wire value, and no secret-leak finding.

      proof: exit 0; `PROBE_EXPECTED=54`; `PROBE_TERMINAL=54`;
      `PROBE_USABLE=41`; `PROVIDER_INDETERMINATE=13`;
      `PEAK_IN_FLIGHT=3`; `PEAK_IN_FLIGHT<=3`;
      `FORBIDDEN_REASONING=0`; `SECRET_LEAK=0`. The immutable safe receipt
      records only parser/schema outcomes, response key names, and trace
      byte-count/digest metadata; it stores no raw trace, response prose, or
      credential material. Populated trace metadata was observed for 4
      `none`, 15 `low`, and 17 `medium` rows without reinterpreting the
      requested setting.

- [x] 24. (S4, S5, S6) Run one serial live full-court smoke after the green soak.
      done-when: `python experiments/2026-09-01-change-live-full-judge-seat-matrix/matrix.py live --limit 1 --workers 1` records critic, defender, judge 0, and judge 1 dispatches or the first typed refusal verbatim.

      proof: exit 0 from clean isolated source commit
      `d3cbed718d946c0b2cdb2ebef96856673d8127f9`;
      `LIVE_EXPECTED=1994544`; `LIVE_TERMINAL=1`; `POSSIBLE=1`;
      `CONFIGURATION_REFUSED=0`; `PROVIDER_INDETERMINATE=0`;
      `UNEXPECTED_ERROR=0`; `PENDING=1994543`; `PEAK_IN_FLIGHT=1`;
      `PEAK_IN_FLIGHT<=3`. Case
      `sha256:f7be2b358edcc0c713f8dc02c630688f4624bf6edb86f58754b802872b689150`
      ended `trial_outcome` with exact logical attempt history
      `critic,critic,defender,judge:0,judge:1`; the second critic attempt is
      the shipped fallback and not another seat. An exact credential scan of
      tracked files and the ignored runtime root reported
      `SECRET_SCAN=PASS LEAK_FILES=0`.

- [x] 25. (S2, S4, S5, S6) Launch the exact ordered-judge-pair prefix with at most three live calls in flight.
      done-when: `matrix.py live --through judge-pairs --workers 3` is launched detached with a PID-specific monitor, and its first checkpoint reports `PEAK_IN_FLIGHT<=3` and an exact expected/pending set.

      proof: clean source commit
      `dfe5bebd2dd987e82e050888a9d7c8400819a583` launched one coordinator with
      worker PID 191 under its Popen-owning PID-specific supervisor. The first
      checkpoint reported `EXPECTED=324 TERMINAL=1 PENDING=323 DUPLICATE=0
      PEAK_IN_FLIGHT<=3`. A nested-PID monitor fault in the preceding launch
      was stopped, preserved as seven files under quarantined `attempt-0002`,
      and excluded by a new 39/39-green resume regression. No provider call
      was made from an uncommitted or tree-mismatched source.

- [x] 26. (S2, S6) Preserve and push the ordered-judge-pair prefix result when terminal or when this session stops monitoring.
      done-when: `RESULTS.md` states exact expected, terminal, possible, impossible, provider-indeterminate, interrupted, and pending counts; no prefix is labelled exhaustive over the full domain.

      proof: session-stop checkpoint `EXPECTED=324 TERMINAL=9 POSSIBLE=8
      IMPOSSIBLE=1 PROVIDER_INDETERMINATE=0 INTERRUPTED=0 PENDING=315
      DUPLICATE=0 PEAK_IN_FLIGHT<=3`; eight clean replacement receipts are in
      retained `attempt-0003`, and its interruption marker forces fresh-root
      resume. `RESULTS.md` labels the result a stopped resumable prefix and
      reports the superseding full cross as `TERMINAL=0`. Machine-ledger
      reconciliation printed `PREFIX_LEDGER_VERIFY=PASS CASES=9 EXPECTED=324
      PENDING=315`; the exact-byte credential scan reported
      `SECRET_SCAN=PASS LEAK_FILES=0`.

- [x] 27. (S2, S6) Continue the immutable queue through the named seat-only
      projections and into the superseding per-seat full cross without changing
      either domain digest.
      done-when: `matrix.py summarize` either reports full-cross `PENDING=0` or
      records the exact remaining count and a resumable next case id; a
      completed projection is never renamed as completion of the full cross.

      proof: the constant-time direct-ordinal summarizer reported
      `judge-pairs 9/324`, `core-courts 9/5832`, `no-variator 9/104976`, and
      `seat-only 9/1994544`. The superseding cross reported
      `EXPECTED=71141539390075109376 TERMINAL=0
      PENDING=71141539390075109376 NEXT_ORDINAL=0` and next case
      `sha256:1b50183d2639aadf2f05611d440a9036c564a7c9b537e2be93410a0bc5b4c25e`.
      Sparse-resume and frozen-domain constant-time regressions brought the
      campaign file to 41/41 green; blast radius remained `CLEAR` and the
      measured code/test total was `4073/5000 WITHIN`. Both frozen domain file
      digests remained unchanged.

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
