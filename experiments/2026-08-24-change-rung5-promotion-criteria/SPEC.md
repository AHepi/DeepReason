# Spec for: Rung 5 — promotion problems and their criteria as programs
Traces: every item cites R/C numbers from REQUEST.md. Untraceable items are bugs.

## The shape, in one paragraph

Nomination is a fold over the log that DETECTS (R1, R2) and freezes what it
detected into one registered, content-addressed **reach certificate**
(`poietic.reach-certificate.v1`, a name already in `claims.py`'s CLOSED set with
no producer). The certificate is the frozen fence-stamped input Rider 5 clause
(4) requires: the five criteria are ordinary registry programs that read the
CANDIDATE's bytes plus that certificate, and never live graph state. Promotion
itself is an ordinary Conj→Crit→Adj pass on the spawned promotion problem, whose
`criteria` are the five commitments.

## Items

### S1 (R1, R2) — nomination as a measure-rule over the log

`src/deepreason/calculus/nomination.py` (new).

before: `state.reach` counts hits; nothing aggregates them by problem lineage,
and `ensure_promotion_problem` (Rung 4) has no caller — the blast gate reports
it `UNREACHABLE` today.

after: three pure functions and one sweep.

- `problem_parents(harness, pid)` — the problems one problem descends from:
  every entry of `provenance.from_` that is itself a problem, plus, for every
  entry that is an ARTIFACT, that artifact's ORIGIN problem (the FIRST `(aid,
  pid)` pair for it in `state.addr`, which is append-only and therefore
  replay-stable; later reach-induced addressing cannot move it).
- `lineage_root(harness, pid)` — walk parents, taking `min()` at every branch so
  the answer is deterministic, until a problem with no parents is reached; a
  cycle returns `min(visited)`. Total by construction.
- `lineage_span(harness, aid)` — the distinct lineage roots of the problems the
  artifact addresses.
- `nominate(harness, config) -> list[Problem]` — for every ACCEPTED artifact with
  `state.reach[aid] > 0` whose `lineage_span` has at least `config.K_FRAME`
  members, over a COHERENT candidate scope (S3), register the reach certificate,
  call Rung 4's `ensure_promotion_problem` unchanged, and pin the five criteria.
  Idempotent: the promotion problem id is already a pure function of the subject.

The measure never decides (R2): `nominate` writes a `Problem` and commitments and
NOTHING else. It sets no status, mints no warrant, and touches no label.

accept:
`python -m pytest tests/test_calculus_nomination.py -q` → 0 failed, and
`python -c "import ast,pathlib; t=ast.parse(pathlib.Path('src/deepreason/calculus/nomination.py').read_text()); names={n.attr for n in ast.walk(t) if isinstance(n,ast.Attribute)}; assert not {'status','hv'} & names"`
→ exit 0 (the module cannot read or write a label).

### S2 (R3) — `K_FRAME` as a Config knob with its versioned-source line

`src/deepreason/config.py`, `src/deepreason/run_manifest.py`.

before: no lineage-span threshold exists.

after: `Config.K_FRAME: int = 2` and `Config.PROMOTION_ENVIRONMENT_MAX: int = 64`
(S3's cap), each with an explicit `data.pop(..., None)` line in
`_versioned_source_config_data` carrying its own reason comment, so no
qualification subject digest and no frozen manifest golden moves — the
`ENGAGED_CRITICISM_AUTHORITY` trap, named by R3 itself.

accept:
`python -c "import json; from tests.test_reusable_qualification import _manifest, _profile; c=json.loads(_manifest(_profile()).engine_config_json); leaked=sorted(k for k in c if k in ('K_FRAME','PROMOTION_ENVIRONMENT_MAX')); assert not leaked, leaked"`
→ exit 0.

### S3 (R1) — the coherent candidate scope, and the reach certificate

`src/deepreason/calculus/claims.py`, `compiler.py`, `programs.py`,
`nomination.py`.

before: `poietic.reach-certificate.v1` is declared in the CLOSED schema set and
refused by `decode` with `claim-schema-not-implemented` — no producer.

after: `ReachCertificateV1` with a producer, a compiler rule, and a
`reach_certificate_wf` STRUCTURAL program (structural for `frame_assertion_wf`'s
own recorded reason: a certificate that could ground reach by being well formed
would let the promotion machinery buy its own case).

Body fields, all frozen at nomination:
- `subject_ref` (MENTION — the mention law, same as every other body here),
- `reach_records`: `(problem_id, lineage_root, measure_seq, subject_seq)` per
  reached problem — the log's own ordering, which is what S5 checks,
- `scope`: the CANONICAL candidate scope — a `declarative-scope.v1` disjunction
  of `eq(field id, text <pid>)` over the reached problems, sorted. COHERENT
  means exactly: it compiles under `scope.py`'s closed DSL within its node and
  depth bounds and admits every reached problem and no other frozen problem. A
  span too large to compile records a typed Measure abstention
  (`promotion.scope-incoherent.v1`) and does NOT nominate — a stated refusal,
  never a silent one.
- `problems`: the frozen problem records (id, description, trigger, sources,
  criteria) in scope,
- `commitments`: the frozen specs (id, eval, budget, observation_valued) of
  every criterion those problems carry,
- `subjects`: the frozen candidate pool — for each ACCEPTED artifact addressed to
  a frozen problem: its id, its declared commitment ids, its `crit`/`load`
  demarcation reading, its `hv` if measured, and its accounted problem ids,
- `consulted`: the consulted grants at nomination (assertion id, subject, scope),
- `incumbents`: per consulted subject, its wound refs (D-6's machine-derivable
  wound list: registered fail warrants against it), accounted set and `hv`,
- `k_frame`, and `truncated`: what the `PROMOTION_ENVIRONMENT_MAX` cap dropped —
  no silent caps.

accept:
`python -c "from deepreason.calculus.claims import decode, CLAIM_SCHEMAS; import json; b=decode(json.dumps({'schema':'poietic.reach-certificate.v1','subject_ref':'b','scope':{'schema':'declarative-scope.v1','predicate':{'const':True}},'k_frame':2})); assert b.subject_ref=='b'"`
→ exit 0 (the declared-but-unbuilt name now has a producer).

### S4 (R4, R8) — criterion 1: subject-demarcation

`src/deepreason/calculus/promotion.py` (new), program `promotion_subject_demarcation`.

The candidate's declared subject must be `demarcated` (§12.2: `crit ∧ load`), AND
— §12.2's closing clause, which Rung 2 could not meet (R8) — if the candidate's
scope is EMPIRICAL, at least one commitment the subject carries must be
`observation_valued`. Empirical is read off the frozen record, not guessed: a
scope is empirical iff some problem it admits carries an observation-valued
criterion.

Rung 2's cost answer is reused verbatim in shape (R8): the reading is CACHED per
subject (one entry in the certificate's `subjects` map), sampled ONCE for the
life of the run (at nomination), and when the variator seat is absent the frozen
reading is `undecided` and the criterion returns **OVERRUN**, never `fail` —
"we could not check" must never look like "we checked and it was fine".

accept: `python -m pytest tests/test_promotion_criteria.py -q -k demarcation`
→ 0 failed.

### S5 (R4) — criterion 2: reach-integrity, against the log's own timestamps

Program `promotion_reach_integrity`. Every reach record the candidate cites
(`reach_case_refs`) must appear in the certificate, and for each, the log's own
ordering must hold: the SUBJECT was registered before the Measure event that
recorded the reach (`subject_seq < measure_seq`). Where the case claims held-out
standing, the sealed-holdout machinery is the authority (I-6, §10.5): the
`Rule.REVEAL` event for the cited evidence must postdate the subject's
registration, so "the log timestamps prove the artifact predates the evidence"
is checked rather than asserted. A cited record absent from the certificate is a
`fail` (the case is not the one nomination froze); a certificate that cannot be
read at all is `overrun`.

accept: `python -m pytest tests/test_promotion_criteria.py -q -k integrity`
→ 0 failed.

### S6 (R4) — criterion 3: scope-determinism

Program `promotion_scope_determinism`. The candidate's scope compiles under
`scope.py`'s closed DSL (C1: the only inputs an expression can name are the five
fields of the `Problem` record, so determinism is STRUCTURAL) and is TOTAL over
every frozen problem record — it returns a bool for each, raising on none.
Exceeding the DSL's node or depth bound is `overrun` (unobtainable), never
`fail` (R13).

accept: `python -m pytest tests/test_promotion_criteria.py -q -k determinism`
→ 0 failed.

### S7 (R4) — criterion 4: compatibility — rivals never co-frame

Program `promotion_compatibility`. If the candidate's scope admits a frozen
problem already admitted by a CONSULTED assertion with a DIFFERENT subject, and
the candidate does not declare succession over that incumbent, the verdict is
`fail` with the detail naming the discrimination route (`disc:<problem id>`) —
an overlapping consulted assertion routes to discrimination; two subjects never
co-frame one problem. A candidate that DOES declare succession is compatibility-
clean and falls to S8, which is where succession is actually adjudicated.

"Declares succession over incumbent I" is machine-read from Rung 4's existing
field: `succeeded_wound_refs ∩ certificate.incumbents[I].wound_refs ≠ ∅`. No new
claim body, and the wound list is D-6's machine-derivable one.

accept: `python -m pytest tests/test_promotion_criteria.py -q -k compatibility`
→ 0 failed.

### S8 (R5, R6, R10) — criterion 5: accounts-for, the STRONG relation

Program `promotion_accounts_for`. With no declared incumbent the verdict is
`pass` with detail `no-incumbent` — there is nothing to succeed. With one, ALL
FOUR parts are required and the WEAK form is never built (R6):

Let `X(e)` = the frozen accounted set of the incumbent subject, and `X(e')` the
candidate subject's, both computed the same way: the problems the subject
addresses where every SUBSTANTIVE evaluable criterion of the problem verdicts
PASS on it (`measures/reach._substantive`, reused, not re-derived).

1. **recovery** — `X(e) ⊆ X(e')`, or the candidate carries an unrefuted account
   of why `e` worked over its restricted domain (a `bounded` validity whose
   `validity_domain` names the residue `X(e) \ X(e')`, which is the tree's
   existing way of saying "it worked over there").
2. **rigidity** — `hv(e') >= hv(e)` over the shared explicanda `X(e) ∩ X(e')`.
   Both readings frozen at nomination. An unmeasured `hv` on either side is
   `overrun`, not `fail`.
3. **non-immunization** — no PROPER functional component of `e'` is removable
   while preserving every registered accounting and criticism outcome. A
   functional component is one commitment on `e'`'s interface; it is IDLE iff
   (a) no registered fail warrant against `e'` names it, (b) it is not a
   criterion of any problem in `X(e')`, and (c) it is not observation-valued.
   Any idle component with at least one other component remaining ⇒ `fail`.
   This is what rejects ad-hoc riders mechanically.
4. **strictness witness** — at least one of: recovery STRICT (`X(e) ⊊ X(e')`);
   criticism survival STRICT (some criterion in the shared explicanda verdicts
   `fail` on `e` and `pass` on `e'`); rigidity STRICT (`hv(e') > hv(e)`). None
   ⇒ `fail` with reason `no-strictness-witness`.

**The refusal R10 names first**: a rival with `X(e) == X(e')`, equal `hv`, no
idle component and no differing criterion meets recovery, rigidity and
non-immunization and is still REFUSED, for want of a strictness witness. That is
the test that passes under the weak reading and must fail under this one, and it
carries the mutation proof.

accept: `python -m pytest tests/test_promotion_succession.py -q` → 0 failed,
four refusal tests present by name.

### S9 (R7, R12) — Remark 9.5's default-consult closure

`src/deepreason/calculus/promotion.py::promotion_criteria_sweep(harness, config)`.

before: a frame assertion addressed to a promotion problem is consulted as soon
as it is ACCEPTED; nothing evaluates the promotion criteria against it.

after: the sweep evaluates the promotion problem's five pinned criteria against
every artifact addressed to it and mints a DEMONSTRATIVE warrant for every
`fail` through `rules/warrants.py::register_fail_warrant` — the tree's ONE
warrant constructor, unchanged. `overrun` mints nothing (pending, never a
refutation — `DR-SEAM-evaluation-x-rules`'s own agreement). The sweep runs in the
scheduler BEFORE the render/standing consultation, so an unattacked assertion
addressed to a promotion problem cannot silently frame its scope: its criteria
fire first, the fail warrant lands, `consultability_of` returns
`FRAME_NOT_UNREFUTED`, and the renderer does not consult it.

The other half of the closure is already delivered and is re-pinned rather than
rebuilt: `standing.py::_promotion_problem_of` already makes the renderer consult
ONLY assertions addressed to `SpawnTrigger.PROMOTION` problems.

accept: `python -m pytest tests/test_promotion_closure.py -q` → 0 failed.

### S10 (R9) — the knowledge view, definition always inline

`src/deepreason/views/knowledge.py` (new), rendered by the existing `deepreason
standing` command.

`knowledge_view(harness)` returns rows for artifacts that are UNREFUTED, ACTIVE
and have `reach > 0`, every row carrying the literal label
`knowledge (unrefuted ∧ active ∧ reach > 0)`; the bare word is never printed.
`active` is read as §12.2's `demarcated` (which supersedes §6's `active ∧ mod`,
R54): `crit` is computed live (pure, no seat), and the `load` half is reported
per row as `load-bearing`, `undecided` or `declared-only` rather than silently
assumed. D-4's H3 discipline is structural here — the label string and the row
are produced by one function, so a caller cannot print one without the other.

accept:
`python -c "from deepreason.views.knowledge import KNOWLEDGE_LABEL; assert KNOWLEDGE_LABEL == 'knowledge (unrefuted ∧ active ∧ reach > 0)'"`
→ exit 0, and
`python -c "import re,pathlib; s=pathlib.Path('src/deepreason/views/knowledge.py').read_text(); assert 'KNOWLEDGE_LABEL' in s"`,
plus a test asserting the CLI never emits the bare word without the definition.

### S11 (R11, R15) — M-4 both halves, the live root as the negative control

`tests/test_promotion_nomination_live.py`.

- POSITIVE: constructed fixtures whose reach events span exactly `K_FRAME`
  distinct lineages nominate; one lineage short does not. The threshold is
  exercised at the boundary, both sides.
- NEGATIVE, on real live data: `nominate` run against the committed
  `experiments/2026-08-22-change-epoch3-second-lineage/run` (run id
  `bb0455384ea0…`, one recorded `reach_set` event, `verify_root` clean) returns
  the EMPTY list, and the test asserts WHY: the one reaching artifact's two
  addressed problems (`conn:0793267d0d4d` and the seed
  `question-4dd62735b90864a75220e09b302500bc`) share ONE lineage root. The root
  is opened `read_only=True` — a writable open repairs, i.e. destroys, the
  evidence.

accept: `python -m pytest tests/test_promotion_nomination_live.py -q`
→ 0 failed.

### S12 (R13) — Prop 12.1: every criterion terminates inside its budget

Each of the five programs takes its bound from `commitment.budget` (steps for
the pair-evaluation loops, the DSL's own node/depth bounds for scope work) and
returns `overrun` — never a slow `fail` — when the bound is hit. `overrun` means
UNOBTAINABLE (C2): the seam's existing agreement already makes an `overrun`
pending and never a refutation, and S9's sweep mints no warrant for one.

accept: `python -m pytest tests/test_promotion_criteria.py -q -k budget`
→ 0 failed, including one case per program driven to `overrun` by a budget of 0.

### S13 (R14) — L-3: the whole promotion path completes solo

`tests/test_promotion_solo.py`: nomination → certificate → criteria → warrants →
consultation, end to end, with NO judge seat and NO ensemble — `Config()`
defaults, where `JUDGE_SEATS_ENABLED` is False. D-6 answer A is what makes this
possible (C7): `accounts-for` is program-checked, and a rubric ruling would enter
only through the existing trial guard, which this rung does not invoke.

accept: `python -m pytest tests/test_promotion_solo.py -q` → 0 failed.

### S14 (R16) — the axiom ledger

`docs/map/INV-axiom-basis.md`: A8's row moves from "NOT YET PROVED — Rung 5 owns
it" to PROVED, and the missing spawn-half check is added in the SAME commit that
lands nomination, as A8's own text demands. A4 and Ax 4.1 (Genesis Inertness)
gain preservation checks over the new modules: no criterion reads
`provenance.<anything but trigger/from_>`, and no promotion module imports an
adjudication or seat path.

accept: `python tools/docs_verify.py` → the 3 known shallow-clone
`CON-run-identity.md` failures and no others; `--audit` → 0 findings.

### S15 (C3) — the map moves in the same commits

`docs/map/SEAM-evaluation-x-rules.md` gains the promotion lifecycle (the ladder's
named exit artifact): the five criteria are ordinary commitments on the existing
evaluation path, and the new structural program joins `_STRUCTURAL_PROGRAMS`.
`SUB-calculus.md`, `CON-standing-and-background.md` and
`CON-problem-layer-lifecycle.md` gain the nomination and closure sections.
`INV-frozen-surfaces.md` records the granted surface-4 contact and its
measurement. Every new check is RUN before it is written down.

accept: `python tools/docs_verify.py` full (not `--fast`) → as S14.

## Assumptions (operator may override)

- **A1 (Q1) — problem lineage.** A problem's lineage root is found by walking
  `provenance.from_` through problems and through the ORIGIN problem of artifact
  sources (first `state.addr` entry), taking `min()` at branches. Assumed,
  operator may override. It is not a free choice: MEASURED against the committed
  attempt-4 root before this spec was written, it puts all 210 problems in ONE
  lineage rooted at the seed, which is exactly what R11 requires the live root to
  show. See Measurements M1.
- **A2 (Q2) — coherent candidate scope.** The scope is DERIVED by nomination as
  the canonical sorted disjunction over the reached problem ids, and coherence
  means it compiles in the closed DSL and admits exactly the reached problems.
  Nomination detects and never decides (R2), so it authors no frame assertion —
  candidates author their own scopes and are judged against S6.
- **A3 (Q3) — how criteria reach run state.** They do not. Every criterion is a
  pure function of the candidate's bytes plus the FROZEN reach certificate,
  read through the existing `BLOB_PROGRAMS` widening (`programs.py`, the
  `dataset_oracle` precedent), whose spec is named in `commitment.budget.extra`.
  This is Rider 5 clause (4) literally — "programs consume frozen fence-stamped
  input artifacts, never live graph state". No program signature changes.
- **A4 (Q3, deviation, recorded not silent).** Rider 5 clause (4) names FOUR
  artifacts (ReachCertificate, IncumbentWoundLedger, ScopeEnvironment,
  CaptureWindow). This rung ships ONE — the reach certificate — carrying the
  incumbent ledger and the scope environment as sections, and no capture window
  (Rung 8 owns capture integration). Reason: C2's size ceiling, and Rung 5's own
  ladder text mandates no artifact count. Assumed, operator may override.
- **A5 (Q3) — the frozen candidate pool bounds what is checkable.** Subjects are
  frozen at nomination. A subject conjectured AFTER nomination is not in the
  environment and its criteria return `overrun` (`subject-not-in-environment`),
  which is pending and honest, never a refusal. Realistically the pool is
  sufficient: a frame assertion's subject is an existing artifact, and a subject
  with no reach case yet cannot be promoted anyway. Re-nomination on a later
  epoch is PARKED, not built.
- **A6 (Q4) — X(e).** The accounted set is the problems the subject addresses
  where every substantive evaluable criterion of the problem verdicts PASS —
  `reach_sweep`'s own all-qualifying-pass test, reusing `_substantive` rather
  than re-deriving it.
- **A7 (Q5) — the knowledge view is not a new public surface.** No new console
  entry point, no new MCP tool, no MCP schema change; the view is a library
  module rendered as an added section by the EXISTING `deepreason standing`
  command. C1 says the public surface is unchanged, and both wheel smokes are
  run to prove it rather than assumed.
- **A8 (Q6) — demonstrative warrants.** They fire through
  `rules/warrants.py::register_fail_warrant`, the tree's one warrant
  constructor, from S9's sweep. `overrun` mints nothing.
- **A10 (Q3) — the six new programs are declared `structural`, and registered
  TWICE.** `class_="structural"` is not a claim that they only check
  well-formedness; in this tree the class only ever WITHHOLDS reach eligibility
  and prose immunity, never grants them (`programs_by_class`'s own docstring),
  and withholding both is exactly what the promotion axis needs. Rung 4 set the
  precedent verbatim for `frame_assertion_wf`: "an artifact that could ground
  reach by being a well-formed frame assertion would let the standing axis buy
  its own promotion case." The same hazard is sharper here — a promotion
  criterion that ground reach would feed nomination, closing a self-amplifying
  loop A8 forbids — and `promotion_accounts_for` passes VACUOUSLY when there is
  no incumbent, so a substantive declaration would sell prose immunity for
  nothing. Mechanically this needs DUAL registration: `programs_by_class()` and
  therefore `_STRUCTURAL_PROGRAMS` read `PROGRAMS` alone, so a criterion living
  only in `BLOB_PROGRAMS` would be substantive by default (`dataset_oracle`'s
  situation, correct for an execution oracle and wrong here). Each criterion is
  therefore registered in `PROGRAMS` with `class_="structural"` to DECLARE its
  class — its `fn` there returns `overrun` with
  `reason="promotion-criterion-requires-blobs"`, since `evaluate` dispatches the
  blob form first and nothing should ever reach it — and in `BLOB_PROGRAMS` to
  receive the frozen certificate. Assumed, operator may override.

- **A9 — a row-number mismatch, reported not resolved.** The operator's R8 cites
  "drift row S-5" for the §12.2 empirical-scope clause; `RECONCILIATION.md`'s
  S-5 row is about standing being derived and never stored. The LADDER's Rung 5
  text carries the same citation. The OBLIGATION is unambiguous in R8's own
  words and is what this spec implements; only the row number is off.

## Questions for operator (STOP if non-empty)

None. Q1–Q6 were answered from the record (A1–A9); each candidate question was
run through `dr-ask-the-right-question`'s dominance test and none survived —
A1 in particular was settled by MEASUREMENT against the live root (M1), which is
cheaper and stronger than asking.

## Out of scope (explicit)

- Re-nomination after a new epoch, and promotion of a subject conjectured after
  nomination — not requested; PARKED.
- The departure protocol's BEHAVIOUR — Rung 6 owns it (Rung 4 assumption A2).
- Falls, revocation grades and the cascade's second entry condition — Rung 7.
- Nomination CONSTANTS tuning and the authority audit — Rung 8.
- `poietic.succession.v1` as a claim body — not needed; succession is declared
  through Rung 4's existing `succeeded_wound_refs`.
- Any new LLM role — C1 forbids it and none is wanted; the variator, conjecturer
  and critic seats are unchanged and no qualification digest moves.

## Frozen-surface contact forecast

`tools/blast_radius.py`, computed, pasted VERBATIM:

    "frozen_surface_contacts": [{"surface": "manifest schemas and validators (run_manifest.py)", "tier": "DIRECT", "target": "src/deepreason/run_manifest.py", "detail": "target file is surface path src/deepreason/run_manifest.py"}]
    "frozen_adjacent_contacts": []
    "frozen_surface_verdict": "CONTACT"
    "consumers.qualification_digest": [{"target": "src/deepreason/run_manifest.py", "tier": "CONFIRMED", "detail": "target file is part of the manifest/qualification surface itself"}]

**The grant, and why this is not an unauthorized stop-run.** The one contact is
`run_manifest.py::_versioned_source_config_data`, and it exists ONLY to add two
`data.pop(...)` lines. The operator granted exactly this contact, in advance, in
their own words, over exactly this file and for exactly this reason:

> "K_frame ships as a Config knob with its _versioned_source_config_data line
> for EVERY schema version (the ENGAGED_CRITICISM_AUTHORITY trap)." (R3)

> "FROZEN SURFACES (ladder row): surface 4 zero — new knobs on Config only, each
> with its versioned-source line" (C1)

The LADDER's own Rung 5 row pre-grants it identically ("Rungs 2, 4, 5, 6, 7, 8
each add knobs and each carry this line in their checklist"). The pop line
changes no schema and no validator: it is the mechanism that keeps the surface
at ZERO effective change, and its effect is MEASURED by S2's acceptance check
rather than asserted. Surfaces 1, 2, 3 and 5 have no target file in this spec.
This is recorded here rather than assumed silently; the operator can halt the
tranche on this section alone.

## Blast-radius census

Every hit from `tools/blast_radius.py`'s `consumers` field, classified. None
omitted.

`consumers.wheel_smoke_pins`: `[]` — empty census. MUST NOT MOVE (C1: public
surface unchanged); both smokes are run at validation to prove it.

`consumers.qualification_digest`: `run_manifest.py` CONFIRMED. **MUST NOT MOVE** —
S2's pop lines are what hold it, and its acceptance check is the proof.

`consumers.tests`:
- `run_manifest.py` → `tests/test_decommissioned_pipeline_stays_out.py:116` —
  MUST NOT MOVE (it pins what is absent from the manifest path).
- `cli/main.py` → `tests/test_calculus_standing.py:416` — **EXPECTED TO MOVE**:
  it asserts the `standing` command's output, which S10 extends with a knowledge
  section. The design predicts it; the test is extended, never weakened.
- `reach_sweep` → `tests/test_reflexive_discipline.py` (11 hits),
  `tests/test_review_fixes.py` (5 hits) — MUST NOT MOVE. `reach_sweep` has a
  ZERO-line diff in this rung; nomination READS `state.reach`, it does not
  change how reach is measured.
- `scan_spawns` → `tests/test_chaos_invariants.py` (3),
  `tests/test_h1_no_spawn_from_refutation.py` (8),
  `tests/test_harness_fixes.py` (9), `tests/test_reflexive_discipline.py` (2),
  `tests/test_research.py` (5), `tests/test_standards.py` (3) — MUST NOT MOVE.
  Nomination is a SEPARATE sweep and adds no branch to `scan_spawns`;
  `spawn.py` has a zero-line diff. `test_h1_no_spawn_from_refutation.py`
  specifically must stay green: H1's deletion is not being undone.
- `ensure_promotion_problem` → `tests/test_calculus_frame_assertions.py`
  (3 hits) — MUST NOT MOVE in behaviour; its `UNREACHABLE` reachability status
  is EXPECTED TO MOVE to REACHABLE, which is the point of the rung.

`consumers.map_checks` (15 documents): `SUB-calculus.md:4`,
`SEAM-evaluation-x-ontology.md` (7 hits), `SEAM-evaluation-x-rules.md` (3),
`SUB-evaluation.md` (6), `SUB-periphery.md` (2), `CON-authority.md` (10),
`CON-packs-and-token-economy.md` (2), `CON-run-identity.md:114`,
`CON-schools.md` (4), `CON-seats.md:193`, `INV-frozen-surfaces.md` (3),
`SEAM-manifest-x-schools.md:215`, `SUB-scheduler.md:147`,
`CON-conjecture-kinds.md` (2). Of these, **EXPECTED TO MOVE**:
`SUB-calculus.md`, `SEAM-evaluation-x-rules.md`, `SEAM-evaluation-x-ontology.md`
and `SUB-evaluation.md` (new programs join the registry and its counts),
`INV-frozen-surfaces.md` (the granted contact), plus `INV-axiom-basis.md` and
`CON-standing-and-background.md` / `CON-problem-layer-lifecycle.md`, which the
gate did not list because this spec's new files do not exist yet. All others:
**MUST NOT MOVE**.

Manual cross-check, RUN (the gate reported `PROGRAMS`/`BLOB_PROGRAMS` as
`UNKNOWN` reachability — they are dicts, not callables):

    grep -rn "PROGRAMS" tests/ docs/map/

Every hit classified:
- `tests/test_verifier_registry.py:48,55` — MUST NOT MOVE (indexes existing
  names only).
- `tests/test_reflexive_discipline.py:292,302,310` — MUST NOT MOVE. It asserts
  over the DECLARATION (`_substantive(kappa) is (spec.class_ != "structural")`)
  and its own docstring says it "cannot go red merely because the registry
  grew". A10's six structural declarations are covered the day they land.
- `tests/test_prose_refutation_boundaries.py:564,572,599` — MUST NOT MOVE, same
  declaration-driven shape.
- `tests/test_decommissioned_pipeline_stays_out.py:67,68,70` — MUST NOT MOVE; it
  merges `PROGRAMS` and `BLOB_PROGRAMS` and asserts membership of existing names.
- `docs/map/SEAM-evaluation-x-ontology.md:54` — **EXPECTED TO MOVE.** Its `G(f)`
  clause pins the EXACT sorted list of functions called with `artifact` as an
  argument inside `programs.py`; the six new wrappers join it. Updated in the
  SAME commit as the registry rows. This is precisely the hit the census exists
  to catch — two consecutive specs missed a hit of this shape (PARKED P6).
- `docs/map/SUB-evaluation.md:50,64,83,162,163,204,264,338` — `:50`, `:64`,
  `:162`, `:163` are prose about the two registries and gain the promotion rows
  (**EXPECTED TO MOVE**); `:83`, `:338` pin function names and a `lean_kernel`
  verdict and MUST NOT MOVE.
- `docs/map/SEAM-evaluation-x-rules.md:60,160,167` — MUST NOT MOVE. `:167`
  asserts `PROGRAMS`/`BLOB_PROGRAMS` are NEVER imported into `rules/`; the new
  modules live in `calculus/`, and `promotion.py` imports FROM `rules/warrants`
  (the `premises.py` direction), never the reverse.
- `docs/map/CON-warrants-and-attacks.md:155`,
  `docs/map/CON-proof-debt-and-localization.md:212`,
  `docs/map/CON-conjecture-kinds.md:101,188`,
  `docs/map/SEAM-evaluation-x-ontology.md:73,96` — MUST NOT MOVE.

## Budget

Per-item production-line estimates (`src/` only):

    S1 nomination.py                        170
    S2 config.py + run_manifest.py           16
    S3 claims.py + compiler.py + programs.py 95
    A10 dual registration + wrappers       35
    S4-S8 promotion.py (5 criteria)         230
    S9 promotion.py sweep                     45
    S10 views/knowledge.py + cli/main.py      70
    S-wiring scheduler.py + __init__.py       25

`python3 -c "print(sum([170,16,95,35,230,45,70,25]))"` → **686**

686 production lines against the ladder's 400–600 estimate and C2's ~800 stop
threshold: WITHIN, no stop owed. What grew relative to the ladder: the frozen
reach certificate (S3, 95 lines) is machinery the ladder's estimate did not name
but Rider 5 clause (4) requires, and it is what keeps the five criteria pure.

Ledgered ceiling for `tools/diff_budget.py`, all paths (production + tests + map
+ tranche artifacts): **1900**. Commits: 7 (one per checklist phase boundary).

Frozen surfaces touched: **surface 4 (`run_manifest.py`), granted above by R3 and
C1, two `data.pop` lines, measured**. Surfaces 1, 2, 3, 5: none.

Rubric: 6/6 yes — every R has a machine-decidable accept (R1→S1/S3, R2→S1,
R3→S2, R4→S4–S7, R5→S8, R6→S8, R7→S9, R8→S4, R9→S10, R10→S8, R11→S11, R12→S9,
R13→S12, R14→S13, R15→S11, R16→S14, R17→DELIVERY.md); census pasted and every
hit classified; frozen-surface forecast recorded with the tool's verbatim list;
every named mechanism traced to code it reaches (`ensure_promotion_problem`
`UNREACHABLE` today and called by S1; `register_fail_warrant` the one constructor;
`BLOB_PROGRAMS`/`budget.extra` the `dataset_oracle` precedent; `Rule.REVEAL` in
`informal/holdout.py`; `_substantive` in `measures/reach.py`); not a
DESIGN-AND-STOP request; nothing untraceable to an R/C number.

## Measurements

M1 — supports A1 and S11's negative half. Run against the committed live root,
`read_only=True`, BEFORE this spec was written:

    problems: 210 artifacts: 216 addr: 89
    reach nonzero: {'dd15f0da59cbec86c1bf837221740c10f30b07808345087941bc627a7866a7ed': 1.0}
    reaching artifact dd15f0da59cbec86 origin conn:0793267d0d4d
      addressed: ['conn:0793267d0d4d', 'question-4dd62735b90864a75220e09b302500bc']
    Counter({'research': 136, 'connection': 46, 'integration': 24, 'discrimination': 3, 'seed': 1})
    distinct lineage roots: 1 [('question-4dd62735b90864a75220e09b302500bc', 210)]
    their lineage roots: {'conn:0793267d0d4d': 'question-4dd62735b90864a75220e09b302500bc',
                          'question-4dd62735b90864a75220e09b302500bc': 'question-4dd62735b90864a75220e09b302500bc'}

The one reach event spans ONE lineage under A1's definition. Nomination must not
fire, which is R11's negative half, on real live data.

M2 — supports A3. `programs.py` already widens for blob-aware programs:
`BLOB_PROGRAMS[arg](text, commitment.budget, artifact, blobs)`, and
`oracle._load_spec` reads `budget.extra["spec"]` as JSON. No signature changes.

M3 — supports the frozen-surface forecast: `tools/blast_radius.py`'s computed
lists, pasted verbatim in that section.
