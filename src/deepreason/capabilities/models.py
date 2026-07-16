"""Typed semantic proposals and immutable simulation lifecycle records."""

from __future__ import annotations

import math
import re
from typing import Any, ClassVar, Literal

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    ValidationInfo,
    field_validator,
    model_validator,
)

from deepreason.canonical import canonical_json, sha256_hex
from deepreason.capabilities.enums import CapabilityLifecycle

_DIGEST = r"^[0-9a-f]{64}$"
_WORKFLOW_ID = r"^sha256:[0-9a-f]{64}$"
_ALIAS = r"^[A-Z][A-Z0-9_]{0,31}$"
_NAME = r"^[A-Za-z][A-Za-z0-9_]{0,63}$"
_MAX_SEMANTIC_JSON_BYTES = 512 * 1024


def _bounded_json(value: Any, *, depth: int = 0) -> Any:
    """Reject non-JSON, non-finite, or pathologically nested proposal data."""

    if depth > 12:
        raise ValueError("simulation parameter data exceeds maximum nesting depth")
    if value is None or isinstance(value, (bool, str, int)):
        return value
    if isinstance(value, float):
        if not math.isfinite(value):
            raise ValueError("simulation parameter numbers must be finite")
        return value
    if isinstance(value, list):
        return [_bounded_json(item, depth=depth + 1) for item in value]
    if isinstance(value, tuple):
        return tuple(_bounded_json(item, depth=depth + 1) for item in value)
    if isinstance(value, dict):
        if any(not isinstance(key, str) or not key for key in value):
            raise ValueError("simulation parameter keys must be nonempty strings")
        return {
            key: _bounded_json(item, depth=depth + 1)
            for key, item in value.items()
        }
    raise ValueError("simulation parameter data must be finite JSON")


class _FrozenModel(BaseModel):
    model_config = ConfigDict(
        extra="forbid", frozen=True, populate_by_name=True, serialize_by_alias=True
    )


class _IdentifiedCapabilityRecord(_FrozenModel):
    id: str = Field(pattern=_WORKFLOW_ID)
    _identity_domain: ClassVar[str]

    def _identity_payload(self) -> dict[str, Any]:
        return self.model_dump(
            mode="json", by_alias=True, exclude={"id"}, exclude_none=True
        )

    @classmethod
    def create(cls, **values):
        provisional = cls.model_validate(
            {"id": "sha256:" + "0" * 64, **values},
            context={"skip_capability_identity": True},
        )
        record_id = "sha256:" + sha256_hex(
            cls._identity_domain.encode("utf-8")
            + b"\x00"
            + canonical_json(provisional._identity_payload())
        )
        return cls.model_validate(
            {**provisional._identity_payload(), "id": record_id}
        )

    @model_validator(mode="after")
    def _id_matches_payload(self, info: ValidationInfo):
        if info.context and info.context.get("skip_capability_identity"):
            return self
        expected = "sha256:" + sha256_hex(
            self._identity_domain.encode("utf-8")
            + b"\x00"
            + canonical_json(self._identity_payload())
        )
        if self.id != expected:
            raise ValueError("capability record id does not match its canonical payload")
        return self


class SimulationParameterSetV1(_FrozenModel):
    name: str = Field(min_length=1, max_length=128)
    values: dict[str, Any]

    @field_validator("values", mode="before")
    @classmethod
    def _finite_bounded_values(cls, value):
        normalized = _bounded_json(value)
        if not isinstance(normalized, dict) or not normalized:
            raise ValueError("a simulation parameter set requires at least one value")
        if len(canonical_json(normalized)) > _MAX_SEMANTIC_JSON_BYTES:
            raise ValueError("simulation parameter data exceeds the contract bound")
        return normalized


class SimulationProposalDraftV1(_FrozenModel):
    """Model-authored semantic content before harness authority is attached."""

    request_identifier: str = Field(min_length=1, max_length=128)
    hypothesis: str = Field(min_length=1, max_length=16_384)
    rival_predictions: tuple[str, ...] = Field(min_length=1, max_length=32)
    discriminating_purpose: str = Field(min_length=1, max_length=8_192)
    declared_assumptions: tuple[str, ...] = Field(default=(), max_length=64)
    input_aliases: tuple[str, ...] = Field(default=(), max_length=64)
    parameter_definitions: tuple[SimulationParameterSetV1, ...] = Field(
        default=(), max_length=256
    )
    requested_seed_set: tuple[int, ...] = Field(default=(), max_length=256)
    simulation_mode: Literal[
        "declarative_numeric_v1", "sandboxed_python_v1"
    ] = "declarative_numeric_v1"
    model_source: str = Field(min_length=1, max_length=262_144)
    requested_observables: tuple[str, ...] = Field(min_length=1, max_length=128)
    interpretation_conditions: tuple[str, ...] = Field(min_length=1, max_length=64)

    @field_validator(
        "rival_predictions",
        "declared_assumptions",
        "input_aliases",
        "requested_seed_set",
        "requested_observables",
        "interpretation_conditions",
    )
    @classmethod
    def _unique_sequences(cls, value):
        if len(value) != len(set(value)):
            raise ValueError("simulation proposal sequences must not contain duplicates")
        return tuple(value)

    @field_validator("input_aliases")
    @classmethod
    def _alias_syntax(cls, value):
        if any(re.fullmatch(_ALIAS, alias) is None for alias in value):
            raise ValueError("simulation inputs must use sealed-catalog aliases")
        return tuple(value)

    @field_validator("requested_observables")
    @classmethod
    def _observable_syntax(cls, value):
        if any(re.fullmatch(_NAME, name) is None for name in value):
            raise ValueError("simulation observables must be plain identifiers")
        return tuple(value)

    @field_validator("requested_seed_set")
    @classmethod
    def _bounded_seeds(cls, value):
        if any(
            isinstance(seed, bool)
            or not isinstance(seed, int)
            or not -(2**63) <= seed < 2**63
            for seed in value
        ):
            raise ValueError("simulation seeds must be signed 64-bit integers")
        return tuple(value)


class SimulationProposalV1(SimulationProposalDraftV1, _IdentifiedCapabilityRecord):
    """Semantic experiment proposal; this record conveys no execution authority."""

    _identity_domain = "capability.simulation-proposal.v1"

    schema_: Literal["capability.simulation-proposal.v1"] = Field(
        "capability.simulation-proposal.v1", alias="schema"
    )
    originating_work_order_ref: str = Field(pattern=_WORKFLOW_ID)
    source_call_seq: int = Field(ge=0)
    proposal_index: int = Field(ge=0, le=31)
    problem_ref: str = Field(min_length=1, max_length=512)
    run_input_digest: str = Field(pattern=_DIGEST)


class CapabilityBudgetDeltaV1(_FrozenModel):
    requests: int = Field(default=0, ge=0, le=1)
    executions: int = Field(default=0, ge=0, le=1)
    result_follow_ups: int = Field(default=0, ge=0, le=1)

    @model_validator(mode="after")
    def _at_most_one_counter(self):
        if sum((self.requests, self.executions, self.result_follow_ups)) > 1:
            raise ValueError("one capability transition may consume one budget class")
        return self


def capability_next_process_digest(
    *,
    previous_process_digest: str,
    request_ref: str,
    request_digest: str,
    lifecycle: CapabilityLifecycle,
    previous_transition_ref: str | None,
    phase_record_ref: str | None,
    trigger_ref: str,
    budget_delta: CapabilityBudgetDeltaV1,
) -> str:
    payload = {
        "previous_process_digest": previous_process_digest,
        "request_ref": request_ref,
        "request_digest": request_digest,
        "lifecycle": lifecycle.value,
        "previous_transition_ref": previous_transition_ref,
        "phase_record_ref": phase_record_ref,
        "trigger_ref": trigger_ref,
        "budget_delta": budget_delta.model_dump(mode="json"),
    }
    return "sha256:" + sha256_hex(
        b"capability.process-step.v1\x00" + canonical_json(payload)
    )


class CapabilityTransitionV1(_IdentifiedCapabilityRecord):
    _identity_domain = "capability.transition.v1"

    schema_: Literal["capability.transition.v1"] = Field(
        "capability.transition.v1", alias="schema"
    )
    manifest_digest: str = Field(pattern=_DIGEST)
    run_input_digest: str = Field(pattern=_DIGEST)
    capability_policy_digest: str = Field(pattern=_DIGEST)
    request_ref: str = Field(pattern=_WORKFLOW_ID)
    request_digest: str = Field(pattern=_WORKFLOW_ID)
    originating_work_order_ref: str = Field(pattern=_WORKFLOW_ID)
    problem_ref: str = Field(min_length=1, max_length=512)
    formal_fence_seq: int = Field(ge=0)
    scratch_fence_seq: int = Field(ge=0)
    lifecycle: CapabilityLifecycle
    previous_transition_ref: str | None = Field(default=None, pattern=_WORKFLOW_ID)
    phase_record_ref: str | None = Field(default=None, pattern=_WORKFLOW_ID)
    trigger_ref: str = Field(min_length=1, max_length=512)
    budget_delta: CapabilityBudgetDeltaV1 = Field(
        default_factory=CapabilityBudgetDeltaV1
    )
    previous_process_digest: str = Field(pattern=_WORKFLOW_ID)
    next_process_digest: str = Field(pattern=_WORKFLOW_ID)
    reason_code: str = Field(min_length=1, max_length=128)

    @model_validator(mode="after")
    def _one_fence_and_initial_link(self):
        if self.formal_fence_seq != self.scratch_fence_seq:
            raise ValueError("capability transition requires one immutable state fence")
        if (self.lifecycle == CapabilityLifecycle.PROPOSED) != (
            self.previous_transition_ref is None
        ):
            raise ValueError("only PROPOSED begins a capability transition chain")
        if self.lifecycle == CapabilityLifecycle.PROPOSED:
            if self.phase_record_ref != self.request_ref:
                raise ValueError("PROPOSED must carry the exact semantic proposal")
        elif self.lifecycle in {
            CapabilityLifecycle.GRANTED,
            CapabilityLifecycle.COMPILED,
            CapabilityLifecycle.DISPATCHED,
            CapabilityLifecycle.SUCCEEDED,
            CapabilityLifecycle.FAILED,
            CapabilityLifecycle.RESULT_PACKAGED,
            CapabilityLifecycle.CONSUMED,
        } and self.phase_record_ref is None:
            raise ValueError("this capability transition requires a phase record")
        expected_budget = {
            CapabilityLifecycle.PROPOSED: CapabilityBudgetDeltaV1(requests=1),
            CapabilityLifecycle.DISPATCHED: CapabilityBudgetDeltaV1(executions=1),
            CapabilityLifecycle.CONSUMED: CapabilityBudgetDeltaV1(result_follow_ups=1),
        }.get(self.lifecycle, CapabilityBudgetDeltaV1())
        if self.budget_delta != expected_budget:
            raise ValueError("capability transition has the wrong budget delta")
        expected_process = capability_next_process_digest(
            previous_process_digest=self.previous_process_digest,
            request_ref=self.request_ref,
            request_digest=self.request_digest,
            lifecycle=self.lifecycle,
            previous_transition_ref=self.previous_transition_ref,
            phase_record_ref=self.phase_record_ref,
            trigger_ref=self.trigger_ref,
            budget_delta=self.budget_delta,
        )
        if self.next_process_digest != expected_process:
            raise ValueError("capability transition process digest is not canonical")
        return self


class SimulationGrantV1(_IdentifiedCapabilityRecord):
    _identity_domain = "capability.simulation-grant.v1"

    schema_: Literal["capability.simulation-grant.v1"] = Field(
        "capability.simulation-grant.v1", alias="schema"
    )
    proposal_ref: str = Field(pattern=_WORKFLOW_ID)
    manifest_digest: str = Field(pattern=_DIGEST)
    run_input_digest: str = Field(pattern=_DIGEST)
    policy_digest: str = Field(pattern=_DIGEST)
    template_identity: str = Field(min_length=1, max_length=128)
    backend_identity: str = Field(min_length=1, max_length=128)
    toolchain_identity: str = Field(min_length=1, max_length=128)
    seed_set: tuple[int, ...] = Field(min_length=1, max_length=256)
    deterministic_step_limit: int = Field(ge=1)
    sample_limit: int = Field(ge=1)
    maximum_output_bytes: int = Field(ge=1)


class CompiledSimulationSpecV1(_FrozenModel):
    schema_: Literal["deepreason-simulation-v1"] = Field(
        "deepreason-simulation-v1", alias="schema"
    )
    language: Literal["python"] = "python"
    entry: str = Field(min_length=1, pattern=r"^[A-Za-z][A-Za-z0-9_]*$")
    seed_set: tuple[int, ...] = Field(min_length=1)
    inputs_ref: str = Field(pattern=_DIGEST)
    observables: tuple[str, ...] = Field(min_length=1)
    checker_ref: str = Field(pattern=_DIGEST)
    deterministic_step_limit: int = Field(ge=1)
    sample_limit: int = Field(ge=1)
    toolchain_id: str = Field(min_length=1)


class CompiledSimulationV1(_IdentifiedCapabilityRecord):
    _identity_domain = "capability.compiled-simulation.v1"

    schema_: Literal["capability.compiled-simulation.v1"] = Field(
        "capability.compiled-simulation.v1", alias="schema"
    )
    proposal_ref: str = Field(pattern=_WORKFLOW_ID)
    grant_ref: str = Field(pattern=_WORKFLOW_ID)
    template_identity: str = Field(min_length=1, max_length=128)
    source_ref: str = Field(pattern=_DIGEST)
    source_sha256: str = Field(pattern=_DIGEST)
    input_ref: str = Field(pattern=_DIGEST)
    input_sha256: str = Field(pattern=_DIGEST)
    checker_ref: str = Field(pattern=_DIGEST)
    checker_sha256: str = Field(pattern=_DIGEST)
    specification: CompiledSimulationSpecV1
    generated_code_bytes: int = Field(ge=1)
    input_bytes: int = Field(ge=1)
    maximum_output_bytes: int = Field(ge=1)


class SimulationWorkOrderV1(_IdentifiedCapabilityRecord):
    """Durable operational authority compiled entirely by the harness."""

    _identity_domain = "capability.simulation-work-order.v1"

    schema_: Literal["capability.simulation-work-order.v1"] = Field(
        "capability.simulation-work-order.v1", alias="schema"
    )
    proposal_ref: str = Field(pattern=_WORKFLOW_ID)
    grant_ref: str = Field(pattern=_WORKFLOW_ID)
    compiled_simulation_ref: str = Field(pattern=_WORKFLOW_ID)
    manifest_digest: str = Field(pattern=_DIGEST)
    run_input_digest: str = Field(pattern=_DIGEST)
    policy_digest: str = Field(pattern=_DIGEST)
    runner_profile: Literal[
        "simulation.declarative.v1", "simulation.container.v1"
    ]
    template_identity: str = Field(min_length=1, max_length=128)
    backend_identity: str = Field(min_length=1, max_length=128)
    toolchain_identity: str = Field(min_length=1, max_length=128)
    maximum_wall_ms: int = Field(ge=1, le=300_000)
    maximum_memory_bytes: int = Field(ge=1, le=4 * 1024 * 1024 * 1024)
    maximum_output_bytes: int = Field(ge=1)
    deterministic_step_limit: int = Field(ge=1)
    sample_limit: int = Field(ge=1)
    network: Literal[False] = False
    filesystem_policy: Literal["isolated_no_filesystem"] = (
        "isolated_no_filesystem"
    )


class SimulationAttemptV1(_FrozenModel):
    attempt: int = Field(ge=0, le=8)
    backend_verdict: Literal["pass", "fail", "overrun"]
    fingerprint: dict[str, Any]
    diagnostics_ref: str | None = Field(default=None, pattern=_DIGEST)
    output_ref: str | None = Field(default=None, pattern=_DIGEST)
    stdout_ref: str = Field(pattern=_DIGEST)
    stderr_ref: str = Field(pattern=_DIGEST)
    sample_count: int = Field(ge=0)

    @field_validator("fingerprint", mode="before")
    @classmethod
    def _bounded_fingerprint(cls, value):
        normalized = _bounded_json(value)
        if not isinstance(normalized, dict):
            raise ValueError("simulation fingerprint must be a JSON object")
        return normalized


class SimulationExecutionReceiptV1(_IdentifiedCapabilityRecord):
    _identity_domain = "capability.simulation-execution-receipt.v1"

    schema_: Literal["capability.simulation-execution-receipt.v1"] = Field(
        "capability.simulation-execution-receipt.v1", alias="schema"
    )
    proposal_ref: str = Field(pattern=_WORKFLOW_ID)
    run_input_digest: str = Field(pattern=_DIGEST)
    simulation_work_order_ref: str = Field(pattern=_WORKFLOW_ID)
    compiled_specification_ref: str = Field(pattern=_WORKFLOW_ID)
    started_at: str = Field(min_length=1, max_length=64)
    completed_at: str = Field(min_length=1, max_length=64)
    execution_disposition: Literal[
        "runner_completed", "dispatch_interrupted"
    ] = "runner_completed"
    operational_status: Literal["succeeded", "failed"]
    attempts: tuple[SimulationAttemptV1, ...] = Field(min_length=1, max_length=9)
    final_backend_verdict: Literal["pass", "fail", "overrun"]
    source_sha256: str = Field(pattern=_DIGEST)
    inputs_sha256: str = Field(pattern=_DIGEST)
    checker_sha256: str = Field(pattern=_DIGEST)
    specification_sha256: str = Field(pattern=_DIGEST)
    output_bytes: int = Field(ge=0)
    output_truncated: bool
    resource_limits: dict[str, Any]
    diagnostic: str | None = Field(default=None, max_length=4_096)

    @field_validator("resource_limits", mode="before")
    @classmethod
    def _bounded_resource_limits(cls, value):
        normalized = _bounded_json(value)
        if not isinstance(normalized, dict):
            raise ValueError("simulation resource limits must be a JSON object")
        return normalized

    @model_validator(mode="after")
    def _attempt_summary_matches(self):
        if self.attempts[-1].backend_verdict != self.final_backend_verdict:
            raise ValueError("receipt final verdict differs from the final attempt")
        if (self.operational_status == "failed") != (
            self.final_backend_verdict != "pass" or self.output_truncated
        ):
            raise ValueError("receipt operational status differs from execution outcome")
        if (
            self.execution_disposition == "dispatch_interrupted"
            and (
                self.operational_status != "failed"
                or self.final_backend_verdict != "overrun"
            )
        ):
            raise ValueError("an interrupted dispatch must remain an unknown failure")
        return self


class SimulationResultPackageV1(_IdentifiedCapabilityRecord):
    _identity_domain = "capability.simulation-result-package.v1"

    schema_: Literal["capability.simulation-result-package.v1"] = Field(
        "capability.simulation-result-package.v1", alias="schema"
    )
    proposal_ref: str = Field(pattern=_WORKFLOW_ID)
    run_input_digest: str = Field(pattern=_DIGEST)
    receipt_ref: str = Field(pattern=_WORKFLOW_ID)
    structured_result_ref: str = Field(pattern=_DIGEST)
    result_context_ref: str = Field(pattern=_DIGEST)
    epistemic_status: Literal["recorded_observation"] = "recorded_observation"
    assumptions: tuple[str, ...] = Field(default=(), max_length=64)
    execution_limitations: tuple[str, ...] = Field(min_length=1, max_length=64)
    original_hypothesis: str = Field(min_length=1, max_length=16_384)
    rival_predictions: tuple[str, ...] = Field(min_length=1, max_length=32)


class SimulationConsumptionV1(_IdentifiedCapabilityRecord):
    _identity_domain = "capability.simulation-consumption.v1"

    schema_: Literal["capability.simulation-consumption.v1"] = Field(
        "capability.simulation-consumption.v1", alias="schema"
    )
    proposal_ref: str = Field(pattern=_WORKFLOW_ID)
    run_input_digest: str = Field(pattern=_DIGEST)
    result_package_ref: str = Field(pattern=_WORKFLOW_ID)
    follow_up_work_order_ref: str = Field(pattern=_WORKFLOW_ID)
    delivery: Literal["fresh_reasoning_work_order"] = "fresh_reasoning_work_order"


__all__ = [
    "CapabilityBudgetDeltaV1",
    "CapabilityLifecycle",
    "CapabilityTransitionV1",
    "CompiledSimulationV1",
    "CompiledSimulationSpecV1",
    "SimulationAttemptV1",
    "SimulationConsumptionV1",
    "SimulationExecutionReceiptV1",
    "SimulationGrantV1",
    "SimulationParameterSetV1",
    "SimulationProposalDraftV1",
    "SimulationProposalV1",
    "SimulationResultPackageV1",
    "SimulationWorkOrderV1",
    "capability_next_process_digest",
]
