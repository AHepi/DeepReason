"""C6 bridge rendering compatibility and unresolved-output validation."""

from __future__ import annotations

import pytest

from deepreason.bridge.models import (
    BridgeOutputV1,
    ClaimClass,
    ClaimLedgerEntryV1,
    ClaimLedgerV1,
    ClaimUseV1,
    RenderingMode,
    UnresolvedItemV1,
)
from deepreason.bridge.validate import (
    RENDERING_COMPATIBILITY,
    validate_bridge_output,
)


def _entry(claim_class):
    references = {
        ClaimClass.SOURCE_FACT: {"source_refs": ["source-1"]},
        ClaimClass.RECORDED_OBSERVATION: {"event_refs": ["event-1"]},
        ClaimClass.SUPPORTED_INFERENCE: {},
        ClaimClass.SURVIVING_CONJECTURE: {
            "formal_artifact_refs": ["artifact-novel"]
        },
        ClaimClass.ASSUMPTION: {},
        ClaimClass.UNKNOWN: {},
        ClaimClass.CONFLICT: {"conflict_refs": ["left", "right"]},
    }[claim_class]
    return ClaimLedgerEntryV1.create(
        claim_class=claim_class,
        claim=f"A {claim_class.value} claim.",
        **references,
    )


def _ledger(entry):
    entries = [entry]
    if entry.claim_class == ClaimClass.SUPPORTED_INFERENCE:
        premise = ClaimLedgerEntryV1.create(
            claim_class="source_fact",
            claim="Premise.",
            source_refs=["source-1"],
        )
        entry = ClaimLedgerEntryV1.create(
            claim_class="supported_inference",
            claim=entry.claim,
            premise_refs=[premise.id],
        )
        entries = [premise, entry]
    return (
        ClaimLedgerV1.create(
            problem_ref="problem-1",
            formal_seq=2,
            output_target="answer",
            entries=entries,
        ),
        entry,
    )


def _output(ledger, entry, mode, *, resolution="answered"):
    section = ClaimUseV1.create(
        span_id="span-1",
        text=entry.claim,
        rendering_mode=mode,
        ledger_entry_ids=[entry.id],
    )
    return BridgeOutputV1.create(
        claim_ledger_id=ledger.id,
        sections=[section],
        resolution=resolution,
    )


@pytest.mark.parametrize("claim_class", list(ClaimClass))
def test_each_class_validates_only_in_its_explicit_default_mode(claim_class):
    entry = _entry(claim_class)
    ledger, entry = _ledger(entry)
    allowed = RENDERING_COMPATIBILITY[claim_class]
    assert len(allowed) == 1
    output = _output(ledger, entry, next(iter(allowed)))
    assert validate_bridge_output(ledger, output).valid


@pytest.mark.parametrize(
    ("claim_class", "invalid_mode"),
    [
        (claim_class, mode)
        for claim_class in ClaimClass
        for mode in RenderingMode
        if mode not in RENDERING_COMPATIBILITY[claim_class]
    ],
)
def test_every_invalid_cross_class_rendering_is_rejected(claim_class, invalid_mode):
    entry = _entry(claim_class)
    ledger, entry = _ledger(entry)
    report = validate_bridge_output(ledger, _output(ledger, entry, invalid_mode))
    assert not report.valid
    assert any(
        finding.code
        in {"BRIDGE_RENDERING_MODE_TOO_STRONG", "BRIDGE_UNKNOWN_ASSERTS_FACT"}
        and finding.span_id == "span-1"
        and entry.id in finding.relevant_ledger_ids
        and finding.allowed_correction_modes
        for finding in report.findings
    )


def test_unknown_cannot_back_a_positive_fact_and_conjecture_cannot_render_as_fact():
    unknown = _entry(ClaimClass.UNKNOWN)
    unknown_ledger, unknown = _ledger(unknown)
    unknown_report = validate_bridge_output(
        unknown_ledger, _output(unknown_ledger, unknown, "fact")
    )
    assert any(
        finding.code == "BRIDGE_UNKNOWN_ASSERTS_FACT"
        for finding in unknown_report.findings
    )

    conjecture = _entry(ClaimClass.SURVIVING_CONJECTURE)
    ledger, conjecture = _ledger(conjecture)
    report = validate_bridge_output(ledger, _output(ledger, conjecture, "fact"))
    assert any(
        finding.code == "BRIDGE_RENDERING_MODE_TOO_STRONG"
        for finding in report.findings
    )


def test_recorded_observation_fact_mode_requires_explicit_profile_permission():
    observation = _entry(ClaimClass.RECORDED_OBSERVATION)
    ledger, observation = _ledger(observation)
    output = _output(ledger, observation, "fact")
    assert not validate_bridge_output(ledger, output).valid
    assert validate_bridge_output(
        ledger, output, allow_observation_as_fact=True
    ).valid


def test_spans_require_known_ledger_mapping_and_matching_ledger():
    fact = _entry(ClaimClass.SOURCE_FACT)
    ledger, fact = _ledger(fact)
    unmapped = ClaimUseV1.create(
        span_id="span-empty",
        text="Unmapped prose.",
        rendering_mode="fact",
        ledger_entry_ids=[],
    )
    output = BridgeOutputV1.create(
        claim_ledger_id=ledger.id,
        sections=[unmapped],
        resolution="answered",
    )
    assert any(
        finding.code == "BRIDGE_SPAN_UNMAPPED"
        for finding in validate_bridge_output(ledger, output).findings
    )

    unknown = ClaimUseV1.create(
        span_id="span-unknown",
        text="Unknown mapping.",
        rendering_mode="fact",
        ledger_entry_ids=["sha256:" + "f" * 64],
    )
    other_output = BridgeOutputV1.create(
        claim_ledger_id="sha256:" + "e" * 64,
        sections=[unknown],
        resolution="answered",
    )
    codes = {
        finding.code for finding in validate_bridge_output(ledger, other_output).findings
    }
    assert "BRIDGE_LEDGER_ENTRY_MISSING" in codes
    assert "BRIDGE_LEDGER_REF_UNKNOWN" in codes


def test_empty_answered_fails_but_explicit_unresolved_terminal_successes_validate():
    unknown = _entry(ClaimClass.UNKNOWN)
    ledger, unknown = _ledger(unknown)
    answered = BridgeOutputV1.create(
        claim_ledger_id=ledger.id,
        sections=[],
        resolution="answered",
    )
    assert not validate_bridge_output(ledger, answered).valid

    for resolution in (
        "partially_answered",
        "underdetermined",
        "insufficient_evidence",
        "conflicting_evidence",
        "outside_scope",
    ):
        unresolved = BridgeOutputV1.create(
            claim_ledger_id=ledger.id,
            sections=[],
            unresolved_items=[
                UnresolvedItemV1.create(
                    description="The requested answer remains missing.",
                    ledger_entry_ids=[unknown.id],
                )
            ],
            resolution=resolution,
            resolution_reason="The validated ledger does not establish an answer.",
        )
        assert validate_bridge_output(ledger, unresolved).valid


def test_empty_unresolved_result_requires_a_reason_instead_of_invention():
    unknown = _entry(ClaimClass.UNKNOWN)
    ledger, _ = _ledger(unknown)
    output = BridgeOutputV1.create(
        claim_ledger_id=ledger.id,
        sections=[],
        resolution="insufficient_evidence",
    )
    report = validate_bridge_output(ledger, output)
    assert not report.valid
    assert report.findings[0].pointer == "/resolution_reason"
