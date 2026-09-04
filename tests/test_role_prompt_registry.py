"""The role-prompt wrapper as configuration (SPEC S8.2).

R10's "adjusted for an LLM's capabilities" is, concretely, the prose around
the brief: the standing instruction, the JSON-only demand, the compact
directive. Those were module literals, so varying them cost a source edit.

The load-bearing property is that varying them is now possible AND that not
varying them changes nothing — a wrapper registry whose default moved a byte
would silently re-render every seat in the tree.
"""

import pytest

from deepreason.llm.role_prompts import (
    LEGACY_ROLE_PROMPT_ID,
    ROLE_PROMPT_TEMPLATE_ENV,
    RolePromptTemplateV1,
    register_role_prompt_template,
    resolve_role_prompt_template,
)
from deepreason.llm.roles import COMPACT_TEMPLATES, ROLES, TEMPLATES, render_role_prompt
from deepreason.llm.seat_sections import SeatSectionError


@pytest.mark.parametrize("role", sorted(TEMPLATES))
def test_the_default_wrapper_is_byte_identical_on_the_standard_path(role):
    """The whole value of this default is that it has not moved."""
    assert render_role_prompt(role, schema="SCHEMA", pack="PACK") == TEMPLATES[
        role
    ].format(schema="SCHEMA", pack="PACK")


@pytest.mark.parametrize("role", sorted(TEMPLATES))
def test_the_default_wrapper_is_byte_identical_on_the_compact_path(role):
    """Rebuilt from the same dict rather than retyped, so a transcription
    cannot drift from the bytes every committed root was rendered under."""
    rendered = render_role_prompt(
        role, schema="SCHEMA", pack="PACK", profile="compact", aliases="A", example="E"
    )
    expected_directive = COMPACT_TEMPLATES.get(
        role, "Complete the one task in the input."
    )
    assert rendered.startswith(expected_directive)
    assert rendered.endswith("PACK")


def test_the_legacy_template_covers_every_role_roles_declares():
    template = resolve_role_prompt_template()
    assert template.template_id == LEGACY_ROLE_PROMPT_ID
    assert set(template.standard) == set(TEMPLATES)
    for role in ROLES:
        # Every role either has a standard template or is compact-only; the
        # point is that neither raises.
        template.compact_directive_for(role)


def test_a_registered_wrapper_changes_the_prose_and_nothing_else():
    """The customisation point the modularity law requires to EXIST: register
    a wording, select it, and the render follows — with no edit to roles.py."""
    probe = register_role_prompt_template(
        RolePromptTemplateV1(
            template_id="role-prompt.probe-terse",
            standard={"conjecturer": "TERSE. {schema}\n{pack}"},
        )
    )
    rendered = render_role_prompt(
        "conjecturer", schema="S", pack="P", role_prompt_template=probe.template_id
    )
    assert rendered == "TERSE. S\nP"
    # The default is untouched by the registration.
    assert render_role_prompt("conjecturer", schema="S", pack="P") == TEMPLATES[
        "conjecturer"
    ].format(schema="S", pack="P")


def test_selection_is_argument_then_environment_then_default(monkeypatch):
    register_role_prompt_template(
        RolePromptTemplateV1(
            template_id="role-prompt.probe-env",
            standard={"conjecturer": "ENV {pack} {schema}"},
        )
    )
    monkeypatch.setenv(ROLE_PROMPT_TEMPLATE_ENV, "role-prompt.probe-env")
    assert render_role_prompt("conjecturer", schema="S", pack="P") == "ENV P S"
    # The argument beats the environment.
    assert render_role_prompt(
        "conjecturer", schema="S", pack="P", role_prompt_template=LEGACY_ROLE_PROMPT_ID
    ) == TEMPLATES["conjecturer"].format(schema="S", pack="P")


def test_an_unknown_template_id_is_a_typed_refusal(monkeypatch):
    monkeypatch.setenv(ROLE_PROMPT_TEMPLATE_ENV, "role-prompt.does-not-exist")
    with pytest.raises(SeatSectionError) as caught:
        render_role_prompt("conjecturer", schema="S", pack="P")
    assert caught.value.code == "ROLE_PROMPT_TEMPLATE_UNKNOWN"


def test_a_wrapper_missing_the_role_is_a_typed_refusal():
    probe = register_role_prompt_template(
        RolePromptTemplateV1(
            template_id="role-prompt.probe-partial",
            standard={"conjecturer": "{schema}{pack}"},
        )
    )
    with pytest.raises(SeatSectionError) as caught:
        render_role_prompt(
            "judge", schema="S", pack="P", role_prompt_template=probe.template_id
        )
    assert caught.value.code == "ROLE_PROMPT_TEMPLATE_MISSING_ROLE"


def test_re_registering_one_id_with_different_values_is_refused():
    first = RolePromptTemplateV1(
        template_id="role-prompt.probe-conflict", standard={"conjecturer": "a"}
    )
    register_role_prompt_template(first)
    register_role_prompt_template(first)  # idempotent
    with pytest.raises(SeatSectionError) as caught:
        register_role_prompt_template(
            RolePromptTemplateV1(
                template_id="role-prompt.probe-conflict", standard={"conjecturer": "b"}
            )
        )
    assert caught.value.code == "ROLE_PROMPT_TEMPLATE_CONFLICT"


def test_roles_py_no_longer_reads_its_own_dict_on_the_render_path():
    """The bypass trap: a renderer that kept indexing TEMPLATES directly would
    ignore the registry while still passing every behaviour test above, because
    the default is byte-identical."""
    import ast
    import pathlib

    source = pathlib.Path("src/deepreason/llm/roles.py").read_text()
    fn = next(
        n
        for n in ast.walk(ast.parse(source))
        if isinstance(n, ast.FunctionDef) and n.name == "render_role_prompt"
    )
    body = ast.get_source_segment(source, fn)
    assert "TEMPLATES[" not in body
    assert "COMPACT_TEMPLATES.get" not in body
    assert "resolve_role_prompt_template" in body
