# LEDGER — 2026-08-25 post-program close-out audit

Date: 2026-08-25 (UTC)
Model: claude-opus-5
HEAD sha: 853bf705cca96e97c22d193df5b1889511bd92c4
Baselines-file sha: eac1b17b527ec6dfe4992b7a3d9cc81ba03610d8
Comparison copy: `experiments/2026-08-13-audit/`

## Scope

Seven dimensions, not five. PART 1 is the standard audit family
(broken, dead, docs-drift, spec-drift, goal-trace) against
`docs/AUDIT_BASELINES.md` as it stands on main. PART 2 and PART 3 are
guided censuses added by the operator's close-out instruction, whose
purpose is a DELETION DECISION:

> "all experiments and tests need to be audited so I can get rid of
> them."

READ-ONLY everywhere. This audit deletes nothing; it rows verdicts and
writes ready-to-send deletion prompts.

## Activation

Prior `ACTIVATION.md` in this clone is `experiments/2026-08-13-audit/
ACTIVATION.md`, recorded for model `claude-sonnet-5`. This run is
`claude-opus-5` — a model change, so per the router's activation rule
each worker GATE is re-proven red once. See `ACTIVATION.md`.

## Findings

| id | dimension | target | gate | verdict | proof file | disposition |
|---|---|---|---|---|---|---|
