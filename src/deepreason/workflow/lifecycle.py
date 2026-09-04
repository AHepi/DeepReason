"""Pure construction and verification of v4 terminal lifecycle authority."""

from __future__ import annotations

from typing import Any, Literal

from deepreason.runtime.budget import Limit
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
    WorkflowResumeDecisionV1,
)


# Owner decision 4a (2026-07-27): a budget-exhausted public run is a typed,
# quiescent stop and continues under a fresh explicit budget, exactly like a
# converged one.  Its closing clause -- "Failure terminals stay
# non-resumable" -- is SUPERSEDED by the operator's law of 2026-08-29:
# every terminal, clean or failed, must leave checkpoints sufficient for
# relaunch, and a stop that cannot assure continuability is itself a defect.
# What decides whether a given root may actually be resumed is the
# SECURITY-channel integrity gate at continue/amend time
# (`runtime/continuation.py`), never membership of this set.
RESUMABLE_STOP_REASONS = frozenset(
    {
        "converged",
        "budget_exhausted",
        "operational_failure",
        # Every seat stood down. Resumable is the whole point: the provider
        # comes back and the run picks up where it stopped.
        "provider_unavailable",
    }
)

# The bridge composes FROM a frozen terminal rather than extending it, which
# is a different question from whether the run may be resumed, and it must not
# move when resumption widens.  One frozenset answering both is how a
# resumption change would silently alter what may be composed out of a failed
# run; the sets are separate so that cannot happen by omission.
COMPOSABLE_STOP_REASONS = frozenset({"converged", "budget_exhausted"})


class UnfinishedWorkflowAuthorityError(ValueError):
    """STOPPED refused: the workflow still holds authority no stop may close.

    Typed so a caller can tell this refusal — which is correct, expected, and
    decided by the record — from the six other ``ValueError``s this module
    raises, which are bugs.  A handler that cannot tell them apart answers all
    seven with the same silence, and that is what published roots carrying a
    budget_exhausted terminal, a valid replay verdict and zero lifecycle
    decisions (soak case ``epoch3``, 11 outstanding work orders).

    Subclasses ``ValueError`` so every handler written before the type existed
    keeps catching it unchanged.
    """

    code = "STOPPED_REFUSES_UNFINISHED_WORKFLOW_AUTHORITY"

    def __init__(self, snapshot: WorkflowLifecycleSnapshotV1):
        self.outstanding_work_count = len(snapshot.outstanding_work)
        self.unconsumed_bound_call_count = len(snapshot.unconsumed_bound_call_seqs)
        super().__init__(
            "STOPPED refuses unfinished workflow authority: "
            f"{self.outstanding_work_count} outstanding work items, "
            f"{self.unconsumed_bound_call_count} unconsumed bound calls"
        )


def outstanding_work_snapshot(
    workflow_state: Any,
    *,
    manifest_digest: str,
    controller_version: Literal[
        "legacy.scheduler.v1",
        "workflow.controller.v1",
        "workflow.controller.v2",
        "workflow.controller.v3",
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
        work = workflow_state.work_orders.get(work_id)
        if work is not None:
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
            continue

        transaction = workflow_state.transaction_work.get(work_id)
        if transaction is None:
            raise ValueError("outstanding work has no replayed authority")
        if transaction.preparation.manifest_digest != manifest_digest:
            raise ValueError("outstanding work belongs to another manifest")
        bound = tuple(
            sorted(
                seq
                for seq, call in workflow_state.transaction_calls_by_seq.items()
                if call.work_order_id == work_id
            )
        )
        if not transaction.issued:
            recovery_status = "prepared"
        elif not transaction.provider_attempts:
            recovery_status = "issued"
        elif not transaction.admissions:
            recovery_status = "provider_result_received"
        else:
            recovery_status = "semantic_admission_received"
        outstanding.append(
            OutstandingWorkItemV1(
                work_order_id=work_id,
                recovery_status=recovery_status,
                bound_call_seqs=bound,
                # A transactional provider call and ProviderAttemptV1 share
                # one atomic Control append.  Such a call is already consumed
                # by replay even when semantic admission is still pending.
                unconsumed_bound_call_seqs=(),
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


# Neither reason is reached through StopController.evaluate: the cycle loop and
# token meter decide exhaustion, and an unhandled error decides operational
# failure.  A receipt for either therefore has no controller evaluation to
# replay and must declare that no controller authority was consumed.
_RUNTIME_DECIDED_STOP_REASONS = frozenset(
    {"budget_exhausted", "operational_failure", "provider_unavailable"}
)


def _is_runtime_decided(decision: StopDecision) -> bool:
    """True for the stops the runtime, not the controller, decides."""

    return (
        decision.stop
        and decision.reason in _RUNTIME_DECIDED_STOP_REASONS
        and decision.escape_action is None
    )


def build_stopped_lifecycle(
    workflow_state: Any,
    *,
    manifest_digest: str,
    controller_version: Literal[
        "legacy.scheduler.v1",
        "workflow.controller.v1",
        "workflow.controller.v2",
        "workflow.controller.v3",
    ],
    workflow_profile: Literal[
        "legacy.scheduler.v1",
        "conjecture.shadow.v1",
        "conjecture.active.v1",
        "inquiry.active.v1",
        "inquiry.active.v2",
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
    if not deterministic_decision.stop or deterministic_decision.reason is None:
        raise ValueError("only a deterministic terminal decision may emit STOPPED")
    if _is_runtime_decided(deterministic_decision):
        # The receipt declares that no controller authority was consumed
        # (identical before and after states); the stop-record digest binding
        # and the unread-provider-authority check below carry the resumption
        # safety properties instead.
        if controller_state_before != controller_state_after:
            raise ValueError(
                "exhaustion STOPPED requires unchanged controller state"
            )
    else:
        verifier = StopController(policy, state=controller_state_before)
        expected_decision = verifier.evaluate(metrics)
        if expected_decision != deterministic_decision:
            raise ValueError("lifecycle stop differs from deterministic StopController")
        if verifier.snapshot() != controller_state_after:
            raise ValueError("lifecycle controller state does not replay exactly")
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
    # ONLY unread provider authority may veto the receipt.  An unconsumed bound
    # call is a provider result nobody has read, so closing a stop over one
    # forces resumption to either re-issue the call (two calls recorded for one
    # authority) or drop a result the record already holds.  Work that is
    # merely OUTSTANDING carries no such result: it is recorded in the snapshot
    # above and re-entered by `Scheduler._recover_workflow_prefixes`, which
    # runs before the first resumed cycle and raises if it cannot finish.
    # Refusing on it instead withheld the receipt for a condition whose remedy
    # is the operation the withheld receipt blocks.
    if snapshot.unconsumed_bound_call_seqs:
        raise UnfinishedWorkflowAuthorityError(snapshot)
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


def build_resumed_lifecycle(
    workflow_state: Any,
    *,
    manifest_digest: str,
    controller_version: Literal[
        "workflow.controller.v1",
        "workflow.controller.v2",
        "workflow.controller.v3",
    ],
    workflow_profile: Literal[
        "conjecture.shadow.v1",
        "conjecture.active.v1",
        "inquiry.active.v1",
        "inquiry.active.v2",
    ],
    workflow_checkpoint_digest: str,
    run_checkpoint_digest: str,
    continuation_seq: int,
    requested_cycles: Limit,
    requested_tokens: Limit,
    resume_event_seq: int,
    validated_post_terminal_drift: bool = False,
) -> tuple[WorkflowLifecycleSnapshotV1, WorkflowResumeDecisionV1]:
    """Authorize one real RESUMED transition from a quiescent typed stop."""

    terminal = workflow_state.terminal_lifecycle_decision
    terminal_snapshot = workflow_state.terminal_lifecycle_snapshot
    terminal_observation = workflow_state.terminal_stop_observation
    if terminal is None or terminal_snapshot is None or terminal_observation is None:
        raise ValueError("continuation requires one active typed STOPPED decision")
    if terminal.deterministic_decision.reason not in RESUMABLE_STOP_REASONS:
        raise ValueError("terminal stop reason does not authorize continuation")
    if (
        terminal.manifest_digest != manifest_digest
        or terminal.controller_version != controller_version
        or terminal.workflow_profile != workflow_profile
    ):
        raise ValueError("terminal lifecycle belongs to another controller authority")
    if (
        terminal_snapshot.process_digest != workflow_state.digest
        or terminal.next_process_digest != workflow_state.digest
    ) and not validated_post_terminal_drift:
        # A bridged run's workflow state legitimately drifts past its stop
        # checkpoint (commitment-bound bridge transactions). The caller
        # asserts that drift was validated by current terminal authority;
        # the resume decision still binds to the CURRENT replayed digest,
        # and the fresh outstanding-work snapshot below still refuses any
        # unfinished authority.
        raise ValueError("terminal process digest differs from current replay")
    if terminal_snapshot.unconsumed_bound_call_seqs:
        raise ValueError("terminal checkpoint contains unfinished provider work")
    if continuation_seq != len(workflow_state.resume_decisions):
        raise ValueError("continuation sequence differs from replayed resume history")
    requested_cycles = Limit.model_validate(requested_cycles)
    requested_tokens = Limit.model_validate(requested_tokens)
    snapshot = outstanding_work_snapshot(
        workflow_state,
        manifest_digest=manifest_digest,
        controller_version=controller_version,
        event_fence_seq=resume_event_seq - 1,
    )
    # Symmetric with build_stopped_lifecycle: a stop that may be TAKEN over
    # outstanding work must be RESUMABLE over it, or the receipt is granted and
    # refused one layer later.
    if snapshot.unconsumed_bound_call_seqs:
        raise ValueError("RESUMED refuses unfinished workflow authority")
    decision = WorkflowResumeDecisionV1.create(
        manifest_digest=manifest_digest,
        controller_version=controller_version,
        workflow_profile=workflow_profile,
        prior_terminal_decision_ref=terminal.id,
        prior_metrics_observation_ref=terminal_observation.id,
        prior_process_digest=terminal.next_process_digest,
        prior_stop_digest=terminal.stop_record_digest,
        prior_checkpoint_ref=terminal_snapshot.id,
        workflow_checkpoint_digest=workflow_checkpoint_digest,
        run_checkpoint_digest=run_checkpoint_digest,
        resume_snapshot_ref=snapshot.id,
        controller_state=terminal_observation.controller_state_after,
        continuation_seq=continuation_seq,
        requested_cycles=requested_cycles,
        requested_tokens=requested_tokens,
        previous_process_digest=workflow_state.digest,
        resume_event_seq=resume_event_seq,
        next_process_digest=workflow_state.digest,
    )
    return snapshot, decision


__all__ = [
    "COMPOSABLE_STOP_REASONS",
    "RESUMABLE_STOP_REASONS",
    "build_resumed_lifecycle",
    "build_stopped_lifecycle",
    "outstanding_work_snapshot",
]
