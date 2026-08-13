# Spec: wheel-smoke re-pin + instrument currency audit

Derived from REQUEST.md R1-R11. The operator pre-answered every design
question in the tranche dispatch, so this SPEC records the acceptance
check for each requirement rather than proposing options.

## Acceptance checks

- **R1/R2/R3/R4 (smoke re-pin).** Run `python scripts/wheel_smoke.py` and
  `python -u scripts/wheel_operational_smoke.py` on the branch tip
  (`074ef1549`, then this tranche's own commits). Reconcile all four pin
  locations against the live surface by DIRECT EXTRACTION (import
  `deepreason.mcp_server._tools()`, hash it exactly as the instruments do
  — `json.dumps(tools, sort_keys=True, separators=(",",":"))` →
  sha256 — rather than reading the pinned constant and assuming it is
  right). Accept when: both instruments exit 0, and every pin (entry
  points, 4× tool-name sets, schema sha256, required modules) matches the
  direct extraction. If a mismatch is found, re-pin it and re-run to
  green in the same commit as the fix.
- **R5/R6 (attribution).** `git log --name-only a9d9b31a3..HEAD` filtered
  to the pin files and the four named surface files. For every commit
  that touches a surface file, read its diff and judge whether it added,
  removed, or renamed a console entry point, an MCP tool, the MCP schema
  shape, or a required wheel module — the only things the pins actually
  track — WITHOUT a same-commit pin update. Accept when the scan command
  and its full output are pasted, and each judged commit's verdict
  (violation / not a violation, with the reason) is recorded.
- **R7 (root sweep).** Run a sweep over every root under `experiments/`
  EXCEPT the named known-hang root, using a filtered copy of
  `tools/root_sweep.py` (identical logic, one path excluded) so the
  excluded root's presence is explicit in the output rather than silently
  absent. Accept when the sweep completes, the excluded root is named in
  the report, and every verdict is diffed against the last committed
  sweep (103 roots: 11 ERROR `UnsupportedRunManifestVersionError`, 84
  `valid=True`, 8 `valid=False`) — matches noted as "no anomaly",
  mismatches traced to the specific reader change that caused them (git
  blame on the relevant `src/` function).
- **R8 (docs currency).** `python tools/docs_verify.py` (full),
  `--audit`, `--links`. Accept when compared against the documented
  baseline (3 pre-existing `CON-run-identity.md` shallow-clone failures)
  with 0 unexplained deviation.
- **R9 (full gate).** `python -m pytest tests/ -q -n 4`, once. Accept
  when compared against the documented baseline (1 pre-existing
  `test_bronze_report.py` failure); any MCP-thread test failure is
  re-run in isolation (`-p no:xdist` or `-n0`) before being attributed to
  the known -n4 flake rather than a real regression.
- **R10 (scope discipline).** Any `src/` defect surfaced by R7-R9 that is
  NOT itself a stale pin is written to `PARKED.md` as a ready-to-send
  `dr-change-orchestrator`/`deepreason-orchestrator` prompt, not fixed
  here.
- **R11 (delivery).** A requirement-by-requirement report with pasted
  proof for R1-R10, committed and pushed at each phase boundary.

## Known constraint

This tranche's own commits (REQUEST.md, SPEC.md, CHECKLIST.md, etc.) are
themselves new files under `experiments/2026-08-13-change-smoke-currency-
audit/`, so the root sweep and docs_verify commands below are re-run
after each commit only if the commit touched something either instrument
reads (`src/`, `docs/map/`, or a committed run root) — a docs-artifact-only
commit does not require a re-run, per CLAUDE.md's ring-vs-boundary
discipline.
