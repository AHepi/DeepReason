# Diagnosis: the security channel's authority census has no branch for the one task kind the defended trial writes

## Stop report, section 4 (pasted verbatim, before anything of mine)

Source: `deepreason stop-report experiments/2026-09-09-fix-solo-criticism-authority/runs/home-solo/runs/run-02818acc38961781e2e820d0d6b591fb`
(full report at `proof/STOP_REPORT_live_root.txt`).

    ## 4. THE STOP, CLASSIFIED
    
    Stop message: `(none recorded)`
    
    Boxes ranked by evidence:
    
    ### 1. CONFIGURATION — RULED OUT
    
    - evidence RULING IT OUT: the run reached a clean terminal (state='completed', stop_reason='budget_exhausted'); there is no failure to attribute. Section 5 reports whether it can be continued.
    
    ### 2. ENVIRONMENT — RULED OUT
    
    - evidence RULING IT OUT: the run reached a clean terminal (state='completed', stop_reason='budget_exhausted'); there is no failure to attribute. Section 5 reports whether it can be continued.
    
    ### 3. MODEL — RULED OUT
    
    - evidence RULING IT OUT: the run reached a clean terminal (state='completed', stop_reason='budget_exhausted'); there is no failure to attribute. Section 5 reports whether it can be continued.
    
    ### 4. HARNESS — RULED OUT
    
    - evidence RULING IT OUT: the run reached a clean terminal (state='completed', stop_reason='budget_exhausted'); there is no failure to attribute. Section 5 reports whether it can be continued.
    

Section 5 of the same report, because it is half the defect:

    - verify_root: {"checks": [], "source": "stored", "violations": 0}
    - continue: **ACCEPTED** — the run is at a terminal and carries no lifecycle refusal
    - amend: **ACCEPTED** — the run is at a terminal and carries no lifecycle refusal

The report ranks all four boxes RULED OUT because the run reached a clean
terminal. It is right: nothing about the RUN failed. What failed is an
instrument reading the run afterwards, which is why no box holds it.

Primary cause: `verification/report.py::_transaction_findings` decides a v6 work
transaction's authority by an `if/elif` chain over `preparation.task_kind.value`
whose last arm is `else: differences.append(f"unknown v6 task kind {task!r}")`
(report.py:972). The chain has arms for `conjecture`, `criticism`,
`bridge_ledger`, `bridge_composition`, `bridge_review`, `scratch_authoring` and
`repair` — seven of the eight members of `WorkflowTaskKind`
(`workflow/models.py:152-160`). The eighth, `DEFENDED_TRIAL_STEP`, was added
when the defended trial was wired through `InquiryTransactionService`
(2026-08-13) and no arm was added with it, so every trial step falls to the
`else` and is emitted as a `security :: transaction-authority` finding.
`VerificationReportV2.valid` is integrity AND security, so ONE trial step is
enough to make a completed, replay-clean run report `valid: false`. This is a
READER gap, not a writer defect: the record is well-formed, replays to zero
violations, and the very authority the census cannot name is already frozen
into the manifest that run bound.

Evidence:

  - `proof/STOP_REPORT_live_root.txt` §5 -> `verify_root: violations 0`,
    `continue: ACCEPTED` on the live root, while the report on the same root
    says `valid: false` with 76 security findings
    (`experiments/2026-09-09-fix-solo-criticism-authority/proof/LIVE_VERIFICATION_CHANNELS.txt`).
    Two instruments, one record, opposite verdicts.
  - `proof/LIVE_ROOT_TASK_KIND_CENSUS.txt` -> over the live root's own
    `workflow_state.transaction_work`: 34 `conjecture`, 18 `criticism`, 7
    `repair` and 75 `defended_trial_step`. The 75 are exactly the 75 findings.
    Their (payload schema, payload role, lease role, lease seat, contract id)
    tuples are four shapes only:
        33  defended-trial-step.v1  judge     judge     0  judgeruling.direct.v1
        17  defended-trial-step.v1  defender  defender  0  defender.direct.v1
         8  defended-trial-step.v1  variator  variator  0  variator.direct.v1
        17  hv-variation-step.v1    variator  variator  0  variator.direct.v1
  - `proof/REPRO_stub_before.txt` -> a stub root on the PRE-EXISTING
    `ENGAGED_CRITICISM_AUTHORITY=defended_trial` road, one cycle: `verify_root`
    violations 0, report `valid: false`, three `transaction-authority` findings,
    all `unknown v6 task kind 'defended_trial_step'` (defender + two judge
    seats). None of the 2026-09-09 solo switches are involved, which is how we
    know the gap predates that tranche.
  - `proof/COMMITTED_ROOT_CENSUS_before.txt` -> the five committed roots that
    carry a `defended_trial_step` preparation, each with its stored
    `REPLAY_VALIDATION.json` verdict beside its recomputed report. This is the
    tranche's before-baseline; nothing may move except the trial-step findings.
  - `src/deepreason/run_manifest.py:1979-2100`
    (`_route_seat_behavioral_contract_assignments`) -> the manifest ALREADY
    carries the frozen grant the census cannot read. Trial contracts are
    assigned to the `defender`/`judge`/`variator` route seats **exactly when
    `criticism_policy.authority == "defended_trial"`**, and the live root's
    stored `route_seat_behavioral_capability_plan` shows them:
    `defender[0] -> defender.direct.v1`, `judge[0] -> judgeruling.direct.v1`
    (+ the grounding contract), `variator[0] -> variator.direct.v1`. The live
    root's `criticism_policy.authority` is `defended_trial`. So the authority
    the finding says is exceeded is written down, in the same manifest, in the
    field built for it.

Implicated code:
  - `src/deepreason/verification/report.py:972` — the `else` arm that emits it
    (the chain it closes starts at :790).
  - `src/deepreason/workflow/models.py:160` — `DEFENDED_TRIAL_STEP`, the kind
    with no arm.
  - `src/deepreason/informal/trial.py:63-130` — `_v6_transactional_trial_call`,
    the ONLY writer of this kind, and therefore the definition of what a
    correct trial step looks like: `role` in {defender, judge, variator},
    `seat` = the judge-ensemble index, `contract_id` from `wire_contract_for`,
    payload `{schema, role, target_id, step}`. `measures/hv.py:157-170` reaches
    the same writer through its alias `v6_transactional_phase_call` with
    `task_payload_schema="hv-variation-step.v1"`, which is why the kind covers
    two payload schemas and a branch that recognises only one would leave 17 of
    the live root's 75 still reported.

Falsifiable prediction (what `dr-reproduce` must show if this is right):

    python experiments/2026-09-10-defect-defended-trial-authority-census/proof/stub_defended_trial_root.py <tmp>
      -> verify_root violations: 0
      -> report valid: False
      -> security findings: N > 0, every one of them
         "unknown v6 task kind 'defended_trial_step'"
      -> integrity findings: 0

    and, mutating ONLY the reader (adding an arm that accepts the kind
    unconditionally), the same root must report `valid: True` with zero
    security findings and its `log.jsonl` byte-identical — proving the cause is
    in the reader and not in what the run wrote.

Ruled out: **the writer.** The hypothesis that the trial records something the
manifest never granted was checked against the manifest itself and fails on
three independent counts. (1) `verify_root` returns ZERO violations on both
roots, and `workflow/replay.py:2393` already runs
`_validate_preparation_behavioral_authority` over EVERY durable preparation —
so each trial step's `(role, seat, contract_id)` has already been proved to sit
inside the manifest's frozen `route_seat_behavioral_capability_plan` before the
security census ever looks at it. (2) The live root's own plan lists exactly the
three trial contracts on exactly the three trial roles. (3) `run_manifest.py`'s
own comment at :3617-3634 records that the compile-time refusal for this case
(`V6_DEFENDED_TRIAL_TRANSACTION_CONTRACT_REQUIRED`) was RETIRED on 2026-08-13
because the wiring made it moot — the same commit that created the kind. The
writer was finished; the reader was not.

## Not this tranche's, parked

See `PARKED.md`. The disagreement between `terminal.continuation_authority`
(true) and the security channel (invalid) is IN scope only as a statement in
VERIFY.md; changing the continuation gate is not.
