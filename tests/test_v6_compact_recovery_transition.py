"""Focused durable-authority tests for v6 compact-recovery transitions."""

from __future__ import annotations

from datetime import datetime, timezone

import pytest

from deepreason.bridge.retry import WorkflowRetryPolicyV1
from deepreason.cli.doctor import run_production_contract_doctor
from deepreason.config import Config
from deepreason.control_events import ControlEventPayloadV3
from deepreason.harness import Harness, WellFormednessError
from deepreason.llm.budget import TokenMeter
from deepreason.llm.firewall import route_fingerprint
from deepreason.ontology import Event, LLMCall, Rule
from deepreason.ontology.event import LLMAttempt
from deepreason.run_manifest import (
    ConjectureContextPolicyV1,
    ContractVersionPolicyV3,
    ControlPlanePolicyV3,
    RunManifest,
    SchoolExecutionPolicyV1,
    ScratchAuthoringPolicyV1,
    compile_run_manifest,
    resolve_route_seat_base_profile,
    write_run_manifest,
)
from deepreason.workflow.models import RouteLeaseRefV1, WorkflowTaskKind
from deepreason.workflow.transaction import (
    CompactRecoveryTransitionV1,
    WorkBudgetDenied,
    WorkLifecycleTransitionV1,
    WorkTerminalV1,
    WorkTransitionKind,
)
from deepreason.workflow.transaction_service import InquiryTransactionService
from tests.test_cli_production_doctor_v6 import _admitted_case


STAMP = "2026-07-20T00:00:00Z"


def _bind_classification(harness: Harness, manifest: RunManifest) -> None:
    report = run_production_contract_doctor(
        manifest,
        case_executor=lambda _manifest, _pair, index: _admitted_case(index),
    )
    harness.bind_model_classification(manifest, report)


def _persist_manifest(manifest: RunManifest, root) -> None:
    write_run_manifest(manifest, root / "run-manifest.json")
    if manifest.route_seat_behavioral_capability_plan is not None:
        _bind_classification(Harness(root), manifest)


def _route(
    endpoint_id: str,
    model: str,
    *,
    model_profile: str | None = None,
) -> dict:
    route = {
        "endpoint_id": endpoint_id,
        "endpoint": f"mock://{endpoint_id}",
        "model": model,
        "provider": "mock",
        "family": model,
        "max_tokens": 64,
        "context_window_tokens": 262_144,
    }
    if model_profile is not None:
        route["model_profile"] = model_profile
    return route


def _manifest(
    *,
    profile: str = "standard",
    historical_without_policy: bool = False,
    route_profiles: dict[tuple[str, int], str] | None = None,
) -> RunManifest:
    route_profiles = route_profiles or {}
    config = Config(
        N_SCHOOLS=0,
        roles={
            "conjecturer": [
                _route(
                    "conjecturer-a",
                    "model-a",
                    model_profile=route_profiles.get(("conjecturer", 0)),
                ),
                _route(
                    "conjecturer-b",
                    "model-b",
                    model_profile=route_profiles.get(("conjecturer", 1)),
                ),
            ],
            "argumentative_critic": [
                _route(
                    "critic-a",
                    "critic-model",
                    model_profile=route_profiles.get(
                        ("argumentative_critic", 0)
                    ),
                ),
            ],
        },
    )
    control = ControlPlanePolicyV3(
        school_execution=SchoolExecutionPolicyV1(
            mode="conditioning_only",
            bindings=(),
            allow_shared=True,
            require_distinct_models=False,
            require_distinct_families=False,
        ),
        conjecture_context=ConjectureContextPolicyV1(
            mode="disabled",
            initial_max_blocks=0,
            initial_max_guides=0,
            max_context_expansion_requests=0,
            max_extra_blocks=0,
            permitted_retrieval_channels=(),
            coverage_slot_mandatory=False,
            exploration_slot_mandatory=False,
        ),
        workflow_retry=WorkflowRetryPolicyV1(),
        contract_versions=ContractVersionPolicyV3(),
        scratch_authoring=ScratchAuthoringPolicyV1(),
    )
    manifest = compile_run_manifest(
        config,
        schema_version=6,
        model_profile=profile,
        workload_profile="text",
        rubric_policy="forbid",
        compiled_at=STAMP,
        control_plane_policy=control,
        run_input_digest="f" * 64,
    )
    if not historical_without_policy:
        return manifest
    payload = manifest.model_dump(mode="json", by_alias=True)
    payload.pop("compact_recovery_policy")
    payload.pop("route_seat_behavioral_capability_plan")
    return RunManifest.model_validate(payload)


def _lease(manifest: RunManifest, *, role: str = "conjecturer", seat: int = 0):
    route = manifest.roles[role][seat]
    return RouteLeaseRefV1(
        role=role,
        seat=seat,
        endpoint_id=route.endpoint_id,
        route_sha256=route_fingerprint(route),
    )


def _durable_result(
    service: InquiryTransactionService,
    *,
    role: str = "conjecturer",
    seat: int = 0,
    trigger: str,
    raw: bytes = b'{"invalid":"switch to compact"}',
):
    manifest = service.manifest
    lease = _lease(manifest, role=role, seat=seat)
    route = manifest.roles[role][seat]
    preparation = service.prepare(
        task_kind=(
            WorkflowTaskKind.CONJECTURE
            if role == "conjecturer"
            else WorkflowTaskKind.CRITICISM
        ),
        attempt_index=0,
        route_lease=lease,
        contract_id={
            "conjecturer": "conjecturer.turn.v6",
            "argumentative_critic": "batch-critic.v2",
            "summarizer": "bridge.ledger.v3",
        }[role],
        trigger_ref=trigger,
        formal_fence_seq=max(0, service.harness._next_seq - 1),
        scratch_fence_seq=max(0, service.harness._next_seq - 1),
        task_payload_value={"task": trigger},
    )
    prompt = f"authorized prompt for {trigger}"
    authorized = service.issue(
        preparation,
        plans=(),
        prompt=prompt,
        max_tokens=8,
    )
    prompt_ref = service.harness.blobs.put(prompt.encode())
    raw_ref = service.harness.blobs.put(raw)
    base_profile = resolve_route_seat_base_profile(
        manifest,
        role=role,
        seat=seat,
        endpoint_id=route.endpoint_id,
    )
    call = LLMCall(
        role=role,
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
                attempt=0,
                contract_id=preparation.contract_id,
                endpoint_id=lease.endpoint_id,
                route_sha256=lease.route_sha256,
                seat=lease.seat,
                model_profile=base_profile,
                transport_profile=base_profile,
                tokens=2,
                valid=False,
            )
        ],
    )
    authorized.reservation.settle(
        {"prompt_tokens": 1, "completion_tokens": 1}
    )
    attempt = service.record_provider_attempt(
        authorized,
        call=call,
        outcome="provider_result",
        usage_status="exact",
    )
    return preparation, attempt


def _exhaust(
    service: InquiryTransactionService,
    *,
    role: str = "conjecturer",
    seat: int = 0,
    trigger: str,
):
    preparation, attempt = _durable_result(
        service, role=role, seat=seat, trigger=trigger
    )
    admission = service.record_semantic_admission(
        attempt,
        outcome="schema_exhausted",
        diagnostic_refs=(service.harness.blobs.put(b"schema exhausted"),),
    )
    terminal = service.terminate(
        work_id=preparation.id,
        attempt_index=0,
        status="schema_exhausted",
        reason_code="schema_exhausted",
        usage_status="exact",
        prompt_tokens=1,
        completion_tokens=1,
        provider_attempt=attempt,
        admission=admission,
    )
    return preparation, attempt, admission, terminal


@pytest.mark.parametrize("profile", ["standard", "frontier"])
def test_schema_exhaustion_atomically_creates_route_seat_transition(
    tmp_path, profile
):
    manifest = _manifest(profile=profile)
    root = tmp_path / profile
    _persist_manifest(manifest, root)
    harness = Harness(root)
    service = InquiryTransactionService(harness, manifest, TokenMeter(10_000))

    preparation, _attempt, admission, terminal = _exhaust(
        service, trigger=f"{profile}-exhausted"
    )

    key = ("conjecturer", 0, "conjecturer-a", _lease(manifest).route_sha256)
    compact = harness.workflow_state.compact_recovery_by_route_seat[key]
    assert compact.manifest_digest == manifest.sha256
    assert compact.work_id == preparation.id
    assert compact.attempt_index == 0
    assert compact.source_profile == profile
    assert compact.target_profile == "compact"
    assert compact.trigger == "schema_exhausted"
    assert compact.scope == "route_seat"
    assert compact.sticky is True
    assert compact.applies_to == "all_subsequent_model_calls"
    assert compact.retry_failed_work is False
    assert compact.semantic_admission_ref == admission.id
    assert terminal.compact_recovery_transition_ref == compact.id
    event = list(harness.log.read())[-1]
    assert [harness.objects.get(ref)[0] for ref in event.outputs] == [
        "workflow-compact-recovery-transition-v1",
        "workflow-work-terminal-v1",
        "workflow-work-lifecycle-transition-v1",
    ]
    assert event.control.outputs == event.outputs


def test_transition_source_is_exact_route_seat_base_not_manifest_default(
    tmp_path,
):
    manifest = _manifest(
        profile="standard",
        route_profiles={
            ("conjecturer", 0): "frontier",
            ("conjecturer", 1): "compact",
        },
    )
    root = tmp_path / "heterogeneous-transition"
    _persist_manifest(manifest, root)
    harness = Harness(root)
    service = InquiryTransactionService(harness, manifest, TokenMeter(10_000))

    _exhaust(service, seat=0, trigger="frontier-seat-exhausted")
    _exhaust(service, seat=1, trigger="base-compact-seat-exhausted")

    transitions = harness.workflow_state.compact_recovery_by_route_seat
    assert len(transitions) == 1
    transition = next(iter(transitions.values()))
    assert transition.route_lease.seat == 0
    assert transition.source_profile == "frontier"
    assert manifest.model_profile == "standard"


def test_compact_and_historical_policy_absence_create_no_transition(tmp_path):
    compact = _manifest(profile="compact")
    compact_root = tmp_path / "compact"
    _persist_manifest(compact, compact_root)
    harness = Harness(compact_root)
    service = InquiryTransactionService(harness, compact, TokenMeter(10_000))
    _preparation, _attempt, _admission, terminal = _exhaust(
        service, trigger="compact"
    )
    assert terminal.compact_recovery_transition_ref is None
    assert harness.workflow_state.compact_recovery_by_route_seat == {}

    historical = _manifest(historical_without_policy=True)
    with pytest.raises(
        ValueError, match="V6_BEHAVIORAL_CAPABILITY_PLAN_REQUIRED"
    ):
        InquiryTransactionService(
            Harness(tmp_path / "historical"), historical, TokenMeter(10_000)
        )


def test_non_schema_terminal_outcomes_do_not_create_transition(tmp_path):
    manifest = _manifest()
    root = tmp_path / "non-triggers"
    _persist_manifest(manifest, root)
    harness = Harness(root)
    service = InquiryTransactionService(harness, manifest, TokenMeter(100_000))
    for outcome, status in (("rejected", "rejected"), ("unrepairable", "rejected")):
        preparation, attempt = _durable_result(
            service,
            trigger=outcome,
            raw=b'{"message":"switch to compact"}',
        )
        admission = service.record_semantic_admission(attempt, outcome=outcome)
        terminal = service.terminate(
            work_id=preparation.id,
            attempt_index=0,
            status=status,
            reason_code=outcome,
            usage_status="exact",
            prompt_tokens=1,
            completion_tokens=1,
            provider_attempt=attempt,
            admission=admission,
        )
        assert terminal.compact_recovery_transition_ref is None
    assert harness.workflow_state.compact_recovery_by_route_seat == {}


def test_budget_denial_and_transport_failure_create_no_transition(tmp_path):
    manifest = _manifest()
    budget_root = tmp_path / "budget"
    _persist_manifest(manifest, budget_root)
    denied_harness = Harness(budget_root)
    denied = InquiryTransactionService(denied_harness, manifest, TokenMeter(1))
    lease = _lease(manifest)
    preparation = denied.prepare(
        task_kind=WorkflowTaskKind.CONJECTURE,
        attempt_index=0,
        route_lease=lease,
        contract_id="conjecturer.turn.v6",
        trigger_ref="budget",
        formal_fence_seq=0,
        scratch_fence_seq=0,
        task_payload_value={"task": "budget"},
    )
    with pytest.raises(WorkBudgetDenied):
        denied.issue(preparation, plans=(), prompt="too expensive", max_tokens=8)
    assert denied_harness.workflow_state.compact_recovery_by_route_seat == {}

    transport_root = tmp_path / "transport"
    _persist_manifest(manifest, transport_root)
    harness = Harness(transport_root)
    service = InquiryTransactionService(harness, manifest, TokenMeter(10_000))
    preparation = service.prepare(
        task_kind=WorkflowTaskKind.CONJECTURE,
        attempt_index=0,
        route_lease=lease,
        contract_id="conjecturer.turn.v6",
        trigger_ref="transport",
        formal_fence_seq=0,
        scratch_fence_seq=0,
        task_payload_value={"task": "transport"},
    )
    authorized = service.issue(
        preparation, plans=(), prompt="transport prompt", max_tokens=8
    )
    prompt_ref = harness.blobs.put(b"transport prompt")
    diagnostic_ref = harness.blobs.put(b"offline transport failure")
    call = LLMCall(
        role="conjecturer",
        model=manifest.roles["conjecturer"][0].model_id,
        endpoint=manifest.roles["conjecturer"][0].base_url,
        prompt_ref=prompt_ref,
        raw_ref="",
        tokens=0,
        attempts=1,
        work_order_id=preparation.id,
        dispatch_authorization_ref=authorized.bundle.id,
        attempt_trace=[
            LLMAttempt(
                prompt_ref=prompt_ref,
                diagnostic_ref=diagnostic_ref,
                contract_id=preparation.contract_id,
                endpoint_id=lease.endpoint_id,
                route_sha256=lease.route_sha256,
                seat=lease.seat,
                model_profile="standard",
                transport_profile="standard",
                usage_unknown=True,
                valid=False,
            )
        ],
    )
    authorized.release()
    attempt = service.record_provider_attempt(
        authorized,
        call=call,
        outcome="transport_failure",
        usage_status="unknown",
        diagnostic_ref=diagnostic_ref,
    )
    terminal = service.terminate(
        work_id=preparation.id,
        attempt_index=0,
        status="transport_failed",
        reason_code="transport_failed",
        usage_status="unknown",
        provider_attempt=attempt,
    )
    assert terminal.compact_recovery_transition_ref is None
    assert harness.workflow_state.compact_recovery_by_route_seat == {}


def test_sticky_transition_is_exact_once_and_scoped_by_role_and_seat(tmp_path):
    manifest = _manifest()
    root = tmp_path / "scope"
    _persist_manifest(manifest, root)
    harness = Harness(root)
    service = InquiryTransactionService(harness, manifest, TokenMeter(100_000))
    first = _exhaust(service, trigger="first")[3]
    second = _exhaust(service, trigger="second")[3]
    other_seat = _exhaust(service, seat=1, trigger="other-seat")[3]
    other_role = _exhaust(
        service, role="argumentative_critic", trigger="other-role"
    )[3]

    assert len(harness.workflow_state.compact_recovery_by_route_seat) == 3
    assert first.compact_recovery_transition_ref == second.compact_recovery_transition_ref
    assert other_seat.compact_recovery_transition_ref != first.compact_recovery_transition_ref
    assert other_role.compact_recovery_transition_ref != first.compact_recovery_transition_ref
    schemas = [
        harness.objects.get(ref)[0]
        for event in harness.log.read()
        for ref in event.outputs
    ]
    assert schemas.count("workflow-compact-recovery-transition-v1") == 3


def test_restart_replays_identical_transition_without_provider_dispatch(tmp_path):
    manifest = _manifest()
    root = tmp_path / "restart"
    _persist_manifest(manifest, root)
    harness = Harness(root)
    service = InquiryTransactionService(harness, manifest, TokenMeter(10_000))
    terminal = _exhaust(service, trigger="restart")[3]
    before = dict(harness.workflow_state.compact_recovery_by_route_seat)
    event_count = len(list(harness.log.read()))

    reopened = Harness(root)
    recovered = InquiryTransactionService(reopened, manifest, TokenMeter(10_000))
    assert recovered.recover_incomplete() == ()

    assert reopened.workflow_state.compact_recovery_by_route_seat == before
    assert len(list(reopened.log.read())) == event_count
    item = next(
        item
        for item in reopened.workflow_state.transaction_work.values()
        if item.terminal and item.terminal.id == terminal.id
    )
    assert item.terminal == terminal


def test_recovery_terminalizes_durable_schema_admission_with_same_transition(
    tmp_path,
):
    manifest = _manifest(profile="frontier")
    root = tmp_path / "recovery-terminal"
    _persist_manifest(manifest, root)
    harness = Harness(root)
    service = InquiryTransactionService(harness, manifest, TokenMeter(10_000))
    preparation, attempt = _durable_result(service, trigger="recover-admission")
    admission = service.record_semantic_admission(
        attempt, outcome="schema_exhausted"
    )
    provider_event_count = sum(
        event.llm is not None for event in harness.log.read()
    )

    reopened = Harness(root)
    recovered = InquiryTransactionService(reopened, manifest, TokenMeter(10_000))
    assert recovered.recover_incomplete() == ()

    item = reopened.workflow_state.transaction_work[preparation.id]
    compact = tuple(reopened.workflow_state.compact_recovery_by_route_seat.values())
    assert len(compact) == 1
    assert compact[0].semantic_admission_ref == admission.id
    assert item.terminal.compact_recovery_transition_ref == compact[0].id
    assert sum(event.llm is not None for event in reopened.log.read()) == (
        provider_event_count
    )
    assert recovered.recover_incomplete() == ()
    assert len(reopened.workflow_state.compact_recovery_by_route_seat) == 1


def test_failed_atomic_append_leaves_transition_and_terminal_unreachable(
    tmp_path, monkeypatch
):
    manifest = _manifest()
    harness = Harness(tmp_path / "atomic")
    _bind_classification(harness, manifest)
    service = InquiryTransactionService(harness, manifest, TokenMeter(10_000))
    preparation, attempt = _durable_result(service, trigger="atomic")
    admission = service.record_semantic_admission(
        attempt, outcome="schema_exhausted"
    )
    original = harness._commit

    def fail_append(*_args, **_kwargs):
        raise OSError("injected append failure")

    monkeypatch.setattr(harness, "_commit", fail_append)
    with pytest.raises(OSError, match="append failure"):
        service.terminate(
            work_id=preparation.id,
            attempt_index=0,
            status="schema_exhausted",
            reason_code="schema_exhausted",
            usage_status="exact",
            prompt_tokens=1,
            completion_tokens=1,
            provider_attempt=attempt,
            admission=admission,
        )
    monkeypatch.setattr(harness, "_commit", original)

    item = harness.workflow_state.transaction_work[preparation.id]
    assert item.terminal is None
    assert harness.workflow_state.compact_recovery_by_route_seat == {}
    assert all(
        harness.objects.get(ref)[0]
        != "workflow-compact-recovery-transition-v1"
        for event in harness.log.read()
        for ref in event.outputs
    )


def _append_forged_terminal(
    harness: Harness,
    compact: CompactRecoveryTransitionV1,
    *,
    admission,
    attempt,
) -> None:
    terminal = WorkTerminalV1.create(
        work_id=compact.work_id,
        attempt_index=compact.attempt_index,
        status="schema_exhausted",
        usage_status="exact",
        prompt_tokens=1,
        completion_tokens=1,
        provider_attempt_ref=attempt.id,
        semantic_admission_ref=admission.id,
        compact_recovery_transition_ref=compact.id,
        reason_code="forged",
    )
    transition = WorkLifecycleTransitionV1.create(
        work_id=compact.work_id,
        attempt_index=compact.attempt_index,
        transition_kind=WorkTransitionKind.WORK_TERMINATED,
        trigger_ref=terminal.id,
    )
    records = (
        ("workflow-compact-recovery-transition-v1", compact),
        ("workflow-work-terminal-v1", terminal),
        ("workflow-work-lifecycle-transition-v1", transition),
    )
    for schema, record in records:
        harness.objects.put(schema, record)
    outputs = [record.id for _schema, record in records]
    payload = ControlEventPayloadV3(
        action="work_transition",
        decision_ref=transition.id,
        inputs=[compact.work_id, terminal.id],
        outputs=outputs,
    )
    harness.log.append(
        Event(
            seq=harness._next_seq,
            ts=datetime.now(timezone.utc).isoformat(),
            rule=Rule.CONTROL,
            inputs=list(payload.inputs),
            outputs=outputs,
            control=payload,
        )
    )


def _append_terminal_without_transition(harness, *, preparation, attempt, admission):
    terminal = WorkTerminalV1.create(
        work_id=preparation.id,
        attempt_index=0,
        status="schema_exhausted",
        usage_status="exact",
        prompt_tokens=1,
        completion_tokens=1,
        provider_attempt_ref=attempt.id,
        semantic_admission_ref=admission.id,
        reason_code="missing-transition",
    )
    transition = WorkLifecycleTransitionV1.create(
        work_id=preparation.id,
        attempt_index=0,
        transition_kind=WorkTransitionKind.WORK_TERMINATED,
        trigger_ref=terminal.id,
    )
    records = (
        ("workflow-work-terminal-v1", terminal),
        ("workflow-work-lifecycle-transition-v1", transition),
    )
    for schema, record in records:
        harness.objects.put(schema, record)
    outputs = [record.id for _schema, record in records]
    payload = ControlEventPayloadV3(
        action="work_transition",
        decision_ref=transition.id,
        inputs=[preparation.id, terminal.id],
        outputs=outputs,
    )
    harness.log.append(
        Event(
            seq=harness._next_seq,
            ts=datetime.now(timezone.utc).isoformat(),
            rule=Rule.CONTROL,
            inputs=list(payload.inputs),
            outputs=outputs,
            control=payload,
        )
    )


@pytest.mark.parametrize("forgery", ["manifest", "route"])
def test_replay_rejects_foreign_manifest_and_route_transitions(tmp_path, forgery):
    manifest = _manifest()
    root = tmp_path / forgery
    _persist_manifest(manifest, root)
    harness = Harness(root)
    service = InquiryTransactionService(harness, manifest, TokenMeter(10_000))
    preparation, attempt = _durable_result(service, trigger=forgery)
    admission = service.record_semantic_admission(
        attempt, outcome="schema_exhausted"
    )
    lease = preparation.route_lease
    if forgery == "route":
        lease = _lease(manifest, seat=1)
    compact = CompactRecoveryTransitionV1.create(
        manifest_digest=("0" * 64 if forgery == "manifest" else manifest.sha256),
        work_id=preparation.id,
        attempt_index=0,
        route_lease=lease,
        source_profile="standard",
        semantic_admission_ref=admission.id,
    )
    _append_forged_terminal(
        harness, compact, admission=admission, attempt=attempt
    )

    with pytest.raises(WellFormednessError, match="compact recovery"):
        Harness(root)


def test_replay_rejects_duplicate_transition_for_one_route_seat(tmp_path):
    manifest = _manifest()
    root = tmp_path / "duplicate"
    _persist_manifest(manifest, root)
    harness = Harness(root)
    service = InquiryTransactionService(harness, manifest, TokenMeter(100_000))
    _exhaust(service, trigger="first")
    preparation, attempt = _durable_result(service, trigger="duplicate")
    admission = service.record_semantic_admission(
        attempt, outcome="schema_exhausted"
    )
    compact = CompactRecoveryTransitionV1.create(
        manifest_digest=manifest.sha256,
        work_id=preparation.id,
        attempt_index=0,
        route_lease=preparation.route_lease,
        source_profile="standard",
        semantic_admission_ref=admission.id,
    )
    _append_forged_terminal(
        harness, compact, admission=admission, attempt=attempt
    )

    with pytest.raises(WellFormednessError, match="duplicate compact recovery"):
        Harness(root)


def test_replay_rejects_missing_terminal_transition_reference(tmp_path):
    manifest = _manifest()
    root = tmp_path / "missing"
    _persist_manifest(manifest, root)
    harness = Harness(root)
    service = InquiryTransactionService(harness, manifest, TokenMeter(10_000))
    preparation, attempt = _durable_result(service, trigger="missing")
    admission = service.record_semantic_admission(
        attempt, outcome="schema_exhausted"
    )
    _append_terminal_without_transition(
        harness,
        preparation=preparation,
        attempt=attempt,
        admission=admission,
    )

    with pytest.raises(WellFormednessError, match="lacks compact recovery"):
        Harness(root)


def test_replay_rejects_transition_under_manifest_without_policy(tmp_path):
    manifest = _manifest(historical_without_policy=True)
    root = tmp_path / "no-policy"
    write_run_manifest(manifest, root / "run-manifest.json")
    harness = Harness(root)
    with pytest.raises(
        ValueError, match="V6_BEHAVIORAL_CAPABILITY_PLAN_REQUIRED"
    ):
        InquiryTransactionService(harness, manifest, TokenMeter(10_000))
    assert harness.workflow_state.compact_recovery_by_route_seat == {}
