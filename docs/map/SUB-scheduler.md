<!-- DR-SUB-scheduler -->
Verified-at: 08dcdf3c
Verify: python -m pytest tests/test_scheduler.py tests/test_rotation.py tests/test_v6_scheduler_model_phase_deferral.py -q
Owns: src/deepreason/scheduler/
Seams: 
Seams-undocumented: authority x scheduler, capabilities x scheduler, harness x scheduler, llm x scheduler, manifest x scheduler, rules x scheduler, scheduler x schools, scheduler x scratch, scheduler x workflow

# The scheduler — what gets worked on, in what order, under what budget

## What it is

The scheduler is the run's control flow: one class, `Scheduler`, whose `step()`
is a cycle and whose `run(cycles)` is a session. It is not a node graph — it is
"apply the enabled rules under budget", so a new phase is a call in a list, not
an edge in a diagram. Every decision it makes is *attention*: which problem to
work, which school to ask, how many provider calls criticism may spend, when to
stop. It never assigns a status and never adjudicates; it hands records to the
harness and reads the state the harness computed. That is structural, not
stylistic — the package writes no file and mutates no status, HV or reach map,
so an attention bug cannot become an epistemic one. Almost everything that
costs tokens is rationed, and almost every ration has a live-run postmortem
behind it; the cheap deterministic work is deliberately not rationed.
`check: ! grep -qE "open\(|write_text|write_bytes|\.mkdir\(" src/deepreason/scheduler/scheduler.py && ! grep -qE "state\.(status|hv|reach)\[[^]]*\] *=" src/deepreason/scheduler/scheduler.py`

## Entry points

- `Scheduler` — constructed by `ops.run_scheduler` with a harness, an adapter, a
  `Config`, and optionally an embedder, research service, browser backend,
  self-calibration controller, stop controller, progress sink and `RunManifest`.
  A v6 manifest is refused unless the adapter carries the global transaction
  dispatch guard.
- `Scheduler.run(cycles, on_cycle=None)` — the session loop: crash recovery,
  resume rehydration, then `step()` per cycle with the stop controller evaluated
  at each completed boundary. `on_cycle` is a read-only hook; a truthy return
  ends the run early. Returns `report()`, plus `stop_reason` if the policy
  stopped it.
- `Scheduler.step()` — one cycle. Capability items pre-empt everything; then
  spawn scan, problem selection, the cycle heartbeat, school allocation, gamma
  (conjecture, or synthesis for connection/integration problems), per-candidate
  criticism, then the sweep tail.
- `Scheduler.report()` — survivors, the Pareto `frontier` over (hv, reach,
  coverage), problems, and the in-memory diagnostics list. Attention and
  reporting only, never a status.
- `Scheduler.activate_interventions(names)` — the response ladder's only lever;
  turns named interventions on for `CAPTURE_W` cycles.
- `reflexive_problems(state)` — the meta-work set, following lineage: a
  successor of a debt problem stays reflexive instead of laundering itself into
  ordinary work.
- `problem_family(state, root_pid)` — transitive spawn closure of a problem;
  used by `FOCUS_FAMILY` and by `easy.py`'s staged pipeline.
- `problem_family_key(state, problem_id)` — the stable provenance-root identity
  a family is known by. Consumed by the anti-relapse gate (`rules/conj.py`),
  `jolts.py` and `views/jolt_signals.py`, so a refuted approach cannot re-enter
  under a fresh successor id.
- `lineage_endpoints(problem, commitments, state)` and
  `stable_component_spec(problem, endpoints)` — the frozen, input-side identity
  handed to the conjecturer for `code`/`website`/`formal` workloads. Never
  candidate output bytes.

The internal phases are the real surface for a change: `_select_problem`,
`_criticize`, `_arg_crit`, `_foreign_arg_crit`, `_simulation_capability_step`,
`_experiment_step`, `_property_step`, `_fuzz_sweep`, `_browser_step`,
`_vision_step`, `_research_step`, `_audit_step`, `_capture_step`, `_lazy_hv`,
`_maybe_config_referee`, `_recover_workflow_prefixes`, `_record_stop`.
`check: grep -q "^class Scheduler:" src/deepreason/scheduler/scheduler.py && for s in reflexive_problems problem_family problem_family_key lineage_endpoints stable_component_spec; do grep -q "^def $s(" src/deepreason/scheduler/scheduler.py || exit 1; done && for s in step run report activate_interventions _select_problem _criticize _arg_crit _foreign_arg_crit _simulation_capability_step _experiment_step _property_step _fuzz_sweep _browser_step _vision_step _research_step _audit_step _capture_step _lazy_hv _maybe_config_referee _recover_workflow_prefixes _record_stop; do grep -q "^    def $s(" src/deepreason/scheduler/scheduler.py || exit 1; done`

Two orderings are load-bearing. The tail of `step()` runs the design steps
before the fuzz sweep, so new generators and properties apply in the same cycle,
and vision after the browser, so it judges freshly recorded renders. Within
`_criticize` one candidate's passes go cheapest-first — program checks,
deterministic fuzz, HV floor, rubric trials — so a target felled for free never
reaches a provider call.
`check: test "$(sed -n "/^    def step(/,/^    def _audit_step(/p" src/deepreason/scheduler/scheduler.py | grep -o "self\._[a-z_]*()" | tail -9 | tr -d "\n")" = "self._lazy_hv()self._experiment_step()self._property_step()self._fuzz_sweep()self._browser_step()self._vision_step()self._research_step()self._audit_step()self._capture_step()" && test "$(sed -n "/^    def _criticize(/,/^    def _standing_recrit_pool(/p" src/deepreason/scheduler/scheduler.py | grep -oE "crit_program\(|crit_fuzz\(|run_hv_floor\(|run_trial\(" | tr -d "\n")" = "crit_program(crit_fuzz(run_hv_floor(run_trial("`

## State it owns

**Nothing on disk, directly.** Durable effects go through collaborators: the
harness (the cycle heartbeat `Measure`, the once-per-run embedder geometry
stamp, dropped-call records, v6 deferral markers, foreign-criticism receipts and
coverage debt, the stop `Measure` and lifecycle `Control` event),
`runtime/stop.py` (`run-stop.json` and `run-stops/<seq>-<digest>.json` under the
run root), and `runtime/progress.py` (`progress.jsonl`). The `RunManifest` is
injected, never imported: roughly thirty branch points read its
`schema_version` and policies, with no compile-time dependency on the module.
`check: grep -q "persist_stop_record" src/deepreason/scheduler/scheduler.py && grep -q "run-stop.json" src/deepreason/runtime/stop.py && grep -q "progress.jsonl" src/deepreason/runtime/progress.py && test "$(grep -c "self\.run_manifest" src/deepreason/scheduler/scheduler.py)" -ge 25 && ! grep -q "from deepreason.run_manifest import" src/deepreason/scheduler/scheduler.py`

**In memory, per instance:** attention caches only, all rebuildable and none
epistemic — `_problem_worked` (liveness ages), `_disc_attempts` / `_disc_last`
(discrimination futility), `_fuzz_clean`, `_vision_done`, `_hv_skipped`,
`_recrit_cursor`, `_flag_streak` / `_cooldown` (capture hysteresis),
`_intervention_until` (ladder expiry), `_v6_deferred_model_phases`. Rebuilding a
`Scheduler` mid-run wipes them, which is why `run()` takes an `on_cycle`
early-stop hook instead. Every signal the package emits is registered in
`src/deepreason/signals.py` — with one exception, recorded under Traps.
`check: for s in _problem_worked _disc_attempts _disc_last _fuzz_clean _vision_done _hv_skipped _recrit_cursor _flag_streak _cooldown _intervention_until _v6_deferred_model_phases; do grep -q "self\.$s" src/deepreason/scheduler/scheduler.py || exit 1; done && for t in cycle embedder spec-generation scheduler-stop stop-escape disc-attempts-exhausted disc-transport-deferred hv-skip-oversize research-awaiting-agent research-fetch-exhausted foreign-criticism-coverage.v1; do grep -q "\"$t\"" src/deepreason/signals.py || exit 1; done && python -m pytest tests/test_signals.py tests/test_scheduler.py::test_on_cycle_true_stops_the_run_early -q`

## Where to change what

| To change... | Edit | Test |
|---|---|---|
| Which problem a cycle works on, or the rank tie-break | `_select_problem`; `Config.LIVENESS_QUEUE`, `FOCUS_PROBLEM`, `FOCUS_FAMILY` | `tests/test_controller.py::test_operator_question_outranks_spawns_at_cycle_zero`, `tests/test_scheduler.py::test_focus_family_restricts_selection` |
| What counts as reflexive/meta work, or its budget share | `_REFLEXIVE_TRIGGERS` + `reflexive_problems`; `Config.INTEGRATION_BUDGET_SHARE` | `tests/test_reflexive_discipline.py::test_reflexive_budget_follows_lineage`, `tests/test_scheduler.py::test_integration_budget_share_caps_connection_work` |
| Add a per-cycle phase, or reorder the sweep tail | the call list at the end of `step`, plus a `_<name>_step` method | `tests/test_scheduler.py::test_multi_cycle_spawns_and_persistence` |
| How much LLM criticism a cycle may spend, or its batching | `_arg_crit`; `Config.ARG_CRIT_PER_CYCLE`, `CRIT_BATCH_K`, `RECRIT_STANDING` | `tests/test_budget.py::test_arg_crit_per_cycle_cap` |
| Which standing survivors get re-criticized, and in what order | `_standing_recrit_pool` | `tests/test_properties.py::test_standing_recrit_pool_includes_active_properties` |
| Discrimination backoff / when a rivalry is left unresolved | `_disc_paused`; `Config.DISC_ATTEMPTS_MAX`, `DISC_COOLDOWN` | `tests/test_rotation.py::test_attempt_cap_frees_the_rotation`, `::test_transport_drop_defers_instead_of_burning_the_futility_cap` |
| When fuzz re-probes, or what clears the clean bit | `_fuzz_sweep` and the `_fuzz_clean.clear()` calls in `_experiment_step` / `_property_step` | `tests/test_experiment.py::test_fuzz_sweep_is_not_rationed_behind_llm_slots` |
| Experiment / property design cadence | `_experiment_step`, `_property_step`; `Config.GEN_PROPOSE_PERIOD`, `GEN_MAX`, `PROP_PROPOSE_PERIOD`, `PROP_MAX` | `tests/test_v6_scheduler_model_phase_deferral.py::test_v6_experiment_and_property_design_defer_before_provider` |
| Capability dispatch order, or recovery of a dispatched item | `_simulation_capability_step`, `_v6_simulation_result_follow_up` | `tests/test_simulation_capability_v5.py::test_conjecture_records_only_proposal_and_scheduler_executes_later`, `::test_dispatched_crash_recovers_as_unknown_without_silent_rerun` |
| Foreign-school criticism coverage, receipts, or coverage debt | `_foreign_arg_crit`, `_foreign_criticism_coverage`; manifest `criticism_policy` | `tests/test_foreign_school_criticism_scheduler_c3.py` |
| Research cadence, backoff, or the agent-mode waiting state | `_research_step`, `_log_research_failure`; `Config.RESEARCH_PERIOD`, `RESEARCH_COOLDOWN`, `RESEARCH_ATTEMPTS_MAX` | `tests/test_research.py::test_backend_exception_is_caught_logged_and_cooled_down`, `::test_agent_mode_waits_and_never_claims_research_off` |
| What ends a run, and what the stop record contains | the stop block in `run`, `_stop_metrics`, `_record_stop` | `tests/test_workflow_stop_lifecycle_c4.py::test_v4_stop_is_a_replayable_control_event_bound_to_run_stop` |
| Add a response-ladder intervention | `activate_interventions` + a derived property, and `capture/ladder.respond` | `tests/test_diversity.py::test_stagnation_ladder_switches_on_spec_injection` |
| A legacy model phase v6 cannot yet dispatch | `_defer_untransactional_v6_phase` at the phase's call site | `tests/test_v6_scheduler_model_phase_deferral.py::test_v6_deferral_marker_is_durable_bounded_and_resume_deduplicated` |
| Config-referee cadence | `_maybe_config_referee`; manifest `inquiry_capability_policy.config_referee` | `tests/test_config_referee.py::test_scheduler_fires_referee_only_on_the_frozen_cadence`, `::test_scheduler_absorbs_budget_denied_referee` |
| What `report()` returns / the Pareto frontier axes | `report`; `Config.PARETO_AXES` and `capture/pareto.frontier` | `tests/test_scheduler.py::test_multi_cycle_spawns_and_persistence` |

`check: python -m pytest tests/test_scheduler.py tests/test_rotation.py tests/test_controller.py::test_operator_question_outranks_spawns_at_cycle_zero tests/test_reflexive_discipline.py::test_reflexive_budget_follows_lineage tests/test_budget.py::test_arg_crit_per_cycle_cap tests/test_properties.py::test_standing_recrit_pool_includes_active_properties tests/test_experiment.py::test_fuzz_sweep_is_not_rationed_behind_llm_slots tests/test_diversity.py::test_stagnation_ladder_switches_on_spec_injection -q`
`check: python -m pytest tests/test_v6_scheduler_model_phase_deferral.py tests/test_workflow_stop_lifecycle_c4.py tests/test_foreign_school_criticism_scheduler_c3.py tests/test_config_referee.py::test_scheduler_fires_referee_only_on_the_frozen_cadence tests/test_config_referee.py::test_scheduler_absorbs_budget_denied_referee tests/test_simulation_capability_v5.py::test_conjecture_records_only_proposal_and_scheduler_executes_later tests/test_simulation_capability_v5.py::test_dispatched_crash_recovers_as_unknown_without_silent_rerun tests/test_research.py::test_backend_exception_is_caught_logged_and_cooled_down tests/test_research.py::test_agent_mode_waits_and_never_claims_research_off -q`

## Traps

- **Cycle 0 fell to the bare id tie-break, and "solved" counted bookkeeping.**
  In `selfstudy run-9175f0ec` an attach-spawned `conn:<id>` sorted before
  `question-<digest>`, and evidence admission had already auto-accepted
  import-role records ADDRESSING the question — scoring it "solved" at the 0.3
  aging weight before a single provider call. The run burned its whole 200k
  budget inside the connection problem and the operator's question terminated
  `budget_denied` with zero calls. Two rules now hold in BOTH selection modes:
  import-role artifacts never count as survivors, and `SpawnTrigger.SEED` wins
  rank ties outright. `FOCUS_FAMILY` is the same class of hazard one level up —
  stage isolation, not a filter convenience: without it an earlier stage's
  unsolved successor leftovers out-age this stage's seed and the staged pipeline
  bleeds backward.
`check: grep -q "ProvenanceRole.IMPORT" src/deepreason/scheduler/scheduler.py && python -m pytest tests/test_controller.py::test_operator_question_outranks_spawns_at_cycle_zero tests/test_scheduler.py::test_focus_family_restricts_selection -q`
- **The meta-economy ate the inquiry.** In the Bronze Age postmortem, debt and
  remove-arbitrariness problems were budgeted as ordinary work and their
  successors escaped the reflexive set entirely — ~40 of 48 artifacts went to
  theory about the run instead of the question. `reflexive_problems` therefore
  follows LINEAGE, not just the trigger, and the whole set draws one
  `INTEGRATION_BUDGET_SHARE`-capped pool.
`check: grep -q "self._integration_cycles / self._cycles < self.config.INTEGRATION_BUDGET_SHARE" src/deepreason/scheduler/scheduler.py && python -m pytest tests/test_reflexive_discipline.py::test_reflexive_budget_follows_lineage -q`
- **Unsolved-first selection starved a run on an unresolvable rivalry.** Run 3
  spent 18 blocked pairwise trials against one conjecturer call: a blocked or
  "neither" ruling leaves the problem unsolved, and unsolved-first re-fed it
  forever. `_disc_paused` adds a cooldown and a permanent attempt cap. The
  exception matters — a transport-dropped ruling is no verdict at all and must
  NOT burn the permanent cap; only the cooldown applies.
`check: grep -q "if not transport_deferred:" src/deepreason/scheduler/scheduler.py && python -m pytest tests/test_rotation.py::test_transport_drop_defers_instead_of_burning_the_futility_cap -q`
- **Accepted-by-neglect, and rationing free criticism.** An artifact used to be
  criticized only in the cycle it was admitted, so anything accepted early was
  never attacked again; a buggy conjectured checker survived 80+ events unvisited
  (intervals/boot postmortem). Leftover argumentative capacity now sweeps a
  standing pool, and ACTIVE conjectured properties are in it — they are criteria
  with kill authority. Seed infrastructure is excluded by design (RC6:
  `ops.review_infrastructure` is its only attack route). The symmetric error was
  making the fuzz sweep reachable only with leftover arg-crit slots — a
  token-economy constraint imposed on criticism that costs sandbox steps, not
  tokens; it now runs every cycle over every standing candidate whose clean bit
  is unset, and the bit clears whenever the generator or property pool grows.
`check: grep -q "artifact.codec != \"code:python-prop\"" src/deepreason/scheduler/scheduler.py && python -m pytest tests/test_properties.py::test_standing_recrit_pool_includes_active_properties tests/test_experiment.py::test_fuzz_sweep_is_not_rationed_behind_llm_slots -q`
- **The capability-state maps pool every capability.** `result_packages`,
  `proposals` and `transitions` hold simulation AND research records together;
  `_simulation_capability_step` filters by `isinstance(package,
  SimulationResultPackageV1)` before scheduling a follow-up reasoning turn. Drop
  the filter and a research package schedules a simulation-shaped turn. Same
  hazard as the per-capability budget invariant: always filter by type.
`check: grep -q "isinstance(package, SimulationResultPackageV1)" src/deepreason/scheduler/scheduler.py && python -m pytest tests/test_simulation_capability_v5.py::test_research_spend_does_not_exhaust_simulation_budgets -q`
- **Ladder interventions must not latch, and recovery must not be lazy.**
  Interventions are stored as expiry cycles and read through derived properties,
  so a fired one clears after `CAPTURE_W` cycles instead of staying on for the
  rest of the run (§11.4 hysteresis); storing a boolean is the failure this
  shape prevents. Symmetrically, `run()` calls `_recover_workflow_prefixes` then
  `_rehydrate_resumed_stop_controller` before the loop — recovery that leaves
  outstanding authority raises, and a resumed run restores `_stop_cycle_offset`
  so stop metrics continue the original cycle numbering instead of restarting
  at 0.
`check: grep -q "return self._cycles < self._intervention_until.get(name, 0)" src/deepreason/scheduler/scheduler.py && ! grep -qE "self\.(recruit_all|tail_weighted|complement|research_priority) *=" src/deepreason/scheduler/scheduler.py && test "$(sed -n "/^    def run(self, cycles/,/for _ in range(cycles)/p" src/deepreason/scheduler/scheduler.py | grep -o "self\._[a-z_]*()" | head -2 | tr -d "\n")" = "self._recover_workflow_prefixes()self._rehydrate_resumed_stop_controller()" && grep -q "cycle=self._stop_cycle_offset + self._cycles" src/deepreason/scheduler/scheduler.py`
- **Silence is not evidence of absence.** In research "agent" mode there is no
  internal fetcher, so uncovered requests wait in `ops.research_docket`. The
  scheduler emits `research-awaiting-agent`, never `research-off` — the latter
  would tell a log reader research was disabled when it was merely pending, and
  the §11.4 exogenous brake would spin against an actuator it does not have.
  Both signals are episode-deduplicated: one event per continuous episode, not
  one per cycle.
`check: grep -q "research-awaiting-agent" src/deepreason/scheduler/scheduler.py && python -m pytest tests/test_research.py::test_agent_mode_waits_and_never_claims_research_off tests/test_research.py::test_null_mode_logs_research_off_once_per_episode -q`
- **A provider success that cannot produce exact receipts is an integrity
  failure, not debt.** `_foreign_arg_crit` resolves every batch's route lease
  before the first provider boundary — one bad binding therefore leaves no
  partial spend — and raises rather than recording partial coverage if a call
  returns without a receipt per assigned target. Route drift raises
  `RouteFirewallError` and stays fail-closed all the way up through `run()`.
`check: grep -q "foreign criticism call did not durably cover every assigned target" src/deepreason/scheduler/scheduler.py && grep -q "foreign criticism plan differs from its resolved route lease" src/deepreason/scheduler/scheduler.py && python -m pytest tests/test_foreign_school_criticism_scheduler_c3.py::test_batch_route_failure_is_detected_before_any_critic_dispatch -q`
- **The v6 deferral marker escapes the signal registry.** Under RunManifest v6
  the adapter fails closed on unbound dispatch, so legacy phases record
  `v6-model-phase-deferred.v1` as visible completion debt instead of failing the
  whole root, and `verification/report.py` reads it back. But the tag is bound to
  a local variable, and `tests/test_signals.py` only AST-scans *literal* first
  elements — so the marker is neither scanned nor registered in `signals.py`.
  Any signal emitted through a variable has the same hole. Observed on
  `08dcdf3c`; recorded, not fixed here.
`check: grep -q "marker = \"v6-model-phase-deferred.v1\"" src/deepreason/scheduler/scheduler.py && grep -q "v6-model-phase-deferred.v1" src/deepreason/verification/report.py && ! python -c "from deepreason.signals import is_known; raise SystemExit(0 if is_known(\"v6-model-phase-deferred.v1\") else 1)"`
