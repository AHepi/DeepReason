"""Historical schema-v3 consumers are gone: the runtime is V6-only."""

from __future__ import annotations

from types import SimpleNamespace

import pytest

from deepreason.cli.main import _doctor_policy_readiness, build_parser


def test_config_compile_parser_rejects_historical_schema_version_selector(capsys):
    parser = build_parser()

    with pytest.raises(SystemExit) as excinfo:
        parser.parse_args(
            ["config", "compile", "--schema-version", "3", "--out", "manifest.json"]
        )
    assert excinfo.value.code == 2
    assert "--schema-version" in capsys.readouterr().err

    parsed = parser.parse_args(["config", "compile", "--out", "manifest.json"])
    assert not hasattr(parsed, "schema_version")


def test_text_entrypoint_prepares_v6_only_manifests():
    import deepreason.cli.main as cli_main

    # The per-policy schema selector was removed with the V6-only CLI; text
    # entry now always flows through managed V6 preparation.
    assert not hasattr(cli_main, "_text_manifest_schema_version")

    from deepreason.preparation import build_preparation_manifest
    from deepreason.provider_profile import ProviderProfileV1

    profile = ProviderProfileV1.create(
        provider="openai",
        endpoint="https://api.example.test/v1",
        model_id="model-schema-consumers",
        model_revision="revision-1",
        family="family-schema-consumers",
        context_window_tokens=131_072,
        maximum_completion_tokens=4_096,
        credential_env="DEEPREASON_SCHEMA_CONSUMERS_TEST_KEY",
    )
    manifest = build_preparation_manifest(
        profile,
        question="What does the bounded record establish?",
        compiled_at="2026-07-22T00:00:00Z",
    )

    assert manifest.schema_version == 6


def test_doctor_reports_policy_roles_and_visible_hashing_fallback(monkeypatch):
    monkeypatch.setattr("importlib.util.find_spec", lambda name: None)
    route = {
        "endpoint": "https://example.invalid/v1",
        "model": "gemma4:31b",
    }
    configured = SimpleNamespace(
        roles={
            "conjecturer": route,
            "synthesizer": route,
            "summarizer": route,
            "thesis": route,
        },
        scratchpad=SimpleNamespace(
            enabled=True,
            semantic_retrieval=True,
            block_role="conjecturer",
            link_role="synthesizer",
            guide_role="summarizer",
        ),
        bridge=SimpleNamespace(
            mode="grounded_two_stage",
            grounding_review=True,
            ledger_role="summarizer",
            composer_role="thesis",
            reviewer_role="grounding_reviewer",
        ),
        EMBEDDER_MODEL="nomic-ai/nomic-embed-text-v1.5",
        EMBEDDER_FAILURE_POLICY="fallback",
    )

    result = _doctor_policy_readiness(configured)

    assert result["required_roles"]["scratch"]["guide"] == "summarizer"
    assert result["required_roles"]["bridge"]["ledger"] == "summarizer"
    assert result["required_roles"]["bridge"]["composer"] == "thesis"
    assert result["required_roles"]["bridge"]["reviewer"] == "grounding_reviewer"
    assert result["scratch_readiness"]["ready"] is True
    assert result["scratch_readiness"]["authoring_ready"] is True
    assert result["scratch_readiness"]["missing_authoring_roles"] == []
    assert result["bridge_readiness"]["ready"] is False
    assert result["bridge_readiness"]["missing_roles"] == ["grounding_reviewer"]
    assert result["embedder"] == {
        "configured_backend": "configured_neural",
        "model": "nomic-ai/nomic-embed-text-v1.5",
        "failure_policy": "fallback",
        "fallback_backend": "deterministic_hashing",
        "dependency_available": False,
        "fallback_active": True,
        "ready": True,
    }


def test_doctor_keeps_manual_scratch_ready_without_authoring_routes(monkeypatch):
    monkeypatch.setattr("importlib.util.find_spec", lambda name: None)
    configured = SimpleNamespace(
        roles={},
        scratchpad=SimpleNamespace(
            enabled=True,
            semantic_retrieval=True,
            block_role="conjecturer",
            link_role="synthesizer",
            guide_role="summarizer",
        ),
        bridge=SimpleNamespace(mode="legacy_thesis", grounding_review=False),
        EMBEDDER_MODEL="nomic-ai/nomic-embed-text-v1.5",
        EMBEDDER_FAILURE_POLICY="fallback",
    )

    result = _doctor_policy_readiness(configured)

    assert result["scratch_readiness"]["ready"] is True
    assert result["scratch_readiness"]["authoring_ready"] is False
    assert result["scratch_readiness"]["missing_authoring_roles"] == [
        "conjecturer",
        "synthesizer",
        "summarizer",
    ]
