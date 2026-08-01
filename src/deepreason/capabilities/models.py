"""Typed semantic proposals and immutable simulation lifecycle records."""

from __future__ import annotations

import math
import re
from typing import Annotated, Any, ClassVar, Literal

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
_SEGMENT = r"[A-Za-z][A-Za-z0-9_]{0,63}"
OBSERVABLE_NAME_PATTERN = rf"^{_SEGMENT}(?:\.{_SEGMENT}){{0,7}}$"
"""An observable name: an identifier, or a dotted path of up to eight of them.

Dots were added after run-b4d6dfda0c20676a864a051fbc97bda4 died at cycle 0 on
`simulation observables must be plain identifiers`. The model had designed a
3x2x3 measurement grid and returned it nested, which is the natural shape for a
grid, and named the cells `animal.baseline.distinct`. Nothing told it not to:
the identifier rule was in neither the schema nor the field's description, so
the refusal was the first and only statement of it.

The repeat is bounded rather than `*` so the pattern stays finite for backends
that compile the schema into a sampling grammar.
"""
ObservableName = Annotated[str, Field(pattern=OBSERVABLE_NAME_PATTERN)]
SealedInputAlias = Annotated[str, Field(pattern=_ALIAS)]
#: The draft refuses a seed outside the signed 64-bit range; `le` is exclusive
#: of 2**63 in the validator, so the schema states the last legal value.
SimulationSeed = Annotated[int, Field(ge=-(2**63), le=2**63 - 1)]
_MAX_SEMANTIC_JSON_BYTES = 512 * 1024


_UNIQUE_ITEMS = {"uniqueItems": True}
"""Duplicates are refused by the validators below; the schema must say so too.

Without it every one of these arrays told the model repetition was legal and
only the prose said otherwise.
"""


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
    rival_predictions: tuple[str, ...] = Field(
        min_length=1, max_length=32,
        json_schema_extra=_UNIQUE_ITEMS,
    )
    discriminating_purpose: str = Field(min_length=1, max_length=8_192)
    declared_assumptions: tuple[str, ...] = Field(
        default=(), max_length=64,
        json_schema_extra=_UNIQUE_ITEMS,
    )
    input_aliases: tuple[SealedInputAlias, ...] = Field(
        default=(), max_length=64,
        json_schema_extra=_UNIQUE_ITEMS,
    )
    parameter_definitions: tuple[SimulationParameterSetV1, ...] = Field(
        default=(), max_length=256
    )
    requested_seed_set: tuple[SimulationSeed, ...] = Field(
        default=(), max_length=256,
        json_schema_extra=_UNIQUE_ITEMS,
    )
    simulation_mode: Literal[
        "declarative_numeric_v1", "sandboxed_python_v1"
    ] = "declarative_numeric_v1"
    model_source: str = Field(min_length=1, max_length=262_144)
    requested_observables: tuple[ObservableName, ...] = Field(
        min_length=1, max_length=128,
        json_schema_extra=_UNIQUE_ITEMS,
    )
    interpretation_conditions: tuple[str, ...] = Field(
        min_length=1, max_length=64,
        json_schema_extra=_UNIQUE_ITEMS,
    )

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
        if any(re.fullmatch(OBSERVABLE_NAME_PATTERN, name) is None for name in value):
            raise ValueError(
                "simulation observables must be identifiers, optionally dotted"
            )
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
    # V5 binds this reference to a legacy WorkOrderEnvelope. V6 binds it to a
    # WorkPreparationV1 and also names the exact durable provider result that
    # supplied the semantic draft. The optional field is omitted from v5 bytes.
    originating_provider_attempt_ref: str | None = Field(
        default=None, pattern=_WORKFLOW_ID
    )
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
    # Present only for v6: consumption follows a durable semantic admission
    # and a completed terminal on the fresh transaction work item.
    follow_up_semantic_admission_ref: str | None = Field(
        default=None, pattern=_WORKFLOW_ID
    )


_HTTPS_URL = r"^https://[^\s]{1,2048}$"


class ResearchFetchProposalDraftV1(_FrozenModel):
    """Model-authored directed-fetch intent before harness authority attaches.

    Directed research: the proposal names explicit https URLs. Choosing
    sources is the proposer's act; validating them against the frozen
    allowlist and executing them safely is the harness's.
    """

    request_identifier: str = Field(min_length=1, max_length=128)
    purpose: str = Field(min_length=1, max_length=2_000)
    urls: tuple[str, ...] = Field(
        min_length=1,
        max_length=3,
        json_schema_extra={
            **_UNIQUE_ITEMS,
            "items": {"type": "string", "pattern": _HTTPS_URL},
        },
    )

    @field_validator("urls")
    @classmethod
    def _https_and_unique(cls, value):
        if len(value) != len(set(value)):
            raise ValueError("research proposal urls must not contain duplicates")
        if any(re.fullmatch(_HTTPS_URL, url) is None for url in value):
            raise ValueError("research proposal urls must be bounded https URLs")
        return tuple(value)


class ResearchFetchProposalV1(ResearchFetchProposalDraftV1, _IdentifiedCapabilityRecord):
    """Semantic fetch proposal; this record conveys no fetch authority."""

    _identity_domain = "capability.research-proposal.v1"

    schema_: Literal["capability.research-proposal.v1"] = Field(
        "capability.research-proposal.v1", alias="schema"
    )
    originating_work_order_ref: str = Field(pattern=_WORKFLOW_ID)
    originating_provider_attempt_ref: str | None = Field(
        default=None, pattern=_WORKFLOW_ID
    )
    source_call_seq: int = Field(ge=0)
    proposal_index: int = Field(ge=0, le=31)
    problem_ref: str = Field(min_length=1, max_length=512)
    run_input_digest: str = Field(pattern=_DIGEST)


class ResearchGrantV1(_IdentifiedCapabilityRecord):
    """Harness-validated fetch authority: every URL matched the frozen
    allowlist and the requests budget still had headroom at grant time."""

    _identity_domain = "capability.research-grant.v1"

    schema_: Literal["capability.research-grant.v1"] = Field(
        "capability.research-grant.v1", alias="schema"
    )
    proposal_ref: str = Field(pattern=_WORKFLOW_ID)
    manifest_digest: str = Field(pattern=_DIGEST)
    run_input_digest: str = Field(pattern=_DIGEST)
    policy_digest: str = Field(pattern=_DIGEST)
    backend_identity: str = Field(min_length=1, max_length=128)
    granted_urls: tuple[str, ...] = Field(min_length=1, max_length=3)
    requests_limit: int = Field(ge=1, le=10_000)
    maximum_response_bytes: int = Field(ge=1_024, le=16 * 1024 * 1024)


class CompiledResearchFetchV1(_IdentifiedCapabilityRecord):
    """The frozen fetch plan: exactly what will be dispatched, nothing else."""

    _identity_domain = "capability.compiled-research-fetch.v1"

    schema_: Literal["capability.compiled-research-fetch.v1"] = Field(
        "capability.compiled-research-fetch.v1", alias="schema"
    )
    proposal_ref: str = Field(pattern=_WORKFLOW_ID)
    grant_ref: str = Field(pattern=_WORKFLOW_ID)
    urls: tuple[str, ...] = Field(min_length=1, max_length=3)
    domain_allowlist: tuple[str, ...] = Field(min_length=1, max_length=64)
    requests_limit: int = Field(ge=1, le=10_000)
    maximum_response_bytes: int = Field(ge=1_024, le=16 * 1024 * 1024)
    timeout_seconds: int = Field(ge=1, le=300)


class ResearchWorkOrderV1(_IdentifiedCapabilityRecord):
    """Durable operational fetch authority compiled entirely by the harness."""

    _identity_domain = "capability.research-work-order.v1"

    schema_: Literal["capability.research-work-order.v1"] = Field(
        "capability.research-work-order.v1", alias="schema"
    )
    proposal_ref: str = Field(pattern=_WORKFLOW_ID)
    grant_ref: str = Field(pattern=_WORKFLOW_ID)
    compiled_research_ref: str = Field(pattern=_WORKFLOW_ID)
    manifest_digest: str = Field(pattern=_DIGEST)
    run_input_digest: str = Field(pattern=_DIGEST)
    policy_digest: str = Field(pattern=_DIGEST)
    backend_identity: Literal["web.contained.v1"] = "web.contained.v1"
    requests_limit: int = Field(ge=1, le=10_000)
    maximum_response_bytes: int = Field(ge=1_024, le=16 * 1024 * 1024)


class ResearchFetchAttemptV1(_FrozenModel):
    """One sanitized fetch attempt inside an execution receipt.

    The requests arithmetic is replay-validated: ``requests_used`` after
    each attempt never exceeds ``requests_limit`` on the receipt, and the
    typed budget-exhaustion outcome always carries both (the grounded
    shape from the 2026-07-27 campaign)."""

    seq: int = Field(ge=1)
    url: str = Field(min_length=1, max_length=4_096)
    host: str = Field(default="", max_length=1_024)
    outcome: str = Field(min_length=1, max_length=64, pattern=r"^[A-Z][A-Z0-9_]*$")
    http_status: int | None = Field(default=None, ge=100, le=599)
    byte_count: int = Field(default=0, ge=0)
    content_sha256: str | None = Field(default=None, pattern=_DIGEST)
    requests_used: int = Field(ge=0)


class ResearchExecutionReceiptV1(_IdentifiedCapabilityRecord):
    _identity_domain = "capability.research-execution-receipt.v1"

    schema_: Literal["capability.research-execution-receipt.v1"] = Field(
        "capability.research-execution-receipt.v1", alias="schema"
    )
    proposal_ref: str = Field(pattern=_WORKFLOW_ID)
    run_input_digest: str = Field(pattern=_DIGEST)
    research_work_order_ref: str = Field(pattern=_WORKFLOW_ID)
    compiled_specification_ref: str = Field(pattern=_WORKFLOW_ID)
    attempts: tuple[ResearchFetchAttemptV1, ...] = Field(min_length=1, max_length=32)
    requests_used_total: int = Field(ge=0)
    requests_limit: int = Field(ge=1, le=10_000)
    outcome: Literal["fetched", "nothing_fetched", "budget_exhausted"]

    @model_validator(mode="after")
    def _receipt_arithmetic(self):
        used = [attempt.requests_used for attempt in self.attempts]
        if used != sorted(used):
            raise ValueError("research receipt attempts must be budget-ordered")
        if self.requests_used_total != used[-1]:
            raise ValueError("research receipt total differs from its attempts")
        if self.requests_used_total > self.requests_limit:
            raise ValueError("research receipt spends beyond its frozen limit")
        if (self.outcome == "budget_exhausted") != any(
            attempt.outcome == "RESEARCH_BUDGET_EXHAUSTED"
            for attempt in self.attempts
        ):
            raise ValueError(
                "budget exhaustion and its typed attempt record must agree"
            )
        return self


class ResearchFetchedItemV1(_FrozenModel):
    url: str = Field(min_length=1, max_length=4_096)
    content_sha256: str = Field(pattern=_DIGEST)
    byte_count: int = Field(ge=0)
    text_sha256: str = Field(pattern=_DIGEST)


class ResearchResultPackageV1(_IdentifiedCapabilityRecord):
    _identity_domain = "capability.research-result-package.v1"

    schema_: Literal["capability.research-result-package.v1"] = Field(
        "capability.research-result-package.v1", alias="schema"
    )
    proposal_ref: str = Field(pattern=_WORKFLOW_ID)
    run_input_digest: str = Field(pattern=_DIGEST)
    execution_receipt_ref: str = Field(pattern=_WORKFLOW_ID)
    items: tuple[ResearchFetchedItemV1, ...] = Field(default=(), max_length=3)


class ResearchConsumptionV1(_IdentifiedCapabilityRecord):
    _identity_domain = "capability.research-consumption.v1"

    schema_: Literal["capability.research-consumption.v1"] = Field(
        "capability.research-consumption.v1", alias="schema"
    )
    proposal_ref: str = Field(pattern=_WORKFLOW_ID)
    run_input_digest: str = Field(pattern=_DIGEST)
    result_package_ref: str = Field(pattern=_WORKFLOW_ID)
    evidence_refs: tuple[str, ...] = Field(min_length=1, max_length=3)


__all__ = [
    "CapabilityBudgetDeltaV1",
    "CapabilityLifecycle",
    "CapabilityTransitionV1",
    "CompiledResearchFetchV1",
    "CompiledSimulationV1",
    "CompiledSimulationSpecV1",
    "ResearchConsumptionV1",
    "ResearchExecutionReceiptV1",
    "ResearchFetchAttemptV1",
    "ResearchFetchProposalDraftV1",
    "ResearchFetchProposalV1",
    "ResearchFetchedItemV1",
    "ResearchGrantV1",
    "ResearchResultPackageV1",
    "ResearchWorkOrderV1",
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
