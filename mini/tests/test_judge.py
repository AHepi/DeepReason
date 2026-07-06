"""M3 — the instrument: rerunning the parent's committed report inputs
reproduces every score byte-for-byte, and the control gate voids runs
where the instrument cannot see a constructed-worse artifact."""

import json
from pathlib import Path

import pytest

from minireason import judge
from minireason.call import MockEndpoint, TokenMeter
from minireason.log import BlobStore

RESULTS = Path(__file__).resolve().parents[2] / "experiments" / "results"
REPORTS = sorted(RESULTS.glob("informal_ab_instrument_report*.json"))


@pytest.mark.parametrize("path", REPORTS, ids=lambda p: p.stem)
def test_committed_reports_rescore_byte_identical(path):
    report = json.loads(path.read_text())
    assert report["pairs"], path
    for pair in report["pairs"]:
        for row in pair["seats"].values():
            if "orders" not in row:
                continue  # an errored seat abstained; nothing to recompute
            got = judge.score_orders(row["orders"][0], row["orders"][1],
                                     pair["len_x"], pair["len_y"])
            assert got["raw"] == row["raw"]
            assert got["adjusted"] == row["adjusted"]
            assert got["order_disagreement"] == row["order_disagreement"]
        margin, point = judge.aggregate(pair["seats"])
        assert margin == pair["margin"]
        assert point == pair["point"]
        assert round(judge.verbosity_penalty(pair["len_x"], pair["len_y"]), 4) == \
            pair["verbosity_penalty"]
    control = report["control_pair"]
    gate_pass = control["margin"] is not None and control["margin"] >= judge.CONTROL_GATE
    assert gate_pass == report["instrument_valid"]
    # The degraded control is deterministic: same source, same bytes.
    # (The first republic report predates the solo_top3 key.)
    solo_top = report.get("solo_top3")
    if solo_top and control["len_x"] == len(solo_top[0]):
        assert control["len_y"] == len(judge.degrade(solo_top[0]))


def test_degrade_is_deterministic_and_rubric_violating():
    text = "a" * 200
    assert judge.degrade(text) == judge.degrade(text)
    assert judge.degrade(text).startswith("a" * 110)
    assert judge.DEGRADE_SENTENCE in judge.degrade(text)


def test_verbosity_penalty_formula():
    assert judge.verbosity_penalty(100, 100) == 0.0
    assert judge.verbosity_penalty(0, 50) == 0.0
    assert judge.verbosity_penalty(100, 150) == pytest.approx(0.05)
    assert judge.verbosity_penalty(100, 1000) == 0.3  # clamped


def _discriminating_seat():
    """A seat that spots the degraded side and ties everything else —
    exactly what a working instrument must do to pass the control gate."""

    def fn(prompt):
        a = prompt.split("CANDIDATE A:\n", 1)[1].split("\n\nCANDIDATE B:", 1)[0]
        b = prompt.split("CANDIDATE B:\n", 1)[1].split("\n\nQUESTION:", 1)[0]
        if judge.DEGRADE_SENTENCE in a:
            winner = "B"
        elif judge.DEGRADE_SENTENCE in b:
            winner = "A"
        else:
            winner = "tie"
        return json.dumps({name: winner for name, _ in judge.CRITERIA})

    return MockEndpoint(fn)


def test_score_run_control_gate_pass(tmp_path):
    pairs = [(f"rank{i}", f"harness text {i} " * 30, f"solo text {i} " * 30)
             for i in range(3)]
    out = judge.score_run({"seat-a": _discriminating_seat()}, pairs, "rubric",
                          TokenMeter(budget=10**6), BlobStore(tmp_path))
    assert out["instrument_valid"]
    # Raw sweep is +1; the undegraded side is longer, so the verbosity
    # penalty shaves the margin — it must still clear the gate easily.
    assert out["control_pair"]["margin"] > 0.9
    assert out["verdict"] == "inconclusive"  # all real pairs tie
    assert out["pair_points"] == {"harness": 0, "solo": 0, "tie": 3}


def test_score_run_blind_instrument_is_void(tmp_path):
    blind = MockEndpoint(lambda p: json.dumps(
        {name: "tie" for name, _ in judge.CRITERIA}))
    pairs = [("rank0", "x " * 40, "y " * 40)]
    out = judge.score_run({"seat-a": blind}, pairs, "rubric",
                          TokenMeter(budget=10**6), BlobStore(tmp_path))
    assert not out["instrument_valid"]
    assert out["verdict"] == "instrument_failed_control_gate"


def test_erroring_seat_abstains_without_killing_the_panel(tmp_path):
    seats = {"dead": MockEndpoint(lambda p: "never json"),
             "alive": _discriminating_seat()}
    row = judge.score_pair(seats, "x " * 40, "y " * 40 + judge.DEGRADE_SENTENCE,
                           "rubric", TokenMeter(budget=10**6), BlobStore(tmp_path))
    assert "error" in row["seats"]["dead"]
    assert row["seats"]["alive"]["adjusted"] is not None
    assert row["margin"] is not None


def test_certify_seat_planted_flaws(tmp_path):
    def oracle_fn(prompt):
        text = prompt.split("ARGUMENT:\n", 1)[1].split("\n\nQUESTION", 1)[0]
        flawed = dict(judge.PLANTED)[text]
        return json.dumps({"violates": flawed})

    good = judge.certify_seat(MockEndpoint(oracle_fn), TokenMeter(), BlobStore(tmp_path))
    assert good == {"planted_flaw_error_rate": 0.0, "n": 12, "passes": True}

    paranoid = judge.certify_seat(
        MockEndpoint(lambda p: json.dumps({"violates": True})),
        TokenMeter(), BlobStore(tmp_path))
    assert paranoid["planted_flaw_error_rate"] == 0.5
    assert not paranoid["passes"]
