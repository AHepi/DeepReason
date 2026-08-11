# Checklist for: docs/ reorganization steps 3-4

Each step: one done-criterion, pasted output required before checking.

- [x] **CS1** (S1, S2, S3 — one commit, per R2's "same commit as each
  move"): `git mv docs/PATROL_DETERMINISM_REPORT.md
  experiments/2026-08-08-corpus-enrichment-patrol-pilot/PATROL_DETERMINISM_REPORT.md`;
  fix the stranded reference in
  `docs/HANDOVER_MONITOR_2026-08-10.md:101`; update `docs/INDEX.md`'s
  Explanation section (new path for the moved report; explicit
  "stayed because ..." line for each of BASIN_REPORT.md,
  CAN_LLMS_EXPLORE.md, MINI_STRESS_REPORT.md, AUTONOMICS_REPORT.md).

  Done-criterion evidence:
  ```
  $ git status --porcelain (before commit f9697675c)
  M docs/HANDOVER_MONITOR_2026-08-10.md
  M docs/INDEX.md
  A  docs/proposals/README.md
  R  docs/PATROL_DETERMINISM_REPORT.md -> experiments/2026-08-08-corpus-enrichment-patrol-pilot/PATROL_DETERMINISM_REPORT.md

  $ grep -rn "docs/PATROL_DETERMINISM_REPORT" src/ tests/ docs/ experiments/ .claude/ CLAUDE.md README.md
  docs/HANDOVER_MONITOR_2026-08-10.md:102:  (relocated 2026-08-11, was `docs/PATROL_DETERMINISM_REPORT.md`) and
  experiments/2026-08-11-change-docs-reorg-steps-3-4/{SPEC,CHECKLIST}.md  (this tranche's own artifacts, expected)
  # DOCS_REORG_PROPOSAL.md's dated-inventory mention does not match
  # (bare filename, no "docs/" path prefix — confirms it was never a
  # navigational link, per A2)

  $ python tools/docs_verify.py
  docs_verify [full]: 53 documents, 856 checks, 4 workers
    FAIL CON-run-identity.md:195 / :197 / :199  (3 known shallow-clone baseline failures)
  docs_verify: 3 failed   # == baseline, zero NEW failures
  ```
  Committed f9697675c, pushed.

- [x] **CS2** (S4, S5 — one commit, combined with CS1 above for
  atomicity): new file `docs/proposals/README.md` stating the
  new-file-forward `ADR-NNNN-<slug>.md` convention (new proposals
  only, no renames of existing files); `docs/INDEX.md`'s Decisions
  section updated to name the convention and link to the new README.

  Done-criterion evidence:
  ```
  $ test -f docs/proposals/README.md && echo "README exists"
  README exists

  $ grep -c "ADR-NNNN" docs/proposals/README.md docs/INDEX.md
  docs/proposals/README.md:2
  docs/INDEX.md:1

  $ git status --porcelain docs/proposals/  (before commit f9697675c)
  ?? docs/proposals/README.md
  ```
  Committed f9697675c (same commit as CS1), pushed.

- [x] **CS3** (C2 boundary gate): run `python -m pytest tests/ -q -n
  4` (full gate — note: the bare `pytest` binary on PATH resolves to
  an isolated `uv`-tool interpreter without the editable install;
  `python -m pytest` is the correct invocation in this container) and
  confirm the only failure is the known pre-existing
  `test_bronze_report` baseline.

  Done-criterion evidence:
  ```
  $ python -m pytest tests/ -q -n 4
  FAILED tests/test_bronze_report.py::test_census_totals_internally_consistent
  1 failed, 3474 passed, 7 skipped in 731.18s (0:12:11)
  ```
  Matches the known baseline exactly (`test_bronze_report`, 1 failed).
  Zero new failures.

- [x] **CS4** (C3 errata checkpoint): review whether CS1-CS2's moves
  and edits surfaced any document claim already known to be wrong
  (candidate for `docs/ERRATA.md`) versus a plain path-currency fix
  (not an errata-worthy factual correction).

  Done-criterion: recorded in DELIVERY.md — "errata: none". This
  tranche only relocated a file and corrected its own resulting path
  citations; it made no factual claim in any committed document that
  the record later showed to be wrong (the ERRATA genre, per
  `docs/INDEX.md`'s own "Corrections" section, is for claims proven
  wrong by evidence — not for a self-consistent path update following
  a deliberate, announced move).
