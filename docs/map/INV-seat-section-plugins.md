<!-- DR-INV-seat-section-plugins -->
Verified-at: 6f9b5614e
Verify: python -m pytest tests/test_seat_section_architecture.py tests/test_conj_pack_legacy_golden.py tests/test_crit_pack_legacy_golden.py -q
Owns: src/deepreason/llm/seat_sections.py, src/deepreason/llm/seat_plugins.py, src/deepreason/llm/seat_layouts.py, src/deepreason/llm/seat_templates.py, src/deepreason/llm/role_prompts.py
Seams: DR-SEAM-packs-and-token-economy-x-rules

# Seat section plugins — a seat is a shell

## What it is

A seat is a shell: what makes one a conjecturer or a critic is the BRIEF it is
shown and the FORM it is asked to fill, both registered, versioned
configuration rather than a code path carrying the seat's name (CLAUDE.md,
"A seat is a shell: its input and its output define it", 2026-09-03). This
document owns the input half: the protocol a brief section renders through,
the registry it resolves from, the layout that composes one seat's brief, and
the shell that pairs a layout with a form and a wording.

It owns how a section is FORMATTED. Where its CONTENT comes from is
`DR-INV-seat-section-sources`, and the split is forced rather than tidy: a
plugin may not call the harness, and nine of the conjecturer's sections need
the record to exist at all.

Both renderers walk a layout. Neither builds a section itself.
`check: python -c "
import ast, pathlib
src = pathlib.Path('src/deepreason/llm/packs.py').read_text()
tree = ast.parse(src)
for name in ('render_conj_pack', 'render_crit_pack'):
    fn = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == name)
    built = sum(1 for c in ast.walk(fn) if isinstance(c, ast.Call)
                and getattr(c.func, 'id', '') == '_pack_section')
    walked = sum(1 for c in ast.walk(fn) if isinstance(c, ast.Call)
                 and getattr(c.func, 'id', '') == '_walk_seat_layout')
    assert built == 0 and walked == 1, (name, built, walked)
"`

## Three layers, not interchangeable

**FROZEN — the change protocol.** (a) A plugin's output is PRESENTATION,
never evidence: no plugin, layout or shell may change what is admitted,
ranked, immune or refuted. (b) The parse half of every form does not vary —
what counts as evidence is not the shell's to move. (c) No silent truncation.
(d) Only the operator authors a plugin.

**VERSIONED — the registries.** Section plugins keyed `(plugin_id, version)`;
seat pack layouts; seat shells; role-prompt templates. A new arrangement is a
registration, never a consumer edit.

**FREE — the values.** Each plugin's parameters and each layout entry's
`priority`/`droppable`/`compressible`/`min_tokens`/`max_render_bytes`, inside
declared envelopes, refused typed at construction rather than silently
clamped.
`check: python -c "
from deepreason.llm.seat_sections import SeatPackLayoutEntryV1, SeatSectionError
try:
    SeatPackLayoutEntryV1(plugin_id='x', priority=99)
except SeatSectionError as error:
    assert error.code == 'SEAT_PACK_LAYOUT_OUT_OF_ENVELOPE'
else:
    raise AssertionError('an out-of-envelope priority was accepted')
"`

## Entry points

| What | Where |
|---|---|
| the protocol, the request, the render, the receipt | `llm/seat_sections.py` |
| the registries and their resolution | `llm/seat_sections.py` |
| the seeded plugins (20 conjecturer + 10 critic + an episode slot) | `llm/seat_plugins.py` |
| the shipped layouts and shells | `llm/seat_layouts.py` |
| formatting without code | `llm/seat_templates.py` |
| the prose that wraps a brief | `llm/role_prompts.py` |
| the one walk that builds a section | `llm/packs.py::_walk_seat_layout` |

## The invariants

**Selection is by id, from an argument or the environment — never `Config`,
never the manifest.** Measured, not preferred: `run_manifest.py` dumps every
`Config` field into `engine_config_json` and `qualification.py` folds that
into every qualification subject digest, so a knob here on `Config` would move
the digest of every qualification bundle in the tree.
`check: python -c "
from deepreason.config import Config
from deepreason.llm.role_prompts import ROLE_PROMPT_TEMPLATE_ENV
from deepreason.llm.seat_sections import SEAT_PACK_LAYOUT_ENV, SEAT_SHELL_ENV
fields = {f.upper() for f in Config.model_fields}
for name in (SEAT_PACK_LAYOUT_ENV, SEAT_SHELL_ENV, ROLE_PROMPT_TEMPLATE_ENV):
    assert name not in fields, name
assert not [f for f in fields if 'SEAT_PACK' in f or 'SEAT_SHELL' in f
            or 'SECTION_PLUGIN' in f], sorted(fields)
"`

**An empty render is an ERROR; `None` is a legal absence.** A dropped section
leaves no header, so "rendered empty" and "never had content" would otherwise
be byte-indistinguishable in the pack.
`check: python -m pytest tests/test_seat_section_contract.py -q`

**Shape buys nothing.** No generation-side name may be read where standing is
decided. `DR-CON-conjecture-kinds`' R-g guardrail, applied to the shell.
`check: python -m pytest tests/test_seat_section_architecture.py -q`

**The default render has not moved.** Both seats' briefs are byte-identical to
what they were before the interface existed; a layout is only a different
arrangement when someone selects one.
`check: python -m pytest tests/test_conj_pack_legacy_golden.py tests/test_crit_pack_legacy_golden.py -q`

**`wire_contract_for`'s answers are frozen by two callers.**
`invariants.py` folds them into a replay authority set and `run_manifest.py`
into a qualification subject, so form selection happens at the dispatch site
and never by changing that function's answer.
`check: python -m pytest tests/test_wire_contract_id_map.py -q`

**Only the operator authors a plugin.** A `.py` plugin executes inside the
harness; an id that does not resolve is a typed refusal, never a load-by-path.
`check: python -m pytest tests/test_seat_section_home.py -q`

## Where to change what

| To do this | Edit | Test |
|---|---|---|
| change what a section SAYS | its plugin in `llm/seat_plugins.py`, or an operator `.tmpl` | the goldens |
| change what one of the nine record-backed sections CONTAINS | its SOURCE — `DR-INV-seat-section-sources` | `tests/test_seat_section_sources.py`, then the goldens |
| add a section to a brief | register a plugin, add a layout entry — no source edit | `tests/test_seat_section_architecture.py` |
| change where a section sits, or its budget | the layout entry | the goldens |
| add a seat kind | register a `SeatShellV1` | `tests/test_seat_shell_swap.py` |
| change the prose around a brief | register a `RolePromptTemplateV1` | `tests/test_role_prompt_registry.py` |
| loosen what a reply may look like | `wire.py::_normalise_shape` | `tests/test_wire_normalisation.py` |

The recipe for the common case is `DR-REC-add-a-section-plugin`.

## Traps

- **A plugin bound in another seat's place may not have its inputs.** The
  conjecturer's `dr.problem` crashed the first time its shell was bound at the
  critic's seat, because a critic's request carries no problem. A plugin
  therefore DECLARES what it cannot render without, and the walk records
  `absent` rather than calling it. A shell is portable; what it can render
  still depends on what the seat's request carries. Fixed 2026-09-03, in the
  tranche that introduced the shell.
- **A normalisation that deletes a rejected value changes a verdict.** N4 was
  specified to drop an optional field supplied as `null` OR `""`, and the
  empty-string half turned a refusal into an acceptance: the repair protocol's
  own fixture is a blank message a contract rejects deliberately. Narrowed to
  `null` only, 2026-09-04, with three doctor tests as the evidence.
- **A `str` operation demotes the `AllocatedPack` marker** — see
  `DR-SEAM-packs-and-token-economy-x-rules`, whose Traps section owns it.
- **A plugin that needs the record is asking for a SOURCE.** The prohibition
  on calling the harness is not a limitation to route around: if a section's
  content cannot be computed from `SectionRequestV1`, the missing piece belongs
  in a source that supplies it, not in a plugin that reaches for it. Nine
  sections were on the wrong side of this line until 2026-09-04 and were being
  computed in the admission code as a result.
