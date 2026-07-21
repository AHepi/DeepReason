"""Frozen authority for deterministic strong-to-atomic v6 execution."""

from __future__ import annotations

import json

import pytest

from deepreason.cli.doctor import production_contract_pairs
from deepreason.llm.firewall import route_fingerprint
from deepreason.llm.wire import (
    ATOMIC_CONJECTURE_CONTRACT_V1,
    ATOMIC_CRITIC_CONTRACT_V1,
    AliasTable,
    AtomicConjectureWireContractV1,
    AtomicCriticWireContractV1,
)
from deepreason.conjecture_turn import ReasoningConjecturerTurnV6
from deepreason.run_manifest import (
    RouteSeatContractDecompositionPlanV1,
    RunManifest,
    RunManifestError,
    _compile_route_seat_behavioral_capability_plan,
    resolve_route_seat_contract_decomposition,
)
from tests.test_v6_contract_schema_repair_policy import _compile_v6


def test_new_v6_manifest_freezes_exact_atomic_edges_and_doctor_pairs():
    manifest = _compile_v6()
    plan = manifest.route_seat_contract_decomposition_plan
    assert isinstance(plan, RouteSeatContractDecompositionPlanV1)
    entries = {(entry.role, entry.seat): entry for entry in plan.entries}

    conjecture = entries[("conjecturer", 0)]
    criticism = entries[("argumentative_critic", 0)]
    assert (
        conjecture.source_contract_id,
        conjecture.atomic_contract_id,
        conjecture.child_partition,
        conjecture.coverage,
        conjecture.source_failure_preserved,
    ) == (
        "conjecturer.turn.v6",
        ATOMIC_CONJECTURE_CONTRACT_V1,
        "conjecture_candidate_slot",
        "all_deterministically_assigned_children",
        True,
    )
    assert (
        criticism.source_contract_id,
        criticism.atomic_contract_id,
        criticism.child_partition,
    ) == (
        "batch-critic.v2",
        ATOMIC_CRITIC_CONTRACT_V1,
        "critic_target",
    )
    assert tuple(
        (entry.role, entry.seat, entry.source_contract_id) for entry in plan.entries
    ) == tuple(
        sorted(
            (entry.role, entry.seat, entry.source_contract_id)
            for entry in plan.entries
        )
    )
    assert {pair.contract_id for pair in production_contract_pairs(manifest)} >= {
        ATOMIC_CONJECTURE_CONTRACT_V1,
        ATOMIC_CRITIC_CONTRACT_V1,
    }


def test_atomic_contracts_are_real_separately_named_and_target_bound():
    aliases = AliasTable({"SRC_001": "target-ref"})
    conjecture = AtomicConjectureWireContractV1(aliases)
    critic = AtomicCriticWireContractV1(aliases, expected_target="target-ref")

    assert conjecture.contract_id == ATOMIC_CONJECTURE_CONTRACT_V1
    assert critic.contract_id == ATOMIC_CRITIC_CONTRACT_V1
    assert critic.model_json_schema()["properties"]["target_alias"]["const"] == (
        "SRC_001"
    )

    reasoning = AtomicConjectureWireContractV1(aliases, reasoning=True)
    reasoning_output = reasoning.compile(
        reasoning.validate_value(
            {
                "candidate": {
                    "claim": "A bounded mechanism",
                    "mechanism": "One explicit causal step",
                    "counterconditions": ["The step is not observed"],
                    "typicality": 0.5,
                    "optional_refs": ["SRC_001"],
                }
            }
        )
    )
    assert isinstance(reasoning_output, ReasoningConjecturerTurnV6)
    assert reasoning_output.candidates[0].optional_refs == ("target-ref",)


def test_decomposition_resolver_is_exact_and_historical_absence_grants_nothing():
    manifest = _compile_v6()
    route = manifest.roles["conjecturer"][0]
    grant = resolve_route_seat_contract_decomposition(
        manifest,
        role="conjecturer",
        seat=0,
        endpoint_id=route.endpoint_id,
        route_sha256=route_fingerprint(route),
        source_contract_id="conjecturer.turn.v6",
    )
    assert grant.atomic_contract_id == ATOMIC_CONJECTURE_CONTRACT_V1
    with pytest.raises(RunManifestError):
        resolve_route_seat_contract_decomposition(
            manifest,
            role="conjecturer",
            seat=0,
            endpoint_id=route.endpoint_id,
            route_sha256="0" * 64,
            source_contract_id="conjecturer.turn.v6",
        )

    payload = json.loads(manifest.canonical_bytes())
    payload.pop("route_seat_contract_decomposition_plan")
    payload.pop("route_seat_behavioral_capability_plan")
    historical = RunManifest.model_validate(payload)
    assert historical.route_seat_contract_decomposition_plan is None
    with pytest.raises(RunManifestError):
        resolve_route_seat_contract_decomposition(
            historical,
            role="conjecturer",
            seat=0,
            endpoint_id=route.endpoint_id,
            route_sha256=route_fingerprint(route),
            source_contract_id="conjecturer.turn.v6",
        )


def test_explicit_empty_plan_authorizes_strong_contract_but_no_atomic_fallback():
    manifest = _compile_v6()
    payload = json.loads(manifest.canonical_bytes())
    payload["route_seat_contract_decomposition_plan"]["entries"] = []
    payload.pop("route_seat_behavioral_capability_plan")
    provisional = RunManifest.model_validate(payload)
    payload["route_seat_behavioral_capability_plan"] = (
        _compile_route_seat_behavioral_capability_plan(provisional).model_dump(
            mode="json", by_alias=True, exclude_none=True
        )
    )
    fallback_disabled = RunManifest.model_validate(payload)
    conjecturer = next(
        entry
        for entry in fallback_disabled.route_seat_behavioral_capability_plan.entries
        if entry.role == "conjecturer" and entry.seat == 0
    )

    assert tuple(item.contract_id for item in conjecturer.contracts) == (
        "conjecturer.turn.v6",
    )
    route = fallback_disabled.roles["conjecturer"][0]
    with pytest.raises(RunManifestError) as caught:
        resolve_route_seat_contract_decomposition(
            fallback_disabled,
            role="conjecturer",
            seat=0,
            endpoint_id=route.endpoint_id,
            route_sha256=route_fingerprint(route),
            source_contract_id="conjecturer.turn.v6",
        )
    assert caught.value.code == "V6_CONTRACT_DECOMPOSITION_GRANT_REQUIRED"


def test_plan_tampering_changes_identity_and_malformed_entries_fail():
    manifest = _compile_v6()
    payload = json.loads(manifest.canonical_bytes())
    plan = payload["route_seat_contract_decomposition_plan"]
    plan["entries"][0]["maximum_children"] -= 1
    payload.pop("route_seat_behavioral_capability_plan")
    with pytest.raises(ValueError):
        RunManifest.model_validate(payload)

    malformed = json.loads(manifest.canonical_bytes())
    malformed["route_seat_contract_decomposition_plan"]["entries"][0][
        "model_may_choose"
    ] = True
    with pytest.raises(ValueError):
        RunManifest.model_validate(malformed)
