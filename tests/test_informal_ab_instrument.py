"""Deterministic mechanics of the instrument-stage scorer (prereg
amendment 2, design aac313a1af55). The live seats are not exercised here —
only the pieces whose behavior the prereg pins exactly: the control-pair
degradation, the verbosity handicap, and the criterion-choice contract."""

import sys
from pathlib import Path

import pytest
from pydantic import ValidationError

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from informal_ab import (  # noqa: E402
    CRITERIA,
    DEGRADE_SENTENCE,
    CriterionChoices,
    _degrade,
    _verbosity_penalty,
)


def test_degradation_is_deterministic_and_rubric_violating():
    text = "x" * 1000
    d1, d2 = _degrade(text), _degrade(text)
    assert d1 == d2
    assert d1.startswith("x" * 550)
    assert d1.endswith(DEGRADE_SENTENCE)
    assert "unknowable" in d1  # the planted unfalsifiability violation


def test_verbosity_penalty_formula():
    assert _verbosity_penalty(100, 100) == 0.0
    assert _verbosity_penalty(0, 100) == 0.0  # degenerate: no ratio
    assert _verbosity_penalty(200, 100) == pytest.approx(0.1)
    assert _verbosity_penalty(100, 200) == pytest.approx(0.1)  # symmetric
    assert _verbosity_penalty(100, 1000) == 0.3  # capped


def test_contract_forces_all_five_criteria():
    fields = set(CriterionChoices.model_fields)
    assert fields == {name for name, _ in CRITERIA}
    with pytest.raises(ValidationError):
        CriterionChoices.model_validate(
            {"mechanism_specificity": "A"})  # partial answers rejected
    with pytest.raises(ValidationError):
        CriterionChoices.model_validate({name: "C" for name, _ in CRITERIA})
