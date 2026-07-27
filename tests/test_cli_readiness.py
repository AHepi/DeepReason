from __future__ import annotations

import builtins
import json
from pathlib import Path

from deepreason.cli.main import build_parser, main
from deepreason.mcp_registration import registration_json, registration_payload
from deepreason.provider_profile import (
    ProviderProfileV1,
    setup_provider_profile_path,
    write_provider_profile,
)


def test_mcp_registration_uses_absolute_installed_path_with_spaces(tmp_path):
    environment = tmp_path / "environment with spaces"
    environment.mkdir()
    python = environment / ("python.exe" if __import__("os").name == "nt" else "python")
    mcp = environment / (
        "deepreason-mcp.exe" if __import__("os").name == "nt" else "deepreason-mcp"
    )
    python.write_text("")
    mcp.write_text("")

    payload = registration_payload(python)
    assert payload == {
        "mcpServers": {
            "deepreason": {
                "command": str(mcp.resolve()),
                "args": [],
            }
        }
    }
    assert json.loads(registration_json(python)) == payload
    assert "env" not in payload["mcpServers"]["deepreason"]


def test_registration_and_yes_are_parser_only_public_authority():
    parser = build_parser()
    registration = parser.parse_args(["mcp-registration"])
    qualification = parser.parse_args(["qualify", "--yes", "--json"])
    assert registration.command == "mcp-registration"
    assert qualification.yes is True
    assert qualification.json is True


def test_interactive_qualification_decline_makes_no_provider_call(
    tmp_path, monkeypatch, capsys
):
    state = tmp_path / "state"
    monkeypatch.setenv("DEEPREASON_HOME", str(state))
    monkeypatch.setenv("DEEPREASON_DECLINE_TEST_KEY", "present-but-never-printed")
    profile = ProviderProfileV1.create(
        provider="generic",
        endpoint="https://example.invalid/v1",
        model_id="decline-test",
        family="fixture",
        context_window_tokens=65_536,
        maximum_completion_tokens=4_096,
        credential_env="DEEPREASON_DECLINE_TEST_KEY",
        output_mechanism="native_json_schema",
    )
    write_provider_profile(
        profile,
        setup_provider_profile_path(environ={"DEEPREASON_HOME": str(state)}),
    )

    class InteractiveInput:
        @staticmethod
        def isatty():
            return True

    monkeypatch.setattr("sys.stdin", InteractiveInput())
    monkeypatch.setattr(builtins, "input", lambda _prompt: "no")
    monkeypatch.setattr(
        "deepreason.qualification.default_qualification_executor",
        lambda _manifest: (_ for _ in ()).throw(
            AssertionError("declined qualification reached the provider")
        ),
    )
    assert main(["qualify"]) == 1
    output = capsys.readouterr()
    assert "maximum expected provider calls" in output.err
    assert "QUALIFICATION_CANCELLED" in output.err
    assert not (state / "qualification-cache").exists()
