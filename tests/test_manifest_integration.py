"""Phase-B evidence path: compile, bind, and preflight a schema-v2 text
manifest exactly as scripts/live_run.py evidence mode does, with zero
tokens. The plan's manifest_integration regression."""

from pathlib import Path

import pytest
from pydantic import ValidationError

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
    with pytest.raises(RunManifestError) as raised:
        load_run_manifest(root / "run-manifest.json")
    assert raised.value.code == "UNSUPPORTED_RUN_MANIFEST_VERSION"
    assert raised.value.rejected_version == 2

    # A rubric-bearing seeded harness passes preflight under this manifest.
    import sys
    sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
    from live_run import seed_bronze

    harness = Harness(tmp_path / "preflight")
    seed_bronze(harness)
    preflight_harness(manifest, harness, config)  # must not raise

    # All-configs-allowed (2026-08-12): a single-family judge matrix used to
    # be rejected at compile time; it now compiles with a typed notice
    # disclosing the same code the retired gate raised, before any call and
    # before a root can even be bound.
    single = _config()
    single.roles["judge"][1]["model"] = "deepseek-v4-flash"
    single_manifest = compile_run_manifest(
        single,
        schema_version=2,
        workload_profile="text",
        rubric_policy="require_cross_family",
    )
    assert [n.code for n in single_manifest.compile_notices] == [
        "SECOND_JUDGE_FAMILY_REQUIRED"
    ]


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
    """All-configs-allowed (2026-08-13): a missing calibration receipt used
    to be refused at compile time; it now compiles with a typed notice
    disclosing the same code the retired gate raised."""
    config = apply_overrides(_config(), {field: value})

    manifest = compile_run_manifest(
        config,
        schema_version=2,
        workload_profile="text",
        rubric_policy="require_cross_family",
    )
    assert [n.code for n in manifest.compile_notices] == [
        "CALIBRATION_RECEIPT_REQUIRED"
    ]


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
    """All-configs-allowed (2026-08-13): an unverifiable calibration
    receipt used to be refused at compile time; it now compiles with a
    typed notice disclosing the same code the retired gate raised."""
    config = apply_overrides(
        _config(),
        {
            field: value,
            "CALIBRATION_RECEIPT": "sha256:arbitrary-reference",
        },
    )

    manifest = compile_run_manifest(
        config,
        schema_version=2,
        workload_profile="text",
        rubric_policy="require_cross_family",
    )
    assert [n.code for n in manifest.compile_notices] == [
        "CALIBRATION_RECEIPT_UNVERIFIED"
    ]


def test_blank_calibration_receipt_is_missing():
    """All-configs-allowed (2026-08-13): a blank receipt counts as
    missing, and now compiles with a typed CALIBRATION_RECEIPT_REQUIRED
    notice instead of raising."""
    config = apply_overrides(
        _config(),
        {
            "TEXT_RUBRIC_AUTHORITY": "calibrated_status",
            "CALIBRATION_RECEIPT": "   ",
        },
    )

    manifest = compile_run_manifest(
        config,
        schema_version=2,
        workload_profile="text",
        rubric_policy="require_cross_family",
    )
    assert [n.code for n in manifest.compile_notices] == [
        "CALIBRATION_RECEIPT_REQUIRED"
    ]


def test_materialized_text_status_authority_is_rechecked_before_adapter_build(tmp_path):
    """All-configs-allowed (2026-08-13): preflight_harness's own recheck
    independently reproduces the same disclosure notice compile_run_manifest
    would have, instead of refusing. The config is unchanged between compile
    and recheck (rather than the prior test's compile-default/recheck-unsafe
    shape) so this exercises the recheck itself without also tripping the
    separate, untouched TEXT_AUTHORITY_POLICY_MANIFEST_MISMATCH guard below
    (SPEC.md Addendum 1, experiments/2026-08-13-change-calibration-receipt-notice/)."""
    config = apply_overrides(
        _config(), {"TEXT_RUBRIC_AUTHORITY": "calibrated_status"}
    )
    manifest = compile_run_manifest(
        config,
        schema_version=2,
        workload_profile="text",
        rubric_policy="require_cross_family",
    )

    notices = preflight_harness(manifest, Harness(tmp_path / "run"), config)
    assert [n.code for n in notices] == ["CALIBRATION_RECEIPT_REQUIRED"]


def test_runtime_calibrated_status_is_unverified_before_adapter_build(tmp_path):
    """All-configs-allowed (2026-08-13): same as above, for the unverified
    (receipt present but never verifiable) code."""
    config = apply_overrides(
        _config(),
        {
            "TEXT_RUBRIC_AUTHORITY": "calibrated_status",
            "CALIBRATION_RECEIPT": "sha256:unfrozen-runtime-upgrade",
        },
    )
    manifest = compile_run_manifest(
        config,
        schema_version=2,
        workload_profile="text",
        rubric_policy="require_cross_family",
    )

    notices = preflight_harness(manifest, Harness(tmp_path / "run"), config)
    assert [n.code for n in notices] == ["CALIBRATION_RECEIPT_UNVERIFIED"]


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


def test_missing_argumentative_authority_uses_safe_observe_only_default():
    partial = _config().model_dump(mode="json")
    partial.pop("ARGUMENTATIVE_AUTHORITY")

    manifest = compile_run_manifest(
        partial,
        schema_version=2,
        workload_profile="text",
        rubric_policy="require_cross_family",
    )

    assert config_from_run_manifest(manifest).ARGUMENTATIVE_AUTHORITY == "observe_only"


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
    with pytest.raises(ValidationError, match="PAIRWISE_AUTHORITY"):
        apply_overrides(_config(), {"PAIRWISE_AUTHORITY": "legacy_status"})
