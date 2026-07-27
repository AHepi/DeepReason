"""RunManifest-v6 recovery for non-conjecture provider work.

Recovery has no provider dependency.  It consumes the one durable raw result
already bound by ``ProviderAttemptV1`` and validates the immutable authority
prefix. Criticism and scratch authoring retain enough durable authority to
resume their ordinary semantic paths. Other caller-owned domains remain
conservatively unapplied where their call-local contract is incomplete.
"""

from __future__ import annotations

import hashlib
import json
import re
from collections.abc import Mapping
from typing import Any

from pydantic import BaseModel, ValidationError

from deepreason.canonical import canonical_json
from deepreason.llm.firewall import reject_model_control_fields, route_fingerprint
from deepreason.llm.repair import (
    RepairDiagnosticEnvelopeV2,
    apply_repair_patch,
    parse_one_json_value,
)
from deepreason.llm.wire import (
    AliasTable,
    BatchCriticWireContractV2,
    RepairPatchWireContract,
)
from deepreason.run_manifest import RunManifest, config_from_run_manifest
from deepreason.scratch.contracts import (
    ClusterGuideWireContract,
    ScratchBlockWireContract,
    ScratchLinkWireContract,
)
from deepreason.scratch.render import ScratchRenderReceiptV1
from deepreason.workflow.criticism import CriticismAssignmentV1
from deepreason.workflow.models import WorkflowTaskKind
from deepreason.workflow.transaction import (
    ContextNamespace,
    ProviderAttemptV1,
    SemanticAdmissionV1,
)
from deepreason.workflow.transaction_service import InquiryTransactionService


_HEX_DIGEST = re.compile(r"^[0-9a-f]{64}$")
_RECOVERABLE_TASKS = frozenset(
    {
        WorkflowTaskKind.CRITICISM,
        WorkflowTaskKind.BRIDGE_LEDGER,
        WorkflowTaskKind.BRIDGE_COMPOSITION,
        WorkflowTaskKind.BRIDGE_REVIEW,
        WorkflowTaskKind.REPAIR,
        WorkflowTaskKind.SCRATCH_AUTHORING,
    }
)


class NonConjectureRecoveryAuthorityError(RuntimeError):
    """The durable prefix does not describe one manifest-authorized call."""


def _authority(condition: bool, message: str) -> None:
    if not condition:
        raise NonConjectureRecoveryAuthorityError(message)


def _mapping(value: Any, label: str) -> dict[str, Any]:
    _authority(isinstance(value, Mapping), f"{label} is not an object")
    return {str(key): item for key, item in value.items()}


def _source_call(harness, provider: ProviderAttemptV1):
    matches = [
        (event.seq, event.llm)
        for event in harness.log.read()
        if event.llm is not None
        and event.llm.work_order_id == provider.work_id
        and event.llm.dispatch_authorization_ref
        == provider.authorization_bundle_ref
    ]
    _authority(
        len(matches) == 1,
        "provider attempt does not have exactly one durable authorized call",
    )
    event_seq, call = matches[0]
    _authority(call.raw_ref == (provider.raw_ref or ""), "provider raw reference differs")
    _authority(bool(call.prompt_ref), "provider call has no durable prompt")
    return event_seq, call


def _route(manifest: RunManifest, preparation, call):
    lease = preparation.route_lease
    routes = manifest.roles.get(lease.role, ())
    _authority(0 <= lease.seat < len(routes), "route seat is absent from the manifest")
    route = routes[lease.seat]
    _authority(lease.endpoint_id == route.endpoint_id, "endpoint differs from manifest")
    _authority(
        lease.route_sha256 == route_fingerprint(route),
        "route fingerprint differs from manifest",
    )
    _authority(call.role == lease.role, "provider role differs from route authority")
    _authority(call.model == route.model_id, "provider model differs from route authority")
    _authority(call.endpoint == route.base_url, "provider endpoint differs from route authority")
    return route


def _common_authority(harness, manifest: RunManifest, provider: ProviderAttemptV1):
    item = harness.workflow_state.transaction_work.get(provider.work_id)
    _authority(item is not None, "provider attempt names no replayed transaction")
    preparation = item.preparation
    _authority(
        preparation.task_kind in _RECOVERABLE_TASKS,
        "work is not a recoverable non-conjecture task",
    )
    _authority(preparation.manifest_digest == manifest.sha256, "manifest digest differs")
    _authority(
        preparation.attempt_index == provider.attempt_index,
        "provider attempt index differs from preparation",
    )
    _authority(
        item.provider_attempts.get(provider.attempt_index) == provider,
        "provider attempt is not the replayed result",
    )
    _authority(
        item.authorization is not None
        and item.reservation is not None
        and item.exposure is not None,
        "provider result lacks complete issued authority",
    )
    authorization = item.authorization
    _authority(provider.authorization_bundle_ref == authorization.id, "bundle differs")
    _authority(provider.contract_id == preparation.contract_id, "contract differs")
    _authority(provider.route_lease == preparation.route_lease, "route lease differs")
    _authority(provider.prompt_sha256 == item.exposure.prompt_sha256, "prompt differs")
    _authority(provider.prompt_sha256 == item.reservation.prompt_sha256, "prompt differs")
    _authority(
        authorization.prompt_sha256 == provider.prompt_sha256,
        "authorization prompt differs",
    )
    _authority(
        authorization.reservation_ref == item.reservation.id
        and authorization.exposure_receipt_ref == item.exposure.id,
        "authorization does not bind the replayed issue records",
    )
    payload = _mapping(preparation.task_payload_value, "task payload")
    event_seq, call = _source_call(harness, provider)
    prompt = harness.blobs.get(call.prompt_ref)
    _authority(
        hashlib.sha256(prompt).hexdigest() == provider.prompt_sha256,
        "durable prompt bytes differ from issued authority",
    )
    _route(manifest, preparation, call)
    return item, preparation, payload, event_seq, call


def _trigger(preparation, payload: Mapping[str, Any], prefix: str) -> None:
    expected = prefix + hashlib.sha256(canonical_json(payload)).hexdigest()
    _authority(preparation.trigger_ref == expected, "task trigger differs from payload")


def _raw_bytes(harness, provider: ProviderAttemptV1) -> bytes:
    _authority(provider.raw_ref is not None, "provider result has no raw reference")
    try:
        return harness.blobs.get(provider.raw_ref)
    except (KeyError, OSError, ValueError) as error:
        raise NonConjectureRecoveryAuthorityError(
            "provider raw blob is unavailable or corrupt"
        ) from error


def _diagnostic(harness, *, code: str, task: str, detail: str, **extra: Any) -> str:
    return harness.blobs.put(
        canonical_json(
            {
                "schema": "nonconjecture-admission-recovery-diagnostic.v1",
                "code": code,
                "task": task,
                "detail": detail[:500],
                **extra,
            }
        )
    )


def _terminalize(
    service: InquiryTransactionService,
    provider: ProviderAttemptV1,
    *,
    outcome: str,
    reason_code: str,
    diagnostic_refs: tuple[str, ...],
    authorized_pointers: tuple[str, ...] = (),
) -> SemanticAdmissionV1:
    admission = service.record_semantic_admission(
        provider,
        outcome=outcome,
        diagnostic_refs=diagnostic_refs,
        authorized_pointers=authorized_pointers,
    )
    service.terminate(
        work_id=provider.work_id,
        attempt_index=provider.attempt_index,
        status="schema_exhausted" if outcome == "schema_exhausted" else "rejected",
        reason_code=reason_code,
        usage_status=provider.usage_status,
        prompt_tokens=provider.prompt_tokens,
        completion_tokens=provider.completion_tokens,
        provider_attempt=provider,
        admission=admission,
    )
    return admission


def _schema_exhausted(
    service: InquiryTransactionService,
    provider: ProviderAttemptV1,
    *,
    task: str,
    error: Exception,
) -> SemanticAdmissionV1:
    diagnostic_ref = _diagnostic(
        service.harness,
        code="stored_raw_schema_invalid",
        task=task,
        detail=f"{type(error).__name__}: {error}",
    )
    return _terminalize(
        service,
        provider,
        outcome="schema_exhausted",
        reason_code=f"recovered_{task}_schema_exhausted"[:128],
        diagnostic_refs=(diagnostic_ref,),
    )


def _existing_admission(item, provider: ProviderAttemptV1):
    admission = item.admissions.get(provider.attempt_index)
    terminal = item.terminal
    if admission is not None:
        _authority(admission.provider_attempt_ref == provider.id, "admission provider differs")
        _authority(admission.work_id == provider.work_id, "admission work differs")
    if terminal is not None:
        _authority(admission is not None, "terminal work has no semantic admission")
        _authority(
            terminal.semantic_admission_ref == admission.id
            and terminal.provider_attempt_ref == provider.id,
            "terminal completion differs from durable provider admission",
        )
    return admission


def _complete_admitted(
    service: InquiryTransactionService,
    provider: ProviderAttemptV1,
    *,
    admitted_refs: tuple[str, ...],
    reason_code: str,
) -> SemanticAdmissionV1:
    admission = service.record_semantic_admission(
        provider,
        outcome="admitted",
        admitted_refs=admitted_refs,
    )
    service.terminate(
        work_id=provider.work_id,
        attempt_index=provider.attempt_index,
        status="completed",
        reason_code=reason_code,
        usage_status=provider.usage_status,
        prompt_tokens=provider.prompt_tokens,
        completion_tokens=provider.completion_tokens,
        provider_attempt=provider,
        admission=admission,
    )
    return admission


def _recover_criticism_effect(
    harness,
    manifest,
    item,
    preparation,
    payload,
    provider,
    source_call_seq,
    call,
    output,
    service,
) -> SemanticAdmissionV1:
    from deepreason.rules.crit import (
        _apply_counterexample_retry_result,
        _crit_argumentative_batch_result,
    )
    from deepreason.workflow.criticism import record_completed_criticism_attempt

    phase = str(payload["phase"])
    fallback_cases = None
    if phase.startswith("counterexample_retry:"):
        # Retry lineage is semantic authority, so validate it before any
        # admission or terminal append can mark this result successful.
        fallback_cases = _criticism_retry_fallback_cases(
            harness,
            manifest,
            preparation,
            payload,
        )
    semantic_ref = harness.blobs.put(
        canonical_json(output.model_dump(mode="json", exclude_none=True))
    )
    admission = _existing_admission(item, provider)
    if admission is not None and admission.outcome != "admitted":
        return admission
    if admission is None:
        # This is the ordinary critic transaction ordering: the provider output
        # is admitted and terminal before the caller applies its domain effect.
        admission = _complete_admitted(
            service,
            provider,
            admitted_refs=(semantic_ref,),
            reason_code="critic_output_admitted",
        )
    else:
        _authority(
            admission.admitted_refs == (semantic_ref,),
            "critic admission differs from the durable validated output",
        )

    if fallback_cases is not None:
        _apply_counterexample_retry_result(
            harness,
            output,
            fallback_cases,
            call,
            critic_school_id=str(payload["critic_school_id"]),
            llm_already_recorded=True,
            restart_safe=True,
            effect_source_call_seq=source_call_seq,
        )
        return admission

    critics = _crit_argumentative_batch_result(
        harness,
        list(preparation.target_refs),
        None,
        config_from_run_manifest(manifest),
        output,
        call,
        authority="observe_only",
        call_kwargs={},
        school_prefix="",
        critic_school_id=str(payload["critic_school_id"]),
        transactional_call=None,
        llm_already_recorded=True,
        restart_safe=True,
        effect_source_call_seq=source_call_seq,
        allow_provider_followup=False,
    )
    for assignment_ref in preparation.input_refs:
        _schema, assignment = harness.objects.get(assignment_ref)
        record_completed_criticism_attempt(
            harness,
            assignment,
            attempt_index=preparation.attempt_index,
            source_call_seq=source_call_seq,
        )
    # Force evaluation so a malformed artifact result cannot masquerade as a
    # completed application. The canonical effects themselves are event-backed.
    tuple(critic.id for critic in critics)
    return admission


def _criticism_retry_fallback_cases(
    harness,
    manifest,
    preparation,
    payload,
) -> dict[str, str]:
    phase = str(payload["phase"])
    try:
        retry_index = int(phase.removeprefix("counterexample_retry:"))
    except ValueError as error:
        raise NonConjectureRecoveryAuthorityError(
            "critic retry phase is malformed"
        ) from error
    _authority(retry_index >= 0, "critic retry phase is malformed")
    previous_phase = "primary" if retry_index == 0 else f"counterexample_retry:{retry_index - 1}"
    caller_trigger_ref = payload.get("caller_trigger_ref")
    _authority(
        isinstance(caller_trigger_ref, str) and caller_trigger_ref,
        "critic retry has no caller identity",
    )
    candidates = []
    for previous in harness.workflow_state.transaction_work.values():
        previous_payload = previous.preparation.task_payload_value
        if not isinstance(previous_payload, Mapping):
            continue
        if (
            previous.preparation.task_kind == WorkflowTaskKind.CRITICISM
            and previous_payload.get("phase") == previous_phase
            and previous_payload.get("caller_trigger_ref") == caller_trigger_ref
            and previous_payload.get("critic_school_id") == payload.get("critic_school_id")
            and previous_payload.get("coverage_attempt_index")
            == payload.get("coverage_attempt_index")
            and set(preparation.target_refs).issubset(previous.preparation.target_refs)
        ):
            provider = previous.provider_attempts.get(previous.preparation.attempt_index)
            if provider is not None and provider.outcome == "provider_result":
                candidates.append((previous, provider))
    _authority(len(candidates) == 1, "critic retry has no unique durable predecessor")
    previous, previous_provider = candidates[0]
    (
        authoritative_previous,
        previous_preparation,
        previous_payload,
        _previous_source_seq,
        _previous_call,
    ) = _common_authority(harness, manifest, previous_provider)
    _authority(authoritative_previous is previous, "critic retry predecessor differs")
    previous_contract = _criticism_contract(
        harness,
        manifest,
        previous,
        previous_preparation,
        previous_payload,
    )
    previous_raw = parse_one_json_value(
        _raw_bytes(harness, previous_provider).decode("utf-8")
    ).value
    reject_model_control_fields(previous_raw)
    previous_output = previous_contract.compile(
        previous_contract.validate_value(previous_raw)
    )
    by_target = {
        case.target: case.case
        for case in previous_output.cases
        if case.attack
    }
    _authority(
        all(target_id in by_target for target_id in preparation.target_refs),
        "critic retry predecessor does not authorize every target",
    )
    return {target_id: by_target[target_id] for target_id in preparation.target_refs}


def _recover_scratch_effect(
    harness,
    item,
    preparation,
    payload,
    provider,
    source_call_seq,
    call,
    output,
    service,
) -> SemanticAdmissionV1:
    from deepreason.scratch.authoring import ScratchAuthoringService
    from deepreason.scratch.service import ScratchService

    admission = _existing_admission(item, provider)
    if admission is not None and admission.outcome != "admitted":
        return admission
    authored = ScratchAuthoringService(
        ScratchService(harness),
        adapter=None,
    ).admit_transactional_effect(
        operation=payload["operation"],
        output=output,
        payload=payload,
        call=call,
        provider_event_seq=source_call_seq,
        context_ref=item.exposure.id,
    )
    if admission is None:
        return _complete_admitted(
            service,
            provider,
            admitted_refs=(authored.id,),
            reason_code="scratch_output_admitted",
        )
    _authority(
        admission.admitted_refs == (authored.id,),
        "scratch admission differs from the canonical authored effect",
    )
    return admission


def _unapplied(
    service: InquiryTransactionService,
    provider: ProviderAttemptV1,
    *,
    task: str,
    detail: str,
    output: Any | None = None,
    authorized_pointers: tuple[str, ...] = (),
) -> SemanticAdmissionV1:
    semantic_ref = None
    if output is not None:
        value = (
            output.model_dump(mode="json", by_alias=True, exclude_none=True)
            if isinstance(output, BaseModel)
            else output
        )
        semantic_ref = service.harness.blobs.put(canonical_json(value))
    diagnostic_ref = _diagnostic(
        service.harness,
        code="validated_but_domain_unapplied",
        task=task,
        detail=detail,
        **({"validated_output_ref": semantic_ref} if semantic_ref else {}),
    )
    return _terminalize(
        service,
        provider,
        outcome="rejected",
        reason_code=f"recovered_{task}_domain_unapplied"[:128],
        diagnostic_refs=(diagnostic_ref,),
        authorized_pointers=authorized_pointers,
    )


def _artifact_digest(harness, target_id: str) -> str:
    artifact = harness.state.artifacts.get(target_id)
    _authority(artifact is not None, "critic target is absent from formal state")
    if artifact.content_ref.startswith("inline:"):
        content = artifact.content_ref.removeprefix("inline:").encode("utf-8")
    else:
        try:
            content = harness.blobs.get(artifact.content_ref)
        except (KeyError, OSError, ValueError):
            content = artifact.content_ref.encode("utf-8")
    return hashlib.sha256(content).hexdigest()


def _criticism_contract(harness, manifest, item, preparation, payload):
    _authority(payload.get("schema") == "criticism.semantic-task.v1", "unknown critic task")
    _trigger(preparation, payload, "criticism:")
    versions = manifest.control_plane_policy.contract_versions
    _authority(preparation.contract_id == versions.batch_critic_contract, "critic contract differs")
    policy = manifest.criticism_policy
    _authority(policy is not None, "manifest does not authorize criticism")
    _authority(policy.authority == "observe_only", "critic authority is not recoverable")
    school_id = payload.get("critic_school_id")
    binding = next((value for value in policy.bindings if value.school_id == school_id), None)
    _authority(binding is not None, "critic school has no manifest binding")
    lease = preparation.route_lease
    _authority(
        (lease.role, lease.seat, lease.endpoint_id)
        == (binding.role, binding.seat, binding.endpoint_id),
        "critic route differs from school binding",
    )
    targets = payload.get("target_ids")
    assignments = payload.get("assignment_refs")
    _authority(
        isinstance(targets, (tuple, list)) and tuple(targets) == preparation.target_refs,
        "critic targets differ from preparation",
    )
    _authority(
        isinstance(assignments, (tuple, list))
        and tuple(assignments) == preparation.input_refs,
        "critic assignments differ from preparation",
    )
    _authority(
        payload.get("coverage_attempt_index") == preparation.attempt_index,
        "critic attempt index differs",
    )
    _authority(isinstance(payload.get("phase"), str) and payload["phase"], "critic phase missing")
    exposed = item.exposure.exposed_items
    aliases = {entry.alias: entry.object_ref for entry in exposed}
    expected_aliases = {
        f"SRC_{index:03d}": target_id
        for index, target_id in enumerate(preparation.target_refs, 1)
    }
    _authority(aliases == expected_aliases, "critic exposure catalog differs from targets")
    _authority(
        all(entry.namespace == ContextNamespace.SOURCE for entry in exposed),
        "critic exposure contains a non-source namespace",
    )
    for entry in exposed:
        _authority(
            entry.content_sha256 == _artifact_digest(harness, entry.object_ref),
            "critic target bytes differ from exposure digest",
        )
    _authority(len(assignments) == len(targets), "critic assignment cardinality differs")
    for assignment_ref, target_id in zip(assignments, targets, strict=True):
        try:
            schema, assignment = harness.objects.get(str(assignment_ref))
        except (KeyError, OSError, ValueError) as error:
            raise NonConjectureRecoveryAuthorityError(
                "criticism assignment is unavailable"
            ) from error
        _authority(schema == "criticism-assignment-v1", "input is not a criticism assignment")
        _authority(isinstance(assignment, CriticismAssignmentV1), "assignment type differs")
        _authority(assignment.id == assignment_ref, "assignment identity differs")
        _authority(assignment.manifest_digest == manifest.sha256, "assignment manifest differs")
        _authority(assignment.target_id == target_id, "assignment target differs")
        _authority(assignment.critic_school_id == school_id, "assignment school differs")
        _authority(
            (assignment.role, assignment.seat, assignment.endpoint_id, assignment.route_sha256)
            == (lease.role, lease.seat, lease.endpoint_id, lease.route_sha256),
            "assignment route differs",
        )
        _authority(
            preparation.attempt_index < assignment.maximum_attempts,
            "critic attempt exceeds assignment ceiling",
        )
    return BatchCriticWireContractV2(
        AliasTable(expected_aliases),
        expected_targets=preparation.target_refs,
    )


def _scratch_contract(harness, manifest, item, preparation, payload):
    _authority(payload.get("schema") == "scratch.authoring-task.v1", "unknown scratch task")
    _trigger(preparation, payload, "scratch-authoring:")
    policy = manifest.scratch_policy
    authoring = manifest.control_plane_policy.scratch_authoring
    _authority(
        policy is not None and policy.enabled and authoring.enabled,
        "manifest does not authorize scratch authoring",
    )
    operation = payload.get("operation")
    expected = {
        "block": (
            policy.block_role,
            "scratch_block",
            "scratch.block.compact.v1",
            "ScratchBlockBodyV1",
        ),
        "link": (
            policy.link_role,
            "scratch_link",
            "scratch.link.compact.v1",
            "ScratchLinkBodyV1",
        ),
        "guide": (
            policy.guide_role,
            "scratch_guide",
            "scratch.cluster-guide.compact.v1",
            "ClusterGuideDraftV1",
        ),
    }.get(operation)
    _authority(expected is not None, "scratch operation is unknown")
    role, template_role, contract_id, output_model = expected
    lease = preparation.route_lease
    _authority(lease.role == role and lease.seat == 0, "scratch role differs from policy")
    _authority(preparation.contract_id == contract_id, "scratch contract differs")
    _authority(
        payload.get("role") == role
        and payload.get("seat") == 0
        and payload.get("template_role") == template_role
        and payload.get("contract_id") == contract_id
        and payload.get("output_model") == output_model,
        "scratch payload call authority differs",
    )
    _authority(
        payload.get("purpose") == "imaginative_workshop"
        and payload.get("epistemic_boundary") == "advisory_non_grounding",
        "scratch epistemic boundary differs",
    )
    context_ref = payload.get("context_receipt_ref")
    task_ref = payload.get("task_ref")
    _authority(isinstance(context_ref, str) and _HEX_DIGEST.fullmatch(context_ref), "scratch receipt ref invalid")
    _authority(isinstance(task_ref, str) and _HEX_DIGEST.fullmatch(task_ref), "scratch task ref invalid")
    receipt_bytes = harness.blobs.get(context_ref)
    task_bytes = harness.blobs.get(task_ref)
    _authority(hashlib.sha256(task_bytes).hexdigest() == payload.get("task_sha256"), "scratch task digest differs")
    try:
        receipt = ScratchRenderReceiptV1.model_validate(json.loads(receipt_bytes))
    except (json.JSONDecodeError, ValidationError, TypeError, ValueError) as error:
        raise NonConjectureRecoveryAuthorityError("scratch receipt is invalid") from error
    _authority(receipt.receipt_hash == payload.get("context_receipt_hash"), "scratch receipt hash differs")
    exposed = item.exposure.exposed_items
    _authority(
        len(exposed) == 1
        and exposed[0].namespace == ContextNamespace.SCRATCH
        and exposed[0].alias == "SCR_001",
        "scratch exposure shape differs",
    )
    rendered_ref = exposed[0].object_ref
    rendered_bytes = harness.blobs.get(rendered_ref)
    _authority(
        exposed[0].content_sha256 == hashlib.sha256(rendered_bytes).hexdigest(),
        "rendered scratch bytes differ from exposure",
    )
    _authority(
        preparation.input_refs
        == tuple(dict.fromkeys((context_ref, rendered_ref, task_ref))),
        "scratch input references differ",
    )
    operation_payload = _mapping(payload.get("operation_payload", {}), "scratch operation payload")
    if operation == "block":
        _authority(not preparation.target_refs, "scratch block unexpectedly names a target")
        return ScratchBlockWireContract()
    handles = receipt.alias_map("block")
    if operation == "link":
        _authority(not preparation.target_refs, "scratch link unexpectedly names a target")
        return ScratchLinkWireContract(
            indexed_block_ids=list(handles.values()),
            handles=handles,
        )
    cluster_id = operation_payload.get("cluster_id")
    _authority(
        isinstance(cluster_id, str)
        and preparation.target_refs == (cluster_id,)
        and isinstance(operation_payload.get("cluster_snapshot"), str),
        "scratch guide target or snapshot differs",
    )
    return ClusterGuideWireContract(handles=handles)


def _bridge_authority(harness, manifest, item, preparation, payload) -> str:
    _authority(payload.get("schema") == "bridge.transaction-task.v1", "unknown bridge task")
    _trigger(preparation, payload, "bridge:")
    template = payload.get("template_role")
    task = preparation.task_kind
    expected_task = {
        "bridge_ledger": WorkflowTaskKind.BRIDGE_LEDGER,
        "bridge_compose": WorkflowTaskKind.BRIDGE_COMPOSITION,
        "bridge_review": WorkflowTaskKind.BRIDGE_REVIEW,
        "bridge_grounding_repair": WorkflowTaskKind.REPAIR,
    }.get(template)
    _authority(task == expected_task, "bridge template differs from task kind")
    policy = manifest.bridge_policy
    _authority(policy is not None, "manifest does not authorize bridge work")
    versions = manifest.control_plane_policy.contract_versions
    expected = {
        "bridge_ledger": (
            policy.ledger_role,
            versions.bridge_ledger_wire_contract,
            "ClaimLedgerV1",
        ),
        "bridge_compose": (
            policy.composer_role,
            versions.bridge_composition_contract,
            "CompositionDraftV1",
        ),
        "bridge_review": (
            policy.reviewer_role,
            "groundingverdictwirev1.direct.v1",
            "GroundingVerdictWireV1",
        ),
        "bridge_grounding_repair": (
            policy.grounding_repair_role,
            "groundingrepairwirev1.direct.v1",
            "GroundingRepairWireV1",
        ),
    }[template]
    role, contract, output_model = expected
    _authority(
        payload.get("role") == role
        and payload.get("seat") == preparation.route_lease.seat
        and preparation.route_lease.role == role,
        "bridge role or seat differs",
    )
    _authority(
        payload.get("contract_id") == contract and preparation.contract_id == contract,
        "bridge contract differs",
    )
    _authority(
        isinstance(payload.get("ordinal"), int)
        and payload["ordinal"] >= 0
        and payload.get("output_model") == output_model,
        "bridge call identity is malformed",
    )
    pack_digest = payload.get("pack_sha256")
    _authority(
        isinstance(pack_digest, str) and _HEX_DIGEST.fullmatch(pack_digest),
        "bridge pack digest is malformed",
    )
    exposed_refs = tuple(entry.object_ref for entry in item.exposure.exposed_items)
    _authority(exposed_refs == preparation.input_refs, "bridge exposure differs from inputs")
    if template in {"bridge_review", "bridge_grounding_repair"}:
        _authority(
            len(item.exposure.exposed_items) == 1,
            "direct bridge exposure must contain one pack",
        )
        direct = item.exposure.exposed_items[0]
        try:
            pack_bytes = harness.blobs.get(direct.object_ref)
        except (KeyError, OSError, ValueError) as error:
            raise NonConjectureRecoveryAuthorityError(
                "direct bridge pack is unavailable"
            ) from error
        _authority(
            direct.content_sha256 == pack_digest
            and hashlib.sha256(pack_bytes).hexdigest() == pack_digest,
            "direct bridge pack differs from exposure",
        )
    return template


def _repair_authority(harness, item, preparation, payload, raw_value):
    _authority(payload.get("schema") == "repair.semantic-task.v1", "unknown repair task")
    _trigger(preparation, payload, "repair:")
    parent_id = payload.get("parent_work_id")
    previous_id = payload.get("previous_work_id")
    previous_provider_ref = payload.get("previous_provider_attempt_ref")
    parent = harness.workflow_state.transaction_work.get(parent_id)
    previous = harness.workflow_state.transaction_work.get(previous_id)
    _authority(parent is not None and parent_id != preparation.id, "repair parent is invalid")
    _authority(previous is not None and previous_id != preparation.id, "previous repair work is invalid")
    _authority(parent.terminal is not None and previous.terminal is not None, "repair ancestry is not terminal")
    previous_providers = tuple(previous.provider_attempts.values())
    _authority(
        len(previous_providers) == 1 and previous_providers[0].id == previous_provider_ref,
        "repair previous provider differs",
    )
    _authority(preparation.route_lease == parent.preparation.route_lease, "repair route differs from parent")
    _authority(preparation.contract_id == parent.preparation.contract_id, "repair contract differs from parent")
    _authority(preparation.target_refs == parent.preparation.target_refs, "repair targets differ from parent")
    _authority(payload.get("repair_index") == preparation.attempt_index, "repair index differs")
    _authority(payload.get("contract_id") == preparation.contract_id, "repair payload contract differs")
    mode = payload.get("mode")
    _authority(mode in {"patch", "full"}, "repair mode is invalid")
    pointers = payload.get("authorized_pointers")
    _authority(
        isinstance(pointers, (tuple, list))
        and tuple(pointers) == tuple(sorted(set(pointers))),
        "repair pointers are not finite and canonical",
    )
    diagnostic_ref = payload.get("diagnostic_ref")
    _authority(
        isinstance(diagnostic_ref, str) and diagnostic_ref in preparation.input_refs,
        "repair diagnostic is not an input",
    )
    excluded = {str(parent_id), str(previous_provider_ref), str(diagnostic_ref)}
    baseline_refs = tuple(ref for ref in preparation.input_refs if ref not in excluded)
    _authority(len(baseline_refs) == 1, "repair has no unique baseline input")
    baseline_bytes = harness.blobs.get(baseline_refs[0])
    _authority(
        hashlib.sha256(baseline_bytes).hexdigest() == payload.get("baseline_sha256"),
        "repair baseline digest differs",
    )
    if mode == "full":
        return tuple(pointers), raw_value
    try:
        envelope = RepairDiagnosticEnvelopeV2.model_validate_json(
            harness.blobs.get(diagnostic_ref)
        )
        baseline = parse_one_json_value(baseline_bytes.decode("utf-8")).value
        contract = RepairPatchWireContract(preparation.contract_id, envelope)
        patch = contract.parse_compile(json.dumps(raw_value, separators=(",", ":")))
        candidate = apply_repair_patch(baseline, patch, envelope)
    except (UnicodeDecodeError, json.JSONDecodeError, TypeError, ValueError, ValidationError) as error:
        raise error
    _authority(envelope.baseline_sha256 == payload.get("baseline_sha256"), "repair envelope baseline differs")
    _authority(envelope.authorized_pointers == tuple(pointers), "repair envelope pointers differ")
    return tuple(pointers), {"patch": patch.model_dump(mode="json", by_alias=True, exclude_none=True), "candidate": candidate}


def recover_nonconjecture_admission(
    harness,
    manifest: RunManifest,
    meter,
    provider: ProviderAttemptV1,
) -> SemanticAdmissionV1 | None:
    """Terminalize one durable non-conjecture result without redispatch.

    ``None`` is returned only for a recovered transport failure, which has no
    semantic result and therefore receives the typed transport terminal
    directly.  Authority mismatches raise before any recovery event is
    appended.  Ordinary stored-output failures become typed terminal records.
    """

    manifest = RunManifest.model_validate(manifest)
    _authority(manifest.schema_version == 6, "non-conjecture recovery requires v6")
    item, preparation, payload, source_call_seq, call = _common_authority(
        harness, manifest, provider
    )
    service = InquiryTransactionService(harness, manifest, meter)
    existing_admission = _existing_admission(item, provider)

    if provider.outcome == "transport_failure":
        if item.terminal is not None:
            return None
        service.terminate(
            work_id=provider.work_id,
            attempt_index=provider.attempt_index,
            status="transport_failed",
            reason_code="recovered_transport_failure",
            usage_status=provider.usage_status,
            prompt_tokens=provider.prompt_tokens,
            completion_tokens=provider.completion_tokens,
            provider_attempt=provider,
        )
        return None
    _authority(provider.outcome == "provider_result", "unknown provider outcome")
    if existing_admission is not None and existing_admission.outcome != "admitted":
        return existing_admission
    raw_bytes = _raw_bytes(harness, provider)
    task = preparation.task_kind.value
    try:
        raw = raw_bytes.decode("utf-8")
        raw_value = parse_one_json_value(raw).value
        reject_model_control_fields(raw_value)
    except (UnicodeDecodeError, TypeError, ValueError) as error:
        return _schema_exhausted(service, provider, task=task, error=error)

    try:
        if preparation.task_kind == WorkflowTaskKind.CRITICISM:
            contract = _criticism_contract(
                harness, manifest, item, preparation, payload
            )
            output = contract.compile(contract.validate_value(raw_value))
            return _recover_criticism_effect(
                harness,
                manifest,
                item,
                preparation,
                payload,
                provider,
                source_call_seq,
                call,
                output,
                service,
            )
        if preparation.task_kind == WorkflowTaskKind.SCRATCH_AUTHORING:
            contract = _scratch_contract(
                harness, manifest, item, preparation, payload
            )
            output = contract.compile(contract.validate_value(raw_value))
            return _recover_scratch_effect(
                harness,
                item,
                preparation,
                payload,
                provider,
                source_call_seq,
                call,
                output,
                service,
            )
        if preparation.task_kind in {
            WorkflowTaskKind.BRIDGE_LEDGER,
            WorkflowTaskKind.BRIDGE_COMPOSITION,
            WorkflowTaskKind.BRIDGE_REVIEW,
        }:
            template = _bridge_authority(
                harness, manifest, item, preparation, payload
            )
            _authority(isinstance(raw_value, Mapping), "bridge result is not an object")
            return _unapplied(
                service,
                provider,
                task=task,
                detail=(
                    f"{template} call-local schema/catalog was not durably complete; "
                    "canonical bridge state remains unchanged"
                ),
            )
        _authority(preparation.task_kind == WorkflowTaskKind.REPAIR, "unexpected task kind")
        if payload.get("schema") == "bridge.transaction-task.v1":
            template = _bridge_authority(
                harness, manifest, item, preparation, payload
            )
            _authority(isinstance(raw_value, Mapping), "bridge repair result is not an object")
            return _unapplied(
                service,
                provider,
                task=task,
                detail=(
                    f"{template} output cannot be applied without the vanished "
                    "bridge workflow caller"
                ),
            )
        pointers, validated = _repair_authority(
            harness, item, preparation, payload, raw_value
        )
        return _unapplied(
            service,
            provider,
            task=task,
            detail=(
                "stored repair response is scope-valid where reconstructible; "
                "the frozen parent contract/domain admission remains outstanding"
            ),
            output=validated,
            authorized_pointers=pointers,
        )
    except NonConjectureRecoveryAuthorityError:
        raise
    except (ValidationError, TypeError, ValueError) as error:
        return _schema_exhausted(service, provider, task=task, error=error)


__all__ = [
    "NonConjectureRecoveryAuthorityError",
    "recover_nonconjecture_admission",
]
