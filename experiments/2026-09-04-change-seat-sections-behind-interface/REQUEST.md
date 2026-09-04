# Request: "the nine brief sections still computed inside the admission code
# move behind the seat-section interface"

Captured: 2026-09-04, from the executor window's opening message (the single
operator message that started this tranche; it was delivered twice, byte-for-
byte identical — one instruction, not two, and nothing is inferred from the
repetition).

Phase: `dr-capture-request`. Authority for every later artifact in this
directory is this file. Nothing here is interpreted; interpretation happens
in `SPEC.md`, where it can be reviewed.

---

## Verbatim

> EXECUTOR WINDOW — CHANGE TRANCHE: the nine brief sections still computed
> inside the admission code move behind the seat-section interface
>
> Read CLAUDE.md IN FULL, especially the seat-is-a-shell law and its stated
> PURPOSE ("slowly separate the authority layer"). Load
> dr-change-orchestrator, dr-drive-harness, dr-ask-the-right-question and
> pinker-write-for-readers. Start at dr-capture-request with THIS prompt as
> authority. Base on main at or after 0f6bf2c854. Tranche directory:
> experiments/2026-09-04-change-seat-sections-behind-interface/. Offline;
> no key.
>
> THE STARTING POINT, read in full first:
> experiments/2026-09-03-change-conjecturer-pluggable-interface/ (SPEC.md
> assumption A6, FEASIBILITY.md §2, DELIVERY.md, PARKED.md P4, P5),
> docs/map/SEAM-packs-and-token-economy-x-rules.md (written by that build;
> it names the nine sections computed in rules/conj.py rather than by the
> renderer, the three appended after allocation, and the AllocatedPack
> rule), docs/map/INV-seat-section-plugins.md, REC-add-a-section-plugin.md.
>
> THE GOAL, one sentence: after this tranche, no section a seat is shown is
> COMPUTED inside rules/ — the generation side assembles every section
> through the registered interface, and rules/ hands over only the state
> the interface may read.
>
> THE CONSTRAINT THAT SHAPES THE DESIGN: the interface forbids a plugin
> from calling the harness or writing the log (SPEC S1.2). The nine
> sections need dossier receipts, fence seqs and work orders — the record
> side. So the design is a registered SOURCE layer beside the plugins:
> a section SOURCE computes a value from read access to the state and the
> record, is registered and versioned like a plugin, writes nothing, and
> its output is what the plugin formats. Decide, in SPEC.md, whether a
> source may READ the log (it may never append) and prove the "never
> appends" clause with an architecture test that goes red on a planted
> write.
>
> BYTE-IDENTICAL DEFAULT, again: both seats' goldens (tests/fixtures/
> conj_pack_legacy_v0, crit_pack_legacy_v0) must pass untouched at the
> end. If they cannot, the refactor is wrong; STOP; never edit a fixture.
>
> THE PURPOSE TEST (the law's "enforced" clause): after the move, the
> existing shape-buys-nothing test still passes, and a NEW test proves
> rules/conj.py no longer imports or constructs any pack section type.
> Mutation-prove both.
>
> SCOPE: the nine A6 sections and the three appended after allocation.
> PARKED P4 (batch critic renderer) and P5 (four seats with hardcoded
> briefs) stay parked unless the same source layer makes one of them a
> one-step registration — if so, say so in PARKED.md with the price, do
> not do it here.
>
> FROZEN SURFACES: forecast NO CONTACT; run tools/blast_radius.py over the
> planned targets before code and paste the verdict in SPEC.md. Reading
> the record is not a contact; a new record object kind IS (surface 2)
> and is a STOP for a grant — the previous build parked exactly that.
>
> Gate at the boundary (full gate alone, 0 failed, nothing weakened);
> docs_verify FULL; map moves in the same commit. Known-not-yours
> docs_verify rows: SEAM-llm-x-rules.md:54, INV-frozen-surfaces.md:181
> and :736, CON-run-identity.md:211/213/215/298.
>
> FINAL MESSAGE: plain words. First sentence: are both defaults still
> byte-identical and is the gate green. Then what now lives outside the
> admission code and what still does not. One closing analogy.

---

## Requirements

R1 (behavior): "the nine brief sections still computed inside the admission
code move behind the seat-section interface" — the headline obligation.

R2 (behavior): "after this tranche, no section a seat is shown is COMPUTED
inside rules/ — the generation side assembles every section through the
registered interface, and rules/ hands over only the state the interface may
read."

R3 (behavior): "the design is a registered SOURCE layer beside the plugins: a
section SOURCE computes a value from read access to the state and the record,
is registered and versioned like a plugin, writes nothing, and its output is
what the plugin formats."

R4 (artifact): "Decide, in SPEC.md, whether a source may READ the log (it may
never append)".

R5 (behavior/artifact): "prove the 'never appends' clause with an architecture
test that goes red on a planted write."

R6 (behavior): "both seats' goldens (tests/fixtures/conj_pack_legacy_v0,
crit_pack_legacy_v0) must pass untouched at the end. If they cannot, the
refactor is wrong; STOP; never edit a fixture."

R7 (behavior): "the existing shape-buys-nothing test still passes".

R8 (behavior/artifact): "a NEW test proves rules/conj.py no longer imports or
constructs any pack section type."

R9 (process): "Mutation-prove both." — R7's test and R8's test.

R10 (behavior): "SCOPE: the nine A6 sections and the three appended after
allocation."

R11 (process): "PARKED P4 (batch critic renderer) and P5 (four seats with
hardcoded briefs) stay parked unless the same source layer makes one of them a
one-step registration — if so, say so in PARKED.md with the price, do not do
it here."

R12 (process/artifact): "forecast NO CONTACT; run tools/blast_radius.py over
the planned targets before code and paste the verdict in SPEC.md."

R13 (process): "Reading the record is not a contact; a new record object kind
IS (surface 2) and is a STOP for a grant — the previous build parked exactly
that."

R14 (process): "Gate at the boundary (full gate alone, 0 failed, nothing
weakened); docs_verify FULL; map moves in the same commit."

R15 (artifact): "FINAL MESSAGE: plain words. First sentence: are both defaults
still byte-identical and is the gate green. Then what now lives outside the
admission code and what still does not. One closing analogy."

R16 (process): "Read CLAUDE.md IN FULL, especially the seat-is-a-shell law and
its stated PURPOSE ('slowly separate the authority layer')." plus "Load
dr-change-orchestrator, dr-drive-harness, dr-ask-the-right-question and
pinker-write-for-readers."

R17 (process): "THE STARTING POINT, read in full first:
experiments/2026-09-03-change-conjecturer-pluggable-interface/ (SPEC.md
assumption A6, FEASIBILITY.md §2, DELIVERY.md, PARKED.md P4, P5),
docs/map/SEAM-packs-and-token-economy-x-rules.md ...,
docs/map/INV-seat-section-plugins.md, REC-add-a-section-plugin.md."

## Standing constraints

C1: "Base on main at or after 0f6bf2c854." — the window.
C2: "Tranche directory:
experiments/2026-09-04-change-seat-sections-behind-interface/." — the window.
C3: "Offline; no key." — the window. No live run, no provider call.
C4: "Known-not-yours docs_verify rows: SEAM-llm-x-rules.md:54,
INV-frozen-surfaces.md:181 and :736, CON-run-identity.md:211/213/215/298." —
the window. These are pre-existing failures, not this tranche's.
C5: "never edit a fixture" — the window, inside R6.
C6: "a new record object kind IS (surface 2) and is a STOP for a grant" — the
window, inside R13.

## Open questions (for dr-spec-change)

Q1: R10 says "the three appended after allocation", while the covering seam
document names FOUR post-allocation re-wraps and the prior tranche's
FEASIBILITY §2 says "appends three more AFTER allocation" above a table of
four rows. Which of the four is outside the named three, and what happens to
it?

Q2: R2 says "no section a seat is shown is COMPUTED inside rules/", which
covers `rules/crit.py` as well; R10's SCOPE names only the conjecturer's nine
plus three. Does the critic's four move in this tranche?

Q3: R4 asks for a decision on whether a source may READ the log. What
argument decides it, and what enforces the "never appends" half at runtime as
well as in a test?

Q4: One of the nine — the frozen-evidence context — is computed by code that
also WRITES a receipt to the record on one path
(`commit_dossier_pack_receipt`, `rules/conj.py`). If the computation moves and
the write may not, where does the split fall?

## Amendments

(append-only; later operator messages land here as R18... or
"R2a supersedes R2", each with its verbatim quote)
