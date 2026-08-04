# Spec for: spec-phase judgment guardrails (P6 promotion)
Traces: every item cites R/C numbers.

## Items

S1 (R1): `.claude/skills/dr-spec-change/SKILL.md` | before: the
fixture-drift/contact forecast is written from recall | after: a
mandatory "Blast-radius census" procedure step — grep tests/ and
docs/map/ for every changed symbol and file, paste hits, classify each
EXPECTED TO MOVE or MUST NOT MOVE — plus a census section in the SPEC
template. Names the P6 evidence.
    accept: the skill contains a numbered census step and the template
    contains "## Blast-radius census".

S2 (R2): same file | before: DESIGN-AND-STOP specs have no required
shape beyond the general template | after: a procedure step requiring,
for DESIGN-AND-STOP requests, a Measurements section (every load-bearing
claim = pasted command output) and a priced Options table (files, frozen
contact, ~lines, risk; rejections cite measurements), plus template
stubs. Cites the rung-4 M1-M5 precedent.
    accept: the skill contains a DESIGN-AND-STOP step and the template
    contains "## Measurements" and "## Options" marked DESIGN-AND-STOP.

S3 (R3): same file | before: the spec is committed as written by its
author | after: a final rubric pass in reviewer stance — six questions,
any "no" routes back to the failing step, result recorded as one line in
SPEC.md — and the exit criteria require it.
    accept: the skill contains a rubric step whose questions cover
    census, contact forecast, reachability, accept-checks, and the
    DESIGN-AND-STOP sections; exit criteria mention the rubric.

## Assumptions (operator may override)

A1: The census greps symbols/files by name; no new tool is built. The
offer the operator approved said "as skill changes" — a
`tools/spec_census.py` remains a possible follow-up, not this tranche.

## Out of scope (explicit)

- Rung-6 folklore-promise source inventory (C1 — goes in the operator's
  rung-6 instruction).
- Changes to dr-validate-change or any other skill: not requested.
- Any src/ or map change (C3).

## Frozen-surface contact forecast

none expected — checked against INV-frozen-surfaces.md; skill files
only.

## Blast-radius census

grep -rn "dr-spec-change" tests/ docs/map/ → no hits. Nothing in the
tree asserts on skill-file content; drift risk is zero. (This tranche
eats its own cooking: census run, empty, pasted.)

## Budget

~60 lines across 1 file + tranche artifacts, 1 commit. Frozen surfaces
touched: none.

Rubric: 6/6 yes (census pasted-empty; contact forecast recorded; no
named mechanisms adopted unverified; every R has an accept; S2 sections
specced; nothing untraceable).
