<!-- DR-SEAM-llm-x-rules -->
Verified-at: b41c5cf10
Verify: python tools/docs_verify.py
Owns: src/deepreason/llm/adapter.py, src/deepreason/llm/firewall.py, src/deepreason/llm/packs.py, src/deepreason/llm/wire.py, src/deepreason/llm/contracts.py, src/deepreason/rules/conj.py, src/deepreason/rules/crit.py
Sides: DR-SUB-llm, DR-SUB-rules

# llm x rules

## The agreement

A rule decides what to ask and what the answer means; `llm/` decides how it is
asked and refuses anything the answer may not contain. A rule hands the adapter
four things — a role name, a rendered pack, a canonical output model, and (for a
school-routed or transactional call) a frozen `EndpointLease` — and receives a
compiled canonical value plus one `LLMCall`. Everything else about the exchange
belongs to `llm/`: which endpoint, which wire contract, which presentation
profile, which output mechanism, how many repair turns, and whether the bytes
about to be sent match the authority the caller was given. In return the adapter
promises that nothing the model writes becomes process authority —
`reject_model_control_fields` runs before any contract validator, so a `route`,
`tool`, `delegate`, `permission` or `status` key is a typed
`ModelControlFieldError` and never a value a rule could act on. The rule's half
is that it will not put a decision in the pack that the schema does not enforce,
and that whatever comes back — an attack, a candidate, a ruling — is a proposal
for the epistemic machinery, never a verdict. The dependency arrow is one way and
the adapter is duck-typed: `rules/` never imports `LLMAdapter`, only its typed
failures and its data, so every rule is testable against a fake adapter exactly
as it is against a fake harness.

More than two dozen files under `src/deepreason` mention both words. Eight modules
in `rules/` actually import `llm/`; seven of those dispatch; two — `conj.py` and
`crit.py` — carry the route, contract and transaction agreement and hold eight of
the fifteen `adapter.call` sites in the package. D2 rev 2 added two of the seven
dispatchers, `rules/relatedness.py` (`relatedness_trial`, reusing the `judge`
role) and `rules/encoding.py` (`draft_encoded_commitment`, reusing
`property_designer` via `template_role`) — neither carries a route/contract/
transaction agreement, so `conj.py`/`crit.py`'s own eight-site share is
unchanged.
`check: ! grep -rq "deepreason\.rules" --include=*.py src/deepreason/llm && test "$(for f in $(grep -rl llm --include=*.py src/deepreason); do grep -ql rules "$f" && echo x; done | wc -l)" -ge 25 && test "$(grep -rl "deepreason\.llm" --include=*.py src/deepreason/rules | wc -l)" -eq 8 && test "$(grep -rl "adapter\.call(" --include=*.py src/deepreason/rules | wc -l)" -eq 7 && test "$(grep -rh "adapter\.call(" --include=*.py src/deepreason/rules | wc -l)" -eq 15 && test "$(cat src/deepreason/rules/conj.py src/deepreason/rules/crit.py | grep -c "adapter\.call(")" -eq 8`

Forty-one names cross the boundary, and every one of them is data or a refusal:
five exception types, eleven canonical output models, six pack renderers with two
alias builders and `AllocatedPack`, six wire-contract classes with
`wire_contract_for` and `AliasTable`, `EndpointLease` and `route_fingerprint`,
`get_profile`/`ModelProfile`, `specs.transmission_score`, the embedder's
`distance`, and `reference_menu` — the reference-menu interface a rule uses to
build the legal-handle menus its pack carries (`DR-INV-reference-menu`).

The count is pinned with `-eq` below, and it is pinned because it had already
drifted: this sentence read "Thirty-nine" while the tree carried FORTY, and the
`seen >=` superset test above cannot see an addition. A count is a claim
(`SCHEMA.md`), so it gets a check that fails when the number is wrong in either
direction rather than only when a name disappears.
`check: test "$(python -c "import ast,pathlib; T=[ast.parse(p.read_text()) for p in pathlib.Path('src/deepreason/rules').rglob('*.py')]; n=[x for t in T for x in ast.walk(t) if isinstance(x, ast.ImportFrom) and (x.module or '').startswith('deepreason.llm')]; print(len({a.name for x in n for a in x.names}))")" = "41" What does not cross is every transport primitive — no `LLMAdapter`,
`build_adapter`, `TokenMeter`, endpoint class, `select_lease`,
`render_role_prompt` or `reject_model_control_fields` is importable by a rule.
`check: python -c "import ast,pathlib; T=[ast.parse(p.read_text()) for p in pathlib.Path('src/deepreason/rules').rglob('*.py')]; n=[x for t in T for x in ast.walk(t) if isinstance(x, ast.ImportFrom) and (x.module or '').startswith('deepreason.llm')]; mods={x.module for x in n}; seen={a.name for x in n for a in x.names}; plain={a.name for t in T for x in ast.walk(t) if isinstance(x, ast.Import) for a in x.names if a.name.startswith('deepreason.llm')}; attrs={x.attr for t in T for x in ast.walk(t) if isinstance(x, ast.Attribute)}; banned={'LLMAdapter','build_adapter','TokenMeter','Reservation','OpenAICompatEndpoint','MockEndpoint','render_role_prompt','reject_model_control_fields','select_lease','resolve_school_role_lease','probe_capabilities','apply_model_profile','clip_pack'}; assert not (seen & banned), sorted(seen & banned); assert not plain, sorted(plain); assert not (attrs & banned), sorted(attrs & banned); assert mods >= {'deepreason.llm.adapter','deepreason.llm.contracts','deepreason.llm.firewall','deepreason.llm.packs','deepreason.llm.wire'}; assert seen >= {'EndpointError','SchemaRepairError','EndpointLease','RouteFirewallError','WorkflowAuthorizationError','RequestEnvelopeExceeded'}" && test "$(grep -rh "LLMAdapter" --include=*.py src/deepreason/rules | wc -l)" -eq 1 && grep -q "LLMAdapter" src/deepreason/rules/crit.py`

## Where it is expressed

| Site | File | Symbol | What it enforces |
|---|---|---|---|
| Dispatch boundary | `llm/adapter.py` | `LLMAdapter.call` | the only function a rule may use to reach a provider |
| Route resolution | `llm/adapter.py` | `_render_request`: role/seat identity, then `lease.verify(endpoint)` | the seat a rule names must be the seat the manifest froze |
| School routing needs a lease | `llm/adapter.py` | `"school-routed calls require an explicit endpoint lease"` | a `school_id` cannot select a route by itself |
| Control-field firewall | `llm/adapter.py`, `llm/firewall.py` | `reject_model_control_fields(candidate)` before `wire_contract.validate_value` | model JSON may not name a route, tool, delegate, permission or status |
| The same firewall, second site | `llm/wire.py` | `WireContract._preflight_value` | runs before `_reject_unknown_fields`, so a control field is a typed `ModelControlFieldError`, not `extra field at /model` |
| Sanitized repair | `llm/adapter.py`, `llm/firewall.py` | `note_control_invalid(e, sanitize_model_control_fields_for_repair(candidate))` | authored routing language never reaches the next model-facing pack |
| Opaque-data exemption | `llm/firewall.py` | `_OPAQUE_DATA_FIELDS = {"counterexample"}` | a critic's application input may legitimately contain a `status` key |
| Attacked target | `llm/wire.py`, `rules/crit.py` | `CriticWireContract` (`Literal[expected_alias]`); `expected_target=target_id` at three sites | the critic attacks the target the rule chose, stated in the schema rather than the prompt |
| Batch roster | `llm/wire.py`, `rules/crit.py` | `BatchCriticWireV2._one_case_per_target`; `if case.target not in target_ids` | one case per assigned target; an unassigned target registers nothing |
| Contracts fail closed | `llm/wire.py` | `CriticTargetRequiredError`, `AliasTableRequiredError` | a compact critic or conjecturer call refuses to build without its target / call-local table |
| Model-facing bodies | `llm/packs.py` | `render_conj_pack`, `render_crit_pack`, `render_batch_crit_pack`, `render_cx_retry_pack`, `render_experiment_pack`, `render_property_pack` | every budgeted pack is rendered inside `llm/`, from raw state |
| Legal-handle menus cross as RENDERED MENUS | `rules/conj.py`, `rules/crit.py`, `llm/packs.py`, `llm/reference_menu.py` | `reference_menus=` on the three pack renderers; `menu_renders_for` | a rule supplies the call-local BINDING (which blocks are citable, which aliases exist); `llm/` decides the menu's layout, its bound and its token cost. The same shape `citable_evidence_context` and `frame_slice_context` already cross by — except that a menu is also read by the REPAIR diagnostic, which is why its legal set has one resolver rather than one per consumer (`DR-INV-reference-menu`) |
| The alias menu is POST-allocation | `rules/conj.py` | `AllocatedPack(pack + ...)` after `aliases_for_pack` | the alias table is derived from the RENDERED pack, so an artifact-alias menu cannot exist before allocation; appending without re-wrapping lets the adapter re-clip a pack already budgeted section-by-section |
| The frame slice crosses as TEXT | `rules/conj.py`, `rules/crit.py`, `llm/packs.py` | `frame_slice_context`, `frame_crisis_context` | a rule computes what a consulted frame says (`calculus/render.py`); `llm/` decides what it costs. The same shape `frozen_evidence_context` and `citable_evidence_context` already cross by |
| No pack in scope renders without its frame | `rules/conj.py`, `rules/crit.py` | all three `render_*_pack` call sites pass both | §9.5's "in every pack in scope" is a census over call sites, not a property of one |
| Allocation marker | `llm/packs.py`, `rules/conj.py`, `llm/adapter.py` | `AllocatedPack`; `pack_is_allocated` | a rule that appends bytes after PackIR allocation must re-wrap, or the adapter re-clips the whole prompt |
| Budget subtraction | `rules/crit.py` | `_conditioned_budget` | bytes a rule prepends come out of the pack budget before rendering, not after |
| Route inputs vs prompt bytes | `rules/crit.py` | `_critic_execution` → `(call_kwargs, prefix)` | school stance is prompt text; only seat, lease and `school_id` are route inputs |
| Presentation authority | `rules/crit.py`, `llm/adapter.py` | `adapter.profile_for(...)`; `V6ModelProfileOverrideForbidden`; `"output mechanism is frozen by endpoint lease"` | a rule reads the effective profile to pick a transport and may not set one |
| Shown gate is the admitting gate | `llm/packs.py`, `oracle.py`, `rules/crit.py` | `_execution_spec_lines` renders `spec["input_check"]`; `admit_counterexample` runs it | a critic aiming at the rendered gate is aiming at the real one |
| Simulation channel statement | `llm/packs.py`, `llm/wire.py` | `_simulation_contract_note()` from `SIMULATION_MODEL_SOURCE_CONTRACT` / `SIMULATION_REQUESTED_OBSERVABLES_CONTRACT` | the rule the critic is told is the object the conjecturer's schema carries |
| Independence assertion | `rules/experiment.py`, `llm/adapter.py` | `relevance_trial` calls `require_cross_family_judges()`, not the ungated `judge_seats()` | the path that uses the guarantee is the path that asserts it |
| Grounds must be in the pack | `rules/experiment.py` | `ruling.decisive_point not in pack` → invalid ruling | a judge may not ground a verdict in text it was not shown |
| Provenance owns the endpoints | `rules/synth.py` | `endpoints + [i for i in output.connects if i in harness.state.artifacts]` | model refs may add a mention, never remove a deterministic endpoint |
| One call, one log entry | `rules/crit.py`, `rules/experiment.py` | `llm_pending` | the shared call attaches to the first committing event, else to a `Measure` |
| Typed failure vocabulary | `rules/conj.py`, `rules/crit.py` | `except EndpointError / SchemaRepairError` in both; `RouteFirewallError`, `RequestEnvelopeExceeded` and `WorkflowAuthorizationError` in `conj.py` only | the adapter's typed failures are the only failure shapes a rule handles |

The firewall is the load-bearing row and it is enforced twice, on both sides of
one call: once directly in `call`, and once inside every wire contract's
preflight, ahead of the extra-field check. The ordering matters more than the
duplication — reversed, a control key that is not in the schema becomes a generic
`extra field at /model` error, whose diagnostic quotes the authored field back
into the next repair pack. The forbidden set names authority, never content, and
the one exemption is the counterexample payload: application data whose keys
belong to the domain, not to the harness.
`check: python -c "import re,pathlib; a=pathlib.Path('src/deepreason/llm/adapter.py').read_text(); w=pathlib.Path('src/deepreason/llm/wire.py').read_text(); assert re.search(r'candidate = repair\.candidate_from_raw\(turn, raw\)\n\s+reject_model_control_fields\(candidate\)\n\s+wire_value = wire_contract\.validate_value\(candidate\)', a); assert re.search(r'_reject_control_fields\(value\)\n\s+schema = self\.model_json_schema\(\)\n\s+_reject_unknown_fields\(value, schema, schema\)', w); from deepreason.llm.firewall import FORBIDDEN_MODEL_CONTROL_FIELDS as F, _OPAQUE_DATA_FIELDS as O; assert {'model','endpoint','route','tool','delegate','permission','spawn','guard_policy','acceptance','status','context_window_tokens'} <= F; assert O == {'counterexample'}; assert re.search(r'self\._preflight_value\(value\)\n\s+return self\.wire_model\.model_validate\(value\)', w)" && ! grep -rq "reject_model_control_fields" --include=*.py src/deepreason/rules && grep -q "^def reject_model_control_fields(" src/deepreason/llm/firewall.py && python -m pytest tests/test_model_firewall.py tests/test_wire_contracts.py::test_counterexample_payload_remains_opaque_domain_data -q`

**The frame slice crosses as rendered TEXT, not as a structure**, and both
renderers take it in two halves. `rules/` computes it (`calculus/render.py`
decides what a consulted frame says about itself); `llm/` decides what it costs
and how it is cut. Passing a `FrameSliceV1` instead would put a `calculus`
import inside `llm/` for a type nothing there reasons about — the same argument
that keeps `frozen_evidence_context` and `citable_evidence_context` strings.

"Wounds render in-frame, IN EVERY PACK IN SCOPE" (§9.5) is therefore a census
over call sites rather than a property of one function, and the census is
checked: all THREE `render_conj_pack`/`render_crit_pack` call sites in `rules/`
pass both halves, including the atomic-decomposition path in `crit.py` that
only exists after a batch critic exhausts its schema. That third site was
missed by the first implementation and caught by the check below, which is why
the check counts call sites instead of asserting the two obvious ones.
`check: python -c "import ast,pathlib;n=0
for m,c in (('src/deepreason/rules/conj.py','render_conj_pack'),('src/deepreason/rules/crit.py','render_crit_pack')):
    T=ast.parse(pathlib.Path(m).read_text())
    for k in ast.walk(T):
        if isinstance(k,ast.Call) and getattr(k.func,'id','')==c:
            n+=1
            p={x.arg for x in k.keywords}
            assert {'frame_slice_context','frame_crisis_context'}<=p,(m,k.lineno,sorted(p))
assert n==3,n"`
`check: python -m pytest tests/test_frame_render.py::test_both_rules_put_the_frame_in_the_pack_they_dispatch tests/test_frame_render.py::test_the_frame_reaches_a_conjecture_pack_end_to_end -q`

The lease travels one way: a rule never resolves its own — it either carries
one the scheduler resolved, or, when a v6 self-dispatching rule has no
scheduler-supplied envelope at all (adjudication-judge-seats-optins tranche,
S13i, 2026-08-10), asks the adapter for its own default via
`LLMAdapter.bound_v6_default_lease`, a thin wrapper the adapter keeps around
the SAME `select_lease` firewall carries. Either way the adapter re-verifies
whichever lease it receives against the live endpoint immediately before
dispatch; `select_lease`/`resolve_school_role_lease` themselves stay
unimportable by `rules/`.
`check: ! grep -rqE "select_lease|resolve_school_role_lease" --include=*.py src/deepreason/rules && grep -q "^def select_lease(" src/deepreason/llm/firewall.py && grep -q "resolve_school_role_lease(" src/deepreason/scheduler/scheduler.py && grep -q "def bound_v6_default_lease(" src/deepreason/llm/adapter.py && grep -q "lease.verify(endpoint)" src/deepreason/llm/adapter.py && grep -q "school-routed calls require an explicit endpoint lease" src/deepreason/llm/adapter.py && python -m pytest tests/test_model_firewall.py::test_endpoint_lease_accepts_only_its_exact_runtime_route tests/test_model_firewall.py::test_endpoint_lease_allows_logged_process_tuning_only tests/test_criticism_school_execution_c3.py -q`

Presentation is read, never written: no rule passes `model_profile` or
`output_mechanism`, and under v6 both are refused outright.
`check: ! grep -rqE "model_profile=|output_mechanism=" --include=*.py src/deepreason/rules && grep -q "adapter.profile_for(\"argumentative_critic\")" src/deepreason/rules/crit.py && grep -q "output mechanism is frozen by endpoint lease" src/deepreason/llm/adapter.py && grep -q "class V6ModelProfileOverrideForbidden" src/deepreason/llm/adapter.py && python -m pytest tests/test_v6_profile_authority.py::test_v6_per_call_profile_override_fails_before_any_effect -q`

Which target is attacked is a deterministic decision, so it is carried by the
contract rather than asked for in prose: a bound `Literal` in the schema, a
resolve-and-compare in `compile`, and a factory that refuses to build at all
without one. Naming a known-but-wrong alias is therefore an ordinary repairable
schema violation.
`check: grep -q "target_alias=(Literal\[expected_alias\], ...)," src/deepreason/llm/wire.py && test "$(grep -c "expected_target=target_id" src/deepreason/rules/crit.py)" -eq 3 && grep -q "class CriticTargetRequiredError" src/deepreason/llm/wire.py && python -c "import unittest; from deepreason.llm.wire import AliasTable, CriticWireContract, UnknownAliasError; c=CriticWireContract(AliasTable({'SRC_001':'a','SRC_002':'b'}),'a'); w=c.wire_model.model_construct(attack=True,target_alias='SRC_002',claim='x',grounds='y',cited_input_aliases=[]); unittest.TestCase().assertRaisesRegex(UnknownAliasError,'does not name the attacked',c.compile,w)" && python -m pytest tests/test_wire_contracts.py::test_compact_critic_target_is_bound_in_schema_and_validation tests/test_wire_contracts.py::test_compact_critic_factory_fails_closed_without_attacked_target tests/test_compact_role_alias_integration.py::test_compact_critic_repairs_a_known_alias_for_the_wrong_target -q`

The batch contract and the batch rule guard the same roster from two directions:
the contract rejects duplicate targets before compilation, the rule drops any
target it did not assign.
`check: grep -q "if case.target not in target_ids or case.target in ruled:" src/deepreason/rules/crit.py && grep -q "batch critic cannot return duplicate target cases" src/deepreason/llm/wire.py && grep -q "def _one_case_per_target" src/deepreason/llm/wire.py && python -c "import unittest; from deepreason.llm.wire import BatchCriticWireV2; unittest.TestCase().assertRaisesRegex(ValueError,'duplicate target cases',BatchCriticWireV2,cases=[{'target_alias':'SRC_001','attack':True},{'target_alias':'SRC_001','attack':False}])" && python -m pytest tests/test_crit_batch.py -q`

Two agreements exist only because the same fact is stated to the model and
enforced by the machine, and both are wired to a single source. The
counterexample admission gate the critic pack renders is the `input_check` the
oracle actually runs; the simulation contract the critic pack quotes is the same
string object the conjecturer's schema carries.
`check: grep -q "def _execution_spec_lines(" src/deepreason/llm/packs.py && test "$(grep -c "spec.get(\"input_check\")" src/deepreason/llm/packs.py)" -eq 2 && grep -q "gate = spec.get(\"input_check\")" src/deepreason/oracle.py && grep -q "from deepreason.oracle import PROPERTY_PROGRAM, admit_counterexample" src/deepreason/rules/crit.py && grep -q "SIMULATION_REQUESTED_OBSERVABLES_CONTRACT," src/deepreason/llm/packs.py && python -c "from deepreason.llm.packs import _simulation_contract_note; from deepreason.llm.wire import SIMULATION_MODEL_SOURCE_CONTRACT as A, SIMULATION_REQUESTED_OBSERVABLES_CONTRACT as B; n=_simulation_contract_note(); assert A in n and B in n" && python -m pytest tests/test_criticism_authority.py::test_execution_counterexample_still_refutes_under_observe_only tests/test_crit_batch.py::test_critic_pack_states_the_simulation_option_and_its_contract -q`

Three smaller rules hold the same line in three different shapes: a synthesizer
may add refs but not remove the endpoints its problem's provenance owns; a judge
whose `decisive_point` is not in the pack rules nothing; and the path that needs
cross-family independence is the path that calls the asserting reader.
`check: grep -q "endpoints + \[i for i in output.connects if i in harness.state.artifacts\]" src/deepreason/rules/synth.py && grep -q "if ruling.decisive_point and ruling.decisive_point not in pack:" src/deepreason/rules/experiment.py && grep -q "judge_seats = adapter.require_cross_family_judges()" src/deepreason/rules/experiment.py && grep -q "    def require_cross_family_judges(" src/deepreason/llm/adapter.py && python -m pytest tests/test_judge_ensemble_boundary.py -q`

A pack that survives allocation must survive the rule's own edits too, and bytes
a rule adds must be paid for before the pack is built, not after.
`check: test "$(grep -c "AllocatedPack(" src/deepreason/rules/conj.py)" -eq 4 && grep -q "if profile is not None and not pack_is_allocated:" src/deepreason/llm/adapter.py && grep -q "class AllocatedPack(str):" src/deepreason/llm/packs.py && grep -q "def _conditioned_budget(" src/deepreason/rules/crit.py && test "$(grep -c "token_budget=" src/deepreason/rules/crit.py)" -eq "$(grep -c "token_budget=_conditioned_budget(" src/deepreason/rules/crit.py)" && test "$(grep -c "token_budget=_conditioned_budget(" src/deepreason/rules/crit.py)" -ge 5 && python -m pytest tests/test_v6_context_continuation.py::test_wide_allocated_pack_dispatches_advisory_context_intact -q`

## What is deliberately absent

**No rule calls the firewall, and no rule may.** `reject_model_control_fields`
appears in the adapter, in `wire.py`'s preflight, in the three `workflow/`
recovery modules, in `bridge/transactional_adapter.py` and in
`scratch/authoring.py` — every place that admits raw model bytes, and never under
`rules/`. A rule that re-checked the candidate would be checking a value the
adapter had already accepted or refused, and would do it after `compile` has
turned wire into canonical, where the control keys no longer exist. The absence
is checked alongside the ordering above.

**No rule selects a lease, names a model, or opens an endpoint.** `select_lease`
and `resolve_school_role_lease` are the scheduler's; a rule receives a frozen
`EndpointLease` and passes it through. `route_fingerprint` is the one firewall
function `conj.py` and `crit.py` do call, and only to build the
`RouteLeaseRefV1` the workflow will verify — reading a route's identity, never
choosing it. Checked above under the lease paragraph.

**`rules/` never imports `LLMAdapter`.** The adapter arrives as an untyped
positional argument, exactly as the harness does (`DR-SUB-rules`). The single
appearance of the name in the package is a docstring in `crit.py`. Making it a
real import to gain type hints would couple every rule test to a concrete
transport and close a currently acyclic graph; the AST check in "The agreement"
is what holds it.

**No rule catches `TokenBudgetExceeded`, and only two carry `llm_pending`.**
Provider-ceiling exhaustion is a run-level stop, not a rule-level recovery: it
passes through the rules untouched and is handled by the scheduler. A
transactional budget DENIAL is the opposite — it arrives already terminalized, so
`conj.py` and `crit.py` re-raise `WorkBudgetDenied` ahead of their broad handlers
like every other transactional caller. The call-reaches-the-log handoff is
narrower still: `llm_pending` lives in exactly the two rules that can return
having registered nothing.
`check: test "$(grep -rl "llm_pending" --include=*.py src/deepreason/rules | wc -l)" -eq 2 && ! grep -rq "TokenBudgetExceeded" --include=*.py src/deepreason/rules && grep -q "TokenBudgetExceeded" src/deepreason/scheduler/scheduler.py && grep -q "except WorkBudgetDenied:" src/deepreason/rules/conj.py && grep -q "except WorkBudgetDenied:" src/deepreason/rules/crit.py && python -m pytest tests/test_review_fixes.py::test_every_llm_call_reaches_the_log tests/test_review_fixes.py::test_retry_exhausted_spend_reaches_the_log -q`

**`llm/packs.py` reimplements rather than imports.** `_active_property_claims`
walks raw `EpistemicState` for the same thing `rules/experiment.py`'s
`active_properties` returns — ACCEPTED `code:python-prop` artifacts with a
MENTION ref into the problem's criteria — and its docstring says outright that
this is why. What reads like duplication is the arrow: importing the rule would
make the pack renderer depend on the epistemic move it renders for, and `llm/`
would import `rules/` for the first time. The two are deliberately not identical
(the renderer takes a criteria set and returns docstring claims; the rule takes
one oracle and checks readiness), so unifying them is not a refactor.
`check: ! grep -q "deepreason.rules" src/deepreason/llm/packs.py && grep -q "packs must not" src/deepreason/llm/packs.py && grep -q "def _active_property_claims(" src/deepreason/llm/packs.py && grep -q "^def active_properties(" src/deepreason/rules/experiment.py`

**`llm/` constructs no epistemic record.** It reads `Status` to render a pack and
never assigns one; it builds no `Warrant`, no `Problem`, and calls no
`create_artifact`. Every consequence of a call is minted by the rule that made
it, through the harness. This is what keeps a transport bug from becoming an
adjudication bug, and it is why `register_fail_warrant` lives in
`rules/warrants.py` with no counterpart on the other side.
`check: ! grep -rqE "register_fail_warrant|Warrant\(|Problem\(|create_artifact" --include=*.py src/deepreason/llm && grep -q "from deepreason.ontology.state import EpistemicState, Status" src/deepreason/llm/packs.py && grep -q "^def register_fail_warrant(" src/deepreason/rules/warrants.py`

**The anti-relapse gate takes an embedder, never an adapter.** `guards/` is the
one part of `rules/` that touches `llm/` without dispatching: it imports
`embedder.distance` and nothing else, and `check(...)` has no `adapter`
parameter. The gate decides whether a candidate is a relapse onto a refuted
prior; giving it a generator would let a model decide what the search is allowed
to reconsider. A degraded gate fails OPEN with a receipt (`DR-SUB-rules`)
precisely so that no one is tempted to ask a model instead.
`check: python -c "import inspect; from deepreason.rules.guards import anti_relapse as g; p=inspect.signature(g.check).parameters; assert 'embedder' in p and 'adapter' not in p" && ! grep -rq "adapter" --include=*.py src/deepreason/rules/guards && grep -q "from deepreason.llm.embedder import distance" src/deepreason/rules/guards/anti_relapse.py`

**`synth.py` and `vision.py` build their own prompt bodies.** Neither imports a
`render_*_pack`; they join literal lines and hand the result straight to
`adapter.call`. That is not an omission to be tidied — an unmarked pack is one
the adapter still clips to the profile, which is the correct treatment for a
prompt with no PackIR sections to allocate between. What `synth.py` does take
from `llm/packs.py` is `aliases_for_values`: alias discipline is not optional at
any pack size, section allocation is.
`check: python -c "import ast,pathlib; g=lambda f:{a.name for n in ast.walk(ast.parse(pathlib.Path(f).read_text())) if isinstance(n,ast.ImportFrom) and n.module=='deepreason.llm.packs' for a in n.names}; assert g('src/deepreason/rules/synth.py')=={'aliases_for_values'}, g('src/deepreason/rules/synth.py'); assert g('src/deepreason/rules/vision.py')==set(), g('src/deepreason/rules/vision.py')" && grep -q "adapter.call(" src/deepreason/rules/vision.py && grep -q "adapter.call(" src/deepreason/rules/synth.py && grep -q "^def render_conj_pack(" src/deepreason/llm/packs.py && grep -q "^def aliases_for_values(" src/deepreason/llm/packs.py`

## How to change it

The order is forced by which side can refuse. Start at the contract, end at the
rule; the other direction ships a pack that promises something the schema does
not enforce.

1. **Read `DR-INV-frozen-surfaces` first.** Wire contract ids, route-seat
   behavioral grants and anything reaching a qualification subject digest are
   not free to move. A new per-run mode goes on `Config`, never the manifest.
2. **Change the wire contract before the pack, and the pack before the rule.**
   A new field means: the canonical model in `llm/contracts.py`, its wire model
   and branch in `wire_contract_for`, the schema encoding in `llm/wire.py`, the
   pack text in `llm/packs.py`, and only then the rule that reads it. Doing the
   pack first produces a prompt asking for something no validator accepts, which
   the model will supply and the adapter will reject on every repair turn until
   the seat exhausts its smallest contract.
3. **Any rule stated in a pack must be encoded in the schema if it is
   mechanically expressible.** With reasoning disabled the JSON Schema is the
   model's only source of structural truth; a cross-field rule living in a
   `model_validator` alone is invisible to it. `tests/test_schema_carries_every_prose_rule.py`
   is the coverage guard — a new array with a uniqueness validator, or a new
   cross-field validator, fails there until its schema counterpart exists.
4. **Anything a rule appends to a pack after allocation must re-wrap
   `AllocatedPack` and be subtracted from the budget first.** The two halves are
   `rules/conj.py`'s three re-wraps and `rules/crit.py`'s `_conditioned_budget`.
   Miss the first and the adapter re-clips a prompt that PackIR already budgeted
   section by section; miss the second and the pack overruns the envelope.
5. **A new failure path needs the same five-arm shape as the existing ones.**
   `WorkBudgetDenied` re-raised, `EndpointError` → transport-failure attempt,
   `SchemaRepairError` → `repair_schema_failure`, `BaseException` → abandon,
   success → attempt + admission + terminal. See `DR-SEAM-llm-x-workflow`; a
   change that updates only the success arm leaves a mid-call crash
   unrecoverable, and no happy-path test will show it.
6. **Never add a model-decidable field where a deterministic one exists.** The
   attacked target, the assigned batch roster, the interface commitments and a
   relation's endpoints are all chosen by code and merely *named* to the model.
   Turning one of them into something the model states is the change this seam
   exists to make expensive.

What breaks first, in the order you will see it: `ModelControlFieldError` or
`AliasTableRequiredError`/`CriticTargetRequiredError` at contract construction
(before any dispatch); then repeated schema-repair turns ending in
`SchemaRepairError` with the same `validation_path` on every attempt — the
signature of a contract the pack asks the model to violate; then a route seat
that has terminally exhausted its smallest contract, which ends the run.

The tests that catch you, cheapest first: `tests/test_model_firewall.py` and
`tests/test_wire_contracts.py` (sub-second), `tests/test_schema_carries_every_prose_rule.py`,
`tests/test_compact_role_alias_integration.py`, `tests/test_crit_batch.py`,
`tests/test_criticism_school_execution_c3.py`, then
`tests/test_v6_conjecture_component_atomicity.py` and
`tests/test_v6_context_continuation.py`.

## Traps

- **A channel the model is asked to use, in a pack that never describes it.** In
  coin canonicity `run-c5f901f38208e862f4ce2fe60a26e551` the critic pack never
  mentioned simulation at all, while prompts demanded a typed simulation in 12 of
  26 calls that carried no channel — so a critic could convict a candidate for
  not having simulated while never being told the channel existed or what a
  program must look like. `_simulation_contract_note()` now states it, built from
  the same two constants the conjecturer's schema carries so the two wordings
  cannot drift. The generalisation: when one role is judged on another role's
  affordance, the affordance's contract belongs in BOTH packs, as one object.
  Checked in "Where it is expressed".
- **A cross-field rule that lives only in a `model_validator` is invisible.** In
  the same run `conjecturer.turn.v6` was rejected 5 times and completed 0, so
  every surviving candidate came from the atomic fallback — which carries no
  capability channel at all. The two turn outcome rules existed only as
  validators, so a model reading the schema could emit a structurally valid turn
  the harness then refused. The cost of the same defect shape was measured on a
  sibling contract (thinking-off batteries, subject `97653fde`):
  `scratch.link.compact.v1` scored 11/20 then 9/20 first-pass with 18 and 22
  repairs on glm-5.2 with thinking off and failed production qualification twice;
  encoding one cross-field rule took it to 20/20 with zero repairs. The dangerous
  direction for such an encoding is a FALSE REJECT, so the regression
  differential-tests schema against validator rather than asserting the schema's
  shape.
`check: python -m pytest tests/test_v6_conjecture_component_atomicity.py::test_the_turn_outcome_rules_are_carried_by_the_schema_and_agree_with_the_validator tests/test_schema_carries_every_prose_rule.py -q`
- **A rules-side string operation silently demoted the allocated pack.** In live
  `run-646f41b8` seq 565 the v6 post-allocation pack edits in `conj.py` returned
  a plain `str`, so the adapter re-applied the profile's aggregate prefix clip to
  a pack `PackIR` had already budgeted section by section and cut the sealed
  advisory context mid-JSON: 86 percent of the context bytes never dispatched,
  with every pre-dispatch authority check passing, because preview and dispatch
  render through the same helper and therefore agree on a digest of the same
  wrong bytes. The full account and the adapter-side guard are in
  `DR-SEAM-llm-x-workflow`; the rules-side half is that `AllocatedPack` must be
  re-applied after every edit, checked above.
- **The two firewall sites are mutually redundant, and no behavioural test pins
  either one alone.** Under mutation: deleting `reject_model_control_fields` from
  `adapter.call` leaves `tests/test_model_firewall.py` fully green, because
  `WireContract._preflight_value` catches it; deleting `_reject_control_fields`
  from the preflight leaves `test_model_firewall.py` and `test_wire_contracts.py`
  green, because the adapter catches it. Only deleting BOTH fails, at
  `test_control_repair_prompts_never_reflect_fields_or_values`, with the
  diagnostic `{"error": "extra field at /model"}` — which is exactly the leak the
  firewall exists to prevent, since that diagnostic goes into the next repair
  pack. **Residue: each site is held only by the structural check in this
  document.** Reversing the order inside `_preflight_value` is likewise green.
  Do not delete either site on the grounds that the tests still pass. The same
  redundancy hides a subtler mutation: deleting the `self._preflight_value(value)`
  CALL from `WireContract.validate_value` — leaving the method defined, and a
  subclass override still calling it — is green everywhere, so the structural
  check pins the call site and its position, not just the method body.
- **Reading `adapter.meter` is not metering.** `conj.py` and `crit.py` read
  `adapter.meter` to hand it to `InquiryTransactionService`; neither calls
  `reserve` or `check`. A rule that booked its own reservation would double-count
  against a bound the workflow already owns (`DR-SEAM-llm-x-workflow`), and the
  ceiling test compares work items, logged calls and metered calls for equality.
`check: ! grep -rqE "meter\.reserve|meter\.check\(" --include=*.py src/deepreason/rules && grep -q "InquiryTransactionService(harness, manifest, adapter.meter)" src/deepreason/rules/conj.py && grep -q "InquiryTransactionService(harness, manifest, adapter.meter)" src/deepreason/rules/crit.py && grep -q "^class TokenMeter:" src/deepreason/llm/budget.py`
