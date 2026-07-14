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
    config_from_run_manifest,
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


def test_embedder_failure_policy_error_fails_closed(tmp_path, monkeypatch):
    """Evidence mode: EMBEDDER_FAILURE_POLICY=error stops the run before
    any model call when the neural backend is unavailable; the default
    fallback policy still degrades visibly."""
    from deepreason import ops
    from deepreason.llm import embedder as embedder_module
    from deepreason.llm.embedder import EmbedderUnavailable

    def unavailable(model):
        raise EmbedderUnavailable("backend missing")

    monkeypatch.setattr(embedder_module, "build_embedder", unavailable)
    monkeypatch.setattr(ops, "make_embedder", ops.make_embedder)

    harness = Harness(tmp_path / "root")
    strict = apply_overrides(Config(), {"EMBEDDER_FAILURE_POLICY": "error"})
    with pytest.raises(EmbedderUnavailable):
        ops.make_embedder(harness, strict)

    lenient = Config()
    assert ops.make_embedder(harness, lenient) is None
    fallback_measures = [
        e for e in harness.log.read()
        if e.inputs and e.inputs[0] == "embedder-fallback"
    ]
    assert len(fallback_measures) == 1


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("ARGUMENTATIVE_AUTHORITY", "trial_required"),
        ("TEXT_RUBRIC_AUTHORITY", "calibrated_status"),
        ("PAIRWISE_AUTHORITY", "calibrated_status"),
        ("INFRASTRUCTURE_REVIEW_AUTHORITY", "calibrated_status"),
    ],
)
def test_text_status_authority_requires_calibration_receipt(field, value):
    config = apply_overrides(_config(), {field: value})

    with pytest.raises(RunManifestError, match="CALIBRATION_RECEIPT_REQUIRED"):
        compile_run_manifest(
            config,
            schema_version=2,
            workload_profile="text",
            rubric_policy="require_cross_family",
        )


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("ARGUMENTATIVE_AUTHORITY", "trial_required"),
        ("TEXT_RUBRIC_AUTHORITY", "calibrated_status"),
        ("PAIRWISE_AUTHORITY", "calibrated_status"),
        ("INFRASTRUCTURE_REVIEW_AUTHORITY", "calibrated_status"),
    ],
)
def test_arbitrary_calibration_receipt_is_unverified(field, value):
    config = apply_overrides(
        _config(),
        {
            field: value,
            "CALIBRATION_RECEIPT": "sha256:arbitrary-reference",
        },
    )

    with pytest.raises(RunManifestError, match="CALIBRATION_RECEIPT_UNVERIFIED"):
        compile_run_manifest(
            config,
            schema_version=2,
            workload_profile="text",
            rubric_policy="require_cross_family",
        )


def test_blank_calibration_receipt_is_missing():
    config = apply_overrides(
        _config(),
        {
            "TEXT_RUBRIC_AUTHORITY": "calibrated_status",
            "CALIBRATION_RECEIPT": "   ",
        },
    )

    with pytest.raises(RunManifestError, match="CALIBRATION_RECEIPT_REQUIRED"):
        compile_run_manifest(
            config,
            schema_version=2,
            workload_profile="text",
            rubric_policy="require_cross_family",
        )


def test_materialized_text_status_authority_is_rechecked_before_adapter_build(tmp_path):
    manifest = compile_run_manifest(
        _config(),
        schema_version=2,
        workload_profile="text",
        rubric_policy="require_cross_family",
    )
    unsafe = apply_overrides(
        _config(), {"TEXT_RUBRIC_AUTHORITY": "calibrated_status"}
    )

    with pytest.raises(RunManifestError, match="CALIBRATION_RECEIPT_REQUIRED"):
        preflight_harness(manifest, Harness(tmp_path / "run"), unsafe)


def test_runtime_calibrated_status_is_unverified_before_adapter_build(tmp_path):
    manifest = compile_run_manifest(
        _config(),
        schema_version=2,
        workload_profile="text",
        rubric_policy="require_cross_family",
    )
    upgraded = apply_overrides(
        _config(),
        {
            "TEXT_RUBRIC_AUTHORITY": "calibrated_status",
            "CALIBRATION_RECEIPT": "sha256:unfrozen-runtime-upgrade",
        },
    )

    with pytest.raises(RunManifestError, match="CALIBRATION_RECEIPT_UNVERIFIED"):
        preflight_harness(manifest, Harness(tmp_path / "run"), upgraded)


def test_runtime_cannot_mutate_frozen_text_authority_policy(tmp_path):
    manifest = compile_run_manifest(
        _config(),
        schema_version=2,
        workload_profile="text",
        rubric_policy="require_cross_family",
    )
    mutated = apply_overrides(
        _config(), {"CALIBRATION_RECEIPT": "sha256:unfrozen-reference"}
    )

    with pytest.raises(
        RunManifestError, match="TEXT_AUTHORITY_POLICY_MANIFEST_MISMATCH"
    ):
        preflight_harness(manifest, Harness(tmp_path / "run"), mutated)


def test_missing_argumentative_authority_fails_closed_for_v2_text_manifest():
    legacy_shape = _config().model_dump(mode="json")
    legacy_shape.pop("ARGUMENTATIVE_AUTHORITY")

    with pytest.raises(
        RunManifestError, match="LEGACY_TEXT_STATUS_AUTHORITY_FORBIDDEN"
    ):
        compile_run_manifest(
            legacy_shape,
            schema_version=2,
            workload_profile="text",
            rubric_policy="require_cross_family",
        )


def test_text_authority_config_round_trips_from_frozen_manifest():
    config = _config()
    manifest = compile_run_manifest(
        config,
        schema_version=2,
        workload_profile="text",
        rubric_policy="require_cross_family",
    )

    rebuilt = config_from_run_manifest(manifest)

    assert rebuilt.TEXT_RUBRIC_AUTHORITY.value == "observe_only"
    assert rebuilt.PAIRWISE_AUTHORITY.value == "observe_only"
    assert rebuilt.INFRASTRUCTURE_REVIEW_AUTHORITY.value == "observe_only"
    assert rebuilt.CALIBRATION_RECEIPT is None


def test_legacy_text_status_authority_is_not_a_normal_manifest_mode():
    config = apply_overrides(_config(), {"PAIRWISE_AUTHORITY": "legacy_status"})

    with pytest.raises(
        RunManifestError, match="LEGACY_TEXT_STATUS_AUTHORITY_FORBIDDEN"
    ):
        compile_run_manifest(
            config,
            schema_version=2,
            workload_profile="text",
            rubric_policy="require_cross_family",
        )
