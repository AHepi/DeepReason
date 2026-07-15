"""C13 compatibility: historical and legacy reads are physically inert."""

from __future__ import annotations

import hashlib
import json
import os
import stat
from pathlib import Path

import pytest

from deepreason.bridge.state import BridgeState
from deepreason.cli.main import main as cli_main
from deepreason.config import Config
from deepreason.harness import Harness
from deepreason.llm.adapter import LLMAdapter
from deepreason.llm.endpoints import MockEndpoint
from deepreason.ontology import Problem, ProblemProvenance
from deepreason.run_manifest import (
    bind_run_manifest,
    compile_run_manifest,
    config_from_run_manifest,
    load_run_manifest,
)
from deepreason.scratch.state import ScratchState


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
def test_tracked_v1_v2_runs_and_manifests_open_without_migration(
    relative_root, schema_version, event_count, expected_digest
):
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
    manifest = load_run_manifest(manifest_path)
    assert manifest.schema_version == schema_version
    assert manifest.sha256 == expected_digest
    assert manifest.canonical_bytes() == original_manifest
    assert "scratch_policy" not in manifest.model_dump(mode="json")
    assert "bridge_policy" not in manifest.model_dump(mode="json")
    assert all(
        payload.decode("utf-8").strip() == expected_digest
        for payload in original_sidecars.values()
    )

    reconstructed = config_from_run_manifest(manifest)
    assert reconstructed.scratchpad.enabled is False
    assert reconstructed.bridge.mode == "legacy_thesis"

    current = Harness(root, read_only=True)
    historical = Harness.at(root, event_count - 1)
    assert current._next_seq == historical._next_seq == event_count
    assert current.scratch_state == historical.scratch_state == ScratchState()
    assert current.bridge_state == historical.bridge_state == BridgeState()
    assert manifest.canonical_bytes() == original_manifest
    assert {
        path.name: path.read_bytes()
        for path in (
            root / "run-manifest.json.sha256",
            root / "run-manifest.sha256",
        )
        if path.exists()
    } == original_sidecars
    assert _tree_snapshot(root) == before


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


def test_bridge_inspect_and_claim_reads_preserve_all_filesystem_metadata(
    tmp_path, monkeypatch, capsys
):
    root = _completed_bridge_root(tmp_path)
    before = _tree_snapshot(root)
    monkeypatch.setattr("deepreason.easy.load_credentials", lambda: None)

    for command in ("inspect", "claims"):
        assert (
            cli_main(
                [
                    "--root",
                    str(root),
                    "bridge",
                    command,
                    "--json",
                ]
            )
            == 0
        )
        capsys.readouterr()
        assert _tree_snapshot(root) == before
