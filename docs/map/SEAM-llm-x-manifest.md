<!-- DR-SEAM-llm-x-manifest -->
Verified-at: 9fa394d9
Verify: python tools/docs_verify.py
Owns: src/deepreason/llm/firewall.py, src/deepreason/llm/adapter.py, src/deepreason/run_manifest.py
Sides: DR-SUB-llm, DR-SUB-manifest

# llm x manifest

## The agreement

The manifest promises one thing and promises it permanently: a closed set of
exact provider routes, one `Route` per role seat, secret-free and
model-concrete, frozen before the first call — so "which model answered" is a
question the record settles rather than one the runtime decides. The LLM
boundary promises in return that it never chooses a route and never repairs
one. `leases_from_manifest` turns `manifest.roles` into one `EndpointLease` per
(role, seat), and nothing downstream may reach past that map: a caller names a
role and a seat index, `select_lease` is total or it raises, and every provider
request — the first turn and every repair turn — re-verifies the live endpoint
object against the leased `Route`, dying with `ROUTE_LEASE_MISMATCH` on any
difference. Identity is a content hash: `route_fingerprint` is the sha256 of
the whole serialized route, it is the key by which the manifest hands back
per-seat authority, and it is what every typed record stores as `route_sha256`.
The division of labour inside that is sharp — the manifest decides WHICH seat
(school bindings, per-seat plans, judge topology), the firewall decides only
whether the runtime still matches the seat it was given, and neither consults
model output to do it. Two route fields, `max_tokens` and `timeout_s`, sit
deliberately outside identity because they are bounded process-health knobs a
controller may tune and log; every other field is frozen. The vocabulary flows
one way: `llm/firewall.py` imports the manifest's types at module scope and the
manifest imports the digest function back inside function bodies, which is what
keeps the cycle from closing.

Twenty-nine modules mention both sides. Three carry the agreement. The import
surface is seven names across three `llm/` modules, and the reverse edge is at
module scope only for the two `llm/` modules that do not import the manifest
back. Named imports are not the only way in: a plain `import
deepreason.run_manifest` would let the provider boundary reach every symbol
under an attribute, so the check forbids that form outright rather than
enumerating what it could reach. The two reverse-edge modules are pinned by the
symbols the manifest imports from them (`DEFAULT_TIMEOUT_S`, `resolve_model`,
`infer_provider`): a bare `! grep` over a path that no longer exists succeeds,
so the prohibition would otherwise be satisfied by deleting its own subject.
`check: python -c "import ast, pathlib; llm=pathlib.Path('src/deepreason/llm'); mods={p.name for p in llm.rglob('*.py') for n in ast.walk(ast.parse(p.read_text())) if isinstance(n, ast.ImportFrom) and (n.module or '').startswith('deepreason.run_manifest')}; assert mods == {'adapter.py','capabilities.py','firewall.py'}, sorted(mods); names={a.name for p in llm.rglob('*.py') for n in ast.walk(ast.parse(p.read_text())) if isinstance(n, ast.ImportFrom) and (n.module or '').startswith('deepreason.run_manifest') for a in n.names}; assert names == {'Route','RunManifest','SchoolRoleBindingV1','infer_model_family','resolve_route_seat_base_profile','resolve_route_seat_behavioral_capability','validate_route_base_url'}, sorted(names); plain={a.name for p in llm.rglob('*.py') for n in ast.walk(ast.parse(p.read_text())) if isinstance(n, ast.Import) for a in n.names if a.name.startswith('deepreason.run_manifest')}; assert plain == set(), sorted(plain); t=ast.parse(pathlib.Path('src/deepreason/run_manifest.py').read_text()); top={n.module for n in t.body if isinstance(n, ast.ImportFrom) and (n.module or '').startswith('deepreason.llm')}; every={n.module for n in ast.walk(t) if isinstance(n, ast.ImportFrom) and (n.module or '').startswith('deepreason.llm')}; assert top == {'deepreason.llm.endpoints','deepreason.llm.providers'}, sorted(top); assert 'deepreason.llm.firewall' in every - top" && grep -q "^DEFAULT_TIMEOUT_S = " src/deepreason/llm/endpoints.py && grep -q "^def resolve_model(" src/deepreason/llm/endpoints.py && grep -q "^def infer_provider(" src/deepreason/llm/providers.py && ! grep -q "run_manifest" src/deepreason/llm/endpoints.py src/deepreason/llm/providers.py && test "$(for f in $(grep -rl "deepreason\.llm" --include=*.py src/deepreason); do grep -ql "RunManifest\|run_manifest" "$f" && echo x; done | wc -l)" -eq 29`

## Where it is expressed

| Site | File | Symbol | What it enforces |
|---|---|---|---|
| The frozen route | `run_manifest.py` | `Route` (frozen, `extra="forbid"`, `_concrete_model`, `_secret_free_url`) | one exact secret-free provider route; `auto`/`auto-alt` cannot survive compilation, a credential-bearing URL cannot be persisted |
| Translation | `llm/firewall.py` | `leases_from_manifest` | `manifest.roles` becomes one `EndpointLease` per role and seat, in seat order; a role with an empty route tuple gets no lease at all |
| Legacy translation | `llm/firewall.py` | `leases_from_endpoints`, `route_from_endpoint` | a pre-manifest role table gets the same frozen shape by reading a live endpoint object |
| Seat lookup | `llm/firewall.py` | `select_lease` | total on (role, seat) or it raises; a lease whose own role/seat disagrees is a `RouteFirewallError`, never a silent substitution |
| Adapter wiring | `llm/adapter.py` | `build_adapter(..., run_manifest=...)` | role table, presentation profile, transactional mode AND the lease map all come from the manifest when one is supplied |
| Endpoint construction | `run_manifest.py`, `llm/adapter.py` | `Route.endpoint_spec()` into `_endpoint_from_spec` | the only manifest-to-endpoint constructor; the credential VALUE is read by `os.environ.get(api_key_env)` here and, at compile time only, in `_route_from_spec` — see Traps |
| Dispatch guard | `llm/firewall.py` | `EndpointLease.verify` | `ROUTE_LEASE_MISMATCH`: `base_url` and `model_id` always, ten more fields whenever the endpoint object exposes them, and `max_tokens` as an eleventh only when the route carries a qualified capacity |
| Re-verification | `llm/adapter.py` | `lease.verify(endpoint)` at three sites | whole-ensemble preflight, render, and again before every repair turn; a mid-call mutation is terminal but carries prior spend |
| Route identity | `llm/firewall.py` | `route_fingerprint` | sha256 over the entire serialized `Route`; the `route_sha256` of every typed record |
| Behavioural grant | `run_manifest.py` | `resolve_route_seat_behavioral_capability` | (role, seat, endpoint_id, route_sha256) must name the frozen seat AND exactly one grant; absence is never permission |
| Presentation grant | `run_manifest.py` | `resolve_route_seat_base_profile` | the seat's frozen base profile, keyed by (role, seat, endpoint_id) only — see Traps |
| Contract gate | `llm/adapter.py` | `_render_request` v6 branch | the chosen wire contract must appear in that seat's frozen behavioral grants, and the profile must equal the grant's |
| Whole-map equality | `llm/adapter.py`, `bridge/transactional_adapter.py` | `bind_v6_authority`, `preview_request_with_v6_classification`, `TransactionalBridgeAdapter.__init__` | the adapter's leases must equal `leases_from_manifest(manifest)` exactly, before any dispatch |
| Request envelope | `llm/adapter.py` | `_enforce_request_envelope` | the route's `context_window_tokens` and `max_tokens` bound the rendered prompt; `REQUEST_ENVELOPE_EXCEEDED` |
| School seat | `llm/firewall.py` | `resolve_school_role_lease` | manifest policy picks the seat, then the runtime lease is compared to `manifest.roles[role][seat]`: `SCHOOL_ROUTE_LEASE_MISMATCH` |
| Ensemble family | `llm/firewall.py` | `require_cross_family_judge_ensemble`, `_lease_families` | judge independence by route family, read only from immutable leases |
| Ensemble school | `llm/firewall.py` | `require_cross_school_judge_ensemble` | the single-family substitute; school comes only from manifest bindings, and a binding whose `endpoint_id` disagrees with the seat is not counted |
| Qualification lease | `cli/doctor.py` | `exercise_production_contract_case`, `_validate_production_contract_request_envelopes` | both battery sites mint their lease straight from `manifest.roles[pair.role][pair.seat]` and run the same envelope check |
| Replay re-derivation | `invariants.py`, `verification/report.py`, `workflow/replay.py`, `workflow/nonconjecture_recovery.py` | `route_sha256` compared to `route_fingerprint(route)` | a recorded receipt must still name the manifest route it claims |

The translation is exact and one-directional: seats are numbered by position, a
role with no routes produces no lease rather than an empty one, and asking for a
seat that does not exist raises instead of falling back to seat zero.
`check: python -c "import types, pytest; from deepreason.run_manifest import Route; from deepreason.llm.firewall import EndpointLease, RouteFirewallError, leases_from_manifest, select_lease; r=Route(endpoint_id='a', base_url='https://h/v1', model_id='m', provider='p', family='f'); m=types.SimpleNamespace(roles={'conjecturer': (r, r), 'judge': ()}); L=leases_from_manifest(m); assert set(L) == {'conjecturer'}; assert [x.seat for x in L['conjecturer']] == [0, 1] and L['conjecturer'][1].route is r; pytest.raises(KeyError, select_lease, L, 'judge', 0); pytest.raises(KeyError, select_lease, L, 'conjecturer', 2); pytest.raises(RouteFirewallError, select_lease, {'judge': (EndpointLease(role='conjecturer', seat=0, route=r),)}, 'judge', 0)"`

`ROUTE_LEASE_MISMATCH` fires on model or base-url substitution unconditionally,
on each of the ten optional fields the endpoint exposes, and on `max_tokens` as
an eleventh only when the route carries a qualified capacity. Four sites in the
tree re-verify. Dropping any single entry from the `optional` map is a silent
weakening of the guard, so the check names all eleven rather than a sample.
`check: python -c "import types, pytest; from deepreason.run_manifest import Route; from deepreason.llm.firewall import EndpointLease, RouteFirewallError; r=Route(endpoint_id='a', base_url='https://h/v1', model_id='m', provider='p', family='f', max_tokens=100); L=EndpointLease(role='judge', seat=1, route=r); e=types.SimpleNamespace(name='https://h/v1', model='m'); L.verify(e); e.max_tokens=999; e.timeout_s=1; L.verify(e); e.temperature=0.9; pytest.raises(RouteFirewallError, L.verify, e).match('field=temperature'); pytest.raises(RouteFirewallError, L.verify, types.SimpleNamespace(name='https://h/v1', model='other')).match('ROUTE_LEASE_MISMATCH.*field=model_id'); pytest.raises(RouteFirewallError, L.verify, types.SimpleNamespace(name='https://other/v1', model='m')).match('ROUTE_LEASE_MISMATCH.*field=base_url'); q=Route(endpoint_id='a', base_url='https://h/v1', model_id='m', provider='p', family='f', model_revision='rev', reasoning='high', output_mode='json_object', output_mechanism='grammar', temperature=0.2, max_tokens=100, context_window_tokens=1000, logprobs=True); Q=EndpointLease(role='judge', seat=1, route=q); good=dict(name='https://h/v1', model='m', endpoint_id='a', family='f', model_revision='rev', provider='p', reasoning='high', temperature=0.2, json_mode=True, output_mechanism='grammar', request_logprobs=True, context_window_tokens=1000, max_tokens=100); Q.verify(types.SimpleNamespace(**good)); wrong=dict(endpoint_id='z', family='g', model_revision='other', provider='q', reasoning='low', temperature=0.9, json_mode=False, output_mechanism='json_text', request_logprobs=False, context_window_tokens=2000, max_tokens=999); assert len(wrong) == 11; [pytest.raises(RouteFirewallError, Q.verify, types.SimpleNamespace(**{**good, k: v})).match('ROUTE_LEASE_MISMATCH.*field=' + k) for k, v in wrong.items()]" && test "$(grep -rn "\.verify(endpoint)" --include=*.py src/deepreason | wc -l)" -eq 4`

The digest is over the route and nothing else: canonical JSON of the whole
model dump, so any single field move produces a different `route_sha256`, and an
absent `context_window_tokens` is serialized away rather than written as null.
`check: python -c "import hashlib, json; from deepreason.run_manifest import Route; from deepreason.llm.firewall import route_fingerprint; a=Route(endpoint_id='a', base_url='https://h/v1', model_id='m', provider='p', family='f'); d=a.model_dump(mode='json'); assert 'context_window_tokens' not in d; assert route_fingerprint(a) == hashlib.sha256(json.dumps(d, sort_keys=True, separators=(',', ':'), ensure_ascii=False).encode()).hexdigest(); moved={route_fingerprint(a.model_copy(update={k: v})) for k, v in (('temperature', 0.1), ('family', 'g'), ('output_mechanism', 'grammar'), ('logprobs', True), ('api_key_env', 'K'), ('timeout_s', 7), ('reasoning', 'none'))}; assert len(moved) == 7 and route_fingerprint(a) not in moved"`

Both grant resolvers refuse rather than default, and each refuses with a
distinct typed code at every layer it can fail: the manifest is not v6, the seat
does not exist, the frozen route's identity differs, the plan is absent, the
plan holds no single grant for that seat, and the grant's own identity differs
from the seat's. That last layer is the one nothing else covers — deleting
`grant.route_sha256 != route_sha256` from the behavioural resolver leaves both
v6 grant test files green, so it is named here rather than left to them.
`check: python -c "import types, pytest; from deepreason.run_manifest import Route, RunManifestError, resolve_route_seat_base_profile as P, resolve_route_seat_behavioral_capability as B; from deepreason.llm.firewall import route_fingerprint; r=Route(endpoint_id='a', base_url='https://h/v1', model_id='m', provider='p', family='f'); sha=route_fingerprint(r); mk=lambda **kw: types.SimpleNamespace(**{'schema_version': 6, 'roles': {'judge': (r,)}, 'model_profile': 'standard', 'route_seat_presentation_plan': None, 'route_seat_behavioral_capability_plan': None, **kw}); g=types.SimpleNamespace(role='judge', seat=0, endpoint_id='a', route_sha256=sha); m=mk(route_seat_behavioral_capability_plan=types.SimpleNamespace(entries=(g,))); code=lambda f, *a, **k: pytest.raises(RunManifestError, f, *a, **k).value.code; assert P(m, role='judge', seat=0, endpoint_id='a') == 'standard'; assert B(m, role='judge', seat=0, endpoint_id='a', route_sha256=sha) is g; assert code(B, m, role='judge', seat=0, endpoint_id='a', route_sha256='0'*64) == 'V6_BEHAVIORAL_ROUTE_MISMATCH'; assert code(B, m, role='judge', seat=1, endpoint_id='a', route_sha256=sha) == 'V6_BEHAVIORAL_ROUTE_REQUIRED'; assert code(B, m, role='judge', seat=0, endpoint_id='b', route_sha256=sha) == 'V6_BEHAVIORAL_ROUTE_MISMATCH'; assert code(B, mk(), role='judge', seat=0, endpoint_id='a', route_sha256=sha) == 'V6_BEHAVIORAL_CAPABILITY_PLAN_REQUIRED'; assert code(B, mk(route_seat_behavioral_capability_plan=types.SimpleNamespace(entries=())), role='judge', seat=0, endpoint_id='a', route_sha256=sha) == 'V6_BEHAVIORAL_GRANT_REQUIRED'; bad=lambda **kw: mk(route_seat_behavioral_capability_plan=types.SimpleNamespace(entries=(types.SimpleNamespace(**{'role': 'judge', 'seat': 0, 'endpoint_id': 'a', 'route_sha256': sha, **kw}),))); assert code(B, bad(route_sha256='1'*64), role='judge', seat=0, endpoint_id='a', route_sha256=sha) == 'V6_BEHAVIORAL_GRANT_MISMATCH'; assert code(B, bad(endpoint_id='z'), role='judge', seat=0, endpoint_id='a', route_sha256=sha) == 'V6_BEHAVIORAL_GRANT_MISMATCH'; assert code(P, m, role='judge', seat=0, endpoint_id='b') == 'ROUTE_SEAT_PRESENTATION_ENDPOINT_MISMATCH'; assert code(P, m, role='judge', seat=1, endpoint_id='a') == 'ROUTE_SEAT_PRESENTATION_ROUTE_REQUIRED'; pp=lambda entries: mk(route_seat_presentation_plan=types.SimpleNamespace(entries=entries)); assert code(P, pp(()), role='judge', seat=0, endpoint_id='a') == 'ROUTE_SEAT_PRESENTATION_GRANT_REQUIRED'; assert P(pp((types.SimpleNamespace(role='judge', seat=0, endpoint_id='a', base_profile='compact'),)), role='judge', seat=0, endpoint_id='a') == 'compact'; assert code(P, pp((types.SimpleNamespace(role='judge', seat=0, endpoint_id='z', base_profile='compact'),)), role='judge', seat=0, endpoint_id='a') == 'ROUTE_SEAT_PRESENTATION_GRANT_MISMATCH'; assert code(P, mk(schema_version=5), role='judge', seat=0, endpoint_id='a') == 'ROUTE_SEAT_PRESENTATION_V6_REQUIRED'; assert code(B, mk(schema_version=5), role='judge', seat=0, endpoint_id='a', route_sha256=sha) == 'V6_BEHAVIORAL_CAPABILITY_REQUIRED'"`

A manifest-built adapter takes its leases from the document, not from the
endpoints it just constructed, and three sites re-assert whole-map equality
before any v6 dispatch.
`check: grep -q "leases = leases_from_manifest(run_manifest) if run_manifest is not None else None" src/deepreason/llm/adapter.py && test "$(grep -c "if self.leases != leases_from_manifest(manifest):" src/deepreason/llm/adapter.py)" -eq 2 && test "$(grep -c 'adapter route leases differ from the manifest' src/deepreason/llm/adapter.py)" -eq 2 && grep -q "if adapter.leases != leases_from_manifest(manifest):" src/deepreason/bridge/transactional_adapter.py && grep -q "adapter route leases differ from the manifest" src/deepreason/bridge/transactional_adapter.py && python -m pytest "tests/test_model_firewall.py::test_adapter_built_from_manifest_keeps_exact_route_and_mechanism" -q`

Two rows of the table — the contract gate and the request envelope — are
enforced inside one render and were carried by nothing else.
The v6 branch of `_render_request` refuses a wire contract absent from that
seat's frozen behavioral grants, or a base profile differing from the grant's;
`_enforce_request_envelope` bounds prompt bytes plus the route's `max_tokens` by
its `context_window_tokens` and leaves an unqualified route unbounded, which is
why the envelope is a route property rather than a controller setting.
`check: python -c "import pytest; from deepreason.run_manifest import Route; from deepreason.llm.firewall import EndpointLease; from deepreason.llm.adapter import _enforce_request_envelope, RequestEnvelopeExceeded; q=Route(endpoint_id='a', base_url='https://h/v1', model_id='m', provider='p', family='f', max_tokens=100, context_window_tokens=200); L=EndpointLease(role='judge', seat=1, route=q); _enforce_request_envelope('judge', 'x'*100, L); e=pytest.raises(RequestEnvelopeExceeded, _enforce_request_envelope, 'judge', 'x'*101, L).value; assert e.code == 'REQUEST_ENVELOPE_EXCEEDED' and (e.completion_bound, e.context_capacity, e.route_seat, e.total_bound) == (100, 200, 1, 201); u=Route(endpoint_id='a', base_url='https://h/v1', model_id='m', provider='p', family='f', max_tokens=100); _enforce_request_envelope('judge', 'x'*100000, EndpointLease(role='judge', seat=0, route=u))" && grep -q "wire contract differs from frozen route-seat behavioral authority" src/deepreason/llm/adapter.py && grep -q "if behavioral.base_profile != base_profile or wire_contract.contract_id not in {" src/deepreason/llm/adapter.py`

School routing resolves a SEAT from manifest policy and then re-compares the
whole route, so a drifted lease is refused after the seat is known rather than
before it is looked up; a v4-and-later manifest with no control-plane policy is
refused outright.
`check: python -c "import types, pytest; from deepreason.run_manifest import Route; from deepreason.llm.firewall import EndpointLease, SchoolRouteResolutionError, resolve_school_role_lease; a=Route(endpoint_id='a', base_url='https://h/v1', model_id='m', provider='p', family='f'); b=a.model_copy(update={'model_id': 'other'}); m=types.SimpleNamespace(schema_version=3, roles={'conjecturer': (a,)}); ok={'conjecturer': (EndpointLease(role='conjecturer', seat=0, route=a),)}; drifted={'conjecturer': (EndpointLease(role='conjecturer', seat=0, route=b),)}; assert resolve_school_role_lease(m, ok, school_id='school-0', role='conjecturer').route is a; assert pytest.raises(SchoolRouteResolutionError, resolve_school_role_lease, m, drifted, school_id='school-0', role='conjecturer').value.code == 'SCHOOL_ROUTE_LEASE_MISMATCH'; assert pytest.raises(SchoolRouteResolutionError, resolve_school_role_lease, m, ok, school_id='', role='conjecturer').value.code == 'SCHOOL_ROUTE_SCHOOL_REQUIRED'; v6=types.SimpleNamespace(schema_version=6, roles={'conjecturer': (a,)}, control_plane_policy=None); assert pytest.raises(SchoolRouteResolutionError, resolve_school_role_lease, v6, ok, school_id='school-0', role='conjecturer').value.code == 'SCHOOL_ROUTE_POLICY_MISSING'" && grep -q "^def test_prompt_and_response_route_prose_cannot_change_the_resolved_lease(" tests/test_school_execution_binding_v4.py && python -m pytest tests/test_school_execution_binding_v4.py -q`

The two ensemble gates read two different manifest surfaces — family from the
leased route, school from `criticism_policy.bindings` — and both fail closed on
an empty lease map. A manifest cannot express an empty family, so the fold's
blank-drop covers only a whitespace one, and it errs toward the stricter gate.
`check: python -c "import pytest; from pydantic import ValidationError; from deepreason.run_manifest import Route, SchoolRoleBindingV1; from deepreason.llm.firewall import EndpointLease, JudgeEnsemblePolicyError, JudgeSchoolEnsemblePolicyError, is_single_family_run, is_single_model_run, require_cross_family_judge_ensemble, require_cross_school_judge_ensemble; r0=Route(endpoint_id='a', base_url='https://h/v1', model_id='m', provider='p', family='glm'); r1=Route(endpoint_id='b', base_url='https://h2/v1', model_id='n', provider='p', family='glm'); L={'judge': (EndpointLease(role='judge', seat=0, route=r0), EndpointLease(role='judge', seat=1, route=r1))}; good=(SchoolRoleBindingV1(school_id='school-0', role='judge', seat=0, endpoint_id='a'), SchoolRoleBindingV1(school_id='school-1', role='judge', seat=1, endpoint_id='b')); assert len(require_cross_school_judge_ensemble(L, good)) == 2; pytest.raises(JudgeSchoolEnsemblePolicyError, require_cross_school_judge_ensemble, L, (good[0], SchoolRoleBindingV1(school_id='school-1', role='judge', seat=1, endpoint_id='a'))); pytest.raises(JudgeEnsemblePolicyError, require_cross_family_judge_ensemble, L); pytest.raises(JudgeSchoolEnsemblePolicyError, require_cross_school_judge_ensemble, {}, good); pytest.raises(ValidationError, Route, endpoint_id='a', base_url='https://h/v1', model_id='m', provider='p', family=''); blank={'judge': (EndpointLease(role='judge', seat=0, route=r0.model_copy(update={'family': ' '})),)}; assert is_single_family_run(blank) is False and is_single_model_run(blank) is True; assert is_single_family_run({}) is False and is_single_model_run({}) is False" && python -m pytest tests/test_judge_ensemble_boundary.py -q`

Family is normative for the judge gate, so exactly one inference function
serves the manifest compiler, the legacy lease freezer and the endpoint builder;
an unknown identifier becomes a provider-stemmed family rather than a guess.
`check: python -c "import inspect; from deepreason.run_manifest import _route_from_spec, infer_model_family; from deepreason.llm.firewall import route_from_endpoint; from deepreason.llm.adapter import _endpoint_from_spec; assert all('infer_model_family' in inspect.getsource(f) for f in (_route_from_spec, route_from_endpoint, _endpoint_from_spec)); assert infer_model_family('deepseek-v4-pro', 'ollama') == 'deepseek' and infer_model_family('glm-5.2', 'ollama') == 'ollama:glm'" && python -m pytest tests/test_providers.py::test_endpoint_family_defaults_to_lease_inference -q`

## What is deliberately absent

**Neither side constructs the other's object.** `EndpointLease` appears nowhere
in `run_manifest.py` — the manifest freezes routes, not seats-in-use — and
`llm/` never loads, compiles, binds or writes a manifest, so no code path in the
provider boundary can parse a document, widen a validator or decide that an
absent field is permission. Leases are minted at exactly three files: the
firewall's two translators, the doctor's battery, and the bridge's ledger
lookup, and the last two build theirs directly from `manifest.roles[role][seat]`.
Adding a `RunManifest` parameter to a firewall helper "so it can check one more
thing" inverts this: the firewall's whole value is that it holds no document and
therefore cannot be argued with. Every name the absence clause forbids is also
pinned as still-defined, because a document-handling name that gets renamed
would otherwise make its own prohibition vacuous.
`check: ! grep -q "EndpointLease" src/deepreason/run_manifest.py && grep -q "^class EndpointLease:" src/deepreason/llm/firewall.py && grep -q "^def leases_from_manifest(" src/deepreason/llm/firewall.py && test "$(grep -rl "EndpointLease(" --include=*.py src/deepreason | sort | tr '\n' ' ')" = "src/deepreason/bridge/harness.py src/deepreason/cli/doctor.py src/deepreason/llm/firewall.py " && test "$(grep -c "route = manifest.roles\[pair.role\]\[pair.seat\]" src/deepreason/cli/doctor.py)" -eq 2 && grep -q "^def exercise_production_contract_case(" src/deepreason/cli/doctor.py && grep -q "^def _validate_production_contract_request_envelopes(" src/deepreason/cli/doctor.py && grep -q "routes = manifest.roles.get(effective.ledger_role, ())" src/deepreason/bridge/harness.py && ! grep -rqE "load_run_manifest|bind_run_manifest|persist_run_manifest|write_run_manifest|compile_run_manifest|MANIFEST_NAME" --include=*.py src/deepreason/llm && for s in load_run_manifest compile_run_manifest bind_run_manifest persist_run_manifest write_run_manifest; do grep -q "^def $s(" src/deepreason/run_manifest.py || exit 1; done && grep -q "^MANIFEST_NAME = " src/deepreason/run_manifest.py`

**The firewall reads five manifest attributes and the adapter reads five, out of
thirty-two fields — and they share only `schema_version`.** The firewall sees
`roles`, `schema_version`, `control_plane_policy`, `criticism_policy` and
`engine_config_json` (only to bound the school roster); it sees no plan, no
profile, no contract vocabulary. The adapter sees `model_profile`, `sha256`,
`compact_recovery_policy`, `route_seat_behavioral_capability_plan` and
`schema_version` — the last only as a v6 gate at the two authority entry points,
read through `getattr` because the argument is duck-typed — and notably NOT
`roles`: inside `LLMAdapter` a route is reachable only through a lease.
Presentation and behavioural authority are resolved in `adapter.py` through the
manifest's own resolvers; route legitimacy is decided in `firewall.py` with no
plan in hand. Searching the firewall for the behavioural-grant check and finding
nothing is the expected result. Both attribute forms are counted: a dotted read
and a `getattr` read widen the surface identically, and enumerating only the
first is how `schema_version` sat unrecorded in the adapter's set.
`check: python -c "import re, pathlib; from deepreason.run_manifest import RunManifest; src=lambda p: pathlib.Path(p).read_text(); read=lambda p: set(re.findall(r'(?<![a-z_])manifest\.([a-z_0-9]+)', src(p))) | set(re.findall(r'getattr\(\s*manifest\s*,\s*[\x27\"]([a-z_0-9]+)', src(p))); assert read('src/deepreason/llm/firewall.py') == {'control_plane_policy', 'criticism_policy', 'engine_config_json', 'roles', 'schema_version'}; assert read('src/deepreason/llm/adapter.py') == {'compact_recovery_policy', 'model_profile', 'route_seat_behavioral_capability_plan', 'schema_version', 'sha256'}; assert read('src/deepreason/llm/firewall.py') & read('src/deepreason/llm/adapter.py') == {'schema_version'}; assert len(RunManifest.model_fields) == 32"`

**No credential ever reaches a lease, a digest or a record.** `Route` has an
`api_key_env` field and no `api_key` field; the value is looked up from the
environment at exactly two sites — `_endpoint_from_spec` when building the
endpoint, and `_route_from_spec` at compile time, where `resolve_model` needs a
live provider call to turn `auto` into a concrete model — plus one presence-only
test in `missing_manifest_credentials`. Neither value ever lands on a `Route`,
and `route_from_endpoint` writes `api_key_env=None` because an endpoint object
does not retain the name.
The firewall mentions the word once, in that assignment. This is why the URL
validator rejects userinfo, queries and fragments outright rather than
stripping them: a route is hashed and persisted, so a value-shaped loophole
would put a secret into the append-only record. The drop is exercised against an
endpoint that *does* carry both `api_key_env` and a live `api_key`: a fixture
without them proves only that the attribute was absent, not that it was dropped.
`check: python -c "import types; from deepreason.run_manifest import Route; from deepreason.llm.firewall import route_from_endpoint, route_fingerprint; assert 'api_key' not in Route.model_fields and 'api_key_env' in Route.model_fields; bare=types.SimpleNamespace(name='https://h/v1', model='m', provider='p', family='f'); assert route_from_endpoint(bare).api_key_env is None; loaded=types.SimpleNamespace(name='https://h/v1', model='m', provider='p', family='f', api_key_env='OLLAMA_API_KEY', api_key='sk-live-secret'); r=route_from_endpoint(loaded); assert r.api_key_env is None, r.api_key_env; assert 'OLLAMA_API_KEY' not in str(r.model_dump(mode='json')) and 'sk-live-secret' not in str(r.model_dump(mode='json')); route_fingerprint(r); import pytest; from deepreason.run_manifest import RouteSecretError; mk=lambda u: Route(endpoint_id='a', base_url=u, model_id='m', provider='p', family='f'); [pytest.raises(RouteSecretError, mk, u) for u in ('https://u:sk-live-secret@h/v1', 'https://u@h/v1', 'https://h/v1?key=sk-live-secret', 'https://h/v1#sk-live-secret')]; assert 'sk-live-secret' not in str(pytest.raises(RouteSecretError, mk, 'https://u:sk-live-secret@h/v1').value)" && test "$(grep -o "api_key" src/deepreason/llm/firewall.py | wc -l)" -eq 1 && grep -q "api_key = os.environ.get(api_key_env) if api_key_env else None" src/deepreason/llm/adapter.py && grep -q "api_key = os.environ.get(api_key_env) if api_key_env else None" src/deepreason/run_manifest.py && test "$(grep -rnE "os\.environ(\.get)?[(\[][^)]*api_key" --include=*.py src/deepreason | wc -l)" -eq 3`

**`FORBIDDEN_MODEL_CONTROL_FIELDS` is not derived from `Route`, and must not
become so.** Four of `Route`'s fifteen field names are also refused as model
output field names; the other twenty-two forbidden names — `route`, `tools`,
`delegate`, `spawn`, `permission`, `status` and the rest — describe authority
the manifest has no field for at all. Deriving the blacklist from the route
model would look like removing a duplication and would delete most of the
firewall. The two lists answer different questions: one says what a route IS,
the other says what a model may never NAME.
`check: python -c "from deepreason.run_manifest import Route; from deepreason.llm.firewall import FORBIDDEN_MODEL_CONTROL_FIELDS as F; assert sorted(set(Route.model_fields) & F) == ['context_window_tokens', 'endpoint_id', 'model_id', 'provider']; assert len(Route.model_fields) == 15 and len(F) == 26; assert {'route', 'routes', 'tools', 'delegate', 'spawn', 'permission', 'status'} <= F" && ! grep -q "model_fields" src/deepreason/llm/firewall.py && python -m pytest tests/test_model_firewall.py -q`

**There is no route selection, no failover and no retry onto another seat.**
`endpoint_index` is a caller argument, `select_lease` raises rather than falling
back to seat zero, and a seat that terminally exhausts its smallest authorized
contract is refused at dispatch (`V6_ROUTE_SEAT_INSUFFICIENT_CAPABILITY`, see
DR-SEAM-llm-x-workflow) rather than rerouted. A "healthy route" fallback would
make the answer to "which model produced this" depend on transport luck, which
is the one thing the frozen manifest exists to prevent. Covered by the
`select_lease` check in "Where it is expressed".

**`max_tokens` and `timeout_s` are deliberately outside route identity.** The
comment in `EndpointLease.verify` says why: they are bounded process-health
controls a deterministic controller may tune and log as Measure events, and
they permit no route, model, reasoning, temperature or output-mode
substitution. The exception is a route carrying a qualified
`context_window_tokens`, where the completion side of the envelope becomes part
of the frozen capacity and `max_tokens` IS checked. Adding either field to the
unconditional set would make every logged controller adjustment a firewall
stop. Covered by the `ROUTE_LEASE_MISMATCH` check above.

**The manifest never sees a model's opinion about routing.** No path from wire
output reaches `leases_from_manifest`, `select_lease` or
`resolve_school_role_lease`: school-routed calls take an explicit
`endpoint_lease` argument the adapter refuses to synthesize, and prose asking
for another endpoint is recorded as content and changes nothing. The live
demonstration is
`tests/test_school_execution_binding_v4.py::test_prompt_and_response_route_prose_cannot_change_the_resolved_lease`,
included in the school check above.

## How to change it

The order is forced by which side is frozen, and by the fact that route bytes
are already in committed records.

1. **Read `DR-INV-frozen-surfaces` first.** `Route` is a manifest schema
   (surface 4) and the qualification pair inventory carries `route_sha256`
   (surface 5). A new route field therefore moves every route digest, every
   behavioural and decomposition grant that stores one, the manifest sha, and
   every qualification subject digest — a cache miss costing the whole battery
   (~14 min, ~1160 calls). If the field must not exist for historical routes,
   it needs the `context_window_tokens` treatment: a `model_serializer` that
   pops it when unset, so old route bytes are unchanged.
2. **A new route field moves in five places or it drifts silently.** `Route`
   (and its serializer), `Route.endpoint_spec()`, `_endpoint_from_spec` in
   `llm/adapter.py`, the `optional` map in `EndpointLease.verify`, and
   `route_from_endpoint` in `llm/firewall.py`. Miss `endpoint_spec` and the
   endpoint is built without it; miss `verify` and nothing enforces it; miss
   `route_from_endpoint` and the legacy path can never reproduce the route.
3. **Never make the digest depend on anything but the route.** `route_fingerprint`
   takes one `Route` and hashes its canonical dump. Adding context — a run id, a
   seat, a manifest sha — would make every recorded `route_sha256` unverifiable
   against the document that produced it.
4. **Decide seat-vs-identity before writing code.** "Which seat serves this
   call" is manifest policy: `SchoolExecutionPolicyV1`, `CriticismPolicyV1`,
   the per-seat plans. "Is the runtime still that seat" is the firewall. A
   change that answers the first question inside `firewall.py`, or the second
   inside `run_manifest.py`, will pass its own tests and leave the other side
   unguarded.
5. **A per-run knob goes on `Config`, never on `Route`.** A manifest field is
   permanent and enters four digests; a `Config` value is invisible to replay.

What breaks first, in the order you will see it: `ROUTE_LEASE_MISMATCH` at the
whole-ensemble preflight or the first render, before any token is spent; then
`"adapter route leases differ from the manifest"` at `bind_v6_authority`; then
`V6_BEHAVIORAL_ROUTE_MISMATCH` or `ROUTE_SEAT_PRESENTATION_ENDPOINT_MISMATCH`
from the manifest resolvers at render; then `SCHOOL_ROUTE_LEASE_MISMATCH` on a
school-routed call and `WORKFLOW_ROUTE_LEASE_MISMATCH` from
`workflow/profiles.py`. The expensive ones arrive last: a qualification cache
miss, and — on a committed root — a `route_sha256` that no longer re-derives
from the manifest route, which is a replay-validation failure rather than a bug
you can fix forward.

The tests that catch you, cheapest first: `tests/test_model_firewall.py` (0.1 s,
lease identity and the control-field list),
`tests/test_providers.py -k family` (the endpoint/lease inference agreement),
`tests/test_judge_ensemble_boundary.py` (0.2 s, the ensemble gates),
`tests/test_school_execution_binding_v4.py` (1.5 s, seat resolution),
`tests/test_v6_route_seat_profile_runtime.py` and
`tests/test_v6_route_seat_behavioral_capability_runtime.py` (4 s, the grant
lookups), then `tests/test_cli_production_doctor_v6.py` (the pair inventory the
subject digest is built from).

## Traps

- **A config that omits `family` crashed three live streams before a single
  request left the machine.** In the bronze flat suite (2026-07-13, amendment 1,
  zero tokens spent) `config/ollama-live.yaml` stamped an empty family on every
  endpoint while the compiled manifest route inferred a real one, so
  `EndpointLease.verify` failed closed on the first call of ANY root using that
  config — finding F2. The endpoint builder now defaults `family` to the same
  deterministic inference the lease uses, with an explicit config override still
  winning. The generalisation: a manifest field that is INFERRED at compile time
  and COPIED at endpoint-construction time is a drift site, and the firewall
  will report it as a route substitution rather than as a missing config key.
  Covered by the family-inference check above.
- **The two grant resolvers do not key on the same identity.**
  `resolve_route_seat_behavioral_capability` takes and compares `route_sha256`;
  `resolve_route_seat_base_profile` takes only `endpoint_id` and never computes
  a fingerprint. So route content that drifts while keeping its `endpoint_id`
  resolves the same presentation, and the whole-route agreement is carried
  elsewhere — by the lease-map equality in `bind_v6_authority`. Looking for a
  digest comparison inside the presentation resolver and concluding it is
  missing is the mistake; adding one there without checking what already covers
  it is the expensive version of the same mistake.
`check: python -c "import inspect, types, pytest; from deepreason.run_manifest import Route, RunManifestError, resolve_route_seat_base_profile as P, resolve_route_seat_behavioral_capability as B; from deepreason.llm.firewall import route_fingerprint; p=set(inspect.signature(P).parameters); assert p == {'manifest', 'role', 'seat', 'endpoint_id'}, sorted(p); assert 'route_sha256' in inspect.signature(B).parameters; assert 'route_fingerprint' not in inspect.getsource(P); r=Route(endpoint_id='a', base_url='https://h/v1', model_id='m', provider='p', family='f'); drifted=r.model_copy(update={'temperature': 0.7}); g=types.SimpleNamespace(role='judge', seat=0, endpoint_id='a', route_sha256=route_fingerprint(r)); m=types.SimpleNamespace(schema_version=6, roles={'judge': (drifted,)}, model_profile='standard', route_seat_presentation_plan=None, route_seat_behavioral_capability_plan=types.SimpleNamespace(entries=(g,))); assert P(m, role='judge', seat=0, endpoint_id='a') == 'standard'; assert pytest.raises(RunManifestError, B, m, role='judge', seat=0, endpoint_id='a', route_sha256=route_fingerprint(r)).value.code == 'V6_BEHAVIORAL_ROUTE_MISMATCH'" && python -m pytest tests/test_v6_route_seat_profile_runtime.py tests/test_v6_route_seat_behavioral_capability_runtime.py -q`
- **A lease frozen from a live endpoint cannot reproduce a manifest route that
  names a credential — and on a test config it reproduces it exactly.**
  `route_from_endpoint` drops `api_key_env`, so for a live route the
  endpoint-derived lease has a different `route_sha256` and every manifest grant
  lookup fails; for a credential-free route the two lease maps are byte-equal.
  **Residue: replacing `leases=leases_from_manifest(run_manifest)` in
  `build_adapter` with `None` leaves
  `tests/test_model_firewall.py::test_adapter_built_from_manifest_keeps_exact_route_and_mechanism`
  green** — verified by mutation — because that fixture's route carries no
  `api_key_env`. The claim is held by the structural check under "Where it is
  expressed" and by `bind_v6_authority`'s equality, not by a behavioural test.
  A fixture without a credential reference cannot see this class of defect. The
  route here sets all fifteen fields to a non-default value on purpose: the
  round trip is the only place `endpoint_spec`, `_endpoint_from_spec` and
  `route_from_endpoint` are compared field-for-field, and a fixture that leaves
  a field at its default cannot notice that link dropping it. A new `Route`
  field fails this check until it is added to the fixture, which is what forces
  it through the five-place list in "How to change it".
`check: python -c "from deepreason.run_manifest import Route; from deepreason.llm.adapter import _endpoint_from_spec; from deepreason.llm.firewall import route_fingerprint, route_from_endpoint; r=Route(endpoint_id='e', base_url='https://h/v1', model_id='m', model_revision='2026-01', provider='ollama', family='f', reasoning='high', output_mode='json_object', output_mechanism='grammar', temperature=0.25, max_tokens=512, context_window_tokens=4096, timeout_s=97, logprobs=True, api_key_env='OLLAMA_API_KEY'); assert len(Route.model_fields) == 15; assert all(getattr(r, f) is not None for f in Route.model_fields), [f for f in Route.model_fields if getattr(r, f) is None]; back=route_from_endpoint(_endpoint_from_spec(r.endpoint_spec())); assert back != r and route_fingerprint(back) != route_fingerprint(r); assert back.model_copy(update={'api_key_env': 'OLLAMA_API_KEY'}) == r, back.model_dump(); free=r.model_copy(update={'api_key_env': None}); assert route_from_endpoint(_endpoint_from_spec(free.endpoint_spec())) == free"`
- **`EndpointLease.verify` treats a missing attribute as a pass.** Only
  `base_url` and `model_id` are unconditional; the other ten — eleven when the
  route carries a qualified capacity — are compared only
  `if hasattr(endpoint, attr)`, which is what keeps `MockEndpoint` usable. The
  consequence is that an endpoint class which stops exposing `output_mechanism`
  or `reasoning` silently drops that field from the firewall instead of failing:
  the guard weakens without any test changing colour. Covered by the
  `ROUTE_LEASE_MISMATCH` check, whose bare two-attribute endpoint verifies clean
  against a fully specified route.
- **`route_fingerprint` is a frozen surface that is not filed as one.** It lives
  in `llm/firewall.py`, which `DR-INV-frozen-surfaces` does not name, yet four
  readers re-derive recorded `route_sha256` values from manifest routes at
  replay. The serializer comment on `Route` — "Preserve historical route bytes
  while making an explicit qualified capacity part of route and manifest
  identity" — is the record of this having already bitten once: a new field had
  to be made invisible when unset precisely so old routes kept their digests.
  Treat any edit to `route_fingerprint`, to `Route`'s field set, or to its
  serializer as an edit to every committed root.
`check: grep -q "if receipt.route_sha256 != route_fingerprint(route):" src/deepreason/invariants.py && grep -q "if lease.route_sha256 != route_fingerprint(route):" src/deepreason/verification/report.py && grep -q "if route_fingerprint(route) != route_lease.route_sha256:" src/deepreason/workflow/replay.py && grep -q "lease.route_sha256 == route_fingerprint(route)," src/deepreason/workflow/nonconjecture_recovery.py && grep -q "^from deepreason.llm.firewall import route_fingerprint$" src/deepreason/invariants.py && grep -q "Preserve historical route bytes" src/deepreason/run_manifest.py`
- **A single-model run cannot hold a rubric trial, and the manifest is where you
  find that out too late.** The same bronze amendment records the design
  consequence: `require_cross_family_judge_ensemble` needs two judge seats from
  distinct families, so three "pure single-model" streams were impossible by the
  harness's own normative invariant and the suite was amended to pin judge seat
  2 to a foreign family in every stream. The gate reads leases, so it is
  decidable at compile time from `manifest.roles` alone — check it while
  designing the route table, not after the first rubric trial refuses.
