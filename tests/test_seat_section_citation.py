"""Citation survives a free-text evidence plugin (SPEC S5, S6, A1).

R7 says a section plugin's output is not typed — free text the harness never
parses. Citation is the one place where that could silently cost a run a
capability, so this file pins the mechanism that prevents it.

The decisive fact is `DR-INV-reference-menu`'s FROZEN clause (b): *a menu
changes what the model is SHOWN; it may never change what the harness
ACCEPTS.* So a free-text evidence plugin cannot break citation VALIDITY — the
contract's enum decides that — it can only break citation USE, by failing to
print handles the schema still accepts. The registry, not the plugin, renders
the menu, which is what makes that unreachable.
"""

import pytest
from pydantic import BaseModel

from deepreason.llm.packs import DISCLOSED_ON_DROP, render_conj_pack
from deepreason.llm.reference_menu import MenuBinding, menu_renders_for
from deepreason.llm.seat_layouts import (
    CONJECTURER_LEGACY_LAYOUT,
    CRITIC_LEGACY_LAYOUT,
)
from deepreason.llm.seat_plugins import ensure_seeded
from deepreason.llm.seat_sections import (
    SeatPackLayoutEntryV1,
    SeatPackLayoutV1,
    SeatSectionError,
    SectionRenderV1,
    register_seat_pack_layout,
    register_section_plugin,
    resolve_section_plugin,
)
from tests.conj_pack_golden_cases import _seed_bare  # committed fixture inputs


@pytest.fixture(autouse=True)
def seeded():
    ensure_seeded()


class _NoParams(BaseModel):
    pass


class _FreeTextEvidence:
    """An operator's own evidence plugin: prose, no structure, nothing the
    harness parses. Exactly what R7 asks to be possible."""

    plugin_id = "dr.evidence.free-text-probe"
    plugin_version = "1.0.0"
    section_id = "citable-evidence-blocks"
    declared_handle_kinds = ("citable_block",)
    parameters_model = _NoParams

    def render(self, request, params):
        return SectionRenderV1(
            section_id=self.section_id,
            text="Some prose about the admitted evidence, in the operator's "
                 "own voice, mentioning no handle at all.",
            declared_handle_kinds=self.declared_handle_kinds,
        )


def test_a_free_text_evidence_plugin_cannot_suppress_the_menu(tmp_path):
    """A1's mechanism, end to end: the plugin renders whatever it likes and
    every bound citable block id STILL appears literally in the pack, because
    the menu is rendered by the walk's caller rather than by the plugin."""
    register_section_plugin(_FreeTextEvidence())
    layout = register_seat_pack_layout(
        SeatPackLayoutV1(
            layout_id="seat-pack.conjecturer.free-text-evidence-probe",
            entries=tuple(
                SeatPackLayoutEntryV1(
                    plugin_id=(
                        "dr.evidence.free-text-probe"
                        if entry.plugin_id == "dr.evidence.citable"
                        else entry.plugin_id
                    ),
                    priority=entry.priority,
                    droppable=entry.droppable,
                    compressible=entry.compressible,
                    min_tokens=entry.min_tokens,
                    params={} if entry.plugin_id == "dr.evidence.citable" else entry.params,
                )
                for entry in CONJECTURER_LEGACY_LAYOUT.entries
            ),
        )
    )
    bound = ("EV-001", "EV-002", "EV-003")
    problem, harness = _seed_bare(tmp_path)
    pack = render_conj_pack(
        problem,
        harness.state,
        harness.commitments,
        harness.blobs,
        vs_k=2,
        token_budget=6000,
        citable_evidence_context="ignored by this plugin",
        reference_menus=menu_renders_for(
            "conjecturer.turn.v6",
            MenuBinding(citable_block_ids=bound),
            handle_kinds=("citable_block",),
        ),
        seat_pack_layout=layout.layout_id,
    )
    assert "in the operator's own voice" in pack
    for block_id in bound:
        assert block_id in pack, block_id


def test_an_evidence_plugin_outside_the_disclosed_set_is_refused(tmp_path):
    """S6. A layout that routed evidence through a section whose absence is
    NOT disclosed would re-open the silent path by configuration — a dropped
    section leaves no header, so the pack would look like a run with no
    admitted evidence in it."""

    class _UndisclosedEvidence(_FreeTextEvidence):
        plugin_id = "dr.evidence.undisclosed-probe"
        section_id = "experimental-generation-context"  # not disclosed on drop

    register_section_plugin(_UndisclosedEvidence())
    with pytest.raises(SeatSectionError) as caught:
        register_seat_pack_layout(
            SeatPackLayoutV1(
                layout_id="seat-pack.conjecturer.undisclosed-evidence-probe",
                entries=(
                    SeatPackLayoutEntryV1(
                        plugin_id="dr.evidence.undisclosed-probe", priority=4
                    ),
                ),
            )
        )
    assert caught.value.code == "SEAT_PACK_LAYOUT_EVIDENCE_NOT_DISCLOSED"


def test_both_shipped_layouts_keep_their_evidence_disclosed():
    """The positive anchor: the refusal above would be vacuous if the shipped
    layouts did not actually satisfy it."""
    for layout in (CONJECTURER_LEGACY_LAYOUT, CRITIC_LEGACY_LAYOUT):
        for entry in layout.entries:
            plugin = resolve_section_plugin(entry.plugin_id, entry.plugin_version)
            if entry.plugin_id.startswith("dr.evidence.") or plugin.declared_handle_kinds:
                assert plugin.section_id in DISCLOSED_ON_DROP, (
                    layout.layout_id,
                    entry.plugin_id,
                )


def test_the_menu_is_rendered_by_the_walk_not_by_a_plugin():
    """S5, structurally: no seeded plugin calls the menu renderer, so a plugin
    cannot decide what legal-handle set the seat is shown."""
    import pathlib

    plugins = pathlib.Path("src/deepreason/llm/seat_plugins.py").read_text()
    packs = pathlib.Path("src/deepreason/llm/packs.py").read_text()
    assert "menu_renders_for" not in plugins
    assert "_menu_sections" not in plugins
    # ...and the renderers do call it, once each, at priority 4.
    assert packs.count("_menu_sections(reference_menus, 4)") == 2
