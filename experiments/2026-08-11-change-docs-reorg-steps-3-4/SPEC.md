# Spec for: docs/ reorganization steps 3-4 (report relocation + ADR convention)

Traces: every item cites R/C numbers from REQUEST.md.

## Preflight findings (drive S1's per-report disposition)

Whole-tree citation sweep (`grep -rn <name> src/ tests/ docs/
experiments/ .claude/ CLAUDE.md README.md`) and origin-directory search,
run before any move, per report:

- **BASIN_REPORT.md** — cited by `src/deepreason/config.py:289`,
  `src/deepreason/capture/ladder.py:65`,
  `src/deepreason/capture/detection.py:261` (code comments), and
  `tests/test_orbit.py:2` (test comment). C1 hard-blocks any file a
  `src/`/`tests/` comment cites — **stays in place**, no disposition
  choice to make. (Its evidence also spans loose files directly under
  `experiments/` — `basin_study_prereg.yaml`,
  `experiments/results/basin_*.json` — not one experiment directory,
  so it would fail the "traces unambiguously" test even without C1.)
- **CAN_LLMS_EXPLORE.md** — no `src/`/`tests/` citation. Evidence
  (`experiments/basin_study_prereg.yaml`,
  `experiments/results/mini_creativity_report.json`,
  `experiments/results/mini_smoke_report.json`) spans loose top-level
  files, not one dated experiment directory — **stays in place**,
  origin does not trace unambiguously.
- **PATROL_DETERMINISM_REPORT.md** — no `src/`/`tests/` citation. Its
  own opening line names its source directly: "Compiled at the
  operator's request from the consistency-patrol window's committed
  work (`experiments/2026-08-08-corpus-enrichment-patrol-pilot/`)",
  and every data path it cites lives under that one directory —
  **traces unambiguously, MOVES** to
  `experiments/2026-08-08-corpus-enrichment-patrol-pilot/PATROL_DETERMINISM_REPORT.md`
  (no filename collision; verified directory listing).
- **MINI_STRESS_REPORT.md** — no `src/`/`tests/` citation (its two
  hits are prose evidence pointers in `docs/map/SEAM-adjudication-x-
  rules.md:247` and `docs/map/CON-warrants-and-attacks.md:236`, not
  `check:` lines). Evidence (`experiments/results/mini_chaos_report.json`,
  `experiments/results/mini_gauntlet_report.json`) spans loose files,
  not one dated experiment directory, and the report's own text notes
  it "predates MiniReason's shared-kernel consolidation" (no single
  current tranche produced it) — **stays in place**, origin does not
  trace unambiguously.
- **AUTONOMICS_REPORT.md** — no `src/`/`tests/` citation. Evidence
  (`experiments/solo_autonomics_design.md`) is a single loose design
  file, not a dated experiment directory — **stays in place**, origin
  does not trace unambiguously.

Net: exactly one move (PATROL_DETERMINISM_REPORT.md); four stay with a
recorded reason.

## Items

S1 (R1, C1): `git mv docs/PATROL_DETERMINISM_REPORT.md
experiments/2026-08-08-corpus-enrichment-patrol-pilot/PATROL_DETERMINISM_REPORT.md`.
accept: `git log --follow` (or `git status`) shows the path as a
rename, not a delete+add; `test -f
experiments/2026-08-08-corpus-enrichment-patrol-pilot/PATROL_DETERMINISM_REPORT.md`;
`test ! -f docs/PATROL_DETERMINISM_REPORT.md`.

S2 (R1): same commit as S1 — sweep and fix every stranded navigational
reference to the old path found by the preflight sweep:
`docs/HANDOVER_MONITOR_2026-08-10.md:101` (bare relative-path
citation `docs/PATROL_DETERMINISM_REPORT.md` → new relative path).
`experiments/2026-08-11-spec-drift-measurement/DOCS_REORG_PROPOSAL.md:31`
is NOT edited — it is a dated inventory ("measured 2026-08-11") of the
PRE-move state, a bare filename in a list, not a navigational link;
rewriting it with the post-move path would misrepresent what was
actually measured that day (same principle as CLAUDE.md's "Experiment
narrative... dated, honest-ledger segments," never retrofitted).
accept: `grep -rn "docs/PATROL_DETERMINISM_REPORT" src/ tests/ docs/
experiments/ .claude/ CLAUDE.md README.md` returns zero hits except
inside this tranche's own REQUEST.md/SPEC.md (which quote the task
instruction/proposal verbatim, not a live link) and
`DOCS_REORG_PROPOSAL.md`'s dated inventory (excluded above, by design).

S3 (R2, same commit as S1/S2): update `docs/INDEX.md` — move
`PATROL_DETERMINISM_REPORT.md`'s link out of the "Explanation" list
into a note under the moved report's new location (or a short
"Relocated" line), and add one line each for CAN_LLMS_EXPLORE.md,
MINI_STRESS_REPORT.md, AUTONOMICS_REPORT.md (BASIN_REPORT.md already
carries an implicit "why" via its code/test comments, add one
explicit line too for uniformity) recording WHY each stayed
(ambiguous origin, per the preflight findings above). No `CLAUDE.md`
line needs a change (grep confirmed `CLAUDE.md` only ever named
`BASIN_REPORT`, which does not move).
accept: `docs/INDEX.md` no longer links to `PATROL_DETERMINISM_REPORT.md`
at its old relative path; it links to (or names) the new path; each of
BASIN_REPORT.md/CAN_LLMS_EXPLORE.md/MINI_STRESS_REPORT.md/
AUTONOMICS_REPORT.md has an explicit one-line "stayed because ..."
note nearby.

S4 (R3): new file `docs/proposals/README.md` stating the new-file-
forward ADR convention: new proposals from this point forward use
`ADR-NNNN-<slug>.md` (4-digit, zero-padded, monotonically increasing);
existing `*_PREPLAN.md`/`*_PLAN.md` files are NOT renamed and remain
valid; states explicitly this is forward-only.
accept: `test -f docs/proposals/README.md`; contains the string
`ADR-NNNN-` and a sentence stating existing files are not renamed.

S5 (R3, same commit as S4): update `docs/INDEX.md`'s Decisions section
to mention the ADR-NNNN convention for new proposals and link to
`docs/proposals/README.md`.
accept: `grep -q "ADR-NNNN" docs/INDEX.md`.

## Assumptions (operator may override)

A1: "the experiment directory that produced each" report means a
SINGLE identifiable dated experiment directory under `experiments/`
whose contents the report's own text or data-path citations point to
— not a loose collection of top-level `experiments/*.yaml` /
`experiments/results/*.json` files. Under this reading only
PATROL_DETERMINISM_REPORT.md qualifies; smallest-reasonable
interpretation matching R1's own "ONLY where the origin traces
unambiguously" qualifier.

A2: fixing a "stranded reference" (R1) means fixing navigational path
citations (relative-link-style mentions used to find the file), not
retroactively rewriting dated historical inventories/snapshots that
describe a past state — S2 draws this line explicitly for
DOCS_REORG_PROPOSAL.md.

A3: `docs/proposals/README.md` is the natural home for the ADR
convention note (proposal step 4 says "add the convention note to
docs/INDEX.md and docs/proposals/" — `docs/proposals/` has no file
today besides the eleven `*_PREPLAN`/`*_PLAN` documents, so a new
`README.md` is the smallest addition, not a rename of any of them).

## Out of scope (explicit)

- Renaming any existing `docs/proposals/*.md` file (R3 forbids it
  explicitly; C1's spirit reinforces it — a rename strands citations
  the same way a report move would).
- Moving BASIN_REPORT.md, CAN_LLMS_EXPLORE.md, MINI_STRESS_REPORT.md,
  or AUTONOMICS_REPORT.md — preflight findings above show none trace
  unambiguously (BASIN_REPORT.md additionally hard-blocked by C1).
- Any other docs/ reorg step beyond the proposal's steps 3-4 (C4).
- Editing `docs/map/*`, `docs/ERRATA.md`, `docs/ERRATA_EXECUTOR.md`,
  `docs/harness-spec-*.md` (C1) — none of this tranche's items touch
  them; MINI_STRESS_REPORT.md's citations in two `docs/map/*.md` files
  are untouched since that report does not move.

## Frozen-surface contact forecast

None. This tranche touches only `docs/` prose files and one experiment
directory's contents (adding a moved file). No `src/deepreason/` code,
no replay/record format, no qualification-subject digest. `INV-frozen-
surfaces.md`'s five items are all `src/`-side; irrelevant here.

## Verification plan (C2)

After the S1-S3 move batch: `python tools/docs_verify.py` full
(baseline: 3 pre-existing shallow-clone failures in
`CON-run-identity.md`; anything beyond that is this tranche's). No
`tests/` files reference `PATROL_DETERMINISM_REPORT.md`, so the
"affected-tests ring" for this tranche is empty by inspection — full
gate still runs once at the boundary (baseline: 1 pre-existing
`test_bronze_report` failure) per C2's own instruction.
