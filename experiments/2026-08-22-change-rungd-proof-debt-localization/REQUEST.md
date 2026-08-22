# Request: Rung D of the v2 calculus program — proof debt and Duhem localization

Captured: 2026-08-22, from the operator's single scheduling message (this
session's opening message, the whole of it).

Route: `dr-change-orchestrator`. This is a CHANGE tranche, not a defect
tranche: the authority is the operator's words plus the ladder section they
name, and nothing here is diagnosed from a failing record.

## Verbatim

> Change tranche: Rung D of the v2 calculus program — proof debt and
> Duhem localization. Route through dr-change-orchestrator; the
> workflow's own stops apply. This rung is OPERATOR-SCHEDULED (ladder:
> "a rung is specced by its own tranche") — the spec phase owns the
> design; the ladder gives only the outline.
>
> SETUP (fresh container): git fetch origin main && git checkout -B
> claude/calculus-rungd-debt-localization-k2vf7q origin/main;
> git merge-base --is-ancestor e1ea05e82 HEAD || re-fetch. pip install
> -e . --break-system-packages -q; pip install pytest pytest-xdist
> jsonschema --break-system-packages -q. Use `python -m pytest`, never
> bare pytest. Read CLAUDE.md in full; load dr-drive-harness,
> dr-explain-to-operator.
>
> AUTHORITY: experiments/2026-08-14-change-calculus-reconciliation-v2/
> LADDER.md "Rung D" section IN FULL (discharges drift rows E-1, E-2;
> added by Rider 4, R55/R56), plus the source docs it cites. The
> operator scheduled it 2026-08-22.
>
> WORK, per the ladder's outline:
> D1 PROOF DEBT (E-1): a receipt format — KERNEL_CHECK /
>    OPEN_CERTIFICATES / AXIOM_DEBT — travelling with derived
>    judgments, itemized and ATTACKABLE, with dependents invalidated
>    on recomputation rather than retroactively. The harness already
>    does this for one class (warrants carry validity nodes); the work
>    is generalization, and THE FIRST DESIGN QUESTION — which derived
>    judgments are in scope (labels? measures? render decisions?) —
>    is answered in SPEC.md with reasons, not assumed. Start narrow;
>    a small scope delivered beats a wide one specced.
> D2 DUHEM LOCALIZATION (E-2): bundle-level problematicity projects to
>    a member ONLY through a standing localization criticism — an
>    ordinary attackable artifact. Structurally the premise channel's
>    cousin: REUSE src/deepreason/premises.py's shape (attribution
>    mentions, never depends) rather than re-deriving it.
> HARD CONSTRAINT, the ladder's own warning: blame assignment is
> NEVER automatic — both rows exist because the automatic version is
> the tempting one. A bundle member is implicated only by a registered,
> attackable localization; no measure, no default, no cascade.
>
> GATE PROVES: receipts recompute from the log (derived, never
> stored); a localization is attackable and its defeat un-implicates
> the member (N1/Lemma 6.1 at this layer); no label moves from a
> receipt or localization alone (seats/evidence + readout inertness);
> MUTATION PROOF on the non-automatic constraint — wire an automatic
> projection in a scratch copy, watch the guard test go RED, restore,
> paste both runs. Axiom ledger: name what this rung PROVES and
> PRESERVES per LADDER.md §5b.
>
> FROZEN SURFACES: forecast none beyond Config knobs (each with its
> _versioned_source_config_data line). If the receipt design wants
> verification-format contact, request the grant in SPEC.md BEFORE
> code.
>
> SIZE: unestimated by the ladder — the diff-budget gate applies;
> ledger a ceiling at plan time and STOP if exceeded. If SPEC shows
> D1+D2 cannot fit one tranche, deliver D2 (smaller, shape exists)
> and park D1 with a ready prompt — say so rather than thinning both.
>
> KNOWN CURRENT STATE: gate baseline 0 failed (3829 at e1ea05e82);
> docs_verify 3 pre-existing shallow-clone failures; 5 MCP-thread
> flaky under -n 4; sweep retired. Parallel windows: a live run
> (experiments only) and a two-call seat-protocol tranche (llm/ +
> profiles) — your blast radius is warrants/validity, a new
> localization module, and map docs; if you find yourself editing
> llm/ or provider profiles, STOP and say so.
>
> GATE: ring while iterating; full gate at the boundary; docs_verify
> full. Map moves in the same commits. Commit and push every phase
> boundary (retry 2s/4s/8s/16s). Deliver R-by-R with pasted PROOF,
> closing with one line each: what now travels with a derived
> judgment, and what it takes to blame a bundle member.

### Cited authority, quoted in full (LADDER.md "Rung D")

> ### Rung D (unnumbered, unscheduled) — proof debt and Duhem localization
>
> **ADDED 2026-08-15 by RIDER 4 (R55, R56).** Deliberately unnumbered: it is not
> Rung 9, because the operator schedules it and a number would imply it follows
> Rung 8. It is written here rather than left in a wish-list so that the end of
> Rung 8 is a KNOWN state rather than an assumed-complete one.
>
> **Discharges:** drift rows E-1 and E-2.
>
> **Entry artifacts:** operator scheduling. No rung blocks on it and it blocks no
> rung.
>
> **Work, in outline only — a rung is specced by its own tranche, not here:**
> - **Proof debt (E-1):** a receipt format `KERNEL_CHECK / OPEN_CERTIFICATES /
>   AXIOM_DEBT` travelling with every derived judgment, itemized and attackable,
>   with dependents invalidated ON RECOMPUTATION rather than retroactively. The
>   harness already does this for one class — warrants carry validity nodes — so
>   the work is generalisation, and the first design question is which derived
>   judgments are in scope (labels? measures? render decisions?).
> - **Duhem localization (E-2):** bundle-level problematicity projects to a member
>   only through a standing localization criticism, which is an ordinary
>   attackable artifact. Structurally the premise channel's cousin: an attribution
>   says "π presupposes X", a localization says "the fault in this bundle lies with
>   member m". Reuse `premises.py`'s shape rather than re-deriving it.
>
> **What it must NOT do:** make blame assignment automatic in the name of
> convenience. Both rows exist because the automatic version is the tempting one.

### Cited authority, quoted in full (RECONCILIATION.md §2O rows E-1, E-2)

> | **E-1** | **Proof debt.** Every derived judgment carries an itemized, attackable manifest of what it rests on: kernel-checked steps, open certificates (attackable conjectures such as slack embeddings), named axioms. Attacking a manifest item invalidates dependents ON RECOMPUTATION, not retroactively. Receipt format `KERNEL_CHECK / OPEN_CERTIFICATES / AXIOM_DEBT` | A result's authority is exactly the authority of its premises and apparatus, and the bill of materials has to stay stapled to the package. The harness already does this for ONE class of judgment — warrants carry validity nodes — and proof debt is that same discipline generalised to every derived judgment | **deferred-essential**; its own future rung, scheduled by the operator. Not in the current seven |
> | **E-2** | **Duhem localization.** A problem whose target is a BUNDLE — theory + apparatus + interpretation — does not project blame onto any member without a STANDING LOCALIZATION CRITICISM. Blame assignment is adjudicated work | This is the H2 premise channel's cousin and it slots into the same machinery: an attribution says "π presupposes X"; a localization says "the fault in this bundle lies with member m". Both are ordinary attackable artifacts, and both exist to stop an automatic projection that would otherwise happen silently | **deferred-essential**; the same future rung |

### Cited authority, quoted in full (REQUEST.md R58 of the v2 program)

> | R58 | Attack-producing derived judgments wire their derivation manifest to the warrant's VALIDITY NODE as **evidence**, not dependence alone, so a manifest attack disables the attack **before pass one**. Pinned by the advice's own regression: target refuted → manifest item attacked → critic loses validity pre-grounded → target reinstated → replay identical. | adopt | Rung D (E-1, proof debt) |

## Requirements

| id | kind | the operator's words for this obligation |
|---|---|---|
| **R1** | process | "Route through dr-change-orchestrator; the workflow's own stops apply." |
| **R2** | process | "the spec phase owns the design; the ladder gives only the outline." |
| **R3** | process | "AUTHORITY: experiments/2026-08-14-change-calculus-reconciliation-v2/LADDER.md \"Rung D\" section IN FULL (discharges drift rows E-1, E-2; added by Rider 4, R55/R56), plus the source docs it cites." |
| **R4** | behavior | "D1 PROOF DEBT (E-1): a receipt format — KERNEL_CHECK / OPEN_CERTIFICATES / AXIOM_DEBT — travelling with derived judgments, itemized and ATTACKABLE, with dependents invalidated on recomputation rather than retroactively." |
| **R5** | artifact | "THE FIRST DESIGN QUESTION — which derived judgments are in scope (labels? measures? render decisions?) — is answered in SPEC.md with reasons, not assumed." |
| **R6** | process | "Start narrow; a small scope delivered beats a wide one specced." |
| **R7** | behavior | "D2 DUHEM LOCALIZATION (E-2): bundle-level problematicity projects to a member ONLY through a standing localization criticism — an ordinary attackable artifact." |
| **R8** | behavior | "REUSE src/deepreason/premises.py's shape (attribution mentions, never depends) rather than re-deriving it." |
| **R9** | behavior | "HARD CONSTRAINT, the ladder's own warning: blame assignment is NEVER automatic ... A bundle member is implicated only by a registered, attackable localization; no measure, no default, no cascade." |
| **R10** | behavior | "GATE PROVES: receipts recompute from the log (derived, never stored)" |
| **R11** | behavior | "a localization is attackable and its defeat un-implicates the member (N1/Lemma 6.1 at this layer)" |
| **R12** | behavior | "no label moves from a receipt or localization alone (seats/evidence + readout inertness)" |
| **R13** | process | "MUTATION PROOF on the non-automatic constraint — wire an automatic projection in a scratch copy, watch the guard test go RED, restore, paste both runs." |
| **R14** | artifact | "Axiom ledger: name what this rung PROVES and PRESERVES per LADDER.md §5b." |
| **R15** | process | "FROZEN SURFACES: forecast none beyond Config knobs (each with its _versioned_source_config_data line). If the receipt design wants verification-format contact, request the grant in SPEC.md BEFORE code." |
| **R16** | process | "SIZE: unestimated by the ladder — the diff-budget gate applies; ledger a ceiling at plan time and STOP if exceeded." |
| **R17** | process | "If SPEC shows D1+D2 cannot fit one tranche, deliver D2 (smaller, shape exists) and park D1 with a ready prompt — say so rather than thinning both." |
| **R18** | process | "GATE: ring while iterating; full gate at the boundary; docs_verify full. Map moves in the same commits. Commit and push every phase boundary (retry 2s/4s/8s/16s)." |
| **R19** | artifact | "Deliver R-by-R with pasted PROOF, closing with one line each: what now travels with a derived judgment, and what it takes to blame a bundle member." |

## Standing constraints

| id | verbatim | where stated |
|---|---|---|
| **C1** | "Use `python -m pytest`, never bare pytest." | SETUP paragraph |
| **C2** | "Read CLAUDE.md in full; load dr-drive-harness, dr-explain-to-operator." | SETUP paragraph |
| **C3** | "your blast radius is warrants/validity, a new localization module, and map docs; if you find yourself editing llm/ or provider profiles, STOP and say so." | KNOWN CURRENT STATE paragraph |
| **C4** | "KNOWN CURRENT STATE: gate baseline 0 failed (3829 at e1ea05e82); docs_verify 3 pre-existing shallow-clone failures; 5 MCP-thread flaky under -n 4; sweep retired." | KNOWN CURRENT STATE paragraph |
| **C5** | "Parallel windows: a live run (experiments only) and a two-call seat-protocol tranche (llm/ + profiles)" | KNOWN CURRENT STATE paragraph |
| **C6** | Branch: the session's designated development branch is `claude/calculus-rungd-debt-localization-6c3u9w`. The operator's SETUP line names `...-k2vf7q`; the session's own branch directive names `...-6c3u9w`, and the checkout that already exists and tracks origin is `-6c3u9w`. Recorded as a discrepancy, resolved in favour of the session directive; no work is lost either way. | SETUP paragraph vs session branch directive |

## Map preflight (recorded here so every later phase starts from the same map)

Resolved ids, read in the mandated order (`INV-frozen-surfaces.md` first, then
seams, then subsystems):

| id | why it is in scope |
|---|---|
| `DR-INV-frozen-surfaces` | read FIRST. Surfaces 1–5; R15 forecasts contact with none of them beyond `Config` |
| `DR-INV-axiom-basis` | R14's axiom ledger is written against it |
| `DR-SUB-calculus` | owns `premises.py`'s companion-subject half and the claim substrate; the localization channel is its cousin |
| `DR-CON-problem-layer-lifecycle` | owns `premises.py` — the shape R8 orders reused |
| `DR-CON-warrants-and-attacks` | owns `rules/warrants.py` — validity nodes, the ONE class that already carries proof debt (R4's "generalisation" base) |
| `DR-SUB-rules` | owns `rules/warrants.py` as a package |
| `DR-SUB-evaluation` | owns `measures/` — a candidate derived-judgment class for R5's scope question |
| `DR-SEAM-adjudication-x-rules` | receipts that reach a validity node touch the warrant → edge → label chain; R12 says no label may move |
| `DR-SEAM-scheduler-x-rules` | `premises.py`'s consumers live here; a localization channel has the same consumer shape |

**Map gap, recorded as a finding rather than a blocker:** there is no
`SEAM-calculus-x-*` document for the calculus package's own seams —
`SUB-calculus.md` lists them under `Seams-undocumented:`. If this tranche adds a
module whose seam is load-bearing, creating the missing document is part of the
tranche (`dr-drive-harness` §4.5).

## Open questions (for dr-spec-change — NOT answered here)

- **Q1** — R5's own question, verbatim: which derived judgments are in scope for
  a receipt? The named candidates are labels, measures, render decisions.
  Render decisions belong to Rung 6, which has NOT been delivered (the ladder's
  execution table shows Rungs 5–8 outstanding); that is evidence for the SPEC,
  not an answer written here.
- **Q2** — does a receipt attach to the JUDGMENT (recomputed each call) or to an
  artifact that carries it? R4 says "travelling with" and R10 says "derived,
  never stored"; the reconciliation of those two words is design work.
- **Q3** — what is a BUNDLE, concretely, in this codebase? E-2 says "theory +
  apparatus + interpretation". Nothing in the tree is named a bundle today, so
  the spec must say what plays that role and how a bundle is registered.
- **Q4** — does R58 (manifest → validity node as EVIDENCE, so a manifest attack
  disables the attack pre-grounded) land in this tranche, or is it a separate
  scope? It is ledgered "Rung D (E-1)" but is not in the operator's own D1 text.
- **Q5** — R16's diff-budget ceiling: what number? The ladder gives no estimate
  for Rung D, so the ceiling is this tranche's to set at plan time.
- **Q6** — does R12's "no label moves" need a NEW guard, or is it already
  structurally true because a receipt/localization is an ordinary artifact with
  no rule of its own? Cheapest authority is the code, so the spec checks rather
  than assumes.

## Amendments

(append-only; later operator messages land here)
