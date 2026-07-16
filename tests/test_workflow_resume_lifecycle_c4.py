from __future__ import annotations

import hashlib
import json

import pytest

from deepreason.bridge.retry import WorkflowRetryPolicyV1
from deepreason.config import Config
from deepreason.harness import Harness
from deepreason.invariants import verify_root
from deepreason.llm.adapter import LLMAdapter
from deepreason.llm.firewall import route_fingerprint
from deepreason.ontology import Rule
from deepreason.run_manifest import (
    ConjectureContextPolicyV1,
    ContractVersionPolicyV1,
    ControlPlanePolicyV1,
    SchoolExecutionPolicyV1,
    bind_run_manifest,
    compile_run_manifest,
)
from deepreason.runtime.continuation import prepare_continuation
from deepreason.runtime.progress import _atomic_json
from deepreason.runtime.stop import (
    StopController,
    StopMetrics,
    StopPolicy,
    build_stop_record,
    persist_stop_record,
    write_stop_record,
)
from deepreason.scheduler.scheduler import Scheduler
from deepreason.workflow.events import ConjectureWorkAssignmentV1
from deepreason.workflow.lifecycle import build_stopped_lifecycle
from deepreason.workflow.models import RouteLeaseRefV1
from deepreason.workflow.profiles import compile_workflow_profile
from deepreason.workflow.reducer import plan_conjecture_batch
from deepreason.workflow.state import WorkflowProcessStateV1


def _manifest(config: Config, policy: StopPolicy):
    control = ControlPlanePolicyV1(
        controller_version="workflow.controller.v1",
        mode="shadow",
        workflow_profile="conjecture.shadow.v1",
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
        contract_versions=ContractVersionPolicyV1(
            bridge_ledger_wire_contract="bridge.ledger.v1",
            conjecturer_turn_contract="conjecturer.legacy.v1",
            control_event_schema="control.event.v1",
        ),
        capability_profile="conjecture-control.v1",
    )
    return compile_run_manifest(
        config,
        schema_version=4,
        workload_profile="text",
        rubric_policy="forbid",
        compiled_at="2026-07-16T00:00:00Z",
        stop_policy=policy.model_dump(mode="json"),
        control_plane_policy=control,
    )


def _stopped_root(root):
    policy = StopPolicy()
    config = Config(
        N_SCHOOLS=0,
        CONTROLLER=False,
        roles={
            "conjecturer": {
                "endpoint_id": "resume-conjecturer",
                "endpoint": "mock://resume-conjecturer",
                "model": "resume-model",
                "provider": "mock",
                "family": "resume-family",
                "max_tokens": 256,
            }
        },
    )
    manifest = _manifest(config, policy)
    bind_run_manifest(manifest, root)
    harness = Harness(root)
    scheduler = Scheduler(
        harness,
        LLMAdapter({}, harness.blobs),
        config,
        stop_controller=StopController(policy),
        run_manifest=manifest,
    )

    def quiet_step():
        scheduler._cycles += 1

    scheduler.step = quiet_step
    report = scheduler.run(20)
    assert report["stop_reason"] == "converged"
    stop = json.loads((root / "run-stop.json").read_text())
    _atomic_json(
        root / "checkpoint.json",
        {
            "schema": "deepreason-checkpoint-v1",
            "manifest_digest": manifest.sha256,
            "stop_digest": stop["digest"],
            "event_seq": harness._next_seq,
        },
    )
    return manifest, config, policy, harness, stop


def _enabled_work(manifest, harness):
    profile = compile_workflow_profile(manifest)
    route = manifest.roles["conjecturer"][0]
    lease = RouteLeaseRefV1(
        seat=0,
        endpoint_id=route.endpoint_id,
        route_sha256=route_fingerprint(route),
    )
    state = WorkflowProcessStateV1.initial(
        manifest_digest=manifest.sha256,
        workflow_profile=profile.workflow_profile,
        formal_fence_seq=harness._next_seq,
        scratch_fence_seq=harness._next_seq,
    )
    reduction = plan_conjecture_batch(
        profile,
        state=state,
        problem_ref="resume-problem",
        assignments=(
            ConjectureWorkAssignmentV1(
                route_lease=lease,
                contract_id=profile.conjecturer_contract_id,
                task_payload_schema_id="conjecture.semantic-ref.v1",
                task_payload_ref="resume-problem",
            ),
        ),
        canonical_problem_refs=("resume-problem",),
    )
    return reduction.work_orders[0], reduction.decisions[0]


def test_prepare_v4_continuation_emits_resumed_with_exact_file_bindings(tmp_path):
    manifest, _config, _policy, harness, stop = _stopped_root(tmp_path)
    run_checkpoint_bytes = (tmp_path / "checkpoint.json").read_bytes()
    workflow_checkpoint_bytes = (tmp_path / "workflow-checkpoint.json").read_bytes()
    event_seq = harness._next_seq

    record = prepare_continuation(tmp_path, cycles=5, tokens=100)

    assert record["prior_stop_digest"] == stop["digest"]
    assert record["run_checkpoint_digest"] == hashlib.sha256(
        run_checkpoint_bytes
    ).hexdigest()
    assert record["workflow_checkpoint_digest"] == hashlib.sha256(
        workflow_checkpoint_bytes
    ).hexdigest()
    replayed = Harness(tmp_path).workflow_state
    resume = replayed.current_resume_decision
    assert resume is not None
    assert resume.id == record["resume_decision_ref"]
    assert resume.resume_event_seq == event_seq
    assert resume.manifest_digest == manifest.sha256
    snapshot = replayed.lifecycle_snapshots[resume.resume_snapshot_ref]
    assert snapshot.outstanding_work == ()
    assert replayed.terminal_lifecycle_decision is None
    last = list(Harness(tmp_path).log.read())[-1]
    assert last.rule == Rule.CONTROL
    assert not any(last.state_diff.model_dump(mode="json").values())
    assert verify_root(tmp_path)["violations"] == []


def test_resumed_scheduler_rehydrates_exact_controller_state(tmp_path):
    manifest, config, policy, _harness, _stop = _stopped_root(tmp_path)
    prepare_continuation(tmp_path, cycles=5, tokens=100)
    resumed = Harness(tmp_path)
    resume = resumed.workflow_state.current_resume_decision
    expected_controller = StopController(policy, state=resume.controller_state)
    next_cycle = resume.controller_state.last_cycle + 1
    expected = expected_controller.evaluate(StopMetrics(cycle=next_cycle))

    scheduler = Scheduler(
        resumed,
        LLMAdapter({}, resumed.blobs),
        config,
        stop_controller=StopController(policy),
        run_manifest=manifest,
    )

    def quiet_step():
        scheduler._cycles += 1

    scheduler.step = quiet_step
    scheduler.run(1)

    assert scheduler.last_stop_decision == expected
    assert scheduler.stop_controller.snapshot() == expected_controller.snapshot()
    assert scheduler.stop_controller.snapshot().last_cycle == next_cycle


def test_resumed_scheduler_refuses_to_drop_bound_stop_controller(tmp_path):
    manifest, config, _policy, _harness, _stop = _stopped_root(tmp_path)
    prepare_continuation(tmp_path, cycles=5, tokens=100)
    resumed = Harness(tmp_path)
    scheduler = Scheduler(
        resumed,
        LLMAdapter({}, resumed.blobs),
        config,
        stop_controller=None,
        run_manifest=manifest,
    )

    with pytest.raises(RuntimeError, match="stop controller"):
        scheduler.run(1)


@pytest.mark.parametrize("filename", ["checkpoint.json", "workflow-checkpoint.json"])
def test_v4_resume_rejects_noncanonical_checkpoint_bytes(tmp_path, filename):
    _stopped_root(tmp_path)
    path = tmp_path / filename
    path.write_bytes(b" " + path.read_bytes())

    with pytest.raises(ValueError, match="CHECKPOINT|checkpoint"):
        prepare_continuation(tmp_path, cycles=5, tokens=100)


def test_resume_control_recovers_without_duplicate_after_log_append_crash(tmp_path):
    _stopped_root(tmp_path)
    first = prepare_continuation(tmp_path, cycles=5, tokens=100)
    (tmp_path / "continuations.jsonl").unlink()

    recovered = prepare_continuation(tmp_path, cycles=5, tokens=100)

    assert recovered == first
    events = [
        event
        for event in Harness(tmp_path).log.read()
        if event.control is not None
        and event.control.decision_ref == first["resume_decision_ref"]
    ]
    assert len(events) == 1
    assert len((tmp_path / "continuations.jsonl").read_text().splitlines()) == 1


def test_resume_rejects_tampered_typed_continuation_history(tmp_path):
    _stopped_root(tmp_path)
    prepare_continuation(tmp_path, cycles=5, tokens=100)
    path = tmp_path / "continuations.jsonl"
    record = json.loads(path.read_text())
    record["prior_checkpoint_ref"] = "sha256:" + "9" * 64
    path.write_text(json.dumps(record, sort_keys=True) + "\n", encoding="utf-8")

    with pytest.raises(ValueError, match="HISTORY_AUTHORITY_MISMATCH"):
        prepare_continuation(tmp_path, cycles=5, tokens=100)


def test_deleting_resumed_control_breaks_checkpointed_replay(tmp_path):
    _stopped_root(tmp_path)
    prepare_continuation(tmp_path, cycles=5, tokens=100)
    log = tmp_path / "log.jsonl"
    lines = log.read_text().splitlines()
    assert json.loads(lines[-1])["rule"] == "Control"
    log.write_text("\n".join(lines[:-1]) + "\n", encoding="utf-8")

    with pytest.raises(ValueError, match="checkpointed tail"):
        Harness(tmp_path)


def test_work_transition_is_blocked_until_resumed_and_consumes_resume(tmp_path):
    manifest, _config, _policy, harness, _stop = _stopped_root(tmp_path)
    work, enabled = _enabled_work(manifest, harness)
    with pytest.raises(ValueError, match="terminal lifecycle"):
        harness.record_control_transition(enabled, work_order=work)

    prepare_continuation(tmp_path, cycles=5, tokens=100)
    resumed = Harness(tmp_path)
    work, enabled = _enabled_work(manifest, resumed)
    resumed.record_control_transition(enabled, work_order=work)

    assert Harness(tmp_path).workflow_state.post_resume_work_started
    with pytest.raises(ValueError, match="ALREADY_RESUMED"):
        prepare_continuation(tmp_path, cycles=5, tokens=100)


def test_untyped_budget_exhaustion_cannot_reopen_v4_terminal_authority(tmp_path):
    manifest, _config, _policy, harness, _stop = _stopped_root(tmp_path)
    exhausted = write_stop_record(
        tmp_path,
        reason="budget_exhausted",
        policy=StopPolicy(),
        metrics=StopMetrics(cycle=10),
        event_seq=harness._next_seq,
    )
    _atomic_json(
        tmp_path / "checkpoint.json",
        {
            "schema": "deepreason-checkpoint-v1",
            "manifest_digest": manifest.sha256,
            "stop_digest": exhausted["digest"],
            "event_seq": harness._next_seq,
        },
    )

    with pytest.raises(ValueError, match="TYPED_STOP"):
        prepare_continuation(tmp_path, cycles=5, tokens=100)


def test_completed_typed_terminal_is_not_continuation_authority(tmp_path):
    policy = StopPolicy()
    config = Config(
        N_SCHOOLS=0,
        CONTROLLER=False,
        roles={
            "conjecturer": {
                "endpoint_id": "completed-conjecturer",
                "endpoint": "mock://completed-conjecturer",
                "model": "completed-model",
                "provider": "mock",
                "family": "completed-family",
            }
        },
    )
    manifest = _manifest(config, policy)
    bind_run_manifest(manifest, tmp_path)
    harness = Harness(tmp_path)
    controller = StopController(policy)
    before = controller.snapshot()
    metrics = StopMetrics(cycle=1, workload_complete=True)
    stop_decision = controller.evaluate(metrics)
    stop_record = build_stop_record(
        reason=stop_decision.reason,
        policy=policy,
        metrics=metrics,
        event_seq=0,
    )
    observation, snapshot, lifecycle = build_stopped_lifecycle(
        harness.workflow_state,
        manifest_digest=manifest.sha256,
        controller_version="workflow.controller.v1",
        workflow_profile="conjecture.shadow.v1",
        policy=policy,
        metrics=metrics,
        deterministic_decision=stop_decision,
        controller_state_before=before,
        controller_state_after=controller.snapshot(),
        stop_event_seq=0,
        stop_record_digest=stop_record["digest"],
    )
    harness.record_lifecycle_transition(observation, snapshot, lifecycle)
    persist_stop_record(tmp_path, stop_record)
    harness.write_workflow_checkpoint()
    _atomic_json(
        tmp_path / "checkpoint.json",
        {
            "schema": "deepreason-checkpoint-v1",
            "manifest_digest": manifest.sha256,
            "stop_digest": stop_record["digest"],
            "event_seq": harness._next_seq,
        },
    )

    with pytest.raises(ValueError, match="NOT_AUTHORIZED"):
        prepare_continuation(tmp_path, cycles=5, tokens=100)
