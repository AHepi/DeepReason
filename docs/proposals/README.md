# docs/proposals/ — pre-acceptance decision queue

This directory holds design proposals awaiting or recording an
operator decision: each carries its own free-text `Status:` header
(accepted / superseded / open) rather than a rigid template — read the
file's own `Status:` line before treating it as current practice.

## Naming convention

**New-file-forward only.** From 2026-08-11, a brand-new proposal in
this directory is named `ADR-NNNN-<slug>.md` — a 4-digit,
zero-padded, monotonically increasing number, then a short
kebab-case slug (e.g. `ADR-0001-docs-reorg.md`). This borrows the
numbered-immutable-decision-record idea from Architecture Decision
Records (Nygard 2011) without requiring the strict one-decision-
per-file discipline; the existing free-text `Status:` header
convention continues inside each file.

**Existing files are not renamed.** The eleven `*_PREPLAN.md`/
`*_PLAN.md` files already in this directory
(`AMENDMENT_EPOCHS.md`, `BEHAVIOR_MODES_PREPLAN.md`,
`CODER_AS_TOOL_PREPLAN.md`, `CRITICISM_SYMMETRY_RESEARCH_PREPLAN.md`,
`DETERMINISTIC_GATES_PREPLAN.md`, `DUAL_MODE_CONJECTURE_PREPLAN.md`,
`GATES_AND_PACKAGES_PREPLAN.md`, `GROUNDED_OVERLAY_PREPLAN.md`,
`HARD_QUESTION_SET_PROMPT.md`, `RECORD_LIFECYCLE_DEFECT_PLAN.md`,
`ROLE_SEAT_SEPARATION_PLAN.md`) keep their current names permanently —
renaming any of them would strand the prose citations to their old
names elsewhere in `docs/`, `src/`, and `tests/` (not machine-checked,
so a missed one silently breaks). The `ADR-NNNN-` scheme applies only
to proposals created from this point forward.
