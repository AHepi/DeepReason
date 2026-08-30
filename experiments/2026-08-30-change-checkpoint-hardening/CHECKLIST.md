# CHECKLIST — checkpoint hardening (P2 law, limbs 2 and 3)

One step, one done-criterion, one line of evidence. Every command below is run
from `/home/user/dr-lanes/lane-A` with

    PYTHONPATH=/home/user/dr-lanes/lane-A/src

prefixed. MEASURED ENVIRONMENT FACT, recorded because it silently invalidates
every result taken without it: the editable install's `.pth` points at
`/home/user/DeepReason/src`, NOT at this worktree, so a bare `python -m pytest`
here tests the OTHER checkout. The first GREEN attempt of S1-S4 in this lane
failed for exactly that reason and no other.

| # | step | done-criterion | state |
|---|---|---|---|
| 1 | Read RECON-A, RECON-SHARED, SPEC.md; re-derive the facts the work depends on rather than trusting them | the S3 differential root's one-byte behaviour re-measured this session (`verify_root` -> `frozen-route`, `attempt-route`; `derive_terminal_authority` -> `current_valid_committed`) | DONE |
| 2 | Write `tests/test_checkpoint_hardening.py` (S3, S4, S5, S6) BEFORE any source change | 5 of 6 tests FAIL against the unfixed tree, each for the defect it names; the 6th (the byte-unchanged control) passes | DONE — `proof/RED-checkpoint-hardening.txt` |
| 3 | S1 — the CONTINUE integrity gate in `runtime/continuation.py`, last precondition, before the first write | `test_one_flipped_log_byte_turns_a_continue_into_a_typed_integrity_refusal` passes; the intact copy still reaches `CONTINUE_TYPED_STOP_REQUIRED` | DONE |
| 4 | S2 — the AMEND integrity gate in `_require_terminal_stop`, after the authority check | 23 `AmendmentError` codes, `AMEND_RECORD_NOT_VERIFIED` among them; `AMEND_NOT_AT_TERMINAL` keeps its three witnesses | DONE |
| 5 | S5 — the ordinary worker-failure terminal records `TERMINAL_LIFECYCLE_NOT_TAKEN_FAILURE_TERMINAL` | `test_a_failure_terminal_records_why_it_cannot_be_continued` passes, and the recorded `continue_refusal` is the code `continue` actually raises on that root | DONE |
| 6 | S6 — the no-harness failure terminal records `TERMINAL_NO_CHECKPOINT_WRITTEN` | `test_a_terminal_that_wrote_no_checkpoint_records_that_fact` passes, with `run-stop.json` and `checkpoint.json` asserted ABSENT | DONE |
| 7 | Ring #1 — the eight files that call `prepare_continuation`, plus amendment, results and error-catalogue | 0 failed beyond the ONE predicted fixture change (P-FIX-1) | DONE |
| 8 | P-FIX-1 — `tests/test_continuation.py`'s witness predicate gains one exclusion clause; the assertion is untouched | the test still demands the exact string `CONTINUE_TYPED_STOP_REQUIRED`; `assert witnesses` still guards an empty set | DONE |
| 9 | S7 — `results_summary` passes its computed verdict into `_terminal`; new `--verify` test | `tests/test_results_command.py` 0 failed; the six-key exact-set assertion unmoved | DONE |
| 10 | S8 — the map moves in the same commits: SUB-amendment (22->23), CON-run-identity (the gate rule + a Traps entry), SUB-application (two rows + the P6 rewrite) | every new/changed `check:` line exits 0 standalone; `tools/docs_verify.py` delta ZERO against the container's own baseline | DONE |
| 11 | S9 — census and probes committed as re-runnable instruments with MEASUREMENTS.md | `proof/` holds four scripts, four JSON outputs and MEASUREMENTS.md; `git status --porcelain --untracked-files=no experiments` empty | DONE |
| 12 | Ring #2 — re-run the full ring after S7/S8 | 0 failed | DONE |
| 13 | Frozen-surface tripwire and diff budget at every commit | the seven-path grep matches nothing; `git diff --stat` inside the ceiling | DONE |
| 14 | VALIDATION.md — every SPEC acceptance check run, with its real output | every S1-S9 `accept:` line present with the command and the output it actually produced | DONE |
| 15 | PARKED.md and DELIVERY.md; push at every phase boundary and the moment anything is parked | seven parked forks each a ready-to-send prompt; DELIVERY.md stands alone | DONE |
