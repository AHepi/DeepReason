"""Localized patch compilation and runner-owned code checks."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest
from pydantic import ValidationError

from deepreason.storage.blobs import BlobStore
from deepreason.workloads.code import (
    CheckSpec,
    CodePatch,
    CodePatchCandidate,
    CodePatchProposal,
    CodeProblem,
    CodeWorkloadSpec,
    PatchApplicationError,
    PatchEdit,
    WorkspaceSpec,
    apply_code_patch,
    build_code_cards,
    compile_patch_candidate,
    declared_root_digest,
    snapshot_workspace,
)
from deepreason.verification.code import verify_code_patch


def _workspace(tmp_path: Path) -> tuple[Path, WorkspaceSpec]:
    root = tmp_path / "repo"
    (root / "src/pkg").mkdir(parents=True)
    (root / "tests").mkdir()
    (root / "src/pkg/math.py").write_text(
        "def double(value):\n    return value + 2\n", encoding="utf-8"
    )
    (root / "tests/test_math.py").write_text(
        "from pkg.math import double\n\ndef test_double():\n    assert double(3) == 6\n",
        encoding="utf-8",
    )
    digest = declared_root_digest(root, ("src/**", "tests/**"))
    return root, WorkspaceSpec(
        root=str(root.resolve()),
        root_digest=digest,
        allowed_paths=("src/**", "tests/**"),
    )


def _compiled_patch(spec: WorkspaceSpec):
    snapshot = snapshot_workspace(spec)
    candidate = CodePatchCandidate(
        patches=(CodePatchProposal(file="F1", anchor="S1", replacement="return value * 2"),),
        rationale="multiplication is the intended operation",
        typicality=0.2,
    )
    patch = compile_patch_candidate(
        candidate,
        snapshot,
        file_aliases={"F1": "src/pkg/math.py"},
        anchor_aliases={"S1": "return value + 2"},
    )
    return snapshot, patch


def test_snapshot_pins_metadata_symbols_dependencies_and_tests(tmp_path):
    _root, spec = _workspace(tmp_path)
    snapshot = snapshot_workspace(spec)

    source = snapshot.file("src/pkg/math.py")
    assert source.language == "python"
    assert [(item.name, item.line_start) for item in source.symbol_index] == [("double", 1)]
    assert snapshot.test_mapping["src/pkg/math.py"] == ("tests/test_math.py",)
    assert any(edge.target == "pkg.math" for edge in snapshot.dependency_edges)


def test_model_contract_cannot_author_commands():
    with pytest.raises(ValidationError):
        CodePatchCandidate.model_validate(
            {
                "patches": [{"file": "F1", "anchor": "S1", "replacement": "pass"}],
                "rationale": "try it",
                "typicality": 0.5,
                "argv": ["sh", "-c", "anything"],
            }
        )


def test_patch_compiles_mandatory_path_anchor_and_base(tmp_path):
    _root, spec = _workspace(tmp_path)
    snapshot, patch = _compiled_patch(spec)

    assert patch.base_root_digest == snapshot.root_digest
    assert patch.edits[0].path == "src/pkg/math.py"
    assert patch.edits[0].base_blob == snapshot.file("src/pkg/math.py").sha256
    assert patch.edits[0].anchor_before == "return value + 2"
    assert patch.model_dump()["schema"] == "deepreason-code-patch-v1"
    assert "schema_" not in patch.model_dump()


def test_patch_applies_only_in_ephemeral_destination(tmp_path):
    root, spec = _workspace(tmp_path)
    snapshot, patch = _compiled_patch(spec)
    destination = tmp_path / "applied"

    artifact = apply_code_patch(spec, snapshot, patch, destination)

    assert "value + 2" in (root / "src/pkg/math.py").read_text(encoding="utf-8")
    assert "value * 2" in (destination / "src/pkg/math.py").read_text(encoding="utf-8")
    assert artifact.base_root_digest == snapshot.root_digest
    assert artifact.root_digest != snapshot.root_digest
    assert len(artifact.root_digest) == 64


def test_pinned_blob_snapshot_replays_without_source_workspace(tmp_path):
    root, spec = _workspace(tmp_path)
    blobs = BlobStore(tmp_path / "blobs")
    snapshot = snapshot_workspace(spec, blobs=blobs)
    candidate = CodePatchCandidate(
        patches=(CodePatchProposal(file="F1", anchor="S1", replacement="return value * 2"),),
        rationale="repair the arithmetic",
        typicality=0.2,
    )
    patch = compile_patch_candidate(
        candidate,
        snapshot,
        file_aliases={"F1": "src/pkg/math.py"},
        anchor_aliases={"S1": "return value + 2"},
    )
    for path in sorted(root.rglob("*"), reverse=True):
        if path.is_file():
            path.unlink()
        elif path.is_dir():
            path.rmdir()

    artifact = apply_code_patch(
        spec,
        snapshot,
        patch,
        tmp_path / "replayed",
        source_blobs=blobs,
    )

    assert artifact.root_digest != snapshot.root_digest
    assert "value * 2" in (tmp_path / "replayed/src/pkg/math.py").read_text()


@pytest.mark.parametrize(
    ("path", "base", "anchor", "code"),
    [
        ("../outside.py", "valid", "return value + 2", "path"),
        ("README.md", "valid", "anything", "forbidden-file"),
        ("src/pkg/math.py", "0" * 64, "return value + 2", "base-mismatch"),
        ("src/pkg/math.py", "valid", "not present", "anchor-missing"),
    ],
)
def test_patch_errors_are_operational(tmp_path, path, base, anchor, code):
    _root, spec = _workspace(tmp_path)
    snapshot = snapshot_workspace(spec)
    if path.startswith(".."):
        with pytest.raises(ValidationError):
            PatchEdit(path=path, base_blob="0" * 64, anchor_before=anchor, replacement="x")
        return
    base_blob = snapshot.file("src/pkg/math.py").sha256 if base == "valid" else base
    patch = CodePatch(
        base_root_digest=snapshot.root_digest,
        edits=(PatchEdit(path=path, base_blob=base_blob, anchor_before=anchor, replacement="x"),),
    )
    with pytest.raises(PatchApplicationError) as caught:
        apply_code_patch(spec, snapshot, patch, tmp_path / f"out-{code}")
    assert caught.value.code == code


def test_source_change_and_symlink_are_rejected_after_snapshot(tmp_path):
    root, spec = _workspace(tmp_path)
    snapshot, patch = _compiled_patch(spec)
    target = root / "src/pkg/math.py"
    outside = tmp_path / "outside.py"
    outside.write_text("return secret\n", encoding="utf-8")
    target.unlink()
    target.symlink_to(outside)

    with pytest.raises(PatchApplicationError) as caught:
        apply_code_patch(spec, snapshot, patch, tmp_path / "out")
    assert caught.value.code == "symlink-escape"


def test_focused_code_cards_are_bounded_and_aliasable(tmp_path):
    _root, spec = _workspace(tmp_path)
    snapshot = snapshot_workspace(spec)

    cards = build_code_cards(
        spec,
        snapshot,
        implicated_paths=("src/pkg/math.py", "tests/test_math.py"),
        diagnostics={"src/pkg/math.py": ["assertion failed"]},
        max_cards=1,
        max_lines=5,
    )

    assert len(cards) == 1
    assert cards[0].alias == "F1"
    assert cards[0].file == "src/pkg/math.py"
    assert cards[0].symbol == "double"
    assert cards[0].diagnostics == ("assertion failed",)
    assert "def double" in cards[0].excerpt


def test_trusted_check_runs_after_patch_and_is_content_addressed(tmp_path):
    _root, workspace_spec = _workspace(tmp_path)
    snapshot, patch = _compiled_patch(workspace_spec)
    check_source = (
        "from pathlib import Path; "
        "text=Path('src/pkg/math.py').read_text(); "
        "raise SystemExit(0 if 'value * 2' in text else 4)"
    )
    check = CheckSpec(
        id="patched-source",
        runner="command",
        argv=(sys.executable, "-c", check_source),
        cwd=".",
        expected_exit=0,
    )
    workload = CodeWorkloadSpec(
        problem=CodeProblem(id="bug-1", description="double adds instead of multiplies"),
        workspace=workspace_spec,
        checks=(check,),
    )
    blobs = BlobStore(tmp_path / "verification-blobs")
    # Persist source bytes before the ephemeral run, then persist the applied
    # tree and check streams into the same append-only store.
    snapshot = snapshot_workspace(workspace_spec, blobs=blobs)

    result = verify_code_patch(workload, snapshot, patch, blobs=blobs)

    assert result.verdict == "pass"
    assert result.artifact is not None
    assert result.checks[0].verdict == "pass"
    assert len(result.checks[0].command_sha256) == 64
    assert all(blobs.get(item.sha256) for item in result.artifact.files)


def test_failed_declared_check_is_an_ordinary_fail(tmp_path):
    _root, workspace_spec = _workspace(tmp_path)
    snapshot, patch = _compiled_patch(workspace_spec)
    check = CheckSpec(
        id="known-failure",
        runner="command",
        argv=(sys.executable, "-c", "raise SystemExit(7)"),
        expected_exit=0,
    )
    workload = CodeWorkloadSpec(
        problem=CodeProblem(id="bug-1", description="test the patch"),
        workspace=workspace_spec,
        checks=(check,),
    )

    result = verify_code_patch(workload, snapshot, patch)

    assert result.verdict == "fail"
    assert result.checks[0].returncode == 7
