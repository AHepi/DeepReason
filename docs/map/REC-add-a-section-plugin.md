<!-- DR-REC-add-a-section-plugin -->
Verified-at: db5cc16ff
Verify: python -m pytest tests/test_seat_section_architecture.py -q
Owns:
Seams: DR-SEAM-packs-and-token-economy-x-rules

# Recipe — add a section to a seat's brief

## When this applies

You want a seat to be shown something it is not shown today, or to be shown
something it already gets in a different shape. The governing invariant is
`DR-INV-seat-section-plugins`; read it first if you have not.

**The whole point of this recipe is that it contains no source edit.** Every
one of the four steps below is a file the operator writes in their own
directory or a variable they set; none of them opens the tree. If you
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

A RUN reads that directory during setup, so the file you put there reaches
the seats of the next run without anything else being done to it. Both halves
of what the loader found reach the run's record: what loaded, and why the rest
did not.
`check: python -m pytest tests/test_seat_section_home.py::test_managed_path_loads_operator_plugins tests/test_seat_section_home.py::test_a_plugin_that_raises_on_import_is_a_notice_in_the_record -q`

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

A layout is DATA, so it is declared the same way the plugin is: a
`<anything>.layout.json` file in the same directory, holding the layout's own
`layout_id` and `entries`, plus an optional `default_for_seat` naming the seat
it binds to. A file that does not parse is REFUSED with
`SEAT_PACK_LAYOUT_FILE_UNPARSEABLE` naming the file, and registers nothing —
never a silent fall back to the seat's default, which is the failure an
operator would actually be hurt by.
`check: python -m pytest tests/test_seat_section_home.py::test_a_file_declared_layout_is_registered tests/test_seat_section_home.py::test_an_unparseable_layout_file_is_refused_typed -q`

**4. Select it.** `DEEPREASON_SEAT_PACK_LAYOUT=conjecturer=<your-layout-id>`,
or bind a `SeatShellV1` naming it. Nothing is a `Config` field and nothing
reaches the manifest — a layout knob on `Config` would move the digest of
every qualification bundle in the tree.
`check: python -c "
from deepreason.config import Config
banned = [f for f in Config.model_fields
          if 'LAYOUT' in f.upper() or 'SEAT_PACK' in f.upper()]
assert not banned, banned
from deepreason.llm import seat_sections
assert seat_sections.SEAT_PACK_LAYOUT_ENV == 'DEEPREASON_SEAT_PACK_LAYOUT'
"`

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
