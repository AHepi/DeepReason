# Delivered: make the wheel smokes visible to the workflow

Five files: CLAUDE.md, dr-drive-harness, dr-execute-step,
dr-validate-change (+ template line), dr-implement-fix.

| R | Disposition | Where |
|---|---|---|
| R1 same-commit pin rule | done | dr-execute-step step 5; dr-implement-fix step 4; dr-drive-harness §4 |
| R2 paste-or-record-not-owed | done | dr-validate-change step 4a3 + template "wheel smoke:" line |
| R3 named at session start | done | CLAUDE.md "Build and test"; dr-drive-harness §4 |
| C1 smoke fix routed, not done here | honoured | scripts/ untouched; defect prompt handed to operator |
| C2 general-use wording | honoured | evidence named as dates/commits only |
| C3 skills + CLAUDE.md only | honoured | git diff --stat: 5 target files + tranche dir |

Acceptance: `grep -c wheel_smoke` = 1 in each of the five files.
Validation proportionate to docs-only change: no src/, tests/, or map
contact, so no gate, sweep, or docs_verify owed (census: the one
existing smoke-asserting test file overlaps none of the target files).

Defect found during capture, ROUTED per C1: `scripts/wheel_smoke.py`
red since `4940b5f7` (2026-07-28) — its entry-point reader lumps the
custom `deepreason.admission.adapters` group in with console scripts.
The packaging is correct; the smoke's reader is wrong. MCP pins
unverified past the failure point; wheel_operational_smoke.py status
unknown. Fix belongs to a deepreason-orchestrator tranche.
