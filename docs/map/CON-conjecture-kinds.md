<!-- DR-CON-conjecture-kinds -->
Verified-at: f2339ade
Verify: python tools/docs_verify.py
Owns: src/deepreason/rules/crit.py, src/deepreason/rules/warrants.py, src/deepreason/scheduler/scheduler.py, src/deepreason/adjudication/grounded.py, src/deepreason/adjudication/support.py, src/deepreason/llm/contracts.py, src/deepreason/llm/packs.py
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
| Four executable-commitment paths | `capabilities/simulation.py`, `capabilities/research.py`, `experiments/lambda_run.py`, `oracle.py`, `informal/skeleton.py` | `SimulationController.propose`, `ResearchController.propose`, `run_arm`, `property_oracle_commitment`/`admit_counterexample`, `draft_forbidden_commitments` |

## Where to change what

| To change... | Edit | Test |
|---|---|---|
| Whether the conjecturer can submit a formal encoding as an explicit option (R-b, currently absent) | `llm/contracts.py::ConjectureCandidate` — Rung D2/D3 territory, not this document's authority to design | (none yet — R-b is unimplemented) |
| Whether execution supremacy protects a target from prose | `rules/warrants.py::execution_backed`/`formally_backed` — narrow vs wide guard, do not conflate (`DR-CON-criticism-source`'s own Traps entry on this) | `tests/test_oracle.py -k execution_backed`, `tests/test_prose_refutation_boundaries.py -k formal` |
| Which artifacts get re-criticized first when standing capacity is left over | `scheduler/scheduler.py::_standing_recrit_pool` — the one place today's system already orders on kind; changing this is D4/R-g territory, price it against the finding in CENSUS.md section 4 first | (none yet — no dedicated test found for this ordering specifically) |
| What the critic pack shows about a target's declared commitments | `llm/packs.py::render_crit_pack`, `_MACHINE_EVAL_NOTE` | `tests/test_prose_refutation_boundaries.py -k formal_target` |
| What happens to a target's dependents when it is refuted | `adjudication/support.py::final_labels` — do not special-case by kind; the cascade's kind-blindness is load-bearing (R-g) | `tests/test_adjudication.py::test_support_cascade_orphaned_not_false` |

## Traps

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
