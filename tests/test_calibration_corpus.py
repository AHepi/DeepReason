"""Tests for the court-calibration matched-pair corpus builder."""

import copy
import json
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
BUILDER = REPO_ROOT / "scripts" / "court_calibration_corpus.py"
OUTPUT = REPO_ROOT / "experiments" / "court_calibration_items" / "pairs_v1.json"

DEFECT_CLASSES = [
    "chronology-error",
    "unsupported-comparison",
    "scope-contradiction",
    "vacuous-forbidden-case",
    "evidence-misquotation",
    "causal-non-sequitur",
]

# One hand-checked pair per defect class: pair_id and the changed field only.
HAND_CHECKED = [
    ("cal-01", "chronology-error", "mechanism"),
    ("cal-02", "unsupported-comparison", "mechanism"),
    ("cal-03", "scope-contradiction", "scope"),
    ("cal-04", "vacuous-forbidden-case", "forbidden"),
    ("cal-05", "evidence-misquotation", "prose_notes"),
    ("cal-06", "causal-non-sequitur", "mechanism"),
]


def run_builder():
    subprocess.run(
        [sys.executable, str(BUILDER)], check=True, cwd=REPO_ROOT, capture_output=True
    )
    return OUTPUT.read_bytes()


@pytest.fixture(scope="module")
def corpus_bytes():
    return run_builder()


@pytest.fixture(scope="module")
def pairs(corpus_bytes):
    return json.loads(corpus_bytes)


def test_rerun_is_byte_identical(corpus_bytes):
    assert run_builder() == corpus_bytes


def test_class_balance(pairs):
    assert len(pairs) == 42
    counts = {}
    for pair in pairs:
        counts[pair["defect_class"]] = counts.get(pair["defect_class"], 0) + 1
    assert counts == {name: 7 for name in DEFECT_CLASSES}


def test_pair_ids_ordered_and_classes_cycle(pairs):
    for index, pair in enumerate(pairs):
        assert pair["pair_id"] == "cal-%02d" % (index + 1)
        assert pair["defect_class"] == DEFECT_CLASSES[index % 6]


@pytest.mark.parametrize("pair_id,defect_class,changed_field", HAND_CHECKED)
def test_single_mutation_property(pairs, pair_id, defect_class, changed_field):
    pair = next(p for p in pairs if p["pair_id"] == pair_id)
    assert pair["defect_class"] == defect_class

    clean = json.loads(pair["clean"])
    corrupted = json.loads(pair["corrupted"])
    assert pair["corrupted"] != pair["clean"]

    # Exactly one top-level field differs, and it is the expected one.
    assert set(clean) == set(corrupted)
    diff = [key for key in clean if clean[key] != corrupted[key]]
    assert diff == [changed_field]

    # The change is a pure extension or a targeted replacement: restoring
    # the clean value of the changed field makes the twins equal again.
    restored = copy.deepcopy(corrupted)
    restored[changed_field] = clean[changed_field]
    assert restored == clean

    if changed_field == "scope":
        sub_diff = [
            key for key in clean["scope"] if clean["scope"][key] != corrupted["scope"][key]
        ]
        assert sub_diff == ["excludes"]
        assert (
            corrupted["scope"]["excludes"]
            == clean["scope"]["excludes"] + [clean["scope"]["covers"][0]]
        )
    elif changed_field == "forbidden":
        assert corrupted["forbidden"][1:] == clean["forbidden"][1:]
        entry_diff = [
            key
            for key in clean["forbidden"][0]
            if clean["forbidden"][0][key] != corrupted["forbidden"][0][key]
        ]
        assert entry_diff == ["case"]
    else:
        # String-append mutations preserve the original text as a prefix.
        assert corrupted[changed_field].startswith(clean[changed_field])
        assert len(corrupted[changed_field]) > len(clean[changed_field])
