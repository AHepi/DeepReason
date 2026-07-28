"""Managed, digest-addressed storage for admitted dossiers and source bytes.

Dossiers live under managed state, never inside a run root; runs reference
them by digest and stage the source bytes into their own blob store at
preparation time.  Reads are bounded and symlink-refusing; writes are
atomic; a digest is verified on every load.
"""

from __future__ import annotations

import os
import stat
import tempfile
from pathlib import Path

from deepreason.canonical import canonical_json, sha256_hex
from deepreason.evidence.models import EvidenceDossierV2
from deepreason.storage.blobs import BlobStore

_MAX_DOSSIER_BYTES = 8 * 1024 * 1024
_DIGEST_CHARS = set("0123456789abcdef")


class AdmissionStoreError(ValueError):
    def __init__(self, code: str, message: str) -> None:
        self.code = code
        super().__init__(f"{code}: {message}")


def _state_home() -> Path:
    home = os.environ.get("DEEPREASON_HOME")
    base = Path(home) if home else Path.home() / ".deepreason"
    return base / "admission"


class AdmissionStore:
    def __init__(self, base: Path | str | None = None) -> None:
        self.base = Path(base) if base is not None else _state_home()
        self.dossiers = self.base / "dossiers"
        self.blobs = BlobStore(self.base / "blobs")

    def save(self, dossier: EvidenceDossierV2, contents: dict[str, bytes]) -> Path:
        """Persist one dossier and every admitted source's exact bytes."""

        for source in dossier.sources:
            body = contents.get(source.content_sha256)
            if body is None or sha256_hex(body) != source.content_sha256:
                raise AdmissionStoreError(
                    "ADMISSION_STORE_SOURCE_MISSING",
                    f"bytes for source {source.id} were not supplied intact",
                )
            self.blobs.put(body)
        payload = canonical_json(
            dossier.model_dump(mode="json", by_alias=True, exclude_none=True)
        )
        target = self.dossiers / f"{dossier.dossier_digest}.json"
        target.parent.mkdir(parents=True, exist_ok=True)
        descriptor, temporary_name = tempfile.mkstemp(
            dir=target.parent, prefix=f".{target.name}.", suffix=".tmp"
        )
        temporary = Path(temporary_name)
        try:
            with os.fdopen(descriptor, "wb") as stream:
                stream.write(payload)
                stream.flush()
                os.fsync(stream.fileno())
            os.replace(temporary, target)
        finally:
            if temporary.exists():
                temporary.unlink()
        return target

    def load(self, dossier_digest: str) -> EvidenceDossierV2:
        digest = dossier_digest.removeprefix("sha256:").strip()
        if len(digest) != 64 or set(digest) - _DIGEST_CHARS:
            raise AdmissionStoreError(
                "ADMISSION_DOSSIER_INVALID", "dossier digest is not a sha256"
            )
        target = self.dossiers / f"{digest}.json"
        try:
            observed = target.lstat()
        except FileNotFoundError:
            raise AdmissionStoreError(
                "ADMISSION_DOSSIER_UNKNOWN",
                f"no stored dossier {digest[:12]}…; run deepreason admit first",
            ) from None
        if (
            not stat.S_ISREG(observed.st_mode)
            or target.is_symlink()
            or not 1 <= observed.st_size <= _MAX_DOSSIER_BYTES
        ):
            raise AdmissionStoreError(
                "ADMISSION_DOSSIER_UNSAFE", "stored dossier is not a bounded file"
            )
        dossier = EvidenceDossierV2.model_validate_json(target.read_bytes())
        if dossier.dossier_digest != digest:
            raise AdmissionStoreError(
                "ADMISSION_DOSSIER_MISMATCH",
                "stored dossier does not match its address",
            )
        return dossier

    def source_bytes(self, dossier: EvidenceDossierV2) -> dict[str, bytes]:
        """Return every source's verified raw bytes, keyed by digest."""

        contents: dict[str, bytes] = {}
        for source in dossier.sources:
            try:
                body = self.blobs.get(source.content_sha256)
            except KeyError:
                raise AdmissionStoreError(
                    "ADMISSION_SOURCE_BYTES_MISSING",
                    f"stored bytes for source {source.id} are unavailable",
                ) from None
            if sha256_hex(body) != source.content_sha256:
                raise AdmissionStoreError(
                    "ADMISSION_SOURCE_BYTES_MISMATCH",
                    f"stored bytes for source {source.id} are corrupt",
                )
            contents[source.content_sha256] = body
        return contents

    def list_digests(self) -> tuple[str, ...]:
        if not self.dossiers.is_dir():
            return ()
        return tuple(
            sorted(
                path.stem
                for path in self.dossiers.iterdir()
                if path.suffix == ".json" and not path.name.startswith(".")
            )
        )


def admission_store(base: Path | str | None = None) -> AdmissionStore:
    return AdmissionStore(base)
