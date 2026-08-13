# Parked (not done, not promised)

## P1 — `preflight_harness`'s returned notices are not printed/logged anywhere

**What:** After this tranche, `preflight_harness` returns
`tuple[CompileNoticeV1, ...]` instead of always `None` (SPEC.md S3), but
no caller (`ops.run_scheduler`, `cli/main.py`'s `reason`/`continue`
commands, `scripts/jolt_*.py`) prints or otherwise surfaces that value —
they all call it as a bare statement today and continue to. This means
the disclosure this tranche adds is visible to a caller that reads the
return value in code (tests, a future script), but not to an operator
watching stderr the way `cli/main.py:857`'s `NOTICE {code}: {message}`
print already surfaces `compile_run_manifest`'s notices at `config
compile` time.

**Why parked, not fixed here:** REQUEST.md's authority (C3, the
frozen-surface grant) scopes this tranche to `run_manifest.py`'s two
call-site conversions; wiring `ops.py`/`cli/main.py` to consume and print
the new return value touches files outside that grant for a
nice-to-have display improvement, not a requirement — SPEC.md's
Assumption A3 records the reasoning. This is also not a defect (nothing
is broken; the information is simply not yet displayed), so it does not
belong in a `deepreason-orchestrator` diagnosis tranche either — it is a
follow-up CHANGE.

**Ready-to-send prompt for the follow-up tranche:**

```
Change tranche: surface preflight_harness's disclosure notices (added
experiments/2026-08-13-change-calibration-receipt-notice/) to the
operator, mirroring cli/main.py:857's existing
`print(f"NOTICE {code}: {message}", file=sys.stderr)` pattern for
compile_run_manifest's compile_notices. Route through
dr-change-orchestrator.

Scope: ops.run_scheduler's call site (ops.py:372) and any CLI command
that calls it (cli/main.py's `reason`/`continue` commands) should log or
print preflight_harness's returned tuple[CompileNoticeV1, ...] when
non-empty, so an operator running a live command sees the same
disclosure a `config compile` run already sees for compile-time notices.
scripts/jolt_*.py's two call sites are lower priority (jolts forbid all
status authority per JOLT_STATUS_AUTHORITY_FORBIDDEN, so the tuple will
always be empty there).

End state: an operator running `deepreason reason` (or `continue`) with
an unsatisfiable calibration-receipt configuration sees a NOTICE line on
stderr identical in spirit to the compile-time one, not just a silently
discarded return value.
```
