<!-- DR-SEAM-bridge-x-llm -->
Verified-at: 08dcdf3c
Verify: python tools/docs_verify.py
Owns: src/deepreason/bridge/transactional_adapter.py, src/deepreason/bridge/harness.py, src/deepreason/bridge/ledger.py, src/deepreason/bridge/compose.py, src/deepreason/llm/roles.py, src/deepreason/llm/repair.py
Sides: DR-SUB-bridge, DR-SUB-llm

# bridge x llm

## The agreement

`llm/` sells one bounded `pack -> schema-valid JSON` call on a frozen route and
knows nothing about grounding; `bridge/` buys exactly that and owns every
epistemic consequence of the answer. Neither side names the other as a type.
Per call the bridge hands over four things — a configured role, a
`template_role`, a rendered pack, and a `WireContract` subclass it built for
this one catalog — and gets back a compiled canonical model plus an `LLMCall`;
the adapter supplies the prompt, the transport, the meter and the finite repair
protocol, and refuses any field the model should not be naming. Under
RunManifest v6 `TransactionalBridgeAdapter` decorates the ordinary adapter so
each of those calls becomes one complete workflow transaction — preparation,
context plan, atomic issue, provider attempt, semantic admission, terminal —
and so a restart revalidates the stored result instead of dispatching again.
What the wrapper ADDS is authority and accounting. What it may not add is
latitude: the route lease, the presentation profile, the wire contract and the
model-control firewall stay the llm side's, re-derived and re-checked at the
boundary rather than restated inside the bridge. The transaction half of that
contract — bundles, reservations, replay pairing — is `DR-SEAM-llm-x-workflow`
and is not repeated here.

Eleven modules name both packages. Six bridge modules import `deepreason.llm`;
only two of those — `transactional_adapter.py` and `harness.py` — carry runtime
authority, and `llm/` imports nothing from `bridge/` at all.
`check: test "$(for f in $(grep -rl "deepreason\.llm" --include=*.py src/deepreason); do grep -ql "deepreason\.bridge" "$f" && echo x; done | wc -l)" -ge 11 && test "$(grep -rl "from deepreason\.llm" --include=*.py src/deepreason/bridge/ | wc -l)" -eq 6 && ! grep -rq "deepreason\.bridge" --include=*.py src/deepreason/llm/ && test "$(grep -rl "dispatch_authorization\|InquiryTransactionService" --include=*.py src/deepreason/bridge/ | wc -l)" -eq 2 && for t in bridge_ledger bridge_compose bridge_review bridge_grounding_repair; do grep -q "\"$t\":" src/deepreason/llm/roles.py || exit 1; done && grep -q "BRIDGE_WIRE_REFERENCE_INVALID" src/deepreason/llm/repair.py`

## Where it is expressed

| Site | File | Symbol | What it enforces |
|---|---|---|---|
| Role roster | `llm/roles.py` | `TEMPLATES` / `COMPACT_TEMPLATES` `bridge_*` entries | the four bridge stages are `template_role`s over configured seats, never §9 generator roles |
| Task roster | `bridge/transactional_adapter.py` | `_TEMPLATE_TASKS`, `_EXACT_V6_CONTRACTS` | only those four roles may be called, and ledger/compose only under the frozen v3/v2 (or batch) contract ids |
| Call-surface narrowing | `bridge/transactional_adapter.py` | `call(..., **authority)` → "bridge transaction authority is adapter-owned" | a bridge stage may not name any dispatch authority; the wrapper owns it |
| Presentation identity | `bridge/transactional_adapter.py` | `__init__` equality on `adapter.base_model_profile` and `adapter.leases` | the handed-in adapter must already be the manifest's adapter |
| Lease resolution | `bridge/transactional_adapter.py` | `select_lease(self._adapter.leases, role, endpoint_index)` → `route_fingerprint` → `RouteLeaseRefV1` | one lease resolved once, then passed as `endpoint_lease=` so the adapter cannot re-resolve |
| Preview freeze | `bridge/transactional_adapter.py` | `preview_request(...)` then "bridge preview changed frozen call authority" | contract identity and lease are checked between issue and dispatch |
| Profile authority | `bridge/transactional_adapter.py` | `resolve_route_seat_base_profile` + `V6ModelProfileOverrideForbidden` | the seat's manifest base profile, per stage; a supplied profile may only equal it |
| Contract authoring | `bridge/ledger.py`, `bridge/compose.py`, `bridge/review.py`, `bridge/repair.py` | `ClaimLedgerWireContractV3`, `BridgeCompositionWireContractV2`, `DirectWireContract(...)`, `GroundingRepairWireContractV1` | the bridge builds its own call-local `WireContract`; `wire_contract_for` never routes a bridge role |
| First refusal | `bridge/ledger.py` | `ClaimLedgerWireContractV2.validate_value` → `self._preflight_value(value)` | the shared control-field/unknown-field firewall runs before kind-aware reference checks |
| Diagnostic protocol | `bridge/ledger.py`, `bridge/compose.py`, `llm/repair.py` | `.code = "BRIDGE_WIRE_REFERENCE_INVALID"` / `"BRIDGE_COMPOSITION_INVALID"`; `diagnostic_from_error` | bridge-shaped repair guidance (legal handles, authorized pointer, instruction) with no import either way |
| Pack allocation | `bridge/ledger.py`, `llm/adapter.py` | `AllocatedPack(pack)`; `pack_is_allocated` guard in `_render_request` | the Stage A catalog pack is pre-budgeted and must not be prefix-clipped by the profile |
| Route fence | `bridge/harness.py`, `bridge/state.py` | `BridgeWorkflowAttemptFenceV1` vs `event.llm.attempt_trace` | a whole-workflow retry may not change contract, seat, endpoint or route digest |
| Retry route liveness | `bridge/harness.py` | `_assert_adapter_matches_retry_lease` → `BRIDGE_WORKFLOW_RETRY_ROUTE_CHANGED` | the live adapter's endpoint object still matches the manifest lease it was compiled from |
| Call persistence | `bridge/harness.py` | `_HarnessBridgeSink.persist_bridge_batch` | an authorized dispatch's `LLMCall` rides its provider result only; the semantic bridge event carries the work id instead |
| Spend carrier | `bridge/workflow.py` | `_error_calls`, `BridgeWorkflowResultV1._terminal_shape` | every `.spend` the adapter hangs on a raised error reaches the result, and `token_count` must equal the retained receipts |
| Recovery revalidation | `bridge/transactional_adapter.py` | `_recover_output` → `reject_model_control_fields` + `wire_contract.compile(validate_value(...))` | a replayed provider result passes the same firewall the live call applied |

The four bridge template roles exist on both the standard and compact prompt
tables, are absent from the §9 generator roster, and the wrapper's task map
covers exactly them.
`check: python -c "from deepreason.bridge.transactional_adapter import _TEMPLATE_TASKS, _EXACT_V6_CONTRACTS; from deepreason.llm.roles import TEMPLATES, COMPACT_TEMPLATES, ROLES; b={n for n in TEMPLATES if n.startswith('bridge_')}; assert set(_TEMPLATE_TASKS)==b=={n for n in COMPACT_TEMPLATES if n.startswith('bridge_')}; assert not b & set(ROLES); assert _EXACT_V6_CONTRACTS=={'bridge_ledger':{'bridge.ledger.v3','bridge.ledger-batch.v1'},'bridge_compose':{'bridge.composition.v2','bridge.composition-batch.v1'}}"`

A bridge stage passes a role, a pack, an output model, a `template_role` and a
`wire_contract` — and nothing else. Every remaining `LLMAdapter.call` parameter
is either supplied by the wrapper or never supplied at all, and the wrapper
turns any leftover keyword into a `ValueError` rather than forwarding it.
`check: ! grep -qE "model_profile|school_id|output_mechanism|endpoint_lease|images=|dispatch_authorization" src/deepreason/bridge/ledger.py src/deepreason/bridge/compose.py src/deepreason/bridge/review.py src/deepreason/bridge/repair.py src/deepreason/bridge/workflow.py && python -c "import inspect; from deepreason.llm.adapter import LLMAdapter; from deepreason.bridge.transactional_adapter import TransactionalBridgeAdapter as T; p=set(inspect.signature(LLMAdapter.call).parameters); w=inspect.signature(T.call).parameters; assert {'model_profile','school_id','output_mechanism','endpoint_lease','images','dispatch_authorization'} <= p; assert 'dispatch_authorization' not in w and w['authority'].kind is inspect.Parameter.VAR_KEYWORD" && grep -q "bridge transaction authority is adapter-owned" src/deepreason/bridge/transactional_adapter.py && grep -q "^class V6ModelProfileOverrideForbidden" src/deepreason/llm/adapter.py && test "$(grep -c "raise V6ModelProfileOverrideForbidden(" src/deepreason/bridge/transactional_adapter.py)" -eq 2`

Route identity is resolved once from the wrapped adapter's frozen leases,
handed back to the adapter as `endpoint_lease=` on all four dispatch and
preview paths, and re-asserted on replay against the `LLMAttempt` fields the
adapter stamped.
`check: grep -q "lease = endpoint_lease or select_lease(self._adapter.leases, role, endpoint_index)" src/deepreason/bridge/transactional_adapter.py && grep -q "adapter route leases differ from the manifest" src/deepreason/bridge/transactional_adapter.py && grep -q "adapter presentation identity differs from the manifest" src/deepreason/bridge/transactional_adapter.py && test "$(grep -c "endpoint_lease=lease," src/deepreason/bridge/transactional_adapter.py)" -eq 4 && grep -q "raise ValueError(\"bridge preview changed frozen call authority\")" src/deepreason/bridge/transactional_adapter.py && grep -q "route_sha256=route_fingerprint(retry_route)," src/deepreason/bridge/harness.py && grep -q "attempt.route_sha256 != fence.route_sha256" src/deepreason/bridge/state.py && python -c "from deepreason.ontology.event import LLMAttempt; from deepreason.bridge.retry import BridgeWorkflowAttemptFenceV1 as F; f={'contract_id','endpoint_id','route_sha256','seat'}; assert f <= set(LLMAttempt.model_fields); assert f | {'role'} <= set(F.model_fields)"`

One bridge model call is one whole transaction, and its terminal's usage comes
from the `LLMCall` the adapter returned rather than from a second count.
`check: python -c "import inspect; from deepreason.bridge.transactional_adapter import TransactionalBridgeAdapter as T; s=inspect.getsource(T.call); missing=[x for x in ('service.prepare(','service.context_plan(','service.issue(','service.record_provider_attempt(','service.record_semantic_admission(','service.terminate(','dispatch_authorization=authorized','prompt_tokens=llm_call.prompt_tokens','completion_tokens=llm_call.completion_tokens') if x not in s]; assert not missing, missing" && python -m pytest tests/test_v6_bridge_transactions.py::test_every_v6_bridge_call_has_an_independent_complete_transaction -q`

Every model-facing bridge contract refuses a routing field before its own
rules run, whether it inherits `WireContract.validate_value` or overrides it.
Losing first refusal does not open the field — Pydantic still rejects it — but
it downgrades a typed `MODEL_CONTROL_FIELD_FORBIDDEN` diagnostic into a generic
extra-field one, which is the difference between a repair turn that is told
what it did and one that is told a schema path.
`check: python -c "import unittest; from deepreason.bridge.ledger import ClaimLedgerCatalogItemV1 as I, ClaimLedgerInputCatalogV3 as C, ClaimLedgerWireContractV3 as L; from deepreason.bridge.review import GroundingVerdictWireV1 as V; from deepreason.bridge.repair import GroundingRepairWireV1 as R; from deepreason.llm.wire import DirectWireContract as D; from deepreason.llm.firewall import ModelControlFieldError as E; cat=C.create(problem_ref='p', formal_seq=8, problem_text='q', output_target='t', items=[I(handle='B1', kind='source', ref='sha256:'+'a'*64, excerpt='e')]); t=unittest.TestCase(); [t.assertRaises(E, c.validate_value, {'endpoint_id': 'x'}) for c in (L(cat), D(V), D(R))]"`

The two bridge error codes are translated into repair guidance by `llm/repair.py`
with no import in either direction: the bridge sets `.code`, `.repair_scope`,
`.legal_handles`, `.instruction` and `.allowed_detail` as plain attributes, and
`diagnostic_from_error` reads them off by name.
`check: python -c "from deepreason.bridge.ledger import ClaimLedgerWireReferenceError as R; from deepreason.bridge.compose import CompositionContractError as C; from deepreason.llm.repair import diagnostic_from_error as D; s={'type':'object','properties':{}}; a=D('bridge.ledger.v3', R('b','/e/0', legal_handles=('B1','B2'), repair_scope='/e'), s); b=D('bridge.composition.v2', C(pointer='/s/0/text', message='b', authorized_pointers=('/s/0/text',), instruction='i', allowed_detail='d'), s); assert a.error=='BRIDGE_WIRE_REFERENCE_INVALID' and \"['B1', 'B2']\" in a.allowed and a.repair_scope=='/e'; assert b.repair_scope=='/s/0/text' and b.instruction=='i' and b.allowed.startswith('d;')"`

Spend crosses in one direction only: the adapter hangs an `LLMCall` on a raised
error's `.spend`, the bridge collects it, and the workflow result is
unconstructible if its token total disagrees with the receipts it retained. The
sink drops the call from the semantic bridge event when the dispatch was
authorized, because the provider result already owns that receipt.
`check: python -c "import inspect, unittest, pydantic; from deepreason.bridge.workflow import BridgeWorkflowResultV1 as B, _error_calls; from deepreason.ontology.event import LLMCall; from deepreason.llm.repair import SchemaRepairError as S; assert 'spend' in inspect.signature(S.__init__).parameters; c=LLMCall(role='r', model='m', endpoint='e', prompt_ref='sha256:'+'a'*64, raw_ref='sha256:'+'b'*64, tokens=7, ms=1, attempts=1); e=RuntimeError('x'); e.spend=c; assert _error_calls(e)==[c]; k=dict(process_status='failure', phase='p', formal_seq=1, error_code='X', error_message='m', model_call_count=1, model_calls=[c]); B(token_count=7, **k); unittest.TestCase().assertRaises(pydantic.ValidationError, B, token_count=6, **k)" && grep -q "if getattr(persisted_llm, \"dispatch_authorization_ref\", None) is not None:" src/deepreason/bridge/harness.py && python -m pytest tests/test_v6_bridge_transactions.py::test_bridge_sink_does_not_append_transactional_call_twice -q`

A restart revalidates rather than re-dispatches: `_recover_output` renders
through `preview_request`, never `call`, and re-applies the control-field
firewall and the contract compiler to the stored raw bytes.
`check: python -c "import inspect; from deepreason.bridge.transactional_adapter import TransactionalBridgeAdapter as T; s=inspect.getsource(T._recover_output); assert 'preview_request(' in s and '_adapter.call(' not in s; assert 'reject_model_control_fields(raw_value)' in s and 'wire_contract.compile(wire_contract.validate_value(raw_value))' in s" && python -m pytest tests/test_v6_bridge_transactions.py::test_v6_bridge_restart_corrupt_saved_result_fails_closed_without_redispatch -q`

## What is deliberately absent

**The bridge owns no provider machinery and no adapter type.** Nothing under
`bridge/` calls `build_adapter`, names an endpoint class, or calls `.complete(`;
`LLMAdapter` appears only in two docstrings, never as an import, an annotation
or an `isinstance`. The adapter is always HANDED in — by `application/bridge.py`
for a service build, by a fixture otherwise — and the bridge discovers what kind
of adapter it got by attribute probe (`staged_ledger_fallback`,
`consume_staged_calls`, `finalize_staged_effect`, `bind_bridge_execution`,
`assert_recovery_complete`), all of which exist only on the wrapper. That is
what lets one `BridgeWorkflow` run against a pre-v6 adapter and a v6 wrapper
without a version branch, and why "tidying" the probes into an isinstance check
breaks every legacy fixture.
`check: ! grep -rqE "build_adapter|OpenAICompatEndpoint|MockEndpoint|request_with_retries|\.complete\(" --include=*.py src/deepreason/bridge/ && ! grep -rqE "^\s*(from|import) .*LLMAdapter|isinstance\([^)]*LLMAdapter|: *LLMAdapter\b" --include=*.py src/deepreason/bridge/ && grep -q "^    def call(" src/deepreason/llm/adapter.py && grep -q "from deepreason.llm.adapter import build_adapter" src/deepreason/application/bridge.py && python -c "from deepreason.bridge.transactional_adapter import TransactionalBridgeAdapter as T; from deepreason.llm.adapter import LLMAdapter as A; n=('staged_ledger_fallback','staged_composition_fallback','consume_staged_calls','finalize_staged_effect','bind_bridge_execution','assert_recovery_complete'); assert all(hasattr(T, x) for x in n), n; assert not any(hasattr(A, x) for x in n), n"`

**No bridge model call is school-routed, carries advisory conjecture context, or
sends images.** The wrapper's signature accepts `school_id`, `conjecture_context`
and `images` purely so it can mirror `LLMAdapter.call`; not one of the four
stage modules ever supplies them. The consequence is typed and load-bearing: no
`SchoolRouteReceiptV1` and no `ConjectureContextCallReceiptV1` can appear on a
bridge `LLMCall`, so a reader of the log can tell bridge traffic from reasoning
traffic by receipt shape alone. Adding a school to a bridge seat would make the
final answer's provenance a stance rather than the record.
`check: ! grep -qE "school_id|conjecture_context|images=" src/deepreason/bridge/ledger.py src/deepreason/bridge/compose.py src/deepreason/bridge/review.py src/deepreason/bridge/repair.py src/deepreason/bridge/workflow.py && grep -q "school_id=school_id," src/deepreason/bridge/transactional_adapter.py && grep -q "SchoolRouteReceiptV1(" src/deepreason/llm/adapter.py && grep -q "ConjectureContextCallReceiptV1" src/deepreason/llm/adapter.py`

**A schema repair of a bridge call is not bridge work.** When
`LLMAdapter.call` raises `SchemaRepairError`, the wrapper hands the INNER
adapter to `InquiryTransactionService.repair_schema_failure`, which prepares its
own work item with `task_payload_value["schema"] == "repair.semantic-task.v1"`.
The bridge's recovery selector `_execution_items` admits only
`bridge.transaction-task.v2` and `contract-decomposition-child.v1` payloads, so
repair work is invisible to bridge replay and consumes no bridge ordinal.
`WorkflowTaskKind.REPAIR` cannot be used to tell them apart — the grounding-repair
STAGE is also that kind — so the payload schema is the only discriminator. Widening
the selector to a task-kind test would make a restart try to replay a repair as
a bridge stage.
`check: python -c "import inspect; from deepreason.bridge.transactional_adapter import TransactionalBridgeAdapter as T, _TEMPLATE_TASKS; from deepreason.workflow.models import WorkflowTaskKind as K; s=inspect.getsource(T._execution_items); assert '_BRIDGE_TRANSACTION_SCHEMA_V2' in s and 'contract-decomposition-child.v1' in s and 'repair' not in s; assert _TEMPLATE_TASKS['bridge_grounding_repair'] is K.REPAIR" && grep -q "\"schema\": \"repair.semantic-task.v1\"" src/deepreason/workflow/repair_transaction.py && grep -q "task_kind=WorkflowTaskKind.REPAIR," src/deepreason/workflow/repair_transaction.py && grep -q "adapter=self._adapter," src/deepreason/bridge/transactional_adapter.py`

**Only the Stage A ledger pack escapes profile clipping.** `AllocatedPack`
appears in exactly one bridge module. The composition, review and repair packs
are plain strings and ARE clipped by `apply_model_profile`; the catalog pack is
not, because prefix-clipping a closed reference catalog leaves the schema
advertising aliases whose kind and excerpt rows the model never saw. Marking the
other three would suppress a budget the profile is supposed to apply; unmarking
this one reintroduces unanswerable handle errors.
`check: python -c "from deepreason.llm.packs import AllocatedPack as A; from deepreason.bridge.ledger import ClaimLedgerCatalogItemV1 as I, ClaimLedgerInputCatalogV3 as C, ClaimLedgerWireContractV3 as L, render_claim_ledger_stage_a_pack as P; cat=C.create(problem_ref='p', formal_seq=8, problem_text='q', output_target='t', items=[I(handle='B1', kind='source', ref='sha256:'+'a'*64, excerpt='e')]); assert isinstance(P(cat, contract=L(cat)), A)" && ! grep -q "AllocatedPack" src/deepreason/bridge/compose.py src/deepreason/bridge/review.py src/deepreason/bridge/repair.py && grep -q "pack_is_allocated = isinstance(pack, AllocatedPack)" src/deepreason/llm/adapter.py && grep -q "if profile is not None and not pack_is_allocated:" src/deepreason/llm/adapter.py`

**There is no import from `llm/` to `bridge/`, and the two protocols that cross
that gap are strings.** `llm/roles.py` holds four bridge prompt templates and
`llm/repair.py` branches on two bridge error codes, both by literal — checked in
"The agreement" above. This is not an oversight waiting for a shared types
module: `llm/` must remain loadable without the bridge, and any type it imported
from `bridge/` would put the epistemic vocabulary inside the transport layer,
which is the boundary `DR-SUB-llm` exists to keep.

**Under an authorization the adapter's own meter gate, repair loop, compact
recovery and profile choice are all inert.** That absence belongs to
`DR-SEAM-llm-x-workflow` and is checked there; do not re-derive it here. The
bridge-visible consequence is only this: `TransactionalBridgeAdapter` sets
`transaction_authority_required = True` at construction, so from that moment the
wrapped adapter cannot be dispatched by anyone else without a bundle either.

## How to change it

Order is forced by which side is frozen and by what a stopped root already
records.

1. **Read `DR-INV-frozen-surfaces` first.** The bridge contract ids and their
   schema-repair grants are compiled into the manifest by
   `_compile_contract_schema_repair_policy`, so touching a contract id — even by
   renaming a wire model class — moves every qualification subject digest and
   costs a full requalification. See `DR-SEAM-bridge-x-manifest` for that half.
2. **Change the contract before the prompt.** A new field or rule goes into the
   bridge's own `WireContract` subclass and its canonical model together (see
   `DR-SUB-bridge`'s "where to change what"); only then does the matching
   sentence go into `llm/roles.py`, and only if the schema genuinely cannot
   carry it. A rule stated in `TEMPLATES` that the schema does not enforce is a
   rule the repair kernel cannot diagnose.
3. **If the failure needs its own repair guidance, add the error code on the
   bridge side and the branch in `diagnostic_from_error` in the same commit.**
   An error carrying `.code`, `.repair_scope` and `.legal_handles` that
   `llm/repair.py` does not recognise degrades silently to the generic
   diagnostic; nothing fails, the model is simply told less.
4. **Add a new bridge model call in three places or none:** `_TEMPLATE_TASKS`
   (which task kind it becomes), `TEMPLATES` + `COMPACT_TEMPLATES` (both, or a
   compact route has no prompt at all), and — if it must be pinned —
   `_EXACT_V6_CONTRACTS`. Missing the compact table is the failure that only
   shows up on a route whose profile selected compact transport.
5. **Move the recovery path with the dispatch path.** Anything the live call
   derives from the manifest (task kind, contract id, route lease, input refs,
   formal fence) is re-derived by `_recover_output` and compared field by field;
   a new field in the task payload that the recovery comparison does not know
   about makes every restart raise `BRIDGE_RECOVERY_AUTHORITY_MISMATCH`.
6. **Never let a bridge stage pass dispatch authority.** The wrapper's
   `**authority` catch-all exists so that a stage which "helpfully" forwards a
   bundle fails at the boundary instead of producing a second request under one
   authorization.

What breaks first, in the order you will see it:
`"unrecognized canonical bridge model call"` or
`"<role> requires one frozen contract from [...]"` (the wrapper refused before
preparing anything); then `"bridge preview changed frozen call authority"` (the
contract or lease moved between issue and dispatch); then
`"dispatch differs from its authorization bundle"` from the adapter; then, on
reopen, `BRIDGE_RECOVERY_AUTHORITY_MISMATCH`; and finally `verify_root`'s
`bridge-replay` failure, which replays the log twice and compares the advisory
bridge state — the expensive one, because the root is already committed.

The tests that catch you, cheapest first:
`tests/test_bridge_stage_a.py` and `tests/test_bridge_ledger.py` (contract and
handle rules, seconds), `tests/test_bridge_diagnostic_matrix.py` (the eight
directed conditions, offline), `tests/test_v6_bridge_transactions.py`
(the wrapper end to end; minutes), then
`tests/test_v6_bridge_staged_execution.py` (the decomposition fallback).

## Traps

- **`__getattr__` forwards reads, not writes — which is why `meter` is an
  explicit property.** `TransactionalBridgeAdapter` delegates unknown attributes
  to the wrapped adapter, so `wrapper.retry_max` and `wrapper.leases` read
  through. Assignment does not: `wrapper.meter = TokenMeter(budget)` would land
  on the wrapper while `LLMAdapter.call` kept reading the inner one.
  `application/bridge.py` performs exactly that assignment on an
  already-wrapped adapter to apply the operator's `--token-budget`, so without
  the property pair the ceiling would be set on an object nobody consults and
  the run would be silently unbounded. Any other mutable adapter field a caller
  sets after wrapping needs the same treatment.
`check: python -c "from deepreason.bridge.transactional_adapter import TransactionalBridgeAdapter as T; assert isinstance(T.meter, property) and T.meter.fset is not None; w=T.__new__(T); w._adapter=type('A', (), {'meter': None})(); w.meter='X'; assert w._adapter.meter=='X' and w.meter=='X'; w._adapter.retry_max=99; assert w.retry_max==99" && grep -q "adapter.meter = TokenMeter(intent.token_budget)" src/deepreason/application/bridge.py`
- **`bridge_policy.max_schema_repair_attempts` reaches the provider by two
  routes, and under v6 only one of them is live.** It becomes the adapter's
  legacy `retry_max` (`application/bridge.py` even asserts the equality) AND it
  compiles into the manifest's per-contract grant. Under an authorization the
  adapter's own ceiling is clamped to zero, so the grant is what governs: the
  regression sets `retry_max=99` with a bridge policy of 0 and a contract grant
  of 1, and gets exactly one repair. Reading the policy number to predict how
  many provider calls a bridge stage may make is therefore wrong for every v6
  run; read `manifest.contract_schema_repair_policy` instead.
`check: grep -q "if adapter.retry_max != policy.max_schema_repair_attempts:" src/deepreason/application/bridge.py && grep -q "bridge_ceiling = min(2, max(0, bridge_policy.max_schema_repair_attempts))" src/deepreason/run_manifest.py && python -m pytest tests/test_v6_bridge_transactions.py::test_bridge_runtime_uses_contract_grant_not_bridge_policy_ceiling tests/test_v6_bridge_transactions.py::test_grounding_direct_contracts_use_their_canonical_zero_grants -q`
- **Two of the four bridge contract ids are derived from a class name, and one
  of them is a manifest key.** `DirectWireContract` builds
  `"<canonical model name lowercased>.direct.v1"`, so the review and grounding-repair
  contracts are `groundingverdictwirev1.direct.v1` and
  `groundingrepairwirev1.direct.v1` — and `run_manifest.py` computes its
  schema-repair grants by instantiating those same classes. Renaming
  `GroundingVerdictWireV1` therefore rewrites a frozen manifest key with no
  visible edit to any id literal. Separately, `llm/wire.py` declares
  `BRIDGE_LEDGER_CONTRACT_V3` and `BRIDGE_COMPOSITION_CONTRACT_V2` and nothing
  reads them: the real pinning lives in `_EXACT_V6_CONTRACTS` and in
  `bridge/harness.py`'s version map. Editing the constants changes nothing.
`check: python -c "from deepreason.llm.wire import DirectWireContract as D; from deepreason.bridge.review import GroundingVerdictWireV1 as V; from deepreason.bridge.repair import GroundingRepairWireV1 as R; assert D(V).contract_id=='groundingverdictwirev1.direct.v1'; assert D(R).contract_id=='groundingrepairwirev1.direct.v1'" && grep -q "DirectWireContract(" src/deepreason/run_manifest.py && test "$(grep -rn "BRIDGE_LEDGER_CONTRACT_V3\|BRIDGE_COMPOSITION_CONTRACT_V2" --include=*.py src/deepreason tests | wc -l)" -eq 2`
- **Bridge recovery tolerates exactly one prompt-digest mismatch, and it is not
  a bug.** `_recover_output` normally rejects a stored result whose reconstructed
  prompt digest differs. The exception: a terminal of `schema_exhausted` whose
  work id and route lease are named by the durable compact-recovery transition.
  The exhausted call necessarily PREDATES the compact transition it triggered,
  so re-rendering it from the live sticky state produces the later compact
  presentation and would falsely reject a correctly recorded base-profile
  prompt. Everything else about that attempt — payload, route, contract, bundle,
  stored prompt bytes — is still checked. **Residue: this branch has no
  dedicated regression;** the bridge recovery tests cover
  `SCHEMA_EXHAUSTED`, `PROVIDER_RECEIPT_MISSING`, `PROVIDER_RESULT_INVALID` and
  `SEQUENCE_MISMATCH`, and none of them exercises a compact transition. It is
  held by the code and its comment alone.
`check: python -c "import inspect; from deepreason.bridge.transactional_adapter import TransactionalBridgeAdapter as T; s=inspect.getsource(T._recover_output); assert 'compact_recovery_by_route_seat' in s and 'schema_exhausted' in s" && grep -q "stored provider result differs from the reconstructed request" src/deepreason/bridge/transactional_adapter.py && test "$(grep -c "compact_recovery_by_route_seat" tests/test_v6_bridge_transactions.py)" -eq 1 && grep -q "compact_recovery_by_route_seat == {}" tests/test_v6_bridge_transactions.py`
