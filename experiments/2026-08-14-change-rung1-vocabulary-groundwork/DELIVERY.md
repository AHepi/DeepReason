# DELIVERY — Rung 1: vocabulary and groundwork

Verdict: **DELIVERED.** VALIDATION.md PASS on all ten acceptance checks.
Rung 1 of the v2 calculus program is complete; **Rung 1b is not started**
(one rung per tranche).

## Requirement-by-requirement reconciliation

| # | Requirement (REQUEST.md) | Delivered | Where |
|---|---|---|---|
| R1 | `accepted` renders as `unrefuted` | YES | `status_display.py::display_status`, now profile-independent |
| R2 | stored labels never change | YES | enum untouched; `positions.accepted` untouched; two regressions pin both halves |
| R3 | every committed root replays byte-unchanged | YES | 107 roots compared, zero drift on all six fields |
| R4 | renderers route through the seam | YES | `views/{why,theory,evidence,export}.py`, pinned by a map check |
| R5 | mint `CON-standing-and-background.md` with checks that can fail | YES | five checks, all inside the 880 docs_verify runs |
| R6 | resolve the controller's "standing" collision | YES | `_under_unresolved_attack`, with its caller and test |
| R7 | ledger the signal-contract layering as a design law | YES | CLAUDE.md, "Operator design laws" |
| R8 | no new skill or workflow | YES | `.claude/` untouched |
| R9 | the map moves in the same commit as the code | YES | commit `534bdaf77` carries both |

## What changed, in one paragraph

Production code is **64 lines**. The display seam maps `accepted → unrefuted`
for every workload profile and gained `status_gloss`; five view renderers stopped
printing the enum value and route through the seam; `why()` gained an
ACCEPTED branch that shows the reader both vocabularies at once; the
controller's `_under_standing_attack` became `_under_unresolved_attack`. The
rest is a map document, a design law, and seven regressions.

## Findings this rung produced (beyond its own scope)

1. **"Standing" was already taken three times, in three senses, none of them
   the calculus's** — and the most dangerous one was user-facing: a text run
   rendered `accepted` as **"standing"**, the calculus's word for the frame-role
   axis Rung 4 introduces. The v2 tranche forecast one collision; there were
   three. Two are fixed, the third is parked with its reason.
2. **`display_status_counts` is persisted** into `progress.jsonl` and the
   text-run result. So the rendered vocabulary does reach disk for runs made from
   now on. No stored status moved — but a reader comparing progress files across
   roots will meet `standing` in older ones and `unrefuted` in newer ones. Written
   into the map document's Traps.
3. **The prediction record.** The SPEC predicted four fixture assertions; seven
   moved. Both misses were recorded at the moment they were found, in SPEC
   amendments, not after the fact. The lesson for Rung 1b: **specifying a code
   change is not specifying its fixtures** — every surprise was a consumer of the
   seam rather than a renderer, so none of them appeared in the renderer table.
4. **The diff budget EXCEEDED** (335 vs 300) and was raised to 350 with the
   census rather than met by trimming: production code was 64 lines, and the
   overage is a required map document plus regressions.

## Instruments, all run

| Instrument | Result |
|---|---|
| full gate | **3598 passed, 7 skipped, 0 failed** (13:53) |
| `docs_verify` full | 3 failed — **exactly** the recorded `AUDIT_BASELINES` shallow-clone baseline; 54 documents, 880 checks |
| `docs_verify --links` | 0 dangling, 54 documents |
| `root_sweep` (107 roots) | **zero verdict drift**; 11 ERROR lines = baseline |
| `blast_radius` | **CLEAR** — no frozen surface, no qualification digest, no wheel-smoke pin |
| `diff_budget` | 335 insertions; ceiling amended to 350 with the census |
| wheel smokes | **not required** — `wheel_smoke_pins` empty; no public surface touched |

## Next

**Rung 1b — the signal contract** (`LADDER.md`). It is unblocked: D-7 is
answered and its ledger half (the CLAUDE.md design law) landed here. Five v2
decisions remain open (D-1, D-3, D-4, D-5, D-6) plus D-8; none of them blocks
Rung 1b.
