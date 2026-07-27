"""Typed authority policy for prospective text workloads.

The argument graph still owns internal ``Status`` values.  This module only
decides whether an LLM-mediated text judgement may create a status-changing
edge in a new schema-v2 text run.  Deterministic, execution, formal, browser,
and verifier-backed paths do not pass through this policy.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from collections.abc import Mapping


class TextAuthorityMode(str, Enum):
    """Authority granted to an LLM-mediated text adjudication surface."""

    OBSERVE_ONLY = "observe_only"
    CALIBRATED_STATUS = "calibrated_status"


class TrialAuthority(str, Enum):
    """Concrete authority passed into a single trial or comparison."""

    OBSERVE_ONLY = "observe_only"
    STATUS = "status"


class AuthoritySurface(str, Enum):
    """Text adjudication surfaces with independently configured policy."""

    RUBRIC = "rubric"
    PAIRWISE = "pairwise"
    INFRASTRUCTURE = "infrastructure"


_SURFACE_FIELDS = {
    AuthoritySurface.RUBRIC: "TEXT_RUBRIC_AUTHORITY",
    AuthoritySurface.PAIRWISE: "PAIRWISE_AUTHORITY",
    AuthoritySurface.INFRASTRUCTURE: "INFRASTRUCTURE_REVIEW_AUTHORITY",
}
_ARGUMENTATIVE_VALUES = {"observe_only", "trial_required"}


@dataclass(frozen=True)
class AuthorityPolicyIssue:
    """A stable policy violation that callers can render in their own API."""

    code: str
    message: str
    pointer: str


def _value(value) -> str:
    return value.value if isinstance(value, Enum) else str(value)


def _get(config, field: str, default):
    if isinstance(config, Mapping):
        return config.get(field, default)
    return getattr(config, field, default)


def text_authority_mode(config, surface: AuthoritySurface | str) -> TextAuthorityMode:
    """Read one typed text-authority knob from a Config-like object."""

    surface = AuthoritySurface(surface)
    raw = _get(config, _SURFACE_FIELDS[surface], TextAuthorityMode.OBSERVE_ONLY)
    return TextAuthorityMode(raw)


def argumentative_authority_mode(config) -> str:
    """Read the V6 prose-authority mode and reject historical bypasses."""

    raw = _get(config, "ARGUMENTATIVE_AUTHORITY", "observe_only")
    value = _value(raw)
    if value not in _ARGUMENTATIVE_VALUES:
        raise ValueError(f"unsupported argumentative authority: {value}")
    return value


def trial_authority_for(
    config,
    workload_profile: str | None,
    surface: AuthoritySurface | str,
) -> TrialAuthority:
    """Choose the concrete mode for an LLM trial/comparison.

    Workloads other than text preserve their established mechanical and formal
    behaviour. Schema-v2 manifest preflight rejects text status modes; a
    calibrated mode remains unavailable until receipt verification exists.
    """

    if workload_profile != "text":
        return TrialAuthority.STATUS
    mode = text_authority_mode(config, surface)
    # calibrated_status is unavailable prospectively until a receipt
    # verifier exists. Never let a bare config value create status authority.
    return TrialAuthority.OBSERVE_ONLY


def calibration_receipt(config) -> str | None:
    """Return a non-blank calibration receipt reference, if one is declared."""

    value = _get(config, "CALIBRATION_RECEIPT", None)
    if not isinstance(value, str):
        return None
    value = value.strip()
    return value or None


def text_status_authority_issues(
    config, workload_profile: str | None
) -> tuple[AuthorityPolicyIssue, ...]:
    """Return prospective schema-v2 text authority violations.

    A receipt reference is a fail-closed gate for this tranche.  Receipt
    matching (domain, routes, prompts, and calibration metrics) belongs to
    the receipt verifier; this policy layer never treats cross-family judging
    alone as authority.
    """

    if workload_profile != "text":
        return ()

    issues: list[AuthorityPolicyIssue] = []
    receipt = calibration_receipt(config)

    argumentative = argumentative_authority_mode(config)
    if argumentative == "trial_required":
        if receipt is None:
            issues.append(
                AuthorityPolicyIssue(
                    "CALIBRATION_RECEIPT_REQUIRED",
                    "text prose status authority requires CALIBRATION_RECEIPT",
                    "/engine_config/CALIBRATION_RECEIPT",
                )
            )
        else:
            issues.append(
                AuthorityPolicyIssue(
                    "CALIBRATION_RECEIPT_UNVERIFIED",
                    "text prose status authority requires a verified calibration receipt",
                    "/engine_config/CALIBRATION_RECEIPT",
                )
            )

    for surface, field in _SURFACE_FIELDS.items():
        mode = text_authority_mode(config, surface)
        if mode == TextAuthorityMode.CALIBRATED_STATUS:
            if receipt is None:
                issues.append(
                    AuthorityPolicyIssue(
                        "CALIBRATION_RECEIPT_REQUIRED",
                        f"{field}=calibrated_status requires CALIBRATION_RECEIPT",
                        "/engine_config/CALIBRATION_RECEIPT",
                    )
                )
            else:
                issues.append(
                    AuthorityPolicyIssue(
                        "CALIBRATION_RECEIPT_UNVERIFIED",
                        f"{field}=calibrated_status requires a verified calibration receipt",
                        "/engine_config/CALIBRATION_RECEIPT",
                    )
                )
    return tuple(issues)


def authority_policy_snapshot(config) -> dict[str, str | None]:
    """Return the frozen policy fields relevant to text status authority."""

    return {
        "ARGUMENTATIVE_AUTHORITY": argumentative_authority_mode(config),
        **{
            field: text_authority_mode(config, surface).value
            for surface, field in _SURFACE_FIELDS.items()
        },
        "CALIBRATION_RECEIPT": calibration_receipt(config),
    }
