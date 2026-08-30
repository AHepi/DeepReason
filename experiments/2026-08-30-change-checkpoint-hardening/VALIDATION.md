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
