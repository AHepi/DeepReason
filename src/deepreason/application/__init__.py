"""Typed application boundary shared by operator-facing clients."""

from deepreason.application.bridge import (
    GROUNDED_BRIDGE_SERVICE,
    GROUNDED_BRIDGE_WORKERS,
    GroundedBridgeApplicationService,
    GroundedBridgeBuildIntentV1,
    GroundedBridgeBuildResultV1,
    GroundedBridgeClaimsIntentV1,
    GroundedBridgeInspectIntentV1,
    GroundedBridgeResultIntentV1,
    GroundedBridgeSnapshotV1,
    GroundedBridgeStartResultV1,
    GroundedBridgeStatusIntentV1,
    GroundedBridgeValidateIntentV1,
    GroundedBridgeViewResultV1,
)
from deepreason.application.conjecture import ConjectureApplicationBoundary
from deepreason.application.models import (
    CancelTextRunIntentV1,
    ContinueTextRunIntentV1,
    InspectTextRunIntentV1,
    OutstandingWorkItemProjectionV1,
    OutstandingWorkResultV1,
    OperatorCancellationIntentV1,
    RunBudgetIntentV1,
    RunCancellationAcceptedV1,
    RunProgressResultV1,
    RunResultV2,
    RunStartedV1,
    RunVerificationSummaryV2,
    StartTextRunIntentV1,
    TextRunTerminalResultV1,
    WatchTextRunIntentV1,
    run_result_exit_code,
)
from deepreason.application.intents import (
    budget_intent,
    continue_text_run_intent,
    start_text_run_intent,
)
from deepreason.application.scratch import (
    SCRATCH_QUERY_SERVICE,
    ScratchAttentionPreviewQueryV1,
    ScratchAttentionPreviewResultV1,
    ScratchMapQueryV1,
    ScratchMapResultV1,
    ScratchOpenPreviewQueryV1,
    ScratchOpenPreviewResultV1,
    ScratchQueryApplicationService,
    ScratchQueryResultV1,
    ScratchQueryV1,
    ScratchRecordDirectOpenQueryV1,
    ScratchRecordDirectOpenResultV1,
    ScratchRelatedQueryV1,
    ScratchRelatedResultV1,
    ScratchSearchQueryV1,
    ScratchSearchResultV1,
)
# The text-run service is reached LAZILY, and that is a constraint rather than
# a style choice: importing this package must not start the run engine.
# `application.conjecture` is a boundary a reduced-engine run legitimately
# uses, and importing it executes this module; an eager import here would drag
# the whole text-run stack into a run that never touches it. The public names
# are unchanged -- `from deepreason.application import TextRunApplicationService`
# still works -- and `mini/tests/test_isolation_fence.py` goes red if the
# eager import returns.
_LAZY_TEXT_RUNS = ("TEXT_RUN_SERVICE", "TEXT_RUN_WORKERS", "TextRunApplicationService")


def __getattr__(name: str):
    if name in _LAZY_TEXT_RUNS:
        from deepreason.application import text_runs

        return getattr(text_runs, name)
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")

__all__ = [
    "CancelTextRunIntentV1",
    "ConjectureApplicationBoundary",
    "ContinueTextRunIntentV1",
    "GROUNDED_BRIDGE_SERVICE",
    "GROUNDED_BRIDGE_WORKERS",
    "GroundedBridgeApplicationService",
    "GroundedBridgeBuildIntentV1",
    "GroundedBridgeBuildResultV1",
    "GroundedBridgeClaimsIntentV1",
    "GroundedBridgeInspectIntentV1",
    "GroundedBridgeResultIntentV1",
    "GroundedBridgeSnapshotV1",
    "GroundedBridgeStartResultV1",
    "GroundedBridgeStatusIntentV1",
    "GroundedBridgeValidateIntentV1",
    "GroundedBridgeViewResultV1",
    "InspectTextRunIntentV1",
    "OutstandingWorkItemProjectionV1",
    "OutstandingWorkResultV1",
    "OperatorCancellationIntentV1",
    "RunBudgetIntentV1",
    "RunCancellationAcceptedV1",
    "RunProgressResultV1",
    "RunResultV2",
    "RunStartedV1",
    "RunVerificationSummaryV2",
    "SCRATCH_QUERY_SERVICE",
    "ScratchAttentionPreviewQueryV1",
    "ScratchAttentionPreviewResultV1",
    "ScratchMapQueryV1",
    "ScratchMapResultV1",
    "ScratchOpenPreviewQueryV1",
    "ScratchOpenPreviewResultV1",
    "ScratchQueryApplicationService",
    "ScratchQueryResultV1",
    "ScratchQueryV1",
    "ScratchRecordDirectOpenQueryV1",
    "ScratchRecordDirectOpenResultV1",
    "ScratchRelatedQueryV1",
    "ScratchRelatedResultV1",
    "ScratchSearchQueryV1",
    "ScratchSearchResultV1",
    "StartTextRunIntentV1",
    "TEXT_RUN_SERVICE",
    "TEXT_RUN_WORKERS",
    "TextRunApplicationService",
    "TextRunTerminalResultV1",
    "WatchTextRunIntentV1",
    "budget_intent",
    "continue_text_run_intent",
    "run_result_exit_code",
    "start_text_run_intent",
]
