"""A unit is refused unless its run BOTH completed and replays.

Implements SPEC S8 §5 / R16, and preserves the organiser tranche's PREREG
Amendments 6 and 9 unchanged. These are not defensive extras: the organiser
tranche's own ARM R reached `completed` over a record that reported four
verification violations, and composition succeeded on it regardless. Without
the second refusal its positions would have been scored as though the record
stood; with it, that arm's verdict was INCONCLUSIVE, which is what the record
actually supported.

Each refusal is driven RED (a fixture that should be refused and is harvested)
and GREEN (the same fixture correctly refused), so neither test can pass
vacuously.
"""
from __future__ import annotations

import json
import pathlib
import sys

import pytest

TOOLS = pathlib.Path(__file__).resolve().parents[1] / "tools"
sys.path.insert(0, str(TOOLS))

import judge_pairwise  # noqa: E402


def _arm(tmp_path: pathlib.Path, *, state: str, valid: bool,
         violations: list) -> pathlib.Path:
    """A fixture arm directory plus the run root its COMPOSED.json names."""
    root = tmp_path / "root"
    (root).mkdir(parents=True, exist_ok=True)
    (root / "run-status.json").write_text(json.dumps(
        {"state": state, "stop_reason": "max_cycles"}))
    (root / "REPLAY_VALIDATION.json").write_text(json.dumps(
        {"valid": valid, "verification": {"violations": violations}}))
    runs = tmp_path / "runs" / "armX"
    runs.mkdir(parents=True, exist_ok=True)
    (runs / "COMPOSED.txt").write_text("a composed unit\n")
    (runs / "COMPOSED.json").write_text(json.dumps({"root": str(root)}))
    return tmp_path


def _harvest(monkeypatch, tranche: pathlib.Path) -> list:
    monkeypatch.setattr(judge_pairwise, "TRANCHE", tranche)
    return judge_pairwise._harness_arm_units("armX")


def test_a_clean_and_replaying_run_IS_harvested(monkeypatch, tmp_path):
    """The green control: without this, the two refusals below could pass by
    refusing everything, which is the classic vacuous guard."""
    tranche = _arm(tmp_path, state="completed", valid=True, violations=[])
    assert len(_harvest(monkeypatch, tranche)) == 1


def test_a_run_that_did_not_complete_is_refused(monkeypatch, tmp_path):
    """Amendment 6's clause: a FAILED arm has no usable unit."""
    tranche = _arm(tmp_path, state="operational_failure", valid=True, violations=[])
    assert _harvest(monkeypatch, tranche) == []


def test_a_run_whose_record_does_not_replay_is_refused(monkeypatch, tmp_path):
    """Amendment 9's clause, and the one the organiser tranche paid for:
    `completed` is not enough when the record reports violations."""
    tranche = _arm(tmp_path, state="completed", valid=False,
                   violations=["attempt-validity at event 142"])
    assert _harvest(monkeypatch, tranche) == []


def test_violations_alone_refuse_even_when_valid_is_not_false(monkeypatch, tmp_path):
    """The organiser root's exact shape: a stored report carrying violations.
    Reading only `valid` would have let it through."""
    tranche = _arm(tmp_path, state="completed", valid=True,
                   violations=["attempt-validity at event 142",
                               "attempt-validity at event 215",
                               "attempt-validity at event 295"])
    assert _harvest(monkeypatch, tranche) == []


def test_a_missing_composed_unit_is_refused_and_does_not_raise(monkeypatch, tmp_path):
    """An arm that never terminated must produce a notice, not a traceback:
    one dead arm may not take the whole judging run down with it."""
    (tmp_path / "runs" / "armX").mkdir(parents=True)
    monkeypatch.setattr(judge_pairwise, "TRANCHE", tmp_path)
    assert judge_pairwise._harness_arm_units("armX") == []


def test_the_five_registered_comparisons_are_exactly_those_in_prereg():
    """C vs V is the load-bearing one: it is the only pair whose two arms
    differ solely in whether the objections carry content about their
    targets, which is what makes this a measurement of criticism rather than
    of a pipeline."""
    labels = [label for _t, _c, label in judge_pairwise.COMPARISONS]
    assert labels == ["C vs 0", "V vs 0", "C vs V", "A vs C", "A vs 0"], labels


def test_two_runs_of_one_arm_cannot_be_pooled_into_one_verdict():
    """R21. The six harness runs are named run by run, so `reveal` — which
    buckets by the treatment's own name — has no key under which two runs of
    one arm could be summed."""
    assert judge_pairwise.HARNESS_RUNS == (
        "armC-run1", "armC-run2", "armV-run1", "armV-run2",
        "armA-run1", "armA-run2")
    for arm in ("armC", "armV", "armA"):
        assert sum(1 for r in judge_pairwise.HARNESS_RUNS if r.startswith(arm)) == 2
