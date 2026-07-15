"""Deterministic epistemic validation for claim ledgers and bridge output."""

from __future__ import annotations

from collections.abc import Iterable

from deepreason.bridge.models import (
    BridgeOutputV1,
    BridgeValidationFindingV1,
    BridgeValidationReportV1,
    ClaimClass,
    ClaimLedgerEntryV1,
    ClaimLedgerV1,
    CorrectionMode,
    RenderingMode,
)


RENDERING_COMPATIBILITY: dict[ClaimClass, frozenset[RenderingMode]] = {
    ClaimClass.SOURCE_FACT: frozenset({RenderingMode.FACT}),
    ClaimClass.RECORDED_OBSERVATION: frozenset({RenderingMode.OBSERVATION}),
    ClaimClass.SUPPORTED_INFERENCE: frozenset({RenderingMode.INFERENCE}),
    ClaimClass.SURVIVING_CONJECTURE: frozenset({RenderingMode.CONJECTURE}),
    ClaimClass.ASSUMPTION: frozenset({RenderingMode.ASSUMPTION}),
    ClaimClass.UNKNOWN: frozenset({RenderingMode.UNKNOWN}),
    ClaimClass.CONFLICT: frozenset({RenderingMode.CONFLICT}),
}


_GROUNDING_CORRECTIONS = [
    CorrectionMode.DOWNGRADE_CLAIM,
    CorrectionMode.REMOVE_SPAN,
    CorrectionMode.CHANGE_RESOLUTION,
    CorrectionMode.REQUEST_LEDGER_AMENDMENT,
]
_REFERENCE_CORRECTIONS = [
    CorrectionMode.REMOVE_SPAN,
    CorrectionMode.REQUEST_LEDGER_AMENDMENT,
]
_RENDER_CORRECTIONS = [
    CorrectionMode.DOWNGRADE_CLAIM,
    CorrectionMode.REMOVE_SPAN,
    CorrectionMode.REQUEST_LEDGER_AMENDMENT,
]


def _finding(
    code: str,
    message: str,
    *,
    pointer: str | None = None,
    span_id: str | None = None,
    ledger_ids: Iterable[str] = (),
    corrections: Iterable[CorrectionMode] = (),
) -> BridgeValidationFindingV1:
    return BridgeValidationFindingV1.create(
        code=code,
        pointer=pointer,
        span_id=span_id,
        message=message,
        relevant_ledger_ids=list(dict.fromkeys(ledger_ids)),
        allowed_correction_modes=list(dict.fromkeys(corrections)),
    )


def _entry_grounding_findings(
    entry: ClaimLedgerEntryV1,
    pointer: str,
    *,
    known_entries: set[str],
    known_conflicts: set[str],
) -> list[BridgeValidationFindingV1]:
    findings: list[BridgeValidationFindingV1] = []
    if entry.claim_class == ClaimClass.SOURCE_FACT and not (
        entry.source_refs or entry.evidence_refs
    ):
        findings.append(
            _finding(
                "BRIDGE_SOURCE_FACT_UNGROUNDED",
                "A source-backed fact requires source_refs or evidence_refs; "
                "scratch_refs are provenance only.",
                pointer=f"{pointer}/source_refs",
                ledger_ids=[entry.id],
                corrections=_GROUNDING_CORRECTIONS,
            )
        )
    if entry.claim_class == ClaimClass.RECORDED_OBSERVATION and not any(
        (
            entry.evidence_refs,
            entry.event_refs,
            entry.trace_refs,
            entry.formal_observation_refs,
        )
    ):
        findings.append(
            _finding(
                "BRIDGE_OBSERVATION_UNGROUNDED",
                "A recorded observation requires evidence, event, trace, or "
                "formal-observation references.",
                pointer=f"{pointer}/evidence_refs",
                ledger_ids=[entry.id],
                corrections=_GROUNDING_CORRECTIONS,
            )
        )
    if entry.claim_class == ClaimClass.SUPPORTED_INFERENCE and not entry.premise_refs:
        findings.append(
            _finding(
                "BRIDGE_INFERENCE_PREMISES_MISSING",
                "A supported inference requires at least one explicit premise_ref.",
                pointer=f"{pointer}/premise_refs",
                ledger_ids=[entry.id],
                corrections=_GROUNDING_CORRECTIONS,
            )
        )
    if (
        entry.claim_class == ClaimClass.SURVIVING_CONJECTURE
        and not entry.formal_artifact_refs
    ):
        findings.append(
            _finding(
                "BRIDGE_CONJECTURE_ARTIFACT_MISSING",
                "A surviving conjecture requires the formal artifact that survived; "
                "it does not require an external source.",
                pointer=f"{pointer}/formal_artifact_refs",
                ledger_ids=[entry.id],
                corrections=_GROUNDING_CORRECTIONS,
            )
        )
    if entry.claim_class == ClaimClass.CONFLICT:
        explicit_sides = len(entry.conflict_refs or []) >= 2
        conflict_objects = bool(entry.source_conflict_refs) and all(
            ref in known_conflicts for ref in entry.source_conflict_refs or []
        )
        if not (explicit_sides or conflict_objects):
            findings.append(
                _finding(
                    "BRIDGE_CONFLICT_REFS_MISSING",
                    "A conflict requires at least two conflicting refs or a known "
                    "source-conflict object naming both sides.",
                    pointer=f"{pointer}/conflict_refs",
                    ledger_ids=[entry.id],
                    corrections=_GROUNDING_CORRECTIONS,
                )
            )
    for premise_index, premise_id in enumerate(entry.premise_refs or []):
        if premise_id not in known_entries:
            findings.append(
                _finding(
                    "BRIDGE_LEDGER_REF_UNKNOWN",
                    "premise_ref does not name an entry in this ledger.",
                    pointer=f"{pointer}/premise_refs/{premise_index}",
                    ledger_ids=[entry.id, premise_id],
                    corrections=_REFERENCE_CORRECTIONS,
                )
            )
    for conflict_index, conflict_id in enumerate(entry.source_conflict_refs or []):
        if conflict_id not in known_conflicts:
            findings.append(
                _finding(
                    "BRIDGE_LEDGER_REF_UNKNOWN",
                    "source_conflict_ref does not name a conflict in this ledger.",
                    pointer=f"{pointer}/source_conflict_refs/{conflict_index}",
                    ledger_ids=[entry.id, conflict_id],
                    corrections=_REFERENCE_CORRECTIONS,
                )
            )
    return findings


def ledger_findings(ledger: ClaimLedgerV1) -> list[BridgeValidationFindingV1]:
    known_entries = {entry.id for entry in ledger.entries}
    known_conflicts = {conflict.id for conflict in ledger.source_conflicts or []}
    findings: list[BridgeValidationFindingV1] = []
    if not ledger.entries and not ledger.uncovered_requirements:
        findings.append(
            _finding(
                "BRIDGE_LEDGER_ENTRY_MISSING",
                "A claim ledger requires an entry or an explicit uncovered requirement.",
                pointer="/entries",
                corrections=[
                    CorrectionMode.CHANGE_RESOLUTION,
                    CorrectionMode.REQUEST_LEDGER_AMENDMENT,
                ],
            )
        )
    for index, entry in enumerate(ledger.entries):
        findings.extend(
            _entry_grounding_findings(
                entry,
                f"/entries/{index}",
                known_entries=known_entries,
                known_conflicts=known_conflicts,
            )
        )
    for req_index, requirement in enumerate(ledger.uncovered_requirements or []):
        for ref_index, entry_id in enumerate(requirement.related_ledger_entry_ids or []):
            if entry_id not in known_entries:
                findings.append(
                    _finding(
                        "BRIDGE_LEDGER_REF_UNKNOWN",
                        "uncovered requirement names an unknown ledger entry.",
                        pointer=(
                            f"/uncovered_requirements/{req_index}/"
                            f"related_ledger_entry_ids/{ref_index}"
                        ),
                        ledger_ids=[entry_id],
                        corrections=_REFERENCE_CORRECTIONS,
                    )
                )
    return findings


def validate_claim_ledger(ledger: ClaimLedgerV1) -> BridgeValidationReportV1:
    ledger = ClaimLedgerV1.model_validate(ledger)
    findings = ledger_findings(ledger)
    return BridgeValidationReportV1.create(
        claim_ledger_id=ledger.id,
        valid=not findings,
        findings=findings,
    )


def _allowed_modes(
    entry: ClaimLedgerEntryV1, *, allow_observation_as_fact: bool
) -> frozenset[RenderingMode]:
    allowed = RENDERING_COMPATIBILITY[entry.claim_class]
    if (
        allow_observation_as_fact
        and entry.claim_class == ClaimClass.RECORDED_OBSERVATION
        and any(
            (
                entry.evidence_refs,
                entry.event_refs,
                entry.trace_refs,
                entry.formal_observation_refs,
            )
        )
    ):
        return allowed | {RenderingMode.FACT}
    return allowed


def output_findings(
    ledger: ClaimLedgerV1,
    output: BridgeOutputV1,
    *,
    allow_observation_as_fact: bool = False,
) -> list[BridgeValidationFindingV1]:
    findings = ledger_findings(ledger)
    entries = {entry.id: entry for entry in ledger.entries}
    if output.claim_ledger_id != ledger.id:
        findings.append(
            _finding(
                "BRIDGE_LEDGER_ENTRY_MISSING",
                "Bridge output names a different or unavailable claim ledger.",
                pointer="/claim_ledger_id",
                ledger_ids=[output.claim_ledger_id],
                corrections=[CorrectionMode.REQUEST_LEDGER_AMENDMENT],
            )
        )
    for section_index, section in enumerate(output.sections):
        if not section.ledger_entry_ids:
            findings.append(
                _finding(
                    "BRIDGE_SPAN_UNMAPPED",
                    "Every output span must map to at least one ledger entry.",
                    span_id=section.span_id,
                    corrections=_REFERENCE_CORRECTIONS,
                )
            )
            continue
        for ref_index, entry_id in enumerate(section.ledger_entry_ids):
            entry = entries.get(entry_id)
            if entry is None:
                findings.append(
                    _finding(
                        "BRIDGE_LEDGER_REF_UNKNOWN",
                        "Output span names an entry outside its claim ledger.",
                        pointer=(
                            f"/sections/{section_index}/ledger_entry_ids/{ref_index}"
                        ),
                        span_id=section.span_id,
                        ledger_ids=[entry_id],
                        corrections=_REFERENCE_CORRECTIONS,
                    )
                )
                continue
            if section.rendering_mode not in _allowed_modes(
                entry, allow_observation_as_fact=allow_observation_as_fact
            ):
                code = (
                    "BRIDGE_UNKNOWN_ASSERTS_FACT"
                    if entry.claim_class == ClaimClass.UNKNOWN
                    and section.rendering_mode == RenderingMode.FACT
                    else "BRIDGE_RENDERING_MODE_TOO_STRONG"
                )
                findings.append(
                    _finding(
                        code,
                        f"{entry.claim_class.value} cannot render as "
                        f"{section.rendering_mode.value}.",
                        span_id=section.span_id,
                        ledger_ids=[entry.id],
                        corrections=_RENDER_CORRECTIONS,
                    )
                )
    if output.resolution.value == "answered" and not output.sections:
        findings.append(
            _finding(
                "BRIDGE_SPAN_UNMAPPED",
                "resolution=answered requires at least one mapped output span.",
                pointer="/sections",
                corrections=[
                    CorrectionMode.CHANGE_RESOLUTION,
                    CorrectionMode.REQUEST_LEDGER_AMENDMENT,
                ],
            )
        )
    if not output.sections and output.resolution.value != "answered":
        if not output.resolution_reason:
            findings.append(
                _finding(
                    "BRIDGE_SPAN_UNMAPPED",
                    "A terminal no-answer result requires an explicit resolution_reason.",
                    pointer="/resolution_reason",
                    corrections=[CorrectionMode.CHANGE_RESOLUTION],
                )
            )
    for unresolved_index, item in enumerate(output.unresolved_items or []):
        for ref_index, entry_id in enumerate(item.ledger_entry_ids or []):
            if entry_id not in entries:
                findings.append(
                    _finding(
                        "BRIDGE_LEDGER_REF_UNKNOWN",
                        "Unresolved item names an entry outside its claim ledger.",
                        pointer=(
                            f"/unresolved_items/{unresolved_index}/"
                            f"ledger_entry_ids/{ref_index}"
                        ),
                        ledger_ids=[entry_id],
                        corrections=_REFERENCE_CORRECTIONS,
                    )
                )
    return findings


def validate_bridge_output(
    ledger: ClaimLedgerV1,
    output: BridgeOutputV1,
    *,
    allow_observation_as_fact: bool = False,
) -> BridgeValidationReportV1:
    ledger = ClaimLedgerV1.model_validate(ledger)
    output = BridgeOutputV1.model_validate(output)
    findings = output_findings(
        ledger,
        output,
        allow_observation_as_fact=allow_observation_as_fact,
    )
    return BridgeValidationReportV1.create(
        claim_ledger_id=ledger.id,
        bridge_output_id=output.id,
        valid=not findings,
        findings=findings,
    )


__all__ = [
    "RENDERING_COMPATIBILITY",
    "ledger_findings",
    "output_findings",
    "validate_bridge_output",
    "validate_claim_ledger",
]
