"""Pure pre-bind checks for autonomous inquiry capability topology.

This module deliberately performs no filesystem writes, route discovery, or
provider calls. A caller must establish that the selected manifest can express
every required autonomous capability before binding a run root.
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict


AutonomousCapabilityName = Literal[
    "attached_evidence", "simulation", "formalization", "research", "code"
]


class AutonomousCapabilityRequirementsV1(BaseModel):
    """Capabilities an inquiry requires rather than merely permits."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    attached_evidence: bool = False
    simulation: bool = False
    formalization: bool = False
    research: bool = False
    code: bool = False

    @property
    def required(self) -> tuple[AutonomousCapabilityName, ...]:
        return tuple(
            name
            for name in (
                "attached_evidence",
                "simulation",
                "formalization",
                "research",
                "code",
            )
            if getattr(self, name)
        )


class AutonomousCapabilityTopologyUnavailable(RuntimeError):
    """Stable preflight refusal raised before a run root may be created."""

    code = "AUTONOMOUS_CAPABILITY_TOPOLOGY_UNAVAILABLE"

    def __init__(self, missing: tuple[AutonomousCapabilityName, ...]) -> None:
        self.missing = missing
        detail = ", ".join(missing) if missing else "unknown"
        super().__init__(f"{self.code}: missing autonomous capability path(s): {detail}")


def manifest_autonomous_capabilities(manifest) -> dict[AutonomousCapabilityName, bool]:
    """Return only capabilities reachable without an operator fallback."""

    topology = getattr(manifest, "inquiry_capability_policy", None)
    simulation_policy = getattr(topology, "simulation", None)
    evidence_policy = getattr(topology, "attached_evidence", None)
    formalization_policy = getattr(topology, "formalization", None)
    research_policy = getattr(topology, "research", None)
    return {
        "attached_evidence": bool(
            getattr(manifest, "schema_version", 0) == 5
            and evidence_policy is not None
            and evidence_policy.enabled
        ),
        "simulation": bool(
            getattr(manifest, "schema_version", 0) == 5
            and simulation_policy is not None
            and simulation_policy.enabled
        ),
        "formalization": bool(
            getattr(manifest, "schema_version", 0) == 5
            and formalization_policy is not None
            and formalization_policy.enabled
        ),
        "research": bool(
            getattr(manifest, "schema_version", 0) == 5
            and research_policy is not None
            and research_policy.enabled
        ),
        "code": False,
    }


def preflight_autonomous_capabilities(
    manifest,
    requirements: AutonomousCapabilityRequirementsV1,
) -> None:
    """Fail closed without touching a run root when topology is incomplete."""

    requirements = AutonomousCapabilityRequirementsV1.model_validate(requirements)
    available = manifest_autonomous_capabilities(manifest)
    missing = tuple(name for name in requirements.required if not available[name])
    if missing:
        raise AutonomousCapabilityTopologyUnavailable(missing)


__all__ = [
    "AutonomousCapabilityRequirementsV1",
    "AutonomousCapabilityTopologyUnavailable",
    "manifest_autonomous_capabilities",
    "preflight_autonomous_capabilities",
]
