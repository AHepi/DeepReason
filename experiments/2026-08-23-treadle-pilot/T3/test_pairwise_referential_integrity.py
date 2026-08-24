"""Test that a named winner with an empty decisive_point triggers a
referential‑integrity block and registers no warrant.

The setup mirrors the pattern in INPUT_test_pattern.txt.
"""

import json

import pytest

from deepreason.config import Config
from deepreason.informal.trial import pairwise_discriminate
from deepreason.llm.adapter import LLMAdapter
from deepreason.llm.endpoints import MockEndpoint
from deepreason.ontology import Problem, ProblemProvenance, Status

# art is defined in the repository's top‑level tests.conftest
from tests.conftest import art


def _pairwise_setup(harness):
    """Create a discrimination problem with two rival artifacts."""
    a = art(
        harness,
        "rival A: the moon's differential pull explains both tides",
    )
    b = art(
        harness,
        "rival B: solar heating explains the tides",
    )
    problem = harness.register_problem(
        Problem(
            id="disc:pi-tides",
            description="discriminate rivals",
            criteria=[],
            provenance=ProblemProvenance.model_validate(
                {"trigger": "discrimination", "from": ["pi-tides", a.id, b.id]}
            ),
        )
    )
    return problem, a, b


def test_empty_decisive_point_blocks_referential_integrity(harness):
    """A named winner with an empty decisive_point must block on referential
    integrity and produce no warrant."""
    problem, a, b = _pairwise_setup(harness)

    # Two consistent rulings, but both have an empty decisive_point.
    responses = [
        json.dumps({"winner": "A", "decisive_point": ""}),
        json.dumps({"winner": "B", "decisive_point": ""}),
    ]

    adapter = LLMAdapter(
        {"judge": MockEndpoint(responses)},
        harness.blobs,
        retry_max=2,
    )

    result = pairwise_discriminate(
        harness,
        problem,
        a.id,
        b.id,
        adapter,
        Config(),
        authority="status",
    )

    # No warrant should be produced.
    assert result is None

    # Both candidates remain ACCEPTED (unresolved).
    assert harness.state.status[a.id] == Status.ACCEPTED
    assert harness.state.status[b.id] == Status.ACCEPTED

    # The harness log must contain a referential‑integrity block event.
    blocks = [
        e
        for e in harness.log.read()
        if any(t == "trial-blocked:referential-integrity" for t in e.inputs)
    ]
    assert blocks, "Expected a referential‑integrity block event in the log"
