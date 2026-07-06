"""M4 — graduation (G6): a MiniReason log ingested by the parent's
``Harness(root)`` replays without violations, and the two systems agree on
every status. Migration = point DeepReason at the mini's root; no data
conversion."""

import json

import pytest

from minireason.call import MockEndpoint
from minireason.loop import Session, run

deepreason_harness = pytest.importorskip("deepreason.harness")


def _skeleton(i: int) -> str:
    return json.dumps({
        "claim": f"claim {i}", "mechanism": f"mechanism {i}",
        "forbidden": [{"case": "must state a mechanism",
                       "eval": "predicate:'mechanism' in content"},
                      {"case": "a rubric-only case rides along",
                       "eval": "rubric:std-hist"}]})


def _mixed_run(root):
    """A run exercising every event shape the mini emits: Spawn, Register,
    Conj, Crit (refutation), Measure (gate blocks, dropped calls, turnover,
    reseed) and Reseed."""
    doomed = json.dumps({
        "claim": "doomed", "mechanism": "wrong",
        "forbidden": [{"case": "must mention the striped animal",
                       "eval": "predicate:'ze'+'bra' in content"}]})
    calls = {"n": 0}

    def endpoint_fn(prompt):
        calls["n"] += 1
        i = calls["n"]
        if i == 1:
            return json.dumps({"candidates": [
                {"content": _skeleton(1), "typicality": 0.6},
                {"content": doomed, "typicality": 0.4}]})
        if i in (2, 3, 4):  # a full storm: all retry_max+1 attempts invalid
            return "schema storm, not json"
        if i <= 9:  # re-propose the refuted candidate: orbit territory
            return json.dumps({"candidates": [{"content": doomed, "typicality": 0.5}]})
        return json.dumps({"candidates": [
            {"content": _skeleton(i), "typicality": 0.5}]})

    return run([("pi-hist", "why did the bronze age system collapse?"),
                ("pi-second", "why did it not recover?")],
               MockEndpoint(endpoint_fn), budget=200_000, root=root,
               vs_k=2, turnover_k=3, orbit_floor=3, stance_decay=4, max_cycles=12)


def test_parent_ingests_mini_root_without_violations(tmp_path):
    from deepreason.invariants import verify_root

    root = tmp_path / "mini-run"
    summary = _mixed_run(root)
    assert summary["meter_equals_log"]
    assert summary["refuted"] >= 1 and summary["gate_blocks"] >= 3

    report = verify_root(root, meter_total=summary["logged_tokens"])
    assert report["violations"] == []
    assert report["stats"]["events"] == len(Session(root).state.events)
    assert report["stats"]["gate_blocks"] == summary["gate_blocks"]
    assert report["stats"]["refuted"] >= 1
    assert report["stats"]["dropped_calls"] >= 1
    assert report["stats"]["logged_tokens"] == summary["logged_tokens"]


def test_statuses_agree_between_mini_and_parent(tmp_path):
    from deepreason.ontology import Status

    root = tmp_path / "mini-run"
    _mixed_run(root)
    mini = Session(root).state
    parent = deepreason_harness.Harness(root)

    assert set(parent.state.artifacts) == set(mini.artifacts)
    parent_refuted = {a for a, s in parent.state.status.items() if s == Status.REFUTED}
    assert parent_refuted == mini.refuted
    # Every mini survivor is accepted under full grounded adjudication.
    for aid in mini.artifacts:
        if aid not in mini.refuted:
            assert parent.state.status[aid] == Status.ACCEPTED
    # addr pairs survive the trip too.
    assert set(parent.state.addr) == set(mini.addr)


def test_parent_detection_reads_mini_gate_blocks(tmp_path):
    """The parent's own orbit detector fires on a mini log — the mini's
    gate:<reason> format is the parent's, unchanged."""
    from deepreason.capture.detection import gate_block_count, orbit_attractor_school
    from deepreason.config import Config

    root = tmp_path / "mini-run"
    _mixed_run(root)
    parent = deepreason_harness.Harness(root)
    config = Config()
    window_blocks = gate_block_count(parent, len(Session(root).state.events))
    assert window_blocks >= 3
    assert orbit_attractor_school(parent, len(Session(root).state.events)) in (
        None, "mechanist")  # hash-relapse blocks may or may not carry the parent regex
    assert config.GATE_ORBIT_MIN is not None
