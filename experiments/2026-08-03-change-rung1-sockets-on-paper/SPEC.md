# Spec for: rung 1 — sockets on paper, and the parked R8 job
Traces: every item cites R/C numbers. Untraceable items are bugs.

Map preflight (DR- ids resolved before this spec, per dr-change-orchestrator):
`DR-CON-schools`, `DR-CON-authority`, `DR-SUB-rules`, `DR-SUB-scheduler`,
`DR-SUB-*` (all 16, for R2), `DR-SCHEMA`, `DR-REC-change-a-seam`,
`DR-INV-frozen-surfaces`.

## Resolving Q1-Q4 (dr-ask-the-right-question applied; record first)

**Q1/Q3 (schools, authority already have `CON-` documents — write new or
extend?).** Resolved from the record, no operator input needed: SCHEMA.md's
"How to CHANGE the map" rule 5 only authorizes a NEW document when none
exists ("Adding a subsystem means: a new SUB- file..."); it says nothing
about adding a second document for a concept already covered. R1 itself says
"**one** map document" per socket — a second document for schools or
authority would make two, which the words rule out, and would violate
SCHEMA's own anti-duplication design ("the map... is not a spec", one
authoritative document per concept). Dominance test: extending is reversible
at near-zero cost if wrong (the operator asks for a split, and the content
already exists to split); duplicating is NOT reversible at near-zero cost
(a second document for the same concept is precisely the "document that
lies" SCHEMA.md warns against the moment the two drift). Extend wins.
Recorded as **A1**.

**Q2 (conjecture source, criticism source — one document, or sections in
`SUB-rules.md`?).** Resolved from the record: rung 1 names them as two
SEPARATE candidate sockets, and neither has a dedicated document today —
`SUB-rules.md` covers all of `rules/` (conj, crit, spawn, warrants, guards,
synth, vision, act, experiment), which is far broader than either single
socket. "One map document... for each candidate socket" plus the CON-
grammar ("a cross-cutting concept that is not a package" — conjecture
generation and criticism generation are each narrower than the `rules/`
package and reach into `llm/`, `run_manifest.py`, `scheduler/` too, exactly
like schools) both point to: two new, focused `CON-` documents, not new
subsections buried in an already-large `SUB-rules.md`. Recorded as **A2**.

**Q3 (scheduler ranking).** Same reasoning as Q2: `SUB-scheduler.md` covers
"problem selection, cycles, budgets, school and capability dispatch" — much
broader than the ranking/tie-break facet rung 1 names. New, focused `CON-`
document. Recorded as **A2** (same assumption, third instance).

**Q4 (per-claim vs per-document checks).** Resolved directly from
`docs/map/SCHEMA.md` "The one rule": every load-bearing claim carries its
own check, with no per-document exception. No new interpretation needed —
this was never actually silent. Recorded as **A3** for traceability only.

No reading above differs materially in file count from its alternative by
more than the ordinary "extend vs. create" choice SCHEMA.md already
resolves, and none touches a frozen surface (`docs/map/` only, `src/`
untouched). No stop required; `dr-ask-the-right-question`'s dominance test
kills all four forks. **Questions for operator: none.**

## Items

### R1 — five socket contracts

S1 (R1, A1): Extend `docs/map/CON-schools.md`. Add a new section (placed
after "## What it is", before "## Where it lives") titled to match the
operator's own words:
`## The socket contract — what it promises, what it is handed, what it must never do`
Three short bullet lists, each bullet a checkable claim citing an existing
check further down the document (reused verbatim, not duplicated prose) or
a new minimal check where no existing one covers the point:
- Promises: e.g. "the roster is a pure function of the log" (existing
  check, `harness.*` grep), "exactly two roles may be school-routed"
  (existing check).
- Handed: the `Refl` policy artifacts, `Config` knobs (`N_SCHOOLS`,
  `STANCE_DECAY`, `XEXAM_SHARE`), the manifest binding fields.
- Must never do: mint status, spend before every binding resolves, let a
  school criticise its own work, let semantic conditioning leak into
  routing authority.
accept: `grep -q "The socket contract" docs/map/CON-schools.md` and
`python tools/docs_verify.py --ring schools` exits 0.

S2 (R1, A1): Extend `docs/map/CON-authority.md` the same way — same
section title, three bullet lists sourced from "The rules it obeys"
(promises: defaults to `observe_only`, two vocabularies never cross;
handed: the five `Config` knobs, the frozen manifest `Literal`; must never
do: widen the manifest vocabulary, let a trial read a knob directly, let
`calibrated_status` yield status without a verified receipt).
accept: `grep -q "The socket contract" docs/map/CON-authority.md` and
`python tools/docs_verify.py --ring authority` exits 0.

S3 (R1, A2): New `docs/map/CON-conjecture-source.md`. Full SCHEMA.md
anatomy (header + `## What it is` / `## The socket contract...` /
`## Where it lives` / `## Where to change what` / `## Traps` — Traps may be
short or absent per SCHEMA precedent for a first-written document). Scope:
`rules/conj.py::conj`, the v4/v5/v6 turn-contract dispatch, the anti-relapse
gate call, `register_batch`. Promises: candidates are compiled from the
problem's own criteria, one register_batch per call, dispatch by
`schema_version`. Handed: the registered problem, school conditioning (if
school-routed), the manifest's schema_version. Must never do: write a
status, bypass the anti-relapse gate, hand-build a warrant (that is
`warrants.register_fail_warrant`'s job alone). Add a row to `INDEX.md`'s
Concepts table.
accept: `python tools/docs_verify.py --ring conjecture-source` (or whole-run
if `--ring` does not resolve a brand-new id) exits 0; `docs_verify --links`
0 dangling.

S4 (R1, A2): New `docs/map/CON-criticism-source.md`. Same shape, scope:
`rules/crit.py` — `crit_program`, `crit_fuzz`, `try_counterexample`,
`crit_argumentative(_batch)`. Promises: a demonstrative fail warrant only
through `warrants.register_fail_warrant`, prose criticism gated by
`_TRIAL_MODES`/authority. Handed: the target artifact, the problem's
commitments/generators/properties, (if school-routed) the critic's own
school conditioning — never the target's school or author. Must never do:
receive scratch context (frozen negative per `SEAM-rules-x-scratch`), let
`observe_only` mint a warrant, let a school criticise its own work. Add a
row to `INDEX.md`'s Concepts table.
accept: as S3.

S5 (R1, A2): New `docs/map/CON-scheduler-ranking.md`. Scope:
`Scheduler._select_problem`, the rank tie-break, `reflexive_problems`,
`problem_family`/`problem_family_key`, `FOCUS_PROBLEM`/`FOCUS_FAMILY`/
`LIVENESS_QUEUE`. Promises: the operator's seed question always wins rank
ties, import-role artifacts never count as survivors (both already
check-backed in `SUB-scheduler.md`'s Traps — cite, do not re-derive).
Handed: the harness state, `Config` knobs, the manifest (injected, never
imported). Must never do: assign a status, write to disk, let an
import-role admission record count as a survivor. Add a row to `INDEX.md`'s
Concepts table.
accept: as S3.

### R2 — every SUB document surfaces its seams in prose

S6 (R2): For each of the 16 `docs/map/SUB-*.md` files, add a `## Seams`
section (placed after the header's checked claim block, before
`## Where to change what`) that turns the `Seams:`/`Seams-undocumented:`
header lines into a reader-facing table:

    | Side | Status | What the agreement is (one line) |
    |---|---|---|
    | DR-SEAM-adjudication-x-rules | documented | <one line, from the seam doc's "The agreement"> |
    | authority x rules | undocumented | <one line: why unwritten — untouched, low-traffic, or a known gap> |

For a documented seam, the one-liner is drawn from the seam document's own
"The agreement" section (a pointer, not new invention). For an
undocumented pair, the one-liner is the author's honest best account of why
it is unwritten (SCHEMA.md: "a pair listed here without a document has NOT
been shown to be uninteresting" — the gloss must not claim otherwise unless
it is actually true, e.g. genuinely no import traffic).
accept per file: `grep -q "^## Seams" docs/map/SUB-<x>.md`; whole-set
accept: `for f in docs/map/SUB-*.md; do grep -q "^## Seams" "$f" || exit 1; done`
and `python tools/docs_verify.py --links` 0 dangling (every `DR-SEAM-`
reference in the new tables must resolve or be a plain undocumented pair
without a `DR-` prefix, per SCHEMA.md's own rule).

Files (16): `SUB-adjudication`, `SUB-amendment`, `SUB-application`,
`SUB-bridge`, `SUB-capabilities`, `SUB-evaluation`, `SUB-harness`,
`SUB-llm`, `SUB-manifest`, `SUB-ontology`, `SUB-periphery`, `SUB-rules`,
`SUB-scheduler`, `SUB-scratch`, `SUB-verification`, `SUB-workflow`.

Note (finding, not scope creep — recorded here because it changes S6's
denominator): `SUB-amendment.md`, `SUB-application.md`, `SUB-periphery.md`
exist on disk but are NOT listed in `INDEX.md`'s Subsystems table. R2 says
"every `docs/map/SUB-*.md`", which includes them regardless of INDEX
coverage; the INDEX gap itself is out of scope (PARKED.md) unless fixing it
is a one-line addition needed for `--links`/`--stale` to pass — in which
case it is the minimal fix, not the goal.

### R3 — the isolated-vs-seam triage rule

S7 (R3): Add a new section to `docs/map/SCHEMA.md`, placed directly before
"## How to CHANGE the map" (it is a prerequisite question to that
procedure), titled `## Triage: is a change isolated, or does it need
REC-change-a-seam?`. Content: a short decidable rule — if the file or
symbol being changed appears in ANY seam document's "Where it is
expressed" table, OR the file is `Owns:`-listed by two or more `SUB`/`CON`
documents, the change is seam-guided and must follow
`docs/map/REC-change-a-seam.md`; otherwise it is isolated (edit the file
and its one owning document). Cite `REC-change-a-seam.md` steps 1-2 and
`INDEX.md`'s seam matrix as the lookup path, per the R8 wording's
"ready-made inputs."
accept: `grep -q "Triage: is a change isolated" docs/map/SCHEMA.md`;
`python tools/docs_verify.py --self-test` exits 0 (SCHEMA.md's own check
target).

### R4 — scope boundary (process, not a work item)

S8 (R4): No item in this spec touches `src/`. Acceptance is negative:
`git diff --stat <tranche-base>..HEAD -- src/` is empty at delivery.

### R5 — acceptance gate for the whole tranche

S9 (R5): After S1-S7 land, run and paste:
`python tools/docs_verify.py` (0 failed), `python tools/docs_verify.py --audit`
(0 findings against the new checks), `python tools/docs_verify.py --links`
(0 dangling). Every new claim introduced by S1-S7 must be among the checks
these commands exercise — a claim added without a corresponding check is a
defect in this tranche, not a follow-up.

## Assumptions (operator may override)

A1 (Q1/Q3-schools/authority): extend `CON-schools.md` and `CON-authority.md`
in place rather than writing new documents, because a second document for
an already-covered concept both contradicts "one map document" and creates
exactly the drift risk SCHEMA.md warns against. See "Resolving Q1-Q4" above
for the full dominance-test reasoning.

A2 (Q2/Q3-scheduler): conjecture source, criticism source, and scheduler
ranking each get one new, narrowly-scoped `CON-` document rather than
subsections inside the much broader `SUB-rules.md`/`SUB-scheduler.md`,
because none is currently covered by a document at its own grain, and the
CON- grammar ("cross-cutting concept... not a package") fits a facet that
reaches beyond one package's directory.

A3 (Q4): "with checks" means SCHEMA.md's ordinary per-claim check rule —
already answered by the record, not actually an open interpretation.

A4: R2's "SUB documents" is read as literally every file matching
`docs/map/SUB-*.md` on disk today (16), including three
(`amendment`/`application`/`periphery`) that are not yet in `INDEX.md`'s
routing table. Smallest reading that is still faithful to "every."

A5: This tranche stays as ONE tranche directory (not split into separate
REQUEST/SPEC/VALIDATE/DELIVER cycles per C1's "a rung may take several
tranches"), executed as many small `dr-execute-step` steps, each committed
and pushed individually. Reasoning: the risk C1/the handover's "commit at
every phase boundary" guidance is protecting against (lost work between
pushes) is already covered by per-step commits; a second REQUEST.md quoting
the same rung-1 words for a "part 2" would add ledger ceremony without a
corresponding reduction in risk. The operator may override and require an
actual split (e.g. 1a for R1, 1b for R2+R3) if preferred.

## Questions for operator

None. All four open questions from REQUEST.md resolved from the record
(SCHEMA.md's own stated rules) via the dominance test in
`dr-ask-the-right-question`; no reading survives to the batch.

## Out of scope (explicit)

- Rungs 2-7 of the modularisation ladder (C1). Not requested this tranche.
- The `INDEX.md` Subsystems-table gap for `amendment`/`application`/
  `periphery` (noted under S6), beyond the minimal addition needed for
  `docs_verify --links`/`--stale` not to regress. A dedicated fix, if
  wanted, is its own tranche — "not requested."
- Writing the SEAM documents themselves for any `Seams-undocumented` pair.
  R2 asks only that undocumented pairs be named and glossed in prose, not
  that they be resolved into full seam documents — that is ordinary future
  map work, already tracked by `INDEX.md`'s matrix.
- Any change to `docs/map/REC-change-a-seam.md`'s existing content beyond
  what S7 cites by reference. R3 asks for a rule in `SCHEMA.md` (or the SUB
  template); `REC-change-a-seam.md` is a citation, not an edit target.
- Adding an `## Invariants` header to any `CON-`/`SUB-` document. SCHEMA.md's
  generic anatomy lists it, but no existing `CON-`/`SUB-` document in the
  repo actually has one (checked: 5 headers each, `Invariants` absent
  throughout) — matching the established convention rather than
  introducing a sixth header nothing else uses is the smaller change.

## Budget

Estimate: ~35-45 lines per new/extended socket document × 5 (S1-S5) ≈
200 lines; ~15-25 lines per SUB document × 16 (S6) ≈ 300 lines; ~25 lines
for SCHEMA.md (S7); a handful of `INDEX.md` lines (S3-S5's Concepts-table
rows). Total ≈ 550-650 lines, well over the ~300-line single-commit
guideline. Per A5, delivered as ONE tranche, MANY commits (target: one
commit per socket document for S1-S5 [5 commits], SUB documents batched
~4-5 per commit for S6 [4 commits], one commit each for S7 and the
`INDEX.md` rows, one validation commit) — roughly 12 commits, each small
enough to review and each independently pushed. Frozen surfaces touched:
none (`docs/map/` only; `INV-frozen-surfaces.md`'s five surfaces all live
under `src/`).
