"""Bounded fixed records for bridge worker operation state.

These records describe transport/process execution only.  They are never
evidence, never an epistemic resolution, and never enter bridge replay state.
Canonical successful and workflow-failure terminals remain owned by
``bridge-result.json`` plus the append-only bridge event log.
"""

from __future__ import annotations

import os
import re
import stat
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, ValidationError, model_validator

from deepreason.runtime.progress import _atomic_json


BRIDGE_OPERATION_STATUS_NAME = "bridge-operation-status.json"
BRIDGE_OPERATION_RESULT_NAME = "bridge-operation-result.json"
_MAX_RECORD_BYTES = 4_096


class BridgeOperationStatusV1(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, hide_input_in_errors=True)

    schema_: Literal["deepreason-bridge-operation-status-v1"] = Field(
        "deepreason-bridge-operation-status-v1", alias="schema"
    )
    state: Literal["running", "failed"]
    manifest_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    process_status: Literal["failure"] | None = None
    error_code: Literal["BRIDGE_WORKER_FAILED"] | None = None
    error_type: str | None = Field(
        default=None,
        min_length=1,
        max_length=128,
        pattern=r"^[A-Za-z_][A-Za-z0-9_.]{0,127}$",
    )
    non_epistemic: Literal[True] = True

    @model_validator(mode="after")
    def _shape(self):
        failed = self.state == "failed"
        if failed != (
            self.process_status == "failure"
            and self.error_code is not None
            and self.error_type is not None
        ):
            raise ValueError("failed operation status requires bounded diagnostics")
        if not failed and self.process_status is not None:
            raise ValueError("running operation status cannot be terminal")
        return self


class BridgeOperationResultV1(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, hide_input_in_errors=True)

    schema_: Literal["deepreason-bridge-operation-result-v1"] = Field(
        "deepreason-bridge-operation-result-v1", alias="schema"
    )
    process_status: Literal["failure"] = "failure"
    manifest_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    error_code: Literal["BRIDGE_WORKER_FAILED"] = "BRIDGE_WORKER_FAILED"
    error_type: str = Field(
        min_length=1,
        max_length=128,
        pattern=r"^[A-Za-z_][A-Za-z0-9_.]{0,127}$",
    )
    non_epistemic: Literal[True] = True


def _path(root: Path | str, name: str) -> Path:
    return Path(root) / name


def _ensure_write_target(path: Path) -> None:
    try:
        observed = path.lstat()
    except FileNotFoundError:
        return
    if not stat.S_ISREG(observed.st_mode) or path.is_symlink():
        raise ValueError("BRIDGE_OPERATION_RECORD_INVALID")


def _safe_remove(path: Path) -> None:
    try:
        observed = path.lstat()
    except FileNotFoundError:
        return
    if not stat.S_ISREG(observed.st_mode) or path.is_symlink():
        raise ValueError("BRIDGE_OPERATION_RECORD_INVALID")
    path.unlink()


def _safe_read(path: Path, model):
    try:
        observed = path.lstat()
    except FileNotFoundError:
        return None
    if (
        not stat.S_ISREG(observed.st_mode)
        or path.is_symlink()
        or not 2 <= observed.st_size <= _MAX_RECORD_BYTES
    ):
        raise ValueError("BRIDGE_OPERATION_RECORD_INVALID")
    flags = os.O_RDONLY | getattr(os, "O_CLOEXEC", 0) | getattr(os, "O_NOFOLLOW", 0)
    try:
        descriptor = os.open(path, flags)
        with os.fdopen(descriptor, "rb") as stream:
            opened = os.fstat(stream.fileno())
            if not stat.S_ISREG(opened.st_mode) or opened.st_size != observed.st_size:
                raise ValueError("BRIDGE_OPERATION_RECORD_INVALID")
            raw = stream.read(_MAX_RECORD_BYTES + 1)
        current = path.lstat()
        if (
            not stat.S_ISREG(current.st_mode)
            or current.st_size != opened.st_size
            or (
                opened.st_ino
                and current.st_ino
                and (opened.st_dev, opened.st_ino)
                != (current.st_dev, current.st_ino)
            )
        ):
            raise ValueError("BRIDGE_OPERATION_RECORD_INVALID")
        return model.model_validate_json(raw)
    except (OSError, ValidationError, ValueError) as error:
        if str(error) == "BRIDGE_OPERATION_RECORD_INVALID":
            raise
        raise ValueError("BRIDGE_OPERATION_RECORD_INVALID") from error


def write_running(root: Path | str, manifest_sha256: str) -> None:
    status_path = _path(root, BRIDGE_OPERATION_STATUS_NAME)
    result_path = _path(root, BRIDGE_OPERATION_RESULT_NAME)
    _ensure_write_target(status_path)
    _ensure_write_target(result_path)
    status = BridgeOperationStatusV1(
        state="running", manifest_sha256=manifest_sha256
    )
    _atomic_json(
        status_path,
        status.model_dump(mode="json", by_alias=True, exclude_none=True),
    )
    # A RUNNING status makes any prior failure result stale; remove it only
    # after the new status is durably visible.
    _safe_remove(result_path)


def write_failure(
    root: Path | str, manifest_sha256: str, error_type: str
) -> BridgeOperationResultV1:
    candidate = str(error_type)[:128]
    bounded_type = (
        candidate
        if re.fullmatch(r"[A-Za-z_][A-Za-z0-9_.]{0,127}", candidate)
        else "WorkerFailure"
    )
    status_path = _path(root, BRIDGE_OPERATION_STATUS_NAME)
    result_path = _path(root, BRIDGE_OPERATION_RESULT_NAME)
    _ensure_write_target(status_path)
    _ensure_write_target(result_path)
    result = BridgeOperationResultV1(
        manifest_sha256=manifest_sha256,
        error_type=bounded_type,
    )
    status = BridgeOperationStatusV1(
        state="failed",
        manifest_sha256=manifest_sha256,
        process_status="failure",
        error_code="BRIDGE_WORKER_FAILED",
        error_type=bounded_type,
    )
    # Publish the result first; a visible failed status always has its result.
    _atomic_json(
        result_path,
        result.model_dump(mode="json", by_alias=True, exclude_none=True),
    )
    _atomic_json(
        status_path,
        status.model_dump(mode="json", by_alias=True, exclude_none=True),
    )
    return result


def clear(root: Path | str) -> None:
    _safe_remove(_path(root, BRIDGE_OPERATION_RESULT_NAME))
    _safe_remove(_path(root, BRIDGE_OPERATION_STATUS_NAME))


def read_status(root: Path | str) -> BridgeOperationStatusV1 | None:
    return _safe_read(
        _path(root, BRIDGE_OPERATION_STATUS_NAME), BridgeOperationStatusV1
    )


def read_result(root: Path | str) -> BridgeOperationResultV1 | None:
    return _safe_read(
        _path(root, BRIDGE_OPERATION_RESULT_NAME), BridgeOperationResultV1
    )


def read_failure(root: Path | str) -> BridgeOperationResultV1 | None:
    """Return only a result paired with the exact durable FAILED status."""

    status = read_status(root)
    if status is None or status.state != "failed":
        return None
    result = read_result(root)
    if result is None:
        raise ValueError("BRIDGE_OPERATION_RECORD_INVALID")
    if (
        result.manifest_sha256 != status.manifest_sha256
        or result.error_code != status.error_code
        or result.error_type != status.error_type
    ):
        raise ValueError("BRIDGE_OPERATION_RECORD_INVALID")
    return result


__all__ = [
    "BRIDGE_OPERATION_RESULT_NAME",
    "BRIDGE_OPERATION_STATUS_NAME",
    "BridgeOperationResultV1",
    "BridgeOperationStatusV1",
    "clear",
    "read_result",
    "read_failure",
    "read_status",
    "write_failure",
    "write_running",
]
