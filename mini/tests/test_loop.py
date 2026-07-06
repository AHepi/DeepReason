"""M2 — the driver: healthy runs stay orbit-free, orbiting runs rotate,
schema storms and budget death never lose spend (meter == log, G1), and a
run's state replays byte-for-byte (G2)."""

import json

from minireason.call import MockEndpoint
from minireason.log import replay
from minireason.loop import Session, run


def _skeleton(i: int, extra: str = "") -> str:
    return json.dumps({
        "claim": f"claim {i}{extra}", "mechanism": f"mechanism {i}",
        "forbidden": [{"case": "must state a mechanism",
                       "eval": "predicate:'mechanism' in content"}]})


def _conj(*contents: str) -> str:
    return json.dumps({"candidates": [
        {"content": c, "typicality": 0.5} for c in contents]})


def test_healthy_run_no_orbit_and_replayable(tmp_path):
    calls = {"n": 0}

    def endpoint_fn(prompt):
        calls["n"] += 1
        i = calls["n"]
        if i <= 3:
            return _conj(_skeleton(2 * i), _skeleton(2 * i + 1))
        return _conj(_skeleton(2), _skeleton(3))  # repeats: dry, not orbiting

    root = tmp_path / "run"
    summary = run([("pi-0", "why?")], MockEndpoint(endpoint_fn),
                  budget=200_000, root=root, vs_k=2, turnover_k=3, orbit_floor=3)
    assert summary["stop"] == "queue-exhausted"
    assert summary["problems"] == {"pi-0": 6}
    assert summary["refuted"] == 0
    assert summary["gate_blocks"] == 0  # healthy arms: zero blocks EVER
    assert summary["meter_equals_log"]
    session = Session(root)
    assert replay(root).digest() == session.state.digest()


def test_orbiting_run_blocks_and_rotates(tmp_path):
    doomed = json.dumps({
        "claim": "doomed", "mechanism": "wrong",
        "forbidden": [{"case": "must mention the striped animal",
                       "eval": "predicate:'ze'+'bra' in content"}]})

    summary = run([("pi-0", "why?")], MockEndpoint(lambda p: _conj(doomed)),
                  budget=200_000, root=tmp_path / "run", vs_k=1,
                  turnover_k=6, orbit_floor=3, stance_decay=50)
    assert summary["refuted"] == 1  # registered once, refuted by its own check
    assert summary["gate_blocks"] >= 3  # every re-proposal refused
    assert summary["rotations"] >= 1  # orbit named the stance; it rotated
    assert summary["problems"] == {"pi-0": 0}
    assert summary["meter_equals_log"]
    events = Session(tmp_path / "run").state.events
    assert any("intervention:reseed" in e.inputs for e in events)
    # The rotation was orbit-triggered, not decay-triggered (decay is 50).
    assert any(i.startswith("orbit:") for e in events for i in e.inputs)


def test_schema_storm_logs_dropped_spend(tmp_path):
    summary = run([("pi-0", "why?")], MockEndpoint(lambda p: "never json"),
                  budget=200_000, root=tmp_path / "run", turnover_k=2)
    assert summary["stop"] == "queue-exhausted"
    assert summary["meter_equals_log"]
    assert summary["tokens"]["total"] > 0  # storms cost real tokens...
    events = Session(tmp_path / "run").state.events
    dropped = [e for e in events if "dropped-call" in e.inputs]
    assert dropped and all(e.llm is not None for e in dropped)  # ...and land on the log


def test_budget_death_is_a_logged_stop(tmp_path):
    def endpoint_fn(prompt):
        return _conj(_skeleton(len(prompt) % 97))

    summary = run([("pi-0", "why?"), ("pi-1", "how?")],
                  MockEndpoint(endpoint_fn), budget=300, root=tmp_path / "run")
    assert summary["stop"] == "budget"
    assert summary["meter_equals_log"]
    assert summary["tokens"]["total"] >= 300  # documented overshoot semantics


def test_turnover_advances_the_queue(tmp_path):
    def endpoint_fn(prompt):
        # One fixed survivor per problem, then repeats: each problem goes
        # dry and the queue advances (never loop a dry problem).
        marker = "how?" if "how?" in prompt else "why?"
        return _conj(_skeleton(hash(marker) % 100, marker))

    summary = run([("pi-0", "why?"), ("pi-1", "how?")],
                  MockEndpoint(endpoint_fn), budget=200_000,
                  root=tmp_path / "run", turnover_k=2)
    assert summary["stop"] == "queue-exhausted"
    assert set(summary["problems"]) == {"pi-0", "pi-1"}
    assert all(n == 1 for n in summary["problems"].values())
    events = Session(tmp_path / "run").state.events
    turnovers = [e for e in events if "intervention:turnover" in e.inputs]
    assert len(turnovers) == 2


def test_stance_decay_rotates_without_orbit(tmp_path):
    calls = {"n": 0}

    def endpoint_fn(prompt):
        calls["n"] += 1
        return _conj(_skeleton(calls["n"]))

    summary = run([("pi-0", "why?")], MockEndpoint(endpoint_fn),
                  budget=200_000, root=tmp_path / "run",
                  stance_decay=2, turnover_k=3, max_cycles=8)
    assert summary["gate_blocks"] == 0
    assert summary["rotations"] >= 2  # decay LOW (fast rotation measured best)
    assert summary["meter_equals_log"]
