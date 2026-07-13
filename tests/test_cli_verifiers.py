"""Safe primary CLI seams for trusted code and simulation operations."""

from __future__ import annotations

import json
import sys
from pathlib import Path

from deepreason.canonical import sha256_hex
from deepreason.cli.main import main as cli_main
from deepreason.config import Config
from deepreason.run_manifest import ToolchainEntry, compile_run_manifest, write_run_manifest
from deepreason.workloads.code import (
    CheckSpec,
    CodePatch,
    CodeProblem,
    CodeWorkloadSpec,
    PatchEdit,
    SimulationSpec,
    WorkspaceSpec,
    declared_root_digest,
    snapshot_workspace,
)


def _route():
    return {
        "endpoint": "https://example.invalid/v1",
        "model": "gemma4:31b",
        "provider": "ollama",
        "family": "gemma",
    }


def _manifest(tmp_path, toolchain):
    manifest = compile_run_manifest(
        Config(roles={"conjecturer": _route()}),
        rubric_policy="forbid",
        compiled_at="2026-07-13T00:00:00Z",
        schema_version=2,
        workload_profile="code",
        toolchains=(toolchain,),
    )
    path, _ = write_run_manifest(manifest, tmp_path / "manifest.json")
    return path


def test_code_runs_only_workload_declared_check(tmp_path, capsys):
    source_root = tmp_path / "source"
    source_root.mkdir()
    source = source_root / "math.py"
    source.write_text("def double(value):\n    return value + 2\n", encoding="utf-8")
    workspace = WorkspaceSpec(
        root=str(source_root.resolve()),
        root_digest=declared_root_digest(source_root, ("*.py",)),
        allowed_paths=("*.py",),
    )
    snapshot = snapshot_workspace(workspace)
    patch = CodePatch(
        base_root_digest=snapshot.root_digest,
        edits=(
            PatchEdit(
                path="math.py",
                base_blob=snapshot.file("math.py").sha256,
                anchor_before="return value + 2",
                replacement="return value * 2",
            ),
        ),
    )
    check = CheckSpec(
        id="fixed",
        runner="command",
        argv=(
            sys.executable,
            "-c",
            "from pathlib import Path; assert 'value * 2' in Path('math.py').read_text()",
        ),
    )
    workload = CodeWorkloadSpec(
        problem=CodeProblem(id="bug", description="double adds"),
        workspace=workspace,
        checks=(check,),
    )
    workload_path = tmp_path / "workload.json"
    workload_path.write_text(workload.model_dump_json(by_alias=True), encoding="utf-8")
    patch_path = tmp_path / "patch.json"
    patch_path.write_text(patch.model_dump_json(by_alias=True), encoding="utf-8")
    manifest_path = _manifest(
        tmp_path,
        ToolchainEntry(
            id=f"python@{sys.version_info.major}.{sys.version_info.minor}",
            runner="local",
            executable=str(Path(sys.executable).resolve()),
            version_output_sha256="a" * 64,
            network=False,
            allowed_programs=("repo_test",),
        ),
    )
    run_root = tmp_path / "run"
    assert cli_main(
        [
            "--root", str(run_root), "code",
            "--workload", str(workload_path),
            "--patch", str(patch_path),
            "--run-manifest", str(manifest_path),
        ]
    ) == 0
    assert json.loads((run_root / "code-result.json").read_text())["verdict"] == "pass"
    assert '"verdict": "pass"' in capsys.readouterr().out


def test_simulate_binds_source_inputs_checker_and_python_fingerprint(tmp_path, capsys):
    inputs = b"[1,5]"
    checker = b"def check(item, seed, output):\n    return output['value'] >= item\n"
    source = b"def simulate(item, rng):\n    return {'value': item + rng.randint(0, 2)}\n"
    inputs_path = tmp_path / "inputs.json"
    checker_path = tmp_path / "checker.py"
    source_path = tmp_path / "model.py"
    inputs_path.write_bytes(inputs)
    checker_path.write_bytes(checker)
    source_path.write_bytes(source)
    source_root = tmp_path / "source"
    source_root.mkdir()
    workspace = WorkspaceSpec(
        root=str(source_root.resolve()),
        root_digest=declared_root_digest(source_root, ("*.py",)),
        allowed_paths=("*.py",),
    )
    toolchain_id = f"python@{sys.version_info.major}.{sys.version_info.minor}"
    simulation = SimulationSpec(
        entry="simulate",
        seed_set=(0, 7),
        inputs_ref=sha256_hex(inputs),
        observables=("value",),
        checker_ref=sha256_hex(checker),
        toolchain_id=toolchain_id,
    )
    workload = CodeWorkloadSpec(
        problem=CodeProblem(id="sim", description="test a pinned model"),
        workspace=workspace,
        simulations=(simulation,),
    )
    workload_path = tmp_path / "simulation-workload.json"
    workload_path.write_text(workload.model_dump_json(by_alias=True), encoding="utf-8")
    version = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
    manifest_path = _manifest(
        tmp_path,
        ToolchainEntry(
            id=toolchain_id,
            runner="local",
            executable=str(Path(sys.executable).resolve()),
            version_output_sha256=sha256_hex(version.encode()),
            network=False,
            allowed_programs=("simulation_oracle",),
        ),
    )
    run_root = tmp_path / "simulation-run"
    assert cli_main(
        [
            "--root", str(run_root), "simulate",
            "--workload", str(workload_path),
            "--source", str(source_path),
            "--inputs", str(inputs_path),
            "--checker", str(checker_path),
            "--run-manifest", str(manifest_path),
        ]
    ) == 0
    result = json.loads((run_root / "simulation-result.json").read_text())
    assert result["verdict"] == "pass"
    assert result["claim"].endswith("not the world")
    assert '"verdict": "pass"' in capsys.readouterr().out
