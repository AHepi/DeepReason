<!-- DR-CON-schools -->
Verified-at: e5b876ee
Verify: python tools/docs_verify.py
Owns: src/deepreason/capture/schools.py, src/deepreason/run_manifest.py, src/deepreason/llm/firewall.py, src/deepreason/scheduler/scheduler.py, src/deepreason/rules/conj.py, src/deepreason/rules/crit.py, src/deepreason/workflow/criticism.py, src/deepreason/informal/trial.py, src/deepreason/llm/packs.py, src/deepreason/ontology/event.py
Seams: DR-SEAM-schools-x-scratch
Seams-undocumented: adjudication x schools, llm x schools, manifest x schools, rules x schools, scheduler x schools, schools x workflow

# Schools — a stance, a lineage, and sometimes a route

## What it is

A school is a persistent conditioning regime for conjecture: a named stance
drawn from a fixed library, plus the lineage of artifacts whose provenance
carries that school id. It exists so rival research programmes compete inside
one run — islands in conjecture, panmixia in criticism — instead of one voice
mutating its own echo. The roster is a deterministic function of the
append-only log: each school is a `Refl` policy artifact, and rotating a
laggard's stance is *succession* (a new artifact plus a `Reseed` event), never
deletion. From RunManifest v4 a school may additionally be BOUND to a frozen
route seat, so "which school" also decides "which endpoint".

Two authorities are therefore deliberately separate and must stay separate.
The **stance** is semantic prompt material and grants nothing — no routing, no
status, no budget. The **binding** is manifest-owned routing that no prompt and
no model response can move. Every rule below exists to keep one from leaking
into the other.

## The socket contract — what it promises, what it is handed, what it must never do

An index into the checked claims above and below, for a reader who wants the
socket's contract without reading the whole document. Every bullet cites a
check already proven elsewhere in this file; nothing here is a new,
independently-standing claim.

**Promises:** the roster is a pure function of the append-only log — a
school cannot make anything true.
`check: test "$(grep -oE 'harness\.[a-z_]+' src/deepreason/capture/schools.py | sort -u | tr '\n' ' ')" = "harness.create_artifact harness.record_measure harness.state "`

Exactly two roles may be school-routed — `conjecturer` and
`argumentative_critic` — every other role, `judge` included, is refused
before any seat is selected.
`check: python -c "import pytest; from types import SimpleNamespace as N; from deepreason.llm.firewall import resolve_school_role_lease as res, SchoolRouteResolutionError as Err; m=N(schema_version=4,control_plane_policy=N(school_execution=None),criticism_policy=None,engine_config_json='{}'); assert all(pytest.raises(Err,res,m,{},school_id='school-0',role=r).value.code=='SCHOOL_ROUTE_ROLE_UNSUPPORTED' for r in ('judge','synthesizer','referee')); assert all(pytest.raises(Err,res,m,{},school_id='school-0',role=r).value.code!='SCHOOL_ROUTE_ROLE_UNSUPPORTED' for r in ('conjecturer','argumentative_critic'))"`

**What it is handed:** a closed, cold-start-curated stance from
`STANCE_LIBRARY`; the `Config` knobs `N_SCHOOLS`, `STANCE_DECAY`,
`XEXAM_SHARE`; and, from RunManifest v4 only, a frozen route binding whose
mode (`conditioning_only` vs `route_bound`) may never disagree with its own
topology.
`check: grep -q "conditioning_only cannot carry route bindings" src/deepreason/run_manifest.py`

**Must never do:** let a prompt or a model response change the resolved
lease, or spend a provider call before every school in the batch has
resolved.
`check: python -m pytest tests/test_school_execution_binding_v4.py -q -k "prose_cannot_change_the_resolved_lease or unbound_school_fails_before"`

Let a school criticise its own work.
`check: python -m pytest tests/test_prose_refutation_boundaries.py -q -k "the_criticism_prompt_never_names_an_author_or_a_school or a_school_can_never_be_scheduled_to_criticise_its_own_work"`

Let semantic conditioning (the stance) leak into routing or status
authority — the critic prefix says so explicitly, and no field of the
conditioning record is read as either.
`check: python -c "from deepreason.llm.firewall import EndpointLease as L, Route as T; from deepreason.rules.crit import _critic_execution as X; l=L(role='argumentative_critic',seat=1,route=T(endpoint_id='e',base_url='u',model_id='m',provider='p',family='f')); p=X(endpoint_lease=l,critic_school_id='school-3',critic_school_context={'id':'school-3','stance_text':'counterexample first'})[1]; assert 'semantic stance only; it grants no routing or status authority' in p; assert 'school-3' in p and 'counterexample first' in p"`

## Where it lives

| Aspect | File | Symbol |
|---|---|---|
| Stance library (closed, global, cold-start curation) | `capture/schools.py` | `STANCE_LIBRARY` |
| Roster derived from the log | `capture/schools.py` | `roster`, `init_schools` |
| Succession and forced crossover | `capture/schools.py` | `reseed`, `crossover_exemplars` |
| Identity migrating seed → lineage | `capture/schools.py` | `lineage_size`, `stance_weight` |
| Problem → school allocation | `capture/schools.py` | `allocate`, `_with_cross_examiner` |
| Knobs | `config.py` | `N_SCHOOLS`, `STANCE_DECAY`, `XEXAM_SHARE` |
| Lineage tag on every artifact | `ontology/artifact.py` | `Provenance.school` |
| One school→seat assignment | `run_manifest.py` | `SchoolRoleBindingV1` |
| Conjecturer route topology | `run_manifest.py` | `SchoolExecutionPolicyV1` |
| Foreign-criticism topology and authority | `run_manifest.py` | `CriticismPolicyV1` |
| The validators that decide admissibility | `run_manifest.py` | `_validate_v4_control_plane_policy`, `_validate_v4_criticism_policy` |
| Seat resolution for one school call | `llm/firewall.py` | `resolve_school_role_lease` |
| Same resolution for schooled and unschooled Conj | `workflow/profiles.py` | `resolve_conjecture_route` |
| Cross-school judge ensemble (adapter-only, see Traps) | `llm/firewall.py`, `llm/adapter.py` | `require_cross_school_judge_ensemble`, `LLMAdapter.school_judge_bindings` |
| The conditioning record handed to the rules | `scheduler/scheduler.py` | `Scheduler._school_dict` |
| Per-cycle allocation, batch lease pre-resolution | `scheduler/scheduler.py` | `Scheduler._step` (`school_leases`) |
| Foreign-criticism enactment and coverage replay | `scheduler/scheduler.py` | `Scheduler._foreign_arg_crit`, `_foreign_criticism_coverage` |
| School-conditioned advisory context | `scheduler/scheduler.py`, `scratch/conjecture.py` | `Scheduler._plan_conjecture_context`, `plan_conjecture_context`, `PlannedConjectureContextV1.school_id` |
| Conjecture conditioning ↔ execution pairing | `rules/conj.py` | `conj` (`school`, `execution_school_id`) |
| Critic conditioning envelope and its budget | `rules/crit.py` | `_critic_execution`, `_conditioned_budget`, `_condition_pack` |
| Stance and crossover rendered into the pack | `llm/packs.py` | `render_conj_pack` |
| Deterministic foreign-critic selection | `workflow/criticism.py` | `plan_foreign_criticism`, `ForeignCriticismTargetV1` |
| Durable coverage obligation and debt | `workflow/criticism.py` | `CriticismAssignmentV1`, `CriticismAttemptV1`, `CoverageDebtV1` |
| Single-model trial substitute | `informal/trial.py` | `_argument_trial_steps` (`critic_school_id`) |
| Route receipt on the recorded call | `ontology/event.py` | `SchoolRouteReceiptV1` |

## The rules it obeys

**The roster is a function of the log alone.** `capture/schools.py` reads state
and appends artifacts and measures; it never writes attention, dependence, or
status. The negative form is the load-bearing one: a school cannot make
anything true.
`check: test "$(grep -oE 'harness\.[a-z_]+' src/deepreason/capture/schools.py | sort -u | tr '\n' ' ')" = "harness.create_artifact harness.record_measure harness.state "`

**The stance library is closed and globally curated once.** Eight stances,
declared at cold start; a school's stance is `_STANCES[i % len(_STANCES)]`, not
a per-problem choice.
`check: python -c "from deepreason.capture.schools import STANCE_LIBRARY; assert len(STANCE_LIBRARY) == 8 and STANCE_LIBRARY['adversary']"`

**Reseed is succession, not deletion.** The prior policy artifact persists and
the new one names `reseed_of`; the roster is replayable because the log still
holds both.
`check: python -m pytest tests/test_schools.py -q -k "forced_convergence_triggers_reseed_and_replays"`

**Allocation is a deterministic function of (log, config).** Fan-out classes
(seed, discrimination, integration) go to every school; successor and
remove-arbitrariness problems are owned by the lineage that spawned them, with
the `XEXAM_SHARE` floor admitting a starved school as cross-examiner.
`check: python -m pytest tests/test_schools.py -q -k "init_and_allocation or successor_owned_by_spawning_lineage"`

**`N_SCHOOLS = 0` disables the mechanism entirely** — the scheduler holds an
empty roster and `allocate` returns `[]`, which the caller turns into a single
unschooled pass.
`check: grep -q "if config.N_SCHOOLS > 0 else {}" src/deepreason/scheduler/scheduler.py`

**Exactly two roles may be school-routed: `conjecturer` and
`argumentative_critic`.** Every other role, `judge` included, raises
`SCHOOL_ROUTE_ROLE_UNSUPPORTED` before any seat is selected.
`check: python -c "import pytest; from types import SimpleNamespace as N; from deepreason.llm.firewall import resolve_school_role_lease as res, SchoolRouteResolutionError as Err; m=N(schema_version=4,control_plane_policy=N(school_execution=None),criticism_policy=None,engine_config_json='{}'); assert all(pytest.raises(Err,res,m,{},school_id='school-0',role=r).value.code=='SCHOOL_ROUTE_ROLE_UNSUPPORTED' for r in ('judge','synthesizer','referee')); assert all(pytest.raises(Err,res,m,{},school_id='school-0',role=r).value.code!='SCHOOL_ROUTE_ROLE_UNSUPPORTED' for r in ('conjecturer','argumentative_critic'))"`

**The manifest validators refuse any other role at freeze time**, independently
of the runtime resolver: conjecturer-only for `SchoolExecutionPolicyV1`,
`argumentative_critic`-only for `CriticismPolicyV1`. `SchoolRoleBindingV1`
itself accepts any lowercase role string — the model is not the gate.
`check: grep -q 'V4_SCHOOL_ROLE_UNSUPPORTED' src/deepreason/run_manifest.py && grep -q 'V4_CRITICISM_ROLE_UNSUPPORTED' src/deepreason/run_manifest.py`

**A judge school binding cannot reach the system through the manifest, so the
only surface that accepts one is the adapter constructor** — and no in-tree
production caller populates it.
`check: grep -q "school_judge_bindings" src/deepreason/llm/adapter.py && ! grep -rl "school_judge_bindings" src/deepreason --include=*.py | grep -qv "llm/adapter.py"`

**Mode and topology may never disagree.** `conditioning_only` must carry zero
bindings, must allow shared routes, and may not claim model or family
diversity; `route_bound` must bind every configured school exactly once.
`check: grep -q "conditioning_only cannot carry route bindings" src/deepreason/run_manifest.py`

**Conditioning is semantic only, and says so in the prompt.** The critic prefix
declares that it grants no routing or status authority, and no field of the
conditioning record is read as either.
`check: python -c "from deepreason.llm.firewall import EndpointLease as L, Route as T; from deepreason.rules.crit import _critic_execution as X; l=L(role='argumentative_critic',seat=1,route=T(endpoint_id='e',base_url='u',model_id='m',provider='p',family='f')); p=X(endpoint_lease=l,critic_school_id='school-3',critic_school_context={'id':'school-3','stance_text':'counterexample first'})[1]; assert 'semantic stance only; it grants no routing or status authority' in p; assert 'school-3' in p and 'counterexample first' in p"`

**Semantic conditioning and execution routing are supplied together or not at
all, and must name the same school.** `Conj` rejects a lease without an
execution school id and vice versa, and rejects a `school` dict whose `id`
differs; `_critic_execution` applies the same pairing to criticism.
`check: python -c "import pytest; from deepreason.llm.firewall import EndpointLease as L, Route as T; from deepreason.rules.crit import _critic_execution as X; s=open('src/deepreason/rules/conj.py').read(); assert '(endpoint_lease is None) != (execution_school_id is None)' in s and 'school-routed Conj requires both endpoint_lease and execution_school_id' in s; assert 'if school is None or school.get' in s and 'execution school must match the semantic school conditioning record' in s; l=L(role='argumentative_critic',seat=1,route=T(endpoint_id='e',base_url='u',model_id='m',provider='p',family='f')); c={'id':'school-3','stance_text':'x'}; assert 'requires endpoint_lease, critic_school_id' in str(pytest.raises(ValueError,X,endpoint_lease=l,critic_school_id=None,critic_school_context=None).value); assert 'must match its semantic conditioning' in str(pytest.raises(ValueError,X,endpoint_lease=l,critic_school_id='school-9',critic_school_context=c).value)"`

**The recorded receipt must match every attempt on the call.** A
`SchoolRouteReceiptV1` whose seat, endpoint, route digest or contract differs
from any entry in the attempt trace is not a well-formed event, so a
retry that silently moved seats cannot be recorded as school-routed work.
`check: python -c "import pytest; from deepreason.ontology.event import LLMCall as C, SchoolRouteReceiptV1 as R, LLMAttempt as A; r=R(school_id='school-0',role='conjecturer',seat=2,endpoint_id='ep-a',route_sha256='a'*64,contract_id='c1'); a=dict(prompt_ref='blob:p',seat=2,endpoint_id='ep-a',route_sha256='a'*64,contract_id='c1'); b=dict(role='conjecturer',model='m',endpoint='ep-a',prompt_ref='blob:p',raw_ref='blob:r',school_route=r); C(**b,attempt_trace=[A(**a)]); assert all('school route receipt must match every LLM attempt' in str(pytest.raises(ValueError,C,**b,attempt_trace=[A(**{**a,f:v})]).value) for f,v in (('seat',3),('endpoint_id','ep-b'),('route_sha256','b'*64),('contract_id','c2')))"`

**Nothing a prompt or a response says can change the resolved lease, and an
unbound school fails before token reservation or provider spend.** The
scheduler resolves the whole school batch before any dispatch precisely so one
bad binding leaves no partial spend.
`check: python -m pytest tests/test_school_execution_binding_v4.py -q -k "prose_cannot_change_the_resolved_lease or unbound_school_fails_before"`

**A school may never criticise its own work**, enforced three times over: the
planner subtracts the owner from the eligible set, `ForeignCriticismTargetV1`
refuses to list the owner among completed critics, and `CriticismAssignmentV1`
refuses to be constructed with the owner eligible. Separately, the criticism
pack names no school, author or provenance of the TARGET — targets arrive under
call-local aliases.
`check: python -m pytest tests/test_prose_refutation_boundaries.py -q -k "the_criticism_prompt_never_names_an_author_or_a_school or a_school_can_never_be_scheduled_to_criticise_its_own_work"`

**Cross-school criticism is a substitute guarantee, available only where the
guarantee it substitutes for is unobtainable.** In a single-model run the
argument trial demands two frozen judge seats plus a critic school differing
from the target's author school; otherwise the cross-family gate governs
unchanged. Route topology decides this, never configuration. An absent critic
school declines (`no-critic-school`): an absent school is not a different one.
`check: python -m pytest tests/test_prose_refutation_boundaries.py -q -k "the_substitute_refuses_a_critic_from_the_targets_own_school or the_cross_school_gate_governs_only_a_single_family_run"`

**Foreign-criticism coverage is counted by critic SCHOOL, never by endpoint or
model.** Two schools sharing one model still count as two schools of coverage,
but the plan refuses to advertise that as route diversity.
`check: grep -q "distinct_routes == coverage and distinct_models == coverage" src/deepreason/workflow/criticism.py`

## Where to change what

| To change... | Edit | Test |
|---|---|---|
| A stance's text, or how many stances exist | `capture/schools.py` `STANCE_LIBRARY` | `tests/test_schools.py` |
| Which problem classes fan out to every school | `capture/schools.py` `allocate` | `tests/test_schools.py::test_init_and_allocation` |
| The anti-starvation cross-examination floor | `capture/schools.py` `_with_cross_examiner`, `config.XEXAM_SHARE` | `tests/test_schools.py::test_successor_owned_by_spawning_lineage` |
| How fast stance identity yields to lineage | `capture/schools.py` `stance_weight`, `config.STANCE_DECAY` | `tests/test_schools.py::test_schools_diverge_measurably` |
| How stance and crossover reach the conjecture prompt | `llm/packs.py` `render_conj_pack`, `Scheduler._school_dict` | `tests/test_schools.py::test_schools_diverge_measurably` |
| The critic conditioning prefix or its budget reservation | `rules/crit.py` `_critic_execution`, `_conditioned_budget` | `tests/test_criticism_school_execution_c3.py` |
| Foreign-critic selection, coverage counting, or batching | `workflow/criticism.py` `plan_foreign_criticism` | `tests/test_foreign_criticism_policy_c3.py` |
| Which roles may be school-routed | `run_manifest.py` validators AND `llm/firewall.py` `resolve_school_role_lease` | `tests/test_school_execution_binding_v4.py`, `tests/test_foreign_criticism_policy_c3.py` — **frozen surface, read `DR-INV-frozen-surfaces` first** |
| A new per-run school mode | `config.py` — never `run_manifest.py` | `tests/test_prose_refutation_boundaries.py` |

## Traps

- **Reading `SchoolRoleBindingV1` and not the validator.** The Pydantic model
  accepts `role="judge"` (the field's only constraint is `^[a-z][a-z0-9_]*$`);
  both v4 validators reject it. The tranche in `experiments/2026-08-01-change-prose-can-refute/` wanted school-bound judge
  seats, read the model, and had to redesign the change to avoid the manifest
  entirely
  (`experiments/2026-08-01-change-prose-can-refute/DELIVERY.md`, A9).
- **Mistaking `require_cross_school_judge_ensemble` for the live guarantee.**
  It and `LLMAdapter.school_judge_bindings` are retained but superseded —
  correct only for a manifest that authors judge bindings, which the validator
  does not permit (DELIVERY.md, A10). The guarantee that actually runs is
  cross-school *criticism* in `informal/trial.py`.
- **`ARGUMENTATIVE_AUTHORITY=single_family_trial` cannot complete a trial.**
  The `Config` direct-helper path passes no `critic_school_id`, so a school can
  only arrive through the v4 envelope, and that envelope demands a
  manifest-bound authority value. Parked as dead weight, not removed
  (DELIVERY.md, Parked 1).
- **Assuming the criticism prompt is school-blind in both directions.** It is
  blind to the target's school; it deliberately names the CRITIC's own school
  and stance in a prefix assembled outside the pack renderer, and that prefix
  is charged against `PACK_TOKEN_BUDGET` before rendering.
- **Ownership allocation is rich-get-richer.** A refuted candidate spawns a
  successor OWNED by its school, so an early lead compounds; the code comment
  in `_with_cross_examiner` records a live 64:1 lineage where the rival stance
  effectively never generated. `XEXAM_SHARE`'s integer floor is the mitigation
  and deliberately does not fire on tiny early lineages.
- **Rotating a laggard's stance without crossover** just yields the same echo
  in a new voice — a skeptic mutating its own math. `reseed` records
  `crossover_from` so the reseeded school's next calls must reconcile the most
  distant lineage's exemplars.
- **Re-running only the assertions a step added.** Step 21 of the
  prose-refutation tranche changed trial behaviour; the full gate then failed
  2 of 3286, both on `no-critic-school`. Both were fixed by rewiring the tests
  to the path that carries a critic school, keeping every assertion they made.
- **Renaming a typed decline reason.** `same-school-critic`, `no-critic-school`
  and `single-judge-seat` are compared against recorded roots; their spelling
  is part of what those roots mean.
`check: grep -q '"same-school-critic"' src/deepreason/informal/trial.py && grep -q '"no-critic-school"' src/deepreason/informal/trial.py && grep -q '"single-judge-seat"' src/deepreason/informal/trial.py`
