"""Advisory provenance on a scratch block: where it came from, what it aims at.

A scratch block is where work sits before anyone -- the model included -- can
know whether it will ever be strong enough to enter the epistemic loop.  Two
optional channels record that: `experiment_refs` names the simulation the note
came out of, `bears_on_refs` names the visible artifact the note was aimed at.
Both are RELEVANCE hypotheses.  Neither grounds anything, and an aim that turns
out to be wrong is still an admissible record of what was attempted.

Two properties these tests exist to hold:

* omitting them must leave every already-stored block byte-identical, because
  block identity is the canonical body and the record is append-only; and
* every rule the validator enforces must be visible in the rendered schema,
  since with reasoning disabled the schema is the model's only structural
  truth (operator rule A2).
"""

from __future__ import annotations

import json

import pytest
from pydantic import ValidationError

from deepreason.capabilities.models import SimulationProposalDraftV1
from deepreason.scratch.attention import AttentionPlanner
from deepreason.scratch.contracts import ScratchBlockWireContract, ScratchBlockWireV1
from deepreason.scratch.models import (
    MAX_PROVENANCE_REFS,
    ScratchBlockBodyV1,
    ScratchBlockV1,
)
from deepreason.scratch.proposals import (
    ScratchBlockDraftBodyV1,
    ScratchNewBlockDraftV1,
    ScratchProposalV1,
)
from deepreason.scratch.render import ScratchRenderer
from deepreason.scratch.service import ScratchService
from tests.test_scratch_attention import _policy, _request, _user


#: Computed on the commit before the two ref fields existed, for
#: `ScratchBlockBodyV1(content="a provisional mechanism")`.  It is pinned as a
#: literal rather than recomputed because recomputation would agree with any
#: change at all -- the point is agreement with history.
_PRE_PROVENANCE_BODY_HASH = (
    "sha256:ff609dcc91dfd6894e752fe9a1e8b1d3fb91fe175dcd7ec1fd45c8d8e0796f8e"
)


def test_a_block_omitting_the_refs_hashes_as_it_did_before_they_existed():
    """The defaults are None, not (), and that is the whole reason this holds.

    `_canonical_value` dumps with `exclude_none=True`, which drops None and
    KEEPS an empty tuple.  Defaulting these fields to () therefore put two more
    keys into every block's canonical bytes and moved every stored block's id
    (measured: ff609dcc -> 248b3201 for identical content), which would have
    invalidated replay validation for every root already in the record.
    """

    body = ScratchBlockBodyV1(content="a provisional mechanism")

    assert body.experiment_refs is None
    assert body.bears_on_refs is None
    assert body.model_dump(mode="json", by_alias=True, exclude_none=True) == {
        "content": "a provisional mechanism"
    }
    assert ScratchBlockV1.compute_body_hash(body) == _PRE_PROVENANCE_BODY_HASH


def test_naming_provenance_changes_the_block_because_it_is_part_of_the_note():
    """Not a metadata sidecar: what a note was aimed at is part of the note."""

    plain = ScratchBlockBodyV1(content="a provisional mechanism")
    aimed = ScratchBlockBodyV1(
        content="a provisional mechanism",
        experiment_refs=("sim.jolt.1",),
        bears_on_refs=("SRC_004",),
    )

    assert ScratchBlockV1.compute_body_hash(aimed) != ScratchBlockV1.compute_body_hash(
        plain
    )


def test_the_standalone_block_seat_offers_no_provenance_at_all():
    """Measured, not judged: offering it there took `scratch.block.compact.v1`
    from 20/20 to 2/20 on glm-5.2 thinking-off.

    Two independent faults, both from putting these fields on this seat. The
    hard one: the contract validates through `model_validate` on a parsed dict,
    which is strict, so a JSON array could not become a `tuple` field and
    18 of 20 cases died `VALIDATION_ERROR` after two repairs each. The soft one:
    this seat sees only `SCR_###` handles, so in 3 of 3 reproduction calls the
    model filled `bears_on_refs` with `["SRC_001", "SRC_002"]` transliterated
    from `SCR_001`/`SCR_002` — naming scratch blocks as artifacts.

    Provenance lives on the conjecture-turn draft instead, where `SRC_###`
    aliases actually exist.
    """

    assert "experiment_refs" not in ScratchBlockWireV1.model_fields
    assert "bears_on_refs" not in ScratchBlockWireV1.model_fields
    assert "bears_on_refs" in ScratchBlockDraftBodyV1.model_fields


def test_a_json_document_survives_the_live_admission_path():
    """The gap that let the 2/20 ship. Every earlier test built models in
    Python with tuples; nothing pushed a JSON DOCUMENT through the contract,
    which is the only path a provider response ever takes.
    """

    contract = ScratchBlockWireContract()
    document = json.dumps(
        {
            "content": "entropy fell under the anti-anchor prompt, not seeds",
            "why_keep_this": "it separates the two explanations",
            "unfinished": "no account of why the prompt does it",
            "possible_next_move": "vary the anchor and re-measure",
        }
    )

    body = contract.compile(contract.validate_json(document))

    assert body.content.startswith("entropy fell")
    assert body.experiment_refs is None and body.bears_on_refs is None


def test_a_conjecture_turn_may_admit_a_draft_that_names_what_it_aims_at():
    """The main-loop path, not just the standalone authoring seat."""

    proposal = ScratchProposalV1(
        new_blocks=(
            ScratchNewBlockDraftV1(
                local_key="NEW_001",
                body=ScratchBlockDraftBodyV1(
                    content="the jolt may be prompt-shaped, not sampler-shaped",
                    experiment_refs=("sim.jolt.1",),
                    bears_on_refs=("SRC_004", "SRC_007"),
                ),
            ),
        )
    )

    draft = proposal.new_blocks[0].body
    assert ScratchBlockBodyV1.model_validate(
        draft.model_dump(mode="python")
    ).bears_on_refs == ("SRC_004", "SRC_007")


def test_the_refs_are_rendered_back_as_history_and_not_as_live_pointers(tmp_path):
    """Otherwise the channel is write-only, and worse than useless if read.

    A source alias is minted per call by enumeration, so SRC_004 in a block
    written three cycles ago names a different artifact now. The keys are
    past-tense so the model reads the aim as a record rather than resolving it
    against the aliases in front of it. Blocks with no refs render exactly as
    they did before the fields existed.
    """

    service = ScratchService(tmp_path / "run")
    aimed = service.create_block(
        {
            "content": "the jolt may be prompt-shaped",
            "experiment_refs": ["jolt: baseline vs schools"],
            "bears_on_refs": ["SRC_004"],
        },
        _user(),
    )
    plain = service.create_block({"content": "no provenance"}, _user())
    pack = AttentionPlanner(service, _policy(coverage_enabled=False)).plan(
        _request([aimed.id, plain.id], maximum_blocks=2)
    )

    payload = json.loads(
        ScratchRenderer(service).render_attention_pack(pack).text.split("\n", 1)[1]
    )
    first, second = payload["blocks"]

    assert first["came_from_experiments"] == ["jolt: baseline vs schools"]
    assert first["was_aimed_at"] == ["SRC_004"]
    assert set(second) == {"handle", "content"}


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("bears_on_refs", ("SRC_0004",)),
        ("bears_on_refs", ("SCR_004",)),
        ("bears_on_refs", ("B4",)),
        ("experiment_refs", ("",)),
        ("experiment_refs", ("x" * 129,)),
    ],
)
def test_a_ref_outside_its_namespace_is_refused(field, value):
    for model in (ScratchBlockDraftBodyV1, ScratchBlockBodyV1):
        with pytest.raises(ValidationError):
            model(content="a note", **{field: value})


def test_an_experiment_ref_is_bounded_exactly_as_the_field_it_names():
    """No tighter, and this is the point of the test.

    `request_identifier` is model-chosen free text. A namespace regex on this
    side would refuse references to experiments the simulation contract itself
    accepted -- a contract mismatch introduced from the reading end, which is
    the same defect as a prose-only rule and just as invisible.
    """

    named = SimulationProposalDraftV1.model_json_schema()["properties"][
        "request_identifier"
    ]
    naming = ScratchBlockDraftBodyV1.model_json_schema()["properties"][
        "experiment_refs"
    ]
    item = next(
        branch for branch in naming["anyOf"] if branch.get("type") == "array"
    )["items"]

    assert (item["minLength"], item["maxLength"]) == (
        named["minLength"],
        named["maxLength"],
    )

    # Concretely: a request identifier the simulation contract accepts must
    # remain nameable from a scratch block.
    awkward = "jolt: baseline vs schools (run 2)"
    assert SimulationProposalDraftV1.model_fields["request_identifier"]
    assert ScratchBlockDraftBodyV1(
        content="a note", experiment_refs=(awkward,)
    ).experiment_refs == (awkward,)


@pytest.mark.parametrize("field", ["experiment_refs", "bears_on_refs"])
def test_the_channels_are_bounded_and_duplicate_free(field):
    prefix = "SRC_00" if field == "bears_on_refs" else "sim.e"
    legal = tuple(f"{prefix}{index}" for index in range(MAX_PROVENANCE_REFS))

    for model in (ScratchBlockDraftBodyV1, ScratchBlockBodyV1):
        assert model(content="a note", **{field: legal})

        with pytest.raises(ValidationError):
            model(content="a note", **{field: legal + (f"{prefix}9",)})
        with pytest.raises(ValidationError, match="duplicates"):
            model(content="a note", **{field: (legal[0], legal[0])})


@pytest.mark.parametrize("field", ["experiment_refs", "bears_on_refs"])
def test_every_rule_the_validator_enforces_is_visible_in_the_schema(field):
    """Rule A2: a constraint the model can only learn by being refused is a
    defect in the contract, not a failure of the model.
    """

    for model in (ScratchBlockDraftBodyV1,):
        rendered = model.model_json_schema()["properties"][field]
        # Nullable, so the array rules live in the array branch of the anyOf;
        # `uniqueItems` is inert against a null instance and stays at the top.
        array_branch = next(
            branch for branch in rendered["anyOf"] if branch.get("type") == "array"
        )
        assert array_branch["maxItems"] == MAX_PROVENANCE_REFS
        assert rendered["uniqueItems"] is True
        assert field not in model.model_json_schema().get("required", [])

        item = array_branch["items"]
        if field == "bears_on_refs":
            assert item["pattern"] == r"^SRC_[0-9]{3}$"
        else:
            assert (item["minLength"], item["maxLength"]) == (1, 128)
            assert "pattern" not in item, (
                "an experiment ref must not carry a namespace the simulation "
                "contract does not itself impose"
            )
