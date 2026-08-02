<!-- DR-SEAM-llm-x-workflow -->
Verified-at: 08dcdf3c
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

Twenty-one modules import both packages. Five carry the agreement.
`check: python -c "import importlib, pkgutil, re, sys, pathlib, deepreason.llm as L; [importlib.import_module('deepreason.llm.' + m.name) for m in pkgutil.iter_modules(L.__path__)]; assert not [m for m in sys.modules if m.startswith('deepreason.workflow')]; s=pathlib.Path('src/deepreason/llm/adapter.py').read_text(); assert not re.search(r'^(from|import) deepreason\.workflow', s, re.M); assert len(re.findall(r'^\s+from deepreason\.workflow', s, re.M)) == 2" && test "$(grep -rn "deepreason\.workflow" --include=*.py src/deepreason/llm/ | wc -l)" -eq 2 && test "$(grep -rl "^from deepreason\.llm" --include=*.py src/deepreason/workflow/ | wc -l)" -eq 8 && grep -q "^from deepreason.llm.budget import" src/deepreason/workflow/transaction_service.py && grep -q "from deepreason.workflow.trace import ConjectureControlTrace" src/deepreason/workflow/__init__.py && test "$(for f in $(grep -rl "deepreason\.llm" --include=*.py src/deepreason); do grep -ql "deepreason\.workflow" "$f" && echo x; done | wc -l)" -ge 18`

## Where it is expressed

| Site | File | Symbol | What it enforces |
|---|---|---|---|
| Global guard | `llm/adapter.py` | `call(...)`, first branch on `transaction_authority_required` | a v6 adapter refuses any dispatch with no bundle |
| Guard armed at build | `llm/adapter.py` | `build_adapter`, `transaction_authority_required=(run_manifest ... schema_version == 6)` | the mode is derived from the manifest, never chosen by a caller |
| Binding | `llm/adapter.py` | `bind_v6_authority(harness, manifest)` | one adapter, one harness, one manifest; refuses without durable model classification or a route-seat behavioral plan |
| The capability object | `workflow/transaction.py` | `AuthorizedDispatch` (preparation, reservation record, exposure receipt, bundle, live `Reservation`) | the only type `call` accepts as authority |
| Dispatch identity | `workflow/transaction.py` | `DispatchAuthorizationBundleV1.verify_dispatch` | "dispatch differs from its authorization bundle" |
| Prompt freeze | `llm/adapter.py` | `preview_request` / `call`, both through `_render_request` | the digest bound at `WORK_ISSUED` is the digest dispatched |
| Atomic issue | `workflow/transaction_service.py` | `reserve_dispatch` → `finalize_dispatch` (`issue`) | plans, reservation, exposure and bundle land in one append or none |
| Meter ownership | `workflow/transaction_service.py`, `llm/budget.py` | `TokenMeter.reserve` at `reserve_dispatch`; bound equality in `call` | the workflow books; the adapter only checks the arithmetic |
| Repair ceiling | `llm/adapter.py`, `workflow/repair_transaction.py` | `retry_max=(0 if dispatch_authorization ...)`; `V6PatchRepairSession` | one bundle, one request; the ceiling is the manifest's grant |
| Route/contract agreement | `llm/adapter.py`, `workflow/transaction_service.py`, `workflow/profiles.py`, `workflow/replay.py` | `resolve_route_seat_behavioral_capability` (twice), `resolve_conjecture_route`, `_manifest_route` | the contract is frozen for the seat, and the seat is the manifest's route |
| Live route liveness | `llm/adapter.py` | `_require_transactional_route_dispatchable` | a route seat that exhausted its smallest contract cannot be dispatched, even mid-transaction |
| Presentation authority | `llm/adapter.py` | `_transactional_base_profile_for` / `_transactional_profile_for` | the profile comes from the manifest plus the durable compact transition, never from adapter state |
| Failure carrier | `llm/adapter.py` | `_spend(attempts)`, bound to `.spend` at nine sites | tokens already spent reach the record even when the call raises |
| Terminal from a failure | callers | `record_provider_attempt(call=spend, outcome="transport_failure", ...)` in six modules | a call that touched the provider still gets a durable attempt |
| Budget denial | `workflow/transaction_service.py` | `reserve_dispatch` → `WorkTerminalV1(status="budget_denied")` → `WorkBudgetDenied` | a refused reservation is a typed terminal, not an adapter exception |
| One action carries a call | `harness.py` | `record_transaction_transition(..., llm=)` | "only provider_result may carry an LLM call" |
| Replay pairing | `workflow/replay.py` | `PROVIDER_RESULT` branch of `_apply_transaction` | the stored attempt and the logged `LLMCall` must agree on bundle, contract, lease, prompt digest, raw blob and token total |
| Mid-flight recovery | `workflow/transaction_service.py` | `recover_incomplete` | unissued work is abandoned, issued-but-unanswered work is abandoned, an unadmitted result is handed back for validation |
| Deterministic resume | `workflow/{conjecture,nonconjecture,atomic}_recovery.py` | `recover_*_admission` | the raw blob named by `ProviderAttemptV1` is re-validated with no provider present |
| Canonical wrapper | `bridge/transactional_adapter.py` | `TransactionalBridgeAdapter.call` | every bridge model call becomes prepare → plan → issue → call → attempt → admission → terminate |
| Controller-v1 generation | `llm/adapter.py`, `workflow/trace.py` | `workflow_dispatch_observer` / `workflow_repair_observer`, `ConjectureControlTrace.require_authority` | the pre-v6 shape: observe-then-dispatch, with `WorkflowAuthorizationError` imported from `llm/adapter.py` |

The bundle's identity is exactly five fields plus the reservation reference; the
adapter passes all six by keyword at its one call site; and the prompt digest in
that tuple is computed the same way on both sides — once when the reservation is
taken, once when the exposure is written, once at dispatch, and once more from
the stored attempt at replay.
`check: python -c "import inspect, re, pathlib; from deepreason.workflow.transaction import DispatchAuthorizationBundleV1 as B; want=['work_id','attempt_index','contract_id','route_lease','prompt_sha256','reservation_ref']; sig=[n for n in inspect.signature(B.verify_dispatch).parameters if n != 'self']; site=re.search(r'verify_dispatch\(\n(.*?)\n            \)', pathlib.Path('src/deepreason/llm/adapter.py').read_text(), re.S).group(1); passed=re.findall(r'^\s+(\w+)=', site, re.M); assert sig == passed == want, (sig, passed)" && grep -q 'raise ValueError("dispatch differs from its authorization bundle")' src/deepreason/workflow/transaction.py && grep -q 'prompt_sha256 = hashlib.sha256(prompt.encode("utf-8")).hexdigest()' src/deepreason/llm/adapter.py && test "$(grep -c 'prompt_sha256 = hashlib.sha256(prompt.encode("utf-8")).hexdigest()' src/deepreason/workflow/transaction_service.py)" -eq 2 && grep -q 'raise ValueError("reserved prompt differs from dispatch prompt")' src/deepreason/workflow/transaction_service.py && grep -q "attempt.prompt_sha256 != item.authorization.prompt_sha256" src/deepreason/workflow/replay.py`

A v6 adapter refuses an unbound call, a pre-v6 adapter keeps the legacy path,
and the bridge wrapper is where an ordinary adapter is switched into
transactional mode — binding once, to one harness and one manifest, before it
can be called at all.
`check: grep -q "if self.transaction_authority_required and dispatch_authorization is None:" src/deepreason/llm/adapter.py && grep -q 'raise TypeError("dispatch_authorization must be an AuthorizedDispatch")' src/deepreason/llm/adapter.py && grep -q "transactional authorization replaces legacy work callbacks" src/deepreason/llm/adapter.py && grep -q "pre-rendered requests require transactional dispatch authorization" src/deepreason/llm/adapter.py && grep -q "workflow dispatch observation requires an unbound conjecturer call" src/deepreason/llm/adapter.py && grep -q "self._adapter.transaction_authority_required = True" src/deepreason/bridge/transactional_adapter.py && grep -q "self._adapter.bind_v6_authority(harness, manifest)" src/deepreason/bridge/transactional_adapter.py && grep -q "transactional adapter is already bound to another harness" src/deepreason/llm/adapter.py && grep -q "transactional adapter is already bound to another manifest" src/deepreason/llm/adapter.py && python -m pytest tests/test_v6_global_dispatch_guard.py::test_transaction_required_adapter_rejects_unbound_dispatch tests/test_v6_global_dispatch_guard.py::test_legacy_adapter_keeps_unbound_dispatch_compatibility tests/test_v6_bridge_transactions.py::test_every_v6_bridge_call_has_an_independent_complete_transaction -q`

Under an authorization the adapter's own meter gate and its own reservation are
both skipped, and the workflow's booked bound must match the one the rendered
request implies. The behavioural half is the ceiling test: work items, logged
calls and metered calls are equal, and nothing is left reserved.
`check: grep -q "if self.meter is not None and dispatch_authorization is None:" src/deepreason/llm/adapter.py && grep -q "^            elif self.meter is not None:" src/deepreason/llm/adapter.py && grep -q "reservation = dispatch_authorization.reservation$" src/deepreason/llm/adapter.py && grep -q "transactional reservation bound differs from rendered request" src/deepreason/llm/adapter.py && grep -q "conservative_prompt_bound," src/deepreason/workflow/transaction_service.py && python -m pytest "tests/test_v6_contract_schema_repair_runtime.py::test_manifest_grant_is_the_exact_provider_call_ceiling" -q`

One bundle authorizes one request: the repair session is built with
`retry_max=0`, which is exactly one attempt, and a second pass raises before
any dispatch.
`check: grep -q "retry_max=(0 if dispatch_authorization is not None else self.retry_max)," src/deepreason/llm/adapter.py && grep -q "transactional repair requires a new authorization bundle" src/deepreason/llm/adapter.py && python -c "import inspect; from deepreason.llm.repair import BoundedRepairSession as S; from deepreason.llm.adapter import WorkflowAuthorizationError as W; assert 'spend' in inspect.signature(W.__init__).parameters; assert S(contract='c', schema={'type':'object'}, initial_request='x', retry_max=0).attempt_count == 1" && python -m pytest tests/test_v6_live_repair_transactions.py::test_conjecture_patch_is_a_distinct_authorized_work_item -q`

The contract-for-this-seat agreement is checked three times over the same
manifest fields — at preparation, at render, and at replay — and terminal
route-seat exhaustion is re-checked immediately before dispatch as well as
durably.
`check: grep -q "wire contract differs from frozen route-seat behavioral authority" src/deepreason/llm/adapter.py && grep -q "V6_BEHAVIORAL_CONTRACT_NOT_AUTHORIZED" src/deepreason/workflow/transaction_service.py && grep -q 'raise WorkflowProfileError("WORKFLOW_ROUTE_LEASE_MISMATCH")' src/deepreason/workflow/profiles.py && grep -q "compact recovery route digest differs from the manifest" src/deepreason/workflow/replay.py && test "$(grep -c "V6_ROUTE_SEAT_INSUFFICIENT_CAPABILITY" src/deepreason/workflow/transaction_service.py)" -eq 3 && grep -q "self._require_transactional_route_dispatchable(route_ref)" src/deepreason/llm/adapter.py && python -m pytest tests/test_v6_insufficient_capability_terminal.py -q`

A typed failure carries its spend, six caller modules convert that spend into a
durable transport-failure attempt rather than losing it, and whichever way the
call ends its `LLMCall` crosses into the control plane at exactly one action —
where replay re-checks it against the issued authority.
`check: python -c "import inspect; from deepreason.llm.repair import SchemaRepairError as E; assert 'spend' in inspect.signature(E.__init__).parameters" && test "$(grep -c "spend = _spend(\|spend=_spend(" src/deepreason/llm/adapter.py)" -eq 9 && test "$(grep -rl 'outcome="transport_failure"' --include=*.py src/deepreason | wc -l)" -eq 6 && grep -q 'raise ValueError("only provider_result may carry an LLM call")' src/deepreason/harness.py && grep -q "provider result requires its work-bound LLM call" src/deepreason/workflow/replay.py && grep -q "provider result differs from issued authority" src/deepreason/workflow/replay.py && grep -q "provider result usage differs from its LLM call" src/deepreason/workflow/replay.py && python -m pytest tests/test_v6_controller3_replay_verification.py::test_provider_result_without_authorized_attempt_fails_closed tests/test_v6_bridge_transactions.py::test_v6_bridge_transport_failure_is_durably_terminalized -q`

A refused reservation is terminalized before it becomes an exception, and every
transactional caller re-raises `WorkBudgetDenied` ahead of its broad handler so
the work is not terminated twice.
`check: grep -q "raise WorkBudgetDenied(terminal) from error" src/deepreason/workflow/transaction_service.py && grep -q 'status="budget_denied",' src/deepreason/workflow/transaction_service.py && test "$(grep -rlE "^ *except WorkBudgetDenied:" --include=*.py src/deepreason | wc -l)" -eq 7 && python -c "import re, pathlib; bad=[f for f in ('src/deepreason/bridge/transactional_adapter.py','src/deepreason/workflow/repair_transaction.py','src/deepreason/scratch/authoring.py','src/deepreason/referee.py') if not re.search(r'except WorkBudgetDenied:\n\s+(#[^\n]*\n\s+)*raise\n\s+except (BaseException|Exception):', pathlib.Path(f).read_text())]; assert not bad, bad" && python -m pytest tests/test_v6_live_repair_transactions.py::test_repair_budget_denial_has_no_repair_exposure_or_dispatch tests/test_v6_context_continuation.py::test_child_budget_denial_has_no_exposure_and_no_dispatch -q`

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
`check: sed -n "/    def _mark_compact_recovery(/,/self._compact_recovery_roles.add(role)/p" src/deepreason/llm/adapter.py | grep -q "if self.transaction_authority_required:" && sed -n "/    def rehydrate_compact_recovery(/,/recovered: set\[str\] = set()/p" src/deepreason/llm/adapter.py | grep -q "if self.transaction_authority_required:" && grep -q "class V6ModelProfileOverrideForbidden" src/deepreason/llm/adapter.py && python -m pytest tests/test_v6_profile_authority.py -q`

**`llm/` appends no event and writes no workflow record.** It reads
`harness.workflow_state` to resolve presentation and route liveness, and it
constructs exactly one workflow type, `RouteLeaseRefV1`, purely to hand back
for verification. Every durable consequence is written by the caller through
`harness.record_transaction_transition`. This is what keeps a transport bug
from becoming a control-plane bug: the adapter can refuse, but it cannot
record.
`check: ! grep -rqE "record_transaction_transition|objects\.put|append_event" --include=*.py src/deepreason/llm && grep -q "state = harness.workflow_state" src/deepreason/llm/adapter.py && test "$(grep -c "RouteLeaseRefV1(" src/deepreason/llm/adapter.py)" -eq 1 && grep -q "    def record_transaction_transition(" src/deepreason/harness.py`

**Recovery has no provider boundary, and that is the whole point of it.** None
of `recover_conjecture_admission`, `recover_nonconjecture_admission` or
`recover_atomic_child_output` takes an adapter; no module under `workflow/`
names `LLMAdapter`, `build_adapter`, `OpenAICompatEndpoint` or calls
`.complete(`. The single exception is `repair_transaction.repair_schema_failure`,
which dispatches through an adapter it is HANDED and has no `retry_max`
parameter of its own — the ceiling is the manifest's grant, not a caller's
argument. A crashed run therefore resumes by re-validating the raw blob a
`ProviderAttemptV1` already names, which is why the same result can be admitted
twice without spending a second token.
`check: python -c "import inspect; from deepreason.workflow import conjecture_recovery as c, nonconjecture_recovery as n, atomic_recovery as a, repair_transaction as r; assert not [f for f in (c.recover_conjecture_admission, n.recover_nonconjecture_admission, a.recover_atomic_child_output) if 'adapter' in inspect.signature(f).parameters]; assert 'adapter' in inspect.signature(r.repair_schema_failure).parameters; assert 'retry_max' not in inspect.signature(r.repair_schema_failure).parameters" && ! grep -rqE "LLMAdapter|build_adapter|OpenAICompatEndpoint|\.complete\(" --include=*.py src/deepreason/workflow && grep -q "The provider boundary is deliberately absent from this module" src/deepreason/workflow/conjecture_recovery.py`

**Issued work is never dispatched again.** `recover_incomplete` closes what it
cannot finish — unissued preparations and issued-but-unanswered attempts become
`abandoned` terminals — and returns only the attempts whose raw result still
needs deterministic validation. Re-issuing an interrupted attempt would be the
intuitive fix and is exactly wrong: the reservation is gone, the exposure
receipt already asserts what the model saw, and a second request against the
same bundle has no authority.
`check: grep -q "Issued work is never dispatched again" src/deepreason/workflow/transaction_service.py && python -m pytest tests/test_v6_contract_schema_repair_runtime.py::test_replay_of_exhausted_repair_chain_never_redispatches tests/test_v6_nonconjecture_recovery.py::test_scheduler_recovers_valid_critic_without_provider_dispatch -q`

**Controller-v1 callbacks and a controller-v3 bundle may not coexist in one
call.** Passing `work_order_id` or `workflow_dispatch_observer` alongside
`dispatch_authorization` is a `ValueError`, and the observer path is restricted
to an unbound conjecturer call. Two generations of process authority describing
one provider request would make the record ambiguous about which one authorized
it. The absence is symmetric: `pre_rendered_request` exists only for the v3
repair path and is refused without an authorization. Both refusals are checked
by the guard check in "Where it is expressed".

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
   modules has the same five-arm shape — `WorkBudgetDenied` re-raised,
   `EndpointError` → transport-failure attempt, `SchemaRepairError` →
   `repair_schema_failure`, `BaseException` → abandon, success → attempt +
   admission + terminal. A change that updates the success arm alone leaves a
   crash mid-call unrecoverable, which no happy-path test will surface.
5. **Never widen `retry_max` under an authorization to "save a round trip".**
   The clamp is what makes provider calls countable against the manifest grant;
   an internal repair produces a provider request with no work item, and
   `len(work) == len(calls)` is the invariant the ceiling test asserts.

What breaks first, in the order you will see it:
`"dispatch differs from its authorization bundle"` (the adapter refused before
sending); then `"transactional reservation bound differs from rendered
request"` (the prompt changed after issue); then, on reopen,
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

## Traps

- **Preview/dispatch digest agreement proves identity, never correctness.**
  Both `preview_request` and `call` render through the same `_render_request`,
  so the bundle's `prompt_sha256` matches whatever that helper produces — even
  when what it produces is wrong. The v6 post-allocation pack edits demoted the
  `AllocatedPack` marker to plain `str`, the profile's prefix clip re-applied to
  a pack `PackIR` had already budgeted section-by-section, and the sealed
  advisory context was cut mid-JSON: observed live with 86 percent of the
  context bytes never dispatched, while every pre-dispatch authority check
  passed. The fix is a CONTENT check inside `_render_request` — so preview and
  dispatch both see it — plus the `pack_is_allocated` guard. When you add a
  step between issue and dispatch, ask what its failure would look like to the
  digest; the answer is usually "nothing".
`check: grep -q "if profile is not None and not pack_is_allocated:" src/deepreason/llm/adapter.py && grep -q "rendered provider request must contain the exact " src/deepreason/llm/adapter.py && grep -q "class AllocatedPack(str):" src/deepreason/llm/packs.py && python -m pytest tests/test_v6_conjecture_scratch_consumption.py::test_initial_v6_conjecture_commits_exact_model_facing_scratch_once tests/test_v6_conjecture_scratch_consumption.py::test_context_commit_failure_abandons_prepared_work_before_dispatch -q`
- **A budget denial arrives already terminalized.** `reserve_dispatch` appends
  the `budget_denied` terminal and then raises `WorkBudgetDenied`, so a caller
  whose `except BaseException: abandon(...)` sees it will write a second
  terminal after termination. Every transactional call site therefore re-raises
  `WorkBudgetDenied` first; `referee.py` carries the comment that says why. The
  sibling shape is `error.transaction_terminalized = True` / `error.spend =
  None`: once a failure has been recorded as a `ProviderAttemptV1`, the flag
  tells the scheduler to log it as dropped rather than re-record it, and
  clearing `.spend` stops the legacy `_drop` path from counting the tokens
  twice. Adding a new exception path without both markers double-counts spend
  or double-terminates work.
`check: grep -q "any further transition would be a second" src/deepreason/referee.py && test "$(grep -rlE "transaction_terminalized" --include=*.py src/deepreason | wc -l)" -eq 7 && grep -q 'if getattr(error, "transaction_terminalized", False):' src/deepreason/scheduler/scheduler.py`
- **`WorkflowAuthorizationError` is defined in `llm/adapter.py`, and both sides
  raise it.** `workflow/trace.py` imports it to signal that its own persistence
  failed; the adapter raises it to refuse an unauthorized dispatch. An
  `except WorkflowAuthorizationError` therefore catches two very different
  events — "the control plane could not record" and "the provider boundary
  refused" — and only the message distinguishes them. Do not move the class to
  `workflow/` to tidy the layering: `llm/` has no module-scope import of
  `workflow/`, and the type must be raisable from inside `call`.
`check: grep -q "^class WorkflowAuthorizationError(RuntimeError):" src/deepreason/llm/adapter.py && grep -q "^from deepreason.llm.adapter import WorkflowAuthorizationError$" src/deepreason/workflow/trace.py && grep -q "def require_authority" src/deepreason/workflow/trace.py`
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
`check: python -c "import re, pathlib; assert re.search(r'if attempt != 0:\n\s+raise WorkflowAuthorizationError\(\n\s+\"transactional repair requires a new authorization bundle\",', pathlib.Path('src/deepreason/llm/adapter.py').read_text())" && grep -q "retry_max=0," tests/test_v6_live_repair_transactions.py && grep -q "transaction_authority_required=True," tests/test_v6_live_repair_transactions.py`
