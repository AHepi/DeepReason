<!-- DR-SEAM-scheduler-x-rules -->
Verified-at: f9fcd1136
Verify: python tools/docs_verify.py
Owns: src/deepreason/scheduler/scheduler.py, src/deepreason/rules/conj.py, src/deepreason/rules/crit.py, src/deepreason/rules/spawn.py
Sides: DR-SUB-rules, DR-SUB-scheduler

# scheduler x rules

## The agreement

The scheduler decides *what is worked on, by whom, how often and how much*; the
rules decide *what that work means epistemically*. Concretely the scheduler
promises to hand a rule a registered problem id, an allocated school, a
`Config`, an adapter it is entitled to spend, and a guarantee that the per-cycle
ration has already been debited — and promises never to reach past the rule into
the record: it mints no problem, registers no warrant, runs no admission gate,
assigns no status, and writes no file. The rules promise in return that every
call is a self-contained move whose entire durable effect is handed to the
harness, that they will refuse work the scheduler had no right to schedule
(`conj` raises on an unregistered problem, a school-routed `conj` raises on a
lease that does not match its conditioning record), and that they will read
nothing about attention — no cycle count, no cadence, no cap. The division shows
up in `Config` itself: of the twenty-nine settings the scheduler reads and the
twelve the rules read, exactly one is shared. Batching is the sharpest case of
the split: the scheduler chooses `CRIT_BATCH_K` as a *call shape*, and the rule
is free to ignore it — a K=1 batch and a COMPACT profile both collapse back to
the single-target contract, because the call structure is not the epistemology.
The one thing crossing back the other way is identity, not authority: the
anti-relapse gate scopes a candidate's comparison domain by the scheduler's
`problem_family_key`, so a refuted approach cannot re-enter under a fresh
successor id (the term of art survives; the TRIGGER does not).

Nine files under `src/` mention both `deepreason.rules` and the scheduler; four
carry the agreement. Of the five rules modules that say "scheduler", only
`conj.py` actually imports it, and only inside a function body. The scheduler's
whole vocabulary of rules is fifteen names from seven modules — four at module
scope, the rest function-local so `rules/` stays importable without the run
loop. Adding a sixteenth is a seam change, and this check is what makes it one.
`check: python -c 'import ast; t = ast.parse(open("src/deepreason/scheduler/scheduler.py").read()); got = sorted({(n.module, a.name) for n in ast.walk(t) if isinstance(n, ast.ImportFrom) and n.module and n.module.startswith("deepreason.rules") for a in n.names}); want = [("deepreason.rules.act", "browser_evidence"), ("deepreason.rules.act", "needs_browser_run"), ("deepreason.rules.act", "run_browser_evidence"), ("deepreason.rules.conj", "conj"), ("deepreason.rules.crit", "QUARANTINE_TICK"), ("deepreason.rules.crit", "crit_argumentative_batch"), ("deepreason.rules.crit", "crit_fuzz"), ("deepreason.rules.crit", "crit_program"), ("deepreason.rules.experiment", "accepted_generators"), ("deepreason.rules.experiment", "active_properties"), ("deepreason.rules.experiment", "propose_generators"), ("deepreason.rules.experiment", "propose_properties"), ("deepreason.rules.spawn", "scan_spawns"), ("deepreason.rules.synth", "synthesize"), ("deepreason.rules.vision", "crit_vision")]; assert got == want, [x for x in got if x not in want] + [x for x in want if x not in got]' && test "$(grep -cE "^from deepreason\.rules" src/deepreason/scheduler/scheduler.py)" -eq 4 && test "$(for f in $(grep -rl "deepreason\.rules" --include=*.py src/deepreason); do grep -ql scheduler "$f" && echo x; done | wc -l)" -eq 9 && test "$(grep -rln scheduler --include=*.py src/deepreason/rules/ | wc -l)" -eq 5 && test "$(grep -rln "deepreason\.scheduler" --include=*.py src/deepreason/rules/ | wc -l)" -eq 1 && grep -q "    from deepreason.scheduler.scheduler import problem_family_key" src/deepreason/rules/conj.py && ! grep -qE "^(from|import) deepreason\.scheduler" src/deepreason/rules/conj.py`

The `Config` partition is the agreement in its most testable form. Cadence,
caps, focus and rotation are the scheduler's; pack size, retry counts and
thresholds are the rules'. `FUZZ_N` is the single shared name, and it is shared
because it is an on/off switch on both sides: the scheduler skips the sweep when
it is zero, `crit_fuzz` uses it as the enumeration bound. Both counts are
pinned exactly, not as floors: a new `Config` read on either side is a seam
change for the same reason a sixteenth rules import is, and a floor would have
let either side grow silently past the number written here.
`check: python -c 'import re, pathlib; cfg = lambda d: {n for p in pathlib.Path(d).rglob("*.py") for n in re.findall(r"config\.([A-Z_]+)", p.read_text())}; r = cfg("src/deepreason/rules"); s = cfg("src/deepreason/scheduler"); assert (len(r), len(s)) == (12, 32), (len(r), len(s)); assert r & s == {"FUZZ_N"}, sorted(r & s); from deepreason.config import Config; c = Config(); assert all(hasattr(c, n) for n in r | s)'`

## Where it is expressed

| Site | File | Symbol | What it enforces |
|---|---|---|---|
| Spawn scan | `scheduler/scheduler.py` | `scan_spawns(harness, config)` at the head of `step` | structural triggers are swept before selection, so a problem minted this cycle is eligible this cycle |
| Spawn rule | `rules/spawn.py` | `scan_spawns`, deterministic problem ids | rescans are idempotent and free; the scheduler may call it every cycle without bookkeeping |
| Problem selection | `scheduler/scheduler.py` | `_select_problem`, the `rank` tuple | age × solved-weight, then SEED, then promotion wound count, then premise-marked, then reflexive, then id — in both selection modes |
| Premise layer (attention only) | `scheduler/scheduler.py`, `premises.py` | `retired_problems` filters the pool, `premise_orphaned` adds one rank term, `premise_work_invited` records the standing invitation | the scheduler consults the premise layer and moves no label; the INVITATION itself is computed inside `rules/crit.py`, because `_arg_crit`'s call is keyword-free by the invariant below |
| Reflexive ration | `scheduler/scheduler.py` | `reflexive_problems` + `INTEGRATION_BUDGET_SHARE` | meta-work draws one capped pool and follows lineage, not just the trigger |
| School allocation | `capture/schools.py` | `allocate` (single caller: the scheduler) | which schools compete on this problem; ownership by provenance with a cross-examination floor (`DR-CON-schools`) |
| School conditioning | `scheduler/scheduler.py` | `_school_dict` → `school=` | the rule receives a plain dict (stance text, weight, crossover), never the scheduler's school registry |
| Route lease | `scheduler/scheduler.py` | `school_leases` resolved for the whole batch before dispatch | one bad school assignment leaves no partial spend |
| Conjecture gate | `rules/conj.py` | `conj(harness, problem_id, ...)`, `"Conj is gated on a registered problem"` | the rule re-reads the problem from state; the scheduler passes an id, not an object |
| Lease agreement | `rules/conj.py` | `"execution school must match the semantic school conditioning record"` | the rule refuses a lease/school pair the scheduler mismatched |
| Capability follow-up | `scheduler/scheduler.py` | `_simulation_capability_step`, `_v6_simulation_result_follow_up` → `conj(..., _capability_result_context=...)` | a simulation result re-enters conjecture through the same rule, with the package refs the scheduler resolved |
| Criticism ladder | `scheduler/scheduler.py` | `_criticize`: `crit_program` → `crit_fuzz` → `run_hv_floor` → `run_trial` | cheapest first; a target felled for free never reaches a provider call |
| Criticism ration | `scheduler/scheduler.py` | `_arg_crit`, `_arg_crit_this_cycle`, `ARG_CRIT_PER_CYCLE`, `CRIT_BATCH_K`, `RECRIT_STANDING` | targets are counted and debited before the rule is called; leftovers sweep the standing pool |
| Batch collapse | `rules/crit.py` | `crit_argumentative_batch` K=1 / `ModelProfile.COMPACT` branches | the rule may un-batch; the scheduler cannot force a batch |
| Prose authority | `rules/crit.py` | `_resolve_authority` | local path reads `Config`; a manifest-bound call must carry the frozen policy value explicitly |
| Fuzz sweep | `scheduler/scheduler.py`, `rules/crit.py` | `QUARANTINE_TICK` snapshot around `crit_fuzz` | an unavailable oracle is *pending*, never clean — the scheduler must not cache a verdict the rule did not reach |
| Design cadence | `scheduler/scheduler.py` | `_experiment_step`, `_property_step`; `GEN_PROPOSE_PERIOD`, `GEN_MAX`, `PROP_PROPOSE_PERIOD`, `PROP_MAX` | one design call per due cycle; `propose_generators` / `propose_properties` know none of it |
| Exogenous caps | `scheduler/scheduler.py` | `_browser_step`, `_vision_step`; `BROWSER_PER_CYCLE`, `VISION_CRIT_PER_CYCLE` | `act.run_browser_evidence` and `vision.crit_vision` are rationed by the caller, once per (candidate, commitment) |
| Domain identity | `rules/conj.py`, `scheduler/scheduler.py` | `root_problem_family` → `problem_family_key` | the only rules→scheduler edge; anti-relapse domains key on the provenance root, not a successor id |
| Diagnostics channel | `scheduler/scheduler.py`, `rules/conj.py` | `self.diagnostics` passed as `conj`'s fifth positional | in-memory, non-epistemic, returned by `report()`; it is not the record |

`conj` takes an id and re-gates on the registry; `synthesize` takes the problem
object because it reads provenance endpoints directly. `step` reaches `conj`
exactly once.
`check: python -c 'import ast, inspect, textwrap; from deepreason.rules.conj import conj; from deepreason.rules.synth import synthesize; from deepreason.scheduler.scheduler import Scheduler as S; assert list(inspect.signature(conj).parameters)[1] == "problem_id"; assert list(inspect.signature(synthesize).parameters)[1] == "problem"; src = inspect.getsource(conj); assert "Conj is gated on a registered problem" in src and "execution school must match the semantic school conditioning record" in src; t = ast.parse(textwrap.dedent(inspect.getsource(S.step))); calls = [n for n in ast.walk(t) if isinstance(n, ast.Call) and getattr(n.func, "id", "") == "conj"]; assert len(calls) == 1; assert [ast.unparse(a) for a in calls[0].args] == ["harness", "problem.id", "self.adapter", "config", "self.diagnostics"]; syn = [n for n in ast.walk(t) if isinstance(n, ast.Call) and getattr(n.func, "id", "") == "synthesize"]; assert len(syn) == 1 and ast.unparse(syn[0].args[1]) == "problem"'`

The rank tuple is the seam's most expensive single line — see Traps. It is
parsed here, not grepped, so a reordering cannot pass by coincidence, and the
non-liveness branch carries the same terms.

**Rung 7 added the wound-count term** (D-1 answered A: the incumbent's
promotion problem stays on the frontier, ranked by wound count, attention
only). It sits AFTER the SEED term in both keys, and that position is the
guarantee rather than a detail: a background carrying forty wounds must not
outrank the operator's own question. The pin below asserts the ORDER, so
moving the term earlier fails here rather than in a live run's budget.
`check: python -c 'import ast, inspect, textwrap; from deepreason.scheduler.scheduler import Scheduler as S; t = ast.parse(textwrap.dedent(inspect.getsource(S._select_problem))); rank = [n for n in ast.walk(t) if isinstance(n, ast.FunctionDef) and n.name == "rank"][0]; ret = [n for n in ast.walk(rank) if isinstance(n, ast.Return)][0]; assert [ast.unparse(e) for e in ret.value.elts] == ["-(age * weight)", "p.provenance.trigger != SpawnTrigger.SEED", "-promotion_wounds.get(p.id, 0)", "p.id in orphaned", "p.id in reflexive", "p.id"], [ast.unparse(e) for e in ret.value.elts]; lam = [n for n in ast.walk(t) if isinstance(n, ast.Lambda) and isinstance(n.body, ast.Tuple)][0]; assert [ast.unparse(e) for e in lam.body.elts] == ["p.provenance.trigger != SpawnTrigger.SEED", "-promotion_wounds.get(p.id, 0)", "p.id in orphaned", "p.id in reflexive"]; src = inspect.getsource(S._select_problem); assert "ProvenanceRole.IMPORT" in src and "survivors_by_problem" in src' && python -m pytest tests/test_controller.py::test_operator_question_outranks_spawns_at_cycle_zero tests/test_scheduler.py::test_focus_family_restricts_selection tests/test_reflexive_discipline.py::test_reflexive_budget_follows_lineage -q`

Whether a rule entry takes `adapter` is exactly whether the scheduler must
ration provider spend for it. `run_browser_evidence` is the informative
exception: it takes a `browser` backend rather than an adapter and is still
capped, because its cost is real-world rather than token.
`check: python -c 'import inspect; from deepreason.rules import spawn, crit, act, conj, synth, experiment, vision; free = (spawn.scan_spawns, crit.crit_program, crit.crit_fuzz, act.needs_browser_run); paid = (conj.conj, crit.crit_argumentative_batch, synth.synthesize, experiment.propose_generators, experiment.propose_properties, vision.crit_vision); assert not [f.__name__ for f in free if "adapter" in inspect.signature(f).parameters]; assert not [f.__name__ for f in paid if "adapter" not in inspect.signature(f).parameters]; p = inspect.signature(act.run_browser_evidence).parameters; assert "adapter" not in p and "browser" in p'`

Within `_criticize` the ladder is ordered by cost, and argumentative criticism
runs only after every admitted candidate has been through it.
`check: python -c 'import inspect; from deepreason.scheduler.scheduler import Scheduler as S; c = inspect.getsource(S._criticize); assert c.index("crit_program(harness, artifact.id)") < c.index("crit_fuzz(harness, artifact.id, config)") < c.index("run_hv_floor(") < c.index("run_trial("); assert c.index("if harness.state.status.get(artifact.id) == Status.ACCEPTED:") < c.index("crit_fuzz(harness, artifact.id, config)"); assert "continue  # budget triage: already felled" in c; g = inspect.getsource(S.step); assert g.index("self._criticize(artifact)") < g.index("self._arg_crit([a.id for a in admitted])")'`

The ration counts TARGETS, not calls — batching buys a cheaper call, never more
budget — and a K=1 batch is byte-for-byte the single-target contract.
`check: python -c 'import inspect; from deepreason.rules.crit import crit_argumentative_batch as b; s = inspect.getsource(b); assert "if len(target_ids) == 1 and not active_v6:" in s; assert s.index("ModelProfile.COMPACT") < s.index("def primary_pack_factory"); assert "structure is not the epistemology" in s' && ! grep -q "crit_argumentative(" src/deepreason/scheduler/scheduler.py && grep -q "^def crit_argumentative(" src/deepreason/rules/crit.py && grep -q "crit_argumentative_batch(" src/deepreason/scheduler/scheduler.py && python -m pytest tests/test_crit_batch.py::test_arg_crit_cap_counts_targets_not_calls tests/test_crit_batch.py::test_scheduler_batches_survivors_into_one_call tests/test_crit_batch.py::test_single_target_delegates_to_single_contract tests/test_budget.py::test_arg_crit_per_cycle_cap -q`

Simulation results re-enter through the *same* rule, carrying the private
`_capability_result_*` refs that only the scheduler may supply; research has no
such path at all.
`check: python -c 'import ast, inspect, textwrap; from deepreason.scheduler.scheduler import Scheduler as S; calls = lambda m: [n for n in ast.walk(ast.parse(textwrap.dedent(inspect.getsource(getattr(S, m))))) if isinstance(n, ast.Call) and getattr(n.func, "id", "") == "conj"]; a = calls("_simulation_capability_step"); b = calls("_v6_simulation_result_follow_up"); c = calls("step"); assert (len(a), len(b), len(c)) == (1, 1, 1); assert "_capability_result_context" in {k.arg for k in a[0].keywords}; assert {"_capability_result_context", "_capability_result_package_ref", "_capability_result_context_ref"} <= {k.arg for k in b[0].keywords}; assert not [k for k in c[0].keywords if str(k.arg).startswith("_capability")]; g = inspect.getsource(S.step); assert g.index("if self._simulation_capability_step():") < g.index("scan_spawns(harness, config)"); assert "deepreason.rules" not in inspect.getsource(S._research_step)' && test "$(grep -rl "_capability_result_context" --include=*.py src/deepreason | sort | tr "\n" " ")" = "src/deepreason/rules/conj.py src/deepreason/scheduler/scheduler.py "`

## What is deliberately absent

**The scheduler makes no epistemic move of its own.** It never calls `spawn`
(only the idempotent `scan_spawns`), never `register_fail_warrant` and never
names `WarrantType`, never runs the anti-relapse gate, never calls
`try_counterexample`, never opens a file, and never assigns a status. Every one
of those symbols exists and is exercised inside `rules/`. This is why an
attention bug in DeepReason cannot become an epistemic one, and it is the first
thing a "small convenience" breaks: minting a problem inline rather than letting
`scan_spawns` find it next cycle is the intuitive shortcut, and it produces a
problem with no structural trigger and no provenance that any rescan can
reproduce.
`check: grep -qx "        scan_spawns(harness, config)" src/deepreason/scheduler/scheduler.py && test "$(ls src/deepreason/scheduler/*.py | wc -l)" -ge 2 && ! grep -qE "\bspawn\(|register_fail_warrant|WarrantType|anti_relapse|try_counterexample|relapse_domain|_RELAPSE_LOG" src/deepreason/scheduler/scheduler.py && ! grep -rqE "path\.open|write_text|\bopen\(" --include=*.py src/deepreason/scheduler/ && grep -q "^def spawn(" src/deepreason/rules/spawn.py && grep -q "        problem = spawn(harness, \*args, \*\*kwargs)" src/deepreason/rules/spawn.py && grep -q "^def register_fail_warrant(" src/deepreason/rules/warrants.py && grep -q "register_fail_warrant(" src/deepreason/rules/act.py && grep -q "^def try_counterexample(" src/deepreason/rules/crit.py && grep -q "try_counterexample(" src/deepreason/rules/crit.py && grep -q "_RELAPSE_LOG = \"relapse.log.jsonl\"" src/deepreason/rules/guards/anti_relapse.py && grep -q "anti_relapse" src/deepreason/rules/conj.py`

**The scheduler never chooses a prose authority.** On the local path it passes
`crit_argumentative_batch` no authority at all and the rule reads the validated
`Config` policy; on the manifest-bound path it forwards `policy.authority`
verbatim, and the rule *refuses* to fall back to `Config` for such a call. So
there is no third state in which attention decides whether a sustained prose
case changes a status — `ARGUMENTATIVE_AUTHORITY` does not appear in the
scheduler at all (`DR-CON-authority`, `DR-INV-frozen-surfaces`).
`check: python -c 'import ast, inspect, textwrap; import deepreason.rules.crit as C; from deepreason.authority import argumentative_authority_mode as M; from deepreason.scheduler.scheduler import Scheduler as S; f = lambda m: [n for n in ast.walk(ast.parse(textwrap.dedent(inspect.getsource(getattr(S, m))))) if isinstance(n, ast.Call) and getattr(n.func, "id", "") == "crit_argumentative_batch"]; a = f("_arg_crit"); b = f("_foreign_arg_crit"); assert len(a) == 1 and not a[0].keywords, [k.arg for k in a[0].keywords]; assert [ast.unparse(k.value) for k in b[0].keywords if k.arg == "argumentative_authority"] == ["policy.authority"]; r = inspect.getsource(C._resolve_authority); assert "return _authority(config)" in r and "manifest-bound criticism requires explicit argumentative authority" in r; assert "ARGUMENTATIVE_AUTHORITY" in inspect.getsource(M)' && ! grep -q "ARGUMENTATIVE_AUTHORITY" src/deepreason/scheduler/scheduler.py`

**No attention state crosses into `rules/`.** The per-cycle counters and caches
that make rationing work — `_arg_crit_this_cycle`, `_advisory_trials_this_cycle`,
`_problem_worked`, `_fuzz_clean`, `_recrit_cursor`, `_disc_attempts`,
`_vision_done` — appear nowhere in the rules package, and neither does any
cadence `Config` name. A rule that could see the cycle counter could ration
itself, and then two places would be deciding one budget. The single mutable
object shared across the seam is `crit.QUARANTINE_TICK`: the scheduler snapshots
it around `crit_fuzz` so an unavailable oracle cannot be mistaken for a clean
verdict. It is derived from deterministic control flow, so it is replay-safe.
`check: python -c 'import inspect; from deepreason.scheduler.scheduler import Scheduler as S; import deepreason.rules.crit as C; f = inspect.getsource(S._fuzz_sweep); assert f.index("from deepreason.rules.crit import QUARANTINE_TICK") < f.index("tick = QUARANTINE_TICK[0]") < f.index("crit_fuzz(harness, aid, config)") < f.index("QUARANTINE_TICK[0] == tick"); assert list(inspect.signature(C.crit_fuzz).parameters) == ["harness", "target_id", "config"]' && grep -q "^QUARANTINE_TICK = \[0\]" src/deepreason/rules/crit.py && grep -q "QUARANTINE_TICK\[0\] += 1" src/deepreason/rules/crit.py && for s in _arg_crit_this_cycle _advisory_trials_this_cycle _problem_worked _fuzz_clean _recrit_cursor _disc_attempts _vision_done; do grep -q "self\.$s" src/deepreason/scheduler/scheduler.py || exit 1; done && ! grep -rqE "_arg_crit_this_cycle|_advisory_trials_this_cycle|_problem_worked|_fuzz_clean|_recrit_cursor|_disc_attempts|_vision_done" --include=*.py src/deepreason/rules/`

**Selecting a problem does not imply calling a rule.** Two whole trigger classes
never reach `rules/` at all. A `DISCRIMINATION` problem is resolved comparatively
in `informal/trial.py` — a pairwise ruling, not more conjectures — and the cycle
returns before school allocation. A `RESEARCH` problem is filtered out of the
candidate set entirely, because research is worked by backends. Reading "the
scheduler selected P and then conjectured" as universal is how a reader
misdiagnoses a cycle that spent tokens on a judge. The one rule that runs
unconditionally is `scan_spawns`, ahead of selection: it takes no adapter, so
the scheduler can afford to sweep every structural trigger every cycle.
`check: python -c 'import inspect; from deepreason.scheduler.scheduler import Scheduler as S; from deepreason.rules.spawn import scan_spawns; g = inspect.getsource(S.step); seg = g[g.index("problem.provenance.trigger == SpawnTrigger.DISCRIMINATION"):g.index("assigned = schools")]; assert "pairwise_discriminate(" in seg and "conj(" not in seg and "synthesize(" not in seg; assert seg.rstrip().endswith("return"); assert "p.provenance.trigger != SpawnTrigger.RESEARCH" in inspect.getsource(S._select_problem); assert g.index("scan_spawns(harness, config)") < g.index("problem = self._select_problem()"); assert list(inspect.signature(scan_spawns).parameters) == ["harness", "config"]' && grep -q "^def pairwise_discriminate(" src/deepreason/informal/trial.py && ! grep -rq "pairwise_discriminate" --include=*.py src/deepreason/rules/ && python -m pytest tests/test_scheduler.py::test_multi_cycle_spawns_and_persistence -q`

**Deterministic criticism is deliberately unrationed.** `crit_program` and
`crit_fuzz` cost sandbox steps, not tokens, so `_fuzz_sweep` runs every cycle
over every standing candidate whose clean bit is unset, and the standing
argumentative sweep runs the fuzz pass *first* so a free refutation saves the
call. Making fuzz reachable only from leftover arg-crit slots is the symmetric
error, and it was a recorded defect: a token-economy constraint imposed on
criticism that spends no tokens. The mechanism is asserted structurally as well
as behaviourally: the outcome tests alone survive both a dead `_fuzz_sweep` and
a standing sweep that skips its free pass, because the other arm still fells the
trap (mutation-audited at `9fa394d9`).
`check: python -c 'import inspect; from deepreason.scheduler.scheduler import Scheduler as S; assert "\n        self._fuzz_sweep()" in inspect.getsource(S.step); f = inspect.getsource(S._fuzz_sweep); assert "config.ARG_CRIT_PER_CYCLE" not in f and "_arg_crit_this_cycle" not in f; assert "        if config.FUZZ_N <= 0:\n            return\n" in f; assert f.index("if aid in self._fuzz_clean:") < f.index("crit_fuzz(harness, aid, config)"); a = inspect.getsource(S._arg_crit); assert "_fuzz_sweep" not in a; assert "                    if aid not in self._fuzz_clean:\n                        crit_fuzz(harness, aid, config)\n" in a; i = a.index("if config.RECRIT_STANDING:"); assert a.index("crit_fuzz(harness, aid, config)", i) < a.index("eligible.append(aid)", i) < a.index("self._arg_crit_this_cycle += 1", i)' && python -m pytest tests/test_properties.py::test_scheduler_conjectures_ground_truth_and_kills_the_trap tests/test_experiment.py::test_fuzz_sweep_is_not_rationed_behind_llm_slots tests/test_crit_batch.py::test_standing_goodhart_trap_is_fuzz_refuted_in_the_sweep tests/test_crit_batch.py::test_standing_survivor_swept_into_leftover_slots tests/test_properties.py::test_standing_recrit_pool_includes_active_properties -q`

**`rules/` does not import the scheduler, with exactly one exception, and it is
about identity rather than control.** `conj.root_problem_family` calls
`scheduler.problem_family_key` from inside a function body — module scope would
be an import cycle — to key anti-relapse domains on the provenance root. Four
other rules modules mention the scheduler only in comments; the check in "The
agreement" is what keeps that true.
`check: grep -q "    family = root_problem_family(harness.state, problem.id)" src/deepreason/rules/conj.py && grep -q "^def problem_family_key(state, problem_id: str) -> str:" src/deepreason/scheduler/scheduler.py && python -m pytest tests/test_guards.py::test_successor_family_scope tests/test_runtime_workload_integration.py::test_scheduler_owns_lineage_and_stable_code_relapse_domain -q`

## How to change it

The order is forced by which side can refuse. The rule can refuse work the
scheduler had no right to schedule; the scheduler cannot refuse a move the rule
already committed. So build the refusal first.

1. **Read `DR-INV-frozen-surfaces` first.** A new per-run knob goes on `Config`,
   never on the manifest — a manifest field moves every qualification subject
   digest. Then decide which side of the `Config` partition it belongs to: a
   cadence/cap name that `rules/` reads is a design error, not a shortcut, and
   the partition check above will say so.
2. **Add the rule entry, with its own gate, before the scheduler call site.**
   A rule that trusts its caller is a rule that cannot be tested against a fake
   harness. `conj`'s `KeyError` on an unregistered problem and its
   lease/school mismatch `ValueError` are the shape to copy.
3. **Ration at the call site, not in the rule.** Add the counter and the
   `Config` cap to the scheduler, debit before the call, and put the phase in
   the tail of `step()` in cost order. If the entry takes an `adapter`, it needs
   a per-cycle cap; if it only takes `harness` and `config`, do not give it one.
4. **Decide the v6 answer at the same time.** Under RunManifest v6 a phase that
   touches a provider must either carry a real transaction inside the rule or be
   routed through `_defer_untransactional_v6_phase` at its call site — the
   adapter's global guard fails the whole root on an unbound dispatch
   (`DR-SEAM-scheduler-x-workflow`).
5. **If the rule needs problem identity, take `problem_family_key`, do not
   re-derive it.** Two walks of the provenance graph that disagree give the
   anti-relapse gate two domains for one family, and a refuted approach re-enters
   under the second one.
6. **Update this document's site table in the same commit.** The import-set
   check will fail on a new `deepreason.rules` import in the scheduler until you
   do, which is deliberate.

What breaks first, in the order you will see it: the import-set and `Config`
partition checks here (immediately, from `python tools/docs_verify.py`); then
`conj`'s own `KeyError` / `ValueError` if the scheduler hands it something
inconsistent; then `tests/test_crit_batch.py::test_arg_crit_cap_counts_targets_
not_calls` if a ration moved into a rule; then, most expensively,
`test_operator_question_outranks_spawns_at_cycle_zero` — because by the time
selection is wrong, a live run has already spent its budget in the wrong place.

The tests that catch you, cheapest first: `tests/test_controller.py` and
`tests/test_scheduler.py` (selection and focus, sub-second),
`tests/test_crit_batch.py` (rationing and batching), `tests/test_guards.py`
(domain scoping), `tests/test_budget.py`, `tests/test_reflexive_discipline.py`,
`tests/test_experiment.py` and `tests/test_properties.py` (unrationed
criticism), then `tests/test_v6_scheduler_model_phase_deferral.py` for the
deferral arm.

## Traps

- **Cycle 0 fell to the bare id tie-break, and "solved" counted bookkeeping.**
  In `selfstudy run-9175f0ec` every problem was never-worked at cycle 0, so rank
  fell through to `p.id` — and an attach-spawned `conn:0e26d6be…` sorts before
  `question-98a0e3a7…`. Worse, evidence admission had already auto-accepted
  import-role records ADDRESSING the question, so it scored "solved" at the 0.3
  aging weight before a single provider call. The run burned its whole 200k
  budget inside the connection problem and the operator's question terminated
  `budget_denied` with zero calls. Two rules now hold in BOTH selection modes:
  import-role artifacts never count as survivors, and `SpawnTrigger.SEED` wins
  rank ties outright. Deleting the SEED term from the rank tuple still leaves a
  tree that imports, runs, and passes the rest of the suite; only
  `test_operator_question_outranks_spawns_at_cycle_zero` notices (verified by
  mutation at `546544b5`). Both halves are checked under "Where it is
  expressed".
- **Accepted-by-neglect: an artifact criticized only in the cycle it was
  admitted.** A buggy conjectured checker survived 80+ events unvisited
  (intervals/boot postmortem) because `_arg_crit` only ever saw `admitted_ids`.
  Leftover capacity now sweeps a standing pool round-robin. The seam detail that
  makes this safe is ordering, not budget: the sweep runs `crit_fuzz` on each
  standing target before spending the call, so a Goodhart survivor is refuted for
  free. Checked under "What is deliberately absent".
- **A successor id is a fresh attention object, and using it as an epistemic key
  reopened refuted ground.** `root_problem_family` exists because anti-relapse
  domains keyed on `succ:<id>` let a refuted approach re-enter unchanged on the
  next generation. The fix is the seam's one back-edge — which means the
  scheduler's `problem_family_key` is load-bearing for an epistemic guard even
  though the scheduler itself has no epistemic authority. Changing that walk is
  not an attention change; its check is under "What is deliberately absent".
- **Reading a rule's docstring as the whole contract.** Five rules modules say
  "scheduler" and only one imports it; the other four are describing an
  obligation their caller carries, not one they enforce. `act.py`'s "the
  scheduler's per-cycle budget counts real runs" is a note about
  `BROWSER_PER_CYCLE`, which `act.py` cannot see and does not check. Grepping for
  the word finds five files and tells you nothing about which four are inert.
`check: test "$(grep -rln scheduler --include=*.py src/deepreason/rules/ | wc -l)" -eq 5 && grep -q "scheduler.s per-cycle budget counts real runs" src/deepreason/rules/act.py && ! grep -q "PER_CYCLE" src/deepreason/rules/act.py`
- **Under v6 the local criticism ladder is empty, and that is not a bug.** With
  a manifest `criticism_policy`, `_arg_crit` delegates the whole phase to
  `_foreign_arg_crit`; without one, a v6 manifest used to make each target
  per-target deferral debt instead of a call — FIXED 2026-08-10
  (adjudication-judge-seats-optins tranche, S13i): `crit_argumentative_batch`
  now self-detects a v6-bound adapter and dispatches live even with no
  `critic_school_id`, so `_arg_crit`'s own call to it stays keyword-free
  (this seam's own invariant, below) while the phase never defers. Recorded
  in full in `DR-SEAM-scheduler-x-workflow`.
`check: python -m pytest tests/test_v6_scheduler_model_phase_deferral.py::test_legacy_argumentative_criticism_dispatches_under_v6 -q`
