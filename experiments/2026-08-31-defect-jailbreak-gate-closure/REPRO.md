# Reproduction: the jailbreak is open on today's HEAD, and the narrowed predicate separates

Two artifacts, both offline, both against COMMITTED roots, both re-runnable.
Neither modifies a committed root: each works on a `copytree` that is thrown
away, and `git status` over the prior tranche's directory is empty after the
first one runs (it is deterministic and rewrote its own JSON byte-for-byte).

## 1. The defect, end to end — RED on today's tree

    python experiments/2026-08-30-change-checkpoint-hardening/proof/forge_amend_ready.py

Transcript: `proof/RED-forge_amend_ready.txt`. Run on HEAD `7f11c0718`:

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

Confirms DIAGNOSIS.md's primary cause exactly: the two arms differ ONLY in
`verify_root_violations`, and both verbs behave identically across that
difference. It also confirms the ruled-out alternative in the same table —
`stored_replay_valid` is `True` on the forged arm, so a gate reading the
published verdict rather than re-deriving it is defeated by this same forgery.

## 2. The narrowing separates — the predicate the fix will use

    python experiments/2026-08-31-defect-jailbreak-gate-closure/proof/security_channel_separation.py

Transcript: `proof/RED-security_channel_separation.txt`; data:
`proof/security_channel_separation.json`. The probe evaluates the shipped
helper if it exists and its DEFINITION otherwise, so the same file is the
before-and-after instrument. On HEAD `7f11c0718` (definition arm):

| root | all `verify_root` checks | SECURITY channel | gate refuses |
|---|---|---|---|
| `2026-08-26-pc2-rematch/run_h3` | — | — | False |
| `…/retired-transport-timeout180-run-42ad2880…` | — | — | False |
| `…/retired-truncation-cap32768-run-58fb0d20…` | attempt-accounting, attempt-blobs, attempt-order, repair-metadata | — | False |
| `2026-08-13-…/failed-epoch1-run-8e22d043…` | — | — | False |
| `2026-08-13-…/failed-epoch3-run-8e22d043…` | — | — | False |
| `…/selfstudy/runs/failed-epoch4-run-9175f0ec…` | — | — | False |
| `…/referee/runs/run-e542c3c1…` | foreign-criticism | — | False |
| `2026-08-27-pc2b-symmetric-reasoning/run` (intact) | — | — | False |
| `2026-08-27-pc2b-symmetric-reasoning/run` (**forged**) | attempt-route, frozen-route | **attempt-route, frozen-route** | **True** |

    separates: True

The third and seventh rows carry the load: those roots ARE replay-invalid
today — four integrity findings and one completion finding between them — and
the predicate leaves them alone. That is the whole difference between the gate
this tranche lands and the one the 2026-08-30 tranche reverted.

## 3. The road NOT taken, measured on the largest committed root

Data: `proof/big_root_channels.json`, on
`experiments/2026-08-12-live-grounded-extension-expansion/run` (12,991 events):

    verify_root violations : []
    report security count  : 495  {'transaction-authority': 494,
                                   'run-result-verification': 1}
    sources                : {'derived': 494, 'terminal': 1}
    security_valid         : False
    a sample detail        : "work sha256:00e7f63d7366 exceeds frozen
                              authority: unknown v6 task kind
                              'defended_trial_step'"

A gate on `verify_root_report(root).security_valid` refuses this root. The
detail says why, and it is not tampering: the current authority table does not
recognise a task kind an older version wrote. Refusing it would contradict the
2026-08-14 operator law that old runs owe the future nothing, and it is the
"right but breaks lawful continues" failure mode GOAL.md names as a stop
condition. `verify_root`'s own violation list on the same root is EMPTY, so the
narrowed predicate is silent here.

## What is reproduced, and what is not

REPRODUCED: the defect (1), the narrowing's separation on nine roots (2), and
the rejection of the report-form road on the one root where the two roads
disagree (3).

NOT reproduced here, and carried from the 2026-08-30 tranche and this
tranche's own diagnosis rather than re-derived: the eight lifecycle collisions
staying green under the narrowed gate (measured as `8 passed in 1469.92s` with
the gate reached 34 times and zero security findings, and independently as
`65 passed` on the three amend-path files with the gate evaluated 48 times and
refused 0). Those become this tranche's own gate evidence at
`dr-verify-outcome`, where the gate is armed for real rather than simulated by
a plugin.
