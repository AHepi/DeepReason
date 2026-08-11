<!-- DR-SUB-workflow -->
Verified-at: 7347d8fe
Verify: python -m pytest tests/test_workflow_reducer_c0.py tests/test_workflow_models_c0.py tests/test_workflow_control_replay_c1.py tests/test_workflow_stop_lifecycle_c4.py tests/test_workflow_resume_lifecycle_c4.py tests/test_workflow_repair_authority_c4.py tests/test_v6_controller3_replay_verification.py -q
Owns: src/deepreason/workflow/
Seams: DR-SEAM-harness-x-workflow, DR-SEAM-llm-x-workflow, DR-SEAM-rules-x-workflow, DR-SEAM-scheduler-x-workflow, DR-SEAM-scratch-x-workflow
Seams-undocumented: application x workflow, bridge x workflow, capabilities x workflow, manifest x workflow, ontology x workflow, packs-and-token-economy x workflow, schools x workflow, verification x workflow

# The workflow control plane — process authority for every model call

## Seams

Note: this package is `src/deepreason/workflow/` (singular, the v6
transactional control plane). `DR-SUB-application` separately `Owns:`
`src/deepreason/workflows/` (plural, the retired website state machine) —
a different directory the near-identical name invites confusing with this
one. An earlier draft of `application x workflow` on the other document
made exactly that mistake and was corrected before commit.

| Side | Status | What the agreement is (one line) |
|---|---|---|
| `DR-SEAM-harness-x-workflow` | documented | the workflow layer owns process authority and holds none of it: every decision becomes durable only as one `Rule.CONTROL` event appended BY the harness |
| `DR-SEAM-llm-x-workflow` | documented | `workflow/` decides by what recorded authority a provider may be spoken to; `llm/` is the only place that speaks to one |
| `DR-SEAM-rules-x-workflow` | documented | `rules/` decides what may be proposed and attacked; `workflow/` decides by what recorded authority a provider may be asked |
| `DR-SEAM-scheduler-x-workflow` | documented | the scheduler decides what and when; the workflow plane decides by what recorded authority any of it may touch a provider |
| `DR-SEAM-scratch-x-workflow` | documented | a scratch note is never authority: every mutation is its own log entry, invisible to this plane's admission chain |
| schools x workflow | undocumented | real: `DR-CON-schools`'s own Where-it-lives table names `workflow/criticism.py` (`plan_foreign_criticism`, `CriticismAssignmentV1`, `CoverageDebtV1`) and `workflow/profiles.py` (`resolve_conjecture_route`) directly |
| application x workflow | undocumented | likely real, corrected on the other side: `DR-SUB-application`'s `runtime.terminal_authority` plausibly consumes the typed terminal this package authors — exact call site not confirmed here either |
| manifest x workflow | undocumented | plausible: v6 dispatch guards and `control_plane_policy` are manifest fields read widely by transactional code, exact import direction not confirmed here |
| bridge x workflow | undocumented | not evidenced here either way — candidate pair, not yet analyzed (consistent with `DR-SUB-bridge`'s own Seams table) |
| capabilities x workflow | undocumented | not evidenced here either way — candidate pair, not yet analyzed |
| ontology x workflow | undocumented | not evidenced here either way — candidate pair, not yet analyzed |
| packs-and-token-economy x workflow | undocumented | not evidenced here either way — candidate pair, not yet analyzed |
| verification x workflow | undocumented | not evidenced here either way — candidate pair, not yet analyzed |

## What it is

`workflow/` answers one question for every provider call the system makes:
by what recorded authority was this call allowed, and what is the durable
consequence of its result. It owns no semantics — it never reads a conjecture,
scores a criticism or moves a status — but nothing reaches a provider without
first passing through a preparation, a token reservation, a context exposure
receipt and a dispatch authorization it authored, and no result becomes an
effect without a typed admission or terminal it authored. Because that chain is
append-only and reference-only, a crashed run can be resumed from the record
alone: the recovery modules re-derive an admission from the raw blob a
`ProviderAttemptV1` already names, with the provider boundary deliberately
absent. Three controller generations coexist — v1 (shadow and active
conjecture), v2 (inquiry), v3 (the transactional v6 runtime) — because roots
written under any of them must stay replay-valid forever. The package writes no
file of its own; every record lands in the harness object store and every
transition is one `Rule.CONTROL` event in the same log as the formal graph.
`check: test "$(grep -rlE 'path\.open|write_text|write_bytes|[^_a-z]open\(' --include=*.py src/deepreason/workflow | wc -l)" -eq 0 && for s in workflow-work-order workflow-transition-decision workflow-work-preparation-v1 workflow-provider-attempt-v1 workflow-semantic-admission-v1 workflow-work-terminal-v1 workflow-work-lifecycle-transition-v1 workflow-run-terminal-commitment-v1 criticism-coverage-debt-v1; do grep -q "\"$s\":" src/deepreason/storage/objects.py || exit 1; done && ! grep -qE "llm\.(endpoints|providers|adapter)" src/deepreason/workflow/conjecture_recovery.py src/deepreason/workflow/nonconjecture_recovery.py src/deepreason/workflow/atomic_recovery.py`

A run's whole control-plane authority is one compiled profile. Exactly four
profile ids exist, and each pins an exact 4-tuple of controller version,
capability profile, conjecturer contract and control-event schema; a manifest
naming an inconsistent combination fails to compile rather than running in a
half-supported mode. The authority enums (`WorkflowTaskKind`,
`CapabilityOutcome`, `TransitionKind`, `WorkItemStatus`, `GuardFindingCode`)
are closed, so an unrecognised value is a load error, not a default.
`check: for p in conjecture.shadow.v1 conjecture.active.v1 inquiry.active.v1 inquiry.active.v2; do grep -q "\"$p\": (" src/deepreason/workflow/profiles.py || exit 1; done && grep -q "workflow profile authority tuple is inconsistent" src/deepreason/workflow/profiles.py && python -m pytest tests/test_workflow_models_c0.py -q -k authority_enums`

## Entry points

- `profiles.compile_workflow_profile` — turn an immutable manifest into the one
  executable `ConjectureWorkflowProfileV1`; raises `WorkflowProfileError` with a
  typed code rather than guessing. `ConjectureWorkflowProfileV1.capability_grant`
  derives what one turn may do; `resolve_conjecture_route` and
  `route_lease_reference` project a runtime lease into secret-free authority.
- `transaction_service.InquiryTransactionService` — the controller-v3 runtime,
  and the only path to a provider under RunManifest v6: `prepare` →
  `context_plan` → `reserve_dispatch` → `finalize_dispatch` (`issue` does both)
  → `record_provider_attempt` → `record_semantic_admission` → `terminate`.
  `repair_schema_failure` runs a separately authorized repair transaction;
  `recover_incomplete` lists attempts a crash left unsettled.
- `reducer.plan_conjecture_work` / `plan_conjecture_batch` / `reduce_conjecture`
  — the pure C0 slice: given a profile, a process state and typed signals,
  produce the next `TransitionDecisionV1`. No I/O, no provider, no harness.
- `state.state_after_transition` / `apply_decision` — the state machine those
  decisions move, over `WorkflowProcessStateV1` and `ConjectureWorkStateV1`.
- `replay.replay_workflow` and `WorkflowReplayState` — rebuild all process
  authority from events plus objects. `bind_run_manifest` supplies v6 route-seat
  authority, `observe_event` tracks calls, `validate` checks without mutating,
  `apply` commits, `recovery_status` reports where a work order was interrupted,
  and `digest` is the value the checkpoint seals.
- `lifecycle.outstanding_work_snapshot` / `build_stopped_lifecycle` /
  `build_resumed_lifecycle` — pure construction of the typed STOPPED and RESUMED
  terminal authority, each refusing to forget unfinished work.
- `trace.ConjectureControlTrace` — the live C1 persistence bracket around one
  work order: `authorize_dispatch`, `record_provider_result`, `record_guard`,
  `record_repair_request`, `follow_up`, `capability_follow_up`, `finish`,
  `abandon`, `seal`. `require_authority` is what makes later failures fail closed.
- `shadow.ConjectureShadowObserver.begin_conjecture` / `finish_conjecture` —
  plan the same work the legacy scheduler is doing and record a
  `ShadowComparisonV1`, without ever changing what actually happens.
- `conjecture_recovery.recover_conjecture_admission`,
  `nonconjecture_recovery.recover_nonconjecture_admission`,
  `atomic_recovery.recover_atomic_child_output`,
  `repair_transaction.repair_schema_failure` — resume a durable result.
- `criticism.plan_foreign_criticism` / `compile_criticism_assignments` /
  `record_completed_criticism_attempt` — deterministic foreign-school criticism
  planning and its `CoverageDebtV1` terminal record.
- `context_continuation.ConjectureContextContinuationV1.create` — bind a model's
  context request to either a child work preparation or a typed, unissued denial.
`check: for s in prepare context_plan reserve_dispatch finalize_dispatch issue record_provider_attempt record_semantic_admission terminate repair_schema_failure recover_incomplete; do grep -q "    def $s(" src/deepreason/workflow/transaction_service.py || exit 1; done; for s in plan_conjecture_work plan_conjecture_batch reduce_conjecture; do grep -q "^def $s(" src/deepreason/workflow/reducer.py || exit 1; done; for s in state_after_transition apply_decision; do grep -q "^def $s(" src/deepreason/workflow/state.py || exit 1; done; for s in outstanding_work_snapshot build_stopped_lifecycle build_resumed_lifecycle; do grep -q "^def $s(" src/deepreason/workflow/lifecycle.py || exit 1; done; for s in compile_workflow_profile resolve_conjecture_route route_lease_reference; do grep -q "^def $s(" src/deepreason/workflow/profiles.py || exit 1; done; grep -q "^def replay_workflow(" src/deepreason/workflow/replay.py || exit 1; for s in observe_event apply validate digest recovery_status bind_run_manifest; do grep -q "    def $s(" src/deepreason/workflow/replay.py || exit 1; done; grep -q "^def recover_conjecture_admission(" src/deepreason/workflow/conjecture_recovery.py && grep -q "^def recover_nonconjecture_admission(" src/deepreason/workflow/nonconjecture_recovery.py && grep -q "^def recover_atomic_child_output(" src/deepreason/workflow/atomic_recovery.py && grep -q "^def repair_schema_failure(" src/deepreason/workflow/repair_transaction.py || exit 1; for s in authorize_dispatch require_authority record_provider_result record_guard record_repair_request follow_up capability_follow_up finish abandon seal; do grep -q "    def $s(" src/deepreason/workflow/trace.py || exit 1; done; for s in begin_conjecture finish_conjecture; do grep -q "    def $s(" src/deepreason/workflow/shadow.py || exit 1; done; for s in plan_foreign_criticism compile_criticism_assignments record_completed_criticism_attempt; do grep -q "^def $s(" src/deepreason/workflow/criticism.py || exit 1; done; grep -q "    def create(" src/deepreason/workflow/context_continuation.py`

## State it owns

Nothing on disk of its own. Durable records go into the harness object store
under 26 `workflow-*` schemas and 3 `criticism-*` schemas, and every transition
is one `Rule.CONTROL` event whose payload (`control.event.v1/v2/v3`) carries
references only — the records themselves are resolved from the store on replay.
The event and the payload must appear together, the decision reference must be
the event's final output, and exactly one control action, v3 `provider_result`,
may carry an `LLMCall`; every other control action carrying one is a load error.
`check: test "$(grep -c '"workflow-[a-z0-9-]*":' src/deepreason/storage/objects.py)" -eq 26 && test "$(grep -c '"criticism-[a-z0-9-]*":' src/deepreason/storage/objects.py)" -eq 3 && grep -q "self.workflow_state = WorkflowReplayState()" src/deepreason/harness.py && grep -q 'if (self.rule == Rule.CONTROL) != (self.control is not None):' src/deepreason/ontology/event.py && grep -q "control decision_ref must be the final event output" src/deepreason/control_events.py && grep -q 'and self.control.action == "provider_result"' src/deepreason/ontology/event.py && grep -q "control decisions cannot contain an LLM call" src/deepreason/ontology/event.py`

The in-memory materialization is `WorkflowReplayState`, held as
`harness.workflow_state`: per-branch process state, work orders, proposal and
guard receipts, transition decisions, per-work transaction items (preparations,
reservations, exposures, provider attempts, admissions, terminals), compact-
recovery and insufficient-capability records keyed by route seat, contract
decompositions, the model-classification binding, and the terminal-commitment
ledger by epoch. `WorkflowReplayState.digest` is the single value the harness
seals into `workflow-checkpoint.json` for tail-loss detection — the file is the
harness's, its content is this package's. Two replays of one root must produce
an equal digest; `verify_root` checks exactly that, plus call pairing
(`DR-SUB-verification`).
`check: grep -q '"process_digest": self.workflow_state.digest,' src/deepreason/harness.py && grep -q "    def write_workflow_checkpoint(" src/deepreason/harness.py && grep -q "if second.workflow_state.digest != h.workflow_state.digest:" src/deepreason/invariants.py && grep -q 'fail("workflow-replay"' src/deepreason/invariants.py && python -m pytest tests/test_workflow_control_replay_c1.py::test_checkpoint_detects_deleted_final_authority_event -q`

The dependency arrow is one-way where it matters: `reducer.py` and `state.py`
reach no provider, no harness and no scheduler, and `replay.py` never runs a
model or the reducer — it materializes only what the records already say.
`check: ! grep -qE "^\s*(from|import)\s+.*\b(llm|harness|scheduler)\b" src/deepreason/workflow/reducer.py src/deepreason/workflow/state.py && grep -q "never run a model or reducer" src/deepreason/workflow/replay.py && ! grep -q "from deepreason.workflow.reducer import" src/deepreason/workflow/replay.py && python -m pytest tests/test_workflow_control_replay_c1.py::test_reopen_replays_workflow_without_reducer_or_model -q`

## Where to change what

| To change... | Edit | Test |
|---|---|---|
| Which capabilities a turn may exercise (candidates, context request, simulation, research, abstention) | `CapabilityOutcome` in `workflow/models.py` and `ConjectureWorkflowProfileV1.capability_grant` in `workflow/profiles.py`. `CONTROLLED_TURN_CONTRACTS` (P-CEPP-1) is the set of "real active-conjecture" contracts (v4/v5/v6/v7) checked here and in `_owned_tuple`'s `"inquiry.active.v2"` membership — v7 (D2 rev 2 dual-mode) grants the identical capability set v6 does, imported from `run_manifest.py`'s own `CONJECTURER_TURN_CONTRACTS` for the `inquiry.active.v2` slot specifically | `tests/test_workflow_reducer_c0.py::test_candidate_payload_requires_candidate_proposal_capability`, `tests/test_v6_transaction_qualification.py::test_v7_manifest_compiles_a_workflow_profile_naming_v7` |
| How many local schema repairs a seat gets, and their scopes | `compile_workflow_profile` in `workflow/profiles.py` — `min(2, RETRY_MAX)` and the `("whole_object", "smallest_subtree")` slice | `tests/test_workflow_reducer_c0.py::test_zero_local_repair_grant_refuses_authorization_and_repaired_receipt` |
| Which stop reasons may be resumed, or composed from | `RESUMABLE_STOP_REASONS` in `workflow/lifecycle.py` | `tests/test_bridge_after_typed_stop.py::test_composition_after_a_non_resumable_stop_stays_forbidden` |
| Add a new kind of provider work (a new role/seat) | `WorkflowTaskKind` in `workflow/models.py`, a contract branch in `workflow/nonconjecture_recovery.py`, and `_RECOVERABLE_TASKS` | `tests/test_v6_nonconjecture_recovery.py::test_invalid_stored_critic_output_terminalizes_without_scheduler_dispatch` |
| Add a durable transaction record | a class in `workflow/transaction.py`, a schema row in `storage/objects.py`, an `apply` branch in `workflow/replay.py`, an `action` literal in `control_events.py` | `tests/test_v6_controller3_replay_verification.py::test_canonical_controller_v3_history_has_zero_replay_violations` |
| What replay refuses in a controller-v3 history | `_apply_transaction` / `_validate_work_decision` / `_plan` in `workflow/replay.py` | `tests/test_v6_controller3_replay_verification.py::test_provider_result_without_authorized_attempt_fails_closed` |
| What a crashed run may resume from a stored blob | `recover_conjecture_admission`, `recover_nonconjecture_admission` | `tests/test_v6_nonconjecture_recovery.py::test_recovered_criticism_applies_canonical_effect_exactly_once` |
| Whether a model's context request is granted | `ConjectureContextContinuationV1.evaluate` in `workflow/context_continuation.py` | `tests/test_v6_context_continuation.py::test_unpermitted_channel_is_typed_denied_without_child_dispatch` |
| Token reservation, and the typed budget-denied terminal | `reserve_dispatch` in `workflow/transaction_service.py` | `tests/test_v6_context_continuation.py::test_child_budget_denial_has_no_exposure_and_no_dispatch` |
| The typed STOPPED / RESUMED terminal records | `build_stopped_lifecycle` / `build_resumed_lifecycle` in `workflow/lifecycle.py` | `tests/test_workflow_stop_lifecycle_c4.py::test_terminal_builder_snapshots_then_refuses_unfinished_provider_work` |
| Foreign-school criticism selection, batching, coverage debt | `plan_foreign_criticism` and `CoverageDebtV1` in `workflow/criticism.py` | `tests/test_foreign_criticism_policy_c3.py::test_shared_models_count_school_coverage_without_claiming_route_diversity` |
| What the shadow observer compares and reports | `ShadowComparisonV1` and `ConjectureShadowObserver.finish_conjecture` in `workflow/shadow.py` | `tests/test_workflow_shadow_c0.py::test_observer_failure_is_non_authoritative` |
| `WorkflowReplayState.digest` — adding state to it | `workflow/replay.py`; a frozen surface, see `DR-INV-frozen-surfaces` and the Traps entry below | `tests/test_workflow_control_replay_c1.py::test_control_trace_round_trips_every_prefix_with_empty_formal_diff` |
`check: python -m pytest tests/test_workflow_reducer_c0.py::test_candidate_payload_requires_candidate_proposal_capability tests/test_workflow_reducer_c0.py::test_zero_local_repair_grant_refuses_authorization_and_repaired_receipt tests/test_bridge_after_typed_stop.py::test_composition_after_a_non_resumable_stop_stays_forbidden tests/test_v6_nonconjecture_recovery.py::test_invalid_stored_critic_output_terminalizes_without_scheduler_dispatch tests/test_v6_controller3_replay_verification.py::test_canonical_controller_v3_history_has_zero_replay_violations tests/test_v6_controller3_replay_verification.py::test_provider_result_without_authorized_attempt_fails_closed tests/test_v6_nonconjecture_recovery.py::test_recovered_criticism_applies_canonical_effect_exactly_once tests/test_v6_context_continuation.py::test_unpermitted_channel_is_typed_denied_without_child_dispatch tests/test_v6_context_continuation.py::test_child_budget_denial_has_no_exposure_and_no_dispatch tests/test_workflow_stop_lifecycle_c4.py::test_terminal_builder_snapshots_then_refuses_unfinished_provider_work tests/test_foreign_criticism_policy_c3.py::test_shared_models_count_school_coverage_without_claiming_route_diversity tests/test_workflow_shadow_c0.py::test_observer_failure_is_non_authoritative tests/test_workflow_control_replay_c1.py::test_control_trace_round_trips_every_prefix_with_empty_formal_diff -q && grep -q "_RECOVERABLE_TASKS = frozenset(" src/deepreason/workflow/nonconjecture_recovery.py && ! grep -q "WorkflowTaskKind.CONJECTURE," src/deepreason/workflow/nonconjecture_recovery.py`

## Traps

- **A repaired atomic child is a DIFFERENT work item, and the merge must name
  it.** In jolt `run-b4d6dfda0c20676a864a051fbc97bda4`, decomposition merges
  containing a repaired child were reported non-replay-valid — two findings, at
  Conj seqs 245 and 386, recorded by the run about itself in
  `REPLAY_VALIDATION.json`. When an atomic child is rejected, the admitted
  candidate comes from a `repair.semantic-task.v1` work item whose decomposition
  authority is its `parent_work_id`; `replay.py` refuses a completion whose
  per-slot inventory differs, so the completion must name the repair. The merge
  exemption resolved each slot by work id and demanded a
  `contract-decomposition-child.v1` payload — it rejected the shape its own
  writer produces.
`check: python -m pytest tests/test_v6_engaged_repair_verification.py::test_merge_whose_child_was_repaired_verifies_clean tests/test_v6_engaged_repair_verification.py::test_the_repaired_child_slot_really_names_repair_work -q`
- **A budget denial is a budget signal, not a recovery failure.**
  `recover_atomic_child_output` raised `ValueError` for any non-completed child
  terminal, so in selfstudy `run-9175f0ec` a token-budget-denied atomic
  candidate child failed the whole run *after* the harness had already written
  its typed run-stop. A `budget_denied` child terminal now re-raises as
  `WorkBudgetDenied` so the ordinary typed-stop path owns it; every other failed
  terminal is still a hard recovery error. Any new terminal status added here
  needs the same judgement call made explicitly.
`check: grep -q "raise WorkBudgetDenied(selected.terminal)" src/deepreason/workflow/atomic_recovery.py && grep -q 'raise ValueError("atomic child is terminally failed")' src/deepreason/workflow/atomic_recovery.py`
- **Making stops typed made every budget-bounded run uncomposable.** On the GLM
  comparison ladder, typed `budget_exhausted` STOPPED decisions caused the
  replay guard to reject the bridge's Stage-A provider call as work-bound after
  terminal (`BRIDGE_STAGE_A_FAILED`); the campaign's bridges had only ever
  succeeded on the bare stops that typed stops replaced. `_post_terminal_
  composition_call` now admits exactly the calls whose preparation carries a
  `source_terminal_commitment_ref` under a resumable stop reason. Ordinary
  work-bound calls after a stop stay forbidden — continuing the reasoning still
  requires typed RESUMED authority — and so does composition after a
  non-resumable stop.
`check: grep -q 'RESUMABLE_STOP_REASONS = frozenset({"converged", "budget_exhausted"})' src/deepreason/workflow/lifecycle.py && python -m pytest tests/test_bridge_after_typed_stop.py::test_terminal_bound_composition_call_survives_a_resumable_stop tests/test_bridge_after_typed_stop.py::test_ordinary_work_after_a_typed_stop_stays_forbidden tests/test_bridge_after_typed_stop.py::test_composition_after_a_non_resumable_stop_stays_forbidden -q`
- **A census over committed roots cannot tell you what the TESTS cover.**
  `RESUMABLE_STOP_REASONS` is enforced twice — `lifecycle.py:273` while
  BUILDING a resume decision (surfaced by `prepare_continuation` as
  `CONTINUE_NOT_AUTHORIZED`) and `replay.py:2251` while APPLYING the
  RESUMED transition (`WellFormednessError`, which IS a `ValueError`
  subclass, so `pytest.raises(ValueError)` alone cannot tell them
  apart — match the message). Tranche
  `2026-08-05-fix-resumable-reason-guard-coverage` opened to add a
  missing test for the first and found one already there:
  `test_completed_typed_terminal_is_not_continuation_authority`, in the
  very file this document's `Verify:` line runs. The false premise came
  from a true census — no committed root carries a receipt whose reason
  is non-resumable, since all 16 stopped on `budget_exhausted` — read as
  "therefore nothing tests it". A CONSTRUCTED test needs no committed
  root. Grep the wrapped error code, not the guard's message: the
  message string appears nowhere in `tests/`.
  The subject is not exotic — `StopController` emits
  `completed`/`converged`/`stuck` and the scheduler writes all three
  into a typed receipt, so the guard's commonest real subject is a run
  that FINISHED.
`check: python -m pytest tests/test_workflow_resume_lifecycle_c4.py::test_completed_typed_terminal_is_not_continuation_authority -q && grep -q 'raise ValueError("terminal stop reason does not authorize RESUMED")' src/deepreason/workflow/replay.py && ! grep -rq "does not authorize continuation" tests/`
- **The replay digest is append-only in a subtler sense than the log is.**
  Transaction, compact-recovery, insufficient-capability, decomposition and
  classification sections appear in `WorkflowReplayState.digest` only when
  non-empty, precisely so that a root written before those features existed
  digests to the same value it always did. Adding an unconditional key — even
  an empty default — silently invalidates every historical replay-valid root,
  which `DR-INV-frozen-surfaces` rules out by definition.
`check: grep -q "Preserve the exact v1/v2 replay digest for every historical root" src/deepreason/workflow/replay.py && grep -q "if self.transaction_work:" src/deepreason/workflow/replay.py && python -m pytest tests/test_workflow_stop_lifecycle_c4.py::test_v1_to_v3_stop_path_does_not_emit_new_control_bytes -q`
- **A pre-built nested pydantic instance skips its parent's validators.**
  Both the reducer and the state machine re-parse whole model trees through
  `_canonical_revalidate` before trusting them, because passing an already
  constructed `WorkOrderEnvelopeV1` into a decision would otherwise carry a
  forged identity straight past the guards that recompute it. Any new code path
  that accepts a caller-supplied authority record needs the same reparse.
`check: grep -q "cannot skip validation" src/deepreason/workflow/state.py && grep -q "cannot bypass guards" src/deepreason/workflow/reducer.py && python -m pytest tests/test_workflow_reducer_c0.py::test_reducer_revalidates_forged_nested_work_order_identity -q`
- **Observation must never change the observed run — until it is authoritative.**
  `ConjectureControlTrace` swallows its own persistence errors through
  `_report`, including a failing diagnostic sink, so a shadow trace cannot alter
  actuation. `require_authority` flips exactly that behaviour: after it, any
  failure raises `WorkflowAuthorizationError` and the active conjecture stops
  before an unbound dispatch. Getting this backwards either makes shadow mode
  able to kill a run, or makes active mode dispatch without durable authority.
`check: grep -q "diagnostics never affect actuation" src/deepreason/workflow/trace.py && python -m pytest tests/test_workflow_shadow_c0.py::test_observer_failure_is_non_authoritative tests/test_workflow_shadow_c0.py::test_active_trace_failure_is_terminal_while_shadow_remains_advisory -q`
- **Repair capacity is reserved before the provider answers, never after.**
  `authorize_dispatch` multiplies the first attempt's conservative bound by
  `max_local_repairs + 1` at issue time, so settlement cannot invent repair
  capacity once a response exists. The visible consequence is that a run which
  hits its token budget mid-retry must be reported as a budget stop, not as
  repair exhaustion — the two have completely different meanings for the record.
`check: grep -q "settlement never invents repair capacity after the" src/deepreason/workflow/trace.py && grep -qF "reserved_tokens *= (" src/deepreason/workflow/trace.py && grep -qF "capability_grant.max_local_repairs + 1" src/deepreason/workflow/trace.py && python -m pytest tests/test_workflow_shadow_c0.py::test_mid_retry_budget_stop_is_not_reported_as_repair_exhaustion -q`
- **Criticism coverage counts schools, never endpoints or models.** Two schools
  sharing one model still count as two critics, and one school reached through
  two endpoints still counts as one. `plan_foreign_criticism` rotates across the
  canonical target order for deterministic spreading, so input order is
  irrelevant; a planner change that starts counting routes would silently
  weaken the manifest's coverage requirement while still reporting it satisfied.
`check: grep -q "is always counted by critic school" src/deepreason/workflow/criticism.py && python -m pytest tests/test_foreign_criticism_policy_c3.py::test_shared_models_count_school_coverage_without_claiming_route_diversity -q`
- **Crash-recovery re-checking "admitted" work must not assume every
  CRITICISM item is batch-shaped.** `Scheduler._recover_workflow_
  prefixes` re-sweeps every admitted `CRITICISM`/`SCRATCH_AUTHORING`
  item to close a crash window between admission and the caller-owned
  effect, and dispatches anything not `CONJECTURE` to
  `recover_nonconjecture_admission`. An atomic child of a criticism
  decomposition (`rules/crit.py`'s `execute_atomic_transition`,
  payload schema `"contract-decomposition-child.v1"`) is still
  `task_kind == CRITICISM`, so it reached
  `_criticism_contract` — a handler built only for the BATCH shape
  (`"criticism.semantic-task.v1"`) — and crashed
  `NonConjectureRecoveryAuthorityError("unknown critic task")` on
  `deepreason continue`, even when the child was already fully
  resolved (Rung L1, 2026-08-08: S6 `PARKED.md` P3, reproduced against
  fixture `experiments/2026-08-08-live-two-seat-ab-s6/home-s6/runs/
  failed-epoch1-run-8c77c6588485304d1f73416318c62949`; connected
  failure D1 `PARKED.md` P2, `tests/test_continuation.py::
  test_a_stop_with_no_typed_receipt_refuses_continuation`). Fixed:
  `recover_nonconjecture_admission` now recognizes the atomic-child
  payload shape before ever reaching `_criticism_contract` — an
  already-terminal child is a no-op (nothing to recover), a
  still-open one refuses with one consistent typed reason. Any new
  atomic-decomposed task family needs the same recognition before its
  own batch-shaped recovery handler, not after.
`check: grep -q 'contract-decomposition-child.v1"' src/deepreason/workflow/nonconjecture_recovery.py && grep -q "atomic criticism decomposition child recovery is not" src/deepreason/workflow/nonconjecture_recovery.py && python -m pytest tests/test_l1_continue_resumable_crash.py -q`
- **`_criticism_contract` recovers a school-optional payload, and the
  two shapes recover through genuinely disjoint logic
  (adjudication-judge-seats-optins tranche, S13e, 2026-08-10).** When
  `payload["critic_school_id"]` is `None` (the legacy/school-free
  dispatch S13i's self-detection produces), recovery skips the
  `criticism_policy`/binding-lookup requirement entirely — there is
  none to recover against — verifies the route belongs to the
  manifest's `argumentative_critic` seats instead of a school binding,
  and reads authority from the frozen `payload["dispatch_authority"]`
  field rather than `criticism_policy.authority` (never a live or
  manifest-reconstructed `Config`: `ARGUMENTATIVE_AUTHORITY` is never
  written to the manifest, so reconstruction would silently report the
  bare default and mask a real override — the same "freeze at mint
  time" principle `critic_school_id` itself already followed). The
  per-target `CriticismAssignmentV1` obligation and its cardinality
  check ALSO do not apply to the school-free shape — that record's own
  `critic_school_id` field is a required, pattern-constrained `str`, so
  the whole obligation concept is inherently school-specific, and the
  self-sufficient dispatch always passes zero assignment refs. A new
  provider work family that ever needs a THIRD partial-envelope shape
  must gate on its own discriminator the same explicit way, not assume
  "school missing" is the only alternative to "school present."
`check: python -c "import inspect; from deepreason.workflow.nonconjecture_recovery import _criticism_contract as C; s = inspect.getsource(C); assert 'if school_id is None:' in s and 'dispatch_authority' in s and 'manifest does not authorize criticism' in s" && python -m pytest tests/test_v6_nonconjecture_recovery.py::test_criticism_contract_recovers_without_a_school tests/test_v6_nonconjecture_recovery.py::test_criticism_contract_refuses_recovery_without_a_school_when_dispatch_authority_is_not_observe_only -q`
