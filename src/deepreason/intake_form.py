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

from deepreason.preparation import PUBLIC_MAX_CYCLES, PUBLIC_MAX_TOKEN_BUDGET
from deepreason.seat_bindings import GROUP_ALIASES

INTAKE_SEAT_CONFLICT = "INTAKE_SEAT_CONFLICT"
INTAKE_CYCLES_CEILING_EXCEEDED = "INTAKE_CYCLES_CEILING_EXCEEDED"
INTAKE_TOKEN_BUDGET_CEILING_EXCEEDED = "INTAKE_TOKEN_BUDGET_CEILING_EXCEEDED"


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
        """B1a: groups sharing a role may not bind conflicting profiles."""

        if not seats:
            return seats
        role_profile: dict[str, str] = {}
        role_group: dict[str, str] = {}
        for group in sorted(seats):
            canonical = GROUP_ALIASES.get(group, group)
            profile = seats[group]
            if canonical in role_profile and role_profile[canonical] != profile:
                raise ValueError(
                    f"{INTAKE_SEAT_CONFLICT}: groups {role_group[canonical]!r} and "
                    f"{group!r} both bind role {canonical!r} to different profiles"
                )
            role_profile[canonical] = profile
            role_group[canonical] = group
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

    @field_validator("token_budget")
    @classmethod
    def _token_budget_within_ceiling(cls, token_budget: int | None) -> int | None:
        """D3: token budget <= the V6 ceiling."""

        if token_budget is not None and token_budget > PUBLIC_MAX_TOKEN_BUDGET:
            raise ValueError(
                f"{INTAKE_TOKEN_BUDGET_CEILING_EXCEEDED}: token_budget={token_budget} "
                f"exceeds the V6 ceiling of {PUBLIC_MAX_TOKEN_BUDGET}"
            )
        return token_budget


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
