"""Anti-relapse gate (spec §3, §11.5): hash + battery-equivalence stages."""

from deepreason.ontology import (
    Artifact,
    Commitment,
    Interface,
    Provenance,
    Status,
    Warrant,
    WarrantType,
)
from deepreason.rules.crit import crit_program
from deepreason.rules.guards.anti_relapse import check
from tests.conftest import art


def _unregistered(text: str, commitments: list[str]) -> Artifact:
    interface = Interface(commitments=commitments)
    content_ref = f"inline:{text}"
    return Artifact(
        id=Artifact.compute_id(content_ref, "utf8", interface),
        content_ref=content_ref,
        codec="utf8",
        interface=interface,
        provenance=Provenance(role="conjecturer"),
    )


def _refute_by_program(harness) -> Artifact:
    harness.register_commitment(Commitment(id="k-moon", eval="predicate:'moon' in content"))
    bad = art(harness, "the tides are magic", interface=Interface(commitments=["k-moon"]))
    crit_program(harness, bad.id)
    assert harness.state.status[bad.id] == Status.REFUTED
    return bad


def test_hash_stage_blocks_refuted_resubmission(harness):
    bad = _refute_by_program(harness)
    resubmission = _unregistered("the tides are magic", ["k-moon"])
    assert resubmission.id == bad.id  # same content + interface => same id
    admitted, reason = check(resubmission, [], harness)
    assert not admitted
    assert reason.startswith("hash")


def test_battery_stage_blocks_equivalent_relapse(harness):
    _refute_by_program(harness)
    paraphrase = _unregistered("tides happen because of magic", ["k-moon"])
    admitted, reason = check(paraphrase, [], harness)
    assert not admitted
    assert "battery-equivalent" in reason


def test_differing_verdicts_admit(harness):
    _refute_by_program(harness)
    candidate = _unregistered("the moon pulls the sea", ["k-moon"])
    admitted, _ = check(candidate, [], harness)
    assert admitted


def test_counter_warrant_exempts(harness):
    """~=_B to a refuted prior is admitted iff it carries a warrant against
    the prior's refuter (spec §3 stage 3)."""
    bad = _refute_by_program(harness)
    refuter = next(
        x
        for x, t in harness.state.att
        if t == bad.id and harness.state.status[x] == Status.ACCEPTED
    )
    nu = art(harness, "nu: the k-moon test is unfair here")
    counter = Warrant(
        id="w-counter", target=refuter, type=WarrantType.ARGUMENTATIVE, validity_node=nu.id
    )
    candidate = _unregistered("tides happen because of magic", ["k-moon"])
    admitted, _ = check(candidate, [counter], harness)
    assert admitted


def test_semantic_gate_blocks_paraphrase_admits_differing_neighbor(harness):
    """P2 acceptance: with the embedder, a near-duplicate of a refuted
    artifact within NEAR_DUP_EPS faces the battery check and blocks; a
    near-neighbor whose verdict-vector differs is admitted (§11.5)."""
    from deepreason.llm.embedder import HashingEmbedder

    _refute_by_program(harness)  # refutes "the tides are magic"
    embedder = HashingEmbedder()
    eps = 0.6
    paraphrase = _unregistered("the tides are magic surely", ["k-moon"])
    admitted, reason = check(paraphrase, [], harness, embedder=embedder, near_dup_eps=eps)
    assert not admitted and "battery-equivalent" in reason
    # Near in embedding space but satisfies the criterion => verdicts differ.
    neighbor = _unregistered("the tides are moon magic", ["k-moon"])
    admitted, _ = check(neighbor, [], harness, embedder=embedder, near_dup_eps=eps)
    assert admitted
    # Far outside eps: the battery check never even runs => admitted cheaply.
    far = _unregistered("continental drift reshapes basins", ["k-moon"])
    admitted, _ = check(far, [], harness, embedder=embedder, near_dup_eps=0.1)
    assert admitted


def test_near_duplicates_of_accepted_never_blocked(harness):
    harness.register_commitment(Commitment(id="k-moon", eval="predicate:'moon' in content"))
    art(harness, "the moon pulls the sea", interface=Interface(commitments=["k-moon"]))
    twin = _unregistered("the moon pulls the seas", ["k-moon"])
    admitted, _ = check(twin, [], harness)
    assert admitted  # blocking would be a diversity gate adjudicating (§0)
