from types import SimpleNamespace

import pytest

from deepreason.cli.main import main
from deepreason.ops import require_website_transaction_contracts


def test_historical_make_workflow_is_not_a_public_command(tmp_path, capsys):
    run_root = tmp_path / "run"
    with pytest.raises(SystemExit) as raised:
        main(["--root", str(run_root), "make", "transactional site"])

    assert raised.value.code == 2
    assert "invalid choice: 'make'" in capsys.readouterr().err
    assert not run_root.exists()


def test_website_transaction_preflight_preserves_v1_through_v5():
    for schema_version in range(1, 6):
        assert (
            require_website_transaction_contracts(
                SimpleNamespace(schema_version=schema_version)
            )
            is None
        )
