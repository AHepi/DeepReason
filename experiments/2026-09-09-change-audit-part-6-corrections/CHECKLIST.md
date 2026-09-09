# Checklist: Part 6 document corrections

From SPEC.md. One done-criterion per step; each step's output pasted below it
when executed. No instrument is run at any step (C1).

- [ ] S1 (R1, R2, AC1, AC2) — `docs/CAN_LLMS_EXPLORE.md`: dated demotion note
  after the standfirst, and a second beside Result 1. Done when both notes
  exist, name E0.1 / four refuted predictions / contamination 1.0 / E2.3 never
  run / "unverified by this repository's own ruling", and separate the demoted
  figures from the undemoted ones. Criterion: `grep -c` for the phrase returns
  2 in that file, and `git diff --numstat` shows 0 deletions for it.

- [ ] S2 (R1, R2, AC1, AC2) — `docs/BASIN_REPORT.md`: the same two notes, the
  second beside the abstract's soft-basin finding (1). Same criterion.

- [ ] S3 (R4, AC4) — the archive line in all ten citing documents:
  `docs/CAN_LLMS_EXPLORE.md`, `docs/BASIN_REPORT.md`,
  `docs/OPERATOR_DIAGNOSIS.md`, `docs/INDEX.md`, `docs/MINI_STRESS_REPORT.md`,
  `docs/MINI_PLAN.md`, `docs/REPORT.md`, `docs/STRESS_INSIGHTS.md`,
  `docs/CONTROLLER_SPEC.md`, `docs/CACHE_DESIGN.md`. Done when `grep -l
  3d839b3` lists exactly those ten under `docs/`.

- [ ] S4 (R5, AC5) — `experiments/results/INDEX_2026-07-13.md`: a dated
  section carrying the `git cat-file -t 3d839b3` command and its exact output,
  then one line for each of the ten unindexed files. Done when the section
  holds ten file lines and the verbatim output string.

- [ ] S5 (R6, AC6) — `CLAUDE.md` judge law: split "0-2.5%" into its two
  sourced halves in the same sentence. Done when the law names 42 clean items
  with `court_calibration_v1_report.json` and 40 clean items with
  `e02_t2_voting_report.json`, and `git diff` for CLAUDE.md shows one changed
  sentence and no other change.

- [ ] S6 (R8, AC8) — `docs/CAN_LLMS_EXPLORE.md`: the judge-zoo paragraph.
  Done when it names 1,561 judgments, eleven models, P3 refuted with zero
  qualifying seats, `e02_t3_judge_zoo_report.json`, and the single-author
  caveat.

- [ ] S7 (R3, R7, AC3, AC7) — `docs/ERRATA.md`: E81 (the demotion's reach),
  E82 (the judge-law compression), E83 (the citing-document discrepancy Q1
  found). Done when all three appear under a `## 2026-09-09` heading.

- [ ] S8 (R11, AC9, AC10) — VALIDATION.md by reading: every path named in an
  added line either exists in the tree or is stated as retired; no claim
  deleted anywhere.

- [ ] S9 (R11, R12, AC10) — DELIVERY.md with the R-by-R table; commit and
  push with retry.
