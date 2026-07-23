"""Hard persistence invariants: immutable records, unambiguous objects,
strict event order, and non-writing time-travel views."""

import hashlib
import json

import pytest
from pydantic import ValidationError

from deepreason.canonical import canonical_json
from deepreason.harness import Harness, ReadOnlyHarnessError, WellFormednessError
from deepreason.invariants import verify_root
from deepreason.log.event_log import EventSequenceError
from deepreason.ontology import (
    Commitment,
    Interface,
    Problem,
    ProblemProvenance,
    Provenance,
    Rule,
)
from deepreason.storage.merge import merge
from deepreason.storage.objects import ObjectConflictError, ObjectStore


def _problem(pid: str = "pi-1", description: str = "a problem") -> Problem:
    return Problem(
        id=pid,
        description=description,
        criteria=["k"],
        provenance=ProblemProvenance.model_validate({"trigger": "seed", "from": []}),
    )


def _tree_digest(root) -> str:
    digest = hashlib.sha256()
    for path in sorted(p for p in root.rglob("*") if p.is_file()):
        digest.update(str(path.relative_to(root)).encode())
        digest.update(path.read_bytes())
    return digest.hexdigest()


def test_registered_ontology_records_are_deeply_immutable(tmp_path):
    harness = Harness(tmp_path / "run")
    commitment = harness.register_commitment(
        Commitment(id="k", eval="predicate:True", budget={"extra": {"case": "fixed"}})
    )
    problem = harness.register_problem(_problem())
    artifact = harness.create_artifact(
        "claim",
        interface=Interface(commitments=[commitment.id]),
        provenance=Provenance(role="seed"),
    )

    with pytest.raises(ValidationError):
        commitment.eval = "predicate:False"
    with pytest.raises(TypeError, match="immutable"):
        commitment.budget.extra["case"] = "rewritten"
    with pytest.raises(TypeError, match="immutable"):
        problem.criteria.append("another")
    with pytest.raises(TypeError, match="immutable"):
        artifact.interface.commitments.append("another")
    with pytest.raises(ValidationError):
        artifact.provenance.school = "rewritten"

    assert Harness(harness.root).state == harness.state


def test_harness_rejects_same_id_commitment_and_problem_conflicts(tmp_path):
    harness = Harness(tmp_path / "run")
    harness.register_commitment(Commitment(id="k", eval="predicate:True"))
    harness.register_problem(_problem())
    before = harness.log.path.read_bytes()

    with pytest.raises(WellFormednessError, match="commitment id"):
        harness.register_commitment(Commitment(id="k", eval="predicate:False"))
    with pytest.raises(WellFormednessError, match="problem id"):
        harness.register_problem(_problem(description="a rewritten problem"))

    assert harness.log.path.read_bytes() == before


def test_object_store_is_namespaced_and_rejects_cross_schema_collision(tmp_path):
    store = ObjectStore(tmp_path / "objects")
    commitment = Commitment(id="shared-id", eval="predicate:True")
    store.put("commitment", commitment)

    assert store._schema_path("commitment", commitment.id).exists()
    assert not store._path(commitment.id).exists()
    with pytest.raises(ObjectConflictError, match="conflicts"):
        store.put("problem", _problem(pid="shared-id"))
    with pytest.raises(ObjectConflictError, match="conflicts"):
        store.put("commitment", Commitment(id="shared-id", eval="predicate:False"))

    # Typed reads must not hide a second namespaced record in a corrupt root.
    problem = _problem(pid="shared-id")
    conflicting = {
        "schema": "problem",
        "id": problem.id,
        "data": problem.model_dump(mode="json", by_alias=True),
    }
    path = store._schema_path("problem", problem.id)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(canonical_json(conflicting))
    with pytest.raises(ObjectConflictError, match="multiple schemas"):
        store.get("shared-id", schema="commitment")


def test_legacy_flat_object_is_readable_and_lazily_namespaced(tmp_path):
    store = ObjectStore(tmp_path / "objects")
    commitment = Commitment(id="k-legacy", eval="predicate:True")
    record = {
        "schema": "commitment",
        "id": commitment.id,
        "data": commitment.model_dump(mode="json", by_alias=True),
    }
    legacy = store._path(commitment.id)
    legacy.parent.mkdir(parents=True, exist_ok=True)
    legacy.write_bytes(canonical_json(record))

    schema, loaded = store.get(commitment.id)
    assert schema == "commitment" and loaded == commitment
    store.put("commitment", commitment)
    assert legacy.exists()  # old record is never deleted (D8)
    assert store._schema_path("commitment", commitment.id).exists()


def test_time_travel_harness_rejects_every_write_and_changes_no_bytes(tmp_path):
    root = tmp_path / "run"
    live = Harness(root)
    live.register_commitment(Commitment(id="k", eval="predicate:True"))
    live.register_problem(_problem())
    live.create_artifact("claim", provenance=Provenance(role="seed"))
    past = Harness.at(root, 1)
    before = _tree_digest(root)

    with pytest.raises(ReadOnlyHarnessError, match="read-only"):
        past.create_artifact("forbidden", provenance=Provenance(role="seed"))
    with pytest.raises(ReadOnlyHarnessError, match="read-only"):
        past.record_measure(inputs=["forbidden"])
    with pytest.raises(RuntimeError, match="read-only"):
        past.blobs.put(b"forbidden")
    with pytest.raises(RuntimeError, match="read-only"):
        past.objects.put("commitment", Commitment(id="other", eval="predicate:True"))
    with pytest.raises(RuntimeError, match="read-only"):
        past.log.append(list(live.log.read())[0])
    with pytest.raises(ReadOnlyHarnessError, match="read-only"):
        merge(past, root)

    assert _tree_digest(root) == before


def test_time_travel_does_not_create_or_repair_storage(tmp_path):
    missing = tmp_path / "missing"
    with pytest.raises(FileNotFoundError):
        Harness.at(missing, 0)
    assert not missing.exists()

    root = tmp_path / "run"
    harness = Harness(root)
    harness.create_artifact("durable", provenance=Provenance(role="seed"))
    with open(harness.log.path, "a", encoding="utf-8") as stream:
        stream.write('{"seq":1,"rule":"Meas')
    before = harness.log.path.read_bytes()
    with pytest.warns(UserWarning, match="dropping torn final line"):
        Harness.at(root, 1)
    assert harness.log.path.read_bytes() == before


def test_replay_verification_does_not_repair_a_torn_tail(tmp_path):
    root = tmp_path / "verify-read-only"
    harness = Harness(root)
    harness.create_artifact("durable", provenance=Provenance(role="seed"))
    with open(harness.log.path, "a", encoding="utf-8") as stream:
        stream.write('{"seq":1,"rule":"Meas')
    before = harness.log.path.read_bytes()

    with pytest.warns(UserWarning, match="dropping torn final line"):
        verify_root(root)

    assert harness.log.path.read_bytes() == before


@pytest.mark.parametrize("bad_seq", [0, 3])
def test_replay_rejects_duplicate_or_gapped_event_sequence(tmp_path, bad_seq):
    root = tmp_path / "run"
    harness = Harness(root)
    harness.create_artifact("a", provenance=Provenance(role="seed"))
    harness.create_artifact("b", provenance=Provenance(role="seed"))
    records = [json.loads(line) for line in harness.log.path.read_text().splitlines()]
    records[1]["seq"] = bad_seq
    harness.log.path.write_text(
        "".join(json.dumps(record, separators=(",", ":")) + "\n" for record in records)
    )

    with pytest.raises(EventSequenceError, match="expected 1"):
        Harness(root)


def test_failed_append_rolls_live_state_back_to_durable_log(tmp_path):
    root = tmp_path / "run"
    first, stale = Harness(root), Harness(root)
    durable = first.create_artifact("durable", provenance=Provenance(role="seed"))

    with pytest.raises(Exception):
        stale.create_artifact("must roll back", provenance=Provenance(role="seed"))

    reopened = Harness(root)
    assert stale.state == reopened.state
    assert set(stale.state.artifacts) == {durable.id}
    assert stale._next_seq == 1


def test_event_log_rejects_wrong_seq_before_append(tmp_path):
    harness = Harness(tmp_path / "run")
    event = harness._commit(Rule.MEASURE, inputs=["ok"], outputs=[])
    wrong = event.model_copy(update={"seq": 7})

    with pytest.raises(EventSequenceError, match="expected 1"):
        harness.log.append(wrong)
