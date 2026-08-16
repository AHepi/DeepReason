# Checklist for: "the neural embedder installs automatically — no run silently measures with the hash fallback again"

State: next=3 blockers=none
Map ids: `DR-SUB-llm` (covering doc, `llm/embedder.py` — S12 owns it),
`DR-SUB-application` (`application/results.py`, `cli/main.py`),
`DR-SUB-periphery` (`pyproject.toml`), `DR-SUB-scheduler` (stamps the
embedder Measure S6 reads), `DR-SEAM-llm-x-rules` (read; the rules side
consumes `NEAR_DUP_EPS`, which this tranche does not change).

Re-read REQUEST.md + SPEC.md before every step. Execute strictly in
order. One step per dr-execute-step invocation.

Commit boundaries: A = packaging + warm-up + docs + map + their tests
(steps 1-12), B = results/terminal surfacing + its tests (13-18),
C = evidence honesty (19-20), D = instruments + close (21-25).

---

## Phase A — the dependency becomes core

- [x] 1. (S1, census) Resolve the census's highest-risk hit BEFORE
      changing anything: read `tests/test_schema_v3_consumers.py:102`
      and `tests/test_wheel_operational.py:4220` and record, in this
      file under the step, whether each derives its value from the live
      environment (EXPECTED TO MOVE) or is a hand-written fixture
      literal (MUST NOT MOVE).
      done-when: both classifications written into this checklist, each
      with the pasted source line.

      **RESOLVED — both MUST NOT MOVE under S1.**

      `tests/test_schema_v3_consumers.py` — the census's highest-risk
      hit is NOT environment-derived. Both tests that assert on the
      doctor embedder block force the answer themselves:

          56:    monkeypatch.setattr("importlib.util.find_spec", lambda name: None)
          109:   monkeypatch.setattr("importlib.util.find_spec", lambda name: None)

      so `dependency_available: False` at line 102 is a monkeypatched
      constant, immune to S1's packaging change. The risk the census
      flagged does not exist.

      `tests/test_wheel_operational.py:4220` — asserts one literal
      about the wheel's package layout, not the dependency list:

          4220:    assert 'packages = ["src/deepreason", "mini/minireason"]' in project

      S1 edits `[project].dependencies` and
      `[project.optional-dependencies]`, never
      `[tool.hatch.build.targets.wheel]`. MUST NOT MOVE.

      **NEWLY CLASSIFIED consumer, found by this step and recorded
      before it can surprise step 7.** The same file asserts the
      doctor embedder block by EXACT DICT EQUALITY
      (`tests/test_schema_v3_consumers.py:102-110`,
      `assert result["embedder"] == {...}`). S3's `warmup_command`
      field will therefore move it — **EXPECTED TO MOVE at step 7, not
      at steps 2-3**. The assertion is not weakened, only extended by
      the one new key, which is what SPEC S3 predicted the field would
      do.

- [x] 2. (S1) Move `fastembed>=0.3` from `[project.optional-
      dependencies].embed` into `[project].dependencies` in
      `pyproject.toml`; leave `embed = []` declared with a comment
      naming it an alias retained so `pip install 'deepreason[embed]'`
      keeps resolving.
      done-when: `python -c "import tomllib,pathlib; d=tomllib.loads(pathlib.Path('pyproject.toml').read_text()); assert any(r.startswith('fastembed') for r in d['project']['dependencies']); assert d['project']['optional-dependencies']['embed'] == []; print('ok')"` → `ok`

      PROOF:

          $ python -c "import tomllib,pathlib; d=tomllib.loads(...); ...; print('ok')"
          ok

- [ ] 3. (S1) Reinstall from the changed pyproject and prove a plain
      install carries fastembed.
      done-when: `pip install -e . --break-system-packages -q && python -c "import fastembed; print(fastembed.__version__)"` → a version string (paste it)

- [ ] 4. (S9, R14, R15) Write the four embedder regression tests in
      `tests/test_embedder.py`:
      `test_fastembed_is_a_core_dependency` (never skips),
      `test_build_embedder_returns_neural_under_plain_install` (skips
      only on a non-fastembed `EmbedderUnavailable`, skip reason naming
      this tranche), `test_hashing_escape_survives`, and confirm the
      existing forced-fallback test still asserts the
      `embedder-fallback` measure.
      done-when: `python -m pytest tests/test_embedder.py -q` → 0 failed (paste tail)

- [ ] 5. (S8, census) Reword the `EmbedderUnavailable` message at
      `src/deepreason/llm/embedder.py:107-109` — it currently instructs
      installing an extra that is now empty — and update the two
      message assertions the census flagged EXPECTED TO MOVE
      (`tests/test_embedder.py:43`, `:193` if it asserts the same).
      done-when: `python -m pytest tests/test_embedder.py -q` → 0 failed, and `grep -n "deepreason\[embed\]" src/deepreason/llm/embedder.py` → no hits

- [ ] 6. (S3, R4) Add the `embedder-warmup` subparser and
      `_cmd_embedder_warmup` to `src/deepreason/cli/main.py`: progress
      line to stderr naming the model, the 523 MB cost and the cache
      dir; fingerprint JSON to stdout; `--model` override; exit 1 with
      the typed reason on `EmbedderUnavailable`.
      done-when: `deepreason embedder-warmup 2>/dev/null | python -c "import json,sys; d=json.load(sys.stdin); assert {'model','version','sentinel'} <= set(d); print(d['model'])"` → the model id (paste), and the stderr progress line pasted

- [ ] 7. (S3, R4) Add `warmup_command` to `doctor`'s existing
      `embedder` readiness block in `cli/main.py` (the dict at
      ~line 1493).
      done-when: the doctor readiness dict carries `"warmup_command": "deepreason embedder-warmup"` — prove with a direct call to the readiness function, pasted

- [ ] 8. (S3, S9) Add a CLI-level test for `embedder-warmup` (parser
      accepts it; the handler surfaces a typed failure rather than a
      traceback when the backend is unavailable).
      done-when: `python -m pytest tests/test_embedder.py -q` → 0 failed (paste tail)

- [ ] 9. (S4, S5, R5, R6) Correct `config.py`'s EMBEDDER_MODEL comment:
      drop `deepreason[embed]` and "atlas radii", state the 523 MB
      `/tmp/fastembed_cache` cost, name `deepreason embedder-warmup`,
      and state that the absolute distance knobs ship unset.
      done-when: `grep -n "deepreason\[embed\]\|atlas radii" src/deepreason/config.py` → no hits, and `grep -n "fastembed_cache" src/deepreason/config.py` → a hit

- [ ] 10. (S4, S8, R5, R10, R11) Update the three docs: `CLAUDE.md`
      Environment section gains the disk-cost + warm-up line;
      `docs/EXPERIMENT_PROGRAM_2026-07.md:101` and
      `docs/SCRATCHPAD_GROUNDED_BRIDGE.md:83` stop instructing a manual
      `[embed]` install. Paste the R10 verification grep showing
      CLAUDE.md's `pip install -e .` lines are unchanged and still
      correct.
      done-when: `grep -rn "deepreason\[embed\]\|\.\[embed\]" --include=*.md --include=*.py . | grep -v "experiments/2026-08-16-change-embedder-auto-install" | grep -v "experiments/2026-08-13-change-lifecycle-operation-parity"` → no hits

- [ ] 11. (S12, R18) Update `docs/map/SUB-llm.md` in this same commit: a
      `Traps` entry naming the grounded-extension run
      (`experiments/2026-08-12-live-grounded-extension-expansion`, log
      seq 2/8) and ONE new executable `check:` asserting
      `pyproject.toml`'s dependency list carries fastembed — a check
      that would FAIL if it moved back to the extra. Advance
      `Verified-at:` only after re-running that document's checks.
      done-when: `python tools/docs_verify.py --only docs/map/SUB-llm.md` (or the full run filtered to that file) → the new check passes, and inverting the condition by hand makes it fail (paste both)

- [ ] 12. (A) [COMMIT] Ring for phase A, then commit and push.
      done-when: `python -m pytest tests/test_embedder.py tests/test_scratch_similarity.py tests/test_manifest_integration.py tests/test_schema_v3_consumers.py tests/test_wheel_operational.py -q` → 0 failed (paste tail); commit pushed; State line refreshed

## Phase B — the fallback becomes loud

- [ ] 13. (S6, S9, R8) Write the two results tests FIRST in
      `tests/test_results_command.py`:
      `test_results_surfaces_embedder_fallback` and
      `test_results_embedder_absence_is_typed`.
      done-when: `python -m pytest tests/test_results_command.py -q -k embedder` → both FAIL for the right reason (paste the failure, proving the guard bites before the change)

- [ ] 14. (S6, R8) Add `NO_EMBEDDER_RECORD` to `ABSENCE_REASONS` and
      `embedder_summary(harness)` to
      `src/deepreason/application/results.py`, reading the log's
      `embedder` / `embedder-fallback` Measure events.
      done-when: `python -c "from deepreason.application.results import embedder_summary; from deepreason.harness import Harness; print(embedder_summary(Harness('experiments/2026-08-12-live-grounded-extension-expansion/run', read_only=True)))"` → a block with `fallback: True` and model `hashing-128` (paste)

- [ ] 15. (S6, R8) Wire it into `results_summary` as
      `summary["embedder"]` and render the glossed line in
      `render_results`.
      done-when: `deepreason results experiments/2026-08-12-live-grounded-extension-expansion/run | grep -i embedder` → a line containing `hashing (fallback)` (paste)

- [ ] 16. (S6, R8, A3) Decorate the run's terminal summary at the print
      site in `_cmd_reason` (`cli/main.py`, beside the existing
      `payload["run_id"]`), leaving `run-result.json` untouched.
      done-when: `grep -n 'payload\["embedder"\]' src/deepreason/cli/main.py` → a hit adjacent to the `run_id` decoration, and `git diff --stat` shows no change under `src/deepreason/runtime/` or to any durable-sidecar writer

- [ ] 17. (S6, S9) Prove the two step-13 tests now pass and the rest of
      the results suite is unmoved.
      done-when: `python -m pytest tests/test_results_command.py tests/test_error_catalog.py -q` → 0 failed (paste tail)

- [ ] 18. (B) [COMMIT] Commit and push phase B.
      done-when: commit pushed; State line refreshed

## Phase C — evidence honesty

- [ ] 19. (S10, R12, R13) APPEND a dated 2026-08-16 segment to
      `experiments/2026-08-12-live-grounded-extension-expansion/RESULTS.md`:
      the pasted Measure events, the S3 verdict's regime, what it does
      NOT change (LLM calls, judge verdicts, artifact statuses, stop
      reasons), what it does affect (novelty/dup/atlas distance
      measures, school-convergence diagnostics), and the R13 scan
      verdict — no ERRATA entry needed, with the
      `semantic_crosscheck.jsonl` evidence for that verdict.
      done-when: `git diff --stat experiments/2026-08-12-live-grounded-extension-expansion/RESULTS.md` shows insertions only, 0 deletions (paste)

- [ ] 20. (C) [COMMIT] Commit and push phase C.
      done-when: commit pushed; State line refreshed

## Phase D — instruments and close

- [ ] 21. (S11, R16) Run both wheel smokes on the changed tree.
      done-when: `python scripts/wheel_smoke.py; echo rc=$?` → `rc=0` and `python -u scripts/wheel_operational_smoke.py; echo rc=$?` → `rc=0` (paste both). If either moves, re-pin in the SAME commit and re-run.

- [ ] 22. (S12, R17) Map check, FULL mode, alone on the box (never
      concurrent with the gate — `dr-drive-harness` §5b).
      done-when: `python tools/docs_verify.py` → 0 failed beyond the 3 baseline `CON-run-identity.md` git-history failures (docs/AUDIT_BASELINES.md); `python tools/docs_verify.py --audit` → the new SUB-llm.md check is not refused (paste both tails)

- [ ] 23. (S13, R17) FULL gate, alone on the box.
      done-when: `python -m pytest tests/ -q -n 4` → output ends `N passed, 0 failed` (paste it verbatim)

- [ ] 24. (S13) Warm-up smoke on a cold-ish path: prove
      `deepreason embedder-warmup` is idempotent and cheap when the
      weights are already cached.
      done-when: a second `deepreason embedder-warmup` run exits 0 in under ~30 s (paste elapsed)

- [ ] 25. (D) [COMMIT] Push and confirm a clean tree.
      done-when: `git status --porcelain` empty AND `git rev-parse HEAD origin/claude/embedder-auto-install-239s5x` prints the same sha twice (paste)

---

Every S-number is covered: S1→2,3; S2→4 (the hashing-escape test);
S3→6,7,8; S4→9,10; S5→9; S6→13,14,15,16,17; S7→(no code; DELIVERY.md
in dr-deliver-change); S8→5,10; S9→4,8,13,17; S10→19; S11→21;
S12→11,22; S13→12,18,20,22,23,25.
