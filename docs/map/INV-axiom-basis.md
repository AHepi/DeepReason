<!-- DR-INV-axiom-basis -->
Verified-at: 748c9ab61
Verify: python -m pytest tests/test_calculus_standing.py tests/test_calculus_frame_assertions.py tests/test_proof_debt.py tests/test_calculus_nomination.py tests/test_promotion_solo.py -q
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
| **A8** | reach can spawn promotion problems but cannot directly alter labels | **Rung 5** | Rung 8 |
| **A9** | render, measures, diagnostics and knowledge views act only through attention | **Rung 6** (render) — **LANDED 2026-08-24**; **Rung 8** (diagnostics) — **LANDED 2026-08-25**, Theorem 14.1 exhibited and mutation-proven twice | Rungs 2, 5, **D** (a receipt is a readout and moves no label) |
| **A10** | all set ordering, numerical evaluation, sampling and serialization are canonical | already true — re-proved by every rung's replay determinism; **Rung 8** states it as an explicit POLICY (rounding rule + declared precision), not a by-product | every rung; **Rung D** logs the rent sample as a canonical artifact rather than a blob |
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

**PRESERVED at Rung 8, where it was one line from being lost.** T-7 asked for
the scope-predicate budget as a `Config` knob, and a criterion reading that knob
LIVE would let a promotion verdict move while its commitment stood still — a
verdict that is no longer a finite-budget function of its own frozen input.
The knob ships, and the bound travels inside the reach certificate
(`scope_max_depth` / `scope_max_nodes`), the same road `k_frame` already takes.
`compile_scope`'s bounds are keyword-only and default to the module constants,
so every caller that is asking "is this well-formed" rather than reaching a
verdict is unchanged.

Mutation-proven: reading the bound from a live `Config()` instead of from the
certificate turns the guard red.

`check: python -m pytest tests/test_promotion_rent.py::test_the_scope_bound_comes_from_the_certificate_not_the_config -q`
`check: python -c "import ast, inspect; from deepreason.calculus.promotion import scope_determinism; t=ast.parse(inspect.getsource(scope_determinism).lstrip()); names={n.id for n in ast.walk(t) if isinstance(n, ast.Name)} | {n.attr for n in ast.walk(t) if isinstance(n, ast.Attribute)}; assert 'scope_max_depth' in names and 'scope_max_nodes' in names and 'Config' not in names"`

## A3 — two passes, in that order

`_adjudicate` is the sole writer of `state.status` and calls the label function
exactly once: grounded attack pass (`compute_label0` over `att`), then the
acyclic support pass (`final_labels` over `dep`). One writer, one call.

`check: python -c "src=open('src/deepreason/harness.py').read(); assert src.count('self.state.status = ')==1; assert src.count('final_labels(')==1; assert 'compute_label0' in src"`

**PRESERVED at Rung 6.** The frame render adds no third pass and no second
writer: no assignment target anywhere in `calculus/render.py` is rooted at `harness`,
so it cannot write `state.status`, `state.att` or `state.dep`, and the
one-writer-one-call property above is untouched.

The check took two rewrites, both recorded because each failure was the check
being wrong rather than the code: a name-based version flagged a local variable
called `status`, and a shape-based version flagged a legitimate local dict
write. What it now asserts is the actual property — nothing assigns THROUGH the
harness — and it was proven non-vacuous by running it against the leak mutation,
where it fails naming the offending target. The three exit grades are a
pure function OF the labels the two passes already produced, never an input to
them.

`check: python -c "import ast,pathlib; t=ast.parse(pathlib.Path('src/deepreason/calculus/render.py').read_text()); root=lambda n: root(n.value) if isinstance(n,(ast.Attribute,ast.Subscript)) else getattr(n,'id',None); tgt=[x for n in ast.walk(t) if isinstance(n,ast.Assign) for x in n.targets]+[n.target for n in ast.walk(t) if isinstance(n,(ast.AugAssign,ast.AnnAssign))]; bad=[ast.dump(x) for x in tgt if root(x)=='harness']; assert not bad, bad; assert 'harness' in pathlib.Path('src/deepreason/calculus/render.py').read_text()"`

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

**PRESERVED at Rung 6, and re-proved one layer out.** Rung 4 proved that
CARRYING a frame moves no label; Rung 6 proves that RENDERING one does not
either — which is a different claim, because the render is the first thing that
reads standing and hands it to a generation seat. Two roots over one graph, one
rendering a non-empty slice and one not, produce identical labels, attack edges
and support edges over the shared artifacts, with the subject REFUTED in both
for Rung 4's own reason. Mutation-proven: leaking the slice into adjudication
(a consulted subject marked `accepted` because it frames) turns the label from
`refuted` to `accepted` and the test RED.

`check: python -m pytest tests/test_frame_render.py::test_rendering_the_frame_slice_moves_no_label tests/test_frame_render.py::test_rendering_writes_nothing_to_the_log -q`

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

## A6 and A9 at Rung 7 — what the cascade's second entry had to preserve

**A6 preserved, and the frame entry is where it could most easily have been
lost.** A fallen frame assertion marks every problem it carried — so the
question "was this assertion ever consultable?" acquired a consequence it did
not have before. The entry answers it by CALLING `separation.consultability`,
Rung 3b's own predicate, rather than re-deriving the graph condition: two
definitions of one invariant would leave no way to tell which the record meant.
An unseparated assertion therefore marks NOTHING — R64's "no attack edge, no
warrant, no label change" gains a fourth clause, "and no mark" — and is
enumerated separately instead, so the silence is visible rather than absent.

`check: python -m pytest tests/test_calculus_axioms_rung7.py -k a6 -q`

**A9 preserved across three new readouts** — the batch offers, the succession
pack and the trial record. The first two write nothing at all. The third DOES
write, deliberately: a diagnostic nobody can attack is a diagnostic nobody can
correct, so the trial record is an ordinary registered artifact plus a measure.
What makes that still A9 is what it is NOT: no status, no edge, no warrant. The
check pins the split by function name, so a second writer in that module fails
here rather than being found later.

`check: python -m pytest tests/test_calculus_axioms_rung7.py -k a9 -q`

**A7 is why "carrying" is COMPUTED.** The cascade needs the set of problems a
fallen frame carried, and A7's mechanism is that there is no mechanism —
nothing stores which assertions a problem was posed under. So the set is σ
evaluated on each immutable `Problem` record, which is exactly what `frames`
has meant since Rung 4. A second meaning would give the cascade a different set
from the renderer's, and the pack and the mark would then disagree about the
same fall.

`check: python -m pytest tests/test_calculus_cascade_frame_entry.py::test_a_fallen_frame_does_not_orphan_its_own_promotion_problem -q`

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

**PROVED at Rung 5.** Both halves now have checks, and the spawn half is the one
Rung 4 had to leave open: `calculus/nomination.py::nominate` is the only
producer of a `SpawnTrigger.PROMOTION` problem outside a test, and it reads
`state.reach` to decide whether to spawn one.

The axiom's force is in the second clause — CANNOT DIRECTLY ALTER LABELS — and
it is asserted structurally AND behaviourally, because either alone is
satisfiable by the wrong thing. Structurally, the measure imports no
adjudication, warrant, LLM or trial path and assigns into no label map;
behaviourally, a firing nomination leaves every pre-existing entry of
`state.status`, `state.hv` and `state.reach` byte-identical. The one addition
a firing nomination makes to `state.status` is the reach certificate's own
registration, which is what every unattacked artifact gets and is not a
judgment moving.

`check: python -c "
import ast, pathlib
t = ast.parse(pathlib.Path('src/deepreason/calculus/nomination.py').read_text())
mods = [(n.module or '') for n in ast.walk(t) if isinstance(n, ast.ImportFrom)]
assert not any(k in m for m in mods for k in ('adjudication', 'warrants', 'llm', 'trial')), mods
W = [ast.unparse(g) for n in ast.walk(t) if isinstance(n, ast.Assign) for g in n.targets if any(k in ast.unparse(g) for k in ('state.status', 'state.hv', 'state.reach'))]
assert not W, W
"`
`check: python -m pytest tests/test_calculus_nomination.py::test_nomination_changes_no_label_and_no_measure -q`

The SPAWN half, on the tree and on real live data. The second check is the
negative control and is the more informative of the two: the committed
attempt-4 root recorded a genuine reach event, and nomination still declines it
because that event spans ONE problem lineage.

`check: python -c "
import inspect
from deepreason.calculus.nomination import nominate
from deepreason.ontology import SpawnTrigger
assert 'ensure_promotion_problem(' in inspect.getsource(nominate)
assert SpawnTrigger.PROMOTION.value == 'promotion'
"`
`check: python -m pytest tests/test_promotion_nomination_live.py::test_nomination_does_not_fire_on_the_committed_live_root -q`

Rung 4's half is retained and WIDENED. Reach measures ground no reach from
structural programs, so a well-formed frame assertion cannot buy its own
promotion case — and neither can a well-formed reach certificate or a passing
promotion criterion. That widening closes the loop from the other side: a
criterion counted SUBSTANTIVE would ground reach, and reach is what nominates,
so the promotion machinery would manufacture the signal that produced it.

`check: python -c "from deepreason.measures.reach import _STRUCTURAL_PROGRAMS as S; assert {'frame_assertion_wf','problem_subject_wf','premise_attribution_wf'} <= S; assert {'reach_certificate_wf','promotion_subject_demarcation','promotion_reach_integrity','promotion_scope_determinism','promotion_compatibility','promotion_accounts_for'} <= S"`

**Trap for Rung 8.** The nomination CONSTANTS are Rung 8's to tune, and tuning
`K_FRAME` cannot be allowed to become a way of altering labels indirectly. The
guard is the same one that holds today: the measure writes a problem and its
paperwork, and nothing else, whatever the threshold says.

## A4, preserved at Rung 5 — no promotion module can reach a label or a seat

A4's own section is above; this is Rung 5's preservation entry, kept beside A8
because the two are broken by the same edit. Neither `nomination.py` nor
`promotion.py` imports an LLM, adapter, seat, provider, qualification, judge,
trial or ensemble path, so the promotion road cannot acquire a seat dependency
by a later edit without this check going red. That is also frozen surface 5 held
at ZERO: the v2 program adds no new LLM role, so no qualification subject digest
moves and no home owes a ~14-minute battery rerun.

`check: python -c "
import ast, pathlib
for name in ('nomination.py', 'promotion.py'):
    t = ast.parse(pathlib.Path('src/deepreason/calculus/' + name).read_text())
    mods = [(n.module or '') for n in ast.walk(t) if isinstance(n, ast.ImportFrom)] + [a.name for n in ast.walk(t) if isinstance(n, ast.Import) for a in n.names]
    assert not any(p in m for m in mods for p in ('llm', 'adapter', 'seat', 'provider', 'qualification', 'judge', 'trial', 'ensemble')), (name, mods)
"`
`check: python -m pytest tests/test_promotion_solo.py -q`

## A9 — render, measures and diagnostics act only through attention

**RENDER HALF PROVED — Rung 6.** Diagnostics remain Rung 8's. Rung 4's
contribution was negative and still holds: the standing view is consumed by
render and schedule ALONE, it is read-only, and it reaches no LLM seat.

`check: python -c "import ast,pathlib; t=ast.parse(pathlib.Path('src/deepreason/calculus/standing.py').read_text()); mods=[(n.module or '') for n in ast.walk(t) if isinstance(n,ast.ImportFrom)]+[a.name for n in ast.walk(t) if isinstance(n,ast.Import) for a in n.names]; assert not any(p in m for m in mods for p in ('llm','adapter','seat','provider','qualification','adjudication')), mods"`

Rung 6 adds the render side, and it takes three checks rather than one because
"acts only through attention" has three distinct failure modes and an import
check catches only the first.

**It reaches no seat.** `calculus/render.py` imports nothing from `llm`,
`adapter`, `seat`, `provider`, `qualification` or `adjudication`. The
articulation digest is a deterministic head plus the subject's declared
commitment ids — NOT a summarizer call, which is also why frozen surface 5
stays at zero across this rung.

`check: python -c "import ast,pathlib; t=ast.parse(pathlib.Path('src/deepreason/calculus/render.py').read_text()); mods=[(n.module or '') for n in ast.walk(t) if isinstance(n,ast.ImportFrom)]+[a.name for n in ast.walk(t) if isinstance(n,ast.Import) for a in n.names]; assert not any(p in m for m in mods for p in ('llm','adapter','seat','provider','qualification','adjudication')), mods"`

**It writes nothing.** No `create_*`, `register_*`, `commit_*` or `append_*`
call anywhere in the module, and a root's `log.jsonl` is byte-identical across
repeated renders.

`check: python -c "import ast,pathlib; t=ast.parse(pathlib.Path('src/deepreason/calculus/render.py').read_text()); bad=[n.func.attr for n in ast.walk(t) if isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute) and n.func.attr.startswith(('create_','register_','commit_','append_'))]; assert not bad, bad"`
`check: python -m pytest tests/test_frame_render.py::test_rendering_writes_nothing_to_the_log -q`

**It moves no label**, which is the failure an import check cannot see: a
render could compute a label leak without importing anything new. Two roots
over one graph, one rendering the slice and one not, produce identical labels,
attack edges and support edges over the shared artifacts — and the claim was
MUTATION-PROVEN, not asserted (the tranche's VALIDATION.md pastes the RED).

`check: python -m pytest tests/test_frame_render.py::test_rendering_the_frame_slice_moves_no_label -q`

**PROVED at Rung 8, for the diagnostics half.** Theorem 14.1: two states with
identical artifacts, attacks and dependencies but different diagnostic values or
attention modes have identical labels. Exhibited by a DIFFERENTIAL over one
scripted record — the same record run with the §14.7 controller in `normal` and
in `diversify`, comparing every label, every `att` edge, every `dep` edge and
every warrant, with the controller's own policy artifact excluded because a
policy having a status is the design (P6), not a leak.

Mutation-proven twice in a scratch copy: teaching `_adjudicate` to read the
recorded mode turns the differential red, and minting a warrant when the mode is
entered — the forbidden move dressed as "so the diversification has teeth" —
turns both the differential and the structural check red.

`check: python -m pytest tests/test_capture14_hysteresis.py -q -k "theorem_14_1 or constructs_no_edge"`


## A10 — canonical ordering, evaluation, sampling, serialization

Re-proved by every rung's replay determinism. Rung 4's own contribution: the
standing view sorts its grants by assertion id, so two renders of one root agree
byte for byte, and the scope document is stored as authored bytes rather than as
a compiled object, so its content address does not move when the compiler does.

`check: python -c "import inspect; from deepreason.calculus.standing import standing_view; assert 'sorted(' in inspect.getsource(standing_view)"`

**PRESERVED at Rung 6.** Every ordering the frame slice introduces is canonical:
slices sort by assertion id, attackers by attacker id, declared departures by
departing-artifact id, and exits by assertion id. So one problem over one state
renders byte-identical packs, and two independently replayed harnesses over one
root agree. The attacker sort is kept even though `Harness._adjudicate` already
sorts `state.att`, because under the render's cap the order decides WHICH
attackers a pack shows — a property this module must own rather than borrow from
a frozen surface.

`check: python -m pytest tests/test_frame_render.py::test_the_slice_is_byte_identical_across_renders tests/test_frame_render.py::test_attackers_render_in_id_order_whatever_order_the_state_holds -q`

**PROVED at Rung 8, for the first time as an explicit POLICY rather than as a
by-product.** §14's diagnostics carry a rounding rule and a fixed precision that
are part of the policy (R48/A10), not of the implementation: `canonical` is
`ROUND_HALF_EVEN` — never HALF_UP, which drifts a series upward on ties — at a
precision the emitted payload STATES, so a reader re-derives every number from
the record without knowing any default. The six are emitted as fixed-precision
decimal STRINGS rather than floats, because a float's repr is the machine's and
a decimal string is the policy's; and absence renders `none` rather than
`0.000000`, so "no data" and "measured zero" stay distinguishable.

`check: python -m pytest tests/test_capture14_diagnostics.py::test_canonical_rounding_is_half_even_at_the_declared_precision tests/test_capture14_diagnostics.py::test_absence_renders_as_none_and_never_as_zero tests/test_capture14_diagnostics.py::test_two_computations_over_one_record_are_byte_identical -q`
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

**Rung 5's own near-miss shape, recorded like Rung 4's.** It would have been
natural to let nomination rank candidate subjects by the provenance role that
authored them, or to let `accounts-for` prefer a rival a conjecturer wrote over
one that was imported. Neither happens: nomination reads reach, addressing and
lineage, and the succession relation reads accounted sets, HV readings,
declared commitments and registered criticism. Nothing reads who wrote what.
The one `provenance` field either module names is `trigger`, which is what a
PROBLEM IS rather than where it came from.

`check: python -c "
import pathlib, re
for name in ('nomination.py', 'promotion.py'):
    src = pathlib.Path('src/deepreason/calculus/' + name).read_text()
    assert not re.search(r'provenance\.(?!trigger|from_)', src), name
"`

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
