"""C7 minimal, non-editing grounded-review protocol."""

from __future__ import annotations

import json

import pytest

from deepreason.bridge.models import (
    BridgeOutputV1,
    ClaimLedgerEntryV1,
    ClaimLedgerV1,
    ClaimUseV1,
)
from deepreason.bridge.review import GroundingReviewService
from deepreason.llm.adapter import LLMAdapter
from deepreason.llm.endpoints import MockEndpoint
from deepreason.llm.repair import SchemaRepairError
from deepreason.storage.blobs import BlobStore


def _fact(claim: str, source: str):
    return ClaimLedgerEntryV1.create(
        claim_class="source_fact", claim=claim, source_refs=[source]
    )


def _case(*entries):
    ledger = ClaimLedgerV1.create(
        problem_ref="problem-review",
        formal_seq=5,
        output_target="answer",
        entries=list(entries),
    )
    sections = [
        ClaimUseV1.create(
            span_id=f"span-{index}",
            text=entry.claim,
            rendering_mode="fact",
            ledger_entry_ids=[entry.id],
        )
        for index, entry in enumerate(entries, 1)
    ]
    output = BridgeOutputV1.create(
        claim_ledger_id=ledger.id,
        sections=sections,
        resolution="answered",
    )
    return ledger, output


def test_reviewer_can_only_classify_and_harness_binds_span_and_refs(tmp_path):
    entry = _fact("The recorded value is 2.", "source-1")
    ledger, output = _case(entry)
    adapter = LLMAdapter(
        {
            "judge": MockEndpoint(
                [json.dumps({"finding": "supported", "message": "Exact match."})]
            )
        },
        BlobStore(tmp_path / "blobs"),
    )

    result = GroundingReviewService(adapter).review(
        ledger,
        output,
        materials={"source-1": "The recorded value is 2."},
    )

    assert result.review.passed
    assert len(result.calls) == 1
    finding = result.review.findings[0]
    assert finding.span_id == "span-1"
    assert finding.ledger_entry_ids == [entry.id]
    assert finding.checked_refs == ["source-1"]
    assert finding.status.value == "supported"


def test_review_pack_is_one_span_and_omits_unrelated_ledger_material(tmp_path):
    first = _fact("First private claim.", "source-first")
    second = _fact("Second private claim.", "source-second")
    ledger, output = _case(first, second)
    prompts: list[str] = []

    def inspect(prompt: str) -> str:
        prompts.append(prompt)
        return '{"finding":"supported"}'

    adapter = LLMAdapter(
        {"judge": MockEndpoint(inspect)}, BlobStore(tmp_path / "blobs")
    )
    result = GroundingReviewService(adapter).review(
        ledger,
        output,
        materials={
            "source-first": "First private claim.",
            "source-second": "Second private claim.",
            "unrelated": "must never enter a pack",
        },
    )

    assert result.review.passed
    assert len(prompts) == 2
    assert "Second private claim." not in prompts[0]
    assert "source-second" not in prompts[0]
    assert "First private claim." not in prompts[1]
    assert "source-first" not in prompts[1]
    assert "must never enter a pack" not in "".join(prompts)


def test_review_pack_uses_only_call_local_handles_for_ids_and_refs(tmp_path):
    entry = _fact("Handle-bound claim.", "private-source-reference")
    ledger, output = _case(entry)
    prompts: list[str] = []

    def inspect(prompt: str) -> str:
        prompts.append(prompt)
        return '{"finding":"supported"}'

    GroundingReviewService(
        LLMAdapter({"judge": MockEndpoint(inspect)}, BlobStore(tmp_path / "blobs"))
    ).review(
        ledger,
        output,
        materials={"private-source-reference": "Exact excerpt."},
    )

    prompt = prompts[0]
    assert '"span_handle": "S1"' in prompt
    assert '"ledger_handle": "E1"' in prompt
    assert '"ref_handle": "R1"' in prompt
    assert output.sections[0].span_id not in prompt
    assert entry.id not in prompt
    assert "private-source-reference" not in prompt


def test_missing_exact_material_forces_unclear_even_if_model_says_supported(tmp_path):
    entry = _fact("Claim requiring a source.", "missing-source")
    ledger, output = _case(entry)
    adapter = LLMAdapter(
        {"judge": MockEndpoint(['{"finding":"supported"}'])},
        BlobStore(tmp_path / "blobs"),
    )

    result = GroundingReviewService(adapter).review(ledger, output, materials={})

    finding = result.review.findings[0]
    assert finding.status.value == "unclear"
    assert finding.checked_refs is None
    assert "missing" in finding.message.casefold()
    assert not result.review.passed


def test_reviewer_wire_cannot_edit_text_or_author_canonical_status(tmp_path):
    entry = _fact("Claim.", "source-1")
    ledger, output = _case(entry)
    invalid = '{"finding":"supported","replacement_text":"edited"}'
    adapter = LLMAdapter(
        {"judge": MockEndpoint([invalid, invalid, invalid])},
        BlobStore(tmp_path / "blobs"),
        retry_max=2,
    )

    with pytest.raises(SchemaRepairError) as raised:
        GroundingReviewService(adapter).review(
            ledger, output, materials={"source-1": "Claim."}
        )

    assert raised.value.spend is not None
    assert raised.value.spend.attempts == 3
    assert all(not attempt.valid for attempt in raised.value.spend.attempt_trace)


@pytest.mark.parametrize(
    "finding",
    [
        "supported",
        "unsupported",
        "overstated",
        "misclassified",
        "citation_mismatch",
        "unclear",
    ],
)
def test_reviewer_finding_vocabulary_is_exact(tmp_path, finding):
    entry = _fact("Claim.", "source-1")
    ledger, output = _case(entry)
    adapter = LLMAdapter(
        {"judge": MockEndpoint([json.dumps({"finding": finding})])},
        BlobStore(tmp_path / finding),
    )

    result = GroundingReviewService(adapter).review(
        ledger, output, materials={"source-1": "Claim."}
    )

    assert result.review.findings[0].status.value == finding
    assert result.review.passed == (finding == "supported")
