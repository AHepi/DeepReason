<!-- DR-SEAM-manifest-x-schools -->
Verified-at: 9fa394d9
Verify: python tools/docs_verify.py
Owns: src/deepreason/run_manifest.py, src/deepreason/llm/firewall.py, src/deepreason/workflow/criticism.py, src/deepreason/v6_policy.py
Sides: DR-CON-schools, DR-SUB-manifest
Sweep: school_id && RunManifest|criticism_policy|school_execution

# Manifest x schools

## The agreement

A school promises the manifest one thing: an identifier of the form
`school-<n>`, minted by counting to `N_SCHOOLS`. It promises nothing else — no
stance, no lineage, no weight, no crossover pointer, nothing that would let the
manifest reason about what a school BELIEVES. The manifest promises back the
only authority a school cannot obtain any other way: a frozen seat. `role`,
`seat` and `endpoint_id` for one school are decided once, before the first
provider call, and no prompt, model response, allocation decision or scheduler
state can move them afterwards. Each side keeps what it can decide alone.
`capture/schools.py` decides who exists and who gets which problem, from the log
and the config; `run_manifest.py` decides who may call what, from the frozen
role matrix. Neither reads the other's state — the manifest's roster arithmetic
comes from `N_SCHOOLS` inside `engine_config_json`, never from the append-only
log, and the allocator has never heard of a route.

The asymmetry that makes this seam expensive: the manifest's half is
permanent. `DR-INV-frozen-surfaces` names manifest schemas *and their
validators* as frozen because every qualification subject digest and every
recorded root depends on exactly which school topologies were admissible. So
the whole force of this document is on admissibility, and admissibility does not
live where a reader expects it.

## Where it is expressed

| Site | File | Symbol | What it enforces |
|---|---|---|---|
| One assignment | `run_manifest.py` | `SchoolRoleBindingV1` | `^school-(0\|[1-9][0-9]*)$`, a lowercase role string, `seat` 0–1023, `endpoint_id` — the entire shared vocabulary |
| Conjecturer topology | `run_manifest.py` | `SchoolExecutionPolicyV1` | mode/topology consistency, canonical sorted unique bindings, the two route-diversity demands |
| Criticism topology and authority | `run_manifest.py` | `CriticismPolicyV1` | coverage minimum, batch cap, `observe_only`/`defended_trial`, shared-seat permission |
| Conjecturer admissibility | `run_manifest.py` | `_validate_v4_control_plane_policy` | conjecturer-only; every configured school bound exactly once; seat in range; `endpoint_id` equals the frozen route's |
| Criticism admissibility | `run_manifest.py` | `_validate_v4_criticism_policy` | `argumentative_critic`-only; coverage ≤ `N_SCHOOLS - 1`; the binding set equals the roster exactly; defended-trial judge topology |
| v6 authority narrowing | `run_manifest.py` | `_validate_v6_capability_policy` | `V6_DEFENDED_TRIAL_TRANSACTION_CONTRACT_REQUIRED` |
| Roster crossing | `run_manifest.py` | `engine_data.get("N_SCHOOLS")` | the only school knob any manifest validator reads out of `Config` |
| Dispatch resolution | `llm/firewall.py` | `resolve_school_role_lease` | re-derives the binding at call time and refuses if the runtime lease differs from the manifest route |
| Conjecture route | `workflow/profiles.py` | `resolve_conjecture_route` | schooled and unschooled `Conj` take the same manifest-owned seat |
| Foreign-critic plan | `workflow/criticism.py` | `plan_foreign_criticism` | the binding set — not the log roster — is the universe of eligible critic schools |
| Durable obligation | `workflow/criticism.py` | `compile_criticism_assignments` | v6 only; every obligation carries `manifest.sha256` |
| Restart re-authorization | `workflow/nonconjecture_recovery.py` | `_criticism_contract` | the frozen lease must equal `(binding.role, binding.seat, binding.endpoint_id)`, and `authority` must be `observe_only` |
| Referee seat | `referee.py` | `run_config_referee` | picks `min(binding.school_id)` off the manifest — the one school id chosen without consulting the roster |
| Qualification inventory | `run_manifest.py`, `cli/doctor.py` | `_route_seat_behavioral_contract_assignments`, `production_contract_pairs` | which critic seats get probed comes from the criticism bindings |
| Replay | `invariants.py` | `verify_root` (`school-route`, `foreign-criticism`) | every `SchoolRouteReceiptV1` re-derived against the bindings; coverage counted against `minimum_foreign_school_coverage` |
| The only in-tree author | `v6_policy.py` | `engaged_criticism_policy`, `PUBLIC_SCHOOL_COUNT` | binds all four public schools to the single critic seat, `observe_only` |

Two of those rows have no test anywhere in `tests/`: nothing imports
`resolve_conjecture_route` or `compile_criticism_assignments`, so their claims
are held up by this check and by the root sweep alone.

`check: python -c "from types import SimpleNamespace as N; import pytest; from deepreason.run_manifest import Route, CriticismPolicyV1 as C, SchoolRoleBindingV1 as B; from deepreason.workflow.criticism import plan_foreign_criticism as P, compile_criticism_assignments as K, ForeignCriticismTargetV1 as T; r=Route(endpoint_id='ep',base_url='http://x',model_id='m',provider='p',family='f'); pol=C(minimum_foreign_school_coverage=1,bindings=tuple(B(school_id='school-%d'%i,role='argumentative_critic',seat=0,endpoint_id='ep') for i in (0,1)),max_batch_size=4,target_eligibility='accepted_school_artifacts',authority='observe_only',allow_shared=True); D='a1b2'*16; m=lambda v: N(schema_version=v,criticism_policy=pol,roles={'argumentative_critic':(r,)},sha256=D,control_plane_policy=N(workflow_retry=N(max_workflow_retries=1))); plan=P(m(6),(T(target_id='A',owner_school_id='school-0'),)); assert [(x.critic_school_id,x.manifest_digest,x.seat,x.endpoint_id) for x in K(m(6),plan)]==[('school-1',D,0,'ep')]; assert str(pytest.raises(ValueError,K,m(5),plan).value)=='criticism obligation records require RunManifest v6'" && grep -q 'select_lease(leases, "conjecturer", 0)' src/deepreason/workflow/profiles.py && grep -q 'if lease.route != manifest.roles\["conjecturer"\]\[lease.seat\]:' src/deepreason/workflow/profiles.py && grep -q "WORKFLOW_ROUTE_LEASE_MISMATCH" src/deepreason/workflow/profiles.py && sh -c '! grep -rq "resolve_conjecture_route\|compile_criticism_assignments" tests/ --include=*.py'`

### The model is not the gate

`SchoolRoleBindingV1` is ONE model serving TWO policies with different role
rules, so the role restriction cannot live on the model — it would have to be
two different restrictions on one field. The model therefore accepts any
lowercase identifier, `judge` included, and the refusal sits in each policy's
validator: `V4_SCHOOL_ROLE_UNSUPPORTED` for conjecturer execution,
`V4_CRITICISM_ROLE_UNSUPPORTED` for criticism. A 2026-08-01 tranche wanted
school-bound judge seats, read the model, and had to redesign the change to
avoid the manifest entirely
(`experiments/2026-08-01-change-prose-can-refute/DELIVERY.md`, A9).

`check: python -c "import pytest; from types import SimpleNamespace as N; from deepreason.run_manifest import SchoolRoleBindingV1 as B, CriticismPolicyV1 as C, SchoolExecutionPolicyV1 as S, _validate_v4_criticism_policy as VC, _validate_v4_control_plane_policy as VS, Route; r=Route(endpoint_id='ep',base_url='http://x',model_id='m',provider='p',family='f'); j=B(school_id='school-0',role='judge',seat=0,endpoint_id='ep'); assert j.role=='judge'; m=N(criticism_policy=C(minimum_foreign_school_coverage=1,bindings=(j,),max_batch_size=1,target_eligibility='accepted_school_artifacts',authority='observe_only',allow_shared=True),control_plane_policy=N(mode='active_inquiry'),engine_config_json='{\"N_SCHOOLS\": 2}',roles={'argumentative_critic':(r,),'judge':(r,)}); assert 'V4_CRITICISM_ROLE_UNSUPPORTED' in str(pytest.raises(ValueError,VC,m).value); k=N(control_plane_policy=N(school_execution=S(mode='route_bound',bindings=(j,),allow_shared=True,require_distinct_models=False,require_distinct_families=False)),engine_config_json='{\"N_SCHOOLS\": 1}',roles={'judge':(r,),'conjecturer':(r,)}); assert 'V4_SCHOOL_ROLE_UNSUPPORTED' in str(pytest.raises(ValueError,VS,k).value)"`

The same split runs the other way for `SchoolExecutionPolicyV1`: mode/topology
consistency IS on the model (`conditioning_only` may carry no bindings), while
completeness is only in the validator (`route_bound` with zero bindings is a
perfectly valid model and a rejected manifest). Neither half is the rule.

The `V4_` prefixes are historical, not conditional: both validators run for
every schema version ≥ 4, and only version 6 loads at all. A manifest that
reaches a run has passed both.

`check: python -c "import pytest; from types import SimpleNamespace as N; from deepreason.run_manifest import SchoolExecutionPolicyV1 as S, SchoolRoleBindingV1 as B, _validate_v4_control_plane_policy as V, Route; b=B(school_id='school-0',role='conjecturer',seat=0,endpoint_id='ep'); mk=lambda **kw: S(**{'mode':'route_bound','bindings':(),'allow_shared':True,'require_distinct_models':False,'require_distinct_families':False, **kw}); assert 'conditioning_only cannot carry route bindings' in str(pytest.raises(Exception,mk,mode='conditioning_only',bindings=(b,)).value); r=Route(endpoint_id='ep',base_url='http://x',model_id='m',provider='p',family='f'); mf=lambda p,n=1: N(control_plane_policy=N(school_execution=p),engine_config_json='{\"N_SCHOOLS\": %d}'%n,roles={'conjecturer':(r,)}); assert str(pytest.raises(ValueError,V,mf(mk())).value).startswith('V4_SCHOOL_BINDING_INCOMPLETE'); V(mf(mk(bindings=(b,)))); V(mf(mk(mode='conditioning_only'),9)); s=open('src/deepreason/run_manifest.py').read(); i=s.index('if self.schema_version >= 4:'); assert '_validate_v4_control_plane_policy(self)' in s[i:i+400] and '_validate_v4_criticism_policy(self)' in s[i:i+400]" && grep -q "if 1 <= schema_version <= 5:" src/deepreason/run_manifest.py && grep -q "class UnsupportedRunManifestVersionError" src/deepreason/run_manifest.py`

### The criticism validator's arithmetic

Foreign criticism is impossible below two schools and refuses to pretend
otherwise: `minimum_foreign_school_coverage` is `ge=1` on the model, and the
validator compares it against `N_SCHOOLS - 1`. So `N_SCHOOLS` of 0 or 1 forbids
any criticism policy at all, rather than compiling one that can never be
satisfied. Above that, the binding set must equal the roster exactly — missing
and extra are both `V4_CRITICISM_BINDING_INCOMPLETE`, an unknown id is
`V4_CRITICISM_SCHOOL_UNKNOWN` — and `seat` and `endpoint_id` must BOTH name the
same frozen route, because a school is not a property of a route and the pair is
the only thing tying the two identities together.

`check: python -c "import pytest; from types import SimpleNamespace as N; from deepreason.run_manifest import SchoolRoleBindingV1 as B, CriticismPolicyV1 as C, _validate_v4_criticism_policy as V, Route; r=Route(endpoint_id='ep',base_url='http://x',model_id='m',provider='p',family='f'); ok=lambda i,s=0,e='ep': B(school_id='school-%d'%i,role='argumentative_critic',seat=s,endpoint_id=e); m=lambda n,bs,cov=1: N(criticism_policy=C(minimum_foreign_school_coverage=cov,bindings=bs,max_batch_size=1,target_eligibility='accepted_school_artifacts',authority='observe_only',allow_shared=True),control_plane_policy=N(mode='active_inquiry'),engine_config_json='{\"N_SCHOOLS\": %d}'%n,roles={'argumentative_critic':(r,)}); V(m(2,(ok(0),ok(1)))); code=lambda *a: str(pytest.raises(ValueError,V,m(*a)).value).split(':')[0]; assert code(0,())=='V4_CRITICISM_FOREIGN_COVERAGE_IMPOSSIBLE'; assert code(1,(ok(0),))=='V4_CRITICISM_FOREIGN_COVERAGE_IMPOSSIBLE'; assert code(2,(ok(0),))=='V4_CRITICISM_BINDING_INCOMPLETE'; assert code(2,(ok(0),ok(1),ok(2)))=='V4_CRITICISM_SCHOOL_UNKNOWN'; assert code(2,(ok(0),ok(1,0,'other')))=='V4_CRITICISM_ENDPOINT_MISMATCH'; assert code(2,(ok(0),ok(1,5)))=='V4_CRITICISM_SEAT_OUT_OF_RANGE'"`

### The bindings are the universe at runtime too

`plan_foreign_criticism` selects foreign critics from the manifest binding set,
not from the log roster, and refuses a target whose owning school has no
binding. The two rosters agree only because both are derived from `N_SCHOOLS`;
the planner does not assume it, it fails closed.

`check: python -c "import pytest; from types import SimpleNamespace as N; from deepreason.run_manifest import CriticismPolicyV1 as C, SchoolRoleBindingV1 as B, Route; from deepreason.workflow.criticism import plan_foreign_criticism as P, ForeignCriticismTargetV1 as T; r=Route(endpoint_id='ep',base_url='http://x',model_id='m',provider='p',family='f'); pol=C(minimum_foreign_school_coverage=1,bindings=tuple(B(school_id='school-%d'%i,role='argumentative_critic',seat=0,endpoint_id='ep') for i in (0,1)),max_batch_size=4,target_eligibility='accepted_school_artifacts',authority='observe_only',allow_shared=True); m=N(criticism_policy=pol,roles={'argumentative_critic':(r,)}); assert [(a.critic_school_id,a.seat,a.endpoint_id) for t in P(m,(T(target_id='A',owner_school_id='school-0'),)).targets for a in t.assignments]==[('school-1',0,'ep')]; assert str(pytest.raises(ValueError,P,m,(T(target_id='A',owner_school_id='school-2'),)).value).startswith('V4_CRITICISM_TARGET_SCHOOL_UNKNOWN'); assert str(pytest.raises(ValueError,P,N(criticism_policy=None,roles={}),()).value)=='V4_CRITICISM_POLICY_REQUIRED'"`

The binding is then re-checked at three further distances from the freeze: at
dispatch (`resolve_school_role_lease`, with its own `SCHOOL_ROUTE_*` codes), at
restart (`_criticism_contract`, which also refuses to recover anything but
`observe_only`), and at replay (`verify_root`).

Three is the count of places that RE-DERIVE from the bindings, and the `Sweep:`
header flags five more files that compare `school_id` without doing so. They are
named here so the sweep resolves and so a reader does not mistake them for a
fourth authority. `src/deepreason/ontology/event.py` and
`src/deepreason/rules/conj.py` enforce that a school-route receipt and a
conjecture-context binding name ONE school — that is `DR-SEAM-schools-x-scratch`,
not this seam. `src/deepreason/rules/crit.py` compares the prompt-side critic
school block to the dispatched critic id and mediates no binding at all.
`src/deepreason/workflow/replay.py` and `src/deepreason/workflow/shadow.py`
compare the receipt against the DURABLE WORK ORDER's frozen `school_id` and
`route_lease`, never against `criticism_policy.bindings`: they INHERIT the
binding through the authorization that minted the work order rather than
re-deriving it (`DR-SUB-workflow`). None of the five reads a manifest school
policy, which is exactly why changing one is not enough to change what they
enforce.

`check: grep -q "school_receipt.school_id != work.school_id" src/deepreason/workflow/replay.py && grep -q "actual_school != ticket.work_order.school_id" src/deepreason/workflow/shadow.py && grep -q "context.school_id != receipt.school_id" src/deepreason/ontology/event.py && grep -q "binding.school_id == school_id" src/deepreason/rules/conj.py && grep -q 'critic_school_context.get("id") != critic_school_id' src/deepreason/rules/crit.py && sh -c '! grep -qE "criticism_policy|school_execution|\.bindings" src/deepreason/workflow/replay.py src/deepreason/workflow/shadow.py src/deepreason/rules/crit.py src/deepreason/rules/conj.py src/deepreason/ontology/event.py'`

`check: python -c "import pytest; from types import SimpleNamespace as N; from deepreason.run_manifest import Route, CriticismPolicyV1 as C, SchoolRoleBindingV1 as B; from deepreason.llm.firewall import resolve_school_role_lease as R, EndpointLease as L, SchoolRouteResolutionError as E; r=Route(endpoint_id='ep',base_url='http://x',model_id='m',provider='p',family='f'); r2=Route(endpoint_id='ep',base_url='http://y',model_id='m2',provider='p',family='f'); r3=Route(endpoint_id='other',base_url='http://x',model_id='m',provider='p',family='f'); pol=lambda *ids: C(minimum_foreign_school_coverage=1,bindings=tuple(B(school_id=i,role='argumentative_critic',seat=0,endpoint_id='ep') for i in ids),max_batch_size=1,target_eligibility='accepted_school_artifacts',authority='observe_only',allow_shared=True); m=lambda p,rt: N(schema_version=6,control_plane_policy=N(school_execution=None),criticism_policy=p,engine_config_json='{\"N_SCHOOLS\": 2}',roles={'argumentative_critic':(rt,)}); ls=lambda rt: {'argumentative_critic':(L(role='argumentative_critic',seat=0,route=rt),)}; code=lambda *a,**k: pytest.raises(E,R,*a,**k).value.code; assert R(m(pol('school-0','school-1'),r),ls(r),school_id='school-0',role='argumentative_critic').route is r; assert code(m(pol('school-0','school-1'),r),ls(r2),school_id='school-0',role='argumentative_critic')=='SCHOOL_ROUTE_LEASE_MISMATCH'; assert code(m(pol('school-0','school-1'),r3),ls(r3),school_id='school-0',role='argumentative_critic')=='SCHOOL_ROUTE_ENDPOINT_MISMATCH'; assert code(m(pol('school-0'),r),ls(r),school_id='school-1',role='argumentative_critic')=='SCHOOL_ROUTE_BINDING_MISSING'; assert code(m(pol('school-0','school-1'),r),ls(r),school_id='school-0',role='judge')=='SCHOOL_ROUTE_ROLE_UNSUPPORTED'" && python -m pytest tests/test_school_execution_binding_v4.py -q -k "unbound_school_fails_before or resolves_all_school_bindings_before_any_dispatch"`

`check: python -c "import hashlib,pytest; from types import SimpleNamespace as N; from deepreason.canonical import canonical_json; from deepreason.run_manifest import CriticismPolicyV1 as C, SchoolRoleBindingV1 as B; from deepreason.workflow.nonconjecture_recovery import _criticism_contract as K, NonConjectureRecoveryAuthorityError as A; pol=lambda auth: C(minimum_foreign_school_coverage=1,bindings=tuple(B(school_id='school-%d'%i,role='argumentative_critic',seat=0,endpoint_id='ep') for i in (0,1)),max_batch_size=1,target_eligibility='accepted_school_artifacts',authority=auth,allow_shared=True); pay=lambda sid: {'schema':'criticism.semantic-task.v1','critic_school_id':sid}; prep=lambda p,seat=0,ep='ep': N(trigger_ref='criticism:'+hashlib.sha256(canonical_json(p)).hexdigest(),contract_id='c1',route_lease=N(role='argumentative_critic',seat=seat,endpoint_id=ep),target_refs=('T',),input_refs=('I',),attempt_index=0); man=lambda auth='observe_only': N(control_plane_policy=N(contract_versions=N(batch_critic_contract='c1')),criticism_policy=pol(auth)); msg=lambda m,p,pr: str(pytest.raises(A,K,None,m,None,pr,p).value); p=pay('school-0'); q=pay('school-9'); assert msg(man(),p,prep(p))=='critic targets differ from preparation'; assert msg(man('defended_trial'),p,prep(p))=='critic authority is not recoverable'; assert msg(man(),p,prep(p,seat=1))=='critic route differs from school binding'; assert msg(man(),p,prep(p,ep='other'))=='critic route differs from school binding'; assert msg(man(),q,prep(q))=='critic school has no manifest binding'" && grep -q '"referee school has no manifest binding"' src/deepreason/workflow/nonconjecture_recovery.py && grep -q "critic_school_id = min(" src/deepreason/referee.py && sh -c '! grep -q "deepreason.capture" src/deepreason/referee.py' && python -m pytest tests/test_v6_nonconjecture_recovery.py -q -k "recovered_criticism_applies_canonical_effect_exactly_once or authority_mismatch_fails_closed"`

`check: grep -q "receipt has no unique manifest binding" src/deepreason/invariants.py && grep -q "criticism_policy.minimum_foreign_school_coverage" src/deepreason/invariants.py && grep -q "^def verify_root" src/deepreason/invariants.py && test "$(grep -c 'expected_seat = matches\[0\]\.seat' src/deepreason/invariants.py)" = 2 && test "$(grep -c 'expected_endpoint = matches\[0\]\.endpoint_id' src/deepreason/invariants.py)" = 2 && grep -q "if receipt.seat != expected_seat:" src/deepreason/invariants.py && grep -q "if expected_endpoint is not None and receipt.endpoint_id != expected_endpoint:" src/deepreason/invariants.py && python -m pytest tests/test_school_execution_binding_v4.py -q -k "receipt_survives_replay" && python -m pytest tests/test_v6_controller3_replay_verification.py -q -k "route_lease or route_differing" && python -m pytest "tests/test_incident_wave_a_v2_fixtures.py::test_incident_derived_roots_receive_expected_v2_dimensions[A1]" -q`

### A school binding is priced in provider calls

`_route_seat_behavioral_contract_assignments` derives critic pairs from the
criticism bindings, so the binding topology decides the qualification pair
inventory, which decides the subject digest, which decides whether the battery
reruns. Three schools on three seats is eight pairs; the same three schools
sharing one seat is four. Moving a school to a different seat is therefore not a
routing tweak — it is a cache miss and a full battery (`DR-SUB-manifest`).

`check: python -c "from deepreason.config import Config; from deepreason.run_manifest import compile_run_manifest, CriticismPolicyV1 as C, SchoolRoleBindingV1 as B; from deepreason.cli.doctor import production_contract_pairs as P; from tests.test_v6_transaction_qualification import STAMP, _control, _criticism_policy, _route; roles={'conjecturer':[_route('conjecturer-route')],'argumentative_critic':[_route('critic-route-%d'%s,s) for s in range(3)]}; comp=lambda p: compile_run_manifest(Config(N_SCHOOLS=3,roles=roles),schema_version=6,workload_profile='text',rubric_policy='forbid',compiled_at=STAMP,control_plane_policy=_control(),criticism_policy=p,run_input_digest='a'*64); shared=C(minimum_foreign_school_coverage=2,bindings=tuple(B(school_id='school-%d'%i,role='argumentative_critic',seat=0,endpoint_id='critic-route-0') for i in range(3)),max_batch_size=4,target_eligibility='accepted_school_artifacts',authority='observe_only',allow_shared=True); seats=lambda m: sorted({x.seat for x in P(m) if x.role=='argumentative_critic'}); a,b=comp(_criticism_policy()),comp(shared); assert seats(a)==[0,1,2] and len(P(a))==8; assert seats(b)==[0] and len(P(b))==4; assert a.sha256!=b.sha256"`

The one in-tree author of a criticism policy hard-codes the roster size it
expects to meet. `PUBLIC_SCHOOL_COUNT` and `Config().N_SCHOOLS` are two
constants in two modules that must be equal or every public run fails at
compile with `V4_CRITICISM_BINDING_INCOMPLETE`.

`check: python -c "from deepreason.config import Config; from deepreason.v6_policy import PUBLIC_SCHOOL_COUNT as P, engaged_criticism_policy as E; assert Config().N_SCHOOLS==P; p=E('ep'); assert {b.school_id for b in p.bindings}=={'school-%d'%i for i in range(P)}; assert {b.role for b in p.bindings}=={'argumentative_critic'} and {b.seat for b in p.bindings}=={0}; assert p.authority=='observe_only' and p.allow_shared and p.minimum_foreign_school_coverage==1" && grep -q "criticism_policy=engaged_criticism_policy(" src/deepreason/preparation.py && grep -q "config.ENGAGED_CRITICISM_AUTHORITY" src/deepreason/preparation.py`

## What is deliberately absent

**The manifest cannot describe what a school is.** No stance, no lineage, no
weight, no crossover pointer, no per-school budget, no per-school status
authority. `SchoolRoleBindingV1` has exactly four fields and `extra="forbid"`,
and the words `stance`, `lineage`, `crossover` and `reseed` do not occur in
`run_manifest.py` at all. This is the whole reason the two authorities stay
separable: a manifest field is permanent and replay-visible, so anything that
lands there stops being a semantic knob and becomes evidence. The AST clause
below is a tripwire: exactly four top-level definitions in `run_manifest.py`
carry `school` or `criticism` in their names, and a fifth is the change this
document exists to price.

`check: python -c "import ast; from deepreason.run_manifest import SchoolRoleBindingV1 as B, SchoolExecutionPolicyV1 as S, CriticismPolicyV1 as C; assert set(B.model_fields)=={'school_id','role','seat','endpoint_id'}; assert set(S.model_fields)=={'mode','bindings','allow_shared','require_distinct_models','require_distinct_families'}; assert set(C.model_fields)=={'minimum_foreign_school_coverage','bindings','max_batch_size','target_eligibility','authority','allow_shared'}; assert all(m.model_config['extra']=='forbid' and m.model_config['frozen'] for m in (B,S,C)); t=ast.parse(open('src/deepreason/run_manifest.py').read()); assert [n.name for n in t.body if isinstance(n,(ast.ClassDef,ast.FunctionDef)) and ('chool' in n.name or 'riticism' in n.name)]==['SchoolRoleBindingV1','SchoolExecutionPolicyV1','CriticismPolicyV1','_validate_v4_criticism_policy']" && grep -q "^STANCE_LIBRARY" src/deepreason/capture/schools.py && grep -q "distinct_routes == coverage and distinct_models == coverage" src/deepreason/workflow/criticism.py && sh -c '! grep -qiE "\bstance\b|lineage|crossover|reseed" src/deepreason/run_manifest.py'`

**The school side cannot describe what a route is.** `capture/schools.py`
imports `json`, `copy`, `typing`, `collections.abc`, `dataclasses`,
`deepreason.canonical` and `deepreason.ontology` (including its `frozen`
submodule) — not the manifest, not the firewall, not `Config`'s type. The
non-`json`/`ontology` imports (added in rung 3's school-population registry,
`DR-SEAM-schools-x-scheduler`) are stdlib utilities and a canonical-hashing
helper already permitted elsewhere in the codebase; none of them can reach a
route. The set is pinned EXACTLY rather than by exclusion, so a
new import is a deliberate decision that updates this list — `contextlib` was
added by rung 5 for `population_backend`, and updating the pin here was the
moment to re-ask whether it could reach a route. It cannot. `roster`, `allocate`, `reseed` and `crossover_exemplars` therefore
cannot consult a binding even accidentally, and allocation cannot become
route-aware without a new import that names the manifest, the firewall, or
`Config` itself. The two sides share one string and its spelling;
`school-01` and `School-0` are rejected by the binding pattern, so an id
that the roster could not have minted cannot enter the manifest either.

`check: python -c "import ast; t=ast.parse(open('src/deepreason/capture/schools.py').read()); mods={n.module for n in ast.walk(t) if isinstance(n,ast.ImportFrom)}|{a.name for n in ast.walk(t) if isinstance(n,ast.Import) for a in n.names}; assert mods=={'json','copy','typing','contextlib','collections.abc','dataclasses','deepreason.canonical','deepreason.ontology','deepreason.ontology.frozen'}, mods; assert not mods & {'deepreason.run_manifest','deepreason.llm.firewall','deepreason.config'}; import pytest; from deepreason.run_manifest import SchoolRoleBindingV1 as B; mk=lambda s: B(school_id=s,role='argumentative_critic',seat=0,endpoint_id='e'); assert [mk('school-%d'%i).school_id for i in range(4)]==['school-0','school-1','school-2','school-3']; assert all(pytest.raises(Exception,mk,s) for s in ('school-01','School-0','skeptic','school-'))" && grep -q 'school_id = f"school-{i}"' src/deepreason/capture/schools.py && sh -c '! grep -q "deepreason\.capture" src/deepreason/run_manifest.py'`

**Only `N_SCHOOLS` crosses from `Config`.** `engine_config_json` is the whole
engine config, so `XEXAM_SHARE` and `STANCE_DECAY` are physically present in the
manifest bytes — and no validator reads them. Allocation pressure and stance
decay stay run-local knobs; only the roster SIZE is an admissibility input. A
validator that started reading `XEXAM_SHARE` would make a scheduling heuristic
into frozen evidence.

`check: grep -q 'engine_data.get("N_SCHOOLS")' src/deepreason/run_manifest.py && grep -qE "^    N_SCHOOLS: int" src/deepreason/config.py && grep -qE "^    XEXAM_SHARE: float" src/deepreason/config.py && grep -qE "^    STANCE_DECAY:" src/deepreason/config.py && sh -c '! grep -qE "XEXAM_SHARE|STANCE_DECAY" src/deepreason/run_manifest.py'`

**There is no manifest surface for a judge school, so the cross-school judge
ensemble is unreachable.** `require_cross_school_judge_ensemble` filters
`binding.role == "judge"`, and no manifest can carry such a binding — both
validators refuse it. The function and `LLMAdapter.school_judge_bindings` are
retained, not live; the guarantee that actually runs is cross-school
*criticism* in `informal/trial.py` (`DR-CON-schools`). Deleting the dead pair is
a change to a public surface, not a cleanup; widening a validator to feed it is
a frozen-surface change.

`check: grep -q 'binding.role == "judge"' src/deepreason/llm/firewall.py && grep -q "def require_cross_school_judge_ensemble" src/deepreason/llm/firewall.py && grep -q "V4_CRITICISM_ROLE_UNSUPPORTED" src/deepreason/run_manifest.py && grep -q "V4_SCHOOL_ROLE_UNSUPPORTED" src/deepreason/run_manifest.py && grep -q "school_judge_bindings" src/deepreason/llm/adapter.py`

**`authority="defended_trial"` is a Literal value no loadable manifest can
hold.** The field offers two values; `_validate_v6_capability_policy` refuses
the second, and only v6 loads. The v4 defended-trial topology rules (a
`defender` route, two judge seats from distinct families) are live code guarding
a state the current schema cannot reach. This is the same trap as the judge
role, one level up: reading the `Literal` gives you two options and the
validators give you one.

`check: python -c "import typing; from deepreason.run_manifest import CriticismPolicyV1 as C; assert typing.get_args(C.model_fields['authority'].annotation)==('observe_only','defended_trial')" && grep -q "V4_CRITICISM_CROSS_FAMILY_JUDGES_REQUIRED" src/deepreason/run_manifest.py && python -m pytest tests/test_v6_manifest_defended_trial.py -q`

**`route_bound` conjecturer execution has no in-tree author.** Every
`SchoolExecutionPolicyV1` constructed anywhere in `src/` is
`conditioning_only`. The readers, the replay validation and the tests all exist;
only an operator-supplied `control_plane_policy` argument to
`compile_run_manifest` can produce a route-bound run. So schools' routing
authority is real, exercised offline, and dormant in every shipped
configuration — do not read the dormancy as evidence the path is dead.

`check: python -c "import ast,pathlib; modes=[(p.name, next((k.value.value for k in n.keywords if k.arg=='mode'), None)) for p in pathlib.Path('src/deepreason').rglob('*.py') for n in ast.walk(ast.parse(p.read_text())) if isinstance(n,ast.Call) and isinstance(n.func,ast.Name) and n.func.id=='SchoolExecutionPolicyV1']; assert modes and all(m=='conditioning_only' for _,m in modes), modes" && grep -q 'mode: Literal\["conditioning_only", "route_bound"\]' src/deepreason/run_manifest.py`

**Criticism cannot demand route diversity.** `require_distinct_models` and
`require_distinct_families` exist on the conjecturer policy only; the criticism
policy has `allow_shared` and nothing else. Two schools sharing one model still
count as two schools of coverage, and the planner explicitly refuses to
advertise that as route diversity. The absence is the design: coverage is a
claim about SCHOOLS, and adding a diversity flag to `CriticismPolicyV1` would
make it silently a claim about routes. Both halves — the absent fields and the
planner's refusal — are pinned by the first check in this section.

## How to change it

The binding is frozen into canonical manifest bytes, then into a run root, then
into receipts that `verify_root` re-derives. Everything downstream of the freeze
is a reader, and readers may be fixed; the freeze may not.

1. **Decide first whether the change needs the manifest at all.** A per-run
   school mode belongs on `Config` — `DR-INV-frozen-surfaces` states the
   precedent and the reason. A manifest field is permanent; a `Config` field is
   invisible to replay. The 2026-08-01 tranche's redesign was exactly this move.
2. **If it does, change the model and the validator in one edit.** They are two
   halves of one rule and the validator is the half that decides. A widened
   validator admits manifests that previously failed, which changes what
   "replay-valid" means for the class, and a narrowed one can invalidate a
   recorded root — wrong by definition.
3. **Move the runtime resolver with it.** `resolve_school_role_lease` re-derives
   the same restriction independently (`SCHOOL_ROUTE_ROLE_UNSUPPORTED`). A
   manifest that admits a role the resolver refuses compiles, qualifies, and
   then dies at dispatch after spending the battery.
4. **Then the three re-checks, together:** `plan_foreign_criticism`'s eligible
   set, `_criticism_contract`'s restart authorization, and `verify_root`'s
   `school-route` and `foreign-criticism` derivations. Change one and a run
   dispatches, completes, and fails its own replay.
5. **Reprice before you commit.** Any change to the binding topology or the
   models changes the qualification subject digest: ~14 min and ~1160 provider
   calls per affected home. Check whether the change moves `production_contract_pairs`
   before assuming it is free.
6. **Finish with the root sweep.** `DR-INV-frozen-surfaces` names the
   instrument. Under `experiments/`, some recorded roots are pre-v6 and raise
   `UnsupportedRunManifestVersionError` as the expected baseline; a further
   non-empty set carries no `run-manifest.json` at all and is NOT part of
   that first set. Conflating them — counting "roots older than v6" — gives a
   strictly larger and wrong baseline. Both sets are non-empty and the three
   kinds partition the roots, which is what the check asserts; it pins no
   count, because every tranche that commits a run root moves them. As a
   dated measurement rather than a live claim, at `e6a11428` on 2026-08-05
   the figures under `experiments/` were 44 roots — 30 v6, 11 raising, 3
   without a manifest, so the wrong baseline would have been 14. Do not
   re-pin them.

`check: python -c "exec(\"import pathlib\nfrom deepreason.run_manifest import load_run_manifest as L, UnsupportedRunManifestVersionError as U\nroots=sorted({p.parent for p in pathlib.Path('experiments').rglob('log.jsonl')})\nassert len(roots)>40, len(roots)\nv=0\nn=0\nm=0\nfor r in roots:\n    p=r/'run-manifest.json'\n    if not p.exists():\n        m+=1\n        continue\n    try:\n        L(p)\n        v+=1\n    except U: n+=1\n    except Exception: pass\nassert n>0 and m>0, (n,m)\nassert n+m>n\nassert v+n+m==len(roots), (v,n,m,len(roots))\")"`

**Trap — this check pinned a census until 2026-08-05, and a census
expires.** It asserted `len(roots)==42` and `(n,m)==(11,3)`, which stopped
being true the moment rung 5 committed its live A/B arm roots (`f6d41bff`)
— correct evidence, correctly committed. The claim the prose makes (the two
sets are different and neither is empty) never stopped being true while the
check was red. Fixed in
`experiments/2026-08-05-fix-expired-census-readers/` along with three
sibling instances: `SEAM-harness-x-verification`'s 45/28/14/3 check and the
two `tests/test_module_fingerprints.py` tests. When you need a number in
this document, write it as a dated measurement with its commit, never as an
assertion.

What breaks first, cheapest first: `tests/test_run_manifest_v4.py` (topology
admissibility, sub-second) and `tests/test_foreign_criticism_policy_c3.py`
(coverage arithmetic and planning); then
`tests/test_school_execution_binding_v4.py` for dispatch and receipt replay;
then `tests/test_v6_manifest_defended_trial.py` and
`tests/test_v6_nonconjecture_recovery.py`; then
`tests/test_reusable_qualification.py` if the subject digest moved. Only after
those, on a later run, `verify_root` — the expensive one, because by then the
root is committed.

`check: python -m pytest tests/test_run_manifest_v4.py tests/test_foreign_criticism_policy_c3.py -q`

## Traps

- **Grep for "school" and "RunManifest" together returns 21 files and still
  misses a third of the agreement.** Nine files carry it: the four in `Owns:`
  plus five downstream enforcers — `workflow/profiles.py`,
  `workflow/nonconjecture_recovery.py`, `referee.py`, `cli/doctor.py`,
  `invariants.py` — which this seam describes but does not own
  (`invariants.py` belongs to `DR-INV-frozen-surfaces`). Only SIX of the nine
  name both words. `referee.py` and `invariants.py` reach the policy through
  `manifest.criticism_policy` without ever spelling `RunManifest`, and
  `cli/doctor.py` projects critic seats without ever spelling `school`. The 21
  meanwhile include files like `harness.py` and `scheduler/scheduler.py` that
  mediate no binding at all, while `report.py`, `findings.py`, `jolts.py` and
  `skills/adoption.py` reach schools only through `Provenance.school` or the
  roster and do not name a manifest at all. Starting from grep costs a day and
  still comes up short in both directions; the table above is the answer.
`check: test "$(for f in $(grep -rl school src/deepreason --include=*.py); do grep -ql RunManifest "$f" && echo x; done | wc -l)" = 21 && test "$(for f in run_manifest.py llm/firewall.py workflow/criticism.py v6_policy.py workflow/profiles.py workflow/nonconjecture_recovery.py referee.py cli/doctor.py invariants.py; do p=src/deepreason/$f; grep -ql school $p && grep -ql RunManifest $p && echo $f; done | sort | tr '\n' ' ')" = "llm/firewall.py run_manifest.py v6_policy.py workflow/criticism.py workflow/nonconjecture_recovery.py workflow/profiles.py " && grep -q "manifest.criticism_policy" src/deepreason/referee.py && grep -q "criticism_policy.minimum_foreign_school_coverage" src/deepreason/invariants.py && grep -q "argumentative_critic" src/deepreason/cli/doctor.py`
- **Reading a model and not its validator.** The recorded instance is A9 of
  `experiments/2026-08-01-change-prose-can-refute/DELIVERY.md`: a tranche read
  `SchoolRoleBindingV1`, saw that `role` accepts `judge`, designed school-bound
  judge seats, and had to redesign the change to avoid the manifest. Both `role`
  and `authority` have this shape today. Read the validator FIRST; the model is
  the union of what two policies need, not the rule either one enforces.
- **The `V4_` prefix does not mean "only schema 4".** Both v4 validators run on
  every v6 manifest, which is the only kind that loads. A change "scoped to v4"
  is a change to every run.
- **`V4_CRITICISM_TARGET_SCHOOL_UNKNOWN` has no test.** Grepping `tests/` for
  the code returns nothing; the guard in `plan_foreign_criticism` is exercised
  only by the check in this document and by the root sweep. It is the point
  where the log-derived roster and the manifest binding set could disagree, so
  treat it as protected by replay, not by the gate.
- **A binding topology change is a provider-spend change.** Moving three schools
  from three critic seats onto one shared seat halves the qualification pair
  inventory (8 → 4) and changes the manifest digest, so the cached "qualified"
  verdict no longer applies. Budget the battery before proposing the routing
  change, not after.
- **`N_SCHOOLS` below 2 forbids a criticism policy outright.** It does not
  compile a policy that quietly never fires: `minimum_foreign_school_coverage`
  is `ge=1` and the validator compares it against `N_SCHOOLS - 1`, so a
  single-school run with the public preset fails at compile. Lowering
  `N_SCHOOLS` to save tokens is not a local edit.
- **`allow_shared=True` is the shipped default, and shared seats are why
  coverage is counted by school.** All four public schools sit on one critic
  seat, so endpoint identity carries no information about which school spoke;
  the durable receipt names both, and only the school id counts toward coverage.
