"""Compact scratch wire values stay loose, local, strict, and bounded."""

from __future__ import annotations

import json

import pytest
from pydantic import ValidationError

from deepreason.scratch.contracts import (
    MAX_GUIDE_ENTRY_POINTS,
    MAX_GUIDE_OPEN_THREADS,
    SCRATCH_CONTRACT_INSTRUCTIONS,
    ClusterGuideWireContract,
    ClusterGuideWireV1,
    ScratchBlockWireContract,
    ScratchBlockWireV1,
    ScratchLinkWireContract,
    ScratchLinkWireV1,
    ScratchWireReferenceError,
)
from deepreason.scratch.models import ScratchBlockBodyV1, ScratchLinkBodyV1


def _hash(character: str) -> str:
    return f"sha256:{character * 64}"


def test_content_only_block_is_valid_and_optionals_remain_absent():
    wire = ScratchBlockWireV1(content="Maybe compression is the attractor.")

    assert wire.model_dump(exclude_none=True) == {
        "content": "Maybe compression is the attractor."
    }
    assert set(ScratchBlockWireV1.model_json_schema()["required"]) == {"content"}
    canonical = ScratchBlockWireContract().compile(wire)
    assert canonical == ScratchBlockBodyV1(content=wire.content)
    assert canonical.unfinished is None
    assert canonical.possible_next_move is None


def test_blocks_may_be_contradictory_or_explicitly_unresolved():
    first = ScratchBlockWireV1(
        content="The shared vocabulary causes convergence.",
        unfinished="Unknown; no causal evidence yet.",
    )
    second = ScratchBlockWireV1(
        content="The shared vocabulary does not cause convergence.",
        possible_next_move="No clear next move yet.",
    )

    assert first.content != second.content
    assert first.unfinished.startswith("Unknown")
    assert second.why_keep_this is None


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("id", _hash("a")),
        ("body_hash", _hash("b")),
        ("provenance", {"actor": "llm"}),
        ("model", "peer-model"),
        ("route", "provider-route"),
        ("status", "accepted"),
    ],
)
def test_block_contract_rejects_ids_provenance_and_control_fields(field, value):
    with pytest.raises(ValidationError, match="extra_forbidden"):
        ScratchBlockWireV1.model_validate({"content": "valid", field: value})


@pytest.mark.parametrize("field", ["content", "why_keep_this", "unfinished"])
def test_required_or_present_block_text_cannot_be_blank(field):
    value = {"content": "valid", field: "   "}
    with pytest.raises(ValidationError, match="whitespace"):
        ScratchBlockWireV1.model_validate(value)


def test_link_indices_compile_to_harness_owned_canonical_ids():
    contract = ScratchLinkWireContract(
        indexed_block_ids=[_hash("a"), _hash("b")]
    )
    wire = contract.validate_value(
        {
            "from_index": 0,
            "to_index": 1,
            "relation_hint": "may conflict with",
            "holds_when": "The claims use the same scope.",
            "weakens_when": "Their scopes differ.",
            "direction": "directed",
        }
    )
    canonical = contract.compile(wire)

    assert isinstance(canonical, ScratchLinkBodyV1)
    assert canonical.from_ == _hash("a")
    assert canonical.to == _hash("b")
    assert canonical.relation_hint == "may conflict with"
    assert canonical.holds_when == "The claims use the same scope."


def test_link_handles_compile_and_open_relation_vocabulary_remains_legal():
    contract = ScratchLinkWireContract(
        handles={"B_left": _hash("a"), "B_right": _hash("b")}
    )
    canonical = contract.parse_compile(
        json.dumps(
            {
                "from_handle": "B_left",
                "to_handle": "B_right",
                "relation_hint": "rhymes unexpectedly with",
                "because": "This is provisional and may be misleading.",
                "direction": "symmetric",
            }
        )
    )

    assert canonical.from_ == _hash("a")
    assert canonical.to == _hash("b")
    assert canonical.direction.value == "symmetric"


@pytest.mark.parametrize(
    "payload",
    [
        {"to_index": 0, "relation_hint": "may relate"},
        {"from_index": 0, "relation_hint": "may relate"},
        {
            "from_index": 0,
            "from_handle": "B1",
            "to_index": 1,
            "relation_hint": "may relate",
        },
        {
            "from_index": 0,
            "to_index": 1,
            "to_handle": "B2",
            "relation_hint": "may relate",
        },
    ],
)
def test_link_requires_exactly_one_local_reference_per_endpoint(payload):
    with pytest.raises(ValidationError, match="exactly one"):
        ScratchLinkWireV1.model_validate(payload)


@pytest.mark.parametrize("value", [_hash("a"), "a" * 64])
def test_canonical_ids_cannot_be_smuggled_as_handles(value):
    with pytest.raises(ValidationError, match="canonical IDs are forbidden"):
        ScratchLinkWireV1(
            from_handle=value,
            to_handle="B2",
            relation_hint="may relate",
        )
    with pytest.raises(ValidationError, match="canonical IDs are forbidden"):
        ClusterGuideWireV1(working_focus="Unresolved", entry_points=[value])


def test_link_indices_are_strict_and_unknown_references_fail_locally():
    with pytest.raises(ValidationError):
        ScratchLinkWireV1(
            from_index="0",
            to_index=1,
            relation_hint="may relate",
        )
    contract = ScratchLinkWireContract(indexed_block_ids=[_hash("a")])
    wire = ScratchLinkWireV1(
        from_index=0,
        to_index=1,
        relation_hint="may relate",
    )
    with pytest.raises(ScratchWireReferenceError) as raised:
        contract.compile(wire)
    assert raised.value.code == "SCRATCH_WIRE_REFERENCE_INVALID"
    assert raised.value.pointer == "/to_index"


def test_minimal_guide_may_leave_all_uncertainty_structure_absent():
    guide = ClusterGuideWireV1(working_focus="The local structure remains unclear.")

    assert guide.model_dump(exclude_none=True) == {
        "working_focus": "The local structure remains unclear."
    }
    assert set(ClusterGuideWireV1.model_json_schema()["required"]) == {
        "working_focus"
    }


def test_guide_contract_resolves_only_provided_entry_handles():
    contract = ClusterGuideWireContract(
        handles={"B1": _hash("a"), "B2": _hash("b")}
    )
    draft = contract.parse_compile(
        '{"working_focus":"Possible mechanisms, still unresolved",'
        '"open_threads":["Which direction is causal?"],'
        '"entry_points":["B2","B1"]}'
    )

    assert draft.working_focus.endswith("unresolved")
    assert draft.entry_points == [_hash("b"), _hash("a")]
    assert draft.local_summary is None
    with pytest.raises(TypeError):
        draft.entry_points.append(_hash("c"))


def test_guide_lists_are_bounded_and_unknown_handle_is_not_inferred():
    with pytest.raises(ValidationError, match="at most 64 items"):
        ClusterGuideWireV1(
            working_focus="Bounded",
            open_threads=[f"thread {index}" for index in range(MAX_GUIDE_OPEN_THREADS + 1)],
        )
    with pytest.raises(ValidationError, match="at most 64 items"):
        ClusterGuideWireV1(
            working_focus="Bounded",
            entry_points=[f"B{index}" for index in range(MAX_GUIDE_ENTRY_POINTS + 1)],
        )
    contract = ClusterGuideWireContract(handles={"B1": _hash("a")})
    wire = ClusterGuideWireV1(working_focus="Unknown", entry_points=["B9"])
    with pytest.raises(ScratchWireReferenceError) as raised:
        contract.compile(wire)
    assert raised.value.pointer == "/entry_points/0"


def test_guide_cannot_author_cluster_snapshot_identity_or_provenance():
    for field, value in (
        ("cluster_id", _hash("a")),
        ("based_on_snapshot", _hash("b")),
        ("authored_by", {"model": "peer"}),
        ("provenance", {"actor": "llm"}),
    ):
        with pytest.raises(ValidationError, match="extra_forbidden"):
            ClusterGuideWireV1.model_validate(
                {"working_focus": "still unresolved", field: value}
            )


def test_wire_schemas_are_closed_and_prompt_instructions_preserve_uncertainty():
    for contract in (
        ScratchBlockWireContract(),
        ScratchLinkWireContract(indexed_block_ids=[_hash("a"), _hash("b")]),
        ClusterGuideWireContract(handles={"B1": _hash("a")}),
    ):
        assert contract.model_json_schema()["additionalProperties"] is False

    for sentence in (
        "Scratch material is non-authoritative.",
        "It may contradict itself.",
        "Do not turn uncertainty into a confident fact.",
        "Do not invent a reason merely to fill an optional field.",
        "Relationships are provisional.",
        "A guide is a temporary navigation aid.",
    ):
        assert sentence in SCRATCH_CONTRACT_INSTRUCTIONS
