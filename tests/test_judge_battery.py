"""The shipped judge battery preserves the normative ensemble boundary."""

import importlib.util
import json
import sys
from pathlib import Path

from deepreason.harness import Harness
from deepreason.llm.endpoints import MockEndpoint


def _load_script():
    path = Path(__file__).resolve().parents[1] / "scripts" / "judge_battery.py"
    spec = importlib.util.spec_from_file_location("judge_battery_test_module", path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_judge_battery_requires_explicit_second_family(monkeypatch, capsys):
    module = _load_script()
    monkeypatch.setenv("DEEPSEEK_API_KEY", "primary-secret")
    monkeypatch.delenv("POOLSIDE_API_KEY", raising=False)
    monkeypatch.setattr(sys, "argv", ["judge_battery.py"])

    assert module.main() == 1
    assert "requires an explicit cross-family second judge" in capsys.readouterr().err


def test_judge_battery_runs_every_probe_on_both_families(monkeypatch, tmp_path):
    module = _load_script()
    constructed_models = []

    def response(prompt):
        if "Which candidate is better?" in prompt:
            return json.dumps({"winner": "neither", "decisive_point": ""})
        return json.dumps({"verdict": "fail", "decisive_point": "probe"})

    def endpoint_factory(base_url, model, **_kwargs):
        constructed_models.append(model)
        return MockEndpoint(response, name=base_url, model=model)

    monkeypatch.setattr(module, "OpenAICompatEndpoint", endpoint_factory)
    monkeypatch.setattr(
        module,
        "CALIBRATION",
        [("a planted flaw", True), ("a clean control", False)],
    )
    monkeypatch.setattr(module, "VERBOSITY_PAIRS", [("terse", "padded")])
    monkeypatch.setenv("DEEPSEEK_API_KEY", "primary-secret")
    monkeypatch.setenv("POOLSIDE_API_KEY", "second-secret")
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "judge_battery.py",
            "--only",
            "v4-pro/reasoning-off",
            "--root",
            str(tmp_path / "run"),
            "--tag",
            "test",
        ],
    )

    assert module.main() == 0
    assert constructed_models == ["deepseek-v4-pro", "poolside/laguna-m.1"]

    report = json.loads(
        (tmp_path / "experiments/results/judge_battery_report_test.json").read_text()
    )
    arm = report["configs"]["v4-pro/reasoning-off"]
    assert arm["judge_ensemble"] == [
        "deepseek-v4-pro",
        "poolside/laguna-m.1",
    ]

    logged_models = [
        event.llm.model
        for event in Harness(tmp_path / "run").log.read()
        if event.llm is not None
    ]
    # Two calibration items and two presentation orders, every one ruled by
    # both seats: no process-only report can accidentally regress to seat 0.
    assert len(logged_models) == 8
    assert set(logged_models) == {"deepseek-v4-pro", "poolside/laguna-m.1"}
