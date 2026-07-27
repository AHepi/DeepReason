"""V6 capability-specialized schemas and patch-only repair regressions."""

from __future__ import annotations

import json
from typing import Literal

import pytest
from pydantic import BaseModel, ConfigDict, Field, ValidationError, model_validator

from deepreason.conjecture_turn import ConjectureTurnV6
from deepreason.llm.repair import (
    RepairPatchV1,
    RepairScopeViolation,
    SchemaExhaustedError,
    UnrepairableDiagnosticError,
    V6PatchRepairSession,
    apply_repair_patch,
    diagnostic_envelope_from_error,
    repair_patch_response_schema,
)
from deepreason.llm.wire import (
    AliasTable,
    BatchCriticWireContractV2,
    ConjecturerTurnWireContractV6,
    V6WireReferenceError,
)
from deepreason.scratch.proposals import V6_SCRATCH_WORKSHOP_SCHEMA_DESCRIPTION
from deepreason.run_manifest import ScratchAuthoringPolicyV1


class _ArchivedFailureShape(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)

    claim: str = Field(min_length=1)
    typicality: float = Field(ge=0.0, le=1.0)
    mode: Literal["safe"]


class _RootCheckedShape(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)

    left: int
    right: int

    @model_validator(mode="after")
    def _values_match(self):
        if self.left != self.right:
            raise ValueError("values must match")
        return self


def _validation_error(model, value):
    with pytest.raises(ValidationError) as raised:
        model.model_validate(value)
    return raised.value


def _simulation_proposal(*, inputs=()):
    return {
        "request_identifier": "bounded-test",
        "hypothesis": "A finite test separates the live rivals.",
        "rival_predictions": ["x is low", "x is high"],
        "discriminating_purpose": "Separate the two declared predictions.",
        "declared_assumptions": ["Inputs are sealed."],
        **({"input_aliases": list(inputs)} if inputs is not None else {}),
        "parameter_definitions": [
            {"name": "one", "values_json": '{"weight":1}'}
        ],
        "requested_seed_set": [7],
        "simulation_mode": "declarative_numeric_v1",
        "model_source": json.dumps(
            {
                "schema": "declarative-numeric.v1",
                "observables": {"x": {"const": 1}},
            }
        ),
        "requested_observables": ["x"],
        "interpretation_conditions": ["x=1 favors the first rival."],
    }


def test_repair_patch_is_one_non_root_operation_with_exact_value_presence():
    assert RepairPatchV1(op="remove", path="/extra").model_dump(
        mode="json", by_alias=True, exclude_unset=True
    ) == {"op": "remove", "path": "/extra"}
    assert RepairPatchV1(op="replace", path="/value", value=None).value is None
    with pytest.raises(ValueError, match="requires value"):
        RepairPatchV1(op="add", path="/missing")
    with pytest.raises(ValueError, match="must omit value"):
        RepairPatchV1(op="remove", path="/extra", value=None)
    with pytest.raises(ValueError, match="parseable root"):
        RepairPatchV1(op="replace", path="", value={})


def test_diagnostic_envelope_authorizes_each_field_and_freezes_valid_claim():
    baseline = {
        "claim": "preserve this exact claim",
        "typicality": 2.0,
        "mode": "unsafe",
        "extra": "remove me",
    }
    error = _validation_error(_ArchivedFailureShape, baseline)
    envelope = diagnostic_envelope_from_error(
        contract="archived.failure.v1",
        error=error,
        schema=_ArchivedFailureShape.model_json_schema(),
        baseline=baseline,
    )

    assert envelope.schema_ == "repair.diagnostic-envelope.v2"
    assert envelope.authorized_pointers == (
        "/extra",
        "/mode",
        "/typicality",
    )
    assert {item.path for item in envelope.frozen_subtree_hashes} == {"/claim"}
    patch_schema = repair_patch_response_schema(envelope)
    branches = {item["properties"]["op"]["const"]: item for item in patch_schema["oneOf"]}
    assert "value" not in branches["remove"]["properties"]
    assert "value" in branches["add"]["required"]
    assert "value" in branches["replace"]["required"]

    repaired = apply_repair_patch(
        baseline,
        RepairPatchV1(op="replace", path="/typicality", value=0.4),
        envelope,
    )
    assert repaired["claim"] == baseline["claim"]
    assert repaired["typicality"] == 0.4
    with pytest.raises(RepairScopeViolation):
        apply_repair_patch(
            baseline,
            RepairPatchV1(op="replace", path="/claim", value="laundered"),
            envelope,
        )


def test_patch_envelope_rejects_stale_baseline_and_wrong_patch_operation():
    baseline = {"claim": "fixed", "typicality": 2.0, "mode": "safe"}
    envelope = diagnostic_envelope_from_error(
        contract="archived.failure.v1",
        error=_validation_error(_ArchivedFailureShape, baseline),
        schema=_ArchivedFailureShape.model_json_schema(),
        baseline=baseline,
    )
    with pytest.raises(RepairScopeViolation):
        apply_repair_patch(
            {**baseline, "claim": "changed before repair"},
            RepairPatchV1(op="replace", path="/typicality", value=0.5),
            envelope,
        )
    with pytest.raises(ValueError, match="already exists"):
        apply_repair_patch(
            baseline,
            RepairPatchV1(op="add", path="/typicality", value=0.5),
            envelope,
        )


def test_missing_field_uses_add_and_extra_field_uses_remove():
    missing = {"claim": "fixed", "typicality": 0.5}
    missing_envelope = diagnostic_envelope_from_error(
        contract="archived.failure.v1",
        error=_validation_error(_ArchivedFailureShape, missing),
        schema=_ArchivedFailureShape.model_json_schema(),
        baseline=missing,
    )
    assert missing_envelope.authorized_pointers == ("/mode",)
    added = apply_repair_patch(
        missing,
        RepairPatchV1(op="add", path="/mode", value="safe"),
        missing_envelope,
    )
    assert _ArchivedFailureShape.model_validate(added).mode == "safe"

    extra = {**added, "unexpected": "remove only this"}
    extra_envelope = diagnostic_envelope_from_error(
        contract="archived.failure.v1",
        error=_validation_error(_ArchivedFailureShape, extra),
        schema=_ArchivedFailureShape.model_json_schema(),
        baseline=extra,
    )
    removed = apply_repair_patch(
        extra,
        RepairPatchV1(op="remove", path="/unexpected"),
        extra_envelope,
    )
    assert _ArchivedFailureShape.model_validate(removed).claim == "fixed"


def test_parseable_v6_session_applies_two_independent_patches_sequentially():
    session = V6PatchRepairSession(
        contract="archived.failure.v1",
        schema=_ArchivedFailureShape.model_json_schema(),
        initial_request="PACK",
        retry_max=2,
    )
    initial = session.turn(0)
    candidate = session.candidate_from_raw(
        initial,
        '{"claim":"keep","typicality":2.0,"mode":"unsafe"}',
    )
    session.note_invalid(
        initial,
        json.dumps(candidate),
        _validation_error(_ArchivedFailureShape, candidate),
    )

    first = session.turn(1)
    assert first.mode == "patch"
    assert "Do not return the surrounding object" in first.request
    assert set(first.authorized_pointers) == {"/mode", "/typicality"}
    candidate = session.candidate_from_raw(
        first,
        '{"schema":"repair.patch.v1","op":"replace",'
        '"path":"/typicality","value":0.5}',
    )
    session.note_invalid(
        first,
        "patch",
        _validation_error(_ArchivedFailureShape, candidate),
    )

    second = session.turn(2)
    assert second.mode == "patch"
    assert second.authorized_pointers == ("/mode",)
    final = session.candidate_from_raw(
        second,
        '{"schema":"repair.patch.v1","op":"replace",'
        '"path":"/mode","value":"safe"}',
    )
    assert _ArchivedFailureShape.model_validate(final).claim == "keep"
    assert final == {"claim": "keep", "typicality": 0.5, "mode": "safe"}


def test_unparseable_v6_session_allows_exactly_one_whole_object_retry():
    session = V6PatchRepairSession(
        contract="archived.failure.v1",
        schema=_ArchivedFailureShape.model_json_schema(),
        initial_request="PACK",
        retry_max=2,
    )
    initial = session.turn(0)
    with pytest.raises(ValueError) as first_error:
        session.candidate_from_raw(initial, "{broken")
    session.note_invalid(initial, "{broken", first_error.value)
    syntax_retry = session.turn(1)
    assert syntax_retry.mode == "whole_object_syntax"

    with pytest.raises(ValueError) as second_error:
        session.candidate_from_raw(syntax_retry, "{still-broken")
    session.note_invalid(syntax_retry, "{still-broken", second_error.value)
    with pytest.raises(SchemaExhaustedError) as exhausted:
        session.turn(2)
    assert exhausted.value.code == "schema_exhausted"
    assert session.exhaustion_error().code == "schema_exhausted"


def test_syntax_retry_can_transition_to_one_final_local_patch():
    session = V6PatchRepairSession(
        contract="archived.failure.v1",
        schema=_ArchivedFailureShape.model_json_schema(),
        initial_request="PACK",
        retry_max=2,
    )
    initial = session.turn(0)
    with pytest.raises(ValueError) as syntax_error:
        session.candidate_from_raw(initial, "{broken")
    session.note_invalid(initial, "{broken", syntax_error.value)

    syntax_retry = session.turn(1)
    candidate = session.candidate_from_raw(
        syntax_retry,
        '{"claim":"keep","typicality":2.0,"mode":"safe"}',
    )
    session.note_invalid(
        syntax_retry,
        json.dumps(candidate),
        _validation_error(_ArchivedFailureShape, candidate),
    )
    patch_turn = session.turn(2)
    assert patch_turn.mode == "patch"
    final = session.candidate_from_raw(
        patch_turn,
        '{"schema":"repair.patch.v1","op":"replace",'
        '"path":"/typicality","value":0.5}',
    )
    assert _ArchivedFailureShape.model_validate(final).claim == "keep"


def test_root_validator_requires_explicit_finite_patch_pointers():
    baseline = {"left": 1, "right": 2}
    error = _validation_error(_RootCheckedShape, baseline)
    with pytest.raises(UnrepairableDiagnosticError, match="explicit"):
        diagnostic_envelope_from_error(
            contract="root.checked.v1",
            error=error,
            schema=_RootCheckedShape.model_json_schema(),
            baseline=baseline,
        )

    envelope = diagnostic_envelope_from_error(
        contract="root.checked.v1",
        error=error,
        schema=_RootCheckedShape.model_json_schema(),
        baseline=baseline,
        root_authorized_pointers=("/right",),
    )
    repaired = apply_repair_patch(
        baseline,
        RepairPatchV1(op="replace", path="/right", value=1),
        envelope,
    )
    assert _RootCheckedShape.model_validate(repaired).left == repaired["right"]


def test_v6_disabled_capabilities_are_absent_not_empty_in_wire_schema():
    contract = ConjecturerTurnWireContractV6(
        reasoning=False,
        aliases=AliasTable(),
        simulation_enabled=False,
    )
    schema = contract.model_json_schema()
    assert "simulation_proposals" not in schema["properties"]
    assert "scratch_proposal" not in schema["properties"]
    assert V6_SCRATCH_WORKSHOP_SCHEMA_DESCRIPTION not in json.dumps(
        schema, sort_keys=True
    )
    candidate = schema["$defs"]["CompactConjectureCandidate"]
    assert "neighbours" not in candidate["properties"]
    assert contract.parse_compile(
        '{"abstention":{"search_signal":"stuck"}}'
    ).abstention is not None
    with pytest.raises(V6WireReferenceError, match="disabled"):
        contract.parse_compile('{"simulation_proposals":[]}')
    with pytest.raises(V6WireReferenceError, match="scratch authoring is disabled"):
        contract.parse_compile('{"scratch_proposal":{}}')


def test_v6_scratch_schema_uses_exact_manifest_ceilings_and_allows_coexistence():
    policy = ScratchAuthoringPolicyV1(
        enabled=True,
        maximum_new_blocks_per_turn=1,
        maximum_revisions_per_turn=2,
        maximum_links_per_turn=3,
        maximum_unresolved_questions_per_turn=4,
        maximum_cluster_suggestions_per_turn=5,
        maximum_total_bytes=1_000_000,
    )
    contract = ConjecturerTurnWireContractV6(
        reasoning=False,
        aliases=AliasTable(),
        scratch_authoring_policy=policy,
    )
    schema = contract.model_json_schema()
    assert "scratch_proposal" in schema["properties"]
    assert schema["properties"]["scratch_proposal"]["description"] == (
        V6_SCRATCH_WORKSHOP_SCHEMA_DESCRIPTION
    )

    scratch = schema["$defs"]["ScratchProposalV1"]["properties"]
    assert {
        name: scratch[name]["maxItems"]
        for name in (
            "new_blocks",
            "revisions",
            "links",
            "unresolved_questions",
            "cluster_suggestions",
        )
    } == {
        "new_blocks": 1,
        "revisions": 2,
        "links": 3,
        "unresolved_questions": 4,
        "cluster_suggestions": 5,
    }

    turn = contract.parse_compile(
        json.dumps(
            {
                "candidates": [
                    {"content": "A formal proposal remains separate.", "typicality": 0.3}
                ],
                "scratch_proposal": {
                    "new_blocks": [
                        {
                            "local_key": "NEW_001",
                            "body": {"content": "An advisory unfinished thought."},
                        }
                    ],
                    "unresolved_questions": [
                        {
                            "question": "Would the countercondition reverse it?",
                            "related_refs": ["NEW_001"],
                        }
                    ],
                },
            }
        )
    )
    assert len(turn.candidates) == 1
    assert turn.scratch_proposal.new_blocks[0].local_key == "NEW_001"

    too_many = {
        "scratch_proposal": {
            "new_blocks": [
                {"local_key": "NEW_001", "body": {"content": "one"}},
                {"local_key": "NEW_002", "body": {"content": "two"}},
            ]
        }
    }
    with pytest.raises(V6WireReferenceError, match="new_blocks exceeds"):
        contract.parse_compile(json.dumps(too_many))


def test_v6_schema_binds_exact_limits_and_disjoint_literal_catalogs():
    contract = ConjecturerTurnWireContractV6(
        reasoning=False,
        aliases=AliasTable({"SRC_001": "artifact-one"}),
        scratch_aliases={"SCR_001": "scratch-one"},
        simulation_enabled=True,
        maximum_simulation_proposals=2,
        simulation_input_aliases={"SIM_001": "sealed-input-one"},
    )
    schema = contract.model_json_schema()
    assert schema["properties"]["simulation_proposals"]["maxItems"] == 2
    assert schema["$defs"]["SimulationProposalWireV1"]["properties"][
        "input_aliases"
    ]["items"]["enum"] == ["SIM_001"]
    assert schema["$defs"]["CompactConjectureCandidate"]["properties"][
        "neighbours"
    ]["items"]["enum"] == ["SRC_001"]
    assert schema["$defs"]["ContextRequestWireV2"]["properties"][
        "requested_visible_aliases"
    ]["items"]["enum"] == ["SCR_001", "SRC_001"]

    turn = contract.parse_compile(
        json.dumps(
            {"simulation_proposals": [_simulation_proposal(inputs=("SIM_001",))]}
        )
    )
    assert isinstance(turn, ConjectureTurnV6)
    assert turn.simulation_proposals[0].input_aliases == ("SIM_001",)

    bad = {"simulation_proposals": [_simulation_proposal(inputs=("SRC_001",))]}
    with pytest.raises(V6WireReferenceError) as raised:
        contract.parse_compile(json.dumps(bad))
    assert raised.value.pointer.endswith("/input_aliases/0")


def test_v6_omits_simulation_inputs_when_catalog_is_empty_and_enforces_cap():
    contract = ConjecturerTurnWireContractV6(
        reasoning=False,
        aliases=AliasTable(),
        simulation_enabled=True,
        maximum_simulation_proposals=1,
    )
    simulation = contract.model_json_schema()["$defs"]["SimulationProposalWireV1"]
    assert "input_aliases" not in simulation["properties"]
    with pytest.raises(V6WireReferenceError, match="no simulation inputs"):
        contract.parse_compile(
            json.dumps(
                {
                    "simulation_proposals": [
                        _simulation_proposal(inputs=()),
                    ]
                }
            )
        )
    with pytest.raises(V6WireReferenceError, match="count exceeds"):
        contract.parse_compile(
            json.dumps(
                {
                    "simulation_proposals": [
                        _simulation_proposal(inputs=None),
                        _simulation_proposal(inputs=None),
                    ]
                }
            )
        )


@pytest.mark.parametrize(
    ("kwargs", "message"),
    [
        ({"aliases": AliasTable({"A1": "artifact"})}, "SRC_###"),
        (
            {
                "aliases": AliasTable(),
                "scratch_aliases": {"S1": "scratch"},
            },
            "SCR_###",
        ),
        (
            {
                "aliases": AliasTable(),
                "simulation_input_aliases": ("INPUT_1",),
            },
            "SIM_###",
        ),
    ],
)
def test_v6_rejects_legacy_or_cross_kind_alias_names(kwargs, message):
    with pytest.raises(ValueError, match=message):
        ConjecturerTurnWireContractV6(
            reasoning=False,
            simulation_enabled=False,
            **kwargs,
        )


def test_batch_critic_v2_binds_only_assigned_src_targets():
    contract = BatchCriticWireContractV2(
        AliasTable(
            {
                "SRC_001": "artifact-one",
                "SRC_002": "artifact-two",
            }
        ),
        expected_targets=("artifact-two",),
    )
    schema = contract.model_json_schema()
    assert schema["properties"]["cases"]["maxItems"] == 1
    case_schema = schema["$defs"]["BatchCriticCaseWireV2"]
    assert case_schema["properties"]["target_alias"]["enum"] == ["SRC_002"]
    output = contract.parse_compile(
        '{"cases":[{"target_alias":"SRC_002","attack":true,"case":"fails"}]}'
    )
    assert output.cases[0].target == "artifact-two"
    with pytest.raises(V6WireReferenceError):
        contract.parse_compile(
            '{"cases":[{"target_alias":"SRC_001","attack":true,"case":"no"}]}'
        )
