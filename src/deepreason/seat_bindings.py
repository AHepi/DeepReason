"""Role-group -> named-profile binding, resolved before any Config exists.

A seat binding names an EXISTING provider profile file per role group
(``deepreason setup --seat conjecture=<path>``); it never mints a new
profile. Resolution happens entirely at this layer, before
``preparation._config_for_profile`` builds ``Config.roles`` — no new
``Config``/``RunManifest`` field carries "which named profile" (Rung S2's
approved Option A, sub-choice 2a; see ``docs/proposals/
ROLE_SEAT_SEPARATION_PLAN.md`` and ``docs/map/CON-seats.md``).
"""

from __future__ import annotations

import os
from collections.abc import Mapping
from pathlib import Path

import yaml

import re

from deepreason.provider_profile import (
    ProviderProfileV1,
    provider_state_dir,
    resolve_provider_profile,
)

SEAT_BINDINGS_FILENAME = "seat-bindings.yaml"
# Part E (S2d/R5, Amendment 11/R27, 2026-08-10): a SEPARATE, school-keyed
# binding file -- conjecture-side school seats are not a GROUP_ROLES
# concept (they carry no role set, they name a manifest-level
# SchoolRoleBindingV1, not a Config.roles override), so this deliberately
# does NOT extend GROUP_ROLES or reuse parse_seat_flags's group
# vocabulary; it reuses only the generic YAML {key: path} round-trip
# (load_seat_bindings/write_seat_bindings) that file format already is.
SCHOOL_SEAT_BINDINGS_FILENAME = "school-seat-bindings.yaml"
# Step 44b (S2d/R27, Amendment 11, 2026-08-10, SPEC.md addendum S18): the
# criticism-side counterpart, in ITS OWN file -- the two levers are fully
# independent (a school may have a distinct conjecture-side route, a
# distinct criticism-side route, both, or neither), so persisting them
# together would let one flag's presence silently imply the other.
CRITICISM_SEAT_BINDINGS_FILENAME = "criticism-seat-bindings.yaml"
_SCHOOL_ID_PATTERN = re.compile(r"^school-(0|[1-9][0-9]*)$")

# Role-group -> endpoint-bearing role names it controls. "coder" is only
# `property_designer`: `rules/experiment.py`'s generator-authoring call
# (role="conjecturer", template_role="experimenter") selects its lease by
# `role`, never `template_role`, so it rides whatever "conjecture" resolves
# to regardless of any "coder" binding (measured, not an oversight — see
# CENSUS.md M20 and this tranche's SPEC.md Assumption A4).
GROUP_ROLES: dict[str, frozenset[str]] = {
    "conjecture": frozenset({"conjecturer", "variator"}),
    "coder": frozenset({"property_designer", "encoder"}),
    "scratch": frozenset({"conjecturer", "synthesizer", "summarizer"}),
}

# "simulation" is a true alias of "conjecture" (operator-approved Q1
# reading): capability-channel proposals are typed conjecturer output
# (CENSUS.md M18/M19), and no separate capability-authoring role exists.
GROUP_ALIASES: dict[str, str] = {"simulation": "conjecture"}


class SeatBindingError(ValueError):
    """Stable, typed seat-binding failure."""

    def __init__(self, code: str, message: str) -> None:
        self.code = code
        super().__init__(f"{code}: {message}")


def _known_groups() -> frozenset[str]:
    return frozenset(GROUP_ROLES) | frozenset(GROUP_ALIASES)


def seat_bindings_path(
    *,
    home: str | None = None,
    environ: Mapping[str, str] | None = None,
) -> Path:
    return provider_state_dir(home=home, environ=environ) / SEAT_BINDINGS_FILENAME


def parse_seat_flags(values: list[str] | None) -> dict[str, str]:
    """Parse repeated ``GROUP=PATH`` flags into ``{group: path}``.

    ``None``/``[]`` (no ``--seat`` given) returns ``{}`` — the default,
    no-bindings case existing configs must reproduce byte-identically.
    """

    if not values:
        return {}
    bindings: dict[str, str] = {}
    for raw in values:
        group, separator, path = raw.partition("=")
        group = group.strip()
        path = path.strip()
        if not separator or not group or not path:
            raise SeatBindingError(
                "SEAT_BINDING_FLAG_MALFORMED",
                f"--seat value {raw!r} must be GROUP=PATH",
            )
        if group not in _known_groups():
            raise SeatBindingError(
                "SEAT_BINDING_GROUP_UNKNOWN",
                f"--seat group {group!r} is not one of "
                f"{sorted(_known_groups())}",
            )
        if group in bindings:
            raise SeatBindingError(
                "SEAT_BINDING_GROUP_DUPLICATED",
                f"--seat group {group!r} was given more than once",
            )
        bindings[group] = path
    return bindings


def write_seat_bindings(bindings: Mapping[str, str], target) -> Path:
    """Write ``{group: path}`` atomically; the file carries no secret."""

    path = Path(target)
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = yaml.safe_dump(dict(bindings), sort_keys=True).encode("utf-8")
    temporary = path.with_name(f".{path.name}.tmp.{os.getpid()}")
    try:
        with open(temporary, "wb") as stream:
            stream.write(payload)
        os.replace(temporary, path)
    finally:
        if temporary.exists():
            temporary.unlink()
    return path


def load_seat_bindings(path) -> dict[str, str]:
    """Read ``{group: path}``; a missing file means no bindings (R3)."""

    location = Path(path)
    if not location.is_file():
        return {}
    decoded = yaml.safe_load(location.read_text(encoding="utf-8")) or {}
    if not isinstance(decoded, dict):
        raise SeatBindingError(
            "SEAT_BINDING_FILE_MALFORMED",
            "seat-bindings file must decode to a group->path mapping",
        )
    return {str(k): str(v) for k, v in decoded.items()}


def resolve_seat_bindings_by_group(
    *,
    home: str | None = None,
    environ: Mapping[str, str] | None = None,
) -> dict[str, ProviderProfileV1]:
    """Return ``{group: ProviderProfileV1}`` for every explicitly bound
    group, keyed by the literal group name an operator used at ``--seat``
    time -- not expanded through role sets and not canonicalized through
    ``GROUP_ALIASES``. A group-keyed view has no role-level ambiguity to
    detect (unlike ``resolve_seat_bindings``, whose role-keyed view must
    canonicalize "simulation" onto "conjecture" to catch a genuine
    conflict), so this needs no conflict-detection pass of its own.
    """

    raw = load_seat_bindings(seat_bindings_path(home=home, environ=environ))
    return {
        group: resolve_provider_profile(raw[group], environ=environ, home=home).profile
        for group in sorted(raw)
    }


def resolve_seat_bindings(
    *,
    home: str | None = None,
    environ: Mapping[str, str] | None = None,
) -> dict[str, ProviderProfileV1]:
    """Return ``{role_name: ProviderProfileV1}`` for every explicitly bound
    role, expanding group aliases and role sets. Refuses typed when two
    bound groups claim the same role with different resolved profiles —
    "never last-one-wins" applies to any such overlap, not only the
    operator-named simulation/conjecture pair (this module's scratch/
    conjecture overlap, both claiming "conjecturer", is the identical
    failure shape).
    """

    by_group = resolve_seat_bindings_by_group(home=home, environ=environ)
    if not by_group:
        return {}
    role_profile: dict[str, ProviderProfileV1] = {}
    role_group: dict[str, str] = {}
    for group in sorted(by_group):
        canonical = GROUP_ALIASES.get(group, group)
        profile = by_group[group]
        for role in sorted(GROUP_ROLES[canonical]):
            if role in role_profile:
                if role_profile[role].profile_digest != profile.profile_digest:
                    raise SeatBindingError(
                        "SEAT_BINDING_ROLE_CONFLICT",
                        f"role {role!r} is bound to different profiles by "
                        f"{role_group[role]!r} and {group!r}",
                    )
                continue
            role_profile[role] = profile
            role_group[role] = group
    return role_profile


def school_seat_bindings_path(
    *,
    home: str | None = None,
    environ: Mapping[str, str] | None = None,
) -> Path:
    return provider_state_dir(home=home, environ=environ) / SCHOOL_SEAT_BINDINGS_FILENAME


def parse_school_seat_flags(values: list[str] | None) -> dict[str, str]:
    """Parse repeated ``school-N=PATH`` flags into ``{school_id: path}``.

    ``None``/``[]`` (no ``--school-seat`` given) returns ``{}`` — the
    default, no-bindings case existing configs must reproduce byte-
    identically. Validates the school-id shape against the same pattern
    ``SchoolRoleBindingV1`` itself enforces (``run_manifest.py``), so a
    malformed id is refused here rather than surfacing later as an
    opaque manifest-validation error.
    """

    if not values:
        return {}
    bindings: dict[str, str] = {}
    for raw in values:
        school_id, separator, path = raw.partition("=")
        school_id = school_id.strip()
        path = path.strip()
        if not separator or not school_id or not path:
            raise SeatBindingError(
                "SCHOOL_SEAT_FLAG_MALFORMED",
                f"--school-seat value {raw!r} must be school-N=PATH",
            )
        if not _SCHOOL_ID_PATTERN.match(school_id):
            raise SeatBindingError(
                "SCHOOL_SEAT_ID_MALFORMED",
                f"--school-seat id {school_id!r} must match school-N (N >= 0)",
            )
        if school_id in bindings:
            raise SeatBindingError(
                "SCHOOL_SEAT_DUPLICATED",
                f"--school-seat {school_id!r} was given more than once",
            )
        bindings[school_id] = path
    return bindings


def resolve_school_seats(
    *,
    home: str | None = None,
    environ: Mapping[str, str] | None = None,
) -> dict[str, ProviderProfileV1]:
    """Return ``{school_id: ProviderProfileV1}`` for every persisted
    conjecture-side school seat (Part E, S2d/R5) -- the carrier
    ``preparation.build_preparation_manifest``'s ``school_seats``
    parameter consumes. No file means no bindings, same shape as
    ``resolve_seat_bindings_by_group``."""

    raw = load_seat_bindings(school_seat_bindings_path(home=home, environ=environ))
    return {
        school_id: resolve_provider_profile(path, environ=environ, home=home).profile
        for school_id, path in sorted(raw.items())
    }


def criticism_seat_bindings_path(
    *,
    home: str | None = None,
    environ: Mapping[str, str] | None = None,
) -> Path:
    return provider_state_dir(home=home, environ=environ) / CRITICISM_SEAT_BINDINGS_FILENAME


def resolve_criticism_seats(
    *,
    home: str | None = None,
    environ: Mapping[str, str] | None = None,
) -> dict[str, ProviderProfileV1]:
    """Return ``{school_id: ProviderProfileV1}`` for every persisted
    criticism-side school seat (Step 44b, S2d/R27) -- the carrier
    ``preparation.build_preparation_manifest``'s ``criticism_seats``
    parameter consumes. No file means no bindings, same shape as
    ``resolve_school_seats``. Values are parsed by the same
    ``parse_school_seat_flags`` the conjecture-side ``--school-seat`` flag
    uses -- the ``school-N=PATH`` shape and validation are identical for
    both levers, only the persisted file and the flag name differ."""

    raw = load_seat_bindings(criticism_seat_bindings_path(home=home, environ=environ))
    return {
        school_id: resolve_provider_profile(path, environ=environ, home=home).profile
        for school_id, path in sorted(raw.items())
    }
