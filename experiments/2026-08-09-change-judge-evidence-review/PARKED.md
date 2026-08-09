# Parked — found during the judge-evidence review, not fixed here

Cross-routing rule (CLAUDE.md, `.claude/skills/README.md`): a defect found
mid-change is parked, not fixed. Both items below were discovered while
running the full gate at this tranche's validation boundary
(VALIDATION.md); this tranche is READ-ONLY archaeology and made zero
`src/`/`tests/` changes (tripwire diff 0), so neither could have been
caused by it, and neither is fixed here.

## P1 — `test_census_totals_internally_consistent` fails deterministically, independent of this tranche

**What.** `tests/test_bronze_report.py::test_census_totals_internally_consistent`
fails even run in isolation: `assert counts["gate_blocked"] ==
census["streams"][stream]["gate_measures"]` → `159 == 165` for one bronze
stream's census row. Proven pre-existing: `git diff origin/main...HEAD --
experiments/bronze_flat_2026-07-13/ tests/test_bronze_report.py
scripts/bronze_census.py` → 0 lines; this failure is present on
`origin/main` (`b5921b3a`) unchanged by anything in this tranche.

**Ready-to-send prompt for a future tranche:**

> Route: `deepreason-orchestrator` (something is broken).
> Goal: `tests/test_bronze_report.py::test_census_totals_internally_consistent`
> fails with `assert 159 == 165` (gate_blocked count vs gate_measures count
> mismatch for one bronze stream) on `origin/main` at `b5921b3a` — diagnose
> why `scripts/bronze_census.py`'s gate-blocked count and the harness's own
> gate-Measure count over `experiments/bronze_flat_2026-07-13/` disagree by
> 6, and fix the reader (never the committed root, per
> `docs/map/INV-frozen-surfaces.md`).
> Evidence: pasted gate output and isolation re-run in
> `experiments/2026-08-09-change-judge-evidence-review/VALIDATION.md`
> ("Full gate" section).
> End state: the test passes; `pytest tests/ -q -n 4` reports 0 failed.

## P2 — three `docs_verify` checks in `CON-run-identity.md` fail under this container's shallow clone

**What.** `python tools/docs_verify.py` reports 3 FAIL at
`CON-run-identity.md:195,197,199` — each check's `git log`/`git show` call
against a specific historical commit hash (`1637e808`, `f304fec1`, etc.)
returns `fatal: ambiguous argument '<hash>': unknown revision`. Proven
environment-caused, not tranche-caused: `git diff origin/main...HEAD --
docs/map/CON-run-identity.md` → 0 lines (this tranche never touched the
document), and `git rev-parse --is-shallow-repository` → `true` — this
container's clone does not carry the commit depth these checks require.

**Ready-to-send prompt for a future tranche:**

> Route: `deepreason-orchestrator` (something is broken) OR a maintenance
> note in `docs/map/SCHEMA.md` if the operator prefers documenting the
> constraint over changing it.
> Goal: `python tools/docs_verify.py` reports 3 FAIL at
> `CON-run-identity.md:195,197,199` in any shallow-clone container
> (`git rev-parse --is-shallow-repository` → `true`) because the checks'
> `git log`/`git show` calls reference specific historical commit hashes
> outside the shallow fetch depth. Either (a) confirm this is expected in
> shallow environments and add a documented `git fetch --unshallow` (or
> `--depth=N`) step to session preflight before `docs_verify` runs, or
> (b) rewrite the checks to tolerate a shallow clone gracefully (skip with
> a clear reason rather than FAIL) if depth cannot be guaranteed.
> Evidence: pasted `docs_verify` output and the diff/shallow-clone proof in
> `experiments/2026-08-09-change-judge-evidence-review/VALIDATION.md`
> ("Map" section).
> End state: `python tools/docs_verify.py` reports 0 failed in a freshly
> cloned container, or the shallow-clone caveat is documented at the
> preflight step CLAUDE.md/`dr-drive-harness` names.
