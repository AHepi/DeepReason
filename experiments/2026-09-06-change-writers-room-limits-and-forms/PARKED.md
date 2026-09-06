# PARKED — the writer's room tranche

Defects and wishes noticed during this tranche, not done here. Each entry
is a ready-to-send prompt for its own tranche.

## P1 — the room's "everything so far" shows the newest tenth of the pool

**What.** RESULTS.md §6: a three-cycle room pool is ~53 000 characters; the
everything section, capped by its stage share (60 % of the flow's 12 000),
showed the newest entries and withheld 10 → 79 with the count in the brief.
R6 of the predecessor asked for everything. The knobs exist and are data:
`MiniFlowV1.brief_budget_chars` and `MiniStageV1.brief_share`. Whether a
seat should read 53 000 characters of room before writing is the operator's
setting, not this tranche's.

```
EXECUTOR WINDOW — CHANGE (configuration): let the room seats read the whole pool
Read CLAUDE.md. Load dr-change-orchestrator and pinker-write-for-readers.
Register (as a file-declared or Python-declared flow in <DEEPREASON_HOME>/
seat_plugins/, not by editing mini/) `mini.flow.room-whole.v1`: the room
flow with brief_budget_chars 60000 and brief_share 1.0 on the conjecture
and commitment stages. Run the census (tools/census.py) on one live
3-cycle run and report the withheld counts (expected 0) beside the
duplicate count, so the operator can see whether a seat that reads the
whole room repeats itself less. OUT OF SCOPE: any change under mini/ or src/.
```

## P2 — the commitment seat wrote the same three commitments for two near-identical conjectures

**What.** RESULTS.md §4: three byte-identical proposal pairs across cycle
2's `d8dfb83a` and `055185d5`; the sealed census rule fails on them. Habit
of the seat or artefact of two targets that are close relatives? One run
cannot say.

```
EXECUTOR WINDOW — MEASURE: are duplicate proposals the seat's habit or the targets' kinship?
Read CLAUDE.md (tokens are cheap; the agent is not). Pre-register, then
run three room runs on three different standard inputs (freeze each with
deepreason input freeze), census each, and report exact-dup per run
beside the pairwise similarity of the conjectures the duplicated
proposals bind. No code changes. Report inconclusive as inconclusive.
```
