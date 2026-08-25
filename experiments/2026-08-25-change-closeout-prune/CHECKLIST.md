# CHECKLIST — close-out prune

State: OPEN

| # | step | done-criterion | req | done |
|---|---|---|---|---|
| 1 | Record pre-state: directory count, KEEP/delete sets, per-file shas for the 18 EXTRACT `PARKED.md` files | `proof/pre-state.txt` shows 152 directories and 18 shas | R2 | [x] |
| 2 | STAGE 1 — build `experiments/OPEN_PARKS.md` by byte-copying every open park item from the 18 EXTRACT directories | file exists; item count == 71 (audit's 60 corrected); every row carries tranche + sha | R2 | [x] |
| 3 | Prove AC2: extracted text is byte-identical to source, nothing summarized | `proof/extraction-fidelity.txt`: 71/71 byte-identical, 0 uncovered lines | R2 | [x] |
| 4 | Commit + push stage 1 BEFORE any deletion | `git log -1` shows the stage-1 commit; push succeeded | R1 | [ ] |
| 5 | STAGE 2 — `git rm -r` the 70 directories | 70 removed; `ls -d experiments/*/` == 83 (82 KEEP + 2 tranche dirs - 1) | R3 | [ ] |
| 6 | Prove AC4: all 82 KEEP directories still present | `proof/keep-intact.txt` reports 82/82, 0 missing | R4 | [ ] |
| 7 | Prove AC7/AC8: nothing outside `experiments/` changed; the 13 P5 docs files untouched | `git status --porcelain -- src/ tests/ docs/ tools/ scripts/ .claude/` empty; 13/13 docs present | R3 | [ ] |
| 8 | GATE A — `python tools/docs_verify.py` FULL mode | `proof/gate-docs-verify.txt`: 3 failed, all `CON-run-identity` (baseline) | R5 | [ ] |
| 9 | GATE B — `python -m pytest tests/ -q -n 4` | `proof/gate-pytest.txt`: 0 failed | R5 | [ ] |
| 10 | Park the 26 dangling `docs/` citations as this tranche's P1 | `PARKED.md` carries the ready-to-send prompt and the 26-row list | A2 | [ ] |
| 11 | Commit + push stage 2 | push succeeded | R1 | [ ] |

Order note: steps 8 and 9 are the two instruments R5 names. They run
ONE AT A TIME (both fan out workers; running them together manufactures
failures — `dr-drive-harness` §5b).

Stop condition, from R5: either gate red on a non-baseline failure means
something load-bearing left the tree. Restore it, row it in
`experiments-census.md` as a KEEP the census missed, name which of
Q-E1..Q-E4 failed to catch it, and report — that is a real block.
