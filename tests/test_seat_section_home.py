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


# ------------------------------------------------- the managed run reads it


def _stub_mini_run():
    """Stand in for the reduced engine: the loader runs during SETUP, before
    the first call, so a stubbed loop is enough to decide whether it ran."""

    def mini_run(problems, endpoint, budget, root, max_cycles):
        return {
            "engine_profile": "mini",
            "model_profile": "compact",
            "stop": "queue-exhausted",
            "cycles": 1,
            "tokens": {"total": 0},
        }

    return mini_run


def test_managed_path_loads_operator_plugins(tmp_path, monkeypatch, clean_registry):
    """A plugin in the operator's own directory is read BY A RUN, not only by
    a test that calls the loader itself.

    Implements S0a (R7, C8) of the mini isolation programme. Before this
    landed, `load_operator_plugins` had no call site anywhere under `src/`, so
    `<DEEPREASON_HOME>/seat_plugins/` was a documented place to put a file
    that nothing ever opened. Both of the loader's lists — what loaded and
    what did not — reach the run's record, because a section missing with no
    reason given is the failure this whole loader exists to prevent.
    """
    import json

    from deepreason.shallow import run_shallow_question
    from tests.test_public_v6_facade import _configure

    state, _ = _configure(monkeypatch, tmp_path)
    plugins = seat_plugins_root(environ={"DEEPREASON_HOME": str(state)})
    plugins.mkdir(parents=True, exist_ok=True)
    (plugins / "dr.operator.probe@experimental-generation-context.tmpl").write_text(
        "GENERATION NOTES: {{ generation_context }}"
    )
    (plugins / "broken.py").write_text("this is not python (")

    monkeypatch.setattr("minireason.loop.run", _stub_mini_run(), raising=True)
    result = run_shallow_question("why does the sky look blue?")

    # The section itself: the run has seen the operator's file.
    assert resolve_section_plugin("dr.operator.probe").section_id == (
        "experimental-generation-context"
    )

    from deepreason.shallow import SHALLOW_SEAT_PLUGINS_RECORD

    disclosed = result["seat_plugins"]
    assert disclosed["loaded"] == ["dr.operator.probe"], disclosed
    assert [notice["code"] for notice in disclosed["notices"]] == [
        "SEAT_PLUGIN_UNLOADABLE"
    ], disclosed

    recorded = json.loads(
        (
            state / "shallow-runs" / result["run_id"] / SHALLOW_SEAT_PLUGINS_RECORD
        ).read_text()
    )
    assert recorded["loaded"] == ["dr.operator.probe"]
    assert "broken.py" in recorded["notices"][0]["path"]


def test_a_plugin_that_raises_on_import_is_a_notice_in_the_record(
    tmp_path, monkeypatch, clean_registry
):
    """Disclose, never die, measured THROUGH A RUN rather than through the
    loader alone.

    Implements S0a (R7, C10). The distinction from the loader-level case
    above is the one that matters operationally: a file that PARSES and then
    raises while executing gets as far as the interpreter before it fails, so
    only a run can show that the failure is disclosed rather than fatal.
    """
    import json

    from deepreason.shallow import (
        SHALLOW_SEAT_PLUGINS_RECORD,
        run_shallow_question,
    )
    from tests.test_public_v6_facade import _configure

    state, _ = _configure(monkeypatch, tmp_path)
    plugins = seat_plugins_root(environ={"DEEPREASON_HOME": str(state)})
    plugins.mkdir(parents=True, exist_ok=True)
    (plugins / "good.py").write_text(_GOOD)
    (plugins / "raises.py").write_text(
        'raise RuntimeError("the operator\'s own experiment blew up")\n'
    )

    monkeypatch.setattr("minireason.loop.run", _stub_mini_run(), raising=True)
    result = run_shallow_question("does a broken plugin stop a run?")

    # The run did not stop, and the plugins that did load are usable.
    assert result["completed"] is True
    assert result["seat_plugins"]["loaded"] == ["dr.operator.probe"]

    recorded = json.loads(
        (
            state / "shallow-runs" / result["run_id"] / SHALLOW_SEAT_PLUGINS_RECORD
        ).read_text()
    )
    assert len(recorded["notices"]) == 1, recorded
    notice = recorded["notices"][0]
    assert notice["code"] == "SEAT_PLUGIN_UNLOADABLE"
    assert "raises.py" in notice["path"]
    assert "RuntimeError" in notice["detail"], "a notice with no reason is a silent skip"


# ------------------------------------------ layouts declared in a file (S0b)


@pytest.fixture
def clean_layouts():
    from deepreason.llm.seat_sections import _LAYOUT_REGISTRY

    before = dict(_LAYOUT_REGISTRY)
    yield
    _LAYOUT_REGISTRY.clear()
    _LAYOUT_REGISTRY.update(before)


def test_a_file_declared_layout_is_registered(tmp_path, clean_layouts):
    """A composition is reachable WITHOUT writing Python.

    Implements S0b (R7, R9, R10, C8). `register_seat_pack_layout` was
    reachable only from Python, so `DR-REC-add-a-section-plugin` step 3 --
    "declare the layout that carries it" -- had no road an operator could
    take without editing the tree. That is the customization point the
    modularity law says must not require a code edit.
    """
    import json

    from deepreason.llm.seat_plugins import ensure_seeded
    from deepreason.llm.seat_sections import (
        resolve_seat_pack_layout,
        seat_pack_layout_ids,
    )

    ensure_seeded()
    (_root(tmp_path) / "probe.layout.json").write_text(
        json.dumps(
            {
                "layout_id": "seat-pack.operator.probe.v0",
                "entries": [
                    {"plugin_id": "dr.problem", "priority": 1},
                    {"plugin_id": "dr.criteria", "priority": 2, "droppable": True},
                ],
                "default_for_seat": "operator.probe",
            }
        )
    )

    loaded, notices = load_operator_plugins(home=tmp_path, environ={})
    assert notices == [], notices
    assert "seat-pack.operator.probe.v0" in loaded
    assert "seat-pack.operator.probe.v0" in seat_pack_layout_ids()

    layout = resolve_seat_pack_layout("operator.probe")
    assert layout.plugin_ids == ("dr.problem", "dr.criteria")
    assert layout.entry_for("dr.criteria").droppable is True


def test_an_unparseable_layout_file_is_refused_typed(tmp_path, clean_layouts):
    """A layout file that does not parse is REFUSED with a code, never a
    silent fallback to the seat's default.

    Implements S0b (C10). Two faces of one refusal: read directly, the reader
    raises a coded error naming the file; read by a run's loader, that same
    refusal becomes a typed notice and the run continues on what did load
    (disclose, never die). The failure this forbids is the third possibility
    -- a brief silently composed from something the operator did not ask for.
    """
    from deepreason.llm.seat_sections import (
        seat_pack_layout_from_file,
        seat_pack_layout_ids,
    )

    root = _root(tmp_path)
    (root / "broken.layout.json").write_text("{not json at all")
    (root / "wrong-shape.layout.json").write_text(
        '{"layout_id": "seat-pack.operator.bad.v0", "entries": [{"priority": 1}]}'
    )

    for name, code in (
        ("broken.layout.json", "SEAT_PACK_LAYOUT_FILE_UNPARSEABLE"),
        ("wrong-shape.layout.json", "SEAT_PACK_LAYOUT_FILE_UNPARSEABLE"),
    ):
        with pytest.raises(SeatSectionError) as caught:
            seat_pack_layout_from_file(root / name)
        assert caught.value.code == code, (name, caught.value)
        assert name in str(caught.value), caught.value

    loaded, notices = load_operator_plugins(home=tmp_path, environ={})
    assert loaded == []
    assert [notice["code"] for notice in notices] == [
        "SEAT_PACK_LAYOUT_FILE_UNPARSEABLE",
        "SEAT_PACK_LAYOUT_FILE_UNPARSEABLE",
    ], notices
    assert all(notice["detail"] for notice in notices), "a notice with no reason"
    assert "seat-pack.operator.bad.v0" not in seat_pack_layout_ids()
