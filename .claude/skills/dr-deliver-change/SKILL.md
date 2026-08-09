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
   next tranches, never silently promised — each with its
   ready-to-send prompt (the park-with-prompt rule), and the close
   RECOMMENDS one next item from the queue, so the operator answers
   go/no-go rather than authoring the follow-up.
3b. **Report the map delta.** One short section: which `docs/map/`
   documents this tranche changed or created, how many checks it added,
   and any document `--stale` still lists with the reason it was left.
   The operator needs to know whether the next reader of this subsystem
   will be told the truth. "No map change" is a legitimate answer for a
   tranche that changed no behaviour — say it rather than omitting the
   section, so its absence is never ambiguous.
3c. **Errata check — mandatory, before DELIVERY.md is committed.** Did
   this tranche find any committed document's claim (a handover, a map
   document, a RESULTS.md, a spec, CLAUDE.md — anything docs/ERRATA.md
   covers) to be wrong? If yes, the `docs/ERRATA.md` entry lands in the
   SAME commit as DELIVERY.md. If no, state "errata: none" explicitly
   in DELIVERY.md's Errata section — state it, do not omit the section.
   Same state-not-silence pattern as 3b's map delta: an absent section
   is ambiguous, an explicit "none" is not.
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

    ## Map delta
    changed: <files>   created: <files>   new checks: <n>
    left stale: <file: reason, or "none">

    ## Errata
    <docs/ERRATA.md entry id(s) added this tranche, or "errata: none">

    ## Parked (not done, not promised)
    <PARKED.md entries with their ready-to-send prompts, or "none">
    recommended next: <entry id + one-line reason, or "none">

## Exit criteria

- Everything pushed; tree clean; DELIVERY.md committed.
- DELIVERY.md's Errata section states either the added entry id(s) or
  "errata: none" — never omitted, never silent.
- The report (its content, not a pointer to it) is presented to the
  operator as the final message of the tranche.
- Tranche closed. New suggestions start a fresh tranche via
  `dr-change-orchestrator`.
