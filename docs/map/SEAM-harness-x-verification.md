<!-- DR-SEAM-harness-x-verification -->
Verified-at: df0fd0fd
Verify: python tools/docs_verify.py
Owns: src/deepreason/harness.py, src/deepreason/invariants.py, src/deepreason/log/event_log.py, src/deepreason/storage/blobs.py
Sides: DR-SUB-harness, DR-SUB-verification

# harness x verification

## The agreement

The harness promises that everything a run knows is reconstructible from
`log.jsonl` and the two content-addressed stores, and that the live session and
a later reopen reach that state through one function — `_apply_event` — so the
record is not a diary written alongside the state but the thing the state is
made of. Verification promises, in exchange, never to touch what it judges: it
opens the root read-only, repairs nothing, writes nothing, and converts every
kind of damage into a typed finding rather than into a fix. Neither side owns a
second implementation of the other's work. `verify_root` does not re-derive
epistemic state with independent code; it re-runs the harness twice, compares
the two materializations, and then checks that the graph the harness produced is
internally well-formed and that every durable projection beside the log agrees
with a fresh replay of the log. The verdict is a function of the root's bytes
and one integer (`meter_total`), which is why two verifications of one root at
two times are comparable at all. Both surfaces are frozen
(`DR-INV-frozen-surfaces`): the asymmetry that governs every change here is that
READERS may be fixed and FORMATS may not, because a committed root is evidence
and evidence whose meaning moves with the code is not evidence.

`verify_root` opens the root only read-only, and takes no configuration beyond
the meter total.
`check: python -c "import ast,pathlib,inspect;import deepreason.harness as H;import deepreason.log.event_log as L;from deepreason.invariants import verify_root;t=pathlib.Path('src/deepreason/invariants.py').read_text();c=[n for n in ast.walk(ast.parse(t)) if isinstance(n,ast.Call) and getattr(n.func,'id',getattr(n.func,'attr',None)) in ('Harness','EventLog')];assert len(c)>=4 and all(any(k.arg=='read_only' and getattr(k.value,'value',None) is True for k in n.keywords) for n in c),[ast.unparse(n) for n in c];assert list(inspect.signature(verify_root).parameters)==['root','meter_total'];o=[];oh=H.Harness.__init__;ol=L.EventLog.__init__;H.Harness.__init__=lambda s,*a,**k:(oh(s,*a,**k),o.append(s._read_only))[0];L.EventLog.__init__=lambda s,*a,**k:(ol(s,*a,**k),o.append(s.read_only))[0];verify_root(pathlib.Path('experiments/2026-08-02-stress-triplet/home-orbit/runs/run-6472629dbc5d408a733d472040671752'));H.Harness.__init__=oh;L.EventLog.__init__=ol;assert len(o)>=19 and all(o),o"`

The dependency arrow points one way only: the verifier imports the writer, and
importing the writer pulls in no verifier. The one place the arrow appears to
reverse — `Harness.__init__` calling `validate_terminal_commitment_storage`,
which lives in the module that later calls `verify_root` — is broken by
function-local imports on both hops.
`check: grep -q "^class Harness:" src/deepreason/harness.py && grep -q "^def verify_root(" src/deepreason/invariants.py && ! grep -qE "deepreason\.(invariants|verification)|from \.+(invariants|verification)" src/deepreason/harness.py && python -c "import sys,deepreason.harness;assert not [m for m in ('deepreason.invariants','deepreason.verification.report') if m in sys.modules];import deepreason.invariants;assert 'deepreason.harness' in sys.modules"`

Every state family the harness rebuilds in `_reset` has its own determinism
finding name, and the correspondence is exact in both directions.
`check: python -c "import ast,re,pathlib,inspect;from deepreason.harness import Harness;T=ast.parse(pathlib.Path('src/deepreason/invariants.py').read_text());want={'replay':'state','scratch-replay':'scratch_state','bridge-replay':'bridge_state','workflow-replay':'workflow_state','capability-replay':'capability_state'};got={k:ast.unparse(n.test) for n in ast.walk(T) if isinstance(n,ast.If) for s in n.body for k in want if ('fail('+chr(39)+k+chr(39)) in ast.unparse(s)};assert set(got)==set(want),sorted(got);assert all(('second.'+want[k]) in v and ('h.'+want[k]) in v for k,v in got.items()),got;s=set(re.findall(r'self\.(\w+_state) = ',inspect.getsource(Harness._reset)));assert s=={'scratch_state','bridge_state','workflow_state','capability_state'},s"`

The finding vocabulary is closed: of the 218 `fail(` sites in `invariants.py`,
exactly one passes a non-literal name — `fail(str(item["check"]), ...)`, which
forwards the `_controller_v3_history` findings — and every name that pass can
forward is a string literal some `fail(` already minted (`school-route`,
`workflow-call-pairing`, `workflow-decision`). Only `detail` is free text.
`check: python -c "import ast,pathlib;T=ast.parse(pathlib.Path('src/deepreason/invariants.py').read_text());C=lambda nm:[n for n in ast.walk(T) if isinstance(n,ast.Call) and getattr(n.func,'id',None)==nm];lit=lambda n:bool(n.args) and isinstance(n.args[0],ast.Constant) and isinstance(n.args[0].value,str);f=C('fail');g=C('finding');assert len(f)==218,len(f);assert len([n for n in f if not lit(n)])==1,[ast.unparse(n) for n in f if not lit(n)];assert len(g)>15 and all(map(lit,g)),[ast.unparse(n) for n in g if not lit(n)];assert {n.args[0].value for n in g}<={n.args[0].value for n in f if lit(n)}"`

`StateDiff` carries two different kinds of thing, and only one is replay input.
`hv_set`, `reach_set`, `addr+` and `carry+` are read back and applied;
`status_changed` is read back only by the incremental transition program;
`att+`, `dep+`, `A+` and `Π+` are written for the record and never read again,
because adjudication recomputes them.
`check: python -c "import ast,pathlib;from deepreason.ontology.event import StateDiff;F=set(StateDiff.model_fields);T=ast.parse(pathlib.Path('src/deepreason/harness.py').read_text());I={id(x) for n in ast.walk(T) if isinstance(n,ast.Call) and getattr(n.func,'id',None)=='StateDiff' for x in ast.walk(n)};r={n.attr for n in ast.walk(T) if isinstance(n,ast.Attribute) and n.attr in F and id(n) not in I};assert r=={'status_changed','hv_set','reach_set','addr_add','carry_add'},r;assert {'att_add','dep_add','a_add','pi_add'}<=F,F"`

## Where it is expressed

| Site | File | Symbol | What it enforces |
|---|---|---|---|
| One application path | `harness.py` | `_apply_event`, reached from `_commit` and from the `__init__` replay loop | live materialization and replay cannot diverge by construction |
| Adjudicate once | `harness.py` | `__init__`'s `_apply_event(event, adjudicate=False)` then `_adjudicate()` | the fixpoint is a pure function of the final graph; new state needing per-event recompute cannot ride on it |
| Rollback on failed append | `harness.py` | `_commit`'s `except` → `_reset()` → re-replay durable log | the in-memory view never outruns the log, which is what makes re-derivation admissible |
| Read-only opens | `invariants.py` | every `Harness(root, read_only=True)` in `verify_root`; `Harness.at` for the prefix probe | validation observes the evidence and never opens a writable view of it |
| Repair asymmetry | `log/event_log.py` | `EventLog.__init__`'s `if not read_only: self._repair_torn_tail()` | a torn final line is a repair on the writer's path and a finding on the verifier's |
| Holdout fence | `harness.py`, `storage/blobs.py` | `if self._read_only: self.blobs = FencedBlobStore(...)`, `historical_sealed_refs` | no read-only reader, verification included, sees holdout bytes no `Reveal` released |
| Replay determinism | `invariants.py` | two `Harness` opens → `replay`, `scratch-replay`, `bridge-replay`, `workflow-replay`, `capability-replay` | one log materializes to one state, five families deep |
| Incremental vs fresh | `invariants.py`, `harness.py` | `h.transitions() != Harness(root, read_only=True).transitions()` | the transition program is a function of the log, not of the instance; the only place a stored root gets per-event adjudication |
| Prefix openability | `invariants.py` | `Harness.at(root, seq)` at five quantile seqs | a truncated replay of a stored root still opens |
| Graph well-formedness | `invariants.py` | `warrant-validity`, `warrant-target`, `carry-carrier`, `carry-warrant`, `att-endpoints`, `dep-dag`, `addr`, `status-domain` | every reference the materialized state holds resolves inside that same state |
| Event stream shape | `log/event_log.py`, `invariants.py` | `validate_seq` → `EventSequenceError`; `seq-stream` | seqs consecutive from 0, enforced at the reader and re-asserted by the verifier |
| Sealed authority prefix | `harness.py` | `write_workflow_checkpoint`, `_verify_workflow_checkpoint` on every full open | a lost log tail is detected at open; verification inherits the raise |
| Terminal storage | `runtime/terminal_authority.py` | `validate_terminal_commitment_storage`, called from `Harness.__init__` | a latched commitment without its immutable stop object makes the root unopenable |
| Digests crossing out | `invariants.py` | `stats["workflow_process_digest"]`, `stats["capability_process_digest"]` from `h.workflow_state.digest` / `h.capability_state.digest` | the verdict carries the harness's own content addresses so a caller can bind them |
| The binding record | `runtime/terminal_authority.py` | `_fresh_replay_validation` — one read-only `Harness` plus one `verify_root` in a single `replay-validation.v1` payload | `REPLAY_VALIDATION.json` names both the re-derived digests and the verdict |
| Cycle break, both hops | `harness.py`, `runtime/terminal_authority.py` | function-local `from deepreason.runtime.terminal_authority import ...` and `from deepreason.invariants import verify_root` | importing the writer never imports the verifier |
| Legacy reader tolerance | `ontology/event.py`, `invariants.py` | `LLMCall.attempt_trace` default; the `elif manifest is not None:` gate; `_legacy_bridge_failure_call_seqs` | pre-manifest roots stay readable while manifest-bound roots must substantiate every call |

The binding record and the digests it quotes come from the harness's own replay
states, not from a recomputation.
`check: grep -q '"workflow_process_digest": h.workflow_state.digest' src/deepreason/invariants.py && grep -q '"capability_process_digest": h.capability_state.digest' src/deepreason/invariants.py && grep -q "replayed = Harness(root, read_only=True)" src/deepreason/runtime/terminal_authority.py && python -W ignore -c "import ast,pathlib;from deepreason.harness import Harness;from deepreason.invariants import verify_root;from deepreason.runtime.terminal_authority import _fresh_replay_validation;q=chr(39);T=ast.parse(pathlib.Path('src/deepreason/runtime/terminal_authority.py').read_text());F=[n for n in ast.walk(T) if isinstance(n,ast.FunctionDef) and n.name=='_fresh_replay_validation'][0];R=[n for n in ast.walk(F) if isinstance(n,ast.Return)];assert len(R)==1 and isinstance(R[0].value,ast.Dict),ast.unparse(F);d={k.value:ast.unparse(v) for k,v in zip(R[0].value.keys,R[0].value.values)};assert d=={'schema':q+'replay-validation.v1'+q,'manifest_digest':'manifest.sha256','workflow_process_digest':'replayed.workflow_state.digest','capability_process_digest':'replayed.capability_state.digest','valid':'not verification['+q+'violations'+q+']','verification':'verification'},d;r=pathlib.Path('experiments/live_research_2026-07-29/selfstudy/runs/failed-epoch4-run-9175f0ecb055e57455af3c50df153c5a');h=Harness(r,read_only=True);w,c=h.workflow_state.digest,h.capability_state.digest;assert w.startswith('sha256:') and c.startswith('sha256:') and w!=c,(w,c);g=verify_root(r);assert g['stats']['workflow_process_digest']==w and g['stats']['capability_process_digest']==c,g['stats'];p=_fresh_replay_validation(r);assert p['workflow_process_digest']==w and p['capability_process_digest']==c and p['valid']==(not p['verification']['violations']),p"`

The transition cross-check and the sampled prefix probe are both present, and the
prefix sample is five quantiles rather than every seq.
`check: grep -q "seqs\[i \* (len(seqs) - 1) // 4\]" src/deepreason/invariants.py && python -W ignore -c "import ast,pathlib;import deepreason.harness as H;from deepreason.invariants import verify_root;q=chr(39);T=ast.parse(pathlib.Path('src/deepreason/invariants.py').read_text());I=[n for n in ast.walk(T) if isinstance(n,ast.If) and any(('fail('+q+'transitions'+q) in ast.unparse(s) for s in n.body)];assert len(I)==1 and ast.unparse(I[0].test)=='h.transitions() != Harness(root, read_only=True).transitions()',[ast.unparse(x.test) for x in I];r=pathlib.Path('experiments/live_research_2026-07-29/selfstudy/runs/failed-epoch4-run-9175f0ecb055e57455af3c50df153c5a');n=len([l for l in (r/'log.jsonl').read_text().splitlines() if l.strip()]);want={i*(n-1)//4 for i in range(5)};at=[];tr=[];oa=H.Harness.at.__func__;H.Harness.at=classmethod(lambda cls,root,seq,*a,**k:(at.append(seq),oa(cls,root,seq,*a,**k))[1]);ot=H.Harness.transitions;H.Harness.transitions=lambda s,*a,**k:(tr.append(1),ot(s,*a,**k))[1];verify_root(r);H.Harness.at=classmethod(oa);H.Harness.transitions=ot;assert len(tr)>=2,tr;assert want<=set(at),(sorted(want),sorted(set(at)));assert len(set(at))<n//4,(sorted(set(at)),n)"`

Reader tolerance is a defaulted field plus a gate, not a special case:
`attempt_trace` defaults empty so an old event still validates, and the demand
for a trace fires only when the root is manifest-bound.
`check: python -c "import ast,pathlib;from deepreason.ontology.event import LLMCall;assert not LLMCall.model_fields['attempt_trace'].is_required();t=pathlib.Path('src/deepreason/invariants.py').read_text();A=ast.parse(t);M='manifest-bound LLM call has no attempt trace';G=[n for n in ast.walk(A) if isinstance(n,ast.If) and any(M in ast.unparse(s) for s in n.body)];assert len(G)==1 and ast.unparse(G[0].test)=='manifest is not None',[ast.unparse(g.test) for g in G];D=[n for n in ast.walk(A) if isinstance(n,ast.FunctionDef) and n.name=='_legacy_bridge_failure_call_seqs'];V=[n for n in ast.walk(A) if isinstance(n,ast.FunctionDef) and n.name=='verify_root'][0];C=[n for n in ast.walk(V) if isinstance(n,ast.Call) and getattr(n.func,'id',None)=='_legacy_bridge_failure_call_seqs'];assert len(D)==1 and len(C)==1,(len(D),len(C))"`

## What is deliberately absent

**The write path never consults the verifier.** No import, deferred or
otherwise, reaches `invariants` or `verification` from `harness.py`, and no
registration is refused because the resulting root would fail validation. This
is not an oversight to be closed by "validating before committing": if the
writer consulted the verifier, a verifier bug would suppress evidence instead of
reporting it, and the log would stop being the only admissible record of what a
run did. Validation is strictly post hoc, and it is allowed to say that a
committed root is broken. Checked above, in both directions — static text and
runtime `sys.modules`.

**Verification does not re-derive labels.** `invariants.py` contains no
`label0`, no `final_labels` and no adjudication call. It checks that the
dependence relation is acyclic and that every status is a member of the `Status`
enum — nothing about which label is *right*. The comment above `status-domain`
records why: `SUSPENDED` / `SUSPENDED_UNSUPPORTED` are legal spec §4
support-cascade labels first produced live on `runs/ab_needham`, and a verifier
that recomputed "expected" labels would have refused them. A clean `verify_root`
does not mean the labels are correct; it means nothing in the graph dangles.
`check: grep -q "final_labels(compute_label0(nodes, att), dep)" src/deepreason/harness.py && grep -q "def _adjudicate" src/deepreason/harness.py && grep -q "toposort(set(h.state.artifacts), build_dep(h.state.artifacts))" src/deepreason/invariants.py && grep -q "Any Status enum member is legal" src/deepreason/invariants.py && ! grep -qE "compute_label0|final_labels|label0|adjudicate\(" src/deepreason/invariants.py`

**Verification never repairs, and the writer always does.** The same torn final
line is truncated by a writable open and left byte-identical by `verify_root`
and by any read-only open. The gate is one `if not read_only:` in
`EventLog.__init__`. Making repair unconditional would make the verifier destroy
the damage it exists to report.
`check: python -W ignore -c "import tempfile,pathlib;from deepreason.harness import Harness;from deepreason.invariants import verify_root;d=pathlib.Path(tempfile.mkdtemp())/'run';h=Harness(d);h.record_measure(inputs=['x']);p=h.log.path;open(p,'a').write('torn');b=p.read_bytes();verify_root(d);Harness(d,read_only=True);assert p.read_bytes()==b,'read-only open rewrote the log';Harness(d);assert p.read_bytes()!=b,'writable open did not repair the torn tail'"`

**Verification cannot read a sealed holdout.** The fence is applied on ANY
read-only open, not only on a truncated `Harness.at` view, so `verify_root`'s
own harness sees `KeyError` for holdout bytes no `Reveal` event released. A
verifier that could read them could leak the answer into a finding's `detail`.
`check: python -c "import tempfile,pathlib;from deepreason.harness import Harness;from deepreason.storage.blobs import FencedBlobStore;d=pathlib.Path(tempfile.mkdtemp())/'run';w=Harness(d);ref=w.blobs.put(b'holdout');b=Harness(d,read_only=True).blobs;assert isinstance(b,FencedBlobStore),type(b);assert not isinstance(Harness(d).blobs,FencedBlobStore);f=FencedBlobStore(b._store,frozenset({ref}));g={};exec(chr(10).join(['def sealed(s,r):','    try:','        s.get(r)','        return False','    except KeyError:','        return True']),g);assert g['sealed'](f,ref) and not g['sealed'](b,ref),'FencedBlobStore does not seal';assert not f.is_grounding_available(ref) and b.is_grounding_available(ref)"`

**Nothing outside the root enters the verdict.** `invariants.py` imports no
`os`, no clock, no randomness and no uuid; its only non-root input is
`meter_total`, the caller's live meter, and the one finding that consumes it
(`accounting`) says so in its detail. There is no strictness flag, no
allow-list, and no way to skip a check — because a verdict that depends on
options is not comparable across roots or across time, which is the property
`REPLAY_VALIDATION.json` is stored to assert.
`check: python -W ignore -c "import ast,json,pathlib,inspect,tempfile,time,shutil;from deepreason.harness import Harness;from deepreason.invariants import verify_root;t=pathlib.Path('src/deepreason/invariants.py').read_text();T=ast.parse(t);full={a.name for n in ast.walk(T) if isinstance(n,ast.Import) for a in n.names}|{n.module for n in ast.walk(T) if isinstance(n,ast.ImportFrom) and not n.level and n.module};ext={x for x in full if not x.startswith('deepreason')};assert ext=={'enum','json','pathlib','urllib.parse'},sorted(ext);dyn=[ast.unparse(n) for n in ast.walk(T) if isinstance(n,ast.Call) and getattr(n.func,'id',getattr(n.func,'attr',None)) in ('__import__','import_module','eval','exec','compile')];assert not dyn,dyn;assert list(inspect.signature(verify_root).parameters)==['root','meter_total'];i=t.index('if meter_total is not None');assert 'accounting' in t[i:i+200];d=pathlib.Path(tempfile.mkdtemp())/'run';h=Harness(d);h.record_measure(inputs=['x']);dump=lambda p: json.dumps(verify_root(pathlib.Path(str(p)),12345),sort_keys=True,default=str);a=dump(d);assert [v['check'] for v in verify_root(d,12345)['violations']]==['accounting'],a;time.sleep(1.1);assert dump(d)==a,'verdict moved between two calls on one root';e=pathlib.Path(tempfile.mkdtemp())/'copy';shutil.copytree(d,e);assert dump(e)==a,'verdict depends on something outside the root bytes (path or filesystem metadata)'"`

**Not every prefix is verified.** `Harness.at` is probed at five quantile seqs,
not at every seq. Bounded on purpose — the cost is linear in events per probe —
so "verify_root passed" is not evidence that an arbitrary historical view opens.
If you need that, sweep it yourself; see the grep above for the sampling
expression.

**`verify_root` writes no file at all**, including `REPLAY_VALIDATION.json`.
That record is assembled by callers out of the return value; see
`DR-SUB-verification` for who writes it and what else it binds. Not "creates no
new file" — every byte under the root is unchanged, on a one-event root and on a
1083-file committed one. (Until 2026-08-03 this check pinned the turmite root,
whose home was gitignored by its ladder and so never survived a fresh clone —
`docs/ERRATA.md` E7.)
`check: python -c "import hashlib,pathlib,tempfile;from deepreason.harness import Harness;from deepreason.invariants import verify_root;s=lambda r:{str(p.relative_to(r)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(r.rglob('*')) if p.is_file()};d=pathlib.Path(tempfile.mkdtemp())/'run';h=Harness(d);h.record_measure(inputs=['x']);b=s(d);assert b;verify_root(d);assert s(d)==b,'verify_root wrote to a fresh root';r=pathlib.Path('experiments/2026-08-02-stress-triplet/home-orbit/runs/run-6472629dbc5d408a733d472040671752');c=s(r);assert len(c)==1083,len(c);verify_root(r);assert s(r)==c,'verify_root wrote to a committed root'"`

## How to change it

1. **Read `DR-INV-frozen-surfaces` first.** Both sides are frozen surfaces. The
   question is never "is this better" but "does any recorded root's `valid` or
   `att` move". The 42-root sweep documented there is the instrument; run it
   before and after and compare byte-identically.
2. **Reader before writer, always.** A new field on a durable record gets a
   default and a reader that decides what its ABSENCE means for a root written
   before the field existed. Only then may the writer emit it. `attempt_trace`
   is the worked example: defaulted so old events validate, demanded only when
   `manifest is not None`.
3. **A new typed event channel moves in one order**: `Rule` and the payload
   field in `ontology/event.py` → the `_apply_event` branch → a `_reset`
   attribute if it materializes state → the `record_*` seam → a determinism
   finding in `verify_root` → a channel entry in `report.py`. Stopping before
   the last step defaults the new finding to `integrity`, and `integrity` is
   what decides `valid` — so every recorded root that trips it flips. See
   `DR-SUB-verification`'s first trap.
4. **Anything added to `_reset` must be reconstructible from the log alone.**
   `_commit`'s failure path resets and re-replays; state that cannot be rebuilt
   that way survives a failed append in memory but not on disk, and the next
   `verify_root` reports it as a `replay` divergence rather than as the write
   bug it is.
5. **Never route the writer through the verifier** to "fail fast". See the
   absences above; this is a design decision, not an unimplemented feature.
6. **If a change makes an existing root unopenable, it is wrong by definition.**
   The symptom is not a helpful error: the root collapses to a single `open`
   finding with empty `stats`, which erases every other finding it would have
   produced.

What breaks first, in the order you will meet it:
`test_replay_reproduces_state_byte_for_byte` (the test that exists FOR the
property — replay against the state a LIVE session actually held; it is not the
only test that makes that comparison, about ten subsystem tests reopen a root
and compare too, but it is the one that names it); then the persistence
invariants — read-only enforcement, torn-tail repair, failed-append rollback,
seq fencing; then `verify_root` over generated messy runs; then the root sweep,
which is the expensive one, because by then you need to know whether a committed
root moved.

`check: python -m pytest tests/test_replay.py tests/test_persistence_invariants.py tests/test_torn_append.py -q`
`check: python -m pytest tests/test_chaos_invariants.py "tests/test_run_manifest.py::test_manifest_is_immutable_canonical_and_hash_verified" -q`

Also worth running when you touch the correlation passes rather than the replay
itself: `tests/test_v6_controller3_replay_verification.py`, which pins the
fail-closed behaviour of the pre-replay controller-v3 correlation.

No `Sweep:` header yet, deliberately (SCHEMA.md sanctions the omission when
stated): this seam's agreement is the replay relation itself, not a single
field — its enforcement sites compare whole materialized states
(`model_dump_json`, digest pairs) rather than testing one symbol, so every
candidate FIELD && OTHER_SIDE spec tried either matches nothing the
compare-or-raise detector can see or flags half the tree. A spec that targets
the state-comparison sites specifically is parked in
`experiments/2026-08-03-fix-attached-evidence-integrity/PARKED.md` with the
other headerless seams.

## Traps

- **Opening a suspect root writable destroys the evidence.** `Harness(root)` is
  the default spelling and it truncates a torn final line in place. A diagnostic
  script that opens the root "just to look" before running `verify_root` has
  already changed the bytes the verifier was going to judge, and the resulting
  clean verdict is worthless. Always `read_only=True`; the check under
  *deliberately absent* demonstrates both halves of the asymmetry.
- **A harness-side raise at open erases every other finding.** A corrupt
  `workflow-checkpoint.json`, a failed `validate_terminal_commitment_storage`,
  and a mid-log seq gap all surface identically: one `open` finding, `"stats":
  {}`. `_controller_v3_history` runs BEFORE replay precisely so its typed
  findings survive that collapse — nothing else does. A caller that indexes into
  `stats` unconditionally crashes on exactly the roots most worth inspecting.
`check: python -c "import tempfile,pathlib,json;from deepreason.harness import Harness;from deepreason.invariants import verify_root;d=pathlib.Path(tempfile.mkdtemp())/'run';h=Harness(d);h.record_measure(inputs=['x']);g=verify_root(d);assert set(g)=={'violations','stats'} and g['stats']['events']==1,g;(d/'workflow-checkpoint.json').write_text(json.dumps({'schema':'workflow.checkpoint.v0'}));b=verify_root(d);assert b['stats']=={} and [v['check'] for v in b['violations']]==['open'],b" && python -c "import ast,pathlib;T=ast.parse(pathlib.Path('src/deepreason/invariants.py').read_text());F=[n for n in ast.walk(T) if isinstance(n,ast.FunctionDef) and n.name=='verify_root'][0];s=[ast.unparse(x) for x in F.body];a=[i for i,x in enumerate(s) if '_controller_v3_history(' in x];b=[i for i,x in enumerate(s) if 'Harness(root, read_only=True)' in x];assert a and b and max(a)<min(b),(a,b)"`
- **Two replays of the same code are not a correctness check.** The `replay`
  finding compares two `Harness` opens of one log; both run the same
  `_apply_event`. It catches NONDETERMINISM — an iteration order that leaked
  into serialization, a set where a list was needed — and nothing else. Nothing
  in `verify_root` ever sees the state a live session held; only tests do, by
  snapshotting before they reopen. `tests/test_replay.py` is the one written for
  it; roughly ten subsystem tests (`test_budget`, `test_hv`, `test_loop`,
  `test_merge`, `test_scheduler`, `test_schools`, ...) repeat the comparison
  incidentally, so deleting `test_replay.py` alone weakens the evidence rather
  than removing the property. Deleting the `replay` finding removes neither.
`check: python -c "import pathlib,subprocess;t=pathlib.Path('tests/test_replay.py').read_text();assert 'def test_replay_reproduces_state_byte_for_byte' in t and 'snapshot = live.state.model_dump_json()' in t and 'reopened.state.model_dump_json() == snapshot' in t;o=subprocess.run(['grep','-rlE',r'Harness\([^)]*\)\.state\.model_dump_json\(\) == |\.state\.model_dump_json\(\) == (harness|live)\.state\.model_dump_json\(\)','tests'],capture_output=True,text=True).stdout.split();assert len(o)>=8,o;i=pathlib.Path('src/deepreason/invariants.py').read_text();assert 'model_dump_json' in i and i.count('model_dump_json')==2,i.count('model_dump_json')"`
- **Tampering with a derived `state_diff` field proves nothing.** `att+`, `dep+`,
  `A+` and `Π+` are written for the record and never read back, so editing them
  in a stored log changes no reopened state; `carry+`, `addr+`, `hv_set` and
  `reach_set` ARE replay inputs and editing them does. A tamper-detection
  experiment that mutates only the first group will report, correctly and
  uselessly, that nothing happened. The read-back set is pinned by the check
  under *The agreement*.
- **Pre-v6 roots are expected to refuse.** Committed roots fall into three
  kinds — a v6 manifest that loads, a pre-v6 manifest that raises
  `UnsupportedRunManifestVersionError`, and no `run-manifest.json` at all,
  which opens fine. All three kinds are non-empty, and every tracked root is
  exactly one of them. Refusal is the expected baseline, not a regression to
  be fixed by widening the manifest loader — see `DR-INV-frozen-surfaces`,
  surface 4. The classification is by DIRECT manifest load over every
  git-tracked root, `runs/jolt_positive_headroom_v3_1/` included;
  `tools/root_sweep.py` scans `experiments/` only — two instruments, two true
  numbers, cite the instrument with the number.

  **The check below deliberately pins no count.** It asserts the partition
  and the non-emptiness, because the counts are not a property of the system:
  every tranche that commits a run root moves them. As a dated measurement
  rather than a live claim, at `e6a11428` on 2026-08-05 the git-tracked
  figures were 47 roots — 30 v6, 14 raising, 3 without a manifest. Do not
  re-pin them.
`check: python -W ignore -c "import pathlib,subprocess,collections;from deepreason.run_manifest import load_run_manifest as L,UnsupportedRunManifestVersionError as U;R=[pathlib.Path(p).parent for p in subprocess.run(['git','ls-files'],capture_output=True,text=True).stdout.splitlines() if p.endswith('/log.jsonl')];g={'L':L,'U':U,'N':'run-manifest.json'};exec(chr(10).join(['def k(r):','    m=r/N','    if not m.exists(): return 2','    try:','        L(m)','        return 0','    except U:','        return 1']),g);c=collections.Counter(g['k'](r) for r in R);assert len(R)>40 and c[0] and c[1] and c[2] and c[0]+c[1]+c[2]==len(R),(len(R),dict(c))"`

- **A census check expires; a partition check does not.** This exact check
  went stale-false TWICE, both times because a tranche committed a run root
  and nothing re-ran it: 42/25 → 45/28 when the stress-triplet roots landed
  (2026-08-02, corrected 2026-08-03 by updating the numerals — `docs/ERRATA.md`
  E3), and 45/28/14/3 → 47/30/14/3 when rung 5's live A/B arms landed
  (`f6d41bff`, 2026-08-04). The first correction updated the numbers, which is
  precisely what guaranteed the second occurrence. Fixed 2026-08-05 in
  `experiments/2026-08-05-fix-expired-census-readers/` by asserting the claim
  the prose actually makes — three non-empty kinds partitioning the tracked
  roots — instead of the census that stood in for it. The same defect had
  two more instances at the same moment: `SEAM-manifest-x-schools`'s
  42/11/3 check, and `tests/test_module_fingerprints.py`, which asserted that
  NO committed root carries a module-fingerprint stamp — true only until the
  first run recorded after rung 4's writer was committed.
- **A verify_root predicate must select by the writer's discriminator, never
  by citation shape.** The `attached-evidence` check keyed its candidate set
  on `mention` refs alone and was tripped by the first live conjecture that
  cited its own evidence (stress-triplet
  `run-0a3e93d6e8031e2e6d1d21dde2fa93cc` — the root this seam's instruments
  flagged with rc=5 plus one violation, both correct about the verdict and
  wrong about the cause). Fixed 2026-08-03 by requiring `import` provenance;
  the writer-reader agreement now has its own document,
  `DR-SEAM-periphery-x-verification`, and the worked diagnosis is in
  `experiments/2026-08-03-fix-attached-evidence-integrity`.
`check: grep -q "artifact.provenance.role == \"import\"" src/deepreason/invariants.py && test -f docs/map/SEAM-periphery-x-verification.md`
- **`seq-stream` is defence in depth, not the enforcement.** The reader raises
  `EventSequenceError` on any gap, so a gapped log never reaches the graph
  checks; it becomes an `open` finding instead. Reading the `seq-stream` name in
  a report and concluding the log was parsed successfully is backwards. The
  collapse is not special-cased per damage type: ONE `try` wraps the read-only
  open, and its handler mints `open` — which is why a seq gap, a corrupt
  checkpoint and a failed `validate_terminal_commitment_storage` are
  indistinguishable in a verdict.
`check: python -W ignore -c "import ast,json,tempfile,pathlib;from deepreason.harness import Harness;from deepreason.invariants import verify_root;d=pathlib.Path(tempfile.mkdtemp())/'run';h=Harness(d);h.record_measure(inputs=['a']);h.record_measure(inputs=['b']);p=h.log.path;L=p.read_text().splitlines();o=json.loads(L[1]);o['seq']=5;L[1]=json.dumps(o);p.write_text(chr(10).join(L)+chr(10));g=verify_root(d);assert [v['check'] for v in g['violations']]==['open'] and g['stats']=={},g;src=pathlib.Path('src/deepreason/invariants.py').read_text();assert 'seq-stream' in src;T=ast.parse(src);V=[n for n in ast.walk(T) if isinstance(n,ast.FunctionDef) and n.name=='verify_root'][0];t=[n for n in V.body if isinstance(n,ast.Try) and any('h = Harness(root, read_only=True)' in ast.unparse(s) for s in n.body)];assert len(t)==1,len(t);assert any((chr(39)+'open'+chr(39)) in ast.unparse(x) for x in t[0].handlers),ast.unparse(t[0].handlers[0])"`
