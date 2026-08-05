# Goal: the operational smoke must report what happened when it fails
Class: defect
Observed: `scripts/wheel_operational_smoke.py` discards its own failure
evidence in three distinct places, so a failing run names a stage and
almost nothing else. Measured across the two preceding tranches:

1. `_run` catches `subprocess.TimeoutExpired` (~line 1475) and raises
   `OperationalSmokeFailure(stage=..., failure_kind=FAILURE_TIMEOUT,
   timeout=True) from None`, never reading `TimeoutExpired.stdout` or
   `.stderr`. The cause of the S1 hang lived entirely in that discarded
   stream; it had to be re-derived by instrumenting the child from
   outside the instrument.
2. `except AssertionError:` (~line 3610) builds the record with no
   message and no traceback. When the smoke failed with
   `failure_kind: assertion_failed`, identifying WHICH of the qualify
   stage's two assertions fired required reading the source and running
   an external poller.
3. `--keep` preserves the temp directory only on SUCCESS
   (`if succeeded and args.keep`), i.e. never when there is something to
   inspect. The T1 counts had to be captured by a background process
   copying the state file mid-run before cleanup deleted it.

Evidence: `experiments/2026-08-05-fix-loopback-fixture-daemon/PARKED.md`
T2, and the diagnosis history of
`experiments/2026-08-05-fix-smoke-entry-point-reader/` and
`experiments/2026-08-05-fix-loopback-fixture-daemon/`.

Success criterion (machine-decidable):

    # a failing run must name its assertion
    python -u scripts/wheel_operational_smoke.py 2>&1 | grep -q "qualification did not make exactly"

    # a failing run must preserve its temp directory under --keep
    python -u scripts/wheel_operational_smoke.py --keep ; ls -d /tmp/deepreason-wheel-operational-*/
    -> at least one directory survives a FAILING run

    python scripts/wheel_smoke.py            -> exits 0
    python -m pytest tests/ -q -n 4          -> ends "0 failed"
    python tools/docs_verify.py              -> "docs_verify: 0 failed"

Note: the smoke's own exit code is expected to remain 1 until T1 is
resolved. This tranche makes the failure LEGIBLE; it does not make it
go away, and a fix that made the smoke pass would be out of scope.

In scope (1):
- `scripts/wheel_operational_smoke.py` — the three concealment sites.

NOT in scope:
- **The typed failure record's shape.** `OperationalSmokeFailure` is
  documented "Fixed, payload-free", its stage/kind/detail vocabularies
  are closed, and `tests/test_wheel_operational.py::
  test_v4_diagnostic_fields_types_and_allowlists_are_closed` pins the
  v4 field set. That closure is load-bearing, not incidental: the smoke
  asserts via `_assert_no_disclosure` that no output or state file ever
  contains the repository path or `TEST_CREDENTIAL`. Raw child output
  in a machine-readable record is exactly the disclosure that assertion
  exists to prevent. **Diagnostics therefore go to a human-facing
  stream, scrubbed; the v4 record stays closed and payload-free.**
- T1 (the 280-vs-300 call-count pin) — the operator's own sequencing:
  T2 first, then T1 with the doctor report preserved.
- `_provider_server`/`ProviderState` dead code, and
  `_unused_loopback_port`'s bind-then-release race.

Budget: <=150 changed lines, 1 commit, ~1 hour.
Stop conditions inherited from orchestrator: yes.

## Map preflight

`docs/map/` owns nothing under `scripts/` (recorded as S3 in the
previous tranche). No `src/` file is touched, so no map document's
claims move. `DR-INV-frozen-surfaces` read: none of the five surfaces
is under `scripts/`.
