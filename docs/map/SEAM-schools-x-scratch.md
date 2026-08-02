<!-- DR-SEAM-schools-x-scratch -->
Verified-at: 08dcdf3c
Verify: python tools/docs_verify.py
Owns: src/deepreason/scratch/conjecture.py, src/deepreason/rules/conj.py, src/deepreason/scheduler/scheduler.py, src/deepreason/workflow/conjecture_recovery.py
Sides: DR-CON-schools, DR-SUB-scratch

# Schools x scratchpad

## The agreement

A school promises the scratchpad exactly one thing: an identifier. Not a stance,
not a weight, not a lineage — the bare string `school-<n>`, and only at the
moment a conjecture context is planned. The scratchpad promises the school
three things in return. It will treat that identifier as a retrieval SEED, so
two schools looking at the same notes at the same fence get differently shuffled
views of one shared pad. It will stamp the identifier onto the plan and onto the
durable call receipt, so a rendered context can never be replayed as another
school's. And it will keep the identifier out of every stored record — no block,
link, cluster, guide, attention receipt or proposal carries a school, because
the pad is one workshop that all schools write into and all schools read from.

The two sides therefore meet at exactly one seat: `conjecturer`. Conjecture is
where conditioning belongs, so conjecture is where the workshop is opened.
Criticism is where status is decided, so criticism gets a school and no notes at
all. That asymmetry is the whole design: islands in conjecture (schools) plus a
commons in imagination (one pad) plus a school-blind, scratch-blind authority
chain (criticism, trial, warrants, edges). `DR-CON-schools` states why schools
grant no status; `DR-SUB-scratch` states why notes ground nothing. This seam is
where those two guarantees are enforced together, and where breaking either one
would be easiest.

## Where it is expressed

| Site | File | Symbol | What it enforces |
|---|---|---|---|
| Seed derivation | `scratch/conjecture.py` | `_seed`, `_expansion_seed` | `school_id` is one field of the canonical payload hashed into `AttentionRequestV1.deterministic_seed` — the only way a school reaches selection |
| Plan binding | `scratch/conjecture.py` | `PlannedConjectureContextV1.school_id` | pattern `^school-(0\|[1-9][0-9]*)$`, default `None`; a stance string cannot occupy the field |
| Planning entry | `scratch/conjecture.py` | `plan_conjecture_context`, `plan_conjecture_context_expansion` | take `school_id: str \| None` and nothing else school-shaped; the expansion planner also refuses a `prior_plan` from another school |
| Replay re-validation | `scratch/conjecture.py` | `validate_conjecture_context_call` | rejects a receipt whose `school_id` differs from the caller's, before it touches scratch state |
| Rule-level pairing | `rules/conj.py` | `conj` (`execution_school_id` vs `conjecture_context_plan.school_id`) | `"conjecture context was planned for another school"` — the plan and the routed school must be one school, or the turn dies before dispatch |
| Prompt assembly | `llm/packs.py` | `render_conj_pack` (`school=`, `scratch_context=`) | the only renderer that holds both; stance is section 5 (compressible), advisory context is section 7 (never compressed, never dropped) |
| v6 aliasing | `rules/conj.py` | `render_v6_conjecture_context`, `plan_kind="scratch"` | the canonical render is swapped for `SCR_###` aliases and byte-accounted as one `ContextPackPlanV1` under the school's work preparation |
| Per-cycle wiring | `scheduler/scheduler.py` | `_plan_conjecture_context`, `_school_dict` | the planner is handed the bare allocated id; `_school_dict` (stance, weight, crossover) goes only to `conj`'s `school=` argument |
| Durable receipt | `ontology/event.py` | `ConjectureContextCallReceiptV1.school_id` | the school travels with the advisory-context proof onto the append-only log |
| v4/v5 replay authority | `workflow/replay.py` | `_validate_proposal` | `context_receipt.school_id != work.school_id` fails the root |
| v6 recovery authority | `workflow/conjecture_recovery.py` | `_authorized_provider_result` | a scratch-bearing exposure is re-validated against the frozen payload's `school_id` on every restart |
| Replay validation | `invariants.py` | `validate_conjecture_context` | a receipt with a `school_id` and no `SchoolRouteReceiptV1` on the same call is not a valid root |

`check: python -c "import inspect; from deepreason.llm import packs; assert {'school','scratch_context'} <= set(inspect.signature(packs.render_conj_pack).parameters); [ (lambda p: (_ for _ in ()).throw(AssertionError(n)) if p & {'school','scratch_context'} else None)(set(inspect.signature(getattr(packs,n)).parameters)) for n in ('render_crit_pack','render_batch_crit_pack') ]"`

`check: python -c "from deepreason.scratch.conjecture import _seed, _expansion_seed as e; assert len({_seed('0'*64,'P',None,3,3), _seed('0'*64,'P','school-0',3,3), _seed('0'*64,'P','school-1',3,3)}) == 3; assert e('0'*64,'P','school-0','sha256:'+'0'*64,'sha256:'+'1'*64) != e('0'*64,'P','school-1','sha256:'+'0'*64,'sha256:'+'1'*64)"`

`check: python -c "import pytest; from pydantic import ValidationError; from deepreason.ontology.event import ConjectureContextCallReceiptV1 as R; from deepreason.scratch.conjecture import PlannedConjectureContextV1 as P; from deepreason.workflow.models import WorkOrderEnvelopeV1 as W; b=dict(manifest_digest='a'*64, problem_id='P', formal_fence_seq=3, scratch_fence_seq=3, selection_receipt_ref='sha256:'+'1'*64, advisory_context_ref='sha256:'+'2'*64, render_receipt_ref='3'*64, rendered_context_ref='4'*64); R(**b, school_id='school-0'); assert all(pytest.raises(ValidationError, R, **b, school_id=v) for v in ('counterexample first','School-0','school-00','')); assert all(m.model_fields['school_id'].default is None for m in (P,R,W))"`

`check: python -c "import pytest; from deepreason.ontology.event import ConjectureContextCallReceiptV1 as R; from deepreason.scratch.conjecture import validate_conjecture_context_call as v; r=R(manifest_digest='a'*64, problem_id='P', school_id='school-0', formal_fence_seq=3, scratch_fence_seq=3, selection_receipt_ref='sha256:'+'1'*64, advisory_context_ref='sha256:'+'2'*64, render_receipt_ref='3'*64, rendered_context_ref='4'*64); k=dict(manifest_digest='a'*64, problem_id='P', scratch_aliases={}, provider_prompt=b''); assert all('belongs to another school' in str(pytest.raises(ValueError, v, None, r, school_id=s, **k).value) for s in ('school-1', None))"`

`check: grep -q "conjecture context was planned for another school" src/deepreason/rules/conj.py && grep -q "context_receipt.school_id != work.school_id" src/deepreason/workflow/replay.py && grep -q "def validate_conjecture_context(" src/deepreason/invariants.py && grep -q "school context has no matching route receipt" src/deepreason/invariants.py`

### The pad is shared, not partitioned

One scratchpad serves every school. A note written during `school-3`'s turn is
an ordinary retrieval candidate for `school-0` on the next cycle, because
nothing in the record says who wrote it in school terms. The school changes the
selection SEED and therefore tie-breaks and exploratory draws; it does not change
the candidate set. Below, three plans over one block at one fence: identical
`final_order`, three distinct request hashes.

`check: python -c "import sys,tempfile,pathlib; sys.path.insert(0,'tests'); from deepreason.harness import Harness; from deepreason.scratch.service import ScratchService; from deepreason.scratch.conjecture import plan_conjecture_context as P; import test_conjecture_scratch_context_v4 as T; h=Harness(pathlib.Path(tempfile.mkdtemp())/'run'); p=T._seed(h); s=ScratchService(h); T._relevant_block(s,p); m=T._manifest(T._config()); f=h._next_seq-1; pl=[P(s,problem=p,school_id=i,manifest_digest=m.sha256,scratch_policy=m.scratch_policy,context_policy=m.control_plane_policy.conjecture_context,formal_fence_seq=f,scratch_fence_seq=f) for i in (None,'school-0','school-1')]; assert len({tuple(x.attention_pack.selection_receipt.final_order) for x in pl})==1; assert len({x.attention_pack.selection_receipt.request_hash for x in pl})==3; assert [x.school_id for x in pl]==[None,'school-0','school-1']"`

The recorded evidence agrees. In the committed selfstudy root
`completed-epoch3-run-9175f0ec` four schools consumed advisory context across
seven distinct seeds; `school-0` and `school-1` selected the identical five
blocks, and every school's selection is a subset of `school-3`'s thirteen.

`check: python -c "import json,pathlib,collections; R=pathlib.Path('experiments/live_research_2026-07-29/selfstudy/runs/completed-epoch3-run-9175f0ecb055e57455af3c50df153c5a'); recs={r['id']: r['data'] for r in (json.loads(p.read_text()) for p in (R/'objects'/'scratch-attention-receipt').rglob('*') if p.is_file())}; ctx=[e['llm']['conjecture_context'] for e in (json.loads(l) for l in (R/'log.jsonl').open()) if (e.get('llm') or {}).get('conjecture_context')]; by=collections.defaultdict(set); seeds=set(); [(by[c['school_id']].update(recs[c['selection_receipt_ref']]['final_order']), seeds.add(recs[c['selection_receipt_ref']]['deterministic_seed'])) for c in ctx]; assert sorted(by)==['school-0','school-1','school-2','school-3']; assert len(seeds)==7; assert by['school-0']==by['school-1'] and by['school-0'] < by['school-3']"`

### The fence sequences without reading

Both sides carry `scratch_fence_seq`, and on every conjecture and criticism
record it equals `formal_fence_seq` — one log prefix, named twice. The criticism
side holds the field and nothing else scratch-shaped: it books its transaction
against the scratch log's position without ever opening it. Three records refuse
a split fence at construction, so a transaction cannot be authored against a
formal state and a different scratch state.

`check: grep -q "formal and scratch context fences must name one event prefix" src/deepreason/scratch/conjecture.py && grep -q "conjecture work requires one formal/scratch state fence" src/deepreason/workflow/models.py && grep -q "transactional work requires one immutable state fence" src/deepreason/workflow/transaction.py && test "$(grep -c "scratch_fence_seq=fence" src/deepreason/rules/crit.py)" -eq 2`

## What is deliberately absent

**Nothing scratch-derived reaches criticism, the trial, warrants or attack
edges.** This is the operator's R5/R6 in
`experiments/2026-08-01-change-prose-can-refute/REQUEST.md`: "the scratchpad
authority chain needs to be completely separate from conjecture/criticism
adjudication... they shouldn't exist together." R5/R6 closed an open question in
the negative — the tranche was heading toward exposing scratch to the critic as
the reading of R3, and was ruled out. The separation is pinned four ways: no
`deepreason.scratch` import anywhere in `rules/crit.py` or `informal/trial.py`
(walked as an AST, so a function-local import cannot hide), no `scratch_context`
parameter on either criticism renderer, and no scratch import in
`rules/warrants.py` or `adjudication/edges.py`.

`check: python -m pytest tests/test_prose_refutation_boundaries.py -q -k "the_criticism_rule_imports_no_scratch_module or the_criticism_rule_touches_scratch_only_as_an_ordering_fence or the_criticism_pack_cannot_be_given_scratch or the_defended_trial_imports_no_scratch_module or no_scratch_identifier_reaches_a_warrant_or_an_attack_edge"`

**Criticism has no slot a scratch context could occupy.** The v4/v5 conjecture
work order (`WorkOrderEnvelopeV1`) carries `advisory_context_ref` and is typed
`Literal[WorkflowTaskKind.CONJECTURE]`; the v6 `WorkPreparationV1` that also
serves `CRITICISM` has no such field at all. In the rule itself, every context
plan `crit.py` builds is `plan_kind="dossier"` — frozen evidence, never the
workshop — while `conj.py` is the only rule that builds a `"scratch"` plan.

`check: test "$(grep -o 'plan_kind="[a-z_]*"' src/deepreason/rules/crit.py | sort -u)" = 'plan_kind="dossier"' && grep -q 'plan_kind="scratch"' src/deepreason/rules/conj.py`

`check: python -c "from deepreason.workflow.transaction import WorkPreparationV1 as K; from deepreason.workflow.models import WorkOrderEnvelopeV1 as W, WorkflowTaskKind as T; import typing; assert 'advisory_context_ref' in W.model_fields and W.model_fields['task_kind'].annotation == typing.Literal[T.CONJECTURE]; assert 'advisory_context_ref' not in K.model_fields and 'school_id' not in K.model_fields; assert K.model_fields['task_kind'].annotation is T"`

**The scratchpad does not know what a school IS.** `scratch/conjecture.py` is
the only module under `scratch/` in which the word appears, and it appears only
as an opaque id. Nothing under `scratch/` imports `deepreason.capture`, so the
stance library, the roster, `allocate` and `reseed` are unreachable from the
pad. A retrieval channel therefore cannot be written that prefers a school's own
notes, because the channel has no way to ask.

`check: grep -q "school_id" src/deepreason/scratch/conjecture.py && ! grep -rl "school" src/deepreason/scratch --include=*.py | grep -qv "conjecture.py"`

`check: ! grep -rq "deepreason\.capture" src/deepreason/scratch/ && grep -q "^STANCE_LIBRARY" src/deepreason/capture/schools.py && grep -q "def allocate" src/deepreason/capture/schools.py`

**Stance text never crosses.** The school dict handed to `conj` carries `id`,
`stance_text`, `weight` and `crossover`; only `id` continues into the planner.
Retrieval cannot be steered by what a school BELIEVES — the seed sees an
identifier, and the identifier's pattern would reject prose anyway.

`check: python -c "import inspect; from deepreason.scratch import conjecture as c; ps=[inspect.signature(f).parameters for f in (c.plan_conjecture_context, c.plan_conjecture_context_expansion)]; assert all(p['school_id'].annotation=='str | None' for p in ps); assert not [k for p in ps for k in p if 'stance' in k or 'weight' in k or k=='school']; assert 'school' not in inspect.signature(c._focus_blocks).parameters"`

**The selection machinery contains no school-shaped concept.** `attention.py` —
`_candidates`, `_apply_channel_limits`, `_final_order`, `AttentionRequestV1`,
`AttentionPolicyV1` — never mentions a school. Every candidate comes from
`service.state.blocks` unfiltered. This is a tripwire rather than a stylistic
rule: the first line that names a school in the selector is the line that turns
the commons into per-school silos.

`check: python -c "import inspect; from deepreason.scratch import attention; from deepreason.scratch.attention import AttentionRequestV1 as Q, AttentionPolicyV1 as Y; assert 'school' not in inspect.getsource(attention); assert not [k for k in list(Q.model_fields)+list(Y.model_fields) if 'school' in k]"`

**A stored note records no school, and an artifact records no note.** The
reference arrow is one-way: `ScratchProvenanceV1.formal_artifact_refs` lets a
note name the formal object it was aimed at, and `Provenance` on an artifact
records the school that generated it and nothing about the pad. Neither the
draft container the model fills in nor the block body has anywhere to put a
school. Two consequences follow, and both are load-bearing: retrieval cannot be
partitioned after the fact, and a scratch identifier cannot ride into formal
state on a provenance field.

`check: python -c "from deepreason.scratch.models import ScratchProvenanceV1 as S, ScratchBlockBodyV1 as B; from deepreason.scratch.proposals import ScratchProposalV1 as D; from deepreason.ontology.artifact import Provenance as A; assert set(S.model_fields)=={'actor','origin','source_refs','formal_artifact_refs'}; assert not [k for m in (B,D) for k in m.model_fields if 'school' in k]; assert 'school' in A.model_fields and not [k for k in A.model_fields if 'scratch' in k]"`

## How to change it

Order matters because the school id is frozen into an append-only receipt long
before replay reads it back.

1. **Decide which authority you are touching.** Retrieval conditioning (which
   notes a school sees) is ordinary work. Anything that would let a note reach
   criticism, the trial, a warrant or an attack edge is refused before design —
   `DR-SUB-scratch`'s `advisory_non_grounding` boundary and R5/R6 both bar it,
   and overturning a pinned negative assertion is an operator's call.
2. **Change `scratch/conjecture.py` first, and only its planning functions.**
   `PlannedConjectureContextV1`'s field set is what the plan/receipt pair is
   built from; adding a field there means adding it to
   `ConjectureContextCallReceiptV1` in `ontology/event.py`, which is an event
   format. Read `DR-INV-frozen-surfaces` before you do: old roots must still
   verify.
3. **Move the three school checks together.** `conj`'s plan/execution pairing,
   `validate_conjecture_context_call`, and `replay._validate_proposal` all
   compare a receipt's school against an authority. Changing one and not the
   others produces a run that dispatches and then fails its own replay.
4. **Then the prompt.** `render_conj_pack` is the only renderer that may gain
   scratch material. If a change makes the criticism pack want it, the change is
   wrong.
5. **Re-run the negative assertions before the positive ones.** They are fast
   and they are the ones that encode decisions:
   `tests/test_prose_refutation_boundaries.py` (0.1 s) fails the instant scratch
   touches the authority chain. Then
   `tests/test_conjecture_scratch_context_v4.py` for the plan/commit lifecycle,
   `tests/test_v6_conjecture_scratch_consumption.py` for the v6 exposure and its
   restart-time re-authorization, and `tests/test_v6_context_continuation.py`
   for school-bound expansion.
6. **Finish with the root sweep.** A change to a reader or a guard here changes
   how recorded roots verify. `DR-INV-frozen-surfaces` names the instrument.

`check: python -m pytest tests/test_v6_conjecture_scratch_consumption.py::test_recovery_rejects_scratch_exposure_without_durable_context_authority tests/test_conjecture_scratch_context_v4.py::test_scratch_handles_never_enter_formal_state_or_grounding -q`

## Traps

- **26 files mention both sides; four carry the agreement.** `grep -rl school`
  intersected with `grep -l scratch` returns 26 modules today, including
  `config.py`, `cli/main.py` and `signals.py`, which name both and mediate
  neither. Starting from grep costs a day; the `Owns:` line above is the answer.
- **The scheduler passes two different school values on the same line of work.**
  `_plan_conjecture_context(problem, school_id)` receives the raw allocated id,
  while `conj` receives `school_id if school_id in school_leases else None`.
  They agree today only because `resolve_school_role_lease` either returns a
  lease or raises, so every assigned school is a key in `school_leases`. Make it
  return `None` for some mode and the plan will carry a school the turn does
  not, and `conj` will refuse the plan it was just handed.
`check: grep -q "context_plan = self._plan_conjecture_context(problem, school_id)" src/deepreason/scheduler/scheduler.py && grep -q "school_id if school_id in school_leases else None" src/deepreason/scheduler/scheduler.py && grep -q "def _plan_conjecture_context(self, problem, school_id: str | None):" src/deepreason/scheduler/scheduler.py`
- **The v4/v5 replay school-context guard has no test behind it.** Deleting
  `or context_receipt.school_id != work.school_id` from
  `workflow/replay.py::_validate_proposal` left 712 tests green under
  `python -m pytest tests/ -n 4 -k "replay or workflow or scratch or context or
  school"` (measured 2026-08-02, mutation reverted). The v6 path IS covered —
  `test_recovery_rejects_scratch_exposure_without_durable_context_authority`
  fails immediately — so the gap is on the pre-v6 envelope only. Treat that
  guard as protected by the root sweep, not by the gate.
- **`school-blind` and `school-scoped` describe different things here.** The
  criticism PROMPT is blind to the target's school but deliberately names the
  critic's own school and stance (`DR-CON-schools`). The scratchpad is the
  reverse: it is school-scoped at the receipt and school-blind at the store.
  Reading either as "schools are absent" leads to the wrong change.
- **The advisory section cannot be compressed away.** `scratch-advisory-context`
  is `droppable=False, compressible=False`, because the committed receipt asserts
  the pack contains those exact bytes once
  (`final_conjecture_pack.count(receipt_text) != 1` raises). The school stance
  section beside it IS compressible. A budget change that starts compressing
  section 7 breaks the receipt, not the prompt.
- **A `str` operation on the pack demotes `AllocatedPack`.** The v6 alias swap
  re-wraps the result deliberately; without the wrapper the adapter re-applies an
  aggregate prefix clip to an already-budgeted pack and cuts the sealed advisory
  context mid-JSON out of the dispatched prompt. The comment in `rules/conj.py`
  records this; do not "simplify" the re-wrap.
- **Historical views can neither plan nor commit.** All three Conj planning
  functions re-check writability and raise `ScratchReadOnly`, so a school-scoped
  plan cannot be built off a replayed prefix. Planning from a historical view
  would append events into a root that was already verified.
