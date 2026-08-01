"""C0 authority records are closed and canonical while semantics stay external."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from deepreason.runtime.stop import StopDecision
from deepreason.scratch.models import RetrievalChannel
from deepreason.workflow.models import (
    BudgetDeltaV1,
    CapabilityGrantV1,
    CapabilityOutcome,
    GuardFindingCode,
    GuardFindingOutcome,
    GuardFindingV1,
    GuardResultV1,
    LocalRepairPolicyV1,
    ProposalReceiptV1,
    ProposalValidationOutcome,
    RouteLeaseRefV1,
    TransitionDecisionV1,
    TransitionKind,
    TriggerKind,
    WorkflowStopDecisionV1,
    WorkOrderEnvelopeV1,
)


def _hash(char: str) -> str:
    return "sha256:" + char * 64


def _blob(char: str) -> str:
    return char * 64


def _route() -> RouteLeaseRefV1:
    return RouteLeaseRefV1(
        seat=0,
        endpoint_id="conjecturer-primary",
        route_sha256="a" * 64,
    )


def _repair() -> LocalRepairPolicyV1:
    return LocalRepairPolicyV1.create(max_schema_repairs=2)


def _grant() -> CapabilityGrantV1:
    return CapabilityGrantV1.create(
        allowed_outcomes=(
            CapabilityOutcome.CANDIDATE_PROPOSAL,
            CapabilityOutcome.CONTEXT_REQUEST,
            CapabilityOutcome.ABSTENTION,
        ),
        max_candidates=3,
        max_local_repairs=2,
        remaining_context_expansions=1,
        max_extra_context_blocks=4,
        permitted_retrieval_channels=(RetrievalChannel.KEYWORD,),
    )


def _work_order(
    *,
    task_payload_ref: str | None = "payload:palimpsestic-phase-braid",
    task_payload_value=None,
):
    repair = _repair()
    return WorkOrderEnvelopeV1.create(
        manifest_digest="b" * 64,
        workflow_profile="conjecture.shadow.v1",
        formal_fence_seq=7,
        scratch_fence_seq=7,
        problem_ref="problem:open-semantic-mechanism",
        target_refs=(),
        school_id="school-0",
        route_lease=_route(),
        contract_id="conjecturer.legacy.v1",
        input_refs=("problem:open-semantic-mechanism",),
        advisory_context_ref=None,
        capability_grant=_grant(),
        budget_reservation_ref=_hash("c"),
        repair_policy_ref=repair.id,
        task_payload_schema_id="semantic.conjecture.payload.v941",
        task_payload_ref=task_payload_ref,
        task_payload_value=task_payload_value,
    )


def _proposal(work_order: WorkOrderEnvelopeV1 | None = None) -> ProposalReceiptV1:
    work_order = work_order or _work_order()
    return ProposalReceiptV1.create(
        work_order_id=work_order.id,
        source_call_seq=8,
        prompt_ref=_blob("d"),
        raw_ref=_blob("e"),
        contract_id=work_order.contract_id,
        route_lease=work_order.route_lease,
        validation_outcome=ProposalValidationOutcome.VALID_FIRST_ATTEMPT,
        attempt_count=1,
        candidate_payload_refs=(_hash("f"),),
        tokens=31,
    )


def _guard(
    work_order: WorkOrderEnvelopeV1 | None = None,
    proposal: ProposalReceiptV1 | None = None,
) -> GuardResultV1:
    work_order = work_order or _work_order()
    proposal = proposal or _proposal(work_order)
    finding = GuardFindingV1(
        candidate_ref=proposal.candidate_payload_refs[0],
        outcome=GuardFindingOutcome.ADMIT,
        code=GuardFindingCode.PASSED,
        related_refs=("artifact:novel-mobius-lattice",),
        detail="A bespoke Möbius-lattice mechanism passes the code-authored guard.",
    )
    return GuardResultV1.create(
        work_order_id=work_order.id,
        proposal_receipt_id=proposal.id,
        findings=(finding,),
        admitted_refs=(finding.candidate_ref,),
        rejected_refs=(),
        deduplicated_refs=(),
    )


def test_all_authority_models_are_closed_frozen_and_canonical():
    work = _work_order()
    proposal = _proposal(work)
    guard = _guard(work, proposal)
    transition = TransitionDecisionV1.create(
        manifest_digest=work.manifest_digest,
        workflow_profile=work.workflow_profile,
        previous_process_digest=_hash("1"),
        trigger_kind=TriggerKind.GUARD_RESULT,
        trigger_ref=guard.id,
        transition_kind=TransitionKind.PROPOSAL_ADMITTED,
        work_order_id=work.id,
        route_lease=work.route_lease,
        budget_delta=BudgetDeltaV1(
            reserved_tokens=proposal.tokens,
            spent_tokens=proposal.tokens,
        ),
        guard_result_ref=guard.id,
        output_refs=guard.admitted_refs,
        next_process_digest=_hash("2"),
    )
    stop = WorkflowStopDecisionV1.create(
        manifest_digest=work.manifest_digest,
        workflow_profile=work.workflow_profile,
        previous_process_digest=_hash("2"),
        policy_digest="3" * 64,
        metrics_ref=_hash("4"),
        deterministic_decision=StopDecision(stop=False),
        next_process_digest=_hash("5"),
    )
    values = (_repair(), _grant(), work, proposal, guard, transition, stop)

    for value in values:
        assert value.model_config.get("extra") == "forbid"
        assert value.model_config.get("frozen") is True
        with pytest.raises(ValidationError, match="extra|forbidden"):
            type(value).model_validate(
                {**value.model_dump(mode="json", by_alias=True), "route": "model-choice"}
            )
        with pytest.raises(ValidationError, match="frozen"):
            value.id = _hash("9")

        forged = value.model_dump(mode="json", by_alias=True)
        forged["id"] = _hash("8")
        with pytest.raises(ValidationError, match="canonical payload"):
            type(value).model_validate(forged)

    nested_values = (
        work.route_lease,
        transition.budget_delta,
        guard.findings[0],
    )
    for value in nested_values:
        assert value.model_config.get("extra") == "forbid"
        assert value.model_config.get("frozen") is True
        payload = value.model_dump(mode="json", by_alias=True)
        with pytest.raises(ValidationError, match="extra|forbidden"):
            type(value).model_validate({**payload, "route": "model-choice"})
        field = next(iter(type(value).model_fields))
        with pytest.raises(ValidationError, match="frozen"):
            setattr(value, field, getattr(value, field))


def test_work_order_references_open_semantics_without_embedding_role_schema():
    first = _work_order(task_payload_ref="payload:palimpsestic-phase-braid")
    second = _work_order(task_payload_ref="payload:unclassified-mobius-coupling")

    assert first.task_payload_schema_id == "semantic.conjecture.payload.v941"
    assert second.task_payload_ref.endswith("unclassified-mobius-coupling")
    assert first.route_lease == second.route_lease
    assert first.capability_grant == second.capability_grant
    assert first.formal_fence_seq == second.formal_fence_seq
    assert first.id != second.id

    payload = first.model_dump(mode="json", by_alias=True)
    payload["candidate_text"] = "Inline semantic prose must stay out of authority."
    with pytest.raises(ValidationError, match="candidate_text|extra"):
        WorkOrderEnvelopeV1.model_validate(payload)


def test_task_specific_semantics_remain_open_and_do_not_author_process_fields():
    payload = {
        "mechanism": "palimpsestic phase braid",
        "claim": "An unfamiliar semantic structure remains admissible.",
        "optional": {"analogy": None, "critic_vocabulary": ["sui generis"]},
    }
    work = _work_order(task_payload_ref=None, task_payload_value=payload)

    assert work.task_payload_value == payload
    assert work.route_lease == _route()
    assert work.capability_grant == _grant()
    with pytest.raises(TypeError):
        work.task_payload_value["route_lease"] = "model-selected"


@pytest.mark.parametrize(
    ("model", "field", "value"),
    (
        (CapabilityGrantV1, "allowed_outcomes", ["delegate_provider"]),
        (TransitionDecisionV1, "transition_kind", "skip_guard_and_accept"),
        (TransitionDecisionV1, "trigger_kind", "model_prose"),
    ),
)
def test_authority_enums_are_closed(model, field: str, value):
    if model is CapabilityGrantV1:
        payload = _grant().model_dump(mode="json", by_alias=True)
    else:
        work = _work_order()
        proposal = _proposal(work)
        guard = _guard(work, proposal)
        payload = TransitionDecisionV1.create(
            manifest_digest=work.manifest_digest,
            workflow_profile=work.workflow_profile,
            previous_process_digest=_hash("1"),
            trigger_kind=TriggerKind.GUARD_RESULT,
            trigger_ref=guard.id,
            transition_kind=TransitionKind.PROPOSAL_ADMITTED,
            work_order_id=work.id,
            route_lease=work.route_lease,
            guard_result_ref=guard.id,
            output_refs=guard.admitted_refs,
            next_process_digest=_hash("2"),
        ).model_dump(mode="json", by_alias=True)
    payload[field] = value
    with pytest.raises(ValidationError, match=field):
        model.model_validate(payload)


def test_proposal_receipt_cannot_author_transition_route_budget_or_status():
    proposal = _proposal()
    for field, value in (
        ("next_transition", "proposal_admitted"),
        ("status", "accepted"),
        ("budget", {"tokens": 1_000_000}),
        ("provider", "alternate"),
    ):
        payload = proposal.model_dump(mode="json", by_alias=True)
        payload[field] = value
        with pytest.raises(ValidationError, match=f"{field}|extra"):
            ProposalReceiptV1.model_validate(payload)


@pytest.mark.parametrize(
    ("outcome", "code"),
    (
        (GuardFindingOutcome.ADMIT, GuardFindingCode.BATTERY_EQUIVALENT),
        (GuardFindingOutcome.REJECT, GuardFindingCode.PASSED),
        (GuardFindingOutcome.DEDUPLICATE, GuardFindingCode.PASSED),
    ),
)
def test_guard_finding_codes_cannot_launder_disposition(outcome, code):
    with pytest.raises(ValidationError, match="passed|deduplication"):
        GuardFindingV1(
            candidate_ref=_hash("6"),
            outcome=outcome,
            code=code,
        )


def test_transition_output_references_are_unique():
    work = _work_order()
    with pytest.raises(ValidationError, match="output references"):
        TransitionDecisionV1.create(
            manifest_digest=work.manifest_digest,
            workflow_profile=work.workflow_profile,
            previous_process_digest=_hash("1"),
            trigger_kind=TriggerKind.CONTEXT_PREPARED,
            trigger_ref=work.id,
            transition_kind=TransitionKind.WORK_ISSUED,
            work_order_id=work.id,
            route_lease=work.route_lease,
            output_refs=(_hash("7"), _hash("7")),
            next_process_digest=_hash("2"),
        )
