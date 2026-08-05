# Parked — noticed during the smoke tranche, not done

## S1 — the operational smoke's own loopback fixture stops serving, so it times out at `qualify` (SECOND DEFECT, blocks this GOAL's third criterion)

**This is why GOAL.md's `wheel_operational_smoke.py -> exits 0`
criterion is NOT met.** It is a defect distinct from the entry-point
reader, it is not caused by this tranche's change, and per the
orchestrator's stop condition ("a command fails twice the same way")
the dig was stopped and reported rather than improvised into a second
fix inside a one-goal tranche.

**The typed record, twice, identically:**

    "schema": "deepreason-wheel-operational-failure-v4",
    "stage": "qualify",
    "failure_kind": "timeout",
    "timeout": true,
    "mcp_liveness": "not_started",
    "first_lifecycle_state": "not_observed"

**Not caused by this tranche.** The complete diff to
`scripts/wheel_operational_smoke.py` is three lines — the schema sha and
two tool names — and all three are read at the MCP stage, which the run
never reaches (`mcp_liveness: not_started`). `STAGE_QUALIFY` precedes
them.

**What the evidence shows, and it is not slowness.** Measured on a
`--keep` run while it was stuck:

- The `deepreason qualify --yes` subprocess accumulated **2 seconds of
  CPU across 175 seconds elapsed, flat** across three samples. It is
  blocked, not working.
- Its main thread sits in `futex_do_wait`; its four worker threads all
  sit in `hrtimer_nanosleep` — the shape of a connect-fail/backoff loop,
  not of request processing.
- The qualify process holds **no socket file descriptors at all** (fds
  0, 1, 2 only).
- Nothing is listening on the profile's endpoint:
  `http://127.0.0.1:52037/v1` → `[Errno 111] Connection refused`, and no
  `/proc/net/tcp` LISTEN entry for that port exists.
- The smoke's own process, which starts the fixture as
  `threading.Thread(target=server.serve_forever, daemon=True)` at
  `scripts/wheel_operational_smoke.py:1245-1247`, was down to **one
  thread and zero socket fds** — the serving thread had exited and
  released the socket while the main thread went on waiting out the
  600s subprocess timeout.

**Ruled out — the container cannot serve loopback HTTP.** A control
`ThreadingHTTPServer` bound in the same container was reachable
immediately on its assigned port. Loopback TCP works here; this
fixture's server specifically stopped.

**What is NOT yet known**, and is the next tranche's job: why the
serving thread exits. Candidates not investigated — an unhandled
exception inside the handler killing `serve_forever`; the daemon thread
being reaped; a port-reuse or bind race; or an interaction with the
600s `_run` timeout path. The diagnosis should start from the record
(a `--keep` run with the server thread instrumented), not from reading
the handler.

**Why it did not surface before.** `wheel_smoke.py` has been red since
`4940b5f7` (2026-07-28) and CI runs the two smokes as consecutive steps
in the same job (`.github/workflows/wheel-smoke.yml`), so the operational
step has not been reached on a green predecessor in over a week. Fixing
the reader is what made this visible — which is the value of the fix,
not a regression from it.

Suggested disposition: its own `deepreason-orchestrator` tranche.

## S2 — both smokes carry byte-identical duplicate pins

`EXPECTED_MCP_TOOLS` and `EXPECTED_MCP_SCHEMA_SHA256` exist twice, once
in each script, and were identically stale before this tranche. Two
copies of one pin can drift apart, and the next person to refresh one
may not know the other exists. De-duplicating into a shared module is a
refactor rather than this defect, and would have required touching a
third file.

Suggested disposition: small change tranche.

## S3 — nothing in `docs/map/` covers `scripts/`

`grep -rl "wheel_smoke" docs/map/` → no hits. The map describes
`src/deepreason/` by charter, and `scripts/` is navigated by convention.
That was defensible while the smokes were invisible to the workflow;
`20f2c8d1` has just named them in `CLAUDE.md` as the third instrument,
so the gap is now a visible one. Not this tranche's job — the fix
touches no `src/` file, so nothing the map currently describes moved.

## S4 — carried, still parked

P1a (ERRATA E5 misidentifies the no-manifest three), P1b (the
delivery-measurement gap), P1e (a `src/` mutation inside a worktree is
never loaded under an editable install), and P7 (the round-robin arm's
`attempt-validity` violation) all remain open and untouched.
