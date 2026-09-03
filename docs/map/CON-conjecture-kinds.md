<!-- DR-CON-conjecture-kinds -->
Verified-at: f2339ade
Verify: python tools/docs_verify.py
Owns: src/deepreason/rules/crit.py, src/deepreason/rules/warrants.py, src/deepreason/rules/relatedness.py, src/deepreason/rules/encoding.py, src/deepreason/scheduler/scheduler.py, src/deepreason/adjudication/grounded.py, src/deepreason/adjudication/support.py, src/deepreason/llm/contracts.py, src/deepreason/llm/packs.py
Seams:
Seams-undocumented: conjecture-kinds x capabilities, conjecture-kinds x evaluation, conjecture-kinds x scheduler-ranking, conjecture-kinds x warrants-and-attacks

# Conjecture kinds — formal vs informal, and where the system may (and may not) tell them apart

## What it is

A conjectured artifact today has no typed "kind" field — `ConjectureCandidate`
carries only `content`, `typicality`, `refs`, `evidence_refs`. Whether an
artifact is FORMAL (carries an executable commitment) or INFORMAL (pure
prose) is a fact about its `Interface.commitments`, discovered by reading
that list, never declared up front. This document is the map's answer to
"where does the system look at that fact, and what is it allowed to do once
it has looked" — the census that produced it is
`experiments/2026-08-08-change-pipeline-census-d1/CENSUS.md`, and the law it
exists to protect is CLAUDE.md's "Operator design law": formalism is an
option, never an obligation; its absence earns no penalty.

Four paths mint an executable commitment today: the conjecturer's own
optional `simulation_proposals`/`research_proposals` output fields
(`rules/conj.py:1969-1970`, executed by `capabilities/simulation.py` and
`capabilities/research.py`); `experiments/lambda_run.py` (an internal
experiment harness, not reachable from the public CLI); the property-oracle
counterexample path (`oracle.py`), which is DEAD — no public path constructs
the first `program:property_oracle` commitment (full chain:
`experiments/2026-08-08-live-two-seat-ab-s6/PARKED.md` P1); and safe-skeleton
forbidden-case compilation (`workloads/models.py:105`, calling
`informal/skeleton.py::draft_forbidden_commitments`).

## The socket contract — what it promises, what it is handed, what it must never do

**Promises:** `crit_program` and `crit_argumentative`/
`crit_argumentative_batch` both run on EVERY target, formal or informal —
there is no code-level branch that skips a target because of its kind.
`crit_program` is a no-op (`[]`) whenever no commitment on the target is
`programs.evaluable`; that is what makes an informal target's DEMONSTRATIVE
pass free of side effects, not a check that reads a "kind" field.
`check: grep -n "def crit_program" -A 8 src/deepreason/rules/crit.py | grep -q "programs.evaluable(kappa)"`

The foundational acceptance computation (Dung grounded extension, Pass 1)
and the dependency support cascade (Pass 2) both take only bare artifact ids
and attack/dependency edge pairs — neither has a parameter through which a
commitment or an `eval` string could reach it.
`check: python -c "import inspect; from deepreason.adjudication.grounded import label0; from deepreason.adjudication.support import final_labels; assert set(inspect.signature(label0).parameters) == {'nodes','att'}; assert set(inspect.signature(final_labels).parameters) == {'label0','dep_edges'}"`

`execution_backed`/`formally_backed` (`rules/warrants.py`) are
PROTECTION-only: each returns `False` — no protection, not a penalty — for
any target that carries no evaluable/substantive commitment, and neither
function can ever cause a target to lose standing it would otherwise have.
`check: python -m pytest tests/test_oracle.py::test_execution_backed_false_without_oracle tests/test_prose_refutation_boundaries.py::test_a_structural_only_target_is_still_refutable_by_prose -q`

A prose case against a target that IS formally backed is refused by TYPE —
the guard runs before the authority branch, not after an attempt is scored.
`check: python -m pytest tests/test_prose_refutation_boundaries.py::test_the_execution_guard_is_consulted_before_the_authority_branch tests/test_prose_refutation_boundaries.py::test_a_prose_case_against_a_formally_backed_target_is_refused_by_type -q`

Refuting a premise orphans its dependents (`SUSPENDED_UNSUPPORTED`); it never
marks them `REFUTED` — "orphaned != false" — and this cascade reads only
`label0` strings and dependency-edge pairs, the same kind-blind inputs as
Pass 1.
`check: python -m pytest tests/test_adjudication.py::test_support_cascade_orphaned_not_false -q`

`Artifact` itself carries no "kind" field — dispatch is on interface
structure only, at the ontology level, not layered on afterward by any
consumer.
`check: python -m pytest tests/test_ontology.py::test_artifact_has_no_kind_field -q`

The optional criticism-source boundary has no dedicated, machine-interpreted
representation or epistemic-control field. Prose, notation, JSON-looking text,
and code-looking text cross unchanged; arbitrary content and its codec remain
transport data and cannot bind graph effects or formalism rank.
`check: python -m pytest tests/test_criticism_source_contract.py::test_arbitrary_content_crosses_without_classification -q`

**What it is handed:** the critic pack (`llm/packs.py::render_crit_pack`)
renders ONE template for every target; what it SHOWS about kind is entirely
data-driven — a target's `TARGET COMMITMENTS` list is populated from
`Interface.commitments` and is empty (or non-evaluable) for an informal
target, at which point `_MACHINE_EVAL_NOTE`'s warning ("do not base a case on
claiming a `predicate:`/`program:` commitment is violated") has nothing to
bind to.
`check: python -c "import inspect; from deepreason.llm import packs; assert 'kind' not in inspect.signature(packs.render_crit_pack).parameters"`

**Must never do:** weight a conjecture's rank, admission, criticism
exposure, survival, or acceptance on its kind (CLAUDE.md's "Operator design
law", DUAL_MODE_CONJECTURE_PREPLAN.md R-g). `Scheduler._select_problem`'s
own ranking key never reads a commitment or an `eval` string — it ranks
`Problem` objects (age, `SEED` trigger, reflexive-lineage membership), which
have no kind to read.
`check: ! grep -n "execution_backed\|formally_backed" src/deepreason/scheduler/scheduler.py`

THAT CHECK IS NOT SUFFICIENT AND NEVER WAS, and the gap is the finding this
clause now carries: kind can be read WITHOUT naming either guard. Two hundred
lines from `_select_problem`, in the same file, `run_report` ranked survivors
on a `coverage` axis that was `passes/evaluable-commitments` (since 2026-09-02,
passes over the commitments actually DECIDED) — an artifact that decided
nothing has no denominator, and writing 0.0 there let
`frontier`, which maximises every axis, drop it below a formally-backed
sibling. Naming a guard is one way to read kind; deriving a score FROM
`Interface.commitments` is another, and only the second one bit. Since
2026-08-30, `scheduler.pareto_scores` OMITS an axis it did not measure and
`capture/pareto.frontier` drops an axis absent from either point out of that
pairwise comparison, so "nothing to check" is neither last nor first on it. The
check below re-derives that from behaviour rather than from a grep, and its
control leg pins the other half: a battery that was checked and FAILED must
still be dominated, or the axis has been destroyed instead of repaired.
`check: python -m pytest tests/test_formalism_optional_rank.py::test_informal_and_formal_of_equal_standing_rank_equally tests/test_formalism_optional_rank.py::test_control_b_a_failed_battery_is_still_dominated tests/test_formalism_optional_rank.py::test_kind_blindness_prose_ranks_the_same_with_and_without_a_formal_channel tests/test_formalism_optional_rank.py::test_architecture_axes_that_must_not_be_zeroed_are_omitted_instead -q`

## Dual-mode conjecture (D2 rev 2) — one artifact, prose plus an optional attack surface

Operator Amendment 1 (`experiments/2026-08-08-change-pipeline-design-d2/REQUEST.md`)
rejected a twin-artifact design and re-anchored this document's own R-g
guardrail to a single direction: nothing may prioritize a FORMAL conjecture
over an informal one, but nothing stops a formal one from carrying MORE
scrutiny than a prose-only one either. The result is a THIRD `program:` kind
(`candidate_checker`, `oracle.py`) with one property none of the four
existing executable-commitment paths have: the carrying artifact's own
CONTENT is prose, never the code under test — the checker source lives in
the commitment's `Budget.extra["spec"]` instead
(`oracle.py::run_from_full_spec`, reusing `_compile`'s existing guarded-exec
engine unchanged). Dispatch needed no new branch in `programs.evaluate`: the
generic `PROGRAMS` registry (`programs.py`) already dispatches any
registered name, so `candidate_checker` joins it exactly the way
`exec_oracle`/`property_oracle` already do.
`check: python -m pytest tests/test_oracle.py::test_crit_program_refutes_a_prose_conjecture_by_running_its_checker tests/test_oracle.py::test_candidate_checker_pass_grants_formally_backed_protection -q`

Two candidate contracts can attach this commitment to their OWN prose,
never a new artifact: `informal/skeleton.py::ForbiddenCase.checker_spec`
and `workloads/text.py::Countercondition.checker_spec` (paired, additively,
via `ReasoningCandidateProposal.checker_specs` — the wire TYPE of
`counterconditions` itself never changes, so this needed no contract-version
bump). Both enforce the SAME coupling with a `model_validator`, not a
`field_validator` — Pydantic silently skips a `field_validator` on a field
left at its default, so a `field_validator`-only guard on `checker_spec`
never fires when the field is omitted (found live while writing the first
of the two, fixed before the second repeated it).
`check: python -m pytest tests/test_informal.py::test_candidate_checker_forbidden_case_requires_checker_spec tests/test_semantic_freedom_constitution.py::test_checker_specs_must_pair_one_to_one_with_counterconditions -q`

**Relatedness without a referee (Amendment 1's own words: "the referee
should be irrelevant... if a referee is needed, the artifact surface needs a
redesign").** A `candidate_checker` commitment must be "directly related to
the explanation," but nothing may adjudicate that by fiat. `rules/relatedness.py`
mints a small auxiliary artifact per (conjecture, commitment) pair
(`mint_relatedness_claim`) linked via `Ref(role=RefRole.MENTION)` — the SAME
role `active_properties` already reads for a structurally identical
"is-this-linked-thing-still-standing" question (M17: `MENTION` is inert to
the support cascade). A challenge reuses `rules/experiment.py::relevance_trial`'s
own SHAPE (`relatedness_trial`: cross-family judge ensemble, referential-
integrity + unanimity guards) rather than a new referee, and registers its
ARGUMENTATIVE fail warrant against the CLAIM artifact, never the conjecture.
`formally_backed` (`rules/warrants.py`) reads the claim's own `Status` via
`relatedness_claim_holds` and excludes the commitment from its substantive
set only while a claim exists and is not `Status.ACCEPTED` — no claim at
all (the default) leaves protection exactly as it was before this tranche.
`check: python -m pytest tests/test_relatedness.py tests/test_prose_refutation_boundaries.py::test_a_challenged_relatedness_claim_strips_only_its_own_commitment -q`

`candidate_checker` deliberately does NOT join `execution_backed`'s narrow
`EXEC_PROGRAMS` set in this tranche — that supremacy is reserved for kinds
that also carry counterexample-admission and fuzz-probe attack channels
(neither is built for this kind here); a future tranche that builds them
is what would earn the join, never the shield alone.
`check: python -c "from deepreason.oracle import EXEC_PROGRAMS, CANDIDATE_CHECKER_PROGRAM; assert CANDIDATE_CHECKER_PROGRAM not in EXEC_PROGRAMS"`

**Encoder delegation without a new manifest role.** `rules/encoding.py::draft_encoded_commitment`
lets the `"coder"` seat author a `candidate_checker`'s source for an
ALREADY-ADMITTED conjecture's prose. Registering `"encoder"` as an
independently-routable role would mean editing `run_manifest.py`'s frozen
`LEGACY_CANONICAL_ROLES` tuple — outside this tranche's own scoped grant
(`REQUEST.md` Amendment 3, C11/C12). Instead `"encoder"` reuses
`property_designer`'s already-configured endpoint via `adapter.call(...,
template_role="encoder")` — the SAME auxiliary-role pattern `experimenter`
already uses to reuse `"conjecturer"`'s endpoint (`llm/adapter.py:898-900`'s
own documented convention; `rules/experiment.py`'s own `propose_properties`
is the live precedent for `experimenter`). Zero `run_manifest.py` contact.
`check: grep -q "property_designer" src/deepreason/run_manifest.py && ! grep -q '"encoder"' src/deepreason/run_manifest.py`

**A conjecture can never be full code (Amendment 4) — a mechanical
check, not a new admission gate.** `programs.py::is_pure_code` is a
narrow, kind-blind AST test: a submission consisting SOLELY of
function/class/import statements trips it; real prose, a bare
docstring-only submission, and prose that merely quotes code inline
(not valid Python syntax as a whole) all pass. Both mandatory
well-formedness programs call it independently on their own two
free-text fields: `workloads/text.py::reasoning_wf_program` (claim,
mechanism — UNCONDITIONALLY mandatory for every reasoning-workload
artifact, the live path) and `informal/skeleton.py::skeleton_wf_program`
(claim, mechanism — mandatory only for problems that already opt into
`skeleton-wf`, a pre-existing, unrelated asymmetry this fix does not
change). A pure-code submission FAILS the same mechanical program a
forbid-nothing skeleton or an oversized envelope already fails today —
refuted by `crit_program`, never blocked at admission; no new arbiter
decides "is this prose" before criticism runs.
`check: python -m pytest tests/test_programs.py tests/test_workload_text.py tests/test_informal.py -k "is_pure_code or reasoning_wf_program or skeleton_wf" -q`

## Where it lives

| Aspect | File | Symbol |
|---|---|---|
| The (absent) kind field | `llm/contracts.py` | `ConjectureCandidate` |
| Mechanical dispatch (no branch, data-driven no-op) | `rules/crit.py` | `crit_program` |
| Argumentative dispatch (also unconditional) | `rules/crit.py` | `crit_argumentative`, `crit_argumentative_batch`, `Scheduler._arg_crit` |
| Prose-immunity guards | `rules/warrants.py` | `execution_backed`, `formally_backed` |
| What the critic sees about kind | `llm/packs.py` | `render_crit_pack`, `_MACHINE_EVAL_NOTE` |
| DEMONSTRATIVE refutation | `rules/crit.py` | `crit_program`, `rules/warrants.py::register_fail_warrant` |
| ARGUMENTATIVE refutation (trial-guarded prose) | `informal/trial.py` | `run_argument_trial_from_case`, `_argument_trial_steps` |
| Foundational kind-blind acceptance | `adjudication/grounded.py`, `adjudication/support.py` | `label0`, `final_labels` |
| The one kind-conditional SCHEDULING term found | `scheduler/scheduler.py` | `Scheduler._standing_recrit_pool` |
| The one kind-conditional RANKING term found (2026-08-27 audit F1; fixed 2026-08-30) | `scheduler/scheduler.py`, `capture/pareto.py` | `pareto_scores`, `frontier` |
| Four executable-commitment paths | `capabilities/simulation.py`, `capabilities/research.py`, `experiments/lambda_run.py`, `oracle.py`, `informal/skeleton.py` | `SimulationController.propose`, `ResearchController.propose`, `run_arm`, `property_oracle_commitment`/`admit_counterexample`, `draft_forbidden_commitments` |
| The dual-mode conjecture's own code-commitment kind (D2 rev 2) | `oracle.py`, `programs.py` | `candidate_checker_commitment`, `run_from_full_spec`, `PROGRAMS["candidate_checker"]` |
| Referee-free relatedness for that kind | `rules/relatedness.py` | `mint_relatedness_claim`, `relatedness_claim_holds`, `relatedness_trial` |
| Encoder-role delegation for that kind | `rules/encoding.py` | `draft_encoded_commitment` |

## Where to change what

| To change... | Edit | Test |
|---|---|---|
| Whether the conjecturer can submit a formal encoding as an explicit option (R-b) — PARTIALLY ANSWERED as of D2 rev 2: `ForbiddenCase.checker_spec`/`Countercondition.checker_spec` let EITHER candidate contract attach `program:candidate_checker` code to its OWN prose; `ConjectureCandidate` itself still carries no dedicated formal-encoding field | `informal/skeleton.py::ForbiddenCase`, `workloads/text.py::Countercondition`/`ReasoningCandidateProposal.checker_specs` | `tests/test_informal.py -k candidate_checker`, `tests/test_semantic_freedom_constitution.py -k checker_specs` |
| Whether execution supremacy protects a target from prose | `rules/warrants.py::execution_backed`/`formally_backed` — narrow vs wide guard, do not conflate (`DR-CON-criticism-source`'s own Traps entry on this) | `tests/test_oracle.py -k execution_backed`, `tests/test_prose_refutation_boundaries.py -k formal` |
| Whether one `candidate_checker` commitment specifically keeps `formally_backed`'s protection | `rules/warrants.py::formally_backed`'s relatedness-gated branch, reading `rules/relatedness.py::relatedness_claim_holds` — do NOT extend this to any other kind without re-deriving R43's three couplings (`REQUEST.md` Amendment 2) | `tests/test_prose_refutation_boundaries.py -k challenged_relatedness` |
| What a survivor scores on a Pareto axis, or whether it is scored on that axis at all | `scheduler/scheduler.py::pareto_scores` — OMIT the key for an axis the harness did not measure; never emit a floor value a commitment-free artifact can reach, and never let `capture/pareto.frontier` default a missing score to 0.0 again | `tests/test_formalism_optional_rank.py::test_informal_and_formal_of_equal_standing_rank_equally`, `::test_architecture_axes_that_must_not_be_zeroed_are_omitted_instead` |
| Which artifacts get re-criticized first when standing capacity is left over | `scheduler/scheduler.py::_standing_recrit_pool` — the one place today's system already orders on kind; changing this is D4/R-g territory, price it against the finding in CENSUS.md section 4 first | (none yet — no dedicated test found for this ordering specifically) |
| What the critic pack shows about a target's declared commitments | `llm/packs.py::render_crit_pack`, `_MACHINE_EVAL_NOTE` | `tests/test_prose_refutation_boundaries.py -k formal_target` |
| What happens to a target's dependents when it is refuted | `adjudication/support.py::final_labels` — do not special-case by kind; the cascade's kind-blindness is load-bearing (R-g) | `tests/test_adjudication.py::test_support_cascade_orphaned_not_false` |
| Whether a challenge to a commitment's relatedness needs a referee | `rules/relatedness.py::relatedness_trial` — reuses `rules/experiment.py::relevance_trial`'s own cross-family judge-ensemble shape rather than inventing one; registers against the relatedness-CLAIM artifact, never the conjecture | `tests/test_relatedness.py` |
| Which seat authors a `candidate_checker` commitment's source when the conjecturer doesn't inline it | `rules/encoding.py::draft_encoded_commitment` — reuses `property_designer`'s configured endpoint via `template_role="encoder"` (`llm/roles.py`); does NOT register `"encoder"` in `run_manifest.py`'s frozen `LEGACY_CANONICAL_ROLES` | `tests/test_encoding.py` |

## Traps

- **Kind can be read without naming a kind guard, and that is how the one real
  penalty got in.** Every check on this concept looked for `execution_backed`
  or `formally_backed`. `run_report`'s `coverage` axis named neither: it
  DERIVED kind from `Interface.commitments` by counting how many were
  evaluable, and scored an artifact with none of them 0.0 — the identical
  coordinate to one that was checked and failed everything. `frontier`
  maximises every axis, so a formally-backed sibling dominated an otherwise
  identical prose one and it left the run's published answer. Live footprint,
  re-measured 2026-08-30 rather than inherited: grounded-extension run
  `experiments/2026-08-12-live-grounded-extension-expansion/run` had 233
  survivors in exactly two score triples — 146 at `(0.0, 0.0, 0.0)` carrying
  nothing evaluable, 87 at `(0.0, 0.0, 1.0)` carrying something — and the
  published frontier was exactly those 87. FIXED 2026-08-30
  (`experiments/2026-08-30-defect-formalism-rank-penalty/`) by making an
  OMITTED axis mean not-measured. The enduring rule is the diagnosis, not the
  fix: when checking this concept, ask what a term is DERIVED from, not which
  helper it calls.
`check: python -m pytest tests/test_formalism_optional_rank.py -q`
- **The same axis read kind a SECOND way, and this time it penalised the formal
  side too.** Applying that enduring rule to the denominator, not just the
  numerator, finds the sibling defect: `coverage` derived its denominator from
  the count of EVALUABLE commitments, so a commitment that was evaluable but
  UNDECIDED — verdict `programs.OVERRUN`, "no verdict obtained" — counted
  against its own artifact. An informal conjecture pays it for every
  observation-valued countercondition it declares
  (`program:reasoning_observation_pending`, unconditional OVERRUN), and a
  FORMAL one pays it for every Lean commitment awaiting the pinned external
  verifier (the four `lean_*` programs, also unconditional OVERRUN). R-g's
  "formal backing may confer PROTECTION; its absence confers no disadvantage"
  was therefore violated in BOTH directions by one arithmetic. Live footprint:
  three roots — P-S1 `9e48a36b1dec91ee`, P-A1 `4565139800f5ca02`, P-R1
  `experiments/2026-08-25-poietics-program/run` — where 100% of the Pareto
  frontier answered harness-minted problems and 100% of the seed-answering
  artifacts were dominated, with zero FAIL verdicts anywhere to explain it.
  FIXED 2026-09-02 (`experiments/2026-09-02-defect-coverage-pending-commitments/`).
  The enduring rule, sharpened: ask what a term is derived from — and then ask
  the same question of its DENOMINATOR, which is where the count of
  commitments hides after the numerator has been cleaned up.
`check: python -m pytest tests/test_coverage_pending_commitments.py -q`
- **A repair to a kind-conditional rank term is not "put everyone on the
  frontier".** The operator's own question when this was parked was whether
  "nothing to check" and "checked and failed" should share a coordinate
  (`experiments/2026-08-27-audit-formalism-optional/PARKED.md:73-77`). The two
  roads that answer it by ASSIGNING a value both fail: 0.0 is today's penalty,
  and a neutral 1.0 makes "nothing to check" out-rank a formally-backed
  artifact whose battery half-passed — the same weight with its sign flipped,
  which R-g's "may weight ranking ... on a conjecture's KIND" forbids in both
  directions. Only declining to score the axis removes the weight instead of
  moving it. The argument is re-runnable at
  `experiments/2026-08-30-defect-formalism-rank-penalty/road_law_probe.py`.
- **The two supremacy guards are not interchangeable** — already recorded in
  `DR-CON-criticism-source`'s own Traps, restated here because it is exactly
  a kind-signal trap: `crit.py` consults the narrow `execution_backed`
  because its guard also decides whether a case is RECORDED as scrutiny;
  `informal/trial.py` consults the wide `formally_backed` because its guard
  decides a STATUS. Widening `crit.py`'s guard to match the trial's would
  delete scrutiny evidence for every target carrying a passing problem
  criterion that is not execution-backed.
`check: grep -q "formally_backed" src/deepreason/informal/trial.py && ! grep -q "formally_backed" src/deepreason/rules/crit.py`
- **A naive grep for "kind-conditional" code over-matches on `compile()`.**
  `llm/wire.py`, `bridge/ledger.py`, `scratch/contracts.py` and others define
  wire-contract `.compile()` methods (JSON-to-typed-object parsing) that
  match `exec\(|...|compile\(`-shaped patterns without being anything to do
  with code EXECUTION or a conjecture's kind. This tranche's own CENSUS.md
  M5 found 51 such false positives out of 77 raw hits; read the surrounding
  function signature before classifying any hit from a pattern this broad.
- **`_standing_recrit_pool`'s kind-conditional ordering is real, but does not
  currently produce a penalty** — found and stress-tested by this document's
  own originating census (CENSUS.md section 4, sub-part (a)): execution-
  backed artifacts queue FIRST for leftover-capacity re-criticism, which can
  only ever DELAY an informal target's turn (never advance it) and cannot
  turn a mechanically-protected re-attack into a real threat. Recorded here
  so a future change to this function is designed against the actual
  finding, not a rediscovery of it.
`check: python -m pytest tests/test_oracle.py::test_property_backed_candidate_counts_as_execution_backed -q`
- **The live capability channel's committed footprint is a single attempt.**
  Across every `experiments/**/log.jsonl` root committed to this repository
  (48 roots, 941 conjecturer wire-validation attempts), exactly ONE ever
  touched a `simulation_proposals`/`research_proposals` field, and it failed
  on a `min_length` schema violation — encoding, not content. Do not
  over-generalize a rate from this; report it as the small sample it is
  (CENSUS.md section 6, M13/M14).
- **The wire-contract firewall rejects a bare `dict` field outright.**
  `llm/wire.py::_reject_unknown_fields` treats an untyped `dict`'s empty
  `"properties": {}` as "no key is ever valid" and raises `extra field at
  <path>/<key>` for every key an LLM-facing structured output actually
  sends. `ForbiddenCase.checker_spec`/`Countercondition.checker_spec` (plain
  `dict`) work only because nothing routes them through `adapter.call`
  directly; the moment a role's OWN output needs this shape
  (`llm/contracts.py::EncoderOutput.tests`), it needs an explicit nested
  model (`EncoderTestCase`) instead. Found live authoring the encoder
  contract (D2 rev 2 step 21); check before reusing `dict` on any new
  LLM-facing field.
`check: python -m pytest tests/test_encoding.py::test_bound_coder_seat_delegates_to_the_encoder_template -q`
- **Registering a genuinely new, independently-routable role touches a
  frozen surface.** `run_manifest.py::LEGACY_CANONICAL_ROLES` is where a
  role like `property_designer` becomes independently routable in the
  manifest — editing that tuple is surface-4 contact, gated the same as any
  other frozen-surface change. The module's OWN comment (line ~52) already
  names the escape hatch: an AUXILIARY role (`experimenter`, now also
  `encoder`) that reuses an existing canonical role's endpoint via
  `adapter.call(..., template_role=...)` never touches this tuple at all.
  Read that comment before assuming a new role needs a manifest entry.
`check: grep -q "independently routable roles" src/deepreason/run_manifest.py`
- **A `field_validator` on a field left at its default never fires.**
  Pydantic v2 skips `field_validator`s for fields the caller omitted
  (unless `validate_default=True`); a `field_validator("checker_spec")`
  alone let `ForbiddenCase(case="x", eval="program:candidate_checker")`
  construct successfully with no checker source at all. Fixed with
  `model_validator(mode="after")`, which inspects `self` regardless of
  which fields were explicitly set; applied proactively (no repeat bug) to
  the second, structurally identical field on `Countercondition`.
`check: python -m pytest tests/test_informal.py::test_candidate_checker_forbidden_case_requires_checker_spec -q`
