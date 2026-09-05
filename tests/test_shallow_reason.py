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

    # R1: the former 200k shallow-mode token ceiling is retired; a
    # formerly-over-ceiling budget is now accepted and flows through.
    calls.clear()
    result = run_shallow_question("q", token_budget=10**9)
    assert result["completed"] is True
    assert calls[-1]["budget"] == 10**9
    with pytest.raises(ShallowReasonError, match="SHALLOW_BUDGET_INVALID"):
        run_shallow_question("q", token_budget=0)
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


def test_failed_qualification_falls_to_the_shallow_fitness_battery(
    tmp_path, monkeypatch, capsys
):
    """Full-battery failure no longer dead-ends: the tier ladder concludes."""

    from deepreason.qualification import ShallowFitnessCaseResultV1

    _configure(monkeypatch, tmp_path)
    monkeypatch.setattr(
        "deepreason.qualification.default_qualification_executor",
        lambda _manifest: (_ for _ in ()).throw(RuntimeError("secret provider body")),
    )
    monkeypatch.setattr(
        "deepreason.shallow_fitness.run_shallow_fitness_battery",
        lambda _profile: tuple(
            ShallowFitnessCaseResultV1(
                case_id=f"case-{index + 1:03d}",
                first_pass_valid=True,
                eventual_valid=True,
                repair_count=0,
            )
            for index in range(6)
        ),
    )
    assert main(["qualify", "--yes", "--json"]) == 0
    output = capsys.readouterr()
    assert "QUALIFICATION_EXECUTION_FAILED" in output.err
    assert "shallow-fitness battery" in output.err
    assert "secret provider body" not in output.err + output.out
    payload = json.loads(output.out)
    assert payload["tier"] == "shallow"
    assert payload["qualification_state"] == "ready_shallow"
    assert payload["next_action"] == 'deepreason reason --shallow "YOUR QUESTION"'


def test_shallow_endpoint_failure_exits_nonzero_with_diagnostic_payload(
    tmp_path, monkeypatch, capsys
):
    _configure(monkeypatch, tmp_path)

    def broken_mini_run(problems, endpoint, budget, root, max_cycles):
        return {
            "engine_profile": "mini",
            "stop": "endpoint-error",
            "cycles": 1,
            "tokens": {"total": 0, "calls": 0},
        }

    monkeypatch.setattr("minireason.loop.run", broken_mini_run, raising=True)
    assert main(["reason", "dead endpoint?", "--shallow"]) == 1
    output = capsys.readouterr()
    payload = json.loads(output.out)
    assert payload["completed"] is False
    assert payload["summary"]["stop"] == "endpoint-error"
    assert "SHALLOW_ENDPOINT_FAILED" in output.err


def test_shallow_result_root_is_isolated_per_run(tmp_path, monkeypatch):
    _configure(monkeypatch, tmp_path)
    calls = []
    monkeypatch.setattr("minireason.loop.run", _stub_mini_run(calls), raising=True)
    first = run_shallow_question("same question")
    second = run_shallow_question("same question")
    assert first["run_id"] != second["run_id"]
    assert calls[0]["root"] != calls[1]["root"]
    assert shallow_module.SHALLOW_DISCLAIMER in first["disclaimer"]


# ------------------------- the STANDARD frozen input (S1, R12)


def _freeze(root, *, description="why does the sky look blue?", criteria=()):
    """Write what `deepreason input freeze --root` writes, by the same call."""
    from deepreason.evidence import (
        AttachedSourceProvenanceV1,
        EvidenceDossierV1,
        RunInputManifestV2,
        RunInputProblemV2,
        bind_run_input,
    )

    dossier = EvidenceDossierV1.create(
        problem_ref="pi-standard",
        sources=(),
        total_byte_count=0,
        creation_provenance=AttachedSourceProvenanceV1(
            supplied_by="operator workload",
            acquisition_method="deepreason input freeze",
        ),
    )
    run_input = RunInputManifestV2.create(
        problem=RunInputProblemV2(
            id="pi-standard", description=description, criteria=criteria
        ),
        evidence_dossier_digest=dossier.dossier_digest,
    )
    bind_run_input(run_input, dossier, root)
    return run_input


def _stub_mini_run_accepting_input(calls):
    def mini_run(problems, endpoint, budget, root, max_cycles, **bound):
        calls.append({"problems": problems, "root": root, "bound": bound})
        return {
            "engine_profile": "mini",
            "model_profile": "compact",
            "stop": "queue-exhausted",
            "cycles": 1,
            "tokens": {"total": 0},
        }

    return mini_run


def test_shallow_takes_the_standard_frozen_input(tmp_path, monkeypatch, capsys):
    """Implements R12: "It's starting input should be standard."

    The standard input is the RunInputManifestV2 `deepreason input freeze`
    writes and the full harness takes -- problem plus criteria. The reduced
    engine takes the same record, states the same problem id, and binds it to
    the run root instead of mini's constant process root.
    """
    state, _ = _configure(monkeypatch, tmp_path)
    frozen_root = tmp_path / "frozen"
    frozen = _freeze(frozen_root)
    calls = []
    monkeypatch.setattr(
        "minireason.loop.run", _stub_mini_run_accepting_input(calls), raising=True
    )

    assert main(["reason", "--shallow", "--run-input", str(frozen_root)]) == 0
    payload = json.loads(capsys.readouterr().out)

    assert payload["question_problem_id"] == "pi-standard"
    assert payload["run_input"]["source"] == "frozen-input"
    assert payload["run_input"]["run_input_digest"] == frozen.run_input_digest
    assert payload["run_input"]["notices"] == []

    assert len(calls) == 1
    problem_id, question = calls[0]["problems"][0]
    assert problem_id == "pi-standard"
    assert question == "why does the sky look blue?"
    assert calls[0]["bound"]["run_input"].run_input_digest == frozen.run_input_digest


def test_the_bare_question_form_is_unchanged(tmp_path, monkeypatch, capsys):
    """C1/C4: nothing regresses for the caller who does not use the new road.

    The engine is called with EXACTLY the arguments it was called with before
    --run-input existed -- the stub below takes no **kwargs, so an extra one
    would be a TypeError rather than a silent difference.
    """
    _configure(monkeypatch, tmp_path)
    calls = []
    monkeypatch.setattr("minireason.loop.run", _stub_mini_run(calls), raising=True)

    assert main(["reason", "why does the sky look blue?", "--shallow"]) == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["run_input"] == {"source": "question", "criteria": 0, "notices": []}
    assert payload["question_problem_id"].startswith("q-")


def test_frozen_criteria_are_bound_and_their_non_use_is_disclosed(
    tmp_path, monkeypatch, capsys
):
    """Criteria reach the run's identity; that they are not compiled into
    commitments is SAID, not left to be inferred from a count."""
    from deepreason.evidence import RunInputCommitmentV1

    _configure(monkeypatch, tmp_path)
    frozen_root = tmp_path / "frozen"
    _freeze(
        frozen_root,
        criteria=(
            RunInputCommitmentV1(id="c-1", eval="program:json-wf"),
        ),
    )
    monkeypatch.setattr(
        "minireason.loop.run", _stub_mini_run_accepting_input([]), raising=True
    )
    assert main(["reason", "--shallow", "--run-input", str(frozen_root)]) == 0
    payload = json.loads(capsys.readouterr().out)

    assert payload["run_input"]["criteria"] == 1
    assert [n["code"] for n in payload["run_input"]["notices"]] == [
        "SHALLOW_RUN_INPUT_CRITERIA_NOT_COMPILED"
    ]


def test_a_question_that_contradicts_the_frozen_input_is_refused(tmp_path, monkeypatch):
    """Two starting inputs that disagree would leave the record saying two
    things; the refusal is typed rather than a silent precedence rule."""
    _configure(monkeypatch, tmp_path)
    frozen_root = tmp_path / "frozen"
    _freeze(frozen_root)
    with pytest.raises(ShallowReasonError, match="SHALLOW_QUESTION_CONFLICTS_WITH_RUN_INPUT"):
        run_shallow_question("a different question", run_input_root=frozen_root)


def test_an_unreadable_or_v1_frozen_input_is_refused_typed(tmp_path, monkeypatch):
    _configure(monkeypatch, tmp_path)
    with pytest.raises(ShallowReasonError, match="SHALLOW_RUN_INPUT_UNREADABLE"):
        run_shallow_question(run_input_root=tmp_path / "nothing-here")


def test_the_full_path_refuses_run_input_rather_than_ignoring_it(tmp_path, monkeypatch, capsys):
    """--run-input starts the reduced engine. Accepting it silently on the
    full path would be a flag that did nothing, which is the shape the
    all-configurations law names as a gate the operator cannot turn on."""
    _configure(monkeypatch, tmp_path)
    frozen_root = tmp_path / "frozen"
    _freeze(frozen_root)
    assert main(["reason", "q", "--run-input", str(frozen_root)]) == 1
    assert "REASON_RUN_INPUT_SHALLOW_ONLY" in capsys.readouterr().err


def test_reason_with_no_question_and_no_frozen_input_is_refused(tmp_path, monkeypatch, capsys):
    _configure(monkeypatch, tmp_path)
    assert main(["reason"]) == 1
    assert "REASON_QUESTION_REQUIRED" in capsys.readouterr().err
