"""Runtime and replay enforcement for frozen route-seat behavioral grants."""

from __future__ import annotations

import pytest

from deepreason.harness import Harness
from deepreason.cli.doctor import run_production_contract_doctor
from deepreason.llm.adapter import LLMAdapter, WorkflowAuthorizationError
from deepreason.llm.budget import TokenMeter
from deepreason.llm.contracts import ConjecturerOutput
from deepreason.llm.endpoints import MockEndpoint
from deepreason.llm.firewall import leases_from_manifest, route_fingerprint
from deepreason.llm.wire import DirectWireContract
from deepreason.run_manifest import RunManifest, RunManifestError
from deepreason.workflow.models import RouteLeaseRefV1, WorkflowTaskKind
from deepreason.workflow.transaction import (
    WorkLifecycleTransitionV1,
    WorkPreparationV1,
    WorkTransitionKind,
)
from deepreason.workflow.transaction_service import InquiryTransactionService
from tests.test_v6_transaction_qualification import _manifest
from tests.test_cli_production_doctor_v6 import _admitted_case


def _bind_classification(harness, manifest):
    report = run_production_contract_doctor(
        manifest,
        case_executor=lambda _manifest, _pair, index: _admitted_case(index),
    )
    harness.bind_model_classification(manifest, report)


def _route_ref(manifest):
    route = manifest.roles["conjecturer"][0]
    return RouteLeaseRefV1(
        role="conjecturer",
        seat=0,
        endpoint_id=route.endpoint_id,
        route_sha256=route_fingerprint(route),
    )


def test_transaction_prepare_requires_exact_route_seat_contract_before_append(tmp_path):
    manifest = _manifest()
    harness = Harness(tmp_path)
    _bind_classification(harness, manifest)
    service = InquiryTransactionService(harness, manifest, TokenMeter(10_000))
    before = tuple(harness.log.read())

    with pytest.raises(
        RunManifestError, match="V6_BEHAVIORAL_CONTRACT_NOT_AUTHORIZED"
    ):
        service.prepare(
            task_kind=WorkflowTaskKind.CONJECTURE,
            attempt_index=0,
            route_lease=_route_ref(manifest),
            contract_id="conjectureroutput.direct.v1",
            trigger_ref="unauthorized-contract",
            formal_fence_seq=0,
            scratch_fence_seq=0,
        )

    assert tuple(harness.log.read()) == before
    assert harness.workflow_state.transaction_work == {}


def test_transaction_prepare_accepts_the_exact_manifest_grant(tmp_path):
    manifest = _manifest()
    harness = Harness(tmp_path)
    _bind_classification(harness, manifest)
    service = InquiryTransactionService(harness, manifest, TokenMeter(10_000))
    preparation = service.prepare(
        task_kind=WorkflowTaskKind.CONJECTURE,
        attempt_index=0,
        route_lease=_route_ref(manifest),
        contract_id="conjecturer.turn.v6",
        trigger_ref="authorized-contract",
        formal_fence_seq=0,
        scratch_fence_seq=0,
        task_payload_value={"task": "authorized-contract"},
    )

    assert preparation.contract_id == "conjecturer.turn.v6"
    assert harness.workflow_state.transaction_work[preparation.id].preparation == preparation


def test_historical_plan_absence_grants_no_new_transaction_authority(tmp_path):
    manifest = _manifest()
    payload = manifest.model_dump(mode="json", by_alias=True)
    payload.pop("route_seat_behavioral_capability_plan")
    historical = RunManifest.model_validate(payload)

    with pytest.raises(
        RunManifestError, match="V6_BEHAVIORAL_CAPABILITY_PLAN_REQUIRED"
    ):
        InquiryTransactionService(Harness(tmp_path), historical, TokenMeter(10_000))


def test_adapter_rejects_ungranted_contract_during_preview_before_dispatch(tmp_path):
    manifest = _manifest()
    harness = Harness(tmp_path)
    route = manifest.roles["conjecturer"][0]
    calls = []
    endpoint = MockEndpoint(
        lambda _prompt: calls.append(True) or "{}",
        name=route.base_url,
        model=route.model_id,
        max_tokens=route.max_tokens,
    )
    adapter = LLMAdapter(
        {"conjecturer": endpoint},
        harness.blobs,
        meter=TokenMeter(10_000),
        model_profile=manifest.model_profile,
        leases=leases_from_manifest(manifest),
        transaction_authority_required=True,
    )
    _bind_classification(harness, manifest)
    adapter.bind_v6_authority(harness, manifest)

    with pytest.raises(WorkflowAuthorizationError, match="behavioral authority"):
        adapter.preview_request(
            "conjecturer",
            "PACK",
            ConjecturerOutput,
            wire_contract=DirectWireContract(ConjecturerOutput),
        )

    assert calls == []
    assert harness.workflow_state.transaction_work == {}


def test_late_manifest_binding_rejects_durable_foreign_contract(tmp_path):
    manifest = _manifest()
    harness = Harness(tmp_path)
    preparation = WorkPreparationV1.create(
        manifest_digest=manifest.sha256,
        task_kind=WorkflowTaskKind.CONJECTURE,
        attempt_index=0,
        formal_fence_seq=0,
        scratch_fence_seq=0,
        trigger_ref="forged-late-bound-contract",
        route_lease=_route_ref(manifest),
        contract_id="batch-critic.v2",
        task_payload_value={"task": "forged-late-bound-contract"},
    )
    transition = WorkLifecycleTransitionV1.create(
        work_id=preparation.id,
        attempt_index=0,
        transition_kind=WorkTransitionKind.WORK_PREPARED,
        trigger_ref=preparation.trigger_ref,
    )
    harness.record_transaction_transition(transition, records=(preparation,))
    assert harness.workflow_state._run_manifest is None

    with pytest.raises(
        ValueError,
        match="work preparation contract lacks route-seat behavioral authority",
    ):
        InquiryTransactionService(harness, manifest, TokenMeter(10_000))

    assert harness.workflow_state._run_manifest is None
    assert (
        harness.workflow_state.transaction_work[preparation.id].preparation
        == preparation
    )
