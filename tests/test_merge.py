"""P3 acceptance (spec §16): two divergent saved graphs merge and
re-adjudicate with no manual conflict resolution; identical artifacts
dedupe by id; school registries union cleanly."""

import shutil

from deepreason.capture import schools
from deepreason.config import Config
from deepreason.harness import Harness
from deepreason.ontology import Commitment, Problem, ProblemProvenance, Status
from deepreason.storage.merge import merge
from tests.conftest import art, attack


def _base(root) -> Harness:
    harness = Harness(root)
    harness.register_commitment(Commitment(id="k-true", eval="predicate:True"))
    harness.register_problem(
        Problem(
            id="pi-1",
            description="a shared seed problem",
            criteria=["k-true"],
            provenance=ProblemProvenance.model_validate({"trigger": "seed", "from": []}),
        )
    )
    schools.init_schools(harness, Config(N_SCHOOLS=2))
    art(harness, "the common ancestor claim")
    return harness


def test_divergent_graphs_merge_and_readjudicate(tmp_path):
    root_a, root_b = tmp_path / "a", tmp_path / "b"
    harness_a = _base(root_a)
    ancestor = next(
        aid for aid, a in harness_a.state.artifacts.items()
        if a.content_ref == "inline:the common ancestor claim"
    )
    shutil.copytree(root_a, root_b)  # fork the session

    # Session A diverges: attacks the ancestor.
    critic_a, _ = attack(harness_a, ancestor, "a-attacks-ancestor")
    assert harness_a.state.status[ancestor] == Status.REFUTED

    # Session B diverges independently: a new artifact, plus a counter-attack
    # on A's critic — whose id B knows but whose artifact B never saw
    # (a dangling target until the union supplies it).
    harness_b = Harness(root_b)
    new_b = art(harness_b, "a claim only B has")
    counter_b, _ = attack(harness_b, critic_a.id, "b-defends-ancestor")

    stats = merge(harness_a, root_b)
    assert stats["merged_objects"] > 0

    # Union re-adjudicated: B's counter-attack materialized against A's
    # critic, reinstating the ancestor — no manual conflict resolution.
    status = harness_a.state.status
    assert status[new_b.id] == Status.ACCEPTED
    assert status[counter_b.id] == Status.ACCEPTED
    assert status[critic_a.id] == Status.REFUTED
    assert status[ancestor] == Status.ACCEPTED

    # Merged history is itself replayable byte-for-byte.
    assert Harness(root_a).state.model_dump_json() == harness_a.state.model_dump_json()


def test_identical_artifacts_dedupe_and_schools_union(tmp_path):
    root_a, root_b = tmp_path / "a", tmp_path / "b"
    harness_a = _base(root_a)
    shutil.copytree(root_a, root_b)
    harness_b = Harness(root_b)
    art(harness_b, "b-only claim")

    before = set(harness_a.state.artifacts)
    stats = merge(harness_a, root_b)
    after = set(harness_a.state.artifacts)
    # Only the genuinely new artifact arrived; shared history deduped by id.
    assert len(after - before) == 1
    assert stats["merged_objects"] == 1

    # School registries union cleanly: same ids, same policies, no dupes.
    roster = schools.roster(harness_a)
    assert sorted(roster) == ["school-0", "school-1"]


def test_merge_is_idempotent(tmp_path):
    root_a, root_b = tmp_path / "a", tmp_path / "b"
    harness_a = _base(root_a)
    shutil.copytree(root_a, root_b)
    harness_b = Harness(root_b)
    art(harness_b, "b-only claim")
    merge(harness_a, root_b)
    snapshot = harness_a.state.model_dump_json()
    stats = merge(harness_a, root_b)  # merging again adds nothing
    assert stats["merged_objects"] == 0 and stats["merged_events"] == 0
    assert harness_a.state.model_dump_json() == snapshot
