<!-- DR-SUB-calculus -->
Verified-at: b41c5cf10
Verify: python -m pytest tests/test_calculus_claim_substrate.py tests/test_calculus_nomination.py tests/test_promotion_criteria.py tests/test_promotion_succession.py tests/test_calculus_succession.py -q
Owns: src/deepreason/calculus/render.py, src/deepreason/calculus/succession.py, src/deepreason/calculus/claims.py, src/deepreason/calculus/compiler.py, src/deepreason/calculus/nomination.py, src/deepreason/calculus/operations.py, src/deepreason/calculus/programs.py, src/deepreason/calculus/promotion.py, src/deepreason/calculus/scope.py, src/deepreason/calculus/separation.py, src/deepreason/calculus/standing.py, src/deepreason/calculus/views.py
Seams: DR-SEAM-calculus-x-rules
Seams-undocumented: calculus x ontology, calculus x problem-layer-lifecycle, calculus x evaluation, calculus x adjudication

# The typed claim substrate — closed bodies, one compiler

## What it owns

A claim is a versioned body from a CLOSED set, compiled to an `Interface` by
ONE controller-owned function. Two guarantees that only work together: nothing
outside the set can become quasi-ontology, and no model ever chooses whether an
endpoint is a `mention`, a `dependence`, or `evidence`.

`check: python -c "from deepreason.calculus import CLAIM_SCHEMAS; assert len(CLAIM_SCHEMAS) == 10 and all(s.startswith('poietic.') for s in CLAIM_SCHEMAS)"`

Six of the ten names have a producer. The other four are declared and REFUSED
by `decode` with `claim-schema-not-implemented`, which is the deliberate shape:
shipping a body model nobody can create is `docs/ERRATA.md` E28's pattern, so a
name joins the implemented set only in the rung that supplies its producer.
Rung 5 supplied `poietic.reach-certificate.v1`'s; Rung 6 supplied
`poietic.departure-declaration.v1`'s.

`check: python -c "from deepreason.calculus.claims import _IMPLEMENTED, CLAIM_SCHEMAS, decode, ClaimDecodeError; assert len(_IMPLEMENTED) == 6 and 'poietic.reach-certificate.v1' in _IMPLEMENTED; import json; missing = [s for s in CLAIM_SCHEMAS if s not in _IMPLEMENTED]; assert len(missing) == 4;
for name in missing:
    try:
        decode(json.dumps({'schema': name}))
    except ClaimDecodeError as e:
        assert e.code == 'claim-schema-not-implemented', (name, e.code)
    else:
        raise AssertionError(name)"`

## Why closed, and why an open predicate is refused

An open `RelationClaim(predicate: str)` would let arbitrary prose predicates
become ontology, and each one would need its interaction with `att`, `dep`,
replay and status re-proven. `decode` refuses an unknown schema name with
`claim-schema-unknown`.

Four of the ten names are DECLARED AND UNBUILT, refused with
`claim-schema-not-implemented`. That split is deliberate: shipping body models
with no producers is `docs/ERRATA.md` E28's pattern — a mechanism nobody
triggers — while closing the NAME set is what actually stops the drift. (This
paragraph read "five of the nine" until 2026-08-24 and contradicted the
`len(missing) == 4` check three paragraphs above it — `docs/ERRATA.md` E50.)

`check: python -m pytest tests/test_calculus_claim_substrate.py::test_an_open_predicate_cannot_enter tests/test_calculus_claim_substrate.py::test_a_declared_but_unbuilt_schema_is_refused_with_its_reason -q`

Rung 4 supplied the producer for `poietic.frame-assertion.v1` — a name the
closed set ALREADY declared. Rung D repeated the pattern for
`poietic.derivation-manifest.v1` (`DR-CON-proof-debt-and-localization`), and
Rung 5 for `poietic.reach-certificate.v1`. Through all three the set did not
grow.

**Rung 6 is the first rung that GREW it**, to 10, and the difference is worth
stating exactly because the earlier phrasing here ("the set did not grow") was
easy to read as the invariant. It is not. `claims.py`'s own docstring states
the rule: "Adding a name here is an ontology change and belongs in the rung
that supplies its producer, never in a convenience commit." What the closure
forbids is a NAME WITHOUT A PRODUCER, not a name. Rung 6 added
`poietic.departure-declaration.v1` and shipped
`operations.file_departure_declaration` in the same tranche, so the rule held
while the count moved. A name added with no producer still fails the refusal
check above.

`check: python -c "from deepreason.calculus import CLAIM_SCHEMAS; from deepreason.calculus.claims import _IMPLEMENTED; assert len(CLAIM_SCHEMAS) == 10 and len(_IMPLEMENTED) == 6 and {'poietic.frame-assertion.v1', 'poietic.derivation-manifest.v1', 'poietic.reach-certificate.v1', 'poietic.departure-declaration.v1'} <= set(_IMPLEMENTED)"`
`check: python -c "from deepreason.calculus import file_departure_declaration; from deepreason.calculus.claims import DEPARTURE_DECLARATION_V1, _IMPLEMENTED; assert DEPARTURE_DECLARATION_V1 in _IMPLEMENTED and callable(file_departure_declaration)"`

`KernelCheckV1` is deliberately a `_Part` and not a `_Body` — it carries no
`schema` name and `decode` cannot reach it, so a body's internal parts can
never widen the closed set by the back door.

`check: python -c "from deepreason.calculus.claims import KernelCheckV1, _MODELS, CLAIM_SCHEMAS; assert KernelCheckV1 not in _MODELS.values() and len(CLAIM_SCHEMAS) == 10"`

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

## Nomination and promotion criteria (Rung 5)

Rung 4 said what a promotion problem IS. Rung 5 says WHEN one exists, and what
a candidate must survive to be promoted through it.

**Nomination is a MEASURE-RULE over the log** (`nomination.py`), never a
decision: reach events for one subject spanning at least `Config.K_FRAME`
distinct problem LINEAGES, over a coherent candidate scope, spawn a promotion
problem. What follows is an ordinary Conj→Crit→Adj pass — there is no promotion
phase in the scheduler, only a step that nominates and one that fires criteria.

LINEAGE is the load-bearing definition and the whole threshold turns on it. A
problem's parents are the problems it descends from, reached through
`provenance.from_` entries that are problems AND through the ORIGIN problem —
the FIRST `state.addr` entry — of entries that are artifacts. Connection and
integration problems are spawned from ARTIFACTS, so a walk that stopped there
would make each its own lineage and a single-question run would look like
dozens. Measured on the committed attempt-4 root: all 210 problems share one
root under this definition, and two under the truncated one.

`check: python -m pytest tests/test_promotion_nomination_live.py -q`

**The five criteria are PROGRAMS over a frozen input** (`promotion.py`). Each is
a pure function of the candidate's bytes and interface plus ONE fence-stamped
reach certificate fetched from the blob store by digest and re-digested on
arrival. None reads live graph state, which is what makes a promotion verdict
reproducible: a candidate evaluated twice on one record gets one answer,
whatever the run did in between.

`accounts-for` is the STRONG succession relation and the weak form was never
built: recovery, rigidity, non-immunization AND a strictness witness, all four
required. A rival that recovers the incumbent's explicanda and nothing more is
REFUSED — that is the case the weak reading admits, and it is what the mutation
proof pins.

`check: python -m pytest tests/test_promotion_succession.py::test_a_rival_that_only_recovers_is_not_a_successor -q`
`check: python -c "import inspect; from deepreason.calculus.promotion import _succeeds_one; src = inspect.getsource(_succeeds_one); assert all(r in src for r in ('recovery-fails', 'rival-is-easier-to-vary', 'excisable-idle-component', 'no-strictness-witness'))"`

**Remark 9.5's closure is an ORDER, not a rule.** A frame assertion nobody
attacked is ACCEPTED, and an accepted assertion addressed to a promotion problem
is CONSULTED — so an unexamined claim would frame its whole scope simply by
having been registered. `promotion_criteria_sweep` runs immediately after the
reach sweep and before anything consumes standing: criteria fire, a `fail` mints
a demonstrative warrant through `rules/warrants.register_fail_warrant`, and
`consultability_of` declines the assertion. An `overrun` mints NOTHING — "we
could not check" must never become the strongest criticism in the calculus.

`check: python -m pytest tests/test_promotion_closure.py -q`
`check: python -c "import inspect; from deepreason.scheduler.scheduler import Scheduler; src = inspect.getsource(Scheduler._promotion_step); assert 'nominate(' in src and 'promotion_criteria_sweep(' in src"`

## Succession, and the one render exception (Rung 7)

Rung 5 gave the RELATION (`accounts-for`, the strong form). Rung 7 gives the
TRIAL — and it is not a new instrument, which is the design. §9.7's own words:
"succession is discrimination." The rivalry reaches the frontier through
`rules/spawn.py`'s existing ≥2-survivors branch, which knows nothing about
frames; `calculus/succession.py` decides only what the PACK shows once that
problem is selected and what the TRIAL RECORDS about how it judged.

**The one proper render exception, and it is ONE SITE.** `render.frame_slices`
returns `()` for a succession trial, so both renderers fall to their existing
`None` path and `render_frame_slice_context` returns the succession context
instead. Suppressing in `frame_slices` rather than in each renderer is what
keeps it one exception: two suppressions could drift, and a pack that
suppressed the digest while keeping the crisis would still be posed in the
incumbent's vocabulary. What the pack shows is both articulation digests, both
candidates' wounds under the same cap, and the criteria in a fixed order —
ordered by SUBJECT ID, never by incumbency, because ordering by who arrived
first is provenance entering appraisal (Ax 4.1). The failure being mitigated
has a name — INCUMBENT-JUDGE BIAS — and the mitigation is symmetric exposure;
"a view from nowhere is not on offer."

`check: python -m pytest tests/test_calculus_succession.py -q`
`check: python -c "
import ast, pathlib
src = pathlib.Path('src/deepreason/calculus/render.py').read_text()
calling = [n.name for n in ast.walk(ast.parse(src)) if isinstance(n, ast.FunctionDef) and 'is_succession_trial(' in ast.unparse(n)]
assert calling == ['frame_slices'], calling
"`

**The trial records four things Q2 requires**
(`docs/RESEARCH_FINDINGS_Q1Q10_2026-08-22.md`), and the number that governs
them is that ordering alone flips the top-1 candidate on 16–39% of prompts:

| | requirement | where |
|---|---|---|
| Q2a | both orders of the two ARTICULATION DIGESTS | `program_road`, `rubric_presentation` |
| Q2b | order-disagreement is a typed NO-VERDICT, never a tiebreak | `NO_VERDICT` / `ORDER_DISAGREEMENT`, reusing the guard's own `blocked:order-swap` |
| Q2c | criterion order fixed or randomized, and WHICH recorded | `SUCCESSION_CRITERION_ORDER = "fixed"`, in the record |
| Q2d | the per-trial FLIP RATE, first-class | `flip_rate`, beside `flips` and `evaluated` |

FIXED rather than randomized, and the reason is recorded rather than assumed:
§12.1's determinism admits exactly two roads — seed the kernel or log the draw
— and Q2's measurement is that criterion order SHIFTS a criterion's mean, not
that randomizing removes the shift. Fixing it makes the shift constant and
named.

Two roads, and the rubric one is OPTIONAL (D-6 answer A, and the operator's
solo law): the program road needs no seat, so succession is never locked out of
a solo run. A rubric ruling is admitted only through the existing
`pairwise_discriminate` guard — its referential-integrity, order-swap and
execution-supremacy screens all still apply — reached through two GENERIC
keywords (`presentation`, `observer`) so `informal/` learns nothing about
frames and no new package edge is created.

`check: python -m pytest tests/test_calculus_succession_trial.py -q`
`check: python -c "
import ast, pathlib
t = ast.parse(pathlib.Path('src/deepreason/informal/trial.py').read_text())
mods = [(n.module or '') for n in ast.walk(t) if isinstance(n, ast.ImportFrom)]
assert not [m for m in mods if 'calculus' in m], mods
"`

## Anomaly conservation (Rung 7)

Nothing new was built for it: `succeeded_wound_refs`, the machine-derived wound
list, and `bounded` validity with its domain and tolerance all shipped at Rungs
4–5. What Rung 7 adds is the proof that the road CLOSES.

A successor claims the incumbent's wounds as MENTIONS, and the role is the
whole of the safety: a DEPENDENCE would suspend the successor the moment a
wound was reinstated away, so a successful defence of the incumbent would
silently unseat its replacement. The successor's scope statement fixes the
incumbent's residual validity domain, leaving a bounded-validity assertion for
the fallen subject — INSTRUMENT STANDING, which is not a third standing value
but a consulted grant whose `validity` reads `bounded` (C3). It is authored by
the successor and attackable like anything: refute it and the fallen subject
stops framing even its bounded domain, and that fall cascades exactly as the
first one did.

`check: python -m pytest tests/test_calculus_anomaly_conservation.py -q`

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
`standing_view`, `origin_problem`, `problem_parents`, `lineage_root`,
`lineage_span`, `candidate_scope`, `build_certificate`, `nominate`,
`criteria_for`, `succeeds`, `ordering_holds`, `promotion_criteria_sweep`,
`fallen_frames`, `unseparated_fallen_frames`, `framed_problem_ids`,
`succession_trial_of`, `is_succession_trial`, `render_succession_context`,
`run_succession_trial`, `record_succession_trial`.

- **A promotion criterion that counted SUBSTANTIVE would close a loop nobody
  wants.** The class in `programs.PROGRAMS` decides whether a program can ground
  reach and confer prose immunity, and reach is what NOMINATES — so a
  substantive promotion criterion would let promotion paperwork manufacture the
  signal that produced it. All six of Rung 5's programs are therefore declared
  `structural`, which in this tree only ever WITHHOLDS. The mechanical
  consequence is dual registration: `programs_by_class()` reads `PROGRAMS`
  alone, so a criterion living only in `BLOB_PROGRAMS` would count substantive
  by default, as `dataset_oracle` correctly does. Shipped 2026-08-24 (Rung 5).
`check: python -c "from deepreason.programs import PROGRAMS, BLOB_PROGRAMS, programs_by_class; from deepreason.calculus.promotion import PROMOTION_PROGRAMS; d = set(programs_by_class()['structural']); assert set(PROMOTION_PROGRAMS) <= d; assert set(PROMOTION_PROGRAMS) <= set(BLOB_PROGRAMS); assert 'dataset_oracle' not in d"`

- **An unknown accounting makes every component look idle.** Non-immunization
  asks what a rival's accounted problems ASK FOR; if the certificate never froze
  one of them, `needed` computes as EMPTY and every uncriticised component
  passes the idle test — felling a rival for the environment's gaps rather than
  for its own riders. The relation answers `overrun` with
  `accounting-not-in-environment` instead. Found by the fixtures during Rung 5's
  own step 10, before it could reach a run.
`check: python -c "import inspect; from deepreason.calculus.promotion import _succeeds_one; assert 'accounting-not-in-environment' in inspect.getsource(_succeeds_one)"`

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
  and only for frame assertions. The check reads CALLERS, not text, and it
  did not always.** Until 2026-08-24 it grepped every file outside
  `calculus/` for the STRING `consultability`, which is a proxy for the claim
  rather than the claim. Rung 7's cascade entry explains in a docstring why it
  calls Rung 3b's predicate instead of re-deriving the graph condition — a
  sentence that makes the code more legible and trips a text grep. Rewording
  the prose to satisfy the proxy would have made the code worse to keep a
  weaker check green, so the check now parses for CALL and IMPORT sites, which
  is what "no caller" always meant. The rest of the row is unchanged, and so is
  the parked question it protects.** Rung 3b shipped the predicate and said Rung 4
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
`check: python -c "
import ast, pathlib
hits = []
for path in sorted(pathlib.Path('src/deepreason').rglob('*.py')):
    if str(path).startswith('src/deepreason/calculus/'):
        continue
    tree = ast.parse(path.read_text())
    for node in ast.walk(tree):
        if isinstance(node, ast.Call) and 'consultability' in ast.unparse(node.func):
            hits.append(f'{path}:call')
        if isinstance(node, ast.ImportFrom) and any('consultability' in a.name for a in node.names):
            hits.append(f'{path}:import')
assert hits == [], hits
" && grep -q "def consultability_of" src/deepreason/calculus/standing.py && grep -q "consultability(harness, assertion_id, body.subject_ref)" src/deepreason/calculus/standing.py && python -c "import ast, pathlib; tree = ast.parse(pathlib.Path('src/deepreason/premises.py').read_text()); mods = {(n.module or '') for n in ast.walk(tree) if isinstance(n, ast.ImportFrom)}; bad = {m for m in mods if m.startswith(('deepreason.calculus.claims', 'deepreason.calculus.compiler', 'deepreason.calculus.operations'))}; assert not bad, sorted(bad)" && grep -q "def standing_attributions" src/deepreason/premises.py`
- **Two-step registration leaves a gap, and the gap is the right trade.**
  `register_problem` then `ensure_problem_subject` can be interrupted between
  the writes. The result is a typed `problem_subject_missing` diagnostic and an
  idempotent repair on resume — preferable to changing event atomicity to close
  a very small recoverable window. The operation is idempotent because the body
  is a pure function of the `Problem` record, so its content address is too.
`check: python -m pytest tests/test_calculus_claim_substrate.py::test_ensure_problem_subject_is_idempotent tests/test_calculus_claim_substrate.py::test_the_missing_companion_diagnostic_names_the_gap_and_clears -q`
- **NO SCHEDULER SELECTION, deliberately — and this row was NARROWED at Rung 5
  rather than retired.** Nothing selects on `problem_status`, and when something
  does it must schedule accepted unresolved subjects and must NOT silently drop
  refuted or orphaned problems from history. That is the claim. The old check
  was a proxy for it — "the scheduler imports nothing from `calculus/`" — and
  Rung 5 broke the proxy without touching the claim: `_promotion_step` calls
  `nominate` and `promotion_criteria_sweep`, which spawn a problem and fire its
  criteria, and neither reads a problem's status to decide what to work on
  next. The check now asserts the claim itself — the scheduler reaches no
  derived problem-status view and no standing view — which is what a future
  reader needs it to say.
`check: python -c "
import ast, pathlib
forbidden = {'problem_status', 'problem_subject_of', 'problem_subject_missing', 'standing_of', 'standing_view'}
for path in sorted(pathlib.Path('src/deepreason/scheduler').rglob('*.py')):
    tree = ast.parse(path.read_text())
    names = {a.name for n in ast.walk(tree) if isinstance(n, ast.ImportFrom) for a in n.names}
    assert not (names & forbidden), (str(path), sorted(names & forbidden))
    mods = [(n.module or '') for n in ast.walk(tree) if isinstance(n, ast.ImportFrom)]
    assert not [m for m in mods if 'calculus.standing' in m or 'calculus.views' in m], str(path)
"`
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

  **NARROWED at Rung 7, and narrowed to what the claim was always about.** The
  check used to forbid the string `deepreason.calculus` appearing anywhere in
  `premises.py` at all, which was a PROXY for "the channel is not on the
  substrate" rather than the claim itself. Rung 7 wires the cascade's SECOND
  entry condition — a fallen frame marks what it framed — and that entry reads
  `calculus.standing.fallen_frames` through a function-local import. It does
  not move the attribution or the premise onto a claim body: `file_premise`
  still builds its own interface, `presupposition_wf` still owns the mention
  law, and the two shapes are still kept in step by hand. So the check now
  asserts the claim itself — `premises.py` imports nothing from
  `calculus.claims`, `calculus.compiler` or `calculus.operations`, the three
  modules the substrate actually lives in. The narrower form is also SHARPER:
  it names the modules, so it cannot be satisfied by reaching the same bodies
  under another path, and it no longer fails for a reader that merely CONSULTS
  the calculus.
`check: python -c "import ast, pathlib; tree = ast.parse(pathlib.Path('src/deepreason/premises.py').read_text()); mods = {(n.module or '') for n in ast.walk(tree) if isinstance(n, ast.ImportFrom)}; bad = {m for m in mods if m.startswith(('deepreason.calculus.claims', 'deepreason.calculus.compiler', 'deepreason.calculus.operations'))}; assert not bad, sorted(bad); assert 'deepreason.calculus.standing' in mods" && python -c "
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
