"""Canonical bridge records use the shared immutable object store."""

from __future__ import annotations

import json

import pytest

from deepreason.bridge.models import (
    BridgeOutputV1,
    BridgeValidationFindingV1,
    BridgeValidationReportV1,
    ClaimLedgerEntryV1,
    ClaimLedgerV1,
    ClaimUseV1,
    GroundingFindingV1,
    GroundingReviewV1,
    SourceConflictV1,
    UncoveredRequirementV1,
    UnresolvedItemV1,
)
from deepreason.storage.objects import ObjectStore


def _records():
    entry = ClaimLedgerEntryV1.create(
        claim_class="source_fact",
        claim="The source records a value.",
        source_refs=["source-1"],
    )
    uncovered = UncoveredRequirementV1.create(requirement="A value remains missing.")
    conflict = SourceConflictV1.create(conflicting_refs=["source-1", "source-2"])
    ledger = ClaimLedgerV1.create(
        problem_ref="problem-1",
        formal_seq=3,
        output_target="answer",
        entries=[entry],
        uncovered_requirements=[uncovered],
        source_conflicts=[conflict],
    )
    use = ClaimUseV1.create(
        span_id="span-1",
        text=entry.claim,
        rendering_mode="fact",
        ledger_entry_ids=[entry.id],
    )
    unresolved = UnresolvedItemV1.create(description="Another value is unresolved.")
    output = BridgeOutputV1.create(
        claim_ledger_id=ledger.id,
        sections=[use],
        unresolved_items=[unresolved],
        resolution="partially_answered",
    )
    finding = BridgeValidationFindingV1.create(
        code="BRIDGE_SOURCE_FACT_UNGROUNDED",
        span_id="span-1",
        message="The factual span lacks grounding.",
    )
    report = BridgeValidationReportV1.create(
        claim_ledger_id=ledger.id,
        bridge_output_id=output.id,
        valid=False,
        findings=[finding],
    )
    grounding = GroundingFindingV1.create(
        span_id="span-1",
        status="supported",
        ledger_entry_ids=[entry.id],
    )
    review = GroundingReviewV1.create(
        claim_ledger_id=ledger.id,
        bridge_output_id=output.id,
        findings=[grounding],
        passed=True,
    )
    return {
        "bridge-ledger-entry": entry,
        "bridge-uncovered-requirement": uncovered,
        "bridge-source-conflict": conflict,
        "bridge-claim-ledger": ledger,
        "bridge-claim-use": use,
        "bridge-unresolved-item": unresolved,
        "bridge-output": output,
        "bridge-validation-finding": finding,
        "bridge-validation-report": report,
        "bridge-grounding-finding": grounding,
        "bridge-grounding-review": review,
    }


@pytest.mark.parametrize("schema", sorted(_records()))
def test_every_bridge_record_round_trips_through_shared_store(tmp_path, schema):
    store = ObjectStore(tmp_path / "objects")
    record = _records()[schema]

    store.put(schema, record)

    assert store.get(record.id, schema=schema) == (schema, record)


def test_bridge_storage_omits_absent_optional_fields_and_rejects_wrong_schema(
    tmp_path,
):
    store = ObjectStore(tmp_path / "objects")
    entry = ClaimLedgerEntryV1.create(
        claim_class="unknown",
        claim="The value is unknown.",
    )
    store.put("bridge-ledger-entry", entry)

    stored = json.loads(
        store._schema_path("bridge-ledger-entry", entry.id).read_text()
    )
    assert "scratch_refs" not in stored["data"]
    with pytest.raises(ValueError):
        store.put("bridge-uncovered-requirement", entry)
