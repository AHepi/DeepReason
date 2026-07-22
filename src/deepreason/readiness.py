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
    load_completed_qualification,
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
        "profile_missing", "profile_invalid", "credential_missing", "unqualified", "ready"
    ]
    next_action: str


def package_version() -> str:
    try:
        return version("deepreason")
    except PackageNotFoundError:
        # Source-tree operation remains truthful about the project version while
        # clean-wheel qualification later proves installed metadata end to end.
        return "0.1.0"


def get_readiness(
    explicit_profile_path: Path | str | None = None,
    *,
    environ: Mapping[str, str] | None = None,
    home: Path | str | None = None,
    qualification_cache_dir: Path | str | None = None,
) -> ReadinessV1:
    """Inspect profile, credential, and completed cache without provider work."""

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
        return ReadinessV1(
            package_version=package_version(),
            ready=False,
            profile_source=selected_source,
            route_identity=None,
            credential_present=False,
            qualification_state=state,
            next_action="deepreason setup",
        )

    profile = resolved.profile
    route = {
        "provider": profile.provider,
        "model_id": profile.model_id,
        "model_revision": profile.model_revision,
        "route_id": profile.endpoint_id,
    }
    present = credential_present(profile, environ=environ)
    if not present:
        return ReadinessV1(
            package_version=package_version(),
            ready=False,
            profile_source=resolved.source,
            route_identity=route,
            credential_present=False,
            qualification_state="credential_missing",
            next_action="deepreason setup",
        )

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
        return ReadinessV1(
            package_version=package_version(),
            ready=False,
            profile_source=resolved.source,
            route_identity=route,
            credential_present=True,
            qualification_state="unqualified",
            next_action="deepreason qualify",
        )
    return ReadinessV1(
        package_version=package_version(),
        ready=True,
        profile_source=resolved.source,
        route_identity=route,
        credential_present=True,
        qualification_state="ready",
        next_action='deepreason reason "YOUR QUESTION"',
    )


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
    "get_readiness",
    "package_version",
    "readiness_json",
    "readiness_text",
]
