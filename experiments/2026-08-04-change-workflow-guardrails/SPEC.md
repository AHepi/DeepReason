# Spec for: promote the rung-4/5 guardrails into the general workflow
Traces: every item cites R/C numbers.

## Items
S1 (R1, R4): .claude/skills/dr-spec-change/SKILL.md | before: step 3 is
a weak "check and flag" | after: step 3 becomes a mandatory written
frozen-surface contact forecast (stop-before-planning on plausible
contact) plus the reader-before-writer guardrail; SPEC template gains a
"Frozen-surface contact forecast" section.
    accept: grep -q "contact forecast" .claude/skills/dr-spec-change/SKILL.md
S2 (R2): same file | before: step 2 resolves ambiguity generally |
after: step 2 additionally requires reachability verification of any
request-named mechanism, with the silent-adoption/silent-deviation
prohibition.
    accept: grep -q "reaches the code" .claude/skills/dr-spec-change/SKILL.md
S3 (R3): .claude/skills/dr-drive-harness/SKILL.md | before: instruments
paragraph names the full docs_verify only | after: adds the --fast
caveat and the full-mode-before-src-commit rule.
    accept: grep -q '\-\-fast' .claude/skills/dr-drive-harness/SKILL.md

## Assumptions (operator may override)
A1: edits land in the two skills only; the handover already carries the
rung-specific versions and stays as-is (its rungs 4-5 text now agrees
with the general rule rather than being the only place it lives).

## Questions for operator (STOP if non-empty)
(none — the operator approved the four proposals verbatim)

## Out of scope (explicit)
- src/, tests/, docs/map/ — not requested.
- Retro-editing past tranche artifacts — never.

## Budget
~45 lines, 1 commit. Frozen surfaces touched: none

## Frozen-surface contact forecast
none expected — skills files only, checked against INV-frozen-surfaces.md
