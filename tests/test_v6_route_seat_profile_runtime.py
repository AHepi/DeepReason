"""Transactional v6 consumes exact manifest route-seat presentation authority."""

from __future__ import annotations

import json

import pytest

from deepreason.application.models import derive_model_execution_summary
from deepreason.conjecture_turn import ConjectureTurnV6
from deepreason.harness import Harness
from deepreason.llm.adapter import LLMAdapter, V6ModelProfileOverrideForbidden
from deepreason.llm.budget import TokenMeter
from deepreason.llm.contracts import ConjecturerOutput
from deepreason.llm.endpoints import MockEndpoint
from deepreason.llm.firewall import leases_from_manifest, route_fingerprint
from deepreason.llm.wire import AliasTable, ConjecturerTurnWireContractV6
from deepreason.run_manifest import (
    RunManifest,
    resolve_route_seat_base_profile,
)
from tests.test_v6_route_seat_presentation_plan import _compile, _route
from tests.test_v6_compact_recovery_transition import _bind_classification


def _heterogeneous_manifest():
    return _compile(
        {
            "conjecturer": [
                _route("conj-compact", model_profile="compact"),
                _route("conj-standard", model_profile="standard"),
            ],
            "argumentative_critic": _route(
                "critic-frontier", model_profile="frontier"
            ),
            "summarizer": _route(
                "summary-compact", model_profile="compact"
            ),
        },
        model_profile="standard",
    )


def _adapter(harness: Harness, manifest: RunManifest):
    endpoints = {}
    for role, routes in manifest.roles.items():
        if not routes:
            continue
        built = []
        for route in routes:
            endpoint = MockEndpoint(
                [],
                name=route.base_url,
                model=route.model_id,
                max_tokens=route.max_tokens,
            )
            endpoint.endpoint_id = route.endpoint_id
            endpoint.family = route.family
            endpoint.model_revision = route.model_revision
            endpoint.output_mechanism = route.output_mechanism
            endpoint.context_window_tokens = route.context_window_tokens
            built.append(endpoint)
        endpoints[role] = built if len(built) > 1 else built[0]
    adapter = LLMAdapter(
        endpoints,
        harness.blobs,
        retry_max=0,
        meter=TokenMeter(100_000),
        model_profile=manifest.model_profile,
        leases=leases_from_manifest(manifest),
        transaction_authority_required=True,
    )
    _bind_classification(harness, manifest)
    adapter.bind_v6_authority(harness, manifest)
    return adapter, endpoints


def test_preview_uses_independent_route_seat_base_profiles(tmp_path):
    manifest = _heterogeneous_manifest()
    harness = Harness(tmp_path)
    adapter, _endpoints = _adapter(harness, manifest)
    aliases = AliasTable()
    contract = ConjecturerTurnWireContractV6(
        reasoning=False,
        aliases=aliases,
        scratch_authoring_policy=manifest.control_plane_policy.scratch_authoring,
    )

    compact_prompt, compact_contract, compact_lease, _ = adapter.preview_request(
        "conjecturer",
        "PACK",
        ConjectureTurnV6,
        endpoint_index=0,
        aliases=aliases,
        wire_contract=contract,
    )
    standard_prompt, standard_contract, standard_lease, _ = adapter.preview_request(
        "conjecturer",
        "PACK",
        ConjectureTurnV6,
        endpoint_index=1,
        aliases=aliases,
        wire_contract=contract,
    )

    assert adapter.base_profile_for("conjecturer", 0) == "compact"
    assert adapter.profile_for("conjecturer", 0) == "compact"
    assert adapter.base_profile_for("conjecturer", 1) == "standard"
    assert adapter.profile_for("conjecturer", 1) == "standard"
    assert adapter.profile_for("argumentative_critic", 0) == "frontier"
    assert adapter.profile_for("summarizer", 0) == "compact"
    assert compact_contract is standard_contract is contract
    assert compact_contract.contract_id == "conjecturer.turn.v6"
    assert compact_prompt != standard_prompt
    assert compact_lease.seat == 0
    assert standard_lease.seat == 1


def test_explicit_profile_cannot_override_exact_route_seat(tmp_path):
    manifest = _heterogeneous_manifest()
    harness = Harness(tmp_path)
    adapter, endpoints = _adapter(harness, manifest)

    with pytest.raises(V6ModelProfileOverrideForbidden) as raised:
        adapter.preview_request(
            "conjecturer",
            "PACK",
            ConjecturerOutput,
            endpoint_index=0,
            aliases=AliasTable(),
            model_profile="standard",
        )

    assert raised.value.code == "V6_MODEL_PROFILE_OVERRIDE_FORBIDDEN"
    assert adapter.meter.snapshot()["calls"] == 0
    assert endpoints["conjecturer"][0].last_transport_attempts == 0


def test_same_model_on_different_roles_retains_independent_profiles(tmp_path):
    conjecturer = _route("shared-conjecturer", model_profile="compact")
    critic = _route("shared-critic", model_profile="frontier")
    conjecturer["model"] = critic["model"] = "shared-model"
    manifest = _compile(
        {
            "conjecturer": conjecturer,
            "argumentative_critic": critic,
        },
        model_profile="standard",
    )
    adapter, _endpoints = _adapter(Harness(tmp_path), manifest)

    assert adapter.profile_for("conjecturer", 0) == "compact"
    assert adapter.profile_for("argumentative_critic", 0) == "frontier"


def test_heterogeneous_summary_and_historical_global_fallback(tmp_path):
    manifest = _heterogeneous_manifest()
    harness = Harness(tmp_path / "planned")
    adapter, _endpoints = _adapter(harness, manifest)
    summary = derive_model_execution_summary(harness, manifest)

    assert summary.mode == "route_seat_base"
    assert summary.base_profile == "standard"
    assert tuple(
        (
            item.role,
            item.seat,
            item.endpoint_id,
            item.route_sha256,
            item.base_profile,
            item.selection_basis,
        )
        for item in summary.route_seat_bases
    ) == tuple(
        sorted(
            (
                entry.role,
                entry.seat,
                entry.endpoint_id,
                route_fingerprint(manifest.roles[entry.role][entry.seat]),
                entry.base_profile,
                entry.selection_basis,
            )
            for entry in manifest.route_seat_presentation_plan.entries
        )
    )
    assert adapter.profile_for("conjecturer", 0) == "compact"

    payload = json.loads(manifest.canonical_bytes())
    payload.pop("route_seat_presentation_plan")
    payload.pop("route_seat_behavioral_capability_plan")
    payload.pop("route_seat_contract_decomposition_plan")
    historical = RunManifest.model_validate(payload)
    route = historical.roles["conjecturer"][0]
    assert resolve_route_seat_base_profile(
        historical,
        role="conjecturer",
        seat=0,
        endpoint_id=route.endpoint_id,
    ) == historical.model_profile
