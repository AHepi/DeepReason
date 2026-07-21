"""Central release policy for starting RunManifest-v6 execution.

Rollback is deliberately a launch-only concern.  Readers, replay, and
verification never consult this module, so disabling new v6 work cannot make
historical roots unavailable for inspection.
"""

from __future__ import annotations

import json
import os
import stat
from collections.abc import Mapping
from pathlib import Path
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from deepreason.cli.doctor import ProductionContractDoctorReportV1
    from deepreason.run_manifest import RunManifest


V6_LAUNCH_DISABLE_ENV = "DEEPREASON_DISABLE_V6_LAUNCHES"
RELEASE_POLICY_ENV = "DEEPREASON_RELEASE_POLICY"
RELEASE_POLICY_SCHEMA = "deepreason-release-policy-v1"

_TRUE = frozenset({"1", "true", "yes", "on"})
_FALSE = frozenset({"0", "false", "no", "off"})
_MAX_POLICY_BYTES = 64 * 1024
BOUND_RUN_MANIFEST_REQUIRED = "RUN_MANIFEST_BOUND_REQUIRED"


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


def resolve_effective_run_manifest(
    explicit_manifest: RunManifest | None,
    *,
    root: Path | str | None,
    operation: str,
    require_bound_manifest: bool = False,
) -> RunManifest | None:
    """Reconcile explicit and run-root manifest authority without mutation."""

    from deepreason.run_manifest import (
        MANIFEST_NAME,
        RunManifestError,
        load_run_manifest,
    )

    effective_manifest = explicit_manifest
    if root is None or (isinstance(root, str) and not root.strip()):
        if require_bound_manifest:
            raise RunManifestError(
                BOUND_RUN_MANIFEST_REQUIRED,
                f"{operation} requires a durably bound run manifest",
                "/root",
            )
        return effective_manifest

    manifest_path = Path(root) / MANIFEST_NAME
    try:
        manifest_path.lstat()
    except FileNotFoundError:
        if require_bound_manifest:
            raise RunManifestError(
                BOUND_RUN_MANIFEST_REQUIRED,
                f"{operation} requires a durably bound run manifest",
                f"/{MANIFEST_NAME}",
            )
        return effective_manifest

    bound_manifest = load_run_manifest(manifest_path)
    if (
        effective_manifest is not None
        and effective_manifest.canonical_bytes()
        != bound_manifest.canonical_bytes()
    ):
        raise RunManifestError(
            "RUN_MANIFEST_CONFLICT",
            f"{operation} root is already bound to a different manifest",
            f"/{MANIFEST_NAME}",
        )
    return bound_manifest


def require_v6_production_qualification(
    manifest: RunManifest,
    *,
    root: Path | str,
    operation: str,
) -> ProductionContractDoctorReportV1:
    """Require one exact canonical qualification report for a v6 launch."""

    from deepreason.cli.doctor import (
        load_production_contract_report,
        validate_production_contract_qualification,
    )
    from deepreason.run_manifest import (
        ProductionQualificationPolicyV1,
        RunManifestError,
    )

    if getattr(manifest, "schema_version", None) != 6:
        raise RunManifestError(
            "V6_PRODUCTION_QUALIFICATION_MANIFEST_REQUIRED",
            "production qualification launch authority requires RunManifest v6",
            "/schema_version",
        )
    policy = getattr(manifest, "production_qualification_policy", None)
    if not isinstance(policy, ProductionQualificationPolicyV1):
        raise RunManifestError(
            "V6_PRODUCTION_QUALIFICATION_POLICY_REQUIRED",
            f"{operation} requires frozen production qualification authority",
            "/production_qualification_policy",
        )
    if root is None or (isinstance(root, str) and not root.strip()):
        raise RunManifestError(
            "V6_PRODUCTION_QUALIFICATION_ROOT_REQUIRED",
            f"{operation} requires one bound run-root identity",
            "/root",
        )
    try:
        root_path = Path(root)
    except (TypeError, ValueError, OSError) as error:
        raise RunManifestError(
            "V6_PRODUCTION_QUALIFICATION_ROOT_REQUIRED",
            f"{operation} requires one usable run-root identity",
            "/root",
        ) from error
    if root_path == Path("."):
        raise RunManifestError(
            "V6_PRODUCTION_QUALIFICATION_ROOT_REQUIRED",
            f"{operation} cannot derive qualification from the working directory",
            "/root",
        )
    try:
        root_status = root_path.lstat()
    except OSError as error:
        raise RunManifestError(
            "V6_PRODUCTION_QUALIFICATION_ROOT_REQUIRED",
            f"{operation} requires one inspectable run-root directory",
            "/root",
        ) from error
    if not stat.S_ISDIR(root_status.st_mode) or stat.S_ISLNK(root_status.st_mode):
        raise RunManifestError(
            "V6_PRODUCTION_QUALIFICATION_ROOT_REQUIRED",
            f"{operation} requires one regular run-root directory",
            "/root",
        )

    report = load_production_contract_report(root_path / policy.report_filename)
    return validate_production_contract_qualification(report, manifest)


__all__ = [
    "BOUND_RUN_MANIFEST_REQUIRED",
    "RELEASE_POLICY_ENV",
    "RELEASE_POLICY_SCHEMA",
    "V6_LAUNCH_DISABLE_ENV",
    "resolve_effective_run_manifest",
    "require_v6_launch_allowed",
    "require_v6_production_qualification",
]
