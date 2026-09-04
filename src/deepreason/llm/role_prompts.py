"""The role-prompt wrapper as a registered, versioned artifact.

`roles.py` holds the prose that wraps a rendered brief — the standing
instruction, the JSON-only demand, and (on the compact path) the ordering of
directive, schema, aliases, example and input. Until now those were literals
in a module-level dict, so varying the wording an operator shows a model cost
a source edit. R10's "adjusted for an LLM's capabilities" is exactly that
variation, so it becomes configuration.

Three layers, as everywhere else in this seam. FROZEN: a wrapper is
PRESENTATION — it may not change what a reply must contain, which is the
contract's business, nor what the harness accepts. VERSIONED: this registry.
FREE: which template id a seat uses.

The shipped `role-prompt.legacy-v0` reproduces today's bytes exactly, and
`tests/test_role_prompt_registry.py` is the check.
"""

from __future__ import annotations

import os

from pydantic import BaseModel, ConfigDict, Field

from deepreason.llm.seat_sections import SeatSectionError

ROLE_PROMPT_TEMPLATE_ENV = "DEEPREASON_ROLE_PROMPT_TEMPLATE"
LEGACY_ROLE_PROMPT_ID = "role-prompt.legacy-v0"


class RolePromptTemplateV1(BaseModel):
    """One arrangement of the prose around a brief.

    `standard` is the whole prompt for a non-compact profile: a format string
    over `{schema}` and `{pack}`. `compact_directive` is the one-line
    instruction the compact path leads with; the rest of that path's ordering
    is machinery, not wording, and stays in `roles.py`.
    """

    model_config = ConfigDict(extra="forbid", frozen=True)

    template_id: str = Field(min_length=1, max_length=96)
    template_version: str = Field(default="1.0.0", min_length=1)
    standard: dict[str, str] = Field(default_factory=dict)
    compact_directive: dict[str, str] = Field(default_factory=dict)

    def standard_for(self, role: str) -> str:
        if role not in self.standard:
            raise SeatSectionError(
                "ROLE_PROMPT_TEMPLATE_MISSING_ROLE",
                f"{self.template_id!r} has no standard template for role "
                f"{role!r}; it covers: " + ", ".join(sorted(self.standard)),
            )
        return self.standard[role]

    def compact_directive_for(self, role: str) -> str:
        # A role with no compact directive falls back to the generic line, as
        # `COMPACT_TEMPLATES.get(role, ...)` does today. Absence here is a
        # legitimate state, not an error: not every role has been tuned for a
        # compact profile.
        return self.compact_directive.get(
            role, "Complete the one task in the input."
        )


_REGISTRY: dict[str, RolePromptTemplateV1] = {}


def register_role_prompt_template(
    template: RolePromptTemplateV1,
) -> RolePromptTemplateV1:
    """Re-registering one id with different values is refused: an id names ONE
    wording, or two runs citing it do not mean the same thing."""

    existing = _REGISTRY.get(template.template_id)
    if existing is not None and existing != template:
        raise SeatSectionError(
            "ROLE_PROMPT_TEMPLATE_CONFLICT",
            f"template id {template.template_id!r} is already registered "
            "with different values",
        )
    _REGISTRY[template.template_id] = template
    return template


def role_prompt_template_ids() -> tuple[str, ...]:
    return tuple(sorted(_REGISTRY))


def resolve_role_prompt_template(
    template_id: str | None = None,
) -> RolePromptTemplateV1:
    """Explicit argument, then the environment, then the shipped default.

    The `DR-INV-render-layout` shape, and for its measured reason: selection
    by id from an argument or the environment reaches neither `Config` nor the
    manifest, so it moves no qualification subject digest.
    """

    _ensure_seeded()
    requested = template_id or os.environ.get(ROLE_PROMPT_TEMPLATE_ENV) or ""
    requested = requested.strip() or LEGACY_ROLE_PROMPT_ID
    template = _REGISTRY.get(requested)
    if template is None:
        raise SeatSectionError(
            "ROLE_PROMPT_TEMPLATE_UNKNOWN",
            f"no role prompt template {requested!r}; registered: "
            + ", ".join(role_prompt_template_ids()),
        )
    return template


_SEEDED = False


def _ensure_seeded() -> None:
    """Build the legacy template FROM `roles.py`'s own dicts.

    Copied by reference rather than retyped, deliberately: a transcription
    could drift from the bytes every committed root was rendered under, and
    the whole value of this default is that it has not.
    """

    global _SEEDED
    if _SEEDED:
        return
    from deepreason.llm.roles import COMPACT_TEMPLATES, TEMPLATES

    register_role_prompt_template(
        RolePromptTemplateV1(
            template_id=LEGACY_ROLE_PROMPT_ID,
            standard=dict(TEMPLATES),
            compact_directive=dict(COMPACT_TEMPLATES),
        )
    )
    _SEEDED = True
