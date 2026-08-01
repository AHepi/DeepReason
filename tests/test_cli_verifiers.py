"""G02 keeps incomplete verifier workflows off the public CLI surface."""

from __future__ import annotations

import pytest

from deepreason.cli.main import main as cli_main


@pytest.mark.parametrize("command", ("prove", "check-proof", "code", "simulate"))
def test_unqualified_verifier_commands_are_not_public(command, tmp_path, capsys):
    root = tmp_path / command

    with pytest.raises(SystemExit) as raised:
        cli_main(["--root", str(root), command])

    assert raised.value.code == 2
    assert f"invalid choice: '{command}'" in capsys.readouterr().err
    assert not root.exists()
