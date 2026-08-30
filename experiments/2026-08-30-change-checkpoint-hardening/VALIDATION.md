# VALIDATION — checkpoint hardening (lane A, batch 2)

Every SPEC.md acceptance check, run, with what it actually produced — including
the four that FAILED and the items they belong to, which are parked rather than
delivered.

REVISED 2026-08-30 after an independent skeptic pass re-ran these claims and
confirmed eight defects. Sections S7, S-BUDGET, S-RING2, S8 and S-CENSUS are
corrected below and say what they got wrong; S-SKEPTIC, S-RING4 and S-DOCS2 are
new. Nothing that was measured has been deleted — the earlier readings stand
beside the corrections, which is what makes this a ledger.

## The environment fact every command here depends on

The editable install's `.pth` names `/home/user/DeepReason/src`, not this
worktree. A bare `python -m pytest` inside the worktree therefore imports the
OTHER checkout and reports on code this lane never touched. Measured:

    $ python -c "import deepreason; print(deepreason.__file__)"
    /home/user/DeepReason/src/deepreason/__init__.py

    $ PYTHONPATH=/home/user/dr-lanes/lane-A/src python -c "import deepreason; print(deepreason.__file__)"
    /home/user/dr-lanes/lane-A/src/deepreason/__init__.py

Every command below carries `PYTHONPATH=/home/user/dr-lanes/lane-A/src`. The
lane's first "GREEN" run of S1-S4 was green for this reason and no other; it was
discarded, and the finding is recorded here rather than buried.

## Box condition

Shared container, four other lanes of the same batch running their own suites.
Ring runs were single-process (`-p no:randomly`, no `-n`). Wall clock is an
upper bound. No full gate was run: the orchestrator runs one at fan-in on an
idle box.

---

## S1 — the CONTINUE integrity gate. NOT DELIVERED (parked, F9).

    accept: pytest tests/test_checkpoint_hardening.py::test_one_flipped_log_byte_turns_a_continue_into_a_typed_integrity_refusal -q  ->  1 passed

RESULT WHEN THE GATE WAS ARMED: **1 passed.** Transcript
`proof/GREEN-checkpoint-hardening.txt` (`6 passed in 46.34s`), against
`proof/RED-checkpoint-hardening.txt` (`5 failed, 1 passed in 8.46s`).

    accept: python -c "... assert 'CONTINUE_RECORD_NOT_VERIFIED' in s; assert 'verify_root' in s"  ->  exit 0

RESULT NOW: **exit 1.** The gate was reverted after ring #1; see S-RING below
and `proof/gate_collisions.md`. The implementation is `git show 5fccb1e91`.

## S2 — the AMEND integrity gate. NOT DELIVERED (parked, F9).

    accept: python -c '... assert len(codes)==23 and "AMEND_RECORD_NOT_VERIFIED" in codes'  ->  exit 0

RESULT WHEN ARMED: exit 0. RESULT NOW: **exit 1** — 22 codes, as before this
tranche. `docs/map/SUB-amendment.md` is restored byte-for-byte to its
`origin/main` state, so its `len(codes)==22` check stays true.

    $ git diff --stat 84514a028 -- docs/map/SUB-amendment.md
    (empty)

## S3 — the one-byte differential. PROVEN, then parked with S1/S2.

The proof exists and is re-runnable as an instrument rather than as a gate test:

    $ PYTHONPATH=.../src python experiments/2026-08-30-change-checkpoint-hardening/proof/forge_one_byte.py
    --- intact ---
      stored_replay_valid: True
      verify_root_violations: []
      terminal_authority: current_valid_committed
      amend_gate: PASSED
      results_terminal_default: True
      results_terminal_verify: True
      continue_gate: REFUSED ValueError: CONTINUE_TYPED_STOP_REQUIRED
    --- forged ---
      stored_replay_valid: True
      verify_root_violations: ['attempt-route', 'frozen-route']
      terminal_authority: current_valid_committed
      amend_gate: PASSED
      results_terminal_default: True
      results_terminal_verify: False
      continue_gate: REFUSED ValueError: CONTINUE_TYPED_STOP_REQUIRED
    edit: {'offset': 22948, 'from': 'a', 'to': '7'}

One byte, one root, and of six surfaces exactly ONE now sees the forgery —
`results --verify`, which is S7. That is the honest measure of what this
tranche delivered against the law's security clause: not the refusal the law
asks for.

    accept: git status --porcelain experiments/  ->  empty after the run

    $ git status --porcelain --untracked-files=no experiments
    (empty)

## S4 — the witness regression over the 16-root gap. NOT DELIVERED (parked, F9).

It passed when the gate was armed (part of the `6 passed` above). It is
meaningless without the gate and was removed with it. The population it selects
over is preserved as a measurement: `proof/census.json`
(`A2_gap_authority_valid_but_replay_invalid`, 16 roots) and `proof/gate_probe.json`
(amend PASSED on 6 of 6 driven).

## S5 — the ordinary worker-failure terminal records its own uncontinuability. DELIVERED.

    accept: pytest tests/test_checkpoint_hardening.py::test_a_failure_terminal_records_why_it_cannot_be_continued -q  ->  1 passed

RED (before the change), `proof/RED-checkpoint-hardening.txt`:

    tests/test_checkpoint_hardening.py:252: KeyError: 'terminal_lifecycle_refusal'

GREEN (after): part of `2 passed, 4 deselected in 4.54s` and of ring #2 below.
The test does not only read the record back; it drives `prepare_continuation`
on a copy of the very root it just made and asserts the refusal the record
CLAIMS is the refusal the verb actually raises.

## S6 — the no-harness failure terminal. DELIVERED.

    accept: pytest tests/test_checkpoint_hardening.py::test_a_terminal_that_wrote_no_checkpoint_records_that_fact -q  ->  1 passed

RED: `tests/test_checkpoint_hardening.py:315: KeyError: 'terminal_lifecycle_refusal'`.
GREEN: as above. The test asserts `run-stop.json` and `checkpoint.json` are
ABSENT, so it is testing the corrupted stop and not a tidier one.

## S7 — the reader answers from the verdict it is holding. WITHDRAWN 2026-08-30.

    accept: pytest tests/test_results_command.py -q  ->  0 failed
    accept: pytest tests/test_results_command.py::test_terminal_readiness_answers_the_rederived_verdict_under_verify -q  ->  1 passed

RED (`proof/RED-results-verify.txt`, results.py stashed):

    E   assert True is False
    tests/test_results_command.py:533: assert True is False
    1 failed in 7.05s

GREEN (`proof/GREEN-results-verify.txt`):

    1 passed in 6.84s

The exact-set assertion on the six `terminal` keys did not move (P-FIX-2 held):
`test_terminal_readiness_answers_the_amend_question` passes unchanged in ring #2.

WITHDRAWN in the skeptic pass, on a measurement this lane never took. S7's
whole justification is SPEC.md's phrase "whose `amend` (after S2) refuses" —
and S2 never landed. With the verbs ungated the change makes the reader state
the OPPOSITE of what they do:

    $ PYTHONPATH=.../src python .../proof/forge_amend_ready.py     # WITH S7 IN PLACE
    --- forged ---
      verify_root_violations: ['attempt-route', 'frozen-route']
      results_amend_ready_default: True
      results_amend_ready_verify: False        <-- S7's answer
      amend: ACCEPTED epoch=1
      continue: ACCEPTED seq=0                 <-- what the verbs actually do

The delivered tree, same probe, same forged byte (this is what
`proof/forge_amend_ready.json` now holds — the S7 reading above is preserved
here and nowhere else):

      results_amend_ready_verify: True         <-- and both verbs accept

At the CLI, on the same forged copy, the delivered pair of lines:

    $ python -m deepreason.cli.main results <forged copy> --verify
      verify_root verdict (...): no
      read from: rederived
      stands at a valid typed terminal: yes (terminal epoch 0)
      ready for `deepreason amend` / `deepreason continue`: yes

Both lines are TRUE, and together they are the disclosure the operator's clause
needs today: the record does not verify, and the verbs will act on it anyway.
S7 replaced the second with a false `no`. Reverted:

    $ git diff --stat origin/main -- src/deepreason/application/results.py tests/test_results_command.py
    (empty)

A second, independent reason it should not stand as written: the verdict S7
reads is not the predicate the parked gate used. See S-SKEPTIC / M4-M5 below.

## S8 — the map moves in the same commit. DELIVERED, describing what shipped.

- `docs/map/SUB-amendment.md` — RESTORED to origin/main. The 22->23 move was
  made and then reverted with S2; leaving it would have been a false claim.
- `docs/map/CON-run-identity.md` — the gate rule was written and then removed
  with S1. What remains is a Traps entry stating the MEASURED finding (terminal
  authority is blind to a forged record; the whole jailbreak completing on an
  `amend_ready` root; 16 of 59 roots; 4 forgeries of the stored verdict
  undetected) and saying plainly that the gate is not shipped.

  CORRECTED 2026-08-30. The check first shipped here asserted the committed
  `forge.json`'s stored numbers, so it could not fail for the reason its own
  prose gives — mutate `terminal_authority.py` until the described blindness is
  gone and the check stays green. It now RE-DERIVES: the second half forges
  `valid: true` onto copies of all four blind roots and two detected ones and
  asks `derive_terminal_authority` afresh. Both arms are in S-SKEPTIC.

- `docs/map/SUB-application.md` — a new "Where to change what" row for the
  failure-terminal records, a new Traps entry for the silent failure terminals,
  and the P6 entry REWRITTEN (never deleted) to say which half of P2 closed and
  which halves are parked. The second row this section originally claimed —
  which verdict the reader answers from — went with the S7 revert. Two
  corrections from the skeptic pass are folded in: the row said "the two
  `except` branches of `_worker`" where there is ONE `except` block with THREE
  exits (the third is parked as F10), and the P6 entry said 16 committed roots
  "stop being silent", which no code change can do to an immutable root. Its
  check:

      $ grep -q "TERMINAL_LIFECYCLE_NOT_TAKEN_FAILURE_TERMINAL" src/deepreason/application/text_runs.py && grep -q "TERMINAL_NO_CHECKPOINT_WRITTEN" src/deepreason/application/text_runs.py
      (exit 0)

  and the pre-existing terminal-emit census it must not break:

      $ python -c '... calls = re.findall(r"progress\.emit\((.*?)\n\s*\)", src, re.S); terminal = [...]; assert len(terminal) == 4; assert all("token_spend=" in c for c in terminal)'
      terminal progress.emit census still 4: PASS

    accept: python tools/docs_verify.py -> 0 failed beyond the baseline set

RECORDED BELOW under S-DOCS.

## S9 — the census and the probes are committed instruments. DELIVERED.

    accept: python .../proof/census.py -> exit 0, prints population: 59

RECORDED BELOW under S-CENSUS.

    accept: git status --porcelain experiments/ -> empty after all run

    $ git status --porcelain --untracked-files=no experiments
    (empty)

`proof/` holds NINE instruments and the output of each:
`census.py`/`census.json`, `forge_probe.py`/`forge.json` (with a `--witnesses`
re-derivation mode), `gate_probe.py`/`gate_probe.json`,
`verify_cost.py`/`verify_cost.json`, `forge_one_byte.py`/`forge_one_byte.json`,
and, added in the skeptic pass,
`forge_amend_ready.py`/`forge_amend_ready.json`,
`control_predicate_arms.py`/`control_predicate_arms.txt`,
`two_predicates.py`/`two_predicates.json` and
`failed_continue_codes.py`/`failed_continue_codes.json` — plus `MEASUREMENTS.md`
and `gate_collisions.md`.

---

## S-BUDGET — the diff budget, both readings

CORRECTED 2026-08-30. The figures first published here (`tests 224, total
317`) were captured at commit `2650d3c87`, one commit before the last change to
`tests/`, and the pasted object had been hand-trimmed — `tools/diff_budget.py`
emits `result_type`, `base` and `against` unconditionally, so a three-key
object cannot be its output. Both commands re-run at HEAD, verbatim:

    $ python tools/diff_budget.py 84514a0280f45d29e5066bb3be3d273ba73798db --ceiling 400 --paths src tests docs/map
    {"result_type": "DIFF_BUDGET_RESULT_V1", "base": "84514a0280f45d29e5066bb3be3d273ba73798db", "against": null, "areas": {"src": 34, "tests": 238, "docs/map": 68}, "total_insertions": 340, "ceiling": 400, "verdict": "WITHIN"}

    $ python tools/diff_budget.py 84514a0280f45d29e5066bb3be3d273ba73798db --ceiling 400 --paths src
    {"result_type": "DIFF_BUDGET_RESULT_V1", "base": "84514a0280f45d29e5066bb3be3d273ba73798db", "against": null, "areas": {"src": 34}, "total_insertions": 34, "ceiling": 400, "verdict": "WITHIN"}

With the gate armed this read `EXCEEDED` at 565 (src 103, tests 397, docs/map
65) and was parked as F8; the revert withdrew it. Both figures are in PARKED.md
F8 so the reading is not lost.

## S-FROZEN — the frozen-surface disposition

    $ git diff --name-only 84514a0280f45d29e5066bb3be3d273ba73798db | grep -E "capabilities/state\.py|/harness\.py|/invariants\.py|/run_manifest\.py|/qualification\.py|llm/firewall\.py|verification/"
    (no match)

The grep is widened past the tripwire's own regex to include
`src/deepreason/verification/`, which is the half of surface 3 the committed
tripwire cannot see. No frozen path is touched, and no grant was requested or
needed. `verify_root` is CONSUMED by the probes under `proof/` (by import,
read-only) and by nothing in `src/`.

Files this lane changed, as measured rather than as claimed:

    $ git diff --name-only 84514a0280f45d29e5066bb3be3d273ba73798db
    docs/map/CON-run-identity.md
    docs/map/SUB-application.md
    experiments/2026-08-29-ultracode-batch-2/SETUP.md
    experiments/2026-08-29-ultracode-batch-2/recon/RECON-A.md
    experiments/2026-08-29-ultracode-batch-2/recon/RECON-B.md
    experiments/2026-08-29-ultracode-batch-2/recon/RECON-C.md
    experiments/2026-08-29-ultracode-batch-2/recon/RECON-D.md
    experiments/2026-08-29-ultracode-batch-2/recon/RECON-E.md
    experiments/2026-08-29-ultracode-batch-2/recon/RECON-SHARED.md
    experiments/2026-08-30-change-checkpoint-hardening/CHECKLIST.md
    experiments/2026-08-30-change-checkpoint-hardening/PARKED.md
    experiments/2026-08-30-change-checkpoint-hardening/REQUEST.md
    experiments/2026-08-30-change-checkpoint-hardening/SPEC.md
    experiments/2026-08-30-change-checkpoint-hardening/VALIDATION.md
    experiments/2026-08-30-change-checkpoint-hardening/proof/GREEN-checkpoint-hardening.txt
    experiments/2026-08-30-change-checkpoint-hardening/proof/GREEN-results-verify.txt
    experiments/2026-08-30-change-checkpoint-hardening/proof/MEASUREMENTS.md
    experiments/2026-08-30-change-checkpoint-hardening/proof/RED-checkpoint-hardening.txt
    experiments/2026-08-30-change-checkpoint-hardening/proof/RED-results-verify.txt
    experiments/2026-08-30-change-checkpoint-hardening/proof/census.json
    experiments/2026-08-30-change-checkpoint-hardening/proof/census.py
    experiments/2026-08-30-change-checkpoint-hardening/proof/forge.json
    experiments/2026-08-30-change-checkpoint-hardening/proof/forge_one_byte.json
    experiments/2026-08-30-change-checkpoint-hardening/proof/forge_one_byte.py
    experiments/2026-08-30-change-checkpoint-hardening/proof/forge_probe.py
    experiments/2026-08-30-change-checkpoint-hardening/proof/gate_collisions.md
    experiments/2026-08-30-change-checkpoint-hardening/proof/gate_probe.json
    experiments/2026-08-30-change-checkpoint-hardening/proof/gate_probe.py
    experiments/2026-08-30-change-checkpoint-hardening/proof/verify_cost.json
    experiments/2026-08-30-change-checkpoint-hardening/proof/verify_cost.py
    src/deepreason/application/text_runs.py
    tests/test_checkpoint_hardening.py

UPDATED after the skeptic pass: `src/deepreason/application/results.py` and
`tests/test_results_command.py` left this list with the S7 revert and are
byte-identical to `origin/main`; five new files under `proof/` joined it
(`forge_amend_ready`, `control_predicate_arms`, `two_predicates`,
`failed_continue_codes`, and their outputs). ONE source file is changed by this
lane in total.

## S-RING — ring #1, the run that stopped the gate

    $ PYTHONPATH=.../src python -m pytest \
        tests/test_continuation.py tests/test_amendment_epochs.py \
        tests/test_amendment_chain_integrity.py \
        tests/test_lifecycle_operation_parity.py tests/test_results_command.py \
        tests/test_terminal_lifecycle_refusal_is_recorded.py \
        tests/test_calculus_standing.py \
        tests/test_v6_resumed_terminal_revalidation.py \
        tests/test_v6_terminal_commitment_authority.py \
        tests/test_workflow_resume_lifecycle_c4.py tests/test_error_catalog.py \
        -q -p no:randomly --tb=line

    8 failed, 174 passed in 1036.65s (0:17:16)

SPEC.md predicted ONE (P-FIX-1). The eight are classified one by one in
`proof/gate_collisions.md`; three cannot be repaired as fixtures without
changing what they assert. Per SPEC.md P-FIX-3(b) this is a STOP and a
re-plan, so the gate was reverted and parked (F9). Nothing was weakened and no
test root was exempted.

## S-RING2 — ring #2, as delivered

Same eleven files plus the new module and the two files S5/S6 touch:

    $ PYTHONPATH=.../src python -m pytest \
        tests/test_checkpoint_hardening.py tests/test_continuation.py \
        tests/test_amendment_epochs.py tests/test_amendment_chain_integrity.py \
        tests/test_lifecycle_operation_parity.py tests/test_results_command.py \
        tests/test_terminal_lifecycle_refusal_is_recorded.py \
        tests/test_calculus_standing.py \
        tests/test_v6_resumed_terminal_revalidation.py \
        tests/test_v6_terminal_commitment_authority.py \
        tests/test_workflow_resume_lifecycle_c4.py tests/test_error_catalog.py \
        tests/test_failure_terminal_reports_real_token_spend.py \
        tests/test_progress.py -q -p no:randomly --tb=short

    1 failed, 193 passed in 703.65s (0:11:43)

The one failure was THIS MODULE'S OWN control test,
`test_committed_roots_are_byte_unchanged_by_this_module`, and it was right to
fire and wrong in its predicate: it flagged `PARKED.md`, a tranche narrative
document edited while the ring ran, as "a committed root moved". Re-run after
the narrowing:

    $ PYTHONPATH=.../src python -m pytest tests/test_checkpoint_hardening.py -q -p no:randomly
    3 passed in 5.19s

MUTATION PROOF of the narrowed control (`proof/RED-byte-unchanged-mutant.txt`)
— one byte appended to a committed root's `log.jsonl`, the test run, the byte
removed:

    E   AssertionError: a committed root moved: [' M experiments/2026-08-13-defect-controller-steering-inert/failed-epoch1-run-8e22d0431fd2b98d/log.jsonl']
    1 failed in 0.51s

TWO CORRECTIONS, 2026-08-30, both from the skeptic pass. First: the sentence
"the assertion is unchanged" was true of the `assert` line and false of the
control. The narrowed predicate kept a status line only when the line's OWN
directory held a `log.jsonl`, which is 1 823 of the 96 288 tracked files inside
a committed root — every file under `blobs/` and `objects/`, the
content-addressed evidence the record is built from, became invisible. Second:
the mutation proof above exercises ONE class, modification, and the predicate
was blind to the worst class, DELETION — removing `log.jsonl` removes the very
file the filter needs. Both are repaired: the predicate is now built from git's
INDEX (`git ls-files`) over NUL-delimited status, and six arms are proven in
S-SKEPTIC below.

P-FIX-1 was NOT needed in the delivered tree: without the gate,
`test_continuation.py::test_a_stop_with_no_typed_receipt_refuses_continuation`
passes unchanged, and `tests/test_continuation.py` is untouched by this lane.

## S-DOCS — `tools/docs_verify.py`, delta ZERO against this container's baseline

    $ PYTHONPATH=.../src python tools/docs_verify.py
      FAIL SEAM-llm-x-rules.md:54
      FAIL CON-discharge-channel.md:150
      FAIL CON-run-identity.md:211
      FAIL CON-run-identity.md:213
      FAIL CON-run-identity.md:215
      FAIL INV-frozen-surfaces.md:181
      FAIL INV-frozen-surfaces.md:734
      FAIL INV-signal-contract.md:243
      FAIL SEAM-llm-x-verification.md:19
    docs_verify: 9 failed

`docs/AUDIT_BASELINES.md` records "6 failed on a full clone, 9 on a shallow
one"; this container is shallow. Nine, and the three `CON-run-identity.md`
failures at :211/:213/:215 are `git log`/`git show -M` history checks that a
shallow clone cannot satisfy — this lane's diff to that document is a pure
ADDITION at line 258 and later, so none of them can have been caused by it.

THE FIRST RUN OF THIS COMMAND REPORTED **10**, and the tenth was this lane's own
new check: it asserted `forge.json["undetected"] == 4` where that key is a LIST
of four root paths. The check was wrong, docs_verify caught it, and it is now

    assert len(rows['undetected']) == 4 and rows['population'] == 16 and rows['detected'] == 12

The gate half of the same check is mutation-proven by construction — it asserts
`'verify_root' not in` either verb's module, so it goes RED the moment the
parked gate lands and the Traps entry is not rewritten with it:

    $ python -c "c='...verify_root...'; assert 'verify_root' not in c, 'the integrity gate landed: REWRITE this Traps entry, never delete it'"
    AssertionError: the integrity gate landed: REWRITE this Traps entry, never delete it

## S-CENSUS — the census re-run, and an independent check on S7

    $ PYTHONPATH=.../src python experiments/2026-08-30-change-checkpoint-hardening/proof/census.py
    ...
    population: 59
    schema_version: {'6': 59}
    triples (state | stop_reason | amend_ready):
      completed | budget_exhausted | True  -> 23
      failed | operational_failure | False  -> 16
      completed | budget_exhausted | False  -> 13
      running | {'absent': True, 'reason': 'NO_STOP_RECORD'} | False  -> 4
      running | budget_exhausted | False  -> 1
      completed | converged | True  -> 1
      running | operational_failure | False  -> 1
    amend_ready: {'False': 35, 'True': 24}
    stored_replay_valid: {'True': 39, 'False': 16, "{'absent': True, 'reason': 'NO_REPLAY_VALIDATION_JSON'}": 4}
    authority_status: {'current_valid_committed': 54, 'current_open_uncommitted': 4, 'invalid_incomplete': 1}
    A2 gap (authority valid AND stored replay invalid): 16
    A1 failed without continuation authority: 15
    finalize population (current_open_uncommitted): 4
    stranded (neither amend nor finalize): 1
      experiments/live_research_2026-07-29/selfstudy/runs/failed-epoch2-run-9175f0ecb055e57455af3c50df153c5a
    exit=0

    $ git status --porcelain experiments/2026-08-30-change-checkpoint-hardening/proof/
    (empty)

The empty second line is worth more than the first: `census.py` drives
`results_summary` over all 59 committed roots on its DEFAULT path, and its
output file is byte-identical. When this was written it certified S7's default
path; with S7 withdrawn it certifies something smaller and still worth having —
that nothing this tranche shipped moved what `deepreason results` says about
any committed root. NOTE, from the skeptic pass: this control covered the
DEFAULT path only. The `--verify` path over committed roots was never asserted
anywhere, and S7 changed it in BOTH directions (on 4 of 6 witness roots
`valid_typed_terminal` moved False->True, and `amend_ready` on two of them).
That gap is one of the reasons S7 is withdrawn rather than kept with a wider
test.

## S-RING3 — the delivered tree, final ring, on an idle box

    $ PYTHONPATH=.../src python -m pytest \
        tests/test_checkpoint_hardening.py tests/test_continuation.py \
        tests/test_amendment_epochs.py tests/test_amendment_chain_integrity.py \
        tests/test_lifecycle_operation_parity.py tests/test_results_command.py \
        tests/test_terminal_lifecycle_refusal_is_recorded.py \
        tests/test_calculus_standing.py \
        tests/test_v6_resumed_terminal_revalidation.py \
        tests/test_v6_terminal_commitment_authority.py \
        tests/test_workflow_resume_lifecycle_c4.py tests/test_error_catalog.py \
        tests/test_failure_terminal_reports_real_token_spend.py \
        tests/test_progress.py tests/test_website_state_machine.py \
        -q -p no:randomly --tb=short

    208 passed in 649.98s (0:10:49)

`tests/test_website_state_machine.py` is in the ring on purpose: the blast
radius named four `_terminal` hits there, and they are a NAME COLLISION with
`results.py`'s `_terminal`, not a consumer of it. Running it proves the
distinction rather than asserting it.

NO FULL GATE was run by this lane. The orchestrator runs one at fan-in on an
idle box, per the batch's own process-hygiene rule.

## S-RING4 — the delivered tree after the skeptic pass

Same fifteen files as ring #3, so the two are comparable:

    $ PYTHONPATH=.../src python -m pytest \
        tests/test_checkpoint_hardening.py tests/test_continuation.py \
        tests/test_amendment_epochs.py tests/test_amendment_chain_integrity.py \
        tests/test_lifecycle_operation_parity.py tests/test_results_command.py \
        tests/test_terminal_lifecycle_refusal_is_recorded.py \
        tests/test_calculus_standing.py \
        tests/test_v6_resumed_terminal_revalidation.py \
        tests/test_v6_terminal_commitment_authority.py \
        tests/test_workflow_resume_lifecycle_c4.py tests/test_error_catalog.py \
        tests/test_failure_terminal_reports_real_token_spend.py \
        tests/test_progress.py tests/test_website_state_machine.py \
        -q -p no:randomly --tb=short

    207 passed in 641.67s (0:10:41)

208 in ring #3, 207 here: the difference is exactly S7's test, removed with S7.

ONE edit landed after this ring: a non-vacuity guard on the control test
(`assert len(roots) >= 50`, because `str.startswith(())` is False for every
path and an empty root set would make the control pass on any mutation). It is
confined to `tests/test_checkpoint_hardening.py`, which nothing else imports,
and that file was re-run alone:

    $ PYTHONPATH=.../src python -m pytest tests/test_checkpoint_hardening.py -q -p no:randomly
    3 passed in 4.81s
No test was weakened, skipped or exempted to reach this number — the two source
edits in this pass both DELETE a claim (`results.py` back to base, the
`continue_refusal` field gone), and the one test edit REPLACES a predicate with
a stricter one whose six arms are proven above.

## S-DOCS2 — `tools/docs_verify.py` after the map repairs

    $ PYTHONPATH=.../src python tools/docs_verify.py
      FAIL SEAM-llm-x-rules.md:54
      FAIL CON-discharge-channel.md:150
      FAIL CON-run-identity.md:211
      FAIL CON-run-identity.md:213
      FAIL CON-run-identity.md:215
      FAIL INV-frozen-surfaces.md:181
      FAIL INV-frozen-surfaces.md:734
      FAIL INV-signal-contract.md:243
      FAIL SEAM-llm-x-verification.md:19
    docs_verify: 9 failed

The same nine `docs/AUDIT_BASELINES.md` predicts for a shallow clone, name for
name — delta ZERO. The re-deriving `CON-run-identity.md` check added in this
pass is not among them; it passes, and it costs 33 s.

`Verified-at:` is NOT advanced on either map document. Both were re-run in full
here — `CON-run-identity.md` 25 checks with 3 failing, `SUB-application.md` 30
checks with 0 failing — and the three failures are the shallow-clone `git log` /
`git show -M` history checks this container cannot satisfy. A stamp claiming a
clean re-derivation would be false; a stale stamp is honest.

## S-SKEPTIC — the independent pass, finding by finding, with its commands

Eight findings, all confirmed by re-running them here before acting on any.

### 1 (blocking) — a forged `amend_ready` root buys BOTH verbs

Reproduced as a committed instrument on a COPY, never on the root:

    $ PYTHONPATH=.../src python experiments/2026-08-30-change-checkpoint-hardening/proof/forge_amend_ready.py
    --- intact ---
      stored_replay_valid: True
      verify_root_violations: []
      results_amend_ready_default: True
      results_amend_ready_verify: True
      amend: ACCEPTED epoch=1
      continue: ACCEPTED seq=0
    --- forged ---
      stored_replay_valid: True
      verify_root_violations: ['attempt-route', 'frozen-route']
      results_amend_ready_default: True
      results_amend_ready_verify: True
      amend: ACCEPTED epoch=1
      continue: ACCEPTED seq=0
    edit: {'offset': 11656, 'from': 'a', 'to': '7'}
    jailbreak_open: True

Nothing in this lane's cone fixes it — the gate that would is parked. What
changed is the PARK: F9 now carries this as its acceptance target, replacing
the weaker endpoint differential, and `DR-CON-run-identity`'s Traps entry
states it. Note the forged arm's first line: the root's own
`REPLAY_VALIDATION.json` still says `valid: true`, so a gate that reads the
STORED verdict clears this forgery.

### 2 and 5 and 6 (major) — S7, and the false premise it shipped with

Answered by reverting S7; see the S7 section above for the measurement and the
`git diff --stat origin/main` that shows both files back at base. The
docstrings that asserted "since 2026-08-30 the ACTING verbs re-derive it" went
with them, in `results.py` and in `tests/test_results_command.py`. SPEC.md's S7
item carries the withdrawal rather than losing it.

    $ grep -c verify_root src/deepreason/runtime/continuation.py src/deepreason/amendment/apply.py
    src/deepreason/runtime/continuation.py:0
    src/deepreason/amendment/apply.py:0

### 3 and 4 (blocking + major) — the byte-unchanged control could not see a delete

The predicate kept a status line only if `Path(line[3:]).parent / "log.jsonl"`
existed ON DISK, so deleting the log (or the root) removed the file the filter
needed, and `blobs/`/`objects/` were never in scope at all. Rebuilt on git's
INDEX, and mutation-proven across six arms against REAL `git status` output in
a scratch repository built for the purpose (a committed root may not be deleted
to watch a test fire):

    $ python experiments/2026-08-30-change-checkpoint-hardening/proof/control_predicate_arms.py
    ### modify log.jsonl (the original mutation proof)          new=True   old=True    (must be True)
    ### delete log.jsonl                                        new=True   old=False   (must be True)
    ### delete the whole run root                               new=True   old=False   (must be True)
    ### modify content-addressed evidence under blobs/          new=True   old=False   (must be True)
    ### rename a root file out of the root                      new=True   old=False   (must be True)
    ### CONTROL: edit tranche narrative not inside any root     new=False  old=False   (must be False)
    NEW predicate correct on all 6 arms: True
    arms the OLD predicate MISSED (4): ['delete log.jsonl', 'delete the whole run root',
      'modify content-addressed evidence under blobs/', 'rename a root file out of the root']
    EXIT=0

The last arm is the reason the narrowing existed and is kept: a tranche editing
its own `PARKED.md` must not turn this control red.

### 7 (blocking) — the map check could not fail for the reason its prose gives

The numeric half re-read the committed `forge.json`. It now re-derives.
Delivered tree:

    $ python experiments/2026-08-30-change-checkpoint-hardening/proof/forge_probe.py --witnesses
    UNDETECTED current_valid_committed  .../run-0a3e93d6e8031e2e6d1d21dde2fa93cc
    UNDETECTED current_valid_committed  .../run-9a6be78e1e79184a0bd89923b957586c
    UNDETECTED current_valid_committed  .../run-e3f4f7007c50fe7e09b301d31851c3e7
    UNDETECTED current_valid_committed  .../completed-epoch3-run-9175f0ecb055e57455af3c50df153c5a
    DETECTED  invalid_incomplete  .../failed-epoch1-run-8c77c6588485304d1f73416318c62949
    DETECTED  invalid_incomplete  .../void-inert-battery-run-6913328037a61ca6
    re-derived: 4 still blind, 2 still detected
    EXIT=0   (33.1s)

MUTATION PROOF — the mechanism the prose names, removed
(`terminal_authority.py`, `if result == pending_result:` -> `if False:`):

    UNDETECTED -> DETECTED on all four blind roots
    the forge measurement MOVED -- rewrite DR-CON-run-identity's Traps entry, never delete it:
      ...run-0a3e93d6e8: forge_detected=True (the record says False); authority=invalid_incomplete
      (and three more)
    EXIT=1

    $ git checkout -- src/deepreason/runtime/terminal_authority.py
    $ git status --porcelain    # the mutant is gone; forge.json was never rewritten

The `verify_root not in ...` half is kept unchanged: it guards the separate
claim that the gate is not shipped.

### 8 (major) — S7 moved `--verify` in both directions, and M4/M5 named the wrong predicate

Moot for the shipped tree, since S7 is withdrawn. The measurement error behind
it is not moot and is corrected in `proof/MEASUREMENTS.md`: "the re-derived
verdict" was used for two different predicates that disagree.

    $ PYTHONPATH=.../src python .../proof/two_predicates.py
        agrees with stored under verify_root(violations non-empty): 6/6
    agrees with stored under verify_root_report(...).summary_payload()['valid']: 2/6

### 9 (minor) — S5 recorded a `continue_refusal` it did not derive

The field is gone. Which code `continue` raises also depends on the cycles and
tokens the operator later passes and on any resume decision an earlier
continuation left, so the terminal cannot know it; 15 of the 16 committed roots
of this shape raise `CONTINUE_TYPED_STOP_REQUIRED` and one raises
`CONTINUE_RESUME_RECOVERY_MISMATCH`. The test did not get weaker: it still
drives `prepare_continuation` on a copy of the root it just made and asserts
the code actually raised.

### 10 (minor) — `SUB-application.md` miscounted, and spoke for committed roots

`_worker` has ONE `except (Exception, SystemExit)` block with THREE exits. Two
now record a typed refusal; the third (`current_terminal_commitment is not
None`) records nothing and is parked as F10, with the measured fairness note
that `deepreason finalize` recovers that root. And "16 committed roots of that
shape stop being silent about it" is impossible — committed roots are
immutable; the row now says a FUTURE run of that shape records it.

### also corrected

- CHECKLIST.md row 12 recorded ring #2 as `0 failed | DONE` where this document
  recorded `1 failed, 193 passed`. It now records the real outcome and points
  the 0-failed criterion at ring #3.
- The diff-budget transcript in three documents (VALIDATION S-BUDGET, DELIVERY,
  PARKED F8) was stale by one commit and hand-trimmed. Re-run at HEAD above.

## Summary

| SPEC item | delivered | acceptance |
|---|---|---|
| S1 CONTINUE integrity gate | NO — parked F9 | passed when armed; reverted after ring #1 |
| S2 AMEND integrity gate | NO — parked F9 | passed when armed; reverted after ring #1 |
| S3 one-byte differential | proven, as an instrument | `proof/forge_one_byte.json` |
| S4 witness regression | NO — parked with S1/S2 | population preserved in `proof/census.json` |
| S5 failure terminal records uncontinuability | YES | RED -> GREEN, in ring #3 |
| S6 no-checkpoint terminal records it | YES | RED -> GREEN, in ring #3 |
| S7 reader answers from the verdict it holds | NO — WITHDRAWN 2026-08-30 | it printed `amend_ready: false` where both verbs ACCEPT; `results.py` and its test are back at `origin/main` |
| S8 map moves in the same commit | YES | docs_verify delta ZERO against the container baseline (S-DOCS2), and the numeric check now RE-DERIVES |
| S9 instruments committed | YES | census exit 0, population 59, tree clean; two instruments added in the skeptic pass |

VERDICT: **PARTIAL.** Limb two of the P2 law is delivered and proven. Limb
three is not, and is parked with its implementation, its proof, a measured
acceptance target, and a ready-to-send re-plan.

The skeptic pass narrowed what this tranche claims rather than widening it: one
shipped item (S7) was withdrawn, one shipped field (`continue_refusal`) was
removed, and two committed instruments were added. Nothing was weakened to stay
green — the two source-side changes both DELETE a claim the tree could not
support, and every test that guarded them is still driven against real records.
