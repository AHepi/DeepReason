# CHECKLIST — close-out prune

State: OPEN

| # | step | done-criterion | req | done |
|---|---|---|---|---|
| 1 | Record pre-state: directory count, KEEP/delete sets, per-file shas for the 18 EXTRACT `PARKED.md` files | `proof/pre-state.txt` shows 152 directories and 18 shas | R2 | [x] |
| 2 | STAGE 1 — build `experiments/OPEN_PARKS.md` by byte-copying every open park item from the 18 EXTRACT directories | file exists; item count == 71 (audit's 60 corrected); every row carries tranche + sha | R2 | [x] |
| 3 | Prove AC2: extracted text is byte-identical to source, nothing summarized | `proof/extraction-fidelity.txt`: 71/71 byte-identical, 0 uncovered lines | R2 | [x] |
| 4 | Commit + push stage 1 BEFORE any deletion | commit `17fd726fb`, pushed | R1 | [x] |
| 5 | STAGE 2 — `git rm -r` the 70 directories | 70 removed; 154 -> 84 directories | R3 | [x] |
| 6 | Prove AC4: all 82 KEEP directories still present | `proof/keep-intact.txt`: 82/82, 0 missing | R4 | [x] |
| 7 | Prove AC7/AC8: nothing outside `experiments/` changed; the 13 P5 docs untouched | `proof/scope-intact.txt`: empty status, 13/13 present | R3 | [x] |
| 8 | GATE A — `python tools/docs_verify.py` FULL mode | `proof/gate-docs-verify.txt`: 3 failed, all `CON-run-identity` (baseline) | R5 | [ ] |
| 9 | GATE B — `python -m pytest tests/ -q -n 4` | `proof/gate-pytest.txt`: 0 failed | R5 | [ ] |
| 10 | Park the 26 dangling `docs/` citations as this tranche's P1 (plus P2, the 60-vs-71 count correction) | `PARKED.md` carries both ready-to-send prompts; `proof/dangling-docs-citations.txt` lists all 26 | A2 | [x] |
| 11 | Commit + push stage 2 | push succeeded | R1 | [ ] |

Order note: steps 8 and 9 are the two instruments R5 names. They run
ONE AT A TIME (both fan out workers; running them together manufactures
failures — `dr-drive-harness` §5b).

Stop condition, from R5: either gate red on a non-baseline failure means
something load-bearing left the tree. Restore it, row it in
`experiments-census.md` as a KEEP the census missed, name which of
Q-E1..Q-E4 failed to catch it, and report — that is a real block.
