<!-- DR-CON-packs-and-token-economy -->
Verified-at: b41c5cf10
Verify: python tools/docs_verify.py
Owns: src/deepreason/llm/packs.py, src/deepreason/packs/allocate.py, src/deepreason/packs/ir.py, src/deepreason/llm/budget.py, src/deepreason/llm/profiles.py, src/deepreason/llm/adapter.py, src/deepreason/rules/crit.py
Seams: 
Seams-undocumented: manifest x packs-and-token-economy, packs-and-token-economy x rules, packs-and-token-economy x schools, packs-and-token-economy x scratch, packs-and-token-economy x workflow

# Packs and the token economy — what the model is shown, and what it costs

## What it is

A *pack* is the model-facing body of one provider call: problem, criteria,
neighbourhood, target, directive, assembled deterministically from the
epistemic state. Packs are where a run's whole state meets a finite context
window, so every pack is a budgeting decision as well as a presentation one —
and the two must not be confused, because a byte cut for cost is
indistinguishable, from the model's side, from a byte that never existed. The
answer is a section-aware IR: a pack declares its parts with priorities and
per-section droppable/compressible flags, and the allocator spends budget on
the optional parts while retaining the mandatory ones in full. Downstream the
assembled *prompt* — role template + schema + example + aliases + pack — is
checked against the frozen route's context window and against the provider
budget meter, both of which refuse rather than truncate. Ordering, compression
and profiles are presentation only; the one place presentation could have
become epistemic, clipping a critic's target, was closed by making that
section mandatory.

## Where it lives

| Aspect | File | Symbol |
|---|---|---|
| What a section may declare | `src/deepreason/packs/ir.py` | `PackSection`, `PackIR` |
| The allocation algorithm | `src/deepreason/packs/allocate.py` | `allocate_pack` |
| Allocation token estimate (chars/4) | `src/deepreason/packs/allocate.py` | `approximate_tokens` |
| Head/tail compression of one section | `src/deepreason/packs/allocate.py` | `_bounded_view` |
| Per-section accounting, overflow | `src/deepreason/packs/allocate.py` | `AllocationResult.accounting`, `mandatory_overflow` |
| Section construction (pins `max_tokens` to the source, so a section never renders more than it has) | `src/deepreason/llm/packs.py` | `_pack_section` |
| Conjecture pack (15 section slots) | `src/deepreason/llm/packs.py` | `render_conj_pack` |
| Single-target criticism pack (10 section slots) | `src/deepreason/llm/packs.py` | `render_crit_pack` |
| Batch criticism pack — NOT on the IR | `src/deepreason/llm/packs.py` | `render_batch_crit_pack`, `_clip` |
| Auxiliary packs — NOT on the IR | `src/deepreason/llm/packs.py` | `render_experiment_pack`, `render_property_pack`, `render_cx_retry_pack` |
| "Already budgeted, do not re-clip" marker | `src/deepreason/llm/packs.py` | `AllocatedPack` |
| Section-size constants | `src/deepreason/llm/packs.py` | `NEIGHBOURHOOD_N`, `ATTACKERS_N`, `FOUNDATION_CHARS` |
| The frame slice's two halves, and their caps | `src/deepreason/calculus/render.py` | `render_frame_slice_context` (digest), `render_frame_crisis_context` (wounds + departures), `FRAME_SLICE_ATTACKERS_N`, `FRAME_SLICE_DEPARTURES_N`, `ARTICULATION_DIGEST_CHARS` |
| Sections whose absence is disclosed rather than silent | `src/deepreason/llm/packs.py` | `DISCLOSED_ON_DROP`, `_allocate_sections` |
| Presentation profiles and their budgets | `src/deepreason/llm/profiles.py` | `PROFILES`, `ProfileSpec.pack_budget` |
| Aggregate prefix clip (legacy path) | `src/deepreason/llm/profiles.py` | `clip_pack`, via `packs.apply_model_profile` |
| Profile → Config projection | `src/deepreason/llm/profiles.py` | `apply_profile_to_config` |
| Per-run pack target | `src/deepreason/config.py` | `Config.PACK_TOKEN_BUDGET` |
| School-prefix budget reservation | `src/deepreason/rules/crit.py` | `_conditioned_budget`, `_condition_pack` |
| Prompt assembly, profile application | `src/deepreason/llm/adapter.py` | `LLMAdapter._render_request` |
| Route envelope enforcement | `src/deepreason/llm/adapter.py` | `_enforce_request_envelope`, `RequestEnvelopeExceeded` |
| Frozen route capacity | `src/deepreason/run_manifest.py` | `Route.context_window_tokens` |
| Provider ceiling, reserve-settle | `src/deepreason/llm/budget.py` | `TokenMeter.reserve`, `Reservation.settle`, `Reservation.release` |
| Meter prompt bound (chars/3) | `src/deepreason/llm/budget.py` | `conservative_prompt_bound` |
| Transactional reservation bound | `src/deepreason/workflow/transaction_service.py` | `prompt_bound` |

## The rules it obeys

**A non-droppable, non-compressible section is retained in full, even when it
exceeds its target.** This is the mandatory-section rule and it is the reason
the IR exists: `allocate_pack` seeds such a section at its full source size
before any budget arithmetic runs, and the shortfall surfaces as
`mandatory_overflow` rather than as a cut.
`check: python -m pytest tests/test_pack_ir.py::test_mandatory_criteria_and_output_contract_are_never_clipped -q`

**So `target_tokens` is a target, not a ceiling.** A pack whose mandatory
sections alone exceed it renders oversize, with `allocated_tokens >
target_tokens`; the optional sections are merely all dropped first. An oversize
prompt is therefore a *transport* problem, refused downstream by the envelope
check — never a silently partial pack.
`check: python -c "from deepreason.packs import PackIR, PackSection, allocate_pack; s=PackSection(id='t', text_ref='inline:'+('x'*40000), priority=1, min_tokens=0, max_tokens=10000, droppable=False, compressible=False, cache_group='t'); r=allocate_pack(PackIR(profile='p', template_role='critic', target_tokens=100, sections=(s,))); assert r.allocated_tokens==10000 and r.mandatory_overflow==9900"`

**Allocation order is `(priority, id)`, not declaration order.** The id
tie-break is load-bearing in `render_crit_pack`: `target` and
`target-support-chain` both sit at priority 4, and the chain follows the
content it supports only because `"target" < "target-support-chain"`.
`check: grep -qF 'sorted(ir.sections, key=lambda section: (section.priority, section.id))' src/deepreason/packs/allocate.py`
`check: python -c "import ast,pathlib;T=ast.parse(pathlib.Path('src/deepreason/llm/packs.py').read_text());F={n.name:n for n in T.body if isinstance(n,ast.FunctionDef)};S=lambda k:{ast.literal_eval(c.args[0]):c.args[2].value for c in ast.walk(F[k]) if isinstance(c,ast.Call) and getattr(c.func,'id','')=='_pack_section'};j=S('render_conj_pack');r=S('render_crit_pack');assert len(j)==17 and len(r)==13;assert r['target']==r['target-support-chain']==4;assert j['frame-slice']==r['frame-slice']==j['frame-crisis']==r['frame-crisis']==4"`

**NO SILENT CAPS — a dropped section whose ABSENCE changes what the model may
DO is named in the pack.** `allocate_pack` cuts an unaffordable optional
section leaving no header and no placeholder, and "absence is the only signal"
is right for a neighbourhood and wrong for a citable-evidence legend: a pack
whose legend the budget cut is byte-indistinguishable from a run with no
admitted evidence in it. P4 measured that shape from the other side — 0 of 36
sub-problem prompts carrying citable blocks — and fixed the GATING; this is the
allocation half (Rung 6, R6). `DISCLOSED_ON_DROP` names the four sections whose
absence is reported (`citable-evidence-blocks`, `frozen-evidence-context`,
`premise-invitation`, `standing-attacks`), and `_allocate_sections` re-allocates
with a mandatory `context-withheld` notice until the notice names exactly what
that allocation cut. When nothing is cut the notice is ABSENT, not empty — an
always-present "withheld: none" line is the empty slot
`docs/RESEARCH_JUDGE_BLINDING_2026-08-22.md` measured as worse than a populated
one.

Convergence is MEASURED, not proved, and the distinction is recorded because
the obvious argument is wrong: the dropped set is not monotone in `remaining`,
since `allocate_pack` admits droppable sections greedily and `continue`s past
one that will not fit, so a smaller budget can afford a later small section it
could not afford before. At most three passes across 115 budgets from 1 to 799,
against a bound of `len(sections) + 1`.
`check: python -m pytest tests/test_frame_render.py::test_the_disclosure_loop_reaches_a_fixed_point tests/test_frame_render.py::test_a_dropped_citable_legend_is_disclosed_in_the_pack tests/test_frame_render.py::test_nothing_dropped_means_no_withheld_notice_at_all -q`
`check: python -c "from deepreason.llm.packs import DISCLOSED_ON_DROP; assert DISCLOSED_ON_DROP == {'citable-evidence-blocks','frozen-evidence-context','premise-invitation','standing-attacks'}, sorted(DISCLOSED_ON_DROP)"`

**Slow-changing sections precede volatile ones** so a provider prefix cache
bills the repeated head at the cached rate — problem context and commitment
schemas before the target, school stance before the neighbourhood. Pure
reordering, zero epistemic content; a dropped section leaves no header and no
placeholder, so absence is the only signal.
`check: python -m pytest tests/test_pack_prefix.py -q`

**NEGATIVE — a droppable section must never be declared non-compressible.**
`allocate_pack` admits a droppable section only when its whole `min_tokens`
fits; if that section is also exact it is then rendered at full source size and
its `take` is rewritten upward, overshooting the target with no accounting
signal. Every droppable section in `packs.py` is compressible — read off the
`_pack_section` call sites structurally, not by line adjacency, because a check
that greps for the forbidden pairing goes silently vacuous the moment the calls
are reformatted. The second check exhibits the overshoot.
`check: python -c "import ast,pathlib;T=ast.parse(pathlib.Path('src/deepreason/llm/packs.py').read_text());K=[{k.arg:getattr(k.value,'value',None) for k in c.keywords} for c in ast.walk(T) if isinstance(c,ast.Call) and getattr(c.func,'id','')=='_pack_section'];D=[k for k in K if k.get('droppable') is True];assert D and all(k.get('compressible') is True for k in D)"`
`check: python -c "from deepreason.packs import PackIR, PackSection, allocate_pack; s=PackSection(id='d', text_ref='inline:'+('x'*4000), priority=1, min_tokens=10, max_tokens=1000, droppable=True, compressible=False, cache_group='d'); r=allocate_pack(PackIR(profile='p', template_role='critic', target_tokens=50, sections=(s,))); assert r.allocated_tokens==1000 and r.mandatory_overflow==0"`

**NEGATIVE — the frame slice is never droppable, and its CRISIS half is never
compressible either.** For every consulted frame assertion whose σ admits the
problem, the pack carries the subject's articulation digest AND the subject's
standing attackers (§9.5, Rung 6) — "the frame ships its own crisis". These are
TWO sections, and the split is §9.5's own wording rather than a convenience:
only the articulation digest is described there as "compressed; expandable by
view".

- `frame-slice` — the digest. Non-droppable, compressible. The expansion is
  `deepreason standing --json`.
- `frame-crisis` — the standing attackers, the departure directive and what has
  already been declared. Non-droppable AND non-compressible, i.e. exact. It
  sorts before `frame-slice` on id, so the crisis leads.

Droppable would let budget pressure restore the settled-frame presentation the
sections exist to abolish, and silently — a dropped section leaves no header and
no placeholder, so nothing downstream could tell a frame with no open
indictments from a frame whose indictments the allocator cut. **Compressible
would do the same thing more quietly still**, and this is measured rather than
feared: the first implementation carried both halves in ONE compressible
section, and at a budget of one token the section survived while
`_bounded_view` cut the `STANDING ATTACKERS` block out of the middle of a pack
that still showed a frame. Its own test caught it
(`experiments/2026-08-24-change-rung6-frame-render-departures/`).

Exact is affordable only because the crisis is BOUNDED BY CONSTRUCTION —
`FRAME_SLICE_ATTACKERS_N` attackers at `_ATTACKER_HEAD_CHARS` each plus
`FRAME_SLICE_DEPARTURES_N` declarations, under 600 tokens against the smallest
shipped pack budget of 1200. Both caps state themselves in-band wherever they
bite ("5 of 12 shown"), so a capped list never reads as a complete one.

POSITION (priority 4, after the cacheable static head, before the
neighbourhood) is a HEDGE and not the mechanism.
`docs/RESEARCH_FINDINGS_Q1Q10_2026-08-22.md` Q1 measured that standing rules
decay in context regardless of placement, so the load-bearing parts are the
allocator flags here and the deterministic `held_frame_obligations` subtraction
in `calculus/render.py` — neither of which depends on the model honouring
anything it was shown.
`check: python -c "import ast,pathlib;T=ast.parse(pathlib.Path('src/deepreason/llm/packs.py').read_text());K={};[K.setdefault(c.args[0].value,[]).append({k.arg:getattr(k.value,'value',None) for k in c.keywords}) for c in ast.walk(T) if isinstance(c,ast.Call) and getattr(c.func,'id','')=='_pack_section' and isinstance(c.args[0],ast.Constant) and c.args[0].value in ('frame-slice','frame-crisis')];assert len(K['frame-slice'])==2 and all(k['droppable'] is False and k['compressible'] is True for k in K['frame-slice']), K;assert len(K['frame-crisis'])==2 and all(k['droppable'] is False and k['compressible'] is False for k in K['frame-crisis']), K"`
`check: python -m pytest tests/test_frame_render.py::test_the_frame_slice_survives_a_budget_that_drops_everything_optional tests/test_frame_render.py::test_the_exact_crisis_section_is_bounded_by_construction -q`

**NEGATIVE — the critic's target may never be excerpted.** The `target` section
is mandatory and exact. Budgeting it converted a transport limit into an
epistemic one: an argument cannot be refuted on bytes the critic was never
shown.
`check: python -m pytest tests/test_pack_prefix.py::test_long_critic_target_arrives_whole_rather_than_excerpted -q`

**Only two renderers are on the IR.** `render_conj_pack` and `render_crit_pack`
go through `_allocate_sections`; `render_batch_crit_pack`,
`render_experiment_pack`, `render_property_pack` and `render_cx_retry_pack`
still return a raw prefix clip at `token_budget * 4` chars and, being plain
`str`, are clipped a second time by the profile inside the adapter. Batch
criticism is the surprise here — the batched critic gets prefix truncation
where the single-target critic gets section allocation.
`check: test "$(grep -cF '_clip("' src/deepreason/llm/packs.py)" = 4`
`check: python -c "import ast,pathlib;T=ast.parse(pathlib.Path('src/deepreason/llm/packs.py').read_text());H=sorted(n.name for n in ast.walk(T) if isinstance(n,ast.FunctionDef) and any(isinstance(c,ast.Call) and getattr(c.func,'id','')=='_allocate_sections' for c in ast.walk(n)));assert H==['render_conj_pack','render_crit_pack']"`
`check: grep -qF '_CHARS_PER_TOKEN = 4' src/deepreason/llm/packs.py && grep -qF 'return text[: token_budget * _CHARS_PER_TOKEN]' src/deepreason/llm/packs.py`

**NEGATIVE — an allocated pack must never be re-clipped by the profile.**
`AllocatedPack` is a `str` subclass whose only job is to make the adapter skip
`apply_model_profile`. Any string operation on a pack demotes the marker, so
every post-allocation edit must re-wrap.
`check: python -m pytest tests/test_v6_context_continuation.py::test_wide_allocated_pack_dispatches_advisory_context_intact -q`

**The envelope bound is the UTF-8 byte length of the whole prompt plus the
route's `max_tokens`, compared against `context_window_tokens`.** Byte length is
used because every token contains at least one byte, making it a true upper
bound without a provider tokenizer. Enforcement is unconditional on every
rendered request — first turns, repair turns, and caller-supplied pre-rendered
requests alike — and a runtime endpoint cannot widen the frozen capacity.
`check: python -m pytest tests/test_v6_request_envelope.py -q`

**A route that declares no capacity is not enveloped at all.**
`context_window_tokens=None` means legacy/unqualified and the check returns
immediately. Where capacity IS declared the manifest validator requires a
finite `max_tokens` strictly below it, so `completion_bound` is never unknown.
`check: grep -qF 'context_window_tokens must be greater than max_tokens' src/deepreason/run_manifest.py`

**The meter fails closed.** Against a finite ceiling `TokenMeter.reserve`
refuses any dispatch whose prompt or completion bound is unknown, and refuses
one whose `total + reserved + bound` would exceed the ceiling — all under one
lock, so concurrent dispatchers cannot jointly overshoot.
`check: python -m pytest tests/test_token_reserve.py -q`

**An oversize conjecture prompt is a typed abandonment, not an exception.**
`rules/conj.py` catches `RequestEnvelopeExceeded` around both preview paths,
abandons the pre-issued context with reason `request_envelope_exceeded`, and
returns zero candidates. Nothing reaches the provider.
`check: grep -qF 'abandon_v6_context_preissue("request_envelope_exceeded")' src/deepreason/rules/conj.py`

**A school prefix is subtracted from the pack budget before rendering, never
appended after.** `_conditioned_budget` reserves `ceil((len(prefix)+2)/4)`
tokens and raises when fewer than 256 remain. No test covers this path; the
check below is structural only.
`check: grep -qF 'critic school conditioning leaves insufficient bounded pack budget' src/deepreason/rules/crit.py`

## Where to change what

| To change... | Edit | Test |
|---|---|---|
| What the conjecturer is shown, or in what order | `llm/packs.py` `render_conj_pack` — a new `_pack_section` with a priority | `tests/test_pack_prefix.py`, `tests/test_harness_fixes.py` |
| Retention, compression or drop policy | `packs/allocate.py` `allocate_pack` | `tests/test_pack_ir.py` |
| Whether a given section may be cut at all | the `droppable`/`compressible` pair at its `_pack_section` call site | `tests/test_pack_prefix.py::test_long_critic_target_arrives_whole_rather_than_excerpted` |
| A profile's presentation budget | `llm/profiles.py` `PROFILES` | `tests/test_compact_profiles.py` |
| The per-run pack target | `config.py` `PACK_TOKEN_BUDGET`, plus `profiles.apply_profile_to_config`, which overwrites it | `tests/test_compact_profiles.py::test_compact_config_applies_only_model_facing_process_defaults`, `tests/test_run_manifest.py::test_source_profiles_compile_orthogonally_and_reconstruct` |
| The request-envelope bound or its typed error | `llm/adapter.py` `_enforce_request_envelope`, `RequestEnvelopeExceeded` | `tests/test_v6_request_envelope.py` |
| The provider ceiling's reservation arithmetic | `llm/budget.py` `conservative_prompt_bound`, `TokenMeter.reserve` | `tests/test_token_reserve.py`, `tests/test_budget.py` |
| Moving a legacy renderer onto the IR | `llm/packs.py`, replacing `_clip(...)` with `_allocate_sections(...)` | `tests/test_pack_ir.py`, `tests/test_crit_batch.py` |

## Traps

- **The marker is a `str` subclass, and `str` operations drop it.** Live
  run-646f41b8 seq 565: the v6 post-allocation edits — replacing the canonical
  scratch text with the model-facing render, appending sealed simulation inputs
  and the workshop prompt — each produced a plain `str`, so the adapter
  re-applied the standard profile's aggregate prefix clip to a pack `PackIR`
  had already budgeted section by section, cutting the sealed advisory context
  mid-JSON out of the dispatched prompt. Every such edit in `rules/conj.py` now
  re-wraps in `AllocatedPack`, and demotion fails loudly before dispatch
  instead of corrupting it.
- **Fixing the appearance of truncation instead of the truncation.**
  `_document_excerpt` existed because compact critics refuted valid compiled
  designs for "ending abruptly"; it produced a labeled head/tail excerpt with a
  note telling the critic not to claim unshown sections were missing. That
  satisfied the symptom and left the defect — the omitted bytes still could not
  be attacked. Fixed 2026-08-01 (`experiments/2026-08-01-change-prose-can-refute`,
  R3/S3) by making the section mandatory instead. The helper survives, now
  uncalled; a call site returning would reopen the defect.
`check: test "$(grep -cF '_document_excerpt' src/deepreason/llm/packs.py)" = 1`
- **Three different token units, none interchangeable.** Allocation counts
  chars/4, the meter reserves at chars/3, the envelope uses UTF-8 bytes. Only
  the last is a genuine upper bound. Reasoning about "the budget" without
  naming which one produces arguments that are off by a third.
`check: python -c "from deepreason.packs.allocate import approximate_tokens as a; from deepreason.llm.budget import conservative_prompt_bound as c; assert a('x'*12)==3 and c('x'*12)==4"`
- **The pack budget is not the prompt budget.** Role template, JSON schema,
  worked example and alias labels are added after allocation, so a pack that
  comfortably fits `PACK_TOKEN_BUDGET` can still blow the route envelope —
  `tests/test_v6_request_envelope.py::test_complete_envelope_can_exceed_when_pack_itself_fits`
  exists because this was assumed away.
`check: grep -qF 'def test_complete_envelope_can_exceed_when_pack_itself_fits' tests/test_v6_request_envelope.py && grep -qF 'aliases=alias_labels' src/deepreason/llm/adapter.py`
- **The cache-ordering comments cite the wrong angle.** `packs.py`, the crit
  ordering comments and `tests/test_pack_prefix.py` all cite
  "docs/TOKEN_ECONOMY.md angle 4"; prefix caching is section 3 of that document
  and section 4 is call elimination. The behaviour is right and the citation is
  off by one — do not follow the pointer.
`check: grep -qF 'TOKEN_ECONOMY.md angle 4' src/deepreason/llm/packs.py && grep -q '^## 3. Angle: prefix caching' docs/TOKEN_ECONOMY.md && grep -q '^## 4. Angle: call elimination' docs/TOKEN_ECONOMY.md`
- **Reading `PROFILES` and concluding the budget — and reading the override
  backwards.** The number the renderers receive as `token_budget` is
  `config.PACK_TOKEN_BUDGET` (default 2500); `easy.py`'s `MAKE_OVERRIDES`
  raises it to 6000 so a stage pack holds a whole `FOUNDATION` document.
  `PROFILES` reaches a run only through `apply_profile_to_config`, which
  OVERWRITES that config value with `spec.pack_budget()` — the preset — so a
  profile projection *lowers* an app-raised budget rather than raising a
  default one. `ProfileSpec.pack_budget`'s `requested` branch, the one that
  could raise it, has no production caller at all: the sole
  `apply_model_profile` call site passes no `requested_tokens`.
`check: python -c "from deepreason.config import Config; from deepreason.llm.profiles import PROFILES, ModelProfile as M; from deepreason.easy import MAKE_OVERRIDES; assert Config().PACK_TOKEN_BUDGET == 2500 and MAKE_OVERRIDES['PACK_TOKEN_BUDGET'] == 6000; assert [PROFILES[m].pack_tokens_max for m in M] == [1200, 2500, 3000]; assert PROFILES[M.STANDARD].pack_budget() == 2500 and PROFILES[M.STANDARD].pack_budget(6000) == 6000"`
`check: python -c "import ast,pathlib;C=[c for p in pathlib.Path('src/deepreason').rglob('*.py') for c in ast.walk(ast.parse(p.read_text())) if isinstance(c,ast.Call) and getattr(c.func,'id','')=='apply_model_profile'];assert len(C)==1 and len(C[0].args)==2 and not C[0].keywords"`
