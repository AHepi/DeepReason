"""Controller-v3 orchestration for transactional provider work."""

from __future__ import annotations

import hashlib
from collections.abc import Iterable
from dataclasses import dataclass
from typing import Any

from deepreason.llm.budget import (
    Reservation,
    TokenBudgetExceeded,
    TokenMeter,
    conservative_prompt_bound,
)
from deepreason.ontology.event import LLMCall
from deepreason.run_manifest import (
    ContractSchemaRepairGrantV1,
    RunManifest,
    RunManifestError,
    resolve_route_seat_behavioral_capability,
    resolve_route_seat_base_profile,
)
from deepreason.workflow.models import RouteLeaseRefV1, WorkflowTaskKind
from deepreason.workflow.transaction import (
    AuthorizedDispatch,
    CompactRecoveryTransitionV1,
    ContextExposureReceiptV2,
    ContextPackPlanV1,
    DispatchAuthorizationBundleV1,
    ProviderAttemptV1,
    RouteSeatInsufficientCapabilityV1,
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


@dataclass(frozen=True)
class ReservedDispatch:
    """Runtime-only token authority awaiting durable issue finalization."""

    preparation: WorkPreparationV1
    reservation_record: TokenReservationV2
    reservation: Reservation

    def release(self) -> None:
        if self.reservation.is_open:
            self.reservation.release()


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
        if manifest.route_seat_behavioral_capability_plan is None:
            raise RunManifestError(
                "V6_BEHAVIORAL_CAPABILITY_PLAN_REQUIRED",
                "transactional execution requires route-seat behavioral authority",
                "/route_seat_behavioral_capability_plan",
            )
        self.harness = harness
        self.manifest = manifest
        self.meter = meter
        self.meter_scope = meter_scope
        self.harness.bind_transaction_manifest(manifest)

    def resolve_schema_repair_grant(
        self,
        contract_id: str,
    ) -> ContractSchemaRepairGrantV1 | None:
        """Resolve only manifest-frozen repair authority for one exact contract."""

        policy = self.manifest.contract_schema_repair_policy
        if policy is None:
            return None
        return next(
            (grant for grant in policy.grants if grant.contract_id == contract_id),
            None,
        )

    def _compact_recovery_transition(
        self,
        *,
        work_id: str,
        attempt_index: int,
        status: str,
        provider_attempt: ProviderAttemptV1 | None,
        admission: SemanticAdmissionV1 | None,
    ) -> tuple[CompactRecoveryTransitionV1 | None, bool]:
        """Return the canonical route-seat transition and whether it is new."""

        policy = self.manifest.compact_recovery_policy
        if status != "schema_exhausted" or policy is None:
            return None, False
        item = self.harness.workflow_state.transaction_work.get(work_id)
        source_profile = (
            resolve_route_seat_base_profile(
                self.manifest,
                role=item.preparation.route_lease.role,
                seat=item.preparation.route_lease.seat,
                endpoint_id=item.preparation.route_lease.endpoint_id,
            )
            if item is not None
            else None
        )
        if source_profile not in policy.source_profiles:
            return None, False
        canonical_attempt = (
            item.provider_attempts.get(attempt_index) if item is not None else None
        )
        canonical_admission = (
            item.admissions.get(attempt_index) if item is not None else None
        )
        if (
            item is None
            or item.preparation.attempt_index != attempt_index
            or provider_attempt is None
            or admission is None
            or canonical_attempt is None
            or canonical_admission is None
            or provider_attempt.id != canonical_attempt.id
            or admission.id != canonical_admission.id
        ):
            raise ValueError(
                "schema exhaustion lacks canonical provider admission authority"
            )
        key = self.harness.workflow_state._route_seat_key(
            item.preparation.route_lease
        )
        existing = self.harness.workflow_state.compact_recovery_by_route_seat.get(
            key
        )
        if existing is not None:
            return existing, False
        compact = CompactRecoveryTransitionV1.create(
            manifest_digest=self.manifest.sha256,
            work_id=work_id,
            attempt_index=attempt_index,
            route_lease=item.preparation.route_lease,
            source_profile=source_profile,
            target_profile=policy.target_profile,
            trigger=policy.trigger,
            scope=policy.scope,
            sticky=policy.sticky,
            applies_to=policy.applies_to,
            retry_failed_work=policy.retry_failed_work,
            semantic_admission_ref=admission.id,
        )
        self.harness.workflow_state._validate_compact_transition(
            compact, item, provider_attempt, admission
        )
        return compact, True

    def _require_open_preparation(
        self,
        preparation: WorkPreparationV1,
    ) -> None:
        if preparation.manifest_digest != self.manifest.sha256:
            raise ValueError("work preparation belongs to another manifest")
        item = self.harness.workflow_state.transaction_work.get(preparation.id)
        if item is None or item.preparation != preparation:
            raise ValueError("work preparation is not canonical in this root")
        if (
            self.harness.workflow_state._route_seat_key(preparation.route_lease)
            in self.harness.workflow_state.insufficient_capability_by_route_seat
        ):
            raise RunManifestError(
                "V6_ROUTE_SEAT_INSUFFICIENT_CAPABILITY",
                "route seat has terminally exhausted its smallest authorized contract",
                "/workflow/insufficient_capability_by_route_seat",
            )
        if item.issued or item.terminal is not None:
            raise ValueError("work preparation is no longer open for dispatch")

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
        source_terminal_commitment_ref: str | None = None,
        task_payload_ref: str | None = None,
        task_payload_value: Any | None = None,
    ) -> WorkPreparationV1:
        classification = self.harness.workflow_state.route_seat_model_classification
        if classification is None:
            raise RunManifestError(
                "V6_MODEL_CLASSIFICATION_REQUIRED",
                "transactional execution requires durable route-seat classification",
                "/route_seat_model_classification",
            )
        self.harness.workflow_state._validate_model_classification(
            self.manifest,
            classification,
        )
        current_terminal = self.harness.workflow_state.current_terminal_commitment
        if (
            source_terminal_commitment_ref is None
            and task_kind == WorkflowTaskKind.REPAIR
            and isinstance(task_payload_value, dict)
            and isinstance(task_payload_value.get("parent_work_id"), str)
        ):
            parent = self.harness.workflow_state.transaction_work.get(
                task_payload_value["parent_work_id"]
            )
            if parent is not None:
                source_terminal_commitment_ref = (
                    parent.preparation.source_terminal_commitment_ref
                )
        if current_terminal is not None:
            if source_terminal_commitment_ref != current_terminal.id:
                raise RunManifestError(
                    "V6_TERMINAL_COMMITMENT_REQUIRED",
                    "post-terminal work requires the exact current commitment",
                    "/workflow/current_terminal_commitment",
                )
        elif source_terminal_commitment_ref is not None:
            raise RunManifestError(
                "V6_TERMINAL_COMMITMENT_FOREIGN",
                "work cannot name terminal authority before it exists",
                "/workflow/current_terminal_commitment",
            )
        route_key = self.harness.workflow_state._route_seat_key(route_lease)
        if (
            route_key
            in self.harness.workflow_state.insufficient_capability_by_route_seat
        ):
            raise RunManifestError(
                "V6_ROUTE_SEAT_INSUFFICIENT_CAPABILITY",
                "route seat has terminally exhausted its smallest authorized contract",
                "/workflow/insufficient_capability_by_route_seat",
            )
        behavioral = resolve_route_seat_behavioral_capability(
            self.manifest,
            role=route_lease.role,
            seat=route_lease.seat,
            endpoint_id=route_lease.endpoint_id,
            route_sha256=route_lease.route_sha256,
        )
        if contract_id not in {
            grant.contract_id for grant in behavioral.contracts
        }:
            raise RunManifestError(
                "V6_BEHAVIORAL_CONTRACT_NOT_AUTHORIZED",
                f"contract {contract_id} is not frozen for "
                f"{route_lease.role}[{route_lease.seat}]",
                "/route_seat_behavioral_capability_plan/entries",
            )
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
            source_terminal_commitment_ref=source_terminal_commitment_ref,
            task_payload_ref=task_payload_ref,
            task_payload_value=task_payload_value,
        )
        if current_terminal is not None:
            from deepreason.runtime.terminal_authority import (
                is_commitment_bound_bridge_work,
            )

            if not is_commitment_bound_bridge_work(
                self.harness.workflow_state,
                preparation,
                current_terminal.id,
            ):
                raise RunManifestError(
                    "V6_POST_TERMINAL_WORK_FORBIDDEN",
                    "post-terminal work must be an exact commitment-bound bridge descendant",
                    "/workflow/current_terminal_commitment",
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

        reserved = self.reserve_dispatch(
            preparation,
            prompt=prompt,
            max_tokens=max_tokens,
        )
        return self.finalize_dispatch(
            reserved,
            plans=plans,
            prompt=prompt,
        )

    def reserve_dispatch(
        self,
        preparation: WorkPreparationV1,
        *,
        prompt: str,
        max_tokens: int,
    ) -> ReservedDispatch:
        """Acquire canonical token authority without exposing model context."""

        self._require_open_preparation(preparation)
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
        except BaseException:
            reservation.release()
            raise
        return ReservedDispatch(
            preparation=preparation,
            reservation_record=reservation_record,
            reservation=reservation,
        )

    def finalize_dispatch(
        self,
        reserved: ReservedDispatch,
        *,
        plans: Iterable[ContextPackPlanV1],
        prompt: str,
    ) -> AuthorizedDispatch:
        """Append the ordinary exposure and authorization for one reservation."""

        preparation = reserved.preparation
        reservation_record = reserved.reservation_record
        try:
            self._require_open_preparation(preparation)
        except BaseException:
            reserved.release()
            raise
        plans = tuple(plans)
        if any(
            plan.work_id != preparation.id or plan.attempt_index != preparation.attempt_index
            for plan in plans
        ):
            reserved.release()
            raise ValueError("context plans belong to another work attempt")
        prompt_sha256 = hashlib.sha256(prompt.encode("utf-8")).hexdigest()
        if reservation_record.prompt_sha256 != prompt_sha256:
            reserved.release()
            raise ValueError("reserved prompt differs from dispatch prompt")
        if not reserved.reservation.is_open:
            raise ValueError("dispatch reservation is no longer open")

        try:
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
            reserved.release()
            raise
        return AuthorizedDispatch(
            preparation=preparation,
            reservation_record=reservation_record,
            exposure_receipt=exposure,
            bundle=bundle,
            reservation=reserved.reservation,
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
        if (
            self.harness.workflow_state._route_seat_key(bundle.route_lease)
            in self.harness.workflow_state.insufficient_capability_by_route_seat
        ):
            raise RunManifestError(
                "V6_ROUTE_SEAT_INSUFFICIENT_CAPABILITY",
                "route seat has terminally exhausted its smallest authorized contract",
                "/workflow/insufficient_capability_by_route_seat",
            )
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
        compact, compact_is_new = self._compact_recovery_transition(
            work_id=work_id,
            attempt_index=attempt_index,
            status=status,
            provider_attempt=provider_attempt,
            admission=admission,
        )
        insufficient = None
        if status == "schema_exhausted":
            fields = self.harness.workflow_state.insufficient_capability_fields(
                work_id,
                attempt_index,
            )
            if fields is not None:
                if compact_is_new and compact is not None:
                    fields = {
                        **fields,
                        "compact_recovery_transition_refs": tuple(
                            dict.fromkeys(
                                (
                                    *fields["compact_recovery_transition_refs"],
                                    compact.id,
                                )
                            )
                        ),
                    }
                insufficient = RouteSeatInsufficientCapabilityV1.create(**fields)
        terminal = WorkTerminalV1.create(
            work_id=work_id,
            attempt_index=attempt_index,
            status=status,
            usage_status=usage_status,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            provider_attempt_ref=(provider_attempt.id if provider_attempt else None),
            semantic_admission_ref=(admission.id if admission else None),
            compact_recovery_transition_ref=(compact.id if compact else None),
            insufficient_capability_ref=(
                insufficient.id if insufficient is not None else None
            ),
            reason_code=reason_code,
        )
        transition = WorkLifecycleTransitionV1.create(
            work_id=work_id,
            attempt_index=attempt_index,
            transition_kind=WorkTransitionKind.WORK_TERMINATED,
            trigger_ref=terminal.id,
        )
        records = []
        if compact_is_new and compact is not None:
            records.append(compact)
        if insufficient is not None:
            records.append(insufficient)
        records.append(terminal)
        self.harness.record_transaction_transition(transition, records=tuple(records))
        return terminal

    def repair_schema_failure(self, **kwargs) -> TransactionRepairResult:
        """Run bounded repair with fresh authority for every provider call."""

        authorized = kwargs.get("authorized")
        if authorized is None:
            raise ValueError("schema repair requires parent transaction authority")
        route_lease = authorized.preparation.route_lease
        base_profile = resolve_route_seat_base_profile(
            self.manifest,
            role=route_lease.role,
            seat=route_lease.seat,
            endpoint_id=route_lease.endpoint_id,
        )
        requested = kwargs.get("model_profile")
        if requested is not None:
            from deepreason.llm.adapter import V6ModelProfileOverrideForbidden
            from deepreason.llm.profiles import get_profile

            try:
                requested = get_profile(requested).name.value
            except (KeyError, TypeError, ValueError) as error:
                raise V6ModelProfileOverrideForbidden(
                    role=route_lease.role,
                    frozen_profile=base_profile,
                ) from error
            if requested != base_profile:
                raise V6ModelProfileOverrideForbidden(
                    role=route_lease.role,
                    frozen_profile=base_profile,
                )
        kwargs["model_profile"] = base_profile
        from deepreason.workflow.repair_transaction import (
            repair_schema_failure,
        )

        try:
            return repair_schema_failure(self, **kwargs)
        except Exception as error:
            from deepreason.llm.repair import SchemaRepairError

            if isinstance(error, SchemaRepairError):
                exhausted = [
                    item
                    for item in self.harness.workflow_state.transaction_work.values()
                    if item.terminal is not None
                    and item.terminal.status == "schema_exhausted"
                    and item.preparation.contract_id
                    == authorized.preparation.contract_id
                    and item.preparation.route_lease == route_lease
                ]
                if exhausted:
                    exhausted.sort(key=lambda item: item.event_seqs[-1])
                    error.source_work_id = exhausted[-1].preparation.id
            raise

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
