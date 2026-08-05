# Goal: the operational smoke's embedded loopback provider stops serving during qualify; make both smokes exit 0
Class: defect
Observed: `python -u scripts/wheel_operational_smoke.py` fails at
`STAGE_QUALIFY` with a typed record —
`{"schema":"deepreason-wheel-operational-failure-v4","stage":"qualify",
"failure_kind":"timeout","timeout":true,"mcp_liveness":"not_started"}` —
twice, identically. The `deepreason qualify --yes` subprocess is BLOCKED,
not slow: measured across three samples it held 2 seconds of CPU against
175 seconds elapsed, flat, with its four worker threads in
`hrtimer_nanosleep` and zero socket file descriptors. Nothing was
listening on the profile's endpoint (`http://127.0.0.1:52037/v1` →
`[Errno 111] Connection refused`, no `/proc/net/tcp` LISTEN entry), and
the smoke's own process was down to one thread holding no socket — the
`threading.Thread(target=server.serve_forever, daemon=True)` started at
`scripts/wheel_operational_smoke.py:1245-1247` had exited. A control
`ThreadingHTTPServer` bound in the same container was reachable
immediately, so the container is not at fault. Evidence:
`experiments/2026-08-05-fix-smoke-entry-point-reader/PARKED.md` S1 and
`VERIFY.md`.

Success criterion (machine-decidable):

    python scripts/wheel_smoke.py
    -> exits 0

    python -u scripts/wheel_operational_smoke.py
    -> exits 0

    python -m pytest tests/ -q -n 4
    -> ends "0 failed" (3338 today; no existing assertion weakened)

    python tools/docs_verify.py
    -> "docs_verify: 0 failed"

In scope (3):
- `scripts/wheel_operational_smoke.py` — the embedded deterministic
  provider fixture and its server lifecycle.
- Whatever the captured exception implicates, which may be the fixture's
  request/response handling OR the product-side request shape that
  reaches it. The operator's instruction is explicit: "Fix fixture or
  reader as evidence dictates."
- `scripts/wheel_smoke.py` only if the same cause reaches it (it
  currently exits 0 and must continue to).

NOT in scope until the evidence names it: any `src/` change. The fixture
is a test double; a product change to satisfy a double is backwards
unless the double is right and the product is wrong, which is exactly
what the captured exception must decide. If the evidence does implicate
`src/`, that widens the tranche and the widening is recorded before any
edit, not after.

Budget: <=150 changed lines, 1 commit, ~2 hours.
Stop conditions inherited from orchestrator: yes — including "a command
fails twice the same way", which this defect has already triggered once
and which ended the previous tranche's dig.

## Method constraint from the operator, binding on dr-diagnose

> "Diagnose WHY the daemon thread exits: capture the thread's actual
> exception first — run with --keep and read the daemon's stderr/log
> before theorizing."

No hypothesis is admissible before the exception is in hand. The
previous tranche established WHERE the failure is and explicitly did
not establish WHY; that boundary is the starting line here.

> "Note the suspect window: the fixture last ran clean 2026-07-27, and
> the rung program changed provider-profile and config surfaces since —
> the fixture may be choking on a request shape it predates."

Recorded as a HYPOTHESIS TO TEST, not a conclusion to confirm. The
record decides; a suspect window that the exception contradicts is a
finding, not something to explain away.

## Map preflight (resolved ids)

`docs/map/` describes `src/deepreason/` and owns nothing under
`scripts/` (`grep -rl "wheel_operational" docs/map/` → no hits), which
the previous tranche already recorded as finding S3. Ids that bound the
work if the evidence crosses into `src/`:

- `DR-INV-frozen-surfaces` — read before designing. Surface 5
  (qualification subject digests) and surface 4 (manifest schemas AND
  validators) are both plausibly adjacent, because the failing stage IS
  `qualify` and the operator's suspect window names provider-profile and
  config surfaces.
- `DR-SUB-manifest` — owns `run_manifest.py` and qualification.
- `DR-SUB-periphery` — owns the MCP/CLI edge the smoke drives.
- `DR-SUB-llm` — owns the adapter and endpoint layer that would build
  whatever request shape reaches the fixture.

## Prior process errors not to repeat

Kill by PID, never by pattern: `pkill -f wheel_operational_smoke` and
`pgrep -f "bin/deepreason qualify" | xargs kill` each matched the
session's own shell command line and killed it (exit 144), twice, in the
previous tranche. The operator's instruction repeats this
("kill processes by PID not pattern") and it is treated as binding.
