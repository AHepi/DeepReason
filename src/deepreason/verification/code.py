"""End-to-end mechanical verification for a localized code patch."""

from __future__ import annotations

import tempfile
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, ConfigDict

from deepreason.workloads.code import (
    AppliedCodeArtifact,
    CodePatch,
    CodeWorkloadSpec,
    WorkspaceSnapshot,
    apply_code_patch,
)
from deepreason.verification.runner import CheckResult, TrustedCheckRunner


class CodeVerificationResult(BaseModel):
    """Mechanical trace only; consumers register ordinary verdicts separately."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    artifact: AppliedCodeArtifact | None
    verdict: Literal["pass", "fail", "overrun"]
    checks: tuple[CheckResult, ...]
    operational_error: str | None = None


def verify_code_patch(
    workload: CodeWorkloadSpec,
    snapshot: WorkspaceSnapshot,
    patch: CodePatch,
    *,
    runner: TrustedCheckRunner | None = None,
    blobs=None,
) -> CodeVerificationResult:
    """Apply in a temporary tree, then execute only predeclared checks.

    Patch-application errors intentionally propagate as operational errors.
    They must be repaired at the transport/schema layer rather than converted
    into a ``fail`` verdict.
    """

    runner = runner or TrustedCheckRunner()
    with tempfile.TemporaryDirectory(prefix="deepreason-code-") as temporary:
        workspace = Path(temporary) / "workspace"
        artifact = apply_code_patch(
            workload.workspace,
            snapshot,
            patch,
            workspace,
            source_blobs=blobs,
            output_blobs=blobs,
        )
        results: list[CheckResult] = []
        if not workload.checks:
            return CodeVerificationResult(
                artifact=artifact,
                verdict="overrun",
                checks=(),
                operational_error="no trusted checks declared",
            )
        for check in workload.checks:
            result = runner.run(check, workspace, blobs)
            results.append(result)
            # The criticism order is fixed by the workload declaration.  A
            # deterministic failure settles this battery; an overrun cannot.
            if result.verdict == "fail":
                break
        verdict = (
            "fail"
            if any(result.verdict == "fail" for result in results)
            else "overrun"
            if any(result.verdict == "overrun" for result in results)
            else "pass"
        )
        return CodeVerificationResult(
            artifact=artifact,
            verdict=verdict,
            checks=tuple(results),
        )
