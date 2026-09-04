# GOAL — repair the rotted soak cases, and establish first whether the soak runs everything

## The operator's instruction, verbatim

> "do the repair. But first establish whether the soak runs everything. Not
> just the first two lines. That was a major fault with verify. If you find
> nothing, don't report back, just continue."

## What that resolves to

Two obligations, in order.

**G1 — establish whether `scripts/cycle_soak.py` runs everything it declares.**
The named precedent is the `docs_verify` fault recorded in
`docs/AUDIT_BASELINES.md`: a parser that discarded openers it could not read,
producing a green total over a population it never examined. The question is
whether the soak has the same shape — anything declared but not run, anything
read but silently dropped, anything reported green that was never examined.

**G2 — repair the five committed soak cases that no longer compile**, found by
`experiments/2026-09-04-review-judge-seat-matrix-soak/` and prompted as its
P1: `pr1`, `pc1`, `pc2`, `pc2b`, `split-legs`, all failing
`V6_SIMULATION_TOOLCHAIN_REQUIRED` before any assertion runs.

## Success criterion (falsifiable, decided by typed output)

1. A written census of what the soak declares versus what it evaluates, with
   the command and output for each claim.
2. All nine committed cases compile and run — individually AND enumerated in
   one process.
3. Every defect found under G1 is either fixed in this tranche or parked with
   a reproduction; none is left undescribed.
4. Every new or changed check is mutation-proven in BOTH directions.
5. Full gate 0 failed. `docs_verify` at its recorded baseline (5 or 6 on this
   shallow clone). Both wheel smokes green. `--case epoch3` exits 0, the
   baseline at `docs/AUDIT_BASELINES.md:210`.

## Scope

**In:** `scripts/cycle_soak.py`; the four committed manifest builders behind
the five broken cases; one new gate test file; `docs/AUDIT_BASELINES.md`, so
the case inventory is baselined rather than one case.

**Out, and PARKED rather than fixed if met:** the three colliding
`question.py`/`criteria.py` module names in committed experiment directories
(the loader fix removes their reach); the soak's missing fault-injection,
truncation and continuability mechanisms (P2 of the review tranche's prompts —
a change tranche, not this defect); anything on a frozen surface.

## What this tranche may NOT do

Weaken an assertion to reach green. Configure away a difference between the
soak's shape and the launch's shape. Edit a committed run root. Touch a frozen
surface without an explicit operator grant.
