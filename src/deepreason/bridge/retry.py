"""Immutable, bounded workflow-level retry authorization for the bridge.

Local JSON repair remains inside one LLM call.  This module governs a fresh
BridgeWorkflow instance after a typed terminal failure.  It has no manifest
activation of its own; RunManifest v4 freezes the policy before production
use, while v1-v3 continue to compile with retries disabled.
"""

from __future__ import annotations

import re
from collections.abc import Callable
from typing import Literal

from pydantic import ConfigDict, Field, StrictInt, field_validator, model_validator

from deepreason.bridge.models import CanonicalBridgeRecord
from deepreason.ontology.frozen import FrozenRecord
from deepreason.scratch.models import HashRef, OpaqueRef


_ERROR_CODE = re.compile(r"^[A-Z][A-Z0-9_]{0,127}$")


class WorkflowRetryPolicyV1(FrozenRecord):
    """Manifest-ready authorization; default construction permits no retry."""

    model_config = ConfigDict(
        frozen=True, extra="forbid", populate_by_name=True
    )

    schema_: Literal["bridge.workflow-retry-policy.v1"] = Field(
        "bridge.workflow-retry-policy.v1", alias="schema"
    )
    max_workflow_retries: StrictInt = Field(default=0, ge=0, le=2)
    retryable_error_codes: tuple[str, ...] = Field(default=(), max_length=16)
    same_catalog_required: Literal[True] = True
    same_formal_fence_required: Literal[True] = True
    same_contract_required: Literal[True] = True
    route_policy: Literal["same_lease"] = "same_lease"

    @field_validator("retryable_error_codes")
    @classmethod
    def _canonical_codes(cls, value):
        if any(_ERROR_CODE.fullmatch(code) is None for code in value):
            raise ValueError("retryable_error_codes must be stable error identifiers")
        if tuple(sorted(set(value))) != value:
            raise ValueError(
                "retryable_error_codes must be sorted and contain no duplicates"
            )
        return value

    @model_validator(mode="after")
    def _enabled_policy_has_a_reason(self):
        if self.max_workflow_retries and not self.retryable_error_codes:
            raise ValueError("enabled workflow retry requires a listed error code")
        if not self.max_workflow_retries and self.retryable_error_codes:
            raise ValueError("disabled workflow retry cannot list error codes")
        return self

    def permits(self, error_code: str | None, completed_retries: int) -> bool:
        return bool(
            error_code in self.retryable_error_codes
            and 0 <= completed_retries < self.max_workflow_retries
        )


class BridgeWorkflowAttemptFenceV1(FrozenRecord):
    """Exact configuration that every fresh retry attempt must retain."""

    model_config = ConfigDict(
        frozen=True, extra="forbid", populate_by_name=True
    )

    schema_: Literal["bridge.workflow-attempt-fence.v1"] = Field(
        "bridge.workflow-attempt-fence.v1", alias="schema"
    )
    manifest_digest: str = Field(pattern=r"^[0-9a-f]{64}$")
    formal_seq: StrictInt = Field(ge=0)
    catalog_id: HashRef
    contract_id: OpaqueRef
    prompt_policy_digest: str = Field(pattern=r"^[0-9a-f]{64}$")
    role: OpaqueRef
    seat: StrictInt = Field(ge=0)
    endpoint_id: OpaqueRef
    route_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")


class BridgeWorkflowRetryV1(CanonicalBridgeRecord):
    """Replay-backed authorization for one new workflow attempt."""

    schema_: Literal["bridge.workflow-retry.v1"] = Field(
        "bridge.workflow-retry.v1", alias="schema"
    )
    ID_DOMAIN = "bridge.workflow-retry.v1"

    prior_failure_id: HashRef
    attempt_number: StrictInt = Field(ge=2, le=3)
    maximum_attempts: StrictInt = Field(ge=1, le=3)
    reason_code: str = Field(pattern=r"^[A-Z][A-Z0-9_]{0,127}$")
    attempt_fence: BridgeWorkflowAttemptFenceV1
    prior_token_count: StrictInt = Field(ge=0)

    @model_validator(mode="after")
    def _attempt_within_maximum(self):
        if self.attempt_number > self.maximum_attempts:
            raise ValueError("workflow retry attempt exceeds its frozen maximum")
        return self


class WorkflowRetryBoundaryError(RuntimeError):
    """A proposed fresh attempt differs from its immutable retry fence."""


def authorize_workflow_retry(
    policy: WorkflowRetryPolicyV1,
    *,
    prior_failure_id: str,
    error_code: str,
    completed_retries: int,
    attempt_fence: BridgeWorkflowAttemptFenceV1,
    prior_token_count: int,
) -> BridgeWorkflowRetryV1:
    """Create one canonical receipt or fail closed without a provider call."""

    policy = WorkflowRetryPolicyV1.model_validate(policy)
    if not policy.permits(error_code, completed_retries):
        raise WorkflowRetryBoundaryError(
            "BRIDGE_WORKFLOW_RETRY_NOT_AUTHORIZED"
        )
    return BridgeWorkflowRetryV1.create(
        prior_failure_id=prior_failure_id,
        attempt_number=completed_retries + 2,
        maximum_attempts=policy.max_workflow_retries + 1,
        reason_code=error_code,
        attempt_fence=attempt_fence,
        prior_token_count=prior_token_count,
    )


def _assert_failed_call_matches_fence(result, fence: BridgeWorkflowAttemptFenceV1) -> None:
    if result.formal_seq != fence.formal_seq:
        raise WorkflowRetryBoundaryError("BRIDGE_WORKFLOW_RETRY_FORMAL_FENCE_CHANGED")
    calls = list(result.model_calls)
    if not calls:
        raise WorkflowRetryBoundaryError("BRIDGE_WORKFLOW_RETRY_CALL_MISSING")
    call = calls[-1]
    if call.role != fence.role or not call.attempt_trace:
        raise WorkflowRetryBoundaryError("BRIDGE_WORKFLOW_RETRY_ROLE_CHANGED")
    for attempt in call.attempt_trace:
        if attempt.contract_id != fence.contract_id:
            raise WorkflowRetryBoundaryError("BRIDGE_WORKFLOW_RETRY_CONTRACT_CHANGED")
        if (
            attempt.seat != fence.seat
            or attempt.endpoint_id != fence.endpoint_id
            or attempt.route_sha256 != fence.route_sha256
        ):
            raise WorkflowRetryBoundaryError("BRIDGE_WORKFLOW_RETRY_ROUTE_CHANGED")


def run_bridge_workflow_with_retries(
    workflow_factory: Callable[[int], object],
    catalog,
    composition_request,
    *,
    retry_policy: WorkflowRetryPolicyV1 | None = None,
    attempt_fence: BridgeWorkflowAttemptFenceV1,
    failure_id_for_result: Callable[[object], str],
    persist_retry: Callable[[BridgeWorkflowRetryV1], None],
    materials=None,
):
    """Run fresh workflow instances under one exact catalog/configuration.

    ``workflow_factory`` receives the one-based workflow attempt number.  A
    fresh object is required on every invocation; BridgeWorkflow itself still
    enforces one run per instance.  The coordinator never feeds a failed
    attempt's fallback ledger into the next attempt.
    """

    policy = WorkflowRetryPolicyV1.model_validate(retry_policy or {})
    if catalog.id != attempt_fence.catalog_id:
        raise WorkflowRetryBoundaryError("BRIDGE_WORKFLOW_RETRY_CATALOG_CHANGED")
    if catalog.formal_seq != attempt_fence.formal_seq:
        raise WorkflowRetryBoundaryError("BRIDGE_WORKFLOW_RETRY_FORMAL_FENCE_CHANGED")

    completed_retries = 0
    prior_tokens = 0
    while True:
        workflow = workflow_factory(completed_retries + 1)
        result = workflow.run(catalog, composition_request, materials=materials)
        prior_tokens += result.token_count
        if result.process_status != "failure" or not policy.permits(
            result.error_code, completed_retries
        ):
            return result
        _assert_failed_call_matches_fence(result, attempt_fence)
        receipt = authorize_workflow_retry(
            policy,
            prior_failure_id=failure_id_for_result(result),
            error_code=result.error_code,
            completed_retries=completed_retries,
            attempt_fence=attempt_fence,
            prior_token_count=prior_tokens,
        )
        persist_retry(receipt)
        completed_retries += 1


__all__ = [
    "BridgeWorkflowAttemptFenceV1",
    "BridgeWorkflowRetryV1",
    "WorkflowRetryBoundaryError",
    "WorkflowRetryPolicyV1",
    "authorize_workflow_retry",
    "run_bridge_workflow_with_retries",
]
