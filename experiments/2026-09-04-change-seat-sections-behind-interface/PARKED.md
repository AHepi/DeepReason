# PARKED — found while moving the nine, not fixed here

Phase: `dr-execute-step` / `dr-validate-change`. Date: 2026-09-04.
Authority for parking rather than fixing: `REQUEST.md` R11, and the change
workflow's scope contract — a defect or improvement found mid-change is
PARKED, never absorbed.

Each entry is written for its future runner: one line of WHAT, then a
ready-to-send prompt.

---

## P1 — the critic's four contexts are still computed in `rules/crit.py`

**What.** R2's sentence is "no section a seat is shown is COMPUTED inside
`rules/`". It is now true for the conjecturer and false for the critic:
`rules/crit.py` still computes `premise_invitation`, `citable_evidence_context`,
`frame_slice_context` and `frame_crisis_context` and passes them to
`render_crit_pack` one by one.

**Why it is parked and not done.** `REQUEST.md` R10 scopes this tranche to "the
nine A6 sections and the three appended after allocation" — the conjecturer's.
The price of doing the critic here is not the three shared sources (this tranche
registers them already) but a piece of machinery this tranche deliberately did
not build: the critic's TWO `render_crit_pack` call sites supply DIFFERENT
SUBSETS. The atomic-decomposition fallback passes the two frame halves and
deliberately not the premise invitation or the legend, because a batch that
exhausted its schema is criticising targets it never invited premises for. A
single registered bundle would supply all four at both sites and change the
bytes of the second one, so the bundle needs a per-call subset selector — an
addition to the source protocol, made for one caller, inside the tranche that
first ships it. That is how a protocol acquires a feature nobody has used.

**The price, measured:** one new source (`premise_invitation`), a
`crit-sources.legacy-v0` bundle, a per-call `only=` or per-entry `applies_to`
selector on the bundle, and a `render_crit_pack` golden captured from the base
commit BEFORE any refactor. Roughly the size of this tranche's own §2, without
its post-allocation half.

```
EXECUTOR WINDOW — CHANGE TRANCHE: the critic's four caller-computed contexts
move behind the seat-section source interface

Read CLAUDE.md IN FULL, especially the seat-is-a-shell law and its stated
PURPOSE ("slowly separate the authority layer"). Load dr-change-orchestrator,
dr-drive-harness, dr-ask-the-right-question and pinker-write-for-readers.
Start at dr-capture-request with THIS prompt as authority. Base on main at or
after the merge of claude/seat-sections-interface-d4vjqe. Tranche directory:
experiments/<date>-change-critic-sections-behind-interface/. Offline; no key.

THE STARTING POINT, read in full first:
experiments/2026-09-04-change-seat-sections-behind-interface/ (SPEC.md §2-§5,
DELIVERY.md, this PARKED.md entry), docs/map/INV-seat-section-sources.md,
docs/map/SEAM-packs-and-token-economy-x-rules.md (its table names the critic's
four and says exactly what blocks them).

THE GOAL, one sentence: after this tranche, R2's sentence is true without
qualification -- no section a seat is shown is COMPUTED inside rules/, the
critic included.

THE QUESTION TO DECIDE FIRST, in SPEC.md, before code: the critic's two
render_crit_pack call sites supply DIFFERENT SUBSETS of the four (the
atomic-decomposition fallback passes the frames and NOT the premise invitation
or the legend, deliberately). Does the bundle gain a per-call subset selector
(an `only=` argument to assemble_sources), or does each call site name its own
registered bundle? Price both against the byte-identical-default acceptance
test, and prefer the one that keeps the CALLER from naming a section.

BYTE-IDENTICAL DEFAULT: tests/fixtures/crit_pack_legacy_v0 must pass untouched,
AND a new golden for the atomic-decomposition call site must be captured from
the base commit BEFORE any refactor. If either cannot pass, the refactor is
wrong; STOP; never edit a fixture.

OUT OF SCOPE: the batch criticism renderer (P2 below, formerly P4); the four
seats with hardcoded briefs (P3 below, formerly P5); any new record object kind.
```

---

## P2 — `render_batch_crit_pack` is still a third renderer the shell never
## reaches (carried forward from the 2026-09-03 tranche's P4)

**What.** Unchanged by this tranche, and re-checked rather than assumed:
`llm/packs.py::render_batch_crit_pack` renders a batched criticism call under
its own contract with its own hardcoded section set.

**Did the source layer make it a one-step registration? NO.** The blocker the
parent tranche named is untouched by anything here: its sections repeat PER
TARGET, and one plugin render call produces one section. A source layer changes
where CONTENT comes from; it does not give the plugin protocol a repetition
construct. The parent tranche's prompt (`experiments/2026-09-03-change-
conjecturer-pluggable-interface/PARKED.md`, P4) stands as written.

---

## P3 — four seats still have hardcoded briefs (carried forward as P5)

**What.** The judge, defender, variator and synthesizer seats. Unchanged.

**Did the source layer make it a one-step registration? PARTLY, and the part
it changed is worth recording.** Those four seats' briefs are rendered by their
own hardcoded renderers, so they still need a layout, a shell and a golden each
— the parent tranche's price. What this tranche removes from that price is the
part nobody had a road for: any of their sections that need the record can now
be a registered source rather than a computation in the dispatching rule. The
parent prompt (`P5`) stands, with one line to add to it: "sections needing the
record register as SOURCES (`DR-INV-seat-section-sources`), not as computations
in the rule."

---

## P4 — the source receipts do not reach the record

**What.** `SectionSourceReceiptV1` says which source, at which version, under
which parameters, produced how many bytes for which slot. It is returned to the
caller and dropped. A run's record therefore cannot answer "which source
produced the evidence section this seat saw" from the record alone, which is the
standard this repo holds everything else to.

**Why it is parked.** Writing it is a NEW RECORD OBJECT KIND: frozen surface 2,
`harness.py` event application. `REQUEST.md` R13 makes that an explicit STOP for
an operator grant, and the 2026-09-03 tranche parked the identical question for
the section-plugin receipts. Two parked items now want the same grant, which is
an argument for asking once for both rather than twice.

```
EXECUTOR WINDOW — CHANGE TRANCHE: the seat's section receipts reach the record

FROZEN SURFACE 2 (harness.py event application) — this tranche EXISTS to
request and use a grant. Do not begin implementation until the operator has
granted it in writing, with tools/blast_radius.py's own frozen_surface_contacts
list pasted in the request.

Read CLAUDE.md IN FULL and docs/map/INV-frozen-surfaces.md BEFORE designing.
Load dr-change-orchestrator, dr-drive-harness, dr-ask-the-right-question and
pinker-write-for-readers.

WHAT: two receipt types are built on every seat call and dropped on the floor
-- SectionReceiptV1 (which plugin formatted which section, at which version,
and whether the allocator kept it) and SectionSourceReceiptV1 (which source
computed its content). Both are proven and tested
(tests/test_seat_section_record.py, tests/test_seat_section_sources.py); what
neither has is a way into log.jsonl.

THE QUESTION TO DECIDE FIRST, in SPEC.md: ONE object kind carrying both halves,
or two? Price both against replay -- verify_root must accept a root written
before this change and a root written after, and the record's per-cycle byte
cost must be stated as a number, not a hope.

ASK FOR THE GRANT ONCE, FOR BOTH. Two tranches have now parked this same
surface for the same reason.
```

---

## P5 — the v6 scratch substitution's failure path is still shaped by
## `rules/conj.py`

**What.** The scratch render is now a registered post-allocation source, but
the caller still wraps that one stage in `try/except` to call
`abandon_v6_context_preissue()`. That is correct — abandoning a pre-issued
context is a record-side act and belongs to the caller — but it means the
stage's existence is a fact about the CALLER's error handling rather than about
the sections, and a reader of the bundle cannot see why the stage boundary is
where it is without reading `conj`.

**Why it is parked and not fixed.** Nothing is broken; this is a legibility
cost, and the alternative (a declared compensating action on the bundle entry)
would put a record-side act behind a registered, swappable configuration —
exactly what the FROZEN clause of `DR-INV-seat-section-sources` forbids. Parked
as an observation with a bias against action: the right fix may be a comment,
which this tranche has already written.

**No prompt.** If a future tranche finds this costing real time, the entry to
write is a documentation one, not a code one.
