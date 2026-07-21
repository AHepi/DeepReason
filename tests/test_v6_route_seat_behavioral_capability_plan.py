"""Frozen route-seat behavioral authority for transactional v6 execution."""

from __future__ import annotations

import json

import pytest
from pydantic import ValidationError

from deepreason.bridge.repair import GroundingRepairWireV1
from deepreason.bridge.review import GroundingVerdictWireV1
from deepreason.llm.firewall import route_fingerprint
from deepreason.llm.wire import DirectWireContract
from deepreason.run_manifest import (
    RouteSeatBehavioralCapabilityPlanV1,
    RunManifest,
    RunManifestError,
    resolve_route_seat_behavioral_capability,
)
from tests.test_v6_contract_schema_repair_policy import _compile_v6


def _entry_map(manifest):
    plan = manifest.route_seat_behavioral_capability_plan
    assert isinstance(plan, RouteSeatBehavioralCapabilityPlanV1)
    return {(entry.role, entry.seat): entry for entry in plan.entries}


def test_new_v6_plan_covers_every_route_and_separates_authority_from_evidence():
    manifest = _compile_v6()
    entries = _entry_map(manifest)
    expected = {
        (role, seat)
        for role, routes in manifest.roles.items()
        for seat, _route in enumerate(routes)
    }

    assert set(entries) == expected
    assert manifest.route_seat_behavioral_capability_plan.authority == (
        "manifest_frozen_route_seat_behavior"
    )
    assert manifest.route_seat_behavioral_capability_plan.evidence == (
        "separate_exact_production_qualification"
    )
    assert tuple(entries) == tuple(sorted(entries))
    assert all(entry.scratch_access == "advisory_available" for entry in entries.values())
    assert all(entry.scratch_formal_authority is False for entry in entries.values())


def test_plan_authorizes_only_existing_contracts_on_exact_route_seats():
    manifest = _compile_v6(
        scratch_authoring=True,
        scratch_enabled=True,
        bridge_mode="grounded_two_stage",
        grounding_review=True,
    )
    entries = _entry_map(manifest)
    verdict = DirectWireContract(GroundingVerdictWireV1).contract_id
    repair = DirectWireContract(GroundingRepairWireV1).contract_id
    flattened = {
        (entry.role, entry.seat, contract.contract_id)
        for entry in entries.values()
        for contract in entry.contracts
    }

    assert ("conjecturer", 0, "conjecturer.turn.v6") in flattened
    assert (manifest.bridge_policy.ledger_role, 0, "bridge.ledger.v3") in flattened
    assert (manifest.bridge_policy.composer_role, 0, "bridge.composition.v2") in flattened
    assert (
        manifest.bridge_policy.reviewer_role,
        manifest.bridge_policy.reviewer_seat,
        verdict,
    ) in flattened
    assert (
        manifest.bridge_policy.grounding_repair_role,
        manifest.bridge_policy.reviewer_seat,
        repair,
    ) in flattened
    assert any(contract_id == "scratch.block.compact.v1" for *_key, contract_id in flattened)
    assert ("conjecturer", 0, "conjecturer.atomic-candidate.v1") in flattened
    assert (
        "argumentative_critic",
        0,
        "critic.atomic-target.v1",
    ) in flattened
    assert all(
        contract.schema_repair.contract_id == contract.contract_id
        for entry in entries.values()
        for contract in entry.contracts
    )
    source_contracts = {
        contract.contract_id: contract
        for entry in entries.values()
        for contract in entry.contracts
        if contract.contract_id in {"conjecturer.turn.v6", "batch-critic.v2"}
    }
    assert all(
        contract.decomposition_permission == "authorized_atomic_children"
        and contract.contract_fallback_permission == "schema_exhaustion_to_atomic"
        for contract in source_contracts.values()
    )


def test_exact_resolver_rejects_historical_or_foreign_route_identity():
    manifest = _compile_v6()
    route = manifest.roles["conjecturer"][0]
    digest = route_fingerprint(route)
    grant = resolve_route_seat_behavioral_capability(
        manifest,
        role="conjecturer",
        seat=0,
        endpoint_id=route.endpoint_id,
        route_sha256=digest,
    )
    assert grant == _entry_map(manifest)[("conjecturer", 0)]

    with pytest.raises(RunManifestError, match="V6_BEHAVIORAL_ROUTE_MISMATCH"):
        resolve_route_seat_behavioral_capability(
            manifest,
            role="conjecturer",
            seat=0,
            endpoint_id=route.endpoint_id,
            route_sha256="0" * 64,
        )
    historical = RunManifest.model_validate(
        {
            key: value
            for key, value in manifest.model_dump(mode="json", by_alias=True).items()
            if key != "route_seat_behavioral_capability_plan"
        }
    )
    assert historical.route_seat_behavioral_capability_plan is None
    with pytest.raises(RunManifestError, match="V6_BEHAVIORAL_CAPABILITY_PLAN_REQUIRED"):
        resolve_route_seat_behavioral_capability(
            historical,
            role="conjecturer",
            seat=0,
            endpoint_id=route.endpoint_id,
            route_sha256=digest,
        )


def test_plan_is_strict_sorted_unique_and_manifest_consistent():
    manifest = _compile_v6()
    payload = manifest.route_seat_behavioral_capability_plan.model_dump(
        mode="json", by_alias=True
    )
    payload["unknown"] = True
    with pytest.raises(ValidationError):
        RouteSeatBehavioralCapabilityPlanV1.model_validate(payload)

    plan_payload = manifest.route_seat_behavioral_capability_plan.model_dump(
        mode="json", by_alias=True
    )
    plan_payload["entries"] = list(reversed(plan_payload["entries"]))
    with pytest.raises(ValidationError):
        RouteSeatBehavioralCapabilityPlanV1.model_validate(plan_payload)

    changed = manifest.model_dump(mode="json", by_alias=True)
    changed["route_seat_behavioral_capability_plan"]["entries"][0][
        "endpoint_id"
    ] = "foreign-endpoint"
    with pytest.raises(ValidationError, match="BEHAVIORAL_CAPABILITY_PLAN_MISMATCH"):
        RunManifest.model_validate(changed)


def test_historical_absence_is_canonical_and_policy_changes_identity():
    manifest = _compile_v6()
    payload = manifest.model_dump(mode="json", by_alias=True)
    payload.pop("route_seat_behavioral_capability_plan")
    historical = RunManifest.model_validate(payload)

    assert historical.route_seat_behavioral_capability_plan is None
    assert b"route_seat_behavioral_capability_plan" not in historical.canonical_bytes()
    assert manifest.canonical_bytes() != historical.canonical_bytes()
    assert manifest.sha256 != historical.sha256
    assert RunManifest.model_validate_json(manifest.canonical_bytes()) == manifest
    assert json.loads(manifest.canonical_bytes())[
        "route_seat_behavioral_capability_plan"
    ]["schema"] == "route-seat-behavioral-capability-plan.v1"


@pytest.mark.parametrize("schema_version", (1, 2, 3, 4, 5))
def test_pre_v6_rejects_behavioral_plan(schema_version):
    manifest = _compile_v6()
    payload = manifest.model_dump(mode="json", by_alias=True)
    payload["schema_version"] = schema_version
    with pytest.raises(ValidationError):
        RunManifest.model_validate(payload)


def test_heterogeneous_presentation_and_compact_recovery_remain_per_seat():
    manifest = _compile_v6()
    payload = manifest.model_dump(mode="json", by_alias=True)
    presentation = payload["route_seat_presentation_plan"]["entries"]
    first = presentation[0]
    first["base_profile"] = "compact"
    first["selection_basis"] = "explicit_endpoint"
    # A directly altered policy is rejected: compilation, not a caller, owns
    # the corresponding behavioral grant and manifest identity.
    with pytest.raises(ValidationError, match="BEHAVIORAL_CAPABILITY_PLAN_MISMATCH"):
        RunManifest.model_validate(payload)
