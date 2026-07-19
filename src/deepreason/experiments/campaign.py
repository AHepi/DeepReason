"""Concurrent autonomous-inquiry campaign coordination and audit.

The campaign layer deliberately treats the files inside each run root as the
source of truth.  In particular, a worker process' return code is diagnostic
only: the reasoning terminal is read from ``run-result.json`` and bridge
terminals are read from typed events in ``log.jsonl``.  This prevents a CLI
presentation bug from turning a failed reasoning run into a bridge candidate.

Campaign policy is dimensional.  Integrity and security findings stop later
waves, while operational, completion, and epistemic findings remain local to
the affected root.  Work already launched in the current wave is always
allowed to finish before the stop decision is made.
"""

from __future__ import annotations

import json
import os
import re
import stat
import subprocess
import tempfile
from collections.abc import Callable, Iterator, Mapping, Sequence
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field, replace
from enum import Enum
from pathlib import Path
from typing import Any

from deepreason.canonical import canonical_json, sha256_hex
from deepreason.run_manifest import MANIFEST_NAME, load_run_manifest


RUN_RESULT_NAME = "run-result.json"
CANONICAL_LOG_NAME = "log.jsonl"
CAMPAIGN_PLAN_SCHEMA = "campaign.plan.v2"
CAMPAIGN_INDEX_SCHEMA = "campaign.index.v2"
ROOT_AUDIT_SCHEMA = "campaign.root-audit.v2"

QUALIFICATION_GATE_SCHEMA = "campaign.qualification-gate.v1"
QUALIFICATION_REPORT_SCHEMA = "deepreason-v6-qualification-report-v1"
QUALIFICATION_GATES = ("R0", "R1", "R2", "R3", "R4")
CAMPAIGN_MANIFEST_AUTHORITY_MISMATCH = "CAMPAIGN_MANIFEST_AUTHORITY_MISMATCH"

_MAX_QUALIFICATION_REPORT_BYTES = 4 * 1024 * 1024
_SHA256_RE = re.compile(r"[0-9a-f]{64}\Z")

class RootClassification(str, Enum):
    """One-dimensional campaign summary, ordered by control severity."""

    SECURITY_FAILURE = "SECURITY_FAILURE"
    INTEGRITY_FAILURE = "INTEGRITY_FAILURE"
    OPERATIONAL_FAILURE = "OPERATIONAL_FAILURE"
    INCOMPLETE = "INCOMPLETE"
    COMPLETE = "COMPLETE"

    @property
    def stops_later_waves(self) -> bool:
        return self in {
            RootClassification.SECURITY_FAILURE,
            RootClassification.INTEGRITY_FAILURE,
        }


@dataclass(frozen=True)
class CampaignFinding:
    """A normalized verifier or campaign finding."""

    channel: str
    check: str
    detail: str
    source: str

    def to_dict(self) -> dict[str, str]:
        return {
            "channel": self.channel,
            "check": self.check,
            "detail": self.detail,
            "source": self.source,
        }


@dataclass(frozen=True)
class PhaseTerminal:
    """Terminal observation for one phase, kept separate from other phases."""

    phase: str
    state: str
    source: str
    sequence: int | None = None
    detail: str | None = None

    def to_dict(self) -> dict[str, Any]:
        value: dict[str, Any] = {
            "phase": self.phase,
            "state": self.state,
            "source": self.source,
        }
        if self.sequence is not None:
            value["sequence"] = self.sequence
        if self.detail is not None:
            value["detail"] = self.detail
        return value


@dataclass(frozen=True)
class AuditDimensions:
    """Independent verifier dimensions plus their complete finding lists."""

    integrity_valid: bool = True
    security_valid: bool = True
    completion_satisfied: bool = True
    epistemic_checks_passed: bool = True
    operational_checks_passed: bool = True
    integrity: tuple[CampaignFinding, ...] = ()
    security: tuple[CampaignFinding, ...] = ()
    completion: tuple[CampaignFinding, ...] = ()
    epistemic: tuple[CampaignFinding, ...] = ()
    operational: tuple[CampaignFinding, ...] = ()
    stats: Mapping[str, Any] = field(default_factory=dict)

    def with_finding(self, finding: CampaignFinding) -> "AuditDimensions":
        if finding.channel not in {
            "integrity",
            "security",
            "completion",
            "epistemic",
            "operational",
        }:
            raise ValueError(f"unknown verification channel: {finding.channel}")
        updates: dict[str, Any] = {
            finding.channel: getattr(self, finding.channel) + (finding,),
        }
        validity_field = {
            "integrity": "integrity_valid",
            "security": "security_valid",
            "completion": "completion_satisfied",
            "epistemic": "epistemic_checks_passed",
            "operational": "operational_checks_passed",
        }[finding.channel]
        updates[validity_field] = False
        return replace(self, **updates)

    def to_dict(self) -> dict[str, Any]:
        return {
            "integrity_valid": self.integrity_valid,
            "security_valid": self.security_valid,
            "completion_satisfied": self.completion_satisfied,
            "epistemic_checks_passed": self.epistemic_checks_passed,
            "operational_checks_passed": self.operational_checks_passed,
            "valid": self.integrity_valid and self.security_valid,
            "integrity": [finding.to_dict() for finding in self.integrity],
            "security": [finding.to_dict() for finding in self.security],
            "completion": [finding.to_dict() for finding in self.completion],
            "epistemic": [finding.to_dict() for finding in self.epistemic],
            "operational": [finding.to_dict() for finding in self.operational],
            "stats": dict(self.stats),
        }


def classify_dimensions(dimensions: AuditDimensions) -> RootClassification:
    """Collapse dimensions using the campaign's explicit precedence.

    Epistemic failure maps to ``INCOMPLETE`` rather than corruption or an
    operational failure.  The epistemic channel remains present in full in
    the audit, so the summary classification never destroys that distinction.
    """

    if not dimensions.security_valid or dimensions.security:
        return RootClassification.SECURITY_FAILURE
    if not dimensions.integrity_valid or dimensions.integrity:
        return RootClassification.INTEGRITY_FAILURE
    if not dimensions.operational_checks_passed or dimensions.operational:
        return RootClassification.OPERATIONAL_FAILURE
    if (
        not dimensions.completion_satisfied
        or dimensions.completion
        or not dimensions.epistemic_checks_passed
        or dimensions.epistemic
    ):
        return RootClassification.INCOMPLETE
    return RootClassification.COMPLETE


@dataclass(frozen=True)
class RootAudit:
    schema: str
    run_id: str
    root: str
    classification: RootClassification
    reasoning_terminal: PhaseTerminal
    bridge_terminal: PhaseTerminal
    canonical_bridge_eligible: bool
    dimensions: AuditDimensions

    @property
    def stops_later_waves(self) -> bool:
        return self.classification.stops_later_waves

    def with_finding(self, finding: CampaignFinding) -> "RootAudit":
        dimensions = self.dimensions.with_finding(finding)
        return replace(
            self,
            dimensions=dimensions,
            classification=classify_dimensions(dimensions),
            canonical_bridge_eligible=(
                self.canonical_bridge_eligible
                and dimensions.integrity_valid
                and dimensions.security_valid
                and not dimensions.integrity
                and not dimensions.security
            ),
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema": self.schema,
            "run_id": self.run_id,
            "root": self.root,
            "classification": self.classification.value,
            "reasoning_terminal": self.reasoning_terminal.to_dict(),
            "bridge_terminal": self.bridge_terminal.to_dict(),
            "canonical_bridge_eligible": self.canonical_bridge_eligible,
            "verification": self.dimensions.to_dict(),
        }


def _mapping(value: Any) -> dict[str, Any]:
    if isinstance(value, Mapping):
        return dict(value)
    if hasattr(value, "model_dump"):
        return dict(value.model_dump(mode="json"))
    raise TypeError(f"expected a mapping or Pydantic model, got {type(value).__name__}")


def _finding(channel: str, raw: Any, *, fallback_source: str) -> CampaignFinding:
    if isinstance(raw, str):
        return CampaignFinding(
            channel=channel,
            check="verification_finding",
            detail=raw,
            source=fallback_source,
        )
    value = _mapping(raw)
    raw_channel = value.get("channel", channel)
    if isinstance(raw_channel, Enum):
        raw_channel = raw_channel.value
    return CampaignFinding(
        channel=str(raw_channel),
        check=str(value.get("check", "verification_finding")),
        detail=str(value.get("detail", value.get("message", ""))),
        source=str(value.get("source", fallback_source)),
    )


def normalize_verification_report(report: Any) -> AuditDimensions:
    """Normalize ``VerificationReportV2`` without coupling to its model type."""

    value = _mapping(report)
    channels: dict[str, tuple[CampaignFinding, ...]] = {}
    for channel in (
        "integrity",
        "security",
        "completion",
        "epistemic",
        "operational",
    ):
        raw_findings = value.get(channel, ()) or ()
        channels[channel] = tuple(
            _finding(channel, raw, fallback_source="verify_root_report")
            for raw in raw_findings
        )
    return AuditDimensions(
        integrity_valid=bool(value.get("integrity_valid", not channels["integrity"])),
        security_valid=bool(value.get("security_valid", not channels["security"])),
        completion_satisfied=bool(
            value.get("completion_satisfied", not channels["completion"])
        ),
        epistemic_checks_passed=bool(
            value.get("epistemic_checks_passed", not channels["epistemic"])
        ),
        operational_checks_passed=bool(
            value.get("operational_checks_passed", not channels["operational"])
        ),
        integrity=channels["integrity"],
        security=channels["security"],
        completion=channels["completion"],
        epistemic=channels["epistemic"],
        operational=channels["operational"],
        stats=dict(value.get("stats", {}) or {}),
    )


def read_reasoning_terminal(root: Path | str) -> tuple[PhaseTerminal, dict[str, Any] | None]:
    """Read the canonical reasoning result; process exit status is irrelevant."""

    path = Path(root) / RUN_RESULT_NAME
    if not path.is_file():
        return (
            PhaseTerminal(
                phase="reasoning",
                state="missing",
                source=RUN_RESULT_NAME,
                detail="canonical run result is missing",
            ),
            None,
        )
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        return (
            PhaseTerminal(
                phase="reasoning",
                state="malformed",
                source=RUN_RESULT_NAME,
                detail=str(error),
            ),
            None,
        )
    if not isinstance(payload, dict):
        return (
            PhaseTerminal(
                phase="reasoning",
                state="malformed",
                source=RUN_RESULT_NAME,
                detail="canonical run result must be a JSON object",
            ),
            None,
        )
    state = payload.get("state")
    if state not in {"completed", "cancelled", "failed"}:
        return (
            PhaseTerminal(
                phase="reasoning",
                state="unknown",
                source=RUN_RESULT_NAME,
                detail=f"unknown terminal state: {state!r}",
            ),
            payload,
        )
    return PhaseTerminal("reasoning", str(state), RUN_RESULT_NAME), payload


def _root_manifest_schema_version(root: Path) -> int | None:
    """Return the bound manifest version, or -1 for an invalid binding."""

    from deepreason.run_manifest import MANIFEST_NAME, load_run_manifest

    target = root / MANIFEST_NAME
    if not target.exists():
        return None
    try:
        return load_run_manifest(target).schema_version
    except Exception:  # noqa: BLE001 - an untrusted binding must fail closed
        return -1


def _canonical_bridge_eligible(
    terminal: PhaseTerminal,
    payload: Mapping[str, Any] | None,
    *,
    manifest_schema_version: int | None = None,
) -> bool:
    if terminal.state != "completed":
        return False
    if manifest_schema_version == -1:
        return False
    if manifest_schema_version == 6:
        return bool(
            payload is not None
            and payload.get("schema") == "deepreason-run-result-v2"
            and payload.get("canonical_bridge_eligible") is True
        )
    if payload is None or payload.get("schema") != "deepreason-run-result-v2":
        return True
    return payload.get("canonical_bridge_eligible") is True


def inspect_bridge_terminal(
    root: Path | str,
) -> tuple[PhaseTerminal, tuple[CampaignFinding, ...]]:
    """Inspect bridge state using only the canonical ``log.jsonl``.

    A malformed final JSON line is treated as a torn append, matching the
    canonical event-log reader.  A malformed line before the tail is durable
    corruption and is reported in the integrity channel.
    """

    path = Path(root) / CANONICAL_LOG_NAME
    if not path.is_file():
        return (
            PhaseTerminal(
                phase="bridge",
                state="unavailable",
                source=CANONICAL_LOG_NAME,
                detail="canonical event log is missing",
            ),
            (
                CampaignFinding(
                    channel="operational",
                    check="canonical_log_missing",
                    detail=f"{CANONICAL_LOG_NAME} does not exist",
                    source=CANONICAL_LOG_NAME,
                ),
            ),
        )

    try:
        physical_lines = path.read_bytes().splitlines()
    except OSError as error:
        return (
            PhaseTerminal(
                phase="bridge",
                state="unavailable",
                source=CANONICAL_LOG_NAME,
                detail=str(error),
            ),
            (
                CampaignFinding(
                    channel="operational",
                    check="canonical_log_unreadable",
                    detail=str(error),
                    source=CANONICAL_LOG_NAME,
                ),
            ),
        )

    nonempty = [(index, line) for index, line in enumerate(physical_lines, 1) if line.strip()]
    bridge_events: list[tuple[int | None, str]] = []
    findings: list[CampaignFinding] = []
    for position, (line_number, raw_line) in enumerate(nonempty):
        try:
            event = json.loads(raw_line)
        except (UnicodeError, json.JSONDecodeError) as error:
            if position == len(nonempty) - 1:
                # Canonical EventLog semantics: the invalid final record was
                # never durably acknowledged and is a recoverable torn tail.
                continue
            findings.append(
                CampaignFinding(
                    channel="integrity",
                    check="canonical_log_malformed",
                    detail=f"line {line_number}: {error}",
                    source=CANONICAL_LOG_NAME,
                )
            )
            continue
        if not isinstance(event, dict) or event.get("rule") != "Bridge":
            continue
        payload = event.get("bridge")
        if not isinstance(payload, dict):
            findings.append(
                CampaignFinding(
                    channel="integrity",
                    check="bridge_event_untyped",
                    detail=f"line {line_number}: Bridge event has no typed payload",
                    source=CANONICAL_LOG_NAME,
                )
            )
            continue
        action = payload.get("action")
        if isinstance(action, str):
            sequence = event.get("seq")
            bridge_events.append(
                (sequence if isinstance(sequence, int) else None, action)
            )

    if not bridge_events:
        return (
            PhaseTerminal("bridge", "not_started", CANONICAL_LOG_NAME),
            tuple(findings),
        )
    sequence, action = bridge_events[-1]
    normalized = action.lower()
    if normalized in {"completed", "bridge_completed"}:
        state = "completed"
    elif normalized in {"failed", "bridge_failed"}:
        state = "failed"
    else:
        state = "incomplete"
    return (
        PhaseTerminal(
            phase="bridge",
            state=state,
            source=CANONICAL_LOG_NAME,
            sequence=sequence,
            detail=None if state in {"completed", "failed"} else action,
        ),
        tuple(findings),
    )


Verifier = Callable[[Path], Any]


def _default_verifier(root: Path) -> Any:
    from deepreason.verification.report import verify_root_report

    return verify_root_report(root)


def audit_root(
    root: Path | str,
    *,
    run_id: str | None = None,
    verifier: Verifier | None = None,
    reasoning_returncode: int | None = None,
    bridge_returncode: int | None = None,
    bridge_expected: bool = False,
) -> RootAudit:
    """Build a read-only, dimensional audit for one run root."""

    root_path = Path(root)
    reasoning_terminal, reasoning_payload = read_reasoning_terminal(root_path)
    bridge_terminal, log_findings = inspect_bridge_terminal(root_path)

    try:
        dimensions = normalize_verification_report(
            (verifier or _default_verifier)(root_path)
        )
    except Exception as error:
        dimensions = AuditDimensions().with_finding(
            CampaignFinding(
                channel="operational",
                check="verification_unavailable",
                detail=f"{type(error).__name__}: {error}",
                source="verify_root_report",
            )
        )

    for finding in log_findings:
        dimensions = dimensions.with_finding(finding)

    if reasoning_terminal.state == "failed":
        dimensions = dimensions.with_finding(
            CampaignFinding(
                "operational",
                "reasoning_failed",
                "canonical run-result.json reports a failed reasoning run",
                RUN_RESULT_NAME,
            )
        )
    elif reasoning_terminal.state == "cancelled":
        dimensions = dimensions.with_finding(
            CampaignFinding(
                "completion",
                "reasoning_cancelled",
                "canonical run-result.json reports cancellation",
                RUN_RESULT_NAME,
            )
        )
    elif reasoning_terminal.state in {"missing", "malformed", "unknown"}:
        dimensions = dimensions.with_finding(
            CampaignFinding(
                "operational",
                "reasoning_terminal_unavailable",
                reasoning_terminal.detail or reasoning_terminal.state,
                RUN_RESULT_NAME,
            )
        )

    if bridge_terminal.state == "failed":
        dimensions = dimensions.with_finding(
            CampaignFinding(
                "operational",
                "bridge_failed",
                "canonical bridge event reports failure",
                CANONICAL_LOG_NAME,
            )
        )
    elif bridge_expected and bridge_terminal.state != "completed":
        dimensions = dimensions.with_finding(
            CampaignFinding(
                "operational",
                "bridge_terminal_missing",
                "automatic bridge command did not produce a completed terminal event",
                CANONICAL_LOG_NAME,
            )
        )

    # Return codes are diagnostic mismatches, never substitutes for canonical
    # terminal files.  A zero exit cannot erase ``state: failed``.
    if reasoning_returncode not in {None, 0} and reasoning_terminal.state == "completed":
        dimensions = dimensions.with_finding(
            CampaignFinding(
                "operational",
                "reasoning_exit_mismatch",
                f"process exited {reasoning_returncode} after a completed canonical result",
                "process",
            )
        )
    if bridge_returncode not in {None, 0} and bridge_terminal.state == "completed":
        dimensions = dimensions.with_finding(
            CampaignFinding(
                "operational",
                "bridge_exit_mismatch",
                f"process exited {bridge_returncode} after a completed bridge event",
                "process",
            )
        )

    return RootAudit(
        schema=ROOT_AUDIT_SCHEMA,
        run_id=run_id or root_path.name,
        root=str(root_path),
        classification=classify_dimensions(dimensions),
        reasoning_terminal=reasoning_terminal,
        bridge_terminal=bridge_terminal,
        canonical_bridge_eligible=(
            _canonical_bridge_eligible(
                reasoning_terminal,
                reasoning_payload,
                manifest_schema_version=_root_manifest_schema_version(root_path),
            )
            and dimensions.integrity_valid
            and dimensions.security_valid
            and not dimensions.integrity
            and not dimensions.security
            and not any(
                finding.check == "verification_unavailable"
                for finding in dimensions.operational
            )
        ),
        dimensions=dimensions,
    )


@dataclass(frozen=True)
class QualificationReportRef:
    """One plan-pinned qualification report."""

    gate: str
    path: Path
    sha256: str


@dataclass(frozen=True)
class CampaignRunPlan:
    run_id: str
    root: Path
    reasoning_command: tuple[str, ...] = ()
    bridge_command: tuple[str, ...] = ()
    working_directory: Path | None = None
    run_manifest: Path | None = None


@dataclass(frozen=True)
class CampaignWavePlan:
    wave_id: str
    runs: tuple[CampaignRunPlan, ...]


@dataclass(frozen=True)
class CampaignPlan:
    waves: tuple[CampaignWavePlan, ...]
    qualification: bool = True
    schema: str = CAMPAIGN_PLAN_SCHEMA
    qualification_reports: tuple[QualificationReportRef, ...] = ()


def _normalized_campaign_root(root: Path | str) -> str:
    """Return the platform-normalized identity for one campaign run root."""

    try:
        resolved = Path(root).resolve()
    except (OSError, RuntimeError, TypeError, ValueError) as error:
        raise ValueError(f"campaign run root is invalid: {root!r}") from error
    return os.path.normcase(os.path.normpath(os.fspath(resolved)))


def _campaign_roots_overlap(left: str, right: str) -> bool:
    """Whether either normalized root contains the other."""

    try:
        common = os.path.commonpath((left, right))
    except ValueError:
        return False
    return common == left or common == right


def _validate_campaign_plan(plan: CampaignPlan) -> None:
    """Validate campaign structure before any root can be opened or launched."""

    if plan.schema != CAMPAIGN_PLAN_SCHEMA:
        raise ValueError(f"unsupported campaign plan schema: {plan.schema!r}")
    if not plan.waves:
        raise ValueError("campaign plan requires a nonempty waves list")
    if not isinstance(plan.qualification, bool):
        raise ValueError("campaign qualification must be a boolean")

    wave_ids: set[str] = set()
    run_ids: set[str] = set()
    root_identities: list[str] = []
    for wave in plan.waves:
        wave_id = wave.wave_id
        normalized_wave_id = wave_id.strip() if isinstance(wave_id, str) else ""
        if not normalized_wave_id or normalized_wave_id in wave_ids:
            raise ValueError("campaign wave IDs must be nonempty and unique")
        wave_ids.add(normalized_wave_id)
        if not wave.runs:
            raise ValueError(f"wave {wave_id!r} requires a nonempty runs list")

        for run in wave.runs:
            run_id = run.run_id
            normalized_run_id = run_id.strip() if isinstance(run_id, str) else ""
            if not normalized_run_id or normalized_run_id in run_ids:
                raise ValueError(
                    "campaign run IDs must be nonempty and globally unique"
                )
            run_ids.add(normalized_run_id)

            root_identity = _normalized_campaign_root(run.root)
            if root_identity in root_identities:
                raise ValueError("campaign run roots must be globally unique")
            if any(
                _campaign_roots_overlap(root_identity, existing)
                for existing in root_identities
            ):
                raise ValueError(
                    "campaign run roots must not be ancestors or descendants"
                )
            root_identities.append(root_identity)


def campaign_plan_from_mapping(
    value: Mapping[str, Any], *, base_directory: Path | str | None = None
) -> CampaignPlan:
    """Validate and resolve the small JSON campaign-plan interface."""

    schema = value.get("schema", CAMPAIGN_PLAN_SCHEMA)
    if schema != CAMPAIGN_PLAN_SCHEMA:
        raise ValueError(f"unsupported campaign plan schema: {schema!r}")
    base = Path(base_directory or Path.cwd())
    raw_waves = value.get("waves")
    if not isinstance(raw_waves, list) or not raw_waves:
        raise ValueError("campaign plan requires a nonempty waves list")
    qualification = value.get("qualification", True)
    if not isinstance(qualification, bool):
        raise ValueError("campaign qualification must be a boolean")
    raw_reports = value.get("qualification_reports", {})
    if raw_reports is None:
        raw_reports = {}
    if not isinstance(raw_reports, Mapping):
        raise ValueError("campaign qualification_reports must be an object")
    unknown_gates = sorted(
        str(gate) for gate in raw_reports if gate not in QUALIFICATION_GATES
    )
    if unknown_gates:
        raise ValueError(
            "unknown campaign qualification gate(s): " + ", ".join(unknown_gates)
        )
    report_refs: list[QualificationReportRef] = []
    for gate in QUALIFICATION_GATES:
        if gate not in raw_reports:
            continue
        raw_report = raw_reports[gate]
        if not isinstance(raw_report, Mapping):
            raise ValueError(f"qualification report {gate} must be an object")
        if set(raw_report) != {"path", "sha256"}:
            raise ValueError(
                f"qualification report {gate} requires exactly path and sha256"
            )
        raw_path = raw_report["path"]
        digest = raw_report["sha256"]
        if not isinstance(raw_path, str) or not raw_path.strip():
            raise ValueError(f"qualification report {gate} path is invalid")
        if not isinstance(digest, str) or _SHA256_RE.fullmatch(digest) is None:
            raise ValueError(
                f"qualification report {gate} sha256 must be one lowercase digest"
            )
        report_path = Path(raw_path)
        if not report_path.is_absolute():
            report_path = base / report_path
        report_refs.append(
            QualificationReportRef(
                gate=gate,
                path=report_path.resolve(),
                sha256=digest,
            )
        )
    waves: list[CampaignWavePlan] = []
    for raw_wave in raw_waves:
        if not isinstance(raw_wave, Mapping):
            raise ValueError("every campaign wave must be an object")
        wave_id = str(raw_wave.get("id", "")).strip()
        if not wave_id:
            raise ValueError("campaign wave IDs must be nonempty and unique")
        raw_runs = raw_wave.get("runs")
        if not isinstance(raw_runs, list) or not raw_runs:
            raise ValueError(f"wave {wave_id!r} requires a nonempty runs list")
        runs: list[CampaignRunPlan] = []
        for raw_run in raw_runs:
            if not isinstance(raw_run, Mapping):
                raise ValueError("every campaign run must be an object")
            run_id = str(raw_run.get("id", "")).strip()
            if not run_id:
                raise ValueError("campaign run IDs must be nonempty and globally unique")
            raw_root = raw_run.get("root")
            if not isinstance(raw_root, str) or not raw_root.strip():
                raise ValueError(f"run {run_id!r} requires a root path")
            root = Path(raw_root)
            if not root.is_absolute():
                root = base / root
            raw_cwd = raw_run.get("cwd")
            cwd = None
            if raw_cwd is not None:
                if not isinstance(raw_cwd, str) or not raw_cwd.strip():
                    raise ValueError(f"run {run_id!r} has an invalid cwd")
                cwd = Path(raw_cwd)
                if not cwd.is_absolute():
                    cwd = base / cwd
            raw_manifest = raw_run.get("run_manifest")
            run_manifest = None
            if raw_manifest is not None:
                if not isinstance(raw_manifest, str) or not raw_manifest.strip():
                    raise ValueError(f"run {run_id!r} has an invalid run_manifest")
                run_manifest = Path(raw_manifest)
                if not run_manifest.is_absolute():
                    run_manifest = base / run_manifest
                run_manifest = run_manifest.resolve()

            def command(name: str) -> tuple[str, ...]:
                raw_command = raw_run.get(name)
                if raw_command is None or raw_command == "" or raw_command == []:
                    return ()
                if (
                    not isinstance(raw_command, list)
                    or not raw_command
                    or any(not isinstance(item, str) or not item for item in raw_command)
                ):
                    raise ValueError(
                        f"run {run_id!r} {name} must be a nonempty string list"
                    )
                return tuple(raw_command)

            runs.append(
                CampaignRunPlan(
                    run_id=run_id,
                    root=root,
                    reasoning_command=command("reasoning_command"),
                    bridge_command=command("bridge_command"),
                    working_directory=cwd,
                    run_manifest=run_manifest,
                )
            )
        waves.append(CampaignWavePlan(wave_id=wave_id, runs=tuple(runs)))
    plan = CampaignPlan(
        schema=CAMPAIGN_PLAN_SCHEMA,
        waves=tuple(waves),
        qualification=qualification,
        qualification_reports=tuple(report_refs),
    )
    _validate_campaign_plan(plan)
    return plan


def load_campaign_plan(path: Path | str) -> CampaignPlan:
    path = Path(path)
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, Mapping):
        raise ValueError("campaign plan must be a JSON object")
    return campaign_plan_from_mapping(value, base_directory=path.parent)


@dataclass(frozen=True)
class CommandOutcome:
    returncode: int | None
    error: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {"returncode": self.returncode, "error": self.error}


CommandRunner = Callable[[Sequence[str], Path | None], int]


def _subprocess_runner(command: Sequence[str], cwd: Path | None) -> int:
    return subprocess.run(list(command), cwd=cwd, check=False).returncode


@dataclass(frozen=True)
class CampaignRunRecord:
    run_id: str
    root: str
    reasoning_process: CommandOutcome | None
    bridge_decision: str
    bridge_process: CommandOutcome | None
    audit: RootAudit

    def to_dict(self) -> dict[str, Any]:
        return {
            "run_id": self.run_id,
            "root": self.root,
            "reasoning_process": (
                self.reasoning_process.to_dict() if self.reasoning_process else None
            ),
            "bridge_decision": self.bridge_decision,
            "bridge_process": (
                self.bridge_process.to_dict() if self.bridge_process else None
            ),
            "audit": self.audit.to_dict(),
        }


@dataclass(frozen=True)
class CampaignWaveRecord:
    wave_id: str
    state: str
    runs: tuple[CampaignRunRecord, ...] = ()
    suppressed_run_ids: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        return {
            "wave_id": self.wave_id,
            "state": self.state,
            "runs": [run.to_dict() for run in self.runs],
            "suppressed_run_ids": list(self.suppressed_run_ids),
        }


@dataclass(frozen=True)
class QualificationReportBinding:
    gate: str
    path: str
    sha256: str
    manifest_sha256s: tuple[str, ...]
    check_ids: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "gate": self.gate,
            "path": self.path,
            "sha256": self.sha256,
            "manifest_sha256s": list(self.manifest_sha256s),
            "check_ids": list(self.check_ids),
        }


@dataclass(frozen=True)
class RunManifestAuthorityBinding:
    run_id: str
    path: str
    schema_version: int
    sha256: str
    manifest: Any = field(repr=False, compare=False)

    def to_dict(self) -> dict[str, Any]:
        return {
            "run_id": self.run_id,
            "path": self.path,
            "schema_version": self.schema_version,
            "sha256": self.sha256,
        }


@dataclass(frozen=True)
class CampaignQualificationGate:
    schema: str
    mode: str
    required: bool
    satisfied: bool
    manifest_sha256s: tuple[str, ...]
    run_manifest_authorities: tuple[RunManifestAuthorityBinding, ...]
    reports: tuple[QualificationReportBinding, ...]
    gate_sha256: str

    def _digest_payload(self) -> dict[str, Any]:
        return {
            "schema": self.schema,
            "mode": self.mode,
            "required": self.required,
            "satisfied": self.satisfied,
            "manifest_sha256s": list(self.manifest_sha256s),
            "run_manifest_authorities": [
                authority.to_dict() for authority in self.run_manifest_authorities
            ],
            "reports": [report.to_dict() for report in self.reports],
        }

    def to_dict(self) -> dict[str, Any]:
        return {**self._digest_payload(), "gate_sha256": self.gate_sha256}



@dataclass(frozen=True)
class CampaignIndex:
    schema: str
    systemic_stop: bool
    stopped_after_wave: str | None
    qualification_gate: CampaignQualificationGate
    waves: tuple[CampaignWaveRecord, ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema": self.schema,
            "systemic_stop": self.systemic_stop,
            "stopped_after_wave": self.stopped_after_wave,
            "waves": [wave.to_dict() for wave in self.waves],
            "qualification_gate": self.qualification_gate.to_dict(),
        }

def _command_manifest_paths(run: CampaignRunPlan) -> tuple[Path, ...]:
    base = (run.working_directory or Path.cwd()).resolve()
    paths: list[Path] = []
    for command in (run.reasoning_command, run.bridge_command):
        for index, argument in enumerate(command):
            raw_path: str | None = None
            if argument == "--run-manifest":
                if index + 1 >= len(command):
                    raise ValueError(
                        f"CAMPAIGN_MANIFEST_REQUIRED: run {run.run_id!r} has "
                        "--run-manifest without a path"
                    )
                raw_path = command[index + 1]
            elif argument.startswith("--run-manifest="):
                raw_path = argument.partition("=")[2]
                if not raw_path:
                    raise ValueError(
                        f"CAMPAIGN_MANIFEST_REQUIRED: run {run.run_id!r} has "
                        "an empty --run-manifest option"
                    )
            if raw_path is None:
                continue
            path = Path(raw_path)
            if not path.is_absolute():
                path = base / path
            paths.append(path.resolve())
    return tuple(paths)


def _launch_manifest_paths(run: CampaignRunPlan) -> tuple[Path, ...]:
    if not run.reasoning_command and not run.bridge_command:
        return ()
    candidates: list[Path] = []
    if run.run_manifest is not None:
        candidates.append(run.run_manifest.resolve())
    candidates.extend(_command_manifest_paths(run))
    bound = run.root / MANIFEST_NAME
    if bound.exists() or bound.is_symlink():
        candidates.append(bound.resolve())
    return tuple(dict.fromkeys(candidates))


def _load_launch_manifests(
    plan: CampaignPlan,
) -> tuple[RunManifestAuthorityBinding, ...]:
    authorities: list[RunManifestAuthorityBinding] = []
    authority_run_ids: set[str] = set()
    for wave in plan.waves:
        for run in wave.runs:
            paths = _launch_manifest_paths(run)
            if (run.reasoning_command or run.bridge_command) and not paths:
                raise ValueError(
                    f"CAMPAIGN_MANIFEST_REQUIRED: launch run {run.run_id!r} "
                    "must name one run_manifest in the plan, pass "
                    "--run-manifest in its command, or have an existing bound "
                    f"{MANIFEST_NAME}"
                )
            manifests_by_digest: dict[str, Any] = {}
            for path in paths:
                try:
                    manifest = load_run_manifest(path)
                except (OSError, ValueError) as error:
                    raise ValueError(
                        f"CAMPAIGN_MANIFEST_INVALID: run {run.run_id!r} "
                        f"cannot load {path}: {error}"
                    ) from error
                manifests_by_digest.setdefault(manifest.sha256, manifest)
            if len(manifests_by_digest) > 1:
                raise ValueError(
                    f"CAMPAIGN_MANIFEST_CONFLICT: run {run.run_id!r} names "
                    "different launch manifests"
                )
            if not manifests_by_digest:
                continue
            if run.run_id in authority_run_ids:
                raise ValueError(
                    f"CAMPAIGN_MANIFEST_CONFLICT: duplicate authority for "
                    f"run {run.run_id!r}"
                )
            manifest = next(iter(manifests_by_digest.values()))
            authorities.append(
                RunManifestAuthorityBinding(
                    run_id=run.run_id,
                    path=str(paths[0]),
                    schema_version=manifest.schema_version,
                    sha256=manifest.sha256,
                    manifest=manifest,
                )
            )
            authority_run_ids.add(run.run_id)
    return tuple(sorted(authorities, key=lambda authority: authority.run_id))


def _bound_manifest_authority_findings(
    run: CampaignRunPlan,
    authority: RunManifestAuthorityBinding | None,
) -> tuple[CampaignFinding, ...]:
    """Verify that a launched root retained its own declared authority."""

    if authority is None:
        return ()
    target = run.root / MANIFEST_NAME
    try:
        bound = load_run_manifest(target)
    except Exception as error:  # noqa: BLE001 - bindings are untrusted
        return (
            CampaignFinding(
                channel="security",
                check=CAMPAIGN_MANIFEST_AUTHORITY_MISMATCH,
                detail=(
                    f"run {run.run_id!r} cannot load bound manifest {target}: "
                    f"{type(error).__name__}: {error}"
                ),
                source=MANIFEST_NAME,
            ),
        )
    if (
        bound.schema_version != authority.schema_version
        or bound.sha256 != authority.sha256
    ):
        return (
            CampaignFinding(
                channel="security",
                check=CAMPAIGN_MANIFEST_AUTHORITY_MISMATCH,
                detail=(
                    f"run {run.run_id!r} declared manifest {authority.path} "
                    f"({authority.sha256}) but bound {target} is "
                    f"{bound.sha256}"
                ),
                source=MANIFEST_NAME,
            ),
        )
    return ()


def _strict_report_json(raw: bytes, *, gate: str) -> Mapping[str, Any]:
    def reject_duplicates(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
        value: dict[str, Any] = {}
        for key, item in pairs:
            if key in value:
                raise ValueError(
                    f"CAMPAIGN_QUALIFICATION_REPORT_INVALID: {gate} contains "
                    f"duplicate JSON member {key!r}"
                )
            value[key] = item
        return value

    try:
        value = json.loads(raw, object_pairs_hook=reject_duplicates)
    except json.JSONDecodeError as error:
        raise ValueError(
            f"CAMPAIGN_QUALIFICATION_REPORT_INVALID: {gate} is not valid JSON"
        ) from error
    if not isinstance(value, Mapping):
        raise ValueError(
            f"CAMPAIGN_QUALIFICATION_REPORT_INVALID: {gate} must be a JSON object"
        )
    return value


def _verify_qualification_report(
    report: QualificationReportRef,
    *,
    required_manifest_sha256s: tuple[str, ...],
) -> QualificationReportBinding:
    path = report.path
    try:
        if path.is_symlink() or not path.is_file():
            raise ValueError(
                f"CAMPAIGN_QUALIFICATION_REPORT_INVALID: {report.gate} must "
                "be a regular, non-symlink file"
            )
        before = path.stat()
        if before.st_size > _MAX_QUALIFICATION_REPORT_BYTES:
            raise ValueError(
                f"CAMPAIGN_QUALIFICATION_REPORT_INVALID: {report.gate} exceeds "
                f"{_MAX_QUALIFICATION_REPORT_BYTES} bytes"
            )
        raw = path.read_bytes()
        after = path.stat()
    except ValueError:
        raise
    except OSError as error:
        raise ValueError(
            f"CAMPAIGN_QUALIFICATION_REPORT_INVALID: cannot read "
            f"{report.gate} report: {error}"
        ) from error
    if (
        len(raw) != before.st_size
        or after.st_size != before.st_size
        or after.st_mtime_ns != before.st_mtime_ns
    ):
        raise ValueError(
            f"CAMPAIGN_QUALIFICATION_REPORT_INVALID: {report.gate} changed "
            "while it was read"
        )
    actual_digest = sha256_hex(raw)
    if actual_digest != report.sha256:
        raise ValueError(
            f"CAMPAIGN_QUALIFICATION_REPORT_DIGEST_MISMATCH: {report.gate} "
            f"expected {report.sha256}, got {actual_digest}"
        )

    value = _strict_report_json(raw, gate=report.gate)
    if value.get("schema") != QUALIFICATION_REPORT_SCHEMA:
        raise ValueError(
            f"CAMPAIGN_QUALIFICATION_REPORT_INVALID: {report.gate} schema must "
            f"be {QUALIFICATION_REPORT_SCHEMA!r}"
        )
    if value.get("gate") != report.gate:
        raise ValueError(
            f"CAMPAIGN_QUALIFICATION_REPORT_INVALID: expected gate "
            f"{report.gate}, got {value.get('gate')!r}"
        )
    if value.get("passed") is not True:
        raise ValueError(
            f"CAMPAIGN_QUALIFICATION_REPORT_FAILED: {report.gate} did not pass"
        )

    raw_manifests = value.get("manifest_sha256s")
    if (
        not isinstance(raw_manifests, list)
        or not raw_manifests
        or any(
            not isinstance(digest, str)
            or _SHA256_RE.fullmatch(digest) is None
            for digest in raw_manifests
        )
        or len(set(raw_manifests)) != len(raw_manifests)
    ):
        raise ValueError(
            f"CAMPAIGN_QUALIFICATION_REPORT_INVALID: {report.gate} requires "
            "a unique, nonempty manifest_sha256s list"
        )
    covered = tuple(sorted(raw_manifests))
    missing = sorted(set(required_manifest_sha256s) - set(covered))
    if missing:
        raise ValueError(
            f"CAMPAIGN_QUALIFICATION_REPORT_SCOPE_MISMATCH: {report.gate} "
            "does not cover launch manifest(s): " + ", ".join(missing)
        )

    raw_checks = value.get("checks")
    if not isinstance(raw_checks, list) or not raw_checks:
        raise ValueError(
            f"CAMPAIGN_QUALIFICATION_REPORT_INVALID: {report.gate} requires "
            "a nonempty checks list"
        )
    check_ids: list[str] = []
    for check in raw_checks:
        if not isinstance(check, Mapping):
            raise ValueError(
                f"CAMPAIGN_QUALIFICATION_REPORT_INVALID: {report.gate} check "
                "entries must be objects"
            )
        check_id = check.get("id")
        if not isinstance(check_id, str) or not check_id.strip():
            raise ValueError(
                f"CAMPAIGN_QUALIFICATION_REPORT_INVALID: {report.gate} check "
                "IDs must be nonempty strings"
            )
        if check.get("passed") is not True:
            raise ValueError(
                f"CAMPAIGN_QUALIFICATION_REPORT_FAILED: {report.gate} check "
                f"{check_id!r} did not pass"
            )
        check_ids.append(check_id)
    if len(set(check_ids)) != len(check_ids):
        raise ValueError(
            f"CAMPAIGN_QUALIFICATION_REPORT_INVALID: {report.gate} check IDs "
            "must be unique"
        )
    return QualificationReportBinding(
        gate=report.gate,
        path=str(path),
        sha256=actual_digest,
        manifest_sha256s=covered,
        check_ids=tuple(check_ids),
    )


def _new_qualification_gate(
    plan: CampaignPlan,
    launch_authorities: Sequence[RunManifestAuthorityBinding],
) -> CampaignQualificationGate:
    mode = "qualification" if plan.qualification else "broad"
    manifest_sha256s = tuple(
        sorted(
            {
                authority.sha256
                for authority in launch_authorities
                if authority.schema_version == 6
            }
        )
    )
    required = not plan.qualification and bool(manifest_sha256s)
    bindings: tuple[QualificationReportBinding, ...] = ()
    if required:
        refs: dict[str, QualificationReportRef] = {}
        for report in plan.qualification_reports:
            if report.gate in refs:
                raise ValueError(
                    f"CAMPAIGN_QUALIFICATION_GATE_INVALID: duplicate "
                    f"{report.gate} report"
                )
            refs[report.gate] = report
        missing = [gate for gate in QUALIFICATION_GATES if gate not in refs]
        extras = sorted(set(refs) - set(QUALIFICATION_GATES))
        if missing or extras:
            details = []
            if missing:
                details.append("missing " + ", ".join(missing))
            if extras:
                details.append("unknown " + ", ".join(extras))
            raise ValueError(
                "CAMPAIGN_QUALIFICATION_GATE_REQUIRED: broad v6 campaigns "
                "require exact digested R0-R4 reports (" + "; ".join(details) + ")"
            )
        bindings = tuple(
            _verify_qualification_report(
                refs[gate],
                required_manifest_sha256s=manifest_sha256s,
            )
            for gate in QUALIFICATION_GATES
        )

    gate = CampaignQualificationGate(
        schema=QUALIFICATION_GATE_SCHEMA,
        mode=mode,
        required=required,
        satisfied=True,
        manifest_sha256s=manifest_sha256s,
        run_manifest_authorities=tuple(launch_authorities),
        reports=bindings,
        gate_sha256="",
    )
    return replace(
        gate,
        gate_sha256=sha256_hex(canonical_json(gate._digest_payload())),
    )




def _invoke(
    runner: CommandRunner, command: Sequence[str], cwd: Path | None
) -> CommandOutcome:
    try:
        return CommandOutcome(returncode=int(runner(command, cwd)))
    except Exception as error:
        return CommandOutcome(
            returncode=None,
            error=f"{type(error).__name__}: {error}",
        )


def _foreign_root_scan_failure(run_id: str, detail: str) -> CampaignFinding:
    return CampaignFinding(
        channel="security",
        check="foreign_root_path",
        detail=f"canonical log for {run_id} cannot be safely scanned: {detail}",
        source=CANONICAL_LOG_NAME,
    )


def _decoded_json_string_values(value: Any) -> Iterator[str]:
    """Yield decoded JSON string values without treating raw bytes as paths."""

    pending = [value]
    while pending:
        current = pending.pop()
        if isinstance(current, str):
            yield current
        elif isinstance(current, Mapping):
            pending.extend(current.values())
        elif isinstance(current, list):
            pending.extend(current)


def _normalized_log_path(value: str, *, base: Path) -> str | None:
    try:
        candidate = Path(value)
        if not candidate.is_absolute():
            candidate = base / candidate
        return _normalized_campaign_root(candidate)
    except (OSError, RuntimeError, TypeError, ValueError):
        return None


def _path_is_at_or_below(candidate: str, root: str) -> bool:
    try:
        return os.path.commonpath((candidate, root)) == root
    except ValueError:
        return False


def _foreign_root_path_findings(
    plans: Sequence[CampaignRunPlan],
    *,
    known_plans: Sequence[CampaignRunPlan] | None = None,
) -> dict[str, tuple[CampaignFinding, ...]]:
    """Stream canonical logs and fail closed on cross-root scan uncertainty."""

    findings: dict[str, list[CampaignFinding]] = {plan.run_id: [] for plan in plans}
    known_roots = {
        plan.run_id: _normalized_campaign_root(plan.root)
        for plan in (known_plans or plans)
    }
    for plan in plans:
        log_path = plan.root / CANONICAL_LOG_NAME
        try:
            if log_path.is_symlink():
                raise ValueError("canonical log must not be a symlink")
            before = log_path.stat()
            if not stat.S_ISREG(before.st_mode):
                raise ValueError("canonical log must be a regular file")
            if before.st_size > _MAX_QUALIFICATION_REPORT_BYTES:
                raise ValueError(
                    "canonical log exceeds "
                    f"{_MAX_QUALIFICATION_REPORT_BYTES} bytes"
                )

            bytes_read = 0
            foreign_ids: set[str] = set()
            with log_path.open("rb") as stream:
                line_number = 0
                while True:
                    raw_line = stream.readline(
                        _MAX_QUALIFICATION_REPORT_BYTES + 1
                    )
                    if not raw_line:
                        break
                    line_number += 1
                    bytes_read += len(raw_line)
                    if bytes_read > _MAX_QUALIFICATION_REPORT_BYTES:
                        raise ValueError(
                            "canonical log exceeded the bounded read limit"
                        )
                    if not raw_line.strip():
                        continue
                    try:
                        record = json.loads(raw_line.decode("utf-8"))
                    except (
                        UnicodeDecodeError,
                        json.JSONDecodeError,
                        RecursionError,
                    ) as error:
                        raise ValueError(
                            f"line {line_number} is not valid UTF-8 JSON: {error}"
                        ) from error
                    for string_value in _decoded_json_string_values(record):
                        candidate = _normalized_log_path(
                            string_value, base=plan.root
                        )
                        if candidate is None:
                            continue
                        for foreign_id, foreign_root in known_roots.items():
                            if (
                                foreign_id != plan.run_id
                                and foreign_id not in foreign_ids
                                and _path_is_at_or_below(candidate, foreign_root)
                            ):
                                findings[plan.run_id].append(
                                    CampaignFinding(
                                        channel="security",
                                        check="foreign_root_path",
                                        detail=(
                                            f"canonical log for {plan.run_id} "
                                            "contains a path at or below the root "
                                            f"of {foreign_id}"
                                        ),
                                        source=CANONICAL_LOG_NAME,
                                    )
                                )
                                foreign_ids.add(foreign_id)
            after = log_path.stat()
            if (
                bytes_read != before.st_size
                or after.st_size != before.st_size
                or after.st_mtime_ns != before.st_mtime_ns
            ):
                raise ValueError("canonical log changed while it was read")
        except (OSError, ValueError) as error:
            findings[plan.run_id].append(
                _foreign_root_scan_failure(plan.run_id, str(error))
            )
    return {run_id: tuple(items) for run_id, items in findings.items()}


class CampaignCoordinator:
    """Execute waves concurrently and apply systemic-stop policy afterward."""

    def __init__(
        self,
        *,
        runner: CommandRunner | None = None,
        verifier: Verifier | None = None,
        max_workers: int | None = None,
    ) -> None:
        self.runner = runner or _subprocess_runner
        self.verifier = verifier or _default_verifier
        self.max_workers = max_workers

    def _validate_policy(self, plan: CampaignPlan) -> None:
        if not plan.qualification:
            return
        for wave in plan.waves:
            for run in wave.runs:
                for command in (run.reasoning_command, run.bridge_command):
                    if "--experimental-v5" in command:
                        raise ValueError(
                            "qualification campaigns cannot use --experimental-v5"
                        )

    def _run_commands(
        self,
        runs: Sequence[CampaignRunPlan],
        *,
        bridge: bool,
    ) -> dict[str, CommandOutcome]:
        commands = {
            run.run_id: (run.bridge_command if bridge else run.reasoning_command, run)
            for run in runs
            if (run.bridge_command if bridge else run.reasoning_command)
        }
        if not commands:
            return {}
        worker_count = self.max_workers or len(commands)
        outcomes: dict[str, CommandOutcome] = {}
        with ThreadPoolExecutor(max_workers=max(1, worker_count)) as executor:
            future_to_id = {
                executor.submit(
                    _invoke,
                    self.runner,
                    command,
                    run.working_directory,
                ): run_id
                for run_id, (command, run) in commands.items()
            }
            for future in as_completed(future_to_id):
                outcomes[future_to_id[future]] = future.result()
        return outcomes

    def run(self, plan: CampaignPlan) -> CampaignIndex:
        _validate_campaign_plan(plan)
        from deepreason.runtime.launch_policy import require_v6_launch_allowed

        self._validate_policy(plan)
        launch_authorities = _load_launch_manifests(plan)
        authority_by_run_id = {
            authority.run_id: authority for authority in launch_authorities
        }
        for authority in launch_authorities:
            require_v6_launch_allowed(
                authority.manifest, operation="campaign launch"
            )
        qualification_gate = _new_qualification_gate(plan, launch_authorities)
        wave_records: list[CampaignWaveRecord] = []
        systemic_stop = False
        stopped_after_wave: str | None = None
        all_runs = tuple(run for wave in plan.waves for run in wave.runs)

        for wave in plan.waves:
            if systemic_stop:
                wave_records.append(
                    CampaignWaveRecord(
                        wave_id=wave.wave_id,
                        state="suppressed",
                        suppressed_run_ids=tuple(run.run_id for run in wave.runs),
                    )
                )
                continue

            # Launch the complete wave first and wait for every sibling.  No
            # root-local exception or terminal state can cancel another root.
            reasoning = self._run_commands(wave.runs, bridge=False)
            manifest_authority_findings = {
                run.run_id: _bound_manifest_authority_findings(
                    run,
                    authority_by_run_id.get(run.run_id),
                )
                for run in wave.runs
            }

            # Cross-root security is part of bridge authorization, not merely
            # a post-campaign diagnostic.  Scan after every reasoning sibling
            # has stopped and before selecting any automatic bridge candidate.
            pre_bridge_cross_root = _foreign_root_path_findings(
                wave.runs,
                known_plans=all_runs,
            )

            bridge_candidates: list[CampaignRunPlan] = []
            bridge_decisions: dict[str, str] = {}
            for run in wave.runs:
                reasoning_outcome = reasoning.get(run.run_id)
                pre_bridge_audit = audit_root(
                    run.root,
                    run_id=run.run_id,
                    verifier=self.verifier,
                    reasoning_returncode=(
                        reasoning_outcome.returncode if reasoning_outcome else None
                    ),
                )
                pre_bridge_audit = _apply_findings(
                    pre_bridge_audit,
                    manifest_authority_findings[run.run_id],
                )
                pre_bridge_audit = _apply_findings(
                    pre_bridge_audit,
                    pre_bridge_cross_root[run.run_id],
                )
                if not run.bridge_command:
                    bridge_decisions[run.run_id] = "not_configured"
                elif pre_bridge_audit.canonical_bridge_eligible:
                    bridge_candidates.append(run)
                    bridge_decisions[run.run_id] = "executed"
                elif pre_bridge_audit.reasoning_terminal.state == "completed":
                    bridge_decisions[run.run_id] = "skipped_not_bridge_eligible"
                else:
                    bridge_decisions[run.run_id] = "skipped_non_completed_reasoning"
            bridges = self._run_commands(bridge_candidates, bridge=True)

            records: list[CampaignRunRecord] = []
            for run in wave.runs:
                reasoning_outcome = reasoning.get(run.run_id)
                bridge_outcome = bridges.get(run.run_id)
                audit = audit_root(
                    run.root,
                    run_id=run.run_id,
                    verifier=self.verifier,
                    reasoning_returncode=(
                        reasoning_outcome.returncode if reasoning_outcome else None
                    ),
                    bridge_returncode=(
                        bridge_outcome.returncode if bridge_outcome else None
                    ),
                    bridge_expected=bridge_decisions[run.run_id] == "executed",
                )
                audit = _apply_findings(
                    audit,
                    manifest_authority_findings[run.run_id],
                )
                if reasoning_outcome is not None and reasoning_outcome.error:
                    audit = audit.with_finding(
                        CampaignFinding(
                            "operational",
                            "reasoning_process_error",
                            reasoning_outcome.error,
                            "process",
                        )
                    )
                if bridge_outcome is not None and bridge_outcome.error:
                    audit = audit.with_finding(
                        CampaignFinding(
                            "operational",
                            "bridge_process_error",
                            bridge_outcome.error,
                            "process",
                        )
                    )
                records.append(
                    CampaignRunRecord(
                        run_id=run.run_id,
                        root=str(run.root),
                        reasoning_process=reasoning_outcome,
                        bridge_decision=bridge_decisions[run.run_id],
                        bridge_process=bridge_outcome,
                        audit=audit,
                    )
                )

            # Re-scan for the final audit so a bridge process cannot introduce
            # a foreign-root reference after the authorization-time scan.
            cross_root = _foreign_root_path_findings(
                wave.runs,
                known_plans=all_runs,
            )
            records = [
                replace(
                    record,
                    audit=_apply_findings(record.audit, cross_root[record.run_id]),
                )
                for record in records
            ]
            wave_records.append(
                CampaignWaveRecord(
                    wave_id=wave.wave_id,
                    state="completed",
                    runs=tuple(records),
                )
            )
            if any(record.audit.stops_later_waves for record in records):
                systemic_stop = True
                stopped_after_wave = wave.wave_id

        return CampaignIndex(
            schema=CAMPAIGN_INDEX_SCHEMA,
            systemic_stop=systemic_stop,
            stopped_after_wave=stopped_after_wave,
            waves=tuple(wave_records),
            qualification_gate=qualification_gate,
        )


def _apply_findings(
    audit: RootAudit, findings: Sequence[CampaignFinding]
) -> RootAudit:
    for finding in findings:
        audit = audit.with_finding(finding)
    return audit


def write_campaign_index(path: Path | str, index: CampaignIndex) -> None:
    """Atomically publish the derived, noncanonical campaign index."""

    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    serialized = json.dumps(index.to_dict(), indent=2, sort_keys=True) + "\n"
    descriptor, temporary_name = tempfile.mkstemp(
        prefix=f".{target.name}.", suffix=".tmp", dir=target.parent
    )
    temporary = Path(temporary_name)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8", newline="\n") as handle:
            handle.write(serialized)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, target)
    finally:
        if temporary.exists():
            temporary.unlink()


__all__ = [
    "AuditDimensions",
    "CAMPAIGN_INDEX_SCHEMA",
    "CAMPAIGN_PLAN_SCHEMA",
    "CANONICAL_LOG_NAME",
    "CampaignCoordinator",
    "CampaignFinding",
    "CampaignIndex",
    "CampaignPlan",
    "CampaignRunPlan",
    "CampaignWavePlan",
    "PhaseTerminal",
    "RootAudit",
    "RootClassification",
    "audit_root",
    "campaign_plan_from_mapping",
    "classify_dimensions",
    "inspect_bridge_terminal",
    "load_campaign_plan",
    "normalize_verification_report",
    "read_reasoning_terminal",
    "write_campaign_index",
]
