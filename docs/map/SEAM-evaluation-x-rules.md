<!-- DR-SEAM-evaluation-x-rules -->
Verified-at: 6721010d
Verify: python tools/docs_verify.py
Owns: src/deepreason/rules/warrants.py, src/deepreason/measures/reach.py, src/deepreason/programs.py, src/deepreason/informal/trial.py
Sides: DR-SUB-evaluation, DR-SUB-rules

# evaluation x rules

## The agreement

Evaluation answers exactly one question for the rules — "can a machine settle
this commitment against these bytes, and what does it say?" — through
`programs.evaluable` and `programs.evaluate`, and it refuses `rubric:` with
`NotEvaluable` so no rule can accidentally program-decide a claim the trial
protocol owns. The rules promise in return that a verdict becomes an epistemic
move only through `rules/warrants.py::register_fail_warrant`, only from a
`fail`: an `overrun` or a sandbox abort is *pending*, never clean and never a
refutation. Beyond verdicts, evaluation lends the rules two SETS rather than two
functions — `oracle.EXEC_PROGRAMS` ("this verdict came from RUNNING the
candidate") and `measures/reach.py::_STRUCTURAL_PROGRAMS` ("passing this proves
only well-formedness") — and `rules/warrants.py` compiles them into the two
predicates that decide what prose may touch: `execution_backed` (narrow) and
`formally_backed` (wide). Nothing else in `rules/` reads either set, and both
reads are function-local to the predicate that needs them. So the formal /
informal line is not a type on an artifact and not a field on a commitment: it
is set membership, recomputed from content on every call, with the sets on the
evaluation side and the predicates on the rules side. Moving one program name
between those two sets silently changes which targets prose may refute and which
criteria can ground reach, without touching either predicate. The dependency
arrow runs both ways on purpose — rules read evaluation's classification, and
evaluation calls back into `rules/warrants.py` to package any fail it produces —
which is why there is exactly one warrant constructor in the tree and evaluation
never has to know what a warrant means. D2 rev 2 (Amendment 2, R43) added a
third import to `formally_backed` specifically: `rules/relatedness.py` (a
same-package, rules-side sibling, not a new evaluation-side dependency) for
the one per-commitment check that can strip a `candidate_checker`
commitment's protection on a sustained relatedness challenge — see
`DR-CON-conjecture-kinds`'s own section on this.

Rung D added a FOURTH in-function import, to `register_fail_warrant` rather than
to either predicate: `deepreason.ontology.artifact.RefRole`, used only when a
caller passes `manifest_ref` (`DR-CON-proof-debt-and-localization`). It is
in-function for the reason the check below pins — this module's TOP-LEVEL
imports stay `{deepreason.ontology}` exactly, so the one shared warrant
constructor never grows a dependency web that every mint site then inherits.
The check catches a module-level regression because it asserts the top-level
set, not merely the presence of the name.
`check: python -c "import ast,pathlib; t=ast.parse(pathlib.Path('src/deepreason/rules/warrants.py').read_text()); f={n.name:{i.module for i in ast.walk(n) if isinstance(i,ast.ImportFrom)} for n in ast.walk(t) if isinstance(n,ast.FunctionDef)}; assert f['execution_backed']=={'deepreason','deepreason.oracle'}; assert f['formally_backed']=={'deepreason','deepreason.measures.reach','deepreason.oracle','deepreason.rules.relatedness'}; assert {i.module for i in t.body if isinstance(i,ast.ImportFrom)}=={'deepreason.ontology'}" && test "$(grep -rl "EXEC_PROGRAMS\|_STRUCTURAL_PROGRAMS" --include=*.py src/deepreason/rules | wc -l)" -eq 1 && python -c "from deepreason.ontology import Commitment; assert set(Commitment.model_fields)=={'id','eval','budget','observation_valued'}"`

`formally_backed` is a superset of `execution_backed` **by construction, not by
convention**: the two sets are disjoint, every `EXEC_PROGRAMS` member is
substantive, and no `_STRUCTURAL_PROGRAMS` member is. Both predicates also carry
the all-currently-pass clause, so a formal claim that is already refuted
mechanically buys no protection from prose.
`check: python -c "from deepreason.oracle import EXEC_PROGRAMS; from deepreason.measures.reach import _STRUCTURAL_PROGRAMS, _substantive; from deepreason.ontology import Commitment; assert EXEC_PROGRAMS and _STRUCTURAL_PROGRAMS; assert EXEC_PROGRAMS.isdisjoint(_STRUCTURAL_PROGRAMS); assert all(_substantive(Commitment(id='k', eval='program:'+p)) for p in EXEC_PROGRAMS); assert not any(_substantive(Commitment(id='k', eval='program:'+p)) for p in _STRUCTURAL_PROGRAMS)"`

`evaluable` is where the informal side begins, and it has two deliberate
refusals: `rubric:`, which belongs to the trial, and `hv_floor`, which is left
unregistered so an HV battery cannot contain itself.
`check: python -c "from deepreason import programs; from deepreason.ontology import Commitment; from deepreason.measures.hv import hv_floor_commitment, is_hv_floor; from deepreason.config import Config; k=hv_floor_commitment(Config()); assert is_hv_floor(k) and programs.evaluable(k) is False; assert 'hv_floor' not in programs.PROGRAMS and 'hv_floor' not in programs.BLOB_PROGRAMS; assert programs.evaluable(Commitment(id='k', eval='rubric:s')) is False; assert programs.evaluable(Commitment(id='k', eval='predicate:True')) is True; assert programs.evaluable(Commitment(id='k', eval='program:json-wf')) is True"`

## Where it is expressed

| Site | File | Symbol | What it enforces |
|---|---|---|---|
| Decidability gate | `programs.py` | `evaluable`, `evaluate`, `NotEvaluable` | one route from a commitment to a verdict; `rubric:` is refused, not guessed |
| "Came from reality" set | `oracle.py` | `EXEC_PROGRAMS` | which passing verdicts a preference or a prose case may not override |
| "Proves nothing" set | `measures/reach.py` | `_STRUCTURAL_PROGRAMS`, `_substantive` | evaluability is not backing; the one predicate reach and prose-immunity share |
| Narrow guard | `rules/warrants.py` | `execution_backed` | ≥1 exec-oracle commitment carried, ALL of them currently passing |
| Wide guard | `rules/warrants.py` | `formally_backed` | ≥1 evaluable AND substantive commitment, ALL of them currently passing |
| The one warrant constructor | `rules/warrants.py` | `register_fail_warrant`, `verdict_on_record` | ν + `w:<κ>:<target>` + critic, one (κ, target) fail verdict on the graph at a time |
| Mechanical criticism | `rules/crit.py` | `crit_program` | skip the not-evaluable, quarantine the aborted, mint only on `FAIL` |
| Prose RECORDING guard | `rules/crit.py` | `crit_argumentative`, `crit_argumentative_batch` | the NARROW guard: an execution-backed target still gets `scrutiny` / `arg-crit-overridden-by-execution` |
| Prose STATUS guard | `informal/trial.py` | `_argument_trial_steps`, decline `"execution-backed"` | the WIDE guard, at the only point prose can mint a warrant |
| Preference guard | `informal/trial.py` | `pairwise_discriminate`, `execution_backed(harness, loser)` | a §10.2 preference never unseats a candidate that runs |
| Visual criticism guard | `rules/vision.py` | `crit_vision` | the narrow guard again: a passing in-process oracle beats a screenshot argument |
| Relapse comparison scope | `rules/guards/anti_relapse.py` | `relapse_domain`, `_battery`, `verdict_vector` | the battery is the EVALUABLE commitments; equivalence is `programs.evaluate` vectors |
| Relapse discrimination (RC2) | `rules/guards/anti_relapse.py` | `programs.program_class(...) == "structural"` | the only consumer of the registry classification; an all-structural battery establishes nothing |
| Executable-policy activation | `rules/experiment.py` | `_oracle_ready` | a generator or checker activates only on a deterministic PASS; abort and overrun fail closed |
| Rubric-warrant well-formedness | `harness.py` | `conforming_transcript` at warrant registration | a rubric-derived demonstrative warrant cannot be hand-built around the trial |
| Rules-side name for the guard | `rules/guards/rubric_verdict.py` | re-export of `run_trial`, `conforming_transcript` | a module with no logic; the trial protocol lives on the evaluation side |
| Fail packaging, reverse direction | `measures/hv.py`, `informal/audits.py` | `register_fail_warrant`, `verdict_on_record` | HV-floor failures and judge-audit findings become ordinary attackable warrants |

`check: grep -q "^def crit_program(" src/deepreason/rules/crit.py && grep -q "^def crit_vision(" src/deepreason/rules/vision.py && grep -q "^def _oracle_ready(" src/deepreason/rules/experiment.py && grep -q "^def _battery(" src/deepreason/rules/guards/anti_relapse.py && grep -q "^def relapse_domain(" src/deepreason/rules/guards/anti_relapse.py && grep -q "^def _argument_trial_steps(" src/deepreason/informal/trial.py && grep -q "^def pairwise_discriminate(" src/deepreason/informal/trial.py && grep -q "from deepreason.informal.trial import conforming_transcript, run_trial" src/deepreason/rules/guards/rubric_verdict.py`

`crit_program` is the whole mechanical side and its order is load-bearing: the
evaluability filter comes first, the sandbox-abort quarantine comes before the
`FAIL` test, and only a `FAIL` reaches `register_fail_warrant`. Reordering the
last two turns an availability failure into a refutation.
`check: python -c "import inspect; from deepreason.rules import crit; s=inspect.getsource(crit.crit_program); assert 'not programs.evaluable(kappa)' in s; assert s.index('sandbox_abort') < s.index('if verdict != programs.FAIL'); assert 'register_fail_warrant(' in s"`

The two guards sit in different files and are not interchangeable: `crit.py`
consults the narrow one, `informal/trial.py` the wide one.
`check: grep -q "if formally_backed(harness, target_id):" src/deepreason/informal/trial.py && grep -q "if execution_backed(harness, loser):" src/deepreason/informal/trial.py && grep -q "if execution_backed(harness, target_id):" src/deepreason/rules/crit.py && ! grep -q "formally_backed" src/deepreason/rules/crit.py`

The behaviour of the boundary, asserted rather than described — the widening, the
scrutiny that survives it, the failing commitment that earns nothing, the guard's
position ahead of every authority branch, and the correction that the line is
execution/formal backing and NOT evaluability.
`check: python -m pytest tests/test_prose_refutation_boundaries.py::test_formal_backing_covers_the_whole_formal_set_not_only_execution tests/test_prose_refutation_boundaries.py::test_the_criticism_rule_still_records_scrutiny_for_a_formal_target tests/test_prose_refutation_boundaries.py::test_a_failing_formal_commitment_earns_no_protection tests/test_prose_refutation_boundaries.py::test_the_execution_guard_is_consulted_before_the_authority_branch tests/test_prose_refutation_boundaries.py::test_a_prose_case_against_a_formally_backed_target_is_refused_by_type tests/test_prose_refutation_boundaries.py::test_the_formal_boundary_is_execution_backing_and_not_evaluability -q`

`_substantive` is defined once and imported once, and its refusal has teeth on
both consumers: no reach from a structural battery, no prose immunity from a
structural commitment, no relapse equivalence from a structural-only battery.

It is NOT the demarcation criterion, and briefly was. `measures/demarcation.py`
imported it for one commit, on an instruction the Formalization then superseded:
§12.2's `crit` is the weak test `K_a ≠ ∅`, and substantiveness is what the
battery EXHIBITS under variation (`load`), not what the interface asserts. The
census below is what makes that reversal visible — a third importer would mean
demarcation had drifted back onto the declaration test
(`DR-CON-problem-layer-lifecycle`; `experiments/2026-08-14-change-calculus-
reconciliation-v2/RECONCILIATION.md` S-1).
`check: grep -q "from deepreason.measures.reach import _substantive" src/deepreason/rules/warrants.py && test "$(grep -rl _substantive --include=*.py src/deepreason | wc -l)" -eq 2 && python -m pytest "tests/test_reflexive_discipline.py::test_structural_programs_never_ground_reach" tests/test_prose_refutation_boundaries.py::test_a_structural_program_confers_no_formal_backing tests/test_guards.py::test_structural_only_does_not_block -q`

Execution supremacy holds in all three directions it is claimed in: a preference
cannot unseat a running loser, a counterexample still refutes under
`observe_only`, and an abort mints nothing.
`check: python -m pytest tests/test_oracle.py::test_pairwise_preference_cannot_refute_execution_backed_loser tests/test_criticism_authority.py::test_execution_counterexample_still_refutes_under_observe_only tests/test_oracle.py::test_sandbox_abort_mints_no_fail_warrant -q`

A rubric-derived demonstrative warrant is refused at registration unless its
`trace_ref` holds a conforming trial transcript, so the §3 guard cannot be
bypassed by constructing the warrant directly.
`check: grep -q "from deepreason.informal.trial import conforming_transcript" src/deepreason/harness.py && grep -q "rubric-derived but trace_ref lacks a" src/deepreason/harness.py && grep -q "^def conforming_transcript(" src/deepreason/informal/trial.py`

## What is deliberately absent

**`formally_backed` is NOT consulted in `rules/crit.py`, and that is a
correction someone already made, not an omission.** The criticism rule's own
guard decides whether a case is RECORDED; the trial's decides a STATUS. Problem
criteria are instantiated into every candidate's interface, so widening the
criticism rule to match the trial deletes the `scrutiny` record for every target
carrying a passing problem criterion — losing the case entirely rather than
declining to act on it, which moves toward adjudication blindness. The negative
grep above is paired with the positive that `crit.py` still consults the narrow
guard, so deleting the guard cannot make the pair pass.

**`program_class` never reaches a guard, a warrant, or adjudication.** It is
process-reporting metadata with exactly one consumer with teeth — the RC2
all-structural check in the anti-relapse gate. Two files in the whole tree
mention it: the definition and that consumer. Wiring it into `_substantive`
would look like tidying and would change what prose may refute (see Traps).
`check: grep -q "programs.program_class(lookup\[cid\]) == \"structural\"" src/deepreason/rules/guards/anti_relapse.py && grep -q "^def program_class(" src/deepreason/programs.py && test "$(grep -rl program_class --include=*.py src/deepreason | wc -l)" -eq 2`

**`adjudication/` imports nothing from evaluation at all — not `programs`, not
`oracle`, not `measures`, not `informal`.** A verdict reaches the labelling
machinery only after it has become a warrant on the graph; the module that
decides what stands cannot recompute a verdict, and so cannot disagree with the
record about one. The check is an AST walk because `from deepreason import
programs` defeats a module-path grep, and it RESOLVES relative imports against
each file's own package before judging them: the earlier version compared
`n.module` verbatim, so `from ..programs import evaluate` and `from .. import
programs` both walked straight through it (measured — both now fail it). The
three positive greps are the counterpart: an absence check over a directory
passes for free once the directory is a husk, so the labelling entry points must
still be there for the absence to mean anything.
`check: python -c "import ast,pathlib;E={'programs','oracle','oracle_sandbox','measures','informal'};R=pathlib.Path('src/deepreason');Q=lambda p:p.relative_to(R.parent).with_suffix('').parts;M=lambda p,n:'.'.join(list(Q(p)[:len(Q(p))-n.level] if n.level else [])+([n.module] if n.module else []));F=sorted(R.joinpath('adjudication').rglob('*.py'));assert len(F)>=4;N=[(p,n) for p in F for n in ast.walk(ast.parse(p.read_text()))];A=lambda s:s.split('.');B=[a.name for p,n in N if isinstance(n,ast.ImportFrom) and M(p,n)=='deepreason' for a in n.names if a.name in E]+[M(p,n) for p,n in N if isinstance(n,ast.ImportFrom) and A(M(p,n))[:1]==['deepreason'] and A(M(p,n))[1:2] and A(M(p,n))[1] in E]+[a.name for p,n in N if isinstance(n,ast.Import) for a in n.names if A(a.name)[:1]==['deepreason'] and A(a.name)[1:2] and A(a.name)[1] in E];raise SystemExit(1 if B else 0)" && grep -q "^def build_att(" src/deepreason/adjudication/edges.py && grep -q "^def grounded_extension(" src/deepreason/adjudication/grounded.py && grep -q "^def final_labels(" src/deepreason/adjudication/support.py`

**No rule indexes the program registry, and no rule reaches the sandbox.**
`PROGRAMS` and `BLOB_PROGRAMS` are never imported into `rules/` and never touched
as attributes there; `evaluate` is the only door, which is what keeps the trace,
the abort signal and the `overrun` verdict on one path. `oracle_sandbox` is
reachable only through `oracle.py`, so no rule can start an interpreter without
the layer that maps `SandboxAborted` to `overrun`. Both halves are AST- and
grep-checked with the positive counterpart, so deleting `evaluate` or the
sandbox import does not make the pair pass.
`check: python -c "import ast,pathlib;F=list(pathlib.Path('src/deepreason/rules').rglob('*.py'));assert F;N=[n for p in F for n in ast.walk(ast.parse(p.read_text()))];reg={'PROGRAMS','BLOB_PROGRAMS'};B=[a.name for n in N if isinstance(n,ast.ImportFrom) for a in n.names if a.name in reg]+[n.attr for n in N if isinstance(n,ast.Attribute) and n.attr in reg];raise SystemExit(1 if B else 0)" && grep -q "from deepreason.oracle_sandbox import run_isolated" src/deepreason/oracle.py && ! grep -rq oracle_sandbox --include=*.py src/deepreason/rules/ && grep -q "^def evaluate(" src/deepreason/programs.py && grep -q "programs.evaluate(" src/deepreason/rules/crit.py`

**The reverse arrow is six names wide and no wider.** Everything `measures/` and
`informal/` import from `rules/` is `register_fail_warrant`, `verdict_on_record`,
`spawn`, `_observe_case`, `execution_backed`, `formally_backed` — packaging and
guards, never a rule that proposes or criticises. Evaluation does not get to
conjecture, and it does not get to mount an argument; it produces verdicts and
hands them to the one constructor. The check pins the exact set, so importing
`crit_argumentative` into `measures/hv.py` fails it (measured) — in the relative
form `from ..rules.crit import ...` as well as the absolute one, which the
earlier `n.module.startswith('deepreason.rules')` test missed (also measured).
Pinning NAMES only works while the package itself stays unimported, so
`from deepreason import rules` and `import deepreason.rules.crit` are refused
too: either would make the arrow silently unbounded.
`check: python -c "import ast,pathlib;R=pathlib.Path('src/deepreason');Q=lambda p:p.relative_to(R.parent).with_suffix('').parts;M=lambda p,n:'.'.join(list(Q(p)[:len(Q(p))-n.level] if n.level else [])+([n.module] if n.module else []));F=[p for d in ('measures','informal') for p in sorted(R.joinpath(d).rglob('*.py'))];assert len(F)>=11;N=[(p,n) for p in F for n in ast.walk(ast.parse(p.read_text()))];names={a.name for p,n in N if isinstance(n,ast.ImportFrom) and M(p,n).startswith('deepreason.rules') for a in n.names};whole=[a.name for p,n in N if isinstance(n,ast.ImportFrom) and M(p,n)=='deepreason' for a in n.names if a.name=='rules']+[a.name for p,n in N if isinstance(n,ast.Import) for a in n.names if a.name.split('.')[:2]==['deepreason','rules']];raise SystemExit(0 if not whole and names=={'register_fail_warrant','verdict_on_record','spawn','_observe_case','execution_backed','formally_backed'} else 1)"`

**Prose never mints a DEMONSTRATIVE warrant, and `crit.py` mints no
ARGUMENTATIVE one.** `WarrantType.DEMONSTRATIVE` is constructed exactly once in
the whole tree, inside `register_fail_warrant`, so "the verdict came from a
program" cannot be asserted by a module that did not run one. There are six
ARGUMENTATIVE constructors and none is in the criticism rule: two in
`informal/trial.py` (the defended trial and the pairwise loser), one in
`rules/vision.py` behind the narrow guard, one in `rules/experiment.py` against
a proposed PROPERTY rather than a candidate, one in `rules/relatedness.py`
(D2 rev 2, `relatedness_trial`, against a relatedness-CLAIM artifact rather
than a candidate or property), and one in `imports.py` for an imported
design. `crit.py` routes to the trial instead of packaging. The
`crit_argumentative` grep is there to pay for the negative next to it: measured,
renaming or deleting `rules/crit.py` made the bare `! grep` pass while proving
nothing, and the ARGUMENTATIVE count does not notice because the file
contributes none.
`check: test "$(grep -rn "WarrantType.DEMONSTRATIVE" --include=*.py src/deepreason | wc -l)" -eq 1 && grep -q "type=WarrantType.DEMONSTRATIVE," src/deepreason/rules/warrants.py && test "$(grep -rn "WarrantType.ARGUMENTATIVE" --include=*.py src/deepreason | wc -l)" -eq 6 && grep -q "^def crit_argumentative(" src/deepreason/rules/crit.py && ! grep -q "WarrantType.ARGUMENTATIVE" src/deepreason/rules/crit.py && grep -q "execution_backed" src/deepreason/rules/vision.py`

**There is no cache of "is this target formal", and the guards do not read the
one cache that exists.** Both predicates call `programs.evaluate` live on every
carried commitment on every call, and neither touches `harness._verdict_cache`,
which only `reach._verdict` fills. That is affordable because verdicts are pure
functions of content, and it is necessary because protection must track the
CURRENT verdict: a target whose exec-oracle starts failing loses its immunity in
the same cycle rather than at the next cache eviction. Adding a memo here would
also inherit `_verdict_cache`'s deliberate sandbox-abort hole, turning machine
availability into an immunity decision.
`check: python -c "import inspect; from deepreason.rules import warrants; s=inspect.getsource(warrants); assert '_verdict_cache' not in s; assert s.count('programs.evaluate(kappa, target, harness.blobs)')==2" && grep -q "_verdict_cache" src/deepreason/measures/reach.py && grep -q 'if \"sandbox_abort\" not in trace:' src/deepreason/measures/reach.py`

## How to change it

1. **Read `DR-INV-frozen-surfaces` first.** The `"execution-backed"` decline
   reason and every `Measure` tag this seam emits are compared against recorded
   roots. Widening a guard is ordinary future-facing work; renaming its typed
   reason reinterprets every stored diagnostic and is a defect.
2. **Decide which of the three questions you are changing.** They are three
   different sets and people conflate them: what is DECIDABLE (`evaluable` /
   `PROGRAMS`), what is SUBSTANTIVE (`_STRUCTURAL_PROGRAMS`), what is PROTECTED
   (`execution_backed` / `formally_backed`). Changing the middle one moves reach
   and prose-immunity together, in opposite directions of harm.
3. **Change the SET, never the predicate.** `execution_backed` and
   `formally_backed` are the only two readers of their sets and both are already
   consulted at every registration path. A new "kind of formal" is a membership
   decision in `oracle.py` or `measures/reach.py`, not a third predicate — a
   third predicate is a third place for a call site to consult the wrong one.
4. **Registering a new program is a THREE-part decision, and the default is the
   dangerous one.** A `PROGRAMS` row needs its `class_`, an explicit answer on
   `EXEC_PROGRAMS`, and an explicit answer on `_STRUCTURAL_PROGRAMS`. Omit the
   third and the program is substantive by default, so anything carrying it and
   passing becomes immune to prose criticism. The registry's own
   `class_="structural"` will NOT save you (see Traps).
5. **Move the guard and its recording sibling together, or deliberately not.**
   If you widen `informal/trial.py`, decide in writing whether `rules/crit.py`
   and `rules/vision.py` move too. The recorded answer so far is no.
6. **Never let a verdict reach adjudication except as a warrant.** A change that
   gives `adjudication/` a program call is not a refactor; it makes the labelling
   machinery able to disagree with its own record.

What breaks first, in the order you will see it. `tests/test_prose_refutation_
boundaries.py` is the cheapest and the most specific — it asserts the guards'
identity, their ORDER relative to every authority branch, and the structural
hole; then `tests/test_reflexive_discipline.py` on the reach side and
`tests/test_guards.py` on the relapse side; then `tests/test_oracle.py` and
`tests/test_criticism_authority.py` for supremacy end to end; then
`tests/test_trial.py` and `tests/test_audits.py`. A guard change that survives
all of those and still moves an existing root's `att` is caught only by the
42-root sweep in `DR-INV-frozen-surfaces`, which is the expensive place to find
out.

## Traps

- **The registry's "structural" and the seam's "structural" WERE two different
  sets, disagreeing on five programs. Fixed 2026-08-22; they are now one set.**
  `_STRUCTURAL_PROGRAMS` was hand-written on 2026-07-10 (`aea0b9a0`); the
  chunked-website programs landed on 2026-07-11 (`1634b35f`) and were never
  added, so `component_wf`, `generator_wf`, `integration_wf`, `manifest_wf` and
  `reasoning-envelope-wf` were structural to the anti-relapse gate (they
  establish no equivalence) and SUBSTANTIVE to `formally_backed` (a passing one
  conferred prose immunity) and to `reach_sweep`. Tranche
  `experiments/2026-08-22-reach-structural-programs-fix` closed the gap by
  DERIVING the set from `ProgramSpec.class_` rather than adding the five names,
  so there is no longer a second set to disagree with.
  Both residues this entry recorded are discharged, and neither by an
  implementer's judgement:
  **(1)** "whether these five *should* be structural for backing is an
  operator's call" — the operator made it, in that tranche's brief: "make
  measures/reach.py::_substantive agree with the structural class that
  programs.PROGRAMS already declares, so a well-formedness gate can never
  ground reach or confer prose immunity."
  **(2)** "not an observed live failure" — it was measured rather than left
  open. On the prose-immunity side it never fired:
  `experiments/2026-08-21-measure-reach-firing/probe_immunity.json` puts
  `backed_only_by_declared_structural` at 0 over 3 528 candidate artifacts, so
  no root's adjudication moved. On the REACH side it was load-bearing in the
  opposite direction — a qualifying criterion must PASS, and
  `reasoning-envelope-wf` fails on prose, so it vetoed hits rather than
  manufacturing them: `experiments/2026-08-22-live-reach-rich-run/rehearsal.json`
  S8a/S8b/S8c, and 793 gate pairs across 46 roots in that tranche's `CENSUS.md`.
  The check below is inverted from asserting the divergence to asserting the
  agreement, so the entry cannot rot back to the old claim unnoticed.
`check: python -c "from deepreason.programs import programs_by_class; from deepreason.measures.reach import _STRUCTURAL_PROGRAMS, _substantive; from deepreason.ontology import Commitment; reg=set(programs_by_class()['structural']); assert reg == set(_STRUCTURAL_PROGRAMS), sorted(reg ^ set(_STRUCTURAL_PROGRAMS)); assert {'component_wf','generator_wf','integration_wf','manifest_wf','reasoning-envelope-wf'} <= reg; assert not any(_substantive(Commitment(id='k', eval='program:'+p)) for p in reg)"`
- **Assuming the guard is on the side you are editing.** The prose-immunity
  guard is in `informal/trial.py`, not in `rules/crit.py`, because the two
  answer different questions — one decides what CHANGES A STATUS, the other what
  gets RECORDED. This was got wrong once and corrected mid-tranche; the test
  `test_the_criticism_rule_still_records_scrutiny_for_a_formal_target` exists
  because the wrong version passed everything else.
- **Reading `evaluable` as "formal".** `SPEC.md`'s A1 in the 2026-08-01 tranche
  did exactly this. The implemented line is narrower on the execution side and
  different in kind on the formal side: `evaluable` admits `program:json-wf`,
  which passes for anything well-formed, and safe skeleton compilation lets a
  conjecturer author `program:` commitments. Were evaluability enough, a
  candidate could immunise itself by filling in the form. The test docstring on
  `test_the_formal_boundary_is_execution_backing_and_not_evaluability` records
  the correction.
- **Deleting a name from `_STRUCTURAL_PROGRAMS` is caught by ONE test, and it is
  not the one you would guess.** Measured: removing `"json-wf"` from the set
  leaves `test_structural_programs_never_ground_reach` GREEN (it exercises
  `lineage_ref`) and `test_a_structural_only_target_is_still_refutable_by_prose`
  GREEN (its target's `json-wf` fails on prose bytes, so the
  all-currently-pass clause declines protection anyway). Only
  `test_a_structural_program_confers_no_formal_backing`, which uses valid JSON,
  goes red. Do not treat a green reach suite as evidence that the immunity side
  is intact.
- **Renaming the `execution-backed` decline reason.** The guard was widened from
  execution to the whole formal set at step 18 of the 2026-08-01 tranche and the
  string deliberately kept its now-inaccurate spelling, because it is compared
  against recorded roots. Same discipline as any typed reason string
  (`DR-INV-frozen-surfaces`).
- **`overrun` is not `fail`, and the rules must never collapse them.** A sandbox
  kill, a missing spec, an unusable checker and a `lean_*` program with no
  verifier all return `overrun`. `crit_program` quarantines rather than minting,
  `_oracle_ready` fails closed rather than activating, and `reach._verdict`
  refuses to cache a trace carrying `sandbox_abort` — three separate places that
  each have to get it right, because there is no shared "did this actually
  decide?" helper.
- **`register_fail_warrant` has nine callers and three of them are on the
  evaluation side** (`measures/hv.py`, `informal/trial.py`,
  `informal/audits.py`). A change to the ν wording, the `w:<κ>:<target>` id
  scheme or the critic provenance is not local to `rules/`; it moves the HV
  floor's warrants and the judge audits' findings too.
`check: test "$(grep -rl "register_fail_warrant(" --include=*.py src/deepreason | grep -cv "rules/warrants.py")" -eq 9 && test "$(grep -rl "register_fail_warrant(" --include=*.py src/deepreason/measures src/deepreason/informal | wc -l)" -eq 3 && grep -q "^def register_fail_warrant(" src/deepreason/rules/warrants.py`
