# Delivered: implement the parked skills-overhaul follow-ups
Branch: claude/skills-overhaul-vk2n8d @ 8cd61452d (pushed, tree clean
pending this commit)

## What changed

Both items parked at the end of the skills-overhaul tranche are
closed. P1 (`dr-drive-harness`'s one rule with no automatic
enforcement) was a genuine fork — build a new checker, or accept the
rule stays a judgment call — priced and put to the operator rather
than guessed; the operator chose judgment-only, which is now recorded
permanently as `docs/ERRATA.md` E24, with a one-clause pointer from
the rule's own text so a future reader finds the acceptance without
re-litigating it. P2 (one leftover explanatory sentence in
`dr-ask-the-right-question`, missed by the prior tranche's own trim
pass) is now trimmed to match the other 8. `docs/ERRATA.md`'s full
documentation-consistency check re-ran clean against its known
baseline; `src/` and `tests/` were never touched.

## Reconciliation

| R | Operator's words (short) | Disposition | Proof |
|---|---|---|---|
| R1 | "Can you implement changes please" (read as PARKED.md P1) | done | Q1 answered by the operator ("judgement only and approved to continue"); recorded as `docs/ERRATA.md` E24 plus a pointer in `dr-drive-harness/SKILL.md`, commit `8cd61452d`. |
| R2 | Same message (read as PARKED.md P2) | done | `dr-ask-the-right-question/SKILL.md` trimmed (5 insertions, 6 deletions, confined to one sentence), same commit `8cd61452d`. |

## Assumptions the operator may override

A1: "Implement changes" (plural) was read as covering BOTH parked
items rather than just the one DELIVERY.md's own "recommended next"
line named (P1). Stated in REQUEST.md at capture time; the operator's
"approved to continue" (received alongside the Q1 answer) confirmed
both proceeding together.

## Map delta

No `docs/map/` document changed or created. `docs/ERRATA.md` gained
one entry (E24); 6 existing map documents cite other, unrelated
`docs/ERRATA.md` entries (E5, E7, E8, E18) in prose, none of which
`check:` commands depend on — confirmed unaffected before committing
(`tools/blast_radius.py`, `frozen_surface_verdict: CLEAR`).

## Errata

`docs/ERRATA.md` E24 — the one entry this tranche added, documenting
the operator-accepted exception (not a correction to a wrong claim,
but the honest closure of a design gap this session's own prior
tranche had already surfaced and parked).

## Parked (not done, not promised)

None. Both prior parked items (P1, P2) are closed by this tranche;
`experiments/2026-08-12-change-skills-overhaul/PARKED.md` stands as
the historical record of what was parked and is not edited
retroactively (a closed tranche's artifact stays as committed).

recommended next: none — both known follow-ups from the skills-overhaul
work are done.
