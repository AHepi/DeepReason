"""C6 deterministic claim-ledger reference discipline."""

from __future__ import annotations

import pytest

from deepreason.bridge.models import (
    ClaimClass,
    ClaimLedgerEntryV1,
    ClaimLedgerV1,
    SourceConflictV1,
    UncoveredRequirementV1,
)
from deepreason.bridge.validate import validate_claim_ledger


def _hash(character: str) -> str:
    return "sha256:" + character * 64


def _entry(claim_class, **values):
    return ClaimLedgerEntryV1.create(
        claim_class=claim_class,
        claim=values.pop("claim", f"A {ClaimClass(claim_class).value} claim."),
        **values,
    )


def _ledger(entries, **values):
    return ClaimLedgerV1.create(
        problem_ref="problem-1",
        formal_seq=4,
        output_target="answer",
        entries=entries,
        **values,
    )


@pytest.mark.parametrize(
    ("claim_class", "references"),
    [
        (ClaimClass.SOURCE_FACT, {"source_refs": ["source-1"]}),
        (ClaimClass.RECORDED_OBSERVATION, {"trace_refs": ["trace-1"]}),
        (ClaimClass.ASSUMPTION, {}),
        (ClaimClass.UNKNOWN, {}),
    ],
)
def test_valid_basic_claim_classes(claim_class, references):
    entry = _entry(claim_class, **references)
    report = validate_claim_ledger(_ledger([entry]))
    assert report.valid
    assert report.findings == []


def test_structural_evidence_grounds_fact_but_scratch_provenance_does_not():
    grounded = _entry(ClaimClass.SOURCE_FACT, evidence_refs=["evidence-1"])
    scratch_only = _entry(
        ClaimClass.SOURCE_FACT,
        claim="Scratch alone cannot ground this.",
        scratch_refs=[_hash("a")],
    )

    assert validate_claim_ledger(_ledger([grounded])).valid
    report = validate_claim_ledger(_ledger([scratch_only]))
    assert not report.valid
    assert [finding.code for finding in report.findings] == [
        "BRIDGE_SOURCE_FACT_UNGROUNDED"
    ]
    assert report.findings[0].relevant_ledger_ids == [scratch_only.id]
    assert report.findings[0].allowed_correction_modes


@pytest.mark.parametrize(
    "references",
    [
        {"evidence_refs": ["evidence-1"]},
        {"event_refs": ["event-1"]},
        {"trace_refs": ["trace-1"]},
        {"formal_observation_refs": ["observation-1"]},
    ],
)
def test_each_observation_grounding_channel_is_valid(references):
    observation = _entry(ClaimClass.RECORDED_OBSERVATION, **references)
    assert validate_claim_ledger(_ledger([observation])).valid


def test_ungrounded_observation_and_inference_without_premises_fail():
    observation = _entry(ClaimClass.RECORDED_OBSERVATION)
    inference = _entry(ClaimClass.SUPPORTED_INFERENCE)
    report = validate_claim_ledger(_ledger([observation, inference]))
    assert {finding.code for finding in report.findings} == {
        "BRIDGE_OBSERVATION_UNGROUNDED",
        "BRIDGE_INFERENCE_PREMISES_MISSING",
    }


def test_inference_requires_a_known_ledger_premise():
    premise = _entry(ClaimClass.SOURCE_FACT, source_refs=["source-1"])
    inference = _entry(ClaimClass.SUPPORTED_INFERENCE, premise_refs=[premise.id])
    assert validate_claim_ledger(_ledger([premise, inference])).valid

    unknown = _entry(ClaimClass.SUPPORTED_INFERENCE, premise_refs=[_hash("f")])
    report = validate_claim_ledger(_ledger([unknown]))
    assert any(finding.code == "BRIDGE_LEDGER_REF_UNKNOWN" for finding in report.findings)


def test_novel_conjecture_is_legal_without_external_evidence_but_needs_artifact():
    conjecture = _entry(
        ClaimClass.SURVIVING_CONJECTURE,
        claim="A genuinely new mechanism may explain the pattern.",
        formal_artifact_refs=["artifact-novel"],
    )
    assert conjecture.source_refs is None
    assert conjecture.evidence_refs is None
    assert validate_claim_ledger(_ledger([conjecture])).valid

    missing = _entry(ClaimClass.SURVIVING_CONJECTURE)
    report = validate_claim_ledger(_ledger([missing]))
    assert [finding.code for finding in report.findings] == [
        "BRIDGE_CONJECTURE_ARTIFACT_MISSING"
    ]


def test_conflict_requires_two_sides_or_a_known_conflict_object():
    explicit = _entry(
        ClaimClass.CONFLICT, conflict_refs=["source-left", "source-right"]
    )
    assert validate_claim_ledger(_ledger([explicit])).valid

    conflict = SourceConflictV1.create(conflicting_refs=["left", "right"])
    indirect = _entry(ClaimClass.CONFLICT, source_conflict_refs=[conflict.id])
    assert validate_claim_ledger(
        _ledger([indirect], source_conflicts=[conflict])
    ).valid

    missing = _entry(ClaimClass.CONFLICT, conflict_refs=["only-one-side"])
    report = validate_claim_ledger(_ledger([missing]))
    assert any(finding.code == "BRIDGE_CONFLICT_REFS_MISSING" for finding in report.findings)


def test_unknown_and_explicit_uncovered_requirement_are_valid_ledger_outcomes():
    unknown = _entry(ClaimClass.UNKNOWN, claim="The requested value is unknown.")
    assert validate_claim_ledger(_ledger([unknown])).valid

    requirement = UncoveredRequirementV1.create(
        requirement="Obtain a measurement for the missing interval.",
        reason="No observation covers it.",
    )
    assert validate_claim_ledger(_ledger([], uncovered_requirements=[requirement])).valid
    missing = validate_claim_ledger(_ledger([]))
    assert [finding.code for finding in missing.findings] == [
        "BRIDGE_LEDGER_ENTRY_MISSING"
    ]
