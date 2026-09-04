<!-- DR-REC-add-a-section-plugin -->
Verified-at: 770ea1344
Verify: python -m pytest tests/test_seat_section_architecture.py -q
Owns:
Seams: DR-SEAM-packs-and-token-economy-x-rules

# Recipe — add a section to a seat's brief

## When this applies

You want a seat to be shown something it is not shown today, or to be shown
something it already gets in a different shape. The governing invariant is
`DR-INV-seat-section-plugins`; read it first if you have not.

**The whole point of this recipe is that it contains no source edit.** If you
find yourself opening a file under `src/deepreason/llm/`, stop: either you are
adding a NEW KIND of thing (in which case the invariant document is what
changes, and this recipe with it), or the interface has a gap worth recording
rather than routing around.

## The four steps

**1. Decide whether the content already reaches the renderer.** A brief's
sections divide in two. Most are computed inside their plugin from the run's
state. The rest need a dossier receipt, a fence sequence, a work order or the
open-criticism view — things a renderer does not hold — and reach the plugin
through `SectionRequestV1.supplied`.

For the CONJECTURER those are computed by registered SOURCES, so this recipe
covers them too: register a source and add its bundle entry, still with no
source edit (`DR-INV-seat-section-sources`, step 2b below). For the CRITIC's
four they are still computed in `rules/crit.py` and passed in one by one; if
your content is one of those, this recipe does not cover you yet — that is a
seam change, and `docs/map/REC-change-a-seam.md` is the one to follow.

**2. Write the plugin.** A `.py` file in
`<provider_state_dir>/seat_plugins/` declaring a module-level `PLUGIN`, or a
`.tmpl` file named `<plugin-id>@<section-id>.tmpl` if you only want a
different FORMAT and no code. Declare `requires` for anything your render
cannot do without, so your plugin declines rather than raises in a seat whose
request does not carry it.

**2b. If it needs the record, write a SOURCE too.** A source reads the state
and the record, computes one value, and appends NOTHING — one write is
permitted and must be declared (`writes_blobs`), and it is content-addressed
blob materialisation only. Register it, add a bundle entry naming its stage,
and your plugin formats what it produced. The stage matters: see
`DR-INV-seat-section-sources` for what the caller does at each boundary.

**3. Register a layout that includes it.** Copy a shipped layout's entries and
add yours; the entry carries the priority and the drop/compress flags, not the
plugin. Priorities 99 and 100 are reserved for the withheld notice and the
restated question.

**4. Select it.** `DEEPREASON_SEAT_PACK_LAYOUT=conjecturer=<your-layout-id>`,
or bind a `SeatShellV1` naming it. Nothing is a `Config` field and nothing
reaches the manifest.

## What you must not do, and why

- **Do not give the plugin a score, rank, weight or authority field.** Shape
  may never buy standing (the formalism-optional law). An architecture test
  goes red if any generation-side name is read where standing is decided.
- **Do not render a menu from inside a plugin.** A plugin may render evidence
  however it likes; it may not also suppress the legal-handle menu, or a
  configuration could silently cost a run its ability to cite
  (`DR-INV-reference-menu`, FROZEN clause (b)).
- **Do not put an evidence section outside `DISCLOSED_ON_DROP`.** Registration
  refuses it: a dropped section leaves no header, so a pack whose evidence the
  budget cut would look exactly like a run that never had any.
- **Do not return an empty string.** Return `None`. Empty is an error; `None`
  is the legal way to have nothing this cycle.

## Proving it worked

Your section's text appears in the rendered pack, and its receipt appears in
the section receipts with a `rendered` disposition. If the allocator cut it,
the receipt says `dropped` and the pack carries a `context-withheld` notice
naming it.
`check: python -m pytest tests/test_seat_section_architecture.py -k limb2 -q`

And the check that makes this recipe true rather than aspirational: adding a
section changes no file under `src/`.
`check: python -c "
import ast, pathlib
source = pathlib.Path('tests/test_seat_section_architecture.py').read_text()
fn = next(n for n in ast.walk(ast.parse(source))
          if isinstance(n, ast.FunctionDef)
          and n.name == 'test_limb2_a_new_section_needs_no_source_edit')
body = ast.get_source_segment(source, fn)
assert 'st_mtime_ns' in body, 'the no-source-edit claim is asserted, not measured'
assert 'seat_plugins_root' in body
"`
