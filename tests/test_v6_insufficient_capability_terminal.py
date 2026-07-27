"""Durable route-seat insufficient-capability authority and replay."""

from __future__ import annotations

import pytest

from deepreason.cli.doctor import run_production_contract_doctor
from deepreason.conjecture_turn import ConjectureTurnV6
from deepreason.llm.adapter import WorkflowAuthorizationError
from deepreason.llm.firewall import leases_from_manifest, route_fingerprint
from deepreason.llm.repair import SchemaExhaustedError
from deepreason.llm.wire import AliasTable, ConjecturerTurnWireContractV6
from deepreason.run_manifest import RunManifestError, resolve_route_seat_base_profile
from deepreason.scratch.authoring import ScratchAuthoringService
from deepreason.scratch.render import ScratchRenderer
from deepreason.scratch.service import ScratchService
from deepreason.workflow.transaction import RouteSeatInsufficientCapabilityV1
from deepreason.workflow.models import RouteLeaseRefV1, WorkflowTaskKind
from deepreason.workflow.transaction_service import InquiryTransactionService

from tests.test_v6_scratch_authoring_transactions import (
    _admitted_qualification_case,
    _adapter,
    _bind_v6_root,
    _context,
)


def _exhaust_minimal_block(root, *, route_profiles=None):
    manifest = _bind_v6_root(
        root,
        grant_ceiling=("scratch.block.minimal.v1", 0),
        route_profiles=route_profiles,
    )
    service = ScratchService(root)
    renderer, rendered, *_rest = _context(service)
    adapter, _endpoints = _adapter(
        service,
        manifest,
        {"conjecturer": ["not-json"] * 4},
    )
    with pytest.raises(SchemaExhaustedError):
        ScratchAuthoringService(
            service,
            adapter,
            renderer=renderer,
            run_manifest=manifest,
        ).author_block(rendered, task="Try the smallest authorized idea")
    return manifest, service, adapter, rendered


def test_smallest_contract_exhaustion_persists_one_exact_route_terminal(tmp_path):
    root = tmp_path / "insufficient-block"
    manifest, service, adapter, _rendered = _exhaust_minimal_block(root)

    work = tuple(service.harness.workflow_state.transaction_work.values())
    assert tuple(item.preparation.contract_id for item in work) == (
        "scratch.block.compact.v1",
        "scratch.block.compact.v1",
        "scratch.block.minimal.v1",
    )
    assert tuple(item.terminal.status for item in work) == (
        "rejected",
        "schema_exhausted",
        "schema_exhausted",
    )
    assert all(
        item.terminal.insufficient_capability_ref is None for item in work[:-1]
    )

    outcomes = service.harness.workflow_state.insufficient_capability_by_route_seat
    assert len(outcomes) == 1
    outcome = next(iter(outcomes.values()))
    assert isinstance(outcome, RouteSeatInsufficientCapabilityV1)
    assert outcome.work_id == work[-1].preparation.id
    assert outcome.contract_id == "scratch.block.minimal.v1"
    assert outcome.attempted_work_ids == tuple(
        item.preparation.id for item in work
    )
    assert outcome.attempted_contract_ids == tuple(
        item.preparation.contract_id for item in work
    )
    assert outcome.decomposition_transition_refs == (
        next(
            iter(
                service.harness.workflow_state.
                contract_decomposition_by_source_work.values()
            )
        ).id,
    )
    assert len(outcome.compact_recovery_transition_refs) == 1
    assert outcome.maximum_schema_repairs == 0
    assert outcome.maximum_provider_calls == 1
    assert outcome.observed_provider_calls == 1
    assert outcome.classification_plan_ref == (
        service.harness.workflow_state.route_seat_model_classification.id
    )
    assert outcome.classification_binding_ref == (
        service.harness.workflow_state.model_classification_binding.id
    )
    assert work[-1].terminal.insufficient_capability_ref == outcome.id
    terminal_event = next(
        event
        for event in service.harness.log.read()
        if work[-1].terminal.id in event.outputs
    )
    assert tuple(terminal_event.outputs) == (
        outcome.id,
        work[-1].terminal.id,
        work[-1].transitions[-1].id,
    )
    assert adapter.meter.calls == 3
    assert adapter.meter.reserved == 0

    restarted = ScratchService(root)
    assert restarted.harness.workflow_state.insufficient_capability_by_route_seat == (
        outcomes
    )
    assert restarted.harness.workflow_state.digest == (
        service.harness.workflow_state.digest
    )


def test_terminal_route_is_sticky_but_another_route_remains_authorized(tmp_path):
    root = tmp_path / "insufficient-isolation"
    manifest, service, _adapter_value, rendered = _exhaust_minimal_block(root)
    redispatches = []

    def forbidden(prompt):
        redispatches.append(prompt)
        raise AssertionError("terminal route seat reached the provider")

    blocked_adapter, _endpoints = _adapter(
        service,
        manifest,
        {"conjecturer": forbidden},
    )
    before_work = tuple(service.harness.workflow_state.transaction_work)
    before_seq = service.harness._next_seq
    with pytest.raises(ValueError, match="V6_ROUTE_SEAT_INSUFFICIENT_CAPABILITY"):
        ScratchAuthoringService(
            service,
            blocked_adapter,
            renderer=ScratchRenderer(service),
            run_manifest=manifest,
        ).author_block(rendered, task="Do not retry a terminal route")
    assert redispatches == []
    assert blocked_adapter.meter.calls == 0
    assert tuple(service.harness.workflow_state.transaction_work) == before_work
    assert service.harness._next_seq == before_seq

    link_adapter, _endpoints = _adapter(
        service,
        manifest,
        {
            "synthesizer": [
                '{"from_index":0,"to_index":1,"relation_hint":"remains separate"}'
            ]
        },
    )
    link = ScratchAuthoringService(
        service,
        link_adapter,
        renderer=ScratchRenderer(service),
        run_manifest=manifest,
    ).author_link(rendered, task="Use the unaffected route seat")
    assert link.body.relation_hint == "remains separate"
    assert link_adapter.meter.calls == 1


def test_prepared_work_cannot_issue_after_route_terminal(tmp_path):
    root = tmp_path / "insufficient-prepared-before-terminal"
    manifest = _bind_v6_root(
        root,
        grant_ceiling=("scratch.block.minimal.v1", 0),
    )
    service = ScratchService(root)
    renderer, rendered, *_rest = _context(service)
    adapter, _endpoints = _adapter(
        service,
        manifest,
        {"conjecturer": ["not-json"] * 4},
    )
    service.harness.bind_model_classification(
        manifest,
        run_production_contract_doctor(
            manifest,
            case_executor=_admitted_qualification_case,
        ),
    )
    lease = leases_from_manifest(manifest)["conjecturer"][0]
    route_ref = RouteLeaseRefV1(
        role=lease.role,
        seat=lease.seat,
        endpoint_id=lease.route.endpoint_id,
        route_sha256=route_fingerprint(lease.route),
    )
    transaction = InquiryTransactionService(
        service.harness,
        manifest,
        adapter.meter,
    )
    fence = max(0, service.harness._next_seq - 1)
    stale = transaction.prepare(
        task_kind=WorkflowTaskKind.SCRATCH_AUTHORING,
        attempt_index=0,
        route_lease=route_ref,
        contract_id="scratch.block.compact.v1",
        trigger_ref="prepared-before-route-capability-terminal",
        formal_fence_seq=fence,
        scratch_fence_seq=fence,
        task_payload_value={
            "schema": "test.stale-scratch-authoring.v1",
            "ordinal": 99,
        },
    )

    with pytest.raises(SchemaExhaustedError):
        ScratchAuthoringService(
            service,
            adapter,
            renderer=renderer,
            run_manifest=manifest,
        ).author_block(rendered, task="Exhaust the smallest authorized contract")

    assert len(service.harness.workflow_state.insufficient_capability_by_route_seat) == 1
    stale_item = service.harness.workflow_state.transaction_work[stale.id]
    assert not stale_item.issued
    assert stale_item.terminal is None
    before_seq = service.harness._next_seq
    before_calls = adapter.meter.calls
    before_reserved = adapter.meter.reserved
    before_work = tuple(service.harness.workflow_state.transaction_work.items())

    with pytest.raises(ValueError, match="V6_ROUTE_SEAT_INSUFFICIENT_CAPABILITY"):
        transaction.issue(
            stale,
            plans=(),
            prompt="This prepared work must never receive dispatch authority.",
            max_tokens=8,
        )

    assert service.harness._next_seq == before_seq
    assert adapter.meter.calls == before_calls
    assert adapter.meter.reserved == before_reserved == 0
    assert tuple(service.harness.workflow_state.transaction_work.items()) == before_work


def test_issued_base_compact_dispatch_cannot_survive_route_terminal(tmp_path):
    root = tmp_path / "issued-before-insufficient-base-compact"
    manifest = _bind_v6_root(
        root,
        grant_ceiling=("scratch.block.minimal.v1", 0),
        route_profiles={"conjecturer": "compact"},
    )
    service = ScratchService(root)
    renderer, rendered, *_rest = _context(service)
    adapter, _endpoints = _adapter(
        service,
        manifest,
        {"conjecturer": ["not-json"] * 4},
    )
    service.harness.bind_model_classification(
        manifest,
        run_production_contract_doctor(
            manifest,
            case_executor=_admitted_qualification_case,
        ),
    )
    adapter.bind_v6_authority(service.harness, manifest)
    aliases = AliasTable()
    contract = ConjecturerTurnWireContractV6(
        reasoning=False,
        aliases=aliases,
        scratch_authoring_policy=manifest.control_plane_policy.scratch_authoring,
    )
    base_profile = resolve_route_seat_base_profile(
        manifest,
        role="conjecturer",
        seat=0,
        endpoint_id=manifest.roles["conjecturer"][0].endpoint_id,
    )
    pack = "Retained provider work authorized before terminal capability."
    prompt, contract, lease, maximum = adapter.preview_request(
        "conjecturer",
        pack,
        ConjectureTurnV6,
        aliases=aliases,
        model_profile=base_profile,
        wire_contract=contract,
    )
    transaction = InquiryTransactionService(
        service.harness,
        manifest,
        adapter.meter,
    )
    fence = service.harness._next_seq - 1
    preparation = transaction.prepare(
        task_kind=WorkflowTaskKind.CONJECTURE,
        attempt_index=0,
        route_lease=RouteLeaseRefV1(
            role="conjecturer",
            seat=0,
            endpoint_id=lease.route.endpoint_id,
            route_sha256=route_fingerprint(lease.route),
        ),
        contract_id=contract.contract_id,
        trigger_ref="issued-before-route-capability-terminal",
        formal_fence_seq=fence,
        scratch_fence_seq=fence,
        task_payload_value={"task": "retained dispatch"},
    )
    authorized = transaction.issue(
        preparation,
        plans=(),
        prompt=prompt,
        max_tokens=maximum,
    )
    assert authorized.reservation.is_open

    with pytest.raises(SchemaExhaustedError):
        ScratchAuthoringService(
            service,
            adapter,
            renderer=renderer,
            run_manifest=manifest,
        ).author_block(rendered, task="Exhaust the smallest compact contract")
    assert len(service.harness.workflow_state.insufficient_capability_by_route_seat) == 1
    before_seq = service.harness._next_seq
    before_calls = adapter.meter.calls
    before_reserved = adapter.meter.reserved

    with pytest.raises(
        WorkflowAuthorizationError,
        match="V6_ROUTE_SEAT_INSUFFICIENT_CAPABILITY",
    ):
        adapter.call(
            "conjecturer",
            pack,
            ConjectureTurnV6,
            aliases=aliases,
            model_profile=base_profile,
            wire_contract=contract,
            dispatch_authorization=authorized,
        )

    assert service.harness._next_seq == before_seq
    assert adapter.meter.calls == before_calls == 3
    assert adapter.meter.reserved == before_reserved
    with pytest.raises(
        RunManifestError,
        match="V6_ROUTE_SEAT_INSUFFICIENT_CAPABILITY",
    ):
        transaction.record_provider_attempt(
            authorized,
            call=object(),
            outcome="provider_result",
            usage_status="exact",
        )
    assert service.harness._next_seq == before_seq
    authorized.release()
    assert adapter.meter.reserved == 0


def test_forged_capability_identity_fails_canonical_validation(tmp_path):
    root = tmp_path / "insufficient-forgery"
    _manifest, service, _adapter_value, _rendered = _exhaust_minimal_block(root)
    state = service.harness.workflow_state
    outcome = next(iter(state.insufficient_capability_by_route_seat.values()))
    item = state.transaction_work[outcome.work_id]
    provider = item.provider_attempts[outcome.attempt_index]
    admission = item.admissions[outcome.attempt_index]
    forged = outcome.model_copy(
        update={"qualification_evidence_sha256": "0" * 64}
    )

    with pytest.raises(ValueError, match="differs from durable authority"):
        state._validate_insufficient_capability(
            forged,
            item,
            provider,
            admission,
        )
