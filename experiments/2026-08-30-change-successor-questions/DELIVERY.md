# Delivered: successor questions — optional to propose, routed by pluggable destination, minting gated off-by-default

Branch: `claude/b2-lane-B` @ `b690b814b` (pushed, tree clean). Two commits:
`6ce1f202f` carries the change and the map; `b690b814b` carries the fix for a
defect this tranche's own `docs_verify` run found in it, plus VALIDATION.md.
Tranche: `experiments/2026-08-30-change-successor-questions/`
Family: `dr-change-orchestrator`. Lane B of ultracode batch 2.

## What changed

A criticism can now propose the question it thinks should be asked NEXT, in one
optional field on both criticism output contracts, and a new package decides
what happens to that proposal. `src/deepreason/successor/` holds four small
modules: a VERSIONED registry of destinations and gates that carries no numeric
field at all; a router whose default destination writes one advisory scratch
block linked to the problem the question was proposed under; the ONE producer of
`SpawnTrigger.SUCCESSOR`, which is off unless a run switches it on and which
lives outside `src/deepreason/rules/` so that H1's deletion stays deleted; and a
package `__init__` that is the whole interface consumers may use. `signals.py`
declares the two receipt families with a real unit and a real staleness.
`ontology/problem.py`'s "INERT VOCABULARY: producers = 0" comment is rewritten
to say what is now true and what did not change. Five new test files carry 42
tests, and six mutation transcripts under `proof/` show each of those five files
going red against the behaviour it guards; a seventh records the one predicted
fixture change. Six map documents move in the same commit,
including a new `DR-CON-successor-questions` and its INDEX row.

Three of the operator's five parked questions are still open, and two of them
bound what could ship. Q1 (a frozen-surface-4 grant) means the two per-run
switches do not exist yet — the channel works on its shipped defaults instead,
because `resolve` and `minting_enabled` read their selector by `getattr`. Q3
(may the criticism side write to the workshop) means NOTHING IN PRODUCTION CALLS
THE ROUTER YET: the road is built and proven, and its one dispatch site is
exactly what Q3 decides. Q5 (the scope of a superseded ruling) means one guard
test is left RED on purpose rather than rewritten by an implementer.

## Reconciliation

| R | Operator's words (short) | Disposition | Proof |
|---|---|---|---|
| R1 | "an optional field the LLM can fill in. Not enforceable." | done | `tests/test_successor_law_line.py` (8 tests, 4 pins); pins 1 and 2 mutation-proved in `proof/law_line_pin1_red.txt`, `proof/law_line_pin2_red.txt` |
| R2 | "it goes to scratchpad by default, linked to the problem it was proposed under and visible by conjecturers" | done-with-assumption A1/A2/A3 — mechanism built and measured end to end; NO PRODUCTION DISPATCH SITE until Q3 | `tests/test_successor_questions.py` (9 tests, visibility measured through `plan_conjecture_context`); `proof/route_mutants_red.txt` |
| R3 | "must function like a plugin that allows for movement elsewhere as well" | done | `tests/test_successor_registry.py` (10 tests); adding a row needs no consumer edit, mutation-proved in `proof/registry_modularity_red.txt` |
| R4 | "build the wiring to mint ... Switch off by default" | done-with-assumption A5 — the road, the gate and the warning are built and proven; the per-run SWITCH is blocked on Q1 | `tests/test_successor_minting.py` (12 tests); `proof/minting_mutants_red.txt` |
| R5 | (standing C8) a minted problem must never outrank the seed question | done for the TIE, parked for STRICT (Q4) | `tests/test_successor_rank_tie.py` (3 tests, both selection modes); `proof/rank_tie_red.txt` |
| R6 | "maximum configurable surface ... none is a code edit" | done-with-assumption A5 — destination is re-aimable by registration + one selector; the selector FIELD is blocked on Q1 | `tests/test_successor_registry.py::test_adding_a_destination_requires_no_edit_to_any_consumer` |

## Assumptions the operator may override

A1: "goes to scratchpad" = one ordinary scratch block via
`ScratchService.create_block`, body `{content, unfinished: "Successor
question"}` — the shape `scratch/authoring.py` already uses for an unresolved
question.

A2: "linked to the problem it was proposed under" = `ScratchProvenanceV1.origin`
carries the problem id. It is a free string outside `body_hash`, so the link
costs no stored block id.

A3: "the problem it was proposed under" = the first problem the criticised
target addresses, which is the same frame the criticism pack leads with.

A4: the shipped default destination row id is `scratchpad.v1`.

A5: a per-run flag is a `Config` field, not a manifest field — and until Q1 is
answered there is no field at all, so the defaults are read by `getattr` and a
run cannot change them.

A6: the minted problem id keeps the historical `succ:` prefix.

A7: "never outrank" is taken as the rank-TIE guarantee. Q4 asks whether the
operator meant strict domination; nothing here forecloses that answer.

A8: the criticism pack is NOT told the field exists by a new pack parameter.
"Not enforceable" reads against an invitation, and the pinned pack signatures
would make one a seam change.

## Map delta

changed: `docs/map/CON-criticism-source.md`,
`docs/map/CON-problem-layer-lifecycle.md`,
`docs/map/CON-scheduler-ranking.md`, `docs/map/SEAM-ontology-x-rules.md`,
`docs/map/SEAM-rules-x-scratch.md`, `docs/map/INDEX.md`
created: `docs/map/CON-successor-questions.md`
new checks: 17, counted mechanically —
`git diff 3688713ee..HEAD -- docs/map | grep -c '^+`check:'` -> 17 (twelve in the new document, five across the five amended ones)
left stale: none — `Verified-at:` was advanced on all six to the commit their
checks were re-run against, and the re-run output is pasted in VALIDATION.md.

Two map claims were CORRECTED rather than merely extended, and both were
already false before this tranche:
`CON-problem-layer-lifecycle.md`'s Traps entry asserted that "`scan_spawns`
mints a SUCCESSOR problem for every REFUTED artifact", describing a loop
deleted at Rung 3a; and the same document's H1 stated an unqualified "translate
is the only path that mints a problem". Neither Traps entry was deleted; both
were rewritten to say what is true and when it stopped being true, per the
never-delete-a-Traps-entry rule.

## Errata

errata: none. The two corrected map claims are recorded in the documents that
carried them (above), which is where a map correction belongs; neither is a
correction to a committed CLAIM about a run, which is what `docs/ERRATA.md`
ledgers.

## The residue, stated plainly

1. **Nothing in production calls `route` or `mint`.** The channel is built,
   tested and mutation-proved; its dispatch site is Q3's decision and the
   granted cone gives `rules/crit.py` OUTPUT SCHEMA ONLY. A live run today
   records the field and routes nothing. This is the single largest gap between
   "delivered" and "working", and it is one call site wide.
2. **One test is RED on this branch, by design** —
   `test_no_source_file_produces_a_successor_problem`. Its rewrite is S19,
   gated on Q5. The exact four-line edit is committed in PARKED.md as P9B-7.
3. **The diff budget verdict is EXCEEDED** — 2486 insertions against SPEC.md's
   ceiling of 1169. The excess is DENSITY, not scope: no path outside the
   declared cone was touched, and the parked paths (`config.py`,
   `run_manifest.py`, `test_decommissioned_pipeline_stays_out.py`,
   `test_h1_no_spawn_from_refutation.py`, `INV-frozen-surfaces.md`) all take a
   zero-line diff. It lands in the tests (1140 insertions against an itemised
   ~490) and in the new map document (183 against 98), because every claim in
   this tranche carries a mutation transcript and the estimate did not price
   those. Recorded rather than trimmed: cutting tests to fit a line estimate
   would trade the thing the tranche is for against the thing it is measured by.
4. **`minting_notices` is reachable but not in `__all__`.** SPEC.md's S6 pins
   `__all__` to six names and S17 calls `s.minting_notices`; both accepts are
   satisfied literally, with the notice helper bound as an ordinary module
   attribute beside the declared interface. The tension is the spec's, not the
   code's, and it is flagged here rather than resolved by editing either accept.
5. **`SpawnTrigger.SUCCESSOR`'s reachability direction changes** at this
   commit, exactly as SPEC.md's forecast predicted, because the trigger
   acquired its first producer. It is declared so it is not read as drift.

## Parked (not done, not promised)

See PARKED.md in full. Seven entries: the five-question operator decision block
(P9B-1..P9B-5), the strict-domination tranche (P9B-6), and the one red guard
test with its ready-to-apply edit (P9B-7).

recommended next: **Q3**. It is the only park that stands between a channel that
is proven and a channel that fires, and both of its roads are already priced.
