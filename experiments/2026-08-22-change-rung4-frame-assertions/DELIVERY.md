# Delivered: Rung 4 — frame assertions and the standing view
Branch: `claude/calculus-rung4-frame-assertions-aafy3a` (pushed, tree clean)

## What changed

DeepReason now has its second axis. Before this tranche the harness could
answer one question about an artifact — is every attack on it defeated? — and
had no way to represent the ordinary condition of mature knowledge: an idea
that is **refuted and still framing** the problems around it.

A **frame assertion** is now an ordinary artifact whose content is Def 9.2's
frame claim: a subject, a scope predicate, a validity, and a departure
protocol. It gets no new event rule and no `kind` field, because the two axes
are separated by EDGE ROLE rather than by a node type — the compiler makes the
subject a MENTION and each cited reach record a DEPENDENCE, and that single
assignment is the whole separation. A wound to the subject cannot drag the
frame down; refuting its case cuts its support.

`standing(b)` is a derived view, recomputed from the log on every call and
never stored. An assertion is CONSULTED only when all four of Def 9.2's
conditions hold, and the fourth calls Rung 3b's separation predicate directly
rather than re-deriving it — `separation.py` has a zero-line diff.

New files: `calculus/scope.py` (the scope predicate in D-5's fixed finite DSL,
reusing `declarative_numeric_v1`'s shape) and `calculus/standing.py` (the
consult path and the derived view). `deepreason standing` and the
`run_standing` MCP tool render it read-only. `verify_root` gains one additive
`standing-integrity` clause. `docs/map/INV-axiom-basis.md` is new: eleven
axioms, each with the rung that proves it, the rungs that preserve it, and a
check that can fail.

**Revocation has no rule of its own, and none was written.** Attack the reach
record; support is cut; pass two makes the assertion `suspended_unsupported`;
it stops being consulted. Orphaned ≠ false does the work — revocation says
unearned, not wrong.

## Reconciliation

| R | Operator's words (short) | Disposition | Proof |
|---|---|---|---|
| R1 | "Frame assertion as an ORDINARY artifact … No new event rule, no kind field" | done | VALIDATION S1, 6 tests |
| R2 | "an assertion carrying a `dependence` ref on its subject FAILS well-formedness" | done | VALIDATION S2; reason `frame-assertion-depends-on-subject` |
| R3 | "CONSULT THROUGH SEPARATION … invoke the delivered machinery" | done | VALIDATION S3; `separation.py` zero-line diff |
| R4 | "standing(b) as a DERIVED view … recomputed from the log, never stored" | done | VALIDATION S4 |
| R5 | "The scope predicate sigma in D-5's fixed DSL … C1 determinism" | done-with-assumption A3 | VALIDATION S5 |
| R6 | "A read-only `standing` view surface (CLI/MCP) … ALL FOUR wheel-smoke pins" | done | VALIDATION S6; both smokes exit 0 |
| R7 | "The axiom-basis INV- map document … checks that can fail" | done | VALIDATION S7; `--audit` 0 findings |
| R8 | "Prop 12.5 … STRONGEST FORM … IDENTICAL labels" | done | VALIDATION S9 |
| R9 | "Prop 12.4, axis independence, BOTH directions" | done | VALIDATION S10 |
| R10 | "Thm 12.3: a frame assertion inherits every exit" | done | VALIDATION S11 |
| R11 | "S-10 … Assert the absence" | done-with-assumption A5 | VALIDATION S11; structural AND behavioural |
| R12 | "L-2 operations parity: amend-then-continue" | done | VALIDATION S11 |
| R13 | "MUTATION PROOF … watch it go RED, restore, paste both runs" | done | VALIDATION S9 — three mutations, both restores, in full |
| R14 | "PROVES A4, A5, A7; PRESERVES A1, A3, A6" | done | VALIDATION S7 |
| R15 | "Request the grant in SPEC.md BEFORE code" | done | SPEC.md S13; REQUEST.md Amendment 2; `INV-frozen-surfaces` |
| R16 | "Deliver R-by-R with pasted PROOF" | done | this document |
| R17 | ceiling 963 | superseded-by R19 | REQUEST.md Amendment 3 |
| R18 | variance recorded | done | REQUEST.md Amendment 3 |
| R19 | ceiling 1850 | **exceeded at 2290, reported** | VALIDATION "The ceiling, stated plainly"; ERRATA E39 |
| R20 | variance cause named | done | REQUEST.md Amendment 3; ERRATA E39 |

Two dispositions a reader should not skim past. **R19 is exceeded**, not met:
the final figure is 2 290 against a ceiling of 1 850, and the entire post-raise
overrun is one document — the mandated axiom ledger at 259 lines against my
~95 estimate. **C7's root-sweep instruction was not followed**, deliberately: a
sweep was started, the operator killed it, and they were right — CLAUDE.M's
standing law retires the instrument and names a single-root replay as the
stronger substitute, which this tranche already commits.

## Assumptions the operator may override

- **A1** Rung 4 owns what a promotion problem IS (`SpawnTrigger.PROMOTION` +
  one idempotent registration); Rung 5 owns WHEN one is spawned. Without the
  notion, Def 9.2's consult condition is undefined.
- **A2** Rung 4 owns the departure protocol's content SLOT only; Rung 6 owns
  its behaviour. Nothing here interprets or acts on it.
- **A3** Sigma reads the `Problem` record and nothing else — which is what
  makes C1 determinism structural rather than promised.
- **A4** The `RECRIT_STANDING` name collision is disambiguated in the map, not
  renamed. Renaming is a compatibility decision and was not requested.
- **A5** An absence is proven structurally AND behaviourally; either alone is
  satisfiable by the wrong thing.
- **A6** No new LLM role, so frozen surface 5 stays at zero and no
  qualification battery is owed.

## Map delta

**Created:** `docs/map/INV-axiom-basis.md` (14 checks).
**Changed:** `SUB-calculus`, `CON-standing-and-background` (rationale →
mechanism), `SEAM-adjudication-x-authority` (the seam extended from authority
to standing), `INV-frozen-surfaces` (the granted contact recorded),
`SUB-periphery` (the four-pin trap), `INDEX`, plus four count-pinning checks
in `SUB-ontology`, `SUB-rules`, `SEAM-rules-x-scratch` and
`SEAM-evaluation-x-ontology`, and one in `SEAM-harness-x-verification`.
**New checks:** ~30 across those documents; every one was RUN before it was
written down.
**Left stale:** `CON-run-identity`, `CON-schools`, `SEAM-manifest-x-schools`
(all stale since `bce018ae5`, the all-configs tranche) and `SUB-evidence`
(since `1a32fb193`, P4). All four predate this work; stamping them would be
claiming a verification I did not perform. The four this tranche did re-verify
had their stamps advanced.

## Errata

**E39** — `LADDER.md`'s per-rung line estimates are systematically low, with
the measurable shape of the error stated so Rungs 5–8 can be checked against
something rather than trusted.
**E40** — E38's grep-based frozen-surface false positive recurred on a second
symbol (`consulted`) in the next tranche to run the gate; two instances on
unrelated symbols in consecutive tranches is a rate, not an anecdote.

## Parked (not done, not promised)

**P1 — rename `Config.RECRIT_STANDING` / `scheduler._standing_recrit_pool`.**
The "standing" name collision became REAL this tranche. Disambiguated in the
map; the rename is a compatibility decision (the field is readable from profile
YAML) and was not requested.

**P2 — gate `premises.py::standing_attributions` on separation.** Inherited
from Rung 3b unchanged. Rung 4 wired `consultability` for frame assertions,
which is what Rung 3b said it would do; whether the premise channel's own
consult predicate should also run it is still open.

**P3 — `INDEX.md` omits three documents that exist** (`INV-signal-contract`,
`REC-add-signal`, `REC-revise-allocation-policy`, all from Rung 1b). Nothing
is broken — `--links` passes — but a reader routing rather than grepping will
not find them. Three lines of work.

Each carries a ready-to-send prompt in PARKED.md.

**Recommended next: Rung 5** (promotion problems and their criteria as
programs), not any parked item. Its entry condition — Rung 4's DELIVERY — is
now met, and it is the rung that gives `SpawnTrigger.PROMOTION` its producer,
closing the one place this tranche left a shape without the measure that fires
it. P3 is three lines and can ride any later tranche; P1 and P2 are real
decisions that should not be spent ahead of the ladder.
