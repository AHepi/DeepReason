# CHECKLIST — checkpoint hardening (P2 law, limbs 2 and 3)

One step, one done-criterion. Every command below is run from
`/home/user/dr-lanes/lane-A` with

    PYTHONPATH=/home/user/dr-lanes/lane-A/src

prefixed. MEASURED ENVIRONMENT FACT, recorded because it silently invalidates
every result taken without it: the editable install's `.pth` points at
`/home/user/DeepReason/src`, NOT at this worktree, so a bare `python -m pytest`
here tests the OTHER checkout. The first GREEN attempt in this lane failed for
exactly that reason and no other.

| # | step | done-criterion | state |
|---|---|---|---|
| 1 | Read RECON-A, RECON-SHARED, SPEC.md; re-derive what the work depends on | the S3 differential root's one-byte behaviour re-measured (`verify_root` -> `frozen-route`, `attempt-route`; `derive_terminal_authority` -> `current_valid_committed`) | DONE |
| 2 | Write `tests/test_checkpoint_hardening.py` BEFORE any source change | 5 of 6 tests FAIL against the unfixed tree, each for the defect it names | DONE — `proof/RED-checkpoint-hardening.txt` |
| 3 | S1 — the CONTINUE integrity gate | the one-byte differential passes: intact -> `CONTINUE_TYPED_STOP_REQUIRED`, forged -> `CONTINUE_RECORD_NOT_VERIFIED` | BUILT, then REVERTED at step 7 |
| 4 | S2 — the AMEND integrity gate | 23 `AmendmentError` codes; forged root -> `AMEND_RECORD_NOT_VERIFIED` | BUILT, then REVERTED at step 7 |
| 5 | S5 — the ordinary worker-failure terminal records `TERMINAL_LIFECYCLE_NOT_TAKEN_FAILURE_TERMINAL` | its test passes, and the recorded `continue_refusal` is the code `continue` actually raises on that root | DONE |
| 6 | S6 — the no-harness failure terminal records `TERMINAL_NO_CHECKPOINT_WRITTEN` | its test passes, with `run-stop.json` and `checkpoint.json` asserted ABSENT | DONE |
| 7 | Ring #1 — the eleven files that consume the changed surfaces | **FAILED: 8 red, 1 predicted.** Three cannot be repaired as fixtures without changing an assertion. SPEC.md P-FIX-3(b) -> STOP and re-plan; the gate is reverted and parked | DONE — `proof/gate_collisions.md`, PARKED.md F9 |
| 8 | Preserve the gate's evidence as an instrument rather than as prose | `proof/forge_one_byte.py` re-derives the six-surface intact/forged table on demand; `proof/forge_one_byte.json` is its output | DONE |
| 9 | S7 — `results_summary` passes its computed verdict into `_terminal`; new `--verify` test | RED before (`assert True is False`), GREEN after; the six-key exact-set assertion unmoved | DONE — `proof/RED-results-verify.txt`, `proof/GREEN-results-verify.txt` |
| 10 | S8 — the map moves in the same commit, and says what actually shipped | `SUB-amendment.md` restored to 22 codes (no gate); `CON-run-identity.md` carries the MEASURED blindness with a check that goes red if the gate lands and the Traps entry is not rewritten; `SUB-application.md` carries the two failure-terminal rows, the reader row, and the P6 entry rewritten | DONE |
| 11 | S9 — census and probes committed as re-runnable instruments | `proof/` holds five scripts, five JSON outputs, MEASUREMENTS.md and gate_collisions.md | DONE |
| 12 | Ring #2 — re-run after the revert and S7 | 0 failed | DONE |
| 13 | Frozen-surface tripwire and diff budget at every commit | the seven-path grep matches nothing; diff budget recorded (EXCEEDED -> parked as F8, decided above this lane) | DONE |
| 14 | VALIDATION.md — every SPEC acceptance check run, with its real output, including the ones that FAILED | every S1-S9 `accept:` line present with the command and what it actually produced | DONE |
| 15 | PARKED.md and DELIVERY.md; push at every phase boundary and the moment anything is parked | nine parked forks, each a ready-to-send prompt; DELIVERY.md stands alone | DONE |
