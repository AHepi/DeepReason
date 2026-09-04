<!-- DR-SEAM-harness-x-workflow -->
Verified-at: 6f9b5614e
Verify: python tools/docs_verify.py
Owns: src/deepreason/harness.py, src/deepreason/workflow/replay.py, src/deepreason/control_events.py, src/deepreason/ontology/event.py
Sides: DR-SUB-harness, DR-SUB-workflow
Sweep: workflow_state && Rule\.CONTROL|record_control_transition|record_transaction_transition

# harness x workflow

## The agreement

The workflow layer owns process authority and holds none of it: every decision
it reaches becomes durable only as one `Rule.CONTROL` event appended by the
harness, and every consequence it later reads back is re-derived from that log
by `WorkflowReplayState`. The harness promises atomicity and re-derivation — the
immutable records land in `objects/` first, the event lands last, and a failure
anywhere in between resets the live view and re-replays the durable log, so
`harness.workflow_state` can never be ahead of `log.jsonl`. It also promises to
run the workflow materializer on *every* event, before the formal object loop,
and to translate the materializer's `ValueError` into `WellFormednessError`
before the append — which makes workflow's replay refusals write-time refusals
decided by the same code. In exchange the workflow layer promises that its
events are inert to the formal graph: the payload carries object references
only, a control event's `StateDiff` must be empty, and `workflow_state` lives
beside `state` rather than inside it, so nothing it records can move an
attack, a dependence, a warrant carriage or a status. It also promises never to
import the harness — every workflow module that needs one takes it as a
duck-typed argument — and never to write an object or append an event itself.
The one shared number is the harness's event sequence: work fences are minted
from `harness._next_seq`, and `WorkflowReplayState.digest`, the value sealed
into `workflow-checkpoint.json`, is a function of the seqs at which control
events landed.
`check: python -W ignore -c "import inspect,tempfile,pathlib,pytest;from deepreason.harness import Harness;from deepreason.ontology.event import Rule;from deepreason.control_events import ControlEventPayloadV3;c=inspect.getsource(Harness._commit);i=[c.index(x) for x in ('self.log.append(event)','except Exception:','self._reset()','for durable in self.log.read():','raise')];assert i==sorted(i),i;d=pathlib.Path(tempfile.mkdtemp())/'run';h=Harness(d);h.record_measure(inputs=['x']);o='sha256:'+'2'*64;p=ControlEventPayloadV3(action='work_transition',decision_ref=o,inputs=['sha256:'+'1'*64,'t'],outputs=[o]);pytest.raises(Exception,h._commit,Rule.CONTROL,inputs=list(p.inputs),outputs=list(p.outputs),control=p);assert list(h.workflow_state.event_inputs_by_seq)==[0],h.workflow_state.event_inputs_by_seq;assert len(list(h.log.read()))==1 and h._next_seq==1"`

SIXTY files under `src/deepreason` name both sides — fifty-nine until
2026-08-30, when `aftercycle.py` joined the census by NAMING the six deciding
packages (`workflow` and `workflows` among them) in a docstring. It imports
nothing from either side, which is worth stating because this census counts
WORD MENTIONS and the two clauses after it count edges: a file can join this
number without adding a single dependency, and this one did. Eight call a
Control-minting seam. Four — this document's `Owns:` set — carry the agreement,
and the dependency arrow between the two packages is absolute in one direction:
no module under `workflow/` names
`deepreason.harness` at all, while `harness.py` names four workflow modules,
always inside a function body. That deferral is not isolation — `storage/
objects.py` imports `workflow.models` at module scope to register the schemas,
so importing the harness loads the workflow package anyway.
`check: python -c "import re,pathlib;t=pathlib.Path('src/deepreason/harness.py').read_text();assert not re.search(r'^(from|import) deepreason\.workflow',t,re.M);assert sorted(set(re.findall(r'from deepreason\.workflow\.(\w+) import',t)))==['criticism','models','replay','transaction']" && python -c "import sys,importlib;importlib.import_module('deepreason.workflow.replay');assert 'deepreason.harness' not in sys.modules" && python -c "import sys,importlib;importlib.import_module('deepreason.harness');assert 'deepreason.workflow.models' in sys.modules" && grep -q "^from deepreason.workflow.models import" src/deepreason/storage/objects.py && ! grep -rq "deepreason\.harness" --include=*.py src/deepreason/workflow/ && grep -q "self.harness.record_transaction_transition(" src/deepreason/workflow/transaction_service.py && test "$(for f in $(grep -rl harness --include=*.py src/deepreason); do grep -ql workflow "$f" && echo x; done | wc -l)" -eq 61 && test "$(grep -rlE "record_control_transition|record_transaction_transition|record_lifecycle_transition|record_resume_transition|record_terminal_commitment|bind_transaction_manifest" --include=*.py src/deepreason | wc -l)" -eq 8`

The action vocabulary is closed and covered in both directions: each of the
eight `ControlEventPayloadV3` actions is minted by a harness seam and dispatched
by `WorkflowReplayState.apply`, each of the six `WorkTransitionKind` members is
named by the transaction seam's record-shape table, and every seam writes its
objects before it commits.
`check: python -c "import inspect,typing;from deepreason.control_events import ControlEventPayloadV3 as C;from deepreason.workflow.replay import WorkflowReplayState as S;from deepreason.workflow.transaction import WorkTransitionKind as K;from deepreason.harness import Harness;acts=set(typing.get_args(C.model_fields['action'].annotation));assert len(acts)==8,acts;a=inspect.getsource(S.apply);seams={n:inspect.getsource(getattr(Harness,n)) for n in ('record_control_transition','record_transaction_transition','record_lifecycle_transition','record_resume_transition','record_terminal_commitment','bind_model_classification','activate_contract_decomposition','complete_contract_decomposition')};h=''.join(seams.values());assert not [x for x in acts if '\"'+x+'\"' not in a or '\"'+x+'\"' not in h];assert not [k.name for k in K if 'WorkTransitionKind.'+k.name not in seams['record_transaction_transition']];assert not [n for n,s in seams.items() if 'self._ensure_writable()' not in s or 'Rule.CONTROL' not in s or s.index('self.objects.put(')>s.index('self._commit(')]"`

The envelope carries references and nothing else — three payload classes, four
(five for v3) fields each, the decision reference always the final output — and
`Event` re-checks the pairing, mirrors inputs and outputs, forbids a non-empty
formal `StateDiff`, and admits an `LLMCall` on exactly one action.
`check: python -c "import inspect,pytest;from deepreason.control_events import ControlEventPayloadV1 as A,ControlEventPayloadV2 as B,ControlEventPayloadV3 as C;from deepreason.ontology.event import Event,Rule,StateDiff,LLMCall;assert set(A.model_fields)==set(B.model_fields)=={'schema_','decision_ref','inputs','outputs'};assert set(C.model_fields)=={'schema_','action','decision_ref','inputs','outputs'};assert all('control decision_ref must be the final event output' in inspect.getsource(k) for k in (A,B,C));o='sha256:'+'0'*64;w='sha256:'+'1'*64;x='sha256:'+'2'*64;p=A(decision_ref=o,inputs=[w,'t'],outputs=[o]);q=C(action='provider_result',decision_ref=o,inputs=[w,'t'],outputs=[o]);call=LLMCall(role='conjecturer',model='m',endpoint='e',prompt_ref=w,raw_ref=x);ev=lambda **kw: Event(**({'seq':0,'ts':'2026-01-01T00:00:00+00:00','rule':Rule.CONTROL,'inputs':[w,'t'],'outputs':[o],'state_diff':StateDiff(),'control':p}|kw));ev();ev(control=q,llm=call);cases=[('Control rule and typed control payload must appear together',{'rule':Rule.MEASURE}),('Control rule and typed control payload must appear together',{'control':None}),('control payload inputs must match Event.inputs',{'inputs':[w,'other']}),('control payload outputs must match Event.outputs',{'outputs':[o,x]}),('process events cannot mutate formal StateDiff',{'state_diff':StateDiff(hv_set={'a':1.0})}),('control decisions cannot contain an LLM call',{'llm':call}),('control decisions cannot contain an LLM call',{'control':q})];assert all(m in str(pytest.raises(ValueError,ev,**k).value) for m,k in cases)" && python -c "import pathlib;t=pathlib.Path('src/deepreason/harness.py').read_text();assert '        if (llm is not None) != (\n            transition.transition_kind == WorkTransitionKind.PROVIDER_RESULT\n        ):\n            raise ValueError(\"only provider_result may carry an LLM call\")\n' in t;assert '        if payload.action == BridgeAction.WORKFLOW_RETRY_STARTED and llm is not None:\n            raise ValueError(\"workflow retry authorization cannot contain an LLM call\")\n' in t"`

`observe_event` runs before the control branch, the control branch runs before
the formal object loop, and the `ValueError`→`WellFormednessError` translation
sits between them. The behavioural consequence: a plain `Measure` event is
indexed by seq into `WorkflowReplayState` yet contributes no authority, and a
root with no control events digests to the frozen empty value that every
pre-controller root has always digested to.
`check: python -W ignore -c "import inspect,tempfile,pathlib;from deepreason.harness import Harness;from deepreason.workflow.replay import WorkflowReplayState as S;s=inspect.getsource(Harness._apply_event);i=[s.index(x) for x in ('self.workflow_state.observe_event(event)','if event.control is not None:','self.workflow_state.apply(event, resolved_workflow)','raise WellFormednessError(str(error)) from error','for oid in event.outputs:')];assert i==sorted(i),i;d=pathlib.Path(tempfile.mkdtemp())/'run';h=Harness(d);h.record_measure(inputs=['x']);w=h.workflow_state;assert w.event_inputs_by_seq=={0:('x',)} and w.event_outputs_by_seq=={0:()},w.event_inputs_by_seq;assert w.event_seqs==[] and not w.branches and not w.transaction_work;assert w.digest==S().digest=='sha256:80e4d37c0f6992a7a8e922341161cd1a269b4e22ac1f2c2db2f5394340448843',w.digest"`

## Where it is expressed

| Site | File | Symbol | What it enforces |
|---|---|---|---|
| The eight minting seams | `harness.py` | `record_control_transition`, `record_transaction_transition`, `record_lifecycle_transition`, `record_resume_transition`, `record_terminal_commitment`, `bind_model_classification`, `activate_contract_decomposition`, `complete_contract_decomposition` | every workflow record reaches the log as exactly one `Rule.CONTROL` event; objects first, append last |
| Record-shape refusals | `harness.py` | `record_control_transition`'s work-order/receipt/guard arms; `record_transaction_transition`'s `expected` table and `WORK_ISSUED`/`WORK_TERMINATED` arms | a transition whose records do not match its kind never reaches `_commit` |
| Work-item binding | `harness.py` | `record_transaction_transition`'s `work_id`/`attempt_index` equality | one append cannot mix records from two work items or two attempts |
| Envelope | `control_events.py` | `ControlEventPayloadV1/V2/V3._authority_references` | references only; canonical ids; no duplicate outputs; `decision_ref` is the last output |
| Rule/payload contract | `ontology/event.py` | `_process_payload_contract` | `Rule.CONTROL` ⇔ `control`; payload mirrors `Event.inputs`/`outputs`; empty formal `StateDiff`; `LLMCall` only on `provider_result` |
| Forged-payload reparse | `ontology/event.py` | `_deeply_revalidate_control_payload` | a preconstructed payload cannot skip nested validation on the live append and fail only on reopen |
| Materialization | `harness.py` | `_apply_event`: `observe_event` → `objects.get` loop → `workflow_state.apply` | replay input is `(event, resolved records)`; live and reopen use one path |
| Ordering | `harness.py` | process branch before `for oid in event.outputs:` | a refused control event cannot transiently register a formal artifact |
| Failure translation | `harness.py` | `except ValueError: raise WellFormednessError` | workflow's replay refusals are also write-time refusals — and open-time ones |
| Rollback | `harness.py` | `_commit`'s `except` → `_reset()` → re-replay | live `workflow_state` never outruns the durable log |
| State slot | `harness.py` | `_reset`'s `self.workflow_state = WorkflowReplayState()` | rebuilt from the log on every open, beside `state`, never inside it |
| Manifest binding | `harness.py`, `workflow/replay.py` | `bind_transaction_manifest` → `WorkflowReplayState.bind_run_manifest` | one root, one v6 manifest; a different digest raises on both halves |
| Auto-bind at open | `harness.py` | `_reset`'s `schema_version == 6` branch, after `_load_workflow_manifest` | a v6 root replays under manifest authority with no caller involved |
| Checkpoint seal | `harness.py` | `write_workflow_checkpoint` | `workflow_state.digest` + `max(event_seqs)` + outstanding ids, one atomic `os.replace` |
| Checkpoint verify | `harness.py` | `_verify_workflow_checkpoint` → `replay_workflow(self.log.read(upto_seq=checkpoint_seq), ...)` | the sealed *prefix* re-derives; a lost tail raises at open |
| Resume cross-check | `harness.py` | `record_resume_transition`'s checkpoint comparisons | a RESUMED decision must quote this root's `workflow-checkpoint.json` bytes and its generic `checkpoint.json` |
| Blob liveness | `harness.py` | `record_lifecycle_transition` and `_apply_event`'s `workflow-stop-metrics-observation` branch | a stop decision cannot name model-signal bytes the root does not hold |
| Object namespace | `storage/objects.py` | 26 `workflow-*` + 3 `criticism-*` schema rows | the schema string is the shared vocabulary: `objects.get` returns it, `apply` dispatches on it |
| Log clock | `harness.py`, callers | `_next_seq`, read as `fence = harness._next_seq - 1` | the work fence is a harness event seq the harness never validates |
| Cross-read | `harness.py` | `bridge_state.apply_v6_provider_result(event, self.workflow_state)` | the bridge reads workflow authority through the harness, inside the same apply |
| Downstream binding | `invariants.py` | `workflow-replay` finding; `stats["workflow_process_digest"]` | two replays of one root must reach one process digest (`DR-SEAM-harness-x-verification`) |
| Open-time terminal storage | `runtime/terminal_authority.py` | `validate_terminal_commitment_storage(self.root, self.workflow_state)`, called from `Harness.__init__` only when `terminal_commitments_by_epoch` is non-empty | a latched terminal commitment whose local stop object is missing or disagrees makes the root unopenable, before `_verify_workflow_checkpoint` runs |

The last row is the one the seam did not name until the `--coverage` sweep found
it: it is the only workflow authority the harness re-validates against files
outside `log.jsonl`/`objects/`, and it raises typed `TERMINAL_*` codes rather
than the seam's usual `WellFormednessError`.
`check: python -c "import inspect;from deepreason.harness import Harness;from deepreason.runtime.terminal_authority import validate_terminal_commitment_storage as v;s=inspect.getsource(Harness.__init__);assert 'self.workflow_state.terminal_commitments_by_epoch' in s and 'validate_terminal_commitment_storage(' in s;assert s.index('validate_terminal_commitment_storage(\n')<s.index('self._verify_workflow_checkpoint()');assert list(inspect.signature(v).parameters)==['root','workflow_state'];b=inspect.getsource(v);assert 'workflow_state.terminal_commitments_by_epoch' in b and 'TERMINAL_STOP_OBJECT_REQUIRED' in b and 'TERMINAL_STOP_OBJECT_MISMATCH' in b"`

The digest the checkpoint seals is a function of harness sequence numbers, at
both branch and transaction level; inserting an unrelated event between two
control events moves it.
`check: python -c "from deepreason.workflow.replay import WorkflowReplayState as S,WorkflowBranchState,TransactionReplayItem;from deepreason.workflow.state import WorkflowProcessStateV1 as P;p=P(manifest_digest='0'*64,workflow_profile='inquiry.active.v1',formal_fence_seq=0,scratch_fence_seq=0);s=S();s.branches['b']=WorkflowBranchState(branch_id='b',process_state=p);d=[s.digest];s.branches['b'].event_seqs.append(3);d.append(s.digest);s.branches['b'].event_seqs[:]=[4];d.append(s.digest);s.transaction_work['w']=TransactionReplayItem(preparation=None);d.append(s.digest);s.transaction_work['w'].event_seqs.append(5);d.append(s.digest);s.transaction_work['w'].event_seqs[:]=[6];d.append(s.digest);assert len(set(d))==6,d" && grep -q "self.event_seqs.append(seq)" src/deepreason/workflow/replay.py && grep -q "branch.event_seqs.append(seq)" src/deepreason/workflow/replay.py && grep -q "item.event_seqs.append(seq)" src/deepreason/workflow/replay.py`

The checkpoint seals the process digest, replaces atomically, re-derives the
sealed prefix rather than the tip, and raises on a lost tail — and a root that
has recorded no control authority has no checkpoint file at all.
`check: python -W ignore -c "import inspect,tempfile,pathlib;from deepreason.harness import Harness;w=inspect.getsource(Harness.write_workflow_checkpoint);v=inspect.getsource(Harness._verify_workflow_checkpoint);assert '\"process_digest\": self.workflow_state.digest,' in w and 'os.replace(temporary, target)' in w;assert 'self.log.read(upto_seq=checkpoint_seq)' in v and 'process_digest != checkpoint_state.digest' in v and 'workflow authority log lost its checkpointed tail' in v;assert v.count('checkpoint_state =')==1 and 'self.workflow_state.digest' not in v;d=pathlib.Path(tempfile.mkdtemp())/'run';h=Harness(d);h.record_measure(inputs=['x']);assert h.write_workflow_checkpoint() is None and not (d/'workflow-checkpoint.json').exists() and h.workflow_checkpoint_digest() is None;Harness(d)" && python -m pytest "tests/test_workflow_control_replay_c1.py::test_checkpoint_detects_deleted_final_authority_event" "tests/test_workflow_control_replay_c1.py::test_checkpoint_verifies_its_prefix_when_newer_controls_exist" -q`

The manifest is loaded before `_reset`, re-bound by `_reset` (which never
reassigns `_workflow_manifest`, so a rollback keeps live authority), and refused
on both halves if it differs from what is already bound.
`check: python -W ignore -c "import inspect,tempfile,pathlib,pytest;from types import SimpleNamespace;from deepreason.harness import Harness;from deepreason.workflow.replay import WorkflowReplayState as S;i=inspect.getsource(Harness.__init__);r=inspect.getsource(Harness._reset);assert i.index('self._workflow_manifest = self._load_workflow_manifest()')<i.index('self._reset()');assert 'self._workflow_manifest =' not in r;assert 'self._workflow_manifest.schema_version == 6' in r and 'self.workflow_state.bind_run_manifest(self._workflow_manifest)' in r;m1=SimpleNamespace(sha256='sha256:'+'a'*64,schema_version=6);m2=SimpleNamespace(sha256='sha256:'+'b'*64,schema_version=6);d=pathlib.Path(tempfile.mkdtemp())/'run';h=Harness(d);h.bind_transaction_manifest(m1);assert 'transaction manifest differs from bound root authority' in str(pytest.raises(ValueError,h.bind_transaction_manifest,m2).value);s=S();s.bind_run_manifest(m1);assert 'workflow replay is already bound to another manifest' in str(pytest.raises(ValueError,s.bind_run_manifest,m2).value)"`

## What is deliberately absent

**The harness never validates a work fence.** `formal_fence_seq` and
`scratch_fence_seq` do not appear anywhere in `harness.py`, even though both are
copies of `harness._next_seq - 1` minted by third parties (`scheduler.py`,
`rules/conj.py`, `rules/crit.py`, `bridge/`). The harness hands out the number
and forgets it; the workflow layer is the only side that re-checks it — that the
two fences are equal, that the work order's fence matches its branch's process
state, and that a `work_enabled` decision begins at the digest its declared
fence implies. Moving that check into the harness would put a v6-shaped
constraint in the frozen materializer and would fire on pre-v6 roots that never
carried one.
`check: python -c "import pathlib;t=pathlib.Path('src/deepreason/harness.py').read_text();assert 'formal_fence_seq' not in t and 'scratch_fence_seq' not in t" && grep -q 'raise ValueError("work-enabled decision does not begin at its declared fence")' src/deepreason/workflow/replay.py && grep -q "state.formal_fence_seq != work.formal_fence_seq" src/deepreason/workflow/replay.py && grep -q 'raise ValueError("transactional work requires one immutable state fence")' src/deepreason/workflow/transaction.py && grep -q "fence = self.harness._next_seq - 1" src/deepreason/scheduler/scheduler.py && grep -q "default_fence = max(0, harness._next_seq - 1)" src/deepreason/rules/conj.py`

**Control events do not adjudicate and do not age the run.** `_adjudicate`
mentions neither workflow nor control; `EpistemicState` has no workflow field;
and `_advance_semantic_event_clock` adds every `Rule.CONTROL` seq to the
exclusion set, so a run that appends fifty transaction receipts has taken zero
semantic actions. This is what stops C1/v6 instrumentation from accelerating
stop policy, ageing, or capture windows — a run's process chatter must not be
able to end it.
`check: python -W ignore -c "import inspect,tempfile,pathlib;from deepreason.harness import Harness;from deepreason.ontology.state import EpistemicState as E;from deepreason.ontology.event import Event,Rule,StateDiff;from deepreason.control_events import ControlEventPayloadV1 as P;a=inspect.getsource(Harness._adjudicate);assert 'workflow' not in a and 'ontrol' not in a;assert not [f for f in E.model_fields if 'workflow' in f];d=pathlib.Path(tempfile.mkdtemp())/'run';h=Harness(d);h.record_measure(inputs=['a']);h.record_measure(inputs=['b']);b=h.semantic_event_clock();o='sha256:'+'0'*64;p=P(decision_ref=o,inputs=['sha256:'+'1'*64,'t'],outputs=[o]);e=Event(seq=2,ts='2026-01-01T00:00:00+00:00',rule=Rule.CONTROL,inputs=list(p.inputs),outputs=list(p.outputs),state_diff=StateDiff(),control=p);h._advance_semantic_event_clock(e);h._next_seq=3;assert b==2 and h.semantic_event_clock()==2,(b,h.semantic_event_clock())"`

**The workflow layer writes no object and appends no event.** There is no
`objects.put(` and no `log.append(` anywhere under `workflow/`; the controllers
call `harness.record_control_transition` / `record_transaction_transition` and
let the harness decide the event shape. What they *may* do is `blobs.put` —
opaque bytes (prompts, raw provider output, canonical semantic payloads) are
theirs to store, because a blob asserts nothing until a record names it. The
asymmetry is deliberate: a workflow bug can leave orphaned bytes, never an
unauthorized event. `criticism-*` obligations are the visible edge of this — they
ride `Rule.MEASURE`, not `Rule.CONTROL`, and the string `criticism` appears zero
times in `workflow/replay.py`, so coverage debt is durable evidence that is
invisible to `WorkflowReplayState` and to its digest.
`check: ! grep -rqE "objects\.put\(|log\.append\(" --include=*.py src/deepreason/workflow/ && grep -rq "harness\.blobs\.put(" --include=*.py src/deepreason/workflow/ && grep -q "self.harness.record_control_transition(" src/deepreason/workflow/trace.py && python -c "import inspect;from deepreason.harness import Harness;s=inspect.getsource(Harness.record_criticism_obligation);assert 'Rule.MEASURE' in s and 'Rule.CONTROL' not in s and 'control=' not in s" && grep -q "class WorkflowReplayState" src/deepreason/workflow/replay.py && ! grep -q "criticism" src/deepreason/workflow/replay.py`

**There is no schema the harness does not name.** All 29 registered
`workflow-*`/`criticism-*` schemas appear as literals in `harness.py`, because
the seam that mints an event is the same place the schema string is chosen; the
object store is the registry, not the authority. The consequence for a reader is
the inverse: a `workflow-` literal in `harness.py` is *not* necessarily a schema.
Exactly one is not — `"workflow-conjecture-call"`, an event-input marker written
by `rules/conj.py` and read by the semantic clock and by `invariants.py`.
`check: python -c "import re,pathlib;from deepreason.storage.objects import SCHEMAS;t=pathlib.Path('src/deepreason/harness.py').read_text();named=set(re.findall(r'\"((?:workflow|criticism)-[a-z0-9-]+)\"',t));reg={k for k in SCHEMAS if k.startswith(('workflow-','criticism-'))};assert len(reg)==29,len(reg);assert reg<=named,sorted(reg-named);assert named-reg=={'workflow-conjecture-call'},sorted(named-reg)"`

**`replay_workflow` has no blob store, so the checkpoint verifies authority and
not evidence.** Its parameters are `(events, objects, manifest)` and its body
never touches a blob, while the harness's own `_apply_event` fetches every
`model_signal_blob_refs` entry of a `workflow-stop-metrics-observation`. Missing
signal bytes are therefore caught by the full open replay and *not* by
`_verify_workflow_checkpoint`. Handing `replay_workflow` a blob store to "make it
consistent" would give the prefix check a second, differently-shaped failure mode
on roots the full open already covers.
`check: python -c "import inspect;from deepreason.workflow.replay import replay_workflow;from deepreason.harness import Harness;s=inspect.getsource(replay_workflow);assert 'blob' not in s and list(inspect.signature(replay_workflow).parameters)==['events','objects','manifest'];a=inspect.getsource(Harness._apply_event);assert 'workflow-stop-metrics-observation' in a and 'self.blobs.get(ref)' in a" && grep -q "for ref in observation.model_signal_blob_refs:" src/deepreason/harness.py`

**No workflow state is reachable from the formal graph, in either direction.**
`workflow_state` is rebuilt in `_reset` beside `state`, and `_adjudicate` reads
only `artifacts`, `warrants`, `commitments` and `carries`. There is no code path
by which a work order, a reservation or a terminal changes an `att` edge — which
is why a run whose control plane is entirely broken still has a well-formed
epistemic graph, and why `verify_root` reports `replay` and `workflow-replay` as
separate findings. Checked by the adjudication half of the ageing check above.

## How to change it

The order is forced by which side is frozen: `harness.py`'s event application is
a frozen surface (`DR-INV-frozen-surfaces`, surface 2), and
`WorkflowReplayState.digest` is append-only in the subtler sense described in
`DR-SUB-workflow`'s traps. Reader before writer, always.

1. **Decide whether a new record needs a new action at all.** Most changes are a
   new record type inside an existing action: a class in `workflow/
   transaction.py`, a schema row in `storage/objects.py`, an `apply` branch in
   `workflow/replay.py`, then a `schema_by_type` entry and a record-shape arm in
   `record_transaction_transition`. No `control_events.py` change, no new
   `Event` shape, no risk to historical roots.
2. **A genuinely new action moves in this order:** the `action` Literal in
   `ControlEventPayloadV3` (and its output-count table) → the dispatch branch in
   `WorkflowReplayState.apply` → the schema rows → the harness seam that mints
   it. Doing the seam first produces an event that the same process cannot
   replay: `apply` falls through to `"controller-v3 action differs from its
   decision record"`, `_apply_event` converts it, and `_commit` rolls back — a
   confusing failure that looks like a record bug.
3. **Anything new in `WorkflowReplayState.digest` appears only when non-empty.**
   An unconditional key — even an empty default — changes the digest of every
   root written before the feature existed, which changes the process digest
   sealed in their checkpoints and the `workflow_process_digest` in every stored
   verdict. `DR-INV-frozen-surfaces` rules this out by definition.
4. **New authority state must be reconstructible from the log alone.**
   `_commit`'s failure path calls `_reset()` and re-replays; anything in
   `WorkflowReplayState` that cannot be rebuilt that way survives a failed append
   in memory and not on disk.
5. **Never let the harness decide anything about workflow semantics.** It
   imports four workflow modules and none of them is a controller, a service, a
   reducer, a trace or a shadow observer. It may refuse a *shape*; it must not
   compute a decision. Widening the import set is the signal that a change is on
   the wrong side of the seam.
6. **A change that makes an existing root unopenable is wrong by definition.**
   Workflow refusals raise through `_apply_event` during the `__init__` replay,
   so a tightened `apply` rule does not produce a finding — it produces a root
   nobody can open, and `verify_root` collapses to one `open` finding with empty
   `stats` (`DR-SEAM-harness-x-verification`).

What breaks first, in the order you will meet it: `Event`'s model validators
(instant, pure); then the harness seam's record-shape `ValueError`s; then
`WorkflowReplayState.apply`, surfacing as `WellFormednessError` with the log
unadvanced; then `_verify_workflow_checkpoint` at the next open
(`"workflow checkpoint differs from replayed authority"`); then `verify_root`'s
`workflow-replay` divergence; then the 42-root sweep, which is the expensive one
because by then the root is committed.

The tests that catch you, cheapest first:
`tests/test_workflow_control_event_storage_c1.py` (the envelope, sub-second),
`tests/test_workflow_control_replay_c1.py` (rollback, checkpoint, capture
windows), `tests/test_workflow_control_recovery_mutation_c1.py` (tampered logs
must fail closed on reopen), then
`tests/test_workflow_stop_lifecycle_c4.py` and
`tests/test_workflow_resume_lifecycle_c4.py`, then
`tests/test_v6_controller3_replay_verification.py` (~28 s) and
`tests/test_replay.py` with `tests/test_persistence_invariants.py`.
`check: grep -q "if second.workflow_state.digest != h.workflow_state.digest:" src/deepreason/invariants.py && grep -q 'fail("workflow-replay"' src/deepreason/invariants.py && python -m pytest tests/test_workflow_control_replay_c1.py tests/test_workflow_control_recovery_mutation_c1.py tests/test_workflow_control_event_storage_c1.py -q`

## Traps

- **Three different things are called a checkpoint digest.**
  `Harness.workflow_checkpoint_digest()` is the sha256 of the
  `workflow-checkpoint.json` *file bytes*; `payload["process_digest"]` inside
  that file is `workflow_state.digest`; and
  `WorkflowReplayState.terminal_checkpoint_digest` returns
  `decision.checkpoint_ref`, which is the *object id of the lifecycle snapshot*
  and not a digest of anything on disk. `record_resume_transition` compares the
  first; `WorkflowLifecycleSnapshotV1.process_digest` carries the second. Picking
  the wrong one produces a comparison that passes for the wrong reason.
`check: python -c "import inspect;from deepreason.workflow.replay import WorkflowReplayState as S;from deepreason.harness import Harness;a=inspect.getsource(S.terminal_checkpoint_digest.fget);b=inspect.getsource(S.terminal_process_digest.fget);c=inspect.getsource(Harness.workflow_checkpoint_digest);assert 'return decision.checkpoint_ref' in a,a;assert 'return snapshot.process_digest' in b,b;assert 'return sha256_hex(data)' in c" && grep -q "decision.checkpoint_ref != snapshot.id" src/deepreason/harness.py && grep -q "workflow_checkpoint_digest != decision.workflow_checkpoint_digest" src/deepreason/harness.py`
- **Four independent layers once assumed zero drift between a typed stop and its
  resume, and a bridged run could not be continued.** In
  `experiments/live_research_2026-07-29/narrow/runs/run-7d8723fbe8626c71db880826c244d332`
  the continuation fence, the resume-lifecycle builder, the resume-decision model
  and the harness's generic-checkpoint cross-check each demanded that
  `checkpoint.json`'s `event_seq` equal the resume seq — which a composed bridge,
  legitimately appending post-terminal events, always violates. The harness half
  now admits drift in one direction only (`checkpoint_seq > resume_event_seq` is
  still fatal) and the current terminal authority must validate the entire
  post-horizon tail. When you add a fifth place that compares a stop fence to a
  resume fence, it needs the same asymmetry, or bridged runs silently become
  un-continuable again.
`check: grep -q "or checkpoint_seq > decision.resume_event_seq" src/deepreason/harness.py && grep -q "The checkpoint records the stop fence; a bridged run resumes" src/deepreason/harness.py && grep -q "sha256_hex(run_checkpoint_bytes) != decision.run_checkpoint_digest" src/deepreason/harness.py && test -d experiments/live_research_2026-07-29/narrow/runs/run-7d8723fbe8626c71db880826c244d332 && python -m pytest tests/test_workflow_resume_lifecycle_c4.py -q`
- **`bind_transaction_manifest` is not one transaction across the seam.** The
  harness assigns `self._workflow_manifest` *before* delegating, and
  `WorkflowReplayState.bind_run_manifest` restores its own previous value on any
  failure. A refused bind therefore leaves the two halves disagreeing: the replay
  state is unbound and the harness holds the manifest it just rejected. Reachable
  today with a non-v6 manifest, shown by the check below. **Residue: no live run
  has been observed to reach it** — every production caller
  (`llm/adapter.bind_v6_authority`, `InquiryTransactionService`, and the harness's
  own decomposition seams) is already inside a v6 path, and the sha256 guard fires
  first whenever the root has a manifest file. Treat the check as a
  characterisation of current behaviour, not as an endorsement of it.
`check: python -W ignore -c "import tempfile,pathlib,pytest;from types import SimpleNamespace;from deepreason.harness import Harness;d=pathlib.Path(tempfile.mkdtemp())/'run';h=Harness(d);f=SimpleNamespace(sha256='sha256:'+'a'*64,schema_version=5);pytest.raises(ValueError,h.bind_transaction_manifest,f);assert h.workflow_state._run_manifest is None and h._workflow_manifest is f"`
- **Verifying only the latest process digest is not verifying the checkpoint.**
  `_verify_workflow_checkpoint` replays the log *up to* `last_control_seq` and
  compares that prefix, because comparing current state against the sealed value
  would let a tampered transition be masked by appending an unrelated later one.
  The comment in the method says so. A "faster" equality against
  `self.workflow_state.digest` passes every honest root and defeats the purpose.
  Do not trust the test named for it:
  `test_checkpoint_verifies_its_prefix_when_newer_controls_exist` tampers with an
  event *inside* the sealed prefix, which moves the tip digest as well, so it
  passes under either implementation. Falsified 2026-08-02 by rewriting
  `checkpoint_state` to `self.workflow_state` after the replay — 45 ring tests
  green. What pins the property now is the structural clause in the checkpoint
  check above (`checkpoint_state` assigned exactly once, `self.workflow_state.
  digest` never read in the method).
- **`WorkflowReplayState.digest` cannot see a failed append, so a digest-only
  rollback test proves nothing.** `observe_event` writes `event_inputs_by_seq` /
  `event_outputs_by_seq`, and neither feeds the digest. Delete `_commit`'s
  `_reset()` and `test_failed_control_append_rolls_live_materialization_back`
  still passes: its refusal is a record-shape `ValueError` raised *before*
  `_commit`, and it asserts only the digest and an empty log. Falsified
  2026-08-02 — a refusal raised inside `_apply_event` (a duplicate transition
  decision) leaves seq 1 indexed against a one-row log. The agreement's check
  above now drives the refusal through `_commit` and asserts the seq index, not
  the digest.
- **Process-only outputs are materialized before the formal object loop on
  purpose.** The comment in `_apply_event` records why: otherwise a corrupt
  process event could transiently register a formal artifact and lean on
  `model_copy` to slip past `Event`'s `StateDiff` validator. Reordering the block
  for readability re-opens that hole, and no happy-path test notices.
- **A tampered control record makes the root unopenable, not invalid.** Deleting
  or altering a `Rule.CONTROL` line makes `Harness(root, read_only=True)` raise
  `WellFormednessError` during replay — you do not get a report listing what is
  wrong. Diagnose from `log.jsonl` and `objects/` directly, and never open a
  suspect root writable: the writable path repairs a torn tail in place
  (`DR-SEAM-harness-x-verification`).
- **Two live harnesses on one root make the workflow view silently stale.**
  Authority read before a contender takes the process lock is pre-lock authority;
  `reload_durable_authority` exists to discard the whole view — `workflow_state`
  included — inside the critical section. Reading `harness.workflow_state`
  outside the lock and acting on it afterwards is the shape of the bug.
