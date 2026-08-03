# Delivered: the executor-infrastructure errata + standing monitor

Branch: `claude/handover-defect-audit-33pv3d` (pushed, tree clean; head is
the commit carrying this file).

## What changed

`docs/ERRATA_EXECUTOR.md` now exists: an append-only, evidence-pointed
ledger dedicated to the less-capable-executor infrastructure built this
session (both cross-cutting skills, the calibration blocks, the skills
index, the handover program). Per your instruction it holds ZERO judgment
entries — it is created in an explicit "Awaiting first results" state, and
its charter says entries derive only from an executor session's committed
record, failures and fired-as-designed confirmations alike. Wiring:
`docs/ERRATA.md`'s scope note routes process-level findings here, and the
handover's calibration section now instructs the executor to feed this
ledger itself whenever the infrastructure misleads it or goes silent — the
executor is the cheapest telemetry, and this session's monitor verifies
and supplements.

Monitoring is armed: Routine `trig_01H2KsMav15TVnhyjJu4uSwn`
("DeepReason executor watch"), cron `47 */2 * * *` UTC (every 2 hours),
firing into THIS session. Each wake: fetch the remote, detect executor
commits/branches, read new tranche artifacts, append evidence-pointed
entries to the ledger, push, and report to you ONLY when something
noteworthy happened — silent otherwise. Cadence is retunable on request.

## Reconciliation

| R | Operator's words (short) | Disposition | Proof |
|---|---|---|---|
| R1 | "this process needs to go in its own errata" | done-with-assumption A1 | docs/ERRATA_EXECUTOR.md (commit ce3db17e); ERRATA.md cross-ref; handover feed-instruction |
| R2 | "But wait for the results" | done | ledger's "Awaiting first results" state; zero E-entries by acceptance check |
| R3 | "keep monitoring progress" | done-with-assumption A3 | trigger trig_01H2KsMav15TVnhyjJu4uSwn, every 2h, self-bind, silent-when-idle |

## Assumptions the operator may override

- A1: ledger named `docs/ERRATA_EXECUTOR.md`, sibling of docs/ERRATA.md.
- A2: the executor feeds its own ledger; the monitor verifies/supplements.
- A3: cadence every 2 hours, silent when nothing changed. Say the word to
  retune or stop (the trigger id above is all that's needed).

## Map delta

None — both files outside the map's charter; zero `src/` changes.
docs_verify --links 0 dangling / --audit 0 findings at commit ce3db17e.

## Parked

Nothing new.

## Amendment R3a (2026-08-03, after delivery)

Cadence revised to every 10 minutes with single-warning-then-terminate
semantics. Mechanics: the platform cron floor is hourly, so the 10-minute
watch runs as a self-re-arming send_later chain (each check re-arms the
next +10min; delivery survives container restarts). The prior 2-hour
Routine trig_01H2KsMav15TVnhyjJu4uSwn is repurposed as an HOURLY
chain-guard: if the chain's state file is stale or missing and monitoring
has not been terminated, it re-arms the chain; if the state says
terminated, it deletes itself. OFF-COURSE means any of: commits touching
frozen surfaces without an operator-approved FIX; implementation (not
SPEC-only) activity on rungs 6-7; one tranche spanning two rungs; work
outside the program and the carried open items without operator words in
a REQUEST.md; history rewrites of committed evidence; committed
credentials; continuing past a red gate. On detection: one warning
message with the evidence pointers, state marked terminated, guard
deleted, chain not re-armed. State file:
<scratchpad>/executor-watch.state (session-local by design; the guard
recreates it after a container recycle).
