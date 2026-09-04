"""The modularity law's "enforced" clause: checks that can FAIL (SPEC S11).

"Enforced" means a check that goes red when a consumer bypasses the interface
or when a customization point requires a code edit to use (CLAUDE.md, the
modularity law, 2026-08-26). Three limbs, each red under a specific bypass.
A test that cannot fail is not a check — `docs_verify --audit`'s own standard,
owed here too — so each limb's mutation is named in its docstring and the two
that need a planted violation carry one in the tranche's record.
"""

import ast
import pathlib

import pytest

PACKS = pathlib.Path("src/deepreason/llm/packs.py")


def _function(path: pathlib.Path, name: str):
    source = path.read_text()
    return next(
        n
        for n in ast.walk(ast.parse(source))
        if isinstance(n, ast.FunctionDef) and n.name == name
    )


def _calls(node, name: str) -> int:
    return sum(
        1
        for c in ast.walk(node)
        if isinstance(c, ast.Call) and getattr(c.func, "id", "") == name
    )


# ------------------------------------------------------------------ limb 1
# RED if a renderer constructs a section other than through the registry. A
# pinned COUNT rather than an asserted intent, the shape DR-INV-render-layout
# already uses for its `_head` bypass trap: a bypass ADDS a call, and a
# count notices what an existence check would not.


@pytest.mark.parametrize("renderer", ["render_conj_pack", "render_crit_pack"])
def test_limb1_no_renderer_builds_a_section_outside_the_registry(renderer):
    fn = _function(PACKS, renderer)
    assert _calls(fn, "_pack_section") == 0, renderer
    assert _calls(fn, "_walk_seat_layout") == 1, renderer


def test_limb1_the_walk_is_the_only_resolver():
    """One door. A second `resolve_section_plugin` CALL site in `packs.py`
    would be a section built outside the walk's accounting.

    Counted as calls via the AST rather than as text: the name also appears in
    prose and in an import, and a text count would have pinned those too —
    brittle to a docstring edit and silent about the thing it guards.
    """
    tree = ast.parse(PACKS.read_text())
    calls = [
        c
        for c in ast.walk(tree)
        if isinstance(c, ast.Call)
        and getattr(c.func, "id", "") == "resolve_section_plugin"
    ]
    assert len(calls) == 1, len(calls)
    inside = _function(PACKS, "_walk_seat_layout")
    assert _calls(inside, "resolve_section_plugin") == 1


def test_limb1_the_seeded_plugins_do_not_build_pack_sections():
    """A plugin returns TEXT; turning that into a budgeted section is the
    walk's job. A plugin that made its own `PackSection` would set its own
    priority and the token economy would be two policies again."""
    plugins = pathlib.Path("src/deepreason/llm/seat_plugins.py").read_text()
    assert "_pack_section" not in plugins
    assert "PackSection" not in plugins
    assert "allocate_pack" not in plugins


# ------------------------------------------------------------------ limb 2
# RED if adding a section requires a source edit. This is the half of the
# modularity law a behaviour test alone misses.


def test_limb2_a_new_section_needs_no_source_edit(tmp_path, monkeypatch):
    """Registers a brand-new plugin from a TEMP HOME DIRECTORY, renders a pack
    with it in the layout, and asserts its text appears and its receipt is
    written — touching no file under `src/`."""
    from deepreason.llm.packs import render_conj_pack
    from deepreason.llm.seat_layouts import CONJECTURER_LEGACY_LAYOUT
    from deepreason.llm.seat_plugins import ensure_seeded
    from deepreason.llm.seat_sections import (
        SeatPackLayoutEntryV1,
        SeatPackLayoutV1,
        load_operator_plugins,
        register_seat_pack_layout,
        seat_plugins_root,
    )
    from tests.conj_pack_golden_cases import _seed_bare

    ensure_seeded()
    before = {p.stat().st_mtime_ns for p in pathlib.Path("src/deepreason").rglob("*.py")}

    root = seat_plugins_root(home=tmp_path, environ={})
    root.mkdir(parents=True, exist_ok=True)
    (root / "arch.py").write_text(
        "from pydantic import BaseModel\n"
        "from deepreason.llm.seat_sections import SectionRenderV1\n"
        "class _P(BaseModel):\n    pass\n"
        "class _S:\n"
        "    plugin_id = 'dr.operator.architecture'\n"
        "    plugin_version = '1.0.0'\n"
        "    section_id = 'experimental-generation-context'\n"
        "    declared_handle_kinds = ()\n"
        "    requires = ()\n"
        "    parameters_model = _P\n"
        "    def render(self, request, params):\n"
        "        return SectionRenderV1(section_id=self.section_id,\n"
        "                               text='A SECTION NOBODY EDITED CODE FOR')\n"
        "PLUGIN = _S()\n"
    )
    loaded, notices = load_operator_plugins(home=tmp_path, environ={})
    assert loaded == ["dr.operator.architecture"], (loaded, notices)

    layout = register_seat_pack_layout(
        SeatPackLayoutV1(
            layout_id="seat-pack.conjecturer.architecture-probe",
            entries=CONJECTURER_LEGACY_LAYOUT.entries
            + (
                SeatPackLayoutEntryV1(
                    plugin_id="dr.operator.architecture", priority=6
                ),
            ),
        )
    )
    problem, harness = _seed_bare(tmp_path)
    receipts: list = []
    pack = render_conj_pack(
        problem,
        harness.state,
        harness.commitments,
        harness.blobs,
        vs_k=2,
        token_budget=4000,
        seat_pack_layout=layout.layout_id,
        section_receipts=receipts,
    )
    assert "A SECTION NOBODY EDITED CODE FOR" in pack
    assert any(r.plugin_id == "dr.operator.architecture" for r in receipts)

    after = {p.stat().st_mtime_ns for p in pathlib.Path("src/deepreason").rglob("*.py")}
    assert before == after, "a file under src/ changed while adding a section"


# ------------------------------------------------------------------ limb 3
# S11.3, widened by §17.6 to the seat-is-a-shell law's own scope boundary:
# the shell governs how content is GENERATED and may never reach what counts
# as EVIDENCE.

# The generation-side IDENTIFIERS. Deliberately not `disposition`: that is an
# ordinary English word this repo already uses for something unrelated
# (`scheduler.py`'s guard-finding dispositions), so including it would make
# this check fire on a pre-existing name rather than on a real read — a check
# that cries wolf gets weakened, and a weakened check guards nothing.
_GENERATION_SIDE_NAMES = (
    "seat_id",
    "shell_id",
    "layout_id",
    "form_id",
    "plugin_id",
    "plugin_version",
    "parameters_digest",
    "SectionReceiptV1",
    "SeatShellV1",
    "SeatPackLayout",
    "resolve_seat_shell",
    "resolve_seat_pack_layout",
    # The SOURCE layer, added 2026-09-04 when the caller-computed sections
    # moved behind the interface. A source decides what a seat is SHOWN, so
    # its names belong on this list for the same reason a plugin's do.
    "bundle_id",
    "source_version",
    "SectionSourceReceiptV1",
    "SeatSourceBundle",
    "resolve_seat_source_bundle",
    "resolve_section_source",
)

_EVIDENCE_SIDE = ("src/deepreason/scheduler", "src/deepreason/adjudication")


def test_limb3_shape_buys_nothing_in_scheduler_or_adjudication():
    """RED if any generation-side name is read where standing is decided.

    These two packages decide rank and status and nothing else, so the check
    is total over them: not one of these names may appear at all.
    """
    offenders = []
    for package in _EVIDENCE_SIDE:
        for path in pathlib.Path(package).rglob("*.py"):
            text = path.read_text()
            for name in _GENERATION_SIDE_NAMES:
                if name in text:
                    offenders.append(f"{path}: {name}")
    assert not offenders, offenders


def test_limb3_shape_buys_nothing_on_the_rules_authority_paths():
    """`rules/` both DISPATCHES and ADJUDICATES, so a total ban would be wrong
    — a dispatch site legitimately names its own seat. The check is therefore
    scoped to the functions that decide standing: any function that registers
    a warrant, sets a status, or mints an admission may not read a
    generation-side name.
    """
    authority_markers = (
        "register_fail_warrant",
        "Status.",
        "register_artifact",
        "create_artifact",
        "Warrant(",
    )
    offenders = []
    for path in pathlib.Path("src/deepreason/rules").rglob("*.py"):
        source = path.read_text()
        tree = ast.parse(source)
        for node in ast.walk(tree):
            if not isinstance(node, ast.FunctionDef):
                continue
            body = ast.get_source_segment(source, node) or ""
            if not any(marker in body for marker in authority_markers):
                continue
            for name in _GENERATION_SIDE_NAMES:
                if name in body:
                    offenders.append(f"{path}::{node.name}: {name}")
    assert not offenders, offenders


def test_limb3_the_shell_carries_nothing_that_could_buy_standing():
    """The criticism-source socket's own standard, owed here: a contract with
    a score field invites a consumer to read it. There is none to read."""
    from deepreason.llm.seat_sections import (
        SeatPackLayoutEntryV1,
        SeatShellV1,
        SectionReceiptV1,
    )
    from deepreason.seat_sources import (
        SectionSourceReceiptV1,
        SectionSourceResultV1,
        SeatSourceBundleEntryV1,
    )

    forbidden = {
        "score",
        "rank",
        "weight",
        "confidence",
        "priority",
        "authority",
        "status",
        "immunity",
    }
    # The SOURCE layer is held to the same standard as the plugin layer, and
    # for the same reason: a source decides what a seat is SHOWN, so a field
    # it could stamp with a rank would be a generation-side name arriving on
    # the evidence side by the back door.
    for model in (
        SeatShellV1,
        SectionReceiptV1,
        SectionSourceReceiptV1,
        SectionSourceResultV1,
        SeatSourceBundleEntryV1,
    ):
        overlap = forbidden & set(model.model_fields)
        assert not overlap, (model.__name__, overlap)
    # `SeatPackLayoutEntryV1.priority` is the ALLOCATOR's priority — which
    # bytes fit a budget — and is named here so the exception is deliberate
    # rather than an oversight. It is never read on the evidence side, which
    # the two checks above are what prove.
    assert "priority" in SeatPackLayoutEntryV1.model_fields
