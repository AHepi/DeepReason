"""Pure construction and verification of v4 terminal lifecycle authority."""

from __future__ import annotations

from typing import Any, Literal

from deepreason.runtime.stop import (
    StopController,
    StopControllerStateV1,
    StopDecision,
    StopMetrics,
    StopPolicy,
    build_stop_record,
)
from deepreason.workflow.models import (
    OutstandingWorkItemV1,
    StopMetricsObservationV1,
    WorkflowLifecycleDecisionV1,
    WorkflowLifecycleSnapshotV1,
)


def outstanding_work_snapshot(
    workflow_state: Any,
    *,
    manifest_digest: str,
    controller_version: Literal[
        "legacy.scheduler.v1", "workflow.controller.v1"
    ],
    event_fence_seq: int,
) -> WorkflowLifecycleSnapshotV1:
    """Snapshot exact unfinished authority and unconsumed bound calls."""

    consumed_calls = {
        receipt.source_call_seq
        for receipt in workflow_state.proposal_receipts.values()
    }
    outstanding = []
    for work_id in workflow_state.outstanding_work_order_ids:
        work = workflow_state.work_orders[work_id]
        if work.manifest_digest != manifest_digest:
            raise ValueError("outstanding work belongs to another manifest")
        bound = tuple(
            sorted(
                seq
                for seq, call in workflow_state.calls_by_seq.items()
                if call.work_order_id == work_id
            )
        )
        outstanding.append(
            OutstandingWorkItemV1(
                work_order_id=work_id,
                recovery_status=workflow_state.recovery_status(work_id).value,
                bound_call_seqs=bound,
                unconsumed_bound_call_seqs=tuple(
                    seq for seq in bound if seq not in consumed_calls
                ),
            )
        )
    orphaned_calls = tuple(
        sorted(set(workflow_state.calls_by_seq) - consumed_calls)
    )
    represented = {
        seq
        for item in outstanding
        for seq in item.unconsumed_bound_call_seqs
    }
    if set(orphaned_calls) != represented:
        raise ValueError("unconsumed provider call is not represented as outstanding work")
    return WorkflowLifecycleSnapshotV1.create(
        manifest_digest=manifest_digest,
        controller_version=controller_version,
        process_digest=workflow_state.digest,
        event_fence_seq=event_fence_seq,
        last_control_seq=(
            max(workflow_state.event_seqs)
            if workflow_state.event_seqs
            else -1
        ),
        outstanding_work=tuple(outstanding),
    )


def build_stopped_lifecycle(
    workflow_state: Any,
    *,
    manifest_digest: str,
    controller_version: Literal[
        "legacy.scheduler.v1", "workflow.controller.v1"
    ],
    workflow_profile: Literal[
        "legacy.scheduler.v1", "conjecture.shadow.v1", "conjecture.active.v1"
    ],
    policy: StopPolicy,
    metrics: StopMetrics,
    deterministic_decision: StopDecision,
    controller_state_before: StopControllerStateV1,
    controller_state_after: StopControllerStateV1,
    stop_event_seq: int,
    stop_record_digest: str,
    model_signal_blob_refs: tuple[str, ...] = (),
) -> tuple[
    StopMetricsObservationV1,
    WorkflowLifecycleSnapshotV1,
    WorkflowLifecycleDecisionV1,
]:
    """Build one fail-closed STOPPED receipt from deterministic inputs."""

    policy = StopPolicy.model_validate(policy)
    metrics = StopMetrics.model_validate(metrics)
    deterministic_decision = StopDecision.model_validate(deterministic_decision)
    controller_state_before = StopControllerStateV1.model_validate(
        controller_state_before.model_dump(mode="python", by_alias=True)
    )
    controller_state_after = StopControllerStateV1.model_validate(
        controller_state_after.model_dump(mode="python", by_alias=True)
    )
    verifier = StopController(policy, state=controller_state_before)
    expected_decision = verifier.evaluate(metrics)
    if expected_decision != deterministic_decision:
        raise ValueError("lifecycle stop differs from deterministic StopController")
    if verifier.snapshot() != controller_state_after:
        raise ValueError("lifecycle controller state does not replay exactly")
    if not deterministic_decision.stop or deterministic_decision.reason is None:
        raise ValueError("only a deterministic terminal decision may emit STOPPED")
    expected_record = build_stop_record(
        reason=deterministic_decision.reason,
        policy=policy,
        metrics=metrics,
        event_seq=stop_event_seq,
    )
    if expected_record["digest"] != stop_record_digest:
        raise ValueError("lifecycle decision differs from its run-stop record")

    snapshot = outstanding_work_snapshot(
        workflow_state,
        manifest_digest=manifest_digest,
        controller_version=controller_version,
        event_fence_seq=stop_event_seq - 1,
    )
    if snapshot.outstanding_work or snapshot.unconsumed_bound_call_seqs:
        raise ValueError("STOPPED refuses unfinished workflow authority")
    observation = StopMetricsObservationV1.create(
        manifest_digest=manifest_digest,
        controller_version=controller_version,
        process_digest=workflow_state.digest,
        stop_policy=policy,
        metrics=metrics,
        model_signal_blob_refs=tuple(sorted(set(model_signal_blob_refs))),
        controller_state_before=controller_state_before,
        controller_state_after=controller_state_after,
    )
    decision = WorkflowLifecycleDecisionV1.create(
        manifest_digest=manifest_digest,
        controller_version=controller_version,
        workflow_profile=workflow_profile,
        previous_process_digest=workflow_state.digest,
        metrics_observation_ref=observation.id,
        checkpoint_ref=snapshot.id,
        deterministic_decision=deterministic_decision,
        stop_record_digest=stop_record_digest,
        stop_event_seq=stop_event_seq,
        next_process_digest=workflow_state.digest,
    )
    return observation, snapshot, decision


__all__ = ["build_stopped_lifecycle", "outstanding_work_snapshot"]
