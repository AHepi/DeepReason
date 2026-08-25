<!-- DR-SEAM-capabilities-x-rules -->
Verified-at: 1662a3f96
Verify: python tools/docs_verify.py
Owns: src/deepreason/rules/conj.py, src/deepreason/rules/crit.py, src/deepreason/capabilities/simulation.py, src/deepreason/capabilities/research.py
Sides: DR-SUB-capabilities, DR-SUB-rules
Sweep: policy_digest|maximum_proposals_per_turn|MAXIMUM_PROPOSALS_PER_TURN && CapabilityController|stage_transactional_proposals|capability_state|simulation_controller|research_controller

# capabilities x rules

## The agreement

The rules side promises that a capability proposal is filed only from inside a
conjecture turn, only as semantic intent the model authored, and only under
authority the turn published in advance: `conj` writes `simulation_authority`
and `research_authority` blocks — enabled flag, policy digest, per-turn ceiling,
sealed-input aliases — into the v6 semantic task payload before the provider is
called, and files nothing those blocks do not permit. The capabilities side
promises never to trust the caller: each controller re-reads that payload from
the durable work item, compares its `policy_digest` against its own frozen
policy, proves the named provider-result event actually carried the content, and
refuses by raising before any event exists. Filing is therefore two-phase —
`stage_transactional_proposals` validates the whole batch while nothing is
durable, `materialize_transactional_proposals` appends it — because a capability
event joins the frozen process-digest chain the instant it is written and cannot
be withdrawn (`DR-INV-frozen-surfaces` surface 1). Where a proposal goes next is
asymmetric, and the rules side has to know which: research is granted, fetched,
packaged and consumed inside the same turn, while simulation is only recorded and
the scheduler executes it a cycle later. The return path crosses in one direction
only and never as authority — consumed research re-enters the next conjecture
pack as citable blocks, a simulation result re-enters as follow-up prompt context
whose binding `conj` re-derives from replayed state rather than from the argument
it was handed. Neither capability mints a warrant, an attack edge or a problem.
And every rules-side read of the replayed capability maps filters by record type
first, because those maps pool both capabilities.

Exactly one rules module reaches the capabilities package, it reaches it only
through function-local imports, and the arrow never points back. `crit.py` is the
second and last rules module that names a capability at all, and its entire
surface is one read of `harness.capability_state`.
`check: test "$(grep -rl 'deepreason\.capabilities' --include=*.py src/deepreason/rules | wc -l)" -eq 1 && test "$(grep -rlE '^class (Simulation|Research)CapabilityController' --include=*.py src/deepreason/capabilities/ | wc -l)" -eq 2 && ! grep -rq 'deepreason\.rules' --include=*.py src/deepreason/capabilities/ && ! grep -rqE '^(from|import) deepreason\.capabilities' --include=*.py src/deepreason/rules/ && grep -q 'from deepreason.capabilities.simulation import' src/deepreason/rules/conj.py && test "$(grep -rl 'capabilit' --include=*.py src/deepreason/rules | wc -l)" -eq 2 && test "$(grep -c 'capability_state' src/deepreason/rules/crit.py)" -eq 1`

## Where it is expressed

| Site | File | Symbol | What it enforces |
|---|---|---|---|
| Authority published | `rules/conj.py` | `payload["simulation_authority"]`, `payload["research_authority"]` in `conjecture.semantic-task.v2` | the turn states, before dispatch, which channels are open and under which policy digest |
| Authority re-derived | `capabilities/simulation.py`, `capabilities/research.py` | `_stage_transactional_proposal` and `require_transactional_origin` | a proposal is refused unless the preparation it names carries a matching enabled flag, policy digest and ceiling — checked at staging AND again at origin admission |
| Provenance re-derived | `capabilities/simulation.py`, `capabilities/research.py` | the `source.llm.work_order_id` / `dispatch_authorization_ref` / `provider_attempt.id in source.outputs` triple | the semantic content came from the one authorized provider result, not from the caller |
| Sealed-input authority | `capabilities/simulation.py` | `expected_aliases = SIM_###` from `policy.input_catalog` vs `draft.input_aliases` | a proposal may name only the catalog aliases the turn was shown |
| Batch staging | `rules/conj.py` | `simulation_controller.stage_transactional_proposals`, `research_controller.stage_transactional_proposals` | the whole batch validates before the first capability event |
| Staging refusal | `rules/conj.py` | `terminate(status="rejected", reason_code="simulation_semantic_rejected" / "research_semantic_rejected")` | an unauthorized capability draft rejects the whole transaction, candidates included |
| Materialization | `rules/conj.py` | `materialize_transactional_proposals` plus the `"differs from its staged batch"` guard | the durable ids equal exactly the staged ids |
| Partial completion | `rules/conj.py` | `_v6_component_diagnostic(component="simulation" / "research", phase="materialization")` | a half-written capability batch does not cancel the turn's candidates |
| In-turn execution | `rules/conj.py` | `research_controller.execute` then `.consume`, inside the materialization block | a research grant completes in the cycle that proposed it; denial is a typed transition, not an exception |
| Pooled-map read | `rules/conj.py` | `_v6_capability_effect_refs(proposal_model=...)`, `_v6_simulation_effect_refs`, `_v6_research_effect_refs` | recovery of a partial batch reads the pooled proposal map per kind |
| Per-turn ceilings | `rules/conj.py` | `simulation_policy.maximum_proposals_per_turn` (manifest) and `MAXIMUM_PROPOSALS_PER_TURN` (module constant) | the two ceilings come from different owners and both bound the same turn |
| Field constraints | `llm/wire.py` | `ObservableName`, `SealedInputAlias`, `SimulationSeed`, `SimulationProposalDraftV1`, `ResearchFetchProposalDraftV1` imported from `capabilities/models.py` | the model-facing schema and the recorded record share one constraint, not two copies |
| Work-order grant (v5) | `capabilities/simulation.py`, `capabilities/research.py` | `propose`'s `CapabilityOutcome.SIMULATION_REQUEST` / `RESEARCH_REQUEST` check | the pre-transaction path refuses intent the originating work order does not permit |
| Criticism read | `rules/crit.py` | `_filed_simulations`, `_simulation_enabled` | the critic is told which simulations exist, filtered by kind, with no controller in reach |
| Criticism render | `llm/packs.py` | `render_batch_crit_pack(simulation_proposals=..., simulation_enabled=...)` | filed proposals reach a critic only as a rendered summary in one gated section |
| Research return path | `rules/conj.py` | `consumed_research_blocks(harness)` as `extra_blocks` | consumed fetches re-enter reasoning as citable, byte-checkable blocks |
| Simulation return path | `rules/conj.py` | `_capability_result_context` / `_simulation_follow_up_index` and the `"follow-up result binding is not canonical"` guard | a result re-enters only as follow-up prompt context, re-derived from replayed state |
| Replay mirror | `workflow/conjecture_recovery.py` | `"simulation authority differs from manifest"`, `"research authority differs from manifest"`, `"reconstructed contract id differs"` | a recovered turn rebuilds the same authority blocks and the same wire contract; owned by `DR-SUB-workflow`, but it re-derives THIS agreement |
| Replay validation | `invariants.py` | the `capability-origin` per-call proposal-count checks | a recorded root is re-judged against both per-turn ceilings |

The published authority and the controller's re-derivation are one agreement in
two packages. Each controller re-derives it TWICE — once when staging a draft,
once in `require_transactional_origin` — and both sites are pinned, because a
file-wide grep is satisfied by whichever one survives.
`check: grep -q '"simulation_authority": {' src/deepreason/rules/conj.py && grep -q '"research_authority": {' src/deepreason/rules/conj.py && python -c "import inspect; from deepreason.capabilities.simulation import SimulationCapabilityController as S; from deepreason.capabilities.research import ResearchCapabilityController as R; q=chr(34); pat=lambda k: k+'_authority.get('+q+'policy_digest'+q+') != self.policy.digest'; assert all(pat(k) in inspect.getsource(getattr(c, m)) for c, k in ((S, 'simulation'), (R, 'research')) for m in ('_stage_transactional_proposal', 'require_transactional_origin'))"`

Staging appends nothing; only the `propose_transactional` step writes a
transition. This is the property that makes a refused batch leave no record.
`check: python -c "import inspect; from deepreason.capabilities.simulation import SimulationCapabilityController as S; from deepreason.capabilities.research import ResearchCapabilityController as R; staged=[inspect.getsource(c._stage_transactional_proposal) for c in (S, R)]; assert not any('_transition' in s or 'record_capability_transition' in s for s in staged); assert all('self._transition(' in inspect.getsource(c.propose_transactional) for c in (S, R))"`

Materialization must reproduce the staged batch exactly, and a failure inside it
is a typed component diagnostic rather than a lost turn.
`check: grep -q "simulation materialization differs from its staged batch" src/deepreason/rules/conj.py && grep -q "research materialization differs from its staged batch" src/deepreason/rules/conj.py && python -m pytest tests/test_v6_conjecture_component_atomicity.py::test_simulation_materialization_failure_admits_valid_partial_components -q`

The rules side files and consumes; it never constructs a transition, and never
imports the frozen state machine.
`check: test "$(grep -rl 'stage_transactional_proposals' --include=*.py src/deepreason/rules/ | wc -l)" -eq 1 && ! grep -rq "record_capability_transition\|CapabilityReplayState\|capabilities\.state" --include=*.py src/deepreason/rules/ && grep -q "    def record_capability_transition(" src/deepreason/harness.py && grep -q "self.harness.record_capability_transition(" src/deepreason/capabilities/simulation.py && grep -q "self.harness.record_capability_transition(" src/deepreason/capabilities/research.py`

The research ceiling is a module constant three off-package readers import
rather than restate; the simulation ceiling is a manifest field.
`check: for f in src/deepreason/rules/conj.py src/deepreason/invariants.py src/deepreason/workflow/conjecture_recovery.py; do grep -q "from deepreason.capabilities.research import" "$f" || exit 1; grep -q "MAXIMUM_PROPOSALS_PER_TURN" "$f" || exit 1; done; ! grep -qE '"maximum_proposals_per_turn": *[0-9]' src/deepreason/rules/conj.py && grep -q "simulation_policy.maximum_proposals_per_turn" src/deepreason/rules/conj.py`

Recovery and `verify_root` re-derive the same authority the controllers checked
on write, and the follow-up context is re-derived rather than believed: the
package, its transition lifecycle and the context blob's bytes must all agree
before the `SIM_###` alias is minted.
A message grep would survive a guard neutered to `or False`, so the comparison
itself is re-derived here, not just its error text.
`check: grep -q "simulation authority differs from manifest" src/deepreason/workflow/conjecture_recovery.py && grep -q "research authority differs from manifest" src/deepreason/workflow/conjecture_recovery.py && grep -q "reconstructed contract id differs" src/deepreason/workflow/conjecture_recovery.py && grep -q "one provider call exceeds its frozen research-proposal authority" src/deepreason/invariants.py && grep -q "one provider call exceeds its frozen proposal-count authority" src/deepreason/invariants.py && grep -q "simulation result context requires a follow-up work index" src/deepreason/rules/conj.py && grep -q "_capability_result_package_ref=package.id" src/deepreason/scheduler/scheduler.py && python -c "import inspect; from deepreason.rules import conj; from deepreason.workflow import conjecture_recovery as cr; s=inspect.getsource(conj); i=s.index('v6 simulation follow-up result binding is not canonical'); g=s[s.rindex('if (', 0, i):i]; assert all(c in g for c in ('result_package is None', 'result_context_ref != transaction_capability_result_ref', 'transition.lifecycle != CapabilityLifecycle.RESULT_PACKAGED', 'harness.blobs.get(transaction_capability_result_ref).decode', '!= _capability_result_context')), g; r=inspect.getsource(cr); a=r[r.rindex('_authority(', 0, r.index('simulation authority differs from manifest')):r.index('simulation authority differs from manifest')]; b=r[r.rindex('_authority(', 0, r.index('research authority differs from manifest')):r.index('research authority differs from manifest')]; assert all(c in a for c in ('policy.enabled', 'policy.digest', 'policy.maximum_proposals_per_turn')), a; assert all(c in b for c in ('research_policy.enabled', 'research_policy.digest', '_RESEARCH_TURN_MAXIMUM')), b"`

Both rules-side readers of the pooled proposal map discriminate by record kind,
and the criticism reader really does drop a research proposal rather than report
it as a simulation.
`check: python -c "import inspect; from types import SimpleNamespace as N; from deepreason.rules import conj; from deepreason.rules.crit import _filed_simulations as F; from deepreason.capabilities.models import ResearchFetchProposalV1 as R, SimulationProposalV1 as S; assert 'isinstance(proposal, proposal_model)' in inspect.getsource(conj._v6_capability_effect_refs); assert 'proposal_model=SimulationProposalV1' in inspect.getsource(conj._v6_simulation_effect_refs); assert 'proposal_model=ResearchFetchProposalV1' in inspect.getsource(conj._v6_research_effect_refs); c=dict(proposal_index=0, originating_work_order_ref='sha256:'+'a'*64, originating_provider_attempt_ref='sha256:'+'a'*64, source_call_seq=3, problem_ref='pi-1', run_input_digest='b'*64); r=R.create(purpose='p'*20, request_identifier='r-1', urls=('https://example.org/a',), **c); s=S.create(request_identifier='s-1', hypothesis='h', rival_predictions=('a','b'), discriminating_purpose='d', model_source='x=1', requested_observables=('x',), interpretation_conditions=('c',), **c); assert F(N(capability_state=N(proposals={r.id: r, s.id: s}, current_transition_by_request={}, transitions={}))) == (('s-1', 'declarative_numeric_v1', 'proposed', ''),)"`

The wire's observable pattern IS the record's, by reference — the annotation is
the capability package's own constrained type, not a literal that happens to
match it today.
`check: python -c "from deepreason.llm import wire; from deepreason.capabilities import models as m; assert wire.ObservableName is m.ObservableName; assert wire.SimulationProposalWireV1.model_fields['requested_observables'].annotation == list[m.ObservableName]; assert wire.SimulationProposalWireV1.model_json_schema()['properties']['requested_observables']['items']['pattern'] == m.OBSERVABLE_NAME_PATTERN" && grep -q "run-b4d6dfda0c20676a864a051fbc97bda4 died at cycle 0" src/deepreason/capabilities/models.py`

The in-turn asymmetry, end to end: the wire admits the field only when the
manifest enables it, an off-allowlist URL is a typed denial rather than a raise,
and a granted fetch is citable before the turn ends.
`check: python -m pytest tests/test_research_conjecture_wire.py::test_v6_turn_research_proposal_fetches_and_consumes_in_cycle tests/test_research_conjecture_wire.py::test_v6_turn_without_research_authority_rejects_the_wire_field tests/test_research_conjecture_wire.py::test_v6_turn_off_allowlist_research_is_a_typed_denial tests/test_research_capability.py::test_work_order_without_research_grant_cannot_propose -q`

## What is deliberately absent

**`conj` never executes a simulation — it only records the proposal.** The
single `.execute(` and the single `.consume(` in the whole file are the research
controller's; the simulation controller is reached for staging and
materialization and nothing else. `SimulationCapabilityController.execute`
exists and is called by the scheduler's own capability phase a cycle later, so
this is a division of labour, not an unimplemented path — a cycle that runs a
simulation runs nothing else, which is a scheduling decision the conjecture turn
is in no position to make.
`check: test "$(grep -c '\.execute(' src/deepreason/rules/conj.py)" -eq 1 && test "$(grep -c '\.consume(' src/deepreason/rules/conj.py)" -eq 1 && test "$(grep -c 'research_controller\.\(execute\|consume\)(' src/deepreason/rules/conj.py)" -eq 2 && test "$(grep -c 'simulation_controller\.' src/deepreason/rules/conj.py)" -eq 2 && grep -q "    def execute(" src/deepreason/capabilities/simulation.py && python -m pytest tests/test_simulation_capability_v5.py::test_conjecture_records_only_proposal_and_scheduler_executes_later -q`

**Criticism may READ filed simulations and may not FILE one, and the refusal is
structural.** `render_batch_crit_pack` is the only pack function in the codebase
with a `simulation_proposals` parameter, and it renders a summary of proposals
that already exist; no critic output model has a simulation or research field at
all — the check discovers the models rather than listing them, so a critic model
added tomorrow is covered — so there is no channel through which a critic could
author intent. The
critic's stated job in that section is to judge whether the claim NEEDED an
experiment, which is a judgement about the target, not a request for compute.
`check: python -c "import inspect; from pydantic import BaseModel; from deepreason.llm import packs, wire, contracts; names=[n for n in dir(packs) if n.startswith('render_') and 'simulation_proposals' in inspect.signature(getattr(packs, n)).parameters]; assert names == ['render_batch_crit_pack'], names; models={n: o for mod in (contracts, wire) for n, o in vars(mod).items() if isinstance(o, type) and issubclass(o, BaseModel) and 'Critic' in n}; assert len(models) >= 6, sorted(models); assert not [(n, f) for n, o in models.items() for f in o.model_fields if 'simulation' in f or 'research' in f]"`

**A simulation result never enters the formal graph.** `simulation.py` creates no
artifact, no commitment and no warrant; the only thing it hands back to the rules
is text (`result_context`), and that text can only reach a model as a follow-up
conjecture pack section. Research is the single exception and it is not an
exception to the principle: `consume` goes through `register_evidence`, the same
canonical entry the rest of the system uses, at `role="import"`, and every
survivor surface excludes import-role artifacts through the one authority that
owns that rule (`ontology.state.counts_as_survivor`, `DR-SUB-ontology`) — the
scheduler used to be the only place it held, which is how `run-1b31f006`
published 24 admission records as survivors. Nothing at
this seam constructs a `Warrant`; `rules/warrants.py` and the whole of
`adjudication/` do not mention capabilities in any spelling.
`check: ! grep -qE "create_artifact|register_batch|register_commitment|register_evidence" src/deepreason/capabilities/simulation.py && grep -q "    def result_context(" src/deepreason/capabilities/simulation.py && grep -q "from deepreason.research.backends import register_evidence" src/deepreason/capabilities/research.py && python -c "import inspect; from deepreason.capabilities.research import ResearchCapabilityController as R; assert 'register_evidence(' in inspect.getsource(R.consume)" && grep -q 'role: str = "import"' src/deepreason/research/backends.py && python -c "import inspect; from deepreason.scheduler.scheduler import Scheduler, run_report; assert all('counts_as_survivor' in inspect.getsource(s) for s in (Scheduler._select_problem, run_report))" && test "$(ls src/deepreason/adjudication/*.py | wc -l)" -ge 3 && ! grep -rqE "capabilit|imulation" --include=*.py src/deepreason/adjudication/ src/deepreason/rules/warrants.py && grep -q "^def register_fail_warrant(" src/deepreason/rules/warrants.py`

**No capability record spawns a problem, and no rule but `conj` can reach a
controller.** `spawn.py`, `warrants.py`, `act.py`, `vision.py`, `experiment.py`,
`synth.py` and `guards/` contain nothing from the capabilities package — the
anti-relapse gate in particular compares formal verdict vectors and has never
seen a proposal. Beware the false positive: `spawn.py` DOES import
`deepreason.research.backends` and DOES raise `SpawnTrigger.RESEARCH`, and
neither has anything to do with `capabilities/research.py` (see Traps).
`check: ! grep -q "deepreason.capabilities" src/deepreason/rules/spawn.py && grep -q "SpawnTrigger.RESEARCH," src/deepreason/rules/spawn.py && grep -q "from deepreason.research.backends import pending" src/deepreason/rules/spawn.py && test "$(grep -rl 'deepreason\.capabilities' --include=*.py src/deepreason/rules | wc -l)" -eq 1`

**The conjecturer pack does not list the proposals already filed.** The critic
pack does; the conjecturer's channel is the turn schema
(`ConjecturerTurnWireContractV6` carries the enabled flags, the ceilings and the
sealed-input aliases) plus, on a follow-up, one recorded RESULT —
`render_conj_pack` takes `capability_result_context` and no proposal list at all.
This one is recorded as fact: the code states no reason for it. Treat "show the
conjecturer its own filing history" as an open design question rather than a
bug, and price the pack-baseline movement before opening it.
`check: python -c "import inspect; from deepreason.llm.packs import render_conj_pack; ps=list(inspect.signature(render_conj_pack).parameters); assert not [p for p in ps if 'proposal' in p], ps; assert 'capability_result_context' in ps and 'scratch_context' in ps"`

**The staging-rejection path is real code with no test.** Both
`simulation_semantic_rejected` and `research_semantic_rejected` appear only in
`conj.py`; no test in the suite names either. The materialization-failure path
next to it IS pinned. Do not read the missing coverage as evidence the path is
dead — read it as the gap it is.
`check: grep -q 'reason_code="simulation_semantic_rejected"' src/deepreason/rules/conj.py && grep -q 'reason_code="research_semantic_rejected"' src/deepreason/rules/conj.py && test "$(grep -rl 'simulation_semantic_rejected\|research_semantic_rejected' --include=*.py src/ | wc -l)" -eq 1 && test "$(grep -rl 'test_simulation_materialization_failure_admits_valid_partial_components' --include=*.py tests/ | wc -l)" -eq 1 && ! grep -rq "semantic_rejected" --include=*.py tests/`

## How to change it

The order matters because the same authority is written once and re-derived in
three other places, one of which is replay.

1. **Read `DR-INV-frozen-surfaces` first.** `SimulationCapabilityPolicyV1` and
   `ResearchCapabilityPolicyV1` are manifest surfaces: a new field moves the
   qualification subject digest and reruns the ~14-minute battery on every
   existing home. `capabilities/state.py` and the phase records are frozen: a
   new field on a *recorded* proposal changes every transition digest, while a
   new field on the *draft* changes only what the model may say. Decide which
   one you actually need before writing anything.
2. **Change the draft model and the wire model together.**
   `SimulationProposalDraftV1` / `ResearchFetchProposalDraftV1` in
   `capabilities/models.py` and their `*WireV1` mirrors in `llm/wire.py` are one
   contract; the wire imports the constrained types from the capability package
   precisely so a constraint cannot exist in one and not the other.
3. **Move the authority block and its three re-derivations in one commit.**
   `payload["simulation_authority"]` / `["research_authority"]` in `conj.py`,
   `_stage_transactional_proposal` in each controller,
   `workflow/conjecture_recovery.py`, and `invariants.py`'s `capability-origin`
   check. Change fewer than all four and a recorded root stops recovering, which
   no test in the write path will show you.
4. **Put new validation in staging, never in materialization.** Staging is the
   only phase that can refuse without leaving a durable record; a refusal raised
   during materialization has already appended part of the batch and degrades to
   a partial component diagnostic.
5. **Filter any new read of the pooled maps by record type.** `proposals`,
   `grants`, `work_orders`, `receipts`, `result_packages` and `consumptions` hold
   both capabilities. See `DR-CON-capability-lifecycle` for the two places where
   this rule is still violated on the capability side.
6. **Do not close the execution asymmetry.** Research-in-turn and
   simulation-in-scheduler are different because their latencies and their
   budgets are different. Making them symmetric is an operator's call.

What breaks first, in the order you will meet it: a `ValidationError` on the turn
wire (which the schema-repair path will try to fix and then give up on, killing
the cycle); `"v6 preparation does not authorize this simulation proposal"` at
staging; `"simulation materialization differs from its staged batch"`; then
`ConjectureRecoveryAuthorityError` on a resumed run; then, worst and last,
`verify_root`'s `capability-origin` failure on a committed root.

The tests that will catch you, cheapest first:
`tests/test_research_conjecture_wire.py` (the whole in-turn research path, ~4 s),
`tests/test_v6_conjecture_component_atomicity.py` (partial completion),
`tests/test_simulation_capability_v5.py` (staging, budgets, denial ladder),
`tests/test_research_capability.py` (allowance, budgets, citable blocks),
`tests/test_research_root_replay.py` (a real recorded root replays and audits).

## Traps

- **One malformed capability field rejects the whole turn, candidates and all.**
  The capability proposals ride inside the conjecturer's single structured
  output, so a field-level pattern failure is a turn-level parse failure. jolt
  `run-b4d6dfda0c20676a864a051fbc97bda4` died at cycle 0 this way: the model
  named a 3x2x3 measurement grid's cells `animal.baseline.distinct` and
  `requested_observables` demanded plain identifiers — a rule stated in neither
  the schema nor the field description, so the refusal was its first utterance.
  `OBSERVABLE_NAME_PATTERN` now admits bounded dotted paths. The general lesson
  survives the fix: a constraint the capability package adds is a constraint the
  conjecture turn inherits, and it must be expressible in the schema the model
  is given, not only in a validator.
`check: python -c "import json, unittest; from pydantic import ValidationError; from deepreason.llm.wire import ConjecturerTurnWireV6 as W; p=dict(request_identifier='s-1', hypothesis='h', rival_predictions=['a', 'b'], discriminating_purpose='d', model_source='x=1', simulation_mode='declarative_numeric_v1', requested_observables=['animal.baseline.distinct'], interpretation_conditions=['c']); t=dict(candidates=[dict(content='a candidate', typicality=0.3)], simulation_proposals=[p]); W.model_validate(t); b=json.loads(json.dumps(t)); b['simulation_proposals'][0]['requested_observables']=['stdout stream']; unittest.TestCase().assertRaises(ValidationError, W.model_validate, b)" && python -m pytest tests/test_simulation_dotted_observables.py -q`
- **"research" names three unrelated things, and grep cannot tell them apart.**
  `SpawnTrigger.RESEARCH` is a *problem kind* minted when an observation-valued
  commitment has no covering evidence; `deepreason/research/` is the evidence
  backend package (`register_evidence`, `pending`); `capabilities/research.py` is
  the fetch capability. A grep for `research` across `rules/` returns `spawn.py`,
  which is not on this seam at all. The one place they genuinely meet is
  `ResearchCapabilityController.consume`, which registers fetched text through
  the evidence backend — the same door an operator-supplied dossier walks
  through.
`check: grep -q "from deepreason.research.backends import pending" src/deepreason/rules/spawn.py && grep -q "from deepreason.research.backends import register_evidence" src/deepreason/capabilities/research.py && ! grep -q "deepreason.capabilities" src/deepreason/rules/spawn.py`
- **Counting a pooled map.** openchallenge `run-9e9812fe`: two consumed research
  fetches exhausted the *simulation* request and execution budgets before the
  first simulation proposal existed, and both typed simulation proposals were
  denied with zero simulations run. The rules side inherited the same hazard and
  answers it twice — `_v6_capability_effect_refs` takes a `proposal_model`, and
  `_filed_simulations` drops anything without a `simulation_mode` — so a
  criticism pack never reports a fetch as a filed simulation. The capability side
  still has two unfixed instances; see `DR-CON-capability-lifecycle`.
`check: grep -q "run-9e9812fe" src/deepreason/capabilities/simulation.py && python -m pytest tests/test_simulation_capability_v5.py::test_research_spend_does_not_exhaust_simulation_budgets -q`
- **Reading a `None` from `execute` as "nothing happened".** `conj` calls
  `research_controller.execute` and treats `None` — and an empty package — as
  "do not consume". The denial itself is a durable `DENIED` transition carrying
  its `reason_code`; the return value carries none of it. A change that logs or
  reports from the return value instead of the record reports silence where the
  record has a reason.
- **Assuming the guard is in the rule.** Whether a proposal may be filed at all
  is decided in the controller's staging validator, not in `conj`; `conj`
  contributes the authority block and then does as it is told. Searching
  `conj.py` for the enabled-check and finding only a payload field is the
  expected result.
- **Believing the v5 path is dead.** `conj` still calls `controller.propose(...)`
  per draft under `active_v5`, with the work order's `capability_grant` as the
  only authority. Production runs are v6, but the v5 branch is live code with a
  different — weaker — admission contract, and a change to "the proposal
  contract" that touches only the transactional path leaves it behind.
`check: grep -q "controller.propose(" src/deepreason/rules/conj.py && grep -q "originating work order does not permit a simulation proposal" src/deepreason/capabilities/simulation.py && grep -q "originating work order does not permit a research proposal" src/deepreason/capabilities/research.py`
