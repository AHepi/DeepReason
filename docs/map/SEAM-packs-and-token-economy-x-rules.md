<!-- DR-SEAM-packs-and-token-economy-x-rules -->
Verified-at: 770ea1344
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
allocator to a fixed point.

**What changed on 2026-09-04, and it is the whole point of this seam:** a rule
no longer computes any of the brief's CONTENT either. Nine of the conjecturer's
twenty section slots need the record to exist at all — a dossier receipt, a
fence sequence, a work order, the open-criticism view — and a section plugin may
not call the harness, so until this date `rules/conj.py` computed those nine and
passed them in as strings. They are now computed by registered section SOURCES
(`DR-INV-seat-section-sources`), which read the record, write nothing, and hand
their values to the plugins that format them. `conj` hands over the state a
source may read and takes the values back; it names no section.

The agreement's asymmetry is still the load-bearing part: `rules/` never
imports the budgeting machinery. `PackIR`, `PackSection` and `allocate_pack`
live in `deepreason.packs`, and no module under `rules/` imports that package at
all — a rule that could build its own section could set its own priority, and
the token economy would then be two policies pretending to be one.
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
          '_pack_section', '_allocate_sections', 'DISCLOSED_ON_DROP',
          'AllocatedPack'}
assert not (names & banned), sorted(names & banned)
"`

## Where it is expressed

### The nine contexts a SOURCE computes and a plugin formats

`render_conj_pack` still accepts nine arguments that are not knobs but CONTENT,
each carrying one conditional block of the conjecturer's brief; two dozen call
sites — the golden fixtures among them — pass them one by one. `rules/conj.py`
is no longer one of those call sites. It passes a single `supplied` mapping, the
assembled output of the seat's registered SOURCE bundle, and the renderer puts
whatever is in it into `SectionRequestV1.supplied` under those same names.
Neither the plugin nor the layout asks where the content came from, and now
neither does the rule.

| supplied key | section id it becomes | the source that computes it |
|---|---|---|
| `frozen_evidence_context` | `frozen-evidence-context` | `dr.src.frozen_evidence` — the dossier union across amendment epochs plus a committed pack receipt |
| `citable_evidence_context` | `citable-evidence-blocks` | `dr.src.citable_evidence` — the legend over bound dossiers plus consumed research blocks |
| `open_criticism_context` | `open-criticisms` | `dr.src.open_criticism` — the discharge channel's own bounded view |
| `capability_result_context` | `capability-result-context` | `dr.src.capability_result` — the simulation follow-up the capability controller recorded |
| `frame_slice_context` | `frame-slice` | `dr.src.frame_slice` — the calculus render for the frame this problem sits in |
| `frame_crisis_context` | `frame-crisis` | `dr.src.frame_crisis` — the crisis half |
| `scratch_context` | `scratch-advisory-context` | `dr.src.scratch_context` — the transaction's context plan, issued before the call |
| `generation_context` | `experimental-generation-context` | `dr.src.generation_context` — free prose the caller holds, routed by the bundle |
| `reference_menus` | one `reference-menu-*` section each | `dr.src.reference_menus` — the call-local `MenuBinding` (`DR-INV-reference-menu`) |

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
assert 'supplied' in params
calls = [n for n in ast.walk(ast.parse(pathlib.Path('src/deepreason/rules/conj.py').read_text()))
         if isinstance(n, ast.Call) and getattr(n.func, 'id', None) == 'render_conj_pack']
assert len(calls) == 1, len(calls)
passed = {k.arg for k in calls[0].keywords}
assert not (SUPPLIED & passed), sorted(SUPPLIED & passed)
assert 'supplied' in passed
from deepreason.seat_sources import (
    STAGE_PRE_CONTRACT, STAGE_RENDER, resolve_seat_source_bundle, resolve_section_source)
bundle = resolve_seat_source_bundle('conjecturer')
supplies = {resolve_section_source(e.source_id, e.source_version).supplies
            for stage in (STAGE_PRE_CONTRACT, STAGE_RENDER)
            for e in bundle.entries_for_stage(stage)}
assert supplies == SUPPLIED, sorted(supplies ^ SUPPLIED)
"`

The critic's four (`premise_invitation`, `citable_evidence_context`,
`frame_slice_context`, `frame_crisis_context`) are the shape the conjecturer's
nine used to have: still computed in `rules/crit.py` and passed in one by one.
Three of the four are literally the sources above; what stops the critic
following the conjecturer in one step is that its two call sites supply
DIFFERENT SUBSETS — the atomic-decomposition fallback deliberately passes the
frames and not the premise invitation — so the bundle would need a per-call
subset selector it does not have. The batch renderer is a third brief the shell
never reaches at all, parked separately. Priced and parked
(`experiments/2026-09-04-change-seat-sections-behind-interface/PARKED.md`).
`check: python -c "
import ast, pathlib
src = pathlib.Path('src/deepreason/llm/packs.py').read_text()
fn = next(n for n in ast.walk(ast.parse(src))
          if isinstance(n, ast.FunctionDef) and n.name == 'render_crit_pack')
body = ast.get_source_segment(src, fn)
for key in ('premise_invitation', 'citable_evidence_context',
            'frame_slice_context', 'frame_crisis_context'):
    assert f'\"{key}\": {key}' in body, key
assert '_walk_seat_layout(' in body and '_pack_section(' not in body
calls = [n for n in ast.walk(ast.parse(pathlib.Path('src/deepreason/rules/crit.py').read_text()))
         if isinstance(n, ast.Call) and getattr(n.func, 'id', None) == 'render_crit_pack']
assert len(calls) == 2, len(calls)
assert len({frozenset(k.arg for k in c.keywords) for c in calls}) == 2
"`

### The four post-allocation applications, and the marker that makes them safe

Allocation is not the last thing that happens to a conjecturer pack. Four
insertions happen after it, because each depends on something that does not
exist until the pack has been rendered: the v6 scratch render is substituted in
place of its canonical text, the sealed simulation inputs and the scratch
workshop prompt are appended, and the post-allocation menus are appended last
because the alias table they describe is DERIVED from the rendered bytes.

All four are registered POST-ALLOCATION SOURCES since 2026-09-04, and the
re-wrap moved with them. That marker is the whole agreement in one type: `str`
operations return a plain `str`, and a plain `str` tells the adapter that this
pack has NOT been budgeted section by section, so the adapter applies the
profile's aggregate prefix clip — a blind cut through whatever happens to sit at
the boundary. The four insertions are separately byte-accounted and bounded by
the request envelope, so the clip would be a second, unaccounted budget applied
on top of the first.

The count that matters is no longer four re-wraps in `conj.py` but ZERO there
and exactly TWO in the runner — one for an append, one for a substitution —
because every application goes through it. A fifth insertion added as a source
inherits the marker by construction; one added anywhere else does not, and that
is what the check pins.
`check: python -c "
import ast, pathlib
t = ast.parse(pathlib.Path('src/deepreason/rules/conj.py').read_text())
wraps = [n for n in ast.walk(t)
         if isinstance(n, ast.Call) and getattr(n.func, 'id', None) == 'AllocatedPack']
assert not wraps, len(wraps)
r = ast.parse(pathlib.Path('src/deepreason/seat_sources/registry.py').read_text())
runner = next(n for n in ast.walk(r)
              if isinstance(n, ast.FunctionDef) and n.name == 'apply_post_allocation')
inside = [n for n in ast.walk(runner)
          if isinstance(n, ast.Call) and getattr(n.func, 'id', None) == 'AllocatedPack']
assert len(inside) == 2, len(inside)
outside = [n for n in ast.walk(r)
           if isinstance(n, ast.Call) and getattr(n.func, 'id', None) == 'AllocatedPack']
assert len(outside) == 2, len(outside)
from deepreason.seat_sources import POST_ALLOCATION_STAGES, resolve_seat_source_bundle
bundle = resolve_seat_source_bundle('conjecturer')
applied = [e for stage in POST_ALLOCATION_STAGES for e in bundle.entries_for_stage(stage)]
assert len(applied) == 4, len(applied)
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
| change what a brief section SAYS, for a section the renderer builds | its plugin, via `DR-REC-add-a-section-plugin` | `tests/test_conj_pack_legacy_golden.py` |
| change what a brief section says, for one of the nine record-backed contexts | its SOURCE in `seat_sources/shipped.py`, or register a new one and swap the bundle entry | `tests/test_seat_section_sources.py`, then the golden |
| change WHERE a section sits or how much of it survives | `llm/packs.py` priorities and flags; `DR-INV-render-layout` for arrangement | `tests/test_render_layout_rules.py` |
| add a block after allocation | register a post-allocation source and add its bundle entry — NOT a fifth re-wrap in `rules/` | `tests/test_pack_prefix.py`, `tests/test_seat_section_sources.py` |
| change what the allocator does when a disclosed section is cut | `llm/packs.py::_allocate_sections`, `DISCLOSED_ON_DROP` | `tests/test_conj_pack_legacy_golden.py` (the `withheld` case) |
| commit something to the record beside a section | `rules/conj.py` — a source may READ the record and may never append to it | `tests/test_seat_section_sources.py` |

## Invariants

- `DR-INV-seat-section-sources` — where a section's content comes from: read
  the record, append nothing, one declared write.
- `DR-INV-seat-section-plugins` — how that content is formatted, and the
  registry both layers resolve from.
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
  context mid-JSON out of the dispatched prompt. Fixed 2026-08 by re-wrapping
  at all four sites in `rules/conj.py`; the trap then was that a FIFTH
  insertion added later inherited nothing. On 2026-09-04 the four insertions
  became registered post-allocation SOURCES and the re-wrap moved into the one
  runner that applies them, so a fifth source inherits it by construction. The
  trap did not disappear, it MOVED: an insertion made anywhere other than a
  source still inherits nothing, which is why the check pins `rules/conj.py` at
  ZERO re-wraps rather than only pinning the runner at two.
- **A menu built before allocation cannot name an alias.** The alias table is
  derived from the rendered pack, so an artifact-alias menu built at the
  pre-allocation call site would name handles that do not exist yet. The two
  menu passes are not an optimisation; they are forced by this ordering, and it
  is the reason the source bundle has a stage AFTER the alias binding rather
  than one post-allocation stage.
- **A pre-v6 run once got a menu for a field its form does not have.** The
  post-allocation menus are gated on the v6 path because the fields they
  describe belong to the v6 turn contract; an ungated version named
  `optional_refs` to seats that could not fill it. Fixed; the gate moved with
  the menus and is now inside `dr.src.post.reference_menus`.
- **The source layer cannot live in `llm/`, and the first attempt put it
  there.** `DR-SUB-llm` forbids that package from importing the harness, the
  scheduler, the rules, the adjudicator or the amendment machinery, so that a
  transport bug cannot become an adjudication bug. A source's whole job is to
  read the record, so the module tripped that check on its first `docs_verify`
  run and moved to its own package, `deepreason.seat_sources`. Recorded because
  the pull to put it beside the plugins it feeds is strong and the arrow it
  would invert is not obvious from the code.
