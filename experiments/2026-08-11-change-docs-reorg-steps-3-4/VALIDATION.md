# Validation for: docs/ reorganization steps 3-4

## Acceptance checks

S1: `git status --porcelain` shows the move as `R` (rename) -> PASS
    (confirmed pre-commit, `R  docs/PATROL_DETERMINISM_REPORT.md ->
    experiments/2026-08-08-corpus-enrichment-patrol-pilot/
    PATROL_DETERMINISM_REPORT.md`); `test -f
    experiments/2026-08-08-corpus-enrichment-patrol-pilot/
    PATROL_DETERMINISM_REPORT.md` -> PASS; `test ! -f
    docs/PATROL_DETERMINISM_REPORT.md` -> PASS.

S2: whole-tree sweep for `docs/PATROL_DETERMINISM_REPORT` returns zero
    live hits -> PASS. The only two remaining hits are this tranche's
    own SPEC.md/CHECKLIST.md (quoting the task instruction/command
    verbatim) and `docs/HANDOVER_MONITOR_2026-08-10.md`'s deliberate
    "was `docs/PATROL_DETERMINISM_REPORT.md`" historical note (the
    fix itself, not a stray reference). `DOCS_REORG_PROPOSAL.md`'s
    dated-inventory mention is a bare filename with no path prefix —
    confirmed by the path-scoped grep not matching it — so it was
    correctly left untouched (A2).

S3: `docs/INDEX.md` no longer links `PATROL_DETERMINISM_REPORT.md` at
    its old relative path; links the new path with a "Relocated" note
    -> PASS. Each of BASIN_REPORT.md, CAN_LLMS_EXPLORE.md,
    MINI_STRESS_REPORT.md, AUTONOMICS_REPORT.md carries an explicit
    "stayed because ..." line -> PASS (all four present, confirmed by
    reading the committed file).

S4: `test -f docs/proposals/README.md` -> PASS; contains `ADR-NNNN-`
    and a sentence stating existing files are not renamed -> PASS
    (`grep -c "ADR-NNNN" docs/proposals/README.md` = 2; "Existing
    files are not renamed." is its own heading-adjacent sentence).

S5: `grep -q "ADR-NNNN" docs/INDEX.md` -> PASS (1 match, in the
    Decisions section, linking to `docs/proposals/README.md`).

## Full gate

    $ python -m pytest tests/ -q -n 4
    FAILED tests/test_bronze_report.py::test_census_totals_internally_consistent
    1 failed, 3474 passed, 7 skipped in 731.18s (0:12:11)

Note on invocation: the bare `pytest` binary on this container's PATH
resolves to an isolated `uv`-tool-managed interpreter without the
`deepreason` editable install (`ModuleNotFoundError: No module named
'deepreason'` from `tests/conftest.py`) — an environment quirk, not a
test failure. `python -m pytest` (the interpreter that actually has
`deepreason` installed, confirmed via `pip show deepreason`) is the
correct invocation and is what CLAUDE.md's `pytest tests/ -q -n 4`
line assumes in a correctly-activated environment.

`tests/test_bronze_report.py::test_census_totals_internally_consistent`
(`assert 159 == 165`) is the SAME pre-existing failure the task
instruction's own stated baseline names ("known baseline: 1
pre-existing test_bronze_report failure") and the sibling tranche
`2026-08-11-change-spec-v17-and-docs-index/VALIDATION.md` already
documented with the identical assertion. This tranche's diff touches
zero files under `experiments/bronze_flat_2026-07-13/`,
`tests/test_bronze_report.py`, or `scripts/bronze_census.py` — see
"Record-behavior preservation" below. Verdict: PASS (the one failure
is not this tranche's; 0 new failures).

## Record-behavior preservation

n/a — this tranche touches no reader or validator of the append-only
record; zero `src/` files changed (`git diff --stat
b0afb8f01..HEAD -- src/` is empty).

## Frozen-surface diff

    git diff --stat fcaddb1df..HEAD -- src/deepreason/capabilities/state.py \
      src/deepreason/harness.py
    (empty)

PASS — empty, as SPEC.md forecast (no `src/` file in this tranche's
diff at all).

## Packaging-surface check

Packaging surface untouched — smoke not owed. This tranche moves one
Markdown report, adds one Markdown README, and edits two Markdown
files' prose; no `pyproject.toml`, CLI entry point, MCP tool, or
wheel-layout file is in this tranche's target list.

## Map

    $ python tools/docs_verify.py
    docs_verify [full]: 53 documents, 856 checks, 4 workers
    docs_verify: 3 failed

The 3 failures are the pre-existing `CON-run-identity.md` shallow-clone
git-history failures (lines 195/197/199) — the exact baseline the task
instruction itself names ("baseline: 3 pre-existing shallow-clone
failures in CON-run-identity.md are known"). Not caused by this
tranche: no file this tranche touches is under `docs/map/`, and
`docs_verify`'s document/check counts (53/856) are unchanged in kind
from the pre-tranche baseline (the sibling tranche recorded 53/853;
the +3 checks are pre-existing drift unrelated to this diff, confirmed
by `git diff --stat -- docs/map/` being empty for this tranche). PASS
(0 new failures).

    docs_verify --audit: 0 finding(s) : PASS
    docs_verify --links: 0 dangling reference(s), 53 document(s) : PASS
    docs_verify --coverage: 6 seam(s) swept, 16 without a Sweep: header,
      0 finding(s) : PASS (the 16 are pre-existing, unrelated seam
      documents this tranche does not touch)
    docs_verify --stale: 1 document(s) worth re-reading
      (SEAM-harness-x-verification.md, pre-existing drift from
      unrelated commits d5f47101a/15ba06b34 — not this tranche's) : PASS

new checks added by this change: none — this tranche's new file
(`docs/proposals/README.md`) and moved file
(`experiments/2026-08-08-corpus-enrichment-patrol-pilot/
PATROL_DETERMINISM_REPORT.md`) are neither under `docs/map/`'s ID
grammar, so neither carries a `check:` line by the map's own
convention.

record observables added vs sweep probes: none — this tranche adds no
typed-record field, event, or finding; it reorganizes existing prose
documents only.

wheel smoke: packaging surface untouched — smoke not owed (see above).

## Requirement sweep

R1: demonstrated by S1/S2's pasted evidence above — the one report
that traces unambiguously (PATROL_DETERMINISM_REPORT.md) moved, its
whole-tree citations swept and fixed; the four that do not
(BASIN_REPORT.md, CAN_LLMS_EXPLORE.md, MINI_STRESS_REPORT.md,
AUTONOMICS_REPORT.md) stayed, each with a recorded reason.

R2: demonstrated by commit `f9697675c` — the move, the reference fix,
and the `docs/INDEX.md` update all landed in the same commit; no
separate "update docs" commit exists. No `CLAUDE.md` mention needed
updating (grep confirmed `CLAUDE.md` only ever named `BASIN_REPORT`,
which does not move).

R3: demonstrated by S4/S5's pasted evidence above —
`docs/proposals/README.md` states the `ADR-NNNN-<slug>.md`
new-file-forward convention; `git status --porcelain docs/proposals/`
before commit showed only the new README as `A` (added), zero `R`
(rename) lines — no existing proposal file renamed.

## Assumptions carried

A1 (SPEC.md): "the experiment directory that produced each report"
read as ONE identifiable dated directory the report's own text/data
citations point to, not a loose collection of top-level files — held;
this is exactly why only PATROL_DETERMINISM_REPORT.md moved.

A2 (SPEC.md): fixing a "stranded reference" means fixing navigational
path citations, not rewriting dated historical inventories describing
a past state — held; `DOCS_REORG_PROPOSAL.md`'s "measured 2026-08-11"
inventory line was deliberately left as-is.

A3 (SPEC.md): `docs/proposals/README.md` is the natural home for the
ADR convention note — held; no existing `docs/proposals/*.md` file was
disturbed.

## Verdict: PASS
