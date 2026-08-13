# SPEC.md — defended_trial criticism authority wired into v6

Traces to REQUEST.md R1–R12. Design authority: the operator's diagnosis is
already complete (REQUEST.md's AUTHORITY block); this SPEC is the concrete
mechanical plan, not a re-derivation of the diagnosis.

## 1. What currently happens (confirmed by reading, not assumed)

- `rules/crit.py::crit_argumentative_batch`, under a v6 manifest, already
  wires its OWN batch-critic call through `InquiryTransactionService` via
  `_v6_transactional_batch_call` (line ~278). That part is correct today.
- When a case attacks and `authority` resolves into `_TRIAL_MODES`
  (`"trial_required"`/`"single_family_trial"`), `_crit_argumentative_batch_result`
  (line ~1876) calls `informal.trial.run_argument_trial_from_case(harness,
  adapter, config, case.target, case.case, llm_pending, authority="status",
  critic_school_id=critic_school_id)` — **regardless of whether the run is
  v6**. Inside, `_argument_trial_steps` dispatches the defender call and
  every judge-ensemble call (`_judge_all`) through plain `adapter.call(...)`
  with **no** `dispatch_authorization`. Under v6
  (`transaction_authority_required=True`), `llm/adapter.py`'s global guard
  (`if self.transaction_authority_required and dispatch_authorization is
  None: raise WorkflowAuthorizationError(...)`) fires the first time the
  defender call is reached — confirmed against `SEAM-llm-x-workflow.md`'s
  own "Where it is expressed" table, first row.
- The rubric trial (`run_trial`, scheduler.py:1141) and pairwise
  discrimination (`pairwise_discriminate`, scheduler.py:1892) are each
  **already** guarded by `Scheduler._defer_untransactional_v6_phase` before
  they are ever called — under v6 they are typed completion debt, never
  dispatched. **Out of scope**: they are not broken today and this tranche
  does not touch them (confirmed: `_defer_untransactional_v6_phase`
  short-circuits with `continue` before `run_trial`/`pairwise_discriminate`
  is imported, for both call sites).
- `run_manifest.py::_validate_v6_capability_policy` refuses compilation
  outright when `manifest.criticism_policy.authority == "defended_trial"`
  (`V6_DEFENDED_TRIAL_TRANSACTION_CONTRACT_REQUIRED`), which is why the live
  crash above has never actually been observed in production — the gate
  makes the run un-launchable in the first place.
- `run_manifest.py::_route_seat_behavioral_contract_assignments` — the
  closed enumeration `resolve_route_seat_behavioral_capability` checks a
  wire contract against — does **not** cover the `defender`/`judge`/
  `variator` roles at all today. Even after R1's dispatch-side wiring, a
  defender/judge call would still be refused on the RENDER side
  (`"wire contract differs from frozen route-seat behavioral authority"`)
  unless this is widened. This is the concrete surface-4 contact named in
  REQUEST.md R7.
- `workflow/nonconjecture_recovery.py::_criticism_contract` (line ~643)
  refuses recovery outright (`"critic authority is not recoverable"`)
  whenever the manifest's `criticism_policy.authority` (school-bound branch,
  line 673) or the frozen `dispatch_authority` payload field (school-free
  branch, line 667) is anything other than `"observe_only"` — confirmed by
  the existing test
  `test_criticism_contract_refuses_recovery_without_a_school_when_dispatch_authority_is_not_observe_only`.
  `_recover_criticism_effect` (line ~282) then hardcodes
  `authority="observe_only"` at its call into `_crit_argumentative_batch_result`
  (line 352) — currently **dead code for any authority but observe_only**,
  because the gate above already refuses everything else before reaching it.
  Widening the gate (R2) without also fixing the hardcode would create a
  **live** silent-downgrade bug — exactly the failure mode the operator's
  diagnosis names.

## 2. Structural constraint that shapes the recovery design (R2)

`workflow/nonconjecture_recovery.py` has **no provider boundary by design**
(`SEAM-llm-x-workflow.md`, "Recovery has no provider boundary, and that is
the whole point of it" — `_recover_criticism_effect` is called with
`adapter=None`). A defended trial's downstream effect (defender + N judge
calls) requires a *live* provider. Recovery therefore cannot literally
"run the trial" for a case whose critic output is being recovered from a
crash. The correct typed behavior, consistent with the invariant above and
with the existing `Scheduler._defer_untransactional_v6_phase` precedent for
"a phase this run's policy authorizes, but this code path cannot currently
dispatch it":

- Resolve the run's REAL authority (not hardcoded).
- If real authority is `observe_only`: unchanged — `_observe_case` records
  the scrutiny evidence, exactly as before.
- If real authority is a trial mode and the case does **not** need the
  trial (grounded by counterexample, or execution-backed override): those
  branches run identically to the observe_only case already (no new
  provider call) — unaffected.
- If real authority is a trial mode and the case **would** enter the trial
  (attacking, not grounded, not execution-backed) **and no adapter is
  available** (the recovery signal — `adapter is None`, true only via this
  call site; every live caller of `_crit_argumentative_batch_result` always
  passes a real adapter): record a typed deferral `Measure`
  (`["defended-trial-deferred", target_id, "recovery-no-provider"]`) and
  mint nothing for that case this attempt. The target is **not** marked
  "observed" (a different, permanent, weaker outcome) and is **not**
  attacked — it simply remains open for the ordinary live criticism sweep
  to reconsider on a later cycle, when a real adapter exists. This is the
  same shape as `_defer_untransactional_v6_phase`'s "become visible
  completion debt instead of tripping the global guard," applied at the
  effect-application layer instead of the scheduler layer, because
  `_crit_argumentative_batch_result` has no `harness`-bound `Scheduler` to
  call that method on.
- If real authority is a trial mode and an adapter **is** supplied (the
  ordinary live path — this function is also called live, not just from
  recovery): dispatch the trial exactly as before, now correctly wired
  by R1.

This delivers exactly what REQUEST.md R2 asks: the run's compiled policy is
never silently downgraded to observe_only, and "a resumed defended-trial
run resumes as defended_trial" — its policy stays defended_trial, and any
case recovery genuinely cannot resolve is left open rather than
misrecorded, not silently answered under the wrong authority.

## 3. R1 mechanical design — trial provider calls through InquiryTransactionService

Template precedent (map preflight, both explicitly named by the task
dispatch): `rules/crit.py::_v6_transactional_batch_call` (the closest
same-package precedent) and `bridge/transactional_adapter.py::
TransactionalBridgeAdapter.call` (the generic single-call v6 wrapper: one
`prepare` → `context_plan` → `issue` → dispatch → `record_provider_attempt`
→ `record_semantic_admission` → `terminate` per call, no batching/atomic-
decomposition machinery needed — the trial's calls are not batchable, each
is its own bounded exchange).

New helper, `informal/trial.py::_v6_transactional_trial_call(harness,
adapter, manifest, *, role, target_id, step, pack, output_model, seat=0,
aliases=None)`:

- `role` is `"defender"`, `"judge"`, or `"variator"`.
- `step` is a caller-supplied string uniquely identifying this exact call
  within one trial invocation (`"defender"`, `"judge:0"`, `"judge:1"`,
  `"judge:paraphrase:0:0"`, `"variator"`, ...) — folded into the trigger
  digest exactly as `phase` is for the batch-critic call, so distinct calls
  never collide and an identical replay (recovery of the SAME crashed work
  item, not a fresh dispatch) is content-addressed.
- Builds the wire contract explicitly (`wire_contract_for(role,
  output_model, adapter.profile_for(role, seat, endpoint_lease=lease),
  aliases)`) exactly once, the same object passed to both `prepare()`'s
  `contract_id` and to `preview_request`/`call`'s `wire_contract=` — the
  same pattern `_v6_transactional_batch_call` uses, so there is no
  independent re-derivation to drift.
- Context plan: one `SOURCE`-namespace `VisibleContextItemV1` wrapping the
  exact rendered pack bytes, content-addressed — the same fallback shape
  `bridge/transactional_adapter.py::_context_seeds` uses for contracts with
  no reference catalog ("Direct review and repair contracts have no
  reference catalog. Bind the exact rendered pack as one content-addressed
  context object.").
- Full outcome handling mirrors `_v6_transactional_batch_call` exactly:
  `WorkBudgetDenied` re-raised untouched; any other pre-issue exception
  abandons (`trial_preissue_failure`) and re-raises; `EndpointError`
  records a `transport_failure` attempt and terminalizes
  `transport_failed`, marks `error.transaction_terminalized = True` and
  `error.spend = None`, re-raises (matches the seven-handler shape
  `SEAM-llm-x-workflow.md` documents); `SchemaRepairError` routes through
  `service.repair_schema_failure`; any other post-issue exception abandons
  (`trial_authority_failure`) and re-raises; success records the provider
  attempt, semantic admission, and a `completed` terminal
  (`trial_output_admitted`), returning `(output, llm_call)` exactly like
  `adapter.call` would.

Call sites, gated on `manifest is not None` (v6-bound), computed once at
the top of `_argument_trial_steps` as `manifest =
adapter.bound_v6_manifest() if getattr(adapter,
"transaction_authority_required", False) else None` and threaded as an
explicit parameter into the two helpers it shares with the (untouched,
out-of-scope) rubric path:

- **Defender call** in `_argument_trial_steps`: `step="defender"`.
- **`_judge_all`** gains `manifest=None` (default — preserves the rubric/
  pairwise call sites byte-for-byte, since they never pass it) and, when
  supplied, dispatches each ensemble seat's call with
  `step=f"{step_prefix}:{index}"` instead of the legacy `adapter.call`.
  `_argument_trial_steps`'s own call passes `step_prefix="judge"`.
- **`_paraphrase_screen`** gains `manifest=None` similarly: the variator
  call uses `step="variator"`; each paraphrase re-ruling's `_judge_all`
  call uses `step_prefix=f"judge:paraphrase:{index}"`.

No change to `_trial_steps` (rubric) or `_pairwise_steps`/
`pairwise_discriminate` call sites — they keep calling `_judge_all`/
`_paraphrase_screen` without the new `manifest` argument, so their behavior
is provably unchanged (default `None`, legacy `adapter.call` path).

`llm/adapter.py`'s `transaction_authority_required` guard is not touched —
R1 satisfies it, never bypasses it (REQUEST.md R1's own wording).

## 4. R7/R8 surface census (every contact, with its grant line quoted)

| Surface | File | Contact | Grant (REQUEST.md R7, quoted) |
|---|---|---|---|
| 4 (manifest schemas + validators) | `run_manifest.py::_validate_v6_capability_policy` | Convert `V6_DEFENDED_TRIAL_TRANSACTION_CONTRACT_REQUIRED` from `raise ValueError` to a `CompileNoticeV1` disclosure (or retire if moot), per R3 | "Surface 4 (`run_manifest.py`) — the named gate's conversion (R3), model AND validator together" |
| 4 (manifest schemas + validators) | `run_manifest.py::_route_seat_behavioral_contract_assignments` | Add `defender`/`judge`/`variator` role-seat contract-id assignments (additive: new tuples added to an existing `set`, no existing assignment removed or narrowed) | "...PLUS whatever behavioral-capability-plan widening R1 needs to grant defender/judge/variator route seats a wire contract under v6" |
| 2 (harness.py event application) | `harness.py` | **Not touched.** `WorkflowTaskKind.DEFENDED_TRIAL_STEP` reuses the existing generic `PROVIDER_RESULT`/transaction-work event-application path (`workflow/replay.py::_apply_transaction`) verbatim — the same code that already applies `WorkflowTaskKind.CRITICISM`/`BRIDGE_LEDGER`/etc. transitions; no new record KIND, no new branch. Confirmed by reading `_apply_transaction`: it dispatches on `TransitionKind`/`action`, not on `task_kind`. | Surface 2 contact avoided entirely — grant not needed, recorded here per R8's "enumerate every contact" so the absence is a finding, not a silent gap |
| 3 (replay-validation readers) | `verification/report.py`, `invariants.py` | **Not touched.** The new task kind's transactions replay and verify through the same generic `PROVIDER_RESULT` pairing/authority checks every other v6 transaction already goes through (`SEAM-llm-x-workflow.md`'s "Replay pairing" row) — no reader needs new knowledge of `DEFENDED_TRIAL_STEP` specifically. | Surface 3 contact avoided entirely, recorded per R8 |
| 5 (qualification subject digest) | `qualification.py::qualification_subject_payload` | The manifest's `route_seat_behavioral_capability_plan` (surface-4 change above) enters the qualification subject digest. Any run whose manifest changes shape (a run that configures defender/judge routes) requalifies (~14 min, ~1160 calls) the next time it is compiled after this lands. Runs with NO defender/judge routes configured are unaffected (the new assignment loop iterates `manifest.roles.get("defender", ())`, empty for those runs — no new tuple added, no digest change). | "REPORT the requalification cost in DELIVERY.md, do not stop" — reported at delivery, not gated here |

`capabilities/state.py` (surface 1) and `invariants.py::verify_root`'s own
format (part of surface 3) are not touched at all.

## 5. Acceptance checks per requirement

- **R1**: `tests/test_v6_defended_trial_transaction_wiring.py` (new) proves
  a defender call and a judge call each carry a `dispatch_authorization`,
  and that `llm/adapter.py`'s unconditional guard would have refused the
  same call without one (constructed the same way
  `SEAM-llm-x-workflow.md`'s own guard-probe check does).
- **R2**: two new tests in `tests/test_v6_nonconjecture_recovery.py` —
  observe_only resumes observe_only (extends the existing coverage);
  defended_trial resumes without downgrading to `_observe_case` (asserts
  the typed deferral Measure, not an `_observe_case`-shaped critic
  artifact).
- **R3**: `run_manifest.py` compiles a v6 manifest with
  `criticism_policy.authority == "defended_trial"` without raising;
  existing manifest-compile tests referencing
  `V6_DEFENDED_TRIAL_TRANSACTION_CONTRACT_REQUIRED` (if any) are found and
  updated in the same commit, per `docs/ERRATA.md`-worthy-if-missed
  discipline (R10).
- **R4**: satisfied by R2's two tests, modeled on
  `test_l1_continue_resumable_crash.py`'s fixture discipline (build a root,
  crash it mid-transaction, `Harness(root)` reopen, call
  `recover_nonconjecture_admission`, assert the log).
- **R5**: the offline regression is R1's own test file — the PROOF ladder's
  (a).
- **R6**: one guarded live attempt per REQUEST.md R6's exact config; judged
  by typed outcomes only (trial firing live = headline; no trial firing =
  INCONCLUSIVE, offline regression remains the proof).
- **R7/R8**: this section (§4).
- **R9**: `docs/map/SUB-workflow.md` and `docs/map/SUB-adjudication.md`
  checked for staleness after implementation; updated in the same commit
  if their content changes (e.g. a new `WorkflowTaskKind` member).
- **R10**: `docs/ERRATA.md` checked for any prior claim that defended_trial
  already works on v6; none found in the tail read at session start
  (through E24) — reconfirmed at delivery.
- **R11/R12**: gate discipline and delivery mechanics, not code — enforced
  by the workflow phases themselves.

## 6. Assumptions (recorded, not asked — resolved from the record)

- **A1.** Rubric trial (`run_trial`) and pairwise discrimination
  (`pairwise_discriminate`) are out of scope: they are already safely
  deferred under v6 by `Scheduler._defer_untransactional_v6_phase`, so
  there is no live defect there to fix, and REQUEST.md's own compile-gate
  name (`V6_DEFENDED_TRIAL_TRANSACTION_CONTRACT_REQUIRED`) keys off
  `criticism_policy.authority`, which only reaches the argument-trial path.
  Resolved from the record (§1), not asked — the record is dispositive and
  the dominance test (`dr-ask-the-right-question`) kills this fork: wiring
  them would be strictly more work for zero additional coverage of the
  named gate.
- **A2.** `defender` is always seat 0 (single-seat role) — confirmed: every
  existing call site (`adapter.call("defender", ...)`) omits
  `endpoint_index`, defaulting to 0, and no code anywhere selects a
  non-zero defender seat.
- **A3.** The new `WorkflowTaskKind.DEFENDED_TRIAL_STEP` member needs no
  entry in `workflow/nonconjecture_recovery.py::_RECOVERABLE_TASKS` — an
  interrupted trial-step work item (issued but unanswered, or unissued) is
  closed by the existing generic `InquiryTransactionService.
  recover_incomplete` sweep as an `abandoned` terminal (the same path
  every non-recoverable-by-name task kind already takes); resuming a
  *specific* in-flight defender/judge exchange is not attempted, consistent
  with §2's "no provider boundary" constraint — an abandoned trial step
  simply means that trial attempt did not complete, and the case remains
  open for the next live cycle. This is deliberately weaker than "resume
  the exact interrupted call," which is architecturally unavailable here
  the same way it is for rubric/pairwise's not-yet-transactional calls.

## 7. Diff budget

**Revised at execution** (Rung S5's own trap: an estimate is not the
ceiling, the measured diff is). Original estimate: 550 lines. Actual,
measured by `python tools/diff_budget.py HEAD`: **900 insertions, 104
deletions** across 11 files. `EXCEEDED` against the original ceiling —
recorded here rather than silently absorbed, per the diff-budget gate's
own purpose.

What the estimate missed, discovered only by executing R1 and running the
gate (not visible from reading the call sites alone):

- `run_manifest.py`'s `_route_seat_behavioral_contract_assignments`
  granting defender/judge/variator contracts turned out to require a
  correct PER-SEAT profile resolution
  (`resolve_route_seat_base_profile`), not the manifest-wide default — a
  seat-level correctness requirement invisible until
  `test_cli_production_doctor_v6.py`'s fixtures (which vary route
  profiles per seat) exposed it.
- The SAME grant surfaced a second, independent closed surface the
  original census did not name: `cli/doctor.py::ProductionContractPairV1.
  contract_id`, a closed `Literal` enumerating every contract the
  offline qualification battery knows how to probe. Widening it (additive
  only) plus writing the three new probe-pack branches
  (`_production_probe_contract`'s dispatch table) is ~54 lines by itself.
- Six existing tests across `test_v6_contract_schema_repair_policy.py`
  and `test_cli_production_doctor_v6.py` pin the EXACT enumerated
  contract set/count a v6 manifest compiles to (`CORE_CONTRACTS` tuples,
  `pair_count`/`case_count` assertions) — additive-by-design fixtures
  that still needed their literal expected values updated to include the
  three new contracts, exactly the kind of update CLAUDE.md's
  frozen-surfaces Traps section pre-authorizes ("a fixture that depended
  on defective behaviour may be minimally updated only when the fix's
  design doc predicted the update in advance" — predicted here, in this
  revision, before the commit that makes it).
- The double-recording bug found only by RUNNING the new offline
  regression (R5) — a v6-dispatched call is already durably recorded on
  its own transaction event, so the trial's legacy "sweep into a
  trial-llm Measure" bookkeeping had to become conditional at three call
  sites (defender, judge ensemble, variator) plus the final critic-artifact
  registration — added real lines (and real correctness) the design's
  prose in §3 did not itemize.
- `test_v6_manifest_defended_trial.py`'s two tests needed a full rewrite
  (asserting successful compilation instead of refusal) once R3 landed.

No line here is scope creep against REQUEST.md's numbered requirements —
every insertion traces to R1, R2, R3, R5, or the fixture-currency
consequence of one of them. The number is reported honestly rather than
re-baselined to make EXCEEDED disappear; DELIVERY.md's PROOF carries the
same figure.
