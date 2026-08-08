# PARKED: bronze census reconciliation is environment-coupled (a reader of fixed bytes giving different answers in different environments)

Parked 2026-08-08 by the monitor session, found on the merged
consolidated head (`c97f6631`) during the post-merge full gate.

## The symptom

`tests/test_bronze_report.py::test_census_totals_internally_consistent`
fails in SOME environments and passes (or skips) in others, on
IDENTICAL commits:

- Monitor container (py 3.11.15, pydantic 2.13.4): FAILS at both
  `b2a9b625` (a head whose own tranche gate reported "3400 passed,
  0 failed") and the merged `c97f6631` — deterministically, isolated
  and under `-n 4` alike:
  `assert counts["gate_blocked"] == census["streams"][stream]["gate_measures"]`
  → `159 == 165` for stream `deepseek-v4-pro` ONLY (qwen3_5_397b
  183/183 and kimi-k2_6 269/269 reconcile). Six gate Measures in that
  root's committed log do not land on a gate-blocked census row.
- D2 executor: reproduced the same failure in a fresh worktree at
  `f103a03a` (its VALIDATION.md, P-D2-1).
- P1/P3-fix executor: full gate at `b2a9b625` reported 0 failed —
  in that environment this test either passed or was skipped
  (skip-count differences across environments are consistent with
  the latter; unresolved which).

## Why this is a real defect and not test noise

`scripts/bronze_census.py` is a READER over committed, immutable
bytes (`experiments/bronze_flat_2026-07-13/`, 2205 tracked files,
present in every clone — the module-level skipif on the root's
absence is NOT the explanation here). A forensic census over frozen
records must be a pure function of those records; an answer that
varies with the installed dependency set means the reader's parsing
or validation behavior (candidate extraction / lenient JSON /
schema_valid classification — the plausible dependency-version
couplings) silently moves. Same class as the repo's recorded
editable-install/import-origin traps: the instrument, not the
record, is unstable.

Not caused by the D2 or O1/O2 tranches: reproduced at commits that
predate both.

## Known facts for the diagnosis

- Failing stream: `deepseek-v4-pro` only; delta exactly 6.
- Monitor env: python 3.11.15, pydantic 2.13.4 (fresh
  `pip install -e . --break-system-packages` today).
- Related parked item, same family: `jsonschema` is an undeclared
  test dependency (original P1 from the S1 census tranche) — the
  same merged-head gate run also failed
  `test_schema_carries_every_prose_rule.py` with
  `ModuleNotFoundError` until `jsonschema` was installed by hand.
  Two instruments, one lesson: the test environment is not pinned.

## Ready-to-send prompt

"`tests/test_bronze_report.py::test_census_totals_internally_consistent`
reconciles in some environments and not others on identical commits
(see experiments/2026-08-08-parked-bronze-census-env/PARKED.md for
the measured facts: stream deepseek-v4-pro, gate_blocked=159 vs
gate_measures=165, delta 6, py 3.11.15 / pydantic 2.13.4). Route
through deepreason-orchestrator from dr-set-goal: identify the six
unmatched gate Measures, bisect which dependency's version changes
the census's row classification (candidate extraction and
schema-validity parsing in scripts/bronze_census.py are the
suspects), and fix the READER to be dependency-version-invariant —
never the committed record, never the test's reconciliation
assertion. Fold in the sibling environment defect: declare
`jsonschema` (undeclared test dependency, S1 census P1) and any
other test-only imports properly, so the gate's result stops
depending on which container ran it."
