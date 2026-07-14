"""Phase-B evidence path: compile, bind, and preflight a schema-v2 text
manifest exactly as scripts/live_run.py evidence mode does, with zero
tokens. The plan's manifest_integration regression."""

from pathlib import Path

import pytest

from deepreason.config import Config, apply_overrides
from deepreason.harness import Harness
from deepreason.run_manifest import (
    RunManifestError,
    bind_run_manifest,
    compile_run_manifest,
    load_run_manifest,
    preflight_harness,
)

ROLE = {
    "endpoint": "https://ollama.com/v1",
    "provider": "ollama",
    "temperature": 0.0,
    "api_key_env": "OLLAMA_API_KEY",
    "json_mode": True,
}


def _config() -> Config:
    roles = {
        name: {**ROLE, "model": "deepseek-v4-pro"}
        for name in (
            "conjecturer", "argumentative_critic", "defender",
            "variator", "synthesizer", "thesis",
        )
    }
    roles["judge"] = [
        {**ROLE, "model": "deepseek-v4-pro"},
        {**ROLE, "model": "gpt-oss:120b"},
    ]
    return apply_overrides(Config(), {"roles": roles})


def test_compile_bind_preflight_text_manifest(tmp_path):
    config = _config()
    manifest = compile_run_manifest(
        config,
        schema_version=2,
        workload_profile="text",
        rubric_policy="require_cross_family",
    )
    assert manifest.schema_version == 2
    assert manifest.workload_profile == "text"
    families = {route.family for route in manifest.roles["judge"]}
    assert len(families) == 2  # deepseek + openai-gpt

    root = tmp_path / "run"
    bind_run_manifest(manifest, root)
    reloaded = load_run_manifest(root / "run-manifest.json")
    assert reloaded.sha256 == manifest.sha256

    # A rubric-bearing seeded harness passes preflight under this manifest.
    import sys
    sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
    from live_run import seed_bronze

    harness = Harness(root)
    seed_bronze(harness)
    preflight_harness(manifest, harness, config)  # must not raise

    # A single-family judge matrix is rejected at compile time, before any
    # call and before a root can even be bound.
    single = _config()
    single.roles["judge"][1]["model"] = "deepseek-v4-flash"
    with pytest.raises(RunManifestError):
        compile_run_manifest(
            single,
            schema_version=2,
            workload_profile="text",
            rubric_policy="require_cross_family",
        )
