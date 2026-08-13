# REQUEST.md — defended_trial criticism authority wired into v6

Tranche: `experiments/2026-08-13-change-defended-trial-wiring/`
Branch: `claude/v6-defended-trial-wiring-07hs1u`
Captured: 2026-08-13, dr-capture-request phase.

## Map preflight (ids resolved before any design)

- `DR-SUB-workflow` (`docs/map/SUB-workflow.md`) — the v6 transactional work
  lifecycle: `InquiryTransactionService`, `WorkflowTaskKind`,
  `nonconjecture_recovery.py`.
- `DR-SEAM-llm-x-workflow` (`docs/map/SEAM-llm-x-workflow.md`) — the agreement
  every provider call must satisfy under RunManifest v6: no dispatch without
  an `AuthorizedDispatch`.
- `DR-SUB-adjudication` (`docs/map/SUB-adjudication.md`) — status semantics;
  read only to confirm the trial's warrant-minting shape is unaffected.
- `DR-SEAM-adjudication-x-rules` (`docs/map/SEAM-adjudication-x-rules.md`) —
  confirms `informal/trial.py` is the one site outside `rules/` allowed to
  mint a warrant, via `register_fail_warrant`; this tranche does not touch
  that minting, only how the trial's own provider calls are authorized.
- `DR-INV-frozen-surfaces` (`docs/map/INV-frozen-surfaces.md`) — the five
  frozen surfaces; `run_manifest.py` (surface 4) is touched under the
  pre-granted scope below, `harness.py` (surface 2) only if additive.

## Operator's verbatim words (2026-08-12), captured as the task's AUTHORITY block

> defended_trial criticism authority is compile-refused for v6 runs
> (V6_DEFENDED_TRIAL_TRANSACTION_CONTRACT_REQUIRED, run_manifest.py) because
> the defender/judge trial logic (informal/trial.py) has never been wired
> into v6's transaction system. Every v6 provider call requires a
> dispatch_authorization (llm/adapter.py's transaction_authority_required
> guard, unconditional); the trial calls don't carry one. Deleting the
> compile-time check doesn't fix this — it turns a clean, free, pre-run
> refusal into a live crash (WorkflowAuthorizationError) mid-cycle, after
> cost is spent, the first time a defender call fires. A second, independent
> gap: existing v6 crash-recovery for criticism (nonconjecture_recovery.py)
> hardcodes observe_only regardless of actual policy — documented as
> unresolved and untested for defended_trial. Real fix is two pieces: (1)
> wire informal/trial.py's defender/judge calls through
> InquiryTransactionService the way the ordinary critic call already is;
> (2) correct the recovery-authority downgrade so a resumed defended trial
> doesn't silently become observe-only.

## Numbered requirements

- **R1.** Wire the defended-trial (argument-trial) path's defender and judge
  provider calls in `informal/trial.py` through `InquiryTransactionService`
  the same way the ordinary batch-critic call in `rules/crit.py`
  (`_v6_transactional_batch_call`) already is: staged, authorized, consumed,
  recorded — no bypass of `llm/adapter.py`'s `transaction_authority_required`
  guard, which stays unconditional.
- **R2.** `workflow/nonconjecture_recovery.py` must resolve the criticism
  authority actually compiled into the run (`manifest.criticism_policy.authority`
  or the frozen `dispatch_authority` payload field for school-free dispatch)
  instead of hardcoding `observe_only` when recovering a crashed criticism
  transaction. A resumed defended-trial-authorized run must not have its
  policy silently downgraded to observe_only.
- **R3.** Only once R1 makes the contract satisfiable: convert
  `V6_DEFENDED_TRIAL_TRANSACTION_CONTRACT_REQUIRED`
  (`run_manifest.py`) from a compile-time refusal into either (a) retirement,
  if the wiring makes it moot, or (b) a typed `CompileNoticeV1` disclosure for
  any sub-case that remains genuinely unwired — never a refusal, per the
  operator's standing "all configurations should be allowed" law
  (CLAUDE.md, 2026-08-12). Must not land before R1 is green (operator's own
  words: deleting the gate first turns a free pre-run refusal into a paid
  mid-cycle crash).
- **R4.** Regression tests for both recovery directions: an observe_only run
  resumes observe_only; a defended_trial run resumes defended_trial (not
  silently downgraded), modeled on `tests/test_l1_continue_resumable_crash.py`'s
  fixture discipline.
- **R5.** An offline regression proving R1: a v6 run fixture with
  defended_trial authority where a defender call dispatches carrying a
  `dispatch_authorization` (mock endpoint) — the primary proof.
- **R6.** One guarded live attempt (tokens are cheap, agent time is not):
  compile a v6 config with `ARGUMENTATIVE_AUTHORITY=trial_required`,
  `ADJUDICATION_STATUS_AUTHORITY_ENABLED=true`, `JUDGE_SEATS_ENABLED=true`,
  `--blind-same-model-judges` on glm-5.2, small cycle/token budget. A trial
  firing live with zero replay violations is the headline; a run where no
  trial fires is recorded INCONCLUSIVE per the stochasticity doctrine — the
  offline regression (R5) remains the proof either way.
- **R7.** Surface contacts, pre-granted and scoped to this diagnosis
  (additive/widening only):
  - Surface 4 (`run_manifest.py`) — the named gate's conversion (R3), model
    AND validator together, PLUS whatever behavioral-capability-plan
    widening R1 needs to grant defender/judge/variator route seats a wire
    contract under v6 (compile-side counterpart of R1's dispatch-side wiring
    — without it, R1's calls would authorize on the dispatch side but still
    be refused by `resolve_route_seat_behavioral_capability` on the render
    side).
  - Surface 3 (replay-validation readers) — ONLY as additive reading of the
    new trial-transaction records, cp1m reader-widening precedent.
  - Surface 2 (`harness.py`) — ONLY if a new record kind needs an additive
    event-application entry, same shape as
    `record_capability_transition`'s existing additive extensions.
  - LAW, not caution: every committed root must replay byte-unchanged —
    prove with a targeted `verify_root_report` on a known-good root at
    validation.
  - Surface 5 contact (qualification digest drift): REPORT the
    requalification cost in DELIVERY.md, do not stop.
- **R8.** Enumerate every surface contact in SPEC.md's census with its grant
  line quoted.
- **R9.** Map documents move in the same commits as the code (`SUB-workflow`'s
  and `SUB-adjudication`'s trial rows both move, if their content becomes
  stale).
- **R10.** If any committed document claims defended_trial already works on
  v6, that is a `docs/ERRATA.md` entry (next free number).
- **R11.** GATE discipline: ring while iterating, full gate at the boundary.
  Known baselines: 1 pre-existing `test_bronze_report` failure; 5
  MCP-thread tests known-flaky under `-n 4` (isolate before attributing).
  `docs_verify` full: 3 pre-existing `CON-run-identity.md` shallow-clone
  failures.
- **R12.** Commit and push every phase boundary (retry 2s/4s/8s/16s). Deliver
  with R-by-R reconciliation and PROOF pasted per authoring-skills G1 — gate
  output, not the word "done".

## Scope note carried from the task dispatch (not the operator's own words,
## but the executing agent's binding instructions for HOW to run this tranche)

Route through `dr-change-orchestrator`, all phases through `dr-deliver-change`
WITHOUT stopping for interactive approval — design authority is the
operator's diagnosis above, already complete. The task dispatch also fixed
the dependency order: (1) TRIAL WIRING, (2) RECOVERY, (3) ONLY THEN the
compile gate — mirrored above as R1 < R2 < R3 (R3 gated on R1).

## Amendments

(none yet)
