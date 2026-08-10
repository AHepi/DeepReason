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
_ARGUMENTATIVE_VALUES = {"observe_only", "trial_required", "single_family_trial"}

# Modes under which a sustained prose case can reach a warrant. Both route
# through the same defended trial and differ only in which ensemble gate the
# run's route topology makes available, so every policy check that applies to
# one applies to the other.
_TRIAL_AUTHORITIES = frozenset({"trial_required", "single_family_trial"})


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


def _adjudication_status_authority_enabled(config) -> bool:
    return bool(_get(config, "ADJUDICATION_STATUS_AUTHORITY_ENABLED", False))


def argumentative_authority_mode(config) -> str:
    """Read the V6 prose-authority mode and reject historical bypasses.

    Returns the DECLARED value, not the operationally-gated one: this
    feeds both the actual dispatch decision (`rules/crit.py::_authority`,
    which applies the master gate itself) and preflight misconfiguration
    detection (`text_status_authority_issues`, `authority_policy_snapshot`)
    -- masking a genuine "trial_required without a calibration receipt"
    issue behind the master gate would hide operator errors, not gate
    authority.
    """

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

    Workloads other than text otherwise preserve their established
    mechanical and formal STATUS behaviour, but that path previously had
    NO suppression at all (Part D, S2b, 2026-08-10) -- JUDGE_SEATS_ENABLED
    is the master judge-dispatch gate consulted here, distinct from
    ADJUDICATION_STATUS_AUTHORITY_ENABLED (Part C), which governs whether
    a judge's ruling may change status once a judge is already permitted
    to fire at all. Schema-v2 manifest preflight rejects text status
    modes; a calibrated mode remains unavailable until receipt
    verification exists.
    """

    if workload_profile != "text":
        if not bool(_get(config, "JUDGE_SEATS_ENABLED", False)):
            return TrialAuthority.OBSERVE_ONLY
        return TrialAuthority.STATUS
    mode = text_authority_mode(config, surface)
    if mode == TextAuthorityMode.CALIBRATED_STATUS:
        resolved = (
            TrialAuthority.STATUS
            if calibration_receipt_is_verified(config)
            else TrialAuthority.OBSERVE_ONLY
        )
    else:
        resolved = TrialAuthority.OBSERVE_ONLY
    if resolved == TrialAuthority.STATUS and not _adjudication_status_authority_enabled(
        config
    ):
        return TrialAuthority.OBSERVE_ONLY
    return resolved


def calibration_receipt_is_verified(config) -> bool:
    """Whether a declared calibration receipt has been VERIFIED, not just named.

    Always False: no receipt verifier exists. Receipt matching -- domain,
    routes, prompts, calibration metrics -- is the verifier's job, and a
    reference string is a claim about a receipt rather than a checked one.

    This is the whole gate on the direct-helper path. `ops.review_infrastructure`
    and the scheduler's rubric trials call `trial_authority_for` with no
    manifest in play, so `text_status_authority_issues` never runs for them:
    if this returns True before a verifier lands, an unverified reference in a
    config file becomes live status authority. Named and isolated so the
    verifier has exactly one place to attach, rather than staying an
    unconditional return that made the surface knob unreadable.
    """

    del config
    return False


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
    if argumentative in _TRIAL_AUTHORITIES:
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
