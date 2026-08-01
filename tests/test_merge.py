"""P3 acceptance (spec §16): two divergent saved graphs merge and
re-adjudicate with no manual conflict resolution; identical artifacts
dedupe by id; school registries union cleanly."""

import shutil

import pytest

from deepreason.capture import schools
from deepreason.config import Config
from deepreason.control_events import ControlEventPayloadV1
from deepreason.harness import Harness
from deepreason.ontology import (
    Commitment,
    Event,
    LLMCall,
    Problem,
    ProblemProvenance,
    Provenance,
    Rule,
    Status,
    Warrant,
    WarrantType,
)
from deepreason.storage.merge import ControlEventMergeError, merge
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


def test_merge_preserves_carriage_added_to_existing_artifact(tmp_path):
    """A source may attach a second warrant to already-deduped critic prose."""
    source_root, dest_root = tmp_path / "source", tmp_path / "dest"
    source = Harness(source_root)
    target_a = art(source, "target A")
    target_b = art(source, "target B")
    nu_a = art(source, "nu A")
    first = Warrant(
        id="w-a",
        target=target_a.id,
        type=WarrantType.ARGUMENTATIVE,
        validity_node=nu_a.id,
    )
    carrier = source.create_artifact(
        "one shared criticism",
        provenance=Provenance(role="critic"),
        warrants=[first],
    )
    shutil.copytree(source_root, dest_root)

    nu_b = art(source, "nu B")
    second = Warrant(
        id="w-b",
        target=target_b.id,
        type=WarrantType.ARGUMENTATIVE,
        validity_node=nu_b.id,
    )
    same_carrier = source.create_artifact(
        "one shared criticism",
        provenance=Provenance(role="critic"),
        warrants=[second],
    )
    assert same_carrier.id == carrier.id
    assert source.state.status[target_b.id] == Status.REFUTED

    dest = Harness(dest_root)
    assert dest.state.status[target_b.id] == Status.ACCEPTED
    merge(dest, source_root)

    assert set(dest.carried_warrant_ids(carrier.id)) == {"w-a", "w-b"}
    assert dest.state.status[target_b.id] == Status.REFUTED
    assert Harness(dest_root).state == dest.state


def test_control_source_is_rejected_before_any_destination_mutation(tmp_path):
    source_root, dest_root = tmp_path / "source-control", tmp_path / "dest"
    source = Harness(source_root)
    source_commitment = source.register_commitment(
        Commitment(id="source-only", eval="predicate:True")
    )
    source_blob = source.blobs.put(b"source-only merge payload")

    work_order_id = "sha256:" + "a" * 64
    decision_id = "sha256:" + "d" * 64
    payload = ControlEventPayloadV1(
        decision_ref=decision_id,
        inputs=[work_order_id, "problem:source-control"],
        outputs=[decision_id],
    )
    # Deliberately append only a syntactically valid authority envelope.  The
    # merge preflight must detect Rule.CONTROL without opening or materializing
    # its referenced workflow objects.
    source.log.append(
        Event(
            seq=source._next_seq,
            ts="2026-07-16T00:00:00Z",
            rule=Rule.CONTROL,
            inputs=list(payload.inputs),
            outputs=list(payload.outputs),
            control=payload,
        )
    )

    destination = Harness(dest_root)
    destination.register_commitment(
        Commitment(id="destination-only", eval="predicate:True")
    )
    before = {
        str(path.relative_to(dest_root)): path.read_bytes()
        for path in dest_root.rglob("*")
        if path.is_file()
    }

    with pytest.raises(ControlEventMergeError, match="Control events"):
        merge(destination, source_root)

    after = {
        str(path.relative_to(dest_root)): path.read_bytes()
        for path in dest_root.rglob("*")
        if path.is_file()
    }
    assert after == before
    assert source_blob not in {
        path.name for path in destination.blobs.root.rglob("*") if path.is_file()
    }
    with pytest.raises(KeyError):
        destination.objects.get(source_commitment.id)


def test_work_bound_call_is_rejected_before_any_destination_mutation(tmp_path):
    source_root, dest_root = tmp_path / "source-work-call", tmp_path / "dest"
    source = Harness(source_root)
    source_commitment = source.register_commitment(
        Commitment(id="source-work-call-only", eval="predicate:True")
    )
    source_blob = source.blobs.put(b"source-only work-bound provider payload")
    source.log.append(
        Event(
            seq=source._next_seq,
            ts="2026-07-16T00:00:00Z",
            rule=Rule.MEASURE,
            inputs=["provider-result"],
            llm=LLMCall(
                role="conjecturer",
                model="fixture",
                endpoint="fixture://merge",
                prompt_ref=source_blob,
                raw_ref=source_blob,
                work_order_id="sha256:" + "a" * 64,
            ),
        )
    )

    destination = Harness(dest_root)
    destination.register_commitment(
        Commitment(id="destination-only", eval="predicate:True")
    )
    before = {
        str(path.relative_to(dest_root)): path.read_bytes()
        for path in dest_root.rglob("*")
        if path.is_file()
    }

    with pytest.raises(ControlEventMergeError, match="work-bound provider"):
        merge(destination, source_root)

    after = {
        str(path.relative_to(dest_root)): path.read_bytes()
        for path in dest_root.rglob("*")
        if path.is_file()
    }
    assert after == before
    assert source_blob not in {
        path.name for path in destination.blobs.root.rglob("*") if path.is_file()
    }
    with pytest.raises(KeyError):
        destination.objects.get(source_commitment.id)
