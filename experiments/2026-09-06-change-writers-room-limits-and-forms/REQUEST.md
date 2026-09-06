# REQUEST — the writer's room: limits, forms, and a census of what is ejected

Captured 2026-09-06 (`dr-capture-request`). The operator's words are quoted
verbatim; requirement numbers are the ledger every later artifact cites.
Predecessor: `experiments/2026-09-05-change-mini-isolation-programme/`
(delivered; its RESULTS.md 2026-09-06 "later" segment and PARKED P12 are the
evidence this request answers).

## The operator's words, verbatim, in order

**Message 1** (2026-09-06, after the programme's delivery):

> The point is to get it working on the 3 artifact types. Is it working? Is
> the log replay valid on the larger harness? How many cycles did you use?
> Will any other additional artifact types be recognised by minis scheduler?
> Are conjecture and critic artifacts built from the same base generic
> artifact? The point is maximum configurability as easily as possible. Can I
> set authority and what a critic actually sees? This was the point

**Message 2** (same exchange, mid-answer):

> This is a writer's room, not part of the epistemology

**Message 3**:

> oh good. That's fine for now. The next step is the fix you mentioned earlier
> and a measure of the types of contents ejected. I'm particularly interested
> to see if the commitment artifacts actually have anything in them?

**Message 4** (after the record answered message 3 — six of fourteen
proposals are commitments, eight are essays, because the clip cut the
instruction off nine of nineteen briefs):

> Just making sure the commitments are sitting in separate artifacts from
> conjecture artifacts? And yes, the limits need changing. You have my
> permission to change the forms completely to fit the writers room - content
> brainstorming purpose. But only if the commitments exist outside conjecture
> artifacts.

## Requirements

| R | Words | Reading |
|---|---|---|
| R1 | "the limits need changing" | The brief limit under which the D8 run lost its instructions is to change: no mandatory section (problem, target, directive) may ever be cut, and the limit itself is to be configurable and larger than the compact preset that cut them. |
| R2 | "You have my permission to change the forms completely to fit the writers room - content brainstorming purpose." | The three seats' forms may be redesigned for content generation; nothing in them is epistemology (message 2). The stored default form stays stored (the 2026-09-05 ruling "stored but not deleted" still binds). |
| R3 | "a measure of the types of contents ejected. I'm particularly interested to see if the commitment artifacts actually have anything in them?" | After R1/R2, a live room run is read for WHAT each seat produced — by type, on-target or not, commitment-shaped or not, duplicated or not — with the commitment seat first. |
| R4 (condition) | "But only if the commitments exist outside conjecture artifacts." / "Just making sure the commitments are sitting in separate artifacts from conjecture artifacts?" | Precondition on R2 and standing constraint: a commitment proposal is its own object in the record, referencing its conjecture by id; a conjecture artifact never carries one. TRUE TODAY (answered on the record 2026-09-06, below) and to be ENFORCED by a test that goes red if it ever stops being true. |
| R5 (law) | "This is a writer's room, not part of the epistemology" | Nothing in this tranche gives any seat authority: no status changes, no elimination, no warrant; the room generates content and the full harness judges it (Amendment 1 of the predecessor programme stands). |
| R-fix | "The next step is the fix you mentioned earlier" | Read, with the operator's message 4, as the limit fix (R1): the defect that emptied the commitment seat's output. The two other candidates the assistant had mentioned — the reasoning field mini's transport drops (predecessor P10) and the storage grant that would give all kinds one base — stay parked; message 4's "limits" names which fix. |

## R4 answered on the record before any change (2026-09-06)

Root `…/shallow-b4dcb1c81ea7af2e5ecd5faa`: 8 conjecture artifacts, 14
proposal RECORDS. Every proposal names an existing conjecture by id in its
`about:` input; no conjecture artifact carries a warrant (all 0) and the
state registers 0 canonical commitments; a proposal is a Measure event with a
blob, written after the artifact it names, and the artifact's own digest does
not change when a proposal is written about it. Four proposals begin with the
same sentence as a conjecture that is not their target — an uninstructed seat
echoing an opening line it was shown — which is text overlap, not shared
storage. So: separate objects, by construction; R4's condition holds.

## Map preflight

`DR-SUB-minireason` (the forms, the seats' briefs, the flow),
`DR-SEAM-llm-x-minireason` (the clip trap, P8's disposal — the seam this
tranche moves), `DR-INV-seat-section-plugins`, `DR-INV-seat-section-sources`
(no status read), `DR-CON-packs-and-token-economy` (the allocator),
`DR-INV-frozen-surfaces` (read first: forecast CLEAR — the change is under
`mini/` and in `src/deepreason/shallow.py`, which is not a frozen surface).
