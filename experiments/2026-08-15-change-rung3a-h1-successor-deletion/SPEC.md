# SPEC — Rung 3a: delete the successor spawn trigger

Traces to REQUEST.md N1–N8. **Diff budget: 260 lines** — production 40,
tests 140, map + errata 80. Deliberately small: "alone" is the requirement.

## The finding that re-decides the enum, before anything else

The ladder said this rung would remove the branch **and delete
`SpawnTrigger.SUCCESSOR` from the enum**, re-chosen under the 2026-08-14 law
against the external advice's recommendation to keep it. **That is now
withdrawn on evidence.** A census of the tree found a SECOND, LIVE producer of
successor problems that has nothing to do with `scan_spawns`:

    easy.py::seed_component        {"trigger": "successor", "from": [repair_of]}
    workflows/website.py:1643,1717 the two live call sites that pass repair_of

Deleting the enum member therefore does not "make the vocabulary match the
behaviour" — it breaks the staged website pipeline's repair path, and fixing
that would drag a whole subsystem into a tranche the operator said must ship
ALONE (N8).

So: **the branch goes, the enum stays.** The advice's recommendation lands, but
for a stronger reason than the advice gave: it argued from old-root parsability,
which the 2026-08-14 law had already retired; the real reason is a live
producer, which nobody had counted. The ladder's paragraph overruling the advice
is corrected in the same commit, because leaving it would leave a plan that
contradicts the tree.

`check: grep -q '"trigger": "successor"' src/deepreason/easy.py && grep -c "repair_of=" src/deepreason/workflows/website.py`

## Is `easy.py`'s repair-successor a SECOND H1 site? — PARKED, not decided here

It is the same shape: something fails (integration criticism implicates a
component), and a problem is minted from that failure. Whether H1 reaches into
the staged website workflow is a real question and it is **the operator's**, not
this tranche's — H1 was stated about the reasoning loop's failed verdict, and
answering it either way here would break N8. Parked with a ready-to-send prompt.

## Changes

| # | Change | R |
|---|---|---|
| T1 | Remove the refuted⇒successor `for` loop from `scan_spawns`. Nothing else in that function moves. | N1 |
| T2 | `SpawnTrigger.SUCCESSOR` KEPT, with its comment corrected: it no longer means "failed verdict (P2)" — no failed verdict produces one. It now records what still does. | the finding above |
| T3 | The regression, verbatim from the advice, plus the sibling that proves the frontier still GROWS by every other structural route. | N2, N4 |
| T4 | The mutation proof: a test that reinstates the deleted loop in-process and asserts the regression FAILS against it. | N3 |
| T5 | Map: `SUB-rules.md`'s successor-inheritance row and `SEAM-ontology-x-rules`' nesting check, in the same commit. | N6 |
| T6 | Errata E29 and E30. | N7 |

## Acceptance checks

| # | Check |
|---|---|
| B1 | Refuting an addressed candidate and re-running `scan_spawns` leaves `state.problems` byte-identical |
| B2 | The same run still spawns connection, discrimination, debt and remove-arbitrariness problems — the frontier grows by every route except refutation |
| B3 | **Mutation:** the old loop, reinstated in-process, makes B1 fail. A regression that cannot fail is not one |
| B4 | Every problem addressable before the change is addressable after (N5) — no criteria, no lineage, no provenance root is lost, because the deleted successor only ever copied its parent's criteria |
| B5 | `SpawnTrigger.SUCCESSOR` still parses and `easy.py`'s repair path still mints its problem |
| B6 | Full gate 0 failed; `docs_verify` full at the recorded 3-failure baseline; map moved in the same commit |

## What this rung does NOT do

Frame-separation (Rung 3b), problem subjects, P4, proof debt. And it does not
touch `easy.py`. N8 is the requirement, not a preference: the operator said
alone, the advice said "the first code tranche should do ONLY this", and the
reason both say it is that H1's deletion is the precondition for everything
after it — a precondition that ships mixed with other work is a precondition
nobody can point at.
