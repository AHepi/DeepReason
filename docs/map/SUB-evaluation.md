<!-- DR-SUB-evaluation -->
Verified-at: 461cf287
Verify: python -m pytest tests/test_oracle.py tests/test_hv.py tests/test_informal.py tests/test_trial.py tests/test_standards.py tests/test_audits.py tests/test_dataset_oracle.py -q
Owns: src/deepreason/programs.py, src/deepreason/oracle.py, src/deepreason/oracle_sandbox.py, src/deepreason/measures/, src/deepreason/informal/
Seams: DR-SEAM-evaluation-x-rules, DR-SEAM-evaluation-x-ontology
Seams-undocumented: adjudication x evaluation, authority x evaluation, evaluation x harness, evaluation x llm, evaluation x periphery, evaluation x scheduler, evaluation x schools, evaluation x verification, evaluation x warrants-and-attacks

# Evaluation — how a commitment becomes a verdict, and where formal stops and informal begins

## What it is

A commitment declares what would refute an artifact; this subsystem decides
whether that declaration can be settled by machine, and settles it when it can.
`programs.py` is the single gate: `evaluate` turns one commitment plus one
artifact's real bytes into `pass | fail | overrun` and a trace, and it refuses —
`NotEvaluable` — for anything the trial protocol must handle instead. `oracle.py`
is the half that gets its verdict by RUNNING untrusted model output against fixed
inputs inside a disposable subprocess; `measures/` scores accepted work on
hard-to-vary and cross-problem reach; `informal/` runs the guarded rubric court
for claims no program can decide. The formal/informal boundary is not a type on
an artifact: it is a pair of predicates in `rules/warrants.py` reading two sets
that live here — `oracle.EXEC_PROGRAMS` and `reach._STRUCTURAL_PROGRAMS` — so
moving a program name between those sets silently changes which targets prose
can refute.

Every verdict is a pure function of content (§0): no wall-clock reaches a verdict
or a trace, and `rubric:` never reaches a program at all.
`check: grep -q "from deepreason.oracle import EXEC_PROGRAMS" src/deepreason/rules/warrants.py && grep -q "from deepreason.measures.reach import _substantive" src/deepreason/rules/warrants.py && sh -c '! grep -nE "^import time|^from time|time\.time\(\)|datetime" src/deepreason/programs.py src/deepreason/oracle.py' && grep -q 'raise NotEvaluable("rubric verdicts require the trial protocol' src/deepreason/programs.py && grep -q "wall-clock must" src/deepreason/programs.py`

## Entry points

**`programs.py` — the gate.**
- `evaluable(commitment)` — is this commitment machine-decidable at all
  (`predicate:`, or a `program:` name in `PROGRAMS`/`BLOB_PROGRAMS`).
- `evaluate(commitment, artifact, blobs)` — the ONE route from a commitment to a
  verdict. Exactly ten modules call it: `rules/crit.py` (`crit_program`,
  `try_counterexample`, `crit_fuzz`, `_crit_proposed_properties`),
  `rules/warrants.py` (`execution_backed`/`formally_backed`),
  `rules/experiment.py::_oracle_ready`,
  `rules/guards/anti_relapse.py::verdict_vector`, `measures/reach.py::_verdict`,
  `measures/hv.py` (`_survival`, `_text_vector`),
  `scheduler.py::Scheduler.report`, `skills/validate.py`, `skills/adoption.py`
  and `experiments/lambda_run.py`.
- `program_class(commitment)` — process classification only (`structural`,
  `execution`, `simulation`, `formal`, `observation`); consumed by the
  anti-relapse gate, never by adjudication.
- `content_text(artifact, blobs)` — the artifact's real bytes, inline or blob.
- `PROGRAMS` (name → `ProgramSpec`) and `BLOB_PROGRAMS` (the additive registry
  for programs that also receive the blob store).

**`oracle.py` — verdicts from execution.**
- `run_from_spec` / `run_property_from_spec` / `check_generator_from_spec` /
  `check_checker_from_spec` / `dataset_from_spec` — the five `programs.py`
  adapters; each reads its frozen spec out of `commitment.budget.extra["spec"]`.
- `exec_oracle_commitment`, `property_oracle_commitment`,
  `dataset_oracle_commitment`, `generator_wf_commitment`,
  `checker_wf_commitment`, `property_violation_commitment` — content-addressed
  constructors; the spec is hashed into the id, so retuning a suite only affects
  future instantiations.
- `admit_counterexample(base, args)` — the critic's grounded recourse: gate a
  proposed input and mint a single-input property oracle, returning a
  deterministic rejection reason the caller may echo back.
- `fuzz_property(source, base, fuzz_n, generator=..., checker=...)` — the
  harness's own experimenter; enumerates `gen(0..n-1)`, no model in the loop.
- `EXEC_PROGRAMS` — the frozen set of "verdict came from reality" program names.
- `dataset_rows(data, delimiter)` — bounded deterministic sidecar parse.
`check: for s in evaluable evaluate program_class content_text programs_by_class external_toolchains; do grep -q "def $s(" src/deepreason/programs.py || exit 1; done; for s in run_from_spec run_property_from_spec check_generator_from_spec check_checker_from_spec dataset_from_spec fuzz_property admit_counterexample counterexample_commitment exec_oracle_commitment property_oracle_commitment generator_wf_commitment checker_wf_commitment property_violation_commitment dataset_oracle_commitment dataset_rows; do grep -q "def $s(" src/deepreason/oracle.py || exit 1; done; grep -q "^PROGRAMS: dict\[str, ProgramSpec\] = {" src/deepreason/programs.py && grep -q "^BLOB_PROGRAMS: dict = {" src/deepreason/programs.py && grep -q "def crit_program(" src/deepreason/rules/crit.py`
`check: python -c 'from deepreason.programs import PROGRAMS, BLOB_PROGRAMS, programs_by_class, external_toolchains; from deepreason.oracle import EXEC_PROGRAMS; assert set(programs_by_class()) == {"structural","execution","simulation","formal","observation"}; assert external_toolchains()["lean4"]; assert "hv_floor" not in PROGRAMS; assert "dataset_oracle" in BLOB_PROGRAMS and "dataset_oracle" not in PROGRAMS; assert EXEC_PROGRAMS == {"exec_oracle","property_oracle","dataset_oracle"}'`
`check: python -c 'import ast,pathlib; found=set(); [found.add(str(f.relative_to("src/deepreason"))) for f in pathlib.Path("src").rglob("*.py") for n in ast.walk(ast.parse(f.read_text())) if isinstance(n,ast.Call) and isinstance(n.func,ast.Attribute) and n.func.attr=="evaluate" and isinstance(n.func.value,ast.Name) and n.func.value.id=="programs"]; raise SystemExit(0 if found == {"measures/hv.py","measures/reach.py","rules/crit.py","rules/experiment.py","rules/guards/anti_relapse.py","rules/warrants.py","scheduler/scheduler.py","skills/adoption.py","skills/validate.py","experiments/lambda_run.py"} else 1)'`

Every public oracle wrapper reaches untrusted code only through
`oracle_sandbox.run_isolated`; the seven `*_local` implementations run in the
worker and never spawn. `oracle_sandbox.py` holds no epistemic policy — it
starts an interpreter, applies OS limits, exchanges bounded JSON, and raises
`SandboxAborted`, which the oracle layer alone maps to `overrun`.
`check: python -c 'import ast,pathlib; t=ast.parse(pathlib.Path("src/deepreason/oracle.py").read_text()); want={"run","run_property","check_generator","check_checker","run_dataset","fuzz_property","admit_counterexample"}; seen={n.name for n in ast.walk(t) if isinstance(n,ast.FunctionDef) and n.name in want and any(isinstance(c,ast.Name) and c.id=="_run_isolated" for c in ast.walk(n))}; raise SystemExit(0 if seen==want else 1)' && python -c 'import re,pathlib; t=pathlib.Path("src/deepreason/oracle.py").read_text(); body=t.split("_LOCAL_OPERATIONS = {")[1].split("}")[0]; raise SystemExit(0 if len(re.findall(r"[A-Za-z_]+_local", body))==7 else 1)' && grep -q "This module has no epistemic policy" src/deepreason/oracle_sandbox.py`

**`measures/` — scores, never adjudications.**
- `reach_sweep(harness, coverage_min)` — cross-problem survival; returns full
  hits and registers them as addressing via `addr_add`.
- `hv_spot_check(harness, adapter, artifact_id, k, embedder)` — lazy HV estimate.
- `hv_floor_commitment(config)` / `is_hv_floor(commitment)` /
  `run_hv_floor(harness, adapter, target_id, commitment, embedder)` — the
  hv-floor criterion; only a `fail` packages a warrant.
- `measures/demarcation.py` is a spec stub with no callers (see Traps).

**`informal/` — the guarded rubric court.**
- `run_trial(harness, target_id, commitment, adapter, config, *, authority)` —
  the full §3 guard for a `rubric:` commitment.
- `run_argument_trial_from_case(...)` — defended trial over a precomputed critic
  case; the only path from prose to an ARGUMENTATIVE warrant.
- `pairwise_discriminate(harness, problem, a_id, b_id, ...)` — §10.2 comparison
  with a mandatory order swap, indexed to the problem, never a global ranking.
- `conforming_transcript(blobs, trace_ref)` — re-checkable well-formedness of a
  rubric warrant's transcript.
- `register_standard` / `resolve_standard` / `precedent_slice` — standards as
  ordinary, attackable case-law artifacts.
- `parse_skeleton` / `skeleton_wf_program` / `draft_forbidden_commitments` /
  `compile_forbidden_commitments` — §10.1 skeletons and the model-authored
  forbidden cases they compile into commitments.
- `docket(harness, config)` / `rule(harness, case_id, holding, spec_id)` — the
  disagreement-ranked appellate queue and the precedent it produces.
- `seal` / `is_sealed` / `reveal` — §10.5 held-out evidence.
- `paraphrase_invariance_audit`, `premise_deletion_audit`,
  `planted_flaw_calibration`, `bias_probes` — program-checked attacks on judge
  BEHAVIOUR, landing as demonstrative warrants against the relevant ν. Only
  `paraphrase_invariance_audit` has a production call site (`scheduler.py`); the
  other three are named nowhere in `src/` outside `informal/audits.py` itself,
  so they run only from tests and operator code.
`check: grep -q "paraphrase_invariance_audit(self.harness, self.adapter, self.config)" src/deepreason/scheduler/scheduler.py || exit 1; sh -c '! grep -rn "premise_deletion_audit\|planted_flaw_calibration\|bias_probes" --include=*.py src/ | grep -v "^src/deepreason/informal/audits\.py:"' || exit 1; grep -q "def reach_sweep(" src/deepreason/measures/reach.py || exit 1; for s in hv_spot_check run_hv_floor is_hv_floor hv_floor_commitment; do grep -q "def $s(" src/deepreason/measures/hv.py || exit 1; done; for s in run_trial run_argument_trial_from_case pairwise_discriminate conforming_transcript; do grep -q "def $s(" src/deepreason/informal/trial.py || exit 1; done; for s in register_standard resolve_standard precedent_slice registered_specs standard_body; do grep -q "def $s(" src/deepreason/informal/standards.py || exit 1; done; for s in parse_skeleton skeleton_wf_program draft_forbidden_commitments compile_forbidden_commitments; do grep -q "def $s(" src/deepreason/informal/skeleton.py || exit 1; done; for s in docket rule spawn_audit_problem; do grep -q "def $s(" src/deepreason/informal/appellate.py || exit 1; done; for s in seal is_sealed reveal; do grep -q "def $s(" src/deepreason/informal/holdout.py || exit 1; done; for s in paraphrase_invariance_audit premise_deletion_audit planted_flaw_calibration bias_probes; do grep -q "def $s(" src/deepreason/informal/audits.py || exit 1; done`

## State it owns

Almost nothing durable of its own — the point is that a verdict is recomputable
from content the log already holds. What it does own:

- **Typed Measure-event vocabulary.** These strings are the record's only trace
  of an evaluation that mints no warrant, and downstream readers (the appellate
  docket, experiment reports, run audits) parse them: `reach-provisional`,
  `hv-nomeasure`, `hv-floor-nomeasure:<id>`, `trial-blocked:<reason>`,
  `trial-declined`, `trial-observation`, `pairwise-observation`,
  `audit-hit:<nu>`, `audit-blocked:ensemble-split`, `judge-error-rate:<r>`,
  `judge-self-preference:<r>`, `judge-verbosity-bias:<r>`, and the `trial-llm` /
  `audit-llm` call-accounting tags. `docket()` reads `trial-blocked:` and
  `audit-hit:` prefixes straight off the log.
- **Measure projections** written through the harness, not by this code:
  `hv={aid: v}`, `reach={aid: count}`, `addr=[(aid, pid)]`.
- **`<root>/holdout/<sha256>`** — sealed bytes deliberately outside the blob
  store, so the deterministic pack renderer cannot leak them. `reveal` is a
  logged `Rule.REVEAL` event; replay reproduces the unsealing.
- **`harness._verdict_cache`** — an in-memory `(commitment_id, artifact_id) →
  verdict` map. TWO fillers, not one: `reach._verdict` and
  `rules/experiment.py::_oracle_ready`. It is a cache of a pure function, never
  persisted, and both fillers deliberately skip sandbox aborts —
  `_oracle_ready` additionally parks the pair in `harness._oracle_pending` so
  the experiment retries rather than treating the envelope as an answer.
`check: python -c "import pathlib; blob=''.join(pathlib.Path(f).read_text() for f in ('src/deepreason/measures/hv.py','src/deepreason/measures/reach.py','src/deepreason/informal/trial.py','src/deepreason/informal/audits.py')); raise SystemExit(0 if all(t in blob for t in ('reach-provisional','hv-nomeasure','hv-floor-nomeasure','trial-blocked:','trial-declined','trial-observation','pairwise-observation','audit-hit:','audit-blocked:ensemble-split','judge-error-rate:','judge-self-preference:','judge-verbosity-bias:','trial-llm','audit-llm')) else 1)" && grep -q 'tag.startswith("trial-blocked:ensemble-split")' src/deepreason/informal/appellate.py && grep -q 'holdout_dir = harness.root / "holdout"' src/deepreason/informal/holdout.py && grep -q "harness._commit(Rule.REVEAL" src/deepreason/informal/holdout.py && grep -q 'tag.startswith("audit-hit:")' src/deepreason/informal/appellate.py && grep -q "_verdict_cache: dict\[tuple\[str, str\], str\] = {}" src/deepreason/harness.py && grep -q 'if "sandbox_abort" not in trace:' src/deepreason/measures/reach.py && grep -q 'if trace.get("sandbox_abort"):' src/deepreason/rules/experiment.py && grep -q "harness._oracle_pending.add(key)" src/deepreason/rules/experiment.py && grep -q "harness._verdict_cache\[key\] = verdict" src/deepreason/rules/experiment.py`

Verdict traces, HV per-edit payloads, trial transcripts and audit findings all
land in the caller's content-addressed blob store as `trace_ref` digests.

## Where to change what

| To change... | Edit | Test |
|---|---|---|
| Add a mechanically-adjudicated program | a function plus a `ProgramSpec` row in `PROGRAMS`, `src/deepreason/programs.py` | `python -m pytest tests/test_oracle.py -q` |
| Add a program that needs durable bytes (not the artifact's own) | `BLOB_PROGRAMS` and the `arg in BLOB_PROGRAMS` branch of `evaluate` | `python -m pytest tests/test_dataset_oracle.py -q` |
| What a `predicate:` expression may contain | `_validate_predicate` and `_SAFE_NAMES`, `programs.py` | `python -m pytest tests/test_security.py -q` |
| What untrusted oracle source may contain | `_guard`, `_ALLOWED`, `_INT_LITERAL_CAP`, `oracle.py` | `python -m pytest tests/test_oracle.py -k "blocked or bomb" -q` |
| Sandbox CPU/memory/IPC limits or the worker protocol | `MEMORY_CAP_BYTES`, `IPC_CAP_BYTES`, `CPU_SECONDS_MAX`, `_cpu_seconds`, `oracle_sandbox.py` | `python -m pytest tests/test_oracle.py -k "sandbox or memory_bomb" -q` |
| Which passing verdicts are immune to a preference or a prose case | `EXEC_PROGRAMS` in `oracle.py`; `_STRUCTURAL_PROGRAMS` in `measures/reach.py` | `python -m pytest tests/test_prose_refutation_boundaries.py -q` |
| Which criteria are too weak to ground reach | `_STRUCTURAL_PROGRAMS` / `_substantive`, `measures/reach.py` | `python -m pytest "tests/test_reflexive_discipline.py::test_structural_programs_never_ground_reach" -q` |
| The reach coverage threshold or the provisional rule | `reach_sweep`'s `coverage_min`; `Config.REACH_COVERAGE_MIN` | `python -m pytest "tests/test_reflexive_discipline.py::test_thin_coverage_yields_provisional_not_reach" -q` |
| HV parameters, the variation kernel, or how equivalence is decided | `hv_floor_commitment` (`HV_K`/`HV_MIN`), `_sample_edits`, `_equivalent`, `_equivalence_battery`, `measures/hv.py` | `python -m pytest tests/test_hv.py "tests/test_reflexive_discipline.py::test_hv_equivalence_decided_by_verdict_vectors" -q` |
| Add or loosen a rubric-trial guard | `_trial_steps` and `_paraphrase_screen`, `informal/trial.py` | `python -m pytest tests/test_trial.py -q` |
| Whether a trial mints a warrant or only an observation | the `TrialAuthority` branches in `informal/trial.py` — the mode itself belongs to `DR-CON-authority` | `python -m pytest tests/test_prose_refutation_boundaries.py -q` |
| Add a judge audit | a `Commitment` constant plus an audit function in `informal/audits.py`; wire it beside the `paraphrase_invariance_audit` call in `scheduler.py` or it never runs | `python -m pytest tests/test_audits.py -q` |
| Standard resolution, precedent ranking, or docket weights | `informal/standards.py`; `docket`'s `bump` weights in `informal/appellate.py` | `python -m pytest tests/test_standards.py -q` |
| The skeleton schema, or what a model-authored forbidden case may name | `Skeleton` / `ForbiddenCase._eval_kind_is_safe`, `informal/skeleton.py` | `python -m pytest tests/test_informal.py -q` |
`check: for s in _validate_predicate _SAFE_NAMES; do grep -q "$s" src/deepreason/programs.py || exit 1; done; grep -q "def _guard(tree: ast.AST) -> None:" src/deepreason/oracle.py && grep -q "_INT_LITERAL_CAP = 1_000_000" src/deepreason/oracle.py && grep -q "^_ALLOWED = (" src/deepreason/oracle.py && grep -q "MEMORY_CAP_BYTES = 512 \* 1024 \* 1024" src/deepreason/oracle_sandbox.py && grep -q "IPC_CAP_BYTES = 8 \* 1024 \* 1024" src/deepreason/oracle_sandbox.py && grep -q "def _cpu_seconds(step_limit: int, units: int) -> int:" src/deepreason/oracle_sandbox.py && grep -q "^CPU_SECONDS_MAX = 30" src/deepreason/oracle_sandbox.py && grep -q "REACH_COVERAGE_MIN: float = 0.5" src/deepreason/config.py && grep -q "coverage_min=config.REACH_COVERAGE_MIN" src/deepreason/scheduler/scheduler.py`
`check: grep -q "_STRUCTURAL_PROGRAMS = frozenset(" src/deepreason/measures/reach.py && grep -q "def _substantive(commitment) -> bool:" src/deepreason/measures/reach.py && grep -q "_EQUIV_BATTERY_CAP = 12" src/deepreason/measures/hv.py && grep -q "def _equivalence_battery(harness, artifact)" src/deepreason/measures/hv.py && grep -q "def _sample_edits(" src/deepreason/measures/hv.py && grep -q "def _equivalent(" src/deepreason/measures/hv.py && grep -q "HV_K: int = 8" src/deepreason/config.py && grep -q "HV_MIN: float | None = None" src/deepreason/config.py && grep -q "def _paraphrase_screen(" src/deepreason/informal/trial.py && grep -q "def _trial_steps(" src/deepreason/informal/trial.py && grep -q "class TrialAuthority" src/deepreason/authority.py && grep -q 'PARAPHRASE_AUDIT = Commitment(id="audit:paraphrase-invariance"' src/deepreason/informal/audits.py && grep -q "def bump(case: str, kind: str, weight: int = 1) -> None:" src/deepreason/informal/appellate.py && grep -q "^class Skeleton(BaseModel):" src/deepreason/informal/skeleton.py && grep -q "def _eval_kind_is_safe(cls, v: str) -> str:" src/deepreason/informal/skeleton.py`

## Traps

- **`overrun` is not `fail`, and the difference is the whole containment
  story.** A sandbox kill, a resource watchdog, an unusable checker, a missing
  spec, and a Lean program with no verifier all return `overrun`, and no `fail`
  warrant may be minted from one. `reach._verdict` refuses to CACHE a verdict
  whose trace carries `sandbox_abort`, because caching the availability envelope
  would turn machine flakiness into graph semantics.
`check: python -m pytest "tests/test_oracle.py::test_sandbox_abort_mints_no_fail_warrant" "tests/test_oracle.py::test_fuzz_abort_remains_pending_instead_of_marking_target_clean" -q`
- **Zero samples must not vacuously pass a floor.** `run_hv_floor` returns
  `overrun` when the variator emitted no edits; falling through would record
  `s_hat=0`, hence `hv=1.0`, hence a PASS from no evidence at all.
  `hv_spot_check` guards the SAME branch but returns `None`, not `overrun`: a
  spot-check reaches no verdict, so it logs `hv-nomeasure` and declines.
`check: python -c 'import ast,pathlib; t=ast.parse(pathlib.Path("src/deepreason/measures/hv.py").read_text()); f={n.name:n for n in t.body if isinstance(n,ast.FunctionDef)}; g=lambda k: next((ast.unparse(x.body[-1]) for x in f[k].body if isinstance(x,ast.If) and isinstance(x.test,ast.UnaryOp) and isinstance(x.test.op,ast.Not) and getattr(x.test.operand,"id","")=="edits"),None); raise SystemExit(0 if g("run_hv_floor")=="return programs.OVERRUN" and g("hv_spot_check")=="return None" else 1)' && grep -q 'record_llm_calls(\[llm_call\], "hv-nomeasure")' src/deepreason/measures/hv.py`
- **Structural well-formedness protects nothing and proves nothing.** Passing
  `json-wf`, `skeleton_wf`, `lineage_ref` or `checker_wf` says the bytes are
  well-formed, not that they answer the problem. `_STRUCTURAL_PROGRAMS` is what
  stops a candidate from attaching `program:json-wf` and immunising itself
  against all prose criticism, and `formally_backed` reuses the same set.
  `formally_backed` is a strict superset of `execution_backed`.
`check: python -m pytest "tests/test_prose_refutation_boundaries.py::test_formal_backing_covers_the_whole_formal_set_not_only_execution" "tests/test_prose_refutation_boundaries.py::test_a_structural_program_confers_no_formal_backing" "tests/test_prose_refutation_boundaries.py::test_a_structural_only_target_is_still_refutable_by_prose" -q`
- **`hv_floor` is deliberately absent from `PROGRAMS`.** It needs the variator,
  and keeping it unregistered is what makes B0 stratification structural: an
  HV battery containing itself would not terminate. `evaluable` returning False
  for it is load-bearing, not an oversight.
`check: sh -c 'grep -q "hv_floor is deliberately NOT here" src/deepreason/programs.py && ! grep -q "\"hv_floor\"" src/deepreason/programs.py'`
- **A model-authored forbidden case may never carry a `predicate:`.** It is
  copied verbatim into a registered Commitment that reaches `evaluate`'s
  `eval()`; an inline predicate there is arbitrary code execution via the
  object-subclasses walk. `ForbiddenCase` rejects any eval kind other than
  `rubric:` or `program:` at parse time, so the skeleton fails `skeleton_wf`
  rather than registering the dangerous commitment.
`check: python -m pytest "tests/test_prose_refutation_boundaries.py::test_the_forbidden_case_form_still_refuses_a_predicate" tests/test_security.py -q`
- **The `execution-backed` decline reason keeps a now-inaccurate spelling on
  purpose.** The guard was widened from execution to the whole formal set, but
  the string is compared against recorded roots; renaming it would change what
  those roots' diagnostics mean.
`check: grep -q 'return _decline(harness, target_id, "execution-backed", diagnostics)' src/deepreason/informal/trial.py && grep -q "keeps its historical spelling" src/deepreason/informal/trial.py`
- **A deduped critic swallows the judge call.** Trial code removes the decisive
  ruling's `LLMCall` from the pending list ONLY when the critic artifact
  actually committed; a byte-identical critic content-address-dedupes and
  commits nothing, so the call must stay and land as `trial-llm`. A live 1M-arrow
  run leaked 13 judge rulings this way (`verify_root` delta 10,022), and a local
  per-seat list separately dropped seat 1's spend whenever seat 2 raised.
`check: python -m pytest tests/test_trial_accounting.py -q`
- **A judge ensemble disagreement blocks; it is never averaged or resolved by
  seat zero.** `_judge_all` and `audits._ensemble_call` both return `None` on any
  split, and every audit preflights `require_cross_family_judges()` before the
  variator (or any other endpoint) can spend.
`check: grep -q "critic-gaming signal" src/deepreason/informal/trial.py && grep -q "rather than selecting seat zero" src/deepreason/informal/audits.py && python -m pytest "tests/test_audits.py::test_audit_paths_preflight_ensemble_before_any_spend" -q`
- **A missing blob evaluates as the empty string, not as an error.**
  `content_text` swallows `KeyError` and returns `""`, so a predicate over a
  sealed or absent artifact yields a confident `fail` rather than an `overrun`.
  This is what makes sealed evidence render safely; it also means a corrupted
  blob store produces verdicts instead of complaints.
`check: python -c 'import inspect, deepreason.programs as p; s=inspect.getsource(p.content_text); raise SystemExit(0 if "except KeyError:" in s and s.rstrip().endswith("return \"\"") else 1)'`
- **HV equivalence is decided by the frozen verdict vector, not by embedding
  distance.** The embedder is a pre-filter and applies only where the vector
  structurally cannot decide; agreement over the pass battery alone is vacuous
  (survivors already pass B0) and would collapse HV to 1.0, so agreement counts
  only when the equivalence battery has margin beyond it.
`check: grep -q "never by embedding proximity" src/deepreason/measures/hv.py && python -m pytest "tests/test_reflexive_discipline.py::test_hv_equivalence_decided_by_verdict_vectors" -q`
- **`measures/demarcation.py` is a spec stub, not machinery.** `crit` and `mod`
  raise `NotImplementedError` and nothing imports them; the demarcation
  discipline that actually bites is `skeleton_wf` failing an artifact that
  forbids nothing.
`check: sh -c 'grep -q "raise NotImplementedError" src/deepreason/measures/demarcation.py && ! grep -rn "measures.demarcation\|measures import demarcation" --include=*.py src/ tests/' && python -m pytest "tests/test_informal.py::test_forbid_nothing_fails_skeleton_wf_refuted_by_program" -q`
- **`ProgramSpec.class_` and `external_toolchain` are reporting facts only.**
  They never alter commitment syntax, verdict interpretation, or labels. The one
  consumer with teeth is the anti-relapse gate, which refuses to establish
  relapse equivalence from an all-`structural` battery.
`check: grep -q "never feeds adjudication" src/deepreason/programs.py && grep -q 'programs.program_class(lookup\[cid\]) == "structural"' src/deepreason/rules/guards/anti_relapse.py`
- **A `lean_*` program is an `overrun`, never a failed proof.** Invoking a kernel
  is not a pure in-process text function, so generic evaluation defers to the
  pinned verifier (`DR-SUB-verification`) and returns
  `external-verifier-required`. Reading that as a refutation would mint a warrant
  from an unavailable toolchain.
`check: python -c 'from deepreason.programs import PROGRAMS; assert PROGRAMS["lean_kernel"].external_toolchain == "lean4" and PROGRAMS["lean_kernel"].class_ == "formal"; assert PROGRAMS["lean_kernel"]("theorem x", None) == ("overrun", {"reason": "external-verifier-required", "toolchain": "lean4"})'`
- **A proposed checker is conjectured ground truth, and the safety net is
  structural.** `checker_wf` only proves a checker compiles, is bounded, and is
  non-vacuous; whether the property FOLLOWS from the problem goes to the
  relevance trial. `property_violation_commitment` declares the property artifact
  as `source_artifact` both inside the hashed spec and as a top-level budget key,
  which `adjudication/edges.py` reads to give the property's attackers an edge
  onto every ν it felled. Drop that key and a model-authored property becomes
  unaccountable ground truth.
`check: grep -q '"source_artifact": property_artifact_id,' src/deepreason/oracle.py && grep -q 'kappa.budget.extra.get("source_artifact")' src/deepreason/adjudication/edges.py`
