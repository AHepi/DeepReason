"""Wire transports are strict, local, and compile to canonical role models."""

import json

import pytest

from deepreason.llm.contracts import (
    ArgumentativeCriticOutput,
    ConjecturerOutput,
    DefenderOutput,
    JudgeRuling,
    SynthesizerOutput,
    VariatorOutput,
)
from deepreason.llm.wire import (
    AliasTable,
    ConjecturerWireContract,
    CriticTargetRequiredError,
    CriticWireContract,
    DefenderWireContract,
    DirectWireContract,
    JudgeWireContract,
    PairwiseJudgeWireContract,
    SynthesizerWireContract,
    UnknownAliasError,
    VariatorWireContract,
    wire_contract_for,
)


def test_compact_conjecturer_resolves_local_aliases():
    table = AliasTable({"A1": "a" * 64, "A2": "b" * 64})
    contract = ConjecturerWireContract(table)
    output = contract.parse_compile(
        json.dumps(
            {
                "candidates": [
                    {"content": "a mechanism", "typicality": 0.2, "neighbours": ["A2"]}
                ]
            }
        )
    )
    assert isinstance(output, ConjecturerOutput)
    assert output.candidates[0].refs[0].target == "b" * 64


def test_unknown_alias_is_a_validation_failure_not_an_inference():
    contract = ConjecturerWireContract(AliasTable({"A1": "a" * 64}))
    with pytest.raises(UnknownAliasError, match="A9"):
        contract.parse_compile(
            '{"candidates":[{"content":"x","typicality":0.5,"neighbours":["A9"]}]}'
        )


def test_every_model_visible_object_is_closed():
    schema = ConjecturerWireContract().model_json_schema()
    assert schema["additionalProperties"] is False
    candidate = schema["$defs"]["CompactConjectureCandidate"]
    assert candidate["additionalProperties"] is False


@pytest.mark.parametrize(
    ("contract", "raw", "canonical_type"),
    [
        (
            CriticWireContract(
                AliasTable({"A1": "target-id", "K1": "input-id"}),
                "target-id",
            ),
            {
                "attack": True,
                "target_alias": "A1",
                "claim": "the mechanism is absent",
                "grounds": "the text names no cause",
                "cited_input_aliases": ["K1"],
            },
            ArgumentativeCriticOutput,
        ),
        (
            DefenderWireContract(AliasTable({"K1": "first clause"})),
            {"clauses": [{"item_alias": "K1", "response": "the cause is explicit"}]},
            DefenderOutput,
        ),
        (
            JudgeWireContract(AliasTable({"K1": "exact decisive span"})),
            {"decision": "fail", "decisive_point_alias": "K1", "grounds": "specific"},
            JudgeRuling,
        ),
        (
            VariatorWireContract(),
            {"edits": [{"content": "changed claim", "changed_fields": ["claim"]}]},
            VariatorOutput,
        ),
        (
            SynthesizerWireContract(AliasTable({"A1": "left-id", "A2": "right-id"})),
            {"relation": "A1 constrains A2", "depends_on": ["A1", "A2"]},
            SynthesizerOutput,
        ),
    ],
)
def test_role_wire_contracts_compile_to_existing_canonical_models(
    contract, raw, canonical_type
):
    assert isinstance(contract.parse_compile(json.dumps(raw)), canonical_type)


@pytest.mark.parametrize(
    "field",
    ["model", "endpoint", "provider", "tool", "command", "delegate", "status", "route"],
)
def test_control_fields_are_rejected(field):
    contract = DirectWireContract(ConjecturerOutput)
    value = {
        "candidates": [{"content": "x", "typicality": 0.5}],
        field: "unauthorized",
    }
    with pytest.raises(ValueError):
        contract.validate_value(value)


def test_counterexample_payload_remains_opaque_domain_data():
    contract = DirectWireContract(ArgumentativeCriticOutput)
    output = contract.parse_compile(
        '{"attack":true,"case":"fault","counterexample":[{"status":"draft"}]}'
    )
    assert output.counterexample == [{"status": "draft"}]


def test_compact_critic_target_is_bound_in_schema_and_validation():
    contract = CriticWireContract(
        AliasTable({"A1": "actual-target", "A2": "standing-attack"}),
        "actual-target",
    )
    assert contract.model_json_schema()["properties"]["target_alias"]["const"] == "A1"
    with pytest.raises(ValueError, match="Input should be 'A1'"):
        contract.parse_compile(
            '{"attack":false,"target_alias":"A2","claim":"",'
            '"grounds":"","cited_input_aliases":[]}'
        )


def test_compact_critic_factory_fails_closed_without_attacked_target():
    with pytest.raises(CriticTargetRequiredError):
        wire_contract_for(
            "argumentative_critic",
            ArgumentativeCriticOutput,
            "compact",
            AliasTable({"A1": "target-id"}),
        )


def test_frontier_factory_retains_direct_canonical_fast_path():
    contract = wire_contract_for("conjecturer", ConjecturerOutput, "frontier")
    assert isinstance(contract, DirectWireContract)
    output = contract.parse_compile(
        '{"candidates":[{"content":"x","typicality":0.5,"refs":[]}]}'
    )
    assert isinstance(output, ConjecturerOutput)


def test_compact_pairwise_judge_preserves_labels_and_exact_decisive_span():
    contract = PairwiseJudgeWireContract(
        AliasTable({"K1": "exact candidate A span", "K2": "candidate B span"})
    )
    ruling = contract.parse_compile(
        '{"winner":"A","decisive_point_alias":"K1"}'
    )
    assert ruling.winner == "A"
    assert ruling.decisive_point == "exact candidate A span"
