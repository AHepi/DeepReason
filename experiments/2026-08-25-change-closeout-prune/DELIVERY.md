# DELIVERY — close-out prune

Both stages of `experiments/2026-08-25-audit/PARKED.md` P4 are complete.
Both gates are at baseline. `VALIDATION.md` verdict: PASS.

## Requirement-by-requirement reconciliation

| req | the operator's requirement | delivered | evidence |
|---|---|---|---|
| **R1** | Do BOTH stages, in the stated order — stage 1 before stage 2 | **YES.** Stage 1 committed at `17fd726fb` before any `git rm` ran. | commit order in `git log` |
| **R2** | One registry `experiments/OPEN_PARKS.md`; every open item moved VERBATIM; each naming tranche + sha; "do not summarize" | **YES, and the count was wrong in the audit's favour.** 71 items, not 60 — see below. All verbatim: each item's exact byte block is a literal substring of the registry, and no non-blank line after any preamble falls outside an item. | `proof/extraction-fidelity.txt` |
| **R3** | Remove the 52 PRUNE + 18 EXTRACT directories | **YES, less one restored under R5.** 70 removed; `live_compare_2026-07-28` restored when both gates proved it load-bearing. Net 69. | `proof/r5-remedy.txt` |
| **R4** | Do not touch the 82 KEEP directories | **YES.** 82/82 present. | `proof/keep-intact.txt` |
| **R5** | Both gates; if red, restore + row as KEEP + name which question failed | **YES — and it fired.** First pass red on both. Restored, rowed KEEP at census row 143, named Q-E1 and explained why it was structurally incapable of catching it. Re-run: `docs_verify` 3 failed (all baseline), pytest 0 failed. | `proof/gate-*-rerun.txt` |
| **R6** | Do not report back unless a real block; report on completion | **HONOURED.** No mid-work report. The red gate was not escalated because R5 itself prescribed the remedy — the operator had pre-authorised exactly this path. | this document |

## Two things the operator should know, neither of them a request for a decision

**1. The park count was 71, not 60.** The audit counted with a regex
matching `P<n>` labels. Three of the eighteen files label items
differently — `2026-07-30-fix-sandbox-contract` carries `## D2a` and
`## D1a`, both full park entries, and D2a was parked *by explicit operator
instruction* ("Park D2a"). A label-based count would have deleted eleven
real items with their directories. The extraction used here is structural
— every heading below the title starts an item — and was verified two
ways. Nothing was lost. The audit's own artifacts still say 60; correcting
them is parked as **P2**.

**2. One directory came back.** `live_compare_2026-07-28` held the
smallest committed run root with no embedder stamp. A test finds that root
by enumerating `git ls-files experiments` and picking by size and
property — it never names the path, so the census's path grep had nothing
to find. Both gates caught it independently on the first pass. Restored,
rowed KEEP, and the method gap parked as **P3** with a proposed fifth
census question: *a directory holding a committed run root is KEEP by
default.*

## What `experiments/` looks like now

| | before | after |
|---|---|---|
| directories | 154 | **85** |
| committed run roots | 113 | 61 |
| open park items, findable in one file | 0 | **71** |

Every surviving directory survives for a machine-checkable reason: a test
opens it, a `docs/map` `check:` line executes against it, `src/`/`scripts/`/
`tools/` reads it, CLAUDE.md or a skill names it, or — now — it holds a
run root a selector may reach.

## Parked, not done

| | | route |
|---|---|---|
| P1 | 26 pruned directories still cited from `docs/` prose (chiefly ERRATA) | pair with the docs-prune tranche (audit P5) |
| P2 | the audit's artifacts still say 60 open parks; true count 71 | `dr-change-orchestrator` |
| P3 | Q-E1 is blind to dynamically-discovered run roots; proposed Q-E5 | `dr-change-orchestrator` |

P5 (the docs prune) was **not** run. "Both stages" named P4's two stages;
P5 has no stages, and the operator reserved the next instruction.

## Nothing is unrecoverable

Every one of the 69 removed directories exists in full at `6e64330fe`:

    git show 6e64330fe:experiments/<tranche>/<file>
