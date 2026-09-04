# Request: four evidence states over the record, and a per-cycle declaration that criticism ran in full

Captured: 2026-09-04 from the executor-window prompt (sole operator-authority
message of this session), which itself carries the operator's decision of
2026-09-04 verbatim and points at `docs/HANDOVER_MONITOR_2026-08-29.md`
section "Queued 2026-09-04", item 1.

Base: `main` at `33f92e88c7` (branch `claude/evidence-states-conjecture-yb1aqd`).
Offline tranche; no API key requested or used.

## Verbatim

### Operator's decision (2026-09-04), quoted in the window prompt

> "keep a note. Those will be next."

Context of that decision, from `docs/HANDOVER_MONITOR_2026-08-29.md:418-436`
(the note the operator asked to be kept; monitor's assessment, accepted):

> ## Queued 2026-09-04 — adoptions from the operator's CR-2.0 revB document
>
> The operator uploaded "CR-2.0 proposal — Creative Revision Event Semantics,
> Revision B" (a theory of creative processes; not a harness design) and asked
> whether it adds anything worth adopting. Monitor's assessment, accepted by the
> operator ("keep a note. Those will be next"): most of it is already how the
> harness works (append-only facts with re-derived statuses; a stop that never
> bears on content; hv relative to a declared variation family; equivalence
> levels; conjecture-before-criticism; deletion/mutation tests). Three items
> are queued, in this order:
>
> 1. **Four evidence states, with a completeness declaration.** OPEN /
>    SUPPORTED / REFUTED / CONTESTED as a DERIVED reading over the record, so an
>    admitted conjecture nobody criticised is not read as a survivor; absence of
>    criticism counts against a conjecture only when the cycle declares
>    criticism ran in full (not budget-cut). Feeds the progress-over-baseline
>    measure directly. Price: a reader (no frozen contact) plus one typed
>    per-cycle declaration from the scheduler (may need a record entry —
>    surface-2 grant like 2026-09-04's).

### The executor window prompt (this tranche's authority), verbatim

> EXECUTOR WINDOW — CHANGE TRANCHE: four evidence states over the record,
> and a per-cycle declaration that criticism ran in full
>
> Read CLAUDE.md IN FULL, especially the 2026-09-03 progress-over-baseline
> law and the judge law. Load dr-change-orchestrator, dr-drive-harness,
> dr-ask-the-right-question and pinker-write-for-readers. Start at
> dr-capture-request with THIS prompt as authority. Base on main at or
> after 33f92e88c7. Tranche directory:
> experiments/2026-09-04-change-evidence-states/. Offline; no key.
>
> THE OPERATOR'S DECISION, verbatim (2026-09-04), accepting the monitor's
> assessment of an uploaded design document: "keep a note. Those will be
> next." The note is docs/HANDOVER_MONITOR_2026-08-29.md, section "Queued
> 2026-09-04", item 1. Read it, then this.
>
> THE PROBLEM, from the record: an admitted conjecture nobody has
> criticised and one that survived a warranted attack both read as
> "accepted" today. The success criterion is "survivors harder to vary,
> bolder conjectures that survived criticism", so the record must be able
> to tell a survivor from an untested one cheaply. The blind-critic
> experiment (experiments/2026-09-04-experiment-blind-critic/RESULTS.md)
> adds a constraint: the critic attacks everything it is shown, so "was
> criticised" must mean a criticism whose attack was WARRANTED or whose
> defended trial ran, never merely that a critic call happened.
>
> WHAT TO BUILD:
>  1. A DERIVED READING, not a new status: for every admitted artifact at
>     any point in the record, one of OPEN (no warranted attack and no
>     completed trial), SUPPORTED (survived at least one warranted attack
>     or defended trial), REFUTED (as today), CONTESTED (evidence both
>     ways — an ensemble-split trial, or a sustained attack alongside a
>     failed one). Computed from attack edges, warrants, trial outcomes
>     and status labels already in the record. It changes NO admission,
>     rank, immunity or refutation (S11.3-style architecture test: RED if
>     scheduler/, adjudication/ or rules/ read it).
>  2. THE COMPLETENESS RULE: the absence of any warranted attack counts
>     toward OPEN only; it may count AGAINST an artifact (as "criticised
>     and nothing landed" → SUPPORTED) only when the cycle carries a typed
>     declaration that criticism dispatch ran in full — every planned
>     criticism call was made — rather than cut by budget or a retired
>     seat. Design the declaration FIRST in SPEC.md: prefer the existing
>     notice/measure channel (`record_measure`, the road the dead-seat
>     tranche took to avoid a new record kind); a NEW record object kind
>     is a surface-2 contact (harness.py) and a STOP for a grant, priced
>     the way experiments/2026-09-03-change-conjecturer-pluggable-
>     interface/ REQUEST.md §1c did it.
>  3. SURFACES: the reading appears in `deepreason results` and in
>     `deepreason stop-report` as counts per state per cycle, and as a
>     per-artifact column in the frontier listing; typed absence where the
>     record predates the declaration.
>  4. THE BASELINE HOOK: `analyse_form_arms.py` (the brief-variation
>     experiment's instrument) and the diversity instrument gain a
>     `--survivors-only` switch that restricts to SUPPORTED artifacts, so
>     the progress law's "survivors" can be compared against B0 on
>     survivors alone. No default behaviour of either instrument changes.
>
> FROZEN SURFACES: forecast NO CONTACT for the reader; run
> tools/blast_radius.py over the planned targets before code and paste
> the verdict in SPEC.md. Historical roots are never edited; the reading
> over a root without declarations yields OPEN/REFUTED only and says why.
>
> PROOF: mutation-proven tests for each state on fixtures built from
> committed roots (P-A2 epoch 4's frontier has sustained attacks;
> the blind-critic roots have 480 attacks with zero warrants — the
> canonical OPEN case); the architecture test; the completeness rule
> proven RED when absence is allowed to count without the declaration.
> Full gate alone, 0 failed; docs_verify FULL; map moves in the same
> commit (a new CON-evidence-states.md with checks that can fail).
> Known-not-yours docs_verify rows: SEAM-llm-x-rules.md:54,
> INV-frozen-surfaces.md:181 and :736, CON-run-identity.md:211/213/215/298.
>
> FINAL MESSAGE: plain words; first sentence says whether the record can
> now tell a survivor from an untested conjecture and whether the gate is
> green; then how many of the committed frontier artifacts turn out OPEN
> versus SUPPORTED, because that number is the point. One closing analogy.

## Requirements

R1 (behavior): "A DERIVED READING, not a new status: for every admitted
artifact at any point in the record, one of OPEN (no warranted attack and no
completed trial), SUPPORTED (survived at least one warranted attack or
defended trial), REFUTED (as today), CONTESTED (evidence both ways — an
ensemble-split trial, or a sustained attack alongside a failed one)."

R2 (behavior): "Computed from attack edges, warrants, trial outcomes and
status labels already in the record."

R3 (behavior): "It changes NO admission, rank, immunity or refutation
(S11.3-style architecture test: RED if scheduler/, adjudication/ or rules/
read it)."

R4 (behavior): "THE COMPLETENESS RULE: the absence of any warranted attack
counts toward OPEN only; it may count AGAINST an artifact (as 'criticised and
nothing landed' → SUPPORTED) only when the cycle carries a typed declaration
that criticism dispatch ran in full — every planned criticism call was made —
rather than cut by budget or a retired seat."

R5 (process): "Design the declaration FIRST in SPEC.md: prefer the existing
notice/measure channel (`record_measure`, the road the dead-seat tranche took
to avoid a new record kind); a NEW record object kind is a surface-2 contact
(harness.py) and a STOP for a grant, priced the way
experiments/2026-09-03-change-conjecturer-pluggable-interface/ REQUEST.md §1c
did it."

R6 (behavior): "SURFACES: the reading appears in `deepreason results` and in
`deepreason stop-report` as counts per state per cycle, and as a per-artifact
column in the frontier listing; typed absence where the record predates the
declaration."

R7 (behavior): "THE BASELINE HOOK: `analyse_form_arms.py` (the brief-variation
experiment's instrument) and the diversity instrument gain a
`--survivors-only` switch that restricts to SUPPORTED artifacts, so the
progress law's 'survivors' can be compared against B0 on survivors alone."

R8 (behavior): "No default behaviour of either instrument changes."

R9 (process): "FROZEN SURFACES: forecast NO CONTACT for the reader; run
tools/blast_radius.py over the planned targets before code and paste the
verdict in SPEC.md."

R10 (behavior): "Historical roots are never edited; the reading over a root
without declarations yields OPEN/REFUTED only and says why."

R11 (process): "PROOF: mutation-proven tests for each state on fixtures built
from committed roots (P-A2 epoch 4's frontier has sustained attacks; the
blind-critic roots have 480 attacks with zero warrants — the canonical OPEN
case); the architecture test; the completeness rule proven RED when absence is
allowed to count without the declaration."

R12 (process): "Full gate alone, 0 failed; docs_verify FULL; map moves in the
same commit (a new CON-evidence-states.md with checks that can fail)."

R13 (process): "FINAL MESSAGE: plain words; first sentence says whether the
record can now tell a survivor from an untested conjecture and whether the
gate is green; then how many of the committed frontier artifacts turn out OPEN
versus SUPPORTED, because that number is the point. One closing analogy."

## Standing constraints

C1: "Read CLAUDE.md IN FULL, especially the 2026-09-03 progress-over-baseline
law and the judge law." — window prompt, opening. The progress law makes
"survivors harder to vary, bolder conjectures that survived criticism" the
acceptance criterion this reading serves.

C2: "The blind-critic experiment ... adds a constraint: the critic attacks
everything it is shown, so 'was criticised' must mean a criticism whose attack
was WARRANTED or whose defended trial ran, never merely that a critic call
happened." — window prompt, THE PROBLEM.

C3: "Base on main at or after 33f92e88c7. Tranche directory:
experiments/2026-09-04-change-evidence-states/. Offline; no key." — window
prompt, opening.

C4: "Known-not-yours docs_verify rows: SEAM-llm-x-rules.md:54,
INV-frozen-surfaces.md:181 and :736, CON-run-identity.md:211/213/215/298." —
window prompt, PROOF.

C5: One tranche, one goal (CLAUDE.md): a defect found mid-change is PARKED,
not fixed.

## Map ids (resolved at capture; recorded per the map-preflight rule)

Resolved from `docs/map/INDEX.md`. Confirmed and extended in SPEC.md after the
seam read.

- `DR-INV-frozen-surfaces` — read first, always. The reader must forecast NO
  CONTACT (R9).
- `DR-CON-warrants-and-attacks` — "the chain: no warrant, no edge, no
  REFUTED". The authority for what a WARRANTED attack is (R1, C2).
- `DR-SUB-adjudication` — "warrants → attack edges → status labels". The
  inputs the reading consumes (R2), and one of the three packages the
  architecture test must keep from reading it (R3).
- `DR-SUB-rules` — the epistemic moves; second forbidden reader (R3).
- `DR-SUB-scheduler` — cycles and dispatch; third forbidden reader (R3), and
  the producer of the per-cycle completeness declaration (R4).
- `DR-CON-authority` — "who may change a Status": the reading changes none.
- `DR-CON-criticism-source` — the socket that attacks a target; the source of
  criticism records the reading reads.
- `DR-SUB-evaluation` — "programs, oracles, measures, informal trials": the
  home of trial outcomes (R1) and of `record_measure` (R5).
- `DR-SUB-verification` — frozen; the reading must not touch replay formats.
- `DR-SUB-harness` — frozen surface 2; a new record object kind would contact
  it (R5) and is a STOP.

## Open questions (for dr-spec-change)

Q1: Which existing typed facts constitute a "warranted attack", a "completed
trial", a "defended trial", a "sustained attack" and an "ensemble-split
trial"? R1/R2 name them; the record's own vocabulary must be mapped to each
before any state can be computed.

Q2: Can the per-cycle completeness declaration ride `record_measure` (R5's
preference) without a new record object kind, and what exactly does "every
planned criticism call was made" mean in terms the scheduler can observe
(planned count vs dispatched count vs a budget/seat cut)?

Q3: What is the "diversity instrument" (R7) — which file — and does
`analyse_form_arms.py` exist under the brief-variation experiment?

Q4: What does "typed absence" (R6) print as, and where does the frontier
listing live in `deepreason results` / `stop-report`?

Q5: Does the reading belong in a new module, and which package may own it so
that the architecture test of R3 is expressible (a package none of scheduler/,
adjudication/, rules/ imports)?

## Amendments

(append-only; later operator messages land here)
