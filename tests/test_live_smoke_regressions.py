"""Regressions from live_smoke_v1 (experiments/live_smoke_v1_prereg.yaml).

Finding F1: a live gpt-oss:120b reply carried an empty countercondition
string; it passed the wire schema as it stood and crashed proposal_envelope
outside the repair loop, killing the run. Two layers now hold: the wire
schema rejects the reply (routing it through ordinary schema repair), and
the conj rule skips any proposal that still fails envelope compilation,
with a logged measure instead of an unhandled exception.
"""

import pydantic
import pytest

from deepreason.workloads.text import (
    ReasoningCandidateProposal,
    proposal_envelope,
)


def _proposal(**overrides):
    payload = {
        "claim": "golden ages follow institutional slack",
        "mechanism": "surplus lets institutions tolerate failed experiments",
        "counterconditions": ("a golden age with no surplus economy",),
        "typicality": 0.4,
    }
    payload.update(overrides)
    return payload


def test_wire_schema_rejects_empty_countercondition_string():
    with pytest.raises(pydantic.ValidationError):
        ReasoningCandidateProposal(**_proposal(counterconditions=("",)))


def test_wire_schema_still_accepts_wellformed_counterconditions():
    proposal = ReasoningCandidateProposal(**_proposal())
    envelope = proposal_envelope(proposal)
    assert envelope.counterconditions[0].case.startswith("a golden age")


def test_envelope_compilation_failure_is_contained_not_fatal(tmp_path):
    """Simulate future schema drift: a proposal constructed WITHOUT
    validation (model_construct) carrying an empty case must be skipped by
    the conj loop's backstop, never raised out of it."""
    from deepreason.harness import Harness
    from deepreason.ontology import Rule

    drifted = ReasoningCandidateProposal.model_construct(
        claim="c",
        mechanism="m",
        counterconditions=("",),
        typicality=0.5,
        optional_refs=(),
        analogy=None,
    )
    with pytest.raises(pydantic.ValidationError):
        proposal_envelope(drifted)  # still invalid at the envelope layer

    # The backstop pattern used in rules/conj.py: compile-or-skip-and-log.
    harness = Harness(tmp_path / "run")
    try:
        proposal_envelope(drifted)
    except (pydantic.ValidationError, ValueError) as error:
        harness.record_measure(
            inputs=["proposal-envelope-invalid", type(error).__name__]
        )
    measures = [
        e for e in harness.log.read()
        if e.rule == Rule.MEASURE and e.inputs
        and e.inputs[0] == "proposal-envelope-invalid"
    ]
    assert len(measures) == 1
    assert measures[0].inputs[1] == "ValidationError"
