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


def build_scenario(root) -> tuple[Harness, dict[str, str], str]:
    """Standard-refutation scenario: refute, then reinstate via case law.

    Also returns the LIVE state snapshot captured at the moment the critic
    refuted the target (before the reinstating attack) — so time-travel can
    be checked against genuine live state, not against a second replay."""
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
    from deepreason.informal.trial import transcript_blob

    critic = h.create_artifact(
        "critic: fails std-1",
        warrants=[
            Warrant(
                id="w-verdict",
                target=target.id,
                type=WarrantType.DEMONSTRATIVE,
                commitment="kappa-taste",
                verdict="fail",
                trace_ref=transcript_blob(
                    h,
                    case="the work violates clause 1 of std-1",
                    answer="the defence disputes the clause's scope",
                    decisive_point="violates clause 1",
                ),
                validity_node=nu.id,
            )
        ],
    )
    # Live state at the refutation point, captured from the LIVE harness
    # before the reinstating attack — the ground truth for time-travel.
    live_at_critic = h.state.model_dump_json()
    attack(h, standard.id, "std-1-is-wrong")
    return h, {"target": target.id, "standard": standard.id, "critic": critic.id}, live_at_critic


def test_replay_reproduces_state_byte_for_byte(tmp_path):
    root = tmp_path / "run"
    live, _, _ = build_scenario(root)
    snapshot = live.state.model_dump_json()

    reopened = Harness(root)  # materializes purely from the log
    assert reopened.state.model_dump_json() == snapshot
    assert reopened.commitments == live.commitments
    assert reopened.warrants == live.warrants


def test_time_travel_truncated_replay(tmp_path):
    root = tmp_path / "run"
    live, ids, live_at_critic = build_scenario(root)
    assert live.state.status[ids["target"]] == Status.ACCEPTED  # reinstated at head

    # Find the seq of the critic's registration: target refuted at that point.
    critic_seq = next(
        e.seq for e in live.log.read() if ids["critic"] in e.outputs
    )
    past = Harness.at(root, critic_seq)
    assert past.state.status[ids["target"]] == Status.REFUTED
    assert ids["standard"] in past.state.artifacts
    assert past.state.addr == [(ids["target"], "pi-1")]

    # Truncated replay of a prefix must reproduce the LIVE state as it was at
    # that prefix (captured from the live harness), not merely a second replay
    # of the same log — this is what proves live and replay do not diverge.
    assert past.state.model_dump_json() == live_at_critic
