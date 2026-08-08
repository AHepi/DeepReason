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
(no hits outside lambda_run.py's own definition file)
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

(filled in step 6)

## 3. Refutation semantics per kind (R8, SPEC.md S7)

(filled in step 8)

## 4. R-g audit (R9, SPEC.md S8)

(filled in step 10)

## 5. Load-knob inventory (R10, SPEC.md S9)

(filled in step 12)

## 6. Historical encoding-failure evidence (R11, SPEC.md S10)

(filled in step 14)

## Summary (SPEC.md S16, filled in step 21)

(filled in step 21)
