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
- **diff_budget** (`python tools/diff_budget.py <base> --ceiling N --paths …`):
  the verdict is `WITHIN`/`EXCEEDED` against RAW INSERTIONS in the named paths,
  and a ceiling set on an estimate of CODE will be exceeded by documentation.
  Operator ruling 2026-09-02: **count executable lines when setting a ceiling**,
  and read an `EXCEEDED` verdict against the measured split before treating it
  as a finding. Worked instance: tranche
  `experiments/2026-09-02-defect-hv-v6-reachability/` returned
  `{"total_insertions": 210, "ceiling": 150, "verdict": "EXCEEDED"}` over four
  files of which roughly 95 lines were executable and 115 were module and
  function docstrings, comments and blanks — the docstrings stating constraints
  the code cannot show, which the tranche's own `REC-` recipe then points a
  future reader at. The instrument is not wrong; a ceiling that counts prose as
  code is. The tool has no `--executable-only` mode today, so the disposal is by
  hand: measure the split before rowing the verdict.

- **docs_verify** (`python tools/docs_verify.py`): **1291 checks over 71
  documents** as of 2026-08-31 (was 1250 over 70 when this entry was written;
  the total moves with every tranche that adds a check and is NOT a pinned
  value — the failure LIST below is what a delta is measured against). On this container's SHALLOW clone the total is 5 OR 6 failed;
  on a full clone, 2 or 3.** The two-valued total is a measured property of
  the documented command on a 4-CPU box, not sloppiness — see the
  CONTAINER-CONDITIONAL row below, which is the whole of the difference.
  Re-baselined 2026-08-30
  (`experiments/2026-08-30-fix-rotted-map-checks/`), which repaired FOUR of
  the six rows the 2026-08-29 baseline recorded; CORRECTED later the same day
  after independent review showed the first version of this entry had recorded
  a single unreplicated LOW observation as a fixed value. The full-clone
  figures are the shallow ones minus the three git-history rows below —
  arithmetic, not a measurement, because no full clone was available here.

  Totals actually observed for this command in one evening, same container:
  **10, 7, 5** (that lane's three runs, on trees that were still moving),
  **6** (independent reviewer, this tree), **5 and 5** (two fresh runs on the
  final tree, 2026-08-30 04:04-04:34 UTC, recorded because a baseline resting
  on one observation is what produced this correction). The reviewer's 6 was
  the five rows below plus the container-conditional row.

  Expected failures, by class. A delta from THIS list is a finding; a
  match is disposition `baseline`.

  | where | class | why |
  |---|---|---|
  | `SEAM-llm-x-rules.md:54` | check malformed | a lost closing backtick merged the check with the paragraph after it. Reported as `unparseable check`, and the single finding keeping `--audit` above zero. Parked P3 (`experiments/2026-08-29-fix-docs-verify-multiline-checks/PARKED.md`). |
  | `INV-frozen-surfaces.md:181` | claim rotted | the census asserting ZERO committed `transport_failure` attempts; one exists, in a root committed 2026-08-26. Pre-existing, and its repair is a design fork rather than a count change — parked at `experiments/2026-08-30-fix-rotted-map-checks/PARKED.md` P-D3. |
  | `SUB-application.md`, the check pairing the `validated_post_terminal_drift` greps with a pytest run | RETIRED as a conditional row, 2026-08-31 | it was conditional because it ran two whole pytest files and cost **160.88 s, 182.8 s, 186.9 s, 195 s, 213.1 s** in five serial timings — 54-71% of docs_verify's own 300 s per-check ceiling (`tools/docs_verify.py:185`) before sharing 4 CPUs with the 3 other workers the same command starts. `experiments/2026-08-31-defect-jailbreak-gate-closure` narrowed it to the four node ids that exercise the claim, measured at **1 s**. A failure here is now a REGRESSION, not a baseline. Anchored by what the check RUNS, not by a line number — see `docs/ERRATA.md` E67. P-D8 is closed by that narrowing. |

  **Disposing of the conditional row takes one command**, and an audit must
  run it before rowing a delta: re-run that check alone
  (`python tools/docs_verify.py --failed`, or paste the check's own command).
  A PASS means the ceiling and the row is `baseline`; a FAIL means the claim
  moved and it IS a finding. The same command settles `:395` — see below.

  Plus, on a container that has not fetched every branch a check reads, 1
  more: `INV-frozen-surfaces.md`'s judge-canary row runs
  `experiments/2026-09-01-defect-judge-canary-compile-gap/price_compile_gap.py`,
  which does `git show origin/claude/deepreason-p-s1-commitments-wowcib:…`.
  A container cloned for a different branch does not have that ref and the
  check dies with `exit status 128`, which looks exactly like a code failure
  and is not. `git fetch origin claude/deepreason-p-s1-commitments-wowcib`
  makes it pass; measured 2026-09-02
  (`experiments/2026-09-02-defect-hv-v6-reachability/`). This row is the same
  class as the three below — an ENVIRONMENT precondition, not a claim that
  rotted — and it is listed separately because it is not fixed by
  `--unshallow`.

  Plus, on a SHALLOW clone only, 3 more: `CON-run-identity.md:211`,
  `:213`, `:215` are git-history checks that need the full history.
  All three PASS after `git fetch --unshallow`; measured 2026-08-29,
  re-measured at their current line numbers 2026-08-30. A container
  that reports `git rev-parse --is-shallow-repository` as `true` will
  show 5 or 6, not 2 or 3, and those 3 are not findings.

  REPAIRED 2026-08-30 and no longer expected. A failure at any of these
  is a REGRESSION, not a baseline: `SEAM-llm-x-verification.md`'s
  crossing check (now pinning the exact import set in BOTH directions,
  resolving package-leaf imports, and pinning the module-level/
  function-local split of every crossing),
  `INV-frozen-surfaces.md`'s discharge-wire qualification-digest pin
  (re-pinned `b9038b84…` -> `02ee7e09…`, with a new check that the
  document's two pins agree), `CON-discharge-channel.md`'s carriage
  round trip (fixture rebound to `engaged_simulation_toolchain()`), and
  `INV-signal-contract.md`'s wander-registry decoupling check (now
  asserted over the unparsed AST rather than raw source text).

  `SUB-application.md:395` is LOAD, not a conditional row, and the two are
  not in the same class. It reported
  `test_restart_recovers_stale_preceding_epoch_without_redispatch` FAILED in
  one loaded run and PASSED serially minutes later on the same tree; two
  fresh serial trials cost 23.2 s and 23.0 s, so it has no margin problem at
  all — it is a restart-timing test that flakes when the box is busy. Dispose
  of it with the same one command.

  ADMISSIBILITY, restated honestly because the earlier wording could not be
  met here. Never run the full gate and `docs_verify` at the same time
  (`dr-drive-harness` §5b); parked as P19
  (`experiments/2026-08-29-ultracode-batch-1/`). But the rule this entry used
  to state — "a docs_verify total taken under concurrent load is not
  admissible as a baseline" — is not achievable on this container: NO full run
  of the instrument here has been taken on a proven-idle box, including the
  ones behind the figures above (load average 1.9 rising to 4.9 across run 1),
  and the documented command self-contends regardless of what else is running.
  Commit `7fbbf2bc2` labelled one such run "quiet box"; that label was wrong
  and is corrected in
  `experiments/2026-08-30-fix-rotted-map-checks/DELIVERY.md` §11.3. What
  replaces the rule: a total from this container is admissible only as the
  RANGE above with its container-conditional row named, and every delta is
  disposed of by re-running the specific failing check ALONE before it is
  rowed.

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
