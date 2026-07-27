import json
import os
from pathlib import Path
import subprocess
import sys


def _run_installed_module(tmp_path: Path, *arguments: str) -> subprocess.CompletedProcess[str]:
    environment = {**os.environ, "PYTHONPATH": ""}
    return subprocess.run(
        [
            sys.executable,
            "-I",
            "-m",
            "deepreason.experiments.campaign_cli",
            *arguments,
        ],
        cwd=tmp_path,
        env=environment,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
        timeout=30,
    )


def test_installed_campaign_module_help_has_no_source_tree_dependency(tmp_path):
    completed = _run_installed_module(tmp_path, "--help")

    assert completed.returncode == 0, completed.stderr
    assert "autonomous-inquiry campaign" in completed.stdout
    assert "--plan" in completed.stdout
    assert "--out" in completed.stdout


def test_installed_campaign_module_audits_one_existing_root(tmp_path):
    root = tmp_path / "run-A1"
    root.mkdir()
    (root / "run-result.json").write_text(
        json.dumps({"schema": "deepreason-run-result-v1", "state": "completed"}),
        encoding="utf-8",
    )
    (root / "log.jsonl").write_text("", encoding="utf-8")
    plan_path = tmp_path / "campaign-plan.json"
    plan_path.write_text(
        json.dumps(
            {
                "schema": "campaign.plan.v2",
                "qualification": True,
                "waves": [
                    {"id": "A", "runs": [{"id": "A1", "root": "run-A1"}]}
                ],
            }
        ),
        encoding="utf-8",
    )
    output_path = tmp_path / "campaign-index.json"

    completed = _run_installed_module(
        tmp_path,
        "--plan",
        str(plan_path),
        "--out",
        str(output_path),
        "--jobs",
        "1",
    )

    assert completed.returncode == 0, completed.stderr
    stdout_index = json.loads(completed.stdout)
    file_index = json.loads(output_path.read_text(encoding="utf-8"))
    assert stdout_index == file_index
    assert file_index["schema"] == "campaign.index.v2"
    assert file_index["waves"][0]["runs"][0]["run_id"] == "A1"
