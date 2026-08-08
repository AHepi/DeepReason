# Parked — found during Rung G1 (actual-diff budget gate), not fixed

## P1 — `.claude/skills/README.md` named in task instructions, absent
on this tranche's own branch (not a defect — a branch-timing artifact)

**Where found:** session preflight (Q1, REQUEST.md), before any code
was read. The task instruction said "Read CLAUDE.md in full first,
then .claude/skills/README.md." `.claude/skills/` on this tranche's
base commit (`d4f63007`) contains only skill subdirectories, no
`README.md`.

**Corrected finding (checked again at park time, not the original
guess):** the file is NOT missing from the project — it exists on
`origin/claude/monitor-session-handover-63ajqv`'s current tip
(`2c9a2023`), along with three skills (`dr-ask-the-right-question`,
`dr-drive-harness`, `dr-explain-to-operator`) this tranche's branch
also does not carry. This tranche's branch was deliberately reset to
`d4f63007` — an EARLIER commit on that same monitor branch — per this
tranche's own task instructions, before the monitor session's later
work (including `README.md` and those three skills) landed on top of
it. This is expected branch divergence, not an absent artifact: the
file exists in the project, just not yet on this branch's own history.

**Not this tranche's finding to fix, and no action is actually owed:**
out of scope regardless (C1: "Scope is G1 alone"); satisfied instead
by reading the skill directory listing and `dr-change-orchestrator`'s
own `SKILL.md`, which serves the same orientation purpose. The
discrepancy resolves itself the ordinary way — whenever this branch's
work is next rebased onto or merged with the monitor branch's later
state, `README.md` and the three newer skills arrive with it. No
follow-up prompt is needed; this entry exists so a future reader does
not re-diagnose the same "missing file" surprise from scratch.
