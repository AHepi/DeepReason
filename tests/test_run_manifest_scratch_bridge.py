"""RunManifest v3 scratch/bridge policy and compatibility contract."""

from __future__ import annotations

import json

import pytest
from pydantic import ValidationError

from deepreason.config import Config
from deepreason.run_manifest import (
    BridgePolicy,
    RunManifest,
    RunManifestError,
    ScratchPolicy,
    compile_run_manifest,
    config_from_run_manifest,
    load_run_manifest,
    write_run_manifest,
)


STAMP = "2026-07-16T00:00:00Z"


def _route(
    model: str = "gemma4:31b",
    *,
    family: str = "gemma",
    endpoint: str = "https://models.invalid/v1",
) -> dict:
    return {
        "endpoint_id": f"{family}-route",
        "endpoint": endpoint,
        "model": model,
        "provider": "fixture",
        "family": family,
        "api_key_env": "FIXTURE_API_KEY",
    }


def _grounded_config(**changes) -> Config:
    values = {
        "scratchpad": {"enabled": True},
        "bridge": {"mode": "grounded_two_stage"},
        "roles": {
            "conjecturer": _route(),
            "synthesizer": _route(),
            "summarizer": _route(),
            "thesis": _route(),
            "judge": _route(),
        },
    }
    values.update(changes)
    return Config(**values)


def _compile(config: Config, **changes) -> RunManifest:
    values = {
        "schema_version": 3,
        "workload_profile": "text",
        "rubric_policy": "forbid",
        "compiled_at": STAMP,
    }
    values.update(changes)
    return compile_run_manifest(config, **values)


@pytest.mark.parametrize("schema_version,workload", [(1, None), (2, "text")])
def test_v1_v2_bytes_and_source_hash_ignore_new_typed_defaults(
    schema_version, workload
):
    config = Config(roles={"conjecturer": _route()})
    legacy_mapping = config.model_dump(mode="json")
    legacy_mapping.pop("scratchpad")
    legacy_mapping.pop("bridge")

    current = compile_run_manifest(
        config,
        schema_version=schema_version,
        workload_profile=workload,
        rubric_policy="forbid",
        compiled_at=STAMP,
    )
    legacy = compile_run_manifest(
        legacy_mapping,
        schema_version=schema_version,
        workload_profile=workload,
        rubric_policy="forbid",
        compiled_at=STAMP,
    )

    assert current.canonical_bytes() == legacy.canonical_bytes()
    assert current.source_config_hash == legacy.source_config_hash
    assert "scratch_policy" not in current.model_dump(mode="json")
    assert "bridge_policy" not in current.model_dump(mode="json")


def test_v3_round_trip_freezes_complete_attention_and_bridge_policy(tmp_path):
    manifest = _compile(_grounded_config())
    path, digest_path = write_run_manifest(manifest, tmp_path / "manifest.json")
    with pytest.raises(RunManifestError) as raised:
        load_run_manifest(path)

    assert digest_path.read_text().strip() == manifest.sha256
    assert raised.value.code == "UNSUPPORTED_RUN_MANIFEST_VERSION"
    assert raised.value.rejected_version == 3
    assert manifest.scratch_policy is not None
    assert manifest.bridge_policy is not None
    assert set(manifest.scratch_policy.per_channel_limits) == {
        "focus",
        "link",
        "cluster",
        "keyword",
        "semantic",
        "recent",
        "loose",
        "dormant",
        "underexposed",
        "exploratory",
        "coverage",
    }
    assert manifest.scratch_policy.attention_policy().max_blocks_per_pack == 24
    workflow = manifest.bridge_policy.workflow_policy()
    assert workflow.ledger_role == "summarizer"
    assert workflow.composer_role == "thesis"
    assert workflow.reviewer_role == "judge"
    assert manifest.bridge_policy.reviewer_seat == 0
    assert manifest.bridge_policy.grounding_repair_role == "judge"
    engine_data = json.loads(manifest.engine_config_json)
    assert "scratchpad" not in engine_data
    assert "bridge" not in engine_data


def test_v3_nested_models_reject_unknown_knobs_and_missing_policies():
    manifest = _compile(_grounded_config())
    scratch = manifest.scratch_policy.model_dump(mode="json")
    scratch["authority_weight"] = 1
    with pytest.raises(ValidationError, match="authority_weight"):
        ScratchPolicy.model_validate(scratch)

    bridge = manifest.bridge_policy.model_dump(mode="json")
    bridge["invent_missing_answers"] = True
    with pytest.raises(ValidationError, match="invent_missing_answers"):
        BridgePolicy.model_validate(bridge)

    payload = manifest.model_dump(mode="json")
    payload.pop("scratch_policy")
    with pytest.raises(ValidationError, match="requires scratch_policy"):
        RunManifest.model_validate(payload)


@pytest.mark.parametrize("sentinel", ["", " auto ", "auto", "auto-alt", "unresolved"])
def test_v3_rejects_unresolved_neural_embedder_identity_on_direct_load(sentinel):
    manifest = _compile(_grounded_config())
    payload = manifest.model_dump(mode="json")
    payload["scratch_policy"]["embedder_model"] = sentinel

    with pytest.raises(ValidationError, match="exact concrete identifier"):
        RunManifest.model_validate(payload)


def test_v3_rejects_duplicate_or_inconsistent_engine_policy_on_direct_load():
    manifest = _compile(_grounded_config())
    payload = manifest.model_dump(mode="json")
    engine_data = json.loads(payload["engine_config_json"])
    engine_data["scratchpad"] = {"enabled": False}
    payload["engine_config_json"] = json.dumps(engine_data)
    with pytest.raises(ValidationError, match="V3_ENGINE_POLICY_DUPLICATE"):
        RunManifest.model_validate(payload)

    payload = manifest.model_dump(mode="json")
    engine_data = json.loads(payload["engine_config_json"])
    engine_data["EMBEDDER_MODEL"] = "different/neural-model"
    payload["engine_config_json"] = json.dumps(engine_data)
    with pytest.raises(ValidationError, match="V3_ENGINE_POLICY_MISMATCH"):
        RunManifest.model_validate(payload)


def test_v3_rejects_credential_bearing_decoy_roles_without_echoing_secret():
    manifest = _compile(_grounded_config())
    payload = manifest.model_dump(mode="json")
    secret = "credential-must-not-be-persisted-or-echoed"
    engine_data = json.loads(payload["engine_config_json"])
    engine_data["roles"] = {
        "conjecturer": {
            "endpoint": f"https://user:{secret}@example.invalid/v1",
            "model": "decoy-model",
        }
    }
    payload["engine_config_json"] = json.dumps(engine_data)

    with pytest.raises(ValidationError) as raised:
        RunManifest.model_validate(payload)

    assert "V3_ENGINE_ROLES_FORBIDDEN" in str(raised.value)
    assert secret not in str(raised.value)


def test_v3_is_secret_free_and_routes_are_concrete(monkeypatch):
    secret = "sk-never-persist-this-value"
    monkeypatch.setenv("FIXTURE_API_KEY", secret)
    config = _grounded_config()
    config.roles["conjecturer"] = _route(model="auto")
    monkeypatch.setattr(
        "deepreason.run_manifest.resolve_model",
        lambda model, _endpoint, key: (
            "gemma4:31b" if model == "auto" and key == secret else model
        ),
    )

    manifest = _compile(config)
    encoded = manifest.canonical_bytes().decode("utf-8")
    assert secret not in encoded
    assert "auto\"" not in encoded
    assert manifest.provider_fallback is False
    assert manifest.roles["conjecturer"][0].model_id == "gemma4:31b"


def test_v3_digest_is_deterministic_and_covers_policy():
    first = _compile(_grounded_config())
    second = _compile(_grounded_config())
    changed = _compile(
        _grounded_config(
            scratchpad={"enabled": True, "coverage_slot_every_n_packs": 7}
        )
    )

    assert first.canonical_bytes() == second.canonical_bytes()
    assert first.sha256 == second.sha256
    assert changed.sha256 != first.sha256
    assert changed.source_config_hash != first.source_config_hash


def test_v3_policy_is_deeply_immutable():
    manifest = _compile(_grounded_config())
    with pytest.raises(ValidationError, match="frozen"):
        manifest.scratch_policy.max_blocks_per_pack = 999
    with pytest.raises(TypeError, match="immutable"):
        manifest.scratch_policy.per_channel_limits["focus"] = 999
    with pytest.raises(ValidationError, match="frozen"):
        manifest.bridge_policy.max_grounding_repair_attempts = 0


def test_grounded_review_requires_explicit_reviewer_before_route_resolution(monkeypatch):
    config = _grounded_config(
        roles={
            "summarizer": _route(),
            "thesis": _route(),
        }
    )
    monkeypatch.setattr(
        "deepreason.run_manifest.resolve_model",
        lambda *_args: pytest.fail("missing reviewer reached route resolution"),
    )
    with pytest.raises(RunManifestError) as raised:
        _compile(config)
    assert raised.value.code == "BRIDGE_REVIEWER_ROUTE_REQUIRED"
    assert raised.value.pointer == "/roles/judge"


def test_grounded_review_can_freeze_seat_zero_of_cross_family_judges():
    config = _grounded_config()
    config.roles["judge"] = [
        _route(),
        _route(
            model="qwen3:32b",
            family="qwen",
            endpoint="https://second.invalid/v1",
        ),
    ]
    manifest = _compile(config, rubric_policy="require_cross_family")
    assert len(manifest.roles["judge"]) == 2
    assert manifest.bridge_policy.reviewer_seats == 1
    assert manifest.bridge_policy.reviewer_seat == 0


def test_review_disabled_needs_ledger_and_composer_but_not_reviewer():
    config = _grounded_config(
        bridge={
            "mode": "grounded_two_stage",
            "grounding_review": False,
            "max_grounding_repair_attempts": 0,
        },
        roles={"summarizer": _route(), "thesis": _route()},
    )
    manifest = _compile(config)
    assert manifest.bridge_policy.grounding_review is False
    assert manifest.roles["judge"] == ()


def test_scratch_disabled_and_semantic_disabled_require_no_optional_embedder():
    disabled = _compile(Config(EMBEDDER_MODEL=None))
    assert disabled.scratch_policy.enabled is False
    assert disabled.scratch_policy.embedder_backend == "disabled"
    assert disabled.scratch_policy.embedder_model is None

    literal_only = _compile(
        Config(
            EMBEDDER_MODEL=None,
            scratchpad={"enabled": True, "semantic_retrieval": False},
        )
    )
    assert literal_only.scratch_policy.enabled is True
    assert literal_only.scratch_policy.semantic_retrieval is False
    assert literal_only.scratch_policy.embedder_backend == "disabled"
    assert literal_only.scratch_policy.attention_policy().semantic_retrieval is False


def test_deterministic_hashing_backend_is_visible_without_neural_model():
    manifest = _compile(
        Config(EMBEDDER_MODEL=None, scratchpad={"enabled": True})
    )
    assert manifest.scratch_policy.embedder_backend == "deterministic_hashing"
    assert manifest.scratch_policy.fallback_embedder == "deterministic_hashing"


def test_compact_profile_clamps_scratch_and_composition_limits():
    manifest = _compile(
        _grounded_config(
            scratchpad={
                "enabled": True,
                "max_blocks_per_pack": 100,
                "max_guides_per_pack": 20,
                "similarity_top_k": 100,
            },
            bridge={
                "mode": "grounded_two_stage",
                "output_section_limit": 100,
            },
        ),
        model_profile="compact",
    )
    assert manifest.scratch_policy.max_blocks_per_pack == 12
    assert manifest.scratch_policy.max_guides_per_pack == 2
    assert max(manifest.scratch_policy.per_channel_limits.values()) <= 12
    assert manifest.bridge_policy.output_section_limit == 12
    assert config_from_run_manifest(manifest).scratchpad.max_blocks_per_pack == 12


def test_v3_runtime_reconstruction_uses_only_frozen_roles(monkeypatch):
    manifest = _compile(_grounded_config())
    payload = manifest.canonical_bytes()
    monkeypatch.setattr(
        "deepreason.run_manifest.resolve_model",
        lambda *_args: pytest.fail("runtime attempted route resolution"),
    )
    loaded = RunManifest.model_validate_json(payload)
    rebuilt = config_from_run_manifest(loaded)

    assert rebuilt.roles["summarizer"]["model"] == "gemma4:31b"
    assert rebuilt.roles["thesis"]["endpoint_id"] == "gemma-route"
    assert loaded.bridge_policy.ledger_role == "summarizer"
    assert loaded.bridge_policy.composer_role == "thesis"
    assert loaded.provider_fallback is False


def test_new_features_require_v3_before_any_route_resolution(monkeypatch):
    monkeypatch.setattr(
        "deepreason.run_manifest.resolve_model",
        lambda *_args: pytest.fail("v3 feature rejection reached route resolution"),
    )
    with pytest.raises(RunManifestError) as scratch_error:
        compile_run_manifest(
            Config(scratchpad={"enabled": True}),
            schema_version=2,
            workload_profile="text",
            rubric_policy="forbid",
            compiled_at=STAMP,
        )
    assert scratch_error.value.code == "SCRATCH_MANIFEST_V3_REQUIRED"

    with pytest.raises(RunManifestError) as bridge_error:
        compile_run_manifest(
            Config(bridge={"mode": "grounded_two_stage"}),
            schema_version=2,
            workload_profile="text",
            rubric_policy="forbid",
            compiled_at=STAMP,
        )
    assert bridge_error.value.code == "GROUNDED_BRIDGE_MANIFEST_V3_REQUIRED"


def test_v3_canonical_json_contains_no_runtime_route_selection_fields():
    manifest = _compile(_grounded_config())
    payload = json.loads(manifest.canonical_bytes())
    assert payload["provider_fallback"] is False
    assert payload["bridge_policy"]["ledger_role"] == "summarizer"
    assert payload["bridge_policy"]["composer_role"] == "thesis"
    assert payload["bridge_policy"]["reviewer_role"] == "judge"
    assert payload["bridge_policy"]["reviewer_seat"] == 0
    assert "route_selector" not in json.dumps(payload)
    assert "auto-alt" not in json.dumps(payload)
