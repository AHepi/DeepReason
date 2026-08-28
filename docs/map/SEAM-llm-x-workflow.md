<!-- DR-SEAM-llm-x-workflow -->
Verified-at: e9fac8671
Verify: python tools/docs_verify.py
Owns: src/deepreason/llm/adapter.py, src/deepreason/workflow/transaction.py, src/deepreason/workflow/transaction_service.py, src/deepreason/workflow/repair_transaction.py, src/deepreason/bridge/transactional_adapter.py
Sides: DR-SUB-llm, DR-SUB-workflow

# llm x workflow

## The agreement

`workflow/` decides by what recorded authority a provider may be spoken to;
`llm/` is the only place that speaks to one. Under RunManifest v6 the adapter
promises never to dispatch without an `AuthorizedDispatch` — a durable
preparation, a settled token reservation, a context exposure receipt and an
authorization bundle the workflow has already appended — and the workflow
promises that the bundle names the exact request: work id, attempt index,
contract id, route lease and prompt digest. The adapter re-derives all five
from the bytes it is about to send and refuses on any difference, so
"authorized" and "sent" cannot drift. The workflow also owns the meter for that
call: it reserves before issue, and the adapter neither gates nor books, only
asserts that the reservation's bound equals the bound it would have computed
itself. One bundle buys exactly one provider request — the adapter's internal
repair loop is clamped off and a second attempt raises rather than reusing the
authority — so every model-facing correction is a separately prepared work item
with its own reservation and its own terminal. In the other direction the
adapter returns an `LLMCall` (or hangs one on `.spend` when it raises), and the
CALLER, never the adapter, turns it into `ProviderAttemptV1`,
`SemanticAdmissionV1` and `WorkTerminalV1`. The dependency arrow is one-way:
`workflow/` imports `llm/` at module scope in eight modules, `llm/` imports
`workflow/` only inside two function bodies, so importing the whole `llm`
package loads no workflow module at all.

Twenty-one modules import both packages (`informal/trial.py` joined this
count 2026-08-13, defended-trial-wiring tranche: its own defender/judge/
variator calls now dispatch through `workflow/transaction_service.py`).
Five carry the agreement. (`workflows/`
— the website package — is a different directory whose name merely starts the
same way, so every count below matches `deepreason.workflow` followed by a dot
or a space, and every import-shape count matches `import` as well as `from`.)
`check: python -c "import importlib, pkgutil, re, sys, pathlib, deepreason.llm as L; [importlib.import_module('deepreason.llm.' + m.name) for m in pkgutil.iter_modules(L.__path__)]; assert not [m for m in sys.modules if m == 'deepreason.workflow' or m.startswith('deepreason.workflow.')]; s=pathlib.Path('src/deepreason/llm/adapter.py').read_text(); assert not re.search(r'^(from|import) deepreason\.workflow', s, re.M); assert len(re.findall(r'^\s+(from|import) deepreason\.workflow', s, re.M)) == 2" && test "$(grep -rnE "deepreason\.workflow[. ]" --include=*.py src/deepreason/llm/ | wc -l)" -eq 2 && test "$(grep -rlE "^(from|import) deepreason\.llm" --include=*.py src/deepreason/workflow/ | wc -l)" -eq 8 && grep -q "^from deepreason.llm.budget import" src/deepreason/workflow/transaction_service.py && grep -q "from deepreason.workflow.trace import ConjectureControlTrace" src/deepreason/workflow/__init__.py && test "$(for f in $(grep -rl "deepreason\.llm" --include=*.py src/deepreason); do grep -qE "deepreason\.workflow[. ]" "$f" && echo x; done | wc -l)" -eq 21`

## Where it is expressed

| Site | File | Symbol | What it enforces |
|---|---|---|---|
| Global guard | `llm/adapter.py` | `call(...)`, first branch on `transaction_authority_required` | a v6 adapter refuses any dispatch with no bundle |
| Guard armed at build | `llm/adapter.py` | `build_adapter`, `transaction_authority_required=(run_manifest ... schema_version == 6)` | the mode is derived from the manifest, never chosen by a caller |
| Binding | `llm/adapter.py` | `bind_v6_authority(harness, manifest)` | one adapter, one harness, one manifest; refuses without durable model classification or a route-seat behavioral plan |
| The capability object | `workflow/transaction.py` | `AuthorizedDispatch` (preparation, reservation record, exposure receipt, bundle, live `Reservation`) | the only type `call` accepts as authority |
| Dispatch identity | `workflow/transaction.py` | `DispatchAuthorizationBundleV1.verify_dispatch` | "dispatch differs from its authorization bundle" |
| Prompt freeze | `llm/adapter.py` | `preview_request` / `call`, both through `_render_request` | the digest bound at `WORK_ISSUED` is the digest dispatched — so the two sides' `conservative_prompt_bound` are equal by construction |
| Atomic issue | `workflow/transaction_service.py` | `reserve_dispatch` → `finalize_dispatch` (`issue`) | plans, reservation, exposure and bundle land in one append or none |
| Meter ownership | `workflow/transaction_service.py`, `llm/budget.py` | `TokenMeter.reserve` at `reserve_dispatch`; `call` consumes `reservation_record.completion_bound_tokens` | the workflow books; the adapter SPENDS WHAT WAS BOOKED and checks the arithmetic |
| Repair ceiling | `llm/adapter.py`, `workflow/repair_transaction.py` | `retry_max=(0 if dispatch_authorization ...)`; `repair_schema_failure`, which builds the `V6PatchRepairSession` defined in `llm/repair.py` | one bundle, one request; the ceiling is the manifest's grant |
| Route/contract agreement | `llm/adapter.py`, `workflow/transaction_service.py`, `workflow/profiles.py`, `workflow/replay.py` | `resolve_route_seat_behavioral_capability` (defined in `run_manifest.py`; called once each at preparation, render and replay), `resolve_conjecture_route`, `_manifest_route` | the contract is frozen for the seat, and the seat is the manifest's route |
| Live route liveness | `llm/adapter.py` | `_require_transactional_route_dispatchable` | a route seat that exhausted its smallest contract cannot be dispatched, even mid-transaction |
| Presentation authority | `llm/adapter.py` | `_transactional_base_profile_for` / `_transactional_profile_for` | the profile comes from the manifest plus the durable compact transition, never from adapter state |
| Failure carrier | `llm/adapter.py` | `_spend(attempts)`, bound to `.spend` at nine sites | tokens already spent reach the record even when the call raises |
| Terminal from a failure | callers | `record_provider_attempt(call=<the spend>, outcome="transport_failure", ...)` in seven modules (six spell the argument `spend`; `repair_transaction` spells it `transport_spend`) | a call that touched the provider still gets a durable attempt |
| Budget denial | `workflow/transaction_service.py` | `reserve_dispatch` → `WorkTerminalV1(status="budget_denied")` → `WorkBudgetDenied` | a refused reservation is a typed terminal, not an adapter exception |
| One action carries a call | `harness.py` | `record_transaction_transition(..., llm=)` | "only provider_result may carry an LLM call" |
| Replay pairing | `workflow/replay.py` | `PROVIDER_RESULT` branch of `_apply_transaction` | the stored attempt and the logged `LLMCall` must agree on bundle, contract, lease, prompt digest, raw blob and token total |
| Mid-flight recovery | `workflow/transaction_service.py` | `recover_incomplete` | unissued work is abandoned, issued-but-unanswered work is abandoned, an unadmitted result is handed back for validation |
| Deterministic resume | `workflow/{conjecture,nonconjecture,atomic}_recovery.py` | `recover_conjecture_admission`, `recover_nonconjecture_admission`, `recover_atomic_child_output` (the atomic one is NOT an `_admission`) | the raw blob named by `ProviderAttemptV1` is re-validated with no provider present |
| Canonical wrapper | `bridge/transactional_adapter.py` | `TransactionalBridgeAdapter.call` | every bridge model call becomes prepare → plan → issue → call → attempt → admission → terminate |
| Controller-v1 generation | `llm/adapter.py`, `workflow/trace.py` | `workflow_dispatch_observer` / `workflow_repair_observer`, `ConjectureControlTrace.require_authority` | the pre-v6 shape: observe-then-dispatch, with `WorkflowAuthorizationError` imported from `llm/adapter.py` |

Every symbol above resolves in the file beside it. Rows rot by rename, so the
table carries its own check rather than relying on the section checks below,
which cover most of these names but not all of them.
`check: python -c "import pathlib; rows=[('src/deepreason/llm/adapter.py', ('def build_adapter', 'transaction_authority_required=(', 'def bind_v6_authority', 'def preview_request', 'def _render_request', 'def _require_transactional_route_dispatchable', '_transactional_base_profile_for', '_transactional_profile_for', 'def _spend', 'workflow_dispatch_observer', 'workflow_repair_observer', 'resolve_route_seat_behavioral_capability')), ('src/deepreason/workflow/transaction.py', ('class AuthorizedDispatch', 'def verify_dispatch', 'class DispatchAuthorizationBundleV1', 'class WorkBudgetDenied')), ('src/deepreason/workflow/transaction_service.py', ('def reserve_dispatch', 'def finalize_dispatch', 'def record_provider_attempt', 'def recover_incomplete', 'resolve_route_seat_behavioral_capability')), ('src/deepreason/workflow/profiles.py', ('resolve_conjecture_route',)), ('src/deepreason/workflow/replay.py', ('def _apply_transaction', '_manifest_route', 'resolve_route_seat_behavioral_capability')), ('src/deepreason/workflow/repair_transaction.py', ('def repair_schema_failure', 'V6PatchRepairSession')), ('src/deepreason/llm/repair.py', ('class V6PatchRepairSession',)), ('src/deepreason/llm/budget.py', ('class TokenMeter', 'def reserve')), ('src/deepreason/run_manifest.py', ('def resolve_route_seat_behavioral_capability',)), ('src/deepreason/harness.py', ('def record_transaction_transition', 'llm=None')), ('src/deepreason/workflow/conjecture_recovery.py', ('def recover_conjecture_admission',)), ('src/deepreason/workflow/nonconjecture_recovery.py', ('def recover_nonconjecture_admission',)), ('src/deepreason/workflow/atomic_recovery.py', ('def recover_atomic_child_output',)), ('src/deepreason/bridge/transactional_adapter.py', ('class TransactionalBridgeAdapter', '    def call(')), ('src/deepreason/workflow/trace.py', ('class ConjectureControlTrace', 'def require_authority'))]; missing=[(f, sym) for f, syms in rows for sym in syms if sym not in pathlib.Path(f).read_text()]; assert not missing, missing"`

The bundle's identity is exactly five fields plus the reservation reference; the
adapter passes all six by keyword at its one call site; and the prompt digest in
that tuple is computed the same way on both sides — once when the reservation is
taken, once when the exposure is written, once at dispatch, and once more from
the stored attempt at replay.
`check: python -c "import inspect, re, pathlib, pytest; from deepreason.workflow.transaction import DispatchAuthorizationBundleV1 as B; from deepreason.workflow.models import RouteLeaseRefV1 as R; want=['work_id','attempt_index','contract_id','route_lease','prompt_sha256','reservation_ref']; sig=[n for n in inspect.signature(B.verify_dispatch).parameters if n != 'self']; site=re.search(r'verify_dispatch\(\n(.*?)\n            \)', pathlib.Path('src/deepreason/llm/adapter.py').read_text(), re.S).group(1); passed=re.findall(r'^\s+(\w+)=', site, re.M); assert sig == passed == want, (sig, passed); i='sha256:'+'0'*64; d='1'*64; r=R(role='conjecturer', seat=0, endpoint_id='e', route_sha256=d); b=B.create(work_id=i, attempt_index=0, contract_id='c', route_lease=r, prompt_sha256=d, reservation_ref=i, exposure_receipt_ref=i, issue_transition_ref=i); ok=dict(work_id=i, attempt_index=0, contract_id='c', route_lease=r, prompt_sha256=d, reservation_ref=i); b.verify_dispatch(**ok); bad=dict(work_id='sha256:'+'2'*64, attempt_index=1, contract_id='c2', route_lease=R(role='conjecturer', seat=1, endpoint_id='e', route_sha256=d), prompt_sha256='3'*64, reservation_ref='sha256:'+'4'*64); [pytest.raises(ValueError, b.verify_dispatch, **{**ok, k: v}) for k, v in bad.items()]" && grep -q 'raise ValueError("dispatch differs from its authorization bundle")' src/deepreason/workflow/transaction.py && grep -q 'prompt_sha256 = hashlib.sha256(prompt.encode("utf-8")).hexdigest()' src/deepreason/llm/adapter.py && test "$(grep -c 'prompt_sha256 = hashlib.sha256(prompt.encode("utf-8")).hexdigest()' src/deepreason/workflow/transaction_service.py)" -eq 2 && grep -q 'raise ValueError("reserved prompt differs from dispatch prompt")' src/deepreason/workflow/transaction_service.py && grep -q "attempt.prompt_sha256 != item.authorization.prompt_sha256" src/deepreason/workflow/replay.py`

A v6 adapter refuses an unbound call, a pre-v6 adapter keeps the legacy path,
and the bridge wrapper is where an ordinary adapter is switched into
transactional mode — binding once, to one harness and one manifest, before it
can be called at all. Do not read
`test_transaction_required_adapter_rejects_unbound_dispatch` as covering the
first clause: it exercises `preview_request` and matches a DIFFERENT refusal
("behavioral manifest authority"). The `call()` guard is covered only by the
inline probe in the check below, which is why the probe is there.
`check: grep -q "if self.transaction_authority_required and dispatch_authorization is None:" src/deepreason/llm/adapter.py && python -c "import json, tempfile, pathlib, pytest; from deepreason.llm.adapter import LLMAdapter, WorkflowAuthorizationError; from deepreason.llm.contracts import ConjecturerOutput; from deepreason.llm.endpoints import MockEndpoint; from deepreason.storage.blobs import BlobStore; e=MockEndpoint([json.dumps({'candidates': [{'content': 'x', 'typicality': 0.5}]})]); a=LLMAdapter({'conjecturer': e}, BlobStore(pathlib.Path(tempfile.mkdtemp()) / 'b'), transaction_authority_required=True); pytest.raises(WorkflowAuthorizationError, a.call, 'conjecturer', 'PACK', ConjecturerOutput).match('RunManifest v6 provider dispatch requires a bound transaction'); assert e.last_transport_attempts == 0" && python -c "import re, pathlib; q=chr(34); s=pathlib.Path('src/deepreason/llm/adapter.py').read_text(); msgs=['RunManifest v6 provider dispatch requires a bound transaction','dispatch_authorization must be an AuthorizedDispatch','transactional authorization replaces legacy work callbacks','pre-rendered requests require transactional dispatch authorization','workflow dispatch observation requires an unbound conjecturer call','transactional adapter is already bound to another harness','transactional adapter is already bound to another manifest']; missing=[m for m in msgs if not re.search(r'raise \w+\(\s*' + re.escape(q + m + q), s)]; assert not missing, missing" && grep -q "self._adapter.transaction_authority_required = True" src/deepreason/bridge/transactional_adapter.py && grep -q "self._adapter.bind_v6_authority(harness, manifest)" src/deepreason/bridge/transactional_adapter.py && python -m pytest tests/test_v6_global_dispatch_guard.py::test_transaction_required_adapter_rejects_unbound_dispatch tests/test_v6_global_dispatch_guard.py::test_legacy_adapter_keeps_unbound_dispatch_compatibility tests/test_v6_bridge_transactions.py::test_every_v6_bridge_call_has_an_independent_complete_transaction -q`

Under an authorization the adapter's own meter gate and its own reservation are
both skipped, and **the completion cap is CONSUMED from the reservation, never
recomputed**: `transport_limits["max_tokens"]` reads
`reservation_record.completion_bound_tokens`, the number the workflow already
booked and already recorded. One cap per dispatch, defined once in
`LLMAdapter._completion_cap` and returned by `preview_request`. The behavioural
half is the ceiling test: work items, logged calls and metered calls are equal,
and nothing is left reserved.

That consumption is the whole guarantee, and it is structural. A second
expression reading the live endpoint would part from the booked number the
moment a controller settles a seat between issue and dispatch — which is
exactly what killed epoch-3 attempt 3 (see Traps). The prompt term cannot
contribute either: `verify_dispatch` pins the rendered bytes to the bundle
digest before the guard runs, so both sides bound the same string. The guard
therefore survives as a corruption detector — reachable only if a live
`Reservation` disagrees with its own `TokenReservationV2` — and when it fires
it writes a diagnostic blob carrying both bounds, both prompt bounds, the
request length and digest, and the live endpoint cap, so the refusal is
diagnosable from the committed root alone.

**Residue closed 2026-08-23:** `tests/test_v6_reservation_bound_authority.py`
now constructs the disagreeing `AuthorizedDispatch` this seam previously
recorded as untested, and pins the consumption shape so reintroducing a second
cap expression fails the suite rather than a live run.
`check: grep -q "if self.meter is not None and dispatch_authorization is None:" src/deepreason/llm/adapter.py && grep -q "^            elif self.meter is not None:" src/deepreason/llm/adapter.py && python -c "import inspect, re; from deepreason.llm.adapter import LLMAdapter; prev=inspect.getsource(LLMAdapter.preview_request); call=inspect.getsource(LLMAdapter.call); assert '_completion_cap(endpoint, lease)' in prev, 'preview stopped using the shared cap'; assert isinstance(inspect.getattr_static(LLMAdapter, '_completion_cap'), staticmethod); cap=re.search(r'transport_limits = \{\n\s+.max_tokens.: \((.*?)\),\n\s+.timeout_s.', call, re.S); assert cap, 'call no longer consumes a cap expression'; body=' '.join(cap.group(1).split()); assert 'reservation_record.completion_bound_tokens' in body, body; assert 'getattr(endpoint,' not in body, body; assert re.search(r'if reservation\.amount != reservation_bound:', call), 'guard removed'; assert 'transactional reservation bound differs from rendered ' in call, 'refusal message moved'; assert 'diagnostic_ref=self.blobs.put(' in call, 'refusal no longer records both sides'" && python -c "from deepreason.llm.budget import TokenMeter, conservative_prompt_bound; t='hello world ' * 40; r=TokenMeter(budget=10**9).reserve(prompt_text=t, max_tokens=77); assert r.amount == conservative_prompt_bound(t) + 77, r.amount" && grep -q "conservative_prompt_bound," src/deepreason/workflow/transaction_service.py && grep -q "prompt_bound = conservative_prompt_bound(prompt)" src/deepreason/workflow/transaction_service.py && python -m pytest "tests/test_v6_contract_schema_repair_runtime.py::test_manifest_grant_is_the_exact_provider_call_ceiling" tests/test_v6_reservation_bound_authority.py -q`

One bundle authorizes one request: the repair session is built with
`retry_max=0`, which is exactly one attempt, and a second pass raises before
any dispatch.
`check: grep -q "retry_max=(0 if dispatch_authorization is not None else self.retry_max)," src/deepreason/llm/adapter.py && python -c "import re, pathlib; q=chr(34); s=pathlib.Path('src/deepreason/llm/adapter.py').read_text(); assert re.search(r'if attempt != 0:\n\s+raise WorkflowAuthorizationError\(\n\s+' + re.escape(q + 'transactional repair requires a new authorization bundle' + q), s)" && python -c "import inspect; from deepreason.llm.repair import BoundedRepairSession as S; from deepreason.llm.adapter import WorkflowAuthorizationError as W; assert 'spend' in inspect.signature(W.__init__).parameters; assert S(contract='c', schema={'type':'object'}, initial_request='x', retry_max=0).attempt_count == 1" && python -m pytest tests/test_v6_live_repair_transactions.py::test_conjecture_patch_is_a_distinct_authorized_work_item -q`

The contract-for-this-seat agreement is checked three times over the same
manifest fields — at preparation, at render, and at replay — and terminal
route-seat exhaustion is re-checked immediately before dispatch as well as
durably.
`check: python -c "import re, pathlib; P=lambda f: pathlib.Path(f).read_text(); A=P('src/deepreason/llm/adapter.py'); T=P('src/deepreason/workflow/transaction_service.py'); R=P('src/deepreason/workflow/replay.py'); F=P('src/deepreason/workflow/profiles.py'); assert re.search(r'grant\.contract_id for grant in behavioral\.contracts\n\s+\}:\n\s+raise WorkflowAuthorizationError\(\n\s+.wire contract differs from frozen route-seat behavioral authority.', A), 'render'; assert re.search(r'grant\.contract_id for grant in behavioral\.contracts\n\s+\}:\n\s+raise RunManifestError\(\n\s+.V6_BEHAVIORAL_CONTRACT_NOT_AUTHORIZED.', T), 'preparation'; assert re.search(r'if lease\.route != manifest\.roles\[.conjecturer.\]\[lease\.seat\]:\n\s+raise WorkflowProfileError\(.WORKFLOW_ROUTE_LEASE_MISMATCH.\)', F), 'lease'; assert re.search(r'if route_fingerprint\(route\) != route_lease\.route_sha256:\n\s+raise ValueError\(.compact recovery route digest differs from the manifest.\)', R), 'replay'; n=len(re.findall(r'in self\.harness\.workflow_state\.insufficient_capability_by_route_seat\n\s+\):\n\s+raise RunManifestError\(\n\s+.V6_ROUTE_SEAT_INSUFFICIENT_CAPABILITY.', T)); assert n == 3, n; assert re.search(r'if key in state\.insufficient_capability_by_route_seat:\n\s+raise WorkflowAuthorizationError\(\n\s+.V6_ROUTE_SEAT_INSUFFICIENT_CAPABILITY: route seat has ', A), 'live'" && grep -q "self._require_transactional_route_dispatchable(route_ref)" src/deepreason/llm/adapter.py && python -m pytest tests/test_v6_insufficient_capability_terminal.py -q`

A typed failure carries its spend, seven caller modules convert that spend into a
durable transport-failure attempt rather than losing it, and whichever way the
call ends its `LLMCall` crosses into the control plane at exactly one action —
where replay re-checks it against the issued authority.
`check: python -c "import inspect; from deepreason.llm.repair import SchemaRepairError as E; assert 'spend' in inspect.signature(E.__init__).parameters" && test "$(grep -c "spend = _spend(\|spend=_spend(" src/deepreason/llm/adapter.py)" -eq 10 && test "$(grep -rl 'outcome="transport_failure"' --include=*.py src/deepreason | wc -l)" -eq 7 && python -c "import re, pathlib; R=pathlib.Path('src/deepreason/workflow/replay.py').read_text(); H=pathlib.Path('src/deepreason/harness.py').read_text(); assert re.search(r'if \(llm is not None\) != \(\n\s+transition\.transition_kind == WorkTransitionKind\.PROVIDER_RESULT\n\s+\):\n\s+raise ValueError\(.only provider_result may carry an LLM call.\)', H), 'one-action'; assert re.search(r'if call is None or call\.work_order_id != transition\.work_id:\n\s+raise ValueError\(.provider result requires its work-bound LLM call.\)', R), 'pairing'; assert re.search(r'or call\.dispatch_authorization_ref != item\.authorization\.id\n\s+or attempt\.authorization_bundle_ref != item\.authorization\.id\n\s+or attempt\.contract_id != item\.authorization\.contract_id\n\s+or attempt\.route_lease != item\.authorization\.route_lease\n\s+or attempt\.prompt_sha256 != item\.authorization\.prompt_sha256\n\s+or attempt\.raw_ref != \(call\.raw_ref or None\)\n\s+\):\n\s+raise ValueError\(.provider result differs from issued authority.\)', R), 'six agreements'; assert re.search(r'!= call\.tokens\n\s+\):\n\s+raise ValueError\(.provider result usage differs from its LLM call.\)', R), 'token total'" && python -m pytest tests/test_v6_controller3_replay_verification.py::test_provider_result_without_authorized_attempt_fails_closed tests/test_v6_bridge_transactions.py::test_v6_bridge_transport_failure_is_durably_terminalized -q`

A refused reservation is terminalized before it becomes an exception. Eight
modules handle `WorkBudgetDenied`, and each handler's shape is load-bearing:
six transactional call sites re-raise it ahead of their broad handler so the
work is not terminated twice (`informal/trial.py`'s `_v6_transactional_
trial_call` joined this set 2026-08-13, defended-trial-wiring tranche, with
the identical shape); `rules/conj.py` re-raises too, except on the
context-continuation path where a denied child IS the answer and the caller
returns no candidates; `scheduler/scheduler.py` is the consumer, not a call
site, and returns because the terminal is already durable.
`check: grep -q "raise WorkBudgetDenied(terminal) from error" src/deepreason/workflow/transaction_service.py && grep -q 'status="budget_denied",' src/deepreason/workflow/transaction_service.py && test "$(grep -rlE "^ *except WorkBudgetDenied:" --include=*.py src/deepreason | wc -l)" -eq 8 && python -c "import re, pathlib; bad=[f for f in ('src/deepreason/bridge/transactional_adapter.py','src/deepreason/workflow/repair_transaction.py','src/deepreason/scratch/authoring.py','src/deepreason/referee.py','src/deepreason/rules/crit.py','src/deepreason/informal/trial.py') if not re.search(r'except WorkBudgetDenied:\n\s+(#[^\n]*\n\s+)*raise\n\s+except (BaseException|Exception):', pathlib.Path(f).read_text())]; assert not bad, bad; assert re.search(r'except WorkBudgetDenied:\n\s+if v6_context_continuation is not None:\n\s+return \[\]\n\s+raise\n', pathlib.Path('src/deepreason/rules/conj.py').read_text()), 'conj'; assert re.search(r'except WorkBudgetDenied:\n\s+(#[^\n]*\n\s+)*return\n\s+except \(SchemaRepairError, EndpointError\) as error:', pathlib.Path('src/deepreason/scheduler/scheduler.py').read_text()), 'scheduler'" && python -m pytest tests/test_v6_live_repair_transactions.py::test_repair_budget_denial_has_no_repair_exposure_or_dispatch tests/test_v6_context_continuation.py::test_child_budget_denial_has_no_exposure_and_no_dispatch -q`

## What is deliberately absent

**Without an authorization the v6 adapter may do nothing at all — and with one,
six of its own faculties are switched off.** It does not gate the meter
(`meter.check()` is guarded by `dispatch_authorization is None`); it does not
book a reservation (`meter.reserve` sits in the `elif`); it does not repair
(`retry_max=0`); it does not change presentation (`_mark_compact_recovery` and
`rehydrate_compact_recovery` both return immediately); it does not accept a
per-call profile that differs from the frozen one
(`V6ModelProfileOverrideForbidden`); and it does not choose its own contract
(the wire contract must appear in the route seat's frozen behavioral grants).
Reading any of these as an adapter that "forgot" to do its job and restoring
one gives the run a provider request no record authorizes.
`check: python -c "import re, pathlib; s=pathlib.Path('src/deepreason/llm/adapter.py').read_text(); body=lambda n: re.search(r'\n    def ' + n + r'\(.*?(?=\n    def )', s, re.S).group(0); assert re.search(r'\n        if self\.transaction_authority_required:\n            return\n', body('_mark_compact_recovery')), 'mark'; assert re.search(r'\n        if self\.transaction_authority_required:\n            return frozenset\(\)\n', body('rehydrate_compact_recovery')), 'rehydrate'; assert re.search(r'grant\.contract_id for grant in behavioral\.contracts\n\s+\}:\n\s+raise WorkflowAuthorizationError\(\n\s+.wire contract differs from frozen route-seat behavioral authority.', s), 'own contract'" && grep -q "if self.meter is not None and dispatch_authorization is None:" src/deepreason/llm/adapter.py && grep -q "^            elif self.meter is not None:" src/deepreason/llm/adapter.py && grep -q "retry_max=(0 if dispatch_authorization is not None else self.retry_max)," src/deepreason/llm/adapter.py && grep -q "class V6ModelProfileOverrideForbidden" src/deepreason/llm/adapter.py && python -m pytest tests/test_v6_profile_authority.py -q`

**`llm/` appends no event and writes no workflow record.** The whole harness
surface it touches is two names: `harness.workflow_state`, read to resolve
presentation and route liveness, and `harness.bind_transaction_manifest`, which
binds replay state to the manifest in memory and appends nothing. It constructs
exactly one workflow type, `RouteLeaseRefV1`, purely to hand back for
verification. Every durable consequence is written by the caller through
`harness.record_transaction_transition`. This is what keeps a transport bug
from becoming a control-plane bug: the adapter can refuse, but it cannot
record. The check is a WHITELIST, not a denylist, because a denylist of
mutator names passes the moment someone adds a mutator with a new name.
`check: python -c "import re, pathlib, glob, inspect; used=set(); [used.update(re.findall(r'harness\.([A-Za-z_]+)', pathlib.Path(f).read_text())) for f in glob.glob('src/deepreason/llm/**/*.py', recursive=True)]; assert used == {'bind_transaction_manifest', 'workflow_state'}, sorted(used); from deepreason.harness import Harness; b=inspect.getsource(Harness.bind_transaction_manifest); assert not re.search(r'append|objects\.put|record_', b), b" && ! grep -rqE "record_transaction_transition|objects\.put|append_event" --include=*.py src/deepreason/llm && grep -q "state = harness.workflow_state" src/deepreason/llm/adapter.py && test "$(grep -c "RouteLeaseRefV1(" src/deepreason/llm/adapter.py)" -eq 1 && grep -q "    def record_transaction_transition(" src/deepreason/harness.py`

**Recovery has no provider boundary, and that is the whole point of it.** None
of `recover_conjecture_admission`, `recover_nonconjecture_admission` or
`recover_atomic_child_output` takes an adapter; `nonconjecture_recovery` even
constructs its `ScratchAuthoringService` with `adapter=None`. No module under
`workflow/` names `LLMAdapter`, `build_adapter`, `OpenAICompatEndpoint` or calls
`.complete(`. The single exception is `repair_transaction.repair_schema_failure`,
which dispatches through an adapter it is HANDED and has no `retry_max`
parameter of its own — the ceiling is the manifest's grant, not a caller's
argument. A crashed run therefore resumes by re-validating the raw blob a
`ProviderAttemptV1` already names, which is why the same result can be admitted
twice without spending a second token. Counting the dispatch sites is the
clause that matters: a denylist of adapter type names is evaded by any new
parameter name, but `workflow/` may contain exactly two `.call(` /
`.preview_request(` sites and both must be in `repair_transaction.py`.
`check: python -c "import inspect; from deepreason.workflow import conjecture_recovery as c, nonconjecture_recovery as n, atomic_recovery as a, repair_transaction as r; assert not [f for f in (c.recover_conjecture_admission, n.recover_nonconjecture_admission, a.recover_atomic_child_output) if 'adapter' in inspect.signature(f).parameters]; assert 'adapter' in inspect.signature(r.repair_schema_failure).parameters; assert 'retry_max' not in inspect.signature(r.repair_schema_failure).parameters" && python -c "from deepreason.llm.adapter import LLMAdapter, build_adapter; from deepreason.llm.endpoints import OpenAICompatEndpoint; assert callable(OpenAICompatEndpoint.complete)" && ! grep -rqE "LLMAdapter|build_adapter|OpenAICompatEndpoint|\.complete\(" --include=*.py src/deepreason/workflow && test "$(grep -rn "\.call(\|\.preview_request(" --include=*.py src/deepreason/workflow/ | wc -l)" -eq 2 && test "$(grep -rn "\.call(\|\.preview_request(" --include=*.py src/deepreason/workflow/ | grep -c "^src/deepreason/workflow/repair_transaction.py:")" -eq 2 && grep -q "adapter=None," src/deepreason/workflow/nonconjecture_recovery.py && grep -q "The provider boundary is deliberately absent from this module" src/deepreason/workflow/conjecture_recovery.py`

**Issued work is never dispatched again.** `recover_incomplete` closes what it
cannot finish — unissued preparations and issued-but-unanswered attempts become
`abandoned` terminals — and returns only the attempts whose raw result still
needs deterministic validation. Re-issuing an interrupted attempt would be the
intuitive fix and is exactly wrong: the reservation is gone, the exposure
receipt already asserts what the model saw, and a second request against the
same bundle has no authority.
`check: grep -q "Issued work is never dispatched again" src/deepreason/workflow/transaction_service.py && python -c "import inspect, re; from deepreason.workflow.transaction_service import InquiryTransactionService as S; b=inspect.getsource(S.recover_incomplete); assert re.search(r'if not item\.issued:\n\s+self\.terminate\((?:[^\n]*\n)*?\s+status=.abandoned.,\n\s+reason_code=.prepared_unissued_recovery.,', b), 'unissued'; assert re.search(r'elif provider is None:\n\s+self\.terminate\((?:[^\n]*\n)*?\s+status=.abandoned.,\n\s+reason_code=.issued_result_unknown_recovery.,', b), 'unanswered'; assert re.search(r'elif admission is None:\n\s+pending_admission\.append\(provider\)', b), 'pending'; assert b.rstrip().endswith('return tuple(pending_admission)'), 'return'" && python -m pytest tests/test_v6_transaction_qualification.py::test_recovery_terminalizes_prepared_but_unissued_work tests/test_v6_transaction_qualification.py::test_issued_without_provider_result_recovers_as_unknown_abandonment tests/test_v6_contract_schema_repair_runtime.py::test_replay_of_exhausted_repair_chain_never_redispatches tests/test_v6_nonconjecture_recovery.py::test_scheduler_recovers_valid_critic_without_provider_dispatch -q`

**Controller-v1 callbacks and a controller-v3 bundle may not coexist in one
call.** Passing `work_order_id` or `workflow_dispatch_observer` alongside
`dispatch_authorization` is a `ValueError`, and the observer path is restricted
to an unbound conjecturer call. Two generations of process authority describing
one provider request would make the record ambiguous about which one authorized
it. The absence is symmetric: `pre_rendered_request` exists only for the v3
repair path — `repair_transaction.py` is its only external caller — and is
refused without an authorization. Both refusals are pinned by the guard check
below the "Where it is expressed" table; only the caller restriction is checked
here.
`check: test "$(grep -rln "pre_rendered_request=" --include=*.py src/deepreason | grep -v "^src/deepreason/llm/adapter.py$" | tr -d '\n')" = "src/deepreason/workflow/repair_transaction.py"`

**`llm/` has no module-scope import of `workflow/`.** The two function-local
imports inside `call` are what keep the graph acyclic while still letting the
adapter type-check the capability it was given. Hoisting them to the top of
`adapter.py` looks like tidying and is an immediate `ImportError`: any
`deepreason.workflow.*` import runs `workflow/__init__.py`, which imports
`workflow/trace.py`, which imports `WorkflowAuthorizationError` from the
partially-initialized `llm/adapter.py`. The check is in "The agreement" above.

## How to change it

The order is forced by which side is frozen. Start at the manifest, end at the
callers; going the other way produces a record whose authority does not exist.

1. **Read `DR-INV-frozen-surfaces` first.** The route-seat behavioral capability
   plan, the schema-repair grants and the compact-recovery policy are manifest
   surfaces: widening any of them moves every qualification subject digest and
   is a 14-minute requalification, not a free change. A per-run mode goes on
   `Config`.
2. **Change the durable record before anything that produces it.** A new field
   on `DispatchAuthorizationBundleV1` means, in this order:
   `workflow/transaction.py` (the model and `verify_dispatch`),
   `transaction_service.finalize_dispatch` (which fills it),
   `llm/adapter.py` (which re-derives and passes it), `record_provider_attempt`
   (if the attempt must carry it), and the `PROVIDER_RESULT` branch of
   `workflow/replay.py` (which re-checks it). Missing the replay branch means
   the field is written and never verified.
3. **Anything that enters `WorkflowReplayState.digest` is append-only in the
   subtler sense.** See `DR-SUB-workflow`'s trap: a new section must appear only
   when non-empty, or every historical replay-valid root changes digest.
4. **Move the failure paths with the success path.** Each of the six caller
   modules reaches the same five OUTCOMES — `WorkBudgetDenied` handled,
   `EndpointError` → transport-failure attempt, `SchemaRepairError` →
   `repair_schema_failure`, unexpected failure → abandon, success → attempt +
   admission + terminal — but NOT the same syntax: `referee.py` dispatches on
   `isinstance` inside one `except Exception` rather than with separate
   `except` clauses, and `conj.py`/`crit.py` use `except Exception` where the
   others use `except BaseException`. Match the outcomes, not the shape. A
   change that updates the success arm alone leaves a crash mid-call
   unrecoverable, which no happy-path test will surface.
`check: python -c "import pathlib; mods=('src/deepreason/rules/conj.py','src/deepreason/rules/crit.py','src/deepreason/workflow/repair_transaction.py','src/deepreason/bridge/transactional_adapter.py','src/deepreason/scratch/authoring.py','src/deepreason/referee.py'); arms=('except WorkBudgetDenied', 'outcome=' + chr(34) + 'transport_failure' + chr(34), 'repair_schema_failure', 'abandon', 'terminate('); missing=[(m, a) for m in mods for a in arms if a not in pathlib.Path(m).read_text()]; assert not missing, missing; r=pathlib.Path('src/deepreason/referee.py').read_text(); assert 'if isinstance(error, EndpointError):' in r and 'if isinstance(error, SchemaRepairError):' in r, 'referee isinstance dispatch'"`
5. **Never widen `retry_max` under an authorization to "save a round trip".**
   The clamp is what makes provider calls countable against the manifest grant;
   an internal repair produces a provider request with no work item, and
   `len(work) == len(calls)` is the invariant the ceiling test asserts.

What breaks first, in the order you will see it:
`"dispatch differs from its authorization bundle"` (the adapter refused before
sending); then `"transactional reservation bound differs from rendered
request"` — **NOT "the prompt changed after issue", which it cannot be**: that
check runs first and would have raised the previous message, so this one means
a live `Reservation` disagrees with its own recorded `TokenReservationV2`, and
its diagnostic blob names both sides; then, on reopen,
`"provider result differs from issued authority"` from `replay.py`; and finally
`verify_root`'s `workflow-replay` failure, which re-derives the process state
twice and compares digests — the expensive one, because by then the root is
committed (see `DR-SUB-verification`).

The tests that catch you, cheapest first:
`tests/test_adapter_workflow_authorization_c2.py` and
`tests/test_v6_global_dispatch_guard.py` (the guard, sub-second),
`tests/test_v6_profile_authority.py` (presentation authority),
`tests/test_v6_contract_schema_repair_runtime.py` and
`tests/test_v6_live_repair_transactions.py` (one bundle, one call),
`tests/test_v6_controller3_replay_verification.py` (replay pairing),
`tests/test_v6_nonconjecture_recovery.py` (mid-flight recovery), then
`tests/test_v6_bridge_transactions.py` (minutes; the full wrapper).
`check: python -c "import pathlib; tests=('tests/test_adapter_workflow_authorization_c2.py','tests/test_v6_global_dispatch_guard.py','tests/test_v6_profile_authority.py','tests/test_v6_contract_schema_repair_runtime.py','tests/test_v6_live_repair_transactions.py','tests/test_v6_controller3_replay_verification.py','tests/test_v6_nonconjecture_recovery.py','tests/test_v6_bridge_transactions.py'); gone=[t for t in tests if not pathlib.Path(t).is_file()]; assert not gone, gone; assert 'fail(' + chr(34) + 'workflow-replay' + chr(34) in pathlib.Path('src/deepreason/invariants.py').read_text(), 'verify_root check name'"`

## Traps

- **The repair `mode` vocabulary is ONE type, imported — writing it twice
  killed a run at cycle 2. FIXED (repair-vocabulary tranche, 2026-08-28).**
  `workflow/repair_transaction.py` is the only writer of a
  `repair.semantic-task.v1` payload's `mode`, and it copies
  `V6RepairTurn.mode` verbatim. That field's `Literal` is therefore the
  vocabulary, and the authority that reads it back
  (`workflow/nonconjecture_recovery.py::_repair_authority`) had a SECOND,
  hand-typed set: `{"patch", "full"}`. They intersected in `patch` alone.
  `full` was emitted nowhere in `src/`; `whole_object_syntax` — what the
  session emits whenever a response cannot be parsed at all, so no baseline
  exists to patch — was accepted nowhere. Technique
  run-456885c569c0f4f7 lost epoch 5 at cycle 2 to
  `NonConjectureRecoveryAuthorityError("repair mode is invalid")`, and it was
  not stochastic: 36 of the 56 repair payloads across three committed roots
  carry the rejected value. The vocabulary now lives once in `llm/repair.py`
  (`V6RepairMode`, with `V6_REPAIR_TASK_MODES` DERIVED by `get_args(...)`
  minus the non-repair `initial`, and `V6_WHOLE_OBJECT_REPAIR_MODES` for the
  modes whose response IS the replacement object), and the reader imports
  both. Adding a mode to the `Literal` now reaches the authority; adding one
  to the authority alone is impossible, because there is no set there to add
  to. Census: `experiments/2026-08-28-audit-run-problems/probes/
  q5_repair_payloads.json`; the tranche is
  `experiments/2026-08-28-defect-repair-vocabulary/`.
`check: python -c "import inspect; from typing import get_args, get_type_hints; from deepreason.llm.repair import V6RepairTurn, V6_REPAIR_TASK_MODES, V6_WHOLE_OBJECT_REPAIR_MODES; from deepreason.workflow import nonconjecture_recovery as N; assert set(get_args(get_type_hints(V6RepairTurn)['mode'])) == V6_REPAIR_TASK_MODES | {'initial'}; assert V6_REPAIR_TASK_MODES == {'whole_object_syntax', 'patch'}; src=inspect.getsource(N._repair_authority); assert 'V6_REPAIR_TASK_MODES' in src and 'V6_WHOLE_OBJECT_REPAIR_MODES' in src; q=chr(34); assert q+'full'+q not in inspect.getsource(N)" && grep -q '"mode": turn.mode,' src/deepreason/workflow/repair_transaction.py && python -m pytest tests/test_v6_repair_mode_vocabulary.py -q`

- **The two record types spell "no raw blob" differently, and only one reader
  translated.** `LLMCall.raw_ref` is a plain `str` whose absence is `""`;
  `ProviderAttemptV1.raw_ref` is `str | None` whose absence is `None`.
  `record_provider_attempt` bridges them with `call.raw_ref or None`, and
  `replay.py`'s copy of the six pairing agreements re-applies the same
  translation — but `verify_root`'s copy compared the two raw. Because the
  writer ALWAYS applies `or None`, that comparison was unsatisfiable for the
  whole `outcome="transport_failure"` class: any dispatch that reached the
  provider and got no body made a run fail its own verifier while terminating
  cleanly. Reproduced offline by
  `python -u scripts/cycle_soak.py --case epoch3 --induce-repairs 2` (violation
  at seq=31; the same shape at seq=24 in the soak tranche's own two recorded
  runs), parked as P1 in
  `experiments/2026-08-23-change-cycle-soak-instrument/PARKED.md`, fixed by
  `experiments/2026-08-25-defect-workflow-call-pairing/`. No committed root
  witnessed it: 0 of 459 committed provider attempts across 14 roots are
  `transport_failure`. The general lesson outlives this fix — when two record
  types encode the same absence differently, a translation applied at the
  writer is owed to EVERY reader of the same agreement, and the copy that
  forgets it fails closed on a shape the writer cannot help producing.
`check: python -c "import re, pathlib; inv=pathlib.Path('src/deepreason/invariants.py').read_text(); rep=pathlib.Path('src/deepreason/workflow/replay.py').read_text(); svc=pathlib.Path('src/deepreason/workflow/transaction_service.py').read_text(); assert 'attempt.raw_ref == (call.raw_ref or None)' in inv, 'verifier lost the translation'; assert 'attempt.raw_ref != (call.raw_ref or None)' in rep, 'replay lost the translation'; assert 'raw_ref=call.raw_ref or None,' in svc, 'writer lost the translation'" && python -m pytest tests/test_v6_transport_failure_pairing.py -q`


- **The reservation bound is ONE number, and the adapter must not compute a
  second one.** Until 2026-08-23 `preview_request` returned a route's CEILING
  for any route declaring `context_window_tokens`, while `call` recomputed the
  cap from the endpoint's currently SETTLED value. Both are lawful readings —
  `EndpointLease.verify` binds `max_tokens` as a ceiling precisely so a
  controller may settle below it (`ERRATA` E43) — so the two agreed until a
  controller moved, and then parted by exactly the amount of the narrowing.
  Epoch-3 attempt 3 (run
  `bb0455384ea09b5b72664a4f6f3f0cb7a5ac227c00a93976e5c8c31873ca84f4`) died at
  cycle 2 of 4 with 290 025 of 400 000 tokens unspent and `verify_root` clean:
  the cycle-2 policy settled `cap:conjecturer` to 20480 against a 32768
  ceiling, and the next dispatch compared a booked `8333 + 32768 = 41101`
  against a recomputed `8333 + 20480 = 28813`. Fixed by
  `experiments/2026-08-23-fix-reservation-bound-authority/`: the cap is defined
  once in `_completion_cap`, returned by `preview_request`, booked by the
  workflow, and CONSUMED at dispatch off `reservation_record`.
  Two things this trap teaches beyond its own fix. First, **the prompt was
  never a candidate** — `verify_dispatch` pins the rendered bytes to the bundle
  digest before the guard runs, so the two prompt bounds are equal by
  construction; the error message and this document both said "the rendered
  request" for months and both were wrong (`ERRATA` E46). Second, **the
  eliminations in a parked finding are evidence, not axioms**: P6-epoch3 ruled
  out a controller re-tune by scanning `log.jsonl` for `max_tokens`, but the
  policy lives under `objects/artifact/` with `provenance.role: "controller"`
  and spells the value `"cap:conjecturer": 20480` inside an `inline:` JSON
  string, so the scan could not have found it (`ERRATA` E47).
`check: python -c "import inspect, re; from deepreason.llm.adapter import LLMAdapter; call=inspect.getsource(LLMAdapter.call); cap=re.search(r'transport_limits = \{\n\s+.max_tokens.: \((.*?)\),\n\s+.timeout_s.', call, re.S); assert cap, 'cap is not a consumed expression'; body=' '.join(cap.group(1).split()); assert 'reservation_record.completion_bound_tokens' in body and 'getattr(endpoint,' not in body, body; assert len(re.findall(r'def _completion_cap', inspect.getsource(LLMAdapter))) == 1" && grep -q "route.context_window_tokens is not None and route.max_tokens is not None" src/deepreason/llm/firewall.py && python -m pytest tests/test_v6_reservation_bound_authority.py -q`

- **A repair attempt's own `diagnostic_ref` is the diagnostic that came AFTER
  it.** `_terminalize_invalid` writes it as `trace_ref or next_diagnostic_ref`,
  so reading the authorized set from a repair attempt compares that attempt's
  response against the NEXT turn's authority. Every converging repair moves the
  pointer on, so every converging repair scores as off-target. That is how the
  first reading of reach-rich `run-40e713b30a147dfc` recorded two
  "sibling-index" patches that the record does not contain — its 13 repair
  turns were all on target. The authority a turn was dispatched under is its
  work preparation's `repair.semantic-task.v1` payload
  (`authorized_pointers`, `diagnostic_ref`, `baseline_sha256`), frozen before
  issue; join `provider_attempt.work_id -> preparation.id` to read it.
  Census: `experiments/2026-08-22-fix-repair-patch-transport/repair_turn_census.py`.
`check: grep -q "diagnostic_ref=trace_ref or next_diagnostic_ref," src/deepreason/workflow/repair_transaction.py && grep -q '"authorized_pointers": list(turn.authorized_pointers),' src/deepreason/workflow/repair_transaction.py && grep -q '"schema": "repair.semantic-task.v1",' src/deepreason/workflow/repair_transaction.py`
- **Preview/dispatch digest agreement proves identity, never correctness.**
  Both `preview_request` and `call` render through the same `_render_request`,
  so the bundle's `prompt_sha256` matches whatever that helper produces — even
  when what it produces is wrong. In live `run-646f41b8` seq 565 the v6
  post-allocation pack edits demoted the `AllocatedPack` marker to plain `str`,
  the profile's aggregate prefix clip re-applied to a pack `PackIR` had already
  budgeted section-by-section, and the sealed advisory context was cut mid-JSON
  — 86 percent of the context bytes never dispatched, with every pre-dispatch
  authority check passing. The fix is a CONTENT check inside `_render_request`,
  so preview and dispatch both see it, plus the `pack_is_allocated` guard. When
  you add a step between issue and dispatch, ask what its failure would look
  like to the digest; the answer is usually "nothing".
`check: python -c "import inspect, re; from deepreason.llm.adapter import LLMAdapter; b=inspect.getsource(LLMAdapter._render_request); assert re.search(r'pack_is_allocated = isinstance\(pack, AllocatedPack\)', b), 'marker'; assert re.search(r'if profile is not None and not pack_is_allocated:\n\s+rendered_pack = apply_model_profile\(rendered_pack, profile\)', b), 'clip'; assert re.search(r'if rendered_pack\.count\(protected\) != 1:\n\s+raise ValueError\(\n\s+.advisory context bytes are absent or duplicated before aliasing.', b), 'pre-alias'; assert re.search(r'if prompt\.count\(advisory_text\) != 1:\n\s+raise ValueError\(\n\s+.rendered provider request must contain the exact ', b), 'content'" && test "$(grep -c "self._render_request(" src/deepreason/llm/adapter.py)" -eq 2 && grep -q "class AllocatedPack(str):" src/deepreason/llm/packs.py && python -m pytest tests/test_v6_context_continuation.py::test_wide_allocated_pack_dispatches_advisory_context_intact tests/test_v6_conjecture_scratch_consumption.py::test_context_commit_failure_abandons_prepared_work_before_dispatch -q`
- **A budget denial arrives already terminalized.** `reserve_dispatch` appends
  the `budget_denied` terminal and then raises `WorkBudgetDenied`, so a caller
  whose `except BaseException: abandon(...)` sees it will write a second
  terminal after termination. The five transactional call sites therefore
  re-raise `WorkBudgetDenied` ahead of their broad handler (see the eight-handler
  check above for `conj.py`'s and the scheduler's different, deliberate shapes);
  `referee.py` carries the comment that says why. Two
  further markers travel on the exception, and they are INDEPENDENT — carrying
  one is not carrying the other. `error.transaction_terminalized = True` is
  written at fifteen sites across seven modules and read at exactly two, both in
  `scheduler.py`, where it selects `diagnostics.append` over `_drop` so a
  failure already durable as a `ProviderAttemptV1` is not re-recorded.
  `error.spend = None`, at twelve sites, separately stops the legacy `_drop`
  path counting tokens that attempt already carries. Adding a new exception
  path without both markers double-counts spend or double-terminates work.
`check: grep -q "any further transition would be a second" src/deepreason/referee.py && python -c "import re, pathlib, glob; files=sorted(f for f in glob.glob('src/deepreason/**/*.py', recursive=True) if 'transaction_terminalized' in pathlib.Path(f).read_text()); assert len(files) == 8, files; lines=[(f, l) for f in files for l in pathlib.Path(f).read_text().splitlines() if 'transaction_terminalized' in l]; writes=[x for x in lines if re.search(r'\.transaction_terminalized = ', x[1])]; reads=[x for x in lines if not re.search(r'\.transaction_terminalized = ', x[1])]; assert len(writes) == 15 and len({f for f, _ in writes}) == 7, (len(writes), sorted({f for f, _ in writes})); assert len(reads) == 2 and {f for f, _ in reads} == {'src/deepreason/scheduler/scheduler.py'}, reads; s=pathlib.Path('src/deepreason/scheduler/scheduler.py').read_text(); assert len(re.findall(r'if getattr\((?:error|e), .transaction_terminalized., False\):\n\s+self\.diagnostics\.append\([^\n]*\n\s+else:\n\s+self\._drop\(', s)) == 2, 'scheduler arms'" && test "$(grep -rn "\.spend = None" --include=*.py src/deepreason | wc -l)" -eq 12`
- **`WorkflowAuthorizationError` is defined in `llm/adapter.py`, and both sides
  raise it.** `workflow/trace.py` imports it to signal that its own persistence
  failed; the adapter raises it to refuse an unauthorized dispatch. An
  `except WorkflowAuthorizationError` therefore catches two very different
  events — "the control plane could not record" and "the provider boundary
  refused" — and only the message distinguishes them. Do not move the class to
  `workflow/` to tidy the layering: `llm/` has no module-scope import of
  `workflow/`, and the type must be raisable from inside `call`.
`check: python -c "import re, pathlib; A=pathlib.Path('src/deepreason/llm/adapter.py').read_text(); T=pathlib.Path('src/deepreason/workflow/trace.py').read_text(); assert re.search(r'^class WorkflowAuthorizationError\(RuntimeError\):', A, re.M), 'defined in llm'; assert len(re.findall(r'raise WorkflowAuthorizationError\(', A)) >= 8, 'adapter raises it'; assert re.search(r'^from deepreason\.llm\.adapter import WorkflowAuthorizationError$', T, re.M), 'trace imports it'; assert re.search(r'if isinstance\(error, WorkflowAuthorizationError\):\n\s+raise error\n\s+raise WorkflowAuthorizationError\(\n\s+.active conjecture transition was not durably authorized.\n\s+\) from error', T), 'trace raises it'; assert re.search(r'def require_authority\(self\) -> None:\n(?:[^\n]*\n)*?\s+self\.authoritative = True\n\s+if self\.failed:\n\s+self\._report\(', T), 'require_authority fails closed'"`
- **A test fixture that pins `retry_max=0` on the adapter hides the clamp.**
  The v6 conjecture fixtures build `LLMAdapter(..., retry_max=0,
  transaction_authority_required=True)`, so deleting
  `retry_max=(0 if dispatch_authorization is not None else self.retry_max)`
  leaves the whole repair suite green. **Residue: the clamp is held only by the
  structural check above and by the `attempt != 0` guard inside the loop, not by
  any behavioural test with a non-zero adapter `retry_max`.** Under mutation the
  asymmetry is stark: deleting the clamp breaks nothing, while corrupting
  `prompt_sha256` or turning the meter `elif` into an `if` breaks
  `test_manifest_grant_is_the_exact_provider_call_ceiling` immediately. The
  generalisation is the one worth keeping — a fixture that pins the same value
  the production code computes tests the fixture, not the code.
`check: python -c "import re, pathlib; q=chr(34); assert re.search(r'if attempt != 0:\n\s+raise WorkflowAuthorizationError\(\n\s+' + re.escape(q + 'transactional repair requires a new authorization bundle' + q) + ',', pathlib.Path('src/deepreason/llm/adapter.py').read_text()), 'clamp guard'; n=len(re.findall(r'LLMAdapter\((?:[^\n]*\n)*?\s+retry_max=0,\n(?:[^\n]*\n)*?\s+transaction_authority_required=True,', pathlib.Path('tests/test_v6_live_repair_transactions.py').read_text())); assert n == 5, n"`
