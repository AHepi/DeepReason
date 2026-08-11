# Request: draft the v1.7 spec amendment and add the docs index (Q1+Q2 approved, Q3+Q4 deferred)

Captured: 2026-08-11 from the operator's reply to
`experiments/2026-08-11-program-closeout/CONSOLIDATED_DECISION_SHEET.md`.

## Verbatim

> "One and two approved. Leave three and four for another window."

Referent (from the immediately preceding message, the consolidated
decision sheet with four numbered questions):

- **Q1**: "Draft a new v1.7 amendment now, covering the six on-`main`
  surfaces, deferring the two branch-only flags to a later amendment
  once that branch merges?" — marked *(Recommended)*.
- **Q2**: "Add one new `docs/INDEX.md` navigation page now (zero
  renames, zero risk), and treat any actual file moves as a separate
  future tranche?" — marked *(Recommended)*.
- Q3 (per-role qualification scope) and Q4 (intake tool default scope)
  — explicitly NOT part of this request: "Leave three and four for
  another window."

## Requirements

R1 (artifact): "One... approved" = Q1 approved at its recommended
option — create `docs/harness-spec-v1.7-amendment.md` covering the six
surfaces `experiments/2026-08-11-spec-drift-measurement/DRIFT_TABLE.md`
found real-on-main-and-undocumented (seats/seat-bindings.v1,
conjecturer.turn.v7, candidate_checker, school-seat routing,
adjudication-blindness/blind-same-model-judge structure, config
referee), deferring `LEGACY_CRITICISM_ENABLED`/`SCHOOL_SEATS_ENABLED`
(adjudication-branch-only) to a later amendment.

R2 (artifact): "...and two approved" = Q2 approved at its recommended
option — create `docs/INDEX.md`, a new top-level navigation page, per
`experiments/2026-08-11-spec-drift-measurement/DOCS_REORG_PROPOSAL.md`'s
step 1 (index-first, move-nothing-load-bearing).

R3 (process): "Leave three and four for another window" — Q3 (per-role
qualification: messages-only vs. S4b Option 1) and Q4 (intake tool
default: small-models-only vs. every-caller) are OUT OF SCOPE for this
tranche. No code or design changes to
`experiments/2026-08-11-change-qualification-messages-s4b/` this
tranche.

## Standing constraints

C1: "The Spec needs updating, but carefully" (original program
handover, still binding) — never edit `docs/harness-spec-v1.3.md`,
`-v1.4-amendment.md`, `-v1.5-amendment.md`, or `-v1.6-amendment.md`'s
existing text; v1.7 is append-only, a new file, "amends... does not
replace or modify" the prior files, matching v1.4-v1.6's own
self-description.

C2 (from `DOCS_REORG_PROPOSAL.md`, still binding): must never move
`docs/map/*.md` (854 automated `check:` commands), `docs/ERRATA.md`,
`docs/ERRATA_EXECUTOR.md`, or `docs/harness-spec-v1.3.md` (cited by
`src/`/`tests/`). R2's index page only ADDS a new file; no existing
file moves this tranche.

## Open questions (for dr-spec-change)

(none — both approved items were already fully designed in the prior
tranches; this request is execution of an already-specified plan, not
a new design.)

## Amendments

(none yet — append-only; future operator words land here)
