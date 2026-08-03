# Spec for: "a skill that teaches other LLMs how to run the harness properly and where to look"

Traces: every item cites R/C numbers from REQUEST.md.

## Survey notes feeding the items

- README.md (363 lines): entirely product-facing (wheel, CLI, MCP), zero
  references to the operating layer (skills, map, CLAUDE.md). The sprawl is
  in "Unsupported and historical boundaries" + "Developer-only source work"
  (36 lines of what-it-is-not) and long defensive narration; the does/how
  content (install, qualify tiers, reason/attach/amend, web, shallow, MCP
  table, architecture) is the part the operator wants kept and centered.
- Seam mentions without a path: both orchestrators' "Map preflight" item 2,
  `dr-plan-steps` rules 4b/4c, `dr-execute-step` map obligations — all say
  "the SEAM document" but never `docs/map/SEAM-<a>-x-<b>.md` nor name
  `REC-change-a-seam.md`. (`dr-validate-change` mentions seams only via
  `--coverage` output, which is self-explanatory — left alone.)
- The skills tree now holds 15 skills with no organising document; CLAUDE.md
  is the only routing text and it predates this session's additions except
  for the one dr-ask-the-right-question paragraph.

## Items

S1 (R1, R6, C3): NEW `.claude/skills/dr-drive-harness/SKILL.md` — the
driving manual: how to run the harness properly, and where to look. Six
sections, index-over-authorities style (it points at the owning document
and quotes only the load-bearing command):
  1. *What you are driving* — the harness in one screen; the typed record
     is the only admissible evidence; model prose never is.
  2. *Session preflight* — rollback check, editable install,
     `python -m pytest` rule, credential env files; defers to CLAUDE.md's
     environment section as the authority.
  3. *Running it* — public lifecycle (`setup → qualify → status → reason`,
     `--attach`, `amend`/`continue`, `--shallow`, `web`) and live-run
     ladders (detached launch, snapshot loop, monitor, deterministic run
     identity and retirement, qualification caching, judging typed
     outcomes only).
  4. *Where to look before modifying* — `docs/map/INDEX.md` routes;
     `INV-frozen-surfaces.md` FIRST, always; the seam file is
     `docs/map/SEAM-<a>-x-<b>.md` (sides alphabetical), read before either
     SUB; the worked recipe is `docs/map/REC-change-a-seam.md`;
     `SCHEMA.md` before writing any map document.
  5. *Where to look when something breaks* — the record-first table:
     `run-status.json`, `progress.jsonl`, `REPLAY_VALIDATION.json`,
     `verify_root`/`verify_root_report` (two instruments, cite which),
     `blobs/` for verbatim rejections, the covering document's Traps,
     `docs/ERRATA.md`; then route to `deepreason-orchestrator`.
  6. *Routing to the workflows* (R6) — defect → `deepreason-orchestrator`;
     operator-suggested change → `dr-change-orchestrator`; ambiguous or
     terse operator message, any stop-and-ask → `dr-ask-the-right-question`
     (C3: reference, not duplication — one paragraph, no idiom table).
    accept: frontmatter name/description; 6 H2 sections; grep hits for
    `deepreason-orchestrator`, `dr-change-orchestrator`,
    `dr-ask-the-right-question`, `docs/map/REC-change-a-seam.md`,
    `INV-frozen-surfaces`, `SEAM-<a>-x-<b>`.

S2 (R2): bidirectional wiring — each orchestrator's "Environment
preflight" section gains one sentence: the full driving manual is
`dr-drive-harness`, load it if this session has not run the harness
before. (Assumption A4 resolves R2 as bidirectional, matching the
precedent of the previous tranche.)
    accept: `grep -l dr-drive-harness` lists both orchestrator SKILL.md
    files.

S3 (R3): NEW `.claude/skills/README.md` — the organising index the tree
lacks: the two families as phase tables (phase → skill → artifact it
owns), the two cross-cutting skills with load triggers, the entry-point
rule (route ALL substantive work through a family), and one line on where
authority lives (CLAUDE.md law; the ledger of each tranche).
    accept: file exists; contains both family names, all 12 phase skills,
    both cross-cutting skills; ≤80 lines.

S4 (R4): CLAUDE.md updates for last turn's and this turn's changes:
  a. "Which workflow to use" gains the driving-skill line (new sessions /
     running the harness → `dr-drive-harness`) and points at
     `.claude/skills/README.md` as the index.
  b. The session-start line ("Start any session by reading the newest
     RESULTS.md segments") gains `docs/ERRATA.md` — corrections to
     committed documents are now part of the truth chain (last turn's
     addition, never registered in CLAUDE.md).
    accept: `grep -c dr-drive-harness CLAUDE.md` ≥1;
    `grep -c ERRATA CLAUDE.md` ≥1; docs_verify stays green (CLAUDE.md is
    grepped by map checks).

S5 (R5): README.md refocus:
  a. NEW short section "Operating this repository" (placed last):
     agents/developers start at CLAUDE.md; the driving manual is
     `.claude/skills/dr-drive-harness/SKILL.md`; substantive work routes
     through the workflow families (one line each). Absorbs the current
     "Developer-only source work" content (editable install + where code
     lives).
  b. Compress "Unsupported and historical boundaries" (~20 lines → ~6):
     keep the load-bearing facts (v1–v5 unsupported, MiniReason not a
     separate entry point, retired commands stay retired), drop the
     repetition.
  c. No cuts to does/how content: install, tier ladder, reason/attach/
     amend, web, shallow, engaged preset, MCP table, architecture stay.
    accept: `grep -c dr-drive-harness README.md` ≥1; `wc -l README.md`
    < 363; headings for Install / amend / MCP / Architecture still
    present.

S6 (R7): explicit seam pointers in the four workflow files that say
"seam" without a path — both orchestrators' Map preflight item 2,
`dr-plan-steps` rule 4b, `dr-execute-step` map obligations — each gains
the concrete names: `docs/map/SEAM-<a>-x-<b>.md`, sides alphabetical, and
`docs/map/REC-change-a-seam.md` as the recipe.
    accept: `grep -l "REC-change-a-seam"` over the four files lists all
    four.

S7 (R8): deferred in the operator's own words ("this job is a later
task. For now, focus on the others."). One PARKED.md entry naming the
job precisely (SUB documents cross-referencing their seams + an
isolated-vs-seam triage rule) so the later tranche starts from a
ready-made line.
    accept: PARKED.md contains the entry with the operator's quote.

## Assumptions (operator may override)

A1 (Q1): "the workflow needs to be more organised" = the skill set lacks
an organising index and consistent cross-references; S3's README plus the
S2/S6 wiring is the smallest change that makes the workflow organised
without restructuring proven phase machinery.

A2 (Q2): "readme" = the root `README.md` (the only README in the repo).

A3 (Q3): the driving skill is an INDEX over the existing authorities
(CLAUDE.md, docs/map, workflow skills) with the run-lifecycle spine —
it quotes load-bearing commands but defers detail to the owning document,
so it cannot drift into a second copy of CLAUDE.md.

A4 (Q4): R2 is bidirectional wiring (skill → workflows AND workflows →
skill), same mechanism as the delivered dr-ask-the-right-question
tranche; R6 is the skill→workflows half stated separately.

## Questions for operator

None. (Run through dr-ask-the-right-question: all four Qs fall to the
dominance test — A1–A4 are each the smallest reading consistent with the
verbatim words and this session's precedent, and no defensible
alternative changes effort by >2x.)

## Out of scope (explicit)

- R8's SUB-doc seam cross-references and the isolated-vs-seam triage rule
  — deferred by the operator's words; parked (S7).
- Restructuring the phase skills' internal content — not requested; they
  are proven machinery.
- README product-content rewrites beyond S5's compression — "more
  narrowly focused" is honored by removing what-it-is-not sprawl, not by
  touching does/how sections.
- A docs_verify mode for `.claude/skills/` — still parked from the
  previous tranche.

## Budget

~430 changed lines across ~10 files (S1 ~200 new, S3 ~70 new, S5 ~-40/+35,
S2/S4/S6 ~25 total, tranche artifacts) — over the ~300 guideline. Split
NOT proposed, with reason: all items are documentation/skills (zero `src/`
lines), each lands as its own commit with its own acceptance check, and
the operator enumerated them as one job ("While you're at it, ..."). The
per-item commits are the ordered sub-tranches in effect, under one
delivery. Frozen surfaces touched: none.
