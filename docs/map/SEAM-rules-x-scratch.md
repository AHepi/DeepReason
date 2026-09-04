<!-- DR-SEAM-rules-x-scratch -->
Verified-at: bc3175394
Verify: python tools/docs_verify.py
Owns: src/deepreason/rules/conj.py, src/deepreason/rules/crit.py, src/deepreason/scratch/conjecture.py
Sides: DR-SUB-rules, DR-SUB-scratch
Sweep: scratch_fence_seq|conjecture_context && Conj|Crit

# rules x scratch

## The agreement

The scratchpad offers the rules a bounded, deterministically selected, immutable
view of what the model has been thinking: sealed to one event-log prefix,
rendered behind opaque handles, and carrying no warrant, status, attack edge or
support for one. The rules promise in return that exactly ONE move consumes it.
The workshop is offered to the move that invents and withheld from the move that
judges: `conj` receives it as a pack section and may write back into it;
`crit` receives one integer, the fence that orders its transaction against the
scratch log, and reads nothing. Both sides fix that fence identically to the
formal one, so a planned context is valid only at the sequence it was planned at
and any intervening event invalidates the plan rather than silently changing
what the model saw. The write-back direction is bounded by the read direction:
a turn may name only handles that turn's own exposure receipt records, and a
scratch write that fails is a typed component diagnostic, never a cancelled
turn. The dependency arrow matches the epistemic one — `rules/` imports
`scratch/`, and `scratch/` imports nothing from `rules/`, so the workshop cannot
reach the machinery that decides what stands.

Exactly one module on each side carries this, and the whole rules-side surface
of the scratchpad is `conj.py`.
`check: python -c "import ast,pathlib as P;pk=lambda p:p.relative_to(P.Path('src')).parts[:-1];res=lambda p,n:(n.module or '') if not n.level else ('.'.join(pk(p)[:len(pk(p))-n.level+1])+'.'+(n.module or '')).strip('.');mods=lambda p:[a.name for n in ast.walk(ast.parse(p.read_text())) if isinstance(n,ast.Import) for a in n.names]+[res(p,n) for n in ast.walk(ast.parse(p.read_text())) if isinstance(n,ast.ImportFrom)];hit=lambda m,t:m==t or m.startswith(t+'.');R=sorted(P.Path('src/deepreason/rules').rglob('*.py'));S=sorted(P.Path('src/deepreason/scratch').rglob('*.py'));assert len(R)>=8 and len(S)>=10,(len(R),len(S));u=sorted(p.relative_to(P.Path('src/deepreason/rules')).as_posix() for p in R if any(hit(m,'deepreason.scratch') for m in mods(p)));assert u==['conj.py'],u;b=[(p.name,m) for p in S for m in mods(p) if hit(m,'deepreason.rules')];assert not b,b" && grep -q "^def plan_conjecture_context(" src/deepreason/scratch/conjecture.py && grep -q "scratch.conjecture import" src/deepreason/rules/conj.py`

## Where it is expressed

| Site | File | Symbol | What it enforces |
|---|---|---|---|
| Plan, at the head | `rules/conj.py` | `plan_conjecture_context`, `plan_conjecture_context_expansion`, called at `plan_fence = harness._next_seq - 1` | the read direction opens at the current log head and nowhere else |
| Fence identity | `scratch/conjecture.py` | `PlannedConjectureContextV1._parts_share_one_fence_and_selection` | one prefix names both logs; the pack, the advisory context and the render receipt all name one selection receipt |
| Model-facing rename | `scratch/conjecture.py` | `render_v6_conjecture_context`, `_v6_aliases_for_render_receipt` | local `B*/C*/L*/G*` handles become `SCR_###` before the provider sees them |
| Pack section | `llm/packs.py` | `render_conj_pack(scratch_context=...)` | scratch enters a pack only as a validated `RenderedScratchPackV1`, in one undroppable, uncompressible section |
| Absence by signature | `llm/packs.py` | `render_crit_pack`, `render_batch_crit_pack` | no parameter exists through which a caller could hand scratch to a criticism pack; their parameter lists are pinned whole, so a rename or a `**kwargs` cannot reopen the door quietly |
| Alias namespaces | `llm/wire.py` | `ConjecturerTurnWireContractV4.__init__`, `ConjecturerTurnWireContractV6._require_namespace` | `SRC_` formal, `SCR_` scratch, `SIM_` sealed inputs; overlap is refused at contract construction |
| Exposure ledger | `rules/conj.py` | `context_plan(plan_kind="scratch")` with `ContextNamespace.SCRATCH` items | every visible scratch handle is byte-accounted in the transaction's exposure receipt |
| Exactly-once, three points | `rules/conj.py`, `scratch/conjecture.py`, `llm/adapter.py` | `pack.count(canonical_scratch_text)`, `final_conjecture_pack.count(receipt_text)`, `prompt.count(advisory_text)` | the committed bytes reach the provider once, checked before dispatch rather than post hoc |
| Commit point | `scratch/conjecture.py` | `prepare_conjecture_context_call` / `commit_conjecture_context` | the receipt and its coverage progress become durable only immediately before dispatch |
| Write-back gate | `rules/conj.py` | `validate_proposal(..., visible_aliases=scratch_aliases, context_ref=exposure_ref)` then `admit_proposal(...)` with the same pair | the whole proposal resolves against what was actually shown BEFORE the first scratch event |
| Component isolation | `rules/conj.py` | `_v6_component_diagnostic(component="scratch", ...)` at `semantic_validation` and `materialization` | a rejected or half-written scratch proposal does not cancel the candidates in the same turn |
| The fence, and only the fence | `rules/crit.py` | `scratch_fence_seq=fence` in `_v6_transactional_batch_call` and `_v6_transactional_atomic_critic_call`, the two helpers `crit_argumentative_batch` dispatches through | criticism orders itself against the scratch log without reading it |
| Record-level role guard | `ontology/event.py` | `LLMCall`'s validator (`only conjecturer calls may carry advisory context`) and `ConjectureContextCallReceiptV1._one_state_prefix` | the durable record refuses a criticism call carrying a context receipt, and re-states the one-prefix rule, independently of any pack or wire guard |
| Replay-side mirror | `workflow/conjecture_recovery.py` | scratch exposure ⟺ `call.conjecture_context`, then `validate_conjecture_context_call` | a recovered scratch-bearing provider result with no context authority is refused; owned by `DR-SUB-workflow`, but it re-derives THIS agreement |
| Replay validation | `invariants.py` | `validate_conjecture_context` | the context fence strictly precedes the call event it authorized |

The agreement is enforced a second time on the durable record, so a pack-side or
wire-side hole alone cannot put scratch in front of a critic.
`check: python -c "import ast,pathlib as P;t=ast.parse(P.Path('src/deepreason/ontology/event.py').read_text());I=[(ast.unparse(n.test),[ast.unparse(s) for s in n.body if isinstance(s,ast.Raise)]) for n in ast.walk(t) if isinstance(n,ast.If)];need=[(['self.formal_fence_seq','!=','self.scratch_fence_seq'],'conjecture context formal and scratch fences must name one prefix'),(['self.role','!=','conjecturer'],'only conjecturer calls may carry advisory context')];assert all(any(all(f in k for f in F) and any(m in r for r in R) for k,R in I) for F,m in need),[k for k,_ in I]"`

`workflow/reducer.py` and `workflow/state.py` compare the same fence pair, but on
the WORKFLOW state rather than on this agreement; they belong to
`DR-SEAM-scratch-x-workflow` and are named here only so the `Sweep:` header above
does not report them as omissions from this document.

The criticism side's total scratch surface is two fence assignments, each equal
to the formal fence at the same call.
`check: test "$(grep -c scratch src/deepreason/rules/crit.py)" -eq 2 && test "$(grep -c fence src/deepreason/rules/crit.py)" -eq 6 && test "$(grep -cE "^ +(formal|scratch)_fence_seq=fence,$" src/deepreason/rules/crit.py)" -eq 4 && test "$(grep -cE "^ +fence = max\(0, harness\._next_seq - 1\)$" src/deepreason/rules/crit.py)" -eq 2`

Scratch reaches a conjecture pack only through the typed record, in a section
the allocator may not drop or compress.
`check: grep -q "RenderedScratchPackV1.model_validate(scratch)" src/deepreason/llm/seat_plugins.py && grep -q "^class RenderedScratchPackV1" src/deepreason/scratch/render.py && python -c "from deepreason.llm.seat_layouts import CONJECTURER_LEGACY_LAYOUT as C, CRITIC_LEGACY_LAYOUT as R;from deepreason.llm.seat_plugins import ensure_seeded;from deepreason.llm.seat_sections import resolve_section_plugin;ensure_seeded();T=lambda l:{resolve_section_plugin(e.plugin_id,e.plugin_version).section_id:e for e in l.entries};j=T(C);r=T(R);e=j['scratch-advisory-context'];assert e.droppable is False and e.compressible is False, e;assert 'scratch-advisory-context' not in r, 'a critic pack carries no scratch'"`

The planned context carries one fence for both logs, matched to the attention
pack it was built from; a plan whose fence has moved cannot commit, a historical
view can neither plan nor commit at all, and `verify_root` re-checks on replay
that the fence precedes its call.
`check: python -c "import ast,pathlib as P;t=ast.parse(P.Path('src/deepreason/scratch/conjecture.py').read_text());f=[n for n in ast.walk(t) if isinstance(n,ast.FunctionDef) and n.name=='_parts_share_one_fence_and_selection'][0];g={ast.unparse(n.test):[ast.unparse(b.exc) for b in n.body if isinstance(b,ast.Raise)] for n in f.body if isinstance(n,ast.If)};need={'self.formal_fence_seq != self.scratch_fence_seq':'formal and scratch context fences must name one event prefix','self.attention_pack.state_seq != self.scratch_fence_seq':'attention pack does not match the scratch fence'};assert all(any(m in r and 'ValueError' in r for r in g.get(k,[])) for k,m in need.items()),g" && test "$(grep -cE "^ +plan_fence = harness\._next_seq - 1$" src/deepreason/rules/conj.py)" -eq 2 && python -c "import ast,pathlib as P;t=ast.parse(P.Path('src/deepreason/invariants.py').read_text());g=[n for n in ast.walk(t) if isinstance(n,ast.If) and ast.unparse(n.test)=='receipt.formal_fence_seq >= event.seq'];assert len(g)==1,len(g);b=[ast.unparse(s) for s in g[0].body];assert any('fail(' in s and 'conjecture-context' in s and 'context fence does not precede the call event' in s for s in b),b" && python -m pytest tests/test_conjecture_scratch_context_v4.py::test_stale_plan_cannot_commit_and_a_fresh_rebuild_can tests/test_conjecture_scratch_context_v4.py::test_historical_views_can_neither_plan_nor_commit_context -q`

The sealed bytes are counted three times on the way to the provider: in the
pack, in the receipt, and in the finished prompt.
`check: python -c "import ast,pathlib as P;S=[('src/deepreason/seat_sources/registry.py','pack.count(result.substitutes) != 1','SEAT_SOURCE_SUBSTITUTION_NOT_UNIQUE'),('src/deepreason/scratch/conjecture.py','final_conjecture_pack.count(receipt_text) != 1','final Conj pack must contain the exact advisory context once'),('src/deepreason/llm/adapter.py','prompt.count(advisory_text) != 1','rendered provider request must contain the exact advisory context once'),('src/deepreason/llm/adapter.py','rendered_pack.count(protected) != 1','advisory context bytes are absent or duplicated before aliasing')];G=[(f,e,m,[n for n in ast.walk(ast.parse(P.Path(f).read_text())) if isinstance(n,ast.If) and ast.unparse(n.test)==e]) for f,e,m in S];assert all(len(g)==1 and any(isinstance(s,ast.Raise) and m in ast.unparse(s) for s in g[0].body) for f,e,m,g in G),[(f,e,len(g)) for f,e,m,g in G]" && python -m pytest tests/test_v6_conjecture_scratch_consumption.py::test_initial_v6_conjecture_commits_exact_model_facing_scratch_once -q`

Every visible handle is exposed under its own namespace in the transaction
ledger, so what the model saw is a typed record rather than an inference from
the prompt text; validation and admission are then given that same alias set and
that same exposure receipt, and an unknown reference is refused before any
scratch event.
`check: grep -q "namespace=ContextNamespace.SCRATCH," src/deepreason/rules/conj.py && grep -q 'plan_kind="scratch",' src/deepreason/rules/conj.py && grep -q 'SCRATCH = "scratch"' src/deepreason/workflow/transaction.py && python -c "import ast,pathlib as P;t=ast.parse(P.Path('src/deepreason/rules/conj.py').read_text());C=[c for c in ast.walk(t) if isinstance(c,ast.Call) and ast.unparse(c.func).endswith(('.validate_proposal','.admit_proposal'))];assert len(C)==2,[ast.unparse(c.func) for c in C];k={ast.unparse(c.func).split('.')[-1]:{a.arg:ast.unparse(a.value) for a in c.keywords} for c in C};assert sorted(k)==['admit_proposal','validate_proposal'],sorted(k);assert all(k[n].get('visible_aliases')=='scratch_aliases' and k[n].get('context_ref')=='exposure_ref' for n in k),k" && python -m pytest tests/test_v6_scratch_atomicity.py::test_unknown_reference_is_rejected_before_any_scratch_event -q`

A scratch component that fails is diagnosed in two typed phases; the turn's
valid candidates still commit.
`check: test "$(grep -c 'component="scratch",' src/deepreason/rules/conj.py)" -eq 2 && python -c "import ast,pathlib;t=ast.parse(pathlib.Path('src/deepreason/rules/conj.py').read_text());C=[(h,c) for n in ast.walk(t) if isinstance(n,ast.Try) for h in n.handlers for c in ast.walk(h) if isinstance(c,ast.Call) and getattr(c.func,'id','')=='_v6_component_diagnostic' and any(k.arg=='component' and getattr(k.value,'value',None)=='scratch' for k in c.keywords)];assert sorted(getattr(k.value,'value',None) for _,c in C for k in c.keywords if k.arg=='phase')==['materialization','semantic_validation'],C;assert not [r for h,_ in C for r in ast.walk(h) if isinstance(r,ast.Raise)],'a scratch component handler re-raises and cancels the turn'" && python -m pytest tests/test_v6_conjecture_component_atomicity.py::test_valid_candidate_and_invalid_optional_scratch_complete_partially -q`

Recovery refuses the two mismatched shapes: scratch exposure without a context
receipt, and a context receipt without scratch exposure.
`check: python -c "import ast,pathlib as P;t=ast.parse(P.Path('src/deepreason/workflow/conjecture_recovery.py').read_text());d=[n for n in ast.walk(t) if isinstance(n,ast.FunctionDef) and n.name=='_authority'][0];assert [s for s in ast.walk(d) if isinstance(s,ast.Raise)],'_authority no longer raises';A=[(ast.unparse(c.args[0]),ast.unparse(c.args[1])) for c in ast.walk(t) if isinstance(c,ast.Call) and ast.unparse(c.func)=='_authority' and len(c.args)==2];need=[('call.conjecture_context is not None','scratch-bearing provider result has no conjecture context authority'),('call.conjecture_context is None','provider call claims scratch context absent from transaction exposure')];assert all(any(a==x and y in b for a,b in A) for x,y in need),A" && grep -q "^def validate_conjecture_context_call(" src/deepreason/scratch/conjecture.py && python -m pytest tests/test_v6_conjecture_scratch_consumption.py::test_recovery_rejects_scratch_exposure_without_durable_context_authority -q`

## What is deliberately absent

**Criticism is given no scratch content, and the refusal is structural.** It is
not that no caller currently passes it — no parameter exists to pass. The
criticism renderers do take non-target parameters (`simulation_proposals`,
`premise_invitation`), and the check below pins their exact signatures rather
than merely counting them, so a scratch parameter cannot arrive disguised as
one more of those. This is
the operator's R5/R6 requirement: the scratchpad authority chain and the
conjecture/criticism adjudication chain must not exist together. Reading the
absence as an oversight and "wiring the critic to the workshop" is the specific
mistake this section exists to prevent.

`reference_menus` (2026-08-26) is precisely the shape this warns about: an
optional argument on both critic renderers that COULD carry scratch handles,
because a reference menu is generic over handle kind. It does not, and the
refusal is re-established rather than assumed — no scratch-kind field is
declared on a critic contract, and `rules/crit.py`'s menu builder asks for
citable blocks only.

`check: python -m pytest tests/test_reference_menu.py -k "no_critic_menu_can_carry_scratch_content" -q`
`check: python -c "import inspect;from deepreason.llm import packs;F={n:inspect.signature(getattr(packs,n)) for n in dir(packs) if n.startswith('render_') and callable(getattr(packs,n))};bad=[n for n,s in F.items() if any('scratch' in p for p in s.parameters)];assert bad==['render_conj_pack'],bad;C={n:list(s.parameters) for n,s in F.items() if 'crit' in n};assert C=={'render_crit_pack':['target_id','state','commitments','blobs','token_budget','premise_invitation','citable_evidence_context','frame_slice_context','frame_crisis_context','reference_menus','layout','seat_pack_layout','section_receipts'],'render_batch_crit_pack':['target_ids','state','commitments','blobs','token_budget','simulation_proposals','simulation_enabled','premise_invitation','citable_evidence_context','reference_menus']},C" && python -m pytest tests/test_prose_refutation_boundaries.py::test_the_criticism_pack_cannot_be_given_scratch -q`


**Criticism cannot WRITE to the workshop either.** The conjecturer turn contract
takes `scratch_aliases` and its wire model carries `scratch_proposal`; no critic
contract takes aliases and no critic wire model has any scratch field at all.
The check enumerates every `Critic`-named class in `llm/wire.py` rather than a
fixed three, so a new critic contract or wire model is covered the moment it is
written. The workshop belongs to the move that invents, in both directions.
`check: python -c "import inspect;from pydantic import BaseModel;from deepreason.llm import wire;assert 'scratch_aliases' in inspect.signature(wire.ConjecturerTurnWireContractV6.__init__).parameters;assert 'scratch_proposal' in wire.ConjecturerTurnWireV6.model_fields;K=[getattr(wire,n) for n in dir(wire) if 'Critic' in n and inspect.isclass(getattr(wire,n))];C=[c for c in K if issubclass(c,wire.WireContract)];M=[c for c in K if issubclass(c,BaseModel)];assert len(C)>=3 and len(M)>=5,([c.__name__ for c in C],[c.__name__ for c in M]);P=[(c.__name__,k) for c in C for k,v in inspect.signature(c.__init__).parameters.items() if 'scratch' in k or v.kind in (v.VAR_KEYWORD,v.VAR_POSITIONAL)];assert not P,P;A=[(c.__name__,a) for c in C for a in dir(c) if 'scratch' in a.lower()];assert not A,A;F=[(c.__name__,f) for c in M for f in c.model_fields if 'scratch' in f];assert not F,F"`

**The separation is enforced by an AST walk, not a header grep**, because a
function-local `import deepreason.scratch...` inside `crit.py` would satisfy a
naive check and still couple the two. The same walk covers `informal/trial.py`,
which is where a sustained prose case actually changes a status, and
`rules/warrants.py` and `adjudication/edges.py`, which are the narrowest part of
the chain: a warrant's referents are an artifact, a commitment, a validity node
and a trace blob, never a scratch object. The walk in
`tests/test_prose_refutation_boundaries.py` matches on the ABSOLUTE module name,
so `from ..scratch.render import ...` slips past it on all four modules; the
probe below resolves each `ImportFrom` level against the importing package
first, and is the half of this claim that catches a relative import.
`check: python -c "import ast,pathlib as P;pk=lambda p:p.relative_to(P.Path('src')).parts[:-1];res=lambda p,n:(n.module or '') if not n.level else ('.'.join(pk(p)[:len(pk(p))-n.level+1])+'.'+(n.module or '')).strip('.');mods=lambda p:[a.name for n in ast.walk(ast.parse(p.read_text())) if isinstance(n,ast.Import) for a in n.names]+[res(p,n) for n in ast.walk(ast.parse(p.read_text())) if isinstance(n,ast.ImportFrom)];F=['src/deepreason/rules/crit.py','src/deepreason/informal/trial.py','src/deepreason/rules/warrants.py','src/deepreason/adjudication/edges.py'];assert all(P.Path(f).is_file() for f in F),F;b=[(f,m) for f in F for m in mods(P.Path(f)) if m=='deepreason.scratch' or m.startswith('deepreason.scratch.')];assert not b,b" && python -m pytest tests/test_prose_refutation_boundaries.py::test_the_criticism_rule_imports_no_scratch_module tests/test_prose_refutation_boundaries.py::test_the_criticism_rule_touches_scratch_only_as_an_ordering_fence tests/test_prose_refutation_boundaries.py::test_the_defended_trial_imports_no_scratch_module tests/test_prose_refutation_boundaries.py::test_no_scratch_identifier_reaches_a_warrant_or_an_attack_edge -q`

**An unresolved question is not a problem.** `ScratchProposalV1` has an
`unresolved_questions` field and `scan_spawns` mints problems from seven
structural triggers over the formal graph — discrimination,
remove-arbitrariness, explanation-debt, connection, integration, research. (The
`SpawnTrigger` enum carries exactly two more that `scan_spawns` never mints:
`SEED` is the operator's question — set as a problem's provenance at run setup,
never spawned by a call — and `AUDIT_CRITIC` is raised from two ladders,
`informal/appellate.py`'s `spawn_audit_problem` and `capture/ladder.py`'s
adjudication-ritual debt sweep.) No edge joins the two AUTOMATICALLY, and none
should. A spawn is a commitment to spend the run's budget; a question in the
workshop is explicitly allowed to be idle, wrong, or unanswerable. The same
holds for the anti-relapse gate, which compares formal verdict vectors and
never a note.

The word AUTOMATICALLY is doing work there, and it is new. The operator's law
of 2026-08-29 (`DR-CON-successor-questions`) opens ONE edge from a question to
a problem, and every property this section defended survives it because of how
narrow that edge is: it fires from an OPTIONAL proposal a critic chose to
write, never from a scan over the graph; it is gated by a per-run switch that
is OFF unless a run turns it on; and its producer is a module outside
`src/deepreason/rules/`, so `scan_spawns` still mints exactly the six triggers
the check below pins and `spawn.py` still takes a zero-line diff. What is now
false is only the unqualified reading — "nothing whatever may connect the two"
— and what remains true is the reason the sentence was written: the budget is
never spent because a note exists.
`check: python -c "import ast,pathlib;t=ast.parse(pathlib.Path('src/deepreason/rules/spawn.py').read_text());fn=[n for n in ast.walk(t) if isinstance(n,ast.FunctionDef) and n.name=='scan_spawns'][0];m={n.attr for c in ast.walk(fn) if isinstance(c,ast.Call) and ast.unparse(c.func).endswith('spawn') for n in ast.walk(c) if isinstance(n,ast.Attribute) and getattr(n.value,'id','')=='SpawnTrigger'};assert sorted(m)==['CONNECTION','DISCRIMINATION','EXPLANATION_DEBT','INTEGRATION','REMOVE_ARBITRARINESS','RESEARCH'],sorted(m)" && python -c "from deepreason.ontology.problem import SpawnTrigger;n=sorted(t.name for t in SpawnTrigger);assert n==['AUDIT_CRITIC','CONNECTION','DISCRIMINATION','EXPLANATION_DEBT','INTEGRATION','PROMOTION','REMOVE_ARBITRARINESS','RESEARCH','SEED','SUCCESSOR'],n" && grep -q "SpawnTrigger.AUDIT_CRITIC," src/deepreason/informal/appellate.py && grep -q "SpawnTrigger.AUDIT_CRITIC," src/deepreason/capture/ladder.py && test "$(grep -c scratch src/deepreason/rules/guards/anti_relapse.py)" -eq 0 && grep -q "^def verdict_vector(" src/deepreason/rules/guards/anti_relapse.py`

**Nothing that crosses the seam leaves a mark on the formal graph.** A scratch
event's `state_diff` is empty, no scratch handle or receipt id appears in any
formal diff or in an admitted artifact's interface, grounding and evidence
lambdas do not move, and an outright self-contradictory note is admitted to
`scratch_state` while `harness.state` is byte-identical before and after.
`check: python -m pytest tests/test_conjecture_scratch_context_v4.py::test_scratch_handles_never_enter_formal_state_or_grounding tests/test_v6_scratch_atomicity.py::test_contradictory_speculation_is_admitted_only_to_scratch -q && ! grep -q scratch src/deepreason/rules/spawn.py && grep -q "^def scan_spawns(" src/deepreason/rules/spawn.py && grep -q "unresolved_questions" src/deepreason/scratch/proposals.py`

**Alias namespaces do not overlap, and that is a refusal rather than a
convention.** Both the v4/v5 and v6 contracts reject a scratch alias that
collides with a formal one at construction, because a collision would let a
speculative note resolve as a formal artifact reference in a `requested_refs`
list.
`check: python -c "exec('def R(f):\n try:\n  f()\n  return chr(32)\n except ValueError as e:\n  return str(e)');from deepreason.llm.wire import AliasTable as A,ConjecturerTurnWireContractV4 as V4,ConjecturerTurnWireContractV6 as V6;a=A({'SRC_001':'art:1'});m=R(lambda: V4(reasoning=False,aliases=a,scratch_aliases={'SRC_001':'s'}));assert 'formal and scratch alias namespaces must not overlap' in m,m;m=R(lambda: V6(reasoning=False,aliases=a,scratch_aliases={'SRC_002':'s'}));assert 'SCR' in m,m;m=R(lambda: V6(reasoning=False,aliases=a,scratch_aliases={'SCR_001':'s'},simulation_enabled=True,maximum_simulation_proposals=1,simulation_input_aliases=('SIM_001','SIM_001')));assert 'v6 visible alias namespaces must be disjoint' in m,m;V6(reasoning=False,aliases=a,scratch_aliases={'SCR_001':'s'},simulation_enabled=True,maximum_simulation_proposals=1,simulation_input_aliases=('SIM_001','SIM_002'))" && grep -q '_require_namespace(scratch, "SCR")' src/deepreason/llm/wire.py`

**The fence on the criticism side is NOT an absence.** It is present and
deliberate: a criticism transaction still has to be ordered against the scratch
log, or a concurrent scratch write could not be placed relative to it. Deleting
`scratch_fence_seq` from `crit.py` to "complete the separation" removes ordering,
not coupling.

## How to change it

The order matters because the receipt is content-addressed and three parties
compare it.

1. **Read `DR-INV-frozen-surfaces` first.** `ScratchPolicy` and its
   `attention_policy()` are manifest surfaces, so any change to pack size,
   channels or roles moves every qualification subject digest — the subject
   payload is a dump of the WHOLE manifest, and `scratch_policy` is a field on
   it. A per-run mode goes on `Config`, never on the manifest.
`check: python -c "import inspect;from deepreason.run_manifest import RunManifest,ScratchPolicy;import deepreason.qualification as q;assert 'scratch_policy' in RunManifest.model_fields,sorted(RunManifest.model_fields);assert callable(getattr(ScratchPolicy,'attention_policy'));s=inspect.getsource(q.qualification_subject_payload);assert 'manifest.model_dump' in s,s"`
2. **Decide which direction you are changing.** Read (scratch → pack) and write
   (turn → scratch) are separately gated and separately recovered; a change that
   touches only one must leave the other's receipts byte-identical.
3. **Change the plan record before the call sites.** `PlannedConjectureContextV1`
   is the contract. Adding a field means its `model_validator` must decide what
   the field's absence means for a plan recorded before you existed, and
   `validate_conjecture_context_call` must re-derive it from the historical view
   at the fence — otherwise the change invalidates existing replay-valid roots
   and is wrong by definition.
4. **Move the exposure and the recovery together.** The scratch exposure items
   in `conj.py` and the biconditional in `workflow/conjecture_recovery.py` are
   one agreement in two files. Change one alone and a crash mid-turn becomes
   unrecoverable, which is a failure mode no test in the read path will surface.
5. **Keep the exactly-once chain intact.** If you insert anything into the pack
   after allocation, it must be separately byte-accounted in a transaction
   context plan and the pack must remain an `AllocatedPack` (see Traps).
6. **Never widen the criticism side to close the asymmetry — the operator has
   now made that call ONCE, and its scope is the whole of it.** The asymmetry
   is the design, and overturning it was always an operator's call rather than
   an implementer's. On 2026-08-29 the operator made one: a criticism may
   propose the next QUESTION, and by default that proposal becomes a scratch
   block linked to the problem it was proposed under. What that decision did
   NOT touch is the read direction and the pack surface, and both are still
   enforced exactly as before: no critic contract takes scratch aliases, no
   critic wire model carries a scratch-named field, `crit.py` imports no
   scratch module at any scope, and neither `render_crit_pack` nor
   `render_batch_crit_pack` gained a parameter. WHO performs the write — the
   criticism rule itself, or something that is not criticism reading what
   criticism recorded — was a SEPARATE question the law did not settle, parked
   for the operator as Q3. **ANSWERED 2026-08-30: ROAD B.** A reader outside
   `rules/` (`successor/reader.py`) walks what criticism already recorded and
   routes it, so THIS RULE IS NOT OVERTURNED — the criticism side was not
   widened at all. `rules/crit.py` takes a ZERO-LINE DIFF against `main`, no
   module under `rules/` names `deepreason.successor` at any scope, and both
   facts are measured rather than asserted
   (`tests/test_successor_dispatch.py::test_rules_crit_takes_a_zero_line_diff`
   and `::test_no_module_under_rules_imports_the_successor_package`). Road A —
   a `_file_successor_question` helper beside `_file_attribution` in `crit.py`
   — would have passed every mechanical check on this page while being a
   workaround of this rule's letter, and was NOT taken.
`check: python -m pytest tests/test_successor_law_line.py::test_nothing_that_labels_ranks_or_admits_reads_a_successor_question tests/test_successor_law_line.py::test_the_channel_has_no_permitted_exception_inside_a_deciding_package tests/test_prose_refutation_boundaries.py -q && test "$(grep -c scratch src/deepreason/rules/crit.py)" -eq 2`
`check: python -m pytest tests/test_successor_dispatch.py::test_rules_crit_takes_a_zero_line_diff tests/test_successor_dispatch.py::test_no_module_under_rules_imports_the_successor_package -q`

What breaks first, in the order you will see it: `ConjectureContextStale` if you
plan at the wrong fence; `"final Conj pack must contain the exact advisory
context once"` if you edit the pack after sealing;
`"rendered provider request must contain the exact advisory context once"` if a
presentation transform runs over an allocated pack; then, only on a later run,
`verify_root`'s `conjecture-context` failure — the expensive one, because by
then the root is committed.

The tests that will catch you, in the order they run cheapest first:
`tests/test_prose_refutation_boundaries.py` (the negative side, 0.1 s),
`tests/test_conjecture_scratch_context_v4.py` (v4/v5 read direction),
`tests/test_v6_conjecture_scratch_consumption.py` (v6 read direction and
recovery), `tests/test_v6_scratch_atomicity.py` and
`tests/test_v6_scratch_authoring_transactions.py` (write direction),
`tests/test_v6_conjecture_component_atomicity.py` (partial completion).

## Traps

- **A destination named on the criticism side would turn a MAP CHECK red, not
  a test.** Two counts in this document are exact: the word `scratch` appears
  in `src/deepreason/rules/crit.py` exactly twice and `fence` exactly six
  times, and both are `scratch_fence_seq`'s ordering role. So a successor
  destination reached by naming it in `crit.py` — even in a comment, even
  inside a function-local import — fails `docs_verify` rather than the test
  suite, and the failure names this seam rather than the change that caused
  it. The channel is therefore reached through a neutrally-named module
  (`DR-CON-successor-questions`), and the wire field is `successor_question`
  rather than anything naming where it goes. Recorded 2026-08-30
  (`experiments/2026-08-30-change-successor-questions/`); the counts have not
  moved.
`check: test "$(grep -c scratch src/deepreason/rules/crit.py)" -eq 2 && test "$(grep -c fence src/deepreason/rules/crit.py)" -eq 6 && python -c "import inspect;from pydantic import BaseModel;from deepreason.llm import wire;K=[getattr(wire,n) for n in dir(wire) if 'Critic' in n and inspect.isclass(getattr(wire,n))];M=[c for c in K if issubclass(c,BaseModel)];assert M;assert not [(c.__name__,f) for c in M for f in c.model_fields if 'scratch' in f];assert {'CompactCritic','BatchCriticCaseWireV2'} <= {c.__name__ for c in M if 'successor_question' in c.model_fields}"`

- **`str` operations demote the `AllocatedPack` marker.** `conj.py` swaps the
  canonical scratch text for the v6 aliased render with `pack.replace(...)` and
  re-wraps the result. Without the re-wrap the adapter re-applies the profile's
  aggregate prefix clip to a pack that `PackIR` had already budgeted
  section-by-section, cutting the sealed advisory context mid-JSON out of the
  dispatched prompt. The comment above the re-wrap in `conj.py` is the record of
  this; every post-allocation insertion below it is separately byte-accounted.
  The FOURTH re-wrap is the reference menus whose handles do not exist until
  after allocation -- the artifact-alias table is derived from the rendered
  pack, and the scratch handles come from the context render that follows it
  (`DR-INV-reference-menu`). It re-wraps for exactly the reason the other
  three do.
`check: test "$(grep -c "pack = AllocatedPack(" src/deepreason/rules/conj.py)" -eq 0 && test "$(grep -c "AllocatedPack(pack" src/deepreason/seat_sources/registry.py)" -eq 2 && grep -q "class AllocatedPack(str):" src/deepreason/llm/packs.py && grep -q "pack_is_allocated = isinstance(pack, AllocatedPack)" src/deepreason/llm/adapter.py`
- **Render-receipt handle maps reload key-sorted, and this seam reads them
  twice.** The receipt is persisted through `canonical_json`, whose sorted keys
  interleave `B10` between `B1` and `B2`. `validate_conjecture_context_call`
  already handles this for the ORDER comparison — it uses `ordered_refs("block")`
  and says so in a comment. The ALIAS derivation beside it,
  `_v6_aliases_for_render_receipt`, numbers `SCR_###` by mapping iteration order
  instead, so a receipt reloaded from a blob and the in-memory receipt the write
  path holds produce different alias tables once a pack reaches ten handles of
  one kind. **Residue: this is a code-reading finding plus the unit probe below,
  not an observed live failure.** No recorded root has been shown to hit it, and
  the seam's own tests render single-block packs. If you touch either function,
  reproduce at 10+ handles before trusting either. Related: `DR-SUB-scratch`'s
  trap, and selfstudy `run-9175f0ec`, where the same reload order produced
  spurious order violations in a different consumer.
`check: python -c "import hashlib;from deepreason.canonical import canonical_json;from deepreason.scratch.render import ScratchRenderReceiptV1;from deepreason.scratch.conjecture import _v6_aliases_for_render_receipt as A;h={'B%d'%i:'sha256:'+hashlib.sha256(str(i).encode()).hexdigest() for i in range(1,13)};r=ScratchRenderReceiptV1.create(state_seq=1,attention_receipt='sha256:'+'a'*64,block_handles=h,cluster_handles={},link_handles={},guide_handles={});q=ScratchRenderReceiptV1.model_validate_json(canonical_json(r.model_dump(mode='json',by_alias=True)));assert r.ordered_refs('block')==q.ordered_refs('block');assert A(r)[0]!=A(q)[0]"`
- **The guard you want is often not on the side you are editing.** A rule about
  what criticism may be given is enforced in the PACK SIGNATURE and the WIRE
  CONTRACT, not inside `crit.py`, because `crit.py` never had the opportunity in
  the first place. Searching `crit.py` for the enforcement and finding nothing is
  the expected result, not evidence that the boundary is unguarded.
- **A refusal raised from inside a nested draft item kills the whole turn.** In
  turmite `run-bc3e8797b3e0609eddb324299c8257bd` a one-block proposal had no
  legal `to_ref`; the old `_not_a_self_link` validator rejected the entire
  conjecture turn, candidates and all, and the run died at cycle 0 discarding a
  correct refutation. Fixed: `_drop_self_links` discards on the container. The
  seam-level lesson survives the fix — a scratch validator that raises rather
  than discards converts an advisory component into a turn-killer, which is
  exactly the coupling the `component="scratch"` diagnostics exist to prevent.
`check: grep -q "def _drop_self_links" src/deepreason/scratch/proposals.py && ! grep -q "_not_a_self_link" src/deepreason/scratch/proposals.py && python -m pytest tests/test_scratch_contracts.py::test_a_self_link_is_dropped_rather_than_killing_the_whole_turn -q`
