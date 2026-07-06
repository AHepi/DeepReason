"""narrate(): the log as deterministic chain-of-thought prose (spec §8 view)."""

import re

from deepreason.harness import Harness
from deepreason.views.narrate import narrate
from tests.conftest import art, attack
from tests.test_replay import build_scenario


def test_narration_is_deterministic_and_covers_transitions(tmp_path):
    root = tmp_path / "run"
    live, ids, _ = build_scenario(root)
    out = narrate(live)
    assert out == narrate(live)  # same log, same words
    assert out == narrate(Harness(root))  # reopened harness narrates identically

    low = out.lower()
    # The refute -> reinstate arc is told with connectors.
    assert "attacked" in low and "refuted" in low
    assert "reinstated" in low
    assert any(w in low for w in ("but ", "so ", "however", "and ", "maybe", "yet ")), out
    # Every transition's id-prefix appears.
    for seq, aid, old, new in live.transitions():
        if old is not None:
            assert aid[:12] in out


def test_narration_is_readable_not_hashes(tmp_path):
    live, _, _ = build_scenario(tmp_path / "run")
    out = narrate(live)
    assert re.search(r"[0-9a-f]{16,}", out) is None  # no raw sha256 dumps


def test_noise_tags_collapse_to_one_aside(tmp_path):
    h = Harness(tmp_path / "run")
    a = art(h, "a claim under deliberation")
    for _ in range(10):
        h.record_measure(inputs=["trial-llm"])
    attack(h, a.id, "counterattack")
    out = narrate(h)
    assert out.count("deliberation") == 1  # ten measures, ONE aside
    assert "10 exchanges" in out


def test_blocked_and_gate_measures_render(tmp_path):
    h = Harness(tmp_path / "run")
    art(h, "some work under trial")
    h.record_measure(inputs=["trial-blocked:ensemble-split", "t1"])
    h.record_measure(inputs=["gate:battery-equivalent (~=_B) to refuted abc", "x", "pi"])
    out = narrate(h).lower()
    assert "judges disagreed" in out
    assert "gate blocked" in out


def test_upto_seq_prefix_narration(tmp_path):
    root = tmp_path / "run"
    live, ids, _ = build_scenario(root)
    critic_seq = next(e.seq for e in live.log.read() if ids["critic"] in e.outputs)
    partial = narrate(live, upto_seq=critic_seq)
    assert "reinstated" not in partial.lower()  # the reinstatement hasn't happened yet
    assert "refuted" in partial.lower()
