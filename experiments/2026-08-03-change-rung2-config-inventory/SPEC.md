# Spec for: rung 2, tranche 1 — buried choices become visible switches (inventory)
Traces: every item cites R/C numbers. Untraceable items are bugs.

Map preflight: `DR-INV-frozen-surfaces` (the "Where authority is allowed to
live instead" section, read in full this phase), `DR-SUB-manifest`,
`DR-CON-authority` (both already covered by rung 1's socket documents —
`CON-authority.md` already documents `ARGUMENTATIVE_AUTHORITY` as the
Config precedent this rung generalizes). No seam document join is created
or edited; this tranche writes zero `docs/map/` content (its deliverable
is an `experiments/` inventory, not a map document — see A3).

## Resolving Q1-Q3 (dr-ask-the-right-question applied; record first)

**Q1/Q2 (sweep scope: authority-shaped only, or general hard-coded
choices?).** Resolved from the record, no operator input needed. Two
independent textual signals both point the same way:
1. Rung 2's own words: "gather hard-coded behavior choices into named
   `Config` values" is the unqualified GOAL sentence. The
   `DR-INV-frozen-surfaces` citation immediately after it answers WHERE
   such choices belong (`config.py`), not WHAT counts — read in full,
   that section is one paragraph stating the general principle
   ("When a change needs a new per-run mode, put it on `Config`... This
   is the codebase's own precedent") and citing `ARGUMENTATIVE_AUTHORITY`
   as ONE illustration, not a scope boundary.
2. "The known first candidate: `engaged_criticism_policy`..." — "known
   FIRST candidate" is explicit: singular known example, not an
   exhaustive or defining one. A goal stated in general terms followed by
   "here is the first known instance" does not narrow the general term to
   match the instance's shape.

Dominance test: reading the scope as "authority-only" produces an
inventory of at most a handful of items (every genuinely authority-shaped
hard-coded value in the repo) and, if wrong, silently under-delivers what
rung 2's own text asks for ("hard-coded behavior choices," unqualified) —
an error the operator would have to notice and ask to be corrected, i.e.
NOT reversible at zero cost, since the report would look complete while
being scoped wrong. Reading it as "general, but practically bounded" (see
S1's methodology) costs more effort now but is reversible in the cheap
direction: if the operator wanted authority-only, they say so and the
extra candidates are simply not acted on (this is an inventory, not
switches — nothing is built from a candidate until a SEPARATE tranche
picks it). General-but-bounded wins. Recorded as **A1**.

**Q3 (inventory document format).** Resolved from the record: this is an
`experiments/` deliverable (a tranche artifact), not a `docs/map/`
document — `docs/map/SCHEMA.md`'s anatomy and check-per-claim rule do not
apply here (no `Verified-at:`/`Verify:`/`Owns:` header, no `check:` lines
required — this is inventory, not a load-bearing map claim). The
smallest reasonable format matching R2's literal words ("a map/code
pointer and current hard-coded value for each candidate") is one table
per logical group, each row: candidate name, file:symbol pointer, current
hard-coded value, one-line note on why it's a behavior choice. Recorded
as **A2**.

No reading above differs materially enough to warrant a stop — both
survive `dr-ask-the-right-question`'s dominance test as decidable from the
record. **Questions for operator: none.**

## Items

S1 (R1, R2, A1, A2): Create
`experiments/2026-08-03-change-rung2-config-inventory/INVENTORY.md`. The
sweep methodology (recorded here so it's auditable, not improvised at
execution time):

1. **Preset/policy-shaped files** — the same shape as the known example
   (a function or module that constructs a typed policy/preset object with
   literal values baked in): `src/deepreason/v6_policy.py`,
   `src/deepreason/runtime/launch_policy.py`,
   `src/deepreason/capabilities/policy.py`. Read each in full; list every
   hard-coded literal that gates a BEHAVIOR CHOICE (a mode, a policy
   value, a feature toggle) as opposed to structural/identity data (ids,
   digests, schema versions) or a value already sourced from `Config`.
2. **Rung 1's five socket areas** — `capture/schools.py`, `rules/conj.py`,
   `rules/crit.py`, `scheduler/scheduler.py`'s ranking, `authority.py` —
   cross-checked against their `docs/map/CON-*.md`/`SUB-*.md` documents
   (already written, rung 1) for any hard-coded literal not already a
   named `Config` field, since these are the sockets rungs 3-7 will build
   registries/switches around next.
3. **`config.py` itself, read in full** — to establish the baseline (what
   is ALREADY a Config knob, so candidates aren't duplicated) and to
   confirm the existing `ARGUMENTATIVE_AUTHORITY`-shaped precedent (three
   knobs already do exactly what rung 2 asks: `ARGUMENTATIVE_AUTHORITY`,
   `TEXT_RUBRIC_AUTHORITY`, `PAIRWISE_AUTHORITY`, `INFRASTRUCTURE_REVIEW_AUTHORITY`
   — these are NOT candidates, they are the model).

This is a bounded, best-effort sweep (three preset-shaped files plus the
five already-mapped sockets), not an exhaustive scan of all ~125k lines —
the smallest reading that still faithfully covers "hard-coded behavior
choices" per A1's reasoning above. Anything found outside this bound
during execution is still recorded (a sweep that stops looking the moment
it hits its stated bound is honest about the bound, not blind past it);
the bound only sets where SYSTEMATIC search stops, not what gets ignored
if seen.

accept: `test -f experiments/2026-08-03-change-rung2-config-inventory/INVENTORY.md`;
the file contains at minimum one row for `engaged_criticism_policy`'s
`authority="observe_only"` (the known, named candidate) with its exact
file:line pointer and current value; every candidate row cites a real
`grep`-able file:symbol pointer (spot-checked, not merely asserted).

S2 (R3): Zero `src/` changes. accept:
`git diff --stat <tranche-base>..HEAD -- src/` empty.

S3 (R4): Tranche ends after the inventory is committed and pushed —
no further switch work, no rung 3. accept: process check at delivery
(DELIVERY.md explicitly states the stop and that tranche 2 — the
`engaged_criticism_policy` switch — is a separate, not-yet-opened
tranche).

S4 (R5-R8, tranche 2): explicitly deferred — separate tranche directory,
opened only after this tranche delivers and the operator (per rung 2's
own "further switches wait for the operator to pick them") confirms which
candidate(s) from the inventory to build next. Not specified further
here.

## Assumptions (operator may override)

A1 (Q1/Q2): the inventory sweep is general ("hard-coded behavior
choices"), not narrowed to authority-shaped values, but practically
bounded to preset/policy-shaped files plus rung 1's five mapped sockets
plus `config.py` itself as baseline — not an exhaustive scan of the whole
tree. See "Resolving Q1-Q3" for the full dominance-test reasoning.

A2 (Q3): inventory format is a plain `experiments/`-tranche Markdown
document (tables: candidate / pointer / current value / note), not a
`docs/map/SCHEMA.md`-anatomy document — this is not a load-bearing map
claim.

## Questions for operator

None.

## Out of scope (explicit)

- Rungs 3-7 (C5). Not requested this tranche.
- Tranche 2 (the `engaged_criticism_policy` switch itself) — R5-R8,
  explicitly a separate, later tranche per the operator's own split.
- An exhaustive, unbounded scan of every hard-coded constant in
  `src/deepreason/` (125k lines) — A1's bounded methodology is the
  smallest reasonable reading; a broader sweep is available on request.
- Picking which inventory candidate becomes the NEXT switch after
  `engaged_criticism_policy` — "further switches wait for the operator to
  pick them" (R4), not this tranche's decision.

## Budget

~1 file created (`INVENTORY.md`), 0 `src/` lines, 1-2 commits (write +
push, possibly a revision after self-review). Well under the 300-line
guideline. Frozen surfaces touched: none (docs-only, `experiments/` only,
zero `src/`).
