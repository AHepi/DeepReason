"""Controller-v3 orchestration for transactional provider work."""

from __future__ import annotations

import hashlib
from collections.abc import Iterable
from dataclasses import dataclass
from typing import Any

from deepreason.llm.budget import (
    TokenBudgetExceeded,
    TokenMeter,
    conservative_prompt_bound,
)
from deepreason.ontology.event import LLMCall
from deepreason.run_manifest import RunManifest
from deepreason.workflow.models import RouteLeaseRefV1, WorkflowTaskKind
from deepreason.workflow.transaction import (
    AuthorizedDispatch,
    ContextExposureReceiptV2,
    ContextPackPlanV1,
    DispatchAuthorizationBundleV1,
    ProviderAttemptV1,
    SemanticAdmissionV1,
    TokenReservationV2,
    VisibleContextItemV1,
    WorkBudgetDenied,
    WorkLifecycleTransitionV1,
    WorkPreparationV1,
    WorkTerminalV1,
    WorkTransitionKind,
)


@dataclass(frozen=True)
class TransactionRepairResult:
    """A schema-valid repair whose domain admission is still caller-owned."""

    output: Any
    llm_call: LLMCall
    preparation: WorkPreparationV1
    authorized: AuthorizedDispatch
    provider_attempt: ProviderAttemptV1


class InquiryTransactionService:
    """Persist, authorize, settle, and recover RunManifest-v6 model work."""

    def __init__(
        self,
        harness,
        manifest: RunManifest,
        meter: TokenMeter,
        *,
        meter_scope: str = "provider-global",
    ) -> None:
        if manifest.schema_version != 6:
            raise ValueError("transaction service requires RunManifest v6")
        control = manifest.control_plane_policy
        if control is None or control.controller_version != "workflow.controller.v3":
            raise ValueError("transaction service requires workflow.controller.v3")
        self.harness = harness
        self.manifest = manifest
        self.meter = meter
        self.meter_scope = meter_scope

    def prepare(
        self,
        *,
        task_kind: WorkflowTaskKind,
        attempt_index: int,
        route_lease: RouteLeaseRefV1,
        contract_id: str,
        trigger_ref: str,
        formal_fence_seq: int,
        scratch_fence_seq: int,
        target_refs: tuple[str, ...] = (),
        input_refs: tuple[str, ...] = (),
        task_payload_ref: str | None = None,
        task_payload_value: Any | None = None,
    ) -> WorkPreparationV1:
        preparation = WorkPreparationV1.create(
            manifest_digest=self.manifest.sha256,
            task_kind=task_kind,
            attempt_index=attempt_index,
            formal_fence_seq=formal_fence_seq,
            scratch_fence_seq=scratch_fence_seq,
            trigger_ref=trigger_ref,
            target_refs=target_refs,
            input_refs=input_refs,
            route_lease=route_lease,
            contract_id=contract_id,
            task_payload_ref=task_payload_ref,
            task_payload_value=task_payload_value,
        )
        transition = WorkLifecycleTransitionV1.create(
            work_id=preparation.id,
            attempt_index=attempt_index,
            transition_kind=WorkTransitionKind.WORK_PREPARED,
            trigger_ref=trigger_ref,
        )
        self.harness.record_transaction_transition(
            transition,
            records=(preparation,),
        )
        return preparation

    @staticmethod
    def context_plan(
        preparation: WorkPreparationV1,
        *,
        plan_kind: str,
        items: Iterable[VisibleContextItemV1],
        maximum_bytes: int,
        rendered_bytes: int,
    ) -> ContextPackPlanV1:
        return ContextPackPlanV1.create(
            work_id=preparation.id,
            attempt_index=preparation.attempt_index,
            plan_kind=plan_kind,
            items=tuple(items),
            maximum_bytes=maximum_bytes,
            rendered_bytes=rendered_bytes,
        )

    def issue(
        self,
        preparation: WorkPreparationV1,
        *,
        plans: Iterable[ContextPackPlanV1],
        prompt: str,
        max_tokens: int,
    ) -> AuthorizedDispatch:
        """Reserve and atomically expose one request, or durably deny it."""

        plans = tuple(plans)
        if any(
            plan.work_id != preparation.id or plan.attempt_index != preparation.attempt_index
            for plan in plans
        ):
            raise ValueError("context plans belong to another work attempt")
        prompt_sha256 = hashlib.sha256(prompt.encode("utf-8")).hexdigest()
        prompt_bound = conservative_prompt_bound(prompt)
        try:
            reservation = self.meter.reserve(
                prompt_text=prompt,
                max_tokens=max_tokens,
            )
        except TokenBudgetExceeded as error:
            terminal = WorkTerminalV1.create(
                work_id=preparation.id,
                attempt_index=preparation.attempt_index,
                status="budget_denied",
                usage_status="exact",
                prompt_tokens=0,
                completion_tokens=0,
                reason_code="token_budget_denied",
            )
            transition = WorkLifecycleTransitionV1.create(
                work_id=preparation.id,
                attempt_index=preparation.attempt_index,
                transition_kind=WorkTransitionKind.BUDGET_DENIED,
                trigger_ref="budget-denied:token-budget",
            )
            self.harness.record_transaction_transition(
                transition,
                records=(terminal,),
            )
            raise WorkBudgetDenied(terminal) from error

        try:
            reservation_record = TokenReservationV2.create(
                work_id=preparation.id,
                attempt_index=preparation.attempt_index,
                meter_scope=self.meter_scope,
                prompt_sha256=prompt_sha256,
                prompt_bound_tokens=prompt_bound,
                completion_bound_tokens=int(max_tokens),
                reserved_tokens=reservation.amount,
            )
            exposure = ContextExposureReceiptV2.create(
                work_id=preparation.id,
                attempt_index=preparation.attempt_index,
                prompt_sha256=prompt_sha256,
                context_plan_refs=tuple(plan.id for plan in plans),
                exposed_items=tuple(item for plan in plans for item in plan.items),
            )
            transition = WorkLifecycleTransitionV1.create(
                work_id=preparation.id,
                attempt_index=preparation.attempt_index,
                transition_kind=WorkTransitionKind.WORK_ISSUED,
                trigger_ref=exposure.id,
            )
            bundle = DispatchAuthorizationBundleV1.create(
                work_id=preparation.id,
                attempt_index=preparation.attempt_index,
                contract_id=preparation.contract_id,
                route_lease=preparation.route_lease,
                prompt_sha256=prompt_sha256,
                reservation_ref=reservation_record.id,
                exposure_receipt_ref=exposure.id,
                issue_transition_ref=transition.id,
            )
            self.harness.record_transaction_transition(
                transition,
                records=(*plans, reservation_record, exposure, bundle),
            )
        except BaseException:
            # The reservation exists only in memory until the issue append.
            # Immutable object writes from a failed append remain unreachable.
            reservation.release()
            raise
        return AuthorizedDispatch(
            preparation=preparation,
            reservation_record=reservation_record,
            exposure_receipt=exposure,
            bundle=bundle,
            reservation=reservation,
        )

    def record_provider_attempt(
        self,
        authorized: AuthorizedDispatch,
        *,
        call: LLMCall,
        outcome: str,
        usage_status: str,
        prompt_tokens: int | None = None,
        completion_tokens: int | None = None,
        diagnostic_ref: str | None = None,
    ) -> ProviderAttemptV1:
        bundle = authorized.bundle
        if call.work_order_id != bundle.work_id:
            raise ValueError("provider call belongs to another work item")
        if usage_status == "exact":
            prompt_tokens = call.prompt_tokens if prompt_tokens is None else prompt_tokens
            completion_tokens = (
                call.completion_tokens if completion_tokens is None else completion_tokens
            )
        attempt = ProviderAttemptV1.create(
            work_id=bundle.work_id,
            attempt_index=bundle.attempt_index,
            authorization_bundle_ref=bundle.id,
            contract_id=bundle.contract_id,
            route_lease=bundle.route_lease,
            prompt_sha256=bundle.prompt_sha256,
            raw_ref=call.raw_ref or None,
            outcome=outcome,
            usage_status=usage_status,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            diagnostic_ref=diagnostic_ref,
        )
        transition = WorkLifecycleTransitionV1.create(
            work_id=bundle.work_id,
            attempt_index=bundle.attempt_index,
            transition_kind=WorkTransitionKind.PROVIDER_RESULT,
            trigger_ref=attempt.id,
        )
        self.harness.record_transaction_transition(
            transition,
            records=(attempt,),
            llm=call,
        )
        return attempt

    def record_semantic_admission(
        self,
        provider_attempt: ProviderAttemptV1,
        *,
        outcome: str,
        admitted_refs: tuple[str, ...] = (),
        diagnostic_refs: tuple[str, ...] = (),
        authorized_pointers: tuple[str, ...] = (),
    ) -> SemanticAdmissionV1:
        admission = SemanticAdmissionV1.create(
            work_id=provider_attempt.work_id,
            attempt_index=provider_attempt.attempt_index,
            provider_attempt_ref=provider_attempt.id,
            outcome=outcome,
            admitted_refs=admitted_refs,
            diagnostic_refs=diagnostic_refs,
            authorized_pointers=authorized_pointers,
        )
        transition = WorkLifecycleTransitionV1.create(
            work_id=provider_attempt.work_id,
            attempt_index=provider_attempt.attempt_index,
            transition_kind=WorkTransitionKind.SEMANTIC_ADMISSION,
            trigger_ref=provider_attempt.id,
        )
        self.harness.record_transaction_transition(
            transition,
            records=(admission,),
        )
        return admission

    def terminate(
        self,
        *,
        work_id: str,
        attempt_index: int,
        status: str,
        reason_code: str,
        usage_status: str,
        prompt_tokens: int | None = None,
        completion_tokens: int | None = None,
        provider_attempt: ProviderAttemptV1 | None = None,
        admission: SemanticAdmissionV1 | None = None,
    ) -> WorkTerminalV1:
        terminal = WorkTerminalV1.create(
            work_id=work_id,
            attempt_index=attempt_index,
            status=status,
            usage_status=usage_status,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            provider_attempt_ref=(provider_attempt.id if provider_attempt else None),
            semantic_admission_ref=(admission.id if admission else None),
            reason_code=reason_code,
        )
        transition = WorkLifecycleTransitionV1.create(
            work_id=work_id,
            attempt_index=attempt_index,
            transition_kind=WorkTransitionKind.WORK_TERMINATED,
            trigger_ref=terminal.id,
        )
        self.harness.record_transaction_transition(
            transition,
            records=(terminal,),
        )
        return terminal

    def repair_schema_failure(self, **kwargs) -> TransactionRepairResult:
        """Run bounded repair with fresh authority for every provider call."""

        from deepreason.workflow.repair_transaction import (
            repair_schema_failure,
        )

        return repair_schema_failure(self, **kwargs)

    def recover_incomplete(self) -> tuple[ProviderAttemptV1, ...]:
        """Close non-dispatchable gaps and return results needing validation.

        Issued work is never dispatched again.  A durable raw provider result
        is instead returned to the caller so deterministic contract validation
        can resume from the stored bytes.
        """

        pending_admission: list[ProviderAttemptV1] = []
        for work_id, item in tuple(self.harness.workflow_state.transaction_work.items()):
            if item.terminal is not None:
                continue
            attempt_index = item.preparation.attempt_index
            provider = item.provider_attempts.get(attempt_index)
            admission = item.admissions.get(attempt_index)
            if not item.issued:
                self.terminate(
                    work_id=work_id,
                    attempt_index=attempt_index,
                    status="abandoned",
                    reason_code="prepared_unissued_recovery",
                    usage_status="exact",
                    prompt_tokens=0,
                    completion_tokens=0,
                )
            elif provider is None:
                self.terminate(
                    work_id=work_id,
                    attempt_index=attempt_index,
                    status="abandoned",
                    reason_code="issued_result_unknown_recovery",
                    usage_status="unknown",
                )
            elif admission is None:
                pending_admission.append(provider)
            else:
                status = {
                    "admitted": "completed",
                    "schema_exhausted": "schema_exhausted",
                    "rejected": "rejected",
                    "unrepairable": "rejected",
                }[admission.outcome]
                self.terminate(
                    work_id=work_id,
                    attempt_index=attempt_index,
                    status=status,
                    reason_code=f"recovered_{admission.outcome}",
                    usage_status=provider.usage_status,
                    prompt_tokens=provider.prompt_tokens,
                    completion_tokens=provider.completion_tokens,
                    provider_attempt=provider,
                    admission=admission,
                )
        return tuple(pending_admission)


__all__ = ["InquiryTransactionService", "TransactionRepairResult"]
