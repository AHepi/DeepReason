"""C7 grounded repair cannot launder epistemic classes or references."""

from __future__ import annotations

import json

import pytest

from deepreason.bridge.models import (
    BridgeOutputV1,
    ClaimLedgerEntryV1,
    ClaimLedgerV1,
    ClaimUseV1,
    GroundingFindingV1,
    GroundingReviewV1,
)
from deepreason.bridge.repair import (
    GroundingRepairError,
    GroundingRepairService,
    RepairDisposition,
    assert_safe_repair_diff,
)
from deepreason.bridge.validate import validate_bridge_output
from deepreason.llm.adapter import LLMAdapter
from deepreason.llm.endpoints import MockEndpoint
from deepreason.storage.blobs import BlobStore


def _fact(*, grounded: bool = True):
    values = {"source_refs": ["source-1"]} if grounded else {}
    return ClaimLedgerEntryV1.create(
        claim_class="source_fact",
        claim="The source establishes a value of 3.",
        **values,
    )


def _case(entry=None):
    entry = entry or _fact()
    ledger = ClaimLedgerV1.create(
        problem_ref="problem-repair",
        formal_seq=9,
        output_target="answer",
        entries=[entry],
    )
    section = ClaimUseV1.create(
        span_id="span-1",
        text="The value is definitely 4.",
        rendering_mode="fact",
        ledger_entry_ids=[entry.id],
    )
    output = BridgeOutputV1.create(
        claim_ledger_id=ledger.id,
        sections=[section],
        resolution="answered",
    )
    return ledger, output, entry


def _review(ledger, output, entry, status, message="Grounded review failed."):
    finding = GroundingFindingV1.create(
        span_id="span-1",
        status=status,
        message=message,
        ledger_entry_ids=[entry.id],
        checked_refs=["source-1"],
    )
    return GroundingReviewV1.create(
        claim_ledger_id=ledger.id,
        bridge_output_id=output.id,
        findings=[finding],
        passed=False,
    )


def _service(tmp_path, responses):
    adapter = LLMAdapter(
        {"judge": MockEndpoint(responses)}, BlobStore(tmp_path / "blobs"), retry_max=2
    )
    return GroundingRepairService(adapter)


def test_citation_mismatch_can_reword_but_must_be_reviewed_again(tmp_path):
    ledger, output, entry = _case()
    review = _review(ledger, output, entry, "citation_mismatch")
    response = json.dumps(
        {
            "action": "correct_wording",
            "replacement_text": "The source establishes a value of 3.",
        }
    )

    result = _service(tmp_path, [response]).repair(ledger, output, review)

    assert result.disposition == RepairDisposition.APPLIED
    assert result.requires_grounded_review
    assert result.output.sections[0].text == entry.claim
    assert result.output.sections[0].ledger_entry_ids == [entry.id]
    assert result.output.sections[0].rendering_mode.value == "fact"
    assert validate_bridge_output(ledger, result.output).valid
    assert len(result.calls) == 1


def test_class_downgrade_is_an_explicit_amendment_not_unknown_remapping(tmp_path):
    ledger, output, entry = _case()
    review = _review(ledger, output, entry, "unsupported")
    result = _service(
        tmp_path, ['{"action":"downgrade_claim"}']
    ).repair(ledger, output, review)

    assert result.disposition == RepairDisposition.LEDGER_AMENDMENT_REQUIRED
    assert result.amendment_span_ids == ["span-1"]
    assert result.output.sections == []
    assert result.output.resolution.value == "insufficient_evidence"
    assert all(
        section.rendering_mode.value != "unknown" for section in result.output.sections
    )
    assert validate_bridge_output(ledger, result.output).valid


def test_change_resolution_quarantines_the_unsupported_positive_span(tmp_path):
    ledger, output, entry = _case()
    review = _review(ledger, output, entry, "unsupported")
    response = json.dumps(
        {
            "action": "change_resolution",
            "resolution": "underdetermined",
            "resolution_reason": "The reviewed span is not supported.",
        }
    )
    result = _service(tmp_path, [response]).repair(ledger, output, review)

    assert result.disposition == RepairDisposition.APPLIED
    assert result.output.sections == []
    assert result.output.resolution.value == "underdetermined"
    assert result.output.resolution_reason == "The reviewed span is not supported."


def test_wire_cannot_add_source_evidence_or_premise_during_schema_repair(tmp_path):
    ledger, output, entry = _case()
    review = _review(ledger, output, entry, "citation_mismatch")
    invalid = json.dumps(
        {
            "action": "correct_wording",
            "replacement_text": "Invented factual slot.",
            "source_refs": ["invented-source"],
            "evidence_refs": ["invented-evidence"],
            "premise_refs": ["invented-premise"],
        }
    )
    result = _service(tmp_path, [invalid, invalid, invalid]).repair(
        ledger, output, review
    )

    assert result.disposition == RepairDisposition.BOUNDED_FAILURE
    assert result.output.sections == []
    assert result.output.resolution.value == "insufficient_evidence"
    assert result.calls[0].attempts == 3
    assert result.diagnostics
    assert "invented-source" not in result.output.model_dump_json()


def test_forbidden_semantic_action_fails_bounded_and_preserves_safe_partial(tmp_path):
    ledger, output, entry = _case()
    review = _review(ledger, output, entry, "unsupported")
    response = json.dumps(
        {"action": "correct_wording", "replacement_text": "Still a fact."}
    )
    result = _service(tmp_path, [response]).repair(ledger, output, review)

    assert result.disposition == RepairDisposition.BOUNDED_FAILURE
    assert result.output.sections == []
    assert result.diagnostics[0].code == "BRIDGE_REPAIR_ACTION_FORBIDDEN"
    assert len(result.calls) == 1


def test_remove_span_does_not_manufacture_optional_unresolved_items(tmp_path):
    ledger, output, entry = _case()
    assert output.unresolved_items is None
    review = _review(ledger, output, entry, "unsupported")
    result = _service(tmp_path, ['{"action":"remove_span"}']).repair(
        ledger, output, review
    )

    assert result.output.unresolved_items is None
    dumped = result.output.model_dump(mode="json", exclude_none=True)
    assert "unresolved_items" not in dumped
    assert validate_bridge_output(ledger, result.output).valid


def test_missing_grounding_is_rejected_before_repair_can_fill_a_fact(tmp_path):
    ledger, output, entry = _case(_fact(grounded=False))
    review = _review(ledger, output, entry, "unsupported")
    endpoint = MockEndpoint(['{"action":"correct_wording","replacement_text":"filled"}'])
    service = GroundingRepairService(
        LLMAdapter({"judge": endpoint}, BlobStore(tmp_path / "blobs"))
    )

    with pytest.raises(GroundingRepairError) as raised:
        service.repair(ledger, output, review)

    assert raised.value.code == "BRIDGE_REPAIR_INPUT_INVALID"
    assert endpoint.last_usage is None


def test_repair_rejects_an_incomplete_or_duplicate_grounding_review(tmp_path):
    ledger, output, entry = _case()
    second = ClaimUseV1.create(
        span_id="span-2",
        text="A second factual span.",
        rendering_mode="fact",
        ledger_entry_ids=[entry.id],
    )
    expanded = BridgeOutputV1.create(
        claim_ledger_id=ledger.id,
        sections=[*output.sections, second],
        resolution="answered",
    )
    finding = GroundingFindingV1.create(
        span_id="span-1",
        status="unsupported",
        ledger_entry_ids=[entry.id],
    )
    incomplete = GroundingReviewV1.create(
        claim_ledger_id=ledger.id,
        bridge_output_id=expanded.id,
        findings=[finding],
        passed=False,
    )
    service = _service(tmp_path, ['{"action":"remove_span"}'])

    with pytest.raises(GroundingRepairError) as raised:
        service.repair(ledger, expanded, incomplete)

    assert raised.value.code == "BRIDGE_REPAIR_REVIEW_INCOMPLETE"


def test_safe_diff_guard_rejects_new_refs_and_new_spans():
    ledger, output, _entry = _case()
    unknown_ref = "sha256:" + "f" * 64
    replaced = ClaimUseV1.create(
        span_id="span-1",
        text="Changed.",
        rendering_mode="fact",
        ledger_entry_ids=[unknown_ref],
    )
    changed_refs = BridgeOutputV1.create(
        claim_ledger_id=ledger.id,
        sections=[replaced],
        resolution="answered",
    )
    with pytest.raises(GroundingRepairError) as refs_error:
        assert_safe_repair_diff(output, changed_refs)
    assert refs_error.value.code == "BRIDGE_REPAIR_REFS_CHANGED"

    added = ClaimUseV1.create(
        span_id="span-new",
        text="New fact.",
        rendering_mode="fact",
        ledger_entry_ids=list(output.sections[0].ledger_entry_ids),
    )
    new_span = BridgeOutputV1.create(
        claim_ledger_id=ledger.id,
        sections=[*output.sections, added],
        resolution="answered",
    )
    with pytest.raises(GroundingRepairError) as span_error:
        assert_safe_repair_diff(output, new_span)
    assert span_error.value.code == "BRIDGE_REPAIR_SPAN_ADDED"


def test_global_semantic_call_cap_quarantines_remaining_failed_spans(tmp_path):
    first = _fact()
    second = ClaimLedgerEntryV1.create(
        claim_class="source_fact",
        claim="A second source-backed claim.",
        source_refs=["source-2"],
    )
    ledger = ClaimLedgerV1.create(
        problem_ref="problem-cap",
        formal_seq=11,
        output_target="answer",
        entries=[first, second],
    )
    sections = [
        ClaimUseV1.create(
            span_id=f"span-{index}",
            text=entry.claim,
            rendering_mode="fact",
            ledger_entry_ids=[entry.id],
        )
        for index, entry in enumerate((first, second), 1)
    ]
    output = BridgeOutputV1.create(
        claim_ledger_id=ledger.id, sections=sections, resolution="answered"
    )
    findings = [
        GroundingFindingV1.create(
            span_id=section.span_id,
            status="unsupported",
            ledger_entry_ids=list(section.ledger_entry_ids),
        )
        for section in sections
    ]
    review = GroundingReviewV1.create(
        claim_ledger_id=ledger.id,
        bridge_output_id=output.id,
        findings=findings,
        passed=False,
    )
    endpoint = MockEndpoint(['{"action":"remove_span"}'])
    service = GroundingRepairService(
        LLMAdapter({"judge": endpoint}, BlobStore(tmp_path / "blobs")),
        max_attempts=1,
    )

    result = service.repair(ledger, output, review)

    assert result.disposition == RepairDisposition.BOUNDED_FAILURE
    assert result.output.sections == []
    assert len(result.calls) == 1
    assert any(item.code == "BRIDGE_REPAIR_ATTEMPT_CAP" for item in result.diagnostics)
    assert validate_bridge_output(ledger, result.output).valid
