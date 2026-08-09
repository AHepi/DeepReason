# Delivered: update the Errata (sweep + automation)
Branch: claude/errata-update-automation-21ftwd @ 3f60ac46c (pushed, tree clean)

## What changed

`docs/ERRATA.md` gained seven new entries (E11-E17) from a from-scratch
sweep of every tranche delivered since its last entry (2026-08-04):
a stale map-document sentence rung 4 shipped and rung 5 quietly fixed
(E11); this ledger's own E5 misidentifying which roots are the
no-manifest three (E12); two CLAUDE.md staleness fixes that already
landed in the tree (the spec-version listing and the turmite/jolt
dating) but were never ledgered (E13, E14); S6's "pre-registered
stochastic miss" characterization of `property_designer` that a same-
tranche correction later showed is actually a structural bootstrap
circularity (E15); S6's PARKED item misattributing a `continue`-crash
mechanism, refuted by L1's diagnosis (E16); and O1's "14 genuine
floating chains" finding, superseded by O2's spec-true re-run showing
zero (E17). One operator-flagged candidate — the S5 budget-headline
episode (R21/R22) — was verified and correctly EXCLUDED: it is the
workflow's own in-tranche amendment mechanism, not an error in a
committed document.

Separately, `.claude/skills/dr-deliver-change/SKILL.md` and
`.claude/skills/dr-verify-outcome/SKILL.md` now each carry a mandatory
"Errata check" checkpoint before their closing artifact (DELIVERY.md /
VERIFY.md) commits — state the entry id(s) added, or state "errata:
none" explicitly. Diagnosis: no delivery-phase skill previously
mandated this check, so the ledger was pure convention and silently
starved; this tranche's own sweep is the evidence (seven genuine
corrections sat unledgered for up to five days across a dozen-plus
tranches). This DELIVERY.md is itself the first artifact produced under
the new checkpoint (see Errata section below).

Environment fixes, required to get an honest full-gate/docs_verify
reading but outside this tranche's own scope: `pytest`/`pytest-xdist`/
`jsonschema` were missing from the system Python used by
`python -m pytest` and were installed; the container's git clone was
shallow, failing 3 unrelated map checks, fixed with
`git fetch --unshallow origin`. Neither changed any tranche file.

## Reconciliation

| R | Operator's words (short) | Disposition | Proof |
|---|---|---|---|
| R1 | "Sweep every tranche delivered since [2026-08-04]... append properly dated, append-only entries" | done | commit dbff393b8; VALIDATION.md S1-S7 |
| R2 | "Every entry: what the document claimed, where, what the record shows, where corrected" | done | E11-E17 text in docs/ERRATA.md; VALIDATION.md S1-S7 |
| R3 | "Do NOT invent errata for in-tranche revision supersessions" | done | VALIDATION.md S8 (S5 budget-headline candidate correctly excluded) |
| R4 | "verify each against the record — do not copy my list blind" | done | VALIDATION.md S1, S2, S7, S8 — every candidate independently re-verified against primary source (git show, direct file reads) before adoption or exclusion |
| R5 | "Diagnose in one paragraph from the skills themselves [why the ledger isn't automatic]" | done | SPEC.md "Diagnosis (R5)"; restated in DELIVERY.md above |
| R6 | "amend dr-deliver-change/SKILL.md and dr-verify-outcome/SKILL.md... mandatory closing checkpoint" | done | commit 2416c6f32; VALIDATION.md S10, S11 |
| R7 | "State-not-silence, the same pattern every other checkpoint in those skills uses" | done | VALIDATION.md S10/S11 (checkpoint text cites each skill's own existing state-not-silence line as its model) |
| R8 | "Full gate at the boundary; docs_verify full" | done | VALIDATION.md "Full gate" and "Map" sections — docs_verify full/audit/links/coverage all clean; gate 3434 passed, 1 pre-existing unrelated failure (see Errata/Parked below) |
| R9 | "Deliver through validate/deliver; push each boundary; stop when delivered" | done | every CHECKLIST.md [COMMIT] step pushed; VALIDATION.md verdict PASS; this DELIVERY.md |
| R10 | "route through dr-change-orchestrator... ledger [the operator's words] in REQUEST.md" | done | REQUEST.md Verbatim section; full phase sequence followed |

## Assumptions the operator may override

A1: `docs/ERRATA_EXECUTOR.md` (the separate, single-writer ledger for
the less-capable-executor infrastructure) is out of this tranche's
scope — every confirmed finding is an ordinary-committed-document
correction, so this had no material effect on what was delivered.
A2: the R6 checkpoint's wording is reused near-verbatim in both skills,
naming each skill's own closing artifact (DELIVERY.md / VERIFY.md)
rather than a single generic phrase.

## Map delta

changed: none   created: none   new checks: 0
left stale: none — this tranche touched no `docs/map/` document.
`docs_verify --stale` lists 33 documents worth re-reading, but all 33
predate this tranche and belong to whichever future tranche next
touches that subsystem (VALIDATION.md's Map section has the full
disposition).

## Errata

**E11-E17 added** (`docs/ERRATA.md`, commit `dbff393b8`) — this
tranche's entire purpose. Summary: E11 (stale map-doc fingerprint-
timing sentence), E12 (this ledger's own E5 misidentifying no-manifest
roots), E13/E14 (two already-fixed CLAUDE.md staleness commits never
ledgered), E15 (S6's stochastic-miss mischaracterization), E16 (S6's
PARKED item's crash-mechanism misattribution), E17 (O1's floating-
chains count superseded by O2). Full text and evidence: `docs/
ERRATA.md`'s "## 2026-08-09 (sweep of tranches since 2026-08-04)"
section.

## Parked (not done, not promised)

P1: `test_bronze_report.py::test_census_totals_internally_consistent`
fails on `origin/main` itself (`159 == 165`), confirmed pre-existing
and identical to D2's own PARKED P-D2-3 (2026-08-08) — not this
tranche's to fix (a `src/`/`tests/` code defect, not a document claim).
Full ready-to-send prompt in `PARKED.md`.

recommended next: P1 — it is a five-day-old, twice-independently-
confirmed regression in the bronze-report census gate that no tranche
since D2 has picked up; routing it through `deepreason-orchestrator`
starting from `dr-set-goal` costs one paste of the prompt already
written.
