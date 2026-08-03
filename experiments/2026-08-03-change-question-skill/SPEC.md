# Spec for: "create a skill for less intelligent LLMs ask the right questions in relation to this harness"

Traces: every item cites R/C numbers from REQUEST.md.

## The survey (R2) — what exists and where the gap is

The two families (C1) are PHASE machinery: they say which artifact comes
next, what it must contain, and when to stop. Twelve subskills, every one
organized around producing a document. What none of them teaches is the
reasoning BETWEEN the operator's words and the machinery — the step where a
capable model silently does four things a weaker one fumbles:

1. **Route a question to the cheapest authority first.** This session's
   42-vs-45 sweep discrepancy was answered by the record (`git ls-files`,
   two instruments) — never by asking. A weaker model asks the operator
   first, or worse, theorizes.
2. **Translate operator shorthand into the repo's typed vocabulary.**
   "start an errata please" (underdetermined artifact → derived from
   honest-ledger conventions), "Do it" (approval of exactly the previously
   stated plan, not a new instruction), "also read Claude.me" (typo,
   resolves by context), "are you using X?" (an operator question that is
   really a prompt to check — the honest "no, and checking found Y" opened
   the periphery seam finding).
3. **Bound a grant.** "fix documentation as you go" is a standing grant that
   still needed a recorded boundary (GOAL.md bounded it to touched
   documents; PARKED took the rest).
4. **Frame uncertainty as a falsifiable fork.** The defect tranche's GOAL
   stated W-vs-R so the record could decide; a weaker model picks a side
   narratively and builds on it.

Prior art (Q4): `dr-decide-or-ask` on the abandoned kw8imd lineage covers a
fifth piece — deriving the operator's answer from their recorded values
before spending their attention (the dominance test). Its content is sound
and is absorbed into the new skill with provenance noted; the lineage itself
is not resurrected.

The gap, in one sentence (R3): the framework tells a model what to PRODUCE
but not what to ASK — of the record, of the map, of itself, and only last of
the operator — so a less capable model either asks nothing (and invents) or
asks the operator everything (and burns the scarcest budget).

## Items

S1 (R1, R3, R4): NEW `.claude/skills/dr-ask-the-right-question/SKILL.md` —
the question-discipline skill. Frontmatter per repo convention (name,
description with explicit load triggers). Body sections, each written for a
less capable reader (short imperatives, decision tables, one worked example
per section drawn from committed artifacts of this repo so every example is
checkable):
  1. *The three authorities, in cost order* — the record (typed artifacts,
     instruments), the framework (CLAUDE.md, docs/map, skill ledgers), the
     operator. A question may only ascend when the cheaper authority
     genuinely cannot answer it. Includes the instrument rule ("cite the
     instrument with the number").
  2. *Reading the operator* (R4) — a translation table for this operator's
     idiom: short approvals bind to the exact stated plan; "as you go"
     grants are standing but must be bounded in the tranche ledger;
     questions about your process are prompts to check and answer
     honestly; apparent typos resolve by repo context before asking;
     new mid-work instructions are APPENDED to REQUEST.md, never absorbed
     silently. Each row cites a real committed exchange.
  3. *Ask the record first* — the diagnostic question sequence for evidence
     (which instrument produced this number; what does the blob/typed
     record say verbatim; do two instruments agree; what would falsify my
     reading), pointing at the existing tools (`verify_root`,
     `root_sweep.py`, `docs_verify.py`, the Traps sections).
  4. *Derive before asking* (absorbed from dr-decide-or-ask, kw8imd
     86f1248e, credited) — the operator's recorded values; the dominance
     test; what genuinely earns a question; batch, recommend, state
     consequences in the operator's terms.
  5. *Frame forks falsifiably* — when uncertain between two readings, write
     both as W/R-style alternatives with the evidence that would decide,
     BEFORE reading code or asking anyone.
  6. *The wrong-question table* — the recorded failure modes this repo has
     already paid for, each with its errata/trap citation (e.g. asking
     "which schema rule failed" before reading the blob; trusting a count
     without its instrument; treating a mention-shaped signal as a
     discriminator).
    accept: file exists; frontmatter has name+description; all six section
    headings present; cites dr-decide-or-ask provenance; ≥4 references to
    committed artifacts (ERRATA ids, tranche paths, or Traps entries).
    Command: grep-based, exact list in CHECKLIST.

S2 (R5, C1): integration wiring, smallest tight set —
  a. `deepreason-orchestrator/SKILL.md`: in "The scope contract", the stop
     conditions item gains one sentence routing any stop-and-ask through
     `dr-ask-the-right-question`.
  b. `dr-change-orchestrator/SKILL.md`: scope contract item 1 ("stop and
     ask — one batched question") gains the same routing sentence.
  c. `dr-spec-change/SKILL.md`: step 2's "Questions for operator" gains the
     routing sentence (derive-first, then batch).
  d. `CLAUDE.md` "Which workflow to use": one line after the two families
     naming the cross-cutting skill and when to load it.
    accept: `grep -l dr-ask-the-right-question` over those four files
    returns all four; `grep -c` in each ≥1.

S3 (R2): the survey itself is recorded — this SPEC's survey section plus
one line in DELIVERY.md's reconciliation citing it satisfies R2's "take a
look over the current framework" as performed, visible work.
    accept: SPEC.md contains "## The survey (R2)" (this section).

## Assumptions (operator may override)

A1 (Q1): "the right questions" addresses all three authorities — record,
framework, operator — in that cost order, with operator-comprehension (R4)
as its own section. Smallest reading that honors both R3 ("think about the
right things") and R4 (understanding the operator's requests).

A2 (Q2): mechanism = one new cross-cutting subskill plus references from
the two orchestrators, dr-spec-change, and one CLAUDE.md routing line. Not a
third workflow family (would contradict C1's "two workflows available" as
the given structure); not a bare document (would fail R5's "integrated
tightly" — nothing would load it).

A3 (Q3): audience = any future agent session operating this repo through
`.claude/skills/` (that is the only machinery that loads skills). The
provider model (glm-5.2) is out of scope: it is prompted through the packs
subsystem, a different and frozen-adjacent surface.

A4 (Q4): `dr-decide-or-ask` is absorbed as prior art with provenance
credit, not resurrected as a file; its lineage (kw8imd) is superseded on
this branch.

## Questions for operator

None. All four Q readings resolved as non-material under the dominance
test (S1 section 4): every reasonable operator holding the recorded values
(tight integration, smallest correct change, operator attention as scarce
budget) picks the same option.

## Out of scope (explicit)

- Provider-side prompting (packs, wire contracts) — not requested; frozen-
  adjacent (A3).
- A docs_verify mode that runs `check:` lines inside `.claude/skills/` —
  not requested; skills carry none today. Parked as a candidate ratchet.
- Resurrecting the kw8imd paper-trail push hook (db8bfc18) — not requested.
- Editing the ten other subskills — the four files in S2 are the load-
  bearing ask-points; more wiring is repetition, not integration.

## Budget

~230 lines total: ~190 new (S1 skill file), ~15 across four S2 files, plus
tranche artifacts. No `src/` changes. Frozen surfaces touched: none.
Commits: one per executed checklist step (expected 2-3).
