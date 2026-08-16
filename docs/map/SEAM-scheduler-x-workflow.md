<!-- DR-SEAM-scheduler-x-workflow -->
Verified-at: 546544b5
Verify: python tools/docs_verify.py
Owns: src/deepreason/scheduler/scheduler.py, src/deepreason/workflow/lifecycle.py, src/deepreason/workflow/shadow.py, src/deepreason/workflow/trace.py, src/deepreason/workflow/criticism.py
Sides: DR-SUB-scheduler, DR-SUB-workflow

# scheduler x workflow

## The agreement

The scheduler decides *what* is worked on and *when*; the workflow plane decides
*by what recorded authority* any of it may touch a provider. Neither reaches
into the other's decision: the scheduler owns attention and owns no transaction,
and the workflow plane owns process authority and owns no cycle. Under
RunManifest v6 the scheduler promises that no cycle begins while a
crash-interrupted work order is open, that a legacy model phase with no
transaction contract is recorded as typed completion debt rather than dispatched
unbound, that every foreign-criticism obligation is durable before its route
lease is even resolved, and that the run's terminal receipt is built from the
whole replayed process state rather than from anything the scheduler remembers.
The workflow plane promises in return that `outstanding_work_order_ids` is the
complete inventory of unfinished authority, that `recover_incomplete` closes
everything that cannot be finished and returns only results still needing
deterministic re-validation, that issued work is never re-dispatched, and that a
STOPPED receipt is refused outright while any work remains open. The bracket
around a provider call belongs to the *rule* that makes it — `conj`, `crit`,
`scratch/authoring`, `referee` — never to the scheduler; what the scheduler
supplies is the `run_manifest=` argument that decides whether a transaction is
opened at all. The generational split is the thing to hold onto: under
controller-v1/v2 the scheduler itself carries the durable bracket
(`ConjectureControlTrace`), under controller-v3 it carries none and verifies the
transaction after the fact.

Fourteen modules under `src/` name `deepreason.workflow` and mention the
scheduler. The count is a coincidence census, not a coupling measure, and it
moved from thirteen on 2026-08-16 for a reason worth stating so the next
reader does not hunt for new coupling: `application/results.py` already
imported `workflow.lifecycle` for `RESUMABLE_STOP_REASONS`, and the embedder
tranche added a DOCSTRING there naming the scheduler as the producer of the
`embedder` Measure events its reader consumes. Prose, not an import — the
load-bearing clauses of this check (which module owns the criticism planners,
and that `workflow/` never imports `scheduler`) are unchanged. Five files
carry the agreement — and one of them,
`workflow/criticism.py`, never names the scheduler at all, so a grep-shaped
search for this seam misses the module whose planners nothing but the scheduler
calls.
`check: test "$(for f in $(grep -rl "deepreason\.workflow" --include=*.py src/deepreason); do grep -qlE "scheduler" "$f" && echo x; done | wc -l)" -eq 14 && test "$(grep -rlE "plan_foreign_criticism|compile_criticism_assignments" --include=*.py src/deepreason | grep -v "workflow/criticism.py")" = "src/deepreason/scheduler/scheduler.py" && ! grep -rq "deepreason\.scheduler" --include=*.py src/deepreason/workflow/ && test "$(grep -c "deepreason\.workflow" src/deepreason/scheduler/scheduler.py)" -eq 16 && test "$(grep -cE "^from deepreason\.workflow" src/deepreason/scheduler/scheduler.py)" -eq 2 && grep -q "^def plan_foreign_criticism(" src/deepreason/workflow/criticism.py && ! grep -q "scheduler" src/deepreason/workflow/criticism.py && grep -q "plan_foreign_criticism(manifest" src/deepreason/scheduler/scheduler.py`

## Where it is expressed

| Site | File | Symbol | What it enforces |
|---|---|---|---|
| Construction guard | `scheduler/scheduler.py` | `Scheduler.__init__`, first branch | a v6 manifest with an adapter that lacks `transaction_authority_required` raises before any state is read |
| Authority binding | `scheduler/scheduler.py` | `adapter.bind_v6_authority(harness, run_manifest)` | one adapter, one harness, one manifest — fixed at construction, not per call |
| Dispatch gate | `scheduler/scheduler.py` | the `run_manifest=` argument of `conj(...)` | whether the rule opens a transaction at all; `None` for any non-active mode |
| Preparation ordering | `scheduler/scheduler.py` | `context_plan = None` under v6 | controller-v3 appends preparation before its pure planners, so the scheduler must not pre-plan context |
| Transaction bracket | `rules/conj.py`, `rules/crit.py`, `scratch/authoring.py`, `referee.py` | `InquiryTransactionService(...)` | the rule that makes the call opens and settles it |
| Recovery entry | `scheduler/scheduler.py` | `run` → `_recover_workflow_prefixes` (latched by `_workflow_recovery_done`) | no cycle starts over an open work order; leftover authority raises |
| Recovery engine | `workflow/transaction_service.py` | `recover_incomplete` | unissued → `abandoned`; issued-unanswered → `abandoned`; unadmitted result → returned for validation |
| Recovery routing | `scheduler/scheduler.py` | task-kind branch → `recover_conjecture_admission` / `recover_nonconjecture_admission` | the conjecture seat needs the embedder; every other seat must not get one |
| Effect re-window | `scheduler/scheduler.py` | `admitted_effect_candidates` | CRITICISM / SCRATCH_AUTHORING work whose admission landed but whose caller-owned effect may not have |
| Legacy recovery | `scheduler/scheduler.py` | `reduce_conjecture(WORK_ABANDONED)` + `record_control_transition` | v4/v5 outstanding orders close through the pure reducer, against their own manifest |
| Deferral | `scheduler/scheduler.py` | `_defer_untransactional_v6_phase` | a legacy model phase becomes `v6-model-phase-deferred.v1` debt instead of an unbound dispatch |
| Obligation before dispatch | `scheduler/scheduler.py` | `record_criticism_obligation(assignment)` | every assignment is durable before the batch's route lease resolves |
| Coverage terminal | `workflow/criticism.py` | `record_completed_criticism_attempt`, `CoverageDebtV1` | per-target receipts and typed debt, counted by critic school |
| Pre-v6 bracket | `scheduler/scheduler.py`, `workflow/trace.py` | `_workflow_control_trace`, `ConjectureControlTrace.abandon/finalize/seal` | WORK_ENABLED + WORK_ISSUED before the provider; abandon on every fail-closed exit |
| Shadow channel | `scheduler/scheduler.py`, `workflow/shadow.py` | `_begin_workflow_shadow` / `_finish_workflow_shadow` | observation is non-authoritative in shadow, terminal in active mode |
| Follow-up assertion | `scheduler/scheduler.py` | `before_work` / `new_work_ids` diff in `_v6_simulation_result_follow_up` | exactly one fresh bound transaction per consumed simulation package |
| Stop terminal | `scheduler/scheduler.py`, `workflow/lifecycle.py` | `_record_stop` → `build_stopped_lifecycle` | the receipt replays the controller exactly and refuses unfinished authority |
| Resume consumption | `scheduler/scheduler.py` | `_rehydrate_resumed_stop_controller` | the stop window comes from `current_resume_decision`, not from the constructor |
| Terminal fence | `workflow/replay.py` | `_post_terminal_composition_call` | a work-bound provider call after a terminal is refused at replay |

Construction is where the seam is armed, and the order inside `__init__` is
load-bearing: the guard, then the binding, then any workflow object at all.
`check: python -c 'import inspect; from deepreason.scheduler.scheduler import Scheduler as S; s = inspect.getsource(S.__init__); assert "RunManifest v6 scheduler requires the global transaction dispatch guard" in s; assert s.index("transaction_authority_required") < s.index("bind_v6_authority") < s.index("ConjectureShadowObserver")' && python -m pytest tests/test_v6_scheduler_model_phase_deferral.py::test_v6_scheduler_rejects_an_unguarded_adapter_before_work tests/test_v6_global_dispatch_guard.py::test_transaction_required_adapter_rejects_unbound_dispatch -q`

The scheduler's only lever over whether a transaction exists is the argument it
passes: `conj` opens an `InquiryTransactionService` only when handed a manifest,
and the scheduler hands one only for schema 4/5/6 in an active control-plane
mode. Under v6 it additionally nulls the context plan it just built, because the
preparation must be the first durable record of the turn.
`check: python -c 'import inspect; from deepreason.scheduler.scheduler import Scheduler as S; g = inspect.getsource(S.step); assert g.index("_plan_conjecture_context(problem, school_id)") < g.index("context_plan = None") < g.index("admitted = conj("); assert "schema_version in {4, 5, 6}" in g and "in {\"active_conjecture\", \"active_inquiry\"}" in g; import deepreason.rules.conj as C; c = inspect.getsource(C.conj); assert c.index("if run_manifest is not None:") < c.index("InquiryTransactionService")'`

Recovery is the first statement of `run()`, latched so it happens once per
`Scheduler`, and fail-closed: anything it cannot settle raises rather than
letting a cycle proceed. The v6 branch returns before the v4/v5 reducer path, so
the two generations never mix.
`check: python -c 'import ast, inspect, textwrap; from deepreason.scheduler.scheduler import Scheduler as S; run = inspect.getsource(S.run); rec = inspect.getsource(S._recover_workflow_prefixes); assert ast.unparse(ast.parse(textwrap.dedent(run)).body[0].body[1]) == "self._recover_workflow_prefixes()"; assert run.index("self._recover_workflow_prefixes()") < run.index("for _ in range(cycles)"); assert "if self._workflow_recovery_done:" in rec; assert "transaction recovery left unfinished authority" in rec; assert rec.index("recover_incomplete()") < rec.index("write_workflow_checkpoint()"); assert rec.index("schema_version == 6") < rec.index("unfinished workflow authority requires its original v4 manifest") < rec.index("reduce_conjecture(") < rec.index("record_control_transition(")' && python -m pytest tests/test_workflow_shadow_c0.py::test_restart_abandons_every_durable_shadow_crash_prefix -q`

Routing is by `WorkflowTaskKind`, and neither recovery function accepts an
adapter — resumption re-validates the stored blob rather than asking a provider
again.
`check: python -c 'import inspect; from deepreason.scheduler.scheduler import Scheduler as S; from deepreason.workflow import conjecture_recovery as c, nonconjecture_recovery as n; rec = inspect.getsource(S._recover_workflow_prefixes); assert "WorkflowTaskKind.CONJECTURE" in rec and "recover_conjecture_admission(" in rec and "recover_nonconjecture_admission(" in rec; assert not [f for f in (c.recover_conjecture_admission, n.recover_nonconjecture_admission) if "adapter" in inspect.signature(f).parameters]' && python -m pytest tests/test_v6_nonconjecture_recovery.py::test_scheduler_recovers_valid_critic_without_provider_dispatch -q`

`recover_incomplete` returns only attempts whose admission is missing; work that
already has one it terminates and forgets. The scheduler widens that set on its
own, adding back CRITICISM and SCRATCH_AUTHORING attempts that are already
admitted, because for those seats the durable admission precedes a
*caller-owned* effect that a crash can still have lost. This is the one place
the scheduler knows something about the transaction the transaction service
does not.
`check: python -c 'import inspect; from deepreason.scheduler.scheduler import Scheduler as S; from deepreason.workflow.transaction_service import InquiryTransactionService as I; rec = inspect.getsource(S._recover_workflow_prefixes); assert "WorkflowTaskKind.CRITICISM, WorkflowTaskKind.SCRATCH_AUTHORING" in rec; assert "recovery_by_id.update(admitted_effect_candidates)" in rec; src = inspect.getsource(I.recover_incomplete); assert "elif admission is None:\n                pending_admission.append(provider)\n            else:\n                status = {" in src; assert src.count("self.terminate(") == 3; assert src.rstrip().endswith("return tuple(pending_admission)")' && python -m pytest tests/test_v6_nonconjecture_recovery.py::test_recovered_criticism_applies_canonical_effect_exactly_once tests/test_v6_nonconjecture_recovery.py::test_recovery_reuses_scratch_effect_already_applied_before_admission -q`

`_defer_untransactional_v6_phase` returns `False` before doing anything at all
for a non-v6 manifest, so historical schedulers keep byte-identical call paths;
under v6 it deduplicates against the log itself, which is what makes the marker
survive a resume.
`check: python -c 'import inspect; from deepreason.scheduler.scheduler import Scheduler as S; d = inspect.getsource(S._defer_untransactional_v6_phase); assert "schema_version != 6" in d and d.index("return False") < d.index("record_measure"); assert d.index("for event in self.harness.log.read()") < d.index("self.harness.record_measure"); assert "v6-model-phase-deferred.v1" in d' && python -m pytest tests/test_v6_scheduler_model_phase_deferral.py -q`

Foreign criticism is the one phase where the scheduler must persist workflow
records *before* dispatch, and the order is plan → obligations → route leases →
provider. One bad lease therefore leaves obligations but no spend and no
coverage receipt.
`check: python -c 'import inspect; from deepreason.scheduler.scheduler import Scheduler as S; f = inspect.getsource(S._foreign_arg_crit); assert f.index("plan_foreign_criticism(manifest") < f.index("record_criticism_obligation(assignment)") < f.index("resolve_school_role_lease(") < f.index("crit_argumentative_batch(")' && python -m pytest tests/test_foreign_school_criticism_scheduler_c3.py -q`

The stop path has two shapes. Without a recognised control plane it writes a
bare stop record and returns; with one it builds the typed receipt, appends the
lifecycle Control event at a pre-computed seq, verifies the event landed on that
fence, and only then persists the stop record and the checkpoint.
`check: python -c 'import inspect; from deepreason.scheduler.scheduler import Scheduler as S; from deepreason.workflow import lifecycle as L; r = inspect.getsource(S._record_stop); assert r.index("write_stop_record(") < r.index("return") < r.index("build_stopped_lifecycle"); assert r.index("build_stopped_lifecycle(") < r.index("record_lifecycle_transition(") < r.index("persist_stop_record(") < r.index("write_workflow_checkpoint()"); assert "lifecycle Control event crossed its stop fence" in r; assert "STOPPED refuses unfinished workflow authority" in inspect.getsource(L.build_stopped_lifecycle)' && python -m pytest tests/test_workflow_stop_lifecycle_c4.py::test_terminal_builder_snapshots_then_refuses_unfinished_provider_work tests/test_workflow_stop_lifecycle_c4.py::test_v4_stop_is_a_replayable_control_event_bound_to_run_stop -q`

## What is deliberately absent

**The scheduler opens and settles no transaction.** It calls none of `prepare`,
`context_plan`, `reserve_dispatch`, `finalize_dispatch`, `issue`,
`record_provider_attempt`, `record_semantic_admission`, `terminate` or
`repair_schema_failure`, and it never calls `record_transaction_transition` —
every one of the six transaction appends is written inside
`transaction_service.py`. The single service method it does call is
`recover_incomplete`. Adding a `service.terminate(...)` to the scheduler to
"tidy up" a work item is the intuitive fix and produces a transition the rule
that owns the work knows nothing about.
`check: ! grep -qE "\.(prepare|context_plan|reserve_dispatch|finalize_dispatch|issue|record_provider_attempt|record_semantic_admission|terminate|repair_schema_failure)\(" src/deepreason/scheduler/scheduler.py && ! grep -q "record_transaction_transition" src/deepreason/scheduler/scheduler.py && grep -q "transaction_service.recover_incomplete()" src/deepreason/scheduler/scheduler.py && test "$(grep -c "self.harness.record_transaction_transition(" src/deepreason/workflow/transaction_service.py)" -eq 6 && for s in prepare context_plan reserve_dispatch finalize_dispatch issue record_provider_attempt record_semantic_admission terminate repair_schema_failure; do grep -q "    def $s(" src/deepreason/workflow/transaction_service.py || exit 1; done && for f in rules/conj.py rules/crit.py scratch/authoring.py referee.py; do grep -q "InquiryTransactionService(" "src/deepreason/$f" || exit 1; done`

**The scheduler never writes to `workflow_state`, and never re-derives it.** It
reads the materialization the harness already holds — outstanding ids,
transaction work, work orders, branches, the current resume decision — and
assigns to none of it; `replay_workflow` and `WorkflowReplayState` do not appear
in the package at all. Its failure bookkeeping is the same discipline one level
down: `_drop` records an `LLMCall` or a Measure and appends no control or
transaction event, which is why calling it on an already-terminalized error
costs a duplicate diagnostic rather than a second transition.
`check: ! grep -qE "workflow_state[A-Za-z_.]* *=[^=]" src/deepreason/scheduler/scheduler.py && ! grep -qE "replay_workflow|WorkflowReplayState" src/deepreason/scheduler/scheduler.py && test "$(grep -c "self.harness.workflow_state" src/deepreason/scheduler/scheduler.py)" -ge 10 && grep -q "^def replay_workflow(" src/deepreason/workflow/replay.py && grep -q "self.workflow_state = WorkflowReplayState()" src/deepreason/harness.py && python -c 'import inspect; from deepreason.scheduler.scheduler import Scheduler as S; d = inspect.getsource(S._drop); assert "record_llm_calls" in d and "record_measure" in d; assert not [t for t in ("record_control_transition", "record_transaction_transition", "workflow") if t in d]'`

**The scheduler mints STOPPED but never RESUMED.** `build_resumed_lifecycle` is
called by `runtime/continuation.py`, outside the run loop; the scheduler only
*consumes* the resulting `current_resume_decision` to restore the stop
controller's window and its cycle offset. This is what keeps resume authority a
decision about a root rather than a decision a running scheduler can make about
itself, and `replay.py` enforces the other half by refusing a work-bound
provider call that follows a terminal without one.
`check: ! grep -q "build_resumed_lifecycle" src/deepreason/scheduler/scheduler.py && grep -q "^def build_resumed_lifecycle(" src/deepreason/workflow/lifecycle.py && grep -q "build_resumed_lifecycle" src/deepreason/runtime/continuation.py && grep -q "resume = self.harness.workflow_state.current_resume_decision" src/deepreason/scheduler/scheduler.py && grep -q "work-bound provider call follows terminal lifecycle state" src/deepreason/workflow/replay.py && python -m pytest tests/test_workflow_resume_lifecycle_c4.py::test_resumed_scheduler_rehydrates_exact_controller_state tests/test_workflow_resume_lifecycle_c4.py::test_resumed_scheduler_refuses_to_drop_bound_stop_controller tests/test_workflow_resume_lifecycle_c4.py::test_work_transition_is_blocked_until_resumed_and_consumes_resume -q`

**Under v6 there is no shadow observer and no scheduler-built control trace.**
`__init__` sets the observer to `None` for schema 6, which switches off the
candidate sink, the ticket and the whole `ConjectureControlTrace` path — the
transaction *is* the record, and a second, parallel bracket around it would be
two authorities describing one call. Restoring the observer "for symmetry" gives
v6 runs shadow comparisons that duplicate their own transactions. The absence is
asymmetric on purpose: in v4/v5 active mode a missing ticket or trace is fatal
before dispatch, because there the trace is the only durable authority.
`check: python -c 'import inspect; from deepreason.scheduler.scheduler import Scheduler as S; i = inspect.getsource(S.__init__); g = inspect.getsource(S.step); assert "if run_manifest is not None and run_manifest.schema_version == 6\n                else ConjectureShadowObserver.from_manifest(run_manifest)" in i; assert g.index("workflow_control_trace = self._workflow_control_trace(shadow_ticket)") < g.index("active conjecture control trace is unavailable") < g.index("admitted = conj("); assert "if self._active_conjecture_mode() and (" in g' && grep -q "workflow_control_trace.require_authority()" src/deepreason/rules/conj.py && python -m pytest tests/test_workflow_shadow_c0.py::test_active_trace_failure_is_terminal_while_shadow_remains_advisory tests/test_workflow_shadow_c0.py::test_active_planning_failure_stops_before_unbound_dispatch -q`

**The v6 capability follow-up passes no trace and asserts afterwards.** The
pre-v6 branch builds `build_capability_follow_up_trace` and hands it to `conj`;
the v6 branch snapshots `transaction_work`, calls `conj`, and requires that
exactly one fresh bound transaction appeared naming this result package. The
scheduler is verifying the rule's transaction, not authoring one, which is why
the assertion is a diff and not a record.
`check: python -c 'import inspect; from deepreason.scheduler.scheduler import Scheduler as S; v6 = inspect.getsource(S._v6_simulation_result_follow_up); legacy = inspect.getsource(S._simulation_capability_step); assert not [t for t in ("workflow_control_trace", "build_capability_follow_up_trace") if t in v6]; assert v6.index("before_work = set(") < v6.index("conj(") < v6.index("new_work_ids ="); assert "simulation result did not create exactly one fresh bound transaction" in v6; assert "build_capability_follow_up_trace" in legacy and "workflow_control_trace=trace" in legacy' && python -m pytest tests/test_v6_engaged_public_defaults.py::test_public_preset_mock_run_stages_and_consumes_one_simulation_proposal -q`

**Transaction recovery is absent from `step()`, and the `run()` prologue does
not cover capability dispatch.** There are two recovery mechanisms on two
cadences:
workflow-transaction recovery runs once, at `run()` entry, and capability
dispatch recovery runs every cycle inside `_simulation_capability_step`, which
pre-empts the rest of `step()`. A partially-completed cycle is therefore
recovered in two different places depending on where it died — an interrupted
simulation dispatch heals on the next `step()`, an interrupted provider
transaction only on the next `run()`.
`check: python -c 'import inspect; from deepreason.scheduler.scheduler import Scheduler as S; step = inspect.getsource(S.step); sim = inspect.getsource(S._simulation_capability_step); assert "_recover_workflow_prefixes" in inspect.getsource(S.run); assert "_recover_workflow_prefixes" not in step; assert step.index("if self._simulation_capability_step():") < step.index("scan_spawns(harness, config)"); assert "CapabilityLifecycle.DISPATCHED" in sim and "interrupted" in sim' && python -m pytest tests/test_simulation_capability_v5.py::test_dispatched_crash_recovers_as_unknown_without_silent_rerun -q`

**`workflow/` names nothing under `deepreason.scheduler`.** The arrow is
one-way, and only two of the scheduler's sixteen workflow references are
module-scope imports — the rest are function-local, which is what lets
`workflow/` stay importable without dragging in the run loop. The check is in
"The agreement" above.

## How to change it

The order is forced by which side can refuse. Start at the authority, end at the
attention; the other direction produces cycles that ran without a record.

1. **Read `DR-INV-frozen-surfaces` first.** Anything that enters
   `WorkflowReplayState.digest` is append-only in the subtler sense
   (`DR-SUB-workflow`'s trap), and `verify_root` re-derives the process state
   twice and compares. A per-run knob goes on `Config`, never on the manifest.
2. **Add the workflow record before the scheduler call site.** A new durable
   record needs its class, a schema row in `storage/objects.py`, an `apply`
   branch in `workflow/replay.py` and an `action` literal in
   `control_events.py` before anything in `scheduler/` may append it. Writing
   the scheduler half first produces an event replay refuses to load, and the
   failure surfaces on reopen rather than at the append.
3. **A new scheduler phase that touches a provider is a transaction question
   first.** Under v6 the choice is exactly two: give the phase a real
   transaction inside the rule that makes the call, or route it through
   `_defer_untransactional_v6_phase` at its call site. There is no third option
   — the adapter's global guard fails the whole root on an unbound dispatch, and
   that is the point.
4. **Move the recovery arm with the dispatch arm.** Any new task kind that
   settles a durable admission *before* applying a caller-owned effect must join
   the `admitted_effect_candidates` set, or a crash between admission and effect
   silently loses the effect while the record says it happened. Any new task
   kind at all needs a branch in the recovery routing, or it falls to
   `recover_nonconjecture_admission` and its `_RECOVERABLE_TASKS` check.
5. **If it can leave work open, it must reach the stop path.** `_record_stop`
   hands the whole `workflow_state` to `build_stopped_lifecycle`, which refuses
   a receipt while anything is outstanding. A phase that can exit a cycle with
   an unsettled work order turns every subsequent stop into a hard failure, not
   a degraded one.

What breaks first, in the order you will see it:
`WorkflowAuthorizationError("RunManifest v6 scheduler requires the global
transaction dispatch guard")` at construction; then the adapter's own refusal
mid-cycle (`DR-SEAM-llm-x-workflow`); then
`RuntimeError("transaction recovery left unfinished authority")` on the next
`run()`; then `ValueError("STOPPED refuses unfinished workflow authority")` when
the run tries to stop; and finally `verify_root`'s `workflow-replay` failure,
which is the expensive one because the root is already committed.

The tests that catch you, cheapest first:
`tests/test_v6_scheduler_model_phase_deferral.py` (guard and deferral,
sub-second), `tests/test_config_referee.py` (budget-denied absorption),
`tests/test_workflow_stop_lifecycle_c4.py` and
`tests/test_workflow_resume_lifecycle_c4.py` (terminal authority, ~1 s),
`tests/test_foreign_school_criticism_scheduler_c3.py` (obligations before
dispatch), `tests/test_workflow_shadow_c0.py` (the pre-v6 bracket and crash
prefixes), `tests/test_v6_nonconjecture_recovery.py` (recovery routing), then
`tests/test_v6_engaged_public_defaults.py` (~25 s; the whole v6 loop).
Deleting `self._recover_workflow_prefixes()` from `run()` fails
`test_restart_abandons_every_durable_shadow_crash_prefix`,
`test_scheduler_recovers_valid_critic_without_provider_dispatch` and
`test_invalid_stored_critic_output_terminalizes_without_scheduler_dispatch`.

## Traps

- **A budget denial arrives already terminalized, and the scheduler's job is to
  absorb it.** Live regression `run-e542c3c1`, the first referee-enabled ladder:
  the cycle-4 config review was token-budget-denied inside `service.issue`,
  which appends a typed `budget_denied` terminal — and the generic pre-issue
  `except` then called `abandon()`, a second transition after termination, which
  failed the run with `WellFormednessError`. `WorkBudgetDenied` now passes
  through the rule and the scheduler absorbs it: `_maybe_config_referee` returns,
  and gamma records a diagnostic and moves to the next school. The two handlers
  must stay ahead of the broad ones — the typed termination is the complete
  durable outcome, and a skipped advisory review must not stall the cycle.
`check: python -c 'import inspect; from deepreason.scheduler.scheduler import Scheduler as S; r = inspect.getsource(S._maybe_config_referee); assert "except WorkBudgetDenied:" in r and r.index("except WorkBudgetDenied:") < r.index("except (SchemaRepairError, EndpointError) as error:"); g = inspect.getsource(S.step); assert "except WorkBudgetDenied as error:" in g and "budget_denied" in g' && test "$(grep -c "except WorkBudgetDenied" src/deepreason/scheduler/scheduler.py)" -eq 2 && python -m pytest tests/test_config_referee.py::test_scheduler_absorbs_budget_denied_referee tests/test_config_referee.py::test_budget_denied_referee_terminates_typed_without_second_transition -q`
- **The deferral marker is the scheduler's substitute for a transaction, and it
  is not in the signal registry.** `v6-model-phase-deferred.v1` is bound to a
  local variable before `record_measure`, and `tests/test_signals.py` AST-scans
  only *literal* first elements, so the one signal that stands in for an absent
  transaction is neither scanned nor registered. `verification/report.py` reads
  it back, so the debt is visible in reports but invisible to the registry.
  Observed on `08dcdf3c`; recorded in `DR-SUB-scheduler`, not fixed there or
  here. Any signal emitted through a variable has the same hole.
`check: grep -q "marker = \"v6-model-phase-deferred.v1\"" src/deepreason/scheduler/scheduler.py && grep -q "v6-model-phase-deferred.v1" src/deepreason/verification/report.py && python -c 'from deepreason.signals import is_known, SIGNALS; assert SIGNALS and is_known(next(iter(SIGNALS))); raise SystemExit(1 if is_known("v6-model-phase-deferred.v1") else 0)'`
- **Residue: the "exactly one fresh bound transaction" assertion is held by
  nothing behavioural.** Deleting the
  `WorkflowAuthorizationError("simulation result did not create exactly one
  fresh bound transaction")` block leaves `tests/test_v6_engaged_public_
  defaults.py` fully green (9 passed, re-measured at `546544b5`); only the
  structural check in "What is deliberately absent" would notice. The happy
  path creates exactly one transaction, so no test distinguishes "verified" from
  "assumed". The generalisation is the same one `DR-SEAM-llm-x-workflow` records
  about `retry_max`: an assertion whose violating case no fixture produces is
  tested by nothing.
- **Under v6 the local criticism ladder is empty, and that is not a bug.**
  `_criticize`'s HV-floor and rubric arms, pairwise discrimination, experiment
  and property design, audit, vision and lazy HV all record deferral debt
  instead of dispatching. Argumentative criticism is a genuine exception, not
  a third case: with a manifest `criticism_policy` present, `_arg_crit`
  delegates the entire phase to `_foreign_arg_crit` and returns — the
  transactional path — and a v6 manifest *without* a criticism policy now
  ALSO dispatches live (FIXED 2026-08-10, adjudication-judge-seats-optins
  tranche, S13i: `crit_argumentative_batch` self-detects a v6-bound adapter
  via `LLMAdapter.bound_v6_manifest()` and resolves its own default route,
  with the scheduler's own call staying keyword-free per
  `DR-SEAM-scheduler-x-rules`'s invariant). Before this fix, the school-free
  case fell through to per-target deferral debt instead — that was the
  actual defect this tranche's operator request ("why were [criticism
  seats] disconnected") traced to. Argumentative criticism is now the ONLY
  local-ladder phase that never defers under v6.
`check: python -c 'import inspect; from deepreason.scheduler.scheduler import Scheduler as S; a = inspect.getsource(S._arg_crit); assert a.index("manifest foreign criticism has no runtime critic role") < a.index("self._foreign_arg_crit()") < a.index("crit_argumentative_batch("); assert "if criticism_policy is not None:\n            self._foreign_arg_crit()\n            return" in a; assert "argumentative-criticism" not in a' && python -m pytest tests/test_v6_scheduler_model_phase_deferral.py::test_legacy_argumentative_criticism_dispatches_under_v6 tests/test_v6_scheduler_model_phase_deferral.py::test_v6_audit_vision_and_lazy_hv_defer_without_dispatch tests/test_v6_scheduler_model_phase_deferral.py::test_v6_pairwise_discrimination_never_reaches_unbound_judge -q`
