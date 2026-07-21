"""Bounded Stage B composition from one already-validated claim ledger.

The composer exposes only call-local ledger handles to the model.  Compilation
can resolve those handles only to entries already present in the input ledger;
it has no operation that creates a claim, source, premise, or grounding ref.
If genuinely new inference or conjecture semantics are needed, the single wire
response can instead return a bounded amendment request.  That is a successful
workflow outcome, not a schema failure and not a ledger mutation.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from enum import Enum
from typing import Literal

from pydantic import Field, StrictInt, create_model, field_validator, model_validator

from deepreason.bridge.models import (
    BridgeOutputV1,
    BridgeRecord,
    BridgeResolution,
    BridgeValidationReportV1,
    ClaimLedgerV1,
    ClaimUseV1,
    RenderingMode,
    UnresolvedItemV1,
)
from deepreason.bridge.validate import validate_bridge_output, validate_claim_ledger
from deepreason.llm.repair import SchemaRepairError
from deepreason.llm.wire import AliasTable, StrictWireModel, WireContract
from deepreason.ontology.event import LLMCall


_MAX_COMPOSITION_TEXT = 262_144
_MAX_COMPOSITION_ITEMS = 10_000
_HANDLE_SENTINEL = "NO_LEDGER_ENTRIES"
_COMPOSER_ROLES = frozenset({"summarizer", "thesis"})


class CompositionContractError(ValueError):
    """A compiled composition violated one exact bridge-output constraint.

    The structured-output repair boundary reads ``pointer`` and
    ``repair_scope`` only as inert validation metadata.  Giving it the exact
    wire field prevents a parseable repair from reopening the surrounding
    section, resolution, evidence handles, or any other semantic content.
    """

    code = "BRIDGE_COMPOSITION_INVALID"

    def __init__(self, *, pointer: str, message: str) -> None:
        self.pointer = pointer
        self.repair_scope = pointer
        super().__init__(message)


class CompositionStatus(str, Enum):
    COMPOSED = "composed"
    LEDGER_AMENDMENT_NEEDED = "ledger_amendment_needed"
    VALIDATION_FAILED = "validation_failed"


class CompositionRequestV1(BridgeRecord):
    """Harness-authored, bounded formatting request for one Stage B call."""

    output_target: str = Field(min_length=1, max_length=512)
    formatting_profile: str = Field(
        min_length=1,
        max_length=128,
        pattern=r"^[A-Za-z][A-Za-z0-9_.:-]{0,127}$",
    )
    desired_length_chars: StrictInt = Field(gt=0, le=_MAX_COMPOSITION_TEXT)
    maximum_sections: StrictInt = Field(gt=0, le=_MAX_COMPOSITION_ITEMS)

    @field_validator("output_target")
    @classmethod
    def _target_is_not_blank(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("output_target must contain non-whitespace text")
        return value


class LedgerAmendmentNeededV1(BridgeRecord):
    """New semantics requested from Stage A, with no IDs or grounding refs."""

    requested_class: Literal["supported_inference", "surviving_conjecture"]
    proposed_claim: str = Field(min_length=1, max_length=_MAX_COMPOSITION_TEXT)
    reason: str = Field(min_length=1, max_length=16_384)

    @field_validator("proposed_claim", "reason")
    @classmethod
    def _text_is_not_blank(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("amendment text must contain non-whitespace text")
        return value


class CompositionFailureV1(BridgeRecord):
    code: str = Field(min_length=1, max_length=128, pattern=r"^[A-Z][A-Z0-9_]*$")
    message: str = Field(min_length=1, max_length=16_384)


@dataclass(frozen=True)
class CompositionResultV1:
    """Typed process result retaining every raw/repair attempt receipt."""

    status: CompositionStatus
    output: BridgeOutputV1 | None = None
    amendment_needed: LedgerAmendmentNeededV1 | None = None
    ledger_validation: BridgeValidationReportV1 | None = None
    output_validation: BridgeValidationReportV1 | None = None
    failure: CompositionFailureV1 | None = None
    call_receipt: LLMCall | None = None

    @property
    def successful(self) -> bool:
        return self.status != CompositionStatus.VALIDATION_FAILED

    @property
    def raw_refs(self) -> tuple[str, ...]:
        if self.call_receipt is None:
            return ()
        traced = tuple(
            attempt.raw_ref
            for attempt in self.call_receipt.attempt_trace
            if attempt.raw_ref
        )
        return traced or ((self.call_receipt.raw_ref,) if self.call_receipt.raw_ref else ())

    @property
    def repair_diagnostic_refs(self) -> tuple[str, ...]:
        if self.call_receipt is None:
            return ()
        return tuple(
            attempt.diagnostic_ref
            for attempt in self.call_receipt.attempt_trace
            if attempt.diagnostic_ref
        )


class CompositionSpanWireV1(StrictWireModel):
    span_id: str = Field(pattern=r"^S[1-9][0-9]{0,5}$")
    text: str = Field(min_length=1, max_length=_MAX_COMPOSITION_TEXT)
    rendering_mode: Literal[
        "fact",
        "observation",
        "inference",
        "conjecture",
        "assumption",
        "unknown",
        "conflict",
    ]
    ledger_entry_handles: list[str] = Field(min_length=1, max_length=2_048)

    @field_validator("text")
    @classmethod
    def _span_is_not_blank(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("span text must contain non-whitespace text")
        return value

    @field_validator("ledger_entry_handles")
    @classmethod
    def _handles_are_unique(cls, value: list[str]) -> list[str]:
        if len(value) != len(set(value)):
            raise ValueError("ledger_entry_handles must not contain duplicates")
        return value


class CompositionSpanWireV2(StrictWireModel):
    """v6 span: epistemic rendering is compiler-owned, never model-authored."""

    span_id: str = Field(pattern=r"^S[1-9][0-9]{0,5}$")
    text: str = Field(min_length=1, max_length=_MAX_COMPOSITION_TEXT)
    ledger_entry_handles: list[str] = Field(min_length=1, max_length=2_048)

    @field_validator("text")
    @classmethod
    def _span_is_not_blank(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("span text must contain non-whitespace text")
        return value

    @field_validator("ledger_entry_handles")
    @classmethod
    def _handles_are_unique(cls, value: list[str]) -> list[str]:
        if len(value) != len(set(value)):
            raise ValueError("ledger_entry_handles must not contain duplicates")
        return value



class CompositionUnresolvedWireV1(StrictWireModel):
    description: str = Field(min_length=1, max_length=_MAX_COMPOSITION_TEXT)
    reason: str | None = Field(default=None, min_length=1, max_length=_MAX_COMPOSITION_TEXT)
    ledger_entry_handles: list[str] | None = Field(default=None, max_length=2_048)

    @field_validator("description", "reason")
    @classmethod
    def _text_is_not_blank(cls, value: str | None) -> str | None:
        if value is not None and not value.strip():
            raise ValueError("unresolved text must contain non-whitespace text")
        return value

    @field_validator("ledger_entry_handles")
    @classmethod
    def _handles_are_unique(cls, value: list[str] | None) -> list[str] | None:
        if value is not None and len(value) != len(set(value)):
            raise ValueError("ledger_entry_handles must not contain duplicates")
        return value


class LedgerAmendmentWireV1(StrictWireModel):
    requested_class: Literal["supported_inference", "surviving_conjecture"]
    proposed_claim: str = Field(min_length=1, max_length=_MAX_COMPOSITION_TEXT)
    reason: str = Field(min_length=1, max_length=16_384)

    @field_validator("proposed_claim", "reason")
    @classmethod
    def _text_is_not_blank(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("amendment text must contain non-whitespace text")
        return value


class BridgeCompositionWireV1(StrictWireModel):
    """Exactly one closed Stage B response; never a list of operations."""

    sections: list[CompositionSpanWireV1] = Field(max_length=_MAX_COMPOSITION_ITEMS)
    unresolved_items: list[CompositionUnresolvedWireV1] | None = Field(
        default=None, max_length=_MAX_COMPOSITION_ITEMS
    )
    resolution: Literal[
        "answered",
        "partially_answered",
        "underdetermined",
        "insufficient_evidence",
        "conflicting_evidence",
        "outside_scope",
    ]
    resolution_reason: str | None = Field(
        default=None, min_length=1, max_length=_MAX_COMPOSITION_TEXT
    )
    ledger_amendment_request: LedgerAmendmentWireV1 | None = None

    @field_validator("resolution_reason")
    @classmethod
    def _reason_is_not_blank(cls, value: str | None) -> str | None:
        if value is not None and not value.strip():
            raise ValueError("resolution_reason must contain non-whitespace text")
        return value

    @model_validator(mode="after")
    def _amendment_is_a_distinct_outcome(self):
        if self.ledger_amendment_request is not None:
            if self.sections:
                raise ValueError(
                    "ledger amendment requests cannot smuggle composed sections"
                )
            if self.resolution == "answered":
                raise ValueError("an amendment-needed result cannot be answered")
            if self.resolution_reason is None:
                raise ValueError("an amendment-needed result requires a resolution_reason")
        return self


class BridgeCompositionWireV2(StrictWireModel):
    """v6 composition response with no rendering-mode authority."""

    sections: list[CompositionSpanWireV2] = Field(max_length=_MAX_COMPOSITION_ITEMS)
    unresolved_items: list[CompositionUnresolvedWireV1] | None = Field(
        default=None, max_length=_MAX_COMPOSITION_ITEMS
    )
    resolution: Literal[
        "answered",
        "partially_answered",
        "underdetermined",
        "insufficient_evidence",
        "conflicting_evidence",
        "outside_scope",
    ]
    resolution_reason: str | None = Field(
        default=None, min_length=1, max_length=_MAX_COMPOSITION_TEXT
    )
    ledger_amendment_request: LedgerAmendmentWireV1 | None = None

    @field_validator("resolution_reason")
    @classmethod
    def _reason_is_not_blank(cls, value: str | None) -> str | None:
        if value is not None and not value.strip():
            raise ValueError("resolution_reason must contain non-whitespace text")
        return value

    @model_validator(mode="after")
    def _amendment_is_a_distinct_outcome(self):
        if self.ledger_amendment_request is not None:
            if self.sections:
                raise ValueError(
                    "ledger amendment requests cannot smuggle composed sections"
                )
            if self.resolution == "answered":
                raise ValueError("an amendment-needed result cannot be answered")
            if self.resolution_reason is None:
                raise ValueError("an amendment-needed result requires a resolution_reason")
        return self


class CompositionDraftV1(BridgeRecord):
    """Harness-side result of compiling the compact wire object."""

    output: BridgeOutputV1 | None = None
    amendment_needed: LedgerAmendmentNeededV1 | None = None

    @model_validator(mode="after")
    def _exactly_one_outcome(self):
        if (self.output is None) == (self.amendment_needed is None):
            raise ValueError("composition draft requires exactly one outcome")
        return self


class BridgeCompositionWireContract(WireContract[CompositionDraftV1]):
    """Resolve only call-local handles from one fixed validated ledger."""

    def __init__(
        self,
        ledger: ClaimLedgerV1,
        *,
        maximum_sections: int,
        desired_length_chars: int,
    ) -> None:
        self.ledger = ClaimLedgerV1.model_validate(ledger)
        self.maximum_sections = maximum_sections
        self.desired_length_chars = desired_length_chars
        aliases = AliasTable.from_values([entry.id for entry in ledger.entries], prefix="E")
        handles = tuple(aliases.aliases) or (_HANDLE_SENTINEL,)
        handle_literal = Literal.__getitem__(handles)

        bound_span = create_model(
            "BoundCompositionSpanWireV1",
            __base__=CompositionSpanWireV1,
            ledger_entry_handles=(
                list[handle_literal],
                Field(min_length=1, max_length=2_048),
            ),
        )
        bound_unresolved = create_model(
            "BoundCompositionUnresolvedWireV1",
            __base__=CompositionUnresolvedWireV1,
            ledger_entry_handles=(
                list[handle_literal] | None,
                Field(default=None, max_length=2_048),
            ),
        )
        bound_wire = create_model(
            "BoundBridgeCompositionWireV1",
            __base__=BridgeCompositionWireV1,
            sections=(
                list[bound_span],
                Field(max_length=maximum_sections),
            ),
            unresolved_items=(
                list[bound_unresolved] | None,
                Field(default=None, max_length=maximum_sections),
            ),
        )
        super().__init__(
            "bridge.compose.compact.v1",
            bound_wire,
            CompositionDraftV1,
            aliases=aliases,
            variant="compact",
        )

    def _resolve(self, handles: list[str] | None) -> list[str] | None:
        if handles is None:
            return None
        return [self.aliases.resolve(handle) for handle in handles]

    def compile(self, wire: BridgeCompositionWireV1) -> CompositionDraftV1:
        if wire.ledger_amendment_request is not None:
            request = wire.ledger_amendment_request
            return CompositionDraftV1(
                amendment_needed=LedgerAmendmentNeededV1(
                    requested_class=request.requested_class,
                    proposed_claim=request.proposed_claim,
                    reason=request.reason,
                )
            )

        total_chars = sum(len(section.text) for section in wire.sections)
        total_chars += sum(
            len(item.description) + len(item.reason or "")
            for item in wire.unresolved_items or []
        )
        total_chars += len(wire.resolution_reason or "")
        if total_chars > self.desired_length_chars:
            raise ValueError(
                "composition exceeds the harness-authored desired_length_chars bound"
            )

        sections = [
            ClaimUseV1.create(
                span_id=section.span_id,
                text=section.text,
                rendering_mode=RenderingMode(section.rendering_mode),
                ledger_entry_ids=self._resolve(section.ledger_entry_handles),
            )
            for section in wire.sections
        ]
        unresolved_items = (
            [
                UnresolvedItemV1.create(
                    description=item.description,
                    reason=item.reason,
                    ledger_entry_ids=self._resolve(item.ledger_entry_handles),
                )
                for item in wire.unresolved_items
            ]
            if wire.unresolved_items is not None
            else None
        )
        output = BridgeOutputV1.create(
            claim_ledger_id=self.ledger.id,
            sections=sections,
            unresolved_items=unresolved_items,
            resolution=BridgeResolution(wire.resolution),
            resolution_reason=wire.resolution_reason,
        )
        report = validate_bridge_output(self.ledger, output)
        if not report.valid:
            first = report.findings[0]
            pointer = first.pointer
            if pointer is None and first.span_id is not None:
                section_index = next(
                    (
                        index
                        for index, section in enumerate(wire.sections)
                        if section.span_id == first.span_id
                    ),
                    None,
                )
                if section_index is not None:
                    pointer = f"/sections/{section_index}/rendering_mode"
            pointer = pointer or ""
            location = pointer or first.span_id or "/"
            raise CompositionContractError(
                pointer=pointer,
                message=f"{first.code} at {location}: {first.message}",
            )
        return CompositionDraftV1(output=output)


_RENDERING_PRECEDENCE = (
    RenderingMode.CONFLICT,
    RenderingMode.UNKNOWN,
    RenderingMode.ASSUMPTION,
    RenderingMode.CONJECTURE,
    RenderingMode.INFERENCE,
    RenderingMode.OBSERVATION,
    RenderingMode.FACT,
)
_MODE_FOR_CLASS = {
    "conflict": RenderingMode.CONFLICT,
    "unknown": RenderingMode.UNKNOWN,
    "assumption": RenderingMode.ASSUMPTION,
    "surviving_conjecture": RenderingMode.CONJECTURE,
    "supported_inference": RenderingMode.INFERENCE,
    "recorded_observation": RenderingMode.OBSERVATION,
    "source_fact": RenderingMode.FACT,
}


class BridgeCompositionWireContractV2(BridgeCompositionWireContract):
    """v6 Stage B contract deriving the weakest mode from ledger classes."""

    def __init__(
        self,
        ledger: ClaimLedgerV1,
        *,
        maximum_sections: int,
        desired_length_chars: int,
    ) -> None:
        super().__init__(
            ledger,
            maximum_sections=maximum_sections,
            desired_length_chars=desired_length_chars,
        )
        handles = tuple(self.aliases.aliases) or (_HANDLE_SENTINEL,)
        handle_literal = Literal.__getitem__(handles)
        bound_span = create_model(
            "BoundCompositionSpanWireV2",
            __base__=CompositionSpanWireV2,
            ledger_entry_handles=(
                list[handle_literal],
                Field(min_length=1, max_length=2_048),
            ),
        )
        bound_unresolved = create_model(
            "BoundCompositionUnresolvedWireV2",
            __base__=CompositionUnresolvedWireV1,
            ledger_entry_handles=(
                list[handle_literal] | None,
                Field(default=None, max_length=2_048),
            ),
        )
        self.wire_model = create_model(
            "BoundBridgeCompositionWireV2",
            __base__=BridgeCompositionWireV2,
            sections=(list[bound_span], Field(max_length=maximum_sections)),
            unresolved_items=(
                list[bound_unresolved] | None,
                Field(default=None, max_length=maximum_sections),
            ),
        )
        self.contract_id = "bridge.composition.v2"

    def _derived_mode(self, entry_ids: list[str]) -> RenderingMode:
        by_id = {entry.id: entry for entry in self.ledger.entries}
        modes = [_MODE_FOR_CLASS[by_id[entry_id].claim_class.value] for entry_id in entry_ids]
        return min(modes, key=_RENDERING_PRECEDENCE.index)

    def compile(self, wire: BridgeCompositionWireV2) -> CompositionDraftV1:
        if wire.ledger_amendment_request is not None:
            request = wire.ledger_amendment_request
            return CompositionDraftV1(
                amendment_needed=LedgerAmendmentNeededV1(
                    requested_class=request.requested_class,
                    proposed_claim=request.proposed_claim,
                    reason=request.reason,
                )
            )
        total_chars = sum(len(section.text) for section in wire.sections)
        total_chars += sum(
            len(item.description) + len(item.reason or "")
            for item in wire.unresolved_items or []
        )
        total_chars += len(wire.resolution_reason or "")
        if total_chars > self.desired_length_chars:
            raise ValueError(
                "composition exceeds the harness-authored desired_length_chars bound"
            )

        entries = {entry.id: entry for entry in self.ledger.entries}
        sections = []
        for index, section in enumerate(wire.sections):
            entry_ids = self._resolve(section.ledger_entry_handles) or []
            process_entries = [
                entries[entry_id]
                for entry_id in entry_ids
                if entries[entry_id].process_observation_refs
            ]
            if process_entries:
                if len(entry_ids) != 1 or len(process_entries) != 1:
                    raise CompositionContractError(
                        pointer=f"/sections/{index}/ledger_entry_handles",
                        message=(
                            "process observations must occupy an exact, standalone span"
                        ),
                    )
                if section.text != process_entries[0].claim:
                    raise CompositionContractError(
                        pointer=f"/sections/{index}/text",
                        message=(
                            "process-observation spans must reproduce the exact "
                            "harness-authored status statement"
                        ),
                    )
            sections.append(
                ClaimUseV1.create(
                    span_id=section.span_id,
                    text=section.text,
                    rendering_mode=self._derived_mode(entry_ids),
                    ledger_entry_ids=entry_ids,
                )
            )
        unresolved_items = (
            [
                UnresolvedItemV1.create(
                    description=item.description,
                    reason=item.reason,
                    ledger_entry_ids=self._resolve(item.ledger_entry_handles),
                )
                for item in wire.unresolved_items
            ]
            if wire.unresolved_items is not None
            else None
        )
        output = BridgeOutputV1.create(
            claim_ledger_id=self.ledger.id,
            sections=sections,
            unresolved_items=unresolved_items,
            resolution=BridgeResolution(wire.resolution),
            resolution_reason=wire.resolution_reason,
        )
        report = validate_bridge_output(
            self.ledger,
            output,
            allow_conservative_mixed_modes=True,
        )
        if not report.valid:
            first = report.findings[0]
            raise CompositionContractError(
                pointer=first.pointer or "",
                message=f"{first.code}: {first.message}",
            )
        return CompositionDraftV1(output=output)


class BridgeCompositionBatchWireContractV1(BridgeCompositionWireContractV2):
    """Separately qualified bounded-ledger child of composition v2."""

    MAXIMUM_BATCH_ENTRIES = 8

    def __init__(
        self,
        ledger: ClaimLedgerV1,
        *,
        maximum_sections: int,
        desired_length_chars: int,
    ) -> None:
        if not 1 <= len(ledger.entries) <= self.MAXIMUM_BATCH_ENTRIES:
            raise ValueError(
                "bridge.composition-batch.v1 requires one through eight ledger entries"
            )
        super().__init__(
            ledger,
            maximum_sections=maximum_sections,
            desired_length_chars=desired_length_chars,
        )
        self.contract_id = "bridge.composition-batch.v1"


def _composition_pack(
    ledger: ClaimLedgerV1,
    request: CompositionRequestV1,
    *,
    contract_version: Literal["v1", "v2"] = "v1",
) -> str:
    aliases = AliasTable.from_values([entry.id for entry in ledger.entries], prefix="E")
    reverse = {canonical: alias for alias, canonical in aliases.aliases.items()}
    entries = []
    for alias, entry in zip(aliases.aliases, ledger.entries, strict=True):
        entries.append(
            {
                "handle": alias,
                "class": entry.claim_class.value,
                "claim": entry.claim,
                "qualification": entry.qualification,
                "premise_handles": [
                    reverse[premise]
                    for premise in entry.premise_refs or []
                    if premise in reverse
                ],
            }
        )
    uncovered = [
        {"requirement": item.requirement, "reason": item.reason}
        for item in ledger.uncovered_requirements or []
    ]
    payload = {
        "task": "compose_one_grounded_output",
        "output_target": request.output_target,
        "formatting_profile": request.formatting_profile,
        "desired_length_chars": request.desired_length_chars,
        "maximum_sections": request.maximum_sections,
        "ledger_entries": entries,
        "uncovered_requirements": uncovered,
    }
    rules = (
        "The following is the complete validated claim ledger available to Stage B.\n"
        "Use only E-handles shown below. Rewording may preserve ledger meaning, but "
        "do not add facts, observations, premises, inferences, conjectures, sources, "
        "or evidence. If a new inference or conjecture is genuinely required, return "
        "ledger_amendment_request and no sections. Missing answers remain missing."
    )
    if contract_version == "v2":
        rules += (
            " Do not author rendering_mode; the compiler derives the weakest mode "
            "from every referenced ledger class. Process observations may be used "
            "only as an exact standalone status statement."
        )
    return rules + "\n\n" + json.dumps(payload, sort_keys=True, ensure_ascii=False)


class BridgeComposer:
    """Execute one Stage B call through the repository's bounded repair kernel."""

    def __init__(
        self,
        adapter,
        *,
        role: str = "thesis",
        contract_version: Literal["v1", "v2"] = "v1",
    ) -> None:
        if role not in _COMPOSER_ROLES:
            raise ValueError("bridge composer role must be thesis or summarizer")
        if contract_version not in {"v1", "v2"}:
            raise ValueError("bridge composition contract_version must be v1 or v2")
        self.adapter = adapter
        self.role = role
        self.contract_version = contract_version

    def compose(
        self,
        ledger: ClaimLedgerV1,
        request: CompositionRequestV1,
    ) -> CompositionResultV1:
        ledger = ClaimLedgerV1.model_validate(ledger)
        request = CompositionRequestV1.model_validate(request)
        ledger_report = validate_claim_ledger(ledger)
        if not ledger_report.valid:
            return CompositionResultV1(
                status=CompositionStatus.VALIDATION_FAILED,
                ledger_validation=ledger_report,
                failure=CompositionFailureV1(
                    code="BRIDGE_LEDGER_INVALID",
                    message="Stage B requires a valid claim ledger.",
                ),
            )
        if request.output_target != ledger.output_target:
            return CompositionResultV1(
                status=CompositionStatus.VALIDATION_FAILED,
                ledger_validation=ledger_report,
                failure=CompositionFailureV1(
                    code="BRIDGE_OUTPUT_TARGET_MISMATCH",
                    message="composition target does not match the validated ledger",
                ),
            )

        contract_type = (
            BridgeCompositionWireContractV2
            if self.contract_version == "v2"
            else BridgeCompositionWireContract
        )
        contract = contract_type(
            ledger,
            maximum_sections=request.maximum_sections,
            desired_length_chars=request.desired_length_chars,
        )
        try:
            draft, call = self.adapter.call(
                self.role,
                _composition_pack(
                    ledger,
                    request,
                    contract_version=self.contract_version,
                ),
                CompositionDraftV1,
                template_role="bridge_compose",
                wire_contract=contract,
            )
        except SchemaRepairError as error:
            staged = getattr(self.adapter, "staged_composition_fallback", None)
            if staged is not None and self.contract_version == "v2":
                output, call = staged(error, ledger, request)
                return CompositionResultV1(
                    status=CompositionStatus.COMPOSED,
                    output=output,
                    ledger_validation=ledger_report,
                    output_validation=validate_bridge_output(
                        ledger, output, allow_conservative_mixed_modes=True
                    ),
                    call_receipt=call,
                )
            return CompositionResultV1(
                status=CompositionStatus.VALIDATION_FAILED,
                ledger_validation=ledger_report,
                failure=CompositionFailureV1(
                    code="BRIDGE_COMPOSITION_REPAIR_EXHAUSTED",
                    message=str(error)[:16_384],
                ),
                call_receipt=error.spend,
            )

        if draft.amendment_needed is not None:
            return CompositionResultV1(
                status=CompositionStatus.LEDGER_AMENDMENT_NEEDED,
                amendment_needed=draft.amendment_needed,
                ledger_validation=ledger_report,
                call_receipt=call,
            )

        assert draft.output is not None
        output_report = validate_bridge_output(
            ledger,
            draft.output,
            allow_conservative_mixed_modes=self.contract_version == "v2",
        )
        if not output_report.valid:
            return CompositionResultV1(
                status=CompositionStatus.VALIDATION_FAILED,
                ledger_validation=ledger_report,
                output_validation=output_report,
                failure=CompositionFailureV1(
                    code="BRIDGE_COMPOSITION_INVALID",
                    message="compiled output failed deterministic bridge validation",
                ),
                call_receipt=call,
            )
        return CompositionResultV1(
            status=CompositionStatus.COMPOSED,
            output=draft.output,
            ledger_validation=ledger_report,
            output_validation=output_report,
            call_receipt=call,
        )


__all__ = [
    "BridgeComposer",
    "BridgeCompositionWireContract",
    "BridgeCompositionWireContractV2",
    "BridgeCompositionBatchWireContractV1",
    "BridgeCompositionWireV1",
    "BridgeCompositionWireV2",
    "CompositionSpanWireV2",
    "CompositionDraftV1",
    "CompositionFailureV1",
    "CompositionRequestV1",
    "CompositionResultV1",
    "CompositionStatus",
    "LedgerAmendmentNeededV1",
]
