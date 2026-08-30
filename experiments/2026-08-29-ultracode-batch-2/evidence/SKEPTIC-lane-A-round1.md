# Skeptic verdict — lane A, first pass (rescued from a stopped workflow)

This verdict COMPLETED inside the A/B workflow that was stopped on 2026-08-30
when the operator removed lane B from this session. It audits LANE A. It is
committed here because it is real verification output that otherwise existed
only inside a container, which is precisely the loss batch 1 recorded.

Lane A's repair pass must dispose of every finding below, not only the
findings from the relaunched skeptic round.

## agent aa840373536b586ab — verdict DEFECTS_FOUND, 9 findings

### 1. [major] S7 does not only tighten `results --verify`; it LOOSENS it on real committed roots, and the tranche never records that direction. On roots whose stored REPLAY_VALIDATION.json says `valid: false` but which re-derive as VALID, `deepreason results --verify` now reports `valid_typed_terminal: true` where before the change it reported `false`. Consequently the headline census number carried into a committed map document — CON-run-identity.md's new Traps entry, "16 of 59 committed roots pass amend's entire precondition while their own REPLAY_VALIDATION.json publishes valid: false", and the same 16 used as SPEC.md S4's witness population for the parked gate — is computed from the STORED verdict, which is precisely the authority S7 exists to stop trusting. At least 2 of those 16 are not gate-relevant at all.

PROOF (the command the skeptic ran, and its real output):

```
cd /home/user/dr-lanes/lane-A && PYTHONPATH=.../src python <compare results_summary(root) vs results_summary(root, verify=True) on the 3 smallest A2-gap roots>

run-e542c3c1fc266943e0260c5aa8d7c107
   stored   valid= False  valid_typed_terminal=False
   rederived valid=  True  valid_typed_terminal=True
   CHANGED: True
run-9a6be78e1e79184a0bd89923b957586c
   stored   valid= False  valid_typed_terminal=False
   rederived valid= False  valid_typed_terminal=False
   CHANGED: False
run-d17935a4bf5ffa67c7f6e67b9a637a00
   stored   valid= False  valid_typed_terminal=False
   rederived valid=  True  valid_typed_terminal=True
   CHANGED: True

That the flip is caused by S7 is shown by the same mutation that proves the S7 test: restoring `valid_terminal = bool(replay and replay.get("valid") and has_binding)` makes `_terminal` answer from `replay` again, so under --verify these roots read False as they did before the change (`1 failed, 25 passed` on tests/test_results_command.py, `assert True is False` at :533). Both are on the SAME 16-root list the map document cites: `python -c "import json; c=json.load(open('.../proof/census.json')); print(len(c['A2_gap_authority_valid_but_replay_invalid']))"` -> 16, and both names appear in it.
```

PROPOSED FIX: Either re-derive the A2 gap before publishing it (census.py computes `stored_replay_valid` only — add a re-derived column, even bounded by log length, and cite THAT number in CON-run-identity.md and in SPEC.md S4's witness population), or state in the Traps entry that 16 is the count of roots whose STORED verdict is false and that the re-derived count is unmeasured. Separately, record the permissive direction of S7 in DELIVERY.md's residue: `--verify` now promotes roots whose published verdict is stale.

### 2. [major] The shipped failure-terminal record hardcodes an unconditional typed claim about which refusal `continue` will raise, and that claim is false for one of the 16 committed roots of exactly the shape the record is written for. `text_runs.py` writes `continue_refusal="CONTINUE_TYPED_STOP_REQUIRED"` on every ordinary worker-failure terminal. DELIVERY.md and VALIDATION.md both assert "the record's claim is TRUE" / "the refusal the record CLAIMS is the refusal the verb actually raises", proven on one synthetic root only.

PROOF (the command the skeptic ran, and its real output):

```
cd /home/user/dr-lanes/lane-A && PYTHONPATH=.../src python <drive prepare_continuation on a tempdir COPY of each of the 16 `failed`/`operational_failure` roots in proof/census.json>

ValueError: CONTINUE_RESUME_RECOVERY_MISMATCH   <- experiments/2026-08-08-live-two-seat-ab-s6/home-s6/runs/failed-epoch1-run-8c77c6588485304d1f73416318c62949
ValueError: CONTINUE_TYPED_STOP_REQUIRED   <- (the other 15)

[('ValueError: CONTINUE_TYPED_STOP_REQUIRED', 15), ('ValueError: CONTINUE_RESUME_RECOVERY_MISMATCH', 1)]

That root is the S5 shape, not an outlier: run-result.json has state=failed, error_type=NonConjectureRecoveryAuthorityError, a `stop` record with schema/digest/event_seq (the ordinary branch's `_v6_run_result` payload), all six checkpoint files present, and one line in continuations.jsonl — so `prepare_continuation` takes the recovery branch and never reaches the `else: raise ValueError("CONTINUE_TYPED_STOP_REQUIRED")` at continuation.py:364.
```

PROPOSED FIX: Do not assert a refusal code the branch cannot know. Either omit `continue_refusal` and let the record state only the fact it owns (no STOPPED lifecycle receipt was taken), or derive the code at write time from the same predicate `prepare_continuation` uses (presence of a current resume decision), or extend the S5 test to a root carrying a continuation record so the generalisation is under test.

### 3. [major] The module's own control test, `test_committed_roots_are_byte_unchanged_by_this_module`, cannot see the two mutations that matter most. Its predicate keeps only `git status` paths whose OWN directory contains a `log.jsonl`, so every file inside a run root's subdirectories (`objects/`, `blobs/`, `run-stops/`) is invisible, and deleting a root's `log.jsonl` outright is invisible too (the `.exists()` guard filters the deletion out). The test is the tranche's only guard that committed evidence was not mutated in place.

PROOF (the command the skeptic ran, and its real output):

```
cd /home/user/dr-lanes/lane-A
# (a) mutate an object inside a committed root
R=experiments/2026-08-13-defect-controller-steering-inert/failed-epoch1-run-8e22d0431fd2b98d
F=$(git ls-files "$R/objects" | head -1); printf 'x' >> "$F"
git status --porcelain "$R"
 M experiments/.../failed-epoch1-run-8e22d0431fd2b98d/objects/artifact/04994bda...json
PYTHONPATH=.../src python -m pytest tests/test_checkpoint_hardening.py::test_committed_roots_are_byte_unchanged_by_this_module -q -p no:randomly
1 passed in 0.48s

# (b) delete the root's log.jsonl entirely
rm $R/log.jsonl; git status --porcelain "$R"
 D experiments/.../failed-epoch1-run-8e22d0431fd2b98d/log.jsonl
... -q -p no:randomly
1 passed in 0.52s

Control for both: the claimed mutation (one byte appended to log.jsonl) does fire —
1 failed ... AssertionError: a committed root moved: [' M experiments/.../log.jsonl']
Both roots were restored; `git status --porcelain` empty afterwards.
```

PROPOSED FIX: Select on the root, not on the file's own directory: mark a path as a root mutation when ANY ancestor directory up to the repo root contains `log.jsonl` (or match against the set of root directories `census.py` already derives from `git ls-files`), and drop the `.exists()` guard so a ` D ` status line still counts. Add both mutants to proof/RED-byte-unchanged-mutant.txt.

### 4. [minor] VALIDATION.md records `(exit 0)` for an S8 acceptance command that actually exits 1. The quoted command asserts `rows['undetected'] == 4`; `undetected` is a list, so the assertion is False. The check line that actually shipped in CON-run-identity.md uses `len(rows['undetected']) == 4` and does pass — so the tranche's recorded evidence for S8 is not the command that was run.

PROOF (the command the skeptic ran, and its real output):

```
cd /home/user/dr-lanes/lane-A
# VALIDATION.md's quoted S8 command, verbatim:
python -c "...; rows=json.loads(...forge.json...); assert rows['undetected'] == 4 and rows['population'] == 16"
Traceback (most recent call last):
  File "<string>", line 1, in <module>
AssertionError
exit=1
# the check line actually shipped in CON-run-identity.md:
python -c "...; assert len(rows['undetected']) == 4 and rows['population'] == 16 and rows['detected'] == 12"
exit=0
```

PROPOSED FIX: Replace the quoted command in VALIDATION.md with the check line as shipped (`len(rows['undetected']) == 4 ... and rows['detected'] == 12`), or re-run and record the real output.

### 5. [minor] The diff-budget figures recorded in VALIDATION.md (S-BUDGET) and DELIVERY.md do not reproduce at HEAD. Both record `tests 224, total_insertions 317`; the tool reports `tests 233, total_insertions 326`. The number was measured at commit 2650d3c87 and never re-measured after c930d26a9 added 9 test lines. The verdict is still WITHIN, and `src: 41` is correct.

PROOF (the command the skeptic ran, and its real output):

```
cd /home/user/dr-lanes/lane-A && python tools/diff_budget.py 84514a0280f45d29e5066bb3be3d273ba73798db --ceiling 400 --paths src tests docs/map
{"result_type": "DIFF_BUDGET_RESULT_V1", ..., "areas": {"src": 41, "tests": 233, "docs/map": 52}, "total_insertions": 326, "ceiling": 400, "verdict": "WITHIN"}

Provenance of the stale figure:
for c in 2650d3c87 c930d26a9 0ff9b8dc7; do git diff --numstat 84514a028 $c -- src tests docs/map | awk '{s+=$1} END {print s}'; done
317
326
326
```

PROPOSED FIX: Re-run `tools/diff_budget.py` at the delivered HEAD and update the S-BUDGET block in VALIDATION.md and the numbers table in DELIVERY.md to 41 / 233 / 52 / 326.

### 6. [minor] SPEC.md's "four populations" table states "Every root is in exactly one bucket" and lists 24 + 16 + 4 + 1 over 59 roots. The union of the four buckets is 44, not 45 — the F7 stranded root is counted both as `invalid_incomplete` and inside the 16 `failed`/`operational_failure` — and 15 roots sit outside the table, not the 13 the accompanying sentence claims.

PROOF (the command the skeptic ran, and its real output):

```
cd /home/user/dr-lanes/lane-A && python -c "<build the four buckets from proof/census.json and intersect them>"
bucket sizes 24 16 4 1 union 44
unbucketed: 15
OVERLAP b2 b4 ['experiments/live_research_2026-07-29/selfstudy/runs/failed-epoch2-run-9175f0ecb055e57455af3c50df153c5a']

MEASUREMENTS.md's own triples do sum correctly (23+16+13+4+1+1+1 = 59), so the error is in SPEC.md's table, not the census.
```

PROPOSED FIX: Either add the missing bucket rows (13 `completed`/`budget_exhausted`/amend_ready-false, 1 `running`/`budget_exhausted`, 1 `running`/`operational_failure`) and move the stranded root out of the 16, or drop the "exactly one bucket" sentence and label the table as a partial view.

### 7. [minor] The measured-blindness half of the new CON-run-identity.md `check:` cannot fail for the reason its prose gives. The Traps entry's load-bearing claim is about live behaviour — `derive_terminal_authority` still says `current_valid_committed` on a forged record, and a canonical forge of the stored verdict is undetected on 4 of 16 roots — but the check verifies that by reading the tranche's own committed `proof/forge.json`. The checking process imports no deepreason module at all, so fixing the blindness would leave the check green.

PROOF (the command the skeptic ran, and its real output):

```
cd /home/user/dr-lanes/lane-A && python -X importtime -c "<the CON-run-identity check line>" 2>&1 | grep -c "deepreason"
0

The entry's OTHER half is live and I mutation-proved it both ways:
printf '\n# verify_root\n' >> src/deepreason/runtime/continuation.py -> AssertionError: the integrity gate landed: REWRITE this Traps entry, never delete it (exit 1)
printf '\n# verify_root\n' >> src/deepreason/amendment/apply.py      -> same AssertionError (exit 1)
both reverted; git status --porcelain empty.
```

PROPOSED FIX: Make the numeric half re-derive rather than read: run `proof/forge_probe.py` (or an inlined single-root version of it) inside the check and compare its live result to 12/4, so a change in `derive_terminal_authority` turns the check red. Alternatively drop the numbers from the check and cite forge.json in prose only, so the check claims no more than it tests.

### 8. [minor] The S7 regression test carries an assertion that passes on the defective tree, and the specific harm named throughout the tranche is demonstrated nowhere. `assert rederived["terminal"]["amend_ready"] is False` is already True before the fix, because the chosen witness root has `stop_reason_resumable: false` and `continuation_authority: false`, so `amend_ready` is False on both paths. The docstring, SPEC.md S7, VALIDATION.md and DELIVERY.md all describe the defect as `--verify` printing `amend_ready: true` for a root `amend` refuses; no test exhibits that. The load-bearing assertion, `valid_typed_terminal`, IS mutation-proven.

PROOF (the command the skeptic ran, and its real output):

```
cd /home/user/dr-lanes/lane-A
# with _terminal reverted to the pre-S7 line, on the same tampered copy the test builds:
UNFIXED TREE (mutation C applied):
  stored   valid_typed_terminal = True  amend_ready = False
  rederived valid_typed_terminal = True  amend_ready = False
  test asserts rederived amend_ready is False -> True

census.json for that root confirms why:
{"amend_ready": false, "stop_reason_resumable": false, "continuation_authority": false, "valid_typed_terminal": true, "root": "experiments/2026-08-13-defect-controller-steering-inert/failed-epoch1-run-8e22d0431fd2b98d", ...}
```

PROPOSED FIX: Either drop the vacuous assertion, or pick/construct a witness with a resumable stop reason and continuation authority whose stored verdict is valid and re-derived verdict is not — then `amend_ready` flips True->False and the harm the docs name is under test.

### 9. [minor] A pre-registered prediction that the tranche itself recorded as WRONG was deleted with the revert, and the correction survives nowhere. SPEC.md P-FIX-4 predicted "tens of seconds, not minutes" of added gate time and instructed that "VALIDATION.md must record the measured before/after wall clock of the ring files rather than assert it". Commit 5fccb1e91 added `proof/RUNTIME.md` saying "That prediction is RECORDED HERE AS WRONG ... because a wrong prediction quietly dropped is how a cost becomes a surprise"; commit 2650d3c87 deleted the file with its figures never filled in, and no before/after ring measurement exists (ring #1 ran 11 files, ring #2 ran 14, so they are not comparable).

PROOF (the command the skeptic ran, and its real output):

```
cd /home/user/dr-lanes/lane-A && grep -rn "P-FIX-4\|tens of seconds" experiments/2026-08-30-change-checkpoint-hardening/ | grep -v SPEC.md
(no output)

git log --oneline --all -- experiments/2026-08-30-change-checkpoint-hardening/proof/RUNTIME.md
2650d3c87 lane A: a failure terminal records why it cannot be continued; --verify answers from the verdict it re-derived
5fccb1e91 lane A: continuation is integrity-gated, and a failure terminal records why it cannot continue

git show 5fccb1e91:.../proof/RUNTIME.md | tail -1
(figures filled in below from the two ring runs)
```

PROPOSED FIX: Add one line to PARKED.md F9 or VALIDATION.md recording that P-FIX-4's estimate was refuted and by roughly how much (ring #1, 11 files with the gate: 1036.65s; ring #2, 14 files without it: 703.65s), so the parked gate's cost is not re-predicted from the same wrong figure.
