"""Deterministic orchestration for the two-stage grounded-output bridge.

The workflow owns sequencing, validation, bounded amendment/repair loops, and
process accounting.  Model adapters can author only the compact Stage A,
Stage B, review, and repair contracts implemented in the neighbouring
modules.  Persistence is injected through one narrow batch sink so this module
never creates a second object store or event log.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from deepreason.bridge.compose import (
    BridgeComposer,
    CompositionRequestV1,
    CompositionStatus,
)
from deepreason.bridge.events import BridgeAction
from deepreason.bridge.ledger import (
    ClaimLedgerInputCatalogV1,
    ClaimLedgerInputCatalogV3,
    ClaimLedgerStageAResultV1,
    amend_claim_ledger_stage_a,
    build_claim_ledger_stage_a,
)
from deepreason.bridge.models import (
    BridgeOutputV1,
    BridgeValidationReportV1,
    ClaimLedgerV1,
    GroundingReviewV1,
)
from deepreason.bridge.repair import GroundingRepairService, RepairDisposition
from deepreason.bridge.review import GroundingReviewService
from deepreason.bridge.validate import validate_bridge_output
from deepreason.ontology.event import LLMCall
from deepreason.ontology.frozen import FrozenList, FrozenRecord


_ERROR_CODE = re.compile(r"^[A-Z][A-Z0-9_]{0,127}$")


class BridgeWorkflowPolicy(FrozenRecord):
    """Frozen execution limits supplied by the harness/RunManifest boundary."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    grounding_review: bool = True
    max_ledger_amendments: Literal[0, 1] = 1
    max_grounding_repair_attempts: int = Field(default=4, ge=0, le=8)
    ledger_role: Literal["summarizer"] = "summarizer"
    ledger_contract_version: Literal["v1", "v2", "v3"] = "v1"
    composition_contract_version: Literal["v1", "v2"] = "v1"
    composer_role: Literal["thesis", "summarizer"] = "thesis"
    reviewer_role: Literal["judge", "grounding_reviewer"] = "judge"

    @model_validator(mode="after")
    def _v6_contract_pair(self):
        if (self.ledger_contract_version == "v3") != (
            self.composition_contract_version == "v2"
        ):
            raise ValueError(
                "bridge.ledger.v3 and bridge.composition.v2 must be selected together"
            )
        return self


@dataclass(frozen=True)
class BridgePersistenceBatch:
    """One append-only bridge event plus canonical objects created by it."""

    action: BridgeAction
    inputs: tuple[str, ...] = ()
    records: tuple[tuple[str, BaseModel], ...] = ()
    llm: LLMCall | None = None
    finding_ref: str | None = None
    error_code: str | None = None
    error_message: str | None = None
    failure_phase: str | None = None
    failure_diagnostics: tuple[BaseModel, ...] = ()
    actor: str = "harness"


class BridgeWorkflowResultV1(FrozenRecord):
    """Typed terminal result; unresolved epistemic resolutions are successes."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    schema_: Literal["bridge.workflow-result.v1"] = Field(
        "bridge.workflow-result.v1", alias="schema"
    )
    process_status: Literal["success", "failure"]
    phase: str = Field(min_length=1, max_length=128)
    formal_seq: int = Field(ge=0)
    claim_ledger: ClaimLedgerV1 | None = None
    bridge_output: BridgeOutputV1 | None = None
    validation_report: BridgeValidationReportV1 | None = None
    grounded_review: GroundingReviewV1 | None = None
    amendment_count: int = Field(default=0, ge=0, le=1)
    event_count: int = Field(default=0, ge=0)
    model_call_count: int = Field(default=0, ge=0)
    token_count: int = Field(default=0, ge=0)
    model_calls: list[LLMCall] = Field(default_factory=FrozenList)
    error_code: str | None = None
    error_message: str | None = Field(default=None, max_length=16_384)

    @field_validator("model_calls", mode="after")
    @classmethod
    def _freeze_calls(cls, value):
        return FrozenList(value)

    @field_validator("error_code")
    @classmethod
    def _valid_error_code(cls, value):
        if value is not None and _ERROR_CODE.fullmatch(value) is None:
            raise ValueError("error_code must be a stable uppercase identifier")
        return value

    @model_validator(mode="after")
    def _terminal_shape(self):
        if self.process_status == "success":
            if self.error_code is not None or self.error_message is not None:
                raise ValueError("successful workflow result cannot carry an error")
            if (
                self.claim_ledger is None
                or self.bridge_output is None
                or self.validation_report is None
                or not self.validation_report.valid
            ):
                raise ValueError("success requires a ledger, output, and valid report")
            if self.bridge_output.claim_ledger_id != self.claim_ledger.id:
                raise ValueError("terminal bridge output must name the terminal ledger")
            if self.validation_report.bridge_output_id != self.bridge_output.id:
                raise ValueError("terminal validation report must name the output")
        elif self.error_code is None or self.error_message is None:
            raise ValueError("failed workflow result requires a typed error")
        if self.model_call_count != len(self.model_calls):
            raise ValueError("model_call_count must equal the retained call receipts")
        if self.token_count != sum(call.tokens for call in self.model_calls):
            raise ValueError("token_count must equal the retained call receipts")
        return self

    @property
    def successful(self) -> bool:
        return self.process_status == "success"


def _ledger_records(
    result: ClaimLedgerStageAResultV1,
    *,
    include_catalog: bool,
) -> tuple[tuple[str, BaseModel], ...]:
    ledger = result.ledger
    records: list[tuple[str, BaseModel]] = []
    if include_catalog:
        records.append(("bridge-ledger-input-catalog", result.catalog))
    records.extend(("bridge-ledger-entry", entry) for entry in ledger.entries)
    records.extend(
        ("bridge-uncovered-requirement", item)
        for item in ledger.uncovered_requirements or ()
    )
    records.extend(
        ("bridge-source-conflict", item) for item in ledger.source_conflicts or ()
    )
    records.append(("bridge-claim-ledger", ledger))
    return tuple(records)


def _validation_records(
    report: BridgeValidationReportV1,
) -> tuple[tuple[str, BaseModel], ...]:
    return (
        *(("bridge-validation-finding", item) for item in report.findings),
        ("bridge-validation-report", report),
    )


def _output_records(output: BridgeOutputV1) -> tuple[tuple[str, BaseModel], ...]:
    return (
        *(("bridge-claim-use", item) for item in output.sections),
        *(("bridge-unresolved-item", item) for item in output.unresolved_items or ()),
        ("bridge-output", output),
    )


def _review_records(review: GroundingReviewV1) -> tuple[tuple[str, BaseModel], ...]:
    return (
        *(("bridge-grounding-finding", item) for item in review.findings),
        ("bridge-grounding-review", review),
    )


def _stable_error_code(error: Exception, default: str) -> str:
    candidate = str(getattr(error, "code", "") or "")
    return candidate if _ERROR_CODE.fullmatch(candidate) else default


def _error_calls(error: Exception) -> list[LLMCall]:
    calls = list(getattr(error, "calls", ()) or ())
    spend = getattr(error, "spend", None)
    if spend is not None and spend not in calls:
        calls.append(spend)
    return calls


def _stage_a_failure_error(failure) -> RuntimeError:
    """Convert the typed Stage A diagnostic into a stable terminal error."""

    error = RuntimeError(failure.message)
    error.code = failure.code  # type: ignore[attr-defined]
    return error


class BridgeWorkflow:
    """Run Stage A then Stage B, with optional review and bounded repair."""

    def __init__(
        self,
        stage_a_adapter,
        composition_adapter,
        *,
        review_adapter=None,
        repair_adapter=None,
        policy: BridgeWorkflowPolicy | dict | None = None,
        sink=None,
    ) -> None:
        self.policy = BridgeWorkflowPolicy.model_validate(policy or {})
        if self.policy.grounding_review and review_adapter is None:
            raise ValueError("grounding_review requires a review adapter")
        if (
            self.policy.grounding_review
            and self.policy.max_grounding_repair_attempts
            and repair_adapter is None
        ):
            raise ValueError("grounding repair attempts require a repair adapter")
        self.stage_a_adapter = stage_a_adapter
        self.composition_adapter = composition_adapter
        self.review_adapter = review_adapter
        self.repair_adapter = repair_adapter
        self.sink = sink
        self._batches: list[BridgePersistenceBatch] = []
        self._calls: list[LLMCall] = []

    def _persist(self, batch: BridgePersistenceBatch) -> None:
        self._batches.append(batch)
        if self.sink is None:
            return
        method = getattr(self.sink, "persist_bridge_batch", None)
        if method is not None:
            method(batch)
        elif callable(self.sink):
            self.sink(batch)
        else:
            raise TypeError("bridge sink must be callable or expose persist_bridge_batch")

    def _record_call(self, call: LLMCall | None) -> None:
        if call is not None:
            self._calls.append(call)

    def _record_adapter_calls(self, adapter, fallback_call: LLMCall | None) -> None:
        consume = getattr(adapter, "consume_staged_calls", None)
        calls = consume(fallback_call) if consume is not None else ((fallback_call,) if fallback_call else ())
        for call in calls:
            self._record_call(call)

    @staticmethod
    def _finalize_adapter_effect(adapter, effect_ref: str) -> None:
        finalize = getattr(adapter, "finalize_staged_effect", None)
        if finalize is not None:
            finalize(effect_ref)

    def _result(
        self,
        *,
        process_status: Literal["success", "failure"],
        phase: str,
        formal_seq: int,
        ledger: ClaimLedgerV1 | None,
        output: BridgeOutputV1 | None,
        report: BridgeValidationReportV1 | None,
        review: GroundingReviewV1 | None,
        amendment_count: int,
        error_code: str | None = None,
        error_message: str | None = None,
    ) -> BridgeWorkflowResultV1:
        return BridgeWorkflowResultV1(
            process_status=process_status,
            phase=phase,
            formal_seq=formal_seq,
            claim_ledger=ledger,
            bridge_output=output,
            validation_report=report,
            grounded_review=review,
            amendment_count=amendment_count,
            event_count=len(self._batches),
            model_call_count=len(self._calls),
            token_count=sum(call.tokens for call in self._calls),
            model_calls=self._calls,
            error_code=error_code,
            error_message=error_message,
        )

    def _failure(
        self,
        error: Exception,
        *,
        default_code: str,
        formal_seq: int,
        phase: str,
        ledger: ClaimLedgerV1 | None = None,
        output: BridgeOutputV1 | None = None,
        report: BridgeValidationReportV1 | None = None,
        review: GroundingReviewV1 | None = None,
        amendment_count: int = 0,
        inputs: tuple[str, ...] = (),
        calls: list[LLMCall] | None = None,
        diagnostics: tuple[BaseModel, ...] = (),
    ) -> BridgeWorkflowResultV1:
        error_code = _stable_error_code(error, default_code)
        message = (str(error).strip() or error_code)[:16_384]
        failed_calls = _error_calls(error) if calls is None else calls
        for call in failed_calls:
            self._record_call(call)
        # A terminal failure event owns at most one otherwise-unrecorded call.
        # Multi-call review failures are emitted as attempt events before here.
        terminal_call = failed_calls[0] if len(failed_calls) == 1 else None
        terminal_inputs = tuple(
            item.id
            for item in (ledger, output, report, review)
            if item is not None
        )
        if not set(inputs).issubset(set(terminal_inputs)):
            raise RuntimeError("bridge failure inputs are not retained partial objects")
        self._persist(
            BridgePersistenceBatch(
                action=BridgeAction.FAILED,
                inputs=terminal_inputs,
                llm=terminal_call,
                error_code=error_code,
                error_message=message,
                failure_phase=phase,
                failure_diagnostics=diagnostics,
            )
        )
        return self._result(
            process_status="failure",
            phase=phase,
            formal_seq=formal_seq,
            ledger=ledger,
            output=output,
            report=report,
            review=review,
            amendment_count=amendment_count,
            error_code=error_code,
            error_message=message,
        )

    def _review(
        self,
        ledger: ClaimLedgerV1,
        output: BridgeOutputV1,
        *,
        materials,
    ):
        service = GroundingReviewService(
            self.review_adapter,
            role=self.policy.reviewer_role,
            max_spans=max(1, min(128, len(output.sections) or 1)),
            allow_conservative_mixed_modes=(
                self.policy.composition_contract_version == "v2"
            ),
        )
        result = service.review(ledger, output, materials=materials)
        attempt_inputs = (ledger.id, output.id)
        for call in result.calls:
            self._record_call(call)
            self._persist(
                BridgePersistenceBatch(
                    action=BridgeAction.GROUNDED_REVIEW_ATTEMPTED,
                    inputs=attempt_inputs,
                    llm=call,
                )
            )
        self._persist(
            BridgePersistenceBatch(
                action=BridgeAction.GROUNDED_REVIEWED,
                inputs=attempt_inputs,
                records=_review_records(result.review),
                finding_ref=result.review.id,
            )
        )
        return result.review

    def run(
        self,
        catalog: ClaimLedgerInputCatalogV1 | ClaimLedgerInputCatalogV3,
        composition_request: CompositionRequestV1,
        *,
        materials=None,
    ) -> BridgeWorkflowResultV1:
        """Execute one bounded bridge workflow against a fixed input catalog."""

        if self._batches or self._calls:
            raise RuntimeError("a BridgeWorkflow instance can run only once")
        catalog = (
            ClaimLedgerInputCatalogV3.model_validate(catalog)
            if isinstance(catalog, ClaimLedgerInputCatalogV3)
            or (
                isinstance(catalog, dict)
                and catalog.get("schema") == "bridge.catalog.v3"
            )
            else ClaimLedgerInputCatalogV1.model_validate(catalog)
        )
        request = CompositionRequestV1.model_validate(composition_request)
        materials = {} if materials is None else materials
        formal_seq = catalog.formal_seq
        amendment_count = 0
        ledger: ClaimLedgerV1 | None = None
        output: BridgeOutputV1 | None = None
        report: BridgeValidationReportV1 | None = None
        review: GroundingReviewV1 | None = None

        try:
            stage_a = build_claim_ledger_stage_a(
                self.stage_a_adapter,
                catalog,
                role=self.policy.ledger_role,
                contract_version=self.policy.ledger_contract_version,
            )
        except Exception as error:
            return self._failure(
                error,
                default_code="BRIDGE_STAGE_A_FAILED",
                formal_seq=formal_seq,
                phase="stage_a",
            )
        ledger = stage_a.ledger
        stage_a_call = stage_a.receipt.llm_call
        if stage_a.failure is None:
            self._record_adapter_calls(self.stage_a_adapter, stage_a_call)
        self._persist(
            BridgePersistenceBatch(
                action=BridgeAction.LEDGER_CREATED,
                records=_ledger_records(stage_a, include_catalog=True),
                llm=stage_a_call if stage_a.failure is None else None,
            )
        )
        if stage_a.failure is None:
            self._finalize_adapter_effect(self.stage_a_adapter, ledger.id)
        self._persist(
            BridgePersistenceBatch(
                action=BridgeAction.LEDGER_VALIDATED,
                inputs=(ledger.id,),
                records=_validation_records(stage_a.validation_report),
                finding_ref=stage_a.validation_report.id,
            )
        )
        if stage_a.failure is not None:
            return self._failure(
                _stage_a_failure_error(stage_a.failure),
                default_code=stage_a.failure.code,
                formal_seq=formal_seq,
                phase="stage_a",
                ledger=ledger,
                report=stage_a.validation_report,
                inputs=(ledger.id, stage_a.validation_report.id),
                calls=[stage_a_call] if stage_a_call is not None else [],
                diagnostics=(stage_a.failure,),
            )

        while True:
            try:
                composition = BridgeComposer(
                    self.composition_adapter,
                    role=self.policy.composer_role,
                    contract_version=self.policy.composition_contract_version,
                ).compose(ledger, request)
            except Exception as error:
                return self._failure(
                    error,
                    default_code="BRIDGE_COMPOSITION_FAILED",
                    formal_seq=formal_seq,
                    phase="stage_b",
                    ledger=ledger,
                    amendment_count=amendment_count,
                    inputs=(ledger.id,),
                )
            if composition.status == CompositionStatus.VALIDATION_FAILED:
                error = RuntimeError(
                    composition.failure.message
                    if composition.failure is not None
                    else "Stage B validation failed"
                )
                error.code = (  # type: ignore[attr-defined]
                    composition.failure.code
                    if composition.failure is not None
                    else "BRIDGE_COMPOSITION_INVALID"
                )
                return self._failure(
                    error,
                    default_code="BRIDGE_COMPOSITION_INVALID",
                    formal_seq=formal_seq,
                    phase="stage_b",
                    ledger=ledger,
                    amendment_count=amendment_count,
                    inputs=(ledger.id,),
                    calls=(
                        [composition.call_receipt]
                        if composition.call_receipt is not None
                        else []
                    ),
                )
            if composition.status == CompositionStatus.LEDGER_AMENDMENT_NEEDED:
                call = composition.call_receipt
                self._record_call(call)
                self._persist(
                    BridgePersistenceBatch(
                        action=BridgeAction.LEDGER_AMENDMENT_REQUESTED,
                        inputs=(ledger.id,),
                        llm=call,
                    )
                )
                if amendment_count >= self.policy.max_ledger_amendments:
                    return self._failure(
                        RuntimeError("bounded ledger-amendment limit reached"),
                        default_code="BRIDGE_LEDGER_AMENDMENT_LIMIT",
                        formal_seq=formal_seq,
                        phase="ledger_amendment",
                        ledger=ledger,
                        amendment_count=amendment_count,
                        inputs=(ledger.id,),
                        calls=[],
                    )
                assert composition.amendment_needed is not None
                try:
                    amended = amend_claim_ledger_stage_a(
                        self.stage_a_adapter,
                        stage_a,
                        request=composition.amendment_needed,
                        role=self.policy.ledger_role,
                        contract_version=self.policy.ledger_contract_version,
                    )
                except Exception as error:
                    return self._failure(
                        error,
                        default_code="BRIDGE_LEDGER_AMENDMENT_FAILED",
                        formal_seq=formal_seq,
                        phase="ledger_amendment",
                        ledger=ledger,
                        amendment_count=amendment_count,
                        inputs=(ledger.id,),
                    )
                prior = ledger
                stage_a = amended
                ledger = amended.ledger
                amendment_count += 1
                amendment_call = amended.receipt.llm_call
                if amended.failure is not None:
                    self._persist(
                        BridgePersistenceBatch(
                            action=BridgeAction.LEDGER_AMENDMENT_ATTEMPTED,
                            inputs=(prior.id,),
                        )
                    )
                    return self._failure(
                        _stage_a_failure_error(amended.failure),
                        default_code=amended.failure.code,
                        formal_seq=formal_seq,
                        phase="ledger_amendment",
                        ledger=ledger,
                        report=amended.validation_report,
                        amendment_count=amendment_count,
                        inputs=(ledger.id, amended.validation_report.id),
                        calls=(
                            [amendment_call]
                            if amendment_call is not None
                            else []
                        ),
                        diagnostics=(amended.failure,),
                    )
                self._record_call(amendment_call)
                if not amended.amended:
                    self._persist(
                        BridgePersistenceBatch(
                            action=BridgeAction.LEDGER_AMENDMENT_ATTEMPTED,
                            inputs=(prior.id,),
                            llm=amendment_call,
                        )
                    )
                    continue
                self._persist(
                    BridgePersistenceBatch(
                        action=BridgeAction.LEDGER_AMENDED,
                        inputs=(prior.id,),
                        records=_ledger_records(amended, include_catalog=False),
                        llm=amendment_call,
                    )
                )
                self._persist(
                    BridgePersistenceBatch(
                        action=BridgeAction.LEDGER_VALIDATED,
                        inputs=(ledger.id,),
                        records=_validation_records(amended.validation_report),
                        finding_ref=amended.validation_report.id,
                    )
                )
                continue

            assert composition.output is not None
            assert composition.output_validation is not None
            output = composition.output
            report = composition.output_validation
            self._record_adapter_calls(
                self.composition_adapter, composition.call_receipt
            )
            self._persist(
                BridgePersistenceBatch(
                    action=BridgeAction.OUTPUT_COMPOSED,
                    inputs=(ledger.id,),
                    records=_output_records(output),
                    llm=composition.call_receipt,
                )
            )
            self._finalize_adapter_effect(self.composition_adapter, output.id)
            self._persist(
                BridgePersistenceBatch(
                    action=BridgeAction.OUTPUT_VALIDATED,
                    inputs=(ledger.id, output.id),
                    records=_validation_records(report),
                    finding_ref=report.id,
                )
            )
            break

        if self.policy.grounding_review:
            repair_calls = 0
            while True:
                try:
                    review = self._review(ledger, output, materials=materials)
                except Exception as error:
                    calls = _error_calls(error)
                    for call in calls:
                        self._record_call(call)
                        self._persist(
                            BridgePersistenceBatch(
                                action=BridgeAction.GROUNDED_REVIEW_ATTEMPTED,
                                inputs=(ledger.id, output.id),
                                llm=call,
                            )
                        )
                    return self._failure(
                        error,
                        default_code="BRIDGE_GROUNDING_REVIEW_FAILED",
                        formal_seq=formal_seq,
                        phase="grounded_review",
                        ledger=ledger,
                        output=output,
                        report=report,
                        amendment_count=amendment_count,
                        inputs=(ledger.id, output.id),
                        calls=[],
                    )
                if review.passed:
                    break
                remaining = self.policy.max_grounding_repair_attempts - repair_calls
                if remaining <= 0:
                    return self._failure(
                        RuntimeError("grounding review remained unresolved after bounded repair"),
                        default_code="BRIDGE_GROUNDING_REPAIR_EXHAUSTED",
                        formal_seq=formal_seq,
                        phase="grounding_repair",
                        ledger=ledger,
                        output=output,
                        report=report,
                        review=review,
                        amendment_count=amendment_count,
                        inputs=(ledger.id, output.id, review.id),
                        calls=[],
                    )
                try:
                    repaired = GroundingRepairService(
                        self.repair_adapter,
                        role=self.policy.reviewer_role,
                        max_attempts=remaining,
                        allow_conservative_mixed_modes=(
                            self.policy.composition_contract_version == "v2"
                        ),
                    ).repair(ledger, output, review)
                except Exception as error:
                    return self._failure(
                        error,
                        default_code="BRIDGE_GROUNDING_REPAIR_FAILED",
                        formal_seq=formal_seq,
                        phase="grounding_repair",
                        ledger=ledger,
                        output=output,
                        report=report,
                        review=review,
                        amendment_count=amendment_count,
                        inputs=(ledger.id, output.id, report.id, review.id),
                    )
                for call in repaired.calls:
                    repair_calls += 1
                    self._record_call(call)
                    self._persist(
                        BridgePersistenceBatch(
                            action=BridgeAction.REPAIR_ATTEMPTED,
                            inputs=(ledger.id, output.id, review.id),
                            llm=call,
                            finding_ref=review.id,
                        )
                    )
                prior_output = output
                output = repaired.output
                self._persist(
                    BridgePersistenceBatch(
                        action=BridgeAction.REPAIR_ATTEMPTED,
                        inputs=(ledger.id, prior_output.id, review.id),
                        records=_output_records(output),
                        finding_ref=review.id,
                    )
                )
                report = validate_bridge_output(
                    ledger,
                    output,
                    allow_conservative_mixed_modes=(
                        self.policy.composition_contract_version == "v2"
                    ),
                )
                self._persist(
                    BridgePersistenceBatch(
                        action=BridgeAction.OUTPUT_VALIDATED,
                        inputs=(ledger.id, output.id),
                        records=_validation_records(report),
                        finding_ref=report.id,
                    )
                )
                if not report.valid:
                    return self._failure(
                        RuntimeError("grounding repair produced an invalid bridge output"),
                        default_code="BRIDGE_REPAIR_OUTPUT_INVALID",
                        formal_seq=formal_seq,
                        phase="grounding_repair",
                        ledger=ledger,
                        output=output,
                        report=report,
                        review=review,
                        amendment_count=amendment_count,
                        inputs=(ledger.id, output.id),
                        calls=[],
                    )
                if repaired.disposition == RepairDisposition.BOUNDED_FAILURE:
                    return self._failure(
                        RuntimeError(
                            "grounding repair exhausted without a valid correction"
                        ),
                        default_code="BRIDGE_GROUNDING_REPAIR_BOUNDED_FAILURE",
                        formal_seq=formal_seq,
                        phase="grounding_repair",
                        ledger=ledger,
                        output=output,
                        report=report,
                        review=review,
                        amendment_count=amendment_count,
                        inputs=(ledger.id, output.id, report.id, review.id),
                        calls=[],
                        diagnostics=tuple(repaired.diagnostics),
                    )
                if not repaired.requires_grounded_review:
                    break

        assert ledger is not None and output is not None and report is not None
        terminal_inputs = [ledger.id, output.id, report.id]
        if review is not None:
            terminal_inputs.append(review.id)
        self._persist(
            BridgePersistenceBatch(
                action=BridgeAction.COMPLETED,
                inputs=tuple(terminal_inputs),
                finding_ref=review.id if review is not None else report.id,
            )
        )
        return self._result(
            process_status="success",
            phase="completed",
            formal_seq=formal_seq,
            ledger=ledger,
            output=output,
            report=report,
            review=review,
            amendment_count=amendment_count,
        )


__all__ = [
    "BridgePersistenceBatch",
    "BridgeWorkflow",
    "BridgeWorkflowPolicy",
    "BridgeWorkflowResultV1",
]
