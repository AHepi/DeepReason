<!-- DR-SEAM-ontology-x-rules -->
Verified-at: 08dcdf3c
Verify: python tools/docs_verify.py
Owns: src/deepreason/ontology/artifact.py, src/deepreason/ontology/problem.py, src/deepreason/ontology/event.py, src/deepreason/frozen.py, src/deepreason/rules/spawn.py, src/deepreason/rules/synth.py
Sides: DR-SUB-ontology, DR-SUB-rules

# ontology x rules

## The agreement

The ontology lends the rules a vocabulary and keeps the right to define it. A
rule may bring seven of the ontology's models into existence — `Artifact`,
`Interface`, `Ref`, `Provenance`, `Warrant`, `Problem`, `ProblemProvenance` — and
may read five of its enums. `Commitment`, `Budget`, `Event`, `StateDiff`,
`LLMCall` and `EpistemicState` are shapes a rule registers, reads or is handed;
never shapes it authors. In return the ontology promises that a validated
record is what it says it is permanently: every record model is a
`FrozenRecord` — `EpistemicState` is the single exception, and it is a
materialized view rather than a record — every sequence and mapping on a record
is *copied* into a `FrozenList`/`FrozenDict` at validation, and an artifact's
`id` is the sha256 of
`(content_ref, codec, interface)` — so what a rule proposed cannot drift after
it proposed it. The prices are symmetric and both are load-bearing. Because the
address covers content and not provenance or carriage, a rule cannot change what
an artifact SAYS without minting a different artifact, and cannot re-stamp who
said it without minting the same one. Because the vocabulary is closed enums —
`RefRole`, `ProvenanceRole`, `SpawnTrigger`, `WarrantType`, `Rule` — a rule that
wants a new kind of move must widen the ontology first, where every root on disk
can be checked against the widening. And because the ontology validates shape
and never reference, all resolution is the rules' problem: which commitment ids
are real, which artifact ids exist, which criteria a candidate inherits.

The dependency is one-way and every write goes through a harness method; nothing
in `rules/` touches the object store, appends to the log, or builds an `Event`.
`check: ! grep -rqE "register_artifact\(|objects\.put\(|log\.append|_commit\(" --include=*.py src/deepreason/rules/ && ! grep -rq "deepreason\.rules" --include=*.py src/deepreason/ontology/ && grep -q "class Artifact(FrozenRecord):" src/deepreason/ontology/artifact.py && grep -q "def register_artifact(" src/deepreason/harness.py && grep -q 'self.objects.put("artifact", artifact)' src/deepreason/harness.py && grep -q "harness.log.read()" src/deepreason/rules/crit.py`

Twelve ontology names reach `rules/` — the seven models above plus `RefRole`,
`Rule`, `SpawnTrigger`, `Status`, `WarrantType` — and the thirteen that do not
are the log line, the process payloads, the materialized view and the test
vocabulary.
`check: python -c "import ast,pathlib; N={a.name for p in pathlib.Path('src/deepreason/rules').rglob('*.py') for n in ast.walk(ast.parse(p.read_text())) if isinstance(n,ast.ImportFrom) and (n.module or '').startswith('deepreason.ontology') for a in n.names}; import deepreason.ontology as o; assert N-set(o.__all__)=={'RefRole'}, sorted(N); assert set(o.__all__)-N=={'Budget','Commitment','ConjectureContextCallReceiptV1','ConjectureTurnEventPayloadV1','ControlEventPayloadV1','ControlEventPayloadV2','ControlEventPayloadV3','EpistemicState','Event','LLMAttempt','LLMCall','SchoolRouteReceiptV1','StateDiff'}, sorted(set(o.__all__)-N)"`

## Where it is expressed

| Site | File | Symbol | What it enforces |
|---|---|---|---|
| Content address | `ontology/artifact.py` | `Artifact.compute_id` | id = sha256 over canonical JSON of `(content_ref, codec, interface)`; `provenance` and `warrants` are outside it |
| The mint door | `harness.py` | `create_artifact` | computes the id on the rule's behalf — the twelve rules-side call sites never see an `id` parameter |
| Two-phase build, conjecture | `rules/conj.py` | `Artifact(id=Artifact.compute_id(content_ref, "utf8", interface), ...)` | the id must exist before registration: occurrence keys, relapse domains and work-order effect refs are all keyed by it |
| Two-phase build, synthesis | `rules/synth.py` | same construction | the anti-relapse gate runs on the built artifact and may refuse it, so no registry state may move first |
| Re-stamp without re-address | `rules/conj.py` | `artifact.model_copy(update={"provenance": ...})` | `FrozenRecord` forbids assignment; provenance is outside the address, so the copy keeps the id |
| Sequence capture | `ontology/artifact.py`, `ontology/problem.py` | `_freeze_sequences`, `_freeze_warrants`, `_freeze_criteria`, `_freeze_sources` | the plain list a rule hands in is copied into a `FrozenList`; the rule's local list stops being the record |
| Interface admission | `harness.py` | `register_batch`, `interface commitment not registered` | a candidate may not name a κ that is not on the record |
| Interface compilation | `workloads/models.py` ← `rules/conj.py` | `compile_interface_draft` | the problem's criteria plus harness-owned mandatory commitments become the candidate's attack surface; unresolvable optional refs are dropped, drafts stay unregistered until admission |
| Commitment door | `rules/{conj,crit,spawn,experiment}.py` | `harness.register_commitment` | ten sites, every one registering a κ minted in `oracle.py`, `measures/hv.py`, `unification/isolation.py`, `informal/skeleton.py` or `workloads/text.py` — the last two reach `conj` as unregistered drafts through `compile_interface_draft` |
| Problem mint | `rules/spawn.py` | `spawn` → `Problem` + `ProblemProvenance.model_validate({"trigger": ..., "from": ...})` | the on-record alias spelling, and one of the nine `SpawnTrigger` values |
| Problem mint, evidence-first | `rules/act.py` | the same pair with `trigger: "research"` | `addr` pairs only record against registered problems, so `act` registers the problem `scan_spawns` would have minted later |
| Battery pinning | `harness.py` | `register_problem` + `POPPER_BATTERY` | the criteria a rule passes are extended by the harness; a rule cannot decline the battery |
| Event tag, chosen | `rules/{conj,crit,warrants,experiment,synth,vision}.py` | `rule=Rule.CONJ`, `rule=Rule.CRIT` | the only two of fifteen `Rule` values any rule names |
| Event tag, implied | `harness.py` | `register_commitment`, `register_problem`, `record_measure`, `record_conjecture_turn_event`, `*_contract_decomposition` | `REGISTER`, `SPAWN`, `MEASURE`, `CONJECTURE_TURN`, `CONTROL` follow from the method called, not from the caller |
| Probation clock | `rules/experiment.py` | `Provenance(event_seq=harness._next_seq)` → `promoted_properties` | `event_seq` and `role` (`act`'s import-evidence filter) are the only two `Provenance` fields any rule reads back off the record |
| Read side | `ontology/state.py` | `harness.state` (`EpistemicState`, `Status`) | rules import `Status` and read the materialized view; they import `EpistemicState` nowhere and construct one at no site |

What a rule may build against what it may only register: two direct `Artifact`
constructions in `rules/`, both content-addressed, fifteen more artifacts through
the harness door that owns the address and exposes no `id` parameter — and ten
commitment registrations against zero commitment constructions. D2 rev 2 added
three of the fifteen (`rules/relatedness.py`: one in `mint_relatedness_claim`,
two in `relatedness_trial`'s ν+critic pair) but zero commitment registrations —
`candidate_checker` commitments register through `oracle.py`/`programs.py`
(evaluation side), never through a new `rules/` site.
`check: python -c "import ast,pathlib; C=[n for p in pathlib.Path('src/deepreason/rules').rglob('*.py') for n in ast.walk(ast.parse(p.read_text())) if isinstance(n,ast.Call) and isinstance(n.func,ast.Name) and n.func.id=='Artifact']; assert len(C)==2, len(C); assert all(any(k.arg=='id' and isinstance(k.value,ast.Call) and ast.unparse(k.value.func)=='Artifact.compute_id' for k in c.keywords) for c in C), [ast.unparse(c) for c in C]" && test "$(grep -rn "harness.create_artifact(" --include=*.py src/deepreason/rules/ | wc -l)" -eq 15 && grep -q "id=Artifact.compute_id(content_ref, codec, interface)," src/deepreason/harness.py && ! grep -rq "harness.register_artifact(" --include=*.py src/deepreason/rules/ && test "$(grep -rn "harness.register_commitment(" --include=*.py src/deepreason/rules/ | wc -l)" -eq 10 && ! grep -rqE "Commitment\(|Budget\(" --include=*.py src/deepreason/rules/ && grep -q "return Commitment(" src/deepreason/oracle.py && grep -q "Commitment(" src/deepreason/measures/hv.py && grep -q "Commitment(" src/deepreason/unification/isolation.py && grep -q "Commitment(" src/deepreason/informal/skeleton.py && grep -q "Commitment(" src/deepreason/workloads/text.py && grep -q "for commitment in draft_forbidden_commitments(skeleton):" src/deepreason/workloads/models.py && grep -q "compiled = tuple(draft_countercondition_commitments(envelope))" src/deepreason/rules/conj.py`

Seven of the fifteen `Rule` tags are reachable from `rules/`; two of those seven
are chosen by name and five follow from the harness method.
`check: python -c "import ast,pathlib,re; R=[ast.parse(p.read_text()) for p in pathlib.Path('src/deepreason/rules').rglob('*.py')]; m={n.func.attr for t in R for n in ast.walk(t) if isinstance(n,ast.Call) and isinstance(n.func,ast.Attribute) and isinstance(n.func.value,ast.Name) and n.func.value.id=='harness'}; s=open('src/deepreason/harness.py').read(); H=[x for x in ast.parse(s).body if isinstance(x,ast.ClassDef) and x.name=='Harness'][0]; tags={g for f in H.body if isinstance(f,ast.FunctionDef) and f.name in m for g in re.findall(r'Rule[.][A-Z_]+', ast.get_source_segment(s,f))}; chosen={'Rule.'+n.value.attr for t in R for n in ast.walk(t) if isinstance(n,ast.keyword) and n.arg=='rule' and isinstance(n.value,ast.Attribute)}; import deepreason.ontology as o; every={'Rule.'+r.name for r in o.Rule}; assert chosen=={'Rule.CONJ','Rule.CRIT'}, sorted(chosen); assert tags|chosen=={'Rule.CONJ','Rule.CRIT','Rule.REGISTER','Rule.SPAWN','Rule.MEASURE','Rule.CONJECTURE_TURN','Rule.CONTROL'}, sorted(tags|chosen); assert every-tags-chosen=={'Rule.ADJ','Rule.REFL','Rule.MERGE','Rule.REVEAL','Rule.RESEED','Rule.SCRATCH','Rule.BRIDGE','Rule.CAPABILITY'}, sorted(every-tags-chosen)" && ! grep -rq "Rule\.ADJ" --include=*.py src/deepreason/ && grep -q 'ADJ = "Adj"' src/deepreason/ontology/event.py`

Four rules-side sites stamp `event_seq`; `create_artifact` does not, and the
field defaults to 0. Only two `Provenance` fields are ever read back off the
record — `event_seq` for the probation clock and `role` for `act`'s
import-evidence filter — alongside the `ProblemProvenance` pair and the one
`model_copy` re-stamp.
`check: test "$(grep -rn "event_seq=harness._next_seq" --include=*.py src/deepreason/rules/ | wc -l)" -eq 4 && grep -q 'provenance=provenance or Provenance(role="user"),' src/deepreason/harness.py && python -c "from deepreason.ontology import Provenance; assert Provenance.model_fields['event_seq'].default == 0" && grep -q "harness.state.artifacts\[aid\].provenance.event_seq" src/deepreason/rules/experiment.py && grep -q 'artifact.provenance.role.value != "import"' src/deepreason/rules/act.py && python -c "import ast,pathlib; R=[ast.parse(p.read_text()) for p in pathlib.Path('src/deepreason/rules').rglob('*.py')]; A={n.attr for t in R for n in ast.walk(t) if isinstance(n,ast.Attribute) and isinstance(n.value,ast.Attribute) and n.value.attr=='provenance'}; assert A=={'event_seq','role','from_','trigger','model_copy'}, sorted(A)"`

Both problem mints construct the provenance through the on-record `from` alias,
and neither touches the battery the harness pins.
`check: test "$(grep -rn "ProblemProvenance.model_validate" --include=*.py src/deepreason/rules/ | wc -l)" -eq 2 && ! grep -rq "from_=" --include=*.py src/deepreason/rules/ && grep -q 'alias="from"' src/deepreason/ontology/problem.py && grep -q "problem.provenance.from_" src/deepreason/rules/synth.py && ! grep -rq "POPPER_BATTERY" --include=*.py src/deepreason/rules/ && grep -q "b for b in POPPER_BATTERY if b not in problem.criteria" src/deepreason/harness.py && python -c "import json; from deepreason.ontology import ProblemProvenance as P; from deepreason.ontology.problem import POPPER_BATTERY; assert POPPER_BATTERY == (); p=P.model_validate({'trigger':'research','from':['a']}); assert list(p.from_)==['a'] and json.loads(p.model_dump_json(by_alias=True))=={'trigger':'research','from':['a']}; assert list(P.model_validate({'trigger':'research','from_':['a']}).from_)==['a']"`

End to end on a committed root: engaged `run-f4fa6663` holds 69 artifacts whose
ids all re-derive to their own content, 29 critic artifacts at `event_seq` 0
against conjecturer artifacts that all carry a real seq, 820 events none of
which is an `Adj`, and problem ids that are prefix schemes rather than trigger
values.
    python -c "import collections; from deepreason.harness import Harness; from deepreason.ontology import Artifact, Rule; h=Harness('experiments/live_engaged_2026-07-27/run-f4fa6663e5412d64df943a5a22342baf', read_only=True); A=list(h.state.artifacts.values()); assert len(A)==69 and all(a.id==Artifact.compute_id(a.content_ref,a.codec,a.interface) for a in A); n=collections.Counter(a.provenance.role.value for a in A); assert n['critic']==29 and n['conjecturer']==36, n; byrole={}; [byrole.setdefault(a.provenance.role.value,set()).add(a.provenance.event_seq) for a in A]; assert byrole['critic']=={0} and len(byrole['conjecturer'])>1 and 0 not in byrole['conjecturer'], byrole; E=list(h.log.read()); tags={e.rule for e in E}; assert len(E)==820 and Rule.ADJ not in tags and {Rule.CONJ,Rule.CRIT,Rule.REGISTER,Rule.SPAWN,Rule.MEASURE}<=tags; assert {p.split(':')[0] for p in h.state.problems if ':' in p}=={'conn','disc','research','succ'}, sorted({p.split(':')[0] for p in h.state.problems})"

The behavioural half — schema round trips, the probation clock, and the two
spawn descriptions that inherit from a `Problem` a rule built.
`check: python -m pytest tests/test_ontology.py tests/test_properties.py::test_probationary_property_is_not_promoted tests/test_properties.py::test_control_receipts_do_not_advance_property_probation tests/test_chaos_invariants.py::test_successor_descriptions_do_not_nest tests/test_harness_fixes.py::test_remove_arbitrariness_carries_root_description_and_criteria tests/test_h1_no_spawn_from_refutation.py -q`

## What is deliberately absent

**A rule never authors a `Commitment`.** Ten sites in `rules/` register one and
none constructs one: the counterexample and property oracles come from
`oracle.py`, the hv floor from `measures/hv.py`, lineage and relation form from
`unification/isolation.py`, and the two draft families `conj` registers after
admission from `informal/skeleton.py` (forbidden cases) and
`workloads/text.py` (reasoning counterconditions), both threaded through
`compile_interface_draft` unregistered. A
commitment is the test that decides a verdict, so a rule that could mint one
could write the exam it is about to sit — `crit_program` would be able to attach
a κ that fails by construction, and `conj` one that passes by construction. The
absence is what makes `formally_backed`'s SUBSTANTIVE clause meaningful rather
than circular (`DR-SEAM-evaluation-x-rules`). Covered by the
build-against-register check above.

**A rule never authors an `Event`, a `StateDiff`, an `LLMCall` or an
`EpistemicState`.** None of the four is imported anywhere under `rules/`. A rule
describes a state delta by choosing which harness method to call, and the method
picks the `Rule` tag and builds the diff; the closest a rule comes to writing a
log line is naming `rule=Rule.CONJ` or `rule=Rule.CRIT`. This is why the whole
package is duck-typed on the harness and testable against a fake — see the
imported-names check above, and `DR-SUB-harness` for the write path.

**Four of the nine `ProvenanceRole` values are unreachable from `rules/`.** The
rules mint `conjecturer`, `critic`, `experimenter`, `import` and `synthesizer`.
`seed` and `user` belong to the operator's entry points, `controller` to
`controller.py`, `variator` to `measures/hv.py`. No rule can author a seed
artifact, which is what makes the operator's seed question a fixed point the
loop cannot manufacture more of.
`check: python -c "import ast,pathlib; R=[ast.parse(p.read_text()) for p in pathlib.Path('src/deepreason/rules').rglob('*.py')]; roles={k.value.value for t in R for n in ast.walk(t) if isinstance(n,ast.Call) and isinstance(n.func,ast.Name) and n.func.id=='Provenance' for k in n.keywords if k.arg=='role' and isinstance(k.value,ast.Constant)}; from deepreason.ontology.artifact import ProvenanceRole as P; assert roles=={'conjecturer','critic','experimenter','import','synthesizer'}, sorted(roles); assert {r.value for r in P}-roles=={'seed','user','controller','variator'}, sorted({r.value for r in P}-roles)" && grep -q 'Provenance(role="seed")' src/deepreason/easy.py && grep -q 'Provenance(role="controller")' src/deepreason/controller.py && grep -q 'Provenance(role="variator")' src/deepreason/measures/hv.py`

**`Provenance.school` is write-only from the rules' side, and only five of the
seventeen rules-side mints write it at all.** `conj`, `synth`, `crit`'s scrutiny
artifact and `register_fail_warrant`'s ν and critic stamp the conditioning
school; the vision critic's pair, all four `experiment` mints, D2 rev 2's three
`relatedness` mints (the claim, and `relatedness_trial`'s own ν+critic pair,
role `"conjecturer"`/`"critic"` only — never a school, the SAME shape
`relevance_trial`'s own mints already use) and all three
`act` evidence artifacts leave it `None`. No rule reads `provenance.school` back
under any circumstance. Routing, pack assembly, the trial's same-school guard and the
jolt signals all read it — the rules stamp it and forget it, which is what keeps
school membership out of every decision a rule makes about what to propose or
attack (`DR-CON-schools`). The `None`s are consequential rather than cosmetic:
`informal/trial.py` compares `critic_school_id` against the target's school, so
a school-less mint is never same-school.
`check: ! grep -rq "provenance\.school" --include=*.py src/deepreason/rules/ && python -c "import ast,pathlib; C=[n for p in pathlib.Path('src/deepreason/rules').rglob('*.py') for n in ast.walk(ast.parse(p.read_text())) if isinstance(n,ast.Call) and isinstance(n.func,ast.Name) and n.func.id=='Provenance']; w=[c for c in C if any(k.arg=='school' for k in c.keywords)]; assert (len(w), len(C))==(6,18), (len(w), len(C))" && grep -q 'provenance.school == school\["id"\]' src/deepreason/llm/packs.py && grep -q "critic_school_id == target.provenance.school" src/deepreason/informal/trial.py`

**No rule builds a `FrozenList` or a `FrozenDict`, and none imports
`deepreason.frozen`.** Freezing is a field validator's job on the ontology side,
and it *copies*: the plain list a rule passes to `Interface(refs=[...])` is not
the object that ends up on the record. So a rule may keep mutating its local
list after construction with no effect on what it built, and equally may not
reach into a record it built to change it. Immutability here is achieved by
copy-on-validate, not by convention on the calling side.
`check: ! grep -rqE "FrozenList|FrozenDict|deepreason\.frozen" --include=*.py src/deepreason/rules/ && grep -q 'refs=\[Ref(target=i, role="dependence")' src/deepreason/rules/synth.py && python -c "from deepreason.ontology import Interface, Ref; src=[Ref(target='a', role='mention')]; i=Interface(refs=src); src.append(Ref(target='b', role='mention')); assert len(i.refs)==1 and type(i.refs).__name__=='FrozenList' and i.refs is not src" && python -c "import inspect, pydantic; import deepreason.ontology as o; M=[(n, getattr(o,n)) for n in o.__all__ if inspect.isclass(getattr(o,n)) and issubclass(getattr(o,n), pydantic.BaseModel)]; assert {n for n,m in M if not m.model_config.get('frozen')}=={'EpistemicState'}, sorted(n for n,m in M if not m.model_config.get('frozen'))" && grep -q "def _freeze_sequences" src/deepreason/ontology/artifact.py`

**Nothing re-derives an artifact's content address after the rule computes it.**
`Artifact` accepts any id string; `register_batch` compares content only when
the id is already present (a collision), and `verify_root` never calls
`compute_id` at all. An artifact whose id is a valid address of *different*
content registers cleanly and replay-validates with zero violations. The
contrast is deliberate and visible one package away: `scratch/models.py` records
re-check `id == compute_id(...)` in a model validator, and the ontology's do
not. The two `compute_id` calls in `rules/` are therefore not a convenience —
they are the entire enforcement.
`check: python -c "import tempfile, shutil; from deepreason.harness import Harness; from deepreason.invariants import verify_root; from deepreason.ontology import Artifact, Interface, Provenance; d=tempfile.mkdtemp(); h=Harness(d); i=Interface(); liar=Artifact(id=Artifact.compute_id('inline:y','utf8',i), content_ref='inline:z', codec='utf8', interface=i, provenance=Provenance(role='conjecturer')); h.register_batch([(liar,[])]); assert liar.id != Artifact.compute_id(liar.content_ref, liar.codec, liar.interface); assert verify_root(d)['violations'] == []; shutil.rmtree(d)" && ! grep -q "compute_id" src/deepreason/invariants.py && grep -q "if self.id != self.compute_id" src/deepreason/scratch/models.py && grep -q "conflicts with its content identity" src/deepreason/harness.py`

**The ontology resolves no reference, and the two halves of an `Interface` are
guarded unequally.** `Interface.commitments` entries must be registered or
`register_batch` raises; `Ref.target` is an opaque string that nothing checks, so
a dangling `dependence` ref registers happily and `build_dep` simply skips it —
the ref survives on the record and contributes no edge. That asymmetry is why
all three hand-built `nu_interface`s in `rules/` name an artifact that is
already on the record — `act`'s the evidence it registered a few statements
earlier, `crit`'s the generator and the property it read back out of
`harness.state` — and why `compile_interface_draft` drops unresolvable optional
refs rather than raising. A reader who "fixes" the missing ref validation will
find that legitimate roots contain refs to artifacts that were never registered.
`check: python -c "import pytest, tempfile, shutil; from deepreason.harness import Harness, WellFormednessError; from deepreason.ontology import Interface, Provenance, Ref; d=tempfile.mkdtemp(); h=Harness(d); a=h.create_artifact('x', interface=Interface(refs=[Ref(target='nowhere', role='dependence')]), provenance=Provenance(role='critic')); assert h.state.dep==[] and h.state.artifacts[a.id].interface.refs[0].target=='nowhere'; pytest.raises(WellFormednessError, h.create_artifact, 'y', interface=Interface(commitments=['unregistered']), provenance=Provenance(role='critic')); shutil.rmtree(d)" && grep -q "interface commitment not registered: {cid}" src/deepreason/harness.py && grep -q "ref.role == RefRole.DEPENDENCE and ref.target in artifacts" src/deepreason/adjudication/edges.py && test "$(grep -rhoE "nu_interface ?= ?Interface\(" --include=*.py src/deepreason/rules/ | wc -l)" -eq 3 && grep -qF "nu_interface=Interface(refs=[Ref(target=evidence.id, role=RefRole.EVIDENCE)])," src/deepreason/rules/act.py && grep -qF "probes += [(gid, src) for gid, src in accepted_generators(harness, cid)]" src/deepreason/rules/crit.py && grep -qF "for prop_id, claim, prop_source in active_properties(harness, base.id):" src/deepreason/rules/crit.py`

**A `SpawnTrigger` value is never a problem id.** `spawn` derives
`f"{trigger.value}:..."` when no id is given, and no caller anywhere omits the
id: all seven `_spawn` sites in `scan_spawns` and both external callers pass
their own short prefix (`succ:`, `disc:`, `ra:`, `debt:`, `conn:`, `research:`,
`integ:`, `audit:`). The one prefix that coincides with a trigger value is
`research:`, and `act.browser_rid` hard-codes that spelling to match. The
consequence is narrow and worth stating exactly: a trigger's `.value` IS
on-record inside `ProblemProvenance.trigger`, but changing it moves no problem
id and breaks no `addr` pair.
`check: python -c "import ast,pathlib; s=pathlib.Path('src/deepreason/rules/spawn.py').read_text(); C=[n for n in ast.walk(ast.parse(s)) if isinstance(n,ast.Call) and isinstance(n.func,ast.Name) and n.func.id=='_spawn']; assert len(C)==6 and all(any(k.arg=='problem_id' for k in c.keywords) for c in C), len(C); X=[n for f in ('src/deepreason/informal/appellate.py','src/deepreason/capture/ladder.py') for n in ast.walk(ast.parse(open(f).read())) if isinstance(n,ast.Call) and isinstance(n.func,ast.Name) and n.func.id=='spawn']; assert len(X)==2 and all(any(k.arg=='problem_id' for k in c.keywords) for c in X), len(X)" && grep -q 'pid = problem_id or f"{trigger.value}' src/deepreason/rules/spawn.py && grep -q 'return f"research:{commitment_id}:{target_id\[:12\]}"' src/deepreason/rules/act.py`

**`Rule.ADJ` is emitted by nobody, in `rules/` or out of it.** Adjudication
writes no event of its own; the status changes it computes ride out on the
`status_changed` field of whatever registration event provoked them. So the
event a rule caused is also the adjudication record, and a reader looking for
"when was this refuted" must read `Crit`/`Conj` events, not an `Adj` event that
does not exist. Covered by the reachable-tags and committed-root checks above.

## How to change it

The two sides fail at different times — the ontology at validation, the rules at
registration — so the first question is which side owns your change.

1. **Read `DR-INV-frozen-surfaces` first.** The ontology's record formats are a
   frozen surface and this seam sits directly on it. Adding a field to `Artifact`
   or `Provenance`, or changing what `compute_id` covers, re-addresses every
   artifact in every root on disk. Adding an optional field to `Event` or
   `LLMCall` requires `exclude_if=lambda value: value is None` or the historical
   key set changes; `DR-SUB-ontology` holds that check.
2. **"A rule should be able to mint a new kind of record" is an ontology
   change first.** Widen the enum or add the model, add the harness door if the
   record persists, then teach the rule. Doing it in the other order produces a
   rule that constructs a record no reader can load, and the failure appears on
   reopen rather than on append.
3. **"A rule needs to record one more fact about an artifact" almost never
   belongs on `Artifact`.** Three places already absorb this without moving an
   address: the ν's `Interface` (`DR-SEAM-adjudication-x-rules`), the
   commitment's `budget.extra`, and a `Measure` event's `inputs`. All three are
   optional and already present in every root, so old roots keep replaying.
4. **If the new fact must live on the artifact, decide whether it is inside the
   address.** Inside (`content_ref`, `codec`, `interface`) means every existing
   artifact re-addresses and every recorded id becomes wrong. Outside
   (`provenance`, `warrants`) means the record changes and the id does not — that
   is the design, and it is why `conj` can re-stamp `event_seq` immediately before
   `register_batch` without disturbing the ids it already computed for the
   relapse domains.
5. **A new `ProvenanceRole`, `RefRole` or `SpawnTrigger` needs its consumer in
   the same commit.** A role nothing branches on is inert by design; a `RefRole`
   nothing branches on is silently a `mention` (`DR-SUB-ontology`); a
   `SpawnTrigger` with no `_spawn` branch never fires. And `adjudication/` must
   stay blind to `ProvenanceRole` — that blindness is the property, not an
   accident (`DR-CON-warrants-and-attacks`).
6. **Order within a rule:** build the record, run the gate, register the
   commitments it needs, then register the artifact. `synth` is the smallest
   example of the gate-first half — `Artifact(...)` → `anti_relapse.check` →
   `record_domain` → `register_batch` — and `conj` registers its admitted draft
   commitments in the statement before `register_batch`, because a blocked
   proposal must not have moved the commitment registry (RC5).

What breaks first, cheapest to most expensive: a `ValidationError` from pydantic
at construction; then `WellFormednessError: interface commitment not registered`
or `artifact id ... conflicts with its content identity` at registration; then
`tests/test_ontology.py`, which is hand-built and runs in under two seconds;
then `tests/test_properties.py` and `tests/test_experiment.py`, where the
probation clock and the generator lifecycle read provenance back; then
`tests/test_replay.py` and `tests/test_persistence_invariants.py`, which is
where a schema change stops being a design question and becomes a broken root.

## Traps

- **A content address that is not the address of its content is undetectable.**
  Registration catches only a collision, and `verify_root` reports zero
  violations on a root containing one — demonstrated by the check in "What is
  deliberately absent". The two `Artifact.compute_id` calls in `rules/conj.py`
  and `rules/synth.py` are the whole guarantee. A `model_copy` that updates
  `content_ref`, `codec` or `interface` produces exactly this: a record that
  keeps the old id and lies about it. The only `model_copy` in `rules/` is one
  nested pair in `conj` — the artifact's copy updates `provenance`, and that
  copy's own copy updates `event_seq` — both outside the address on purpose.
`check: python -c "from deepreason.ontology import Artifact, Interface, Provenance, Ref; i=Interface(commitments=['k1'], refs=[Ref(target='a', role='dependence')]); a=Artifact(id=Artifact.compute_id('inline:x','utf8',i), content_ref='inline:x', codec='utf8', interface=i, provenance=Provenance(role='conjecturer')); b=a.model_copy(update={'provenance': a.provenance.model_copy(update={'event_seq': 7})}); assert b.id==a.id==Artifact.compute_id(b.content_ref,b.codec,b.interface); c=a.model_copy(update={'content_ref':'inline:y'}); assert c.id==a.id and c.id!=Artifact.compute_id(c.content_ref,c.codec,c.interface); d=a.model_copy(update={'interface': Interface(commitments=['k1','k2'], refs=i.refs)}); assert d.id!=Artifact.compute_id(d.content_ref,d.codec,d.interface)" && grep -q 'update={"event_seq": harness._next_seq}' src/deepreason/rules/conj.py`
- **`event_seq` is 0 for everything minted through `create_artifact`.** Only the
  four sites that build `Provenance(event_seq=harness._next_seq)` themselves —
  `conj`, `synth` and the two `experiment` proposals — carry a real sequence.
  Every critic artifact on engaged `run-f4fa6663`, all twenty-nine of them, reads
  as `event_seq=0`, i.e. as if registered before the run began. Any new rule that
  wants an age, a probation clock, or an ordering must stamp it at the mint site;
  the harness will not, and the default is silently plausible.
- **Immutability fails in two different ways and only one of them is a
  `ValidationError`.** Reassigning a field on a `FrozenRecord` raises
  `ValidationError`; mutating a `FrozenList`/`FrozenDict` in place raises
  `TypeError`. Code that catches only the former to detect "I tried to change a
  record" misses half of them. `DR-SUB-ontology` holds the check.
- **The `from` / `from_` split spelling crosses this seam in both directions.**
  Both problem mints construct through the alias
  (`ProblemProvenance.model_validate({"trigger": ..., "from": ...})`) while
  `synth` reads through the Python name (`problem.provenance.from_`). Both are
  correct — `populate_by_name` admits either — and the hazard is neither: it is a
  `model_dump(by_alias=False)` anywhere on the write path, which writes a `from_`
  key no existing root has.
- **Re-registering a `Problem` under the same id is idempotent only if the whole
  record matches; otherwise it is a `WellFormednessError`, never an update.**
  `scan_spawns` is idempotent by design and reruns every cycle, so a rule that
  recomputes a problem's criteria or description between scans turns a rescan
  into a crash rather than a refresh. `spawn`'s `pid in harness.state.problems`
  early return exists for exactly this; any new spawn path needs the same guard,
  and a problem whose content must change needs a new id.
`check: python -c "import tempfile, shutil, pytest; from deepreason.harness import Harness, WellFormednessError; from deepreason.ontology import Problem, ProblemProvenance as PP; d=tempfile.mkdtemp(); h=Harness(d); pv=PP.model_validate({'trigger':'seed','from':[]}); p=Problem(id='q', description='d', criteria=[], provenance=pv); h.register_problem(p); assert h.register_problem(p).id=='q'; other=Problem(id='q', description='d', criteria=[], provenance=PP.model_validate({'trigger':'remove-arbitrariness','from':['a']})); pytest.raises(WellFormednessError, h.register_problem, other); shutil.rmtree(d)" && grep -q "if pid in harness.state.problems:" src/deepreason/rules/spawn.py`
- **Reading a `Status` is free; the seam that governs writing one is a different
  document.** Rules read `harness.state.status` and `state.att` and write
  neither. `DR-SEAM-adjudication-x-rules` holds the warrant triple, the supremacy
  guards, and what a rule may do to the graph.

**RETIRED 2026-08-15 — this claim was authenticated against a PRE-v2 run root,
and v2 readers no longer parse it.** Deleting `SpawnTrigger.SUCCESSOR` (the
decommissioned website pipeline's remnant, operator ruling 2026-08-15) means
roots carrying `trigger: "successor"` no longer load. That is the 2026-08-14
law working as written — "old runs do not need to be valid or returnable" — and
NOT a defect to repair by widening a reader. The claim itself is unchanged and
still believed; what it lost is its historical witness. It is re-authenticated
the moment a current-version root exercises the same property, and the honest
state until then is an unwitnessed claim, said so here rather than left as a
green check over a root nobody can open.
