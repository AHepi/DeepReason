"""Runtime connection for durable v6 route-seat compact recovery."""

from __future__ import annotations

import pytest

from deepreason.harness import Harness
from deepreason.invariants import verify_root
from deepreason.llm.adapter import LLMAdapter
from deepreason.llm.budget import TokenMeter
from deepreason.llm.endpoints import MockEndpoint
from deepreason.llm.firewall import leases_from_manifest, route_fingerprint
from deepreason.llm.wire import (
    AliasTable,
    ConjectureTurnV6,
    ConjecturerTurnWireContractV6,
)
from deepreason.ontology import LLMCall
from deepreason.ontology.event import LLMAttempt
from deepreason.run_manifest import (
    config_from_run_manifest,
    resolve_route_seat_base_profile,
)
from deepreason.scheduler.scheduler import Scheduler
from deepreason.workflow.models import RouteLeaseRefV1, WorkflowTaskKind
from deepreason.workflow.transaction_service import InquiryTransactionService
from tests.test_v6_compact_recovery_transition import (
    _bind_classification,
    _exhaust,
    _manifest,
    _persist_manifest,
)


def _adapter(harness, manifest, responses=None):
    if manifest.route_seat_behavioral_capability_plan is not None:
        from deepreason.run_manifest import write_run_manifest

        write_run_manifest(manifest, harness.root / "run-manifest.json")
        _bind_classification(harness, manifest)
    responses = responses or {}
    endpoints = {}
    for role, routes in manifest.roles.items():
        if not routes:
            continue
        built = []
        for seat, route in enumerate(routes):
            built.append(
                MockEndpoint(
                    responses.get((role, seat), []),
                    name=route.base_url,
                    model=route.model_id,
                    max_tokens=route.max_tokens,
                )
            )
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
    adapter.bind_v6_authority(harness, manifest)
    return adapter, endpoints


def _dispatch_conjecture(adapter, harness, manifest, *, trigger: str):
    route = manifest.roles["conjecturer"][0]
    base_profile = resolve_route_seat_base_profile(
        manifest,
        role="conjecturer",
        seat=0,
        endpoint_id=route.endpoint_id,
    )
    aliases = AliasTable()
    contract = ConjecturerTurnWireContractV6(
        reasoning=False,
        aliases=aliases,
        scratch_authoring_policy=manifest.control_plane_policy.scratch_authoring,
    )
    prompt, contract, lease, maximum = adapter.preview_request(
        "conjecturer",
        "A later independent conjecture task.",
        ConjectureTurnV6,
        endpoint_index=0,
        aliases=aliases,
        model_profile=base_profile,
        wire_contract=contract,
    )
    service = InquiryTransactionService(harness, manifest, adapter.meter)
    preparation = service.prepare(
        task_kind=WorkflowTaskKind.CONJECTURE,
        attempt_index=0,
        route_lease=RouteLeaseRefV1(
            role="conjecturer",
            seat=0,
            endpoint_id=lease.route.endpoint_id,
            route_sha256=route_fingerprint(lease.route),
        ),
        contract_id=contract.contract_id,
        trigger_ref=trigger,
        formal_fence_seq=max(0, harness._next_seq - 1),
        scratch_fence_seq=max(0, harness._next_seq - 1),
        task_payload_value={"task": trigger},
    )
    authorized = service.issue(
        preparation,
        plans=(),
        prompt=prompt,
        max_tokens=maximum,
    )
    output, call = adapter.call(
        "conjecturer",
        "A later independent conjecture task.",
        ConjectureTurnV6,
        endpoint_index=0,
        aliases=aliases,
        model_profile=base_profile,
        wire_contract=contract,
        dispatch_authorization=authorized,
    )
    provider = service.record_provider_attempt(
        authorized,
        call=call,
        outcome="provider_result",
        usage_status="exact",
    )
    admitted_ref = harness.blobs.put(b"later compact result")
    admission = service.record_semantic_admission(
        provider,
        outcome="admitted",
        admitted_refs=(admitted_ref,),
    )
    service.terminate(
        work_id=preparation.id,
        attempt_index=0,
        status="completed",
        reason_code="test_completed",
        usage_status="exact",
        prompt_tokens=provider.prompt_tokens,
        completion_tokens=provider.completion_tokens,
        provider_attempt=provider,
        admission=admission,
    )
    return prompt, contract, output, call


@pytest.mark.parametrize("profile", ["standard", "frontier"])
def test_transition_changes_only_later_exact_seat_calls_and_survives_restart(
    tmp_path, profile
):
    manifest = _manifest(profile=profile)
    root = tmp_path / profile
    _persist_manifest(manifest, root)
    harness = Harness(root)
    adapter, endpoints = _adapter(
        harness,
        manifest,
        {
            ("conjecturer", 0): [
                '{"candidates":[{"content":"later idea",'
                '"typicality":0.5}]}'
            ]
        },
    )
    assert adapter.profile_for("conjecturer", 0) == profile
    assert adapter.profile_for("conjecturer", 1) == profile
    assert adapter.profile_for("argumentative_critic", 0) == profile

    service = InquiryTransactionService(harness, manifest, adapter.meter)
    failed = _exhaust(service, trigger="genuine-schema-exhaustion")
    failed_terminal = failed[3]
    assert failed_terminal.status == "schema_exhausted"
    assert adapter.profile_for("conjecturer", 0) == "compact"
    assert adapter.profile_for("conjecturer", 1) == profile
    assert adapter.profile_for("argumentative_critic", 0) == profile

    prompt, contract, _output, call = _dispatch_conjecture(
        adapter,
        harness,
        manifest,
        trigger="later-independent-work",
    )
    assert contract.contract_id == "conjecturer.turn.v6"
    assert harness.blobs.get(call.prompt_ref).decode("utf-8") == prompt
    assert {attempt.model_profile for attempt in call.attempt_trace} == {profile}
    assert {attempt.transport_profile for attempt in call.attempt_trace} == {
        "compact"
    }
    assert failed_terminal == harness.workflow_state.transaction_work[
        failed[0].id
    ].terminal
    assert endpoints["conjecturer"][0].last_transport_attempts == 1

    violations = verify_root(root)["violations"]
    assert not [
        finding
        for finding in violations
        if finding["check"] == "attempt-profile-authority"
    ]
    reopened = Harness(root)
    rebuilt, rebuilt_endpoints = _adapter(reopened, manifest)
    assert rebuilt.profile_for("conjecturer", 0) == "compact"
    assert rebuilt.profile_for("conjecturer", 1) == profile
    assert rebuilt_endpoints["conjecturer"][0].last_transport_attempts == 0


def test_heterogeneous_transition_preserves_exact_base_and_seat_isolation(
    tmp_path,
):
    manifest = _manifest(
        profile="standard",
        route_profiles={
            ("conjecturer", 0): "frontier",
            ("conjecturer", 1): "compact",
            ("argumentative_critic", 0): "standard",
        },
    )
    root = tmp_path / "heterogeneous-runtime"
    _persist_manifest(manifest, root)
    harness = Harness(root)
    adapter, _endpoints = _adapter(
        harness,
        manifest,
        {
            ("conjecturer", 0): [
                '{"candidates":[{"content":"later idea",'
                '"typicality":0.5}]}'
            ]
        },
    )
    assert adapter.profile_for("conjecturer", 0) == "frontier"
    assert adapter.profile_for("conjecturer", 1) == "compact"
    assert adapter.profile_for("argumentative_critic", 0) == "standard"

    _exhaust(
        InquiryTransactionService(harness, manifest, adapter.meter),
        seat=0,
        trigger="frontier-seat-exhaustion",
    )
    assert adapter.profile_for("conjecturer", 0) == "compact"
    assert adapter.profile_for("conjecturer", 1) == "compact"
    assert adapter.base_profile_for("conjecturer", 0) == "frontier"
    assert adapter.base_profile_for("conjecturer", 1) == "compact"
    assert adapter.profile_for("argumentative_critic", 0) == "standard"

    _prompt, _contract, _output, call = _dispatch_conjecture(
        adapter,
        harness,
        manifest,
        trigger="later-frontier-seat-work",
    )
    assert {attempt.model_profile for attempt in call.attempt_trace} == {
        "frontier"
    }
    assert {attempt.transport_profile for attempt in call.attempt_trace} == {
        "compact"
    }
    reopened = Harness(root)
    rebuilt, _ = _adapter(reopened, manifest)
    assert rebuilt.base_profile_for("conjecturer", 0) == "frontier"
    assert rebuilt.profile_for("conjecturer", 0) == "compact"
    assert rebuilt.base_profile_for("conjecturer", 1) == "compact"
    assert rebuilt.profile_for("argumentative_critic", 0) == "standard"


def test_base_compact_and_policy_absence_never_infer_transition(tmp_path):
    compact = _manifest(profile="compact")
    compact_harness = Harness(tmp_path / "base-compact")
    compact_adapter, _endpoints = _adapter(compact_harness, compact)
    assert compact_adapter.profile_for("conjecturer", 0) == "compact"

    historical = _manifest(historical_without_policy=True)
    historical_harness = Harness(tmp_path / "historical")
    with pytest.raises(RuntimeError, match="behavioral authority"):
        _adapter(historical_harness, historical)
    assert historical_harness.workflow_state.compact_recovery_by_route_seat == {}


def test_scheduler_binds_live_canonical_route_seat_authority(tmp_path):
    manifest = _manifest()
    harness = Harness(tmp_path / "scheduler")
    adapter, _endpoints = _adapter(harness, manifest)
    Scheduler(
        harness,
        adapter,
        config_from_run_manifest(manifest),
        workload_profile="text",
        run_manifest=manifest,
    )
    _exhaust(
        InquiryTransactionService(harness, manifest, adapter.meter),
        trigger="scheduler-visible-transition",
    )
    assert adapter.profile_for("conjecturer", 0) == "compact"
    assert adapter.profile_for("conjecturer", 1) == "standard"


def test_transition_between_preview_and_dispatch_fails_prompt_authority(tmp_path):
    manifest = _manifest()
    harness = Harness(tmp_path / "preview-dispatch-drift")
    adapter, endpoints = _adapter(
        harness,
        manifest,
        {
            ("conjecturer", 0): [
                '{"candidates":[{"content":"must not dispatch",'
                '"typicality":0.5}]}'
            ]
        },
    )
    aliases = AliasTable()
    contract = ConjecturerTurnWireContractV6(
        reasoning=False,
        aliases=aliases,
        scratch_authoring_policy=manifest.control_plane_policy.scratch_authoring,
    )
    prompt, contract, lease, maximum = adapter.preview_request(
        "conjecturer",
        "Prepared before another work item exhausts.",
        ConjectureTurnV6,
        aliases=aliases,
        wire_contract=contract,
        model_profile=manifest.model_profile,
    )
    service = InquiryTransactionService(harness, manifest, adapter.meter)
    preparation = service.prepare(
        task_kind=WorkflowTaskKind.CONJECTURE,
        attempt_index=0,
        route_lease=RouteLeaseRefV1(
            role="conjecturer",
            seat=0,
            endpoint_id=lease.route.endpoint_id,
            route_sha256=route_fingerprint(lease.route),
        ),
        contract_id=contract.contract_id,
        trigger_ref="pre-transition-preview",
        formal_fence_seq=max(0, harness._next_seq - 1),
        scratch_fence_seq=max(0, harness._next_seq - 1),
        task_payload_value={"task": "pre-transition-preview"},
    )
    authorized = service.issue(
        preparation,
        plans=(),
        prompt=prompt,
        max_tokens=maximum,
    )
    _exhaust(service, trigger="intervening-schema-exhaustion")

    with pytest.raises(ValueError, match="dispatch differs from its authorization"):
        adapter.call(
            "conjecturer",
            "Prepared before another work item exhausts.",
            ConjectureTurnV6,
            aliases=aliases,
            wire_contract=contract,
            model_profile=manifest.model_profile,
            dispatch_authorization=authorized,
        )

    authorized.release()
    service.terminate(
        work_id=preparation.id,
        attempt_index=0,
        status="abandoned",
        reason_code="prompt_authority_changed",
        usage_status="exact",
        prompt_tokens=0,
        completion_tokens=0,
    )
    assert endpoints["conjecturer"][0].last_transport_attempts == 0
    assert adapter.meter.snapshot()["reserved"] == 0


def test_transactional_bridge_uses_the_same_route_seat_authority(tmp_path):
    from tests.test_v6_bridge_transactions import (
        _ledger_contract,
        _manifest as bridge_manifest,
        _qualified_transactional_adapter,
    )
    from deepreason.llm.repair import SchemaRepairError

    manifest = bridge_manifest()
    root = tmp_path / "bridge"
    harness = Harness(root)
    route = manifest.roles["summarizer"][0]
    endpoint = MockEndpoint(
        ["{not-json", '{"value":"ok"}'],
        name=route.base_url,
        model=route.model_id,
        max_tokens=route.max_tokens,
    )
    base = LLMAdapter(
        {"summarizer": endpoint},
        harness.blobs,
        retry_max=0,
        meter=TokenMeter(100_000),
        model_profile=manifest.model_profile,
        leases=leases_from_manifest(manifest),
    )
    adapter = _qualified_transactional_adapter(base, harness, manifest)
    commitment = harness.workflow_state.current_terminal_commitment
    assert commitment is not None
    assert adapter.source_terminal_commitment_ref == commitment.id
    assert adapter.profile_for("summarizer", 0) == "standard"

    with pytest.raises(SchemaRepairError):
        adapter.call(
            "summarizer",
            "SRC_1: schema-exhausted bridge source",
            _ledger_contract().canonical_model,
            template_role="bridge_ledger",
            wire_contract=_ledger_contract(),
        )

    assert adapter.profile_for("summarizer", 0) == "compact"

    _output, call = adapter.call(
        "summarizer",
        "SRC_1: bounded source",
        _ledger_contract().canonical_model,
        template_role="bridge_ledger",
        wire_contract=_ledger_contract(),
    )
    assert {attempt.model_profile for attempt in call.attempt_trace} == {
        "standard"
    }
    assert {attempt.transport_profile for attempt in call.attempt_trace} == {
        "compact"
    }
    assert {attempt.contract_id for attempt in call.attempt_trace} == {
        "bridge.ledger.v3"
    }
    assert endpoint.last_transport_attempts == 1


def _record_forged_compact_call(
    harness,
    manifest,
    *,
    seat: int,
    trigger: str,
    route_sha256: str | None = None,
):
    route = manifest.roles["conjecturer"][seat]
    lease = RouteLeaseRefV1(
        role="conjecturer",
        seat=seat,
        endpoint_id=route.endpoint_id,
        route_sha256=route_fingerprint(route),
    )
    service = InquiryTransactionService(harness, manifest, TokenMeter(100_000))
    preparation = service.prepare(
        task_kind=WorkflowTaskKind.CONJECTURE,
        attempt_index=0,
        route_lease=lease,
        contract_id="conjecturer.turn.v6",
        trigger_ref=trigger,
        formal_fence_seq=max(0, harness._next_seq - 1),
        scratch_fence_seq=max(0, harness._next_seq - 1),
        task_payload_value={"task": trigger},
    )
    prompt = "forged compact transport"
    authorized = service.issue(
        preparation, plans=(), prompt=prompt, max_tokens=8
    )
    prompt_ref = harness.blobs.put(prompt.encode())
    raw_ref = harness.blobs.put(b'{"invalid":true}')
    diagnostic_ref = harness.blobs.put(b"invalid output")
    call = LLMCall(
        role="conjecturer",
        model=route.model_id,
        endpoint=route.base_url,
        prompt_ref=prompt_ref,
        raw_ref=raw_ref,
        tokens=2,
        attempts=1,
        prompt_tokens=1,
        completion_tokens=1,
        work_order_id=preparation.id,
        dispatch_authorization_ref=authorized.bundle.id,
        attempt_trace=[
            LLMAttempt(
                prompt_ref=prompt_ref,
                raw_ref=raw_ref,
                diagnostic_ref=diagnostic_ref,
                contract_id=preparation.contract_id,
                endpoint_id=route.endpoint_id,
                route_sha256=route_sha256 or route_fingerprint(route),
                seat=seat,
                model_profile=manifest.model_profile,
                transport_profile="compact",
                tokens=2,
                valid=False,
            )
        ],
    )
    authorized.reservation.settle(
        {"prompt_tokens": 1, "completion_tokens": 1}
    )
    provider = service.record_provider_attempt(
        authorized,
        call=call,
        outcome="provider_result",
        usage_status="exact",
    )
    admission = service.record_semantic_admission(provider, outcome="rejected")
    service.terminate(
        work_id=preparation.id,
        attempt_index=0,
        status="rejected",
        reason_code="forged_compact",
        usage_status="exact",
        prompt_tokens=1,
        completion_tokens=1,
        provider_attempt=provider,
        admission=admission,
    )


@pytest.mark.parametrize("mode", ["before-transition", "wrong-seat", "wrong-route"])
def test_invariants_reject_nonchronological_or_foreign_compact_use(tmp_path, mode):
    manifest = _manifest()
    root = tmp_path / mode
    _persist_manifest(manifest, root)
    harness = Harness(root)
    if mode == "before-transition":
        _record_forged_compact_call(
            harness, manifest, seat=0, trigger=mode
        )
        _exhaust(
            InquiryTransactionService(harness, manifest, TokenMeter(100_000)),
            trigger="later-transition",
        )
    elif mode == "wrong-seat":
        _exhaust(
            InquiryTransactionService(harness, manifest, TokenMeter(100_000)),
            trigger="seat-zero-transition",
        )
        _record_forged_compact_call(
            harness, manifest, seat=1, trigger=mode
        )
    else:
        _exhaust(
            InquiryTransactionService(harness, manifest, TokenMeter(100_000)),
            trigger="valid-transition",
        )
        _record_forged_compact_call(
            harness,
            manifest,
            seat=1,
            trigger=mode,
            route_sha256="0" * 64,
        )
    violations = verify_root(root)["violations"]
    assert any(
        finding["check"] == "attempt-profile-authority"
        for finding in violations
    )
