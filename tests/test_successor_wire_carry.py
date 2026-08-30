"""The optional field SURVIVES the wire, on both criticism contracts.

Operator law, 2026-08-29 (CLAUDE.md): "This should be an optional field the LLM
can fill in." The field is only worth having if a value the model actually
wrote reaches the object the rest of the harness reads. That crossing happens
in exactly two places -- `llm/wire.py`'s batch-critic compile and its compact/
atomic critic compile -- and it was measured UNGUARDED: replacing both with
`None` left 97 tests green, so the whole channel could have become a silent
no-op with nothing red.

What is asserted here is the CARRY and only the carry: a filled question in the
model's own JSON arrives on the contract object, verbatim, by both roads. The
companion claim -- that nothing which DECIDES may read the field -- belongs to
tests/test_successor_law_line.py and is not restated here.

Both roads are exercised through `parse_compile`, the same entry the adapter
uses, rather than by constructing a wire object directly: a carry that works
only when the value is handed in by hand is not the carry the law asks for.
"""

from __future__ import annotations

import json

from deepreason.llm.contracts import ArgumentativeCriticOutput, BatchCriticOutput
from deepreason.llm.wire import (
    AliasTable,
    AtomicCriticWireContractV1,
    BatchCriticWireContractV2,
    CriticWireContract,
)

QUESTION = "what would settle whether the solar term is measurable at all?"
TARGET = "artifact-under-criticism"


def _batch_contract() -> BatchCriticWireContractV2:
    return BatchCriticWireContractV2(
        AliasTable({"SRC_001": TARGET}), expected_targets=(TARGET,)
    )


def _batch_payload(**extra) -> str:
    case = {"target_alias": "SRC_001", "attack": True, "case": "fails at neap"}
    case.update(extra)
    return json.dumps({"cases": [case]})


def _atomic_payload(**extra) -> str:
    body = {
        "attack": True,
        "target_alias": "A1",
        "claim": "fails at neap",
        "grounds": "the record shows two peaks",
        "cited_input_aliases": [],
    }
    body.update(extra)
    return json.dumps(body)


def test_the_batch_critic_wire_carries_a_filled_successor_question():
    """`llm/wire.py`'s batch compile. The value is the model's, read out of the
    JSON it returned, and it must arrive on the case unchanged."""
    output = _batch_contract().parse_compile(_batch_payload(successor_question=QUESTION))

    assert isinstance(output, BatchCriticOutput)
    assert len(output.cases) == 1
    assert output.cases[0].target == TARGET          # the case is the right one
    assert output.cases[0].successor_question == QUESTION


def test_the_compact_critic_wire_carries_a_filled_successor_question():
    """`llm/wire.py`'s compact/atomic compile -- the second and only other
    place the field crosses from wire to contract."""
    contract = CriticWireContract(AliasTable({"A1": TARGET}), TARGET)
    output = contract.parse_compile(_atomic_payload(successor_question=QUESTION))

    assert isinstance(output, ArgumentativeCriticOutput)
    assert output.successor_question == QUESTION


def test_the_atomic_critic_contract_carries_it_too():
    """The atomic variant ships under its own contract id and separately frozen
    authority; it must not be a road where the field quietly disappears."""
    contract = AtomicCriticWireContractV1(AliasTable({"A1": TARGET}), TARGET)
    output = contract.parse_compile(_atomic_payload(successor_question=QUESTION))

    assert output.successor_question == QUESTION


def test_an_omitted_field_arrives_as_none_on_both_roads():
    """The other half of "optional": a criticism that proposed nothing is not
    given a proposal, and the absence is None rather than an empty string, so
    an unfilled field canonicalises to the bytes it always did."""
    batch = _batch_contract().parse_compile(_batch_payload())
    assert batch.cases[0].successor_question is None

    compact = CriticWireContract(
        AliasTable({"A1": TARGET}), TARGET
    ).parse_compile(_atomic_payload())
    assert compact.successor_question is None


def test_the_field_is_offered_to_the_model_on_both_schemas():
    """A carry nothing can fill is not a channel. The schema the model is shown
    must declare the field on both roads, or a compliant model can never fill
    it and the tests above would be proving a road no traffic can reach."""
    batch_case = _batch_contract().model_json_schema()["$defs"][
        "BatchCriticCaseWireV2"
    ]
    assert "successor_question" in batch_case["properties"]

    compact = CriticWireContract(
        AliasTable({"A1": TARGET}), TARGET
    ).model_json_schema()
    assert "successor_question" in compact["properties"]
