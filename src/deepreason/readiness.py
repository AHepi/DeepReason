"""Stable, secret-free readiness projection for the public V6 facade."""

from __future__ import annotations

import os
from importlib.metadata import PackageNotFoundError, version
from pathlib import Path
from typing import Literal, Mapping

from pydantic import BaseModel, ConfigDict, Field

from deepreason.preparation import qualification_subject_manifest
from deepreason.provider_profile import (
    PROFILE_ENV,
    ProviderProfileError,
    credential_present,
    provider_state_dir,
    resolve_provider_profile,
)
from deepreason.qualification import (
    QualificationError,
    SHALLOW_NEXT_ACTION,
    load_completed_qualification,
    load_qualification_tier,
    qualification_subject_digest,
)


class ReadinessV1(BaseModel):
    """One deterministic answer to whether a public question may start."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    schema_: Literal["deepreason-readiness.v1"] = Field(
        "deepreason-readiness.v1", alias="schema"
    )
    package_version: str
    product_mode: Literal["v6-only"] = "v6-only"
    ready: bool
    profile_source: Literal["explicit", "environment", "setup"] | None
    route_identity: dict[str, str | None] | None
    credential_present: bool
    qualification_state: Literal[
        "profile_missing",
        "profile_invalid",
        "credential_missing",
        "unqualified",
        "ready_shallow",
        "ready",
    ]
    next_action: str


class SeatReadinessV1(BaseModel):
    """One seat group's own readiness: whether ITS bound profile is
    provably capable, independent of any other seat or the run's
    combination-subject qualification (S3, docs/proposals/
    ROLE_SEAT_SEPARATION_PLAN.md)."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    schema_: Literal["deepreason-seat-readiness.v1"] = Field(
        "deepreason-seat-readiness.v1", alias="schema"
    )
    group: str
    package_version: str
    ready: bool
    profile_source: Literal["explicit", "environment", "setup"] | None
    route_identity: dict[str, str | None] | None
    credential_present: bool
    qualification_state: Literal[
        "profile_missing",
        "profile_invalid",
        "credential_missing",
        "unqualified",
        "ready_shallow",
        "ready",
    ]
    next_action: str


def package_version() -> str:
    try:
        return version("deepreason")
    except PackageNotFoundError:
        # Source-tree operation remains truthful about the project version while
        # clean-wheel qualification later proves installed metadata end to end.
        return "0.1.0"


def _readiness_fields(
    explicit_profile_path: Path | str | None,
    *,
    environ: Mapping[str, str] | None,
    home: Path | str | None,
    qualification_cache_dir: Path | str | None,
) -> dict:
    """Inspect profile, credential, and completed cache without provider
    work; shared by `get_readiness` (the default profile) and
    `get_seat_readiness` (each bound seat's own profile) -- one profile,
    uniformly, per call."""

    try:
        resolved = resolve_provider_profile(
            explicit_profile_path, environ=environ, home=home
        )
    except ProviderProfileError as error:
        environment = os.environ if environ is None else environ
        if explicit_profile_path is not None:
            selected_source = "explicit"
        elif PROFILE_ENV in environment:
            selected_source = "environment"
        else:
            selected_source = "setup"
        state = (
            "profile_missing"
            if error.code == "PROVIDER_PROFILE_MISSING"
            else "profile_invalid"
        )
        return {
            "ready": False,
            "profile_source": selected_source,
            "route_identity": None,
            "credential_present": False,
            "qualification_state": state,
            "next_action": "deepreason setup",
        }

    profile = resolved.profile
    route = {
        "provider": profile.provider,
        "model_id": profile.model_id,
        "model_revision": profile.model_revision,
        "route_id": profile.endpoint_id,
    }
    present = credential_present(profile, environ=environ)
    if not present:
        return {
            "ready": False,
            "profile_source": resolved.source,
            "route_identity": route,
            "credential_present": False,
            "qualification_state": "credential_missing",
            "next_action": "deepreason setup",
        }

    manifest = qualification_subject_manifest(profile)
    subject = qualification_subject_digest(manifest, profile)
    state_dir = provider_state_dir(home=home, environ=environ)
    cache_dir = (
        Path(qualification_cache_dir)
        if qualification_cache_dir is not None
        else state_dir / "qualification-cache"
    )
    try:
        load_completed_qualification(cache_dir, subject)
    except QualificationError:
        # No usable full-tier evidence.  A durable shallow-tier record makes
        # the projection truthful: the reduced engine is ready even though a
        # full V6 inquiry may not start.
        tier = None
        try:
            tier = load_qualification_tier(cache_dir, subject).tier
        except QualificationError:
            tier = None
        if tier == "shallow":
            return {
                "ready": False,
                "profile_source": resolved.source,
                "route_identity": route,
                "credential_present": True,
                "qualification_state": "ready_shallow",
                "next_action": SHALLOW_NEXT_ACTION,
            }
        return {
            "ready": False,
            "profile_source": resolved.source,
            "route_identity": route,
            "credential_present": True,
            "qualification_state": "unqualified",
            "next_action": "deepreason qualify",
        }
    return {
        "ready": True,
        "profile_source": resolved.source,
        "route_identity": route,
        "credential_present": True,
        "qualification_state": "ready",
        "next_action": 'deepreason reason "YOUR QUESTION"',
    }


def get_readiness(
    explicit_profile_path: Path | str | None = None,
    *,
    environ: Mapping[str, str] | None = None,
    home: Path | str | None = None,
    qualification_cache_dir: Path | str | None = None,
) -> ReadinessV1:
    """Inspect profile, credential, and completed cache without provider work."""

    fields = _readiness_fields(
        explicit_profile_path,
        environ=environ,
        home=home,
        qualification_cache_dir=qualification_cache_dir,
    )
    return ReadinessV1(package_version=package_version(), **fields)


def get_seat_readiness(
    *,
    environ: Mapping[str, str] | None = None,
    home: Path | str | None = None,
    qualification_cache_dir: Path | str | None = None,
) -> tuple["SeatReadinessV1", ...]:
    """One `SeatReadinessV1` per bound seat group's OWN profile (S3):
    "is THIS seat's own profile provably capable," independent of any
    other seat or the run's combination-subject qualification. No
    bindings -> `()`; `ReadinessV1`/`get_readiness` are untouched."""

    from deepreason.seat_bindings import load_seat_bindings, seat_bindings_path

    raw = load_seat_bindings(seat_bindings_path(home=home, environ=environ))
    if not raw:
        return ()
    entries = []
    for group in sorted(raw):
        fields = _readiness_fields(
            raw[group],
            environ=environ,
            home=home,
            qualification_cache_dir=qualification_cache_dir,
        )
        entries.append(
            SeatReadinessV1(group=group, package_version=package_version(), **fields)
        )
    return tuple(entries)


def readiness_json(readiness: ReadinessV1) -> str:
    return readiness.model_dump_json(by_alias=True, exclude_none=False)


def readiness_text(readiness: ReadinessV1) -> str:
    route = readiness.route_identity or {}
    lines = [
        f"DeepReason {readiness.package_version}",
        "Product mode: V6-only",
        f"Profile source: {readiness.profile_source or 'none'}",
        "Route: "
        + (
            f"{route.get('provider')}/{route.get('model_id')}"
            if route
            else "none"
        ),
        f"Credential present: {str(readiness.credential_present).lower()}",
        f"Qualification: {readiness.qualification_state}",
        f"Next action: {readiness.next_action}",
    ]
    return "\n".join(lines)


__all__ = [
    "ReadinessV1",
    "SeatReadinessV1",
    "get_readiness",
    "get_seat_readiness",
    "package_version",
    "readiness_json",
    "readiness_text",
]
