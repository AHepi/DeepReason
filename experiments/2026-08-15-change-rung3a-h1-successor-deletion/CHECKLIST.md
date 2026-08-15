# CHECKLIST — Rung 3a

State: **complete.** Full gate 3644 passed / 0 failed; docs_verify full at the 3-failure baseline.

| # | Step | Done-criterion | State |
|---|---|---|---|
| 1 | T1 — remove the refuted⇒successor loop from `scan_spawns` | the branch is gone; `scan_spawns` still compiles and every other trigger's code path is untouched | ✅ |
| 2 | T2 — correct the enum member's comment; KEEP the member | `SpawnTrigger.SUCCESSOR` still parses; its comment no longer claims a failed verdict produces it | ✅ |
| 3 | T3 — the regression (B1) and its sibling (B2) | both pass; the sibling proves the frontier still grows by every other route | ✅ |
| 4 | T4 — the mutation proof (B3) | the reinstated loop makes B1's assertion fail, proven in-process | ✅ |
| 5 | B4/B5 — addressability and the surviving producer | no problem loses criteria or lineage; `easy.py`'s repair path still mints its problem | ✅ |
| 6 | Fix the fallout in existing tests | every test that asserted a successor is spawned by refutation is re-founded, not weakened | ✅ |
| 7 | T5 — map moves in the same commit | `docs_verify` full at the 3-failure baseline | ✅ |
| 8 | T6 — errata E29, E30 | both minted against a freshly re-checked ledger tail | ✅ |
| 9 | **[COMMIT]** the gate | full gate 0 failed; diff budget measured | ✅ |
| 10 | VALIDATION.md + DELIVERY.md + PARKED.md | R-by-R reconciliation; the `easy.py` question parked with a ready-to-send prompt | ✅ |
