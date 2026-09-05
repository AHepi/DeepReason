# Request: the mini isolation programme — mini alone, relaxed forms, a commitment-generating artifact, a pluggable flow
Captured: 2026-09-05, from the executor-window instruction carrying the
operator's message of the same date. Phase: `dr-capture-request`.

This file QUOTES. It does not interpret. Interpretation happens in
`SPEC.md`, where it is visible and reviewable.

## Map preflight (recorded here so every later phase starts from the same map)

Resolved from `docs/map/INDEX.md` before any design:

| id | why it is in scope |
|---|---|
| `DR-INV-frozen-surfaces` | read FIRST, always; the forecast for R2 lives against it |
| `DR-INV-seat-section-plugins` | the seat-shell: layout + form + wording as registered configuration (R7) |
| `DR-INV-seat-section-sources` | where a brief section's CONTENT comes from (R5, R6) |
| `DR-REC-add-a-section-plugin` | the recipe R7's exposure changes must follow |
| `DR-INV-render-layout` | where a rendered brief puts what it carries (R2, R6) |
| `DR-CON-packs-and-token-economy` | section allocation and budgets (R2's length question) |
| `DR-CON-conjecture-source` | the socket that proposes candidate artifacts (R4, R7) |
| `DR-CON-criticism-source` | the socket that attacks or scrutinises a target (R5, R7) |
| `DR-CON-conjecture-kinds` | the R-g guardrail: shape buys nothing (R2, R4) |
| `DR-SUB-verification` | `verify_root`, which decides whether a mini root stays replay-valid |
| `DR-SUB-manifest` | `RunManifest` and qualification, which R1/R11 must NOT activate |
| `DR-SEAM-packs-and-token-economy-x-rules` | the seam the brief crosses to reach a seat |

**A gap, recorded as a finding rather than a blocker (`dr-drive-harness` §4):**
the map has **no document for MiniReason at all**. `mini/minireason/` is under
no subsystem document's `Owns:` header, and no `SUB-`, `CON-` or `SEAM-`
document names it. `docs/map/INDEX.md`'s coverage section says so in general
terms ("`docs/map` describes `src/deepreason/`"), which is honest but leaves
this programme's whole subject unmapped. Creating `SUB-minireason.md` and the
one seam this work crosses is therefore part of the programme, not a
side-errand — see `CHECKLIST.md`.

## Verbatim

> the episodes and artifact form adjustments need to be tested again. For
> now, the current default conjecture form needs stored but not deleted.
> One more history conjecture experiment. But before that:
>
> Proposal set up that is not permanent: First, mini needs to be tested in
> isolation. Second, mini artifact forms need to not limit prose length at
> all. Third, it needs to run its full conjecture/criticism cycles with
> commitments disabled. Fourth, within mini, there needs to be a new kind
> of artifact that generates commitments on conjectures, but does not
> force a strict format. Fifth, critics see the conjecture artifact, not
> the proposed commitments. Sixth, within mini, conjecturers see
> everything generated so far and so do commitment artifacts. Seventh, all
> three seats need the same pluggable interface with relaxed forms and
> have the information they say calibrated on the fly and modifiable by
> the controller. Don't change the controller just yet, the controller
> steps in only when I can see how best to manage input output flows in
> mini properly.
> The mini flow also needs to be adjustable in a pluggable way and add new
> artifact types on the fly if I can see it might help. The last part is
> to test this new config in isolation without the larger harness
> activated. It's starting input should be standard.

## Requirements

Numbered R1-R12 for the twelve numbered obligations, per the window's own
instruction. The three preamble sentences are numbered separately because
they order the programme rather than sit inside it.

### The programme

R1 (behavior): "mini needs to be tested in isolation"
R2 (behavior): "mini artifact forms need to not limit prose length at all"
R3 (behavior): "it needs to run its full conjecture/criticism cycles with
    commitments disabled"
R4 (behavior): "within mini, there needs to be a new kind of artifact that
    generates commitments on conjectures, but does not force a strict format"
R5 (behavior): "critics see the conjecture artifact, not the proposed
    commitments"
R6 (behavior): "within mini, conjecturers see everything generated so far and
    so do commitment artifacts"
R7 (behavior): "all three seats need the same pluggable interface with relaxed
    forms and have the information they say calibrated on the fly and
    modifiable by the controller"
R8 (process): "Don't change the controller just yet, the controller steps in
    only when I can see how best to manage input output flows in mini
    properly"
R9 (behavior): "The mini flow also needs to be adjustable in a pluggable way"
R10 (behavior): "and add new artifact types on the fly if I can see it might
    help"
R11 (behavior): "The last part is to test this new config in isolation without
    the larger harness activated"
R12 (behavior): "It's starting input should be standard."

### The three preamble sentences (they ORDER the programme)

R-again (process, DEFERRED): "the episodes and artifact form adjustments need
    to be tested again". The window places episodes OUT OF SCOPE ("episodes
    (R-again, later)"). The artifact-form half is what R2/R4/R7 do here.
R-stored (behavior, BINDING HERE): "For now, the current default conjecture
    form needs stored but not deleted." Also ledgered as a standing operator
    ruling in CLAUDE.md (2026-09-05).
R-history (process, DEFERRED): "One more history conjecture experiment. But
    before that:" — the "but before that" makes this programme's ordering
    explicit: the history experiment follows it. Out of scope here.

## Standing constraints

C1: "Proposal set up that is not permanent" — verbatim, opening the numbered
    list. The window's operational reading, which SPEC.md must honour: every
    piece ships behind a registered id or a per-run switch, defaults OFF for
    the full harness, and can be turned off without removal.
C2: "Don't change the controller just yet" — verbatim (also R8). The
    controller hook is DEFINED, not implemented.
C3 (window): "This window ends at SPEC.md + CHECKLIST.md and STOPS for the
    operator's approval. No production code in this window."
C4 (window): "Nothing here alters the full harness's default behaviour; the
    goldens for both existing seats stay byte-identical."
C5 (window): "FROZEN SURFACES: forecast per D2. Any contact is disposed in
    SPEC.md with blast_radius rows before code, and is a STOP for a grant."
C6 (CLAUDE.md, 2026-09-03): success is progress over the no-harness baseline;
    correctness and completeness are not the goal. Binds D8.
C7 (CLAUDE.md, 2026-09-03): a seat is a shell — its input (brief) and output
    (form) define it, both registered versioned configuration. Binds R7.
C8 (CLAUDE.md, 2026-08-26): modularity is enforced, and customisation is easy
    — every varying behaviour reachable as configuration or a registered
    artifact, with an architecture test that goes red on a bypass. Binds
    R7, R9, R10.
C9 (CLAUDE.md, 2026-08-08): formalism is an option, never an obligation.
    Nothing may penalise a conjecture for being informal. Binds R2 and R4
    directly — R4's artifact "does not force a strict format".
C10 (CLAUDE.md, 2026-08-12 / 2026-08-28): all configurations are allowed;
    seat configuration is ungated; a gate switched off produces a typed
    WARNING, never a refusal and never silence. Binds R3.

## Open questions (for dr-spec-change; NOT answered here)

Q1: R3 says "commitments disabled". Mini's canonical `Commitment` objects are
    compiled from each candidate's own `forbidden` cases AND from a mandatory
    `skeleton-wf` well-formedness commitment. Does "commitments disabled" mean
    both, or only the model-authored forbidden cases?
Q2: R2 says "not limit prose length at all". Which limit — the required output
    SHAPE (the JSON skeleton), a character/token cap, or the truncation of
    what a seat is SHOWN?
Q3: R7 says "all three seats". Mini has ONE seat today (conjecturer). Are the
    three conjecturer, critic, commitment?
Q4: R6 says conjecturers "see everything generated so far". Everything in the
    run, or everything for the problem under work?
Q5: R12's "standard" starting input — the same question file and criteria the
    full harness takes, or `deepreason reason --shallow`'s single question
    string?
Q6: R1/R11 — what exactly does "the larger harness" exclude, by module?
Q7: R10's "add new artifact types on the fly" — at run configuration time, or
    while a run is in flight?

## Amendments

(append-only; later operator messages land here as R13... or "R2a supersedes
R2", each with its verbatim quote)

### Amendment 1 (2026-09-05) — SPEC.md approved; Q-A answered; E2 and E3 forbidden

Captured from the executor-window instruction of 2026-09-05 carrying the
operator's message of the same date, which also ledgered the ruling in
CLAUDE.md as a standing law.

**Approval.** SPEC.md is APPROVED AS WRITTEN (2026-09-05). CHECKLIST.md's
blocker is lifted and step 1 may run.

**The operator's words, verbatim, answering Q-A:**

> within mini, criticism can't overturn anything. The point is content
> generation for now. Then testing on the full harness.

**R13 (behavior, binding): "within mini, criticism can't overturn
anything."** In the mini flow a criticism is written to the record and shown
to whichever seats the layouts allow, and it changes NO status. This is
Q-A's road E1 and only E1.

**R14 (scope, binding): "The point is content generation for now. Then
testing on the full harness."** Mini's job in this programme is to GENERATE
content — conjectures, criticisms, commitment proposals. What that content
is worth is decided later by running it through the full harness, whose
authority layer this programme does not touch.

**What R13/R14 forbid, stated so it is not rediscovered.** Q-A road E2 (a
critic that may eliminate behind a per-run switch) is NOT built — not behind
a switch, not off by default, not at all. Q-A road E3 (elimination arriving
with the commitment artifact) is NOT built here either: the T4 commitment
artifact PROPOSES commitments and eliminates nothing. SPEC.md's earlier
recommendation ("E1 as the isolation flow's default, with E2 built and
switched OFF, and E3 as the flow that follows") is SUPERSEDED by the
operator's own answer; SPEC.md §Q-A records it as answered rather than
deleting it.

**Window scope (this executor window only):** T0, T1, T2. Each sub-tranche
is its own delivery — `dr-validate-change` then `dr-deliver-change` before
the next starts. T3-T7 go to later windows.
