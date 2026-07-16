"""Replay-only materialization for durable workflow authority transitions."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Iterable, Mapping

from pydantic import BaseModel

from deepreason.canonical import canonical_json, sha256_hex
from deepreason.control_events import ControlEventPayloadV1
from deepreason.workflow.models import (
    CapabilityOutcome,
    GuardFindingOutcome,
    GuardResultV1,
    ProposalReceiptV1,
    ProposalValidationOutcome,
    TransitionDecisionV1,
    TransitionKind,
    WorkOrderEnvelopeV1,
    repair_attempt_trigger_ref,
)
from deepreason.workflow.state import (
    WorkItemStatus,
    WorkflowProcessStateV1,
    apply_decision,
)


_SCHEMA_MODELS = {
    "workflow-work-order": WorkOrderEnvelopeV1,
    "workflow-proposal-receipt": ProposalReceiptV1,
    "workflow-guard-result": GuardResultV1,
    "workflow-transition-decision": TransitionDecisionV1,
}
_PROVIDER_TRANSITIONS = {
    TransitionKind.PROPOSAL_RECEIVED,
    TransitionKind.REPAIR_EXHAUSTED,
}
_VALID_PROPOSAL_OUTCOMES = {
    ProposalValidationOutcome.VALID_FIRST_ATTEMPT,
    ProposalValidationOutcome.VALID_AFTER_REPAIR,
}
_FAILED_PROPOSAL_OUTCOMES = {
    ProposalValidationOutcome.REPAIR_EXHAUSTED,
    ProposalValidationOutcome.TRANSPORT_FAILED,
}
_GUARDED_TRANSITIONS = {
    TransitionKind.PROPOSAL_ADMITTED,
    TransitionKind.PROPOSAL_REJECTED,
    TransitionKind.PROPOSAL_DEDUPLICATED,
}


class WorkflowRecoveryStatus(str, Enum):
    ENABLED = "enabled"
    ISSUED = "issued"
    PROVIDER_RESULT_RECEIVED = "provider_result_received"
    REPAIR_PENDING = "repair_pending"
    CONTEXT_PENDING = "context_pending"
    FINISHED = "finished"
    ABANDONED = "abandoned"


@dataclass
class WorkflowBranchState:
    branch_id: str
    process_state: WorkflowProcessStateV1
    work_order_ids: list[str] = field(default_factory=list)
    decision_ids: list[str] = field(default_factory=list)
    event_seqs: list[int] = field(default_factory=list)


@dataclass(frozen=True)
class _PlannedApply:
    decision: TransitionDecisionV1
    work_order: WorkOrderEnvelopeV1
    proposal: ProposalReceiptV1 | None
    guard: GuardResultV1 | None
    branch_id: str
    next_state: WorkflowProcessStateV1
    new_branch: bool


def _canonical(model_type, value):
    payload = (
        value.model_dump(mode="python", by_alias=True)
        if isinstance(value, BaseModel)
        else value
    )
    return model_type.model_validate(payload)


def _record_map(
    records: Iterable[tuple[str, str, BaseModel]],
) -> dict[str, tuple[str, BaseModel]]:
    result: dict[str, tuple[str, BaseModel]] = {}
    for schema, object_id, value in records:
        if schema not in _SCHEMA_MODELS:
            raise ValueError(f"control event uses non-workflow schema {schema!r}")
        normalized = _canonical(_SCHEMA_MODELS[schema], value)
        if normalized.id != object_id:
            raise ValueError("resolved workflow object ID differs from its record")
        if object_id in result:
            raise ValueError("control event resolves one object ID more than once")
        result[object_id] = (schema, normalized)
    return result


def _call_index(values: Any) -> dict[int, Any]:
    if isinstance(values, Mapping):
        return {int(seq): call for seq, call in values.items()}
    indexed: dict[int, Any] = {}
    for value in values:
        if isinstance(value, tuple) and len(value) == 2:
            seq, call = value
        else:
            seq, call = getattr(value, "seq", None), getattr(value, "llm", None)
        if seq is not None and call is not None:
            indexed[int(seq)] = call
    return indexed


def _guard_transition(
    guard: GuardResultV1,
) -> tuple[TransitionKind, tuple[str, ...]]:
    outcomes = {finding.outcome for finding in guard.findings}
    if GuardFindingOutcome.ADMIT in outcomes:
        return TransitionKind.PROPOSAL_ADMITTED, guard.admitted_refs
    if GuardFindingOutcome.REJECT in outcomes:
        return TransitionKind.PROPOSAL_REJECTED, guard.rejected_refs
    return TransitionKind.PROPOSAL_DEDUPLICATED, guard.deduplicated_refs


@dataclass
class WorkflowReplayState:
    """Deterministic process-only index reconstructed from ``Control`` events."""

    work_orders: dict[str, WorkOrderEnvelopeV1] = field(default_factory=dict)
    proposal_receipts: dict[str, ProposalReceiptV1] = field(default_factory=dict)
    guard_results: dict[str, GuardResultV1] = field(default_factory=dict)
    decisions: dict[str, TransitionDecisionV1] = field(default_factory=dict)
    branches: dict[str, WorkflowBranchState] = field(default_factory=dict)
    work_to_branch: dict[str, str] = field(default_factory=dict)
    decision_event_seq: dict[str, int] = field(default_factory=dict)
    calls_by_seq: dict[int, Any] = field(default_factory=dict)
    event_seqs: list[int] = field(default_factory=list)

    def observe_event(self, event: Any) -> None:
        """Index a preceding work-bound provider call without mutating authority."""

        call = getattr(event, "llm", None)
        seq = getattr(event, "seq", None)
        if call is None or seq is None or getattr(call, "work_order_id", None) is None:
            return
        seq = int(seq)
        if seq in self.calls_by_seq:
            raise ValueError("workflow provider-call sequence appears more than once")
        work_id = call.work_order_id
        work = self.work_orders.get(work_id)
        if work is None:
            raise ValueError("provider call names an unknown work order")
        branch_id = self.work_to_branch[work_id]
        item = self.branches[branch_id].process_state.work_item(work_id)
        if item is None or item.status not in {
            WorkItemStatus.ISSUED,
            WorkItemStatus.REPAIR_PENDING,
        }:
            raise ValueError("provider call was not preceded by issued work")
        bound_calls = sum(
            prior.work_order_id == work_id
            for prior in self.calls_by_seq.values()
        )
        if bound_calls >= work.capability_grant.max_provider_calls:
            raise ValueError("provider-call capability is already exhausted")
        self.calls_by_seq[seq] = call

    def _branch_for(
        self,
        decision: TransitionDecisionV1,
        work_order: WorkOrderEnvelopeV1 | None,
    ) -> tuple[str, WorkflowProcessStateV1, bool]:
        known = self.work_to_branch.get(decision.work_order_id)
        if known is not None:
            if decision.transition_kind == TransitionKind.WORK_ENABLED:
                raise ValueError("duplicate work-order enable transition")
            return known, self.branches[known].process_state, False
        if decision.transition_kind != TransitionKind.WORK_ENABLED or work_order is None:
            raise ValueError("unknown work order must begin with work_enabled")

        matches = [
            branch_id
            for branch_id, branch in self.branches.items()
            if branch.process_state.digest == decision.previous_process_digest
        ]
        if len(matches) > 1:
            raise ValueError("work-order branch is ambiguous at its state digest")
        if matches:
            return matches[0], self.branches[matches[0]].process_state, False
        initial = WorkflowProcessStateV1.initial(
            manifest_digest=work_order.manifest_digest,
            workflow_profile=work_order.workflow_profile,
            formal_fence_seq=work_order.formal_fence_seq,
            scratch_fence_seq=work_order.scratch_fence_seq,
        )
        if initial.digest != decision.previous_process_digest:
            raise ValueError("work-enabled decision does not begin at its declared fence")
        return work_order.id, initial, True

    @staticmethod
    def _validate_work_decision(
        work: WorkOrderEnvelopeV1,
        decision: TransitionDecisionV1,
        state: WorkflowProcessStateV1,
    ) -> None:
        if (
            decision.work_order_id != work.id
            or decision.route_lease != work.route_lease
            or decision.manifest_digest != work.manifest_digest
            or decision.workflow_profile != work.workflow_profile
        ):
            raise ValueError("transition decision differs from its work-order authority")
        if (
            state.manifest_digest != work.manifest_digest
            or state.workflow_profile != work.workflow_profile
            or state.formal_fence_seq != work.formal_fence_seq
            or state.scratch_fence_seq != work.scratch_fence_seq
        ):
            raise ValueError("work order belongs to another replay branch")
        if (
            decision.transition_kind == TransitionKind.WORK_ENABLED
            and decision.trigger_ref != work.problem_ref
        ):
            raise ValueError("work-enabled trigger differs from its selected problem")
        if (
            decision.transition_kind == TransitionKind.WORK_ISSUED
            and decision.trigger_ref
            != (work.advisory_context_ref or work.id)
        ):
            raise ValueError("work-issued trigger differs from its prepared context")
        if state.selected_problem_ref not in {None, work.problem_ref}:
            raise ValueError("work order differs from the branch selected problem")
        current = state.work_item(work.id)
        grant = work.capability_grant
        budget = decision.budget_delta
        if decision.transition_kind == TransitionKind.WORK_ISSUED:
            if budget.spent_tokens or budget.released_tokens:
                raise ValueError("work issuance may only reserve tokens")
        elif decision.transition_kind in _PROVIDER_TRANSITIONS:
            # Exact provider settlement is checked against its receipt below.
            pass
        elif decision.transition_kind in {
            TransitionKind.WORK_FINISHED,
            TransitionKind.WORK_ABANDONED,
        }:
            expected_release = current.reserved_tokens if current is not None else 0
            if (
                budget.reserved_tokens
                or budget.spent_tokens
                or budget.released_tokens != expected_release
            ):
                raise ValueError("work completion has an invalid budget release")
        elif any(budget.model_dump(mode="json").values()):
            raise ValueError("transition cannot change token budget state")
        if (
            decision.transition_kind == TransitionKind.CONTEXT_REQUESTED
            and CapabilityOutcome.CONTEXT_REQUEST not in grant.allowed_outcomes
        ):
            raise ValueError("work order does not grant context-request authority")
        if (
            decision.transition_kind == TransitionKind.CONTEXT_GRANTED
            and CapabilityOutcome.CONTEXT_REQUEST not in grant.allowed_outcomes
        ):
            raise ValueError("work order does not grant context-expansion authority")
        if (
            decision.transition_kind == TransitionKind.REPAIR_REQUESTED
            and (
                current is None
                or current.local_repairs_used >= grant.max_local_repairs
            )
        ):
            raise ValueError("work order has exhausted local-repair authority")
        calls = (current.provider_calls_used if current else 0) + (
            decision.provider_call_delta
        )
        repairs = (current.local_repairs_used if current else 0) + (
            decision.local_repair_delta
        )
        contexts = (current.context_expansions_used if current else 0) + (
            decision.context_expansion_delta
        )
        if calls > grant.max_provider_calls:
            raise ValueError("transition exceeds provider-call capability")
        if repairs > grant.max_local_repairs:
            raise ValueError("transition exceeds local-repair capability")
        if contexts > grant.remaining_context_expansions:
            raise ValueError("transition exceeds context-expansion capability")

    @staticmethod
    def _validate_observed_call_capability(
        work: WorkOrderEnvelopeV1,
        decision: TransitionDecisionV1,
        prior_calls: Any,
        event_seq: int | None,
    ) -> None:
        if prior_calls is None:
            return
        calls = _call_index(prior_calls)
        bound_count = sum(
            getattr(call, "work_order_id", None) == work.id
            and (event_seq is None or seq < event_seq)
            for seq, call in calls.items()
        )
        if decision.transition_kind == TransitionKind.WORK_ENABLED and bound_count:
            raise ValueError("provider call predates its work-order authority")
        if bound_count > work.capability_grant.max_provider_calls:
            raise ValueError("preceding calls exceed provider-call capability")

    def _validate_proposal(
        self,
        work: WorkOrderEnvelopeV1,
        decision: TransitionDecisionV1,
        proposal: ProposalReceiptV1,
        state: WorkflowProcessStateV1,
        prior_calls: Any,
        event_seq: int | None,
    ) -> None:
        if (
            proposal.id != decision.trigger_ref
            or proposal.work_order_id != work.id
            or proposal.route_lease != work.route_lease
            or proposal.contract_id != work.contract_id
            or tuple(proposal.candidate_payload_refs) != tuple(decision.output_refs)
        ):
            raise ValueError("proposal receipt differs from its transition authority")
        if len(proposal.candidate_payload_refs) > work.capability_grant.max_candidates:
            raise ValueError("proposal exceeds its candidate capability")
        allowed = work.capability_grant.allowed_outcomes
        if (
            proposal.candidate_payload_refs
            and CapabilityOutcome.CANDIDATE_PROPOSAL not in allowed
        ):
            raise ValueError("proposal exceeds its candidate capability")
        if (
            proposal.context_request_ref is not None
            and CapabilityOutcome.CONTEXT_REQUEST not in allowed
        ):
            raise ValueError("proposal exceeds its context-request capability")
        if (
            proposal.abstention_ref is not None
            and CapabilityOutcome.ABSTENTION not in allowed
        ):
            raise ValueError("proposal exceeds its abstention capability")
        outcome = proposal.validation_outcome
        if (
            decision.transition_kind == TransitionKind.PROPOSAL_RECEIVED
            and outcome not in _VALID_PROPOSAL_OUTCOMES
        ) or (
            decision.transition_kind == TransitionKind.REPAIR_EXHAUSTED
            and outcome not in _FAILED_PROPOSAL_OUTCOMES
        ):
            raise ValueError(
                "proposal validation outcome differs from its provider transition"
            )
        expected_repair_delta = proposal.attempt_count - 1
        if decision.local_repair_delta != expected_repair_delta:
            label = (
                "valid-after-repair receipt"
                if outcome == ProposalValidationOutcome.VALID_AFTER_REPAIR
                else "proposal receipt"
            )
            raise ValueError(
                f"{label} attempt count differs from local-repair consumption"
            )
        current = state.work_item(work.id)
        if current is None:
            raise ValueError("proposal receipt belongs to work that was not issued")
        expected_reserved = max(0, proposal.tokens - current.reserved_tokens)
        expected_released = max(0, current.reserved_tokens - proposal.tokens)
        delta = decision.budget_delta
        if (
            delta.reserved_tokens != expected_reserved
            or delta.spent_tokens != proposal.tokens
            or delta.released_tokens != expected_released
        ):
            raise ValueError("proposal budget settlement differs from issued work")

        if prior_calls is None:
            return
        calls = _call_index(prior_calls)
        preceding_bound_calls = {
            seq: call
            for seq, call in calls.items()
            if getattr(call, "work_order_id", None) == work.id
            and (event_seq is None or seq < event_seq)
        }
        consumed_call_seqs = {
            receipt.source_call_seq
            for receipt in self.proposal_receipts.values()
            if receipt.work_order_id == work.id
        }
        if len(consumed_call_seqs) != current.provider_calls_used:
            raise ValueError(
                "provider-call receipts differ from process-state consumption"
            )
        newly_consumed = set(preceding_bound_calls) - consumed_call_seqs
        if (
            not consumed_call_seqs.issubset(preceding_bound_calls)
            or len(preceding_bound_calls)
            != current.provider_calls_used + decision.provider_call_delta
            or newly_consumed != {proposal.source_call_seq}
        ):
            raise ValueError(
                "provider call transition must consume exactly its preceding source call"
            )
        call = calls.get(proposal.source_call_seq)
        if call is None:
            raise ValueError("proposal receipt has no preceding provider call")
        if event_seq is not None and proposal.source_call_seq >= event_seq:
            raise ValueError("proposal receipt points to a non-preceding provider call")
        trace = tuple(getattr(call, "attempt_trace", ()))
        if (
            getattr(call, "role", None) != "conjecturer"
            or getattr(call, "work_order_id", None) != work.id
            or getattr(call, "prompt_ref", None) != proposal.prompt_ref
            or (getattr(call, "raw_ref", None) or None) != proposal.raw_ref
            or int(getattr(call, "tokens", -1)) != proposal.tokens
            or int(getattr(call, "attempts", -1)) != proposal.attempt_count
            or not trace
        ):
            raise ValueError("proposal receipt differs from its provider call")
        repair_triggers = tuple(
            prior.trigger_ref
            for prior in self.decisions.values()
            if prior.work_order_id == work.id
            and prior.transition_kind == TransitionKind.REPAIR_REQUESTED
        )
        expected_repair_triggers = tuple(
            repair_attempt_trigger_ref(
                int(getattr(attempt, "attempt", -1)),
                getattr(attempt, "diagnostic_ref", ""),
            )
            for attempt in trace[:-1]
        )
        if (
            not all(expected_repair_triggers)
            or repair_triggers != expected_repair_triggers
        ):
            raise ValueError(
                "repair requests differ from provider attempt diagnostics"
            )
        school_receipt = getattr(call, "school_route", None)
        if work.school_id is None:
            if school_receipt is not None:
                raise ValueError("provider call adds an unauthorized school route")
        elif (
            school_receipt is None
            or school_receipt.school_id != work.school_id
            or school_receipt.role != "conjecturer"
            or school_receipt.seat != work.route_lease.seat
            or school_receipt.endpoint_id != work.route_lease.endpoint_id
            or school_receipt.route_sha256 != work.route_lease.route_sha256
            or school_receipt.contract_id != work.contract_id
        ):
            raise ValueError("provider call differs from its school authority")
        context_receipt = getattr(call, "conjecture_context", None)
        if work.advisory_context_ref is None:
            if context_receipt is not None:
                raise ValueError("provider call adds unauthorized advisory context")
        elif (
            context_receipt is None
            or context_receipt.manifest_digest != work.manifest_digest
            or context_receipt.problem_id != work.problem_ref
            or context_receipt.school_id != work.school_id
            or context_receipt.formal_fence_seq != work.formal_fence_seq
            or context_receipt.scratch_fence_seq != work.scratch_fence_seq
            or context_receipt.advisory_context_ref != work.advisory_context_ref
        ):
            raise ValueError("provider call differs from its advisory-context authority")
        if len(trace) != proposal.attempt_count:
            raise ValueError("proposal attempt count differs from its attempt trace")
        if tuple(attempt.attempt for attempt in trace) != tuple(range(len(trace))):
            raise ValueError("proposal attempt trace has non-canonical indices")
        if any(attempt.usage_unknown and attempt.tokens for attempt in trace):
            raise ValueError("attempt with unknown usage must record zero tokens")
        known_trace_tokens = sum(
            attempt.tokens for attempt in trace if not attempt.usage_unknown
        )
        if known_trace_tokens != call.tokens:
            raise ValueError("provider-call spend differs from attempt-trace token total")
        if any(attempt.usage_unknown and attempt.valid for attempt in trace):
            raise ValueError("attempt with unknown usage cannot be valid")
        if outcome in _VALID_PROPOSAL_OUTCOMES:
            if not trace[-1].valid or any(attempt.valid for attempt in trace[:-1]):
                raise ValueError(
                    "valid proposal outcome differs from attempt-trace validity"
                )
        elif any(attempt.valid for attempt in trace):
            raise ValueError("failed proposal outcome differs from attempt-trace validity")
        has_unknown_usage = any(attempt.usage_unknown for attempt in trace)
        if (
            outcome == ProposalValidationOutcome.TRANSPORT_FAILED
            and not has_unknown_usage
        ) or (
            outcome == ProposalValidationOutcome.REPAIR_EXHAUSTED
            and has_unknown_usage
        ):
            raise ValueError(
                "failed proposal outcome differs from attempt usage evidence"
            )
        if any(
            attempt.contract_id != work.contract_id
            or attempt.seat != work.route_lease.seat
            or attempt.endpoint_id != work.route_lease.endpoint_id
            or attempt.route_sha256 != work.route_lease.route_sha256
            for attempt in trace
        ):
            raise ValueError("proposal provider call differs from its route authority")

    def _validate_guard(
        self,
        work: WorkOrderEnvelopeV1,
        decision: TransitionDecisionV1,
        guard: GuardResultV1,
    ) -> None:
        proposal = self.proposal_receipts.get(guard.proposal_receipt_id)
        if (
            guard.id != decision.trigger_ref
            or guard.id != decision.guard_result_ref
            or guard.work_order_id != work.id
            or proposal is None
            or proposal.work_order_id != work.id
            or {item.candidate_ref for item in guard.findings}
            != set(proposal.candidate_payload_refs)
        ):
            raise ValueError("guard result differs from its proposal authority")
        expected_kind, expected_outputs = _guard_transition(guard)
        if (
            decision.transition_kind != expected_kind
            or tuple(decision.output_refs) != tuple(expected_outputs)
        ):
            raise ValueError("guard disposition differs from its transition decision")

    def _validate_context_request(
        self,
        work: WorkOrderEnvelopeV1,
        decision: TransitionDecisionV1,
        state: WorkflowProcessStateV1,
    ) -> None:
        if decision.transition_kind != TransitionKind.CONTEXT_REQUESTED:
            return
        current = state.work_item(work.id)
        proposal = (
            self.proposal_receipts.get(current.proposal_receipt_id)
            if current is not None and current.proposal_receipt_id is not None
            else None
        )
        if (
            proposal is None
            or proposal.context_request_hash is None
            or proposal.context_request_ref is None
            or decision.trigger_ref != proposal.context_request_hash
        ):
            raise ValueError(
                "context-request trigger differs from its stored proposal receipt"
            )

    def _validate_context_decision(
        self,
        work: WorkOrderEnvelopeV1,
        decision: TransitionDecisionV1,
        state: WorkflowProcessStateV1,
    ) -> None:
        if decision.transition_kind not in {
            TransitionKind.CONTEXT_GRANTED,
            TransitionKind.CONTEXT_DENIED,
        }:
            return
        current = state.work_item(work.id)
        proposal = (
            self.proposal_receipts.get(current.proposal_receipt_id)
            if current is not None and current.proposal_receipt_id is not None
            else None
        )
        if (
            current is None
            or current.status != WorkItemStatus.CONTEXT_PENDING
            or proposal is None
            or proposal.context_request_hash is None
            or proposal.context_request_ref is None
        ):
            raise ValueError("context decision has no pending stored request")
        if not (
            decision.trigger_ref.startswith("sha256:")
            and len(decision.trigger_ref) == 71
        ):
            raise ValueError("context decision requires a canonical decision reference")

    def _validate_follow_up_work(self, work: WorkOrderEnvelopeV1) -> None:
        parent_ref = work.input_refs[-1] if work.input_refs else None
        parent = self.work_orders.get(parent_ref) if parent_ref is not None else None
        if parent is None:
            return
        parent_branch = self.branches[self.work_to_branch[parent.id]]
        parent_item = parent_branch.process_state.work_item(parent.id)
        if parent_item is None or parent_item.status != WorkItemStatus.FINISHED:
            raise ValueError("context follow-up predates closure of its parent work")
        grants = [
            prior
            for prior in self.decisions.values()
            if prior.work_order_id == parent.id
            and prior.transition_kind == TransitionKind.CONTEXT_GRANTED
        ]
        if len(grants) != 1:
            raise ValueError("context follow-up requires one parent grant")
        parent_grant = parent.capability_grant
        expected_remaining = parent_grant.remaining_context_expansions - 1
        child_grant = work.capability_grant
        if expected_remaining < 0 or (
            child_grant.remaining_context_expansions != expected_remaining
            or child_grant.max_candidates != parent_grant.max_candidates
            or child_grant.max_local_repairs != parent_grant.max_local_repairs
        ):
            raise ValueError("context follow-up does not reduce parent capability")
        expected_inputs = tuple(dict.fromkeys((*parent.input_refs, parent.id)))
        if (
            work.id == parent.id
            or work.input_refs != expected_inputs
            or work.advisory_context_ref is None
            or work.advisory_context_ref == parent.advisory_context_ref
            or work.problem_ref != parent.problem_ref
            or work.school_id != parent.school_id
            or work.route_lease != parent.route_lease
            or work.contract_id != parent.contract_id
            or work.manifest_digest != parent.manifest_digest
            or work.workflow_profile != parent.workflow_profile
            or work.repair_policy_ref != parent.repair_policy_ref
            or work.task_payload_schema_id != parent.task_payload_schema_id
            or work.task_payload_ref != parent.task_payload_ref
            or work.task_payload_value != parent.task_payload_value
        ):
            raise ValueError("context follow-up differs from its parent authority")

    def _plan(
        self,
        payload: ControlEventPayloadV1,
        resolved_records: Iterable[tuple[str, str, BaseModel]],
        *,
        prior_calls: Any = None,
        event_seq: int | None = None,
    ) -> _PlannedApply:
        payload = _canonical(ControlEventPayloadV1, payload)
        records = _record_map(resolved_records)
        if tuple(records) != tuple(payload.outputs):
            raise ValueError("resolved workflow records differ from control outputs")
        decision_entry = records.get(payload.decision_ref)
        if decision_entry is None or decision_entry[0] != "workflow-transition-decision":
            raise ValueError("control decision_ref does not name one transition decision")
        decision = decision_entry[1]
        assert isinstance(decision, TransitionDecisionV1)
        if decision.id in self.decisions:
            raise ValueError("duplicate transition decision")
        if tuple(payload.inputs) != (decision.work_order_id, decision.trigger_ref):
            raise ValueError("control inputs differ from transition decision")

        supplied_work = next(
            (
                value
                for schema, value in records.values()
                if schema == "workflow-work-order"
            ),
            None,
        )
        if supplied_work is not None and not isinstance(supplied_work, WorkOrderEnvelopeV1):
            raise TypeError("workflow work-order record has the wrong model")
        work = supplied_work or self.work_orders.get(decision.work_order_id)
        if work is None:
            raise ValueError("transition decision names an unknown work order")
        if supplied_work is not None and supplied_work.id != decision.work_order_id:
            raise ValueError("control event supplies another work order")
        if (
            supplied_work is not None
            and decision.transition_kind == TransitionKind.WORK_ENABLED
        ):
            self._validate_follow_up_work(supplied_work)

        expected_schemas = ["workflow-transition-decision"]
        if decision.transition_kind == TransitionKind.WORK_ENABLED:
            expected_schemas.insert(0, "workflow-work-order")
        proposal = next(
            (
                value
                for schema, value in records.values()
                if schema == "workflow-proposal-receipt"
            ),
            None,
        )
        if decision.transition_kind in _PROVIDER_TRANSITIONS:
            expected_schemas.insert(0, "workflow-proposal-receipt")
            if not isinstance(proposal, ProposalReceiptV1):
                raise ValueError("provider-result transition requires one proposal receipt")
        guard = next(
            (
                value
                for schema, value in records.values()
                if schema == "workflow-guard-result"
            ),
            None,
        )
        if decision.transition_kind in _GUARDED_TRANSITIONS:
            expected_schemas.insert(0, "workflow-guard-result")
            if not isinstance(guard, GuardResultV1):
                raise ValueError("guarded transition requires one guard result")
        actual_schemas = [schema for schema, _value in records.values()]
        if actual_schemas != expected_schemas:
            raise ValueError("control outputs have the wrong transition record shape")

        branch_id, state, new_branch = self._branch_for(decision, supplied_work)
        prior_repair_requests = sum(
            prior.work_order_id == work.id
            and prior.transition_kind == TransitionKind.REPAIR_REQUESTED
            for prior in self.decisions.values()
        )
        if decision.transition_kind == TransitionKind.REPAIR_REQUESTED:
            if prior_repair_requests >= work.capability_grant.max_local_repairs:
                raise ValueError("work order has exhausted local-repair authority")
            if any(
                prior.work_order_id == work.id
                and prior.transition_kind == TransitionKind.REPAIR_REQUESTED
                and prior.trigger_ref == decision.trigger_ref
                for prior in self.decisions.values()
            ):
                raise ValueError("repair diagnostic was already consumed")
        if (
            proposal is not None
            and proposal.attempt_count - 1 != prior_repair_requests
        ):
            raise ValueError(
                "proposal attempts differ from durable repair-request authority"
            )
        self._validate_work_decision(work, decision, state)
        self._validate_context_request(work, decision, state)
        self._validate_context_decision(work, decision, state)
        self._validate_observed_call_capability(
            work,
            decision,
            prior_calls,
            event_seq,
        )
        if proposal is not None:
            self._validate_proposal(
                work,
                decision,
                proposal,
                state,
                prior_calls,
                event_seq,
            )
        if guard is not None:
            self._validate_guard(work, decision, guard)
        next_state = apply_decision(state, decision)
        return _PlannedApply(
            decision=decision,
            work_order=work,
            proposal=proposal,
            guard=guard,
            branch_id=branch_id,
            next_state=next_state,
            new_branch=new_branch,
        )

    def validate(
        self,
        payload: ControlEventPayloadV1,
        resolved_records: Iterable[tuple[str, str, BaseModel]],
        *,
        prior_calls: Any = None,
        event_seq: int | None = None,
    ) -> None:
        self._plan(
            payload,
            resolved_records,
            prior_calls=prior_calls,
            event_seq=event_seq,
        )

    def apply(
        self,
        event: Any,
        resolved_records: Iterable[tuple[str, str, BaseModel]],
        *,
        prior_calls: Any = None,
    ) -> None:
        payload = getattr(event, "control", None)
        if payload is None:
            raise ValueError("workflow replay accepts only typed control events")
        seq = int(getattr(event, "seq"))
        planned = self._plan(
            payload,
            resolved_records,
            prior_calls=(self.calls_by_seq if prior_calls is None else prior_calls),
            event_seq=seq,
        )
        decision = planned.decision
        work = planned.work_order
        if planned.new_branch:
            self.branches[planned.branch_id] = WorkflowBranchState(
                branch_id=planned.branch_id,
                process_state=planned.next_state,
            )
        branch = self.branches[planned.branch_id]
        branch.process_state = planned.next_state
        if work.id not in branch.work_order_ids:
            branch.work_order_ids.append(work.id)
        branch.decision_ids.append(decision.id)
        branch.event_seqs.append(seq)
        self.work_orders.setdefault(work.id, work)
        self.work_to_branch[work.id] = planned.branch_id
        self.decisions[decision.id] = decision
        self.decision_event_seq[decision.id] = seq
        if planned.proposal is not None:
            self.proposal_receipts[planned.proposal.id] = planned.proposal
        if planned.guard is not None:
            self.guard_results[planned.guard.id] = planned.guard
        self.event_seqs.append(seq)

    @property
    def outstanding_work_order_ids(self) -> tuple[str, ...]:
        outstanding = []
        for work_id, branch_id in self.work_to_branch.items():
            item = self.branches[branch_id].process_state.work_item(work_id)
            if item is not None and item.status not in {
                WorkItemStatus.FINISHED,
                WorkItemStatus.ABANDONED,
            }:
                outstanding.append(work_id)
        return tuple(sorted(outstanding))

    def recovery_status(self, work_order_id: str) -> WorkflowRecoveryStatus:
        branch_id = self.work_to_branch[work_order_id]
        item = self.branches[branch_id].process_state.work_item(work_order_id)
        if item is None:
            raise KeyError(work_order_id)
        mapping = {
            WorkItemStatus.ENABLED: WorkflowRecoveryStatus.ENABLED,
            WorkItemStatus.ISSUED: WorkflowRecoveryStatus.ISSUED,
            WorkItemStatus.PROPOSAL_RECEIVED: (
                WorkflowRecoveryStatus.PROVIDER_RESULT_RECEIVED
            ),
            WorkItemStatus.REPAIR_PENDING: WorkflowRecoveryStatus.REPAIR_PENDING,
            WorkItemStatus.CONTEXT_PENDING: WorkflowRecoveryStatus.CONTEXT_PENDING,
            WorkItemStatus.FINISHED: WorkflowRecoveryStatus.FINISHED,
            WorkItemStatus.ABANDONED: WorkflowRecoveryStatus.ABANDONED,
        }
        return mapping[item.status]

    @property
    def digest(self) -> str:
        payload = {
            "branches": [
                {
                    "branch_id": branch_id,
                    "process_digest": self.branches[branch_id].process_state.digest,
                    "decision_ids": list(self.branches[branch_id].decision_ids),
                    "event_seqs": list(self.branches[branch_id].event_seqs),
                }
                for branch_id in sorted(self.branches)
            ]
        }
        return "sha256:" + sha256_hex(
            b"workflow.replay-state.v1\x00" + canonical_json(payload)
        )


def replay_workflow(events: Iterable[Any], objects: Any) -> WorkflowReplayState:
    """Reconstruct workflow state from records; never run a model or reducer."""

    state = WorkflowReplayState()
    for event in events:
        state.observe_event(event)
        payload = getattr(event, "control", None)
        if payload is None:
            continue
        records = []
        for object_id in event.outputs:
            schema, value = objects.get(object_id)
            records.append((schema, object_id, value))
        state.apply(event, records, prior_calls=state.calls_by_seq)
    return state


# Stable v1 spelling for callers that prefer explicit versioning.
WorkflowReplayStateV1 = WorkflowReplayState


__all__ = [
    "WorkflowBranchState",
    "WorkflowRecoveryStatus",
    "WorkflowReplayState",
    "WorkflowReplayStateV1",
    "replay_workflow",
]
