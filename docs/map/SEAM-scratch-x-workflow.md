<!-- DR-SEAM-scratch-x-workflow -->
Verified-at: 770ea1344
Verify: python tools/docs_verify.py
Owns: src/deepreason/scratch/authoring.py, src/deepreason/workflow/nonconjecture_recovery.py
Sides: DR-SUB-scratch, DR-SUB-workflow

# scratch x workflow

## The agreement

The scratchpad promises the control plane that a note is never authority: every
scratch mutation is its own log entry, its formal `state_diff` is empty, and no
scratch record grants, denies or settles a unit of work. The control plane
promises in
return that it will authorize a scratch model call exactly as it authorizes any
other — preparation, context plan, token reservation, exposure receipt,
dispatch, provider attempt, semantic admission, terminal — while reading nothing
the scratchpad wrote. The two append-only histories are ordered against each
other by a single integer, `scratch_fence_seq`, which every workflow record
carrying it must set equal to `formal_fence_seq`, so "the state this work was
planned against" is one log prefix and not two. Content crosses in exactly one
direction and one shape: the rendered pack enters the transaction as a
`VisibleContextItemV1` in the `SCRATCH` namespace — an alias, an object ref, a
sha256 and a byte count, never text — and the note that comes back leaves as a
bare object id in `SemanticAdmissionV1.admitted_refs`. The join between a
transaction and the note it produced is the scratch event's `context_ref`, which
under v6 holds the workflow exposure receipt's id; that single field is what
makes the write idempotent, so a crash between the scratch effect and its
admission is re-derived from the record instead of re-dispatched. The import
arrow is deliberately lopsided: `scratch/authoring.py` is a CONSUMER of
`InquiryTransactionService`, and the control plane proper — reducer, state
machine, transaction, transaction service, trace, replay, lifecycle — imports no
scratch module at all.

FORTY-NINE files under `src/deepreason` mention both sides. This sentence read
"Forty-seven" while its own check asserted 48 — a pre-existing disagreement of
one, corrected here rather than left, and NOT caused by this tranche. The 48
became 50 on 2026-09-04 when `seat_sources/shipped.py` joined: it names the
v6 scratch workshop prompt and the transaction work order it reads a fence
from. It became 49 on 2026-08-30 when `aftercycle.py` joined by naming `workflow` in a
docstring while importing nothing from either side; the census counts WORD
MENTIONS, and the import-graph clause after it is what counts edges. Nine carry
the agreement — the ones named in the table below — and the two this document owns
are where most of it is written. Exactly one scratch module reaches into the
workflow, and exactly four workflow modules reach back, none of them the control
plane. The module enumeration is dynamic rather than a file list, so a rename
fails the check instead of slipping past a grep, and it is read from the IMPORT
GRAPH rather than from the source text: a relative `from ..scratch import` in a
control-plane module resolves to the same edge as an absolute one, which a
substring test missed.
`check: test "$(for f in $(grep -rl scratch src/deepreason --include=*.py); do grep -ql workflow "$f" && echo x; done | wc -l)" -eq 50 && python -c "import ast,pathlib;B=lambda pkg,l:('deepreason.'+pkg) if l==1 else ('deepreason' if l==2 else 'deepreason.UNRESOLVED');T=lambda n,pkg:[a.name for a in n.names] if isinstance(n,ast.Import) else ([(B(pkg,n.level)+'.'+(n.module or '')).rstrip('.')] if n.level else [n.module or '']);D=lambda pkg,other:sorted(p.stem for p in pathlib.Path('src/deepreason/'+pkg).glob('*.py') if any(m==other or m.startswith(other+'.') for n in ast.walk(ast.parse(p.read_text())) if isinstance(n,(ast.Import,ast.ImportFrom)) for m in T(n,pkg)) or other in p.read_text());assert D('scratch','deepreason.workflow')==['authoring'],D('scratch','deepreason.workflow');assert D('workflow','deepreason.scratch')==['conjecture_recovery','models','nonconjecture_recovery','profiles'],D('workflow','deepreason.scratch')"`

Four workflow records carry `scratch_fence_seq`, every one of them refuses a
value that differs from its formal fence, and the refusal is a validator rather
than a convention. The set is enumerated at import time, so a fifth record that
forgot the identity validator fails here. Each named validator is then CALLED
with mismatched fences and must raise: a validator whose body still mentions the
comparison but no longer raises passes a source-text test and fails this one.
`check: python -c "import types,inspect,pkgutil,importlib,pydantic,pytest,deepreason.workflow as W;V={'deepreason.workflow.models.RepairWorkOrderV1':'_one_state_fence','deepreason.workflow.models.WorkOrderEnvelopeV1':'_authority_shape','deepreason.workflow.state.WorkflowProcessStateV1':'_one_state_prefix','deepreason.workflow.transaction.WorkPreparationV1':'_one_state_fence_and_payload'};seen={};[seen.update({o.__module__+'.'+n:o}) for m in pkgutil.iter_modules(W.__path__) for n,o in vars(importlib.import_module('deepreason.workflow.'+m.name)).items() if inspect.isclass(o) and issubclass(o,pydantic.BaseModel) and o.__module__=='deepreason.workflow.'+m.name and 'scratch_fence_seq' in getattr(o,'model_fields',{})];assert sorted(seen)==sorted(V),sorted(seen);assert all('formal_fence_seq' in o.model_fields for o in seen.values());[pytest.raises(ValueError,vars(o)[V[k]],types.SimpleNamespace(formal_fence_seq=7,scratch_fence_seq=6)).match('fence') for k,o in seen.items()]" && python -c "from deepreason.workflow.state import WorkflowProcessStateV1 as S;S.initial(manifest_digest='0'*64,workflow_profile='inquiry.active.v1',formal_fence_seq=7,scratch_fence_seq=6)" 2>&1 | grep -q "workflow state requires one formal/scratch fence"`

## Where it is expressed

| Site | File | Symbol | What it enforces |
|---|---|---|---|
| Fence identity | `workflow/transaction.py`, `workflow/models.py`, `workflow/state.py` | `_one_state_fence_and_payload`, `_authority_shape`, `_one_state_fence`, `_one_state_prefix` | a preparation, a work order, a repair order and a process state each refuse a scratch fence that differs from the formal one |
| Fence assignment | `scratch/authoring.py` | `fence = max(0, harness._next_seq - 1)` in `_v6_call`, passed as both fences to `prepare(task_kind=SCRATCH_AUTHORING)` | a scratch transaction opens at the current log head and nowhere else |
| Typed names | `workflow/models.py` | `WorkflowTaskKind.SCRATCH_AUTHORING`, `CapabilityOutcome.SCRATCH_PROPOSAL` | the control plane names scratch work without knowing what a note says |
| Exposure | `scratch/authoring.py` → `workflow/transaction.py` | `context_plan(plan_kind="scratch", items=(VisibleContextItemV1(namespace=SCRATCH, alias="SCR_001", ...),))` | the rendered pack is byte-accounted by hash under its own alias namespace |
| Pre-transaction gate | `scratch/authoring.py` | `_validate_context` → `SCRATCH_CONTEXT_NOT_RENDERED`, `SCRATCH_CONTEXT_FORGED` | the attention receipt must already be durable in scratch state, and the render's handle order must equal its `final_order`, before a transaction opens |
| Exposure fidelity | `scratch/authoring.py` | `prompt.count(rendered.text) != 1` → `SCRATCH_CONTEXT_NOT_EXPOSED`; `"content-addressed scratch preparation drifted"` | the exact rendered bytes reach the provider once and hash to the refs the preparation already named |
| The join key | `scratch/authoring.py` | `context_ref=authorized.exposure_receipt.id` (v6) vs `blobs.put(receipt_bytes)` (legacy) | one `OpaqueRef` field on the scratch event names the workflow exposure receipt under v6 and the render-receipt blob before it |
| Effect before authority | `scratch/authoring.py` | `admit_transactional_effect(...)` then `_admit_effect(result, block.id)` | the scratch event lands first; the admission then names an object the log already contains |
| Idempotent write | `scratch/authoring.py` | `SCRATCH_RECOVERY_EFFECT_DUPLICATED`, `SCRATCH_RECOVERY_EFFECT_MISMATCH` | one exposure receipt may own at most one scratch effect per action, and a matching one is verified rather than repeated |
| Restart selection | `scratch/authoring.py` | `_resolve_recovery_payload` filtering `task_kind != WorkflowTaskKind.SCRATCH_AUTHORING`, `_pending_decomposition_for_parent` | the shared `transaction_work` map pools every task kind; the scratch scan must filter or it will adopt another seat's work |
| Recovery authority | `workflow/nonconjecture_recovery.py` | `_scratch_contract`, `_recover_scratch_effect` | role, seat, contract id, epistemic boundary, receipt hash, exposure shape and input refs are re-proved from the stored blob before the effect is re-derived |
| Receipt reload order | `workflow/nonconjecture_recovery.py` | `ScratchLinkWireContract(indexed_block_ids=list(receipt.ordered_refs("block")))` | the reloaded handle map is read by handle index, never by mapping order |
| Decomposition shape | `workflow/replay.py` | `child_partition == "scratch_single_object"` → `scratch-{operation}-minimal` | replay derives the child key from a three-valued operation literal, never from a scratch record |
| Retrieval grant | `workflow/models.py`, `workflow/profiles.py` | `CapabilityGrantV1.permitted_retrieval_channels`, `_bounded_channels` | the workflow grants scratch channels by NAME, and refuses `direct_open` |
| Separate materialization | `harness.py` | `_apply_event`: `workflow_state.apply(...)`, then `scratch_state.apply(...)` | one event moves at most one of the two states; process events cannot touch the formal `StateDiff` |
| Replay validation | `invariants.py` | `validate_v6_expansion_lineage`, `"selection receipt names another scratch fence"` | an expanded advisory context is proved from the workflow transaction history, and the scratch fence is re-checked against the replayed selection and render receipts |

The scratch transaction opens at the log head with one exposed item, the record
of what the model saw has no field that could hold the text, and the scratchpad
must have committed the selection — with the render's handle order compared
against the committed order — before the transaction opens at all. The gate is
exercised, not read: `_validate_context` is called with no committed receipt, and
then with the committed order REVERSED, and must refuse both — an order-blind
comparison keeps every symbol this paragraph names and still forges the pack.
`check: grep -q "fence = max(0, self.service.harness._next_seq - 1)" src/deepreason/scratch/authoring.py && grep -q "task_kind=WorkflowTaskKind.SCRATCH_AUTHORING," src/deepreason/scratch/authoring.py && grep -q "formal_fence_seq=fence," src/deepreason/scratch/authoring.py && grep -q "scratch_fence_seq=fence," src/deepreason/scratch/authoring.py && grep -q "plan_kind=\"scratch\"," src/deepreason/scratch/authoring.py && grep -q "namespace=ContextNamespace.SCRATCH," src/deepreason/scratch/authoring.py && grep -q "alias=\"SCR_001\"," src/deepreason/scratch/authoring.py && python -c "from deepreason.workflow.transaction import VisibleContextItemV1 as V;assert sorted(V.model_fields)==['alias','content_sha256','namespace','object_ref','planned_bytes'], sorted(V.model_fields)" && python -c "import types,pytest;from deepreason.scratch.authoring import ScratchAuthoringService as S, ScratchAuthoringError as E;from deepreason.scratch.render import ScratchRenderReceiptV1 as R;B='sha256:'+'b'*64;C='sha256:'+'c'*64;r=R.create(state_seq=1,attention_receipt='sha256:'+'a'*64,block_handles={'B1':B,'B2':C},cluster_handles={},link_handles={},guide_handles={});d=types.SimpleNamespace(receipt=r);mk=lambda o:types.SimpleNamespace(service=types.SimpleNamespace(state=types.SimpleNamespace(attention_receipts={} if o is None else {r.attention_receipt:types.SimpleNamespace(final_order=o)})));assert pytest.raises(E,S._validate_context,mk(None),d).value.code=='SCRATCH_CONTEXT_NOT_RENDERED';assert pytest.raises(E,S._validate_context,mk((C,B)),d).value.code=='SCRATCH_CONTEXT_FORGED';assert S._validate_context(mk((B,C)),d)"`

The effect precedes its admission, the join is `context_ref`, and the
transactional scratch event carries no provider call of its own. All THREE
authoring entry points are checked, not just `author_block`: the ordering is a
property of each seat, and a reversal in `author_link` or `author_cluster_guide`
is the same defect.
`check: python -c "import inspect;from deepreason.scratch.authoring import ScratchAuthoringService as S;a=inspect.getsource(S.admit_transactional_effect);[__import__('sys').exit('order: '+f.__name__) for f in (S.author_block,S.author_link,S.author_cluster_guide) if not inspect.getsource(f).index('admit_transactional_effect(') < inspect.getsource(f).index('self._admit_effect(result,')];assert 'event.scratch.context_ref == context_ref' in a and a.count('event.llm is not None')==3 and 'llm=' not in a and 'SCRATCH_RECOVERY_EFFECT_DUPLICATED' in a and 'SCRATCH_RECOVERY_EFFECT_MISMATCH' in a" && python -c "import inspect;from deepreason.scratch.authoring import ScratchAuthoringService as S;assert 'context_ref=authorized.exposure_receipt.id' in inspect.getsource(S._v6_call);assert 'context_ref = self.service.harness.blobs.put(receipt_bytes)' in inspect.getsource(S._legacy_call)"`

Recovery re-derives the note with the provider boundary absent, re-proves the
declared epistemic boundary, and touches the rendered bytes only to hash them.
The seventeen `_authority` re-proofs are read from the AST, not the text: none
may take a constant condition, and the two this seam depends on — the epistemic
boundary and the single-item exposure shape — must still test the values they
name. `_authority(True, "scratch epistemic boundary differs")` keeps every string
a grep would look for and re-proves nothing.
`check: python -c "import ast,inspect,textwrap;from deepreason.workflow import nonconjecture_recovery as N;r=inspect.getsource(N._recover_scratch_effect);c=inspect.getsource(N._scratch_contract);assert 'adapter=None' in r and 'admit_transactional_effect' in r;assert c.count('rendered_bytes')==2 and 'hashlib.sha256(rendered_bytes).hexdigest()' in c and 'receipt.ordered_refs(' in c;t=ast.parse(textwrap.dedent(c));C=[n for n in ast.walk(t) if isinstance(n,ast.Call) and getattr(n.func,'id',None)=='_authority' and len(n.args)>1];assert len(C)>=17,len(C);assert not [n for n in C if isinstance(n.args[0],ast.Constant)];M={ast.literal_eval(n.args[1]):ast.dump(n.args[0]) for n in C if isinstance(n.args[1],ast.Constant)};assert 'epistemic_boundary' in M['scratch epistemic boundary differs'] and 'advisory_non_grounding' in M['scratch epistemic boundary differs'];assert 'ContextNamespace' in M['scratch exposure shape differs'] and 'SCR_001' in M['scratch exposure shape differs']" && python -m pytest tests/test_v6_scratch_authoring_transactions.py::test_restart_recovers_durable_scratch_result_without_redispatch tests/test_v6_constrained_scratch_execution.py::test_minimal_scratch_durable_result_recovers_without_redispatch -q`

Replay computes the minimal-contract child key from the operation literal alone,
inside a method that imports nothing from `scratch`; `verify_root` then re-checks
the fence against the replayed scratch state and proves an expanded context from
the durable transaction lineage. The method's import list is read from its AST,
not searched for the string `deepreason.scratch`, so a relative
`from ..scratch import` inside it fails; the three-valued literal is pinned as a
set, so a fourth operation cannot be added silently. Each replay-validation
message is located
through the `if` that raises it and the GUARD is inspected, because a diagnostic
string survives the comparison that earns it: `elif False:` above
`selection receipt names another scratch fence` leaves the grep green and the
fence unchecked.
`check: python -c "import ast,inspect,textwrap;from deepreason.workflow.replay import WorkflowReplayState as W;src=inspect.getsource(W._validate_contract_decomposition_transition);assert 'scratch_single_object' in src and 'scratch-{operation}-minimal' in src and 'scratch decomposition source operation is invalid' in src;assert not [n for n in ast.walk(ast.parse(textwrap.dedent(src))) if isinstance(n,(ast.Import,ast.ImportFrom))];assert sorted({ast.literal_eval(e) for n in ast.walk(ast.parse(textwrap.dedent(src))) if isinstance(n,ast.Set) for e in n.elts})==['block','guide','link']" && python -c "import ast,pathlib;t=ast.parse(pathlib.Path('src/deepreason/invariants.py').read_text());G=lambda m:sorted([n for n in ast.walk(t) if isinstance(n,ast.If) and m in ast.dump(ast.Module(body=n.body,type_ignores=[]))],key=lambda n:len(ast.dump(n)))[0];a=ast.dump(G('selection receipt names another scratch fence').test);b=ast.dump(G('render receipt names another scratch fence').test);c=ast.dump(G('expanded context has no durable continuation decision').test);assert 'state_seq' in a and 'scratch_fence_seq' in a and 'NotEq' in a, a;assert 'state_seq' in b and 'scratch_fence_seq' in b and 'NotEq' in b, b;assert 'decision_ref' in c, c" && grep -q "h.workflow_state.transaction_work.get(call.work_order_id)" src/deepreason/invariants.py`

## What is deliberately absent

**The control plane cannot read a note, and the refusal is structural rather
than habitual.** `reducer`, `state`, `transaction`, `transaction_service`,
`trace`, `replay` and `lifecycle` import no scratch module — see the enumeration
check above. The only structured scratch record any workflow module reloads is
`ScratchRenderReceiptV1`, which is a handle→hash table plus a fence; it has no
field that could carry a block's content. A design that hands the reducer or the
replay validator a note is not a design that needs review; it is already
impossible without adding an import that this seam's first check forbids. The
word ONLY is checked too: exactly one scratch record is deserialized anywhere
under `workflow/`, and it is this one.
`check: python -c "from deepreason.scratch.render import ScratchRenderReceiptV1 as R;from deepreason.workflow.nonconjecture_recovery import ScratchRenderReceiptV1 as Q;assert Q is R;assert sorted(R.model_fields)==['attention_receipt','block_handles','cluster_handles','guide_handles','link_handles','receipt_hash','schema_','state_seq'], sorted(R.model_fields)" && test "$(grep -rhoE "Scratch[A-Za-z0-9_]*\.model_validate(_json)?\(" src/deepreason/workflow/ | sort -u)" = "ScratchRenderReceiptV1.model_validate("`

**No event is both a scratch mutation and a control transition.** `Event.rule`
is one value, and each process payload must appear together with its own rule, so
a scratch write and the transition that authorized it are always distinct log
entries with distinct sequence numbers. That is precisely why the fence has work
to do: without the separation there would be nothing to order. The same
validator makes the formal `StateDiff` of both empty, so neither can move a
status.
`check: python -c "from deepreason.ontology import Rule;from deepreason.ontology.event import Event;from deepreason.scratch.events import ScratchEventPayloadV1 as P;from deepreason.scratch.models import domain_hash;b=domain_hash(\"f\",{\"b\":1});p=P(action=\"block_created\",actor=\"user\",outputs=[b]);Event(seq=0,ts=\"t\",rule=Rule.SCRATCH,outputs=[b],scratch=p)" && python -c "from deepreason.ontology import Rule;from deepreason.ontology.event import Event;from deepreason.scratch.events import ScratchEventPayloadV1 as P;from deepreason.scratch.models import domain_hash;b=domain_hash(\"f\",{\"b\":1});p=P(action=\"block_created\",actor=\"user\",outputs=[b]);Event(seq=0,ts=\"t\",rule=Rule.CONTROL,outputs=[b],scratch=p)" 2>&1 | grep -q "Scratch rule and typed scratch payload must appear together"`

**Scratch state is not in the workflow replay digest, and never may be.**
`WorkflowReplayState` holds no scratch field, and `digest` — the value the
harness seals into `workflow-checkpoint.json` and `verify_root` compares across
two replays — has no scratch section. The two states are materialized side by
side by `Harness._apply_event`, never one inside the other. Folding scratch into
the digest would change the digest of every root written before the change, which
`DR-INV-frozen-surfaces` rules out by definition.
`check: python -c 'import inspect;from deepreason.workflow.replay import WorkflowReplayState as W;from deepreason.harness import Harness;s=W();assert "transaction_work" in vars(s) and not [a for a in vars(s) if "scratch" in a];d=inspect.getsource(W.__dict__["digest"].fget);assert "transactions" in d and "scratch" not in d;h=inspect.getsource(Harness._apply_event);assert h.index("self.workflow_state.apply(event, resolved_workflow)") < h.index("self.scratch_state.apply(event, self.objects)")' && grep -q "process events cannot mutate formal StateDiff" src/deepreason/ontology/event.py`

**Scratch authoring is never a process branch.** `WorkOrderEnvelopeV1.task_kind`
is a one-value `Literal[CONJECTURE]`, so a `SCRATCH_AUTHORING` preparation cannot
become a work order, cannot enter `WorkflowProcessStateV1.work_items`, and has no
branch state to advance. It lives entirely in the controller-v3 transaction
history and is settled through the non-conjecture recovery path. Widening that
`Literal` to "make scratch a first-class work kind" would give notes a seat in
the process state machine, which is the coupling this seam exists to prevent.
`CapabilityGrantV1.task_kind` is pinned to the same one value, because the
envelope only accepts a grant of its own kind — widening the grant is the first
half of that change and would otherwise pass unnoticed.
`check: python -c "import typing;from deepreason.workflow.models import WorkOrderEnvelopeV1 as E, CapabilityGrantV1 as G, WorkflowTaskKind as K;assert typing.get_args(E.model_fields['task_kind'].annotation)==(K.CONJECTURE,);assert typing.get_args(G.model_fields['task_kind'].annotation)==(K.CONJECTURE,);assert K.SCRATCH_AUTHORING in set(K)" && grep -q "WorkflowTaskKind.SCRATCH_AUTHORING," src/deepreason/workflow/nonconjecture_recovery.py`

**`direct_open` is never granted.** `CapabilityGrantV1` is the one place the
workflow speaks the scratchpad's `RetrievalChannel` vocabulary, and it refuses
the single channel that would let a model name a specific block instead of
describing what it wants retrieved. Eleven channels are grantable; the twelfth
is refused at construction, not filtered downstream. The count is part of the
claim: all eleven are granted in ONE call, so a new channel that nobody wired
into the grant shows up here rather than in a run.
`check: python -c "from deepreason.workflow.models import CapabilityGrantV1 as G,CapabilityOutcome as O;from deepreason.scratch.models import RetrievalChannel as R;ok=tuple(c for c in R if c is not R.DIRECT_OPEN);assert len(list(R))==12 and len(ok)==11,len(ok);G.create(allowed_outcomes=(O.CANDIDATE_PROPOSAL,O.CONTEXT_REQUEST),max_candidates=1,max_local_repairs=0,remaining_context_expansions=1,max_extra_context_blocks=1,permitted_retrieval_channels=ok)" && python -c "from deepreason.workflow.models import CapabilityGrantV1 as G,CapabilityOutcome as O;from deepreason.scratch.models import RetrievalChannel as R;G.create(allowed_outcomes=(O.CANDIDATE_PROPOSAL,O.CONTEXT_REQUEST),max_candidates=1,max_local_repairs=0,remaining_context_expansions=1,max_extra_context_blocks=1,permitted_retrieval_channels=(R.DIRECT_OPEN,))" 2>&1 | grep -q "direct_open is never a conjecture capability"`

**The fence is NOT an absence to be optimised away.** It is redundant-looking
precisely because both sides always set it from the same `_next_seq - 1`, and
someone will eventually propose deleting `scratch_fence_seq` as duplicated data.
It is the field that makes "this work was planned against that scratch prefix" a
claim a replay can check; removing it removes the ordering, not the coupling. It
is also frozen: it is part of every recorded preparation and work order, so its
removal invalidates existing replay-valid roots.

## How to change it

1. **Read `DR-INV-frozen-surfaces` first.** `WorkPreparationV1`,
   `WorkOrderEnvelopeV1` and `WorkflowProcessStateV1` are content-addressed
   records inside recorded roots, and `ScratchPolicy` / the scratch-authoring
   policy are manifest surfaces, so widening either end moves qualification
   subject digests. A per-run mode goes on `Config`.
2. **Decide which of the three couplings you are touching**, because they are
   separately gated: the FENCE (ordering), the EXPOSURE (scratch → transaction),
   and the EFFECT (transaction → scratch). A change to one must leave the other
   two byte-identical in the record.
3. **Change the durable record before the call sites.** Adding a field to the
   exposure item or the preparation means deciding what its absence means for a
   record written before you existed, and `nonconjecture_recovery._scratch_contract`
   must be able to re-derive it from the stored blob alone — it has no provider
   and no live state.
4. **Move the write path and the recovery path together.** The authoring
   service's `admit_transactional_effect` and the recovery module's
   `_recover_scratch_effect` are one agreement in two files: the first appends
   the effect, the second must recognise that same effect as already done. Change
   one alone and a crash between the scratch event and its admission becomes
   either a duplicate note or a hard recovery failure — neither shows up in a
   test that never crashes.
5. **Keep the effect before the admission.** `SemanticAdmissionV1` with
   `outcome="admitted"` requires `admitted_refs`, and those refs must already
   name objects in the log. Reversing the order produces an admission that points
   at nothing until the next append.
6. **Never let the control plane import `scratch`.** If a control-plane module
   needs to know something about a note, the answer is a typed field on a
   workflow record, not a lookup.

What breaks first, in the order you will meet it: `SCRATCH_CONTEXT_NOT_RENDERED`
or `SCRATCH_CONTEXT_FORGED` if the selection is not durable or the render order
drifted; `"content-addressed scratch preparation drifted"` if you change what is
hashed without changing what is put; `SCRATCH_CONTEXT_NOT_EXPOSED` if a
presentation transform edits the pack after the plan was priced;
`"scratch exposure shape differs"` from recovery if you add a second exposed
item; then, only on a later run, `verify_root`'s `workflow-replay` or
`scratch-replay` failure — the expensive one, because the root is committed.

The tests that will catch you, cheapest first:
`tests/test_scratch_replay.py` (the two states stay separate),
`tests/test_v6_scratch_atomicity.py` (the write direction),
`tests/test_v6_scratch_authoring_transactions.py` (the whole transaction
lifecycle, including budget denial, transport failure, repair and restart),
`tests/test_v6_constrained_scratch_execution.py` (the minimal-contract
decomposition child), `tests/test_v6_controller3_replay_verification.py`
(controller-v3 replay).
`check: python -m pytest tests/test_v6_scratch_authoring_transactions.py::test_block_link_and_guide_each_use_complete_independent_transactions tests/test_v6_scratch_authoring_transactions.py::test_request_envelope_overflow_has_no_scratch_or_transaction_mutation tests/test_v6_scratch_authoring_transactions.py::test_transport_failure_is_typed_once_without_scratch_effect tests/test_scratch_replay.py::test_scratch_events_replay_at_every_fence_and_leave_formal_state_unchanged -q`

## Traps

- **A budget denial is a budget signal, not a scratch failure.** `_v6_call`
  catches `WorkBudgetDenied` and re-raises it BEFORE the generic
  `except BaseException` that abandons the preparation with
  `scratch_preissue_failure`. Swapping those two clauses would convert the typed
  budget stop that `DR-SUB-workflow` owns into a scratch-shaped abandonment, and
  the run would report the wrong reason for stopping. The reservation is refused
  before any exposure exists, so a denied scratch call leaves no evidence that
  the model was shown anything.
`check: python -c 'import inspect;from deepreason.scratch.authoring import ScratchAuthoringService as S;src=inspect.getsource(S._v6_call);assert src.index("except WorkBudgetDenied:") < src.index("except BaseException:")' && python -m pytest tests/test_v6_scratch_authoring_transactions.py::test_budget_denial_has_no_exposure_or_provider_dispatch -q`
- **`transaction_work` pools every task kind.** The scratch restart scan walks
  the same map that holds conjecture, criticism, bridge and repair items, so
  `_resolve_recovery_payload` filters on `task_kind` and `manifest_digest` before
  it will adopt an item, and `_repair_items` filters on `WorkflowTaskKind.REPAIR`
  plus the parent work id. This is the scratch instance of the general rule that
  a shared workflow map must be filtered by type before it is counted; an
  unfiltered scan here would resume another seat's unfinished work as if it were
  a scratch chain. Two matching unfinished chains fail closed rather than
  guessing.
`check: python -c 'import inspect;from deepreason.scratch.authoring import ScratchAuthoringService as S;r=inspect.getsource(S._resolve_recovery_payload);p=inspect.getsource(S._repair_items);assert "task_kind != WorkflowTaskKind.SCRATCH_AUTHORING" in r and "manifest_digest != manifest.sha256" in r;assert "task_kind == WorkflowTaskKind.REPAIR" in p' && python -m pytest tests/test_v6_scratch_authoring_transactions.py::test_ambiguous_unfinished_scratch_chains_fail_closed_before_redispatch -q`
- **Render-receipt handle maps reload key-sorted, and the recovery path is the
  second consumer in this seam to meet it.** The receipt reaching
  `_scratch_contract` came out of a blob through canonical JSON, whose sorted keys
  iterate `B1, B10, B11, B2, …`. The link contract is therefore built from
  `receipt.ordered_refs("block")`, which sorts by handle INDEX, with a comment
  saying why; `.values()` would hand the recovered call a different block table
  than the live call used, at ten or more handles. Same failure family as
  selfstudy `run-9175f0ec`; related: `DR-SEAM-rules-x-scratch`'s trap on the alias
  derivation, and `DR-SUB-scratch`'s.
`check: python -c "import hashlib;from deepreason.canonical import canonical_json;from deepreason.scratch.render import ScratchRenderReceiptV1 as R;h={'B%d'%i:'sha256:'+hashlib.sha256(str(i).encode()).hexdigest() for i in range(1,13)};r=R.create(state_seq=1,attention_receipt='sha256:'+'a'*64,block_handles=h,cluster_handles={},link_handles={},guide_handles={});q=R.model_validate_json(canonical_json(r.model_dump(mode='json',by_alias=True)));assert r.ordered_refs('block')==q.ordered_refs('block');assert list(q.alias_map('block').values())!=list(q.ordered_refs('block'))"`
- **The exposure receipt is the note's only durable link back to its
  transaction, and it lives in an untyped field.**
  `ScratchEventPayloadV1.context_ref` is an `OpaqueRef` because its referent
  changes with the controller generation: under v6 it is
  `authorized.exposure_receipt.id`, and on the legacy path it is the
  render-receipt blob id. Reading it as one or the other without checking the
  generation is how a reader concludes a v6 root has no advisory context.
- **Residue: `verify_root` does not re-prove the authoring join.** Replay
  validation pins the CONJECTURE advisory-context receipt to the scratch fence,
  the selection receipt and the render receipt, and it re-derives an expansion
  from the transaction lineage — but it has no rule pairing a `scratch_authoring`
  transaction's exposure receipt with the `context_ref` of the scratch effect it
  produced. That binding is enforced only in the live and recovery code paths.
  No recorded root has been shown to exploit the gap, and closing it would need a
  reader-side check that leaves every existing root valid; until then this entry
  is the record that the asymmetry is known and unclosed, not deliberate.
`check: ! grep -q "SCRATCH_AUTHORING\|scratch_authoring" src/deepreason/invariants.py && grep -q "^def verify_root" src/deepreason/invariants.py && grep -q "selection receipt names another scratch fence" src/deepreason/invariants.py && python -c 'from deepreason.workflow.models import WorkflowTaskKind as K;assert K.SCRATCH_AUTHORING.value == "scratch_authoring"'`
