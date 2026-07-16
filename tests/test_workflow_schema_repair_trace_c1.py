"""Durable C1 schema-repair requests bracket the next provider dispatch."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from deepreason.harness import Harness
from deepreason.llm.adapter import LLMAdapter
from deepreason.llm.budget import TokenMeter
from deepreason.llm.endpoints import MockEndpoint
from deepreason.llm.firewall import leases_from_manifest
from deepreason.ontology import Problem, ProblemProvenance
from deepreason.run_manifest import bind_run_manifest
from deepreason.scheduler.scheduler import Scheduler
from deepreason.workflow.models import TransitionKind
from deepreason.workflow.replay import WorkflowRecoveryStatus

from tests.test_workflow_shadow_c0 import _candidate, _config, _manifest


@dataclass(frozen=True)
class _RepairRun:
    harness: Harness
    scheduler: Scheduler
    dispatch_snapshots: tuple[tuple[TransitionKind, ...], ...]


def _control_decisions(harness: Harness):
    decisions = []
    for event in harness.log.read():
        if event.control is None:
            continue
        _schema, decision = harness.objects.get(
            event.control.decision_ref,
            schema="workflow-transition-decision",
        )
        decisions.append((event, decision))
    return decisions


def _run_repaired_conjecture(root: Path, *, invalid_attempts: int) -> _RepairRun:
    config = _config(retry_max=invalid_attempts)
    manifest = _manifest(config, "shadow")
    bind_run_manifest(manifest, root)
    harness = Harness(root)
    harness.register_problem(
        Problem(
            id="pi-workflow-repair-trace-c1",
            description="Exercise durable repair authority before retry dispatch.",
            provenance=ProblemProvenance.model_validate(
                {"trigger": "seed", "from": []}
            ),
        )
    )

    responses = iter(("{not-valid-json",) * invalid_attempts + (_candidate(),))
    snapshots: list[tuple[TransitionKind, ...]] = []

    def complete(_prompt: str) -> str:
        # MockEndpoint invokes this at the provider boundary. Capturing the
        # durable log here proves each repair request precedes the next call,
        # instead of merely being summarized after the final response.
        snapshots.append(
            tuple(
                decision.transition_kind
                for _event, decision in _control_decisions(harness)
            )
        )
        return next(responses)

    endpoint = MockEndpoint(
        complete,
        name=manifest.roles["conjecturer"][0].base_url,
        model=manifest.roles["conjecturer"][0].model_id,
        max_tokens=256,
    )
    meter = TokenMeter(budget=100_000)
    adapter = LLMAdapter(
        {"conjecturer": endpoint},
        harness.blobs,
        meter=meter,
        retry_max=invalid_attempts,
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
    scheduler.run(1)
    return _RepairRun(harness, scheduler, tuple(snapshots))


def _work_trace(run: _RepairRun):
    comparisons = [
        item for item in run.scheduler.workflow_shadow_observations if item.matched
    ]
    assert len(comparisons) == 1
    comparison = comparisons[0]
    assert comparison.matched
    work_order_id = comparison.work_order_id
    assert work_order_id is not None
    decisions = [
        (event, decision)
        for event, decision in _control_decisions(run.harness)
        if decision.work_order_id == work_order_id
    ]
    provider_events = [
        event
        for event in run.harness.log.read()
        if event.llm is not None and event.llm.work_order_id == work_order_id
    ]
    assert len(provider_events) == 1
    return work_order_id, decisions, provider_events[0]


def test_one_schema_repair_is_durable_before_retry_and_final_proposal(tmp_path):
    run = _run_repaired_conjecture(tmp_path / "one-repair", invalid_attempts=1)
    work_order_id, decisions, provider_event = _work_trace(run)
    by_kind = {
        decision.transition_kind: event
        for event, decision in decisions
    }
    repairs = [
        (event, decision)
        for event, decision in decisions
        if decision.transition_kind == TransitionKind.REPAIR_REQUESTED
    ]

    assert len(run.dispatch_snapshots) == 2
    assert TransitionKind.WORK_ISSUED in run.dispatch_snapshots[0]
    assert TransitionKind.REPAIR_REQUESTED not in run.dispatch_snapshots[0]
    assert run.dispatch_snapshots[1].count(
        TransitionKind.REPAIR_REQUESTED
    ) == 1
    assert len(repairs) == 1
    assert (
        by_kind[TransitionKind.WORK_ISSUED].seq
        < repairs[0][0].seq
        < provider_event.seq
        < by_kind[TransitionKind.PROPOSAL_RECEIVED].seq
    )
    assert run.harness.workflow_state.recovery_status(
        work_order_id
    ) == WorkflowRecoveryStatus.FINISHED


def test_two_schema_repairs_are_distinct_and_each_precedes_next_dispatch(tmp_path):
    run = _run_repaired_conjecture(tmp_path / "two-repairs", invalid_attempts=2)
    _work_order_id, decisions, provider_event = _work_trace(run)
    repairs = [
        (event, decision)
        for event, decision in decisions
        if decision.transition_kind == TransitionKind.REPAIR_REQUESTED
    ]

    assert len(run.dispatch_snapshots) == 3
    assert run.dispatch_snapshots[1].count(
        TransitionKind.REPAIR_REQUESTED
    ) == 1
    assert run.dispatch_snapshots[2].count(
        TransitionKind.REPAIR_REQUESTED
    ) == 2
    assert len(repairs) == 2
    assert repairs[0][1].id != repairs[1][1].id
    assert repairs[0][1].trigger_ref != repairs[1][1].trigger_ref
    assert repairs[0][0].seq < repairs[1][0].seq < provider_event.seq
    proposal_event = next(
        event
        for event, decision in decisions
        if decision.transition_kind == TransitionKind.PROPOSAL_RECEIVED
    )
    assert provider_event.seq < proposal_event.seq


def test_replay_cut_after_repair_request_is_repair_pending(tmp_path):
    run = _run_repaired_conjecture(tmp_path / "repair-prefix", invalid_attempts=1)
    work_order_id, decisions, _provider_event = _work_trace(run)
    repair_event = next(
        event
        for event, decision in decisions
        if decision.transition_kind == TransitionKind.REPAIR_REQUESTED
    )

    prefix = Harness.at(run.harness.root, repair_event.seq)
    assert prefix.workflow_state.recovery_status(
        work_order_id
    ) == WorkflowRecoveryStatus.REPAIR_PENDING
    assert prefix.workflow_state.outstanding_work_order_ids == (work_order_id,)
    assert prefix._next_seq == repair_event.seq + 1
    assert tuple(prefix.workflow_state.calls_by_seq) == ()
