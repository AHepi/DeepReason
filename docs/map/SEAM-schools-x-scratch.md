<!-- DR-SEAM-schools-x-scratch -->
Verified-at: 08dcdf3c
Verify: python tools/docs_verify.py
Owns: src/deepreason/scratch/conjecture.py, src/deepreason/rules/conj.py, src/deepreason/scheduler/scheduler.py
Sides: DR-CON-schools, DR-SUB-scratch
Sweep: school_id && conjecture_context|ConjectureContextCall|PlannedConjectureContext|scratch

# Schools x scratchpad

## The agreement

A school gives the scratchpad exactly one thing: an identifier. Not a stance,
not a weight, not a lineage — the bare string `school-<n>`, and only at the
moment a conjecture context is planned. The scratchpad gives three things back.
It treats that identifier as a retrieval SEED, so two schools reading one pad at
one fence get differently drawn views of the same notes. It stamps the
identifier onto the plan and onto the durable call receipt, so rendered bytes
can never be replayed as another school's. And it keeps the identifier out of
every stored record — no block, link, cluster, guide, attention receipt or
proposal carries a school, because the pad is one workshop that all schools
write into and all schools read from.

The two sides therefore meet at exactly one seat, `conjecturer`. Conditioning
belongs to the move that invents, so that is where the workshop opens.
Criticism decides what stands, so criticism gets a school and no notes at all.
That is the whole shape: islands in conjecture, a commons in imagination, and an
authority chain that is blind to both. `DR-CON-schools` says why a school grants
no status; `DR-SUB-scratch` says why a note grounds nothing;
`DR-SEAM-rules-x-scratch` says how the pad reaches a pack at all. This document
is only about what the school id does once both of those hold — and about the
non-interaction that R5/R6 pinned, which is the reason the seam is interesting
rather than routine.

## Where it is expressed

| Site | File | Symbol | What it enforces |
|---|---|---|---|
| Seed derivation | `scratch/conjecture.py` | `_seed`, `_expansion_seed` | `school_id` is one field of the canonical payload hashed into `AttentionRequestV1.deterministic_seed` — the only route by which a school reaches selection |
| Plan binding | `scratch/conjecture.py` | `PlannedConjectureContextV1.school_id` | pattern `^school-(0\|[1-9][0-9]*)$`, default `None`; stance prose cannot occupy the field |
| Planning entry | `scratch/conjecture.py` | `plan_conjecture_context`, `plan_conjecture_context_expansion` | take `school_id: str \| None` and nothing else school-shaped; the expansion planner also refuses a `prior_plan` from another school |
| Receipt re-validation | `scratch/conjecture.py` | `validate_conjecture_context_call` | rejects a receipt whose `school_id` differs from the caller's, before touching scratch state |
| Rule-level pairing | `rules/conj.py` | `conj` (`execution_school_id` vs `conjecture_context_plan.school_id`) | `"conjecture context was planned for another school"` — plan and routed school must be one school, or the turn dies before dispatch |
| Prompt assembly | `llm/packs.py` | `render_conj_pack` (`school=`, `scratch_context=`) | the only renderer holding both; stance is section 5 (compressible), advisory context section 7 (never compressed, never dropped) |
| Per-cycle wiring | `scheduler/scheduler.py` | `_plan_conjecture_context`, `_school_dict` | the planner is handed the bare allocated id; the stance/weight/crossover dict goes only to `conj`'s `school=` argument |
| Dispatch boundary | `llm/adapter.py` | `LLMAdapter.call` (`school_id != conjecture_context.school_id`) | `"school route and advisory context must name one school"` — refused before the provider is contacted; the same block refuses advisory context for any role but `conjecturer` |
| Shadow replay audit | `workflow/shadow.py` | school/context comparison (`actual_school != ticket.work_order.school_id`) | records typed `ShadowMismatchCode.SCHOOL` — observational, an audit signal rather than a raise |
| Durable receipt | `ontology/event.py` | `ConjectureContextCallReceiptV1.school_id` | the school travels with the advisory-context proof onto the append-only log |
| v4/v5 replay authority | `workflow/replay.py` | `_validate_proposal` | `context_receipt.school_id != work.school_id` fails the root |
| v6 recovery authority | `workflow/conjecture_recovery.py` | `_validate_authority` | a scratch-bearing exposure is re-validated against the frozen payload's `school_id` on every restart |
| Event well-formedness | `harness.py` | conjecture-turn application (`context.school_id != payload.school_id`) | `"conjecture turn source context belongs to another work item"` — the turn is refused at APPEND time, before any replay reads it. A FROZEN surface: this guard cannot be relaxed |
| Replay validation | `invariants.py` | `validate_conjecture_context` | a receipt carrying a `school_id` with no `SchoolRouteReceiptV1` on the same call is not a valid root |

`check: python -c "import inspect; from deepreason.llm import packs; sig=lambda n: set(inspect.signature(getattr(packs,n)).parameters); assert {'school','scratch_context'} <= sig('render_conj_pack'); assert all(not sig(n) & {'school','scratch_context'} for n in ('render_crit_pack','render_batch_crit_pack'))"`

`check: python -c "from deepreason.scratch.conjecture import _seed, _expansion_seed as e; assert len({_seed('0'*64,'P',None,3,3), _seed('0'*64,'P','school-0',3,3), _seed('0'*64,'P','school-1',3,3)}) == 3; assert e('0'*64,'P','school-0','sha256:'+'0'*64,'sha256:'+'1'*64) != e('0'*64,'P','school-1','sha256:'+'0'*64,'sha256:'+'1'*64)"`

`check: python -c "import pytest; from pydantic import ValidationError; from deepreason.ontology.event import ConjectureContextCallReceiptV1 as R; from deepreason.scratch.conjecture import PlannedConjectureContextV1 as P; from deepreason.workflow.models import WorkOrderEnvelopeV1 as W; b=dict(manifest_digest='a'*64, problem_id='P', formal_fence_seq=3, scratch_fence_seq=3, selection_receipt_ref='sha256:'+'1'*64, advisory_context_ref='sha256:'+'2'*64, render_receipt_ref='3'*64, rendered_context_ref='4'*64); R(**b, school_id='school-0'); assert all(pytest.raises(ValidationError, R, **b, school_id=v) for v in ('counterexample first','School-0','school-00','')); assert all(m.model_fields['school_id'].default is None for m in (P,R,W))"`

`check: python -c "import pytest; from deepreason.ontology.event import ConjectureContextCallReceiptV1 as R; from deepreason.scratch.conjecture import validate_conjecture_context_call as v; r=R(manifest_digest='a'*64, problem_id='P', school_id='school-0', formal_fence_seq=3, scratch_fence_seq=3, selection_receipt_ref='sha256:'+'1'*64, advisory_context_ref='sha256:'+'2'*64, render_receipt_ref='3'*64, rendered_context_ref='4'*64); k=dict(manifest_digest='a'*64, problem_id='P', scratch_aliases={}, provider_prompt=b''); assert all('belongs to another school' in str(pytest.raises(ValueError, v, None, r, school_id=s, **k).value) for s in ('school-1', None))"`

The same mismatch is caught seven more times, at different distances from the
call — two of them (`llm/adapter.py` at dispatch, `workflow/shadow.py` in
shadow replay) found by the `--coverage` sweep after the hand-written list had
already been corrected once: in the rule before dispatch, in the expansion planner against the
prior plan, in v4/v5 replay against the work order, in v6 restart recovery
against the frozen payload, in `harness.py` when the conjecture turn is
APPENDED, and in `verify_root` against the route receipt on the same event. The check below reads each guard through the AST rather than by
grep, because a commented-out comparison leaves the text intact — the earlier
grep form of this check passed with `workflow/replay.py`'s clause disabled by a
single `#`. That matters more here than elsewhere: the v4/v5 replay comparison,
and the receipt comparison the v6 restart path leans on, have no gate test
behind them at all (see Traps), so this check is their only tripwire short of
the root sweep.

`check: python -c "import ast, pathlib; fn=lambda p,n: next(f for f in ast.walk(ast.parse(pathlib.Path(p).read_text())) if isinstance(f, ast.FunctionDef) and f.name==n); live=lambda f,e: any(ast.unparse(n)==e for n in ast.walk(f)); msg=lambda f,m: any(m in ast.unparse(n) for n in ast.walk(f) if isinstance(n, (ast.Raise, ast.Call))); c=fn('src/deepreason/rules/conj.py','conj'); assert live(c, 'conjecture_context_plan.school_id != execution_school_id') and msg(c, 'conjecture context was planned for another school'); x=fn('src/deepreason/scratch/conjecture.py','plan_conjecture_context_expansion'); assert live(x, 'prior.school_id != school_id'); r=fn('src/deepreason/workflow/replay.py','_validate_proposal'); assert live(r, 'context_receipt.school_id != work.school_id'); a=fn('src/deepreason/workflow/conjecture_recovery.py','_validate_authority'); assert live(a, \"payload.get('school_id')\"); v=fn('src/deepreason/invariants.py','validate_conjecture_context'); assert live(v, 'receipt.school_id is not None and route_receipt is None') and msg(v, 'school context has no matching route receipt'); assert live(fn('src/deepreason/invariants.py','verify_root'), 'validate_conjecture_context(e)')"`

### The pad is shared, not partitioned

One scratchpad serves every school. A note written during `school-3`'s turn is
an ordinary retrieval candidate for `school-0` on the next cycle, because
nothing in the record says who wrote it in school terms. The school changes the
selection SEED, and therefore tie-breaks and exploratory draws; it does not
change the candidate set. Three plans over one pad of six blocks at one fence:
one `final_order` of at least three blocks, identical across all three, and
three distinct request hashes. The pad has to hold several blocks for that to
mean anything — over a single-block pad the order assertion is satisfied by any
selector at all, including one that reorders or partitions by school.

`check: python -c "import sys,tempfile,pathlib; sys.path.insert(0,'tests'); from deepreason.harness import Harness; from deepreason.scratch.service import ScratchService; from deepreason.scratch.models import ScratchProvenanceV1 as V; from deepreason.scratch.conjecture import plan_conjecture_context as P; import test_conjecture_scratch_context_v4 as T; h=Harness(pathlib.Path(tempfile.mkdtemp())/'run'); p=T._seed(h); s=ScratchService(h); [s.create_block({'content': 'Note %d: a delayed negative feedback loop might stabilize the observed oscillation.' % i, 'unfinished': 'Check whether delay %d changes sign.' % i}, V(actor='user', origin='b3-test', formal_artifact_refs=[p.id])) for i in range(6)]; m=T._manifest(T._config()); f=h._next_seq-1; pl=[P(s,problem=p,school_id=i,manifest_digest=m.sha256,scratch_policy=m.scratch_policy,context_policy=m.control_plane_policy.conjecture_context,formal_fence_seq=f,scratch_fence_seq=f) for i in (None,'school-0','school-1')]; o=[tuple(x.attention_pack.selection_receipt.final_order) for x in pl]; assert len(o[0]) >= 3, o; assert len(set(o))==1, o; assert len({x.attention_pack.selection_receipt.request_hash for x in pl})==3; assert [x.school_id for x in pl]==[None,'school-0','school-1']"`

The record agrees. In the committed selfstudy root
`completed-epoch3-run-9175f0ec`, four schools consumed advisory context across
seven distinct seeds; `school-0` and `school-1` selected the identical five
blocks, and every school's selection is a subset of `school-3`'s thirteen.

`check: python -c "import json,pathlib,collections; R=pathlib.Path('experiments/live_research_2026-07-29/selfstudy/runs/completed-epoch3-run-9175f0ecb055e57455af3c50df153c5a'); recs={r['id']: r['data'] for r in (json.loads(p.read_text()) for p in (R/'objects'/'scratch-attention-receipt').rglob('*') if p.is_file())}; ctx=[e['llm']['conjecture_context'] for e in (json.loads(l) for l in (R/'log.jsonl').open()) if (e.get('llm') or {}).get('conjecture_context')]; by=collections.defaultdict(set); seeds=set(); [(by[c['school_id']].update(recs[c['selection_receipt_ref']]['final_order']), seeds.add(recs[c['selection_receipt_ref']]['deterministic_seed'])) for c in ctx]; assert sorted(by)==['school-0','school-1','school-2','school-3']; assert len(seeds)==len(ctx)==7; assert len(by['school-3'])==13 and all(v <= by['school-3'] for v in by.values()); assert by['school-0']==by['school-1'] and len(by['school-0'])==5"`

### Where each side carries the school

The two seats carry their school in structurally different places, and the
difference is what keeps the pad on one side. A conjecture work order names its
school on the ENVELOPE, beside `advisory_context_ref`. Criticism has no
envelope field at all: `WorkPreparationV1` — the v6 record that serves
`CRITICISM`, `REPAIR`, `SCRATCH_AUTHORING` and the rest — has neither
`school_id` nor `advisory_context_ref`, so a critic's school rides in the typed
payload as `critic_school_id` and there is nowhere for advisory context to sit.
`verify_root` reads both spellings through `_prepared_school_id`; only one of
them can be accompanied by a pad.

What criticism does carry is the fence. `scratch_fence_seq` appears twice in
`crit.py`, both times equal to the formal fence at the same call: the criticism
transaction is ORDERED against the scratch log without being allowed to read it.
Deleting it to "complete the separation" would remove ordering, not coupling.

`check: python -c "import typing; from deepreason.workflow.transaction import WorkPreparationV1 as K; from deepreason.workflow.models import WorkOrderEnvelopeV1 as W, WorkflowTaskKind as T; assert 'advisory_context_ref' in W.model_fields and 'school_id' in W.model_fields and W.model_fields['task_kind'].annotation == typing.Literal[T.CONJECTURE]; assert not {'advisory_context_ref','school_id'} & set(K.model_fields) and K.model_fields['task_kind'].annotation is T" && grep -q 'critic_school_id' src/deepreason/rules/crit.py && grep -q 'payload.get("critic_school_id")' src/deepreason/invariants.py && grep -q "transactional work requires one immutable state fence" src/deepreason/workflow/transaction.py && grep -q "conjecture work requires one formal/scratch state fence" src/deepreason/workflow/models.py && grep -q "formal and scratch context fences must name one event prefix" src/deepreason/scratch/conjecture.py && test "$(grep -c "scratch_fence_seq=fence" src/deepreason/rules/crit.py)" -eq 2`

`check: python -c "import ast,inspect; import deepreason.harness as h; src=inspect.getsource(h); t=ast.parse(src); found=any(isinstance(n,ast.Compare) and any('school_id' in ast.dump(c) for c in [n.left]+n.comparators) for n in ast.walk(t)); assert found, 'harness no longer compares school_id on conjecture-turn application'"`

`check: grep -q "school route and advisory context must name one school" src/deepreason/llm/adapter.py`
`check: grep -q "only conjecturer calls accept advisory context" src/deepreason/llm/adapter.py`
`check: grep -q "ShadowMismatchCode.SCHOOL" src/deepreason/workflow/shadow.py`

Two files trip the coverage sweep but belong elsewhere, named here so the
sweep's dismissal rule is satisfied by an explanation rather than silence:
`verification/report.py` compares `school_id` only to FILTER candidates when
assembling the epistemic report (read side, no refusal), and
`workflow/nonconjecture_recovery.py` guards `critic_school_id` for the
criticism-assignment seam, not this one.

## What is deliberately absent

**A school reaches criticism; the scratchpad does not.** This is the sharpest
fact in the seam, and it is easy to misread as an oversight because criticism is
visibly school-aware — `_critic_execution` builds a conditioning prefix naming
the critic's own school and stance, and pays for it out of the pack budget. The
critic therefore HAS the conditioning half of the pair and is denied the
workshop half. The operator's words are R5/R6 in
`experiments/2026-08-01-change-prose-can-refute/REQUEST.md`: "the scratchpad
authority chain needs to be completely separate from conjecture/criticism
adjudication... they shouldn't exist together." R5/R6 closed an open question in
the negative — the tranche was heading toward exposing scratch to the critic as
its reading of R3, and was overruled. `DR-SEAM-rules-x-scratch` documents the
mechanism of the refusal (AST-walked imports, absent parameters, absent wire
fields); what belongs here is that the refusal survives school conditioning
rather than being an artifact of the critic having no context at all.

`check: python -m pytest tests/test_prose_refutation_boundaries.py::test_the_criticism_rule_imports_no_scratch_module tests/test_prose_refutation_boundaries.py::test_the_criticism_pack_cannot_be_given_scratch tests/test_prose_refutation_boundaries.py::test_the_defended_trial_imports_no_scratch_module tests/test_prose_refutation_boundaries.py::test_no_scratch_identifier_reaches_a_warrant_or_an_attack_edge -q && python -c "from deepreason.llm.firewall import EndpointLease as L, Route as T; from deepreason.rules.crit import _critic_execution as X; p=X(endpoint_lease=L(role='argumentative_critic',seat=1,route=T(endpoint_id='e',base_url='u',model_id='m',provider='p',family='f')), critic_school_id='school-3', critic_school_context={'id':'school-3','stance_text':'counterexample first'})[1]; assert 'school-3' in p and 'counterexample first' in p and 'scratch' not in p.lower()"`

**Criticism cannot even declare a scratch context plan.** Every
`ContextPackPlanV1` the criticism rule builds is `plan_kind="dossier"` or
`"citable"` — frozen evidence either way, the second being the admitted-block
legend P4 added — and `conj.py` is the only rule that builds a `"scratch"`
plan. The exposure ledger is the record of what a seat was shown, so this is
not a habit of the current call sites: a criticism seat that showed scratch
would have to mint a plan kind it never mints.

`check: python -c "import ast, pathlib; kinds=lambda p: [k.value for n in ast.walk(ast.parse(pathlib.Path(p).read_text())) if isinstance(n, ast.Call) for k in n.keywords if k.arg=='plan_kind']; c=kinds('src/deepreason/rules/crit.py'); assert c, 'criticism builds no context pack plan at all'; assert all(isinstance(v, ast.Constant) and v.value in {'dossier','citable'} for v in c), [ast.unparse(v) for v in c]; assert any(isinstance(v, ast.Constant) and v.value=='scratch' for v in kinds('src/deepreason/rules/conj.py'))"`

**The scratchpad does not know what a school IS.** `scratch/conjecture.py` is
the only module under `scratch/` in which the word appears at all, and there it
is an opaque id. Nothing under `scratch/` imports `deepreason.capture`, so the
stance library, the roster, `allocate` and `reseed` are unreachable from the pad.
A retrieval channel that preferred a school's own notes therefore cannot be
written, because the channel has no way to ask.

That negative grep also covers the selection machinery, which is where
partitioning would actually be implemented: `attention.py` — `_candidates`,
`_apply_channel_limits`, `_final_order`, `AttentionRequestV1`,
`AttentionPolicyV1` — never mentions a school, and every candidate comes from
`service.state.blocks` unfiltered. Treat it as a tripwire rather than a style
rule: the first line naming a school in the selector is the line that turns the
commons into silos.

`check: python -c "import pathlib; S=pathlib.Path('src/deepreason/scratch'); mods={p: p.read_text() for p in S.rglob('*.py')}; assert 'school_id' in mods[S/'conjecture.py']; assert '    def _final_order(' in mods[S/'attention.py']; assert [p.name for p in mods if 'school' in mods[p]]==['conjecture.py'], sorted(p.name for p in mods if 'school' in mods[p]); assert not [p.name for p in mods if 'deepreason.capture' in mods[p]]; t=pathlib.Path('src/deepreason/capture/schools.py').read_text(); assert '\nSTANCE_LIBRARY' in '\n'+t and '\ndef allocate' in t and '\ndef reseed' in t"`

**Stance text never crosses.** The school dict handed to `conj` carries `id`,
`stance_text`, `weight` and `crossover`; only `id` continues into the planner.
Retrieval cannot be steered by what a school BELIEVES — the seed sees an
identifier, and the identifier's pattern would reject prose anyway.

`check: python -c "import inspect; from deepreason.scratch import conjecture as c; ps=[inspect.signature(f).parameters for f in (c.plan_conjecture_context, c.plan_conjecture_context_expansion)]; assert all(p['school_id'].annotation=='str | None' for p in ps); assert not [k for p in ps for k in p if 'stance' in k or 'weight' in k or k=='school']; assert not [k for k in inspect.signature(c._focus_blocks).parameters if 'school' in k]"`

**A stored note records no school, and an artifact records no note.** The
reference arrow is one-way: `ScratchProvenanceV1.formal_artifact_refs` lets a
note name the formal object it was aimed at, while `Provenance` on an artifact
records the school that generated it and nothing about the pad. Neither the
draft container the model fills in nor the block body has anywhere to put a
school. Two consequences, both load-bearing: retrieval cannot be partitioned
after the fact, and a scratch identifier cannot ride into formal state on a
provenance field.

`check: python -c "from deepreason.scratch.models import ScratchProvenanceV1 as S, ScratchBlockBodyV1 as B; from deepreason.scratch.proposals import ScratchProposalV1 as D; from deepreason.ontology.artifact import Provenance as A; assert set(S.model_fields)=={'actor','origin','source_refs','formal_artifact_refs'}; assert not [k for m in (B,D) for k in m.model_fields if 'school' in k]; assert 'school' in A.model_fields and not [k for k in A.model_fields if 'scratch' in k]"`

## How to change it

The school id is frozen into an append-only receipt long before replay reads it
back, so the order is fixed.

1. **Decide which authority you are touching.** Changing which notes a school
   sees is ordinary work. Anything that would let a note reach criticism, the
   trial, a warrant or an attack edge is refused before design — R5/R6 and
   `advisory_non_grounding` both bar it, and overturning a pinned negative
   assertion is an operator's call, not an implementer's.
2. **Change `scratch/conjecture.py` first, and only its planning functions.**
   `PlannedConjectureContextV1`'s field set is what the plan/receipt pair is
   built from; adding a field there means adding it to
   `ConjectureContextCallReceiptV1`, which is an event format. Read
   `DR-INV-frozen-surfaces` first: old roots must still verify.
3. **Do not partition the pad by adding a school to a scratch record.** That is
   the change this document exists to price. It moves every stored block's
   content address, so every recorded root's `scratch_state` re-derives
   differently — wrong by definition. If schools need private notes, the seam to
   change is retrieval (a channel keyed on the seed), not storage.
4. **Move the five school comparisons together.** `conj`'s plan/execution
   pairing, `plan_conjecture_context_expansion`'s `prior_plan` refusal,
   `validate_conjecture_context_call` (which `conjecture_recovery.
   _validate_authority` re-runs on every restart), `replay._validate_proposal`
   and `invariants.validate_conjecture_context` all compare a receipt's school
   against an authority. Change one and a run dispatches, then fails its own
   replay. Two of them are unguarded by the gate, so the map check on the
   agreement section is what catches a half-move.
5. **Then the prompt.** `render_conj_pack` is the only renderer that may gain
   scratch material. If a change makes the criticism pack want it, the change is
   wrong.
6. **Finish with the root sweep.** A change to a reader or a guard here changes
   how recorded roots verify; `DR-INV-frozen-surfaces` names the instrument.

What breaks first, cheapest first: `tests/test_prose_refutation_boundaries.py`
(0.1 s) the instant scratch touches the authority chain; then
`tests/test_conjecture_scratch_context_v4.py` for the v4/v5 plan/commit
lifecycle; then `tests/test_v6_conjecture_scratch_consumption.py` for the v6
exposure and its restart-time re-authorization; then
`tests/test_v6_context_continuation.py` for school-bound expansion. Only after
those, on a later run, `verify_root`'s `conjecture-context` failure — the
expensive one, because by then the root is committed.

`check: python -m pytest tests/test_v6_conjecture_scratch_consumption.py::test_recovery_rejects_scratch_exposure_without_durable_context_authority tests/test_conjecture_scratch_context_v4.py::test_scratch_handles_never_enter_formal_state_or_grounding -q`

## Traps

- **26 files mention both sides; three carry the agreement.** `grep -rl school`
  intersected with `grep -l scratch` returns 26 modules today, including
  `config.py`, `cli/main.py`, `signals.py` and `referee.py`, which name both and
  mediate neither. Starting from grep costs a day; the `Owns:` line is the
  answer, and the durable re-checks are in `workflow/replay.py`,
  `workflow/conjecture_recovery.py` and `invariants.py`, owned elsewhere.
- **The scheduler passes two different school values on one line of work.**
  `_plan_conjecture_context(problem, school_id)` receives the raw allocated id
  — forwarded unchanged by `_dispatch_conjecture_context_plan`, its only caller
  — while `conj` receives `school_id if school_id in school_leases else None`.
  They agree today only because `resolve_school_role_lease` either returns a
  lease or raises, so every assigned school is a key in `school_leases`. Make it
  return `None` for some mode and the plan carries a school the turn does not,
  and `conj` refuses the plan it was just handed.
`check: python -c 'import inspect; from deepreason.scheduler.scheduler import Scheduler as S; o = inspect.getsource(S._dispatch_conjecture_context_plan); assert "return self._plan_conjecture_context(problem, school_id)" in o, "the owner no longer forwards the raw allocated id"; assert "self._dispatch_conjecture_context_plan(\n                        problem, school_id\n                    )" in inspect.getsource(S.step)' && grep -q "school_id if school_id in school_leases else None" src/deepreason/scheduler/scheduler.py && grep -q "def _plan_conjecture_context(self, problem, school_id: str | None):" src/deepreason/scheduler/scheduler.py`
- **Two of the five school comparisons have no test behind them, and the v6 one
  is not the exception it was written up as.** Deleting
  `or context_receipt.school_id != work.school_id` from
  `workflow/replay.py::_validate_proposal` left 483 passed / 0 failed across
  every `tests/test_*{school,scratch,context,recover,conjecture}*.py` file.
  Deleting the v6 twin — `receipt.school_id != school_id` in
  `validate_conjecture_context_call` — left the same set at 482 passed, its one
  failure a thread-liveness flake in `test_mcp_scratch_bridge.py` that is green
  on a clean re-run. No test in the repository names
  `validate_conjecture_context_call` or the string "belongs to another school"
  at all. An earlier revision of this trap asserted the v6 path WAS covered,
  because `test_recovery_rejects_scratch_exposure_without_durable_context_authority`
  fails when recovery is broken; that test covers the ADJACENT guard — that a
  scratch-bearing exposure carry a context receipt at all — and passes with the
  school comparison deleted. Treat both comparisons as protected by the root
  sweep and by this document's AST check, not by the gate. (Measured
  2026-08-02; both mutations reverted, tree confirmed clean.) Residue: the full
  gate was not run under either mutation, so a covering test outside that file
  selection has not been excluded.
- **"School-blind" and "school-scoped" describe different things here.** The
  criticism PROMPT is blind to the target's school and deliberately names the
  critic's own (`DR-CON-schools`). The scratchpad is the reverse: school-scoped
  at the receipt, school-blind at the store. Reading either as "schools are
  absent from this side" leads to the wrong change.
- **The advisory section cannot be compressed away; the stance beside it can.**
  `scratch-advisory-context` is `droppable=False, compressible=False`, because
  the committed receipt asserts the pack contains those exact bytes once. The
  `school-stance` section is `droppable=False, compressible=True` with a
  24-token floor. A budget change that starts compressing section 7 to make room
  for section 5 breaks the receipt, not the prompt.
`check: python -c "from deepreason.llm.seat_layouts import CONJECTURER_LEGACY_LAYOUT as C, CRITIC_LEGACY_LAYOUT as R;from deepreason.llm.seat_plugins import ensure_seeded;from deepreason.llm.seat_sections import resolve_section_plugin;ensure_seeded();T=lambda l:{resolve_section_plugin(e.plugin_id,e.plugin_version).section_id:e for e in l.entries};j=T(C);r=T(R);a=j['scratch-advisory-context']; b=j['school-stance'];assert a.droppable is False and a.compressible is False and a.priority==7, a;assert b.droppable is False and b.compressible is True and b.min_tokens==24 and b.priority==5, b"`
