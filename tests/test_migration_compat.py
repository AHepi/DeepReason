"""C13 compatibility: historical reads fail closed and stay physically inert."""

from __future__ import annotations

import hashlib
import json
import os
import stat
from pathlib import Path

import pytest

from deepreason.config import Config
from deepreason.harness import Harness
from deepreason.llm.adapter import LLMAdapter
from deepreason.llm.endpoints import MockEndpoint
from deepreason.ontology import Problem, ProblemProvenance
from deepreason.run_manifest import (
    UnsupportedRunManifestVersionError,
    bind_run_manifest,
    compile_run_manifest,
    load_run_manifest,
)


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
_TRACKED_RUNS = (
    (
        "experiments/gemma4_dna_unattended_2026-07-12",
        1,
        186,
        "59b771a313c48caf22809b46c7c8cdc768a88d7857dc87f15b5149f8010ffa09",
    ),
    (
        "experiments/bronze_pilot_2026-07-14",
        2,
        75,
        "4778fb7b3a08d7b8ba40f0113bf7dd1e6d06024634fa316b62682b0331529d6c",
    ),
)


def _tree_snapshot(root: Path):
    """Capture directories, types, modes, mtimes, links, and file bytes."""

    root = root.resolve()
    paths = [
        root,
        *sorted(root.rglob("*"), key=lambda item: item.relative_to(root).as_posix()),
    ]
    snapshot = []
    for path in paths:
        observed = path.lstat()
        if stat.S_ISREG(observed.st_mode):
            payload = path.read_bytes()
        elif stat.S_ISLNK(observed.st_mode):
            payload = os.fsencode(os.readlink(path))
        else:
            payload = b""
        snapshot.append(
            (
                "." if path == root else path.relative_to(root).as_posix(),
                stat.S_IFMT(observed.st_mode),
                stat.S_IMODE(observed.st_mode),
                observed.st_mtime_ns,
                payload,
            )
        )
    return tuple(snapshot)


@pytest.mark.parametrize(
    ("relative_root", "schema_version", "event_count", "expected_digest"),
    _TRACKED_RUNS,
)
def test_tracked_v1_v2_runs_and_manifests_fail_closed_without_migration(
    relative_root, schema_version, event_count, expected_digest
):
    """V6-only: historical roots are rejected raw, byte-for-byte untouched."""

    root = REPOSITORY_ROOT / relative_root
    manifest_path = root / "run-manifest.json"
    before = _tree_snapshot(root)
    original_manifest = manifest_path.read_bytes()
    original_sidecars = {
        path.name: path.read_bytes()
        for path in (
            root / "run-manifest.json.sha256",
            root / "run-manifest.sha256",
        )
        if path.exists()
    }

    assert hashlib.sha256(original_manifest).hexdigest() == expected_digest
    assert json.loads(original_manifest)["schema_version"] == schema_version
    assert all(
        payload.decode("utf-8").strip() == expected_digest
        for payload in original_sidecars.values()
    )

    with pytest.raises(UnsupportedRunManifestVersionError) as raised:
        load_run_manifest(manifest_path)
    assert raised.value.code == "UNSUPPORTED_RUN_MANIFEST_VERSION"
    assert raised.value.rejected_version == schema_version

    # Opening the run root fails closed at the same raw version boundary,
    # for both a current view and a historical replay cut.
    with pytest.raises(UnsupportedRunManifestVersionError) as current_raised:
        Harness(root, read_only=True)
    assert current_raised.value.rejected_version == schema_version
    with pytest.raises(UnsupportedRunManifestVersionError) as historical_raised:
        Harness.at(root, event_count - 1)
    assert historical_raised.value.rejected_version == schema_version

    # The fail-closed reads never migrate, rewrite, or annotate the tree.
    assert manifest_path.read_bytes() == original_manifest
    assert {
        path.name: path.read_bytes()
        for path in (
            root / "run-manifest.json.sha256",
            root / "run-manifest.sha256",
        )
        if path.exists()
    } == original_sidecars
    assert _tree_snapshot(root) == before


@pytest.fixture
def _below_public_admission(monkeypatch):
    """Keep pre-v6 bridge read coverage below the public G02 wrapper.

    Mirrors the committed test_cli_bridge idiom: the raw V6-only loading
    boundary is exercised elsewhere; this file's subject is that completed
    bridge reads remain physically inert.
    """

    from deepreason.run_manifest import RunManifest

    monkeypatch.setattr(
        "deepreason.run_manifest.load_run_manifest",
        lambda path, **_kwargs: RunManifest.model_validate_json(
            Path(path).read_bytes()
        ),
    )
    monkeypatch.setattr(
        "deepreason.runtime.launch_policy.require_v6_launch_allowed",
        lambda _subject, *, operation: None,
    )


def _grounded_manifest():
    route = {
        "endpoint_id": "migration-fixture",
        "endpoint": "https://models.invalid/v1",
        "model": "fixture-model",
        "provider": "fixture",
        "family": "fixture",
    }
    return compile_run_manifest(
        Config(
            bridge={
                "mode": "grounded_two_stage",
                "grounding_review": False,
                "max_schema_repair_attempts": 0,
                "max_grounding_repair_attempts": 0,
            },
            roles={"summarizer": route, "thesis": route},
        ),
        schema_version=3,
        workload_profile="text",
        rubric_policy="forbid",
        compiled_at="2026-07-16T00:00:00Z",
    )


def _completed_bridge_root(tmp_path: Path) -> Path:
    root = tmp_path / "completed-bridge"
    harness = Harness(root)
    harness.register_problem(
        Problem(
            id="problem-migration-read",
            description="What does this bounded record establish?",
            provenance=ProblemProvenance(trigger="seed"),
        )
    )
    manifest = _grounded_manifest()
    bind_run_manifest(manifest, root)
    adapter = LLMAdapter(
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
                                    "requirement": "Grounding for the requested conclusion.",
                                    "reason": "The bounded record contains no evidence.",
                                }
                            ],
                        }
                    )
                ],
                name="scripted-migration-ledger",
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
                            "resolution_reason": "No grounding is present.",
                        }
                    )
                ],
                name="scripted-migration-composer",
            ),
        },
        harness.blobs,
        retry_max=0,
    )
    terminal = harness.build_bridge(
        "problem-migration-read",
        "answer",
        manifest.bridge_policy.workflow_policy(),
        run_manifest_digest=manifest.sha256,
        stage_a_adapter=adapter,
    )
    assert terminal.process_status == "success"
    return root


def _bridge_cli(root: Path, *argv: str) -> int:
    """Drive the bridge subcommand below the public V6-only admission wrapper."""

    import argparse

    from deepreason.cli import bridge as bridge_cli

    parser = argparse.ArgumentParser()
    parser.add_argument("--root", required=True)
    subparsers = parser.add_subparsers(dest="command", required=True)
    bridge_cli.register_parser(subparsers)
    args = parser.parse_args(["--root", str(root), "bridge", *argv])
    return bridge_cli._handle_bridge_command(args)


def test_bridge_inspect_and_claim_reads_preserve_all_filesystem_metadata(
    tmp_path, monkeypatch, capsys, _below_public_admission
):
    root = _completed_bridge_root(tmp_path)
    before = _tree_snapshot(root)
    monkeypatch.setattr("deepreason.easy.load_credentials", lambda: None)

    for command in ("inspect", "claims"):
        assert _bridge_cli(root, command, "--json") == 0
        capsys.readouterr()
        assert _tree_snapshot(root) == before
