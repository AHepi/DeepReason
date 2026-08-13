# Delivered: wheel-smoke re-pin + instrument currency audit (full sweep)
Branch: `claude/sweep-smoke-currency-2-e6kh3King` (pushed, tree clean)

## What changed

Nothing in `src/`. This tranche's job was to find and fix stale pins in
the two wheel-smoke instruments and confirm the rest of the repo's
self-checking instruments (the root sweep, the docs map's re-derivation
checks, the pytest gate) are still telling the truth after the last few
merged tranches. The finding, stated plainly because it runs against the
tranche's own motivating premise: **no pin was stale.** Both
`scripts/wheel_smoke.py` and `scripts/wheel_operational_smoke.py` passed
on their first run against the current branch tip, and a full
direct-extraction reconciliation (recomputing the MCP tool-name set and
schema hash live from `deepreason.mcp_server._tools()`, not reading the
pinned constants and trusting them) confirmed all four pin locations
already agree with the live surface, byte for byte.

## Reconciliation against REQUEST.md

- **R1** (run both smokes as-is): PASS. Both passed cleanly, verbatim
  output pasted in CHECKLIST.md Step 1.
- **R2** (reconcile all pins by direct extraction): PASS. Entry points,
  the MCP tool-name set in all 4 locations, the schema sha256
  (recomputed, not eyeballed), and required wheel modules all confirmed
  current — CHECKLIST.md Step 2.
- **R3/R4** (re-pin + re-run green, PROOF): satisfied by the
  reconciliation standing in place of a fix — there was nothing to
  re-pin. Both instruments were already green; that IS the after-pass
  proof.
- **R5/R6** (attribution scan): PASS. `git log a9d9b31a3..HEAD` filtered
  to the pin files and the four named surface files found one touching
  commit (`e9a1a878c`); its full diff was read and judged not a
  violation — it changed CLI/intake internal behavior, never a console
  entry point, MCP tool, schema shape, or required module. Zero
  violations found; no `docs/ERRATA_EXECUTOR.md` entry written (a
  "nothing found" entry would misrepresent an absence as a finding —
  CHECKLIST.md Step 3 carries the full reasoning as the record instead).
- **R7** (root sweep): PASS. 102 of 103 committed roots swept (the one
  named hang root excluded by a scratch path-filtered copy of the
  instrument's own logic, not diagnosed). Byte-identical, per root and
  per column, to the last committed raw sweep file once the excluded
  root and whitespace are normalized out. Zero verdicts moved across two
  intervening reader changes (`85717580f`, `6e1623db2`) — the complete
  answer to "which reader change moved which verdict" is "neither did."
- **R8** (docs currency): PASS. Full/`--audit`/`--links` all match the
  documented baseline exactly (3 pre-existing `CON-run-identity.md`
  shallow-clone failures; 0 audit findings; 0 dangling links).
- **R9** (full gate, once): PASS. `1 failed, 3539 passed, 7 skipped` —
  the same pre-existing `test_bronze_report.py` assertion
  (`159 == 165`) the last two tranches also recorded. Zero MCP-thread
  failures; no isolation re-run needed.
- **R10** (scope discipline): PASS. The one `src/`-adjacent finding
  (root_sweep.py's general per-root slowdown, not just the named hang
  root) was NOT diagnosed or fixed — parked as P1 with a full
  diagnostic-starting-point prompt.
- **R11** (delivery): this document, plus CHECKLIST.md's step-by-step
  proof and PARKED.md's follow-on.

## The one real finding: root_sweep.py's general throughput

Excluding only the one already-known, already-parked hang root, a
straight serial re-run of `tools/root_sweep.py`'s own logic hit a
45-minute wall-clock guard at 34/102 roots — individual roots costing
30-125 seconds each. No prior committed report times this instrument's
per-root cost, so there is no baseline to compare against, but this pace
implies a full serial sweep now takes on the order of 90-100 minutes,
which is a plausible second contributor (beyond any pin drift, of which
none was found) to the operator's "the workflow is failing big time."
Completed for THIS run by parallelizing the independent, read-only
per-root checks across 4 processes in a scratch wrapper — `tools/
root_sweep.py` itself is untouched, and the parallel run's output is
byte-identical to the serial baseline, so the workaround did not change
what was measured, only how long measuring it took. Diagnosing WHY the
per-root cost grew this large is parked (P1), not investigated here —
out of a pin-currency tranche's scope.

## Map delta

None. `INV-frozen-surfaces.md` was read in full before starting (none
of the five frozen surfaces were touched); the map gap found during
preflight (`INDEX.md`'s Subsystems table omits `SUB-application.md`,
`SUB-periphery.md`, `SUB-amendment.md`) is noted in REQUEST.md but not
fixed — out of scope for a pin-currency tranche, not promised as done
here.

## Errata

None. Part 2's attribution scan (REQUEST.md R6) found zero same-commit
violations, so no `docs/ERRATA_EXECUTOR.md` entry was warranted — an
absence of evidence is not itself a correction to record. This
constitutes the tranche's errata checkpoint: scan performed, proof
pasted (CHECKLIST.md Step 3), nothing to enter.

## Parked (not done, not promised)

- **P1** — `tools/root_sweep.py`'s general per-root throughput
  degradation (30-125s/root, independent of the one named hang root).
  Full ready-to-send prompt in `PARKED.md`.

## PROOF (gate output, not the word "done")

```
$ python scripts/wheel_smoke.py
wheel smoke passed: isolated V6-only contents, clean imports, exact
entry points, module parity, MCP registration, and exact MCP schemas

$ python -u scripts/wheel_operational_smoke.py
wheel operational smoke passed: installed setup, explicit qualification
(80 qualification calls; 418 total calls), readiness, question-only
reasoning, replay-verified terminal retrieval, cache reuse, opaque MCP
restart, budget ceiling, and pre-V6 fail-closed admission

$ python -m pytest tests/test_mcp.py tests/test_mcp_help.py -q
89 passed in 1.22s

$ python tools/docs_verify.py
docs_verify: 3 failed   (documented baseline)
$ python tools/docs_verify.py --audit
docs_verify --audit: 0 finding(s)
$ python tools/docs_verify.py --links
docs_verify --links: 0 dangling reference(s), 53 document(s)

$ python -m pytest tests/ -q -n 4
1 failed, 3539 passed, 7 skipped in 775.26s (0:12:55)   (documented baseline)
```

Full detail, per-root sweep diff, and per-commit attribution judgment
are in `CHECKLIST.md`.
