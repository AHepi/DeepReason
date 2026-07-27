"""Separately authorized RunManifest-v6 schema repair transactions."""

from __future__ import annotations

import hashlib
import re
from typing import Any

from pydantic import BaseModel

from deepreason.canonical import canonical_json
from deepreason.llm.endpoints import EndpointError
from deepreason.llm.firewall import route_fingerprint
from deepreason.llm.repair import (
    RepairPatchV1,
    SchemaExhaustedError,
    SchemaRepairError,
    UnrepairableDiagnosticError,
    V6PatchRepairSession,
)
from deepreason.llm.wire import RepairPatchWireContract
from deepreason.workflow.models import WorkflowTaskKind
from deepreason.workflow.transaction import (
    ContextNamespace,
    VisibleContextItemV1,
    WorkBudgetDenied,
)
from deepreason.workflow.transaction_service import TransactionRepairResult


class _PointerValidationError(ValueError):
    """Give legacy field diagnostics finite v6 patch authority."""

    code = "extra_forbidden"

    def __init__(self, message: str, pointer: str) -> None:
        super().__init__(message)
        self.pointer = pointer
        self.repair_scope = pointer
        self.authorized_pointers = (pointer,)


def _finite_error(error: Exception) -> Exception:
    """Recover a pointer only from the wire layer's exact field diagnostic."""

    if getattr(error, "pointer", "") or getattr(error, "authorized_pointers", ()):
        return error
    matched = re.fullmatch(r"extra field at (?P<pointer>/.*)", str(error))
    if matched is not None:
        return _PointerValidationError(str(error), matched.group("pointer"))
    return error


def _record_bytes(harness, value: BaseModel | dict[str, Any]) -> tuple[str, bytes]:
    payload = (
        value.model_dump(mode="json", by_alias=True, exclude_none=True)
        if isinstance(value, BaseModel)
        else value
    )
    data = canonical_json(payload)
    return harness.blobs.put(data), data


def _diagnostic_refs(*values: str | None) -> tuple[str, ...]:
    return tuple(dict.fromkeys(value for value in values if value))


def _raw_text(harness, call) -> str:
    if not call.raw_ref:
        raise ValueError("schema failure has no durable provider result")
    return harness.blobs.get(call.raw_ref).decode("utf-8")


def _assess(
    session: V6PatchRepairSession,
    turn,
    raw: str,
    parent_contract,
):
    """Apply one response and either compile output or derive finite authority."""

    try:
        candidate = session.candidate_from_raw(turn, raw)
    except (TypeError, ValueError) as error:
        diagnostic = session.note_invalid(turn, raw, _finite_error(error))
        return None, diagnostic
    try:
        wire = parent_contract.validate_value(candidate)
        return parent_contract.compile(wire), None
    except (TypeError, ValueError) as error:
        diagnostic = session.note_invalid(turn, raw, _finite_error(error))
        return None, diagnostic


def _terminalize_invalid(
    service,
    authorized,
    call,
    *,
    diagnostic_ref: str | None,
    admission_outcome: str,
    admission_diagnostic_refs: tuple[str, ...],
    authorized_pointers: tuple[str, ...],
    reason_code: str,
):
    provider = service.record_provider_attempt(
        authorized,
        call=call,
        outcome="provider_result",
        usage_status="exact",
        diagnostic_ref=diagnostic_ref,
    )
    admission = service.record_semantic_admission(
        provider,
        outcome=admission_outcome,
        diagnostic_refs=admission_diagnostic_refs,
        authorized_pointers=authorized_pointers,
    )
    status = "schema_exhausted" if admission_outcome == "schema_exhausted" else "rejected"
    service.terminate(
        work_id=authorized.preparation.id,
        attempt_index=authorized.preparation.attempt_index,
        status=status,
        reason_code=reason_code,
        usage_status="exact",
        prompt_tokens=call.prompt_tokens,
        completion_tokens=call.completion_tokens,
        provider_attempt=provider,
        admission=admission,
    )
    return provider


def _raise_exhausted(
    session: V6PatchRepairSession,
    message: str | None = None,
    *,
    spend=None,
):
    error = (
        SchemaExhaustedError(message, spend=spend)
        if message is not None
        else session.exhaustion_error(spend=spend)
    )
    error.transaction_terminalized = True
    raise error


def repair_schema_failure(
    service,
    *,
    adapter,
    authorized,
    error: SchemaRepairError,
    role: str,
    pack: str,
    output_model: type[BaseModel],
    wire_contract,
    endpoint_index: int = 0,
    template_role: str | None = None,
    model_profile: str | None = None,
    output_mechanism=None,
    endpoint_lease=None,
    preserve_terminalized_spend: bool = False,
    school_id: str | None = None,
    root_authorized_pointers: tuple[str, ...] = (),
    reason_prefix: str = "schema",
) -> TransactionRepairResult:
    """Repair one invalid v6 result through independently issued work items.

    The failed parent result is first made durable and terminal. Every model-
    facing correction then gets a fresh preparation, token reservation,
    exposure receipt, authorization bundle, provider result, and typed
    terminal. A schema-valid final repair is returned without semantic
    admission so the owning domain service can still perform its deterministic
    semantic checks.
    """

    parent = authorized.preparation
    if wire_contract.contract_id != parent.contract_id:
        raise ValueError("repair contract differs from its parent authority")
    if (
        authorized.bundle.contract_id != parent.contract_id
        or authorized.bundle.route_lease != parent.route_lease
    ):
        raise ValueError("repair parent authorization differs from its preparation")
    if endpoint_lease is None:
        raise ValueError("repair requires the parent's frozen endpoint lease")
    if (
        endpoint_lease.role != parent.route_lease.role
        or endpoint_lease.seat != parent.route_lease.seat
        or endpoint_lease.route.endpoint_id != parent.route_lease.endpoint_id
        or route_fingerprint(endpoint_lease.route) != parent.route_lease.route_sha256
    ):
        raise ValueError("repair endpoint lease differs from its parent authority")
    spend = getattr(error, "spend", None)
    if spend is None:
        raise ValueError("schema failure has no durable provider spend") from error
    if spend.work_order_id != parent.id or spend.attempts != 1:
        raise ValueError("v6 parent call used unbound or internal repair authority")

    grant = service.resolve_schema_repair_grant(parent.contract_id)
    maximum_repairs = grant.maximum_schema_repairs if grant is not None else 0
    initial_request = service.harness.blobs.get(spend.prompt_ref).decode("utf-8")
    exhaustion_spend = spend if preserve_terminalized_spend else None
    session = V6PatchRepairSession(
        contract=parent.contract_id,
        schema=wire_contract.model_json_schema(),
        initial_request=initial_request,
        retry_max=maximum_repairs,
        root_authorized_pointers=root_authorized_pointers,
    )
    initial_turn = session.turn(0)
    initial_raw = _raw_text(service.harness, spend)
    original_diagnostic_ref = (
        spend.attempt_trace[-1].diagnostic_ref if spend.attempt_trace else None
    )

    try:
        unexpected_output, diagnostic = _assess(
            session,
            initial_turn,
            initial_raw,
            wire_contract,
        )
    except UnrepairableDiagnosticError as unrepairable:
        unrepairable_ref, _ = _record_bytes(
            service.harness,
            {
                "schema": "repair.unrepairable.v1",
                "contract": parent.contract_id,
                "message": str(unrepairable)[:500],
            },
        )
        _terminalize_invalid(
            service,
            authorized,
            spend,
            diagnostic_ref=original_diagnostic_ref or unrepairable_ref,
            admission_outcome="schema_exhausted",
            admission_diagnostic_refs=_diagnostic_refs(original_diagnostic_ref, unrepairable_ref),
            authorized_pointers=(),
            reason_code=f"{reason_prefix}_unrepairable",
        )
        error.spend = None
        _raise_exhausted(
            session,
            "schema_exhausted: diagnostic is not finitely repairable",
            spend=exhaustion_spend,
        )
    if unexpected_output is not None or diagnostic is None:
        raise ValueError("adapter rejected an output that revalidates successfully")

    diagnostic_ref, _ = _record_bytes(service.harness, diagnostic)
    pointers = tuple(getattr(diagnostic, "authorized_pointers", ()))
    initial_provider = _terminalize_invalid(
        service,
        authorized,
        spend,
        diagnostic_ref=original_diagnostic_ref or diagnostic_ref,
        admission_outcome=("schema_exhausted" if maximum_repairs == 0 else "rejected"),
        admission_diagnostic_refs=_diagnostic_refs(original_diagnostic_ref, diagnostic_ref),
        authorized_pointers=pointers,
        reason_code=(
            f"{reason_prefix}_schema_exhausted"
            if maximum_repairs == 0
            else f"{reason_prefix}_repair_requested"
        ),
    )
    error.spend = None
    if maximum_repairs == 0:
        _raise_exhausted(session, spend=exhaustion_spend)

    last_spend = exhaustion_spend
    previous_preparation = parent
    previous_provider = initial_provider
    for repair_index in range(1, maximum_repairs + 1):
        try:
            turn = session.turn(repair_index)
        except SchemaExhaustedError:
            _raise_exhausted(session, spend=last_spend)

        diagnostic_value = turn.diagnostic_envelope or session.syntax_diagnostic
        if diagnostic_value is None:
            raise ValueError("repair turn lacks a bound diagnostic")
        turn_diagnostic_ref, diagnostic_bytes = _record_bytes(service.harness, diagnostic_value)
        baseline_bytes = session.invalid_text.encode("utf-8")
        baseline_ref = service.harness.blobs.put(baseline_bytes)
        payload = {
            "schema": "repair.semantic-task.v1",
            "parent_work_id": parent.id,
            "previous_work_id": previous_preparation.id,
            "previous_provider_attempt_ref": previous_provider.id,
            "repair_index": repair_index,
            "mode": turn.mode,
            "contract_id": parent.contract_id,
            "authorized_pointers": list(turn.authorized_pointers),
            "baseline_sha256": hashlib.sha256(baseline_bytes).hexdigest(),
            "diagnostic_ref": turn_diagnostic_ref,
        }
        fence = max(0, service.harness._next_seq - 1)
        trigger_ref = "repair:" + hashlib.sha256(canonical_json(payload)).hexdigest()
        preparation = service.prepare(
            task_kind=WorkflowTaskKind.REPAIR,
            attempt_index=repair_index,
            route_lease=parent.route_lease,
            contract_id=parent.contract_id,
            trigger_ref=trigger_ref,
            formal_fence_seq=fence,
            scratch_fence_seq=fence,
            target_refs=parent.target_refs,
            input_refs=tuple(
                dict.fromkeys(
                    (
                        parent.id,
                        previous_provider.id,
                        baseline_ref,
                        turn_diagnostic_ref,
                    )
                )
            ),
            task_payload_value=payload,
        )
        repair_authorized = None

        context_values = tuple(
            dict.fromkeys(
                (
                    (baseline_ref, baseline_bytes),
                    (turn_diagnostic_ref, diagnostic_bytes),
                )
            )
        )
        rendered_bytes = len(turn.request.encode("utf-8"))
        items = tuple(
            VisibleContextItemV1(
                namespace=ContextNamespace.SOURCE,
                alias=f"SRC_{index:03d}",
                object_ref=object_ref,
                content_sha256=hashlib.sha256(content).hexdigest(),
                planned_bytes=(rendered_bytes if index == 1 else 0),
            )
            for index, (object_ref, content) in enumerate(context_values, 1)
        )
        try:
            plan = service.context_plan(
                preparation,
                plan_kind="combined",
                items=items,
                maximum_bytes=rendered_bytes,
                rendered_bytes=rendered_bytes,
            )
            dispatch_contract = (
                RepairPatchWireContract(parent.contract_id, turn.diagnostic_envelope)
                if turn.mode == "patch"
                else wire_contract
            )
            dispatch_output_model = RepairPatchV1 if turn.mode == "patch" else output_model
            prompt, preview_contract, preview_lease, maximum_tokens = adapter.preview_request(
                role,
                pack,
                dispatch_output_model,
                endpoint_index=endpoint_index,
                template_role=template_role,
                wire_contract=dispatch_contract,
                model_profile=model_profile,
                endpoint_lease=endpoint_lease,
                pre_rendered_request=turn.request,
            )
            if (
                prompt != turn.request
                or preview_contract is not dispatch_contract
                or preview_lease != endpoint_lease
            ):
                raise ValueError("repair preview changed frozen call authority")
            repair_authorized = service.issue(
                preparation,
                plans=(plan,),
                prompt=prompt,
                max_tokens=maximum_tokens,
            )
        except WorkBudgetDenied:
            raise
        except BaseException:
            service.terminate(
                work_id=preparation.id,
                attempt_index=preparation.attempt_index,
                status="abandoned",
                reason_code=f"{reason_prefix}_repair_preissue_failure",
                usage_status="exact",
                prompt_tokens=0,
                completion_tokens=0,
            )
            raise

        repair_error = None
        try:
            _wire_output, repair_call = adapter.call(
                role,
                pack,
                dispatch_output_model,
                endpoint_index=endpoint_index,
                template_role=template_role,
                wire_contract=dispatch_contract,
                model_profile=model_profile,
                output_mechanism=output_mechanism,
                endpoint_lease=endpoint_lease,
                school_id=school_id,
                dispatch_authorization=repair_authorized,
                pre_rendered_request=turn.request,
            )
        except EndpointError as transport_error:
            transport_spend = getattr(transport_error, "spend", None)
            if transport_spend is None:
                if repair_authorized.reservation.is_open:
                    repair_authorized.release()
                service.terminate(
                    work_id=preparation.id,
                    attempt_index=preparation.attempt_index,
                    status="abandoned",
                    reason_code=f"{reason_prefix}_repair_result_unknown",
                    usage_status="unknown",
                )
            else:
                transport_diagnostic = (
                    transport_spend.attempt_trace[-1].diagnostic_ref
                    if transport_spend.attempt_trace
                    else turn_diagnostic_ref
                )
                provider = service.record_provider_attempt(
                    repair_authorized,
                    call=transport_spend,
                    outcome="transport_failure",
                    usage_status="unknown",
                    diagnostic_ref=transport_diagnostic,
                )
                service.terminate(
                    work_id=preparation.id,
                    attempt_index=preparation.attempt_index,
                    status="transport_failed",
                    reason_code=f"{reason_prefix}_repair_transport_failure",
                    usage_status="unknown",
                    provider_attempt=provider,
                )
                transport_error.spend = None
            transport_error.transaction_terminalized = True
            raise
        except SchemaRepairError as caught:
            repair_error = caught
            repair_call = getattr(caught, "spend", None)
            if repair_call is None:
                if repair_authorized.reservation.is_open:
                    repair_authorized.release()
                service.terminate(
                    work_id=preparation.id,
                    attempt_index=preparation.attempt_index,
                    status="abandoned",
                    reason_code=f"{reason_prefix}_repair_result_unknown",
                    usage_status="unknown",
                )
                caught.transaction_terminalized = True
                raise
        except BaseException:
            if repair_authorized.reservation.is_open:
                repair_authorized.release()
            service.terminate(
                work_id=preparation.id,
                attempt_index=preparation.attempt_index,
                status="abandoned",
                reason_code=f"{reason_prefix}_repair_dispatch_failure",
                usage_status="unknown",
            )
            raise

        last_spend = repair_call if preserve_terminalized_spend else None
        repair_raw = _raw_text(service.harness, repair_call)
        try:
            compiled, next_diagnostic = _assess(
                session,
                turn,
                repair_raw,
                wire_contract,
            )
        except UnrepairableDiagnosticError as unrepairable:
            unrepairable_ref, _ = _record_bytes(
                service.harness,
                {
                    "schema": "repair.unrepairable.v1",
                    "contract": parent.contract_id,
                    "message": str(unrepairable)[:500],
                },
            )
            trace_ref = (
                repair_call.attempt_trace[-1].diagnostic_ref if repair_call.attempt_trace else None
            )
            _terminalize_invalid(
                service,
                repair_authorized,
                repair_call,
                diagnostic_ref=trace_ref or unrepairable_ref,
                admission_outcome="schema_exhausted",
                admission_diagnostic_refs=_diagnostic_refs(trace_ref, unrepairable_ref),
                authorized_pointers=turn.authorized_pointers,
                reason_code=f"{reason_prefix}_repair_unrepairable",
            )
            if repair_error is not None:
                repair_error.spend = None
            _raise_exhausted(
                session,
                "schema_exhausted: repair produced an object-wide failure",
                spend=last_spend,
            )

        if compiled is not None:
            provider = service.record_provider_attempt(
                repair_authorized,
                call=repair_call,
                outcome="provider_result",
                usage_status="exact",
            )
            if repair_error is not None:
                raise ValueError("adapter rejected a repair that revalidates successfully")
            return TransactionRepairResult(
                output=compiled,
                llm_call=repair_call,
                preparation=preparation,
                authorized=repair_authorized,
                provider_attempt=provider,
            )
        if next_diagnostic is None:
            raise ValueError("invalid repair lacks deterministic diagnostics")

        next_diagnostic_ref, _ = _record_bytes(service.harness, next_diagnostic)
        trace_ref = (
            repair_call.attempt_trace[-1].diagnostic_ref if repair_call.attempt_trace else None
        )
        try:
            session.turn(repair_index + 1)
        except (IndexError, SchemaExhaustedError, UnrepairableDiagnosticError):
            has_next = False
        else:
            has_next = repair_index < maximum_repairs
        next_pointers = tuple(getattr(next_diagnostic, "authorized_pointers", ()))
        previous_provider = _terminalize_invalid(
            service,
            repair_authorized,
            repair_call,
            diagnostic_ref=trace_ref or next_diagnostic_ref,
            admission_outcome=("rejected" if has_next else "schema_exhausted"),
            admission_diagnostic_refs=_diagnostic_refs(trace_ref, next_diagnostic_ref),
            authorized_pointers=next_pointers or turn.authorized_pointers,
            reason_code=(
                f"{reason_prefix}_repair_step_rejected"
                if has_next
                else f"{reason_prefix}_schema_exhausted"
            ),
        )
        if repair_error is not None:
            repair_error.spend = None
        if not has_next:
            _raise_exhausted(session, spend=last_spend)
        previous_preparation = preparation

    _raise_exhausted(session, spend=last_spend)


__all__ = ["repair_schema_failure"]
