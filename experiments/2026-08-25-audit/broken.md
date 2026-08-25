# Dimension: broken code

Broken means an instrument's output moved from `docs/AUDIT_BASELINES.md`
§Instruments. The instruments define broken; this worker adds no judgment
of its own.

| id | instrument | result | baseline | verdict | proof |
|---|---|---|---|---|---|
| B1 | `python -m pytest tests/ -q -n 4` | **4162 passed, 6 skipped, 0 failed** (998s) | 0 failed | **baseline** | proof/broken-gate.txt |
| B2 | `python tools/docs_verify.py` | 64 docs, 1069 checks, **3 failed** | 3 pre-existing `CON-run-identity` git-history failures | **baseline** | proof/docs-full.txt |
| B3 | `python scripts/wheel_smoke.py` | exit 0 | exit 0 | **baseline** | proof/wheel-smoke.txt |
| B4 | `python -u scripts/wheel_operational_smoke.py` | exit 0 | exit 0 | **baseline** | proof/wheel-operational-smoke.txt |
| B5 | root sweep | NOT RUN | retired 2026-08-22 | **baseline** | proof/broken-sweep.txt |
| B6 | `treadle doctor` | NOT RUNNABLE | exit 0, every line OK | **no evidence** | proof/treadle-doctor.txt |
| B7 | `cycle_soak.py --case epoch3` | NOT RUN | exit 0 | **baseline (not applicable)** | proof/cycle-soak.txt |

## All live instruments are at baseline

**B1.** 4162 passed, 6 skipped, 0 failed. No failure to re-run serially,
so no `flaky` row. Note for CLAUDE.md's benefit rather than as a finding:
its §Build and test still says "expect ~3100 passed" — the tree is at
4162.

**B2.** The three failures are `CON-run-identity.md:200`, `:202`, `:204`,
two of them reporting `fatal: ambiguous argument '<sha>': unknown
revision`. The baseline attributes exactly this to an unshallowed clone.
Cause **confirmed rather than assumed**: `git rev-parse
--is-shallow-repository` → `true`, `git rev-list --count HEAD` → 54.
Detail in `docs-drift.md`.

**B4 is the one worth reading.** It passed every stage: installed setup,
explicit qualification (80 qualification calls, 418 total), readiness,
question-only reasoning, **replay-verified terminal retrieval**, cache
reuse, opaque MCP restart, budget ceiling, and pre-V6 fail-closed
admission. Two baseline notes are discharged by this:

- The baseline marks the wheel smokes "KNOWN STALE at recording time — a
  re-pin tranche is in flight". Both smokes now pass clean, so the pins
  match the surface.
- The baseline records the `reason`-stage failure `terminal verification
  is incomplete` (`_assert_resumable_terminal`) as FIXED on 2026-08-21,
  and explicitly says "seeing it again is a finding, not a baseline."
  It did not recur. The stage that carries that assertion —
  replay-verified terminal retrieval — is green.

## Two instruments produced no verdict, and are recorded that way

**B6 `treadle doctor` — not runnable, and this is NOT a delta.** Both
prerequisites are absent: `tools/treadle/.venv/bin/treadle` does not
exist, and `OLLAMA_API_KEY` is unset with no `experiments/*/env` file to
recreate it from. The baseline anticipates the first case exactly: "If
`tools/treadle/.venv` is absent the container has rolled back; rebuild it
per `tools/treadle/VENDORED.md` before treating anything here as a
delta."

An instrument that could not run has produced no evidence in either
direction. Rowing it `baseline` would claim a green it never gave;
rowing it `broken` would invent a failure. It is rowed **no evidence**
and parked as **P6** so the next session with credentials runs it. This
matters more than the usual missing-instrument case, because the
baseline says a `WARN model tag ... NOT on endpoint` line "is always a
finding: hosted checkpoints are retired without notice, and that line is
how this repo learns" — that early-warning channel is currently dark.

**B7 cycle soak — not run, correctly.** The baseline records it as a
PRE-LAUNCH instrument: "Like the wheel smokes, NO gate runs it — it is
minutes-long and is run by hand before a live launch." This audit is
read-only by the operator's own instruction and launches nothing, so the
condition that makes the soak meaningful does not exist. Not-run is the
correct state here, not an omission.

**Count line: 7 instruments rowed — 5 baseline, 1 no-evidence (parked),
1 not-applicable. 0 broken, 0 flaky.**
