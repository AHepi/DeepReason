"""C13 explicit derived bridge views over immutable historical sources."""

from __future__ import annotations

import argparse
import json
import os
import shutil
import stat
from pathlib import Path

import pytest

import deepreason.bridge.derived as derived_bridge
from deepreason.application import bridge as bridge_application
from deepreason.bridge.derived import (
    DerivedBridgeError,
    open_derived_source,
    reserve_derived_destination,
    source_snapshot_digest,
)
from deepreason.bridge.harness import build_grounded_bridge
from deepreason.bridge.evidence_pack import assemble_evidence_pack
from deepreason.canonical import canonical_json
from deepreason.cli import bridge as bridge_cli
from deepreason.config import Config
from deepreason.harness import Harness
from deepreason.informal import holdout
from deepreason.llm.adapter import LLMAdapter
from deepreason.llm.endpoints import MockEndpoint
from deepreason.ontology import (
    Artifact,
    Interface,
    Problem,
    ProblemProvenance,
    Provenance,
)
from deepreason.run_manifest import (
    bind_run_manifest,
    compile_run_manifest,
    write_run_manifest,
)
from deepreason.scratch.models import ScratchProvenanceV1
from deepreason.scratch.service import ScratchService
from deepreason.storage.blobs import BlobStore


STAMP = "2026-07-16T00:00:00Z"


def _route() -> dict:
    return {
        "endpoint_id": "fixture-route",
        "endpoint": "https://models.invalid/v1",
        "model": "fixture-31b",
        "provider": "fixture",
        "family": "fixture",
    }


def _v3_manifest():
    return compile_run_manifest(
        Config(
            scratchpad={"enabled": True},
            bridge={"mode": "grounded_two_stage", "grounding_review": False},
            roles={"summarizer": _route(), "thesis": _route()},
        ),
        schema_version=3,
        workload_profile="text",
        rubric_policy="forbid",
        compiled_at=STAMP,
    )


def _legacy_manifest(schema_version: int = 2):
    return compile_run_manifest(
        Config(roles={"summarizer": _route()}),
        schema_version=schema_version,
        workload_profile="text" if schema_version >= 2 else None,
        rubric_policy="forbid",
        compiled_at=STAMP,
    )


def _problem(problem_id: str, description: str | None = None) -> Problem:
    return Problem(
        id=problem_id,
        description=description or f"What is justified for {problem_id}?",
        provenance=ProblemProvenance.model_validate({"trigger": "seed", "from": []}),
    )


def _scripted_adapter(harness: Harness) -> LLMAdapter:
    return LLMAdapter(
        {
            "summarizer": MockEndpoint(
                [
                    json.dumps(
                        {
                            "entries": [
                                {
                                    "entry_key": "K1",
                                    "claim_class": "unknown",
                                    "claim": "The requested conclusion is not established.",
                                }
                            ],
                            "uncovered_requirements": [
                                {
                                    "requirement": "Grounding for a positive answer.",
                                    "reason": "The fixed formal record does not supply it.",
                                }
                            ],
                        }
                    )
                ],
                name="derived-scripted-summarizer",
            ),
            "thesis": MockEndpoint(
                [
                    json.dumps(
                        {
                            "sections": [
                                {
                                    "span_id": "S1",
                                    "text": "The requested conclusion remains unknown.",
                                    "rendering_mode": "unknown",
                                    "ledger_entry_handles": ["E1"],
                                }
                            ],
                            "resolution": "insufficient_evidence",
                            "resolution_reason": "The source fence lacks grounding.",
                        }
                    )
                ],
                name="derived-scripted-thesis",
            ),
        },
        harness.blobs,
        retry_max=0,
    )


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", required=True)
    subparsers = parser.add_subparsers(dest="command", required=True)
    bridge_cli.register_parser(subparsers)
    return parser


def _run(root: Path, *argv: str) -> int:
    args = _parser().parse_args(["--root", str(root), "bridge", *argv])
    return bridge_cli.run_command(args)


def _tree_snapshot(root: Path) -> dict[str, tuple]:
    """Capture bytes, types, and stat metadata for the entire source tree."""

    paths = [root, *sorted(root.rglob("*"))]
    snapshot = {}
    for path in paths:
        observed = path.lstat()
        if stat.S_ISREG(observed.st_mode):
            payload = path.read_bytes()
            kind = "file"
        elif stat.S_ISLNK(observed.st_mode):
            payload = os.readlink(path).encode()
            kind = "symlink"
        elif stat.S_ISDIR(observed.st_mode):
            payload = b""
            kind = "directory"
        else:
            payload = b""
            kind = "other"
        # Read before the final lstat so an access-time update caused by this
        # snapshot is part of the baseline rather than mistaken for the build.
        observed = path.lstat()
        key = "." if path == root else path.relative_to(root).as_posix()
        snapshot[key] = (
            kind,
            observed.st_mode,
            observed.st_size,
            observed.st_mtime_ns,
            observed.st_ctime_ns,
            observed.st_uid,
            observed.st_gid,
            observed.st_nlink,
            payload,
        )
    return snapshot


def _old_source(
    tmp_path: Path, *, schema_version: int = 2
) -> tuple[Path, str, int]:
    root = tmp_path / "old-run"
    harness = Harness(root)
    for index in range(5):
        harness.register_problem(_problem(f"dummy-{index}"))
    problem_id = "historical-target"
    harness.register_problem(
        _problem(problem_id, "What conclusion does the historical fence justify?")
    )
    fence = harness._next_seq - 1
    harness.register_problem(_problem("created-after-fence"))
    bind_run_manifest(_legacy_manifest(schema_version), root)
    return root, problem_id, fence


def _source_with_blob(tmp_path: Path) -> tuple[Harness, str, int, str]:
    root = tmp_path / "blob-source"
    harness = Harness(root)
    problem_id = "blob-target"
    harness.register_problem(_problem(problem_id))
    artifact = harness.create_artifact(
        b"A source-backed observation with immutable bytes.",
        problem_id=problem_id,
    )
    return harness, problem_id, harness._next_seq - 1, artifact.content_ref


@pytest.mark.parametrize("legacy_schema_version", [1, 2])
def test_cli_derived_bridge_uses_independent_log_and_preserves_source(
    tmp_path, monkeypatch, capsys, legacy_schema_version
):
    source_root, problem_id, fence = _old_source(
        tmp_path, schema_version=legacy_schema_version
    )
    destination = tmp_path / "derived-view"
    manifest_path, _ = write_run_manifest(_v3_manifest(), tmp_path / "bridge-v3.json")
    before = _tree_snapshot(source_root)
    monkeypatch.setattr(
        bridge_application,
        "_build_bridge_adapter",
        lambda _manifest, harness: _scripted_adapter(harness),
    )

    assert (
        _run(
            source_root,
            "build",
            problem_id,
            "--derived-output",
            str(destination),
            "--at-seq",
            str(fence),
            "--run-manifest",
            str(manifest_path),
            "--json",
        )
        == 0
    )
    result = json.loads(capsys.readouterr().out)
    snapshot = bridge_cli._load_snapshot(destination)
    terminal = snapshot.terminal

    assert result["terminal"]["source_run_digest"] == terminal.source_run_digest
    assert terminal.process_status == "success"
    assert terminal.resolution.value == "insufficient_evidence"
    assert terminal.formal_seq == fence
    assert terminal.terminal_event_seq < fence
    assert len(terminal.source_run_digest) == 64
    assert snapshot.evidence_pack.source_run_digest == terminal.source_run_digest
    assert Harness(destination).state.problems == {}
    assert "created-after-fence" not in snapshot.evidence_pack.problem_family_refs
    assert _tree_snapshot(source_root) == before

    encoded_source = str(source_root.resolve()).encode()
    assert all(
        encoded_source not in path.read_bytes()
        for path in destination.rglob("*")
        if path.is_file()
    )


def test_failed_source_requires_explicit_labelled_diagnostic_derived_bridge(
    tmp_path, monkeypatch, capsys
):
    source_root, problem_id, fence = _old_source(tmp_path, schema_version=2)
    (source_root / "run-result.json").write_text(
        json.dumps(
            {
                "schema": "deepreason-run-result-v1",
                "state": "failed",
                "workload": "text",
            }
        ),
        encoding="utf-8",
    )
    manifest_path, _ = write_run_manifest(_v3_manifest(), tmp_path / "bridge-v3.json")
    monkeypatch.setattr(
        bridge_application,
        "_build_bridge_adapter",
        lambda _manifest, harness: _scripted_adapter(harness),
    )

    rejected = tmp_path / "rejected-view"
    assert (
        _run(
            source_root,
            "build",
            problem_id,
            "--derived-output",
            str(rejected),
            "--at-seq",
            str(fence),
            "--run-manifest",
            str(manifest_path),
        )
        == 1
    )
    assert "BRIDGE_REASONING_NOT_COMPLETED" in capsys.readouterr().err
    assert not rejected.exists()

    destination = tmp_path / "diagnostic-view"
    assert (
        _run(
            source_root,
            "build",
            problem_id,
            "--derived-output",
            str(destination),
            "--at-seq",
            str(fence),
            "--run-manifest",
            str(manifest_path),
            "--diagnostic-after-failure",
            "--json",
        )
        == 0
    )
    capsys.readouterr()
    marker = json.loads((destination / "diagnostic-bridge.json").read_text())
    assert marker["canonical"] is False
    assert marker["label"] == "noncanonical-after-failure"
    assert marker["source_state"] == "failed"
    assert marker["formal_seq"] == fence


def test_source_digest_is_path_independent_and_binds_canonical_records(tmp_path):
    source_root, _problem_id, fence = _old_source(tmp_path)
    copied_root = tmp_path / "copied-run"
    shutil.copytree(source_root, copied_root)
    first = open_derived_source(source_root, tmp_path / "view-a", fence)
    copied = open_derived_source(copied_root, tmp_path / "view-b", fence)

    assert first.source_run_digest == copied.source_run_digest
    assert source_snapshot_digest(first.harness) == first.source_run_digest

    # A legacy caller-authored problem ID does not bind its description, so
    # including sorted canonical object records is what makes this alteration
    # visible even though the event envelope itself is unchanged.
    record_path = copied.harness.objects._schema_path("problem", "historical-target")
    record = json.loads(record_path.read_bytes())
    record["data"]["description"] = "Altered copied description."
    record_path.write_bytes(canonical_json(record))
    altered = Harness.at(copied_root, fence)
    assert source_snapshot_digest(altered) != first.source_run_digest


@pytest.mark.parametrize("corruption", ["missing", "tampered"])
def test_derived_source_rejects_missing_or_tampered_required_blob(
    tmp_path, corruption
):
    harness, _problem_id, fence, ref = _source_with_blob(tmp_path)
    destination = tmp_path / "derived-view"
    source = open_derived_source(harness.root, destination, fence)
    blob_path = harness.blobs._path(ref)
    if corruption == "missing":
        blob_path.unlink()
    else:
        blob_path.write_bytes(b"attacker-controlled replacement")

    with pytest.raises(
        DerivedBridgeError, match="BRIDGE_DERIVED_SOURCE_BLOB_INVALID"
    ):
        source_snapshot_digest(source.harness)
    with pytest.raises(
        DerivedBridgeError, match="BRIDGE_DERIVED_SOURCE_BLOB_INVALID"
    ):
        reserve_derived_destination(source)
    assert not destination.exists()

    with pytest.raises(
        DerivedBridgeError, match="BRIDGE_DERIVED_SOURCE_BLOB_INVALID"
    ):
        open_derived_source(harness.root, tmp_path / "second-view", fence)


def test_derived_source_rejects_blob_shard_symlink(tmp_path):
    harness, _problem_id, fence, ref = _source_with_blob(tmp_path)
    blob_path = harness.blobs._path(ref)
    shard = blob_path.parent
    external_shard = tmp_path / "external-shard"
    external_shard.mkdir()
    shutil.move(blob_path, external_shard / ref)
    shard.rmdir()
    try:
        shard.symlink_to(external_shard, target_is_directory=True)
    except OSError as error:
        pytest.skip(f"directory symlinks unavailable: {error}")

    destination = tmp_path / "derived-view"
    with pytest.raises(
        DerivedBridgeError, match="BRIDGE_DERIVED_SOURCE_BLOB_INVALID"
    ):
        open_derived_source(harness.root, destination, fence)
    assert not destination.exists()


@pytest.mark.parametrize("malicious_ref", ["absolute", "traversal"])
def test_blob_store_and_historical_replay_reject_path_references(
    tmp_path, malicious_ref
):
    sentinel = tmp_path / "outside-secret.txt"
    secret = "SENTINEL MUST NEVER BE READ OR ECHOED"
    sentinel.write_text(secret)
    ref = (
        str(sentinel.resolve())
        if malicious_ref == "absolute"
        else "../../outside-secret.txt"
    )

    store = BlobStore(tmp_path / "standalone-blobs")
    with pytest.raises(KeyError) as get_error:
        store.get(ref)
    with pytest.raises(ValueError) as prefix_error:
        store.resolve_prefix("..")
    assert secret not in str(get_error.value)
    assert secret not in str(prefix_error.value)

    root = tmp_path / f"malicious-run-{malicious_ref}"
    harness = Harness(root)
    interface = Interface()
    artifact = Artifact(
        id=Artifact.compute_id(ref, "utf8", interface),
        content_ref=ref,
        codec="utf8",
        interface=interface,
        provenance=Provenance(role="user"),
    )
    harness.register_artifact(artifact)
    with pytest.raises(ValueError) as replay_error:
        Harness.at(root, harness._next_seq - 1)
    assert secret not in str(replay_error.value)


def test_transient_missing_blob_aborts_assembly_before_model_call(
    tmp_path, monkeypatch
):
    source_harness, problem_id, fence, ref = _source_with_blob(tmp_path)
    source = open_derived_source(
        source_harness.root, tmp_path / "reserved-destination", fence
    )
    destination = Harness(tmp_path / "execution-destination")
    blob_path = source_harness.blobs._path(ref)
    original_bytes = blob_path.read_bytes()
    original_view = derived_bridge._verified_source_view

    def transiently_missing_view(harness, *, sealed_refs):
        view = original_view(harness, sealed_refs=sealed_refs)
        verified_get = view.blobs.get

        class TransientBlobView:
            root = view.blobs.root
            read_only = True

            @staticmethod
            def get(candidate):
                if candidate != ref:
                    return verified_get(candidate)
                blob_path.unlink()
                try:
                    return verified_get(candidate)
                finally:
                    blob_path.write_bytes(original_bytes)

        view.blobs = TransientBlobView()
        return view

    class NeverCalledAdapter:
        @staticmethod
        def call(*_args, **_kwargs):
            pytest.fail("source assembly failure reached a model adapter")

    monkeypatch.setattr(
        derived_bridge, "_verified_source_view", transiently_missing_view
    )
    with pytest.raises(ValueError, match="source blob changed during assembly"):
        build_grounded_bridge(
            destination,
            problem_id,
            "answer",
            {},
            run_manifest_digest="0" * 64,
            stage_a_adapter=NeverCalledAdapter(),
            source_harness=source.harness,
            source_run_digest=source.source_run_digest,
        )

    assert blob_path.read_bytes() == original_bytes
    assert source_snapshot_digest(source.harness) == source.source_run_digest
    assert list(destination.log.read()) == []


def test_same_root_evidence_error_is_not_masked_by_derived_handler(
    tmp_path, monkeypatch
):
    harness = Harness(tmp_path / "same-root")
    harness.register_problem(_problem("same-root-problem"))

    def sentinel(*_args, **_kwargs):
        raise ValueError("same-root sentinel")

    monkeypatch.setattr("deepreason.bridge.harness.assemble_evidence_pack", sentinel)
    with pytest.raises(ValueError, match="same-root sentinel"):
        build_grounded_bridge(
            harness,
            "same-root-problem",
            "answer",
            {},
            run_manifest_digest="0" * 64,
            stage_a_adapter=None,
        )


def test_derived_holdout_availability_is_fixed_at_source_fence(tmp_path):
    source_root = tmp_path / "holdout-source"
    harness = Harness(source_root)
    problem_id = "holdout-problem"
    harness.register_problem(_problem(problem_id))
    secret = b"sealed future measurement: capsule mass is 31 kilograms"
    sealed = holdout.seal(harness, secret, problem_id=problem_id)
    alias_interface = Interface()
    alias = Artifact(
        id=Artifact.compute_id(sealed.content_ref, "raw", alias_interface),
        content_ref=sealed.content_ref,
        codec="raw",
        interface=alias_interface,
        provenance=Provenance(role="user"),
    )
    harness.register_artifact(alias, problem_id=problem_id)
    pre_reveal_seq = harness._next_seq - 1

    before_reveal = open_derived_source(
        source_root, tmp_path / "before-reveal-view", pre_reveal_seq
    )
    before_digest = before_reveal.source_run_digest
    before_pack = assemble_evidence_pack(
        derived_bridge._verified_source_view(
            before_reveal.harness,
            sealed_refs=before_reveal.sealed_blob_refs,
        ),
        problem_id,
        formal_seq=pre_reveal_seq,
        source_run_digest=before_digest,
    )
    assert secret.decode() not in before_pack.model_dump_json()
    sealed_artifact_ids = {sealed.id, alias.id}
    assert all(
        item.ref not in sealed_artifact_ids for item in before_pack.catalog_items
    )
    assert all(
        not sealed_artifact_ids
        & {
            *item.lineage.evidence_refs,
            *item.lineage.source_refs,
            *item.lineage.dependence_refs,
        }
        for item in [*before_pack.survivors, *before_pack.argued_refutations]
    )

    holdout.reveal(harness, sealed.id)
    reveal_seq = harness._next_seq - 1
    assert harness.blobs.get(sealed.content_ref) == secret

    historical_after_reveal = open_derived_source(
        source_root, tmp_path / "historical-after-reveal", pre_reveal_seq
    )
    historical_pack = assemble_evidence_pack(
        derived_bridge._verified_source_view(
            historical_after_reveal.harness,
            sealed_refs=historical_after_reveal.sealed_blob_refs,
        ),
        problem_id,
        formal_seq=pre_reveal_seq,
        source_run_digest=historical_after_reveal.source_run_digest,
    )
    assert historical_after_reveal.source_run_digest == before_digest
    assert historical_pack.id == before_pack.id
    assert secret.decode() not in historical_pack.model_dump_json()
    assert all(
        item.ref not in sealed_artifact_ids
        for item in historical_pack.catalog_items
    )

    revealed = open_derived_source(
        source_root, tmp_path / "revealed-view", reveal_seq
    )
    assert sealed.content_ref not in revealed.sealed_blob_refs
    assert revealed.harness.blobs.get(sealed.content_ref) == secret
    revealed_pack = assemble_evidence_pack(
        derived_bridge._verified_source_view(
            revealed.harness,
            sealed_refs=revealed.sealed_blob_refs,
        ),
        problem_id,
        formal_seq=reveal_seq,
        source_run_digest=revealed.source_run_digest,
    )
    assert secret.decode() in revealed_pack.model_dump_json()
    assert any(
        item.ref == sealed.id
        and item.kind == "evidence"
        and secret.decode() in item.excerpt
        for item in revealed_pack.catalog_items
    )


def test_derived_pack_uses_captured_holdout_availability_snapshot(tmp_path):
    harness, problem_id, fence, ref = _source_with_blob(tmp_path)
    source = open_derived_source(harness.root, tmp_path / "view", fence)
    assert source.sealed_blob_refs == frozenset()

    holdout_root = harness.root / "holdout"
    holdout_root.mkdir()
    marker = holdout_root / ref
    marker.write_bytes(b"transient marker must not change the captured fence")
    try:
        view = derived_bridge._verified_source_view(
            source.harness,
            sealed_refs=source.sealed_blob_refs,
        )
    finally:
        marker.unlink()
        holdout_root.rmdir()

    pack = assemble_evidence_pack(
        view,
        problem_id,
        formal_seq=fence,
        source_run_digest=source.source_run_digest,
    )
    assert "A source-backed observation with immutable bytes." in pack.model_dump_json()
    assert source_snapshot_digest(source.harness) == source.source_run_digest


@pytest.mark.parametrize(
    "case, expected",
    [
        ("missing", "BRIDGE_DERIVED_SOURCE_NOT_FOUND"),
        ("existing", "BRIDGE_DERIVED_DESTINATION_EXISTS"),
        ("same", "BRIDGE_DERIVED_ROOTS_OVERLAP"),
        ("nested", "BRIDGE_DERIVED_ROOTS_OVERLAP"),
        ("ancestor", "BRIDGE_DERIVED_ROOTS_OVERLAP"),
        ("negative", "BRIDGE_DERIVED_SEQ_INVALID"),
        ("out-of-range", "BRIDGE_DERIVED_SEQ_OUT_OF_RANGE"),
    ],
)
def test_derived_root_and_fence_rejections(tmp_path, case, expected):
    source_root, _problem_id, fence = _old_source(tmp_path)
    source = source_root
    destination = tmp_path / "new-view"
    seq = fence
    if case == "missing":
        source = tmp_path / "missing"
    elif case == "existing":
        destination.mkdir()
    elif case == "same":
        destination = source_root
    elif case == "nested":
        destination = source_root / "nested-view"
    elif case == "ancestor":
        destination = source_root.parent
    elif case == "negative":
        seq = -1
    elif case == "out-of-range":
        seq = 10_000

    with pytest.raises(DerivedBridgeError, match=expected):
        open_derived_source(source, destination, seq)


def test_derived_rejects_source_and_destination_symlinks(tmp_path):
    source_root, _problem_id, fence = _old_source(tmp_path)
    source_link = tmp_path / "source-link"
    try:
        source_link.symlink_to(source_root, target_is_directory=True)
    except OSError as exc:
        if getattr(exc, "winerror", None) == 1314:
            pytest.skip("Windows symlink privilege is unavailable")
        raise
    with pytest.raises(DerivedBridgeError, match="BRIDGE_DERIVED_SYMLINK_REJECTED"):
        open_derived_source(source_link, tmp_path / "view-a", fence)

    destination_link = tmp_path / "destination-link"
    destination_link.symlink_to(tmp_path / "missing-target", target_is_directory=True)
    with pytest.raises(DerivedBridgeError, match="BRIDGE_DERIVED_SYMLINK_REJECTED"):
        open_derived_source(source_root, destination_link, fence)


def test_derived_cli_requires_paired_flags_manifest_and_no_focus(
    tmp_path, monkeypatch, capsys
):
    source_root, problem_id, fence = _old_source(tmp_path)
    destination = tmp_path / "derived"
    monkeypatch.setattr(
        bridge_application,
        "_build_bridge_adapter",
        lambda *_args: pytest.fail("invalid preflight reached adapter construction"),
    )

    assert _run(source_root, "build", problem_id, "--at-seq", str(fence)) == 1
    assert "BRIDGE_DERIVED_FLAGS_REQUIRED" in capsys.readouterr().err
    assert not destination.exists()

    assert (
        _run(
            source_root,
            "build",
            problem_id,
            "--derived-output",
            str(destination),
            "--at-seq",
            str(fence),
        )
        == 1
    )
    assert "BRIDGE_DERIVED_MANIFEST_REQUIRED" in capsys.readouterr().err
    assert not destination.exists()

    assert (
        _run(
            source_root,
            "build",
            problem_id,
            "--derived-output",
            str(destination),
            "--at-seq",
            str(fence),
            "--run-manifest",
            str(tmp_path / "unused.json"),
            "--focus-block",
            "00",
        )
        == 1
    )
    assert "BRIDGE_DERIVED_SCRATCH_CONTEXT_UNAVAILABLE" in capsys.readouterr().err
    assert not destination.exists()


def test_derived_fails_closed_on_source_scratch_state(tmp_path):
    source = tmp_path / "source"
    harness = Harness(source)
    harness.register_problem(_problem("p"))
    ScratchService(harness).create_block(
        {"content": "Unpersisted destination context must not be inferred."},
        ScratchProvenanceV1(actor="user", origin="derived-test"),
    )
    fence = harness._next_seq - 1

    with pytest.raises(
        DerivedBridgeError, match="BRIDGE_DERIVED_SCRATCH_CONTEXT_UNAVAILABLE"
    ):
        open_derived_source(source, tmp_path / "destination", fence)


@pytest.mark.parametrize("destination_kind", ["same", "ancestor", "nested"])
def test_low_level_derived_bridge_recomputes_digest_and_rejects_overlap(
    tmp_path, destination_kind
):
    source_root, problem_id, fence = _old_source(tmp_path)
    historical = Harness.at(source_root, fence)
    separate = Harness(tmp_path / "separate")

    with pytest.raises(ValueError, match="source digest does not match"):
        build_grounded_bridge(
            separate,
            problem_id,
            "answer",
            {},
            run_manifest_digest="0" * 64,
            stage_a_adapter=None,
            source_harness=historical,
            source_run_digest="1" * 64,
        )

    if destination_kind == "same":
        overlapping_sink = Harness(source_root)
    elif destination_kind == "ancestor":
        overlapping_sink = Harness(source_root.parent)
    else:
        overlapping_sink = Harness(source_root / "nested-sink")
    with pytest.raises(ValueError, match="source and destination must not overlap"):
        build_grounded_bridge(
            overlapping_sink,
            problem_id,
            "answer",
            {},
            run_manifest_digest="0" * 64,
            stage_a_adapter=None,
            source_harness=historical,
            source_run_digest=source_snapshot_digest(historical),
        )
