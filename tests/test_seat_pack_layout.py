"""The seat pack layout: composition as configuration (SPEC S10, §17.1).

`RenderLayoutPolicyV1` governs ARRANGEMENT — where a rendered prompt puts what
it carries. This governs COMPOSITION — which parts it carries at all. The two
are siblings and a run reads both.

The FREE layer's one rule is tested here: a value outside its declared
envelope is REFUSED, never clamped. A silently clamped value is a
configuration that did not do what it says.
"""

import os

import pytest

from deepreason.llm.seat_sections import (
    MAXIMUM_ENTRY_PRIORITY,
    MAXIMUM_MIN_TOKENS,
    SEAT_PACK_LAYOUT_ENV,
    SeatPackLayoutEntryV1,
    SeatPackLayoutV1,
    SeatSectionError,
    register_seat_pack_layout,
    resolve_seat_pack_layout,
)


def _entry(plugin_id="dr.test.entry", **kwargs):
    kwargs.setdefault("priority", 1)
    return SeatPackLayoutEntryV1(plugin_id=plugin_id, **kwargs)


def test_an_entry_carries_its_own_allocation_facts():
    entry = _entry(priority=4, droppable=True, compressible=True, min_tokens=64)
    assert (entry.priority, entry.droppable, entry.min_tokens) == (4, True, 64)


@pytest.mark.parametrize(
    "field,value",
    [
        ("priority", MAXIMUM_ENTRY_PRIORITY + 1),
        ("priority", 0),
        ("min_tokens", MAXIMUM_MIN_TOKENS + 1),
        ("max_render_bytes", 0),
    ],
)
def test_an_out_of_envelope_value_raises_rather_than_clamping(field, value):
    """The FREE layer refuses; it does not quietly fit the value into range."""
    with pytest.raises(SeatSectionError) as caught:
        _entry(**{field: value})
    assert caught.value.code == "SEAT_PACK_LAYOUT_OUT_OF_ENVELOPE"


def test_priority_99_and_100_are_outside_the_envelope():
    """Reserved: the allocator orders by `(priority, id)` and 99 is the
    withheld notice, 100 the restated question. An entry claiming either would
    interleave with them."""
    for reserved in (99, 100):
        with pytest.raises(SeatSectionError):
            _entry(priority=reserved)


def test_a_layout_refuses_the_same_plugin_twice():
    """A section id renders once per pack; twice would produce two `## id`
    headers the allocator budgets independently."""
    with pytest.raises(SeatSectionError) as caught:
        SeatPackLayoutV1(
            layout_id="probe-duplicate",
            entries=[_entry("dr.test.same"), _entry("dr.test.same", priority=2)],
        )
    assert caught.value.code == "SEAT_PACK_LAYOUT_DUPLICATE_PLUGIN"


def test_a_layout_is_frozen_and_closed():
    layout = SeatPackLayoutV1(layout_id="probe-frozen", entries=[_entry()])
    with pytest.raises(Exception):
        layout.layout_id = "other"
    with pytest.raises(Exception):
        SeatPackLayoutV1(layout_id="probe-frozen-2", unknown_flag=True)


def test_re_registering_one_id_with_different_values_is_refused():
    first = SeatPackLayoutV1(layout_id="probe-conflict", entries=[_entry()])
    register_seat_pack_layout(first)
    register_seat_pack_layout(first)  # idempotent
    with pytest.raises(SeatSectionError) as caught:
        register_seat_pack_layout(
            SeatPackLayoutV1(
                layout_id="probe-conflict", entries=[_entry(priority=2)]
            )
        )
    assert caught.value.code == "SEAT_PACK_LAYOUT_CONFLICT"


def test_selection_is_argument_then_environment_then_default(monkeypatch):
    register_seat_pack_layout(
        SeatPackLayoutV1(layout_id="probe-seat-default", entries=[_entry()]),
        default_for_seat="probe-seat",
    )
    register_seat_pack_layout(
        SeatPackLayoutV1(layout_id="probe-seat-other", entries=[_entry(priority=3)])
    )

    monkeypatch.delenv(SEAT_PACK_LAYOUT_ENV, raising=False)
    assert resolve_seat_pack_layout("probe-seat").layout_id == "probe-seat-default"

    monkeypatch.setenv(SEAT_PACK_LAYOUT_ENV, "probe-seat=probe-seat-other")
    assert resolve_seat_pack_layout("probe-seat").layout_id == "probe-seat-other"

    # The argument beats the environment.
    assert (
        resolve_seat_pack_layout("probe-seat", "probe-seat-default").layout_id
        == "probe-seat-default"
    )


def test_the_environment_assigns_per_seat(monkeypatch):
    """One process renders every seat, so a single-valued variable could not
    say which seat it meant."""
    register_seat_pack_layout(
        SeatPackLayoutV1(layout_id="probe-a", entries=[_entry()]),
        default_for_seat="probe-seat-a",
    )
    register_seat_pack_layout(
        SeatPackLayoutV1(layout_id="probe-b", entries=[_entry(priority=2)]),
        default_for_seat="probe-seat-b",
    )
    monkeypatch.setenv(
        SEAT_PACK_LAYOUT_ENV, "probe-seat-a=probe-b, probe-seat-b=probe-a"
    )
    assert resolve_seat_pack_layout("probe-seat-a").layout_id == "probe-b"
    assert resolve_seat_pack_layout("probe-seat-b").layout_id == "probe-a"


def test_a_malformed_assignment_is_a_typed_refusal_not_a_silent_default(
    monkeypatch,
):
    """A configuration that quietly did nothing is the shape the
    all-configurations law calls a gate the operator cannot turn on."""
    register_seat_pack_layout(
        SeatPackLayoutV1(layout_id="probe-malformed", entries=[_entry()]),
        default_for_seat="probe-seat-malformed",
    )
    for raw in ("probe-seat-malformed", "=probe-malformed", "probe-seat-malformed="):
        monkeypatch.setenv(SEAT_PACK_LAYOUT_ENV, raw)
        with pytest.raises(SeatSectionError) as caught:
            resolve_seat_pack_layout("probe-seat-malformed")
        assert caught.value.code == "SEAT_PACK_LAYOUT_ASSIGNMENT_MALFORMED"


def test_an_unregistered_layout_id_is_a_typed_refusal(monkeypatch):
    monkeypatch.setenv(SEAT_PACK_LAYOUT_ENV, "probe-seat-x=no-such-layout")
    with pytest.raises(SeatSectionError) as caught:
        resolve_seat_pack_layout("probe-seat-x")
    assert caught.value.code == "SEAT_PACK_LAYOUT_UNKNOWN"


def test_no_layout_or_shell_knob_reaches_config():
    """`DR-INV-render-layout`'s own check shape, owed here for the same
    measured reason: `run_manifest.py::_source_config_data` dumps every
    `Config` field into `engine_config_json`, and `qualification.py` folds
    that into every qualification subject digest."""
    from deepreason.config import Config

    bad = [
        field
        for field in Config.model_fields
        if any(
            token in field.upper()
            for token in ("SEAT_PACK", "CONJ_PACK", "SECTION_PLUGIN", "SEAT_SHELL")
        )
    ]
    assert not bad, bad
    assert SEAT_PACK_LAYOUT_ENV == "DEEPREASON_SEAT_PACK_LAYOUT"
    assert SEAT_PACK_LAYOUT_ENV not in {f.upper() for f in Config.model_fields}


def test_the_environment_variable_is_not_read_at_import_time():
    """Resolved per call, so an operator changing the variable does not need a
    restart — the property DR-INV-render-layout already relies on."""
    import inspect

    from deepreason.llm import seat_sections

    source = inspect.getsource(seat_sections.resolve_seat_pack_layout)
    assert "os.environ" in source
    module_head = inspect.getsource(seat_sections).split("def resolve_seat_pack_layout")[0]
    assert f'os.environ.get({SEAT_PACK_LAYOUT_ENV}' not in module_head
