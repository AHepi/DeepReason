"""Windows long-path regressions for the immutable blob store."""

import os
from pathlib import Path

import pytest

from deepreason.canonical import sha256_hex
from deepreason.storage.blobs import BlobStore, _io_path


def _long_blob_root(tmp_path: Path) -> Path:
    segments = [f"blob-long-segment-{index}-" + ("x" * 72) for index in range(4)]
    return tmp_path.joinpath(*segments, "blobs")


def test_long_path_atomic_temp_write_final_read_and_exists(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    root = _long_blob_root(tmp_path)
    data = b"canonical blob bytes remain independent of the filesystem path"
    replacements: list[tuple[Path, Path, bytes]] = []
    real_replace = os.replace

    def observe_replace(source, target) -> None:
        source_path = Path(source)
        target_path = Path(target)
        assert source_path.exists()
        assert source_path.read_bytes() == data
        assert not target_path.exists()
        replacements.append((source_path, target_path, source_path.read_bytes()))
        real_replace(source, target)

    monkeypatch.setattr(os, "replace", observe_replace)

    store = BlobStore(root)
    ref = store.put(data)
    logical_path = store._path(ref)

    assert ref == sha256_hex(data)
    assert logical_path == root / ref[:2] / ref
    assert len(os.path.abspath(str(logical_path))) > 260
    assert replacements
    temp_path, final_path, written = replacements[0]
    assert temp_path.name == f"{ref}.tmp.{os.getpid()}"
    assert final_path.name == ref
    assert written == data
    if os.name == "nt":
        assert str(temp_path).startswith("\\\\?\\")
        assert str(final_path).startswith("\\\\?\\")

    assert store.get(ref) == data
    assert store.resolve_prefix(ref[:12]) == ref

    # A second put exercises the long final-path existence check and does not
    # create or replace another temporary file.
    assert store.put(data) == ref
    assert len(replacements) == 1
    assert all(".tmp." not in item.name for item in final_path.parent.iterdir())


def test_long_path_read_only_store_reads_without_creating_or_writing(
    tmp_path: Path,
) -> None:
    root = _long_blob_root(tmp_path)
    data = b"read-only long-path blob"
    writable = BlobStore(root)
    ref = writable.put(data)

    read_only = BlobStore(root, read_only=True)
    assert read_only.root == root
    assert read_only.get(ref) == data
    assert read_only.resolve_prefix(ref[:16]) == ref
    with pytest.raises(RuntimeError, match="read-only"):
        read_only.put(b"must not be written")

    missing_root = root / ("missing-read-only-" + ("y" * 80))
    assert not _io_path(missing_root).exists()
    BlobStore(missing_root, read_only=True)
    assert not _io_path(missing_root).exists()
