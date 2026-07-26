"""Explicit shallow (reduced-engine) public surface.

Shallow mode is the declared fallback for models that cannot complete
production qualification and an explicit low-cost option for end users.
It must run without any qualification evidence, never touch the
qualification cache, and always label its output as shallow.
"""

from __future__ import annotations

import json

import pytest

import deepreason.shallow as shallow_module
from deepreason.cli.main import main
from deepreason.shallow import (
    SHALLOW_DEFAULT_MAX_CYCLES,
    SHALLOW_DEFAULT_TOKEN_BUDGET,
    SHALLOW_RESULT_SCHEMA,
    ShallowReasonError,
    run_shallow_question,
)
from tests.test_public_v6_facade import _configure


def _stub_mini_run(calls):
    def mini_run(problems, endpoint, budget, root, max_cycles):
        calls.append(
            {
                "problems": problems,
                "endpoint": endpoint,
                "budget": budget,
                "root": root,
                "max_cycles": max_cycles,
            }
        )
        return {
            "engine_profile": "mini",
            "model_profile": "compact",
            "stop": "queue-exhausted",
            "cycles": 3,
            "tokens": {"total": 1234},
        }

    return mini_run


def test_shallow_runs_without_qualification_and_labels_output(
    tmp_path, monkeypatch, capsys
):
    state, profile = _configure(monkeypatch, tmp_path)
    calls = []
    monkeypatch.setattr(
        "minireason.loop.run", _stub_mini_run(calls), raising=True
    )

    assert main(["reason", "why does the sky look blue?", "--shallow"]) == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["schema"] == SHALLOW_RESULT_SCHEMA
    assert payload["mode"] == "shallow"
    assert "shallow" in payload["disclaimer"]
    assert payload["run_id"].startswith("shallow-")
    assert payload["provider"] == profile.provider
    assert payload["model_id"] == profile.model_id
    assert payload["summary"]["engine_profile"] == "mini"

    # No qualification evidence was needed, consulted, or created.
    assert not (state / "qualification-cache").exists()
    assert len(calls) == 1
    call = calls[0]
    assert call["budget"] == SHALLOW_DEFAULT_TOKEN_BUDGET
    assert call["max_cycles"] == SHALLOW_DEFAULT_MAX_CYCLES
    assert call["problems"][1:] == []
    problem_id, question = call["problems"][0]
    assert problem_id.startswith("q-")
    assert question == "why does the sky look blue?"
    # The endpoint is the configured profile route, key included privately.
    assert call["endpoint"].model == profile.model_id
    assert call["endpoint"].api_key == "never-print-this-secret"
    assert "never-print-this-secret" not in json.dumps(payload)
    # The run root lives under the managed shallow area.
    assert str(call["root"]).startswith(str(state))


def test_shallow_budget_and_cycles_flow_through_and_are_bounded(
    tmp_path, monkeypatch, capsys
):
    _configure(monkeypatch, tmp_path)
    calls = []
    monkeypatch.setattr("minireason.loop.run", _stub_mini_run(calls), raising=True)
    assert (
        main(
            [
                "reason",
                "bounded?",
                "--shallow",
                "--cycles",
                "5",
                "--token-budget",
                "9000",
            ]
        )
        == 0
    )
    capsys.readouterr()
    assert calls[0]["budget"] == 9000
    assert calls[0]["max_cycles"] == 5

    with pytest.raises(ShallowReasonError, match="SHALLOW_BUDGET_INVALID"):
        run_shallow_question("q", token_budget=10**9)
    with pytest.raises(ShallowReasonError, match="SHALLOW_CYCLES_INVALID"):
        run_shallow_question("q", cycles=0)
    with pytest.raises(ShallowReasonError, match="SHALLOW_QUESTION_REQUIRED"):
        run_shallow_question("   ")


def test_shallow_fails_closed_without_credential_or_profile(
    tmp_path, monkeypatch, capsys
):
    _configure(monkeypatch, tmp_path, credential=False)

    def forbidden(*_args, **_kwargs):  # pragma: no cover - dispatch is the bug
        raise AssertionError("shallow dispatched without a credential")

    monkeypatch.setattr("minireason.loop.run", forbidden, raising=True)
    assert main(["reason", "no key?", "--shallow"]) == 1
    err = capsys.readouterr().err
    assert "SHALLOW_CREDENTIAL_MISSING" in err

    monkeypatch.setenv("DEEPREASON_HOME", str(tmp_path / "empty-home"))
    assert main(["reason", "no profile?", "--shallow"]) == 1
    assert "SHALLOW_PROFILE_UNAVAILABLE" in capsys.readouterr().err


def test_failed_qualification_points_to_shallow_fallback(
    tmp_path, monkeypatch, capsys
):
    _configure(monkeypatch, tmp_path)
    monkeypatch.setattr(
        "deepreason.qualification.default_qualification_executor",
        lambda _manifest: (_ for _ in ()).throw(RuntimeError("secret provider body")),
    )
    assert main(["qualify", "--yes"]) == 1
    err = capsys.readouterr().err
    assert "QUALIFICATION_EXECUTION_FAILED" in err
    assert 'deepreason reason --shallow "YOUR QUESTION"' in err
    assert "secret provider body" not in err


def test_shallow_result_root_is_isolated_per_run(tmp_path, monkeypatch):
    _configure(monkeypatch, tmp_path)
    calls = []
    monkeypatch.setattr("minireason.loop.run", _stub_mini_run(calls), raising=True)
    first = run_shallow_question("same question")
    second = run_shallow_question("same question")
    assert first["run_id"] != second["run_id"]
    assert calls[0]["root"] != calls[1]["root"]
    assert shallow_module.SHALLOW_DISCLAIMER in first["disclaimer"]
