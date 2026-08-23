<!-- DR-INV-axiom-basis -->
Verified-at: 03b1edf4
Verify: python -m pytest tests/test_calculus_standing.py tests/test_calculus_frame_assertions.py tests/test_proof_debt.py -q
Owns: 
Seams: 
Seams-undocumented: 

# The axiom basis — eleven claims, who proves each, and who must not break it

## What this is, and why it is an `INV-` rather than a `CON-`

`docs/POIETIC_CALCULUS_FORMALIZED.md` §17 gives a minimal axiom set sufficient
for its thirteen results; v0.1's Axiom 4.1 (Genesis Inertness) joins it from the
foundational source. Together they are the backbone the v2 calculus program is
built on, and the reason they need a document is stated in the program ladder
itself (`experiments/2026-08-14-change-calculus-reconciliation-v2/LADDER.md`
§5b): **an axiom nobody answers for is an axiom nobody is testing.**

So every row below names two things, not one. The rung that PROVES it — the
tranche whose gate first exhibits the property — and the rungs that PRESERVE
it, which is where a later change is most likely to break it by accident.

This is an `INV-` document because the rows are obligations on future work, not
descriptions of a subsystem. It owns no files: an axiom is not a module, and
giving it an `Owns:` list would make some package look like the axiom's
custodian when the whole point is that every package is.

**Scope, stated so the document is not over-read.** A `check:` here proves the
axiom holds where the CURRENT tree can exhibit it. It does not prove the axiom
in general, and for the four axioms whose proving rung has not landed yet the
row says so plainly rather than shipping a check that cannot fail — a vacuous
check is worse than an admitted gap, because it reports success.

## The eleven

| Axiom | Statement (compressed) | Proved at | Preserved by |
|---|---|---|---|
| **A1** | the log is append-only; state is a pure fold over it | already true — recorded Rung 1 | every rung; **Rung D** re-proves it for receipts |
| **A2** | all verdicts are finite-budget deterministic results | already true | every rung; **Rung D** re-proves it for a re-run kernel check |
| **A3** | status = grounded attack pass, then the acyclic support pass | already true | Rungs 2, 3, 4, 6, **D** |
| **A4** | standing is a derived consultation relation and never enters status computation | **Rung 4** | Rungs 5, 6, 7 |
| **A5** | a frame assertion mentions but does not depend on its subject | **Rung 2** (attributions), **Rung 4** (frame assertions) | Rung 3b, **Rung D** (derivation manifests mention their subject). Rung D's THIRD site — localizations — is PARKED and does not yet answer for it |
| **A6** | consulted frame assertions satisfy frame-separation | **Rung 3b** | Rungs 4, 7 |
| **A7** | problems immutably record their pose-time frame assertions | **Rung 4** | Rungs 6, 7 |
| **A8** | reach can spawn promotion problems but cannot directly alter labels | **Rung 5** — NOT YET LANDED | Rung 8 |
| **A9** | render, measures, diagnostics and knowledge views act only through attention | **Rung 6** (render), **Rung 8** (diagnostics) — NOT YET LANDED | Rungs 2, 5, **D** (a receipt is a readout and moves no label) |
| **A10** | all set ordering, numerical evaluation, sampling and serialization are canonical | already true — re-proved by every rung's replay determinism | every rung; **Rung D** logs the rent sample as a canonical artifact rather than a blob |
| **Ax 4.1** | **Genesis Inertness** — appraisal predicates are invariant under permutation of provenance; origin confers neither warrant nor stigma | stated here; **no rung may violate it** | every rung; **Rung D** — neither `receipt()` nor a manifest reads provenance |

## A1 — append-only log, state a pure fold

Two independent materializations of one log agree, and reopening a root
read-only writes nothing. `verify_root`'s first check is the fold's own
determinism.

`check: grep -q "two replays of the same log produced different state" src/deepreason/invariants.py`
`check: python -m pytest tests/test_calculus_standing.py::test_standing_is_recomputed_from_the_log_and_never_stored -q`

**Rung D extends the fold to proof debt.** A receipt is built on every call from
replayed state and stored nowhere, so there is no receipt record that could
disagree with the log implying it; and because nothing is rewritten, a
judgment's dependents are invalidated ON RECOMPUTATION rather than
retroactively — the log's prefix before an attack replays to exactly what it
always replayed to.

`check: python -m pytest tests/test_proof_debt.py -k "recomputed_from_the_log or replays_identically or recomputation_not_retroactively" -q`

## A2 — finite-budget deterministic verdicts

Every program in the registry is a pure function returning a typed verdict, and
the scope predicate added at Rung 4 is bounded by construction: it is validated
whole before evaluation, under explicit depth and node ceilings, so it cannot
fail part-way through and cannot run long.

`check: python -c "from deepreason.calculus.scope import _MAX_DEPTH, _MAX_NODES; assert _MAX_DEPTH > 0 and _MAX_NODES > 0"`
`check: python -m pytest tests/test_calculus_scope_predicate.py::test_the_same_problem_and_state_give_the_same_answer -q`

**Rung D adds the case a recorded verdict cannot settle.** A derivation
manifest records what its author observed, but `proof_debt.receipt` never reads
that back: it RE-RUNS every re-runnable kernel check and reports the current
verdict beside the recorded one. A check with no runnable program is reported
`not-rerunnable`, never as a pass — "we could not check" must not look like "we
checked and it was fine", which is the same typed abstention the rent sweep
records with no variator. That is A2 in its sharpest form: a verdict is what
the budgeted function returns now, not what somebody wrote down.

`check: python -m pytest tests/test_proof_debt.py::test_a_receipt_reruns_its_kernel_checks_rather_than_reading_them_back -q`
`check: python -c "from deepreason.proof_debt import NOT_RERUNNABLE; assert NOT_RERUNNABLE == 'not-rerunnable'"`

## A3 — two passes, in that order

`_adjudicate` is the sole writer of `state.status` and calls the label function
exactly once: grounded attack pass (`compute_label0` over `att`), then the
acyclic support pass (`final_labels` over `dep`). One writer, one call.

`check: python -c "src=open('src/deepreason/harness.py').read(); assert src.count('self.state.status = ')==1; assert src.count('final_labels(')==1; assert 'compute_label0' in src"`

## A4 — standing is derived, and never enters status computation

**PROVED at Rung 4**, in the strongest form available: two runs over the same
graph, one carrying frame assertions and one carrying none, produce IDENTICAL
labels — with the subject REFUTED in both, because a run where standing could
only agree with the label has nothing to catch. Two structural companions guard
what the behavioural test cannot: `_adjudicate` names no standing symbol, and
nothing in `adjudication/` imports the view.

The behavioural test was mutation-proven RED before it was trusted, and the
mutation had to be revised twice before it bit
(`experiments/2026-08-22-change-rung4-frame-assertions/VALIDATION.md`).

**How a later rung breaks this by accident:** by making render or schedule read
standing and then letting that value flow back into anything `_adjudicate`
consults. The seam that owns the boundary is `DR-SEAM-adjudication-x-authority`.

`check: python -m pytest tests/test_calculus_standing.py::test_frame_assertions_do_not_move_a_single_label tests/test_calculus_standing.py::test_label_computation_names_no_standing_symbol tests/test_calculus_standing.py::test_no_adjudication_module_imports_the_standing_view -q`
`check: python -c "from deepreason.ontology import Event, EpistemicState; from deepreason.ontology.problem import Problem; assert not [f for m in (Problem, EpistemicState, Event) for f in m.model_fields if 'standing' in f or 'frame' in f]"`

## A5 — mention, never depend, on the subject

**Rung 2** proved the attribution half; **Rung 4** the frame-assertion half. The
compiler is the only authority on ref roles, and it emits `MENTION` for the
subject in both. Well-formedness names the LAW when an artifact declares a
dependence on its subject anyway, rather than reporting a generic interface
mismatch — which is what lets a reader tell a violated separation from a botched
registration.

`check: python -c "
from deepreason.calculus.claims import FrameAssertionV1, PremiseAttributionV1
from deepreason.calculus.compiler import compile_interface
s = {'schema': 'declarative-scope.v1', 'predicate': {'const': True}}
f = compile_interface(FrameAssertionV1(subject_ref='b', scope=s, departure_protocol='p', reach_case_refs=['c']))
assert {r.target: r.role.value for r in f.refs} == {'b': 'mention', 'c': 'dependence'}
a = compile_interface(PremiseAttributionV1(problem_subject_ref='s', premise_ref='x'))
assert {r.target: r.role.value for r in a.refs} == {'s': 'mention', 'x': 'mention'}
"`
`check: python -m pytest tests/test_calculus_frame_assertions.py::test_an_assertion_that_depends_on_its_subject_fails_well_formedness tests/test_calculus_claim_substrate.py::test_an_attribution_mentions_its_premise_and_never_depends_on_it -q`

## A6 — consulted assertions satisfy frame-separation

**PROVED at Rung 3b**, and Rung 4 PRESERVES it by INVOKING that predicate rather
than re-deriving the graph condition: `standing.py::consultability_of` calls
`separation.consultability` and returns its `FRAME_NOT_SEPARATED` code unchanged.
Two definitions of one invariant would leave no way to tell which the record
meant.

The mention law is necessary and NOT sufficient — that is the whole reason A6
exists beside A5. An assertion can mention its subject and still share an
adjudication component with it, whenever a record it DEPENDS on depends on that
subject.

`check: python -c "import inspect; from deepreason.calculus import standing; src=inspect.getsource(standing.consultability_of); assert 'consultability(harness, assertion_id, body.subject_ref)' in src" && python -m pytest tests/test_calculus_frame_assertions.py::test_an_unseparated_assertion_is_unconsultable_with_rung3bs_own_code -q`

## A7 — problems immutably record their pose-time frame assertions

**PROVED at Rung 4**, and the mechanism is that there is no mechanism: `Problem`
is a frozen record with no frame field, and an assertion reaches a problem only
through `addr`, the ordinary addressing relation, at registration time. Nothing
can rewrite which assertions a problem was posed under, because nothing stores
it — the log's own append-only ordering is the record.

`check: python -c "
from deepreason.ontology.problem import Problem
assert Problem.model_config.get('frozen') is True, Problem.model_config
assert sorted(Problem.model_fields) == ['criteria', 'description', 'id', 'provenance']
"`
`check: python -m pytest tests/test_calculus_standing.py::test_no_field_was_added_to_problem_state_or_event -q`

## A8 — reach spawns promotion problems, and cannot alter labels

**NOT YET PROVED — Rung 5 owns it**, and this row is the obligation rather than
the discharge. What Rung 4 established that Rung 5 will build on: a promotion
problem is an ordinary `Problem` with `SpawnTrigger.PROMOTION`, and being
addressed to one changes nothing about any label — it changes only whether an
assertion is CONSULTED.

Half of A8 is checkable today, and only half. Reach measures ground no reach
from structural programs, so a well-formed frame assertion cannot buy its own
promotion case.

`check: python -c "from deepreason.measures.reach import _STRUCTURAL_PROGRAMS as S; assert {'frame_assertion_wf','problem_subject_wf','premise_attribution_wf'} <= S"`

No check is offered for the spawn half. Rung 5 must add one here in the same
commit that lands nomination.

## A9 — render, measures and diagnostics act only through attention

**NOT YET PROVED — Rung 6 (render) and Rung 8 (diagnostics) own it.** Rung 4's
contribution is negative and worth stating: the standing view is consumed by
render and schedule ALONE, it is read-only, and it reaches no LLM seat, so
nothing this rung added can act other than through attention.

`check: python -c "import ast,pathlib; t=ast.parse(pathlib.Path('src/deepreason/calculus/standing.py').read_text()); mods=[(n.module or '') for n in ast.walk(t) if isinstance(n,ast.ImportFrom)]+[a.name for n in ast.walk(t) if isinstance(n,ast.Import) for a in n.names]; assert not any(p in m for m in mods for p in ('llm','adapter','seat','provider','qualification','adjudication')), mods"`

Rung 6 must add the render-side check here in the same commit.

## A10 — canonical ordering, evaluation, sampling, serialization

Re-proved by every rung's replay determinism. Rung 4's own contribution: the
standing view sorts its grants by assertion id, so two renders of one root agree
byte for byte, and the scope document is stored as authored bytes rather than as
a compiled object, so its content address does not move when the compiler does.

`check: python -c "import inspect; from deepreason.calculus.standing import standing_view; assert 'sorted(' in inspect.getsource(standing_view)"`
`check: python -c "
from deepreason.calculus.claims import FrameAssertionV1, encode
s = {'schema': 'declarative-scope.v1', 'predicate': {'const': True}}
b = FrameAssertionV1(subject_ref='b', scope=s, departure_protocol='p')
assert encode(b) == encode(b)
assert encode(b).index('\"departure_protocol\"') < encode(b).index('\"subject_ref\"')
"`

## Ax 4.1 — Genesis Inertness

> All appraisal predicates are invariant under permutation of provenance
> records; origin confers neither warrant nor stigma.

**No rung proves this one, and no rung may violate it.** LADDER §5b names the
shape it will be violated in, and it is worth quoting because it is a shape, not
a lapse: *"a ranking, a gate or a criterion that reads WHO or WHAT produced a
content instead of what it declares."* Attention MAY read provenance
(`RECONCILIATION.md` V-4); appraisal may NOT.

The line is easy to cross while doing something reasonable. Rung 4's own
near-miss shape, recorded as a worked example: it would have been natural to
make the standing view rank grants by the provenance role that authored the
assertion, or to make `consultability_of` prefer an assertion authored by a
conjecturer over one imported. Neither happens; consultation reads the body, the
addressing, the label and the graph, and nothing about who wrote it.

`check: python -c "
import pathlib, re
src = pathlib.Path('src/deepreason/calculus/standing.py').read_text()
# provenance.trigger is a field of the PROBLEM record -- what the problem is.
# Anything else under provenance is origin, and appraisal may not read it.
assert not re.search(r'provenance\.(?!trigger|from_)', src), 'standing reads provenance as origin'
# .role here is EDGE role (mention/dependence/evidence), never an authoring
# seat. Anchored to where the name came FROM rather than to what it is
# spelled: every receiver of .role must be bound by a loop over .refs.
from_refs = set(re.findall(r'for (\w+) in [\w.()]*\brefs\b', src))
receivers = set(re.findall(r'(\w+)\.role\b', src))
assert receivers and receivers <= from_refs, (sorted(receivers), sorted(from_refs))
assert 'Provenance(' not in src and 'provenance=' not in src
"`
`check: python -c "import ast,pathlib; t=ast.parse(pathlib.Path('src/deepreason/calculus/scope.py').read_text()); src=pathlib.Path('src/deepreason/calculus/scope.py').read_text(); assert 'provenance.trigger' in src; assert 'provenance.from_' in src; import re; assert not re.search(r'provenance\.(?!trigger|from_)', src), 'sigma may read only the two provenance fields the Problem record exposes'"`

The second check deserves its wording. Sigma DOES read `provenance.trigger` and
`provenance.from_`, and that is not a violation: those are fields of the problem
record — what the problem IS — not a record of who authored a content. The check
pins exactly those two and refuses any third, because the third would be where
provenance-as-origin gets in.

## How to change this document

1. **A rung that proves an axiom rewrites that row and adds a check that would
   fail if the axiom stopped holding.** Run the check before writing it down.
2. **A row saying NOT YET PROVED is a debt, not a placeholder.** Do not add a
   check to it that passes trivially; `docs_verify --audit` refuses checks that
   cannot fail, and a row that reports success while proving nothing is worse
   than the admitted gap.
3. **Never delete a row.** An axiom that stopped being load-bearing is rewritten
   to say when and why, per `DR-SCHEMA`.
4. **Adding an axiom is a change to the calculus, not to this document.** It
   belongs in the source documents first, and arrives here with the rung that
   answers for it.

## Traps

- **Proving an axiom on the module that implements it, rather than on the
  module that could break it.** A4 is the worked case: the standing module being
  read-only is necessary and nowhere near sufficient, because a perfectly
  read-only view still breaks A4 the moment `_adjudicate` consults it. Rung 4's
  mutation proof is the evidence — the standing module was unchanged throughout,
  and the test went RED from a three-line leak in `harness.py`.
- **A check that cannot see its own violation.** Rung 4's `standing-integrity`
  check first used the STRICT frame-assertion recogniser, which requires the
  declared interface to match the controller's compiler. An assertion violating
  A5 is therefore not recognised by it at all, and the check reported nothing on
  a root built purposely to violate A5. Recognition for CONSULT must be strict;
  recognition for INTEGRITY must not be.
`check: grep -q "def declared_frame_assertions" src/deepreason/calculus/standing.py && grep -q "_declared_frame_assertions" src/deepreason/invariants.py`
