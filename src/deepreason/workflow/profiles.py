"""Repository-owned workflow profiles compiled from immutable v4 manifests."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Literal

from pydantic import ConfigDict, Field, StrictInt, model_validator

from deepreason.frozen import FrozenRecord
from deepreason.llm.firewall import (
    EndpointLease,
    resolve_school_role_lease,
    route_fingerprint,
    select_lease,
)
from deepreason.run_manifest import (
    ConjectureContextPolicyV1,
    RunManifest,
    config_from_run_manifest,
)
from deepreason.scratch.models import RetrievalChannel
from deepreason.workflow.models import (
    CapabilityGrantV1,
    CapabilityOutcome,
    LocalRepairPolicyV1,
    RouteLeaseRefV1,
)


WorkflowProfileId = Literal["conjecture.shadow.v1", "conjecture.active.v1"]


_OWNED_PROFILE_MODES: dict[str, Literal["shadow", "active_conjecture"]] = {
    "conjecture.shadow.v1": "shadow",
    "conjecture.active.v1": "active_conjecture",
}


class WorkflowProfileError(ValueError):
    """A manifest does not name one complete repository-owned profile."""


class ConjectureWorkflowProfileV1(FrozenRecord):
    """Small executable profile; this is not a user-authored workflow DSL."""

    model_config = ConfigDict(frozen=True, extra="forbid", populate_by_name=True)

    schema_: Literal["workflow.conjecture-profile.v1"] = Field(
        "workflow.conjecture-profile.v1", alias="schema"
    )
    manifest_digest: str = Field(pattern=r"^[0-9a-f]{64}$")
    controller_version: Literal["workflow.controller.v1"] = "workflow.controller.v1"
    mode: Literal["shadow", "active_conjecture"]
    workflow_profile: WorkflowProfileId
    capability_profile: Literal["conjecture-control.v1"] = "conjecture-control.v1"
    conjecturer_contract_id: Literal["conjecturer.legacy.v1", "conjecturer.turn.v4"]
    control_event_schema: Literal["control.event.v1"] = "control.event.v1"
    model_profile: Literal["compact", "standard", "frontier"]
    workload_profile: Literal["text", "code", "formal", "website"]
    max_candidates: StrictInt = Field(gt=0, le=256)
    context_policy: ConjectureContextPolicyV1
    repair_policy: LocalRepairPolicyV1

    @property
    def shadow(self) -> bool:
        return self.mode == "shadow"

    def capability_grant(self, *, completed_context_expansions: int = 0) -> CapabilityGrantV1:
        if isinstance(completed_context_expansions, bool) or completed_context_expansions < 0:
            raise ValueError("completed context expansions must be a non-negative integer")
        remaining = max(
            0,
            self.context_policy.max_context_expansion_requests
            - completed_context_expansions,
        )
        outcomes = [CapabilityOutcome.CANDIDATE_PROPOSAL]
        if self.conjecturer_contract_id == "conjecturer.turn.v4":
            if (
                self.context_policy.mode == "harness_plus_model_request"
                and remaining
            ):
                outcomes.append(CapabilityOutcome.CONTEXT_REQUEST)
            outcomes.append(CapabilityOutcome.ABSTENTION)
        return CapabilityGrantV1.create(
            allowed_outcomes=tuple(outcomes),
            max_candidates=self.max_candidates,
            max_local_repairs=self.repair_policy.max_schema_repairs,
            remaining_context_expansions=(
                remaining if CapabilityOutcome.CONTEXT_REQUEST in outcomes else 0
            ),
            max_extra_context_blocks=(
                self.context_policy.max_extra_blocks
                if CapabilityOutcome.CONTEXT_REQUEST in outcomes
                else 0
            ),
            permitted_retrieval_channels=(
                tuple(
                    RetrievalChannel(value)
                    for value in self.context_policy.permitted_retrieval_channels
                )
                if CapabilityOutcome.CONTEXT_REQUEST in outcomes
                else ()
            ),
        )

    @model_validator(mode="after")
    def _owned_tuple(self):
        expected_mode = _OWNED_PROFILE_MODES[self.workflow_profile]
        if self.mode != expected_mode:
            raise ValueError("workflow profile and control mode differ")
        if self.mode == "shadow":
            if self.conjecturer_contract_id != "conjecturer.legacy.v1":
                raise ValueError("shadow profile must preserve the legacy conjecturer contract")
            if self.context_policy.mode != "disabled":
                raise ValueError("shadow profile must not actuate conjecture context")
        elif self.conjecturer_contract_id != "conjecturer.turn.v4":
            raise ValueError("active conjecture profile requires the v4 turn contract")
        return self


def compile_workflow_profile(manifest: RunManifest) -> ConjectureWorkflowProfileV1:
    """Compile one exact built-in profile without interpreting user workflow code."""

    manifest = RunManifest.model_validate(manifest)
    if manifest.schema_version != 4 or manifest.control_plane_policy is None:
        raise WorkflowProfileError("WORKFLOW_MANIFEST_V4_REQUIRED")
    control = manifest.control_plane_policy
    if control.controller_version != "workflow.controller.v1":
        raise WorkflowProfileError("WORKFLOW_CONTROLLER_VERSION_UNSUPPORTED")
    if control.mode not in {"shadow", "active_conjecture"}:
        raise WorkflowProfileError("WORKFLOW_MODE_UNSUPPORTED")
    try:
        expected_mode = _OWNED_PROFILE_MODES[control.workflow_profile]
    except KeyError as error:
        raise WorkflowProfileError("WORKFLOW_PROFILE_UNSUPPORTED") from error
    if control.mode != expected_mode:
        raise WorkflowProfileError("WORKFLOW_PROFILE_MODE_MISMATCH")
    if control.capability_profile != "conjecture-control.v1":
        raise WorkflowProfileError("WORKFLOW_CAPABILITY_PROFILE_UNSUPPORTED")
    if control.contract_versions.control_event_schema != "control.event.v1":
        raise WorkflowProfileError("WORKFLOW_CONTROL_EVENT_SCHEMA_UNSUPPORTED")

    config = config_from_run_manifest(manifest)
    maximum_repairs = min(2, max(0, int(config.RETRY_MAX)))
    repair_policy = LocalRepairPolicyV1.create(
        max_schema_repairs=maximum_repairs,
        scopes=("whole_object", "smallest_subtree")[:maximum_repairs],
    )
    return ConjectureWorkflowProfileV1(
        manifest_digest=manifest.sha256,
        mode=control.mode,
        workflow_profile=control.workflow_profile,
        conjecturer_contract_id=control.contract_versions.conjecturer_turn_contract,
        model_profile=manifest.model_profile,
        workload_profile=manifest.workload_profile,
        max_candidates=config.VS_K,
        context_policy=control.conjecture_context,
        repair_policy=repair_policy,
    )


def route_lease_reference(lease: EndpointLease) -> RouteLeaseRefV1:
    """Project a runtime lease into its secret-free canonical authority fields."""

    return RouteLeaseRefV1(
        role=lease.role,
        seat=lease.seat,
        endpoint_id=lease.route.endpoint_id,
        route_sha256=route_fingerprint(lease.route),
    )


def resolve_conjecture_route(
    manifest: RunManifest,
    leases: Mapping[str, tuple[EndpointLease, ...]],
    *,
    school_id: str | None,
) -> tuple[EndpointLease, RouteLeaseRefV1]:
    """Resolve the same manifest-owned route for schooled and unschooled Conj."""

    manifest = RunManifest.model_validate(manifest)
    lease = (
        resolve_school_role_lease(
            manifest,
            leases,
            school_id=school_id,
            role="conjecturer",
        )
        if school_id is not None
        else select_lease(leases, "conjecturer", 0)
    )
    if lease.route != manifest.roles["conjecturer"][lease.seat]:
        raise WorkflowProfileError("WORKFLOW_ROUTE_LEASE_MISMATCH")
    return lease, route_lease_reference(lease)


__all__ = [
    "ConjectureWorkflowProfileV1",
    "WorkflowProfileError",
    "compile_workflow_profile",
    "resolve_conjecture_route",
    "route_lease_reference",
]
