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

from deepreason.provider_profile import (
    ProviderProfileV1,
    provider_state_dir,
    resolve_provider_profile,
)

SEAT_BINDINGS_FILENAME = "seat-bindings.yaml"

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
