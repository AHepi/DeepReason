"""The census's argumentative column must be able to move.

Implements SPEC S10 / R23, and exists because of a measurement rather than a
worry: across the 20 most criticism-heavy committed roots in this repository
there are 1 141 warrants and every one of them is DEMONSTRATIVE (measured
2026-09-09; the same shape the 2026-09-08 audit reported for the two roots it
examined, and for the organiser tranche's terminal root). So no committed root
can drive the argumentative branch, and ARM A returning zero would be
indistinguishable from an instrument that always returns zero.

These tests drive both roads on a fixture and assert the split moves.
"""
from __future__ import annotations

import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "tools"))
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[3] / "src"))

from deepreason.ontology import Warrant, WarrantType  # noqa: E402

import record_census  # noqa: E402


def _warrant(wid: str, kind: WarrantType) -> Warrant:
    return Warrant(
        id=wid, target="a" * 64, type=kind, commitment="c" * 64,
        verdict="fail", trace_ref="inline:{}", validity_node="v" * 64,
    )


def test_the_argumentative_column_moves_when_an_argumentative_warrant_exists():
    """The positive control no committed root can provide."""
    split = record_census.warrants_by_road({
        "w1": _warrant("w1", WarrantType.DEMONSTRATIVE),
        "w2": _warrant("w2", WarrantType.ARGUMENTATIVE),
        "w3": _warrant("w3", WarrantType.ARGUMENTATIVE),
    })
    assert split["argumentative"] == 2, split
    assert split["demonstrative"] == 1, split


def test_the_two_roads_are_counted_apart_and_not_summed():
    """A census that summed the roads would report the corpus's 1 141
    demonstrative warrants as 1 141 criticisms that moved a status, which is
    the exact misreading the audit's 2.3a exists to prevent."""
    only_demonstrative = record_census.warrants_by_road({
        f"w{i}": _warrant(f"w{i}", WarrantType.DEMONSTRATIVE) for i in range(7)
    })
    assert only_demonstrative["demonstrative"] == 7
    assert only_demonstrative["argumentative"] == 0


def test_an_empty_warrant_set_reports_zero_on_both_roads_and_does_not_raise():
    """A run that minted nothing is a fact the census must be able to state."""
    split = record_census.warrants_by_road({})
    assert split["demonstrative"] == 0 and split["argumentative"] == 0
