# REQUEST — P4, three-layer citable evidence

Tranche of the v2 calculus program
(`experiments/2026-08-14-change-calculus-reconciliation-v2/`). Authority is
that program's REQUEST.md **R62** (Amendment 8, RIDER 5) plus the operator's
board sentence of 2026-08-15. Nothing here is a new operator instruction; this
file re-states the authority verbatim so the tranche can be run from one page.

## The authority, verbatim

Operator, RIDER 5 (2026-08-15), the clause this tranche discharges:

> (5) P4 gains the advice's three-layer acceptance and NO live pilot judges
> premise extraction, localization, or succession before P4 lands

Operator, board sentence (2026-08-15), verbatim:

> "So the board now reads: Rung 3 next, alone — delete the successor loop,
> prove the frontier can't grow by refutation, mutation-proof the proof; then
> problem subjects; P4 before any live judgment; A19 queued behind it"

The advisory source R62 adopts — `docs/proposals/CALCULUS_IMPLEMENTATION_
ADVICE.md`, "P4 must precede any meaningful live evaluation", verbatim:

> The branch's measured evidence defect is structural. On the examined run,
> subproblems accounted for 36 of 49 conjecturer calls, but subproblem prompts
> received aliases rather than citable block IDs. Quotes were optional,
> producing 101 verified block references but zero byte-checked quotations. The
> current `EvidenceRefClaimV1` likewise makes `quote` optional.
>
> A stronger prompt is not enough.
>
> The context packer must put full citable block IDs and the relevant bytes
> into every subproblem context. For the new calculus contracts, use a
> quoted-evidence subtype or semantic rule requiring `quote` to be non-null. Do
> not mutate the old V1 contract globally merely to serve the new claim types.
>
> The acceptance condition should bind all three layers:
>
> ```text
> block bytes appear in the recorded context-exposure receipt
> model returns block ID plus exact quote
> semantic admission byte-checks quote against those same recorded bytes
> claim interface depends on the admitted evidence record
> ```
>
> Schema and offline view work can proceed before P4, but premise extraction,
> localization, and succession should not be judged by a live pilot until this
> channel is fixed.

## Requirements

| # | Requirement | Source |
|---|---|---|
| M1 | The context packer puts full citable block ids AND the relevant bytes into **every** problem's conjecturer context, not only the seed/epoch problems. | advice ¶3; R62 |
| M2 | Those block bytes appear in the **recorded context-exposure receipt** for the call — the run's own typed receipt, not a prose claim. | acceptance line 1 |
| M3 | A **quoted-evidence subtype** exists whose `quote` cannot be null, and the new calculus claim channel uses it. `EvidenceRefClaimV1` is **not** mutated. | acceptance line 2; R62's "old V1 unmutated" |
| M4 | Admission **byte-checks the quote against those same recorded bytes** — a citation to a block that was not exposed to that call is a typed outcome, not a pass. | acceptance line 3 |
| M5 | The claim **interface DEPENDS on the admitted evidence record** when the claim carries evidence. | acceptance line 4 |
| M6 | The critic channel that authors calculus claims (the premise filing) can see the citable universe, so M3–M5 are reachable rather than decorative. | R62 read against Rung 2's delivered channel |
| M7 | No live pilot judges premise extraction, localization or succession before this lands; A19 unblocks on delivery of M1–M6 **and** a credential, not on M1–M6 alone. | R62 |

## Standing constraints inherited (not re-derived here)

- No new LLM role (qualification subject digests — `LADDER.md` §2 row 5).
- All configurations compile; a topology that cannot produce evidence gets a
  typed disclosure, never a stop (all-configs law).
- Solo runs reach every capability (L-3).
- Nothing ranks, admits or accepts a conjecture differently for carrying or
  lacking a citation (L-4's neighbour: visibility never creates support —
  already the standing rule in `evidence/render.py`).
- No cross-version proof is owed (2026-08-14 law).
- Frozen surfaces untouched: `harness.py` event application, `capabilities/
  state.py` digests, replay-validation formats, manifest schemas, anything
  altering qualification subject digests.
