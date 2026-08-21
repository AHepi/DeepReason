# Delivered: Rung 3b — the frame-separation invariant

Branch: `claude/calculus-rung3b-frame-separation-yqjxyt` (pushed, tree clean).
Base: `main@c8071fc34`. Discharges **R43** and **R64** of the v2 calculus
program (`experiments/2026-08-14-change-calculus-reconciliation-v2/LADDER.md`,
Rung 3b).

## What changed

One new module, `src/deepreason/calculus/separation.py` (111 lines), and one new
test file, `tests/test_calculus_frame_separation.py` (134 lines).

The module answers two questions and does nothing else. **Are these two things
separated?** — `adjudication_component` returns `Comp_L(x)`, the connected
component of a node in the undirected graph obtained from `att ∪ dep` by
forgetting edge directions (Definition 7.1), and `frame_separated` returns
whether two nodes' components are disjoint (Definition 7.2). **May this
assertion be consulted?** — `consultability` returns a frozen `Consultability`
verdict carrying a typed code, `frame-not-separated`, with the shared component
named in `detail`, or `frame-endpoint-unregistered` when the graph condition
cannot be evaluated at all.

A violation makes the assertion unconsultable and produces **nothing else**: no
attack edge, no warrant, no label change, no event. That is R64, and it is the
part with teeth. Proven behaviourally — the violation test captures the attack
edges, the support edges, every status label, the warrant map and the log's line
count before the call and asserts all five equal after it — and structurally: the
module holds no call that could write, and imports nothing from `adjudication`.
It consumes that package's output through replayed state, never its logic.

Mention edges turned out to need no filtering out of the graph. `build_dep`
builds support edges from `RefRole.DEPENDENCE` and from nothing else, so the
graph the harness already records excludes them — the exclusion Definition 7.2
calls for is a property of the existing code, not a line this rung wrote.

Nothing is stored. Components are recomputed from replayed state on every call,
like every other mark in this codebase.

## Reconciliation

| R | Operator's words (short) | Disposition | Proof |
|---|---|---|---|
| R1 | the predicate, derived over undirected `att ∪ dep`, never stored | done | `1da817eaa`; VALIDATION S1 |
| R2 | mention edges EXCLUDED from that graph | done | VALIDATION S1 — the mention yields singleton components |
| R3 | a failing frame is UNCONSULTABLE with a typed diagnostic | done-with-assumption **A1** | VALIDATION S2; the unregistered-endpoint refusal is A1 |
| R4 | NEVER a manufactured refutation — no edge, no warrant, no label change | done | VALIDATION S3 (structural, exit 0) + S6 (five-way equality) |
| R5 | scope boundary stated; no Rung 4 machinery | done | SPEC.md S4 states it; VALIDATION S4's two commands prove it HELD |
| R6 | the gate EXHIBITS the separation, not merely the mention | done | VALIDATION S5 — disjoint components asserted, plus Theorem 7.3's extension in full |
| R7 | the violation is inert; byte-identical label comparison | done | VALIDATION S6 |
| R8 | MUTATION PROOF: disable the check, watch it go RED, paste both runs | done | VALIDATION S7 — **two** mutations, RED then GREEN, both pasted |
| R9 | axiom ledger: PROVES A6 and A5, PRESERVES A1 and A3 | done | VALIDATION S8 table, each with named evidence |
| R10 | size: STOP if the plan exceeds ~200 | done, `superseded-by:R15` as a ceiling | The PLAN was 193, under the threshold. The ACTUAL 312 tripped `diff_budget.py` and was raised as a STOP, not absorbed |
| R11 | frozen surfaces: forecast none | done | `git diff --stat` over all five surfaces: EMPTY. `blast_radius.py` `CLEAR` at spec time and again at the commit checkpoint |
| R12 | the map moves in the same commits, with a check that would fail on regression | done | `1da817eaa` carries code, exports and both map documents; 5 new checks, each RUN before written down, 2 mutation-proved |
| R13 | ring while iterating, full gate at the boundary, docs_verify FULL | done | ring 58 passed; gate **3759 passed, 0 failed**; docs_verify 3 failed = baseline exactly |
| R14 | deliver R-by-R with pasted PROOF | done | this document |
| R15 | "Proceed at 312 (Recommended)" | done | Amendment 1; steps 12–15 executed |
| R16 | record the variance so the ceiling keeps its meaning at Rung 4 | done | VALIDATION §R16, line for line |

No requirement is deferred and none is not-done.

## Assumptions the operator may override

- **A1** — an unregistered endpoint gets its own typed refusal
  (`frame-endpoint-unregistered`) rather than a silent "consultable". The literal
  reading of Definition 7.2 would report a frame whose subject does not exist as
  SEPARATED, hence consultable. Six lines, and the precedent is this repo's own:
  `premises.py::premise_rent_sweep` records that "we could not check" must never
  look like "we checked and it was fine".
- **A2** — `Comp_L(x)` for a node with no `att`/`dep` edge is the singleton
  `{x}`. Definition 7.1 leaves isolated vertices formally undiscussed; the
  singleton is the only reading on which an empty graph is separated rather than
  an error.
- **A3** — the invariant is stated in the two map documents that already cover
  it rather than in a new `INV-frame-separation.md`, because LADDER §5b assigns
  the v2 axiom `INV-` document to **Rung 4**.

## Map delta

    changed: docs/map/SUB-calculus.md, docs/map/CON-standing-and-background.md
    created: none
    new checks: 5 (4 in SUB-calculus.md, 1 in CON-standing-and-background.md)
    left stale: SUB-calculus.md — 1 commit, which IS this tranche's own
                code+map commit. A document cannot carry the hash of the commit
                that contains it. The base already listed it at 2 commits stale,
                so this tranche reduced it; the residue is the unavoidable
                self-reference.

`SUB-calculus.md` gains `separation.py` to `Owns:`, the pair
`calculus x adjudication` to `Seams-undocumented:` (a real, previously
unrecorded agreement that PREDATES this rung — `views.py` already reads
`harness.state.status` the same way), an invariant section with two checks, and
two `Traps` entries. `CON-standing-and-background.md`, the concept document for
the standing axis, gains the invariant under *Invariants* and a row under *Where
to change what*. `Verified-at:` advanced on both, and only after their checks
were re-run. `docs_verify --audit` reports 0 findings repo-wide, so none of the
five new checks is vacuous.

## Errata

Two entries, landed in this commit:

- **E35** — `docs/COMPUTABLE_CALCULUS.md` Proposition 9.6's proof discharges
  Pass 2 only and is therefore incomplete, and Law 9.4's "this single interface
  constraint is the whole separation of the axes" is false as stated. What Prop
  9.6 concludes survives, but only under the hypothesis this rung ships. The gap
  is now executable rather than only argued in the Formalization's prose.
- **E36** — `docs/map/INV-frozen-surfaces.md` still opens with the law CLAUDE.md
  retired on 2026-08-14, and still names the 42-root sweep as its instrument
  after LADDER §2 removed it as a gate obligation. Found at this rung's map
  preflight; not fixed here (PARKED P3).

## Parked (not done, not promised)

- **P1** — `premises.py::standing_attributions` is the codebase's only existing
  consultation predicate and carries the mention law WITHOUT separation. Wiring
  it would change Rung 2's delivered cascade semantics, so the park's prompt
  makes it a measurement tranche first: count, over committed roots, how many
  consulted attributions would become unconsultable, and name the node that
  joins each pair.
- **P2** — `docs/map/INDEX.md`'s concept table omits two existing `CON-`
  documents. The prompt asks for a completeness CHECK, not two table rows, since
  two rows leave the next addition to fall out the same way.
- **P3** — `INV-frozen-surfaces.md` states the retired law (E36).

Each carries a ready-to-send prompt in `PARKED.md`; the follow-up costs a paste.

**Recommended next: P3.** Not because it is the most interesting — it is the
least — but because `INV-frozen-surfaces.md` is the document every tranche is
instructed to open FIRST, and it currently tells that reader the opposite of
what CLAUDE.md's operator law says about whether a record format may change.
Every rung from 4 onward reads it at preflight, and Rungs 4 and 7 have forecast
contact with exactly the surface it misdescribes.

## What a Rung 4 builder can now rely on

Rung 4 can build the frame layer against an invariant that already exists,
already refuses, and has been shown failable — so its gate invokes Theorem 7.3
instead of re-arguing it, and it inherits, tested, the fact the mention law
alone never gave it: that separation and mention are independent, and only the
first is what keeps a wound from moving the frame.
