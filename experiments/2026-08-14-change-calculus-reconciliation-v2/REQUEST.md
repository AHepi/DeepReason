# REQUEST — Calculus reconciliation, v2 (design-and-stop)

Route: `dr-change-orchestrator`. Tranche kind: DESIGN-AND-STOP. **No code in
this tranche.** The deliverable at the gate is a set of committed documents and
an ended turn.

Date opened: 2026-08-14. Branch: `claude/calculus-reconciliation-v2-qqghvn`.
Base: `50e2397a9` (the commit that landed
`docs/COMPUTABLE_CALCULUS.md` + `.pdf`).

---

## 1. The operator's words, verbatim

> Design-and-stop tranche: reconcile the Computable Calculus with the
> shipped harness — the v2 reconciliation. Route through
> dr-change-orchestrator; STOP after the deliverables below. NO CODE in
> this tranche.
>
> SETUP (fresh container): git fetch origin main && git checkout -B
> claude/calculus-reconciliation-e94wjt origin/main; git merge-base
> --is-ancestor 50e2397a9 HEAD || re-fetch. pip install -e .
> --break-system-packages -q; pip install pytest pytest-xdist jsonschema
> --break-system-packages -q. Use `python -m pytest`, never bare pytest.
> Read CLAUDE.md in full; load dr-drive-harness, dr-explain-to-operator.
> Then read docs/COMPUTABLE_CALCULUS.md IN FULL (the PDF is authoritative
> on any extraction doubt) and docs/harness-spec-v1.3.md plus ALL
> amendment files.
>
> AUTHORITY for REQUEST.md — the calculus document plus the operator's
> ledgered doctrine (2026-08-13, verbatim, all of it): problems are
> first-class subjects of criticism ("the problem itself is the subject of
> criticism, which is summarily refuted"); "Problems spawn conjectures,
> but failed conjectures shouldn't spawn problems"; the faulty-instrument
> and siren examples; the background doctrine ("a first class
> epistemological object that shaped a person's world view... nothing in
> the spec that makes the above epistemological distinction"); and the
> operator's confirmation: "The successor functioning should replace
> conjecture spawned sub problems."
>
> THREE HEADLINE ITEMS, PRE-DECIDED BY THE OPERATOR (design them, do not
> re-litigate them):
> H1. The calculus's spawn trigger "failed verdict ⇒ successor problem"
>     is DELETED from the v2 design. A failed conjecture records its
>     failed commitments and mints nothing. Succession lives on the
>     problem layer via the frame/premise cascade (§9.7-9.8). Design the
>     consequence: what covers legitimate sharpening (answer: premise-
>     criticism and discrimination on the problem layer — say how).
> H2. GENERALIZE the premise channel: provenance.frame becomes the
>     special case of recorded problem premises. Design the general
>     mechanism in the calculus's own idiom: a critic may register a
>     problem's hidden presupposition as an ordinary artifact AND an
>     adjudicated attribution artifact ("π presupposes X"); when the
>     attribution stands unrefuted and X is refuted, the §9.8 orphan
>     cascade fires unchanged (retire / translate / independence). The
>     siren case must have a complete legal move sequence; N3 keeps its
>     force; nothing is hardcoded.
> H3. Status vocabulary: the calculus's terms (unrefuted /
>     suspended_unsupported etc.) are adopted at VIEW and presentation
>     layers only — stored record labels never change; readers stay
>     byte-compatible with every committed root.
>
> DELIVERABLES (all committed, then STOP):
> 1. RECONCILIATION.md — the full drift table: every definitional,
>    axiomatic, and mechanical divergence between the calculus, the
>    v1.3+amendments spec series, and the current tree. One row each:
>    calculus says / spec says / code does / proposed disposition
>    (adopt / adapt / defer / conflict-needs-word). The three headline
>    items appear as ALREADY-DECIDED rows. Anything requiring an
>    operator word beyond the three is BATCHED into one decision sheet
>    at the end — priced options, one recommendation each.
> 2. LADDER.md — the v2 implementation program as gated rungs, each
>    rung one tranche with entry/exit artifacts and its gate, in
>    dependency order (suggested shape, verify against the drift table:
>    groundwork/vocabulary → premise channel + spawn-trigger deletion →
>    frame assertions + standing view → promotion problems + programs →
>    render semantics + departure protocol → falls/cascade/orphans →
>    rent/nomination/authority-audit + capture integration). Per rung:
>    estimated size, frozen-surface forecast (additive contacts
>    enumerated — provenance fields are reader-widening; every committed
>    root must replay byte-unchanged at every rung), and which calculus
>    propositions its gate proves.
> 3. Map preflight recorded; existing PARKED items that the v2 program
>    absorbs (P4 evidence-citability, P5 conviction-criteria, P6
>    anti-relapse degradation, the signal-contract park) each get one
>    row saying which rung absorbs them.
>
> CONSTRAINTS: frozen surfaces are FORECAST here, never touched (no code
> this tranche); the calculus's own C-invariants (derived-never-stored,
> content-never-type, measures-never-adjudicate) are binding on every
> proposed design; the operator's standing laws (all-configs,
> operations-parity, solo, formalism-optional, seats/evidence) each get a
> drift-table row confirming the v2 design honors them or naming the
> tension. Errata check: any committed document contradicted by the
> calculus's adoption gets an entry candidate ROW in RECONCILIATION.md
> (entries are minted by the implementing tranches, not this one — next
> free number moves fast; check the tail). Commit and push every phase
> boundary (retry 2s/4s/8s/16s). Deliver the batched decision sheet as
> the final artifact and STOP for the operator's words.

## 2. Requirements

Authority ranking inside this tranche: the operator's words above >
`docs/COMPUTABLE_CALCULUS.pdf` (the extraction `.md` is a convenience) >
`docs/harness-spec-v1.3.md` + amendments v1.4–v1.7 > the tree.

| # | Requirement | Source |
|---|---|---|
| R1 | Route through `dr-change-orchestrator`; STOP after the deliverables. | prompt ¶1 |
| R2 | NO CODE in this tranche. Frozen surfaces are FORECAST, never touched. | prompt ¶1, CONSTRAINTS |
| R3 | Read the calculus IN FULL; the PDF governs on extraction doubt. Read v1.3 + ALL amendments. | prompt SETUP |
| R4 | Authority for this ledger = the calculus + the operator's ledgered doctrine of 2026-08-13 (all five fragments quoted in §1). | prompt AUTHORITY |
| R5 | **H1 — pre-decided, not re-litigated.** Delete "failed verdict ⇒ successor problem" from the v2 design. A failed conjecture records its failed commitments and mints nothing. | prompt H1 |
| R6 | **H1 consequence, to be designed:** what covers legitimate sharpening — premise-criticism and discrimination on the problem layer. Say HOW. | prompt H1 |
| R7 | **H2 — pre-decided.** Generalize the premise channel: `provenance.frame` becomes the special case of recorded problem premises. | prompt H2 |
| R8 | H2 mechanism, in the calculus's own idiom: a critic may register a problem's hidden presupposition as an ordinary artifact AND an adjudicated attribution artifact ("π presupposes X"). | prompt H2 |
| R9 | H2 firing rule: attribution unrefuted ∧ X refuted ⇒ the §9.8 orphan cascade fires UNCHANGED (retire / translate / independence). | prompt H2 |
| R10 | H2 worked example: the siren case must have a COMPLETE legal move sequence. | prompt H2 |
| R11 | H2 constraints: N3 (no insolubility) keeps its force; nothing is hardcoded. | prompt H2 |
| R12 | **H3 — pre-decided.** Calculus status vocabulary adopted at VIEW and presentation layers ONLY. Stored record labels never change; readers stay byte-compatible with every committed root. | prompt H3 |
| R13 | Deliverable 1: `RECONCILIATION.md` — full drift table, every definitional / axiomatic / mechanical divergence across calculus × spec series × tree. Columns: calculus says / spec says / code does / disposition ∈ {adopt, adapt, defer, conflict-needs-word}. | prompt D1 |
| R14 | H1/H2/H3 appear in the drift table as ALREADY-DECIDED rows. | prompt D1 |
| R15 | Anything needing an operator word beyond the three headline items is BATCHED into ONE decision sheet at the end — priced options, one recommendation each. | prompt D1, closing |
| R16 | Deliverable 2: `LADDER.md` — the v2 program as gated rungs, one tranche each, entry/exit artifacts and gate, in dependency order; the suggested seven-rung shape is to be VERIFIED against the drift table, not assumed. | prompt D2 |
| R17 | Per rung: estimated size; frozen-surface forecast with additive contacts enumerated; every committed root replays byte-unchanged at EVERY rung; which calculus propositions the rung's gate proves. | prompt D2 |
| R18 | Deliverable 3a: map preflight recorded (this file, §3). | prompt D3 |
| R19 | Deliverable 3b: PARKED items absorbed by the v2 program — P4 evidence-citability, P5 conviction-criteria, P6 anti-relapse degradation, the signal-contract park — one row each naming the absorbing rung. | prompt D3 |
| R20 | The calculus's own C-invariants are binding on every proposed design: C4 derived-never-stored, C3 content-never-type, C5 measures-never-adjudicate. | prompt CONSTRAINTS |
| R21 | Each operator standing law (all-configs, operations-parity, solo, formalism-optional, seats/evidence) gets a drift-table row confirming the v2 design honors it, or naming the tension. | prompt CONSTRAINTS |
| R22 | Errata check: any committed document contradicted by adopting the calculus gets an entry-candidate ROW here (entries are MINTED by the implementing tranches, not this one). Next free number checked against the ledger tail. | prompt CONSTRAINTS |
| R23 | Commit and push at every phase boundary, with retry backoff 2s/4s/8s/16s. | prompt CONSTRAINTS |
| R24 | The batched decision sheet is the FINAL artifact; then STOP for the operator's words. | prompt closing |

### Recorded deviations from the prompt's literal SETUP

| # | What the prompt said | What was done | Why |
|---|---|---|---|
| D-a | `git checkout -B claude/calculus-reconciliation-e94wjt origin/main` | Work is on `claude/calculus-reconciliation-v2-qqghvn`, already at `50e2397a9` = `origin/main` head | The session's designated branch is `claude/calculus-reconciliation-v2-qqghvn` and it already pointed at the required base commit. Same base, same content; only the branch name differs. Flagged rather than silently absorbed. |
| D-b | ancestry assert on `50e2397a9` | `git log --oneline -1` = `50e2397a9` (HEAD itself) | Ancestry holds trivially. |

### Authority gaps recorded at capture time (R4)

Three of the five doctrine fragments in R4 are quoted verbatim in the prompt
and are therefore fully in hand. Two are NAMED but not quoted, and are not
recoverable from this repository:

| Fragment | Status | Handling |
|---|---|---|
| "the problem itself is the subject of criticism, which is summarily refuted" | verbatim | binding as written |
| "Problems spawn conjectures, but failed conjectures shouldn't spawn problems" | verbatim | binding as written |
| "a first class epistemological object that shaped a person's world view... nothing in the spec that makes the above epistemological distinction" | verbatim (with the operator's own ellipsis) | binding as written |
| "The successor functioning should replace conjecture spawned sub problems." | verbatim | binding as written |
| **the faulty-instrument example** | NAMED, not quoted | Reconstructible from the calculus itself: Closure 3 (§3.4) and §9.6 both work the example — "the faulty instrument is an attack on the observation, and its success is an ordinary reinstatement". Used in that form. |
| **the siren example** | NAMED, not quoted; **absent from this repository** (`grep -rni siren --include=*.md .` returns nothing outside this tranche) | R10 requires a complete legal move sequence for it. RECONCILIATION.md reconstructs the canonical siren case explicitly AS A RECONSTRUCTION, marked as such, and the decision sheet carries one line asking the operator to confirm or supply the original. |

## 3. Map preflight (R18)

Resolved before designing, in the order `dr-drive-harness` §4 fixes:
`INDEX.md` → `INV-frozen-surfaces.md` → seams → subsystems.

**Frozen surfaces read first** (`DR-INV-frozen-surfaces`): all five, plus the
frozen-adjacent `route_fingerprint`. The v2 program's forecast contacts are
enumerated per rung in `LADDER.md` §4.

**Seams read before their subsystems** (the ordering rule):

| Seam id | Why this program touches it |
|---|---|
| `DR-SEAM-ontology-x-rules` | owns `ontology/problem.py` AND `rules/spawn.py` — the exact pair H1 (spawn deletion) and H2 (problem premises) move together |
| `DR-SEAM-adjudication-x-rules` | owns `rules/warrants.py` + `adjudication/edges.py` — the attribution artifact of H2 must ride the existing warrant→edge chain, adding no new edge species |
| `DR-SEAM-scheduler-x-rules` | orphan marks deprioritize problems (attention only, C5); retirement removes a problem from selection without deleting it |
| `DR-SEAM-evaluation-x-rules` | promotion criteria (§9.4) are ordinary program commitments evaluated by the existing evaluation path |
| `DR-SEAM-adjudication-x-authority` | the standing layer must never reach label computation (Prop 12.5); this seam's whole content is "the agreement IS the absence of traffic" |
| `DR-SEAM-llm-x-rules` | the frame slice (§9.5) is a pack section, rendered deterministically |

**Subsystems in scope:** `DR-SUB-ontology`, `DR-SUB-rules`,
`DR-SUB-adjudication`, `DR-SUB-scheduler`, `DR-SUB-llm`, `DR-SUB-evaluation`,
`DR-SUB-verification` (frozen), `DR-SUB-harness` (frozen),
`DR-SUB-manifest` (frozen).

**Concepts in scope:** `DR-CON-warrants-and-attacks` (the no-warrant-no-edge
chain the premise channel must not bypass), `DR-CON-authority`,
`DR-CON-scheduler-ranking`, `DR-CON-packs-and-token-economy`,
`DR-CON-conjecture-kinds` (the R-g guardrail: nothing may weight outcomes on
conjecture KIND).

**Map gap, recorded as a finding, not a blocker (`dr-drive-harness` §4.5):**
the standing layer of §9 has NO map id, because it does not exist in the tree.
The v2 program must MINT one — a new `CON-standing-and-background.md`
(`DR-CON-standing-and-background`) — and Rung 1 owns that minting. A second
gap: `DR-SEAM-scheduler-x-rules` exists, but no document covers
`problem-layer lifecycle` (pose → orphan → resolution), which is what Rung 6
creates.

## 4. Amendments

### Amendment 1 — 2026-08-14, operator's answer to D-2 (Road B)

Received after `DECISIONS.md` was delivered; appended verbatim BEFORE acting on
it, per the ledger rule.

> D-2: Road B. The original example, operator verbatim (2026-08-13): "What
> is the colour of a siren. It's a question that could be interpreted as a
> problem, but it's fundamentally flawed before even receiving an answer...
> In this case, the problem itself is the subject of criticism, which is
> summarily refuted. Not a conjecture, a problem." The presupposition X =
> "a siren is the kind of thing that has a colour" — a category error, no
> instrument or measurement anywhere. The eight-move sequence must work
> with X refuted by argument alone.

| # | Requirement | Source |
|---|---|---|
| R25 | The siren example is the operator's own, quoted above. The Doppler reconstruction is SUPERSEDED and must be replaced, not annotated. | Amendment 1 |
| R26 | X = "a siren is the kind of thing that has a colour". A category error: **no instrument or measurement anywhere.** The sequence may not route through an observation, an evidence artifact, or the faulty-instrument reinstatement. | Amendment 1 |
| R27 | The move sequence must work **with X refuted by argument alone.** | Amendment 1 |
| R28 | "Not a conjecture, a problem" — the criticised object is the PROBLEM, and it is "fundamentally flawed before even receiving an answer". The sequence must reach retirement without any conjecture on π having been proposed or having failed. | Amendment 1 |

**Supersession note.** R10's deliverable (a complete legal move sequence for the
siren case) is unchanged; only its subject matter is replaced. `DECISIONS.md`
D-2 is ANSWERED and closed. The remaining six decisions (D-1, D-3 … D-7) are
still open, and Amendment 1 adds a seventh, D-8, whose necessity was discovered
in the course of satisfying R27.

### Amendment 2 — 2026-08-14, operator's answer to D-7 (option iii)

Appended verbatim BEFORE acting on it, per the ledger rule.

> D-7: (iii), content follows — the operator-parked signal-contract design
> (ledgered with the monitor, 2026-08-13), absorbed as its own rung or
> folded into Rungs 1+4 as the drift table prefers:
> (1) The signal REGISTRY is a CONTRACT, not a wiring: a signal is anything
> declaring name, unit, producer-agnostic semantics, and a staleness bound;
> new setups add signals by declaration through this typed channel, never
> by teaching a consumer about a subsystem. (i) is therefore included.
> (2) Signals are keyed by SEAT INSTANCE, not role — operator's requirement
> verbatim: a conjecturer sitting in "multiple structurally asymmetric
> seats that may need throttling independently."
> (3) The allocation controller consumes ONLY the signal interface — pinned
> by an architecture test that fails if controller.py imports
> schools/rules/criticism internals.
> (4) Topology-independence is a compiled matrix test: every configuration
> class (solo, no-schools, judges-off, legacy-on...) compiles, the
> controller attaches, every policy-referenced signal has a producer.
> (5) A topology that cannot produce a signal compiles with a typed
> "allocation open-loop for signal X" notice — disclose, never die.
> (6) Layering: FROZEN = the change protocol (decisions typed+recorded,
> interface-only consumption, envelope bounds, allocation touches
> efficiency never evidence); VERSIONED = the registry and policy
> algorithm (policy-as-recorded-artifact, referee-reviewed); FREE =
> parameter values within envelopes. Ledger as a CLAUDE.md design law +
> INV- map doc with checks + two REC- recipes (add-signal,
> revise-allocation-policy); a future dedicated workflow only after two
> recorded recipe failures (authoring-skills E1 tripwire).

| # | Requirement | Source |
|---|---|---|
| R29 | The signal registry becomes a typed CONTRACT: every signal declares **name, unit, producer-agnostic semantics, staleness bound**. New setups add signals **by declaration through this channel**, never by teaching a consumer about a subsystem. The existing registry (`src/deepreason/signals.py`, candidate (i)) is included, not superseded. | Amendment 2 (1) |
| R30 | Signals are keyed by **seat instance, not role** — one conjecturer may sit in "multiple structurally asymmetric seats that may need throttling independently". | Amendment 2 (2) |
| R31 | The allocation controller consumes **only** the signal interface, pinned by an architecture test that FAILS if `controller.py` imports schools / rules / criticism internals. | Amendment 2 (3) |
| R32 | Topology-independence is a **compiled matrix test**: every configuration class (solo, no-schools, judges-off, legacy-on, …) compiles, the controller attaches, and every policy-referenced signal has a producer. | Amendment 2 (4) |
| R33 | A topology that cannot produce a signal **compiles**, carrying a typed `allocation open-loop for signal X` notice. **Disclose, never die.** | Amendment 2 (5) |
| R34 | Three layers, and they are not interchangeable. **FROZEN** = the change protocol (decisions typed and recorded, interface-only consumption, envelope bounds, allocation touches efficiency never evidence). **VERSIONED** = the registry and the policy algorithm (policy-as-recorded-artifact, referee-reviewed). **FREE** = parameter values within envelopes. | Amendment 2 (6) |
| R35 | Ledger as a **CLAUDE.md design law** + an **INV- map document with checks** + **two REC- recipes** (`add-signal`, `revise-allocation-policy`). **No dedicated workflow/skill** until two recipe failures are recorded (the `authoring-skills` E1 tripwire). | Amendment 2 (6) |
| R36 | Placement — its own rung, or folded into Rungs 1+4 — is **delegated to the drift table's preference**, and must be argued from it. | Amendment 2 preamble |

**Note.** D-7's option (iii) was "something not in the tree — paste it and it
gets a rung". The search recorded in `RECONCILIATION.md` §5 was therefore
correct and is left standing as the reason this design was not found: it was
never committed here.

### Amendment 3 — 2026-08-15, the attribution-priority directive

Operator, verbatim, on being told the premise channel has no producer:

> Also, the gap needs to be filled by upgrading the token optimisation system.
> This is going to require extensive testing. My guess is multiple different
> forms. Each prioritising attribution creation differently.
> There will need to be signals specifically designed to detect when particular
> forms are necessary. This will probably be routed through config with options
> for users to adjust sensitivity: a depth vs breadth sort of setup.
> Whatever the setup, this system needs dials that can function automatically,
> but still be adaptable for user needs.

| # | Requirement | Lands at |
|---|---|---|
| R37 | The producer gap is filled by the ALLOCATION layer, not by a fixed rule: what motivates a premise attribution is the token-optimisation system deciding it is worth spending on. | Rung 2 (hook) + Rung 1b-ii (policy) |
| R38 | **Multiple forms**, each prioritising attribution creation differently — not one policy. | post-evidence rung |
| R39 | **Signals designed to detect when a particular form is necessary** — declared through the signal contract (Rung 1b-i), never by teaching the controller about a subsystem. | Rung 1b-ii |
| R40 | Routed through **config**, with a user-adjustable **sensitivity** dial on a **depth vs breadth** axis. | Rung 1b-ii |
| R41 | The dials **function automatically by default** and remain **adaptable for user needs**. | Rung 1b-ii |
| R42 | **Extensive testing**: the forms are experiment arms, pre-registered and oracle-scored, not chosen by argument. | its own experiment program |

**Guardrails this directive inherits, stated so no rung can quietly drop them:**

- **Allocation touches EFFICIENCY, NEVER EVIDENCE** (the operator's own FROZEN
  layer). A policy may decide how often a critic is ASKED for a premise. It may
  never influence whether a premise stands, nor weight any label.
- **H1 is not reopened.** A run thrashing on a problem may redirect ATTENTION
  toward premise work; it may not mint a problem from that failure. Failure →
  attention is legal; failure → problem is what H1 deleted.
- **Formalism-optional applies.** No conjecture may be ranked, admitted or
  accepted differently for having, or lacking, an attribution.
- **All configurations compile.** A topology that cannot produce an
  attribution-priority signal compiles with the typed open-loop notice.

**Sequencing recommendation, recorded for the operator's decision:** ship the
channel and ONE deliberately dumb producer first (Rung 2), with the detection
signals declared alongside it, and only then tune multiple forms against live
data. The reverse order repeats the E28 pattern — a controller holding authority
over something that never happens — and the harness has two recorded instances
of exactly that (the controller that never steered; the reach trigger that never
fired).

---

### Amendment 4 — 2026-08-15, RIDER 2: the Formalization as companion authority

Operator, verbatim:

> RIDER 2 (append to REQUEST.md as an amendment): a companion authority is
> now on main — docs/POIETIC_CALCULUS_FORMALIZED.md, a formal
> reconstruction that repairs the Computable Calculus. Absorb into the
> drift table and ladder at the current rung boundary:
> (1) Rung 3 gains a REQUIRED invariant: frame-separation (§7) — the
> mention law alone does not secure wound persistence; the design enforces
> component-separation and its gate proves Theorem 7.3's precondition.
> (2) Rung 6 gains the third exit grade: premise-contested (§8.2) — do NOT
> adopt the FrameDecisive axiom; three grades, honestly.
> (3) New decision ND-2 for the operator's sheet: restored-premise
> resolution — recommend orphanhood-as-derived-view deactivating on
> reinstatement with the exit episode retained (consistent with D-3's
> derived-premises answer and C4), over a fourth revalidate resolution.
> (4) D-6's program-first succession adopts §3.5's Superseded criteria
> (recovery, rigidity, non-immunization) as the program-checkable forms;
> refuted and superseded are distinct derived relations (§1's split).
> (5) The A1-A10 axiom set (§17) becomes the backbone of the v2 INV- map
> document; each rung's gate names which axioms it proves or preserves.
> (6) The capture rung adopts §14's formulas (SC, ATH, Debt, RR, VAR, EGR)
> as the diagnostic definitions.

| # | Requirement | Lands |
|---|---|---|
| R43 | **Rung 3 gains a REQUIRED invariant: frame-separation (§7.2).** The mention law is necessary but NOT sufficient for wound persistence; the design enforces component-separation over the undirected `att ∪ dep` graph (mention edges excluded), and the rung's gate proves Theorem 7.3's precondition rather than assuming it. | Rung 3 |
| R44 | **Rung 6 gains the third exit grade: contestation (§8.2).** Three grades — fall (`R`), revocation (`SU`), contestation (`S`). The `FrameDecisive` axiom is NOT adopted, so "exactly two exits" is not claimed. | Rung 6 |
| R45 | **ND-2 joins the decision sheet**: restored-premise resolution. Recommendation — orphanhood as a derived view that DEACTIVATES on reinstatement with the exit episode retained, over a fourth `revalidate` resolution. | DECISIONS.md |
| R46 | **D-6's program-first succession adopts §3.5's `Superseded` criteria** — recovery, rigidity, non-immunization — as the program-checkable forms. **`Refuted` and `Superseded` are distinct derived relations** (§1's split): unilateral defeat vs comparative theory choice. | Rungs 5, 7 |
| R47 | **The A1–A10 axiom set (§17) is the backbone of the v2 `INV-` map document**, and **each rung's gate names which axioms it proves or preserves.** | Rung 4 owns the document; every rung names its axioms |
| R48 | **The capture rung adopts §14's formulas** — SC, ATH, Debt, RR, VAR, EGR — as the diagnostic definitions, including their windowing and canonical rounding. | Rung 8 |

### Amendment 5 — 2026-08-15, RIDER 3: v0.1 as foundational authority, and precedence

Operator, verbatim:

> RIDER 3 (append to REQUEST.md): the third authority is on main —
> docs/POIETIC_CALCULUS_v0.1.md, the foundational source. The
> Formalization's §1 integration-boundary table can now be verified
> against the source directly rather than taken on its word; where the
> three documents disagree, precedence for the v2 DESIGN is: Formalization
> (repairs) over Computable Calculus (design) over v0.1 (epistemology),
> with every departure from v0.1 rowed in RECONCILIATION.md and one line
> saying why. Two source anchors to honor: v0.1 §7's clean cut —
> bookkeeping implementable, genesis left open, "an engine that implements
> the bookkeeping faithfully and leaves genesis open IS an implementation
> of 𝔓" — is the program's charter sentence; and v0.1 Axiom 4.1 (Genesis
> Inertness: provenance confers nothing, neither warrant nor stigma) joins
> the A1-A10 basis in the INV- document.

| # | Requirement | Lands |
|---|---|---|
| R49 | **Precedence for the v2 DESIGN, in order: Formalization (repairs) > Computable Calculus (design) > v0.1 (epistemology).** Precedence governs DESIGN only; it is not a claim that a later document is more true. | program-wide |
| R50 | **Every departure from v0.1 is ROWED in RECONCILIATION.md with one line saying why.** | RECONCILIATION.md §2M |
| R51 | **v0.1 §7's clean cut is the program's CHARTER SENTENCE**: "an engine that implements the bookkeeping faithfully and leaves genesis open IS an implementation of 𝔓." No rung may treat the open genesis layer as an incompleteness to be closed. | program-wide |
| R52 | **v0.1 Axiom 4.1 (Genesis Inertness) joins the A1–A10 basis** in the `INV-` document: all appraisal predicates are invariant under permutation of provenance records — origin confers neither warrant nor stigma. | Rung 4's `INV-` document |
| R53 | **The Formalization's §1 integration-boundary table is now VERIFIABLE against v0.1 rather than taken on its word**, and the verification is recorded. | RECONCILIATION.md §2M |
