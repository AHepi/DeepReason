# Parked — found while specifying Items 4+5, not built this tranche

## Residue 1 — ~528 of 572 typed error codes remain uncataloged

SPEC.md's S2 budgets only the registry MECHANISM plus 44 hand-written
entries (QUALIFICATION_*, DOCTOR_* — R1's own immediate complaint
area). The census (ERROR_CENSUS.md) found 572 real codes across ~40
prefix families (BRIDGE_* 121, TERMINAL_* 59, SCRATCH_* 54, JOLT_* 43,
V3-V6_* 46, RUN_* 25, CONTINUE_* 19, ADMISSION_* 17, PREPARATION_* 15,
AMEND(MENT)_* 15, SCHOOL_* 11, WORKFLOW_* 8, ROUTE_* 8, and ~40 smaller
families). Once S2's mechanism is approved and built, each remaining
family is its own bounded follow-on tranche (one family or a small
cluster per tranche, each with its own before/after coverage count),
never one giant "catalog everything" tranche — 572 entries of prose
quality worth writing is not a single-sitting task, and CLAUDE.md's own
"no half-finished implementations" rule argues for finishing families
completely rather than a thin pass over all 572.

**Ready-to-run entry point:** once S2 delivers, `dr-change-orchestrator`
per family, starting from `dr-capture-request` with "extend the error
catalog to the BRIDGE_* family" (or whichever is next), citing this
PARKED.md entry and ERROR_CENSUS.md's family counts.

## Residue 2 — S4b Option 1 (per-role provenance qualification)

SPEC.md's Q1 asks the operator to choose between (a) message-only
(this tranche's recommendation) and (b) S4b's parked Option 1
(per-role provenance qualification, real frozen-surface-5 contact).
If the operator chooses (b), it is NOT folded into this tranche even
on approval — it needs its own `dr-spec-change` cycle against
`qualification_subject_payload`'s digest-equality check, exactly as
`experiments/2026-08-06-change-qualification-per-seat-s4/PARKED.md`
already anticipated.

**Ready-to-run entry point:** `dr-change-orchestrator`, starting from
`dr-capture-request` with the operator's Q1(b) answer plus
`experiments/2026-08-06-change-qualification-per-seat-s4/PARKED.md`'s
S4b entry and its SPEC.md revision-1 "Option 1" sketch. Map ids:
`DR-CON-seats`, `DR-SUB-manifest`, `INV-frozen-surfaces.md` surface 5.

## Residue 3 — the two adjudication-branch-only intake fields

FORM_DR1_RUN_APPLICATION.md's Parts E2/E3/F1/F3/G1 (marked `†`) exist
only on the unmerged `claude/adjudication-judge-seats-optins-4nb7ov`
branch. `IntakeFormV1` (S3) should model these as OPTIONAL fields whose
Pydantic validators can be written against that branch's actual schema
once merged — this tranche cannot validate a schema for a surface that
doesn't exist on main yet. Not a blocker for S3's approval (the
mandatory Parts A-D fully exist on main today), but S3's implementation
should leave these fields last, gated on the adjudication branch's
merge status at execution time.

## No other defects surfaced

Reading `qualification.py`, `readiness.py`, `run_manifest.py`'s JSON
Schema export, and the census's raise-site sample surfaced no new code
defects — every finding above is scope residue, not a bug.
