"""Offline regression canary for the defended-trial dispatch chain."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


SCRIPT = (
    Path(__file__).parents[1]
    / "experiments/2026-09-01-defect-judge-canary-compile-gap/run_stubbed_canary.py"
)


def test_one_cycle_reaches_defender_and_both_judge_provider_results(tmp_path):
    completed = subprocess.run(
        [sys.executable, str(SCRIPT), "--home", str(tmp_path / "fresh-home")],
        cwd=SCRIPT.parents[2],
        check=True,
        text=True,
        capture_output=True,
    )
    result = json.loads(completed.stdout)

    assert result["first_refusal"] is None
    assert result["policy_authority"] == "defended_trial"
    assert result["critical_sequence"] == [
        "argumentative_critic[0]",
        "defender[0]",
        "judge[0]",
        "judge[1]",
    ]
    assert [
        (row["dispatch"], row["task_kind"], row["step"])
        for row in result["typed_work"]
    ] == [
        ("argumentative_critic[0]", "criticism", "primary"),
        ("defender[0]", "defended_trial_step", "defender"),
        ("judge[0]", "defended_trial_step", "judge:0"),
        ("judge[1]", "defended_trial_step", "judge:1"),
    ]
    assert [row["provider_outcome"] for row in result["typed_work"]] == [
        "provider_result"
    ] * 4
    assert [row["terminal"] for row in result["typed_work"]] == ["completed"] * 4
    assert all(row["authorized"] for row in result["typed_work"])
    assert result["trial_contracts"] == {
        "defender[0]": ["defender.direct.v1"],
        "judge[0]": ["judgeruling.direct.v1"],
        "judge[1]": ["judgeruling.direct.v1"],
    }
    assert result["target_status_before"] == "accepted"
    assert result["target_formally_backed"] is False
    assert result["target_status"] == "refuted"
