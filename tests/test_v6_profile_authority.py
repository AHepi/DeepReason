"""Transactional v6 presentation follows only durable manifest authority."""

from __future__ import annotations

import pytest

from deepreason.config import Config
from deepreason.harness import Harness
from deepreason.llm.adapter import (
    LLMAdapter,
    SchemaRepairError,
    V6ModelProfileOverrideForbidden,
    build_adapter,
)
from deepreason.llm.budget import TokenMeter
from deepreason.llm.endpoints import MockEndpoint
from deepreason.llm.firewall import leases_from_manifest, route_fingerprint
from deepreason.llm.wire import (
    AliasTable,
    ConjectureTurnV6,
    ConjecturerTurnWireContractV6,
)
from deepreason.report import eval_report
from deepreason.workflow.models import RouteLeaseRefV1, WorkflowTaskKind
from deepreason.workflow.transaction_service import InquiryTransactionService
from tests.test_v6_transaction_qualification import _manifest as _base_manifest
from tests.test_v6_compact_recovery_transition import _bind_classification


def _manifest_for(profile: str):
    manifest = _base_manifest()
    plan = manifest.route_seat_presentation_plan
    assert plan is not None
    return manifest.model_copy(
        update={
            "model_profile": profile,
            "pack_profile": profile,
            "output_profile": profile,
            "route_seat_presentation_plan": plan.model_copy(
                update={
                    "entries": tuple(
                        entry.model_copy(update={"base_profile": profile})
                        for entry in plan.entries
                    )
                }
            ),
            "route_seat_behavioral_capability_plan": (
                manifest.route_seat_behavioral_capability_plan.model_copy(
                    update={
                        "entries": tuple(
                            entry.model_copy(update={"base_profile": profile})
                            for entry in manifest.route_seat_behavioral_capability_plan.entries
                        )
                    }
                )
            ),
        }
    )


def _transactional_adapter(tmp_path, profile: str, responses):
    manifest = _manifest_for(profile)
    harness = Harness(tmp_path)
    route = manifest.roles["conjecturer"][0]
    endpoint = MockEndpoint(
        responses,
        name=route.base_url,
        model=route.model_id,
        max_tokens=route.max_tokens,
    )
    meter = TokenMeter(100_000)
    adapter = LLMAdapter(
        {"conjecturer": endpoint},
        harness.blobs,
        retry_max=2,
        meter=meter,
        model_profile=manifest.model_profile,
        leases=leases_from_manifest(manifest),
        transaction_authority_required=True,
    )
    _bind_classification(harness, manifest)
    adapter.bind_v6_authority(harness, manifest)
    return harness, manifest, adapter, endpoint, meter


def _authorize(harness, manifest, adapter, *, trigger: str):
    aliases = AliasTable()
    contract = ConjecturerTurnWireContractV6(
        reasoning=False,
        aliases=aliases,
        scratch_authoring_policy=manifest.control_plane_policy.scratch_authoring,
    )
    prompt, preview_contract, lease, maximum = adapter.preview_request(
        "conjecturer",
        "PACK",
        ConjectureTurnV6,
        aliases=aliases,
        wire_contract=contract,
    )
    assert preview_contract is contract
    route = lease.route
    service = InquiryTransactionService(harness, manifest, adapter.meter)
    preparation = service.prepare(
        task_kind=WorkflowTaskKind.CONJECTURE,
        attempt_index=0,
        route_lease=RouteLeaseRefV1(
            role="conjecturer",
            seat=0,
            endpoint_id=route.endpoint_id,
            route_sha256=route_fingerprint(route),
        ),
        contract_id=contract.contract_id,
        trigger_ref=trigger,
        formal_fence_seq=0,
        scratch_fence_seq=0,
        task_payload_value={"task": trigger},
    )
    authorization = service.issue(
        preparation,
        plans=(),
        prompt=prompt,
        max_tokens=maximum,
    )
    return contract, authorization


@pytest.mark.parametrize("profile", ("standard", "frontier"))
def test_transactional_v6_adapter_exhaustion_alone_does_not_compact(
    tmp_path,
    profile,
):
    harness, manifest, adapter, endpoint, meter = _transactional_adapter(
        tmp_path / profile,
        profile,
        ["model says compact recovery"],
    )
    contract, authorization = _authorize(
        harness,
        manifest,
        adapter,
        trigger=f"{profile}-schema-exhaustion",
    )

    with pytest.raises(SchemaRepairError) as raised:
        adapter.call(
            "conjecturer",
            "PACK",
            ConjectureTurnV6,
            aliases=AliasTable(),
            wire_contract=contract,
            dispatch_authorization=authorization,
        )

    spend = raised.value.spend
    assert spend is not None and spend.attempts == 1
    assert {attempt.model_profile for attempt in spend.attempt_trace} == {profile}
    assert {attempt.transport_profile for attempt in spend.attempt_trace} == {
        profile
    }
    assert adapter.profile_for("conjecturer") == profile
    assert adapter._compact_recovery_roles == set()
    assert meter.snapshot()["calls"] == 1
    assert meter.snapshot()["reserved"] == 0
    assert endpoint.last_transport_attempts == 1

    _prompt, next_contract, _lease, _maximum = adapter.preview_request(
        "conjecturer",
        "NEXT",
        ConjectureTurnV6,
        aliases=AliasTable(),
        wire_contract=ConjecturerTurnWireContractV6(
            reasoning=False,
            aliases=AliasTable(),
            scratch_authoring_policy=manifest.control_plane_policy.scratch_authoring,
        ),
    )
    assert next_contract.contract_id == "conjecturer.turn.v6"
    harness.record_llm_calls([spend], "dropped-call", "schema-exhausted")
    report = eval_report(harness, Config())
    assert report["process"]["transport_totals"]["compact_recovery_calls"] == 0


def test_transactional_v6_compact_profile_remains_compact_after_exhaustion(tmp_path):
    harness, manifest, adapter, _endpoint, _meter = _transactional_adapter(
        tmp_path / "compact",
        "compact",
        ["invalid compact output"],
    )
    contract, authorization = _authorize(
        harness,
        manifest,
        adapter,
        trigger="compact-schema-exhaustion",
    )

    with pytest.raises(SchemaRepairError) as raised:
        adapter.call(
            "conjecturer",
            "PACK",
            ConjectureTurnV6,
            aliases=AliasTable(),
            wire_contract=contract,
            dispatch_authorization=authorization,
        )

    assert adapter.profile_for("conjecturer") == "compact"
    assert adapter._compact_recovery_roles == set()
    assert {
        attempt.transport_profile for attempt in raised.value.spend.attempt_trace
    } == {"compact"}
    _prompt, next_contract, _lease, _maximum = adapter.preview_request(
        "conjecturer",
        "NEXT",
        ConjectureTurnV6,
        aliases=AliasTable(),
        wire_contract=ConjecturerTurnWireContractV6(
            reasoning=False,
            aliases=AliasTable(),
            scratch_authoring_policy=manifest.control_plane_policy.scratch_authoring,
        ),
    )
    assert next_contract.contract_id == "conjecturer.turn.v6"


def test_v6_durable_drop_cannot_rehydrate_compact_recovery(
    tmp_path,
    monkeypatch,
):
    harness, manifest, adapter, endpoint, _meter = _transactional_adapter(
        tmp_path / "restart",
        "standard",
        ["bad durable output"],
    )
    contract, authorization = _authorize(
        harness,
        manifest,
        adapter,
        trigger="durable-schema-exhaustion",
    )
    with pytest.raises(SchemaRepairError) as raised:
        adapter.call(
            "conjecturer",
            "PACK",
            ConjectureTurnV6,
            aliases=AliasTable(),
            wire_contract=contract,
            dispatch_authorization=authorization,
        )
    harness.record_llm_calls(
        [raised.value.spend], "dropped-call", "schema-exhausted"
    )

    replacement = MockEndpoint(
        [],
        name=endpoint.name,
        model=endpoint.model,
        max_tokens=endpoint.max_tokens,
    )
    monkeypatch.setattr(
        "deepreason.llm.adapter._endpoint_from_spec",
        lambda _spec: replacement,
    )
    rebuilt = build_adapter(
        Config(),
        harness.blobs,
        run_manifest=manifest,
        process_events=Harness(harness.root).log.read(),
    )
    rebuilt.bind_v6_authority(Harness(harness.root), manifest)

    assert rebuilt.transaction_authority_required is True
    assert rebuilt.rehydrate_compact_recovery(Harness(harness.root).log.read()) == (
        frozenset()
    )
    assert rebuilt.profile_for("conjecturer") == "standard"
    assert rebuilt._compact_recovery_roles == set()
    _prompt, next_contract, _lease, _maximum = rebuilt.preview_request(
        "conjecturer",
        "NEXT",
        ConjectureTurnV6,
        aliases=AliasTable(),
        wire_contract=ConjecturerTurnWireContractV6(
            reasoning=False,
            aliases=AliasTable(),
            scratch_authoring_policy=manifest.control_plane_policy.scratch_authoring,
        ),
    )
    assert next_contract.contract_id == "conjecturer.turn.v6"


@pytest.mark.parametrize(
    ("frozen", "requested"),
    (("standard", "compact"), ("frontier", "standard")),
)
def test_v6_per_call_profile_override_fails_before_any_effect(
    tmp_path,
    frozen,
    requested,
):
    harness, _manifest, adapter, endpoint, meter = _transactional_adapter(
        tmp_path / f"{frozen}-override",
        frozen,
        [],
    )

    with pytest.raises(V6ModelProfileOverrideForbidden) as raised:
        adapter.preview_request(
            "conjecturer",
            "PACK",
            ConjectureTurnV6,
            aliases=AliasTable(),
            model_profile=requested,
        )

    assert raised.value.code == "V6_MODEL_PROFILE_OVERRIDE_FORBIDDEN"
    assert raised.value.frozen_profile == frozen
    assert endpoint.last_transport_attempts == 0
    assert meter.snapshot()["calls"] == 0
    assert meter.snapshot()["reserved"] == 0
    assert harness.workflow_state.transaction_work == {}


@pytest.mark.parametrize("profile", ("standard", "frontier", "compact"))
def test_v6_exact_frozen_per_call_profile_is_permitted(tmp_path, profile):
    _harness, _manifest, adapter, endpoint, meter = _transactional_adapter(
        tmp_path / f"{profile}-exact",
        profile,
        [],
    )

    _prompt, contract, _lease, _maximum = adapter.preview_request(
        "conjecturer",
        "PACK",
        ConjectureTurnV6,
        aliases=AliasTable(),
        model_profile=profile,
        wire_contract=ConjecturerTurnWireContractV6(
            reasoning=False,
            aliases=AliasTable(),
            scratch_authoring_policy=_manifest.control_plane_policy.scratch_authoring,
        ),
    )

    assert adapter.profile_for("conjecturer") == profile
    assert contract.contract_id == "conjecturer.turn.v6"
    assert endpoint.last_transport_attempts == 0
    assert meter.snapshot()["calls"] == 0
