"""Deterministic, harness-owned workflows.

Workflow modules are process machinery only.  They may decide which bounded
operation runs next, but they never adjudicate artifacts or grant a generated
object any status privilege.  The ordinary DeepReason commitments, critics,
guards and event log remain the normative path.
"""

from deepreason.workflows.manifest_compiler import (
    CompactArtDirection,
    CompactComponentContract,
    CompactDesignOutline,
    CompactOutlineComponent,
    ManifestCompileResult,
    ManifestCompiler,
    ManifestDiagnostic,
    compile_compact_manifest,
)
from deepreason.workflows.website import (
    NextAction,
    StageOutcome,
    StageResult,
    TerminalSummary,
    WebsiteStage,
    WebsiteStateMachine,
    WebsiteWorkflow,
    run_website_workflow,
)

__all__ = [
    "CompactArtDirection",
    "CompactComponentContract",
    "CompactDesignOutline",
    "CompactOutlineComponent",
    "ManifestCompileResult",
    "ManifestCompiler",
    "ManifestDiagnostic",
    "NextAction",
    "StageOutcome",
    "StageResult",
    "TerminalSummary",
    "WebsiteStage",
    "WebsiteStateMachine",
    "WebsiteWorkflow",
    "compile_compact_manifest",
    "run_website_workflow",
]
