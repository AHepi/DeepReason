"""M1 — gate: refuted-relapse blocking, normalized equivalence, and the
orbit detector's measured signature (healthy: zero blocks ever; orbiting:
above-floor block rate with school attribution)."""

from minireason import gate
from minireason.checks import compile_checks
from minireason.log import artifact_id
from minireason.loop import Session

BAD = '{"claim": "c", "mechanism": "m", "forbidden": []}'  # refuted on arrival


def _register(session, content, stance="mechanist", pid="pi-0"):
    cks = compile_checks(content)
    aid = artifact_id(f"inline:{content}", "utf8",
                      {"commitments": [c["id"] for c in cks], "refs": []})
    for c in cks:
        session.register_commitments([c])
    session.register_candidates([(aid, content, cks)], pid, stance, None)
    return aid, cks


def _refuted_session(tmp_path):
    s = Session(tmp_path / "run")
    s.spawn_problem("pi-0", "d")
    aid, _ = _register(s, BAD)
    s.refute(aid, [{"commitment": "skeleton-wf", "eval": "program:skeleton_wf",
                    "verdict": "fail"}])
    assert s.state.refuted == {aid}
    return s, aid


def test_hash_relapse_blocked(tmp_path):
    s, aid = _refuted_session(tmp_path)
    ok, reason = gate.check(aid, BAD, s.state)
    assert not ok and reason.startswith("hash:") and aid[:12] in reason


def test_normalized_equivalence_blocks_paraphrase_order(tmp_path):
    s, aid = _refuted_session(tmp_path)
    # Same token set, different bytes => different hash, same equivalence class.
    shuffled = '{"mechanism": "m", "claim": "c", "forbidden": []}'
    other_id = "f" * 64
    ok, reason = gate.check(other_id, shuffled, s.state)
    assert not ok and "to refuted" in reason and aid[:12] in reason


def test_genuinely_new_content_admitted(tmp_path):
    s, _ = _refuted_session(tmp_path)
    ok, reason = gate.check("e" * 64, '{"claim": "entirely new", "mechanism": "different"}',
                            s.state)
    assert ok and reason == "admitted"


def test_live_duplicates_are_never_gated(tmp_path):
    s = Session(tmp_path / "run")
    s.spawn_problem("pi-0", "d")
    good = '{"claim": "c", "mechanism": "m", "forbidden": [{"case": "x", "eval": "rubric:std"}]}'
    aid, _ = _register(s, good)
    ok, _ = gate.check(aid, good, s.state)
    assert ok  # dedupe is the caller's job; the gate only blocks relapse


def test_orbit_healthy_never_fires(tmp_path):
    s = Session(tmp_path / "run")
    s.spawn_problem("pi-0", "d")
    for i in range(30):
        _register(s, f'{{"claim": "c{i}", "mechanism": "m{i}"}}')
    assert gate.gate_blocks(s.state.events, 20) == []
    assert gate.orbit(s.state.events, s.state.artifacts) is None


def test_orbit_fires_at_floor_and_names_the_school(tmp_path):
    s, aid = _refuted_session(tmp_path)
    for _ in range(5):  # the measured orbiting arms logged 7-14 per window
        ok, reason = gate.check(aid, BAD, s.state)
        assert not ok
        s.measure([f"gate:{reason}"])
    assert len(gate.gate_blocks(s.state.events, 20)) == 5
    assert gate.orbit(s.state.events, s.state.artifacts, window=20, floor=5) == "mechanist"
    # One block below the floor: silent.
    assert gate.orbit(s.state.events, s.state.artifacts, window=20, floor=6) is None
    # Outside the window: silent again (rate, not lifetime count).
    for _ in range(25):
        s.measure(["padding"])
    assert gate.orbit(s.state.events, s.state.artifacts, window=20, floor=5) is None
