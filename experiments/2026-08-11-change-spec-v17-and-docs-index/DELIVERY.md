# Delivered: v1.7 spec amendment + docs/INDEX.md

Branch: `claude/operator-program-seven-items-zpur05` @ `ad38df332`
(pushed, tree clean)

## What changed

Two new documentation files, no code, no behavior change.

`docs/harness-spec-v1.7-amendment.md` documents six features that
already ship on `main` and are already exercised by the test suite but
were never named anywhere in the harness spec series (v1.3-v1.6): the
seat-binding record (`seat-bindings.v1`), the opt-in `conjecturer.
turn.v7` wire contract and its `candidate_checker` eval-kind entry,
school-seat route enforcement, the adjudication-blindness epistemic
check, and the config-referee review role. It amends the prior four
files without editing or reinterpreting any of them, in the same style
each of v1.4/v1.5/v1.6 already established. Two related flags
(`LEGACY_CRITICISM_ENABLED`, `SCHOOL_SEATS_ENABLED`) are deliberately
excluded — both exist only on a branch not yet merged into `main`,
re-confirmed still unmerged at delivery time.

`docs/INDEX.md` is a new top-level navigation page for the `docs/`
directory (100 files, several coexisting naming conventions, no prior
single entry point). It groups existing files by kind — reference,
explanation, decisions, corrections, how-to, dated snapshots, design
notes — without moving, renaming, or restating any of them.

`CLAUDE.md`'s own directory-map line was updated in the same commit as
the v1.7 file, to list it — closing the exact gap `docs/ERRATA.md` E13
already found once before (a stale spec listing).

## Reconciliation

| R | Operator's words (short) | Disposition | Proof |
|---|---|---|---|
| R1 | "One... approved" (Q1: draft v1.7) | done | commit `0c1326e51`, VALIDATION.md S1/S2 |
| R2 | "...and two approved" (Q2: docs index) | done | commit `487e79edf`, VALIDATION.md S3 |
| R3 | "Leave three and four for another window" | honored | `git diff --stat` for this tranche touches zero files under `experiments/2026-08-11-change-qualification-messages-s4b/` and zero `src/` files |

## Assumptions the operator may override

A1: v1.7's internal structure follows v1.6's established pattern
("Status and scope" opening, then lettered sections) — a formatting
choice, not a content decision.
A2: `docs/INDEX.md` restates no underlying document's facts, only
points to them — kept the index from becoming a second place anything
could drift out of sync.

## Map delta

changed: `CLAUDE.md` (one line, directory-map listing)
created: `docs/harness-spec-v1.7-amendment.md`, `docs/INDEX.md`
(neither under `docs/map/` — both outside that system's own stated
scope, "describes `src/deepreason/`"; neither carries a `check:` line
by design)
new checks: 0 (see VALIDATION.md — no new record observable, no new
`src/` claim)
left stale: none — `docs_verify --stale` reports 0 documents worth
re-reading

## Errata

errata: none. This tranche found no wrong claim in any committed
document — it only closed a documentation SILENCE (six shipped
surfaces the spec never mentioned), which is not the same as the spec
being wrong about anything it does say.

## Parked (not done, not promised)

none — nothing was parked; everything R1/R2 asked for is delivered,
and R3's deferral (Q3/Q4) was already fully designed and parked in
`experiments/2026-08-11-change-qualification-messages-s4b/PARKED.md`
in the prior tranche, not re-parked here.

recommended next: whenever the operator is ready for "another window,"
Q3 (per-role qualification scope) and Q4 (intake tool default scope)
from `experiments/2026-08-11-program-closeout/
CONSOLIDATED_DECISION_SHEET.md` are the two still-open decisions; both
are fully spec'd and waiting in
`experiments/2026-08-11-change-qualification-messages-s4b/SPEC.md`.
