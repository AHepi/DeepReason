"""A criticism declares what it essentially rests on, and the declaration is
registered on its validity node as EVIDENCE.

Regression (tranche experiments/2026-09-05-criticism-premise-declaration,
reproducing the OIS 1.1 §0 finding at 323fefb53): a criticism whose essential
premise had been refuted went on defeating its target -- the pair came back
('refuted', 'suspended_unsupported') where the same graph with the premise
declared as EVIDENCE on the validity node came back ('accepted', 'refuted').
The evidence closure was never at fault; the critic contract had no field in
which a criticism could name its own premises, so the correct branch was
unreachable from the wire.

What is asserted here is the typed record -- statuses, refs on nu, declined
Measures -- never a model's prose.
"""

import json

import pytest

from deepreason.config import Config
from deepreason.llm.adapter import LLMAdapter
from deepreason.llm.contracts import ArgumentativeCriticOutput, BatchCase
from deepreason.llm.endpoints import MockEndpoint
from deepreason.llm.firewall import leases_from_endpoints
from deepreason.llm.wire import AliasTable, CriticWireContract, UnknownAliasError
from deepreason.ontology import (
    Provenance,
    Status,
    Warrant,
    WarrantType,
)
from deepreason.ontology.artifact import RefRole
from deepreason.rules.crit import crit_argumentative

_CASE = "the tilt account cannot explain the observed nocturnal gap"
_DEFENCE = "the tilt account does explain it"
_RULING = json.dumps({"verdict": "fail", "decisive_point": "the observed nocturnal gap"})


def _adapter(harness, critic_payload):
    """critic + defender + two judge seats drawn from two model FAMILIES.

    Two families is the ordinary cross-family ensemble the defended trial
    demands, so the trial reaches its mint site without the cross-school
    substitute -- which keeps this file's subject the premise declaration and
    not the authority ladder.
    """
    endpoints = {
        "argumentative_critic": MockEndpoint(
            [json.dumps(critic_payload)], name="mock://critic", model="qwen-test"
        ),
        "defender": MockEndpoint(
            [json.dumps({"answer": _DEFENCE})], name="mock://defender", model="qwen-test"
        ),
        "judge": [
            MockEndpoint([_RULING], name="mock://judge-a", model="qwen-test"),
            MockEndpoint([_RULING], name="mock://judge-b", model="llama-test"),
        ],
    }
    return LLMAdapter(
        endpoints,
        harness.blobs,
        retry_max=2,
        leases=leases_from_endpoints(endpoints),
    )


def _target_and_premise(harness):
    target = harness.create_artifact(
        "the nocturnal urban-rural gap is set by the sky view factor",
        provenance=Provenance(role="conjecturer"),
    )
    premise = harness.create_artifact(
        "standard k: a surface-energy account must close its budget",
        provenance=Provenance(role="seed"),
    )
    return target, premise


def _refute(harness, victim_id, *, warrant_id):
    """Refute an artifact the way §0 does: a second criticism carrying its own
    argumentative warrant and its own validity node."""
    nu = harness.create_artifact(
        f"nu: the case against {victim_id[:12]} is sound",
        provenance=Provenance(role="critic"),
    )
    return harness.create_artifact(
        f"criticism of {victim_id[:12]}",
        provenance=Provenance(role="critic"),
        warrants=[
            Warrant(
                id=warrant_id,
                target=victim_id,
                type=WarrantType.ARGUMENTATIVE,
                validity_node=nu.id,
            )
        ],
    )


def _nu_of(harness, target_id):
    """The validity node of the warrant minted against `target_id`.

    Read through `harness.warrants` rather than the critic artifact's own
    `warrants` field: that field is the legacy on-record encoding, and a
    warrant acquired after the carrier's content was fixed lives only in the
    carriage relation (DR-CON-warrants-and-attacks, Traps).
    """
    warrant = next(w for w in harness.warrants.values() if w.target == target_id)
    return harness.state.artifacts[warrant.validity_node]


# --------------------------------------------------------------------------
# The defect itself.
# --------------------------------------------------------------------------


def test_a_declared_premise_is_registered_on_the_validity_node_as_evidence(harness):
    target, premise = _target_and_premise(harness)
    critic = crit_argumentative(
        harness,
        target.id,
        _adapter(
            harness,
            {"attack": True, "case": _CASE, "premises_essential": [premise.id]},
        ),
        Config(
            ARGUMENTATIVE_AUTHORITY="trial_required",
            ADJUDICATION_STATUS_AUTHORITY_ENABLED=True,
        ),
    )

    assert critic is not None
    nu = _nu_of(harness, target.id)
    assert [(ref.target, ref.role) for ref in nu.interface.refs] == [
        (premise.id, RefRole.EVIDENCE)
    ]


def test_refuting_a_declared_premise_reinstates_the_criticism_s_target(harness):
    """The §0 pair, reached through the contract instead of by hand."""
    target, premise = _target_and_premise(harness)
    critic = crit_argumentative(
        harness,
        target.id,
        _adapter(
            harness,
            {"attack": True, "case": _CASE, "premises_essential": [premise.id]},
        ),
        Config(
            ARGUMENTATIVE_AUTHORITY="trial_required",
            ADJUDICATION_STATUS_AUTHORITY_ENABLED=True,
        ),
    )
    assert critic is not None
    assert harness.state.status[target.id] == Status.REFUTED

    _refute(harness, premise.id, warrant_id="w:test:premise")

    assert (
        harness.state.status[target.id].value,
        harness.state.status[critic.id].value,
    ) == ("accepted", "refuted")


def test_a_criticism_that_declares_nothing_keeps_todays_behaviour(harness):
    """The formalism-optional law, as a test rather than a promise: declaring
    no premise is a complete answer, mints exactly what it always minted, and
    is not weakened by anything the declaration road added."""
    target, premise = _target_and_premise(harness)
    critic = crit_argumentative(
        harness,
        target.id,
        _adapter(harness, {"attack": True, "case": _CASE}),
        Config(
            ARGUMENTATIVE_AUTHORITY="trial_required",
            ADJUDICATION_STATUS_AUTHORITY_ENABLED=True,
        ),
    )

    assert critic is not None
    assert _nu_of(harness, target.id).interface.refs == []
    assert harness.state.status[target.id] == Status.REFUTED

    _refute(harness, premise.id, warrant_id="w:test:premise")

    # Refuting an artifact this criticism never leaned on changes nothing:
    # the target stays refuted, exactly as it does today.
    assert harness.state.status[target.id] == Status.REFUTED
    assert harness.state.status[critic.id] == Status.ACCEPTED


def test_an_empty_declaration_is_never_a_failed_call(harness):
    """The source proposal's "empty discriminator is a failed call" rule was
    NOT adopted, and its analogue for this field must stay un-adopted: no
    decline, no penalty, no missing warrant."""
    target, _ = _target_and_premise(harness)
    critic = crit_argumentative(
        harness,
        target.id,
        _adapter(
            harness, {"attack": True, "case": _CASE, "premises_essential": []}
        ),
        Config(
            ARGUMENTATIVE_AUTHORITY="trial_required",
            ADJUDICATION_STATUS_AUTHORITY_ENABLED=True,
        ),
    )

    assert critic is not None
    declines = [
        event
        for event in harness.log.read()
        if list(event.inputs)[:1] == ["trial-declined"]
    ]
    assert declines == []


def test_a_premise_absent_from_the_record_mints_nothing_and_is_recorded(harness):
    """Never a silent drop: an id naming nothing declines typed, above any
    provider spend, and leaves the target's status untouched."""
    target, _ = _target_and_premise(harness)
    critic = crit_argumentative(
        harness,
        target.id,
        _adapter(
            harness,
            {
                "attack": True,
                "case": _CASE,
                "premises_essential": ["0" * 64],
            },
        ),
        Config(
            ARGUMENTATIVE_AUTHORITY="trial_required",
            ADJUDICATION_STATUS_AUTHORITY_ENABLED=True,
        ),
    )

    assert critic is None
    assert harness.state.status[target.id] == Status.ACCEPTED
    assert not harness.state.att
    reasons = [
        list(event.inputs)[2]
        for event in harness.log.read()
        if list(event.inputs)[:1] == ["trial-declined"]
    ]
    assert reasons == ["unknown-premise"]


# --------------------------------------------------------------------------
# The wire road: an unknown handle is a failed call, not a silent drop.
# --------------------------------------------------------------------------


def test_the_compact_contract_names_the_legal_premises_and_resolves_them():
    aliases = AliasTable(aliases={"A1": "art-target", "A2": "art-premise"})
    contract = CriticWireContract(aliases=aliases, expected_target="art-target")

    schema = contract.model_json_schema()
    field = schema["properties"]["essential_premise_aliases"]
    assert field["items"] == {"type": "string", "enum": ["A1", "A2"]}

    compiled = contract.compile(
        contract.wire_model.model_construct(
            attack=True,
            target_alias="A1",
            claim="c",
            grounds="g",
            cited_input_aliases=[],
            essential_premise_aliases=["A2"],
        )
    )
    assert compiled.premises_essential == ["art-premise"]

    with pytest.raises(UnknownAliasError):
        contract.compile(
            contract.wire_model.model_construct(
                attack=True,
                target_alias="A1",
                claim="c",
                grounds="g",
                cited_input_aliases=[],
                essential_premise_aliases=["Z9"],
            )
        )


def test_the_field_is_optional_on_both_criticism_outputs():
    """The symmetry `DR-CON-criticism-source` already asserts for
    `successor_question`: a field one criticism seat can fill and the other
    cannot is a difference in surface, not in contract."""
    for model in (ArgumentativeCriticOutput, BatchCase):
        assert "premises_essential" in model.model_fields
    assert ArgumentativeCriticOutput(attack=False).premises_essential is None
    assert BatchCase(target="t", attack=False).premises_essential is None


def test_an_undeclared_criticism_canonicalises_to_the_bytes_it_always_did():
    """Regression (this tranche, caught by
    `tests/test_l1_continue_resumable_crash.py` before it was committed): the
    critic output's dump is content-addressed and compared on recovery
    (`workflow/nonconjecture_recovery.py`, "critic admission differs from the
    durable validated output"). A field defaulting to `[]` rather than `None`
    survives `exclude_none`, moves that digest, and makes every committed
    critic transaction unreplayable -- a change to what is WRITTEN, made to
    fix what is READ."""
    from deepreason.canonical import canonical_json

    dumped = ArgumentativeCriticOutput(attack=True, case="c").model_dump(
        mode="json", exclude_none=True
    )
    assert "premises_essential" not in dumped
    assert canonical_json(dumped) == canonical_json(
        {"attack": True, "case": "c"}
    )


# --------------------------------------------------------------------------
# A KNOWN GAP, recorded and not fixed here.
# --------------------------------------------------------------------------


def test_an_undecided_essential_premise_leaves_its_target_refuted_today(tmp_path):
    """KNOWN GAP, recorded rather than fixed (monitor amendment, 2026-09-05).

    Fixture F2 of the OIS 1.1 audit
    (`experiments/2026-09-05-audit-ois-1-1-spec-drift/proof/
    check11_da1_vs_harness.py`): the criticism's essential premise is not
    REFUTED but UNDECIDED — K and a rival M attack each other, so both
    suspend. Spec §11.3 says an undecided essential premise prevents its
    dependent from becoming in; DeepReason leaves the criticism's target
    `refuted`.

    That is a DIFFERENT defect from the one this tranche fixes, with a
    different cause (pass ORDER in `adjudication/`), and `adjudication/` is
    out of this tranche's scope by its GOAL.md and by the monitor's
    instruction. So this test asserts what the harness DOES today, deliberately
    — it is a tripwire, not an approval. When the pass-order tranche lands it
    will go red, and that is the signal to update it, not a regression.
    See PARKED.md P4.

    The declaration road this tranche added is NOT what is being measured: the
    criticism here declares nothing, and the fixture is the audit's, unchanged
    in shape.
    """
    from deepreason.harness import Harness
    from deepreason.ontology import Interface, Ref
    from deepreason.ontology.artifact import Artifact

    harness = Harness(tmp_path / "f2")

    # M's warrant against K must exist before M does, so K's warrant names M's
    # id in advance: ids are content addresses, and edges.py lets a warrant
    # target dangle until its target appears.
    m_text = "M: rival standard"
    m_id = Artifact.compute_id(f"inline:{m_text}", "utf8", Interface())

    target = harness.create_artifact(
        "A: the target account", provenance=Provenance(role="critic")
    )
    nu_k = harness.create_artifact("nu K->M", provenance=Provenance(role="critic"))
    premise = harness.create_artifact(
        "K: the standard",
        provenance=Provenance(role="critic"),
        warrants=[
            Warrant(
                id="w:K->M",
                target=m_id,
                type=WarrantType.ARGUMENTATIVE,
                validity_node=nu_k.id,
            )
        ],
    )
    nu_m = harness.create_artifact("nu M->K", provenance=Provenance(role="critic"))
    rival = harness.create_artifact(
        m_text,
        provenance=Provenance(role="critic"),
        warrants=[
            Warrant(
                id="w:M->K",
                target=premise.id,
                type=WarrantType.ARGUMENTATIVE,
                validity_node=nu_m.id,
            )
        ],
    )
    assert rival.id == m_id, "content-addressed id prediction failed"

    nu_c = harness.create_artifact("nu of C", provenance=Provenance(role="critic"))
    criticism = harness.create_artifact(
        "C: criticism of A, essentially using K",
        provenance=Provenance(role="critic"),
        interface=Interface(refs=[Ref(target=premise.id, role=RefRole.DEPENDENCE)]),
        warrants=[
            Warrant(
                id="w:C->A",
                target=target.id,
                type=WarrantType.ARGUMENTATIVE,
                validity_node=nu_c.id,
            )
        ],
    )

    labels = {
        "A": harness.state.status[target.id].value,
        "K": harness.state.status[premise.id].value,
        "M": harness.state.status[rival.id].value,
        "C": harness.state.status[criticism.id].value,
    }
    assert labels == {
        "A": "refuted",
        "K": "suspended",
        "M": "suspended",
        "C": "suspended_unsupported",
    }, labels
