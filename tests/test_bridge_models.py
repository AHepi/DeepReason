"""Canonical bridge records preserve epistemic categories and identities."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from deepreason.bridge.models import (
    MAX_BRIDGE_REFS,
    BridgeOutputV1,
    BridgeResolution,
    BridgeValidationFindingV1,
    BridgeValidationReportV1,
    ClaimClass,
    ClaimLedgerEntryV1,
    ClaimLedgerV1,
    ClaimUseV1,
    CorrectionMode,
    GroundingFindingV1,
    GroundingReviewV1,
    GroundingStatus,
    RenderingMode,
    SourceConflictV1,
    UncoveredRequirementV1,
    UnresolvedItemV1,
)
from deepreason.scratch.models import domain_hash


def _hash(character: str) -> str:
    return f"sha256:{character * 64}"


def _entry(
    claim_class: ClaimClass | str = ClaimClass.UNKNOWN,
    claim: str = "The answer is not established.",
    **values,
) -> ClaimLedgerEntryV1:
    return ClaimLedgerEntryV1.create(
        claim_class=claim_class,
        claim=claim,
        **values,
    )


def _ledger(*entries: ClaimLedgerEntryV1) -> ClaimLedgerV1:
    return ClaimLedgerV1.create(
        problem_ref="problem-1",
        formal_seq=7,
        output_target="answer",
        entries=list(entries),
    )


def _use(entry: ClaimLedgerEntryV1, mode: RenderingMode | str) -> ClaimUseV1:
    return ClaimUseV1.create(
        span_id="span-1",
        text=entry.claim,
        rendering_mode=mode,
        ledger_entry_ids=[entry.id],
    )


def test_claim_class_vocabulary_is_exact_and_closed():
    assert {item.value for item in ClaimClass} == {
        "source_fact",
        "recorded_observation",
        "supported_inference",
        "surviving_conjecture",
        "assumption",
        "unknown",
        "conflict",
    }
    with pytest.raises(ValidationError):
        _entry("probably_fact")
    with pytest.raises(ValidationError):
        _entry("fact-like")


@pytest.mark.parametrize("claim_class", list(ClaimClass))
def test_every_claim_class_has_one_canonical_identity(claim_class):
    entry = _entry(claim_class, f"A {claim_class.value} statement.")

    assert entry.id.startswith("sha256:")
    assert len(entry.id) == 71
    assert entry.claim_class == claim_class


def test_optional_epistemic_fields_are_genuinely_absent():
    entry = _entry()
    data = entry.model_dump(mode="json", by_alias=True, exclude_none=True)

    assert set(data) == {"schema", "id", "claim_class", "claim"}
    assert entry.source_refs is None
    assert entry.evidence_refs is None
    assert entry.premise_refs is None
    assert entry.scratch_refs is None


def test_scratch_references_are_separate_provenance_not_grounding_fields():
    entry = _entry(
        ClaimClass.SOURCE_FACT,
        "A scratch note suggested this fact.",
        scratch_refs=[_hash("a")],
    )

    assert entry.scratch_refs == [_hash("a")]
    assert entry.source_refs is None
    assert entry.evidence_refs is None
    assert entry.event_refs is None
    assert entry.trace_refs is None
    assert entry.formal_observation_refs is None


def test_each_epistemic_reference_channel_remains_distinct():
    premise = _entry(ClaimClass.SOURCE_FACT, "Premise", source_refs=["source-1"])
    conflict = SourceConflictV1.create(
        conflicting_refs=["source-left", "source-right"]
    )
    entry = _entry(
        ClaimClass.SUPPORTED_INFERENCE,
        "A derived claim.",
        source_refs=["source-1"],
        evidence_refs=["evidence-1"],
        event_refs=["event-1"],
        trace_refs=["trace-1"],
        formal_observation_refs=["observation-1"],
        premise_refs=[premise.id],
        formal_artifact_refs=["artifact-1"],
        conflict_refs=["claim-left", "claim-right"],
        source_conflict_refs=[conflict.id],
        scratch_refs=[_hash("b")],
    )

    assert entry.premise_refs == [premise.id]
    assert entry.source_conflict_refs == [conflict.id]
    assert entry.scratch_refs == [_hash("b")]


def test_source_conflict_structurally_names_at_least_two_unique_refs():
    conflict = SourceConflictV1.create(
        conflicting_refs=["source-a", "source-b"],
        description="The sources disagree about the measured value.",
    )
    assert conflict.conflicting_refs == ["source-a", "source-b"]

    with pytest.raises(ValidationError):
        SourceConflictV1.create(conflicting_refs=["source-a"])
    with pytest.raises(ValidationError, match="duplicates"):
        SourceConflictV1.create(conflicting_refs=["source-a", "source-a"])


def test_uncovered_requirements_can_remain_unresolved_without_fabricated_refs():
    uncovered = UncoveredRequirementV1.create(
        requirement="Determine the value at the missing time point.",
        reason="No source or observation covers it.",
        scratch_refs=[_hash("c")],
    )
    assert uncovered.related_ledger_entry_ids is None
    assert uncovered.scratch_refs == [_hash("c")]


def test_ledger_identity_contains_canonical_entries_not_display_formatting():
    entry = _entry(ClaimClass.UNKNOWN, "No grounded answer is available.")
    ledger = ClaimLedgerV1.create(
        problem_ref="problem-1",
        formal_seq=3,
        output_target="summary",
        entries=[entry],
        uncovered_requirements=None,
        source_conflicts=None,
    )

    assert ledger.entries == [entry]
    with pytest.raises(ValidationError, match="extra_forbidden"):
        ClaimLedgerV1.model_validate(
            {**ledger.model_dump(mode="json", by_alias=True), "display_heading": "Claims"}
        )
    with pytest.raises(ValidationError):
        ClaimLedgerV1.create(
            problem_ref="problem-1",
            formal_seq="3",
            output_target="summary",
            entries=[entry],
        )


def test_claim_use_maps_one_stable_span_to_typed_ledger_entries():
    entry = _entry(ClaimClass.SURVIVING_CONJECTURE, "A novel possibility.")
    use = _use(entry, RenderingMode.CONJECTURE)

    assert use.span_id == "span-1"
    assert use.ledger_entry_ids == [entry.id]
    assert use.rendering_mode == RenderingMode.CONJECTURE
    with pytest.raises(ValidationError):
        ClaimUseV1.create(
            span_id="../span",
            text="unsafe",
            rendering_mode="fact",
            ledger_entry_ids=[entry.id],
        )


def test_terminal_resolution_vocabulary_is_exact():
    assert {item.value for item in BridgeResolution} == {
        "answered",
        "partially_answered",
        "underdetermined",
        "insufficient_evidence",
        "conflicting_evidence",
        "outside_scope",
    }
    assert {item.value for item in RenderingMode} == {
        "fact",
        "observation",
        "inference",
        "conjecture",
        "assumption",
        "unknown",
        "conflict",
    }


@pytest.mark.parametrize(
    "resolution",
    [
        BridgeResolution.PARTIALLY_ANSWERED,
        BridgeResolution.UNDERDETERMINED,
        BridgeResolution.INSUFFICIENT_EVIDENCE,
        BridgeResolution.CONFLICTING_EVIDENCE,
        BridgeResolution.OUTSIDE_SCOPE,
    ],
)
def test_unresolved_terminal_outputs_are_canonical_success_shapes(resolution):
    unknown = _entry()
    ledger = _ledger(unknown)
    unresolved = UnresolvedItemV1.create(
        description="The missing answer remains missing.",
        reason="Grounding is absent.",
        ledger_entry_ids=[unknown.id],
    )
    output = BridgeOutputV1.create(
        claim_ledger_id=ledger.id,
        sections=[],
        unresolved_items=[unresolved],
        resolution=resolution,
        resolution_reason="The available record does not settle the problem.",
    )

    assert output.resolution == resolution
    assert output.sections == []
    assert output.unresolved_items == [unresolved]


def test_bridge_output_rejects_duplicate_span_ids():
    entry = _entry()
    ledger = _ledger(entry)
    first = _use(entry, "unknown")
    second = ClaimUseV1.create(
        span_id=first.span_id,
        text="Different wording.",
        rendering_mode="unknown",
        ledger_entry_ids=[entry.id],
    )
    with pytest.raises(ValidationError, match="duplicate span"):
        BridgeOutputV1.create(
            claim_ledger_id=ledger.id,
            sections=[first, second],
            resolution="underdetermined",
        )


def test_validation_finding_carries_location_refs_and_allowed_corrections():
    entry = _entry()
    finding = BridgeValidationFindingV1.create(
        code="BRIDGE_UNKNOWN_ASSERTS_FACT",
        span_id="span-1",
        message="An unknown cannot back a factual assertion.",
        relevant_ledger_ids=[entry.id],
        allowed_correction_modes=[
            CorrectionMode.DOWNGRADE_CLAIM,
            CorrectionMode.REMOVE_SPAN,
        ],
    )

    assert finding.span_id == "span-1"
    assert finding.pointer is None
    assert finding.allowed_correction_modes == [
        CorrectionMode.DOWNGRADE_CLAIM,
        CorrectionMode.REMOVE_SPAN,
    ]
    with pytest.raises(ValidationError, match="pointer or span_id"):
        BridgeValidationFindingV1.create(
            code="BRIDGE_SPAN_UNMAPPED",
            message="Missing location.",
        )
    root_finding = BridgeValidationFindingV1.create(
        code="BRIDGE_LEDGER_ENTRY_MISSING",
        pointer="",
        message="The root object is missing a required ledger entry.",
    )
    assert root_finding.pointer == ""


def test_validation_report_truth_value_matches_findings():
    entry = _entry()
    ledger = _ledger(entry)
    valid = BridgeValidationReportV1.create(
        claim_ledger_id=ledger.id,
        valid=True,
        findings=[],
    )
    assert valid.valid is True

    finding = BridgeValidationFindingV1.create(
        code="BRIDGE_INFERENCE_PREMISES_MISSING",
        pointer="/entries/0/premise_refs",
        message="Inference has no premises.",
    )
    invalid = BridgeValidationReportV1.create(
        claim_ledger_id=ledger.id,
        valid=False,
        findings=[finding],
    )
    assert invalid.valid is False
    with pytest.raises(ValidationError, match="valid report"):
        BridgeValidationReportV1.create(
            claim_ledger_id=ledger.id,
            valid=True,
            findings=[finding],
        )


def test_grounding_status_vocabulary_and_review_consistency():
    assert {item.value for item in GroundingStatus} == {
        "supported",
        "unsupported",
        "overstated",
        "misclassified",
        "citation_mismatch",
        "unclear",
    }
    entry = _entry(ClaimClass.SOURCE_FACT, "Grounded.", source_refs=["source-1"])
    ledger = _ledger(entry)
    output = BridgeOutputV1.create(
        claim_ledger_id=ledger.id,
        sections=[_use(entry, "fact")],
        resolution="answered",
    )
    supported = GroundingFindingV1.create(
        span_id="span-1",
        status="supported",
        ledger_entry_ids=[entry.id],
        checked_refs=["source-1"],
    )
    review = GroundingReviewV1.create(
        claim_ledger_id=ledger.id,
        bridge_output_id=output.id,
        findings=[supported],
        passed=True,
    )
    assert review.passed is True

    unsupported = GroundingFindingV1.create(
        span_id="span-1",
        status="unsupported",
        ledger_entry_ids=[entry.id],
    )
    with pytest.raises(ValidationError, match="passed must be false"):
        GroundingReviewV1.create(
            claim_ledger_id=ledger.id,
            bridge_output_id=output.id,
            findings=[unsupported],
            passed=True,
        )


def test_reference_and_payload_bounds_are_enforced():
    refs = [f"source-{index}" for index in range(MAX_BRIDGE_REFS + 1)]
    with pytest.raises(ValidationError):
        _entry(ClaimClass.SOURCE_FACT, source_refs=refs)
    with pytest.raises(ValidationError, match="blank"):
        _entry(ClaimClass.SOURCE_FACT, source_refs=["   "])
    with pytest.raises(ValidationError):
        _entry(claim="x" * 262_145)


def test_lists_and_records_are_immutable_and_extra_fields_forbidden():
    entry = _entry(ClaimClass.SOURCE_FACT, source_refs=["source-1"])
    ledger = _ledger(entry)
    with pytest.raises(TypeError):
        entry.source_refs.append("source-2")
    with pytest.raises(TypeError):
        ledger.entries.append(_entry())
    with pytest.raises(ValidationError, match="extra_forbidden"):
        ClaimLedgerEntryV1.create(
            claim_class="unknown",
            claim="Unknown.",
            confidence=0.8,
        )


def test_domain_separation_and_caller_supplied_id_verification_for_every_model():
    entry = _entry()
    uncovered = UncoveredRequirementV1.create(requirement="Missing requirement.")
    conflict = SourceConflictV1.create(conflicting_refs=["left", "right"])
    ledger = ClaimLedgerV1.create(
        problem_ref="problem-1",
        formal_seq=1,
        output_target="answer",
        entries=[entry],
        uncovered_requirements=[uncovered],
        source_conflicts=[conflict],
    )
    use = _use(entry, "unknown")
    unresolved = UnresolvedItemV1.create(description="Still missing.")
    output = BridgeOutputV1.create(
        claim_ledger_id=ledger.id,
        sections=[use],
        unresolved_items=[unresolved],
        resolution="underdetermined",
    )
    finding = BridgeValidationFindingV1.create(
        code="BRIDGE_UNKNOWN_ASSERTS_FACT",
        span_id="span-1",
        message="Invalid rendering.",
    )
    report = BridgeValidationReportV1.create(
        claim_ledger_id=ledger.id,
        bridge_output_id=output.id,
        valid=False,
        findings=[finding],
    )
    grounding = GroundingFindingV1.create(
        span_id="span-1",
        status="unclear",
    )
    review = GroundingReviewV1.create(
        claim_ledger_id=ledger.id,
        bridge_output_id=output.id,
        findings=[grounding],
        passed=False,
    )
    records = [
        entry,
        uncovered,
        conflict,
        ledger,
        use,
        unresolved,
        output,
        finding,
        report,
        grounding,
        review,
    ]

    assert len({record.id for record in records}) == len(records)
    payload = {"same": "payload"}
    domains = {record.ID_DOMAIN for record in records}
    assert len({domain_hash(domain, payload) for domain in domains}) == len(domains)
    for record in records:
        dumped = record.model_dump(mode="json", by_alias=True, exclude_none=True)
        with pytest.raises(ValidationError, match="canonical"):
            type(record).model_validate({**dumped, "id": _hash("f")})

