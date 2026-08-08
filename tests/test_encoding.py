"""Encoder-role delegation (D2 rev 2, Item 7, R38): the coder seat
authors commitment code for an already-admitted conjecture's own
prose, via a follow-up call that reuses property_designer's endpoint."""

import json

from deepreason.llm.adapter import LLMAdapter
from deepreason.llm.endpoints import MockEndpoint
from deepreason.rules.encoding import draft_encoded_commitment

ENCODER_OUTPUT = json.dumps({
    "source": "def solve(x):\n    return x * 2",
    "entry": "solve",
    "tests": [{"in": [1], "out": 2}],
})


def test_no_coder_seat_bound_is_a_no_op(harness):
    adapter = LLMAdapter({}, harness.blobs, retry_max=2)

    result = draft_encoded_commitment(harness, adapter, "doubling", "repeated addition")

    assert result is None


def test_bound_coder_seat_delegates_to_the_encoder_template(harness):
    adapter = LLMAdapter(
        {"property_designer": MockEndpoint([ENCODER_OUTPUT])},
        harness.blobs,
        retry_max=2,
    )

    result = draft_encoded_commitment(
        harness, adapter, "doubling composes with addition", "multiplication distributes"
    )

    assert result == {
        "source": "def solve(x):\n    return x * 2",
        "entry": "solve",
        "tests": [{"in": [1], "out": 2}],
    }
    # The delegation call is logged even though it minted no artifact directly.
    assert any(
        e.llm and e.llm.role == "property_designer" for e in harness.log.read()
    )
