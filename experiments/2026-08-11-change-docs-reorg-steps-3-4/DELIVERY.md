# Delivery: docs/ reorganization steps 3-4

## Requirement-by-requirement reconciliation

| Req | Operator's words | Delivered |
|---|---|---|
| R1 | "Relocate the five standalone top-level reports ... ONLY where the origin traces unambiguously; otherwise leave in place and add the INDEX.md pointer instead, recording why." | Exactly one report (`PATROL_DETERMINISM_REPORT.md`) traced unambiguously — its own opening line names `experiments/2026-08-08-corpus-enrichment-patrol-pilot/` as its sole data source — and moved there via `git mv`. The other four (`BASIN_REPORT.md`, `CAN_LLMS_EXPLORE.md`, `MINI_STRESS_REPORT.md`, `AUTONOMICS_REPORT.md`) stayed: each cites evidence scattered across loose top-level `experiments/` files rather than one dated directory, and `BASIN_REPORT.md` is additionally hard-blocked (cited by `src/deepreason/config.py`, `capture/ladder.py`, `capture/detection.py`, `tests/test_orbit.py` comments). `docs/INDEX.md` records the reason for each. |
| R1 (sweep) | "Every move: git mv, then a grep sweep of the WHOLE tree ... for the old path" | Whole-tree grep (`src/`, `tests/`, `docs/`, `experiments/`, `.claude/`) run before and after the move; the one live citation found (`docs/HANDOVER_MONITOR_2026-08-10.md:101`) was fixed in the same commit. Confirmed zero remaining hits outside this tranche's own artifacts and the deliberate historical note. |
| R2 | "Update docs/INDEX.md and any CLAUDE.md mention in the same commit as each move." | `docs/INDEX.md` updated in commit `f9697675c`, the same commit as the `git mv`. `CLAUDE.md` needed no change — it only ever names `BASIN_REPORT`, which did not move (confirmed by grep). |
| R3 | "New-file-forward ADR numbering for docs/proposals/ (ADR-NNNN-\<slug\>.md for NEW proposals only): add the convention note to docs/INDEX.md and docs/proposals/ — do NOT rename any existing file." | New `docs/proposals/README.md` states the convention; `docs/INDEX.md`'s Decisions section links to it. `git status` before commit showed zero rename lines under `docs/proposals/` — all eleven existing files untouched. |
| C1 (hard) | Never move `docs/map/*`, `docs/ERRATA.md`, `docs/ERRATA_EXECUTOR.md`, `docs/harness-spec-*.md`, or anything a `check:`/`src/`/`tests/` comment cites. | Held. None of these paths appear in this tranche's diff. `BASIN_REPORT.md` (the one report a code/test comment cites) was correctly identified and left in place. |
| C2 (process) | `docs_verify.py` full after every move batch; affected-tests ring; full gate at the boundary. | `docs_verify.py`: 3 failed = the named baseline (`CON-run-identity.md` shallow-clone), 0 new. Affected-tests ring: empty by inspection (no `tests/` file cites `PATROL_DETERMINISM_REPORT.md`). Full gate: `1 failed, 3474 passed, 7 skipped` — the named baseline (`test_bronze_report`), 0 new. |
| C3 (process) | Commit and push every phase boundary; errata checkpoint at delivery. | Two phase-boundary commits (`b0afb8f01` planning, `f9697675c` execution), both pushed with retry available (first attempt succeeded both times). Errata checkpoint: **none** — see below. |
| C4 (scope) | "This tranche is steps 3-4 ONLY." | Confirmed: `git diff --stat fcaddb1df..HEAD` touches only `docs/` (three files: HANDOVER_MONITOR, INDEX, the new proposals README), one moved report, and this tranche's own `experiments/2026-08-11-change-docs-reorg-steps-3-4/` artifacts. Zero `src/` files. |

## Errata checkpoint

**errata: none.** This tranche relocated one file and corrected its
own resulting path citations — a path-currency fix following a
deliberate, announced move, not a document making a factual claim the
record later showed to be wrong (the genre `docs/ERRATA.md` exists
for). No such claim was found in any document touched or read this
tranche.

## Parked

One item, `PARKED.md` P1: bare `pytest` on this container's PATH
resolves to an isolated interpreter lacking the `deepreason` editable
install (a container/environment quirk discovered while running the
full gate, not a docs-reorg matter — carries its own ready-to-send
prompt for a future tranche).

## Full gate

    1 failed, 3474 passed, 7 skipped in 731.18s (0:12:11)

The one failure (`test_bronze_report.py::test_census_totals_internally_consistent`)
is the task instruction's own named pre-existing baseline. See
VALIDATION.md for the full breakdown.

## Verdict

VALIDATION.md: PASS. All five SPEC.md items (S1-S5) and all seven
REQUEST.md requirements/constraints (R1-R3, C1-C4) satisfied. Steps
3-4 of `DOCS_REORG_PROPOSAL.md` are complete; step 1 (`docs/INDEX.md`)
shipped in the prior tranche; step 2 does not exist in the proposal's
own numbering (the proposal's items are numbered 1, 2, 3, 4 where item
2 is "Do NOT move" — a constraint, not an action — so nothing was
skipped).
