"""Experiment E placement report — determinism, unit hygiene, rate shape.

Guards scripts/experiment_e_placement.py and its committed output
experiments/results/glm_judge_v1_experiment_e_placement.json:

  * the script reruns byte-identically (deterministic, no timestamps);
  * every rate carries explicit numerator/denominator fields;
  * the three incompatible unit levels appear as separate sections and
    precision/recall keys always name their unit level;
  * the label-free court-cross section reports no precision/recall.
"""

import json
import re
import subprocess
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[1]
SCRIPT = REPO / "scripts/experiment_e_placement.py"
REPORT = REPO / "experiments/results/glm_judge_v1_experiment_e_placement.json"

RATE_KEY = re.compile(r"(rate|precision|recall|proportion)", re.IGNORECASE)
PR_KEY = re.compile(r"(precision|recall)", re.IGNORECASE)
UNIT_MARKERS = ("item_level", "candidate_level", "court_conviction_level")


@pytest.fixture(scope="module")
def report() -> dict:
    return json.loads(REPORT.read_text())


def _walk(node, path=()):
    """Yield (key_path_tuple, key, value) for every dict entry."""
    if isinstance(node, dict):
        for key, value in node.items():
            yield path + (key,), key, value
            yield from _walk(value, path + (key,))
    elif isinstance(node, list):
        for i, value in enumerate(node):
            yield from _walk(value, path + (str(i),))


def test_script_reruns_byte_identically(tmp_path):
    committed = REPORT.read_bytes()
    out1 = tmp_path / "run1.json"
    out2 = tmp_path / "run2.json"
    for out in (out1, out2):
        proc = subprocess.run(
            [sys.executable, str(SCRIPT), str(out)],
            capture_output=True, text=True, cwd=REPO)
        assert proc.returncode == 0, proc.stderr
    assert out1.read_bytes() == out2.read_bytes(), \
        "two reruns produced different bytes"
    assert out1.read_bytes() == committed, \
        "rerun output differs from committed report"


def test_every_rate_has_numerator_and_denominator(report):
    """Any dict-valued key that names a rate must be an explicit
    numerator/denominator/value triple (validation_context quotes
    candidate-level numbers that cannot be recomputed, so its parsed
    scalars are exempt by construction: they are plain floats under keys
    inside 'parsed_candidate_level_numbers', not dict-valued rates)."""
    checked = 0
    for key_path, key, value in _walk(report):
        if not RATE_KEY.search(key):
            continue
        if isinstance(value, dict):
            missing = {"numerator", "denominator", "value"} - set(value)
            assert not missing, \
                f"{'.'.join(key_path)} lacks fields {missing}"
            num, den = value["numerator"], value["denominator"]
            assert isinstance(num, int) and isinstance(den, int)
            if den:
                assert value["value"] == round(num / den, 6), \
                    f"{'.'.join(key_path)} value != numerator/denominator"
            checked += 1
    assert checked >= 20, f"only {checked} structured rates found"


def test_scalar_rate_keys_only_in_validation_context(report):
    """Outside validation_context (non-recomputable quoted aggregates),
    no rate-named key may be a bare number."""
    for key_path, key, value in _walk(report):
        if key_path[0] == "validation_context":
            continue
        if RATE_KEY.search(key) and isinstance(value, (int, float)):
            # allowed only inside a structured rate triple
            assert key in ("value",), \
                f"bare scalar rate at {'.'.join(key_path)}"


def test_three_unit_levels_are_separate_sections(report):
    for section in ("unit_glossary", "calibration_placement",
                    "bare_critic_placement", "court_cross_distributions",
                    "validation_context", "majority_language_caveat"):
        assert section in report, f"missing top-level section {section}"
    glossary = report["unit_glossary"]
    for level in ("candidate_level_flag", "item_level_objection",
                  "court_conviction"):
        assert level in glossary, f"unit level {level} missing from glossary"
        assert isinstance(glossary[level], str) and glossary[level]
    # each dataset section declares which unit levels it contains
    assert report["calibration_placement"]["unit_levels_present"] == \
        ["item_level_objection", "court_conviction"]
    assert report["bare_critic_placement"]["unit_levels_present"] == \
        ["item_level_objection"]
    assert report["validation_context"]["unit_level"] == \
        "candidate_level_flag"
    assert report["validation_context"]["recomputable_from_this_repo"] \
        is False


def test_precision_recall_keys_always_name_their_unit_level(report):
    for key_path, key, _value in _walk(report):
        if PR_KEY.search(key):
            assert any(m in key for m in UNIT_MARKERS), \
                f"precision/recall key without unit level: " \
                f"{'.'.join(key_path)}"


def test_court_cross_is_label_free(report):
    cross = report["court_cross_distributions"]
    assert cross["label_free"] is True
    for key_path, key, _value in _walk(cross):
        assert not PR_KEY.search(key), \
            f"precision/recall reported for unlabeled pool: " \
            f"{'.'.join(key_path)}"


def test_key_placement_numbers(report):
    cal = report["calibration_placement"]["placement"]
    assert cal["interventions_sustained_on_corrupted"]["numerator"] == 5
    assert cal["interventions_sustained_on_corrupted"]["denominator"] == 42
    assert cal["interventions_sustained_on_clean"]["numerator"] == 0
    assert cal["interventions_sustained_on_clean"]["denominator"] == 42
    assert cal["critic_right_but_court_vetoed"]["numerator"] == 37
    assert cal["critic_right_but_court_vetoed"]["denominator"] == 42
    assert cal["critic_wrong_but_court_prevented_damage"]["numerator"] == 42
    assert cal["critic_wrong_but_court_prevented_damage"]["denominator"] == 42
    bare = report["bare_critic_placement"]["placement"]
    assert bare["convictions_on_flawed"]["numerator"] == 40
    assert bare["convictions_on_flawed"]["denominator"] == 40
    assert bare["convictions_on_sound"]["numerator"] == 27
    assert bare["convictions_on_sound"]["denominator"] == 40


def test_majority_language_caveat_refuses_voting_vocabulary(report):
    caveat = report["majority_language_caveat"]
    assert "wrong_majorities_repaired" in caveat["not_computable_here"]
    assert "correct_majorities_broken" in caveat["not_computable_here"]
    analogues = caveat["closest_computable_analogues"]
    assert "planted_defects_convicted" in analogues
    assert "clean_items_convicted" in analogues
