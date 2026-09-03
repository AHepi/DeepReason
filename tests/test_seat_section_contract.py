"""The section contract's one load-bearing distinction (SPEC S1.3).

A plugin returning `None` says "this section has nothing this cycle". A
plugin returning an EMPTY STRING says "this section rendered, and rendered to
nothing", which is not a thing the pack can express: `allocate_pack` drops an
unaffordable optional section leaving no header and no placeholder, so absence
is the only signal a section has, and two different situations may not share
it (`DR-INV-render-layout` Traps; `DR-CON-packs-and-token-economy`'s NO SILENT
CAPS rule).

Implements R7 (a plugin's output is free text) bounded by A4 (its receipt is
not).
"""

import pytest
from pydantic import BaseModel, ValidationError

from deepreason.llm.seat_sections import (
    DISPOSITIONS,
    SeatSectionError,
    SeatSectionPluginV1,
    SectionReceiptV1,
    SectionRenderV1,
    SectionRequestV1,
)


class _NoParams(BaseModel):
    pass


class _SilentPlugin:
    """The legal way to say nothing."""

    plugin_id = "dr.test.silent"
    plugin_version = "1.0.0"
    parameters_model = _NoParams

    def render(self, request, params):
        return None


def test_an_empty_text_is_an_error_not_an_absence():
    with pytest.raises(ValidationError):
        SectionRenderV1(section_id="probe", text="")


def test_none_is_a_legal_absence():
    plugin = _SilentPlugin()
    assert plugin.render(SectionRequestV1(), _NoParams()) is None


def test_a_one_character_render_is_legal():
    """The floor is EMPTY, not SHORT. A plugin whose content happens to be
    tiny is rendering, not declining."""
    render = SectionRenderV1(section_id="probe", text="x")
    assert render.text == "x"


def test_the_request_is_frozen_and_closed():
    """A plugin that could mutate its request could reach the run's state
    through the brief — the one direction the seat-is-a-shell law forbids."""
    request = SectionRequestV1(supplied={"generation_context": "x"})
    with pytest.raises(ValidationError):
        request.supplied = {}
    with pytest.raises(ValidationError):
        SectionRequestV1(unknown_field=True)


def test_the_render_is_frozen_and_closed():
    render = SectionRenderV1(section_id="probe", text="x")
    with pytest.raises(ValidationError):
        render.text = "y"
    with pytest.raises(ValidationError):
        SectionRenderV1(section_id="probe", text="x", unknown_field=True)


def test_a_section_id_may_not_be_empty():
    """A section with no id renders no `## ` header, which is the same silent
    absence an empty text would be."""
    with pytest.raises(ValidationError):
        SectionRenderV1(section_id="", text="x")


@pytest.mark.parametrize("disposition", DISPOSITIONS)
def test_every_declared_disposition_is_accepted(disposition):
    receipt = SectionReceiptV1(
        section_id="probe",
        plugin_id="dr.test.silent",
        plugin_version="1.0.0",
        parameters_digest="sha256:" + "0" * 64,
        source_bytes=10,
        rendered_bytes=10,
        disposition=disposition,
    )
    assert receipt.disposition == disposition


def test_an_undeclared_disposition_is_a_typed_refusal():
    """Typed, and asserted on the CODE rather than the message: a guard gutted
    to keep its string would pass a message-grep."""
    with pytest.raises(SeatSectionError) as caught:
        SectionReceiptV1(
            section_id="probe",
            plugin_id="dr.test.silent",
            plugin_version="1.0.0",
            parameters_digest="sha256:" + "0" * 64,
            source_bytes=10,
            rendered_bytes=10,
            disposition="clipped",
        )
    assert caught.value.code == "SEAT_SECTION_DISPOSITION_UNKNOWN"


def test_absent_and_dropped_are_different_dispositions():
    """`absent` is the plugin declining; `dropped` is the allocator cutting
    content that existed. Collapsing them would lose exactly the distinction
    this file exists to protect."""
    assert "absent" in DISPOSITIONS and "dropped" in DISPOSITIONS


def test_a_plugin_satisfies_the_protocol_structurally():
    """The protocol is runtime-checkable so a home-directory plugin can be
    refused at LOAD time rather than at render time (S3.4)."""
    assert isinstance(_SilentPlugin(), SeatSectionPluginV1)
    assert not isinstance(object(), SeatSectionPluginV1)
