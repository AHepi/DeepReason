# Spec for: automatic blast-radius analysis in the skills workflow
Traces: every item cites R/C numbers. Untraceable items are bugs.
DESIGN-AND-STOP: no code, no CHECKLIST.md, no execution this window (C3).

## Map preflight

This tranche's target files are `tools/` and `.claude/skills/` — outside
`docs/map/`'s own subsystem domain (which covers `src/deepreason/`
packages). The one map document that governs regardless is read in full:
`docs/map/INV-frozen-surfaces.md` (the five surfaces and the
frozen-adjacent list — CENSUS.md Part A6 reproduces the load-bearing
lines). No `SEAM-*`/`SUB-*`/`CON-*` document is in scope: this design
touches no `src/deepreason/` package.

`check: grep -q "INV-frozen-surfaces.md" docs/map/INDEX.md`

## Measurements

Part 1's full evidence base is `CENSUS.md` (committed alongside this
document), cited below by its own section letters (A1-A6, B1-B7, C).
New measurements specific to this SPEC's own design decisions:

**M1 — `tools/` has exactly three files today; the new tool is a fourth, not a modification of an existing one.**
```
$ ls tools/*.py
tools/diff_budget.py
tools/docs_verify.py
tools/root_sweep.py
```
Confirms the new tool is purely additive to `tools/` — no existing gate
is touched.

**M2 — `qualification_subject_payload` hashes the WHOLE manifest dump, confirming symbol-level (not just file-level) surface-5 contact is possible.**
```
$ sed -n '248,274p' src/deepreason/qualification.py
def qualification_subject_payload(manifest, profile):
    ...
    behavior = manifest.model_dump(mode="json", by_alias=True)
    behavior.pop("compiled_at", None)
    behavior.pop("run_input_digest", None)
    pairs = tuple({"pair_subject_digest": ..., **_pair_payload(pair)} for pair in production_contract_pairs(manifest))
    return {"schema": ..., "provider_profile": ..., "manifest_behavior": behavior, "pair_inventory": pairs}
```
A field added ANYWHERE on `RunManifest` or a model it embeds changes
`manifest_behavior`, and therefore the qualification subject digest —
this is the exact fact `2026-08-08-change-pipeline-design-d2/SPEC.md`
M20 already established. A file-only frozen-surface check (does the
target file equal `qualification.py`) would miss this; a symbol-aware
consumer check (does the target symbol resolve to a `RunManifest`
field) is required for the tool to catch it. Directly supports Item 2's
design (frozen-surface contacts computed at both file AND symbol
granularity).

**M3 — the wheel-smoke pins are name/hash constants, greppable without executing the wheel build.**
```
$ grep -n "EXPECTED_MCP_SCHEMA_SHA256\|EXPECTED_MCP_TOOLS" scripts/wheel_smoke.py
24:EXPECTED_MCP_SCHEMA_SHA256 = (
41:EXPECTED_MCP_TOOLS = {
198:    if names != EXPECTED_MCP_TOOLS:
201:    if hashlib.sha256(encoded).hexdigest() != EXPECTED_MCP_SCHEMA_SHA256:
```
Confirms Item 1's "wheel-smoke pins" consumer check can be a plain
string-membership grep (is the touched symbol's name a key inside
`EXPECTED_MCP_TOOLS`, or does the touched file affect the object
`EXPECTED_MCP_SCHEMA_SHA256` is computed from) — no new dependency
needed to compute this consumer class.

**M4 — the gates pre-plan's own rule for a sixth gate is satisfied by this tranche's own origin.**
```
$ grep -n "sixth gate" docs/proposals/DETERMINISTIC_GATES_PREPLAN.md
185:  every incident becoming another instrument. The ledger above is closed at
186:  five; a sixth gate requires its own recorded-failure citation and an
187:  operator word, same as a frozen surface.
```
This tranche's origin incident is `docs/ERRATA_EXECUTOR.md`'s
2026-08-09 entry (CENSUS.md B1) — the recorded-failure citation — and
REQUEST.md's verbatim operator words are the operator word. Both
preconditions the ladder's own rule demands are satisfied by this
tranche BEFORE Item 2 proposes a sixth rung. Directly supports Fork F2
(amend the existing ladder document vs. write a standalone proposal).

**M5 — no existing test or map document currently asserts on any name this design introduces.**
```
$ grep -rn "blast_radius\|BLAST_RADIUS" tests/ docs/map/ tools/ .claude/skills/
(no hits)
```
Confirms Item 1's typed result name (`BLAST_RADIUS_RESULT_V1`) and tool
path (`tools/blast_radius.py`) are free of collision. Feeds the
Blast-radius census section below.

**M6 — the two skill files this design amends are referenced today only in prose/docstrings describing `diff_budget.py`'s own behavior, not in a way this design's addition disturbs.**
```
$ grep -rn "dr-execute-step" tests/test_diff_budget.py
8:gets exercised via subprocess, matching how dr-execute-step actually
78:    """Permanent mutation companion (dr-execute-step 'Durable tests' rule
$ grep -n "dr-execute-step" docs/map/INV-frozen-surfaces.md
158:hand. `dr-execute-step` runs this gate at every `[COMMIT]` step; EXCEEDED is
```
Both hits describe `diff_budget.py`'s existing checkpoint, unchanged by
this design (Item 2 ADDS a second gate invocation alongside it, per
Item 2's own wording — it never edits `diff_budget.py`'s own behavior or
these existing sentences). Feeds the Blast-radius census section below.

**M7 — the "declared target" input shape the manual convention already uses is dual-granularity (files AND symbols), which this design's tool input mirrors rather than narrows.**
```
$ grep -n "grep -rn" .claude/skills/dr-spec-change/SKILL.md
```
(step 4's own text, already quoted in CENSUS.md A1: `grep -rn "<symbol>"
tests/ docs/map/`) — the existing manual census already operates at
symbol granularity, not file granularity alone; a file-only tool input
would be a REGRESSION from current practice. Resolves REQUEST.md Q3.

## Items

S1 (R1, R4): the tool design (`tools/blast_radius.py`,
`BLAST_RADIUS_RESULT_V1`) — see Item 1 below.
    accept: this document's Item 1 section names the tool's CLI, input
    shape, four computations, typed result schema, exit classes, mutation-
    proof plan, and map `check:` line placement, each traced to an R/C/M
    number; `test -f experiments/2026-08-10-change-blast-radius-analysis/SPEC.md`
    -> exit 0 (this document, committed).

S2 (R4): the three skill checkpoints — see Item 2 below.
    accept: Item 2 names, for each of the three checkpoints R4 specifies,
    the exact skill file, the exact step/section amended, and the exact
    obligation added, each state-not-silence per CENSUS.md A5's precedent.

S3 (R2): the design premise (operator's self-assessment ledgered as
context; the system's own disclosure obligation as the target) governs
Item 1's disclosure-summary computation and Item 2's grant-request
checkpoint specifically — see the "Design premise, applied" note inside
Item 2.
    accept: Item 2's grant-request checkpoint text names R2/the design
    premise explicitly as its justification, not as background color.

S4 (R3): `CENSUS.md`, committed alongside this document.
    accept: `test -f experiments/2026-08-10-change-blast-radius-analysis/CENSUS.md`
    -> exit 0; contains Parts A (six items, A1-A6) and B (seven cases,
    B1-B7) plus a synthesis (Part C) naming what Part 2 must fix — all
    three present in the committed file.

S5 (R5): `HIDDEN_LEGACY_INVENTORY.md`, committed alongside this document.
    accept: `test -f experiments/2026-08-10-change-blast-radius-analysis/HIDDEN_LEGACY_INVENTORY.md`
    -> exit 0; contains five inventory rows plus the related-pattern and
    targeted-sweep sections.

S6 (C4): the Frozen-surface contact forecast section below, checked from
scratch against `INV-frozen-surfaces.md`'s five-item list, not assumed
from C4's own "expect none."
    accept: the Frozen-surface contact forecast section below pastes the
    file-list check (M-less, direct comparison) rather than asserting
    the operator's prediction unchecked.

S7 (C5): the Decision sheet section below, every fork priced with a
recommendation.
    accept: the Decision sheet section contains at least F1-F5, each
    with two-or-more roads, a cost statement per road, and one
    recommendation citing a measurement or CENSUS.md case.

S8 (C6): commit and push `REQUEST.md` (done), `CENSUS.md`,
`HIDDEN_LEGACY_INVENTORY.md`, and this `SPEC.md`, then STOP.
    accept: `git log --oneline origin/claude/blast-radius-analysis-design-3avwew..HEAD`
    at delivery time -> empty (nothing unpushed); no `CHECKLIST.md` exists
    in this tranche's directory.

S9 (C7): every item below that touches what a mechanism weights, reports,
or gates carries an explicit R-g/solo-law note.
    accept: Item 1's "R-g and solo law" subsection and Item 2's per-
    checkpoint notes are both present.

## Design decisions

### Item 1 (R1, R4): the tool — `tools/blast_radius.py`

**Why this shape, in one sentence (CENSUS.md Part C):** every one of the
seven failure cases (CENSUS.md B1-B7) was answerable from the tree at
grant time by a static trace a person COULD run by hand and, in six of
seven cases, did — months late, after the fact, or only during a live
run (B4). The tool's entire job is running that same trace mechanically,
every time, before the grant is asked for.

**CLI, mirroring `diff_budget.py`'s established shape (M1, CENSUS.md A3):**
```
python tools/blast_radius.py --files <path> [<path> ...]
                              [--symbols <name> [<name> ...]]
                              [--against <ref>]
python tools/blast_radius.py --self-test
```
`--files`/`--symbols` are the "declared target symbols/files" R4 names
(resolves Q3, M7: both granularities, matching existing manual practice
rather than narrowing it). At least one of `--files`/`--symbols` is
required unless `--self-test`. `--against <ref>` is optional; when
given, it enables the diff-aware reachability comparison (see below);
when omitted, the tool reports a snapshot against the current working
tree only.

**Computation 1 — frozen-surface contacts (all five, plus frozen-adjacent).**
Two tiers, because file-level and symbol-level contact are different
claims (M2):
- DIRECT: a `--files` entry's path matches one of the five files
  `INV-frozen-surfaces.md` names, or the frozen-adjacent
  `llm/firewall.py`. Deterministic path comparison; no ambiguity.
- SYMBOL-INDIRECT: a `--symbols` entry is defined in, or referenced by
  (`grep -n "\b<symbol>\b"`) one of the same six files. Reported
  separately from DIRECT and labeled "plausible" rather than
  "confirmed" — a grep-based symbol reference is not proof of semantic
  contact (a comment or an unrelated identically-named local variable
  would false-positive), so the disclosure summary states this
  explicitly rather than overclaiming precision the grep cannot back.
  This is the same honesty the manual convention already practices
  (CENSUS.md A1: "not this file's own mechanical enforcement" — a
  grep-based tool inherits the same limits as a grep-based human, and
  should say so, not claim more).

**Computation 2 — reachability changes (dispatch paths dead or newly-live; the property_designer/legacy-criticism failure class, CENSUS.md B3/B4).**
Two modes:
- SNAPSHOT (always run): for each `--symbols` entry that names a
  function or a role-dispatch-table VALUE (e.g. a string appearing as a
  value inside `GROUP_ROLES`, `dict`-based role/route tables — the
  DISPATCH SHAPE B4's own trace walked by hand), statically compute
  whether it is reachable from a fixed, hand-maintained ENTRY-POINT set
  (the `deepreason` console commands, `scheduler.py`'s dispatch loop,
  the role-dispatch tables themselves) via `ast`-based call-name
  resolution (stdlib `ast`, no new dependency — mirrors `diff_budget.py`'s
  own dependency-free precedent, M1). Reports REACHABLE / UNREACHABLE /
  UNKNOWN per symbol. UNKNOWN is a first-class, honestly-reported
  outcome for anything the static walk cannot resolve (fully dynamic
  dispatch, e.g. `getattr(obj, name)` with a runtime-computed `name`) —
  never silently folded into REACHABLE, per this repo's own
  "counts are claims" check-writing rule (`docs/map/SCHEMA.md`, CENSUS.md
  A6).
- DIFF (only with `--against <ref>`): the same snapshot computed against
  `<ref>`'s tree, compared to the working-tree snapshot. A symbol whose
  status crosses REACHABLE→UNREACHABLE is flagged `newly_dead`;
  UNREACHABLE→REACHABLE is flagged `newly_live`. This is the mechanized
  form of B3's own failure (`N_SCHOOLS` becoming load-bearing) and B1's
  own failure class in miniature (a dependency that was not there before
  becoming load-bearing after).
- **Known, disclosed limit (per Computation 1's own honesty rule):** the
  entry-point set is hand-maintained, the same way `INV-frozen-surfaces.md`'s
  own `Owns:` lists are hand-maintained but check-verified. A newly-added
  entry point not yet in the tool's registry could cause a false
  UNREACHABLE. This is named explicitly rather than hidden, and is the
  reason Computation 2's report always carries an UNKNOWN bucket rather
  than forcing a binary answer.

**Computation 3 — consumers of every touched symbol (tests, map checks, qualification digests, wheel-smoke pins).**
Mechanizes the existing manual grep (CENSUS.md A1) plus two new
consumer classes M2/M3 established are checkable without new
dependencies:
- `tests`: `grep -rn "<symbol>" tests/` (unchanged from manual practice,
  now run automatically for every declared symbol, not just the ones
  the author remembers to grep).
- `map_checks`: `grep -rn "<symbol>" docs/map/` (same).
- `qualification_digest`: CONFIRMED if the symbol resolves (via the same
  `ast` walk as Computation 2) to a field on `RunManifest` or a model
  `qualification_subject_payload` embeds (M2); PLAUSIBLE if the symbol
  is merely referenced inside `qualification.py` without resolving to a
  manifest field; absent otherwise.
- `wheel_smoke_pins`: CONFIRMED if the symbol's name is a key inside
  `scripts/wheel_smoke.py`'s `EXPECTED_MCP_TOOLS` or a
  `pyproject.toml` console-script entry-point name (M3); PLAUSIBLE if
  merely referenced in `scripts/wheel_smoke.py` or
  `scripts/wheel_operational_smoke.py` without matching a pinned name.

**Computation 4 — the disclosure summary, in operator terms.**
A plain-language paragraph generated FROM the three structured
computations above — never a separate, hand-written gloss that could
drift from the data. Template: "This change touches N of the five
frozen surfaces (list, each with its one-line plain meaning already
carried in `INV-frozen-surfaces.md`'s own prose — the tool quotes it,
never re-writes it). M symbol(s) would become newly reachable; K would
become newly dead (or: 'no reachability change detected against
`<ref>`' when `--against` is unset or nothing crossed). P test file(s)
and Q map document(s) assert on the touched symbols today." Every
number in the summary is the count of a list the JSON result also
carries in full — pre-satisfies `dr-explain-to-operator`'s glossing
requirement (CLAUDE.md, `dr-explain-to-operator/SKILL.md`) by
construction, so a STOP message that embeds this summary is glossed
without the author having to hand-write the gloss under time pressure.

**Typed result — `BLAST_RADIUS_RESULT_V1`:**
```json
{
  "result_type": "BLAST_RADIUS_RESULT_V1",
  "targets": {"files": ["..."], "symbols": ["..."]},
  "base": "<ref or null>",
  "frozen_surface_contacts": [
    {"surface": "<one of the five, verbatim from INV-frozen-surfaces.md>",
     "tier": "DIRECT" | "SYMBOL_INDIRECT",
     "target": "<the --files or --symbols entry>", "detail": "..."}
  ],
  "frozen_adjacent_contacts": [ "...same shape, route_fingerprint..." ],
  "reachability": [
    {"symbol": "...", "status_current": "REACHABLE" | "UNREACHABLE" | "UNKNOWN",
     "status_base": "REACHABLE" | "UNREACHABLE" | "UNKNOWN" | null,
     "direction": "newly_dead" | "newly_live" | "unchanged" | null}
  ],
  "consumers": {
    "tests": [{"target": "...", "hits": ["<file:line>", "..."]}],
    "map_checks": [{"target": "...", "hits": ["..."]}],
    "qualification_digest": [{"target": "...", "tier": "CONFIRMED" | "PLAUSIBLE"}],
    "wheel_smoke_pins": [{"target": "...", "tier": "CONFIRMED" | "PLAUSIBLE", "pin": "..."}]
  },
  "disclosure_summary": "<plain-language paragraph, generated from the fields above>",
  "frozen_surface_verdict": "CONTACT" | "CLEAR"
}
```
`frozen_surface_verdict` is the ONLY scalar verdict field, deliberately
narrow (the gates pre-plan's own shape rule, CENSUS.md A4: "A gate
reports facts; the OWNING SKILL decides policy") — reachability and
consumer findings are reported as lists for the calling skill to
classify (EXPECTED TO MOVE / MUST NOT MOVE, exactly the existing manual
census's own vocabulary, CENSUS.md A1), never collapsed into a single
pass/fail the tool itself does not have standing to declare.

**Exit classes (mirrors `diff_budget.py`, M1, gates pre-plan shape rule):**
`0` result emitted (JSON printed; `frozen_surface_verdict` may itself be
`CONTACT` — the exit code never encodes policy); `2` invalid invocation
(neither `--files` nor `--symbols` given, and not `--self-test`); `3`
evidence unavailable (a declared file does not exist in the tree, or
`--against` names a ref that does not resolve / the working directory is
not a git tree).

**Mutation-proof plan (named here per DESIGN-AND-STOP's own rule that no
code is written this window; the plan itself is the deliverable):**
1. Frozen-surface DIRECT tier: `--files src/deepreason/harness.py` must
   yield a non-empty `frozen_surface_contacts`; removing that argument
   (any other file) must yield empty. Kills a tool that hard-codes
   "always empty" or "always non-empty."
2. Reachability: in a temp fixture repo (mirroring `diff_budget.py`'s own
   `--self-test`, M1), a function defined but never called must report
   `UNREACHABLE`; adding one call site from a registered entry point
   must flip it to `REACHABLE`. Kills a tool that reports REACHABLE
   unconditionally.
3. Consumers: a temp fixture `tests/` file referencing a target symbol
   must appear in `consumers.tests`; deleting that file must remove the
   hit. Kills a tool with a hard-coded or cached hit list.
Each proof is RED before the fix, GREEN after, per `dr-execute-step`'s
own "Durable tests, checks, and probes" rule 3 (CENSUS.md's own citation
of that rule) — to be attested with `tools/mutation_attest.py` if/when
Rung G2 is built, or by pasted RED/GREEN output otherwise, at
implementation time (out of scope for this window, C3).

**Map `check:` line placement.** A new subsection of
`docs/map/INV-frozen-surfaces.md`, mirroring the existing "Diff budget
gate (Rung G1)" subsection exactly (same document, same pattern, so a
reader who already knows where to look for one gate finds the other):
```
### Blast-radius gate (Rung G6)
...
check: python -c "import ast; ast.parse(open('tools/blast_radius.py').read())"
check: grep -q "BLAST_RADIUS_RESULT_V1" tools/blast_radius.py
```
Additionally — closing the gap CENSUS.md A6 names explicitly (the
2026-08-09 incident has no Traps entry in `INV-frozen-surfaces.md`
itself, only in `docs/ERRATA_EXECUTOR.md`) — Item 1's implementation
step should ALSO backfill a Traps entry for that incident into
`INV-frozen-surfaces.md`, per the document's own convention ("a Traps
entry is never deleted, only rewritten to say when it was fixed"). Named
here as part of Item 1's scope since it is the same document, the same
commit, and the same root cause this gate exists to close; not treated
as a separate item because splitting it would violate "one tranche, one
goal" in the other direction (two tiny fixes to the same file in two
tranches).

**R-g and solo law (C7).** The tool is fully deterministic and consults
no LLM, judge, or seat at any point — it reads `git`, the filesystem, and
Python ASTs only. It cannot weight anything by conjecture kind (formal
vs. informal) because it never inspects a conjecture or artifact at all,
only code, tests, and map documents — R-g's prohibition does not apply
by construction, the same way Computation 2's honesty rule does not
apply to a computation that never runs. It requires no seat, ensemble,
or judge to invoke — a solo run and a run with every seat filled compute
byte-identical results for the same tree and the same declared targets,
satisfying the solo law's "may never be structurally locked out" the
same way `diff_budget.py` already does (M1: the existing gate has never
had a seat/judge dependency; this one inherits that shape, not invents a
new exemption).

### Item 2 (R4, R2): the three skill checkpoints

**Design premise, applied (R2, S3).** Every checkpoint below is written
so the OPERATOR never has to run `tools/blast_radius.py` themselves, read
its JSON, or know it exists as a command — the SKILL runs it and embeds
its output. The operator's only obligation stays what it already is:
read the disclosure and answer. This is R2's "the operator cannot be the
blast-radius calculator" made concrete: the calculator is the tool, run
by the skill, never handed to the operator as a homework assignment.

**Checkpoint 1 — `dr-spec-change`, the census becomes tool-backed.**
Amends `.claude/skills/dr-spec-change/SKILL.md` steps 3 and 4. Today
both steps are pure hand-run prose (CENSUS.md A1, A2). The amendment:
before writing the "Frozen-surface contact forecast" and "Blast-radius
census" sections, run `python tools/blast_radius.py --files <every
planned target file> --symbols <every planned target symbol>` and paste
its `BLAST_RADIUS_RESULT_V1` JSON (or the relevant excerpted fields) into
SPEC.md. The existing manual `grep -rn "<symbol>" tests/ docs/map/` step
is RETAINED as a required cross-check specifically for anything the
tool's own honesty rules mark `UNKNOWN` or the tool cannot resolve
(dynamic dispatch, symbols not expressible as a single grep-able
identifier) — the tool augments the census, it does not remove the
author's own judgment where the tool has said, in writing, that it
cannot judge. Rubric step 8's own two existing yes/no items ("blast-
radius census pasted," "frozen-surface contact forecast recorded") are
unchanged in wording; what changes is that "pasted" now means "the
tool's own result is pasted," not an author-run grep.

**Checkpoint 2 — grant-request time, the load-bearing one.** This is the
checkpoint CENSUS.md B1 shows failing directly: the 2026-08-09 tranche's
SPEC.md had ALREADY identified surface-3 contact in prose, and the STOP
that finding should have forced did not happen before the commit landed.
Two amendments, both required, because the STOP can originate from
either skill depending on how the tranche is going:
- `dr-spec-change` step 3 gains one sentence: "The STOP message — and
  this document's own Frozen-surface contact forecast / Decision sheet
  sections — MUST embed `tools/blast_radius.py`'s computed
  `frozen_surface_contacts` (and `frozen_adjacent_contacts`) list
  verbatim, never a hand-written summary of it. A STOP that describes
  contact without pasting the tool's own list is not this checkpoint."
- `dr-ask-the-right-question` section 4 ("What earns a question") gains
  a clause on its existing "frozen-surface or irreversible action" entry:
  "when the earning reason is frozen-surface contact, the question MUST
  embed `tools/blast_radius.py`'s `BLAST_RADIUS_RESULT_V1` result — this
  is section 1's own 'cite the instrument with the number' rule, applied
  to this specific instrument."
Effect: the words the operator gives in response are words given OVER a
pasted, computed contact list — never over a paraphrase of one, and
never inferred from memory of an earlier SPEC.md section three steps
back (B1's exact failure mode).

**Checkpoint 3 — `dr-execute-step` commits, actual-touch drift.** Amends
`.claude/skills/dr-execute-step/SKILL.md` step 6, immediately alongside
the existing `diff_budget.py` invocation (same step, same `[COMMIT]`
trigger — one more command in the same sequence, not a new step). After
reading `DIFF_BUDGET_RESULT_V1.verdict`: also run
`python tools/blast_radius.py --files <this step's actually git-added
files> --symbols <this step's actually touched top-level defs, from the
diff hunks> --against <tranche base>` and compare its
`frozen_surface_contacts` and `reachability` output against THIS
document's own Frozen-surface contact forecast and Blast-radius census
sections. Any `frozen_surface_contacts` entry not already named in
SPEC.md, OR any `reachability` entry whose `direction` is `newly_dead`/
`newly_live` and was not predicted, is DRIFT — a STOP in the exact
format `diff_budget.py`'s `EXCEEDED` already uses (priced options,
recommendation, "not a footnote," CENSUS.md A3's own quoted language),
never silently absorbed into the commit. This is B1's own fix,
mechanized: the surface-3 touch would have been flagged HERE, at the
exact commit, before push, regardless of whether the author remembered
SPEC.md's own earlier finding.

**R-g and solo law (C7), all three checkpoints.** None of the three
checkpoints reads, weights, or reports on conjecture kind, seat
configuration, or judge availability — they operate entirely on the
tranche's own files, symbols, and git history. All three run identically
for a solo session and a fully-staffed one, the same as the existing
`diff_budget.py` checkpoints they sit beside.

**Named, explicit non-goal (bounding this tranche, "one tranche, one
goal"):** generalizing Checkpoint 2 to every other STOP-capable phase in
either workflow family (e.g. `dr-propose-fix`'s approval gate,
`dr-execute-step` step 2's own tree-contradiction STOP) is real future
work but is NOT specified here — Checkpoint 2 is bounded to the two
sites (`dr-spec-change`, `dr-ask-the-right-question`) that concretely
exist and are concretely testable this tranche. Recorded as a candidate
for a future rung, not silently assumed complete.

## Assumptions (operator may override)

A1 (Q1): the PARKED/ERRATA sweep for "any others" (R3) is bounded to:
all 17 `docs/ERRATA.md` entries (read in full), all 37 `PARKED.md` files
under `experiments/` (grepped for disconnection-pattern language;
substantial ones read in full), and the two named leads ("Road E,"
`GATES_AND_PACKAGES_PREPLAN.md`'s dangling citation) traced to ground.
CENSUS.md Part B's "Cases considered and set aside" subsection states
this bound explicitly and names what was checked and rejected, rather
than leaving "every" unbounded. Smallest reasonable reading consistent
with "a targeted sweep," not an unbounded archaeology.

A2 (Q2): the tool's CLI shape, typed result name, exit classes, and map
`check:` line placement are fully specified in Item 1 (naming
`tools/blast_radius.py`, `BLAST_RADIUS_RESULT_V1`, and a new subsection
of `INV-frozen-surfaces.md` mirroring the "Diff budget gate (Rung G1)"
precedent exactly); the three skill files receiving amendment text are
named in Item 2 (`dr-spec-change`, `dr-ask-the-right-question`,
`dr-execute-step`) — chosen because these are the only three sites
CENSUS.md's evidence (A1-A5, B1) traces the disclosure gap to.

A3 (Q3): tool input is dual-granularity (`--files` AND `--symbols`),
resolved by M7 — the existing manual convention already operates at
symbol granularity; a file-only design would regress current practice.

A4 (Q4): `CENSUS.md` and `HIDDEN_LEGACY_INVENTORY.md` are tranche-local
documents (`experiments/2026-08-10-change-blast-radius-analysis/`),
produced THIS window alongside `SPEC.md`, rather than deferred past the
SPEC-AND-STOP boundary or placed under `docs/`. Justification: (a) they
are research/documentation artifacts, not code — C3's "no code this
window" does not reach them; (b) direct precedent —
`experiments/2026-08-08-change-pipeline-census-d1/CENSUS.md` is exactly
this shape (a tranche-local census document cited by SPEC.md M-numbers)
and D1 was itself a phase within the same `dr-change-orchestrator`
family, not a separate tranche; (c) "tokens are cheap; the agent is not"
(CLAUDE.md) favors producing them now, using research already performed,
over a second round-trip. Smallest reading that still satisfies R3/R5
literally as artifact deliverables. Operator may override toward a
`docs/`-level location if the inventory is meant to be a standing,
repo-wide reference rather than tranche narrative — priced as Fork F4
below.

A5 (Q5): Part 2 (R4) is a DESIGN this window, not an implementation —
`tools/blast_radius.py` and the three skill amendments are SPECIFIED in
full (Item 1, Item 2) but not written; C3's "no code this window"
governs, and R4's own prose ("a deterministic tool... that computes")
describes the DESIGNED shape, read as the DESIGN-AND-STOP convention
already reads equivalent language in prior tranches
(`2026-08-08-change-pipeline-design-d2/SPEC.md`'s own Item 1-6 prose is
in the same present-tense "computes"/"builds" voice while itself being
SPEC ONLY). Matches C3 literally rather than by inference alone.

## Questions for operator (STOP if non-empty)

(empty as a formal blocking section — every material fork below is
priced in the Decision sheet instead, per this tranche's DESIGN-AND-STOP
shape; precedent: `2026-08-08-change-pipeline-design-d2/SPEC.md`'s own
"empty... every material fork is priced in the Decision sheet below
instead.")

## Out of scope (explicit)

- Building `tools/blast_radius.py` itself, or editing any `.claude/skills/*.md`
  file, or editing `docs/proposals/DETERMINISTIC_GATES_PREPLAN.md` — all
  deferred past this SPEC-AND-STOP boundary (C3, A5); named precisely so
  the Budget section below can price them without performing them.
- Generalizing Checkpoint 2 to every STOP-capable phase in both workflow
  families — named as a future candidate in Item 2, not specified here.
- Retiring, repurposing, or reconnecting anything
  `HIDDEN_LEGACY_INVENTORY.md` lists (`property_designer`, the dead
  `ARGUMENTATIVE_AUTHORITY` value, the unwired audit functions) — R5 asks
  for the inventory so the OPERATOR can decide priorities; this tranche
  makes no re-connection recommendation and takes no such action.
- Backfilling the `bias_probes`/judge-audit-machinery gap
  (`HIDDEN_LEGACY_INVENTORY.md` item 4) with real live evidence — that is
  exactly the kind of work CLAUDE.md's own "tokens are cheap" law
  reserves for a dedicated tranche with its own goal, not a side effect
  of a design spec.
- Any change to `experiments/2026-08-09-change-judge-evidence-review/`
  or any other cited tranche's own artifacts.

## Frozen-surface contact forecast

**NONE — checked against `INV-frozen-surfaces.md`'s five-item list, not
assumed from C4's own prediction.**

This tranche's own target files (S6): `tools/blast_radius.py` (new),
`.claude/skills/dr-spec-change/SKILL.md`,
`.claude/skills/dr-ask-the-right-question/SKILL.md`,
`.claude/skills/dr-execute-step/SKILL.md`,
`docs/proposals/DETERMINISTIC_GATES_PREPLAN.md`,
`docs/map/INV-frozen-surfaces.md` (a new subsection plus a Traps entry,
never touching an existing check or `Owns:` line).

```
$ for f in tools/blast_radius.py .claude/skills/dr-spec-change/SKILL.md \
    .claude/skills/dr-ask-the-right-question/SKILL.md \
    .claude/skills/dr-execute-step/SKILL.md \
    docs/proposals/DETERMINISTIC_GATES_PREPLAN.md \
    docs/map/INV-frozen-surfaces.md; do echo "$f"; done
```
None of the six paths equal, or lie under, `src/deepreason/capabilities/state.py`,
`src/deepreason/harness.py`, `src/deepreason/invariants.py`,
`src/deepreason/run_manifest.py`, `src/deepreason/qualification.py`, or
the frozen-adjacent `src/deepreason/llm/firewall.py`. Every surface
individually checked, per `INV-frozen-surfaces.md`'s own list:

- Surface 1 (`capabilities/state.py`): NONE. No target file is this file
  or under `src/deepreason/capabilities/`.
- Surface 2 (`harness.py`): NONE.
- Surface 3 (`invariants.py`/`verification/`): NONE.
- Surface 4 (`run_manifest.py`): NONE.
- Surface 5 (`qualification.py`): NONE.
- Frozen-adjacent (`llm/firewall.py`): NONE.
- `INV-frozen-surfaces.md` itself: this tranche DOES touch it, but only
  by ADDING a new subsection (mirroring the existing "Diff budget gate
  (Rung G1)" precedent) and a new Traps entry — no existing `Owns:`
  line, `check:` line, or prose sentence in the document is edited. The
  document's own `Verify:` command (`python tools/docs_verify.py`)
  governs additions the same as edits; the addition ships with its own
  new `check:` lines (Item 1), so it is held to the same standard as
  every existing claim in the file, not exempted from it.

Matches the operator's own prediction (C4, "expect none — tools/ and
skills only") exactly, now verified rather than assumed.

## Blast-radius census

`grep -rn "blast_radius\|BLAST_RADIUS" tests/ docs/map/ tools/ .claude/skills/`
(M5) -> no hits. New symbol and new tool path; nothing exists yet to
collide with or move.

`grep -rn "dr-execute-step" tests/test_diff_budget.py docs/map/INV-frozen-surfaces.md`
(M6) -> two hits, both prose describing `diff_budget.py`'s OWN existing
checkpoint behavior ("gets exercised via subprocess, matching how
dr-execute-step actually [works]"; "`dr-execute-step` runs this gate at
every `[COMMIT]` step") -> MUST NOT MOVE: Item 2's Checkpoint 3 amendment
ADDS a second gate invocation alongside `diff_budget.py`'s existing one
in the same step; it does not alter `diff_budget.py`'s own behavior, its
own test file's assertions, or these two existing sentences. Confirmed
by inspection of both hit sites (M6's own pasted output above).

`grep -rn "dr-spec-change\|dr-ask-the-right-question" tests/ docs/map/`
-> no hits beyond the `dr-execute-step` ones already listed above (both
files were included in the same grep pass, M6) -> vacuous MUST NOT MOVE:
nothing currently asserts on these two skill files' content, so nothing
is at risk of drifting when they gain new paragraphs.

`grep -n "sixth gate" docs/proposals/DETERMINISTIC_GATES_PREPLAN.md` (M4)
-> one hit, the ladder's own closing rule -> EXPECTED TO MOVE in the
sense that this tranche's own existence is what SATISFIES that rule's
precondition (a sixth gate requires a citation and a word — both are
now on record); the rule's TEXT itself is not proposed to change.

`ls tools/*.py` (M1) -> three existing files, none named `blast_radius.py`
-> EXPECTED TO MOVE (a fourth file added); no existing file's content is
touched.

## Measurements

See "Measurements" above (M1-M7); `CENSUS.md` Parts A and B are the
Part-1 evidence base, cited throughout by section letter rather than
repeated here.

## Options (forks)

**F1 — reachability computation approach (Item 1, Computation 2).**
- Option A (grep-heuristic only: does the symbol NAME appear as a
  substring anywhere in `src/`): cheapest to build, but cannot
  distinguish a definition from a call, a comment, or a docstring
  mention — would have flagged B4's `property_designer` as "referenced"
  everywhere its GROUP_ROLES entry and its one call site both appear,
  without ever computing that the call site is itself unreachable. NOT
  chosen: it would not have caught the actual failure case it exists to
  catch.
- Option B (AST-based call-name resolution from a hand-maintained
  entry-point registry, M1's dependency-free precedent): correctly
  distinguishes definition/call/reference, walks the caller graph the
  way B4's own manual trace did, and stays honest about its own limits
  (UNKNOWN for dynamic dispatch) rather than overclaiming. Costs more to
  build than Option A (an AST walker vs. a `grep -l`), but it is the
  only option that actually reproduces the trace CENSUS.md B4 shows was
  needed. RECOMMENDED (priced in Decision sheet).

**F2 — where the new gate lives: amend the existing ladder document, or write a standalone proposal?**
- Option A (amend `docs/proposals/DETERMINISTIC_GATES_PREPLAN.md`, add a
  "### Rung G6" section): reuses the ladder's own shape rules, its own
  "Order and cost" bookkeeping, and its own explicit rule for a sixth
  gate (M4) — the rule's own precondition (recorded-failure citation +
  operator word) is satisfied by THIS tranche, which is exactly the
  circumstance the rule anticipates. Smallest diff; one document gains
  one section.
- Option B (a new, standalone `docs/proposals/BLAST_RADIUS_PREPLAN.md`):
  avoids touching a document already governing five other rungs, but
  duplicates the shape-rules preamble, creates a second ladder with no
  cross-reference, and does not honor the existing document's own
  "closed at five... a sixth gate requires..." sentence, which reads as
  addressed TO this exact situation.
- RECOMMENDED: Option A. M4's own quoted text is the deciding measurement
  — the existing document already names the exact precondition this
  tranche meets.

**F3 — checkpoint 2's scope: the two sites named, or every STOP-capable phase?**
- Option A (bounded to `dr-spec-change` + `dr-ask-the-right-question`,
  Item 2's own "named, explicit non-goal"): matches what CENSUS.md's
  evidence actually traces to (B1's failure is a `dr-spec-change`-phase
  failure); testable and mutation-provable within this tranche's own
  scope once built.
- Option B (every STOP in both families, e.g. `dr-propose-fix`'s
  approval gate too): broader coverage, but "one tranche, one goal"
  (CLAUDE.md's own cross-routing rule) — no case in CENSUS.md's evidence
  base traces to a `dr-propose-fix`-phase disclosure failure, so
  extending there now would be UNMEASURED design, the same discipline
  `2026-08-08-change-pipeline-design-d2/SPEC.md` already applied to its
  own Fork F1.
- RECOMMENDED: Option A, with Option B named as future work (Item 2's own
  text), not silently dropped.

**F4 — `HIDDEN_LEGACY_INVENTORY.md`'s location: tranche-local, or `docs/`-level standing reference?**
- Option A (tranche-local, as delivered, A4): smallest footprint,
  consistent with how `PARKED.md`/`RESULTS.md` already work in this
  repo (CLAUDE.md's own convention: "Experiment narrative lives in the
  experiment's RESULTS.md"); the document is still fully linkable and
  citable from wherever the operator wants to reference it next.
- Option B (`docs/HIDDEN_LEGACY_INVENTORY.md`, repo-root-level,
  standing): matches R5's own language ("so the operator can decide...
  from a single page instead of archaeology-per-incident") more
  literally — a repo-root document is easier for a FUTURE session to
  find without knowing which tranche produced it, and would sit
  alongside `docs/ERRATA.md`/`docs/ERRATA_EXECUTOR.md` as a third
  standing ledger with its own append-only convention (new entries as
  more disconnections surface, mirroring those two documents' own
  discipline).
- RECOMMENDED: Option B, on reflection — R5's own "single page" framing
  is about FUTURE discoverability, which a tranche-local document
  actively works against once this tranche's directory is no longer the
  first place a later session looks. Flagged as the one place this
  Decision sheet recommends AGAINST what was already delivered (A4) —
  the operator's words can keep the file where it is (cheap: a `git mv`
  and a header note in a later tranche) or confirm the `docs/`-level
  promotion; either way this is a small, reversible, zero-frozen-surface
  move, not blocking delivery of the file itself.

**F5 — should Item 1's tool ALSO re-check `HIDDEN_LEGACY_INVENTORY.md`'s own five items for a re-connection recommendation?**
- Option A (yes, add a fifth computation): scope creep against R4's own
  four named computations (frozen-surface contacts, reachability,
  consumers, disclosure summary) — R4 does not ask for a recommendation
  engine, and Out of scope already states this tranche makes no
  re-connection recommendation.
- Option B (no): Item 1 stays at the four computations R4 names.
- RECOMMENDED: Option B — R4's own text is the deciding measurement; nothing
  in the request asks the tool to grade `HIDDEN_LEGACY_INVENTORY.md`'s
  own entries.

## Budget

**Headline: ~755 lines of future `dr-plan-steps`/`dr-execute-step`
implementation work, forecast by item — verified as the sum of its own
itemization:**

| Item | Forecast (lines) | Basis |
|---|---|---|
| `tools/blast_radius.py` (CLI, four computations, typed result, exit classes, `--self-test` fixture) | 420 | comparable to `tools/diff_budget.py` (229 lines) scaled up for three additional computations (reachability's AST walk, consumer's four sub-checks, disclosure-summary generation) beyond diff_budget's single line-count computation — roughly 1.8x on three added computations |
| Mutation-proof tests (`tests/test_blast_radius.py`, three proofs named in Item 1) | 180 | comparable to `tests/test_diff_budget.py`'s own scope for a single-gate test file |
| `dr-spec-change` amendment (Checkpoint 1) | 25 | one procedure-step paragraph plus template-section wording, comparable to the existing diff-budget amendment's own size (`dr-spec-change` step 6, ~10 lines) doubled for the two sections (steps 3 and 4) it touches |
| `dr-ask-the-right-question` amendment (Checkpoint 2, second site) | 10 | one clause added to an existing bullet |
| `dr-execute-step` amendment (Checkpoint 3) | 20 | one additional command plus drift-handling paragraph inserted into the existing step 6, comparable to the existing diff-budget paragraph's own size |
| `docs/proposals/DETERMINISTIC_GATES_PREPLAN.md` new "Rung G6" section | 55 | comparable to the existing G1 rung's own section length (~17 lines) scaled for four named computations instead of one |
| `docs/map/INV-frozen-surfaces.md` new subsection + backfilled Traps entry for the 2026-08-09 incident | 45 | comparable to the existing "Diff budget gate (Rung G1)" subsection (~15 lines) plus one Traps entry at the file's own existing Traps-entry average length (~30 lines) |
| **Sum** | | 420+180+25+10+20+55+45 = **755** |

```
$ python3 -c "print(420+180+25+10+20+55+45)"
755
```

**This tranche's own artifact size** (distinct from the forecast above —
this is what was ACTUALLY produced this window): `REQUEST.md` (181
lines, already committed), `CENSUS.md`, `HIDDEN_LEGACY_INVENTORY.md`,
and this `SPEC.md` — four commits total across the tranche (REQUEST.md
already pushed; the remaining three files land in one commit closing
this window, per C6). Frozen surfaces touched: NONE (Frozen-surface
contact forecast section above). `tools/` and `src/` lines changed this
window: zero (DESIGN-AND-STOP, C3).

Rubric: 6/6 yes
- every R has a spec item with a machine-decidable accept: yes (S1-S9
  cover R1-R5 and C2-C7; R1/R4 covered jointly by S1/S2 since R4 is the
  detailed elaboration of R1's headline ask).
- blast-radius census pasted (or pasted-empty) and every hit classified:
  yes (four grep results, three MUST NOT MOVE / vacuous, one EXPECTED TO
  MOVE, all classified with reasoning).
- frozen-surface contact forecast recorded: yes (checked from scratch
  against all five surfaces plus frozen-adjacent individually; none).
- every mechanism the request names traced to code it actually reaches:
  yes — R4's named precedents (diff_budget.py's shape, the gates
  pre-plan's shape rules, the errata checkpoint pattern) were each
  verified against their actual source (M1, M4, CENSUS.md A3-A5) before
  being adopted as this design's own shape, not assumed from the
  request's own description of them.
- DESIGN-AND-STOP sections: yes — Measurements (M1-M7, plus CENSUS.md's
  own A/B sections cited throughout) and Options (F1-F5) both present,
  every option priced, every rejection or recommendation cites a
  measurement or a CENSUS.md case.
- nothing in the spec untraceable to an R/C/M number: yes (re-read pass
  performed; every item, fork, and assumption cites a number).

## Decision sheet — every open fork, priced as roads, with a recommendation

**Fork F1 — how should the tool tell whether a piece of code can actually run, versus just whether its name shows up somewhere?**
- Road A (a simple text search: does the target's name appear anywhere
  in the source): quick to build, but this is the SAME kind of check
  that already missed `property_designer`'s deadness for two whole
  tranches (`HIDDEN_LEGACY_INVENTORY.md` item 1) — the role's name
  appeared everywhere it needed to for the check to look satisfied, while
  the actual wiring to reach it was broken underneath.
- Road B (trace the real call chain — who calls this, and does THAT
  caller ever get called, all the way back to something the harness
  actually runs): costs more to build, but it is the same trace a person
  did by hand, three tranches too late, when this exact gap was
  discovered live (`HIDDEN_LEGACY_INVENTORY.md` item 1). Reports "I
  can't tell" honestly rather than guessing when the code takes a path
  too dynamic to trace automatically (a string looked up at
  run time, for instance).
- **Recommendation: Road B.** It is the only option that would have
  actually caught the incident it exists to prevent.

**Fork F2 — should this new check get its own brand-new rulebook, or join the one that already exists?**
- Road A (add one new section to the existing "deterministic gates"
  plan, which already lists five related checks and says in so many
  words that a sixth one needs exactly a recorded incident plus your own
  go-ahead — both of which this tranche supplies): reuses machinery
  already in place; one document grows by one section.
- Road B (write an entirely separate plan from scratch): avoids touching
  the existing document, but duplicates its ground rules and ignores
  that document's own invitation for exactly this situation.
- **Recommendation: Road A.**

**Fork F3 — how far should the "you must show your work before asking for permission" rule reach, right now?**
- Road A (apply it everywhere two specific places in the workflow ask
  the operator for permission on something risky — the two places the
  evidence in this tranche actually points to): matches what the record
  shows went wrong; buildable and testable within this one tranche.
- Road B (apply it to every place in the whole workflow that ever asks
  for permission on anything): broader safety net, but nothing in this
  tranche's evidence shows those OTHER places have actually failed this
  way — building for a failure that hasn't been observed is a guess, not
  a fix.
- **Recommendation: Road A**, with Road B named as a natural next step
  once this one has run for a while, not dropped.

**Fork F4 — where should the "what's been quietly disconnected" page live: inside this project folder, or as a standing, repo-wide reference next to the error ledgers?**
- Road A (leave it inside this tranche's own folder, as delivered):
  costs nothing extra now; matches how similar pages already work
  elsewhere in this repo.
- Road B (promote it to sit alongside the repo's two existing running
  ledgers of "things that went wrong," as a third one — "things that got
  quietly disconnected"): matches the operator's own stated purpose for
  the page more closely — a single, easy-to-find spot for a FUTURE
  session that doesn't already know which folder to look in.
- **Recommendation: Road B** — moving it is a small, cheap, fully
  reversible follow-up (a file move plus a one-line note), not a reason
  to hold up delivering the page itself today.

**Fork F5 — should this same tool also tell the operator which disconnected pieces are worth reconnecting first?**
- Road A (yes, have it rank/recommend): more directly useful, but was
  never asked for, and grading old decisions is a different, larger job
  than disclosing new ones.
- Road B (no — just the four things actually asked for: which locked
  rooms it touches, what would go dark or come alive, who's using it,
  and a plain-language summary): stays inside what was actually
  requested.
- **Recommendation: Road B.**

Every road above awaits the operator's own words before any
implementation work (`dr-plan-steps`) begins, per C6/S8.
