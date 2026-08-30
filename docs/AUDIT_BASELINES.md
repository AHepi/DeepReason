# Audit baselines — expected instrument outputs

Read by the dr-audit family (PRECEDENCE 2): a delta from these values
is a finding; a match is disposition `baseline`. This file moves only
in a non-audit tranche, in the same commit as whatever moved the
value, with the audit family's close gate re-run there. A baseline
believed wrong during an audit is rowed and parked, never edited
mid-audit.

Recorded 2026-08-12 at main 074ef1549.

## Instruments

- **Full pytest gate** (`python -m pytest tests/ -q -n 4`):
  **0 failed.** The one long-standing pre-existing failure,
  `tests/test_bronze_report.py::test_census_totals_internally_consistent`
  (`assert 159 == 165`), is gone: the operator ruled the Bronze Flat v1
  census baseline irrelevant on 2026-08-13 and the test was deleted
  rather than re-baselined. The diagnosis prompt parked against it in
  `experiments/2026-08-09-change-judge-evidence-review/PARKED.md` P1 is
  therefore obsolete — do not pick it up.
  Known-flaky under `-n 4`, green in serial re-run: 3 tests in
  `tests/test_mcp_run.py`, 2 in `tests/test_mcp_scratch_bridge.py`
  (thread-join timing).
- **docs_verify** (`python tools/docs_verify.py`): **1249 checks over
  70 documents; 2 failed on a full clone, 5 failed on a shallow
  one.** Re-baselined 2026-08-30
  (`experiments/2026-08-30-fix-rotted-map-checks/`), which repaired FOUR
  of the six rows the 2026-08-29 baseline recorded. The shallow figure
  is MEASURED on this container; the full-clone figure is the shallow
  one minus the three git-history rows below, and is arithmetic rather
  than a measurement, because no full clone was available here.

  Expected failures, by class. A delta from THIS list is a finding; a
  match is disposition `baseline`.

  | where | class | why |
  |---|---|---|
  | `SEAM-llm-x-rules.md:54` | check malformed | a lost closing backtick merged the check with the paragraph after it. Reported as `unparseable check`, and the single finding keeping `--audit` above zero. Parked P3 (`experiments/2026-08-29-fix-docs-verify-multiline-checks/PARKED.md`). |
  | `INV-frozen-surfaces.md:181` | claim rotted | the census asserting ZERO committed `transport_failure` attempts; one exists, in a root committed 2026-08-26. Pre-existing, and its repair is a design fork rather than a count change — parked at `experiments/2026-08-30-fix-rotted-map-checks/PARKED.md` P-D3. |

  Plus, on a SHALLOW clone only, 3 more: `CON-run-identity.md:211`,
  `:213`, `:215` are git-history checks that need the full history.
  All three PASS after `git fetch --unshallow`; measured 2026-08-29,
  re-measured at their current line numbers 2026-08-30. A container
  that reports `git rev-parse --is-shallow-repository` as `true` will
  show 5, not 2, and those 3 are not findings.

  REPAIRED 2026-08-30 and no longer expected. A failure at any of these
  is a REGRESSION, not a baseline: `SEAM-llm-x-verification.md`'s
  crossing check (now pinning the exact import set in BOTH directions),
  `INV-frozen-surfaces.md`'s discharge-wire qualification-digest pin
  (re-pinned `b9038b84…` -> `02ee7e09…`, with a new check that the
  document's two pins agree), `CON-discharge-channel.md`'s carriage
  round trip (fixture rebound to `engaged_simulation_toolchain()`), and
  `INV-signal-contract.md`'s wander-registry decoupling check (now
  asserted over the unparsed AST rather than raw source text).

  CONTENTION, not findings — two rows in `SUB-application.md`, both
  measured on 2026-08-30 while a second `docs_verify` and two pytest
  gates ran concurrently on a 4-CPU box:

  - `:421` runs two pytest files, took 160.88 s on an idle box
    (2026-08-29) and 195 s serially on 2026-08-30, and TIMED OUT at the
    300 s check ceiling in both loaded full runs. A `TIMEOUT after 300s`
    there means the box was busy, not that the claim moved.
  - `:395` reported
    `test_restart_recovers_stale_preceding_epoch_without_redispatch`
    FAILED in one loaded run and PASSED serially minutes later on the
    same tree. It is a restart-timing test and it flakes under load.

  Both PASS when run alone. Never run the full gate and `docs_verify`
  at the same time (`dr-drive-harness` §5b); parked as P19
  (`experiments/2026-08-29-ultracode-batch-1/`). A docs_verify total
  taken under concurrent load is not admissible as a baseline.

  ENVIRONMENT, or the number is meaningless: this container resolves
  `python` to `/usr/local/bin/python` while `pip` resolves to
  `/usr/bin/pip`, so `pip install -e .` arms a DIFFERENT interpreter
  than the checks invoke and every `python -m pytest` check dies with
  `No module named pytest`. Measured cost of getting this wrong: 502
  failures, none of them real. Run `python -m pip install -e . pytest
  pytest-xdist jsonschema --break-system-packages` and confirm
  `python -m pytest --version` before trusting any docs_verify total.

- ~~**docs_verify**, superseded 2026-08-29~~ (`python tools/
  docs_verify.py`): "3 pre-existing failures, all `CON-run-identity.md`
  git-history checks — they require an unshallowed clone; on a full
  clone the expected value is 0 failed." Kept visible because tranche
  artifacts cite it, and because HOW it was wrong is the lesson.

  It undercounted BY CONSTRUCTION. The parser (`tools/
  docs_verify.py:47`) required a check's opening and closing backtick
  on one line, and the parse loop had no `else`: a column-0 `check:`
  opener it could not read was discarded with no output at all. 72
  such openers stood across 27 map documents — concentrated in the
  INV- documents, because a claim strong enough to need an invariant
  is usually defended by a multi-statement block. So the old "0 failed
  on a full clone" was a statement about 1141 checks presented as a
  statement about the map, and 4 of the 5 non-shallow failures now
  listed above were already true when it was recorded. The instrument
  cannot regress this way again: an opener the grammar cannot parse is
  now a loud `unparseable check` failure, never a skip.
- **treadle doctor** (`tools/treadle/.venv/bin/treadle --repo . doctor`,
  with `OLLAMA_API_KEY` exported): expected **exit 0 and every line OK**
  — no `MISS`, no `WARN`. Recorded 2026-08-23 at install: 5 environment
  lines, 3 stage lines (`pilot`, `review`, `review_full`), credentials,
  and 4 model-tag lines (`gpt-oss:120b`, `deepseek-v4-pro:0813` three
  times). The line COUNT moves whenever `treadle.toml` gains or loses a
  stage or a `context_files` entry — compare the OK/WARN/MISS verdicts,
  not the arithmetic. A `WARN
  credentials` line is baseline ONLY when the key is unset — with the key
  exported it is a finding. A `WARN model tag ... NOT on endpoint` is
  always a finding: hosted checkpoints are retired without notice, and
  that line is how this repo learns. `NOTE model-tag check skipped` means
  the endpoint was unreachable, which is a network fact, not a verdict —
  re-run before rowing it. If `tools/treadle/.venv` is absent the
  container has rolled back; rebuild it per `tools/treadle/VENDORED.md`
  before treating anything here as a delta.
- **Sweep scope under the 2026-08-14 law** (CLAUDE.md, "Old runs owe
  the future nothing"): the sweep's obligation is CURRENT-VERSION roots
  only — a committed root's verdict may not move while current readers
  don't change. Rows for prior-version roots are historical; new ERROR
  lines appearing because a format moved on are the law working, not a
  finding. Replay-byte-unchanged proofs over historical roots are no
  longer gate obligations anywhere.
- **root_sweep — RETIRED as an instrument** (operator ruling
  2026-08-22, ledgered in CLAUDE.md §Build and test): no audit, gate,
  or grant runs it anymore; reader changes are proven by targeted
  regression tests instead. The historical baseline below is kept only
  so old tranche artifacts that cite it remain interpretable.
- ~~**root_sweep**~~ (`python tools/root_sweep.py`): 11 ERROR lines, all
  `UnsupportedRunManifestVersionError`. Known hang (pre-existing,
  parked): `experiments/live_tri_2026-07-27/
  run-c5ab654afd1b4aa131aede83bdca0f03` — run the sweep under
  `timeout` and exclude this root; the timeout firing THERE is
  baseline, anywhere else is a finding.
- **Wheel smokes** (`python scripts/wheel_smoke.py`;
  `python -u scripts/wheel_operational_smoke.py`): expected exit 0
  both. KNOWN STALE at recording time — a re-pin tranche is in
  flight; until it lands, smoke failures naming MCP schema sha or
  tool-set pins are baseline-listed as pending that tranche, and any
  OTHER smoke failure is a finding.
  The `reason`-stage failure `terminal verification is incomplete`
  (`_assert_resumable_terminal`) was a FINDING from 2026-08-15
  (`a476c564f`) and is FIXED as of 2026-08-21,
  `experiments/2026-08-21-fix-wheel-smoke-reason-stage/`. It is recorded
  here as a fixed value, NOT as a carve-out: seeing it again is a
  finding, not a baseline. It never was flaky — the one contrary
  observation died at an earlier stage that shares the `reason` label
  in the failure envelope.

- **Cycle soak** (`python -u scripts/cycle_soak.py --case epoch3`):
  **expected exit 0.** The pre-launch instrument added 2026-08-23
  (`experiments/2026-08-23-change-cycle-soak-instrument/`). Like the wheel
  smokes, NO gate runs it — it is minutes-long and is run by hand before a
  live launch. It drives `TextRunApplicationService` for 8 cycles on the
  launch config's own shape against the wheel smoke's stub, and asserts a
  typed terminal, no `operational_failure`, a clean `verify_root`, and a
  cycle depth past 2 (the deepest of the four recorded 2026-08-22 deaths).
  Its exit status is three-valued and the distinction is load-bearing:
  **0** clean, **1** a real regression, **3** ONLY seams listed in the
  script's `EXPECTED_RED` map failed. Exit 3 is a baseline value only while
  that map is non-empty; an empty map plus exit 3 is a finding.
  Seam dispositions are recorded per run in `<out>/soak-report.json`. A
  seam reported `not-coverable` or `partial` is NOT coverage — see that
  tranche's RESULTS.md for the standing honesty rows.
  `--induce-repairs N` is a PROBE, not part of this baseline: it makes the
  stub answer the run's first N wire schemas unusably once, to reach the
  repair ladder the always-valid stub cannot. **It now exits 0** — it exited 1
  on a `workflow-call-pairing` violation until
  `experiments/2026-08-25-defect-workflow-call-pairing/` fixed the verifier
  (the check compared an absent raw blob spelled `None` on the durable attempt
  against the same absence spelled `""` on the call). Seeing exit 1 under the
  probe again is a FINDING, not a baseline. The baseline proper remains the
  bare invocation above.
  `EXPECTED_RED` is now EMPTY, and that is its correct resting state: its one
  entry (`D4-reservation-bound`) outlived its fix and was removed by the same
  tranche. While the map is empty `_verdict` cannot return 3, so the
  "empty map plus exit 3" finding above is unreachable rather than latent.

## Census anchors (move with the tree; verify before trusting)

- Committed-root census and per-root verdicts: the newest committed
  sweep output under `experiments/*sweep*` / the last audit tranche's
  `proof/broken-sweep.txt` is the comparison copy.
- Operator design laws: CLAUDE.md §"Operator design laws" is the
  authoritative list; `dr-audit-goal-trace` re-derives it each run.
