"""Frozen authority for Milestone 5 staged bridge and minimal scratch contracts."""

from __future__ import annotations

import pytest
from deepreason.bridge.compose import BridgeCompositionBatchWireContractV1
from deepreason.bridge.ledger import ClaimLedgerBatchWireContractV1
from deepreason.cli.doctor import (
    _production_probe_contract,
    production_contract_pairs,
    run_production_contract_doctor,
)
from deepreason.scratch.contracts import (
    ClusterGuideMinimalWireContract,
    ScratchBlockMinimalWireContract,
    ScratchLinkMinimalWireContract,
)
from tests.test_cli_production_doctor_v6 import (
    _admitted_case,
    _manifest as _doctor_manifest,
)
from tests.test_v6_contract_schema_repair_policy import _compile_v6


STAGED_CONTRACTS = {
    "bridge.ledger-batch.v1",
    "bridge.composition-batch.v1",
    "scratch.block.minimal.v1",
    "scratch.link.minimal.v1",
    "scratch.cluster-guide.minimal.v1",
}


def _manifest():
    return _compile_v6(
        scratch_authoring=True,
        scratch_enabled=True,
        bridge_mode="grounded_two_stage",
        grounding_review=True,
    )


def test_staged_edges_are_exact_sorted_and_separately_authorized():
    manifest = _manifest()
    plan = manifest.route_seat_contract_decomposition_plan
    assert plan is not None
    staged = {
        entry.atomic_contract_id: entry
        for entry in plan.entries
        if entry.atomic_contract_id in STAGED_CONTRACTS
    }

    assert set(staged) == STAGED_CONTRACTS
    assert staged["bridge.ledger-batch.v1"].source_contract_id == "bridge.ledger.v3"
    assert staged["bridge.ledger-batch.v1"].child_partition == "bridge_catalog_batch"
    assert staged["bridge.composition-batch.v1"].source_contract_id == (
        "bridge.composition.v2"
    )
    assert staged["bridge.composition-batch.v1"].child_partition == (
        "bridge_ledger_batch"
    )
    assert all(
        staged[contract].child_partition == "scratch_single_object"
        and staged[contract].maximum_children == 1
        for contract in STAGED_CONTRACTS
        if contract.startswith("scratch.")
    )
    keys = tuple((item.role, item.seat, item.source_contract_id) for item in plan.entries)
    assert keys == tuple(sorted(set(keys)))

    repair_ids = {
        item.contract_id for item in manifest.contract_schema_repair_policy.grants
    }
    behavioral_ids = {
        item.contract_id
        for route in manifest.route_seat_behavioral_capability_plan.entries
        for item in route.contracts
    }
    assert STAGED_CONTRACTS <= repair_ids
    assert STAGED_CONTRACTS <= behavioral_ids


def test_new_contracts_are_real_strict_production_constructors():
    manifest = _manifest()
    pairs = {
        pair.contract_id: pair
        for pair in production_contract_pairs(manifest)
        if pair.contract_id in STAGED_CONTRACTS
    }
    assert set(pairs) == STAGED_CONTRACTS

    constructed = {
        contract_id: _production_probe_contract(manifest, pair, 0)[0]
        for contract_id, pair in pairs.items()
    }
    assert isinstance(constructed["bridge.ledger-batch.v1"], ClaimLedgerBatchWireContractV1)
    assert isinstance(
        constructed["bridge.composition-batch.v1"],
        BridgeCompositionBatchWireContractV1,
    )
    assert isinstance(
        constructed["scratch.block.minimal.v1"], ScratchBlockMinimalWireContract
    )
    assert isinstance(
        constructed["scratch.link.minimal.v1"], ScratchLinkMinimalWireContract
    )
    assert isinstance(
        constructed["scratch.cluster-guide.minimal.v1"],
        ClusterGuideMinimalWireContract,
    )
    assert all(contract.contract_id == contract_id for contract_id, contract in constructed.items())

    with pytest.raises(ValueError, match="extra field"):
        constructed["scratch.block.minimal.v1"].validate_value(
            {"content": "one thought", "why_keep_this": "not in minimal contract"}
        )


def test_doctor_evidence_classifies_every_staged_contract_on_its_exact_route():
    manifest = _doctor_manifest(scratch_authoring=True)
    report = run_production_contract_doctor(
        manifest,
        case_executor=lambda _manifest, _pair, index: _admitted_case(index),
    )
    assert report.summary.qualified is True
    assert report.route_seat_model_classification is not None
    qualified_contracts = {
        contract_id
        for entry in report.route_seat_model_classification.entries
        if entry.selected_class == "qualified_exact_behavior"
        for contract_id in entry.authorized_contract_ids
    }
    assert STAGED_CONTRACTS <= qualified_contracts


def test_disabled_features_add_no_staged_bridge_or_scratch_authority():
    manifest = _compile_v6(
        scratch_authoring=False,
        scratch_enabled=False,
        bridge_mode="legacy_thesis",
    )
    contract_ids = {
        contract.contract_id
        for route in manifest.route_seat_behavioral_capability_plan.entries
        for contract in route.contracts
    }
    assert STAGED_CONTRACTS.isdisjoint(contract_ids)
