<!-- DR-SEAM-rules-x-scratch -->
Verified-at: 08dcdf3c
Verify: python tools/docs_verify.py
Owns: src/deepreason/rules/conj.py, src/deepreason/rules/crit.py, src/deepreason/scratch/conjecture.py
Sides: DR-SUB-rules, DR-SUB-scratch

# rules x scratch

## The agreement

The scratchpad offers the rules a bounded, deterministically selected, immutable
view of what the model has been thinking: sealed to one event-log prefix,
rendered behind opaque handles, and carrying no warrant, status, attack edge or
support for one. The rules promise in return that exactly ONE move consumes it.
The workshop is offered to the move that invents and withheld from the move that
judges: `conj` receives it as a pack section and may write back into it;
`crit` receives one integer, the fence that orders its transaction against the
scratch log, and reads nothing. Both sides fix that fence identically to the
formal one, so a planned context is valid only at the sequence it was planned at
and any intervening event invalidates the plan rather than silently changing
what the model saw. The write-back direction is bounded by the read direction:
a turn may name only handles that turn's own exposure receipt records, and a
scratch write that fails is a typed component diagnostic, never a cancelled
turn. The dependency arrow matches the epistemic one — `rules/` imports
`scratch/`, and `scratch/` imports nothing from `rules/`, so the workshop cannot
reach the machinery that decides what stands.

Exactly one module on each side carries this, and the whole rules-side surface
of the scratchpad is `conj.py`.
`check: test "$(grep -rl "deepreason\.scratch" --include=*.py src/deepreason/rules | wc -l)" -eq 1 && ! grep -rq "deepreason\.rules" --include=*.py src/deepreason/scratch/ && grep -q "^def plan_conjecture_context(" src/deepreason/scratch/conjecture.py && grep -q "deepreason.scratch.conjecture import" src/deepreason/rules/conj.py`

## Where it is expressed

| Site | File | Symbol | What it enforces |
|---|---|---|---|
| Plan, at the head | `rules/conj.py` | `plan_conjecture_context`, `plan_conjecture_context_expansion`, called at `plan_fence = harness._next_seq - 1` | the read direction opens at the current log head and nowhere else |
| Fence identity | `scratch/conjecture.py` | `PlannedConjectureContextV1._parts_share_one_fence_and_selection` | one prefix names both logs; the pack, the advisory context and the render receipt all name one selection receipt |
| Model-facing rename | `scratch/conjecture.py` | `render_v6_conjecture_context`, `_v6_aliases_for_render_receipt` | local `B*/C*/L*/G*` handles become `SCR_###` before the provider sees them |
| Pack section | `llm/packs.py` | `render_conj_pack(scratch_context=...)` | scratch enters a pack only as a validated `RenderedScratchPackV1`, in one undroppable, uncompressible section |
| Absence by signature | `llm/packs.py` | `render_crit_pack`, `render_batch_crit_pack` | no parameter exists through which a caller could hand scratch to a criticism pack |
| Alias namespaces | `llm/wire.py` | `ConjecturerTurnWireContractV4.__init__`, `ConjecturerTurnWireContractV6._require_namespace` | `SRC_` formal, `SCR_` scratch, `SIM_` sealed inputs; overlap is refused at contract construction |
| Exposure ledger | `rules/conj.py` | `context_plan(plan_kind="scratch")` with `ContextNamespace.SCRATCH` items | every visible scratch handle is byte-accounted in the transaction's exposure receipt |
| Exactly-once, three points | `rules/conj.py`, `scratch/conjecture.py`, `llm/adapter.py` | `pack.count(canonical_scratch_text)`, `final_conjecture_pack.count(receipt_text)`, `prompt.count(advisory_text)` | the committed bytes reach the provider once, checked before dispatch rather than post hoc |
| Commit point | `scratch/conjecture.py` | `prepare_conjecture_context_call` / `commit_conjecture_context` | the receipt and its coverage progress become durable only immediately before dispatch |
| Write-back gate | `rules/conj.py` | `validate_proposal(..., visible_aliases=scratch_aliases, context_ref=exposure_ref)` then `admit_proposal(...)` with the same pair | the whole proposal resolves against what was actually shown BEFORE the first scratch event |
| Component isolation | `rules/conj.py` | `_v6_component_diagnostic(component="scratch", ...)` at `semantic_validation` and `materialization` | a rejected or half-written scratch proposal does not cancel the candidates in the same turn |
| The fence, and only the fence | `rules/crit.py` | `scratch_fence_seq=fence` in `_v6_transactional_batch_call` and `_v6_transactional_atomic_critic_call`, the two helpers `crit_argumentative_batch` dispatches through | criticism orders itself against the scratch log without reading it |
| Replay-side mirror | `workflow/conjecture_recovery.py` | scratch exposure ⟺ `call.conjecture_context`, then `validate_conjecture_context_call` | a recovered scratch-bearing provider result with no context authority is refused; owned by `DR-SUB-workflow`, but it re-derives THIS agreement |
| Replay validation | `invariants.py` | `validate_conjecture_context` | the context fence strictly precedes the call event it authorized |

The criticism side's total scratch surface is two fence assignments, each equal
to the formal fence at the same call.
`check: test "$(grep -c scratch src/deepreason/rules/crit.py)" -eq 2 && test "$(grep -c fence src/deepreason/rules/crit.py)" -eq 6 && test "$(grep -cE "^ +(formal|scratch)_fence_seq=fence,$" src/deepreason/rules/crit.py)" -eq 4 && test "$(grep -cE "^ +fence = max\(0, harness\._next_seq - 1\)$" src/deepreason/rules/crit.py)" -eq 2`

Scratch reaches a conjecture pack only through the typed record, in a section
the allocator may not drop or compress.
`check: grep -q "scratch_context = RenderedScratchPackV1.model_validate(scratch_context)" src/deepreason/llm/packs.py && grep -A 5 '"scratch-advisory-context",' src/deepreason/llm/packs.py | grep -q "droppable=False" && grep -q "^class RenderedScratchPackV1" src/deepreason/scratch/render.py`

The planned context carries one fence for both logs, matched to the attention
pack it was built from; a plan whose fence has moved cannot commit, a historical
view can neither plan nor commit at all, and `verify_root` re-checks on replay
that the fence precedes its call.
`check: grep -qE "^ +if self\.formal_fence_seq != self\.scratch_fence_seq:$" src/deepreason/scratch/conjecture.py && grep -q "formal and scratch context fences must name one event prefix" src/deepreason/scratch/conjecture.py && grep -qE "^ +if self\.attention_pack\.state_seq != self\.scratch_fence_seq:$" src/deepreason/scratch/conjecture.py && grep -q "attention pack does not match the scratch fence" src/deepreason/scratch/conjecture.py && test "$(grep -cE "^ +plan_fence = harness\._next_seq - 1$" src/deepreason/rules/conj.py)" -eq 2 && grep -qE "^ +if receipt\.formal_fence_seq >= event\.seq:$" src/deepreason/invariants.py && grep -q "context fence does not precede the call event" src/deepreason/invariants.py && python -m pytest tests/test_conjecture_scratch_context_v4.py::test_stale_plan_cannot_commit_and_a_fresh_rebuild_can tests/test_conjecture_scratch_context_v4.py::test_historical_views_can_neither_plan_nor_commit_context -q`

The sealed bytes are counted three times on the way to the provider: in the
pack, in the receipt, and in the finished prompt.
`check: grep -q "if pack.count(canonical_scratch_text) != 1:" src/deepreason/rules/conj.py && grep -q "if final_conjecture_pack.count(receipt_text) != 1:" src/deepreason/scratch/conjecture.py && grep -q "if prompt.count(advisory_text) != 1:" src/deepreason/llm/adapter.py && grep -q "advisory context bytes are absent or duplicated before aliasing" src/deepreason/llm/adapter.py && python -m pytest tests/test_v6_conjecture_scratch_consumption.py::test_initial_v6_conjecture_commits_exact_model_facing_scratch_once -q`

Every visible handle is exposed under its own namespace in the transaction
ledger, so what the model saw is a typed record rather than an inference from
the prompt text; validation and admission are then given that same alias set and
that same exposure receipt, and an unknown reference is refused before any
scratch event.
`check: grep -q "namespace=ContextNamespace.SCRATCH," src/deepreason/rules/conj.py && grep -q 'plan_kind="scratch",' src/deepreason/rules/conj.py && grep -q 'SCRATCH = "scratch"' src/deepreason/workflow/transaction.py && test "$(grep -c "visible_aliases=scratch_aliases," src/deepreason/rules/conj.py)" -eq 2 && test "$(grep -c "context_ref=exposure_ref," src/deepreason/rules/conj.py)" -eq 2 && python -m pytest tests/test_v6_scratch_atomicity.py::test_unknown_reference_is_rejected_before_any_scratch_event -q`

A scratch component that fails is diagnosed in two typed phases; the turn's
valid candidates still commit.
`check: test "$(grep -c 'component="scratch",' src/deepreason/rules/conj.py)" -eq 2 && python -c "import ast,pathlib;t=ast.parse(pathlib.Path('src/deepreason/rules/conj.py').read_text());C=[(h,c) for n in ast.walk(t) if isinstance(n,ast.Try) for h in n.handlers for c in ast.walk(h) if isinstance(c,ast.Call) and getattr(c.func,'id','')=='_v6_component_diagnostic' and any(k.arg=='component' and getattr(k.value,'value',None)=='scratch' for k in c.keywords)];assert sorted(getattr(k.value,'value',None) for _,c in C for k in c.keywords if k.arg=='phase')==['materialization','semantic_validation'],C;assert not [r for h,_ in C for r in ast.walk(h) if isinstance(r,ast.Raise)],'a scratch component handler re-raises and cancels the turn'" && python -m pytest tests/test_v6_conjecture_component_atomicity.py::test_valid_candidate_and_invalid_optional_scratch_complete_partially -q`

Recovery refuses the two mismatched shapes: scratch exposure without a context
receipt, and a context receipt without scratch exposure.
`check: grep -q "scratch-bearing provider result has no conjecture context authority" src/deepreason/workflow/conjecture_recovery.py && grep -q "provider call claims scratch context absent from transaction exposure" src/deepreason/workflow/conjecture_recovery.py && grep -q "^def validate_conjecture_context_call(" src/deepreason/scratch/conjecture.py && python -m pytest tests/test_v6_conjecture_scratch_consumption.py::test_recovery_rejects_scratch_exposure_without_durable_context_authority -q`

## What is deliberately absent

**Criticism is given no scratch content, and the refusal is structural.** It is
not that no caller currently passes it — no parameter exists to pass. This is
the operator's R5/R6 requirement: the scratchpad authority chain and the
conjecture/criticism adjudication chain must not exist together. Reading the
absence as an oversight and "wiring the critic to the workshop" is the specific
mistake this section exists to prevent.
`check: python -c "import inspect;from deepreason.llm import packs;bad=[n for n in dir(packs) if n.startswith('render_') and 'scratch_context' in inspect.signature(getattr(packs,n)).parameters];assert bad==['render_conj_pack'],bad" && python -m pytest tests/test_prose_refutation_boundaries.py::test_the_criticism_pack_cannot_be_given_scratch -q`

**Criticism cannot WRITE to the workshop either.** The conjecturer turn contract
takes `scratch_aliases` and its wire model carries `scratch_proposal`; no critic
contract takes aliases and no critic output model has any scratch field at all.
The workshop belongs to the move that invents, in both directions.
`check: python -c "import inspect;from deepreason.llm import wire;N=('BatchCriticWireContractV2','CriticWireContract','AtomicCriticWireContractV1');S=[inspect.signature(getattr(wire,n).__init__).parameters for n in N];assert 'scratch_aliases' in inspect.signature(wire.ConjecturerTurnWireContractV6.__init__).parameters;assert 'scratch_proposal' in wire.ConjecturerTurnWireV6.model_fields;assert not [k for p in S for k in p if 'scratch' in k];assert not [k for p in S for k,v in p.items() if v.kind in (v.VAR_KEYWORD,v.VAR_POSITIONAL)],'a variadic critic __init__ can absorb scratch_aliases without naming it';assert not [a for n in N for a in dir(getattr(wire,n)) if 'scratch' in a],'a critic contract exposes a scratch attribute';assert not [f for m in (wire.ArgumentativeCriticOutput,wire.BatchCriticOutput) for f in m.model_fields if 'scratch' in f]"`

**The separation is enforced by an AST walk, not a header grep**, because a
function-local `import deepreason.scratch...` inside `crit.py` would satisfy a
naive check and still couple the two. The same walk covers `informal/trial.py`,
which is where a sustained prose case actually changes a status, and
`rules/warrants.py` and `adjudication/edges.py`, which are the narrowest part of
the chain: a warrant's referents are an artifact, a commitment, a validity node
and a trace blob, never a scratch object.
`check: python -m pytest tests/test_prose_refutation_boundaries.py::test_the_criticism_rule_imports_no_scratch_module tests/test_prose_refutation_boundaries.py::test_the_criticism_rule_touches_scratch_only_as_an_ordering_fence tests/test_prose_refutation_boundaries.py::test_the_defended_trial_imports_no_scratch_module tests/test_prose_refutation_boundaries.py::test_no_scratch_identifier_reaches_a_warrant_or_an_attack_edge -q`

**An unresolved question is not a problem.** `ScratchProposalV1` has an
`unresolved_questions` field and `scan_spawns` mints problems from seven
structural triggers over the formal graph — successor, discrimination,
remove-arbitrariness, explanation-debt, connection, integration, research. (The
`SpawnTrigger` enum carries two more that `scan_spawns` never mints: `SEED` is
the operator's question, and `AUDIT_CRITIC` is raised by the response ladder in
`informal/appellate.py`.) No edge joins the two, and none should. A spawn is a
commitment to spend the run's budget; a question in the workshop is explicitly
allowed to be idle, wrong, or unanswerable. The same holds for the anti-relapse
gate, which compares formal verdict vectors and never a note.
`check: python -c "import ast,pathlib;t=ast.parse(pathlib.Path('src/deepreason/rules/spawn.py').read_text());fn=[n for n in ast.walk(t) if isinstance(n,ast.FunctionDef) and n.name=='scan_spawns'][0];m={n.attr for c in ast.walk(fn) if isinstance(c,ast.Call) and ast.unparse(c.func).endswith('spawn') for n in ast.walk(c) if isinstance(n,ast.Attribute) and getattr(n.value,'id','')=='SpawnTrigger'};assert sorted(m)==['CONNECTION','DISCRIMINATION','EXPLANATION_DEBT','INTEGRATION','REMOVE_ARBITRARINESS','RESEARCH','SUCCESSOR'],sorted(m)" && test "$(grep -c scratch src/deepreason/rules/guards/anti_relapse.py)" -eq 0 && grep -q "^def verdict_vector(" src/deepreason/rules/guards/anti_relapse.py`

**Nothing that crosses the seam leaves a mark on the formal graph.** A scratch
event's `state_diff` is empty, no scratch handle or receipt id appears in any
formal diff or in an admitted artifact's interface, grounding and evidence
lambdas do not move, and an outright self-contradictory note is admitted to
`scratch_state` while `harness.state` is byte-identical before and after.
`check: python -m pytest tests/test_conjecture_scratch_context_v4.py::test_scratch_handles_never_enter_formal_state_or_grounding tests/test_v6_scratch_atomicity.py::test_contradictory_speculation_is_admitted_only_to_scratch -q && ! grep -q scratch src/deepreason/rules/spawn.py && grep -q "^def scan_spawns(" src/deepreason/rules/spawn.py && grep -q "unresolved_questions" src/deepreason/scratch/proposals.py`

**Alias namespaces do not overlap, and that is a refusal rather than a
convention.** Both the v4/v5 and v6 contracts reject a scratch alias that
collides with a formal one at construction, because a collision would let a
speculative note resolve as a formal artifact reference in a `requested_refs`
list.
`check: grep -q "formal and scratch alias namespaces must not overlap" src/deepreason/llm/wire.py && grep -q "v6 visible alias namespaces must be disjoint" src/deepreason/llm/wire.py && grep -q '_require_namespace(scratch, "SCR")' src/deepreason/llm/wire.py`

**The fence on the criticism side is NOT an absence.** It is present and
deliberate: a criticism transaction still has to be ordered against the scratch
log, or a concurrent scratch write could not be placed relative to it. Deleting
`scratch_fence_seq` from `crit.py` to "complete the separation" removes ordering,
not coupling.

## How to change it

The order matters because the receipt is content-addressed and three parties
compare it.

1. **Read `DR-INV-frozen-surfaces` first.** `ScratchPolicy` and its
   `attention_policy()` are manifest surfaces, so any change to pack size,
   channels or roles moves every qualification subject digest. A per-run mode
   goes on `Config`, never on the manifest.
2. **Decide which direction you are changing.** Read (scratch → pack) and write
   (turn → scratch) are separately gated and separately recovered; a change that
   touches only one must leave the other's receipts byte-identical.
3. **Change the plan record before the call sites.** `PlannedConjectureContextV1`
   is the contract. Adding a field means its `model_validator` must decide what
   the field's absence means for a plan recorded before you existed, and
   `validate_conjecture_context_call` must re-derive it from the historical view
   at the fence — otherwise the change invalidates existing replay-valid roots
   and is wrong by definition.
4. **Move the exposure and the recovery together.** The scratch exposure items
   in `conj.py` and the biconditional in `workflow/conjecture_recovery.py` are
   one agreement in two files. Change one alone and a crash mid-turn becomes
   unrecoverable, which is a failure mode no test in the read path will surface.
5. **Keep the exactly-once chain intact.** If you insert anything into the pack
   after allocation, it must be separately byte-accounted in a transaction
   context plan and the pack must remain an `AllocatedPack` (see Traps).
6. **Never widen the criticism side to close the asymmetry.** The asymmetry is
   the design. Overturning it is an operator's call, not an implementer's.

What breaks first, in the order you will see it: `ConjectureContextStale` if you
plan at the wrong fence; `"final Conj pack must contain the exact advisory
context once"` if you edit the pack after sealing;
`"rendered provider request must contain the exact advisory context once"` if a
presentation transform runs over an allocated pack; then, only on a later run,
`verify_root`'s `conjecture-context` failure — the expensive one, because by
then the root is committed.

The tests that will catch you, in the order they run cheapest first:
`tests/test_prose_refutation_boundaries.py` (the negative side, 0.1 s),
`tests/test_conjecture_scratch_context_v4.py` (v4/v5 read direction),
`tests/test_v6_conjecture_scratch_consumption.py` (v6 read direction and
recovery), `tests/test_v6_scratch_atomicity.py` and
`tests/test_v6_scratch_authoring_transactions.py` (write direction),
`tests/test_v6_conjecture_component_atomicity.py` (partial completion).

## Traps

- **`str` operations demote the `AllocatedPack` marker.** `conj.py` swaps the
  canonical scratch text for the v6 aliased render with `pack.replace(...)` and
  re-wraps the result. Without the re-wrap the adapter re-applies the profile's
  aggregate prefix clip to a pack that `PackIR` had already budgeted
  section-by-section, cutting the sealed advisory context mid-JSON out of the
  dispatched prompt. The comment above the re-wrap in `conj.py` is the record of
  this; every post-allocation insertion below it is separately byte-accounted.
`check: test "$(grep -c "pack = AllocatedPack(" src/deepreason/rules/conj.py)" -eq 3 && grep -q "class AllocatedPack(str):" src/deepreason/llm/packs.py && grep -q "pack_is_allocated = isinstance(pack, AllocatedPack)" src/deepreason/llm/adapter.py`
- **Render-receipt handle maps reload key-sorted, and this seam reads them
  twice.** The receipt is persisted through `canonical_json`, whose sorted keys
  interleave `B10` between `B1` and `B2`. `validate_conjecture_context_call`
  already handles this for the ORDER comparison — it uses `ordered_refs("block")`
  and says so in a comment. The ALIAS derivation beside it,
  `_v6_aliases_for_render_receipt`, numbers `SCR_###` by mapping iteration order
  instead, so a receipt reloaded from a blob and the in-memory receipt the write
  path holds produce different alias tables once a pack reaches ten handles of
  one kind. **Residue: this is a code-reading finding plus the unit probe below,
  not an observed live failure.** No recorded root has been shown to hit it, and
  the seam's own tests render single-block packs. If you touch either function,
  reproduce at 10+ handles before trusting either. Related: `DR-SUB-scratch`'s
  trap, and selfstudy `run-9175f0ec`, where the same reload order produced
  spurious order violations in a different consumer.
`check: python -c "import hashlib;from deepreason.canonical import canonical_json;from deepreason.scratch.render import ScratchRenderReceiptV1;from deepreason.scratch.conjecture import _v6_aliases_for_render_receipt as A;h={'B%d'%i:'sha256:'+hashlib.sha256(str(i).encode()).hexdigest() for i in range(1,13)};r=ScratchRenderReceiptV1.create(state_seq=1,attention_receipt='sha256:'+'a'*64,block_handles=h,cluster_handles={},link_handles={},guide_handles={});q=ScratchRenderReceiptV1.model_validate_json(canonical_json(r.model_dump(mode='json',by_alias=True)));assert r.ordered_refs('block')==q.ordered_refs('block');assert A(r)[0]!=A(q)[0]"`
- **The guard you want is often not on the side you are editing.** A rule about
  what criticism may be given is enforced in the PACK SIGNATURE and the WIRE
  CONTRACT, not inside `crit.py`, because `crit.py` never had the opportunity in
  the first place. Searching `crit.py` for the enforcement and finding nothing is
  the expected result, not evidence that the boundary is unguarded.
- **A refusal raised from inside a nested draft item kills the whole turn.** In
  turmite `run-bc3e8797b3e0609eddb324299c8257bd` a one-block proposal had no
  legal `to_ref`; the old `_not_a_self_link` validator rejected the entire
  conjecture turn, candidates and all, and the run died at cycle 0 discarding a
  correct refutation. Fixed: `_drop_self_links` discards on the container. The
  seam-level lesson survives the fix — a scratch validator that raises rather
  than discards converts an advisory component into a turn-killer, which is
  exactly the coupling the `component="scratch"` diagnostics exist to prevent.
`check: grep -q "def _drop_self_links" src/deepreason/scratch/proposals.py && ! grep -q "_not_a_self_link" src/deepreason/scratch/proposals.py && python -m pytest tests/test_scratch_contracts.py::test_a_self_link_is_dropped_rather_than_killing_the_whole_turn -q`
