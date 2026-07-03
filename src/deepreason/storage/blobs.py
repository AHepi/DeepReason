"""Content-addressed blob store (spec §1, §14).

Content is Sigma* (Def 3.1): opaque bytes + codec. Blobs are addressed by
sha256 and never mutated or deleted (D8).
"""

from pathlib import Path


class BlobStore:
    def __init__(self, root: Path) -> None:
        self.root = root

    def put(self, data: bytes) -> str:
        """Store bytes, return sha256 hash. TODO(P0)."""
        raise NotImplementedError

    def get(self, ref: str) -> bytes:
        """Fetch bytes by hash. TODO(P0)."""
        raise NotImplementedError
