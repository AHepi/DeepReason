"""The template layer, refusals first (SPEC S4).

An operator's plugin directory is TRUSTED and a `.py` plugin in it executes.
That trust is exactly why the TEMPLATE kind must be unable to execute at all:
an operator who wants code writes a plugin, and one who only wants a different
FORMAT writes a text file that provably cannot run anything.

The refusal cases come first because the grammar is a WHITELIST. A blacklist
would have to anticipate every escape; a whitelist has to anticipate none, and
these tests are what proves the whitelist is actually closed.
"""

import pytest

from deepreason.llm.seat_sections import SeatSectionError
from deepreason.llm.seat_templates import render_template


@pytest.mark.parametrize(
    "source,label",
    [
        ("{{ 1 + 1 }}", "arithmetic"),
        ("{{ name.upper() }}", "a call"),
        ("{{ name | upper }}", "a filter"),
        ("{{ __import__('os') }}", "an import"),
        ("{{ name.__class__.__mro__ }}", "traversal to the interpreter"),
        ("{{ a.b.c }}", "two-dot traversal"),
        ("{{ items[0] }}", "indexing"),
        ("{{ a == b }}", "a comparison"),
        ("{{ a if b else c }}", "a conditional expression"),
        ("{% if name %}x{% endif %}", "a construct that does not exist"),
        ("{% import os %}", "an import tag"),
        ("{% for x in items.values() %}{{ x }}{% endfor %}", "a call in a loop"),
        ("{{ name.__dict__ }}", "a dunder attribute"),
        ("{{ name._private }}", "a private attribute"),
    ],
)
def test_refuses_everything_that_is_not_substitution_or_iteration(source, label):
    with pytest.raises(SeatSectionError) as caught:
        render_template(source, {"name": "n", "a": {"b": {"c": 1}}, "items": [1], "b": 1, "c": 1})
    assert caught.value.code in {
        "SEAT_TEMPLATE_NOT_EXPRESSIBLE",
        "SEAT_TEMPLATE_UNKNOWN_NAME",
        "SEAT_TEMPLATE_NOT_ITERABLE",
    }, (label, caught.value.code)


def test_a_callable_attribute_is_refused_rather_than_rendered():
    """Not merely uncalled — refused. Rendering `<bound method ...>` into a
    prompt would be a silent leak of interpreter internals."""

    class _Holder:
        def method(self):
            return "x"

    with pytest.raises(SeatSectionError) as caught:
        render_template("{{ h.method }}", {"h": _Holder()})
    assert caught.value.code == "SEAT_TEMPLATE_NOT_EXPRESSIBLE"


@pytest.mark.parametrize("source", ["{{ name", "{% for x in xs %}", "a {{ b"])
def test_an_unclosed_delimiter_is_refused_not_shipped_as_text(source):
    """A best-effort renderer would ship `{{ name` to a model as literal text.
    A template that did not do what it says is the failure this layer exists
    to prevent."""
    with pytest.raises(SeatSectionError) as caught:
        render_template(source, {"name": "n", "xs": []})
    assert caught.value.code == "SEAT_TEMPLATE_UNCLOSED"


def test_an_unknown_name_is_refused_and_says_what_was_available():
    with pytest.raises(SeatSectionError) as caught:
        render_template("{{ missing }}", {"present": 1})
    assert caught.value.code == "SEAT_TEMPLATE_UNKNOWN_NAME"
    assert "present" in str(caught.value)


# --------------------------------------------------------------- the positive
# The refusals above would be satisfied by a renderer that refused everything,
# so the two constructs that DO exist are pinned too.


def test_substitution_and_one_dot_traversal():
    assert render_template("Hi {{ name }}", {"name": "there"}) == "Hi there"
    assert render_template("{{ item.id }}", {"item": {"id": "A1"}}) == "A1"


def test_iteration_over_a_declared_sequence():
    out = render_template(
        "{% for block in blocks %}- {{ block.id }}\n{% endfor %}",
        {"blocks": [{"id": "EV-001"}, {"id": "EV-002"}]},
    )
    assert out == "- EV-001\n- EV-002\n"


def test_nested_iteration():
    out = render_template(
        "{% for g in groups %}[{% for m in g.members %}{{ m }}{% endfor %}]{% endfor %}",
        {"groups": [{"members": ["a", "b"]}, {"members": ["c"]}]},
    )
    assert out == "[ab][c]"


def test_an_empty_sequence_renders_nothing_rather_than_failing():
    assert render_template("x{% for i in xs %}{{ i }}{% endfor %}y", {"xs": []}) == "xy"


def test_a_string_is_not_a_sequence_to_iterate():
    """Iterating a string would silently produce one line per character."""
    with pytest.raises(SeatSectionError) as caught:
        render_template("{% for c in s %}{{ c }}{% endfor %}", {"s": "abc"})
    assert caught.value.code == "SEAT_TEMPLATE_NOT_ITERABLE"


def test_a_template_with_no_delimiters_is_its_own_text():
    assert render_template("just prose", {}) == "just prose"


# ------------------------------------------------------- S4.3, the byte ceiling
# NO SILENT CAPS. A template that overruns its declared ceiling names itself
# and stops; a clip here would be a second budget applied underneath the
# allocator's accounting, which is the exact shape `_allocate_sections` exists
# to abolish.


def _probe_layout(max_render_bytes, text, tag):
    from pydantic import BaseModel

    from deepreason.llm.seat_sections import (
        SectionRenderV1,
        SeatPackLayoutEntryV1,
        SeatPackLayoutV1,
        register_section_plugin,
    )

    class _NoParams(BaseModel):
        pass

    class _Fat:
        plugin_id = f"dr.test.template-ceiling-{tag}"
        plugin_version = "1.0.0"
        section_id = "problem"
        declared_handle_kinds = ()
        parameters_model = _NoParams

        def render(self, request, params):
            return SectionRenderV1(section_id=self.section_id, text=text)

    register_section_plugin(_Fat())
    return SeatPackLayoutV1(
        layout_id=f"seat-pack.probe.ceiling-{tag}",
        entries=(
            SeatPackLayoutEntryV1(
                plugin_id=_Fat.plugin_id,
                priority=1,
                max_render_bytes=max_render_bytes,
            ),
        ),
    )


def test_a_template_overrun_names_the_plugin_and_stops(tmp_path):
    from deepreason.llm.packs import render_conj_pack
    from deepreason.llm.seat_plugins import ensure_seeded
    from deepreason.llm.seat_sections import register_seat_pack_layout
    from tests.conj_pack_golden_cases import _seed_bare

    ensure_seeded()
    layout = register_seat_pack_layout(_probe_layout(64, "x" * 512, "overrun"))
    problem, harness = _seed_bare(tmp_path)
    with pytest.raises(SeatSectionError) as caught:
        render_conj_pack(
            problem,
            harness.state,
            harness.commitments,
            harness.blobs,
            vs_k=2,
            token_budget=4000,
            seat_pack_layout=layout.layout_id,
        )
    assert caught.value.code == "SEAT_SECTION_RENDER_OVERRUN"
    assert "dr.test.template-ceiling-overrun" in str(caught.value)
    assert "512" in str(caught.value) and "64" in str(caught.value)


def test_a_render_inside_its_ceiling_is_untouched(tmp_path):
    """The positive anchor: the refusal above would be vacuous if the ceiling
    also mangled renders that fit."""
    from deepreason.llm.packs import render_conj_pack
    from deepreason.llm.seat_plugins import ensure_seeded
    from deepreason.llm.seat_sections import register_seat_pack_layout
    from tests.conj_pack_golden_cases import _seed_bare

    ensure_seeded()
    layout = register_seat_pack_layout(_probe_layout(4096, "y" * 512, "within"))
    problem, harness = _seed_bare(tmp_path)
    pack = render_conj_pack(
        problem,
        harness.state,
        harness.commitments,
        harness.blobs,
        vs_k=2,
        token_budget=4000,
        seat_pack_layout=layout.layout_id,
    )
    assert "y" * 512 in pack
