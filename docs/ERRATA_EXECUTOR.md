# Errata — the less-capable-executor infrastructure

Started 2026-08-03 at the operator's request ("this process needs to go in
its own errata. But wait for the results and keep monitoring progress.").

## Scope

This ledger tracks THE PROCESS, not the codebase: the infrastructure built
on 2026-08-03 to let a less capable model operate DeepReason —

- `.claude/skills/dr-ask-the-right-question/` (question discipline),
- `.claude/skills/dr-drive-harness/` (driving manual + the "Calibration
  for less capable executors" block),
- `.claude/skills/README.md` (the workflow index),
- `docs/HANDOVER_2026-08-03.md` (the Sonnet-calibrated modularisation
  program, rungs 1–7).

An entry records an infrastructure claim that an executor session's RECORD
showed to be wrong, misleading, silent where it mattered — or
load-bearing-and-correct (a gate that fired as designed is evidence too,
and belongs here as much as a failure). Corrections to ordinary committed
documents stay in `docs/ERRATA.md`; defects in `src/` go to a
`deepreason-orchestrator` tranche, never here.

## Entry discipline (inherited from docs/ERRATA.md)

Append-only; never rewrite an entry — a correction to a correction is a
new entry. Evidence pointers only: every claim cites the executor
session's committed artifact (tranche ledger, commit hash, pasted output,
run root), never an impression of how the session "went". Entries are
written by whichever session holds the evidence: the executor session
itself (per the feed-instruction in `docs/HANDOVER_2026-08-03.md`) or the
monitoring session reviewing its record.

## Entries

**X1 — the infrastructure's own deployment raced the executor.** The
first executor session branched (`claude/delivery-rungs-handover-m22sdy`,
merge-base `9a319c10`) from the handover-delivery commit — BEFORE this
ledger and the handover's feed-instruction were pushed (`ce3db17e`). The
executor therefore cannot follow an instruction its checkout never
carried; its findings land in `docs/ERRATA.md` instead (its E9). Not an
executor fault and not evidence against the skills — a sequencing gap in
the rollout of the monitoring layer itself. The monitor compensates by
reviewing the executor's artifacts directly.

**X2 — first on-course observation (rung 1, in progress).** Same branch,
head `7d89024c` at first check: rung 1 opened through
`dr-change-orchestrator` with the handover quoted verbatim in REQUEST.md
(`experiments/2026-08-03-change-rung1-sockets-on-paper/`); scope held to
`docs/map/` exactly as the rung specifies (zero `src/`/`tests/` lines
against base); 24 checklist steps completed with a confirmatory full gate
(3290 passed, 0 failed, per commit `88e209fb`). VALIDATION.md and
DELIVERY.md not yet present — tranche mid-flight, consistent with the
workflow's phase order. The per-rung spec format held an executor to
scope without intervention; recorded as load-bearing-and-correct so far,
verdict deferred until the tranche delivers.
