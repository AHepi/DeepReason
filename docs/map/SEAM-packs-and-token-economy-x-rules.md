<!-- DR-SEAM-packs-and-token-economy-x-rules -->
Verified-at: a0d36323f
Verify: python tools/docs_verify.py
Owns: src/deepreason/llm/packs.py, src/deepreason/rules/conj.py
Sides: DR-CON-packs-and-token-economy, DR-SUB-rules

# packs-and-token-economy x rules

## The agreement

A rule decides WHAT the seat is shown; the pack layer decides HOW MUCH of it
survives a finite context window. The division is not "rule computes, renderer
formats" — it is sharper than that and asymmetric in one direction only. The
renderer owns every budgeting decision: it alone builds `PackSection` values,
alone assigns priorities and droppable/compressible flags, and alone runs the
allocator to a fixed point. A rule owns the CONTENT of the conditional blocks
whose computation needs the harness — a dossier receipt, a fence sequence, a
work order, a scratch context plan — because those cannot be recomputed from
the epistemic state a renderer is handed. So the rule computes those blocks and
passes them in as strings, and the renderer decides where they sit and what
happens to them when the budget runs short.

The agreement's asymmetry is the load-bearing part: `rules/` never imports the
budgeting machinery. `PackIR`, `PackSection` and `allocate_pack` live in
`deepreason.packs`, and no module under `rules/` imports that package at all —
a rule that could build its own section could set its own priority, and the
token economy would then be two policies pretending to be one.
`check: python -c "
import ast, glob
bad = [f for f in glob.glob('src/deepreason/rules/**/*.py', recursive=True)
       for n in ast.walk(ast.parse(open(f).read()))
       if isinstance(n, ast.ImportFrom) and (n.module or '').startswith('deepreason.packs')]
assert not bad, bad
plain = [f for f in glob.glob('src/deepreason/rules/**/*.py', recursive=True)
         for n in ast.walk(ast.parse(open(f).read()))
         if isinstance(n, ast.Import) for a in n.names
         if a.name.startswith('deepreason.packs')]
assert not plain, plain
names = {a.name for f in glob.glob('src/deepreason/rules/**/*.py', recursive=True)
         for n in ast.walk(ast.parse(open(f).read()))
         if isinstance(n, ast.ImportFrom) and (n.module or '') == 'deepreason.llm.packs'
         for a in n.names}
banned = {'PackIR', 'PackSection', 'allocate_pack', 'approximate_tokens',
          '_pack_section', '_allocate_sections', 'DISCLOSED_ON_DROP'}
assert not (names & banned), sorted(names & banned)
"`

## Where it is expressed

### The nine contexts a rule computes and the renderer only formats

`render_conj_pack` accepts nine arguments that are not knobs but CONTENT, each
carrying one conditional block of the conjecturer's brief. `rules/conj.py::conj`
computes all nine and passes them at its single call site; the renderer wraps
each in a fixed header, gives it a fixed priority and fixed drop/compress flags,
and never asks where it came from.

| argument | section id it becomes | why the rule computes it |
|---|---|---|
| `frozen_evidence_context` | `frozen-evidence-context` | needs the dossier union across amendment epochs and a committed pack receipt |
| `citable_evidence_context` | `citable-evidence-blocks` | needs the legend over bound dossiers plus consumed research blocks |
| `open_criticism_context` | `open-criticisms` | needs the discharge channel's own bounded view |
| `capability_result_context` | `capability-result-context` | needs the simulation follow-up the capability controller recorded |
| `frame_slice_context` | `frame-slice` | needs the calculus render for the frame this problem sits in |
| `frame_crisis_context` | `frame-crisis` | as above, the crisis half |
| `scratch_context` | `scratch-advisory-context` | needs the transaction's context plan, which is issued before the call |
| `generation_context` | `experimental-generation-context` | supplied by the caller as free prose |
| `reference_menus` | one `reference-menu-*` section each | needs the call-local `MenuBinding` (`DR-INV-reference-menu`) |

`check: python -c "
import ast, pathlib
SUPPLIED = {'frozen_evidence_context', 'citable_evidence_context',
            'frame_slice_context', 'frame_crisis_context',
            'open_criticism_context', 'capability_result_context',
            'scratch_context', 'generation_context', 'reference_menus'}
fn = next(n for n in ast.walk(ast.parse(pathlib.Path('src/deepreason/llm/packs.py').read_text()))
          if isinstance(n, ast.FunctionDef) and n.name == 'render_conj_pack')
params = {a.arg for a in fn.args.args + fn.args.kwonlyargs}
assert SUPPLIED <= params, sorted(SUPPLIED - params)
calls = [n for n in ast.walk(ast.parse(pathlib.Path('src/deepreason/rules/conj.py').read_text()))
         if isinstance(n, ast.Call) and getattr(n.func, 'id', None) == 'render_conj_pack']
assert len(calls) == 1, len(calls)
passed = {k.arg for k in calls[0].keywords}
assert SUPPLIED <= passed, sorted(SUPPLIED - passed)
"`

Nine of the brief's twenty section slots therefore have their content decided
outside the renderer. That is why a change making the brief pluggable cannot
reach every slot by rewriting `render_conj_pack` alone: for these nine, a
section plugin FORMATS a value the caller supplies, and moving the computation
itself behind the interface would drag the dossier, fence-sequence and
work-order plumbing across this seam
(`experiments/2026-09-03-change-conjecturer-pluggable-interface/SPEC.md`, A6).

### The four post-allocation re-wraps, and the marker that makes them safe

Allocation is not the last thing that happens to a conjecturer pack. Four
insertions happen after it, all in `conj.py`, because each depends on something
that does not exist until the pack has been rendered: the v6 scratch render is
substituted in place of its canonical text, the sealed simulation inputs and the
scratch workshop prompt are appended, and the post-allocation menus are appended
last because the alias table they describe is DERIVED from the rendered bytes.

Every one of the four re-wraps its result in `AllocatedPack`. That marker is the
whole agreement in one type: `str` operations return a plain `str`, and a plain
`str` tells the adapter that this pack has NOT been budgeted section by section,
so the adapter applies the profile's aggregate prefix clip — a blind cut through
whatever happens to sit at the boundary. The four insertions are separately
byte-accounted and bounded by the request envelope, so the clip would be a
second, unaccounted budget applied on top of the first.
`check: python -c "
import ast, pathlib
t = ast.parse(pathlib.Path('src/deepreason/rules/conj.py').read_text())
wraps = [n for n in ast.walk(t)
         if isinstance(n, ast.Call) and getattr(n.func, 'id', None) == 'AllocatedPack']
assert len(wraps) == 4, len(wraps)
"`

The adapter's half is one branch, and it is pinned as a branch rather than by
its message because a gutted guard keeps its strings: the marker test and the
clip it suppresses are asserted together, and the clip is called once to show it
really does shorten a pack.
`check: python -c "
import ast, pathlib
from deepreason.llm.packs import AllocatedPack, apply_model_profile
long = 'x' * 200000
assert len(apply_model_profile(long, 'compact')) < len(long)
assert type(AllocatedPack(long)) is not str and isinstance(AllocatedPack(long), str)
t = ast.parse(pathlib.Path('src/deepreason/llm/adapter.py').read_text())
marker = [n for n in ast.walk(t)
          if isinstance(n, ast.Assign)
          and getattr(n.targets[0], 'id', None) == 'pack_is_allocated'
          and isinstance(n.value, ast.Call)
          and getattr(n.value.func, 'id', None) == 'isinstance'
          and getattr(n.value.args[1], 'id', None) == 'AllocatedPack']
assert len(marker) == 1, len(marker)
guarded = [n for n in ast.walk(t)
           if isinstance(n, ast.If) and 'pack_is_allocated' in ast.dump(n.test)
           and any(isinstance(c, ast.Call)
                   and getattr(c.func, 'id', None) == 'apply_model_profile'
                   for c in ast.walk(n))]
assert len(guarded) == 1, len(guarded)
"`

### What the renderer refuses to take from the rule

The rule supplies content and nothing else. It does not pass a priority, a
`min_tokens`, a droppable flag, or a section id: every one of those is a literal
inside `render_conj_pack`, which is why `DR-CON-packs-and-token-economy`'s
section table can be read from one function. The rule's only budget input is a
single number, `token_budget`, and a single count, `neighbourhood_n` — both from
`Config`, neither section-specific.
`check: python -c "
import ast, pathlib
calls = [n for n in ast.walk(ast.parse(pathlib.Path('src/deepreason/rules/conj.py').read_text()))
         if isinstance(n, ast.Call) and getattr(n.func, 'id', None) == 'render_conj_pack']
passed = {k.arg for k in calls[0].keywords}
banned = {'priority', 'min_tokens', 'max_tokens', 'droppable', 'compressible',
          'sections', 'cache_group', 'section_id'}
assert not (passed & banned), sorted(passed & banned)
assert 'token_budget' in passed and 'neighbourhood_n' in passed
"`

## Where to change what

| To do this | Edit | Test |
|---|---|---|
| change what a brief section SAYS, for a section the renderer builds | `llm/packs.py::render_conj_pack` | `tests/test_conj_pack_legacy_golden.py` |
| change what a brief section says, for one of the nine caller-computed contexts | `rules/conj.py::conj` | the owning subsystem's tests, then the golden |
| change WHERE a section sits or how much of it survives | `llm/packs.py` priorities and flags; `DR-INV-render-layout` for arrangement | `tests/test_render_layout_rules.py` |
| add a block after allocation | `rules/conj.py`, re-wrapping in `AllocatedPack` | `tests/test_pack_prefix.py` |
| change what the allocator does when a disclosed section is cut | `llm/packs.py::_allocate_sections`, `DISCLOSED_ON_DROP` | `tests/test_conj_pack_legacy_golden.py` (the `withheld` case) |

## Invariants

- `DR-INV-render-layout` — arrangement is a policy a renderer READS, never a
  constant it holds.
- `DR-INV-reference-menu` — a menu changes what the model is SHOWN and may
  never change what the harness ACCEPTS; the pre-allocation menus cross this
  seam as content, and the post-allocation ones cross it after.
- `DR-CON-packs-and-token-economy`'s NO SILENT CAPS rule — a section cut for
  budget must leave a signal, which is why `DISCLOSED_ON_DROP` exists and why
  the `AllocatedPack` marker matters: an aggregate clip leaves none.

## Traps

- **A `str` operation demotes the marker, and the demotion is silent.**
  `pack + text`, `pack.replace(...)` and `"".join(...)` all return a plain
  `str`, after which the adapter re-applies the profile's aggregate prefix clip
  to a pack the allocator had already budgeted — cutting the sealed advisory
  context mid-JSON out of the dispatched prompt. Fixed by re-wrapping at all
  four sites (`rules/conj.py`, the comment above the first re-wrap states the
  constraint); the trap is that a FIFTH insertion added later inherits nothing
  and must re-wrap too. The check above pins the count at four for exactly that
  reason.
- **A menu built before allocation cannot name an alias.** The alias table is
  derived from the rendered pack, so an artifact-alias menu built at the
  pre-allocation call site would name handles that do not exist yet. The two
  menu passes are not an optimisation; they are forced by this ordering.
- **A pre-v6 run once got a menu for a field its form does not have.** The
  post-allocation menus are gated on the v6 path because the fields they
  describe belong to the v6 turn contract; an ungated version named
  `optional_refs` to seats that could not fill it. Fixed; the gate is in
  `conj.py` at the `post_allocation_menus` assignment.
