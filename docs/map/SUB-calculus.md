<!-- DR-SUB-calculus -->
Verified-at: e901bb05
Verify: python -m pytest tests/test_calculus_claim_substrate.py -q
Owns: src/deepreason/calculus/claims.py, src/deepreason/calculus/compiler.py, src/deepreason/calculus/operations.py, src/deepreason/calculus/programs.py, src/deepreason/calculus/views.py
Seams: 
Seams-undocumented: calculus x ontology, calculus x problem-layer-lifecycle, calculus x evaluation

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

Seven of the nine names are DECLARED AND UNBUILT, refused with
`claim-schema-not-implemented`. That split is deliberate: shipping body models
with no producers is `docs/ERRATA.md` E28's pattern — a mechanism nobody
triggers — while closing the NAME set is what actually stops the drift.

`check: python -m pytest tests/test_calculus_claim_substrate.py::test_an_open_predicate_cannot_enter tests/test_calculus_claim_substrate.py::test_a_declared_but_unbuilt_schema_is_refused_with_its_reason -q`

## The compiler is the only authority on ref roles

Ref roles are SEMANTICS: they decide whether an attack propagates, whether pass
two suspends the claim, and whether an attacker of the evidence is lifted onto
a validity node. A body says WHAT it relates; the controller says HOW. Checked
structurally — every `RefRole` decision in the package lives in `compiler.py`,
and nothing here imports the synthesizer, which compiles every connected
endpoint as `DEPENDENCE` and would be exactly wrong for an attribution.

`check: python -m pytest tests/test_calculus_claim_substrate.py::test_the_compiler_is_the_only_authority_on_ref_roles tests/test_calculus_claim_substrate.py::test_no_body_field_names_a_ref_role tests/test_calculus_claim_substrate.py::test_an_attribution_mentions_its_premise_and_never_depends_on_it -q`

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

## State it owns

**None that persists, and none added anywhere else.** No field was added to
`Problem`, `EpistemicState` or `Event`, and no relation table was introduced —
a second graph would need its interactions with `att`, `dep`, replay and status
re-proven. The companion is computed from the record that already exists and
found through `addr`.

`check: python -m pytest tests/test_calculus_claim_substrate.py::test_no_field_was_added_to_problem_state_or_event -q`

## Entry points

`decode`, `encode`, `compile_interface`, `ensure_problem_subject`,
`problem_subject_of`, `problem_status`, `problem_subject_missing`.

## Traps

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
- **Both programs are STRUCTURAL.** Passing says the body is well formed and
  controller-compiled, never that its claim holds — so they are in
  `measures/reach.py::_STRUCTURAL_PROGRAMS`, ground no reach, and confer no
  prose immunity.
`check: python -c "from deepreason.measures.reach import _STRUCTURAL_PROGRAMS as S; assert {'problem_subject_wf','premise_attribution_wf'} <= S"`
- **The premise channel is NOT yet on this substrate.** `premises.py` still
  registers its own attribution shape and works exactly as delivered at Rung 2.
  The union carries a `poietic.premise-attribution.v1` body that compiles to the
  same interface, and moving the channel onto it is a later step with its own
  regression obligations. Reading the two as one is the misreading to avoid.
`check: ! grep -q "deepreason.calculus" src/deepreason/premises.py`
