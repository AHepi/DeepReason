"""Central release policy for starting RunManifest-v6 execution.

Rollback is deliberately a launch-only concern.  Readers, replay, and
verification never consult this module, so disabling new v6 work cannot make
historical roots unavailable for inspection.
"""

from __future__ import annotations

import json
import os
from collections.abc import Mapping
from pathlib import Path
from typing import Any


V6_LAUNCH_DISABLE_ENV = "DEEPREASON_DISABLE_V6_LAUNCHES"
RELEASE_POLICY_ENV = "DEEPREASON_RELEASE_POLICY"
RELEASE_POLICY_SCHEMA = "deepreason-release-policy-v1"

_TRUE = frozenset({"1", "true", "yes", "on"})
_FALSE = frozenset({"0", "false", "no", "off"})
_MAX_POLICY_BYTES = 64 * 1024


def _invalid(detail: str) -> ValueError:
    return ValueError(f"V6_LAUNCH_POLICY_INVALID: {detail}")


def _disabled(operation: str, source: str) -> ValueError:
    return ValueError(
        f"V6_LAUNCH_DISABLED: {operation} is disabled by {source}; "
        "historical v6 inspection and verification remain available"
    )


def _read_policy(path: Path) -> Mapping[str, Any]:
    try:
        if path.is_symlink() or not path.is_file():
            raise _invalid("release policy must be a regular, non-symlink file")
        size = path.stat().st_size
        if size > _MAX_POLICY_BYTES:
            raise _invalid("release policy exceeds 65536 bytes")
        raw = path.read_bytes()
    except ValueError:
        raise
    except OSError as error:
        raise _invalid(f"cannot read release policy: {error}") from error
    if len(raw) != size:
        raise _invalid("release policy changed while it was read")

    def reject_duplicates(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
        value: dict[str, Any] = {}
        for key, item in pairs:
            if key in value:
                raise _invalid(f"duplicate JSON member {key!r}")
            value[key] = item
        return value

    try:
        value = json.loads(raw, object_pairs_hook=reject_duplicates)
    except ValueError as error:
        if str(error).startswith("V6_LAUNCH_POLICY_INVALID"):
            raise
        raise _invalid("release policy is not valid JSON") from error
    if not isinstance(value, Mapping):
        raise _invalid("release policy must be a JSON object")
    if value.get("schema") != RELEASE_POLICY_SCHEMA:
        raise _invalid(f"release policy schema must be {RELEASE_POLICY_SCHEMA!r}")
    enabled = value.get("v6_launches_enabled")
    if not isinstance(enabled, bool):
        raise _invalid("v6_launches_enabled must be a boolean")
    allowed = {"schema", "v6_launches_enabled"}
    unknown = sorted(set(value) - allowed)
    if unknown:
        raise _invalid(f"unknown release policy member(s): {', '.join(unknown)}")
    return value


def require_v6_launch_allowed(subject: Any, *, operation: str) -> None:
    """Reject a new v6 launch when the central rollback policy disables it.

    Non-v6 subjects return before environment or policy parsing.  A broken
    rollback configuration therefore cannot change any v1-v5 launch path.
    """

    if getattr(subject, "schema_version", None) != 6:
        return

    raw_disable = os.environ.get(V6_LAUNCH_DISABLE_ENV)
    if raw_disable is not None:
        normalized = raw_disable.strip().casefold()
        if normalized not in _TRUE | _FALSE:
            raise _invalid(
                f"{V6_LAUNCH_DISABLE_ENV} must be one of "
                "1/0, true/false, yes/no, or on/off"
            )
        if normalized in _TRUE:
            raise _disabled(operation, V6_LAUNCH_DISABLE_ENV)

    raw_path = os.environ.get(RELEASE_POLICY_ENV)
    if raw_path is None:
        return
    if not raw_path.strip():
        raise _invalid(f"{RELEASE_POLICY_ENV} must name a policy file")
    policy = _read_policy(Path(raw_path))
    if not policy["v6_launches_enabled"]:
        raise _disabled(operation, RELEASE_POLICY_ENV)


__all__ = [
    "RELEASE_POLICY_ENV",
    "RELEASE_POLICY_SCHEMA",
    "V6_LAUNCH_DISABLE_ENV",
    "require_v6_launch_allowed",
]
