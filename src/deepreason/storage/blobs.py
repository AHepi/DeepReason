"""Content-addressed blob store (spec §1, §14).

Content is Sigma* (Def 3.1): opaque bytes + codec. Blobs are addressed by
sha256 and never mutated or deleted (D8).
"""

import os
from pathlib import Path
import re
import stat

from deepreason.canonical import sha256_hex


_CANONICAL_BLOB_REF = re.compile(r"^[0-9a-f]{64}$")
_CANONICAL_BLOB_PREFIX = re.compile(r"^[0-9a-f]{1,64}$")


class BlobStore:
    def __init__(self, root: Path, *, read_only: bool = False) -> None:
        self.root = Path(root)
        self.read_only = read_only
        if not read_only:
            self.root.mkdir(parents=True, exist_ok=True)

    def _path(self, ref: str) -> Path:
        if not isinstance(ref, str) or _CANONICAL_BLOB_REF.fullmatch(ref) is None:
            raise KeyError("invalid blob reference")
        return self.root / ref[:2] / ref

    def put(self, data: bytes) -> str:
        if self.read_only:
            raise RuntimeError("blob store is read-only")
        ref = sha256_hex(data)
        path = self._path(ref)
        if not path.exists():
            path.parent.mkdir(parents=True, exist_ok=True)
            tmp = path.parent / f"{ref}.tmp.{os.getpid()}"
            tmp.write_bytes(data)
            os.replace(tmp, path)
        return ref

    def get(self, ref: str) -> bytes:
        path = self._path(ref)
        shard = path.parent
        try:
            root_before = self.root.lstat()
            shard_before = shard.lstat()
            file_before = path.lstat()
        except OSError as error:
            raise KeyError("blob not found") from error
        if (
            not stat.S_ISDIR(root_before.st_mode)
            or _link_like(self.root, root_before)
            or not stat.S_ISDIR(shard_before.st_mode)
            or _link_like(shard, shard_before)
            or not stat.S_ISREG(file_before.st_mode)
            or _link_like(path, file_before)
            or file_before.st_nlink != 1
        ):
            raise KeyError("invalid blob storage path")
        try:
            data = path.read_bytes()
            root_after = self.root.lstat()
            shard_after = shard.lstat()
            file_after = path.lstat()
        except OSError as error:
            raise KeyError("blob became unavailable") from error
        if (
            not _same_identity(root_before, root_after)
            or not _same_identity(shard_before, shard_after)
            or not _same_identity(file_before, file_after)
            or _link_like(self.root, root_after)
            or _link_like(shard, shard_after)
            or _link_like(path, file_after)
            or len(data) != file_after.st_size
            or sha256_hex(data) != ref
        ):
            raise KeyError("blob integrity check failed")
        return data

    def resolve_prefix(self, prefix: str) -> str:
        """Unique-prefix resolution (the CLI `blob` command): deterministic
        sorted scan; raises KeyError when nothing matches and ValueError
        naming the candidates when the prefix is ambiguous."""
        if (
            not isinstance(prefix, str)
            or _CANONICAL_BLOB_PREFIX.fullmatch(prefix) is None
        ):
            raise ValueError("invalid blob prefix")
        if len(prefix) >= 2:
            shard_dirs = [self.root / prefix[:2]]
        else:
            if not self.root.exists():
                raise KeyError(f"no blob matches prefix {prefix!r}")
            shard_dirs = sorted(p for p in self.root.iterdir() if p.is_dir())
        matches: list[str] = []
        for shard in shard_dirs:
            if not shard.is_dir():
                continue
            matches.extend(
                p.name for p in sorted(shard.iterdir())
                if p.name.startswith(prefix) and ".tmp." not in p.name
            )
        if not matches:
            raise KeyError(f"no blob matches prefix {prefix!r}")
        if len(matches) > 1:
            heads = ", ".join(m[:16] for m in matches[:6])
            raise ValueError(f"ambiguous blob prefix {prefix!r}: {heads}"
                             + (" …" if len(matches) > 6 else ""))
        return matches[0]


def _link_like(path: Path, observed: os.stat_result) -> bool:
    if stat.S_ISLNK(observed.st_mode):
        return True
    reparse_flag = getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0x400)
    if getattr(observed, "st_file_attributes", 0) & reparse_flag:
        return True
    is_junction = getattr(path, "is_junction", None)
    return bool(is_junction is not None and is_junction())


def _same_identity(before: os.stat_result, after: os.stat_result) -> bool:
    if stat.S_IFMT(before.st_mode) != stat.S_IFMT(after.st_mode):
        return False
    if before.st_ino and after.st_ino:
        return (before.st_dev, before.st_ino) == (after.st_dev, after.st_ino)
    return (
        before.st_size,
        before.st_mtime_ns,
        before.st_ctime_ns,
    ) == (
        after.st_size,
        after.st_mtime_ns,
        after.st_ctime_ns,
    )


def historical_sealed_refs(
    store: BlobStore,
    artifacts,
    revealed_artifact_ids: set[str],
) -> frozenset[str]:
    """Identify unrevealed holdout refs without reading their secret bytes."""

    revealed_refs = {
        artifacts[artifact_id].content_ref
        for artifact_id in revealed_artifact_ids
        if artifact_id in artifacts
    }
    candidates: set[str] = set()
    for artifact in artifacts.values():
        ref = artifact.content_ref
        if ref.startswith("inline:"):
            continue
        if _CANONICAL_BLOB_REF.fullmatch(ref) is None:
            raise ValueError("invalid historical artifact blob reference")
        if ref not in revealed_refs:
            candidates.add(ref)

    holdout_root = store.root.parent / "holdout"
    try:
        root_stat = holdout_root.lstat()
    except FileNotFoundError:
        return frozenset()
    except OSError as error:
        raise ValueError("invalid historical holdout namespace") from error
    if not stat.S_ISDIR(root_stat.st_mode) or _link_like(holdout_root, root_stat):
        raise ValueError("invalid historical holdout namespace")

    sealed: set[str] = set()
    for ref in candidates:
        marker = holdout_root / ref
        try:
            marker_stat = marker.lstat()
        except FileNotFoundError:
            continue
        except OSError as error:
            raise ValueError("invalid historical holdout marker") from error
        if (
            not stat.S_ISREG(marker_stat.st_mode)
            or _link_like(marker, marker_stat)
            or marker_stat.st_nlink != 1
        ):
            raise ValueError("invalid historical holdout marker")
        sealed.add(ref)
    return frozenset(sealed)


class FencedBlobStore:
    """Read-only blob facade that preserves holdout visibility at one fence."""

    def __init__(self, store: BlobStore, sealed_refs: frozenset[str]) -> None:
        self._store = store
        self.root = store.root
        self.read_only = True
        self.sealed_refs = sealed_refs

    def _path(self, ref: str) -> Path:
        return self._store._path(ref)

    def put(self, _data: bytes) -> str:
        raise RuntimeError("blob store is read-only")

    def get(self, ref: str) -> bytes:
        if ref in self.sealed_refs:
            raise KeyError(f"blob is sealed at this historical fence: {ref}")
        return self._store.get(ref)

    def resolve_prefix(self, prefix: str) -> str:
        return self._store.resolve_prefix(prefix)

    def is_grounding_available(self, ref: str) -> bool:
        return ref not in self.sealed_refs
