# PARKED — Rung 6

Anything noticed but not requested. Nothing here is fixed in this tranche.

## Carried in from the operator, explicitly

**P4b — the "optionally with a quote" prompt wording.** Named in the
ladder's Rung 6 work list and in the operator's brief as STAYING PARKED.
This tranche absorbs P4's RENDER half only (R6). Do not absorb P4b.

Ready-to-send prompt, when the operator wants it:

```
Route: dr-change-orchestrator.
Goal: land P4b — the premise-invitation prompt wording that invites a
citation "optionally with a quote" — as its own tranche. It was parked by
P4 (experiments/2026-08-16-change-p4-citable-evidence/) as a separate
prompt change, and Rung 6 deliberately did not absorb it
(experiments/2026-08-24-change-rung6-frame-render-departures/REQUEST.md
R6). Evidence pointers: llm/packs.py::premise_invitation_note, its
`citable` branch, and llm/contracts.py::QuotedEvidenceRefV1, whose type
already requires the quote the wording only invites. End state: the
invitation's wording and the type agree, with a test that fails if they
diverge again.
```

## Found during this tranche

(none yet)
