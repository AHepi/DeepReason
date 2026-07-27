from __future__ import annotations

from pathlib import Path

import pytest

from deepreason.storage.blobs import BlobStore
from deepreason.workloads.code import (
    CodePatch,
    CodePatchCandidate,
    CodePatchProposal,
    PatchApplicationError,
    WorkspaceSnapshot,
    WorkspaceSpec,
    apply_code_patch,
    compile_patch_candidate,
    declared_root_digest,
    snapshot_workspace,
)


def _workspace(tmp_path: Path, source: str) -> tuple[Path, WorkspaceSpec]:
    root = tmp_path / "repo"
    root.mkdir()
    (root / "main.py").write_text(source, encoding="utf-8")
    return root, WorkspaceSpec(
        root=str(root.resolve()),
        root_digest=declared_root_digest(root, ("*.py",)),
        allowed_paths=("*.py",),
    )


def test_localized_patch_rejects_duplicate_anchor(tmp_path: Path):
    _root, spec = _workspace(tmp_path, "value = 1\nvalue = 1\n")
    snapshot = snapshot_workspace(spec)
    patch = compile_patch_candidate(
        CodePatchCandidate(
            patches=(CodePatchProposal(file="F1", anchor="S1", replacement="value = 2"),),
            rationale="change only the intended binding",
            typicality=0.1,
        ),
        snapshot,
        file_aliases={"F1": "main.py"},
        anchor_aliases={"S1": "value = 1"},
    )

    with pytest.raises(PatchApplicationError) as caught:
        apply_code_patch(spec, snapshot, patch, tmp_path / "applied")
    assert caught.value.code == "anchor-ambiguous"


def test_snapshot_and_patch_replay_from_content_addressed_blobs(tmp_path: Path):
    root, spec = _workspace(tmp_path, "value = 1\n")
    blobs = BlobStore(tmp_path / "blobs")
    snapshot = snapshot_workspace(spec, blobs=blobs)
    patch = compile_patch_candidate(
        CodePatchCandidate(
            patches=(CodePatchProposal(file="F1", anchor="S1", replacement="value = 2"),),
            rationale="replayable localized change",
            typicality=0.1,
        ),
        snapshot,
        file_aliases={"F1": "main.py"},
        anchor_aliases={"S1": "value = 1"},
    )
    snapshot_ref = blobs.put(snapshot.model_dump_json().encode())
    patch_ref = blobs.put(patch.model_dump_json().encode())
    (root / "main.py").unlink()
    root.rmdir()

    replayed_snapshot = WorkspaceSnapshot.model_validate_json(blobs.get(snapshot_ref))
    replayed_patch = CodePatch.model_validate_json(blobs.get(patch_ref))
    artifact = apply_code_patch(
        spec,
        replayed_snapshot,
        replayed_patch,
        tmp_path / "replayed",
        source_blobs=blobs,
        output_blobs=blobs,
    )

    assert (tmp_path / "replayed/main.py").read_text(encoding="utf-8") == "value = 2\n"
    assert artifact.patch_digest == patch.digest
    assert all(blobs.get(item.sha256) for item in artifact.files)

