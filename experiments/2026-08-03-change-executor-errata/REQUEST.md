# Request: "this process needs to go in its own errata... wait for the results and keep monitoring progress"

Captured: 2026-08-03, from the operator's message following delivery of the
modularisation handover.

## Verbatim

> now that you've begun building out the infrastructure for less capable
> model, this process needs to go in its own errata. But wait for the
> results and keep monitoring progress.

## Requirements

R1 (artifact): "this process needs to go in its own errata" — "this
process" = the less-capable-executor infrastructure built this session
(dr-ask-the-right-question, dr-drive-harness + calibration block, the
skills index, the Sonnet-calibrated handover). "its own errata" = a
dedicated ledger, separate from docs/ERRATA.md.

R2 (process): "But wait for the results" — no judgment entries before an
executor session has produced a record. The ledger is created with its
charter; content waits.

R3 (process): "keep monitoring progress" — a standing watch on the
executor's progress from this session, feeding the ledger when results
arrive.

## Standing constraints

C1 (ERRATA.md's own charter): "Entries are appended, never rewritten...
Evidence pointers only; no narrative." The new ledger inherits the house
errata discipline.

C2 (repo law): the record is the only admissible evidence — ledger entries
derive from the executor session's committed artifacts, not from
impressions.

## Open questions (for spec)

Q1: Ledger name/location. Q2: Should the handover tell the EXECUTOR to
feed the ledger itself (cheapest telemetry)? Q3: Monitoring mechanism and
cadence.

## Amendments

(append-only)

R3a (supersedes R3's cadence and reporting rule), operator verbatim
2026-08-03: "Actually can you check in every 10 minutes to see if process
has veered of course. If it does, emit a single warning, then terminate.
I'll handle it after that." — cadence 10 minutes; on off-course detection:
ONE warning to the operator, then ALL monitoring terminates (no further
checks, no intervention); the operator takes over. On-course behavior
(silent when idle, errata-feeding when results arrive) is unchanged.
