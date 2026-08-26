"""The typed discharge on the wire (REBUILD F1, R3), and what it must NOT move.

Two claims, and the second is the one that protects everything else.

1. A candidate can CARRY a discharge: `DischargeWireV1` with a handle, a kind,
   and the content that kind requires. The `kind` enum in the EMITTED schema is
   derived from `DISCHARGE_KIND_DECLARATIONS`, so declaring a fourth kind
   reaches the model without this file being edited (R12).
2. With the channel OFF the field is PRUNED from every contract that embeds
   the two candidate models -- not merely unused, ABSENT -- so a channel-off
   run's schema bytes are what they were before this tranche existed. Three
   committed tests read `$defs["CompactConjectureCandidate"]["properties"]`
   directly (`test_v6_patch_repair_and_wire.py:330,432`,
   `test_wire_contracts.py:58`), which is what turns pruning from an
   optimisation into a requirement.

And the measurement the frozen-surface grant rests on: the qualification
subject embeds `contract_id` STRINGS, never a wire schema, so these additions
leave the subject digest at `b9038b84efdea313...` (SPEC.md M4).
"""

import json

import pytest

from deepreason.discharge import DISCHARGE_KIND_DECLARATIONS, DischargeKindDeclaration
from deepreason.llm.wire import (
    AliasTable,
    AtomicConjectureWireContractV1,
    CompactConjectureCandidate,
    ConjecturerWireContract,
    DischargeWireV1,
    discharge_kind_enum,
)
from deepreason.workloads.text import ReasoningCandidateProposal

CANDIDATE_DEFS = ("CompactConjectureCandidate", "ReasoningCandidateProposal")


def _defs(schema: dict) -> dict:
    return schema.get("$defs", {})


def _properties(schema: dict, name: str) -> dict:
    return _defs(schema).get(name, {}).get("properties", {})


# --- 1: a candidate can carry a discharge --------------------------------- #


def test_a_discharge_carries_a_handle_a_kind_and_its_content():
    """R3. The three things a discharge is, and nothing else."""
    discharge = DischargeWireV1(
        handle="a" * 64,
        kind="revised",
        note="added the solar term to the range calculation",
        where="paragraph 2, the spring-neap formula",
    )
    assert discharge.handle == "a" * 64
    assert discharge.kind == "revised"
    # Strict and closed like every wire model here: a model cannot smuggle a
    # field past the contract by inventing one.
    with pytest.raises(Exception):
        DischargeWireV1(handle="x", kind="revised", note="n", verdict="accepted")


def test_both_candidate_models_accept_discharges():
    """R3. "a new candidate ... must carry, per criticism handle, a typed
    discharge" -- the obligation is on the CANDIDATE, so the field is on both
    candidate models rather than on the turn. `CompactConjectureCandidate` is
    reused by the v4/v5/v6 turns AND the atomic contract, and
    `ReasoningCandidateProposal` by the three reasoning twins, so these two
    fields are the whole surface.
    """
    compact = CompactConjectureCandidate(
        content="the tide is lunar plus solar",
        typicality=0.4,
        discharges=[DischargeWireV1(handle="h", kind="revised", note="n", where="w")],
    )
    assert compact.discharges[0].kind == "revised"

    reasoning = ReasoningCandidateProposal(
        claim="the tide is lunar plus solar",
        mechanism="the two forcings add in quadrature at the harbour",
        counterconditions=("the harbour is not shallow",),
        typicality=0.4,
        discharges=(DischargeWireV1(handle="h", kind="rebutted", note="n"),),
    )
    assert reasoning.discharges[0].kind == "rebutted"


def test_a_candidate_without_discharges_is_still_valid():
    """R4's other half, at the schema layer: an undischarged submission is not
    a schema error. It is returned once and then ACCEPTED with a disclosure --
    disclose, never die. A required field here would make the wire enforce a
    gate the design forbids, and no re-ask could ever be attempted because the
    reply would not parse.
    """
    assert CompactConjectureCandidate(content="c", typicality=0.1).discharges == []


def test_the_kind_enum_is_derived_from_the_registry(monkeypatch):
    """R12. A fourth kind reaches the MODEL by declaration.

    The strongest form of the modularity claim, because the model can only act
    on what the schema offers it: if the enum were a literal here, a declared
    kind would be legal in Python and invisible on the wire, which is worse
    than not declaring it.
    """
    assert set(discharge_kind_enum()) == set(DISCHARGE_KIND_DECLARATIONS)

    monkeypatch.setitem(
        DISCHARGE_KIND_DECLARATIONS,
        "scoped_out",
        DischargeKindDeclaration(
            name="scoped_out",
            asserts="the criticism is outside the problem as posed",
            requires=("note",),
            directive_line="scoped_out -- say which part of the problem excludes it",
        ),
    )
    assert "scoped_out" in discharge_kind_enum()

    contract = ConjecturerWireContract(discharge_enabled=True)
    kind = _properties(contract.model_json_schema(), "DischargeWireV1").get("kind", {})
    assert "scoped_out" in kind.get("enum", []), kind


# --- 2: with the channel OFF the field is ABSENT --------------------------- #


@pytest.mark.parametrize(
    "build",
    [
        pytest.param(lambda: ConjecturerWireContract(), id="compact-conjecturer"),
        pytest.param(
            lambda: AtomicConjectureWireContractV1(AliasTable(), reasoning=False),
            id="atomic-compact",
        ),
        pytest.param(
            lambda: AtomicConjectureWireContractV1(AliasTable(), reasoning=True),
            id="atomic-reasoning",
        ),
    ],
)
def test_the_field_is_pruned_when_the_channel_is_off(build):
    """R10's schema half, and the reason pruning is a requirement.

    `CompactConjectureCandidate` is embedded by contracts this tranche has no
    business changing. A field added and not pruned would grow their schemas,
    and three committed tests read that `$def`'s properties directly.
    """
    schema = build().model_json_schema()
    for name in CANDIDATE_DEFS:
        assert "discharges" not in _properties(schema, name), name
    assert "DischargeWireV1" not in _defs(schema)


def test_the_field_is_present_when_the_channel_is_on():
    """The companion that stops the pruning test passing vacuously.

    Without this, a `discharges` field deleted from the models entirely would
    satisfy every absence assertion above.
    """
    schema = ConjecturerWireContract(discharge_enabled=True).model_json_schema()
    assert "discharges" in _properties(schema, "CompactConjectureCandidate")
    assert "DischargeWireV1" in _defs(schema)


def test_the_three_committed_reads_of_the_candidate_def_are_unmoved():
    """The census's own hits, asserted rather than reasoned about.

    `test_v6_patch_repair_and_wire.py` reads `"neighbours" not in ...properties`
    and that property's alias enum; `test_wire_contracts.py` reads
    `additionalProperties is False` on the same `$def`. None enumerates the
    full property set -- which is exactly why a PRUNED field moves none of
    them, and why an unpruned one would.
    """
    schema = ConjecturerWireContract().model_json_schema()
    candidate = _defs(schema)["CompactConjectureCandidate"]
    assert candidate["additionalProperties"] is False
    assert set(candidate["properties"]) == {
        "content",
        "typicality",
        "neighbours",
        "evidence_refs",
    }


def test_the_qualification_subject_digest_does_not_move():
    """SPEC.md M4, re-measured as a committed test rather than a session note.

    The qualification subject embeds `contract_id` STRINGS and the manifest, not
    any wire schema, so a wire field cannot reach it. Surface 5 stays at zero
    for this half of the tranche, and it is checked rather than argued.
    """
    from deepreason.qualification import qualification_subject_digest
    from tests.test_reusable_qualification import _manifest, _profile

    profile = _profile()
    assert qualification_subject_digest(_manifest(profile), profile) == (
        "b9038b84efdea313c3f3f2a8862d8acf180d3938ab3d1bf3588c3585dfe07386"
    )


def test_a_pruned_schema_still_round_trips_a_candidate():
    """Omission and encoding must not disagree.

    `prune_property`'s own docstring names the failure: a surviving constraint
    that still advertises a removed field, under `additionalProperties: false`.
    A schema that forbids what it advertises has no satisfying document.
    """
    contract = ConjecturerWireContract()
    schema = contract.model_json_schema()
    payload = {"candidates": [{"content": "the tide is lunar plus solar", "typicality": 0.4}]}
    json.dumps(schema)                                   # positive anchor: renderable
    assert contract.parse_compile(json.dumps(payload)).candidates[0].typicality == 0.4
