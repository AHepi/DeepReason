<!-- DR-CON-warrants-and-attacks -->
Verified-at: 7b82206d
Verify: python tools/docs_verify.py
Owns: src/deepreason/rules/warrants.py, src/deepreason/adjudication/edges.py, src/deepreason/adjudication/grounded.py, src/deepreason/adjudication/support.py, src/deepreason/ontology/warrant.py
Seams: 
Seams-undocumented: adjudication x warrants-and-attacks, harness x warrants-and-attacks, ontology x warrants-and-attacks, rules x warrants-and-attacks, verification x warrants-and-attacks

# Warrants and attack edges — the only route to REFUTED

## What it is

Nothing in this system is refuted by being disliked. An artifact reaches
`Status.REFUTED` through one chain and no other: some artifact CARRIES a
registered `Warrant` naming it as target, that carriage materializes an attack
edge in `att`, and the grounded extension finds the attacker accepted. Every
link is mechanical — a bare verdict is not an edge, an unregistered warrant is
not an edge, and the label is a pure function of `att` and `dep`. The concept is
spread across five files because the chain deliberately separates *who may mint
a warrant* (`rules/warrants.py` and the paths that call it) from *what a warrant
does to the graph* (`adjudication/`), so no rule can reach a Status except by
putting an attackable object on the record first. What makes it hard to navigate
is that the guards protecting a target from refutation do not live in the
adjudicator or in the criticism rule — they sit at each mint site, and the two
supremacy guards are not the same predicate.

## Where it lives

| Aspect | File | Symbol |
|---|---|---|
| The warrant record and its two types | `src/deepreason/ontology/warrant.py` | `Warrant`, `WarrantType` — `DEMONSTRATIVE`, `ARGUMENTATIVE` |
| Status vocabulary the chain terminates in | `src/deepreason/ontology/state.py` | `Status`, `EpistemicState.carries` |
| The only place a DEMONSTRATIVE warrant is minted | `src/deepreason/rules/warrants.py` | `register_fail_warrant` (ν + warrant + critic, one triple) |
| One (κ, target) fail verdict at a time | `src/deepreason/rules/warrants.py` | `verdict_on_record`, `skip_if_on_record` |
| Execution supremacy predicate | `src/deepreason/rules/warrants.py` | `execution_backed` |
| Prose-immunity predicate (a superset) | `src/deepreason/rules/warrants.py` | `formally_backed` |
| What counts as an execution verdict | `src/deepreason/oracle.py` | `EXEC_PROGRAMS` |
| What counts as substantive rather than structural | `src/deepreason/measures/reach.py` | `_substantive`, `_STRUCTURAL_PROGRAMS` |
| Carriage → attack edge (the base relation) | `src/deepreason/adjudication/edges.py` | `build_att` `carry_pairs` / `carriers` |
| Validity-node closure (ν falls ⇒ every carrier falls) | `src/deepreason/adjudication/edges.py` | `build_att` fixpoint, final block |
| Case-law closure (rubric standards) | `src/deepreason/adjudication/edges.py` | `build_att`, `RefRole.MENTION` branch |
| Evidence closure and its dependence lineage | `src/deepreason/adjudication/edges.py` | `evidence_lineage`, `RefRole.EVIDENCE` |
| Source-artifact closure (LLM-proposed ground truth) | `src/deepreason/adjudication/edges.py` | `budget.extra["source_artifact"]` branch |
| Support edges and their DAG constraint | `src/deepreason/adjudication/edges.py` | `build_dep`, `toposort`, `DependenceCycleError` |
| Pass 1 — grounded extension and raw labels | `src/deepreason/adjudication/grounded.py` | `grounded_extension`, `label0` |
| Pass 2 — support cascade to `Status` | `src/deepreason/adjudication/support.py` | `final_labels` |
| Where the whole graph is recomputed | `src/deepreason/harness.py` | `Harness._adjudicate` (every applied event; bulk replay passes `adjudicate=False` and recomputes once at the end) |
| Warrant well-formedness at the write boundary | `src/deepreason/harness.py` | `_validate_warrant`, `register_batch` |
| Carriage as an explicit append-only relation | `src/deepreason/harness.py`, `src/deepreason/ontology/event.py` | `Harness.carried_warrant_ids` / `carrier_ids`; `StateDiff.carry_add` (wire alias `carry+`) |
| Rubric transcript conformance | `src/deepreason/informal/trial.py` | `conforming_transcript`, `transcript_blob` |
| Formal supremacy gate for prose | `src/deepreason/informal/trial.py` | `_argument_trial_steps` |
| Pairwise-preference gate | `src/deepreason/informal/trial.py` | `pairwise_discriminate` |
| Typed non-outcomes (no warrant, but on the record) | `src/deepreason/informal/trial.py` | `_decline`, `_block` |
| Execution supremacy in the criticism rule | `src/deepreason/rules/crit.py` | `crit_argumentative`, `crit_argumentative_batch` |
| Mechanical mint sites (demonstrative) | `rules/crit.py`, `rules/act.py`, `rules/experiment.py`, `measures/hv.py`, `workloads/formal.py`, `informal/audits.py`, `skills/adoption.py`, `informal/trial.py` | twelve `register_fail_warrant` calls |
| Argumentative mint sites | `informal/trial.py` (×2), `rules/vision.py`, `rules/experiment.py`, `imports.py` | five hand-built `Warrant(...)` constructions |
| The blindness report when the chain never fires | `src/deepreason/verification/report.py` | `_adjudication_blindness_findings` |

## The rules it obeys

**No registered warrant, no edge — and no registered target, no edge either.**
`build_att` looks each carried id up in the `warrants` map and drops it if
absent; it adds `(carrier, w.target)` only when the target is a registered
artifact. Dangling refs are legal (import/merge order) and take effect when the
target appears.
`check: python -c "from deepreason.adjudication.edges import build_att; from deepreason.ontology.artifact import Artifact, Provenance; from deepreason.ontology.warrant import Warrant, WarrantType; p=Provenance(role='critic'); c=Artifact(id='C', content_ref='inline:c', warrants=['w'], provenance=p); t=Artifact(id='T', content_ref='inline:t', provenance=p); w=Warrant(id='w', target='T', type=WarrantType.ARGUMENTATIVE, validity_node='N'); assert build_att({'C':c,'T':t}, {}, {}) == set(); assert build_att({'C':c}, {'w':w}, {}) == set(); assert build_att({'C':c,'T':t}, {'w':w}, {}) == {('C','T')}"`

The write boundary enforces the same thing earlier: registering an artifact that
claims a warrant nobody provided or registered is a `WellFormednessError`, so an
edge can never be asserted by content alone.
`check: python -m pytest tests/test_adjudication.py -k unregistered_warrant_rejected -q`

**Carriage is a relation, not a field.** `state.carries` is the authority;
`Artifact.warrants` is the legacy on-record encoding and `build_att` unions
both. This is what lets one criticism artifact attack a second target without
changing its content-addressed id — a re-registered `(artifact, warrant)` pair
commits even when the artifact dedupes.
`check: python -c "from deepreason.adjudication.edges import build_att; from deepreason.ontology.artifact import Artifact, Provenance; from deepreason.ontology.warrant import Warrant, WarrantType; p=Provenance(role='critic'); bare=Artifact(id='C', content_ref='inline:c', provenance=p); t=Artifact(id='T', content_ref='inline:t', provenance=p); w=Warrant(id='w', target='T', type=WarrantType.DEMONSTRATIVE, validity_node='N'); assert build_att({'C':bare,'T':t}, {'w':w}, {}) == set(); assert build_att({'C':bare,'T':t}, {'w':w}, {}, [('C','w')]) == {('C','T')}"`

**The edge builder is blind to `WarrantType`.** Demonstrative and argumentative
warrants produce the identical edge; the type is a claim about the warrant's
provenance for readers and audits, and it buys no extra force in the graph. All
the asymmetry between the two lives upstream, in what each mint site is allowed
to do.
`check: python -c "from deepreason.adjudication.edges import build_att; from deepreason.ontology.artifact import Artifact, Provenance; from deepreason.ontology.warrant import Warrant, WarrantType; p=Provenance(role='critic'); c=Artifact(id='C', content_ref='inline:c', warrants=['w'], provenance=p); t=Artifact(id='T', content_ref='inline:t', provenance=p); e=lambda ty: build_att({'C':c,'T':t}, {'w': Warrant(id='w', target='T', type=ty, validity_node='N')}, {}); assert e(WarrantType.ARGUMENTATIVE) == e(WarrantType.DEMONSTRATIVE) == {('C','T')}"`

**`WarrantType.DEMONSTRATIVE` is written in exactly one file.** Twelve call
sites across eight modules mint demonstrative warrants, and every one of them
goes through `register_fail_warrant` — the id scheme `w:<commitment>:<target>`,
the ν wiring and the duplicate guard exist once. A hand-built demonstrative
warrant anywhere else is the defect this arrangement is designed to prevent.
`check: test "$(grep -rl 'WarrantType.DEMONSTRATIVE' src/deepreason --include=*.py)" = src/deepreason/rules/warrants.py`

**A rubric-derived demonstrative warrant must carry a conforming transcript**,
and the harness — not the trial — enforces it, so the guard is unbypassable by
any caller. Conformance is re-checkable by program: a case, an answer, a
decisive point that actually occurs in the exchange, and a checks dict.
`check: python -c "import inspect, json; from deepreason.harness import Harness; from deepreason.informal.trial import conforming_transcript as ct; s=inspect.getsource(Harness._validate_warrant); assert 'conforming_transcript' in s and 'rubric:' in s; t=lambda dp: json.dumps({'case':'c','answer':'a','ruling':{'verdict':'fail','decisive_point':dp},'checks':{}}); assert ct({'x':t('c')},'x') and not ct({'x':t('zzz')},'x')"`

**Labels are a pure function of the graph.** `label0` takes nodes and `att`;
`final_labels` takes those labels and `dep`. No measure, provenance role,
school, novelty score or Pareto rank is in scope at the point the Status is
computed — measures act upstream via Spawn, budgeted commitments or attention,
never here.
`check: python -c "import inspect; from deepreason.adjudication.grounded import label0; from deepreason.adjudication.support import final_labels; from deepreason.harness import Harness; assert list(inspect.signature(label0).parameters) == ['nodes','att']; assert list(inspect.signature(final_labels).parameters) == ['label0','dep_edges']; s=inspect.getsource(Harness._adjudicate); assert not any(t in s for t in ('state.hv','state.reach','school','provenance','rank'))"`

**REFUTED means attacked from the grounded extension, and nothing else.** Mutual
attack is `suspended`, not refuted. And refuting a premise never refutes its
dependents: pass 2 gives them `SUSPENDED_UNSUPPORTED`, because orphaned is not
false.
`check: python -c "from deepreason.adjudication.grounded import label0 as l; from deepreason.adjudication.support import final_labels as f; from deepreason.ontology.state import Status as S; assert l({'a','b'}, [('b','a')]) == {'a':'refuted','b':'accepted'}; assert l({'a','b'}, [('a','b'),('b','a')]) == {'a':'suspended','b':'suspended'}; assert f({'d':'accepted','p':'refuted'}, [('d','p')]) == {'p':S.REFUTED,'d':S.SUSPENDED_UNSUPPORTED}"`

**Four closure rules widen `att`, all of them by lifting an existing attack onto
a validity node and then onto every carrier of the warrant beneath it.**
Validity-node closure is the base; case-law closure attacks the ν of every
rubric warrant citing a refuted standard; evidence closure follows
`RefRole.EVIDENCE` through its whole dependence lineage; source-artifact closure
collapses every verdict a refuted proposed property produced. Reinstatement is
derived from the fixpoint, never curated — the closures run to convergence, so a
refuted standard reinstates its victims in the same pass.
`check: python -m pytest tests/test_adjudication.py -q`

**Nothing in the adjudicator knows about supremacy, and nothing is deleted.**
The guards decide only whether an edge is CREATED; once on the graph an edge is
adjudicated like any other, and execution can still refute later.
`check: grep -q 'def build_att' src/deepreason/adjudication/edges.py && ! grep -qE 'execution_backed|formally_backed' src/deepreason/adjudication/edges.py`

**`formally_backed` is a strict superset of `execution_backed`.** Execution
backing needs at least one `EXEC_PROGRAMS` commitment, all passing. Formal
backing needs at least one commitment that is evaluable AND substantive, all
passing — which adds `predicate:` criteria and substantive `program:` checks.
Both are all-or-nothing on the commitments they see: a target with none of them
gets no protection at all, and a target with one already failing gets none
either, because a mechanically defeated claim is not worth shielding.
`check: python -m pytest tests/test_prose_refutation_boundaries.py -k "formal_backing or structural_program or failing_formal" -q`

**Evaluable is not enough — the commitment must be SUBSTANTIVE.** Safe skeleton
compilation turns a conjecturer's own forbidden cases into `program:`
commitments, so a candidate could otherwise attach `program:json-wf` and
immunise itself against all criticism by being well-formed. Structural
well-formedness proves nothing about the subject, so it protects nothing about
the subject; `_STRUCTURAL_PROGRAMS` is disjoint from `EXEC_PROGRAMS`. The set is
DERIVED from `programs.PROGRAMS`' declared `class_`, never hand-listed beside it
— a second copy of it drifted five names deep and let a well-formedness gate
immunise prose (`DR-SUB-evaluation` Traps; tranche
`experiments/2026-08-22-reach-structural-programs-fix`).
`check: python -c "from deepreason.oracle import EXEC_PROGRAMS; from deepreason.measures.reach import _substantive, _STRUCTURAL_PROGRAMS as sp; from deepreason.ontology import Commitment; from deepreason.programs import programs_by_class; assert EXEC_PROGRAMS == {'exec_oracle','property_oracle','dataset_oracle'}; assert not (EXEC_PROGRAMS & sp); assert set(programs_by_class()['structural']) == set(sp); assert all(not _substantive(Commitment(id='k', eval='program:' + n)) for n in sp); assert not _substantive(Commitment(id='k', eval='program:json-wf')); assert _substantive(Commitment(id='k', eval=\"predicate:'x' in content\"))"`

**`formally_backed` has exactly ONE call site — `_argument_trial_steps`.** The
defended trial is the only path where a free-form textual case against a single
target mints a warrant, so it is the only place the widened guard belongs. Every
other guarded mint site keeps the narrower `execution_backed`, and that
asymmetry is deliberate rather than an oversight: `pairwise_discriminate` rules
on a rivalry rather than on one target, and `crit_vision`'s case is
image-grounded, not prose. Do not read "prose cannot refute a formal claim" as a
property of the whole informal family — it is a property of one function.
The criticism rule keeps `execution_backed` for a different reason again: its
guard also governs whether a case is RECORDED. Problem criteria are instantiated
into every candidate's interface, so widening it there would suppress the
scrutiny record for every target carrying a passing criterion — losing the case
entirely instead of declining to act on it.
`check: python -c "import inspect; from deepreason.informal import trial; from deepreason.rules import vision, crit; assert sum('formally_backed(' in l for l in inspect.getsource(trial).splitlines()) == 1; assert 'formally_backed(harness, target_id)' in inspect.getsource(trial._argument_trial_steps); assert 'execution_backed(harness, target_id)' in inspect.getsource(vision.crit_vision); assert 'formally_backed' not in inspect.getsource(vision) + inspect.getsource(crit)"`
`check: python -m pytest tests/test_prose_refutation_boundaries.py -k "resists_prose or structural_only_target" -q`

**The refusal is typed, it precedes any provider spend, and it precedes the
authority branch.** `_argument_trial_steps` declines before the defender or
judge call; both the trial and the criticism rule consult their guard strictly
above the authority branch, so no authority mode — including one that does not
exist yet — can reach past it. The decline reason keeps the historical spelling
`execution-backed` even though the guard widened; see DR-INV-frozen-surfaces.
`check: python -m pytest tests/test_prose_refutation_boundaries.py -k "records_scrutiny_for_a_formal_target or guard_is_consulted_before or refused_by_type" -q`

**A pairwise preference cannot refute an execution-backed loser.** The rivalry
stands unresolved — exactly as for a `neither` ruling — and the judge calls are
still logged. This is the same principle applied to §10.2's comparison path
rather than to a case against a single target.
`check: grep -q 'if execution_backed(harness, loser):' src/deepreason/informal/trial.py`

**Two argumentative mint sites consult no supremacy guard at all.**
`imports.register_epistemic_import_failure` (a demonstrated import-plan
violation, typed argumentative) and `experiment.relevance_trial` (a ruling that
a proposed property does not follow from the problem) construct their warrants
directly. The three LLM-preference paths — defended trial, pairwise, vision —
are guarded; these two are not. Read this before assuming the guard is a
property of the type rather than of the call site.
`check: python -c "import inspect; from deepreason import imports; s=inspect.getsource(imports.register_epistemic_import_failure); assert 'WarrantType.ARGUMENTATIVE' in s and 'backed' not in s"`

**A run in which criticism ran and `att` stayed empty is reported.**
`_adjudication_blindness_findings` is whole-run, not windowed, and is an
epistemic finding: it does not gate `valid`.
`check: python -m pytest tests/test_adjudication_blindness.py -k attacked_nothing_is_flagged -q`
`check: python -c "import inspect; from deepreason.verification.report import VerificationReportV2 as R, _adjudication_blindness_findings as f; b=inspect.getsource(f).split('\"\"\"')[2]; assert 'log.read()' in b and 'recent_semantic_events' not in b; assert '\"epistemic\"' in b; v=inspect.getsource(R.valid.fget); assert 'self.integrity_valid and self.security_valid' in v and 'epistemic' not in v"`

## Where to change what

| To change... | Edit | Test |
|---|---|---|
| Add a mechanical refutation route (a new fail-verdict source) | the owning rule, calling `rules/warrants.py` `register_fail_warrant` — never a hand-built demonstrative `Warrant` | `python -m pytest tests/test_adjudication.py tests/test_act.py -q` |
| Change what execution protects | `oracle.py` `EXEC_PROGRAMS` — read only by `execution_backed` | `python -m pytest tests/test_prose_refutation_boundaries.py -k boundary_is_execution_backing -q` |
| Change what counts as a formal claim | `measures/reach.py` `_STRUCTURAL_PROGRAMS` / `_substantive` — shared with the reach measure, so a change moves both | `python -m pytest tests/test_prose_refutation_boundaries.py -k "structural_program or formal_backing" -q` |
| Change which targets prose may not refute | `informal/trial.py` `_argument_trial_steps` guard — NOT `rules/crit.py`, see the rule above | `python -m pytest tests/test_prose_refutation_boundaries.py -k "resists_prose or refused_by_type" -q` |
| Add a closure rule (a new way an attack propagates) | `adjudication/edges.py` `build_att` fixpoint; a new `RefRole` also touches `ontology/artifact.py` | `python -m pytest tests/test_adjudication.py tests/test_replay.py -q` |
| Change the duplicate-verdict guard | `rules/warrants.py` `verdict_on_record` and every `skip_if_on_record=True` caller | `python -m pytest tests/test_hv.py tests/test_workload_formal.py -q` |
| Change how a Status is derived from edges | `adjudication/grounded.py` `label0`, `adjudication/support.py` `final_labels` — this reinterprets every recorded root; DR-INV-frozen-surfaces | `python -m pytest tests/test_replay.py tests/test_persistence_invariants.py -q` |
| Add a field to `Warrant` | `ontology/warrant.py` — a frozen record format on disk in every root | `python -m pytest tests/test_replay.py tests/test_ontology.py -q` |

## Traps

- **A run where the whole chain never fires, reported as clean.** jolt
  `run-b4d6dfda0c20676a864a051fbc97bda4` finished with `len(state.att) == 0`,
  zero warrants across 851 events, all 72 artifacts ACCEPTED, and
  `epistemic_checks_passed: true`. Total blindness was the case the windowed
  detector was least able to see, and verification called the detector only to
  prove it did not raise, discarding every flag. Fixed 2026-07-31 with the
  whole-run derivation in `verification/report.py`; the measurement over all 42
  roots was **26 newly flagged, 0 whose `valid` moved**. The residue matters
  more than the fix: text runs default to `OBSERVE_ONLY`, so almost none of them
  ever mint a warrant. Evidence: `experiments/live_jolt_2026-07-31/RESULTS.md`,
  `tests/test_adjudication_blindness.py`.
- **Reading `evaluable` as the formal boundary.** SPEC.md's A1 did, in the
  2026-08-01 tranche. The implemented line is narrower on one axis and wider on
  another: `execution_backed` needs an exec oracle, `formally_backed` needs
  substantive evaluability, and a `predicate:` commitment is evaluable but not
  execution-backed. The two readings protect different sets and the difference
  is invisible from either function alone — which is why
  `test_the_formal_boundary_is_execution_backing_and_not_evaluability` asserts
  it rather than describing it.
- **Widening the guard in the criticism rule instead of the trial.** Same
  tranche, corrected at step 18. It looks like the same guard in two places; it
  is not. `crit.py`'s guard decides whether a case is RECORDED, `trial.py`'s
  decides whether a warrant is MINTED. Widening the recording one deletes
  scrutiny evidence and moves toward adjudication blindness, not away from it.
  Also DR-INV-frozen-surfaces, Traps.
- **Assuming a critic artifact committed because a warrant was built.** Critic
  artifacts are content-addressed: a byte-identical critic (same target, same
  spec, same decisive quote from a second rubric κ) dedupes and commits nothing,
  while the carriage relation still commits. The 1M arrow-of-time run leaked 13
  judge rulings (~770 tokens each) by attaching the LLM call unconditionally —
  `verify_root` meter 1 000 214 vs log 990 192, delta 10 022. Both trial paths
  now compare `critic.id` against the pre-registration artifact set before
  removing the call from `calls`. Evidence: `docs/MINI_STRESS_REPORT.md` §F4,
  `tests/test_trial_accounting.py`.
- **Expecting `verdict_on_record` to see an argumentative warrant.** It matches
  on `(commitment, target)`, and all five argumentative warrants in the tree
  leave `commitment` unset. The duplicate-verdict guard is therefore a guard on
  mechanical verdicts only; the argumentative paths dedupe by content address
  and by their own id schemes — `w:argtrial:…`, `w:pairwise:…`, `w:vision:…`,
  and the two unguarded ones, `w:prop-rel:…` (`experiment.relevance_trial`) and
  `w:import:…` (`imports.register_epistemic_import_failure`) — instead.
- **Treating `Artifact.warrants` as the carriage relation.** It is the legacy
  encoding, kept so old roots replay unchanged. `state.carries` is what a new
  log writes and what `carried_warrant_ids` / `carrier_ids` read; `build_att`
  unions the two. Iterating only the artifact field misses every warrant
  acquired after the carrier's content was fixed.
