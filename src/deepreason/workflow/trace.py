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

from deepreason.llm.adapter import WorkflowAuthorizationError
from deepreason.ontology import LLMAttempt, LLMCall
from deepreason.workflow.events import WorkflowSignalKind, WorkflowSignalV1
from deepreason.workflow.models import (
    BudgetDeltaV1,
    CapabilityGrantV1,
    GuardFindingOutcome,
    GuardFindingV1,
    GuardResultV1,
    ProposalReceiptV1,
    ProposalValidationOutcome,
    RepairWorkOrderV1,
    RouteLeaseRefV1,
    TransitionDecisionV1,
    TransitionKind,
    TriggerKind,
    WorkOrderEnvelopeV1,
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
    authoritative: bool = False
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
        if self.error_sink is not None:
            try:
                self.error_sink(error)
            except Exception:  # noqa: BLE001 - diagnostics never affect actuation
                pass
        if self.authoritative:
            if isinstance(error, WorkflowAuthorizationError):
                raise error
            raise WorkflowAuthorizationError(
                "active conjecture transition was not durably authorized"
            ) from error

    def require_authority(self) -> None:
        """Make subsequent persistence failures fail closed."""

        self.authoritative = True
        if self.failed:
            self._report(RuntimeError("authoritative workflow trace already failed"))

    def authorize_dispatch(self, reserved_tokens: int = 0) -> str | None:
        """Persist enable/issue immediately before the provider boundary."""

        if self.dispatch_authorized:
            return self.ticket.work_order.id
        if self.failed:
            if self.authoritative:
                self._report(
                    RuntimeError("dispatch authorization follows a failed trace")
                )
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
                controller_version=original_issued.controller_version,
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
        context_request_hash: str | None = None,
        context_request_ref: str | None = None,
        abstention_hash: str | None = None,
        abstention_ref: str | None = None,
    ) -> None:
        """Persist the provider receipt before any candidate guard executes."""

        if not self.dispatch_authorized or self.failed:
            if self.authoritative:
                self._report(
                    RuntimeError(
                        "provider result requires successful dispatch authorization"
                    )
                )
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
                context_request_hash=(context_request_hash if final_valid else None),
                context_request_ref=(context_request_ref if final_valid else None),
                abstention_hash=(abstention_hash if final_valid else None),
                abstention_ref=(abstention_ref if final_valid else None),
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

    def record_context_request(self) -> None:
        """Persist the model's bounded request before its semantic decision."""

        if self.proposal_receipt is None or self.failed:
            if self.authoritative:
                self._report(
                    RuntimeError("context request has no durable proposal receipt")
                )
            return
        try:
            request_hash = self.proposal_receipt.context_request_hash
            if request_hash is None or self.proposal_receipt.context_request_ref is None:
                raise ValueError("proposal receipt has no context request")
            reduced = reduce_conjecture(
                self.process_state,
                WorkflowSignalV1(
                    kind=WorkflowSignalKind.CONTEXT_REQUESTED,
                    work_order=self.ticket.work_order,
                    trigger_ref=request_hash,
                ),
            )
            decision = reduced.decisions[0]
            self.harness.record_control_transition(decision)
            self.process_state = reduced.state
            self.decision_ids.append(decision.id)
        except Exception as error:  # noqa: BLE001 - shadow remains contained
            self._report(error)

    def record_context_decision(self, *, granted: bool, trigger_ref: str) -> None:
        """Persist a code-authored grant or denial before its turn event."""

        if self.failed:
            if self.authoritative:
                self._report(RuntimeError("context decision follows a failed trace"))
            return
        try:
            reduced = reduce_conjecture(
                self.process_state,
                WorkflowSignalV1(
                    kind=(
                        WorkflowSignalKind.CONTEXT_GRANTED
                        if granted
                        else WorkflowSignalKind.CONTEXT_DENIED
                    ),
                    work_order=self.ticket.work_order,
                    trigger_ref=trigger_ref,
                ),
            )
            decision = reduced.decisions[0]
            self.harness.record_control_transition(decision)
            self.process_state = reduced.state
            self.decision_ids.append(decision.id)
        except Exception as error:  # noqa: BLE001 - shadow remains contained
            self._report(error)

    def finish(self, trigger_ref: str | None = None) -> None:
        """Close a no-candidate or superseded work order exactly once."""

        if self.failed:
            if self.authoritative:
                self._report(RuntimeError("work completion follows a failed trace"))
            return
        try:
            from deepreason.workflow.state import WorkItemStatus

            item = self.process_state.work_item(self.ticket.work_order.id)
            if item is None:
                raise ValueError("workflow completion has no work item")
            if item.status in {WorkItemStatus.FINISHED, WorkItemStatus.ABANDONED}:
                return
            receipt = self.proposal_receipt
            reduced = reduce_conjecture(
                self.process_state,
                WorkflowSignalV1(
                    kind=WorkflowSignalKind.WORK_FINISHED,
                    work_order=self.ticket.work_order,
                    trigger_ref=(
                        trigger_ref
                        or (receipt.id if receipt is not None else self.ticket.work_order.id)
                    ),
                ),
            )
            decision = reduced.decisions[0]
            self.harness.record_control_transition(decision)
            self.process_state = reduced.state
            self.decision_ids.append(decision.id)
        except Exception as error:  # noqa: BLE001 - shadow remains contained
            self._report(error)

    def follow_up(
        self,
        *,
        advisory_context_ref: str,
        formal_fence_seq: int,
        scratch_fence_seq: int,
    ) -> "ConjectureControlTrace":
        """Create fresh one-call authority for a granted context expansion."""

        try:
            parent = self.ticket.work_order
            parent_grant = parent.capability_grant
            remaining = parent_grant.remaining_context_expansions - 1
            if remaining < 0:
                raise ValueError("context follow-up exceeds expansion authority")
            allowed = tuple(
                outcome
                for outcome in parent_grant.allowed_outcomes
            )
            grant = CapabilityGrantV1.create(
                profile_id=parent_grant.profile_id,
                allowed_outcomes=allowed,
                max_candidates=parent_grant.max_candidates,
                max_local_repairs=parent_grant.max_local_repairs,
                remaining_context_expansions=remaining,
                max_extra_context_blocks=parent_grant.max_extra_context_blocks,
                permitted_retrieval_channels=parent_grant.permitted_retrieval_channels,
            )
            inputs = tuple(dict.fromkeys((*parent.input_refs, parent.id)))
            values = parent.model_dump(
                mode="python",
                by_alias=True,
                exclude={
                    "id",
                    "formal_fence_seq",
                    "scratch_fence_seq",
                    "input_refs",
                    "advisory_context_ref",
                    "capability_grant",
                },
            )
            work = WorkOrderEnvelopeV1.create(
                **values,
                formal_fence_seq=formal_fence_seq,
                scratch_fence_seq=scratch_fence_seq,
                input_refs=inputs,
                advisory_context_ref=advisory_context_ref,
                capability_grant=grant,
            )
            if work.id == parent.id:
                raise ValueError("context follow-up must use a fresh work order")
            initial = WorkflowProcessStateV1.initial(
                manifest_digest=work.manifest_digest,
                workflow_profile=work.workflow_profile,
                formal_fence_seq=formal_fence_seq,
                scratch_fence_seq=scratch_fence_seq,
            )
            enabled_state = state_after_transition(
                initial,
                transition_kind=TransitionKind.WORK_ENABLED,
                work_order_id=work.id,
                trigger_ref=work.problem_ref,
            )
            enabled = TransitionDecisionV1.create(
                manifest_digest=work.manifest_digest,
                controller_version=work.controller_version,
                workflow_profile=work.workflow_profile,
                previous_process_digest=initial.digest,
                trigger_kind=TriggerKind.PROBLEM_SELECTED,
                trigger_ref=work.problem_ref,
                transition_kind=TransitionKind.WORK_ENABLED,
                work_order_id=work.id,
                route_lease=work.route_lease,
                next_process_digest=enabled_state.digest,
            )
            issued_state = state_after_transition(
                enabled_state,
                transition_kind=TransitionKind.WORK_ISSUED,
                work_order_id=work.id,
                trigger_ref=advisory_context_ref,
            )
            issued = TransitionDecisionV1.create(
                manifest_digest=work.manifest_digest,
                controller_version=work.controller_version,
                workflow_profile=work.workflow_profile,
                previous_process_digest=enabled_state.digest,
                trigger_kind=TriggerKind.CONTEXT_PREPARED,
                trigger_ref=advisory_context_ref,
                transition_kind=TransitionKind.WORK_ISSUED,
                work_order_id=work.id,
                route_lease=work.route_lease,
                next_process_digest=issued_state.digest,
            )
            planning = (enabled, issued)
            ticket = ShadowTicketV1.create(
                work_order=work,
                initial_process_state=initial,
                process_state=issued_state,
                planning_decisions=planning,
                expected_decision_refs=tuple(item.id for item in planning),
                expected_transition_kinds=tuple(
                    item.transition_kind for item in planning
                ),
                event_start_seq=self.harness._next_seq,
                meter_before=None,
            )
            return ConjectureControlTrace(
                self.harness,
                ticket,
                error_sink=self.error_sink,
                authoritative=self.authoritative,
            )
        except Exception as error:
            self._report(error)
            raise AssertionError("unreachable") from error

    def capability_follow_up(
        self,
        *,
        result_package_ref: str,
        result_context_ref: str,
        formal_fence_seq: int,
        scratch_fence_seq: int,
    ) -> "ConjectureControlTrace":
        """Create fresh provider authority for one packaged capability result."""

        try:
            parent = self.ticket.work_order
            inputs = tuple(
                dict.fromkeys((*parent.input_refs, parent.id, result_package_ref))
            )
            values = parent.model_dump(
                mode="python",
                by_alias=True,
                exclude={
                    "id",
                    "formal_fence_seq",
                    "scratch_fence_seq",
                    "input_refs",
                    "advisory_context_ref",
                    "task_payload_schema_id",
                    "task_payload_ref",
                    "task_payload_value",
                },
            )
            work = WorkOrderEnvelopeV1.create(
                **values,
                formal_fence_seq=formal_fence_seq,
                scratch_fence_seq=scratch_fence_seq,
                input_refs=inputs,
                advisory_context_ref=None,
                task_payload_schema_id="simulation-result-context.v1",
                task_payload_value={
                    "parent_work_order_ref": parent.id,
                    "result_package_ref": result_package_ref,
                    "result_context_ref": result_context_ref,
                },
            )
            if work.id == parent.id:
                raise ValueError("capability result follow-up must use fresh work")
            initial = WorkflowProcessStateV1.initial(
                manifest_digest=work.manifest_digest,
                workflow_profile=work.workflow_profile,
                formal_fence_seq=formal_fence_seq,
                scratch_fence_seq=scratch_fence_seq,
            )
            enabled_state = state_after_transition(
                initial,
                transition_kind=TransitionKind.WORK_ENABLED,
                work_order_id=work.id,
                trigger_ref=work.problem_ref,
            )
            enabled = TransitionDecisionV1.create(
                manifest_digest=work.manifest_digest,
                controller_version=work.controller_version,
                workflow_profile=work.workflow_profile,
                previous_process_digest=initial.digest,
                trigger_kind=TriggerKind.PROBLEM_SELECTED,
                trigger_ref=work.problem_ref,
                transition_kind=TransitionKind.WORK_ENABLED,
                work_order_id=work.id,
                route_lease=work.route_lease,
                next_process_digest=enabled_state.digest,
            )
            issued_state = state_after_transition(
                enabled_state,
                transition_kind=TransitionKind.WORK_ISSUED,
                work_order_id=work.id,
                trigger_ref=work.id,
            )
            issued = TransitionDecisionV1.create(
                manifest_digest=work.manifest_digest,
                controller_version=work.controller_version,
                workflow_profile=work.workflow_profile,
                previous_process_digest=enabled_state.digest,
                trigger_kind=TriggerKind.CONTEXT_PREPARED,
                trigger_ref=work.id,
                transition_kind=TransitionKind.WORK_ISSUED,
                work_order_id=work.id,
                route_lease=work.route_lease,
                next_process_digest=issued_state.digest,
            )
            planning = (enabled, issued)
            ticket = ShadowTicketV1.create(
                work_order=work,
                initial_process_state=initial,
                process_state=issued_state,
                planning_decisions=planning,
                expected_decision_refs=tuple(item.id for item in planning),
                expected_transition_kinds=tuple(
                    item.transition_kind for item in planning
                ),
                event_start_seq=self.harness._next_seq,
                meter_before=None,
            )
            return ConjectureControlTrace(
                self.harness,
                ticket,
                error_sink=self.error_sink,
                authoritative=self.authoritative,
            )
        except Exception as error:
            self._report(error)
            raise AssertionError("unreachable") from error

    def record_repair_request(self, rejected_attempt: LLMAttempt) -> None:
        """Persist bounded schema-repair authority before the next dispatch."""

        if not self.dispatch_authorized or self.failed:
            if self.authoritative:
                self._report(
                    RuntimeError(
                        "repair request requires successful dispatch authorization"
                    )
                )
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
            work = self.ticket.work_order
            if (
                attempt.contract_id != work.contract_id
                or attempt.seat != work.route_lease.seat
                or attempt.endpoint_id != work.route_lease.endpoint_id
                or attempt.route_sha256 != work.route_lease.route_sha256
            ):
                raise ValueError("workflow repair changed frozen route authority")
            if not attempt.raw_ref:
                raise ValueError("workflow schema repair requires rejected raw output")
            repair_attempt = attempt.attempt + 1
            repair_work_order = (
                RepairWorkOrderV1.create(
                    parent_work_order_id=work.id,
                    attempt=repair_attempt,
                    rejected_prompt_ref=attempt.prompt_ref,
                    rejected_raw_ref=attempt.raw_ref,
                    rejected_diagnostic_ref=attempt.diagnostic_ref,
                    validation_pointer=attempt.validation_path,
                    authorized_subtree_pointer=attempt.repair_scope,
                    remaining_local_attempts=(
                        work.capability_grant.max_local_repairs
                        - repair_attempt
                        + 1
                    ),
                    contract_id=work.contract_id,
                    route_lease=work.route_lease,
                    formal_fence_seq=work.formal_fence_seq,
                    scratch_fence_seq=work.scratch_fence_seq,
                    repair_policy_ref=work.repair_policy_ref,
                )
                if self.authoritative
                else None
            )
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
            self.harness.record_control_transition(
                decision,
                repair_work_order=repair_work_order,
            )
            self.process_state = reduced.state
            self.decision_ids.append(decision.id)
        except Exception as error:  # noqa: BLE001 - shadow is non-authoritative
            self._report(error)

    def record_guard(self, findings: Sequence[GuardFindingV1]) -> None:
        """Persist the code-authored disposition before semantic admission."""

        if self.proposal_receipt is None or self.failed:
            if self.authoritative:
                self._report(RuntimeError("guard requires a durable proposal receipt"))
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


def build_capability_follow_up_trace(
    harness,
    parent: WorkOrderEnvelopeV1,
    *,
    result_package_ref: str,
    result_context_ref: str,
    formal_fence_seq: int,
    scratch_fence_seq: int,
    authoritative: bool,
    error_sink=None,
) -> ConjectureControlTrace:
    """Reconstruct fresh result-consumption authority from durable parent work."""

    parent = WorkOrderEnvelopeV1.model_validate(
        parent.model_dump(mode="python", by_alias=True)
    )
    inputs = tuple(dict.fromkeys((*parent.input_refs, parent.id, result_package_ref)))
    values = parent.model_dump(
        mode="python",
        by_alias=True,
        exclude={
            "id",
            "formal_fence_seq",
            "scratch_fence_seq",
            "input_refs",
            "advisory_context_ref",
            "task_payload_schema_id",
            "task_payload_ref",
            "task_payload_value",
        },
    )
    work = WorkOrderEnvelopeV1.create(
        **values,
        formal_fence_seq=formal_fence_seq,
        scratch_fence_seq=scratch_fence_seq,
        input_refs=inputs,
        advisory_context_ref=None,
        task_payload_schema_id="simulation-result-context.v1",
        task_payload_value={
            "parent_work_order_ref": parent.id,
            "result_package_ref": result_package_ref,
            "result_context_ref": result_context_ref,
        },
    )
    if work.id == parent.id:
        raise ValueError("capability result follow-up must use fresh work")
    initial = WorkflowProcessStateV1.initial(
        manifest_digest=work.manifest_digest,
        workflow_profile=work.workflow_profile,
        formal_fence_seq=formal_fence_seq,
        scratch_fence_seq=scratch_fence_seq,
    )
    enabled_state = state_after_transition(
        initial,
        transition_kind=TransitionKind.WORK_ENABLED,
        work_order_id=work.id,
        trigger_ref=work.problem_ref,
    )
    enabled = TransitionDecisionV1.create(
        manifest_digest=work.manifest_digest,
        controller_version=work.controller_version,
        workflow_profile=work.workflow_profile,
        previous_process_digest=initial.digest,
        trigger_kind=TriggerKind.PROBLEM_SELECTED,
        trigger_ref=work.problem_ref,
        transition_kind=TransitionKind.WORK_ENABLED,
        work_order_id=work.id,
        route_lease=work.route_lease,
        next_process_digest=enabled_state.digest,
    )
    issued_state = state_after_transition(
        enabled_state,
        transition_kind=TransitionKind.WORK_ISSUED,
        work_order_id=work.id,
        trigger_ref=work.id,
    )
    issued = TransitionDecisionV1.create(
        manifest_digest=work.manifest_digest,
        controller_version=work.controller_version,
        workflow_profile=work.workflow_profile,
        previous_process_digest=enabled_state.digest,
        trigger_kind=TriggerKind.CONTEXT_PREPARED,
        trigger_ref=work.id,
        transition_kind=TransitionKind.WORK_ISSUED,
        work_order_id=work.id,
        route_lease=work.route_lease,
        next_process_digest=issued_state.digest,
    )
    planning = (enabled, issued)
    ticket = ShadowTicketV1.create(
        work_order=work,
        initial_process_state=initial,
        process_state=issued_state,
        planning_decisions=planning,
        expected_decision_refs=tuple(item.id for item in planning),
        expected_transition_kinds=tuple(item.transition_kind for item in planning),
        event_start_seq=harness._next_seq,
        meter_before=None,
    )
    return ConjectureControlTrace(
        harness,
        ticket,
        error_sink=error_sink,
        authoritative=authoritative,
    )


__all__ = ["ConjectureControlTrace", "build_capability_follow_up_trace"]
