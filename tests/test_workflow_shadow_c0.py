"""C0 workflow observer is diagnostic only; legacy actuation stays authoritative."""

from __future__ import annotations

import copy
import hashlib
import json
import shutil
from dataclasses import dataclass
from pathlib import Path

import pytest

from deepreason.bridge.retry import WorkflowRetryPolicyV1
from deepreason.config import Config
from deepreason.harness import Harness
from deepreason.invariants import verify_root
from deepreason.llm.adapter import LLMAdapter, WorkflowAuthorizationError
from deepreason.llm.budget import TokenMeter
from deepreason.llm.endpoints import MockEndpoint
from deepreason.llm.firewall import leases_from_manifest, route_fingerprint
from deepreason.ontology import Problem, ProblemProvenance
from deepreason.ontology import Rule
from deepreason.run_manifest import (
    ConjectureContextPolicyV1,
    ContractVersionPolicyV1,
    ControlPlanePolicyV1,
    RunManifest,
    SchoolExecutionPolicyV1,
    bind_run_manifest,
    compile_run_manifest,
)
from deepreason.scheduler.scheduler import Scheduler
from deepreason.workflow.models import (
    CapabilityGrantV1,
    RouteLeaseRefV1,
    TransitionDecisionV1,
    TransitionKind,
    TriggerKind,
    WorkOrderEnvelopeV1,
)
from deepreason.workflow.profiles import (
    compile_workflow_profile,
    route_lease_reference,
)
from deepreason.workflow.reducer import plan_conjecture_work
from deepreason.workflow.shadow import (
    ConjectureShadowObserver,
    ShadowMismatchCode,
    ShadowTerminationKind,
)
from deepreason.workflow.state import WorkflowProcessStateV1, state_after_transition


STAMP = "2026-07-16T00:00:00Z"


def _config(
    *,
    vs_k: int = 1,
    retry_max: int = 0,
    schools: int = 0,
) -> Config:
    return Config(
        N_SCHOOLS=schools,
        VS_K=vs_k,
        FLOOR=0,
        SPEC_INJECTION=False,
        CONTROLLER=False,
        NEAR_DUP_EPS=None,
        RETRY_MAX=retry_max,
        RESEARCH_BACKEND=None,
        model_profile="standard",
        roles={
            "conjecturer": {
                "endpoint_id": "workflow-c0-conjecturer",
                "endpoint": "mock://workflow-c0-conjecturer",
                "model": "workflow-c0-model",
                "provider": "mock",
                "family": "workflow-c0-family",
                "max_tokens": 256,
            }
        },
    )


def _disabled_context() -> ConjectureContextPolicyV1:
    return ConjectureContextPolicyV1(
        mode="disabled",
        initial_max_blocks=0,
        initial_max_guides=0,
        max_context_expansion_requests=0,
        max_extra_blocks=0,
        permitted_retrieval_channels=(),
        coverage_slot_mandatory=False,
        exploration_slot_mandatory=False,
    )


def _manifest(config: Config, mode: str) -> RunManifest:
    controlled = mode in {"shadow", "active_conjecture"}
    active = mode == "active_conjecture"
    control = ControlPlanePolicyV1(
        controller_version=(
            "workflow.controller.v1" if controlled else "legacy.scheduler.v1"
        ),
        mode=mode,
        workflow_profile=(
            "conjecture.active.v1"
            if active
            else "conjecture.shadow.v1"
            if controlled
            else "legacy.scheduler.v1"
        ),
        school_execution=SchoolExecutionPolicyV1(
            mode="conditioning_only",
            bindings=(),
            allow_shared=True,
            require_distinct_models=False,
            require_distinct_families=False,
        ),
        conjecture_context=_disabled_context(),
        workflow_retry=WorkflowRetryPolicyV1(),
        contract_versions=ContractVersionPolicyV1(
            bridge_ledger_wire_contract=(
                "bridge.ledger.v2" if active else "bridge.ledger.v1"
            ),
            conjecturer_turn_contract=(
                "conjecturer.turn.v4"
                if active
                else "conjecturer.legacy.v1"
            ),
            control_event_schema="control.event.v1" if controlled else "none",
        ),
        capability_profile="conjecture-control.v1" if controlled else "legacy.v1",
    )
    return compile_run_manifest(
        config,
        schema_version=4,
        workload_profile="text",
        rubric_policy="forbid",
        compiled_at=STAMP,
        control_plane_policy=control,
    )


def _candidates(*contents: str) -> str:
    return json.dumps(
        {
            "candidates": [
                {
                    "content": content,
                    "typicality": 0.42 + index / 100,
                }
                for index, content in enumerate(contents)
            ]
        }
    )


def _candidate() -> str:
    return _candidates("A deterministic C0 scheduler candidate.")


def _normalized_events(harness: Harness) -> list[dict]:
    events = list(harness.log.read())
    call_refs = {
        int(value.removeprefix("conjecture-call:"))
        for event in events
        for value in event.inputs
        if value.startswith("conjecture-call:")
    }
    split_calls = {
        event.seq: event.llm
        for event in events
        if event.llm is not None
        and event.inputs
        and event.inputs[0] == "workflow-conjecture-call"
    }
    records = []
    for event in events:
        if event.rule == Rule.CONTROL:
            continue
        record = event.model_dump(mode="json", by_alias=True)
        record.pop("ts")
        if event.seq in split_calls and event.seq in call_refs:
            # C1 persists the provider completion before admission. Collapse
            # the split pair back to the legacy semantic event for the
            # noninterference differential.
            continue
        if event.seq in split_calls and event.seq not in call_refs:
            record["inputs"] = [
                "conj-noregister",
                *(
                    value
                    for value in record["inputs"]
                    if value.startswith("school:")
                ),
            ]
        conjecture_refs = [
            value
            for value in record["inputs"]
            if value.startswith("conjecture-call:")
        ]
        if conjecture_refs:
            source_seq = int(conjecture_refs[0].removeprefix("conjecture-call:"))
            record["inputs"] = [
                value
                for value in record["inputs"]
                if not value.startswith("conjecture-call:")
            ]
            record["llm"] = split_calls[source_seq].model_dump(
                mode="json", by_alias=True
            )
        record["seq"] = len(records)
        # Wall-clock latency is observational and naturally differs by a
        # millisecond across two otherwise identical in-process mock runs.
        if record["llm"] is not None:
            record["llm"].pop("ms")
            # C1 adds a process-only work-order correlation pointer in shadow
            # mode.  It has no semantic, formal, scratch, bridge, or accounting
            # effect and is compared through replayable control tests instead.
            record["llm"].pop("work_order_id", None)
            for attempt in record["llm"]["attempt_trace"]:
                attempt.pop("ms")
        records.append(record)
    return records


def _tree_payloads(root: Path) -> dict[str, str]:
    """Durable content except manifest sidecars, whose policies intentionally differ."""

    payloads = {}
    for path in sorted(item for item in root.rglob("*") if item.is_file()):
        relative = path.relative_to(root).as_posix()
        if (
            relative.startswith("run-manifest")
            or relative == "log.jsonl"
            or relative == "workflow-checkpoint.json"
            or relative.startswith("objects/workflow-")
            or relative.startswith("objects/artifact/")
        ):
            continue
        payloads[relative] = hashlib.sha256(path.read_bytes()).hexdigest()
    return payloads


def _all_tree_payloads(root: Path) -> dict[str, str]:
    return {
        path.relative_to(root).as_posix(): hashlib.sha256(path.read_bytes()).hexdigest()
        for path in sorted(item for item in root.rglob("*") if item.is_file())
    }


@dataclass
class _RunCapture:
    harness: Harness
    scheduler: Scheduler
    prompts: list[str]
    meter: TokenMeter
    meter_before: dict
    report: dict


def _run(
    root: Path,
    mode: str,
    *,
    response: str | None = None,
    responses: tuple[str, ...] | None = None,
    cycles: int = 1,
    vs_k: int = 1,
    problem_id: str = "pi-workflow-shadow-c0",
    retry_max: int = 0,
    meter_budget: int = 100_000,
) -> _RunCapture:
    if response is not None and responses is not None:
        raise ValueError("provide one fixed response or one response sequence")
    config = _config(vs_k=vs_k, retry_max=retry_max)
    manifest = _manifest(config, mode)
    bind_run_manifest(manifest, root)
    harness = Harness(root)
    harness.register_problem(
        Problem(
            id=problem_id,
            description="Exercise one deterministic legacy conjecture cycle.",
            provenance=ProblemProvenance.model_validate(
                {"trigger": "seed", "from": []}
            ),
        )
    )
    prompts: list[str] = []
    scripted = iter(responses) if responses is not None else None

    def complete(prompt: str) -> str:
        prompts.append(prompt)
        if scripted is not None:
            return next(scripted)
        return _candidate() if response is None else response

    meter = TokenMeter(budget=meter_budget)
    meter_before = meter.snapshot()
    endpoint = MockEndpoint(
        complete,
        name=manifest.roles["conjecturer"][0].base_url,
        model=manifest.roles["conjecturer"][0].model_id,
        max_tokens=256,
    )
    adapter = LLMAdapter(
        {"conjecturer": endpoint},
        harness.blobs,
        meter=meter,
        retry_max=retry_max,
        model_profile=manifest.model_profile,
        leases=leases_from_manifest(manifest),
    )
    scheduler = Scheduler(
        harness,
        adapter,
        config,
        workload_profile="text",
        run_manifest=manifest,
    )
    report = scheduler.run(cycles)
    return _RunCapture(harness, scheduler, prompts, meter, meter_before, report)


def _assert_authoritative_surfaces_equal(
    legacy: _RunCapture,
    shadow: _RunCapture,
) -> None:
    assert shadow.prompts == legacy.prompts
    assert shadow.meter.snapshot() == legacy.meter.snapshot()
    assert shadow.report == legacy.report
    assert shadow.scheduler._cycles == legacy.scheduler._cycles
    assert shadow.scheduler._problem_worked == legacy.scheduler._problem_worked
    assert _normalized_events(shadow.harness) == _normalized_events(legacy.harness)
    def normalized_state(harness):
        value = harness.state.model_dump(mode="json")
        semantic_seq = {
            event.seq: index
            for index, event in enumerate(
                event
                for event in harness.log.read()
                if event.rule != Rule.CONTROL
                and not (
                    event.inputs
                    and event.inputs[0] == "workflow-conjecture-call"
                )
            )
        }
        for artifact in value["artifacts"].values():
            artifact["provenance"]["event_seq"] = semantic_seq[
                artifact["provenance"]["event_seq"]
            ]
        return value

    assert normalized_state(shadow.harness) == normalized_state(legacy.harness)
    assert shadow.harness.scratch_state == legacy.harness.scratch_state
    assert shadow.harness.bridge_state == legacy.harness.bridge_state
    assert shadow.harness.commitments == legacy.harness.commitments
    assert shadow.harness.warrants == legacy.harness.warrants
    assert _tree_payloads(shadow.harness.root) == _tree_payloads(legacy.harness.root)


def test_shadow_cycle_persists_control_without_changing_legacy_actuation(tmp_path):
    legacy = _run(tmp_path / "legacy", "legacy")
    shadow = _run(tmp_path / "shadow", "shadow")

    observations = getattr(shadow.scheduler, "workflow_shadow_observations", None)
    assert observations, "the shadow reducer must actually observe the conjecture path"
    assert all(observation.matched for observation in observations)

    # Exact prompts, calls, admission, scheduler bookkeeping, and accounting
    # remain those of the authoritative legacy scheduler.
    _assert_authoritative_surfaces_equal(legacy, shadow)

    control_events = [
        event for event in shadow.harness.log.read() if event.rule == Rule.CONTROL
    ]
    assert control_events
    assert shadow.harness.workflow_state.outstanding_work_order_ids == ()
    reopened = Harness(shadow.harness.root)
    assert reopened.state == shadow.harness.state
    assert reopened.scratch_state == shadow.harness.scratch_state
    assert reopened.bridge_state == shadow.harness.bridge_state
    assert reopened.workflow_state.digest == shadow.harness.workflow_state.digest
    assert verify_root(
        shadow.harness.root,
        meter_total=shadow.meter.total,
    )["violations"] == []


def test_active_basic_conjecture_is_bound_ordered_and_semantically_compatible(
    tmp_path,
):
    legacy = _run(tmp_path / "legacy", "legacy")
    shadow = _run(tmp_path / "shadow", "shadow")
    active = _run(tmp_path / "active", "active_conjecture")

    _assert_authoritative_surfaces_equal(legacy, shadow)
    assert active.harness.state == shadow.harness.state
    assert active.harness.scratch_state == shadow.harness.scratch_state
    assert active.harness.bridge_state == shadow.harness.bridge_state
    assert active.report == shadow.report == legacy.report

    (work_order_id,) = tuple(active.harness.workflow_state.work_orders)
    work = active.harness.workflow_state.work_orders[work_order_id]
    assert work.workflow_profile == "conjecture.active.v1"
    assert work.contract_id == "conjecturer.turn.v4"

    events = tuple(active.harness.log.read())
    controls = {}
    for event in events:
        if event.control is None:
            continue
        _schema, decision = active.harness.objects.get(
            event.control.decision_ref,
            schema="workflow-transition-decision",
        )
        if decision.work_order_id == work_order_id:
            controls[decision.transition_kind] = event.seq
    (provider_event,) = tuple(
        event
        for event in events
        if event.llm is not None and event.llm.role == "conjecturer"
    )
    (admission_event,) = tuple(
        event
        for event in events
        if event.rule == Rule.CONJ and event.outputs
    )

    assert provider_event.llm.work_order_id == work_order_id
    assert provider_event.llm.conjecture_context is None
    assert {
        attempt.contract_id for attempt in provider_event.llm.attempt_trace
    } == {"conjecturer.turn.v4"}
    assert (
        controls[TransitionKind.WORK_ENABLED]
        < controls[TransitionKind.WORK_ISSUED]
        < provider_event.seq
        < controls[TransitionKind.PROPOSAL_RECEIVED]
        < controls[TransitionKind.PROPOSAL_ADMITTED]
        < admission_event.seq
    )
    assert active.harness.workflow_state.outstanding_work_order_ids == ()
    assert active.harness.workflow_state.recovery_status(
        work_order_id
    ).value == "finished"
    assert active.scheduler.workflow_shadow_observations
    assert all(
        observation.matched
        for observation in active.scheduler.workflow_shadow_observations
    )
    assert verify_root(
        active.harness.root,
        meter_total=active.meter.total,
    )["violations"] == []


def test_active_planning_failure_stops_before_unbound_dispatch(
    tmp_path,
    monkeypatch,
):
    def fail_planning(*_args, **_kwargs):
        raise RuntimeError("injected active planning failure")

    monkeypatch.setattr(
        ConjectureShadowObserver,
        "begin_conjecture",
        fail_planning,
    )
    shadow = _run(tmp_path / "shadow-planner-failure", "shadow")
    assert shadow.harness.state.artifacts

    active_root = tmp_path / "active-planner-failure"
    with pytest.raises(RuntimeError, match="injected active planning failure"):
        _run(active_root, "active_conjecture")

    failed = Harness(active_root)
    assert failed.state.artifacts == {}
    assert failed.workflow_state.work_orders == {}
    assert not any(
        event.llm is not None and event.llm.role == "conjecturer"
        for event in failed.log.read()
    )


def test_active_trace_failure_is_terminal_while_shadow_remains_advisory(
    tmp_path,
    monkeypatch,
):
    original = Harness.record_control_transition

    def fail_enable(self, decision, **kwargs):
        if decision.transition_kind == TransitionKind.WORK_ENABLED:
            raise RuntimeError("injected durable enable failure")
        return original(self, decision, **kwargs)

    monkeypatch.setattr(Harness, "record_control_transition", fail_enable)

    shadow = _run(tmp_path / "shadow-trace-failure", "shadow")
    assert shadow.harness.state.artifacts
    assert len(shadow.prompts) == 1

    active_root = tmp_path / "active-trace-failure"
    with pytest.raises(
        WorkflowAuthorizationError,
        match="not durably authorized",
    ):
        _run(active_root, "active_conjecture")

    failed = Harness(active_root)
    assert failed.state.artifacts == {}
    assert failed.workflow_state.work_orders == {}
    assert not any(
        event.llm is not None and event.llm.role == "conjecturer"
        for event in failed.log.read()
    )
    assert any(
        event.rule == Rule.MEASURE
        and event.inputs
        and event.inputs[0] == "dropped-call"
        for event in failed.log.read()
    )


def _record_enabled_work(root: Path, work: WorkOrderEnvelopeV1) -> None:
    initial = WorkflowProcessStateV1.initial(
        manifest_digest=work.manifest_digest,
        workflow_profile=work.workflow_profile,
        formal_fence_seq=work.formal_fence_seq,
        scratch_fence_seq=work.scratch_fence_seq,
    )
    next_state = state_after_transition(
        initial,
        transition_kind=TransitionKind.WORK_ENABLED,
        work_order_id=work.id,
        trigger_ref=work.problem_ref,
    )
    decision = TransitionDecisionV1.create(
        manifest_digest=work.manifest_digest,
        workflow_profile=work.workflow_profile,
        previous_process_digest=initial.digest,
        trigger_kind=TriggerKind.PROBLEM_SELECTED,
        trigger_ref=work.problem_ref,
        transition_kind=TransitionKind.WORK_ENABLED,
        work_order_id=work.id,
        route_lease=work.route_lease,
        next_process_digest=next_state.digest,
    )
    Harness(root).record_control_transition(decision, work_order=work)


@pytest.mark.parametrize(
    ("forgery", "expected_detail"),
    (
        ("contract", "contract_id"),
        ("route", "route_lease"),
        ("capability", "capability_grant"),
        ("repair", "repair_policy_ref"),
    ),
)
def test_verify_root_rejects_work_outside_manifest_authority(
    tmp_path,
    forgery: str,
    expected_detail: str,
):
    root = tmp_path / forgery
    manifest = _manifest(_config(), "shadow")
    bind_run_manifest(manifest, root)
    profile = compile_workflow_profile(manifest)
    route = manifest.roles["conjecturer"][0]
    valid_work = plan_conjecture_work(
        profile,
        problem_ref="problem:manifest-authority",
        school_id=None,
        route_lease=RouteLeaseRefV1(
            seat=0,
            endpoint_id=route.endpoint_id,
            route_sha256=route_fingerprint(route),
        ),
        contract_id="conjecturer.direct.v1",
        formal_fence_seq=0,
        scratch_fence_seq=0,
        task_payload_schema_id="conjecture.semantic-ref.v1",
        task_payload_ref="problem:manifest-authority",
        input_refs=("problem:manifest-authority",),
    )
    values = valid_work.model_dump(
        mode="python",
        by_alias=True,
        exclude={"id"},
    )
    if forgery == "contract":
        values["contract_id"] = "forged.contract.v99"
    elif forgery == "route":
        values["route_lease"] = RouteLeaseRefV1(
            seat=0,
            endpoint_id="forged-endpoint",
            route_sha256="f" * 64,
        )
    elif forgery == "capability":
        grant_values = valid_work.capability_grant.model_dump(
            mode="python",
            by_alias=True,
            exclude={"id"},
        )
        grant_values["max_candidates"] += 1
        values["capability_grant"] = CapabilityGrantV1.create(**grant_values)
    elif forgery == "repair":
        values["repair_policy_ref"] = "sha256:" + "9" * 64
    forged_work = WorkOrderEnvelopeV1.create(**values)
    _record_enabled_work(root, forged_work)

    violations = verify_root(root)["violations"]

    assert any(
        item["check"] == "workflow-work-order-authority"
        and expected_detail in item["detail"]
        for item in violations
    )


def test_verify_root_accepts_conditioning_only_school_on_default_route(tmp_path):
    root = tmp_path / "conditioning-only-school"
    manifest = _manifest(_config(schools=1), "shadow")
    bind_run_manifest(manifest, root)
    profile = compile_workflow_profile(manifest)
    route = manifest.roles["conjecturer"][0]
    work = plan_conjecture_work(
        profile,
        problem_ref="problem:conditioning-only-school",
        school_id="school-0",
        route_lease=RouteLeaseRefV1(
            seat=0,
            endpoint_id=route.endpoint_id,
            route_sha256=route_fingerprint(route),
        ),
        contract_id="conjecturer.direct.v1",
        formal_fence_seq=0,
        scratch_fence_seq=0,
        task_payload_schema_id="conjecture.semantic-ref.v1",
        task_payload_ref="problem:conditioning-only-school",
        input_refs=("problem:conditioning-only-school",),
    )
    _record_enabled_work(root, work)

    assert verify_root(root)["violations"] == []


def test_c1_shadow_trace_temporally_brackets_provider_and_admission(tmp_path):
    """Authority must surround, not merely summarize, matched Conj work.

    The legacy path currently combines the provider receipt and semantic Conj
    admission in one event.  C1's safe order intentionally requires those
    boundaries to be split so the proposal transition is durable before the
    semantic artifact is admitted.
    """

    run = _run(tmp_path / "shadow-temporal-order", "shadow")
    comparison = run.scheduler.workflow_shadow_observations[0]
    assert comparison.matched
    work_order_id = comparison.work_order_id
    assert work_order_id is not None

    events = list(run.harness.log.read())
    controls = {}
    for event in events:
        if event.control is None:
            continue
        _schema, decision = run.harness.objects.get(
            event.control.decision_ref,
            schema="workflow-transition-decision",
        )
        if decision.work_order_id == work_order_id:
            assert decision.transition_kind not in controls
            controls[decision.transition_kind] = event

    provider_events = [
        event
        for event in events
        if event.llm is not None and event.llm.work_order_id == work_order_id
    ]
    admission_events = [
        event
        for event in events
        if event.rule == Rule.CONJ
        and set(event.outputs).intersection(comparison.admitted_refs)
    ]
    assert len(provider_events) == 1
    assert len(admission_events) == 1
    assert {
        TransitionKind.WORK_ENABLED,
        TransitionKind.WORK_ISSUED,
        TransitionKind.PROPOSAL_RECEIVED,
        TransitionKind.PROPOSAL_ADMITTED,
    }.issubset(controls)

    reopened = Harness(run.harness.root)
    assert reopened.workflow_state.digest == run.harness.workflow_state.digest
    assert reopened.workflow_state.outstanding_work_order_ids == ()
    assert (
        reopened.workflow_state.recovery_status(work_order_id).value
        == "finished"
    )

    enabled_seq = controls[TransitionKind.WORK_ENABLED].seq
    issued_seq = controls[TransitionKind.WORK_ISSUED].seq
    provider_seq = provider_events[0].seq
    proposal_seq = controls[TransitionKind.PROPOSAL_RECEIVED].seq
    admission_seq = admission_events[0].seq
    guard_seq = controls[TransitionKind.PROPOSAL_ADMITTED].seq
    _schema, issued_decision = run.harness.objects.get(
        controls[TransitionKind.WORK_ISSUED].control.decision_ref,
        schema="workflow-transition-decision",
    )
    _schema, proposal_decision = run.harness.objects.get(
        controls[TransitionKind.PROPOSAL_RECEIVED].control.decision_ref,
        schema="workflow-transition-decision",
    )
    assert issued_decision.budget_delta.reserved_tokens >= (
        provider_events[0].llm.tokens
    )
    assert proposal_decision.budget_delta.reserved_tokens == 0
    violations = []
    if not enabled_seq < issued_seq < provider_seq:
        violations.append(
            "WORK_ENABLED < WORK_ISSUED < bound provider event"
        )
    if not provider_seq < proposal_seq:
        violations.append("bound provider event < PROPOSAL_RECEIVED")
    if not proposal_seq < guard_seq < admission_seq:
        violations.append(
            "PROPOSAL_RECEIVED < guarded disposition < semantic Conj admission"
        )
    assert not violations, (
        f"unsafe C1 event order {violations}: enabled={enabled_seq}, "
        f"issued={issued_seq}, provider={provider_seq}, proposal={proposal_seq}, "
        f"admission={admission_seq}, guard={guard_seq}"
    )


def test_restart_abandons_every_durable_shadow_crash_prefix(tmp_path):
    complete = _run(tmp_path / "complete", "shadow")
    manifest = complete.scheduler.run_manifest
    assert manifest.schema_version == 4
    old_work_order_ids = tuple(complete.harness.workflow_state.work_orders)
    assert len(old_work_order_ids) == 1
    assert complete.harness.workflow_state.outstanding_work_order_ids == ()

    cut_seqs = {}
    for event in complete.harness.log.read():
        if event.control is not None:
            _schema, decision = complete.harness.objects.get(
                event.control.decision_ref,
                schema="workflow-transition-decision",
            )
            labels = {
                TransitionKind.WORK_ENABLED: "enabled",
                TransitionKind.WORK_ISSUED: "issued",
                TransitionKind.PROPOSAL_RECEIVED: "proposal-received",
            }
            if decision.transition_kind in labels:
                cut_seqs[labels[decision.transition_kind]] = event.seq
        if (
            event.llm is not None
            and event.llm.work_order_id in old_work_order_ids
        ):
            cut_seqs["provider-call"] = event.seq
    assert set(cut_seqs) == {
        "enabled",
        "issued",
        "provider-call",
        "proposal-received",
    }

    complete_lines = (complete.harness.root / "log.jsonl").read_bytes().splitlines(
        keepends=True
    )
    for label, cut_seq in cut_seqs.items():
        crash_root = tmp_path / f"crash-{label}"
        shutil.copytree(complete.harness.root, crash_root)
        (crash_root / "log.jsonl").write_bytes(
            b"".join(complete_lines[: cut_seq + 1])
        )
        (crash_root / "workflow-checkpoint.json").unlink()
        bind_run_manifest(manifest, crash_root)

        resumed = Harness(crash_root)
        assert tuple(resumed.workflow_state.work_orders) == old_work_order_ids
        assert resumed.workflow_state.outstanding_work_order_ids == old_work_order_ids

        endpoint = MockEndpoint(
            lambda _prompt: _candidates("A distinct post-restart candidate."),
            name=manifest.roles["conjecturer"][0].base_url,
            model=manifest.roles["conjecturer"][0].model_id,
            max_tokens=256,
        )
        adapter = LLMAdapter(
            {"conjecturer": endpoint},
            resumed.blobs,
            meter=TokenMeter(budget=100_000),
            retry_max=0,
            model_profile=manifest.model_profile,
            leases=leases_from_manifest(manifest),
        )
        scheduler = Scheduler(
            resumed,
            adapter,
            _config(),
            workload_profile="text",
            run_manifest=manifest,
        )

        scheduler.run(1)

        assert scheduler._cycles == 1
        assert resumed.workflow_state.outstanding_work_order_ids == ()
        assert all(
            resumed.workflow_state.recovery_status(work_order_id).value
            == "abandoned"
            for work_order_id in old_work_order_ids
        )
        durable = Harness(crash_root)
        assert durable.workflow_state.outstanding_work_order_ids == ()
        assert all(
            durable.workflow_state.recovery_status(work_order_id).value
            == "abandoned"
            for work_order_id in old_work_order_ids
        )


def test_semantic_clock_collapses_split_conjecture_call_carrier(tmp_path):
    legacy = _run(tmp_path / "legacy-semantic-clock", "legacy")
    shadow = _run(tmp_path / "shadow-semantic-clock", "shadow")
    events = list(shadow.harness.log.read())
    carrier = next(
        event
        for event in events
        if event.llm is not None
        and event.inputs
        and event.inputs[0] == "workflow-conjecture-call"
    )
    admission = next(
        event
        for event in events
        if f"conjecture-call:{carrier.seq}" in event.inputs
    )

    before_carrier = shadow.harness.semantic_event_clock(carrier.seq)
    assert shadow.harness.semantic_event_clock(carrier.seq + 1) == before_carrier
    assert shadow.harness.semantic_event_clock(admission.seq + 1) == (
        before_carrier + 1
    )
    assert shadow.harness._next_seq > legacy.harness._next_seq
    assert shadow.harness.semantic_event_clock() == (
        legacy.harness.semantic_event_clock()
    )
    assert Harness(shadow.harness.root).semantic_event_clock() == (
        shadow.harness.semantic_event_clock()
    )


def test_shadow_explains_legacy_no_register_as_deduplication(tmp_path):
    legacy = _run(tmp_path / "legacy-dedupe", "legacy", cycles=2)
    shadow = _run(tmp_path / "shadow-dedupe", "shadow", cycles=2)

    observations = shadow.scheduler.workflow_shadow_observations
    assert len(observations) == 2
    assert all(observation.matched for observation in observations)
    first, second = observations
    assert TransitionKind.PROPOSAL_ADMITTED in first.expected_transition_kinds
    assert second.admitted_refs == ()
    assert second.proposal_candidate_refs == second.deduplicated_refs
    assert second.deduplicated_refs
    assert TransitionKind.PROPOSAL_DEDUPLICATED in (
        second.expected_transition_kinds
    )
    assert TransitionKind.WORK_FINISHED not in second.expected_transition_kinds
    _assert_authoritative_surfaces_equal(legacy, shadow)


def test_shadow_explains_mixed_admission_and_existing_deduplication(tmp_path):
    first = _candidates("Existing candidate.")
    mixed = _candidates("Existing candidate.", "New candidate.")
    legacy = _run(
        tmp_path / "legacy-mixed-dedupe",
        "legacy",
        cycles=2,
        vs_k=2,
        responses=(first, mixed),
    )
    shadow = _run(
        tmp_path / "shadow-mixed-dedupe",
        "shadow",
        cycles=2,
        vs_k=2,
        responses=(first, mixed),
    )

    comparison = shadow.scheduler.workflow_shadow_observations[1]
    assert comparison.matched
    assert len(comparison.proposal_candidate_refs) == 2
    assert len(comparison.admitted_refs) == 1
    assert len(comparison.deduplicated_refs) == 1
    assert set(comparison.proposal_candidate_refs) == {
        *comparison.admitted_refs,
        *comparison.deduplicated_refs,
    }
    assert TransitionKind.PROPOSAL_ADMITTED in comparison.expected_transition_kinds
    assert TransitionKind.WORK_FINISHED not in comparison.expected_transition_kinds
    _assert_authoritative_surfaces_equal(legacy, shadow)


def test_shadow_names_repeated_candidate_occurrences_independently(tmp_path):
    repeated = _candidates("Repeated candidate.", "Repeated candidate.")
    legacy = _run(
        tmp_path / "legacy-repeated-candidate",
        "legacy",
        vs_k=2,
        response=repeated,
    )
    shadow = _run(
        tmp_path / "shadow-repeated-candidate",
        "shadow",
        vs_k=2,
        response=repeated,
    )

    comparison = shadow.scheduler.workflow_shadow_observations[0]
    assert comparison.matched
    assert len(comparison.proposal_candidate_refs) == 2
    assert len(set(comparison.proposal_candidate_refs)) == 2
    assert comparison.admitted_refs == comparison.proposal_candidate_refs[:1]
    assert comparison.deduplicated_refs == comparison.proposal_candidate_refs[1:]
    _assert_authoritative_surfaces_equal(legacy, shadow)


def test_direct_shadow_observer_consumes_snapshots_without_mutation(tmp_path):
    run = _run(tmp_path / "direct-shadow", "shadow")
    manifest = run.scheduler.run_manifest
    observer = ConjectureShadowObserver.from_manifest(manifest)
    assert observer is not None

    events = tuple(run.harness.log.read())
    call_event = next(event for event in events if event.llm is not None)
    contract_id = call_event.llm.attempt_trace[0].contract_id
    route = route_lease_reference(
        leases_from_manifest(manifest)["conjecturer"][0]
    )
    problem_ref = "pi-workflow-shadow-c0"
    canonical_problem_refs = tuple(sorted(run.harness.state.problems))

    before = {
        "formal": copy.deepcopy(run.harness.state),
        "scratch": copy.deepcopy(run.harness.scratch_state),
        "bridge": copy.deepcopy(run.harness.bridge_state),
        "commitments": copy.deepcopy(run.harness.commitments),
        "warrants": copy.deepcopy(run.harness.warrants),
        "events": _normalized_events(run.harness),
        "files": _all_tree_payloads(run.harness.root),
        "prompts": tuple(run.prompts),
        "meter": run.meter.snapshot(),
        "report": copy.deepcopy(run.report),
    }

    for invalid_refs in ((), ("problem:another-prefix",)):
        with pytest.raises(ValueError, match="canonical"):
            observer.begin_conjecture(
                problem_ref=problem_ref,
                canonical_problem_refs=invalid_refs,
                school_id=None,
                route_lease=route,
                contract_id=contract_id,
                formal_fence_seq=0,
                scratch_fence_seq=0,
                event_start_seq=0,
                meter_before=run.meter_before,
            )

    ticket = observer.begin_conjecture(
        problem_ref=problem_ref,
        canonical_problem_refs=canonical_problem_refs,
        school_id=None,
        route_lease=route,
        contract_id=contract_id,
        formal_fence_seq=0,
        scratch_fence_seq=0,
        event_start_seq=0,
        meter_before=run.meter_before,
    )
    admitted_refs = tuple(
        output
        for event in events
        if event.rule.value == "Conj"
        for output in event.outputs
    )
    comparison = observer.finish_conjecture(
        ticket,
        actual_problem_ref=problem_ref,
        events=events,
        admitted_refs=admitted_refs,
        meter_after=run.meter.snapshot(),
    )

    assert comparison.matched
    assert comparison.expected_route == comparison.actual_route == route
    assert comparison.admitted_refs == admitted_refs

    wrong_problem = observer.finish_conjecture(
        ticket,
        actual_problem_ref="pi-another-workflow-problem",
        events=events,
        admitted_refs=admitted_refs,
        meter_after=run.meter.snapshot(),
    )
    assert not wrong_problem.matched
    assert ShadowMismatchCode.PROBLEM in wrong_problem.mismatch_codes

    changed_meter = dict(run.meter.snapshot())
    changed_meter["calls"] += 1
    budget_mismatch = observer.finish_conjecture(
        ticket,
        actual_problem_ref=problem_ref,
        events=events,
        admitted_refs=admitted_refs,
        meter_after=changed_meter,
    )
    assert not budget_mismatch.matched
    assert ShadowMismatchCode.BUDGET in budget_mismatch.mismatch_codes

    context_ticket = observer.begin_conjecture(
        problem_ref=problem_ref,
        canonical_problem_refs=canonical_problem_refs,
        school_id=None,
        route_lease=route,
        contract_id=contract_id,
        formal_fence_seq=0,
        scratch_fence_seq=0,
        event_start_seq=0,
        meter_before=run.meter_before,
        advisory_context_ref="sha256:" + "9" * 64,
    )
    context_mismatch = observer.finish_conjecture(
        context_ticket,
        actual_problem_ref=problem_ref,
        events=events,
        admitted_refs=admitted_refs,
        meter_after=run.meter.snapshot(),
    )
    assert not context_mismatch.matched
    assert ShadowMismatchCode.CONTEXT in context_mismatch.mismatch_codes

    contract_ticket = observer.begin_conjecture(
        problem_ref=problem_ref,
        canonical_problem_refs=canonical_problem_refs,
        school_id=None,
        route_lease=route,
        contract_id="conjecturer.unexpected.v999",
        formal_fence_seq=0,
        scratch_fence_seq=0,
        event_start_seq=0,
        meter_before=run.meter_before,
    )
    contract_mismatch = observer.finish_conjecture(
        contract_ticket,
        actual_problem_ref=problem_ref,
        events=events,
        admitted_refs=admitted_refs,
        meter_after=run.meter.snapshot(),
    )
    assert not contract_mismatch.matched
    assert ShadowMismatchCode.CONTRACT in contract_mismatch.mismatch_codes

    assert run.harness.state == before["formal"]
    assert run.harness.scratch_state == before["scratch"]
    assert run.harness.bridge_state == before["bridge"]
    assert run.harness.commitments == before["commitments"]
    assert run.harness.warrants == before["warrants"]
    assert _normalized_events(run.harness) == before["events"]
    assert _all_tree_payloads(run.harness.root) == before["files"]
    assert tuple(run.prompts) == before["prompts"]
    assert run.meter.snapshot() == before["meter"]
    assert run.report == before["report"]


@pytest.mark.parametrize(
    "method_name",
    ("from_manifest", "begin_conjecture", "finish_conjecture"),
)
def test_observer_failure_is_non_authoritative(
    tmp_path,
    monkeypatch,
    method_name: str,
):
    def fail_observation(*_args, **_kwargs):
        raise RuntimeError(f"injected-{method_name}-failure")

    monkeypatch.setattr(ConjectureShadowObserver, method_name, fail_observation)
    legacy = _run(tmp_path / f"legacy-{method_name}", "legacy")
    shadow = _run(tmp_path / f"shadow-{method_name}", "shadow")

    observations = shadow.scheduler.workflow_shadow_observations
    assert observations
    assert any(
        getattr(observation, "error_type", None) == "RuntimeError"
        for observation in observations
    )
    _assert_authoritative_surfaces_equal(legacy, shadow)


def test_candidate_sink_setup_failure_is_non_authoritative(tmp_path, monkeypatch):
    original = Scheduler._workflow_shadow_candidate_sink

    def fail_only_when_shadow_is_enabled(self):
        if self.workflow_shadow_observer is not None:
            raise RuntimeError("injected-candidate-sink-setup-failure")
        return original(self)

    monkeypatch.setattr(
        Scheduler,
        "_workflow_shadow_candidate_sink",
        fail_only_when_shadow_is_enabled,
    )
    legacy = _run(tmp_path / "legacy-candidate-sink-failure", "legacy")
    shadow = _run(tmp_path / "shadow-candidate-sink-failure", "shadow")

    observations = shadow.scheduler.workflow_shadow_observations
    assert observations
    assert any(
        observation.error_type == "RuntimeError" for observation in observations
    )
    _assert_authoritative_surfaces_equal(legacy, shadow)


def test_schema_repair_drop_is_observed_without_shadow_side_effects(tmp_path):
    invalid_response = "{this-is-not-valid-json"
    legacy = _run(
        tmp_path / "legacy-schema-drop",
        "legacy",
        response=invalid_response,
    )
    shadow = _run(
        tmp_path / "shadow-schema-drop",
        "shadow",
        response=invalid_response,
    )

    observations = shadow.scheduler.workflow_shadow_observations
    assert len(observations) == 1
    comparison = observations[0]
    assert comparison.matched
    assert comparison.admitted_refs == ()
    assert comparison.source_call_seq is not None
    assert shadow.meter.snapshot()["calls"] >= 1
    assert any(
        event.llm is not None
        and event.rule.value == "Measure"
        and event.inputs
        and event.inputs[0] == "dropped-call"
        for event in shadow.harness.log.read()
    )
    _assert_authoritative_surfaces_equal(legacy, shadow)
    assert any(event.rule == Rule.CONTROL for event in shadow.harness.log.read())


def test_unrepresentable_legacy_problem_ref_cannot_escape_observer(tmp_path):
    problem_id = "pi-" + "x" * 512
    legacy = _run(
        tmp_path / "legacy-long-problem-ref",
        "legacy",
        problem_id=problem_id,
    )
    shadow = _run(
        tmp_path / "shadow-long-problem-ref",
        "shadow",
        problem_id=problem_id,
    )

    observations = shadow.scheduler.workflow_shadow_observations
    assert len(observations) == 1
    diagnostic = observations[0]
    assert not diagnostic.matched
    assert diagnostic.error_type == "ValidationError"
    assert diagnostic.problem_ref.startswith("unrepresentable:sha256:")
    assert ShadowMismatchCode.OBSERVER_ERROR in diagnostic.mismatch_codes
    _assert_authoritative_surfaces_equal(legacy, shadow)


def test_mid_retry_budget_stop_is_not_reported_as_repair_exhaustion(tmp_path):
    invalid_response = "{this-is-not-valid-json"
    legacy = _run(
        tmp_path / "legacy-mid-retry-budget-stop",
        "legacy",
        response=invalid_response,
        retry_max=2,
        meter_budget=850,
    )
    shadow = _run(
        tmp_path / "shadow-mid-retry-budget-stop",
        "shadow",
        response=invalid_response,
        retry_max=2,
        meter_budget=850,
    )

    observations = shadow.scheduler.workflow_shadow_observations
    assert len(observations) == 1
    comparison = observations[0]
    assert not comparison.matched
    assert (
        comparison.termination_kind
        == ShadowTerminationKind.TOKEN_BUDGET_EXCEEDED
    )
    assert ShadowMismatchCode.BUDGET in comparison.mismatch_codes
    assert TransitionKind.REPAIR_EXHAUSTED not in comparison.expected_transition_kinds
    assert comparison.proposal_receipt_id is None
    assert any("token budget" in item["stopped"] for item in shadow.scheduler.diagnostics)
    work_order_id = comparison.work_order_id
    assert work_order_id is not None
    assert shadow.harness.workflow_state.recovery_status(
        work_order_id
    ).value == "abandoned"
    assert shadow.harness.workflow_state.outstanding_work_order_ids == ()
    transition_kinds = []
    for event in shadow.harness.log.read():
        if event.control is None:
            continue
        _schema, decision = shadow.harness.objects.get(
            event.control.decision_ref,
            schema="workflow-transition-decision",
        )
        if decision.work_order_id == work_order_id:
            transition_kinds.append(decision.transition_kind)
    assert TransitionKind.WORK_ABANDONED in transition_kinds
    assert TransitionKind.REPAIR_EXHAUSTED not in transition_kinds
    assert (shadow.harness.root / "workflow-checkpoint.json").exists()
    reopened = Harness(shadow.harness.root)
    assert reopened.workflow_state.outstanding_work_order_ids == ()
    assert reopened.workflow_state.recovery_status(work_order_id).value == "abandoned"
    violations = verify_root(
        shadow.harness.root,
        meter_total=shadow.meter.total,
    )["violations"]
    assert not [item for item in violations if item["check"] == "repair-metadata"]
    _assert_authoritative_surfaces_equal(legacy, shadow)
