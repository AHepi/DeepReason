"""Canonical immutable records for the grounded final-output bridge.

The claim ledger preserves epistemic categories before prose composition.
Scratch references are represented in a separate provenance-only field and
are never interchangeable with source, evidence, observation, premise, or
formal-artifact references.
"""

from __future__ import annotations

import re
from enum import Enum
from typing import ClassVar, Literal

from pydantic import ConfigDict, Field, StrictBool, StrictInt, field_validator, model_validator

from deepreason.ontology.frozen import FrozenList, FrozenRecord
from deepreason.scratch.models import HashRef, OpaqueRef, domain_hash


MAX_BRIDGE_TEXT = 262_144
MAX_BRIDGE_SHORT_TEXT = 16_384
MAX_BRIDGE_REFS = 2_048
MAX_LEDGER_ENTRIES = 10_000
MAX_OUTPUT_SECTIONS = 10_000
MAX_FINDINGS = 10_000

BridgeText = str


class ClaimClass(str, Enum):
    SOURCE_FACT = "source_fact"
    RECORDED_OBSERVATION = "recorded_observation"
    SUPPORTED_INFERENCE = "supported_inference"
    SURVIVING_CONJECTURE = "surviving_conjecture"
    ASSUMPTION = "assumption"
    UNKNOWN = "unknown"
    CONFLICT = "conflict"


class BridgeResolution(str, Enum):
    ANSWERED = "answered"
    PARTIALLY_ANSWERED = "partially_answered"
    UNDERDETERMINED = "underdetermined"
    INSUFFICIENT_EVIDENCE = "insufficient_evidence"
    CONFLICTING_EVIDENCE = "conflicting_evidence"
    OUTSIDE_SCOPE = "outside_scope"


class RenderingMode(str, Enum):
    FACT = "fact"
    OBSERVATION = "observation"
    INFERENCE = "inference"
    CONJECTURE = "conjecture"
    ASSUMPTION = "assumption"
    UNKNOWN = "unknown"
    CONFLICT = "conflict"


class CorrectionMode(str, Enum):
    CORRECT_WORDING = "correct_wording"
    DOWNGRADE_CLAIM = "downgrade_claim"
    CHANGE_RESOLUTION = "change_resolution"
    REMOVE_SPAN = "remove_span"
    REQUEST_LEDGER_AMENDMENT = "request_ledger_amendment"


class GroundingStatus(str, Enum):
    SUPPORTED = "supported"
    UNSUPPORTED = "unsupported"
    OVERSTATED = "overstated"
    MISCLASSIFIED = "misclassified"
    CITATION_MISMATCH = "citation_mismatch"
    UNCLEAR = "unclear"


def _nonblank(value: str | None) -> str | None:
    if value is not None and not value.strip():
        raise ValueError("text must contain a non-whitespace character")
    return value


def _bounded_text(value: str | None, *, maximum: int = MAX_BRIDGE_TEXT) -> str | None:
    value = _nonblank(value)
    if value is not None and len(value) > maximum:
        raise ValueError(f"text must contain at most {maximum} characters")
    return value


def _freeze_unique(value, field_name: str):
    if value is None:
        return None
    if any(isinstance(item, str) and not item.strip() for item in value):
        raise ValueError(f"{field_name} must not contain blank references")
    if len(value) != len(set(value)):
        raise ValueError(f"{field_name} must not contain duplicates")
    return FrozenList(value)


class BridgeRecord(FrozenRecord):
    model_config = ConfigDict(frozen=True, extra="forbid", populate_by_name=True)


class CanonicalBridgeRecord(BridgeRecord):
    """Domain-separated content record with verified caller-supplied ID."""

    id: HashRef
    ID_DOMAIN: ClassVar[str]

    @classmethod
    def create(cls, **values):
        payload = {}
        for name, field in cls.model_fields.items():
            if name in {"schema_", "id"}:
                continue
            if name in values:
                value = values[name]
            elif field.is_required():
                continue
            else:
                value = field.get_default(call_default_factory=True)
            if value is not None:
                payload[name] = value
        return cls(id=domain_hash(cls.ID_DOMAIN, payload), **values)

    def identity_payload(self) -> dict:
        return self.model_dump(
            mode="json",
            by_alias=True,
            exclude={"schema_", "id"},
            exclude_none=True,
        )

    @model_validator(mode="after")
    def _identity_matches(self):
        if self.id != domain_hash(self.ID_DOMAIN, self.identity_payload()):
            raise ValueError(f"id does not match canonical {self.ID_DOMAIN} identity")
        return self


class ClaimLedgerEntryV1(CanonicalBridgeRecord):
    schema_: Literal["bridge.claim-ledger.entry.v1"] = Field(
        "bridge.claim-ledger.entry.v1", alias="schema"
    )
    ID_DOMAIN: ClassVar[str] = "bridge.claim-ledger.entry.v1"

    claim_class: ClaimClass
    claim: BridgeText
    source_refs: list[OpaqueRef] | None = Field(default=None, max_length=MAX_BRIDGE_REFS)
    evidence_refs: list[OpaqueRef] | None = Field(default=None, max_length=MAX_BRIDGE_REFS)
    event_refs: list[OpaqueRef] | None = Field(default=None, max_length=MAX_BRIDGE_REFS)
    trace_refs: list[OpaqueRef] | None = Field(default=None, max_length=MAX_BRIDGE_REFS)
    formal_observation_refs: list[OpaqueRef] | None = Field(
        default=None, max_length=MAX_BRIDGE_REFS
    )
    premise_refs: list[HashRef] | None = Field(default=None, max_length=MAX_BRIDGE_REFS)
    formal_artifact_refs: list[OpaqueRef] | None = Field(
        default=None, max_length=MAX_BRIDGE_REFS
    )
    conflict_refs: list[OpaqueRef] | None = Field(default=None, max_length=MAX_BRIDGE_REFS)
    source_conflict_refs: list[HashRef] | None = Field(
        default=None, max_length=MAX_BRIDGE_REFS
    )
    # Intellectual provenance only. These refs never satisfy any grounding
    # requirement and deliberately have their own field and type.
    scratch_refs: list[HashRef] | None = Field(default=None, max_length=MAX_BRIDGE_REFS)
    qualification: BridgeText | None = None

    @field_validator("claim", "qualification")
    @classmethod
    def _bounded_claim_text(cls, value):
        return _bounded_text(value)

    @field_validator(
        "source_refs",
        "evidence_refs",
        "event_refs",
        "trace_refs",
        "formal_observation_refs",
        "premise_refs",
        "formal_artifact_refs",
        "conflict_refs",
        "source_conflict_refs",
        "scratch_refs",
        mode="after",
    )
    @classmethod
    def _freeze_refs(cls, value, info):
        return _freeze_unique(value, info.field_name)


class UncoveredRequirementV1(CanonicalBridgeRecord):
    schema_: Literal["bridge.uncovered-requirement.v1"] = Field(
        "bridge.uncovered-requirement.v1", alias="schema"
    )
    ID_DOMAIN: ClassVar[str] = "bridge.uncovered-requirement.v1"

    requirement: BridgeText
    reason: BridgeText | None = None
    related_ledger_entry_ids: list[HashRef] | None = Field(
        default=None, max_length=MAX_BRIDGE_REFS
    )
    scratch_refs: list[HashRef] | None = Field(default=None, max_length=MAX_BRIDGE_REFS)

    @field_validator("requirement", "reason")
    @classmethod
    def _bounded_text_fields(cls, value):
        return _bounded_text(value)

    @field_validator("related_ledger_entry_ids", "scratch_refs", mode="after")
    @classmethod
    def _freeze_refs(cls, value, info):
        return _freeze_unique(value, info.field_name)


class SourceConflictV1(CanonicalBridgeRecord):
    schema_: Literal["bridge.source-conflict.v1"] = Field(
        "bridge.source-conflict.v1", alias="schema"
    )
    ID_DOMAIN: ClassVar[str] = "bridge.source-conflict.v1"

    conflicting_refs: list[OpaqueRef] = Field(min_length=2, max_length=MAX_BRIDGE_REFS)
    description: BridgeText | None = None
    scratch_refs: list[HashRef] | None = Field(default=None, max_length=MAX_BRIDGE_REFS)

    @field_validator("description")
    @classmethod
    def _bounded_description(cls, value):
        return _bounded_text(value)

    @field_validator("conflicting_refs", "scratch_refs", mode="after")
    @classmethod
    def _freeze_refs(cls, value, info):
        return _freeze_unique(value, info.field_name)


class ClaimLedgerV1(CanonicalBridgeRecord):
    schema_: Literal["bridge.claim-ledger.v1"] = Field(
        "bridge.claim-ledger.v1", alias="schema"
    )
    ID_DOMAIN: ClassVar[str] = "bridge.claim-ledger.v1"

    problem_ref: OpaqueRef
    formal_seq: StrictInt = Field(ge=0)
    output_target: str = Field(min_length=1, max_length=512)
    entries: list[ClaimLedgerEntryV1] = Field(max_length=MAX_LEDGER_ENTRIES)
    uncovered_requirements: list[UncoveredRequirementV1] | None = Field(
        default=None, max_length=MAX_LEDGER_ENTRIES
    )
    source_conflicts: list[SourceConflictV1] | None = Field(
        default=None, max_length=MAX_LEDGER_ENTRIES
    )
    advisory_context_ref: HashRef | None = None
    retrieval_receipt_ref: HashRef | None = None

    @field_validator("output_target")
    @classmethod
    def _nonblank_target(cls, value):
        return _nonblank(value)

    @field_validator("entries", "uncovered_requirements", "source_conflicts", mode="after")
    @classmethod
    def _freeze_objects(cls, value, info):
        if value is None:
            return None
        ids = [item.id for item in value]
        if len(ids) != len(set(ids)):
            raise ValueError(f"{info.field_name} must not contain duplicate identities")
        return FrozenList(value)


class ClaimUseV1(CanonicalBridgeRecord):
    schema_: Literal["bridge.claim-use.v1"] = Field(
        "bridge.claim-use.v1", alias="schema"
    )
    ID_DOMAIN: ClassVar[str] = "bridge.claim-use.v1"

    span_id: str = Field(min_length=1, max_length=256)
    text: BridgeText
    rendering_mode: RenderingMode
    ledger_entry_ids: list[HashRef] = Field(max_length=MAX_BRIDGE_REFS)

    @field_validator("span_id")
    @classmethod
    def _valid_span_id(cls, value):
        value = _nonblank(value)
        if re.fullmatch(r"[A-Za-z][A-Za-z0-9_.:-]{0,255}", value) is None:
            raise ValueError("span_id must be one opaque local identifier")
        return value

    @field_validator("text")
    @classmethod
    def _bounded_span_text(cls, value):
        return _bounded_text(value)

    @field_validator("ledger_entry_ids", mode="after")
    @classmethod
    def _freeze_ledger_refs(cls, value, info):
        return _freeze_unique(value, info.field_name)


class UnresolvedItemV1(CanonicalBridgeRecord):
    schema_: Literal["bridge.unresolved-item.v1"] = Field(
        "bridge.unresolved-item.v1", alias="schema"
    )
    ID_DOMAIN: ClassVar[str] = "bridge.unresolved-item.v1"

    description: BridgeText
    reason: BridgeText | None = None
    ledger_entry_ids: list[HashRef] | None = Field(default=None, max_length=MAX_BRIDGE_REFS)

    @field_validator("description", "reason")
    @classmethod
    def _bounded_text_fields(cls, value):
        return _bounded_text(value)

    @field_validator("ledger_entry_ids", mode="after")
    @classmethod
    def _freeze_refs(cls, value, info):
        return _freeze_unique(value, info.field_name)


class BridgeOutputV1(CanonicalBridgeRecord):
    schema_: Literal["bridge.output.v1"] = Field("bridge.output.v1", alias="schema")
    ID_DOMAIN: ClassVar[str] = "bridge.output.v1"

    claim_ledger_id: HashRef
    sections: list[ClaimUseV1] = Field(max_length=MAX_OUTPUT_SECTIONS)
    unresolved_items: list[UnresolvedItemV1] | None = Field(
        default=None, max_length=MAX_OUTPUT_SECTIONS
    )
    resolution: BridgeResolution
    resolution_reason: BridgeText | None = None

    @field_validator("resolution_reason")
    @classmethod
    def _bounded_reason(cls, value):
        return _bounded_text(value)

    @field_validator("sections", "unresolved_items", mode="after")
    @classmethod
    def _freeze_unique_objects(cls, value, info):
        if value is None:
            return None
        ids = [item.id for item in value]
        if len(ids) != len(set(ids)):
            raise ValueError(f"{info.field_name} must not contain duplicate identities")
        if info.field_name == "sections":
            spans = [item.span_id for item in value]
            if len(spans) != len(set(spans)):
                raise ValueError("sections must not contain duplicate span IDs")
        return FrozenList(value)


class BridgeValidationFindingV1(CanonicalBridgeRecord):
    schema_: Literal["bridge.validation.finding.v1"] = Field(
        "bridge.validation.finding.v1", alias="schema"
    )
    ID_DOMAIN: ClassVar[str] = "bridge.validation.finding.v1"

    code: str = Field(min_length=1, max_length=128, pattern=r"^[A-Z][A-Z0-9_]*$")
    pointer: str | None = Field(default=None, max_length=2_048)
    span_id: str | None = Field(default=None, max_length=256)
    message: str = Field(min_length=1, max_length=MAX_BRIDGE_SHORT_TEXT)
    relevant_ledger_ids: list[HashRef] = Field(
        default_factory=FrozenList, max_length=MAX_BRIDGE_REFS
    )
    allowed_correction_modes: list[CorrectionMode] = Field(
        default_factory=FrozenList, max_length=len(CorrectionMode)
    )

    @field_validator("span_id", "message")
    @classmethod
    def _nonblank_fields(cls, value):
        return _nonblank(value)

    @field_validator("pointer")
    @classmethod
    def _json_pointer_shape(cls, value):
        if value is not None and value != "" and not value.startswith("/"):
            raise ValueError("pointer must be a JSON Pointer")
        return value

    @field_validator("relevant_ledger_ids", "allowed_correction_modes", mode="after")
    @classmethod
    def _freeze_lists(cls, value, info):
        return _freeze_unique(value, info.field_name)

    @model_validator(mode="after")
    def _has_location(self):
        if self.pointer is None and self.span_id is None:
            raise ValueError("validation finding requires pointer or span_id")
        return self


class BridgeValidationReportV1(CanonicalBridgeRecord):
    schema_: Literal["bridge.validation.report.v1"] = Field(
        "bridge.validation.report.v1", alias="schema"
    )
    ID_DOMAIN: ClassVar[str] = "bridge.validation.report.v1"

    claim_ledger_id: HashRef
    bridge_output_id: HashRef | None = None
    valid: StrictBool
    findings: list[BridgeValidationFindingV1] = Field(max_length=MAX_FINDINGS)

    @field_validator("findings", mode="after")
    @classmethod
    def _freeze_findings(cls, value):
        ids = [item.id for item in value]
        if len(ids) != len(set(ids)):
            raise ValueError("findings must not contain duplicate identities")
        return FrozenList(value)

    @model_validator(mode="after")
    def _validity_matches_findings(self):
        if self.valid == bool(self.findings):
            raise ValueError("valid report must have no findings; invalid report requires findings")
        return self


class GroundingFindingV1(CanonicalBridgeRecord):
    schema_: Literal["bridge.grounding.finding.v1"] = Field(
        "bridge.grounding.finding.v1", alias="schema"
    )
    ID_DOMAIN: ClassVar[str] = "bridge.grounding.finding.v1"

    span_id: str = Field(min_length=1, max_length=256)
    status: GroundingStatus
    message: str | None = Field(default=None, max_length=MAX_BRIDGE_SHORT_TEXT)
    ledger_entry_ids: list[HashRef] = Field(
        default_factory=FrozenList, max_length=MAX_BRIDGE_REFS
    )
    checked_refs: list[OpaqueRef] | None = Field(default=None, max_length=MAX_BRIDGE_REFS)

    @field_validator("span_id", "message")
    @classmethod
    def _nonblank_fields(cls, value):
        return _nonblank(value)

    @field_validator("ledger_entry_ids", "checked_refs", mode="after")
    @classmethod
    def _freeze_refs(cls, value, info):
        return _freeze_unique(value, info.field_name)


class GroundingReviewV1(CanonicalBridgeRecord):
    schema_: Literal["bridge.grounding.review.v1"] = Field(
        "bridge.grounding.review.v1", alias="schema"
    )
    ID_DOMAIN: ClassVar[str] = "bridge.grounding.review.v1"

    claim_ledger_id: HashRef
    bridge_output_id: HashRef
    findings: list[GroundingFindingV1] = Field(max_length=MAX_FINDINGS)
    passed: StrictBool

    @field_validator("findings", mode="after")
    @classmethod
    def _freeze_findings(cls, value):
        ids = [item.id for item in value]
        if len(ids) != len(set(ids)):
            raise ValueError("grounding findings must not contain duplicate identities")
        return FrozenList(value)

    @model_validator(mode="after")
    def _passed_matches_findings(self):
        failing = {
            GroundingStatus.UNSUPPORTED,
            GroundingStatus.OVERSTATED,
            GroundingStatus.MISCLASSIFIED,
            GroundingStatus.CITATION_MISMATCH,
            GroundingStatus.UNCLEAR,
        }
        if self.passed == any(finding.status in failing for finding in self.findings):
            raise ValueError("passed must be false when any grounding finding fails")
        return self


__all__ = [
    "BridgeOutputV1",
    "BridgeRecord",
    "BridgeResolution",
    "BridgeValidationFindingV1",
    "BridgeValidationReportV1",
    "CanonicalBridgeRecord",
    "ClaimClass",
    "ClaimLedgerEntryV1",
    "ClaimLedgerV1",
    "ClaimUseV1",
    "CorrectionMode",
    "GroundingFindingV1",
    "GroundingReviewV1",
    "GroundingStatus",
    "RenderingMode",
    "SourceConflictV1",
    "UncoveredRequirementV1",
    "UnresolvedItemV1",
]
