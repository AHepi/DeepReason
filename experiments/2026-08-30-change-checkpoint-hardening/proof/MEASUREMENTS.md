# MEASUREMENTS — the numbers SPEC.md rests on, and the command for each

Every figure here was produced in this worktree on 2026-08-30 by the scripts
beside this file. Nothing is carried from prose. Two figures ARE carried and
are labelled as such.

All four instruments are read-only against committed roots: they open no
writable harness on an original, and every probe that writes copies first. The
tree was clean after each (`git status --porcelain experiments/` empty).

Box condition, stated because it bounds the timings: this container is shared
with four other lanes of the same batch. Each instrument was run with no other
instrument of THIS lane running, but not on an idle box. The timings in M6 are
therefore upper bounds.

## The instruments

| script | output | what it answers |
|---|---|---|
| `census.py` | `census.json` | what all 59 committed roots say, and what the two verbs would do with each |
| `forge_probe.py` | `forge.json` | is the stored replay verdict tamper-evident |
| `gate_probe.py` | `gate_probe.json` | what `continue` and `amend` do TODAY with a replay-invalid record |
| `verify_cost.py` | `verify_cost.json` | what re-deriving the verdict costs, per root |

Two of the four carry a correction worth naming, because getting them wrong
produced a confidently wrong number first:
`derive_terminal_authority(root)` WITHOUT the bound manifest short-circuits to
`historical_read_only` for every root, which reads as "all 59 refused" and as
"every forge detected". Both scripts now load the manifest, and both say so in
a comment. The first, wrong run of each is not in the committed output.

## M1 — the census

    python experiments/2026-08-30-change-checkpoint-hardening/proof/census.py

    population: 59
    schema_version: {'6': 59}
    triples (state | stop_reason | amend_ready):
      completed | budget_exhausted | True  -> 23
      failed | operational_failure | False  -> 16
      completed | budget_exhausted | False  -> 13
      running | ABSENT:NO_STOP_RECORD | False  -> 4
      running | budget_exhausted | False  -> 1
      completed | converged | True  -> 1
      running | operational_failure | False  -> 1
    amend_ready: {'False': 35, 'True': 24}
    stored_replay_valid: {'True': 39, 'False': 16, 'ABSENT:NO_REPLAY_VALIDATION_JSON': 4}
    verification_source: {'stored': 55, 'ABSENT:NO_REPLAY_VALIDATION_JSON': 4}

## M2 — the two gaps, and the stranded root

Same run:

    authority_status: {'current_valid_committed': 54, 'current_open_uncommitted': 4, 'invalid_incomplete': 1}
    A2 gap (authority valid AND stored replay invalid): 16
    A1 failed without continuation authority: 15
    finalize population (current_open_uncommitted): 4
    stranded (neither amend nor finalize): 1
      experiments/live_research_2026-07-29/selfstudy/runs/failed-epoch2-run-9175f0ecb055e57455af3c50df153c5a
        authority_status invalid_incomplete
        authority_detail_code TERMINAL_REPLAY_VALIDATION_BINDING_INVALID
        stored_replay_valid true

CORRECTION to the reconnaissance this lane was handed: 15, not 16, of the
failed roots lack continuation authority. The one exception is
`experiments/2026-08-08-live-two-seat-ab-s6/home-s6/runs/failed-epoch1-run-8c77c6588485304d1f73416318c62949`,
which carries a resume decision from an earlier continuation. Recorded rather
than rounded — the 16 in the "failed / operational_failure" triple and the 15
in "no continuation authority" are different counts of different things.

## M3 — the stored verdict is not uniformly tamper-evident

    python experiments/2026-08-30-change-checkpoint-hardening/proof/forge_probe.py

    population: 16
    forge DETECTED on: 12
    forge UNDETECTED on: 4
      experiments/2026-08-02-stress-triplet/home-triage/runs/run-0a3e93d6e8031e2e6d1d21dde2fa93cc
      experiments/2026-08-04-change-rung5-dumb-alternative-backend/rr-home/runs/run-9a6be78e1e79184a0bd89923b957586c
      experiments/2026-08-08-corpus-enrichment-patrol-pilot/home/runs/run-e3f4f7007c50fe7e09b301d31851c3e7
      experiments/live_research_2026-07-29/selfstudy/runs/completed-epoch3-run-9175f0ecb055e57455af3c50df153c5a
    outcomes: {'invalid_incomplete / TERMINAL_REPLAY_VALIDATION_BINDING_MISMATCH': 12,
               'current_valid_committed / None': 4}

The forge writes CANONICAL bytes. An earlier version of this probe
pretty-printed the forged file and was caught on all 16 by
`TERMINAL_REPLAY_VALIDATION_NONCANONICAL` — a measurement of the probe's
formatting, not of the binding. The attacker the law names ("I don't want a
jailbroken run to be continuable") is one who read how the file is written, so
the probe writes it the way the product does.

## M4/M5 — what the two verbs do today, and what the verdict re-derives to

    python experiments/2026-08-30-change-checkpoint-hardening/proof/gate_probe.py

    run-e542c3c1                   294 ev  amend: PASSED  continue: REFUSED CONTINUE_TYPED_STOP_REQUIRED  verify_root 15.45s ['foreign-criticism' x5]
    run-9a6be78e (rr-home)         388 ev  amend: PASSED  continue: ACCEPTED seq=0                        verify_root 16.27s ['attempt-validity']
    run-d17935a4                   550 ev  amend: PASSED  continue: ACCEPTED seq=0                        verify_root 21.57s ['foreign-criticism' x4]
    completed-epoch2-run-9e9812fe  561 ev  amend: PASSED  continue: ACCEPTED seq=0                        verify_root 26.42s ['foreign-criticism' x3]
    run-faa5feae                   581 ev  amend: PASSED  continue: REFUSED CONTINUE_TYPED_STOP_REQUIRED  verify_root 25.47s ['foreign-criticism' x3]
    failed-epoch1-run-9175f0ec     594 ev  amend: PASSED  continue: REFUSED CONTINUE_TYPED_STOP_REQUIRED  verify_root 32.40s ['run-input']

`amend` PASSED on 6 of 6. `continue` ACCEPTED 3 of 6, and refused the other 3
for a reason unrelated to their records. On all six the re-derived verdict
AGREES with the root's own stored `valid: false` — the gate this tranche adds
recomputes the record's own published judgement, it does not invent a stricter
one.

The probe drives only witnesses under 600 events. That is a runtime budget,
stated as one: `verify_root` is O(run length), and the smallest witnesses
answer the same question as the largest.

## M6 — the price of re-deriving

    python experiments/2026-08-30-change-checkpoint-hardening/proof/verify_cost.py

       27 events     0.69s    25.7 ms/event  2026-08-26-pc2-rematch/run_h3
       31 events     0.74s    23.7 ms/event  retired-transport-timeout180-run-42ad2880
       62 events     1.80s    29.0 ms/event  retired-truncation-cap32768-run-58fb0d20
       64 events     3.07s    48.0 ms/event  failed-epoch1-run-8e22d0431fd2b98d
       79 events     4.59s    58.1 ms/event  failed-epoch2-run-8e22d0431fd2b98d
      114 events     8.10s    71.0 ms/event  failed-epoch3-run-8e22d0431fd2b98d
      161 events     5.62s    34.9 ms/event  failed-epoch4-run-9175f0ec
      188 events    11.38s    60.5 ms/event  failed-epoch1-run-0d1f88e1
      276 events    13.04s    47.3 ms/event  run-0c3ce902
      280 events    15.30s    54.6 ms/event  completed-epoch3-run-9e9812fe
      285 events    16.77s    58.8 ms/event  run-9e9812fe
      294 events    17.23s    58.6 ms/event  run-e542c3c1
      300 events    18.88s    62.9 ms/event  run-5a771259

CARRIED, NOT RE-RUN (the two figures this lane inherited): 15.2 s at 300
events and 146.7 s at 3 751 events. The first is reproduced here within box
noise (18.88 s on a shared container). The second is not re-run: a
147-second measurement is not worth the box time when the shape is already
established by thirteen points.

## M7 — no frozen surface is touched

    python tools/blast_radius.py \
      --files src/deepreason/runtime/continuation.py src/deepreason/amendment/apply.py \
              src/deepreason/application/text_runs.py src/deepreason/application/results.py \
      --symbols prepare_continuation _require_terminal_stop terminalize_text_run _terminal

    "frozen_surface_contacts": []
    "frozen_adjacent_contacts": []
    "frozen_surface_verdict": "CLEAR"
    consumers.qualification_digest: []
    consumers.wheel_smoke_pins: []

## M8 — "containment-breach evidence" has no record to gate on

    grep -rn "containment" --include=*.py src/deepreason/ | wc -l   ->  77

Every hit is a limit, a timeout, or a free-text `sandbox_abort` trace string
(`verification/simulation.py`, `verification/runner.py`, `verification/lean.py`,
`v6_policy.py`). No event kind, no `verify_root` check, no receipt field.

    sed -n '119,129p' src/deepreason/verification/report.py

    _SECURITY_CHECKS = frozenset(
        {
            "attempt-route",
            "capability-authority",
            "capability-compiled-authority",
            "capability-grant",
            "capability-work-order",
            "frozen-route",
            "school-route",
        }
    )

Seven names, none about containment, in a file inside frozen surface 3.

## M9 — the map preflight could not be performed as written

    grep -n -iE "application|amendment|periphery" docs/map/INDEX.md
    46:| `SUB-harness.md` | the append-only log, event application, state materialization. **Frozen** |
    54:| `SUB-bridge.md` | the grounded-application bridge: ledger, compose, evidence packs |
    129:| — | periphery × verification | `SEAM-periphery-x-verification.md` |
    136:the periphery × verification and calculus × rules cases — every import between

    ls docs/map/ | grep -E "application|amendment|periphery"
    SEAM-periphery-x-verification.md
    SUB-amendment.md
    SUB-application.md
    SUB-periphery.md
