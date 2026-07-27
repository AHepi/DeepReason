"""V6-only discrimination at the raw RunManifest loading boundary."""

from __future__ import annotations

import json

import pytest

import deepreason.run_manifest as run_manifest_module
from deepreason.ontology import Commitment
from deepreason.run_manifest import (
    RunManifestError,
    bind_run_manifest,
    config_from_run_manifest,
    load_run_manifest,
    write_run_manifest,
)
from tests.test_run_input_v6_commitments import _bind_v2
from tests.test_run_manifest import _compile_v6_manifest


@pytest.mark.parametrize("schema_version", (1, 2, 3, 4, 5))
def test_historical_version_is_rejected_before_model_validation(
    tmp_path, monkeypatch, schema_version
):
    secret = "nested-secret-must-never-be-reported"
    path = tmp_path / "historical.json"
    path.write_text(
        json.dumps(
            {
                "roles": {"conjecturer": {"api_key": secret}},
                "engine_config_json": {"not": "a serialized configuration"},
                "nested": {"schema_version": 6, "secret": secret},
                "schema_version": schema_version,
            }
        ),
        encoding="utf-8",
    )
    original_files = set(tmp_path.iterdir())

    def forbidden(*_args, **_kwargs):
        pytest.fail("historical payload passed the raw version boundary")

    class ValidationTrap:
        model_validate = classmethod(forbidden)
        model_validate_json = classmethod(forbidden)

    monkeypatch.setattr(run_manifest_module, "RunManifest", ValidationTrap)
    monkeypatch.setattr(run_manifest_module, "compile_run_manifest", forbidden)
    monkeypatch.setattr(run_manifest_module, "config_from_run_manifest", forbidden)
    monkeypatch.setattr(run_manifest_module, "_manifest_sidecar_digest", forbidden)
    monkeypatch.setattr(run_manifest_module, "ProcessLock", forbidden)

    with pytest.raises(RunManifestError) as raised:
        load_run_manifest(path)

    error = raised.value
    assert error.code == "UNSUPPORTED_RUN_MANIFEST_VERSION"
    assert error.pointer == "/schema_version"
    assert error.rejected_version == schema_version
    assert secret not in str(error)
    assert set(tmp_path.iterdir()) == original_files


@pytest.mark.parametrize(
    ("case", "raw"),
    (
        ("malformed", b"{"),
        ("array", b"[]"),
        ("scalar", b"42"),
        ("missing", b"{}"),
        ("boolean", b'{"schema_version":true}'),
        ("string", b'{"schema_version":"1"}'),
        ("zero", b'{"schema_version":0}'),
        ("future", b'{"schema_version":7}'),
        (
            "excessive-nesting",
            b'{"schema_version":6,"nested":'
            + (b"[" * 10_000)
            + b"0"
            + (b"]" * 10_000)
            + b"}",
        ),
    ),
)
def test_nonhistorical_invalid_documents_remain_distinct(tmp_path, case, raw):
    path = tmp_path / f"{case}.json"
    path.write_bytes(raw)

    with pytest.raises(RunManifestError) as raised:
        load_run_manifest(path, verify_hash=False)

    error = raised.value
    assert error.code == "INVALID_RUN_MANIFEST"
    assert error.code != "UNSUPPORTED_RUN_MANIFEST_VERSION"
    assert not hasattr(error, "rejected_version")


def test_v6_uses_existing_model_validation_and_preserves_identity(
    tmp_path, monkeypatch
):
    manifest = _compile_v6_manifest()
    path, _ = write_run_manifest(manifest, tmp_path / "v6.json")
    original_bytes = path.read_bytes()
    original_validate_json = run_manifest_module.RunManifest.model_validate_json
    calls = []

    class ValidationSpy:
        @classmethod
        def model_validate_json(cls, raw):
            calls.append(raw)
            return original_validate_json(raw)

        @classmethod
        def model_validate(cls, *_args, **_kwargs):
            pytest.fail("V6 loader changed its model-validation entry point")

    monkeypatch.setattr(run_manifest_module, "RunManifest", ValidationSpy)

    loaded = load_run_manifest(path)

    assert calls == [original_bytes]
    assert loaded == manifest
    assert loaded.canonical_bytes() == original_bytes
    assert loaded.sha256 == manifest.sha256
    assert config_from_run_manifest(loaded) == config_from_run_manifest(manifest)
    assert path.read_bytes() == original_bytes


def test_v6_nested_model_validation_remains_active(tmp_path):
    manifest = _compile_v6_manifest()
    payload = json.loads(manifest.canonical_bytes())
    payload["provider_fallback"] = True
    path = tmp_path / "invalid-v6.json"
    path.write_text(json.dumps(payload), encoding="utf-8")

    with pytest.raises(RunManifestError) as raised:
        load_run_manifest(path, verify_hash=False)

    assert raised.value.code == "INVALID_RUN_MANIFEST"
    assert not hasattr(raised.value, "rejected_version")


def test_bound_v6_manifest_reloads_with_bytes_hash_input_and_config_unchanged(
    tmp_path,
):
    root = tmp_path / "run"
    run_input = _bind_v2(
        root,
        Commitment(id="k-g00-v6-binding", eval="predicate:True"),
    )
    manifest = _compile_v6_manifest(run_input_digest=run_input.run_input_digest)
    path, _ = bind_run_manifest(manifest, root)

    loaded = load_run_manifest(path)

    assert loaded == manifest
    assert loaded.run_input_digest == run_input.run_input_digest
    assert loaded.canonical_bytes() == manifest.canonical_bytes()
    assert loaded.sha256 == manifest.sha256
    assert config_from_run_manifest(loaded) == config_from_run_manifest(manifest)
