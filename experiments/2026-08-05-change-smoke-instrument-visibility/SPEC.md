# Spec for: make the wheel smokes visible to the workflow
Traces: every item cites R/C numbers.

## Items

S1 (R1, R3): `CLAUDE.md` "Build and test" + `dr-drive-harness` §4 |
before: instruments named are gate, sweep, docs_verify; smokes absent |
after: both name the wheel smokes as the third instrument (no gate runs
them), with the same-commit pin-update rule.
    accept: grep -c "wheel_smoke" CLAUDE.md .claude/skills/dr-drive-harness/SKILL.md → ≥1 each.

S2 (R1): `dr-execute-step` step 5 | before: same-commit obligation
covers the map only | after: also covers smoke pins when the step
changes the packaging surface.
    accept: grep "wheel_smoke" .claude/skills/dr-execute-step/SKILL.md → hit in step 5.

S3 (R1, R2): `dr-validate-change` | before: no smoke check | after:
step 4c — run and paste when the packaging surface moved; explicit
"not owed" line otherwise; template line added.
    accept: grep "4c\|smoke" .claude/skills/dr-validate-change/SKILL.md → step and template hits.

S4 (R1): `dr-implement-fix` step 4 rings | after: conditional smoke
ring when FIX.md's sites touch the packaging surface.
    accept: grep "wheel_smoke" .claude/skills/dr-implement-fix/SKILL.md → hit in step 4.

## Assumptions (operator may override)

A1: "smoke" = `scripts/wheel_smoke.py` + `scripts/wheel_operational_smoke.py`
(the failing instrument found). `mini/scripts/smoke.py` and
`tests/test_live_smoke_regressions.py` are different instruments, not
covered — smallest reading.

## Out of scope (explicit)

- Fixing `scripts/wheel_smoke.py` (C1 — routed as a defect tranche).
- Adding the smokes to the full gate or CI changes — not requested.
- A map document for the packaging surface — worth considering later;
  not requested.

## Frozen-surface contact forecast

none expected — checked against INV-frozen-surfaces.md; skill files +
CLAUDE.md only.

## Blast-radius census

grep -rln "wheel_smoke|wheel_operational_smoke" tests/ docs/map/ →
`tests/test_wheel_operational.py` only, which asserts on the CI workflow
file and the scripts themselves — none of which this tranche touches.
MUST NOT MOVE and cannot: no overlap with target files.

## Budget

~40 lines across 5 files, 1 commit. Frozen surfaces touched: none.

Rubric: 6/6 yes — every R has an item with a greppable accept; census
pasted (one hit, classified, no overlap); contact forecast recorded; no
named mechanism adopted unverified (the smoke failure itself was
re-derived live, not trusted from memory); not a DESIGN-AND-STOP spec so
M/O sections not owed; nothing untraceable.
