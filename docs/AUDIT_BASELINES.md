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
- **docs_verify** (`python tools/docs_verify.py`): 3 pre-existing
  failures, all `CON-run-identity.md` git-history checks — they
  require an unshallowed clone; on a full clone the expected value
  is 0 failed.
- **treadle doctor** (`tools/treadle/.venv/bin/treadle --repo . doctor`,
  with `OLLAMA_API_KEY` exported): expected **exit 0 and every line OK**
  — no `MISS`, no `WARN`. Recorded 2026-08-23 at install: 5 environment
  lines, 2 stage lines (`pilot`, `review`), credentials, and 3 model-tag
  lines (`gpt-oss:120b`, `deepseek-v4-pro:0813` twice). A `WARN
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

## Census anchors (move with the tree; verify before trusting)

- Committed-root census and per-root verdicts: the newest committed
  sweep output under `experiments/*sweep*` / the last audit tranche's
  `proof/broken-sweep.txt` is the comparison copy.
- Operator design laws: CLAUDE.md §"Operator design laws" is the
  authoritative list; `dr-audit-goal-trace` re-derives it each run.
