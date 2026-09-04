<!-- tranche: 2026-09-04-defect-dead-seat-retirement -->

# Parked — found here, deliberately NOT done here

Each entry: one line of WHAT, then a ready-to-send prompt.

---

## P1 — A transport fault spends the schema-repair budget, so an unreachable provider looks like an incapable model

WHAT: found while diagnosing. `conjecturer#1` in P-A1 recorded 6
`transport_failed` work terminals AND 2 `schema_exhausted` ones on the same
seat, having passed qualification 20/20 first-pass with 0 repairs on both of
its forms. The seat did not lose the ability to fill the form; it lost the
ability to reach the provider — but the contract ladder counts a zero-byte
transport return as a failed attempt like any other, walks down to the
smallest authorized contract, and mints
`RouteSeatInsufficientCapabilityV1`, whose recorded reason is
`smallest_authorized_contract_schema_exhausted`. The record therefore says
"this model cannot satisfy this schema" about a model that was never asked.
This tranche routes AROUND the exhausted seat; it does not change what
exhausts one.

```
DEFECT TRANCHE: a transport fault spends the schema-repair budget, so an
unreachable provider is recorded as an incapable model
(P-A1 run 4565139800f5ca02)

Read CLAUDE.md fully, then load deepreason-orchestrator, dr-drive-harness,
dr-ask-the-right-question and pinker-write-for-readers. Start at dr-set-goal.
Run `deepreason stop-report` on the motivating root before diagnosing.

THE DEFECT, FROM THE RECORD: in run 4565139800f5ca02
(`experiments/2026-09-01-live-all-modules-p-a1/run/`, READ-ONLY) the seat
`conjecturer#1` (ollama-glm-5.3) carries 6 `transport_failed` work terminals
(`provider_transport_failure`) and 2 `schema_exhausted` ones, and its single
`workflow-route-seat-insufficient-capability-v1` record gives the reason
`smallest_authorized_contract_schema_exhausted` after walking
`conjecturer.turn.v6` x5 -> `conjecturer.atomic-candidate.v1` x2. Stop report
section 2 records that same seat at 20/20 first-pass with 0 repairs on BOTH
forms; section 3 records 23 RemoteDisconnected and 6 zero-token returns on its
endpoint. Census: `experiments/2026-09-04-defect-dead-seat-retirement/proof/
terminal_census.txt`.

GOAL (for dr-set-goal to bound): an attempt that never reached the provider
must not spend the seat's schema-repair budget, and must not be recorded as
evidence about the seat's capability. Success criterion, falsifiable: on a stub
whose endpoint returns zero bytes N times and then answers correctly, the seat
completes its work and mints NO insufficient-capability record, where today it
exhausts; and a seat that genuinely emits invalid JSON still exhausts exactly
as it does now. Mutation-proven RED/GREEN, committed.

DESIGN CONSTRAINTS: `workflow/transaction_service.py` and `workflow/replay.py`
carry the ladder and the exhaustion mint; the classification already exists
(`llm/transport_policy.py::classify`, merged 2026-09-03) — do not build a
second one. Read `experiments/2026-09-02-defect-provider-transport-faults/
FIX.md` first. Frozen surfaces untouched; the exhaustion RECORD FORMAT does not
change, only what causes one to be minted.

OUT OF SCOPE: the transport layer and its retry policy; seat retirement
(shipped by experiments/2026-09-04-defect-dead-seat-retirement/); live runs.
```
