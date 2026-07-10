"""Content-addressed blob store (spec §1, §14).

Content is Sigma* (Def 3.1): opaque bytes + codec. Blobs are addressed by
sha256 and never mutated or deleted (D8).
"""

import os
from pathlib import Path

from deepreason.canonical import sha256_hex


class BlobStore:
    def __init__(self, root: Path, *, read_only: bool = False) -> None:
        self.root = Path(root)
        self.read_only = read_only
        if not read_only:
            self.root.mkdir(parents=True, exist_ok=True)

    def _path(self, ref: str) -> Path:
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
        if not path.exists():
            raise KeyError(f"blob not found: {ref}")
        return path.read_bytes()

    def resolve_prefix(self, prefix: str) -> str:
        """Unique-prefix resolution (the CLI `blob` command): deterministic
        sorted scan; raises KeyError when nothing matches and ValueError
        naming the candidates when the prefix is ambiguous."""
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
