# Checklist for: "the neural embedder installs automatically — no run silently measures with the hash fallback again"

State: next=19 blockers=none (STOP resolved by R21 — ceiling raised to 450, no scope change)
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

- [x] 3. (S1) Reinstall from the changed pyproject and prove a plain
      install carries fastembed.
      done-when: `pip install -e . --break-system-packages -q && python -c "import fastembed; print(fastembed.__version__)"` → a version string (paste it)

      PROOF — fastembed was UNINSTALLED first, so this is the packaging
      change working and not a leftover from the SPEC's P3 measurement:

          $ pip uninstall -y fastembed --break-system-packages -q
          $ python -c "import fastembed"
          ModuleNotFoundError: No module named 'fastembed'
          $ pip install -e . --break-system-packages -q
          $ python -c "import fastembed; print('fastembed', fastembed.__version__)"
          fastembed 0.8.0

- [x] 4. (S9, R14, R15) Write the four embedder regression tests in
      `tests/test_embedder.py`:
      `test_fastembed_is_a_core_dependency` (never skips),
      `test_build_embedder_returns_neural_under_plain_install` (skips
      only on a non-fastembed `EmbedderUnavailable`, skip reason naming
      this tranche), `test_hashing_escape_survives`, and confirm the
      existing forced-fallback test still asserts the
      `embedder-fallback` measure.
      done-when: `python -m pytest tests/test_embedder.py -q` → 0 failed (paste tail)

      PROOF:

          $ python -m pytest tests/test_embedder.py -q
          ..............                                        [100%]
          14 passed in 5.92s

      MUTATION PROOF (durable-tests rule 3 — the guarded claim was broken
      and the tests went red, including the one that must never skip):

          $ pip uninstall -y fastembed --break-system-packages -q
          $ python -m pytest tests/test_embedder.py -q -k "core_dependency or returns_neural"
          E  AssertionError: fastembed is missing, which is a packaging
             regression and never a reason to skip: fastembed not installed
          FAILED tests/test_embedder.py::test_fastembed_is_a_core_dependency
          FAILED tests/test_embedder.py::test_build_embedder_returns_neural_under_plain_install
          2 failed, 12 deselected in 0.12s

      Note the second line: with fastembed absent the weight-fetch test
      FAILS rather than skipping, which is the property R14 asked for.

      IN-SCOPE CORRECTION made by this step, recorded because it is a
      deletion: `tests/test_embedder.py` carried a module-level
      `fastembed = pytest.importorskip("fastembed")`. A `Skipped` raised
      at module scope skips the WHOLE module — so with fastembed absent,
      `test_fastembed_is_a_core_dependency` would have vanished silently
      instead of failing, which is the exact silence this tranche exists
      to remove. It is replaced by a comment; the `neural` fixture below
      it already skips on the one condition that warrants a skip
      (fastembed present, weights unfetchable), since `build_embedder`
      raises `EmbedderUnavailable` in both cases.

- [x] 5. (S8, census) Reword the `EmbedderUnavailable` message at
      `src/deepreason/llm/embedder.py:107-109` — it currently instructs
      installing an extra that is now empty — and update the two
      message assertions the census flagged EXPECTED TO MOVE
      (`tests/test_embedder.py:43`, `:193` if it asserts the same).
      done-when: `python -m pytest tests/test_embedder.py -q` → 0 failed, and `grep -n "deepreason\[embed\]" src/deepreason/llm/embedder.py` → no hits

      PROOF:

          $ python -m pytest tests/test_embedder.py -q
          ..............                                        [100%]
          14 passed in 5.51s
          $ grep -n "deepreason\[embed\]" src/deepreason/llm/embedder.py
          (no hits)

      The message now reads "fastembed not importable — reinstall the
      package (pip install -e . / pip install deepreason)". Only ONE
      assertion moved (`tests/test_embedder.py:111`), not the two the
      census allowed for: `:193`'s hit was the `neural` fixture's
      `pytest.skip(str(e))`, which passes the message through and
      asserts nothing about it. The moved assertion was STRENGTHENED,
      not weakened — `match="deepreason\[embed\]"` became
      `match="fastembed"` plus two explicit checks that the message
      still carries an actionable `pip install` and no longer names the
      empty extra.

- [x] 6. (S3, R4) Add the `embedder-warmup` subparser and
      `_cmd_embedder_warmup` to `src/deepreason/cli/main.py`: progress
      line to stderr naming the model, the 523 MB cost and the cache
      dir; fingerprint JSON to stdout; `--model` override; exit 1 with
      the typed reason on `EmbedderUnavailable`.
      done-when: `deepreason embedder-warmup 2>/dev/null | python -c "import json,sys; d=json.load(sys.stdin); assert {'model','version','sentinel'} <= set(d); print(d['model'])"` → the model id (paste), and the stderr progress line pasted

      PROOF — stdout (the typed fingerprint):

          nomic-ai/nomic-embed-text-v1.5
          {"model": "nomic-ai/nomic-embed-text-v1.5",
           "sentinel": "d6e3599ce0377000",
           "version": "fastembed-0.8.0+onnxruntime-1.28.0"}
          rc=0

      PROOF — stderr (the visible progress line R4 asked for):

          embedder-warmup: initializing nomic-ai/nomic-embed-text-v1.5
          (~523 MB of ONNX weights on first use, cached at
          /tmp/fastembed_cache); this is a one-time cost per cache, not
          per run ...
          embedder-warmup: ready in 4.3s — nomic-ai/nomic-embed-text-v1.5
          (fastembed-0.8.0+onnxruntime-1.28.0)

      The cache directory is DERIVED the way fastembed derives it
      (`FASTEMBED_CACHE_PATH`, else `fastembed_cache` under the system
      temp dir) rather than hardcoded, so the printed path is the real
      one on any machine. `EMBEDDER_MODEL` unset is NOT refused — it
      reports the hashing fingerprint and exits 0, per the
      all-configurations law (C6); only a genuinely unbuildable backend
      exits 1, which is a runtime failure at the point of use.

- [x] 7. (S3, R4) Add `warmup_command` to `doctor`'s existing
      `embedder` readiness block in `cli/main.py` (the dict at
      ~line 1493).
      done-when: the doctor readiness dict carries `"warmup_command": "deepreason embedder-warmup"` — prove with a direct call to the readiness function, pasted

      PROOF — `_doctor_policy_readiness(...)["embedder"]` called directly
      on this container, AFTER the packaging change:

          {
            "configured_backend": "configured_neural",
            "dependency_available": true,
            "failure_policy": "fallback",
            "fallback_active": false,
            "fallback_backend": "deterministic_hashing",
            "model": "nomic-ai/nomic-embed-text-v1.5",
            "ready": true,
            "warmup_command": "deepreason embedder-warmup"
          }

      Two things at once: the new field is present, and
      `dependency_available: true` / `fallback_active: false` is the
      tranche's whole point showing up in the preflight. Before step 2
      the same call on the same container returned false/true.

      The exact-dict assertion predicted at step 1 moved as predicted
      (`tests/test_schema_v3_consumers.py:97-105`, one key added, the
      other seven unchanged). Ring:

          $ python -m pytest tests/test_schema_v3_consumers.py -q
          ....                                                  [100%]
          4 passed in 0.36s

- [x] 8. (S3, S9) Add a CLI-level test for `embedder-warmup` (parser
      accepts it; the handler surfaces a typed failure rather than a
      traceback when the backend is unavailable).
      done-when: `python -m pytest tests/test_embedder.py -q` → 0 failed (paste tail)

      PROOF:

          $ python -m pytest tests/test_embedder.py -q
          .................                                     [100%]
          17 passed in 4.64s

      Three tests, all driving the REAL parser and `main()` rather than
      the handler directly, so a parser that stopped admitting the
      command would fail them:
      `test_embedder_warmup_reports_the_backend_a_run_will_use` (an
      unset EMBEDDER_MODEL is a chosen configuration, reported and
      exit 0, never refused — C6),
      `test_embedder_warmup_surfaces_a_typed_failure_not_a_traceback`
      (exit 1 with `EMBEDDER_WARMUP_UNAVAILABLE`, empty stdout, no
      traceback), and
      `test_embedder_warmup_names_the_real_cache_directory` (the printed
      path is derived, both branches asserted).

      ONE FAILURE, corrected within the step: the first version passed
      `--model ""` to mean "no model", but an empty string is falsy and
      fell through to the config default, so the test read
      `nomic-ai/nomic-embed-text-v1.5` where it expected `hashing-128`.
      Replaced with a real partial config (`EMBEDDER_MODEL: null`) via
      the global `--config`, which is how an operator would actually
      select the hashing road. The test's assertion was not weakened —
      it still demands `hashing-128`.

- [x] 9. (S4, S5, R5, R6) Correct `config.py`'s EMBEDDER_MODEL comment:
      drop `deepreason[embed]` and "atlas radii", state the 523 MB
      `/tmp/fastembed_cache` cost, name `deepreason embedder-warmup`,
      and state that the absolute distance knobs ship unset.
      done-when: `grep -n "deepreason\[embed\]\|atlas radii" src/deepreason/config.py` → no hits, and `grep -n "fastembed_cache" src/deepreason/config.py` → a hit

      PROOF:

          $ grep -n "deepreason\[embed\]\|atlas radii" src/deepreason/config.py
          (no hits)
          $ grep -n "fastembed_cache" src/deepreason/config.py
          527:    # (FASTEMBED_CACHE_PATH, else `fastembed_cache` under the system temp

      THREE false claims removed from a comment that operators and
      agents read as authority:
      (a) "Requires the optional dependency group (pip install
          'deepreason[embed]')" — false since step 2;
      (b) "~0.5 GB" — measured at 523 MB, and the location was never
          stated at all, which is the half that actually bites on a
          container where the cache lands in /tmp;
      (c) "EVERY distance threshold (NEAR_DUP_EPS, RESEED_DIST_MIN,
          atlas radii) is scale-specific: recalibrate ... before
          trusting a config on a new embedder" — this reads as though
          shipped values need recalibrating. They do not exist. Both
          named knobs default to None, no "atlas radii" knob exists in
          config at all, and the two knobs that DO ship armed are
          embedder-safe by construction. The corrected comment states
          the scale-specificity (still true) and that arming an
          absolute threshold is what requires calibration.

- [x] 10. (S4, S8, R5, R10, R11) Update the three docs: `CLAUDE.md`
      Environment section gains the disk-cost + warm-up line;
      `docs/EXPERIMENT_PROGRAM_2026-07.md:101` and
      `docs/SCRATCHPAD_GROUNDED_BRIDGE.md:83` stop instructing a manual
      `[embed]` install. Paste the R10 verification grep showing
      CLAUDE.md's `pip install -e .` lines are unchanged and still
      correct.
      done-when: `grep -rn "deepreason\[embed\]\|\.\[embed\]" --include=*.md --include=*.py . | grep -v "experiments/2026-08-16-change-embedder-auto-install" | grep -v "experiments/2026-08-13-change-lifecycle-operation-parity"` → no hits

      PROOF — R11 (no doc still instructs a manual extra install):

          $ grep -rn "deepreason\[embed\]\|\.\[embed\]" --include=*.md --include=*.py --include=*.sh . | grep -v .git | grep -v <this tranche> | grep -v <2026-08-13 PARKED ledger>
          (no hits)

      PROOF — R10 (CLAUDE.md's plain-install lines keep working
      unchanged by S1, VERIFIED BY GREP as the requirement asked):

          $ git diff CLAUDE.md | grep -E "^[-+].*pip install -e"
          +The embedder costs DISK, and the container clears it. `pip install -e .`

      The only `pip install -e .` line in the diff is an ADDITION, in the
      new prose. Neither of the two pre-existing install lines
      (`CLAUDE.md:72` in the rollback-recovery block, `:99` in Build and
      test) is added or removed, i.e. both are byte-identical and both
      now do strictly more than they did: the same command that installs
      the CLI installs the neural backend.

      ONE ITERATION within the step: the first wording of
      `docs/EXPERIMENT_PROGRAM_2026-07.md` kept the literal token while
      making the sentence historical ("needed a manual `.[embed]`
      install when E0.1 ran"), which is TRUE but left the grep dirty and
      would have made a future reader adjudicate instruction-vs-history.
      Reworded to "a manual optional-extra install", which preserves the
      historical fact and leaves the check unambiguous.

- [x] 11. (S12, R18) Update `docs/map/SUB-llm.md` in this same commit: a
      `Traps` entry naming the grounded-extension run
      (`experiments/2026-08-12-live-grounded-extension-expansion`, log
      seq 2/8) and ONE new executable `check:` asserting
      `pyproject.toml`'s dependency list carries fastembed — a check
      that would FAIL if it moved back to the extra. Advance
      `Verified-at:` only after re-running that document's checks.
      done-when: `python tools/docs_verify.py --only docs/map/SUB-llm.md` (or the full run filtered to that file) → the new check passes, and inverting the condition by hand makes it fail (paste both)

      NOTE on the command: `docs_verify.py` has no `--only` flag (its
      filters are `--fast`, `--failed`, `--ring`). Every one of
      SUB-llm.md's own `check:` lines was extracted and run instead,
      which is what the criterion meant:

          ALL 18 CHECKS EXIT 0

      PROOF — the new check passes:

          $ python -c "...pyproject core deps must carry fastembed, [embed] must be []..." \
              && grep -q '"embedder-warmup"' src/deepreason/cli/main.py \
              && python -m pytest tests/test_embedder.py::test_fastembed_is_a_core_dependency -q
          .                                                     [100%]
          1 passed in 0.08s
          rc=0

      MUTATION PROOF — fastembed moved back into the [embed] extra, the
      exact regression the check exists to catch, and the check goes red:

          core deps: ['pydantic>=2.7', 'pyyaml>=6.0']
          embed extra: ['fastembed>=0.3']
          AssertionError: ('fastembed must stay in the CORE dependency
            list', ['pydantic>=2.7', 'pyyaml>=6.0'])
          check rc=1
          --- restored; check green again ---
          check passes

      The check asserts BOTH halves of R1/R2 — fastembed in the core
      list AND the [embed] extra still declared and empty — plus that
      the warm-up command still exists, so removing either half of the
      tranche fails the map, not just the tests.

      `Verified-at:` advanced to this commit only because all 18 checks
      were actually re-run above.

- [x] 12. (A) [COMMIT] Ring for phase A, then commit and push.
      done-when: `python -m pytest tests/test_embedder.py tests/test_scratch_similarity.py tests/test_manifest_integration.py tests/test_schema_v3_consumers.py tests/test_wheel_operational.py -q` → 0 failed (paste tail); commit pushed; State line refreshed

      PROOF:

          $ python -m pytest tests/test_embedder.py tests/test_scratch_similarity.py \
              tests/test_manifest_integration.py tests/test_schema_v3_consumers.py \
              tests/test_wheel_operational.py -q
          ........................................................ [ 45%]
          ........................................................ [ 91%]
          ..............                                           [100%]
          158 passed in 41.22s

      Phase A closes: the dependency is core, the warm-up exists, the
      docs and the map moved with it, and every consumer the census
      named is green.

## Phase B — the fallback becomes loud

- [x] 13. (S6, S9, R8) Write the two results tests FIRST in
      `tests/test_results_command.py`:
      `test_results_surfaces_embedder_fallback` and
      `test_results_embedder_absence_is_typed`.
      done-when: `python -m pytest tests/test_results_command.py -q -k embedder` → both FAIL for the right reason (paste the failure, proving the guard bites before the change)

      PROOF — the guards bite before the reader exists (`-k` widened to
      `"embedder or neural_backend"`; the third test's name does not
      contain the substring "embedder", and the narrower selector
      silently ran only two of the three):

          $ python -m pytest tests/test_results_command.py -q -k "embedder or neural_backend"
          tests/test_results_command.py:693: KeyError
          FAILED ...::test_results_surfaces_the_embedder_and_names_a_fallback_loudly
          FAILED ...::test_results_names_the_neural_backend_when_no_fallback_happened
          FAILED ...::test_results_embedder_absence_is_typed_not_a_failure
          3 failed, 22 deselected in 3.64s

      All three fail with `KeyError: 'embedder'` — the reader has no such
      key yet, which is exactly the right reason.

      THREE tests, not the two planned. The third
      (`..._names_the_neural_backend_when_no_fallback_happened`) exists
      because a "fallback" label carries no information unless the
      no-fallback case renders differently; a test suite that only ever
      checked the fallback branch would pass against a reader that
      printed "(fallback)" unconditionally.

      Both fixtures are COMMITTED evidence selected by property, never
      by path (durable-tests rule 1, and this file's own stated
      discipline). Surveyed across all 107 tracked roots:
      4 carry an `embedder-fallback` Measure, 105 carry the `embedder`
      stamp, and 2 carry NEITHER — the absence case is real committed
      history, not a constructed corner.

- [x] 14. (S6, R8) Add `NO_EMBEDDER_RECORD` to `ABSENCE_REASONS` and
      `embedder_summary(harness)` to
      `src/deepreason/application/results.py`, reading the log's
      `embedder` / `embedder-fallback` Measure events.
      done-when: `python -c "from deepreason.application.results import embedder_summary; from deepreason.harness import Harness; print(embedder_summary(Harness('experiments/2026-08-12-live-grounded-extension-expansion/run', read_only=True)))"` → a block with `fallback: True` and model `hashing-128` (paste)

      PROOF — the grounded-extension root, read by the new function:

          {"backend": "hashing", "model": "hashing-128",
           "version": "1", "fingerprint": "4226e035204776db",
           "fallback": true,
           "configured_model": "nomic-ai/nomic-embed-text-v1.5",
           "fallback_reason": "fastembed not installed (pip install
             'deepreason[embed]'): No module named 'fastembed'"}

      That single block is the whole tranche's motivating fact, now
      readable: the run asked for neural geometry, got hashing-128, and
      the reason is quoted from its own log.

      LAST STAMP WINS, deliberately: an amended run continues into a new
      epoch and stamps again (this root carries stamps at seq 8 and seq
      10092), so the reported geometry is the one its final cycles used.

      The three step-13 tests still FAIL here, correctly — this step adds
      the function; step 15 wires it into `results_summary`.

      OBSERVED, not caused by this step, and PARKED rather than fixed:
      `experiments/jolt_architecture_2026-07-16/run` cannot be opened by
      `Harness()` at all (`UnsupportedRunManifestVersionError`: schema
      version 3). That is a pre-existing property of every reader that
      constructs a Harness, `deepreason results` included, and is exactly
      what the 2026-08-14 "old runs owe the future nothing" law
      contemplates. The absence fixture selects the SMALLEST root with no
      embedder stamp, which is
      `live_compare_2026-07-28/deepseek/shallow-runs/shallow-dc6fe3f9c26cede686906a16`,
      not the jolt root, so no test depends on it.

- [x] 15. (S6, R8) Wire it into `results_summary` as
      `summary["embedder"]` and render the glossed line in
      `render_results`.
      done-when: `deepreason results experiments/2026-08-12-live-grounded-extension-expansion/run | grep -i embedder` → a line containing `hashing (fallback)` (paste)

      PROOF — the grounded-extension run, through the public command:

          ## Measurement instrument
            embedder (the model that turned this run's text into vectors,
            so its novelty, near-duplicate and school-distance readings
            are on that model's scale): hashing (fallback) — this run was
            configured for nomic-ai/nomic-embed-text-v1.5 but could not
            build it, so it measured with hashing-128 instead; distance
            readings are on the lexical scale, not the configured one

      PROOF — a run that got the backend it asked for, so "(fallback)"
      still means something:

          ## Measurement instrument
            embedder (...): hashing (hashing-128)

      ON R8's LITERAL WORDING: the requirement says surface
      `"embedder: hashing (fallback)"`. The operative phrase
      `hashing (fallback)` is present verbatim; the colon falls after
      the in-line gloss because `render_results`'s own docstring makes
      glossing this surface's contract ("every technical label glossed
      in place... a label nobody can interpret sends them back to
      guessing"). Matching the literal string would have required
      dropping the gloss on the one command whose reason for existing is
      that operators could not interpret raw labels.

      ONE TEST ASSERTION CORRECTED within the step: the step-13 draft
      asserted `"embedder:" in rendered`, which the glossed line does not
      contain. Replaced with two STRONGER assertions — the rendered line
      carries `<backend> (<model>)`, and the no-fallback rendering must
      NOT contain `(fallback)`, so the alarm word cannot decay into
      decoration.

- [x] 16. (S6, R8, A3) Decorate the run's terminal summary at the print
      site in `_cmd_reason` (`cli/main.py`, beside the existing
      `payload["run_id"]`), leaving `run-result.json` untouched.
      done-when: `grep -n 'payload\["embedder"\]' src/deepreason/cli/main.py` → a hit adjacent to the `run_id` decoration, and `git diff --stat` shows no change under `src/deepreason/runtime/` or to any durable-sidecar writer

      PROOF — the decoration sits beside the two that were already there:

          2401:    payload["run_id"] = prepared.managed_run_id
          2403:        payload["evidence_dossier_digest"] = dossier_digest
          2409:    payload["embedder"] = embedder_summary(Harness(accepted.root, read_only=True))

      PROOF — no durable record format moved:

          $ git diff --stat d52c739ff -- src/deepreason/runtime/ \
              src/deepreason/application/text_runs.py \
              src/deepreason/application/models.py \
              src/deepreason/invariants.py src/deepreason/harness.py
          (empty)

      `run-result.json` on disk is untouched, `TextRunTerminalResultV1`'s
      strict schema is untouched, and `verify_root` sees nothing new.
      This is the smallest reading recorded as A3: the geometry is
      ALREADY in the log as Measure events — what was missing was a
      surface showing it to whoever launched the run, which is a
      presentation gap, not a record gap. The root is opened read-only,
      so reading a run's own result cannot repair (i.e. destroy) it.

- [x] 17. (S6, S9) Prove the two step-13 tests now pass and the rest of
      the results suite is unmoved.
      done-when: `python -m pytest tests/test_results_command.py tests/test_error_catalog.py -q` → 0 failed (paste tail)

      PROOF:

          $ python -m pytest tests/test_results_command.py tests/test_error_catalog.py -q
          .................................                     [100%]
          33 passed in 83.56s (0:01:23)

      The census's two predictions for this file both held: the
      key-enumerating tests absorbed the new `embedder` key and the new
      `NO_EMBEDDER_RECORD` absence reason without any assertion being
      weakened (`_key_shape` compares two roots against each other, so a
      key added to both sides stays consistent), and
      `tests/test_error_catalog.py` did not move — S6 added an absence
      REASON, which is a different vocabulary from the error catalog.

- [x] 18. (B) [COMMIT] Commit and push phase B.
      done-when: commit pushed; State line refreshed

      A REAL DEFECT WAS CAUGHT HERE by the map obligation, not by the
      ring, and it is worth recording as the strongest argument for the
      same-commit rule. `docs/map/SUB-application.md` covers
      `application/results.py`, so phase B owed it an update. Running
      that document's checks failed:

          E  AssertionError: assert 'Harness(' not in 'def _cmd_re...xit_code()\n'
          FAILED tests/test_application_text_runs_d0.py::
                 test_clients_have_only_thin_service_dispatch_and_one_registry

      Step 16 had written
      `embedder_summary(Harness(accepted.root, read_only=True))` directly
      into `_cmd_reason`, violating an architectural boundary the repo
      enforces by source inspection: CLI and MCP clients are THIN service
      dispatch and may not construct a `Harness`, a scheduler, or a stop
      policy of their own. The SPEC's blast-radius census did not surface
      it, because the guard greps the FUNCTION BODY rather than naming
      any symbol the census tracks.

      Fixed, not weakened: `embedder_summary_for_root(root)` was added to
      `application/results.py` — the layer that already opens roots for
      `results_summary` — and `_cmd_reason` calls that. The assertion is
      untouched and now passes:

          $ python -m pytest ...::test_clients_have_only_thin_service_dispatch_and_one_registry \
              ...::test_cli_and_mcp_handlers_are_thin_application_adapters -q
          ..                                                    [100%]
          2 passed in 0.28s

      A SECOND, SMALLER CATCH, from mutation-proving the map check I had
      just written: the first version asserted the decoration with
      `grep -q 'payload["embedder"] = embedder_summary'`, and commenting
      the line OUT still matched it — a check that cannot fail. Replaced
      with an AST assertion over `_cmd_reason`'s own body, which
      re-mutated correctly:

          --- mutated: decoration commented out ---
          AssertionError: the printed terminal payload must carry the embedder
          AST check rc=1
          --- restored ---
          AST check rc=0

      The same check now also asserts `Harness(` stays out of
      `_cmd_reason`, so the boundary this step violated is guarded from
      the map as well as from the test.

      `SUB-application.md`'s `Verified-at:` is deliberately NOT advanced.
      That document's full check set did not finish inside a 10-minute
      budget, so only the checks this change touches were re-run. A stale
      stamp is honest; a false one is not.

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
