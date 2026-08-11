# Request: execute docs/ reorganization steps 3-4 (report relocation + ADR numbering convention)

Captured: 2026-08-11, cleanup follow-on to
`experiments/2026-08-11-change-spec-v17-and-docs-index/` (which shipped
step 1, `docs/INDEX.md`, and explicitly left steps 3-4 "for another
window").

## Verbatim

Operator, this window: "So what about the cleanup research? I still
need it." Then, on request for the referent: "The reorganisation."

Referent resolved to
`experiments/2026-08-11-spec-drift-measurement/DOCS_REORG_PROPOSAL.md`,
whose step 1 (docs/INDEX.md) already shipped. The task instruction
bounds this tranche to exactly the proposal's steps 3 and 4, no more:

> (3) Relocate the five standalone top-level reports (BASIN_REPORT.md,
> CAN_LLMS_EXPLORE.md, PATROL_DETERMINISM_REPORT.md,
> MINI_STRESS_REPORT.md, AUTONOMICS_REPORT.md) into the experiment
> directory that produced each — ONLY where the origin traces
> unambiguously; otherwise leave in place and add the INDEX.md pointer
> instead, recording why. Every move: git mv, then a grep sweep of the
> WHOLE tree (src/, tests/, docs/, experiments/, .claude/) for the old
> path — prose citations are not machine-checked, and a missed one
> silently strands a reference. Update docs/INDEX.md and any CLAUDE.md
> mention in the same commit as each move.
> (4) New-file-forward ADR numbering for docs/proposals/
> (ADR-NNNN-<slug>.md for NEW proposals only): add the convention note
> to docs/INDEX.md and docs/proposals/ — do NOT rename any existing
> file.

## Requirements

R1 (artifact, proposal step 3): for each of the five standalone
top-level reports, determine whether its origin experiment directory
can be traced unambiguously. Where yes: `git mv` it into that
directory, then grep the whole tree (`src/`, `tests/`, `docs/`,
`experiments/`, `.claude/`) for the old path and fix every hit. Where
no: leave the file in place at `docs/` top level and record, in
`docs/INDEX.md`, WHY it stayed (ambiguous origin).

R2 (artifact, proposal step 3): update `docs/INDEX.md` and any
`CLAUDE.md` mention in the SAME COMMIT as each move (not batched at
the end).

R3 (artifact, proposal step 4): add a documented convention —
`ADR-NNNN-<slug>.md` — for NEW proposals only in `docs/proposals/`,
noted in both `docs/INDEX.md` and `docs/proposals/` (e.g. a short
README or convention note). Do NOT rename any existing
`docs/proposals/*.md` file.

## Standing constraints (from the proposal and CLAUDE.md, both binding)

C1 (hard, proposal + task instruction): never move `docs/map/*.md`
(854 `check:` commands), `docs/ERRATA.md`, `docs/ERRATA_EXECUTOR.md`,
`docs/harness-spec-*.md`, or anything a `check:` line or `src/`/`tests/`
comment cites.

C2 (process, task instruction): after every move batch, run
`python tools/docs_verify.py` full (baseline: 3 pre-existing
shallow-clone failures in `CON-run-identity.md` are known; anything
else introduced by this tranche must be fixed or is a stop condition).
Then the affected-tests ring. Full gate once at the boundary (known
baseline: 1 pre-existing `test_bronze_report` failure).

C3 (process, task instruction): commit and push at every phase
boundary (retry 2s/4s/8s/16s backoff). Stop after `dr-deliver-change`.
Errata checkpoint at delivery ("errata: none" or an entry).

C4 (scope, task instruction): this tranche is steps 3-4 ONLY, exactly
as the proposal bounds them — no other reorg step, no unrelated
cleanup.

## Map preflight

This tranche touches only `docs/` prose and `docs/proposals/`
convention — no `src/deepreason/` subsystem behavior changes. No
`DR-SUB-`/`DR-CON-`/`DR-SEAM-` id applies (consistent with the sibling
step-1 tranche, `2026-08-11-change-spec-v17-and-docs-index`, which
recorded none for the same reason). `docs/map/INV-frozen-surfaces.md`
reviewed: none of its five frozen surfaces are `docs/`-reorg-related;
C1 above is the tranche's own frozen-surface list, taken directly from
the approved proposal.
