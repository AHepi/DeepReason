# Delivery: Part 6 document corrections

Delivered 2026-09-09 on branch `claude/audit-part-6-corrections-9c9gsj`.
Authority: the operator's "do it", answering the monitor's recommendation to
make the documents honest on the 2026-09-08 capability audit's §6.1-§6.4.

Documents only. **No instrument was run in this window** — no gate, no
`docs_verify`, no smoke, no soak, no live call (CLAUDE.md's MANDATORY block,
and the brief's own rule). Validation was reading.

## Requirement by requirement

| R | operator's words (abridged) | delivered | where |
|---|---|---|---|
| R1 | demotion note at the top and beside Result 1 / the soft-basin claim, in both documents | **YES** | `docs/CAN_LLMS_EXPLORE.md` (notice above "The question"; reach note under Result 1), `docs/BASIN_REPORT.md` (notice above the abstract; marker under P1). Each names E0.1, all four predictions refuted, contamination 1.0 on both roots, E2.3 appointed and never run, and states the finding as "unverified by this repository's own ruling" |
| R2 | state which numbers the demotion reaches and which it does not | **YES** | Demoted: 0.846, 0.888, 0.973, 0.865, 1.037, 1.12, the offline 0.85-0.94 band, and every echo-vs-chance figure. Not demoted: gate-block counts (0 healthy, 54 and 36 orbiting) and the 4.3× cost figure, with the audit's reason — the gate's embedding path ships disarmed (`config.py:350`), so that era's gate was hash-and-verdict-only |
| R3 | one-line errata entry recording the demotion's reach | **YES** | `docs/ERRATA.md` E82 |
| R4 | archive line in each citing document | **YES, and the set is corrected** | Ten documents: `CAN_LLMS_EXPLORE`, `BASIN_REPORT`, `OPERATOR_DIAGNOSIS`, `INDEX`, `MINI_STRESS_REPORT`, `MINI_PLAN`, `REPORT`, `STRESS_INSIGHTS`, `CONTROLLER_SPEC`, `CACHE_DESIGN`. See the deviation note below |
| R5 | index line per unindexed file, saying whether it is recoverable | **YES, with recoverability recorded as unverified** | `experiments/results/INDEX_2026-07-13.md`, appended section. `git cat-file -t 3d839b3` returns **`fatal: Not a valid object name 3d839b3`** here (shallow clone), so recoverability could not be established for any file and is recorded as UNVERIFIED rather than asserted |
| R6 | split "0-2.5%" into its two sources with units, same sentence, meaning unchanged | **YES** | `CLAUDE.md` judge law: 0.0 = the defended court's SUSTAIN rate on 42 clean items (`court_calibration_v1_report.json`); 2.5% = an unanimous judge PAIR's FLAG rate on 40 clean items with no defender (`e02_t2_voting_report.json`). One sentence changed; every other number and clause byte-identical |
| R7 | errata entry for R6 | **YES** | `docs/ERRATA.md` E83 |
| R8 | judge-zoo paragraph in the right capability-facing document | **YES — `docs/CAN_LLMS_EXPLORE.md`** | New section before "What this shows, and what it doesn't": eleven models, six families, 1,561 judgments, temperature 0, P3 REFUTED with zero qualifying seats, and the caveat that the unlabelled and clean items had one author. Chosen because §6.2 names that document as the one written for outside readers and the one the zoo is contrasted against |
| R9 | leave the original text in place; never delete a claim, mark it | **YES** | Twelve of thirteen files show 0 deletions. The one deletion is the CLAUDE.md sentence R6 asks to have split in place |
| R10 | each edit cites the audit section and the primary artifact | **YES** | Every added block names its §6.x and its primary artifact |
| R11 | deliver through validation (reading) and delivery with the R-by-R table | **YES** | `VALIDATION.md` (PASS), this file |
| R12 | commit and push with retry | **YES** | Five commits on the branch; push below |

## One deviation from the brief's wording, and its reason

The brief says "each of the nine citing documents the audit names". The
audit's nine came from `INDEX_2026-07-13.md`'s own "Citations elsewhere"
paragraph, and the record does not match it: `docs/STATE_OF_THE_THEORY.md` is
in that list but carries no citation to any of the thirteen retired files and
no `experiments/results/` path at all, while `docs/OPERATOR_DIAGNOSIS.md` and
`docs/INDEX.md` both cite and appear in neither list.

The note therefore went to the **ten documents that actually cite a retired
file**. `docs/STATE_OF_THE_THEORY.md` was left untouched, because a note there
would assert a citation the document does not make — the same error the audit
records against itself in §6.1. The discrepancy is itself ledgered as
`docs/ERRATA.md` E84, and the 2026-07-13 entry's own wording was NOT edited:
it is a record of an act on the day it happened, and "and others" was never a
closed list.

## One error found and corrected inside the tranche

The first draft of both demotion notes called
`e01_embedder_recalibration_report.json` "retired from the working tree". It
is present; the retirement did not reach it. Caught at validation by testing
the path instead of trusting the sentence, corrected in both documents before
delivery, and recorded rather than silently fixed.

## What is now true of the record

- A reader arriving at `docs/CAN_LLMS_EXPLORE.md` or `docs/BASIN_REPORT.md`
  meets the demotion before the claim it qualifies, and is told exactly which
  numbers it reaches.
- A reader who follows a citation to a retired result file is told where the
  data went and that a shallow clone cannot get there.
- The ten result files no index named are now indexed, under the same standing
  rule that made their absence a finding.
- CLAUDE.md's judge law carries its two measurements with their units, so
  "0-2.5%" can no longer be read as one measured interval.
- The repository's widest capability result is cited by a capability-facing
  document, with its own limit attached.

## Residue — what this tranche did NOT do

- **E2.3 still has not run.** The demotion is neither lifted nor made final.
  These edits change what the documents say, not what is known about the
  basin.
- **Recoverability at `3d839b3` is unresolved.** It needs a full clone
  (`git fetch --unshallow`), which was outside this tranche's authority.
- **No instrument confirms this diff.** `docs_verify` was not run and no
  `check:` line was added; no `docs/map` document was touched, so nothing here
  falls in that verifier's scope — an argument, not a measurement.
- **PARKED.md is absent because nothing was parked.** No defect was found
  mid-tranche.
