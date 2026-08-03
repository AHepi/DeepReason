<!-- DR-SEAM-adjudication-x-rules -->
Verified-at: 08dcdf3c
Verify: python tools/docs_verify.py
Owns: src/deepreason/rules/warrants.py, src/deepreason/adjudication/edges.py
Sides: DR-SUB-adjudication, DR-SUB-rules

# adjudication x rules

## The agreement

The rules construct attackable objects; adjudication decides what they do to the
graph. A rule's entire power over status is the right to put three things on the
record at once — an attackable validity node ν, a `Warrant` naming a target, and
an artifact that CARRIES that warrant — after which it has no further say. In
return the adjudicator promises to read only what a rule can be held to: the
warrant's `target`, its `validity_node`, and its `commitment` used as a lookup
key into the commitment map. Who minted it, under what authority, with which of
the two `WarrantType`s and with which `verdict` string never enters. Neither
package imports the other and neither calls the other; `Harness` mediates both
directions, and the rules' return path is the recomputed `EpistemicState`, never
a function call. The consequence worth carrying into any change is that all the
epistemology sits upstream — every supremacy guard, every duplicate-verdict
guard, every decision that a case is not worth minting lives in `rules/` — and
that once an edge exists no rule can withdraw it.

The independence is mutual and is at the level of names, not only of imports.
`check: ! grep -rq "deepreason\.adjudication" --include=*.py src/deepreason/rules/ && ! grep -rq "deepreason\.rules" --include=*.py src/deepreason/adjudication/ && ! grep -rqE "build_att|build_dep|toposort|label0|final_labels|grounded_extension" --include=*.py src/deepreason/rules/ && grep -q "^def build_att(" src/deepreason/adjudication/edges.py && grep -q "^def label0(" src/deepreason/adjudication/grounded.py && grep -q "^def register_fail_warrant(" src/deepreason/rules/warrants.py`

## Where it is expressed

| Site | File | Symbol | What it enforces |
|---|---|---|---|
| The one constructor | `rules/warrants.py` | `register_fail_warrant` | ν is created as an artifact BEFORE the critic, the warrant's `validity_node` is that ν's id, the id is `w:<κ>:<target>`, and the type is `DEMONSTRATIVE` — twelve call sites in eight modules inherit all four |
| Carriage declaration | `rules/warrants.py` | `harness.create_artifact(..., warrants=[warrant])` | a rule asserts an attack only by handing the harness an artifact carrying the warrant; `register_batch` converts that to `StateDiff.carry_add` |
| Write boundary | `harness.py` | `register_batch`, `_validate_warrant` | an unprovided warrant, an unregistered ν or an unregistered κ is a `WellFormednessError` — the rules side cannot assert an edge by content alone |
| Base edge | `adjudication/edges.py` | `build_att` `carry_pairs` / `carriers` | (carrier → `w.target`), and only for a registered carrier, a resolvable warrant id and a registered target |
| Read surface | `adjudication/edges.py` | `w.target`, `w.validity_node`, `w.commitment` | the only three warrant fields the graph ever sees |
| Closure channel | `rules/warrants.py` | the `nu_interface=` parameter | the sole means by which a rule shapes attack PROPAGATION; four call sites pass it |
| Evidence closure | `rules/act.py` → `adjudication/edges.py` | `nu_interface=Interface(refs=[Ref(..., role=RefRole.EVIDENCE)])`, `dep_reliability` → `evidence_lineage` | an attack on the browser's source-reliability artifact reaches the ν through the screenshots' `dependence` refs |
| Evidence closure, hand-built | `rules/vision.py` | `crit_vision`'s ν, one `EVIDENCE` ref per screenshot | the visual case falls when the images it judged are refuted |
| Source-artifact closure | `oracle.property_violation_commitment` → `rules/crit.py` → `adjudication/edges.py` | `budget.extra["source_artifact"]` | refuting a proposed property collapses every verdict minted under it |
| Credit without closure | `rules/crit.py` | `nu_interface = Interface(refs=[Ref(target=gen_id, role=RefRole.MENTION)])`, forwarded as `nu_interface=nu_interface` | the generator that designed the killing experiment is visible in the graph and load-bearing in none of it |
| Case-law closure | `informal/trial.py` → `adjudication/edges.py` | `nu_interface=Interface(refs=[Ref(target=standard.id, role="mention")])` + `kappa.eval.startswith("rubric:")` | the only mint site in the tree that can reach the rubric branch, and it is not in `rules/`; owned by `DR-CON-warrants-and-attacks` |
| Duplicate-verdict guard | `rules/warrants.py` | `verdict_on_record`, `skip_if_on_record` | one (κ, target) fail verdict at a time — `att` is a set and cannot tell a second critic from a first |
| Supremacy guards | `rules/warrants.py` | `execution_backed`, `formally_backed` | whether an edge is CREATED; adjudication never learns either exists |
| Availability handoff | `rules/crit.py` | `harness._oracle_pending`, `QUARANTINE_TICK` | an oracle that could not run mints no warrant, which downstream is indistinguishable from one that passed |
| Return path, edges | `rules/experiment.py`, `rules/guards/anti_relapse.py` | `harness.state.att` | the only two rules-side readers of the attack relation |
| Return path, labels | `rules/act.py`, `rules/experiment.py`, `rules/spawn.py`, `rules/vision.py`, `rules/guards/anti_relapse.py` | `state.status` | five rules read labels to choose what to work on; no rule writes one |
| Recompute point | `harness.py` | `Harness._adjudicate` | the ONLY caller of `build_att` anywhere in `src/`; `invariants.verify_root` does not call it, it reopens the root as a `Harness` and so recomputes through this same method |

There is one recompute point, not two. `invariants.verify_root` never names
`build_att`: it reopens the root as a `Harness`, so the read path re-derives
labels through the same `_adjudicate` the write path uses, and no second
implementation of the fixpoint can drift from the first.
`check: test "$(grep -rn "build_att(" --include=*.py src/deepreason | grep -vc "def build_att(")" -eq 1 && ! grep -q "build_att" src/deepreason/invariants.py && grep -q "h = Harness(root, read_only=True)" src/deepreason/invariants.py && python -c "import ast,inspect;from deepreason import harness as H;t=ast.parse(inspect.getsource(H));f=[n for n in ast.walk(t) if isinstance(n,ast.FunctionDef) and n.name=='_adjudicate'];assert len(f)==1;assert sum(1 for c in ast.walk(f[0]) if isinstance(c,ast.Call) and getattr(c.func,'id','')=='build_att')==1"`

One constructor, twelve call sites, and exactly two hand-built warrants inside
`rules/` — both `ARGUMENTATIVE`, because `DEMONSTRATIVE` is written in one file.
`check: test "$(grep -rn "register_fail_warrant(" --include=*.py src/deepreason | grep -vc "def register_fail_warrant")" -eq 12 && test "$(grep -rl "register_fail_warrant(" --include=*.py src/deepreason | grep -vc "src/deepreason/rules/warrants.py")" -eq 8 && test "$(grep -rn "Warrant(" --include=*.py src/deepreason/rules | grep -vc "src/deepreason/rules/warrants.py")" -eq 2 && test "$(grep -rl "WarrantType.DEMONSTRATIVE" --include=*.py src/deepreason/rules)" = src/deepreason/rules/warrants.py && grep -A4 "warrant = Warrant(" src/deepreason/rules/vision.py | grep -q "WarrantType.ARGUMENTATIVE"`

`nu_interface` is a single optional parameter and the whole propagation surface a
rule has; four sites in the tree pass it.
`check: test "$(grep -rnE "\bnu_interface=" --include=*.py src/deepreason | grep -vc "src/deepreason/rules/warrants.py")" -eq 4 && grep -q "interface=nu_interface," src/deepreason/rules/warrants.py && grep -q "nu_interface: Interface | None = None," src/deepreason/rules/warrants.py`

Evidence closure is two declarations on the rules side and one walk on the
adjudication side: the ν names the evidence, the screenshots name the browser's
reliability as a `dependence`, and `evidence_lineage` follows that transitively.
The role on the ν's ref is what buys the closure: the same graph with `mention`
in place of `evidence` reaches neither the ν nor the carrier.
`check: grep -q "dep_reliability = Ref(target=reliability.id, role=RefRole.DEPENDENCE)" src/deepreason/rules/act.py && grep -q "nu_interface=Interface(refs=\[Ref(target=evidence.id, role=RefRole.EVIDENCE)\])" src/deepreason/rules/act.py && test "$(grep -c "RefRole.DEPENDENCE" src/deepreason/adjudication/edges.py)" -eq 2 && grep -q "^    def evidence_lineage(evidence_id: str)" src/deepreason/adjudication/edges.py && python -c "from deepreason.adjudication.edges import build_att; from deepreason.ontology import Artifact, Commitment, Interface, Provenance, Warrant, WarrantType; from deepreason.ontology.artifact import Ref, RefRole; p=Provenance(role='critic'); A=lambda i,**k: Artifact(id=i, content_ref='inline:'+i, provenance=p, **k); ws={'w':Warrant(id='w',target='T',type=WarrantType.DEMONSTRATIVE,commitment='k',verdict='fail',validity_node='N'),'wx':Warrant(id='wx',target='R',type=WarrantType.ARGUMENTATIVE,validity_node='T')}; g=lambda role: build_att({x.id:x for x in [A('C',warrants=['w']),A('T'),A('N',interface=Interface(refs=[Ref(target='E',role=role)])),A('E',interface=Interface(refs=[Ref(target='R',role=RefRole.DEPENDENCE)])),A('R'),A('X',warrants=['wx'])]}, ws, {'k':Commitment(id='k',eval='program:x')}); closes=g(RefRole.EVIDENCE); inert=g(RefRole.MENTION); assert {('X','N'),('X','C')} <= closes, sorted(closes); assert not ({('X','N'),('X','C')} & inert), sorted(inert)"`

Source-artifact closure crosses the seam as one dictionary key, minted in the
oracle, requested by the criticism rule, read in the fixpoint. The oracle writes
that id twice — once inside the content-addressed spec, once as the top-level
`budget.extra` key — and only the second is the one `edges.py` reads, so the
check exercises the minted commitment rather than grepping for either line.
`check: python -c "import json; from deepreason.ontology import Budget, Commitment; from deepreason.oracle import property_violation_commitment; base=Commitment(id='b',eval='program:property_oracle',budget=Budget(extra={'spec':json.dumps({'entry':'f','inputs':[],'checker':'x','input_check':None,'step_limit':10})})); cx=property_violation_commitment(base,'P','source',[1]); assert cx.budget.extra['source_artifact'] == 'P', cx.budget.extra; from deepreason.adjudication.edges import build_att; from deepreason.ontology import Artifact, Provenance, Warrant, WarrantType; p=Provenance(role='critic'); A=lambda i,**k: Artifact(id=i, content_ref='inline:'+i, provenance=p, **k); arts={x.id:x for x in [A('C',warrants=['w']),A('T'),A('N'),A('P'),A('X',warrants=['wx'])]}; ws={'w':Warrant(id='w',target='T',type=WarrantType.DEMONSTRATIVE,commitment=cx.id,verdict='fail',validity_node='N'),'wx':Warrant(id='wx',target='P',type=WarrantType.ARGUMENTATIVE,validity_node='T')}; closes=build_att(arts,ws,{cx.id:cx}); inert=build_att(arts,ws,{cx.id:Commitment(id=cx.id,eval=cx.eval)}); assert {('X','N'),('X','C')} <= closes, sorted(closes); assert not ({('X','N'),('X','C')} & inert), sorted(inert)" && grep -q "kappa.budget.extra.get(\"source_artifact\")" src/deepreason/adjudication/edges.py && grep -q "cx = property_violation_commitment(base, prop_id, prop_source, violation)" src/deepreason/rules/crit.py`

The write boundary refuses the three ways a rule can hand over an incoherent
warrant; the criticism rule registers its counterexample commitment before
minting against it; and each closure is pinned through the rule that actually
mints the interface rather than through a hand-built graph.
`check: grep -q "carried warrant not provided/registered: {wid}" src/deepreason/harness.py && grep -q "validity_node {warrant.validity_node} not registered" src/deepreason/harness.py && grep -q "commitment {warrant.commitment} not registered" src/deepreason/harness.py && grep -q "harness.register_commitment(cx)" src/deepreason/rules/crit.py && python -m pytest tests/test_adjudication.py::test_unregistered_warrant_rejected tests/test_act.py::test_fail_registers_demonstrative_warrant tests/test_vision.py::test_refuting_browser_reliability_reinstates_visually_refuted_app tests/test_properties.py::test_refuting_the_property_reinstates_its_victims -q`

Both ends of the seam, end to end, on two committed roots: engaged
`run-f4fa6663` carries one `register_fail_warrant` warrant with the `w:<κ>:<target>`
id, one carriage pair, one edge and exactly one `REFUTED`; stress-triplet
orbit `run-6472629d` ran to completion with none of the four and 42 `ACCEPTED`.
(The none-of-the-four half originally pinned jolt `run-b4d6dfda` — 72
`ACCEPTED`, 851 events — but that root's home was gitignored by its ladder and
never entered the record; `docs/ERRATA.md` E7.)
`check: python -c "from deepreason.harness import Harness; from deepreason.ontology import Status, WarrantType; b='experiments/2026-08-02-stress-triplet/home-orbit/runs/run-6472629dbc5d408a733d472040671752'; h=Harness(b, read_only=True); assert (len(h.warrants), len(h.state.carries), len(h.state.att)) == (0,0,0); assert set(h.state.status.values()) == {Status.ACCEPTED} and len(h.state.artifacts) == 42 and len(list(h.log.read())) == 600; g='experiments/live_engaged_2026-07-27/run-f4fa6663e5412d64df943a5a22342baf'; k=Harness(g, read_only=True); (wid, w), = k.warrants.items(); assert w.type is WarrantType.DEMONSTRATIVE and wid == 'w:%s:%s' % (w.commitment, w.target); assert len(k.state.carries) == 1 and len(k.state.att) == 1; assert sum(1 for s in k.state.status.values() if s == Status.REFUTED) == 1"`

## What is deliberately absent

**The adjudicator cannot see which rule minted a warrant, nor with what force.**
An AST walk over `edges.py` finds exactly three attributes read off a warrant.
`type`, `verdict`, `trace_ref` and `id` are all populated by
`register_fail_warrant` and all invisible downstream. The asymmetry between a
demonstrative and an argumentative warrant is entirely a property of what each
MINT SITE was allowed to do, never of what the graph does with the result.
The walk cannot be dodged by renaming: it first asserts that `w` is the ONLY
name `edges.py` binds from the `warrants` map (so `ww = warrants[wid]` fails the
check before any attribute is read), and it then reads attributes off `w` and
off `warrants[...]` / `warrants.get(...)` alike.
`check: python -c "import ast,inspect;from deepreason.adjudication import edges;from deepreason.ontology.warrant import Warrant;t=ast.parse(inspect.getsource(edges));NW=lambda n: any(isinstance(x,ast.Name) and x.id=='warrants' for x in ast.walk(n));b={n.id for s in ast.walk(t) if isinstance(s,(ast.Assign,ast.For,ast.comprehension)) for v in [s.value if isinstance(s,ast.Assign) else s.iter] if NW(v) for x in (s.targets if isinstance(s,ast.Assign) else [s.target]) for n in ast.walk(x) if isinstance(n,ast.Name)};assert b=={'w'},b;a={n.attr for n in ast.walk(t) if isinstance(n,ast.Attribute) and ((isinstance(n.value,ast.Name) and n.value.id=='w') or (isinstance(n.value,(ast.Subscript,ast.Call)) and NW(n.value)))};assert a=={'target','validity_node','commitment'},a;assert {'id','type','verdict','trace_ref'}<=set(Warrant.model_fields)"`

**"Fail" is a rules-side constant, not an adjudication test.** A warrant whose
`verdict` is `"pass"` produces the same attack edge as one whose verdict is
`"fail"`, and a warrant whose id bears no relation to `w:<κ>:<target>` produces
it too. Nothing in the graph re-checks that a fail warrant records a failure.
That is why `register_fail_warrant` hard-codes `verdict="fail"` and
`type=WarrantType.DEMONSTRATIVE` instead of taking them as parameters — the
single constructor IS the enforcement, and a hand-built demonstrative warrant
elsewhere would be unpoliced by anything downstream of it. The graph the check
builds registers the ν and an attacker of it, so the equality covers the closure
fixpoint and not only the base edge: a verdict or type test added ANYWHERE in
`build_att` breaks it.
`check: python -c "from deepreason.adjudication.edges import build_att; from deepreason.ontology import Artifact, Provenance, Warrant, WarrantType; p=Provenance(role='critic'); A=lambda i,**k: Artifact(id=i,content_ref='inline:'+i,provenance=p,**k); e=lambda v,ty: build_att({x.id:x for x in [A('C',warrants=['zz']),A('T'),A('N'),A('X',warrants=['wx'])]},{'zz':Warrant(id='zz',target='T',type=ty,verdict=v,commitment='k',validity_node='N'),'wx':Warrant(id='wx',target='N',type=WarrantType.ARGUMENTATIVE,validity_node='T')},{}); assert e('fail',WarrantType.DEMONSTRATIVE)==e('pass',WarrantType.ARGUMENTATIVE)=={('C','T'),('C','X'),('X','C'),('X','N')}, sorted(e('pass',WarrantType.ARGUMENTATIVE))" && grep -q 'verdict="fail",' src/deepreason/rules/warrants.py && grep -q "type=WarrantType.DEMONSTRATIVE," src/deepreason/rules/warrants.py && grep -q 'warrant_id or f"w:{commitment_id}:{target_id}"' src/deepreason/rules/warrants.py`

**Case-law closure is unreachable from `rules/`, and that is a filter rather than
an oversight.** `crit_program` mints only against commitments `programs.evaluable`
admits, and `evaluable` recognises `predicate:` and `program:` only; every other
rules-side mint uses a `program:` commitment the rule constructed itself
(counterexample, prop-oracle, browser, checker-wf). So no ν minted inside
`rules/` can ever enter the `rubric:` branch of the fixpoint. The branch belongs
to `informal/trial.py` alone — the one site in the tree that hands
`register_fail_warrant` a ν mentioning a standard, under the rubric κ the trial
was called on. `informal/audits.py` is NOT a second such site, though it is the
other module that reasons about rubric warrants: it walks them
(`_rubric_warrants`) and attacks their ν, but its own warrant carries
`audit:paraphrase-invariance` / `audit:premise-deletion`, both `program:`, so it
lands on the ordinary validity-node closure and never on the case-law one. A
change that lets a rules-side route mint against a rubric κ silently turns every
`mention` on its ν into case law.
`check: python -c "from deepreason.programs import evaluable; from deepreason.ontology import Commitment as K; assert not evaluable(K(id='k', eval='rubric:std-1')); assert evaluable(K(id='k', eval='predicate:1==1'))" && grep -q "if kappa is None or not programs.evaluable(kappa):" src/deepreason/rules/crit.py && grep -q "kappa.eval.startswith(\"rubric:\")" src/deepreason/adjudication/edges.py && test "$(grep -rln "nu_interface=Interface(refs=\[Ref(target=standard.id, role=\"mention\")\])," --include=*.py src/deepreason)" = src/deepreason/informal/trial.py && python -c "from deepreason.informal.audits import PARAPHRASE_AUDIT, PREMISE_AUDIT; assert [k.eval for k in (PARAPHRASE_AUDIT, PREMISE_AUDIT)] == ['program:paraphrase_audit', 'program:premise_deletion_audit']"`

**The generator credit on a fuzz ν is deliberately inert.** `crit_fuzz` mentions
the generator that designed the killing experiment so the credit is in the graph,
and gets no closure from it: a generator only chose where to look, so refuting it
must not unwind a counterexample that was RUN. The inertness is bought entirely
by the commitment's eval being `program:` — flip the same graph's κ to `rubric:`
and the identical `mention` propagates onto the ν and every carrier.
`check: python -c "from deepreason.adjudication.edges import build_att; from deepreason.ontology import Artifact, Commitment, Interface, Provenance, Warrant, WarrantType; from deepreason.ontology.artifact import Ref; p=Provenance(role='critic'); A=lambda i,**k: Artifact(id=i, content_ref='inline:'+i, provenance=p, **k); arts={x.id:x for x in [A('C',warrants=['w']),A('T'),A('N',interface=Interface(refs=[Ref(target='G',role='mention')])),A('G'),A('X',warrants=['wx'])]}; ws={'w':Warrant(id='w',target='T',type=WarrantType.DEMONSTRATIVE,commitment='k',verdict='fail',validity_node='N'),'wx':Warrant(id='wx',target='G',type=WarrantType.ARGUMENTATIVE,validity_node='T')}; f=lambda ev: build_att(arts,ws,{'k':Commitment(id='k',eval=ev)}); inert=f('program:property_oracle'); closes=f('rubric:std-1'); assert ('X','N') not in inert and ('X','C') not in inert, sorted(inert); assert ('X','N') in closes and ('X','C') in closes, sorted(closes)" && grep -q "nu_interface = Interface(refs=\[Ref(target=gen_id, role=RefRole.MENTION)\])" src/deepreason/rules/crit.py`

**No supremacy vocabulary crosses into `edges.py`.** The guards decide only
whether an edge is created. Once created, an edge is adjudicated exactly like any
other, so an execution-backed target that a prose case was refused against can
still be refuted later by execution, and the graph has no memory that a refusal
ever happened. Adding a "this warrant was argumentative, weigh it less" test to
the fixpoint is the change this absence forbids.
`check: grep -q "^def build_att(" src/deepreason/adjudication/edges.py && ! grep -qE "execution_backed|formally_backed|verdict_on_record|programs\.|EXEC_PROGRAMS" src/deepreason/adjudication/edges.py && grep -q "^def execution_backed(" src/deepreason/rules/warrants.py && grep -q "^def formally_backed(" src/deepreason/rules/warrants.py && grep -q "^def verdict_on_record(" src/deepreason/rules/warrants.py && grep -q "    from deepreason import programs" src/deepreason/rules/warrants.py`

**Nothing removes an edge, on either side.** `build_att` starts from an empty set
on every call and only ever adds; there is no retraction, no `discard`, no
`remove`. A rule that wants to undo an attack must mint another attack, which is
D8 (nothing is deleted) expressed as an absence of code rather than as a rule.
`check: ! grep -qE "\.discard\(|\.remove\(|^ *del " src/deepreason/adjudication/edges.py && grep -q "att: set\[tuple\[str, str\]\] = set()" src/deepreason/adjudication/edges.py && test "$(grep -c "att.add(" src/deepreason/adjudication/edges.py)" -eq 5`

**No rule computes, asserts or mutates a label; five read labels and only two
read the attack relation.** Reading is deliberately allowed and is the seam's
return path:
`promoted_properties` uses `state.att` for "was this property ever attacked and
did it survive", and the anti-relapse gate uses it to find a prior's refuters.
Both go through `EpistemicState`, so what they see is whatever the last
`_adjudicate` produced — never a graph they computed themselves.
`check: test "$(grep -rl "harness\.state\.att" --include=*.py src/deepreason/rules | sort | tr "\n" " ")" = "src/deepreason/rules/experiment.py src/deepreason/rules/guards/anti_relapse.py " && test "$(grep -rl "state\.status" --include=*.py src/deepreason/rules | sort | tr "\n" " ")" = "src/deepreason/rules/act.py src/deepreason/rules/experiment.py src/deepreason/rules/guards/anti_relapse.py src/deepreason/rules/spawn.py src/deepreason/rules/vision.py " && ! grep -rqE "state\.(att|dep|status|conn)\s*(=[^=]|\.(add|update|discard|pop|clear)\()" --include=*.py src/deepreason/rules/ && grep -q "self.state.status = " src/deepreason/harness.py`

## How to change it

The two sides fail differently, so the first question is which one the change is.

1. **Read `DR-INV-frozen-surfaces` and `DR-SUB-adjudication` first.** Labels are
   never read back from a log; opening a root replays and recomputes them. A
   change to `edges.py` therefore does not improve old runs, it makes them
   disagree with the `att+` and `status_changed` deltas they recorded at write
   time. Sweep every openable root before and after and require
   `valid`/`att` byte-identical.
2. **"A new way to be refuted" is entirely rules-side.** Mint through
   `register_fail_warrant` with your own ν wording, critic wording and trace
   payload. Nothing in `adjudication/` moves, no recorded root changes meaning,
   and the write boundary already refuses the malformed cases for you. Never
   hand-build a `DEMONSTRATIVE` warrant: the id scheme, the ν wiring and the
   duplicate guard exist once, and the graph re-checks none of them.
3. **"A new way an attack propagates" moves both sides, and the declaration must
   tolerate being absent.** Every ν written before your change has no such ref
   and no such budget key, and those roots must keep replaying to the same
   labels. Add the declaration to the ν's `Interface` or to the commitment's
   `budget.extra` — both are already content-addressed and already optional.
   Do NOT add a field to `Warrant` to carry it: `Warrant` is a frozen record
   format present in every root on disk, and `edges.py` reads three of its fields
   by design.
4. **A guard never belongs in `edges.py`.** If the answer to "should this
   refute?" depends on what the TARGET carries, it is `rules/warrants.py`; if it
   depends on what the graph already says, it is the fixpoint. Confusing the two
   puts an epistemic policy where every recorded root will re-derive it.
5. **Order within the rules side:** register the commitment, then call
   `register_fail_warrant`. `_validate_warrant` rejects a warrant whose κ is not
   registered, and `crit.py` registers `cx` immediately before minting for
   exactly this reason.

What breaks first, cheapest to most expensive: `WellFormednessError: warrant …:
commitment … not registered` or `… validity_node … not registered` at
registration; then `carried warrant not provided/registered` if you build the
carriage by hand; then `tests/test_adjudication.py`, which is fast and hand-built
and will catch a closure that no longer converges; then
`tests/test_replay.py` and `tests/test_persistence_invariants.py`, which is where
a semantics change stops being a design question and becomes a broken root.

The tests that will catch you, in that order:
`tests/test_adjudication.py` (graph semantics, hand-built),
`tests/test_act.py` and `tests/test_vision.py` (evidence closure through the
rules that mint it), `tests/test_properties.py` (source-artifact closure),
`tests/test_prose_refutation_boundaries.py` (the guards),
`tests/test_adjudication_blindness.py` (the chain never firing),
`tests/test_replay.py` and `tests/test_persistence_invariants.py` (recorded
roots).

## Traps

- **The graph records that an edge is missing, never why.** A guard declining, a
  duplicate verdict skipped, a sandbox abort, an oracle overrun, and a critic
  that simply found nothing all leave `att` identically empty. `crit_program`
  routes the unavailable case to `harness._oracle_pending` and `crit_fuzz` bumps
  `QUARANTINE_TICK` precisely because the adjudicator cannot tell it from a pass;
  neither word appears in `edges.py`, and cannot, since the package sees no rules
  and no calls. jolt `run-b4d6dfda0c20676a864a051fbc97bda4` is what the failure
  looks like from outside: 851 events, 72 artifacts, zero warrants, everything
  ACCEPTED, `epistemic_checks_passed: true`. The detector lives in
  `verification/report.py` (`DR-SUB-verification`) and has to.
`check: grep -q "harness._oracle_pending.add(pending_key)" src/deepreason/rules/crit.py && grep -q "QUARANTINE_TICK\[0\] += 1" src/deepreason/rules/crit.py && grep -q "^def build_att(" src/deepreason/adjudication/edges.py && ! grep -qiE "pending|abort|unavailable|quarantine" src/deepreason/adjudication/edges.py && grep -q "adjudication-blindness" src/deepreason/verification/report.py && grep -q '"epistemic_checks_passed": true,' experiments/live_jolt_2026-07-31/jolt-reason-epoch3.json`
- **A warrant can commit while its critic artifact does not.** Critic artifacts
  are content-addressed, so a byte-identical critic — same target, same spec, same
  decisive quote from a second rubric κ — dedupes and registers nothing, while the
  carriage pair still commits and the edge still appears. Code that treats "the
  critic came back" as "an event was written" mis-accounts: the 1M arrow-of-time
  run leaked 13 judge rulings (~770 tokens each) this way, `verify_root` metering
  1 000 214 against a log of 990 192. All THREE trial paths — `_trial_steps`,
  `_argument_trial_steps`, `_pairwise_steps` — now compare `critic.id` against
  the pre-registration artifact set. Evidence:
  `docs/MINI_STRESS_REPORT.md` §F4, `tests/test_trial_accounting.py`.
`check: test "$(grep -c "critic.id not in before" src/deepreason/informal/trial.py)" -eq 3 && python -c "import ast,inspect;from deepreason.informal import trial;t=ast.parse(inspect.getsource(trial));f={n.name for n in ast.walk(t) if isinstance(n,ast.FunctionDef) and 'critic.id not in before' in ast.unparse(n)};assert f=={'_trial_steps','_argument_trial_steps','_pairwise_steps'}, f" && python -m pytest tests/test_trial_accounting.py -q`
- **A decorative `mention` on a ν is inert only for as long as its commitment is
  not `rubric:`.** The two `MENTION` refs minted in `rules/crit.py` are credit and
  readability, and today no rules-side route can reach the rubric branch. That is
  a consequence of `programs.evaluable`, not of anything either file says about
  itself. Widening `evaluable`, or adding a rules-side mint against a rubric κ,
  makes those citations load-bearing without anyone editing `edges.py`. See the
  two closure checks above.
- **Assuming the guard is on the side you are editing.** `rules/crit.py` consults
  `execution_backed` and `informal/trial.py` consults `formally_backed`, and
  neither is visible from `adjudication/`. Searching `edges.py` for the reason a
  target was not refuted and finding nothing is the expected result, not evidence
  that the boundary is unguarded. `DR-CON-warrants-and-attacks` holds the full
  guard-by-guard breakdown; `DR-SEAM-rules-x-scratch` holds the analogous
  criticism-side separation.
