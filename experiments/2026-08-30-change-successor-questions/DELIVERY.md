# Delivered: successor questions — optional to propose, routed by pluggable destination, minting gated off-by-default

Branch: `claude/lane-b-stack-window-9teltn` (the pickup window's branch;
originally `claude/b2-lane-B` @ `fdfe8a6e4`). NINE commits since the SPEC
commit `3688713ee`, not two: four delivered the change (`6ce1f202f` the change
and the map, `b690b814b` a defect this tranche's own `docs_verify` found in it
plus VALIDATION.md, `3d0041010` and `fdfe8a6e4` two count corrections), and
five carry the adversarial audit this lane had never had and its repairs.

CORRECTED 2026-08-30 (audit F20): this header previously read "@ `b690b814b`
... Two commits", naming neither the delivered head nor the real count. The
commit that introduced that error is itself titled "DELIVERY head hash
correction".
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
to say what is now true and what did not change. SIX new test files carry 56
tests, and six mutation transcripts under `proof/` show each of the five
original files going red against the behaviour it guards; a seventh records the
one predicted fixture change. (As delivered this read five files and 42 tests;
the 2026-08-30 audit found three of those tests could not fail and one
deliverable had no guard at all, and the repair added fourteen tests and the
sixth file — see FINDINGS.md and the re-measurement section below.) Six map documents move in the same commit,
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
| R1 | "an optional field the LLM can fill in. Not enforceable." | done | `tests/test_successor_law_line.py` (12 tests, 4 pins, each now carrying a BEHAVIOURAL half beside its spelling half); `proof/law_line_pin1_red.txt` and `proof/law_line_pin2_red.txt` — note per audit F7 that the pin-1 transcript proves SPELLING only: its mutant reads no `successor_question` and moves no ranking. The behavioural rank, admission and status pins added 2026-08-30 are what actually close the law |
| R2 | "it goes to scratchpad by default, linked to the problem it was proposed under and visible by conjecturers" | done-with-assumption A1/A2/A3 — mechanism built and measured end to end; NO PRODUCTION DISPATCH SITE until Q3 | `tests/test_successor_questions.py` (9 tests, visibility measured through `plan_conjecture_context`); `proof/route_mutants_red.txt` |
| R3 | "must function like a plugin that allows for movement elsewhere as well" | done-with-assumption A5 | `tests/test_successor_registry.py` (13 tests); adding a row needs no consumer edit, mutation-proved in `proof/registry_modularity_red.txt` — but per audit F16 the plugin point is proven against a `_Selects` STUB, not against `deepreason.config.Config`, which forbids extra fields (`extra_forbidden`), so no run can SELECT a registered alternative until Q1's field lands |
| R4 | "build the wiring to mint ... Switch off by default" | done-with-assumption A5 — the road, the gate and the warning are built and proven; the per-run SWITCH is blocked on Q1 | `tests/test_successor_minting.py` (13 tests); `proof/minting_mutants_red.txt` |
| R5 | (standing C8) a minted problem must never outrank the seed question | done for the TIE, parked for STRICT (Q4) | `tests/test_successor_rank_tie.py` (4 tests, both selection modes; per audit F11 the LIVENESS_QUEUE arm was VACUOUS as delivered — it passed with that mode's seed term deleted — and the fixture now carries a successor whose id sorts BEFORE the seed, so each mode's term dies on its own deletion); `proof/rank_tie_red.txt` |
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
new checks: 24, counted mechanically —
`git diff 3688713ee..HEAD -- docs/map | grep -c '^+`check:'` -> 24
left stale: none — `Verified-at:` is `bc3175394` on all SEVEN touched documents,
a commit that actually contains the package, the tests and the documents, and
every check in all seven was re-run against it.

CORRECTED 2026-08-30 (audit F10, F30, F31, F35), and the correction is larger
than an arithmetic slip:

- The delivered figure was "17 (twelve in the new document, five across the
  five amended ones)". The total 17 was reproducible; the SPLIT was wrong in
  both components and right only by coincidence — the new document contributed
  NINE tool-visible checks, not twelve, and the amended documents eight, not
  five. The sentence also said "five amended" where six were amended.
- The reason the new document showed nine and not the fourteen it had written
  is that FIVE of its `check:` spans were INDENTED, and `tools/docs_verify.py`
  anchors the opener at column 0 and drops an indented one silently — no check,
  no error, as its own self-test asserts. Five claims read as authenticated and
  were not.
- All five now sit at column 0. Across the seven touched documents the count is
  now 110 spans written, 110 parsed, 110 passing, 0 dropped, 0 parse errors;
  `CON-successor-questions.md` alone carries 16, all of them run.

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

1. **Nothing in production calls `route`, `mint`, `minting_notices` or
   `unknown_destination_notices`.** The channel is built, tested and
   mutation-proved; its dispatch site is Q3's decision and the granted cone
   gives `rules/crit.py` OUTPUT SCHEMA ONLY. A live run today records the field
   and routes nothing. This is the single largest gap between "delivered" and
   "working", and it is one call site wide. Widened 2026-08-30 (audit F13):
   neither TYPED DISCLOSURE reaches anywhere either — not the operator's
   warning text on the minting gate, and not the unknown-destination fallback
   notice. Both functions return the right thing when called and nothing calls
   them. Q2 decides which road carries them, and neither road is built.
2. **One test is RED on this branch, by design** —
   `test_no_source_file_produces_a_successor_problem`. Its rewrite is S19,
   gated on Q5. The exact four-line edit is committed in PARKED.md as P9B-7.
3. **The diff budget verdict is EXCEEDED**, and by more than was declared.
   CORRECTED 2026-08-30 (audit F14): the delivered figure of "2486 insertions"
   is not reproducible by any invocation, and understates the overrun by about
   30% in the self-serving direction. SPEC.md makes EXCEEDED "a STOP and a
   re-plan", so the size of the overrun is exactly the number a reviewer prices
   that stop against. Re-derived with SPEC.md's own command:

       at the delivered head fdfe8a6e4 : 3222 insertions vs a 1169 ceiling
       at this head, after the audit    : 5829 insertions vs a 1169 ceiling

   The sub-figures were also stale: "the tests (1140 against an itemised ~490)"
   and "the new map document (183 against 98)" were the values at the FIRST
   implementation commit, and both had grown before delivery. The excess is
   DENSITY, not scope — no path outside the declared cone was touched, and the
   parked paths (`config.py`, `run_manifest.py`,
   `test_decommissioned_pipeline_stays_out.py`,
   `test_h1_no_spawn_from_refutation.py`, `INV-frozen-surfaces.md`) still all
   take a zero-line diff. The growth from 3222 to 5829 is the audit record
   itself (`FINDINGS.md`, 35 reproduced findings) plus the fourteen tests and
   the map repairs it forced. Recorded rather than trimmed.
4. **`minting_notices` is reachable but not in `__all__`.** SPEC.md's S6 pins
   `__all__` to six names and S17 calls `s.minting_notices`; both accepts are
   satisfied literally, with the notice helper bound as an ordinary module
   attribute beside the declared interface. The tension is the spec's, not the
   code's, and it is flagged here rather than resolved by editing either accept.
   Audit F29 found a worse problem beside it: `__init__.py` CLAIMED `__all__`
   was pinned by `tests/test_successor_registry.py` and no test pinned it —
   dropping two names left all 42 tests green. It is pinned now, and the
   comment says only what is true.
5. **`SpawnTrigger.SUCCESSOR`'s reachability direction changes** at this
   commit, exactly as SPEC.md's forecast predicted, because the trigger
   acquired its first producer. It is declared so it is not read as drift.

## The adversarial audit this lane never had, and its repair — 2026-08-30

`HANDOFF-lane-B.md` named the missing skeptic pass "the single most important
thing on this page". It ran in the pickup window: five independent lenses, each
in its own worktree, each RE-RUNNING this lane's claims rather than reading
them. 155 claims re-run, 33+ source mutations. **35 findings, every one
reproduced by the lens that raised it: 3 blocking, 20 major, 12 minor.** They
are recorded in full, with commands and output, in `FINDINGS.md`.

**The shipped CODE was clean. The PROOF of its cleanliness was not.** Every
penalty the skeptics constructed had to be added by them; none was already
there. What failed was this tranche's evidence.

The three blocking findings are one defect with three faces:
`tests/test_successor_law_line.py`, the artifact this document offers as proof
of the operator's "never penalized" law, was a set of SUBSTRING SEARCHES over
source text. A rank penalty (F1), an admission rejection written one call-frame
above the probed guard (F2) and a status flip from REFUTED to ACCEPTED (F3)
each changed real behaviour and each left all 42 tests green. All three are now
pinned behaviourally, beside the spelling pins rather than instead of them.

Re-measured on the repaired tree:

| | as delivered | after repair |
|---|---|---|
| successor test files | 5 | 6 |
| successor tests | 42 | 56 |
| `CON-successor-questions.md` checks written / run | 14 / 9 | 16 / 16 |
| checks across the seven touched documents, written / parsed | — | 110 / 110 |
| `Verified-at:` stamp | `3688713ee` (FALSE — the code did not exist there) | `bc3175394` |
| diff-budget insertions vs a 1169 ceiling | claimed 2486, really 3222 | 5829 |

Twenty-six of the 35 are repaired. What is NOT repaired, and why:

- **F12's root cause is an operator decision, not a defect.** No `Config` field
  exists for either successor switch, and `Config` forbids extras, so no real
  run can select an alternative destination or turn minting on. Adding the
  fields needs frozen surface 4 — question Q1. The registry and the map now
  DISCLOSE this instead of claiming otherwise; the switch still does not exist.
- **The Q3 and Q5 gaps are unchanged** — one dispatch site, one guard test.
- Nine findings are claim corrections applied in this document and
  VALIDATION.md rather than in code.

## Parked (not done, not promised)

See PARKED.md in full. Seven entries: the five-question operator decision block
(P9B-1..P9B-5), the strict-domination tranche (P9B-6), and the one red guard
test with its ready-to-apply edit (P9B-7).

recommended next: **Q3**. It is the only park that stands between a channel that
is proven and a channel that fires, and both of its roads are already priced.
