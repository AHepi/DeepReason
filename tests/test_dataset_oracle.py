"""Dataset oracle (§6): claims about admitted data are falsifiable, not argued."""

from __future__ import annotations

import pytest

from deepreason import programs
from deepreason.harness import Harness
from deepreason.oracle import (
    FAIL,
    OVERRUN,
    PASS,
    dataset_oracle_commitment,
    dataset_rows,
    run_dataset,
)


CSV = (
    "name,score\n"
    "alpha,10\n"
    "beta,20\n"
    "gamma,40\n"
)

PASSING_CHECK = (
    "def check(rows):\n"
    "    return all(int(row['score']) >= 10 for row in rows)\n"
)

FAILING_CHECK = (
    "def check(rows):\n"
    "    return all(int(row['score']) > 15 for row in rows)\n"
)


def _rows():
    return dataset_rows(CSV.encode("utf-8"), ",")


def test_dataset_rows_parse_deterministically():
    rows = _rows()
    assert rows == [
        {"name": "alpha", "score": "10"},
        {"name": "beta", "score": "20"},
        {"name": "gamma", "score": "40"},
    ]
    with pytest.raises(ValueError, match="delimiter"):
        dataset_rows(b"a;b\n1;2\n", ";")


def test_dataset_claims_pass_and_fail_by_execution():
    verdict, detail = run_dataset(PASSING_CHECK, _rows())
    assert verdict == PASS and detail["rows"] == 3
    verdict, detail = run_dataset(FAILING_CHECK, _rows())
    assert verdict == FAIL and detail["claim_holds"] is False


def test_hostile_and_runaway_checks_are_contained():
    hostile = "import os\ndef check(rows):\n    return True\n"
    verdict, detail = run_dataset(hostile, _rows())
    assert verdict == FAIL and "unsafe" in detail["error"]

    dunder = "def check(rows):\n    return rows.__class__ is list\n"
    verdict, detail = run_dataset(dunder, _rows())
    assert verdict == FAIL and "unsafe" in detail["error"]

    runaway = (
        "def check(rows):\n"
        "    total = 0\n"
        "    while True:\n"
        "        total = total + 1\n"
    )
    verdict, detail = run_dataset(runaway, _rows(), step_limit=1_000)
    assert verdict == FAIL and "step limit" in detail["error"]


def test_oversized_payload_is_a_typed_overrun():
    wide = [{"col": "x" * 1_000} for _ in range(10_000)]
    verdict, detail = run_dataset(PASSING_CHECK, wide)
    assert verdict == OVERRUN
    assert "payload bound" in detail["error"]


def test_commitment_freezes_sidecar_identity():
    first = dataset_oracle_commitment("a" * 64, ",")
    again = dataset_oracle_commitment("a" * 64, ",")
    other = dataset_oracle_commitment("b" * 64, ",")
    assert first.id == again.id
    assert first.id != other.id
    assert first.eval == "program:dataset_oracle"
    assert programs.evaluable(first)


def test_evaluate_runs_the_check_against_the_admitted_sidecar(tmp_path):
    harness = Harness(tmp_path / "run")
    sidecar_ref = harness.blobs.put(CSV.encode("utf-8"))
    commitment = dataset_oracle_commitment(sidecar_ref, ",")
    claim = harness.create_artifact(PASSING_CHECK, codec="code:python")
    verdict, trace = programs.evaluate(commitment, claim, harness.blobs)
    assert verdict == PASS
    assert trace["source_sha256"] == sidecar_ref
    assert trace["eval"] == "program:dataset_oracle"

    refuted = harness.create_artifact(FAILING_CHECK, codec="code:python")
    verdict, _trace = programs.evaluate(commitment, refuted, harness.blobs)
    assert verdict == FAIL


def test_missing_or_corrupt_sidecar_is_a_typed_overrun(tmp_path):
    harness = Harness(tmp_path / "run")
    commitment = dataset_oracle_commitment("c" * 64, ",")
    claim = harness.create_artifact(PASSING_CHECK, codec="code:python")
    verdict, trace = programs.evaluate(commitment, claim, harness.blobs)
    assert verdict == OVERRUN
    assert "unavailable" in trace["error"]
