# Request: wheel-smoke re-pin + instrument currency audit (full sweep)

Captured: 2026-08-13 from the task-dispatch message (operator authority via
the enclosing tranche instructions).

## Map preflight (recorded before any other artifact)

Resolved ids (`docs/map/INDEX.md` routing):

- `DR-SUB-periphery` (`docs/map/SUB-periphery.md`) — owns
  `src/deepreason/mcp_server.py`, the module whose `_tools()` output is
  what `scripts/wheel_smoke.py`/`scripts/wheel_operational_smoke.py`/
  `tests/test_mcp.py`/`tests/test_mcp_help.py` all pin (tool-name set +
  schema sha256).
- `DR-SUB-application` (`docs/map/SUB-application.md`) — owns
  `src/deepreason/cli/` (`cli/main.py`, the `deepreason` console entry
  point) and `src/deepreason/intake_form.py`.
- `INV-frozen-surfaces.md` read in full before touching anything: none of
  the five frozen surfaces (capability-state digests, `harness.py` event
  application, replay-validation record formats, manifest schemas +
  validators, qualification-subject digests) are touched by this tranche
  — it re-pins test/build instruments and audits ledger currency, no
  `src/` behavior changes are in scope unless Part 2 finds a real
  same-commit violation.
- **Map gap found during preflight, not fixed in this tranche** (out of
  scope for a pin-currency audit; noted for a future docs tranche):
  `docs/map/INDEX.md`'s "Subsystems" routing table (lines ~34-47) omits
  three subsystem documents that exist on disk and are `Owns:`-declared —
  `SUB-application.md`, `SUB-periphery.md`, `SUB-amendment.md`. A reader
  following INDEX.md's table alone would not discover that
  `mcp_server.py` (periphery) or `cli/` (application) have owning
  documents at all. `scripts/wheel_smoke.py`,
  `scripts/wheel_operational_smoke.py`, and `tools/root_sweep.py` /
  `tools/docs_verify.py` themselves have no owning map document anywhere
  — they are cross-cutting build/test instruments outside the map's
  13-subsystem scope (CLAUDE.md's "Build and test" section is their
  authority instead).

## Verbatim

> Tranche: full sweep — wheel-smoke re-pin + instrument currency audit.
> Route through the merged workflow (dr-change-orchestrator); no stops.

> AUTHORITY, operator verbatim (2026-08-12): "smoke is behind again. The
> workflow is failing big time." / "Also smoke needs updating." / "there
> needs to be a full sweep of repo again."

> PART 1 — SMOKE RE-PIN (the motivating defect). Run both instruments as
> they stand: python scripts/wheel_smoke.py; python -u
> scripts/wheel_operational_smoke.py. Capture the failures verbatim — they
> are the evidence of WHICH pins are stale. Then reconcile every pin
> against main's actual surface: console entry points, the MCP tool-name
> sets (ALL FOUR pin locations: wheel_smoke.py,
> wheel_operational_smoke.py, tests/test_mcp.py SUPPORTED_TOOLS,
> tests/test_mcp_help.py SUPPORTED_TOOL_NAMES), the MCP schema sha256
> (recompute by direct extraction, not eyeballing), and required wheel
> modules. Re-pin and re-run BOTH smokes green in the same commit. PROOF =
> pasted before-failure and after-pass output.

> PART 2 — ATTRIBUTION (errata, not blame-guessing). git log the pinned
> files and the surface files (mcp_server.py, intake_form.py, cli/main.py,
> pyproject.toml) since commit a9d9b31a3 to identify exactly which merged
> tranche(s) changed the public surface without updating the pins in the
> same commit — the same-commit rule is written law (CLAUDE.md, Build and
> test). Each confirmed violation is a docs/ERRATA_EXECUTOR.md entry
> naming the tranche and the commits (next entry follows the ledger's
> dating convention); the scan command and output are the proof either way.

> PART 3 — INSTRUMENT CURRENCY SWEEP (the "full sweep" half). (a)
> root_sweep.py full-tree run — EXCLUDE the known hang root
> experiments/live_tri_2026-07-27/run-c5ab654afd1b4aa131aede83bdca0f03
> (pre-existing parked performance defect; skip with a timeout guard or
> path filter, note it in the report; do NOT diagnose it here). Expected
> baseline: 11 ERROR lines (UnsupportedRunManifestVersionError); any OTHER
> verdict change from the last committed sweep is a finding — the reader
> moved with the recent merges, so re-derive and report which reader change
> moved which verdict. (b) docs_verify full, --audit, --links (baseline: 3
> pre-existing CON-run-identity.md shallow-clone failures). (c) full pytest
> gate once (baselines: 1 pre-existing test_bronze_report failure; 5
> MCP-thread tests known-flaky under -n 4, isolate before attributing).
> Fix ONLY instrument/pin staleness in this tranche; any src/ defect found
> is PARKED with a ready-to-send prompt.

> DELIVER: R-by-R with pasted proof; the sweep report (what moved, what
> did not, what was excluded and why); errata checkpoint (entries from
> Part 2, or the scan-proof of none). Commit and push every phase boundary
> (retry 2s/4s/8s/16s).

## Requirements (numbered for tracing)

- R1. Run `python scripts/wheel_smoke.py` and `python -u
  scripts/wheel_operational_smoke.py` as-is on the current branch tip;
  capture verbatim output as evidence.
- R2. Reconcile all pins against main's actual surface: console entry
  points (`pyproject.toml` `[project.scripts]`), the MCP tool-name set in
  all four pin locations, the MCP schema sha256 (recomputed by direct
  extraction), required wheel modules.
- R3. Re-pin whatever is stale and re-run both smokes to green, in the
  same commit as the re-pin.
- R4. PROOF: paste before-failure and after-pass output for both
  instruments.
- R5. `git log` the pinned files and the four named surface files since
  `a9d9b31a3`; identify any merged tranche that changed the public
  surface without updating the pins in the same commit.
- R6. Each confirmed R5 violation becomes a `docs/ERRATA_EXECUTOR.md`
  entry (tranche + commits named); if none, record the scan command and
  its empty result as proof of none.
- R7. `tools/root_sweep.py` full-tree run, excluding the known-hang root
  by a timeout guard or path filter (not diagnosed here); compare against
  the last committed sweep (103 roots, 11 ERROR
  `UnsupportedRunManifestVersionError`, 84 `valid=True`, 8 `valid=False`);
  report any OTHER verdict change and which reader change caused it.
- R8. `python tools/docs_verify.py` full, `--audit`, `--links`; compare
  against the documented baseline (3 pre-existing `CON-run-identity.md`
  shallow-clone failures).
- R9. Full pytest gate once (`python -m pytest tests/ -q -n 4`); compare
  against the documented baseline (1 pre-existing
  `test_bronze_report.py` failure; check the 5 known-flaky MCP-thread
  tests in isolation before attributing any failure to them).
- R10. Fix ONLY instrument/pin staleness in this tranche. Any `src/`
  defect discovered is PARKED with a ready-to-send prompt, not fixed
  here.
- R11. Deliver: requirement-by-requirement report with pasted proof; a
  sweep report (what moved, what did not, what was excluded and why); an
  errata checkpoint. Commit and push at every phase boundary, retrying
  push on network failure (2s/4s/8s/16s backoff).
