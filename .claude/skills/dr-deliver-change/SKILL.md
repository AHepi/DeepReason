---
name: dr-deliver-change
description: Close a validated change tranche — final commit and push, requirement-by-requirement reconciliation against the operator's verbatim words, and the delivery report (DELIVERY.md). Use only after VALIDATION.md says PASS.
---

# Deliver the change

Input: a PASS VALIDATION.md. Output: everything pushed, and
DELIVERY.md — the report the operator actually reads. Delivery is
reconciliation, not celebration: its job is to make any gap between
what was asked and what was done impossible to miss.

## Procedure

1. Final tree check: `git status --porcelain` must be empty after a
   last commit+push of the tranche directory; confirm the branch head
   exists on origin (`git rev-parse HEAD origin/<branch>` — one hash).
2. Build the reconciliation table from REQUEST.md's verbatim
   requirements — walk EVERY R number, including amendments and
   superseded ones (superseded rows say so). Allowed dispositions:
   - `done` — with the commit hash and the acceptance output pointer
   - `done-with-assumption` — cite A<n>; the operator may override
   - `deferred` — ONLY with the operator's quoted words permitting it
   - `not-done` — forbidden here; that is a FAIL, go back
3. Surface the assumptions (from VALIDATION.md) and PARKED.md
   contents as explicit lists. Parked items are offered as candidate
   next tranches, never silently promised.
4. Write DELIVERY.md leading with the outcome in plain sentences a
   reader who saw none of the work can follow: what changed, where,
   how it is proven. No process narration ("first I read the file...").
5. If the request touched experiments/live evidence: append the dated
   segment to the relevant RESULTS.md per that record's honest-ledger
   style ("accepted does not mean true"; never claim more than the
   record shows). Commit and push it.

## DELIVERY.md template

    # Delivered: <request headline>
    Branch: <branch> @ <head hash> (pushed, tree clean)

    ## What changed
    <plain-language summary, files named, 3-8 sentences>

    ## Reconciliation
    | R | Operator's words (short) | Disposition | Proof |
    |---|---|---|---|
    | R1 | "..." | done | commit <hash>, VALIDATION S1 |
    | R2 | "..." | done-with-assumption A1 | ... |

    ## Assumptions the operator may override
    A1: <one line>

    ## Parked (not done, not promised)
    <PARKED.md lines, or "none">

## Exit criteria

- Everything pushed; tree clean; DELIVERY.md committed.
- The report (its content, not a pointer to it) is presented to the
  operator as the final message of the tranche.
- Tranche closed. New suggestions start a fresh tranche via
  `dr-change-orchestrator`.
