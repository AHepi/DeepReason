"""Bounded grounded-output repair with deterministic anti-laundering guards.

Schema repair remains owned by :class:`deepreason.llm.adapter.LLMAdapter`.
This module adds one semantic repair call per failed span.  The model-facing
contract contains no sources, evidence, premises, ledger IDs, tools, or new
factual slots.  Epistemic-class changes are never applied here: they become
explicit Stage-A ledger-amendment requests.
"""

from __future__ import annotations

import json
from enum import Enum

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from deepreason.bridge.models import (
    BridgeOutputV1,
    BridgeResolution,
    ClaimLedgerV1,
    ClaimUseV1,
    CorrectionMode,
    GroundingReviewV1,
    GroundingStatus,
)
from deepreason.bridge.validate import validate_bridge_output
from deepreason.llm.wire import DirectWireContract
from deepreason.ontology.event import LLMCall
from deepreason.ontology.frozen import FrozenList, FrozenRecord


_REPAIR_ROLES = frozenset({"judge", "grounding_reviewer"})
_MAX_SEMANTIC_REPAIR_CALLS = 8
_FAILED = frozenset(status for status in GroundingStatus if status != GroundingStatus.SUPPORTED)
_ALLOWED_BY_STATUS: dict[GroundingStatus, frozenset[CorrectionMode]] = {
    GroundingStatus.UNSUPPORTED: frozenset(
        {
            CorrectionMode.DOWNGRADE_CLAIM,
            CorrectionMode.CHANGE_RESOLUTION,
            CorrectionMode.REMOVE_SPAN,
            CorrectionMode.REQUEST_LEDGER_AMENDMENT,
        }
    ),
    GroundingStatus.OVERSTATED: frozenset(
        {
            CorrectionMode.CORRECT_WORDING,
            CorrectionMode.DOWNGRADE_CLAIM,
            CorrectionMode.CHANGE_RESOLUTION,
            CorrectionMode.REMOVE_SPAN,
            CorrectionMode.REQUEST_LEDGER_AMENDMENT,
        }
    ),
    GroundingStatus.MISCLASSIFIED: frozenset(
        {
            CorrectionMode.DOWNGRADE_CLAIM,
            CorrectionMode.REMOVE_SPAN,
            CorrectionMode.REQUEST_LEDGER_AMENDMENT,
        }
    ),
    GroundingStatus.CITATION_MISMATCH: frozenset(
        {
            CorrectionMode.CORRECT_WORDING,
            CorrectionMode.REMOVE_SPAN,
            CorrectionMode.REQUEST_LEDGER_AMENDMENT,
        }
    ),
    GroundingStatus.UNCLEAR: frozenset(
        {
            CorrectionMode.CORRECT_WORDING,
            CorrectionMode.DOWNGRADE_CLAIM,
            CorrectionMode.CHANGE_RESOLUTION,
            CorrectionMode.REMOVE_SPAN,
            CorrectionMode.REQUEST_LEDGER_AMENDMENT,
        }
    ),
}
_UNRESOLVED_RESOLUTIONS = frozenset(
    {
        BridgeResolution.PARTIALLY_ANSWERED,
        BridgeResolution.UNDERDETERMINED,
        BridgeResolution.INSUFFICIENT_EVIDENCE,
        BridgeResolution.CONFLICTING_EVIDENCE,
        BridgeResolution.OUTSIDE_SCOPE,
    }
)


class RepairDisposition(str, Enum):
    APPLIED = "applied"
    LEDGER_AMENDMENT_REQUIRED = "ledger_amendment_required"
    BOUNDED_FAILURE = "bounded_failure"


class GroundingRepairWireV1(BaseModel):
    """One local action; canonical references are intentionally absent."""

    model_config = ConfigDict(extra="forbid")

    action: CorrectionMode
    replacement_text: str | None = Field(default=None, max_length=262_144)
    resolution: BridgeResolution | None = None
    resolution_reason: str | None = Field(default=None, max_length=262_144)

    @field_validator("replacement_text", "resolution_reason")
    @classmethod
    def _optional_text_nonblank(cls, value):
        if value is not None and not value.strip():
            raise ValueError("optional repair text must be absent or non-blank")
        return value

    @model_validator(mode="after")
    def _action_shape(self):
        if self.action == CorrectionMode.CORRECT_WORDING:
            if self.replacement_text is None:
                raise ValueError("correct_wording requires replacement_text")
            if self.resolution is not None or self.resolution_reason is not None:
                raise ValueError("correct_wording may only supply replacement_text")
        elif self.action == CorrectionMode.CHANGE_RESOLUTION:
            if self.resolution is None or self.resolution_reason is None:
                raise ValueError("change_resolution requires resolution and reason")
            if self.replacement_text is not None:
                raise ValueError("change_resolution cannot supply replacement_text")
        elif any(
            value is not None
            for value in (self.replacement_text, self.resolution, self.resolution_reason)
        ):
            raise ValueError(f"{self.action.value} does not accept substantive fields")
        return self


class BridgeRepairDiagnostic(FrozenRecord):
    model_config = ConfigDict(frozen=True, extra="forbid")

    code: str = Field(min_length=1, max_length=128)
    span_id: str = Field(min_length=1, max_length=256)
    message: str = Field(min_length=1, max_length=16_384)
    attempted_action: CorrectionMode | None = None


class BridgeRepairResult(FrozenRecord):
    model_config = ConfigDict(frozen=True, extra="forbid")

    output: BridgeOutputV1
    disposition: RepairDisposition
    diagnostics: list[BridgeRepairDiagnostic] = Field(default_factory=FrozenList)
    calls: list[LLMCall] = Field(default_factory=FrozenList)
    amendment_span_ids: list[str] = Field(default_factory=FrozenList)
    requires_grounded_review: bool = False

    @field_validator("diagnostics", "calls", "amendment_span_ids", mode="after")
    @classmethod
    def _freeze_sequences(cls, value):
        return FrozenList(value)


class GroundingRepairError(RuntimeError):
    def __init__(self, code: str, message: str) -> None:
        self.code = code
        super().__init__(f"{code}: {message}")


def _make_output(
    original: BridgeOutputV1,
    *,
    sections,
    resolution: BridgeResolution,
    resolution_reason: str | None,
) -> BridgeOutputV1:
    return BridgeOutputV1.create(
        claim_ledger_id=original.claim_ledger_id,
        sections=list(sections),
        unresolved_items=(
            list(original.unresolved_items) if original.unresolved_items is not None else None
        ),
        resolution=resolution,
        resolution_reason=resolution_reason,
    )


def _quarantine_span(
    output: BridgeOutputV1,
    span_id: str,
    *,
    requested_resolution: BridgeResolution | None = None,
    reason: str | None = None,
) -> BridgeOutputV1:
    sections = [section for section in output.sections if section.span_id != span_id]
    default_resolution = (
        BridgeResolution.PARTIALLY_ANSWERED
        if sections
        else BridgeResolution.INSUFFICIENT_EVIDENCE
    )
    resolution = requested_resolution or default_resolution
    if resolution == BridgeResolution.PARTIALLY_ANSWERED and not sections:
        resolution = BridgeResolution.INSUFFICIENT_EVIDENCE
    if resolution == BridgeResolution.ANSWERED:
        resolution = default_resolution
    return _make_output(
        output,
        sections=sections,
        resolution=resolution,
        resolution_reason=(
            reason
            or "One or more spans remain unresolved after grounded review."
        ),
    )


def assert_safe_repair_diff(
    before: BridgeOutputV1,
    after: BridgeOutputV1,
) -> None:
    """Reject structural edits that could launder a new claim or reference."""

    if after.claim_ledger_id != before.claim_ledger_id:
        raise GroundingRepairError(
            "BRIDGE_REPAIR_LEDGER_CHANGED", "repair cannot change its claim ledger"
        )
    old = {section.span_id: section for section in before.sections}
    for section in after.sections:
        previous = old.get(section.span_id)
        if previous is None:
            raise GroundingRepairError(
                "BRIDGE_REPAIR_SPAN_ADDED", "repair cannot introduce a new span"
            )
        if list(section.ledger_entry_ids) != list(previous.ledger_entry_ids):
            raise GroundingRepairError(
                "BRIDGE_REPAIR_REFS_CHANGED",
                "repair cannot add, remove, or replace ledger references",
            )
        if section.rendering_mode != previous.rendering_mode:
            raise GroundingRepairError(
                "BRIDGE_REPAIR_CLASS_CHANGE_REQUIRES_AMENDMENT",
                "epistemic-class changes require an explicit ledger amendment",
            )
    if (
        after.resolution == BridgeResolution.ANSWERED
        and before.resolution != BridgeResolution.ANSWERED
    ):
        raise GroundingRepairError(
            "BRIDGE_REPAIR_RESOLUTION_TOO_STRONG",
            "a repaired output cannot newly assert resolution=answered",
        )
    before_unresolved = [item.id for item in before.unresolved_items or ()]
    after_unresolved = [item.id for item in after.unresolved_items or ()]
    if after_unresolved != before_unresolved:
        raise GroundingRepairError(
            "BRIDGE_REPAIR_UNRESOLVED_CHANGED",
            "local repair cannot manufacture or rewrite unresolved items",
        )


def _repair_pack(section, finding, entries, allowed) -> str:
    entry_handles = {entry.id: f"E{index}" for index, entry in enumerate(entries, 1)}
    ref_fields = (
        "source_refs",
        "evidence_refs",
        "event_refs",
        "trace_refs",
        "formal_observation_refs",
        "formal_artifact_refs",
        "conflict_refs",
        "source_conflict_refs",
    )
    all_refs = list(
        dict.fromkeys(
            ref
            for entry in entries
            for field in ref_fields
            for ref in getattr(entry, field) or ()
        )
    )
    ref_handles = {ref: f"R{index}" for index, ref in enumerate(all_refs, 1)}
    localized_entries = []
    for entry in entries:
        value = entry.model_dump(
            mode="json",
            by_alias=True,
            exclude_none=True,
            exclude={"schema_", "id", "scratch_refs"},
        )
        value["ledger_handle"] = entry_handles[entry.id]
        for field in ref_fields:
            if field in value:
                value[field] = [ref_handles[ref] for ref in value[field]]
        if "premise_refs" in value:
            # Premises outside this failed span are not repair-authorable.
            value["premise_count"] = len(value.pop("premise_refs"))
        localized_entries.append(value)
    payload = {
        "task": "Choose one permitted local correction for this failed span.",
        "failed_span": {
            "span_handle": "S1",
            "text": section.text,
            "rendering_mode": section.rendering_mode.value,
        },
        "grounding_finding": {
            "status": finding.status.value,
            "message": finding.message,
        },
        "relevant_ledger_entries": localized_entries,
        "permitted_actions": sorted(action.value for action in allowed),
        "constraints": [
            "Do not add a source, evidence reference, premise, citation, or claim.",
            "Do not browse, call tools, edit the ledger, or edit any other span.",
            "A class change can only request a separate ledger amendment.",
            "Leave a missing factual answer missing.",
        ],
    }
    return json.dumps(payload, sort_keys=True, ensure_ascii=False)


class GroundingRepairService:
    """Apply one bounded semantic repair call to each failed review span."""

    def __init__(
        self,
        adapter,
        *,
        role: str = "judge",
        max_attempts: int = 4,
    ) -> None:
        if role not in _REPAIR_ROLES:
            raise ValueError("grounding repair role must be judge or grounding_reviewer")
        self.adapter = adapter
        self.role = role
        if (
            type(max_attempts) is not int
            or not 1 <= max_attempts <= _MAX_SEMANTIC_REPAIR_CALLS
        ):
            raise ValueError(
                "max_attempts must be an integer in "
                f"1..{_MAX_SEMANTIC_REPAIR_CALLS}"
            )
        self.max_attempts = max_attempts

    def repair(
        self,
        ledger: ClaimLedgerV1,
        output: BridgeOutputV1,
        review: GroundingReviewV1,
    ) -> BridgeRepairResult:
        ledger = ClaimLedgerV1.model_validate(ledger)
        output = BridgeOutputV1.model_validate(output)
        review = GroundingReviewV1.model_validate(review)
        if review.claim_ledger_id != ledger.id or review.bridge_output_id != output.id:
            raise GroundingRepairError(
                "BRIDGE_REPAIR_REVIEW_MISMATCH",
                "grounding review does not name this ledger and output",
            )
        if not validate_bridge_output(ledger, output).valid:
            raise GroundingRepairError(
                "BRIDGE_REPAIR_INPUT_INVALID",
                "deterministic bridge validation must pass before grounding repair",
            )

        by_span = {section.span_id: section for section in output.sections}
        by_entry = {entry.id: entry for entry in ledger.entries}
        reviewed_spans = [finding.span_id for finding in review.findings]
        if (
            len(reviewed_spans) != len(set(reviewed_spans))
            or set(reviewed_spans) != set(by_span)
        ):
            raise GroundingRepairError(
                "BRIDGE_REPAIR_REVIEW_INCOMPLETE",
                "grounding review must contain exactly one finding for every span",
            )
        current = output
        calls: list[LLMCall] = []
        diagnostics: list[BridgeRepairDiagnostic] = []
        amendments: list[str] = []
        failed = False
        requires_review = False
        semantic_attempts = 0

        for finding in review.findings:
            if finding.status not in _FAILED:
                continue
            section = by_span.get(finding.span_id)
            if section is None:
                raise GroundingRepairError(
                    "BRIDGE_REPAIR_SPAN_UNKNOWN",
                    f"review names unknown span {finding.span_id!r}",
                )
            if list(finding.ledger_entry_ids) != list(section.ledger_entry_ids):
                raise GroundingRepairError(
                    "BRIDGE_REPAIR_REFS_MISMATCH",
                    "review references do not exactly match the failed span",
                )
            # A prior local action may already have quarantined this span.
            live_section = next(
                (item for item in current.sections if item.span_id == finding.span_id),
                None,
            )
            if live_section is None:
                continue
            entries = [by_entry[entry_id] for entry_id in section.ledger_entry_ids]
            allowed = _ALLOWED_BY_STATUS[finding.status]
            patch = None
            if semantic_attempts >= self.max_attempts:
                failed = True
                diagnostics.append(
                    BridgeRepairDiagnostic(
                        code="BRIDGE_REPAIR_ATTEMPT_CAP",
                        span_id=section.span_id,
                        message=(
                            "Global semantic repair call cap reached; the failed "
                            "span was quarantined without another model call."
                        ),
                    )
                )
                before = current
                current = _quarantine_span(current, section.span_id)
                assert_safe_repair_diff(before, current)
                continue
            try:
                semantic_attempts += 1
                patch, call = self.adapter.call(
                    self.role,
                    _repair_pack(section, finding, entries, allowed),
                    GroundingRepairWireV1,
                    template_role="bridge_grounding_repair",
                    wire_contract=DirectWireContract(GroundingRepairWireV1),
                )
                calls.append(call)
                if patch.action not in allowed:
                    raise GroundingRepairError(
                        "BRIDGE_REPAIR_ACTION_FORBIDDEN",
                        f"{patch.action.value} is not permitted for {finding.status.value}",
                    )

                before = current
                if patch.action == CorrectionMode.CORRECT_WORDING:
                    replacement = ClaimUseV1.create(
                        span_id=section.span_id,
                        text=patch.replacement_text,
                        rendering_mode=section.rendering_mode,
                        ledger_entry_ids=list(section.ledger_entry_ids),
                    )
                    current = _make_output(
                        current,
                        sections=[
                            replacement if item.span_id == section.span_id else item
                            for item in current.sections
                        ],
                        resolution=current.resolution,
                        resolution_reason=current.resolution_reason,
                    )
                    requires_review = True
                elif patch.action == CorrectionMode.CHANGE_RESOLUTION:
                    if patch.resolution not in _UNRESOLVED_RESOLUTIONS:
                        raise GroundingRepairError(
                            "BRIDGE_REPAIR_RESOLUTION_TOO_STRONG",
                            "repair resolution must remain explicitly unresolved",
                        )
                    current = _quarantine_span(
                        current,
                        section.span_id,
                        requested_resolution=patch.resolution,
                        reason=patch.resolution_reason,
                    )
                elif patch.action == CorrectionMode.REMOVE_SPAN:
                    current = _quarantine_span(current, section.span_id)
                else:
                    # DOWNGRADE_CLAIM and REQUEST_LEDGER_AMENDMENT both need
                    # Stage A. Quarantine the failed prose from the safe partial
                    # output and preserve an explicit amendment request.
                    amendments.append(section.span_id)
                    current = _quarantine_span(current, section.span_id)
                    diagnostics.append(
                        BridgeRepairDiagnostic(
                            code="BRIDGE_REPAIR_LEDGER_AMENDMENT_REQUIRED",
                            span_id=section.span_id,
                            message=(
                                "Epistemic-class changes require a bounded Stage-A "
                                "ledger amendment."
                            ),
                            attempted_action=patch.action,
                        )
                    )
                assert_safe_repair_diff(before, current)
                report = validate_bridge_output(ledger, current)
                if not report.valid:
                    raise GroundingRepairError(
                        "BRIDGE_REPAIR_OUTPUT_INVALID",
                        report.findings[0].message,
                    )
            except Exception as error:  # preserve bounded adapter spend and partial output
                spend = getattr(error, "spend", None)
                if spend is not None:
                    calls.append(spend)
                failed = True
                diagnostics.append(
                    BridgeRepairDiagnostic(
                        code=getattr(error, "code", "BRIDGE_REPAIR_BOUNDED_FAILURE"),
                        span_id=section.span_id,
                        message=str(error)[:16_384],
                        attempted_action=(
                            patch.action if patch is not None else None
                        ),
                    )
                )
                before = current
                current = _quarantine_span(current, section.span_id)
                assert_safe_repair_diff(before, current)

        disposition = (
            RepairDisposition.BOUNDED_FAILURE
            if failed
            else (
                RepairDisposition.LEDGER_AMENDMENT_REQUIRED
                if amendments
                else RepairDisposition.APPLIED
            )
        )
        return BridgeRepairResult(
            output=current,
            disposition=disposition,
            diagnostics=diagnostics,
            calls=calls,
            amendment_span_ids=list(dict.fromkeys(amendments)),
            requires_grounded_review=requires_review,
        )


__all__ = [
    "BridgeRepairDiagnostic",
    "BridgeRepairResult",
    "GroundingRepairError",
    "GroundingRepairService",
    "GroundingRepairWireV1",
    "RepairDisposition",
    "assert_safe_repair_diff",
]
