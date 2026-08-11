# Parked: automatic blast-radius analysis in the skills workflow

Deliberately not fixed by this tranche — named here rather than
silently passed over, per this repo's own convention.

## P1 — `tests/test_bronze_report.py::test_census_totals_internally_consistent`, pre-existing failure

`assert counts["gate_blocked"] == census["streams"][stream]["gate_measures"]`
fails `159 == 165` on every full-gate run in this environment.

**Verified pre-existing, not caused by this tranche** (VALIDATION.md):
reproduced identically, deterministically (no `-n` parallelism), and
again in an isolated `git worktree` at this tranche's own base commit
(`25686797`), before any of this tranche's own changes. This tranche
touches zero lines of `scripts/bronze_census.py`,
`tests/test_bronze_report.py`, or `experiments/bronze_flat_2026-07-13/`
— entirely outside its own scope (a blast-radius disclosure tool and
three skill-checkpoint amendments).

Not diagnosed further here — one tranche, one goal. A future
`deepreason-orchestrator` tranche (dr-set-goal → dr-diagnose) should
pick this up if the operator wants it fixed; likely candidates worth
checking first (not investigated here): a retained-data directory
(`experiments/bronze_flat_2026-07-13/`) that may not be fully checked
out in this container's shallow clone, mirroring the same class of gap
`CON-run-identity.md`'s three pre-existing failures show for git
history depth.
