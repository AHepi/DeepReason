"""Conflict-safe binding and verification for frozen run inputs."""

from __future__ import annotations

from contextlib import contextmanager
import hashlib
import json
import os
from pathlib import Path
import re
import stat
import tempfile

from deepreason.evidence.models import (
    AttachedSourceProvenanceV1,
    AttachedSourceV1,
    EvidenceDossierV1,
    RunInputManifest,
    RunInputManifestV1,
    RunInputManifestV2,
)
from deepreason.canonical import canonical_json
from deepreason.locking import ProcessLock, RUN_INPUT_LOCK_NAME
from deepreason.storage.blobs import BlobStore


RUN_INPUT_NAME = "run-input.json"
RUN_INPUT_HASH_NAME = "run-input.sha256"
EVIDENCE_DOSSIER_NAME = "evidence-dossier.json"
EVIDENCE_DOSSIER_HASH_NAME = "evidence-dossier.sha256"
_MAX_RECORD_BYTES = 8 * 1024 * 1024
_MAX_HASH_BYTES = 1_024


class RunInputError(ValueError):
    def __init__(self, code: str, message: str):
        super().__init__(f"{code}: {message}")
        self.code = code


def stage_attached_source(
    root: Path | str,
    *,
    source_id: str,
    title: str,
    source_locator: str,
    source_class: str,
    media_type: str,
    content: bytes | str,
    provenance: AttachedSourceProvenanceV1,
    retrieved_at_claim: str | None = None,
    license_or_usage_note: str | None = None,
    declared_entities: tuple[str, ...] = (),
    declared_facets: tuple[str, ...] = (),
) -> AttachedSourceV1:
    """Store pre-freeze source bytes and return their immutable source card."""

    body = content.encode("utf-8") if isinstance(content, str) else bytes(content)
    if not body:
        raise RunInputError("RUN_INPUT_SOURCE_EMPTY", "attached source body is empty")
    ref = BlobStore(Path(root) / "blobs").put(body)
    return AttachedSourceV1(
        id=source_id,
        title=title,
        source_locator=source_locator,
        source_class=source_class,
        media_type=media_type,
        content_ref=ref,
        content_sha256=ref,
        byte_count=len(body),
        retrieved_at_claim=retrieved_at_claim,
        license_or_usage_note=license_or_usage_note,
        provenance=provenance,
        declared_entities=declared_entities,
        declared_facets=declared_facets,
    )


def _canonical_bytes(model) -> bytes:
    return canonical_json(
        model.model_dump(mode="json", by_alias=True, exclude_none=True)
    )


def _atomic_write(target: Path, payload: bytes) -> None:
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
        directory_flag = getattr(os, "O_DIRECTORY", None)
        if os.name != "nt" and directory_flag is not None:
            directory_fd = os.open(target.parent, os.O_RDONLY | directory_flag)
            try:
                os.fsync(directory_fd)
            finally:
                os.close(directory_fd)
    finally:
        if temporary.exists():
            temporary.unlink()


def _read_regular(path: Path, maximum_bytes: int, *, required: bool = True) -> bytes | None:
    try:
        observed = path.lstat()
    except FileNotFoundError:
        if required:
            raise RunInputError("RUN_INPUT_FILE_UNAVAILABLE", f"missing {path.name}")
        return None
    if (
        not stat.S_ISREG(observed.st_mode)
        or path.is_symlink()
        or not 1 <= observed.st_size <= maximum_bytes
    ):
        raise RunInputError("RUN_INPUT_FILE_UNSAFE", f"unsafe {path.name}")
    flags = os.O_RDONLY | getattr(os, "O_CLOEXEC", 0) | getattr(os, "O_NOFOLLOW", 0)
    descriptor = os.open(path, flags)
    try:
        opened = os.fstat(descriptor)
        if not stat.S_ISREG(opened.st_mode) or opened.st_size != observed.st_size:
            raise RunInputError("RUN_INPUT_FILE_UNSAFE", f"changed {path.name}")
        chunks = []
        remaining = maximum_bytes + 1
        while remaining > 0:
            chunk = os.read(descriptor, remaining)
            if not chunk:
                break
            chunks.append(chunk)
            remaining -= len(chunk)
        payload = b"".join(chunks)
    finally:
        os.close(descriptor)
    current = path.lstat()
    if (
        len(payload) != observed.st_size
        or len(payload) > maximum_bytes
        or not stat.S_ISREG(current.st_mode)
        or current.st_size != observed.st_size
        or (
            observed.st_ino
            and current.st_ino
            and (observed.st_dev, observed.st_ino) != (current.st_dev, current.st_ino)
        )
    ):
        raise RunInputError("RUN_INPUT_FILE_UNSAFE", f"changed {path.name}")
    return payload


def _read_digest(path: Path) -> str | None:
    payload = _read_regular(path, _MAX_HASH_BYTES, required=False)
    if payload is None:
        return None
    try:
        digest = payload.decode("ascii").strip()
    except UnicodeDecodeError as error:
        raise RunInputError("RUN_INPUT_HASH_INVALID", f"invalid {path.name}") from error
    if re.fullmatch(r"[0-9a-f]{64}", digest) is None:
        raise RunInputError("RUN_INPUT_HASH_INVALID", f"invalid {path.name}")
    return digest


@contextmanager
def _input_lock(root: Path):
    with ProcessLock(root / RUN_INPUT_LOCK_NAME, owner="run-input", blocking=True):
        yield


def _check_source_blobs(root: Path, dossier: EvidenceDossierV1) -> None:
    store = BlobStore(root / "blobs", read_only=True)
    for source in dossier.sources:
        try:
            body = store.get(source.content_ref)
        except KeyError as error:
            raise RunInputError(
                "RUN_INPUT_SOURCE_UNAVAILABLE",
                f"source {source.id} blob is unavailable or corrupt",
            ) from error
        if len(body) != source.byte_count or hashlib.sha256(body).hexdigest() != source.content_sha256:
            raise RunInputError(
                "RUN_INPUT_SOURCE_MISMATCH",
                f"source {source.id} bytes do not match its card",
            )


def _bind_record(target: Path, sidecar: Path, payload: bytes, digest: str) -> None:
    existing = _read_regular(target, _MAX_RECORD_BYTES, required=False)
    recorded_digest = _read_digest(sidecar)
    if existing is not None and existing != payload:
        raise RunInputError("RUN_INPUT_CONFLICT", f"different record already binds {target.name}")
    if recorded_digest is not None and recorded_digest != digest:
        raise RunInputError("RUN_INPUT_CONFLICT", f"different digest already binds {target.name}")
    if existing is None:
        _atomic_write(target, payload)
    if recorded_digest is None:
        _atomic_write(sidecar, (digest + "\n").encode("ascii"))


def bind_run_input(
    run_input: RunInputManifest,
    dossier: EvidenceDossierV1,
    root: Path | str,
) -> tuple[Path, Path]:
    """Bind one immutable dossier and run input after verifying all blobs."""

    root_path = Path(root)
    root_path.mkdir(parents=True, exist_ok=True)
    if run_input.evidence_dossier_digest != dossier.dossier_digest:
        raise RunInputError(
            "RUN_INPUT_DOSSIER_MISMATCH",
            "run input does not reference the supplied dossier",
        )
    if run_input.problem.id != dossier.problem_ref:
        raise RunInputError(
            "RUN_INPUT_PROBLEM_MISMATCH",
            "run input and dossier name different problems",
        )
    _check_source_blobs(root_path, dossier)
    dossier_payload = _canonical_bytes(dossier)
    input_payload = _canonical_bytes(run_input)
    dossier_path = root_path / EVIDENCE_DOSSIER_NAME
    input_path = root_path / RUN_INPUT_NAME
    with _input_lock(root_path):
        # A partial crash is recoverable only with the exact same canonical
        # records; neither write can replace an earlier identity.
        _bind_record(
            dossier_path,
            root_path / EVIDENCE_DOSSIER_HASH_NAME,
            dossier_payload,
            dossier.dossier_digest,
        )
        _bind_record(
            input_path,
            root_path / RUN_INPUT_HASH_NAME,
            input_payload,
            run_input.run_input_digest,
        )
    return input_path, dossier_path


def _resolve_record_path(path: Path | str, name: str) -> Path:
    value = Path(path)
    return value / name if value.is_dir() else value


def load_run_input(path: Path | str, *, verify_hash: bool = True) -> RunInputManifest:
    target = _resolve_record_path(path, RUN_INPUT_NAME)
    payload = _read_regular(target, _MAX_RECORD_BYTES)
    assert payload is not None
    try:
        decoded = json.loads(payload)
        schema = decoded.get("schema") if isinstance(decoded, dict) else None
        model = {
            "run-input-manifest.v1": RunInputManifestV1,
            "run-input-manifest.v2": RunInputManifestV2,
        }.get(schema)
        if model is None:
            raise ValueError("unknown run-input schema")
        value = model.model_validate_json(payload)
    except (UnicodeError, json.JSONDecodeError, ValueError) as error:
        raise RunInputError("RUN_INPUT_INVALID", "run-input schema is invalid") from error
    if verify_hash:
        expected = _read_digest(target.parent / RUN_INPUT_HASH_NAME)
        if expected is not None and expected != value.run_input_digest:
            raise RunInputError("RUN_INPUT_HASH_MISMATCH", "run-input sidecar differs")
    return value


def load_evidence_dossier(
    path: Path | str, *, verify_hash: bool = True
) -> EvidenceDossierV1:
    target = _resolve_record_path(path, EVIDENCE_DOSSIER_NAME)
    payload = _read_regular(target, _MAX_RECORD_BYTES)
    assert payload is not None
    try:
        value = EvidenceDossierV1.model_validate_json(payload)
    except ValueError as error:
        raise RunInputError("EVIDENCE_DOSSIER_INVALID", "dossier schema is invalid") from error
    if verify_hash:
        expected = _read_digest(target.parent / EVIDENCE_DOSSIER_HASH_NAME)
        if expected is not None and expected != value.dossier_digest:
            raise RunInputError("RUN_INPUT_HASH_MISMATCH", "dossier sidecar differs")
    return value


def verify_run_input(root: Path | str) -> dict:
    root_path = Path(root)
    run_input = load_run_input(root_path)
    dossier = load_evidence_dossier(root_path)
    if run_input.evidence_dossier_digest != dossier.dossier_digest:
        raise RunInputError("RUN_INPUT_DOSSIER_MISMATCH", "bound records disagree")
    if run_input.problem.id != dossier.problem_ref:
        raise RunInputError("RUN_INPUT_PROBLEM_MISMATCH", "bound records disagree")
    _check_source_blobs(root_path, dossier)
    report = {
        "valid": True,
        "run_input_digest": run_input.run_input_digest,
        "evidence_dossier_digest": dossier.dossier_digest,
        "source_count": len(dossier.sources),
        "source_bytes": dossier.total_byte_count,
    }
    if isinstance(run_input, RunInputManifestV2):
        report["input_schema_version"] = 2
    return report


__all__ = [
    "EVIDENCE_DOSSIER_HASH_NAME",
    "EVIDENCE_DOSSIER_NAME",
    "RUN_INPUT_HASH_NAME",
    "RUN_INPUT_NAME",
    "RunInputError",
    "bind_run_input",
    "load_evidence_dossier",
    "load_run_input",
    "stage_attached_source",
    "verify_run_input",
]
