<!-- DR-SUB-capabilities -->
Verified-at: 546544b5
Verify: python -m pytest tests/test_simulation_capability_v5.py tests/test_research_capability.py tests/test_research_root_replay.py -q
Owns: src/deepreason/capabilities/
Seams: DR-SEAM-capabilities-x-rules
Seams-undocumented: capabilities x harness, capabilities x llm, capabilities x ontology, capabilities x scheduler, capabilities x verification, capabilities x workflow

# Capabilities — running a program and fetching a document, under frozen authority

## What it is

`capabilities/` is the run's only contact with anything outside its own
reasoning: it executes a model-proposed program, or it fetches a document from a
frozen host allowlist. The model contributes semantic intent and nothing else —
hypothesis, rival predictions, observable names, URLs, purpose — while every
operational parameter (toolchain, runner profile, wall-clock and memory ceiling,
seeds, request budget, response byte cap) is authored by the manifest policy or
by this package's own code. Intent becomes action only by walking the typed
lifecycle described in `DR-CON-capability-lifecycle`, one chained transition per
step, so a run's entire outside contact re-derives from the append-only log and
a denial is a durable record rather than silence. Two capabilities exist,
simulation and research; they share the state machine, the transition record,
the event envelope and the replay validator, and differ in their budgets, their
controllers, and where in the cycle they execute. The package is deliberately
import-light at the top level — `ontology/event.py` must be able to load the
capability event envelope without dragging in the controllers.
`check: ! grep -qE "^(from|import) " src/deepreason/capabilities/__init__.py && grep -q "no eager re-exports" src/deepreason/capabilities/__init__.py`

The two capabilities run at different points. Research executes *inside* the
conjecture turn (`rules/conj.py` grants, fetches and consumes before the turn's
effects are materialized), while simulation only ever *proposes* during a turn
and is executed later by the scheduler's own capability phase
(`_simulation_capability_step`). The scheduler never reaches the research
CAPABILITY at all — but do not read that as "the scheduler has nothing to do
with research". It owns a separate, older subsystem of the same name: the §12
`ResearchService` driven by `_research_step` over `research/backends.py`, which
shares no code, no budget and no record type with `capabilities/research.py`.
Grepping `research` in `scheduler.py` finds that one, not this package.
`check: grep -q "    def _simulation_capability_step(" src/deepreason/scheduler/scheduler.py && grep -q "research_controller.execute(" src/deepreason/rules/conj.py && ! grep -qE "ResearchCapabilityController|capabilities\.research|capabilities import research" src/deepreason/scheduler/scheduler.py && grep -q "    def _research_step(" src/deepreason/scheduler/scheduler.py && grep -q "from deepreason.research.backends import ResearchService" src/deepreason/scheduler/scheduler.py`

## Entry points

- `simulation.SimulationCapabilityController` — constructed from a live
  `Harness` plus a v5/v6 `RunManifest`; refuses to exist without one.
  - `.propose` records semantic intent as a `PROPOSED` transition and stops; no
    grant, no compilation, no dispatch.
  - `.stage_transactional_proposals` / `.propose_transactional` /
    `.materialize_transactional_proposals` — the v6 path, where drafts are
    validated against the turn's authority before any event is appended and
    materialized as workflow effects afterwards.
  - `.require_transactional_origin` — fail-closed re-derivation of a proposal's
    completed v6 work item, provider attempt, semantic admission and task
    payload; the same predicate `verify_root` re-runs on replay.
  - `.execute` — the whole VALIDATED → GRANTED|DENIED → COMPILED → DISPATCHED →
    SUCCEEDED|FAILED → RESULT_PACKAGED walk for one already-recorded proposal
    (the DENIED leg is emitted by the `_denied` helper, not inline). Returns
    `None` on denial. CONSUMED is NOT part of this walk — `.consume` appends it
    separately, and only for a package a caller chose to bind.
  - `.recover_interrupted` — closes a durable `DISPATCHED` prefix as an explicit
    unknown failure rather than rerunning the work order.
  - `.consume` / `.consume_transactional` — bind a result package to one fresh
    follow-up work item, spending the follow-up budget.
  - `.result_context` / `.accounting` — the model-facing result text
    (`simulation-result-context.v1`) and the replay-derived roll-up
    (`capability-accounting.v1`).
`check: grep -q "^class SimulationCapabilityController" src/deepreason/capabilities/simulation.py && for s in propose stage_transactional_proposals propose_transactional materialize_transactional_proposals require_transactional_origin execute recover_interrupted consume consume_transactional result_context accounting; do grep -q "    def $s(" src/deepreason/capabilities/simulation.py || exit 1; done && grep -q '"schema": "simulation-result-context.v1"' src/deepreason/capabilities/simulation.py && grep -q '"schema": "capability-accounting.v1"' src/deepreason/capabilities/simulation.py && grep -q ").require_transactional_origin(proposal)" src/deepreason/invariants.py && python -c "import inspect; from deepreason.capabilities.simulation import SimulationCapabilityController as C; s=inspect.getsource(C.execute)+inspect.getsource(C._denied); missing=[n for n in ('VALIDATED','GRANTED','DENIED','COMPILED','DISPATCHED','SUCCEEDED','FAILED','RESULT_PACKAGED') if f'CapabilityLifecycle.{n}' not in s]; assert not missing, missing; assert 'CapabilityLifecycle.CONSUMED' not in s"`

- `research.ResearchCapabilityController` — same shape, v6 only, with an
  injectable `transport` so tests never reach the network.
  - `.propose`, `.stage_transactional_proposals`, `.propose_transactional`,
    `.materialize_transactional_proposals`, `.require_transactional_origin` —
    the mirror of the simulation staging path.
  - `.execute` — allowlist check, budget check, dynamic-allowance check, grant,
    compile, dispatch, receipt, package. Every rejection is a typed `DENIED`
    transition carrying its reason code.
  - `.consume` — registers packaged text as candidate evidence, capped by
    `maximum_sources` across the whole run.
- `research.dynamic_research_allowance` — pure function of replayed state
  returning how much of the frozen cap is *currently* grantable, plus the three
  readings it derived that from. The cap itself never moves.
- `research.blocks_for_fetched_text` / `research.consumed_research_blocks` — the
  deterministic segmentation that makes fetched material citable and
  byte-checkable exactly like an attached dossier.
`check: grep -q "^class ResearchCapabilityController" src/deepreason/capabilities/research.py && for s in propose stage_transactional_proposals propose_transactional materialize_transactional_proposals require_transactional_origin execute consume; do grep -q "    def $s(" src/deepreason/capabilities/research.py || exit 1; done && for s in dynamic_research_allowance blocks_for_fetched_text consumed_research_blocks; do grep -q "^def $s(" src/deepreason/capabilities/research.py || exit 1; done && grep -q "def __init__(self, harness, manifest, \*, transport=None)" src/deepreason/capabilities/research.py && grep -q "raise ValueError(\"research controller requires one v6 run manifest\")" src/deepreason/capabilities/research.py`

- `state.CapabilityReplayState` — the replay-only state machine; `.apply` is the
  single validator every capability event passes through and `.digest` is the
  content address `verify_root` compares across two replays. Both are FROZEN;
  see `DR-INV-frozen-surfaces`.
- `events.CapabilityEventPayloadV1` — the only admissible capability event body.
- `models` — every phase record, plus `capability_next_process_digest` and
  `OBSERVABLE_NAME_PATTERN`.
- `policy.InquiryCapabilityPolicyV1` — the whole opt-in topology
  (`attached_evidence`, `simulation`, `formalization`, `research`,
  `config_referee`) that the manifest freezes. FOUR of the five expose their own
  `digest` property; `FormalizationCapabilityPolicyV1` does NOT, and reaches the
  manifest digest only through its parent's dump. Do not assume a sub-policy
  digest exists before looking for it.
- `audit.write_tranche_a_audits` — post-run markdown reconstructed from typed
  events only; never from model self-report.
- `evidence.attach_frozen_evidence` / `render_frozen_evidence` — v5-only
  manifest-frozen dossier attachment.
`check: grep -q "^class CapabilityReplayState" src/deepreason/capabilities/state.py && grep -q "    def apply(" src/deepreason/capabilities/state.py && grep -q "    def digest(" src/deepreason/capabilities/state.py && grep -q "^class CapabilityEventPayloadV1" src/deepreason/capabilities/events.py && grep -q "^def capability_next_process_digest(" src/deepreason/capabilities/models.py && for s in AttachedEvidencePolicyV1 SimulationCapabilityPolicyV1 FormalizationCapabilityPolicyV1 ResearchCapabilityPolicyV1 ConfigRefereePolicyV1 FrozenEvidencePolicyV1 InquiryCapabilityPolicyV1; do grep -q "^class $s(" src/deepreason/capabilities/policy.py || exit 1; done && python -c "from deepreason.capabilities import policy as p; assert {'attached_evidence','simulation','formalization','research','config_referee'} <= set(p.InquiryCapabilityPolicyV1.model_fields); assert not isinstance(getattr(p.FormalizationCapabilityPolicyV1,'digest',None), property); assert all(isinstance(getattr(c,'digest',None), property) for c in (p.AttachedEvidencePolicyV1,p.SimulationCapabilityPolicyV1,p.ResearchCapabilityPolicyV1,p.ConfigRefereePolicyV1))" && grep -q "^def write_tranche_a_audits(" src/deepreason/capabilities/audit.py && grep -q "^def attach_frozen_evidence(" src/deepreason/capabilities/evidence.py && grep -q "^def render_frozen_evidence(" src/deepreason/capabilities/evidence.py`

## State it owns

Nothing of its own on disk except the post-run audit markdown: `audit.py` is the
only module in the package that writes a file, and it writes atomically into an
already-stopped root. Everything else persists through the harness — fifteen
`capability-*` object-store schemas (one transition schema plus seven phase
schemas per capability kind), raw blobs for simulation source / sealed inputs /
checker / stdout / stderr / diagnostics / structured output / result context and
for each fetched document's text, and exactly one `Rule.CAPABILITY` event per
transition whose payload is a `CapabilityEventPayloadV1`. The event and the
payload are paired by well-formedness in the ontology, so a capability event can
neither appear bare nor smuggle a payload onto another rule.
`check: test "$(grep -rlE "write_text|write_bytes|\.open\(" --include=*.py src/deepreason/capabilities)" = "src/deepreason/capabilities/audit.py" && grep -q "def _atomic_write" src/deepreason/capabilities/audit.py && for s in capability-transition capability-simulation-proposal capability-simulation-grant capability-compiled-simulation capability-simulation-work-order capability-simulation-receipt capability-simulation-result-package capability-simulation-consumption capability-research-proposal capability-research-grant capability-compiled-research-fetch capability-research-work-order capability-research-receipt capability-research-result-package capability-research-consumption; do grep -q "\"$s\":" src/deepreason/storage/objects.py || exit 1; done && test "$(grep -oE '"capability-[a-z-]+":' src/deepreason/storage/objects.py | sort -u | wc -l)" -eq 15 && grep -q "if (self.rule == Rule.CAPABILITY) != (self.capability is not None):" src/deepreason/ontology/event.py`

The in-memory materialization is `CapabilityReplayState`, held by the harness as
`harness.capability_state` and rebuilt entirely by replay: nine maps
(`proposals`, `transitions`, `current_transition_by_request`, `grants`,
`compiled`, `work_orders`, `receipts`, `result_packages`, `consumptions`), the
consumed event sequence list, and the single run-wide `process_digest` that
every transition extends. The maps are POOLED across both capability kinds —
that pooling is the package's main hazard, and is covered under Traps. The
research controller additionally records one `Measure` event carrying the
allowance and its three readings, so the tuning is auditable without being
re-derived by hand — but ONLY for a proposal that has already cleared the
enabled, backend-identity, allowlist and hard-budget gates. Those four denials
return before the reading is taken, so a `DENIED` transition with no
accompanying allowance `Measure` is normal, not a lost record.
`check: grep -q "self.capability_state = CapabilityReplayState()" src/deepreason/harness.py && grep -q "self.capability_state.apply(" src/deepreason/harness.py && grep -q "f\"research-allowance:{allowance}/{self.policy.maximum_requests}\"" src/deepreason/capabilities/research.py && python -c "import inspect; from deepreason.capabilities.research import ResearchCapabilityController as R; s=inspect.getsource(R.execute); assert s.index('research_disabled') < s.index('backend_identity_mismatch') < s.index('url_outside_frozen_allowlist') < s.index('requests_budget_exhausted') < s.index('record_measure') < s.index('requests_allowance_exhausted')" && python -c "import dataclasses; from deepreason.capabilities.state import CapabilityReplayState as S; f=[x.name for x in dataclasses.fields(S)]; assert f == ['proposals','transitions','current_transition_by_request','grants','compiled','work_orders','receipts','result_packages','consumptions','event_seqs','process_digest'], f"`

## Where to change what

| To change... | Edit | Test |
|---|---|---|
| What a model may say in a simulation proposal (fields, bounds, observable syntax) | `SimulationProposalDraftV1` and `OBSERVABLE_NAME_PATTERN` in `capabilities/models.py`, AND `SimulationProposalWireV1` in `llm/wire.py` — both, or the schema and the validator diverge | `tests/test_simulation_capability_v5.py::test_v5_wire_allows_simulation_only_and_rejects_authority_fields` |
| The bounds a simulation actually runs under (requests, executions, wall/memory, seeds, runner profile) | `SimulationCapabilityPolicyV1` in `capabilities/policy.py` — a manifest surface, so `DR-INV-frozen-surfaces` and the qualification-cache cost apply | `tests/test_run_manifest_v5_inquiry.py::test_simulation_runner_profile_must_match_exact_frozen_toolchain` |
| Whether a simulation proposal is granted, and the typed reason when it is not | the `reason = "..."` ladder in `SimulationCapabilityController.execute` (`capabilities/simulation.py`) | `tests/test_simulation_capability_v5.py::test_invalid_declarative_program_is_denied_without_dispatch` |
| Which runner may run model-authored Python, and what must be present for it | `SimulationCapabilityController._toolchain_available` in `capabilities/simulation.py` | `tests/test_simulation_capability_v5.py::test_sandboxed_python_has_no_host_fallback`, `tests/test_contained_simulation_runner.py::test_contained_runner_unavailable_host_denies_typed` |
| How sealed inputs are resolved into the compiled input document | `SimulationCapabilityController._compile_inputs` plus `SimulationInputBindingV1` in `capabilities/policy.py` | `tests/test_simulation_capability_v5.py::test_v5_wire_rejects_malformed_sealed_input_alias` |
| What a crash-interrupted dispatch records | `SimulationCapabilityController.recover_interrupted` in `capabilities/simulation.py` | `tests/test_simulation_capability_v5.py::test_dispatched_crash_recovers_as_unknown_without_silent_rerun` |
| Which hosts research may reach, and its run-total request/source/byte budgets | `ResearchCapabilityPolicyV1` in `capabilities/policy.py` | `tests/test_run_manifest_v5_inquiry.py::test_research_policy_fields_are_digest_stable_and_allowlist_gated`, `tests/test_research_capability.py::test_source_consumption_is_capped_by_the_frozen_policy` |
| How much of the frozen research cap is currently grantable (waste, refusal streak, stagnation) | `dynamic_research_allowance` in `capabilities/research.py` | `tests/test_research_capability.py::test_waste_tightening_denies_grants_and_citation_restores_them`, `::test_refusal_streak_tightens_the_allowance`, `::test_stagnation_widens_the_allowance_to_the_cap` |
| How a fetched document becomes citable, byte-checkable evidence | `blocks_for_fetched_text` / `consumed_research_blocks` / `ResearchCapabilityController.consume` in `capabilities/research.py` | `tests/test_research_capability.py::test_consumed_fetches_become_citable_byte_checked_blocks` |
| When a proposal may be filed at all, and how many per turn | `MAXIMUM_PROPOSALS_PER_TURN` in `capabilities/research.py` and `maximum_proposals_per_turn` on the simulation policy; the staging call sites live in `rules/conj.py` | `tests/test_simulation_capability_v5.py::test_conjecture_records_only_proposal_and_scheduler_executes_later` |
| The post-run audit markdown | `write_tranche_a_audits` and `_transition_chains` in `capabilities/audit.py` | `tests/test_research_root_replay.py::test_live_research_root_replays_valid_and_audits_cleanly` |
| The lifecycle states, their legal predecessors, or which record a state may carry | `CapabilityLifecycle` in `capabilities/enums.py`, `_ALLOWED_PREVIOUS` / `_PHASE_MODELS` / `_RESEARCH_PHASE_MODELS` in `capabilities/state.py`, AND the `expected` map in `Harness.record_capability_transition` — FROZEN, see `DR-INV-frozen-surfaces` and `DR-CON-capability-lifecycle` | `tests/test_research_root_replay.py::test_live_research_root_replays_valid_and_audits_cleanly` |
| Add a third capability kind | every row above plus the `capability-*` schema map in `storage/objects.py` and the per-kind branches in `invariants.py` — a frozen-surface change requiring explicit operator approval | `tests/test_simulation_capability_v5.py::test_research_spend_does_not_exhaust_simulation_budgets` (pooled-map hazard), `tests/test_research_root_replay.py::test_live_research_root_replays_valid_and_audits_cleanly` (per-kind `verify_root` branch), then the full gate |

`check: test -d experiments/live_research_2026-07-29/wide/runs/run-0c3ce902cc5bca75a709b04e2473d100 && python -m pytest tests/test_simulation_capability_v5.py::test_v5_wire_allows_simulation_only_and_rejects_authority_fields tests/test_simulation_capability_v5.py::test_v5_wire_rejects_malformed_sealed_input_alias tests/test_simulation_capability_v5.py::test_conjecture_records_only_proposal_and_scheduler_executes_later tests/test_simulation_capability_v5.py::test_invalid_declarative_program_is_denied_without_dispatch tests/test_simulation_capability_v5.py::test_sandboxed_python_has_no_host_fallback tests/test_contained_simulation_runner.py::test_contained_runner_unavailable_host_denies_typed tests/test_run_manifest_v5_inquiry.py::test_simulation_runner_profile_must_match_exact_frozen_toolchain tests/test_run_manifest_v5_inquiry.py::test_research_policy_fields_are_digest_stable_and_allowlist_gated tests/test_research_capability.py::test_source_consumption_is_capped_by_the_frozen_policy tests/test_research_capability.py::test_consumed_fetches_become_citable_byte_checked_blocks tests/test_research_capability.py::test_waste_tightening_denies_grants_and_citation_restores_them tests/test_research_capability.py::test_refusal_streak_tightens_the_allowance tests/test_research_capability.py::test_stagnation_widens_the_allowance_to_the_cap tests/test_research_root_replay.py::test_live_research_root_replays_valid_and_audits_cleanly tests/test_simulation_capability_v5.py::test_research_spend_does_not_exhaust_simulation_budgets -q`

The table's Edit column is checked too — a row that points at a symbol which has
been renamed away sends the reader to the wrong file, which is the failure mode
a map exists to prevent.
`check: set -e; for pair in SimulationProposalDraftV1:capabilities/models.py OBSERVABLE_NAME_PATTERN:capabilities/models.py capability_next_process_digest:capabilities/models.py SimulationProposalWireV1:llm/wire.py SimulationCapabilityPolicyV1:capabilities/policy.py SimulationInputBindingV1:capabilities/policy.py ResearchCapabilityPolicyV1:capabilities/policy.py maximum_proposals_per_turn:capabilities/policy.py _toolchain_available:capabilities/simulation.py _compile_inputs:capabilities/simulation.py recover_interrupted:capabilities/simulation.py MAXIMUM_PROPOSALS_PER_TURN:capabilities/research.py dynamic_research_allowance:capabilities/research.py blocks_for_fetched_text:capabilities/research.py consumed_research_blocks:capabilities/research.py write_tranche_a_audits:capabilities/audit.py _transition_chains:capabilities/audit.py CapabilityLifecycle:capabilities/enums.py _ALLOWED_PREVIOUS:capabilities/state.py _PHASE_MODELS:capabilities/state.py _RESEARCH_PHASE_MODELS:capabilities/state.py record_capability_transition:harness.py; do grep -q "${pair%%:*}" "src/deepreason/${pair##*:}" || { echo "MISSING $pair"; exit 1; }; done; python -c "import inspect, re; from deepreason.capabilities.simulation import SimulationCapabilityController as C; assert len(re.findall(r'reason = .', inspect.getsource(C.execute))) >= 5"`

## Traps

- **The replayed maps pool BOTH capabilities; a per-capability budget that
  counts them raw is wrong.** In openchallenge `run-9e9812fe` two research
  fetches consumed the simulation request and execution budgets before the first
  simulation proposal existed, and both typed simulation proposals were denied
  with zero simulations run. Every count in `execute`, in `_requests_already_used`,
  in `_sources_already_consumed`, in `accounting` and in the `capability-budget`
  checks of `verify_root` must filter by record type first.
`check: grep -q "run-9e9812fe" src/deepreason/capabilities/simulation.py && grep -q "isinstance(item, SimulationProposalV1)" src/deepreason/capabilities/simulation.py && grep -q "isinstance(order, SimulationWorkOrderV1)" src/deepreason/capabilities/simulation.py && grep -q "isinstance(receipt, ResearchExecutionReceiptV1)" src/deepreason/capabilities/research.py && python -m pytest tests/test_simulation_capability_v5.py::test_research_spend_does_not_exhaust_simulation_budgets -q`
- **A rule stated only in a refusal message is a rule the model never saw.**
  jolt `run-b4d6dfda0c20676a864a051fbc97bda4` died at cycle 0 on `simulation
  observables must be plain identifiers`: the model had designed a 3x2x3
  measurement grid and named its cells `animal.baseline.distinct`, which is the
  natural shape, and neither the schema nor the field description said
  otherwise. `OBSERVABLE_NAME_PATTERN` now admits bounded dotted paths and is
  emitted into the schema. The repeat is bounded rather than `*` so backends
  that compile the schema into a sampling grammar still see a finite pattern.
  The general form of this trap — read the diagnostic blob before theorising
  about a cycle-0 death — is a project invariant, not a local one.
`check: grep -q "^OBSERVABLE_NAME_PATTERN = " src/deepreason/capabilities/models.py && grep -q "run-b4d6dfda0c20676a864a051fbc97bda4 died at cycle 0" src/deepreason/capabilities/models.py && python -c "import re; from deepreason.capabilities.models import OBSERVABLE_NAME_PATTERN as P; from deepreason.llm.wire import SimulationProposalWireV1 as W; assert re.fullmatch(P, 'animal.baseline.distinct'); assert '{0,7}' in P and '*' not in P; pats=lambda o: [p for k,v in o.items() for p in ([v] if k=='pattern' else pats(v))] if isinstance(o,dict) else ([p for v in o for p in pats(v)] if isinstance(o,list) else []); assert P in pats(W.model_json_schema())" && python -m pytest tests/test_simulation_dotted_observables.py -q`
- **The research request budget is run-cumulative, not per-proposal, and it is
  never a stored counter.** Spend is re-derived as the maximum
  `requests_used_total` over replayed research receipts, and the fetcher is
  preloaded with it before the first URL of a new proposal, so a second proposal
  cannot restart the budget. Exhaustion is a typed record carrying count and
  limit, never a silent stop.
`check: grep -q "fetcher.requests_used = already_used" src/deepreason/capabilities/research.py && grep -q "    def _requests_already_used(" src/deepreason/capabilities/research.py && grep -q "requests_budget_exhausted" src/deepreason/capabilities/research.py && python -m pytest tests/test_research_capability.py::test_budget_is_cumulative_and_exhaustion_is_typed tests/test_research_capability.py::test_off_allowlist_proposal_is_denied_without_dispatch -q`
- **A durable `DISPATCHED` with no receipt must never be rerun.** Replay cannot
  know whether the external subprocess began or completed, so
  `recover_interrupted` writes an explicit unknown operational failure —
  `execution_disposition="dispatch_interrupted"`, `execution_observed: False` —
  and states in the result context that the interruption does not refute the
  hypothesis. Separately, a `failure_policy` of `terminal` turns an interrupted
  dispatch into `CapabilityTerminalError` and ends the inquiry, so the two
  failure paths must be changed together.
`check: grep -q "never a silent rerun" src/deepreason/capabilities/simulation.py && grep -q "execution_disposition=\"dispatch_interrupted\"" src/deepreason/capabilities/simulation.py && grep -q "class CapabilityTerminalError" src/deepreason/capabilities/simulation.py && grep -q "self.policy.failure_policy == \"terminal\"" src/deepreason/capabilities/simulation.py && grep -q '"execution_observed": False,' src/deepreason/capabilities/simulation.py && grep -q "The interrupted dispatch does not refute the motivating hypothesis." src/deepreason/capabilities/simulation.py && python -m pytest tests/test_simulation_capability_v5.py::test_dispatched_crash_recovers_as_unknown_without_silent_rerun -q`
- **Policy serialization is byte-load-bearing, and the digest properties do not
  agree with each other.** New research and config-referee fields carry `exclude_if` so an
  existing disabled policy keeps its exact bytes, its manifest digest, and
  therefore its cached qualification; dropping that would rerun the ~14-minute
  battery on every existing home. Worse, the digest properties disagree about
  aliasing, and it is a TWO-versus-FOUR split, not one outlier:
  `SimulationCapabilityPolicyV1` and `FrozenEvidencePolicyV1` dump WITHOUT
  `by_alias` and so hash the field name `schema_`, while
  `AttachedEvidencePolicyV1`, `ResearchCapabilityPolicyV1`,
  `ConfigRefereePolicyV1` and the parent `InquiryCapabilityPolicyV1` dump WITH
  it and hash `schema`. Every one of them is frozen by existing roots; none may
  be "tidied" toward the other convention.
`check: test "$(grep -c "exclude_if" src/deepreason/capabilities/policy.py)" -eq 3 && python -c "import inspect; from deepreason.capabilities import policy as p; a=lambda c: 'by_alias=True' in inspect.getsource(c.digest.fget); assert not a(p.SimulationCapabilityPolicyV1) and not a(p.FrozenEvidencePolicyV1); assert a(p.AttachedEvidencePolicyV1) and a(p.ResearchCapabilityPolicyV1) and a(p.ConfigRefereePolicyV1) and a(p.InquiryCapabilityPolicyV1)"`
- **The research per-turn proposal ceiling is a wire constant, not a policy
  field.** `MAXIMUM_PROPOSALS_PER_TURN = 2` lives in `research.py` precisely
  because growing `ResearchCapabilityPolicyV1` would perturb frozen manifest
  digests; the run-total budgets do live in the policy. The simulation side made
  the opposite choice (`maximum_proposals_per_turn` IS a policy field), so the
  two are not symmetric and neither should be "harmonised" without accepting a
  digest change.
`check: grep -q "^MAXIMUM_PROPOSALS_PER_TURN = 2" src/deepreason/capabilities/research.py && ! sed -n "/^class ResearchCapabilityPolicyV1/,/^class ConfigRefereePolicyV1/p" src/deepreason/capabilities/policy.py | grep -q "maximum_proposals_per_turn" && grep -q "maximum_proposals_per_turn: int" src/deepreason/capabilities/policy.py`
- **Authority narrows down the chain and is re-checked on replay, never only on
  write.** A grant may not widen the proposed URLs, a compiled fetch must match
  its grant field for field, and a result package may not carry content no
  attempt receipted. These are enforced in `state.apply`, so a controller bug
  that produced a wider grant would fail `verify_root` rather than reach a pack.
`check: python -c "import inspect; from deepreason.capabilities.state import CapabilityReplayState as S; a=inspect.getsource(S.apply); missing=[m for m in ('research grant widens the proposed urls','research package carries unreceipted content','capability transition changed frozen authority','compiled research fetch') if m not in a]; assert not missing, missing"`
- **`evidence.py` is a v5-only path with no live caller.** Both functions
  short-circuit unless `manifest.schema_version == 5`, and nothing under `src/`
  or `tests/` calls either — production runs are v6, where dossier material
  arrives through the research capability instead. Treat it as dormant, not as
  the current mechanism; do not wire new work through it without first deciding
  whether it should exist at all.
`check: test "$(grep -rl "attach_frozen_evidence\|render_frozen_evidence" --include=*.py src tests)" = "src/deepreason/capabilities/evidence.py" && grep -q "manifest.schema_version != 5" src/deepreason/capabilities/evidence.py`
