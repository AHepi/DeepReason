"""Capability-typed workflow records for the conjecture control boundary.

These records contain process authority and immutable references only.  Role
payloads remain in their existing semantic contracts and model output never
authors a :class:`TransitionDecisionV1` or :class:`GuardResultV1`.
"""

from __future__ import annotations

from enum import Enum
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
from deepreason.frozen import FrozenDict, FrozenList
from deepreason.runtime.stop import StopDecision
from deepreason.scratch.models import RetrievalChannel


_ZERO_ID = "sha256:" + "0" * 64
_ID_PATTERN = r"^sha256:[0-9a-f]{64}$"
_DIGEST_PATTERN = r"^[0-9a-f]{64}$"


def freeze_workflow_json(value: Any) -> Any:
    """Return a deeply immutable canonical-JSON value."""

    if isinstance(value, dict):
        return FrozenDict(
            {
                str(key): freeze_workflow_json(item)
                for key, item in value.items()
            }
        )
    if isinstance(value, (list, tuple)):
        return FrozenList(freeze_workflow_json(item) for item in value)
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    raise TypeError("task payload values must be canonical JSON values")


def repair_attempt_trigger_ref(attempt: int, diagnostic_ref: str) -> str:
    """Bind one repair authorization to a diagnostic occurrence.

    Content-addressed diagnostics can repeat byte-for-byte across attempts.
    The attempt index keeps each bounded authorization distinct while the
    original immutable diagnostic pointer remains visible when it fits.
    """

    if type(attempt) is not int or attempt < 0:
        raise ValueError("repair attempt index must be a nonnegative integer")
    if not isinstance(diagnostic_ref, str) or not diagnostic_ref:
        raise ValueError("repair attempt requires an immutable diagnostic reference")
    direct = f"repair-attempt:{attempt}:{diagnostic_ref}"
    if len(direct) <= 512:
        return direct
    return "repair-attempt:sha256:" + sha256_hex(
        b"workflow.repair-attempt.v1\x00"
        + canonical_json(
            {"attempt": attempt, "diagnostic_ref": diagnostic_ref}
        )
    )


def _validate_json_pointer(value: str) -> str:
    """Validate the RFC 6901 spelling used at the repair boundary."""

    if value == "":
        return value
    if not value.startswith("/"):
        raise ValueError("repair paths must be canonical JSON pointers")
    for token in value[1:].split("/"):
        index = 0
        while index < len(token):
            if token[index] != "~":
                index += 1
                continue
            if index + 1 >= len(token) or token[index + 1] not in {"0", "1"}:
                raise ValueError("repair paths contain an invalid JSON pointer escape")
            index += 2
    return value


class WorkflowRecord(BaseModel):
    """Strict immutable base for process records, including nested helpers."""

    model_config = ConfigDict(
        extra="forbid",
        frozen=True,
        populate_by_name=True,
    )


class IdentifiedWorkflowRecord(WorkflowRecord):
    """Domain-separated content identity shared by canonical workflow records."""

    id: str = Field(pattern=_ID_PATTERN)
    _identity_domain: ClassVar[str]

    def _identity_payload(self) -> dict[str, Any]:
        return self.model_dump(
            mode="json",
            by_alias=True,
            exclude={"id"},
            exclude_none=True,
        )

    @classmethod
    def create(cls, **values):
        provisional = cls.model_validate(
            {"id": _ZERO_ID, **values},
            context={"skip_workflow_identity": True},
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
        if info.context and info.context.get("skip_workflow_identity"):
            return self
        expected = "sha256:" + sha256_hex(
            self._identity_domain.encode("utf-8")
            + b"\x00"
            + canonical_json(self._identity_payload())
        )
        if self.id != expected:
            raise ValueError("workflow record id does not match its canonical payload")
        return self


class WorkflowTaskKind(str, Enum):
    CONJECTURE = "conjecture"


class CapabilityOutcome(str, Enum):
    CANDIDATE_PROPOSAL = "candidate_proposal"
    CONTEXT_REQUEST = "context_request"
    ABSTENTION = "abstention"


class ProposalValidationOutcome(str, Enum):
    VALID_FIRST_ATTEMPT = "valid_first_attempt"
    VALID_AFTER_REPAIR = "valid_after_repair"
    REPAIR_EXHAUSTED = "repair_exhausted"
    TRANSPORT_FAILED = "transport_failed"


class GuardFindingOutcome(str, Enum):
    ADMIT = "admit"
    REJECT = "reject"
    DEDUPLICATE = "deduplicate"


class GuardFindingCode(str, Enum):
    PASSED = "passed"
    BATTERY_EQUIVALENT = "battery_equivalent"
    REFUTED_EQUIVALENT = "refuted_equivalent"
    CONTENT_DUPLICATE = "content_duplicate"
    INTERFACE_INVALID = "interface_invalid"
    SCHEMA_INVALID = "schema_invalid"


class TransitionKind(str, Enum):
    WORK_ENABLED = "work_enabled"
    WORK_ISSUED = "work_issued"
    PROPOSAL_RECEIVED = "proposal_received"
    PROPOSAL_ADMITTED = "proposal_admitted"
    PROPOSAL_REJECTED = "proposal_rejected"
    PROPOSAL_DEDUPLICATED = "proposal_deduplicated"
    REPAIR_REQUESTED = "repair_requested"
    REPAIR_EXHAUSTED = "repair_exhausted"
    CONTEXT_REQUESTED = "context_requested"
    CONTEXT_GRANTED = "context_granted"
    CONTEXT_DENIED = "context_denied"
    WORK_FINISHED = "work_finished"
    WORK_ABANDONED = "work_abandoned"


class TriggerKind(str, Enum):
    PROBLEM_SELECTED = "problem_selected"
    CONTEXT_PREPARED = "context_prepared"
    PROVIDER_RESULT = "provider_result"
    GUARD_RESULT = "guard_result"
    CONTEXT_DECISION = "context_decision"
    REPAIR_DECISION = "repair_decision"
    WORKFLOW_TERMINATION = "workflow_termination"


class RouteLeaseRefV1(WorkflowRecord):
    role: Literal["conjecturer"] = "conjecturer"
    seat: int = Field(ge=0)
    endpoint_id: str = Field(min_length=1, max_length=512)
    route_sha256: str = Field(pattern=_DIGEST_PATTERN)


class BudgetDeltaV1(WorkflowRecord):
    reserved_tokens: int = Field(default=0, ge=0)
    spent_tokens: int = Field(default=0, ge=0)
    released_tokens: int = Field(default=0, ge=0)


class LocalRepairPolicyV1(IdentifiedWorkflowRecord):
    _identity_domain = "workflow.local-repair-policy.v1"

    schema_: Literal["workflow.local-repair-policy.v1"] = Field(
        "workflow.local-repair-policy.v1", alias="schema"
    )
    max_schema_repairs: int = Field(ge=0, le=2)
    scopes: tuple[Literal["whole_object", "smallest_subtree"], ...] = (
        "whole_object",
        "smallest_subtree",
    )
    same_contract: Literal[True] = True
    same_route: Literal[True] = True

    @field_validator("scopes")
    @classmethod
    def _canonical_scopes(cls, value):
        canonical = tuple(
            scope
            for scope in ("whole_object", "smallest_subtree")
            if scope in value
        )
        if tuple(value) != canonical:
            raise ValueError("repair scopes must be unique and in canonical order")
        return tuple(value)


class CapabilityGrantV1(IdentifiedWorkflowRecord):
    _identity_domain = "workflow.capability-grant.v1"

    schema_: Literal["workflow.capability-grant.v1"] = Field(
        "workflow.capability-grant.v1", alias="schema"
    )
    profile_id: Literal["conjecture-control.v1"] = "conjecture-control.v1"
    task_kind: Literal[WorkflowTaskKind.CONJECTURE] = WorkflowTaskKind.CONJECTURE
    allowed_outcomes: tuple[CapabilityOutcome, ...]
    max_candidates: int = Field(ge=0, le=256)
    max_provider_calls: Literal[1] = 1
    max_local_repairs: int = Field(ge=0, le=2)
    remaining_context_expansions: int = Field(ge=0, le=8)
    max_extra_context_blocks: int = Field(ge=0, le=1_000)
    permitted_retrieval_channels: tuple[RetrievalChannel, ...] = ()

    @field_validator("allowed_outcomes")
    @classmethod
    def _canonical_outcomes(cls, value):
        order = tuple(CapabilityOutcome)
        canonical = tuple(item for item in order if item in value)
        if tuple(value) != canonical or not value:
            raise ValueError("allowed outcomes must be nonempty, unique, and canonical")
        return tuple(value)

    @field_validator("permitted_retrieval_channels")
    @classmethod
    def _bounded_channels(cls, value):
        if len(value) != len(set(value)):
            raise ValueError("retrieval channels must not contain duplicates")
        if RetrievalChannel.DIRECT_OPEN in value:
            raise ValueError("direct_open is never a conjecture capability")
        return tuple(value)

    @model_validator(mode="after")
    def _context_allowance_is_consistent(self):
        permits_request = CapabilityOutcome.CONTEXT_REQUEST in self.allowed_outcomes
        if self.remaining_context_expansions and not permits_request:
            raise ValueError(
                "context expansions require the context_request capability"
            )
        if not permits_request and (
            self.max_extra_context_blocks or self.permitted_retrieval_channels
        ):
            raise ValueError("context limits require the context_request capability")
        if (
            permits_request
            and self.remaining_context_expansions
            and not self.max_extra_context_blocks
        ):
            raise ValueError("context requests require a positive extra-block limit")
        return self


class WorkOrderEnvelopeV1(IdentifiedWorkflowRecord):
    _identity_domain = "workflow.work-order-envelope.v1"

    schema_: Literal["workflow.work-order-envelope.v1"] = Field(
        "workflow.work-order-envelope.v1", alias="schema"
    )
    manifest_digest: str = Field(pattern=_DIGEST_PATTERN)
    controller_version: Literal["workflow.controller.v1"] = "workflow.controller.v1"
    workflow_profile: Literal["conjecture.shadow.v1", "conjecture.active.v1"]
    task_kind: Literal[WorkflowTaskKind.CONJECTURE] = WorkflowTaskKind.CONJECTURE
    formal_fence_seq: int = Field(ge=0)
    scratch_fence_seq: int = Field(ge=0)
    problem_ref: str = Field(min_length=1, max_length=512)
    target_refs: tuple[str, ...] = ()
    school_id: str | None = Field(
        default=None, pattern=r"^school-(0|[1-9][0-9]*)$"
    )
    route_lease: RouteLeaseRefV1
    contract_id: str = Field(min_length=1, max_length=512)
    input_refs: tuple[str, ...] = ()
    advisory_context_ref: str | None = None
    capability_grant: CapabilityGrantV1
    budget_reservation_ref: str | None = None
    repair_policy_ref: str = Field(pattern=_ID_PATTERN)
    task_payload_schema_id: str = Field(min_length=1, max_length=512)
    task_payload_ref: str | None = None
    task_payload_value: Any | None = None

    @field_validator("target_refs", "input_refs")
    @classmethod
    def _unique_refs(cls, value):
        if len(value) != len(set(value)):
            raise ValueError("workflow references must not contain duplicates")
        return tuple(value)

    @field_validator("task_payload_value", mode="before")
    @classmethod
    def _canonical_payload_value(cls, value):
        return None if value is None else freeze_workflow_json(value)

    @model_validator(mode="after")
    def _authority_shape(self):
        if self.formal_fence_seq != self.scratch_fence_seq:
            raise ValueError("conjecture work requires one formal/scratch state fence")
        if self.route_lease.role != "conjecturer":
            raise ValueError("conjecture work requires a conjecturer route lease")
        if self.capability_grant.task_kind != self.task_kind:
            raise ValueError("capability grant belongs to another task kind")
        if (self.task_payload_ref is None) == (self.task_payload_value is None):
            raise ValueError("work order requires exactly one task payload ref or value")
        return self


class RepairWorkOrderV1(IdentifiedWorkflowRecord):
    """One immutable authorization for the next local schema-repair attempt.

    A repair remains subordinate to its parent conjecture work order.  It may
    replace only ``authorized_subtree_pointer`` and cannot change the frozen
    contract, route, state fence, or local-repair policy.
    """

    _identity_domain = "workflow.repair-work-order.v1"

    schema_: Literal["workflow.repair-work-order.v1"] = Field(
        "workflow.repair-work-order.v1", alias="schema"
    )
    parent_work_order_id: str = Field(pattern=_ID_PATTERN)
    # Provider attempt zero is the original request.  Repair attempts are
    # therefore numbered one and two, matching the attempt they authorize.
    attempt: int = Field(ge=1, le=2)
    rejected_prompt_ref: str = Field(min_length=1, max_length=512)
    rejected_raw_ref: str = Field(min_length=1, max_length=512)
    rejected_diagnostic_ref: str = Field(min_length=1, max_length=512)
    validation_pointer: str = Field(default="", max_length=2_048)
    authorized_subtree_pointer: str = Field(default="", max_length=2_048)
    # Includes this authorized dispatch.  The value is captured before the
    # repair result consumes an allowance at provider settlement.
    remaining_local_attempts: int = Field(ge=1, le=2)
    contract_id: str = Field(min_length=1, max_length=512)
    route_lease: RouteLeaseRefV1
    formal_fence_seq: int = Field(ge=0)
    scratch_fence_seq: int = Field(ge=0)
    repair_policy_ref: str = Field(pattern=_ID_PATTERN)

    @field_validator("validation_pointer", "authorized_subtree_pointer")
    @classmethod
    def _canonical_pointer(cls, value: str) -> str:
        return _validate_json_pointer(value)

    @model_validator(mode="after")
    def _one_state_fence(self):
        if self.formal_fence_seq != self.scratch_fence_seq:
            raise ValueError("repair work requires one immutable state fence")
        return self


class ProposalReceiptV1(IdentifiedWorkflowRecord):
    _identity_domain = "workflow.proposal-receipt.v1"

    schema_: Literal["workflow.proposal-receipt.v1"] = Field(
        "workflow.proposal-receipt.v1", alias="schema"
    )
    work_order_id: str = Field(pattern=_ID_PATTERN)
    source_call_seq: int = Field(ge=0)
    prompt_ref: str = Field(min_length=1, max_length=512)
    raw_ref: str | None = Field(default=None, max_length=512)
    contract_id: str = Field(min_length=1, max_length=512)
    route_lease: RouteLeaseRefV1
    validation_outcome: ProposalValidationOutcome
    attempt_count: int = Field(ge=1, le=3)
    candidate_payload_refs: tuple[str, ...] = Field(default=(), max_length=256)
    context_request_hash: str | None = Field(default=None, pattern=_ID_PATTERN)
    context_request_ref: str | None = None
    abstention_hash: str | None = Field(default=None, pattern=_ID_PATTERN)
    abstention_ref: str | None = None
    tokens: int = Field(ge=0)

    @field_validator("candidate_payload_refs")
    @classmethod
    def _unique_candidates(cls, value):
        if len(value) != len(set(value)):
            raise ValueError("candidate payload references must be unique")
        return tuple(value)

    @model_validator(mode="after")
    def _proposal_shape(self):
        if (self.context_request_hash is None) != (self.context_request_ref is None):
            raise ValueError("context request hash and ref must appear together")
        if (self.abstention_hash is None) != (self.abstention_ref is None):
            raise ValueError("abstention hash and ref must appear together")
        if self.candidate_payload_refs and self.abstention_hash is not None:
            raise ValueError("candidate proposals cannot accompany abstention")
        valid = self.validation_outcome in {
            ProposalValidationOutcome.VALID_FIRST_ATTEMPT,
            ProposalValidationOutcome.VALID_AFTER_REPAIR,
        }
        if valid and self.raw_ref is None:
            raise ValueError("a valid proposal receipt requires a raw response ref")
        if not valid and (
            self.candidate_payload_refs
            or self.context_request_hash is not None
            or self.abstention_hash is not None
        ):
            raise ValueError("failed proposal receipts cannot carry semantic outcomes")
        if (
            self.validation_outcome == ProposalValidationOutcome.VALID_FIRST_ATTEMPT
            and self.attempt_count != 1
        ):
            raise ValueError("first-attempt validity requires exactly one attempt")
        if (
            self.validation_outcome == ProposalValidationOutcome.VALID_AFTER_REPAIR
            and self.attempt_count < 2
        ):
            raise ValueError("repaired validity requires more than one attempt")
        return self


class GuardFindingV1(WorkflowRecord):
    candidate_ref: str = Field(min_length=1, max_length=512)
    outcome: GuardFindingOutcome
    code: GuardFindingCode
    related_refs: tuple[str, ...] = ()
    detail: str | None = Field(default=None, max_length=8_192)

    @field_validator("related_refs")
    @classmethod
    def _unique_related_refs(cls, value):
        if len(value) != len(set(value)):
            raise ValueError("related guard references must be unique")
        return tuple(value)

    @model_validator(mode="after")
    def _code_matches_disposition(self):
        if (self.outcome == GuardFindingOutcome.ADMIT) != (
            self.code == GuardFindingCode.PASSED
        ):
            raise ValueError("only a passed code can admit a proposal")
        if (
            self.outcome == GuardFindingOutcome.DEDUPLICATE
            and self.code != GuardFindingCode.CONTENT_DUPLICATE
        ):
            raise ValueError("deduplication requires a content-duplicate code")
        return self


class GuardResultV1(IdentifiedWorkflowRecord):
    _identity_domain = "workflow.guard-result.v1"

    schema_: Literal["workflow.guard-result.v1"] = Field(
        "workflow.guard-result.v1", alias="schema"
    )
    work_order_id: str = Field(pattern=_ID_PATTERN)
    proposal_receipt_id: str = Field(pattern=_ID_PATTERN)
    guard_id: Literal["anti-relapse.v1"] = "anti-relapse.v1"
    findings: tuple[GuardFindingV1, ...] = Field(min_length=1)
    admitted_refs: tuple[str, ...] = ()
    rejected_refs: tuple[str, ...] = ()
    deduplicated_refs: tuple[str, ...] = ()

    @model_validator(mode="after")
    def _findings_are_complete(self):
        candidates = [finding.candidate_ref for finding in self.findings]
        if len(candidates) != len(set(candidates)):
            raise ValueError("guard findings must name every candidate once")
        classified = {
            GuardFindingOutcome.ADMIT: tuple(self.admitted_refs),
            GuardFindingOutcome.REJECT: tuple(self.rejected_refs),
            GuardFindingOutcome.DEDUPLICATE: tuple(self.deduplicated_refs),
        }
        flattened = [item for values in classified.values() for item in values]
        if len(flattened) != len(set(flattened)) or set(flattened) != set(candidates):
            raise ValueError("guard result classifications must partition its findings")
        for outcome, refs in classified.items():
            expected = tuple(
                finding.candidate_ref
                for finding in self.findings
                if finding.outcome == outcome
            )
            if tuple(refs) != expected:
                raise ValueError("guard result order differs from its findings")
        return self


class TransitionDecisionV1(IdentifiedWorkflowRecord):
    _identity_domain = "workflow.transition-decision.v1"

    schema_: Literal["workflow.transition-decision.v1"] = Field(
        "workflow.transition-decision.v1", alias="schema"
    )
    manifest_digest: str = Field(pattern=_DIGEST_PATTERN)
    controller_version: Literal["workflow.controller.v1"] = "workflow.controller.v1"
    workflow_profile: Literal["conjecture.shadow.v1", "conjecture.active.v1"]
    previous_process_digest: str = Field(pattern=_ID_PATTERN)
    trigger_kind: TriggerKind
    trigger_ref: str = Field(min_length=1, max_length=512)
    transition_kind: TransitionKind
    work_order_id: str = Field(pattern=_ID_PATTERN)
    route_lease: RouteLeaseRefV1
    budget_delta: BudgetDeltaV1 = Field(default_factory=BudgetDeltaV1)
    # Replay-visible consumption of non-budget capability allowances.  These
    # are deltas, not caller-authored limits: the reducer derives them from a
    # validated provider receipt or context decision and checks them against
    # the immutable work-order grant before creating the transition.
    provider_call_delta: int = Field(default=0, ge=0, le=1)
    local_repair_delta: int = Field(default=0, ge=0, le=2)
    context_expansion_delta: int = Field(default=0, ge=0, le=1)
    guard_result_ref: str | None = Field(default=None, pattern=_ID_PATTERN)
    output_refs: tuple[str, ...] = ()
    next_process_digest: str = Field(pattern=_ID_PATTERN)

    @field_validator("output_refs")
    @classmethod
    def _unique_output_refs(cls, value):
        if len(value) != len(set(value)):
            raise ValueError("transition output references must be unique")
        return tuple(value)

    @model_validator(mode="after")
    def _guard_authorizes_admission(self):
        expected_trigger = {
            TransitionKind.WORK_ENABLED: TriggerKind.PROBLEM_SELECTED,
            TransitionKind.WORK_ISSUED: TriggerKind.CONTEXT_PREPARED,
            TransitionKind.PROPOSAL_RECEIVED: TriggerKind.PROVIDER_RESULT,
            TransitionKind.PROPOSAL_ADMITTED: TriggerKind.GUARD_RESULT,
            TransitionKind.PROPOSAL_REJECTED: TriggerKind.GUARD_RESULT,
            TransitionKind.PROPOSAL_DEDUPLICATED: TriggerKind.GUARD_RESULT,
            TransitionKind.REPAIR_REQUESTED: TriggerKind.REPAIR_DECISION,
            TransitionKind.REPAIR_EXHAUSTED: TriggerKind.PROVIDER_RESULT,
            TransitionKind.CONTEXT_REQUESTED: TriggerKind.PROVIDER_RESULT,
            TransitionKind.CONTEXT_GRANTED: TriggerKind.CONTEXT_DECISION,
            TransitionKind.CONTEXT_DENIED: TriggerKind.CONTEXT_DECISION,
            TransitionKind.WORK_FINISHED: TriggerKind.PROVIDER_RESULT,
            TransitionKind.WORK_ABANDONED: TriggerKind.WORKFLOW_TERMINATION,
        }[self.transition_kind]
        if self.trigger_kind != expected_trigger:
            raise ValueError("transition kind requires its canonical trigger kind")
        guarded = self.transition_kind in {
            TransitionKind.PROPOSAL_ADMITTED,
            TransitionKind.PROPOSAL_REJECTED,
            TransitionKind.PROPOSAL_DEDUPLICATED,
        }
        if guarded != (self.guard_result_ref is not None):
            raise ValueError("proposal disposition requires exactly one guard result")
        provider_result = self.transition_kind in {
            TransitionKind.PROPOSAL_RECEIVED,
            TransitionKind.REPAIR_EXHAUSTED,
        }
        if self.provider_call_delta != int(provider_result):
            raise ValueError(
                "provider-result transitions consume exactly one provider call"
            )
        if self.local_repair_delta and not provider_result:
            raise ValueError(
                "only provider-result transitions consume local repairs"
            )
        context_granted = self.transition_kind == TransitionKind.CONTEXT_GRANTED
        if self.context_expansion_delta != int(context_granted):
            raise ValueError(
                "context-granted transitions consume exactly one expansion"
            )
        carries_outputs = provider_result or guarded
        if self.output_refs and not carries_outputs:
            raise ValueError("only provider and guard transitions carry outputs")
        return self


class WorkflowStopDecisionV1(IdentifiedWorkflowRecord):
    _identity_domain = "workflow.stop-decision.v1"

    schema_: Literal["workflow.stop-decision.v1"] = Field(
        "workflow.stop-decision.v1", alias="schema"
    )
    manifest_digest: str = Field(pattern=_DIGEST_PATTERN)
    workflow_profile: Literal["conjecture.shadow.v1", "conjecture.active.v1"]
    deterministic_decision: StopDecision
    policy_digest: str = Field(pattern=_DIGEST_PATTERN)
    metrics_ref: str = Field(min_length=1, max_length=512)
    previous_process_digest: str = Field(pattern=_ID_PATTERN)
    next_process_digest: str = Field(pattern=_ID_PATTERN)


__all__ = [
    "BudgetDeltaV1",
    "CapabilityGrantV1",
    "CapabilityOutcome",
    "GuardFindingCode",
    "GuardFindingOutcome",
    "GuardFindingV1",
    "GuardResultV1",
    "IdentifiedWorkflowRecord",
    "LocalRepairPolicyV1",
    "ProposalReceiptV1",
    "ProposalValidationOutcome",
    "RepairWorkOrderV1",
    "RouteLeaseRefV1",
    "TransitionDecisionV1",
    "TransitionKind",
    "TriggerKind",
    "WorkflowRecord",
    "WorkflowStopDecisionV1",
    "WorkflowTaskKind",
    "WorkOrderEnvelopeV1",
    "freeze_workflow_json",
    "repair_attempt_trigger_ref",
]
