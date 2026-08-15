# DELIVERY — Rung 3c: the claim substrate and companion problem subjects

| # | Requirement | State | Where |
|---|---|---|---|
| C1 | Closed discriminated union; no open `RelationClaim(predicate)` | **DONE** | `calculus/claims.py` — nine names closed, two bodies built, seven refused typed |
| C2 | ONE compiler owns every ref role | **DONE** | `calculus/compiler.py`; pinned by an AST walk over the whole package |
| C3 | Deterministic companion subjects, six recognition conditions | **DONE** | `calculus/operations.py`, `calculus/views.py` |
| C4 | Two-step, idempotent, with a typed missing-companion diagnostic | **DONE** | `ensure_problem_subject`, `problem_subject_missing` |
| C5 | No fields on `Problem`/`EpistemicState`/`Event`; no relation table | **HELD** | the companion is computed from the existing record and found through `addr` |
| C6 | `problem_status` derived from the companion's ordinary status | **DONE** | `calculus/views.py` |
| C7 | Critics attack the companion like anything else | **DONE** | no new attack species, no new authority |
| C8 | NO scheduler integration | **HELD** | pinned: nothing under `scheduler/` imports `deepreason.calculus` |
| C9 | The synthesizer is not retrofitted | **HELD** | nothing in the package imports it; dedicated authoring operations instead |

## The design decision worth naming

**Closing the NAME set does not require building the bodies.** Seven of the
nine schemas are declared and refused with `claim-schema-not-implemented`, a
different code from `claim-schema-unknown`. Shipping nine body models with no
producers would be the pattern `docs/ERRATA.md` E28 records — a mechanism
nobody triggers, which this program has now paid for three times. What R60
actually asks for is that arbitrary prose predicates cannot become ontology,
and a closed name set delivers that today.

## What is next

P4 — the three-layer citable evidence flow (R62) — and A19 is queued behind it.
Rung 3b (frame-separation) sits immediately before Rung 4, where its subject
first exists. Moving the premise channel onto this substrate is unscheduled and
belongs to whichever rung needs the two shapes unified.
