# Verification

## Criterion command + output

GOAL.md's four criteria, run verbatim at `82ffff57`, each instrument
alone:

    $ python scripts/wheel_smoke.py
    wheel smoke passed: isolated V6-only contents, clean imports, exact
    entry points, module parity, MCP registration, and exact MCP schemas
    rc=0
    -> PASS

    $ python -u scripts/wheel_operational_smoke.py
    ::error title=DeepReason installed-wheel operational smoke failed::
    {"schema":"deepreason-wheel-operational-failure-v4","stage":"qualify",
     "failure_kind":"timeout","timeout":true,"mcp_liveness":"not_started", ...}
    rc=1
    -> FAIL, blocked by a SECOND defect (PARKED.md S1). Not caused by
       this change; see below.

    $ python -m pytest tests/ -q -n 4
    3338 passed, 7 skipped in 738.52s (0:12:18)
    rc=0
    -> PASS (0 failed)

    $ python tools/docs_verify.py
    docs_verify [full]: 51 documents, 815 checks, 4 workers
    docs_verify: 0 failed
    -> PASS

Three of four met. The fourth is blocked by a defect this tranche found
rather than caused, and the honest verdict below says so instead of
reporting the three as a clean sweep.

## What the fix proves

The entry-point reader — the defect the tranche exists for — is fixed
and the instrument runs to completion. `wheel_smoke.py` now executes
PAST the line that had been raising since `4940b5f7` (2026-07-28) and
into `_check_mcp`, which had not run since 2026-07-26. Both stages pass.

Mutation-proven on real wheel bytes, before the assertions were
committed:

| mutation | result |
|---|---|
| real wheel, real pins | PASSED |
| pin forgets the adapters group | FAILED (group-set mismatch) |
| a console script changed | FAILED |
| an adapter added without updating the pin | FAILED |

The third and fourth rows are what make this more than a symptom fix:
before the change, the smoke asserted console scripts by equality and
asserted NOTHING about the adapters group, so a vanished adapter would
have passed unnoticed. It now cannot.

## The two pins, and why refreshing them is not rubber-stamping

The smoke exists to catch UNINTENDED drift, so a pin refresh is only
correct if the drift is intended. Both additions verified against the
record before acceptance:

| tool | landed in | documented |
|---|---|---|
| `amend_run` | `0a946726` "Implement amendment epochs" | `README.md` — "amend_run carries exactly the CLI amend…" |
| `run_findings` | `73e05bdc` "Add findings command" | `README.md` MCP tool table |

Nothing was REMOVED (`only pinned: []`), so the drift is purely
additive from two documented features, and the pin last moved at
`82c73367` — which predates both. Refreshed in BOTH scripts, which held
byte-identical stale copies: 18 → 20 tools, sha `7520ea29…` →
`39d73561…`, and both verified equal to the live facade afterwards.

## Record-behavior preservation

No run root, reader or validator is touched — the change is confined to
two files under `scripts/`, which `src/` never imports. `docs_verify`
`0 failed` and the gate's `3338 passed` are unchanged from the P1
tranche's numbers, so nothing in the record moved.

Adjacent test file re-run directly: `tests/test_wheel_operational.py`
→ `108 passed`. It asserts on the operational smoke's internals, not on
the pins or the reader.

## The blocked criterion, characterised rather than waved away

`wheel_operational_smoke.py` times out at `STAGE_QUALIFY`, twice,
identically. Full analysis in PARKED.md S1. The three findings that
make it a real defect rather than an environment excuse:

1. **It is blocked, not slow.** The `qualify` subprocess accumulated
   **2s of CPU across 175s elapsed, flat** across three samples; its
   four worker threads sat in `hrtimer_nanosleep` and it held **zero
   socket fds**.
2. **Its fixture is not serving.** Nothing listens on the profile's
   `http://127.0.0.1:52037/v1` (`[Errno 111] Connection refused`, no
   `/proc/net/tcp` LISTEN entry), and the smoke's own process was down
   to **one thread with no socket** — the
   `threading.Thread(target=server.serve_forever, daemon=True)` started
   at `scripts/wheel_operational_smoke.py:1245-1247` had exited.
3. **The container is not at fault.** A control `ThreadingHTTPServer`
   bound in the same container was reachable immediately.

Not caused by this tranche: the complete diff to that script is three
lines — the sha and two tool names — all read at the MCP stage, which
never starts (`mcp_liveness: not_started`).

Why it took until now to see: `wheel_smoke.py` has been red since
`4940b5f7`, and `.github/workflows/wheel-smoke.yml` runs the two smokes
as consecutive steps in one job, so the operational step has not run on
a green predecessor in over a week. **Fixing the reader is what made
this visible** — the fix's value, not a regression from it.

## Verdict: **PASS on the goal's defect; FAIL on the goal's full
criterion, blocked by a second defect**

The entry-point reader is fixed, proven, and its instrument is green.
The MCP pins are refreshed and verified. The gate and the map are
unchanged and clean. GOAL.md's criterion nonetheless is not fully met,
because it required BOTH smokes to exit 0 and the operational one is
blocked by a distinct defect that this tranche surfaced and parked
under its stop condition ("a command fails twice the same way").

Recording this as a partial rather than as a PASS is the point: a
tranche that reported green here would be claiming the operational
surface is verified when it has not run to completion since
2026-07-27.

## Residue (honest)

- **S1 — the operational smoke's loopback fixture stops serving.** The
  next tranche, with the evidence above as its starting record. Until
  it lands, the operational half of the public surface remains
  unverified, and no amount of green from `wheel_smoke.py` changes
  that.
- **S2 — the duplicated pin.** Two byte-identical copies across two
  scripts; refreshing one and not the other is a live drift hazard,
  and this tranche had to update both by hand.
- **S3 — `docs/map/` covers no part of `scripts/`.** Newly relevant now
  that `CLAUDE.md` names the smokes as the third instrument.
- **Two self-inflicted process errors, recorded so they are not
  repeated**: `pkill -f wheel_operational_smoke` and
  `pgrep -f "bin/deepreason qualify" | xargs kill` each matched this
  session's own shell command line and killed it (exit 144), twice. Kill
  by PID, or filter the pattern against your own command line.
- **P1a, P1b, P1e and P7 remain parked** and untouched.
