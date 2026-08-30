# VALIDATION — checkpoint hardening (lane A, batch 2)

Every SPEC.md acceptance check, run, with what it actually produced — including
the four that FAILED and the items they belong to, which are parked rather than
delivered.

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

## S7 — the reader answers from the verdict it is holding. DELIVERED.

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

## S8 — the map moves in the same commit. DELIVERED, describing what shipped.

- `docs/map/SUB-amendment.md` — RESTORED to origin/main. The 22->23 move was
  made and then reverted with S2; leaving it would have been a false claim.
- `docs/map/CON-run-identity.md` — the gate rule was written and then removed
  with S1. What remains is a Traps entry stating the MEASURED finding (terminal
  authority is blind to a forged record; 16 of 59 roots; 4 forgeries of the
  stored verdict undetected) and saying plainly that the gate is not shipped,
  with a check that goes RED if the gate lands and the entry is not rewritten:

      $ python -c "import pathlib,json; c=pathlib.Path('src/deepreason/runtime/continuation.py').read_text(); a=pathlib.Path('src/deepreason/amendment/apply.py').read_text(); assert 'verify_root' not in c and 'verify_root' not in a; rows=json.loads(pathlib.Path('experiments/2026-08-30-change-checkpoint-hardening/proof/forge.json').read_text()); assert rows['undetected'] == 4 and rows['population'] == 16"
      (exit 0)

- `docs/map/SUB-application.md` — two new "Where to change what" rows (the two
  failure-terminal records; which verdict the reader answers from), a new Traps
  entry for the silent failure terminals, and the P6 entry REWRITTEN (never
  deleted) to say which half of P2 closed and which two halves are parked. Its
  new check:

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

`proof/` holds five instruments and their outputs: `census.py`/`census.json`,
`forge_probe.py`/`forge.json`, `gate_probe.py`/`gate_probe.json`,
`verify_cost.py`/`verify_cost.json`, `forge_one_byte.py`/`forge_one_byte.json`,
plus `MEASUREMENTS.md` and `gate_collisions.md`.

---

## S-BUDGET — the diff budget, both readings

    $ python tools/diff_budget.py 84514a0280f45d29e5066bb3be3d273ba73798db --ceiling 400 --paths src tests docs/map
    {"areas": {"src": 41, "tests": 224, "docs/map": 52}, "total_insertions": 317, "ceiling": 400, "verdict": "WITHIN"}

    $ python tools/diff_budget.py 84514a0280f45d29e5066bb3be3d273ba73798db --ceiling 400 --paths src
    {"areas": {"src": 41}, "total_insertions": 41, "ceiling": 400, "verdict": "WITHIN"}

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
    src/deepreason/application/results.py
    src/deepreason/application/text_runs.py
    tests/test_checkpoint_hardening.py
    tests/test_results_command.py

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
document edited while the ring ran, as "a committed root moved". Its predicate
now selects only tracked files whose own directory carries a `log.jsonl` — a
run root — and the assertion is unchanged. Re-run:

    $ PYTHONPATH=.../src python -m pytest tests/test_checkpoint_hardening.py -q -p no:randomly
    3 passed in 5.19s

MUTATION PROOF that the narrowed control is not vacuous
(`proof/RED-byte-unchanged-mutant.txt`) — one byte appended to a committed
root's `log.jsonl`, the test run, the byte removed:

    E   AssertionError: a committed root moved: [' M experiments/2026-08-13-defect-controller-steering-inert/failed-epoch1-run-8e22d0431fd2b98d/log.jsonl']
    1 failed in 0.51s

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
output file is byte-identical after S7. That is an independent confirmation,
over 59 real roots rather than one fixture, that S7's default path is
behaviour-identical — which is what SPEC.md P-FIX-2 predicted and what allowed
the six-key exact-set assertion to stay put.

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

## Summary

| SPEC item | delivered | acceptance |
|---|---|---|
| S1 CONTINUE integrity gate | NO — parked F9 | passed when armed; reverted after ring #1 |
| S2 AMEND integrity gate | NO — parked F9 | passed when armed; reverted after ring #1 |
| S3 one-byte differential | proven, as an instrument | `proof/forge_one_byte.json` |
| S4 witness regression | NO — parked with S1/S2 | population preserved in `proof/census.json` |
| S5 failure terminal records uncontinuability | YES | RED -> GREEN, in ring #3 |
| S6 no-checkpoint terminal records it | YES | RED -> GREEN, in ring #3 |
| S7 reader answers from the verdict it holds | YES | RED -> GREEN; census.json byte-identical over 59 roots |
| S8 map moves in the same commit | YES | docs_verify 9 failed = baseline, delta ZERO |
| S9 instruments committed | YES | census exit 0, population 59, tree clean |

VERDICT: **PARTIAL.** Limb two of the P2 law is delivered and proven. Limb
three is not, and is parked with its implementation, its proof, and a
ready-to-send re-plan.
