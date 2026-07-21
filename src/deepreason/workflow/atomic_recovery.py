"""Deterministic recovery of durable atomic decomposition child results."""

from __future__ import annotations

from collections.abc import Mapping

from deepreason.canonical import canonical_json
from deepreason.llm.firewall import reject_model_control_fields
from deepreason.llm.repair import parse_one_json_value
from deepreason.workflow.nonconjecture_recovery import (
    _common_authority,
    _repair_authority,
    _route,
    _source_call,
)


def recover_atomic_child_output(harness, manifest, service, root_item, contract):
    """Return one schema-valid child output without provider redispatch."""

    descendants = [
        item
        for item in harness.workflow_state.transaction_work.values()
        if isinstance(item.preparation.task_payload_value, Mapping)
        and item.preparation.task_payload_value.get("schema")
        == "repair.semantic-task.v1"
        and item.preparation.task_payload_value.get("parent_work_id")
        == root_item.preparation.id
    ]
    descendants.sort(key=lambda item: item.preparation.attempt_index)
    selected = descendants[-1] if descendants else root_item
    if selected.terminal is not None and selected.terminal.status != "completed":
        raise ValueError("atomic child is terminally failed")
    provider = selected.provider_attempts.get(selected.preparation.attempt_index)
    if provider is None or provider.raw_ref is None:
        raise ValueError("atomic child has no durable provider result")
    if selected.preparation.task_kind.value == "conjecture":
        item = selected
        preparation = item.preparation
        if (
            preparation.manifest_digest != manifest.sha256
            or item.provider_attempts.get(preparation.attempt_index) != provider
            or item.authorization is None
            or item.exposure is None
            or provider.authorization_bundle_ref != item.authorization.id
            or provider.contract_id != preparation.contract_id
            or provider.route_lease != preparation.route_lease
            or provider.prompt_sha256 != item.exposure.prompt_sha256
        ):
            raise ValueError("atomic conjecture provider authority differs")
        _event_seq, call = _source_call(harness, provider)
        _route(manifest, preparation, call)
        payload = preparation.task_payload_value
    else:
        item, preparation, payload, _event_seq, call = _common_authority(
            harness, manifest, provider
        )
    raw = harness.blobs.get(provider.raw_ref).decode("utf-8")
    raw_value = parse_one_json_value(raw).value
    reject_model_control_fields(raw_value)
    if preparation.task_kind.value == "repair":
        _pointers, repaired = _repair_authority(
            harness, item, preparation, payload, raw_value
        )
        candidate = repaired.get("candidate") if isinstance(repaired, Mapping) else repaired
    else:
        candidate = raw_value
    output = contract.compile(contract.validate_value(candidate))
    if item.terminal is None:
        admitted_ref = harness.blobs.put(
            canonical_json(output.model_dump(mode="json", exclude_none=True))
        )
        admission = service.record_semantic_admission(
            provider, outcome="admitted", admitted_refs=(admitted_ref,)
        )
        service.terminate(
            work_id=preparation.id,
            attempt_index=preparation.attempt_index,
            status="completed",
            reason_code="atomic_child_output_admitted",
            usage_status=provider.usage_status,
            prompt_tokens=provider.prompt_tokens,
            completion_tokens=provider.completion_tokens,
            provider_attempt=provider,
            admission=admission,
        )
    return output, call


__all__ = ["recover_atomic_child_output"]
