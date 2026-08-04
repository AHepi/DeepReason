# Delivered: spec-phase judgment guardrails (P6 promotion)

One file changed: `.claude/skills/dr-spec-change/SKILL.md`. Procedure
grew from 5 steps to 8; template and exit criteria extended to match.

| R | Disposition | Where |
|---|---|---|
| R1 census | done | step 4 + "## Blast-radius census" template section; names the P6 evidence and that both misses were under the more capable model |
| R2 DESIGN-AND-STOP shape | done | step 5 + "## Measurements"/"## Options" template stubs; cites the rung-4 M1-M5 precedent |
| R3 rubric pass | done | step 8 (six questions, reviewer stance, any "no" routes back) + "Rubric:" template line + exit criterion |
| C1 rung-6 inventory excluded | honoured | Out of scope in SPEC.md; belongs in the operator's rung-6 instruction |
| C2 general-use wording | honoured | no rung/executor references except as named evidence |
| C3 skill files only | honoured | `git diff --stat`: 1 skill file + tranche dir |

Validation (proportionate to a docs-only change): acceptance greps all
present (8 hits across the four required markers); step numbering
continuous 1–8; no src/, map, or test file touched, so no gate or sweep
owed. This tranche's own SPEC.md follows the new template — census
(pasted-empty), contact forecast, rubric line — so the format is proven
writable by construction.

Assumption carried: A1 — census is a grep procedure, no
`tools/spec_census.py` built; possible follow-up if the operator wants
the census as a command output.
