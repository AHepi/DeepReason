# Verification

## Criterion command + output

    # a failing run names its assertion
    $ python -u scripts/wheel_operational_smoke.py --keep
    --- assertion failed (qualify) ---
    qualification did not announce the frozen maximum

    Traceback (most recent call last):
    --- end assertion failed (qualify) ---
    --- retained artifacts ---
    temp root kept for inspection: /tmp/deepreason-wheel-operational-0s4jo3nt
    --- end retained artifacts ---
    -> PASS

    # a failing run preserves its temp directory under --keep
    $ ls -d /tmp/deepreason-wheel-operational-*/
    /tmp/deepreason-wheel-operational-0s4jo3nt/
    -> PASS (the run exited 1; the artifacts survived)

    $ python scripts/wheel_smoke.py            -> rc=0        PASS
    $ python -m pytest tests/ -q -n 4          -> 3338 passed, 7 skipped, 0 failed   PASS
    $ python tools/docs_verify.py              -> docs_verify: 0 failed              PASS
    $ python -m pytest tests/test_wheel_operational.py -q -> 108 passed, UNEDITED    PASS

    $ python .../repro.py
    VERDICT: 0 of 3 concealments present       (was 3 of 3)                          PASS

The operational smoke still exits 1. That is the declared expectation,
not a shortfall: GOAL.md scoped this tranche to making the failure
LEGIBLE, and stated that a fix which made the smoke pass would be out of
scope. T1 owns the failure itself.

## What the fix asserts now

| concealment | before | after |
|---|---|---|
| child output on `TimeoutExpired` | dropped (`from None`, never read) | reported to stderr, redacted |
| `AssertionError` message | dropped (handler bound no name) | message + traceback, redacted |
| `--keep` on failure | temp dir deleted | retained, path printed, `cleanup_completed: True` |

The typed v4 record is unchanged — same field set, same closed
vocabularies, same `OperationalSmokeFailure` signature. Its closure is
load-bearing (`_assert_no_disclosure` proves no output carries the repo
path or `TEST_CREDENTIAL`; a test pins the field set), so the fix added
a channel beside it rather than widening it. Verified the channel
respects that guarantee:

    repo path removed : True
    credential removed: True
    rest preserved    : True

`repro.py`'s third check was rewritten from a source grep to a
behavioural probe — the success-path guard legitimately remains, so its
presence proved nothing — and mutation-proven: disabling retention turns
it red.

## Corrupted measurements, and the clean one

Three gate runs this session were invalidated by load I created myself
(U3). The authoritative run was taken with `ps` confirmed idle and
nothing else scheduled:

    3338 passed, 7 skipped in 691.84s   rc=0   no failures

The intermediate readings (`3 failed`, `1 failed`, `4 failed`) are
recorded in PARKED.md U1/U3 rather than deleted, because a measurement
taken against a box the measurer loaded is a specific, repeatable
mistake and the record should say so.

## Verdict: **PASS**

All five criteria met. The instrument now reports what happened when it
fails, and proved it within minutes of landing by correcting a wrong
inference this session had already committed to writing (U2).

## Residue (honest)

- **T1 is next and is now better shaped.** The assertion that fires is
  the announced-maximum pin (840), not the call-count pin (280 vs 300)
  the previous tranche predicted from the stage name. Both are shadows
  of one contract-pair inventory, so T1 should ask its
  regression-or-correct question once about the inventory (U2).
- **U1** — a second parallel-load flake, distinct from the documented
  one, in `test_criticism_school_execution_c3.py`.
- **U3** — my own measurement discipline; worth a line in `CLAUDE.md`'s
  gate discipline, since it cost ~40 minutes here.
- **Untouched and still parked** from earlier tranches: T3 (dead
  `_provider_server`/`ProviderState`), T4 (`_unused_loopback_port`'s
  bind-then-release race), S2 (duplicate MCP pins), S3 (`docs/map/`
  covers no part of `scripts/`), P1a, P1b, P1e, P7.
- **Not proven**: that these three were the ONLY places the smoke drops
  evidence. Three were found by needing them; a systematic audit of
  every `except` in the file was not done.
