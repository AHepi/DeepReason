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


def test_all_null_endpoints_report_every_violation_in_one_message():
    """Live regression: a model emitting every reference field null received
    a diagnostic naming only the first violated endpoint, patched it, and
    exhausted its two-repair budget on the undisclosed second violation."""

    with pytest.raises(ValidationError) as captured:
        ScratchLinkWireV1.model_validate({"relation_hint": "may relate"})
    message = str(captured.value)
    assert "from_index or from_handle" in message
    assert "to_index or to_handle" in message


def test_single_element_array_wrapper_is_tolerated_like_a_fence():
    """Live regression: a fully qualified model wrapped one valid object in
    a JSON array and the object-wide extra-field error terminally exhausted
    the route seat's smallest contract."""

    contract = ScratchLinkWireContract(
        handles={"B_left": _hash("a"), "B_right": _hash("b")}
    )
    payload = {
        "from_handle": "B_left",
        "to_handle": "B_right",
        "relation_hint": "rhymes unexpectedly with",
    }
    wire = contract.validate_value([payload])
    assert contract.compile(wire).from_ == _hash("a")

    with pytest.raises(ValueError):
        contract.validate_value([payload, payload])
    with pytest.raises(ValueError):
        contract.validate_value([[payload]])


def test_the_endpoint_rule_is_enforced_by_the_schema_not_only_by_prose():
    """Regression (thinking-off battery, subject 97653fde...): with glm-5.2's
    reasoning disabled, scratch.link.compact.v1 scored 11/20 then 9/20
    first-pass valid with 18 then 22 repairs, and failed production
    qualification twice; scratch.link.minimal.v1 fell with it. The rule it
    kept breaking - exactly one of index/handle per endpoint - existed only
    in the class docstring, while the schema left all four reference fields
    independently optional and nullable.

    A model that treats the schema as the source of structural truth must be
    unable to express the violation at all. This pins that property of the
    SCHEMA, so the constraint cannot regress back into prose.
    """

    from deepreason.scratch.contracts import (
        ScratchLinkMinimalWireContract,
        ScratchLinkWireContract,
    )

    # jsonschema is not a declared dependency of this project, so the
    # behavioural half runs only where it is available; the structural
    # assertions below are unconditional and are what actually pin the fix.
    jsonschema = pytest.importorskip("jsonschema", reason="optional checker")

    handles = {"SCR_001": "a", "SCR_002": "b"}
    for contract in (
        ScratchLinkWireContract(handles=handles),
        ScratchLinkMinimalWireContract(handles=handles),
    ):
        schema = contract.model_json_schema()

        # Structural pin, checked before any optional validator runs: the
        # exclusion is present, per-endpoint, and null is gone from the four
        # reference fields so `required` cannot be satisfied by a null.
        assert schema["allOf"] == [
            {"oneOf": [{"required": ["from_index"]}, {"required": ["from_handle"]}]},
            {"oneOf": [{"required": ["to_index"]}, {"required": ["to_handle"]}]},
        ]
        for name, expected in (
            ("from_index", "integer"), ("to_index", "integer"),
            ("from_handle", "string"), ("to_handle", "string"),
        ):
            field = schema["properties"][name]
            assert field.get("type") == expected, field
            assert "anyOf" not in field and "default" not in field, field

        def valid(document) -> bool:
            try:
                jsonschema.validate(document, schema)
            except jsonschema.ValidationError:
                return False
            return True

        # Legal forms stay legal — including the MIXED endpoint form, which a
        # paired oneOf would wrongly forbid. _require_one_reference_per_endpoint
        # tests each endpoint independently, so the schema must too.
        assert valid({"from_handle": "SCR_001", "to_handle": "SCR_002", "relation_hint": "r"})
        assert valid({"from_index": 0, "to_index": 1, "relation_hint": "r"})
        assert valid({"from_index": 0, "to_handle": "SCR_002", "relation_hint": "r"})

        # Every way of breaking the prose rule is now invalid JSON.
        assert not valid(
            {"from_index": 0, "from_handle": "SCR_001", "to_index": 1, "relation_hint": "r"}
        )
        assert not valid({"to_index": 1, "relation_hint": "r"})
        assert not valid(
            {"from_index": None, "from_handle": None, "to_index": None,
             "to_handle": None, "relation_hint": "r"}
        )
        # An explicit null must not satisfy `required`: that was the escape
        # hatch a nullable type would have left open.
        assert not valid(
            {"from_index": None, "from_handle": "SCR_001", "to_handle": "SCR_002",
             "relation_hint": "r"}
        )

        # _strict_schema closes any subschema carrying `properties`, so the
        # exclusion branches must carry `required` only or they would be
        # rewritten into closed objects that reject relation_hint.
        for clause in schema["allOf"]:
            for branch in clause["oneOf"]:
                assert set(branch) == {"required"}, branch

    # The runtime is NOT narrowed: an explicit null for the unused field is
    # still admitted, exactly as before. The schema tightens what the model
    # is told, never what the harness accepts.
    from deepreason.scratch.contracts import ScratchLinkWireV1

    assert ScratchLinkWireV1(
        from_index=None, from_handle="SCR_001", to_index=1, to_handle=None,
        relation_hint="r",
    ).from_handle == "SCR_001"


def test_legal_handles_are_named_in_the_schema_not_only_enforced_by_the_compiler():
    """Regression (gpt-oss:20b battery, subject 382bfcef...): with thinking off,
    `scratch.link.compact.v1` reached 20/20 eventual validity and STILL failed
    the release gate on 2 alias failures, and `scratch.cluster-guide.compact.v1`
    failed with 4 alias failures and 4 scope violations. The contract knows the
    legal handles — it is built with the alias table and rejects anything
    outside it — but the schema said only {"type": "string"}, so a model
    reading the schema had nothing to choose from and invented handles.

    Corroborating detail from the same battery: the MINIMAL cluster guide,
    which has no handle field at all, scored 20/20.

    The v6 conjecturer already binds its alias arrays this way; this pins the
    same treatment for the scratch contracts.
    """

    from deepreason.scratch.contracts import (
        ClusterGuideMinimalWireContract,
        ClusterGuideWireContract,
        ScratchLinkMinimalWireContract,
        ScratchLinkWireContract,
    )

    handles = {"SCR_001": "a", "SCR_002": "b"}
    legal = ["SCR_001", "SCR_002"]

    for contract in (
        ScratchLinkWireContract(handles=handles),
        ScratchLinkMinimalWireContract(handles=handles),
    ):
        properties = contract.model_json_schema()["properties"]
        for name in ("from_handle", "to_handle"):
            assert properties[name]["enum"] == legal, name
            # A free-length string is exactly what let the model invent one.
            assert "maxLength" not in properties[name]

    guide = ClusterGuideWireContract(handles=handles).model_json_schema()
    array_branch = next(
        option
        for option in guide["properties"]["entry_points"]["anyOf"]
        if option.get("type") == "array"
    )
    assert array_branch["items"]["enum"] == legal

    # The minimal guide carries no handle field, so there is nothing to bind
    # and nothing to invent — which is why it never failed.
    assert "entry_points" not in ClusterGuideMinimalWireContract(
        handles=handles
    ).model_json_schema()["properties"]

    # With no handles bound, an empty enum would be unsatisfiable, so the
    # field is left alone and the endpoint exclusion admits only the index.
    unbound = ScratchLinkWireContract(handles={}).model_json_schema()
    assert "enum" not in unbound["properties"]["from_handle"]

    # The schema now says exactly what the compiler enforces.
    contract = ScratchLinkWireContract(handles=handles)
    with pytest.raises(Exception):
        contract.parse_compile(
            '{"from_handle": "SCR_999", "to_handle": "SCR_001", '
            '"relation_hint": "r"}'
        )


def test_a_self_link_is_dropped_rather_than_killing_the_whole_turn():
    """Regression (turmite run-bc3e8797b3e0609eddb324299c8257bd): a proposal
    declared exactly ONE new block, so no legal `to_ref` existed — every target
    is either that same block (a self-link) or a key the response never
    declares. `_not_a_self_link` raised from inside the nested link model, which
    rejects the entire conjecture turn, candidates and all.

    The model then oscillated between the two invalid values across four repair
    attempts — `to_ref` "NEW_001" (self-link), then an out-of-namespace handle,
    then back — because each diagnostic names only the violation of the state
    it is in, and nothing ever said the field was unsatisfiable and the link
    should simply be removed. The route seat exhausted its smallest authorized
    contract and the run died at cycle 0, discarding a correct refutation it
    had already written.

    A self-link is inert: it adds no edge between distinct blocks, so dropping
    it cannot change what the scratch graph says.
    """

    import pytest

    from deepreason.scratch.proposals import ScratchProposalLinkV1, ScratchProposalV1

    first = {"local_key": "NEW_001", "body": {"content": "a mechanism"}}
    second = {"local_key": "NEW_002", "body": {"content": "another"}}

    # The exact shape that killed the run: one block, one self-link.
    proposal = ScratchProposalV1.model_validate(
        {
            "new_blocks": (first,),
            "links": (
                {
                    "from_ref": "NEW_001",
                    "to_ref": "NEW_001",
                    "relation_hint": "self-consistency check for spiral prediction",
                },
            ),
        }
    )
    assert proposal.links == ()
    assert len(proposal.new_blocks) == 1, "the block must survive the dropped link"

    # A link between distinct blocks is untouched.
    kept = ScratchProposalV1.model_validate(
        {
            "new_blocks": (first, second),
            "links": (
                {"from_ref": "NEW_001", "to_ref": "NEW_002", "relation_hint": "revision"},
            ),
        }
    )
    assert [(l.from_ref, l.to_ref) for l in kept.links] == [("NEW_001", "NEW_002")]

    # Mixed: the self-link goes, the real one stays, and order is preserved.
    mixed = ScratchProposalV1.model_validate(
        {
            "new_blocks": (first, second),
            "links": (
                {"from_ref": "NEW_001", "to_ref": "NEW_001", "relation_hint": "x"},
                {"from_ref": "NEW_001", "to_ref": "NEW_002", "relation_hint": "y"},
            ),
        }
    )
    assert [(l.from_ref, l.to_ref) for l in mixed.links] == [("NEW_001", "NEW_002")]

    # The judgement still exists on the link; only the DISPOSAL moved. It
    # cannot be a raise there: a nested raise aborts the whole model, which is
    # exactly the behaviour being removed.
    assert ScratchProposalLinkV1(
        from_ref="NEW_001", to_ref="NEW_001", relation_hint="x"
    ).is_self_link
    assert not ScratchProposalLinkV1(
        from_ref="NEW_001", to_ref="NEW_002", relation_hint="x"
    ).is_self_link

    # A self-link naming an UNDECLARED key is dropped before the namespace
    # check, so ordering cannot turn the drop into a smuggling route: the link
    # is gone, and it contributes no reference either way.
    stray = ScratchProposalV1.model_validate(
        {
            "new_blocks": (first,),
            "links": (
                {"from_ref": "NEW_009", "to_ref": "NEW_009", "relation_hint": "x"},
            ),
        }
    )
    assert stray.links == ()

    # And the closed-namespace rule still refuses an undeclared target: this
    # change must not become a way to smuggle unknown keys past admission.
    with pytest.raises(Exception):
        ScratchProposalV1.model_validate(
            {
                "new_blocks": (first,),
                "links": (
                    {"from_ref": "NEW_001", "to_ref": "NEW_009", "relation_hint": "x"},
                ),
            }
        )
