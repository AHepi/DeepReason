from __future__ import annotations

import json
from types import SimpleNamespace

import pytest

from deepreason.config import Config
from deepreason.harness import Harness
from deepreason.llm.adapter import LLMAdapter
from deepreason.ontology import Rule
from deepreason.runtime.stop import (
    StopController,
    StopMetrics,
    StopPolicy,
    build_stop_record,
)
from deepreason.scheduler.scheduler import Scheduler
from deepreason.workflow.lifecycle import (
    build_stopped_lifecycle,
    outstanding_work_snapshot,
)
from deepreason.workflow.replay import WorkflowRecoveryStatus


def _manifest(version: int):
    return SimpleNamespace(
        schema_version=version,
        sha256="a" * 64,
        control_plane_policy=(
            SimpleNamespace(
                mode="shadow",
                controller_version="workflow.controller.v1",
                workflow_profile="conjecture.shadow.v1",
            )
            if version == 4
            else None
        ),
    )


def _quiet_scheduler(tmp_path, *, version: int, policy: StopPolicy) -> Scheduler:
    harness = Harness(tmp_path)
    scheduler = Scheduler(
        harness,
        LLMAdapter({}, harness.blobs),
        Config(N_SCHOOLS=0),
        stop_controller=StopController(policy),
    )
    scheduler.run_manifest = _manifest(version)

    def quiet_step():
        scheduler._cycles += 1

    scheduler.step = quiet_step
    return scheduler


def test_stop_controller_state_rehydrates_exactly():
    policy = StopPolicy(min_cycles=99, window=3, stable_windows=99)
    original = StopController(policy)
    assert not original.evaluate(StopMetrics(cycle=1)).stop
    state = original.snapshot()

    restored = StopController(policy, state=state)
    expected = original.evaluate(StopMetrics(cycle=2))
    actual = restored.evaluate(StopMetrics(cycle=2))

    assert actual == expected
    assert restored.snapshot() == original.snapshot()
    with pytest.raises(ValueError, match="another policy"):
        StopController(StopPolicy(enabled=False), state=state)


def test_v4_stop_is_a_replayable_control_event_bound_to_run_stop(tmp_path):
    scheduler = _quiet_scheduler(
        tmp_path,
        version=4,
        policy=StopPolicy(min_cycles=0, window=1, stable_windows=1),
    )
    report = scheduler.run(2)

    assert report["stop_reason"] == "converged"
    events = list(scheduler.harness.log.read())
    controls = [event for event in events if event.rule == Rule.CONTROL]
    assert len(controls) == 1
    assert not any(controls[0].state_diff.model_dump(mode="json").values())
    assert [scheduler.harness.objects.get(ref)[0] for ref in controls[0].outputs] == [
        "workflow-stop-metrics-observation",
        "workflow-lifecycle-snapshot",
        "workflow-lifecycle-decision",
    ]

    replayed = Harness(tmp_path).workflow_state
    stop = json.loads((tmp_path / "run-stop.json").read_text())
    assert replayed.terminal_stop_digest == stop["digest"]
    assert replayed.terminal_checkpoint_digest is not None
    assert replayed.terminal_process_digest == replayed.digest
    assert replayed.terminal_controller_version == "workflow.controller.v1"
    assert replayed.terminal_lifecycle_snapshot.outstanding_work == ()
    assert replayed.terminal_stop_observation.controller_state_after.window[-1].cycle == 1


def test_v1_to_v3_stop_path_does_not_emit_new_control_bytes(tmp_path):
    scheduler = _quiet_scheduler(
        tmp_path,
        version=3,
        policy=StopPolicy(min_cycles=0, window=1, stable_windows=1),
    )
    scheduler.run(2)

    events = list(scheduler.harness.log.read())
    assert [event.rule for event in events] == [Rule.MEASURE]
    stop = json.loads((tmp_path / "run-stop.json").read_text())
    assert stop["schema"] == "deepreason-run-stop-v1"
    assert stop["event_seq"] == 0


def test_model_stuck_signal_cannot_directly_emit_stopped(tmp_path):
    scheduler = _quiet_scheduler(
        tmp_path,
        version=4,
        policy=StopPolicy(
            min_cycles=100,
            window=2,
            stable_windows=99,
            stuck_signal_window=2,
            escape_attempts=0,
        ),
    )
    quiet_step = scheduler.step

    def injected_step():
        scheduler.diagnostics.append({"search_signal": "stuck"})
        quiet_step()

    scheduler.step = injected_step
    scheduler.run(3)

    assert scheduler.last_stop_decision is not None
    assert not scheduler.last_stop_decision.stop
    assert not (tmp_path / "run-stop.json").exists()
    assert not any(event.rule == Rule.CONTROL for event in scheduler.harness.log.read())


class _OutstandingReplay:
    def __init__(self):
        self.work_id = "sha256:" + "1" * 64
        self.outstanding_work_order_ids = (self.work_id,)
        self.work_orders = {
            self.work_id: SimpleNamespace(manifest_digest="a" * 64)
        }
        self.calls_by_seq = {7: SimpleNamespace(work_order_id=self.work_id)}
        self.proposal_receipts = {}
        self.event_seqs = [3]
        self.digest = "sha256:" + "2" * 64

    def recovery_status(self, _work_id):
        return WorkflowRecoveryStatus.ISSUED


def test_terminal_builder_snapshots_then_refuses_unfinished_provider_work():
    replay = _OutstandingReplay()
    snapshot = outstanding_work_snapshot(
        replay,
        manifest_digest="a" * 64,
        controller_version="workflow.controller.v1",
        event_fence_seq=4,
    )
    assert snapshot.outstanding_work[0].unconsumed_bound_call_seqs == (7,)

    policy = StopPolicy(min_cycles=0, window=1, stable_windows=1)
    controller = StopController(policy)
    before = controller.snapshot()
    metrics = StopMetrics(cycle=1)
    decision = controller.evaluate(metrics)
    stop = build_stop_record(
        reason=decision.reason,
        policy=policy,
        metrics=metrics,
        event_seq=5,
    )
    with pytest.raises(ValueError, match="unfinished workflow authority"):
        build_stopped_lifecycle(
            replay,
            manifest_digest="a" * 64,
            controller_version="workflow.controller.v1",
            workflow_profile="conjecture.active.v1",
            policy=policy,
            metrics=metrics,
            deterministic_decision=decision,
            controller_state_before=before,
            controller_state_after=controller.snapshot(),
            stop_event_seq=5,
            stop_record_digest=stop["digest"],
        )
