# Parked findings — adjudication / judge-seats / legacy-criticism / schools opt-ins

Findings surfaced during this tranche's own execution and validation that
are real, but out of this tranche's scope to fix — per CLAUDE.md's
cross-routing rule, "a defect found mid-change is PARKED, not fixed... One
tranche, one goal." Each below was investigated with real evidence, not
assumed pre-existing.

## 1. `test_bronze_report.py::test_census_totals_internally_consistent` — pre-existing, unrelated

Fails: `assert counts["gate_blocked"] == census["streams"][stream]["gate_measures"]`
→ `159 == 165`. Reproduces deterministically (identical numbers across
three separate full-gate runs this tranche).

`census` is built by `scripts/bronze_census.py::build_census()`, scanning
the committed, historical `experiments/bronze_flat_2026-07-13/` roots.
Neither that script nor that directory was touched by this tranche
(`git diff --stat 81d08e5f0.. -- scripts/bronze_census.py
experiments/bronze_flat_2026-07-13/` is empty).

**Confirmed pre-existing**, not this tranche's: reproduced against the
tranche's TRUE base commit (`81d08e5f0`) in an isolated `git worktree`,
before any of this tranche's changes — identical failure, identical
numbers (`159 == 165`).

Operator's own words (2026-08-11), accepting this as a documented
exception: "62 may not be possible as old experiments represent old
choices I made. Anyway, continue."

**Recommended next step:** a dedicated tranche to re-derive
`bronze_census.py`'s gate-measure accounting against the July 13th roots,
or to determine whether the historical data itself needs re-processing.

## 2. `tools/root_sweep.py` hangs indefinitely on one specific historical root

`python tools/root_sweep.py <output>` does not terminate. Run, monitored,
and killed after 1h37m pinned at ~100% CPU with zero forward progress.

`strace -p <pid> -f` showed it repeatedly issuing `newfstatat` probes
against dozens of type-prefixed object paths (`objects/capability-*/…`,
all `ENOENT`) for one specific root:
`experiments/live_tri_2026-07-27/run-c5ab654afd1b4aa131aede83bdca0f03` — an
ordinary-sized root (508 log lines, 711 objects, 5.2 MB total), not one
that should plausibly take this long.

**Not this tranche's:** the only production code this tranche's own fix
(Step 61) changed is one narrowed early-exit branch in
`verification/report.py::authority_differences` — no new lookup, no loop,
no new object read. `verify_root_report` called DIRECTLY (not through
`root_sweep.py`'s full-tree driver) on two other v6 roots
(`experiments/live_engaged_2026-07-27/run-f4fa6663e5412d64df943a5a22342baf`,
`experiments/bronze_pilot_2026-07-14`) completed normally in under 90
seconds each — the hang is specific to this one root, or to something in
`root_sweep.py`'s own driving of the object-store lookup for it, not a
general slowdown from this tranche's changes.

**Recommended next step:** a dedicated tranche to profile
`verify_root_report`/the content-addressed object-store lookup path
specifically against `live_tri_2026-07-27/run-c5ab654afd1b4aa131aede83bdca0f03`
— likely a pathological branch in a type-guessing linear scan over
candidate object-type directories, worth fixing once (it may affect other
roots with a similar content shape, not just this one).

## 3. `test_mcp_run.py`/`test_mcp_scratch_bridge.py` — transient parallel-execution flakiness, not filed as a defect

Five tests (`test_start_poll_result_and_progress_notifications`,
`test_cancel_waits_for_safe_boundary`,
`test_typed_v6_stop_can_continue_and_append`,
`test_bridge_start_poll_result_claims_and_unresolved_success`,
`test_progress_callback_failure_cannot_relabel_success`) failed on ONE of
three full-gate runs during this tranche's validation, all on
`thread.join(timeout=5)` / `not thread.is_alive()` assertions under `-n 4`
parallel CPU contention. All 5 passed cleanly re-run in isolation, and none
failed on the other two full-gate runs (before and after the isolated
re-run). Zero code overlap with anything this tranche touched.

Not filed as a tracked defect — recorded here only so a future session
that hits the same non-deterministic failure recognizes it instantly
rather than re-diagnosing it, and so it isn't silently absent from this
tranche's record. If it recurs reliably (not just once under load), it's
worth a dedicated look at whether these tests' fixed 5-second timeouts are
too tight for a loaded CI machine.
