# DELIVERY — Rung 3a: the successor spawn trigger is deleted

| # | Requirement | State | Where |
|---|---|---|---|
| N1 | The refuted⇒successor branch is REMOVED from `scan_spawns` | **DONE** | `rules/spawn.py` — 25 lines out, a 6-line comment in saying why the absence is the design |
| N2 | The advice's decisive regression | **DONE** | `tests/test_h1_no_spawn_from_refutation.py::test_refutation_alone_cannot_grow_the_problem_frontier` |
| N3 | A MUTATION proof | **DONE** | `::test_the_regression_would_catch_the_old_loop` — the deleted loop restored in-process, and the frontier grows again |
| N4 | Every other structural trigger still fires | **DONE** | `::test_every_other_structural_trigger_still_fires`, plus the re-founded `test_multi_cycle_spawns_and_persistence` |
| N5 | No addressability lost | **DONE** | the successor only ever copied its parent's criteria under a new id |
| N6 | Map moves in the same commit | **DONE** | `SUB-rules.md`, `SEAM-ontology-x-rules.md`, `SEAM-rules-x-scratch.md` |
| N7 | Errata for the falsified spec sentences | **DONE** | `docs/ERRATA.md` E29 (harness-spec §3 + §7) and E30 (COMPUTABLE_CALCULUS §5 + §9.6) |
| N8 | **ALONE** | **HELD** | no frame-separation, no problem subjects, no P4, no `easy.py`. The one thing that tempted a widening is parked, not done |

## The decision this rung reversed, and why

The ladder said to delete `SpawnTrigger.SUCCESSOR` as well, and overruled the
external advice for recommending it be kept. **Withdrawn on evidence.** A census
found a live producer outside `scan_spawns` — `easy.py::seed_component`, called
with `repair_of` from two sites in `workflows/website.py` — so deleting the
member breaks the staged pipeline's repair path.

The reusable half of the mistake, recorded in the ladder and struck rather than
removed: the overruling argument was sound about the law (old roots really are
owed nothing) and simply never asked whether anything CURRENT still produced the
value. **A compatibility question and a liveness question look alike and are
not**, and only one of them survives a law that retires compatibility.

## What is next

Not decided here. The board, unchanged by this rung except that its first item
is now done: problem subjects and the closed claim substrate, then P4, then A19
behind it. `PARKED.md` P1 — whether H1 reaches the staged pipeline — is the
operator's, and it is the only thing that would let the enum member go.
