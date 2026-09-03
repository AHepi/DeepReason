"""The section-plugin registry: the VERSIONED layer (SPEC S2).

Modelled on `llm/layout.py::register_layout_policy`, whose own invariant
document proves a registry needs no consumer edit to gain an entry. Two
properties are load-bearing here and are tested as such: a version resolves
NUMERICALLY (so "1.10.0" beats "1.9.0"), and an unregistered id is a typed
refusal rather than a filesystem lookup.
"""

import pytest
from pydantic import BaseModel

from deepreason.llm.seat_sections import (
    SECTION_PLUGIN_REGISTRY,
    SeatSectionError,
    SectionRenderV1,
    SectionRequestV1,
    register_section_plugin,
    resolve_section_plugin,
    section_plugin_ids,
)


class _NoParams(BaseModel):
    pass


class _Probe:
    parameters_model = _NoParams

    def __init__(self, plugin_id, version, text="x"):
        self.plugin_id = plugin_id
        self.plugin_version = version
        self._text = text

    def render(self, request: SectionRequestV1, params: BaseModel):
        return SectionRenderV1(section_id=self.plugin_id, text=self._text)


@pytest.fixture
def clean_registry():
    """The registry is process-global, like the layout policy registry it is
    modelled on, so a test that adds to it puts it back."""
    before = dict(SECTION_PLUGIN_REGISTRY)
    yield
    SECTION_PLUGIN_REGISTRY.clear()
    SECTION_PLUGIN_REGISTRY.update(before)


def test_registering_and_resolving_a_plugin(clean_registry):
    plugin = register_section_plugin(_Probe("dr.test.registry", "1.0.0"))
    assert resolve_section_plugin("dr.test.registry") is plugin
    assert resolve_section_plugin("dr.test.registry", "1.0.0") is plugin
    assert "dr.test.registry" in section_plugin_ids()


def test_registering_the_same_object_twice_is_idempotent(clean_registry):
    """A module imported twice must not be an error."""
    plugin = _Probe("dr.test.idempotent", "1.0.0")
    register_section_plugin(plugin)
    register_section_plugin(plugin)
    assert resolve_section_plugin("dr.test.idempotent") is plugin


def test_re_registering_one_version_with_a_different_object_is_refused(
    clean_registry,
):
    """A version names ONE render, or two receipts citing it do not mean the
    same thing."""
    register_section_plugin(_Probe("dr.test.conflict", "1.0.0", text="a"))
    with pytest.raises(SeatSectionError) as caught:
        register_section_plugin(_Probe("dr.test.conflict", "1.0.0", text="b"))
    assert caught.value.code == "SEAT_SECTION_PLUGIN_CONFLICT"


def test_unpinned_resolves_to_the_highest_version_numerically(clean_registry):
    """Regression against the obvious bug: a plain string sort puts "1.10.0"
    before "1.9.0" and would silently resolve to the wrong plugin."""
    register_section_plugin(_Probe("dr.test.versions", "1.9.0", text="nine"))
    newest = register_section_plugin(
        _Probe("dr.test.versions", "1.10.0", text="ten")
    )
    assert resolve_section_plugin("dr.test.versions") is newest
    assert (
        resolve_section_plugin("dr.test.versions", "1.9.0")._text == "nine"
    )


def test_an_unregistered_id_is_a_typed_refusal_and_not_a_load_by_path(
    clean_registry, tmp_path, monkeypatch
):
    """S3.2's trust boundary, asserted rather than described.

    A plugin's code runs inside the harness, so the ONLY thing that may
    introduce one is the operator placing a file in their own plugin
    directory. An id that does not resolve must therefore be refused, never
    looked up on disk — otherwise a configuration value, a model reply or a
    fetched document naming a path would be arbitrary code execution wearing
    a plugin's clothes.
    """
    planted = tmp_path / "dr.evil.py"
    planted.write_text("raise AssertionError('a plugin was loaded by path')")
    monkeypatch.chdir(tmp_path)

    with pytest.raises(SeatSectionError) as caught:
        resolve_section_plugin("dr.evil")
    assert caught.value.code == "SEAT_SECTION_PLUGIN_UNKNOWN"

    for candidate in ("./dr.evil.py", str(planted), "dr.evil.py"):
        with pytest.raises(SeatSectionError) as caught:
            resolve_section_plugin(candidate)
        assert caught.value.code == "SEAT_SECTION_PLUGIN_UNKNOWN"


def test_an_unregistered_version_of_a_registered_id_is_refused(clean_registry):
    register_section_plugin(_Probe("dr.test.pinned", "1.0.0"))
    with pytest.raises(SeatSectionError) as caught:
        resolve_section_plugin("dr.test.pinned", "2.0.0")
    assert caught.value.code == "SEAT_SECTION_PLUGIN_UNKNOWN"


def test_a_malformed_plugin_is_refused_at_registration(clean_registry):
    """Refused at LOAD rather than at render, so an operator's typo surfaces
    where they can see it."""
    with pytest.raises(SeatSectionError) as caught:
        register_section_plugin(object())
    assert caught.value.code == "SEAT_SECTION_PLUGIN_MALFORMED"
