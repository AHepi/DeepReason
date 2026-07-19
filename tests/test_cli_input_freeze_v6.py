"""Concrete operator workflow for immutable v6 criteria."""

from __future__ import annotations

import json

from deepreason.cli.main import main
from deepreason.evidence import RunInputManifestV1, RunInputManifestV2, load_run_input


def _workload(*, evaluation: str = "predicate:True", sources=()) -> dict:
    return {
        "schema": "deepreason-text-workload-v1",
        "problem": {
            "id": "criteria-demo",
            "description": "Find a solution satisfying every immutable criterion.",
        },
        "criteria": [
            {
                "id": "C001",
                "eval": evaluation,
                "budget": {
                    "steps": 123,
                    "time_ms": 50,
                    "extra": {"requirement": "never violate this constraint"},
                },
                "observation_valued": False,
            }
        ],
        "sources": list(sources),
        "allow_rubric": False,
        "allow_formalization": True,
        "allow_simulation": True,
        "brain": {"enabled": False, "query": None},
    }


def _write(path, payload) -> None:
    path.write_text(json.dumps(payload), encoding="utf-8")


def test_input_freeze_binds_complete_v6_criterion_and_is_idempotent(
    tmp_path, capsys
):
    root = tmp_path / "run"
    problem = tmp_path / "problem.json"
    _write(problem, _workload())

    argv = [
        "--root",
        str(root),
        "input",
        "freeze",
        "--problem",
        str(problem),
        "--schema-version",
        "6",
    ]
    assert main(argv) == 0
    result = json.loads(capsys.readouterr().out)
    frozen = load_run_input(root)

    assert isinstance(frozen, RunInputManifestV2)
    assert result["run_input_digest"] == frozen.run_input_digest
    criterion = frozen.problem.criteria[0]
    assert criterion.id == "C001"
    assert criterion.eval == "predicate:True"
    assert criterion.budget.steps == 123
    assert criterion.budget.extra["requirement"] == (
        "never violate this constraint"
    )

    assert main(argv) == 0
    assert json.loads(capsys.readouterr().out)["run_input_digest"] == (
        frozen.run_input_digest
    )

    changed = tmp_path / "changed.json"
    _write(changed, _workload(evaluation="predicate:False"))
    changed_argv = [*argv]
    changed_argv[changed_argv.index(str(problem))] = str(changed)
    assert main(changed_argv) == 1
    assert "RUN_INPUT_CONFLICT" in capsys.readouterr().err
    assert load_run_input(root) == frozen


def test_input_freeze_keeps_v5_id_only_and_requires_dossier_for_sources(
    tmp_path, capsys
):
    problem = tmp_path / "problem.json"
    _write(problem, _workload())
    v5_root = tmp_path / "v5"

    assert main(
        [
            "--root",
            str(v5_root),
            "input",
            "freeze",
            "--problem",
            str(problem),
            "--schema-version",
            "5",
        ]
    ) == 0
    capsys.readouterr()
    legacy = load_run_input(v5_root)
    assert isinstance(legacy, RunInputManifestV1)
    assert legacy.problem.criteria == ("C001",)

    sourced = tmp_path / "sourced.json"
    _write(sourced, _workload(sources=("SRC1",)))
    assert main(
        [
            "--root",
            str(tmp_path / "needs-dossier"),
            "input",
            "freeze",
            "--problem",
            str(sourced),
        ]
    ) == 1
    assert "INPUT_DOSSIER_REQUIRED" in capsys.readouterr().err
