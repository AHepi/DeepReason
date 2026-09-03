<!-- DR-SUB-scheduler -->
Verified-at: 66e56fe88
Verify: python -m pytest tests/test_scheduler.py tests/test_rotation.py tests/test_v6_scheduler_model_phase_deferral.py tests/test_controller.py tests/test_controller_steering_parity.py -q
Owns: src/deepreason/scheduler/, src/deepreason/controller.py
Seams: DR-SEAM-scheduler-x-rules, DR-SEAM-scheduler-x-workflow, DR-SEAM-schools-x-scheduler, DR-SEAM-llm-x-scheduler, DR-SEAM-evaluation-x-scheduler
Seams-undocumented: authority x scheduler, capabilities x scheduler, harness x scheduler, manifest x scheduler, scheduler x scratch

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
`check: ! grep -rqE "open\(|write_text|write_bytes|\.mkdir\(" src/deepreason/scheduler/ --include=*.py && ! grep -rqE "state\.(status|hv|reach)\[[^]]*\] *=" src/deepreason/scheduler/ --include=*.py && grep -rqE "open\(|write_text|write_bytes|\.mkdir\(" src/deepreason/runtime/progress.py && grep -qE "state\.(status|hv|reach)\[[^]]*\] *=" src/deepreason/harness.py`

## Seams

| Side | Status | What the agreement is (one line) |
|---|---|---|
| `DR-SEAM-scheduler-x-rules` | documented | the scheduler decides what is worked on, by whom, how often; the rules decide what that work means epistemically |
| `DR-SEAM-scheduler-x-workflow` | documented | the scheduler decides what and when; the workflow plane decides by what recorded authority any of it may touch a provider |
| `DR-SEAM-evaluation-x-scheduler` | documented | the scheduler dispatches evaluation's work AND interprets its verdicts to rank; `overrun` means no verdict was obtained, so it may move no coordinate |
| authority x scheduler | undocumented | real: `scheduler/scheduler.py` is jointly `Owns:`-listed by `DR-CON-authority` — `Scheduler._criticize`/`Scheduler.step` are named rubric/pairwise call sites for `trial_authority_for` |
| scheduler x schools | undocumented | real, richly evidenced from the schools side (`DR-CON-schools`'s Where-it-lives table): `Scheduler._school_dict`, `_step`'s `school_leases`, `_foreign_arg_crit`, `_plan_conjecture_context` |
| capabilities x scheduler | undocumented, asymmetric | real for simulation only (`_simulation_capability_step`); research capability is never reached by the scheduler at all — see `DR-SUB-capabilities`'s Seams table for the full asymmetry and the unrelated same-named subsystem it warns about |
| llm x scheduler | **deliberately absent** | confirmed from the llm side: `llm/`'s own check proves it never imports `scheduler` |
| manifest x scheduler | **deliberately absent** | confirmed from the manifest side: its own exclusion-list check names `scheduler` explicitly, matching this package's own "the `RunManifest` is injected, never imported" claim |
| scheduler x scratch | **deliberately absent** | confirmed from the scratch side: its own dependency allowlist excludes `scheduler` explicitly |
| harness x scheduler | undocumented | real: durable scheduler effects (the cycle heartbeat `Measure`, dropped-call records, the stop `Measure`/lifecycle `Control` event) all go through the harness as a collaborator, per this document's own "State it owns" |

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
- `pareto_scores(harness, artifact_id)` — one survivor's score per Pareto axis,
  with an axis OMITTED where the harness measured nothing. An omitted axis is
  the typed "not measured", which `capture/pareto.frontier` drops out of that
  pairwise comparison instead of reading as 0.0. `coverage` is passes over the
  commitments that were actually DECIDED: a commitment evaluating `OVERRUN` —
  the verdict for "this module obtained no verdict" — leaves the denominator,
  and the axis is omitted entirely for an artifact that decided nothing, which
  covers both an empty battery and a battery every member of which is
  undecidable. `hv` and `reach` still emit their 0.0 default. Module-level, and
  the single place the axis rule lives.
`check: python -m pytest tests/test_coverage_pending_commitments.py tests/test_formalism_optional_rank.py -q`
- `run_report(harness, config, *, diagnostics=())` — survivors, the Pareto
  `frontier` over (hv, reach, coverage) via `pareto_scores`, problems, and the
  diagnostics passed in. Attention and reporting only, never a status. Since
  2026-08-30 a survivor with nothing to check does not compete on `coverage`,
  so a run whose survivors include commitment-free artifacts publishes a LONGER
  frontier than it used to — and `frontier_delta` is a `StopMetrics` input, so
  that also moves when such a run stops. It is module-level on
  purpose: constructing a `Scheduler` seeds schools, which APPENDS events, so a
  caller that only wants the report over a stopped root (`finalize_stopped_root`
  in `DR-SUB-application`) would otherwise have to mutate the record to read it.
- `Scheduler.report()` — the same report, delegating to `run_report` so the two
  can never disagree.
`check: grep -q "^def run_report(" src/deepreason/scheduler/scheduler.py && grep -q "^def pareto_scores(" src/deepreason/scheduler/scheduler.py && grep -q "return run_report(self.harness, self.config, diagnostics=self.diagnostics)" src/deepreason/scheduler/scheduler.py && grep -q "run_report(harness, config_from_run_manifest(manifest))" src/deepreason/application/text_runs.py && python -m pytest tests/test_lifecycle_operation_parity.py::test_finalize_resumes_after_an_interrupted_terminalization -q`
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
`check: grep -q "^class Scheduler:" src/deepreason/scheduler/scheduler.py && grep -q "def run_scheduler(" src/deepreason/ops.py && grep -q "RunManifest v6 scheduler requires the global transaction dispatch guard" src/deepreason/scheduler/scheduler.py && for s in reflexive_problems problem_family problem_family_key lineage_endpoints stable_component_spec; do grep -q "^def $s(" src/deepreason/scheduler/scheduler.py || exit 1; done && for s in step run report activate_interventions _select_problem _criticize _arg_crit _foreign_arg_crit _simulation_capability_step _experiment_step _property_step _fuzz_sweep _browser_step _vision_step _research_step _audit_step _capture_step _lazy_hv _maybe_config_referee _recover_workflow_prefixes _record_stop; do grep -q "^    def $s(" src/deepreason/scheduler/scheduler.py || exit 1; done && for c in rules/conj.py jolts.py views/jolt_signals.py easy.py; do grep -q "from deepreason.scheduler.scheduler import" "src/deepreason/$c" || exit 1; done`

## The per-cycle signal emission carries TWO instrument families (Rung 8)

`_record_detection_signals` fires once per cycle and now emits two families
over one state of the record. The three v2 detection signals read the standing
graph as it stands; `capture14.emit` reads a fixed SEQUENCE-NUMBER window
`W_m(n)` and emits §14's six, G-5's promotion-conditioning pair, and §14.7's
hysteresis step. They are a distinct family and not a replacement — the full
three-population table is in `DR-INV-signal-contract` (V-6).

Three orderings inside `capture14.emit` are load-bearing. The vector is
computed ONCE and emitted six times, so the six describe one window rather than
six adjacent ones. An owed `after` is paid BEFORE new elevations are recorded,
so an elevation happening in this same cycle cannot have its own `before`
mistaken for an owed `after`. And the hysteresis step runs LAST, so its policy
reads the vector this cycle actually emitted.

`check: grep -q "capture14.emit(harness, self.config)" src/deepreason/scheduler/scheduler.py && python -m pytest tests/test_capture14_emission.py tests/test_capture14_promotion_conditioning.py -q`

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
`_intervention_until` (ladder expiry), `_v6_deferred_model_phases`,
`_seed_cycles` / `_capability_cycles` (the allocation policy's two cycle
classes — `DR-CON-scheduler-ranking`). Rebuilding a
`Scheduler` mid-run wipes them, which is why `run()` takes an `on_cycle`
early-stop hook instead. Every signal the package emits is registered in
`src/deepreason/signals.py` — with one exception, recorded under Traps.
`check: for s in _problem_worked _disc_attempts _disc_last _fuzz_clean _vision_done _hv_skipped _recrit_cursor _flag_streak _cooldown _intervention_until _v6_deferred_model_phases _seed_cycles _capability_cycles; do grep -q "self\.$s" src/deepreason/scheduler/scheduler.py || exit 1; done && for t in cycle embedder spec-generation scheduler-stop stop-escape disc-attempts-exhausted disc-transport-deferred hv-skip-oversize research-awaiting-agent research-fetch-exhausted foreign-criticism-coverage.v1; do grep -q "\"$t\"" src/deepreason/signals.py || exit 1; done && python -m pytest tests/test_signals.py tests/test_scheduler.py::test_on_cycle_true_stops_the_run_early -q`
The "one exception" is an exact count, not a hedge: this check AST-scans every
`record_measure` head in the package, fails on any unregistered literal, and
fails if a SECOND variable-headed signal appears (both mutations were run).
`check: python -c "import ast,deepreason.signals as S; h=[(n.lineno,next((k.value.elts[0] for k in n.keywords if k.arg=='inputs' and getattr(k.value,'elts',None)),None)) for n in ast.walk(ast.parse(open('src/deepreason/scheduler/scheduler.py').read())) if isinstance(n,ast.Call) and getattr(n.func,'attr',getattr(n.func,'id',''))=='record_measure']; g=lambda e: e.values[0] if isinstance(e,ast.JoinedStr) and e.values else e; bad=[(l,g(e).value) for l,e in h if isinstance(g(e),ast.Constant) and not S.is_known(g(e).value)]; var=sorted(ast.unparse(e) for l,e in h if not isinstance(g(e),ast.Constant)); assert h, 'scan found no record_measure calls'; assert not bad, bad; assert var==['marker','signal'], var"`

## Where to change what

| To change... | Edit | Test |
|---|---|---|
| Which problem a cycle works on, or the rank tie-break | `_select_problem`; `Config.LIVENESS_QUEUE`, `FOCUS_PROBLEM`, `FOCUS_FAMILY` | `tests/test_controller.py::test_operator_question_outranks_spawns_at_cycle_zero`, `tests/test_scheduler.py::test_focus_family_restricts_selection` |
| What counts as reflexive/meta work, or its budget share | `_REFLEXIVE_TRIGGERS` + `reflexive_problems`; `Config.INTEGRATION_BUDGET_SHARE` | `tests/test_reflexive_discipline.py::test_reflexive_budget_follows_lineage`, `tests/test_scheduler.py::test_integration_budget_share_caps_connection_work` |
| Add a per-cycle phase, or reorder the sweep tail | the call list at the end of `step`, plus a `_<name>_step` method | `tests/test_scheduler.py::test_multi_cycle_spawns_and_persistence` |
| How much LLM criticism a cycle may spend, or its batching | `_arg_crit`; `Config.ARG_CRIT_PER_CYCLE`, `CRIT_BATCH_K`, `RECRIT_STANDING` | `tests/test_budget.py::test_arg_crit_per_cycle_cap` |
| Which standing survivors get re-criticized, and in what order | `_standing_recrit_pool` | `tests/test_properties.py::test_standing_recrit_pool_includes_active_properties` |
| What counts as a survivor in the published set and in the aging weight | NOT this package: `counts_as_survivor` in `ontology/state.py` (`DR-SUB-ontology`). `run_report` and `_select_problem` are consumers and may not re-spell the rule | `tests/test_import_role_survivors.py::test_the_writer_publishes_a_survivor_set_the_invariant_already_holds_over` |
| Discrimination backoff / when a rivalry is left unresolved | `_disc_paused`; `Config.DISC_ATTEMPTS_MAX`, `DISC_COOLDOWN` | `tests/test_rotation.py::test_attempt_cap_frees_the_rotation`, `::test_transport_drop_defers_instead_of_burning_the_futility_cap` |
| When fuzz re-probes, or what clears the clean bit | `_fuzz_sweep` and the `_fuzz_clean.clear()` calls in `_experiment_step` / `_property_step` | `tests/test_experiment.py::test_fuzz_sweep_is_not_rationed_behind_llm_slots` |
| Experiment / property design cadence | `_experiment_step`, `_property_step`; `Config.GEN_PROPOSE_PERIOD`, `GEN_MAX`, `PROP_PROPOSE_PERIOD`, `PROP_MAX` | `tests/test_v6_scheduler_model_phase_deferral.py::test_v6_experiment_and_property_design_defer_before_provider` |
| Capability dispatch order, or recovery of a dispatched item | `_simulation_capability_step`, `_v6_simulation_result_follow_up` | `tests/test_simulation_capability_v5.py::test_conjecture_records_only_proposal_and_scheduler_executes_later`, `::test_dispatched_crash_recovers_as_unknown_without_silent_rerun` |
| Foreign-school criticism coverage, receipts, or coverage debt | `_foreign_arg_crit`, `_foreign_criticism_coverage`; manifest `criticism_policy` | `tests/test_foreign_school_criticism_scheduler_c3.py` |
| Research cadence, backoff, or the agent-mode waiting state | `_research_step`, `_log_research_failure`; `Config.RESEARCH_PERIOD`, `RESEARCH_COOLDOWN`, `RESEARCH_ATTEMPTS_MAX` | `tests/test_research.py::test_backend_exception_is_caught_logged_and_cooled_down`, `::test_agent_mode_waits_and_never_claims_research_off` |
| What ends a run, and what the stop record contains | the stop block in `run`, `_stop_metrics`, `_record_stop` | `tests/test_workflow_stop_lifecycle_c4.py::test_v4_stop_is_a_replayable_control_event_bound_to_run_stop` |
| Add a response-ladder intervention | `activate_interventions` + a derived property, and `capture/ladder.respond` | `tests/test_diversity.py::test_stagnation_ladder_switches_on_spec_injection` |
| A legacy model phase v6 cannot yet dispatch (argumentative criticism is the one exception, fixed 2026-08-10 — it self-dispatches through `crit_argumentative_batch` instead of deferring; see `SEAM-rules-x-workflow`'s Traps) | `_defer_untransactional_v6_phase` at the phase's call site | `tests/test_v6_scheduler_model_phase_deferral.py::test_v6_deferral_marker_is_durable_bounded_and_resume_deduplicated` |
| Config-referee cadence | `_maybe_config_referee`; manifest `inquiry_capability_policy.config_referee` | `tests/test_config_referee.py::test_scheduler_fires_referee_only_on_the_frozen_cadence`, `::test_scheduler_absorbs_budget_denied_referee` |
| What `report()` returns / the Pareto frontier axes | `report`; `Config.PARETO_AXES` and `capture/pareto.frontier` | `tests/test_scheduler.py::test_multi_cycle_spawns_and_persistence` |
| What each survivor scores on an axis, or whether an axis is scored for it at all | `pareto_scores` — omit the key for an axis the harness did not measure; NEVER emit a floor value a commitment-free artifact can reach, which weights rank on conjecture kind (`DR-CON-conjecture-kinds`, R-g) | `tests/test_formalism_optional_rank.py::test_architecture_axes_that_must_not_be_zeroed_are_omitted_instead` |

Every Test cell above is a node id this check runs by name, so renaming a test
breaks the row instead of silently passing under a whole-file run; every Edit
cell names a symbol the check greps for.
`check: python -m pytest tests/test_scheduler.py::test_focus_family_restricts_selection tests/test_scheduler.py::test_integration_budget_share_caps_connection_work tests/test_scheduler.py::test_multi_cycle_spawns_and_persistence tests/test_rotation.py::test_attempt_cap_frees_the_rotation tests/test_rotation.py::test_transport_drop_defers_instead_of_burning_the_futility_cap tests/test_controller.py::test_operator_question_outranks_spawns_at_cycle_zero tests/test_reflexive_discipline.py::test_reflexive_budget_follows_lineage tests/test_budget.py::test_arg_crit_per_cycle_cap tests/test_properties.py::test_standing_recrit_pool_includes_active_properties tests/test_experiment.py::test_fuzz_sweep_is_not_rationed_behind_llm_slots tests/test_diversity.py::test_stagnation_ladder_switches_on_spec_injection tests/test_formalism_optional_rank.py::test_architecture_axes_that_must_not_be_zeroed_are_omitted_instead -q`
`check: python -m pytest tests/test_v6_scheduler_model_phase_deferral.py::test_v6_experiment_and_property_design_defer_before_provider tests/test_v6_scheduler_model_phase_deferral.py::test_v6_deferral_marker_is_durable_bounded_and_resume_deduplicated tests/test_workflow_stop_lifecycle_c4.py::test_v4_stop_is_a_replayable_control_event_bound_to_run_stop tests/test_foreign_school_criticism_scheduler_c3.py tests/test_config_referee.py::test_scheduler_fires_referee_only_on_the_frozen_cadence tests/test_config_referee.py::test_scheduler_absorbs_budget_denied_referee tests/test_simulation_capability_v5.py::test_conjecture_records_only_proposal_and_scheduler_executes_later tests/test_simulation_capability_v5.py::test_dispatched_crash_recovers_as_unknown_without_silent_rerun tests/test_research.py::test_backend_exception_is_caught_logged_and_cooled_down tests/test_research.py::test_agent_mode_waits_and_never_claims_research_off -q`
`check: for c in LIVENESS_QUEUE FOCUS_PROBLEM FOCUS_FAMILY INTEGRATION_BUDGET_SHARE ARG_CRIT_PER_CYCLE CRIT_BATCH_K RECRIT_STANDING DISC_ATTEMPTS_MAX DISC_COOLDOWN GEN_PROPOSE_PERIOD GEN_MAX PROP_PROPOSE_PERIOD PROP_MAX RESEARCH_PERIOD RESEARCH_COOLDOWN RESEARCH_ATTEMPTS_MAX PARETO_AXES CAPTURE_W; do grep -qE "^    $c:" src/deepreason/config.py || exit 1; done && for m in _disc_paused _standing_recrit_pool _foreign_criticism_coverage _v6_simulation_result_follow_up _log_research_failure _stop_metrics _defer_untransactional_v6_phase; do grep -q "^    def $m(" src/deepreason/scheduler/scheduler.py || exit 1; done && grep -q "^def pareto_scores(" src/deepreason/scheduler/scheduler.py && grep -q "^_REFLEXIVE_TRIGGERS = (" src/deepreason/scheduler/scheduler.py && grep -q "^def respond(" src/deepreason/capture/ladder.py && grep -q "config_referee" src/deepreason/run_manifest.py`

## Traps

- **A rule repeated at two dispatch sites is a rule at one of them, and the
  other one killed a run.** `Scheduler.step` produced its conjecture context
  plan from TWO independent expressions: the primary dispatch planned it and
  then, under v6, nulled it (`context_plan = None`) because controller-v3
  appends durable preparation before its pure planners and `rules/conj.py:827`
  raises `v6 conjecture context must be planned after durable work preparation`
  on a pre-made plan. The `ConjectureContextStale` handler sixty lines below
  re-planned with a second expression that carried no v6 rule, so a v6 run
  whose context went stale retried with exactly what Conj refuses. `ValueError`
  is caught by none of the handlers around the dispatch, so it propagated and
  terminalized the run. By construction that retry is the ONLY path on which a
  v6 run can reach the raise. Latent in every v6 run that authors scratch
  material — `ConjectureContextStale` is raised from three sites, all in
  `scratch/conjecture.py`, so the retry is reachable only when the scratchpad
  is live enough to build a context that can go stale; the trigger is
  stochastic, not configuration-specific. Live evidence, two roots: P-A2 epoch
  3, run `63e48f57415d05323b608a84f138ee5c22c274d7d8ebccc2e219b613d7c3a722`
  (`experiments/2026-09-02-live-p-a2-corrected/FINDINGS.md` F7 — `failed` /
  `operational_failure` at cycle 0, `verify_root` 0 violations, last provider
  call `valid=True`: the model succeeded and the harness refused its own next
  step); and episode-config arm A, root
  `run-cd878ff440f61294de34bea1fd45f8ad` (run id
  `ddd04beda27574b911d439cb95aadc40328d9a7a4276a39dd7aef8a53d4c6f90`, cycle 0,
  71 323 tokens, `TERMINAL_LIFECYCLE_NOT_TAKEN_FAILURE_TERMINAL`) — of three
  arms on the same question only A authored scratch, and only A died. FIXED
  2026-09-03 (`experiments/2026-09-03-defect-v6-context-retry-main/`; the fix
  originates at `06b0d9fd9` on branch `claude/model-profile-registry-opkgal`):
  `_dispatch_conjecture_context_plan` is the ONE owner of a dispatch-time
  context plan and both sites call it, so there is nowhere left to drift — and
  its v6 branch SKIPS the planner rather than discarding its result, so a v6
  retry no longer spends work building a plan that will be refused. The
  enduring rule is the structural half: a behaviour test alone passes happily
  while a second call site bypasses the rule, which is why the regression binds
  the call graph by AST — the method name occurs in this module's own prose and
  a string search would score a comment as a call site.
`check: python -m pytest tests/test_scheduler_v6_context_plan_retry.py -q`

- **A gate that reads only `schema_version` cannot be opened by any
  configuration, and eleven phases died on that line.**
  `_defer_untransactional_v6_phase` (`scheduler.py:696`) computed its whole
  answer from `manifest.schema_version != 6`, returning True for every v6
  manifest before reading any other value — no grant, no route, no lease, no
  `Config` field. It was correct when written: v6 makes the adapter fail closed
  on any unbound provider dispatch, so typed completion debt beats a killed
  root. Operations parity (2026-08-13) then made v6 the only path a current run
  takes, which turned the `!= 6` escape into dead code and the safety net into a
  permanent lock. The eleven phases — `hv-floor`, `hv-spot-check`,
  `rubric-trial`, `pairwise-discrimination`, `premise-demarcation-variation`,
  `paraphrase-audit-variation`, `paraphrase-audit-judgment`,
  `experiment-generator-authoring`, `property-design`,
  `property-relevance-trial`, `vision-criticism` — kept their run-config knobs
  (`HV_K`, `HV_MIN`, `AUDIT_PERIOD`, `GEN_*`, `PROP_*`, `VISION_CRIT_PER_CYCLE`,
  `ADVISORY_TRIALS_PER_CYCLE`), which parsed, compiled and appeared live over
  phases that could not fire. Measured across 50 committed v6 roots: **2 661
  `hv` deferral records, 0 `hv_set` measurements**, including 336 deferrals on
  grounded-extension run `8e22d0431fd2b98d`
  (`experiments/2026-08-12-live-grounded-extension-expansion/run`), which
  completed cleanly with `variator[0]` holding `variator.direct.v1` — the exact
  grant the gate stands in for. FIXED 2026-09-02
  (`experiments/2026-09-02-defect-hv-v6-reachability/`): the gate consults
  `workflow/legacy_phase_contracts.py`, a declared VERSIONED table of
  phase → (role, authorizing contracts, dispatch). Three traps inside the trap.
  First, **a deferral RECORD is not a deferral CALL** — the marker is
  deduplicated by the `(phase, role, target_ref, obligation_ref)` tuple, so
  every count above under-states the calls and the true rate is unrecoverable
  from the record. Second, **opening the gate on the grant alone would be worse
  than the defect**: nine rows still have no dispatch written, and letting them
  through would send them to a provider unbound and trip the fail-closed guard
  the gate exists to respect — so the row's `dispatch` field, not the presence
  of a grant, is what converts a phase, and `REC-give-a-legacy-phase-v6-
  transactional-dispatch.md` is the one-phase-per-tranche path. `hv-spot-check`
  and `hv-floor` are the two converted, and `hv-floor` only on an OPERATOR
  RULING, because it mints a fail warrant and therefore decides status. Third,
  `premise-rent` is a `target_ref`, not a phase: both the 2026-09-01 P-A1
  write-up and this tranche's own instruction listed twelve phase names against
  eleven call sites on that misreading, and the record's own six-element
  `inputs` tuple settles the slot.
`check: python -m pytest tests/test_hv_v6_reachability.py -q`
`check: python -c "
import ast, pathlib
tree = ast.parse(pathlib.Path('src/deepreason/scheduler/scheduler.py').read_text())
calls = [n for n in ast.walk(tree) if isinstance(n, ast.Call)
         and isinstance(n.func, ast.Attribute)
         and n.func.attr == '_defer_untransactional_v6_phase']
from deepreason.workflow.legacy_phase_contracts import LEGACY_PHASE_CONTRACTS
assert len(calls) == 11, len(calls)
assert {c.args[0].value for c in calls} == set(LEGACY_PHASE_CONTRACTS)
assert {(c.args[0].value, c.args[1].value) for c in calls} == {
    (r.phase, r.role) for r in LEGACY_PHASE_CONTRACTS.values()
}
"`


- **A Pareto axis whose floor is reachable by carrying no commitment ranks on
  conjecture KIND, and `run_report` did exactly that for four months.**
  `coverage = passes/evaluable if evaluable else 0.0` gave an artifact with
  NOTHING to check the same coordinate as one that was checked and failed
  everything; `frontier` maximises every axis, so a formally-backed sibling
  dominated an otherwise-identical prose one and it left the published answer.
  On grounded-extension run
  `experiments/2026-08-12-live-grounded-extension-expansion/run` that was 146
  of 233 survivors — the frontier was exactly the 87 that carried a battery,
  and not one of the 146 survived it. Found by the 2026-08-27 audit (finding
  F1, its one UNLAWFUL-PENALTY row); the law is CLAUDE.md's formalism-optional
  design law and `DUAL_MODE_CONJECTURE_PREPLAN.md` R-g. FIXED 2026-08-30
  (`experiments/2026-08-30-defect-formalism-rank-penalty/`): `pareto_scores`
  OMITS an axis it did not measure and `frontier` drops an absent axis from
  that pairwise comparison. Two traps inside the trap. First, the repair is
  not "put everyone on the frontier": an artifact that WAS checked and failed
  must still be dominated by one that passed, or the axis has been destroyed
  rather than fixed — `test_control_b_a_failed_battery_is_still_dominated`
  exists to catch that. Second, `hv` and `reach` still emit 0.0 for an
  unmeasured artifact and therefore still carry this shape; the 2026-08-27
  audit rowed them STRUCTURAL-GAP rather than unlawful and neither is
  reachable as a penalty in any committed root, but do not read the coverage
  repair as having closed the class. `hv` became REACHABLE on 2026-09-02 (the
  Traps entry above), so a run may now carry a measured `hv` for some artifacts
  and an absent one for others — the shape `pareto_scores` was taught to handle
  by omitting an axis it did not measure, and the case worth re-reading that
  repair for.
`check: python -m pytest tests/test_formalism_optional_rank.py -q`
- **The class was NOT closed, and the third instalment cost three live roots:
  the axis charged an artifact for every falsifiable claim it made.** The entry
  above repaired the axis when the battery is EMPTY. It said nothing about a
  battery that is full and UNDECIDABLE, and that is where the next penalty
  lived: `coverage` counted `programs.OVERRUN` in its denominator as a
  non-pass, and OVERRUN is the verdict for "the harness obtained no verdict".
  An observation-valued countercondition returns it unconditionally
  (`programs.py::_reasoning_observation_pending`), so declaring a testable
  claim LOWERED your own rank until evidence arrived. Measured on three
  committed roots — P-S1 `9e48a36b1dec91ee` (98 survivors, 58 on the
  frontier), P-A1 `4565139800f5ca02` (11, 7), and the poietics run P-R1
  `experiments/2026-08-25-poietics-program/run` (58, 40) — the split was
  TOTAL on every one: every frontier member answered a harness-minted
  `connection` problem and every dominated artifact answered the operator's
  seed question. No commitment FAILED anywhere across all 156 survivors, so the
  axis carried no quality signal at all; its whole variance was the count of
  declared counterconditions, and the seed answers passed twice as many checks
  (4 vs 2) as the artifacts that dominated them. FIXED 2026-09-02
  (`experiments/2026-09-02-defect-coverage-pending-commitments/`): an OVERRUN
  verdict leaves the denominator, exactly as an unmeasured axis leaves the
  pairwise comparison. Three enduring lessons. First, the defect is FIVE
  program families wide, not one — the four `lean_*` programs also return
  OVERRUN pending their external verifier, so a formally-backed conjecture was
  being penalised FOR being formal, R-g's protection running backwards.
  Second, the reason the gate was green for four months is that
  `test_formalism_optional_rank.py` built its pending commitment as
  `eval="observation"`, which `programs.evaluable` screens out, while
  `workloads/text.py` rewrites every live declaration into
  `program:reasoning_observation_pending`, which it does not: **a regression
  test that constructs its own fixture can pin a shape the harness rewrites
  away before any artifact carries it.** Third, this is why the seam matters:
  the pair scores 11 on `INDEX.md`'s own metric — enough for a row, tying
  `harness x workflow` — and had none; and the ranking crossing itself is a
  TWELFTH the metric cannot count at all, because `pareto_scores` reaches the
  evaluation side by importing the PACKAGE (`from deepreason import programs`)
  inside a function body, which a `deepreason.<module>` census misses twice
  over. `DR-SEAM-evaluation-x-scheduler` now exists.
`check: python -m pytest tests/test_coverage_pending_commitments.py -q`
- **The steering controller was attached to every run and could move nothing on
  any of them.** `ops.run_scheduler` builds `Controller(harness, adapter)`
  whenever `config.CONTROLLER` is true, and `Scheduler` steps it once per cycle,
  so every check anyone had written — "is it wired?" — passed. The barrier it
  steers WITHIN was the defect: a static table naming six roles with a widest
  ceiling of 5,000, against a compiled v6 manifest that binds eleven roles and
  pins `max_tokens=16384` on every one. Both guards in `_propose` (no envelope
  for the role; current cap outside the envelope) then skipped in silence and
  `step()` returned `None` forever. Grounded-extension run `8e22d0431fd2b98d`
  recorded 12,991 events with zero steering artifacts while `judge` — whose
  largest completion in 342 calls was 141 tokens — stayed pinned at 16,384
  throughout. Two traps inside the trap: that root's 3,380 `rule="Control"`
  events are `control.event.v3` WORKFLOW TRANSACTIONS, not steering, and
  `cap:conjecturer`'s static ceiling of 5,000 sits BELOW that run's median
  conjecturer completion of 4,968 — so "move the cap into the static envelope"
  is not the fix, it pins the seat where half its calls truncate and the widen
  path clamps back to the same number. FIXED 2026-08-13
  (`experiments/2026-08-13-defect-controller-steering-inert/`): barriers are
  derived per run by `cap_envelope(knob, configured_cap)`, anchored so a SEAT
  INSTANCE's assigned cap may only WIDEN the barrier. The clause that used to
  follow — "and the controller can never move a cap past the operator's own
  setting" — was FALSE as written and is corrected here rather than deleted:
  because the anchor only widens, a seat assigned a cap BELOW the static
  ceiling (e.g. 3000 against `cap:conjecturer`'s 5000) kept a barrier wider
  than its own route, and a truncation signal could widen it past the assigned
  limit. True since 2026-08-22
  (`experiments/2026-08-22-fix-route-lease-maxtokens/`) and only for seats whose
  route declares `context_window_tokens`, where `Controller._lease_ceiling`
  bounds the proposal at the lease; an unqualified seat still widens past its
  configured cap by design. Coverage is derived rather
  than enumerated, so a twelfth role cannot silently reintroduce this.
  SEAT INSTANCE, not role, since 2026-08-21 (Rung 1b-ii): a role bound to ONE
  seat keeps the bare role name — which is why nothing in a committed root is
  re-spelled and all 26 tests here passed unchanged — while a role bound to
  several gets `cap:<role>#<seat>` per seat, so two structurally asymmetric
  seats filled by one conjecturer throttle independently instead of sharing one
  knob. `_apply_cap` writes that seat's endpoint alone; writing the role's whole
  ensemble is what made them one throttle.
`check: grep -q "^def cap_envelope" src/deepreason/controller.py && grep -q "^def is_generator_knob" src/deepreason/controller.py && python -m pytest tests/test_controller_steering_parity.py::test_every_manifest_bound_role_gets_a_barrier_containing_its_cap tests/test_controller_steering_parity.py::test_the_grounded_configuration_steers_instead_of_sitting_inert tests/test_controller.py::test_controller_does_not_normalize_an_explicit_cap_outside_its_envelope -q`
- **The envelope bounds the proposal; it does not bound the consumer.** A
  decision inside its barrier, past its dwell, and logged as a policy artifact
  can still be refused at the point of use. Reach-rich epoch 2 (run
  `40e713b3…`, `log.jsonl` seq 442 then 577) settled the conjecturer seat from
  its leased 32768 to 20480 after three spotless windows — lawful on every axis
  the controller answers to — and the route firewall, which bound `max_tokens`
  for equality on any route declaring `context_window_tokens`, refused the next
  dispatch and ended the run at cycle 2 of 24 with
  `stop_reason=operational_failure`. Nothing in the map connected the two
  sides; nothing in the import graph could, since `controller.py` imports no
  `deepreason.llm` and reaches the leases duck-typed through
  `self.adapter.leases`. FIXED 2026-08-22
  (`experiments/2026-08-22-fix-route-lease-maxtokens/`): the firewall binds a
  qualified route's cap as a ceiling, the controller never proposes above that
  ceiling, and the agreement is written up at `DR-SEAM-llm-x-scheduler`. When
  adding or widening a controller knob, the question the envelope does not
  answer is what refuses the value downstream.
`check: python -m pytest tests/test_route_lease_maxtokens_tuning.py -q && test -f docs/map/SEAM-llm-x-scheduler.md`
- **A role the controller cannot steer must be named, not skipped.** Silence was
  the whole reason the defect above survived two live epochs: an inert
  controller and a healthy one wrote the same thing — nothing. `step()` now
  appends one `controller-authority` Measure record stating `full`/`partial`/
  `none`, the steerable SEAT INSTANCES, and every unsteerable one with a typed
  reason, episode-deduplicated the way `research-awaiting-agent` is (re-emitted
  only when the authority set changes, never once per cycle). A seat-assigned
  limit is OPTIONAL — a manifest may bind a role with no `max_tokens` at all,
  which is a configuration and not a fault; the controller does not invent a
  limit the operator declined to assign, it records `no-assigned-limit`.
  The same record carries `open_loop` since 2026-08-21: the policy-referenced
  signals this TOPOLOGY cannot produce at all. Silence was the defect shape
  once; a controller whose fail-static branch can never fire, because no seat
  bound to the run can attack a policy, must not be silent about that either.
`check: grep -q "controller-authority" src/deepreason/controller.py && python -m pytest tests/test_controller_steering_parity.py::test_a_controller_with_nothing_to_steer_records_that_it_has_nothing tests/test_controller_steering_parity.py::test_partial_authority_names_which_roles_are_out_of_reach tests/test_controller_steering_parity.py::test_the_authority_record_is_episode_deduplicated -q`
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
  bleeds backward. **The first of those two rules then held only where it was
  patched.** It was spelled out in `_select_problem` and nowhere else, so
  `run_report` — the writer of every root's published survivor set, two hundred
  lines up in the SAME FILE — kept counting import-role records, and
  `run-1b31f006` (poietics P-R1, the first run here to bind a non-empty dossier
  at seed) published **82 survivors of which 24 were IMPORT-role sections of
  the operator's own record**, each registered at log seq 5-40 against a log
  whose first LLM-bearing event is seq 85. `deepreason results` reported all 82
  as "positions still standing at the end". The check below used to grep this
  file for the literal, which cannot distinguish one site that has the clause
  from another that does not. FIXED 2026-08-25: the rule moved to
  `ontology/state.py::counts_as_survivor`, every survivor surface calls it, and
  no consumer may re-spell it
  (`experiments/2026-08-25-fix-import-role-survivors/`).
`check: python -c "
import inspect, pathlib
from deepreason.scheduler.scheduler import Scheduler, run_report
for site in (Scheduler._select_problem, run_report):
    assert 'counts_as_survivor' in inspect.getsource(site), site
assert 'ProvenanceRole.IMPORT' not in pathlib.Path(inspect.getfile(Scheduler)).read_text()
" && python -m pytest tests/test_controller.py::test_operator_question_outranks_spawns_at_cycle_zero tests/test_scheduler.py::test_focus_family_restricts_selection tests/test_import_role_survivors.py -q`
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
`check: grep -q "marker = \"v6-model-phase-deferred.v1\"" src/deepreason/scheduler/scheduler.py && grep -q "v6-model-phase-deferred.v1" src/deepreason/verification/report.py && python -c "from deepreason.signals import is_known; assert is_known('cycle'), 'registry lookup is broken - this check proved nothing'; assert not is_known('v6-model-phase-deferred.v1'), 'marker is now registered: delete this trap'"`
