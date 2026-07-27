"""Stage B composes only validated ledger entries through bounded repair."""

from __future__ import annotations

import json

import pytest

from deepreason.bridge.compose import (
    BridgeComposer,
    CompositionRequestV1,
    CompositionStatus,
)
from deepreason.bridge.models import (
    ClaimClass,
    ClaimLedgerEntryV1,
    ClaimLedgerV1,
    SourceConflictV1,
    UncoveredRequirementV1,
)
from deepreason.harness import Harness
from deepreason.llm.adapter import LLMAdapter
from deepreason.llm.endpoints import MockEndpoint


def _entry(claim_class: ClaimClass | str, claim: str, **values):
    return ClaimLedgerEntryV1.create(
        claim_class=claim_class,
        claim=claim,
        **values,
    )


def _ledger(
    *entries: ClaimLedgerEntryV1,
    uncovered: list[UncoveredRequirementV1] | None = None,
    conflicts: list[SourceConflictV1] | None = None,
) -> ClaimLedgerV1:
    return ClaimLedgerV1.create(
        problem_ref="problem-fixture",
        formal_seq=7,
        output_target="answer",
        entries=list(entries),
        uncovered_requirements=uncovered,
        source_conflicts=conflicts,
    )


def _request(**changes) -> CompositionRequestV1:
    values = {
        "output_target": "answer",
        "formatting_profile": "plain",
        "desired_length_chars": 4_096,
        "maximum_sections": 8,
    }
    values.update(changes)
    return CompositionRequestV1(**values)


def _compose(tmp_path, ledger, response, *, retry_max=2):
    harness = Harness(tmp_path / "run")
    endpoint = MockEndpoint(response if callable(response) else [response])
    adapter = LLMAdapter(
        {"thesis": endpoint},
        harness.blobs,
        retry_max=retry_max,
    )
    result = BridgeComposer(adapter).compose(ledger, _request())
    return result, harness, endpoint


def _span(text: str, mode: str, handle: str = "E1", span_id: str = "S1"):
    return {
        "span_id": span_id,
        "text": text,
        "rendering_mode": mode,
        "ledger_entry_handles": [handle],
    }


def _wire(*, sections=None, resolution="answered", **values) -> str:
    payload = {"sections": sections or [], "resolution": resolution, **values}
    return json.dumps(payload)


def test_answer_from_fact_rewords_only_a_known_opaque_ledger_entry(tmp_path):
    fact = _entry(
        ClaimClass.SOURCE_FACT,
        "The recorded value is forty-two.",
        source_refs=["source-1"],
    )
    ledger = _ledger(fact)

    def answer(prompt: str) -> str:
        assert "E1" in prompt
        assert fact.id not in prompt
        assert "source-1" not in prompt
        return _wire(
            sections=[_span("The value in the record is 42.", "fact")]
        )

    result, _harness, _endpoint = _compose(tmp_path, ledger, answer)

    assert result.status == CompositionStatus.COMPOSED
    assert result.successful
    assert result.output is not None and result.output.resolution.value == "answered"
    assert result.output.sections[0].text == "The value in the record is 42."
    assert result.output.sections[0].ledger_entry_ids == [fact.id]
    assert result.output_validation is not None and result.output_validation.valid
    assert len(result.raw_refs) == 1


def test_answer_from_supported_inference_keeps_explicit_inference_mode(tmp_path):
    premise = _entry(
        ClaimClass.SOURCE_FACT,
        "The measured input increased.",
        source_refs=["source-input"],
    )
    inference = _entry(
        ClaimClass.SUPPORTED_INFERENCE,
        "The response follows from the measured input.",
        premise_refs=[premise.id],
    )
    ledger = _ledger(premise, inference)
    response = _wire(
        sections=[
            _span(
                "From that measured increase, the response follows.",
                "inference",
                "E2",
            )
        ]
    )

    result, _harness, _endpoint = _compose(tmp_path, ledger, response)

    assert result.status == CompositionStatus.COMPOSED
    assert result.output.sections[0].rendering_mode.value == "inference"
    assert result.output.sections[0].ledger_entry_ids == [inference.id]


def test_conjectural_output_remains_visibly_conjectural(tmp_path):
    conjecture = _entry(
        ClaimClass.SURVIVING_CONJECTURE,
        "A latent feedback loop may explain the pattern.",
        formal_artifact_refs=["artifact-survivor"],
    )
    result, _harness, _endpoint = _compose(
        tmp_path,
        _ledger(conjecture),
        _wire(
            sections=[
                _span(
                    "One surviving conjecture is a latent feedback loop.",
                    "conjecture",
                )
            ]
        ),
    )

    assert result.status == CompositionStatus.COMPOSED
    assert result.output.sections[0].rendering_mode.value == "conjecture"
    assert result.output.sections[0].ledger_entry_ids == [conjecture.id]


def test_partial_result_preserves_answered_and_unknown_parts(tmp_path):
    fact = _entry(
        ClaimClass.SOURCE_FACT,
        "The first interval is covered.",
        source_refs=["source-interval"],
    )
    unknown = _entry(
        ClaimClass.UNKNOWN,
        "The second interval is not covered by the record.",
    )
    response = _wire(
        sections=[_span("The first interval is covered.", "fact")],
        unresolved_items=[
            {
                "description": "The second interval remains unknown.",
                "reason": "The ledger records no coverage.",
                "ledger_entry_handles": ["E2"],
            }
        ],
        resolution="partially_answered",
        resolution_reason="Only the first interval is established.",
    )

    result, _harness, _endpoint = _compose(tmp_path, _ledger(fact, unknown), response)

    assert result.status == CompositionStatus.COMPOSED
    assert result.output.resolution.value == "partially_answered"
    assert result.output.unresolved_items[0].ledger_entry_ids == [unknown.id]


@pytest.mark.parametrize(
    ("resolution", "reason"),
    [
        ("insufficient_evidence", "No ledger entry establishes the answer."),
        ("outside_scope", "The requested subject is outside the ledger's scope."),
        ("underdetermined", "The ledger leaves more than one answer possible."),
    ],
)
def test_no_answer_resolutions_are_successful_epistemic_outputs(
    tmp_path, resolution, reason
):
    unknown = _entry(ClaimClass.UNKNOWN, "The requested answer is not established.")
    response = _wire(
        unresolved_items=[
            {
                "description": "The requested answer remains missing.",
                "ledger_entry_handles": ["E1"],
            }
        ],
        resolution=resolution,
        resolution_reason=reason,
    )

    result, _harness, _endpoint = _compose(tmp_path, _ledger(unknown), response)

    assert result.status == CompositionStatus.COMPOSED
    assert result.successful
    assert result.output.resolution.value == resolution
    assert result.output.sections == []


def test_conflicting_evidence_renders_only_as_conflict(tmp_path):
    conflict = SourceConflictV1.create(
        conflicting_refs=["source-left", "source-right"],
        description="The two measurements disagree.",
    )
    entry = _entry(
        ClaimClass.CONFLICT,
        "The available measurements conflict.",
        source_conflict_refs=[conflict.id],
    )
    response = _wire(
        sections=[_span("The measurements remain in conflict.", "conflict")],
        resolution="conflicting_evidence",
        resolution_reason="The validated sources disagree.",
    )

    result, _harness, _endpoint = _compose(
        tmp_path, _ledger(entry, conflicts=[conflict]), response
    )

    assert result.status == CompositionStatus.COMPOSED
    assert result.output.resolution.value == "conflicting_evidence"
    assert result.output.sections[0].rendering_mode.value == "conflict"


@pytest.mark.parametrize(
    "requested_class", ["supported_inference", "surviving_conjecture"]
)
def test_new_semantics_return_typed_successful_amendment_without_ids_or_refs(
    tmp_path, requested_class
):
    fact = _entry(
        ClaimClass.SOURCE_FACT,
        "The record establishes one premise.",
        source_refs=["source-1"],
    )
    response = _wire(
        resolution="underdetermined",
        resolution_reason="A new ledger entry is required before composition.",
        ledger_amendment_request={
            "requested_class": requested_class,
            "proposed_claim": "A bounded new semantic step to evaluate in Stage A.",
            "reason": "The existing ledger has no entry for this step.",
        },
    )

    result, _harness, _endpoint = _compose(tmp_path, _ledger(fact), response)

    assert result.status == CompositionStatus.LEDGER_AMENDMENT_NEEDED
    assert result.successful
    assert result.output is None
    assert result.amendment_needed.requested_class == requested_class
    amendment_data = result.amendment_needed.model_dump(mode="json")
    assert set(amendment_data) == {"requested_class", "proposed_claim", "reason"}
    assert "sha256:" not in json.dumps(amendment_data)
    assert not any("ref" in key for key in amendment_data)
    assert result.call_receipt is not None
    assert len(result.raw_refs) == 1


def test_unknown_handle_is_locally_repaired_and_never_becomes_an_entry(tmp_path):
    fact = _entry(
        ClaimClass.SOURCE_FACT,
        "A grounded fact.",
        source_refs=["source-1"],
    )
    invalid = _wire(sections=[_span("A grounded fact.", "fact", "E99")])
    valid = _wire(sections=[_span("A grounded fact.", "fact", "E1")])
    harness = Harness(tmp_path / "run")
    adapter = LLMAdapter(
        {"thesis": MockEndpoint([invalid, valid])},
        harness.blobs,
        retry_max=2,
    )

    result = BridgeComposer(adapter).compose(_ledger(fact), _request())

    assert result.status == CompositionStatus.COMPOSED
    assert result.output.sections[0].ledger_entry_ids == [fact.id]
    assert result.call_receipt.attempts == 2
    assert [attempt.valid for attempt in result.call_receipt.attempt_trace] == [
        False,
        True,
    ]
    assert len(result.raw_refs) == 2
    assert len(result.repair_diagnostic_refs) == 1


def test_canonical_id_handle_and_persistent_mode_laundering_fail_boundedly(tmp_path):
    fact = _entry(
        ClaimClass.SOURCE_FACT,
        "A grounded fact.",
        source_refs=["source-1"],
    )
    invalid_handle = _wire(
        sections=[_span("A grounded fact.", "fact", fact.id)]
    )
    invalid_mode = _wire(
        sections=[_span("A grounded fact presented as inference.", "inference", "E1")]
    )
    harness = Harness(tmp_path / "run")
    adapter = LLMAdapter(
        {
            "thesis": MockEndpoint(
                [invalid_handle, invalid_mode, json.dumps("E99")]
            )
        },
        harness.blobs,
        retry_max=2,
    )

    result = BridgeComposer(adapter).compose(_ledger(fact), _request())

    assert result.status == CompositionStatus.VALIDATION_FAILED
    assert not result.successful
    assert result.failure.code == "BRIDGE_COMPOSITION_REPAIR_EXHAUSTED"
    assert result.call_receipt is not None and result.call_receipt.attempts == 3
    assert len(result.raw_refs) == 3
    assert len(result.repair_diagnostic_refs) == 3


def test_invalid_ledger_and_target_mismatch_do_not_call_the_model(tmp_path):
    ungrounded = _entry(ClaimClass.SOURCE_FACT, "An ungrounded alleged fact.")
    ledger = _ledger(ungrounded)
    calls = 0

    def must_not_call(_prompt):
        nonlocal calls
        calls += 1
        raise AssertionError("model call must not occur")

    harness = Harness(tmp_path / "run")
    composer = BridgeComposer(
        LLMAdapter({"thesis": MockEndpoint(must_not_call)}, harness.blobs)
    )
    invalid = composer.compose(ledger, _request())
    assert invalid.status == CompositionStatus.VALIDATION_FAILED
    assert invalid.failure.code == "BRIDGE_LEDGER_INVALID"

    valid_fact = _entry(
        ClaimClass.SOURCE_FACT,
        "A grounded fact.",
        source_refs=["source-1"],
    )
    mismatch = composer.compose(
        _ledger(valid_fact), _request(output_target="different-target")
    )
    assert mismatch.status == CompositionStatus.VALIDATION_FAILED
    assert mismatch.failure.code == "BRIDGE_OUTPUT_TARGET_MISMATCH"
    assert calls == 0


def test_empty_valid_ledger_with_uncovered_requirement_can_abstain(tmp_path):
    requirement = UncoveredRequirementV1.create(
        requirement="Obtain a measurement for the missing interval.",
        reason="No accepted source covers it.",
    )
    ledger = _ledger(uncovered=[requirement])
    response = _wire(
        unresolved_items=[
            {"description": "The required measurement remains unavailable."}
        ],
        resolution="insufficient_evidence",
        resolution_reason="The validated ledger has an uncovered requirement.",
    )

    result, _harness, _endpoint = _compose(tmp_path, ledger, response)

    assert result.status == CompositionStatus.COMPOSED
    assert result.output.resolution.value == "insufficient_evidence"
    assert result.output.unresolved_items[0].ledger_entry_ids is None
