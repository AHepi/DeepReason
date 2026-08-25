<!-- DR-SUB-adjudication -->
Verified-at: 748c9ab61
Verify: python -m pytest tests/test_adjudication.py -q
Owns: src/deepreason/adjudication/
Seams: DR-SEAM-adjudication-x-rules, DR-SEAM-adjudication-x-authority
Seams-undocumented: adjudication x harness, adjudication x ontology, adjudication x schools, adjudication x verification

# Adjudication — the two passes that turn a graph into a verdict

## What it is

This package is the entirety of DeepReason's status semantics. Given the attack
relation `att` and the support relation `dep`, it computes the `Status` label of
every artifact — and nothing else in the system is allowed to compute one. Pass 1
is Dung's grounded extension: unique, skeptical, and a Kleene fixpoint, so
reinstatement is *derived* rather than ruled — refute a critic and its target
comes back without anyone deciding that it should. Pass 2 walks `dep` in
topological order and demotes anything whose premises fell to
`suspended_unsupported`, because an orphaned claim is not a false one. Its inputs
are deliberately starved: measures, school membership, novelty and Pareto rank
must not enter here, and act upstream through Spawn, budgeted commitments, or
attention instead. Three logic modules plus a docstring-only `__init__`, no I/O,
no configuration, no state.

The package imports nothing but `deepreason.ontology`, and that narrowness is the
blindness property, not an accident of the current implementation. Read the
import graph from the AST, not from one spelling of `import`: `import
deepreason.harness`, `from deepreason import harness` and `from . import edges`
are all ways in, and a grep for `from deepreason\.` sees none of them.
`check: python -c "import ast,pathlib; d=pathlib.Path('src/deepreason/adjudication'); assert sorted(p.name for p in d.glob('*.py'))==['__init__.py','edges.py','grounded.py','support.py']; names=[x for p in sorted(d.glob('*.py')) for n in ast.walk(ast.parse(p.read_text())) for x in ([a.name for a in n.names] if isinstance(n,ast.Import) else ([n.module or '']+(['deepreason.'+a.name for a in n.names] if n.module=='deepreason' else [])+(['deepreason.RELATIVE'] if n.level else []) if isinstance(n,ast.ImportFrom) else []))]; roots={'.'.join(x.split('.')[:2]) for x in names if x.split('.')[0]=='deepreason'}; assert roots=={'deepreason.adjudication','deepreason.ontology'}, roots"`

No provenance, school, measure, or ranking word appears anywhere in the three
logic modules, and no function touches instance state, a file, or JSON.
`check: ! grep -rqE "provenance|school|pareto|novelty|hv|reach|measure" src/deepreason/adjudication/edges.py src/deepreason/adjudication/grounded.py src/deepreason/adjudication/support.py && ! grep -rqE "self\.|open\(|json\.|import os|Path\(" src/deepreason/adjudication/*.py`

## Entry points

- `build_att(artifacts, warrants, commitments, carries)` — every attack edge, computed as a fixpoint so that the four closure rules compose in one call.
- `build_dep(artifacts)` — support edges from `RefRole.DEPENDENCE` refs, and from nothing else.
- `toposort(nodes, dep_edges)` — dependencies before dependents, lexicographic tie-break; also the DAG test.
- `DependenceCycleError` — what `toposort` raises; `Harness.register_batch` converts it to `WellFormednessError` and refuses the registration outright.
- `grounded_extension(nodes, att)` — least fixed point of Dung's characteristic function `F`.
- `label0(nodes, att)` — pass 1. Returns three **strings**: `accepted`, `refuted`, `suspended`.
- `final_labels(label0, dep_edges)` — pass 2. The only producer of `Status` values in the codebase.
- `evidence_lineage` (nested in `build_att`) — an evidence artifact plus its transitive registered `dependence` sources; the reach of evidence invalidation.

Resolved from the AST, so that a rename to `final_labels_v2` is a failure rather
than a substring match, and so that `evidence_lineage`'s nesting inside
`build_att` — the reason its cache cannot outlive one call — is asserted
structurally.
`check: python -c "import ast,pathlib; top=lambda f: {n.name:n for n in ast.parse(pathlib.Path('src/deepreason/adjudication/'+f).read_text()).body if isinstance(n,(ast.FunctionDef,ast.ClassDef))}; e=top('edges.py'); assert {'build_att','build_dep','toposort','DependenceCycleError'} <= set(e), sorted(e); assert isinstance(e['DependenceCycleError'],ast.ClassDef); assert 'evidence_lineage' not in e; assert 'evidence_lineage' in {n.name for n in ast.walk(e['build_att']) if isinstance(n,ast.FunctionDef)}; assert {'grounded_extension','label0'} <= set(top('grounded.py')), sorted(top('grounded.py')); assert 'final_labels' in top('support.py'), sorted(top('support.py'))"`

Exactly THREE modules in `src/` call any of them, and the list is pinned exactly
rather than as a minimum, so a fourth is a failure: `harness.py`
(`Harness._adjudicate`, the sole writer of `state.status`), `invariants.py`
(`verify_root` re-derives `dep` and re-runs `toposort` rather than trusting the
recorded graph), and — since Rung 8 — `calculus/audit.py`.

**Why the third is legitimate, and why it is not a weakening.** The first two
WRITE or VALIDATE labels. `audit.py` computes labels it never applies: §9.9's C5
and P6 clauses are DIFFERENTIALS, and the only way to show standing does not
reach a label is to compute the labels without it and find them unchanged. It
imports the real `label0`/`final_labels` rather than reimplementing the two
passes, and that is the point — a reimplementation would be measuring itself,
which is the mistake `experiments/2026-08-22-measure-grounded-flip-rate/`
records avoiding in as many words ("not a reimplementation — a reimplementation
would measure itself"). It reads a COPY of the relations and writes nothing:
`state.status` still has exactly one writer.
`check: python -c "import pathlib; imp=sorted(str(p) for p in pathlib.Path('src').rglob('*.py') if 'from deepreason.adjudication' in p.read_text() and 'deepreason/adjudication/' not in str(p)); assert imp==['src/deepreason/calculus/audit.py','src/deepreason/harness.py','src/deepreason/invariants.py'], imp" && [ "$(grep -rc "self.state.status = " src/deepreason/harness.py)" = 1 ] && grep -qE "^    def _adjudicate\(" src/deepreason/harness.py && grep -q "self._apply_event(event, adjudicate=False)" src/deepreason/harness.py && grep -A2 "except DependenceCycleError as e:" src/deepreason/harness.py | grep -q "raise WellFormednessError(str(e)) from e" && grep -q "toposort(set(h.state.artifacts), build_dep(h.state.artifacts))" src/deepreason/invariants.py`

## State it owns

Nothing persistent, and nothing in memory between calls: every function is a pure
map from its arguments, and the one cache (`evidence_cache`) lives and dies inside
a single `build_att` invocation. What persists is its *output*.
`Harness._adjudicate` writes the returned sets into `EpistemicState.att`, `.dep`,
`.status` and `.conn`, and `Harness._apply_event` records the per-event delta on
the log line as `att+`, `dep+` and `status_changed`. Those three keys on every
line of `log.jsonl` are this package's only durable trace — and the only
epistemic field the record has. Reading a committed root proves only that the
record once had those keys; the writer has to be exercised too, or renaming the
`att+` wire alias and zeroing `status_changed` both pass.
`check: python -c "import json,pathlib,tempfile; from deepreason.harness import Harness; from deepreason.ontology import Provenance,Warrant,WarrantType; t=pathlib.Path(tempfile.mkdtemp())/'run'; h=Harness(t); a=h.create_artifact('claim',provenance=Provenance(role='seed')); nu=h.create_artifact('nu',provenance=Provenance(role='critic')); h.create_artifact('critic',provenance=Provenance(role='critic'),warrants=[Warrant(id='w',target=a.id,type=WarrantType.ARGUMENTATIVE,validity_node=nu.id)]); L=[json.loads(l) for l in (t/'log.jsonl').read_text().splitlines()]; assert all({'att+','dep+','status_changed'} <= set(e['state_diff']) for e in L); assert L[-1]['state_diff']['att+'] and L[-1]['state_diff']['status_changed'], L[-1]; assert h.state.att and h.state.status and h.state.conn is not None; R=[json.loads(l) for l in pathlib.Path('experiments/live_engaged_2026-07-27/run-f4fa6663e5412d64df943a5a22342baf/log.jsonl').read_text().splitlines()]; assert all({'att+','dep+','status_changed'} <= set(e['state_diff']) for e in R); assert any(e['state_diff']['status_changed'] for e in R)"`

The two passes have different output types, and the boundary is load-bearing:
`label0` hands back plain strings, `final_labels` is where `Status` enters, and
`suspended_unsupported` exists only on the far side of pass 2.
`check: python -c "from deepreason.adjudication.grounded import label0; from deepreason.adjudication.support import final_labels; from deepreason.ontology.state import Status; l=label0({'a','b','c'},{('a','b')}); assert l=={'a':'accepted','b':'refuted','c':'accepted'}, l; f=final_labels(l,{('c','b')}); assert (f['a'],f['b'],f['c'])==(Status.ACCEPTED,Status.REFUTED,Status.SUSPENDED_UNSUPPORTED), f; assert label0({'a','b'},{('a','b'),('b','a')})=={'a':'suspended','b':'suspended'}"`

## Seams

| Side | Status | What the agreement is (one line) |
|---|---|---|
| `DR-SEAM-adjudication-x-rules` | documented | the rules construct attackable objects; adjudication alone decides what they do to the graph — a rule's entire power over status is the right to put warrant/target/validity-node on an artifact, never a `Status` value itself |
| adjudication x harness | undocumented | real and load-bearing (not merely unanalyzed): `harness.py` is the ONLY caller of `build_att`/`build_dep`/`toposort` (`Harness._adjudicate`, the sole writer of `state.status`) — a genuine candidate seam, just not yet written up |
| adjudication x ontology | undocumented | the one package adjudication imports at all (its whole import surface is `deepreason.ontology` plus itself) — likely foundational vocabulary rather than a two-way agreement, but not shown uninteresting merely because it's one-directional |
| adjudication x verification | undocumented | real: `invariants.py`'s `verify_root` re-derives `dep` and reruns `toposort` independently rather than trusting the recorded graph, and `verification/report.py` hosts the adjudication-blindness detector this package structurally cannot host itself |
| `DR-SEAM-adjudication-x-authority` | documented | indirect, not absent: `DR-CON-authority` gates whether an LLM-mediated judgement may mint a warrant AT ALL, upstream in `rules/crit.py`/`informal/trial.py` — by the time a warrant reaches `build_att`, authority's decision is already baked in; adjudication itself never imports `authority.py`. The seam document measures why that indirection is load-bearing: a policy consulted at label time moves a committed root's verdict, one consulted at mint time cannot |
| adjudication x schools | **deliberately absent** | this package's own check proves it: no `provenance`, `school`, or ranking word appears anywhere in the three logic modules. A school's self-criticism refusal is enforced upstream, in criticism planning — not here, and should not be |

## Where to change what

| To change... | Edit | Test |
|---|---|---|
| what a ref role does to the graph | `build_dep` / `build_att` in `adjudication/edges.py`, alongside `RefRole` in `ontology/artifact.py` | `tests/test_adjudication.py::test_support_cascade_orphaned_not_false` |
| add a closure rule (a new way refuting X collapses Y's warrant) | the fixpoint body of `build_att` | `tests/test_adjudication.py::test_standard_refutation_collapses_verdicts_and_reinstates` |
| what refuting a rubric standard collapses (case law) | the `kappa.eval.startswith("rubric:")` branch of `build_att` | `tests/test_adjudication.py::test_standard_refutation_collapses_verdicts_and_reinstates` |
| how a proposed property's verdicts unwind | the `budget.extra["source_artifact"]` branch of `build_att`; the key is minted by `oracle.property_violation_commitment` | `tests/test_properties.py::test_refuting_the_property_reinstates_its_victims` |
| how far evidence invalidation reaches | `evidence_lineage` in `edges.py` | `tests/test_vision.py::test_refuting_browser_reliability_reinstates_visually_refuted_app` |
| the attack semantics (grounded → preferred, stable, credulous) | `grounded_extension` in `adjudication/grounded.py` | `tests/test_adjudication.py::test_mutual_attack_suspended` |
| add or retire a `Status` label | `final_labels` in `adjudication/support.py` plus `Status` in `ontology/state.py` | `tests/test_adjudication.py::test_support_cascade_orphaned_not_false` |
| dep ordering, or how a cycle is refused | `toposort` / `DependenceCycleError` in `edges.py`; the refusal itself is `Harness.register_batch` | `tests/test_adjudication.py::test_dep_cycle_rejected` |
| when adjudication runs (per event vs once at the end) | `Harness._adjudicate` and the `adjudicate=` flag on `Harness._apply_event` — not this package | `tests/test_replay.py::test_replay_reproduces_state_byte_for_byte` |
| catch a run in which criticism ran and attacked nothing | `verification/report.py` `_adjudication_blindness_findings` — this package structurally cannot see it | `tests/test_adjudication_blindness.py::test_a_run_whose_criticism_attacked_nothing_is_flagged` |
| let a measure, school, or rank steer status | nothing here, by construction — route it through `rules/spawn.py`, a budgeted `Commitment`, or attention | the import-surface and starved-input checks under *What it is* (not a pytest id — this row is a prohibition) |

Six of those eleven rows land in one fast module: grounded correctness,
reinstatement, validity-node closure across every carrier, the support cascade,
cycle rejection, and case-law collapse. The other five are deliberately tested
elsewhere — the two closure rows go through the rules that mint their interfaces
(next paragraph), and the scheduling, blindness and route-it-upstream rows are
outside this package by construction.
`check: python -m pytest tests/test_adjudication.py -q && python -c "import pathlib; text=pathlib.Path('docs/map/SUB-adjudication.md').read_text(); section=text.split('## Where to change what',1)[1].split('## Traps',1)[0]; rows=[l for l in section.splitlines() if l.startswith('| ') and '---' not in l][1:]; assert len(rows)==11, len(rows); assert sum(1 for r in rows if 'tests/test_adjudication.py::' in r)==6, [r for r in rows if 'tests/test_adjudication.py::' in r]"`

Every test named in that table is collectable — including the two rows no other
check on this page touches (`test_replay.py` for the `adjudicate=` flag,
`test_adjudication_blindness.py` for the detector this package cannot host).
`check: IDS=$(python -c "import pathlib,re; print(' '.join(sorted(set(re.findall(r'tests/[A-Za-z0-9_/]+[.]py::[A-Za-z0-9_]+', pathlib.Path('docs/map/SUB-adjudication.md').read_text())))))") && [ "$(echo $IDS | wc -w)" -ge 9 ] && python -m pytest --collect-only -q $IDS > /dev/null`

Source-artifact closure and evidence closure are exercised end-to-end through the
rules that actually mint those interfaces, not through hand-built graphs.
`check: python -m pytest tests/test_properties.py::test_refuting_the_property_reinstates_its_victims tests/test_vision.py::test_refuting_browser_reliability_reinstates_visually_refuted_app -q`

## Traps

**No warrant, no attack edge, no `REFUTED` — and a run where that happened end to
end looks perfect.** `build_att` only emits `(carrier, warrant.target)` for a
carry pair whose warrant id resolves in the `warrants` map; an unresolvable pair
is skipped silently (`if w is None: continue`). With `att` empty, pass 1 accepts
everything, which is indistinguishable from "everything survived criticism".
Regression `jolt run-b4d6dfda0c20676a864a051fbc97bda4`: 851 events, 72 artifacts,
zero warrants, all `ACCEPTED`, `epistemic_checks_passed: true` — that root
predates the detector and its home was gitignored by the ladder, so it exists
only in the session that ran it (`docs/ERRATA.md` E7). The committed
demonstration is stress-triplet `run-6472629d` (orbit): `att` empty, everything
`ACCEPTED`, and the blindness finding fires. The detector for
that state is in `verification/report.py`, and it has to be, because this package
sees no rules and no calls. Upstream, `Harness.register_batch` refuses an
unregistered carried warrant and `verify_root` fails `carry-warrant`; the silent
skip here is safe only because of those two.
`check: grep -q "adjudication-blindness" src/deepreason/verification/report.py && grep -qE "^def _adjudication_blindness_findings\(" src/deepreason/verification/report.py && ! grep -rqi "blind" src/deepreason/adjudication/ && python -m pytest tests/test_adjudication.py::test_unregistered_warrant_rejected -q && python -c "import json,pathlib; from deepreason.adjudication.edges import build_att; from deepreason.adjudication.grounded import label0; from deepreason.harness import Harness; from deepreason.ontology import Artifact,Provenance,Status; from deepreason.verification.report import verify_root_report; c=Artifact(id='C',content_ref='inline:C',provenance=Provenance(role='critic'),warrants=['nope']); assert build_att({'C':c},{},{})==set(); assert set(label0({'C'},set()).values())=={'accepted'}; r='experiments/2026-08-02-stress-triplet/home-orbit/runs/run-6472629dbc5d408a733d472040671752'; h=Harness(r,read_only=True); assert (len(h.state.artifacts),len(h.warrants),len(h.state.att))==(42,0,0); assert set(h.state.status.values())=={Status.ACCEPTED}; rep=verify_root_report(pathlib.Path(r)); assert rep.valid and not rep.epistemic_checks_passed; assert sum(1 for f in rep.epistemic if f.check=='adjudication-blindness')==1; assert json.loads(pathlib.Path(r+'/run-result.json').read_text())['verification']['epistemic_checks_passed'] is False"`

**A `mention` ref on a validity node is inert — until the warrant's commitment is
a `rubric:`.** Then case-law closure treats *every* `mention` target on the nu as
a standard, and each of that standard's attackers becomes an attacker of the nu,
which the validity-node closure lifts onto every carrier. A decorative citation
added to a rubric warrant's nu therefore becomes load-bearing without the author
touching `edges.py`. `rules/crit.py` deliberately relies on the opposite side of
this: a property-violation warrant `mention`s the property "for readers and
reach" and gets its closure from `budget.extra["source_artifact"]` instead,
because its commitment is `program:`, not `rubric:`.
`check: python -c "from deepreason.adjudication.edges import build_att; from deepreason.ontology import Artifact, Commitment, Interface, Provenance, Warrant, WarrantType; from deepreason.ontology.artifact import Ref; A=lambda i,**k: Artifact(id=i, content_ref='inline:'+i, provenance=Provenance(role='critic'), **k); arts={x.id:x for x in [A('C',warrants=['w']),A('T'),A('N',interface=Interface(refs=[Ref(target='S',role='mention')])),A('S'),A('X',warrants=['wx'])]}; wx=Warrant(id='wx',target='S',type=WarrantType.ARGUMENTATIVE,validity_node='T'); w=Warrant(id='w',target='T',type=WarrantType.DEMONSTRATIVE,commitment='k',verdict='fail',validity_node='N'); f=lambda ev: build_att(arts,{'w':w,'wx':wx},{'k':Commitment(id='k',eval=ev)}); r=f('rubric:std-1'); p=f('program:prop-oracle'); assert ('X','N') in r and ('X','C') in r, sorted(r); assert ('X','N') not in p, sorted(p)"`

**Evidence closure follows the lineage, not the named artifact.**
`evidence_lineage` walks transitive `dependence` refs beneath each `evidence`
target, so an attack several hops below a screenshot still refutes the vision
critic that cited it and reinstates the app. That reach is intentional — evidence
invalidation had to stay an explicit attack-graph derivation rather than a hidden
status check — but it means adding a `dependence` ref to an evidence artifact
widens the blast radius of every warrant that ever cited it.
`check: python -c "from deepreason.adjudication.edges import build_att; from deepreason.ontology import Artifact, Interface, Provenance, Warrant, WarrantType; from deepreason.ontology.artifact import Ref; A=lambda i,**k: Artifact(id=i, content_ref='inline:'+i, provenance=Provenance(role='critic'), **k); arts={x.id:x for x in [A('C',warrants=['w']),A('T'),A('N',interface=Interface(refs=[Ref(target='E',role='evidence')])),A('E',interface=Interface(refs=[Ref(target='R',role='dependence')])),A('R'),A('X',warrants=['wx'])]}; att=build_att(arts,{'w':Warrant(id='w',target='T',type=WarrantType.ARGUMENTATIVE,validity_node='N'),'wx':Warrant(id='wx',target='R',type=WarrantType.ARGUMENTATIVE,validity_node='T')},{}); assert ('X','R') in att and ('X','N') in att and ('X','C') in att, sorted(att)"`

**Edges materialize only when both endpoints are registered, and the two
endpoints have different rules.** A warrant's *target* may dangle — import and
merge order is allowed to introduce a critic before its target, and the edge
appears when the target does — but its *validity node* may not:
`Harness._validate_warrant` rejects an unregistered `validity_node` at
registration time. Likewise a `dependence` ref to an unregistered artifact builds
no `dep` edge, so a cycle can be created by the registration that closes it
rather than by the one that declares it.
`check: python -m pytest tests/test_adjudication.py::test_mutual_attack_suspended tests/test_adjudication.py::test_dep_cycle_rejected -q && grep -q "validity_node {warrant.validity_node} not registered" src/deepreason/harness.py && grep -q "ref.target in artifacts" src/deepreason/adjudication/edges.py`

**`build_att` is a full recompute with a quadratic inner scan, and
`Harness._adjudicate` calls it after every committed event.** The fixpoint rescans
`list(att)` once per carrier per pass. This is why opening a root replays with
`adjudicate=False` and adjudicates once at the end, and why `Harness.transitions()`
keeps an incremental shadow: the from-scratch per-event rewalk was measured
quadratic in the log length. Any closure rule added to the fixpoint pays that cost
on every event of every run.
`check: grep -q "was measured quadratic" src/deepreason/harness.py && grep -qE "^    def transitions\(" src/deepreason/harness.py && grep -q "INCREMENTAL: the shadow" src/deepreason/harness.py && grep -c "for x, target in list(att)" src/deepreason/adjudication/edges.py | grep -qx 4`

**Changing anything here changes the status map of every committed root.** Labels
are never read back from the log — reopening a root replays the events and
recomputes them, so a semantics change does not "improve" old runs, it makes them
disagree with the `att+` and `status_changed` deltas they recorded at write time.
Treat this package under `DR-INV-frozen-surfaces`: fix readers, not labels.
`check: python -c "import json,pathlib; from deepreason.harness import Harness; from deepreason.ontology import Status; r='experiments/live_engaged_2026-07-27/run-f4fa6663e5412d64df943a5a22342baf'; rec={tuple(p) for l in pathlib.Path(r+'/log.jsonl').read_text().splitlines() for p in json.loads(l)['state_diff']['att+']}; h=Harness(r, read_only=True); assert rec and rec=={tuple(p) for p in h.state.att}; assert sum(1 for s in h.state.status.values() if s==Status.REFUTED)==1"`
