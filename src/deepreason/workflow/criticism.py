"""Pure deterministic planning for manifest-bound foreign-school criticism.

The planner selects schools and batches only.  It does not inspect or
interpret criticism content, call a provider, or grant epistemic status.
"""

from __future__ import annotations

import hashlib
import json
import re
from collections import defaultdict
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from deepreason.run_manifest import Route, RunManifest
from deepreason.workflow.models import IdentifiedWorkflowRecord


class ForeignCriticismTargetV1(BaseModel):
    """One already-eligible accepted artifact and its generating school."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    target_id: str = Field(min_length=1, max_length=256)
    owner_school_id: str = Field(pattern=r"^school-(0|[1-9][0-9]*)$")
    completed_critic_school_ids: tuple[str, ...] = ()

    @field_validator("completed_critic_school_ids", mode="after")
    @classmethod
    def _canonical_completed_schools(cls, value: tuple[str, ...]) -> tuple[str, ...]:
        if value != tuple(sorted(value)) or len(value) != len(set(value)):
            raise ValueError("completed critic schools must be sorted and distinct")
        if any(re.fullmatch(r"school-(0|[1-9][0-9]*)", school) is None for school in value):
            raise ValueError("completed critic schools must use canonical school ids")
        return value

    @field_validator("completed_critic_school_ids", mode="after")
    @classmethod
    def _owner_is_not_completed(cls, value: tuple[str, ...], info) -> tuple[str, ...]:
        if info.data.get("owner_school_id") in value:
            raise ValueError("the owner school cannot be a completed foreign critic")
        return value


class ForeignCriticAssignmentV1(BaseModel):
    """One foreign school and its exact manifest-owned critic route."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    target_id: str = Field(min_length=1, max_length=256)
    owner_school_id: str = Field(pattern=r"^school-(0|[1-9][0-9]*)$")
    critic_school_id: str = Field(pattern=r"^school-(0|[1-9][0-9]*)$")
    role: Literal["argumentative_critic"]
    seat: int = Field(ge=0, le=1_023)
    endpoint_id: str = Field(min_length=1, max_length=256)
    route_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    model_identity_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")


class ForeignCriticismTargetPlanV1(BaseModel):
    """Coverage record for one target, separate from route/model diversity."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    target_id: str = Field(min_length=1, max_length=256)
    owner_school_id: str = Field(pattern=r"^school-(0|[1-9][0-9]*)$")
    completed_critic_school_ids: tuple[str, ...]
    assignments: tuple[ForeignCriticAssignmentV1, ...]
    foreign_school_coverage: int = Field(ge=1)
    distinct_route_coverage: int = Field(ge=1)
    distinct_model_coverage: int = Field(ge=1)
    route_diverse: bool

    @field_validator("assignments", mode="after")
    @classmethod
    def _canonical_assignments(
        cls, value: tuple[ForeignCriticAssignmentV1, ...]
    ) -> tuple[ForeignCriticAssignmentV1, ...]:
        keys = tuple(assignment.critic_school_id for assignment in value)
        if keys != tuple(sorted(keys)) or len(keys) != len(set(keys)):
            raise ValueError("critic assignments must use sorted distinct schools")
        return value


class ForeignCriticismBatchV1(BaseModel):
    """One bounded provider batch under one school-owned route lease."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    critic_school_id: str = Field(pattern=r"^school-(0|[1-9][0-9]*)$")
    role: Literal["argumentative_critic"]
    seat: int = Field(ge=0, le=1_023)
    endpoint_id: str = Field(min_length=1, max_length=256)
    route_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    target_ids: tuple[str, ...]

    @field_validator("target_ids", mode="after")
    @classmethod
    def _canonical_targets(cls, value: tuple[str, ...]) -> tuple[str, ...]:
        if not value or value != tuple(sorted(value)) or len(value) != len(set(value)):
            raise ValueError("batch targets must be non-empty, sorted, and distinct")
        return value


class ForeignCriticismPlanV1(BaseModel):
    """Complete deterministic plan; safe to persist as an audit record."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    targets: tuple[ForeignCriticismTargetPlanV1, ...]
    batches: tuple[ForeignCriticismBatchV1, ...]


class CriticismAssignmentV1(IdentifiedWorkflowRecord):
    """One durable coverage obligation, persisted before provider work."""

    _identity_domain = "criticism.assignment.v1"

    schema_: Literal["criticism.assignment.v1"] = Field(
        "criticism.assignment.v1", alias="schema"
    )
    manifest_digest: str = Field(pattern=r"^[0-9a-f]{64}$")
    target_id: str = Field(min_length=1, max_length=256)
    owner_school_id: str = Field(pattern=r"^school-(0|[1-9][0-9]*)$")
    critic_school_id: str = Field(pattern=r"^school-(0|[1-9][0-9]*)$")
    eligible_school_order: tuple[str, ...]
    order_index: int = Field(ge=0, le=1_023)
    role: Literal["argumentative_critic"] = "argumentative_critic"
    seat: int = Field(ge=0, le=1_023)
    endpoint_id: str = Field(min_length=1, max_length=256)
    route_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    maximum_attempts: int = Field(ge=1, le=16)

    @field_validator("eligible_school_order")
    @classmethod
    def _eligible_order_is_closed(cls, value):
        if not value or len(value) != len(set(value)):
            raise ValueError("eligible critic school order must be nonempty and unique")
        if any(re.fullmatch(r"school-(0|[1-9][0-9]*)", item) is None for item in value):
            raise ValueError("eligible critic schools must use canonical IDs")
        return tuple(value)

    @model_validator(mode="after")
    def _selected_school_is_eligible(self):
        if self.owner_school_id in self.eligible_school_order:
            raise ValueError("owner school cannot satisfy its own criticism obligation")
        if (
            self.order_index >= len(self.eligible_school_order)
            or self.eligible_school_order[self.order_index] != self.critic_school_id
        ):
            raise ValueError("criticism assignment differs from eligible-school order")
        return self


class CriticismAttemptV1(IdentifiedWorkflowRecord):
    """One completed or failed try; only completed tries reduce coverage debt."""

    _identity_domain = "criticism.attempt.v1"

    schema_: Literal["criticism.attempt.v1"] = Field(
        "criticism.attempt.v1", alias="schema"
    )
    assignment_ref: str = Field(pattern=r"^sha256:[0-9a-f]{64}$")
    target_id: str = Field(min_length=1, max_length=256)
    critic_school_id: str = Field(pattern=r"^school-(0|[1-9][0-9]*)$")
    attempt_index: int = Field(ge=0, le=15)
    outcome: Literal[
        "completed",
        "schema_failure",
        "transport_failure",
        "budget_denied",
    ]
    coverage_completed: bool = False
    source_call_seq: int | None = Field(default=None, ge=0)
    diagnostic_ref: str | None = Field(default=None, max_length=512)

    @model_validator(mode="after")
    def _attempt_shape(self):
        if self.outcome == "completed":
            if not self.coverage_completed or self.source_call_seq is None:
                raise ValueError("completed criticism requires exact source-call coverage")
        elif self.coverage_completed or self.diagnostic_ref is None:
            raise ValueError("failed criticism must retain debt and a diagnostic")
        return self


class CoverageDebtV1(IdentifiedWorkflowRecord):
    """Terminal dimensional record of completed and outstanding schools."""

    _identity_domain = "criticism.coverage-debt.v1"

    schema_: Literal["criticism.coverage-debt.v1"] = Field(
        "criticism.coverage-debt.v1", alias="schema"
    )
    target_id: str = Field(min_length=1, max_length=256)
    owner_school_id: str = Field(pattern=r"^school-(0|[1-9][0-9]*)$")
    required_school_coverage: int = Field(ge=0, le=1_023)
    completed_school_ids: tuple[str, ...] = ()
    outstanding_school_ids: tuple[str, ...] = ()
    attempt_refs: tuple[str, ...] = ()
    termination_reason: Literal[
        "coverage_complete",
        "ordinary_stop",
        "attempts_exhausted",
        "budget_exhausted",
    ]

    @field_validator("completed_school_ids", "outstanding_school_ids")
    @classmethod
    def _canonical_schools(cls, value):
        if tuple(value) != tuple(sorted(value)) or len(value) != len(set(value)):
            raise ValueError("coverage schools must be sorted and unique")
        return tuple(value)

    @field_validator("attempt_refs")
    @classmethod
    def _unique_attempts(cls, value):
        if len(value) != len(set(value)) or any(
            re.fullmatch(r"sha256:[0-9a-f]{64}", item) is None for item in value
        ):
            raise ValueError("coverage debt attempts must be unique canonical records")
        return tuple(value)

    @model_validator(mode="after")
    def _coverage_shape(self):
        if set(self.completed_school_ids) & set(self.outstanding_school_ids):
            raise ValueError("completed and outstanding criticism coverage must be disjoint")
        complete = len(self.completed_school_ids) >= self.required_school_coverage
        if complete != (self.termination_reason == "coverage_complete"):
            raise ValueError("coverage completion reason differs from completed schools")
        if complete and self.outstanding_school_ids:
            raise ValueError("complete criticism coverage cannot retain debt")
        return self


def _route_hash(route: Route) -> str:
    encoded = json.dumps(
        route.model_dump(mode="json"),
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _model_identity_hash(route: Route) -> str:
    identity = (
        route.provider.strip().casefold(),
        route.model_id.strip().casefold(),
        (route.model_revision or "").strip().casefold(),
    )
    encoded = json.dumps(identity, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def plan_foreign_criticism(
    manifest: RunManifest,
    targets: tuple[ForeignCriticismTargetV1, ...],
) -> ForeignCriticismPlanV1:
    """Select distinct foreign schools and split calls into bounded batches.

    Input order is deliberately irrelevant.  Selection rotates across the
    canonical target order for deterministic load spreading, while coverage
    is always counted by critic school rather than by endpoint or model.
    """

    policy = manifest.criticism_policy
    if policy is None:
        raise ValueError("V4_CRITICISM_POLICY_REQUIRED")

    normalized = tuple(sorted(targets, key=lambda target: target.target_id))
    target_ids = tuple(target.target_id for target in normalized)
    if len(target_ids) != len(set(target_ids)):
        raise ValueError("V4_CRITICISM_TARGET_DUPLICATE")

    bindings = {binding.school_id: binding for binding in policy.bindings}
    routes = manifest.roles["argumentative_critic"]
    target_plans: list[ForeignCriticismTargetPlanV1] = []
    batch_targets: dict[tuple[str, str, int, str, str], list[str]] = defaultdict(list)

    for target_index, target in enumerate(normalized):
        if target.owner_school_id not in bindings:
            raise ValueError(
                "V4_CRITICISM_TARGET_SCHOOL_UNKNOWN: target owner has no critic binding"
            )
        foreign_schools = sorted(set(bindings) - {target.owner_school_id})
        if len(foreign_schools) < policy.minimum_foreign_school_coverage:
            raise ValueError("V4_CRITICISM_FOREIGN_COVERAGE_UNSATISFIED")
        completed = set(target.completed_critic_school_ids)
        if not completed.issubset(foreign_schools):
            raise ValueError(
                "V4_CRITICISM_COMPLETED_SCHOOL_UNKNOWN: completed coverage is not "
                "a configured foreign school"
            )
        missing = sorted(set(foreign_schools) - completed)
        needed = max(0, policy.minimum_foreign_school_coverage - len(completed))
        if needed:
            offset = target_index % len(missing)
            rotated = missing[offset:] + missing[:offset]
            selected = sorted(rotated[:needed])
        else:
            selected = []

        assignments: list[ForeignCriticAssignmentV1] = []
        for critic_school_id in selected:
            binding = bindings[critic_school_id]
            route = routes[binding.seat]
            route_sha256 = _route_hash(route)
            assignment = ForeignCriticAssignmentV1(
                target_id=target.target_id,
                owner_school_id=target.owner_school_id,
                critic_school_id=critic_school_id,
                role=binding.role,
                seat=binding.seat,
                endpoint_id=binding.endpoint_id,
                route_sha256=route_sha256,
                model_identity_sha256=_model_identity_hash(route),
            )
            assignments.append(assignment)
            batch_targets[
                (
                    assignment.critic_school_id,
                    assignment.role,
                    assignment.seat,
                    assignment.endpoint_id,
                    assignment.route_sha256,
                )
            ].append(target.target_id)

        assignment_tuple = tuple(assignments)
        covered_schools = sorted(completed | set(selected))
        covered_routes = [routes[bindings[school].seat] for school in covered_schools]
        distinct_routes = len({_route_hash(route) for route in covered_routes})
        distinct_models = len({_model_identity_hash(route) for route in covered_routes})
        coverage = len(covered_schools)
        target_plans.append(
            ForeignCriticismTargetPlanV1(
                target_id=target.target_id,
                owner_school_id=target.owner_school_id,
                completed_critic_school_ids=target.completed_critic_school_ids,
                assignments=assignment_tuple,
                foreign_school_coverage=coverage,
                distinct_route_coverage=distinct_routes,
                distinct_model_coverage=distinct_models,
                # A shared model is not advertised as route diversity even if
                # it is served through separately named endpoints.
                route_diverse=(distinct_routes == coverage and distinct_models == coverage),
            )
        )

    batches: list[ForeignCriticismBatchV1] = []
    for key in sorted(batch_targets):
        critic_school_id, role, seat, endpoint_id, route_sha256 = key
        assigned_targets = sorted(batch_targets[key])
        for start in range(0, len(assigned_targets), policy.max_batch_size):
            batches.append(
                ForeignCriticismBatchV1(
                    critic_school_id=critic_school_id,
                    role=role,
                    seat=seat,
                    endpoint_id=endpoint_id,
                    route_sha256=route_sha256,
                    target_ids=tuple(
                        assigned_targets[start : start + policy.max_batch_size]
                    ),
                )
            )

    return ForeignCriticismPlanV1(targets=tuple(target_plans), batches=tuple(batches))


def compile_criticism_assignments(
    manifest: RunManifest,
    plan: ForeignCriticismPlanV1,
) -> tuple[CriticismAssignmentV1, ...]:
    """Compile the deterministic plan into durable obligation records."""

    if manifest.schema_version != 6 or manifest.criticism_policy is None:
        raise ValueError("criticism obligation records require RunManifest v6")
    retry_ceiling = 1 + manifest.control_plane_policy.workflow_retry.max_workflow_retries
    eligible_by_owner = {
        target.owner_school_id: tuple(
            sorted(
                binding.school_id
                for binding in manifest.criticism_policy.bindings
                if binding.school_id != target.owner_school_id
            )
        )
        for target in plan.targets
    }
    records = []
    for target in plan.targets:
        eligible = eligible_by_owner[target.owner_school_id]
        for assignment in target.assignments:
            records.append(
                CriticismAssignmentV1.create(
                    manifest_digest=manifest.sha256,
                    target_id=assignment.target_id,
                    owner_school_id=assignment.owner_school_id,
                    critic_school_id=assignment.critic_school_id,
                    eligible_school_order=eligible,
                    order_index=eligible.index(assignment.critic_school_id),
                    role=assignment.role,
                    seat=assignment.seat,
                    endpoint_id=assignment.endpoint_id,
                    route_sha256=assignment.route_sha256,
                    maximum_attempts=retry_ceiling,
                )
            )
    return tuple(
        sorted(records, key=lambda record: (record.target_id, record.order_index))
    )


__all__ = [
    "CoverageDebtV1",
    "CriticismAssignmentV1",
    "CriticismAttemptV1",
    "ForeignCriticAssignmentV1",
    "ForeignCriticismBatchV1",
    "ForeignCriticismPlanV1",
    "ForeignCriticismTargetPlanV1",
    "ForeignCriticismTargetV1",
    "compile_criticism_assignments",
    "plan_foreign_criticism",
]
