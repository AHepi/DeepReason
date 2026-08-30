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
| 5 | S5 — the ordinary worker-failure terminal records `TERMINAL_LIFECYCLE_NOT_TAKEN_FAILURE_TERMINAL` | its test passes, and the test drives `prepare_continuation` on a copy of the root it just made to prove the record's claim | DONE — the `continue_refusal` FIELD was dropped in the skeptic pass (step 18): it was a constant, and one of the 16 committed roots of that shape refuses with a different code |
| 6 | S6 — the no-harness failure terminal records `TERMINAL_NO_CHECKPOINT_WRITTEN` | its test passes, with `run-stop.json` and `checkpoint.json` asserted ABSENT | DONE |
| 7 | Ring #1 — the eleven files that consume the changed surfaces | **FAILED: 8 red, 1 predicted.** Three cannot be repaired as fixtures without changing an assertion. SPEC.md P-FIX-3(b) -> STOP and re-plan; the gate is reverted and parked | DONE — `proof/gate_collisions.md`, PARKED.md F9 |
| 8 | Preserve the gate's evidence as an instrument rather than as prose | `proof/forge_one_byte.py` re-derives the six-surface intact/forged table on demand; `proof/forge_one_byte.json` is its output | DONE |
| 9 | S7 — `results_summary` passes its computed verdict into `_terminal`; new `--verify` test | RED before (`assert True is False`), GREEN after; the six-key exact-set assertion unmoved | BUILT, then REVERTED at step 16 — its premise was S2, which never landed |
| 10 | S8 — the map moves in the same commit, and says what actually shipped | `SUB-amendment.md` restored to 22 codes (no gate); `CON-run-identity.md` carries the MEASURED blindness with a check that goes red if the gate lands and the Traps entry is not rewritten; `SUB-application.md` carries the two failure-terminal rows, the reader row, and the P6 entry rewritten | DONE |
| 11 | S9 — census and probes committed as re-runnable instruments | `proof/` holds five scripts, five JSON outputs, MEASUREMENTS.md and gate_collisions.md | DONE |
| 12 | Ring #2 — re-run after the revert and S7 | 0 failed | **1 failed, 193 passed** — this module's own control test, whose predicate flagged a tranche narrative document. Predicate narrowed, re-run green. The 0-failed criterion was met by ring #3 (VALIDATION S-RING3), not here |
| 13 | Frozen-surface tripwire and diff budget at every commit | the seven-path grep matches nothing; diff budget recorded (EXCEEDED -> parked as F8, decided above this lane) | DONE |
| 14 | VALIDATION.md — every SPEC acceptance check run, with its real output, including the ones that FAILED | every S1-S9 `accept:` line present with the command and what it actually produced | DONE |
| 15 | PARKED.md and DELIVERY.md; push at every phase boundary and the moment anything is parked | nine parked forks, each a ready-to-send prompt; DELIVERY.md stands alone | DONE |

## Skeptic pass, 2026-08-30 — eight confirmed findings, re-run by an
## independent reader against this lane's own claims

| # | step | done-criterion | state |
|---|---|---|---|
| 16 | Revert S7 (`results.py`, `test_results_command.py`) — it printed `amend_ready: no` on a forged root both verbs ACCEPT | both files byte-identical to `origin/main`; the false docstring premise ("since 2026-08-30 the ACTING verbs re-derive it") goes with them | DONE |
| 17 | Repair the byte-unchanged control: select roots from git's INDEX, not the filesystem | six arms against real git output, the four the old predicate missed now caught, the narrative-document control still green | DONE — `proof/control_predicate_arms.txt` |
| 18 | Drop the `continue_refusal` constant from S5's record | the field is absent, and the test still drives `prepare_continuation` and asserts the code it really raises | DONE |
| 19 | Make `CON-run-identity.md`'s numeric check RE-DERIVE | `forge_probe.py --witnesses` exits 0 on the delivered tree and exits 1 against a mutant that removes the pending-projection skip | DONE — both arms recorded in VALIDATION S-SKEPTIC |
| 20 | Measure the FULL jailbreak the S3 differential could not reach | on an `amend_ready` root, forged: `amend` ACCEPTED, `continue` ACCEPTED — committed as F9's acceptance target | DONE — `proof/forge_amend_ready.json` |
| 21 | Correct every stale or over-stated number in the committed reports | diff budget re-run at HEAD; MEASUREMENTS M4/M5 names its predicate; SUB-application's branch count and its "16 roots stop being silent" claim rewritten | DONE |
| 22 | Ring #4 and the two map documents' checks, after all of the above | 0 failed; `docs_verify` delta ZERO against the container baseline | DONE — VALIDATION S-RING4, S-DOCS2 |
