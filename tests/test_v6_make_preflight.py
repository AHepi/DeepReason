from types import SimpleNamespace

import pytest

from deepreason.cli.main import main
from deepreason.ops import require_website_transaction_contracts


def test_explicit_v6_make_rejects_before_root_binding_or_dispatch(
    tmp_path, monkeypatch, capsys
):
    run_root = tmp_path / "run"
    manifest_path = tmp_path / "v6-manifest.json"
    manifest = SimpleNamespace(schema_version=6, engine_profile="full")
    monkeypatch.setattr(
        "deepreason.run_manifest.load_run_manifest",
        lambda _path: manifest,
    )
    monkeypatch.setattr(
        "deepreason.easy.make",
        lambda *_args, **_kwargs: pytest.fail("rejected v6 make executed"),
    )
    monkeypatch.setattr(
        "deepreason.llm.adapter.build_adapter",
        lambda *_args, **_kwargs: pytest.fail("rejected v6 make dispatched"),
    )

    exit_code = main(
        [
            "--root",
            str(run_root),
            "make",
            "transactional site",
            "--run-manifest",
            str(manifest_path),
        ]
    )

    assert exit_code == 1
    assert "V6_WEBSITE_TRANSACTION_CONTRACT_UNAVAILABLE" in capsys.readouterr().err
    assert not run_root.exists()
    assert not (run_root / "run-manifest.json").exists()
    assert not (run_root / "run-result.json").exists()


def test_website_transaction_preflight_preserves_v1_through_v5():
    for schema_version in range(1, 6):
        assert (
            require_website_transaction_contracts(
                SimpleNamespace(schema_version=schema_version)
            )
            is None
        )
