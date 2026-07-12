"""Runner-owned execution of trusted code-workload checks.

Candidate output never reaches ``argv``, ``cwd`` or ``env``.  Commands are
copied verbatim from :class:`~deepreason.workloads.code.CheckSpec` and executed
without a shell.  Wall-clock and OS limits are containment only: a containment
abort returns ``overrun`` and therefore supplies no fail warrant.
"""

from __future__ import annotations

import os
import signal
import subprocess
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from deepreason.canonical import canonical_json, sha256_hex
from deepreason.workloads.code import CheckSpec

_OUTPUT_LIMIT = 8 * 1024 * 1024
_MEMORY_LIMIT = 1024 * 1024 * 1024


class CheckResult(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    check_id: str
    runner: str
    verdict: Literal["pass", "fail", "overrun"]
    command_sha256: str
    expected_exit: int
    returncode: int | None = None
    stdout_ref: str | None = None
    stderr_ref: str | None = None
    stdout_sha256: str
    stderr_sha256: str
    detail: dict = Field(default_factory=dict)


def _minimal_environment(workspace: Path, declared: dict[str, str]) -> dict[str, str]:
    environment = {
        "HOME": str(workspace),
        "LC_ALL": "C.UTF-8",
        "PATH": os.environ.get("PATH", os.defpath),
        "PYTHONDONTWRITEBYTECODE": "1",
        "PYTHONHASHSEED": "0",
        "PYTHONNOUSERSITE": "1",
    }
    environment.update(declared)
    return environment


def _limit_child() -> None:
    """Best-effort emergency containment, never part of pass/fail semantics."""

    try:
        import resource

        resource.setrlimit(resource.RLIMIT_AS, (_MEMORY_LIMIT, _MEMORY_LIMIT))
        resource.setrlimit(resource.RLIMIT_CPU, (30, 31))
    except (ImportError, OSError, ValueError):
        pass


def _kill(process: subprocess.Popen[bytes]) -> None:
    try:
        if os.name == "posix":
            os.killpg(process.pid, signal.SIGKILL)
        else:
            process.kill()
    except ProcessLookupError:
        pass


class TrustedCheckRunner:
    def __init__(self, *, containment_timeout_s: int = 60, output_limit: int = _OUTPUT_LIMIT) -> None:
        if containment_timeout_s <= 0 or output_limit <= 0:
            raise ValueError("runner containment limits must be finite and positive")
        self.containment_timeout_s = containment_timeout_s
        self.output_limit = output_limit

    def run(self, check: CheckSpec, workspace: str | Path, blobs=None) -> CheckResult:
        workspace = Path(workspace).resolve()
        cwd = (workspace / check.cwd).resolve()
        try:
            cwd.relative_to(workspace)
        except ValueError as error:
            raise ValueError("trusted check cwd escapes candidate workspace") from error
        if not cwd.is_dir():
            raise ValueError(f"trusted check cwd is not a directory: {check.cwd}")
        argv = list(check.argv)
        command_sha = sha256_hex(
            canonical_json(
                {
                    "id": check.id,
                    "runner": check.runner,
                    "argv": argv,
                    "cwd": check.cwd,
                    "env": check.env,
                    "expected_exit": check.expected_exit,
                    "step_or_item_limit": check.step_or_item_limit,
                }
            )
        )
        try:
            process = subprocess.Popen(  # noqa: S603 - argv is trusted workload input
                argv,
                cwd=cwd,
                env=_minimal_environment(workspace, check.env),
                stdin=subprocess.DEVNULL,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                close_fds=True,
                start_new_session=(os.name == "posix"),
                preexec_fn=_limit_child if os.name == "posix" else None,
            )
        except OSError as error:
            return self._result(
                check,
                command_sha,
                "overrun",
                None,
                b"",
                str(error).encode(),
                blobs,
                {"unavailable": type(error).__name__},
            )
        try:
            stdout, stderr = process.communicate(timeout=self.containment_timeout_s)
        except subprocess.TimeoutExpired:
            _kill(process)
            stdout, stderr = process.communicate()
            return self._result(
                check,
                command_sha,
                "overrun",
                process.returncode,
                stdout,
                stderr,
                blobs,
                {"sandbox_abort": "wall-clock containment timeout"},
            )
        if len(stdout) + len(stderr) > self.output_limit:
            return self._result(
                check,
                command_sha,
                "overrun",
                process.returncode,
                stdout[: self.output_limit],
                stderr[: self.output_limit],
                blobs,
                {"sandbox_abort": "output containment limit"},
            )
        if process.returncode is not None and process.returncode < 0:
            return self._result(
                check,
                command_sha,
                "overrun",
                process.returncode,
                stdout,
                stderr,
                blobs,
                {"sandbox_abort": f"worker terminated by signal {-process.returncode}"},
            )
        verdict = "pass" if process.returncode == check.expected_exit else "fail"
        return self._result(
            check,
            command_sha,
            verdict,
            process.returncode,
            stdout,
            stderr,
            blobs,
            {},
        )

    @staticmethod
    def _result(
        check: CheckSpec,
        command_sha: str,
        verdict: Literal["pass", "fail", "overrun"],
        returncode: int | None,
        stdout: bytes,
        stderr: bytes,
        blobs,
        detail: dict,
    ) -> CheckResult:
        stdout_ref = blobs.put(stdout) if blobs is not None else None
        stderr_ref = blobs.put(stderr) if blobs is not None else None
        return CheckResult(
            check_id=check.id,
            runner=check.runner,
            verdict=verdict,
            command_sha256=command_sha,
            expected_exit=check.expected_exit,
            returncode=returncode,
            stdout_ref=stdout_ref,
            stderr_ref=stderr_ref,
            stdout_sha256=sha256_hex(stdout),
            stderr_sha256=sha256_hex(stderr),
            detail=detail,
        )


class VerifierOperationalError(RuntimeError):
    """No verifier verdict exists; callers must not create a fail warrant."""


class VerificationRunner:
    def __init__(self, registry) -> None:
        self.registry = registry

    def verify(self, request, blobs=None):
        from deepreason.verification.registry import VerifierRegistryError

        try:
            return self.registry.verify(request.backend, request, blobs)
        except VerifierRegistryError as error:
            raise VerifierOperationalError(str(error)) from error


VerifierRunner = VerificationRunner
