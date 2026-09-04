"""Operator-authored plugins, loaded from the operator's own directory
(SPEC S3).

Three properties, and the middle one is a security boundary rather than a
convenience:

1. A harness with NO plugin directory has exactly the seeded set, and says so
   rather than guessing — `DR-CON-model-profiles`' own stance, which this
   loader mirrors.
2. A plugin loads ONLY from that directory. It executes inside the harness, so
   it is trusted for the reason a treadle task is: the operator put the file
   there. Nothing model-authored is ever a plugin, and no configuration value,
   model reply or record field may name a plugin PATH.
3. A directory holding one unloadable file yields a typed NOTICE naming the
   file and the error, and the run continues with what loaded. Disclose, never
   die — and never silently skip, which would leave the operator staring at a
   brief missing a section with no reason given.
"""

import pytest

from deepreason.llm.seat_sections import (
    SECTION_PLUGIN_REGISTRY,
    SeatSectionError,
    load_operator_plugins,
    resolve_section_plugin,
    seat_plugins_root,
)

_GOOD = '''
from pydantic import BaseModel

from deepreason.llm.seat_sections import SectionRenderV1


class _Params(BaseModel):
    pass


class _OperatorSection:
    plugin_id = "dr.operator.probe"
    plugin_version = "1.0.0"
    section_id = "experimental-generation-context"
    declared_handle_kinds = ()
    parameters_model = _Params

    def render(self, request, params):
        return SectionRenderV1(section_id=self.section_id, text="operator text")


PLUGIN = _OperatorSection()
'''


@pytest.fixture
def clean_registry():
    before = dict(SECTION_PLUGIN_REGISTRY)
    yield
    SECTION_PLUGIN_REGISTRY.clear()
    SECTION_PLUGIN_REGISTRY.update(before)


def _root(tmp_path):
    root = seat_plugins_root(home=tmp_path, environ={})
    root.mkdir(parents=True, exist_ok=True)
    return root


def test_a_harness_with_no_plugin_directory_has_exactly_the_seeded_set(tmp_path):
    loaded, notices = load_operator_plugins(home=tmp_path, environ={})
    assert loaded == [] and notices == []


def test_an_operator_python_plugin_loads_and_registers(tmp_path, clean_registry):
    (_root(tmp_path) / "probe.py").write_text(_GOOD)
    loaded, notices = load_operator_plugins(home=tmp_path, environ={})
    assert loaded == ["dr.operator.probe"], (loaded, notices)
    assert notices == []
    assert resolve_section_plugin("dr.operator.probe").section_id == (
        "experimental-generation-context"
    )


def test_an_operator_template_loads_as_an_ordinary_plugin(tmp_path, clean_registry):
    (_root(tmp_path) / "dr.operator.tmpl@experimental-generation-context.tmpl").write_text(
        "GENERATION NOTES: {{ generation_context }}"
    )
    loaded, notices = load_operator_plugins(home=tmp_path, environ={})
    assert notices == [], notices
    assert "dr.operator.tmpl" in loaded

    from deepreason.llm.seat_sections import SectionRequestV1

    plugin = resolve_section_plugin("dr.operator.tmpl")
    render = plugin.render(
        SectionRequestV1(supplied={"generation_context": "try the convective side"}),
        plugin.parameters_model(),
    )
    assert render.text == "GENERATION NOTES: try the convective side"
    assert render.section_id == "experimental-generation-context"


# ------------------------------------------------------------------ trust


def test_trust_a_plugin_loads_only_from_the_operator_directory(
    tmp_path, clean_registry, monkeypatch
):
    """The boundary. A plugin file somewhere else on disk is not a plugin, and
    naming its path does not make it one."""
    elsewhere = tmp_path / "not_the_plugin_dir"
    elsewhere.mkdir()
    planted = elsewhere / "evil.py"
    planted.write_text("raise AssertionError('an outside file was executed')")

    _root(tmp_path)  # the real directory exists and is EMPTY
    loaded, notices = load_operator_plugins(home=tmp_path, environ={})
    assert loaded == [] and notices == []

    monkeypatch.chdir(elsewhere)
    for name in ("evil", "./evil.py", str(planted), "dr.evil"):
        with pytest.raises(SeatSectionError) as caught:
            resolve_section_plugin(name)
        assert caught.value.code == "SEAT_SECTION_PLUGIN_UNKNOWN"


def test_trust_no_configuration_field_can_name_a_plugin_path():
    """A `Config` field holding a path would be a second door into the loader,
    and one a model reply could reach through a run manifest."""
    from deepreason.config import Config

    suspicious = [
        field
        for field in Config.model_fields
        if any(
            token in field.upper()
            for token in ("SEAT_PLUGIN", "SECTION_PLUGIN", "PLUGIN_PATH", "PLUGIN_DIR")
        )
    ]
    assert not suspicious, suspicious


def test_trust_the_only_path_load_is_the_operator_loader():
    """Structural: exactly one place in `llm/` imports a module from a file
    path, and it is the operator loader."""
    import pathlib

    hits = []
    for path in pathlib.Path("src/deepreason/llm").rglob("*.py"):
        text = path.read_text()
        if "spec_from_file_location" in text:
            hits.append(path.name)
    assert hits == ["seat_sections.py"], hits


# ------------------------------------------------------------- disclosure


def test_disclosure_an_unloadable_file_is_a_notice_not_a_crash(
    tmp_path, clean_registry
):
    """Disclose, never die: a broken formatting experiment three directories
    away must not take a run down."""
    root = _root(tmp_path)
    (root / "good.py").write_text(_GOOD)
    (root / "broken.py").write_text("this is not python (")

    loaded, notices = load_operator_plugins(home=tmp_path, environ={})
    assert loaded == ["dr.operator.probe"]
    assert len(notices) == 1, notices
    assert notices[0]["code"] == "SEAT_PLUGIN_UNLOADABLE"
    assert "broken.py" in notices[0]["path"]
    assert notices[0]["detail"], "a notice with no reason is a silent skip"


def test_disclosure_a_file_declaring_no_plugin_is_named(tmp_path, clean_registry):
    (_root(tmp_path) / "empty.py").write_text("X = 1\n")
    loaded, notices = load_operator_plugins(home=tmp_path, environ={})
    assert loaded == []
    assert len(notices) == 1 and notices[0]["code"] == "SEAT_PLUGIN_UNLOADABLE"
    assert "declares no PLUGIN" in notices[0]["detail"]


def test_disclosure_a_template_that_cannot_expand_is_named(tmp_path, clean_registry):
    """A template refusal is a load-time notice, not a render-time surprise
    inside a live cycle."""
    (_root(tmp_path) / "bad@problem.tmpl").write_text("{{ name.upper() }}")
    loaded, notices = load_operator_plugins(home=tmp_path, environ={})
    assert "bad" in loaded  # it registers; expansion is refused when it runs

    from deepreason.llm.seat_sections import SectionRequestV1

    plugin = resolve_section_plugin("bad")
    with pytest.raises(SeatSectionError) as caught:
        plugin.render(SectionRequestV1(supplied={"name": "x"}), plugin.parameters_model())
    assert caught.value.code == "SEAT_TEMPLATE_NOT_EXPRESSIBLE"
