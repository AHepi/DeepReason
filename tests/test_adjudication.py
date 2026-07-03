"""P0 acceptance tests (spec §16) — deterministic core.

Grounded extension correctness, reinstatement (Lemma 3.1), validity-node
closure, two-pass support cascade, dep cycle rejection, and the case-law
closure: standard refutation => dependent-verdict collapse => target
reinstatement, all in pass 1.
"""

import pytest

from deepreason.harness import WellFormednessError
from deepreason.ontology import (
    Artifact,
    Commitment,
    Interface,
    Provenance,
    Ref,
    Status,
    Warrant,
    WarrantType,
)
from tests.conftest import art, attack


def test_grounded_extension_unattacked_accepted(harness):
    a = art(harness, "claim A")
    assert harness.state.status[a.id] == Status.ACCEPTED


def test_attack_refutes(harness):
    target = art(harness, "target claim")
    critic, nu = attack(harness, target.id, "c1")
    status = harness.state.status
    assert status[target.id] == Status.REFUTED
    assert status[critic.id] == Status.ACCEPTED
    assert status[nu.id] == Status.ACCEPTED


def test_reinstatement_lemma_3_1(harness):
    """k attacks a, j attacks k, j unattacked => {j, a} accepted."""
    a = art(harness, "target claim")
    k, _ = attack(harness, a.id, "k")
    assert harness.state.status[a.id] == Status.REFUTED
    j, _ = attack(harness, k.id, "j")
    status = harness.state.status
    assert status[j.id] == Status.ACCEPTED
    assert status[k.id] == Status.REFUTED
    assert status[a.id] == Status.ACCEPTED  # reinstated, derived not ruled


def test_validity_node_closure(harness):
    """Attacking a warrant's nu attacks the warrant (via its carrier)."""
    target = art(harness, "target claim")
    critic, nu = attack(harness, target.id, "c1")
    assert harness.state.status[target.id] == Status.REFUTED
    attack(harness, nu.id, "nu-is-unsound")
    status = harness.state.status
    assert status[nu.id] == Status.REFUTED
    assert status[critic.id] == Status.REFUTED  # closure lifted the attack
    assert status[target.id] == Status.ACCEPTED  # reinstated


def test_support_cascade_orphaned_not_false(harness):
    premise = art(harness, "premise")
    dependent = art(
        harness,
        "dependent claim",
        interface=Interface(refs=[Ref(target=premise.id, role="dependence")]),
    )
    assert harness.state.status[dependent.id] == Status.ACCEPTED
    attack(harness, premise.id, "kills-premise")
    status = harness.state.status
    assert status[premise.id] == Status.REFUTED
    assert status[dependent.id] == Status.SUSPENDED_UNSUPPORTED  # NOT refuted


def test_mutual_attack_suspended(harness):
    """An unresolved attack cycle leaves both suspended (grounded semantics)."""
    nu1 = art(harness, "nu 1")
    nu2 = art(harness, "nu 2")
    w1 = Warrant(id="w1", target="B", type=WarrantType.ARGUMENTATIVE, validity_node=nu1.id)
    a = Artifact(
        id="A", content_ref="inline:critic A", warrants=["w1"],
        provenance=Provenance(role="critic"),
    )
    harness.register_artifact(a, warrants=[w1])  # target "B" dangles until B registers
    w2 = Warrant(id="w2", target="A", type=WarrantType.ARGUMENTATIVE, validity_node=nu2.id)
    b = Artifact(
        id="B", content_ref="inline:critic B", warrants=["w2"],
        provenance=Provenance(role="critic"),
    )
    harness.register_artifact(b, warrants=[w2])
    assert harness.state.status["A"] == Status.SUSPENDED
    assert harness.state.status["B"] == Status.SUSPENDED


def test_dep_cycle_rejected(harness):
    a = Artifact(
        id="A",
        content_ref="inline:a",
        interface=Interface(refs=[Ref(target="B", role="dependence")]),
        provenance=Provenance(role="import"),
    )
    harness.register_artifact(a)  # dangling dependence: no edge yet
    b = Artifact(
        id="B",
        content_ref="inline:b",
        interface=Interface(refs=[Ref(target="A", role="dependence")]),
        provenance=Provenance(role="import"),
    )
    with pytest.raises(WellFormednessError):
        harness.register_artifact(b)  # materializing B would close the cycle


def test_standard_refutation_collapses_verdicts_and_reinstates(harness):
    """Case-law closure (§1): refute a standard => every nu citing it is
    attacked => warrants fall => targets reinstate (parallel fifths)."""
    harness.register_commitment(Commitment(id="kappa-taste", eval="rubric:std-1"))
    standard = art(harness, "standard std-1: no parallel fifths")
    target = art(
        harness, "informal work", interface=Interface(commitments=["kappa-taste"])
    )
    nu = art(
        harness,
        "nu: judged under std-1",
        interface=Interface(refs=[Ref(target=standard.id, role="mention")]),
    )
    from deepreason.informal.trial import transcript_blob

    verdict_warrant = Warrant(
        id="w-verdict",
        target=target.id,
        type=WarrantType.DEMONSTRATIVE,
        commitment="kappa-taste",
        verdict="fail",
        trace_ref=transcript_blob(
            harness,
            case="the work violates clause 1 of std-1",
            answer="the defence disputes the clause's scope",
            decisive_point="violates clause 1",
        ),
        validity_node=nu.id,
    )
    critic = harness.create_artifact(
        "critic: fails std-1",
        provenance=Provenance(role="critic"),
        warrants=[verdict_warrant],
    )
    assert harness.state.status[target.id] == Status.REFUTED

    # The productive attack lands on the standard, not the work (§10.3).
    attacker, _ = attack(harness, standard.id, "std-1-is-wrong")
    status = harness.state.status
    assert status[standard.id] == Status.REFUTED
    assert status[nu.id] == Status.REFUTED       # case-law extension
    assert status[critic.id] == Status.REFUTED   # validity-node closure
    assert status[target.id] == Status.ACCEPTED  # reinstated, computed not curated
    assert status[attacker.id] == Status.ACCEPTED


def test_unregistered_warrant_rejected(harness):
    a = Artifact(
        id="X", content_ref="inline:x", warrants=["ghost"],
        provenance=Provenance(role="critic"),
    )
    with pytest.raises(WellFormednessError):
        harness.register_artifact(a)
