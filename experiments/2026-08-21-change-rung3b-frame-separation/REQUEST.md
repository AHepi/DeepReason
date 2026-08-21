# REQUEST — Rung 3b: the frame-separation invariant

Route: `dr-change-orchestrator`. **Rung 3b of the v2 calculus program**
(`experiments/2026-08-14-change-calculus-reconciliation-v2/LADDER.md`).
Date: 2026-08-21. Branch: `claude/calculus-rung3b-frame-separation-yqjxyt`.
Base: `main@c8071fc34` (ancestor verified).

## 1. Authority

The operator-approved program ladder, `LADDER.md` Rung 3b, which discharges
**R43** and **R64** of that program's `REQUEST.md`. Entry condition met: Rung 3a
delivered 2026-08-15 (`experiments/2026-08-15-change-rung3a-h1-successor-
deletion/DELIVERY.md`).

The source the rung encodes, verbatim from
`docs/POIETIC_CALCULUS_FORMALIZED.md` §7:

> **Definition 7.1 (Adjudication component).** Let \(Q_L\) be the undirected
> graph obtained from \(att_L\cup dep_L\) by forgetting edge directions. Let
> \(\operatorname{Comp}_L(x)\) be the connected component of \(x\) in \(Q_L\).

> **Definition 7.2 (Frame-separation invariant).** A consulted frame assertion
> \(f\) with subject \(b\) is separated when
> \(\operatorname{Comp}_L(f)\cap\operatorname{Comp}_L(b)=\varnothing\).
> Mention edges are deliberately excluded from \(Q_L\). Reach records supporting
> \(f\) must mention, rather than depend on, the subject if subject refutation is
> not intended to revoke the reach case.

> **Theorem 7.3 (Wound persistence).** Suppose \(\operatorname{Consult}_L(f,\pi)\),
> \(\operatorname{subject}(f)=b\), and the frame-separation invariant holds. Let
> \(L'\) extend \(L\) only by registering a new critic component whose only
> connection to the old adjudication graph is an attack on \(b\). Then
> \(\ell_{L'}(f)=\ell_L(f)=\mathsf U\).

And LADDER Rung 3b's own enforcement clause, verbatim:

> **R64 — what a violation DOES.** A frame that fails separation becomes
> **UNCONSULTABLE, with a typed diagnostic — never a manufactured refutation.**
> An unmet engineering invariant is a reason to stop trusting a frame; it is not
> a reason to invent a defeat for it. Putting a fabricated verdict on the graph
> to record a code fault would make the record lie about epistemics in order to
> report a bug, and the record is the only admissible evidence this system has.

Tranche instruction, verbatim on scope:

> This rung is deliberately small; do not grow it.

> S3 SCOPE BOUNDARY, stated in SPEC.md: full frame assertions do not exist until
> Rung 4. This rung ships the predicate and the enforcement over constructible
> graph shapes now, so Rung 4 builds its frame layer against an invariant that
> already exists and already has teeth. Rung 4's gate will then invoke Theorem
> 7.3 instead of re-arguing it. Do not build any Rung 4 machinery (no frame
> assertion artifact, no standing view, no scope DSL).

## 2. Requirements

| # | Requirement | Source |
|---|---|---|
| R1 | **The predicate.** Frame-separation as a DERIVED check over the undirected `att ∪ dep` graph, mention edges excluded, computed from replayed state. Derived, never stored — like every mark in this codebase. | S1, Def 7.1/7.2 |
| R2 | **Mention edges are excluded** from the graph, and that exclusion is proven, not merely inherited: a mention-only link between two artifacts must leave them separated. | S1, Def 7.2 |
| R3 | **The enforcement.** A construction that FAILS separation is UNCONSULTABLE and carries a TYPED diagnostic (a code a caller branches on, not message text). | S2, R64 |
| R4 | **Never a manufactured refutation.** A separation violation yields NO attack edge, NO warrant, NO label change, NO status movement anywhere. | S2, R64 |
| R5 | **Scope boundary stated in SPEC.md**: no frame-assertion artifact, no standing view, no scope DSL, no Rung 4 machinery of any kind. | S3 |
| R6 | **Gate — separation HOLDS.** For every consulted-assertion-shaped construction this rung can build over current machinery, the gate EXHIBITS the separation (Theorem 7.3's precondition), not merely the mention. | Gate |
| R7 | **Gate — the violation is inert.** A constructed violation yields the typed unconsultable diagnostic and nothing else; the strongest available form is a before/after label comparison that is byte-identical. | Gate, R4 |
| R8 | **MUTATION PROOF.** Disable the separation check in a scratch copy, run the violation test, watch it go RED, restore, paste both runs. | Gate |
| R9 | **Axiom ledger** (LADDER §5b) named in VALIDATION.md: this rung PROVES **A6** and its precondition **A5**; PRESERVES **A1**, **A3**. | Gate, §5b |
| R10 | **Size.** LADDER estimates 80–140 lines. If SPEC.md's plan exceeds ~200, STOP and say what grew. | SIZE |
| R11 | **Frozen surfaces: forecast none** (LADDER §4 consolidated table, Rung 3b row: all dashes). Any wanted contact with verification formats is requested in SPEC.md BEFORE code. | FROZEN SURFACES |
| R12 | **The map moves in the same commits.** The covering documents gain the invariant and a check that would fail if it regressed; the check is RUN before it is written down. | GATE, SCHEMA.md |
| R13 | **Gate discipline.** Ring while iterating; full gate (`python -m pytest tests/ -q -n 4`, 0 failed) at the boundary; `python tools/docs_verify.py` FULL against `docs/AUDIT_BASELINES.md`. | GATE |
| R14 | **Delivery.** R-by-R with pasted PROOF, closing with one line: what a Rung 4 builder can now rely on that they could not before. | Deliver |

## 3. Map preflight

`DR-INV-frozen-surfaces` read FIRST. Rung 3b forecasts zero contact with all
five surfaces; nothing in this plan writes an event, a digest, a manifest field
or a replay-validation record.

Resolved ids, in reading order:

- **`DR-SUB-calculus`** — the typed claim substrate; owns
  `src/deepreason/calculus/`. The predicate belongs here: it is a derived view
  over replayed state, exactly the shape `views.py` already has. This is the
  covering document for R12.
- **`DR-SUB-adjudication`** — owns `att`/`dep` and is the ONLY producer of
  status. Read to establish that the predicate consumes its OUTPUT and never
  its logic: `build_dep` emits edges from `RefRole.DEPENDENCE` and from nothing
  else, so mention edges are already absent from `dep` and R2's exclusion is a
  property of the existing graph rather than a filter this rung adds.
- **`DR-SUB-ontology`** — `RefRole`, `Interface`, `Status` vocabulary.
- **`DR-CON-warrants-and-attacks`** — no warrant, no edge, no REFUTED: the
  chain R4 must leave untouched.

**Finding, recorded rather than deferred (per `dr-drive-harness` §4).** The pair
`calculus × adjudication` has no seam document and is not listed in
`SUB-calculus.md`'s `Seams-undocumented:` line, yet the predicate reads
`harness.state.att` and `harness.state.dep` — adjudication's output, reached
through the harness's derived state. This is not NEW traffic: `views.py` already
reads `harness.state.status` the same way, so the undocumented agreement
predates this rung. The tranche adds the pair to `SUB-calculus.md`'s
`Seams-undocumented:` line (which is what that header is for — keeping the
identification without promising a file nobody wrote) and does NOT write a seam
document, because `INDEX.md` §"How to CHANGE the map" rule 6 ranks seam writing
by measured coupling and this pair has zero direct imports in either direction.

## 4. Amendments

(none yet)
