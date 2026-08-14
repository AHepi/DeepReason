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
