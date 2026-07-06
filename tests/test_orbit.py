"""Refuted-attractor orbiting detector + ladder response (basin study,
docs/BASIN_REPORT.md). The signal is gate-block rate: exactly 0 in every
healthy committed root, ~7-14 per 20-event window in the two orbiting
arms. The response is stance rotation — the antidote the live battery
measured working (fast decay beat permanence on novelty AND separation)."""

import json

from deepreason.capture.detection import (
    gate_block_count,
    orbit_attractor_school,
    raw_flags,
)
from deepreason.capture.ladder import respond
from deepreason.capture.schools import roster
from deepreason.config import Config
from deepreason.harness import Harness
from deepreason.llm.adapter import LLMAdapter
from deepreason.llm.embedder import HashingEmbedder
from deepreason.llm.endpoints import MockEndpoint
from deepreason.ontology import Commitment, Problem, ProblemProvenance, Provenance
from deepreason.scheduler.scheduler import Scheduler


def _seed(h):
    h.register_commitment(
        Commitment(id="k-x", eval="predicate:'x' in content"))
    h.register_problem(Problem(
        id="pi-o", description="a problem", criteria=["k-x"],
        provenance=ProblemProvenance.model_validate({"trigger": "seed", "from": []})))


def _orbit(h, school="school-0", blocks=6):
    """Reproduce the live signature: a refuted artifact + a stream of
    gate measures naming it (the exact strings conj.py records)."""
    from tests.conftest import attack

    a = h.create_artifact("the attractor x", problem_id="pi-o",
                          provenance=Provenance(role="conjecturer", school=school))
    attack(h, a.id, "kills it")
    for _ in range(blocks):
        h.record_measure(inputs=[
            f"gate:battery-equivalent (~=_B) to refuted {a.id[:12]}",
            a.id, "pi-o"])
    return a


def test_orbit_flag_fires_and_names_the_school(tmp_path):
    h = Harness(tmp_path / "run")
    _seed(h)
    _orbit(h, school="school-1", blocks=6)
    cfg = Config()
    assert gate_block_count(h, cfg.CAPTURE_W) >= 6
    flags = raw_flags(h, HashingEmbedder(), cfg)
    assert flags["attractor_orbiting"] is True
    assert orbit_attractor_school(h, cfg.CAPTURE_W) == "school-1"


def test_orbit_flag_silent_on_healthy_run(tmp_path):
    h = Harness(tmp_path / "run")
    _seed(h)
    for i in range(10):
        h.create_artifact(f"healthy candidate x{i}", problem_id="pi-o")
    flags = raw_flags(h, HashingEmbedder(), Config())
    assert flags["attractor_orbiting"] is False


def test_orbit_flag_respects_disable_knob(tmp_path):
    h = Harness(tmp_path / "run")
    _seed(h)
    _orbit(h, blocks=8)
    flags = raw_flags(h, HashingEmbedder(), Config(GATE_ORBIT_MIN=None))
    assert flags["attractor_orbiting"] is False


def test_ladder_rotates_the_orbiting_school(tmp_path):
    h = Harness(tmp_path / "run")
    _seed(h)
    adapter = LLMAdapter(
        {"conjecturer": MockEndpoint(lambda p: json.dumps({"candidates": [
            {"content": "x", "typicality": 0.5}]}))}, h.blobs, retry_max=1)
    scheduler = Scheduler(h, adapter, Config(N_SCHOOLS=2, FLOOR=0))
    before = {s: p["stance"] for s, p in roster(h).items()}
    _orbit(h, school="school-0", blocks=6)

    applied = respond(scheduler, {"attractor_orbiting": True})

    assert any(a.startswith("orbit-reseed:school-0") for a in applied), applied
    after = roster(h)
    assert after["school-0"]["stance"] != before["school-0"]  # rotated
    assert after["school-1"]["stance"] == before["school-1"]  # untouched
    # The live pack roster the scheduler renders from is refreshed too
    # (a reseed the packs never see is a logged no-op).
    assert scheduler.schools["school-0"]["stance"] == after["school-0"]["stance"]
