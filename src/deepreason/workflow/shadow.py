"""Owned conjecture planning plus non-authoritative shadow comparison."""

from __future__ import annotations

from collections import Counter
from enum import Enum
import hashlib
import re
from typing import Literal, Mapping, Sequence

from pydantic import Field, field_validator, model_validator

from deepreason.run_manifest import RunManifest
from deepreason.workflow.events import (
    ConjectureWorkAssignmentV1,
    WorkflowSignalKind,
    WorkflowSignalV1,
)
from deepreason.workflow.models import (
    GuardFindingCode,
    GuardFindingOutcome,
    GuardFindingV1,
    GuardResultV1,
    IdentifiedWorkflowRecord,
    ProposalReceiptV1,
    ProposalValidationOutcome,
    RouteLeaseRefV1,
    TransitionDecisionV1,
    TransitionKind,
    WorkOrderEnvelopeV1,
    WorkflowRecord,
    repair_attempt_trigger_ref,
)
from deepreason.workflow.profiles import (
    ConjectureWorkflowProfileV1,
    compile_workflow_profile,
)
from deepreason.workflow.reducer import (
    plan_conjecture_batch,
    reduce_conjecture,
)
from deepreason.workflow.state import WorkflowProcessStateV1, apply_decision


class ShadowMismatchCode(str, Enum):
    PROBLEM = "problem"
    SCHOOL = "school"
    ROUTE = "route"
    CONTRACT = "contract"
    CONTEXT = "context"
    PROPOSAL = "proposal"
    ADMISSION = "admission"
    BUDGET = "budget"
    MISSING_CALL = "missing_call"
    MULTIPLE_CALLS = "multiple_calls"
    OBSERVER_ERROR = "observer_error"


class ShadowTerminationKind(str, Enum):
    """Closed scheduler stop reasons that preclude a workflow conclusion."""

    TOKEN_BUDGET_EXCEEDED = "token_budget_exceeded"


_SCHOOL_ID_PATTERN = re.compile(r"^school-(0|[1-9][0-9]*)$")
_WORKFLOW_ID_PATTERN = re.compile(r"^sha256:[0-9a-f]{64}$")


def _diagnostic_ref(value: object, *, max_length: int = 512) -> str:
    """Return a bounded, canonically encodable identifier for diagnostics."""

    if isinstance(value, str):
        try:
            encoded = value.encode("utf-8")
        except UnicodeEncodeError:
            encoded = value.encode("utf-8", errors="surrogatepass")
        else:
            if 1 <= len(value) <= max_length:
                return value
        digest_input = b"str\x00" + encoded
    else:
        try:
            type_name = f"{type(value).__module__}.{type(value).__qualname__}"
            digest_input = b"type\x00" + type_name.encode("utf-8")
        except Exception:  # pragma: no cover - defensive diagnostic fallback
            digest_input = b"unrepresentable"
    return "unrepresentable:sha256:" + hashlib.sha256(digest_input).hexdigest()


def _diagnostic_seq(value: object) -> int:
    return value if type(value) is int and value >= 0 else 0


class MeterSnapshotV1(WorkflowRecord):
    prompt_tokens: int = Field(ge=0)
    completion_tokens: int = Field(ge=0)
    total: int = Field(ge=0)
    budget: int | None = Field(default=None, ge=0)
    calls: int = Field(ge=0)
    reserved: int = Field(ge=0)

    @model_validator(mode="after")
    def _total_matches_components(self):
        if self.total != self.prompt_tokens + self.completion_tokens:
            raise ValueError("meter total differs from its token components")
        return self


class ShadowTicketV1(IdentifiedWorkflowRecord):
    _identity_domain = "workflow.shadow-ticket.v1"

    schema_: Literal["workflow.shadow-ticket.v1"] = Field(
        "workflow.shadow-ticket.v1", alias="schema"
    )
    work_order: WorkOrderEnvelopeV1
    initial_process_state: WorkflowProcessStateV1
    process_state: WorkflowProcessStateV1
    planning_decisions: tuple[TransitionDecisionV1, ...]
    expected_decision_refs: tuple[str, ...]
    expected_transition_kinds: tuple[TransitionKind, ...]
    event_start_seq: int = Field(ge=0)
    meter_before: MeterSnapshotV1 | None = None

    @model_validator(mode="after")
    def _planning_trace_matches_summary(self):
        if tuple(item.id for item in self.planning_decisions) != (
            self.expected_decision_refs
        ):
            raise ValueError("shadow planning decisions differ from their references")
        if tuple(item.transition_kind for item in self.planning_decisions) != (
            self.expected_transition_kinds
        ):
            raise ValueError("shadow planning transitions differ from their summary")
        replayed = self.initial_process_state
        for decision in self.planning_decisions:
            replayed = apply_decision(replayed, decision)
        if replayed != self.process_state:
            raise ValueError("shadow planning decisions do not reconstruct process state")
        return self


class ShadowComparisonV1(IdentifiedWorkflowRecord):
    _identity_domain = "workflow.shadow-comparison.v1"

    schema_: Literal["workflow.shadow-comparison.v1"] = Field(
        "workflow.shadow-comparison.v1", alias="schema"
    )
    work_order_id: str | None = Field(
        default=None, pattern=r"^sha256:[0-9a-f]{64}$"
    )
    problem_ref: str = Field(min_length=1, max_length=512)
    actual_problem_ref: str | None = Field(default=None, min_length=1, max_length=512)
    school_id: str | None = Field(
        default=None, pattern=r"^school-(0|[1-9][0-9]*)$"
    )
    event_start_seq: int = Field(ge=0)
    event_end_seq: int = Field(ge=0)
    expected_route: RouteLeaseRefV1 | None = None
    actual_route: RouteLeaseRefV1 | None = None
    expected_contract_id: str | None = None
    actual_contract_id: str | None = None
    source_call_seq: int | None = Field(default=None, ge=0)
    expected_decision_refs: tuple[str, ...] = ()
    expected_transition_kinds: tuple[TransitionKind, ...] = ()
    transition_decisions: tuple[TransitionDecisionV1, ...] = ()
    actual_event_seqs: tuple[int, ...] = ()
    admitted_refs: tuple[str, ...] = ()
    proposal_candidate_refs: tuple[str, ...] = ()
    rejected_refs: tuple[str, ...] = ()
    deduplicated_refs: tuple[str, ...] = ()
    proposal_receipt_id: str | None = Field(
        default=None, pattern=r"^sha256:[0-9a-f]{64}$"
    )
    guard_result_id: str | None = Field(
        default=None, pattern=r"^sha256:[0-9a-f]{64}$"
    )
    proposal_receipt: ProposalReceiptV1 | None = None
    guard_result: GuardResultV1 | None = None
    meter_token_delta: int | None = Field(default=None, ge=0)
    call_tokens: int | None = Field(default=None, ge=0)
    matched: bool
    mismatch_codes: tuple[ShadowMismatchCode, ...]
    termination_kind: ShadowTerminationKind | None = None
    error_type: str | None = Field(default=None, max_length=256)

    @field_validator("mismatch_codes")
    @classmethod
    def _canonical_mismatches(cls, value):
        canonical = tuple(code for code in ShadowMismatchCode if code in value)
        if tuple(value) != canonical:
            raise ValueError("shadow mismatch codes must be unique and canonical")
        return tuple(value)

    @model_validator(mode="after")
    def _match_shape(self):
        if self.matched == bool(self.mismatch_codes):
            raise ValueError("shadow match flag differs from mismatch codes")
        if self.event_end_seq < self.event_start_seq:
            raise ValueError("shadow event span is reversed")
        if (ShadowMismatchCode.OBSERVER_ERROR in self.mismatch_codes) != (
            self.error_type is not None
        ):
            raise ValueError("observer errors require their exception type")
        if self.termination_kind is not None and (
            ShadowMismatchCode.BUDGET not in self.mismatch_codes
        ):
            raise ValueError("scheduler termination requires a budget mismatch")
        if tuple(item.id for item in self.transition_decisions) != (
            self.expected_decision_refs
        ):
            raise ValueError("shadow decisions differ from their references")
        if tuple(item.transition_kind for item in self.transition_decisions) != (
            self.expected_transition_kinds
        ):
            raise ValueError("shadow decisions differ from their transition summary")
        if (self.proposal_receipt.id if self.proposal_receipt else None) != (
            self.proposal_receipt_id
        ):
            raise ValueError("shadow proposal receipt differs from its reference")
        if (self.guard_result.id if self.guard_result else None) != self.guard_result_id:
            raise ValueError("shadow guard result differs from its reference")
        return self

    @classmethod
    def observer_error(
        cls,
        *,
        problem_ref: str,
        school_id: str | None,
        event_start_seq: int,
        event_end_seq: int,
        error: Exception,
        work_order_id: str | None = None,
    ) -> "ShadowComparisonV1":
        safe_start = _diagnostic_seq(event_start_seq)
        safe_end = max(safe_start, _diagnostic_seq(event_end_seq))
        return cls.create(
            work_order_id=(
                work_order_id
                if isinstance(work_order_id, str)
                and _WORKFLOW_ID_PATTERN.fullmatch(work_order_id)
                else None
            ),
            problem_ref=_diagnostic_ref(problem_ref),
            school_id=(
                school_id
                if isinstance(school_id, str)
                and _SCHOOL_ID_PATTERN.fullmatch(school_id)
                else None
            ),
            event_start_seq=safe_start,
            event_end_seq=safe_end,
            matched=False,
            mismatch_codes=(ShadowMismatchCode.OBSERVER_ERROR,),
            error_type=_diagnostic_ref(type(error).__name__, max_length=256),
        )


def _meter_snapshot(value: Mapping[str, int] | None) -> MeterSnapshotV1 | None:
    return MeterSnapshotV1.model_validate(value) if value is not None else None


def _gate_findings(
    events: Sequence[object],
    *,
    problem_ref: str,
) -> tuple[tuple[GuardFindingV1, ...], bool, bool]:
    """Recover code-authored legacy guard outcomes from the event suffix."""

    findings: list[GuardFindingV1] = []
    invalid_envelope = False
    wrong_problem = False
    for event in events:
        inputs = tuple(getattr(event, "inputs", ()))
        if not inputs:
            continue
        if inputs[0] == "proposal-envelope-invalid":
            invalid_envelope = True
            continue
        if not inputs[0].startswith("gate:"):
            continue
        if len(inputs) < 3 or inputs[2] != problem_ref:
            wrong_problem = True
            continue
        reason = inputs[0].removeprefix("gate:")
        code = (
            GuardFindingCode.BATTERY_EQUIVALENT
            if "battery-equivalent" in reason
            else GuardFindingCode.REFUTED_EQUIVALENT
            if reason.startswith("hash:")
            else GuardFindingCode.INTERFACE_INVALID
        )
        findings.append(
            GuardFindingV1(
                candidate_ref=inputs[1],
                outcome=GuardFindingOutcome.REJECT,
                code=code,
                related_refs=(inputs[1],),
            )
        )
    return tuple(findings), invalid_envelope, wrong_problem


def _synthetic_candidate_ref(call) -> str:
    """Reference a valid raw proposal when legacy dedupe hid candidate IDs."""

    source = call.raw_ref or call.prompt_ref
    return f"raw-proposal:{source}"


class ConjectureShadowObserver:
    """Pure owned planner/comparator with no Harness, store, meter, or adapter.

    Shadow mode uses both planning and post-hoc comparison.  Active mode uses
    the same repository-owned planner to issue durable authority before the
    provider boundary; the scheduler makes setup failures fatal there.
    """

    def __init__(self, profile: ConjectureWorkflowProfileV1) -> None:
        self.profile = ConjectureWorkflowProfileV1.model_validate(profile)

    @classmethod
    def from_manifest(
        cls,
        manifest: RunManifest | None,
    ) -> "ConjectureShadowObserver | None":
        if (
            manifest is None
            or manifest.schema_version != 4
            or manifest.control_plane_policy is None
            or manifest.control_plane_policy.mode
            not in {"shadow", "active_conjecture"}
        ):
            return None
        return cls(compile_workflow_profile(manifest))

    def begin_conjecture(
        self,
        *,
        problem_ref: str,
        canonical_problem_refs: Sequence[str],
        school_id: str | None,
        route_lease: RouteLeaseRefV1,
        contract_id: str,
        formal_fence_seq: int,
        scratch_fence_seq: int,
        event_start_seq: int,
        meter_before: Mapping[str, int] | None = None,
        advisory_context_ref: str | None = None,
    ) -> ShadowTicketV1:
        if problem_ref not in set(canonical_problem_refs):
            raise ValueError("workflow problem is not canonical at its fence")
        if (
            not self.profile.shadow
            and contract_id != self.profile.conjecturer_contract_id
        ):
            raise ValueError("active work must use the owned conjecturer contract")
        state = WorkflowProcessStateV1.initial(
            manifest_digest=self.profile.manifest_digest,
            workflow_profile=self.profile.workflow_profile,
            formal_fence_seq=formal_fence_seq,
            scratch_fence_seq=scratch_fence_seq,
        )
        assignment = ConjectureWorkAssignmentV1(
            school_id=school_id,
            route_lease=route_lease,
            contract_id=contract_id,
            task_payload_schema_id="conjecture.semantic-ref.v1",
            task_payload_ref=problem_ref,
            input_refs=(problem_ref,),
            advisory_context_ref=advisory_context_ref,
        )
        reduction = plan_conjecture_batch(
            self.profile,
            state=state,
            problem_ref=problem_ref,
            assignments=(assignment,),
            canonical_problem_refs=canonical_problem_refs,
        )
        if len(reduction.work_orders) != 1:
            raise ValueError("one conjecture assignment must produce one work order")
        return ShadowTicketV1.create(
            work_order=reduction.work_orders[0],
            initial_process_state=state,
            process_state=reduction.state,
            planning_decisions=reduction.decisions,
            expected_decision_refs=tuple(item.id for item in reduction.decisions),
            expected_transition_kinds=tuple(
                item.transition_kind for item in reduction.decisions
            ),
            event_start_seq=event_start_seq,
            meter_before=_meter_snapshot(meter_before),
        )

    def finish_conjecture(
        self,
        ticket: ShadowTicketV1,
        *,
        actual_problem_ref: str | None,
        events: Sequence[object],
        admitted_refs: Sequence[str],
        candidate_dispositions: Sequence[GuardFindingV1] = (),
        meter_after: Mapping[str, int] | None = None,
        termination_kind: ShadowTerminationKind | None = None,
    ) -> ShadowComparisonV1:
        ticket = ShadowTicketV1.model_validate(ticket)
        termination_kind = (
            None
            if termination_kind is None
            else ShadowTerminationKind(termination_kind)
        )
        events = tuple(events)
        admitted = tuple(admitted_refs)
        dispositions = tuple(
            GuardFindingV1.model_validate(
                finding.model_dump(mode="python")
                if isinstance(finding, GuardFindingV1)
                else finding
            )
            for finding in candidate_dispositions
        )
        calls = [
            event
            for event in events
            if getattr(event, "llm", None) is not None
            and event.llm.role == "conjecturer"
        ]
        mismatches: set[ShadowMismatchCode] = set()
        if termination_kind == ShadowTerminationKind.TOKEN_BUDGET_EXCEEDED:
            mismatches.add(ShadowMismatchCode.BUDGET)
        if actual_problem_ref != ticket.work_order.problem_ref:
            mismatches.add(ShadowMismatchCode.PROBLEM)
        if not calls:
            mismatches.add(ShadowMismatchCode.MISSING_CALL)
        if len(calls) > 1:
            mismatches.add(ShadowMismatchCode.MULTIPLE_CALLS)
        call_event = calls[0] if calls else None
        call = call_event.llm if call_event is not None else None
        trace = tuple(call.attempt_trace) if call is not None else ()
        actual_route = None
        actual_contract = None
        if trace:
            first = trace[0]
            actual_route = RouteLeaseRefV1(
                role="conjecturer",
                seat=first.seat,
                endpoint_id=first.endpoint_id,
                route_sha256=first.route_sha256,
            )
            routes = {
                (
                    attempt.seat,
                    attempt.endpoint_id,
                    attempt.route_sha256,
                )
                for attempt in trace
            }
            if len(routes) != 1:
                mismatches.add(ShadowMismatchCode.ROUTE)
            contracts = {attempt.contract_id for attempt in trace}
            actual_contract = first.contract_id
            if len(contracts) != 1:
                mismatches.add(ShadowMismatchCode.CONTRACT)
        if actual_route != ticket.work_order.route_lease:
            mismatches.add(ShadowMismatchCode.ROUTE)
        if actual_contract != ticket.work_order.contract_id:
            mismatches.add(ShadowMismatchCode.CONTRACT)
        actual_school = (
            call.school_route.school_id
            if call is not None and call.school_route is not None
            else None
        )
        if actual_school != ticket.work_order.school_id:
            mismatches.add(ShadowMismatchCode.SCHOOL)
        expected_context = ticket.work_order.advisory_context_ref
        actual_context = (
            call.conjecture_context.advisory_context_ref
            if call is not None and call.conjecture_context is not None
            else None
        )
        if actual_context != expected_context:
            mismatches.add(ShadowMismatchCode.CONTEXT)

        conjecture_events = tuple(
            event
            for event in events
            if getattr(getattr(event, "rule", None), "value", None) == "Conj"
        )
        if any(
            not event.inputs or event.inputs[0] != ticket.work_order.problem_ref
            for event in conjecture_events
        ):
            mismatches.add(ShadowMismatchCode.PROBLEM)

        gate_findings, invalid_envelope, gate_problem_mismatch = _gate_findings(
            events,
            problem_ref=ticket.work_order.problem_ref,
        )
        if gate_problem_mismatch:
            mismatches.add(ShadowMismatchCode.PROBLEM)

        actual_outputs = tuple(
            output
            for event in conjecture_events
            for output in event.outputs
        )
        if actual_outputs != admitted:
            mismatches.add(ShadowMismatchCode.ADMISSION)

        after = _meter_snapshot(meter_after)
        meter_delta = None
        before = ticket.meter_before
        if (before is None) != (after is None):
            mismatches.add(ShadowMismatchCode.BUDGET)
        elif before is not None and after is not None:
            total_delta = after.total - before.total
            prompt_delta = after.prompt_tokens - before.prompt_tokens
            completion_delta = after.completion_tokens - before.completion_tokens
            call_delta = after.calls - before.calls
            call_tokens = call.tokens if call is not None else 0
            known_usage_attempts = sum(
                1 for attempt in trace if not attempt.usage_unknown
            )
            trace_tokens = sum(attempt.tokens for attempt in trace)
            if (
                min(total_delta, prompt_delta, completion_delta, call_delta) < 0
                or prompt_delta + completion_delta != total_delta
                or total_delta != call_tokens
                or call_delta != known_usage_attempts
                or (trace and trace_tokens != call_tokens)
                or after.budget != before.budget
                or after.reserved != before.reserved
            ):
                mismatches.add(ShadowMismatchCode.BUDGET)
            meter_delta = max(0, total_delta)

        proposal = None
        guard = None
        decision_refs = list(ticket.expected_decision_refs)
        transition_kinds = list(ticket.expected_transition_kinds)
        decisions = list(ticket.planning_decisions)
        state = ticket.process_state
        if call is not None and trace and termination_kind is None:
            final_valid = bool(trace[-1].valid)
            validation = (
                ProposalValidationOutcome.VALID_FIRST_ATTEMPT
                if final_valid and len(trace) == 1
                else ProposalValidationOutcome.VALID_AFTER_REPAIR
                if final_valid
                else ProposalValidationOutcome.TRANSPORT_FAILED
                if any(attempt.usage_unknown for attempt in trace)
                else ProposalValidationOutcome.REPAIR_EXHAUSTED
            )
            findings = list(dispositions or gate_findings)
            if dispositions:
                disposition_refs = [finding.candidate_ref for finding in findings]
                if len(disposition_refs) != len(set(disposition_refs)):
                    mismatches.add(ShadowMismatchCode.PROPOSAL)
                    findings = []
                side_admitted = tuple(
                    finding.candidate_ref
                    for finding in findings
                    if finding.outcome == GuardFindingOutcome.ADMIT
                )
                if side_admitted != actual_outputs:
                    mismatches.add(ShadowMismatchCode.ADMISSION)
                event_rejections = Counter(
                    finding.candidate_ref for finding in gate_findings
                )
                side_rejections = Counter(
                    finding.related_refs[0]
                    if finding.related_refs
                    else finding.candidate_ref
                    for finding in findings
                    if finding.outcome == GuardFindingOutcome.REJECT
                )
                if event_rejections != side_rejections:
                    mismatches.add(ShadowMismatchCode.PROPOSAL)
            else:
                known_candidates = {
                    finding.candidate_ref for finding in findings
                }
                for reference in actual_outputs:
                    if reference in known_candidates:
                        mismatches.add(ShadowMismatchCode.PROPOSAL)
                        continue
                    findings.append(
                        GuardFindingV1(
                            candidate_ref=reference,
                            outcome=GuardFindingOutcome.ADMIT,
                            code=GuardFindingCode.PASSED,
                            related_refs=(reference,),
                        )
                    )
                    known_candidates.add(reference)
            no_register = bool(
                call_event.inputs
                and call_event.inputs[0] == "conj-noregister"
            )
            if final_valid and not findings and not dispositions:
                if no_register:
                    reference = _synthetic_candidate_ref(call)
                    findings.append(
                        GuardFindingV1(
                            candidate_ref=reference,
                            outcome=(
                                GuardFindingOutcome.REJECT
                                if invalid_envelope
                                else GuardFindingOutcome.DEDUPLICATE
                            ),
                            code=(
                                GuardFindingCode.SCHEMA_INVALID
                                if invalid_envelope
                                else GuardFindingCode.CONTENT_DUPLICATE
                            ),
                            related_refs=(reference,),
                        )
                    )
                else:
                    mismatches.add(ShadowMismatchCode.PROPOSAL)
            if not final_valid and (findings or dispositions):
                mismatches.add(ShadowMismatchCode.PROPOSAL)
                findings = []
            candidate_refs = tuple(
                finding.candidate_ref for finding in findings
            )
            proposal = ProposalReceiptV1.create(
                work_order_id=ticket.work_order.id,
                source_call_seq=call_event.seq,
                prompt_ref=call.prompt_ref,
                raw_ref=call.raw_ref or None,
                contract_id=actual_contract or ticket.work_order.contract_id,
                route_lease=actual_route or ticket.work_order.route_lease,
                validation_outcome=validation,
                attempt_count=max(1, len(trace)),
                candidate_payload_refs=candidate_refs if final_valid else (),
                tokens=call.tokens,
            )
            reducible = (
                actual_contract == ticket.work_order.contract_id
                and actual_route == ticket.work_order.route_lease
                and len(candidate_refs)
                <= ticket.work_order.capability_grant.max_candidates
            )
            if not reducible and len(candidate_refs) > (
                ticket.work_order.capability_grant.max_candidates
            ):
                mismatches.add(ShadowMismatchCode.PROPOSAL)
            if reducible:
                # Each rejected schema attempt authorizes exactly one bounded
                # repair before the next provider dispatch.  Derive the same
                # transitions as the live adapter callback so shadow
                # comparison covers crash-visible repair prefixes.
                for rejected in trace[:-1]:
                    if (
                        rejected.valid
                        or rejected.usage_unknown
                        or not rejected.diagnostic_ref
                    ):
                        mismatches.add(ShadowMismatchCode.PROPOSAL)
                        reducible = False
                        break
                    repaired = reduce_conjecture(
                        state,
                        WorkflowSignalV1(
                            kind=WorkflowSignalKind.REPAIR_REQUESTED,
                            work_order=ticket.work_order,
                            trigger_ref=repair_attempt_trigger_ref(
                                rejected.attempt,
                                rejected.diagnostic_ref,
                            ),
                        ),
                    )
                    state = repaired.state
                    decision_refs.extend(
                        item.id for item in repaired.decisions
                    )
                    transition_kinds.extend(
                        item.transition_kind for item in repaired.decisions
                    )
                    decisions.extend(repaired.decisions)
            if reducible:
                if final_valid:
                    signal = WorkflowSignalV1.proposal(
                        ticket.work_order,
                        proposal,
                    )
                else:
                    signal = WorkflowSignalV1.repair_exhausted(
                        ticket.work_order,
                        proposal,
                    )
                reduced = reduce_conjecture(state, signal)
                state = reduced.state
                decision_refs.extend(item.id for item in reduced.decisions)
                transition_kinds.extend(
                    item.transition_kind for item in reduced.decisions
                )
                decisions.extend(reduced.decisions)
            if final_valid and findings:
                admitted_findings = tuple(
                    finding.candidate_ref
                    for finding in findings
                    if finding.outcome == GuardFindingOutcome.ADMIT
                )
                rejected_findings = tuple(
                    finding.candidate_ref
                    for finding in findings
                    if finding.outcome == GuardFindingOutcome.REJECT
                )
                deduplicated_findings = tuple(
                    finding.candidate_ref
                    for finding in findings
                    if finding.outcome == GuardFindingOutcome.DEDUPLICATE
                )
                guard = GuardResultV1.create(
                    work_order_id=ticket.work_order.id,
                    proposal_receipt_id=proposal.id,
                    findings=tuple(findings),
                    admitted_refs=admitted_findings,
                    rejected_refs=rejected_findings,
                    deduplicated_refs=deduplicated_findings,
                )
                if reducible:
                    reduced = reduce_conjecture(
                        state,
                        WorkflowSignalV1.guarded(ticket.work_order, guard),
                    )
                    decision_refs.extend(item.id for item in reduced.decisions)
                    transition_kinds.extend(
                        item.transition_kind for item in reduced.decisions
                    )
                    decisions.extend(reduced.decisions)
            elif final_valid and reducible:
                reduced = reduce_conjecture(
                    state,
                    WorkflowSignalV1(
                        kind=WorkflowSignalKind.WORK_FINISHED,
                        work_order=ticket.work_order,
                        trigger_ref=proposal.id,
                    ),
                )
                decision_refs.extend(item.id for item in reduced.decisions)
                transition_kinds.extend(
                    item.transition_kind for item in reduced.decisions
                )
                decisions.extend(reduced.decisions)

        ordered_mismatches = tuple(
            code for code in ShadowMismatchCode if code in mismatches
        )
        end_seq = max(
            ticket.event_start_seq,
            max(
                (
                    getattr(event, "seq", ticket.event_start_seq)
                    for event in events
                ),
                default=ticket.event_start_seq,
            ),
        )
        return ShadowComparisonV1.create(
            work_order_id=ticket.work_order.id,
            problem_ref=ticket.work_order.problem_ref,
            actual_problem_ref=actual_problem_ref,
            school_id=ticket.work_order.school_id,
            event_start_seq=ticket.event_start_seq,
            event_end_seq=end_seq,
            expected_route=ticket.work_order.route_lease,
            actual_route=actual_route,
            expected_contract_id=ticket.work_order.contract_id,
            actual_contract_id=actual_contract,
            source_call_seq=(call_event.seq if call_event is not None else None),
            expected_decision_refs=tuple(decision_refs),
            expected_transition_kinds=tuple(transition_kinds),
            transition_decisions=tuple(decisions),
            actual_event_seqs=tuple(getattr(event, "seq") for event in events),
            admitted_refs=admitted,
            proposal_candidate_refs=(
                proposal.candidate_payload_refs if proposal is not None else ()
            ),
            rejected_refs=guard.rejected_refs if guard is not None else (),
            deduplicated_refs=(
                guard.deduplicated_refs if guard is not None else ()
            ),
            proposal_receipt_id=proposal.id if proposal is not None else None,
            guard_result_id=guard.id if guard is not None else None,
            proposal_receipt=proposal,
            guard_result=guard,
            meter_token_delta=meter_delta,
            call_tokens=call.tokens if call is not None else None,
            matched=not ordered_mismatches,
            mismatch_codes=ordered_mismatches,
            termination_kind=termination_kind,
        )


__all__ = [
    "ConjectureShadowObserver",
    "MeterSnapshotV1",
    "ShadowComparisonV1",
    "ShadowMismatchCode",
    "ShadowTerminationKind",
    "ShadowTicketV1",
]
