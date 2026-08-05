# Results — the wheel smoke's entry-point reader

## 2026-08-05 — a section-blind parser, and the defect it was hiding

**What was observed.** `scripts/wheel_smoke.py` had been red since
`4940b5f7` (2026-07-28). Its reader collected every non-blank,
non-`[`-prefixed line of the wheel's `entry_points.txt` into one set and
compared it for equality against the two console scripts. That commit
added a legitimate `[project.entry-points."deepreason.admission.adapters"]`
group, so the `epub` and `pdf` entries read as unexpected console
scripts. The error message named its own defect: two of the four
"console entry points" it listed were not console entry points.

**What the record showed.** `entry_points.txt` is INI — the same
`name = target` line is a console script or a plugin depending only on
the `[group]` header above it — and the reader skipped those headers
instead of switching on them. The packaging was correct throughout;
only the instrument was wrong.

**What was fixed.** The reader parses by group and compares each group
against `REQUIRED_ENTRY_POINT_GROUPS`, which pins the GROUP SET as well
as each group's contents. That second half matters: before, the smoke
asserted console scripts by equality and asserted nothing about the
adapters, so a vanished adapter would have passed unnoticed. Fixing
only the reported symptom would have traded one blind spot for another.
Mutation-proven four ways on real wheel bytes.

Because the reader raised before `_check_mcp`, the MCP tool set and
schema sha had gone unverified since 2026-07-26 and were both stale in
BOTH scripts, which carried byte-identical copies. Refreshed to 20 tools
(`+amend_run`, `+run_findings`) and sha `39d73561…`, after verifying
both additions are documented public surface (`0a946726`, `73e05bdc`,
`README.md`) and that nothing had been removed. This is the
same-commit pin rule's (`20f2c8d1`) first exercise, and the inverse case
it exists to prevent: the surface changed and the pin never followed.

**What the record now shows.** `wheel_smoke.py` rc=0 — "isolated V6-only
contents, clean imports, exact entry points, module parity, MCP
registration, and exact MCP schemas". Full gate `3338 passed, 0 failed`;
`docs_verify` `51 documents, 815 checks, 0 failed`.

**The residue, which is the more important half.** Fixing the reader let
the operational smoke run for the first time in over a week, and it
fails — `stage: qualify`, `failure_kind: timeout`, twice identically.
Its own in-process loopback fixture stops serving: the qualify
subprocess accumulated 2s of CPU across 175s elapsed with four workers
asleep and no sockets, nothing listened on the profile endpoint, and the
smoke's process was down to one thread with its `serve_forever` daemon
gone. A control server in the same container was reachable, so the
container is not at fault, and the three-line pin diff cannot reach a
stage that never started.

So the public surface is half-verified, and the honest statement is that
the operational half has not been proven since 2026-07-27. Accepted does
not mean true; green on one instrument does not mean green on the
surface it shares with another. S1 carries the evidence a follow-up
tranche needs.
