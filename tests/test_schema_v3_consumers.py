"""Focused checks for runtime consumers of RunManifest schema version 3."""

from __future__ import annotations

from types import SimpleNamespace

import pytest

from deepreason import mcp_server
from deepreason.cli.main import (
    _doctor_policy_readiness,
    _text_manifest_schema_version,
    build_parser,
)
from deepreason.config import Config
from deepreason.run_manifest import compile_run_manifest, write_run_manifest


def test_config_compile_parser_accepts_schema_v3():
    parsed = build_parser().parse_args(
        ["config", "compile", "--schema-version", "3", "--out", "manifest.json"]
    )

    assert parsed.schema_version == 3


def test_text_entrypoint_selects_v3_only_for_v3_policy():
    legacy = SimpleNamespace(
        scratchpad=SimpleNamespace(enabled=False),
        bridge=SimpleNamespace(mode="legacy_thesis"),
    )
    scratch = SimpleNamespace(
        scratchpad=SimpleNamespace(enabled=True),
        bridge=SimpleNamespace(mode="legacy_thesis"),
    )
    bridge = SimpleNamespace(
        scratchpad=SimpleNamespace(enabled=False),
        bridge=SimpleNamespace(mode="grounded_two_stage"),
    )

    assert _text_manifest_schema_version(legacy) == 2
    assert _text_manifest_schema_version(scratch) == 3
    assert _text_manifest_schema_version(bridge) == 3


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


def test_mcp_start_run_accepts_v3_text_before_credential_preflight(
    tmp_path, monkeypatch
):
    manifest = compile_run_manifest(
        Config(),
        schema_version=3,
        workload_profile="text",
        rubric_policy="forbid",
        compiled_at="2026-07-16T00:00:00Z",
    )
    manifest_path, _digest_path = write_run_manifest(
        manifest, tmp_path / "manifest.json"
    )
    monkeypatch.setattr("deepreason.run_manifest.preflight_payload", lambda *_args: None)
    monkeypatch.setattr("deepreason.ops.require_full_engine", lambda *_args, **_kwargs: None)
    monkeypatch.setattr(
        mcp_server,
        "_missing_manifest_credentials",
        lambda _manifest: ["DEEPREASON_TEST_STOP_AFTER_VERSION_CHECK"],
    )

    with pytest.raises(ValueError, match="RUN_CREDENTIAL_MISSING"):
        mcp_server._start_run(
            {
                "root": str(tmp_path / "run"),
                "workload": "text",
                "problem": {"description": "Why?"},
                "run_manifest_ref": str(manifest_path),
                "budget": {"cycles": 1, "token_budget": 1},
            }
        )
