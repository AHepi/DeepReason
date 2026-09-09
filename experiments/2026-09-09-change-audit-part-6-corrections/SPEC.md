# Spec: make the documents honest on the audit's Part 6

From REQUEST.md R1-R12, C1-C5. Documents only. No instrument runs.

## Scope

Twelve files, all documents:

| file | requirement |
|---|---|
| `docs/CAN_LLMS_EXPLORE.md` | R1, R2, R4, R8 |
| `docs/BASIN_REPORT.md` | R1, R2, R4 |
| `docs/ERRATA.md` | R3, R7 |
| `CLAUDE.md` | R6 |
| `experiments/results/INDEX_2026-07-13.md` | R5 |
| `docs/OPERATOR_DIAGNOSIS.md`, `docs/INDEX.md`, `docs/MINI_STRESS_REPORT.md`, `docs/MINI_PLAN.md`, `docs/REPORT.md`, `docs/STRESS_INSIGHTS.md`, `docs/CONTROLLER_SPEC.md`, `docs/CACHE_DESIGN.md` | R4 |

Out of scope by C3: everything under `src/`, `tests/`, and everything under
`experiments/` except `experiments/results/INDEX_2026-07-13.md` and this
tranche's own ledger. Out of scope by C2: `docs/map/` — no check is added,
so no map document is touched.

Reading of C3 recorded: this tranche's own directory
(`experiments/2026-09-09-change-audit-part-6-corrections/`) sits under
`experiments/`, and creating it is required by C4 (route through
`dr-change-orchestrator`, whose artifacts are REQUEST/SPEC/CHECKLIST/
VALIDATION/DELIVERY). C3 forbids changing existing experiment content; the
workflow's own new ledger is not that. No existing file under `experiments/`
is modified except the index R5 names.

## Answers to REQUEST.md's open questions

**Q1 — which documents get the archive line (R4).** The nine the audit names
are not the nine that cite. Derived from the record, not chosen:

- `docs/STATE_OF_THE_THEORY.md` is in the audit's nine (it inherits the name
  from `INDEX_2026-07-13.md`'s own "Citations elsewhere" paragraph) but
  carries no citation to any of the thirteen retired files and no
  `experiments/results/` path at all. There is nothing in it to annotate; a
  note there would assert a citation the document does not make.
- `docs/OPERATOR_DIAGNOSIS.md` (cites `operator_probes.json`) and
  `docs/INDEX.md` (cites `mini_creativity_report`, `mini_smoke_report`,
  `mini_chaos_report`, `mini_gauntlet_report`) are NOT in the audit's nine
  and do cite.

DECISION: the line goes where there is a citation to annotate — the ten
documents that name one of the thirteen. That is the audit's nine, minus
`STATE_OF_THE_THEORY.md` (nothing to annotate), plus `OPERATOR_DIAGNOSIS.md`
and `docs/INDEX.md` (annotations the audit's list would have missed). The
discrepancy is itself recorded as an errata entry, because
`INDEX_2026-07-13.md` names a citing document that no longer cites.

**Q2 — what the index may assert about recoverability (R5).** `git cat-file
-t 3d839b3` in this container returns, verbatim:

    fatal: Not a valid object name 3d839b3

`git rev-parse --is-shallow-repository` returns `true`. So this window cannot
resolve the archive commit and therefore cannot establish, for ANY of the
thirteen files, whether it is present at `3d839b3`. DECISION: the index line
records what is known (the file, the document that cites it, that it is
absent from the working tree, that no index names it) and states
recoverability as UNVERIFIED FROM A SHALLOW CLONE, with the command and its
exact output stated once at the head of the section. Asserting "recoverable"
on a commit that cannot be read would be the same error §6.1 says the audit
made — a check performed on the fields in front of it.

**Q3 — where the judge-zoo paragraph goes (R8).** `docs/CAN_LLMS_EXPLORE.md`.
It is the document §6.2 names as "written for outside readers" and the one
whose Tier-2, n=1 evidence the zoo is contrasted against; putting the zoo
anywhere else leaves the gap §6.2 names exactly where it was.

**Q4 — where "at the top" is (R1).** In both documents, immediately after the
italic standfirst block and before the first section heading, as a dated note
under its own bold lead. In `docs/BASIN_REPORT.md` that is after the `Data:`
lines and before `## Abstract`; in `docs/CAN_LLMS_EXPLORE.md` after the
italic standfirst and before `## The question`.

## Assumptions recorded

A1: "next free number" (R3, R7) means E81 onward — `docs/ERRATA.md`'s highest
existing entry is E80.

A2: R9's precedent ("never delete a claim, mark it") binds every edit: no
existing sentence, table row or number is removed or reworded anywhere in
this tranche. Every edit is an insertion. Verified at validation by
`git diff` showing no deletions outside the tranche ledger — except R6, where
the operator's brief explicitly asks for one sentence to be SPLIT into its two
sources in place ("add the sourcing in the same sentence"), so the law's
numbers and meaning are preserved while the sentence gains its sourcing.

A3: The dated note carries the date 2026-09-09 and names the audit section
and the primary artifact (R10).

## Acceptance checks (reading, per R11 — no instrument is run)

| # | requirement | check |
|---|---|---|
| AC1 | R1 | `docs/CAN_LLMS_EXPLORE.md` and `docs/BASIN_REPORT.md` each carry a dated demotion note at the top AND a second note beside Result 1 / the soft-basin claim; each names E0.1, the four refuted predictions, contamination 1.0 on both roots, E2.3 appointed and never run, and the phrase "unverified by this repository's own ruling" |
| AC2 | R2 | each demotion note lists the demoted figures (0.846, 0.888, 0.973, 0.865, 1.037, 1.12, echo-vs-chance) and the undemoted ones (gate-block counts 0/54/36, the 4.3× cost figure) with the audit's reason |
| AC3 | R3 | `docs/ERRATA.md` gains an entry recording the demotion's reach |
| AC4 | R4 | each of the ten citing documents carries one line naming commit `3d839b3` and that a shallow clone cannot follow it |
| AC5 | R5 | `experiments/results/INDEX_2026-07-13.md` gains a section with one line per unindexed file (ten lines), the `git cat-file` command and its exact output |
| AC6 | R6 | CLAUDE.md line ~581 splits 0-2.5% into 0.0 (42 clean items, `court_calibration_v1_report.json`) and 2.5% (40 clean items, no defender, `e02_t2_voting_report.json`); the law's other numbers and its operational reading are byte-identical |
| AC7 | R7 | `docs/ERRATA.md` gains an entry for the compression |
| AC8 | R8 | `docs/CAN_LLMS_EXPLORE.md` gains a paragraph on the eleven-model zoo with 1,561 judgments, P3 refuted, zero qualifying seats, and the single-author caveat |
| AC9 | R9, R10 | every added block names its audit section and its primary artifact; `git diff` shows no deleted claim |
| AC10 | R11, R12 | VALIDATION.md confirms every file path named in an added line exists in the tree or is explained as retired; DELIVERY.md carries the R-by-R table; branch pushed |

## Files that added lines will point at (existence to be confirmed at validation)

Present in the tree: `experiments/results/INDEX_2026-07-13.md`,
`experiments/results/e01_embedder_recalibration_report.json`,
`experiments/results/e02_t3_judge_zoo_report.json`,
`experiments/results/court_calibration_v1_report.json`,
`experiments/results/e02_t2_voting_report.json`,
`docs/EXPERIMENT_PROGRAM_2026-07.md`, `experiments/basin_study_prereg.yaml`,
`experiments/2026-09-08-audit-llm-capabilities/AUDIT_REPORT.md`.

Absent by the 2026-07-13 retirement, and named as such wherever cited: the
thirteen report files under `experiments/results/`.

## Budget

Twelve files, insertions only, roughly 150 added lines. No file gains a
section longer than the claim it qualifies.
