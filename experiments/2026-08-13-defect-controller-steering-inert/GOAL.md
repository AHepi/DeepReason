# Goal: make the dynamic token-steering controller actually fire on runs launched through the one door

Class: defect

Observed: the grounded-extension root
`experiments/2026-08-12-live-grounded-extension-expansion/run` (run id
`8e22d0431fd2b98dc915c66f2f3ccc6dc43184b4c326ff5d388a7c013a80989d`,
state `completed`, stop_reason `budget_exhausted`, 12,991 log events
across both epochs) contains ZERO token-steering artifacts: measured on
the committed `log.jsonl`, the substring counts for `cap:`, `envelope`,
`referee`, `steer`, `policy_eval` and `knob` are all 0, while
`config.py` defaults `CONTROLLER=True` and `ops.run_scheduler`
constructs `Controller(harness, adapter)` when it is true
(`src/deepreason/ops.py` ~407).

TRAP (recorded by the operator, verified here): the log's 3,380
`rule="Control"` events are workflow TRANSACTION records
(`control.event.v3`, action census: 2,702 `work_transition`, 666
`provider_result`, 3 `contract_decomposition_activated`, 3
`contract_decomposition_completed`, 2 `lifecycle_stopped`, 2
`terminal_committed`, 1 `classification_bound`, 1 `lifecycle_resumed`).
They are NOT steering-controller records and must never be counted as
such.

Consequence in the same record: rule mix Conj 42 / Spawn 2,894 /
Crit 16 / Measure 6,556 / Register 85 / Scratch 14 / Refl 4; generation
ran against the profiles' static `max_tokens` pins because nothing
steered.

Success criterion (machine-decidable):

    python -m pytest tests/test_controller_steering_parity.py -q
    -> passes, and its assertions are:
       (1) a run started through
           application/text_runs.py::TextRunApplicationService.start_manifest_run
           from a COMPILED manifest records controller attachment in the
           typed record;
       (2) that same run records at least one controller policy
           evaluation OR the typed nothing-to-steer record when the
           controller is ON but has no envelope it may steer within;
       (3) the controller's envelope table covers EVERY role the
           manifest binds (judge and defender included);
       (4) the managed-path (`deepreason reason`) fixture record is
           byte-unchanged against its pre-fix bytes.

    python -m pytest tests/ -q -n 4
    -> N passed, 0 failed

    python tools/docs_verify.py
    -> 0 failed

    python tools/root_sweep.py   (42 committed roots)
    -> no committed root's verdict moves

In scope (max 3):
  - `src/deepreason/controller.py` (envelope table, `_propose`, the
    inert path)
  - `src/deepreason/ops.py` (`run_scheduler` controller construction /
    attachment on the one door)
  - `src/deepreason/config.py` + the compiled-manifest carry of
    `CONTROLLER` (whichever of `run_manifest.py` / `v6_policy.py` /
    `application/text_runs.py` the diagnosis names — at most one of
    them, chosen after DIAGNOSIS.md)

NOT in scope: the scheduler-side debt-vs-spawn problem selection defect
(why `Crit` dispatched 16 times against 380 criticism-coverage-debt
records). If diagnosis surfaces it, it is PARKED with a ready prompt —
one tranche, one goal: the steering loop fires.

Budget: <=150 changed lines, 1 commit for the fix (phase-boundary
commits for artifacts are separate), ~1 working session.

Stop conditions inherited from orchestrator: yes.

## Map preflight (ids resolved before any design)

Read in order: `docs/map/INDEX.md` -> `docs/map/INV-frozen-surfaces.md`
-> the seam -> the subsystems.

Resolved ids:
  - `DR-SUB-application` — owns `src/deepreason/application/`,
    `cli/`, `runtime/`; the one door
    (`start_manifest_run`) lives here.
  - `DR-SUB-scheduler` — owns `src/deepreason/scheduler/`;
    `Scheduler._maybe_config_referee` (scheduler.py:695) and its call
    site (scheduler.py:1897) are the referee cadence.
  - `DR-SUB-manifest` — owns `run_manifest.py`; **FROZEN** (manifest
    schemas + validators). Any change here needs explicit operator
    approval.
  - `DR-SUB-harness` — owns `harness.py`; **FROZEN** (event
    application). New typed records must go through existing event
    application, not new well-formedness rules.
  - `DR-SUB-verification` — owns `invariants.py`/`verification/`;
    **FROZEN** (replay-validation record formats). Old roots must
    replay byte-unchanged.
  - `DR-SEAM-scheduler-x-workflow`, `DR-SEAM-harness-x-workflow` — the
    documented seams nearest the control path.

MAP GAP (a finding, not a blocker — recorded per dr-drive-harness §4.5):
no map document `Owns:` any of `src/deepreason/controller.py`,
`src/deepreason/ops.py`, `src/deepreason/config.py`,
`src/deepreason/referee.py`, `src/deepreason/control_events.py`,
`src/deepreason/v6_policy.py`. Verified by reading every `Owns:` line
in `docs/map/SUB-*.md`; `SUB-periphery.md` claims "everything no other
map document owns" but its `Owns:` list does not name these files, so
its own `check:` does not cover them. Closing that gap for the files
this tranche touches is part of the tranche (map moves in the same
commit as the code).

## Errata note reserved

Next free ledger number is **E28** (tail of `docs/ERRATA.md` ends at
E27). Any committed document claiming the steering controller is live
on all runs earns E28.
