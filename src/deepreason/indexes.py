"""Rebuildable, noncanonical indexes over an immutable run log."""

from __future__ import annotations

import base64
import hashlib
import json
import os
import tempfile
from pathlib import Path
from typing import Any

from deepreason.canonical import canonical_json
from deepreason.ontology.event import Event
from deepreason.storage.objects import ObjectStore


INDEX_SCHEMA = "deepreason-derived-indexes.v1"
INDEX_DIRECTORY = Path("indexes") / "v1"
_CATEGORIES = (
    "event-offsets",
    "work-orders",
    "provider-calls",
    "artifacts",
    "criticism-coverage",
    "capability-lifecycles",
)


class DerivedIndexError(ValueError):
    pass


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _generation_key(source_digest: str) -> str:
    """Losslessly shorten a 256-bit hex digest for one safe filename."""

    return base64.urlsafe_b64encode(bytes.fromhex(source_digest)).decode().rstrip("=")


def _io_path(path: Path) -> Path:
    """Use Win32's extended namespace only at filesystem boundaries."""

    path = Path(path)
    if os.name != "nt":
        return path
    value = str(path)
    if not os.path.isabs(value):
        value = os.path.abspath(value)
    if len(value) < 240 or value.startswith("\\\\?\\"):
        return Path(value)
    if value.startswith("\\\\"):
        return Path("\\\\?\\UNC\\" + value.lstrip("\\"))
    return Path("\\\\?\\" + value)


def _write_atomic(path: Path, payload: bytes) -> None:
    io_path = _io_path(path)
    io_path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary = tempfile.mkstemp(prefix=".index.", suffix=".tmp", dir=io_path.parent)
    try:
        with os.fdopen(descriptor, "wb") as stream:
            stream.write(payload)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, io_path)
    except BaseException:
        try:
            os.unlink(temporary)
        except OSError:
            pass
        raise


def _event_rows(log_bytes: bytes) -> tuple[list[tuple[int, int, Event]], list[dict]]:
    parsed: list[tuple[int, int, Event]] = []
    offsets: list[dict] = []
    offset = 0
    for line in log_bytes.splitlines(keepends=True):
        raw = line.rstrip(b"\r\n")
        if not raw:
            offset += len(line)
            continue
        try:
            event = Event.model_validate_json(raw)
        except ValueError as error:
            raise DerivedIndexError("cannot index a malformed canonical log") from error
        parsed.append((offset, len(line), event))
        offsets.append(
            {
                "seq": event.seq,
                "offset": offset,
                "length": len(line),
                "rule": event.rule.value,
            }
        )
        offset += len(line)
    return parsed, offsets


def _category_document(
    category: str,
    source_digest: str,
    entries: list[dict[str, Any]],
) -> dict[str, Any]:
    """Build one versioned projection payload without touching the filesystem."""

    return {
        "schema": INDEX_SCHEMA,
        "category": category,
        "source_log_sha256": source_digest,
        "entries": entries,
    }


def rebuild_indexes(root: Path | str) -> Path:
    """Rebuild all v1 indexes and publish their manifest last.

    Readers treat ``manifest.json`` as the commit point.  The files contain
    no authority and may be deleted or regenerated without affecting replay,
    root identity, or verification.
    """

    root = Path(root)
    log_path = root / "log.jsonl"
    try:
        log_bytes = _io_path(log_path).read_bytes()
    except OSError as error:
        raise DerivedIndexError("canonical log.jsonl is unavailable") from error
    source_digest = _sha256(log_bytes)
    parsed, offsets = _event_rows(log_bytes)
    objects = ObjectStore(root / "objects", read_only=True)

    work_orders: list[dict[str, Any]] = []
    provider_calls: list[dict[str, Any]] = []
    artifacts: list[dict[str, Any]] = []
    criticism: list[dict[str, Any]] = []
    lifecycles: list[dict[str, Any]] = []
    for _offset, _length, event in parsed:
        call = event.llm
        if call is not None:
            provider_calls.append(
                {
                    "seq": event.seq,
                    "role": call.role,
                    "work_id": call.work_order_id,
                    "authorization_ref": call.dispatch_authorization_ref,
                    "prompt_ref": call.prompt_ref,
                    "raw_ref": call.raw_ref,
                    "tokens": call.tokens,
                    "attempts": call.attempts,
                }
            )
        capability = event.capability
        if capability is not None:
            lifecycles.append(
                {
                    "seq": event.seq,
                    "transition_ref": capability.transition_ref,
                    "inputs": list(capability.inputs),
                    "outputs": list(capability.outputs),
                }
            )
        for object_id in event.outputs:
            try:
                schema, value = objects.get(object_id)
            except (FileNotFoundError, ValueError):
                continue
            if schema == "artifact":
                artifacts.append({"seq": event.seq, "artifact_id": object_id})
            if schema in {
                "workflow-work-order",
                "workflow-work-preparation-v1",
                "workflow-dispatch-authorization-v1",
                "workflow-work-terminal-v1",
            }:
                work_orders.append(
                    {
                        "seq": event.seq,
                        "schema": schema,
                        "object_id": object_id,
                        "work_id": getattr(value, "work_id", object_id),
                    }
                )
            if schema.startswith("criticism-"):
                criticism.append(
                    {
                        "seq": event.seq,
                        "schema": schema,
                        "object_id": object_id,
                        "assignment_ref": getattr(value, "assignment_ref", None),
                    }
                )

    category_values = {
        "event-offsets": offsets,
        "work-orders": work_orders,
        "provider-calls": provider_calls,
        "artifacts": artifacts,
        "criticism-coverage": criticism,
        "capability-lifecycles": lifecycles,
    }
    index_dir = root / INDEX_DIRECTORY
    files: dict[str, dict[str, str]] = {}
    for category in _CATEGORIES:
        document = _category_document(category, source_digest, category_values[category])
        payload = canonical_json(document) + b"\n"
        # Generation-specific immutable filenames keep the previously
        # published manifest coherent while a new generation is assembled.
        # Only the final manifest replacement changes what readers observe.
        payload_digest = _sha256(payload)
        filename = (
            f"{category}.{_generation_key(source_digest)}.{_generation_key(payload_digest)}.json"
        )
        _write_atomic(index_dir / filename, payload)
        files[category] = {"file": filename, "sha256": payload_digest}

    manifest = {
        "schema": INDEX_SCHEMA,
        "source_log": "log.jsonl",
        "source_log_sha256": source_digest,
        "files": files,
    }
    manifest_path = index_dir / "manifest.json"
    _write_atomic(manifest_path, canonical_json(manifest) + b"\n")
    return manifest_path


def load_indexes(root: Path | str) -> dict[str, list[dict[str, Any]]]:
    """Read a coherent derived generation after verifying every binding."""

    root = Path(root)
    index_dir = root / INDEX_DIRECTORY
    try:
        manifest = json.loads(_io_path(index_dir / "manifest.json").read_bytes())
        log_bytes = _io_path(root / "log.jsonl").read_bytes()
    except (OSError, ValueError) as error:
        raise DerivedIndexError("derived index manifest is unavailable or malformed") from error
    if manifest.get("schema") != INDEX_SCHEMA or manifest.get("source_log_sha256") != _sha256(
        log_bytes
    ):
        raise DerivedIndexError("derived indexes do not bind the current canonical log")
    result: dict[str, list[dict[str, Any]]] = {}
    for category in _CATEGORIES:
        metadata = manifest.get("files", {}).get(category, {})
        filename = metadata.get("file")
        try:
            expected_filename = (
                f"{category}.{_generation_key(manifest['source_log_sha256'])}."
                f"{_generation_key(metadata['sha256'])}.json"
            )
        except (KeyError, TypeError, ValueError):
            raise DerivedIndexError("derived index manifest contains an unsafe filename") from None
        if filename != expected_filename:
            raise DerivedIndexError("derived index manifest contains an unsafe filename")
        try:
            payload = _io_path(index_dir / filename).read_bytes()
            document = json.loads(payload)
        except (OSError, ValueError) as error:
            raise DerivedIndexError(f"derived {category} index is malformed") from error
        if (
            metadata.get("sha256") != _sha256(payload)
            or document.get("schema") != INDEX_SCHEMA
            or document.get("category") != category
            or document.get("source_log_sha256") != manifest["source_log_sha256"]
            or not isinstance(document.get("entries"), list)
        ):
            raise DerivedIndexError(f"derived {category} index failed verification")
        result[category] = document["entries"]
    return result


__all__ = [
    "DerivedIndexError",
    "INDEX_DIRECTORY",
    "INDEX_SCHEMA",
    "load_indexes",
    "rebuild_indexes",
]
