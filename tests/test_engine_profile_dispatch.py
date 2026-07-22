"""Engine profiles select executable surfaces, not reporting labels."""

from __future__ import annotations

import pytest

from deepreason import mcp_server
from deepreason.cli.main import main as cli_main
from deepreason.config import Config
from deepreason.ops import EngineProfileError, run_scheduler
from deepreason.run_manifest import (
    RunManifestError,
    compile_run_manifest,
    write_run_manifest,
)
from deepreason.runtime.launch_policy import V6_RUN_MANIFEST_REQUIRED


def _mini_manifest(tmp_path):
    manifest = compile_run_manifest(
        Config(
            engine_profile="mini",
            roles={
                "conjecturer": {
                    "endpoint": "https://ollama.invalid/v1",
                    "model": "gemma4:31b",
                    "provider": "ollama",
                    "family": "gemma",
                }
            },
        ),
        rubric_policy="forbid",
        compiled_at="2026-07-11T00:00:00Z",
    )
    path, _ = write_run_manifest(manifest, tmp_path / "mini-manifest.json")
    return manifest, path


def _mcp_call(name: str, arguments: dict) -> dict:
    return mcp_server.handle(
        {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "tools/call",
            "params": {"name": name, "arguments": arguments},
        }
    )["result"]


def test_ops_rejects_pre_v6_mini_before_adapter_or_model_call(
    tmp_path,
    monkeypatch,
):
    manifest, _ = _mini_manifest(tmp_path)
    from deepreason.harness import Harness

    harness = Harness(tmp_path / "legacy-run")
    monkeypatch.setattr(
        "deepreason.llm.adapter.build_adapter",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(
            AssertionError("historical admission built an adapter")
        ),
    )

    with pytest.raises(RunManifestError) as caught:
        run_scheduler(
            harness,
            Config(engine_profile="mini"),
            cycles=1,
            run_manifest=manifest,
        )

    assert caught.value.code == V6_RUN_MANIFEST_REQUIRED


def test_bound_v6_mini_reaches_engine_preflight_before_adapter(
    tmp_path,
    monkeypatch,
):
    from tests.test_v6_global_dispatch_guard import (
        _bound_qualified_v6_scheduler_root,
    )

    manifest, harness, config, _report = _bound_qualified_v6_scheduler_root(
        tmp_path / "run",
        engine_profile="mini",
    )
    monkeypatch.setattr(
        "deepreason.llm.adapter.build_adapter",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(
            AssertionError("engine preflight built an adapter")
        ),
    )

    with pytest.raises(EngineProfileError) as caught:
        run_scheduler(
            harness,
            config,
            cycles=1,
            run_manifest=manifest,
        )

    assert caught.value.code == "ENGINE_PROFILE_UNSUPPORTED_FOR_FULL_RUN"


def test_cli_rejects_mini_run_and_omits_historical_make(
    tmp_path, monkeypatch, capsys
):
    _manifest, path = _mini_manifest(tmp_path)
    monkeypatch.setattr(
        "deepreason.easy.make",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(
            AssertionError("website workflow started")
        ),
    )

    website_root = tmp_path / "website-run"
    with pytest.raises(SystemExit) as raised:
        cli_main(
            [
                "--root", str(website_root), "make", "DNA page",
                "--run-manifest", str(path), "--dry-run",
            ]
        )
    assert raised.value.code == 2
    assert "invalid choice: 'make'" in capsys.readouterr().err
    assert not (website_root / "run-manifest.json").exists()

    full_root = tmp_path / "full-run"
    full_root.mkdir()
    (full_root / "run-manifest.json").write_bytes(path.read_bytes())
    (full_root / "run-manifest.sha256").write_bytes(
        path.with_suffix(path.suffix + ".sha256").read_bytes()
    )
    before = {item.name: item.read_bytes() for item in full_root.iterdir()}
    assert cli_main(
        [
            "--root", str(full_root), "run", "--budget", "1",
            "--run-manifest", str(path), "--dry-run",
        ]
    ) == 1
    assert "UNSUPPORTED_RUN_MANIFEST_VERSION" in capsys.readouterr().err
    assert {item.name: item.read_bytes() for item in full_root.iterdir()} == before


def test_mcp_rejects_mini_before_worker_or_manifest_binding(tmp_path):
    _manifest, path = _mini_manifest(tmp_path)
    website_root = tmp_path / "mcp-website"
    result = _mcp_call(
        "start_make",
        {
            "root": str(website_root),
            "problem": {"description": "DNA page"},
            "run_manifest_ref": str(path),
            "budget": {"cycles": 1, "token_budget": 0},
        },
    )
    assert result["isError"] is True
    assert "UNSUPPORTED_RUN_MANIFEST_VERSION" in result["content"][0]["text"]
    assert not (website_root / "run-manifest.json").exists()
    assert str(website_root.resolve()) not in mcp_server._MAKE_THREADS


def test_mcp_run_cycles_rejects_mini_config_before_binding(tmp_path, monkeypatch):
    monkeypatch.setenv("DEEPREASON_ENABLE_LEGACY_MCP", "1")
    root = tmp_path / "mcp-run"
    config = tmp_path / "mini.yaml"
    config.write_text(
        "engine_profile: mini\n"
        "roles:\n"
        "  conjecturer:\n"
        "    endpoint: https://ollama.invalid/v1\n"
        "    model: gemma4:31b\n"
        "    provider: ollama\n",
        encoding="utf-8",
    )
    result = _mcp_call(
        "run_cycles", {"root": str(root), "config": str(config), "cycles": 1}
    )
    assert result["isError"] is True
    assert "ENGINE_PROFILE_UNSUPPORTED_FOR_FULL_RUN" in result["content"][0]["text"]
    assert not (root / "run-manifest.json").exists()
