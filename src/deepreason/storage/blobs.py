"""Content-addressed blob store (spec §1, §14).

Content is Sigma* (Def 3.1): opaque bytes + codec. Blobs are addressed by
sha256 and never mutated or deleted (D8).
"""

from pathlib import Path

from deepreason.canonical import sha256_hex


class BlobStore:
    def __init__(self, root: Path) -> None:
        self.root = Path(root)
        self.root.mkdir(parents=True, exist_ok=True)

    def _path(self, ref: str) -> Path:
        return self.root / ref[:2] / ref

    def put(self, data: bytes) -> str:
        ref = sha256_hex(data)
        path = self._path(ref)
        if not path.exists():
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(data)
        return ref

    def get(self, ref: str) -> bytes:
        path = self._path(ref)
        if not path.exists():
            raise KeyError(f"blob not found: {ref}")
        return path.read_bytes()
