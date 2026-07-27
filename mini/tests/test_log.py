"""M0 — log: replay determinism, seq discipline, torn writes, and the
subset reader over freshly generated parent roots (the plan's committed-
root fixture, regenerated: runs/ is gitignored in the parent repo)."""

import pytest

from minireason.log import Event, EventLog, SeqError, replay
from minireason.loop import Session


def _seeded(tmp_path):
    s = Session(tmp_path / "run")
    s.spawn_problem("pi-0", "why did X happen?")
    commitment_ids = s.register_commitments(
        [{"id": "skeleton-wf", "eval": "program:skeleton_wf",
          "observation_valued": False, "budget": {"extra": {}}}]
    )
    artifact = s.build_candidate(
        '{"claim": "c", "mechanism": "m"}', commitment_ids, "mechanist"
    )
    s.register_candidates(
        [(artifact, [])], "pi-0", None
    )
    return s


def test_replay_is_deterministic_and_pure(tmp_path):
    s = _seeded(tmp_path)
    live = s.state.digest()
    assert replay(tmp_path / "run").digest() == live
    assert replay(tmp_path / "run").digest() == replay(tmp_path / "run").digest()
    # Reopening a session replays to the same state (state == f(log)).
    assert Session(tmp_path / "run").state.digest() == live


def test_seq_must_be_consecutive(tmp_path):
    log = EventLog(tmp_path / "log.jsonl")
    log.append(Event(seq=0, ts="t", rule="Measure"))
    with pytest.raises(SeqError):
        log.append(Event(seq=2, ts="t", rule="Measure"))
    with pytest.raises(ValueError):
        Event(seq=1, ts="t", rule="NotARule")


def test_torn_final_line_dropped_with_warning(tmp_path):
    log = EventLog(tmp_path / "log.jsonl")
    log.append(Event(seq=0, ts="t", rule="Measure", inputs=["ok"]))
    with open(tmp_path / "log.jsonl", "a") as f:
        f.write('{"seq": 1, "rule":')  # crash mid-append
    with pytest.warns(UserWarning, match="torn final line"):
        events = list(EventLog(tmp_path / "log.jsonl").read())
    assert [e.seq for e in events] == [0]


def test_bad_interior_line_raises(tmp_path):
    log = EventLog(tmp_path / "log.jsonl")
    log.append(Event(seq=0, ts="t", rule="Measure"))
    with open(tmp_path / "log.jsonl", "a") as f:
        f.write("garbage\n")
    log2 = EventLog.__new__(EventLog)
    log2.path = tmp_path / "log.jsonl"
    with open(tmp_path / "log.jsonl", "a") as f:
        f.write(Event(seq=2, ts="t", rule="Measure").model_dump_json() + "\n")
    with pytest.raises(Exception):
        list(log2.read())


def test_subset_reader_parses_parent_roots(tmp_path):
    """G6, read direction: the mini replay ingests parent-generated roots."""
    deepreason = pytest.importorskip("deepreason.harness")
    from deepreason.ontology import Provenance, Warrant, WarrantType

    # Root 1: plain conjectures + a problem.
    h1 = deepreason.Harness(tmp_path / "p1")
    from deepreason.ontology import Problem
    from deepreason.ontology.problem import ProblemProvenance, SpawnTrigger

    h1.register_problem(Problem(id="pi-x", description="d",
                                provenance=ProblemProvenance(trigger=SpawnTrigger.SEED)))
    a = h1.create_artifact("first claim", provenance=Provenance(role="conjecturer"),
                           problem_id="pi-x", )
    h1.create_artifact("second claim", provenance=Provenance(role="conjecturer"))
    state1 = replay(tmp_path / "p1")
    assert set(state1.problems) == {"pi-x"}
    assert len(state1.artifacts) == 2
    assert (a.id, "pi-x") in state1.addr
    assert state1.refuted == set()

    # Root 2: an attack — the mini reader must see the refutation.
    h2 = deepreason.Harness(tmp_path / "p2")
    target = h2.create_artifact("doomed claim", provenance=Provenance(role="conjecturer"))
    nu = h2.create_artifact("nu: the attack is sound", provenance=Provenance(role="critic"))
    h2.create_artifact(
        "critic: it fails", provenance=Provenance(role="critic"),
        warrants=[Warrant(id="w-1", target=target.id, type=WarrantType.ARGUMENTATIVE,
                          validity_node=nu.id)])
    state2 = replay(tmp_path / "p2")
    assert state2.refuted == {target.id}
    assert state2.status(target.id) == "refuted-by-check"
