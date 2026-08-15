# REQUEST — Rung 3c: the claim substrate and companion problem subjects

Route: `dr-change-orchestrator`. **Rung 3c of the v2 calculus program.**
Date: 2026-08-15. Branch: `claude/calculus-rung2-step2-premise-pes36e`.

## 1. Authority

Operator, verbatim, summarising the board:

> So the board now reads: Rung 3 next, alone — delete the successor loop, prove
> the frontier can't grow by refutation, mutation-proof the proof; then problem
> subjects; P4 before any live judgment; A19 queued behind it

and closing:

> just continue autonomously until complete.
> continue

Rung 3a is delivered, so **"then problem subjects"** is this tranche. It
matches the external advice's own recommended order, where the claim substrate
is the tranche after H1.

Substantive authority, ledgered as R59 and R60 (`RECONCILIATION.md` §2P):

- **R59** — problems become criticizable through deterministic COMPANION
  subject artifacts (`poietic.problem-subject.v1`), two-step idempotent
  registration, **no fields added** to `Problem` / `EpistemicState` / `Event`.
- **R60** — claim bodies are a **CLOSED discriminated union**, compiled to
  interfaces **only by the controller**. Models never choose `mention` /
  `dependence` / `evidence`. The generic synthesizer is not retrofitted.

## 2. Requirements

| # | Requirement | Source |
|---|---|---|
| C1 | A closed discriminated union of versioned claim bodies. **No open `RelationClaim(predicate: str)`** — an open predicate lets arbitrary prose become quasi-ontology. | R60 |
| C2 | ONE compiler is the only place a claim body becomes an `Interface`. Models propose bodies and endpoint ids; the controller alone chooses ref roles. | R60 |
| C3 | Every newly registered problem can acquire one DETERMINISTIC companion subject artifact, recognised only when all six of the advice's conditions agree. | R59 |
| C4 | Registration is TWO-STEP and IDEMPOTENT: `register_problem` then `ensure_problem_subject`. A crash between them yields a typed `problem-subject-missing` diagnostic and an idempotent repair on resume. | R59 |
| C5 | **No fields added** to `Problem`, `EpistemicState` or `Event`; no new relation table. The companion is found through `addr`, computed from the existing record. | R59, the advice's second explicit rejection |
| C6 | A derived `problem_status(problem_id)` reads the companion's ORDINARY artifact status. The `Problem` record stays the immutable scheduling and provenance record. | R59 |
| C7 | Critics attack the companion exactly as they attack any other artifact — no new attack species, no new authority. | R59 |
| C8 | **NO scheduler integration.** The advice defers it, and this rung obeys. | R59 |
| C9 | The generic synthesizer is NOT retrofitted. It compiles every connected endpoint as `DEPENDENCE`, which is wrong for the calculus; the fix is dedicated claim-authoring operations, not a smarter synthesizer. | R60 |

## 3. Map preflight

`DR-INV-frozen-surfaces` first — C5 exists to keep this tranche out of surfaces
1, 2 and 3 entirely. Then `DR-SEAM-ontology-x-rules`, `DR-SUB-ontology`,
`DR-CON-problem-layer-lifecycle` (the premise channel this substrate will
eventually re-found), `DR-SUB-evaluation` (the new structural program joins the
existing evaluation path).

## 4. Amendments

(none yet)
