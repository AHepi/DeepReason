<!-- DR-SEAM-llm-x-minireason -->
Verified-at: f8100b9b0
Verify: python -m pytest mini/tests/test_mini_seat_shell.py mini/tests/test_mini_exposure.py mini/tests/test_mini_sources.py mini/tests/test_mini_forms.py -q
Owns:
Seams:
Seams-undocumented:

# llm × minireason — the reduced engine borrows the seat, never the authority

## What this seam is

`DR-SUB-minireason` is a small outer loop over the parent's record; it owns no
renderer, no wire schema, no route firewall and no repair protocol of its own.
Every one of those it takes from `DR-SUB-llm`. The traffic is therefore
**one-directional and large**: mini names `deepreason.llm` at fifty symbol
crossings across eleven `llm/` modules, while `llm/` imports `minireason`
nowhere (one docstring in `llm/budget.py` mentions it by name, and that is
the whole of the reverse direction). The asymmetry is the design: a reduced
engine that had its own seat machinery would be a second protocol, and the
mini isolation programme (2026-09-05) exists to test mini *in isolation from
the larger harness*, not in isolation from the record's own tools.

`check: python -c "
import ast, pathlib
crossings = set()
for path in sorted(pathlib.Path('mini/minireason').glob('*.py')):
    for node in ast.walk(ast.parse(path.read_text())):
        if isinstance(node, ast.ImportFrom) and (node.module or '').startswith('deepreason.llm'):
            crossings.update((path.name, node.module, a.name) for a in node.names)
        if isinstance(node, ast.Import):
            crossings.update((path.name, a.name, a.name) for a in node.names if a.name.startswith('deepreason.llm'))
modules = {m for _, m, _ in crossings}
assert len(crossings) >= 45 and len(modules) >= 10, (len(crossings), sorted(modules))
for must in ('deepreason.llm.packs', 'deepreason.llm.seat_sections', 'deepreason.llm.wire', 'deepreason.llm.firewall'):
    assert must in modules, must
back = [str(p) for p in pathlib.Path('src/deepreason/llm').rglob('*.py')
        for n in ast.walk(ast.parse(p.read_text()))
        if (isinstance(n, ast.ImportFrom) and 'minireason' in (n.module or ''))
        or (isinstance(n, ast.Import) and any('minireason' in a.name for a in n.names))]
assert back == [], back
"`

## The agreement, in one sentence each

**Mini renders a brief through the ONE public road, and builds no section.**
`packs.render_seat_brief` (the walk) and `packs.allocate_seat_brief` (the
allocator) are the two public entries `DR-INV-seat-section-plugins` declares,
each one call to its private counterpart; `minireason/seats.py` calls those
and names no `_`-prefixed symbol of `packs`, constructs no `PackSection`, and
never calls `allocate_pack` itself. Reaching past the underscore would be the
bypass the modularity law's tests exist to catch; building a second renderer
would be worse.
`check: python -m pytest mini/tests/test_mini_seat_shell.py::test_mini_renders_through_the_public_road_only -q`

**Mini's seats are shells registered in `llm`'s own registries, and the
shell's `form_id` is READ.** Three section plugins plus a directive plugin,
three layouts and three shells register through `seat_sections`' registries
exactly as the shipped ones do. `seats.form_for_seat` takes the shell's
`form_id` as its declared default — the first consumer that field ever had —
so binding another shell in a seat's place changes what the seat is asked for
as well as what it is shown. The full harness's two shells are untouched and
their goldens byte-identical.
`check: python -m pytest mini/tests/test_mini_seat_shell.py::test_binding_another_shell_changes_both_what_is_shown_and_what_is_asked tests/test_conj_pack_legacy_golden.py tests/test_crit_pack_legacy_golden.py -q`

**Mini's FORMS are `WireContract`s outside the V6 contract Literals.** The
relaxed forms in `minireason/forms.py` subclass `llm.wire.WireContract`, so
mini's call layer validates, repairs and blobs them through the same
`BoundedRepairSession` the full harness uses — but their ids are never added
to `ContractVersionPolicyV3` (Road M of the programme's SPEC: a registry
here touches no frozen surface; an id there touches three). The stored
default form HOLDS the shipped `ReferenceFreeConjecturerWireContract`
instance, unchanged.
`check: python -c "
import sys; sys.path.insert(0, 'mini')
from deepreason.llm.wire import WireContract, ReferenceFreeConjecturerWireContract
from deepreason.run_manifest import ContractVersionPolicyV3
from minireason.forms import mini_form_ids, resolve_mini_form
for fid in mini_form_ids():
    assert isinstance(resolve_mini_form(fid).contract, WireContract), fid
assert isinstance(resolve_mini_form('mini.conjecturer.legacy-v0').contract, ReferenceFreeConjecturerWireContract)
literal = str(ContractVersionPolicyV3.model_fields['conjecturer_turn_contract'].annotation)
assert 'mini.' not in literal, literal
"`

**The route lease and the profile clip are `llm`'s, and mini obeys both.**
`minireason/call.py` verifies its `EndpointLease` and fingerprints the route
with `llm.firewall`, and clips every rendered prompt with
`llm.profiles.clip_pack` at the profile's pack budget. The clip is a TRAP
recorded below: it is silent, and it is a third length limit the programme's
"not limit prose length at all" did not name.
`check: python -c "
import ast, pathlib
src = pathlib.Path('mini/minireason/call.py').read_text()
fn = next(n for n in ast.walk(ast.parse(src)) if isinstance(n, ast.FunctionDef) and n.name == 'call')
names = {c.func.id for c in ast.walk(fn) if isinstance(c, ast.Call) and isinstance(c.func, ast.Name)}
assert {'clip_pack', 'route_fingerprint'} <= names, sorted(names)
"`

## Which fraction of each side is involved

| Side | The part this seam touches |
|---|---|
| `DR-SUB-llm` | `seat_sections.py` (the registries and the request/render/receipt models), the two public entries in `packs.py`, `wire.py`'s `WireContract` base and the shipped reference-free contract, `firewall.py`'s lease and fingerprint, `profiles.py`'s clip, `repair.py`'s bounded session. Nothing in `llm/` knows mini exists. |
| `DR-SUB-minireason` | `sources.py` (the projection and the five plugins), `seats.py` (layouts, shells, `form_for_seat`, `render_mini_brief`), `forms.py` (the contracts), `call.py` (dispatch), `compat.py` (the lease and the kernel), and since the programme's T5 `loop.py`, whose stage walk renders every seat's brief through `render_mini_brief` and dispatches through the ONE leased route. |

## Where to change what

| To change... | Edit | Test |
|---|---|---|
| what a mini seat is SHOWN | a layout in `minireason/seats.py`, or a `.layout.json` under `<DEEPREASON_HOME>/seat_plugins/` naming registered plugins — never `packs.py` | `mini/tests/test_mini_exposure.py` |
| what a mini seat is ASKED FOR | register a `MiniFormV1` in `minireason/forms.py`, name it in a shell, or select it with `DEEPREASON_MINI_FORM` | `mini/tests/test_mini_seat_shell.py` |
| the road a brief takes to text | `packs.render_seat_brief` / `allocate_seat_brief` — and every consumer keeps to them | `tests/test_seat_section_architecture.py`, the public-road test above |
| how a mini reply is validated or repaired | NOT here: it is `llm/wire.py` and `llm/repair.py`, shared with the full harness | `tests/test_wire_contracts.py` |

## Invariants

- `DR-INV-seat-section-plugins` — the plugin protocol, the registries, the
  FROZEN clause that a plugin's output is presentation and never evidence.
  Mini's plugins are held to it, and additionally to the rule that no mini
  source reads an artifact's status (`SUB-minireason`, who sees what).
- `DR-INV-frozen-surfaces` — the reason mini's forms live in a registry of
  their own rather than in `ContractVersionPolicyV3`.

## Why this seam carries no `Sweep:` header

The agreement here is carried by imports and by two registries, not by a
FIELD that any site compares or raises on. A `Sweep:` spec is a field name
paired with the other side's symbols, and `--coverage` looks for `==`, `!=`
and `raise` around that field; there is no such field. The enforcement
inventory is the four checks above and the tests they name, each of which was
shown red under a mutation before it was written down.

## Traps

- **Mini's dict `State` is not what the plugins read.** The first walk from a
  live mini session rendered `dr.problem` and died on `dr.neighbourhood` with
  `'dict' object has no attribute 'content_ref'`: mini's `State` projects
  every artifact to a dict, the shipped plugins read ontology objects. Fixed
  2026-09-05 (mini isolation programme, T3 step 24) by ONE read-only
  projection, `sources.mini_section_request`; the before-state is a committed
  test, `mini/tests/test_mini_sources.py::test_the_dict_view_alone_cannot_feed_the_shipped_plugins`.
- **The profile clip in mini's call layer is a silent length limit.**
  `call.py` runs `clip_pack(prompt, profile)` on every prompt — 4 800
  characters on the compact profile — with no notice in the brief or the
  record. The programme's SPEC named two silent cuts in the loop's own prompt
  builder and removed both; this third one sits one layer down and was found
  while T3 was designed. NOT fixed here: parked with a ready-to-send prompt at
  `experiments/2026-09-05-change-mini-isolation-programme/PARKED.md` P8.
  DISPOSED by T5 (step 40) without touching the call layer: the loop hands
  the everything section its share of the profile's prompt budget
  (`MiniStageV1.brief_share`), so the retention rule withholds and NAMES what
  does not fit instead of the clip cutting it; and any brief that still
  overruns the clip is recorded as `mini:brief-clipped` with both sizes, so
  the cut is never silent in the record. The clip itself is unchanged.
- **`LLMCall.role` names the leased route, not the seat.** Mini's manifest
  grants one canonical role, `conjecturer`, and the manifest refuses
  non-canonical roles, so every stage -- critic and commitment seats included
  -- dispatches through that lease and its calls carry `role="conjecturer"`.
  Which SEAT spoke is stated by the record the stage writes (`kind:` on the
  `mini:record` event that carries the spend), never by the call. A
  per-seat role in the call would need canonical roles or a manifest change
  on a frozen surface; parked as P9 of the programme.
- **A counted map claim moves when a public entry is added.**
  `CON-packs-and-token-economy` pinned "only two renderers are on the IR" by
  counting callers of `_allocate_sections`; `allocate_seat_brief` was a third
  the moment it existed, and the full `docs_verify` caught it. Moved with the
  code (T3 step 25), not deleted: the claim names the public entry and pins
  all three.
