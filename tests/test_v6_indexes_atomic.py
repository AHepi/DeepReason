"""Derived v1 indexes publish complete immutable generations only."""

from __future__ import annotations
import json


import pytest

import deepreason.indexes as index_module
from deepreason.harness import Harness
from deepreason.indexes import load_indexes, rebuild_indexes
from deepreason.ontology import Provenance
from deepreason.verification.report import verify_root_report


def test_failed_same_log_rebuild_preserves_published_generation(tmp_path, monkeypatch):
    root = tmp_path / "run"
    harness = Harness(root)
    harness.create_artifact("indexed idea", provenance=Provenance(role="user"))
    manifest_path = rebuild_indexes(root)
    before_manifest = manifest_path.read_bytes()
    before = load_indexes(root)
    work_orders_filename = __import__("json").loads(before_manifest)["files"]["work-orders"]["file"]

    real_write = index_module._write_atomic

    def interrupted(path, payload):
        if path.name == work_orders_filename:
            raise OSError("simulated rebuild interruption")
        return real_write(path, payload)

    monkeypatch.setattr(index_module, "_write_atomic", interrupted)
    with pytest.raises(OSError, match="simulated rebuild interruption"):
        rebuild_indexes(root)

    assert manifest_path.read_bytes() == before_manifest
    assert load_indexes(root) == before
    assert (root / "log.jsonl").read_bytes()


def test_interrupted_changed_builder_cannot_overwrite_published_files(
    tmp_path,
    monkeypatch,
):
    root = tmp_path / "cross-version"
    harness = Harness(root)
    harness.create_artifact("stable indexed idea", provenance=Provenance(role="user"))
    manifest_path = rebuild_indexes(root)
    before_manifest = manifest_path.read_bytes()
    before_manifest_value = json.loads(before_manifest)
    before = load_indexes(root)
    old_payloads = {
        metadata["file"]: (manifest_path.parent / metadata["file"]).read_bytes()
        for metadata in before_manifest_value["files"].values()
    }

    original_document = index_module._category_document

    def changed_builder(category, source_digest, entries):
        return {
            **original_document(category, source_digest, entries),
            "builder_revision": "v2-test",
        }

    original_write = index_module._write_atomic
    written: list[str] = []
    old_work_orders = before_manifest_value["files"]["work-orders"]["file"]

    def interrupted(path, payload):
        written.append(path.name)
        if path.name.startswith("work-orders.") and path.name != old_work_orders:
            raise OSError("simulated cross-version rebuild interruption")
        return original_write(path, payload)

    monkeypatch.setattr(index_module, "_category_document", changed_builder)
    monkeypatch.setattr(index_module, "_write_atomic", interrupted)
    with pytest.raises(OSError, match="cross-version rebuild interruption"):
        rebuild_indexes(root)

    assert manifest_path.read_bytes() == before_manifest
    assert load_indexes(root) == before
    assert any(name.startswith("event-offsets.") for name in written)
    assert old_work_orders not in written
    assert {
        name: (manifest_path.parent / name).read_bytes() for name in old_payloads
    } == old_payloads


def test_indexes_are_excluded_from_root_authority_and_verification(tmp_path):
    root = tmp_path / "noncanonical"
    harness = Harness(root)
    harness.create_artifact("canonical history", provenance=Provenance(role="user"))
    before = verify_root_report(root)

    manifest_path = rebuild_indexes(root)
    assert verify_root_report(root) == before

    # Even malformed derived bytes are operationally rebuildable and must not
    # change the verdict over canonical log/object authority.
    manifest_path.write_text("not an index", encoding="utf-8")
    assert verify_root_report(root) == before


def test_indexes_round_trip_beyond_legacy_windows_path_limit(tmp_path):
    short_root = tmp_path / "source"
    harness = Harness(short_root)
    artifact = harness.create_artifact(
        "long path indexed idea",
        provenance=Provenance(role="user"),
    )
    long_root = tmp_path.joinpath(*(["derived-index-long-path"] * 12), "run")
    assert len(str(long_root.resolve())) > 260
    index_module._io_path(long_root).mkdir(parents=True)
    index_module._io_path(long_root / "log.jsonl").write_bytes(
        (short_root / "log.jsonl").read_bytes()
    )
    index_module._io_path(long_root / "objects" / "artifact").mkdir(parents=True)
    source_object = next((short_root / "objects" / "artifact").glob("*.json"))
    target_object = long_root / "objects" / "artifact" / source_object.name
    index_module._io_path(target_object).write_bytes(source_object.read_bytes())

    manifest_path = rebuild_indexes(long_root)
    manifest = json.loads(index_module._io_path(manifest_path).read_bytes())
    indexes = load_indexes(long_root)

    assert manifest["source_log_sha256"]
    assert indexes["artifacts"] == [{"artifact_id": artifact.id, "seq": 0}]
