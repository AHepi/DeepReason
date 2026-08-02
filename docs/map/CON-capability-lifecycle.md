<!-- DR-CON-capability-lifecycle -->
Verified-at: 08dcdf3c
Verify: python tools/docs_verify.py
Owns: src/deepreason/capabilities/enums.py, src/deepreason/capabilities/events.py, src/deepreason/capabilities/models.py, src/deepreason/capabilities/policy.py, src/deepreason/capabilities/state.py, src/deepreason/capabilities/simulation.py, src/deepreason/capabilities/research.py, src/deepreason/capabilities/audit.py
Seams: 
Seams-undocumented: capabilities x harness, capabilities x llm, capabilities x rules, capabilities x scheduler, capabilities x verification, capabilities x workflow

# The capability lifecycle — proposal, admission, work order, result

## What it is

A capability is the only way the run reaches outside its own reasoning: it runs
a program, or it fetches a document. The model may express *semantic intent*
and nothing else; every operational parameter — toolchain, runner profile,
wall-clock and memory bounds, domain allowlist, request ceiling — is code- or
manifest-authored. Intent becomes action by walking a ten-state lifecycle
(`PROPOSED → VALIDATED → GRANTED|DENIED → COMPILED → DISPATCHED →
SUCCEEDED|FAILED → RESULT_PACKAGED → CONSUMED`), one typed, chained, digest-linked
transition per step, so that a run's entire outside contact re-derives from the
append-only log. Two capabilities exist — simulation and research — and they
share the state machine, the transition record, the event envelope and the
replay validator, while differing in almost everything else: their budgets,
their controllers, and *where in the cycle they execute*. That sharing is the
navigational hazard: the replayed state keeps ONE set of maps for BOTH, so every
count, every budget and every report must discriminate by record type.

## Where it lives

| Aspect | File | Symbol |
|---|---|---|
| The ten-state vocabulary | `src/deepreason/capabilities/enums.py` | `CapabilityLifecycle` |
| Legal predecessor of each state | `src/deepreason/capabilities/state.py` | `_ALLOWED_PREVIOUS` |
| Which record type each state may carry | `src/deepreason/capabilities/state.py` | `_PHASE_MODELS`, `_RESEARCH_PHASE_MODELS` |
| The replayed state (nine pooled maps) | `src/deepreason/capabilities/state.py` | `CapabilityReplayState.proposals / grants / compiled / work_orders / receipts / result_packages / consumptions / transitions / current_transition_by_request` |
| Content address over that state | `src/deepreason/capabilities/state.py` | `CapabilityReplayState.digest` (FROZEN) |
| The single replay validator | `src/deepreason/capabilities/state.py` | `CapabilityReplayState.apply` (FROZEN) |
| Chained per-step process digest | `src/deepreason/capabilities/models.py` | `capability_next_process_digest`, `CapabilityBudgetDeltaV1` |
| The transition record itself | `src/deepreason/capabilities/models.py` | `CapabilityTransitionV1` |
| Simulation phase records | `src/deepreason/capabilities/models.py` | `SimulationProposalV1`, `SimulationGrantV1`, `CompiledSimulationV1`, `SimulationWorkOrderV1`, `SimulationExecutionReceiptV1`, `SimulationResultPackageV1`, `SimulationConsumptionV1` |
| Research phase records | `src/deepreason/capabilities/models.py` | `ResearchFetchProposalV1`, `ResearchGrantV1`, `CompiledResearchFetchV1`, `ResearchWorkOrderV1`, `ResearchExecutionReceiptV1`, `ResearchResultPackageV1`, `ResearchConsumptionV1` |
| Event envelope on the log | `src/deepreason/capabilities/events.py` | `CapabilityEventPayloadV1` |
| Frozen budgets and runner identity | `src/deepreason/capabilities/policy.py` | `SimulationCapabilityPolicyV1`, `ResearchCapabilityPolicyV1`, `InquiryCapabilityPolicyV1` |
| Write path + schema/model binding | `src/deepreason/harness.py` | `Harness.record_capability_transition` |
| Replay application point | `src/deepreason/harness.py` | `Harness._apply_event` → `capability_state.apply` |
| Simulation controller | `src/deepreason/capabilities/simulation.py` | `SimulationCapabilityController._transition`, `.propose`, `.stage_transactional_proposals`, `.execute`, `.recover_interrupted`, `.consume`, `.accounting` |
| Research controller | `src/deepreason/capabilities/research.py` | `ResearchCapabilityController._transition`, `.propose`, `.stage_transactional_proposals`, `.execute`, `.consume`, `._requests_already_used`, `._sources_already_consumed` |
| Replay-derived research allowance | `src/deepreason/capabilities/research.py` | `dynamic_research_allowance`, `MAXIMUM_PROPOSALS_PER_TURN` |
| Fetched text → citable blocks | `src/deepreason/capabilities/research.py` | `blocks_for_fetched_text`, `consumed_research_blocks` |
| Model-facing proposal wire | `src/deepreason/llm/wire.py` | `SimulationProposalWireV1`, `ResearchFetchProposalWireV1`, `TURN_OUTCOME_SHAPE`, `ConjecturerTurnWireV6.research_proposals` |
| Conjecture-turn staging and materialization | `src/deepreason/rules/conj.py` | `_v6_capability_effect_refs`, `_v6_simulation_effect_refs`, `_v6_research_effect_refs` (and the `simulation_drafts` / `research_drafts` blocks) |
| Filed-proposal view in criticism packs | `src/deepreason/rules/crit.py` | `_filed_simulations` |
| Scheduler capability phase | `src/deepreason/scheduler/scheduler.py` | `Scheduler._simulation_capability_step`, `Scheduler._v6_simulation_result_follow_up` |
| Replay validation of the whole lifecycle | `src/deepreason/invariants.py` | `verify_root` — the `capability-replay`, `capability-budget`, `capability-origin`, `capability-work-order`, `capability-receipt`, `capability-consumption` checks |
| Post-run audits and roll-up | `src/deepreason/capabilities/audit.py`, `src/deepreason/findings.py` | `write_tranche_a_audits`, `_transition_chains`, `findings_summary` |

## The rules it obeys

**Ten states, and the predecessor set is closed.** `PROPOSED` may have no
predecessor; `DENIED` may follow only `VALIDATED`; nothing may follow `DENIED`
or `CONSUMED` — both are terminal.
`check: python -c "from deepreason.capabilities.state import _ALLOWED_PREVIOUS as A; from deepreason.capabilities.enums import CapabilityLifecycle as L; assert set(A) == set(L) and len(L) == 10; assert A[L.PROPOSED] == set() and A[L.DENIED] == {L.VALIDATED}; assert not any(L.DENIED in p or L.CONSUMED in p for p in A.values())"`

**`VALIDATED` and `DENIED` are the only states that carry no phase record**;
each of the other eight has exactly one simulation model and one research model.
The rule is enforced twice — on write and on replay — and in both directions: a
phase record on a bare transition is refused, and a bare transition where one is
required is refused.
`check: python -c "from deepreason.capabilities.state import _PHASE_MODELS as P, _RESEARCH_PHASE_MODELS as R; from deepreason.capabilities.enums import CapabilityLifecycle as L; assert set(L) - set(P) == {L.VALIDATED, L.DENIED}; assert all(len(v) == 2 and v[0] not in R and v[1] in R for v in P.values())"`
`check: grep -q 'this capability transition cannot carry a phase record' src/deepreason/capabilities/state.py && grep -q 'capability phase record has the wrong type' src/deepreason/capabilities/state.py && grep -q 'this capability transition cannot carry a phase record' src/deepreason/harness.py && grep -q 'capability transition requires its phase record' src/deepreason/harness.py`

**A chain never mixes kinds.** One proposal's chain is simulation-shaped or
research-shaped for its whole life, decided by the type of the `PROPOSED` record.
`check: grep -q 'capability chain cannot mix simulation and research records' src/deepreason/capabilities/state.py`

**There is ONE process-digest chain for the whole run, not one per proposal.**
Every transition's `previous_process_digest` must equal the state's current
digest, and the state advances to its `next_process_digest`; concurrent
proposals therefore interleave on a single hash chain. The step digest binds the
lifecycle value and the budget delta, so neither can be restated after the fact.
`check: grep -q 'transition.previous_process_digest != self.process_digest' src/deepreason/capabilities/state.py`
`check: python -c "from deepreason.capabilities.models import capability_next_process_digest as f, CapabilityBudgetDeltaV1 as B; from deepreason.capabilities.enums import CapabilityLifecycle as L; k = dict(previous_process_digest='sha256:'+'0'*64, request_ref='sha256:'+'1'*64, request_digest='sha256:'+'1'*64, previous_transition_ref=None, phase_record_ref=None, trigger_ref='provider-call:1'); assert f(lifecycle=L.PROPOSED, budget_delta=B(), **k) != f(lifecycle=L.VALIDATED, budget_delta=B(), **k) != f(lifecycle=L.VALIDATED, budget_delta=B(requests=1), **k)"`

**The state digest covers the consumed event sequence, not only the maps**, and
is deterministic across instances — that is what lets `verify_root` replay a log
twice and compare.
`check: python -c "from deepreason.capabilities.state import CapabilityReplayState as S; a, b = S(), S(); b.event_seqs.append(1); assert a.digest == S().digest != b.digest"`
`check: grep -q 'capability-replay", "two replays produced different capability state"' src/deepreason/invariants.py`

**Authority is frozen inside a chain.** Manifest digest, capability-policy
digest, originating work order, problem ref, request digest, run-input digest
and both fence seqs are compared against the previous transition on every step.
A fixture that mutates any of them mid-chain is rejected as malformed, not
merely as wrong.
`check: grep -q 'capability transition changed frozen authority' src/deepreason/capabilities/state.py`

**Admission may only narrow.** A research grant may never widen the proposed
URL set; a result package may be consumed at most once — that one is enforced
separately for each kind. Content attestation is NOT symmetric: `apply` checks
that every item in a `ResearchResultPackageV1` was actually FETCHED by its
receipt, while the `SimulationResultPackageV1` branch validates only
`proposal_ref` and `run_input_digest` and never reads `receipt_ref` at all.
`check: grep -q 'research grant widens the proposed urls' src/deepreason/capabilities/state.py && grep -q 'research package carries unreceipted content' src/deepreason/capabilities/state.py && test "$(grep -c 'was consumed more than once' src/deepreason/capabilities/state.py)" = 2`
`check: python -c "import inspect; from deepreason.capabilities.state import CapabilityReplayState as S; s = inspect.getsource(S.apply); sim = s.split('elif isinstance(phase_record, SimulationResultPackageV1):')[1].split('elif isinstance')[0]; assert 'research package carries unreceipted content' in s; assert 'receipt' not in sim"`

**The event envelope pins the record to its request.** Input one must be the
proposal; the last output must be the transition; outputs must be canonical IDs
and must not repeat.
`check: grep -q 'capability event input one must name its proposal' src/deepreason/capabilities/events.py && grep -q 'capability transition must be the final event output' src/deepreason/capabilities/events.py && grep -q 'capability outputs must be canonical record IDs' src/deepreason/capabilities/events.py && grep -q 'capability outputs must not repeat' src/deepreason/capabilities/events.py`

**The model authors intent only.** The proposal wire carries hypothesis, purpose,
observables, aliases and URLs — never a runner profile, toolchain, resource
bound, request limit or allowlist. A research proposal is three fields.
`check: python -c "from deepreason.llm.wire import SimulationProposalWireV1 as S, ResearchFetchProposalWireV1 as R; ops = {'runner_profile','toolchain_identity','backend_identity','maximum_wall_ms','maximum_memory_bytes','maximum_steps','maximum_samples','maximum_output_bytes','requests_limit','domain_allowlist','maximum_response_bytes'}; assert not ops & set(S.model_fields) and not ops & set(R.model_fields); assert set(R.model_fields) == {'purpose','request_identifier','urls'}"`

### The per-capability budget rule

**A budget meters ONLY its own capability's records — but the state maps pool
ALL capabilities' records, so every count must filter by type.** The simulation
request and execution gates rank the proposal among `SimulationProposalV1`s and
count `SimulationWorkOrderV1`s; the research gates read
`ResearchExecutionReceiptV1.requests_used_total` and
`ResearchConsumptionV1.evidence_refs`. Neither can see the other's spend.
`check: python -c "import inspect; from deepreason.capabilities.simulation import SimulationCapabilityController as C; s = inspect.getsource(C.execute); assert 'isinstance(item, SimulationProposalV1)' in s and 'isinstance(order, SimulationWorkOrderV1)' in s"`
`check: python -c "import inspect; from deepreason.capabilities.research import ResearchCapabilityController as C; assert 'isinstance(receipt, ResearchExecutionReceiptV1)' in inspect.getsource(C._requests_already_used) and 'isinstance(consumption, ResearchConsumptionV1)' in inspect.getsource(C._sources_already_consumed)"`
`check: python -m pytest tests/test_simulation_capability_v5.py::test_research_spend_does_not_exhaust_simulation_budgets -q`

**`verify_root` re-derives the same budgets with the same filters**, so a
recorded root is judged against per-capability totals rather than pooled ones.
`check: python -c "import inspect; from deepreason import invariants; s = inspect.getsource(invariants.verify_root); assert 'not isinstance(grant, ResearchGrantV1)' in s and 'isinstance(receipt, SimulationExecutionReceiptV1)' in s and 'not isinstance(consumption, ResearchConsumptionV1)' in s"`

**The research cap is authority; the allowance is tuning.**
`ResearchCapabilityPolicyV1.maximum_requests` is frozen in the manifest and
never moves; `dynamic_research_allowance` derives a grantable subset of it from
replayed state alone (uncited consumed sources, trailing refusal streak,
stagnation) and is clamped so it can never exceed the cap.
`check: python -c "import inspect; from deepreason.capabilities.research import dynamic_research_allowance as f; assert 'max(0, min(cap, cap - waste_penalty - streak_penalty))' in inspect.getsource(f)"`
`check: python -m pytest tests/test_research_capability.py -k "waste_tightening or stagnation_widens" -q`

**The research per-turn ceiling is a module constant, deliberately NOT a policy
field** — growing the policy schema would perturb frozen manifest digests
(DR-INV-frozen-surfaces surface 4) — and the wire's `max_length` is bound to the
same number. Simulation's per-turn ceiling *is* a policy field, because it was
frozen into v5 manifests before that constraint was understood.
`check: python -c "from deepreason.capabilities.research import MAXIMUM_PROPOSALS_PER_TURN as M; from deepreason.capabilities.policy import ResearchCapabilityPolicyV1 as R, SimulationCapabilityPolicyV1 as S; from deepreason.llm.wire import ConjecturerTurnWireV6 as W; assert M == 2 and 'maximum_proposals_per_turn' not in R.model_fields and 'maximum_proposals_per_turn' in S.model_fields; assert [m.max_length for m in W.model_fields['research_proposals'].metadata if hasattr(m, 'max_length')] == [M]"`

### Dispatch — and the asymmetry between the two capabilities

**Simulation executes in the scheduler; research executes inside the conjecture
turn.** A simulation proposal is *only* recorded by the conjecture rule; the
scheduler's capability phase runs before problem selection, executes or consumes
at most one item, and spends the whole cycle. A research grant completes within
the cycle that proposed it, so fetched material becomes citable before the next
turn's citation checks. The scheduler holds no research controller at all.
`check: grep -q 'if self._simulation_capability_step():' src/deepreason/scheduler/scheduler.py && grep -q 'isinstance(package, SimulationResultPackageV1)' src/deepreason/scheduler/scheduler.py && ! grep -q 'ResearchCapabilityController' src/deepreason/scheduler/scheduler.py`
`check: grep -q 'research_controller.execute(' src/deepreason/rules/conj.py && ! grep -q 'simulation_controller.execute(' src/deepreason/rules/conj.py`

**A denial is a durable typed transition, never an exception and never
silence.** Both controllers return `None` and write a `DENIED` transition whose
`reason_code` names the refusal (`request_budget_exhausted`,
`runner_unavailable`, `url_outside_frozen_allowlist`, `invalid_model_program`, …).
`check: python -m pytest tests/test_research_capability.py::test_off_allowlist_proposal_is_denied_without_dispatch tests/test_simulation_capability_v5.py::test_invalid_declarative_program_is_denied_without_dispatch -q`

**A durable `DISPATCHED` prefix is never silently re-run.** If the process dies
after the work order is committed and before a receipt is, recovery writes a
`dispatch_interrupted` receipt with `execution_observed: False` — an explicit
unknown, not a repeat execution.
`check: python -m pytest tests/test_simulation_capability_v5.py::test_dispatched_crash_recovers_as_unknown_without_silent_rerun -q`

## Where to change what

| To change... | Edit | Test |
|---|---|---|
| Add or reorder a lifecycle state | `capabilities/enums.py` `CapabilityLifecycle`, `state.py` `_ALLOWED_PREVIOUS` + `_PHASE_MODELS`, `harness.py` `record_capability_transition`'s schema map — FROZEN (DR-INV-frozen-surfaces surface 1); needs operator approval | `python -m pytest tests/test_simulation_capability_v5.py tests/test_research_capability.py -q` |
| Move a simulation budget | `capabilities/policy.py` `SimulationCapabilityPolicyV1`, and the gate in `simulation.py` `execute` — keep the `SimulationProposalV1` / `SimulationWorkOrderV1` filters | `python -m pytest tests/test_simulation_capability_v5.py -k budget -q` |
| Change what research may fetch | `capabilities/policy.py` `ResearchCapabilityPolicyV1.domain_allowlist`, `research/fetch.py` `WebResearchConfigV1.allows` | `python -m pytest tests/test_research_capability.py -k allowlist -q` |
| Retune how much of the research cap is grantable | `capabilities/research.py` `dynamic_research_allowance` only — never `maximum_requests`, which is manifest-frozen | `python -m pytest tests/test_research_capability.py -k "allowance or tighten or stagnation" -q` |
| Change when a simulation result re-enters reasoning | `scheduler/scheduler.py` `_simulation_capability_step` / `_v6_simulation_result_follow_up` | `python -m pytest tests/test_simulation_capability_v5.py -k scheduler_executes_later -q` |
| Change when fetched material becomes citable | `rules/conj.py` research materialization block, `capabilities/research.py` `consume` + `blocks_for_fetched_text` | `python -m pytest tests/test_research_capability.py -k citable -q` |
| Add a third capability | `capabilities/models.py` records, `state.py` `_PHASE_MODELS` + an `apply` branch, `harness.py` schema map, `llm/wire.py` `TURN_OUTCOME_SHAPE`, `rules/conj.py` staging + materialization — plus a type filter at EVERY site that counts a pooled map | `python -m pytest tests/test_research_capability.py tests/test_v6_insufficient_capability_reporting.py -q` |
| Change a post-run capability report | `capabilities/audit.py` `write_tranche_a_audits`, `findings.py` `findings_summary` | `python -m pytest tests/test_research_root_replay.py -q` |

## Traps

- **Counting a pooled map.** openchallenge `run-9e9812fe`: two consumed research
  fetches exhausted the *simulation* request and execution budgets before the
  first simulation proposal existed, and both typed simulation proposals were
  denied (`request_budget_exhausted`, `execution_budget_exhausted`) with zero
  simulations run. Fixed by filtering `execute`'s counts to `SimulationProposalV1`
  and `SimulationWorkOrderV1`. Regression:
  `tests/test_simulation_capability_v5.py::test_research_spend_does_not_exhaust_simulation_budgets`.
- **The same pooling still stands in two live places.**
  `SimulationCapabilityController.consume` gates on
  `CapabilityReplayState.consumption_count`, which is `len(self.consumptions)`
  over BOTH kinds, so a research consumption spends simulation follow-up budget;
  and `accounting()` reports `simulation_backend_attempts` by summing `attempts`
  across every receipt, while `ResearchExecutionReceiptV1` also has an `attempts`
  list. `verify_root`'s own budget check *does* filter, so a recorded root is
  judged on the per-capability count while the live gate uses the pooled one.
  Recorded as unfixed; do not assume symmetry with the `execute` gate.
`check: python -c "import inspect; from deepreason.capabilities.simulation import SimulationCapabilityController as C; from deepreason.capabilities.state import CapabilityReplayState as S; assert 'self.harness.capability_state.consumption_count' in inspect.getsource(C.consume); assert inspect.getsource(S.__dict__['consumption_count'].fget).strip().endswith('return len(self.consumptions)'); a = inspect.getsource(C.accounting); assert 'attempts = sum(len(receipt.attempts) for receipt in state.receipts.values())' in a and '\"simulation_backend_attempts\": attempts,' in a"`
- **Believing the dataclass annotations.** `CapabilityReplayState` annotates its
  maps as `dict[str, SimulationProposalV1]`, `dict[str, SimulationGrantV1]` and
  so on, yet `apply` stores `ResearchGrantV1` into `self.grants`,
  `ResearchExecutionReceiptV1` into `self.receipts`, and so on. The annotation is
  the historical shape, not the current contents; `isinstance` is the only
  reliable discriminator, which is why `_RESEARCH_PHASE_MODELS` exists.
`check: python -c "import typing; from deepreason.capabilities.state import CapabilityReplayState as S; h = typing.get_type_hints(S); assert 'SimulationGrantV1' in str(h['grants']) and 'SimulationProposalV1' in str(h['proposals'])" && grep -q 'elif isinstance(phase_record, ResearchGrantV1):' src/deepreason/capabilities/state.py`
- **Building two chains independently in a fixture.** The process digest chain is
  global, not per-proposal: a transition's `previous_process_digest` must equal
  whatever the state holds *at that moment*. Two proposals' chains constructed in
  isolation and then concatenated will fail replay with "capability event differs
  from its transition". Within one chain, manifest sha and both fence seqs are
  additionally frozen — a fixture that advances a fence mid-chain is malformed.
- **Reading a `None` return as a failure.** Both `execute` methods return `None`
  on denial. The typed `DENIED` transition and its `reason_code` are the
  evidence; the return value carries none of it. A caller that logs "no result"
  has discarded the only thing the record was written for.
- **Over-reading an interrupted dispatch.** `recover_interrupted` writes a
  receipt with `backend_verdict "overrun"`, `operational_status "failed"` and
  `execution_observed: False`, and packages limitations saying no completion was
  observed. That is not a simulation that ran and failed; nothing is known about
  whether the runner started. Treating it as a refutation of the hypothesis
  reverses the whole point of the recovery path.
- **Expecting research to behave like simulation.** Research grants, fetches,
  packages and consumes inside one conjecture turn; simulation only *proposes*
  there, and the scheduler's capability phase does the rest a cycle later.
  A research package left at `RESULT_PACKAGED` (empty fetch, or source budget
  exhausted) is terminal and never schedules a follow-up reasoning turn — the
  scheduler filters available packages to `SimulationResultPackageV1` for exactly
  this reason.
