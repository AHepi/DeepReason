# CHECKLIST — Rung 1

State: **all steps executed; see VALIDATION.md**

| # | Step | Done-criterion |
|---|---|---|
| 1 | Baseline root sweep before any edit | sweep output committed as `sweep-before.txt` |
| 2 | S1 + S2 — display seam and glosses | `display_status(ACCEPTED, *) == "unrefuted"`; `status_gloss` covers four labels |
| 3 | S3 — five renderer sites route through the seam | no `status.value` render left in `views/` |
| 4 | S4 — controller rename | `_under_standing_attack` absent from `src/` and `tests/` |
| 5 | S7 — regression tests | `tests/test_calculus_vocabulary.py` passes |
| 6 | Predicted fixture updates | the four assertions in `tests/test_text_authority_policy.py` updated, and only those |
| 7 | S5 — map document | `docs_verify --links` resolves `DR-CON-standing-and-background`; its checks run |
| 8 | S6 — CLAUDE.md design law | law present |
| 9 | [COMMIT] ring tests + diff budget + blast radius | ring green, diff under 300, zero frozen-surface contact |
| 10 | Full gate | `python -m pytest tests/ -q -n 4` — 0 failed |
| 11 | `docs_verify` full | 0 failed |
| 12 | Root sweep after | byte-identical to step 1 |
| 13 | VALIDATION.md + DELIVERY.md | acceptance checks A1–A10 each with pasted output |
