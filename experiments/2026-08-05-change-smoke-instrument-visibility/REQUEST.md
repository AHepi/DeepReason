# Request: make the wheel smokes visible to the workflow

Captured 2026-08-05, monitor session.

## Operator's words (verbatim)

> The skills need updating so smoke is updated. It's way behind

## Finding that grounds the request (verified before capture)

`python scripts/wheel_smoke.py` FAILS on the current tree:

    AssertionError: unexpected console entry points: ['deepreason = ...',
    'deepreason-mcp = ...', 'epub = deepreason.admission.adapters_epub:MANIFEST',
    'pdf = deepreason.admission.adapters_pdf:MANIFEST']

The epub/pdf entries are a custom entry-point group
(`[project.entry-points."deepreason.admission.adapters"]`, pyproject.toml:41),
not console scripts — the packaging is correct; the smoke's READER lumps
all entry-point groups together. Red since `4940b5f7` (2026-07-28, EPUB
adapter). Nobody noticed because grep proves the smokes are invisible:
zero mentions in `.claude/skills/`, `CLAUDE.md`, or `docs/map/INDEX.md`.
`EXPECTED_MCP_TOOLS`/schema-sha pins are unverified past the failure
point; `wheel_operational_smoke.py` untested since 2026-07-27.

## Requirements

- R1: The workflow skills must name the wheel smokes as an instrument
  and say WHEN they are owed: any change touching the packaging surface
  (pyproject entry points, CLI commands, MCP tools/schema, wheel
  layout) updates the smoke's pinned expectations and re-runs it in the
  SAME commit.
- R2: Validation must either paste smoke output or explicitly record
  "packaging surface untouched — not owed", so the skip is a decision.
- R3: The instrument is named where sessions start (CLAUDE.md /
  dr-drive-harness), not only in mid-workflow skills.

## Constraints

- C1: Fixing `scripts/wheel_smoke.py` itself is NOT this tranche — a
  defect found while capturing a change is routed, not fixed inline.
  It goes to a defect tranche (prompt handed to the operator).
- C2: General-use wording (operator's standing rule).
- C3: Skill files + CLAUDE.md only; no src/, scripts/, or map change.
