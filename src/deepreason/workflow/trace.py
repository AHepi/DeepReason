"""Live C1 persistence seam for one shadow conjecture work order.

The legacy scheduler still chooses and executes the work in shadow mode.  This
small object only brackets that execution with replayable authority records;
all failures are reported through a diagnostic callback and then contained so
the observer cannot alter the semantic path.
"""

from __future__ import annotations

from collections.abc import Callable, Sequence
from dataclasses import dataclass, field
from typing import Any

from deepreason.ontology import LLMAttempt, LLMCall
from deepreason.workflow.events import WorkflowSignalKind, WorkflowSignalV1
from deepreason.workflow.models import (
    BudgetDeltaV1,
    GuardFindingOutcome,
    GuardFindingV1,
    GuardResultV1,
    ProposalReceiptV1,
    ProposalValidationOutcome,
    RouteLeaseRefV1,
    TransitionDecisionV1,
    TransitionKind,
    repair_attempt_trigger_ref,
)
from deepreason.workflow.reducer import reduce_conjecture
from deepreason.workflow.shadow import ShadowComparisonV1, ShadowTicketV1
from deepreason.workflow.state import (
    WorkflowProcessStateV1,
    apply_decision,
    state_after_transition,
)


@dataclass
class ConjectureControlTrace:
    """Persist one temporally ordered shadow trace without owning semantics."""

    harness: Any
    ticket: ShadowTicketV1
    error_sink: Callable[[Exception], None] | None = None
    process_state: WorkflowProcessStateV1 = field(init=False)
    proposal_receipt: ProposalReceiptV1 | None = field(default=None, init=False)
    decision_ids: list[str] = field(default_factory=list, init=False)
    dispatch_authorized: bool = field(default=False, init=False)
    failed: bool = field(default=False, init=False)

    def __post_init__(self) -> None:
        self.ticket = ShadowTicketV1.model_validate(
            self.ticket.model_dump(mode="python", by_alias=True)
        )
        self.process_state = self.ticket.initial_process_state

    def _report(self, error: Exception) -> None:
        self.failed = True
        if self.error_sink is None:
            return
        try:
            self.error_sink(error)
        except Exception:  # noqa: BLE001 - diagnostics never affect actuation
            return

    def authorize_dispatch(self, reserved_tokens: int = 0) -> str | None:
        """Persist enable/issue immediately before the provider boundary."""

        if self.dispatch_authorized:
            return self.ticket.work_order.id
        if self.failed:
            return None
        try:
            if type(reserved_tokens) is not int or reserved_tokens < 0:
                raise ValueError("workflow reservation must be a nonnegative integer")
            # The adapter reports the first attempt's conservative bound.
            # Reserve the same ceiling for every locally authorized schema
            # attempt so settlement never invents repair capacity after the
            # provider has already responded.  C4 will emit per-repair work
            # orders; C1 keeps the bounded logical call under one issuance.
            reserved_tokens *= (
                self.ticket.work_order.capability_grant.max_local_repairs + 1
            )
            if len(self.ticket.planning_decisions) != 2:
                raise ValueError("conjecture dispatch requires enable and issue decisions")
            enabled, original_issued = self.ticket.planning_decisions
            enabled_state = apply_decision(
                self.ticket.initial_process_state,
                enabled,
            )
            issued_state = state_after_transition(
                enabled_state,
                transition_kind=TransitionKind.WORK_ISSUED,
                work_order_id=self.ticket.work_order.id,
                trigger_ref=original_issued.trigger_ref,
                reserved_tokens=reserved_tokens,
            )
            issued = TransitionDecisionV1.create(
                manifest_digest=original_issued.manifest_digest,
                workflow_profile=original_issued.workflow_profile,
                previous_process_digest=enabled_state.digest,
                trigger_kind=original_issued.trigger_kind,
                trigger_ref=original_issued.trigger_ref,
                transition_kind=TransitionKind.WORK_ISSUED,
                work_order_id=self.ticket.work_order.id,
                route_lease=self.ticket.work_order.route_lease,
                budget_delta=BudgetDeltaV1(
                    reserved_tokens=reserved_tokens
                ),
                next_process_digest=issued_state.digest,
            )
            planning_decisions = (enabled, issued)
            self.ticket = ShadowTicketV1.create(
                work_order=self.ticket.work_order,
                initial_process_state=self.ticket.initial_process_state,
                process_state=issued_state,
                planning_decisions=planning_decisions,
                expected_decision_refs=tuple(
                    item.id for item in planning_decisions
                ),
                expected_transition_kinds=tuple(
                    item.transition_kind for item in planning_decisions
                ),
                event_start_seq=self.ticket.event_start_seq,
                meter_before=self.ticket.meter_before,
            )
            for decision in self.ticket.planning_decisions:
                self.harness.record_control_transition(
                    decision,
                    work_order=(
                        self.ticket.work_order
                        if decision.transition_kind == TransitionKind.WORK_ENABLED
                        else None
                    ),
                )
                self.decision_ids.append(decision.id)
            self.process_state = self.ticket.process_state
            self.dispatch_authorized = True
            return self.ticket.work_order.id
        except Exception as error:  # noqa: BLE001 - shadow is non-authoritative
            self._report(error)
            return None

    def record_provider_result(
        self,
        *,
        source_call_seq: int,
        llm_call: LLMCall,
        candidate_refs: Sequence[str],
    ) -> None:
        """Persist the provider receipt before any candidate guard executes."""

        if not self.dispatch_authorized or self.failed:
            return
        try:
            call = LLMCall.model_validate(
                llm_call.model_dump(mode="python", by_alias=True)
            )
            refs = tuple(candidate_refs)
            if len(refs) != len(set(refs)):
                raise ValueError("workflow proposal candidate references repeat")
            attempts = tuple(call.attempt_trace)
            if not attempts:
                raise ValueError("workflow provider result has no attempt trace")
            work = self.ticket.work_order
            if call.work_order_id != work.id:
                raise ValueError("workflow provider result names another work order")
            if any(
                attempt.contract_id != work.contract_id
                or attempt.seat != work.route_lease.seat
                or attempt.endpoint_id != work.route_lease.endpoint_id
                or attempt.route_sha256 != work.route_lease.route_sha256
                for attempt in attempts
            ):
                raise ValueError("workflow provider result changed route authority")
            final_valid = attempts[-1].valid
            validation = (
                ProposalValidationOutcome.VALID_FIRST_ATTEMPT
                if final_valid and len(attempts) == 1
                else ProposalValidationOutcome.VALID_AFTER_REPAIR
                if final_valid
                else ProposalValidationOutcome.TRANSPORT_FAILED
                if any(attempt.usage_unknown for attempt in attempts)
                else ProposalValidationOutcome.REPAIR_EXHAUSTED
            )
            proposal = ProposalReceiptV1.create(
                work_order_id=work.id,
                source_call_seq=source_call_seq,
                prompt_ref=call.prompt_ref,
                raw_ref=call.raw_ref or None,
                contract_id=work.contract_id,
                route_lease=RouteLeaseRefV1.model_validate(work.route_lease),
                validation_outcome=validation,
                attempt_count=len(attempts),
                candidate_payload_refs=refs if final_valid else (),
                tokens=call.tokens,
            )
            signal = (
                WorkflowSignalV1.proposal(work, proposal)
                if final_valid
                else WorkflowSignalV1.repair_exhausted(work, proposal)
            )
            reduced = reduce_conjecture(self.process_state, signal)
            self.harness.record_control_transition(
                reduced.decisions[0],
                proposal_receipt=proposal,
            )
            self.process_state = reduced.state
            self.proposal_receipt = proposal
            self.decision_ids.append(reduced.decisions[0].id)
        except Exception as error:  # noqa: BLE001 - shadow is non-authoritative
            self._report(error)

    def record_repair_request(self, rejected_attempt: LLMAttempt) -> None:
        """Persist bounded schema-repair authority before the next dispatch."""

        if not self.dispatch_authorized or self.failed:
            return
        try:
            attempt = LLMAttempt.model_validate(
                rejected_attempt.model_dump(mode="python", by_alias=True)
            )
            if attempt.valid or attempt.usage_unknown or not attempt.diagnostic_ref:
                raise ValueError(
                    "workflow repair requires a schema-invalid attempt diagnostic"
                )
            prior_requests = sum(
                self.harness.workflow_state.decisions[decision_id].transition_kind
                == TransitionKind.REPAIR_REQUESTED
                for decision_id in self.decision_ids
                if decision_id in self.harness.workflow_state.decisions
            )
            if attempt.attempt != prior_requests:
                raise ValueError("workflow repair request has a non-canonical index")
            if prior_requests >= (
                self.ticket.work_order.capability_grant.max_local_repairs
            ):
                raise ValueError("workflow local-repair authority is exhausted")
            reduced = reduce_conjecture(
                self.process_state,
                WorkflowSignalV1(
                    kind=WorkflowSignalKind.REPAIR_REQUESTED,
                    work_order=self.ticket.work_order,
                    trigger_ref=repair_attempt_trigger_ref(
                        attempt.attempt,
                        attempt.diagnostic_ref,
                    ),
                ),
            )
            decision = reduced.decisions[0]
            self.harness.record_control_transition(decision)
            self.process_state = reduced.state
            self.decision_ids.append(decision.id)
        except Exception as error:  # noqa: BLE001 - shadow is non-authoritative
            self._report(error)

    def record_guard(self, findings: Sequence[GuardFindingV1]) -> None:
        """Persist the code-authored disposition before semantic admission."""

        if self.proposal_receipt is None or self.failed:
            return
        try:
            canonical = tuple(
                GuardFindingV1.model_validate(
                    item.model_dump(mode="python", by_alias=True)
                    if isinstance(item, GuardFindingV1)
                    else item
                )
                for item in findings
            )
            if not canonical:
                raise ValueError("workflow guard requires at least one finding")
            proposal_refs = tuple(self.proposal_receipt.candidate_payload_refs)
            if tuple(item.candidate_ref for item in canonical) != proposal_refs:
                raise ValueError("workflow guard order differs from its proposal")
            guard = GuardResultV1.create(
                work_order_id=self.ticket.work_order.id,
                proposal_receipt_id=self.proposal_receipt.id,
                findings=canonical,
                admitted_refs=tuple(
                    item.candidate_ref
                    for item in canonical
                    if item.outcome == GuardFindingOutcome.ADMIT
                ),
                rejected_refs=tuple(
                    item.candidate_ref
                    for item in canonical
                    if item.outcome == GuardFindingOutcome.REJECT
                ),
                deduplicated_refs=tuple(
                    item.candidate_ref
                    for item in canonical
                    if item.outcome == GuardFindingOutcome.DEDUPLICATE
                ),
            )
            reduced = reduce_conjecture(
                self.process_state,
                WorkflowSignalV1.guarded(self.ticket.work_order, guard),
            )
            self.harness.record_control_transition(
                reduced.decisions[0],
                guard_result=guard,
            )
            self.process_state = reduced.state
            self.decision_ids.append(reduced.decisions[0].id)
        except Exception as error:  # noqa: BLE001 - shadow is non-authoritative
            self._report(error)

    def abandon(self, trigger_ref: str) -> None:
        """Close any durable nonterminal prefix and release its reservation.

        A graceful scheduler stop may arrive after only part of this trace was
        persisted.  Derive abandonment from the harness replay state rather
        than the optimistic in-memory copy so even an enabled-only or issued
        prefix is closed exactly once.
        """

        try:
            work_id = self.ticket.work_order.id
            branch_id = self.harness.workflow_state.work_to_branch.get(work_id)
            if branch_id is None:
                self.seal()
                return
            durable_state = self.harness.workflow_state.branches[
                branch_id
            ].process_state
            item = durable_state.work_item(work_id)
            if item is None:
                raise ValueError("durable workflow branch has no work item")
            from deepreason.workflow.state import WorkItemStatus

            if item.status in {
                WorkItemStatus.FINISHED,
                WorkItemStatus.ABANDONED,
            }:
                self.process_state = durable_state
                self.seal()
                return
            reduced = reduce_conjecture(
                durable_state,
                WorkflowSignalV1(
                    kind=WorkflowSignalKind.WORK_ABANDONED,
                    work_order=self.ticket.work_order,
                    trigger_ref=trigger_ref,
                ),
            )
            decision = reduced.decisions[0]
            self.harness.record_control_transition(decision)
            self.process_state = reduced.state
            self.decision_ids.append(decision.id)
            self.seal()
        except Exception as error:  # noqa: BLE001 - shadow is non-authoritative
            self._report(error)

    def finalize(self, comparison: ShadowComparisonV1) -> None:
        """Cross-check independently derived shadow decisions and seal prefix."""

        try:
            comparison = ShadowComparisonV1.model_validate(
                comparison.model_dump(mode="python", by_alias=True)
            )
            if comparison.matched and tuple(self.decision_ids) != (
                comparison.expected_decision_refs
            ):
                raise ValueError(
                    "durable workflow trace differs from shadow comparison"
                )
            self.seal()
        except Exception as error:  # noqa: BLE001 - shadow is non-authoritative
            self._report(error)

    def seal(self) -> None:
        """Checkpoint the durable prefix when comparison is unavailable."""

        try:
            self.harness.write_workflow_checkpoint()
        except Exception as error:  # noqa: BLE001 - shadow is non-authoritative
            self._report(error)


__all__ = ["ConjectureControlTrace"]
