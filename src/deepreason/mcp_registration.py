"""Secret-free MCP registration data for the installed stdio server."""

from __future__ import annotations

import json
import os
from pathlib import Path
import shutil
import sys


class MCPRegistrationError(ValueError):
    """The installed MCP executable could not be resolved safely."""


def installed_mcp_executable(
    python_executable: Path | str | None = None,
) -> Path:
    """Resolve the MCP console script beside the active Python executable."""

    python = Path(python_executable or sys.executable).resolve()
    names = ("deepreason-mcp.exe", "deepreason-mcp") if os.name == "nt" else (
        "deepreason-mcp",
        "deepreason-mcp.exe",
    )
    for name in names:
        candidate = python.parent / name
        if candidate.is_file():
            return candidate.resolve()
    discovered = shutil.which("deepreason-mcp")
    if discovered:
        candidate = Path(discovered).resolve()
        if candidate.is_file():
            return candidate
    raise MCPRegistrationError(
        "MCP_EXECUTABLE_NOT_FOUND: deepreason-mcp is not installed beside the active Python"
    )


def registration_payload(
    python_executable: Path | str | None = None,
) -> dict[str, object]:
    """Return generic stdio registration without client-specific mutation."""

    executable = installed_mcp_executable(python_executable)
    return {
        "mcpServers": {
            "deepreason": {
                "command": str(executable),
                "args": [],
            }
        }
    }


def registration_json(
    python_executable: Path | str | None = None,
) -> str:
    return json.dumps(
        registration_payload(python_executable),
        sort_keys=True,
        separators=(",", ":"),
    )


__all__ = [
    "MCPRegistrationError",
    "installed_mcp_executable",
    "registration_json",
    "registration_payload",
]
