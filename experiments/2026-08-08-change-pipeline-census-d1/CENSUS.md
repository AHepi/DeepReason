# CENSUS — Rung D1 pipeline census (dual-mode conjecture program)

Every claim below is backed by the pasted command immediately above or
below it. Measured against branch `claude/pipeline-census-d1-c9h41d`,
continued from `origin/claude/monitor-session-handover-63ajqv` HEAD
`371e84d7` (see this tranche's REQUEST.md). MEASURE ONLY — no file
under `src/`, `tests/`, or `tools/` is touched anywhere in this
tranche.

## 1. Executable-commitment paths (R6, SPEC.md S5)

Four named paths, plus a bounded search for others.

### M1 — the live path: conjecturer-authored simulation/research proposals

The conjecturer's own structured LLM output carries optional proposal-draft
fields; nothing else on the live path originates a capability-channel
proposal.

```
$ grep -n "simulation_drafts\s*=\|research_drafts\s*=" src/deepreason/rules/conj.py
1969:    simulation_drafts = output.simulation_proposals if active_v5 or active_v6 else ()
1970:    research_drafts = getattr(output, "research_proposals", ()) if active_v6 else ()
```

```
$ grep -rl "SimulationProposalV1(" src/deepreason
src/deepreason/capabilities/simulation.py
```
Only `capabilities/simulation.py` constructs the typed wrapper —
confirming the S1 census's own M18/M19 finding
(`experiments/2026-08-06-change-seat-census-s1/CENSUS.md:322-323,428-429`):
`rules/conj.py:555` and `rules/conj.py:1774` (both `role="conjecturer"`)
are the only call sites that can yield a capability-channel proposal;
`capabilities/simulation.py`/`capabilities/research.py` only manage the
`PROPOSED -> VALIDATED -> GRANTED -> COMPILED -> DISPATCHED ->
SUCCEEDED/FAILED -> RESULT_PACKAGED -> CONSUMED` lifecycle of a proposal
that already exists.

Execution itself happens in `SimulationController.execute`
(`capabilities/simulation.py:467`), which compiles the model's source via
`simulation.compiler.compile_declarative_numeric` /
`validate_sandboxed_python_source` and dispatches to one of two execution
backends depending on `proposal.simulation_mode`:

```
$ sed -n '128,159p' src/deepreason/capabilities/simulation.py
```
(quoted above in this tranche's research — `sandboxed_python_v1` requires
`ContainedSimulationBackend` / `verification/contained.py`'s
`exec(compile(ast.parse(source), ...))` inside a subprocess with denied
network; `declarative_numeric_v1` requires `simulation.declarative.v1` and
runs locally, no subprocess.)

The result is **not** attached back to the conjectured artifact as a
`Commitment` — `SimulationController.consume` (`capabilities/simulation.py:1027`)
creates a *fresh reasoning work order* instead:

```
$ grep -n "def consume(" -A 8 src/deepreason/capabilities/simulation.py | head -10
    def consume(
        self,
        package: SimulationResultPackageV1,
        *,
        follow_up_work_order_ref: str,
        formal_fence_seq: int,
        scratch_fence_seq: int,
        follow_up_semantic_admission_ref: str | None = None,
    ) -> SimulationConsumptionV1:
```
The simulation/research result is reinjected as rendered context for a
later conjecture turn (`scratch/conjecture.py`'s `ConjectureContextCallReceiptV1`
supplies the same `conjecture_context=` advisory channel), not as a new
executable interface on the artifact. This is the mechanism DUAL_MODE's own
"what exists today" section calls "the live conjecturer cannot submit formal
at all (R-b fails today)" — the executable code runs, but its output never
becomes part of the conjectured artifact's own criticized commitment set.

### M2 — `experiments/lambda_run.py`: an internal experiment harness, not reachable from the public CLI

```
$ grep -rln "lambda_run" src/deepreason/
(no output — exit 1, zero hits: the literal string "lambda_run" does
not appear anywhere under src/deepreason/, including inside the module
itself, which never self-references its own filename)
$ grep -n "lambda_run\|lambda-run" pyproject.toml
(no hits)
$ python -c "import tomllib,pathlib; d=tomllib.loads(pathlib.Path('pyproject.toml').read_text()); print(d['project']['scripts'])"
{'deepreason': 'deepreason.cli.main:main', 'deepreason-mcp': 'deepreason.mcp_server:main'}
```
`lambda_run.py`'s own `run_arm` constructs the ONE Commitment with an
executable `eval` directly, on the harness, by hand:

```
$ sed -n '30,45p' src/deepreason/experiments/lambda_run.py
    harness = Harness(root)
    criteria: list[str] = []
    if program_criteria_in_loop:
        harness.register_commitment(Commitment(id="oracle", eval=oracle_eval))
        criteria = ["oracle"]
```
This is the lambda dose-response experiment (spec §11.8), invoked only by
`tests/test_lambda.py` and ad hoc scripts — no `deepreason` CLI subcommand,
no console entry point, no scheduler capability-phase call reaches it. It
registers a commitment directly rather than going through any admission
gate a live run's conjecturer would have to pass, which is exactly why it
is not a live-reachable path.

### M3 — the dead property-oracle path (S6 PARKED P1, reused verbatim)

Full diagnosis chain, quoted from
`experiments/2026-08-08-live-two-seat-ab-s6/PARKED.md` lines 24-49 (this
tranche's own re-verification of each cited line follows the quote):

> 1. `GROUP_ROLES["coder"] = frozenset({"property_designer"})`
>    (`seat_bindings.py`) — the `coder` group's ONLY role.
> 2. `property_designer` is dispatched from exactly one call site,
>    `rules/experiment.py::propose_properties`, which early-returns `[]`
>    unless `oracle.py::checker_wf_commitment(base)` returns non-`None`.
> 3. `checker_wf_commitment(base)` (`oracle.py:776`) itself early-returns
>    `None` unless `base.eval == f"program:{PROPERTY_PROGRAM}"` — i.e.
>    unless an ACTIVE property-oracle commitment already exists in the
>    run's own graph.
> 4. The only function anywhere in `src/deepreason/` that constructs a
>    NEW `Commitment` with `eval == "program:property_oracle"` is
>    `oracle.py::property_oracle_commitment` (line 335).
> 5. `property_oracle_commitment`'s only caller in the entire tree is
>    `oracle.py::admit_counterexample` (line 431).
> 6. `admit_counterexample` (`oracle.py:386`) itself REQUIRES
>    `base.eval == f"program:{PROPERTY_PROGRAM}"` as its own precondition
>    (line 397) — it mints a counterexample-derived oracle INHERITING an
>    existing base oracle's own spec; it does not mint the first one.

Re-verified against this tranche's own tree (byte-identical line numbers,
`src/` untouched throughout):

```
$ grep -n "GROUP_ROLES\s*=\|\"property_designer\"" src/deepreason/seat_bindings.py
36:    "coder": frozenset({"property_designer"}),
$ grep -n "def propose_properties" src/deepreason/rules/experiment.py
433:def propose_properties(harness, base, problem, adapter, config) -> list:
$ grep -n "def checker_wf_commitment" src/deepreason/oracle.py
776:def checker_wf_commitment(base: Commitment) -> Commitment | None:
$ grep -n "def property_oracle_commitment\|def admit_counterexample" src/deepreason/oracle.py
335:def property_oracle_commitment(
386:def admit_counterexample(base: Commitment, args) -> tuple[Commitment | None, str]:
```
Every line number above matches the current tree exactly — the identical
function names still stand at the cited lines. **Verdict: still dead** — no new caller
of `property_oracle_commitment` or `admit_counterexample` exists anywhere
in `src/deepreason/` beyond the ones PARKED P1 already named; the
circularity (minting the first property-oracle commitment requires an
existing one) is unchanged by anything since 2026-08-08's S6 tranche.

### M4 — safe-skeleton forbidden-case compilation (`workloads/models.py:105`)

```
$ sed -n '100,115p' src/deepreason/workloads/models.py
    # Safe skeleton compilation remains the only route by which model-
    # authored counterconditions can add commitments. Drafted, not
    # registered: registration is the caller's post-admission step.
    from deepreason.informal.skeleton import draft_forbidden_commitments, parse_skeleton

    skeleton = parse_skeleton(content)
    if skeleton is not None:
        for commitment in draft_forbidden_commitments(skeleton):
            drafts.setdefault(commitment.id, commitment)
            if commitment.id not in commitments:
                commitments.append(commitment.id)
```
```
$ grep -n "def draft_forbidden_commitments\|def parse_skeleton\|class ForbiddenCase" src/deepreason/informal/skeleton.py
25:class ForbiddenCase(BaseModel):
64:def parse_skeleton(text: str) -> Skeleton | None:
111:def draft_forbidden_commitments(skeleton: Skeleton) -> list[Commitment]:
```
This is the ONE model-authored route (per `rules/warrants.py`'s own
docstring, quoted in section 3 below) that lets a conjecturer's own prose
add `Commitment`s to its artifact's interface without going through the
harness-owned criteria/mandatory-interface path. `ForbiddenCase` forbids
`predicate:`-kind commitments specifically for RCE (remote code
execution) reasons — see M5's bounded search below for why `predicate:`
is treated as more dangerous than `program:` here — so this route can
only mint `program:`-eval'd commitments, which is what makes it
"formal-capable" in `formally_backed`'s sense (section 3).

### M5 — bounded search for paths these four miss

The naive pattern (`exec(|subprocess\.|ast\.parse(|compile(`) over-matches
badly — `compile(` alone matches every wire-contract `.compile()` method
(JSON→typed-object parsing, unrelated to code execution) and `re.compile`.
Narrowed to the actual executable-authoring primitives, excluding those
false positives:

```
$ grep -rnP "(?<!re\.)(?<!_)\bexec\(|(?<!_)\beval\(|subprocess\.(Popen|run|call|check_)|ast\.parse\(|(?<!re\.)\bcompile\(" src/deepreason/ --include="*.py" | grep -v "test_" | wc -l
77
```
Of these 77, 51 are `def compile(self, wire: ...)` / `contract.compile(...)`
/ `compiler.compile(...)` wire-contract methods (`llm/wire.py`,
`bridge/ledger.py`, `scratch/contracts.py`, `workflow/*_recovery.py`,
`workflows/manifest_compiler.py`, `bridge/compose.py`,
`bridge/transactional_adapter.py`, `scratch/authoring.py`,
`workflows/website.py`, `cli/doctor.py`, `referee.py`) — JSON-to-typed-
object parsing, not code execution; false positives of the grep pattern,
confirmed by reading every hit's surrounding function signature. The
remaining 26 are:

```
$ grep -rnP "(?<!re\.)(?<!_)\bexec\(|(?<!_)\beval\(|subprocess\.(Popen|run|call|check_)|ast\.parse\(|(?<!re\.)\bcompile\(" src/deepreason/ --include="*.py" | grep -v "test_" | grep -v "def compile\|\.compile(wire\|\.compile(self\|\.compile(contract\|\.compile(outline\|\.compile(raw\|contract\.compile\|compiler\.compile\|\.compile(candidate\|compile_kwargs\|super\(\).compile\|firing inside compile\|compile()"
src/deepreason/verification/simulation.py:123:        tree = ast.parse(source)
src/deepreason/verification/simulation.py:129:        exec(compile(tree, f"<{label}>", "exec"), namespace)  # noqa: S102 - guarded+isolated
src/deepreason/verification/simulation.py:326:def _kill(process: subprocess.Popen[bytes]) -> None:
src/deepreason/verification/simulation.py:352:    process = subprocess.Popen(  # noqa: S603 - fixed interpreter/module command
src/deepreason/verification/lean.py:107:        return subprocess.run(  # noqa: S603 - trusted executable and fixed Lean flags
src/deepreason/verification/runner.py:70:def _kill(process: subprocess.Popen[bytes]) -> None:
src/deepreason/verification/runner.py:139:            process = subprocess.Popen(  # noqa: S603 - argv is trusted workload input
src/deepreason/verification/contained.py:81:    tree = ast.parse(source)
src/deepreason/verification/contained.py:98:        exec(compile(tree, "<" + label + ">", "exec"), namespace)
src/deepreason/verification/contained.py:411:def _kill_group(process: subprocess.Popen[bytes]) -> None:
src/deepreason/verification/contained.py:466:                    probe = subprocess.run(  # noqa: S603 - fixed probe command
src/deepreason/verification/contained.py:633:                process = subprocess.Popen(  # noqa: S603 - frozen containment command
src/deepreason/oracle_sandbox.py:70:def _kill_worker(process: subprocess.Popen) -> None:
src/deepreason/oracle_sandbox.py:99:    process = subprocess.Popen(  # noqa: S603 - fixed interpreter/module command
src/deepreason/workloads/code.py:349:        tree = ast.parse(data.decode("utf-8"))
src/deepreason/oracle.py:119:        tree = ast.parse(source)
src/deepreason/oracle.py:125:        exec(compile(tree, "<candidate>", "exec"), namespace)  # noqa: S102 - guarded+sandboxed
src/deepreason/informal/skeleton.py:37:        controlled text into an eval() — arbitrary code execution via the
src/deepreason/programs.py:60:    """Defense-in-depth for the predicate eval() (stress-campaign RCE).
src/deepreason/programs.py:61:    eval() with __builtins__={} is escapable via `().__class__.__base__.
src/deepreason/programs.py:69:        tree = ast.parse(expr, mode="eval")
src/deepreason/programs.py:354:            verdict = PASS if bool(eval(arg, namespace)) else FAIL
src/deepreason/experiments/campaign.py:878:    return subprocess.run(list(command), cwd=cwd, check=False).returncode
src/deepreason/imports.py:291:            return subprocess.run(
src/deepreason/simulation/compiler.py:222:        tree = ast.parse(source)
src/deepreason/admission/adapters.py:186:        completed = subprocess.run(
```
Of these 26, two (`informal/skeleton.py:37`, `programs.py:60-61`) are
docstring/comment PROSE mentioning `eval()` as a risk being defended
against, not a call — 24 are actual sites.

Classification of all 24:

- **`verification/simulation.py` + `verification/contained.py`**
  (`ast.parse` + `exec(compile(...))`, `subprocess.Popen`): the two
  execution backends behind M1's simulation channel
  (`declarative_numeric_v1` local-in-process vs `sandboxed_python_v1`
  containerized) — not a new commitment-acquisition path, an execution
  BACKEND for M1.
- **`verification/lean.py` + `verification/runner.py`** (`subprocess.run`/
  `Popen`): a Lean4 kernel backend and a generic program runner, wired
  from `verification/__init__.py` and `cli/main.py:2279`
  (`LeanBackend`, gated on `item.id.startswith("lean4@")`) — an
  execution backend for the same `formally_backed`/`predicate:`
  mechanism M4 feeds, not a new path.
- **`oracle.py:119-125` + `oracle_sandbox.py`** (`ast.parse` +
  `exec(compile(...))`, `subprocess.Popen`): `oracle.py::_compile` is
  the in-process guarded loader for candidate/checker source; confirmed
  below to be the sole non-test caller of `oracle_sandbox.py`'s process
  spawn, i.e. the execution engine for M3/M4's `program:`-eval'd
  commitments, not a new path.
- **`programs.py:69,354`** (`ast.parse(..., mode="eval")`,
  `eval(arg, namespace)`): the `predicate:`-kind commitment evaluator —
  `formally_backed`'s own docstring (quoted in section 3) names
  `predicate:` as the other formal-criterion kind alongside substantive
  `program:` checks, and states `ForbiddenCase` forbids `predicate:` for
  model-authored commitments specifically because of this evaluator's
  RCE exposure. This is an execution engine for an EXISTING commitment
  kind (operator-authored `predicate:` criteria), not a new
  model-reachable path — model-authored commitments cannot use it (M4).
- **`admission/adapters.py`** (`subprocess.run` spawning
  `deepreason.admission.adapter_host`): a genuinely DIFFERENT sandboxed
  execution surface, found by this bounded search and not named in the
  task's four paths — but its own module docstring
  (`"""The §3a admission adapter contract: plugins that mint canonical
  authority. Adapters convert non-text sources into normalized
  blocks."""`) and its callers (`admission/parse.py`, `admission/attach.py`,
  `capabilities/research.py`) show it converts PDF/EPUB evidence sources
  into text blocks for the attached-evidence pipeline — it produces
  evidence content, never a `Commitment` on an artifact's interface.
  Reported here because R6 asks for "any path you find that these
  miss," but classified OUT OF SCOPE for "executable commitment" per
  R6's own framing (an artifact's commitment set), not silently dropped.
- **`imports.py:291`** (`npm` subprocess): dependency-tooling
  infrastructure (installing JS packages for a workload), unrelated to
  any artifact's commitment set.
- **`workloads/code.py:349`** (`ast.parse` only, no following
  `exec`/`compile`): static metadata extraction (symbol/dependency
  graph for the code workload's own artifact interface) — parses but
  never executes, so it cannot mint an executable commitment.
- **`simulation/compiler.py:222`** (`ast.parse`, inside
  `validate_sandboxed_python_source`): the M1 validation step that
  checks the model's proposed simulation source BEFORE it reaches
  either execution backend above — part of M1's own pipeline, not a
  separate path.
- **`experiments/campaign.py:878`** (`subprocess.run`): campaign
  automation tooling (running a shell command as part of
  `CampaignCoordinator`'s own audit/report workflow, per
  `docs/map/SUB-periphery.md`), unrelated to any artifact's commitment
  set.

```
$ grep -rln "oracle_sandbox" src/deepreason/ --include="*.py" | grep -v test
src/deepreason/oracle_sandbox.py
src/deepreason/oracle.py
```
`oracle.py` is `oracle_sandbox.py`'s only caller outside its own
definition, confirming the sandbox is a backend for the oracle/checker/
generator/dataset program family already covered by M3/M4's `eval=`
construction sites.

**M5 verdict:** no NEW path by which an artifact acquires an executable
commitment was found. One adjacent-but-distinct sandboxed-execution
surface was found (`admission/adapters.py`, evidence ingestion) and is
reported above rather than silently dropped, per R6's own instruction to
report "any path you find that these miss" — it does not qualify as a
commitment-acquisition path because it never touches an artifact's
`Interface.commitments`.

## 2. Criticism dispatch per kind (R7, SPEC.md S6)

### M6 — crit_program vs crit_argumentative: NOT an either/or dispatch by kind

```
$ grep -n "def crit_program\|def crit_argumentative\b\|def crit_argumentative_batch" src/deepreason/rules/crit.py
895:def crit_program(harness, target_id: str) -> list[Artifact]:
1175:def crit_argumentative(
1336:def crit_argumentative_batch(
```
```
$ grep -n "crit_program(harness\|crit_argumentative_batch(harness" src/deepreason/scheduler/scheduler.py
1089:        crit_program(harness, artifact.id)
1259:                crit_argumentative_batch(harness, batch, self.adapter, config)
1413:                    crit_argumentative_batch(
```
`scheduler.py:1086-1089` (`Scheduler._criticize`) calls `crit_program`
UNCONDITIONALLY on every artifact, formal or informal:

```
$ sed -n '1086,1090p' src/deepreason/scheduler/scheduler.py
    def _criticize(self, artifact) -> None:
        harness, config = self.harness, self.config
        crit_program(harness, artifact.id)
        if harness.state.status.get(artifact.id) == Status.ACCEPTED:
```
`crit_program` itself (`rules/crit.py:895-919`) is a no-op for an informal
artifact — it iterates `target.interface.commitments`, skips every
commitment where `programs.evaluable(kappa)` is false, and returns `[]`
when there is nothing evaluable. There is no branch that asks "is this
target formal or informal" — the SAME call runs on every target every
cycle, and the answer differs only because the DATA differs (whether any
commitment happens to be machine-evaluable). Separately,
`Scheduler._arg_crit` (`scheduler.py:1186-1259`) builds its own
`eligible` list from `admitted_ids` filtered on `Status.ACCEPTED` and a
per-cycle cap (`config.ARG_CRIT_PER_CYCLE`) — again no kind check — and
dispatches `crit_argumentative_batch` on that list. **Both mechanisms run
against both kinds of target; "dispatch by kind" is a data-driven
OUTCOME of `crit_program`'s own no-op-when-nothing-evaluable behavior,
not a code-level selection.**

One exception, found while tracing this: `_standing_recrit_pool`
(`scheduler.py:1150-1181`, feeding `_arg_crit`'s leftover-capacity sweep)
DOES branch on kind when ordering its queue:

```
$ sed -n '1163,1181p' src/deepreason/scheduler/scheduler.py
            role = artifact.provenance.role if artifact.provenance else ""
            if role not in ("conjecturer", "synthesizer") and artifact.codec != "code:python-prop":
                continue
            carries = any(
                (kappa := harness.commitments.get(cid)) is not None
                and kappa.eval in execution_evals
                for cid in artifact.interface.commitments
            )
            (backed if carries else rest).append(aid)
        return backed + rest
```
Execution-oracle-carrying (formal) artifacts are placed FIRST in the
standing re-criticism queue; the docstring's own reasoning: "a passing
oracle is the strongest standing claim on the graph, and a Goodhart
survivor... can hide nowhere else" — i.e. formal survivors are queued
first because a re-attack against them is the only way to catch a
checker that passes the frozen inputs but is wrong in general, NOT
because formal targets are considered more suspect. This IS a
kind-conditional scheduling term (flagged and analyzed for R-g
compliance in section 4 below, "R-g audit" sub-part (a)).

### M7 — ARGUMENTATIVE_AUTHORITY: read site and enforcement site

Read (resolved from `Config`, or from the frozen manifest policy when
manifest-bound):

```
$ grep -n "ARGUMENTATIVE_AUTHORITY:" src/deepreason/config.py
380:    ARGUMENTATIVE_AUTHORITY: Literal[
```
```
$ sed -n '378,382p' src/deepreason/config.py
    ARGUMENTATIVE_AUTHORITY: Literal[
        "observe_only", "trial_required", "single_family_trial"
    ] = "observe_only"
```
Enforced (`rules/crit.py:1303-1324`, `crit_argumentative`'s tail — the
batch variant `crit_argumentative_batch` has the identical gate at
line 1837):

```
$ sed -n '1303,1324p' src/deepreason/rules/crit.py
        if authority == "observe_only":
            return _observe_case(...)
        if authority in _TRIAL_MODES:
            from deepreason.informal.trial import run_argument_trial_from_case
            return run_argument_trial_from_case(...)
        raise RuntimeError("unreachable argumentative authority mode")
```
`observe_only` records the critic's case as scrutiny evidence without
creating a warrant/attack edge (`_observe_case`) — no status change ever
results. `trial_required`/`single_family_trial` route the case through
`informal/trial.py::run_argument_trial_from_case` (the defended
cross-family trial: critic drafts, defender answers, a judge from a
DIFFERENT model family rules a narrow question, program checks screen
the ruling — module docstring, `rules/crit.py:1-13`). The execution-
supremacy guard (`execution_backed`, M8 below) is checked BEFORE this
authority gate is reached at all — a purely argumentative case never
gets to `observe_only`/trial dispatch if the target already carries a
passing execution-backed commitment; it is discarded first
(`crit.py:1249-1301`, "Execution supremacy... a purely argumentative
case cannot override it").

### M8 — the pack: same renderer for every target, kind-signaled by data not by branch

```
$ grep -n "def render_crit_pack" src/deepreason/llm/packs.py
806:def render_crit_pack(
```
```
$ sed -n '821,830p' src/deepreason/llm/packs.py
    commitments_lines = [
        "TARGET COMMITMENTS (the target's declared attack surface):"
    ]
    for cid in target.interface.commitments:
        kappa = commitments.get(cid)
        commitments_lines.append(
            f"- {cid}: {kappa.eval if kappa else '(unregistered)'}"
        )
        if kappa is not None:
            commitments_lines += _execution_spec_lines(kappa)
```
```
$ grep -n "_MACHINE_EVAL_NOTE\s*=" -A 8 src/deepreason/llm/packs.py
79:_MACHINE_EVAL_NOTE = (
80-    "MACHINE-EVALUATED COMMITMENTS: schemas whose eval starts with "
81-    "'predicate:' or 'program:' are checked by the harness DETERMINISTICALLY "
82-    "— every target shown here currently PASSES them (failures were refuted "
83-    "mechanically before this call). Do NOT base a case on claiming such a "
84-    "commitment is violated (e.g. re-counting a length bound): that claim is "
85-    "machine-decided and your case would assert a falsehood. Argue about the "
86-    "SUBSTANCE of the content instead."
87-)
```
There is exactly one pack template (`render_crit_pack`) for every
argumentative-criticism call, formal or informal target alike — no
`if target.is_formal: render_x() else render_y()` branch exists anywhere
in `llm/packs.py`. What the critic SEES about kind is entirely a
function of the DATA: an informal target's "TARGET COMMITMENTS" list is
either empty or contains only non-evaluable entries, so
`_MACHINE_EVAL_NOTE`'s warning has nothing to bind to; a formal target's
list shows its `program:`/`predicate:` commitments plus this note
steering the critic away from re-litigating an already-mechanically-
decided question. This is R-c's "kind signal exists structurally but not
as a submission-time option" (DUAL_MODE_CONJECTURE_PREPLAN.md's own
"what exists today") made concrete: the signal is read from
`Interface.commitments`, not from any typed "kind" field — because no
such field exists on `ConjectureCandidate` yet:

```
$ grep -n "class ConjectureCandidate" -A 10 src/deepreason/llm/contracts.py
35:class ConjectureCandidate(BaseModel):
36:    content: str
37:    # Stated probability/typicality estimate for this candidate (§11.6).
38:    typicality: float = Field(ge=0.0, le=1.0)
39:    # Born-connected (§7 L1): refs to neighbourhood artifacts where natural.
40:    refs: list[CandidateRef] = Field(default_factory=list)
41:    # Claimed groundings in admitted evidence blocks (admission §4); checked
42:    # deterministically after admission, never trusted on arrival.
43:    evidence_refs: list[EvidenceRefClaimV1] = Field(default_factory=list, max_length=8)
```
`content`, `typicality`, `refs`, `evidence_refs` only — no commitment
channel, confirming R-b's "the conjecturer has the OPTION to submit a
conjecture in both forms" is not yet built.

### M9 — execution_backed / formally_backed prose-immunity, exact semantics (`rules/warrants.py`)

```
$ grep -n "^def execution_backed\|^def formally_backed" src/deepreason/rules/warrants.py
24:def execution_backed(harness, target_id: str) -> bool:
61:def formally_backed(harness, target_id: str) -> bool:
```
Both docstrings, quoted verbatim (load-bearing, not paraphrased):

> `execution_backed`: "True iff the target carries at least one
> exec-oracle commitment and EVERY exec-oracle commitment it carries
> currently passes. A passing execution verdict is a warrant from
> reality... a purely *argumentative* warrant... must not override it.
> Every argumentative registration path consults this guard and, when it
> holds, registers nothing: the critic keeps its grounded recourse
> (supply a failing input via a stronger exec-oracle... or attack the
> oracle's validity node / the commitment itself), but it cannot win by
> assertion or preference."

> `formally_backed`: "True iff the target carries at least one EVALUABLE
> AND SUBSTANTIVE commitment and EVERY such commitment currently passes.
> A superset of `execution_backed`... SUBSTANTIVE is load-bearing... An
> artifact's commitments are compiled from the problem's criteria plus
> harness-owned mandatory ones, EXCEPT for one model-authored route: safe
> skeleton compilation turns a conjecturer's own forbidden cases into
> Commitments (workloads/models.py:105). `ForbiddenCase` forbids
> `predicate:` there for RCE reasons... Were mere evaluability enough, a
> candidate could attach `program:json-wf`, which passes for anything
> well-formed, and immunise itself against criticism. Structural
> well-formedness proves nothing about the subject, so it protects
> nothing about the subject."

`execution_backed` gates ONE thing: whether an ordinary argumentative
attack is allowed to register a warrant at all (M7's guard, checked
before the authority gate). `formally_backed` is the broader
prose-immunity predicate — a strict superset, adding `predicate:`
criteria and substantive `program:` checks beyond the narrower
"exec-oracle" set (`EXEC_PROGRAMS = {exec_oracle, property_oracle,
dataset_oracle}`, oracle.py:51) `execution_backed` uses. Both are
PROTECTION-ONLY by construction: each returns `False` (no protection)
whenever the target carries no evaluable commitment at all — an
informal target is simply outside either guard's domain, never
penalized by it; the guard only ever SUBTRACTS a critic's power against
a target that already passed a real check, never ADDS a requirement an
informal target must meet.

## 3. Refutation semantics per kind (R8, SPEC.md S7)

### M10 — the DEMONSTRATIVE path: what dies

```
$ sed -n '895,919p' src/deepreason/rules/crit.py
def crit_program(harness, target_id: str) -> list[Artifact]:
    """Evaluate the target's commitments; register a critic per failure."""
    target = harness.state.artifacts[target_id]
    critics: list[Artifact] = []
    for cid in target.interface.commitments:
        kappa = harness.commitments.get(cid)
        if kappa is None or not programs.evaluable(kappa):
            continue
        if verdict_on_record(harness, cid, target_id):
            continue
        verdict, trace = programs.evaluate(kappa, target, harness.blobs)
        pending_key = (cid, target_id)
        if trace.get("sandbox_abort"):
            harness._oracle_pending.add(pending_key)
            continue
        harness._oracle_pending.discard(pending_key)
        if verdict != programs.FAIL:
            continue
        critics.append(register_fail_warrant(harness, ...))
    return critics
```
```
$ grep -n "class Status" -A 7 src/deepreason/ontology/state.py
16:class Status(str, Enum):
17:    ACCEPTED = "accepted"
18:    REFUTED = "refuted"
19:    SUSPENDED = "suspended"
20:    SUSPENDED_UNSUPPORTED = "suspended_unsupported"
```
A DEMONSTRATIVE fail warrant registers a critic artifact carrying
`WarrantType.DEMONSTRATIVE`, `commitment=<the failed kappa's id>`,
`verdict="fail"`, and an attackable `validity_node` (nu, asserting the
test was sound and relevant) — the `Warrant` model's own field comment
marks `commitment`/`verdict` "Demonstrative-only fields"
(`ontology/warrant.py:24-26`). The adjudication pass (Pass 1, attack
edges from warrants) turns this into a `Status.REFUTED` label on the
TARGET ARTIFACT ITSELF — today's system has no separate "encoding"
object distinct from the conjectured artifact (that split is D2/D3
territory, not built yet), so what "dies" is the one artifact that
carried the failing commitment. The nu node remains independently
attackable (N1: "execution can still refute" — `warrants.py`'s own
`execution_backed` docstring) — a critic can contest whether the test
itself was sound/relevant, which is the recourse against a wrong or
unsound oracle, distinct from contesting the target's content.

### M11 — what a trial-guarded prose refutation can and cannot do

```
$ grep -n "def run_argument_trial_from_case\|def _argument_trial_steps" src/deepreason/informal/trial.py
553:def run_argument_trial_from_case(
601:def _argument_trial_steps(
```
```
$ sed -n '559,571p' src/deepreason/informal/trial.py
    """Defended trial over a PRECOMPUTED critic case (phase C trial_required).
    New calls are advisory by default. Explicit canonical ``status``
    authority is required to enter the defended court path. ... The defender
    answers, the frozen cross-family judge ensemble rules, and the existing
    guard checks screen the ruling (referential integrity, ensemble
    unanimity, paraphrase invariance). Only a guard-accepted sustained (fail)
    ruling mints the ARGUMENTATIVE warrant; every other outcome records a
    ["trial-declined", target, reason] Measure and registers no warrant."""
```
```
$ sed -n '688,706p' src/deepreason/informal/trial.py
    trace_ref = transcript_blob(...)
    nu = harness.create_artifact(
        f"nu: the defended trial sustaining case {case_hash} against "
        f"{target_id} is sound", ...
    )
    warrant = Warrant(
        id=f"w:argtrial:{case_hash}:{target_id}",
        target=target_id,
        type=WarrantType.ARGUMENTATIVE,
        trace_ref=trace_ref,
        validity_node=nu.id,
    )
```
**CAN**: after passing FOUR guards in sequence — (1) a defender answers
the critic's case, (2) a judge ensemble from a DIFFERENT model family
than the critic rules the case sustained, (3) referential-integrity
check, (4) ensemble-unanimity and paraphrase-invariance screens (the
same screens the rubric trial uses) — mint a real `WarrantType.ARGUMENTATIVE`
fail warrant with its own attackable `validity_node`, carrying the full
transcript as `trace_ref`. This feeds the SAME adjudication pipeline as
a DEMONSTRATIVE warrant and can move the target to `Status.REFUTED`.

**CANNOT**: (a) override a target that is `execution_backed`
(M9 above) — the guard is checked before the trial is ever entered,
so a purely argumentative case against an execution-backed target
never reaches this far; (b) carry `commitment`/`verdict` fields — the
`Warrant` model reserves those for DEMONSTRATIVE only, so an
ARGUMENTATIVE warrant is never tied to a specific machine-checked
commitment, only to the judge's ruling text; (c) fire on anything less
than a guard-accepted UNANIMOUS sustained ruling — any decline at any
of the four gates registers no warrant at all, only an observational
Measure (`["trial-declined", target, reason]`).

### M12 — `suspended_unsupported`: what happens to dependents

```
$ grep -n "^def \|SUSPENDED_UNSUPPORTED" src/deepreason/adjudication/support.py
15:def final_labels(
30:            final[a] = Status.SUSPENDED_UNSUPPORTED
```
```
$ sed -n '1,32p' src/deepreason/adjudication/support.py
"""Pass 2 — support cascade over the dep DAG (spec §4).
Process in topological order (dependencies before dependents). Refuting a
premise makes dependents ``suspended_unsupported``, NOT refuted — orphaned
!= false. Attacking a relation artifact refutes the relation while its
endpoints may stay accepted.
"""
def final_labels(label0, dep_edges):
    ...
    for a in toposort(nodes, dep_edges):
        supported = all(final[b] == Status.ACCEPTED for b in deps[a])
        if label0[a] == "accepted" and supported:
            final[a] = Status.ACCEPTED
        elif label0[a] == "accepted":
            final[a] = Status.SUSPENDED_UNSUPPORTED
        elif label0[a] == "refuted":
            final[a] = Status.REFUTED
        else:
            final[a] = Status.SUSPENDED
    return final
```
This is Pass 2 of adjudication, run over the whole dependency DAG
(`dep_edges`), AFTER Pass 1 assigns each artifact's own `label0` from
its own warrants (REFUTED if directly attacked and sustained, else
whatever Pass-1 attack-edge semantics gave it — `label0[a] in
{"accepted", "refuted"}` is the only input this pass reads). An
artifact that was itself never attacked (`label0[a] == "accepted"`) but
depends on something that ended up NOT `Status.ACCEPTED` (refuted or
itself unsupported) becomes `SUSPENDED_UNSUPPORTED` — "orphaned != false"
per the module's own docstring: it is not judged wrong, only left
without a standing premise. This cascade is KIND-BLIND by construction
— `final_labels` takes only `label0` (a string) and `dep_edges` (id
pairs); it has no access to any artifact's commitments, so a formal
dependent and an informal dependent of a refuted premise are orphaned
by the exact same code path, with the exact same status.

## 4. R-g audit (R9, SPEC.md S8)

R-g: "no mechanism... may weight ranking, scheduling, or acceptance on a
conjecture's KIND... Formal backing may confer PROTECTION..., its absence
confers no disadvantage." This audit's job is to try to REFUTE
"protection-only, no penalty" — not assume it. Three sub-searches, per
R-g's own text ("scheduler ranking terms, pack rendering differences,
acceptance criteria").

### (a) Scheduler ranking terms

```
$ grep -n "execution_backed\|formally_backed" src/deepreason/scheduler/scheduler.py
(no output — exit 1, zero hits)
```
Neither guard FUNCTION is ever called from `scheduler.py`. Widening to
the underlying concept both guards test (an execution-oracle-evaluable
commitment) finds `_standing_recrit_pool`'s own inline re-derivation of
it instead of a call to either guard:

```
$ grep -n "execution_evals\|EXEC_PROGRAMS" src/deepreason/scheduler/scheduler.py
1161:        from deepreason.oracle import EXEC_PROGRAMS
1164:        execution_evals = {f"program:{p}" for p in EXEC_PROGRAMS}
1181:                and kappa.eval in execution_evals
```
(M6's `carries = any(...)` block sits at lines 1176-1184, using this
`execution_evals` set built at line 1164 — the same concept as
`execution_backed`, computed locally rather than by calling the shared
helper, but the same underlying kind-signal.)

```
$ grep -n "def rank(p):" -A 8 src/deepreason/scheduler/scheduler.py
1023:            def rank(p):
1024:                age = self._cycles - self._problem_worked.get(p.id, -1)
1025:                weight = 1.0 if not survivors_by_problem.get(p.id) else 0.3
1026:                return (
1027:                    -(age * weight),
1028:                    p.provenance.trigger != SpawnTrigger.SEED,
1029:                    p.id in reflexive,
1030:                    p.id,
1031:                )
```
`_select_problem`'s own ranking key (`docs/map/CON-scheduler-ranking.md`'s
"single tie-break authority") — age, whether the PROBLEM already has a
survivor, `SEED` trigger, reflexive-lineage membership, and problem id.
Zero kind terms; the key cannot even SEE a conjecture's commitments (it
ranks `Problem` objects, not artifacts). **Verdict: CONFIRMS** for
top-level problem selection.

`_standing_recrit_pool` DOES branch on kind (quoted in M6): execution-
backed artifacts are queued FIRST for leftover-capacity re-criticism.
Read against R-g's own wording — "may weight ranking, scheduling... on a
conjecture's KIND" — this IS a kind-conditional scheduling term, and this
audit reports it plainly rather than reasoning it away. Whether it is a
PENALTY: attempting to refute the informal-favoring reading —

- An informal target in the leftover-capacity pool gets criticized
  SOONER whenever the backed queue is short (fewer or no execution-backed
  survivors exist), and LATER (or not at all this cycle) whenever the
  backed queue is long — so a formal target's presence in the pool can
  only ever DELAY an informal target's re-criticism turn, never bring it
  forward. That is a scheduling effect ON INFORMAL TARGETS caused by the
  presence of formal ones, running in the direction of LESS scrutiny for
  informal, not more.
- For the formal targets themselves: being queued first for RE-criticism
  is not a bar to acceptance (they are already `Status.ACCEPTED`,
  `_standing_recrit_pool`'s own filter `harness.state.status.get(aid) !=
  Status.ACCEPTED: continue`), and an ordinary argumentative attack
  against them is guarded to register nothing while `execution_backed`
  holds (M9) — so the "attack" they receive first is mechanically
  toothless while their oracle passes. The docstring's own justification
  — catching a Goodhart survivor that "can hide nowhere else" — is a
  search for TRUE POSITIVES (a checker that is wrong in general despite
  passing frozen inputs), not an extra bar the target must clear beyond
  what its own commitments already require.
- **This audit could not construct a scenario where this ordering makes
  a formal conjecture LESS LIKELY to survive than an informal one would
  under the same content.** It changes WHEN a (mechanically-neutralized)
  attack attempt happens, never WHETHER a target can be admitted, rank
  for problem selection, or reach `Status.ACCEPTED`.

**Verdict: CONFIRMS "no penalty," with one genuine kind-conditional
scheduling term on the record** — `_standing_recrit_pool`'s ordering IS a
scheduling decision that reads kind, which is worth D2/D4 knowing about
explicitly (it is the one place today's system already "weights
scheduling... on a conjecture's KIND" in the letter of R-g, even though
this audit could not find it to weight OUTCOMES against formal
conjectures). This is the load-bearing finding this audit was asked to
surface plainly if found; it is reported here rather than silently
absorbed into a clean CONFIRMS.

### (b) Pack rendering differences

Already traced in full in M8: one template (`render_crit_pack`), no
`if`/`else` branch on kind anywhere in `llm/packs.py`.

```
$ grep -n "def render_crit_pack\|def render_batch_crit_pack\|def render_cx_retry_pack" src/deepreason/llm/packs.py
```
```
$ grep -c "is_formal\|target.kind\|\.kind ==" src/deepreason/llm/packs.py
0
```
No pack-rendering function branches on any "kind" attribute (none
exists to branch on — confirmed by the `ConjectureCandidate` field list
in M8). The one content difference — `_MACHINE_EVAL_NOTE` appearing
meaningfully only when `TARGET COMMITMENTS` is non-empty — is R-d's
"criticism arrives on the form matched to the kind" working as intended
(steering the critic away from re-litigating a machine-decided
question), not a demand placed on informal targets. **Verdict: CONFIRMS.**

### (c) Acceptance criteria

```
$ grep -rn "execution_backed\|formally_backed" src/deepreason/workflow/*.py src/deepreason/scheduler/*.py
(no output — exit 1, zero hits)
```
Neither `workflow/` nor `scheduler/` calls either guard at all — the v6
transactional work lifecycle's admission/acceptance machinery never
reads them (`_standing_recrit_pool`'s inline re-derivation, (a) above,
is the only place in either package that tests the same underlying
concept, and it is a scheduling term, not an acceptance one).

```
$ grep -n "def label0" -A 12 src/deepreason/adjudication/grounded.py
def label0(nodes: set[str], att: Iterable[tuple[str, str]]) -> dict[str, str]:
    """accepted if in G; refuted if attacked from G; else suspended."""
    att = set(att)
    g = grounded_extension(nodes, att)
    labels: dict[str, str] = {}
    for a in nodes:
        if a in g:
            labels[a] = "accepted"
        elif any((b, a) in att for b in g):
            labels[a] = "refuted"
        else:
            labels[a] = "suspended"
    return labels
```
The foundational acceptance computation (Pass 1, Dung grounded
extension) takes only `nodes: set[str]` (bare ids) and
`att: Iterable[tuple[str, str]]` (attack-edge id pairs) — it has no
parameter through which a commitment, an `eval` string, or any kind
signal could reach it even if someone wanted it to. An artifact with no
attacker is accepted VACUOUSLY, regardless of whether it carries zero
commitments (pure prose) or ten `program:`-eval'd ones. Pass 2
(`final_labels`, M12) is the same shape: `label0` (strings) and
`dep_edges` (id pairs) only. **Verdict: CONFIRMS** — acceptance is
structurally kind-blind two layers deep (Pass 1 and Pass 2 both), not
merely kind-blind by absence of an `if` statement that could be added
later without changing the function signature.

### R-g audit summary

Two of three sub-searches (pack rendering, acceptance criteria) found
NO kind-conditional term at all, at any layer checked. The third
(scheduler ranking/scheduling) found ONE genuine kind-conditional
scheduling term (`_standing_recrit_pool`'s queue ordering) that this
audit could not turn into a demonstrated penalty despite deliberately
trying — its effect runs, if anything, toward LESS re-criticism pressure
on informal targets when formal ones are present, and it touches
neither rank (problem selection), admission, nor acceptance. The
preplan's own expected finding — "protection-only asymmetry, no
penalty" — SURVIVES this audit, with the one scheduling-term exception
named explicitly so D2/D4 do not have to re-discover it.

## 5. Load-knob inventory (R10, SPEC.md S9)

Two families, structurally distinct: `Config` (`config.py`) knobs are
read LIVE from a mutable per-run-instance object the `Scheduler` holds a
reference to — never digested into the manifest (`INV-frozen-surfaces.md`:
"When a change needs a new per-run mode, put it on `Config`... never on
the manifest... `ARGUMENTATIVE_AUTHORITY` is a `Config` field"). Every
other family below (capability policies, `v6_policy.py` presets,
`CriticismPolicyV1`, scratch `AttentionPolicyV1`) is a field on
`RunManifest` or a manifest-embedded sub-model, hashed into the manifest
digest at mint time — a value in these families cannot change mid-run
without minting a different run identity.

```
$ sed -n '10,13p' src/deepreason/config.py
Knobs whose spec start value is "tune" default to ``None`` and must be set
before the phases that consume them.
"""
```
```
$ grep -n "class Config(BaseModel)" src/deepreason/config.py
247:class Config(BaseModel):
```
`Config` is instantiated once per run and passed by reference into
`Scheduler.__init__`; nothing re-reads it from a frozen digest — this is
the "read live" family for every row below marked Config.

| Knob | Location | Unit | Default | Mint-time vs live |
|---|---|---|---|---|
| `INTEGRATION_BUDGET_SHARE` | `config.py:263` | fraction of cycles | `0.30` | Live (`Config`) |
| `TRIAL_PARAPHRASE_N` | `config.py:268` | count | `2` | Live (`Config`) |
| `AUDIT_PERIOD` | `config.py:270` | cycles | `30` | Live (`Config`) |
| `USER_RULINGS_BUDGET` | `config.py:271` | count | `2` | Live (`Config`) |
| `HOLDOUT_SHARE` | `config.py:272` | fraction | `0.2` | Live (`Config`) |
| `XEXAM_SHARE` | `config.py:276` | fraction | `0.15` | Live (`Config`) |
| `RESEED_RATIO_MAX` | `config.py:288` | fraction | `0.3` | Live (`Config`) |
| `NEIGHBOURHOOD_N` | `config.py:299` | count (exemplars/pack) | `8` | Live (`Config`) |
| `CAPTURE_W` | `config.py:318` | count | `20` | Live (`Config`) |
| `CRIT_DEBT_CEILING` | `config.py:321` | fraction | `0.5` | Live (`Config`) |
| `RESEARCH_PERIOD` | `config.py:332` | cycles | `5` | Live (`Config`) |
| `RESEARCH_ATTEMPTS_MAX` | `config.py:356` | count | `5` | Live (`Config`) |
| `CX_RETRY_MAX` | `config.py:407` | count | `1` | Live (`Config`) |
| `FUZZ_N` | `config.py:418` | count | `64` | Live (`Config`) |
| `GEN_PROPOSE_PERIOD` | `config.py:424` | cycles | `5` | Live (`Config`) |
| `GEN_MAX` | `config.py:425` | count | `3` | Live (`Config`) |
| `PROP_PROPOSE_PERIOD` | `config.py:433` | cycles | `7` | Live (`Config`) |
| `PROP_MAX` | `config.py:434` | count | `3` | Live (`Config`) |
| `DISC_ATTEMPTS_MAX` | `config.py:441` | count | `3` | Live (`Config`) |
| `HV_CONTENT_MAX_CHARS` | `config.py:450` | chars | `8000` | Live (`Config`) |
| `CHUNK_MAX_CHARS` | `config.py:521` | chars | `4000` | Live (`Config`) |
| `PACK_TOKEN_BUDGET` | `config.py:528` | tokens | `2500` | Live (`Config`) |
| `RETRY_MAX` | `config.py:529` | count | `2` | Live (`Config`) |
| `ARG_CRIT_PER_CYCLE` | `config.py:358` | targets/cycle | `None` (uncapped) | Live (`Config`) |
| `CRIT_BATCH_K` | `config.py:363` | targets/call | `None` (1) | Live (`Config`) |
| `RECRIT_STANDING` | `config.py:413` | bool (feature gate) | `True` | Live (`Config`) |

```
$ grep -n "^class " src/deepreason/capabilities/policy.py
16:class _PolicyModel(BaseModel):
40:class SimulationInputBindingV1(_PolicyModel):
59:class SimulationCapabilityPolicyV1(_PolicyModel):
172:class FrozenEvidenceItemV1(_PolicyModel):
196:class FrozenEvidencePolicyV1(_PolicyModel):
250:class AttachedEvidencePolicyV1(_PolicyModel):
286:class FormalizationCapabilityPolicyV1(_PolicyModel):
304:class ResearchCapabilityPolicyV1(_PolicyModel):
380:class ConfigRefereePolicyV1(_PolicyModel):
417:class InquiryCapabilityPolicyV1(_PolicyModel):
```
```
$ grep -n "simulation_capability_policy: SimulationCapabilityPolicyV1" src/deepreason/run_manifest.py
1195:    simulation_capability_policy: SimulationCapabilityPolicyV1 | None = None
```
Confirms `SimulationCapabilityPolicyV1` is a `RunManifest` field — every
knob inside it is hashed into the manifest and therefore mint-time
frozen:

| Knob | Location | Unit | Default | Mint-time vs live |
|---|---|---|---|---|
| `maximum_simulation_requests` | `capabilities/policy.py:79` | requests/run | `0` | Mint-time (`RunManifest.simulation_capability_policy`) |
| `maximum_simulation_executions` | `capabilities/policy.py:80` | executions/run | `0` | Mint-time (manifest) |
| `maximum_proposals_per_turn` | `capabilities/policy.py:81` | proposals/turn | `0` | Mint-time (manifest) |
| `maximum_generated_code_bytes` | `capabilities/policy.py:82` | bytes | `0` | Mint-time (manifest) |
| `maximum_input_bytes` | `capabilities/policy.py:83` | bytes | `0` | Mint-time (manifest) |
| `maximum_output_bytes` | `capabilities/policy.py:84` | bytes | `0` | Mint-time (manifest) |
| `maximum_wall_ms` | `capabilities/policy.py:85` | milliseconds | `0` | Mint-time (manifest) |
| `maximum_memory_bytes` | `capabilities/policy.py:86` | bytes | `0` | Mint-time (manifest) |
| `maximum_steps` | `capabilities/policy.py:87` | steps | `0` | Mint-time (manifest) |
| `maximum_samples` | `capabilities/policy.py:88` | samples | `0` | Mint-time (manifest) |
| `maximum_follow_up_reasoning_turns` | `capabilities/policy.py:93` | turns/run | `0` | Mint-time (manifest) |
| `maximum_sources` (research) | `capabilities/policy.py:201` | sources/run | `0` | Mint-time (manifest) |
| `maximum_excerpt_bytes_per_source` | `capabilities/policy.py:202` | bytes | `0` | Mint-time (manifest) |
| `maximum_total_excerpt_bytes` | `capabilities/policy.py:203` | bytes | `0` | Mint-time (manifest) |
| `maximum_requests` (inquiry) | `capabilities/policy.py:320` | requests/run | `0` | Mint-time (manifest) |
| `cadence_cycles` | `capabilities/policy.py:394` | cycles | `0` | Mint-time (manifest) |
| `window_events` | `capabilities/policy.py:395` | events | `0` | Mint-time (manifest) |

```
$ grep -n "class CriticismPolicyV1" -A 8 src/deepreason/run_manifest.py
522:class CriticismPolicyV1(BaseModel):
...
531:    minimum_foreign_school_coverage: int = Field(ge=1, le=1_023)
533:    max_batch_size: int = Field(ge=1, le=256)
```

| Knob | Location | Unit | Default | Mint-time vs live |
|---|---|---|---|---|
| `minimum_foreign_school_coverage` | `run_manifest.py:531` | schools | none (required, 1-1023) | Mint-time (manifest, `frozen=True` model) |
| `max_batch_size` | `run_manifest.py:533` | targets/call | none (required, 1-256) | Mint-time (manifest, `frozen=True` model) |

```
$ grep -n "class AttentionPolicyV1" -A 20 src/deepreason/scratch/attention.py
33:class AttentionPolicyV1(ScratchRecord):
34:    """Immutable policy seam later compiled into RunManifest v3."""
39:    max_blocks_per_pack: int = Field(gt=0, le=1_000)
40:    max_guides_per_pack: int = Field(ge=0, le=100)
44:    coverage_slot_every_n_packs: int = Field(gt=0)
45:    exploratory_fraction: float = Field(ge=0.0, le=1.0)
46:    underexposed_fraction: float = Field(ge=0.0, le=1.0)
47:    dormant_after_events: int = Field(ge=0)
48:    similarity_top_k: int = Field(gt=0, le=10_000)
50:    guide_max_open_threads: int = Field(ge=0, le=256)
51:    guide_max_entry_points: int = Field(ge=0, le=256)
```
The class's own docstring states it: "Immutable policy seam later
compiled into RunManifest v3" — mint-time by the type's own design intent.

| Knob | Location | Unit | Default | Mint-time vs live |
|---|---|---|---|---|
| `max_blocks_per_pack` | `scratch/attention.py:39` | blocks/pack | none (required, 1-1000) | Mint-time (compiled into `RunManifest` v3) |
| `max_guides_per_pack` | `scratch/attention.py:40` | guides/pack | none (required, 0-100) | Mint-time (manifest) |
| `coverage_slot_every_n_packs` | `scratch/attention.py:44` | packs | none (required, >0) | Mint-time (manifest) |
| `exploratory_fraction` | `scratch/attention.py:45` | fraction | none (required, 0-1) | Mint-time (manifest) |
| `underexposed_fraction` | `scratch/attention.py:46` | fraction | none (required, 0-1) | Mint-time (manifest) |
| `dormant_after_events` | `scratch/attention.py:47` | events | none (required, >=0) | Mint-time (manifest) |
| `similarity_top_k` | `scratch/attention.py:48` | count | none (required, 1-10000) | Mint-time (manifest) |
| `guide_max_open_threads` | `scratch/attention.py:50` | threads | none (required, 0-256) | Mint-time (manifest) |
| `guide_max_entry_points` | `scratch/attention.py:51` | entry points | none (required, 0-256) | Mint-time (manifest) |

`v6_policy.py`'s "engaged" preset is a fixed COMPILATION of the manifest
fields above (`PUBLIC_SCHOOL_COUNT = 4`, `v6_policy.py:53`, and the "fixed
public 6-cycle/100k-token envelope" the module's own docstring names) —
not a separate knob family, a specific set of frozen VALUES for the
mint-time fields already tabled. No additional live-read knob lives in
this module.

**Summary for D4:** the Config family (26 knobs tabled) is where a
future load-dial mechanism would act WITHOUT minting a new run —
D4's own accept criterion ("a no-mix-specified run is byte-identical to
today") is easiest to satisfy here, since these are already read live
and already have no manifest-digest interaction. Every manifest-embedded
family (17 knobs tabled across capability policies, criticism policy, and
scratch attention) would require a NEW MANIFEST per mix — consistent
with D4's own "Frozen at mint time into the manifest (the rung-7
placement law: a continuation continues under the mix it was minted
with)" design note.

## 6. Historical encoding-failure evidence (R11, SPEC.md S10)

(filled in step 14)

## Summary (SPEC.md S16, filled in step 21)

(filled in step 21)
