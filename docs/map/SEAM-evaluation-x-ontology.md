<!-- DR-SEAM-evaluation-x-ontology -->
Verified-at: 9fa394d9
Verify: python tools/docs_verify.py
Owns: src/deepreason/programs.py, src/deepreason/ontology/commitment.py, src/deepreason/ontology/artifact.py, src/deepreason/oracle.py, src/deepreason/oracle_sandbox.py, src/deepreason/measures/hv.py, src/deepreason/informal/skeleton.py
Sides: DR-SUB-evaluation, DR-SUB-ontology

# evaluation x ontology

## The agreement

The ontology hands evaluation two records and one guarantee about them: an
`Artifact` whose identity is `sha256(canonical(content_ref, codec, interface))`
and nothing else, and a `Commitment` that will still say what it said, because
both are `FrozenRecord`s. In exchange `programs.evaluate` promises that a verdict
is a function of that address and of nothing else — it reads `content_ref`,
`codec` and `interface`, never a fourth field, never `id`, and never the two
fields `compute_id` deliberately leaves out. That is one line drawn twice: the
ontology excludes `provenance` and `warrants` from the address, and evaluation
excludes them from the verdict, so two artifacts with the same id can never
disagree about a criterion. The ontology validates nothing about `eval` —
`Commitment.eval` is a bare `str` carrying its grammar in a comment — which makes
`evaluate`'s `partition(":")` the sole definition of `predicate:` / `program:` /
`rubric:` and the sole authority on what is admissible. Nor does the ontology
address a commitment: `Commitment.id` is any string, so the evaluation side
manufactures the missing half of purity itself, hashing each frozen spec into the
id at eight mint sites and reading that spec back out of `Budget.extra`.
Determinism is a requirement here rather than an observation, because a verdict's
trace is content-addressed into the blob store and referenced by
`Warrant.trace_ref`: one wall-clock value anywhere on the pure path would fork two
runs' logs from identical inputs. The whole arrangement exists so that a verdict
recorded at seq 40 can be re-derived at seq 4000 from bytes the log already holds.

Purity behaviourally: the same address, two records differing in every
unaddressed field — role, school, `event_seq`, carried warrants, and the `id`
itself — produce identical `(verdict, trace)` under a predicate, a structural
program, and an interface-reading program.
`check: python -c "from deepreason.ontology import Artifact, Commitment, Interface, Provenance, Ref; from deepreason import programs; from deepreason.ontology.frozen import FrozenRecord; assert all(issubclass(R, FrozenRecord) and R.model_config['frozen'] for R in (Artifact, Commitment)); i=Interface(commitments=['k'], refs=[Ref(target='t', role='dependence')]); mk=lambda **kw: Artifact(content_ref='inline:hello', codec='utf8', interface=i, **kw); a=mk(id=Artifact.compute_id('inline:hello','utf8',i), provenance=Provenance(role='conjecturer', school='s1', event_seq=9), warrants=['w1']); b=mk(id='', provenance=Provenance(role='variator')); assert {'provenance','warrants'} <= set(Artifact.model_fields) and a.id != b.id; assert all(programs.evaluate(Commitment(id='k', eval=e), a, None) == programs.evaluate(Commitment(id='k', eval=e), b, None) for e in ('predicate:len(content)>2','predicate:len(codec)==4','program:json-wf','program:lineage_ref'))"`

Structurally: `evaluate` touches exactly three attributes of the artifact it is
given, its predicate namespace is exactly the safe names plus `content` and
`codec`, and its trace is exactly the commitment id, the eval string, the verdict
and the program's own detail. Of the program implementations that receive the
artifact object, only `_lineage_ref` and `manifest.component_wf` read it at all,
and both read only `interface.refs` — which is inside the address. The scan is
receiver-BLIND for the five distinctive `Artifact` fields (`content_ref`,
`codec`, `interface`, `provenance`, `warrants`) and it pins where the object may
TRAVEL: the only calls it is passed to are `content_text` and the registry
dispatch, it is never rebound to another name, and every registered program AND
every delegate they forward to takes it as a parameter literally called
`artifact`. Those three clauses exist because a receiver-scoped scan alone is
defeated by a rename, and the field it would then hide is `id` — too common a
name to scan for blind, and the one whose absence "What is deliberately absent"
leans on this very check to prove.
`check: python -c "import ast,inspect,pathlib; from deepreason import programs as P; F=('src/deepreason/programs.py','src/deepreason/manifest.py','src/deepreason/workloads/text.py','src/deepreason/oracle.py'); T={f: ast.parse(pathlib.Path(f).read_text()) for f in F}; ev=[n for n in ast.walk(T[F[0]]) if isinstance(n,ast.FunctionDef) and n.name=='evaluate'][0]; D=[[k.value if isinstance(k,ast.Constant) else '**'+ast.unparse(v) for k,v in zip(d.keys,d.values)] for d in sorted([n for n in ast.walk(ev) if isinstance(n,ast.Dict)], key=lambda n:(n.lineno,n.col_offset))]; assert D[0]==['__builtins__','**_SAFE_NAMES','content','codec'], D[0]; assert D[-1]==['commitment','eval','verdict','**detail'], D[-1]; A=lambda f: sorted({n.attr for n in ast.walk(T[f]) if isinstance(n,ast.Attribute) and isinstance(n.value,ast.Name) and n.value.id=='artifact'}); R=lambda f: sorted({ast.unparse(n) for n in ast.walk(T[f]) if isinstance(n,ast.Attribute) and n.attr in {'content_ref','codec','interface','provenance','warrants'}}); G=lambda f: sorted({ast.unparse(n.func) for n in ast.walk(T[f]) if isinstance(n,ast.Call) and any(isinstance(a,ast.Name) and a.id=='artifact' for a in list(n.args)+[k.value for k in n.keywords])}); assert [A(f) for f in F]==[['codec','content_ref','interface'],['interface'],[],[]], [A(f) for f in F]; assert [R(f) for f in F]==[['artifact.codec','artifact.content_ref','artifact.interface'],['artifact.interface'],[],[]], [R(f) for f in F]; assert [G(f) for f in F]==[['BLOB_PROGRAMS[arg]','component_wf','content_text','dataset_from_spec','fn','frame_assertion_wf','integration_wf','manifest_wf','premise_attribution_wf','premise_resolution_wf_program','presupposition_wf_program','problem_subject_wf','reasoning_wf_program','self.fn'],[],[],[]], [G(f) for f in F]; assert {list(inspect.signature(getattr(s,'fn',s)).parameters)[2] for s in list(P.PROGRAMS.values())+list(P.BLOB_PROGRAMS.values())}=={'artifact'}; import deepreason.manifest as M, deepreason.workloads.text as W, deepreason.oracle as O; assert {list(inspect.signature(f).parameters)[2] for f in (M.component_wf,M.manifest_wf,M.integration_wf,W.reasoning_wf_program,O.dataset_from_spec)}=={'artifact'} and list(inspect.signature(P.content_text).parameters)[0]=='artifact'; assert not [ast.unparse(n) for f in F for n in ast.walk(T[f]) if isinstance(n,(ast.Assign,ast.AnnAssign,ast.AugAssign)) and isinstance(getattr(n,'value',None),ast.Name) and n.value.id=='artifact']"`

The grammar, asserted rather than described. Note the asymmetry between the two
machine kinds: an unknown `program:` name is `evaluable=False` and raises, while
ANY `predicate:` is `evaluable=True` and an unparseable one is a `fail` verdict.
`check: python -c "import pytest; from deepreason import programs; from deepreason.ontology import Artifact, Commitment, Interface, Provenance; a=Artifact(id='x', content_ref='inline:hello', codec='utf8', interface=Interface(), provenance=Provenance(role='seed')); V=lambda e: programs.evaluate(Commitment(id='k', eval=e), a, None)[0]; E=lambda e: programs.evaluable(Commitment(id='k', eval=e)); assert (V('predicate:len(content)==5'), V('predicate:len(content)==4'), V('predicate:))'), V('predicate:'), V('program:json-wf'))==('pass','fail','fail','fail','fail'); assert [E(e) for e in ('predicate:))','predicate:','program:json-wf','program:nope','rubric:s','garbage')]==[True,True,True,False,False,False]; [pytest.raises(programs.NotEvaluable, programs.evaluate, Commitment(id='k', eval=e), a, None) for e in ('program:nope','rubric:s','garbage')]"`

The ontology's side of that: `Commitment` carries four fields, no field validator
and no model validator, and admits an `eval` string of any shape. The one thing
`Budget` does enforce is the shape of the frozen-spec channel — `extra` is
`Mapping[str, int | str]` copied into a `FrozenDict`, so a spec cannot be a nested
object and must be carried as a JSON *string*.
`check: python -c "import pytest; from pydantic import ValidationError; from deepreason.ontology import Commitment; from deepreason.ontology.commitment import Budget; from deepreason.frozen import FrozenDict; assert set(Commitment.model_fields)=={'id','eval','budget','observation_valued'} and Commitment.model_fields['eval'].annotation is str; assert not dict(Commitment.__pydantic_decorators__.field_validators) and not dict(Commitment.__pydantic_decorators__.model_validators); assert Commitment(id='k', eval='not-a-kind').eval=='not-a-kind'; assert set(Budget.__pydantic_decorators__.field_validators)=={'_freeze_extra'} and type(Budget(extra={'a':1}).extra) is FrozenDict; pytest.raises(ValidationError, Budget, extra={'spec': {'entry': 'f'}})" && grep -q '# "program:<ref>" | "rubric:<spec-id>" | "predicate:<expr>"' src/deepreason/ontology/commitment.py`

Because the ontology admits any `eval`, every path that turns UNTRUSTED text into
one has to guard itself. There are two, and they are not the same guard:
`ForbiddenCase._eval_kind_is_safe` is a prefix check that bans `predicate:` and
admits any program name (an unregistered one compiles into an inert,
never-evaluable criterion), while `Countercondition.eval` is a regex that also
constrains the character set and is followed by a `PROGRAMS` membership check at
draft time.
`check: python -c "import pytest; from pydantic import ValidationError; from deepreason.informal.skeleton import ForbiddenCase, forbidden_commitment; from deepreason.workloads.text import Countercondition; from deepreason.ontology import Commitment; from deepreason import programs; assert Commitment(id='k', eval='predicate:1==1').eval=='predicate:1==1'; pytest.raises(ValidationError, ForbiddenCase, case='c', eval='predicate:1==1'); pytest.raises(ValidationError, ForbiddenCase, case='c', eval='nonsense'); pytest.raises(ValidationError, Countercondition, case='c', eval='predicate:1==1'); k=forbidden_commitment(ForbiddenCase(case='c', eval='program:not-registered')); assert programs.evaluable(k) is False and k.id.startswith('fc:')" && grep -q "def _eval_kind_is_safe(cls, v: str) -> str:" src/deepreason/informal/skeleton.py && grep -q 'raise ValueError(f"countercondition uses unknown program: {program}")' src/deepreason/workloads/text.py`

The commitment half of purity, which the ontology does not supply: nine mint
sites hash the canonical spec into the id, so identical parameters reconstruct a
byte-identical `Commitment` and different parameters cannot share one. D2 rev 2
added the ninth, `oracle.py::candidate_checker_commitment` — the SAME
`sha256_hex(canonical_json(spec))[:12]` convention, over a `{source, entry,
tests, step_limit}` spec rather than `{entry, tests, ...}`, since the carrying
artifact's own content is prose, never the candidate under test.
`check: python -c "import json; from deepreason.oracle import exec_oracle_commitment; a=exec_oracle_commitment('f',[[[1],1]]); b=exec_oracle_commitment('f',[[[1],1]]); c=exec_oracle_commitment('f',[[[2],2]]); assert a==b and a.id!=c.id and a.id.startswith('exec-oracle@') and json.loads(a.budget.extra['spec'])['tests']==[[[1],1]]" && test "$(grep -c 'sha256_hex(canonical_json' src/deepreason/oracle.py)" -eq 7 && test "$(grep -c 'sha256_hex(canonical_json' src/deepreason/measures/hv.py)" -eq 1 && test "$(grep -c 'sha256_hex(canonical_json' src/deepreason/informal/skeleton.py)" -eq 1 && python -c "from deepreason.oracle import _load_spec; from deepreason.ontology.commitment import Budget; assert [_load_spec(b) for b in (None, Budget(), Budget(extra={'other': 1}), Budget(extra={'spec': 'not json'}), Budget(extra={'spec': '{}'}))]==[{}]*5 and _load_spec(Budget(extra={'spec': '{\"a\": 1}'}))=={'a': 1}"`

## Where it is expressed

| Site | File | Symbol | What it enforces |
|---|---|---|---|
| The address | `ontology/artifact.py` | `Artifact.compute_id` | what a verdict is a pure function OF: `(content_ref, codec, interface)`; `provenance` and `warrants` are outside it |
| The verdict door | `programs.py` | `evaluate` | reads those three fields and no other; returns `(verdict, trace)` and never touches the record |
| The bytes | `programs.py` | `content_text` | `inline:` prefix, else a bare 64-hex blob ref; anything else, or a missing blob, is `""` |
| Grammar, declared | `ontology/commitment.py` | `Commitment.eval` (a comment) | the three spellings — documented, unvalidated |
| Grammar, enforced | `programs.py` | `evaluable`, `evaluate`, `NotEvaluable` | the only parser; `rubric:` and unknown `program:` refuse, every `predicate:` is admitted |
| Grammar, untrusted | `informal/skeleton.py` | `ForbiddenCase._eval_kind_is_safe` | model-authored eval may not be a `predicate:` — the ontology would have taken it |
| Grammar, untrusted (2) | `workloads/text.py` | `Countercondition.eval` pattern | the same job, tighter: charset regex plus a `PROGRAMS` membership check in `draft_countercondition_commitments` |
| Frozen-spec channel | `ontology/commitment.py` | `Budget.extra`, `_freeze_extra` | `Mapping[str, int \| str]`, copied into a `FrozenDict` at validation |
| Spec load | `oracle.py` | `_load_spec` | `json.loads(budget.extra.get("spec", "{}"))` under a guarding `except`; unparseable OR absent yields `{}`, which every adapter turns into `overrun` |
| Commitment content address | `oracle.py`, `measures/hv.py`, `informal/skeleton.py` | `sha256_hex(canonical_json(spec))` in the id | the half of purity the ontology does not provide; eight sites |
| Off-record evaluation | `measures/hv.py` | `Artifact(id="", ...)` in `_text_vector`, `_survival` | an HV variant is evaluated without ever being addressed, registered or replayed |
| Interface as content | `programs.py`, `manifest.py` | `_lineage_ref`, `component_wf` | the only two programs that read the artifact object, and only `interface.refs` |
| Verdict vocabulary | `programs.py`, `oracle.py` | `PASS, FAIL, OVERRUN` | three bare strings that coincide with `ontology.Verdict` by value and import it nowhere |
| Verdict on record | `ontology/warrant.py` | `Warrant.verdict`, `Warrant.trace_ref` | the literal `"fail"` plus a blob digest of the trace |
| Trace address | `rules/crit.py`, `storage/blobs.py` | `harness.blobs.put(canonical_json(trace))`, `sha256_hex(data)` | why no wall-clock may enter a trace |
| Determinism at the process edge | `oracle_sandbox.py` | `PYTHONHASHSEED=0`, `_cpu_seconds`, `WALL_GRACE_SECONDS` → `SandboxAborted` | the one wall-clock in the stack, and it can only produce `overrun` |

Registration keeps the two records honest in the only way it can — by refusing a
second record under an id already taken — and the ontology's own immutability does
the rest. `register_commitment` computes nothing: it does not re-derive the spec
digest, does not call `evaluable`, and does not look at `eval` at all.
`check: python -c "import inspect, tempfile, shutil, pytest; from deepreason.harness import Harness, WellFormednessError; from deepreason.ontology import Commitment; from deepreason.ontology.commitment import Budget; s=inspect.getsource(Harness.register_commitment); assert 'canonical_json' not in s and 'compute_id' not in s and 'evaluable' not in s and 'eval' not in s; d=tempfile.mkdtemp(); h=Harness(d); liar=Commitment(id='exec-oracle@deadbeefdead', eval='program:exec_oracle', budget=Budget(extra={'spec': '{}'})); assert h.register_commitment(liar).id==liar.id and h.register_commitment(liar).id==liar.id; pytest.raises(WellFormednessError, h.register_commitment, Commitment(id='exec-oracle@deadbeefdead', eval='program:json-wf')); shutil.rmtree(d)"`

`content_text` is the whole bytes-resolution rule and it has exactly two accepting
shapes. It also never consults `codec`: the decode is UTF-8 with replacement for
every artifact, and `codec` reaches the evaluation only as a value in the predicate
namespace.
`check: python -c "import inspect, pathlib, tempfile, shutil; from deepreason.storage.blobs import BlobStore; from deepreason.ontology import Artifact, Interface, Provenance; from deepreason import programs; assert 'codec' not in inspect.getsource(programs.content_text); d=tempfile.mkdtemp(); b=BlobStore(d); ref=b.put(b'X'); mk=lambda r: Artifact(id='x', content_ref=r, codec='utf8', interface=Interface(), provenance=Provenance(role='seed')); assert programs.content_text(mk('inline:hi'), None)=='hi' and programs.content_text(mk(ref), b)=='X'; assert [programs.content_text(mk(r), b) for r in ('sha256:'+ref, 'blob:'+ref, 'inline:', '0'*64)]==['','','','']; from deepreason.ontology import Commitment; V=lambda e: programs.evaluate(Commitment(id='k', eval=e), mk('sha256:'+ref), b)[0]; assert (V('predicate:len(content)==0'), V('program:json-wf'))==('pass','fail'); Q=chr(34); A=pathlib.Path('src/deepreason/llm/adapter.py').read_text(); assert Q+'sha256:'+Q+' + ' not in A and 'f'+Q+'sha256:{' not in A; shutil.rmtree(d)" && grep -q 'decode("utf-8", errors="replace")' src/deepreason/programs.py && test "$(grep -c codec src/deepreason/programs.py)" -eq 1 && grep -q '"sha256:" + sha256_hex(' src/deepreason/capabilities/models.py && grep -q '"sha256:" + sha256_hex(' src/deepreason/conjecture_events.py && grep -q 'f"sha256:{digest}"' src/deepreason/scratch/service.py`

Trace determinism, end to end: the trace key set is fixed, two evaluations
canonicalize to the same bytes, and that canonical JSON is what becomes the blob
digest a warrant points at.
`check: python -c "from deepreason.canonical import canonical_json; from deepreason import programs; from deepreason.ontology import Artifact, Commitment, Interface, Provenance; a=Artifact(id='x', content_ref='inline:hello', codec='utf8', interface=Interface(), provenance=Provenance(role='seed')); k=Commitment(id='k', eval='predicate:len(content)==5'); t1=programs.evaluate(k,a,None)[1]; t2=programs.evaluate(k,a,None)[1]; assert set(t1)=={'commitment','eval','verdict'} and canonical_json(t1)==canonical_json(t2)" && grep -q "trace_ref=harness.blobs.put(canonical_json(trace))," src/deepreason/rules/crit.py && grep -q "ref = sha256_hex(data)" src/deepreason/storage/blobs.py`

## What is deliberately absent

**No verdict reads either of the two fields outside the address.** `provenance`
and `warrants` are excluded from `compute_id` on the ontology side and from every
program path on the evaluation side; if they were not, two artifacts sharing an id
could disagree about a criterion and the address would stop determining the
verdict. The boundary is exactly five reads, all named below and none of them on a
verdict path: three `problem.provenance` reads that rank the appellate docket, one
`artifact.provenance.role` read that orders user rulings first inside a precedent
pack, one `target.provenance.school` read in the trial's same-school critic guard,
plus one `harness.warrants` map lookup that is not an artifact field at all. In the
same sweep, `Commitment.observation_valued` reaches no verdict either: the only
`observation_valued` reads on this side are on a `ForbiddenCase` at mint time. It
decides whether a research problem is spawned (`rules/spawn.py`), never what a
program says.
`check: python -c "import ast,pathlib; F=[pathlib.Path(p) for p in ('src/deepreason/programs.py','src/deepreason/oracle.py','src/deepreason/oracle_sandbox.py','src/deepreason/manifest.py','src/deepreason/workloads/text.py')]+[p for d in ('measures','informal') for p in pathlib.Path('src/deepreason').joinpath(d).rglob('*.py')]; G=lambda names: sorted((p.name, ast.unparse(n)) for p in F for n in ast.walk(ast.parse(p.read_text())) if isinstance(n,ast.Attribute) and n.attr in names); assert G({'provenance','warrants'})==[('appellate.py','problem.provenance')]*3+[('audits.py','harness.warrants'),('standards.py','artifact.provenance'),('trial.py','target.provenance')], G({'provenance','warrants'}); assert G({'observation_valued'})==[('skeleton.py','case.observation_valued')]*2, G({'observation_valued'})" && grep -q "if kappa is None or not kappa.observation_valued:" src/deepreason/rules/spawn.py && grep -q "critic_school_id == target.provenance.school" src/deepreason/informal/trial.py`

**`evaluate` never reads `artifact.id`.** That is what makes the HV variator
possible: `_text_vector` and `_survival` build `Artifact(id="", ...)` per edit and
evaluate the whole battery against records that are never registered, never
addressed and never replayed. An `id` read here — a memo key, a log line, a
dedupe — would silently collapse every variant onto one identity, and the failure
would look like an HV score rather than a bug. Covered by the attribute check in
"The agreement"; the positive counterpart is that both id-less constructions still
exist.
`check: test "$(grep -c 'id="",' src/deepreason/measures/hv.py)" -eq 2 && grep -q "def _text_vector(harness, battery: list\[str\], text: str) -> tuple:" src/deepreason/measures/hv.py && grep -q "def _survival(harness, artifact, text, battery, edits, embedder)" src/deepreason/measures/hv.py`

**`Budget.steps` and `Budget.time_ms` are read by nothing in the tree.** Both are
declared, defaulted, serialized into every recorded commitment — and never
consulted. `time_ms` is dead on purpose: honouring a millisecond budget would make
a verdict a function of the machine, which is the one thing §0 forbids, and
`test_program_verdict_trace_is_deterministic` pins that `time_ms=0` still yields
`pass`. `steps` is dead by supersession: every real bound is
`extra["spec"]["step_limit"]`, which is inside the commitment's content address,
whereas `Budget.steps` is not part of any spec digest. Reading either one back into
the evaluator is the change this absence exists to stop.
`check: python -c "import ast,pathlib; hits=[(str(p),n.lineno,ast.unparse(n)) for p in pathlib.Path('src/deepreason').rglob('*.py') for n in ast.walk(ast.parse(p.read_text())) if isinstance(n,ast.Attribute) and n.attr in ('steps','time_ms')]; assert hits==[], hits; from deepreason.ontology.commitment import Budget; assert set(Budget.model_fields)=={'steps','time_ms','extra'} and Budget.model_fields['steps'].default==100_000 and Budget.model_fields['time_ms'].default==2_000" && grep -q "_STEP_LIMIT_DEFAULT = 100_000" src/deepreason/oracle.py`

**No wall-clock and no randomness on the pure path, and the one clock that does
exist can only produce `overrun`.** `programs.py` and `oracle.py` import no clock
and no entropy source AT ANY NESTING DEPTH — not `time`, `random`, `datetime`,
`secrets`, `uuid` or `importlib`, and never through `__import__`. The check walks
the AST rather than grepping line starts, because a function-local
`import time as _t` followed by `_t.monotonic()` passes every textual pattern a
module-level grep can express. The sole timing construct in the whole stack is
the sandbox's `cpu_seconds + WALL_GRACE_SECONDS` watchdog, whose only outcome is
`SandboxAborted` → `_sandbox_abort_verdict` → `overrun`, a verdict from which no
warrant may be minted. So machine availability can make a verdict *unavailable*
but can never flip `pass` to `fail`, and `Warrant.verdict`, which is only ever
`"fail"`, is never timing-dependent.
`check: python -c "import ast,pathlib; BAD={'time','random','datetime','secrets','uuid','importlib'}; hits=[(f,n.lineno,ast.unparse(n)) for f in ('src/deepreason/programs.py','src/deepreason/oracle.py') for n in ast.walk(ast.parse(pathlib.Path(f).read_text())) if (isinstance(n,ast.Import) and any(a.name.split('.')[0] in BAD for a in n.names)) or (isinstance(n,ast.ImportFrom) and (n.module or '').split('.')[0] in BAD) or (isinstance(n,ast.Call) and isinstance(n.func,ast.Name) and n.func.id=='__import__')]; assert hits==[], hits" && grep -q "timeout=cpu_seconds + WALL_GRACE_SECONDS" src/deepreason/oracle_sandbox.py && python -c "from deepreason.oracle import _sandbox_abort_verdict, OVERRUN; from deepreason.oracle_sandbox import SandboxAborted; v,d=_sandbox_abort_verdict(SandboxAborted('watchdog')); assert (v, sorted(d))==(OVERRUN, ['error','sandbox_abort'])"`

**The ontology never crosses the sandbox boundary.** `oracle_sandbox.py` imports
`deepreason.canonical` and (worker-side, function-locally) `deepreason.oracle`, and
nothing else from the package — no `Artifact`, no `Commitment`, no `Budget`.
Untrusted code receives canonical JSON and returns canonical JSON; it cannot be
handed a record, so it cannot mutate one, mis-address one, or learn who authored
the content it is running. `PYTHONHASHSEED=0` in the worker environment is the
other half: without it, set and dict iteration order in untrusted source would make
the verdict a function of the process.
`check: python -c "import ast,pathlib; t=ast.parse(pathlib.Path('src/deepreason/oracle_sandbox.py').read_text()); mods={n.module for n in ast.walk(t) if isinstance(n,ast.ImportFrom) and n.module}|{a.name for n in ast.walk(t) if isinstance(n,ast.Import) for a in n.names}; assert {m for m in mods if m.startswith('deepreason')}=={'deepreason.canonical','deepreason.oracle'}, sorted(mods)" && grep -q 'PYTHONHASHSEED": "0"' src/deepreason/oracle_sandbox.py && grep -q "This module has no epistemic policy" src/deepreason/oracle_sandbox.py && grep -q "from deepreason.oracle import _LOCAL_OPERATIONS" src/deepreason/oracle_sandbox.py`

**`ontology.Verdict` is not the verdict vocabulary, and evaluation would not be
improved by making it so.** `programs.py` and `oracle.py` each define
`PASS, FAIL, OVERRUN` as bare strings that coincide with the enum's values;
`Verdict` is exported from nowhere and imported by nothing, and `Warrant.verdict`
is a plain `str | None` that `register_fail_warrant` fills with the literal
`"fail"`. The strings are on-record in every existing root, so typing the field is
a change to recorded shapes rather than a cleanup (`DR-INV-frozen-surfaces`,
surface 3).
`check: python -c "import deepreason.ontology as o; from deepreason.ontology.commitment import Verdict; from deepreason.ontology import Warrant; from deepreason import programs, oracle; assert (programs.PASS, programs.FAIL, programs.OVERRUN)==('pass','fail','overrun')==tuple(v.value for v in Verdict); assert (oracle.PASS, oracle.FAIL, oracle.OVERRUN)==(programs.PASS, programs.FAIL, programs.OVERRUN); assert 'Verdict' not in o.__all__ and not hasattr(o,'Verdict'); assert Warrant.model_fields['verdict'].annotation==(str|None)" && python -c "import re, pathlib; F=[pathlib.Path('src/deepreason/programs.py'), pathlib.Path('src/deepreason/oracle.py')]+sorted(p for d in ('measures','informal') for p in pathlib.Path('src/deepreason').joinpath(d).rglob('*.py')); assert len(F)>=13, len(F); hits=[(p.name, i, l.strip()) for p in F for i, l in enumerate(p.read_text().split(chr(10)), 1) if re.search(r'\bVerdict\b', l)]; assert hits==[], hits" && grep -q 'verdict="fail",' src/deepreason/rules/warrants.py`

**Thirteen of the ontology's exported names never reach this side, and they are
exactly the log machinery.** Fourteen import statements bring in twelve names —
`Artifact`, `Commitment`, `Budget`, `Interface`, `Ref`, `RefRole`, `Provenance`,
`Warrant`, `WarrantType`, `Rule`, `Status`, `SpawnTrigger`. Absent are `Event`,
`StateDiff`, `EpistemicState`, `LLMCall`, `LLMAttempt`, the SIX typed process
payloads (three `ControlEventPayload` versions, the two conjecture receipts, and
`SchoolRouteReceiptV1`), and `Problem`/`ProblemProvenance`. Evaluation therefore
cannot author a log line, cannot describe a state delta, and cannot construct
the materialized view it reads: it names a `Rule` and calls a harness method,
and it reads
`harness.state` duck-typed. Even `informal/appellate.py`, which causes problems to
exist, goes through `rules.spawn` rather than building a `Problem`.
`check: python -c "import ast,pathlib; import deepreason.ontology as o; F=[pathlib.Path(p) for p in ('src/deepreason/programs.py','src/deepreason/oracle.py','src/deepreason/oracle_sandbox.py')]+[p for d in ('measures','informal') for p in pathlib.Path('src/deepreason').joinpath(d).rglob('*.py')]; I=[n for p in F for n in ast.walk(ast.parse(p.read_text())) if isinstance(n,ast.ImportFrom) and (n.module or '').startswith('deepreason.ontology')]; N={a.name for n in I for a in n.names}; assert len(I)==14, len(I); assert N-set(o.__all__)=={'RefRole'}, sorted(N); assert set(o.__all__)-N=={'ConjectureContextCallReceiptV1','ConjectureTurnEventPayloadV1','ControlEventPayloadV1','ControlEventPayloadV2','ControlEventPayloadV3','EpistemicState','Event','LLMAttempt','LLMCall','Problem','ProblemProvenance','SchoolRouteReceiptV1','StateDiff'}, sorted(set(o.__all__)-N)"`

## How to change it

The two sides fail at different times — the ontology at construction, evaluation
at `evaluate` — and the first question is always which of the two content
addresses your change moves: the artifact's, which the ontology owns, or the
commitment's, which the evaluation side manufactures.

1. **Read `DR-INV-frozen-surfaces` first.** Both record formats this seam joins
   are frozen surfaces. Changing what `compute_id` covers re-addresses every
   artifact in every root; changing `Budget`'s field set changes the bytes of every
   recorded commitment. Neither is a design question once roots exist.
2. **A new program parameter goes in `budget.extra` and into the id digest, in
   that order and in one commit.** `extra` only admits `int | str`, so a structured
   spec is a canonical JSON string; the mint site must hash the same object it
   serializes, or two commitments with different behaviour share an id and the
   second registration raises `WellFormednessError` at a site that has nothing to
   do with the change.
3. **A new `eval` kind is three edits, not one.** The `partition(":")` branch in
   `evaluate`, the matching clause in `evaluable`, and a decision in
   `measures/reach.py::_substantive` about whether it is substantive
   (`DR-SEAM-evaluation-x-rules`). Do NOT add a validator to `Commitment.eval` to
   "make the grammar real": every root on disk contains eval strings that were
   never validated, and a validator runs on reopen.
4. **Anything a program needs to read must be inside the address.** Adding a read
   of `provenance`, `warrants` or `id` makes the verdict a function of something
   the id does not cover, which means a replay can legitimately disagree with the
   record. If the fact genuinely belongs to the artifact, it belongs in
   `interface` — which is addressed, and which `lineage_ref` already demonstrates
   reading.
5. **Never let a clock or a random source into a verdict or a trace.** The trace is
   canonicalized into a blob whose digest a warrant carries; one timestamp forks
   two identical runs' logs. If you need a resource bound, express it as a
   deterministic count (`step_limit`) that rides in the hashed spec, and map its
   exhaustion to `overrun` rather than `fail`.
6. **Untrusted text becoming an `eval` string needs its own guard.** The ontology
   will not stop it. There are two such guards today and they differ; a third
   surface that admits model-authored evals needs an explicit decision about
   `predicate:`, not an inherited one.

What breaks first, cheapest to most expensive: a pydantic `ValidationError` at
construction, or `NotEvaluable` at the first `evaluate` call; then
`tests/test_ontology.py` and `tests/test_security.py`, both of which run in under a
second and pin the address and the predicate sandbox respectively; then
`tests/test_review_fixes.py` for the determinism pins; then `tests/test_oracle.py`
and `tests/test_hv.py`, where the spec digest and the off-record variant path get
exercised end to end; then `tests/test_replay.py` and
`tests/test_persistence_invariants.py`, which is where a shape change stops being a
design question and becomes a broken root.

`check: python -m pytest "tests/test_review_fixes.py::test_program_verdict_trace_is_deterministic" "tests/test_review_fixes.py::test_skeleton_id_includes_observation_valued" "tests/test_budget.py::test_predicate_comprehensions_work" "tests/test_ontology.py::test_compute_id_deterministic_and_content_sensitive" "tests/test_ontology.py::test_commitment_defaults" tests/test_security.py -q`

## Traps

- **A malformed `predicate:` is a REFUTATION, not an error.** `evaluable` is purely
  syntactic on that branch: anything after `predicate:` is "machine-decidable".
  `evaluate` then catches every exception from `_validate_predicate` and `eval` —
  including `UnsafePredicate` — and returns `fail` with the error in the trace. So
  `predicate:))` and `predicate:` fail against every artifact that carries them, and
  a critic evaluating that criterion mints a demonstrative warrant from a typo. The
  contrast with the other machine kind is total: `program:nope` is `evaluable=False`
  and raises. Pinned by the grammar check in "The agreement".
- **`codec` is data, never a decoder.** `content_text` decodes UTF-8 with
  `errors="replace"` for every artifact regardless of the codec it declares, and
  passes the codec string into the predicate namespace as a value. An artifact
  declaring `f64le` or `raw` reaches its criterion as mojibake, and `len(content)`
  counts replacement characters. This is consistent with untypedness — meaning is
  imposed by the program, not by a field — but it means "the codec says binary" is
  never a reason a program did not see the bytes.
- **Two blob-reference spellings coexist and only one resolves.** `BlobStore._path`
  accepts a bare 64-hex digest and raises `KeyError` for everything else;
  `content_text` swallows that `KeyError` and returns `""`. Meanwhile the prefixed
  `sha256:<hex>` spelling is live and widespread — `capabilities/models.py`,
  `capabilities/state.py`, `conjecture_events.py`, `scratch/service.py` and
  `workflow/` all mint it. (`llm/adapter.py` does NOT: it only matches work-order
  ids against `sha256:[0-9a-f]{64}`, so it reads the spelling and never sources
  one.) An `Artifact.content_ref`
  carrying the prefixed form evaluates as the empty string with full confidence:
  `predicate:len(content)==0` passes, `program:json-wf` fails, and nothing anywhere
  reports a missing blob. The same swallow is what lets sealed holdout evidence
  render safely, so it is not removable — see `DR-SUB-evaluation`.
- **A commitment id that lies about its spec is undetectable.** The ontology does
  not address a commitment, and `register_commitment` re-derives nothing: it
  compares whole records under an id already present and is otherwise content with
  `exec-oracle@deadbeefdead` carrying an unrelated spec. The eight
  `sha256_hex(canonical_json(spec))` mint sites are the entire guarantee, exactly as
  the two `Artifact.compute_id` calls in `rules/` are the entire guarantee on the
  artifact side (`DR-SEAM-ontology-x-rules`). A hand-built commitment in a test
  fixture or an operator script bypasses it completely.
- **Registration dedupes by id, so anything that distinguishes two commitments must
  be IN the id.** Recorded near-miss: `forbidden_commitment` hashes `case`, `eval`
  AND `observation_valued`, because without the third an
  `observation_valued=False` case registered first would mask a later `True` one and
  silently suppress the §12 research spawn — a field the evaluator ignores changing
  behaviour through the id rather than through a verdict.
  `test_skeleton_id_includes_observation_valued` exists for this.
- **Reading the model and not the mint site.** `Commitment` looks permissive and is:
  the `eval` grammar, the spec digest, the step bound and the safety of untrusted
  eval text are all enforced one package away, by `programs.py`, `oracle.py`,
  `informal/skeleton.py` and `workloads/text.py`. Concluding "the ontology allows
  it" says nothing about whether any path can produce it. This is the same mistake
  `DR-INV-frozen-surfaces` records for the manifest — model versus validator — in a
  different package.
