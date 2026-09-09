# Validation: Part 6 document corrections

Verdict: **PASS**.

Method, per SPEC.md AC10 and the brief: **validation here is reading**. No
instrument was run in this window — no gate, no `docs_verify`, no smoke, no
live call (C1, and CLAUDE.md's MANDATORY block). Every check below is a
`grep`, a `git diff`, a path test, or a read of a committed file.

## Scope check (C3)

`git diff --numstat` over the whole tree, at validation:

```
9	1	CLAUDE.md
68	0	docs/BASIN_REPORT.md
13	0	docs/CACHE_DESIGN.md
98	0	docs/CAN_LLMS_EXPLORE.md
12	0	docs/CONTROLLER_SPEC.md
90	0	docs/ERRATA.md
14	0	docs/INDEX.md
13	0	docs/MINI_PLAN.md
13	0	docs/MINI_STRESS_REPORT.md
12	0	docs/OPERATOR_DIAGNOSIS.md
12	0	docs/REPORT.md
12	0	docs/STRESS_INSIGHTS.md
79	0	experiments/results/INDEX_2026-07-13.md
```

Nothing under `src/`, nothing under `tests/`, nothing under `docs/map/`, and
the only file touched under `experiments/` is the index the brief names. The
tranche's own ledger directory is new, not a modification of existing
experiment content.

## AC9 (no claim deleted) — the load-bearing check

Twelve of the thirteen files show **0 deletions**. The single deletion is
`CLAUDE.md`'s one sentence, which R6 explicitly directs to be split in place
("add the sourcing in the same sentence"). Its diff, read in full: the phrase
`0-2.5% false conviction of sound work` becomes the same two numbers with
their instruments, units and corpora named, and every other number and clause
in the law is byte-identical. Nothing else in that entry changed.

## Acceptance checks

| # | check | result |
|---|---|---|
| AC1 | demotion notes at top and beside the claim, in both documents | PASS — `grep -c` on "unverified by this repository's own ruling": 2 in `docs/CAN_LLMS_EXPLORE.md`, 2 in `docs/BASIN_REPORT.md`. Both name E0.1, all four predictions refuted, contamination 1.0 on both roots, E2.3 appointed and never run |
| AC2 | demoted vs undemoted figures stated | PASS — each reach note lists 0.846/0.888/0.973/0.865/1.037/1.12 (and the offline 0.85-0.94 band in `BASIN_REPORT.md`) plus echo-vs-chance as DEMOTED, and gate-block counts 0/54/36 and 4.3× as NOT demoted, with the disarmed embedding path as the reason |
| AC3 | errata entry for the demotion's reach | PASS — E81 |
| AC4 | archive line in every citing document | PASS — `grep -l 3d839b3 docs/*.md` lists the ten citing documents (plus `docs/EXPERIMENT_PROGRAM_2026-07.md`, which already named the commit and was not touched) |
| AC5 | index lines for the unindexed files | PASS — the appended section carries the `git cat-file -t 3d839b3` command with its exact output, ten lines for the unindexed files and three for the indexed ones |
| AC6 | judge law split with sources and units | PASS — 0.0 = defended court SUSTAIN rate, 42 clean items, `court_calibration_v1_report.json`; 2.5% = unanimous judge PAIR flag rate, 40 clean items, no defender, `e02_t2_voting_report.json` |
| AC7 | errata entry for the compression | PASS — E82 |
| AC8 | judge-zoo paragraph | PASS — new section in `docs/CAN_LLMS_EXPLORE.md`: eleven models, six families, 1,561 judgments, temperature 0, P3 REFUTED with zero qualifying seats, plus the single-author caveat |
| AC9 | nothing deleted; every block cites its audit section and artifact | PASS — see above; every added block names its §6.x and its primary artifact |
| AC10 | every added line's paths resolve | PASS — see next section |

## Path resolution (AC10)

Every repository path named in an added line was tested. All resolve, with
exactly one class of exception: the thirteen retired result files, which are
absent by the deliberate 2026-07-13 retirement. Every added line that names
one of the thirteen states that it is absent — that is what those lines are
for. Present and verified: `experiments/results/INDEX_2026-07-13.md`,
`e01_embedder_recalibration_report.json`, `e02_t3_judge_zoo_report.json`,
`court_calibration_v1_report.json`, `e02_t2_voting_report.json`,
`experiments/e02_t3_judge_zoo_prereg.yaml`,
`docs/EXPERIMENT_PROGRAM_2026-07.md`,
`experiments/2026-09-08-audit-llm-capabilities/AUDIT_REPORT.md`,
`experiments/2026-08-09-change-judge-evidence-review/`,
`docs/RESEARCH_JUDGE_BLINDING_2026-08-22.md`, `src/deepreason/config.py`,
and every `docs/*.md` cross-reference.

## Quoted figures checked against their primary source

- `INDEX_2026-07-13.md:75-77` reads, at those exact lines: *"Consequences:
  prior hash-based novelty numbers demoted to unverified; E2.3 now gates any
  repetition of the soft-basin claim."* Quoted correctly.
- `docs/EXPERIMENT_PROGRAM_2026-07.md:135-137` carries P2's 20% prediction
  and its 40% falsifier with the sentence *"E2.3 must run before the basin
  claim is repeated anywhere."* Quoted correctly; line 143 opens the **Why**
  paragraph the notes cite.
- The 0.26 / 0.32 medians in both demotion notes appear verbatim in
  `experiments/results/e01_embedder_recalibration_report.json`
  (`diagnostic_notes`): *"cross-problem median distance (0.26) sits BELOW the
  planted-paraphrase median (0.32)"*.
- `NEAR_DUP_EPS: float | None = None` is at `src/deepreason/config.py:350`,
  with the comment at line 704 confirming none ship armed.
- E2.3: no report under `experiments/results/`, no tranche directory —
  searched both. The "never ran" claim holds on the tree as it stands.

## One error found and corrected inside this tranche

The first draft of both demotion notes described
`e01_embedder_recalibration_report.json` as *"retired from the working tree"*.
It is not — it is present, and the 2026-07-13 retirement did not reach it.
Caught at validation by testing the path rather than trusting the sentence,
and corrected in both documents before delivery. Recorded here rather than
silently fixed, because it is the same failure shape audit §6.1 records
against itself.

## Residue — what this tranche does NOT establish

- **Recoverability at `3d839b3` is unresolved, not resolved.** This window
  could not read the commit (`fatal: Not a valid object name 3d839b3` on a
  shallow clone), so the index entry records UNVERIFIED for all thirteen
  files. A full clone would settle it; that was outside this tranche.
- **The demotion is not lifted and not confirmed final.** E2.3 still has not
  run. These edits make the documents say what the record says; they generate
  no new evidence about the basin.
- **No instrument confirms these documents render or verify.** `docs_verify`
  was not run (C1). No `check:` line was added anywhere, and no `docs/map`
  document was touched, so nothing in this diff falls inside that verifier's
  scope — but that is an argument, not a measurement.
