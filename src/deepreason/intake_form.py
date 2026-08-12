"""IntakeFormV1: a schema-validatable run-application form.

Replaces the previously hand-maintained, prose-only FORM_DR1_RUN_APPLICATION.md
as the DEFAULT way to describe a run before it starts, for every caller (a
human filling the file by hand, a small model, or a large one) — per the
operator's 2026-08-11 decision ("default for everyone"). The file this model
validates is a bounded artifact a caller can write, check, and fix without any
dialog state; `model_json_schema()` gives the same shape a JSON-Schema-aware
tool or a human editor can already consult, following the same pattern
RunManifest and Config already use elsewhere in this codebase.

Standalone by design (SPEC.md A3): this model never touches `RunManifest`'s
own schema or validators, and validating an `IntakeFormV1` instance never
mints or alters anything — it only checks whether a caller's stated intent
would be well-formed BEFORE any provider call is made.

Scope boundary (SPEC.md Addendum 2): only conditions checkable from the file
ALONE are enforced here. Conditions that need external state — whether this
exact question+config already has a run root (D1a), or what qualification
tier a provider concluded at (D4) — are not modeled; a standalone file
validator has no access to that state and should not pretend to.
"""

from __future__ import annotations

import re

from pydantic import BaseModel, ConfigDict, Field, ValidationError, field_validator

from deepreason.preparation import PUBLIC_MAX_CYCLES

INTAKE_SEAT_CONFLICT = "INTAKE_SEAT_CONFLICT"
INTAKE_CYCLES_CEILING_EXCEEDED = "INTAKE_CYCLES_CEILING_EXCEEDED"

# Part A — filed once via `deepreason setup`, host-owned. The MCP facade's own
# design boundary (mcp_server.py's module docstring, enforced by
# tests/test_public_v6_facade.py::
# test_mcp_schemas_expose_no_path_manifest_provider_or_credential_authority)
# is that an endpoint model NEVER receives provider/credential authority
# through any MCP tool schema — so `validate_intake`'s MCP-exposed schema
# must exclude these fields entirely, even though `IntakeFormV1` itself
# models them for the CLI/human path. One list, used by both the MCP schema
# filter (mcp_server.py) and the FORM_DR1 generator (tools/render_form_dr1.py)
# so "which fields are host-owned" has one answer, not two independently
# maintained ones.
HOST_OWNED_FIELDS = frozenset(
    {
        "provider",
        "endpoint",
        "model",
        "model_revision",
        "family",
        "context_window_tokens",
        "maximum_completion_tokens",
        "reasoning",
        "credential_env",
    }
)


class IntakeFormV1(BaseModel):
    """A run application, validatable offline before any token is spent.

    Parts follow FORM_DR1_RUN_APPLICATION.md's own lettering. Part A is
    optional here (filed once via `deepreason setup`, not necessarily
    repeated in every intake file); Part B1 and Part D's own fields are
    the ones this file actually applies per-run.
    """

    model_config = ConfigDict(extra="forbid")

    # Part A — the applicant's provider (optional: usually set once via
    # `deepreason setup`, not repeated per intake file).
    provider: str | None = Field(
        default=None, description="A1: the provider name, e.g. 'ollama'."
    )
    endpoint: str | None = Field(default=None, description="A2: the provider endpoint (https).")
    model: str | None = Field(default=None, description="A3: the exact model id.")
    model_revision: str | None = Field(default=None, description="A4: the model revision.")
    family: str | None = Field(
        default=None,
        description="A5: model family — governs Part F judge eligibility.",
    )
    context_window_tokens: int | None = Field(
        default=None, description="A6: the context window, in tokens.", gt=0
    )
    maximum_completion_tokens: int | None = Field(
        default=None,
        description=(
            "A7: completion ceiling. Reasoning-class models may burn this "
            "entirely on hidden thought; raise it rather than treating a "
            "typed seat failure as a defect report."
        ),
        gt=0,
    )
    credential_env: str | None = Field(
        default=None, description="A9: env var name holding the credential; keys never stored."
    )
    reasoning: str | None = Field(default=None, description="A8: the reasoning mode.")

    # Part B1 — seat assignments (all optional; blank = one model fills
    # every role, the protected solo configuration).
    seats: dict[str, str] | None = Field(
        default=None,
        description=(
            "B1: role-group seats, GROUP -> PROFILE. Groups: conjecture "
            "(conjecturer+variator), coder, scratch, simulation (alias of "
            "conjecture)."
        ),
    )

    # Part D — the question.
    question: str = Field(description="D1: the question text; part of run identity.")
    cycles: int | None = Field(default=None, description="D2: cycle budget.", gt=0)
    token_budget: int | None = Field(default=None, description="D3: token budget.", gt=0)
    shallow: bool = Field(
        default=False, description="D4: run the MiniReason reduced engine."
    )
    dossier: str | None = Field(
        default=None, description="D5: a stored admission dossier sha256."
    )
    attach: list[str] | None = Field(
        default=None, description="D5: files/directories to admit as evidence."
    )
    allow_partial: bool = Field(
        default=False, description="D5: admit bounded prefixes of oversized attachments."
    )

    @field_validator("seats")
    @classmethod
    def _no_conflicting_role_bindings(cls, seats: dict[str, str] | None) -> dict[str, str] | None:
        """B1a: groups sharing a role used to refuse a conflicting profile
        pair; all-configs-allowed (2026-08-12) makes this advisory instead —
        `seats` has no consumer that resolves a canonical winner today (grep
        confirmed no caller reads a "resolved" projection of this field), so
        there is nothing to resolve INTO; the form is returned exactly as
        given, and a caller wanting the resolution rule itself (a direct
        group beats an alias, then alphabetically-later-group-wins) applies
        it the same way `seat_bindings.resolve_seat_bindings` does once these
        seats are actually wired to a run."""

        return seats

    @field_validator("cycles")
    @classmethod
    def _cycles_within_ceiling(cls, cycles: int | None) -> int | None:
        """D2: cycles <= the V6 ceiling."""

        if cycles is not None and cycles > PUBLIC_MAX_CYCLES:
            raise ValueError(
                f"{INTAKE_CYCLES_CEILING_EXCEEDED}: cycles={cycles} exceeds the "
                f"V6 ceiling of {PUBLIC_MAX_CYCLES}"
            )
        return cycles


def mcp_safe_schema() -> dict:
    """`IntakeFormV1`'s JSON Schema with every `HOST_OWNED_FIELDS` property
    removed — the shape `validate_intake`'s MCP tool actually advertises and
    enforces. The CLI's `validate-intake` command uses the full, unfiltered
    `IntakeFormV1.model_json_schema()` (a human/developer may legitimately
    describe their own provider setup in a file); the MCP surface may not.
    """

    schema = IntakeFormV1.model_json_schema()
    schema = dict(schema)
    schema["properties"] = {
        name: value
        for name, value in schema["properties"].items()
        if name not in HOST_OWNED_FIELDS
    }
    if "required" in schema:
        schema["required"] = [name for name in schema["required"] if name not in HOST_OWNED_FIELDS]
    return schema


_LEADING_CODE = re.compile(r"^([A-Z][A-Z0-9_]{2,127}):")


def render_intake_validation_errors(error: ValidationError) -> list[str]:
    """Render every violation in `error` as one human-readable line.

    The single shared rendering path for both the `validate-intake` CLI
    command and the `validate_intake` MCP tool — the same function, not two
    re-implementations, per SPEC.md's "same code path" requirement. Prefers
    an `error_catalog` entry when a violation carries one of our own
    `CODE: message` strings (B1a/D2/D3's field validators); falls back to
    Pydantic's own location/message for ordinary shape errors (a missing
    mandatory field, a wrong type).
    """

    from deepreason.error_catalog import lookup

    lines = []
    for item in error.errors():
        loc = ".".join(str(part) for part in item["loc"]) or "(form)"
        # Pydantic wraps a raised ValueError as "Value error, <original>" in
        # `msg`, but keeps the original exception itself in `ctx["error"]` —
        # use that directly so the leading CODE: prefix survives intact.
        original = item.get("ctx", {}).get("error")
        msg = str(original) if isinstance(original, ValueError) else str(item["msg"])
        matched = _LEADING_CODE.match(msg)
        if matched is not None:
            code = matched.group(1)
            entry = lookup(code)
            if entry is not None:
                lines.append(
                    f"{loc}: {entry.summary} {entry.what_it_means} Next: {entry.next_action}"
                )
                continue
        if item["type"] == "missing":
            lines.append(f"{loc}: this field is required.")
        else:
            lines.append(f"{loc}: {msg}")
    return lines
