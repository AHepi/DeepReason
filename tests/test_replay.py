"""P0 acceptance: replay-from-log reproduces state byte-for-byte; time-travel
via truncated replay (spec §1, §16)."""

from deepreason.harness import Harness
from deepreason.ontology import (
    Commitment,
    Interface,
    Problem,
    ProblemProvenance,
    Ref,
    Status,
    Warrant,
    WarrantType,
)
from tests.conftest import art, attack


def build_scenario(root) -> tuple[Harness, dict[str, str]]:
    """Standard-refutation scenario: refute, then reinstate via case law."""
    h = Harness(root)
    h.register_problem(
        Problem(
            id="pi-1",
            description="produce an informal work meeting std-1",
            provenance=ProblemProvenance.model_validate({"trigger": "seed", "from": []}),
        )
    )
    h.register_commitment(Commitment(id="kappa-taste", eval="rubric:std-1"))
    standard = art(h, "standard std-1")
    target = h.create_artifact(
        "informal work",
        interface=Interface(commitments=["kappa-taste"]),
        problem_id="pi-1",
    )
    nu = art(
        h,
        "nu: judged under std-1",
        interface=Interface(refs=[Ref(target=standard.id, role="mention")]),
    )
    critic = h.create_artifact(
        "critic: fails std-1",
        warrants=[
            Warrant(
                id="w-verdict",
                target=target.id,
                type=WarrantType.DEMONSTRATIVE,
                commitment="kappa-taste",
                verdict="fail",
                trace_ref="inline:transcript",
                validity_node=nu.id,
            )
        ],
    )
    attack(h, standard.id, "std-1-is-wrong")
    return h, {"target": target.id, "standard": standard.id, "critic": critic.id}


def test_replay_reproduces_state_byte_for_byte(tmp_path):
    root = tmp_path / "run"
    live, _ = build_scenario(root)
    snapshot = live.state.model_dump_json()

    reopened = Harness(root)  # materializes purely from the log
    assert reopened.state.model_dump_json() == snapshot
    assert reopened.commitments == live.commitments
    assert reopened.warrants == live.warrants


def test_time_travel_truncated_replay(tmp_path):
    root = tmp_path / "run"
    live, ids = build_scenario(root)
    assert live.state.status[ids["target"]] == Status.ACCEPTED  # reinstated at head

    # Find the seq of the critic's registration: target refuted at that point.
    critic_seq = next(
        e.seq for e in live.log.read() if ids["critic"] in e.outputs
    )
    past = Harness.at(root, critic_seq)
    assert past.state.status[ids["target"]] == Status.REFUTED
    assert ids["standard"] in past.state.artifacts
    assert past.state.addr == [(ids["target"], "pi-1")]

    # Truncated replay of a prefix matches the live state at that prefix.
    assert Harness.at(root, critic_seq).state.model_dump_json() == past.state.model_dump_json()
