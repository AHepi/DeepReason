# Goal: a stopped run whose record verifies intact is resumable by `continue`, whatever terminal it reached

Class: defect

Observed: three committed roots, each a different terminal shape, all
refuse `continue` while their own records report no integrity problem.

- **Shape 1 — failed terminal.** `experiments/2026-09-01-live-all-modules-p-a1/run`
  (run `4565139800f5ca020e2b74acff45355c1277a9d510068a8e8b4ed65813f1a49c`)
  `run-status.json`: `state: failed`, `stop_reason: operational_failure`,
  `terminal_lifecycle_refusal: TERMINAL_LIFECYCLE_NOT_TAKEN_FAILURE_TERMINAL`,
  at cycle 5 after 1 093 086 spent tokens of a 3 000 000 budget.
- **Shape 2 — killed run, then finalized.** `experiments/2026-09-02-live-p-a2-corrected/run`
  (run `63e48f57415d05323b608a84f138ee5c22c274d7d8ebccc2e219b613d7c3a722`, epoch 4)
  `run-status.json`: `state: running`, `stop_reason: null` after a container
  kill at cycle 4; `continue` refused `CONTINUE_STOP_REQUIRED`;
  `deepreason finalize` wrote a clean `budget_exhausted` terminal and
  `continue` is STILL refused
  `STOPPED_REFUSES_UNFINISHED_WORKFLOW_AUTHORITY` ("10 outstanding work items")
  — `RESULTS.md` Segment 8, F8.
- **Shape 3 — ordinary clean completion.**
  `experiments/2026-09-03-change-provenance-history-channel/` PARKED.md P1:
  a four-cycle run that reached `state: completed`, `stop_reason:
  budget_exhausted`, exit code 0, 47 admitted conjectures, still carries
  `terminal_lifecycle_refusal: STOPPED_REFUSES_UNFINISHED_WORKFLOW_AUTHORITY`,
  and `results --json` on the same root reports `"stop_reason_resumable": true`
  while `continue` refuses `CONTINUE_TYPED_STOP_REQUIRED`. Two typed records
  disagree about one root.

The law this contradicts (operator, 2026-08-29, verbatim in CLAUDE.md):
"clean stop. with an assurance that continuing is possible. ... I don't
want a jailbroken run to be continuable." Ledgered reading: EVERY terminal
— clean or failed — must leave checkpoints sufficient for relaunch; a stop
that cannot assure continuability is itself a defect; and `continue`/`amend`
are gated on the record verifying intact (that gate is on main since
971860c42, `runtime/continuation.py` `record_verification_refusal`).

Success criterion (machine-decidable):

    python -m pytest tests/test_stopped_run_resumption.py -q
    # 0 failed. The file carries, for EACH of the three shapes, a pair:
    #   GREEN: a stub root driven to that shape; `continue` is accepted and
    #          the run reaches a cycle number strictly greater than the one
    #          the stop recorded.
    #   RED:   the same stub root with one byte of log.jsonl altered;
    #          `continue` is refused with the integrity gate's own typed code
    #          (RECORD_VERIFICATION_* from runtime/continuation.py), NOT with
    #          a lifecycle refusal.

    python -m pytest tests/ -q -n 4
    # 0 failed (full gate at the phase boundary).

Plus two record-agreement checks in the same file:

    # run-status.json `terminal_lifecycle_refusal` and `results --json`
    # `stop_reason_resumable` describe the SAME root consistently — a
    # fixture that fails if they disagree again.

In scope (max 3):
- `src/deepreason/application/text_runs.py` (the terminal/receipt write path)
- `src/deepreason/runtime/continuation.py` (the `continue`/`amend` gate)
- `src/deepreason/workflow/lifecycle.py` (the "unfinished workflow authority" predicate)

NOT in scope: seat-level degradation — one seat's terminal exhaustion
retiring the seat instead of the run (`llm/adapter.py:524`). That is the
mechanism that KILLED P-A1; making a killed run resumable is this tranche,
stopping it dying is not. Parked with a prompt.

Also NOT in scope, parked: the jailbreak tranche's P2 ("a record too
corrupt to replay passes the gate",
`experiments/2026-08-31-defect-jailbreak-gate-closure/`), which this fix
WIDENS EXPOSURE TO without widening the residue itself; and budget
exhaustion terminating as `operational_failure` anywhere else (check,
record, park).

Budget: <=150 changed lines, 1 commit for the fix (map in the same commit),
~1 working session.

Stop conditions inherited from orchestrator: yes. Named additionally by the
window instruction: any contact with a frozen surface; any NEW record format
or event kind; any change to the jailbreak gate's predicates; and a record
showing the three shapes are NOT one defect (then STOP and propose a split).

## Map preflight (DR- ids resolved before any design)

Read in this order, per `dr-drive-harness` §4:

1. `docs/map/INDEX.md` — routing.
2. `docs/map/INV-frozen-surfaces.md` — the five surfaces (seven paths).
   Forecast: this tranche touches NONE. `harness.py`,
   `capabilities/state.py`, `invariants.py`, `verification/`,
   `run_manifest.py`, `qualification.py` and `llm/firewall.py`'s
   `route_fingerprint` are untouched; any contact is an immediate stop.
3. Subsystems and concepts that own the in-scope paths:
   - `DR-SUB-application` — owns `src/deepreason/application/`,
     `src/deepreason/runtime/`, `src/deepreason/cli/`.
   - `DR-CON-run-identity` — owns `application/text_runs.py`,
     `runtime/continuation.py`, `runtime/progress.py`, `ui/status.py`.
   - `DR-SUB-workflow` — owns `src/deepreason/workflow/`.
   - `DR-SUB-verification` — owns `invariants.py`, `verification/`. READ
     ONLY: the integrity gate is consumed, never modified.

**Map finding, recorded not deferred.** The two seams this defect actually
lives on are BOTH undocumented, and `INDEX.md` says a pair listed without a
document "has NOT been shown to be uninteresting":

- `application x workflow` — declared `Seams-undocumented:` by BOTH
  `SUB-application.md` and `SUB-workflow.md`. This is exactly the seam
  where the STOPPED receipt meets the outstanding-work-item predicate,
  i.e. the seam shapes 2 and 3 die on.
- `application x run-identity` — declared `Seams-undocumented:` by both
  `SUB-application.md` and `CON-run-identity.md`. This is the seam where
  the terminal write meets the `continue` gate.

Per `dr-drive-harness` §4 item 5 this is a finding, not a blocker. Writing
`SEAM-application-x-workflow.md` becomes part of this tranche if the fix
lands there; otherwise it is parked with a prompt.
