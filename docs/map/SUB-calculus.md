<!-- DR-SUB-calculus -->
Verified-at: 03b1edf4
Verify: python -m pytest tests/test_calculus_claim_substrate.py -q
Owns: src/deepreason/calculus/claims.py, src/deepreason/calculus/compiler.py, src/deepreason/calculus/operations.py, src/deepreason/calculus/programs.py, src/deepreason/calculus/scope.py, src/deepreason/calculus/separation.py, src/deepreason/calculus/standing.py, src/deepreason/calculus/views.py
Seams: 
Seams-undocumented: calculus x ontology, calculus x problem-layer-lifecycle, calculus x evaluation, calculus x adjudication

# The typed claim substrate — closed bodies, one compiler

## What it owns

A claim is a versioned body from a CLOSED set, compiled to an `Interface` by
ONE controller-owned function. Two guarantees that only work together: nothing
outside the set can become quasi-ontology, and no model ever chooses whether an
endpoint is a `mention`, a `dependence`, or `evidence`.

`check: python -c "from deepreason.calculus import CLAIM_SCHEMAS; assert len(CLAIM_SCHEMAS) == 9 and all(s.startswith('poietic.') for s in CLAIM_SCHEMAS)"`

## Why closed, and why an open predicate is refused

An open `RelationClaim(predicate: str)` would let arbitrary prose predicates
become ontology, and each one would need its interaction with `att`, `dep`,
replay and status re-proven. `decode` refuses an unknown schema name with
`claim-schema-unknown`.

Five of the nine names are DECLARED AND UNBUILT, refused with
`claim-schema-not-implemented`. That split is deliberate: shipping body models
with no producers is `docs/ERRATA.md` E28's pattern — a mechanism nobody
triggers — while closing the NAME set is what actually stops the drift.

`check: python -m pytest tests/test_calculus_claim_substrate.py::test_an_open_predicate_cannot_enter tests/test_calculus_claim_substrate.py::test_a_declared_but_unbuilt_schema_is_refused_with_its_reason -q`

Rung 4 supplied the producer for `poietic.frame-assertion.v1` — a name the
closed set ALREADY declared. The set did not grow, and that is the property
worth checking: an ontology addition riding in on a rung meant only to build
one is exactly what the closure exists to stop.

`check: python -c "from deepreason.calculus import CLAIM_SCHEMAS; from deepreason.calculus.claims import _IMPLEMENTED; assert len(CLAIM_SCHEMAS) == 9 and len(_IMPLEMENTED) == 4 and {'poietic.frame-assertion.v1', 'poietic.derivation-manifest.v1'} <= set(_IMPLEMENTED)"`

Rung D repeats the pattern for `poietic.derivation-manifest.v1` (`DR-CON-proof-debt-and-localization`):
a producer for a name the set already held, so the closure is exercised twice
over and the count is still 9. `KernelCheckV1` is deliberately a `_Part` and not
a `_Body` — it carries no `schema` name and `decode` cannot reach it, so a
body's internal parts can never widen the closed set by the back door.

`check: python -c "from deepreason.calculus.claims import KernelCheckV1, _MODELS, CLAIM_SCHEMAS; assert KernelCheckV1 not in _MODELS.values() and len(CLAIM_SCHEMAS) == 9"`

## The compiler is the only authority on ref roles

Ref roles are SEMANTICS: they decide whether an attack propagates, whether pass
two suspends the claim, and whether an attacker of the evidence is lifted onto
a validity node. A body says WHAT it relates; the controller says HOW. Checked
structurally — every `RefRole` decision in the package lives in `compiler.py`,
and nothing here imports the synthesizer, which compiles every connected
endpoint as `DEPENDENCE` and would be exactly wrong for an attribution.

`check: python -m pytest tests/test_calculus_claim_substrate.py::test_the_compiler_is_the_only_authority_on_ref_roles tests/test_calculus_claim_substrate.py::test_no_body_field_names_a_ref_role tests/test_calculus_claim_substrate.py::test_an_attribution_mentions_its_premise_and_never_depends_on_it -q`

## Frame assertions, and the standing view they derive (Rung 4)

A frame assertion is an ORDINARY artifact whose CONTENT is Def 9.2's frame
claim `<subject b, scope sigma, validity v, departure protocol>`. No `kind`
field, no event rule of its own: the two axes — truth-standing (`status`) and
frame-standing (`standing`) — are separated by EDGE ROLE, not by a node type.
The compiler makes the subject a MENTION (Law 9.4) and each cited reach record
a DEPENDENCE, and that one assignment is the whole separation: a wound to the
subject cannot drag the frame down, and refuting the case cuts the frame's
support.

`standing(b)` (Def 9.3) is DERIVED — recomputed from replayed state on every
call, never stored — and is consumed by render and schedule alone. `scope.py`
holds sigma in `declarative-scope.v1`, a fixed finite DSL (D-5 answered A)
whose leaves reach the `Problem` record and nothing else, which is what makes
C1 determinism structural rather than promised.

`check: python -m pytest tests/test_calculus_frame_assertions.py tests/test_calculus_standing.py tests/test_calculus_scope_predicate.py -q`
`check: python -c "import ast,pathlib; t=ast.parse(pathlib.Path('src/deepreason/calculus/standing.py').read_text()); assert not any(isinstance(n,ast.Call) and 'create_artifact' in ast.unparse(n.func) for n in ast.walk(t)); mods=[(n.module or '') for n in ast.walk(t) if isinstance(n,ast.ImportFrom)]; assert not any('adjudication' in m for m in mods), mods"`

**Revocation has NO rule of its own** (S-10), and no function implements one:
attacking a reach record cuts support, pass two makes the assertion
`suspended_unsupported`, and it simply stops being consulted. Orphaned != false
does the work — revocation says unearned, not wrong.

`check: python -m pytest tests/test_calculus_frame_assertions.py::test_revocation_has_no_rule_of_its_own tests/test_calculus_standing.py::test_standing_changes_without_status_changing -q`

## Companion problem subjects

A problem is criticisable through a deterministic COMPANION artifact, not
through a status of its own. `Problem` stays the immutable scheduling and
provenance record; `problem_status` reads the companion's ordinary artifact
status; critics attack the companion exactly as they attack anything else.

Recognition requires all six conditions — body parses, `problem_id` resolves,
the copies MATCH the record, the structural commitment is present, the artifact
ADDRESSES the problem, and the interface carries only the permitted refs.
Condition three carries the weight: without it a companion drifts from its
problem and criticism lands on a stale statement of the question.

`check: python -m pytest tests/test_calculus_claim_substrate.py::test_each_recognition_condition_is_required tests/test_calculus_claim_substrate.py::test_criticising_the_companion_moves_the_problems_standing -q`

## Frame-separation, and what a violation may do

Definition 7.2 (`docs/POIETIC_CALCULUS_FORMALIZED.md` §7): an assertion `f` with
subject `b` is SEPARATED when `Comp(f) ∩ Comp(b) = ∅` in the undirected graph
obtained from `att ∪ dep`. Mention edges need no filtering out of that graph —
`build_dep` emits `dep` from `RefRole.DEPENDENCE` and from nothing else — and
that exclusion is what makes the invariant satisfiable at all. Components are
recomputed from replayed state on every call; nothing is stored.

`check: python -m pytest tests/test_calculus_frame_separation.py::test_a_mention_leaves_the_assertion_and_its_subject_separated tests/test_calculus_frame_separation.py::test_wound_persistence_holds_when_the_separation_does -q`

A violation makes the assertion UNCONSULTABLE with a typed code and does nothing
else — no attack edge, no warrant, no label change (R64). Enforced structurally
rather than by review, so an edit that reaches for the write path fails here: the
module holds no call that could write, and imports nothing from `adjudication` —
it consumes that package's OUTPUT through replayed state, never its logic.

`check: ! grep -qE "create_artifact|register_|record_|blobs\.put|Warrant" src/deepreason/calculus/separation.py && grep -q "def consultability" src/deepreason/calculus/separation.py && python -c "import ast,pathlib; t=ast.parse(pathlib.Path('src/deepreason/calculus/separation.py').read_text()); mods=[(n.module or '') for n in ast.walk(t) if isinstance(n,ast.ImportFrom)]+[a.name for n in ast.walk(t) if isinstance(n,ast.Import) for a in n.names]; assert not any('adjudication' in m for m in mods), mods"`

## State it owns

**None that persists, and none added anywhere else.** No field was added to
`Problem`, `EpistemicState` or `Event`, and no relation table was introduced —
a second graph would need its interactions with `att`, `dep`, replay and status
re-proven. The companion is computed from the record that already exists and
found through `addr`.

`check: python -m pytest tests/test_calculus_claim_substrate.py::test_no_field_was_added_to_problem_state_or_event -q`

## Entry points

`decode`, `encode`, `compile_interface`, `ensure_problem_subject`,
`problem_subject_of`, `problem_status`, `problem_subject_missing`,
`adjudication_component`, `frame_separated`, `consultability`,
`ensure_promotion_problem`, `file_frame_assertion`, `compile_scope`,
`scope_admits`, `consultability_of`, `consulted`, `standing_of`, `frames`,
`standing_view`.

## Traps

- **The mention law is necessary and NOT sufficient, and a green mention test
  hides that.** `docs/COMPUTABLE_CALCULUS.md` derived wound persistence from the
  frame assertion merely MENTIONING its subject; `docs/POIETIC_CALCULUS_FORMALIZED.md`
  §7 corrects it — in a connected graph a new attack on the subject moves the
  assertion's label through pre-existing paths. An assertion can mention its
  subject and still share a component with it, whenever a record it DEPENDS on
  depends on that subject. So the gate asserts DISJOINT COMPONENTS, never the
  presence of a mention ref. Shipped 2026-08-21 (Rung 3b); the error corrected is
  in the source documents, not in a run.
`check: python -m pytest tests/test_calculus_frame_separation.py::test_a_reach_case_that_depends_on_the_subject_is_unconsultable -q`
- **`consultability` had NO caller in `src/` until Rung 4 — WIRED 2026-08-22,
  and only for frame assertions.** Rung 3b shipped the predicate and said Rung 4
  owned the consultation site; `standing.py::consultability_of` is that site. It
  CALLS `separation.consultability` and returns its `Consultability` value with
  `FRAME_NOT_SEPARATED` unchanged rather than re-deriving the graph condition —
  two definitions of one invariant would leave no way to tell which the record
  meant. The other half of the old row still stands: do NOT "finish the job" by
  gating `premises.py::standing_attributions`. That is a separate open question
  with its own measurement obligation
  (`experiments/2026-08-21-change-rung3b-frame-separation/PARKED.md` P1, carried
  forward as `experiments/2026-08-22-change-rung4-frame-assertions/PARKED.md`
  P2), and `premises.py` is untouched.
`check: python -c "import pathlib; hits=[str(p) for p in sorted(pathlib.Path('src/deepreason').rglob('*.py')) if 'consultability' in p.read_text() and not str(p).startswith('src/deepreason/calculus/')]; assert hits == [], hits" && grep -q "def consultability_of" src/deepreason/calculus/standing.py && grep -q "consultability(harness, assertion_id, body.subject_ref)" src/deepreason/calculus/standing.py && ! grep -q "deepreason.calculus" src/deepreason/premises.py && grep -q "def standing_attributions" src/deepreason/premises.py`
- **Two-step registration leaves a gap, and the gap is the right trade.**
  `register_problem` then `ensure_problem_subject` can be interrupted between
  the writes. The result is a typed `problem_subject_missing` diagnostic and an
  idempotent repair on resume — preferable to changing event atomicity to close
  a very small recoverable window. The operation is idempotent because the body
  is a pure function of the `Problem` record, so its content address is too.
`check: python -m pytest tests/test_calculus_claim_substrate.py::test_ensure_problem_subject_is_idempotent tests/test_calculus_claim_substrate.py::test_the_missing_companion_diagnostic_names_the_gap_and_clears -q`
- **NO SCHEDULER INTEGRATION, deliberately.** Nothing selects on
  `problem_status` yet. When it does, it must schedule accepted unresolved
  subjects and must NOT silently drop refuted or orphaned problems from
  history.
`check: ! grep -rq "deepreason.calculus" src/deepreason/scheduler/`
- **All three programs are STRUCTURAL.** Passing says the body is well formed and
  controller-compiled, never that its claim holds — so they are in
  `measures/reach.py::_STRUCTURAL_PROGRAMS`, ground no reach, and confer no
  prose immunity.
`check: python -c "from deepreason.measures.reach import _STRUCTURAL_PROGRAMS as S; assert {'problem_subject_wf','premise_attribution_wf','frame_assertion_wf'} <= S"`
- **The premise channel is NOT yet on this substrate.** `premises.py` still
  registers its own attribution shape and works exactly as delivered at Rung 2.
  The union carries a `poietic.premise-attribution.v1` body that compiles to the
  same interface, and moving the channel onto it is a later step with its own
  regression obligations. Reading the two as one is the misreading to avoid.
  The two shapes are kept in step BY HAND, and P4 is the worked example: the
  citation dependence R62 requires landed in both, as `citation_ref` on the
  body and as the `citation_ref` keyword on `file_premise`. A change that lands
  in one and not the other is the drift this row exists to catch.
`check: ! grep -q "deepreason.calculus" src/deepreason/premises.py && python -c "
from deepreason.calculus.claims import PremiseAttributionV1 as A
from deepreason.calculus.compiler import compile_interface
import inspect
from deepreason.premises import file_premise
assert 'citation_ref' in A.model_fields, sorted(A.model_fields)
assert 'citation_ref' in inspect.signature(file_premise).parameters
i = compile_interface(A(problem_subject_ref='s', premise_ref='x', citation_ref='c'))
roles = {r.target: r.role.value for r in i.refs}
assert roles == {'s': 'mention', 'x': 'mention', 'c': 'dependence'}, roles
"`
