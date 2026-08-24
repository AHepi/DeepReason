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

**Nothing was parked, and that is a finding rather than an absence.** Three
problems surfaced and all three were IN SCOPE, so parking them would have
been wrong:

- `DR-SUB-calculus` stated the declared-but-unbuilt schema count as five
  while its own check three paragraphs above asserted four. Found while
  moving the same counts; fixed in the same commit and recorded as
  `docs/ERRATA.md` **E50**.
- `calculus/render.py::declared_departures` overwrote instead of unioning,
  so a candidate departing on two counts silently un-declared one. This
  tranche's own code, found by review; fixed and pinned.
- The `context-withheld` notice sorted to position 0 of every pack carrying
  one, invalidating the cacheable prefix. Also this tranche's own code;
  fixed and pinned.

The cross-routing rule parks a DEFECT FOUND MID-CHANGE — a pre-existing
fault in code this tranche did not write. A fault in code the tranche
itself just wrote is not that; shipping it and filing a prompt to fix it
later would be parking work into the operator's queue that belongs in this
commit.

**Three `docs_verify` failures are environmental, not defects.**
`CON-run-identity.md:200/202/204` name commits a shallow clone does not
contain; they pass on a full clone. Pre-existing at this tranche's base and
unchanged by it — nothing to park.
