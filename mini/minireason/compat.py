"""Shared compatibility kernel for MiniReason.

MiniReason keeps its deliberately small scheduler and rule surface.  Model
presentation, wire validation, bounded repair, route freezing, canonical
bytes, and run-manifest persistence come from the parent implementation so a
mini run does not become a second protocol.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

from deepreason.canonical import canonical_json, sha256_hex
from deepreason.llm.contracts import ConjecturerOutput
from deepreason.llm.firewall import EndpointLease, RouteFirewallError, route_from_endpoint
from deepreason.llm.profiles import ModelProfile, ProfileSpec, get_profile
from deepreason.llm.wire import (
    ReferenceFreeConjecturerWireContract,
    WireContract,
    wire_contract_for,
)
from deepreason.run_manifest import (
    MANIFEST_NAME,
    RunManifest,
    load_run_manifest,
    persist_run_manifest,
)


ENGINE_PROFILE = "mini"
DEFAULT_MODEL_PROFILE = ModelProfile.COMPACT
# Mini intentionally has no embedding model.  ``None`` makes the canonical
# anti-relapse guard run its exact (slower) battery check against every
# refuted prior, as documented by that guard.  Keep this explicit so the
# reduced engine cannot drift onto a private equivalence threshold.
MINI_NEAR_DUP_EPS: float | None = None


@dataclass(frozen=True, slots=True)
class CompatibilityKernel:
    """Immutable process bindings used by the mini control loop."""

    profile: ProfileSpec
    lease: EndpointLease
    wire_contract: WireContract[ConjecturerOutput]
    manifest: RunManifest


def _new_manifest(profile: ProfileSpec, lease: EndpointLease) -> RunManifest:
    """Build MiniReason's secret-free process manifest.

    The source hash covers only the already-resolved, non-secret route and
    presentation choice.  It is reporting/replay metadata and never enters an
    artifact, commitment, warrant, status, or adjudication input.
    """

    source = {
        "engine_profile": ENGINE_PROFILE,
        "model_profile": profile.name.value,
        "roles": {
            "conjecturer": [lease.route.model_dump(mode="json")],
        },
    }
    return RunManifest(
        engine_profile=ENGINE_PROFILE,
        model_profile=profile.name.value,
        roles={"conjecturer": (lease.route,)},
        rubric_policy="forbid",
        concurrency=profile.default_concurrency,
        pack_profile=profile.name.value,
        output_profile=profile.name.value,
        source_config_hash=sha256_hex(canonical_json(source)),
        compiled_at=datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        # Full DeepReason may reconstruct its ordinary Config from this file;
        # the mini-specific engine selection remains manifest metadata.
        engine_config_json="{}",
    )


def _verify_existing(
    manifest: RunManifest,
    profile: ProfileSpec,
    lease: EndpointLease,
) -> None:
    if manifest.engine_profile != ENGINE_PROFILE:
        raise RouteFirewallError(
            "MINI_ROOT_ENGINE_MISMATCH: refusing to downgrade a non-mini run root"
        )
    if manifest.model_profile != profile.name.value:
        raise RouteFirewallError(
            "MINI_ROOT_PROFILE_MISMATCH: existing root is bound to "
            f"{manifest.model_profile!r}, requested {profile.name.value!r}"
        )
    routes = manifest.roles.get("conjecturer", ())
    if len(routes) != 1 or routes[0] != lease.route:
        raise RouteFirewallError(
            "MINI_ROOT_ROUTE_MISMATCH: existing root is bound to a different endpoint"
        )
    if manifest.rubric_policy != "forbid":
        raise RouteFirewallError(
            "MINI_ROOT_RUBRIC_POLICY_MISMATCH: MiniReason does not run rubric judging"
        )


def initialize(
    root: Path | str,
    endpoint: object,
    model_profile: str | ModelProfile | ProfileSpec = DEFAULT_MODEL_PROFILE,
) -> CompatibilityKernel:
    """Freeze MiniReason's route and compact transport before its first call."""

    profile = get_profile(model_profile)
    lease = EndpointLease(
        role="conjecturer",
        seat=0,
        route=route_from_endpoint(endpoint),
    )
    lease.verify(endpoint)
    path = Path(root) / MANIFEST_NAME
    if path.exists():
        manifest = load_run_manifest(path)
        _verify_existing(manifest, profile, lease)
    else:
        manifest = _new_manifest(profile, lease)
        persist_run_manifest(manifest, Path(root))
    # Mini does not preserve conjecturer references in its canonical candidate
    # path. Its compact schema therefore omits references entirely instead of
    # exposing raw ids or pretending an empty alias table is a usable contract.
    # Other explicitly selected profiles retain the shared selector.
    contract = (
        ReferenceFreeConjecturerWireContract()
        if profile.name == ModelProfile.COMPACT
        else wire_contract_for("conjecturer", ConjecturerOutput, profile.name)
    )
    return CompatibilityKernel(
        profile=profile,
        lease=lease,
        wire_contract=contract,
        manifest=manifest,
    )
