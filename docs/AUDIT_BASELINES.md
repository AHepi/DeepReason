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
  repair ladder the always-valid stub cannot. Under it the soak currently
  exits 1 on a `workflow-call-pairing` violation, parked as P1 in that
  tranche. Do not read that exit as a baseline delta; the baseline is the
  bare invocation above.

## Census anchors (move with the tree; verify before trusting)

- Committed-root census and per-root verdicts: the newest committed
  sweep output under `experiments/*sweep*` / the last audit tranche's
  `proof/broken-sweep.txt` is the comparison copy.
- Operator design laws: CLAUDE.md §"Operator design laws" is the
  authoritative list; `dr-audit-goal-trace` re-derives it each run.
